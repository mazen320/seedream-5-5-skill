# Example 2: poster with exact text

**Ask:** "Make a poster for our night market: Lantern Street Night Market, 14–16 March,
Harbour Square, 6pm till late."

**Mode:** text-to-image, using the poster template. The text is the hard part, so every
string is quoted, placed and given a rank in the hierarchy.

## Prompt (`poster.txt`)

```text
An A2 portrait event poster for a night market. The top third holds the headline "LANTERN STREET"
in tall condensed bold capitals, warm cream, centred, with "NIGHT MARKET" directly below it in a
smaller spaced-out sans serif. The middle holds the key visual: a narrow street seen from street
level at dusk, strings of round paper lanterns in amber and red zig-zagging overhead toward a
glowing vanishing point, food stall awnings on both sides, a soft haze catching the light. The
bottom band is a solid deep navy strip holding, left-aligned in cream, "14–16 MARCH" on the first
line and "HARBOUR SQUARE · 6PM TILL LATE" on the second. Palette of navy, amber, red and cream,
with a light risograph print grain over the whole poster. Every word is spelled exactly as quoted
and nothing else is written.
Exclusions: no extra text, no logos, no watermark, no people in the foreground.
```

```bash
python skills/seedream-5-5/scripts/seedream.py generate --prompt-file poster.txt --size 2:3 --out out --name night_market_poster
```

## Why it works

- Each piece of text has a quoted string, a position, a style and a rank in the hierarchy
  (failure mode 6).
- The lines are short, and the long line is split into two lines on purpose.
- "nothing else is written" together with "no extra text" stops the model inventing filler
  words.
- `2:3` (1728x2592) is close to the A-series portrait ratio.

**Check:** Read every word in the output. If any word is wrong, edit only that word with a
one-change edit ("Image 1 is the current poster. Change only the bottom line to read …").
Don't regenerate the whole poster.
