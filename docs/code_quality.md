# Code quality

These rules are the bar for this repository. `scripts/check_code_quality.py` enforces the ones a script can see. `mypy --strict` enforces the types.

## Layers

Imports point downward. A module may import the same rank or a lower rank.

| Rank | Package | Owns |
|------|---------|------|
| 10 | `merca/models` | Frozen Pydantic DTOs. No I/O. |
| 15 | `merca/core/exceptions` | Error types. |
| 20 | `merca/http` | curl_cffi. No CLI imports. |
| 30 | `merca/core` | Envelope, paths, the profile store, instruct. |
| 40 | `merca/catalog`, `merca/basket`, `merca/policy` | Search, cart, slot, preflight. |
| 45 | `merca/service` | Use cases the CLI and MCP share: order show/edit, history, slots, checkout. |
| 50 | `merca/cli`, `merca/mcp` | Typer and FastMCP. They do not import each other. |

## File and function rules

- 250 lines or fewer per file under `merca/`.
- No work at import time. No network, no file reads, no prints in library modules.
- `print` is allowed only in `merca/cli/catch.py`.
- No em dash or en dash in Python.
- Every module has `__all__`.
- Public models are frozen Pydantic models, not dataclasses.
- `mypy --strict` is clean. No untyped public function.
- Fail closed with a typed exception. The envelope sets `error_type` and `retryable`.
- Do not log or print the session token. Session files are mode `0600`.

## Gate

```bash
python scripts/check_code_quality.py
ruff check .
mypy merca scripts/check_code_quality.py
pytest -q -m "not live"
```
