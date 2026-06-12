#!/usr/bin/env python3
"""Perplexity /search и /chat с автоматическим логированием стоимости для Hermes.

Тарифы Perplexity (docs.perplexity.ai/getting-started/pricing, сверено 2026-06-11):
  /search            : $5.00 / 1000 запросов  -> $0.005 за запрос (токены не тарифицируются)
  /chat sonar (low)  : request fee $5 / 1000 + $1.00 / 1M вход + $1.00 / 1M выход
  прочие тарифы chat — см. CHAT_PRICING ниже.

Каждый вызов:
  1) делает запрос к Perplexity,
  2) считает стоимость по тарифу,
  3) дописывает строку в CSV-реестр (с накопительным итогом),
  4) печатает стоимость запроса и общий итог в stderr.

Ключ читается из .env в рантайме (никогда не хардкодится в коде —
execute_code сжимает hex-строки ключей, см. pitfall в SKILL.md).
"""
import csv
import datetime
import json
import os
import sys
import urllib.request

HERMES_HOME = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "hermes"
)
ENV_PATH = os.environ.get("HERMES_ENV_PATH", os.path.join(HERMES_HOME, ".env"))
LEDGER = os.environ.get(
    "HERMES_COST_LEDGER", os.path.join(HERMES_HOME, "costs", "perplexity_costs.csv")
)

# $5.00 / 1000 запросов, без токенов
SEARCH_COST_PER_REQUEST = 5.0 / 1000

# request fee ($/1000 запросов) по размеру контекста + цена токенов ($/1M)
CHAT_PRICING = {
    "sonar": {"req": {"low": 5, "medium": 8, "high": 12}, "in": 1.0, "out": 1.0},
    "sonar-pro": {"req": {"low": 6, "medium": 10, "high": 14}, "in": 3.0, "out": 15.0},
    "sonar-reasoning-pro": {"req": {"low": 6, "medium": 10, "high": 14}, "in": 2.0, "out": 8.0},
}


def _read_key():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "PERPLEXITY_API_KEY" not in line or "=" not in line:
                continue
            val = line.split("=", 1)[1].strip().strip('"').strip("'")
            if val:
                return val
    raise RuntimeError("PERPLEXITY_API_KEY не найден в " + ENV_PATH)


def _post(url, payload, key):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _log(endpoint, model, units, cost):
    """Дописывает строку в CSV-реестр и возвращает накопительный итог."""
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    is_new = not os.path.exists(LEDGER)
    total = cost
    if not is_new:
        with open(LEDGER, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    total += float(row["cost_usd"])
                except (KeyError, ValueError):
                    pass
    with open(LEDGER, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(
                ["timestamp", "endpoint", "model", "units", "cost_usd", "running_total_usd"]
            )
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        w.writerow([ts, endpoint, model, units, "%.6f" % cost, "%.6f" % total])
    return total


def search(query, max_results=5, max_tokens_per_page=256):
    """Поиск через /search. Стоимость фиксированная: $0.005 за запрос."""
    key = _read_key()
    body = _post(
        "https://api.perplexity.ai/search",
        {
            "query": query,
            "max_results": max_results,
            "max_tokens_per_page": max_tokens_per_page,
        },
        key,
    )
    cost = SEARCH_COST_PER_REQUEST
    total = _log("/search", "-", "1 request", cost)
    sys.stderr.write(
        "[COST] Perplexity /search: $%.4f (этот запрос) | "
        "итого Hermes/Perplexity: $%.4f\n" % (cost, total)
    )
    return body


def chat(query, model="sonar", max_tokens=500, search_context_size="low"):
    """Чат через /chat/completions. Стоимость = request fee + цена токенов из usage."""
    key = _read_key()
    body = _post(
        "https://api.perplexity.ai/chat/completions",
        {
            "model": model,
            "messages": [{"role": "user", "content": query}],
            "max_tokens": max_tokens,
        },
        key,
    )
    usage = body.get("usage", {})
    p_in = usage.get("prompt_tokens", 0)
    p_out = usage.get("completion_tokens", 0)
    pricing = CHAT_PRICING.get(model, CHAT_PRICING["sonar"])
    req_fee = pricing["req"].get(search_context_size, pricing["req"]["low"]) / 1000.0
    cost = req_fee + p_in / 1e6 * pricing["in"] + p_out / 1e6 * pricing["out"]
    total = _log("/chat/completions", model, "%d in / %d out tok" % (p_in, p_out), cost)
    sys.stderr.write(
        "[COST] Perplexity /chat %s: $%.5f (%d in / %d out tok) | "
        "итого Hermes/Perplexity: $%.4f\n" % (model, cost, p_in, p_out, total)
    )
    return body


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Perplexity search/chat с логированием стоимости")
    ap.add_argument("query", help="поисковый запрос или сообщение")
    ap.add_argument("--mode", choices=["search", "chat"], default="search")
    ap.add_argument("--model", default="sonar")
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--max-tokens", type=int, default=500)
    ap.add_argument("--context", default="low", choices=["low", "medium", "high"])
    a = ap.parse_args()

    if a.mode == "search":
        out = search(a.query, max_results=a.max_results)
        for r in out.get("results", []):
            print("- %s — %s" % (r.get("title", ""), r.get("url", "")))
            if r.get("snippet"):
                print("  " + r["snippet"])
    else:
        out = chat(a.query, model=a.model, max_tokens=a.max_tokens, search_context_size=a.context)
        print(out["choices"][0]["message"]["content"])
