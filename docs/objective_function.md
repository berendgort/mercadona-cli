# Objective

The right products arrive in a slot the household can receive. The slot is booked early; the order is trimmed or topped up before its change deadline; history says what the household really eats.

A run is good when all of these are true:

- Search either returns one product or `error_type: ambiguous` with candidates. It does not guess.
- Cart writes send a PUT only when `--yes` is present.
- The slot is Monday, Tuesday, or Wednesday, and the hours sit inside 11:00 to 18:00. Friday never passes.
- Preflight rejects a blacklist hit, a duplicate, a quantity above 18, a cart outside 10 to 65 lines, or a spend outside 60 to 260 euros (Mercadona minimum is 60). Line prices are the spend.
- `order edit` sends a PUT only with `--yes`, only for a `confirmed` order before `changes_until`, never empties the order, and never adds a product.
- `checkout` without `--confirm` prints the slot and stops. With `--confirm --yes` it places one order with the saved payment method, and refuses when another future order is already booked. It never adds or changes a card and never cancels an order.
- A cart write either sticks (verified by a re-read) or fails. It never silently does nothing.
- `history` counts what was packed, not what was ordered.

Auth failures return `error_type: auth` and one login line. The token is never printed.
