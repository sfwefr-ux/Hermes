# Деплой лендинга на Vercel

## Порядок действий

1. Создать HTML/CSS лендинг локально (например `C:\Users\1\badlock-landing\index.html`)
2. Создать репозиторий на GitHub через API:

```python
import json, urllib.request
token = ...  # GITHUB_PERSONAL_ACCESS_TOKEN из .env
data = json.dumps({'name': 'badlock-landing', 'private': False, 'auto_init': False}).encode()
req = urllib.request.Request('https://api.github.com/user/repos', data=data, method='POST')
req.add_header('Authorization', f'Bearer {token}')
# ...
```

3. Закоммитить и запушить:

```bash
cd /c/Users/1/badlock-landing
git init && git add -A && git commit -m "Landing"
git push https://sfwefr-ux:${TOKEN}@github.com/sfwefr-ux/badlock-landing.git master
```

4. Залить через Vercel CLI (надёжнее, чем MCP API):

```bash
VERCEL_TOKEN=$(grep VERCEL_TOKEN /c/Users/1/AppData/Local/hermes/.env | cut -d= -f2)
cd /c/Users/1/badlock-landing
vercel --prod --yes --token "$VERCEL_TOKEN"
```

Результат: `https://<project-name>.vercel.app`

## Pitfalls

- **Vercel MCP `create_deployment`** требует gitSource с repoId — почти всегда падает 400/404. CLI надёжнее.
- **GitHub интеграция** — может не работать для новых репо без установки GitHub App. Но CLI деплоит напрямую, без Git-связки.
- **415 Unsupported Media Type** — Vercel v13 API не принимает raw-файлы, нужен CLI.
- **Телефон-заглушку** `+7 (999) 123-45-67` заменить на реальный перед деплоем.

## Текущие проекты на Vercel

- `fitfuel-app` — FitFuel PWA (Next.js, prod: fitfuel-app-kohl.vercel.app)
- `badlock-landing` — лендинг BadLock (статический HTML, prod: badlock-landing.vercel.app)
