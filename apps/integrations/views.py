import json
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.integrations.auth import (
    SCOPES,
    authenticate,
    digest,
    exchange_code,
    origin,
    refresh_tokens,
    revoke,
    vendor_for_user,
)
from apps.integrations.models import (
    AuditEvent,
    AuthorizationCode,
    Connection,
    DesignAsset,
    OAuthClient,
    PendingConsent,
    TokenPair,
)
from apps.vendors.panel import panel_context


def limited(request: HttpRequest, key: str, limit: int = 40) -> bool:
    # Proxy must preserve REMOTE_ADDR; never trust caller-supplied forwarded headers.
    key = 'mcp:' + key + ':' + digest(request.META.get('REMOTE_ADDR', 'unknown'))
    cache.add(key, 0, 60)
    return cache.incr(key) > limit


def no_store(response: HttpResponse) -> HttpResponse:
    response['Cache-Control'] = 'no-store'
    response['Pragma'] = 'no-cache'
    return response


@require_GET
def discovery(request: HttpRequest) -> JsonResponse:
    try:
        base = origin()
    except ValidationError:
        return JsonResponse({'error': 'mcp_not_configured'}, status=503)
    return JsonResponse(
        {
            'issuer': base,
            'authorization_endpoint': base + '/integrations/oauth/authorize/',
            'token_endpoint': base + '/integrations/oauth/token/',
            'registration_endpoint': base + '/integrations/oauth/register/',
            'revocation_endpoint': base + '/integrations/oauth/revoke/',
            'response_types_supported': ['code'],
            'grant_types_supported': ['authorization_code', 'refresh_token'],
            'code_challenge_methods_supported': ['S256'],
            'token_endpoint_auth_methods_supported': ['none'],
            'scopes_supported': sorted(SCOPES),
        }
    )


@require_GET
def resource_metadata(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            'resource': origin() + '/mcp/',
            'authorization_servers': [origin()],
            'scopes_supported': sorted(SCOPES),
            'bearer_methods_supported': ['header'],
        }
    )


@csrf_exempt
@require_POST
def register(request: HttpRequest) -> HttpResponse:
    if limited(request, 'register', 10):
        return JsonResponse({'error': 'slow_down'}, status=429)
    try:
        if len(request.body) > 16000:
            raise ValueError
        data = json.loads(request.body)
        uris = data['redirect_uris']
        if not isinstance(uris, list) or not 1 <= len(uris) <= 5:
            raise ValueError
        for uri in uris:
            if not isinstance(uri, str):
                raise ValueError
            parsed = urlsplit(uri)
            if (
                parsed.scheme != 'https'
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.fragment
                or len(uri) > 2000
            ):
                raise ValueError
        if data.get('token_endpoint_auth_method', 'none') != 'none':
            raise ValueError
        client = OAuthClient.objects.create(
            name=str(data.get('client_name', 'ChatGPT'))[:150], redirect_uris=uris
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'error': 'invalid_client_metadata'}, status=400)
    return no_store(
        JsonResponse(
            {
                'client_id': str(client.pk),
                'client_name': client.name,
                'redirect_uris': uris,
                'token_endpoint_auth_method': 'none',
                'grant_types': ['authorization_code', 'refresh_token'],
                'response_types': ['code'],
            },
            status=201,
        )
    )


@login_required
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def authorize(request: HttpRequest) -> HttpResponse:
    vendor = vendor_for_user(request.user)
    try:
        if request.method == 'POST':
            data = signing.loads(
                request.POST.get('request', ''), salt='mcp-consent', max_age=900
            )
            if data['user_id'] != request.user.pk:
                raise ValueError
        else:
            data = {
                key: request.GET.get(key, '')
                for key in [
                    'client_id',
                    'redirect_uri',
                    'state',
                    'scope',
                    'resource',
                    'code_challenge',
                    'code_challenge_method',
                    'response_type',
                ]
            }
            data['user_id'] = request.user.pk
        client = OAuthClient.objects.get(pk=data['client_id'])
        if data['redirect_uri'] not in client.redirect_uris:
            raise ValueError
        scopes = set(data['scope'].split())
        if (
            not scopes
            or not scopes <= SCOPES
            or 'vendor:read' not in scopes
            or data['resource'] != origin() + '/mcp/'
            or data['response_type'] != 'code'
            or data['code_challenge_method'] != 'S256'
            or not re.fullmatch(r'[A-Za-z0-9_-]{43}', data['code_challenge'])
            or len(data['state']) > 1000
        ):
            raise ValueError
    except (
        ValueError,
        TypeError,
        KeyError,
        signing.BadSignature,
        OAuthClient.DoesNotExist,
    ):
        return HttpResponse('درخواست اتصال معتبر نیست.', status=400)
    if request.method == 'POST':
        # Signed requests are session-bound and consumed once.
        nonce = digest(request.POST['request'])
        pending = request.session.pop('mcp_consent', None)
        consumed = PendingConsent.objects.filter(
            digest=nonce, vendor=vendor, consumed_at__isnull=True
        ).update(consumed_at=timezone.now())
        if pending != nonce or not consumed:
            return HttpResponse('این درخواست قبلاً استفاده شده است.', status=400)
        if request.POST.get('decision') != 'approve':
            return redirect(
                data['redirect_uri']
                + ('&' if '?' in data['redirect_uri'] else '?')
                + urlencode({'error': 'access_denied', 'state': data['state']})
            )
        connection = Connection.objects.create(
            vendor=vendor, client=client, scopes=' '.join(sorted(scopes))
        )
        raw = secrets.token_urlsafe(48)
        AuthorizationCode.objects.create(
            digest=digest(raw),
            connection=connection,
            redirect_uri=data['redirect_uri'],
            challenge=data['code_challenge'],
            resource=data['resource'],
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        return no_store(
            redirect(
                data['redirect_uri']
                + ('&' if '?' in data['redirect_uri'] else '?')
                + urlencode({'code': raw, 'state': data['state'], 'iss': origin()})
            )
        )
    signed = signing.dumps(data, salt='mcp-consent')
    PendingConsent.objects.get_or_create(digest=digest(signed), vendor=vendor)
    request.session['mcp_consent'] = digest(signed)
    return no_store(
        render(
            request,
            'pages/integrations/consent.html',
            {
                'client_name': client.name,
                'vendor': vendor,
                'signed_request': signed,
                'can_write': 'vendor:write' in scopes,
            },
        )
    )


@csrf_exempt
@require_POST
def token(request: HttpRequest) -> HttpResponse:
    if limited(request, 'token'):
        return JsonResponse({'error': 'slow_down'}, status=429)
    data = request.POST.dict()
    try:
        if data.get('grant_type') == 'authorization_code':
            result = exchange_code(data)
        elif data.get('grant_type') == 'refresh_token':
            result = refresh_tokens(data)
        else:
            return JsonResponse({'error': 'unsupported_grant_type'}, status=400)
    except (ValidationError, PermissionDenied):
        return no_store(JsonResponse({'error': 'invalid_grant'}, status=400))
    return no_store(JsonResponse(result))


@csrf_exempt
@require_POST
def revoke_token(request: HttpRequest) -> HttpResponse:
    value = digest(request.POST.get('token', ''))
    from django.db.models import Q

    pair = TokenPair.objects.filter(
        Q(access_digest=value) | Q(refresh_digest=value),
        connection__client_id=request.POST.get('client_id', ''),
    ).first()
    if pair:
        revoke(pair.connection)
    return no_store(JsonResponse({}))


@login_required
@require_http_methods(['GET', 'POST'])
def panel(request: HttpRequest) -> HttpResponse:
    vendor = vendor_for_user(request.user)
    if request.method == 'POST':
        connection = get_object_or_404(
            Connection, pk=request.POST.get('connection'), vendor=vendor
        )
        revoke(connection)
        messages.success(request, 'دسترسی این اتصال قطع شد.')
        return redirect('integrations:panel')
    return no_store(
        render(
            request,
            'pages/integrations/panel.html',
            panel_context(
                vendor,
                'integrations',
                mcp_url=(settings.PUBLIC_SITE_URL.rstrip('/') + '/mcp/')
                if settings.PUBLIC_SITE_URL
                else request.build_absolute_uri('/mcp/'),
                mcp_ready=settings.PUBLIC_SITE_URL.startswith('https://'),
                connections=Connection.objects.filter(vendor=vendor)
                .select_related('client')
                .order_by('-created_at')[:20],
                events=vendor_events(vendor.pk),
                assets=DesignAsset.objects.filter(vendor=vendor).order_by(
                    '-created_at'
                )[:20],
            ),
        )
    )


def vendor_events(vendor_id: int) -> QuerySet[AuditEvent]:
    from apps.integrations.models import AuditEvent

    return AuditEvent.objects.filter(connection__vendor_id=vendor_id).select_related(
        'connection__client'
    )[:30]


@require_GET
def private_image(request: HttpRequest, pk: str) -> HttpResponse:
    if request.headers.get('Authorization', '').startswith('Bearer '):
        vendor = authenticate(request.headers['Authorization'][7:]).vendor
    else:
        if not request.user.is_authenticated:
            raise PermissionDenied
        vendor = vendor_for_user(request.user)
    asset = get_object_or_404(DesignAsset, pk=pk, vendor=vendor)
    return no_store(FileResponse(asset.image.open('rb'), content_type='image/png'))


@csrf_exempt
def mcp_wsgi_unavailable(request: HttpRequest) -> HttpResponse:
    response = JsonResponse(
        {'error': 'MCP requires the ASGI deployment (core.asgi:application).'},
        status=503,
    )
    if not request.headers.get('Authorization'):
        response.status_code = 401
        response['WWW-Authenticate'] = (
            'Bearer resource_metadata="'
            f'{origin()}/.well-known/oauth-protected-resource"'
        )
    return response
