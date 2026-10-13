# The Wunderstrahl's beam and effects (docs/219, the FX track)

`make_fx.py` generates everything the beam draws; never hand-edit its outputs. `preview.py` renders the review sheets in
`art/wunderstrahl/fx_review/` (a schematic simulation of the generated files, not the engine): `beam_diagram.png`,
`view_1p.png`, `view_3p.png`, `contact_sheet.png`, `textures.png`, and one second of motion in `anim_1p.gif` /
`anim_3p.gif` (30 fps, the worst frame rate the helix must read at). The preview does not model the materials'
brightness (scaleRGB), bloom or the engine's own beam geometry: judge layout, timing and motion there, brightness in game.

```
python tools/wunderstrahl/fx/make_fx.py --out-root tmp/wunderstrahl/stage           # write (stage); textures go to the repo
python tools/wunderstrahl/fx/make_fx.py --check --out-root tmp/wunderstrahl/stage   # the gate: regenerate, validate, compare
python tools/wunderstrahl/fx/make_fx.py --selftest                                  # planted faults (one per major rule), each caught by its own rule
python tools/wunderstrahl/fx/make_fx.py --vendor [--force]                          # re-extract the donors (sha-pinned)
python tools/wunderstrahl/fx/preview.py                                             # the review sheets
```

Outputs: `share/raw/fx/tod/wunderstrahl/fx_ws_*.efx` (10), `source_data/tod2_wunderstrahl_fx.gdt` (2 beams, the flame
table, 6 materials `mtl_tod2_wsfx_*`, 5 images `i_tod2_wsfx_*`), `model_export/tod_wunderstrahl_fx/*.png` (5 textures,
always written to the repo; the folder holds only generated textures, so a stray PNG is retired on write and fails
`--check`). The `wsfx` prefix keeps clear of the art track's `mtl_tod2_ws_*` / `i_tod2_ws_*`; the name check reads the
repo, the private root and the stage's GDTs.

Donors (`donor/`, every byte pinned in `donor/provenance.json`): the Purifier's beam block (`t7_beams.gdt`
flamethrower_beam), the WaW port's flame table block (`flame_firstperson`), `beam.awi` + `flametable.awi` (every field
is range-checked against them), two stock elements (`fx_raz_dest_weak_point_exp`: spark tail, flame), and the two
material types' techsets (verified to exist).

LOCKSTEP: `BEAM_RANGE = 2400` = `TOD_WS_RANGE`, `BEAM_LAUNCH_SPEED = 6000` = `TOD_WS_LAUNCH_SPEED` (module-level lines,
read by `tools/wunderstrahl/test_wunderstrahl.js`). When `_tod_wunderstrahl.gsc` is in the tree (the stage first, then the
repo), `fx_ws_zombie_burn` must end inside `TOD_WS_BURN_LIFE` and `fx_ws_disintegrate` / `_nl` inside `TOD_WS_DIE_LIFE`
(minus one frame).

Zone: the main session's `install.py` writes an `fx,tod/wunderstrahl/<name>` line for every `.efx` in the folder (so
`fx_ws_disintegrate_nl` too; the script must also precache it before playing it). The beams, flame table, materials and
images come in as the weapon's dependencies; explicit `beam,tod2_ws_beam_1p`, `beam,tod2_ws_beam_3p` and
`flametable,tod2_ws_flametable` lines are optional and use valid keywords (`beam,` as the repo's `beam,tod_archer_cable`;
`flametable,` as the stock `core_common.csv`'s `flametable,default_flame_firstperson`). Never zone the materials bare.
The sync needs the `Copy-Tree` line for `model_export\tod_wunderstrahl_fx` (`tools/wunderstrahl/wire.py` carries it).
`wire.py` gates `make_fx.py --check` in `build_map.ps1`; `--selftest` (read-only, a few seconds) belongs beside it.

The kill effects' lane (`KILL_FX_LOOPING`, on): the script plays `fx_ws_zombie_burn` / `fx_ws_disintegrate` / `_nl`
through `tod_ability_fx::burst_at`, a tag_origin host the SERVER plays them on and deletes after `TOD_WS_BURN_LIFE` 1.0 s /
`TOD_WS_DIE_LIFE` 2.0 s. CLAUDE.md says server one-shot effects render nothing and points at a looping FX on a host
(docs/162: the proven lane), so every element of those three LOOPS once per `ONCE_LOOP_MS` 5 s, forever: one round lands
inside the carrier, and the host's delete stops it before the loop comes round (checked). Set it False only if the
script moves them to a client lane (clientfield -> CSC `PlayFX`): there a looping effect loops until it is killed. One
more gap is the script's: `burst_at` plays one frame after spawning the host, where CLAUDE.md asks for two.

## What plays what

| Effect | Played by | Role | Elements / peak particles / lights |
|---|---|---|---|
| `fx_ws_origin_1p` | beam `tod2_ws_beam_1p` originEffect (loops at the viewmodel's tag_flash) | hot point, soft halo, six gold sparks orbiting the lens, motes streaming out; one small light (r 100). Nothing wider than 4 u across even if a size is a radius (the 1p rule) | 10 / 21 / 1 |
| `fx_ws_origin_3p` | beam `tod2_ws_beam_3p` originEffect (world model's tag_flash) | the same, larger; light r 160 | 10 / 21 / 1 |
| `fx_ws_aura_1p` | `tod2_ws_beam_1p` beamEffect, every 36 u, carried out at 150 u/s | the golden double helix (r 2.6, pitch 18, 8 segments a turn: a gold major strand, a thinner pale-lemon minor one), four orbs spiralling along it, a soft sheath, motes; lives 280 u from the lens, fades near the camera | 41 / 46 per instance / 0 |
| `fx_ws_aura_3p` | `tod2_ws_beam_3p` beamEffect, every 68 u, at 260 u/s | the same helix for teammates (r 4.6, pitch 34, 6 segments a turn), lives 600 u | 35 / 39 per instance / 0 |
| `fx_ws_impact` | both beams' blockedEffect (loops where the beam is stopped; +X out of the wall) + `blockedEffectSound tod_ws_impact_loop` | molten core, a still burn disc flat on the wall (generated texture; `IMPACT_DISC_FLAT` False = a camera-facing glow), glow, molten sparks + blinking droplets, orbs splashing, a lit smoke wisp; one flickering light (r 210). The core and disc fade inside 12-36 u | 8 / 58 / 1 |
| `fx_ws_tip` | both beams' targetEffect (the beam's end in open air, 2400 u out) | a soft fizzling flare and motes; no light | 3 / 12 / 0 |
| `fx_ws_lens_cool` | both beams' deathEffect (one-shot at the lens after the release) | fading glow, dimming hot point, heat wisp, three or four cinders (1p-safe; true one-shots - the engine plays it and nothing deletes it). No beam in the tools' GDTs sets a deathEffect (0 of 96, 93 of them stock), so it may never play - harmless | 4 / 8 / 0 |
| `fx_ws_zombie_burn` | script `burst_at`, on a zombie the beam passes (<= ~3/s each) | flash, yellow sparks, embers, two flame licks, soot puff; orientation-free; loops once per 5 s on its 1.0 s carrier | 5 / 33 / 0 |
| `fx_ws_disintegrate` | script `burst_at`, at the torso on the kill | flash + pop + shock ring, ember burst, orbs scattering, dark ash puff; one small light flash (r 180, 0.22 s); orientation-free; loops once per 5 s on its 2.0 s carrier | 7 / 48 / 1 |
| `fx_ws_disintegrate_nl` | script, the same kill once kills come fast (NOT played yet: the staged script precaches only the two above) | the same without the light. Suggested per-holder cap: lit up to ~4 kills/s, `_nl` up to ~8/s, nothing above (a kill costs ~40 particle-seconds either way; four holders in one crowd near the cap reach ~4,000 particles against FX_ELEM_LIMIT 4096). Drop it from `EFFECTS` if the script will not use it | 6 / 48 / 0 |

A whole beam at the full 2400 u: ~442 particles blocked / ~396 in open air for 1p, ~429 / ~383 for 3p (budget 480; 8-9
aura instances carry the swirl, the rest are empty). `make_fx.py` prints the live numbers on every write.

How the helix works: each aura instance carries exactly two full turns and `beamEffectDistance` = 2 x pitch, so chained
instances tile one continuous double helix that slides outward (and so reads as spinning, ~8 turns/s). Its strands are a
bright gold major one and a thinner, dimmer, pale-lemon minor one: two equal strands repeat every half pitch, and at 30 fps
the helix moves half of that a frame - they would just swap places (a strobe the first animation showed). Told apart, the
pattern repeats every full pitch and a 30 fps frame moves it a quarter of that (`STROBE_FPS` / `STROBE_MAX`, checked).
Strand segments are 'line' sprites oriented along the helix by a tiny velocity (0.08 u/s). A point fixed on a sliding
helix only moves straight ahead, so each orb SLIPS back along its strand (`slip` -40 / -60 u/s, with the matching orbit;
the orbit speed is corrected for the engine's linear velocity interpolation and holds the strand to 0.05 u) - in the world
it spirals outward (~2 turns/s), it lives `reach / (speed + slip)` so it rides the whole swirl, and it never runs ahead of
its carrier past a wall. The aura's bounding box reaches back over the slipped orbs.

## The beams (tod2_ws_beam_1p / _3p)

`beamShape ribbon` wearing `mtl_tod2_wsfx_core_1p` / `_3p` (effect_lit_scroll_emissive_blend_nocull, scaleRGB 48 / 72,
no view falloff, scroll U -4.5 UV/s), width 0.8 -> 9 (1p) / 1.4 -> 14 (3p) over maxLength (the core texture's profile
gives a white-hot axis, a warm body, a faint halo and clear edges; at this brightness most of the ribbon glows), colour
(1, .80, .10, 1) -> (1, .68, .06, .85) (blue kept low so the glow stays yellow round the white-hot axis),
`maxLength 2400`, `useVirtualTarget 1`, `virtualTargetDistance 2400`, `virtualTargetMass 0`, `dieIfTooLong 0`,
`collisionMode nodes`, `collisionMask "shot and not body"`, `dieIfBlocked 0`, `launchSpeed 6000`, `retractSpeed 10000`,
`reverseRetract 0`, `leadin/leadoutDistance 0`, no gravity, every wave amplitude and weight 0, `numSegments 24`,
`uvMode "repeating horizontal"`, `textureRepeatLength 128 / 192`, `unblockedEffectSound ""`.

Why a ribbon with a profiled texture: it is the stock laser recipe. Every stock beam texture with an axis profile rides a
ribbon: Gorod Krovi's laser trap beams (`dlc3_laser_robot_trap`, `fxt_trail_laser`) and the lightning beams
(`fxt_lightning_beam_trail`; the i1024 material alone is on 21 beams, 20 ribbons and a cross). A ribbon must face the
camera round its axis (stock turret beams read from every side), and `beam.awi` says the shape scales "do not apply to
ribbon". The polygon shapes (triangle .. octagon; the teleport tubes are octagons) are closed tubes wearing textures that
tile across V, whose V mapping round the tube is not documented, so a profiled texture could band or stripe on them
(the Purifier's hexagon wears `gfx_trail_laser_em`, a material with no GDT record: its texture is inferred from the name).
`BEAM_SHAPE` is one switch: a closed shape gets the uniform tube texture and the 3p falloff back, and the gate checks the
texture that shape needs.

Brightness: by stock standards 48 / 72 is modest (stock emissive effect materials have a median scaleRGB of 64; the
core's own material type has 4 stock users at 128-1024). In THIS dark map it is bright: the Archer's charge ring is 1,
the crown's grid lines 8 (docs/164: each doubling = +1 stop), the lit sign card 16 - so the core sits ~1.6-2.2 stops
above the sign card, the "really super strong laser". At the first look, check that targets stay readable round the
crosshair, where the 1p beam runs. It is ~4x (1p) / ~6x (3p) the gold strands (12), so it is the hottest thing in the beam
while the swirl keeps its colour.

## The flame table (tod2_ws_flametable)

The gas weapon's own flame stream, made invisible: fire / drips / smoke brightness 0, smoke max alpha 0, fuel and flame
streams 0.1 u wide and 0.01 u long, chunks 1 u, the longest spawn intervals, an empty fire window, every sound field
empty, every material slot `mtl_tod2_wsfx_stream` - the laser core's image premultiplied (`i_tod2_wsfx_core_add`) in an
ADDITIVE material (effect_lit_emissive_add, scaleRGB 8; the type already links in this map: the Archer's charge ring):
brightness 0 adds nothing, where the blend core material would draw black quads; anything that does draw reads as a
thin yellow thread, whether the additive pass reads alpha or not. `heat` stays empty. The stream is straight and fast (2000 u/s, no gravity, 0.5 s) so its
`streamPrimaryLight` (warm yellow 0.85 / 0.62 / 0.16, radius 300 + flutter 30) travels along the beam.

**Recommendation: leave the weapon's `flameTableFirstPerson` / `ThirdPerson` EMPTY for the first build** (today
`install.py` lines 137-138 set both to `tod2_ws_flametable`; blank them there and skip the optional `flametable,` zone
line, or keep them and accept the unproven path). No stock beam
weapon pairs its beam with an authored flame table: the Dragon Gauntlet's (`wpn_t7_zmb_dlc3_gauntlet_dragon.gdt`) names
`default_laser`, which the asset lists know only as a LASER asset, and the Panzer's (`mechz_spiki.gdt` lines 27474-27487,
which ran in Map One's native builds) leaves both fields empty beside `panzer_flame_beam`. The table is the option for a
second pass (its light along the beam is the one thing it adds).

## Assumptions to check in the first native look (the native look is unverified until a build and the user's playtest)

0. **Do the kill effects and the kill light render at all?** They ride `burst_at` (a server host, one frame of
   replication; no user console holds a `[TOD_ABFX] BURST` line yet), authored for the looping lane (`KILL_FX_LOOPING`).
   If they do not show: two frames before playing (CLAUDE.md), or a clientfield -> CSC lane with `KILL_FX_LOOPING = False`.
1. **beamEffect instances are born at the lens and retired at the beam's end** (the Purifier's emitter is timed for it).
   If the engine fills the beam at ignition instead (or drops instances as the beam extends at 6000 u/s), the swirl shows
   full-length for ~1.9 s (1p) / ~2.3 s (3p) after each trigger pull, then recedes to its reach. That pre-fill peaks at
   ~67 x 46 = 3,082 live particles for the 1p beam and ~36 x 39 = 1,404 for a 3p beam, against `FX_ELEM_LIMIT(4096)`
   (docs/162: the Radiant string is verified, the game limit inferred; past it new elements are skipped, nothing
   crashes). Levers if it shows: a 1p-aura `spawnRange` of ~360 (camera distance; the semantics are [INFERRED] in
   docs/162, so not used blind) so far instances spawn nothing, or fewer segments. An instance not retired at a wall would
   pass it (the orbs slip BACK along the strands, so none run ahead).
2. **A 'line' sprite points along its own (graph) velocity**, as in the IW engine: that is how each strand segment lies
   along the helix. If it followed its host's motion instead, the strands would read as dashes along the beam.
3. **Sprite size = full width** (one stock box supports it; the elites' preview assumes radius). The strict 1p checks
   already read a size as a radius (`SIZE_TO_WIDTH` 2), so the effects at the shooter's eye stay under 4 u either way; if
   it is a radius, the other sprites are twice as wide as drawn in the preview.
4. **U grows from the lens**: `CORE_SCROLL_U` negative flows outward. Flip the sign if the core shimmer runs into the gun.
5. **A ribbon faces the camera round its axis, with V across it.** If the core looks like a flat bar or vanishes from
   some side, `BEAM_SHAPE` is the knob (a closed shape then wants a texture uniform across V).
6. **The blocked frame**: +X out of the surface (the Purifier's blocked flames splash in local Y/Z just off X = 0.5..5).
   If the burn disc stands out of grazing walls, set `IMPACT_DISC_FLAT = False`.
7. **The aura instances' roll round the beam** is not pinned by anything we know: the helix is symmetric, so any roll
   reads the same (the orbs' starting phases shift, harmlessly).
8. **deathEffect** is unused by all 93 stock beams (and the 3 ported ones), so `fx_ws_lens_cool` may never play, or play
   only on some releases.
9. **Brightness**: core scaleRGB 48 / 72, particles 12-16 (the stock ray_thin template's material is 8), set from stock
   evidence rather than measured in game: the first look decides (`CORE[...]['scale_rgb']`, `PARTICLE_SCALE_RGB`).
10. **Lights**: one beam carries at most the origin light (1p r 100 / 3p r 160), the impact light (r 210) and, only if
    the flame table is used, the stream light (r 300 + 30) - each shadowless, in all four lighting states, at most two
    alive per element - plus one kill flash per lit disintegrate.
11. **Width over the beam's length**: `beam.awi` defines endWidth at maximum length. If the engine interpolates over
    the CURRENT length instead, a beam blocked at 100 u flares to 9 / 14 u at the wall: lower `end_w` if it does.
12. **The near 1p swirl** (8 segments a turn, straight line sprites) can read as octagons right by the lens, where the
    loops are seen almost end-on; more segments cost particles against the 480 beam budget (`AURA['1p']['segs']`).

Knobs (all in `make_fx.py`): `AURA` (helix, speed, reach, alpha, orbs), `ORIGIN`, `CORE` (widths, scaleRGB, repeat,
falloff), `BEAM_SHAPE`, `PARTICLE_SCALE_RGB`, `CORE_START/END_COLOR` (lower blue first if the beam reads white),
`CORE_SCROLL_U`, `DIE_LIGHT`, `IMPACT_DISC_FLAT`, `KILL_FX_LOOPING` / `ONCE_LOOP_MS`, `STREAM_LIGHT_*`, `TARGET_EFFECT`
(`fx_ws_impact` to put the wall splash at the open-air end as docs/219 first said).
