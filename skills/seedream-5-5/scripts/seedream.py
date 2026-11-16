#!/usr/bin/env python3
"""Key-safe helper for Seedream 5.5 on BytePlus ModelArk.

Standard library only (Python 3.8+).

    python seedream.py models
    python seedream.py generate --prompt "..." --size 16:9 --out out/
    python seedream.py generate --prompt-file shot.txt --image ref1.png --image ref2.png
    python seedream.py generate --prompt "..." --dry-run      # no key, no network

Key handling:
  * The API key is read ONLY from the ARK_API_KEY environment variable.
  * There is deliberately no --api-key flag (flags end up in shell history).
  * The key is never printed, logged, or written to any file. Error text from
    the server is scrubbed of the key before it is shown.

Every saved image gets a sidecar .txt with the exact prompt and parameters
(reference images are recorded by source and SHA-256, not by their bytes).
"""

import argparse
import base64
import datetime as _dt
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
DEFAULT_MODEL = "dola-seedream-5-5-261028"
MIN_AREA = 921600  # pixels; smaller requests are rejected by the API

SIZE_PRESETS = {
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "2:3": "1728x2592",
    "3:2": "2592x1728",
    "1:1": "2048x2048",
}

ENV_KEY = "ARK_API_KEY"


class HelperError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Key handling
# --------------------------------------------------------------------------- #

def get_key():
    key = os.environ.get(ENV_KEY, "").strip()
    if not key:
        raise HelperError(
            "{} is not set. Export your own ModelArk key in this shell, e.g.\n"
            "  bash:       export {}=...\n"
            "  PowerShell: $env:{} = '...'".format(ENV_KEY, ENV_KEY, ENV_KEY)
        )
    return key


def scrub(text, key):
    """Remove the key (and any Bearer token) from text before showing it."""
    if not text:
        return text
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-]+", "Bearer [REDACTED]", text)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def request_json(method, url, key, payload=None, timeout=300):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise HelperError("HTTP {} from {}:\n{}".format(e.code, url, scrub(body, key)))
    except urllib.error.URLError as e:
        raise HelperError("Network error for {}: {}".format(url, scrub(str(e.reason), key)))
    try:
        return json.loads(body)
    except ValueError:
        raise HelperError("Non-JSON response from {}:\n{}".format(url, scrub(body[:2000], key)))


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #

def parse_size(value):
    """Accept a ratio preset ('16:9'), 'WxH', or a size keyword passed through."""
    v = value.strip()
    if v in SIZE_PRESETS:
        v = SIZE_PRESETS[v]
    m = re.fullmatch(r"(\d+)\s*[xX*]\s*(\d+)", v)
    if not m:
        # Keywords like '2K' are passed through untouched for the API to judge.
        return v
    w, h = int(m.group(1)), int(m.group(2))
    if w * h < MIN_AREA:
        raise HelperError(
            "Size {}x{} is {} px; Seedream needs at least {} px of area. "
            "Try a preset: {}".format(
                w, h, w * h, MIN_AREA,
                ", ".join("{}={}".format(k, s) for k, s in SIZE_PRESETS.items()),
            )
        )
    return "{}x{}".format(w, h)


def load_image(ref):
    """Return (value_for_api, record_for_sidecar) for a path, URL or data URI."""
    if ref.startswith(("http://", "https://")):
        return ref, {"source": ref}
    if ref.startswith("data:"):
        digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()
        return ref, {"source": "inline data URI", "sha256": digest}
    if not os.path.isfile(ref):
        raise HelperError("Reference image not found: {}".format(ref))
    with open(ref, "rb") as f:
        raw = f.read()
    mime = mimetypes.guess_type(ref)[0] or sniff_mime(raw) or "image/png"
    uri = "data:{};base64,{}".format(mime, base64.b64encode(raw).decode("ascii"))
    return uri, {
        # Recorded as given, not absolute, so sidecars don't leak usernames or home paths.
        "source": ref.replace("\\", "/"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "mime": mime,
    }


def sniff_mime(raw):
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def ext_for(raw):
    return {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(
        sniff_mime(raw), ".bin"
    )


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_models(args):
    key = get_key()
    resp = request_json("GET", args.base_url.rstrip("/") + "/models", key)
    items = resp.get("data", resp if isinstance(resp, list) else [])
    pattern = (args.filter or "").lower()
    found = [m for m in items if pattern in json.dumps(m).lower()]
    if args.json:
        print(json.dumps(found, indent=2))
        return 0
    if not found:
        print("No models matched '{}'. {} models visible to this key.".format(pattern, len(items)))
        return 1
    for m in found:
        print(m.get("id") or m.get("name") or json.dumps(m))
    return 0


def build_payload(args):
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    else:
        prompt = (args.prompt or "").strip()
    if not prompt:
        raise HelperError("Give --prompt or --prompt-file.")

    payload = {
        "model": args.model,
        "prompt": prompt,
        "size": parse_size(args.size),
        "response_format": "b64_json",
        "watermark": args.watermark,
    }
    image_records = []
    if args.image:
        values = []
        for ref in args.image:
            value, record = load_image(ref)
            values.append(value)
            image_records.append(record)
        payload["image"] = values[0] if len(values) == 1 else values
    if args.extra:
        try:
            extra = json.loads(args.extra)
        except ValueError as e:
            raise HelperError("--extra must be a JSON object: {}".format(e))
        if not isinstance(extra, dict):
            raise HelperError("--extra must be a JSON object.")
        for reserved in ("prompt", "image", "response_format"):
            if reserved in extra:
                raise HelperError("Set '{}' with its own flag, not --extra.".format(reserved))
        payload.update(extra)
    return payload, image_records


def redacted_payload(payload, image_records):
    shown = dict(payload)
    if "image" in shown:
        shown["image"] = image_records
    return shown


def unique_path(out_dir, stem, ext):
    path = os.path.join(out_dir, stem + ext)
    n = 2
    while os.path.exists(path) or os.path.exists(os.path.splitext(path)[0] + ".txt"):
        path = os.path.join(out_dir, "{}_{}{}".format(stem, n, ext))
        n += 1
    return path


def write_sidecar(path, payload, image_records, index, total, response_meta):
    lines = [
        "# Seedream generation record",
        "created: " + _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "image: {} ({} of {})".format(os.path.basename(path), index + 1, total),
        "model: " + str(payload.get("model")),
        "",
        "## prompt",
        payload["prompt"],
        "",
        "## parameters",
        json.dumps(
            {k: v for k, v in payload.items() if k not in ("prompt", "image")},
            indent=2, ensure_ascii=False,
        ),
        "",
        "## reference images (in order: Image 1, Image 2, ...)",
        json.dumps(image_records, indent=2, ensure_ascii=False) if image_records else "none",
        "",
        "## response metadata",
        json.dumps(response_meta, indent=2, ensure_ascii=False),
        "",
    ]
    txt = os.path.splitext(path)[0] + ".txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return txt


def cmd_generate(args):
    payload, image_records = build_payload(args)

    if args.dry_run:
        print(json.dumps(redacted_payload(payload, image_records), indent=2, ensure_ascii=False))
        return 0

    key = get_key()
    url = args.base_url.rstrip("/") + "/images/generations"
    resp = request_json("POST", url, key, payload, timeout=args.timeout)

    if resp.get("error"):
        raise HelperError("API error: " + scrub(json.dumps(resp["error"]), key))
    data = resp.get("data") or []
    if not data:
        raise HelperError("No images in response: " + scrub(json.dumps(resp)[:2000], key))

    os.makedirs(args.out, exist_ok=True)
    stem = args.name or _dt.datetime.now().strftime("seedream_%Y%m%d_%H%M%S")
    meta = {k: v for k, v in resp.items() if k != "data"}

    saved = 0
    for i, item in enumerate(data):
        if item.get("error"):
            print("image {} failed: {}".format(i + 1, scrub(json.dumps(item["error"]), key)),
                  file=sys.stderr)
            continue
        b64 = item.get("b64_json")
        if not b64:
            print("image {} has no b64_json (keys: {})".format(i + 1, sorted(item)),
                  file=sys.stderr)
            continue
        raw = base64.b64decode(b64)
        item_meta = dict(meta)
        item_meta.update({k: v for k, v in item.items() if k != "b64_json"})
        path = unique_path(args.out, stem if len(data) == 1 else "{}_{}".format(stem, i + 1),
                           ext_for(raw))
        with open(path, "wb") as f:
            f.write(raw)
        txt = write_sidecar(path, payload, image_records, i, len(data), item_meta)
        print("saved {}  (+ {})".format(path, os.path.basename(txt)))
        saved += 1
    return 0 if saved else 1


# --------------------------------------------------------------------------- #

def main(argv=None):
    p = argparse.ArgumentParser(description="Seedream 5.5 helper for BytePlus ModelArk.")
    p.add_argument("--base-url", default=os.environ.get("ARK_BASE_URL", DEFAULT_BASE_URL),
                   help="API base (default: %(default)s; env ARK_BASE_URL)")
    sub = p.add_subparsers(dest="cmd")

    pm = sub.add_parser("models", help="List models visible to your key.")
    pm.add_argument("--filter", default="seedream", help="Substring filter (default: seedream).")
    pm.add_argument("--json", action="store_true", help="Print full JSON records.")

    pg = sub.add_parser("generate", help="Generate image(s).")
    src = pg.add_mutually_exclusive_group()
    src.add_argument("--prompt")
    src.add_argument("--prompt-file", help="UTF-8 text file holding the prompt.")
    pg.add_argument("--size", default="16:9",
                    help="Preset ({}) or WxH; min area {} px.".format(
                        ", ".join(SIZE_PRESETS), MIN_AREA))
    pg.add_argument("--image", action="append",
                    help="Reference image: local path, URL or data URI. Repeat for "
                         "several; order = Image 1, Image 2, ...")
    pg.add_argument("--model", default=os.environ.get("SEEDREAM_MODEL", DEFAULT_MODEL),
                    help="Model ID (default: %(default)s; env SEEDREAM_MODEL)")
    pg.add_argument("--watermark", action="store_true", help="Ask for a watermark (off by default).")
    pg.add_argument("--extra", help="JSON object of extra request fields, passed through as-is.")
    pg.add_argument("--out", default="seedream_out", help="Output folder (default: %(default)s)")
    pg.add_argument("--name", help="File stem; a suffix is added rather than overwrite.")
    pg.add_argument("--timeout", type=int, default=300)
    pg.add_argument("--dry-run", action="store_true",
                    help="Print the request body (images summarised) and exit. No key needed.")

    args = p.parse_args(argv)
    try:
        if args.cmd == "models":
            return cmd_models(args)
        if args.cmd == "generate":
            return cmd_generate(args)
        p.print_help()
        return 2
    except HelperError as e:
        print("error: " + str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
