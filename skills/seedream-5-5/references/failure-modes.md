# Failure modes and fixes

Check the brief against this list **before** generating. Each check costs nothing, and each
mistake it catches would cost a render.

## 1. Asymmetric details become symmetric

**Symptom:** A one-off feature (one eye, one sleeve, an earring on one side, a scar) gets
mirrored, doubled or dropped.

**Fix:** Name the asymmetry, say which side it is on, and say what fills the other side. Then
repeat it in the exclusions.

> exactly one black button eye, on the toy's left; on the right side, where the second eye
> would be, a small stitched X in red thread. … Exclusions: no second eye.

Put the same wording in the character sheet and in every later prompt.

## 2. Rows of identical objects

**Symptom:** You ask for twelve bottles on a shelf, a line of chairs, or a grid of icons. The
count is wrong, and the items vary in shape, label or spacing.

**Fix:** Generate **one** clean hero object. Generate the scene separately, with the space
where the row will go left empty. Then duplicate the object and place the copies in an
editor. If some variation is acceptable, ask for a loose, natural-looking arrangement
instead of identical items.

## 3. Identity bleed with more than two people

**Symptom:** Faces, hair or clothes mix between characters. Two people tend to come out with
the same face.

**Fix:** Keep to **two identifiable people per image** at most. Give each person their own
reference image with an explicit role, and describe them by screen position ("on the left…,
on the right…"). For groups, generate each person separately and composite them. Or keep the
extras small, distant and out of focus.

## 4. Text warps once the image is animated

**Symptom:** The text in the still looks clean, but once an image-to-video model (such as
Seedance) animates the frame, the letters wobble, melt or change. The video model redraws
them on every frame.

**Fix:** For any frame meant for video, put `no text` in the exclusions and add signs, titles
and captions in compositing. If text has to be part of the scene, keep it large, flat and
facing the camera, and lock the camera off in the video prompt.

## 5. Identity drifts across edits

**Symptom:** After several rounds of edits, the face, proportions or product details have
slowly changed.

**Fix:**
- Change one thing per round.
- Repeat the full keep-list every round.
- Attach the original image again as an extra reference with the role "identity reference
  only".
- If the drift has gone too far, restart from the best earlier version, using its sidecar
  `.txt` as the record.

## 6. Text errors in still images

**Symptom:** Letters are misspelled, extra words appear, or long lines break.

**Fix:**
- Quote each string exactly.
- Keep each line short.
- Give the line breaks and the alignment.
- Add "every word is spelled exactly as quoted, and nothing else is written".
- For anything legally exact, such as prices or ingredients, add the text in a layout tool
  instead.

## 7. Reference leakage

**Symptom:** The background, lighting or props from a reference image show up when you only
wanted the subject from it.

**Fix:** Say what to **ignore** as well as what to take: "Image 1 provides only the shape and
logo; ignore its background, lighting and props."

## 8. Keyword soup

**Symptom:** The output looks generic and over-processed, and parts of the prompt are ignored.

**Fix:** Rewrite the tags as sentences. Replace prestige words ("masterpiece", "8k",
"award-winning") with concrete visual facts: the light, the lens, the material, where things
are placed.
