---
description: Edit an existing image with Seedream 5.5 (swap, remove, relight, restore, restyle, outpaint) and keep untouched pixels original
argument-hint: <image path> what to change, e.g. "photo.jpg remove the people in the background"
---

Use the seedream-5-5 skill (read references/editing.md) to make this edit: $ARGUMENTS

Use the edit formula: name the exact target, the change, and list everything to keep. Match the
input's aspect ratio. For a region, use a `<bbox>` or draw a red mark on a copy of the image. To
extend the canvas, pad with `export.py --fit pad --pad-color blur` first. After the edit, run
`export.py merge original edited` so only the changed areas are new, then check the result and
report what changed.
