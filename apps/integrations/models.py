import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.deconstruct import deconstructible

from apps.common.models import TimeStampedModel


@deconstructible
class PrivateStorage(FileSystemStorage):
    def __init__(self) -> None:
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name: str) -> str:
        raise ValueError('Private images require an authenticated download.')


class OAuthClient(TimeStampedModel):
    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4)
    name = models.CharField(max_length=150)
    redirect_uris = models.JSONField(default=list)


class Connection(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE)
    client = models.ForeignKey(OAuthClient, on_delete=models.CASCADE)
    scopes = models.CharField(
        max_length=200, default='vendor:read vendor:write offline_access'
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)


class AuthorizationCode(TimeStampedModel):
    digest = models.CharField(max_length=64, unique=True)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    redirect_uri = models.URLField(max_length=2000)
    challenge = models.CharField(max_length=128)
    resource = models.URLField(max_length=2000)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True)


class TokenPair(TimeStampedModel):
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    access_digest = models.CharField(max_length=64, unique=True)
    refresh_digest = models.CharField(max_length=64, unique=True, null=True)
    access_expires_at = models.DateTimeField()
    refresh_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)


class DesignAsset(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    image = models.ImageField(storage=PrivateStorage(), upload_to='designs/%Y/%m/')
    order = models.ForeignKey(
        'orders.Order', null=True, blank=True, on_delete=models.SET_NULL
    )
    portfolio = models.ForeignKey(
        'portfolio.PortfolioItem', null=True, blank=True, on_delete=models.SET_NULL
    )
    provenance = models.CharField(max_length=40, default='ai_concept', editable=False)


class Operation(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    kind = models.CharField(max_length=40)
    payload = models.JSONField()
    expires_at = models.DateTimeField()
    executed_at = models.DateTimeField(null=True)
    result = models.JSONField(default=dict)
    target_version = models.CharField(max_length=64, blank=True)


class AuditEvent(TimeStampedModel):
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    action = models.CharField(max_length=80)
    object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def get_action_label(self) -> str:
        return {
            "save_design": "ذخیره تصویر خصوصی",
            "quote": "ارسال پیشنهاد قیمت",
            "message": "ارسال پیام",
            "design": "ارسال طرح",
            "stage": "تغییر مرحله پروژه",
            "profile": "ویرایش پروفایل",
            "portfolio": "ویرایش نمونه‌کار",
            "publish": "تغییر انتشار نمونه‌کار",
        }.get(self.action, "فعالیت دستیار")


class PendingConsent(TimeStampedModel):
    digest = models.CharField(max_length=64, unique=True)
    vendor = models.ForeignKey('vendors.Vendor', on_delete=models.CASCADE)
    consumed_at = models.DateTimeField(null=True)
