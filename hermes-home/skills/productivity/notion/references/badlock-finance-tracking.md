# BadLock — Finance Tracking Pattern

Pattern for small service business: track expenses and income via Notion database, with voice-based entry via Telegram assistant.

## Database: Финансы BadLock

URL: https://app.notion.com/p/9223f4719d97476ab8b8f2b578a4061d
Data source: `collection://adf0add2-8621-4627-b9e0-1ccff18ceae1`

### Schema

| Field | Type | Values |
|-------|------|--------|
| Название | TITLE | Short description |
| Тип | SELECT | Расход (red), Доход (green) |
| Сумма | NUMBER | In rubles |
| Категория | SELECT | Материалы, Инструмент, Транспорт, Реклама, Связь, Аренда, Личное, Установка замка, Вскрытие, СКУД, Видеонаблюдение, Домофон, Прочее |
| Дата | DATE | When the transaction happened |
| Комментарий | RICH_TEXT | Details |

### Cron: Monthly Analytics

Job ID: `db889a31a4f8`
Schedule: `0 9 1 * *` (1st of every month at 9am MSK)
Delivers summary: total income, total expenses, net profit, top categories.

### Voice Entry Workflow

User sends voice message → agent transcribes → creates Notion page with `notion_create_pages`.

Example entries:
- "Расход 3500, материалы, купил цилиндры" → Тип=Расход, Категория=Материалы, Сумма=3500
- "Заработал 18000, установка замка, Петроградская" → Тип=Доход, Категория=Установка замка, Сумма=18000
- "Расход 12300, личное, запчасти на авто" → Тип=Расход, Категория=Личное, Сумма=12300

## Knowledge Base: Objection Handling

URL: https://app.notion.com/p/37a87c762cb081c6abb7f784dad6e787

12 objection types × 50 responses each = 600 scripts, adapted for locks/security systems business. Stored under `## 🗣️ Работа с возражениями`.
