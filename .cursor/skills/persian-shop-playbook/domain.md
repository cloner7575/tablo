# Domain & commerce (bounded apps on this starter)

Full NightRuby detail: `~/.cursor/skills/nightruby-store/{architecture,commerce}.md`  
On this starter, split ownership across apps (do not grow a monolith `shop`).

## App ownership

| App | Models / modules |
|-----|------------------|
| `apps.catalog` | Category, Collection, Product, ProductImage, ProductColor, ProductVariant, HeroSlide, SiteFeature, Testimonial (+ BrandStory/Promo later); `adapters.product_to_dict`; `selectors` (paginated lists); `seed_shop` |
| `apps.cart` | Cart, CartItem; `services` get/add/update/remove/merge/serialize |
| `apps.orders` | Order, OrderItem (snapshots); checkout `create_order_from_cart` (**no stock decrement**) |
| `apps.payments` | Payment; Zarinpal client; verify + **decrement stock on paid**; Celery notify |
| `apps.panel` | No models — reads catalog/orders |
| `apps.accounts` | User (+ optional profile) |
| `apps.common` | TimeStampedModel, persian helpers |

## Catalog models

- **Category** — title/name, slug, subtitle, sort_order, is_active; optional image for circle merchandising
- **Collection** — title, slug, subtitle, is_active; M2M via Product.collections
- **Product** — name, slug, description, price, sale_price (nullable toman), category, collections M2M, flags is_new/is_sale/best_seller/is_active; `effective_price`, `is_on_sale`
- **ProductImage** — file, alt, sort_order, is_primary
- **ProductColor** — FK product, unique (product, name), hex_code
- **ProductVariant** — size, optional color FK, stock, sku, optional price/sale_price; unique (product, size, color)

## Cart (DB — required at scale)

- **Cart** — user XOR session_key (guest)
- **CartItem** — variant FK, color_name denormalized, qty; unique (cart, variant)
- Guest cart by session; **merge on login**
- Stock checked on mutate; serialize for Alpine drawer

## Orders / payments

- **Order** — status pending_payment|paid|failed|cancelled|fulfilled; snapshot address fields; total
- **OrderItem** — snapshot only (product_name, size, color_name, unit_price, qty, line_total)
- Checkout creates order + items from cart, clears cart, **does not** decrement stock
- **Payment** — authority, ref_id, amount, status; Zarinpal v4; amount rial = toman×10
- On verify success (idempotent): mark paid, **decrement stock**, Celery notify

## Catalog reads

- `ProductQuerySet.active()` / `with_relations()`
- **Server pagination** on list views and DRF — never dump entire catalog into `products_json`
- Page-sized `product_to_dict` only

## Services map

| Module | Role |
|--------|------|
| `catalog.adapters` | `product_to_dict`, `ensure_default_variant` |
| `catalog.selectors` | Home slices, paginated lists, search |
| `cart.services` | get_or_create, add/update/remove, merge_guest_cart, serialize |
| `orders.services` | create_order_from_cart |
| `payments.zarinpal` | request/verify |
| `payments.services` | mark_paid_and_decrement (atomic, idempotent) |

## Commerce rules

1. Guest cart by session; merge on login/register  
2. Checkout form → Order + snapshots → Payment request → Zarinpal  
3. Callback: Status OK + verify 100/101 → paid + stock decrement + clear already done at checkout  
4. Wishlist: Alpine + localStorage — not a Django model unless asked  
5. Thin views; no payment state machine inside catalog views  

## Product dict keys (cards / PDP)

```
id, slug, name, price, sale_price, display_price, effective_price_num,
image_url, gallery, category_title, is_new, is_sale, best_seller,
sizes, colors, variants, variant_matrix, default_variant_id, description, in_stock
```

## Storefront URL map (`app_name` shop)

`/` home · `/shop/products/` · `/shop/products/<slug>/` · `/shop/wishlist/` ·
`/shop/cart/` + add|update|remove|api · `/shop/checkout/` ·
`/shop/payment/callback|success|failed/` · `/panel/` · `/api/`

## Seed

`manage.py seed_shop` in `apps.catalog`
