# 167 — THE RENDERED SKY: image-model BILLBOARDS for the city's ad screens (12 images)

<!-- art-pack
name: sky3d_billboards
refs:
  docs/sky_preview/sky3d_ingame_city.png | the rendered city at game resolution: the coloured rectangles on the towers are the AD SCREENS your billboards replace. Match this palette (v4 palette: near-black structure, saturated cyan / magenta / violet / green / orange neon, warm amber windows; RED is reserved for the moon, the sign and the origin tower) and this darkness.
  docs/sky_preview/sky3d_ingame_moon.png | the hero view: the blood moon over the title gantry. Nothing you make should compete with this red; billboards are supporting cast.
preview: 1920x1080
-->

> **STATUS: DELIVERED AND SHIPPED 2026-09-25 (v6, docs/166 §8).** The drop (`Downloads/files - 2026-09-25T101516.779.zip`: twelve RGB PNGs at the exact sizes, 40-68 % near-black, no red, hues cyan x2 / magenta x2 / violet x2 / green x2 / orange x4 - the gold pair came back orange-gold, accepted) is installed as `art/sky3d/billboards/ad_01..12.png` at 512 px on the long side; `render_sky3d.ps1` picks the folder up by default and `screen_mi()` gives each screen an image of its own orientation. Measured with Blender's Python (`Image.pixels` = display bytes). Earlier: brief written 2026-09-24, reworded for the v4 palette 2026-09-25. Companion to docs/166 §6 (the rendered sky).
> Pack: `.\tools\make_art_pack.ps1 docs\167_sky3d_billboards_art_prompt.md` →
> `~/Downloads/tod_sky3d_billboards_art_pack.zip` (run it AFTER a `render_sky3d.ps1` has written
> the two `sky3d_ingame_*.png` refs). Install: drop the PNGs in `art/sky3d/billboards/` and
> re-render with `--screens-dir art\sky3d\billboards` (75 % of the ~600 ad screens wear one, the
> rest keep the procedural mosaic); `build_city.py` normalises each screen's metre UVs by its own
> size, so any aspect works — the image is stretched to the screen, which is what a billboard does.
> The screens are 0.1–0.4° tall in the sky (12–60 px at 1080p): what reads is COLOUR, one big shape,
> and maybe one word. Detail is wasted.

<!-- PACK:BEGIN -->
# TOWER OF DOOM II — twelve billboards for a night megacity (12 files)

## Open `sky3d_ingame_city.png` first, then `sky3d_ingame_moon.png`

The first is the city your billboards live in: a rendered night megacity of near-black towers wearing
saturated neon panels (cyan, magenta, violet, green, orange) and warm amber windows under a black space
sky with nebula and planets, seen from a tower. The second is the hero view with the blood moon
and the title sign: your billboards must never be brighter or redder than that sign. The small coloured rectangles on the buildings
are the ad screens. Your twelve images go onto those screens, hundreds of metres away, so each
one is only a few dozen pixels tall on the player's monitor. Design for that distance: one bold
colour field, one big shape or face or glyph, at most one short word. No fine print, no small
logos, nothing that needs to be read up close.

## Deliverables

| file | size | orientation | content |
|---|---|---|---|
| `ad_01.png` … `ad_06.png` | 1024 × 1024 | square | six different ads |
| `ad_07.png` … `ad_10.png` | 1536 × 1024 | landscape | four different ads |
| `ad_11.png`, `ad_12.png` | 1024 × 1536 | portrait | two different ads |

PNG, RGB, no alpha, no transparency. Fill the whole canvas edge to edge (the screen shows all of it).

## Palette and mood — hard rules

- **Dark.** Every image must be at least half near-black. The city is dark; a bright white billboard
  would be a searchlight. Light comes from the coloured shapes, not from a white background.
- **Colours:** the city's neon — cyan, magenta, violet, green, orange, gold — one or two per image,
  fully saturated on near-black. NO RED and no blood tones: red belongs to the moon, the title sign and
  the origin tower alone. No pastel, no daylight blue, no white backgrounds.
- **Subjects (one per image, your choice, in this spirit):** a masked face, a cybernetic eye, a
  hand holding a glowing vial, a hooded figure, a corporate glyph, a stylised skull, a bottle of
  something red, a blade, a circuit-brain, a helmet visor, a syringe, a rising sun logo. Evil
  corporate megacity, not friendly retail.
- **Text:** optional, at most ONE short word per image, huge and simple (OBEY, DRINK, SLEEP, BUY,
  RISE, ASCEND, DOOM, VOID). No sentences, no small text anywhere.
- **Style:** painted / photographic, glossy, with visible glow around the bright shapes, like a
  screen seen through haze. Not flat vector, not cartoon, not wireframe.

## Prompts (paste-ready; attach `sky3d_ingame_city.png` to each)

**Square ads (ad_01–ad_06):** "A 1024×1024 dark cyberpunk billboard advertisement, mostly black
background, one large glowing [SUBJECT] in [COLOUR] neon (cyan / magenta / violet / green / orange — never red) with soft glow, one giant
simple word [WORD] or no text, painted photographic style, seen through haze, no small text, no
logos, evil megacorporation mood. Match the palette of the attached city image."
Rotate the main colour so the twelve images cover the whole neon range (two cyan, two magenta, two violet, two green, two orange, two gold).

**Landscape ads (ad_07–ad_10):** same prompt at 1536×1024, composition left-to-right: the shape on
one side, the word on the other.

**Portrait ads (ad_11–ad_12):** same prompt at 1024×1536, a tall figure or bottle.

## Delivery checklist
- twelve PNGs, exact filenames and sizes above, RGB, no alpha
- each at least half near-black, no white backgrounds
- one subject and at most one word per image
- no red anywhere; the twelve images spread across cyan / magenta / violet / green / orange / gold

## Do NOT
- no white or bright backgrounds, no daylight colours, no green
- no small text, no sentences, no fine logos, no borders or frames (the screen has its own)
- no transparency, no watermarks
<!-- PACK:END -->
