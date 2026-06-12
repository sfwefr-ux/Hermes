---
name: firecrawl
description: "Web scraping and content extraction via Firecrawl API. Converts any website to clean markdown."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [firecrawl, scraping, parser, markdown, web]
---

# Firecrawl — Парсинг сайтов

Парсинг любых сайтов в чистый markdown через Firecrawl API. Удобно для анализа сайтов конкурентов, сбора цен, мониторинга изменений.

## Когда применять

- Спарсить сайт конкурента и сравнить с BadLock
- Извлечь цены, услуги, контакты с любого сайта
- Собрать контент для анализа (отзывы, статьи, каталоги)
- Когда curl/web_fetch недостаточно (JS-рендеринг, сложная структура)

## Ключ

В `.env`: `FIRECRAWL_API_KEY` (35 символов, формат `fc-` + hex).

## Эндпоинт

```
POST https://api.firecrawl.dev/v1/scrape
Authorization: Bearer $FIRECR...ype: application/json

{
  "url": "https://target-site.ru",
  "formats": ["markdown"]
}
```

Ответ:
```json
{
  "success": true,
  "data": {
    "markdown": "# Заголовок\n\nКонтент...",
    "metadata": {
      "title": "Заголовок страницы",
      "description": "...",
      "language": "ru"
    }
  }
}
```

## Python usage

```python
import urllib.request, json

# Read key from .env
env_path = r"C:\Users\1\AppData\Local\hermes\.env"
with open(env_path, 'r') as f:
    for line in f:
        if 'FIRECRAWL' in line:
            api_key = line.strip().split('=', 1)[1]
            break

data = json.dumps({
    "url": "https://target-site.ru",
    "formats": ["markdown"]
}).encode()

req = urllib.request.Request(
    "https://api.firecrawl.dev/v1/scrape",
    data=data,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req, timeout=60) as resp:
    body = json.loads(resp.read())
    if body['success']:
        print(body['data']['markdown'])
```

## Pitfalls

- **401 Unauthorized** — ключ неверный или обрезан при записи в .env (частая проблема с execute_code, см. `perplexity-search` skill)
- Формат ключа: `fc-` + 32 hex символа. Если длина не 35 — ключ повреждён
- Таймаут: 60 секунд (страницы грузятся дольше простых API)
- Не все сайты отдают контент — некоторые блокируют ботов

## Связанные навыки

- `perplexity-search` — AI-поиск для общего анализа (альтернатива ручному парсингу)
- `yandex-competitor-analysis` — браузерный анализ конкурентов на Яндекс Картах
