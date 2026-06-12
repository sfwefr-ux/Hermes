# Notion MCP via MCP Market — Verification Notes

**Date:** June 2026
**Server:** Notion MCP v1.2.0
**Endpoint:** `https://link.mcpmarket.com/{id}/notion/mcp`
**Auth:** Same Supabase Bearer JWT as Miro (cross-service token reuse confirmed)

## Connection

- Initial attempt with `Accept: application/json` → HTTP 406 "Not Acceptable: Client must accept both application/json and text/event-stream"
- Fixed by adding `Accept: application/json, text/event-stream` → HTTP 200
- Response is SSE (`text/event-stream`), must parse `data:` lines

## Tools (16 total)

| Tool | Purpose |
|------|---------|
| `notion_search` | Full workspace search |
| `notion_fetch` | Read pages, databases, data sources |
| `notion_create_pages` | Create pages (standalone + in databases) |
| `notion_update_page` | Edit properties + Markdown content |
| `notion_duplicate_page` | Clone pages |
| `notion_move_pages` | Move to different parent |
| `notion_create_database` | Create DBs with SQL DDL |
| `notion_update_data_source` | Modify DB schema |
| `notion_create_view` | Views: table, board, calendar, timeline, gallery, form, chart, map, dashboard |
| `notion_update_view` | Configure filters, sorts, grouping |
| `notion_get_comments` | Read comment threads |
| `notion_create_comment` | Add comments |
| `notion_get_users` | List workspace members |
| `notion_get_teams` | List teamspaces |

## Resources (2)

- `notion://docs/enhanced-markdown-spec` — Notion-flavored Markdown spec
- `notion://docs/view-dsl-spec` — View configuration DSL

## Cyrillic Support

**Notion MCP**: Cyrillic works perfectly in page content, titles, properties, callouts, tables — all block types. No encoding issues.

**Miro MCP**: Cyrillic in DSL (layout_read/layout_update) shows as `????` — encoding bug in Miro's DSL transport. Individual tool calls (diagram_create, doc_create, table_create) handle Cyrillic correctly. Avoid layout_read/layout_update for Cyrillic-heavy boards; use dedicated create tools instead.

## Test Page

Created comprehensive test page covering all block types: headings (H1-H3 with colors), formatting (bold, italic, strikethrough, underline, code), text/background colors, links, citations, toggles, lists (bulleted, numbered, nested), to-do items, quotes (single + multi-line), details/summary, callouts (with icons), tables, columns, code blocks (Python), Mermaid diagrams, table of contents, date mentions, cover image + icon. All rendered correctly.
