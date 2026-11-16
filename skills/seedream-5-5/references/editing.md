# Editing images: a playbook

Seedream 5.5 edits by instruction. You pass the image as Image 1 and say what to change and what to
keep. There is no mask parameter. You point at things with words, with `<bbox>` coordinates, or by
drawing marks on the image. Every recipe below was run on Seedream 5.5 (November 2026, n = 1 each)
unless marked otherwise. Before/after images are in the
[evidence log](https://github.com/mazen320/seedream-5-5-skill/blob/main/evidence/README.md#round-6-editing).

## The formula

> Image 1 is [what it is]. [Action] only [the exact target] [to the new state]. Keep [everything
> else, listed by name] exactly as in Image 1.

- **Name the target precisely.** Write "the glaze of the dripper", not "it" or "the colour".
- **List what to keep.** The model keeps what you name. "Keep the rest" is weaker than naming the
  face, pose, clothes, background, lighting, framing and text.
- **Make one change per edit** when precision matters. Three named changes in one edit worked in
  our café test, but each extra change adds risk.
- **Use the same `--size` ratio as the input**, or the frame gets reshaped.
- **Every edit redraws the whole frame** (faint noise everywhere). Run
  `export.py merge original.png edited.png` afterwards, so only the changed areas are new and the
  rest stays pixel-identical.

## Recipes

| Job | What we asked | Result |
|---|---|---|
| **Background swap** (product) | Wet black slate, night kitchen, pendant light; keep the dripper's shape, glaze, rim, holes, size, position and angle | ✅ Product unchanged, new scene with a believable reflection |
| **Colour change** | Glaze from sage to cobalt; keep the raw rim and everything else | ✅ Exact. Rim, highlights, shadows and background untouched |
| **Relight** | Blue-hour window plus a warm lamp from the right; keep face, pose, objects and framing | ✅ Mood changed, person and studio kept. It added a visible lamp to justify the light |
| **Restore and colourise an old photo** | Remove scratches, rebuild the torn corner, sharpen, natural colour; keep identity and age, no beautifying | ✅ Clean, sharp and natural, same person. Colours are a guess (the clay came out grey), so give known colours if they matter |
| **Edit by drawing on the image** | A red circle and arrow: "add a sleeping kitten inside the red circle, then remove every red mark" | ✅ Kitten placed in the circle, marks erased, nothing else changed |
| **Remove things** | The people walking past outside a café window; fill with the empty street | ✅ Passers-by gone; the customers, barista and chalkboard kept |
| **Restyle** | The photo redrawn as a watercolour children's-book page; keep the composition and the one-eyed bear | ✅ Same layout and characters. It added a second patch to the bear, so check small details |
| **Sketch to image** | A rough line sketch, rendered as a photoreal home office following its layout | ✅ Window, desk, laptop, mug and plant all where the sketch put them |
| **Extend the canvas** (outpaint 2:3 → 16:9) | "Extend into a wide 16:9 banner" | ❌ It made a **poster inside a bigger picture**: the original as a framed panel in the middle |
| ″ with a better prompt | "One single continuous illustration … no frame, no border, no inset panel, no poster-within-a-poster" | ✅ Seamless, but the lettering was re-laid out |
| ″ with a padded canvas (best) | `export.py --fit pad --pad-color blur` first, then "fill the blurred areas by continuing the scene; keep the centre strip exactly" | ✅ Seamless, and the original layout and text placement were kept |

Earlier rounds also tested, and they held:
- a 3-step edit chain (snow, then a beanie, then a mug) with the characters unchanged;
- a 3-change precision edit (swap, rewrite, remove);
- a `<bbox>` region edit that fixed one quote mark on a magazine cover;
- translating a poster's text (see `prompting.md`).

## How to point at a region

| Method | When | Prompt |
|---|---|---|
| Words | The target is unique and easy to name | "the croissant on the centre table" |
| `<bbox>x1 y1 x2 y2</bbox>` | Small or repeated things; text fixes | Coordinates on a 0–999 grid of the image: "the pull quote at `<bbox>35 405 380 520</bbox>`" |
| Drawn marks | The user can show you, or you can draw them (Pillow) | "Image 1 has red marks drawn on it as instructions … then remove every red mark" |

Drawing marks is the most intuitive way for users. Draw a thick red circle, arrow or scribble with
Pillow, send that image, and always end with "remove every red mark completely".

## Outpainting (extend the canvas)

```bash
python scripts/export.py poster.jpg --size 2560x1440 --fit pad --pad-color blur --out work
python scripts/seedream.py generate --image work/poster_2560x1440.jpg --size 2560x1440 --name banner \
  --prompt "Image 1 is a wide canvas: the centre strip is a finished poster, and the blurred grey areas on the left and right are empty space to be filled. Fill them by continuing the scene outward in the same style, colours and lighting, so it reads as one seamless wide image with no seams, frames or borders. Keep the centre strip exactly as it is, including its lettering. Write no new text."
python scripts/export.py merge work/poster_2560x1440.jpg out/banner.png   # keep the centre pixel-identical
```

Asking for "extend to 16:9" on the original image alone tends to produce a framed panel (*Tested*).

## People and faces

- **Identity holds** across relighting, restoration, a 3-step chain and restyling (*Tested*).
- **Avoid "beautify", "younger" and "slimmer"** unless that's the actual brief. Say "keep her
  features, age and skin texture exactly".
- **Real people in reference photos** can trip the safety filter. State the context ("restoring a
  family photograph", "editing our own staff photo for the website").
- **Restoration and colourisation guess colours.** Give the known ones: "her cardigan was navy,
  the clay is terracotta".

## Products

- Give the product's role as Image 1: "keep its exact shape, colour, logo and proportions".
- Background swaps and colour changes are reliable (*Tested*). Check small details: hole counts,
  label text and the logo.
- Exclude genre props by name: "no saucer, no plate, no extra beans" (failure mode 13).
- For catalogue sets, change one attribute at a time (colourways, backgrounds) from the same
  master, then `merge`.

## When an edit goes wrong

| Symptom | Fix |
|---|---|
| Things you didn't mention changed | Name them in the keep-list, then `merge` |
| The change spread too far | A `<bbox>` or a drawn circle around the target |
| A text typo or duplicated line | A small region edit on that line only, not a full regeneration |
| Tiny invented extras (a patch, a seal, a barcode) | Exclude each one by name and re-run that one edit |
| The frame shape changed | Pass the input's exact ratio, or its WxH, with `--size` |
| Each round gets noisier | Edit the last *merged* image, not the raw output |
