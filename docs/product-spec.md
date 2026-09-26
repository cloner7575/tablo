# Product Spec — تابلو دات کام

## Vision

تابلو دات کام یک پلتفرم Lead Generation برای صنعت تابلوسازی ایران است.
بازدیدکننده درخواست ساخت تابلو ثبت می‌کند؛ تابلو‌سازهای مرتبط پیشنهاد قیمت می‌فرستند؛ مشتری بهترین پیشنهاد را انتخاب می‌کند.

## Goals (MVP)

1. تبدیل بازدیدکننده به `ProjectRequest`
2. اتصال Request به Vendor مناسب (شهر + نوع سرویس)
3. چرخه Quote → Accept → Complete → Review
4. صفحات SEO قابل ایندکس برای سرویس، شهر، Vendor و Portfolio

## Roles

| Role | Capabilities |
|------|----------------|
| Customer | ثبت درخواست، مشاهده پیشنهادها، گفتگو، Accept، Review |
| Vendor | مشاهده Requestهای منطبق، ارسال Quote، گفتگو، مدیریت Portfolio و پروفایل |
| Admin | تأیید/تعلیق Vendor، مدیریت محتوا، بررسی Request/Review |

## Core flows

### Customer

Homepage CTA → Wizard (نوع، شهر، ابعاد، نور، توضیح، عکس، بودجه، موبایل/OTP) → Success → Dashboard → Quotes → Accept → Complete → Review

### Vendor

Signup → Pending verification → Admin approve → Dashboard → Matched requests → Submit quote → Win → Complete project

## Non-goals (MVP)

payment gateway، AI، قیمت‌گذاری قطعی، اپ موبایل، blog، حسابداری، حمل‌ونقل

## Chat (MVP)

گفتگوی ۱:۱ وابسته به هر `Quote` با Django Channels + WebSocket (Redis channel layer).
باز شدن بعد از ثبت پیشنهاد؛ مذاکره قبل از Accept؛ ادامه بعد از پذیرش؛ بستن thread پیشنهادهای بازنده.

## Success criteria

Clone → Docker Compose → Seed → ثبت Request → Quote → Accept → Complete → Review روی UI واقعی با دادهٔ seed.
