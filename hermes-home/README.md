# Hermes — конфигурация и кастомизация

Снимок рабочей конфигурации Hermes Agent (каталог `HERMES_HOME`).
Версионируются только конфиг и кастомизация — **без секретов и runtime-данных**.

## Что в репозитории
- `config.yaml` — основной конфиг (модели, MCP-серверы, тулсеты). Секреты вынесены в `${ENV}`-ссылки.
- `SOUL.md` — системный промпт и правила оркестрации/маршрутизации.
- `skills/` — кастомные и установленные скиллы (в т.ч. `media/replicate`, `research/perplexity-search`).
- `cron/jobs.json` — расписания cron-задач.

## Чего здесь НЕТ (намеренно, см. `.gitignore`)
- `.env`, `auth.json` — все ключи и токены.
- `state.db`, `kanban.db` — состояние сессий/канбан.
- `logs/`, `*_cache/`, `sessions/`, `sandboxes/`, `memories/`, `mcp-servers/node_modules` — runtime/тяжёлое.

## Развёртывание из снимка
1. Скопировать содержимое в `HERMES_HOME` (`%LOCALAPPDATA%\hermes` на Windows).
2. Создать `.env` со своими ключами (см. `${...}`-ссылки в `config.yaml`):
   `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, `PERPLEXITY_API_KEY`, `FIRECRAWL_API_KEY`,
   `GITHUB_PERSONAL_ACCESS_TOKEN`, `GOOGLE_API_KEY`, `FAL_KEY`, `REPLICATE_API_TOKEN`,
   `MCP_MCPMARKET_API_KEY`, `CONTEXT7_API_KEY`, `TELEGRAM_BOT_TOKEN` и т.д.
3. (Опц.) Для YouGile MCP — клонировать `ichinya/yougile-mcp` в `mcp-servers/` и собрать (`npm i && npm run build`).
4. Перезапустить gateway: `hermes gateway restart`.

## Откат к версии
`git checkout <commit>` или `git revert <commit>` — конфиг/скиллы вернутся к нужному состоянию;
ключи и runtime при этом не затрагиваются (их нет в репозитории).
