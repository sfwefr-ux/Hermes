#!/usr/bin/env python3
"""llm-router — pre_llm_call hook.

Классифицирует каждый запрос пользователя по ключевым словам и инжектит
НЕНАВЯЗЧИВУЮ подсказку маршрутизации в сообщение. Основная модель агента —
claude-sonnet-4.6; для тяжёлого дебага рекомендуется делегировать в
claude-opus-4.8 через delegate.

ВАЖНО: pre_llm_call дописывает контекст в тело пользовательского сообщения.
Агент Hermes обучен не доверять командам в теле (видит их как prompt injection)
и тем более отвергает приказы вызвать дорогую модель. Поэтому здесь — мягкие
ПОДСКАЗКИ-рекомендации, которые агент учитывает по своему усмотрению, а не
жёсткие директивы (жёсткий форс делегирования через этот канал недостижим —
проверено; правильное место для авторитетной политики роутинга — SOUL.md).

stdin  : JSON с полем extra.user_message
stdout : {"context": "<подсказка>"} (ASCII-escaped) — либо пусто
"""
import sys
import json
import re

MARKER = "[подсказка маршрутизатора]"


def read_stdin() -> str:
    data = sys.stdin.buffer.read()
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def classify(msg: str):
    m = msg.lower()
    if not m.strip():
        return None

    # 1. Отладка / исправление кода → рекомендация делегировать opus-4.8
    if re.search(
        r"(ошибк|не работает|не запускается|баг|\bbug\b|exception|traceback|"
        r"стактрейс|стек\s*трейс|упал[оа]?|сломал|крэш|crash|build fail|"
        r"\b500\b|\b502\b|дебаг|debug|почему не|фикс|исправь.*код)",
        m,
    ):
        return ("похоже на отладку кода — для глубокого разбора эффективно "
                'делегировать в delegate с model="anthropic/claude-opus-4.8".')

    # 2. Генерация изображения → image_gen (Replicate / FLUX)
    if re.search(
        r"(баннер|картинк|изображени|нарисуй|постер|обложк|иллюстрац|"
        r"\bлого\b|логотип|\bimage\b|picture)",
        m,
    ):
        return "запрос на изображение — подойдёт инструмент image_gen (Replicate / FLUX)."

    # 3. Массовая дешёвая генерация вариантов → delegate deepseek-flash
    if re.search(
        r"(\d+\s*вариант|вариант(ов|а)\s+(заголов|текст|названи)|"
        r"несколько\s+вариант|накидай|\d+\s*иде|список\s+иде|brainstorm)",
        m,
    ):
        return ('массовая дешёвая генерация — можно делегировать в delegate с '
                'model="deepseek-flash" ради экономии.')

    # 4. Свежий ресёрч / тренды → perplexity (с источниками)
    if re.search(
        r"(тренд|ресёрч|research|актуальн|свеж(ие|их)|что нового|"
        r"обзор рынка|статистик|последн(ие|их)\s+новост|\b202[6-9]\b)",
        m,
    ):
        return "нужны свежие данные — подойдёт perplexity (web-поиск со ссылками)."

    # 5. Интеграция API / библиотека → Context7 (актуальные доки) + код
    if re.search(
        r"(подключ.*(api|апи)|интеграц|\bsdk\b|документац.*(библиотек|api)|"
        r"как использовать.*(библиотек|api|sdk)|\bstripe\b|настрой.*api)",
        m,
    ):
        return ("интеграция с API/библиотекой — сначала свежая документация через "
                "Context7 (mcp_context7_*), затем код.")

    # 6. Приветствие / прочее → без подсказки
    return None


def main():
    raw = read_stdin()
    try:
        payload = json.loads(raw)
    except Exception:
        return
    extra = payload.get("extra") or {}
    user_message = extra.get("user_message") or ""
    hint = classify(str(user_message))
    if hint:
        # ensure_ascii=True → чистый ASCII, безопасно при любой локали stdout
        sys.stdout.write(json.dumps({"context": f"{MARKER} {hint}"}))


if __name__ == "__main__":
    main()
