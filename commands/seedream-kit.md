---
description: Generate a consistent set of images for this project (hero, OG card, illustrations, icons) into the right folders
argument-hint: what the project needs, e.g. "landing page: hero, 3 feature images, OG card, favicons"
---

Use the seedream-5-5 skill (read references/project-assets.md) to build an image kit for this
project: $ARGUMENTS

1. Find where this project keeps images (public/, static/, Assets/, Assets.xcassets...).
2. If there is a logo or existing imagery, run `export.py style` on it; otherwise write
   `.seedream/style.md` from what the user asked. Keep one look for the whole set.
3. Write `.seedream/assets.json` and run `seedream.py batch` without --yes. Show the user the plan
   and the estimated cost, and wait for their go-ahead before running it with --yes.
4. Make icons with `export.py icons` when a logo or favicon is part of the kit.
5. Look at every image, fix what's wrong with one targeted re-run, wire the files into the project
   (img tags with alt text, OG meta, manifest link), and report files and cost (`seedream.py costs`).
