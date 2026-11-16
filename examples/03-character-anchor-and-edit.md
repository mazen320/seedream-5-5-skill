# Example 3: character anchor, a two-person scene, and a multi-round edit

**Goal:** a one-eyed knitted toy that stays the same in every shot of a short film. It
appears next to a child, and one shot later needs a costume change.

**Failure modes checked:**
- Asymmetry: the toy has exactly one eye, and the model tends to add a second one.
- Head count: two characters at most, and each one gets its own reference.
- Edit drift across rounds.

## Round 0: the anchor (`anchor_bramble.txt`)

```text
A full-body character reference of Bramble, a hand-knitted toy bear about 30 cm tall in chunky
mustard-yellow wool with visible stitches, short rounded ears and a slightly lopsided smile in
brown thread. Bramble has exactly one eye: a single shiny black button on the toy's left side of
the face; on the right side, where the second eye would be, there is a small stitched X in red
thread. A faded blue patch is sewn onto the left knee. Neutral standing pose, arms slightly away
from the body, facing the camera, whole figure visible with space around it. Plain light-grey
seamless backdrop, soft even studio light. Sharp focus throughout.
Exclusions: no second eye, no props, no other characters, no text.
```

```bash
python scripts/seedream.py generate --prompt-file anchor_bramble.txt --size 2:3 --out anchors --name bramble_anchor
```

Repeat this step for the child (`mila_anchor.png`), using the character-anchor template in
`SKILL.md`.

## Round 1: the two-person scene (`sh020.txt`)

```text
A cinematic film still, 16:9, from a gentle family film. Image 1 provides Bramble the knitted bear:
keep the single button eye on the toy's left, the red stitched X on the right, the mustard wool and
the blue knee patch exactly. Image 2 provides Mila, the child: keep her face, curly auburn hair and
yellow raincoat exactly. Mila sits on the left of frame on a window seat, holding Bramble up on the
right of frame so they face each other in profile. Rain streaks the window behind them; soft grey
daylight from the window with a warm lamp glow from camera right. Medium two-shot at eye level on a
40mm lens, gentle depth of field.
Exclusions: no other people, no text, no second eye on the bear.
```

```bash
python scripts/seedream.py generate --prompt-file sh020.txt --image anchors/bramble_anchor.png --image anchors/mila_anchor.png --size 16:9 --out renders --name sh020_v1
```

## Round 2: the edit (`sh020_edit.txt`)

```text
Image 1 is the current frame. Change only one thing: Bramble now wears a tiny red knitted scarf
wrapped once around the neck, its ends hanging over the chest. Keep everything else exactly as in
Image 1: Mila's face, hair, raincoat and pose, Bramble's single button eye on the left and red
stitched X on the right, the window, the rain, the lighting and the camera framing. Image 2 is
Bramble's identity reference only; use it to keep the toy's face and wool unchanged.
Exclusions: no other changes, no second eye on the bear, no text.
```

```bash
python scripts/seedream.py generate --prompt-file sh020_edit.txt --image renders/sh020_v1.png --image anchors/bramble_anchor.png --size 16:9 --out renders --name sh020_v2
```

## Why it is written this way

- The asymmetry is fixed in three places: in the anchor, in each later scene prompt, and in
  the exclusions. The prompt names the missing eye's side and says what replaces it.
- Screen positions ("left of frame", "right of frame") and a reference for each character
  keep the two identities from bleeding into each other.
- The edit states a single change, then restates the full preservation list. The original
  anchor is attached again as an "identity only" reference to limit drift.
- The sidecars `sh020_v1.txt` and `sh020_v2.txt` record which file was Image 1 and which was
  Image 2, with their hashes. The edit chain can be audited later.
