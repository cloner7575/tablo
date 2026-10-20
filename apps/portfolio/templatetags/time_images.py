"""Time-aware covers share one accessible picture component across all pages."""

from django import template
from django.templatetags.static import static

from apps.common.daylight_images import scene_source, scene_variants
from apps.portfolio.demo import demo_image_path
from apps.portfolio.models import TIME_IMAGE_FIELDS, PortfolioItem

register = template.Library()


@register.inclusion_tag("components/_time_image.html")
def time_image(
    item: PortfolioItem,
    source: str = "",
    alt: str | None = None,
    width: int = 800,
    height: int = 600,
    lazy: bool = True,
    high: bool = False,
    deferred: bool = False,
) -> dict[str, object]:
    fallback = source or (
        item.image.url if item.image else static(demo_image_path(item))
    )
    variants = scene_variants(item.image.url if item.image else demo_image_path(item))
    shared_scene = bool(variants)
    variants.update(
        {
            name.removeprefix("image_"): getattr(item, name).url
            for name in TIME_IMAGE_FIELDS
            if getattr(item, name)
        }
    )
    return {
        "source": fallback,
        "variants": variants,
        "alt": item.title if alt is None else alt,
        "width": width,
        "height": height,
        "lazy": lazy,
        "high": high,
        "deferred": deferred,
        "single_exposure": shared_scene or not item.image,
    }


@register.inclusion_tag("components/_time_image.html")
def scene_image(
    source: str,
    alt: str = "",
    width: int = 800,
    height: int = 600,
    lazy: bool = True,
    high: bool = False,
) -> dict[str, object]:
    """Render shared public photography through the existing site clock."""
    return {
        "source": scene_source(source),
        "variants": scene_variants(source),
        "alt": alt,
        "width": width,
        "height": height,
        "lazy": lazy,
        "high": high,
        "single_exposure": True,
    }


@register.inclusion_tag("components/_time_image.html")
def hero_time_image() -> dict[str, object]:
    return {
        "source": static("img/hero-signage-iran-v3.webp"),
        "variants": {
            phase: static(f"img/hero-signage-{phase}.webp")
            for phase in ("morning", "day", "sunset", "night")
        },
        "alt": "تصویر مفهومی نمای کافه با حروف برجسته، کامپوزیت و زمینهٔ چوبی",
        "single_exposure": True,
        "width": 1254,
        "height": 1254,
        "high": True,
    }
