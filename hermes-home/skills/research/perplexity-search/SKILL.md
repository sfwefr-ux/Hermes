---
name: perplexity-search
description: "Perplexity AI-powered search for market research, competitor analysis, and web lookups. HTTP API via curl or Python urllib. Логирует стоимость каждого запроса."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [perplexity, search, research, api, market-analysis]
---

# Perplexity Search

AI-поиск через Perplexity API. Для исследования рынка, анализа конкурентов, поиска цен, отзывов и трендов. Русский язык поддерживается.

## ⚠️ Основной способ вызова: `pplx_search.py` (логирует стоимость)

**Всегда вызывай скилл через `pplx_search.py`** — он сам считает стоимость по тарифу, дописывает её в CSV-реестр с накопительным итогом и печатает траты в stderr. Ручные curl/urllib (ниже) оставлены как справка; при них расход НЕ логируется.

```bash
# поиск (по умолчанию): $0.005 за запрос
python skills/research/perplexity-search/pplx_search.py "установка электронных замков СПб" --max-results 5

# чат с AI-анализом: request fee + токены
python skills/research/perplexity-search/pplx_search.py "сравни цены X и Y" --mode chat --model sonar --max-tokens 500
```

Или из Python:

```python
import sys; sys.path.insert(0, r"C:\Users\1\AppData\Local\hermes\skills\research\perplexity-search")
import pplx_search
res = pplx_search.search("запрос", max_results=5)   # стоимость залогирована автоматически
```

После каждого вызова в stderr появляется строка вида:
`[COST] Perplexity /search: $0.0050 (этот запрос) | итого Hermes/Perplexity: $1.2340`

## Тарифы (docs.perplexity.ai, сверено 2026-06-11)

| Эндпоинт | Стоимость |
|----------|-----------|
| `/search` | **$5.00 / 1000 запросов = $0.005 за запрос** (токены не тарифицируются) |
| `/chat sonar` (low/med/high context) | request fee $5 / $8 / $12 за 1000 + $1/1M вход + $1/1M выход |
| `/chat sonar-pro` | request fee $6 / $10 / $14 за 1000 + $3/1M вход + $15/1M выход |
| `/chat sonar-reasoning-pro` | request fee $6 / $10 / $14 за 1000 + $2/1M вход + $8/1M выход |

## Реестр расходов

CSV: `%LOCALAPPDATA%\hermes\costs\perplexity_costs.csv` (колонки: timestamp, endpoint, model, units, cost_usd, running_total_usd). Путь переопределяется переменной `HERMES_COST_LEDGER`. Это источник истины по тратам на Perplexity — реальные счета приходят на стороне Hermes, а не Claude Code.

## Когда применять

- Поиск конкурентов, цен, рыночной информации (альтернатива/дополнение к `yandex-competitor-analysis`)
- Анализ трендов, новостей, технологий
- Любой поисковый запрос, где нужен AI-анализ результатов (а не просто список ссылок)
- Когда curl/web_fetch недостаточно — Perplexity сам читает страницы и синтезирует ответ

## Ключ

Ключ в `.env`: `PERPLEXITY_API_KEY`. Загружать в рантайме через чтение файла.

## Эндпоинты

### `/search` — поиск (проверен, работает)

```
POST https://api.perplexity.ai/search
Authorization: Bearer $PERPLEXITY_API_KEY
Content-Type: application/json

{
  "query": "установка электронных замков Санкт-Петербург",
  "max_results": 5,
  "max_tokens_per_page": 256
}
```

Возвращает массив `results[]`, каждый с полями:
- `title` — заголовок источника
- `url` — ссылка на источник
- `snippet` — фрагмент текста с ответом
- `date` / `last_updated` — даты

### `/chat/completions` — чат с AI-анализом (не проверен)

```
POST https://api.perplexity.ai/chat/completions
Authorization: Bearer $PERPLEXITY_API_KEY
Content-Type: application/json

{
  "model": "sonar",
  "messages": [{"role": "user", "content": "..."}],
  "max_tokens": 500
}
```

Модели: `sonar` (быстрый), `sonar-pro` (глубокий), `sonar-reasoning` (рассуждения).
Для `sonar` — `max_tokens` минимум 16.

## Использование в Python

### Чтение ключа из .env

```python
env_path = r"C:\Users\1\AppData\Local\hermes\.env"
with open(env_path, 'r') as f:
    for line in f:
        if 'PERPLEXITY' in line:
            api_key = line.strip().split('=', 1)[1]
            break
```

### Поиск

```python
import urllib.request, json

data = json.dumps({
    "query": "запрос",
    "max_results": 5,
    "max_tokens_per_page": 200
}).encode()

req = urllib.request.Request(
    "https://api.perplexity.ai/search",
    data=data,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(req, timeout=30) as resp:
    body = json.loads(resp.read())
    for r in body['results']:
        print(r['title'], r['url'])
```

## Важный pitfall: execute_code и API-ключи

**execute_code сжимает строки, содержащие hex-паттерны (API-ключи, токены) в `...`**, что ломает f-строки и `.replace()`.

❌ НЕ работает:
```python
key = "pplx-aBcDeFgHiJkLmNoPqRsTuVwXyZ1234"  # сожмётся в pplx-...234
print(f"Bearer {key}")  # SyntaxError
```

✅ Работает:
```python
# Способ 1: читать из .env (рекомендуется)
with open(env_path) as f:
    for line in f:
        if 'PERPLEXITY' in line:
            key = line.strip().split('=', 1)[1]

# Способ 2: собирать из частей
prefix = "pplx-"
suffix = "aBcDeFgHiJkLmNoPqRsTuVwXyZ1234"
key = prefix + suffix

# Способ 3: без f-строк с ключом
headers = {"Authorization": "Bearer " + key}
```

Это относится ко ВСЕМ API-ключам, не только Perplexity.

## Связанные навыки

- `yandex-competitor-analysis` — браузерный анализ конкурентов на Яндекс Картах (дополняет Perplexity)
- `firecrawl` — парсинг конкретных сайтов (когда Perplexity недостаточно)
