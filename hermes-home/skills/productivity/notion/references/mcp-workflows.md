# MCP Notion: рабочие паттерны

Быстрые шаблоны для типовых операций через Notion MCP.

## Создание базы данных (DDL)

Самый быстрый способ — SQL DDL через `notion_create_database`:

```
CREATE TABLE (
  "Название" TITLE,
  "Тип" SELECT('Вариант1':red, 'Вариант2':green),
  "Сумма" NUMBER,
  "Дата" DATE,
  "Комментарий" RICH_TEXT
)
```

Цвета: `default, gray, brown, orange, yellow, green, blue, purple, pink, red`.

Создаётся без parent — на уровне workspace. Потом базу можно перенести вручную.

## Добавление опций в SELECT

Использовать `notion_update_data_source` с полным списком опций (нельзя добавить одну — нужно перечислить все):

```
ADD COLUMN "Категория" SELECT('Старая':gray, 'Новая':pink, ...)
```

⚠️ **Важно:** в statements нужно перечислить ВСЕ существующие опции + новую. `ALTER COLUMN ... SET` не добавляет опции к существующему списку — он заменяет весь список.

## Создание записей

Через `notion_create_pages` с parent `data_source_id`:

```json
{
  "parent": {"data_source_id": "uuid"},
  "pages": [{
    "properties": {
      "Название": "Заголовок",
      "Тип": "Расход",
      "Сумма": 5000,
      "Категория": "Материалы",
      "date:Дата:start": "2026-06-10",
      "date:Дата:is_datetime": 0,
      "Комментарий": "Детали покупки"
    }
  }]
}
```

Особенности:
- Дата: обязательно разворачивать в `date:ИмяПоля:start` и `date:ИмяПоля:is_datetime`
- `is_datetime: 0` — просто дата, `is_datetime: 1` — дата+время
- Числа: передавать как number, не строку
- SELECT: точное совпадение с именем опции (чувствительно к регистру)

## Ежемесячная аналитика через cron

Паттерн: cron-задача 1-го числа + навык `notion`:

```
schedule: "0 9 1 * *"  # 9 утра, 1-е число каждого месяца
skills: ["notion"]
```

В prompt указать:
1. data_source_id базы
2. Формулы расчёта (сумма доходов, сумма расходов, прибыль)
3. Формат вывода

## Поиск записей по фильтру

```json
{
  "query": "запрос",
  "data_source_url": "collection://uuid",
  "filters": {
    "created_date_range": {
      "start_date": "2026-06-01",
      "end_date": "2026-06-30"
    }
  }
}
```

## Обновление страниц: команды и pitfalls

`notion_update_page` — 6 команд, каждая со своим синтаксисом:

| Команда | Что делает | Ключевое поле |
|---------|-----------|---------------|
| `update_properties` | Меняет свойства страницы | `properties` |
| `update_content` | Find-and-replace в теле | `content_updates` (массив `{old_str, new_str}`) |
| `replace_content` | Полная замена тела | `new_str` |
| `insert_content` | Добавить в конец/начало | `content` + опционально `position` |
| `apply_template` | Применить шаблон | `template_id` |
| `update_verification` | Верификация (Enterprise) | `verification_status` |

⚠️ **Pitfalls:**

1. **`command` обязателен** — без него ошибка `"Invalid option: expected one of..."`. Легко забыть при вызове.

2. **`insert_content` vs `update_content`:**
   - `insert_content` — добавить в конец (по умолчанию) или начало (`position: {"type": "start"}`). Не требует знать текущее содержимое.
   - `update_content` — найти `old_str` и заменить на `new_str`. Требует точного совпадения текста. Лучше сначала `notion_fetch` для получения актуального текста.

3. **`update_content` принимает `content_updates`** — массив объектов `{old_str, new_str}`, а не просто `content` и `old_str`/`new_str` на верхнем уровне.

4. **`page_id`** — всегда обязателен (UUID страницы, не базы данных).

5. **Массовая загрузка контента:** для добавления большого объёма структурированного текста используй повторные вызовы `insert_content` с `position: {"type": "end"}` — каждый новый блок добавляется в конец страницы.
