# داده‌ها و تصاویر واقعی صنعت تابلو

منابع در ۱۳ اکتبر ۲۰۲۶ بررسی شدند. مجموعهٔ دادهٔ قابل تکرار در `apps/catalog/industry_content.json` است: ۱۲ نوع تابلو، ۱۱ نمونهٔ تصویری منبع‌دار و معرفی ۷ مجموعهٔ رسمی. نوشته‌های راهنما خلاصهٔ تألیفی‌اند؛ متن مقاله‌های سایت‌های مرجع کپی نشده است.

منابع رسمی:

- [نوین گرافیک](https://novin-graphics.com/)
- [نما تابش](https://namatabesh.com/)
- [رنگین‌رسانه](https://ranginrasaneh.com/) و [تابلو راهنمای طبقات](https://ranginrasaneh.com/table-guide-for-classes/)
- [دورال](https://www.doralsign.com/)
- [برند تابلو](https://brandtablo.com/)
- [تابلو دیبا](https://tablodiba.com/)
- [نوین لایت](https://novinlight.com/)

## دادهٔ قابل بررسی

نمونه‌ها: امیرشکلات، گراد، رستوران وزرا، شیرین‌عسل، موزهٔ جواهرات ملی، آرامیس، پارسینا، راهنمای رفاه فرازان هدف، حروف آفاق، حروف لاسوگاسی و تابلو روان Welcome. نام‌ها و نوع تابلو از معرفی منبع گرفته شده‌اند؛ برای پارسینا که فقط «فلزی» معرفی شده، نوع «استیل» حدس زده نشده است. محل اجرای نمونه‌ها، مبلغ، ابعاد و ضمانت منتشر نشده‌اند چون در این بررسی برای هر نمونه تأیید نشده‌اند.

`PortfolioItem` نمونهٔ مرجع را بدون حساب تابلوساز نگه می‌دارد و نام منبع، صفحهٔ منبع و URL عکس اصلی دارد. قید دیتابیس اجازهٔ نمونهٔ بدون عضو و بدون منبع/تصویر را نمی‌دهد. صفحهٔ مرجع از صفحهٔ نمونه‌کار عضو جداست. ذخیره‌ها، جست‌وجو، دستهٔ خدمت، sitemap و CreativeWork برای نمونه‌های مرجع کار می‌کنند. ترتیب امتیاز، نمونه‌های فاقد امتیاز را بعد از اعضا قرار می‌دهد.

تصاویر اصلی از وب‌سایت‌های مرجع دریافت و برای وب به WebP تبدیل شده‌اند؛ واترمارک حذف نشده است. نسخه‌های مصرفی در `static/img/references/` هستند. نشانی عکس‌های نمونه‌کار در JSON موجود است. تصاویر معرفی خدمت به منبع تصویر لینک دارند. عکس سه مقالهٔ اولیه نیز با عکس منبع‌دار جایگزین شده است.

معرفی ۷ مجموعه از وب‌سایت رسمی، عضویت یا تأیید آن‌ها در مارکت‌پلیس را اثبات نمی‌کند. برای آن‌ها حساب، امتیاز مشتری، سفارش، زمان پاسخ یا قیمت ساختگی ایجاد نشده است. شهر دفتر فقط در موارد بررسی‌شده ثبت شده؛ شهر دفتر به عنوان محل اجرای نمونه‌کار استفاده نشده است. استان کرج به البرز اصلاح شد و مشهد/خراسان رضوی به انتخاب‌های شهر اضافه شدند.

## اعمال و بازیابی

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_industry_content
```

فرمان بدون دسترسی شبکه و از فایل‌های همین پروژه اجرا می‌شود. تکرار آن رکورد یا فایل تکراری نمی‌سازد. برخورد نامک یک مرجع با نمونه‌کار عضو، عملیات را با rollback متوقف می‌کند. هنگام وجود دادهٔ آزمایشی در پیش‌نمایش DEBUG:

```bash
.venv/bin/python manage.py import_industry_content --archive-demo
```

بایگانی فقط اثر انگشت دقیق seed قبلی را هدف می‌گیرد: نام، تلفن و نشانی نمونهٔ تابلوساز و مشخصات دقیق مشتری/عنوان/توضیح درخواست. عضو واقعی با نام یا شمارهٔ مشابه باقی می‌ماند. فرمان با این گزینه در production اجرا نمی‌شود. داده‌های کاربران به طور گسترده حذف نمی‌شوند.

در دیتابیس پیش‌نمایش این جلسه ۱۰ تابلوساز و ۲۰ نمونه‌کار آزمایشی غیرفعال شدند، نظرهای مربوط منتشر نیستند، ۲۰ درخواست آزمایشی و سفارش‌های مربوط وضعیت لغوشده دارند و ۶ ایدهٔ seed به پیش‌نویس رفتند. تصویرهای اولیهٔ موجود در فایل‌ها حذف نشده‌اند. قبل از migration و واردسازی، پشتیبان سازگار SQLite در `/tmp/tablo-preview-before-industry.sqlite3` با دسترسی ۰۶۰۰ ذخیره شد. این تغییر داده روی `/tmp/tablo-preview.sqlite3` اعمال شده است؛ دیتابیس production این جلسه تغییر نکرد.

## تصویر جدید لندینگ

ابزار: built-in imagegen در حالت تولید تصویر جدید. خروجی اصلی PNG باقی مانده و فایل مصرفی پروژه `static/img/hero-signage-iran-v3.webp` است؛ ۱۲۵۴×۱۲۵۴ پیکسل. تصویر یک طرح مفهومی مستقل است و همین برچسب در صفحه دیده می‌شود. قاب عکس در تم تاریک هم گوشهٔ گرد دارد تا نوشته و نمای مغازه بریده نشوند.

پرامپت نهایی:

```text
Create a new square photorealistic architectural hero image for an Iranian sign-ordering marketplace website. Subject: a believable finished small Iranian cafe storefront photographed from pavement at a mild three-quarter angle. NOT an isometric miniature, render toy, exploded parts, floating tools, collage, or futuristic building. Real installed Iranian signage craft seen in source websites: fabricated 3D Persian channel letters with white acrylic faces and polished stainless steel returns, warm-white LED illumination, firmly mounted on a matte navy/cobalt composite fascia; neat brushed-metal trims, a vertical thermowood strip, simple grey stone walls with natural texture, a full-height dark aluminum framed glass entrance. The main fascia must contain exactly the correct connected Persian text «کافه آبی», tastefully lettered right to left, no other brand or text. Letter depth and fasteners physically plausible. Show a modest real shop frontage with warm interior, a couple of chairs behind glass and small green plant by doorway. Signage is the main visual subject, across the upper middle of frame, fully within safe margins for circular and rounded-square crop. Streetscape feels Iranian, human-scale building, clean ordinary pavement, no crowds or cars. Architectural editorial photography at blue hour, real natural mixed daylight and warm shop light, tasteful cobalt blue sign details consistent with #1464c4 website, white and light grey stone, soft dark navy tones. Avoid excessive neon cyberpunk, red accent, logos from actual companies, phone numbers, watermarks and impossible luxurious facades. This is an original AI concept inspired by real signage materials, never portray it as a completed client project. Premium, inviting and convincingly photographic, highly detailed fabricated signage and facade, 1:1 composition.
```

## اعتبارسنجی

۲۳۲ تست Django و ۱۳ تست JavaScript موفق شدند؛ ruff check/format، system check، بررسی migration و collectstatic production انجام شدند. واردسازی تکرارشونده، مالکیت نمونه‌کار عضو، بایگانی محدود، ذخیره و جست‌وجوی مرجع و تعداد کوئری ثابت پوشش تست دارند. نمایش منابع و تصاویر در دسکتاپ و عرض ۳۷۵ پیکسل، ذخیرهٔ واقعی در مرورگر و نسبت‌دادن عکس مقاله بررسی شدند.

## تغییر نمایش به درخواست مالک

داده‌ها و تصاویر برای سید استفاده می‌شوند. لینک وب‌سایت‌های مرجع، نوشته‌های منبع، نام سازنده در کارت نمونهٔ مرجع، زیرنویس منبع عکس خدمات/مقاله و creator نمونهٔ مرجع در خروجی عمومی حذف شدند. توضیح‌های سید صرفاً دربارهٔ تابلو و خدمات‌اند. URL و نام منبع در مدل‌ها و فایل JSON داخلی برای ردیابی باقی می‌مانند؛ API عمومی نمونه‌کار نیز آن‌ها را نمایش نمی‌دهد. داده‌های مجموعه‌ها به صورت کارت اطلاعاتی بدون لینک خارجی نمایش داده می‌شوند.
