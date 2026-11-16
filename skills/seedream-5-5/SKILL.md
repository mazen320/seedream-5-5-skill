---
name: seedream-5-5
description: Write prompts that work for ByteDance Seedream image models (5.5, 5.0, 4.5) and generate or edit images through BytePlus ModelArk, Volcengine Ark, Runware, WaveSpeed, Kie.ai, Evolink, fal, Replicate or OpenRouter. Use when the user wants to create, edit, restyle, translate or combine images with Seedream, or needs images for a project they are building in one consistent style: hero and section images, OG cards, favicons and app icons, empty states, game sprites and icons, App Store screenshots. Also for product shots, ads, posters with exact text (including Chinese), infographics, app, website, game HUD or kiosk UI mockups, dark-mode variants, event graphics, consistent characters, storyboards, video keyframes (Seedance, Kling), transparent PNGs, or splitting a flat image into editable layers; or debugging bad Seedream output, square outputs or safety-filter refusals. Not for SVG, vector, HTML or code-native graphics.
license: MIT
compatibility: Requires Python 3.8+, network access, and the user's own key for one supported platform in its environment variable (e.g. ARK_API_KEY, FAL_KEY, REPLICATE_API_TOKEN). The optional export step needs Pillow.
metadata:
  version: "2.2.0"
  default-model: "dola-seedream-5-5-261028"
---

# Seedream

Turn the user's intent into a Seedream prompt, run it through `scripts/seedream.py` on the
user's platform, check the result against the brief, and fix one thing at a time.

## Rules that always apply

- **Keys belong to the user and stay in their environment variable.** Never ask for a key in
  chat, and never write one to a file, flag, prompt or commit. If it is missing, name the variable
  (`python scripts/seedream.py providers` lists them) and stop.
- **Never overwrite outputs.** The script adds `_2`, `_3` and so on.
- **Never switch platform or model silently.** If the default fails, say what you found.
- **Report back** the file paths, the prompt you used, the platform and the size. The sidecar
  `.txt` next to each image is the full record.
- Run the script from the user's working directory, so relative paths refer to their files.

## Pick the platform

| The user has a key for… | `--provider` | Newest Seedream there |
|---|---|---|
| BytePlus ModelArk (international) | `byteplus` (default) | 5.5 |
| Volcengine Ark (China) | `volcengine` | 5.5 |
| Runware / WaveSpeed / Kie.ai / Evolink | `runware` / `wavespeed` / `kie` / `evolink` | 5.5 |
| fal / OpenRouter | `fal` / `openrouter` | 5.5 (fal also does `--layers`) |
| Replicate | `replicate` | 5.0 Pro (no 5.5 yet) |

Platforms add models often. If the user asks about a version, check the platform's live model list
before you say it isn't available.

The script converts sizes, references and polling for each platform. Kie.ai and Evolink need
reference images as **public URLs**. The others also accept local files. Endpoints, fields and
prices are in [references/providers.md](references/providers.md).

```bash
S=<this-skill-dir>/scripts/seedream.py
python $S providers                                            # platforms + key variable names
python $S models                                               # model IDs (byteplus / volcengine)
python $S generate --prompt "..." --size 16:9 --out out --name hero
python $S generate --provider fal --prompt-file p.txt --image a.png --size 2:3
python $S generate --prompt "..." --size 1:1 --background transparent   # RGBA PNG (5.5)
python $S generate --prompt "..." --dry-run                    # show the request; no key, no cost
python $S generate --prompt "..." --count 4                    # 4 options + an HTML contact sheet
python $S generate --image poster.png --layers 12 --ocr --size 2K --prompt "Split into layers. Name every layer in English."

E=<this-skill-dir>/scripts/export.py                           # finishing; needs Pillow
python $E merge original.png edited.png                        # after an edit: keep untouched pixels original
python $E out/poster.png --to instagram-post --to story        # platform sizes (python $E presets)
python $E out/portrait.png --flip                              # fix a detail on the wrong side
python $E layers out/poster_layers --original poster.png --live-text   # SVG for Figma (editable text), aligned PNGs
python $E split out/icons.png --square --names sun,rain,snow   # transparent sheet -> one PNG per item
```

## Working inside a project

When the images belong to a codebase, do the whole job, not just the render
([references/project-assets.md](references/project-assets.md)):

1. Find where the project keeps images (`public/`, `static/`, `Assets/`, `Assets.xcassets`…) and
   write there, not to a temp folder.
2. Lock the look in `.seedream/style.md` and pass `--style` (or `style_file` in a manifest).
3. For more than two assets, write `.seedream/assets.json` and run `batch`. It prints the plan
   and the estimated cost and spends nothing until `--yes`. Show the user that plan first.
   Re-runs skip unchanged assets.
4. Get exact sizes with `--final-size WxH` or `export.py --to og|x-card|appstore-*|steam-*`.
   Make icons with `export.py icons` (favicons, PWA, iOS, Android, plus the `<head>` tags).
5. Wire it in (img tags with alt text, OG meta, manifest link) and report files and cost (`costs`).

```bash
python $S batch .seedream/assets.json            # plan + cost; add --yes to generate
python $S generate --prompt "..." --style .seedream/style.md --size 2K --final-size 1200x630
python $E icons public/images/logo.png --out public --bg "#ffffff" --name MyApp
python $S costs --out .seedream
```

Offer `--count` when the user is exploring a look. Each option is a separate billed image, so
use 1 when the brief is precise.

- **Size:** always send one. The API returns a square image when size is missing (the script
  defaults to 16:9, or to a `2K` tier with `--layers` so the layers follow the input's shape).
  - Ratio presets: `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `3:2`, `2:3`, `21:9`.
  - Tiers: `1K`, `1.5K`, `2K`.
  - Or any `WxH` with an area between **921,600 and 4,624,220 px**. The API enforces this range.
- **References:** up to **10** on 5.5. They are numbered Image 1, Image 2 and so on, in the
  order you pass them.

## Decide the mode

| The user has… | Mode | What the prompt must do |
|---|---|---|
| Only an idea | Text-to-image | Follow the prompt structure below |
| One image to change | Edit | Action + named target + change, then everything to keep |
| Several images to combine | Multi-reference | Give each image a role: what to take from it and what to ignore |
| A previous output to refine | Multi-round edit | Use the last output as Image 1 and make one change per round |
| A specific region to change | Region edit | `<bbox>x1 y1 x2 y2</bbox>` or `<point>x y</point>` on a 0–999 grid |
| A need for a cut-out asset | Transparent | `--background transparent` (PNG) plus "Set a transparent background." |
| A set of icons, stickers or sprites | Sheet + split | One grid render with a transparent background, then `export.py split` |
| A flat design to make editable | Layers or rebuild | Clean UI, flat graphics: **rebuild** it as SVG/HTML with live text (no extra renders). Painterly or photo content: `--layers N --ocr`, then `export.py layers --live-text`. Every layer is billed |
| A design to translate | Localise | Edit with each line's translation spelled out, then `merge` |
| An app, website, dashboard, game HUD or kiosk screen | UI | Spec-style prompt with labels, grid, hex colours: [references/ui-ux.md](references/ui-ux.md) |
| An event (stage screen, badge, signage) | Event kit | Exact wall ratio as `WxH`, placeholder for the QR code, then reuse the stage screen as Image 1 ([use-cases.md](references/use-cases.md) §12) |

## Prompt structure

Write **prose sentences**, in this order:

1. **Deliverable and purpose:** what the image is and what it's for ("an e-commerce hero shot",
   "a poster for…").
2. **Subject**, with 2–3 specific physical details.
3. **Action and setting.**
4. **Layout:** where things sit, foreground and background, and empty space left for copy.
5. **Materials and textures.**
6. **Lighting:** source, direction, quality, colour.
7. **Camera:** shot size, angle, lens, depth of field.
8. **Style and grade.**
9. **Exact text**, in double quotes, with where it sits and how large it is relative to the
   rest.
10. **Exclusions:** one last line.

**Detail beats brevity** (*Tested*). Whatever you leave out, the model invents. Go up to about 600
English words or 300 Chinese characters (*Official*). For text in Chinese, or a look rooted in a
culture, write the prompt in that language (*Tested* for Chinese).

**Reference roles** (always state them):
> Image 1 provides the product's exact shape, colour and logo; ignore its background.
> Image 2 provides only the lighting and colour grade.

**Edits:** name the target exactly, never "it". Repeat the keep-list every round.
> Image 1 is the current image. Change only the jacket from grey wool to red leather. Keep the
> face, pose, hair, background, framing and lighting exactly as in Image 1.

There are 14 templates, including text-heavy design, icon sheets, translation, layer
decomposition and image sets, in [references/prompting.md](references/prompting.md). Playbooks for common jobs are in
[references/use-cases.md](references/use-cases.md).

## Check before you spend a render

Each item is labelled *Tested* (we ran it), *Official* (ByteDance docs) or *Reported* (seen in
public reviews or production work). The full list is in
[references/failure-modes.md](references/failure-modes.md).

- **One-sided details can come out mirrored** (*Tested*: 3 in 6). An eyepatch or earring can land on
  the wrong side. Layout positions ("on the image-left") and the **count** of details do hold. If the
  side matters, state it both ways, check the result, and mirror-flip the image if needed.
- **Exclusions leak in busy scenes** (*Tested*). Keep crowded frames simple at the edges.
- **Identical items in complex layouts** (*Tested*). The count holds, but not the sameness. For
  catalogue work, generate one item and duplicate it.
- **Text headed for video** (*Reported*). Leave it out of the still and add it in post.
- **Small or dense text** (*Reported*). Keep text big and short, and put fine print in a layout tool.
- **Safety filter** (*Reported*). Use neutral wording and state the business context. Don't
  use photos of real people as references.
- **Invented extras** (*Tested*). Watch for barcodes on covers, seals on calligraphy, and
  saucers or plates under referenced products. Exclude each one by name.
- **Floating objects** (*Tested*). Describe the physical contact: "sits inside the mug like a
  funnel in a jar", not "on the mug".
- **Real brand logos** (*Tested*). "Placeholder logos" came back as Airbnb, Slack and Stripe.
  Ask for plain grey shapes with no letters, or pass the real logos as references.
- **Invented filler copy** (*Tested*). Empty text slots in UI get made-up sentences and numbers.
  Write every string yourself. For a deck or concept, write plausible copy and tell the user
  it's a placeholder; grey bars look unfinished.
- **Layers cost per layer and aren't studio cut-outs** (*Tested*). Pick N deliberately, ask for
  English names, check edges on a solid colour, and use `--alpha-floor` to clear haze.
- **Speed** (*Tested*). About 25 s per render at 1K or 2K, and 49–61 s for a layer split. 1K saves
  money, not time. For live apps, see the speed playbook in `use-cases.md`.
- **Edits redraw the whole frame** (*Tested*). Run `export.py merge` after edits.
  - For a typo or a duplicated line, use a small region edit rather than a full regeneration.

## Workflow

1. Get the goal, where the image will be used, the aspect ratio, any references, and which
   platform key the user has. Ask once.
2. Check that the key's environment variable is set. Never ask for the key itself.
3. Pick the mode and template, write the prompt, assign reference roles, and choose a size.
4. Run the pre-flight checks above.
5. Generate with a meaningful `--name`. If the request is unusual, run `--dry-run` first.
6. Look at the image and compare it to the brief clause by clause.
   - Zoom in on every piece of text and on the product details.
   - Fix things with one-change or region edits, not full rewrites.
   - Run `export.py merge` after each edit.
7. Finish for the destination with `export.py --to <preset>`. A 2:3 or 16:9 image posted to the
   Instagram feed gets cropped to 4:5, so export it or warn the user. For a set of sizes, render
   the wide master, then the tall one **with the wide one as Image 1** ("the same scene, props,
   light and lettering, recomposed for a tall 9:16 frame; one continuous photograph"), and crop
   4:5 or 1:1 from the tall one. Small differences between versions (one more bun) are fine
   unless the user specified them; don't spend renders matching details nobody asked for. Mirror-flip with `--flip`
   if a one-sided detail landed on the wrong side.
8. Report the paths, the prompt, the platform, the size and the number of renders used.
