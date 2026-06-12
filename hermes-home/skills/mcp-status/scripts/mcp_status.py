#!/usr/bin/env python3
"""Показать установленные MCP-серверы Hermes, наличие ключей и активность.

Читает:
  - <HERMES_HOME>/config.yaml  → секция mcp_servers (что установлено)
  - <HERMES_HOME>/.env         → какие ключи присутствуют (ТОЛЬКО имена, без значений)
  - <HERMES_HOME>/logs/agent.log → какие серверы реально зарегистрировались (активны)

Секреты не печатаются никогда — только факт «ключ есть / нет».
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME", "").strip()
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA", "").strip()
    if local:
        return Path(local) / "hermes"
    return Path.home() / ".hermes"


# Известные пакеты/серверы, которым нужен ключ через наследуемую переменную окружения
# (в самом config их может не быть как ${VAR}).
KNOWN_ENV_HINTS = {
    "@modelcontextprotocol/server-github": "GITHUB_PERSONAL_ACCESS_TOKEN",
    "firecrawl-mcp": "FIRECRAWL_API_KEY",
}


def load_env_keys(home: Path) -> set[str]:
    keys: set[str] = set()
    envf = home / ".env"
    if not envf.exists():
        return keys
    for line in envf.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, val = line.partition("=")
        if val.strip():
            keys.add(name.strip())
    return keys


def collect_strings(obj) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += collect_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            out += collect_strings(v)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def key_status(name: str, cfg: dict, env_keys: set[str]) -> str:
    strings = collect_strings(cfg)
    blob = " ".join(strings)

    # 1) ссылки вида ${VAR}
    refs = set(re.findall(r"\$\{([A-Z0-9_]+)\}", blob))
    # 2) известные пакеты, требующие ключ из окружения
    for s in strings:
        for pkg, var in KNOWN_ENV_HINTS.items():
            if pkg in s:
                refs.add(var)

    if refs:
        present = [v for v in sorted(refs) if v in env_keys]
        missing = [v for v in sorted(refs) if v not in env_keys]
        if missing and not present:
            return f"✗ нет ключа (отсутствует: {', '.join(missing)})"
        if missing:
            return f"⚠ частично (есть: {', '.join(present)}; нет: {', '.join(missing)})"
        return f"✓ ключ есть ({', '.join(present)})"

    # 3) ключ зашит прямо в конфиг (inline Bearer / --api-key c литералом)
    if re.search(r"Bearer\s+\S+", blob) or "--api-key" in strings or "sk_" in blob or "ctx7sk-" in blob:
        return "✓ ключ зашит в конфиг (inline)"

    return "— ключ не требуется"


def log_status(home: Path) -> dict[str, str]:
    """Последнее известное состояние каждого сервера из лога."""
    status: dict[str, str] = {}
    logf = home / "logs" / "agent.log"
    if not logf.exists():
        return status
    reg = re.compile(r"MCP server '([^']+)' \(([^)]+)\): registered (\d+) tool")
    fail = re.compile(r"MCP server '([^']+)' failed after .* giving up")
    for line in logf.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = reg.search(line)
        if m:
            status[m.group(1)] = f"✅ активен ({m.group(3)} инстр.)"
            continue
        f = fail.search(line)
        if f:
            status[f.group(1)] = "❌ не подключился"
    return status


def main() -> int:
    home = hermes_home()
    cfgf = home / "config.yaml"
    if not cfgf.exists():
        print(f"config.yaml не найден: {cfgf}")
        return 1
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load(cfgf.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"Не удалось прочитать config.yaml: {e}")
        return 1

    servers = cfg.get("mcp_servers") or {}
    env_keys = load_env_keys(home)
    live = log_status(home)

    if not servers:
        print("MCP-серверы не настроены (секция mcp_servers пуста).")
        return 0

    print(f"MCP-серверы Hermes ({home})\n")
    rows = []
    for name, scfg in servers.items():
        scfg = scfg if isinstance(scfg, dict) else {}
        stype = scfg.get("type") or ("http" if scfg.get("url") else "stdio")
        rows.append((name, stype, key_status(name, scfg, env_keys), live.get(name, "❔ статус неизвестен")))

    w0 = max(len(r[0]) for r in rows + [("СЕРВЕР", "", "", "")])
    w1 = max(len(r[1]) for r in rows + [("", "ТИП", "", "")])
    print(f"{'СЕРВЕР'.ljust(w0)}  {'ТИП'.ljust(w1)}  {'КЛЮЧ'.ljust(34)}  АКТИВНОСТЬ")
    print("-" * (w0 + w1 + 34 + 24))
    for name, stype, ks, act in rows:
        print(f"{name.ljust(w0)}  {stype.ljust(w1)}  {ks.ljust(34)}  {act}")

    active = sum(1 for r in rows if "активен" in r[3])
    print(f"\nИтого: установлено {len(rows)}, активно {active}.")
    print("Команды управления: /reload-mcp — переподключить серверы.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
