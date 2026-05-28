"""Typed async client for the SAM.gov Get Opportunities Public API (v2).

API reference: https://open.gsa.gov/api/get-opportunities-public-api/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

import httpx

BASE_URL = "https://api.sam.gov/opportunities/v2/search"
MAX_LIMIT = 1000
# The API rejects a postedFrom/postedTo window wider than one year.
MAX_WINDOW_DAYS = 365


class SamGovError(Exception):
    """Raised when a SAM.gov request fails for a reason worth surfacing to the caller."""


@dataclass
class Opportunity:
    """A single contract opportunity, normalized from the API's verbose record.

    Only the fields useful for a bid/no-bid first pass are kept; the raw record is
    preserved in ``raw`` for callers that need everything.
    """

    notice_id: str
    title: str
    solicitation_number: str | None
    agency: str | None
    posted_date: str | None
    response_deadline: str | None
    notice_type: str | None
    set_aside: str | None
    set_aside_code: str | None
    naics_code: str | None
    active: bool
    ui_link: str | None
    description_link: str | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Opportunity:
        active_raw = str(data.get("active", "")).strip().lower()
        return cls(
            notice_id=data.get("noticeId", ""),
            title=data.get("title", ""),
            solicitation_number=data.get("solicitationNumber") or None,
            agency=data.get("fullParentPathName") or None,
            posted_date=data.get("postedDate") or None,
            response_deadline=data.get("responseDeadLine") or None,
            notice_type=data.get("type") or None,
            set_aside=data.get("typeOfSetAsideDescription") or None,
            set_aside_code=data.get("typeOfSetAside") or None,
            naics_code=data.get("naicsCode") or None,
            active=active_raw == "yes",
            ui_link=data.get("uiLink") or None,
            description_link=data.get("description") or None,
            raw=data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "notice_id": self.notice_id,
            "title": self.title,
            "solicitation_number": self.solicitation_number,
            "agency": self.agency,
            "posted_date": self.posted_date,
            "response_deadline": self.response_deadline,
            "notice_type": self.notice_type,
            "set_aside": self.set_aside,
            "set_aside_code": self.set_aside_code,
            "naics_code": self.naics_code,
            "active": self.active,
            "ui_link": self.ui_link,
            "description_link": self.description_link,
        }


def _to_api_date(value: str) -> str:
    """Convert an ISO ``YYYY-MM-DD`` date to the API's ``MM/dd/yyyy`` format.

    Accepts the API format as-is so callers can pass either.
    """
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    raise SamGovError(
        f"Invalid date {value!r}. Use ISO format YYYY-MM-DD (e.g. 2026-05-27)."
    )


class SamGovClient:
    """Thin async wrapper over the SAM.gov Opportunities v2 search endpoint."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise SamGovError(
                "No SAM.gov API key provided. Set the SAM_GOV_API_KEY environment "
                "variable. Get a free key at https://sam.gov/content/api-keys."
            )
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> SamGovClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        params = {k: v for k, v in params.items() if v is not None}
        params["api_key"] = self._api_key
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.get(self._base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise SamGovError(_describe_status_error(exc)) from exc
        except httpx.RequestError as exc:
            raise SamGovError(
                f"Could not reach SAM.gov ({exc.__class__.__name__}). "
                "Check your network connection and try again."
            ) from exc
        finally:
            if self._client is None:
                await client.aclose()

    async def search_opportunities(
        self,
        *,
        title: str | None = None,
        posted_from: str | None = None,
        posted_to: str | None = None,
        ptype: str | None = None,
        set_aside: str | None = None,
        naics_code: str | None = None,
        state: str | None = None,
        status: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Search opportunities. Dates are ISO ``YYYY-MM-DD``.

        ``posted_from``/``posted_to`` default to the trailing 30 days because the
        API requires a date window whenever ``limit`` is supplied.
        """
        if limit < 1 or limit > MAX_LIMIT:
            raise SamGovError(f"limit must be between 1 and {MAX_LIMIT}.")
        if offset < 0:
            raise SamGovError("offset must be 0 or greater.")

        today = date.today()
        from_iso = posted_from or (today - timedelta(days=30)).isoformat()
        to_iso = posted_to or today.isoformat()
        self._validate_window(from_iso, to_iso)

        params = {
            "title": title,
            "postedFrom": _to_api_date(from_iso),
            "postedTo": _to_api_date(to_iso),
            "ptype": ptype,
            "typeOfSetAside": set_aside,
            "ncode": naics_code,
            "state": state,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
        payload = await self._get(params)
        opportunities = [
            Opportunity.from_api(item) for item in payload.get("opportunitiesData", [])
        ]
        return {
            "total_records": payload.get("totalRecords", 0),
            "limit": payload.get("limit", limit),
            "offset": payload.get("offset", offset),
            "count": len(opportunities),
            "opportunities": [opp.to_dict() for opp in opportunities],
        }

    async def get_opportunity(
        self,
        notice_id: str,
        *,
        posted_from: str | None = None,
        posted_to: str | None = None,
    ) -> Opportunity:
        """Fetch a single opportunity by its notice ID.

        Because the search endpoint requires a posted-date window, this looks back
        one year by default. Pass ``posted_from`` if the notice is older than that.
        """
        if not notice_id or not notice_id.strip():
            raise SamGovError("notice_id is required.")

        today = date.today()
        from_iso = posted_from or (today - timedelta(days=MAX_WINDOW_DAYS)).isoformat()
        to_iso = posted_to or today.isoformat()
        self._validate_window(from_iso, to_iso)

        params = {
            "noticeid": notice_id.strip(),
            "postedFrom": _to_api_date(from_iso),
            "postedTo": _to_api_date(to_iso),
            "limit": 1,
        }
        payload = await self._get(params)
        records = payload.get("opportunitiesData", [])
        if not records:
            raise SamGovError(
                f"No opportunity found with notice ID {notice_id!r} in the searched "
                "date window. If it is older than a year, pass an earlier posted_from."
            )
        return Opportunity.from_api(records[0])

    @staticmethod
    def _validate_window(from_iso: str, to_iso: str) -> None:
        try:
            start = date.fromisoformat(from_iso)
            end = date.fromisoformat(to_iso)
        except ValueError as exc:
            raise SamGovError("Dates must be ISO format YYYY-MM-DD.") from exc
        if start > end:
            raise SamGovError("posted_from must be on or before posted_to.")
        if (end - start).days > MAX_WINDOW_DAYS:
            raise SamGovError(
                "The posted-date window cannot exceed one year (SAM.gov constraint)."
            )


def _describe_status_error(exc: httpx.HTTPStatusError) -> str:
    status = exc.response.status_code
    if status in (401, 403):
        return (
            "SAM.gov rejected the request as unauthorized (HTTP "
            f"{status}). Your API key is missing, invalid, or not yet active."
        )
    if status == 429:
        return (
            "SAM.gov rate limit exceeded (HTTP 429). Public keys have a daily request "
            "cap; wait and retry, or request a higher-tier role."
        )
    if status == 400:
        return (
            f"SAM.gov rejected the request as malformed (HTTP 400): "
            f"{exc.response.text[:300]}"
        )
    return f"SAM.gov returned an unexpected error (HTTP {status})."
