# AGENTS.md

`merca` looks up Mercadona products, fills the cart, books a slot (`checkout --confirm --yes`), edits a booked order, and learns from delivered orders.

Read `docs/objective_function.md`, `docs/code_quality.md`, `docs/data_engineering_standards.md`, and `docs/WIRE.md` before editing.

- Downward layers (`service` at 45 holds use cases shared by CLI and MCP). 250 lines. Frozen Pydantic. `mypy --strict`. No token in output.
- One writer per fact. Spend is the sum of line prices. PUT body comes from `build_put_body`.
- No fixture, no new wire field.
- `--yes` or the cart and the order do not change.
- Order writes: `checkout --confirm --yes` (place) and `order edit --yes`. Never cancel, never DELETE an order, never add or change a card.
- Every cart write is a full replacement with id + version, then re-read. A stale version returns 200 and changes nothing.
- Do not commit `session.json`.

```bash
python scripts/check_code_quality.py
ruff check .
mypy merca scripts/check_code_quality.py
pytest -q -m "not live"
```

Recipe for callers: `merca instruct --json`.

## Playbook

- [`docs/cli_playbook.md`](docs/cli_playbook.md) — how this stack was built; rate limits and stop rules
