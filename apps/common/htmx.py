"""Helpers for HTMX request detection and client-side events."""

from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponse


def is_htmx(request: HttpRequest) -> bool:
    """True when HTMX issued the request, so the view may return a partial."""
    return request.headers.get("HX-Request") == "true"


def is_boosted(request: HttpRequest) -> bool:
    """True for hx-boost navigation, which still expects a full page body."""
    return request.headers.get("HX-Boosted") == "true"


def trigger_client_event(
    response: HttpResponse,
    name: str,
    detail: object = None,
) -> HttpResponse:
    """Add `name` to the HX-Trigger header without dropping existing events."""
    raw = response.headers.get("HX-Trigger")
    events: dict[str, object] = json.loads(raw) if raw else {}
    events[name] = detail
    response.headers["HX-Trigger"] = json.dumps(events)
    return response
