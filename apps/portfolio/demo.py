"""Demo image fallbacks for portfolio items without uploaded media."""

from __future__ import annotations

from apps.portfolio.models import PortfolioItem

PORTFOLIO_DEMO_IMAGES: tuple[str, ...] = (
    "img/demo/portfolio-cafe.png",
    "img/demo/portfolio-boutique.png",
    "img/demo/portfolio-office.png",
    "img/demo/portfolio-restaurant.png",
    "img/demo/service-chalnium.png",
    "img/demo/service-neon.png",
    "img/demo/service-led.png",
    "img/demo/workshop-banner.png",
)


def demo_image_path(item: PortfolioItem) -> str:
    """Return a static path for items that have no uploaded image."""
    return PORTFOLIO_DEMO_IMAGES[item.pk % len(PORTFOLIO_DEMO_IMAGES)]


def attach_demo_image(item: PortfolioItem) -> PortfolioItem:
    """Attach ``demo_image`` static path when ``image`` is empty."""
    if not item.image:
        item.demo_image = demo_image_path(item)  # type: ignore[attr-defined]
    return item
