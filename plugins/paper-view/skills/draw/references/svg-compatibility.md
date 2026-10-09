# SVG compatibility for Paper View MCP drawing

Use this guide for SVG submitted through `draw_svg_layer` or `update_svg_layer`. It reflects production checks on 2026-10-09. The Board's other import paths may have different rules.

## Four-format drawing subset

The MCP accepts these elements: `svg`, `g`, `defs`, `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `text`, `tspan`, `linearGradient`, `radialGradient`, `stop`, `marker`, `title`, and `desc`. Use a numeric four-value `viewBox`. Use direct attributes for fill, stroke, opacity, font, and transform; give definitions unique IDs and reference them with `url(#id)`. Local gradients and start/end markers are suitable for ordinary diagrams. Use explicit colors on marker paths.

The MCP attribute allowlist is: `id`, `viewBox`, `width`, `height`, `preserveAspectRatio`, `x`, `y`, `x1`, `x2`, `y1`, `y2`, `cx`, `cy`, `r`, `rx`, `ry`, `d`, `points`, `transform`, `fill`, `fill-rule`, `stroke`, `stroke-width`, `stroke-linecap`, `stroke-linejoin`, `stroke-dasharray`, `stroke-dashoffset`, `opacity`, `fill-opacity`, `stroke-opacity`, `font-family`, `font-size`, `font-weight`, `font-style`, `text-anchor`, `dominant-baseline`, `letter-spacing`, `offset`, `stop-color`, `stop-opacity`, `gradientUnits`, `gradientTransform`, `markerWidth`, `markerHeight`, `refX`, `refY`, `orient`, `marker-start`, `marker-mid`, `marker-end`, and `pointer-events`. This is the upload allowlist, not a promise of native PPTX support; the exceptions below still apply.

An end-to-end production sample with a radial gradient, polygon, positional `tspan`, and explicit polygon arrowheads downloaded as SVG, PNG, JPEG, and editable PPTX. The PPTX contained nine native shapes and a native gradient, with no picture. The earlier flow, dense-chart, gradient, and scientific-figure samples also downloaded in all four formats. This is evidence for those tested combinations, not a guarantee for arbitrary SVG.

Keep each submitted layer at most 512 KiB, at most 4,000 XML elements including the root, and at most 64 levels deep. A node's text or attribute value must be at most 20,000 characters. Split a large diagram into logical layers with the same `viewBox`, then inspect alignment in Board. Keep tightly aligned details together.

## Rewrite before submission

| SVG feature | Observed MCP behavior | Vector-friendly replacement |
| --- | --- | --- |
| `clipPath` / `clip-path` | Rejected | Draw the visible outline directly as a path, polygon, circle, or rounded rect. |
| `mask` | Rejected | Use explicit shapes with opacity or a local gradient; pre-render genuinely soft masking as a separate raster asset. |
| `pattern` | Rejected | Repeat ordinary shapes or use dashed strokes. |
| `symbol` / `use` | Rejected | Expand each instance into concrete shapes and groups. |
| `filter` and shadows | Rejected | Layer offset translucent shapes for simple shadows; use a raster asset for complex effects. |
| `style`, `class`, blend modes, `@font-face` | Rejected | Move supported presentation properties onto each element; choose an installed font and inspect text layout. |
| `image`, embedded/data images, external URLs | Rejected | Use an image-generation result or Board image import as a separate raster element; do not describe it as vector-editable. |
| `foreignObject` | Rejected | Rebuild labels and containers with SVG text and shapes. |
| `animate` and other animation | Rejected | Draw the intended static frame. Motion needs a separate media workflow. |
| `tspan dx/dy` | Rejected | Use explicit `x`/`y` on a `tspan` or separate `text` elements. |

External CSS, fonts, scripts, event handlers, and unresolved `url(#id)` references are outside the MCP drawing subset. Do not silently remove required content: simplify the effect, use a separate raster element, or tell the user which part cannot remain editable.

## PPTX-specific check

`marker-mid` is accepted by the MCP and appears in SVG/PNG/JPEG, but the native PowerPoint converter rejects it. Draw middle arrowheads as explicit filled `polygon` or `path` elements. A production sample with `marker-mid` failed its selected-element PPTX download; the equivalent drawing with polygon arrowheads succeeded in all four formats.

`gradientTransform` is upload-allowed, but a production drawing containing a transformed linear gradient failed selected-element editable PPTX download with "当前内容无法转换为可编辑 PowerPoint。" Use an ordinary linear or radial gradient without `gradientTransform` when editable PPTX matters. A matching control with the angle set through `x1`/`y1`/`x2`/`y2` exported with native shapes and a native gradient. Verify the exported slide for the exact drawing.

Use the selected SVG element's Download menu for editable PPTX. The Board menu's whole-board PPTX export places the entire canvas as one picture. For a requested editable PPTX, download it, check that it opens, and inspect its visual result; do not infer success from the presence of a PPTX option. Very large or dynamic selections can use picture mode, so report that loss of element editability.
