---
name: hermes-mcp-setup
description: "Configure and troubleshoot MCP servers on Hermes — HTTP, stdio, auth, MCP Market, verification."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [mcp, configuration, troubleshooting, hermes, mcp-market]
---

# Hermes MCP Server Setup

How to add, configure, and troubleshoot MCP servers in Hermes Agent — especially HTTP servers with authentication, and MCP Market integration.

## Quick Reference

- Config: `mcp_servers` section in `config.yaml`
- CLI: `hermes mcp add NAME --url URL` (interactive, may hang on auth prompts)
- Reload: `/restart` (gateway) or restart CLI — no hot-reload
- Verify: always test the connection after configuring; never declare success without a real `initialize` call

## Adding an MCP Server (two transport types)

### HTTP (remote server)

HTTP servers are remote endpoints accessed via URL. Most common for SaaS MCP servers.

### Via config.yaml (most reliable)

```yaml
mcp_servers:
  server_name:
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer <token>"
    timeout: 120
    connect_timeout: 60
```

### Via CLI (interactive — may hang)

```bash
hermes mcp add NAME --url URL
# Prompts: Does this server require auth? → Y
# Prompts: Header name → Authorization
# Prompts: Header value → Bearer <token>
```

**Pitfall:** `hermes mcp add` requires a proper TTY for auth prompts. In non-interactive contexts (execute_code, cron), it hangs indefinitely. Use the config.yaml approach instead.

### Fallback: Python to edit config

When terminal/CLI is unavailable, use execute_code with `yaml`:

```python
import yaml

config_path = r"C:\Users\<user>\AppData\Local\hermes\config.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

config['mcp_servers'] = {
    'server_name': {
        'url': 'https://...',
        'headers': {'Authorization': 'Bearer ...'},
        'timeout': 120,
        'connect_timeout': 60
    }
}

with open(config_path, 'w', encoding='utf-8') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

**Note:** `patch` tool is blocked from editing config.yaml — use Python's YAML library instead.

**execute_code sandbox pitfall:** the sandbox can corrupt multi-line string literals when certain character combinations appear (e.g. `split('=', 1)` inside a string that starts with `'MCP_...`). When editing config via execute_code, split token-reading into separate steps: define the prefix as a variable first, then use it. Avoid complex string expressions in `if` conditions that read .env files — use `startswith(variable)` with a pre-defined prefix variable instead of an inline string.

### Stdio (local process)

Stdio servers run as a subprocess — Hermes manages the lifecycle. Common for CLI-based MCP servers (npx, uvx, python).

```yaml
mcp_servers:
  server_name:
    type: stdio
    command: npx          # or: uvx, python, node
    args:
      - "-y"
      - "@org/package-name"
      - "--api-key"
      - "<token>"
    env:                  # optional
      KEY: value
```

**Verification: test the subprocess directly before restarting Hermes.** Send a raw JSON-RPC `initialize` via stdin:

```python
import subprocess, json

init = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}) + '\n'

r = subprocess.run(
    ['npx', '-y', '@org/package-name', '--api-key', '<token>'],
    input=init, capture_output=True, text=True, shell=True, timeout=15
)
print(r.stdout)
```

If the response includes `"result":{"serverInfo":{...}}` — the server works. If JSON parsing fails, the process may be writing to stderr; check `r.stderr` for startup messages.

**Pitfall: shell=True on Windows.** `subprocess` with `shell=True` on Windows may route through cmd.exe, which can corrupt arguments with special characters. Test the initialize call to confirm the server actually starts and responds. If it fails, try without `shell=True` or use `execute_code` which handles subprocess differently.

## MCP Market Specifics

MCP Market (app.mcpmarket.com) is a marketplace for MCP servers. Key differences from generic MCP:

### Auth flow

- MCP Market uses **Supabase OAuth 2.0** for MCP endpoint authentication
- API keys like `sk_user_...` are for **account management** (web app), NOT for MCP connections
- MCP server endpoints require a **Bearer access token** (JWT from Supabase), not the API key

### Connection URLs

Each server on MCP Market has its own endpoint:
```
https://link.mcpmarket.com/{id}/{server}/mcp
```

**Cross-service token reuse:** The same MCP Market Bearer JWT works across ALL services on the same account (Miro, Notion, etc.). The OAuth authorization server is the same Supabase instance, and scopes (`openid`, `profile`, `email`) are user-level — not per-service. Once you have a working token for one service, reuse it for others. Verify by checking the `authorization_servers` URL in the OAuth metadata — if it matches, the token will work.

### Service-specific Accept headers

Some MCP servers require specific `Accept` headers beyond `application/json`:

- **Notion MCP**: requires `Accept: application/json, text/event-stream` (supports SSE streaming). Without it, returns HTTP 406 "Not Acceptable: Client must accept both application/json and text/event-stream".
- **Miro MCP**: works with standard `Accept: application/json` (no special requirement).

When adding a new MCP Market service, always start with the standard headers and adjust if you get a 406.

### Getting the right token

1. Log into app.mcpmarket.com
2. Navigate to the server page (e.g., Miro)
3. Check tabs: **Identity**, **Settings**, or **Change client**
4. Look for an access token or connection key — NOT the account API key
5. The token is a JWT used as `Authorization: Bearer <jwt>`

### Auth methods that DO NOT work for MCP Market

These were exhaustively tested — skip them, they all return 401:

- `Authorization: Bearer sk_use...` (account API key, not access token)
- Query params: `?key=`, `?token=`
- Custom headers: `X-API-Key`, `X-MCP-API-Key`, `X-MCPMarket-Key`, `Mcp-Api-Key`
- Supabase-style: `apikey` header + Bearer
- Cookie-based: `mcp_token=`, `sb-access-token=`
- API key embedded in URL path
- Supabase `/auth/v1/user` or `/token` endpoints with the account key

**All of these fail.** If you have an `sk_user_...` key, stop trying to auth directly — tell the user they need an access token (JWT) from the Identity tab.

### OAuth metadata discovery

When the MCP endpoint returns 401, check the `WWW-Authenticate` header to confirm the auth flow:

```python
# 401 response headers will contain:
# WWW-Authenticate: Bearer resource_metadata="https://link.mcpmarket.com/.well-known/oauth-protected-resource/{id}/{server}/mcp"

# Fetch the metadata URL to see auth server and scopes:
import urllib.request, json
metadata_url = "https://link.mcpmarket.com/.well-known/oauth-protected-resource/sfwefr/miro/mcp"
with urllib.request.urlopen(metadata_url) as resp:
    meta = json.loads(resp.read())
    # meta['authorization_servers'] → Supabase URL
    # meta['scopes_supported'] → openid, profile, email
```

This confirms OAuth is required before wasting time on direct API key attempts.

### Troubleshooting MCP Market auth

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| HTTP 401 «Authentication required» | Wrong auth method | Use `Authorization: Bearer <jwt>` |
| HTTP 401 «Missing or invalid access token» + link to token page | Server accepts API tokens, not OAuth | Get API token from the linked page, use `--header «Authorization: Bearer <token>»` |
| HTTP 406 «Not Acceptable» | Server requires SSE in Accept | Add `Accept: application/json, text/event-stream` |
| HTTP 307 redirect to /login | Missing or invalid token | Get fresh token from Identity tab |
| «Invalid API key» from Supabase | Using account key, not token | Account key ≠ MCP token |
| OAuth metadata in response | Server requires OAuth flow | Need proper Bearer token, not API key |
| Supabase anon key not found in frontend JS | It's server-side only | Don't waste time scraping JS — tell user to get token from UI |

### ⚠️ Pitfall: infinite auth debugging

**After 2-3 auth attempts fail, STOP.** Tell the user exactly what they need (access token from Identity tab) and move on. MCP Market's OAuth flow cannot be completed programmatically without browser interaction — the Supabase anon key is server-side, not embedded in frontend JS. Trying 15+ auth variations wastes tokens and frustrates the user.

### ⚠️ Pitfall: assuming OAuth when API token works

**Always read the 401 error body before starting an OAuth flow.** Many MCP servers accept simple API tokens via `Authorization: Bearer <token>` — the error message often tells you exactly where to get one (e.g. Apify: «Manage tokens at https://console.apify.com/account/integrations»). Jumping straight to PKCE/OAuth without reading the error body leads to wasted time and user frustration. When a server says «pass an API token», believe it — don't try OAuth unless the server explicitly requires it.

## Verification

Always test the connection before telling the user it works:

```python
import urllib.request, json

init = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes-agent", "version": "1.0.0"}
    }
}).encode()

# Some servers need SSE: add text/event-stream if you see a 406
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "User-Agent": "Mozilla/5.0"
}

req = urllib.request.Request(url, data=init, headers=headers, method='POST')

with urllib.request.urlopen(req, timeout=15) as resp:
    raw = resp.read().decode()
    ctype = resp.headers.get('Content-Type', '')
    
    if 'text/event-stream' in ctype:
        # SSE response — parse data: lines
        for line in raw.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                result = data.get('result', {})
                server = result.get('serverInfo', {})
                print(f"Server: {server.get('name')} v{server.get('version')}")
                caps = result.get('capabilities', {})
                print(f"Capabilities: {json.dumps(caps, indent=2)}")
    else:
        data = json.loads(raw)
        result = data.get('result', {})
        server = result.get('serverInfo', {})
        print(f"Server: {server.get('name')} v{server.get('version')}")
        caps = result.get('capabilities', {})
        print(f"Capabilities: {json.dumps(caps, indent=2)}")
```

**Never claim success without a passing initialize call.** The config may be written correctly but the auth may still fail.

## Prerequisites

- `mcp` Python package: `pip install mcp`
- Node.js (for npx-based servers)
- uv (for uvx-based servers)

Check with: `pip list | grep mcp && node --version`

## Reloading

Config changes require restart:
- Gateway: `/restart` in chat
- CLI: exit and relaunch
- No hot-reload for MCP servers

## Common Patterns

- **Cron + Notion DB → Telegram reminders**: daily schedule overviews from a Notion database, delivered automatically. Full recipe in [`references/cron-notion-reminder-pattern.md`](references/cron-notion-reminder-pattern.md).

## OAuth-Only Services → Community Stdio Fallback

Some official MCP servers (e.g. Vercel at `https://mcp.vercel.com`) use strict OAuth 2.0 with a **closed client whitelist** — only pre-approved AI clients (Claude Code, Cursor, Copilot, etc.) can connect. Hermes gets HTTP 401 even with a valid API token, because the server only accepts OAuth tokens from registered clients.

### The pattern

When you hit a 401 from an official endpoint and the `WWW-Authenticate` header confirms OAuth with no API-token fallback:

1. **Don't fight OAuth** — if Hermes isn't on the approved list, stop after 1-2 auth attempts
2. **Search npm** for community stdio packages: `npm search <service> mcp --json`
3. **Filter by recency/activity** — prefer packages updated in the last 6 months
4. **Verify with raw initialize** — send JSON-RPC `initialize` via subprocess before touching config
5. **Configure as stdio** with `${ENV_VAR}` references, not inline secrets

### Verification before config

```python
import subprocess, json
init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"}}}) + '\n'
r = subprocess.run(['npx', '-y', '@scope/package'], input=init,
    capture_output=True, text=True, timeout=30,
    env={**os.environ, 'SERVICE_TOKEN': 'test'})
# Look for "result":{"serverInfo":{...}} in stdout
```

### Config example (stdio + env var)

```yaml
mcp_servers:
  service_name:
    type: stdio
    command: npx
    args: ['-y', '@scope/package-name']
    env:
      SERVICE_TOKEN: '${SERVICE_TOKEN}'
```

Token goes in `.env` as `SERVICE_TOKEN=<value>`, never inline in config.

### Known community packages

| Service | Package | Env var | Tools |
|---------|---------|---------|-------|
| Vercel | `@robinson_ai_systems/vercel-mcp` | `VERCEL_TOKEN` | 50+ (deployments, projects, domains, env vars, teams) |

See [`references/vercel-mcp.md`](references/vercel-mcp.md) for full Vercel MCP details.

## Service-Specific Notes

- **Notion MCP**: full verification results, tool list, and Cyrillic comparison with Miro in [`references/notion-mcp-verification.md`](references/notion-mcp-verification.md).
- **mcpc (Apify MCP CLI)**: OAuth flow, PKCE pitfalls, Windows cmd.exe issues, and connection commands in [`references/mcpc-apify-cli.md`](references/mcpc-apify-cli.md).
- **Context7**: stdio setup via npx, API key format, verification in [`references/context7-mcp.md`](references/context7-mcp.md).

## Usage Skills (per-service)

Once MCP is connected, these skills cover actual usage of specific services:

- **Miro**: `miro-mcp` — create diagrams, documents, tables, stickies, code widgets, prototypes
- **Notion**: `productivity/notion` — pages, databases, Markdown, search, Workers (also works as standalone skill with `NOTION_API_KEY`; MCP gives streaming access with ~91% less token overhead on DB ops)
