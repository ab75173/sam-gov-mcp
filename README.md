# sam-gov-mcp

[![CI](https://github.com/ab75173/sam-gov-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ab75173/sam-gov-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that lets an
LLM search federal contract opportunities on [SAM.gov](https://sam.gov). Ask in plain
English — *"active small-business cybersecurity solicitations posted this month"* — and the
model calls these tools to pull and summarize matching opportunities.

It is a clean, typed, **tested reference implementation** of an MCP server over a real
federal data source, built to exercise the MCP server pattern end-to-end and to model the
SAM.gov procurement data domain. Several SAM.gov MCP servers already exist; the goal here is
not novelty but a well-engineered foundation layer (see [roadmap](#roadmap)). Not affiliated
with or endorsed by GSA or SAM.gov.

## Tools

| Tool | Description |
|------|-------------|
| `search_opportunities` | Search opportunities by title, posted-date window, notice type, set-aside, NAICS, state, and status. |
| `get_opportunity` | Fetch a single opportunity by its notice ID. |
| `list_set_aside_codes` | List valid set-aside and procurement-type codes (offline, no API key needed). |

## Example

Asked *"Find small-business solicitations for NAICS 541512 posted this month,"* the model
calls `search_opportunities(naics_code="541512", set_aside="SBA", procurement_type="o")`
and the server returns normalized records like:

```json
{
  "total_records": 3,
  "count": 3,
  "opportunities": [
    {
      "notice_id": "abc123def456",
      "title": "Cybersecurity Support Services",
      "solicitation_number": "W912-26-R-0001",
      "agency": "DEPT OF DEFENSE.DEPT OF THE ARMY",
      "posted_date": "2026-05-01",
      "response_deadline": "2026-06-15T17:00:00-04:00",
      "notice_type": "Combined Synopsis/Solicitation",
      "set_aside": "Total Small Business Set-Aside (FAR 19.5)",
      "set_aside_code": "SBA",
      "naics_code": "541512",
      "active": true,
      "ui_link": "https://sam.gov/opp/abc123def456/view"
    }
  ]
}
```

The server normalizes SAM.gov's verbose API records down to the fields useful for a
bid/no-bid first pass, while preserving the raw record internally.

## Requirements

- Python 3.10+
- A free SAM.gov API key — sign in at [sam.gov](https://sam.gov), open your profile, and
  generate a key under **API Key**.

## Install

```bash
git clone https://github.com/ab75173/sam-gov-mcp.git
cd sam-gov-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configure

Copy the example env file and add your key:

```bash
cp .env.example .env
# edit .env and set SAM_GOV_API_KEY=...
```

The server reads the key from the `SAM_GOV_API_KEY` environment variable. The `.env` file
is gitignored and must never be committed.

## Run with Claude Desktop

Add this to your `claude_desktop_config.json`
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "/absolute/path/to/sam-gov-mcp/.venv/bin/sam-gov-mcp",
      "env": {
        "SAM_GOV_API_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop. You should see the `sam-gov` tools available. Try:

> Find active small-business cybersecurity solicitations posted in the last month.

## Develop

```bash
pytest        # run the test suite (fully mocked — no key or network needed)
ruff check .  # lint
```

See [BUILD.md](BUILD.md) for a full step-by-step walkthrough from clone to a running
server inside Claude Desktop.

## Design notes

A few SAM.gov API quirks the client handles so callers (and the LLM) don't have to:

- **Date formats.** The API expects `MM/dd/yyyy`, but LLMs reason in ISO dates. Tools
  accept `YYYY-MM-DD` and convert internally.
- **Mandatory date window.** The search endpoint requires `postedFrom`/`postedTo` whenever
  `limit` is set, and rejects windows wider than one year. The client defaults to a sensible
  trailing window and validates the span before calling out.
- **Auth as a query param.** The key is passed as `api_key`, sourced from the
  `SAM_GOV_API_KEY` environment variable and never logged or committed.
- **Friendly errors.** HTTP 401/403, 429 (rate limit), 400, and network failures are
  translated into actionable messages instead of raw stack traces, so the model can relay
  what went wrong.

Tests are fully mocked with `httpx.MockTransport`, so the suite runs without an API key or
network access — which also keeps CI hermetic.

## Roadmap

This is repo 1 of a small series. It is intentionally the **foundation layer**: clean data
access that higher-value work builds on.

1. **sam-gov-mcp** *(this repo)* — opportunity search over the SAM.gov v2 API.
2. **procurement-agent-evals** *(planned)* — a bid/no-bid agent on top of this server, with a
   functional eval framework that grades its recommendations.
3. **pre-ATO assessment harness** *(planned)* — maps adversarial/red-team findings to
   NIST 800-53 controls and MITRE ATLAS techniques to produce a pre-authorization evidence
   report for federal LLM deployments.

## License

MIT — see [LICENSE](LICENSE).
