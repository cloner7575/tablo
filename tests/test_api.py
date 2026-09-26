import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_health_endpoint_is_public(client) -> None:
    response = client.get(reverse("api:v1:health"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_me_requires_authentication(client) -> None:
    response = client.get(reverse("api:v1:me"))
    assert response.status_code == 403
    body = response.json()
    assert set(body) == {"detail", "code"}
    assert body["code"] == "not_authenticated"


def test_me_returns_the_session_user(auth_client, user) -> None:
    response = auth_client.get(reverse("api:v1:me"))
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == user.username
    assert body["email"] == user.email


def test_me_updates_own_profile(auth_client, user) -> None:
    response = auth_client.patch(
        reverse("api:v1:me"),
        data={"first_name": "Ada", "email": "Ada@Example.com"},
        content_type="application/json",
    )
    assert response.status_code == 200

    user.refresh_from_db()
    assert user.first_name == "Ada"
    assert user.email == "ada@example.com"


def test_me_cannot_take_another_users_email(auth_client, staff_user) -> None:
    response = auth_client.patch(
        reverse("api:v1:me"),
        data={"email": staff_user.email.upper()},
        content_type="application/json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "invalid"
    assert "email" in body["errors"]


def test_username_is_read_only(auth_client, user) -> None:
    auth_client.patch(
        reverse("api:v1:me"),
        data={"username": "someone-else"},
        content_type="application/json",
    )
    user.refresh_from_db()
    assert user.username == "ada"
