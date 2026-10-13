# 166 — TOD II: THE RENDERED SKY (Blender + Cycles replaces the drawn sky) — 2026-09-24; v4 THE REFERENCE COPY 2026-09-25 (§6); v5 THE BIG CITY 2026-09-25 (§7); v6 THE COLOUR PASS + THE SPIRE CLUSTER 2026-09-25 (§8); v7 THE TITLE GATE 2026-09-29 (§9); v7b THE HERO SIGN + NO SHIPS 2026-09-29 (§9.7); v7c NO ASTEROIDS 2026-09-29 (§9.8); v8 COSMIC CYBERCITY 2026-09-29 (§10); v9 CLEARER SKYLINE + OMINOUS GATE 2026-09-29 (§11)

> **STATUS 2026-09-29 22:22:17 Eastern - v9 CLEARER SKYLINE + OMINOUS GATE (section 11): the current sky restores the imposing dark crimson title, reduces baked skyline content from 1,838 to 1,222 building groups (33.51%) and gives Skyrail a readable station/train. All 14 retained planet/moon groups clear the conservative skyline by at least 3.16 degrees. Final 8192 x 4096 / 160-sample render; EXR SHA-256 `0e160e9d1bd09e71e698162cbb7f670f843d26cd4f03099254b49d64033782a8`; city score 0.64, whole sky 0.6336461901664734. Guarded FULL build and fresh sky/probe bake verified: all 209 runtime inputs and 77 authoring artifacts match, all 11 required assets packed, current source parity true. [Local visual review](../art/sky3d/simplify_review/review.html) and [build receipt](../art/sky3d/simplify_review/build.json). Section 11 supersedes v8's exact title/composition assumptions. Native appearance remains UNPLAYED; the user tests.**

> **STATUS 2026-09-29 19:45 Eastern - v8 COSMIC CYBERCITY (§10): the shipping sky now uses the authored cyber monument, 363 reworked lower-city blocks and a clearer elevated celestial composition. This supersedes v7's exact painted gate and gate-linked moon assumptions. Final render: 8192 x 4096 at 160 samples, EXR SHA-256 `7e4f8e519e33a2290dbdcc02c09755defa1e4c9dbe3c04130f5bdee52fba7c70`, city score 0.64, whole sky 0.6456634402275085. FULL BUILD OK 19:45:13; fresh LED and new sky image proven in [the build receipt](../art/sky3d/cohesion_review/build.json). All linked inputs match the snapshot; one copied but unlinked peer Lucky script is recorded separately, so whole-snapshot parity is not claimed. Native presentation remains UNPLAYED; the user tests.**
>

> **STATUS 2026-09-29 17:23 Eastern - THE TURN BUILT: `"skyRotation" "40"` (61) is deployed in e7's FULL BUILD OK 17:23:27 (tmp/typeface/full2.log, .ff 17:21:57, FF 222,833,728 B); the sky image is unchanged (the same HCVKQ32N... .iwi, EXR fb178d52...), the sky is in the ledger, test_jumppad OK. By the engine rule the sign now sits due WEST (yaw 180), where the jump reveal looks. UNPLAYED - the user's next jump confirms it.**
>
> **STATUS 2026-09-29 16:23 Eastern - v7c NO ASTEROIDS (§9.8): the belt, the drifting rocks and both black holes' debris retired (601 rocks; real asteroid models are coming). BUILT by session 22: FULL BUILD OK 16:23 (tmp/sky_asteroids/full1.log; the log is UTF-16), FF 222,709,376 B written 16:18:40, fresh bake (geom_key saw the sky), the NEW sky .iwi `HCVKQ32NX5A7IIAGB7VB4AS4WU` (31.2 MB, 16:16:28), `image,i_skybox_tod_cybercity` in the 16:18:40 ledger, deployed EXR sha = repo (fb178d52...), scripts / ui / zone_source diffs clean, nothing synced after. It also carried fd's companion freeze and d2's card UI. UNPLAYED.**
>
> **STATUS 2026-09-29 13:36 Eastern - v7b THE HERO SIGN + NO SHIPS + THE TURN (§9.7): the sign 25 % bigger and authored in W with
> its neon x3 over its own knee (peak 2.88 W vs the city's 1 W cap), the static ships retired (the sky fleet flies real models),
> finished `--roll 0`; the in-game bearing = -(SSI sun azimuth + skyRotation) (§2, corrected twice; 61 sets skyRotation 40).
> EXR sha256 c312071e... (94,805,738 B, 13:36:08). BUILT in session fd's FULL BUILD OK 14:25:54 (tmp/spire_removal/full1.log; the spire removal): FF 216,215,232 B written 14:23:04, fresh bake (LED 14:18), the NEW sky .iwi `SPX6GZXGJB7OFJUXXLTMIIIF45` (31.2 MB, 14:20:18) converted, `image,i_skybox_tod_cybercity` + its material + the skybox xmodel in the 14:23:04 ledger, deployed EXR sha = repo (c312071e...), deployed tod_skybox.gdt skyRotation 180 / skyStops 4.35, nothing synced after. UNPLAYED.**
>
> **STATUS 2026-09-29 11:32 Eastern - v7 THE TITLE GATE (§9): the sign is the user's reference painting on one card; the moon disc moved behind its crest in lavender; finished with --roll -90 (session 61). Ship render 8192 @ 160 = 539 s; finish score 0.640, gain 1.2279e-02, rgb 42/23/35, seam 0.69x; EXR sha256 609d0a89... (94,514,518 B, 11:31:51). BUILT in session 61's combined FULL BUILD OK (tmp/transit_bay/full1.log): FF 221,747,008 B written 11:49:36, the NEW sky .iwi `K4ZX4GKG44RFVEE3EERNSZ424Y` (31.3 MB, 11:47:29) converted + packed, deployed EXR sha = repo (609d0a89...), fresh bake (geom_key saw the sky change). UNPLAYED.**
>
> (v6 status follows)

> **STATUS 2026-09-25 11:43:06 Eastern — v6 THE COLOUR PASS + THE SPIRE CLUSTER (§8) IS BUILT: FULL BUILD OK 2026-09-25 11:43:06 Eastern (log tmp/sky3d_build/full_build_v6_113517.log; the fourth launch — the first was blocked by a delete-safety hook, the second refused because BlackOps3 was running (the user's 11:25 test), the third stopped by hand at the Radiant bake to fold in the Retriever fix): FF 206,925,056 B (the sky is STREAMED, so the .ff size is the peer's 11:20:25 figure — the proof is the NEW content-hash sky .iwi `5ZL5ANMTL255TXVGOC4VBTCJKJ`, 29,355,495 B, at 11:42:17; v5's was `NRQSHJDV6LO3ZFEGG3DB5R5L5D`), LED fresh 100,170,906 B (11:41:42), BSP 19.2 MB, navmesh 3 components (tower / spire / crown island, both towers connected), bank 199.6 MiB, 8 known-waived warnings, deployed EXR sha = repo (06cf89a3…), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, the deployed tod_skybox.gdt skyStops 1.0 + the dark SSI stops −7.2 (the peers' darkening), the deployed _tod_fall.gsc TOD_FALL_GATE_OPEN 0, and the deployed tod_archer_weapons.gdt lines 340-341 carry the Retriever's ammoCounterIcon / ammoCounterClip. ONE build carries the v6 sky, the Retriever crash fix and the peers' blackout darkening; tod_dev / tod_god are ARMED (the user's 09-24 test state, unchanged by this pass); UNPLAYED — the user tests.** The 8192 @ 160 spp ship render took 551 s; the finish ran
> `--white 1.0 --knee-w 0.70 --knee-max-w 1.0 --sat 1.10 --display-mult 6.5` (the previews at the game's factor; W → display white would be 5.78). Previews
> `docs/sky_preview/sky3d_*.png` (19 views incl. `ruby`), `sky3d_contact.png`, `sky3d_ref_vs_render.png` (the reference beside ours); the v6a..v6h rounds beside them.
>
> (v5 status, superseded) STATUS 2026-09-25 04:38:45 Eastern — v5 THE BIG CITY (§7) IS BUILT: FULL BUILD OK 04:38:45 Eastern: FF 206,962,048 B (the sky is a STREAMED image, so the .ff size does not move: the proof is the NEW sky .iwi `NRQSHJDV6LO3ZFEGG3DB5R5L5D`, 29.1 MB, at 04:38:02 — v4's was `EHDAWQ6EGNRBHBMDYRWRZYSP23`), LED bake fresh (100.2 MB), navmesh 3 components, banks 109.4 / 209.3 MB, 8 known-waived warnings, deployed EXR sha = repo (81791e06…, 81,996,466 B), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, skyStops 6.0 unchanged; the build carries the peer's 03:26 script fixes (startup failures, docs/170). Log: tmp/sky3d_build/full_build_v5.log. UNPLAYED — the user tests.**** The 8192 @ 160 spp ship render took 475 s; the finish ran `--white 1.0 --knee-w 0.70
> --knee-max-w 1.0 --display-mult auto` (6.30 → the worldspawn key keeps 6.5, 3 % brighter than W = white). Previews
> `docs/sky_preview/sky3d_*.png` (18 views), `sky3d_contact.png`, `sky3d_before_after.png`; the v5a..v5h rounds beside them.
>
> (v4 status, superseded) STATUS 2026-09-25 02:57:04 Eastern — v4 THE REFERENCE COPY (§6) FULL BUILD OK: FF 206,962,432 B, sky .iwi
> `EHDAWQ6EGNRBHBMDYRWRZYSP23` 28.5 MB, deployed EXR sha d6453532…, factor 6.5, skyStops 6.0. Log: tmp/sky3d_build/full_build_v4.log.
>
> (v1 status, superseded) STATUS 2026-09-25 00:02:31 Eastern: FULL BUILD OK with the first 8192 ship render (FF
> 198,784,448 B; the sky is a streamed image, so the .ff size does not move — the proof is the NEW
> sky `.iwi` `CFE55UDPLPVBWJ3P5KDZGV6U6K`, 31.96 MB, in the pack; banks 108.1 / 209.3 MB; 8 known-waived
> warnings; deployed EXR = repo). A second render with the sign fix (§6) follows with its own build.
> UNPLAYED. Pipeline: `tools/sky3d/`. The drawn generator (`tools/gen_tod_sky.js`) is kept as the A/B
> and the fallback.

## 1. The user's ask, and the honest diagnosis

User, 2026-09-24, on the comparison shot of Cybercity I's sky against the current TOD II sky:
*"what we have is just a colour change with the new sign … nowhere near where we should be … these
buildings don't look as realistic as they should … closer to the tower there's no buildings at all …
there shouldn't just be square boxes with square windows … maybe the way we built the skybox is
limiting … is there a better process?"*

Yes. The process was the limit, in four specific ways:

| what the picture needed | why `gen_tod_sky.js` could not give it |
|---|---|
| **depth** — occlusion, shadow, haze that thickens with distance, glass that reflects the sky | it is a 2-D painter: boxes drawn back-to-front with a hand-written fog rule; no light transport at all |
| **the lower hemisphere** — the player spawns at the crown and looks DOWN | the painter's eye sat at street level, so below the horizon there was only a floor grid; the whole nadir was empty |
| **buildings that are not boxes** | every solid was a box/taper with a line grid; adding profiles (v19.19) made cleaner boxes, not architecture |
| **material** — lit glass, wet asphalt, light pollution glowing in fog | a rasteriser cannot invent lighting by sharpening (docs/150 §1 already said so) |

The two routes that were on the table before today (docs/150): keep drawing, or commission an
image-model panorama (docs/151 — never sent). The image-model route has the quality but none of
the control: no seamless sphere, no exact text, a different exposure every roll, no editability.

**The new route: build the city as real 3-D geometry and render it.** Blender 4.2 is already the
repo's art tool (teleporter, altars, zombies, shop) and Cycles has an equirectangular panoramic
camera, so the ENTIRE picture — 10,000 buildings, streets, highways, harbour, fog, moon, the sign —
is a scene, and the physics does the depth: real perspective from a camera 220 m up (the city
continues below the horizon to the nadir), occlusion, moonlight and shadow, glossy glass, a
scattering fog volume that turns every window into light pollution and fades the far city. The
output is a linear equirect EXR that drops into the SAME asset name, GDT, zone line and exposure
contract as before. Nothing else in the map changes.

## 2. The pipeline

```
tools/sky3d/build_city.py    Blender -b: builds the procedural megacity (seeded), renders Cycles/OptiX -> raw linear EXR
tools/sky3d/finish_sky.py    Blender -b: exposure solve, peak knee, half-float ZIP16 asset, previews, seam check
tools/sky3d/render_sky3d.ps1 one command for both; -Ship = 8192x4096 -> the asset
art/sky3d/tod2_sky.blend     the saved scene (open it in Blender to look around / steer)
docs/sky_preview/sky3d_*.png the previews: the sphere + nine in-game views at 1080p, cg_fov 65
```

```
.\tools\sky3d\render_sky3d.ps1                 # 2048 preview in ~1 min, previews only
.\tools\sky3d\render_sky3d.ps1 -Ship           # 8192x4096 @ 256 spp -> source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr
.\tools\sky3d\render_sky3d.ps1 -FinishOnly -Raw $env:TEMP\tod_sky3d\raw_8192.exr -Mirror   # re-finish, no re-render
.\tools\build_map.ps1                          # a sky change is a FULL build (fresh content-hash sky .iwi = proof)
```

### What is in the scene (build_city.py, all seeded, every count/size a constant at the top)
- **Districts:** 12 Voronoi districts, each a street grid at its own rotation (no city-wide alignment).
  Three LOD bands by distance: 140 m blocks to 7 km, 280 m to 14 km, 560 m to 26 km; density thins
  outward and clumps around three downtowns (`DOWNTOWN`: radius + a height boost).
- **Buildings:** rect / chamfered / L / elliptical footprints, 1–4 setback tiers, log-normal heights
  per band, 8 % supertalls, 12 % dead towers (silhouettes). Details inside 11 km: antenna masts with
  red beacons, rooftop plant, sparse neon roof outlines and corner tubes (accents, ~7 %), giant ad
  screens on the façade that faces the tower (~16 % of mid-band towers).
- **The façade shader** is one material for every building: Brick-texture window grids in metres
  (per-window random lit/unlit and colour temperature, per-floor dark bands, tenant clusters),
  three styles by seed (curtain wall → punched windows), a per-building tint palette (warm white 60 %,
  then amber / ember / red / magenta / cyan), glass roughness 0.07 vs spandrel 0.62, grime noise.
- **Streets:** traffic trails (red one way, warm white the other), sodium curb lights, and a lit road
  surface under every street inside 8 km. Widths scale with distance (`amin`: at least ~1.2 texels of
  the 8192 ship) so thin emitters never sparkle.
- **The podium:** the tower's own plaza (nothing stands inside `R_INNER` 380 m): three ring roads,
  eight radial boulevards, pavilions, a canal ring — so a player looking down past the arena sees a
  city, not a void.
- **Two elevated ring highways** on pylons (2.3 km and 5.2 km), four trails each, bridging the harbour.
- **The harbour:** a 54° wedge of water from 1.3 km to 9 km (rough 0.11, bump), the far-shore city beyond.
- **Landmarks:** THE NEEDLE (900 m, lit spines), THE ARCOLOGY (a stepped pyramid on the shore, ember
  terraces), THE TWIN GATES (two 700 m towers, three skybridges).
- **The sign:** two masts, trusses with X-braces, a chamfered plate with a neon border, "TOWER OF
  DOOM" (Impact, red) "II" (ember) "CYBERCITY" (Bahnschrift, cyan) as extruded emissive letters,
  1 km ahead, centre 11° up; the moon (16° up, 11° across) rises behind it — docs/150's composition.
- **Atmosphere:** a fog box (42 km, density 4.5e-4/m at street level falling off over 300 m, patchy,
  red-tinted scatter, anisotropy 0.38) — this is the light pollution and the depth; two cloud sheets
  (1.5 km and 2.9 km, noise coverage, lit ember from below, a hole around the moon); a world sky
  gradient with nebula wisps and stars; a red sun lamp for moonlight; four searchlight spots.
- **Camera:** equirectangular, at (0,0,220 m), forward +Y. Measured 2026-09-24: centre column = +Y,
  +X = image right, zenith = row 0 — that is the BLENDER frame only. ⚠️ **CORRECTED 2026-09-29 (session 61, from the engine's
  own sky shader + the user's 15:33 screenshot rebuilt from the .map, docs/196 §3): in game the image's CENTRE column faces world yaw -(SSI sun azimuth + skyRotation), image right = the viewer's right (NOT mirrored); the SSI sun azimuth = the SSI yaw if its pitch > 90, else yaw + 180 (ours: 140).** The first reading
  ("the centre column faces world +X at skyRotation 0") left the SSI sun out of the sum: with `--roll 0` and skyRotation 180 the
  sign sat at yaw ~40 (measured 41.4), not 180. The old line ("so the moon/sign land where the drawn sky put them") was never
  measured in the engine either. The finish stays `--roll 0`; session 61 sets `"skyRotation"` to 40 in `mtl_skybox_tod_cybercity`
  (tod_skybox.gdt): -(140 + 40) = -180 = the gate due WEST, where the jump reveal looks. A change to either SSI's yaw now also
  turns the visible sky; test_jumppad checks the whole sum.

### The exposure contract (finish_sky.py)
Unchanged from docs/104 §4: `score = mean(linear) × 1024` is solved to `--target-score` (0.16, the
dark pass) by scaling the whole picture, so the bake's sky light cannot move with the picture.
Peaks are soft-clipped relative to the mean (`--knee 10 --knee-max 32`: the clip starts at 10× the
mean and asymptotes at 32×), the analogue of the drawn sky's display knee. The EXR is written by our
own half/ZIP16 writer (channels A,B,G,R — the layout the converter has always accepted).

### Render cost (RTX 5060 Laptop, OptiX; measured 2026-09-24)
| size | spp | wall time |
|---|---|---|
| 1024×512 | 24 | 11 s |
| 2048×1024 | 48 | 70 s |
| 8192×4096 (the ship) | 160, adaptive 0.025 | 3108 s = 52 min |
The finish at 8192 takes ~19 s (8 s of it the EXR write); the raw render stays under `%TEMP%\tod_sky3d\raw_8192.exr` (361 MB), so `-FinishOnly` retunes exposure/knee/mirror/roll/tint with no re-render.
⚠️ **A WORLD volume marched every sky ray to `volume_max_steps`** and made the first test 6× slower
than the same scene with the fog as a bounded MESH box (rays leave it). Keep the fog a mesh; its step is
`0.1 × mean(bbox) × material.volume_step_rate` (`FOG_RATE`).

## 3. Knobs (build_city.py, top of file) — the ones the first playtest is likely to ask for
| symptom | knob |
|---|---|
| too dark / too bright overall | `finish_sky.py --target-score` (the WORLD's light moves with it — read docs/104 §4 first) |
| neon / windows halo white in game | `--knee 8 --knee-max 24` (re-finish only, no re-render) |
| the sign reads backwards | `--mirror` (re-finish only) — the engine does NOT mirror (docs/196 §3), so this should never be needed |
| the sign / moon at the wrong bearing | `"skyRotation"` in `mtl_skybox_tod_cybercity` (tod_skybox.gdt): the centre column faces yaw -(SSI sun azimuth 140 + skyRotation); 40 = the gate due west. Keep `--roll` 0. Tell session 61 (test_jumppad checks the sum) |
| the city below the horizon reads too high/low | `CAM_H` (220 m); re-render |
| too hazy / too clear | `FOG_D0`, `FOG_H0` |
| too much / too little neon | the two probabilities in `City.building` under `if on('neon')` |
| windows too white | the `tint` ramp in `mat_facade`, `pal` split in `City.building` |
| the plaza below the tower | `City.podium` |
| a different city | `--seed` |

## 4. In-game checklist (the user tests)
1. From the crown hall, look DOWN over the parapet: the plaza rings, streets and rooftops should be
   there — that is the whole point of the camera height.
2. The sign: the right way round (`--mirror` if not), under the moon, readable at 1080p.
3. Spin on the spiral: no vertical seam (the finish prints the wrap delta; a rendered sphere is
   periodic by construction).
4. Glare: if windows or the sign bloom white, lower the knee (re-finish). If the whole world is
   red-lit rather than red-skied, `--tint 1,1.1,1.1` (docs/104 §4b, re-finish only) pulls the
   light back without touching the picture's exposure.
5. Sharpness: judge only against `docs/sky_preview/sky3d_ingame_*.png` at 1:1.

## 5. What would make it better still (partner asks)
- **Ad-screen textures:** twelve image-model billboards — the one thing an image model does better
  than a procedural shader. The brief and pack are docs/167; the drop goes in `art/sky3d/billboards/`
  and `--screens-dir` puts them on 75 % of the ~600 screens (the material normalises each screen's
  metre UVs by its own size, so any aspect works).
- **Mood references:** two or three paintings/stills the user loves, to calibrate haze, colour and
  how much neon "realistic" means to them.
- **GPU time:** the two Blender studios that stay open for the user share the GPU; pausing their
  previews during a ship render roughly doubles its speed.

## 6. v4 — THE REFERENCE COPY (2026-09-25)

### 6.1 What happened between v1 and v4
The user judged the v1 render (§1–5) "a lot cleaner, the depth is really nice" but wrong in kind:
*"we lost the cyber feeling … no extremely high skyscrapers … the sky is dull, the upper half is empty
… planets, stars, black holes … the train, I don't see the train … the red is orange … too much black
and gray … can the sky be dark while still being colorful?"* Two iterations (v2 THE CYBER PASS: supertalls,
THE ORIGIN + storm, rails + trains, ships, bodies; v3: Cybercity I's grid language) read as purple-grey
mush, and the user stopped the cycle: *"I'll come with a great reference we can copy from."* They brought
three ChatGPT images (`C:\Users\jorda\Downloads\sky_refs\ref1..3.png`, 1774×887): *"these are what we will
use as a reference. If we can build something to this level that would be wild."* v4 copies them.

### 6.2 The references, measured (true display values)
⚠️ **`bpy.data.images.load(png).pixels` returns the DISPLAY bytes / 255 — it does not linearise.** The
first measurement re-encoded them and read the references as bright and grey (mean 0.42, 3 % black); every
number below is from the corrected tools (scratchpad `ref_stats.py`, `ref_colors.py`, `mush_mask.py`).

| measure (display) | ref1 / ref2 / ref3 | v3 city view | v4 (final, 2048 check) |
|---|---|---|---|
| near-black (v < 0.12) | 22 / 18 / 21 % | 36 % (but grey-mauve elsewhere) | 6–16 % |
| "mush" (v 0.12–0.6, s < 0.35) | 4 / 5 / 4 % | 28 % | 5–29 % (the preview blur averages windows to grey) |
| saturated (s > 0.55, v > 0.25) | 36 / 33 / 33 % | 4 % | 11–30 % |
| bright (v > 0.85) | 10 / 9 / 9 % | 0 % | 1–6 % |
| mean saturation (v > 0.12) | 0.66 / 0.65 / 0.63 | 0.38 | 0.43–0.49 |
| mean luminance | 0.21 / 0.21 / 0.21 | 0.14 | 0.15–0.23 |

Key colours (sRGB): space voids (3,2,6), indigo space (17,23,54), blue-violet distance (28,34,75), magenta
nebula (162,53,88), orange nebula (210,120,61), warm city glow (221,140,59), cyan neon (39,197,228),
magenta neon (214,56,175), violet (111,59,180), green (24,215,137), dark tower bodies (22,18,26). Hue share
of the saturated pixels: blue 36–56 %, magenta 9–17 %, violet 9–18 %, red 8–16 %, orange 8–10 %, cyan 3–4 %.

### 6.3 Units: W = display white
Every emitter in `build_city.py` is now authored in **W = display white** (a neon tube 0.9, a lit window
0.95 × amber (0.76,0.30,0.07), a panel field 0.6 × its hue, the space voids 0.001, indigo patches to 0.06,
nebula to ~0.8). A saturated display colour needs its minor channels **under ~0.05 W** — the blood moon
read ORANGE with green at 0.20 and is (1.0,0.06,0.03) now; pink and gold were pastel until their minor
channels dropped. `finish_sky.py --white 1.0 --knee-w 0.70 --knee-max-w 1.0` puts the soft knee in W.

### 6.4 The picture vs the light: `sky_intensity_factor`
The docs/104 contract (`score = mean × 1024 → 0.16`) is kept, so the bake's sky light, `skyStops 6.0` and
the reflection probes do not move at all. The references' brightness is reached IN GAME by the worldspawn
key `sky_intensity_factor0/1` (docs/162 05 §4.4 — "the sky box's color will be multiplied by this
interpolated intensity factor", range 0..10, verified in t7.def.json; it does not light the bake). The
finish's `--display-mult auto` prints the value that puts W at display white under the contract
(**≈7 for v4**); `gen_tower_map.js` carries it (a full build), and the previews are rendered through the
same factor with the one calibrated absolute mapping we have (Cybercity I's approved canvas gain
0.0176 = display white). If the sky reads too bright/dark in game, that key is the knob, not the EXR.

### 6.5 What is in the scene now (deltas to §2)
- **Towers:** matte near-black bodies with a painted ambient floor `BODY_FLOOR` (never black), dense warm
  windows (amber / gold / a few cool; lit fraction ~0.46), and on 65 % of them (`PANEL_FRAC`) full-height
  translucent NEON PANELS in one hue on 30–52 % of the columns with a lit circuit grid (`E_PANEL`, `E_PLINE`);
  lit edges and collars on every tier; neon RINGS round the crowns (14 % of tall towers, 1–3 on every
  megatower), SIGILS (circle-and-spokes / hexagon / diamond emblems, `mat_sigil`) on faces and floating,
  spiked crowns on ~30 % of tall towers. Palette (`PAL_TABLE`): cyan, magenta, violet, green, orange, blue,
  pink, gold — red stays reserved for the moon, the sign and THE ORIGIN.
- **Floating platforms** (reference 2): 9 saucers over the mid city, dark undersides, two neon rims, small
  towers on top, LIGHT-FALLS pouring from below (`mat_lightfall`).
- **Glowing ribbons:** the two ring highways (orange / magenta) and the four rail decks glow (`mat_ribbon`).
  Streets are a WARM sodium carpet with neon accents (the references' orange horizon).
- **THE SKY is space:** black voids, patchy indigo glow (`SKY_GLOW`), domain-warped nebula in magenta /
  pink / orange / violet / teal with dust lanes, brighter round the black hole (`NEB_CORES`), three star
  layers (~50k faint, ~10k medium, ~70 big stars with four-point flares). No cloud sheets (`--clouds` brings
  them back), no fog veil (`FOG_D0` 1e-5 — a warm band only where 20 km of it stack at the horizon), a
  whisper of sky-blue haze.
- **Bodies:** ONE oblique black hole (`gargantua`: shadow r 3.6°, a two-arm spiral disc to 5 R in
  orange → magenta → violet with dust lanes, a thin photon ring, a lensed glow ring, 90 rocks), two banded
  ringed gas giants with moons, three CRACKED planets with glowing fissures (orange lava, cyan energy, green
  energy — `mat_cracked`), a ringed moonlet, two spiral galaxies (`mat_galaxy`), 60 drifting asteroids.
- **THE ORIGIN:** crimson panels and thick veins, three giant neon rings, a crimson beam into the sky, a
  violet SELF-LIT storm (density 0.012, six lights, six bolts) — thunderclouds, not black blobs.
- **Ships:** four capital ships (two high against the nebula) with long orange / cyan plumes, fighters with
  longer trails, the three airships; near-vertical pillars of light from the megatowers.
- **The sign:** "TOWER OF DOOM II / FALLEN CYBERCITY"; the flicker on FALLEN's A and E is subtle now
  (0.28 read as a missing letter).

### 6.6 Cost (RTX 5060 Laptop, OptiX)
| size | spp | wall time |
|---|---|---|
| 1024×512 | 24 | 11 s |
| 2048×1024 | 48 | 30 s |
| 4096×2048 | 64 | 105 s |
| 8192×4096 (the ship) | 160 | 500 s (8.3 min) |
Three times faster than v1 at every size: the 1100 m fog box at 4.5e-4/m was most of v1's 52 minutes.

### 6.7 Knobs that changed
| symptom | knob |
|---|---|
| the sky too bright / dark in game | worldspawn `sky_intensity_factor0/1` in gen_tower_map.js (the finish prints the value that makes W white) |
| neon halos white in game | `--knee-w 0.6 --knee-max-w 0.9` (re-finish only) |
| towers read as coloured boxes | `PANEL_FRAC`, the `pfrac` range in `mat_facade` (0.30–0.52) |
| too much / too little nebula | `NEB_GAIN` (1.3), the two thresholds in `world_sky` (0.49 / 0.51) |
| the sky not black enough between the nebulae | the `glowf` threshold (0.47) and `SKY_GLOW` |
| the storm too dark / too thin | `ORIGIN['storm_d']` (0.012), the emission strength in `mat_storm` (8e-4/m), the six lights in `make_storm` |
| a colour reads pastel | its minor channels in `PAL` / `PAL_TABLE` (keep them ≤ 0.05) |
| windows too dense / sparse | `litfrac` gauss in `City.building` (0.46 ± 0.13), `frame` in `mat_facade` |

## 7. v5 — THE BIG CITY (2026-09-25, the user's feedback on the v4 contact sheet)

### 7.1 The feedback, item by item
The user read the v4 contact sheet (§6) and gave eight notes. Each maps to one change; the check after every change was
a 1024 or 2048 preview through the same finish, then the contact sheet.

| the note | what changed |
|---|---|
| "the spaceships need way more detail … I can barely tell it's a spaceship … a little bit bigger" | `make_starships` rebuilt: BATTLECRUISERS 1.0–1.4 km long (was 0.5–0.9), five of them, with a real silhouette read from below — keel, main hull, dorsal deck, spine, a bridge tower with a lit command deck and two sensor masts, two engine nacelles, a stern wall with seven hot nozzles and long plumes, swept wings and a dorsal fin with neon leading edges, three decks of lit windows a side and two along the belly, a small cool hangar slot, running lights; twelve fighters, two escort V-formations. The hull is DIFFUSE near-black (`mat_shiphull`) — a glossy hull mirrored the city's neon into beige plates. `ship_cap()` keeps every building and supertall out of a cruiser's lane (the first cruiser had rolled in behind the green cake megatower). |
| "too many buildings … by making so many they have to be so small … three times as big" / "half what we have on the ground" | `LOT_P` 320 / 640 / 1280 m (was 140 / 280 / 560); heights ×2–2.5 (band-0 median 200–230 m, cap 2100); **1,840 buildings instead of 9,749**, ~a fifth. Each carries three times the detail: 1–6 setback tiers by height, lit BELTS on panel towers, buttress FINS with lit edges, an emblem on the face, ANTENNA arrays, a lit PLINTH (the lobby steps out), a second screen on the tall ones. |
| "a colour that's so dominant … the windows" | the window tint follows the tower's hue row (`PAL_TABLE`: cool white, cyan, violet, pink, green, gold; amber is one row of ten plus a 10 % sprinkle), lit fraction 0.46 → 0.26, `E_WIN` 0.95 → 0.70. The city's colour is its NEON; the windows are its texture. Panel columns are 18–48 m wide (was 9–22: the bigger towers read as barcodes) with the circuit grid scaled to a third of the panel; `PANEL_FRAC` 0.60 so four towers in ten are dark window towers (the references' dark mass); the hue weights lean blue / cyan (their saturated pixels are 36–56 % blue). |
| "the sky is a bit empty … more planets in the distance to show off the depth … double what we have" | `BODIES` doubled: five gas giants (three ringed), five cracked planets, seven moons and moonlets, TWO black holes, four galaxies (one edge-on), a COMET with an ion and a dust tail, an asteroid BELT of ~220 rocks arcing over the right sky, 90 drifting rocks. Distant small worlds carry `dim` (0.5–0.6): dimmer and hazed toward indigo, so the sky reads deep. |
| "the black holes need a little bit more detail" | the LENSED FAR SIDE bent over and under the shadow (`mat_lensarc`: an annulus in the view plane, bright on the axis perpendicular to the disc, gone along the disc), polar JETS (nested soft fans), eight tidal STREAMS spiralling in, a finer orbital-turbulence octave, a hotter and brighter Doppler side, 150 debris rocks with clumps, tilt 0.95 → 1.05 rad. The second hole (`maelstrom`, az −12 el 70, cool blue) is small and near edge-on. |
| "our major buildings need a lot more detail … the tall buildings with the rings around them" | `mega_detail` on every supertall inside 12 km: 2–4 neon BELTS hugging the shaft, one or two RING PLATFORMS (a dark annular deck with lit rims, 6–14 pods and window blocks on top, 2–4 light-falls under it), 4–8 buttress fins with lit edges, an antenna array; heroes ×1.3 taller. |
| "the ground floor looks circular but then leads into the background … not an even bleed … looks odd" (contact tile 7) | THE CORE: the podium's ring roads continue outward to 1.42 km (`CORE_ROADS`, eight rings) with twelve radial boulevards on the lots' sector boundaries (`core_radials`); the lots between the rings are POLAR (`CORE_BANDS`: six rings, median height 26 m at the foot rising to 300 m at the edge, 153 lots) and the square districts start beyond `R_CORE` — the circle BECOMES the city instead of ending at a wall. THE LOOP monorail rides over the last ring road. The ring roads are at the streets' own brightness (they were the picture). |
| "I do like the streets" | unchanged in kind; the road quad is 30 m on the 51 m streets between the bigger lots. |

### 7.2 Two things a preview taught
- **A rolled ZIGGURAT (base 0.9–1.2 × h) at 2.7 km with h 2978 was a 3 km wide pyramid, and `mega_detail` scaled its ring
  platform to a 3.6 km radius with 1.9 km pods — the deck passed OVER the camera and a pod stood 1.2 km from it; half the
  sky of the first 2048 check was a dark speckled slab with magenta edges.** Ziggurat bases cap at 1200 m and roll only
  beyond 4.5 km; a platform's outer radius caps at `Ri + 300 + 0.06 h` and never comes within 900 m of the camera; pods cap
  at `40 + 0.07 h`; fins at 320 m. Anything scaled from a supertall's radius needs a ceiling.
- **A tube CONE reads as solid paper** — the comet's tails and the jets read as grey cones, and the cruisers' seven 1.4 km
  ENGINE PLUMES (orange at 0.67 W) were the "beige planks" that three rounds blamed on the wings, the hull and the hangar bay
  in turn (a bounding-box probe of the saved .blend named `ship_plume_2`). `soft_fan()` builds a strip of quads in the view
  plane with PER-CORNER alpha (`Acc.poly(..., cols=)`), nested three deep (a bright thin core in a soft sheath) — that reads
  as a comet, a jet, an exhaust. When a colour in the picture has no owner, probe the .blend by angle instead of guessing.

### 7.3 The numbers
| | v4 (§6) | v5 |
|---|---|---|
| lots / buildings | 10,194 / 9,749 | 1,847 / 1,840 (153 on the core rings) |
| lot pitch, inner band | 140 m | 320 m |
| band-0 median height | 48–100 m | 200–230 m |
| supertalls | 53 | 45 (+ `mega_detail` on each inside 12 km) |
| sky bodies | 9 + 60 rocks | 26 + 220 belt rocks + 90 drifting + 195 debris |
| capital ships / fighters | 4 / 5 | 5 / 12 |
| scene faces | 1.12 M | 0.69 M |
| 2048 @ 48 render | 24 s | 24 s |
| 8192 @ 160 render (the ship) | 500 s | 475 s |
| `display-mult auto` | 6.53 | 6.30 (gen_tower_map.js keeps 6.5) |

### 7.4 Knobs added
| symptom | knob |
|---|---|
| too many / too few buildings | `LOT_P` (320 / 640 / 1280), the built probabilities in `City.layout` (0.82 / 0.70 / 0.50 / 0.30) |
| the towers too tall / short | the `lognorm` medians in `City.building` (200 / 230 / 340 / 560), the cap 2100 |
| the windows too dense / too white / too amber | `litfrac` gauss (0.26 ± 0.10), the 55 / 35 / 10 mix in `mat_facade` (`wtint` / `WIN_ICE` / `WIN_AMBER`), `E_WIN` |
| a tower reads as a barcode / as a coloured crate | `colW` (18–48 m) and `pfrac` (0.28–0.50) in `mat_facade`; `PANEL_FRAC` |
| the core's seam into the grid | `CORE_BANDS` (the last ring's radius and height), `R_CORE`, `CORE_ROADS` brightness |
| a cruiser hidden / too small / too bright | `STARSHIPS` (az, d, z, L), `ship_cap` margin (4°), the window alpha 0.7, the bay alpha 0.6 |
| the sky too busy / too empty | `BODIES` (`dim` for distance), `ASTEROID_BELT['n']`, `ASTEROIDS_DRIFT` |
| the black hole's halo / jets / streams | `mat_lensarc` strength (E_HOLE × 1.05), the jets' three alphas (0.045 / 0.07 / 0.13), `streams` per hole |
| a supertall's rings and decks | `mega_detail` (belt count 2–4, deck radius cap, pods 6–14) |

## 8. v6 — THE COLOUR PASS and THE SPIRE CLUSTER (2026-09-25, the user's notes on the v5 build)

### 8.1 The asks
| the note | what changed |
|---|---|
| "I downloaded all those assets you requested" | the docs/167 drop (`Downloads/files - 2026-09-25T101516.779.zip`, twelve RGB PNGs at the brief's exact sizes, every one at least 40 % near-black, no red, the six neon hues covered) is installed as `art/sky3d/billboards/ad_01..12.png` at 512 px on the long side (a screen is 2–9 texels tall in the 8192 ship; the originals were 28 MB of repo for nothing). 75 % of the ad screens wear one, and each screen gets an image of its OWN orientation (`screen_mi`: wide / tall / square) instead of a stretched random one. `render_sky3d.ps1` uses the folder by default (`-ScreensDir none` for the procedural mosaic only). |
| "the building may have too many windows … cut the windows by 35 % but keep the consistency and detail" | the lit fraction 0.26 → 0.169 (`litfrac` gauss, clamp 0.05–0.36) and the platform pods 0.35–0.6 → 0.23–0.39; the grid, frames, lobby rows and tint rules are unchanged. On the spires (below) the windows are dimmer again (E_WIN × 0.5) and the lowest six floors are dense and AMBER, the references' warm bases. |
| "the red giant planet should be about 4x bigger" | `ruby` r 2.4 → 9.6° (19° across, the biggest body in the sky, high over the moon lane at az −20 el 47); crimson bands (v6b's first pass read ORANGE — recoloured to deep reds with one dull-gold band, 9 broad bands instead of 15), a thin dark-red ring, two moons, ×1.25 brighter through a new per-body `gain`. Red is otherwise still the moon's, the sign's and THE ORIGIN's. |
| "the entire skybox … more colourful, more contrasting, more elegant … a little bland" | the nebula in jewel tones (`NEB_*`: v4i's pink and orange read dusty tan) with a deep blue band and `NEB_GAIN` 1.45, deeper voids (`SKY_GLOW` more violet, the cloud powers 1.9 / 1.8); the neon weights cover the whole range (magenta and violet up with the cyan; the window-tint rows the same); half the districts light their streets in neon and three of the core's ring roads glow magenta / cyan / violet between the amber ones (`CORE_ROAD_HUES`); `BODY_FLOOR` ×0.7 and bluer (deeper near-black bodies); the fog's scatter grades warm at the street to violet-magenta above `FOG_H0` (`FOG_SCATTER_HI`), the high haze is violet-blue; `finish_sky.py --sat 1.10` as the grade on top (the mean contract is re-held, so the world's light does not move). |
| "our buildings … look like New York buildings … they should really reference the ones I sent … one looks like a New York style one and then one looks like an actual cyber city tower … take a step back" | THE SPIRE CLUSTER, §8.2–8.3. |

### 8.2 The step back: what the references' towers are, and what v5 was
Read side by side (`docs/sky_preview/v6h_ref_vs_render.png`, left the reference, right ours), the gap was the building GRAMMAR, not the palette:

| the references | v5 (and every version before it) | v6 |
|---|---|---|
| a tower is a BUNDLE of tapering spires — a tall core and many thinner needles packed against it, aspect 1:10 and slimmer, every top a point | one extruded footprint with setback tiers and a flat roof — Manhattan in neon | a tapered core of 3–5 frustum segments ending in a needle, 4–8 satellite spires of 30–92 % of its height clustered against it |
| light is CONCENTRATED: a few giant saturated crystal slabs, lit collars, a handful of edge seams, warm window clusters at the base; the body is dark solid metal | light is SPREAD: a window grid over the whole face (the amber carpet) or a full-height panel field | 1–3 crystal slabs per tall spire (`mat_crystal`, wider and taller than the slim core, saturated with white-hot cracks), a collar at every break, seams on a few edges only, dense amber windows on the lowest floors, thin light rows every seven floors, faint vertical grooves; the rest of the face is the painted near-black |
| rings and halos round the spires; greebled lower bodies | rings on 22 % of the tall panel towers | a halo ring on a third of the spires over 300 m; 2–6 greebles with lit slots on the lower body |
| blocky greebled low structures in the foreground | the same box tiers everywhere | the box tiers kept for the low blocks (under 90 m) and 15 % of the mid-rise |

### 8.3 How a spire cluster is built (`City.building`, the `spire` branch)
Nearly every tower over 90 m (85 %; 40 % of 60–90 m). `Acc.loft(fp0, z0, fp1, z1)` is the new primitive: side quads between two footprints with the same vertex count — a frustum when the top is the bottom scaled. The core is a 6–16-gon of radius 0.28–0.45 × half the site (slim: v6b's first cut at 0.55–0.78 read as drums) lofted through 3–5 segments (scale 0.80–0.94 each) to the shoulder at 74–88 % of h, then a needle (`struct`) to h with its upper half lit and a beacon. Satellites: 4–8 (1–3 beyond 11 km), radius 0.35–0.8 × the core's, 1.0–2.3 core radii out, two lofted segments and a needle each. Crystal slabs: 1–3 on towers over 150 m, standing 0.8 m off a core face, 1–2 core radii wide, 35–70 % of h tall, lofted to 80–95 % at the top. Seams: `tube()` along every second or third core edge following the taper, alpha 0.50; a `neon.prism` collar (fp × 1.03) at every break, alpha 0.45; satellites two or three seams at 0.42. The facade encodes the spire as `style ≥ 2` in the 'bld' attribute (a FLOAT_COLOR, so 2.x survives) and `mat_facade`'s spire branch draws the rows / grooves / amber base instead of the grid; the panel branch is never reached (`style < PANEL_FRAC` is false). Downstream details a spire does not wear: parapet strips, corner tubes, collar strips, pyramid crowns, antenna arrays and masts, rooftop plant and lights (it has its collars and its needle); it keeps the plinth, the ad screens, the belts' sigil.

### 8.4 What the previews taught (five rounds, every one measured after the third)
- **The `v6a` sheet answered the first three notes but the towers were still boxes** — the user's side-by-side complaint came in while it rendered, and it was right: no palette change fixes a grammar problem.
- **`v6b` lit every edge and read as a NEON WIRE CAGE**; the references' bodies are dark mass with a few seams. Seams on every 2nd/3rd edge, softer collars, faint grooves (`v6c`); still fat drums → slim cores in dense bundles (`v6e`).
- **THE PALE-SLAB HUNT: judge a colour by MEASURING, never on a downscaled contact sheet.** Three rounds "fixed" slabs that looked pastel — lowering `E_CRYSTAL` 0.85 → 0.60, capping every line to a fraction of its cell (a texel-wide line at 3 km covers most of a 7 m cell: at the 8192 ship a "one-texel" line is 2.3 m wide there — that cap is right and stays) — while the measured box mean barely moved. A render with `--skip crystal` proved the slabs were where I thought; sampling the same pixel boxes across `v6e / v6g / v6h` proved the mean was diluted by dark grid pixels and that the slab CORES were at display 0.78 — DARKER than the references' (their slab cores sit at 0.9+ with white cracks), not paler. `E_CRYSTAL` went to 1.10 and the 97th percentile in the slab box went 0.78 → 0.95 (`v6h`). The 1:1 crop (`%TEMP%\tod_sky3d\crop_v6g_v6h.png`) also showed the "pale cyan slab" of the strip was a box tower's PANEL field, not a crystal at all.
- **A patch guard keyed on a version tag collided with a comment I had written a round earlier** (`'v6f' in src` was true because the E_PANEL line said "v6f") and the render "`v6f`" was a no-op — check what a guard string matches before trusting an "already applied".
- **The red giant at 4× read as an orange Jupiter**: the palette had a pale-gold band and orange-red hot bands; at 19° across the eye averages the bands. Crimson / blood-red bands with one dull gold, fewer and broader.

### 8.5 The numbers
| | v5 (§7) | v6 |
|---|---|---|
| lots / buildings | 1,847 / 1,840 | 1,847 / 1,838 (55 lots under the supertalls); spires ≈ 85 % of those over 90 m |
| scene faces | 0.69 M | 1.10 M (neon 0.48 M — the seams and collars; crystal 7.2 k) |
| ad screens | 314, procedural mosaic | 328; 75 % wear a docs/167 billboard of their own orientation |
| lit window fraction | 0.26 | 0.169 |
| 2048 @ 48 render | 24 s | 27–28 s |
| 8192 @ 160 render (the ship) | 475 s | 551 s |
| `display-mult auto` (W → display white) | 6.30 | 5.78 — the previews are rendered at the worldspawn 6.5, so they show the game's brightness (about 12 % over W = white); to sit exactly on W set `SKY_INTENSITY_FACTOR` in gen_tower_map.js to 5.78 (a regen + full build) |
| `--sat` | — | 1.10 |

### 8.6 Knobs added
| symptom | knob |
|---|---|
| the spires too thick / too thin, too few needles | `rc` (0.28–0.45 × half the site), `nsat` (4–8), the satellites' `rs` / `ds` / `hs` ranges in the `spire` branch |
| the towers read as wire cages again | the seam alphas (0.50 core / 0.42 satellite), `seam_step`, the collar alpha 0.45, the rows' gate 0.56 and weight 0.75, the grooves' gate 0.56 and weight 0.25 |
| the crystal slabs too bright / dull / too many | `E_CRYSTAL` (1.10), the slab count per tower (1–3 over 150 m), `cw` (1–2 core radii), the z-span (35–70 % of h) |
| the box towers' fields pastel again | `E_PANEL` (0.45), the hot-cell weight 0.22, the grid-line cap (16 % of the cell) |
| too many / too few windows | `litfrac` gauss (0.169 ± 0.065); the spire windows E_WIN × 0.5; the amber base `low` (v < 26 m) |
| the red giant | `ruby`: r 9.6, `cols`, `ring`, `gain` 1.25, `bands` 9 |
| the sky's colour | `NEB_*` + `NEB_BLUE`, `NEB_GAIN` 1.45, `SKY_GLOW`, the cloud powers 1.9 / 1.8; `--sat` |
| the city's colour | `NEON_W`, `PAL_TABLE` weights, `ROAD_HUES`, `CORE_ROAD_HUES`, `BODY_FLOOR`, `FOG_SCATTER_HI`, `HAZE_SCATTER` |
| the billboards | `art/sky3d/billboards/` (`-ScreensDir`), `screen_mi` (p = 0.75), the image screens' E_SCREEN × 1.6 |

## 9. v7 — THE TITLE GATE (2026-09-29, the user's reference image)

### 9.1 The ask
User, 2026-09-29, with one image (`art/sky3d/sign/tod2_title_gate_reference.png`, 1448 x 1086, a ChatGPT painting of a
theme-park gate): *"We really need to improve the cybercity 2 sign in the skybox. Looks so bland and plain. It should look
like a very bright neon sign with cyber designs all over it. It super plain right now. Please follow the reference exactly.
Dont stop until its indistinguishable."* The v2..v6 gantry was a flat plate with extruded letters; at the shipped display
level (display-mult 10, W ~6.8x over display white) "FALLEN CYBERCITY" clipped to a solid cyan bar and "TOWER OF DOOM" sat
red-on-red.

### 9.2 The route: the painting itself, on one card
A skybox is seen from ONE point, so a flat emissive card at the right place is indistinguishable from modelled geometry —
and it is the only way the skull, the lettering, the banners and the neon can be the reference's own, pixel for pixel. The
card stands in the city (`make_title_gate`, `GATE` in `build_city.py`): perpendicular to the view toward the text box
centre (az 0, el 11 — unchanged, so the jump-pad reveal camera still aims at it), 1 km out, the reference's width = 52 deg.
Buildings nearer than the card hide its feet; the ones behind it show through the arch. A building that straddles the
card's plane simply reads as standing in front of it (its front face is nearer), so the city is untouched.

COLOURS: the texture is display-referred (the painting's own pixels, loaded Non-Color), decoded with the previews' 2.2,
divided by the finish's `--sat` (1.2) about Rec.709 luminance, and emitted at `GATE['white']` = 0.1467 W per display 1.0
(= preview gain 0.0176 / (the ship's gain 0.0120 x display-mult 10)) — so the FINISHED sky shows the gate in the reference's
own colours. Measured in the reveal view mapped back onto the reference (the card faces that camera, so the map is a pure
scale, 0.761): letters (113,33,58) vs the reference's (110,29,55), FALLEN CYBERCITY (96,20,152) vs (94,16,151), the banner
(62,9,43) vs (59,9,42), the skull (70,35,51) vs (67,32,48) — the +3 is the scene's thin haze in front of the card.

### 9.3 The cut (`tools/sky3d/cut_title_gate.py`; the masks from `tools/sky3d/segment_title_gate.py`)
| step | what and why |
|---|---|
| masks | BiRefNet-**DIS5K** (dichotomous segmentation, trained on gates / fences / towers). The general BiRefNet found only the text panel (a logo); BiRefNet-COD only the skull. DIS5K at 1024 = the whole gate, soft edges, and it KEEPS the reference's moon; at 2048 = a crisp upper silhouette (orb rings with their see-through gaps, every crest spike, railing bars) that leaves the moon out but drops the pillar bodies. Both masks are committed; the model is never needed again unless the reference changes. |
| combine | alpha = the 2048 mask; inside the pillar zones below the banner tops the union with the 1024 mask; the pillars below y 700 solid (both masks lose them there — that band is at / below the horizon, behind the core's buildings). |
| removed | the roller-coaster loop behind the left railing (a polygon above the gate's top rail, left of its spike post, minus one railing post); the fence / gate leaves / lamps / city under the arch (below y 800); the base fades over y 900..960 (the reference's fog and floor). |
| snap | the masks top out at 254/255 and the neon city behind is ~100x the banners' own light: a 0.4 % leak drew a GREEN TOWER THROUGH BOTH BANNERS in the first render. Near-opaque is opaque now (`(a - 0.03) / 0.92`). |
| opaque neon | DIS gives the thinnest white-hot tubes partial alpha (the orb rings' tips 0.18..0.76, the spire's line 0.91): white-hot pixels within 3 px of the gate are opaque, never under the arch (the reference's ferris wheel glows through the lattice columns). |
| spire tip | the central spire runs off the reference's top edge: a painted taper to 104 px above it that carries the block's own panel detail (each tip pixel samples the block band y 22..64, its column stretched back to the block's width), the first 14 rows continuing the block's top rows (no seam), and the reference line's own 17-px cross-section laid up it, fading out at 78 px. |
| edges | pymatting's `estimate_foreground_ml`: a half-covered edge pixel keeps the gate's colour, not the reference's purple sky. |
| glow | the painted glow outside the silhouette goes with the sky, so it is REBUILT, measured: the reference's neon glows are TIGHT and in the tube's colour (the orb rings: +0.47 linear 4 px out, +0.02 at 16 px) — one blur (sigma 5 px) of the gate's coloured neon, its weight fitted to ten measured points (rms 0.024); a white-hot core's halo is its tube's colour, so white cores are not glow sources (the first cut made the rings and beacons read WHITE). THE SPIRE'S AURA, the one wide glow (a magenta-violet haze ~90 px across), is LIFTED from the reference's right side minus its sky and mirrored onto the left, where the reference's moon sits under it. The glow ships as `_glow.png`, added light on the same decode (it never occludes). |

A MOON COLOUR MODEL (remove whatever looks like the reference's moon) was tried first and REMOVED: it read the crest spikes'
grey-lavender lit faces as moon and half-erased three spikes — and the 2048 mask had never included the moon at all. Check
what each mask actually holds before adding a fix for it.

### 9.4 The moon
The reference's moon peeks out upper-left behind the crest; the v6 blood moon sat dead behind it and the new crest would
have hidden it entirely. `MOON_DISC` puts the visible disc + halo where the reference's moon is (its centre and radius
measured on the reference, carried through the card's frame: az -3.3, el 20.7, r 5.1), and `MOON_STYLE 'reference'` gives
it the reference's pale lavender with a faint violet halo (an A/B against the blood moon: red behind the red neon ring
merged into one blob; the lavender lets the ring pop, as in the reference). `--moon-style blood` restores the red. The
moonlight lamp and `moon_dir()` (every planet's terminator) keep MOON_EL at az 0: no body's shading moved.

### 9.5 The ship
(⚠️ v7b, §9.7: the roll below was WRONG in game — the gate landed due NORTH; the ship is now `--roll 0` + `skyRotation` 180.)
`render_sky3d.ps1`'s defaults ARE the shipped recipe now (score 0.64, sat 1.2, display-mult 10, knee 0.7..1.0 W) plus
`--roll -90`: the gate and moon face due WEST (session 61's crown->tower jump flies south with the sign on the player's
right; its reveal camera is yaw 180 / pitch -11, and its test_jumppad lockstep reads `roll` from `sky3d_stats.json`).
`finish_sky.py`'s preview views follow `--roll` (they are named after content) and gained `reveal` (az 0, pitch 11).
Iterate on the sign without a full render: `build_city.py --region "-45,45,-26,38"` renders just that window (a cropped
border render, ~30 s at 8192 scale) and writes its placement to `<out>.region.json`.

### 9.6 Knobs
| symptom | knob |
|---|---|
| the gate too big / small | `GATE['w_deg']` (52: the reference's width) |
| the gate too high / low (the reveal camera aims at `box_el`) | `GATE['box_el']` (11) — tell session 61's `_tod_jumppad.gsc` |
| the gate too bright / dark against the sky | `GATE['white']` (0.1467 = the ship's display white; x2 = one stop) |
| the glow too strong / weak / wide | `GLOW_SIG` + the fitted weights in `cut_title_gate.py` (they refit on every run), `AURA` |
| a leftover piece of the reference's background | a polygon in `cut_title_gate.py` (`COASTER`, `UNDER_ARCH`), reference pixels |
| the moon | `MOON_REF` (the moon in the texture's pixels; v7b: it follows the gate), `--moon-style reference` or `blood` |
| a new reference image | `segment_title_gate.py --ref <png>` (a venv with torch + transformers), then re-measure every polygon |

(v7b replaced the size and brightness rows: `w_deg` is 65 and `white` is 1.0; see §9.7's own knob table.)

### 9.7 v7b — THE HERO SIGN + NO SHIPS (2026-09-29 afternoon, after the user played v7)

**The asks.** *"Your sign is looking actually very good detailed to spec. My main issue right now is maybe it needs to be a
little bit bigger like 25% bigger and it needs to be way brighter it should be the one thing that sticks out in the skybox ...
not even close to how bright it should be"*; and, the same hour: *"we're adding spaceships to the map that fly around ... you
need to remove all the spaceships that you've added into the sky ... I don't want that inconsistency where you have some static
spaceships ... but then we have another agent adding actual models"* (the sky fleet, docs/192).

**Why v7 read dim.** v7 emitted the painting's white at 0.1467 W, the PREVIEW's display white (display-mult 10), so the
previews matched the reference pixel for pixel. But every other emitter in this sky is authored in W (§6), so in the sky itself
the sign stood 6.8x under the city's neon. And the finish's knee caps every channel at 1 W, so even a W-authored sign could
only tie the brightest city pixel, never beat it.

| | v7 | v7b |
|---|---|---|
| size (`GATE['w_deg']`) | 52 deg | **65** (x1.25; the text box stays at el 11; the spire tip rises to el 34.7, so session 61 moved its jump reveal's pitch -11 -> -13 to keep the whole gate inside the 2.35:1 bars, checked through the engine mapping) |
| the painting's own pixels (`white`) | 0.1467 W per display 1 | **1.0 W** = the city's unit (x6.8) |
| its neon (`neon`, a smoothstep on the painting's max channel `neon_lo` 0.55 -> `neon_hi` 0.95: the tubes and white-hot cores, ~20 % of the silhouette) | x1 | **x3 more** (3 W peaks) |
| the rebuilt halo (`glow`) | 0.1467 W | **3.0 W** (it belongs to the tubes) |
| the knee | the city's, 0.7 -> 1 W | **its own, 2 -> 4 W**, by the card's mask |
| the exposure solve | the whole sky | **outside the sign** (the city holds exactly; the sign is added light) |
| lighting (`lights`) | a weak mesh light | **camera rays + glossy reflections only**: it lights no fog, core or street (20x v7's neon would paint the core pink and scatter noise through the fog) |

**THE MASK.** The card writes a view-layer AOV `sign` = alpha + `mask_glow` (2) x the glow texture's max channel. The
compositor's File Output node writes it beside the raw as `<raw>.sign.exr` (Composite passes the picture through untouched).
`finish_sky.py` loads that path by default, normalises its interior (the fog scatters ~1 % of the camera paths before they reach
the card), and blends the city's knee into the sign's by it. The AOV is written only where the card is the camera ray's FIRST
surface, so a building in front of the sign keeps the city's knee. `--no-sign-mask` (`-NoSignMask`) is the v7 finish.
Measured on the region test (4096 scale, CPU): inside the sign mean 0.45 W, p90 2.2 W, p99 2.7 W, max 2.8 W per channel;
outside it p99.9 0.96 W, max 0.98 W. The sign's neon is ~2.9x the brightest city pixel.

**Two exposures, both good.** The previews at display-mult 10 put W 6.8x over display white. There the city's neon is already
pastel and the sign's neon clips pink-white: it is the brightest thing in view, but the PNG cannot show how much brighter. The
user keeps asking for a brighter sky (the 12:24 x8 pass, fd's +0.5 stop today), which says the game shows the sky darker than
that. At display-mult 1.47 (W = display white) v7's sign reads as a dark red sign and v7b's as bright red neon over the dark
city (`docs/sky_preview/sky3d_sign_v7_vs_v7b.png`, top v7, bottom v7b). Both brackets make the sign the one thing that sticks
out; the HDR headroom above 1 W is what the game's bloom sees.

**THE SHIPS ARE RETIRED.** The 3 airships, 5 battlecruisers, 12 fighters and ~38 loose aircraft lights are gone; the sky fleet
flies real models through the map. `retired()` still runs the airship and starship builders for their random draws and deletes
what they made, and the loose aircraft keep their draws but skip their boxes. So everything after them in the random stream (the
four searchlights) stays exactly where v7 put it. The buildings the v5b `ship_cap()` lanes kept low stay low (the city does not
move). The `ships` preview view is gone. `--ships` (`-Ships`) is the A/B.

**THE MOON follows the gate.** `moon_disc()` carries `MOON_REF` (the moon in the texture's pixels, 690.8 / 268.4, r 134.6)
through the card, so it still peeks out behind the crest at the new size: az -4.35, el 23.57, r 6.58 deg (was -3.3 / 20.7 / 5.1).

**THE TURN (session 61, the same hour).** The user's first jump showed the sign was NOT where the reveal camera looks. Session
61 decoded the engine's sky shader (docs/196 §3). ⚠️ The first reading below ("at skyRotation 0 the centre column faces world +X")
was INCOMPLETE: the user's 15:33 screenshot, rebuilt from the .map, put the sign at yaw ~41 with rotation 180. The firm rule is §2's:
the centre column faces yaw -(SSI sun azimuth 140 + skyRotation), and 61 sets skyRotation 40 for the gate due WEST. The v7
`--roll -90` had put the gate off the reveal shot, and the image seam inside it. The fix is in two places that move together: this finish is `--roll 0` (the gate stays on the centre column where Cycles
rendered it, and the seam goes due east, behind the camera; the image is clampU, so the gate must never straddle the seam), and
fd put `"skyRotation" "180"` in `mtl_skybox_tod_cybercity`. test_jumppad reads `roll` from `sky3d_stats.json` and fails any
half-landed pair. Residual risk (61): if the engine packed skyRotation's float2 the other way round, the gate lands north
again; 180 is the one value where the turn direction does not matter, and the user's next jump confirms it.

**The ship.** 8192 @ 160 spp on the GPU = 532 s (1,068,488 faces, 707 objects: the ships' 34 objects are gone). Finish
`--roll 0` with the v7 recipe (score 0.64, sat 1.2, display-mult 10, knee 0.7 -> 1 W) + the mask: the mask covers 2.34 % of
the sphere; the sign's peak is 2.88 W; the gain 1.2076e-02 (v7 1.2279e-02: the city 1.7 % darker, 0.02 stop — the solve no longer
counts the sign's region, which v7 had filled with a picture darker than the city's average, and the ships' light going away
pulls the other way); the city scores 0.640, the whole sky 0.687 (the sign adds +7.3 % light); seam
1.29x the adjacent-column noise. EXR 94,805,738 B, sha256 c312071e... (first written 13:36:08; re-finished byte-identically
13:42:49). The moon disc: az -4.35 el 23.57 r 6.58. `tools/art_cohesion/verify_tower_design.js` (fd) now pins the whole-sky
score as `SKY_SCORE` 0.6865346431732178 (the bake's sky energy includes the sign's light). A whole-sphere solve
(`--whole-sky-gain`, the city giving up the sign's 7 %) was tried and fails that gate. Move `SKY_SCORE` with it if it is ever
wanted.

**Testing while the game runs.** An 8 GB laptop GPU running BO3 has no room for an 8192 OptiX render. `--device cpu`
(`-Device cpu`) renders a region test on the CPU (at below-normal priority it did not disturb the game); the ship render waits
for the game to close.

| symptom | knob |
|---|---|
| the sign too big / small | `GATE['w_deg']` (65) — ⚠️ LOCKSTEP with session 61's first-jump scene: `tools/jump_title/gen_fx.py` places its blaze glows from `GATE` (w_deg, D, box_el) + `art/sky3d/sign/tod2_title_gate.json` (ref_width_px) + feature pixels on the reference, so moving or rescaling the sign makes `gen_fx --check` go stale (regenerate); changing `box_el` fails `test_jump_title.js` until `TOD_JT_SIGN_EL` in `_tod_jump_title.csc` matches, and moves the reveal pitch. Ping 61. |
| the whole sign (metal, banners, skull) too bright / dark | `GATE['white']` (1.0 W; x2 = one stop) |
| the neon too hot / not hot enough | `GATE['neon']` (3), `neon_lo` / `neon_hi` (which pixels count as neon) |
| the halo | `GATE['glow']` (3.0 W) |
| the sign's peaks clip too soon / too late in the EXR | `finish_sky.py --sign-knee-w 2.0 --sign-knee-max-w 4.0` |
| the city should give up the sign's light share (the whole sky back to score 0.64) | `finish_sky.py --whole-sky-gain` + move `SKY_SCORE` in verify_tower_design.js |
| the sign should light the city and the fog | `GATE['lights'] = True` (a mesh light; expect fog noise) |
| the static ships back | `-Ships` (A/B only; the fleet replaces them) |

### 9.8 v7c — NO ASTEROIDS (2026-09-29, late afternoon)

**The ask.** *"One more thing we need to remove are the asteroids ... we're going to add actual asteroid models going through the
sky so then we need to remove the static ones so those don't overlap static and dynamic."*

**What went.** Every static rock: the BELT (220 rocks arcing over the right sky, v5), the 90 DRIFTING rocks, and the DEBRIS
FIELDS of both black holes (gargantua 198, maelstrom 93: they read exactly like asteroids). 601 rocks in all; the scene drops from
707 objects to 106 (every rock was its own instance). The black holes keep their discs, the lensed halo, the photon ring, jets and
tidal streams; the cracked planets and moons stay (they are worlds, not rocks).

**How.** The same rule as the ships: the callers still compute every rock's place (the shared random stream), and
`scatter_rocks()` builds nothing, so everything after them (the rest of the bodies, the retired ships' draws, the searchlights)
stays exactly where it was. `--asteroids` (`-Asteroids`) is the A/B. The sign and the roll are untouched, so session 61's
jump-scene gates (gen_fx, test_jumppad) stay valid; the whole-sky score moves, so `SKY_SCORE` in
`tools/art_cohesion/verify_tower_design.js` moves with it (the gate's own rule): 0.6865346 -> 0.6865103.

**The ship.** 8192 @ 160 = 532 s (106 objects, 1,020,408 faces); the v7b finish; EXR 94,570,259 B sha256 fb178d52... 16:00:16. BUILT by session 22: FULL BUILD OK 16:23 (tmp/sky_asteroids/full1.log; the log is UTF-16), FF 222,709,376 B written 16:18:40, fresh bake (geom_key saw the sky), the NEW sky .iwi `HCVKQ32NX5A7IIAGB7VB4AS4WU` (31.2 MB, 16:16:28), `image,i_skybox_tod_cybercity` in the 16:18:40 ledger, deployed EXR sha = repo (fb178d52...), scripts / ui / zone_source diffs clean, nothing synced after. It also carried fd's companion freeze and d2's card UI. UNPLAYED.

## 10. v8 — A coherent cosmic cybercity (2026-09-29)

### 10.1 Direction

The user's new direction is a consistent dark cosmic cybercity: the title should belong to its architecture, the lower city should leave more room for space, and planets and stars should read clearly above the skyline. This supersedes the earlier request to reproduce the haunted gate painting. The v7 cutout remains a historical A/B option; it is no longer the shipping title or the source of the cinematic's colors and feature positions. Section 10 defines the current title, visible moon and celestial positions. Earlier exact-painting requirements, gate-linked moon geometry and reference-image cinematic anchors in section 9 apply only to that archived `--sign-style gate` path.

### 10.2 The authored title

`tools/sky3d/cyber_title.py` builds a physical monument in Blender: graphite chassis, recessed enamel panels, machined metal edges, bolted service rails, interrupted cyan/violet channels, cooling slots, structural blade supports and an open segmented energy crest with paired angular sensor ports. Broad finish variation, directional machining, seam dirt, fastener patina and selective contact wear distinguish the materials. Wear is placed on edges and joints rather than spread uniformly over every face. The final `cyber_monument_2` receipt records 12 objects and 21,988 base faces; its open crest and angular ports replace the first iteration's solid face-like crest.

The lettering is repository-owned Orbitron typography: `TOWER OF`, `DOOM II`, and `CYBERCITY`. Its face, bevel and backing are separate surfaces. Ivory letter edges, recessed caps and cyan secondary text remain distinct from the darker chassis. The crest has four cyan and four violet light segments; its two sensor cores are cool white-blue. The title writes the existing `sign` AOV and respects `GATE['lights'] = False`, so its brighter presentation does not turn it into a diffuse or volumetric Blender light.

The layout contract stays at `GATE` width 65 degrees, distance 1,000 m and elevation 11 degrees. The world bearing remains west, yaw 180. `--roll 0`, no image mirror, SSI yaw 140/pitch 130 and material `skyRotation 40` remain paired under the measured engine rule:

```
world_yaw = -(SSI_sun_azimuth + skyRotation) - roll - Blender_azimuth
```

For these SSIs the sun azimuth is 140 degrees. The jump camera remains yaw 180/pitch -13; neither flight timing nor the crash/reveal sequence is retimed.

`build_city.py` defaults to `--sign-style cyber`, saves an adjacent `<raw>.title.json` authoring report, and sends the monument's sign AOV through the existing finish. The archived painting is selected only with `--sign-style gate`; the old gantry is also retained for historical comparison.

### 10.3 Skyline and celestial clearance

363 ordinary window-grid blocks became four engineered forms: 93 blade foundries, 95 split vaults, 93 offset transit bastions and 82 forked terraces. Each has bounded utility masses, broad armor patches, seam recesses and sparse vertical inlays with nonuniform metal finish. Footprints and height ceilings stay intact. The wrapper runs the legacy builder to preserve every random draw, rolls back only ordinary-block mesh additions, then builds the replacement from private RNG. All 148,964 tall-spire facade faces, their roof faces, crystal slabs, traffic trails and transit ribbons remain byte-identical in the before/after scene audit. No global tower shortening was needed.

`skyline.py` measures a conservative silhouette at half-degree azimuth intervals, including solid roofs, attached neon rings/crowns/crystals and the title. `clearance.py` projects the actual planet, ring and moon vertices against it. All 20 planets/primary moon groups clear that envelope by at least 3.04 degrees. Atmospheric volumes, orbital tether cable, arbitrary FX and the two black-hole discs are not part of that planet-versus-building guarantee. Records: `art/sky3d/cohesion_review/clearance.json`, `skyline.json`, `preserved_spires.json`.

The visible moon is separated from the title crest. Its final disc position is azimuth 8 degrees, elevation 39 degrees, radius 5.1 degrees (previous gate-linked disc approximately -4.35 / 23.57 / 6.58). Its illumination direction (`MOON_EL`/`moon_dir()`) stays fixed, so this compositional move does not turn every planet's terminator or the scene's moonlight.

| Body | Previous azimuth/elevation | Final azimuth/elevation |
|---|---|---|
| giant | [-98.0, 14.0] | [-98.0, 49.0] |
| cool | [140.0, 34.0] | [140.0, 52.0] |
| ember | [32.0, 36.0] | [32.0, 55.0] |
| brown | [-60.0, 30.0] | [-60.0, 44.0] |
| ice | [110.0, 21.0] | [130.0, 64.0] |
| jade | [-176.0, 27.0] | [-176.0, 31.0] |
| obsidian | [128.0, 57.0] | [151.0, 64.0] |
| far_ember | [60.0, 30.0] | [52.0, 72.0] |
| grey | [52.0, 23.0] | [5.0, 53.0] |
| sombrero | [-100.0, 46.0] | [-110.0, 74.0] |

The giant's lowest ring/moon extent is 38.68 degrees. Several smaller bodies also moved sideways to avoid clustering after being raised. Faint stars fade in over 15-32 degrees, medium stars over 35-52, and large flares over 55-67. The raised gas giant exposed an existing ring-shadow error: a world-space light vector was dotted with local ring coordinates. The shader now transforms that vector into ring space and uses a finite penumbra; the obsolete rectangular stripe is gone.

Both black-hole definitions stay fixed: gargantua `(az 75, el 55, r 3.6, tilt 1.05)` and maelstrom `(-12, 70, 1.3, 1.25)`. Their literal source entries still feed `tools/sky_ships/gen_lanes.js`, keeping the moving asteroid orbits tied to the same hole bearings. Their existing plane-tilt convention discrepancy is recorded separately; this pass does not change the orbit definitions. The dynamic sky-fleet lanes and runtime scenery behavior are unchanged.

Static ships and all static asteroids remain retired. Their builders still consume the existing random draws before discarding their geometry, preserving the downstream seeded layout. `-Ships` and `-Asteroids` remain A/B-only options.

### 10.4 The first-jump reveal follows the authored sign

`tools/jump_title/gen_fx.py` now reads the literal `REFERENCE_WIDTH`, `FEATURE_PIXELS`, `CINEMATIC_COLORS` and `CREST_LIGHT_RADIUS_FRACTION` assignments from `cyber_title.py` with Python's AST reader. Native generation works without importing Blender, and neither the retired reference PNG nor its JSON defines the current title effects.

The main title and subtitle anchors stay at `(0,0)` and `(-4,100)` in the 1448-unit design grid; the crest and sensor centers stay at `(-2,-215)`, `(-42,-192)` and `(41,-192)`. Their palette is authored linear RGB: ivory `(0.82,0.85,1)`, subtitle cyan `(0.11,0.62,0.86)`, energy-weighted crest `(0.3208904109589041,0.4421917808219178,1)`, and both sensors `(0.62,0.87,1)`. The smaller crest's glow scales from 4800/4500 to 3244/3041 native units to retain the former halo proportion.

Only `fx_jt_blaze.efx` changes among the seven generated jump effects. The smoke veil, all timings, particle counts, alpha curves, bounds and velocities remain unchanged, as do both flight/client scripts. The storyboard already consumes the same generator table, so it follows these anchors and colors automatically. Storyboard effects remain illustrative stand-ins, not proof of native appearance.

### 10.5 Exposure, bake and proof

The existing finish contract remains: the city outside the sign holds target score 0.64; the city knee is 0.7 to 1 W and the sign knee is 2 to 4 W. The sign's contribution is added light, so changing its area or palette legitimately changes the whole-sky score. The measured final whole-sky `SKY_SCORE` is `0.6456634402275085`; `verify_tower_design.js` pins this value. SSI exposure, skyStops 4.35 and skyRotation 40 remain unchanged.

Use the fresh sign AOV from the same raw render. Darkening a broad fraction of the city can raise the finish's solved gain, so judge the finished panorama and record its RGB share, upper-half mean, peaks and gain as well as its score. The sky image supplies native GI and reflections: equal mean energy does not guarantee identical directional light or color. The changed image therefore requires a guarded FULL build and fresh LED/probe bake. No sun-volume, probe, fog or exposure retuning is part of this composition pass.

| Evidence | Final value |
|---|---|
| Blender master / raw render / sign mask / title report | `art/sky3d/tod2_sky.blend`; `tmp/sky_cohesion/raw_8192.exr` and `raw_8192.sign.exr`; `art/sky3d/cohesion_review/title.json` (`cyber_monument_2`) |
| Render size / samples / duration | 8192 x 4096, 160 samples, 508.158 s on Cycles/OptiX; `tmp/sky_cohesion/raw_8192.render.json` |
| Finished EXR SHA-256 / byte count | `7e4f8e519e33a2290dbdcc02c09755defa1e4c9dbe3c04130f5bdee52fba7c70`; 93,457,038 bytes |
| City score / whole-sky score / gain / RGB share | 0.64 / 0.6456634402275085 / 0.012666848866534757 / 43.2115% red, 22.8010% green, 33.9875% blue |
| Mean / upper-half mean / sign peak / seam ratio | 0.0006305307 / 0.0008106958 / 2.69428 W / 1.66311x adjacent-column noise |
| Skyline and planet clearance | 20 planet/moon groups, minimum 3.04 degrees (ember); giant lowest ring/moon extent 38.68 degrees |
| Full monument angular bounds | Azimuth -34.3825 to 34.4174 degrees; elevation -10.4652 to 28.5568 degrees |
| DOOM II angular bounds | Azimuth -20.4888 to 20.4888 degrees; elevation 7.0497 to 14.4927 degrees |
| TOWER OF / CYBERCITY angular bounds | -10.5130 to 10.5130 / 14.5950 to 17.0711 degrees; -8.3024 to 7.9092 / 5.0262 to 6.7710 degrees (azimuth / elevation) |
| Guarded FULL build log / completion / fastfile | `tmp/sky_cohesion/full.log`: FULL BUILD OK 2026-09-29 19:45:13 Eastern; FF 224,890,752 bytes at 19:38:51, SHA-256 `27a6f13ba405cf2b05d69ee43f245d15bc6b950f0ace77d2120336a03085e313` |
| Fresh sky `.iwi` / image/material/model/effect ledger entries + both SSIs in fresh LED | New `56XXDMGQ44UDHW46QRH6DEHQXY.iwi`, 31,251,297 bytes at 19:37:15; all 11 expected assets packed (sky image/material/model/techset + seven jump effects). Fresh LED 119,704,569 bytes at 19:36:25 carries both SSIs; the geometry receipt matches exact EXR/GDT/map input and BSP/LED output hashes |
| Repository/deployed source parity | 208 of 209 runtime files match the original snapshot exactly; 17 authoring artifacts match. One copied but unlinked Lucky script changed before the build, documented below. Linked-source snapshot parity is true; whole-snapshot/current-source parity is conservatively false |

Source checks passed during authoring: `python tools/jump_title/gen_fx.py --check`, `node tools/jump_title/test_jump_title.js`, `node tools/test_jumppad.js`, and `node tools/sky_ships/gen_lanes.js --check` (1,482 lane bands against 4,825 obstacles; two sky-wall blockers). `node tools/sky_ships/test_sky_ships.js` also passed: 224 complete flights; all 109 first appearances out of view; 240 asteroid drifts, 24 swallowed black-hole orbits (10 passing behind), 300 streaks, and all 13 negative controls caught. The final score also passed `tools/art_cohesion/verify_tower_design.js`; the guarded build passed its required pre- and post-link gates. The [build receipt](../art/sky3d/cohesion_review/build.json) retains the precise source, bake and packed-asset evidence.

The only exception is `scripts/zm/zm_tod2_cybercity/_tod_lucky.gsc`, edited by its owning session at 19:26:31 after the 19:26:18 snapshot. Its current and deployed bytes agree (`277469582c7da4cbc3978fa75f5d1c436399072f567c0a60d076cd98a2dcc9ed`), while the original snapshot records `dcc2541d492bbaa8aac668e3d68e83c5bff44b41a4acb584523da4ec386bdd1d`. Lucky is unwired: neither its GSC nor CSC sibling appears in the fresh compiled ledger, and none of the 193 scanned packed-script/UI/zone/header sources references its file or namespace. The verifier records this exact file in `ignored_unlinked_source_changes`; it does not waive a changed linked script, UI, zone or sky input. `linked_source_snapshot_parity` and `copied_sources_match_current` are true; `current_source_parity` and `deployed_inputs_match_snapshot` remain false. All deployed audited inputs precede the fastfile. The failed first attempt stopped before sky conversion/bake when the peer briefly wired unfinished Lucky assets; `tmp/sky_cohesion/full_attempt1.log` and `build_inputs_attempt1.json` preserve that attempt separately.

Native presentation remains **UNPLAYED** until the user's next match. The user checks the sign at the first-jump reveal, readable typography and crest/sensor flares, clear planets and rings in every direction, the dark city/space balance, and the absence of static duplicates of moving ships and asteroids. Agents build and stop; no unrequested game launch.


The [local review gallery](../art/sky3d/cohesion_review/index.html) links the saved final images directly. Only the title reveal, city and lower-skyline rows pair the same before/after camera; the cinematic reveal is a separate presentation view. These are Blender projection approximations. The gallery applies no additional grading, filtering or image transformation.

For a lightweight interactive view of the finished HDR panorama, open [sky_preview.blend](../art/sky3d/sky_preview.blend) with **Rendered** viewport shading and **Scene World** enabled; Numpad 0 restores the title camera. The saved [Blender screenshot](../art/sky3d/cohesion_review/blender_preview.png) and [preview settings](../art/sky3d/cohesion_review/preview.json) record the finished texture and display bracket. This is an approximate preview, with BO3 bloom and exposure still awaiting the user. The editable source remains `art/sky3d/tod2_sky.blend`.
## 11. v9 - A clearer skyline, ominous title and readable Skyrail station (2026-09-29)

### 11.1 The revised direction

The user found the previous panorama too busy, especially its city depth and secondary sky details, and agreed to a moderate reduction of roughly one third. The station also needed a clearer identity. The user then clarified that v8's title redesign had lost its awe and menace: the sign should be the most impressive dark cyber landmark. This direction supersedes section 10's exact cyber-monument design, lettering and cinematic palette. Earlier sections remain historical evidence rather than current title contracts.

The final v9 panorama has been rendered, reviewed, installed and included in a verified guarded FULL build. Native visual verification remains the user's playtest. The reductions below concern **authored content baked into the sky image**. They are not native entity counts or measured game-performance savings.

### 11.2 Deliberately reduce depth and secondary clutter

The final composition receipt records **1,222 visible building groups versus 1,838 before the pass: 616 fewer, a 33.51% reduction**. Ordinary lots fall from 1,792 to 1,189, megatowers from 45 to 32, and the tether remains one. All eight designated hero megatowers remain. Retained buildings keep their detailed material treatment, trim and structure.

`tools/sky3d/city_composition.py` ranks stable lot identities with a depth bias and small district variation. More nearby forms survive while distant layers become less crowded. The generator still consumes the original random draws, preserving the seeded placement and appearance of retained assets. Four ordinary lots are omitted for station clearance. Three lot records carry `title_clearance`; one was already excluded by the depth policy, so this removes two additional foreground crowns that overlapped the subtitle. The title rule rejects the whole nearby lot envelope in front of the gate plane, rather than shaving pieces from a building.

| Ordinary-lot band | Before | Final |
|---|---|---|
| core | 153 | 136 |
| near | 147 | 123 |
| middle | 657 | 464 |
| far | 580 | 336 |
| outer | 255 | 130 |

`tools/sky3d/sky_simplify.py` retires nine complete named sky groups: `dusk`, `far_giant`, `far_ember`, `far_a`, `far_b`, `far_c`, `edge`, `sombrero` and `harbinger`. The named celestial-group count goes from 27 to 18. This includes planets/moons, both black holes, galaxies and the static comet; it is not a count of individual discs, pixels or moonlets. Ten attached satellite moonlets remain. Both black-hole definitions stay unchanged for the dynamic fleet's source contract.

Floating sigils fall from 40 to 26, air lanes from 10 to 6, searchlight beams from 7 to 4, and crown lasers from 4 to 2. The star policy retains faint background stars while reducing medium stars and large flares. Spatial masks soften nebula competition around the title, station and selected sky sectors without changing global exposure. Static ships and asteroids remain retired. The retained architecture and space bodies keep their surface detail.

### 11.3 Restore an ominous title

`tools/sky3d/ominous_title.py` uses the approved `art/sky3d/sign/v9_ominous_gate.png`, SHA-256 `c57446ab29a92f3c85b7cbc421ec3d04a8f96aed0b5e01e1b82cb6c31db9b580`. The image was created with the built-in `image_gen.imagegen` tool from the saved reference artwork; its [prompt](../art/sky3d/sign/v9_ominous_gate.prompt.txt) and [provenance](../art/sky3d/sign/v9_ominous_gate.provenance.json) are preserved. The `ominous_gate_1` title restores a menacing industrial gate, dark metal and luminous crimson lettering, with violet secondary text. It replaces the v8 white-blue cyber monument as the default sign style.

The art is a packed 1414 x 1112 RGBA image on 7,158 sparse coplanar alpha-aware tiles. These preserve nonzero source alpha and the filtering margin without a full opaque canvas or an extra halo layer. Material relief is authored in the image; the gate is not a fully modeled three-dimensional structure. Its unaltered alpha feeds the existing `sign` AOV. Camera/glossy visibility and `lights_city = false` keep it from becoming a diffuse or volumetric Blender light.

The first projection made the metal and letter faces too pale. The final local presentation uses body emission strength 0.16 W and a 1.4x neon response, with shader strength reaching 0.224 W. This calibration changes the title presentation while preserving its source image and the city's finish/exposure settings. It is separate from the final measured sign peak of 0.5826132894 W in the finish receipt. The report's `reference_bracket` records the earlier 4096 calibration view; it is not the final 8192 gain or a BO3 measurement.

The reference width remains 65 degrees at distance 1,000 m, with the main-text anchor at Blender azimuth 0/elevation 11 degrees. The full-card angular bounds are azimuth -35.3253 to 32.3846 and elevation -18.3190 to 34.4331 degrees. The authored text regions read `TOWER OF DOOM II` and `FALLEN CYBERCITY`; the latter is image wording, not a map/repository rename. The title [receipt](../art/sky3d/simplify_review/title.json) contains the exact text bounds and feature angles.

`tools/jump_title/gen_fx.py` reads the new module's literal feature and linear-color contract. The title/core/ring/eyes are red and the subtitle violet. Offsets about source pixel `(707,481)` are title `(0,0)`, subtitle `(0,134)`, crest `(1,-174)`, and eyes `(-37,-191)` / `(41,-191)` on a 1414-pixel design width. The crest light radius is `145/1414` of sign width. Only `fx_jt_blaze.efx` changes among the seven generated effects; timelines, delays, element counts, the other six effects and both flight scripts remain unchanged. `gen_fx.py --check` passes all seven outputs and `test_jump_title.js` passes its positive and negative controls.

The measured world-bearing rule remains `world_yaw = -(SSI_sun_azimuth + skyRotation) - roll - Blender_azimuth`. SSI sun azimuth 140, `skyRotation 40`, `--roll 0` and no mirror keep the main sign due west at yaw 180. Jump-flight timing is unchanged.

### 11.4 Make the station readable

`tools/sky3d/cyber_station.py` builds one transit landmark at the existing nearest Skyrail position, replacing that line's overlapping legacy station/train presentation. The `cyber_station_1` [receipt](../art/sky3d/simplify_review/station.json) records 14 objects and 21,168 base faces: two boarding platforms, two visible tracks, a long split canopy, a five-car train and `SKYRAIL STATION` lettering. It does not add another cluster of towers, rings, holograms or beams.

Its center is `(642.9021, 11.2219, 400)` m, bearing 89 degrees and elevation 15.6389 degrees from the panorama camera. Bounds span azimuth 68.4278 to 109.5722 and elevation 13.5858 to 19.7801 degrees. The city checks the station's physical footprint and nearby foreground corridor, clearing local platform/track obstructions while retaining the distant district.

The final 8192 projection review found the station label, platform numbers, canopy, piers and pale articulated train readable; the right cab extends beyond the roof and finer train windows survive. Track tops are naturally occluded from the below-platform viewing angle. This is offline projected-image review, not native verification.

### 11.5 Clearance, finish and preserved contracts

The v9 skyline audit includes the retained city, attached skyline details, station and sparse title geometry. It conservatively includes faint title pixels; the title additionally exposes an alpha-0.25 silhouette profile for future analysis. All nine retired groups are explicitly checked for zero visible remaining objects. All **14 active planet/moon groups**, including applicable rings and moonlets, now clear the conservative skyline by at least **3.16 degrees**. This guarantee excludes atmospheric volumes, the tether cable and both black-hole discs.

The visible primary moon moves from elevation 39 to 41 degrees at unchanged azimuth 8/radius 5.1 degrees. Its measured clearance is 3.40 degrees, resolving the initial 1.39-degree conflict with the taller title crest. Its illumination direction stays fixed, preserving planet terminators and the scene's moonlight. Both black-hole bearings and the existing deferred orbit-plane unit discrepancy remain untouched.

The final finish holds city score 0.64 and measures whole-sky score **0.6336461901664734**, now pinned by the tower-design gate. The city knee stays 0.7 to 1 W, the sign knee 2 to 4 W, saturation 1.2, display multiplier 10 and preview gain 0.0176. SSI exposure, skyStops 4.35, skyRotation 40 and probe layout are unchanged. The final sign mask comes from the same raw render as the panorama.

| Final art evidence | Value |
|---|---|
| Render | 8192 x 4096, 160 samples, 572.441 s, Cycles/OptiX |
| Installed EXR / bytes | SHA-256 `0e160e9d1bd09e71e698162cbb7f670f843d26cd4f03099254b49d64033782a8`; 92,552,244 bytes |
| Installed Blender master / bytes | SHA-256 `cd131a7e6d2f595011f2f2516a9589255d0866a869baf0841c98886390464bfd`; 173,748,333 bytes |
| City / whole-sky score / gain | 0.64 / 0.6336461901664734 / 0.014337081656738686 |
| RGB share | 45.0983% red, 22.8333% green, 32.0684% blue |
| Mean / upper-half mean / sign peak | 0.0006187951 / 0.0007584684 / 0.5826132894 W |
| Wrap-seam ratio | 0.6504551x adjacent-column noise |
| Geometry clearance | 14 active planet/moon groups; minimum 3.16 degrees; primary moon 3.40 degrees |

Final projected views show no new wrap seam or orphaned parts of the retired sky groups. A faint vertical halo/texture crease above Gargantua's center is also visible in the historical v8 projection and remains an inherited preview limitation. It is not newly introduced or native-verified by this pass.

Under docs/162 chapters 05 and 06, directional sky color affects GI and reflections even when average energy is held constant. The changed image therefore requires a guarded FULL build with fresh LED/probe bake and a newly compiled sky image. The v9 source-pinned pipeline lives in `tools/sky_simplify/`, stages in `tmp/sky_simplify/` and records final evidence in `art/sky3d/simplify_review/`. It preserves v8's review folder, and `simplify_review/before/` retains the exact previous EXR/master/stats/preview. The author/render/finish/install receipts connect the used artwork, geometry modules, saved master, raw render, fresh sign AOV and installed bytes. The build snapshot records 209 runtime inputs and 77 authoring artifacts. The old v8 Lucky exception is not inherited.

### 11.6 Native build proof and review

The guarded FULL build succeeded in `tmp/sky_simplify/full.log`. The [build receipt](../art/sky3d/simplify_review/build.json), verified at **22:22:17 Eastern on 2026-09-29**, proves a fresh sky/probe bake, a newly compiled sky image and all 11 required sky/jump assets in the final ledger. Both SSIs appear in the fresh LED. The geometry record binds the exact EXR/GDT/map inputs to the BSP/LED outputs.

| Native build evidence | Verified value |
|---|---|
| Fastfile | 225,465,792 bytes at 22:20:29 Eastern; SHA-256 `b35213394e56e91e766bc4a1fa2e4ae18982858d43279ea57eeb7e0176caa386` |
| Fresh LED | 119,704,569 bytes at 22:18:02 Eastern; SHA-256 `48f5c09a4cfe9cd0fb03cdc90a47f677b6f60f23ab5e416c73d2c850d2b26db0` |
| New compiled sky image | `NYHHHP3JKYN35WNOGLSXXB646M.iwi`; 31,206,053 bytes at 22:18:50 Eastern; SHA-256 `42fab7218454fa1ed1bc93ae76957ee62f6220939410d3d4484947fab5e6eb35` |
| Exact runtime/source parity | All 209 runtime inputs match the snapshot and deployed copies; all 77 authoring artifacts match; no later-source or unlinked-peer exceptions |
| Packed sky/jump assets | 11 expected entries; both SSIs proven in the fresh LED |
| Build snapshot / log identity | SHA-256 `d62ac736628de5e51d4c19abd95e5a97bf30f99706c0ce925bfd0297d0435646` / `df890e2322b671f361ebd9d85aca6ed317994ca248de80b4fe4b6257d2467566` |

`current_source_parity`, `linked_source_snapshot_parity`, `deployed_inputs_match_snapshot` and `copied_sources_match_current` are all true. Every audited deployed input predates the fastfile. The guarded build passed its mandatory source, flight, geometry, lighting and post-link gates. No sync or build was performed as part of publishing this documentation, and the game was not launched.

The [local review page](../art/sky3d/simplify_review/review.html) opens with the final cinematic reveal, then pairs historical v8 and final v9 title/city images at the same camera and display bracket before showing the station, upper sky and full panorama. Detailed build and hash metadata is collapsed beneath the visuals. It links saved images directly without grading, filtering or transformations. These are Blender projections, not game screenshots.

For an interactive approximation of the finished HDR, open [simplify_preview.blend](../art/sky3d/simplify_preview.blend) with **Rendered** viewport shading and **Scene World** enabled; Numpad 0 restores the title camera. The saved [viewport screenshot](../art/sky3d/simplify_review/blender_preview.png) and [preview settings](../art/sky3d/simplify_review/preview.json) record the correct texture and display bracket. The editable source remains `art/sky3d/tod2_sky.blend`.

Native appearance remains **UNPLAYED**. The user checks title scale and menace during the first-jump reveal, subtitle readability, the less crowded city depth, the Skyrail station/train, celestial clearance and the city/space balance under BO3 bloom and exposure. Agents build and stop; no unrequested game launch.

## 12. Approved cyber middle ground (2026-09-30)

The user said v9 looked reverted: the title returned too far toward the old
super-scary gate and the buildings still read like New York. The user approved
[the new concept](../art/sky3d/middle_ground_review/concept.png): "Yes—use this
direction." This supersedes the v9 direction in section 11. The packed image
was verified as v9, so this was an art-direction miss rather than a cache rollback.

The title now uses the concept's engineered pylons, dimensional metal lettering
and smaller angular mechanical death-mask. Dark worn plates, red letter edges,
violet subtitle/channels and a few cyan inserts preserve its imposing presence.
The transparent artwork was extracted with built-in imagegen; the exact generated
pixels, prompt and provenance are preserved under `art/sky3d/sign/v10_cyber_hero.*`.
`cyber_hero_title.py` packs that source onto sparse alpha-aware Blender tiles. It
keeps the 65-degree reference width, 1,000 m distance, [0, 11 degree] title anchor,
`sign` AOV and camera/glossy-only visibility. The title does not illuminate the
city. First-jump glow offsets follow the measured main row, subtitle, forehead
channel and eye cores; timing and camera bearings are unchanged.

### 12.1 Architecture coverage and material quality

v9 modernized only 267 of 1,189 retained ordinary buildings. The new coverage
also includes ordinary spires below 400 m and nearer than 7,000 m: **624 modern
ordinary buildings, including 357 newly covered smaller spires**. The remaining
565 spires preserve the distant/tall silhouette. All 32 retained megatowers,
including the eight placed heroes, retain their positions and shapes. Their
surface treatment uses the dark spire material instead of bright office grids.

Four deterministic families—tapered keel, split crown, cantilever relay and
offset slot—provide taper, open slots and supported overhangs. New spire upper
masses are slimmer than ordinary blocks. Ring-deck and floating-platform pods
use the same kit at their actual deck elevation. Closed undersides and inset
roof panels keep these elevated forms physically coherent. Materials include
separate dark coating/exposed plate values, nonluminous panel joints, runoff,
recess dirt, varied roughness and shallow surface pitting. Sparse inset channels
carry emission. The review pass strengthened surface contrast where the first
candidate still appeared too smooth; the first candidate remains preserved in
`middle_ground_review/before_surface_refinement/`.

`check_architecture.py` exercises the real accumulator over all 624 affected
ordinary lot dimensions: 428,808 vertices stay inside their original local
width/depth/height, all four families appear, global RNG stays unchanged and an
elevated 713 m copy preserves topology, UVs and materials. It also checks the
strict coverage boundaries and rejects invalid inputs. The actual authoring
comparison preserves every original lot field and keep/drop decision, all hero
records, station keepout and celestial groups. Floating sigils on replaced
crowns are retired; the visible count falls from 26 to 19. Air lanes remain six,
search beams four and crown lasers two.

### 12.2 Layout, review and production status

The earlier moderate reduction stays intact: 1,222 building groups and 18 named
sky groups. The Skyrail station and five-car train retain their reserved view.
All 14 retained planet/ring/moon groups clear the conservative solid skyline by
at least 3.16 degrees; the primary moon now has 10.32 degrees of clearance above
the smaller engineered crest. No celestial body was moved in this pass.

The isolated pipeline is `tools/sky_middle_ground/`, staging is
`tmp/sky_middle_ground/`, and review/evidence is
`art/sky3d/middle_ground_review/`. Earlier v8/v9 evidence and the approved concept
comparison remain intact. The source/hash receipts bind authoring modules,
packed images, saved master, raw render and paired AOV to the installed asset.
The finish preserves the .64 city-score target and skyStops 4.35 / skyRotation
40; the measured whole-sky score is recorded with the final output.

The final panorama is **8192 x 4096 at 160 samples**. The installed source EXR
is 92,485,317 bytes, SHA-256
`feead2c4a543683c5903b6f98af8ee729621b7f584aa51ef167dcea25ea021fd`.
The city score is .64; the measured whole-sky score is 0.6343138813972473;
finish gain is 0.016525428679573573. The wrap seam is 0.6225
times the adjacent-column difference. No new wrap seam appeared in the final
panorama review. The inherited faint Gargantua halo crease recorded in section
11 is outside this revision. The final title, city, upper sky, station and
panorama have been reviewed. The [comparison page](../art/sky3d/middle_ground_review/final_review.html)
keeps the same cameras for the previous/new sky.

**Production status: guarded FULL build verified; ready for the user to test.**

Guarded FULL BUILD OK; verified 2026-09-30 09:46. FF 225,466,880 bytes at 2026-09-30T09:42:38.418042-04:00; fresh BSP/LED and both SSIs; new sky image i_skybox_tod_cybercity_WXHEDVDOTJLNYAXEVUKI6KL47L.iwi. All 209 runtime inputs match the captured snapshot and deployed copies; all 86 authoring artifacts still match; all 11 sky/jump assets packed. A separate in-progress _tod_shop.gsc edit landed after the build snapshot and is not included. Sky inputs are current; whole-checkout source parity is explicitly false. No later shop work was overwritten or synced. The saved finished preview uses
Rendered shading with Scene World/Scene Lights enabled. It approximates the
display bracket; BO3 bloom, exposure and visual quality remain the user's
playtest. Keep the case-safe asteroid fix. No agent game launch.

**Preview reopening correction (09:49):** Blender reset all saved viewports to
Solid when the final preview was reopened. The display-only
[launcher](../tools/sky_middle_ground/open_preview.ps1) restores Rendered and
Scene World/Scene Lights using `activate_preview.py`. Actual upstream MCP
activation and the [reopened screenshot](../art/sky3d/middle_ground_review/blender_reopened.png)
confirm the finished sky is visible. These two helpers were added after the
native build snapshot; they do not alter or resave any built art. The exact HDR
hash and settings are recorded in `preview_activation.json` alongside the review.



### 12.3 Exact native build evidence

| Evidence | Verified value |
|---|---|
| Fastfile | 225,466,880 bytes; SHA-256 `6116070342496dcaa6f2e6c4a61b117566dcada2bfa3a7be211ba040764047ff` |
| Fresh LED | 119,704,569 bytes; SHA-256 `09a608e156406e76e6dde6dfd3935e146b3bdf15b884d4d10ef54fa84231942a` |
| Compiled sky | `i_skybox_tod_cybercity_WXHEDVDOTJLNYAXEVUKI6KL47L.iwi`, 31,248,465 bytes; SHA-256 `b577af0ebdd58f1f850fef653693c76dda0f3bd935dfd036d1294389ff6ade6b` |
| Built snapshot / authoring parity | 209 / 86; later shop source edit explicitly recorded, whole-checkout parity false |

[Build receipt](../art/sky3d/middle_ground_review/build.json) binds these bytes to the captured source and fresh bake. No game was launched. Native visuals await the user.

## 13. Shared city architecture and readable celestial surfaces (2026-09-30)

The user likes the close cyber buildings but sees the distant city and sign as
different asset packs. They also report that planets and stars glow so strongly
that surface detail disappears. The approved close kit is now the common family:
all 1,189 retained ordinary lots use it, including the remaining 565 legacy lots.
The eight hero towers and 32 large landmarks retain their recognizable forms;
their surfaces use the same worn graphite/alloy palette, physical panel scale,
roughness, recess grime and subtle pitting. Upward landmark decks use worn alloy;
undersides stay dark. Landmark neon outline intensity is reduced locally.

The retained 1,222 building groups, station, cinematic anchors and celestial
positions are preserved. The actual accumulator geometry passes footprint,
height, elevated-lot UV parity and random-state checks. Composition auditing
compares all 1,792 candidate records with the approved layout. Replacing old lots
also removes obsolete hosts for 15 secondary floating sigils; four remain.

Planet body emission, hot cracks, ring/atmosphere glow and star strengths are
reduced separately. Directional light masks give gas and rock worlds a darker
side. Surface bands, craters and texture remain visible. This is not an exposure
change: native skyStops 4.35 and skyRotation 40 remain. Finishing uses the exact
approved baseline gain 0.016525428679573573, pinned by `finish_profile.json`, so
automatic normalization cannot brighten the unchanged city/nebula or cancel
the local reductions. City and whole-sky scores are measured outputs now.

The title keeps its approved imposing lettering and angular death-mask. A
neutral-metal-only highlight shoulder matches its frame to the city. The
lettering rectangle and saturated neon channels are protected. Parallel first
jump work (docs/196 section 6) requires a dull baked title plus a native lit
card after the crash. This pass carries that behavior through the authoring
configuration and enforces `sign_state=dull` at installation/build snapshot.

The native card uses a Blender material bake of the same immutable painting
through the shared frame shader. Exact source projection is checked at all
four image corners and the title anchor. Twenty-seven opaque scene objects
act as holdouts at their true depths, including the ground, so the runtime card
does not redraw hidden sign feet over the painted foreground. Source artwork
and native quad geometry remain unchanged; derived visibility alpha is
intentionally different. The normalized texture is exported as straight-alpha
RGBA with Standard/sRGB encoding, without bloom or denoising. Native scaleRGB
16 remains the first-jump owner's brightness setting. The final material bake
uses response **0.06** for architectural reflected spill; the shared lettering
rectangle and bright saturated tube cores retain full intensity. Tube protection
uses a smooth chroma gate from 0.35 to 0.75 multiplied by the highlight gate.
This preserves dark frame detail without changing preview exposure or the
native brightness knob. Final native brightness and soft-edge blending need
the user's playtest.

The reproducible pipeline is `tools/sky_consistency/`. The comparison gallery
is `art/sky3d/consistency_review/review.html`; historical evidence stays in the
older review folders. The finished Blender preview provides separate Before
jump and After reveal scenes, using the generated native model's actual UVs,
geometry and GDT texture/scale bindings. Its display conversion remains an
approximation of BO3. Preview screenshots do not establish native quality.

Production status: guarded FULL BUILD OK, 2026-09-30 11:26; verified 11:26:52.
The 8192x4096/160 render finished in 492.6 seconds. Fixed-gain city score is
0.4551386638; whole-sky score is 0.4450815916. The same celestial comparison
masks reduce all-channel >=250 clipping from 33.45% to 0.067%; these are display
PNG measurements. Both sign states were reviewed in Blender.

[Build proof](../art/sky3d/consistency_review/build.json) verifies all 212 runtime
inputs and 111 authoring artifacts, current source parity, fresh BSP/LED and
both SSIs, 11 packed sky/jump assets, and the native sign's model/material/image
plus exact two-triangle coverage. Fastfile: 225,982,016 bytes, SHA-256
`1e6dcdfe5e984f6273e66cf5ec33a6dfcaf4f8c3435510199acbd102d99c586c`.
Compiled sky: `i_skybox_tod_cybercity_7GK7H3JLFEPGLM3OY4JTWDN7NE.iwi`,
31,030,541 bytes, SHA-256
`b476db2ef977541729a3aa0d4834a57f303252424c99006bedd39c2c549cbe52`.

Two native import failures were fixed in the sign generator: BO3 rejects
leading GDT comments, and the 1536x1024 fixed-angular-size card needs
`noMipMaps=1` / `noPicMip=1`. Failed build logs and snapshots are preserved.
The failed-link sky cache was backed up and regenerated during the successful
forced fresh build; no stale-cache exception was used. A read-only SQLite
compatibility fix was captured before baking/linking; all 212 runtime inputs
were byte-identical across that verifier-only snapshot update. No game was
launched. Native appearance and reveal behavior await the user's playtest.

## 14. The Dealer above the city (2026-09-30)

The user accepted the consistent city and asked for the title's skull to
resemble the Black Market Dealer, appear around the map and become the final
boss. His canonical likeness is the actual shop vendor: dark hood, angular
charcoal mask, red X eyes and uneven stitched grin. The crest translates that
hood into the accepted title's worn cyber armor. The lettering, frame, city
layout, planet detail, station and first-jump reveal retain the approved design.
Final-boss encounter design is separate from this art delivery; see
[Dealer identity](dealer_identity.md) and [finale draft](dealer_finale_design.md).

The built-in imagegen tool edited the accepted title with the existing merchant
render as the character reference. [Source image](../art/sky3d/sign/v12_dealer.png),
[exact prompt](../art/sky3d/sign/v12_dealer.prompt.txt) and provenance are retained.
The frame and lettering are visually preserved, not pixel-identical. Measured
title, subtitle and both frame registrations are zero pixels; their mean source
brightness differs by less than 1.3%. The three crest glow anchors follow the
new forehead and eyes. Native card projection remains two triangles with the
same angular size, title bearing, material finish and foreground holdouts.

The isolated pipeline is `tools/sky_dealer/`; review evidence is
`art/sky3d/dealer_review/`. All 1,189 ordinary lots and 1,222 building groups
match the preceding composition. Fourteen celestial groups retain at least
3.16 degrees of clearance. The main moon's conservative alpha-bound clearance
is 8.81 degrees; the reduction comes from sparse edge pixels in the new title
image, not a moved planet or building. The meaningful opaque edge changes by
only 0.09 degrees. The final 8192x4096/160 render uses the unchanged gain
0.016525428679573573: city score .4551451667, whole score .4450453222.
Native skyStops 4.35 and skyRotation 40 remain unchanged.

Three small wall displays reuse a new 1024 portrait of the exact native vendor
and mask, with the existing worn graphite/bronze frame materials. Locations
and matched reviews are in [Dealer presence](../art/dealer_presence/review.html).
They add 84 noncolliding triangles and no entities, dynamic lights or runtime
threads. They foreshadow the same character without adding skyline clutter.

**Current status:** sky, lit card and three panel sources are authored and
reviewed. The first combined snapshot captured 214 runtime inputs and 154
authoring artifacts. Its build was stopped before map compilation/lighting when
the explicit sync list was found to omit the new portrait folder. The one-row
sync correction is now gated; the failed attempt's snapshot/log are preserved
under `tmp/sky_dealer/attempt1_sync_omission`. A fresh snapshot and guarded FULL
build are still required after shared-machine resource coordination. This is
not a completed native delivery. Blender preview lighting is approximate.
The user playtests, and no game has been launched by this pass.

Resource incident: another session ran Map One's Radiant from the shared Steam
tools while this pass's production denoise was finishing. That overlap could
have increased memory pressure on the 16 GB workstation; the reported Radiant
issue has no proven root cause. This pass closed its own Blender processes and
left the other map's processes untouched. Launch/render guards now cover the
real Radiant executable and native compiler stages; evidence stays alongside
the dealer review. Do not treat a successful render as proof that overlap is
harmless, or a preview as proof of native game appearance.

## 15. Distant facade detail and depth (2026-09-30, source stage)

**2026-10-01 correction: shipping builds unblocked.** Leaving the unrendered
architecture change in `tools/sky3d/cyber_architecture.py` invalidated a source
hash in the existing shipping card receipt, blocking every build at that gate.
The active file has now been restored byte-for-byte to the receipt's baseline
(`fef254fe...`). The depth candidate is preserved unchanged under
`tools/sky_depth/staged_sources/cyber_architecture.py` (`562224e6...`). The depth
workflow imports and pins that isolated candidate; it must not copy it over
the shipping source for a preview. The normal card gate, generated jump FX
check and jump scene contract pass. No gate exception, receipt rewrite or
runtime artwork change was made. Evidence: `depth_review/build_unblock.json`.

This extends the existing **wire last** rule to hashed authoring sources:
prepare unfinished art in an isolated directory, then publish a complete
reviewed source/art/receipt set. A source-only edit can block native builds
even when the runtime images are unchanged. This correction unblocks the
shipping card; the visual depth enhancement remains unrendered and unbuilt.

The user requested another pass on distant readability and outer-building
detail. This pass preserves the accepted composition, Dealer title, station,
celestial positions and fixed sky gain. It does not reverse the concurrent
high-altitude fleet additions or the latest jump timing and Dealer laugh.

The audit found that the native image already retains 8192x4096, compressed
HDR, no mipmaps and no picmip. A 16K sky is not supported by the established
native pipeline. At 10 km, an equatorial panorama texel spans about 7.67 m;
at 20 km, about 15.34 m. The 0.38 m material seams cannot carry distant
readability. Previously, architectural detail stopped beyond 10 km.

`cyber_architecture_4_depth` adds broad service recesses with actual inset
backs and bevels, asymmetric replacement armor and sheltered contact dirt.
Angular-size gates omit features too small for the native panorama. Structural
envelopes, roof silhouettes, neon and caller RNG remain unchanged. A bounded
0.78..1.0 orientation multiplier reduces the existing material ambient floor
on sheltered faces; it does not add light or raise emission. This shared
material change also affects near buildings and landmarks, which must be
included in the visual review.

The pure geometry audit uses the 1,189 accepted lot dimensions/positions with
explicitly sampled angles and palettes. It passes close-geometry equality,
silhouette/bounds, RNG, translated elevation and recess winding/open-mouth
checks. Its counts are sampled evidence, not production coverage. Actual
Blender authoring records every build call and projected bay size in
`tmp/sky_depth/author.json` under `depth_geometry`.

The isolated pipeline is [tools/sky_depth](../tools/sky_depth/README.md).
The exact previous master, EXR, stats, source and preview states are preserved
under `art/sky3d/depth_review/before`; earlier receipts remain historical.
The candidate sampling profile keeps the same 8K/160 maximum, lowers adaptive
threshold to .0125, raises its minimum to 32 and sets Cycles' actual
`filter_width` to 1.0 with `BLACKMAN_HARRIS`. Blender's `render.filter_size`
is not the Cycles reconstruction width. Receipts read back the actual Cycles
properties. These candidate settings require matched crop review before use.

Review three identical angular crops from (1) old geometry/old sampling,
(2) new geometry/old sampling and (3) new geometry/candidate sampling, all at
the same seed and fixed inspection exposure. Finalize the master before
these crops so their exact master hash matches production. Review broad
facade relief and nearby landmark shading, then record an honest visual
decision. The cropped Standard/sRGB output is approximate and cannot prove
native brightness or bloom. The final finished views and two-state preview
remain separate checks. The native lit card will be rebaked from this same
master to retain exact foreground visibility, without changing the approved
Dealer source painting or cinematic anchors.

**Status at source preparation:** no new sky Blender process, final render,
native installation or build has run. Another session's Dealer-boss Blender
studio/export and then a Map One linker occupied the workstation. Source and
pipeline checks passed; crop review, full production render, two-state preview
and a combined guarded FULL build remain pending resource clearance. Do not
claim this pass is visible in game. Do not close foreign sessions without
explicit user authorization. The user playtests; no game is launched here.
