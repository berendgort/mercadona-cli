# Wire

Captured with `curl_cffi` impersonating Chrome, October 2026. Bodies in `fixtures/` are trimmed public catalog objects or a cart built from those public products. No account, no address, no token.

## Search

`GET https://tornillos.mercadona.es/search?q={query}&wh={warehouse}&lang=es`

A POST of `{"query","wh","lang"}` returns the same object. The client uses GET.

Response: `hits[]` with `id`, `display_name`, `slug`, `brand`, `share_url`, `price_instructions.unit_price`.

Fixtures: `fixtures/search_leche.json` (two hits), `fixtures/search_one.json`.

Plain `curl` without a browser impersonation receives HTTP 403. That is not an auth failure.

## Product

`GET https://tienda.mercadona.es/api/products/{id}/?lang=es&wh={warehouse}`

Fixture: `fixtures/product_17330.json`.

## Cart

Needs `Authorization: Bearer <MO-user.token>` and the customer uuid from the same local storage object. The CLI stores them with `merca login`. It does not send a password.

`GET https://tienda.mercadona.es/api/customers/{uuid}/cart/?lang=es&wh={warehouse}`

`PUT` the same path **replaces the whole basket** when the body carries the cart `id` and its current `version`:

```json
{"id": "<cart uuid>", "version": 3, "lines": [{"product_id": "10381", "quantity": 1}]}
```

Measured live, October 2026:

- A PUT without id/version merges: quantities above 0 are set, but `quantity: 0` is **ignored** (the line stays). So removal needs the full list.
- A PUT with a stale `version` returns **200 and changes nothing**. The client re-reads after every write and retries once; a write that does not stick is an error.
- `lines: []` with id + version empties the cart.

Keys `item_id`, `amount`, and `currency` are forbidden. Lock: `fixtures/cart_put_request.json` and `merca/basket/wire.py`.

`fixtures/cart_ok.json` is a cart object in the GET shape, filled with public search hits so preflight tests have a real price list. It is not an order.

## Orders

`GET https://tienda.mercadona.es/api/customers/{uuid}/orders/?lang=es&wh={warehouse}`

The CLI keeps `id`, `status_ui`, `start_date`, `end_date`, `products_count`, and `summary.products` / `summary.total`. Address, phone, and payment method are dropped. Fixture: `fixtures/orders_page.json` (synthetic, no account).

## Receipt

`GET https://tienda.mercadona.es/api/customers/{uuid}/orders/{id}/receipt/?lang=es&wh={warehouse}`

Header `Accept: application/pdf`. A PDF body starts with `%PDF`. 404 is `not_found`. The CLI writes the file and returns the path and byte count. It does not print the PDF.

## Order edit

Captured from the tienda web bundle and one live edit, October 2026. A confirmed order can change until `changes_until`.

`GET https://tienda.mercadona.es/api/customers/{uuid}/orders/{id}/?lang=es&wh={warehouse}`

The CLI keeps `status_ui` and `changes_until` only. Fixture: `fixtures/order_detail.json` (synthetic).

`GET https://tienda.mercadona.es/api/customers/{uuid}/orders/{id}/cart/?lang=es&wh={warehouse}`

Returns `{"id": <cart uuid>, "lines": [{"id", "product_id", "quantity", "sources", "product"}]}`. Fixture: `fixtures/order_cart.json` (public products, fake ids).

`PUT` the same path saves the order. The body is the **full** line list, not a delta. A line missing from the list is removed:

```json
{"cart": {"id": "<cart uuid>", "lines": [{"id": 9000000001, "quantity": 2, "product_id": "3819", "sources": ["+CO"]}]}}
```

`version` is sent only when the GET returned one. Lock: `merca/basket/order_edit.py` `build_order_put_body`. The CLI refuses to remove every line (the web app treats that as cancel) and refuses products that are not already in the order (adding a line has not been captured).

## Delivered lines

`GET https://tienda.mercadona.es/api/customers/{uuid}/orders/{id}/lines/prepared/?lang=es&wh={warehouse}` (paged by `next_page`)

The CLI keeps `product_id`, `product.display_name`, `ordered_quantity`, `prepared_quantity`, `original_price_instructions.unit_price`, `total_prepared_price`. A weighed product can appear on two lines. Fixture: `fixtures/delivered_lines.json` (public products). Delivered orders are cached under `~/.config/merca/cache/delivered/`.

## Slots

`GET https://tienda.mercadona.es/api/customers/{uuid}/addresses/` returns the saved addresses; the CLI uses the `permanent_address` one and never prints it.

`GET https://tienda.mercadona.es/api/customers/{uuid}/addresses/{address_id}/slots/` returns about ten days of 2-hour slots: `id`, `start`, `end` (UTC), `available`, `open`, `price`. Fixture: `fixtures/slots.json` (synthetic).

## Checkout (place an order)

From the tienda web bundle, October 2026. Steps, in order:

1. `POST /api/customers/{uuid}/checkouts/` with `{"cart": {"id", "version"?, "lines": [{"quantity", "product_id", "sources"}]}}`. Below the minimum the server answers 400 `min_purchase_amount_in_cart_not_reached_error` (60 € in October 2026). Response has the checkout `id`.
2. `PUT /checkouts/{id}/delivery-info/` with `{"address": <address object as GET returns it>, "slot": <slot object as GET returns it>}`.
3. `GET /checkouts/{id}/`: must carry a `payment_method` (the account's saved one). If not, the CLI stops.
4. `POST /checkouts/{id}/confirm/`. 201 with `order_id` is a booked order. 202 means 3-D Secure; the human finishes in the app.

Steps 1 to 3 were exercised live; the 400 above is the real minimum check. The confirm step mirrors the bundle and the result is checked by `merca orders`.

## Not called

`DELETE /orders/{id}/` and `/orders/{id}/cancel/` (cancel), adding or changing a card, Bizum, 3-D Secure, and postal-code change are not implemented. Without `--confirm --yes`, checkout only reads (cart, address, slots).
