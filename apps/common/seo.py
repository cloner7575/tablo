"""Canonical URLs and structured data shared by public pages."""

from __future__ import annotations

from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.encoding import iri_to_uri

PRIVATE_PREFIXES = (
    '/accounts/',
    '/admin/',
    '/request/',
    '/orders/',
    '/chats/',
    '/api/',
    '/portfolio/manage/',
    '/inspiration/manage/',
    '/inspiration/saved/',
    '/vendors/dashboard/',
    '/vendors/requests/',
    '/vendors/quotes/',
    '/vendors/projects/',
    '/vendors/profile/',
    '/vendors/onboarding/',
    '/vendors/chats/',
)
FILTER_PARAMETERS = frozenset(
    {'q', 'service', 'city', 'style', 'source', 'sort', 'status'}
)


def public_url(request: HttpRequest, path: str) -> str:
    if urlsplit(path).scheme in {'http', 'https'}:
        return iri_to_uri(path)
    origin = getattr(settings, 'PUBLIC_SITE_URL', '')
    if origin:
        return iri_to_uri(origin.rstrip('/') + '/' + path.lstrip('/'))
    return request.build_absolute_uri(path)


def canonical_url(request: HttpRequest) -> str:
    path = request.path
    page = request.GET.get('page', '')
    if len(page) <= 6 and page.isascii() and page.isdigit() and int(page) > 1:
        path += f'?page={int(page)}'
    return public_url(request, path)


def should_noindex(request: HttpRequest) -> bool:
    return request.path.startswith(PRIVATE_PREFIXES) or any(
        request.GET.get(key) for key in FILTER_PARAMETERS
    )


def breadcrumbs(
    request: HttpRequest, items: list[tuple[str, str]]
) -> dict[str, object]:
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': index,
                'name': name,
                'item': public_url(request, path),
            }
            for index, (name, path) in enumerate(items, 1)
        ],
    }


def default_social_image(request: HttpRequest) -> str:
    return public_url(request, static('img/hero-signage-iran-v3.webp'))
