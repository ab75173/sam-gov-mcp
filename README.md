# sam-gov-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that lets an
LLM search federal contract opportunities on [SAM.gov](https://sam.gov). Ask in plain
English ("active small-business cybersecurity solicitations posted this month") and the
model calls these tools to pull and summarize matching opportunities.

This is a clean, tested **reference implementation** of an MCP server over a real federal
data source — built to learn the MCP server pattern and the SAM.gov procurement data
model. It is not affiliated with or endorsed by GSA or SAM.gov.

## Tools

| Tool | Description |
|------|-------------|
| `search_opportunities` | Search opportunities by title, posted-date window, notice type, set-aside, NAICS, state, and status. |
| `get_opportunity` | Fetch a single opportunity by its notice ID. |
| `list_set_aside_codes` | List valid set-aside and procurement-type codes (offline, no API key needed). |

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

## License

MIT — see [LICENSE](LICENSE).
