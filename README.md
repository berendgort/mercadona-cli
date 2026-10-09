# merca

Mercadona cart CLI for humans and agents. Search the public catalog, check the delivery window, change the basket when `--yes` is set, and stop before payment.

```bash
pipx install 'mercadona-cli[mcp] @ git+https://github.com/berendgort/mercadona-cli.git'
merca instruct --json
merca setup --cp 08860 --wh 3087 --json
merca login --token '<MO-user.token>' --uuid '<MO-user.uuid>' --json
merca search "leche" --json
```

The token comes from the tienda site local storage (`MO-user`). Do not put a password in the command or in the environment.

`merca checkout` prints the slot and stops. Pay in the Mercadona app.

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
