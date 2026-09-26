"""Shared DRF building blocks: pagination and a single error envelope."""

from __future__ import annotations

import logging

from rest_framework import exceptions, pagination, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from apps.common.services import database_status

logger = logging.getLogger(__name__)


class DefaultPagination(pagination.PageNumberPagination):
    """Page number pagination with a capped client-controlled page size."""

    page_size_query_param = "page_size"
    max_page_size = 100


def api_exception_handler(
    exc: Exception,
    context: dict[str, object],
) -> Response | None:
    """Return every handled API error as {detail, code, errors}.

    Unhandled exceptions return None so DRF re-raises them: a 500 belongs in
    the logs and the error tracker, not in a prettified response body.
    """
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error in %r", context.get("view"))
        return None

    code = getattr(exc, "default_code", "error")
    data = response.data

    if isinstance(exc, exceptions.ValidationError):
        response.data = {
            "detail": "Invalid input.",
            "code": "invalid",
            "errors": data,
        }
        return response

    if isinstance(data, dict) and "detail" in data:
        response.data = {"detail": str(data["detail"]), "code": code}
        return response

    response.data = {"detail": str(data), "code": code}
    return response


class HealthAPIView(APIView):
    """Liveness/readiness probe for load balancers and uptime checks."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list[type] = []

    def get(self, request: Request) -> Response:
        reachable, database = database_status()
        payload = {"status": "ok" if reachable else "degraded", "database": database}
        code = status.HTTP_200_OK if reachable else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=code)
