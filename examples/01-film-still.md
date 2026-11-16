# Example 1: film still for image-to-video

**Goal:** a 16:9 keyframe that Seedance will animate. One character, rain at night, and the
moment just before she turns.

**Failure modes checked:** one person (no identity bleed). The neon sign is described as an
unreadable glow, so no letters are left to warp in video.

## Prompt (`shot_010.txt`)

```text
A cinematic film still, 16:9, from a quiet neo-noir drama. A woman in her early thirties with a
dark shoulder-length bob, a small scar through her left eyebrow and a charcoal wool coat stands
at the edge of a wet tram platform at night, framed on the right third of the image, three-quarter
back view, her head beginning to turn toward camera left. Behind her the empty platform recedes
to a vanishing point; a single tram's headlights glow out of focus in the far distance. Steady
fine rain, puddles reflecting a magenta and teal neon glow from an unseen sign above frame. Medium
shot from shoulder height on a 50mm lens, shallow depth of field with the background softly
blurred. Cool, low-contrast grade with lifted blacks and a faint 35mm film grain. The frame reads
as the instant before she notices someone, so the motion has somewhere to go.
Exclusions: no readable text or signage, no subtitles, no other people.
```

## Command

```bash
python scripts/seedream.py generate --prompt-file shot_010.txt --size 16:9 --out renders --name sh010_v1
```

## Why it is written this way

- The order follows the guide: deliverable, subject, position, background, atmosphere,
  camera, grade.
- The scar's side ("left eyebrow") is stated, so the detail stays fixed in later shots.
- The light comes from an *unseen* sign. That way the image gets neon colour without any
  letters.
- The last sentence gives Seedance a motion cue: the head turn has already begun.

## Review checklist

The scar is on the left. Exactly one person is in frame. There are no glyphs anywhere. She is
on the right third. The rain is visible in the light.
