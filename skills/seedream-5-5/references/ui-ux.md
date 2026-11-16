# UI and UX design: websites, apps, dashboards, games, kiosks, icons

Seedream 5.5 is good at UI **concepts**: a screen a designer, founder or client can react to, a
pitch-deck visual, a store screenshot, or a starting point to rebuild in Figma. It does not make
working UI. The output is pixels, so for a real product, rebuild the design as code or vectors.

Everything marked *Tested* below was run on Seedream 5.5 in November 2026 (n = 1 each). The images are in
the [evidence log](https://github.com/mazen320/seedream-5-5-skill/blob/main/evidence/README.md#round-3-ui-layers-and-speed).

## What it does well (*Tested*)

| Job | Result |
|---|---|
| Phone app screen (light mode) | Every quoted label exact, layout followed top to bottom, consistent icon family, a believable iOS look |
| Dark mode from the light screen | Every element, position and word kept; only the colours changed |
| Desktop SaaS landing page | Nav, hero, buttons, a product card with a chart and feature cards, all as asked |
| Dark analytics dashboard | Sidebar, KPI cards with sparklines, area chart and donut chart, exact labels |
| Marketing mockup: the app on a phone | The real screen from the reference, legible and undistorted, in a photo scene |
| Icon set (9 icons, transparent) | One consistent family in one render, then cut into 9 files with `export.py split` |
| UI split into layers (with caveats) | 15 named layers (cards, labels, avatar, tab bar) with exact positions. It ran out of slots, so one card's text and two ghost outlines stayed in the base plate. Ask for enough layers |
| Game HUD over gameplay | Portrait, HP/MP bars, quest tracker, minimap, 6 ability slots with keybinds and a cooldown, coin counter: all labels exact |
| Kiosk ordering screen (9:16 touchscreen) | Header, language toggle, category tabs, 4 product cards with food photos and prices, checkout bar: all exact |

## What goes wrong (*Tested*)

- **"Placeholder logos" become real brands.** We asked for "five grey placeholder customer logos"
  and got Airbnb, Notion, X, Slack and Stripe. Never ask for logos you don't supply. Write "five
  plain grey rounded rectangles of different widths, no letters, no symbols, no real brands", or
  pass your client's real logos as references.
- **Filler copy gets invented.** Anything you leave blank gets plausible text: feature card
  sentences, legend values, axis labels, a "Good morning!" greeting. That's fine for a concept,
  but read every word before it goes into a deck. If it must say nothing, write "short grey
  placeholder bars instead of words".
- **Unused canvas stays empty.** On a 16:10 dashboard with little content, the bottom third was
  left blank. Either describe enough content to fill the frame, or choose a ratio that fits it.
- **Small extras on game UI.** The HUD minimap gained an "NNW" label next to the "N" we asked for.
  Zoom in on every corner of a HUD.
- **No device frame unless you ask.** Write "flat front-on screenshot, no phone frame, no hand,
  no perspective" for a screen; ask for the device by name when you want a mockup.

## Prompt template: a screen

> A high-fidelity [mobile app / desktop website / web app dashboard] UI screen, flat front-on
> screenshot (no device frame, no browser chrome, no perspective), for a design review. The
> product is "[Name]", [one line on what it does], [light / dark] mode.
> Layout from top to bottom: [each region in order, with every label in double quotes, its
> alignment and what it contains].
> Style: [platform look, e.g. clean modern iOS / modern SaaS], [grid, e.g. 8-point / 12-column,
> 1200 px content width], rounded corners [n] px, one accent colour [name + hex] on [background hex],
> text [hex], a geometric sans-serif typeface, crisp vector edges, consistent icon stroke weight.
> Every word is spelled exactly as quoted and nothing else is written. No device mockup, no
> watermark, no lorem ipsum, no real brand logos.

Hex colours, a grid and a corner radius are worth including: they read as a spec, and the
output follows them.

## Sizes that match real screens

| Target | `--size` | Notes |
|---|---|---|
| iPhone screen | `1290x2796` | Native 3x iPhone resolution, inside the API's area limit |
| Android phone | `1440x3120` | |
| Desktop web page (above the fold) | `2560x1600` | 16:10; use `2560x1440` for 16:9 |
| Tablet | `1536x2048` | iPad portrait at 2x; native iPad Pro (2048x2732) is over the API limit, so upscale |
| App Store screenshot | `1290x2796` | Then add marketing text in a layout tool |
| Game screen / HUD | `2560x1440` | 16:9; use `1440x2560` for a portrait mobile game |
| Kiosk touchscreen (portrait) | `1440x2560` | Most ordering kiosks are 9:16 portrait at 1080x1920 or larger |
| Digital signage / menu board | `2560x1440` or `1440x2560` | Landscape or portrait screen |

## Games

- **HUD and menus:** describe the gameplay scene underneath (camera, hero, environment), then the
  HUD region by region, as in the screen template. Give every number in quotes ("HP 820/1000",
  keybinds "1", "Q") and name the frame style ("dark slate panels with thin antique-gold trim").
  Add "no real game logos".
- **Inventory icons, skill icons and items:** use the icon-sheet workflow below. Ask for "the
  same lighting direction and outline on every item", one render, then `export.py split`. For
  Unity or Godot, use `--square` and import the PNGs as sprites.
- **Game UI kit pieces** (buttons, panels, frames): put them on one transparent sheet, split
  them, and nine-slice them in the engine. Plain panels with the decoration on the corners slice
  best.
- **Key art and store capsules:** treat them as posters. Keep the title text big, and put the
  rating and platform badges in a layout tool.

## Kiosks, self-service and signage

- Design for distance and touch: say "designed to be read from 60 cm away with big touch targets,
  minimum touch target 88 px, high contrast". The output followed it (*Tested*).
- Give every price exactly ("Classic Stack $9.50"). Seedream copies them, but check each one
  before the screen goes to a store.
- Food photos inside cards came out appetising and consistent. For real menus, swap in your own
  photography or pass it as references.
- For menu boards and signage loops, render each screen with the same style block. For a gentle
  motion loop, hand the still to a video model as a keyframe.

## Workflows

**Screen family** (*untested*). Render the key screen first. Then make each sibling screen with that one as
Image 1: "Image 1 is the home screen of the same app. Create the [settings] screen in exactly the
same visual style: same colours, type, corner radius, icon style and tab bar." Repeat the style
block word for word.

**Dark mode or a theme.** Edit with the screen as Image 1, list the new colour per role
(background, cards, primary text, secondary text, accent), and say "keep every element, position,
size and word exactly as in Image 1". *Tested:* nothing moved.

**Device and marketing mockups.** Pass the screen as Image 1: "a smartphone … its screen showing
exactly the app screen from Image 1, undistorted, with every word legible". *Tested:* the screen
came through sharp. Leave empty space for a headline and set the headline in a layout tool.

**Icon set.** One render with every icon in a grid, plus `--background transparent`, then
`python scripts/export.py split icons.png --square --names a,b,c…`. You get one trimmed PNG per
icon, in reading order. One render keeps the style consistent and costs one image instead of
nine.

**Hand-off to Figma or code.** First choose how. In our tests (round 3), an agent that
**rebuilt** a clean app screen as an SVG did better than one that split it into layers. It
measured every element from the image, drew 67 layers with editable text and vector icons, and
paid for no extra images. The layer split cost 20 billed images, and its text was still pixels.

- **Clean UI** (flat cards, icons, text): rebuild it as SVG, HTML/CSS or SwiftUI from the image.
  Seedream's job ends at the approved screen.
- **Painterly or photographic content** that can't be redrawn (posters, key art, illustrated
  screens, game HUDs over a scene): use the layer split below.
- **Need both:** split with a small N (8–12) to get coordinates and OCR, then rebuild the flat parts
  from `layers.json` and keep only the pictures (photos, maps, illustrations) as images.

To split the screen into layers
(`generate --image screen.png --layers 15 --ocr`), then `export.py layers <folder>`, which writes
`layers.svg`, with one positioned image per element. Design tools that import SVG, such as Figma,
Illustrator and Inkscape, should keep each element as its own layer. We have checked the file,
but not opened it in each app. `layers.json`
lists every element's box, its text and a guess at the font and colour, so a coding agent can
rebuild the screen in HTML/CSS or SwiftUI from real coordinates instead of guessing them from
pixels.

Add `--live-text` to make the SVG's text layers real, editable `<text>` with the OCR'd words, a
guess at the font, the colour and the size (*Tested* on the app screen: every label landed in
place, with a sans-serif fallback where the guessed font wasn't installed). Icons and cards stay as
pictures. For a fully vector screen, have the agent redraw the icons from `layers.json`.

**Website section by section** (*untested*). For a long page, render the hero, the features and the pricing
sections as separate images at the same width, each with the shared style block. One tall image
of a whole page cramps the text.
