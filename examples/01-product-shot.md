# Example 1: product shot from a phone photo

**Ask:** "Turn this phone photo of our coffee dripper into a premium hero shot. Leave room for
ad copy. We also want a banner with twelve of them on a shelf."

**Mode:** single reference (the phone photo is Image 1). The banner request hits a known
failure mode, rows of identical objects, so it is planned as two renders and a composite.

## Hero (`hero.txt`)

```text
A studio product photograph of the ceramic pour-over coffee dripper in Image 1. Image 1 provides
the exact shape, proportions, the matte sage-green glaze, the unglazed rim and the three-hole
base; keep them exactly and ignore Image 1's kitchen background and lighting. The dripper stands
on a pale travertine slab, viewed from slightly above at about 20 degrees, filling half the
frame on the right, with the left half left as clean negative space for copy. Warm beige
seamless backdrop. Soft key light from a large softbox at upper right, gentle fill from the
left, a thin rim light separating the rim from the backdrop; a soft natural shadow falls to the
lower left. A few roasted coffee beans rest loosely near the base, softly out of focus.
Exclusions: no text, no logos, no second dripper.
```

```bash
python skills/seedream-5-5/scripts/seedream.py generate --prompt-file hero.txt --image phone.jpg --size 1:1 --out out --name dripper_hero
```

## Banner: an empty shelf, then a composite (`shelf.txt`)

```text
A wide studio photograph of a long, empty floating oak shelf against a warm beige wall, seen
straight on at eye level, running edge to edge across the frame. Soft light from the upper
right with a gentle gradient across the wall and a soft shadow under the shelf. The shelf
surface is clear and evenly lit along its whole length.
Exclusions: no objects on the shelf, no text, no plants.
```

```bash
python skills/seedream-5-5/scripts/seedream.py generate --prompt-file shelf.txt --size 16:9 --out out --name shelf_plate
```

Next, cut out the hero dripper and place twelve copies on the shelf. Give each copy a small
contact shadow, and vary the spacing by a pixel or two.

## Why it works

- The prompt says what to take from Image 1 **and** what to ignore. This stops the kitchen
  background from leaking in (failure mode 7).
- The negative space is part of the layout clause, so the ad copy has room.
- The row of twelve is never asked of the model (failure mode 2).
