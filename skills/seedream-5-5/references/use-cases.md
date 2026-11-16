# Playbooks by use case

These are the jobs people use Seedream for most, ranked by how often they appear in public reviews,
vendor tests and ByteDance's own material (November 2026). Each playbook covers which model and
settings to use, the template to start from, and what usually goes wrong.

## 1. Realistic people, fashion and lifestyle

Seedream's strongest category in public head-to-head tests (*Reported*).

- **Model:** 5.5 by default. Some users prefer 4.5 for natural skin (*Reported*).
- **Template:** Photoreal. Name the skin texture, a real light source and a lens.
- **Watch for:**
  - The plastic "AI glamour" look.
  - Safety-filter false positives on swimwear and lingerie. Use neutral wording, state the
    catalogue context, frame wider.
  - Rejections of reference photos showing real people.

## 2. E-commerce and advertising

- **Model:** 5.5. Use `--background transparent` for cut-outs.
- **Template:** Product. Use the product photo as Image 1, give it the role "exact shape, colour,
  logo", and say what to ignore.
- **Pattern:** reviewers report that Seedream suits mood-led "campaign" images better than strict
  catalogue fidelity (*Reported*). For catalogue work, check the label and shape against the
  original before publishing.
- **Watch for:**
  - Product drift during edits.
  - Identical items not being identical.

## 3. Posters, social covers and Chinese text

Seedream is especially strong on Chinese text (*Reported*, *Tested*).

- **Template:** Poster.
- **Language:** write the prompt in the same language as the text.
- **Watch for:**
  - Small or dense English text.
  - Unrequested seal stamps on Chinese designs.
  - Put fine print in a layout tool.

## 4. Infographics and slides

- **Model:** 5.5. ByteDance claims better dense text for this version.
- **Template:** Infographic. Quote every number and label.
- **Watch for:** bar heights are only roughly proportional. For real data, use a charting tool and
  let Seedream do the illustration.

## 5. Consistent characters: comics, storyboards, mascots

- **Flow:** character sheet, then scenes with the sheet as an "identity" reference, then
  one-change edits.
- **Image sets:** 5.5 can't return them. Call it once per panel, or use 4.5 / 5.0 Lite with
  `sequential_image_generation` (see `prompting.md`).
- **Watch for:**
  - Left/right swaps of one-sided details. Mirror-flip the result.
  - Repeat the character block word for word in every panel.

## 6. Editing by instruction

Covers restoration, object swaps, retouching and region edits. The full playbook, with 9 tested edit
types, is [`editing.md`](editing.md).

- **Model:** 5.5. ByteDance claims stable editing over 100 rounds. We saw no meaningful drift
  over 3 rounds (*Tested*).
- **Template:** Edit, or Region edit (`<bbox>`).
- **Prompt formula:** action + named target + change + keep-list.
- **Marking up:** you can draw on the image and explain what the marks mean.

## 7. Keyframes for image-to-video (Seedance, Kling and others)

- **Template:** Keyframe.
- **Pattern:** approve cheap stills first, then spend on video. Reuse the last frame of one clip
  as the first frame of the next.
- **Watch for:** text in the frame melts once it is animated. Add text in post.

## 8. Transparent assets, icon sets and layers (5.5)

- **Stickers, icons, overlays:** use `--background transparent` and say "Set a transparent
  background." in the prompt (*Tested*).
- **Icon sets and sprite sheets:** render the whole set in one grid with a transparent background,
  then `export.py split`. You get a consistent style and pay for one image (*Tested*).
- **Layer decomposition:** `--layers N --ocr` turns a flat poster, ad or screen into editable
  layers plus a base plate. The split itself is *Tested*. `export.py layers` then writes an SVG
  with one image per layer (for design tools such as Figma or Illustrator), and canvas-sized
  aligned PNGs for Photoshop, After Effects parallax or a game engine. We checked these files
  for correctness, but haven't opened them in each of those apps. Read the edge caveats in
  `prompting.md` first.

## 9. UI and UX: websites, apps, dashboards, games, kiosks

Screens for pitch decks, design reviews, store listings and starting points for Figma. Covers
light and dark mode, device mockups, game HUDs and inventory icons, kiosk and self-service screens,
and hand-off as layers: see [`ui-ux.md`](ui-ux.md). Phone, web, dashboard, HUD and kiosk screens
are all *Tested*.

- **Watch for:** real brand logos when you ask for "placeholder logos", invented filler copy, and
  empty canvas when there is little content (all *Tested*).

## 10. Localisation: the same design in other languages

- **Flow:** finish the design once, then for each language run one edit with the design as Image 1
  and every line's translation spelled out (*Tested* with Spanish). Then `export.py merge`, so only
  the text areas change and the artwork stays the original pixels.
- **Watch for:** longer translations need room. Say "refit the line to the same width" or
  shorten the copy. For Chinese, Japanese or Arabic, write the prompt in that language too.

## 11. Speed, cost and live apps

- **Latency:** a 5.5 render takes about **20–30 s** (*Tested*: 1K averaged 24 s and 2K averaged 27 s
  over 3 runs each). Layer splits took 49–61 s. That is not real-time.
- **1K saves money, not time.** It is barely faster, but on BytePlus it costs $0.020 against
  $0.035 at 2K. Draft at 1K when you are exploring looks; render the final at 2K.
- **In an app or a game:**
  - Generate ahead of time, or queue requests in the background and show a placeholder.
  - Cache results by a hash of the prompt and references, so a repeated request costs nothing.
  - Use `--count` (parallel requests) when the user is choosing between looks.
  - Keep keys on the server and never in client code.
- **Interactive editing loop:** user marks a region, then a `<bbox>` edit, then `export.py
  merge`, then show it. Each round takes about half a minute, and the pixels outside the box stay
  the user's original.

## 12. Events: stage screens, badges, signage

- **Stage and LED walls:** use the exact wall ratio as `WxH`. A 32:9 wall at `3584x1008` came out
  clean (*Tested*). Keep the centre third simple and high contrast, so it reads from the back of
  the room, and keep sponsor logos out ("no sponsor logos"). Add the real ones in a layout tool.
- **Badges and lanyards:** a 2:3 badge with the name, role, company and a "SPEAKER" tag came out
  exact (*Tested*). Ask for "a plain grey square placeholder" where the QR code goes. Never let the
  model draw a QR code or a barcode; generate the real one and paste it in.
- **A whole event kit:** render the stage screen first, then make badges, social cards and
  signage with the stage screen as Image 1 ("the same gradient, light ribbons and logotype
  style"). Then export each one to its size with `export.py --to` or `--size`.
- **Print:** 5.5 tops out at about 4.6 MP. For A-size posters and roll-ups, upscale with a
  dedicated upscaler or render on 5.0 Lite / 4.5 at 4K.

## Picking a model

| Need | Use |
|---|---|
| The best edits, transparency, layers | 5.5 |
| A 4K deliverable | 5.0 Lite or 4.5 (5.5 tops out at 2K) |
| A batch or image set in one call | 5.0 Lite, 4.5 or 4.0 |
| The lowest cost per image | 5.0 Flash |
| More than 10 references | 5.0 Lite, 4.5 or 4.0 (up to 14) |
