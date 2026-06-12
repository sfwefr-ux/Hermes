---
name: replicate
description: "Генерация картинок и видео. Основной путь — встроенные инструменты Hermes (image_generate, video_generate через FAL). Replicate — запасной канал (cheap/premium), если FAL недоступен или пользователь явно просит Replicate."
version: 3.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [replicate, image, video, generation, cheap, premium, flux, imagen, veo, wan, fal, pixverse]
    related_skills: []
---

# Генерация картинок и видео

**ПОРЯДОК ДЕЙСТВИЙ: сначала встроенные инструменты Hermes, потом Replicate.**

## 🔒 Правило: всегда спрашивай уровень

Перед любой генерацией картинки/видео **спроси у пользователя — cheap или premium**, если он
не указал это сам. Если в запросе уже есть «недорого/повседневка/для рекламы» (cheap) или
«премиум/топ/Veo» (premium) — не переспрашивай, делай сразу.

---

## Путь 1: Встроенные инструменты Hermes (ОСНОВНОЙ)

Работают через FAL (ключ `FAL_KEY` в `.env`). Не требуют Replicate-кредитов.

### Картинка: `image_generate`
```
image_generate(prompt="...", aspect_ratio="landscape|square|portrait")
```
Цена: ~$0.01 (FAL).

### Видео: `video_generate`
Поддерживает **text-to-video** и **image-to-video** (передать `image_url`).
```
video_generate(prompt="...", image_url="https://...", duration=5, aspect_ratio="16:9")
```
Модель: pixverse-v6 (FAL). Цена: ~$0.03 за ролик.

### Image-to-video (оживление картинки)
1. Сгенерировать картинку через `image_generate` или взять готовый URL
2. Передать URL в `video_generate` с промптом, описывающим движение
3. Результат — MP4, отдаётся через markdown `![alt](url)`

### Если FAL не сработал
Переходить к **Пути 2 (Replicate)**.

---

## Путь 2: Replicate (ЗАПАСНОЙ)

Используется когда:
- FAL вернул ошибку
- Пользователь явно сказал «через Replicate»
- Нужны специфичные модели (imagen-4-ultra, veo-3.1)

Требует `REPLICATE_API_TOKEN` в `.env` и **кредиты на счету** (https://replicate.com/account/billing).

⚠️ **Проверка кредитов**: при 402 ошибке — сообщить пользователю, что нужен баланс. Не пытаться повторно.

### Модели по уровням

| Тип | cheap (повседневный) | premium (лучшее) |
|-----|----------------------|------------------|
| Картинка | `black-forest-labs/flux-schnell` (~$0.003/шт) | `google/imagen-4-ultra` (~$0.06/шт) |
| Видео | `wan-video/wan-2.2-t2v-fast` (~$0.05/ролик) | `google/veo-3.1` со звуком (~$6/ролик) |

Любую можно переопределить флагом `--model owner/name`.

### Уровни по словам пользователя

- **«недорого / дешёвый сервис / обычная картинка / для повседневки / для рекламной кампании»**
  → cheap (по умолчанию). Повседневные модели, копейки за штуку.
- **«премиум / премиум-качество / премиум-видео / топ-качество / лучшее / фотореализм / Veo»**
  → premium. Флагманские модели, дороже — предупреди о цене (особенно видео).

### ⚠️ Стоимость Replicate

- cheap-картинка — копейки (~$0.003), cheap-видео — недорого (~$0.05). Подходит для потока/рекламы.
- premium-видео (veo-3.1) — **ДОРОГО (~$6 за ролик ~8с)**: запускай ТОЛЬКО по явному запросу и
  СНАЧАЛА предупреди о цене.
- Каждый вызов пишет оценку в `<HERMES_HOME>/spend-log.md`.

### Как вызывать Replicate

Скрипт: `python skills/media/replicate/replicate_gen.py`

Повседневная картинка (cheap по умолчанию):
```bash
python skills/media/replicate/replicate_gen.py --type image \
  --prompt "баннер для акции, кофе и пончики, яркие цвета" --aspect 16:9
```

Премиум-картинка:
```bash
python skills/media/replicate/replicate_gen.py --type image --tier premium \
  --prompt "фотореалистичный портрет, студийный свет" --aspect 1:1
```

Повседневное видео (cheap):
```bash
python skills/media/replicate/replicate_gen.py --type video \
  --prompt "короткий ролик: логотип вылетает из дыма" --aspect 16:9
```

Премиум-видео (после предупреждения о цене):
```bash
python skills/media/replicate/replicate_gen.py --type video --tier premium \
  --prompt "кот-бариста готовит латте, киношный план" --resolution 1080p
```

Параметры: `--tier cheap|premium`, `--model owner/name`, `--aspect 16:9|1:1|9:16`,
`--resolution 480p|720p|1080p`, `--duration` (только veo), `--no-audio`, `--output-format jpg|png`, `--out-dir`.

### Что делает скрипт

1. Берёт `REPLICATE_API_TOKEN` из env или `<HERMES_HOME>/.env`.
2. Выбирает модель по `--tier` (или `--model`), создаёт prediction; для видео опрашивает до готовности.
3. Скачивает результат: картинки → `<HERMES_HOME>/image_cache`, видео → `<HERMES_HOME>/video_cache`.
4. Печатает локальный путь(и) в stdout; оценку стоимости пишет в `spend-log.md`.

---

## Резюме: порядок действий при запросе «сделай картинку/видео»

1. Спросить cheap/premium (если не указано)
2. **Сначала** `image_generate` / `video_generate` (FAL, встроенные)
3. **Если FAL не сработал** — Replicate-скрипт
4. Если Replicate 402 — сказать пользователю про отсутствие кредитов
