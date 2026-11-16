# Prompt templates

Fill in the brackets and delete any clause you don't need. Every template follows the same
order: deliverable, subject, layout, materials, lighting, camera, style, text, exclusions.

## Photoreal

> A photorealistic [shot size] photograph of [subject, with 2–3 specific physical details],
> [action or pose] in [location, with 2 concrete details]. [Where the subject sits in the frame;
> what is in the foreground and background.] [Materials and textures.] Lit by [light source,
> its direction, quality and colour temperature]. Shot on a [focal length] lens at [aperture]
> with [depth of field]. [Mood or grade.] Exclusions: [short list].

## Product

> A studio product photograph of the [product] in Image 1. Image 1 provides the exact shape,
> proportions, [colour and finish] and logo placement. Keep them exactly, and ignore Image 1's
> background and lighting. The product is [standing / flat lay / held / worn], viewed from
> [angle], and fills about [fraction] of the frame, with [side] left as empty space for copy.
> [Surface and backdrop.] [Key, fill and rim light, and where reflections should appear.]
> [Props, if any, and where they go.] Exclusions: no extra logos, no text, no duplicate
> products.

## Poster or graphic with exact text

> A [format, e.g. A2 portrait concert poster]. The top third holds the headline "[EXACT
> TEXT]" in [typeface style, weight, colour], centred. The middle holds [the key visual]. The
> bottom band holds, left-aligned in smaller type, "[LINE 1]" and below it "[LINE 2]".
> [Palette.] [Texture: print grain, paper.] Every word is spelled exactly as quoted, and
> nothing else is written. Exclusions: no extra text, no watermark.

Text rules: quote every character, name what it is printed on (a sign, a label, a screen),
and give its position, line breaks, alignment and hierarchy. Short lines render best.

## Infographic or slide

> A clean [16:9] infographic on a [background]. Title at the top: "[TITLE]". The layout is
> [three columns / a timeline / a 2x2 grid]. [Module 1: icon and label "[TEXT]", with value
> "[NUMBER]"]... [Chart type, axes, legend, if any.] [Style: flat vector, line weight,
> palette.] Exclusions: no decorative text, no logos.

## Character sheet (for consistency across images)

> A full-body character reference of [name]: [age, build, face, hair, distinguishing marks,
> including any asymmetry and which side of the image it is on], wearing [the outfit, layer by layer, with
> colours and materials]. Neutral standing pose, arms slightly away from the body, facing the
> camera, the whole figure in frame with space around it. Plain light-grey seamless backdrop,
> soft even light, sharp focus throughout. Exclusions: no props, no other people, no text.

Use this image as an "identity" reference in every later prompt.

## Multi-reference composite

> Image 1 provides [character A]'s face, hair and outfit. Image 2 provides [character B / the
> product]. Image 3 provides the location and lighting only. [Scene: who is where, by screen
> position, doing what.] [Camera.] [Grade.] Keep the identities from Images 1 and 2 exactly.
> Exclusions: no other people, no text.

## Local edit

> Image 1 is the current image. In [exact area], [operation: replace / remove / recolour /
> add] [what], at [strength or size]. Match the surrounding texture, grain and lighting, and
> blend the edges. Keep everything else exactly as in Image 1: [the identity, pose,
> background, framing and lighting].

## Style transfer

> Re-render Image 1 in the style of Image 2. Take only Image 2's [palette, contrast, grain,
> brushwork, lighting mood]. Keep Image 1's composition, subjects, poses and proportions
> exactly. Exclusions: no new objects, no text.

## Keyframe for a video model

> A [aspect ratio] still frame. [Subject] is [doing a specific action at a specific moment],
> at [screen position], shot as [shot size] from [angle] on a [lens]. [Simple background.]
> [Motivated light source.] [Atmosphere.] The frame shows the instant before [the next action],
> so the motion has somewhere to go. Exclusions: no on-screen text, no subtitles.

## Words that help, and words that don't

| Helps | Doesn't |
|---|---|
| "soft north-window light from the left, cool 5600K" | "beautiful lighting" |
| "85mm lens at f/2, background softly blurred" | "8k, ultra HD, masterpiece" |
| "matte sage-green glaze, unglazed rim" | "high quality product" |
| "the subject sits on the right third, with empty sky on the left" | "nice composition" |
