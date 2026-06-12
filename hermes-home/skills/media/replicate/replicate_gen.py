#!/usr/bin/env python3
"""Replicate generation helper for Hermes.

Генерация картинок и видео через Replicate в премиум-качестве.
Только стандартная библиотека (urllib) — внешних зависимостей нет.

Дефолтные модели (лучшее на 2026):
  image -> google/imagen-4-ultra
  video -> google/veo-3.1

Стоимость каждого вызова логируется в <HERMES_HOME>/spend-log.md (оценка).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API_ROOT = "https://api.replicate.com/v1"

# Модели по уровням: cheap — повседневные дешёвые, premium — лучшее качество.
DEFAULT_MODELS = {
    ("image", "cheap"): "black-forest-labs/flux-schnell",
    ("image", "premium"): "google/imagen-4-ultra",
    ("video", "cheap"): "wan-video/wan-2.2-t2v-fast",
    ("video", "premium"): "google/veo-3.1",
}

# Грубая оценка стоимости (USD) для лога расходов. Не биллинг.
COST_HINT = {
    "black-forest-labs/flux-schnell": ("image", 0.003),
    "google/imagen-4-ultra": ("image", 0.06),
    "black-forest-labs/flux-1.1-pro-ultra": ("image", 0.06),
    "google/nano-banana": ("image", 0.039),
    "recraft-ai/recraft-v3": ("image", 0.04),
    "wan-video/wan-2.2-t2v-fast": ("video", 0.05),
    "google/veo-3.1": ("video", 6.0),   # ~8с, с аудио
    "google/veo-3": ("video", 6.0),
    "minimax/hailuo-02": ("video", 0.5),
    "kwaivgi/kling-v2.1": ("video", 0.28),
}


def hermes_home() -> Path:
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "hermes"
    return Path.home() / ".hermes"


def load_token() -> str:
    tok = os.environ.get("REPLICATE_API_TOKEN") or os.environ.get("REPLICATE_API_KEY")
    if tok:
        return tok.strip()
    env_file = hermes_home() / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("REPLICATE_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit("Error: REPLICATE_API_TOKEN не задан (env или <HERMES_HOME>/.env).")


def _req(url: str, token: str, method: str = "GET", body: dict | None = None,
         extra_headers: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"Replicate API {e.code}: {detail[:500]}")


def create_prediction(model: str, inputs: dict, token: str) -> dict:
    url = f"{API_ROOT}/models/{model}/predictions"
    # Prefer: wait — блокирует до ~60с, картинки обычно успевают.
    return _req(url, token, method="POST", body={"input": inputs},
                extra_headers={"Prefer": "wait"})


def poll(prediction: dict, token: str, timeout_s: int = 900) -> dict:
    status = prediction.get("status")
    get_url = (prediction.get("urls") or {}).get("get")
    start = time.time()
    while status in ("starting", "processing"):
        if time.time() - start > timeout_s:
            sys.exit(f"Таймаут ожидания ({timeout_s}s). id={prediction.get('id')}")
        time.sleep(3)
        prediction = _req(get_url, token)
        status = prediction.get("status")
    return prediction


def collect_outputs(output) -> list[str]:
    if output is None:
        return []
    if isinstance(output, str):
        return [output]
    if isinstance(output, list):
        return [o for o in output if isinstance(o, str)]
    if isinstance(output, dict):
        # некоторые модели отдают {"output": url} или {"video": url}
        for v in output.values():
            if isinstance(v, str) and v.startswith("http"):
                return [v]
    return []


def download(urls: list[str], out_dir: Path, kind: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, url in enumerate(urls):
        ext = url.split("?")[0].rsplit(".", 1)[-1]
        if len(ext) > 5 or "/" in ext:
            ext = "mp4" if kind == "video" else "png"
        name = f"replicate_{kind}_{ts}_{i}.{ext}"
        dest = out_dir / name
        with urllib.request.urlopen(url, timeout=300) as r, open(dest, "wb") as f:
            f.write(r.read())
        saved.append(dest)
    return saved


def log_cost(model: str, est: float) -> None:
    try:
        path = hermes_home() / "spend-log.md"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{ts} | replicate {model} ~${est:.3f} | итог ~${est:.3f}\n")
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Replicate image/video generation for Hermes")
    ap.add_argument("--type", choices=["image", "video"], required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--tier", choices=["cheap", "premium"], default="cheap",
                    help="cheap — повседневные дешёвые модели (по умолчанию); premium — лучшее качество")
    ap.add_argument("--model", default=None, help="owner/name; переопределяет выбор по --tier")
    ap.add_argument("--aspect", default=None, help="aspect_ratio, напр. 16:9, 1:1, 9:16")
    ap.add_argument("--duration", type=int, default=None, help="видео: длительность в секундах")
    ap.add_argument("--resolution", default=None, help="видео: 720p/1080p")
    ap.add_argument("--no-audio", action="store_true", help="видео: без звука")
    ap.add_argument("--image", default=None, help="видео: исходное изображение (url/путь) для image-to-video")
    ap.add_argument("--output-format", default=None, help="картинка: jpg/png")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    token = load_token()
    model = args.model or DEFAULT_MODELS[(args.type, args.tier)]

    inputs: dict = {"prompt": args.prompt}
    if args.type == "image":
        if args.aspect:
            inputs["aspect_ratio"] = args.aspect
        if args.output_format:
            inputs["output_format"] = args.output_format
        default_out = hermes_home() / "image_cache"
    else:
        if args.aspect:
            inputs["aspect_ratio"] = args.aspect
        if args.duration:
            inputs["duration"] = args.duration
        if args.resolution:
            inputs["resolution"] = args.resolution
        if args.no_audio:
            inputs["generate_audio"] = False
        if args.image:
            inputs["image"] = args.image
        default_out = hermes_home() / "video_cache"

    out_dir = Path(args.out_dir) if args.out_dir else default_out

    print(f"[replicate] tier={args.tier} model={model} type={args.type}", file=sys.stderr)
    pred = create_prediction(model, inputs, token)
    pred = poll(pred, token)

    if pred.get("status") != "succeeded":
        sys.exit(f"Генерация не удалась: status={pred.get('status')} error={pred.get('error')}")

    urls = collect_outputs(pred.get("output"))
    if not urls:
        sys.exit(f"Пустой вывод. raw={json.dumps(pred.get('output'))[:300]}")

    saved = download(urls, out_dir, args.type)

    est = COST_HINT.get(model, (args.type, 0.05))[1]
    log_cost(model, est)

    print(f"[replicate] стоимость ~${est:.3f} (оценка, записано в spend-log.md)", file=sys.stderr)
    for p in saved:
        print(str(p))


if __name__ == "__main__":
    main()
