from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.catalog.models import Service
from apps.common.persian import format_relative
from apps.locations.models import City, Province
from apps.quotes.services import create_quote
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.vendors.models import Vendor, VerificationStatus

User = get_user_model()
URL = reverse("vendors:requests")


@pytest.fixture
def city(db):
    province = Province.objects.create(name="تهران", slug="tehran")
    return City.objects.create(name="تهران", slug="tehran", province=province)


@pytest.fixture
def chalnium(db):
    return Service.objects.create(title="چلنیوم", slug="chalnium", sort_order=1)


@pytest.fixture
def neon(db):
    return Service.objects.create(title="نئون", slug="neon", sort_order=2)


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="09121111111",
        phone="09121111111",
        role=UserRole.CUSTOMER,
        password="x",
    )


def _vendor(phone: str, city: City, *services: Service, approved: bool = True):
    user = User.objects.create_user(
        username=phone, phone=phone, role=UserRole.VENDOR, password="x"
    )
    vendor = Vendor.objects.create(
        user=user,
        business_name=f"تابلوساز {phone[-2:]}",
        slug=f"vendor-{phone[-2:]}",
        city=city,
        phone=phone,
        verification_status=(
            VerificationStatus.APPROVED if approved else VerificationStatus.PENDING
        ),
        is_active=True,
    )
    vendor.services.add(*services)
    return vendor


@pytest.fixture
def vendor(city, chalnium, neon):
    return _vendor("09122222222", city, chalnium, neon)


def _request(customer, city, service=None, **extra) -> ProjectRequest:
    defaults = {
        "title": "تابلو مغازه",
        "width_cm": 300,
        "height_cm": 80,
        "lighting_type": LightingType.LED,
        "status": RequestStatus.RECEIVING_QUOTES,
    }
    defaults.update(extra)
    return ProjectRequest.objects.create(
        customer=customer, city=city, service=service, **defaults
    )


def _quote(vendor, project_request):
    return create_quote(
        vendor=vendor,
        project_request=project_request,
        price=10_000_000,
        estimated_delivery_days=7,
    )


def _get(client: Client, vendor, **params):
    client.force_login(vendor.user)
    return client.get(URL, params)


@pytest.mark.django_db
def test_default_tab_shows_only_requests_without_my_quote(
    client, vendor, customer, city, chalnium
):
    open_req = _request(customer, city, chalnium, title="تابلو باز")
    quoted_req = _request(customer, city, chalnium, title="تابلو پاسخ‌داده")
    _quote(vendor, quoted_req)

    response = _get(client, vendor)

    assert response.status_code == 200
    body = response.content.decode()
    assert open_req.title in body
    assert quoted_req.title not in body
    tabs = {tab["key"]: tab for tab in response.context["status_tabs"]}
    assert (tabs["open"]["count"], tabs["quoted"]["count"], tabs["all"]["count"]) == (
        1,
        1,
        2,
    )
    assert tabs["open"]["current"]


@pytest.mark.django_db
def test_quoted_tab_marks_my_quote(client, vendor, customer, city, chalnium):
    _request(customer, city, chalnium, title="تابلو باز")
    quoted_req = _request(customer, city, chalnium, title="تابلو پاسخ‌داده")
    _quote(vendor, quoted_req)

    body = _get(client, vendor, status="quoted").content.decode()

    assert quoted_req.title in body
    assert "تابلو باز" not in body
    assert "پیشنهاد داده‌اید" in body


@pytest.mark.django_db
def test_unknown_status_falls_back_to_open(client, vendor, customer, city, chalnium):
    _request(customer, city, chalnium)
    response = _get(client, vendor, status="<script>")
    assert response.status_code == 200
    assert response.context["status"] == "open"


@pytest.mark.django_db
def test_service_chip_filters_and_ignores_foreign_slug(
    client, vendor, customer, city, chalnium, neon
):
    _request(customer, city, chalnium, title="کار چلنیوم")
    _request(customer, city, neon, title="کار نئون")
    other = Service.objects.create(title="استیل", slug="steel", sort_order=3)

    body = _get(client, vendor, service="neon").content.decode()
    assert "کار نئون" in body
    assert "کار چلنیوم" not in body

    response = _get(client, vendor, service=other.slug)
    assert response.context["service"] == ""
    assert "کار چلنیوم" in response.content.decode()

    chips = [chip["label"] for chip in response.context["service_filters"]]
    assert chips[:3] == ["همه", "چلنیوم", "نئون"]


@pytest.mark.django_db
def test_guidance_chip_lists_requests_without_service(
    client, vendor, customer, city, chalnium
):
    _request(customer, city, chalnium, title="کار چلنیوم")
    _request(customer, city, None, title="نمی‌دانم چه تابلویی", needs_guidance=True)

    body = _get(client, vendor, service="guidance").content.decode()

    assert "نمی‌دانم چه تابلویی" in body
    assert "کار چلنیوم" not in body


@pytest.mark.django_db
def test_card_shows_competition_budget_and_persian_digits(
    client, vendor, customer, city, chalnium
):
    rival = _vendor("09123333333", city, chalnium)
    busy = _request(
        customer,
        city,
        chalnium,
        title="پرطرفدار",
        budget_min=5_000_000,
        budget_max=9_000_000,
    )
    _quote(rival, busy)
    _request(customer, city, chalnium, title="فقط سقف", budget_max=4_000_000)
    _request(customer, city, chalnium, title="بی‌بودجه")

    body = _get(client, vendor).content.decode()

    assert "۱ پیشنهاد" in body
    assert "اولین پیشنهاد را شما بدهید" in body
    assert "۵٬۰۰۰٬۰۰۰ تا ۹٬۰۰۰٬۰۰۰ تومان" in body
    assert "تا ۴٬۰۰۰٬۰۰۰ تومان" in body
    assert "توافقی" in body
    assert " ۰ تومان تا" not in body
    assert "۳۰۰ × ۸۰" in body


@pytest.mark.django_db
def test_card_flags_preferred_vendor_and_near_deadline(
    client, vendor, customer, city, chalnium
):
    _request(
        customer,
        city,
        chalnium,
        title="انتخاب مستقیم",
        preferred_vendor=vendor,
        deadline=timezone.localdate() + timedelta(days=3),
    )

    body = _get(client, vendor).content.decode()

    assert "شما را انتخاب کرده" in body
    assert "فوری" in body


@pytest.mark.django_db
def test_deadline_is_near_property(customer, city):
    today = timezone.localdate()
    assert _request(customer, city, deadline=today + timedelta(days=7)).deadline_is_near
    assert not _request(
        customer, city, deadline=today + timedelta(days=8)
    ).deadline_is_near
    assert not _request(customer, city).deadline_is_near


@pytest.mark.django_db
def test_empty_states(client, vendor, customer, city, chalnium):
    body = _get(client, vendor).content.decode()
    assert "فعلاً درخواست تازه‌ای نیست" in body

    quoted = _request(customer, city, chalnium)
    _quote(vendor, quoted)
    body = _get(client, vendor).content.decode()
    assert "به همه درخواست‌ها پیشنهاد داده‌اید" in body

    body = _get(client, vendor, service="guidance").content.decode()
    assert "با این فیلتر درخواستی نیست" in body


@pytest.mark.django_db
def test_pending_vendor_sees_approval_state(client, city, chalnium):
    pending = _vendor("09124444444", city, chalnium, approved=False)
    body = _get(client, pending).content.decode()
    assert "بعد از تأیید پروفایل" in body


@pytest.mark.django_db
def test_request_feed_query_count_is_flat(client, vendor, customer, city, chalnium):
    def queries() -> int:
        client.force_login(vendor.user)
        with CaptureQueriesContext(connection) as ctx:
            assert client.get(URL, {"status": "all"}).status_code == 200
        return len(ctx)

    for _ in range(2):
        _quote(vendor, _request(customer, city, chalnium))
    baseline = queries()
    for _ in range(4):
        _request(customer, city, chalnium)
    assert queries() == baseline


def test_format_relative():
    now = timezone.now()
    assert format_relative(now, now=now) == "همین حالا"
    assert format_relative(now - timedelta(minutes=5), now=now) == "۵ دقیقه پیش"
    assert format_relative(now - timedelta(hours=3), now=now) == "۳ ساعت پیش"
    assert format_relative(now - timedelta(days=1, hours=2), now=now) == "دیروز"
    assert format_relative(now - timedelta(days=4), now=now) == "۴ روز پیش"
    assert "/" in format_relative(now - timedelta(days=30), now=now)
    assert format_relative(None) == ""


def _detail(client: Client, vendor, pk: int):
    client.force_login(vendor.user)
    return client.get(reverse("vendors:request_detail", kwargs={"pk": pk}))


@pytest.mark.django_db
def test_detail_shows_tags_budget_and_competition(
    client, vendor, customer, city, chalnium
):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    from apps.requests.models import RequestImage

    rival = _vendor("09125555555", city, chalnium)
    req = _request(
        customer,
        city,
        chalnium,
        title="جزئیات کامل",
        preferred_vendor=vendor,
        budget_max=7_500_000,
        deadline=timezone.localdate() + timedelta(days=2),
        text_content="نانوایی آفتاب",
        district="جردن",
        description="سردر روشن می‌خواهم.",
    )
    _quote(rival, req)
    buf = BytesIO()
    Image.new("RGB", (40, 40), (10, 20, 30)).save(buf, format="JPEG")
    RequestImage.objects.create(
        request=req,
        image=SimpleUploadedFile("d.jpg", buf.getvalue(), content_type="image/jpeg"),
    )

    body = _detail(client, vendor, req.pk).content.decode()

    assert "vp-brief" in body
    assert "شما را انتخاب کرده" in body
    assert "فوری" in body
    assert "تا ۷٬۵۰۰٬۰۰۰ تومان" in body
    assert " ۰ تومان تا" not in body
    assert "۱ پیشنهاد ثبت شده" in body
    assert "نانوایی آفتاب" in body
    assert "جردن" in body
    assert "عکس‌های مشتری" in body
    assert "بررسی و ارسال پیشنهاد" in body
    assert reverse("vendors:request_quote", kwargs={"pk": req.pk}) in body
    assert "ثبت و ارسال پیشنهاد" not in body


@pytest.mark.django_db
def test_detail_existing_quote_hides_cta(client, vendor, customer, city, chalnium):
    req = _request(customer, city, chalnium, title="قبلاً پاسخ داده‌ام")
    _quote(vendor, req)

    body = _detail(client, vendor, req.pk).content.decode()

    assert "پیشنهاد شما ثبت شده" in body
    assert "۱۰٬۰۰۰٬۰۰۰ تومان" in body
    assert "بررسی و ارسال پیشنهاد" not in body
    assert reverse("vendors:my_quotes") in body


@pytest.mark.django_db
def test_detail_unknown_request_is_404(client, vendor):
    assert _detail(client, vendor, 999_999).status_code == 404
