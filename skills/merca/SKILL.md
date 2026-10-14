---
name: merca
description: Drive the merca CLI for Mercadona search, cart edits, and delivery slots. Use when the user wants a Mercadona basket, a product id, or a Monday delivery window. Never pay.
---

# merca

The cart is right, or the command fails. The human pays in the Mercadona app.

```bash
merca instruct --json
merca setup --cp 08860 --wh 3087 --json
merca search "leche" --json
merca orders --limit 8 --json
merca receipt <order_id> --out ticket.pdf --json
merca cart add <id> --qty 1 --yes --json
merca cart fill --file lines.txt --yes --json
merca slot --day LUN --label "De 11:00 a 13:00" --json
merca checkout --day LUN --label "De 11:00 a 13:00" --json
```

- Always pass `--json`.
- `error_type: ambiguous` means show `candidates` and wait for an id.
- `error_type: auth` → show `merca instruct --json` → `data.login_howto` to the human. Need **Local Storage → MO-user → token + uuid**. Cookies (`__mo_da`, `_abck`, …) are wrong. Human runs `merca login` in their own terminal.
- Without `--yes`, do not retry `cart add` against the network.
- `checkout` loads the live cart, runs preflight, sets `stopped_before_pay`. Stop there.
- `orders` is id, status, slot, totals. `receipt` writes a PDF. Do not print the PDF or any address.
