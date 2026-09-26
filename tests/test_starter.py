import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.test import Client, RequestFactory
from django.urls import reverse
from django.views.defaults import permission_denied


@pytest.mark.django_db
def test_user_model_is_custom() -> None:
    assert get_user_model()._meta.label == "accounts.User"


@pytest.mark.django_db
def test_health_reports_database(client) -> None:
    response = client.get(reverse("common:health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_home_page_is_accessible(client) -> None:
    response = client.get(reverse("common:home"))
    assert response.status_code == 200
    html = response.content.decode()
    assert 'href="#main"' in html
    assert "<main" in html
    assert "Skip to content" in html
    assert 'lang="' in html
    assert 'dir="' in html
    assert "has-mobile-chrome" in html
    assert "mobile-cta" in html
    assert "data-nav-toggle" in html


@pytest.mark.django_db
def test_base_template_ships_htmx_and_csrf_header(client) -> None:
    html = client.get(reverse("common:home")).content.decode()
    assert "vendor/htmx.min.js" in html
    assert "X-CSRFToken" in html


def test_unknown_url_renders_the_project_404_page(client) -> None:
    response = client.get("/definitely-not-a-page/")
    assert response.status_code == 404
    html = response.content.decode()
    assert "404" in html
    assert "We could not find that page." in html


def test_500_template_renders_without_request_or_context() -> None:
    # Django renders handler500 with no context processors and no request.
    html = render_to_string("500.html")
    assert "500" in html
    assert "Something went wrong" in html


def test_403_template_renders() -> None:
    request = RequestFactory().get("/private/")
    response = permission_denied(request, PermissionDenied())
    assert response.status_code == 403
    assert "403" in response.content.decode()


@pytest.mark.django_db
def test_csrf_failure_renders_the_friendly_page() -> None:
    strict = Client(enforce_csrf_checks=True)
    response = strict.post(reverse("accounts:login"), {"username": "x"})
    assert response.status_code == 403
    assert "Your session expired" in response.content.decode()


def test_health_panel_is_htmx_only(client) -> None:
    response = client.get(reverse("common:health_panel"))
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("common:home")


@pytest.mark.django_db
def test_health_panel_returns_a_fragment_for_htmx(client) -> None:
    response = client.get(
        reverse("common:health_panel"),
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "<html" not in html
    assert 'id="health-panel"' in html
