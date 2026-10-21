"""Bounded HTTPS downloads pinned to a validated public IP, with real image decoding."""

import http.client
import ipaddress
import socket
import ssl
import uuid
from io import BytesIO
from time import monotonic
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict


class ChatGPTFile(BaseModel):
    model_config = ConfigDict(extra='forbid')
    download_url: str
    file_id: str
    mime_type: str | None = None
    file_name: str | None = None


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str) -> None:
        super().__init__(host, timeout=15, context=ssl.create_default_context())
        self.address = address

    def connect(self) -> None:
        raw = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def normalize_image(content: bytes) -> SimpleUploadedFile:
    if len(content) > settings.IMAGE_UPLOAD_MAX_BYTES:
        raise ValidationError('حجم تصویر بیش از حد مجاز است.')
    try:
        with Image.open(BytesIO(content)) as image:
            if (
                image.format not in {'JPEG', 'PNG', 'WEBP'}
                or image.width * image.height > 25_000_000
            ):
                raise ValidationError('فرمت یا ابعاد تصویر مجاز نیست.')
            image.verify()
        with Image.open(BytesIO(content)) as image:
            output = BytesIO()
            image.convert('RGB').save(output, format='PNG')
        result = output.getvalue()
        if len(result) > settings.IMAGE_UPLOAD_MAX_BYTES:
            raise ValidationError('حجم تصویر پردازش‌شده بیش از حد مجاز است.')
        return SimpleUploadedFile(
            f'{uuid.uuid4().hex}.png', result, content_type='image/png'
        )
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationError('فایل تصویر معتبر نیست.') from exc


def download_image(file: ChatGPTFile) -> SimpleUploadedFile:
    url = urlsplit(file.download_url)
    if (
        url.scheme != 'https'
        or not url.hostname
        or url.port not in {None, 443}
        or url.username
        or url.password
        or url.fragment
        or len(file.download_url) > 8000
    ):
        raise ValidationError('نشانی فایل معتبر نیست.')
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(url.hostname, 443, type=socket.SOCK_STREAM)
        }
        if not addresses or any(
            not ipaddress.ip_address(ip).is_global for ip in addresses
        ):
            raise ValidationError('نشانی خصوصی یا داخلی مجاز نیست.')
        connection = PinnedHTTPS(url.hostname, sorted(addresses)[0])
        try:
            connection.request('GET', url.path + ('?' + url.query if url.query else ''))
            response = connection.getresponse()
            # Never follow redirects or forward OAuth credentials to a file host.
            if response.status != 200:
                raise ValidationError(
                    'فایل در دسترس نیست؛ تصویر را دوباره انتخاب کنید.'
                )
            chunks: list[bytes] = []
            total = 0
            deadline = monotonic() + 20
            while total <= settings.IMAGE_UPLOAD_MAX_BYTES:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise ValidationError('زمان دریافت تصویر تمام شد.')
                if connection.sock:
                    connection.sock.settimeout(min(15, remaining))
                chunk = response.read1(
                    min(65536, settings.IMAGE_UPLOAD_MAX_BYTES + 1 - total)
                )
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            content = b''.join(chunks)
        finally:
            connection.close()
    except (OSError, http.client.HTTPException) as exc:
        raise ValidationError('دریافت تصویر انجام نشد؛ دوباره تلاش کنید.') from exc
    return normalize_image(content)
