import base64
import hashlib
import json
from datetime import timedelta
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils import timezone
from PIL import Image

from apps.accounts.models import User
from apps.catalog.models import Service
from apps.integrations.auth import (
    authenticate,
    issue_tokens,
    refresh_tokens,
    revoke,
)
from apps.integrations.files import ChatGPTFile, download_image, normalize_image
from apps.integrations.models import (
    Connection,
    DesignAsset,
    OAuthClient,
    Operation,
    TokenPair,
)
from apps.integrations.services import (
    ProfileAction,
    PublishAction,
    execute_operation,
    prepare,
)
from apps.integrations.tools.context import bearer
from apps.integrations.tools.read import list_records, read_messages
from apps.locations.models import City, Province
from apps.portfolio.models import PortfolioItem
from apps.requests.models import ProjectRequest
from apps.vendors.models import Vendor

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def public_origin(settings):
    settings.PUBLIC_SITE_URL = "https://tablo.example"


def test_mcp_requires_bearer(client):
    response = client.post('/mcp/', data='{}', content_type='application/json')
    assert response.status_code == 401
    assert 'resource_metadata' in response['WWW-Authenticate']


def test_discovery_has_pkce_and_resource(client, settings):
    settings.PUBLIC_SITE_URL = 'https://tablo.example'
    response = client.get('/.well-known/oauth-authorization-server')
    assert response.status_code == 200
    assert response.json()['code_challenge_methods_supported'] == ['S256']
    assert response.json()['issuer'] == 'https://tablo.example'


@pytest.fixture
def vendors():
    province = Province.objects.create(name='تهران', slug='tehran')
    city = City.objects.create(name='تهران', slug='tehran', province=province)
    service = Service.objects.create(title='چلنیوم', slug='channel')
    result = []
    for number in range(2):
        user = User.objects.create_user(username=f'vendor-{number}', role='vendor')
        result.append(
            Vendor.objects.create(
                user=user,
                city=city,
                business_name=f'کارگاه {number}',
                verification_status='approved',
            )
        )
    for vendor in result:
        vendor.services.add(service)
    return result


@pytest.fixture
def connection(vendors):
    client = OAuthClient.objects.create(
        name='ChatGPT', redirect_uris=['https://chatgpt.com/callback']
    )
    return Connection.objects.create(vendor=vendors[0], client=client)


@pytest.fixture
def credentials(connection):
    return issue_tokens(connection)


def test_oauth_consent_and_pkce_round_trip(client, vendors):
    response = client.post(
        '/integrations/oauth/register/',
        data=json.dumps(
            {
                'client_name': 'ChatGPT',
                'redirect_uris': ['https://chatgpt.com/callback'],
            }
        ),
        content_type='application/json',
    )
    client_id = response.json()['client_id']
    verifier = 'a' * 64
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip('=')
    )
    params = {
        'client_id': client_id,
        'redirect_uri': 'https://chatgpt.com/callback',
        'response_type': 'code',
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'resource': 'https://tablo.example/mcp/',
        'scope': 'vendor:read vendor:write offline_access',
        'state': 'hello',
    }
    client.force_login(vendors[0].user)
    consent = client.get('/integrations/oauth/authorize/', params)
    assert consent.status_code == 200
    signed = consent.context['signed_request']
    response = client.post(
        '/integrations/oauth/authorize/', {'request': signed, 'decision': 'approve'}
    )
    values = parse_qs(urlsplit(response.url).query)
    assert values['state'] == ['hello']
    assert (
        client.post(
            '/integrations/oauth/authorize/', {'request': signed, 'decision': 'approve'}
        ).status_code
        == 400
    )
    data = {
        'grant_type': 'authorization_code',
        'code': values['code'][0],
        'client_id': client_id,
        'redirect_uri': params['redirect_uri'],
        'resource': params['resource'],
        'code_verifier': verifier,
    }
    bad = client.post('/integrations/oauth/token/', data | {'code_verifier': 'b' * 64})
    assert bad.status_code == 400
    tokens = client.post('/integrations/oauth/token/', data)
    assert tokens.status_code == 200
    assert authenticate(tokens.json()['access_token']).vendor_id == vendors[0].pk
    assert client.post('/integrations/oauth/token/', data).status_code == 400
    assert TokenPair.objects.get().access_digest != tokens.json()['access_token']


def test_refresh_rotates_and_revocation_is_immediate(connection, credentials):
    data = {
        'refresh_token': credentials['refresh_token'],
        'client_id': str(connection.client_id),
        'resource': 'https://tablo.example/mcp/',
    }
    rotated = refresh_tokens(data)
    with pytest.raises(ValidationError):
        refresh_tokens(data)
    with pytest.raises(PermissionDenied):
        authenticate(credentials['access_token'])
    revoke(connection)
    with pytest.raises(PermissionDenied):
        authenticate(rotated['access_token'])


@pytest.mark.parametrize('change', ['suspended', 'inactive', 'role', 'user_inactive'])
def test_account_state_rechecked(connection, credentials, change):
    vendor = connection.vendor
    if change == 'suspended':
        vendor.verification_status = 'suspended'
        vendor.save()
    if change == 'inactive':
        vendor.is_active = False
        vendor.save()
    if change == 'role':
        vendor.user.role = 'customer'
        vendor.user.save()
    if change == 'user_inactive':
        vendor.user.is_active = False
        vendor.user.save()
    with pytest.raises(PermissionDenied):
        authenticate(credentials['access_token'])


def test_tenant_scope_for_requests_portfolio_and_assets(
    client, vendors, credentials, settings
):
    own, other = vendors
    public = ProjectRequest.objects.create(
        title='عمومی', city=own.city, needs_guidance=True, status='submitted'
    )
    private = ProjectRequest.objects.create(
        title='محرمانه', city=own.city, preferred_vendor=other, status='submitted'
    )
    portfolio = PortfolioItem.objects.create(
        vendor=other, title='مخفی', slug='hidden', is_published=False
    )
    asset = DesignAsset.objects.create(
        vendor=other, title='تصویر خصوصی', image=normalize_image(image_bytes())
    )
    token = bearer.set(credentials['access_token'])
    try:
        assert [item['id'] for item in list_records('requests').items] == [public.pk]
        assert list_records('portfolio').items == []
        assert list_records('designs').items == []
        with pytest.raises(Http404):
            prepare(
                authenticate(credentials['access_token']),
                PublishAction(kind='publish', portfolio_id=portfolio.pk),
            )
        with pytest.raises(Http404):
            read_messages(99999)
    finally:
        bearer.reset(token)
    client.force_login(own.user)
    assert client.get(f'/integrations/assets/{asset.pk}/').status_code == 404
    assert private.pk != public.pk
    assert not str(asset.image.path).startswith(str(settings.MEDIA_ROOT))
    with pytest.raises(ValueError):
        _ = asset.image.url


def test_previews_do_not_write_and_execute_once(connection):
    draft = prepare(connection, ProfileAction(kind='profile', description='تخصص جدید'))
    connection.vendor.refresh_from_db()
    assert connection.vendor.description == ''
    result = execute_operation(connection, draft.pk)
    assert execute_operation(connection, draft.pk) == result
    connection.vendor.refresh_from_db()
    assert connection.vendor.description == 'تخصص جدید'
    assert connection.auditevent_set.count() == 1


def test_changed_or_expired_previews_rejected(connection):
    draft = prepare(connection, ProfileAction(kind='profile', description='پیش‌نویس'))
    vendor = connection.vendor
    vendor.business_name = 'نام تازه'
    vendor.save()
    with pytest.raises(ValidationError):
        execute_operation(connection, draft.pk)
    draft = prepare(connection, ProfileAction(kind='profile', description='پیش‌نویس'))
    Operation.objects.filter(pk=draft.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    with pytest.raises(ValidationError):
        execute_operation(connection, draft.pk)


def image_bytes():
    stream = BytesIO()
    Image.new('RGB', (8, 8), 'blue').save(stream, format='PNG')
    return stream.getvalue()


@pytest.mark.parametrize(
    'url',
    [
        'http://example.com/image.png',
        'https://127.0.0.1/x',
        'https://[::1]/x',
        'https://169.254.169.254/x',
        'https://localhost/x',
    ],
)
def test_private_download_targets_rejected(url):
    with pytest.raises(ValidationError):
        download_image(ChatGPTFile(download_url=url, file_id='file_test'))


def test_real_image_validation():
    with pytest.raises(ValidationError):
        normalize_image(b'not an image')
    uploaded = normalize_image(image_bytes())
    assert uploaded.content_type == 'image/png'


def test_panel_and_revoke(client, connection, credentials):
    client.force_login(connection.vendor.user)
    response = client.get('/integrations/chatgpt/')
    assert response.status_code == 200
    assert 'https://tablo.example/mcp/' in response.content.decode()
    assert credentials['access_token'] not in response.content.decode()
    client.post('/integrations/chatgpt/', {'connection': str(connection.pk)})
    with pytest.raises(PermissionDenied):
        authenticate(credentials['access_token'])


def rpc(method, credentials=None, params=None):
    import httpx

    from core.asgi import application

    async def call():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=application),
            base_url='https://tablo.example',
        ) as client:
            headers = {'Accept': 'application/json, text/event-stream'}
            if credentials:
                headers['Authorization'] = 'Bearer ' + credentials['access_token']
            return await client.post(
                '/mcp/',
                json={
                    'jsonrpc': '2.0',
                    'id': 1,
                    'method': method,
                    'params': params or {},
                },
                headers=headers,
            )

    return async_to_sync(call)()


def test_real_sdk_transport_and_tools(credentials):
    assert rpc('tools/list').status_code == 401
    response = rpc(
        'initialize',
        credentials,
        {
            'protocolVersion': '2025-03-26',
            'capabilities': {},
            'clientInfo': {'name': 'test', 'version': '1'},
        },
    )
    assert response.status_code == 200
    tools = rpc('tools/list', credentials).json()['result']['tools']
    assert {tool['name'] for tool in tools} >= {
        'save_design',
        'prepare_operation',
        'confirm_operation',
    }
    file_tool = next(tool for tool in tools if tool['name'] == 'save_design')
    assert file_tool['_meta']['openai/fileParams'] == ['file']
    result = rpc(
        'tools/call', credentials, {'name': 'panel_summary', 'arguments': {}}
    ).json()['result']
    assert not result.get('isError')
    assert result['structuredContent']['business_name'] == 'کارگاه 0'


def test_read_scope_cannot_prepare(connection):
    connection.scopes = 'vendor:read'
    connection.save()
    token_data = issue_tokens(connection)
    result = rpc(
        'tools/call',
        token_data,
        {
            'name': 'prepare_operation',
            'arguments': {'action': {'kind': 'profile', 'description': 'ممنوع'}},
        },
    ).json()['result']
    assert result['isError']
    assert not Operation.objects.exists()


def test_token_expiry(connection, credentials):
    TokenPair.objects.update(access_expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(PermissionDenied):
        authenticate(credentials['access_token'])
    TokenPair.objects.update(refresh_expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        refresh_tokens(
            {
                'refresh_token': credentials['refresh_token'],
                'client_id': str(connection.client_id),
                'resource': 'https://tablo.example/mcp/',
            }
        )


def test_sdk_file_save_and_owner_image(monkeypatch, client, credentials, connection):
    from apps.integrations.tools import write

    monkeypatch.setattr(
        write, 'download_image', lambda file: normalize_image(image_bytes())
    )
    response = rpc(
        'tools/call',
        credentials,
        {
            'name': 'save_design',
            'arguments': {
                'file': {
                    'file_id': 'file_123',
                    'download_url': 'https://files.example/image',
                },
                'title': 'طرح شب',
            },
        },
    ).json()['result']
    assert not response.get('isError')
    asset_id = response['structuredContent']['asset_id']
    result = rpc(
        'tools/call',
        credentials,
        {'name': 'view_design', 'arguments': {'asset_id': asset_id}},
    ).json()['result']
    assert any(item['type'] == 'image' for item in result['content'])
    asset = DesignAsset.objects.get(pk=asset_id)
    assert asset.vendor_id == connection.vendor_id
    assert client.get(f'/integrations/assets/{asset_id}/').status_code == 403
    client.force_login(connection.vendor.user)
    assert client.get(f'/integrations/assets/{asset_id}/').status_code == 200
    assert (
        rpc(
            'resources/read', credentials, {'uri': 'ui://tablo/design-saver.html'}
        ).status_code
        == 200
    )


def test_owner_scopes_for_quotes_orders_messages(connection, credentials, vendors):
    from apps.chat.models import Conversation
    from apps.integrations.services import (
        DesignAction,
        MessageAction,
        QuoteAction,
        StageAction,
    )
    from apps.orders.models import Order
    from apps.quotes.models import Quote

    other = vendors[1]
    request = ProjectRequest.objects.create(
        title='خصوصی', city=other.city, preferred_vendor=other, status='submitted'
    )
    quote = Quote.objects.create(
        vendor=other, request=request, price=100, estimated_delivery_days=2
    )
    order = Order.objects.create(
        vendor=other,
        request=request,
        quote=quote,
        customer=other.user,
        agreed_price=100,
    )
    conversation = Conversation.objects.create(quote=quote)
    asset = DesignAsset.objects.create(
        vendor=other, title='طرح', image=normalize_image(image_bytes())
    )
    actions = [
        StageAction(kind='stage', order_id=order.pk, stage='installation'),
        MessageAction(kind='message', conversation_id=conversation.pk, body='پیام'),
        QuoteAction(
            kind='quote', request_id=request.pk, price=100, estimated_delivery_days=2
        ),
        DesignAction(
            kind='design',
            order_id=order.pk,
            asset_id=asset.pk,
            price=100,
            installation_cost=0,
            materials='فلز',
            notes='طرح',
        ),
    ]
    for action in actions:
        with pytest.raises(Http404):
            prepare(connection, action)
    token = bearer.set(credentials['access_token'])
    try:
        for kind in ['quotes', 'projects', 'conversations', 'notifications']:
            assert list_records(kind).items == []
        with pytest.raises(Http404):
            read_messages(conversation.pk)
    finally:
        bearer.reset(token)


def test_lists_have_constant_query_count(
    connection, credentials, django_assert_num_queries
):
    for index in range(6):
        PortfolioItem.objects.create(
            vendor=connection.vendor, title=f'کار {index}', slug=f'work-{index}'
        )
    token = bearer.set(credentials['access_token'])
    try:
        with django_assert_num_queries(4):
            assert len(list_records('portfolio').items) == 6
    finally:
        bearer.reset(token)


@pytest.mark.django_db(transaction=True)
def test_concurrent_refresh_has_one_winner(connection, credentials):
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    data = {
        'refresh_token': credentials['refresh_token'],
        'client_id': str(connection.client_id),
        'resource': 'https://tablo.example/mcp/',
    }

    def attempt():
        close_old_connections()
        try:
            refresh_tokens(data)
            return True
        except ValidationError:
            return False
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [False, True]
    assert TokenPair.objects.filter(revoked_at__isnull=True).count() == 1


@pytest.mark.parametrize(
    'overrides',
    [
        {'redirect_uri': 'https://attacker.example/callback'},
        {'resource': 'https://attacker.example/mcp/'},
        {'scope': 'vendor:read admin'},
        {'code_challenge_method': 'plain'},
    ],
)
def test_bad_consent_not_redirected(client, connection, overrides):
    client.force_login(connection.vendor.user)
    params = {
        'client_id': str(connection.client_id),
        'redirect_uri': 'https://chatgpt.com/callback',
        'response_type': 'code',
        'code_challenge': 'a' * 43,
        'code_challenge_method': 'S256',
        'resource': 'https://tablo.example/mcp/',
        'scope': 'vendor:read',
    }
    response = client.get('/integrations/oauth/authorize/', params | overrides)
    assert response.status_code == 400
    assert 'Location' not in response


def test_image_download_no_redirect_and_rebinding(monkeypatch):
    from apps.integrations import files

    monkeypatch.setattr(
        files.socket,
        'getaddrinfo',
        lambda *args, **kwargs: [(None, None, None, None, ('93.184.216.34', 443))],
    )
    seen = []

    class ConnectionStub:
        def __init__(self, host, address):
            seen.append((host, address))

        def request(self, *args):
            pass

        def getresponse(self):
            class Response:
                status = 302

            return Response()

        def close(self):
            pass

    monkeypatch.setattr(files, 'PinnedHTTPS', ConnectionStub)
    with pytest.raises(ValidationError):
        download_image(
            ChatGPTFile(file_id='file_x', download_url='https://example.com/image')
        )
    assert seen == [('example.com', '93.184.216.34')]


def test_quote_preview_submit_and_message_idempotency(connection):
    from apps.chat.models import Conversation
    from apps.integrations.services import MessageAction, QuoteAction
    from apps.quotes.models import Quote

    customer = User.objects.create_user(username='customer', role='customer')
    item = ProjectRequest.objects.create(
        customer=customer,
        title='فروشگاه',
        city=connection.vendor.city,
        preferred_vendor=connection.vendor,
        status='submitted',
    )
    draft = prepare(
        connection,
        QuoteAction(
            kind='quote',
            request_id=item.pk,
            price=1000,
            installation_cost=100,
            estimated_delivery_days=3,
        ),
    )
    assert not Quote.objects.exists()
    result = execute_operation(connection, draft.pk)
    assert execute_operation(connection, draft.pk) == result
    assert Quote.objects.count() == 1
    quote = Quote.objects.get()
    conversation = Conversation.objects.create(quote=quote)
    message = prepare(
        connection,
        MessageAction(
            kind='message', conversation_id=conversation.pk, body='سلام؛ طرح آماده است.'
        ),
    )
    result = execute_operation(connection, message.pk)
    assert execute_operation(connection, message.pk) == result
    assert conversation.messages.count() == 1


def test_concept_portfolio_and_customer_workflow(connection):
    from apps.integrations.services import (
        DesignAction,
        PortfolioAction,
        PublishAction,
        StageAction,
    )
    from apps.orders.models import Order
    from apps.quotes.models import Quote

    customer = User.objects.create_user(username='owner', role='customer')
    vendor = connection.vendor
    item = ProjectRequest.objects.create(
        customer=customer, city=vendor.city, preferred_vendor=vendor, status='accepted'
    )
    quote = Quote.objects.create(
        vendor=vendor, request=item, price=1000, estimated_delivery_days=3
    )
    order = Order.objects.create(
        vendor=vendor, customer=customer, request=item, quote=quote, agreed_price=1000
    )
    asset = DesignAsset.objects.create(
        vendor=vendor, title='طرح', image=normalize_image(image_bytes())
    )
    draft = prepare(
        connection,
        DesignAction(
            kind='design',
            order_id=order.pk,
            asset_id=asset.pk,
            price=1000,
            installation_cost=100,
            materials='چلنیوم',
            notes='طرح پیشنهادی',
        ),
    )
    execute_operation(connection, draft.pk)
    order.refresh_from_db()
    assert order.stage == 'approval'
    invalid = prepare(
        connection, StageAction(kind='stage', order_id=order.pk, stage='installation')
    )
    with pytest.raises(ValidationError):
        execute_operation(connection, invalid.pk)
    order.refresh_from_db()
    assert order.design_approved_at is None
    draft = prepare(
        connection,
        PortfolioAction(
            kind='portfolio',
            title='طرح فروشگاه',
            service=vendor.services.first().pk,
            city=vendor.city_id,
            asset_id=asset.pk,
        ),
    )
    result = execute_operation(connection, draft.pk)
    portfolio = PortfolioItem.objects.get(pk=result['portfolio_id'])
    assert portfolio.is_ai_concept and not portfolio.is_published
    publish = prepare(
        connection, PublishAction(kind='publish', portfolio_id=portfolio.pk)
    )
    execute_operation(connection, publish.pk)
    portfolio.refresh_from_db()
    assert portfolio.is_published


@pytest.mark.django_db(transaction=True)
def test_concurrent_code_exchange_has_one_winner(connection):
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    from apps.integrations.auth import digest, exchange_code
    from apps.integrations.models import AuthorizationCode

    verifier = 'a' * 64
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip('=')
    )
    AuthorizationCode.objects.create(
        digest=digest('one-code'),
        connection=connection,
        redirect_uri='https://chatgpt.com/callback',
        challenge=challenge,
        resource='https://tablo.example/mcp/',
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    data = {
        'code': 'one-code',
        'client_id': str(connection.client_id),
        'redirect_uri': 'https://chatgpt.com/callback',
        'resource': 'https://tablo.example/mcp/',
        'code_verifier': verifier,
    }

    def attempt():
        close_old_connections()
        try:
            exchange_code(data)
            return True
        except ValidationError:
            return False
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [False, True]
    assert TokenPair.objects.count() == 1


def test_consent_and_revoke_require_csrf(connection):
    from django.test import Client

    client = Client(enforce_csrf_checks=True)
    client.force_login(connection.vendor.user)
    assert (
        client.post(
            '/integrations/oauth/authorize/', {'decision': 'approve'}
        ).status_code
        == 403
    )
    assert (
        client.post(
            '/integrations/chatgpt/', {'connection': str(connection.pk)}
        ).status_code
        == 403
    )
    connection.refresh_from_db()
    assert connection.revoked_at is None


def test_connection_guide_always_shows_address(client, connection, settings):
    settings.PUBLIC_SITE_URL = ''
    client.force_login(connection.vendor.user)
    response = client.get('/integrations/chatgpt/')
    assert response.status_code == 200
    assert response.context['mcp_url'] == 'http://testserver/mcp/'
    assert not response.context['mcp_ready']
    content = response.content.decode()
    assert 'Add custom MCP server' in content
    assert 'OAuth' in content
    assert 'Plugins' in content
