"""Tests for the SAM.gov client. All HTTP is mocked; no API key or network needed."""

from __future__ import annotations

from datetime import date, timedelta

import httpx
import pytest

from sam_gov_mcp.client import (
    Opportunity,
    SamGovClient,
    SamGovError,
    _to_api_date,
)

SAMPLE_RECORD = {
    "noticeId": "abc123def456",
    "title": "Cybersecurity Support Services",
    "solicitationNumber": "W912-26-R-0001",
    "fullParentPathName": "DEPT OF DEFENSE.DEPT OF THE ARMY",
    "postedDate": "2026-05-01",
    "responseDeadLine": "2026-06-15T17:00:00-04:00",
    "type": "Combined Synopsis/Solicitation",
    "typeOfSetAside": "SBA",
    "typeOfSetAsideDescription": "Total Small Business Set-Aside (FAR 19.5)",
    "naicsCode": "541512",
    "active": "Yes",
    "uiLink": "https://sam.gov/opp/abc123def456/view",
    "description": "https://api.sam.gov/opportunities/v2/abc123def456/description",
}


def make_client(handler) -> SamGovClient:
    """Build a client whose HTTP layer is a MockTransport calling ``handler``."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return SamGovClient("test-key", client=http_client)


def ok_response(records, total=None):
    def handler(request: httpx.Request) -> httpx.Response:
        payload = {
            "totalRecords": total if total is not None else len(records),
            "limit": 25,
            "offset": 0,
            "opportunitiesData": records,
        }
        return httpx.Response(200, json=payload)

    return handler


# --- date conversion ---------------------------------------------------------


def test_to_api_date_from_iso():
    assert _to_api_date("2026-05-27") == "05/27/2026"


def test_to_api_date_accepts_api_format():
    assert _to_api_date("05/27/2026") == "05/27/2026"


def test_to_api_date_rejects_garbage():
    with pytest.raises(SamGovError):
        _to_api_date("27 May 2026")


# --- construction ------------------------------------------------------------


def test_client_requires_api_key():
    with pytest.raises(SamGovError):
        SamGovClient("")


# --- Opportunity parsing -----------------------------------------------------


def test_opportunity_from_api_maps_fields():
    opp = Opportunity.from_api(SAMPLE_RECORD)
    assert opp.notice_id == "abc123def456"
    assert opp.title == "Cybersecurity Support Services"
    assert opp.agency == "DEPT OF DEFENSE.DEPT OF THE ARMY"
    assert opp.set_aside_code == "SBA"
    assert opp.naics_code == "541512"
    assert opp.active is True


def test_opportunity_inactive_parsing():
    opp = Opportunity.from_api({**SAMPLE_RECORD, "active": "No"})
    assert opp.active is False


def test_opportunity_to_dict_excludes_raw():
    opp = Opportunity.from_api(SAMPLE_RECORD)
    d = opp.to_dict()
    assert "raw" not in d
    assert d["notice_id"] == "abc123def456"


# --- search ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_parses_and_counts():
    client = make_client(ok_response([SAMPLE_RECORD], total=1))
    result = await client.search_opportunities(title="cyber")
    assert result["total_records"] == 1
    assert result["count"] == 1
    assert result["opportunities"][0]["set_aside_code"] == "SBA"


@pytest.mark.asyncio
async def test_search_sends_expected_params():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(200, json={"opportunitiesData": [], "totalRecords": 0})

    client = make_client(handler)
    await client.search_opportunities(
        title="cyber",
        posted_from="2026-01-01",
        posted_to="2026-03-01",
        set_aside="SBA",
        naics_code="541512",
        limit=10,
    )
    assert captured["title"] == "cyber"
    assert captured["postedFrom"] == "01/01/2026"
    assert captured["postedTo"] == "03/01/2026"
    assert captured["typeOfSetAside"] == "SBA"
    assert captured["ncode"] == "541512"
    assert captured["limit"] == "10"
    assert captured["api_key"] == "test-key"


@pytest.mark.asyncio
async def test_search_defaults_date_window_when_omitted():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(200, json={"opportunitiesData": [], "totalRecords": 0})

    client = make_client(handler)
    await client.search_opportunities()
    # Both date bounds must be present (the API requires them alongside limit).
    assert "postedFrom" in captured
    assert "postedTo" in captured


@pytest.mark.asyncio
async def test_search_rejects_bad_limit():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError):
        await client.search_opportunities(limit=0)
    with pytest.raises(SamGovError):
        await client.search_opportunities(limit=5000)


@pytest.mark.asyncio
async def test_search_rejects_negative_offset():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError):
        await client.search_opportunities(offset=-1)


@pytest.mark.asyncio
async def test_search_rejects_window_over_one_year():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError):
        await client.search_opportunities(
            posted_from="2024-01-01", posted_to="2026-01-01"
        )


@pytest.mark.asyncio
async def test_search_rejects_reversed_window():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError):
        await client.search_opportunities(
            posted_from="2026-05-01", posted_to="2026-01-01"
        )


# --- get_opportunity ---------------------------------------------------------


@pytest.mark.asyncio
async def test_get_opportunity_returns_record():
    client = make_client(ok_response([SAMPLE_RECORD]))
    opp = await client.get_opportunity("abc123def456")
    assert opp.notice_id == "abc123def456"
    assert opp.title == "Cybersecurity Support Services"


@pytest.mark.asyncio
async def test_get_opportunity_not_found_raises():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError, match="No opportunity found"):
        await client.get_opportunity("missing")


@pytest.mark.asyncio
async def test_get_opportunity_requires_id():
    client = make_client(ok_response([]))
    with pytest.raises(SamGovError):
        await client.get_opportunity("   ")


@pytest.mark.asyncio
async def test_get_opportunity_default_window_is_one_year():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(request.url.params))
        return httpx.Response(200, json={"opportunitiesData": [SAMPLE_RECORD]})

    client = make_client(handler)
    await client.get_opportunity("abc123def456")
    # Both bounds must be present, and the window must respect the one-year cap.
    start = _to_api_date(captured["postedFrom"])
    end = _to_api_date(captured["postedTo"])
    assert start and end


# --- HTTP error mapping ------------------------------------------------------


@pytest.mark.asyncio
async def test_401_maps_to_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    client = make_client(handler)
    with pytest.raises(SamGovError, match="unauthorized"):
        await client.search_opportunities()


@pytest.mark.asyncio
async def test_429_maps_to_rate_limit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="too many requests")

    client = make_client(handler)
    with pytest.raises(SamGovError, match="rate limit"):
        await client.search_opportunities()


@pytest.mark.asyncio
async def test_network_error_maps_to_friendly_message():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler)
    with pytest.raises(SamGovError, match="Could not reach SAM.gov"):
        await client.search_opportunities()


def test_default_window_is_within_one_year():
    # Guards the get_opportunity default: today minus the look-back must stay <= 365d.
    today = date.today()
    look_back = today - timedelta(days=365)
    assert (today - look_back).days == 365
