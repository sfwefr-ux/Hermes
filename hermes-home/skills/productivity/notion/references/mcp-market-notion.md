# MCP Market + Notion: подключение

## Как это работает

MCP Market предоставляет Notion MCP-сервер по тому же механизму, что и Miro:
- OAuth через Supabase (тот же `authorization_servers`)
- Один JWT-токен на все сервисы
- Каждый сервис — отдельный URL на `link.mcpmarket.com`

## Добавление в Hermes

```yaml
# config.yaml
mcp_servers:
  mcpmarket_notion:
    url: 'https://link.mcpmarket.com/sfwefr/notion/mcp'
    headers:
      Authorization: 'Bearer ${MCP_MCPMARKET_API_KEY}'
      Accept: 'application/json, text/event-stream'
    timeout: 120
    connect_timeout: 60
```

## Обязательные заголовки

| Заголовок | Значение | Зачем |
|-----------|----------|-------|
| `Authorization` | `Bearer <JWT>` | Supabase OAuth |
| `Accept` | `application/json, text/event-stream` | **Обязателен** — без него 406 |
| `Content-Type` | `application/json` | Для POST-запросов |

## Проверка работоспособности

```python
# Отправить initialize
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "hermes-agent", "version": "1.0.0"}
  }
}
# Ожидаемый ответ: serverInfo.name = "Notion MCP", version ~1.2.0
```

## Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| 406 Not Acceptable | Нет SSE в Accept | Добавить `text/event-stream` |
| 401 Unauthorized | Токен `sk_user_...` вместо JWT | Нужен Bearer JWT из Identity таба MCP Market |
| Инструменты не появляются | Нужен рестарт | `/restart` в чате Hermes |

## Отличия от прямого Notion API

| | MCP Market Notion | Прямой API |
|---|---|---|
| Ключ | JWT-токен MCP Market | `NOTION_API_KEY` (`ntn_` или `secret_`) |
| Настройка | config.yaml | .env |
| Инструменты | notion_search, notion_fetch... | curl/ntn |
| Кириллица | ✅ | ✅ |
| Markdown | Автоматически | Через `/markdown` endpoint |
