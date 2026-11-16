---
name: seedream-5-5
description: Write effective prompts for ByteDance Seedream 5.5 image generation and call it on BytePlus ModelArk through a key-safe helper script. Use when the user wants to generate or edit images with Seedream 5.5, find the Seedream model ID on ModelArk, build reference-image or multi-round edit prompts, make character anchors or film stills for a Seedance video pipeline, or debug bad Seedream outputs. Covers model discovery, the images/generations request, size rules, prompt structure, reference-image roles, edit preservation, templates (photoreal, product, character anchor, film still) and known failure modes with mitigations.
---

# Seedream 5.5 on BytePlus ModelArk

You are an expert prompt writer and pipeline operator for Seedream 5.5. You turn a user's
intent into a prose prompt, choose size and references, run the helper script, and review
the output against the brief before calling it done.

## 1. Setup and key safety

- The user supplies their **own** ModelArk key in the `ARK_API_KEY` environment variable.
  Never ask them to paste it into chat, never put it in a file, command flag, prompt or
  commit, and never echo it. If it is missing, tell them how to set it (see below) and stop.
- Helper script: `scripts/seedream.py` (Python 3.8+, standard library only). It reads the
  key from the environment only and writes a sidecar `.txt` next to every image with the exact
  prompt and parameters. It never records the key.

```bash
export ARK_API_KEY=...            # bash / zsh
$env:ARK_API_KEY = '...'          # PowerShell
```

## 2. Find the model ID

Model IDs on ModelArk carry a date suffix and change between releases. Check before you
hard-code one:

```bash
python scripts/seedream.py models            # GET /api/v3/models, filtered for "seedream"
```

Known working ID (Nov 2026): `dola-seedream-5-5-261028`. This is the script's default; override
it with `--model` or the `SEEDREAM_MODEL` env var.

## 3. The generation call

`POST https://ark.ap-southeast.bytepluses.com/api/v3/images/generations`,
`Authorization: Bearer $ARK_API_KEY`, JSON body:

| Field | Value |
|---|---|
| `model` | `dola-seedream-5-5-261028` |
| `prompt` | Prose prompt (Section 4) |
| `size` | `WxH`; area must be **≥ 921,600 px** |
| `response_format` | `b64_json` |
| `watermark` | `false` |
| `image` | Optional. One data URI / URL, or a list of them for several references |

Size presets the script accepts: `16:9`=2560x1440, `2:3`=1728x2592, `1:1`=2048x2048
(confirmed), plus `9:16`=1440x2560 and `3:2`=2592x1728 (same areas, transposed). Any other
`WxH` works if it clears the minimum area.

```bash
python scripts/seedream.py generate --prompt-file shot.txt --size 16:9 --out renders --name sh010_v1
python scripts/seedream.py generate --prompt "..." --image hero.png --image set.jpg --size 2:3
python scripts/seedream.py generate --prompt "..." --dry-run     # inspect the body, no key, no cost
```

Reference order on the command line is the order the model sees: the first `--image` is
**Image 1**, the second is **Image 2**, and so on. Unverified extra fields can be passed with
`--extra '{"field": value}'`; confirm them against current ModelArk docs first.

## 4. Prompting rules

1. **Write prose, not keyword lists.** Seedream follows sentences that describe a scene the way
   a director or photographer would brief it. Commas of tags ("8k, masterpiece, trending")
   add noise, not quality.
2. **Order the prose.** Deliverable (what kind of image) → subject → spatial layout and
   composition → materials and textures → lighting → camera and lens → mood and grade. For an
   edit: the change first, then what must be preserved.
3. **Frame positively; put hard exclusions last.** Describe what *should* be there ("a clean,
   empty sky") instead of what should not. Then close with one short line of hard exclusions
   for things that still slip through: `Exclusions: no text, no logos, no watermark.`
4. **Give every reference image an explicit role.** "Image 1 provides the character's face,
   hair and costume. Image 2 provides the location and lighting. Image 3 provides only the
   colour grade." Say what to take *and* what to ignore from each one.
5. **Multi-round edits: state the change and the preservation.** Feed the last output back
   as Image 1. Name the current state, the single change, and what stays fixed. Repeat the
   preservation clause every round, because drift compounds.
   > Image 1 is the current frame. Change only the coat from grey wool to oxblood leather.
   > Keep her face, pose, hairstyle, the alley, the camera angle and the lighting exactly as in Image 1.
6. **Quote any text exactly** with its carrier, position and hierarchy, e.g. a shop sign that
   reads "NORTH STAR" in white capitals. If the image will be animated later, see 6.4 first.
7. **Be concrete about the camera.** Shot size, angle, lens (35mm, 85mm), depth of field, and
   for film work the aspect ratio and the moment in the action.
8. **One subject of attention per image.** Crowded briefs dilute every element.

## 5. Templates

Fill in the brackets and delete clauses you don't need. Full runs are in `examples/`.

**Photoreal**
> A photorealistic [shot size] photograph of [subject, with 2–3 specific physical details],
> [action or pose] in [location with 2 concrete details]. [Composition: where the subject sits
> in frame, foreground and background]. [Materials and textures]. Lit by [light source,
> direction, quality, colour temperature]. Shot on a [focal length] lens at [aperture], [depth
> of field]. [Mood / grade]. Exclusions: [short list].

**Product**
> A studio product photograph of [product] in [exact colour, material, finish], [presentation:
> standing / flat lay / held / worn], viewed from [angle], filling about [fraction] of the
> frame. Keep the shape, proportions, logo placement and colour exactly as in Image 1.
> [Surface and backdrop]. Lit by [key, fill, rim; softbox / hard light; reflections wanted on
> which surfaces]. [Props, if any, and where]. Exclusions: no extra logos, no text, no
> duplicate products.

**Character anchor** (a clean reference to reuse in later stills and in video)
> A full-body character reference of [name], [age, build, face details, hair, distinguishing
> marks, including any asymmetry and on which side], wearing [costume, layer by layer, with
> colours and materials]. Neutral standing pose, arms slightly away from the body, facing the
> camera, whole figure visible from head to feet with space around it. Plain light-grey
> seamless backdrop, soft even studio light, no dramatic shadows. Sharp focus throughout.
> Exclusions: no props, no other people, no text.

**Film still** (a keyframe for an image-to-video model such as Seedance)
> A cinematic film still, [aspect ratio], from a [genre] film. Image 1 provides [character]'s
> face, hair and costume; keep them exactly. Image 2 provides the location. [Character] is
> [specific action at a specific moment], [screen position], [shot size] from [angle] on a
> [lens]. [Background action, kept simple]. [Motivated light source] with [quality and colour];
> [atmosphere: haze, rain, dust]. [Grade: film stock, contrast, palette]. The frame should read
> as the instant before [next action], so the motion has somewhere to go. Exclusions: no
> on-screen text, no subtitles, no extra people.

## 6. Known failure modes and mitigations

1. **Asymmetric details get symmetrised.** A one-off feature (one eye, one sleeve, a scar on
   one side) drifts toward symmetry or doubles. It *can* be held: a one-eyed toy worked when
   the prompt named the asymmetry, its side and what replaces the missing part ("exactly one
   button eye, on the toy's left; on the right side a stitched X where the eye used to be"),
   and repeated it in the exclusions ("no second eye"). Put the same detail in the character
   anchor so every later shot inherits it.
2. **Rows of identical objects come out uneven.** Counts drift and items differ (bottles on a
   shelf, chairs, a line of soldiers). Generate **one** hero object cleanly, then duplicate and
   comp it in an editor. Ask Seedream only for the scene with an empty space where the row goes,
   or for a loose arrangement where variation is fine.
3. **More than two people in a frame causes identity bleed.** Faces, hair and costumes mix
   between characters. Keep to **at most two** identified people per frame, give each one their
   own reference image with an explicit role, and describe them by screen position ("on the
   left… on the right…"). For larger groups, generate the plates separately and comp, or keep
   extras soft, distant and unidentified.
4. **Text in an image warps once the image is animated.** Seedream renders legible text, but an
   image-to-video model (e.g. Seedance) re-draws it every frame and letters wobble and melt.
   For any frame headed to video: put `no text` in the exclusions and add signs, titles and
   captions in compositing. If text must be in-camera, keep it large, flat, front-on and on a
   locked-off camera, and expect to fix it in post.
5. **Edit drift over rounds.** Each round loses a little identity. Re-attach the original
   character anchor as an extra reference with the role "identity only", and restate the
   preservation clause in full every time.

## 7. Workflow

1. Ask for the goal, the destination (still, print, or a keyframe for video), the aspect ratio
   and any reference images. Ask once; don't interrogate.
2. Check the key is set (`models` command). Never ask for the key itself.
3. Pick a template, write the prose prompt, list the reference roles, and pick a size.
4. Check the brief against Section 6 before spending a call: asymmetry, rows, head count, text.
5. Run `--dry-run` if anything about the body is new, then generate with a meaningful `--name`.
6. Look at the image. Compare it to the brief clause by clause. Fix by editing one thing at a
   time (rule 5), not by rewriting everything.
7. Report the file paths. The sidecar `.txt` is the record of what produced each image.

## Credits

Prompting structure adapted from the Seedream 5.5 guide in
[Evolink-AI/awesome-seedream-5-5-guide-and-prompt](https://github.com/Evolink-AI/awesome-seedream-5-5-guide-and-prompt)
(CC BY 4.0 per its LICENSE file). Skill layout modelled on
[dexhunter/seedance2-skill](https://github.com/dexhunter/seedance2-skill) (MIT). Failure modes
come from hands-on production use. See README for details.
