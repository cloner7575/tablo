from io import BytesIO

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.urls import reverse
from PIL import Image

from apps.accounts.models import PhoneOTP, UserRole
from apps.accounts.services import request_otp, verify_otp_and_login
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.orders.services import complete_order, create_review
from apps.quotes.services import accept_quote, create_quote
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.requests.services import submit_project_request
from apps.vendors.models import Vendor, VerificationStatus

User = get_user_model()


@pytest.fixture
def province(db):
    return Province.objects.create(name="تهران", slug="tehran")


@pytest.fixture
def city(province):
    return City.objects.create(name="تهران", slug="tehran", province=province)


@pytest.fixture
def service(db):
    return Service.objects.create(title="چلنیوم", slug="chalnium", sort_order=1)


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="09121111111",
        phone="09121111111",
        role=UserRole.CUSTOMER,
        is_verified=True,
        password="x",
    )


@pytest.fixture
def vendor_user(db):
    return User.objects.create_user(
        username="09122222222",
        phone="09122222222",
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )


@pytest.fixture
def vendor(vendor_user, city, service):
    v = Vendor.objects.create(
        user=vendor_user,
        business_name="سپهراد",
        slug="sepehrad",
        city=city,
        phone="09122222222",
        verification_status=VerificationStatus.APPROVED,
        is_active=True,
    )
    v.services.add(service)
    return v


@pytest.fixture
def project_request(customer, city, service):
    req = ProjectRequest.objects.create(
        customer=customer,
        title="تابلو مغازه",
        service=service,
        city=city,
        width_cm=300,
        height_cm=80,
        lighting_type=LightingType.LED,
        status=RequestStatus.DRAFT,
    )
    return submit_project_request(project_request=req)


@pytest.mark.django_db
def test_otp_login_creates_user(client: Client):
    otp = request_otp(phone="09123334444")
    assert PhoneOTP.objects.filter(phone="09123334444").exists()
    rf = RequestFactory()
    req = rf.post("/")
    req.session = client.session
    user = verify_otp_and_login(
        request=req, phone="09123334444", code=otp.code, purpose="login"
    )
    assert user.phone == "09123334444"
    assert user.is_verified


@pytest.mark.django_db
def test_duplicate_quote_prevented(vendor, project_request):
    create_quote(
        vendor=vendor,
        project_request=project_request,
        price=10_000_000,
        estimated_delivery_days=7,
    )
    with pytest.raises(ValidationError):
        create_quote(
            vendor=vendor,
            project_request=project_request,
            price=11_000_000,
            estimated_delivery_days=8,
        )


@pytest.mark.django_db
def test_vendor_cannot_access_unmatched_request(vendor, customer, city):
    other = Service.objects.create(title="نئون", slug="neon")
    req = ProjectRequest.objects.create(
        customer=customer,
        service=other,
        city=city,
        status=RequestStatus.RECEIVING_QUOTES,
        title="نئون",
    )
    with pytest.raises(PermissionDenied):
        create_quote(
            vendor=vendor,
            project_request=req,
            price=1_000_000,
            estimated_delivery_days=3,
        )


@pytest.mark.django_db
def test_accept_quote_creates_order(customer, vendor, project_request):
    quote = create_quote(
        vendor=vendor,
        project_request=project_request,
        price=18_500_000,
        estimated_delivery_days=7,
        warranty="12 ماه",
    )
    order = accept_quote(quote=quote, user=customer)
    assert order.agreed_price == 18_500_000
    project_request.refresh_from_db()
    assert project_request.status == RequestStatus.ACCEPTED


@pytest.mark.django_db
def test_review_only_after_completed(customer, vendor, project_request):
    quote = create_quote(
        vendor=vendor,
        project_request=project_request,
        price=9_000_000,
        estimated_delivery_days=5,
    )
    order = accept_quote(quote=quote, user=customer)
    with pytest.raises(ValidationError):
        create_review(
            user=customer,
            project_request=project_request,
            rating=5,
            comment="عالی",
        )
    complete_order(order=order, user=customer)
    project_request.refresh_from_db()
    review = create_review(
        user=customer,
        project_request=project_request,
        rating=5,
        comment="عالی",
    )
    assert review.rating == 5
    vendor.refresh_from_db()
    assert vendor.review_count == 1


@pytest.mark.django_db
def test_api_requests_requires_auth(client: Client):
    url = reverse("api:v1:request-list")
    response = client.get(url)
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_portfolio_detail_shows_hero_vendor_and_cta(
    client: Client, vendor, service, city
):
    from apps.portfolio.models import PortfolioItem

    item = PortfolioItem.objects.create(
        vendor=vendor,
        title="تابلو نئون کافه ساحل",
        slug="cafe-sahel-neon",
        description="اجرای تابلو نئون سردر با نورپردازی شبانه برای کافه ساحل.",
        service=service,
        city=city,
        is_published=True,
    )
    response = client.get(reverse("portfolio:detail", kwargs={"slug": item.slug}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "تابلو نئون کافه ساحل" in body
    assert vendor.business_name in body
    assert "درخواست قیمت مشابه" in body
    assert 'class="pf-detail"' in body
    assert "pf-hero--compact" in body
    assert "img/demo/" in body or "portfolio/" in body


@pytest.mark.django_db
def test_wizard_shell_shows_named_steps(client: Client, service, city):
    response = client.get(reverse("requests:wizard_service"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "wz-shell" in body
    assert "نوع تابلو" in body
    assert "مرحله" in body


@pytest.mark.django_db
def test_request_detail_uses_rich_layout(
    client: Client, customer, vendor, project_request
):
    create_quote(
        vendor=vendor,
        project_request=project_request,
        price=12_000_000,
        estimated_delivery_days=6,
        warranty="۱۲ ماه",
    )
    client.force_login(customer)
    response = client.get(
        reverse("requests:request_detail", kwargs={"pk": project_request.pk})
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "req-detail" in body
    assert "پیشنهادهای دریافتی" in body
    assert vendor.business_name in body


def _jpeg_upload(name: str = "site.jpg") -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (80, 60), (40, 40, 40)).save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


@pytest.mark.django_db
def test_wizard_accepts_multiple_request_photos(client: Client, service, city):
    from apps.requests.models import RequestImage

    session = client.session
    session["request_wizard"] = {
        "service_id": service.pk,
        "city_id": city.pk,
        "width_cm": 200,
        "height_cm": 60,
        "lighting_type": LightingType.LED,
        "description": "سردر مغازه میوه",
    }
    session.save()

    response = client.post(
        reverse("requests:wizard_image"),
        data={
            "images": [
                _jpeg_upload("a.jpg"),
                _jpeg_upload("b.jpg"),
            ]
        },
    )
    assert response.status_code == 302
    draft_id = client.session["request_wizard"]["draft_id"]
    assert RequestImage.objects.filter(request_id=draft_id).count() == 2


@pytest.mark.django_db
def test_request_detail_shows_photo_gallery_and_brief(
    client: Client, customer, project_request
):
    from apps.requests.models import RequestImage

    project_request.description = "لوگوی سفید روی زمینه مشکی می‌خواهم"
    project_request.text_content = "فروشگاه گل یاس"
    project_request.district = "ونک"
    project_request.business_type = "گل‌فروشی"
    project_request.save()
    RequestImage.objects.create(
        request=project_request, image=_jpeg_upload("one.jpg"), sort_order=0
    )
    RequestImage.objects.create(
        request=project_request, image=_jpeg_upload("two.jpg"), sort_order=1
    )

    client.force_login(customer)
    response = client.get(
        reverse("requests:request_detail", kwargs={"pk": project_request.pk})
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "req-brief" in body
    assert "فروشگاه گل یاس" in body
    assert "لوگوی سفید" in body
    assert "req-gallery" in body
    assert body.count('class="req-gallery__item"') >= 2


@pytest.mark.django_db
def test_vendor_request_detail_shows_customer_photos(
    client: Client, vendor, vendor_user, project_request
):
    from apps.requests.models import RequestImage

    RequestImage.objects.create(
        request=project_request, image=_jpeg_upload("v.jpg"), sort_order=0
    )
    client.force_login(vendor_user)
    response = client.get(
        reverse("vendors:request_detail", kwargs={"pk": project_request.pk})
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "vp-req-brief" in body
    assert "vp-req-photos" in body
    assert "عکس‌های مشتری" in body
    assert "vp-req-specs" in body
    assert "ارسال پیشنهاد" in body
    assert "ثبت و ارسال پیشنهاد" not in body
    assert reverse("vendors:request_quote", kwargs={"pk": project_request.pk}) in body


@pytest.mark.django_db
def test_vendor_quote_page_after_viewing_request(
    client: Client, vendor, vendor_user, project_request
):
    client.force_login(vendor_user)
    detail = client.get(
        reverse("vendors:request_detail", kwargs={"pk": project_request.pk})
    )
    assert detail.status_code == 200
    assert "ارسال پیشنهاد" in detail.content.decode()

    quote_page = client.get(
        reverse("vendors:request_quote", kwargs={"pk": project_request.pk})
    )
    assert quote_page.status_code == 200
    body = quote_page.content.decode()
    assert "پیشنهاد قیمت شما" in body
    assert "ثبت و ارسال پیشنهاد" in body
    assert "بازگشت به جزئیات" in body


@pytest.mark.django_db
def test_wizard_service_offers_unsure_path(client: Client, service):
    response = client.get(reverse("requests:wizard_service"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "نمی‌دانم" in body
    assert "wz-cards" in body
    assert service.title in body


@pytest.mark.django_db
def test_unsure_request_matches_any_vendor_in_city(vendor, customer, city, vendor_user):
    from apps.requests.selectors import matched_requests_for_vendor

    req = ProjectRequest.objects.create(
        customer=customer,
        city=city,
        service=None,
        needs_guidance=True,
        description="مغازه میوه دارم، تابلو می‌خوام ولی نوعش را نمی‌دانم",
        status=RequestStatus.RECEIVING_QUOTES,
        title="درخواست راهنمایی تابلو — تهران",
    )
    matched = list(matched_requests_for_vendor(vendor))
    assert req in matched


@pytest.mark.django_db
def test_wizard_accepts_unsure_size_and_lighting(client: Client, service, city):
    session = client.session
    session["request_wizard"] = {
        "service_id": service.pk,
        "city_id": city.pk,
    }
    session.save()

    response = client.post(
        reverse("requests:wizard_dimensions"),
        data={"size_choice": "unsure"},
    )
    assert response.status_code == 302
    data = client.session["request_wizard"]
    assert data.get("size_choice") == "unsure"
    assert data.get("width_cm") is None

    response = client.post(
        reverse("requests:wizard_lighting"),
        data={"lighting_type": LightingType.UNSURE},
    )
    assert response.status_code == 302
    assert client.session["request_wizard"]["lighting_type"] == LightingType.UNSURE


@pytest.mark.django_db
def test_vendor_dashboard_panel_shell(client: Client, vendor, vendor_user):
    client.force_login(vendor_user)
    response = client.get(reverse("vendors:dashboard"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "vp-shell" in body
    assert "vp-nav" in body
    assert vendor.business_name in body
    assert "درخواست بدون پیشنهاد" in body


@pytest.mark.django_db
def test_vendor_list_shows_rich_cards(client: Client, vendor):
    response = client.get(reverse("vendors:list"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "vn-list" in body
    assert vendor.business_name in body
    assert "vn-card" in body


@pytest.mark.django_db
def test_vendor_public_shows_rich_profile(client: Client, vendor, service):
    response = client.get(reverse("vendors:public", kwargs={"slug": vendor.slug}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "vn-profile" in body
    assert "vn-hero--compact" in body
    assert vendor.business_name in body
    assert "درخواست قیمت از این تابلو‌ساز" in body
    assert service.title in body


@pytest.mark.django_db
def test_home_ok(client: Client):
    response = client.get(reverse("common:home"))
    assert response.status_code == 200
    assert "قیمت بگیر" in response.content.decode()


@pytest.mark.django_db
def test_unicode_vendor_slug_reverses_and_resolves(client: Client, vendor):
    vendor.slug = "چلنیوم-پارس"
    vendor.save(update_fields=["slug"])
    url = reverse("vendors:public", kwargs={"slug": vendor.slug})
    assert "/vendors/" in url
    response = client.get(url)
    assert response.status_code == 200
    assert vendor.business_name in response.content.decode()


@pytest.mark.django_db
def test_pending_vendor_hidden_from_list_and_public(client: Client, city, service):
    pending_user = User.objects.create_user(
        username="09128880001",
        phone="09128880001",
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )
    pending = Vendor.objects.create(
        user=pending_user,
        business_name="در انتظار تأیید",
        slug="pending-vendor",
        city=city,
        phone="09128880001",
        verification_status=VerificationStatus.PENDING,
        is_active=True,
    )
    pending.services.add(service)

    list_body = client.get(reverse("vendors:list")).content.decode()
    assert pending.business_name not in list_body

    response = client.get(reverse("vendors:public", kwargs={"slug": pending.slug}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_service_page_shows_catalog_content(client: Client, service, vendor):
    service.suitable_for = "مغازه، بوتیک و سردر فروشگاهی"
    service.materials = "چلنیوم، پلکسی، نورپردازی LED"
    service.faq = [
        {"question": "چلنیوم برای کجا مناسب است؟", "answer": "سردر مغازه و برندینگ."}
    ]
    service.save()
    Service.objects.create(title="نئون", slug="neon-related", is_active=True)

    response = client.get(reverse("catalog:service", kwargs={"slug": service.slug}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "svc-page" in body
    assert "svc-hero__visual" in body
    assert "مغازه، بوتیک و سردر فروشگاهی" in body
    assert "چلنیوم، پلکسی، نورپردازی LED" in body
    assert "چلنیوم برای کجا مناسب است؟" in body
    assert vendor.business_name in body
    assert "برای این نوع تابلو قیمت بگیر" in body
    assert "svc-related" in body
    assert "نئون" in body


@pytest.mark.django_db
def test_city_page_shows_conversion_layout(client: Client, city, vendor, service):
    response = client.get(reverse("catalog:city", kwargs={"slug": city.slug}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "city-page" in body
    assert city.name in body
    assert vendor.business_name in body
    assert "vn-card" in body
    assert service.title in body


@pytest.mark.django_db
def test_vendor_onboarding_accepts_cover(client: Client, city, service):
    fresh = User.objects.create_user(
        username="09129990001",
        phone="09129990001",
        role=UserRole.VENDOR,
        is_verified=True,
        password="x",
    )
    client.force_login(fresh)
    cover = _jpeg_upload("cover.jpg")
    response = client.post(
        reverse("vendors:onboarding"),
        data={
            "business_name": "کارگاه تست",
            "description": "توضیحات کافی برای پروفایل",
            "phone": "09129990001",
            "city": city.pk,
            "address": "تهران",
            "instagram": "@test",
            "website": "",
            "years_of_experience": 3,
            "services": [service.pk],
            "cover_image": cover,
        },
    )
    assert response.status_code == 302
    created = Vendor.objects.get(user=fresh)
    assert created.verification_status == VerificationStatus.PENDING
    assert bool(created.cover_image)
