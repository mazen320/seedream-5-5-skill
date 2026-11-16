#!/usr/bin/env python3
"""Export a generated image for where it will be used: crop/resize to platform sizes,
pad instead of crop, or mirror-flip a detail that landed on the wrong side.

Requires Pillow (`pip install pillow`). The generator script itself needs nothing extra.

    python export.py presets
    python export.py out/poster.png --to instagram-post --to story
    python export.py out/poster.png --to instagram-post --fit pad --pad-color "#f4efe6"
    python export.py out/captain.png --flip                      # mirror horizontally
    python export.py out/hero.png --size 1600x900 --gravity top  # any custom size
    python export.py merge original.jpg edited.png               # keep untouched pixels original
    python export.py layers out/poster_layers                     # stack, SVG for Figma, check vs source
    python export.py split out/icons.png --names sun,cloud,rain   # cut a transparent sheet into assets
    python export.py icons out/logo.png --out public/icons         # favicons, PWA, iOS, Android + HTML tags

Every export is written next to the source as <name>_<preset>.<ext> with a small
.txt sidecar saying how it was derived. Sources are never overwritten.
"""

import argparse
import json
import os
import sys

PRESETS = {
    # name: (width, height, note)
    "instagram-post": (1080, 1350, "Instagram feed portrait, 4:5 (tallest the feed shows)"),
    "instagram-square": (1080, 1080, "Instagram feed square, 1:1"),
    "story": (1080, 1920, "Instagram / TikTok / Reels / Shorts, 9:16"),
    "youtube-thumb": (1280, 720, "YouTube thumbnail, 16:9"),
    "x-post": (1600, 900, "X / Twitter in-feed image, 16:9"),
    "linkedin": (1200, 627, "LinkedIn link/feed image, ~1.91:1"),
    "facebook": (1200, 630, "Facebook / Open Graph share image, ~1.91:1"),
    "pinterest": (1000, 1500, "Pinterest pin, 2:3"),
    "a4-300dpi": (2480, 3508, "A4 portrait at 300 dpi (needs upscaling from 2K)"),
    "a5-300dpi": (1748, 2480, "A5 portrait at 300 dpi"),
    "desktop": (2560, 1440, "Desktop wallpaper, 16:9"),
    "phone-wallpaper": (1290, 2796, "Phone wallpaper, ~9:19.5"),
    "og": (1200, 630, "Open Graph / link preview (Slack, LinkedIn, Facebook, iMessage)"),
    "x-card": (1200, 628, "X summary_large_image card"),
    "appstore-iphone-6.9": (1320, 2868, "App Store screenshot, iPhone 6.9-inch"),
    "appstore-iphone-6.5": (1284, 2778, "App Store screenshot, iPhone 6.5-inch"),
    "appstore-ipad-13": (2064, 2752, "App Store screenshot, iPad 13-inch"),
    "play-feature": (1024, 500, "Google Play feature graphic"),
    "steam-capsule": (616, 353, "Steam main capsule"),
    "steam-header": (920, 430, "Steam header capsule"),
}

GRAVITY = {"center": (0.5, 0.5), "top": (0.5, 0.0), "bottom": (0.5, 1.0),
           "left": (0.0, 0.5), "right": (1.0, 0.5)}


def need_pillow():
    try:
        from PIL import Image  # noqa: F401
        return Image
    except ImportError:
        sys.exit("error: export needs Pillow. Install it with:  pip install pillow")


def parse_wh(s):
    try:
        w, h = s.lower().replace("*", "x").split("x")
        return int(w), int(h)
    except ValueError:
        sys.exit("error: --size must look like 1600x900")


def hex_color(s, mode):
    if s.lower() == "transparent":
        return (0, 0, 0, 0)
    s = s.lstrip("#")
    if len(s) != 6:
        sys.exit("error: --pad-color must be #rrggbb or 'transparent'")
    rgb = tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    return rgb + (255,) if mode == "RGBA" else rgb


def cover_crop(Image, im, w, h, gravity):
    """Scale to cover w x h, then crop the overflow according to gravity."""
    scale = max(w / im.width, h / im.height)
    rw, rh = max(w, round(im.width * scale)), max(h, round(im.height * scale))
    im = im.resize((rw, rh), Image.LANCZOS)
    gx, gy = GRAVITY[gravity]
    left, top = round((rw - w) * gx), round((rh - h) * gy)
    return im.crop((left, top, left + w, top + h)), scale


def contain_pad(Image, im, w, h, color, gravity):
    """Scale to fit inside w x h and pad the rest."""
    scale = min(w / im.width, h / im.height)
    rw, rh = round(im.width * scale), round(im.height * scale)
    im2 = im.resize((rw, rh), Image.LANCZOS)
    mode = "RGBA" if (im.mode == "RGBA" or len(color) == 4) else "RGB"
    canvas = Image.new(mode, (w, h), color if mode == "RGBA" else color[:3])
    gx, gy = GRAVITY[gravity]
    canvas.paste(im2, (round((w - rw) * gx), round((h - rh) * gy)), im2 if im2.mode == "RGBA" else None)
    return canvas, scale


def unique(path):
    base, ext = os.path.splitext(path)
    n, p = 2, path
    while os.path.exists(p):
        p = "{}_{}{}".format(base, n, ext)
        n += 1
    return p


def save(im, src, label, how, out_dir, fmt):
    stem = os.path.splitext(os.path.basename(src))[0]
    ext = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}[fmt or ("png" if im.mode == "RGBA" else "jpeg")]
    if ext == ".jpg" and im.mode == "RGBA":
        im = im.convert("RGB")
    path = unique(os.path.join(out_dir or os.path.dirname(src) or ".", "{}_{}{}".format(stem, label, ext)))
    kw = {"quality": 92, "optimize": True} if ext in (".jpg", ".webp") else {"optimize": True}
    im.save(path, **kw)
    with open(os.path.splitext(path)[0] + ".txt", "w", encoding="utf-8") as f:
        f.write("# Export record\nsource: {}\n{}\nsize: {}x{}\n".format(os.path.basename(src), how, im.width, im.height))
    print("saved {}  ({}x{})".format(path, im.width, im.height))
    return path


def regions(mask, min_px):
    """Bounding boxes of connected white regions in an 'L' mask (pure Python, 4-connectivity).
    Regions smaller than min_px pixels are dropped as noise."""
    w, h = mask.size
    px = mask.load()
    seen = bytearray(w * h)
    boxes = []
    for y in range(h):
        for x in range(w):
            if px[x, y] < 128 or seen[y * w + x]:
                continue
            stack = [(x, y)]
            seen[y * w + x] = 1
            x0 = x1 = x
            y0 = y1 = y
            n = 0
            while stack:
                cx, cy = stack.pop()
                n += 1
                x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny] >= 128:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            if n >= max(1, min_px):
                boxes.append((x0, y0, x1, y1))
    return boxes


def merge(argv):
    """Keep the original's pixels everywhere except where the edit actually changed something.

    Seedream re-renders the whole image on every edit, which adds faint noise and drift to
    areas you asked it to keep. This finds the regions that really changed, feathers their
    edges, and pastes only those onto the original.
    """
    p = argparse.ArgumentParser(prog="export.py merge",
                                description="Paste only the changed regions of an edit back onto the original.")
    p.add_argument("original")
    p.add_argument("edited")
    p.add_argument("--threshold", type=int, default=16,
                   help="Per-pixel difference (0-255) that counts as a real change (default 16)")
    p.add_argument("--grow", type=int, default=40, help="Padding around each changed region, in pixels (default 40)")
    p.add_argument("--feather", type=int, default=12, help="Edge softness in pixels (default 12)")
    p.add_argument("--min-area", type=float, default=0.0005,
                   help="Ignore changed specks smaller than this fraction of the image (default 0.0005)")
    p.add_argument("--save-mask", action="store_true", help="Also save the mask used, for checking")
    p.add_argument("--out", help="Output folder (default: next to the edited image)")
    a = p.parse_args(argv)

    Image = need_pillow()
    from PIL import ImageChops, ImageFilter
    orig = Image.open(a.original).convert("RGB")
    edit = Image.open(a.edited).convert("RGB")
    if edit.size != orig.size:
        print("note: edited image is {}x{}, original {}x{}; resizing the edit to match.".format(
            edit.width, edit.height, orig.width, orig.height), file=sys.stderr)
        edit = edit.resize(orig.size, Image.LANCZOS)

    # Work on a smaller copy for speed and to ignore pixel-level noise.
    scale = max(1, max(orig.size) // 1024)
    small = (orig.width // scale, orig.height // scale)
    diff = ImageChops.difference(orig.resize(small, Image.BILINEAR), edit.resize(small, Image.BILINEAR))
    diff = diff.convert("L").filter(ImageFilter.GaussianBlur(2))
    raw = diff.point(lambda v: 255 if v >= a.threshold else 0)
    # Join nearby changed pixels (e.g. the strokes of rewritten text) into one region.
    join = max(3, (a.grow // scale) | 1)
    joined = raw.filter(ImageFilter.MaxFilter(min(join * 2 + 1, 61)))
    boxes = regions(joined, a.min_area * small[0] * small[1])

    # Fill a padded box around each region, so text and objects are replaced whole,
    # never half old and half new.
    from PIL import ImageDraw
    mask = Image.new("L", small, 0)
    pad = max(1, a.grow // scale)
    draw = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in boxes:
        draw.rectangle((max(0, x0 - pad), max(0, y0 - pad), min(small[0] - 1, x1 + pad),
                        min(small[1] - 1, y1 + pad)), fill=255)

    mask = mask.resize(orig.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(max(1, a.feather)))
    changed = sum(1 for v in mask.resize(small).getdata() if v > 127) / float(small[0] * small[1])
    bbox = mask.point(lambda v: 255 if v > 127 else 0).getbbox()

    result = Image.composite(edit, orig, mask)
    how = ("op: merged changed regions of {} onto {}; threshold {}, grow {}, feather {}; "
           "{:.1%} of the image taken from the edit; changed area bbox {}".format(
               os.path.basename(a.edited), os.path.basename(a.original), a.threshold, a.grow,
               a.feather, changed, bbox))
    out_dir = a.out or os.path.dirname(a.edited) or "."
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    save(result, a.edited, "merged", how, out_dir, "png")
    if a.save_mask:
        save(mask, a.edited, "mask", "op: merge mask (white = taken from the edit)", out_dir, "png")
    print("{:.1%} of the image came from the edit; everything else is the original's pixels.".format(changed))
    if changed > 0.5:
        print("warning: over half the image changed. The edit may have shifted the whole frame; "
              "check it, or raise --threshold.", file=sys.stderr)
    if changed == 0:
        print("warning: no changes detected; lower --threshold if the edit was subtle.", file=sys.stderr)
    return 0


def layers(argv):
    """Assemble a --layers folder: canvas-sized aligned PNGs (drop into Photoshop / After Effects /
    a game engine and they line up), a flattened composite, and a layered SVG that Figma,
    Illustrator and Inkscape import as separate layers."""
    import base64, io as _io, json
    p = argparse.ArgumentParser(prog="export.py layers")
    p.add_argument("folder", help="The <name>_layers folder written by seedream.py generate --layers")
    p.add_argument("--original", help="The image that was split: everything is scaled back to its exact size "
                                      "(the split canvas comes back slightly larger) and the stack is compared with it")
    p.add_argument("--svg-max", type=int, default=0,
                   help="Longest side of the SVG canvas (default: the original's size, else 2048)")
    p.add_argument("--live-text", action="store_true",
                   help="In the SVG, write OCR'd text layers as editable <text> (font guess, colour, size from the "
                        "split) instead of pictures. Approximate: check sizes and fonts in your design tool")
    p.add_argument("--alpha-floor", type=int, default=0,
                   help="Make pixels with alpha below this fully transparent (e.g. 48): removes glow haze "
                        "and faint specks before you move layers onto a new background")
    a = p.parse_args(argv)
    Image = need_pillow()
    with open(os.path.join(a.folder, "layers.json"), encoding="utf-8") as f:
        man = json.load(f)
    W, H = man["canvas"]
    sx = sy = 1.0
    if a.original:
        with Image.open(a.original) as o:
            ow, oh = o.size
        sx, sy = ow / float(W), oh / float(H)
        if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
            print("scaling the {}x{} split canvas to the original's {}x{}".format(W, H, ow, oh))
        W, H = ow, oh
    out = os.path.join(a.folder, "aligned")
    os.makedirs(out, exist_ok=True)
    comp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    svg_max = a.svg_max or (max(W, H) if a.original else 2048)
    k = min(1.0, svg_max / float(max(W, H)))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           'width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(round(W * k), round(H * k))]
    for l in sorted(man["layers"], key=lambda l: l["z_index"]):
        x1, y1, x2, y2 = [int(round(v * s)) for v, s in zip(l["box"], (sx, sy, sx, sy))]
        im = Image.open(os.path.join(a.folder, l["file"])).convert("RGBA")
        if a.alpha_floor and l["z_index"] != 0:
            r, g, b, al = im.split()
            im = Image.merge("RGBA", (r, g, b, al.point(lambda v: 0 if v < a.alpha_floor else v)))
        im = im.resize((max(1, x2 - x1), max(1, y2 - y1)), Image.LANCZOS)
        full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        full.alpha_composite(im, (max(0, x1), max(0, y1)), (max(0, -x1), max(0, -y1)))
        full.save(os.path.join(out, l["file"]))
        comp.alpha_composite(full)
        small = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
        buf = _io.BytesIO()
        small.save(buf, "PNG", optimize=True)
        label = _xml(l.get("text") or l.get("name") or l["file"])
        if a.live_text and l.get("text_lines"):
            svg.append(_live_text(l, sx, sy, k, label))
            continue
        svg.append('<g id="layer_{0}"><title>{1}</title><image x="{2}" y="{3}" width="{4}" height="{5}" '
                   'xlink:href="data:image/png;base64,{6}"/></g>'.format(
                       os.path.splitext(l["file"])[0], label, round(x1 * k), round(y1 * k),
                       small.width, small.height, base64.b64encode(buf.getvalue()).decode()))
    svg.append("</svg>")
    comp.save(os.path.join(a.folder, "composite.png"))
    with open(os.path.join(a.folder, "layers.svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("{} layers -> aligned/ (canvas {}x{}), composite.png, layers.svg".format(len(man["layers"]), W, H))
    if a.original:
        from PIL import ImageChops, ImageStat
        o = Image.open(a.original).convert("RGB").resize((W, H), Image.LANCZOS)
        diff = ImageStat.Stat(ImageChops.difference(o, comp.convert("RGB"))).mean
        print("mean difference from the original: {:.1f} / 255 per channel (under ~8 is visually the same)".format(
            sum(diff) / 3))
    return 0


def _xml(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _live_text(l, sx, sy, k, label):
    """One <text> per OCR line. Line boxes ('absolute') are in canvas pixels, like the layer boxes."""
    out = ['<g id="layer_{}"><title>{}</title>'.format(_xml(os.path.splitext(l["file"])[0]), label)]
    for line in l["text_lines"]:
        ab = (line.get("bounding_box") or {}).get("absolute") or l["box"]
        lx1, ly1, lx2, ly2 = ab[0] * sx, ab[1] * sy, ab[2] * sx, ab[3] * sy
        runs = line.get("runs") or []
        st = (runs[0].get("style") if runs else None) or {}
        size = (ly2 - ly1) * 0.8                        # line box ~ ascender to descender plus padding
        out.append('<text x="{:.1f}" y="{:.1f}" font-family="{}" font-size="{:.1f}" font-weight="{}" '
                   'font-style="{}" fill="{}" textLength="{:.1f}" lengthAdjust="spacingAndGlyphs">{}</text>'.format(
                       lx1 * k, (ly2 - (ly2 - ly1) * 0.2) * k, _xml((st.get("similar_font_family") + ", " if st.get("similar_font_family") else "") + "sans-serif"),
                       size * k, "bold" if st.get("bold") else "normal", "italic" if st.get("italic") else "normal",
                       _xml(st.get("foreground_color") or "#000000"), (lx2 - lx1) * k,
                       _xml("".join(r.get("text", "") for r in runs))))
    out.append("</g>")
    return "".join(out)


def split(argv):
    """Cut a transparent sheet (icons, stickers, sprites) into one trimmed PNG per item."""
    p = argparse.ArgumentParser(prog="export.py split")
    p.add_argument("image", help="A PNG with a transparent background (e.g. from --background transparent)")
    p.add_argument("--names", help="Comma-separated names in reading order (top-left to bottom-right)")
    p.add_argument("--pad", type=int, default=16, help="Transparent margin around each item (default 16)")
    p.add_argument("--square", action="store_true", help="Pad each item to a square canvas (app icons)")
    p.add_argument("--min-area", type=float, default=0.002,
                   help="Ignore specks smaller than this fraction of the image (default 0.002)")
    p.add_argument("--join", type=int, default=0,
                   help="Merge parts closer than this many pixels (rain drops under a cloud). Default: auto")
    p.add_argument("--out", help="Output folder (default: <name>_parts next to the source)")
    a = p.parse_args(argv)
    Image = need_pillow()
    from PIL import ImageFilter
    src = Image.open(a.image)
    if src.mode != "RGBA" or src.getextrema()[3][0] == 255:
        sys.exit("error: needs a PNG with transparency; generate with --background transparent.")
    alpha = src.getchannel("A")
    scale = min(1.0, 512.0 / max(src.size))
    sm = alpha.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))))
    mask = sm.point(lambda v: 255 if v > 24 else 0)
    join = a.join or max(3, int(max(src.size) * 0.012))
    rad = max(1, int(join * scale))
    mask = mask.filter(ImageFilter.MaxFilter(rad * 2 + 1))
    min_px = a.min_area * sm.width * sm.height
    boxes = regions(mask, min_px)
    if not boxes:
        sys.exit("error: no items found.")
    # reading order: a box joins the current row if it overlaps the row's whole vertical span
    rows, span = [], None
    for b in sorted(boxes, key=lambda b: b[1]):
        if rows and b[1] <= span[1] and b[3] >= span[0]:
            rows[-1].append(b)
            span = (min(span[0], b[1]), max(span[1], b[3]))
        else:
            rows.append([b])
            span = (b[1], b[3])
    boxes = [b for r in rows for b in sorted(r, key=lambda b: b[0])]
    import re as _re
    names = [_re.sub(r"[^\w.-]+", "_", n.strip()) for n in a.names.split(",")] if a.names else []
    if names and len(names) != len(boxes):
        print("warning: found {} items but got {} names; unnamed items are numbered.".format(
            len(boxes), len(names)), file=sys.stderr)
    out = a.out or os.path.splitext(a.image)[0] + "_parts"
    os.makedirs(out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.image))[0]
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        box = [int(x0 / scale), int(y0 / scale), int((x1 + 1) / scale), int((y1 + 1) / scale)]
        piece = src.crop(box)
        bb = piece.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bb:
            piece = piece.crop(bb)
        w, h = piece.size
        if a.square:
            w = h = max(w, h)
        canvas = Image.new("RGBA", (w + 2 * a.pad, h + 2 * a.pad), (0, 0, 0, 0))
        canvas.alpha_composite(piece, (a.pad + (w - piece.width) // 2, a.pad + (h - piece.height) // 2))
        name = names[i] if i < len(names) else "{}_{:02d}".format(stem, i + 1)
        path = unique(os.path.join(out, name + ".png"))
        canvas.save(path)
        print("saved {}  {}x{}".format(path, canvas.width, canvas.height))
    print("{} items from {}".format(len(boxes), a.image))
    return 0


ICON_SETS = {
    # file: (size, needs an opaque background)
    "favicon-16x16.png": (16, False), "favicon-32x32.png": (32, False), "favicon-48x48.png": (48, False),
    "apple-touch-icon.png": (180, True), "icon-192.png": (192, False), "icon-512.png": (512, False),
}
ANDROID = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def icons(argv):
    """One square source -> web favicons, PWA icons (incl. maskable), an iOS AppIcon set and
    Android launcher icons, plus the HTML tags and web manifest to wire them up."""
    p = argparse.ArgumentParser(prog="export.py icons")
    p.add_argument("image", help="Square-ish logo or icon (transparent PNG works best)")
    p.add_argument("--out", help="Output folder (default: <name>_icons next to the source)")
    p.add_argument("--bg", default="#ffffff",
                   help="Background for icons that can't be transparent (iOS, apple-touch, maskable). Default #ffffff")
    p.add_argument("--padding", type=float, default=0.0,
                   help="Extra transparent margin around the art, as a fraction (e.g. 0.08)")
    p.add_argument("--name", default="App", help="App name for site.webmanifest")
    a = p.parse_args(argv)
    Image = need_pillow()
    src = Image.open(a.image).convert("RGBA")
    if abs(src.width - src.height) > 2:
        side = min(src.size)
        print("note: source is {}x{}; using the centred {}x{} square.".format(src.width, src.height, side, side),
              file=sys.stderr)
        src = src.crop(((src.width - side) // 2, (src.height - side) // 2,
                        (src.width - side) // 2 + side, (src.height - side) // 2 + side))
    if a.padding:
        pad = int(src.width * a.padding)
        canvas = Image.new("RGBA", (src.width + 2 * pad, src.height + 2 * pad), (0, 0, 0, 0))
        canvas.alpha_composite(src, (pad, pad))
        src = canvas
    if src.width < 512:
        print("warning: source is only {} px; icons above that are upscaled.".format(src.width), file=sys.stderr)
    out = a.out or os.path.splitext(a.image)[0] + "_icons"
    os.makedirs(out, exist_ok=True)
    bg = hex_color(a.bg, "RGB")

    def sized(n, opaque=False, inset=0.0):
        art = src
        if inset:
            inner = max(1, int(round(n * (1 - 2 * inset))))
            im = Image.new("RGBA", (n, n), bg + (255,) if opaque else (0, 0, 0, 0))
            im.alpha_composite(art.resize((inner, inner), Image.LANCZOS), ((n - inner) // 2, (n - inner) // 2))
        else:
            im = art.resize((n, n), Image.LANCZOS)
            if opaque:
                flat = Image.new("RGBA", (n, n), bg + (255,))
                flat.alpha_composite(im)
                im = flat
        return im.convert("RGB") if opaque else im

    written = []
    def put(im, rel):
        path = os.path.join(out, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        im.save(path)
        written.append(rel)

    for fn, (n, opaque) in ICON_SETS.items():
        put(sized(n, opaque), fn)
    put(sized(512, True, inset=0.22), "icon-maskable-512.png")       # art inside the 80% safe circle
    ico = os.path.join(out, "favicon.ico")
    sized(48).save(ico, sizes=[(16, 16), (32, 32), (48, 48)])
    written.append("favicon.ico")
    # iOS: one 1024 universal icon, opaque (App Store rejects alpha)
    put(sized(1024, True), "ios/AppIcon.appiconset/AppIcon-1024.png")
    with open(os.path.join(out, "ios/AppIcon.appiconset/Contents.json"), "w", encoding="utf-8") as f:
        json.dump({"images": [{"filename": "AppIcon-1024.png", "idiom": "universal", "platform": "ios",
                               "size": "1024x1024"}], "info": {"author": "xcode", "version": 1}}, f, indent=2)
    written.append("ios/AppIcon.appiconset/Contents.json")
    for dens, n in ANDROID.items():
        put(sized(n), "android/mipmap-{}/ic_launcher.png".format(dens))
    put(sized(512, True), "android/play-store-512.png")
    manifest = {"name": a.name, "short_name": a.name, "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
        "theme_color": a.bg, "background_color": a.bg, "display": "standalone"}
    with open(os.path.join(out, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    written.append("site.webmanifest")
    tags = ('<link rel="icon" href="/favicon.ico" sizes="any">\n'
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">\n'
            '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">\n'
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
            '<link rel="manifest" href="/site.webmanifest">\n')
    with open(os.path.join(out, "head-snippet.html"), "w", encoding="utf-8") as f:
        f.write(tags)
    print("{} files in {}".format(len(written) + 1, out))
    print("Copy the web files to your site root (e.g. public/) and add to <head>:\n" + tags.rstrip())
    print("iOS: drag ios/AppIcon.appiconset into Assets.xcassets. Android: copy android/mipmap-* into app/src/main/res/.")
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if argv is None:
        argv = sys.argv[1:]
    if argv[:1] == ["presets"]:
        for k, (w, h, note) in PRESETS.items():
            print("{:<17} {:>4}x{:<5} {}".format(k, w, h, note))
        return 0
    if argv[:1] == ["merge"]:
        return merge(argv[1:])
    if argv[:1] == ["layers"]:
        return layers(argv[1:])
    if argv[:1] == ["split"]:
        return split(argv[1:])
    if argv[:1] == ["icons"]:
        return icons(argv[1:])

    p = argparse.ArgumentParser(description="Export a Seedream image for a platform.")
    p.add_argument("image", help="Source image (never modified)")
    p.add_argument("--to", action="append", choices=sorted(PRESETS), help="Platform preset (repeatable)")
    p.add_argument("--size", help="Custom WxH instead of / as well as presets")
    p.add_argument("--fit", choices=["crop", "pad"], default="crop",
                   help="crop = fill and trim (default); pad = fit whole image and pad")
    p.add_argument("--gravity", choices=sorted(GRAVITY), default="center",
                   help="Which part to keep when cropping / where to place when padding")
    p.add_argument("--pad-color", default="#ffffff", help="#rrggbb or 'transparent' (with --fit pad)")
    p.add_argument("--flip", action="store_true", help="Mirror horizontally (fix a detail on the wrong side)")
    p.add_argument("--format", choices=["png", "jpeg", "webp"], help="Output format (default: png if transparent, else jpeg)")
    p.add_argument("--out", help="Output folder (default: next to the source)")
    a = p.parse_args(argv)

    if not (a.to or a.size or a.flip):
        p.error("give at least one of --to, --size or --flip")
    Image = need_pillow()
    if not os.path.isfile(a.image):
        sys.exit("error: not found: " + a.image)
    src = Image.open(a.image)
    src = src.convert("RGBA") if src.mode in ("RGBA", "LA", "P") and "transparency" in src.info or src.mode == "RGBA" else src.convert("RGB")
    if a.out:
        os.makedirs(a.out, exist_ok=True)

    base, flip_note = src, ""
    if a.flip:
        from PIL import ImageOps
        base = ImageOps.mirror(src)
        flip_note = "mirrored horizontally; "
        if not (a.to or a.size):
            save(base, a.image, "flipped", "op: mirrored horizontally", a.out, a.format)
            print("note: check that the image has no text, which would now read backwards.", file=sys.stderr)
            return 0

    targets = [(k, PRESETS[k][0], PRESETS[k][1]) for k in (a.to or [])]
    if a.size:
        w, h = parse_wh(a.size)
        targets.append(("{}x{}".format(w, h), w, h))
    for label, w, h in targets:
        if a.fit == "crop":
            im, scale = cover_crop(Image, base, w, h, a.gravity)
            lost_w = 1 - (w / (base.width * scale))
            lost_h = 1 - (h / (base.height * scale))
            how = "op: {}cropped to {}x{} (gravity {}); trimmed {:.0%} width, {:.0%} height".format(
                flip_note, w, h, a.gravity, lost_w, lost_h)
            if max(lost_w, lost_h) > 0.15:
                print("warning: {} trims {:.0%} of the image; check nothing important was cut, "
                      "or use --fit pad / --gravity.".format(label, max(lost_w, lost_h)), file=sys.stderr)
        else:
            im, scale = contain_pad(Image, base, w, h, hex_color(a.pad_color, base.mode), a.gravity)
            how = "op: {}fitted inside {}x{} and padded with {}".format(flip_note, w, h, a.pad_color)
        if scale > 1.05:
            print("warning: {} upscales the source {:.1f}x; for print, use a dedicated upscaler.".format(label, scale),
                  file=sys.stderr)
        save(im, a.image, label, how, a.out, a.format)
    return 0


if __name__ == "__main__":
    sys.exit(main())
