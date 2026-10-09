"""MCP server builds without importing the CLI."""

from __future__ import annotations

from merca.mcp.server import build_server


def test_mcp_server_builds() -> None:
    server = build_server()
    assert server is not None
    assert type(server).__name__ == "FastMCP"
