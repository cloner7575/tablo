from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class AnalyticsProvider(Protocol):
    def track(self, event: str, payload: dict[str, object] | None = None) -> None: ...


class ConsoleAnalyticsProvider:
    def track(self, event: str, payload: dict[str, object] | None = None) -> None:
        logger.info("analytics event=%s payload=%s", event, payload or {})


class NoOpAnalyticsProvider:
    def track(self, event: str, payload: dict[str, object] | None = None) -> None:
        return None


def get_analytics_provider() -> AnalyticsProvider:
    path = getattr(
        settings,
        "ANALYTICS_PROVIDER",
        "apps.analytics.services.ConsoleAnalyticsProvider",
    )
    module_path, class_name = path.rsplit(".", 1)
    from importlib import import_module

    module = import_module(module_path)
    return getattr(module, class_name)()


def track(event: str, payload: dict[str, object] | None = None) -> None:
    get_analytics_provider().track(event, payload)
