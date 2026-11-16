# Failure modes and fixes

Check the brief against this list **before** you generate. Each entry carries an evidence label:

- **Tested**: we ran it on Seedream 5.5 and saw the result. See the [evidence log](https://github.com/mazen320/seedream-5-5-skill/blob/main/evidence/README.md) (n = 1 per test, so treat these as spot checks).
- **Official**: stated in the ByteDance ModelArk / Volcengine docs.
- **Reported**: comes up repeatedly in public reviews or production use, but we have not reproduced it.

---

## 1. One-sided details can come out mirrored. *Tested*

**Symptom:** a detail on one side of a face or body (an eyepatch, an earring, a single antenna, a
button eye) lands on the other side. In our runs this happened **3 times in 6**:
- an earring asked for on the "image-left ear" landed on the right;
- an antenna asked for on the "image-right" side landed on the left;
- a button eye asked for on "the toy's left" landed on the viewer's left.

Two eyepatch frames ("his own left eye") came out correct, and so did a knee patch on "the left knee".
No wording we tried was reliable.

**What does hold** (*Tested*):
- **Layout positions:** "barista on the image-left", "sunlight from the image-right", "she sits on
  the image-left" and "framed on the right third" were all followed in 6+ renders.
- **The count** of one-off details: one eye, one earring, one antenna and one eyepatch stayed one
  each, when named and repeated in the exclusions ("exactly one gold hoop earring … Exclusions: no
  second earring").

**Fix:**
- If the side matters, give it both ways: "his own left eye, which is on the right of the image
  when he faces the camera".
- **Check the result.**
- If it's wrong, **mirror-flip the finished image**. This is safe when the image has no text.
- Or supply a reference that already has the detail on the right side, and write "exactly where it
  is in Image 1".

## 2. Exclusions leak in busy scenes. *Tested*

**Symptom:** In a crowded scene, the model adds the things you excluded at the edges. In our café
test, under "no other people, no other text", it added passers-by outside the window and two extra
chalkboard menus covered in writing.

**Fix:**
- Fewer competing elements per frame.
- Fill the edges deliberately, for example "the window shows an empty street".
- Clean up the final image.

In simple scenes the exclusions held (*Tested*).

## 3. Repeated objects: the count holds, the sameness doesn't. *Tested* / *Reported*

**Symptom:** You ask for identical items in a complex arrangement, such as a 3×3 grid of teapots in
a busy stall. The count comes out right (9), but 4 of the 9 teapots are a different design. A simple row of 12
identical bottles came out perfect (*Tested*). Production users report drift in counts and
layouts (*Reported*).

**Fix:**
- For a simple row, just ask for it.
- If every item must be identical (catalogue or packaging work), generate **one** hero item and
  duplicate it in an editor.
- If some variation is acceptable, ask for a "loose, natural arrangement".

## 4. Text in an image melts once it's animated. *Reported*

**Symptom:** Text in a still is clean. Once an image-to-video model (Seedance, Kling and others)
animates the frame, the letters wobble or change, because the video model redraws them on every
frame.

**Fix:**
- For frames headed to video, add `no text` to the exclusions and put titles and signs on in compositing.
- If text has to be in the shot, keep it large, flat and facing the camera, and lock off the camera
  in the video prompt.

## 5. Small, dense or long text breaks. *Reported* / *Official*

**Symptom:** Large headlines and short labels render exactly (*Tested*: a poster, a chalkboard, an
infographic and a Chinese calligraphy poster). Small print, long paragraphs and fine English
typography are the most common text complaint (*Reported*). ByteDance acknowledges small-text
limits for 5.0 Pro (*Official*).

**Fix:**
- Put every string in double quotes.
- Keep lines short.
- State where the text goes, how it is aligned and how big it is relative to other text.
- Add "every word is spelled exactly as quoted and nothing else is written".
- Fine print, prices and legal text go in a layout tool.

**Also:** Chinese prompts asking for Chinese calligraphy added red seal stamps nobody asked for
(*Tested*). Exclude them explicitly if that matters.

## 6. Square output, or the wrong aspect ratio. *Reported* / *Official*

**Symptom:** You get a square image when you wanted 16:9, or the output ignores the input image's
shape.

**Cause and fix:**
- Always send an explicit size: `WxH`, or a preset plus the ratio written in the prompt (*Official*).
- If you leave `size` out, the default is a square 2K image.
- Some third-party platforms use `aspect_ratio` / `image_size` fields instead. The helper script
  converts for you.

## 7. Edits change things you didn't ask to change. *Reported*

**Symptom:** A product's shape or colour shifts, furniture moves, or the edit spills into nearby
areas.

**What we saw:** over 3 one-change edits, the face stayed the same and only a prop moved slightly
(*Tested*). ByteDance claims 5.5 stays stable over 100 rounds (*Official claim, not verified*).

**Fix:**
- Make one change per round.
- Name the target exactly and never use "it" or "that one".
- Repeat the full keep-list every round.
- Use the last accepted output as Image 1, and re-attach the original as an "identity reference
  only".
- For precise areas, use `<bbox>` / `<point>` tags (see `prompting.md`).

## 8. Safety filter false positives. *Reported* / *Official*

**Symptom:**
- HTTP 400 `InputTextSensitiveContentDetected`, `OutputImageSensitiveContentDetected` or
  `…PrivacyInformation` on legitimate work.
- Swimwear, lingerie, medical and fitness shots are the usual triggers.
- The same prompt can pass on one run and fail on the next, because the output is checked too.

**Fix:**
- Use neutral wording ("fitted", "athletic"; not "tight", "sexy").
- State the business context ("an e-commerce catalogue photo").
- Frame wider.
- Avoid reference photos of real, identifiable people. Public-figure look-alikes are blocked by
  design (*Official*).

Requests the filter rejects are not billed (*Official*).

## 9. A plastic, "AI glamour" look. *Reported*

**Symptom:** Skin is too smooth, the lighting looks like stock photography, and the result looks
generic, mostly from vague prompts.

**Fix:**
- Name concrete light, lens and texture ("visible pores", "soft north-window light", "50mm
  f/2.8", "fine film grain").
- Users report that 4.5 renders skin more naturally than 5.0 Pro.

## 10. Short prompts make the model guess. *Tested*

**Symptom:** Anything left out gets invented. In our test, a 60-word prompt produced a black chef's
jacket, which we never asked for. The 230-word version of the same brief followed almost every
detail.

**Fix:** For anything that matters, write it down. The official soft limit is about 600 English
words or 300 Chinese characters; beyond that, detail gets lost.

## 11. Every edit re-renders the whole frame. *Tested*

**Symptom:** you asked to change one object, and the change is right. But the rest of the image
has shifted very slightly: faint noise, softened texture, and tiny colour drift. Each round of
edits adds a little more.

**Fix:** after an edit, run `python scripts/export.py merge original.png edited.png`. It finds
the regions that really changed, pads them into whole boxes so text is never half old and half
new, feathers the edges, and pastes only those regions onto the original. On our café test,
6.8% of the image came from the edit and the rest stayed pixel-identical. Always zoom in and
check rewritten text in the merged result. If letters are mixed, raise `--grow`.

## 12. Text lines get duplicated or marks get misplaced. *Tested*

**Symptom:** on a dense layout such as a magazine cover, one cover line is printed twice, or a
closing quote mark lands mid-sentence.

**Fix:**
- Read every word in the output.
- Fix it with a small region edit: "Remove the second 'THE ALTITUDE ISSUE' under the masthead;
  keep everything else exactly." Don't regenerate the whole image.
- Then `merge`.

## 13. Invented extras: props, barcodes, seals. *Tested*

**Symptom:** the model adds things that "belong" to the genre:
- a barcode with made-up digits on a magazine cover
- a red seal on Chinese calligraphy
- a saucer or base plate under a product it took from a reference photo

**Fix:**
- Exclude each one by name: "no barcode, no price", "no seal stamps", "the dripper has no
  saucer and no base plate; it sits directly in the mug".
- On product shots, compare the result against the reference photo before you deliver it.

## 14. Objects float or perch instead of sitting in place. *Tested*

**Symptom:** a dripper hovers above a mug or balances on its rim, a cup floats over a table, or
a hand doesn't quite grip the handle.

**Fix:** describe the physical contact, not just the position. "The dripper sits *inside* the
mug opening, its lower cone hidden in the mug, like a funnel in a jar" worked where "on top of
the mug" failed.

## 15. Headline bands on photos. *Tested*

**Symptom:** you ask for a headline on a photo, and the model lays a flat, hard-edged light band
behind the text. It reads as a design mistake.

**Fix:** say where the headline sits *in the scene*: "set directly on the soft, bright wall area
at the top of the photo, with no box or band behind it". Or render the image without text and
set the type in a layout tool.

## 16. "Placeholder logos" become real brands. *Tested*

**Symptom:** on a website mockup we asked for "five grey placeholder customer logos" and got
Airbnb, Notion, X, Slack and Stripe. Publishing that implies endorsements you don't have.

**Fix:**
- Never ask for "logos" you don't supply.
- Write "plain grey rounded rectangles of different widths, no letters, no symbols, no real
  brands", or pass the real logos as references.
- Check every mockup for real trademarks before it leaves your machine.

## 17. Blank areas get filled with invented copy. *Tested*

**Symptom:** UI screens come back with extra sentences, legend values, axis labels or a greeting
you didn't write, even with "nothing else is written".

**Fix:** write the copy for every text slot. For a deck or concept, write plausible copy and tell
the user it's a placeholder. Grey placeholder bars avoid invented claims but look unfinished: in our
website test the version with real copy read as more complete. Read every word before the image
goes into a deck.

## 18. Layer edges are not clean cut-outs. *Tested*

**Symptom:** after `--layers`, a layer moved onto a new background shows a straight clipped
edge, a fringe, or semi-transparent haze from glows. Leftover text or outlines remain in the
base plate if the layer count ran out.

**Fix:**
- Check every layer on a solid colour (the layer viewer has a green background).
- `export.py layers --alpha-floor 48` clears haze.
- Ask for enough layers, roughly one per element plus spares. Every layer is billed.
- Re-split with fewer, larger groups, or fix the remaining edges by hand.

## 19. "Draft at 1K to go faster" doesn't. *Tested*

**Symptom:** 1K renders took about as long as 2K (24 s vs 27 s average over 3 runs each).

**Fix:** draft at 1K to save **money** ($0.020 vs $0.035 on BytePlus), not time. For speed, run
options in parallel (`--count`) and change less per round with region edits.

## 20. A new aspect ratio from a reference splits the frame. *Tested*

**Symptom:** asked to recreate a 16:9 banner as a 4:5 post, with the banner as Image 1, the model
returned two panels joined by a visible seam. A second attempt added a sixth bun to a scene of
five.

**Fix:**
- Render the widest format first, then the tallest with the first as Image 1: "the same scene,
  props, light and lettering, recomposed for a tall 9:16 frame; one continuous photograph". An
  agent without the skill did this and matched all three versions in 3 renders. Ours rendered the
  tall one from scratch and the two sets didn't match.
- Crop the in-between ratios (4:5, 1:1) from the tall one with `export.py --to instagram-post`.
- Don't spend renders on details the user didn't set, such as an exact item count.
- Re-render only if the crop loses the subject. If you do, say "a single continuous photograph,
  not a collage" and repeat the item count ("exactly five buns").

## 21. Platform facts go stale. *Tested*

**Symptom:** the skill said fal had no Seedream 5.5; fal had added `v5.5` text-to-image, edit and
layerize endpoints. An agent without the skill checked fal's live schema and got it right.

**Fix:** when the user asks which version a platform has, check its live model list or API schema
before answering (for fal: `https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=<id>`), and
tell the user if the skill's table is out of date.

## 22. "Extend the image" makes a picture inside a picture. *Tested*

**Symptom:** asked to extend a 2:3 poster into a 16:9 banner, the model drew the original as a
framed panel in the middle of a new scene.

**Fix:** pad the image onto the wide canvas first (`export.py --size 2560x1440 --fit pad --pad-color
blur`) and ask to "fill the blurred areas by continuing the scene … keep the centre strip exactly".
Or say "one continuous illustration, no frame, no border, no inset panel". See `editing.md`.

---

## Claims we tested and could not reproduce

All of these are *Tested*, n = 1. Each warning may still apply in other conditions, so the fix is
kept as an optional safety step.

| Claim | Our result |
|---|---|
| "More than 2 people causes identity bleed" | 3 described people, 3 people from 3 references, and 5 people in a café all stayed distinct. Still give each person a reference and a screen position. |
| "References leak their background unless you say ignore" | One reference, no leak, with or without the clause. Saying what to ignore is cheap insurance when you use several references. |
| "Avoid negatives and describe positively" | "No people, no umbrellas, no boats" was obeyed. Either style works. |
| "Keyword lists ruin quality" | The tag soup still looked good, but prose controlled framing and props. Use prose for **control**. |
