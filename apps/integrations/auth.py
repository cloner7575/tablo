"""Opaque, revocable OAuth credentials bound to a vendor and MCP resource."""

import base64
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.integrations.models import AuthorizationCode, Connection, TokenPair
from apps.vendors.models import Vendor

SCOPES = {'vendor:read', 'vendor:write', 'offline_access'}


def origin() -> str:
    from urllib.parse import urlsplit

    value = settings.PUBLIC_SITE_URL.rstrip('/')
    parsed = urlsplit(value)
    if (
        parsed.scheme != 'https'
        or not parsed.hostname
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValidationError('PUBLIC_SITE_URL must be a public HTTPS origin.')
    return value


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def vendor_for_user(user: User) -> Vendor:
    if not user.is_active or user.role != 'vendor':
        raise PermissionDenied('حساب تابلوساز فعال لازم است.')
    vendor = Vendor.objects.select_related('user').filter(user=user).first()
    if not vendor or not vendor.is_approved:
        raise PermissionDenied('حساب تابلوساز باید فعال و تأییدشده باشد.')
    return vendor


def eligible(connection: Connection) -> None:
    if connection.revoked_at:
        raise PermissionDenied('اتصال قطع شده است.')
    vendor_for_user(connection.vendor.user)


def authenticate(raw: str, scope: str = 'vendor:read') -> Connection:
    token = (
        TokenPair.objects.select_related('connection__vendor__user')
        .filter(
            access_digest=digest(raw),
            revoked_at__isnull=True,
            access_expires_at__gt=timezone.now(),
        )
        .first()
    )
    if not token:
        raise PermissionDenied('توکن نامعتبر یا منقضی است.')
    connection = token.connection
    eligible(connection)
    if scope not in connection.scopes.split():
        raise PermissionDenied('مجوز این عملیات داده نشده است.')
    Connection.objects.filter(pk=connection.pk).update(last_used_at=timezone.now())
    return connection


def issue_tokens(connection: Connection) -> dict[str, object]:
    access = secrets.token_urlsafe(48)
    refresh = (
        secrets.token_urlsafe(48)
        if 'offline_access' in connection.scopes.split()
        else None
    )
    TokenPair.objects.create(
        connection=connection,
        access_digest=digest(access),
        refresh_digest=digest(refresh) if refresh else None,
        access_expires_at=timezone.now() + timedelta(hours=1),
        refresh_expires_at=timezone.now() + timedelta(days=30),
    )
    result: dict[str, object] = {
        'access_token': access,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': connection.scopes,
    }
    if refresh:
        result['refresh_token'] = refresh
    return result


@transaction.atomic
def exchange_code(data: dict[str, str]) -> dict[str, object]:
    code = (
        AuthorizationCode.objects.select_for_update()
        .filter(digest=digest(data.get('code', '')))
        .first()
    )
    if not code or code.consumed_at or code.expires_at <= timezone.now():
        raise ValidationError('invalid_grant')
    connection = Connection.objects.select_for_update().get(pk=code.connection_id)
    eligible(connection)
    verifier = data.get('code_verifier', '')
    import re

    if not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}', verifier):
        raise ValidationError('invalid_grant')
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip('=')
    )
    if (
        not secrets.compare_digest(challenge, code.challenge)
        or data.get('client_id') != str(connection.client_id)
        or data.get('redirect_uri') != code.redirect_uri
        or data.get('resource') != code.resource
    ):
        raise ValidationError('invalid_grant')
    code.consumed_at = timezone.now()
    code.save(update_fields=['consumed_at'])
    return issue_tokens(connection)


@transaction.atomic
def refresh_tokens(data: dict[str, str]) -> dict[str, object]:
    # Revocation and refresh lock the connection before its tokens.
    candidate = TokenPair.objects.filter(
        refresh_digest=digest(data.get('refresh_token', ''))
    ).first()
    if not candidate:
        raise ValidationError('invalid_grant')
    connection = Connection.objects.select_for_update().get(pk=candidate.connection_id)
    token = TokenPair.objects.select_for_update().get(pk=candidate.pk)
    eligible(connection)
    if (
        token.revoked_at
        or token.refresh_expires_at <= timezone.now()
        or data.get('client_id') != str(connection.client_id)
        or data.get('resource') != origin() + '/mcp/'
        or data.get('scope', connection.scopes) != connection.scopes
    ):
        raise ValidationError('invalid_grant')
    token.revoked_at = timezone.now()
    token.save(update_fields=['revoked_at'])
    return issue_tokens(connection)


@transaction.atomic
def revoke(connection: Connection) -> None:
    locked = Connection.objects.select_for_update().get(pk=connection.pk)
    locked.revoked_at = timezone.now()
    locked.save(update_fields=['revoked_at'])
    TokenPair.objects.filter(connection=locked, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
