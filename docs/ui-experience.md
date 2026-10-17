# سیستم طراحی و تجربهٔ موبایل

جهت جاری محصول، رنگ‌ها و هر دو تم jeddy.ir است و جایگزین محدودیت قبلی سفید/قرمز شده. جزئیات بازبینی فیچرها و معماری اطلاعات در [product-review.md](product-review.md) آمده است.

| نقش | روشن | تاریک |
| --- | --- | --- |
| زمینه | `#f8fafc` | `#0c1424` |
| سطح | `#ffffff` | `#111e32` |
| سطح دوم | `#f0f4f9` | `#19283e` |
| متن | `#16263c` | `#edf4ff` |
| متن فرعی | `#596b80` | `#a5b6cd` |
| مرز | `#dfe7ef` | `#2b3d55` |
| تأکید | `#1464c4` | `#79b8ff` |

دکمهٔ اصلی در هر دو تم آبی کبالت با نوشتهٔ سفید است. تصویر بخش اول در روشن قاب نرم و در تاریک قاب دایره‌ای دارد، مطابق جهت بصری مرجع. تایپوگرافی خودمیزبان Vazirmatn و چیدمان RTL حفظ شده‌اند.

## فایل‌های اصلی

- `static/css/tokens.css`: رنگ‌های هر دو حالت و fallback تنظیم دستگاه؛ فاصله، سایه و حرکت.
- `static/css/experience.css`: بازنویسی لایهٔ تجربه برای صفحهٔ اصلی، خدمات، نمونه‌کار، متخصصان، گالری، مقاله، پنل، فرم و گفت‌وگو.
- `static/js/theme.js`: اسکریپت کوچک پیش از CSS برای انتخاب تم بدون نمایش لحظه‌ای تم اشتباه؛ ذخیرهٔ ترجیح، تغییر تنظیم دستگاه و همگام‌سازی تب‌ها.
- `static/css/polish.css`: پرداخت مشترک کارت‌ها، دکمه‌ها، منوها و قاب متحرک لندینگ؛ پس از لایهٔ پنل بارگذاری می‌شود.
- `static/js/experience.js`: ورود محتوا، حرکت کنترل‌پذیر تصویر اصلی، ناوبری فعال، فیلتر واکنش‌گرا و پیشرفت مطالعهٔ مقاله.
- `static/js/app.js`: dialog موبایل، بازگرداندن فوکوس و وضعیت ارسال فرم.

تم اولیه از انتخاب ذخیره‌شده یا تنظیم دستگاه می‌آید. انتخاب دستی کاربر ذخیره و در صفحات بعدی حفظ می‌شود. اگر storage غیرفعال باشد، دکمه در همان صفحه همچنان کار می‌کند. برچسب دسترس‌پذیر دکمه، اقدام بعدی و aria-pressed حالت فعلی را نشان می‌دهند.

## موبایل و دسترس‌پذیری

هدر موبایل شامل برند، تغییر تم و منوست. نوار پایین چهار مسیر خانه، نمونه‌ها، درخواست قیمت و حساب را دارد. ذخیره‌ها و ایده‌های تابلو در پنل مشتری در دسترس‌اند. نوار هنگام تمرکز روی ورودی و در ویزارد/ورود/پنل متخصص/ویرایش محتوا/گفت‌وگو پنهان می‌شود. فیلترها در موبایل بسته‌اند مگر انتخاب فعالی داشته باشند؛ بدون JavaScript باز می‌مانند. ورودی‌های متنی حداقل ۱۶ پیکسل و اقدامات اصلی حداقل ۴۴ پیکسل‌اند.

منو از native dialog برای focus trap و Escape استفاده می‌کند. محتوا پیش از JavaScript هم قابل دیدن است. حرکت ورود هر عنصر یک بار اجرا می‌شود و تنظیم زندهٔ کاهش حرکت، انیمیشن جاری را متوقف می‌کند. هیچ کتابخانهٔ انیمیشن جدیدی اضافه نشده است.

بررسی مرورگر: تم روشن و تاریک، ماندگاری تم بین صفحات، انتخاب خدمات و انتقال به سفارش، فیلتر متخصصان، صفحه‌های گالری و مقاله، و پنل‌های خصوصی با رندر فقط‌خواندنی. آزمون‌های خودکار: ۲۲۵ تست Python و ۱۳ تست JavaScript؛ lint/format، Django check، missing migrations و manifest production موفق. صفحه‌بندی متخصصان و تعداد کوئری ثابت نیز تست دارند.

## تصویر اختصاصی

ابزار: built-in imagegen، در حالت edit. فایل مصرفی: `static/img/hero-signage-blue-v2.webp`؛ ابعاد ۱۲۵۴×۱۲۵۴ و حجم ۱۰۴۵۶۲ بایت. فایل قرمز قبلی بازنویسی نشده است. خروجی فقط برای مصرف وب به WebP فشرده شد و در صفحه برچسب مفهومی/هوش مصنوعی دارد.

پرامپت نهایی ویرایش:

```text
Edit this original isometric signage-marketplace hero. Preserve the exact storefront, camera, composition, white beveled base, industrial signage components, abstract illuminated stacked-panel emblem, silver ruler, plant details, lighting and craft quality. Replace ALL red/crimson plastic, acrylic, wires, signage panel, interior shelving and machine accents with premium cobalt blue (#1464c4 to #155db4), with subtle cyan edge reflections. Keep white and silver neutral, dark glass deep navy. Change the neutral backdrop to a very pale cool icy blue (#eaf3fc), with natural soft product-photo shadow. Absolutely no red, pink, warm gold, purple or writing. The resulting image should be a clean high-end cool blue isometric product hero that harmonizes with a professional navy-blue light/dark website. Do not alter the emblem geometry or add text. Square composition.
```

## سفارش ساده پس از بررسی صنعت — ۲۱ مهر ۱۴۰۵

ساختار عمومی و پنل‌ها با مسیر سفارش مشتری هماهنگ شدند؛ جزئیات در `docs/simple-ordering.md` است. بررسی دیداری موبایل، فرم واقعی بدون ارسال پیامک، هر دو تم صفحهٔ اصلی و snapshotهای پنل انجام شد. عرض متن گالری در پنل و نوار چهارگزینه‌ای موبایل در این بررسی اصلاح شدند.

تصاویر نهایی:

- `/home/alisafari/.codex/visualizations/2026/10/12/01a12f15-9f21-7fe1-b12c-39abcec51fdf/tablo-simple-desktop.png`
- `/home/alisafari/.codex/visualizations/2026/10/12/01a12f15-9f21-7fe1-b12c-39abcec51fdf/tablo-simple-dark.png`
- `/home/alisafari/.codex/visualizations/2026/10/12/01a12f15-9f21-7fe1-b12c-39abcec51fdf/tablo-simple-mobile.png`

اعتبارسنجی نهایی: ۲۲۵ تست Django، دو فایل تست JavaScript، lint و format، system check، بررسی migration و collectstatic با ذخیره‌ساز production.

## پرداخت کارت‌ها، منو و حرکت لندینگ — ۲۱ مهر ۱۴۰۵

رنگ‌های مرجع حفظ شدند. هدر به قاب شناور با نشانگر مسیر فعال تبدیل شد؛ کارت‌ها قاب تصویری یکسان، دکمهٔ ذخیرهٔ مشخص، حالت فوکوس و واکنش به ماوس دارند. دکمه‌ها سایه و حالت فشردن یکدست دارند. بخش اول، قاب تصویر با جزئیات ساخت تابلو، تایپوگرافی برجسته و مراحل سه‌گانهٔ سفارش دارد. متن صفحهٔ نمونه تابلوها ساده‌تر شد.

حرکت‌ها با CSS و Web Animations اجرا می‌شوند؛ React، Framer Motion یا کتابخانهٔ جدید اضافه نشده است. ورود محتوا یک بار اجرا می‌شود. حرکت آرام تصویر و دو برچسب فقط هنگام دیده‌شدن قاب و فعال‌بودن صفحه اجرا می‌شود. کاربر می‌تواند آن را متوقف کند؛ تغییر زندهٔ prefers-reduced-motion نیز رعایت می‌شود. بدون JavaScript یا IntersectionObserver محتوا ثابت و قابل دیدن است.

بررسی دیداری: لندینگ روشن و تاریک در دسکتاپ، منوی موبایل و بازگشت فوکوس با Escape، کارت نمونه‌کار در ۳۷۵ و ۱۲۸۰ پیکسل، فهرست تابلوساز در ۷۶۸ پیکسل و snapshot فقط‌خواندنی پنل مشتری و تابلوساز در ۳۷۵ پیکسل. این نماها اسکرول افقی نداشتند.

تصاویر در پوشهٔ visualizations جلسه:

- `tablo-polished-desktop.png`
- `tablo-polished-dark.png`
- `tablo-polished-cards.png`
- `tablo-polished-mobile-menu.png`

اعتبارسنجی: ۲۲۵ تست Django و ۱۳ تست JavaScript (۹ حرکت و ۴ تم)، ruff، Django check، نبود migration جدید و collectstatic با manifest production.
