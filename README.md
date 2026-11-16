# seedream-5-5-skill

A Claude Code skill for prompting and calling **Seedream 5.5** (ByteDance's image model) on
**BytePlus ModelArk**. It contains:

- `SKILL.md`: the prompting guide Claude follows. It covers model discovery, the request
  format, size rules, prose prompt structure, reference-image roles, multi-round edits,
  four templates and known failure modes.
- `scripts/seedream.py`: a key-safe helper written with the Python standard library only.
  It lists models, generates images and saves each image with a sidecar `.txt` that holds
  the exact prompt and parameters.
- `examples/`: three worked examples (film still, product shot, character anchor and edit).

## Install

Claude Code finds skills in folders that contain a `SKILL.md`.

**Personal (all projects):**

```bash
git clone https://github.com/<you>/seedream-5-5-skill ~/.claude/skills/seedream-5-5
```

On Windows PowerShell:

```powershell
git clone https://github.com/<you>/seedream-5-5-skill "$HOME\.claude\skills\seedream-5-5"
```

**One project only:** clone into `<project>/.claude/skills/seedream-5-5` instead.

Restart Claude Code (or start a new session). Then ask for something like *"make a 16:9
film still of …with Seedream"*. The skill loads on its own, or you can call it with
`/seedream-5-5`.

## Set your key

Get an API key from the BytePlus ModelArk console and enable Seedream 5.5 for your account.
Then put the key in the environment of the shell that runs Claude Code:

```bash
export ARK_API_KEY=...
```

```powershell
$env:ARK_API_KEY = '...'
```

The script reads the key **only** from `ARK_API_KEY`. It has no `--api-key` flag, so the key
never ends up in shell history. It never prints, logs or writes the key, and it removes the
key from any server error text before showing it. Don't paste your key into the chat.

## Use the script directly

```bash
python scripts/seedream.py models                      # find Seedream model IDs for your key
python scripts/seedream.py generate --prompt "A photorealistic ..." --size 16:9 --out renders
python scripts/seedream.py generate --prompt-file shot.txt --image anchor.png --image set.jpg --size 2:3
python scripts/seedream.py generate --prompt "..." --dry-run   # shows the request body; no key or network needed
```

| Option | Meaning |
|---|---|
| `--size` | `16:9`, `9:16`, `2:3`, `3:2`, `1:1` or any `WxH` with an area of at least 921,600 px |
| `--image` | Path, URL or data URI. Repeat the option for several references. The order you give them is Image 1, Image 2 and so on |
| `--model` | Defaults to `dola-seedream-5-5-261028`. You can also set `SEEDREAM_MODEL` |
| `--name` | File stem. The script adds `_2`, `_3` and so on rather than overwrite a file |
| `--extra` | JSON object of extra request fields, passed through unchanged |
| `--base-url` | Defaults to the `ap-southeast` endpoint. You can also set `ARK_BASE_URL` |

Each `name.png` gets a `name.txt` next to it. The `.txt` holds the prompt, size, model, a
SHA-256 and source path for each reference image, and the response metadata. This makes
every image reproducible and easy to compare.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests run against a local mock server. They make no network calls and use no real key.
They check the request body, the size validation, the sidecars, and that the key never
appears in output or on disk.

## Credits

- **[Evolink-AI/awesome-seedream-5-5-guide-and-prompt](https://github.com/Evolink-AI/awesome-seedream-5-5-guide-and-prompt)**:
  its Seedream 5.5 guide table shaped this skill's prompt order (deliverable, subject, layout,
  materials, lighting), the reference-role rule, exact-text quoting and the multi-round edit
  pattern. That repo's README badge says MIT, but its `LICENSE` file says **CC BY 4.0**. The
  ideas here are adapted and reworded, not copied, and are credited under CC BY 4.0.
- **[dexhunter/seedance2-skill](https://github.com/dexhunter/seedance2-skill)** (MIT,
  © 2026 Dex): the structural model for a video-model prompting skill (constraints, syntax,
  templates, common mistakes, workflow).
- The failure modes in Section 6 of `SKILL.md` come from producing a short film with Seedream
  5.5 and Seedance.

This is not an official ByteDance or BytePlus project. Model IDs, limits and pricing change,
so check the ModelArk docs and `seedream.py models`.

## License

MIT. See [LICENSE](LICENSE).
