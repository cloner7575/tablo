import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.accounts.models import User
from apps.catalog.models import Service
from apps.locations.models import City, Province
from apps.portfolio.models import PortfolioItem
from apps.vendors.models import Vendor, VerificationStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def creative_data():
    province = Province.objects.create(name="تهران", slug="tehran")
    city = City.objects.create(name="تهران", slug="tehran", province=province)
    service = Service.objects.create(title="چلنیوم", slug="chalnium")
    user = User.objects.create_user(username="maker")
    vendor = Vendor.objects.create(
        user=user,
        business_name="کارگاه نور",
        city=city,
        verification_status=VerificationStatus.APPROVED,
    )
    item = PortfolioItem.objects.create(
        vendor=vendor, service=service, city=city, title="کافه روشن"
    )
    return city, service, vendor, item


def test_board_toggle_is_private_idempotent_and_post_only(client, creative_data):
    item = creative_data[3]
    url = reverse("portfolio:board_toggle", kwargs={"pk": item.pk})
    assert client.get(url).status_code == 405
    client.post(url, {"action": "add"})
    client.post(url, {"action": "add"})
    assert client.session["inspiration_board"] == [item.pk]
    assert len(client.get(reverse("editorial:saved")).context["items"]) == 1
    assert not Client().get(reverse("editorial:saved")).context["items"]
    client.post(url, {"action": "remove"})
    assert client.session["inspiration_board"] == []


def test_board_hides_unpublished_and_unapproved_work(client, creative_data):
    item = creative_data[3]
    url = reverse("portfolio:board_toggle", kwargs={"pk": item.pk})
    client.post(url)
    item.is_published = False
    item.save()
    assert client.post(url).status_code == 404
    assert not client.get(reverse("editorial:saved")).context["items"]
    item.is_published = True
    item.save()
    item.vendor.verification_status = VerificationStatus.PENDING
    item.vendor.save()
    assert client.post(url).status_code == 404


def test_gallery_filters_and_has_constant_queries(
    client, creative_data, django_assert_num_queries
):
    city, service, vendor, item = creative_data
    url = reverse("portfolio:list")
    with django_assert_num_queries(4):
        response = client.get(
            url, {"service": service.slug, "city": city.slug, "q": "کافه"}
        )
    assert list(response.context["page_obj"]) == [item]
    for i in range(6):
        PortfolioItem.objects.create(
            vendor=vendor, service=service, city=city, title=f"کافه {i}"
        )
    with django_assert_num_queries(4):
        client.get(url, {"service": service.slug, "city": city.slug})
    assert not client.get(url, {"q": "ناموجود"}).context["page_obj"]


def test_board_limit_does_not_drop_saved_items(client, creative_data):
    vendor = creative_data[2]
    items = [
        PortfolioItem.objects.create(vendor=vendor, title=f"کار {i}") for i in range(25)
    ]
    for item in items:
        client.post(
            reverse("portfolio:board_toggle", kwargs={"pk": item.pk}), {"action": "add"}
        )
    assert len(client.session["inspiration_board"]) == 24
    assert items[0].pk in client.session["inspiration_board"]


def test_board_query_count_is_constant(client, creative_data):
    vendor, item = creative_data[2:]
    client.post(reverse("portfolio:board_toggle", kwargs={"pk": item.pk}))
    url = reverse("editorial:saved")
    with CaptureQueriesContext(connection) as few:
        client.get(url)
    for index in range(5):
        sample = PortfolioItem.objects.create(vendor=vendor, title=f"اثر {index}")
        client.post(reverse("portfolio:board_toggle", kwargs={"pk": sample.pk}))
    with CaptureQueriesContext(connection) as many:
        client.get(url)
    assert len(few) == len(many)


def test_creative_mutations_require_csrf(creative_data):
    client = Client(enforce_csrf_checks=True)
    assert client.post(reverse("requests:from_board")).status_code == 403
    url = reverse("portfolio:board_toggle", kwargs={"pk": creative_data[3].pk})
    assert client.post(url).status_code == 403


def test_board_rejects_invalid_destination(client, creative_data):
    url = reverse("portfolio:board_toggle", kwargs={"pk": creative_data[3].pk})
    response = client.post(url, {"destination": "https://untrusted.example"})
    assert response.status_code == 400
    assert "inspiration_board" not in client.session


def test_gallery_keeps_filters_when_paginating(client, creative_data):
    city, service, vendor, _ = creative_data
    for i in range(12):
        PortfolioItem.objects.create(
            vendor=vendor, service=service, city=city, title=f"نمونه {i}"
        )
    response = client.get(
        reverse("portfolio:list"), {"service": service.slug, "page": 2}
    )
    assert len(response.context["page_obj"]) == 1
    assert f"service={service.slug}" in response.context["filter_query"]


def test_saving_reference_preserves_local_gallery_filters(client, creative_data):
    url = reverse("portfolio:board_toggle", kwargs={"pk": creative_data[3].pk})
    response = client.post(
        url, {"destination": "gallery", "return_query": "service=chalnium&page=2"}
    )
    assert response.url == reverse("portfolio:list") + "?service=chalnium&page=2"


def test_board_references_start_a_project(client, creative_data):
    item = creative_data[3]
    client.post(reverse("portfolio:board_toggle", kwargs={"pk": item.pk}))
    response = client.post(reverse("requests:from_board"))
    assert response.url == reverse("requests:wizard_need")
    draft = client.session["request_wizard"]
    assert item.title in draft["description"]
    assert (
        reverse("portfolio:detail", kwargs={"slug": item.slug}) in draft["description"]
    )
    assert client.get(reverse("requests:from_board")).status_code == 405


def test_empty_board_cannot_seed_a_request(client):
    response = client.post(reverse("requests:from_board"))
    assert response.url == reverse("editorial:saved")
    assert "request_wizard" not in client.session


def test_removed_editor_is_not_available(client):
    assert client.get("/request/studio/").status_code == 404
    assert "استودیو" not in client.get(reverse("common:home")).content.decode()


def test_board_references_survive_the_request_wizard(auth_client, creative_data):
    from apps.requests.models import ProjectRequest

    city, service, _, item = creative_data
    auth_client.post(reverse("portfolio:board_toggle", kwargs={"pk": item.pk}))
    auth_client.post(reverse("requests:from_board"))
    description = auth_client.session["request_wizard"]["description"]
    steps = [
        ("wizard_service", {"choice": service.pk}),
        ("wizard_city", {"city": city.pk}),
        ("wizard_dimensions", {"size_choice": "medium"}),
        ("wizard_lighting", {"lighting_type": "led"}),
        ("wizard_description", {"description": description}),
        ("wizard_image", {"csrfmiddlewaretoken": "test-token"}),
        ("wizard_budget", {"csrfmiddlewaretoken": "test-token"}),
        ("wizard_submit", {}),
    ]
    for step, payload in steps:
        response = auth_client.post(reverse(f"requests:{step}"), payload)
        assert response.status_code == 302, step
    project = ProjectRequest.objects.get(customer=auth_client.session["_auth_user_id"])
    assert item.title in project.description
    assert project.service == service
    assert project.city == city
