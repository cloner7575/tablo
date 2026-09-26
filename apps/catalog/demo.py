from __future__ import annotations

from apps.catalog.models import Service

SERVICE_IMAGES: dict[str, str] = {
    "chalnium": "img/demo/service-chalnium.png",
    "neon": "img/demo/service-neon.png",
    "composite": "img/demo/service-composite.png",
    "steel": "img/demo/service-steel.png",
    "flexi": "img/demo/service-flexi.png",
    "led": "img/demo/service-led.png",
}


def attach_demo_image(service: Service) -> Service:
    """Attach a static demo path when the service has no uploaded icon."""
    service.demo_image = SERVICE_IMAGES.get(  # type: ignore[attr-defined]
        service.slug, "img/demo/service-chalnium.png"
    )
    return service
