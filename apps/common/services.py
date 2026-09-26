"""Infrastructure-level checks shared by the HTML and API health endpoints."""

from __future__ import annotations

import logging

from django.db import DatabaseError, connections

logger = logging.getLogger(__name__)


def database_status() -> tuple[bool, str]:
    """Return (reachable, human readable status) for the default database."""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError as exc:
        logger.exception("Database health check failed")
        return False, f"unreachable: {exc.__class__.__name__}"
    return True, "ok"
