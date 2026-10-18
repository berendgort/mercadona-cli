---
name: merca
description: Drive the merca CLI for Mercadona search, cart, booking a delivery slot, editing a booked order, and purchase history. Use when the user wants a Mercadona basket, a product id, a delivery, or to trim an order. Never cancel an order or touch a card.
---

# merca

The cart is right, or the command fails. The human pays in the Mercadona app.

```bash
merca instruct --json
merca history --orders 16 --json            # what we really buy, per product
merca orders --limit 8 --json
merca order show <order_id> --json          # confirmed: lines + deadline; delivered: packed
merca order edit <order_id> --file f.txt --json        # dry run diff
merca order edit <order_id> --file f.txt --yes --json  # save
merca search "leche" --json
merca cart fill --file lines.txt --replace --yes --json
merca slots --json
merca checkout --day LUN,MAR,MIE --label 11:00-18:00 --json                  # dry run
merca checkout --day LUN,MAR,MIE --label 11:00-18:00 --confirm --yes --json  # books it
```

- Always pass `--json`.
- `error_type: ambiguous` means show `candidates` and wait for an id.
- `error_type: auth` → show `merca instruct --json` → `data.login_howto` to the human. Need **Local Storage → MO-user → token + uuid**. Cookies (`__mo_da`, `_abck`, …) are wrong. Human runs `merca login` in their own terminal.
- Without `--yes`, do not retry `cart add` against the network.
- `checkout --confirm --yes` books the order with the saved card. It refuses when a future order already exists: edit that one instead. `needs_authentication` = human finishes 3-D Secure in the app.
- Every cart write is verified by a re-read. `order edit` refuses after `changes_until`.
- `orders` is id, status, slot, totals. `receipt` writes a PDF. Do not print the PDF or any address.
