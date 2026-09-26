"""Guardrails for the settings layer.

These tests exist because the failure modes are silent: an email backend that
quietly talks to SMTP, a test run that inherits a developer's `.env`, or a
production deploy started without a real secret key.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings

from core.settings.env import get_bool, get_int, get_list

BASE_DIR = Path(settings.BASE_DIR)


def test_test_settings_are_hermetic() -> None:
    assert settings.DEBUG is False
    assert settings.LANGUAGE_CODE == "en-us"
    assert settings.TEXT_DIRECTION == "ltr"
    assert settings.TIME_ZONE == "UTC"
    assert settings.MAILERS["default"]["BACKEND"].endswith("locmem.EmailBackend")
    assert settings.CACHES["default"]["BACKEND"].endswith("LocMemCache")


def test_email_uses_the_mailers_api_not_the_deprecated_settings() -> None:
    # EMAIL_* is deprecated in Django 6.1 and removed in 7.0.
    assert settings.is_overridden("MAILERS")
    assert not settings.is_overridden("EMAIL_BACKEND")
    assert not settings.is_overridden("EMAIL_HOST")


def test_api_defaults_are_locked_down() -> None:
    rest = settings.REST_FRAMEWORK
    assert rest["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]
    assert rest["DEFAULT_PAGINATION_CLASS"] == "apps.common.api.DefaultPagination"
    assert rest["ALLOWED_VERSIONS"] == ["v1"]


def test_language_is_pinned_so_locale_middleware_cannot_switch_it() -> None:
    assert [code for code, _label in settings.LANGUAGES] == [settings.LANGUAGE_CODE]


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", True), ("true", True), ("ON", True), ("0", False), ("", False)],
)
def test_get_bool(monkeypatch, value: str, expected: bool) -> None:
    monkeypatch.setenv("CORE_TEST_FLAG", value)
    assert get_bool("CORE_TEST_FLAG") is expected


def test_get_int_rejects_garbage(monkeypatch) -> None:
    monkeypatch.setenv("CORE_TEST_INT", "twelve")
    with pytest.raises(ValueError):
        get_int("CORE_TEST_INT", 1)


def test_get_list_splits_and_strips(monkeypatch) -> None:
    monkeypatch.setenv("CORE_TEST_LIST", " a , b ,, c ")
    assert get_list("CORE_TEST_LIST") == ["a", "b", "c"]


def _run_production_check(**env: str) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "core.settings.production",
        **env,
    }
    return subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_refuses_an_insecure_secret_key() -> None:
    result = _run_production_check(
        DJANGO_SECRET_KEY="django-insecure-nope",
        DJANGO_ALLOWED_HOSTS="example.com",
    )
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY" in result.stderr


def test_production_refuses_empty_allowed_hosts() -> None:
    result = _run_production_check(
        DJANGO_SECRET_KEY="x" * 60,
        DJANGO_ALLOWED_HOSTS="",
    )
    assert result.returncode != 0
    assert "DJANGO_ALLOWED_HOSTS" in result.stderr


def test_production_passes_the_deploy_check_when_configured() -> None:
    result = _run_production_check(
        DJANGO_SECRET_KEY="x7q2" * 20,
        DJANGO_ALLOWED_HOSTS="example.com",
    )
    assert result.returncode == 0, result.stderr
