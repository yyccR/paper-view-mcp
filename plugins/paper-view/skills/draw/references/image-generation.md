# Image inputs and native parameters

Read the live `list_image_models` result before choosing parameters. The server forwards `model_parameters` as native inference body fields; it does not guarantee that every upstream model, configured gateway, or account accepts every field. Provider validation errors must be reported, not silently ignored or retried as a different request. Model IDs stay under server configuration; credentials, endpoints, HTTP headers, local filesystem paths, and shared upstream file IDs are not inference inputs.

## Inputs

- `prompt`: 1–32,000 characters.
- `reference_images`: array of public HTTP(S) URLs or `data:image/png;base64,...`, JPEG, or WebP data URLs. Never pass a local path, raw unprefixed Base64, private-network URL, or a chat attachment handle. An attachment must first be read and encoded or uploaded with authorization. Each inline image is limited to 10 MiB decoded; the combined request is limited to 24 MiB. Read the model's `max_reference_images` from the catalog (currently 3 for Nano Banana, 14 for other Nano Banana variants, 16 for GPT Image).
- `mask_image`: public URL or data URL for a PNG with an alpha channel and transparent pixels, matching the first reference's dimensions. Requires a GPT Image model and at least one reference. Transparent regions mark the region to edit.
- `model_parameters`: JSON object of provider-native inference settings. Use exact REST field names and nested objects. Do not move these fields into the prompt.
- `session_id`: destination canvas only. For “change the previous image”, pass its `image_url` in `reference_images` explicitly.

For a local reference, read the file and construct `data:<actual MIME>;base64,<encoded bytes>`. Do not echo the encoded image back to the user. SVG drawing tools still reject embedded `<image>`; reference-based model generation does not change that rule.

## GPT Image

Use Images API body fields in `model_parameters`, for example:

```json
{
  "size": "1536x1024",
  "quality": "high",
  "n": 2,
  "background": "transparent",
  "output_format": "webp",
  "output_compression": 90
}
```

Other native fields include `moderation`, `complexity`, `safety_identifier`, `user`, `stream`, `partial_images`, and model/access-specific `frame_count`, `frame_duration_ms`, `svg`, and `markup`. The live schema and official provider documentation describe the current fields. Future native body fields are forwarded too; upstream decides support. Supply model, prompt, references, and mask through their named tool arguments, not inside this object.

`size` overrides the shorthand `image_size`/`aspect_ratio`. Explicit dimensions must satisfy the configured model's edge, pixel, multiple-of-16, and aspect ratio limits. Billing uses the resulting 1K/2K/4K tier; `size="auto"` reserves the 4K tier. Use identical options when quoting and submitting. Avoid contradictory `generation_quality` and native `quality`.

`n` supports 1–10 outputs, charged per delivered image. `stream=true` allows upstream streaming; `partial_images` requires streaming. The worker consumes previews and returns every completed output through `get_image_job`; it does not stream previews through MCP.

Transparent backgrounds require PNG/WebP. Compression applies to JPEG/WebP. GIF frame options require GIF output. GIF/SVG cannot use streaming, partial images, or masks; SVG requires `n=1`. These preview outputs depend on upstream model/account access. `markup` requires GPT Image 2.5 references, accepts `{"image_url":"..."}`, and cannot combine with a mask. GPT Image 2 does not accept `input_fidelity`.

Official reference: https://developers.openai.com/api/reference/resources/images/

## Nano Banana / Gemini

Use the native `generateContent` body structure:

```json
{
  "generationConfig": {
    "temperature": 0.8,
    "topP": 0.95,
    "seed": 42,
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {"aspectRatio": "16:9", "imageSize": "2K"},
    "thinkingConfig": {"thinkingLevel": "HIGH"}
  },
  "tools": [{"googleSearch": {}}]
}
```

The example shows field placement, not a claim that every variant accepts all of these options. Other native body fields such as `systemInstruction`, `safetySettings`, `toolConfig`, `cachedContent`, and `labels`, plus generation fields such as `topK`, `maxOutputTokens`, `stopSequences`, and `candidateCount`, are forwarded unchanged. Preserve native field spelling; put generation fields inside `generationConfig`, not at the top level.

Nested `imageConfig` overrides the shorthand ratio/size, and its effective size determines the Credit tier. `responseModalities`, when supplied, must include IMAGE. `candidateCount` reserves per candidate (1–8); model support is validated upstream, and only delivered final images are charged. Thought images are not delivered. ImageSize 512, when supported upstream, uses the lowest 1K billing tier. Nano Banana's original 2.5 Flash Image model remains 1K only. Model-specific search, thinking, safety, and response settings may differ by the configured Gemini/Vertex/compatibility gateway.

Official references: https://ai.google.dev/api/generate-content and https://ai.google.dev/gemini-api/docs/image-generation
