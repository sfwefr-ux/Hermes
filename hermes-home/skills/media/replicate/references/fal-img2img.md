# FAL Image-to-Image через fal_client

## Предпосылки

`image_generate` в Hermes не поддерживает img2img — это чисто text-to-image.
Когда пользователь присылает фото и хочет его модифицировать, нужен прямой вызов FAL API.

## Формат ключа в .env

FAL_KEY в `.env` имеет формат `key_id:key_secret`:
```
FAL_KEY=fff29a93-58b5-43da-b9a1-1d28a5d5d224:2dce0ea8a32c75700bd13c644bfdaf36
```

`fal_client` требует их раздельно: `FAL_KEY_ID` и `FAL_KEY_SECRET`.

## Рабочий код (проверено 19.06.2026)

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
        'prompt': 'detailed English prompt here',
        'strength': 0.40,
        'num_inference_steps': 28,
        'guidance_scale': 3.5
    }
)
# Результат: result['images'][0]['url']
```

## Параметры

| Параметр | Диапазон | Рекомендация |
|----------|----------|-------------|
| strength | 0.20–0.95 | 0.35–0.45: интерьер меняется, мебель сохраняется. Выше 0.55 — меняет саму мебель (пользователь бесится). 0.20–0.30: сцена почти не меняется |
| num_inference_steps | 20–50 | 28 — оптимально по скорость/качество |
| guidance_scale | 1.5–7 | 3.5 — стандарт для flux |

## Питы и антипаттерны

### ❌ Композит (birefnet + paste)
Вырезание мебели через birefnet и вставка в другой фон НЕ РАБОТАЕТ.
Освещение, перспектива, тени не совпадают — выглядит отвратительно.
Единственный путь — img2img.

### ❌ Img2img на референсном фото
Если пользователь прислал ДВА фото (свою мебель + референс интерьера) —
НЕ делай img2img на референсе. База — фото пользователя.
Референс используй только для описания интерьера в промпте.

### ❌ Выдумывание мебели
Если пользователь прислал фото мебели — промпт должен НАЧИНАТЬСЯ с точного описания этой мебели.
Не «a tall shelving unit» вместо «a low two-compartment bench with notched feet».
Пользователь видит подмену мгновенно.

### ✅ Правильный промпт
```
[ТОЧНОЕ описание мебели из vision/разметки].
The exact same [предмет] placed in [описание интерьера].
```

## Ошибки и решения

### `MissingCredentialsError`
Причина: `fal_client` не видит ключ.
Решение: разбить `FAL_KEY` на `FAL_KEY_ID` и `FAL_KEY_SECRET` и установить их в `os.environ`.

### `ModuleNotFoundError: No module named 'fal_client'`
Решение: `pip install fal-client -q` перед импортом.

### `Path /dev/inpainting not found` (404)
Модель `fal-ai/flux/dev/inpainting` не существует. Используй `fal-ai/flux/dev/image-to-image`
с низким strength вместо inpainting.

## Стоимость

~$0.01 за генерацию (FAL flux/dev), оценивается примерно.
birefnet (удаление фона) — бесплатно на FAL.
