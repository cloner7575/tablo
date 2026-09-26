from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class SmsProvider(Protocol):
    def send(self, phone: str, message: str) -> None: ...


class ConsoleSmsProvider:
    """Development SMS provider — logs to console."""

    def send(self, phone: str, message: str) -> None:
        logger.info("SMS to %s: %s", phone, message)
        print(f"[SMS] to={phone} message={message}")


class NoOpSmsProvider:
    def send(self, phone: str, message: str) -> None:
        logger.debug("NoOp SMS to %s", phone)


def get_sms_provider() -> SmsProvider:
    path = getattr(settings, "SMS_PROVIDER", "apps.accounts.sms.ConsoleSmsProvider")
    module_path, class_name = path.rsplit(".", 1)
    from importlib import import_module

    module = import_module(module_path)
    cls = getattr(module, class_name)
    return cls()
