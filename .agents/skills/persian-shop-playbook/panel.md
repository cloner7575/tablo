# Staff panel (condensed from nightruby-panel)

Full detail: `~/.cursor/skills/nightruby-panel/{SKILL,screens,product-form}.md`

Custom dark RTL panel at **`/panel/`**. Day-to-day ops live here. Optionally redirect `/admin/` → `panel:dashboard`.

On this starter: `apps.panel` has **no models** — it reads/writes `apps.catalog` and `apps.orders` (and payments via order relations).

## Tokens

```
bg #0f0f10  surface #1a1a1c  surface-2 #222224  hover #2a2a2d  border #323235
accent #00E5FF (cyan)  gold #C9A66B  cream #F3EBDF
danger #FF453A  success #32D74B  info #5AC8FA  muted #98989D
```

Font: Vazirmatn only. Body charcoal + faint cyan/gold glows. Cards radius 16. Primary buttons cyan. Force `dir=ltr` on hex, phone, slug, password.

## Shell

Sidebar + main. Brand, nav groups, badges, user footer. Mobile: overlay off-canvas (Alpine). Sticky topbar: title, `+ محصول`, سفارش badge, لینک سایت, خروج POST.

Nav groups:

1. داشبورد
2. فروش و سفارش — سفارش‌ها (needs_action), محصولات (low_stock)
3. کاتالوگ — دسته‌ها، کالکشن‌ها، راهنمای سایز
4. صفحه اصلی سایت — هیرو، مزایا، نظرات، اینستا، داستان برند، بنر

## Auth

`/panel/login/` — staff only (`is_staff`). Non-staff authenticated → Persian error + storefront. Split brand/form desktop.

## Mixins / stats

`StaffRequiredMixin` · `PanelContextMixin` · Persian form error flash · `get_panel_nav_stats`: pending_payment, to_process, shipping, needs_action, low_stock (`0<stock<3`), no_image · `format_toman`

## Dashboard

KPIs: فروش امروز / ۷ روز / نیاز به اقدام / سفارش‌های امروز. Pipeline strip 30d. Chart.js cyan sales (Jalali MM/DD). Alerts + recent order cards.

## Orders

Tabs: action (default), payment, process, shipping, done, cancelled, all. Detail stepper + quick next actions. Bulk status updates. Copy phone/address.

## Product form (signature UX)

Create = **info only**. After PK: tabs `?tab=info|media|colors|variants`.

| Tab | Behavior |
|-----|----------|
| اطلاعات | name, slug LTR, category, prices, collections, flags, sticky save |
| تصاویر | AJAX dropzone, reorder, primary, delete; max 10MB images |
| رنگ‌ها | per-product cards, hex + color picker, optional color image |
| سایز و موجودی | formset size×color, blank stock→10, blank price→inherit |

Product list: search, filters low/no_image/inactive, card grid, Alpine bulk, paginate 20.

## Catalog + CMS

Category / Collection / SizeGuide (interactive JSON table). Homepage CMS via generic content CRUD factory views. Magazine: no panel CRUD unless asked.

## Shared components

sidebar · messages · form_field · form_errors_summary · formset_errors_summary · bulk_bar · status_badge · order_card · color_picker · content_form

## Do not

- Only Django admin inlines for colors/variants as the merchant UX
- Global Color table
- Require variant prices (inheritance default)
- Unlock media upload before product has a PK
- Ship desktop-only panel — staff use phones
