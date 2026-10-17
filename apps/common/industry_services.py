"""Install reviewed public reference content without creating commercial identities."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from apps.catalog.industry import industry_content
from apps.catalog.models import Service
from apps.editorial.models import (
    Article,
    Category,
    CategoryKind,
    Idea,
    PublicationStatus,
)
from apps.locations.models import City, Province
from apps.orders.models import Order, OrderStatus
from apps.portfolio.models import PortfolioItem
from apps.requests.models import ProjectRequest, RequestStatus
from apps.reviews.models import Review
from apps.vendors.models import Vendor


def _reference_file(filename: str) -> str:
    source = Path(settings.BASE_DIR) / "static" / "img" / "references" / filename
    if not source.is_file():
        raise FileNotFoundError(f"Missing reviewed image: {filename}")
    target = f"industry/references/{filename}"
    if default_storage.exists(target):
        return target
    return default_storage.save(target, ContentFile(source.read_bytes()))


@transaction.atomic
def install_industry_content() -> dict[str, int]:
    content = industry_content()
    for province_slug, province_name, city_slug, city_name in [
        ("tehran", "تهران", "tehran", "تهران"),
        ("alborz", "البرز", "karaj", "کرج"),
        ("khorasan-razavi", "خراسان رضوی", "mashhad", "مشهد"),
    ]:
        province, _ = Province.objects.get_or_create(
            slug=province_slug, defaults={"name": province_name}
        )
        City.objects.update_or_create(
            slug=city_slug, defaults={"name": city_name, "province": province}
        )
    services: dict[str, Service] = {}
    for index, entry in enumerate(content["services"]):
        service, _ = Service.objects.update_or_create(
            slug=entry["slug"],
            defaults={
                "title": entry["title"],
                "description": entry["description"],
                "suitable_for": entry["suitable_for"],
                "materials": entry["materials"],
                "faq": entry["faq"],
                "icon": _reference_file(entry["image"]),
                "source_name": entry["source_name"],
                "source_url": entry["source_url"],
                "sort_order": index,
                "is_active": True,
            },
        )
        services[entry["slug"]] = service
    # Reverse insertion keeps the curated storefront examples first on the home.
    for entry in reversed(content["projects"]):
        if PortfolioItem.objects.filter(
            slug=entry["slug"], vendor__isnull=False
        ).exists():
            raise ValidationError("نامک نمونهٔ مرجع با نمونه‌کار یک عضو تداخل دارد.")
        project, _ = PortfolioItem.objects.update_or_create(
            slug=entry["slug"],
            defaults={
                "vendor": None,
                "title": entry["title"],
                "description": entry["description"],
                "service": services.get(entry["service"]),
                "image": _reference_file(entry["image"]),
                "source_name": entry["source_name"],
                "source_url": entry["source_url"],
                "source_image_url": entry["source_image_url"],
                "is_published": True,
            },
        )
        project.full_clean()
    categories = [
        ("cafe", "کافه و رستوران"),
        ("shop", "فروشگاه و مغازه"),
        ("clinic", "مطب و خدمات درمانی"),
        ("office", "شرکت و فضای اداری"),
        ("building", "نام ساختمان و راهنما"),
        ("beauty", "سالن زیبایی"),
        ("bakery", "قنادی و مواد غذایی"),
    ]
    for index, (slug, title) in enumerate(categories):
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                "name": title,
                "kind": CategoryKind.BUSINESS,
                "sort_order": index,
            },
        )
    article_photos = {
        "choose-shop-sign": "novin-amir-chocolate.webp",
        "prepare-sign-brief": "namatabesh-vozara.webp",
        "ai-sign-inspiration": "novin-gerad.webp",
    }
    for slug, filename in article_photos.items():
        project = next(p for p in content["projects"] if p["image"] == filename)
        Article.objects.filter(slug=slug).update(
            image=_reference_file(filename),
            thumbnail="",
            image_alt=project["title"],
            image_caption=project["title"],
            updated_at=timezone.now(),
        )
    return {
        "services": len(services),
        "projects": len(content["projects"]),
        "categories": len(categories),
    }


@transaction.atomic
def archive_seeded_demo() -> dict[str, int]:
    # Match the exact historical seed identities, never a broad phone prefix alone.
    from apps.common.management.commands.seed_demo import VENDOR_NAMES

    ids = []
    for index, name in enumerate(VENDOR_NAMES):
        ids.extend(
            Vendor.objects.filter(
                business_name=name,
                user__phone=f"0912000{index:04d}",
                phone=f"0912000{index:04d}",
                address=f"خیابان نمونه، پلاک {index + 1}",
            ).values_list("pk", flat=True)
        )
    vendor_count = Vendor.objects.filter(pk__in=ids).update(is_active=False)
    portfolio_count = PortfolioItem.objects.filter(vendor_id__in=ids).update(
        is_published=False
    )
    Review.objects.filter(vendor_id__in=ids).update(is_published=False)
    # Match descriptions, numbered titles and exact seed customer identities.
    requests = ProjectRequest.objects.none()
    for index in range(8):
        requests |= ProjectRequest.objects.filter(
            customer__phone=f"0912111{index:04d}",
            customer__username=f"0912111{index:04d}",
            customer__first_name=f"مشتری{index + 1}",
            title__regex=r"^درخواست .+ #[0-9]+$",
            description="نیاز به تابلو سردر مغازه با کیفیت بالا.",
        )
    request_ids = list(requests.values_list("pk", flat=True))
    request_count = ProjectRequest.objects.filter(pk__in=request_ids).update(
        status=RequestStatus.CANCELLED
    )
    Order.objects.filter(request_id__in=request_ids).update(
        status=OrderStatus.CANCELLED
    )
    demo_slugs = [
        "cafe-warm",
        "boutique-gold",
        "restaurant-neon",
        "retail-raised",
        "beauty-steel",
        "jewelry-gold",
    ]
    Idea.objects.filter(slug__in=demo_slugs, created_by__isnull=True).update(
        status=PublicationStatus.DRAFT
    )
    return {
        "vendors_archived": vendor_count,
        "portfolio_archived": portfolio_count,
        "requests_archived": request_count,
    }


@transaction.atomic
def refresh_industry_content(*, archive_demo: bool = False) -> dict[str, int]:
    stats = install_industry_content()
    if archive_demo:
        stats.update(archive_seeded_demo())
    return stats
