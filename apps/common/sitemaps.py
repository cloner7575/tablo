from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import CityServicePage, Service
from apps.locations.models import City
from apps.portfolio.models import PortfolioItem
from apps.vendors.models import Vendor, VerificationStatus


class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["common:home", "requests:wizard_start", "vendors:list"]

    def location(self, item):
        return reverse(item)


class ServiceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Service.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("catalog:service", kwargs={"slug": obj.slug})


class CitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return City.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("catalog:city", kwargs={"slug": obj.slug})


class VendorSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Vendor.objects.filter(
            is_active=True, verification_status=VerificationStatus.APPROVED
        )

    def location(self, obj):
        return reverse("vendors:public", kwargs={"slug": obj.slug})


class PortfolioSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return PortfolioItem.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("portfolio:detail", kwargs={"slug": obj.slug})


class CityServiceSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.85

    def items(self):
        return CityServicePage.objects.filter(is_published=True).select_related(
            "city", "service"
        )

    def location(self, obj):
        return reverse(
            "catalog:city_service",
            kwargs={"city_slug": obj.city.slug, "service_slug": obj.slug},
        )


sitemaps = {
    "static": StaticViewSitemap,
    "services": ServiceSitemap,
    "cities": CitySitemap,
    "vendors": VendorSitemap,
    "portfolio": PortfolioSitemap,
    "city_service": CityServiceSitemap,
}
