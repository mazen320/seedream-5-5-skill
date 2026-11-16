# Project assets: style lock, batch manifests, icons, exact sizes

Use this when images belong to a codebase: a website, an app, a game or a docs site. The goal is
to put files in the project's own folders, at the right sizes and in a consistent style, from a
manifest the user can commit and re-run.

## 1. Find where images live

Look before you write. Use the first match:

| Project | Put images in | Icons / meta |
|---|---|---|
| Next.js, Vite, CRA, Astro, SvelteKit | `public/` (`public/images/`) | `public/` root, tags in the layout `<head>` |
| Hugo, Jekyll, Eleventy | `static/` or `assets/` | site root |
| Rails / Django | `app/assets/images/` / `static/` | |
| iOS (Xcode) | `Assets.xcassets` | `AppIcon.appiconset` |
| Android | `app/src/main/res/drawable*/` | `res/mipmap-*/` |
| Flutter / React Native | `assets/images/` (and register it) | platform folders |
| Unity | `Assets/Art/...` (import PNGs as Sprite 2D/UI) | |
| Godot | `res://assets/` | |

If nothing matches, ask once, or use `assets/generated/`. Never leave final assets in a temp folder.

## 2. Lock the style once

Write the look to `.seedream/style.md` (one paragraph: medium, palette with hex codes, line
quality, lighting, what to avoid). Pass it with `--style .seedream/style.md`, or set `style_file`
in a manifest. The script appends it to every prompt as "House style for this project: …".

*Tested:* four assets with one style file (hero, link-preview card, empty state, logo mark) came out
in a single coherent palette and illustration style. See
[`examples/04-project-asset-kit.md`](../../../examples/04-project-asset-kit.md).

## 3. Batch from a manifest

```json
{
  "provider": "byteplus",
  "out": "public/images",
  "style_file": ".seedream/style.md",
  "defaults": {"size": "16:9"},
  "assets": [
    {"name": "hero", "prompt": "...", "size": "21:9"},
    {"name": "og-image", "prompt": "...", "size": "2K", "final_size": "1200x630"},
    {"name": "empty-trips", "prompt": "... Set a transparent background.", "size": "1:1", "background": "transparent"},
    {"name": "feature-sync", "prompt": "...", "image": ["refs/screenshot.png"], "export": ["x-card"]}
  ]
}
```

```bash
python scripts/seedream.py batch .seedream/assets.json            # plan + estimated cost, spends nothing
python scripts/seedream.py batch .seedream/assets.json --yes      # generate (parallel, --jobs 3)
python scripts/seedream.py batch .seedream/assets.json --yes --only hero --force
python scripts/seedream.py costs --out .seedream                  # what this project has cost
```

- **Approval:** without `--yes`, `batch` prints the plan and the estimated cost and exits with
  code 3. Show that plan to the user before you spend on more than a few images.
- **Paths** in the manifest are relative to the project root: the manifest's folder, or its parent
  when the manifest lives in `.seedream/` (set `"root"` to override).
- **Idempotent:** each asset's inputs (prompt, style, size, references, model, output folder,
  exports) are hashed into `.seedream/state/<name>.json`. A re-run skips anything unchanged. Edit
  one prompt and only that asset re-renders: its previous file is moved to
  `.seedream/replaced/<time>/` and the new one keeps the same name, so your code's paths stay
  valid. *Tested* live: after one prompt edit, "3 up to date, 1 to generate".
- **Out of your web root:** prompt records, the state, the cost ledger and `batch_sheet.html` go in
  `.seedream/`. Only the images go in `out`.
- **Per-asset fields:** `prompt` (required), `size`, `image` (references), `background`,
  `output_format`, `final_size`, `fit` (`crop`/`pad`), `model`, `out`, `export` (preset names
  from `export.py presets`), and `"style": false` to skip the house style.
- YAML works too if PyYAML is installed. Commit `.seedream/assets.json` and `style.md`; add
  `.seedream/state/`, `.seedream/replaced/` and `.seedream/records/` to `.gitignore` if you
  don't want them in the repo.
- A file with the asset's name that the batch didn't make is never overwritten: the new image gets
  `_2` and the batch tells you.

## 4. Exact sizes

Seedream can't render below about 0.92 MP, so 512×512 or 1200×630 never come straight from the API.
Render at a ratio close to the target, then:

- `--final-size 1200x630` (generate or manifest) saves an exact-size copy next to the master.
- `export.py <img> --to og` and the other presets: `og`, `x-card`, `appstore-iphone-6.9`,
  `appstore-iphone-6.5`, `appstore-ipad-13`, `play-feature`, `steam-capsule`, `steam-header`,
  plus the social and print sizes.

## 5. Icons and favicons

```bash
python scripts/export.py icons public/images/logo-mark.png --out public --bg "#F4EDE1" --name Fernway
```

From one square image, this writes:
- favicons: `favicon.ico` (16/32/48) and 16, 32 and 48 px PNGs;
- `apple-touch-icon.png` (180, opaque);
- PWA icons at 192 and 512, plus a maskable 512 with an 80% safe zone, and `site.webmanifest`;
- `ios/AppIcon.appiconset/` (1024, opaque, with `Contents.json`);
- `android/mipmap-*/ic_launcher.png` and a 512 Play Store icon;
- `head-snippet.html` with the `<link>` tags. Paste them into the layout and say where.

Generate the mark with `--background transparent`, a bold simple shape and no text. Check it at 32 px:
detailed marks turn to mush (*Tested*: our fern-and-track mark read at 180 px but was busy at 32 px).
For favicons, ask for "one bold shape, two colours, no fine detail".

## 6. Recipes by project type

| Project | Assets | Notes |
|---|---|---|
| Landing page | hero (21:9 or 16:9), 3 feature illustrations, OG card, favicon set, empty states | One style file; leave headline space in the hero; real copy goes in HTML, not the image |
| Mobile app | app icon, onboarding illustrations (9:16), empty states, App Store screenshots | Screens are UI concepts ([`ui-ux.md`](ui-ux.md)); store screenshots via `--to appstore-*` |
| Game | item icons (sheet + `split`), key art, Steam capsules, HUD mockup | Transparent sheets; `--to steam-capsule` |
| Docs / blog | per-article cover images, diagrams' decorative art | A manifest entry per article; covers via `--final-size 1600x840` |
| Event | stage screen, badges, social cards, signage | Stage first, then the rest with it as a reference ([`use-cases.md`](use-cases.md) §12) |

## 7. After generating

- Look at every image before you wire it in (text, extra items, edges).
- Wire it up: `<img>` tags with real alt text, the OG `<meta>` tags, the manifest link, or Unity
  import settings.
- Report the files written, what they cost (`costs`), and anything you'd redo.
