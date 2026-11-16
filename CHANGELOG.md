# Changelog

## 2.2.0 (2026-11-16)

**For projects**
- `seedream.py batch`: generate a whole asset list from `.seedream/assets.json` with one style.
  It shows the plan and the estimated cost before spending (`--yes`), runs jobs in parallel, and
  re-renders only the assets whose inputs changed, keeping their file names.
- `--style FILE`, `--final-size WxH`, `seedream.py costs` (a cost ledger kept next to your images).
- `export.py icons`: favicons, PWA icons, iOS `AppIcon.appiconset` and Android mipmaps from one
  logo, plus the `<head>` tags.
- `export.py style`: start `.seedream/style.md` from a logo or a screenshot (real palette).
- New size presets: `og`, `x-card`, App Store, Google Play, Steam.
- Claude Code commands: `/seedream`, `/seedream-kit`, `/seedream-edit`, `/seedream-icons`.

**Editing and layers**
- `references/editing.md`: 9 tested edit types (background swap, colour change, relight,
  restore, draw-to-edit, remove, restyle, sketch to image, outpaint).
- `export.py --fit pad --pad-color blur` creates an outpainting canvas.
- `--layers N --ocr` splits an image into layers (BytePlus, Volcengine, fal). `export.py layers`
  then writes an SVG with optional editable text and aligned PNGs, and can scale everything back
  to the original's size.
- `export.py split` cuts a transparent sheet into one file per icon or sprite.

**Coverage**
- `references/ui-ux.md`: apps, websites, dashboards, game HUDs, kiosks, dark mode, mockups.
- Event playbook (stage screens, badges); localisation; speed and live-app guidance.
- fal and OpenRouter now default to Seedream 5.5.
- 22 failure modes, all labelled Tested, Official or Reported; evidence rounds 3 to 6; 45 offline tests.

## 2.0.0

- 9 API platforms, `--count` options with a contact sheet, `export.py` (merge, presets, flip),
  a prompt library, failure modes with evidence labels, and skill-creator evals.
