# Platforms, models and API reference

These facts come from each platform's published docs, as of November 2026. Prices change
often, so check them before you quote any to a user. **Live** means the helper script has been
run against the real API. Every other platform follows its docs and is covered by offline mock
tests.

## Seedream versions

| Version | Best for | Max refs | Size | Notes |
|---|---|---|---|---|
| **5.5** | Edit stability, transparent PNGs, layer decomposition, dense text | 10 | `1K`/`1.5K`/`2K`, or 921,600–4,624,220 px | No image sets, no streaming, no 4K. Output defaults to PNG |
| 5.0 Pro | Multilingual text, region editing | 10 | Same as 5.5 | Output defaults to JPEG |
| 5.0 Flash | Cheaper and faster | 10 | Same as 5.5 | |
| 5.0 Lite | 4K, image sets | 14 | `2K`/`3K`/`4K`, 3.7–16.8 MP | `sequential_image_generation` |
| 4.5 | Natural skin (*Reported*), 4K, image sets | 14 | `2K`/`4K` | Always JPEG |
| 4.0 | Older; image sets | 14 | `1K`/`2K`/`4K` | Always JPEG |

On every version, the aspect ratio must be between 1:16 and 16:1. None of the current ByteDance
docs list `seed` or `guidance_scale` (*Official*).

## Official ByteDance API (BytePlus / Volcengine): Live on BytePlus

`POST {base}/images/generations` with the header `Authorization: Bearer $ARK_API_KEY`.

| Platform | `--provider` | Base URL | 5.5 model ID |
|---|---|---|---|
| BytePlus ModelArk | `byteplus` | `https://ark.ap-southeast.bytepluses.com/api/v3` | `dola-seedream-5-5-261028` |
| Volcengine Ark | `volcengine` | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-seedream-5-5-261028` |

The two platforms issue different keys, but both read the same environment variable,
`ARK_API_KEY`. Other IDs:

| Version | BytePlus | Volcengine |
|---|---|---|
| 5.0 Pro | `dola-seedream-5-0-pro-260628` | `doubao-` prefix |
| 5.0 Flash | `dola-seedream-5-0-flash-260915` | `doubao-` prefix |
| 5.0 Lite | `seedream-5-0-260128` | `doubao-` prefix |
| 4.5 | `seedream-4-5-251128` | `doubao-` prefix |
| 4.0 | `seedream-4-0-250828` | `doubao-` prefix |

The helper's `models` command lists the IDs your key can use.

| Field | Values |
|---|---|
| `prompt` | Recommended up to about 600 English words or 300 Chinese characters. 5.5 also accepts 15 other languages |
| `image` | A string or a list of URLs / `data:image/<fmt>;base64,…`. Formats: jpeg, png, webp, bmp, tiff, gif, heic, heif. Max 30 MB each, max 10 images (5.5) |
| `size` | A tier (`1K`, `1.5K`, `2K`; default `2K`) or `WxH`. **When you use a tier, also write the ratio in the prompt** |
| `response_format` | `url` (default; expires after 24 h) or `b64_json`. The helper uses `b64_json` |
| `output_format` | `png` (5.5 default) or `jpeg` |
| `background` | 5.5: `auto`, `transparent` or `opaque`. `transparent` needs `png` |
| `watermark` | **Defaults to `true`** (adds an "AI generated" mark). The helper sends `false` unless you pass `--watermark` |
| `layer_decomposition` + `layer_decomposition_options` | 5.5: split one image into 2–100 layers (`max_images`); `text_recognition: true` adds OCR. The script's `--layers N --ocr` sets both. Each `data` item carries `z_index`, `bounding_box` (`absolute` canvas px and `normalized` 0–1000), `name`, `description` and, for text, `text_recognition` (text, lines, font guess, colour). Every returned layer is billed as an image. Don't send `background` with it |
| `safety_identifier` | A hashed end-user ID, for apps that serve the public |
| `sequential_image_generation` + `…options.max_images` | **5.0 Lite / 4.5 / 4.0 only.** Up to 15 images, counting inputs plus outputs; billed on `max_images` |

**Response:** `data[].b64_json` or `data[].url`, plus `usage.generated_images`. You are only
billed for images that succeed.

**Prices** on BytePlus for 5.5: $0.035 per 2K image, $0.020 up to 1.5K, plus $0.008 per input
image. The rate limit is 500 images per minute per model.

**Errors:**

| Code | Meaning |
|---|---|
| `InvalidParameter` (400) | Check `param`. Out-of-range size errors state the exact limit |
| `InputTextSensitiveContentDetected` / `OutputImageSensitiveContentDetected` (400) | Safety filter; see failure mode 8 |
| `InputImageSensitiveContentDetected.PrivacyInformation` (400) | The reference image shows a real person |
| `InvalidImageURL.*` (400) | The reference URL can't be reached |
| 401 / 403 | Wrong key, or the model isn't enabled for this account |
| 429 `ModelAccountIpmRateLimitExceeded` / `ServerOverloaded` | Back off and retry |
| 500 `InternalServiceError` | Retry |

## Third-party platforms

The helper converts the provider-neutral flags into each platform's own field names.

| `--provider` | Key env var | Default model | How the helper sends size | References | Flow |
|---|---|---|---|---|---|
| `runware` | `RUNWARE_API_KEY` | `bytedance:seedream@5.5` | `width`/`height`, or `resolution` tier | `inputs.referenceImages` (≤10, URL or base64) | Sync task array |
| `wavespeed` | `WAVESPEED_API_KEY` | `bytedance/seedream-v5.5` (`/edit` when there are images) | `aspect_ratio` + `resolution` (`1k`/`1.5k`/`2k`) | `images` (≤10) | Async: `GET /predictions/{id}/result` |
| `kie` | `KIE_API_KEY` | `seedream/5-5-text-to-image` (`5-5-image-to-image` when there are images) | `aspect_ratio` + `size` tier | `image_urls` (≤10, **public URLs only**) | Async: `GET /jobs/recordInfo?taskId=` |
| `evolink` | `EVOLINK_API_KEY` | `doubao-seedream-5.5` | `size` `WxH`, or `quality` tier | `image_urls` (≤10, **public URLs only**) | Async: `GET /tasks/{id}` |
| `fal` | `FAL_KEY` (header `Key …`) | `bytedance/seedream/v5.5/text-to-image` (`/edit` when there are images; `/layerize` for `--layers`, which takes `image_url`, `max_images`, `enable_text_recognition`) | `image_size {width,height}` or `auto_1K`/`auto_1.5K`/`auto_2K` | `image_urls` (≤10) | Async queue: `status_url` → `response_url`. 5.5 takes `background: transparent` |
| `replicate` | `REPLICATE_API_TOKEN` | `bytedance/seedream-5-pro` | `aspect_ratio` + `size` (`1K`/`2K`) | `image_input` (≤10) | `Prefer: wait`, then poll `urls.get` |
| `openrouter` | `OPENROUTER_API_KEY` | `bytedance-seed/seedream-5-5` (5.0 Pro: `bytedance-seed/seedream-5-0-pro`) | `aspect_ratio` + `resolution` | `input_references` | Sync, `data[].b64_json` |

**Notes:**
- **Platforms that only take named ratios** (WaveSpeed, Kie, Replicate, OpenRouter) reject any
  custom `WxH` that isn't close to a preset ratio. Use a preset ratio such as `16:9`. If you pass
  a bare tier (`2K`), the helper sends `1:1` and prints a warning; with reference images, it lets
  the platform follow the input image.
- **Transparent output:** `--background transparent` forces PNG on every platform, because several
  of them default to JPEG, which has no alpha channel.
- **Older models** (5.0 Lite, 4.5, 4.0): the helper allows their larger limits (up to 16.7 MP,
  `3K`/`4K` tiers, 14 references) when you pass their model ID with `--model`.
- **Kie.ai** returns HTTP 200 even on errors. The helper checks `code`.
- **Seed:** on 5.x, only OpenRouter and AI/ML API document a seed parameter. Runware returns the
  seed it used.
- **Image downloads:** where a platform returns an image URL, the helper downloads it **without**
  sending your key. Replicate deletes its outputs after 1 hour, and ByteDance URLs expire after
  24 hours. The helper saves the image straight away.

**Also host Seedream, but not wired into the helper:** Segmind (5.5), Atlas Cloud (5.5), AI/ML
API (5.0), Together AI (5.0 Lite) and ModelsLab. Their request contracts were incomplete or
contradictory in the docs. You can still call them yourself using the prompting guidance in this
skill.

**Sources:** BytePlus ModelArk image API and pricing docs; Volcengine Ark docs; the Runware,
WaveSpeed, Kie.ai, Evolink, fal, Replicate and OpenRouter model pages (November 2026).
