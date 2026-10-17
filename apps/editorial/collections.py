from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.accounts.models import User
from apps.editorial.models import Idea, SavedReference

SAVED_IDEAS_KEY = "inspiration_ideas"
SAVED_IDEAS_LIMIT = 24
REFERENCE_KEYS = {"idea": SAVED_IDEAS_KEY, "portfolio_item": "inspiration_board"}


def browser_reference_ids(request: HttpRequest, kind: str) -> list[int]:
    values = request.session.get(REFERENCE_KEYS[kind], [])
    if not isinstance(values, list):
        return []
    return list(
        dict.fromkeys(value for value in values if type(value) is int and value > 0)
    )[:24]


def reference_ids(request: HttpRequest, kind: str) -> list[int]:
    guest = browser_reference_ids(request, kind)
    if not request.user.is_authenticated:
        return guest
    cache_key = f"_saved_{kind}_ids"
    if not hasattr(request, cache_key):
        stored = list(
            SavedReference.objects.filter(
                user=request.user, **{f"{kind}__isnull": False}
            )
            .order_by("-created_at")
            .values_list(f"{kind}_id", flat=True)
        )
        setattr(request, cache_key, list(dict.fromkeys(stored + guest))[:24])
    return getattr(request, cache_key)


@transaction.atomic
def save_reference(request: HttpRequest, *, kind: str, pk: int, action: str) -> bool:
    if request.user.is_authenticated:
        User.objects.select_for_update().get(pk=request.user.pk)
        references = SavedReference.objects.filter(
            user=request.user, **{f"{kind}__isnull": False}
        )
        existing = references.filter(**{f"{kind}_id": pk})
        guest = browser_reference_ids(request, kind)
        if action == "remove":
            existing.delete()
        elif not existing.exists():
            if references.count() >= 24:
                return False
            SavedReference.objects.create(user=request.user, **{f"{kind}_id": pk})
        request.session[REFERENCE_KEYS[kind]] = [
            value for value in guest if value != pk
        ]
        return True
    ids = browser_reference_ids(request, kind)
    if kind == "idea":
        visible = Idea.objects.published()
    else:
        from apps.portfolio.selectors import discoverable_items

        visible = discoverable_items()
    ids = list(visible.filter(pk__in=ids).values_list("pk", flat=True))
    if action == "remove":
        ids = [value for value in ids if value != pk]
    elif pk not in ids:
        if len(ids) >= 24:
            return False
        ids.append(pk)
    request.session[REFERENCE_KEYS[kind]] = ids
    return True


@transaction.atomic
def import_browser_references(request: HttpRequest) -> int:
    from apps.portfolio.selectors import discoverable_items

    User.objects.select_for_update().get(pk=request.user.pk)
    pending = 0
    for kind, queryset in (
        ("idea", Idea.objects.published()),
        ("portfolio_item", discoverable_items()),
    ):
        valid = queryset.filter(
            pk__in=browser_reference_ids(request, kind)
        ).values_list("pk", flat=True)
        remaining = []
        for pk in valid:
            if not save_reference(request, kind=kind, pk=pk, action="add"):
                remaining.append(pk)
        request.session[REFERENCE_KEYS[kind]] = remaining
        pending += len(remaining)
    return pending


def saved_idea_ids(request: HttpRequest) -> list[int]:
    return reference_ids(request, "idea")


def saved_ideas(request: HttpRequest) -> QuerySet[Idea]:
    return (
        Idea.objects.published()
        .filter(pk__in=saved_idea_ids(request))
        .select_related("category", "service")
    )
