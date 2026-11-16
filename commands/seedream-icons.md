---
description: Turn a logo into favicons, PWA icons, an iOS AppIcon set and Android launcher icons, wired into the project
argument-hint: <logo path, or a description to generate one> [background colour]
---

Use the seedream-5-5 skill (read references/project-assets.md, section 5) for: $ARGUMENTS

If no logo file is given, generate a bold, simple mark with `--background transparent` and no text
(it must read at 32 px). Then run `export.py icons <logo> --out <the project's public or icons
folder> --bg <brand background>`. Check the 32 px favicon, add the `<head>` tags from
head-snippet.html to the project's layout, and tell the user where the iOS and Android files go.
