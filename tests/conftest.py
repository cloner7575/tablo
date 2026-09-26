import pytest
from django.contrib.auth import get_user_model
from django.test import Client

PASSWORD = "pass-pass-pass"


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        username="ada",
        email="ada@example.com",
        password=PASSWORD,
    )


@pytest.fixture
def staff_user(db):
    return get_user_model().objects.create_user(
        username="grace",
        email="grace@example.com",
        password=PASSWORD,
        is_staff=True,
    )


@pytest.fixture
def auth_client(client: Client, user) -> Client:
    client.force_login(user)
    return client
