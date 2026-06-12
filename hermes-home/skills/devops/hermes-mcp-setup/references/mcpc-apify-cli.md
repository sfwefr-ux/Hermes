# mcpc — Apify MCP CLI Client

`mcpc` (`@apify/mcpc`) — универсальный CLI-клиент для работы с MCP-серверами.
Установка: `npm install -g @apify/mcpc` (требует Node.js ≥ 20).

## Основные команды

```
mcpc connect <server> @session [--header "..."]  # Подключиться к MCP-серверу
mcpc @session tools-list          # Список инструментов
mcpc @session tools-call <name> [args]  # Вызвать инструмент
mcpc login <server>               # OAuth-авторизация (редко нужна)
mcpc --json @session ...          # JSON-вывод для скриптов
```

## Аутентификация

### PRIMARY: API-токен (Bearer)

**Apify MCP принимает API-токены напрямую** — OAuth не требуется.
Токен получается на https://console.apify.com/account/integrations.

```bash
mcpc connect https://mcp.apify.com @apify --header "Authorization: Bearer <API_TOKEN>"
```

Это самый простой и надёжный способ. Именно так подключается CloudCode.

### Почему не OAuth (если предложат)

Apify MCP **не требует** OAuth/PKCE. Сервер принимает простой Bearer-токен.
Ошибка 401 в логах содержит прямую инструкцию:
> *«Pass an Apify API token in the Authorization: Bearer *** header.
> Manage tokens at https://console.apify.com/account/integrations»*

**Всегда читай ошибку 401 до конца** — она говорит, какой метод аутентификации нужен.

### OAuth (запасной путь, если токен недоступен)

`mcpc login https://mcp.apify.com` запускает PKCE-флоу:

- Каждый вызов генерирует НОВЫЙ `code_challenge` — код из предыдущего URL невалиден
- Нужен живой процесс (локальный HTTP-сервер на 127.0.0.1)
- Windows cmd.exe ломает URL авторизации через `start` → `Schema validation failed`
- Решение: PowerShell вместо cmd, или ручная вставка URL в браузер

## Диагностика

Логи бриджа:
```
~/.mcpc/logs/bridge-@<session>.log
```

Конфигурация сессий и профилей:
```
~/.mcpc/sessions.json
~/.mcpc/profiles.json
```

Именно из логов видна реальная причина отказа — сервер сам пишет, что ему нужно.
