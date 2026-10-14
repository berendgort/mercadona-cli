# merca

Mercadona cart CLI for humans and agents. Search the public catalog, check the delivery window, change the basket when `--yes` is set, and stop before payment.

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

`merca cart fill --file lines.txt --yes` sets many quantities in one request. Each line is `product_id qty`.

`merca checkout` loads the live cart when you are logged in, runs preflight, prints the slot, and stops. Pay in the Mercadona app.

## For AI agents

1. Run `merca instruct --json` and follow `data.flows`.
2. Pass `--json` on every command. Read `ok`, `error_type`, `retryable`.
3. `ambiguous` includes `candidates`. Ask for an id or pass one.
4. `auth` includes `human_fix`. Ask the human to run `merca login`. Do not invent a token.
5. `cart add` and `cart remove` without `--yes` return `validation_error` and do not call the API.
6. There is no pay command. Do not add one.

## Quality gate

```bash
python scripts/check_code_quality.py
ruff check .
mypy merca scripts/check_code_quality.py
pytest -q -m "not live"
```

Live search: `pytest -q -m live`.
