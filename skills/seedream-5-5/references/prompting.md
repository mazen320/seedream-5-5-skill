# Prompt templates

Fill in the brackets and delete any clause you don't need. Every template follows the same
order: deliverable and purpose, subject, action and setting, layout, materials, light, camera,
style, exact text, then exclusions.

Templates marked *Tested* produced a good result on Seedream 5.5 in our evidence run. The rest are
built from the official guide and are *untested*.

## Photoreal (*Tested*)

> A photorealistic [shot size] photograph of [subject, with 2–3 specific physical details],
> [action or pose] in [location, with 2 concrete details]. [Where the subject sits in the frame;
> what is in the foreground and background.] [Materials and textures.] Lit by [light source,
> direction, quality, colour temperature]. Shot on a [focal length] lens at [aperture],
> [depth of field]. [Mood or grade.] Exclusions: [short list].

To avoid the plastic "AI look", name skin texture, a real light source and a lens. The model fills
anything vague with generic stock lighting.

## Product (*Tested*, text-only version; it missed one detail: we asked for 3 base holes and got 4 holes in the side wall)

> A studio product photograph of the [product] in Image 1, for [use: an e-commerce listing / an
> ad]. Image 1 provides the exact shape, proportions, [colour and finish] and logo placement; keep
> them exactly and ignore Image 1's background and lighting. The product is [standing / flat lay /
> held / worn], viewed from [angle], and fills about [fraction] of the frame, with [side] left as
> empty space for copy. [Surface and backdrop.] [Key, fill and rim light, and where reflections
> should fall.] [Props and where they go.] Exclusions: no extra logos, no text, no duplicate
> products.

## Poster or graphic with exact text (*Tested*)

> A [format, e.g. A2 portrait concert poster] for [purpose]. The top third holds the headline
> "[EXACT TEXT]" in [typeface style, weight, colour], centred. The middle holds [the key visual].
> The bottom band holds, left-aligned in smaller type, "[LINE 1]", and below it "[LINE 2]".
> [Palette.] [Texture.] Every word is spelled exactly as quoted and nothing else is written.
> Exclusions: no extra text, no watermark.

**Text rules:**
- Put every string in double quotes.
- Name what the text is printed on, where it goes, how the lines break, how it is aligned, and how
  big it is relative to other text.
- Keep lines short.
- For Chinese text, write the whole prompt in Chinese (*Tested*). Add 不要印章 ("no seal stamps") if
  you don't want red seals.
- Colours can be given as hex codes alongside a colour name (*Reported*).

## Infographic or slide (*Tested*)

> A clean [16:9] infographic slide on a [background]. Title at the top, [alignment, weight,
> colour]: "[TITLE]". [Chart type] with exactly [n] [bars / points] labelled "[A]", "[B]"… with the
> values "[1]", "[2]"… printed above each. On the right third, [n] stacked icon rows: [icon] with
> "[label]"… [Style: flat vector, line weight, one accent colour.] Every word and number is
> spelled exactly as quoted and nothing else is written.

Bar heights come out only roughly proportional to the values (*Tested*). Where accuracy matters,
use a real chart.

## Character sheet, for consistency (*Tested*)

> A full-body character reference of [name]: [age, build, face, hair, distinguishing marks],
> wearing [the outfit, layer by layer, with colours and materials]. Neutral standing pose, arms
> slightly away from the body, facing the camera, the whole figure in frame with space around it.
> Plain light-grey seamless backdrop, soft even light, sharp focus throughout. Exclusions: no
> props, no other people, no text.

Use this image as an "identity" reference in every later prompt. For a one-sided detail, state the
**count** ("exactly one button eye") and check which side it lands on. Mirror-flip the sheet if the
side is wrong; prompt wording can't fix it reliably (*Tested*).

## Multi-reference composite (*Tested* with 2 and 3 references)

> Image 1 provides [character A]: keep [face, hair, outfit] exactly; [A] is on the image-left.
> Image 2 provides [character B]: keep […] exactly; [B] is in the middle. Image 3 provides only
> the location and lighting. [Action.] [Camera.] [Grade.] Exclusions: no other people, no text.

Screen positions held for people in our tests. Left/right placement failed only for small details
on one subject.

## Edit, one change per round (*Tested* over 3 rounds)

> Image 1 is the current image. Change only one thing: [action: add / remove / replace / change]
> [named target] [to what]. Keep everything else exactly as in Image 1: [identity, pose, other
> props, background, lighting, framing]. Image 2 is [subject]'s identity reference only.
> Exclusions: no other changes, no text.

Never say "it" or "that one". Name the target. On 5.5, feed the previous output back in as an
ordinary RGB image (*Official*).

## Region edit with coordinates (5.5 / 5.0 Pro, *Tested* once: it fixed a misplaced quote mark on the round-2 magazine cover)

> In Image 1, replace the mug inside <bbox>412 530 610 760</bbox> with a glass of orange juice.
> Keep everything else unchanged.

Coordinates run 0–999 on both axes, measured from the top-left corner. Use `<point>x y</point>` for
a single spot. With several images, prefix the tag with the image: "Image 2 <bbox>…</bbox>". You
can also draw arrows or boxes on the image and explain them in words: "the red box marks…".

## Transparent asset (5.5, *Tested*)

> A die-cut sticker of [subject], [style], thick white outline. Set a transparent background.

Run with `--background transparent` (the output must be PNG). Our test produced a true RGBA image
with fully transparent corners.

## Icon set or sticker sheet (5.5, *Tested*)

> A set of [n] [app / game / UI] icons for [product], arranged in a clean [rows] by [cols] grid with
> equal spacing, each icon centred in its own cell, for use as separate UI assets. Icons, row by
> row: [list]. Style: one consistent family: [shape language], [outline], [palette with roles],
> same visual weight and same size in every cell, flat vector look. Set a transparent background.
> No grid lines, no labels, no text, no frames around the icons.

Run with `--background transparent --size 1:1`, then
`python scripts/export.py split sheet.png --square --names a,b,c`. *Tested:* 9 weather icons in
one consistent family, cut into 9 files in the right order.

## Translate the text in a finished design (5.5, *Tested*)

> Image 1 is a finished [poster / banner / ad]. Translate only its text into [language], keeping
> each line in the same position, colour, typeface and relative size: "[old]" becomes "[new]"; …
> Keep [the scene, subject, colours, lighting and composition] exactly as in Image 1. Every word is
> spelled exactly as quoted and nothing else is written.

Give the translation yourself, line by line, rather than "translate to Spanish". *Tested:* four
Spanish lines, exact, with longer words refitted into the same layout. Run `export.py merge`
afterwards so the artwork stays pixel-identical.

## Layer decomposition (5.5, *Tested*)

Splits one image into an opaque **base plate** (the scene with the foreground removed and filled
in) plus transparent layers. Each layer has a name, a box and a z-order. With `--ocr`, text
layers also come back with the exact text, a guess at the font, its colour and bold/italic.

```bash
python scripts/seedream.py generate --image poster.png --layers 12 --ocr --size 2K \
  --prompt "Split this poster into editable layers. Name every layer in English."
python scripts/export.py layers out/<name>_layers --original poster.png   # aligned PNGs, SVG, composite
```

What we saw:
- **Poster** (asked for 12, got 11): the title, subtitle, date and venue each became a text layer with
  exact OCR. The lantern strings were split by depth, and the left and right market stalls became
  separate layers. The stack matched the original to 4.5/255.
- **App screen** (asked for 15, got 15): status bar, greeting, avatar, each card, section title
  and tab bar. With 15 slots it ran out before giving "Morning loop" its own text layer. The
  leftover text and two ghost card outlines stayed in the base plate.
- **Layer names:** with an English prompt that didn't mention names, they came back in Chinese.
  Adding "Name every layer in English." gave English names.
- **Billing:** every returned layer is a billed image. 15 layers cost about as much as 15 renders.
  Ask for the number you need: roughly one per element you want to move, plus a few spare.
- **Edges are not studio cut-outs.** Some layers are clipped with a straight edge where the model
  decided the object ends, and glows (lantern light, shadows) come with semi-transparent haze.
  Over the original background you can't see it. Moved onto a new background, you can. Check each
  layer on the viewer's green background. `export.py layers --alpha-floor 48` reduced the haze in our test (see the evidence log),
  and fix hard cuts by hand or re-split with fewer, larger groups.
- **Size:** a layer split accepts only a tier (`1K`, `1.5K`, `2K`); an exact `WxH` is rejected with
  HTTP 400. The returned canvas is slightly larger than the input (1391x3015 for a 1290x2796 screen).
  `export.py layers --original screen.png` scales everything back to the original's exact size.
- The base plate is a clean background for re-layout. Look for leftovers before you build on it.

## Image set or storyboard (5.0 Lite / 4.5 / 4.0 only, *Official*)

Seedream 5.5 cannot return a set. Either call it once per panel, repeating the same character
block word for word, or use an older model:

```bash
python scripts/seedream.py generate --model seedream-4-5-251128 --size 2K --prompt "A series of 4 storyboard panels. Panel 1: … Panel 2: …" \
  --extra '{"sequential_image_generation": "auto", "sequential_image_generation_options": {"max_images": 4}}'
```

- Set `max_images` to exactly the number of panels, because billing is reserved on `max_images`.
- Inputs plus outputs can't exceed 15.

## Keyframe for a video model

> A [aspect ratio] still frame. [Subject] is [doing a specific action at a specific moment], at
> [screen position], [shot size] from [angle] on a [lens]. [Simple background.] [Motivated light
> source.] [Atmosphere.] The frame shows the instant before [the next action], so the motion has
> somewhere to go. Exclusions: no on-screen text, no subtitles.

Use the still as the first frame. For a chain of clips, reuse the last frame of one clip as the
first frame of the next.

## Words that help, and words that don't

| Helps | Doesn't |
|---|---|
| "soft north-window light from the left, cool 5600K" | "beautiful lighting" |
| "85mm lens at f/2, background softly blurred" | "8k, ultra HD, masterpiece" |
| "matte sage-green glaze, unglazed rim" | "high quality product" |
| "the subject sits on the right third, with empty sky on the left" | "nice composition" |

Tag lists still produce good-looking images (*Tested*), but prose is what gives you control over
props, framing and placement.
