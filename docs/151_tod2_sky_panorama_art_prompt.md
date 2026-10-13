<!-- art-pack
name: tod2_sky_panorama
refs:
  docs/sky_preview/evil_ingame_moon.png | THE TARGET COMPOSITION, drawn: the blood moon over the "TOWER OF DOOM II / CYBERCITY" gantry, red city, red floor grid. The painting REPLACES the drawn city and sky; the gantry is drawn on top of your painting afterwards, so leave the horizon centre free of competing signage.
  docs/sky_preview/evil_sky_equirect.png | THE LAYOUT: a 2:1 equirectangular panorama, horizon exactly on the middle row, the moon and the hero direction at the horizontal centre, left edge meets right edge. Your delivery must have this exact geometry.
  docs/sky_preview/evil_ingame_city.png | The drawn city's window/edge density seen at game resolution (1080p at the game's field of view). Match or exceed this density of lit detail; the game shows the sky at about one texel per pixel.
  docs/sky_preview/night_ingame_city.png | TOWER OF DOOM 1's sky (cyan, upbeat). What this map must NOT be: no cyan-dominant palette, no synthwave sunshine.
preview: 1920x1080
-->

# 151 — TOD II: THE PAINTED SKY PANORAMA (image-model backdrop for the evil cybercity)

**Status: BRIEF WRITTEN 2026-09-20, NOT YET SENT.** Companion to docs/150 (the
evil sky, the sign, and the `--backdrop` path in `tools/gen_tod_sky.js`).

## Why this brief exists

The user's reference images (the "TOWER OF DOOM / CYBERCITY" sign over a neon
arena, a ringed planet behind it) were painted by an image model. Our sky is
DRAWN by `tools/gen_tod_sky.js`: boxes, lines, analytic shading. A rasteriser
cannot reach painted lighting, materials and volumetrics no matter how it is
sharpened (docs/104 §4g, §4i–§4k were all sharpening passes); an image model
cannot spell, cannot wrap a sphere seamlessly and cannot hold the game's HDR
exposure. So the split is: **the image model paints the city and sky, the
generator projects the painting onto the sphere, draws the sign on top, and
runs the proven exposure / sharpen / EXR tail.** That is what `--backdrop` does.

## Install, when the drop comes back (`files (N).zip`)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'` — LOOK at the PNG:
   2:1, horizon on the middle row, no text, the left edge continues into the
   right edge.
2. Copy the PNG to `source_data/tod_skybox/_masters/i_skybox_tod2_evil_pano.png`
   (masters folder; the shipped asset is the EXR the generator writes).
3. Preview (20 s): `node tools/gen_tod_sky.js --theme evil --width 2048 --preview-only --backdrop source_data/tod_skybox/_masters/i_skybox_tod2_evil_pano.png`
   then open `docs/sky_preview/evil_bd_ingame_moon.png` (the sign over the
   painting) and `evil_bd_sky_equirect.png` (the whole sphere, the wrap).
   - painting's hero direction not under the sign → `--rotate <deg>` (+ moves
     the painting toward higher azimuth; the moon/sign bearing is the centre)
   - visible step at the wrap → `--seam-blend 3` (degrees of mirrored
     crossfade; default 1.5)
   - painting mirrored → `--flip-x`
   - the painting is only a horizon strip → `--backdrop-mode band --band-el lo,hi`
     (the drawn zenith and floor stay, feathered over `--feather` degrees)
   - too crisp / halos → `--sharpen 3:0.25` or `--sharpen none`
4. Ship: the same command without `--width 2048 --preview-only` writes
   `source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr` (the asset name,
   GDT, zone line and map wiring do not change).
5. FULL build; proof = a fresh content-hash sky `.iwi`. Flip this STATUS.

<!-- PACK:BEGIN -->
# TOWER OF DOOM II — the painted sky: ONE seamless 360° panorama (1 file)

## Open `evil_ingame_moon.png` and `evil_sky_equirect.png` first

`evil_ingame_moon.png` is the picture we drew ourselves: a blood moon over the
title gantry, a red wireframe city, a red floor grid. It is the COMPOSITION
and the PALETTE. Your painting replaces everything in it except the gantry
with the sign — that gantry is added on top of your painting by our tools,
centred on the horizon at the middle of the panorama, about 45° wide and from
the horizon up to ~14° above it. So the centre of your panorama is the hero
direction, and nothing there should compete with a sign (no other signage,
no big bright object sitting right on the horizon at the centre; a giant
planet BEHIND that spot, partly hidden by the skyline, is exactly right).

`evil_sky_equirect.png` is the GEOMETRY your file must have: a 2:1
equirectangular panorama. Horizon on the exact middle row. The full sphere:
top row = straight up, bottom row = straight down. The left edge must continue
seamlessly into the right edge.

## Deliverable

| file | size | format |
|---|---|---|
| `i_skybox_tod2_evil_pano.png` | **8192 × 4096** ideal; **4096 × 2048** minimum; if your tool caps lower, deliver its maximum at EXACTLY 2:1 (e.g. 3072 × 1536, 2048 × 1024) | PNG, RGB, 8-bit or 16-bit, non-interlaced, no alpha |

One file. No variants unless asked. Name it exactly as above.

## Hard rules

1. **2:1 equirectangular, full sphere.** Not a cylinder strip, not a fisheye,
   not a wide photo. Horizon on the middle row (row height/2). The very top
   rows and very bottom rows converge to single points, so keep them
   near-uniform (dark zenith sky at the top, black at the bottom) — no shapes
   that would pinch there.
2. **Seamless wrap.** The right edge continues into the left edge with no
   step in tone or content. Test it: shift the image by half its width and
   look at the join.
3. **NO TEXT of any kind.** No letters, numerals, logos or readable words on
   any sign, billboard or building. Billboards show abstract glyphs, bars,
   symbols, faces or static only. Our tools add the title afterwards.
4. **Palette: black, blood red, crimson, ember orange, dark maroon haze.**
   ONE cold accent, cyan, used sparingly (a few small signs, one rail line,
   a single holographic panel) so it reads as a wound in the red, not a
   second theme. No blue skies, no purple sunsets, no cyan-dominant blocks,
   no white light sources larger than a window.
5. **Dark overall.** The picture is a night sky the game lights the world
   with; a bright painting brightens the arena. Large areas must be near
   black. Highlights are small and saturated (neon strips, windows,
   beacons). No lens flares, no bloom haze filling the frame, no vignette,
   no film grain, no letterbox bars.
6. **Camera: a rooftop plaza in the middle of the megacity, at about the
   height of the mid-rise roofs.** Nearest towers ~15–25° tall above the
   horizon on all sides; a far ring of megastructures rising above them in
   haze; the city floor visible far below the horizon (street grids, lit
   avenues) fading to black straight down. Nothing closer than a wide plaza:
   no parapet, no railing, no foreground object.
7. **Sharp, photoreal concept-art rendering**, not painterly brush strokes,
   not cel-shaded, not pixel art, not a wireframe. Fine detail matters: the
   game shows the panorama at about one texel per screen pixel, so panel
   lines, window rows, cable trays and antenna lattices should be crisp.

## What to paint (all around, the hero direction at the centre)

- **Sky, upper half:** near-black, with a faint dark-red nebula and sparse
  stars near the zenith; thin ash-grey cirrus lit crimson from below; a light-
  pollution dome glowing dark red along the whole skyline.
- **Bodies:** a giant ringed gas planet (rust / ember bands, thin bright ring)
  low over the skyline BEHIND the centre — its lower third hidden by the
  towers, so the sign can stand in front of it; a small dark-red moon higher
  up and to one side; optionally a distant black hole with a thin hot
  accretion ring high on the opposite side.
- **Skyline, all 360°:** megatowers in black glass and dark steel with red
  neon edge strips, setback tiers, antenna masts with red aircraft beacons,
  rooftop dish arrays, cooling stacks venting lit steam; two or three
  landmark shapes (a stepped ziggurat, a gate-like twin tower with a sky
  bridge, a floating platform on searchlights); elevated ring highways on
  pylons with red tail-light streams; a single rail line in cold cyan; a
  few holographic panels (abstract symbols only); searchlight beams sweeping
  up; ground mist between the towers lit red from below.
- **Below the horizon:** the city floor far below — dark blocks, red-lit
  avenues in a grid, scattered ember windows, the glow fading to black at
  the nadir. No wireframe grid needed (our floor grid is drawn separately if
  we keep it); a real city floor is preferred.
- **Mood:** evil, oppressive, cathedral-scale, everything watching the arena.
  Not neon-party synthwave, not sunset, not cosy.

## Paste-ready prompt

> Seamless 360-degree equirectangular panorama, 2:1, horizon exactly on the
> middle row, full sphere from zenith to nadir. Night. A rooftop plaza in the
> centre of a vast dystopian cyberpunk megacity. Palette: near-black sky,
> blood red and crimson neon, ember-orange windows, dark maroon haze; a single
> cold cyan accent used sparingly. Megatowers of black glass and dark steel
> with red neon edge strips, setback tiers, antenna masts with red beacons,
> elevated ring highways with red tail-light streams, holographic billboards
> showing only abstract glyphs, searchlight beams, ground mist lit red from
> below, a far ring of megastructures in haze. A giant ringed gas planet low
> over the skyline at the centre of the panorama, its lower third hidden
> behind the towers; a small dark-red moon higher up; faint red nebula and
> sparse stars near the zenith; thin ash clouds lit crimson from beneath. The
> bottom half: the dark city floor far below, red-lit street grids fading to
> black straight down. Ultra-detailed photoreal concept art, cinematic,
> razor-sharp, high dynamic range. No text, no letters, no logos, no lens
> flare, no vignette, no people, no watermark, no border.

Attach `evil_ingame_moon.png` and `evil_sky_equirect.png` as references and
say: *"match this composition and palette; the sign is added later by us, so
paint nothing where it stands."* Attach `evil_ingame_city.png` and say:
*"this is how dense the lit detail must be at game resolution — at least this
many windows, edges and lights per building, painted rather than drawn."*
Attach `night_ingame_city.png` and say: *"this is the first map's sky — NOT
this palette."*

If your generator has a dedicated 360 / skybox / equirectangular mode, use it
(it handles the wrap and the pole pinch); pick its darkest sci-fi or cyberpunk
style and the prompt above.

## Delivery checklist

- [ ] one PNG, `i_skybox_tod2_evil_pano.png`, RGB, non-interlaced, width = 2 × height
- [ ] horizon on the middle row; zenith and nadir rows near-uniform
- [ ] left edge continues into right edge (shift by half the width and check)
- [ ] NO text, letters or numerals anywhere
- [ ] centre of the panorama on the horizon is clear of signage; the planet sits behind the skyline there
- [ ] palette black / red / ember with one small cyan accent; nothing blue, purple or cyan-dominant
- [ ] dark overall; no flare, bloom wash, vignette, grain or bars

## Do NOT

- do not write any text, even "abstract" text that could be read
- do not paint the title sign or any sign at the centre of the horizon
- do not deliver a non-2:1 image, a strip, a fisheye, or a stitched photo
- do not use the first map's cyan / magenta synthwave palette
- do not add a sun, a sunset, daylight, or a bright white sky
- do not put a large bright object (moon, planet disc) in the top 5 % of the image
- do not blur, soften, add film grain, or vignette
<!-- PACK:END -->
