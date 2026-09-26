from __future__ import annotations

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import CityServicePage, Service
from apps.locations.models import City, Province
from apps.orders.models import Order, OrderStatus
from apps.portfolio.models import PortfolioItem
from apps.quotes.models import Quote, QuoteStatus
from apps.requests.models import LightingType, ProjectRequest, RequestStatus
from apps.reviews.models import Review
from apps.vendors.models import Vendor, VerificationStatus

User = get_user_model()

SERVICES = [
    ("چلنیوم", "chalnium", "تابلو حروف برجسته چلنیوم"),
    ("نئون", "neon", "تابلو نئون و نئون فلکسی"),
    ("کامپوزیت", "composite", "تابلو کامپوزیت سردر"),
    ("استیل", "steel", "تابلو استیل و حروف استیل"),
    ("فلکسی", "flexi", "تابلو فلکسی و بنر نورانی"),
    ("LED", "led", "تابلو LED و تلویزیون شهری"),
]

VENDOR_NAMES = [
    "تابلو سازی سپهراد",
    "نورنگار تهران",
    "چلنیوم پارس",
    "نئون‌گستر کرج",
    "استیل‌ویژن",
    "حروف برجسته آریا",
    "تابلوسازان البرز",
    "کامپوزیت‌کار تهران",
    "ال ای دی روشن",
    "فلکسی‌نت",
]


class Command(BaseCommand):
    help = "Seed realistic demo data for تابلو دات کام"

    @transaction.atomic
    def handle(self, *args, **options):
        province, _ = Province.objects.get_or_create(
            slug="tehran",
            defaults={"name": "تهران", "is_active": True},
        )
        tehran, _ = City.objects.get_or_create(
            slug="tehran",
            defaults={"name": "تهران", "province": province, "is_active": True},
        )
        karaj_province, _ = Province.objects.get_or_create(
            slug="alborz",
            defaults={"name": "البرز", "is_active": True},
        )
        karaj, _ = City.objects.get_or_create(
            slug="karaj",
            defaults={"name": "کرج", "province": karaj_province, "is_active": True},
        )
        cities = [tehran, karaj]

        services: list[Service] = []
        for i, (title, slug, desc) in enumerate(SERVICES):
            svc, _ = Service.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "description": desc,
                    "is_active": True,
                    "sort_order": i,
                },
            )
            services.append(svc)

        CityServicePage.objects.get_or_create(
            city=tehran,
            service=services[0],
            defaults={
                "title": "تابلو چلنیوم در تهران",
                "slug": "chalnium-sign",
                "body": (
                    "اگر در تهران به تابلو چلنیوم نیاز دارید، درخواست خود را ثبت کنید "
                    "تا تابلو‌سازهای تأییدشده پیشنهاد قیمت بفرستند."
                ),
                "meta_description": "سفارش و مقایسه قیمت تابلو چلنیوم در تهران",
                "is_published": True,
            },
        )
        CityServicePage.objects.get_or_create(
            city=karaj,
            service=services[1],
            defaults={
                "title": "تابلو نئون در کرج",
                "slug": "neon-sign",
                "body": (
                    "برای تابلو نئون مغازه یا کافه در کرج، چند پیشنهاد قیمت بگیرید "
                    "و بهترین تابلو‌ساز را انتخاب کنید."
                ),
                "meta_description": "سفارش تابلو نئون در کرج",
                "is_published": True,
            },
        )

        vendors: list[Vendor] = []
        for i, name in enumerate(VENDOR_NAMES):
            phone = f"0912000{i:04d}"
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "username": phone,
                    "role": "vendor",
                    "is_verified": True,
                    "first_name": name.split()[-1],
                },
            )
            if created:
                user.set_unusable_password()
                user.save()
            city = cities[i % 2]
            description = (
                f"{name} با تمرکز روی طراحی، ساخت و نصب تابلوهای فروشگاهی "
                f"در {city.name} فعالیت می‌کند. از مشاوره اولیه تا نصب نهایی "
                f"همراه کسب‌وکار شماست؛ با نمونه‌کار واقعی و زمان‌بندی شفاف."
            )
            vendor, created = Vendor.objects.get_or_create(
                user=user,
                defaults={
                    "business_name": name,
                    "slug": slugify(name, allow_unicode=True) or f"vendor-{i}",
                    "description": description,
                    "phone": phone,
                    "city": city,
                    "address": f"خیابان نمونه، پلاک {i + 1}",
                    "instagram": f"tablo_{i}",
                    "years_of_experience": 3 + (i % 10),
                    "verification_status": VerificationStatus.APPROVED,
                    "rating": Decimal(str(round(3.8 + (i % 12) * 0.1, 2))),
                    "review_count": 0,
                    "completed_projects": 5 + i * 2,
                    "response_time_hours": 6 + (i % 18),
                    "is_active": True,
                    "is_featured": i < 3,
                },
            )
            if not created and (
                not vendor.description or "متخصص ساخت انواع تابلو" in vendor.description
            ):
                vendor.description = description
                vendor.years_of_experience = 3 + (i % 10)
                vendor.is_featured = i < 3
                vendor.save(
                    update_fields=[
                        "description",
                        "years_of_experience",
                        "is_featured",
                        "updated_at",
                    ]
                )
            vendor.services.set(random.sample(services, k=random.randint(2, 4)))
            vendors.append(vendor)

        # Portfolio 20 — rich demo titles/descriptions (refresh thin seeds)
        portfolio_briefs = [
            (
                "تابلو نئون سردر کافه ساحل",
                (
                    "طراحی و ساخت تابلو نئون سفارشی برای سردر کافه با فونت "
                    "دست‌نویس و نور گرم شبانه. نصب روی نمای کامپوزیت انجام شد."
                ),
                "neon",
            ),
            (
                "حروف برجسته چلنیوم بوتیک",
                (
                    "اجرای حروف چلنیوم طلایی با بک‌لایت LED برای بوتیک پوشاک. "
                    "فونت برند و فاصله حروف مطابق هویت بصری مشتری تنظیم شد."
                ),
                "chalnium",
            ),
            (
                "تابلو استیل لابی اداری",
                (
                    "تابلو استیل مات برای لابی شرکت با نور نقطه‌ای مخفی. "
                    "مناسب فضای داخلی لوکس و خوانایی از فاصله دور."
                ),
                "steel",
            ),
            (
                "سردر کامپوزیت هایپرمارکت",
                (
                    "نمای کامپوزیت کامل سردر به همراه باکس نورانی لوگو. "
                    "ابعاد بزرگ و مقاوم در برابر شرایط شهری."
                ),
                "composite",
            ),
            (
                "تابلو فلکسی داروخانه شبانه",
                (
                    "تابلو فلکسی دو طرفه با نور LED یکنواخت برای داروخانه. "
                    "خوانایی بالا در روز و شب و مصرف برق بهینه."
                ),
                "flexi",
            ),
            (
                "تلویزیون شهری LED نمایشگاه",
                (
                    "نصب پنل LED شهری برای نمایشگاه خودرو با کنترل محتوا "
                    "از راه دور و ساختار مقاوم باد."
                ),
                "led",
            ),
            (
                "تابلو لاس‌وگاسی رستوران",
                (
                    "ترکیب حروف برجسته و نوار نوری متحرک برای رستوران. "
                    "جلب توجه در خیابان پرتردد شبانگاهی."
                ),
                "neon",
            ),
            (
                "لوگوی استیل طلافروشی",
                (
                    "لوگوی استیل براق با آبکاری طلایی و نور مخفی برای طلافروشی. "
                    "جزئیات ظریف و نصب دقیق روی سنگ."
                ),
                "steel",
            ),
        ]
        service_by_slug = {s.slug: s for s in services}
        for i in range(20):
            vendor = vendors[i % len(vendors)]
            base_title, description, service_slug = portfolio_briefs[
                i % len(portfolio_briefs)
            ]
            service = service_by_slug.get(service_slug, services[i % len(services)])
            title = f"{base_title} — {vendor.city.name}"
            if i >= len(portfolio_briefs):
                title = f"{base_title} ({i + 1}) — {vendor.city.name}"
            item, created = PortfolioItem.objects.get_or_create(
                slug=f"sample-{i + 1}",
                defaults={
                    "vendor": vendor,
                    "title": title,
                    "description": description,
                    "service": service,
                    "city": vendor.city,
                    "is_published": True,
                },
            )
            if not created:
                item.title = title
                item.description = description
                item.service = service
                item.city = vendor.city
                item.vendor = vendor
                item.is_published = True
                item.save(
                    update_fields=[
                        "title",
                        "description",
                        "service",
                        "city",
                        "vendor",
                        "is_published",
                        "updated_at",
                    ]
                )

        customers = []
        for i in range(8):
            phone = f"0912111{i:04d}"
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    "username": phone,
                    "role": "customer",
                    "is_verified": True,
                    "first_name": f"مشتری{i + 1}",
                },
            )
            if created:
                user.set_unusable_password()
                user.save()
            customers.append(user)

        # Requests 20
        requests: list[ProjectRequest] = []
        for i in range(20):
            customer = customers[i % len(customers)]
            service = services[i % len(services)]
            city = cities[i % 2]
            status = [
                RequestStatus.RECEIVING_QUOTES,
                RequestStatus.QUOTED,
                RequestStatus.ACCEPTED,
                RequestStatus.COMPLETED,
            ][i % 4]
            req, _ = ProjectRequest.objects.get_or_create(
                title=f"درخواست {service.title} #{i + 1}",
                customer=customer,
                defaults={
                    "description": "نیاز به تابلو سردر مغازه با کیفیت بالا.",
                    "service": service,
                    "city": city,
                    "district": "مرکز شهر",
                    "business_type": "فروشگاه",
                    "width_cm": 200 + i * 10,
                    "height_cm": 60 + (i % 5) * 10,
                    "lighting_type": random.choice(list(LightingType.values)),
                    "budget_min": 5_000_000 + i * 100_000,
                    "budget_max": 15_000_000 + i * 200_000,
                    "status": status,
                },
            )
            requests.append(req)

        # Quotes ~50
        quote_count = 0
        for req in requests:
            eligible = [
                v
                for v in vendors
                if req.service_id in set(v.services.values_list("id", flat=True))
                and v.city_id == req.city_id
            ]
            if len(eligible) < 3:
                eligible = list({*eligible, *vendors[:5]})
            for vendor in eligible[:3]:
                if quote_count >= 50:
                    break
                _, created = Quote.objects.get_or_create(
                    request=req,
                    vendor=vendor,
                    defaults={
                        "price": random.randint(8_000_000, 35_000_000),
                        "estimated_delivery_days": random.randint(3, 20),
                        "description": "پیشنهاد اجرای کامل شامل طراحی و نصب.",
                        "warranty": f"{random.choice([6, 12, 18, 24])} ماه",
                        "installation_cost": random.randint(500_000, 3_000_000),
                        "material_details": "متریال درجه یک",
                        "status": QuoteStatus.PENDING
                        if req.status
                        in {RequestStatus.RECEIVING_QUOTES, RequestStatus.QUOTED}
                        else QuoteStatus.VIEWED,
                    },
                )
                if created:
                    quote_count += 1
            if quote_count >= 50:
                break

        # Complete a few with orders + reviews
        for req in requests:
            if req.status not in {RequestStatus.ACCEPTED, RequestStatus.COMPLETED}:
                continue
            quote = req.quotes.first()
            if quote is None:
                continue
            quote.status = QuoteStatus.ACCEPTED
            quote.save(update_fields=["status"])
            order, _ = Order.objects.get_or_create(
                request=req,
                defaults={
                    "quote": quote,
                    "customer": req.customer,
                    "vendor": quote.vendor,
                    "agreed_price": quote.price,
                    "status": OrderStatus.COMPLETED
                    if req.status == RequestStatus.COMPLETED
                    else OrderStatus.ACTIVE,
                    "completed_at": timezone.now()
                    if req.status == RequestStatus.COMPLETED
                    else None,
                },
            )
            if req.status == RequestStatus.COMPLETED:
                Review.objects.get_or_create(
                    request=req,
                    defaults={
                        "customer": req.customer,
                        "vendor": quote.vendor,
                        "rating": random.randint(4, 5),
                        "comment": "کار تمیز و به‌موقع انجام شد.",
                        "is_published": True,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {len(services)} services, {len(cities)} cities, "
                f"{len(vendors)} vendors, "
                f"portfolios={PortfolioItem.objects.count()}, "
                f"requests={ProjectRequest.objects.count()}, "
                f"quotes={Quote.objects.count()}"
            )
        )
