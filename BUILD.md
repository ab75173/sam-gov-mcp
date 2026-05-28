# BUILD.md — from empty machine to a running, public, CI-green MCP server

This is the copy-paste walkthrough for setting up `sam-gov-mcp` from scratch, verifying it
works, and getting it onto GitHub. Every command is runnable as-is on macOS/Linux. The
only things that need your input are your SAM.gov API key (Step 1) and your GitHub handle
(already set to `ab75173` throughout — change it if that's not you).

---

## Step 1 — Get a SAM.gov API key

1. Go to [sam.gov](https://sam.gov) and sign in (create an account if needed).
2. Open your profile menu → **Account Details**.
3. Under **API Key**, generate a new key and copy it.

Public keys have a daily request cap. That's fine for development and demos.

> The key is a secret. It goes in a local `.env` file that is gitignored. It must never be
> committed or pasted into a public place.

---

## Step 2 — Set up the project locally

```bash
cd ~/dev/sam-gov-mcp          # the repo you just built
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Using a virtualenv matters: the `mcp` package depends on `PyJWT`, which can collide with a
system-managed `PyJWT` if you install into the base Python. The venv has its own isolated
package space and avoids the collision entirely.

---

## Step 3 — Add your key

```bash
cp .env.example .env
# open .env and set:  SAM_GOV_API_KEY=your_real_key
```

Confirm the real `.env` is ignored before you ever commit:

```bash
git check-ignore .env        # should print ".env"
```

The server reads `SAM_GOV_API_KEY` from the environment. For local CLI testing you can
export it: `export SAM_GOV_API_KEY=$(grep -v '^#' .env | cut -d= -f2-)`.

---

## Step 4 — Verify it works

```bash
pytest -v        # all tests pass, fully mocked (no key or network needed)
ruff check .     # clean
```

Confirm the server boots and registers its tools:

```bash
python -c "import asyncio; from sam_gov_mcp.server import mcp; \
print([t.name for t in asyncio.run(mcp.list_tools())])"
```

Expected:

```
['search_opportunities', 'get_opportunity', 'list_set_aside_codes']
```

---

## Step 5 — Use it inside Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) and add:

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "/Users/adam/dev/sam-gov-mcp/.venv/bin/sam-gov-mcp",
      "env": { "SAM_GOV_API_KEY": "your_real_key" }
    }
  }
}
```

Use the absolute path to the `sam-gov-mcp` script inside your venv. Restart Claude Desktop,
then try:

> Find active small-business cybersecurity solicitations posted in the last month.

---

## Step 6 — Push to GitHub

The first commit and repo creation (this was done for you, but here's the equivalent):

```bash
git add -A
git commit -m "Initial commit: SAM.gov MCP server (search, get, set-aside codes)"
git branch -M main
gh repo create ab75173/sam-gov-mcp --public --source=. --remote=origin --push
```

Then watch CI go green:

```bash
gh run watch
```

CI runs lint + tests on Python 3.10, 3.11, and 3.12 (`.github/workflows/ci.yml`).

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `unauthorized (HTTP 401/403)` | Key missing, wrong, or not yet active. Re-check `.env`. New keys can take a short while to activate. |
| `rate limit exceeded (HTTP 429)` | Public-key daily cap hit. Wait, or request a higher-tier role on SAM.gov. |
| `No opportunity found ... in the searched date window` | `get_opportunity` looks back one year by default. Pass `posted_from` to widen for older notices. |
| `PyJWT` install conflict | You installed into system Python. Use the venv (Step 2). |
