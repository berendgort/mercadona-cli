# merca

Mercadona CLI for humans and agents. Search the catalog, fill the basket, book a delivery slot, edit the booked order before its deadline, and learn from past deliveries. Every write needs `--yes`.

```bash
pipx install 'mercadona-cli[mcp] @ git+https://github.com/berendgort/mercadona-cli.git'
merca instruct --json
merca setup --cp 08860 --wh 3087 --json
merca login --token '<token>' --uuid '<uuid>' --json
merca search "leche" --json
```

### Login (Local Storage — not Cookies)

1. Open [tienda.mercadona.es](https://tienda.mercadona.es) and stay logged in (`Hola …`).
2. F12 → **Application** → **Local Storage** → `https://tienda.mercadona.es`.
3. Click the key **`MO-user`**. Copy the JSON fields **`token`** and **`uuid`**.
4. Run `merca login` in your own terminal (do not paste the token into chat).

**Wrong panel:** Cookies (`__mo_ca`, `__mo_da`, `__mo_ui`, `_abck`, `bm_sz`, Amplitude, `g_state`) are not used by `merca`. Do not put a password in the command or in the environment.

`merca orders` lists recent tickets (id, status, slot, totals). `merca receipt <id> --out ticket.pdf` saves the PDF. Neither prints an address, a phone, or a card.

`merca history --orders 16` learns from what was actually packed in your delivered orders: how many orders each product was in, quantity per week, and how many days between buys. Delivered orders are cached under `~/.config/merca/cache/`.

`merca cart fill --file lines.txt --yes` sets quantities (`product_id qty`, `0` removes). `--replace` makes the cart exactly the file. `merca cart clear --yes` empties it. Every write is re-read; a write that did not stick is an error.

`merca slots` lists delivery slots in local time. `merca checkout --day LUN,MAR,MIE --label 11:00-18:00` runs preflight and shows the slot it would book. Add `--confirm --yes` to place the order with the account's saved payment method. It refuses when another future order is already booked, and it never adds or changes a card. If the bank wants 3-D Secure, the result says `needs_authentication` and you finish in the app.

`merca order show <id>`: for a confirmed order, the lines and the change deadline; for a delivered one, what was packed and any shortages. `merca order edit <id> --file lines.txt` prints the diff; `--yes` saves it. Absolute quantities, `0` removes, a new id is added, unlisted lines stay. It refuses after `changes_until` and refuses to empty the order.

The loop this enables: book the slot early, then trim or top up the order before its deadline, and let `history` say what you really eat.

## For AI agents

1. Run `merca instruct --json` and follow `data.flows`.
2. Pass `--json` on every command. Read `ok`, `error_type`, `retryable`.
3. `ambiguous` includes `candidates`. Ask for an id or pass one.
4. `auth` includes `human_fix`. Ask the human to run `merca login`. Do not invent a token.
5. Writes without `--yes` return `validation_error` and do not call the API.
6. `checkout --confirm --yes` is the only way an order is placed. Nothing cancels an order or touches a card.

## Quality gate

```bash
python scripts/check_code_quality.py
ruff check .
mypy merca scripts/check_code_quality.py
pytest -q -m "not live"
```

Live search: `pytest -q -m live`.
