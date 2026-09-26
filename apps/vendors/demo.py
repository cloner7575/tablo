"""Demo cover images for vendors without uploaded media."""

from __future__ import annotations

from apps.vendors.models import Vendor

VENDOR_DEMO_COVERS: tuple[str, ...] = (
    "img/demo/portfolio-boutique.png",
    "img/demo/portfolio-cafe.png",
    "img/demo/service-steel.png",
    "img/demo/service-composite.png",
    "img/demo/portfolio-office.png",
    "img/demo/service-flexi.png",
    "img/demo/workshop-banner.png",
    "img/demo/service-neon.png",
)


def demo_cover_path(vendor: Vendor) -> str:
    return VENDOR_DEMO_COVERS[vendor.pk % len(VENDOR_DEMO_COVERS)]


def attach_demo_cover(vendor: Vendor) -> Vendor:
    """Attach ``demo_cover`` static path when ``cover_image`` is empty."""
    if vendor.cover_image:
        vendor.demo_cover = ""  # type: ignore[attr-defined]
    else:
        vendor.demo_cover = demo_cover_path(vendor)  # type: ignore[attr-defined]
    return vendor
