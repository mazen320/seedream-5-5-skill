#!/usr/bin/env python3
"""Key-safe Seedream helper for many API platforms.

Standard library only (Python 3.8+).

    python seedream.py providers
    python seedream.py models                                   # BytePlus / Volcengine only
    python seedream.py generate --prompt "..." --size 16:9 --out out
    python seedream.py generate --provider fal --prompt-file p.txt --image https://.../ref.png
    python seedream.py generate --prompt "..." --dry-run          # no key, no network
    python seedream.py batch assets.json                          # plan + cost; add --yes to run
    python seedream.py costs                                      # what this project has spent

Key handling:
  * Each provider's key is read ONLY from its environment variable (see `providers`).
  * There is deliberately no --api-key flag (flags end up in shell history).
  * Keys are never printed, logged or written to files, and are scrubbed from error text.
  * Result images on third-party CDNs are downloaded WITHOUT the API key.

Every saved image gets a sidecar .txt with the exact prompt and parameters.
Reference images are recorded by the path or URL as given plus their SHA-256, never by
their bytes and never as absolute paths.
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
import time
import urllib.error
import urllib.request
import uuid

MIN_AREA = 921600      # Seedream 5.5 / 5.0 pro / 5.0 flash, confirmed by the API
MAX_AREA = 4624220     # same models, confirmed by the API
MAX_AREA_LEGACY = 16777216   # 5.0 lite / 4.5 / 4.0 (official docs; 4K class)

# Ratio presets -> WxH (all within the 5.5 area limits).
SIZE_PRESETS = {
    "1:1": "2048x2048",
    "4:3": "2304x1728",
    "3:4": "1728x2304",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "3:2": "2592x1728",
    "2:3": "1728x2592",
    "21:9": "3024x1296",
}
TIERS = {"1K", "1.5K", "2K"}
TIERS_LEGACY = {"1K", "2K", "3K", "4K"}   # 5.0 lite / 4.5 / 4.0 (varies by model)


def _now():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HelperError(Exception):
    pass


def warn(msg):
    print("warning: " + msg, file=sys.stderr)


# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #
#
# Each provider declares: env var, default base URL, default models, whether local
# files can be sent inline (data URIs), and build/submit/collect functions.
# "live" marks providers whose contract was exercised against the real API.

PROVIDERS = {
    "byteplus": {
        "env": "ARK_API_KEY",
        "base": "https://ark.ap-southeast.bytepluses.com/api/v3",
        "model": "dola-seedream-5-5-261028",
        "inline_images": True,
        "live": True,
        "note": "Official ByteDance (international). Seedream 5.5.",
    },
    "volcengine": {
        "env": "ARK_API_KEY",
        "base": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "doubao-seedream-5-5-261028",
        "inline_images": True,
        "live": False,
        "note": "Official ByteDance (China). Same API as byteplus.",
    },
    "runware": {
        "env": "RUNWARE_API_KEY",
        "base": "https://api.runware.ai/v1",
        "model": "bytedance:seedream@5.5",
        "inline_images": True,
        "live": False,
        "note": "Seedream 5.5. Sync task API.",
    },
    "wavespeed": {
        "env": "WAVESPEED_API_KEY",
        "base": "https://api.wavespeed.ai/api/v3",
        "model": "bytedance/seedream-v5.5",
        "edit_model": "bytedance/seedream-v5.5/edit",
        "inline_images": True,
        "live": False,
        "note": "Seedream 5.5. Async (submit + poll).",
    },
    "kie": {
        "env": "KIE_API_KEY",
        "base": "https://api.kie.ai/api/v1",
        "model": "seedream/5-5-text-to-image",
        "edit_model": "seedream/5-5-image-to-image",
        "inline_images": False,
        "live": False,
        "note": "Seedream 5.5. Async. Reference images must be public URLs.",
    },
    "evolink": {
        "env": "EVOLINK_API_KEY",
        "base": "https://api.evolink.ai/v1",
        "model": "doubao-seedream-5.5",
        "inline_images": False,
        "live": False,
        "note": "Seedream 5.5 (availability varies). Async. Reference images must be public URLs.",
    },
    "fal": {
        "env": "FAL_KEY",
        "base": "https://queue.fal.run",
        "model": "bytedance/seedream/v5.5/text-to-image",
        "edit_model": "bytedance/seedream/v5.5/edit",
        "inline_images": True,
        "live": False,
        "note": "Seedream 5.5 (5.0 Pro: --model bytedance/seedream/v5/pro/...). Async queue. --layers uses v5.5/layerize.",
    },
    "replicate": {
        "env": "REPLICATE_API_TOKEN",
        "base": "https://api.replicate.com/v1",
        "model": "bytedance/seedream-5-pro",
        "inline_images": True,
        "live": False,
        "note": "Seedream 5.0 Pro (no 5.5 yet). Async with wait.",
    },
    "openrouter": {
        "env": "OPENROUTER_API_KEY",
        "base": "https://openrouter.ai/api/v1",
        "model": "bytedance-seed/seedream-5-5",
        "inline_images": True,
        "live": False,
        "note": "Seedream 5.5 (5.0 Pro: --model bytedance-seed/seedream-5-0-pro). Sync.",
    },
}


# --------------------------------------------------------------------------- #
# Key handling
# --------------------------------------------------------------------------- #

def get_key(provider):
    env = PROVIDERS[provider]["env"]
    key = os.environ.get(env, "").strip()
    if not key:
        raise HelperError(
            "{} is not set (needed for provider '{}'). Export your own key in this shell:\n"
            "  bash:       export {}=...\n"
            "  PowerShell: $env:{} = '...'".format(env, provider, env, env)
        )
    return key


def scrub(text, key):
    """Remove the key (and any Bearer/Key token) from text before showing it."""
    if not text:
        return text
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"(?i)\b(bearer|key)\s+[A-Za-z0-9._:\-]{8,}", r"\1 [REDACTED]", text)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

class Http:
    def __init__(self, key, auth_header="Authorization", auth_prefix="Bearer "):
        self.key = key
        self.auth_header = auth_header
        self.auth_prefix = auth_prefix

    def json(self, method, url, payload=None, headers=None, timeout=300):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header(self.auth_header, self.auth_prefix + self.key)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise HelperError("HTTP {} from {}:\n{}".format(e.code, url, scrub(body, self.key)))
        except urllib.error.URLError as e:
            raise HelperError("Network error for {}: {}".format(url, scrub(str(e.reason), self.key)))
        except OSError as e:          # e.g. socket.timeout on Python 3.8
            raise HelperError("Network error for {}: {}".format(url, scrub(str(e), self.key)))
        try:
            return json.loads(body)
        except ValueError:
            raise HelperError("Non-JSON response from {}:\n{}".format(url, scrub(body[:2000], self.key)))


def download(url, timeout=300):
    """Fetch a result image. Deliberately sends NO credentials."""
    if url.startswith("data:"):
        return base64.b64decode(url.split(",", 1)[1])
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, OSError) as e:
        raise HelperError("Could not download result image {}: {}".format(url, e))


def poll(fn, timeout, interval):
    """Call fn() until it returns a non-None value or the timeout passes."""
    deadline = time.time() + timeout
    failures = 0
    while True:
        try:
            result = fn()
            failures = 0
        except HelperError as e:
            # A job that was already submitted (and billed) shouldn't die on one blip.
            if failures < 3 and re.search(r"HTTP (429|5\d\d)|Network error", str(e)):
                failures += 1
                time.sleep(max(interval, 0.5) * failures)
                continue
            raise
        if result is not None:
            return result
        if time.time() > deadline:
            raise HelperError("Timed out after {}s waiting for the result.".format(timeout))
        time.sleep(interval)


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #

def is_legacy(model):
    """True for Seedream 5.0 lite / 4.5 / 4.0, which allow 4K sizes and 14 references."""
    m = (model or "").lower()
    if "seedream" not in m and "seedream" not in m.replace("-", ""):
        return False
    return bool(re.search(r"seedream[-_/@.v]*4|seedream-5-0-(lite-)?260128|seedream-5-0-lite|seedream/v5/lite|seedream-5-lite", m))


def parse_size(value, model=None):
    """Return (kind, data). kind is 'wh' with (w, h) or 'tier' with e.g. '2K'."""
    legacy = is_legacy(model)
    max_area = MAX_AREA_LEGACY if legacy else MAX_AREA
    v = value.strip()
    if v.upper() in ((TIERS_LEGACY | TIERS) if legacy else TIERS):
        return "tier", v.upper()
    if v in SIZE_PRESETS:
        v = SIZE_PRESETS[v]
    m = re.fullmatch(r"(\d+)\s*[xX*]\s*(\d+)", v)
    if not m:
        raise HelperError("Unrecognised --size '{}'. Use a ratio ({}), a tier (1K, 1.5K, 2K) "
                          "or WxH.".format(value, ", ".join(SIZE_PRESETS)))
    w, h = int(m.group(1)), int(m.group(2))
    if not MIN_AREA <= w * h <= max_area:
        raise HelperError(
            "Size {}x{} is {:,} px; this model needs {:,} to {:,} px of area. "
            "Presets: {}".format(w, h, w * h, MIN_AREA, max_area,
                                 ", ".join("{}={}".format(k, s) for k, s in SIZE_PRESETS.items())))
    if max(w, h) / min(w, h) > 16:
        raise HelperError("Aspect ratio must be between 1:16 and 16:1.")
    return "wh", (w, h)


def ratio_of(w, h):
    """Map WxH to the closest named ratio, for providers that only take aspect_ratio."""
    target = w / h
    best = min(SIZE_PRESETS, key=lambda r: abs(eval_ratio(r) - target))
    if abs(eval_ratio(best) - target) > 0.02:
        raise HelperError("This provider only accepts named aspect ratios ({}); {}x{} is not one."
                          .format(", ".join(SIZE_PRESETS), w, h))
    return best


def eval_ratio(r):
    a, b = r.split(":")
    return int(a) / int(b)


def sniff_mime(raw):
    if raw.startswith(b"\x89PNG"):
        return "image/png"
    if raw.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


def ext_for(raw):
    return {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(sniff_mime(raw), ".bin")


def safe_source(ref):
    """A path for the sidecar that never leaks usernames or home directories:
    relative to the working directory when inside it, otherwise just the file name."""
    if not os.path.isabs(ref):
        return ref.replace("\\", "/")
    try:
        rel = os.path.relpath(ref)
        if not rel.startswith(".."):
            return rel.replace("\\", "/")
    except ValueError:          # different drive on Windows
        pass
    return os.path.basename(ref)


def load_image(ref, inline_ok):
    """Return (value_for_api, record_for_sidecar) for a path, URL or data URI."""
    if ref.startswith(("http://", "https://")):
        return ref, {"source": ref}
    if ref.startswith("data:"):
        if not inline_ok:
            raise HelperError("This provider needs public image URLs, not data URIs.")
        return ref, {"source": "inline data URI", "sha256": hashlib.sha256(ref.encode()).hexdigest()}
    if not os.path.isfile(ref):
        raise HelperError("Reference image not found: {}".format(ref))
    if not inline_ok:
        raise HelperError("This provider needs public image URLs. Upload '{}' somewhere public "
                          "(or use byteplus / volcengine / runware / wavespeed / fal / replicate / "
                          "openrouter, which accept local files).".format(ref))
    with open(ref, "rb") as f:
        raw = f.read()
    mime = mimetypes.guess_type(ref)[0] or sniff_mime(raw) or "image/png"
    uri = "data:{};base64,{}".format(mime, base64.b64encode(raw).decode("ascii"))
    return uri, {
        "source": safe_source(ref),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "mime": mime,
    }


# --------------------------------------------------------------------------- #
# Request builders: return (url, body) for the submit call.
# `spec` is the provider-neutral request.
# --------------------------------------------------------------------------- #

def _ark(spec, base):
    body = {"model": spec["model"], "prompt": spec["prompt"],
            "response_format": "b64_json", "watermark": spec["watermark"]}
    kind, val = spec["size"]
    body["size"] = "{}x{}".format(*val) if kind == "wh" else val
    if spec["images"]:
        body["image"] = spec["images"][0] if len(spec["images"]) == 1 else spec["images"]
    if spec["background"]:
        body["background"] = spec["background"]
    if spec["output_format"]:
        body["output_format"] = spec["output_format"]
    if spec.get("layers"):
        body["layer_decomposition"] = True
        body["layer_decomposition_options"] = {"max_images": spec["layers"],
                                               "text_recognition": spec.get("layers_ocr", False)}
    return base + "/images/generations", body


def _runware(spec, base):
    task = {"taskType": "imageInference", "taskUUID": str(uuid.uuid4()),
            "model": spec["model"], "positivePrompt": spec["prompt"],
            "outputType": "base64Data", "numberResults": 1}
    kind, val = spec["size"]
    if kind == "wh":
        task["width"], task["height"] = val
    else:
        task["resolution"] = val
    if spec["images"]:
        task["inputs"] = {"referenceImages": spec["images"]}
    if spec["output_format"]:
        task["outputFormat"] = spec["output_format"].upper().replace("JPEG", "JPG")
    if spec["background"]:
        task["settings"] = {"background": spec["background"]}
    return base, [task]


def _tier_and_ratio(spec, default_tier="2K"):
    """Ratio-only platforms need an aspect ratio. A bare tier gets 1:1 for text-to-image
    (said out loud, never silently) and follows the input image for edits."""
    kind, val = spec["size"]
    if kind == "wh":
        return default_tier, ratio_of(*val)
    if not spec["images"]:
        warn("size '{}' has no aspect ratio; sending 1:1. Pass a ratio like 16:9 to change it.".format(val))
        return val, "1:1"
    return val, None


def _wavespeed(spec, base):
    tier, ratio = _tier_and_ratio(spec)
    body = {"prompt": spec["prompt"], "resolution": tier.lower()}
    if ratio:
        body["aspect_ratio"] = ratio
    if spec["images"]:
        body["images"] = spec["images"]
    if spec["output_format"]:
        body["output_format"] = spec["output_format"]
    if spec["background"]:
        body["background"] = spec["background"]
    return base + "/" + spec["model"], body


def _kie(spec, base):
    tier, ratio = _tier_and_ratio(spec)
    inp = {"prompt": spec["prompt"], "size": tier}
    if ratio:
        inp["aspect_ratio"] = ratio
    if spec["images"]:
        inp["image_urls"] = spec["images"]
    if spec["output_format"]:
        inp["output_format"] = spec["output_format"]
    if spec["background"]:
        inp["background"] = spec["background"]
    return base + "/jobs/createTask", {"model": spec["model"], "input": inp}


def _evolink(spec, base):
    kind, val = spec["size"]
    body = {"model": spec["model"], "prompt": spec["prompt"], "watermark": spec["watermark"]}
    if kind == "wh":
        body["size"] = "{}x{}".format(*val)
    else:
        body["quality"] = val
    if spec["images"]:
        body["image_urls"] = spec["images"]
    if spec["output_format"]:
        body["output_format"] = spec["output_format"]
    if spec["background"]:
        body["background"] = spec["background"]
    return base + "/images/generations", body


def _fal(spec, base):
    kind, val = spec["size"]
    if spec.get("layers"):
        tier = val if kind == "tier" and val in ("1K", "1.5K", "2K") else None
        body = {"prompt": spec["prompt"], "image_url": spec["images"][0], "max_images": spec["layers"],
                "enable_text_recognition": bool(spec.get("layers_ocr")),
                "image_size": "auto_" + tier if tier else "auto"}
        return base + "/bytedance/seedream/v5.5/layerize", body
    body = {"prompt": spec["prompt"], "num_images": 1}
    if kind == "wh":
        body["image_size"] = {"width": val[0], "height": val[1]}
    else:
        body["image_size"] = "auto_" + val
    if spec["background"]:
        if "v5.5" in spec["model"]:
            body["background"] = spec["background"]
        else:
            warn("Only fal's Seedream 5.5 endpoints take a background option; --background ignored.")
    if spec["images"]:
        body["image_urls"] = spec["images"]
    if spec["output_format"]:
        body["output_format"] = spec["output_format"]
    return base + "/" + spec["model"], body


def _replicate(spec, base):
    tier, ratio = _tier_and_ratio(spec)
    if tier not in ("1K", "2K"):
        warn("Replicate accepts 1K or 2K; using 2K instead of {}.".format(tier))
    inp = {"prompt": spec["prompt"], "size": tier if tier in ("1K", "2K") else "2K"}
    inp["aspect_ratio"] = ratio or "match_input_image"
    if spec["images"]:
        inp["image_input"] = spec["images"]
    if spec["output_format"]:
        inp["output_format"] = spec["output_format"]
    return base + "/models/" + spec["model"] + "/predictions", {"input": inp}


def _openrouter(spec, base):
    tier, ratio = _tier_and_ratio(spec)
    if tier not in ("1K", "2K"):
        warn("OpenRouter accepts 1K or 2K; using 2K instead of {}.".format(tier))
    body = {"model": spec["model"], "prompt": spec["prompt"],
            "resolution": tier if tier in ("1K", "2K") else "2K", "n": 1}
    if ratio:
        body["aspect_ratio"] = ratio
    if spec["images"]:
        body["input_references"] = [{"type": "image_url", "image_url": {"url": u}} for u in spec["images"]]
    if spec["output_format"]:
        body["output_format"] = spec["output_format"]
    if spec["background"]:
        body["background"] = spec["background"]
    return base + "/images", body


BUILDERS = {
    "byteplus": _ark, "volcengine": _ark, "runware": _runware, "wavespeed": _wavespeed,
    "kie": _kie, "evolink": _evolink, "fal": _fal, "replicate": _replicate,
    "openrouter": _openrouter,
}


# --------------------------------------------------------------------------- #
# Result collection: return (list of image refs (url / data: / b64 str), metadata dict).
# --------------------------------------------------------------------------- #

def _b64(s):
    return "data:;base64," + s


def collect(provider, http, resp, base, args):
    t, iv = args.timeout, args.poll_interval

    if provider in ("byteplus", "volcengine"):
        if resp.get("error"):
            raise HelperError("API error: " + json.dumps(resp["error"]))
        imgs = [_b64(d["b64_json"]) if d.get("b64_json") else d.get("url") for d in resp.get("data", [])
                if not d.get("error")]
        return [i for i in imgs if i], {k: v for k, v in resp.items() if k != "data"}

    if provider == "runware":
        if resp.get("errors"):
            raise HelperError("API error: " + json.dumps(resp["errors"]))
        out, meta = [], {}
        for d in resp.get("data", []):
            ref = (_b64(d["imageBase64Data"]) if d.get("imageBase64Data")
                   else d.get("imageDataURI") or d.get("imageURL"))
            if ref:
                out.append(ref)
            meta.update({k: d[k] for k in ("seed", "cost", "imageUUID") if k in d})
        return out, meta

    if provider == "wavespeed":
        pid = resp["data"]["id"]

        def check():
            r = http.json("GET", "{}/predictions/{}/result".format(base, pid))["data"]
            if r["status"] == "completed":
                return r
            if r["status"] in ("failed", "cancelled", "timeout", "deleted"):
                raise HelperError("WaveSpeed task {}: {}".format(r["status"], r.get("error")))
            return None
        r = poll(check, t, iv)
        return r.get("outputs", []), {"id": pid}

    if provider == "kie":
        if resp.get("code") not in (None, 200):
            raise HelperError("Kie error: " + json.dumps(resp))
        tid = resp["data"]["taskId"]

        def check():
            r = http.json("GET", "{}/jobs/recordInfo?taskId={}".format(base, tid))
            if r.get("code") not in (None, 200):
                raise HelperError("Kie error: " + json.dumps(r))
            d = r["data"]
            if d["state"] == "success":
                return d
            if d["state"] == "fail":
                raise HelperError("Kie task failed: {}".format(d.get("failMsg") or d))
            return None
        d = poll(check, t, iv)
        result = json.loads(d["resultJson"]) if isinstance(d.get("resultJson"), str) else d.get("resultJson", {})
        return result.get("resultUrls", []), {"taskId": tid}

    if provider == "evolink":
        tid = resp["id"]

        def check():
            r = http.json("GET", "{}/tasks/{}".format(base, tid))
            if r["status"] == "completed":
                return r
            if r["status"] == "failed":
                raise HelperError("Evolink task failed: {}".format(r.get("error") or r))
            return None
        r = poll(check, t, iv)
        return [x if isinstance(x, str) else x.get("url") for x in r.get("results", [])], {"id": tid}

    if provider == "fal":
        status_url, response_url = resp["status_url"], resp["response_url"]

        def check():
            r = http.json("GET", status_url)
            if r["status"] == "COMPLETED":
                return http.json("GET", response_url)
            if r["status"] not in ("IN_QUEUE", "IN_PROGRESS"):
                raise HelperError("fal request status: {}".format(r))
            return None
        r = poll(check, t, iv)
        meta = {"request_id": resp.get("request_id"), "seed": r.get("seed")}
        if r.get("layers"):           # v5.5/layerize: convert to the ModelArk layer shape
            items = []
            for l in r["layers"]:
                img = l.get("image") or {}
                d = {k: l.get(k) for k in ("z_index", "bounding_box", "name", "description", "text_recognition")}
                d["url"] = img.get("url")
                d["size"] = "{}x{}".format(img.get("width") or 0, img.get("height") or 0)
                d["background"] = "opaque" if l.get("z_index") == 0 else "transparent"
                items.append(d)
            meta["_layer_items"] = items
        return [i["url"] for i in r.get("images", [])], meta

    if provider == "replicate":
        def done(r):
            if r["status"] == "succeeded":
                return r
            if r["status"] in ("failed", "canceled"):
                raise HelperError("Replicate prediction {}: {}".format(r["status"], r.get("error")))
            return None
        r = done(resp) or poll(lambda: done(http.json("GET", resp["urls"]["get"])), t, iv)
        out = r["output"] if isinstance(r["output"], list) else [r["output"]]
        return out, {"id": r.get("id"), "metrics": r.get("metrics")}

    if provider == "openrouter":
        if resp.get("error"):
            raise HelperError("API error: " + json.dumps(resp["error"]))
        return [_b64(d["b64_json"]) if d.get("b64_json") else d.get("url") for d in resp.get("data", [])], \
            {k: v for k, v in resp.items() if k != "data"}

    raise HelperError("Unknown provider " + provider)


def make_http(provider, key):
    if provider == "fal":
        return Http(key, auth_prefix="Key ")
    return Http(key)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_providers(_args):
    print("{:<11} {:<20} {:<5} {}".format("provider", "key env var", "live", "default model / notes"))
    for name, p in PROVIDERS.items():
        print("{:<11} {:<20} {:<5} {}\n{:<38}{}".format(
            name, p["env"], "yes" if p["live"] else "no", p["model"], "", p["note"]))
    print("\n'live' = verified against the real API by the maintainers. Others follow each "
          "platform's published docs and are covered by offline mock tests.")
    return 0


def cmd_models(args):
    if args.provider not in ("byteplus", "volcengine"):
        print("Model listing is only available for byteplus / volcengine. Default for {}: {}"
              .format(args.provider, PROVIDERS[args.provider]["model"]))
        return 0
    key = get_key(args.provider)
    base = (args.base_url or PROVIDERS[args.provider]["base"]).rstrip("/")
    resp = Http(key).json("GET", base + "/models")
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


def build_spec(args):
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    else:
        prompt = (args.prompt or "").strip()
    if not prompt:
        raise HelperError("Give --prompt or --prompt-file.")
    style_file = getattr(args, "style", None)
    if style_file:
        with open(style_file, "r", encoding="utf-8") as f:
            style = f.read().strip()
        if style:
            prompt = prompt + "\n\nHouse style for this project: " + style
    p = PROVIDERS[args.provider]
    images, records = [], []
    for ref in args.image or []:
        value, record = load_image(ref, p["inline_images"])
        images.append(value)
        records.append(record)
    output_format = args.output_format
    if args.background == "transparent":
        if output_format not in (None, "png"):
            raise HelperError("A transparent background needs --output-format png.")
        output_format = "png"      # several platforms default to JPEG, which has no alpha
    model = args.model or (p.get("edit_model") if images and p.get("edit_model") else p["model"])
    max_refs = 14 if is_legacy(model) else 10
    if len(images) > max_refs:
        raise HelperError("Too many reference images for {} (max {}).".format(model, max_refs))
    layers = getattr(args, "layers", None)
    if getattr(args, "ocr", False) and layers is None:
        raise HelperError("--ocr only applies to --layers.")
    if layers is not None:
        if not re.search(r"5[-.]5", model):
            raise HelperError("--layers needs a Seedream 5.5 model (got {}).".format(model))
        if args.provider not in ("byteplus", "volcengine", "fal"):
            raise HelperError("--layers is wired for byteplus, volcengine and fal. On {} pass that platform's own "
                              "layer fields with --extra (see references/providers.md).".format(args.provider))
        if len(images) != 1:
            raise HelperError("--layers splits exactly one image: pass it with a single --image.")
        if not 2 <= layers <= 100:
            raise HelperError("--layers takes 2-100 (each returned layer is a billed image).")
        if args.background:
            raise HelperError("--layers cannot be combined with --background; layers are already transparent.")
        if getattr(args, "count", 1) > 1:
            raise HelperError("--layers cannot be combined with --count.")
        if args.size and not re.fullmatch(r"(1|1\.5|2)[kK]", args.size.strip()):
            raise HelperError("--layers takes a size tier (1K, 1.5K or 2K), not {}; the layers follow the "
                              "input's shape. Use export.py layers --original to get the exact size back.".format(args.size))
    size = args.size or ("2K" if layers is not None else "16:9")    # a tier lets layers follow the input's shape
    spec = {"model": model, "prompt": prompt, "size": parse_size(size, model), "images": images,
            "background": args.background, "output_format": output_format,
            "watermark": args.watermark, "layers": layers,
            "layers_ocr": bool(getattr(args, "ocr", False))}
    return spec, records


def apply_extra(body, extra_json):
    if not extra_json:
        return body
    try:
        extra = json.loads(extra_json)
    except ValueError as e:
        raise HelperError("--extra must be a JSON object: {}".format(e))
    if not isinstance(extra, dict):
        raise HelperError("--extra must be a JSON object.")
    target = body[0] if isinstance(body, list) else body.get("input", body)
    for reserved in ("prompt", "positivePrompt", "image", "images", "image_urls", "image_input",
                     "inputs", "input_references", "referenceImages"):
        if reserved in extra:
            raise HelperError("Set '{}' with its own flag (--prompt / --image), not --extra.".format(reserved))
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(target.get(k), dict):
            target[k].update(v)
        else:
            target[k] = v
    return body


def summarise_body(body, records):
    """Copy of the request body with inline image data replaced by sidecar records."""
    text = json.dumps(body)
    text = re.sub(r'"data:[^"]{64,}"', '"<inline image>"', text)
    shown = json.loads(text)
    return {"request": shown, "reference_images": records}


def unique_path(out_dir, stem, ext):
    path = os.path.join(out_dir, stem + ext)
    n = 2
    while os.path.exists(path) or os.path.exists(os.path.splitext(path)[0] + ".txt"):
        path = os.path.join(out_dir, "{}_{}{}".format(stem, n, ext))
        n += 1
    return path


def final_model(request, spec):
    """The model actually sent (after --extra), not just the one we started with."""
    if isinstance(request, list) and request:
        return request[0].get("model", spec["model"])
    if isinstance(request, dict):
        return request.get("model", spec["model"])
    return spec["model"]


def write_sidecar(path, provider, spec, summary, index, total, meta):
    lines = [
        "# Seedream generation record",
        "created: " + _now(),
        "image: {} ({} of {})".format(os.path.basename(path), index + 1, total),
        "provider: " + provider,
        "model: " + str(final_model(summary["request"], spec)),
        "",
        "## prompt",
        spec["prompt"],
        "",
        "## request (inline images summarised)",
        json.dumps(summary["request"], indent=2, ensure_ascii=False),
        "",
        "## reference images (in order: Image 1, Image 2, ...)",
        json.dumps(summary["reference_images"], indent=2, ensure_ascii=False) if summary["reference_images"] else "none",
        "",
        "## response metadata",
        json.dumps(meta, indent=2, ensure_ascii=False, default=str),
        "",
    ]
    records = getattr(_RECORDS, "dir", None)
    if records:
        os.makedirs(records, exist_ok=True)
        txt = os.path.join(records, os.path.splitext(os.path.basename(path))[0] + ".txt")
    else:
        txt = os.path.splitext(path)[0] + ".txt"
    with open(txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return txt


_RECORDS = __import__("threading").local()     # batch sets .dir per worker thread


PRICES_USD = {     # per generated image, BytePlus ModelArk list price, November 2026 (references/providers.md)
    "byteplus": {"2K": 0.035, "1.5K": 0.020, "input": 0.008},
}


def estimate_cost(provider, spec, n_images=1):
    """Rough USD estimate, or None where we don't track the platform's price."""
    table = PRICES_USD.get(provider)
    if not table or not re.search(r"5[-.]5", spec["model"]):
        return None
    kind, val = spec["size"]
    area = val[0] * val[1] if kind == "wh" else {"1K": 1048576, "1.5K": 2359296}.get(val, 4194304)
    per = table["1.5K"] if area <= 2359296 else table["2K"]
    inputs = table["input"] * len(spec["images"])
    if spec.get("layers"):                       # one call, billed per returned layer (up to N)
        return round(per * spec["layers"] + inputs, 4)
    return round(n_images * (per + inputs), 4)   # --count makes separate calls, each re-sends the inputs


def ledger_add(out_dir, record):
    """Append one line per paid call to <out>/.seedream-ledger.jsonl (no prompts, no keys)."""
    try:
        out_dir = getattr(_RECORDS, "ledger", None) or out_dir
        with _SAVE_LOCK:
            with open(os.path.join(out_dir, ".seedream-ledger.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
    except OSError:
        pass


def _export_module():
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import export
    return export


def _check_wh(value):
    m = re.fullmatch(r"\s*(\d+)\s*[xX*]\s*(\d+)\s*", str(value))
    if not m or not (16 <= int(m.group(1)) <= 8192 and 16 <= int(m.group(2)) <= 8192):
        raise HelperError("final size must look like 1200x630 (got {!r}).".format(value))
    return int(m.group(1)), int(m.group(2))


def finalize_size(path, final_size, fit):
    """Resize a saved image to an exact WxH next to it (needs Pillow). Returns the new path."""
    try:
        _ex = _export_module()
        from PIL import Image
    except ImportError:
        warn("--final-size needs Pillow (pip install pillow); kept the original size.")
        return None
    w, h = _check_wh(final_size)
    src = Image.open(path)
    src = src.convert("RGBA") if src.mode in ("RGBA", "LA", "P") else src.convert("RGB")
    if fit == "pad":
        im, scale = _ex.contain_pad(Image, src, w, h, (0, 0, 0, 0) if src.mode == "RGBA" else (255, 255, 255), "center")
    else:
        im, scale = _ex.cover_crop(Image, src, w, h, "center")
    stem, ext = os.path.splitext(path)
    out = unique_path(os.path.dirname(path) or ".", "{}_{}x{}".format(os.path.basename(stem), w, h), ext)
    im.save(out)
    print("final size: {}  ({}x{}, {})".format(out, w, h, fit))
    return out


def cmd_generate(args):
    provider = args.provider
    spec, records = build_spec(args)
    base = (args.base_url or PROVIDERS[provider]["base"]).rstrip("/")
    url, body = BUILDERS[provider](spec, base)
    body = apply_extra(body, args.extra)
    summary = summarise_body(body, records)

    if getattr(args, "final_size", None):
        _check_wh(args.final_size)
    est = estimate_cost(provider, spec, max(1, getattr(args, "count", 1) or 1))
    if args.dry_run:
        print(json.dumps({"provider": provider, "url": url, **summary,
                          "estimated_cost_usd": est if est is not None else "unknown for this platform; check its pricing page"},
                         indent=2, ensure_ascii=False))
        return 0

    key = get_key(provider)
    os.makedirs(args.out, exist_ok=True)
    stem = args.name or _dt.datetime.now().strftime("seedream_%Y%m%d_%H%M%S")
    count = max(1, args.count)
    if count > 8:
        raise HelperError("--count is capped at 8 per call (each one is a billed image).")

    def one(index):
        """One full request -> saved files. Each option is its own API call."""
        http = make_http(provider, key)
        headers = {"Prefer": "wait=60"} if provider == "replicate" else None
        call_body = apply_extra(BUILDERS[provider](spec, base)[1], args.extra) if count > 1 else body
        resp = None
        try:
            resp = http.json("POST", url, call_body, headers=headers, timeout=args.timeout)
            refs, meta = collect(provider, http, resp, base, args)
        except HelperError as e:
            raise HelperError(scrub(str(e), key))
        except (KeyError, TypeError, IndexError, AttributeError, ValueError) as e:
            raise HelperError(scrub("Unexpected response shape from {} ({}: {}). Response: {}".format(
                provider, type(e).__name__, e, json.dumps(resp)[:1500]), key))
        layer_resp = None
        if spec.get("layers") and isinstance(meta, dict) and meta.get("_layer_items"):
            layer_resp = {"data": meta.pop("_layer_items")}
        elif spec.get("layers") and isinstance(resp, dict) and any(
                isinstance(d, dict) and "z_index" in d for d in resp.get("data", [])):
            layer_resp = resp
        if layer_resp is not None:
            files = save_layers(args.out, stem, layer_resp, provider, spec, summary, meta)
            n = (meta.get("usage") or {}).get("generated_images") or len(files)
            ledger_add(args.out, {"time": _now(),
                                  "provider": provider, "model": final_model(summary["request"], spec),
                                  "file": os.path.basename(os.path.dirname(files[0])) if files else stem,
                                  "images": n, "inputs": len(spec["images"]),
                                  "est_usd": estimate_cost(provider, dict(spec, layers=n))})
            return files
        refs = [r for r in (refs or []) if isinstance(r, str) and r]
        if not refs:
            raise HelperError(scrub("No images in response: " + json.dumps(resp)[:2000], key))
        paths = []
        for i, ref in enumerate(refs):
            raw = base64.b64decode(ref.split(",", 1)[1]) if ref.startswith("data:") else download(ref)
            name = stem
            if count > 1:
                name = "{}_{}".format(stem, index + 1)
            if len(refs) > 1:
                name = "{}_{}".format(name, i + 1)
            with _SAVE_LOCK:
                path = unique_path(args.out, name, ext_for(raw))
                with open(path, "wb") as f:
                    f.write(raw)
            txt = write_sidecar(path, provider, spec, summary, i, len(refs), meta)
            print("saved {}  (+ {})".format(path, os.path.basename(txt)))
            paths.append(path)
            if getattr(args, "final_size", None):
                fin = finalize_size(path, args.final_size, getattr(args, "fit", "crop") or "crop")
                if fin:
                    paths.append(fin)
        usage = meta.get("usage") if isinstance(meta, dict) else None
        ledger_add(args.out, {"time": _now(),
                              "provider": provider, "model": final_model(summary["request"], spec),
                              "file": os.path.basename(paths[0]),
                              "images": (usage or {}).get("generated_images") or len(refs),
                              "inputs": len(spec["images"]),
                              "est_usd": estimate_cost(provider, spec, (usage or {}).get("generated_images") or len(refs))})
        return paths

    if count == 1:
        args._saved = one(0) or []
        return 0 if args._saved else 1

    from concurrent.futures import ThreadPoolExecutor
    saved, errors = [], []
    with ThreadPoolExecutor(max_workers=min(count, 4)) as pool:
        futures = [pool.submit(one, i) for i in range(count)]
        for i, fut in enumerate(futures):
            try:
                saved.extend(fut.result())
            except HelperError as e:
                errors.append("option {}: {}".format(i + 1, e))
    for e in errors:
        print("error: " + e, file=sys.stderr)
    args._saved = saved
    if saved:
        sheet = write_contact_sheet(args.out, stem, saved, spec)
        print("contact sheet: {}  ({} of {} options)".format(sheet, len(saved), count))
    return 0 if saved else 1


_SAVE_LOCK = __import__("threading").Lock()


def _slug(text, fallback):
    text = re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_").lower()[:40]
    return text if re.search(r"[a-z]", text) else fallback


def save_layers(out_dir, stem, resp, provider, spec, summary, meta):
    """Layer decomposition: one PNG per layer, a manifest, and an interactive HTML layer viewer."""
    folder = unique_path(out_dir, stem + "_layers", "")
    os.makedirs(folder)
    items = sorted((d for d in resp.get("data", []) if isinstance(d, dict) and not d.get("error")),
                   key=lambda d: d.get("z_index", 0))
    layers, canvas = [], None
    for d in items:
        z = d.get("z_index", len(layers))
        if not (d.get("b64_json") or d.get("url")):
            warn("layer {} came back without image data; skipped.".format(z))
            continue
        raw = base64.b64decode(d["b64_json"]) if d.get("b64_json") else download(d["url"])
        name = d.get("name") or ("base" if z == 0 else "layer {}".format(z))
        tr = d.get("text_recognition") or {}
        slug = _slug(tr.get("text"), "") or _slug(name, "base" if z == 0 else "layer")
        path = unique_path(folder, "{:02d}_{}".format(z, slug), ".png")     # equal z_index never overwrites
        fname = os.path.basename(path)
        with open(path, "wb") as f:
            f.write(raw)
        try:
            size = [int(v) for v in str(d.get("size", "0x0")).split("x")]
        except ValueError:
            size = [0, 0]
        box = (d.get("bounding_box") or {}).get("absolute")
        if z == 0:
            box = box or [0, 0, size[0], size[1]]
            canvas = canvas or [box[2], box[3]]
        elif box is None:
            box = [0, 0, canvas[0], canvas[1]] if canvas else [0, 0, size[0], size[1]]
        layers.append({"z_index": z, "file": fname, "name": name, "description": d.get("description"),
                       "box": box, "box_normalized": (d.get("bounding_box") or {}).get("normalized"),
                       "pixel_size": size, "background": d.get("background"),
                       "text": tr.get("text"), "text_lines": tr.get("lines")})
    if not layers:
        raise HelperError("The layer response contained no images.")
    canvas = canvas or [max(l["box"][2] for l in layers), max(l["box"][3] for l in layers)]
    manifest = {"canvas": canvas, "model": final_model(summary["request"], spec), "provider": provider,
                "prompt": spec["prompt"], "reference_images": summary["reference_images"],
                "usage": meta.get("usage"), "layers": layers,
                "note": "Each layer PNG is a high-resolution crop. Scale it to 'box' ([x1, y1, x2, y2] in canvas "
                        "pixels) and place it there; layer 0 is the opaque background plate."}
    with open(os.path.join(folder, "layers.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    viewer = write_layer_viewer(folder, stem, manifest)
    print("saved {} layers in {}  (+ layers.json, {})".format(len(layers), folder, os.path.basename(viewer)))
    usage = meta.get("usage") or {}
    if usage.get("generated_images"):
        print("billed images: {}".format(usage["generated_images"]))
    return [os.path.join(folder, l["file"]) for l in layers]


def write_layer_viewer(folder, stem, manifest):
    """Self-contained page: toggle, solo, fade and drag layers; read OCR text and font guesses."""
    data = json.dumps(manifest, ensure_ascii=False).replace("<", "\\u003c")
    page = """<!doctype html><meta charset="utf-8"><title>%s layers</title>
<style>body{margin:0;display:flex;font:13px system-ui,sans-serif;background:#141414;color:#ddd;height:100vh}
#stage{flex:1;overflow:auto;display:flex;align-items:center;justify-content:center;
background:repeating-conic-gradient(#2a2a2a 0 25%%,#202020 0 50%%) 0 0/24px 24px}
#canvas{position:relative;box-shadow:0 0 0 1px #444}#canvas img{position:absolute;cursor:move;user-select:none}
#canvas img.sel{outline:2px solid #3DDC97}aside{width:340px;overflow:auto;border-left:1px solid #333;padding:12px}
.row{display:flex;gap:6px;align-items:center;padding:6px;border-radius:6px}.row:hover,.row.sel{background:#222}
.row b{flex:1;font-weight:500}.row small{color:#888;display:block}button{background:#2b2b2b;color:#ddd;
border:1px solid #444;border-radius:4px;padding:2px 6px;cursor:pointer}pre{white-space:pre-wrap;color:#aaa}</style>
<div id="stage"><div id="canvas"></div></div><aside><h3>%s</h3>
<p>Click a layer to select. Drag to move. Eye toggles; S solos. Positions are canvas pixels.</p>
<p>Check edges on: <button data-bg="checker">checker</button> <button data-bg="#00b140">green</button>
<button data-bg="#000">black</button> <button data-bg="#fff">white</button></p>
<div id="list"></div><pre id="info"></pre></aside>
<script>const M=%s;const cv=document.getElementById('canvas'),list=document.getElementById('list'),info=document.getElementById('info');
const W=M.canvas[0],H=M.canvas[1];let k=Math.max(0.05,Math.min((innerWidth-380)/W,(innerHeight-40)/H,1));
cv.style.width=W*k+'px';cv.style.height=H*k+'px';const els=[];
function place(e,l){const[b1,b2,b3,b4]=l.box;e.style.left=b1*k+'px';e.style.top=b2*k+'px';e.style.width=(b3-b1)*k+'px';e.style.height=(b4-b2)*k+'px'}
function sel(i){els.forEach((e,j)=>{e.img.classList.toggle('sel',i===j);e.row.classList.toggle('sel',i===j)});
const l=M.layers[i];info.textContent=JSON.stringify({name:l.name,box:l.box,text:l.text,font:l.text_lines&&l.text_lines.map(x=>x.runs.map(r=>r.style))},null,1)}
M.layers.forEach((l,i)=>{const img=new Image();img.src=l.file;img.style.zIndex=l.z_index;place(img,l);cv.appendChild(img);
const row=document.createElement('div');row.className='row';row.innerHTML='<button class=e>&#128065;</button><button class=s>S</button><b>'+
(l.text?'&#8220;'+l.text.replace(/</g,'&lt;')+'&#8221;':(l.name||'').replace(/</g,'&lt;'))+'<small>z '+l.z_index+' &middot; '+l.file+'</small></b>';
list.prepend(row);els.push({img,row});
row.querySelector('.e').onclick=ev=>{ev.stopPropagation();img.style.display=img.style.display==='none'?'':'none'};
row.querySelector('.s').onclick=ev=>{ev.stopPropagation();const solo=els.every((x,j)=>j===i||x.img.style.display==='none');
els.forEach((x,j)=>x.img.style.display=(solo||j===i)?'':'none')};row.onclick=()=>sel(i);
img.onpointerdown=ev=>{if(l.z_index===0)return;sel(i);ev.preventDefault();const sx=ev.clientX,sy=ev.clientY,b=l.box.slice();
img.setPointerCapture(ev.pointerId);img.onpointermove=m=>{const dx=Math.round((m.clientX-sx)/k),dy=Math.round((m.clientY-sy)/k);
l.box=[b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy];place(img,l);sel(i)};img.onpointerup=()=>img.onpointermove=null}});
document.querySelectorAll('[data-bg]').forEach(bt=>bt.onclick=()=>{const v=bt.dataset.bg;const st=document.getElementById('stage');
st.style.background=v==='checker'?'':v;});</script>
""" % (html_escape(stem), html_escape(stem), data)
    path = os.path.join(folder, "viewer.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


def html_escape(text):
    import html
    return html.escape(str(text))


def write_contact_sheet(out_dir, stem, paths, spec):
    """A self-contained HTML page showing all options side by side (no dependencies)."""
    import html
    cards = "\n".join(
        '<figure><a href="{0}"><img src="{0}" loading="lazy"></a><figcaption>{1}</figcaption></figure>'.format(
            html.escape(os.path.relpath(p, out_dir).replace(os.sep, "/")), html.escape(os.path.basename(p))) for p in paths)
    page = """<!doctype html><meta charset="utf-8"><title>{t}</title>
<style>body{{font:14px system-ui,sans-serif;margin:24px;background:#111;color:#ddd}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}
img{{width:100%;border-radius:8px;background:repeating-conic-gradient(#333 0 25%,#222 0 50%) 0 0/20px 20px}}
figure{{margin:0}}figcaption{{padding:6px 2px;color:#aaa}}pre{{white-space:pre-wrap;background:#1b1b1b;padding:12px;border-radius:8px}}</style>
<h1>{t}</h1><p>{n} options &middot; model {m}</p><div class="grid">{c}</div><h2>Prompt</h2><pre>{p}</pre>""".format(
        t=html.escape(stem), n=len(paths), m=html.escape(spec["model"]), c=cards, p=html.escape(spec["prompt"]))
    path = unique_path(out_dir, stem + "_sheet", ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


# --------------------------------------------------------------------------- #

def _load_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith((".yaml", ".yml")):
        try:
            import yaml
        except ImportError:
            raise HelperError("A YAML manifest needs PyYAML (pip install pyyaml), or write it as JSON.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("assets"), list):
        raise HelperError("The manifest needs an 'assets' list.")
    return data


def _asset_hash(fields):
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode("utf-8")).hexdigest()[:16]


_RESERVED = {"con", "prn", "aux", "nul"} | {"com%d" % i for i in range(1, 10)} | {"lpt%d" % i for i in range(1, 10)}


def _project_root(manifest_path, man):
    """Relative paths in a manifest are relative to the project root: the manifest's folder, or
    its parent when the manifest sits in .seedream/. A "root" key overrides this."""
    mdir = os.path.dirname(os.path.abspath(manifest_path))
    if man.get("root"):
        return os.path.normpath(os.path.join(mdir, man["root"]))
    return os.path.dirname(mdir) if os.path.basename(mdir) == ".seedream" else mdir


def cmd_batch(args, gen_parser):
    """Generate every asset in a manifest with one shared style. Skips assets whose inputs haven't
    changed, shows the plan and cost before spending, and runs jobs in parallel."""
    man = _load_manifest(args.manifest)
    root = _project_root(args.manifest, man)
    rel = lambda q: q if (not q or os.path.isabs(q) or re.match(r"^(https?:|data:)", q)) else os.path.join(root, q)
    provider = args.provider or man.get("provider") or os.environ.get("SEEDREAM_PROVIDER", "byteplus")
    if provider not in PROVIDERS:
        raise HelperError("Unknown provider in manifest: {}".format(provider))
    out_dir = rel(man.get("out") or "seedream_out")
    style = man.get("style") or ""
    if man.get("style_file"):
        sf = rel(man["style_file"])
        if not os.path.isfile(sf):
            raise HelperError("style_file not found: {} (paths are relative to {})".format(man["style_file"], root))
        with open(sf, "r", encoding="utf-8") as f:
            style = (style + "\n" + f.read()).strip()
    defaults = man.get("defaults") or {}
    meta_dir = os.path.join(root, ".seedream")               # state, records, ledger, sheet: not in public/
    state_dir = os.path.join(meta_dir, "state")
    only = set(args.only.split(",")) if args.only else None
    names = [a.get("name") for a in man["assets"]]
    if only and only - set(names):
        warn("--only names not in the manifest: " + ", ".join(sorted(only - set(names))))
    try:
        presets = set(_export_module().PRESETS)
    except ImportError:
        presets = set()

    plan, seen = [], set()
    needs_pillow = False
    for a in man["assets"]:
        name = a.get("name") or ""
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or name.strip(".") == ""
                or name.split(".")[0].lower() in _RESERVED):
            raise HelperError("Asset names must start with a letter or digit and use only letters, digits, "
                              "'.', '_' or '-' (got {!r}).".format(name))
        if name in seen:
            raise HelperError("Duplicate asset name: " + name)
        seen.add(name)
        if only and name not in only:
            continue
        cfg = dict(defaults, **a)
        prompt = (cfg.get("prompt") or "").strip()
        if not prompt:
            raise HelperError("Asset {} has no prompt.".format(name))
        full_prompt = prompt + ("\n\nHouse style for this project: " + style
                                if style and cfg.get("style", True) is not False else "")
        images = cfg.get("image") or []
        images = [rel(i) for i in ([images] if isinstance(images, str) else images)]
        asset_out = rel(cfg["out"]) if cfg.get("out") else out_dir
        exports = cfg.get("export") or []
        bad = [e for e in exports if e not in presets]
        if bad:
            raise HelperError("Asset {}: unknown export preset(s) {} (see export.py presets).".format(name, ", ".join(bad)))
        if cfg.get("final_size"):
            _check_wh(cfg["final_size"])
        needs_pillow = needs_pillow or bool(exports or cfg.get("final_size"))
        argv = ["--provider", provider, "--prompt", full_prompt, "--out", asset_out, "--name", name]
        model = cfg.get("model") or man.get("model")
        for flag, val in (("--size", cfg.get("size")), ("--background", cfg.get("background")),
                          ("--output-format", cfg.get("output_format")), ("--final-size", cfg.get("final_size")),
                          ("--fit", cfg.get("fit")), ("--model", model)):
            if val:
                argv += [flag, str(val)]
        if args.base_url:
            argv += ["--base-url", args.base_url]
        for i in images:
            argv += ["--image", i]
        gargs = gen_parser.parse_args(argv)
        gargs.poll_interval = args.poll_interval
        spec, _ = build_spec(gargs)
        refs = []
        for i in images:
            if os.path.isfile(i):
                with open(i, "rb") as f:
                    refs.append(hashlib.sha256(f.read()).hexdigest()[:16])
            else:
                refs.append(i)
        h = _asset_hash({"p": provider, "m": spec["model"], "prompt": full_prompt, "size": spec["size"],
                         "bg": cfg.get("background"), "fmt": cfg.get("output_format"), "final": cfg.get("final_size"),
                         "fit": cfg.get("fit"), "refs": refs, "out": os.path.relpath(asset_out, root),
                         "export": sorted(exports)})
        state_path = os.path.join(state_dir, name + ".json")
        prev, fresh = None, False
        if os.path.isfile(state_path):
            try:
                with open(state_path, encoding="utf-8") as f:
                    prev = json.load(f)
                fresh = (not args.force and prev.get("hash") == h
                         and all(os.path.exists(os.path.join(root, x)) for x in prev.get("files", [])))
            except (OSError, ValueError):
                prev = None
        plan.append({"name": name, "args": gargs, "hash": h, "state": state_path, "fresh": fresh, "prev": prev,
                     "cost": estimate_cost(provider, spec), "export": exports})

    todo = [x for x in plan if not x["fresh"]]
    known = [x["cost"] for x in todo if x["cost"] is not None]
    total = round(sum(known), 3) if known else None
    print("batch: {} assets, {} up to date, {} to generate on {}".format(len(plan), len(plan) - len(todo), len(todo), provider))
    for x in plan:
        print("  {:<28} {}".format(x["name"], "up to date (skip)" if x["fresh"] else
                                   "generate  ~${}".format(x["cost"]) if x["cost"] is not None else "generate  (price unknown)"))
    if todo:
        print("estimated cost: {}".format("~${} for {} images".format(total, len(todo)) if total is not None and len(known) == len(todo)
                                          else "unknown for some assets on this platform"))
    if todo and needs_pillow:
        try:
            import PIL  # noqa: F401
        except ImportError:
            raise HelperError("final_size / export need Pillow (pip install pillow). Nothing was spent.")
    if args.dry_run or not todo:
        return 0
    if not args.yes:
        print("Nothing spent. Re-run with --yes to generate these {} images.".format(len(todo)))
        return 3

    os.makedirs(state_dir, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    for x in todo:      # move this asset's previous files aside, so the new ones keep the same names
        for old in (x["prev"] or {}).get("files", []):
            src = os.path.join(root, old)
            if os.path.isfile(src):
                dst = os.path.join(meta_dir, "replaced", stamp, old)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                os.replace(src, dst)

    from concurrent.futures import ThreadPoolExecutor
    results, errors = {}, []

    def run(x):
        _RECORDS.dir = os.path.join(meta_dir, "records")
        _RECORDS.ledger = meta_dir
        try:
            cmd_generate(x["args"])
            files = list(getattr(x["args"], "_saved", []) or [])
            if not files:
                raise HelperError("no image saved")
            relfiles = [os.path.relpath(f, root).replace(os.sep, "/") for f in files]
            want = os.path.splitext(os.path.basename(files[0]))[0]
            if want != x["name"]:
                warn("{0}: a file named {0} that this batch didn't make already exists in {1}, so the new image is "
                     "{2}. Move or delete the old file and re-run with --only {0} --force to take the name.".format(
                         x["name"], os.path.relpath(os.path.dirname(files[0]), root), os.path.basename(files[0])))

            def save_state():
                with open(x["state"], "w", encoding="utf-8") as f:
                    json.dump({"hash": x["hash"], "files": relfiles, "made": _now()}, f, indent=2)
            save_state()                                   # paid image recorded before any export step
            for preset in x["export"]:
                for e in _export_preset(files[0], preset):
                    files.append(e)
                    relfiles.append(os.path.relpath(e, root).replace(os.sep, "/"))
            save_state()
            return files
        except HelperError:
            raise
        except BaseException as e:                         # SystemExit from a helper must not kill the batch
            raise HelperError("{}: {}".format(type(e).__name__, e))

    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 8))) as pool:
        futs = {x["name"]: pool.submit(run, x) for x in todo}
        for name, fut in futs.items():
            try:
                results[name] = fut.result()
            except HelperError as e:
                errors.append("{}: {}".format(name, e))
    for e in errors:
        print("error: " + e, file=sys.stderr)
    shown = [fs[0] for fs in results.values() if fs]
    if shown:
        sheet = os.path.join(meta_dir, "batch_sheet.html")
        page = write_contact_sheet(meta_dir, "batch_tmp", shown,
                                   {"model": man.get("model") or PROVIDERS[provider]["model"],
                                    "prompt": "Style: " + (style or "(none)")})
        os.replace(page, sheet)
        print("batch sheet: {}".format(sheet))
    print("done: {} generated, {} failed, {} skipped".format(len(results), len(errors), len(plan) - len(todo)))
    return 0 if not errors else 1


def _export_preset(path, preset):
    """Crop one image to a named preset; returns the written path(s). Thread-safe (no folder diffing)."""
    ex = _export_module()
    from PIL import Image
    w, h, _note = ex.PRESETS[preset]
    with Image.open(path) as im:
        src = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    out, scale = ex.cover_crop(Image, src, w, h, "center")
    with _SAVE_LOCK:
        written = ex.save(out, path, preset, "op: cropped to {}x{} (gravity center)".format(w, h), None, None)
    return [written]


def cmd_costs(args):
    path = os.path.join(args.out, ".seedream-ledger.jsonl")
    if not os.path.isfile(path):
        print("No ledger at {} yet (it is written next to generated images).".format(path))
        return 0
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    by = {}
    for r in rows:
        k = (r.get("provider"), r.get("model"))
        c = by.setdefault(k, {"calls": 0, "images": 0, "usd": 0.0, "unknown": 0})
        c["calls"] += 1
        c["images"] += r.get("images") or 0
        if r.get("est_usd") is None:
            c["unknown"] += 1
        else:
            c["usd"] += r["est_usd"]
    for (prov, model), c in sorted(by.items(), key=lambda kv: str(kv[0])):
        print("{:<11} {:<36} {:>4} calls {:>5} images  ~${:.3f}{}".format(
            prov, model, c["calls"], c["images"], c["usd"], "  (+{} unpriced)".format(c["unknown"]) if c["unknown"] else ""))
    print("Estimates from list prices; your invoice is the source of truth.")
    return 0


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--provider", default=os.environ.get("SEEDREAM_PROVIDER", "byteplus"),
                        choices=sorted(PROVIDERS),
                        help="API platform (default: %(default)s; env SEEDREAM_PROVIDER)")
    common.add_argument("--base-url", default=os.environ.get("SEEDREAM_BASE_URL"),
                        help="Override the provider's API base URL (env SEEDREAM_BASE_URL)")

    p = argparse.ArgumentParser(description="Key-safe Seedream helper for many API platforms.")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("providers", help="List supported platforms and their key variables.")

    pm = sub.add_parser("models", parents=[common],
                        help="List Seedream models visible to your key (byteplus/volcengine).")
    pm.add_argument("--filter", default="seedream", help="Substring filter (default: seedream).")
    pm.add_argument("--json", action="store_true", help="Print full JSON records.")

    pg = sub.add_parser("generate", parents=[common], help="Generate or edit an image.")
    src = pg.add_mutually_exclusive_group()
    src.add_argument("--prompt")
    src.add_argument("--prompt-file", help="UTF-8 text file holding the prompt.")
    pg.add_argument("--size", default=None,
                    help="Ratio ({}), tier (1K, 1.5K, 2K) or WxH with {:,}-{:,} px. Default 16:9 (2K with --layers).".format(
                        ", ".join(SIZE_PRESETS), MIN_AREA, MAX_AREA))
    pg.add_argument("--image", action="append",
                    help="Reference image: local path, URL or data URI. Repeat (max 10); "
                         "order = Image 1, Image 2, ...")
    pg.add_argument("--model", default=os.environ.get("SEEDREAM_MODEL"),
                    help="Model ID (default: the provider's Seedream default; env SEEDREAM_MODEL)")
    pg.add_argument("--background", choices=["auto", "transparent", "opaque"],
                    help="Seedream 5.5: transparent PNG output (needs png).")
    pg.add_argument("--output-format", choices=["png", "jpeg"])
    pg.add_argument("--watermark", action="store_true",
                    help="Keep the provider's AI watermark (off by default where configurable).")
    pg.add_argument("--layers", type=int, metavar="N",
                    help="Seedream 5.5 (byteplus, volcengine, fal): split the one --image into up to N editable layers (2-100; each "
                         "returned layer is billed). Saves PNGs, layers.json and an HTML layer viewer.")
    pg.add_argument("--ocr", action="store_true",
                    help="With --layers: read the text, font guess and colour of text layers.")
    pg.add_argument("--style", metavar="FILE",
                    help="A project style file (e.g. .seedream/style.md) appended to every prompt for a consistent look.")
    pg.add_argument("--final-size", metavar="WxH",
                    help="Also save an exact-size copy (e.g. 1200x630, 512x512); Seedream's own sizes have a minimum area. Needs Pillow.")
    pg.add_argument("--fit", choices=["crop", "pad"], default="crop", help="How --final-size fits: crop (default) or pad.")
    pg.add_argument("--extra", help="JSON object merged into the request body (provider-specific fields).")
    pg.add_argument("--out", default="seedream_out", help="Output folder (default: %(default)s)")
    pg.add_argument("--name", help="File stem; a suffix is added rather than overwrite.")
    pg.add_argument("--count", type=int, default=1,
                    help="Generate N options in parallel (max 8; each is a billed image) plus an HTML contact sheet.")
    pg.add_argument("--timeout", type=int, default=300)
    pg.add_argument("--poll-interval", type=float, default=2.0, help=argparse.SUPPRESS)
    pg.add_argument("--dry-run", action="store_true",
                    help="Print the request (images summarised) and exit. No key needed.")

    pb = sub.add_parser("batch", help="Generate every asset in a JSON/YAML manifest with one shared style.")
    pb.add_argument("manifest")
    pb.add_argument("--provider", choices=sorted(PROVIDERS), help="Overrides the manifest's provider.")
    pb.add_argument("--base-url", default=os.environ.get("SEEDREAM_BASE_URL"))
    pb.add_argument("--yes", action="store_true", help="Spend: without it, batch only prints the plan and the cost.")
    pb.add_argument("--dry-run", action="store_true", help="Print the plan and the estimated cost; no key needed.")
    pb.add_argument("--force", action="store_true", help="Regenerate assets even if they are up to date.")
    pb.add_argument("--only", help="Comma-separated asset names to run.")
    pb.add_argument("--jobs", type=int, default=3, help="Parallel requests (default 3, max 8).")
    pb.add_argument("--poll-interval", type=float, default=2.0, help=argparse.SUPPRESS)

    pc = sub.add_parser("costs", help="Summarise the cost ledger written next to generated images.")
    pc.add_argument("--out", default="seedream_out", help="Folder holding .seedream-ledger.jsonl")

    for stream in (sys.stdout, sys.stderr):      # Windows consoles default to a legacy codepage
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = p.parse_args(argv)
    try:
        if args.cmd == "providers":
            return cmd_providers(args)
        if args.cmd == "models":
            return cmd_models(args)
        if args.cmd == "generate":
            return cmd_generate(args)
        if args.cmd == "batch":
            return cmd_batch(args, pg)
        if args.cmd == "costs":
            return cmd_costs(args)
        p.print_help()
        return 2
    except HelperError as e:
        print("error: " + str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
