# Vercel MCP — Setup Notes

## Official Endpoint (OAuth-only — Hermes NOT supported)

- **URL:** `https://mcp.vercel.com`
- **Auth:** OAuth 2.0 with closed client whitelist
- **Approved clients:** Claude Code, Claude.ai, ChatGPT, Codex CLI, Cursor, VS Code Copilot, Devin, Raycast, Goose, Windsurf, Gemini
- **Hermes status:** NOT on the approved list — returns HTTP 401 even with valid `VERCEL_TOKEN` in `Authorization: Bearer` header
- **OAuth metadata:** `https://mcp.vercel.com/.well-known/oauth-protected-resource` → scopes: `openid`, `offline_access`, auth server: same endpoint

## Community Alternative: `@robinson_ai_systems/vercel-mcp`

- **Package:** `@robinson_ai_systems/vercel-mcp` v1.0.1
- **Type:** stdio (local process via npx)
- **Auth:** `VERCEL_TOKEN` environment variable (Vercel personal access token)
- **Tools:** 50+ — deployments, projects, domains, environment variables, teams, feature flags, webhooks
- **Token format:** starts with `vcp_`
- **Token source:** https://vercel.com/account/tokens

### Hermes config

```yaml
mcp_servers:
  vercel:
    type: stdio
    command: npx
    args: ['-y', '@robinson_ai_systems/vercel-mcp']
    env:
      VERCEL_TOKEN: '${VERCEL_TOKEN}'
```

### .env

```
VERCEL_TOKEN=vcp_...
```

### Verification

```python
import subprocess, json
init = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes-agent", "version": "1.0.0"}
    }
}) + '\n'
r = subprocess.run(
    ['npx', '-y', '@robinson_ai_systems/vercel-mcp'],
    input=init, capture_output=True, text=True, timeout=30,
    env={**os.environ, 'VERCEL_TOKEN': 'test'}
)
# Expect: {"result":{"serverInfo":{"name":"@robinsonai/vercel-mcp","version":"1.0.0"},...}}
```

### Apply

After adding to config, run `/reload-mcp` in chat (or `/restart` gateway / restart CLI).

## Vercel CLI (`vercel mcp` command)

The `vercel mcp` CLI command only configures **local clients** (Claude Code, Cursor, VS Code) — it does NOT deploy an MCP server. Not useful for Hermes integration.
