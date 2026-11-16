<div align="center">

# Seedream 5.5 Skill

**Give any AI coding agent the ability to write great Seedream 5.5 prompts and generate images with them.**

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and [about 70 more agents](https://github.com/vercel-labs/skills#supported-agents).

[![Tests](https://github.com/<you>/seedream-5-5-skill/actions/workflows/test.yml/badge.svg)](.github/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-lightgrey)
[![Agent Skills spec](https://img.shields.io/badge/spec-agentskills.io-purple)](https://agentskills.io/specification)

</div>

<!-- Hero: a 3x2 grid of real outputs (product, poster, character, photoreal, infographic, edit before/after). -->

---

```bash
npx skills add <you>/seedream-5-5-skill
```

Then ask your agent:

> Make a 2:3 poster for "Lantern Street Night Market, 14–16 March, Harbour Square" with paper lanterns at dusk.

Your agent then:

1. writes the prompt as structured prose, not a pile of tags
2. picks the right size
3. assigns a role to each reference image
4. checks for known failure modes before spending a render
5. calls ModelArk
6. saves the image along with a full record of how it was made

## Why this skill

- **Prompts that follow how Seedream reads.** The prompt is built in a fixed order:
  deliverable, subject, layout, materials, light, camera, style, exact text, and exclusions
  last.
- **Reference images get explicit roles.** Each one is told what to take and what to ignore:
  "Image 1 provides the shape and logo; ignore its background." This stops backgrounds and
  props leaking between images.
- **Edits that don't drift.** Each round makes one change and restates everything that must
  stay the same.
- **It knows how Seedream breaks.** It catches symmetric "fixes" to asymmetric details, rows
  of identical objects, faces blending once there are three or more people, text that melts
  when the image is animated, and more.
- **Key-safe by design.** The key is read only from `ARK_API_KEY`. It is never printed,
  logged, written to a file or accepted as a flag, and it is removed from error messages.
- **Reproducible.** Every image is saved with a `.txt` sidecar holding the exact prompt,
  the parameters, and the SHA-256 of each reference image.
- **Nothing to install.** It is one Python file that uses only the standard library, with an
  offline test suite in CI.

## Install

| Agent | Command or location |
|---|---|
| **Any agent** (via [skills CLI](https://github.com/vercel-labs/skills)) | `npx skills add <you>/seedream-5-5-skill` |
| **Claude Code** (plugin) | `/plugin marketplace add <you>/seedream-5-5-skill` then `/plugin install seedream-5-5` |
| **Claude Code** (manual) | Copy `skills/seedream-5-5/` to `~/.claude/skills/` or `.claude/skills/` |
| **Codex** | Copy it to `~/.agents/skills/` or `.agents/skills/` |
| **Cursor** | Copy it to `~/.cursor/skills/` or `.agents/skills/` |
| **Gemini CLI** | `gemini skills install https://github.com/<you>/seedream-5-5-skill --path skills/seedream-5-5` |
| **GitHub Copilot** | Copy it to `~/.copilot/skills/` or `.github/skills/` |

To copy it manually:

```bash
git clone https://github.com/<you>/seedream-5-5-skill
cp -r seedream-5-5-skill/skills/seedream-5-5 ~/.agents/skills/
```

## Set your key

Create an API key in the BytePlus ModelArk console and enable Seedream 5.5 for it. Then set
the key in the shell your agent runs in:

```bash
export ARK_API_KEY=...
```

```powershell
$env:ARK_API_KEY = '...'
```

Don't paste the key into the chat. The skill tells the agent never to ask you for it.

## What's inside

```
skills/seedream-5-5/
├── SKILL.md                   core rules, mode picker, prompt structure, pre-flight checks
├── scripts/seedream.py        models · generate · --dry-run
└── references/
    ├── api.md                 endpoint, fields, sizes, errors
    ├── prompting.md           templates: photoreal, product, poster, infographic, character
    │                          sheet, composite, local edit, style transfer, video keyframe
    └── failure-modes.md       8 failure modes, each with its symptom and fix
examples/                      3 worked examples
tests/                         offline tests against a mock API
```

`SKILL.md` stays short. The agent reads the reference files only when it needs them.

## Examples

| | |
|---|---|
| [Product shot from a phone photo](examples/01-product-shot.md) | Take only the product from a reference, leave room for copy, and comp a row of twelve instead of asking the model for it |
| [Poster with exact text](examples/02-poster-with-exact-text.md) | Quote every string, place it, give it a rank in the hierarchy, and allow no filler words |
| [Consistent character](examples/03-consistent-character.md) | A one-eyed mascot that stays the same through a character sheet, a two-person scene and an edit |

## Use the script directly

```bash
S=skills/seedream-5-5/scripts/seedream.py
python $S models                                        # Seedream model IDs your key can use
python $S generate --prompt "..." --size 16:9 --out out --name hero
python $S generate --prompt-file p.txt --image a.png --image b.jpg --size 2:3
python $S generate --prompt "..." --dry-run              # show the request; no key, no cost
```

| Option | Meaning |
|---|---|
| `--size` | `16:9`, `9:16`, `2:3`, `3:2`, `1:1`, or any `WxH` with an area of at least 921,600 px |
| `--image` | A file path, URL or data URI. Repeat it for more images, which become Image 1, Image 2 and so on |
| `--model` | Defaults to `dola-seedream-5-5-261028`. Can also be set with `SEEDREAM_MODEL` |
| `--name` | The file name stem. The script adds `_2`, `_3` and so on rather than overwrite a file |
| `--extra` | A JSON object of extra request fields, passed through unchanged |

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check the request body, the size rules, the sidecar files, the spec-compliant
frontmatter, and that the key never shows up in output or on disk.

## Contributing

Found a new way Seedream breaks, or a better fix for one? Open an issue or PR with the
prompt, the sidecar `.txt` and what went wrong. Failure modes that come with a tested fix are
the most valuable contribution.

## License

MIT. See [LICENSE](LICENSE). This project is not affiliated with ByteDance or BytePlus.
Model IDs, limits and pricing change, so check with `seedream.py models` and the ModelArk
docs.

<sub>Acknowledgment: part of the prompt structure is adapted from the Seedream 5.5 guide in
[Evolink-AI/awesome-seedream-5-5-guide-and-prompt](https://github.com/Evolink-AI/awesome-seedream-5-5-guide-and-prompt)
(CC BY 4.0).</sub>
