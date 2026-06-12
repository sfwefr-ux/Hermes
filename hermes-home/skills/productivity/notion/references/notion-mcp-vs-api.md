# Notion: MCP vs Direct API

**Дата:** Июнь 2026  
**MCP-сервер:** Notion MCP v1.2.0 (через MCP Market)  
**Прямой API:** Notion API 2025-09-03 (через `ntn` CLI или `curl`)

## Когда что использовать

| Сценарий | MCP | Прямой API |
|----------|-----|------------|
| Создание страниц с Markdown | ✅ `notion_create_pages` | ✅ `POST /v1/pages` + `markdown` |
| Чтение страниц | ✅ `notion_fetch` | ✅ `GET /v1/pages/{id}/markdown` |
| Создание баз данных | ✅ `notion_create_database` (SQL DDL) | ✅ `POST /v1/data_sources` (JSON) |
| Поиск | ✅ `notion_search` (semantic) | ✅ `POST /v1/search` |
| Работа с view | ✅ `notion_create_view` + DSL | ❌ Только UI |
| Комментарии | ✅ create/get | ❌ Нет в прямом API |
| Пользователи/команды | ✅ `notion_get_users`/`get_teams` | ❌ Нет в прямом API |
| Workers (sync/tools/webhooks) | ❌ | ✅ `ntn workers` |
| Файлы (upload) | ❌ | ✅ `ntn files create` / 3-step HTTP |
| Массовые DB-операции | ✅ ~91% токен-экономия | ⚠️ Полные JSON-ответы |
| Работа без .env | ✅ Токен MCP Market | ❌ Нужен `NOTION_API_KEY` |

## Формат Markdown

Оба способа используют **Notion-flavored Markdown** (XML-теги для callout, details, columns, table_of_contents, mentions).

Спецификация: `notion://docs/enhanced-markdown-spec` (ресурс MCP).

## Кириллица

Оба способа работают с кириллицей без проблем — в отличие от Miro DSL.

## MCP-инструменты (полный список)

`notion_search`, `notion_fetch`, `notion_create_pages`, `notion_update_page`, 
`notion_duplicate_page`, `notion_move_pages`, `notion_create_database`, 
`notion_update_data_source`, `notion_create_view`, `notion_update_view`,
`notion_get_comments`, `notion_create_comment`, `notion_get_users`, `notion_get_teams`

## Ресурсы MCP

- `notion://docs/enhanced-markdown-spec` — полная спека Markdown
- `notion://docs/view-dsl-spec` — DSL для настройки view (FILTER, SORT BY, GROUP BY, etc.)
