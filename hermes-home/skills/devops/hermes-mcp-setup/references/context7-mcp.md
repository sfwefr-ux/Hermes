# Context7 MCP Server

Context7 provides up-to-date library documentation and code examples for AI agents. MCP server: `@upstash/context7-mcp` v3.1.0.

## Setup

Stdio transport via npx:

```yaml
mcp_servers:
  context7:
    type: stdio
    command: npx
    args:
      - "-y"
      - "@upstash/context7-mcp"
      - "--api-key"
      - "ctx7sk-..."
```

API key from: https://context7.com/dashboard

## Verification

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
    ['npx', '-y', '@upstash/context7-mcp', '--api-key', 'ctx7sk-...'],
    input=init, capture_output=True, text=True, shell=True, timeout=15
)
# Expects: {"result":{"serverInfo":{"name":"Context7","version":"3.1.0",...}}}
```

## Capabilities

- Tools: library documentation lookup, code examples
- Server describes itself as: "Use this server to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI..."
