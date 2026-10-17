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

`PUT` the same path. Body, and only this body:

```json
{"lines": [{"product_id": "10381", "quantity": 1}]}
```

`quantity: 0` removes that line. Keys `item_id`, `amount`, and `currency` are forbidden. Lock: `fixtures/cart_put_request.json` and `merca/basket/wire.py`.

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

## Not called

Placing a new order, `DELETE /orders/{id}/` (cancel), payment, Bizum, and postal-code change are not implemented. Checkout stops in process. Checkout may GET the cart so preflight can run. It does not POST an order.
