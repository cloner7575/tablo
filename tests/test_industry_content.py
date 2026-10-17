"""Public source projects must never impersonate registered marketplace vendors."""

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.catalog.models import Service
from apps.common.industry_services import refresh_industry_content
from apps.locations.models import City, Province
from apps.orders.models import Order
from apps.portfolio.models import PortfolioItem
from apps.portfolio.selectors import discoverable_items
from apps.vendors.models import Vendor


@pytest.fixture
def reference_project() -> PortfolioItem:
    return PortfolioItem.objects.create(
        title="تابلو استیل گراد",
        slug="reference-gerad",
        vendor=None,
        image="industry/gerad.webp",
        source_name="نوین گرافیک",
        source_url="https://novin-graphics.com/",
        source_image_url="https://novin-graphics.com/gerad.webp",
        description="نمونهٔ منتشرشده در وب‌سایت سازنده.",
    )


@pytest.mark.django_db
def test_source_project_is_discoverable_without_a_marketplace_account(
    client, reference_project, django_assert_num_queries
) -> None:
    assert not User.objects.exists()
    with django_assert_num_queries(1):
        projects = list(discoverable_items())
        assert projects[0].source_name == "نوین گرافیک"
        assert projects[0].vendor is None
    html = client.get(
        reverse("portfolio:detail", args=[reference_project.slug])
    ).content.decode()
    assert "https://novin-graphics.com/" not in html
    assert "نوین گرافیک" not in html
    assert "منبع اصلی" not in html
    assert "/request/vendor/" not in html
    assert '"creator"' not in html


@pytest.mark.django_db
def test_reference_requires_a_creator_source_and_an_image() -> None:
    item = PortfolioItem(title="بدون منبع", slug="without-source", vendor=None)
    with pytest.raises(ValidationError):
        item.full_clean()


@pytest.mark.django_db
def test_source_projects_can_be_saved_and_filtered_by_creator(
    client, reference_project
) -> None:
    page = client.get(reverse("portfolio:list"), {"q": "نوین گرافیک"})
    assert "تابلو استیل گراد" in page.content.decode()
    response = client.post(
        reverse("portfolio:board_toggle", args=[reference_project.pk]),
        {"action": "add", "destination": "gallery"},
    )
    assert response.status_code == 302
    assert reference_project.pk in client.session["inspiration_board"]
    detail = client.post(
        reverse("portfolio:board_toggle", args=[reference_project.pk]),
        {"action": "remove", "destination": "detail"},
    )
    assert detail.url == reverse("portfolio:detail", args=[reference_project.slug])


@pytest.mark.django_db
def test_rating_sort_does_not_put_unrated_external_sources_first(
    client, reference_project
) -> None:
    province = Province.objects.create(name="تهران", slug="tehran")
    city = City.objects.create(name="تهران", slug="tehran", province=province)
    user = User.objects.create(username="member")
    vendor = Vendor.objects.create(
        user=user,
        business_name="عضو",
        city=city,
        verification_status="approved",
        rating=4,
    )
    item = PortfolioItem.objects.create(vendor=vendor, title="نمونهٔ عضو")
    response = client.get(reverse("portfolio:list"), {"sort": "maker"})
    assert response.context["page_obj"].object_list[0].pk == item.pk


@pytest.mark.django_db
def test_site_seed_works_on_an_empty_database_and_is_repeatable() -> None:
    call_command("seed_site")
    call_command("seed_site")
    assert Service.objects.filter(is_active=True).count() == 12
    assert PortfolioItem.objects.filter(vendor__isnull=True).count() == 11
    assert City.objects.get(slug="tehran").province.slug == "tehran"
    assert City.objects.count() == 3
    assert not User.objects.exists()
    assert not Vendor.objects.exists()
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_import_is_repeatable_and_creates_no_fake_accounts_or_orders() -> None:
    call_command("import_industry_content")
    call_command("import_industry_content")
    assert PortfolioItem.objects.filter(vendor__isnull=True).count() == 11
    assert Service.objects.filter(is_active=True).count() == 12
    assert not User.objects.exists()
    assert not Vendor.objects.exists()
    assert not Order.objects.exists()
    assert City.objects.get(slug="karaj").province.slug == "alborz"
    assert Service.objects.get(slug="led").title == "تابلو ال‌ای‌دی و روان"


@pytest.mark.django_db
def test_public_seed_pages_do_not_publish_source_links(client) -> None:
    call_command("import_industry_content")
    routes = ["common:home", "portfolio:list", "catalog:services", "vendors:list"]
    for route in routes:
        response = client.get(reverse(route))
        assert response.status_code == 200
        html = response.content.decode()
        assert "https://novin-graphics.com/" not in html
        assert "https://namatabesh.com/" not in html
        assert "دیدن منبع اصلی" not in html
        assert "معرفی از وب‌سایت رسمی" not in html


@pytest.mark.django_db
def test_demo_archival_preserves_an_actual_member_with_a_similar_name() -> None:
    province = Province.objects.create(name="تهران", slug="tehran")
    city = City.objects.create(name="تهران", slug="tehran", province=province)
    genuine_user = User.objects.create(username="real-member", phone="09120000000")
    genuine = Vendor.objects.create(
        user=genuine_user,
        business_name="تابلو سازی سپهراد",
        city=city,
        phone="09120000000",
        address="نشانی واقعی",
    )
    seeded_user = User.objects.create(username="09120000001", phone="09120000001")
    seeded = Vendor.objects.create(
        user=seeded_user,
        business_name="نورنگار تهران",
        city=city,
        phone="09120000001",
        address="خیابان نمونه، پلاک 2",
    )
    refresh_industry_content(archive_demo=True)
    genuine.refresh_from_db()
    seeded.refresh_from_db()
    assert genuine.is_active
    assert not seeded.is_active
    assert User.objects.filter(pk=genuine_user.pk).exists()


@pytest.mark.django_db
def test_import_refuses_to_overwrite_a_member_project() -> None:
    province = Province.objects.create(name="تهران", slug="tehran")
    city = City.objects.create(name="تهران", slug="tehran", province=province)
    user = User.objects.create(username="real-member")
    vendor = Vendor.objects.create(user=user, business_name="عضو واقعی", city=city)
    original = PortfolioItem.objects.create(
        vendor=vendor, slug="reference-novin-amir-chocolate", title="کار واقعی عضو"
    )
    with pytest.raises(ValidationError):
        refresh_industry_content()
    original.refresh_from_db()
    assert original.vendor_id == vendor.pk
    assert original.title == "کار واقعی عضو"
    assert not Service.objects.exists()
