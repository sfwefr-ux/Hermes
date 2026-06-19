# Сжатие изображений и видео для веб-деплоя

Используется при подготовке лендингов и сайтов с медиа на Vercel (лимит ~100 МБ на деплой).

## Видео: ffmpeg

```bash
ffmpeg -y -i input.mp4 \
  -c:v libx264 -crf 28 -preset fast \
  -vf "scale=720:-2" \
  -c:a aac -b:a 64k \
  -movflags +faststart \
  output.mp4
```

- `crf 28` — агрессивное, но приемлемое качество для веба (23 — качество по умолчанию)
- `scale=720:-2` — ширина 720px, высота авто (сохраняет пропорции)
- `-movflags +faststart` — для стриминга (браузер начинает играть до полной загрузки)

Степень сжатия: обычно 25→4 МБ.

## Изображения: PIL (PNG → JPG)

```python
from PIL import Image
import os

for f in os.listdir('images/'):
    if f.lower().endswith('.png'):
        img = Image.open(f'images/{f}')
        # RGBA → RGB с кремовым фоном
        if img.mode in ('RGBA', 'P'):
            rgb = Image.new('RGB', img.size, (245,237,224))
            rgb.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb
        # Макс. ширина 1200px
        if img.width > 1200:
            ratio = 1200 / img.width
            img = img.resize((1200, int(img.height * ratio)), Image.LANCZOS)
        jpg_name = f.rsplit('.',1)[0] + '.jpg'
        img.save(f'images/{jpg_name}', 'JPEG', quality=80, optimize=True)
        os.remove(f'images/{f}')
```

Степень сжатия: 70 МБ → 7 МБ для пачки рендеров.

## HTML: замена расширений

После конвертации — patch с replace_all:
```
patch(path='index.html', old_string='.png', new_string='.jpg', replace_all=true)
```

## Vercel: деплой статики

```bash
vercel --prod --yes --token "$VERCEL_TOKEN" --scope sfwefr-ux
```

Токен брать из `<HERMES_HOME>/.env` (строка `VERCEL_TOKEN=`).
