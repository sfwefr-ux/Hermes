# Vercel MCP — установка и подключение

## Official vs Community

### Official (https://mcp.vercel.com) — НЕ работает с Hermes
- Remote HTTP MCP, OAuth 2.0 (Supabase), endpoint `https://mcp.vercel.com`
- Принимает ТОЛЬКО одобренных клиентов: Claude Code, Cursor, VS Code Copilot, ChatGPT, Codex CLI, Devin, Gemini
- Hermes в списке нет → всегда 401 даже с правильным Bearer токеном
- Прямой Vercel API токен тоже не принимает — только OAuth JWT от зарегистрированного клиента
- Заносить в config.yaml бессмысленно — сервер будет висеть offline

### Community: @robinson_ai_systems/vercel-mcp ✅ РАБОТАЕТ
- npm: `@robinson_ai_systems/vercel-mcp` v1.0.1
- 50+ инструментов: деплои, домены, env vars, проекты, команды, логи, firewall, KV, Blob, Postgres
- Тип: **stdio** (npx)
- Auth: `VERCEL_TOKEN` в env

## Установка

### 1. Получить токен
https://vercel.com/account/tokens → создать с нужными правами

### 2. Добавить в .env
```
VERCEL_TOKEN=vcp_...
```

### 3. config.yaml
```yaml
mcp_servers:
  vercel:
    type: stdio
    command: npx
    args:
      - "-y"
      - "@robinson_ai_systems/vercel-mcp"
    env:
      VERCEL_TOKEN: "${VERCEL_TOKEN}"
```

### 4. Проверка (Python)
```python
import subprocess, json, os

init = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "hermes-agent", "version": "1.0.0"}
    }
}) + "\n"

r = subprocess.run(
    [r"C:\Program Files\nodejs\npx.CMD", "-y", "@robinson_ai_systems/vercel-mcp"],
    input=init, capture_output=True, text=True, timeout=30,
    env={**os.environ, "VERCEL_TOKEN": os.environ.get("VERCEL_TOKEN", "")}
)
print(r.stdout[:500])
# Ожидаем: {"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"@robinsonai/vercel-mcp",...}}}
```

## Pitfalls

- **npx с --help на Windows зависает** — не запускай `npx -y pkg --help` в subprocess с timeout < 30s, будет TimeoutExpired. Для проверки пакета — отправляй JSON-RPC initialize.
- **npm.CMD** — npm доступен как `C:\Program Files\nodejs\npm.CMD`, не как `npm` в subprocess без правильного PATH.
- **npx.CMD** — аналогично: `C:\Program Files\nodejs\npx.CMD`.
- **OAuth metadata URL** официального сервера: `https://mcp.vercel.com/.well-known/oauth-protected-resource` — authorization_servers указывает на сам mcp.vercel.com, fetch дает 401. Это тупик.

## OAuth-auth официального сервера — всё что не работает
(чтобы не повторять попытки)
- `Authorization: Bearer <vercel_api_token>` → 401
- `Bearer dummy_*` → 401 (тот же ответ, что без токена)
- WWW-Authenticate в ответе 401: `Bearer error="invalid_token", error_description="No authorization provided", resource_metadata="https://mcp.vercel.com/.well-known/oauth-protected-resource"`
- Scopes: openid, offline_access
- Hermes не в списке approved clients → OAuth flow не завершить

## Инструменты (основные категории)
Billing, Deployments, DNS, Domains, Edge Config, Environment Variables, Firewall, Function Metrics, Git, KV Storage, Blob Storage, Postgres, Projects, Secrets, Teams, Webhooks
