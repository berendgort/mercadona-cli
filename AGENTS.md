# AGENTS.md

`merca` looks up Mercadona products, checks a delivery slot, edits the cart, and edits the lines of a confirmed order. The human pays.

Read `docs/objective_function.md`, `docs/code_quality.md`, `docs/data_engineering_standards.md`, and `docs/WIRE.md` before editing.

- Downward layers. 250 lines. Frozen Pydantic. `mypy --strict`. No token in output.
- One writer per fact. Spend is the sum of line prices. PUT body comes from `build_put_body`.
- No fixture, no new wire field.
- `--yes` or the cart and the order do not change.
- Do not place a new order, cancel an order, or call payment. `order edit` is the only order write.
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
