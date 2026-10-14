"""Orders stay free of address, phone, and card data."""

from __future__ import annotations

import json
from pathlib import Path

from merca.basket.orders import parse_orders, save_receipt
from merca.core.exceptions import MercaHTTPError
from merca.http.client import HttpClient
from merca.models.profile import Session

ROOT = Path(__file__).resolve().parents[1]


def test_parse_orders_drops_pii() -> None:
    payload = json.loads((ROOT / "fixtures" / "orders_page.json").read_text(encoding="utf-8"))
    rows = parse_orders(payload)
    assert len(rows) == 1
    blob = json.dumps(rows[0].model_dump(mode="json"))
    assert rows[0].id == "1001"
    assert rows[0].status == "delivered"
    assert rows[0].products_eur == "40.00"
    assert rows[0].total_eur == "48.20"
    assert "redacted" not in blob
    assert "0000" not in blob
    assert "+34" not in blob


def test_receipt_writes_pdf_and_hides_the_token(tmp_path: Path) -> None:
    def ok(*_args: object, **_kwargs: object) -> tuple[int, bytes]:
        return 200, b"%PDF-1.4\n" + b"x" * 120

    client = HttpClient(token="SECRET-TOKEN", bytes_transport=ok)
    session = Session(token="SECRET-TOKEN", uuid="user-uuid")
    dest = tmp_path / "ticket.pdf"
    saved = save_receipt(session, "3087", "1001", dest, client=client)
    assert dest.read_bytes().startswith(b"%PDF")
    assert saved["bytes"] == dest.stat().st_size
    assert "SECRET-TOKEN" not in json.dumps(saved)

    def boom(*_args: object, **_kwargs: object) -> tuple[int, bytes]:
        raise RuntimeError("Bearer SECRET-TOKEN")

    broken = HttpClient(token="SECRET-TOKEN", bytes_transport=boom)
    try:
        broken.request_bytes("GET", "https://tienda.mercadona.es/api/orders/1/receipt/")
    except MercaHTTPError as exc:
        assert "SECRET-TOKEN" not in str(exc)
    else:
        raise AssertionError("expected HTTP error")
