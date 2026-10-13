# 150 — TOD II: THE EVIL SKY, THE SIGN, AND THE BACKDROP PATH (2026-09-20)

> **STATUS 2026-09-20 11:52 Eastern: FULL BUILD VERIFIED, UNPLAYED.**
> `node tools/gen_tod_sky.js --theme evil` → `source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr`
> 41,886,850 B (39.9 MB half, zip16), gain 0.02603 solved for score 0.324, linear
> RGB share 67/16/17, knee 4.16 % of pixels, seam 0.09× of its neighbours, 42
> previews in `docs/sky_preview/evil_*.png` (`evil_ingame_moon.png` = the sign at
> 0.96 texel/px). Render 2278 s: the machine ran at 70 % of nominal CPU (Balanced
> plan, i7-14650HX) for the first half — a normal run is ~6 min. The teleporter
> session's full build included this EXR: source/deployed hashes match, fresh
> sky IWI `7SQVLRM3ZWWD4VZ6TPCUEZ7N7F` (21,681,431 bytes), fresh LED, FF written
> 11:45:41 (179,327,872 bytes), all build checks passed at 11:52. Evidence:
> `tmp/teleporter_build/`. Deployment is still the shared TOD1 folder described
> in README. No game launch; checklist for the user's first look: §5.

The ask (user, 2026-09-20): the TOD1 cyber sky again but *"more evil and red
and darkness"*, at the quality of the two reference paintings (a chrome
"TOWER OF DOOM / CYBERCITY" sign on a gantry over a neon arena, a ringed
planet behind it), *"and yes a Tower of Doom II sign right on the outside"*.
Then: *"I need you to understand exactly how to make these images super sharp
with all the correct curves and details. Seems whenever we do this it's never
this high quality"* and *"these reference images are also AI generated so I'm
confused on how those AIs can build these images but we can't. Maybe it's the
file ext."*

## 1. The honest answer first: it is not the file extension

The references were **painted by an image model** — a diffusion network that
has seen millions of photographs and renders and synthesises lighting,
materials, reflections, haze and grime pixel by pixel. Our sky is **drawn by a
program** (`tools/gen_tod_sky.js`): boxes, tapers, lines, an analytic fog
model and hand-written shading rules. That is why every quality pass since
v17.71 (Lanczos resolve, 16k paint, three unsharp passes, the peak knee) made
the lines cleaner without ever making the picture look painted. Sharpening
sharpens edges; it cannot invent the lit glass, the wet floor, the volumetric
light the painting has. **The gap is the rendering model, not the resolution
and not the format.**

The two routes, and what each can and cannot do:

| | drawn (`gen_tod_sky.js`) | painted (image model) |
|---|---|---|
| lighting, materials, volumetrics | rules; flat fills, neon lines | real, the thing the refs have |
| a sphere that wraps, poles that do not pinch | by construction | only in a dedicated 360 mode; otherwise a seam and pinched poles |
| text | exact | cannot spell reliably; cannot be fixed after |
| exposure the map is lit by | solved to a target score (docs/104 §4) | unknown; every drop is a different brightness |
| repeatable, editable | every knob is a constant | a new roll each time |

So the pipeline built today does the split that uses each for what it is good
at: **the image model paints the city and the sky; the generator projects the
painting onto the sphere, draws THE SIGN on top, and runs the proven
exposure / sharpen / EXR tail.** That is `--backdrop` (§4). Until a painted
panorama exists, `--theme evil` (§2) ships the drawn version with the same
sign — the picture in `docs/sky_preview/evil_ingame_moon.png`.

### What "super sharp" can and cannot mean here
The sky is one 8192 × 4096 texture on a dome (BO3 rejected 16k, docs/104 §4g).
At the game's field of view (cg_fov 65 → 80.7° horizontal at 16:9) one screen
pixel at 1080p sees **0.96 texel** — the sky is already at native resolution
there. At 1440p it is 1.28 screen px per texel, at 4K 1.92: on a high-res
monitor the sky is softer than the world by exactly that factor and nothing in
the file can change it. Judge sharpness only on `*_ingame_*.png` crops at 1:1
(the 2048 equirect previews are 4× minified). Detail therefore has to come
from CONTENT — more, finer, better-lit things in the picture — which is the
image-model route again.

## 2. `--theme evil` — the palette turned to blood

Same drawn city, same lights, same exposure solve (target score 0.324, the
world's light budget does not move). What changed, in `THEMES.evil`:

| element | night (TOD1) | evil (TOD II) |
|---|---|---|
| sky gradient | indigo → violet | black-red zenith, ember horizon |
| the moon | pale chrome | BLOOD MOON (`sunTop/Mid/Bot` red-orange), r 5.5°, el 16° |
| glow dome | magenta / cyan | crimson / dark violet |
| clouds | violet lit magenta | ash lit crimson from below |
| nebula, dust | violet + blue | dark red, `nebDust` 0.55, `aurora` 0 |
| building hues | cyan 40 % … | red 34, orange 14, magenta 18, violet 12, gold 6, **cyan 10, blue 6** — cyan kept sparse as the wound in the red |
| mist, strata, shafts, storm | violet / pale | maroon, ember, red-orange |
| ground grid (new keys `ground/gline/gline5`) | cyan lines, magenta every 5th | red lines, ember every 5th (was hardcoded; night unchanged) |
| bloom colour | blue-white | red-orange |

`BODIES` (planets and black holes) used to be gated on `THEME === 'night'`;
they are gated on `T.moon` now, so evil keeps the giant, the moonlet, rust,
ice, Gargantua and the Maelstrom (their own colours stand — the warm holes
read as fire under a red sky).

## 3. THE SIGN — a gantry, not a sticker

`drawSign` / `GLYPHS` / `layoutLine` in `tools/gen_tod_sky.js`.

- **Where:** a vertical plane at `SIGN_D` 1000 — INSIDE the empty plaza
  (`INNER_R` 1100), so no building can ever stand in front of it — at the moon's
  bearing (`--sign-az <deg>` turns it). Main line centre el 11°, cap height
  3.6° (`SIGN_EL_MID`, `SIGN_CAP`); the chassis top at ~13.9°, the top truss to
  ~15°, so the moon (el 16, r 5.5 → lower limb at 10.5°) **rises from behind the
  gantry with its lower third hidden**, the reference's planet composition.
  Letters span ±17.9° of azimuth, the gantry ±22.7°: about half the screen at
  the game's field of view, as in the reference.
- **The structure:** two round masts (`roundBody`, tapering 0.20 → 0.11 em,
  in the skyline ledger, red beacons on top), a top and a bottom truss band
  (chords + X-braces every 0.55 em), a dark chamfered chassis (an octagon
  signed-distance field) with a neon border and two inner panel seams, two side
  light bars, "TOWER OF DOOM" with a small raised "OF", "II" in ember, and
  "CYBERCITY" as a tracked brand line below.
- **The letters are analytic distance fields.** Every glyph is a list of
  segments and circular arcs (`GLYPHS`: T O W E R F D M I C Y B); each pixel of
  the sign's angular box is ray-cast onto the plane (exact projection, no
  billboard approximation), and the tube profile is a function of the distance
  to the nearest stroke: a hot core, a coloured body, a darker glass rim,
  anti-aliased by the pixel's footprint on the plane, a soft glow beyond the
  tube, and a dark offset copy behind (the 3D extrusion). **A bowl is a true
  circle at any resolution** — the "actually curved lines" the user asked for
  in the v0.7 solids pass — and the 2048 preview draws the same sign as the
  8192 ship.
- **Depth:** the chassis, tubes and trusses write the depth buffer, so later
  curve items (air lanes, trails) stop at it.
- **Colours are theme keys** (`signMain/Num/Sub/Bar/Plate/Border/Truss/
  Extrude/MastHue/Beacon`): evil = blood-red title, ember II, cold-cyan brand;
  night = the reference's own palette (chrome-white title, magenta subline), so
  TOD1 can adopt the sign by rendering `--theme night`.
- **Flags:** `--sign-az <deg>` (bearing off the moon), `--sign-mirror` (see
  the checklist), `TOD_SKY_SKIP=sign`.

## 4. `--backdrop` — the painted panorama path

```
node tools/gen_tod_sky.js --theme evil --width 2048 --preview-only --backdrop <pano.png>   # 20 s preview
node tools/gen_tod_sky.js --theme evil --backdrop <pano.png>                                # the EXR
```

| flag | default | what |
|---|---|---|
| `--backdrop <png>` | — | 8/16-bit RGB / grey / palette PNG, non-interlaced (own reader, no ffmpeg) |
| `--backdrop-mode equirect|band` | equirect | the PNG is the full sphere (2:1, horizon on the middle row), or only a horizon strip |
| `--band-el lo,hi` | -12,40 | band mode: the strip's elevation range; the drawn zenith and floor stay |
| `--feather <deg>` | 4 | band mode: crossfade into the drawn caps |
| `--rotate <deg>` | 0 | turns the painting (0 = its centre under the moon and the sign) |
| `--flip-x` | off | mirrors it |
| `--seam-blend <deg>` | 1.5 | mirrored crossfade at the wrap for a painting that was not painted tileable |

Mechanics: the PNG is resampled onto the paint buffer with Lanczos-2 (wrap-
aware in x, streamed row by row — no second full-size buffer), the drawn
sky's bloom seeds under the replaced rows are cleared, **the drawn city is
skipped and only the sign items draw** (`it.sign`), then the resolve, the
sharpen passes, the peak knee, the tint, the gain solve, the seam check, the
EXR and every preview run exactly as for a drawn sky. Previews carry a `_bd`
tag (`evil_bd_ingame_moon.png` …) so the approved drawn set is never
overwritten by an import trial. The gain guard (0.012..0.048) is a NOTE, not a
throw, for a backdrop — a painting has its own mean; the world's light is still
held at the target score. Verified on a synthetic non-tiling panorama: the
centre marker landed under the sign (rotate 0, not mirrored), the wrap blend
brought the seam to 0.36× of its neighbours, the sign drew on top with the
masts in front of the painting.

The brief for the painting is **docs/151** (`tools/make_art_pack.ps1
docs\151_tod2_sky_panorama_art_prompt.md`). It asks for a 2:1 equirect,
horizon on the middle row, seamless, NO TEXT, the planet behind the centre
skyline, black / red / ember with one cyan accent, dark overall.

## 5. In-game checklist (the user tests)

1. **Does the title read the right way round?** A lat-long dome viewed from
   inside can be mirrored by the engine's UV winding; the previews cannot
   know. If "TOWER OF DOOM II" reads backwards in game: re-render with
   `--sign-mirror`, nothing else moves.
2. **Is the sign where you want it?** It is under the moon. `--sign-az <deg>`
   moves it round (positive = higher azimuth, the direction the previews call
   "right").
3. **Is it high enough over the parapets on the low floors?** The chassis
   spans el ~6..14°. If the walls hide its lower half from floor 1, raise
   `SIGN_EL_MID` (11 → 13) or shrink `SIGN_CAP`.
4. **Is the world's light right?** The score is held at 0.324 like v18.97; the
   linear RGB share moved from 22/27/51 to ~63/18/20 (red-dominant) — the
   arena's ambient will read warmer. If the world looks red-lit rather than
   red-skied, `--tint 1,1.1,1.1` (docs/104 §4b) pulls the light back without
   touching the picture's exposure.
5. **Sharpness:** compare 1:1 crops of `docs/sky_preview/evil_ingame_moon.png`
   against the game at 1080p; both should show the same tube edges. Softer in
   game at 1440p/4K is the texture cap (§1), not the render.

## 6. Bisect and knobs
`TOD_SKY_SKIP=sign,rings,…`, `--sign-az`, `--sign-mirror`, `--theme evil|night`,
`--backdrop …`, `--width 2048 --preview-only` for a 20 s look. Sign geometry
constants sit together at the top of the sign section (`SIGN_D`, `SIGN_EL_MID`,
`SIGN_CAP`); layout (runs, scales, stroke widths, tracking) is the `SG` object
where the sign is registered; glyph shapes are `GLYPHS`.

## 7. Files
- `tools/gen_tod_sky.js` — `THEMES.evil`, `THEMES.*.sign*`, `GLYPHS`,
  `layoutLine`, `drawSign`, the sign registration, `readPng`, the backdrop
  composite, the `it.sign` gate in the city pass, the gain-guard note, the
  `_bd` preview tag, the themed ground grid, `BODIES` gated on `T.moon`.
- `source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr` — the TOD II
  sky (same asset name: GDT, zone, map wiring unchanged).
- `docs/sky_preview/evil_*.png` — the drawn evil set; `evil_ingame_moon.png`
  is the sign at game resolution.
- `docs/151_tod2_sky_panorama_art_prompt.md` — the painting brief.
