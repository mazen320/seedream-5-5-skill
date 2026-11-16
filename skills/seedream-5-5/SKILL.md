---
name: seedream-5-5
description: Generate and edit images with ByteDance Seedream 5.5 on BytePlus ModelArk, and write prompts that work for it. Use when the user asks to create, edit, restyle or combine images with Seedream, ByteDance or BytePlus ModelArk (text-to-image, image-to-image, multiple reference images, keeping a character or product consistent, posters with exact text, product shots, infographics, storyboards or keyframes for a video model), when they need the Seedream model ID, or when they are debugging bad Seedream output. Not for SVG, vector, HTML or code-native graphics.
license: MIT
compatibility: Requires Python 3.8+, network access to BytePlus ModelArk, and the user's own key in the ARK_API_KEY environment variable.
metadata:
  version: "1.0.0"
  model-id: "dola-seedream-5-5-261028"
---

# Seedream 5.5

Turn the user's intent into a Seedream prompt, run it through `scripts/seedream.py`, check
the result against the brief, and fix one thing at a time.

## Rules that always apply

- **The key belongs to the user and stays in `ARK_API_KEY`.** Never ask for it in chat, and
  never write it to a file, a flag, a prompt or a commit. If it is missing, give the export
  command (below) and stop.
- **Never overwrite outputs.** Each run writes new files. The script adds `_2`, `_3` and so on.
- **Never switch the model ID silently.** If the default fails, run `models` and tell the user
  what you found.
- **Report back** the file paths, the prompt you used and the size. The sidecar `.txt` next to
  each image is the full record.
- Run the script from the user's working directory, so relative paths refer to their files.

```bash
export ARK_API_KEY=...          # bash / zsh
$env:ARK_API_KEY = '...'        # PowerShell
```

## Quick reference

```bash
S=<this-skill-dir>/scripts/seedream.py
python $S models                                               # find Seedream model IDs for this key
python $S generate --prompt "..." --size 16:9 --out out --name hero
python $S generate --prompt-file p.txt --image a.png --image b.jpg --size 2:3 --out out
python $S generate --prompt "..." --dry-run                    # print the request; no key, no cost
```

- **Size:** `16:9` (2560x1440), `9:16`, `2:3` (1728x2592), `3:2`, `1:1` (2048x2048), or any
  `WxH` with an area of at least **921,600 px**.
- **References:** repeat `--image` to add more. The order you give them is **Image 1, Image 2
  and so on**.

Full API details are in [references/api.md](references/api.md).

## Decide the mode

| The user has… | Mode | What the prompt must do |
|---|---|---|
| Only an idea | Text-to-image | Follow the prompt structure below |
| One image to change | Edit | State the change first, then everything to keep |
| Several images to combine | Multi-reference | Give each image a role: what to take from it and what to ignore |
| A previous output to refine | Multi-round edit | Use the last output as Image 1 and change one thing per round |

## Prompt structure

Write **prose, not keyword lists**, in this order:

1. **Deliverable.** What kind of image it is: a photo, a poster, a product shot, an
   infographic, a film still.
2. **Subject.** Two or three specific physical details.
3. **Layout.** Where things sit in the frame, the foreground and background, and any empty
   space left for copy.
4. **Materials and textures.**
5. **Lighting.** The source, its direction, quality and colour.
6. **Camera.** Shot size, angle, lens, depth of field.
7. **Style and grade.**
8. **Exact text**, if any. Put every character in quotes and say what it is printed on, where
   it sits, and in what hierarchy.
9. **Exclusions.** One last line of hard "no"s.

Describe what should be in the image ("a clean, empty sky") rather than what shouldn't. Keep
the "no"s for that final exclusions line. Use concrete visual facts, not prestige words like
"8k", "masterpiece" or "award-winning".

**Reference roles** (always state them):
> Image 1 provides the product's exact shape, colour and logo; ignore its background.
> Image 2 provides only the lighting and colour grade.

**Edits** (repeat the keep-list every round, because drift adds up):
> Image 1 is the current image. Change only the jacket from grey wool to red leather. Keep the
> face, pose, hair, background, framing and lighting exactly as in Image 1.

Ready-made templates for photoreal, product, poster, infographic, character sheet, edit and
video-keyframe images are in [references/prompting.md](references/prompting.md).

## Check before you spend a render

- **Asymmetric details** (one eye, one sleeve, a scar on one side) drift toward symmetry.
  Name the side and what replaces the missing part, then repeat it in the exclusions.
- **Rows of identical objects** come out with the wrong count or uneven shapes. Generate one
  object and duplicate it in an editor.
- **More than two identifiable people** makes faces and costumes blend together. Keep to two,
  give each one their own reference, and place them by screen position.
- **Text that will later be animated** by a video model wobbles and melts. Leave it out and
  add it in post.
- **Long edit chains** slowly lose identity. Attach the original image again as an "identity
  only" reference.

Symptoms and fixes are covered in more depth in
[references/failure-modes.md](references/failure-modes.md).

## Workflow

1. Get the goal, where the image will be used, the aspect ratio and any references. Ask once.
2. Check the key with `models`. Never ask for the key itself.
3. Pick the mode and template, write the prompt, assign the reference roles, and choose a size.
4. Run the pre-flight check above.
5. Generate with a meaningful `--name`. Use `--dry-run` first if the request is unusual.
6. Look at the image and compare it to the brief clause by clause. Fix it with a one-change
   edit, not a full rewrite.
7. Report the paths, the prompt and the size.
