# Objective

The cart holds the products for the next delivery, inside the household window, and the human pays in the Mercadona app.

A run is good when all of these are true:

- Search either returns one product or `error_type: ambiguous` with candidates. It does not guess.
- `cart add` and `cart remove` send a PUT only when `--yes` is present.
- The slot is Monday, Tuesday, or Wednesday, and the hours sit inside 11:00 to 18:00. Friday never passes.
- Preflight rejects a blacklist hit, a duplicate, a quantity above 18, a cart outside 10 to 65 lines, or a spend outside 50 to 260 euros. Line prices are the spend.
- `checkout` prints the slot and stops. The process never confirms an order and never pays.

Auth failures return `error_type: auth` and one login line. The token is never printed.
