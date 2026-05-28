"""Tests for the MCP server layer: tool registration and offline behavior."""

from __future__ import annotations

import pytest

from sam_gov_mcp import server
from sam_gov_mcp.server import (
    list_set_aside_codes,
    mcp,
    search_opportunities,
)


@pytest.mark.asyncio
async def test_all_three_tools_registered():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert names == {
        "search_opportunities",
        "get_opportunity",
        "list_set_aside_codes",
    }


@pytest.mark.asyncio
async def test_list_set_aside_codes_is_offline():
    result = await list_set_aside_codes()
    assert "SBA" in result["set_aside_codes"]
    assert "8A" in result["set_aside_codes"]
    assert result["procurement_types"]["o"] == "Solicitation"


@pytest.mark.asyncio
async def test_search_without_api_key_returns_error(monkeypatch):
    monkeypatch.delenv(server.API_KEY_ENV, raising=False)
    result = await search_opportunities(title="cyber")
    assert "error" in result
    assert "API key" in result["error"]
