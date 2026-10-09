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

## Not called

Order confirmation, payment, Bizum, and postal-code change are not implemented. Checkout stops in process.
