# Seedream 5.5 on BytePlus ModelArk: API reference

Base URL: `https://ark.ap-southeast.bytepluses.com/api/v3`. Override it with `--base-url` or
the `ARK_BASE_URL` environment variable. Every request sends the header
`Authorization: Bearer $ARK_API_KEY`.

## Find the model ID

`GET /models` lists every model your key can see. Search the list for `seedream`.

```bash
python scripts/seedream.py models          # IDs only
python scripts/seedream.py models --json   # full records
```

Model IDs carry a date suffix that changes between releases. The confirmed working ID as of
November 2026 is `dola-seedream-5-5-261028`. This is the script's default. Override it with
`--model` or the `SEEDREAM_MODEL` environment variable.

## Generate or edit

`POST /images/generations`

```json
{
  "model": "dola-seedream-5-5-261028",
  "prompt": "A studio product photograph of ...",
  "size": "2560x1440",
  "response_format": "b64_json",
  "watermark": false,
  "image": ["data:image/png;base64,...", "https://example.com/ref2.jpg"]
}
```

| Field | Notes |
|---|---|
| `size` | `WxH`. The area must be at least **921,600 px**. Smaller sizes are rejected |
| `response_format` | `b64_json` returns the image bytes inline, and the script decodes them |
| `watermark` | `false` by default in the script. Pass `--watermark` to turn it on |
| `image` | Optional. One data URI or URL as a string, or a list for several references. The script turns local paths into data URIs |

The response arrives as `data[]`, where each item has a `b64_json` field. Other top-level
fields, such as `created` and `usage`, are saved into the sidecar file.

## Size presets

| Preset | Size | Status |
|---|---|---|
| `16:9` | 2560x1440 | confirmed |
| `2:3` | 1728x2592 | confirmed |
| `1:1` | 2048x2048 | confirmed |
| `9:16` | 1440x2560 | the 16:9 size turned sideways |
| `3:2` | 2592x1728 | the 2:3 size turned sideways |

## Extra fields

`--extra '{"field": value}'` merges extra fields into the request body. Use it only for
fields you have confirmed in the current ModelArk docs. `prompt`, `image` and
`response_format` are blocked from `--extra`; set them with their own flags.

## Sidecar record

Every `name.png` gets a `name.txt` next to it. The file records:

- the timestamp
- the model
- the exact prompt
- every parameter
- each reference image, in order, with its source path or URL and its SHA-256 hash
- the response metadata

The key is never recorded.

## Errors

| What you see | Likely cause |
|---|---|
| `ARK_API_KEY is not set` | Export the key in the same shell that runs the agent |
| HTTP 401 / 403 | The key is wrong, or Seedream isn't enabled for this account or region |
| HTTP 404 on the model | The ID has changed. Run `models` |
| `Size ... needs at least 921600 px` | Choose a preset or a larger `WxH` |
| HTTP 400 that mentions `image` | The reference URL can't be reached, or the image format isn't supported. Try a local PNG or JPEG |
