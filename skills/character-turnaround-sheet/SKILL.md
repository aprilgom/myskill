---
name: character-turnaround-sheet
description: Use when a user provides or references a character image and wants a turnaround, model sheet, character sheet, reference sheet, expression sheet, pose sheet, animation reference, or consistent multi-view character design.
---

# Character Turnaround Sheet

## Overview

Create production-useful animation reference sheets from one or more character images. The priority is identity consistency across views, not making a prettier redesign.

Use the `imagegen` skill when the requested output is a raster image. If the user only wants a prompt, spec, or critique, do not generate an image unless asked.

## Workflow

1. Classify the request.
   - If the user wants an image asset, use `imagegen` after this skill's analysis.
   - If the user wants only a prompt, spec, critique, or production notes, stay text-only.
   - If no source image is available, ask for one unless the user explicitly wants a generic template.

2. Label every input image.
   - Main identity reference
   - Style reference
   - Outfit or accessory reference
   - Expression/pose reference
   - Edit target

3. Choose the sheet type and views.
   - Turnaround/model sheet: default to front, 3/4 front, side, 3/4 back, and back.
   - Character sheet: turnaround plus expressions, palette, and detail callouts.
   - Expression sheet: multiple facial expressions with one locked head design.
   - Pose sheet: action poses with locked proportions, costume, and silhouette.

4. Extract identity locks before prompting.
   Record the silhouette, proportions, face shape, hairstyle, outfit construction, palette, accessories, markings, and distinctive asymmetry. These are hard constraints.

5. Handle missing side/back information.
   Infer conservatively from visible seams, hairstyle volume, and accessory placement. Ask only when hidden details are central to the request or invention would change the design materially.

6. Generate or write the deliverable.
   Use the prompt pattern below for raster generation. For text-only requests, return the same constraints as a reusable prompt/spec.

7. Validate the result.
   Inspect the output against the verification checklist. If a generated sheet fails identity consistency or sheet usability, iterate once with a targeted correction before delivering, unless the user asked for a single draft only.

## Input Triage

Before generating or writing a prompt, identify:

- Source image role: main identity reference, style reference, outfit reference, accessory reference, or edit target.
- Output type: turnaround/model sheet, character sheet, expression sheet, pose sheet, or combined sheet.
- Required views: default to front, 3/4 front, side, 3/4 back, and back for turnarounds.
- Style lock: preserve the source art style unless the user explicitly asks for another style.
- Identity locks: silhouette, proportions, face shape, hairstyle, outfit, palette, accessories, markings, and distinctive asymmetry.

Ask only when a missing choice would materially change the output, such as adult/child age ambiguity, hidden back details, or whether to invent unseen costume details. Otherwise make conservative assumptions and state them briefly.

## Sheet Types

- **Turnaround / model sheet:** Neutral standing character, same scale, same pose family, multiple angles, plain background.
- **Character sheet:** Turnaround plus close-ups, expression row, hand/prop/detail callouts, and palette swatches.
- **Expression sheet:** Multiple facial expressions with the same head design, angle, and style.
- **Pose sheet:** Action poses that preserve the same body proportions, costume, and silhouette.

For animation production, prefer clean orthographic or near-orthographic views over dramatic camera angles.

## Prompt Pattern

When generating from a character image, include this structure:

```text
Use case: illustration-story
Asset type: animation model sheet / character reference sheet
Primary request: Create a clean production model sheet based on the provided character image.
Input images: Image 1 is the main identity, costume, palette, and art-style reference.
Identity lock: Preserve the character's silhouette, body proportions, face shape, hairstyle, outfit construction, colors, accessories, markings, and any asymmetrical details from the source image.
Sheet layout: White or light neutral background, aligned full-body views in one row, consistent scale and eye-line, clear spacing, no overlapping figures.
Views: Front, 3/4 front, side profile, 3/4 back, back.
Pose: Neutral standing A-pose or relaxed model-sheet stance, arms positioned to reveal costume details, feet grounded on the same baseline.
Style: Match the source image's rendering style and line quality. Clean animation reference, readable shapes, no painterly background.
Details: Add small callouts only if useful for hidden or important costume/accessory details.
Avoid: redesigning the character, changing age/body type, changing outfit, changing palette, extra characters, dramatic lighting, perspective distortion, cropped body parts, text labels unless requested.
```

For a combined character sheet, add:

```text
Add a compact expression row with neutral, happy, angry, sad, surprised, and determined expressions.
Add small palette swatches and close-up detail callouts for important accessories or markings.
Keep the sheet organized and uncluttered.
```

## Verification

After generation, verify the result and cite concrete evidence in the final response when useful:

- Same character across every view, not variants or siblings.
- Consistent height, head-to-body ratio, limb length, body type, and silhouette.
- Hair, clothing layers, accessories, markings, and asymmetry preserved from all angles.
- No missing side/back information unless it was impossible to infer.
- Model-sheet usability: full body visible, aligned baseline, neutral background, readable details.
- No unwanted text, watermarks, extra characters, duplicate limbs, merged accessories, or cropped figures.

Evidence to collect:

- Which source image was treated as the identity reference.
- Which views or sheet elements were requested and whether they are present.
- Any visible mismatch that required an iteration.
- Any inferred side/back details that were not visible in the source.

If a generation fails validation, iterate with the smallest targeted correction. Name the mismatch directly in the next prompt, for example: "The side and back views changed the hairstyle; keep the exact same hair volume, bang shape, and tied ribbon from the front reference."

## Handling Unseen Details

If the source image does not show the side or back:

- Infer conservatively from visible clothing seams, hairstyle volume, and accessory placement.
- Do not invent major props, logos, patterns, or color blocks.
- If the back design is central to the request, ask whether to invent a back view or keep it minimal and consistent.

## Output Format

For generated image output, include:

- The generated sheet shown inline when possible.
- The saved file path if the asset was moved into the workspace.
- Verification notes: identity preservation, requested views present, and any visible limitations.
- A brief note of any assumptions, especially inferred side/back details.
- The final prompt if the user is likely to reuse or refine it.

For prompt-only output, include:

- A ready-to-use prompt with labeled constraints.
- An avoid list focused on identity drift and model-sheet failures.
- Optional negative prompt wording if the user's target tool supports it.
