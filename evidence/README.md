# Evidence log

Every rule in this skill is labelled with how much evidence backs it. This page is the evidence.

- **Model:** Seedream 5.5 (`dola-seedream-5-5-261028`) on BytePlus ModelArk.
- **Date:** November 2026.
- **Selection:** one render per test, no re-rolls, no cherry-picking.
- **Sidecars:** each image has a `.txt` sidecar next to it with the exact prompt and parameters.

> **About the sidecars:** they were written by an earlier version of the helper script, so the format
> differs slightly from what the current script writes. Their reference hashes point at full-size
> originals that aren't in the repo; the images here are web-sized copies. In edit-chain rounds 2–3,
> the identity reference was attached without the stated role the skill recommends.
>
> n = 1 per test. These are spot checks, not benchmarks. They are enough to show that a rule can fail
> or can hold, but not enough to give a failure rate. Re-run them yourself; if your results differ, open
> an issue.

## Summary

| Claim we started with | Test | Result | Verdict |
|---|---|---|---|
| Rows of identical objects drift | A row of 12 identical bottles | 12 bottles, all uniform | ❌ Not reproduced (simple scene) |
| ″ | A 3×3 grid of identical teapots in a busy market stall | The count was right (9), but 4 of the 9 were a different design | ⚠️ **Uniformity breaks before count, in complex scenes** |
| More than 2 people cause identity bleed | 3 people described in text | All 3 distinct | ❌ Not reproduced |
| ″ | 3 people, each from their own reference image | All 3 identities kept | ❌ Not reproduced |
| ″ | A busy café with 5 described people | All 5 distinct. Placement mostly right (the woman "at the window table" sat at a back table) | ❌ Not reproduced |
| References leak backgrounds unless told to ignore them | A bear from a room photo, placed on a beach, prompted with and without "ignore …" | Neither version leaked | ❌ Not reproduced (single reference) |
| Avoid negatives and describe positively | "No people, no umbrellas, no boats" vs "completely empty beach" | Both versions obeyed | ❌ Negatives work |
| Hard exclusions hold | The busy café with "no other people, no other text" | People walking past outside the window, plus two extra chalkboard menus full of writing | ⚠️ **Exclusions leak in busy scenes** |
| One-off asymmetric details hold | A one-eyed bear, one earring, one antenna, one eyepatch | Exactly one of each, every time | ✅ The **count** holds |
| Naming the side puts a one-sided detail there | Earring ("image-left ear"), antenna ("image-right side"), button eye ("toy's left"), and 2 eyepatches ("his own left eye") | Earring, antenna and button eye mirrored; both eyepatches correct | ⚠️ **3 in 6 mirrored.** Check, and mirror-flip if wrong. Layout positions (barista, light, seating) held every time |
| Edit chains drift | 3 one-change edits in a row (scarf, then beanie, then glasses) | The face was essentially unchanged; only the bear shifted slightly | ✅ Stable over 3 rounds |
| Prose beats keyword soup | The same city scene written as tags and as prose | Both looked good; prose controlled the umbrella, the framing and the props | ⚠️ Prose = **control**, not quality |
| Long prompts lose detail | About 230 words vs about 60 words | The long prompt followed almost every detail; the short one invented the rest | ✅ **Longer = more control** (the official limit is about 600 English words) |
| Exact text renders | A poster, a chalkboard, a banner title, an infographic, Chinese calligraphy | Every string was exact | ✅ Holds (Chinese added red seal stamps nobody asked for) |
| Minimum size is 921,600 px | A 1024x768 request | HTTP 400 "at least 921600" | ✅ Confirmed |
| Maximum size | A 4096x4096 request | HTTP 400 "at most 4624220" | ✅ **Max area 4,624,220 px** |
| 9:16 works | 1440x2560 | Rendered | ✅ |
| Transparent output (`background: transparent`) | A lemon sticker | A true RGBA PNG: corner alpha 0, centre alpha 255 | ✅ Works ([image](../assets/gallery/transparent.png)) |

## Images

### Counting and uniformity
| 12 bottles (uniform) | 3×3 teapots (count right, design drifts) |
|:-:|:-:|
| [<img src="img/rows.jpg" width="420">](img/rows.txt) | [<img src="img/c_grid.jpg" width="300">](img/c_grid.txt) |

### People and identity
| 3 described people | 3 from references | Busy café, 5 people |
|:-:|:-:|:-:|
| [<img src="img/three_people.jpg" width="280">](img/three_people.txt) | [<img src="img/c_threerefs.jpg" width="280">](img/c_threerefs.txt) | [<img src="img/c_cafe.jpg" width="280">](img/c_cafe.txt) |

### Left/right placement (fails)
| Asked: earring on the **image-left** ear | Asked: antenna on the **image-right** side |
|:-:|:-:|
| [<img src="img/asym1.jpg" width="300">](img/asym1.txt) | [<img src="img/asym2.jpg" width="300">](img/asym2.txt) |

### Reference leakage
| Without an "ignore" clause | With an "ignore" clause |
|:-:|:-:|
| [<img src="img/leak_noignore.jpg" width="380">](img/leak_noignore.txt) | [<img src="img/leak_ignore.jpg" width="380">](img/leak_ignore.txt) |

### Negatives vs positive framing
| "No people, no umbrellas, no boats" | "Completely empty and deserted" |
|:-:|:-:|
| [<img src="img/neg_word.jpg" width="380">](img/neg_word.txt) | [<img src="img/neg_pos.jpg" width="380">](img/neg_pos.txt) |

### Keyword soup vs prose
| Tags | Prose |
|:-:|:-:|
| [<img src="img/soup.jpg" width="380">](img/soup.txt) | [<img src="img/prose.jpg" width="380">](img/prose.txt) |

### Long vs short prompt
| About 230 words | About 60 words |
|:-:|:-:|
| [<img src="img/c_long.jpg" width="300">](img/c_long.txt) | [<img src="img/c_short.jpg" width="300">](img/c_short.txt) |

### Edit chain, rounds 2–3 (round 1 is in the main gallery)
| + beanie | + glasses |
|:-:|:-:|
| [<img src="img/edit2.jpg" width="380">](img/edit2.txt) | [<img src="img/edit3.jpg" width="380">](img/edit3.txt) |

### Text
| Infographic with exact numbers | Chinese calligraphy poster | 9:16 |
|:-:|:-:|:-:|
| [<img src="img/c_infographic.jpg" width="320">](img/c_infographic.txt) | [<img src="img/c_chinese.jpg" width="220">](img/c_chinese.txt) | [<img src="img/tall.jpg" width="160">](img/tall.txt) |

## Round 2: hard tasks, with the skill vs without it

There are 4 hard tasks. Each one was run by an agent with the skill and by an agent without it,
both pinned to Seedream 5.5, and graded on 25 checks.

| | With skill | Without skill |
|---|---|---|
| Checks passed | **25 / 25** | 24 / 25 |
| Renders used | **10** | 12 |
| Where it differed | Fixed a duplicated cover line and a misplaced quote mark with region edits | Added a barcode with invented digits to the cover. Its product ad looks cleaner, though: no headline band, and the dripper sits properly in the mug |

| Test | What Seedream 5.5 did |
|---|---|
| **Precision edit:** swap the croissant for cake, rewrite the chalkboard, remove the cat | All three were exact in one render. It also re-rendered the whole frame with faint noise, so only the changed regions were pasted back (`export.py merge`) |
| **3-step edit chain:** snow, then a beanie, then a mug | Each step built on the last, and the girl's identity and the one-eyed bear held through all 3 |
| **Product ad from 2 references** (product + person) | The product and the person came through faithfully and the text was exact. It invented a saucer under the dripper, which a one-change edit removed |
| **Magazine cover with 5 text elements** | Magazine-grade. The first render printed one cover line twice; region edits fixed it |

| Before | Precision edit | Edit chain, step 3 |
|:-:|:-:|:-:|
| [<img src="img/r2_cafe_original.jpg" width="300">](img/r2_cafe_original.jpg) | [<img src="img/r2_cafe_edit.jpg" width="300">](img/r2_cafe_edit.txt) | [<img src="img/r2_chain3.jpg" width="300">](img/r2_chain3.txt) |

| Product ad (2 references) | Magazine cover, first render | Magazine cover, after 2 region edits |
|:-:|:-:|:-:|
| [<img src="img/r2_ad.jpg" width="240">](img/r2_ad.txt) | [<img src="img/r2_cover_v1.jpg" width="240">](img/r2_cover_v1.txt) | [<img src="img/r2_cover.jpg" width="240">](img/r2_cover.txt) |

New failure modes from this round, now in the skill:
- an edit re-renders the whole frame;
- text gets duplicated;
- extras get invented (a barcode, a saucer);
- objects perch instead of sitting in place;
- a hard-edged band appears behind headlines.

## Round 3: UI, layers and speed

Live spot checks of jobs the first two rounds didn't cover. n = 1 each unless stated.

| Test | Result | Verdict |
|---|---|---|
| Phone app screen with 20 exact labels | Every label exact, and the layout followed top to bottom | ✅ |
| Dark mode from the light screen (as Image 1) | Every element, position and word kept; only the colours changed | ✅ |
| Desktop SaaS landing page | Convincing, every quoted word exact. **"Grey placeholder logos" came back as Airbnb, Notion, X, Slack and Stripe** | ⚠️ **Real trademarks** |
| Dark analytics dashboard | Exact labels. Added legend values and axis labels we didn't ask for, and left the bottom third empty | ⚠️ Invented copy |
| The app on a phone, from the screenshot | Screen reproduced legibly in a photo scene | ✅ |
| 9 icons on one transparent sheet, then `export.py split` | One consistent family, cut into 9 files in reading order | ✅ |
| Poster text translated to Spanish | All 4 lines exact; longer words refitted | ✅ |
| **Layer split**, poster (asked for 12) | 11 layers: 4 text layers with exact OCR and font guesses, lantern strings split by depth, the stalls as separate groups, plus a clean base plate. The re-stack matched the original to 4.5/255 | ✅ Works. ⚠️ Edges: a hard clipped edge on one stall, and glow haze around distant lanterns |
| **Layer split**, app screen (asked for 15, English names) | 15 named layers (cards, labels, avatar, tab bar). It ran out of slots: one card's text and two ghost card outlines stayed in the base plate | ⚠️ Pick the layer count deliberately; each layer is billed |
| Game HUD over a gameplay scene | Bars, quest tracker, minimap, 6 ability slots with keybinds and a cooldown, all exact. The minimap added an "NNW" label we didn't ask for | ✅ (one small extra) |
| Kiosk ordering screen, 9:16 | Tabs, 4 product cards with prices, language toggle and checkout bar, all exact; big touch targets | ✅ |
| 32:9 stage LED wall at 3584x1008 | Logotype, date and hashtags exact; centre kept clean | ✅ |
| Speaker badge with a QR placeholder | Name, role, company and tag exact; the placeholder stayed a plain grey square | ✅ |
| `export.py layers --original --live-text` on the app split | Scaled back to exactly 1290x2796; every OCR'd label became editable SVG text in the right place and size ([render](img/r3_live_text.jpg): original left, SVG right). Guessed fonts that aren't installed fall back to sans-serif | ✅ |
| Speed: same prompt at 1K and 2K, 3 runs each ([raw times](img/r3_speed_timing.txt)) | 1K averaged 24 s, 2K averaged 27 s. Layer splits took 49–61 s | ⚠️ 1K saves money, not time |

| App screen | Dark mode from it | The app on a phone |
|:-:|:-:|:-:|
| [<img src="img/r3_ui_app.jpg" width="200">](img/r3_ui_app.txt) | [<img src="img/r3_ui_dark.jpg" width="200">](img/r3_ui_dark.txt) | [<img src="img/r3_ui_mockup.jpg" width="380">](img/r3_ui_mockup.txt) |

| Landing page (note the real logos) | Dashboard |
|:-:|:-:|
| [<img src="img/r3_web_landing.jpg" width="400">](img/r3_web_landing.txt) | [<img src="img/r3_web_dashboard.jpg" width="400">](img/r3_web_dashboard.txt) |

| Layer split: original, base plate, foreground layers on green | App screen: base plate, layers on green, re-stacked |
|:-:|:-:|
| [<img src="img/r3_layers_poster.jpg" width="420">](img/r3_layers_poster.txt) | [<img src="img/r3_layers_ui.jpg" width="420">](img/r3_layers_ui.txt) |

| Game HUD | Kiosk | Badge |
|:-:|:-:|:-:|
| [<img src="img/r3_game_hud.jpg" width="420">](img/r3_game_hud.txt) | [<img src="img/r3_kiosk.jpg" width="160">](img/r3_kiosk.txt) | [<img src="img/r3_event_badge.jpg" width="160">](img/r3_event_badge.txt) |

[<img src="img/r3_event_stage.jpg" width="840">](img/r3_event_stage.txt)

| Edge close-up on green (hard cut, haze) | Same, after `--alpha-floor 48` (haze reduced, hard cut remains) | Icon sheet, then split into 9 files | Spanish poster |
|:-:|:-:|:-:|:-:|
| <img src="img/r3_layers_edges.jpg" width="240"> | <img src="img/r3_layers_alpha_floor.jpg" width="240"> | [<img src="img/r3_icons.png" width="200">](img/r3_icons.txt)<br><img src="img/r3_icons_split.jpg" width="300"> | [<img src="img/r3_poster_es.jpg" width="200">](img/r3_poster_es.txt) |

## Rounds 3 and 4: with the skill vs without it, on new kinds of task

Six tasks: a website hero with a logo strip, dark mode plus a Figma hand-off, game item icons,
one launch image in three social sizes, a fal request without spending, and a poster translated
into two languages. Each was run by an agent with the skill and one without, both on Seedream 5.5.

| | With skill | Without skill |
|---|---|---|
| Round 3 checks | 39 / 41 | **41 / 41** |
| Round 3 billed images | 31 (22 of them on the layer split) | **9** |
| Round 4 (the 4 tasks re-run with the fixed skill; without-skill runs reused from round 3) | 28 / 28, 6 images | 28 / 28, 5 images |

**What the skill got wrong in round 3, and the fix:**
- **fal:** it said fal had no Seedream 5.5. The agent without the skill checked fal's live schema
  and found `v5.5` endpoints. The provider table is now updated, and the skill now says to check
  live model lists.
- **Figma hand-off:** it used a 20-layer split (pixels, 20 billed images). The agent without the
  skill rebuilt the screen as an SVG with editable text for free. The skill now says to rebuild
  clean UI, and to split only painterly or photo content.
- **Social sizes:** re-rendering the 4:5 version from the banner produced a two-panel seam and
  then an extra bun. Rendering the tall version with the banner as Image 1 and cropping 4:5 from
  it now takes fewer renders.
- **Placeholder copy:** grey bars in place of a subline looked unfinished. The skill now says to
  write plausible copy and flag it.

**What the skill did better:** native transparent icons in 1 render. The agent without the skill
didn't know Seedream 5.5 can output transparency, chroma-keyed a magenta background, and needed
a second render.

## Round 5: a project asset kit from one manifest

`seedream.py batch` with a style file and four assets (21:9 hero, 1200×630 link preview,
transparent empty state, transparent logo mark), then `export.py icons`. 4 images in 31 s in
parallel, about $0.14. The re-run reported "4 up to date" and spent nothing. All four share one
style. The logo mark is too detailed for a 32 px favicon. Then, with the manifest moved to
`.seedream/assets.json`, we edited one prompt (the empty state, to "a single object, no background
tile"): the batch reported "3 up to date, 1 to generate", kept the file name, and the new image was a
free-floating object ([image](img/r5_empty-trips_v2.png)). See
[examples/04-project-asset-kit.md](../examples/04-project-asset-kit.md).

| Hero | Link preview (1200×630) | Empty state | Logo mark |
|:-:|:-:|:-:|:-:|
| [<img src="img/r5_hero.jpg" width="300">](img/r5_hero.txt) | [<img src="img/r5_og-image.jpg" width="220">](img/r5_og-image.txt) | [<img src="img/r5_empty-trips.png" width="140">](img/r5_empty-trips.txt) | [<img src="img/r5_logo-mark.png" width="140">](img/r5_logo-mark.txt) |

## Round 6: editing

Nine kinds of edit, each run once on Seedream 5.5, with the original as Image 1 and a named
keep-list. The recipes are in [`editing.md`](../skills/seedream-5-5/references/editing.md). In each
pair below, the left image is the input and the right is the output.

| Edit | Result |
|---|---|
| Background swap (product) | ✅ Product unchanged |
| Colour change (glaze) | ✅ Exact; rim and shadows kept |
| Relight (blue hour + lamp) | ✅ Person kept; it added a visible lamp |
| Restore + colourise an old photo | ✅ Same person; colours are a guess |
| Edit by drawing red marks | ✅ Kitten in the circle, marks erased |
| Remove passers-by | ✅ Customers and chalkboard kept |
| Restyle as watercolour | ✅ Layout kept; one extra patch on the bear |
| Sketch to photo | ✅ Layout followed |
| Outpaint 2:3 → 16:9 | ❌ A poster inside a picture. Fixed with "no inset panel" (✅, lettering moved), or best, a blurred padded canvas (✅, layout kept) |

| | |
|:-:|:-:|
| [<img src="img/r6_bg.jpg" width="400">](img/r6_bg.txt) | [<img src="img/r6_recolor.jpg" width="400">](img/r6_recolor.txt) |
| [<img src="img/r6_relight.jpg" width="400">](img/r6_relight.txt) | [<img src="img/r6_restore.jpg" width="400">](img/r6_restore.txt) |
| [<img src="img/r6_markup.jpg" width="400">](img/r6_markup.txt) | [<img src="img/r6_remove.jpg" width="400">](img/r6_remove.txt) |
| [<img src="img/r6_style.jpg" width="400">](img/r6_style.txt) | [<img src="img/r6_sketch.jpg" width="400">](img/r6_sketch.txt) |
| [<img src="img/r6_outpaint.jpg" width="400">](img/r6_outpaint.txt) ❌ | [<img src="img/r6_outpaint3.jpg" width="400">](img/r6_outpaint3.txt) ✅ padded canvas |
