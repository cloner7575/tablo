from django.conf import settings
from django.http import HttpRequest

from apps.common.seo import (
    canonical_url,
    default_social_image,
    public_url,
    should_noindex,
)


def site(request: HttpRequest) -> dict[str, object]:
    return {
        "CANONICAL_URL": canonical_url(request),
        "PAGE_NOINDEX": should_noindex(request),
        "DEFAULT_SOCIAL_IMAGE": default_social_image(request),
        "SITE_ORIGIN": public_url(request, "/"),
        "SITE_NAME": getattr(settings, "SITE_NAME", "Core"),
        "TEXT_DIRECTION": getattr(settings, "TEXT_DIRECTION", "ltr"),
    }
