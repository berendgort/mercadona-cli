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
merca cart add <id> --qty 1 --yes --json
merca slot --day LUN --label "De 11:00 a 13:00" --json
merca checkout --day LUN --label "De 11:00 a 13:00" --json
```

- Always pass `--json`.
- `error_type: ambiguous` means show `candidates` and wait for an id.
- `error_type: auth` means ask the human to run `merca login --token <MO-user.token> --uuid <MO-user.uuid>`.
- Without `--yes`, do not retry `cart add` against the network.
- `checkout` sets `stopped_before_pay`. Stop there.
