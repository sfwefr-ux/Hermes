# Cron + Notion DB → Telegram Reminders

Recurring pattern: create a cron job that queries a Notion database daily
and sends formatted reminders via Telegram.

## When to Use

- Daily schedule overviews (appointments, tasks, deadlines)
- Status-based reminders (find all "pending" items due tomorrow)
- Business operations: installation schedules, client follow-ups, shift plans

## Proven Setup

### 1. Notion Database Schema

Example — installation schedule:

```
CREATE TABLE ("Дата" DATE, "Время" RICH_TEXT, "Адрес" RICH_TEXT,
  "Имя клиента" TITLE, "Тип работ" SELECT(...), "Телефон" PHONE_NUMBER,
  "Статус" SELECT('Ожидает':yellow, 'Подтверждён':green, 'Выполнен':blue, 'Отменён':red))
```

Key columns: date field (for filtering tomorrow's items), status field (to find active records).

### 2. Cron Job

```python
cronjob(
    action='create',
    name='Evening reminder — tomorrow appointments',
    schedule='0 23 * * *',  # 11 PM daily
    prompt='''Query Notion DB (data source: collection://xxx).
Find all rows with status "Подтверждён" AND date = TOMORROW.
Format as Telegram message:
  🔔 Монтажи на завтра — {date}
  • {time} — {address}, {client}, {work_type}, tel: {phone}
If none: "Завтра монтажей нет. Можно отдыхать! 🏠"
Send as final response (auto-delivers to Telegram).''',
    deliver='origin'  # Delivers to the same Telegram chat
)
```

### 3. End-User Flow

1. User dictates new appointment → assistant adds to Notion DB with status "Подтверждён"
2. Every night at 23:00 → cron fires, queries Notion, formats summary
3. Summary auto-delivers to Telegram
4. User sees tomorrow's schedule without opening any app

### Pitfalls

- **Date math**: cron prompt must use relative language ("TOMORROW" / "завтра") — the agent running the cron will compute it at execution time
- **Time zones**: cron fires in server local time (UTC+3 for Moscow). Explicitly mention timezone in prompt if critical
- **Empty results**: always handle the "no appointments" case with a friendly message — silence is ambiguous
- **Token efficiency**: keep the prompt concise. The cron agent fetches all pages from Notion DB — large DBs may need pagination/filtering hints in the prompt

### Verified With

- Notion MCP v1.2.0 (via MCP Market)
- Hermes cron scheduler
- Telegram delivery
- June 2026
