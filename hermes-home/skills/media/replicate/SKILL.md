---
name: replicate
description: "Генерация картинок и видео, включая img2img (изменение фото пользователя). Основной путь — встроенные инструменты Hermes (image_generate text-to-image, video_generate через FAL) + прямой img2img через fal_client. Replicate — запасной канал (cheap/premium)."
version: 3.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [replicate, image, video, generation, cheap, premium, flux, imagen, veo, wan, fal, pixverse]
    related_skills: []
---

# Генерация картинок и видео

**ПОРЯДОК ДЕЙСТВИЙ: сначала встроенные инструменты Hermes, потом Replicate.**

## 🔒 Правило: всегда спрашивай уровень

## ⚠️ Pitfall: «помести мою мебель в интерьер»

Когда пользователь присылает ФОТО своей мебели и просит «добавить скандинавский интерьер»
или «сделай красиво», НЕЛЬЗЯ выдумывать мебель. Нельзя генерировать «похожую» — пользователь
видит подмену мгновенно и злится.

**Правильный порядок:**
1. `vision_analyze` — получить ТОЧНОЕ описание мебели (форма, цвет, детали, фурнитура, пропорции, количество отделений)
2. Если vision недоступен — использовать описание из авторазметки фото (система даёт его)
3. Промпт должен начинаться с ДОСЛОВНОГО описания мебели, и только потом — интерьер
4. Мебель в промпте = та же конструкция, тот же цвет, те же ручки/ножки/крепления
5. Интерьер описывать отдельным абзацем: пол, стены, свет, декор

**Формат промпта:**
```
[ТОЧНОЕ описание мебели из vision/разметки].
The exact same [предмет] placed in [описание интерьера].
```

Нельзя: «a tall shelving unit» вместо «a low two-compartment bench with notched feet».
Пользователь прислал комод с двумя отделениями — в генерации должно быть два отделения.
Пользователь прислал тёмное дерево — в генерации тёмное дерево.

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

### Image-to-image (img2img) — когда пользователь прислал фото

**`image_generate` НЕ ПРИНИМАЕТ входное изображение.** Это text-to-image.
Если пользователь присылает фото и просит «измени фон / добавь интерьер / сделай красиво» —
НЕ генерируй заново. Пользователь заметит подмену мебели мгновенно и взбесится.

**⚠️ Pitfall: композит (вырезать мебель и вставить в другой фон)**
НЕ ДЕЛАЙ. Разное освещение, перспектива, тени — выглядит ужасно, пользователь бесится.
Единственный рабочий путь — img2img с НИЗКИМ strength на ОРИГИНАЛЬНОМ фото пользователя.

**⚠️ Pitfall: референсное фото не трогай**
Если пользователь присылает два фото — своё И референс интерьера — НЕ делай img2img на референсе.
Начинай с ФОТО ПОЛЬЗОВАТЕЛЯ как базы. Промпт описывай интерьер с референса.
Референс — только для вдохновения, не для редактирования.

**Порядок img2img через FAL (основной путь, раз ключ есть в `.env`):**

1. Определи путь к фото (из сообщения или `image_cache`)
2. Прочитай FAL_KEY из `.env` (формат `id:secret`)
3. Разбей на FAL_KEY_ID / FAL_KEY_SECRET, установи в env
4. Установи `pip install fal-client -q` если нет
5. Вызови `fal_client.subscribe('fal-ai/flux/dev/image-to-image', ...)`

```python
import base64, os, fal_client

# Ключ из .env
with open(r'C:\Users\1\AppData\Local\hermes\.env') as f:
    for line in f:
        if line.startswith('FAL_KEY='):
            key = line.split('=',1)[1].strip()
            break
parts = key.split(':', 1)
os.environ['FAL_KEY_ID'] = parts[0]
os.environ['FAL_KEY_SECRET'] = parts[1]

# Чтение фото
with open(img_path, 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Генерация
result = fal_client.subscribe(
    'fal-ai/flux/dev/image-to-image',
    arguments={
        'image_url': f'data:image/jpeg;base64,{img_b64}',
        'prompt': '...',
        'strength': 0.40,
        'num_inference_steps': 28,
        'guidance_scale': 3.5
    }
)
print(result['images'][0]['url'])
```

Параметры:
- `strength`: **0.30–0.55** для img2img. Выше 0.55 — меняет сам объект (мебель), пользователь бесится. 0.35–0.45 — интерьер меняется, мебель сохраняется. Для «сохрани сцену но поменяй предмет» — 0.20–0.30
- `num_inference_steps`: 28 достаточно для качества
- Промпт: на английском, детальный. НАЧИНАЙ с точного описания предмета с фото, потом интерьер

**Если FAL_KEY не в `.env` или не в формате id:secret** — fallback на Replicate через curl (см. `references/fal-img2img.md`).

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
2. **Пользователь прислал фото?** → img2img через `fal-ai/flux/dev/image-to-image` (см. раздел выше). База — фото пользователя, strength 0.35–0.45
3. **Text-to-image без фото** → `image_generate` / `video_generate` (FAL, встроенные)
4. **Если FAL не сработал** → Replicate-скрипт
5. Если Replicate 402 → сказать пользователю про отсутствие кредитов
