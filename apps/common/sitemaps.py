from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import Max, Q, QuerySet
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import CityServicePage, Service
from apps.editorial.models import (
    Article,
    Category,
    CategoryKind,
    Idea,
    PublicationStatus,
)
from apps.locations.models import City
from apps.portfolio.models import PortfolioItem
from apps.portfolio.selectors import discoverable_items
from apps.vendors.models import Vendor, VerificationStatus


class PublicSitemap(Sitemap):
    def get_domain(self, site: object | None = None) -> str:
        origin = settings.PUBLIC_SITE_URL
        return urlsplit(origin).netloc if origin else super().get_domain(site)

    def get_protocol(self, protocol: str | None = None) -> str:
        origin = settings.PUBLIC_SITE_URL
        return urlsplit(origin).scheme if origin else super().get_protocol(protocol)


class StaticViewSitemap(PublicSitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self) -> list[str]:
        return [
            'common:home',
            'common:guide',
            'catalog:services',
            'portfolio:list',
            'vendors:list',
            'editorial:ideas',
            'editorial:articles',
        ]

    def location(self, item: str) -> str:
        return reverse(item)


class ServiceSitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self) -> QuerySet[Service]:
        return Service.objects.filter(is_active=True)

    def location(self, obj: Service) -> str:
        return reverse('catalog:service', kwargs={'slug': obj.slug})

    def lastmod(self, obj: Service) -> datetime:
        return obj.updated_at


class CitySitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self) -> QuerySet[City]:
        return City.objects.filter(is_active=True)

    def location(self, obj: City) -> str:
        return reverse('catalog:city', kwargs={'slug': obj.slug})

    def lastmod(self, obj: City) -> datetime:
        return obj.updated_at


class VendorSitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self) -> QuerySet[Vendor]:
        return Vendor.objects.filter(
            is_active=True, verification_status=VerificationStatus.APPROVED
        )

    def location(self, obj: Vendor) -> str:
        return reverse('vendors:public', kwargs={'slug': obj.slug})

    def lastmod(self, obj: Vendor) -> datetime:
        return obj.updated_at


class PortfolioSitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self) -> QuerySet[PortfolioItem]:
        return discoverable_items()

    def location(self, obj: PortfolioItem) -> str:
        return reverse('portfolio:detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj: PortfolioItem) -> datetime:
        return obj.updated_at


class CityServiceSitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.85

    def items(self) -> QuerySet[CityServicePage]:
        return (
            CityServicePage.objects.filter(
                is_published=True, city__is_active=True, service__is_active=True
            )
            .select_related('city', 'service')
            .order_by('pk')
        )

    def location(self, obj: CityServicePage) -> str:
        return reverse(
            'catalog:city_service',
            kwargs={'city_slug': obj.city.slug, 'service_slug': obj.slug},
        )

    def lastmod(self, obj: CityServicePage) -> datetime:
        return obj.updated_at


class IdeaSitemap(PublicSitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self) -> QuerySet[Idea]:
        return Idea.objects.published()

    def lastmod(self, obj: Idea) -> datetime:
        return obj.updated_at


class ArticleSitemap(PublicSitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self) -> QuerySet[Article]:
        return Article.objects.published()

    def lastmod(self, obj: Article) -> datetime:
        return obj.updated_at


class ContentCategorySitemap(PublicSitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self) -> QuerySet[Category]:
        return (
            Category.objects.filter(is_active=True)
            .annotate(
                latest_idea=Max(
                    'ideas__updated_at',
                    filter=Q(
                        ideas__status=PublicationStatus.PUBLISHED,
                        ideas__published_at__lte=timezone.now(),
                    ),
                ),
                latest_article=Max(
                    'articles__updated_at',
                    filter=Q(
                        articles__status=PublicationStatus.PUBLISHED,
                        articles__published_at__lte=timezone.now(),
                    ),
                ),
            )
            .filter(Q(latest_idea__isnull=False) | Q(latest_article__isnull=False))
            .order_by('sort_order', 'pk')
        )

    def location(self, obj: Category) -> str:
        route = (
            'editorial:idea_category'
            if obj.kind == CategoryKind.BUSINESS
            else 'editorial:article_category'
        )
        return reverse(route, kwargs={'category_slug': obj.slug})

    def lastmod(self, obj: Category) -> datetime:
        return max(
            value
            for value in (obj.updated_at, obj.latest_idea, obj.latest_article)
            if value
        )


sitemaps = {
    'static': StaticViewSitemap,
    'services': ServiceSitemap,
    'cities': CitySitemap,
    'vendors': VendorSitemap,
    'portfolio': PortfolioSitemap,
    'city_service': CityServiceSitemap,
    'ideas': IdeaSitemap,
    'articles': ArticleSitemap,
    'content_categories': ContentCategorySitemap,
}
