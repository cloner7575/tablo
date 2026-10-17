"""Session helpers for the private inspiration board."""

from django.db.models import QuerySet
from django.http import HttpRequest

from apps.editorial.collections import reference_ids
from apps.portfolio.models import PortfolioItem
from apps.portfolio.selectors import discoverable_items

BOARD_SESSION_KEY = "inspiration_board"
BOARD_LIMIT = 24


def board_ids(request: HttpRequest) -> list[int]:
    return reference_ids(request, "portfolio_item")


def board_items(request: HttpRequest) -> QuerySet[PortfolioItem]:
    return discoverable_items().filter(pk__in=board_ids(request))
