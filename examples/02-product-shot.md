# Example 2: product shot from a reference photo (and the "row" trap)

**Goal:** a premium hero image of a ceramic pour-over coffee dripper, made from the client's
phone photo. The client also wants "a shelf of twelve of them" for a banner.

**Failure modes checked:** the request for a row of twelve identical objects. Seedream would
drift on the count and the shapes. So the hero is generated once. For the banner, the shelf
is generated empty and the hero is comped onto it twelve times.

## Step 1: the hero (`hero.txt`)

```text
A studio product photograph of the ceramic pour-over coffee dripper shown in Image 1. Image 1
provides the exact shape, proportions, the matte sage-green glaze, the unglazed rim and the
three-hole base; keep them exactly and ignore Image 1's kitchen background and lighting. The
dripper stands on a pale travertine slab, viewed from slightly above at a 20-degree angle,
filling about half the frame, with generous negative space on the left for copy. Warm beige
seamless backdrop. Soft key light from a large softbox at upper right, gentle fill from the
left, a thin rim light separating the rim from the backdrop; a soft natural shadow falls to the
lower left. A few roasted coffee beans rest loosely near the base, out of focus in the foreground.
Exclusions: no text, no logos, no second dripper.
```

```bash
python scripts/seedream.py generate --prompt-file hero.txt --image client_photo.jpg --size 1:1 --out renders --name dripper_hero_v1
```

## Step 2: the empty shelf plate (`shelf.txt`)

```text
A wide studio photograph of a long, empty floating oak shelf against a warm beige wall, seen
straight on at eye level, the shelf running edge to edge across the frame. Soft light from the
upper right with a gentle gradient across the wall and a soft shadow under the shelf. The shelf
surface is clear and evenly lit along its whole length, ready for products to be placed on it.
Exclusions: no objects on the shelf, no text, no plants.
```

```bash
python scripts/seedream.py generate --prompt-file shelf.txt --size 16:9 --out renders --name shelf_plate_v1
```

In an editor, cut out the hero dripper and place twelve copies on the shelf. Add a small
shadow to each copy and vary the spacing by a pixel or two so the row looks natural.

## Why it is written this way

- Image 1 gets a role covering what to take *and* what to ignore. Without this, the kitchen
  background tends to leak into the image.
- The clause "keep them exactly" protects the product's identity, and the hard exclusion
  "no second dripper" covers the count.
- The negative space is asked for in the prompt, so the layout works for ad copy.
