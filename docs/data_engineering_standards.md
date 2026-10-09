# Data engineering

One fact has one writer. The parsers trust fixtures, not guesses.

| Fact | Writer | Everyone else |
|------|--------|----------------|
| Profile (postal code, warehouse, blacklist, bounds) | `merca/core/store.py` | reads |
| Session token | `merca/core/store.py` | reads, never logs |
| Catalog product | `parse_product` / `parse_search` on a captured body | no second product shape |
| Cart lines | `parse_cart` | no second cart parser |
| Cart PUT body | `build_put_body` | CLI passes `--yes`, then calls this |
| Spend | sum of `unit_price * quantity` on the lines | ignore any summary total |
| Delivery window | `check_delivery_slot` | checkout calls it and then stops |

Do not invent a request or response field. If a call has no fixture, raise `unsupported` and stop.

Do not keep a second copy of the basket in this repo. The Mercadona cart is the basket. Local JSON files under `fixtures/` are captured examples for tests, not a live cart.

Writes are explicit. A draft, a search, and a slot check do not PUT. `cart add` without `--yes` does not open HTTP.

`checkout` does not POST confirmation, payment, or Bizum. The human pays in the app.
