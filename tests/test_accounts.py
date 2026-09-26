import pytest
from django.core import mail
from django.urls import reverse

from tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "route",
    [
        "accounts:login",
        "accounts:password_reset",
        "accounts:password_reset_done",
        "accounts:password_reset_complete",
    ],
)
def test_public_auth_screens_render(client, route: str) -> None:
    assert client.get(reverse(route)).status_code == 200


def test_password_change_screen_renders(auth_client) -> None:
    assert auth_client.get(reverse("accounts:password_change")).status_code == 200


def test_invalid_reset_link_explains_itself(client) -> None:
    url = reverse(
        "accounts:password_reset_confirm",
        kwargs={"uidb64": "bad", "token": "bad-token"},
    )
    response = client.get(url)
    assert response.status_code == 200
    assert "invalid or has already been used" in response.content.decode()


def test_login_page_renders_a_csrf_protected_form(client) -> None:
    response = client.get(reverse("accounts:login"))
    assert response.status_code == 200
    assert "csrfmiddlewaretoken" in response.content.decode()


def test_login_rejects_bad_credentials(client, user) -> None:
    response = client.post(
        reverse("accounts:password_login"),
        {"username": user.username, "password": "wrong-password"},
    )
    assert response.status_code == 200
    assert "form-errors" in response.content.decode()
    assert not response.wsgi_request.user.is_authenticated


def test_login_signs_the_user_in(client, user) -> None:
    response = client.post(
        reverse("accounts:password_login"),
        {"username": user.username, "password": PASSWORD},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("common:home")


def test_logout_requires_post(auth_client) -> None:
    assert auth_client.get(reverse("accounts:logout")).status_code == 405

    response = auth_client.post(reverse("accounts:logout"))
    assert response.status_code == 302


def test_password_change_requires_authentication(client) -> None:
    response = client.get(reverse("accounts:password_change"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.headers["Location"]


def test_password_reset_email_uses_namespaced_confirm_url(client, user) -> None:
    response = client.post(
        reverse("accounts:password_reset"),
        {"email": user.email},
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert "/accounts/password/reset/" in mail.outbox[0].body
