---
name: miro-mcp
description: "Create and manage Miro boards via MCP Market — diagrams, documents, tables, stickies, shapes, code widgets, prototypes."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [miro, mcp-market, diagrams, whiteboard, visualization]
---

# Miro MCP — Working with Miro Boards via MCP Market

Use Miro MCP Market tools to create visual content on Miro boards directly from Hermes Agent.

## Prerequisites

Miro must be connected via MCP Market (see `hermes-mcp-setup` skill for auth setup). The Miro MCP tools are prefixed `mcp_mcpmarket_`.

## Tool Inventory

### Discovery & Reading

| Tool | Purpose |
|------|---------|
| `board_search_boards` | Find boards by name |
| `context_explore` | List high-level items on a board |
| `context_get` | Read content of a specific item |
| `layout_read` | Read board items as DSL |
| `board_list_items` | Paginated listing of board items |

### Creating Content (fire-and-forget)

| Tool | Creates |
|------|---------|
| `diagram_create` | Flowchart, UML class, UML sequence, ERD |
| `doc_create` | Markdown documents |
| `table_create` | Structured tables with text + select columns |
| `code_widget_create` | Syntax-highlighted code blocks |
| `layout_create` | Frames, stickies, shapes, text, cards |
| `prototype_create` | Interactive HTML prototypes |

### Editing Content

| Tool | Purpose |
|------|---------|
| `doc_update` | Find-and-replace in markdown docs |
| `doc_get` | Read raw markdown for precise editing |
| `table_sync_rows` | Insert/update table rows |
| `table_list_rows` | Read table rows with filtering |
| `layout_update` | Edit board items via DSL find-and-replace |
| `code_widget_update` | Update code widget content |

### Comments

| Tool | Purpose |
|------|---------|
| `comment_create` | Add canvas comment |
| `comment_list_comments` | Read comments |
| `comment_reply` | Reply to thread |
| `comment_resolve` | Resolve/unresolve thread |

## Proven Workflow

For a full-board demo, follow this sequence:

1. **Discover**: `board_search_boards` → find the target board
2. **Explore**: `context_explore` → see what's already there
3. **Diagram**: `diagram_get_dsl(type)` → get DSL spec, then `diagram_create`
4. **Document**: `doc_create` with markdown (Cyrillic works fine in creation)
5. **Table**: `table_create` with columns, then `table_sync_rows` to populate
6. **Decorations**: `layout_create` with stickies, shapes, text
7. **Code**: `code_widget_create` for syntax-highlighted examples
8. **Verify**: `context_explore` again → confirm everything is there

## DSL Systems (Two Different Ones!)

Miro has TWO separate DSL formats — don't mix them up:

### Diagram DSL (for `diagram_create`)

Format obtained via `diagram_get_dsl(diagram_type=...)`. Key rules:
- Starts with `graphdir TB|LR|BT|RL`
- Color palette: `palette #hex1 #hex2 #hex3`
- Nodes: `n<id> <label> <object_type> <color_index>`
  - Object types: `flowchart-process`, `flowchart-decision`, `flowchart-terminator`, `flowchart-data`
- Connectors: `c <source> <label> <target>` (use `-` for empty label)
- Clusters: `cluster <id> "<label>" <node1> <node2> ...` — MUST be at end of DSL
- Example in `references/diagram-dsl-example.md`

### Layout DSL (for `layout_create` / `layout_update`)

Format obtained via `layout_get_dsl`. Key rules:
- Each line: `id TYPE [parent=REF] key=value... "content"`
- Types: `FRAME`, `STICKY`, `SHAPE`, `TEXT`, `CARD` (single-line)
- Block types: `DOC`, `TABLE` (heredoc with `<<<` ... `>>>`)
- **Coordinate systems differ**:
  - Board-level items (no parent): center is (0,0), x/y = center of item
  - Frame children (parent=): x/y relative to frame TOP-LEFT corner, marks child CENTER
  - DOC/TABLE: x/y = TOP-LEFT corner (not center!) in all coordinate systems
- Content with HTML: use `<p>` tags for multi-paragraph, `<a href="...">` for links

## Язык контента — ВСЕГДА РУССКИЙ

Все названия, заголовки и тексты на досках Miro должны быть на русском языке. Пользователь явно этого требует.

## ⚠️ Cyrillic Encoding Pitfall (CRITICAL)

**When reading back DSL from boards containing Cyrillic text:**

- `layout_read` returns Cyrillic characters as `????` in the DSL output
- This makes `layout_update` with `old_string` **impossible to match** for any content containing Cyrillic
- `context_get` for docs and `context_explore` titles: same `????` issue for Cyrillic titles

**Workarounds:**

1. **Создание всегда работает**: Cyrillic в `doc_create`, `diagram_create`, `layout_create` (стикеры/фигуры), `table_create` — всё сохраняется корректно. Баг только на чтении.
2. **Удаление старых элементов**: вместо попыток `layout_update` с Cyrillic `old_string`, создавай новый контент поверх. Старые элементы можно «вытолкнуть» далеко за край доски, размещая новый контент в центре (x= -400..500, y=-200..700) — пользователь их просто не увидит при обычном просмотре.
3. **Обновление документов**: используй `doc_update` (find-and-replace), а не `layout_update`.
4. **Обновление таблиц**: используй `table_sync_rows`.

**Проверено — создание работает:** ✅ `doc_create` ✅ `diagram_create` ✅ `layout_create` ✅ `table_create` ✅ `code_widget_create`
**Сломано на чтении:** ❌ `layout_read` ❌ `layout_update` (с Cyrillic old_string)

## Table Operations

```python
# Create with columns (text + select types)
table_create(
    table_title="My Tracker",
    columns=[
        {"column_title": "Task", "column_type": "text"},
        {"column_title": "Status", "column_type": "select",
         "options": [
             {"displayValue": "To Do", "color": "#FF0000"},
             {"displayValue": "Done", "color": "#00FF00"}
         ]}
    ]
)

# Populate rows
table_sync_rows(rows=[
    {"cells": [
        {"columnTitle": "Task", "value": "Design API"},
        {"columnTitle": "Status", "value": "To Do"}
    ]}
])

# Read with filtering
table_list_rows(filter_by='{"Status": ["To Do", "In Progress"]}', limit=10)
```

## Code Widgets

```python
code_widget_create(
    code="# your code here",
    language="Python",  # JavaScript, TypeScript, C++, Java, Go, Rust, SQL, HTML, CSS, JSON, YAML, Mermaid...
    title="Example Widget",
    line_numbers_visible=True
)
```

## Sticky Note Colors

Valid: `gray`, `light_yellow`, `yellow`, `orange`, `light_green`, `green`, `dark_green`, `cyan`, `light_pink`, `pink`, `violet`, `red`, `light_blue`, `blue`, `dark_blue`, `black`

## Shape Types

Valid: `rectangle`, `round_rectangle`, `circle`, `triangle`, `rhombus`, `parallelogram`, `trapezoid`, `pentagon`, `hexagon`, `octagon`, `star`, `cross`, `cloud`, `can`, `left_arrow`, `right_arrow`, `left_right_arrow`, `left_brace`, `right_brace`, `wedge_round_rectangle_callout`, `flow_chart_predefined_process`
