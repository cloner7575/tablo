from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, RequestFactory
from django.urls import reverse

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
def test_quote_price_not_editable_by_customer_api(
    client: Client, customer, vendor, project_request
):
    quote = create_quote(
        vendor=vendor,
        project_request=project_request,
        price=10_000_000,
        estimated_delivery_days=4,
    )
    client.force_login(customer)
    url = reverse("api:v1:quote-detail", kwargs={"pk": quote.pk})
    response = client.patch(url, data={"price": 1}, content_type="application/json")
    assert response.status_code in (403, 405)
    quote.refresh_from_db()
    assert quote.price == 10_000_000
