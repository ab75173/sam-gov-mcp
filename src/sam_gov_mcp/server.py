"""FastMCP server exposing SAM.gov contract-opportunity search as MCP tools."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import SamGovClient, SamGovError
from .constants import PROCUREMENT_TYPES, SET_ASIDE_CODES

mcp = FastMCP("sam-gov")

API_KEY_ENV = "SAM_GOV_API_KEY"


def _make_client() -> SamGovClient:
    """Build a client from the environment, raising a clear error if the key is unset."""
    return SamGovClient(os.environ.get(API_KEY_ENV, ""))


@mcp.tool()
async def search_opportunities(
    title: str | None = None,
    posted_from: str | None = None,
    posted_to: str | None = None,
    procurement_type: str | None = None,
    set_aside: str | None = None,
    naics_code: str | None = None,
    state: str | None = None,
    status: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """Search active and historical federal contract opportunities on SAM.gov.

    Args:
        title: Keyword(s) to match against the opportunity title.
        posted_from: Earliest posted date, ISO format YYYY-MM-DD. Defaults to 30 days ago.
        posted_to: Latest posted date, ISO format YYYY-MM-DD. Defaults to today.
            The window between posted_from and posted_to cannot exceed one year.
        procurement_type: Notice-type code. One of:
            o=Solicitation, k=Combined Synopsis/Solicitation, p=Pre-solicitation,
            r=Sources Sought, s=Special Notice, a=Award Notice, u=Justification,
            g=Sale of Surplus Property, i=Intent to Bundle Requirements.
        set_aside: Set-aside code, e.g. SBA (Total Small Business), 8A, HZC (HUBZone),
            SDVOSBC, WOSB. Call list_set_aside_codes for the full table.
        naics_code: NAICS industry code (up to 6 digits), e.g. 541512.
        state: Two-letter place-of-performance state, e.g. VA.
        status: One of active, inactive, archived, cancelled, deleted.
        limit: Max results to return, 1-1000 (default 25).
        offset: Page index for pagination (default 0).

    Returns a dict with total_records, count, and a list of normalized opportunities.
    """
    try:
        async with _make_client() as client:
            return await client.search_opportunities(
                title=title,
                posted_from=posted_from,
                posted_to=posted_to,
                ptype=procurement_type,
                set_aside=set_aside,
                naics_code=naics_code,
                state=state,
                status=status,
                limit=limit,
                offset=offset,
            )
    except SamGovError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def get_opportunity(
    notice_id: str,
    posted_from: str | None = None,
) -> dict[str, Any]:
    """Fetch a single SAM.gov opportunity by its notice ID.

    Args:
        notice_id: The SAM.gov notice ID (the long alphanumeric id from a listing).
        posted_from: Optional earliest posted date (ISO YYYY-MM-DD) to widen the lookup
            window. The search defaults to the trailing year; pass this if the notice
            is older than that.

    Returns the full normalized opportunity, or an {"error": ...} dict if not found.
    """
    try:
        async with _make_client() as client:
            opportunity = await client.get_opportunity(
                notice_id, posted_from=posted_from
            )
            return opportunity.to_dict()
    except SamGovError as exc:
        return {"error": str(exc)}


@mcp.tool()
async def list_set_aside_codes() -> dict[str, Any]:
    """List the valid SAM.gov set-aside and procurement-type codes.

    Useful for translating a plain-English request (e.g. "small business HUBZone
    solicitations") into the codes the search_opportunities tool expects. This tool
    runs entirely offline and needs no API key.
    """
    return {
        "set_aside_codes": SET_ASIDE_CODES,
        "procurement_types": PROCUREMENT_TYPES,
    }


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
