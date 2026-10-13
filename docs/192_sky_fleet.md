# 192 - THE SKY FLEET (huge ships flying through the sky)

**2026-09-29 23:49 - ASTEROID FREEZE CORRECTION BUILT; USER RETEST PENDING.** The first v3 playtest exposed the case-insensitive d/D local collision in rock_state (section 11). Guarded script-only build passed; FF 225,465,920 bytes at 23:48:11. All 209 captured runtime inputs match current/deployed sources; only the fleet CSC changed. Exact proof: `tmp/freeze_audit/build.json`. The old bug is reproduced by the corrected test evaluator; no agent game launch.

**v3 BUILD HISTORY: (s10: flames, wormholes, detail, asteroids, black-hole rocks, shooting stars) BUILT in session 0a's FULL BUILD OK 2026-09-29 18:10 (.ff 18:02:01, FF 224,136,320 B, tmp/sky_ships/full_v3.log; compiled check: 15 models exact, 65 effects). UNPLAYED.**

**v2 STATUS (history): v2 (s8 detail + s9 flight) BUILT in session fd's FULL BUILD OK 2026-09-29 (.ff 14:23:04, FF 216,215,232 B,
tmp/spire_removal/full1.log; compiled check: 8 models exact, 10 effects, no warp). UNPLAYED. v1 was BUILT 11:49:36 and PLAYED 13:03
("more detail and more movement ... like an airplane ... spawn far away ... pass the tower").** Ships
authored live in Blender through MCP (studio port 9890); master `art/sky_ships/sky_fleet.blend`; review renders
`art/sky_ships/review/` (v2: `v2_<ship>_<view>.png`, `09_detail_review.py`). Sections 1-7 are v1's design; s8-s9 supersede
them where they differ (no warp; far approach; the detail).

User 2026-09-29: *"I would want to build these with blender MCP and then scale them up huge and
fly them through the sky repeatedly. Spawn them in randomly and then fly over the sky."* +
*"Minor details are not needed but high level detail should be 100% so its very obvious from far
away."* + *"Open an instance of blender so i can watch your work."*

## 1. The experience, moment by moment

- **The sky is alive.** Wherever you are in the run, look up or out and there is traffic: a
  capital ship crawling across the sky, a cargo hauler dragging its containers, a gunship cutting
  across, a wing of fighters streaking past in a V. Cybercity is fallen; its fleet still flies.
- **Warp in.** A white-hot flash blooms in empty sky inside a wider cyan glow and a spray of sparks,
  with a low boom (far away, echoing). A huge ship slides out of the flash, bleeding off speed.
- **Cruise.** Big ships are slow (minutes to cross), small ships are fast (seconds). Engines are the
  brightest thing on each ship (white-hot exhaust spikes + glow + a light trail); neon lines trace the
  hull's outline; window bands give it scale; red and green running lights mark port and starboard
  (steady, not blinking, in this pass). From below (where you usually see them) the belly reads too:
  the hangar glow, keel lines, engine blaze.
- **Warp out.** The ship accelerates away and vanishes into a flash.
- **Never in the way.** No ship ever passes through the tower, the crown, the spire or the arena.
  Ships are scenery: they never block a shot, never hide a zombie, never make noise over combat.
- **As you descend, the traffic comes with you.** Each ship picks an altitude near yours, so the
  fleet stays in view from the crown hall down to the plaza.

## 2. Readability rules (the user's bar: "very obvious from far away")

1. **Silhouette first.** Each class is a different SHAPE you can name at a glance: arrowhead
   dreadnought, container hauler, forked gunship, delta fighter. No greebles, no micro panels.
2. **Big features only.** Nothing a player needs to read is smaller than ~100 units; emissive lines
   are 40-80 units wide on the big ships (1 px at 15,000 units is ~16 units).
3. **Brightness ladder.** Engines > neon edge lines > window bands > hull. The hull is dark metal so
   the lights carry the shape at night.
4. **Scale cues.** Window bands and container stacks say "this is enormous".

## 3. The fleet

| Class | Length (units, with exhaust) | Silhouette | Colour variants | Cruise | Crosses in | Live cap |
|---|---|---|---|---|---|---|
| DREADNOUGHT | 11,300 | long arrowhead hull, stepped command tower at the stern, two huge side engine pods + a triple main engine, glowing belly hangar, two window rows a side | red / cyan | 120 u/s | 68-125 s | 1 |
| HAULER | 6,600 | wedge cockpit with a lit visor, a spine carrying 18 coloured containers in two tiers, a four-drive engine block | amber | 200 u/s | 46-114 s | 1 |
| GUNSHIP | 3,600 | forked bow (two prongs), forward-swept wings, twin canted fins, two drives | magenta / green | 650 u/s | 16-39 s | 1 |
| FIGHTER | 1,070 | delta dart, twin canted fins, one fat drive; a V wing of 3-5 | cyan / orange | 1,600 u/s | 8-15 s | 1 wing |

The numbers live in the authoring scripts (`tools/sky_ships/02..05`, exported sizes in
`art/sky_ships/manifest.json`) and the director (`add_class` in `_tod_sky_ships.csc`); this table is a
snapshot. Triangles: 2,214 / 1,008 / 622 / 298. Glow (`sky_lib.EMIT`, native scaleRGB): neon 48, engines
110, windows 18, running lights 70, hangar 32, canopy 24, containers 3.5 - sized from the crown alarm's
lesson that distance eats emission in this map (36 -> 144 to read from ~10,000 units). One table to retune.

## 4. How it works

- **Client-side only.** Each player's own game spawns, flies and deletes the ships
  (`spawn( localClientNum, origin, "script_model" )`, `MoveTo`, `RotateTo`, `PlayFxOnTag`,
  `Delete`). Treyarch's multiplayer Swarm killstreak (`scripts/mp/killstreaks/_missile_swarm.csc`)
  is this exact pattern. Zero server entities (the spire's binding budget), zero network traffic.
- **Inside the sky seal.** The map is sealed in a sky box (x/y +-12,224, z -544..39,500); the Umbra,
  sun and FPS volumes all cover it. Ships fly INSIDE it, so they are lit, culled and drawn like any
  other object. They spawn and leave INSIDE it too, which is why they warp in and out.
- **Lanes are generated, not typed.** `tools/sky_ships/gen_lanes.js` reads the live `.map`, measures
  every solid brush with `tools/convex_brush.js`, and emits the straight lanes (plus the altitude
  bands per class) where the whole ship clears every structure by a margin and stays inside the
  seal. The same check re-runs on every build, so a later geometry change cannot put a lane through
  a wall.
- **The spawner.** Per class: a random gap between arrivals, a live cap, an altitude chosen around
  the local player's height, a random lane and direction. Warp-in, cruise, warp-out, delete.

## 5. Evidence (what is verified vs. still a test)

- VERIFIED: the sky itself cannot move (its material has a fixed `skyRotation` only; no script
  function touches the sky).
- VERIFIED: client scripts spawn, move, rotate, link, show/hide and play tag FX on client models
  (stock `_missile_swarm.csc`, `zm/_ambient.csc`, `_helicopter.csc`, `_microwave_turret.csc`).
- VERIFIED: an xmodel is dropped only by on-screen size (`cullOutDiameter`, "stop drawing this model
  if its on-screen pixel diameter is less than this value", default 0), not by distance.
- TEST: how a very large client model looks in the native renderer (lighting, LOD switch, bloom).
  The first playtest answers it; dev logs `[TOD_SKY]` record every spawn and delete.

## 6. Files, gates, logs

- Authoring (Blender MCP, port 9890): `tools/sky_ships/mcp_bootstrap.py` + `mcp_call.py`; `01_studio.py`
  (textures + materials), `02_dreadnought.py` .. `05_fighter.py`, `06_export.py` (xmodel_bin + staged GDT +
  manifest), `install.py` (staged GDT -> `source_data/tod_sky_ships.gdt`), `07_review_renders.py`,
  `08_retune_glow.py`, `96..99` studio view helpers, `98_backdrop.py` (our real sky EXR as the studio backdrop).
- Generated: `gen_lanes.js` -> `scripts/zm/zm_tod2_cybercity/_tod_sky_lanes.csc` (+ `art/sky_ships/lanes.json`,
  plan views `plot_lanes.py`); `gen_fx.py` -> `share/raw/fx/tod/sky/*.efx`; `make_sounds.py` ->
  `sound_assets/tod/sfx/tod_sky_*.wav` + `sound/aliases/tod_sky.csv`.
- Runtime: `scripts/zm/zm_tod2_cybercity/_tod_sky_ships.csc` (#using from the entry .csc). No server half.
- Gates (build_map.ps1): `gen_lanes.js --check` (re-tests the committed lanes against the LIVE map; fails only
  when a lane is really blocked), `gen_fx.py --check`, `verify_native.py` (+ `--compiled-ledger` after the link:
  all 7 models with exact triangle counts, the 6 effects, every material), `test_sky_ships.js`.
- Dev logs `[TOD_SKY]`: READY (lanes loaded), SORTIE (ship, model, wing, lane, from/to, speed, player),
  WARP_OUT, DONE (deleted count, live), NO_LANE, REVEAL. `TOD_SKY_LOG 1` for playtests, 0 before a publish.
- First-jump reveal: session 61's `util::clientNotify( "tod_jump_reveal" )` arrives as a CSC level notify; a
  fighter wing crosses high (el ~28 deg) and a hauler low over the city, both flying south with the rider,
  on paths the generator checks clear (`reveal_high` / `reveal_low`). The sky sign sits due WEST after
  session 22's roll; the title box (el 7..15) stays clear.

## 7. Open follow-ups (the user's call)

- ~~The painted sky still carries frozen battlecruisers, fighters and an asteroid belt~~ - session 22 retired the
  painted ships (13:44) and every painted asteroid (16:23) so the moving ones replace them.
- ~~Asteroids (tumbling rocks) and meteor streaks~~ - BUILT in v3 (section 10).
- Recorded sounds can replace the synthesised ones by the same file names.

## 8. v2 - "a lot more detail" (user 2026-09-29 13:10)

User, after playing v1: *"those need a little bit more detail and more movement ... they actually need a lot more
detail. I underestimated how much detail we should be adding."* The silhouettes stay (they read); each ship gains the
LAYERS that make AAA capital ships look enormous and inhabited, built with a reusable kit
(`tools/sky_ships/detail_lib.py`; every piece a closed, outward-facing solid with explicit winding):

| Kit piece | What it gives far away |
|---|---|
| `plates_on_loft` | raised armour plates over any lofted hull (merged 1x1..2x2, inset, lifted, walled; a share in the lighter armour = two-tone): shading breaks that catch the moon |
| `turret`, `mast`, `dish`, `dome` | silhouette breaks: gun batteries, antenna masts with cross-arms (each tip carries a light), radar dishes, sensor blisters |
| `vent_bank`, `fin_bank`, `truss` | louvres, radiator fins, lattice beams |
| `nozzle` | flanged bells with collars, lips and a glowing throat (the exhaust plume is a slimmer cyan/amber cone now, not a white blob) |
| `block_field` | greeble fields sampled on the hull surface |
| `deco_quad`, `ad_panel` | emissive markings (map typeface) and billboard screens |

| Ship | v1 tris | v2 tris | What was added |
|---|---|---|---|
| DREADNOUGHT | 2,214 | 35,364 | 536 plates; tiered dorsal citadel with window rows, masts, dishes, domes; 14 heavy triple turrets, 20 point-defence, 8 belly turrets; a detailed command tower; finned plated pods on trusses; flanged nozzles; 3 lit hangar bays with chevrons; TOD-01 + the crown emblem on the belly; ~780 greebles; waist strakes; a keel blade; 70 belly lights |
| HAULER | 1,008 | 13,874 | framed corrugated containers with corner lights + HAUL-07 / crown markings; truss spine + clamps; finned engine block + RCS pods; plated cockpit, bridge windows, masts; THE BILLBOARD (3 of the sky's ads under the cargo, 2 portrait screens on the block) |
| GUNSHIP | 622 | 3,994 | railgun prongs (coil rings, emitters), panelled wings, tip pods, missile racks, chin ball turret, framed canopy, intakes, searchlight, mast, GS-13 |
| FIGHTER | 298 | 1,056 | plates, intakes, 4 missiles, wing panels, framed canopy, fin lights |

Textures (`make_textures.py`, system Python + PIL, deterministic, `--check` in the build): `i_tod_sky_plate_c/plate2_c`
(2048: a recursive 16-px panel layout, seams, bolt rows, recessed insets, vent slots, grilles, hazard plates, grime
and run-off streaks) with a matching `plate_n` normal map + gloss/spec; `win2_c` (four rows of lived-in windows);
`deco_c` (TOD-01 / HAUL-07 / GS-13, the crown emblem, chevrons, arrows - fonts/tod_tower1.ttf); `ads_c` / `ads2_c`
(8 of `art/sky3d/billboards`). Colours and atlas cells live in `sky_data.py` (shared by Blender and system Python).
Variants: every class has a B model now (the hauler's B swaps its neon to teal AND its ad wall). Export guards: every
material under 60,000 vertices (one BO3 surface), exact compiled triangle counts (verify_native).

## 9. v2 - the flight: "like an airplane", far away -> past the tower -> far away (user 2026-09-29 13:15-13:20)

User: *"They should be kind of going across the sky like an airplane"* + *"the spaceships shouldn't spawn like pretty
close to the tower. They should spawn kind of far away and kind of move in the direction of the tower and pass by ...
then they fly away from the tower once they pass it ... cyber realistic."*

**The experience.** A few pixels of silhouette and a blinking strobe appear low over the horizon, on the side you are
NOT looking at. The ship grows steadily as it comes in, descending toward the city; it passes the tower at full size
(fighters weaving and banking in their V, gunships weaving, capital ships swaying slowly), engines blazing and
trailing light; then it climbs away and shrinks back to a blinking point. No flashes, no pops.

**How (all in `_tod_sky_ships.csc`, all data generated in `_tod_sky_lanes.csc`):**
- A flight is a straight line through a generated PASS lane, extended far beyond the sealed box both ways. The ship
  starts `approach` units before the lane (where it is `spawn_px` pixels long: 14 big / 12 gunship / 10 fighter) and
  flies at `speed * (1 + d / xs)` until the lane, so far out it closes fast but LOOMS steadily (its distance halves
  every `xs*ln2/speed` s), then cruises through the pass and leaves the same way (climbing).
- **THE SCALED STAND-IN.** Nothing may draw outside the sealed box (+-12,032). A ship beyond it is drawn on the same
  line of sight, closer and smaller: distance x k and SetScale(k) - identical on screen (the Source-engine 3D-skybox
  trick). `stand_in()` finds the largest k in closed form: each box corner moves linearly with the drawn distance
  along the camera ray, so every corner/axis gives one bound. Inside the lane k = 1 and it is the real ship.
- **Blockers.** `gen_lanes.js` lists every solid within 7,000 of a side wall or the top (grown 400, merged): the crown and
  the arena after the spire's removal. A stand-in overlapping one is hidden that tick (the structure stands between the
  player and the far ship). The build re-checks that every live solid near the walls is still covered.
- **Out of view.** `choose_way()` flies the lane the way whose far approach bearing is outside a 55-degree cone around
  the camera's view (a coin toss only when the lane runs square across the view).
- **Lights.** White strobes (big ships double-flash) and red beacons are one-shot flashes at the model's light anchors
  (exported with the models), sized `max(drawn distance x 0.0045, k x the class's light size)` in three effect sizes, so
  a far ship reads as a blinking point like an aircraft at night.
- Engine FX (they cannot follow SetScale) run only at full size; the engine loop sound from k >= 0.6.
- Knobs: `MOTION` in `gen_lanes.js` (speed, xs, spawn_px, glide / climb, weave, bob, bank, sway, schedule; the lanes'
  clearance grows with the weave / bob / bank); `TOD_SKY_*` defines (view cone, tick, light size, `TOD_SKY_BANK_SIGN`
  if the banks look like skids).
- The v1 warp flash / boom are retired whole.

**Session 61's first-jump crash (docs/196).** Two v2 gunships collide in front of the dimmed sign (61's
`_tod_jump_title.csc`); at `tod_jump_title_ignite` (under the white-out) this module sends `reveal_high` - a fighter wing
across the blazing sign, high and behind the smoke, centre of frame ~2 s after ignite - and `reveal_low` - a hauler far
out near the horizon, 11 degrees left of the sign, that passes the tower about half a minute after the landing.

**Proof (`test_sky_ships.js`, build gate).** `tools/sky_ships/gsc_eval.js` interprets the pure GSC, so the gate flies
the SHIPPING functions (pick_lane, choose_way, make_path, path_pose, wing_pose, path_speed, stand_in): 112 whole flights
from seven player spots x four views, every tick of every ship INSIDE the box, on the camera ray at the right scale
(BEARING), CLEAR of every real solid (oriented-box test), SMOOTH; every flight appears and vanishes small; the salute's
timing and clearance of the crash; 8 negative controls (a stand-in without the wall fit, no blockers, a return after
spawn, no delete, missing zone lines, the warp coming back). Flight lengths: dreadnought ~194 s, hauler ~123 s,
gunship ~55 s, fighter wing ~20 s.

**Logs** `[TOD_SKY]` rev=2: READY (lanes, blockers), SORTIE (lane, dir, pass start, speed, approach, glide / climb,
player, camera), FULL (the ship reached full size), DONE (secs, ticks, `hidden_ticks`, `k_min`, `full`). Judge in play:
the speeds (`MOTION.speed`), the pop-in size (`spawn_px`), the bank direction, and how often ships hide near the crown.

## 10. v3 - propulsion, wormholes, more detail, asteroids, shooting stars (user 2026-09-29 ~15:40)

User, after v2: *"They look a lot better ... one more iteration ... right now they don't have any propelling system ...
I can't see any flames coming out of the back of the jets or the spaceships or ... some time warp black hole pulses ...
some of the spaceships should come through like a wormhole ... fighter jets probably just need fire and flames and
exhaust ... add more detail to each of the spaceships"*; then *"add kind of flying asteroids going around ... a little
bit more subtle than the spaceships ... higher up in the atmosphere. But still visible, so players can see the
movement ... and also shooting stars"*; and *"Make sure we focus on quality and detail of each."*

**The experience, moment by moment.**
- A far ship is a blinking point with an ENGINE GLINT behind it (cyan for plasma drives, orange for fire). As it looms
  in, the glint becomes a real flame: every nozzle burns its own effect, sized to the drawn nozzle. Capital ships and
  gunships run PLASMA (a white-hot disc in the bell, a flickering white core ray, a wide cyan plume, heat shimmer, a
  glowing contrail left in the sky); the DREADNOUGHT's five main drives also throw a TIME-WARP PULSE every 1.8 s (an
  electric shock ring ripping out of the drive, a lens-distortion ring, a violet flash) and its eight auxiliary
  thrusters fire too. FIGHTERS burn real FIRE (an animated flame flipbook, three afterburner shock diamonds, sparks,
  a lit vapour CONTRAIL). HAULERS burn heavy industrial fire trailing SMOKE and embers.
- About a third of the flights arrive through a WORMHOLE, opening where the player is looking: the rift tears open
  (a swirling violet-cyan vortex, lightning, a lens ring, a rising sound), and 1.6 s later the ship BURSTS through
  (a crack, a boom, a shock ring) at 3.2x its cruise speed, growing out of the rift and easing back to cruise. Some
  flights leave the same way: a rift opens ahead of the ship, the ship shrinks into it, the rift collapses with a
  suck and a pop.
- ASTEROIDS drift high over the city (never below 22 degrees): single rocks or clusters of 2-4, 7-45 px at their
  closest, tumbling, swelling out of the distance and fading back into it over one to two minutes, 0.35-1.1 degrees
  a second (you can see them move). Five rock models (boulder, shard, veined, slab, rubble; the veined and slab rocks
  carry glowing magenta / cyan / amber mineral veins and crystals).
- The two painted BLACK HOLES (Gargantua, the Maelstrom) keep rocks in orbit: they circle in the painted disc's own
  plane, speed up as they spiral in (Kepler), pass behind the shadow on the far side, and are swallowed at the
  horizon with a flash.
- SHOOTING STARS every 6-22 s (three kinds: quick bright, medium, long slow), now and then a SHOWER of 4-7 from one
  radiant, and every 80-200 s a FIREBALL (orange, or green) that bursts into fragments.

**The detail pass** (v2 tris -> v3; every ship's silhouette kept):

| Ship | v2 | v3 | What was added |
|---|---|---|---|
| DREADNOUGHT | 35,364 | 45,752 | flank trenches with cyan light strips and ribs, cyber light lines tracing the upper flanks, a forward bridge, a keeled prow, radar arrays between the citadel tiers, intake vanes + rim lights, 8 auxiliary thrusters, pipe runs, docking clamps, TOD-01 on both bow flanks |
| HAULER | 13,874 | 19,262 | a bridge tower (wheelhouse, dish, beacon mast), twin banded fuel tanks, two gantry cranes over the cargo, lock bars on every container, marquee bulbs round every ad screen |
| GUNSHIP | 3,994 | 6,614 | a dorsal twin cannon, shield emitters on the prongs, a belly sensor pod, afterburner petals, trailing-edge flaps, greeble fields |
| FIGHTER | 1,056 | 2,016 | canards, intake splitters, a dorsal spine with a racing stripe, a nose sensor spike, afterburner petals, canopy frame |

**How.**
- FLAME TAGS: every nozzle is a bone `tag_eng_<i>` (child of tag_origin, at the exhaust plane, turned 180 degrees
  about Z so +X points aft), exported by `06_export.py` and checked by `verify_native.py`. The director plays the
  flame with PlayFXOnTag; the tag follows SetScale, so a stand-in's flames sit on its nozzles (`tag_check()` proves
  this once per game in play; if tags did not scale, flames would show only at full size).
- Effects cannot be scaled, so each flame kind exists in FIVE SIZE BUCKETS (1, 1/2, 1/4, 1/8, 1/16 of the kind's
  reference nozzle); `flame_bucket()` picks the one within sqrt(2) of the drawn nozzle, with 12 % hysteresis. A nozzle
  under ~2 px on screen (or below the smallest bucket) shows the angular GLINT instead (three sizes).
- Every effect is GENERATED by `gen_fx.py` from stock BO3 elements (materials, flipbooks, element types) rewritten
  to explicit sky-scale numbers; the 17 stock donors are snapshots in `art/sky_ships/fx_donors/`. 65 effects:
  4 kinds x 5 flames, 6 glints, 3 rift phases x 7 sizes, 3 stars + their trail, fireballs (2 colours + trails +
  bursts + fragments), the v2 lights, and `fx_sky_eng_gunship` (session 61's crash scene plays it: the same plasma
  flames at the gunship's nozzles, so that scene's engines match).
- RIFTS are camera-facing effects on a `tag_origin` host moved every tick to the rift's stand-in, in 7 size buckets
  (2000 ... 31 units) because a rift can be drawn anywhere from a map corner to the far wall. A rift that a structure
  would hide is not opened (the ship arrives / leaves the normal way).
- NO POP-INS: `flight_pops()` samples a planned flight every second from the player's camera; a flight whose ship
  would come into or leave sight longer than 40 px (a structure hiding its approach - the crown round a player in the
  crown hall) is re-planned on other lanes, then the other way round, else not flown (`NO_LANE why=pops`).
- ASTEROIDS are the same scaled stand-in (a ball-shaped box), on great-circle drifts in bearing space
  (`rock_plan` / `rock_state`); black-hole rocks orbit in the painted disc's plane, derived from `build_city.py`'s hole
  table and the GDT's skyRotation + SSI sun yaw by `gen_lanes.js skyHoles()` (Gargantua sits at yaw 105, the
  Maelstrom at 192 with skyRotation 40).
- STARS are runner effects (a billboard flying at a baked speed with an attached trail), placed by `star_plan()`
  inside the sealed box, above 12 degrees, clear of every structure; the speeds are baked into the effects and read
  back by the director from the generated lanes file (LOCKSTEP by generation).
- EVERYTHING RUNS ON REAL TIME (session 61's finding: client `wait` counts frames): motion advances by the
  `GetRealTime` delta, schedules use `waitrealtime`.
- Sounds (`make_sounds.py`, synthesised): `tod_sky_worm_open` (2.4 s), `tod_sky_worm_burst` (3.0 s),
  `tod_sky_worm_close` (1.7 s), 3D at the rift, under combat.

**Proof (`test_sky_ships.js` v3, a build gate).** 224 whole flights (4 classes x 7 player spots x 4 views, normal and
forced through rifts) run through the SHIPPING director functions (`flight_plan`, `plan_once`, `flight_pops`,
`stand_in`, `engine_want`, `rift_make`, `worm_boost` ...): every tick INSIDE / BEARING / CLEAR / SMOOTH, every flame a
real effect within 0.6-1.6x of the drawn nozzle, few swaps a flight, every rift inside the box, unhidden, in its size
bucket; 109/109 normal flights first appear out of view; 82/110 rifts open in view; nothing pops in or out big (49
re-planned, 5 refused). The first-jump salute crosses the sign at ignite + 4.0 s (t 8.8, inside 7f's clear-title
window 7.4-10.3), 3,795 u from the crash. 240 asteroid drifts (inside, on the ray, above 18 degrees, never popped,
visibly moving, peak 7-45 px), 24 black-hole orbits (they stay round their hole, 10 pass behind it, all swallowed at
the shadow), 300 streaks (inside, above the skyline, 17-34 degrees long). Lockstep (every effect precached, zoned,
children two deep, the rift aliases, every model zoned, one flame tag per nozzle) and lifecycle (ships, rift hosts,
rocks deleted on every path). 13 negative controls.

**Logs** `[TOD_SKY]` rev 3: SORTIE (+ `tries`, `worm_in`, `worm_out`), WORM_OPEN / WORM_BURST / WORM_CLOSE / WORM_SKIP,
TAG_CHECK (do tags scale), DONE (+ `rt_ratio`, `fx_swaps`, `tags_scale`), NO_LANE (`why=pops|no_lane`), ROCK / ROCK_DONE,
HOLE_EAT, STAR / SHOWER / FIREBALL, REVEAL. `TOD_SKY_LOG 1` for the playtest, 0 before a publish.

**Judge in play (knobs):** flame looks (`gen_fx.py` `flame()`: lengths, colours, alphas), how often rifts appear
(`MOTION.worm` in `gen_lanes.js`: in/out percent), asteroid rate and size (`TOD_SKY_ROCK_GAP_*`, `rock_plan` `big`),
star rate (`TOD_SKY_STAR_GAP_*`, `TOD_SKY_SHOWER_PCT`), fireball rate (`TOD_SKY_BALL_GAP_*`).

## 11. Asteroid update error flood (2026-09-29 user playtest)

The user reported severe freezing. The preserved console at
`tmp/freeze_audit/runs/20260929_233655_105_096bbe02/console_mp.log` contains
14,327 script-error blocks, all naming `_tod_sky_ships.csc`, from 76,342 to
232,697 ms. The first error occurs 5.651 seconds after the fleet READY message,
inside the first asteroid's 3-8-second start window. Ships, stars and rifts had
not yet started; Lucky/golden records only show initialization. The log and
the deployed old script are preserved under `tmp/freeze_audit/`.

Native CSC local names are case-insensitive. `rock_state()` assigned a direction
vector to `d`, then a scalar distance to `D`; both name the same slot. At birth,
the captured shard has radius 655.6 and angular size zero, so the distance floor
gives `2 * 655.6 / 0.00001 = 131120000`. The erroneous `cam + d * D` therefore
adds `17192454400000000` to the camera vector. This exactly matches the first
native error's `1.71925e+016` operand. Its undefined result cascades through the
placement/update loop, producing about 92 error reports per second.

The correction uses distinct `direction` and `distance` locals. The one-time
READY diagnostic now includes `rock_math=case_safe` to identify the repaired
script in the next playtest. The test evaluator now case-folds local bindings,
parameters, foreach destinations and assignments while preserving string keys.
The focused regression runs the shipping zero-age shard calculation at the
captured camera position; restoring `d`/`D` must fail with the exact captured
operand. Run `node tools/sky_ships/test_sky_ships.js --native-semantics-only`
for that short regression. It also runs before the normal whole-flight gate.

Independent audits found no other case-only local collision in the 69 fleet
functions or 19 generated lane functions; generated calls and data match.
Guarded script-only BUILD OK, verified 2026-09-29T23:49:50.526166: FF 225,465,920 bytes at 23:48:11.
Both the focused native-semantics regression and the complete fleet simulation
passed (224 flights, 240 drifts, 24 orbits, 300 streaks, plus the existing
13 negative controls). `tmp/freeze_audit/build.json` proves all 209 runtime
inputs match the captured/current/deployed hashes, the repaired CSC is packed
in the fresh ledger, and geometry/lighting are unchanged. Only the fleet CSC
changed at runtime. No game was launched by the agent; native freeze resolution
requires the user's next test, checking `rock_math=case_safe` in READY and
absence of repeating script errors while asteroids appear.

## 12. v4 - the sky filled up: the high layer, convoys, the high belt, satellites, the entity budget (user 2026-09-30 ~20:30)

User: *"We have spaceships and meteors throughout the sky. Can we add more but at a higher altitude. I would love the
sky filled up. Maybe 1.5x more"*; *"if there are any enhancements you can make for a more atmospheric player experience
lets do it"*; and *"lets make sure we dont have any leaks or bugs. Ive already had a game where my game was freezing
cause of this. We have to make sure things get cleaned up completely and we have some efficient code on all these
moving parts"* (the freeze was s11's asteroid error flood).

**The experience, moment by moment.**
- THE HIGH LAYER. A second stream of traffic ABOVE the first. Every class keeps the schedule the user approved (v3's
  low layer: 1,500..9,000 u over the player's feet, 3,500..14,000 u sideways) and gains a second one flown 9,000..20,000 u
  over the player and 1,200..16,000 u sideways, so it crosses nearly overhead: seen from the crown hall's open roof or
  the terrace it is never under 31 degrees up and often near the zenith (71 of 110 gate flights above 60 degrees).
  Dreadnoughts up there are rare (one every 90..200 s), haulers / gunships / fighter wings every 20..90 s. The
  expected ships in the sky at once go 5.9 -> 9.3 (x1.59; the gate computes it from each schedule's cap and gap and
  the measured flight times).
- CONVOYS. 30 % of normal hauler flights lead a freight convoy: one or two more haulers on the SAME line 16 s astern
  (~8,300 u at cruise: a 1,700 u gap between a stern and the next bow), each a little staggered (+-250 u sideways,
  +-120 u up). 22 % of gunship flights fly as a patrol pair 7 s apart. Only a lead that is ALONE in its tier may bring
  followers (convoys never pile up past the cap + its followers), and never a rift flight (the followers would come out
  of nothing / fly on past a closed rift).
- THE HIGH BELT. A third (35 %) of the asteroid drifts and shooting stars now start 58..86 degrees up; a shower's
  radiant can sit as high as 78. Rates x1.5: rocks 6 -> 9 at once, a new drift every 3.5..9.5 s (was 5..14), a streak
  every 4..15 s (was 6..22), a fireball every 55..135 s (was 80..200); the black holes carry 9 + 6 orbiting rocks
  (was 6 + 4).
- SATELLITES. Up to three at a time, a new one every 20..55 s: a warm-white point of 2.7..7.1 px crossing the upper
  sky (never under 30 degrees) at 0.2..0.5 degrees a second for 70..160 s, tumbling - a small white flare every
  2.2..4.5 s. The night sky's slowest movers; you notice them when you stop to look.

**How.**
- ONE TABLE still: `gen_lanes.js MOTION` gained `hi` (the high schedule: first, gap, cap) and `convoy` ([% of normal
  flights, followers min, max, seconds astern]) per class, emitted into the generated `motion()` as `hi_*` /
  `convoy_*`. The director runs `class_loop( def, tier )` twice per class; `sched()` / `live_key()` (one live counter
  per class per tier) / `tier_name()` are pure; `pick_lane( def, p, tier )` plans the tier's window (the high tier's
  relaxed pass keeps the altitude floor and drops the sideways limits first); `sortie( ..., tier )` counts against its
  tier.
- CONVOYS are fixed-path sorties: `convoy_fixed( def, plan, side, dz )` (pure) builds the follower's path from the
  lead's plan; `convoy_followers()` launches them on real time.
- SATELLITES: `sat_plan()` (a great circle like a rock's drift, floor 30 degrees), `sat_point()` (the stand-in of a
  far point, one shared `ball_def` cached on level), `sat_fx()` in FOUR sizes (`gen_fx.py SATS` 18 / 48 / 110 / 250 u:
  the xs size is for the crown hall, whose north wall is only 3,700 u away) on a `tag_origin` host, re-picked when the
  drawn distance crosses a size boundary; the flare is a strobe one-shot (`light_fx`), as the ships' lights are.
- THE POP GUARD, TWICE TIGHTER. `flight_pops()` judges a hidden <-> shown change by the LARGER size of the two samples
  round it (a departing fighter accelerates: between two 1 s samples it went from 54 px in sight to 30 px behind the
  crown), and it samples the FALLBACK of a rift departure out to the normal departure distance. v3 decided the
  departure rift at flight time only (WORM_SKIP: "fly out instead") and never checked that fly-out: the gate's new
  random draw caught a fighter flying out behind the crown at 59 px. Now `plan_once()` tries the departure rift from
  the planning camera like the arrival (hidden -> a normal fly-out, which the guard samples); the flight-time skip
  stays as the fallback for a camera that moved.
- THE ENTITY BUDGET (the user's leak / freeze worry, made mechanical). `TOD_SKY_ENT_MAX` 96 per client: every client
  entity the fleet spawns (ships, rift hosts, drifting rocks, orbiting rocks, satellite hosts) is counted at its spawn
  (`ents_add`) and uncounted at its Delete; a sortie / drift / satellite that would pass the budget is not started
  (`BUDGET` log, nothing spawned). Every cap, convoy, 4-rock cluster, orbit and rift host at once would be ~105 (the
  gate computes it), so the budget bites only in that pile-up; normal play sits around 40..60.
- CLEANUP AND COST. Every spawn has its Delete on every path (the gate's lifecycle block now checks sortie, drift,
  hole_loop, satellite and the rift pair function by function, requires the number of spawn sites to equal the number
  of budget counts, and the live counters to go up and down exactly once); `rift_end` is idempotent (the host is
  cleared after its Delete, so the sortie's final double call cannot uncount twice); the black-hole loop makes ONE
  `ball_def` per orbiting rock instead of one per tick (v3 churned a struct per rock per tick); satellites share one.
  Per entity per 0.1 s tick the work is one `stand_in` (8 corners x 3 axes + 2 blockers), one MoveTo and one RotateTo;
  at the budget that is under a thousand MoveTo a second, no per-tick logging, no growing arrays (every counter is a
  bounded int per client); `flight_pops` runs at most 600 samples x 8 attempts once per sortie, never per tick; the
  schedules run on real time. The v3 error-flood class (a script error inside a 0.1 s loop) has no new entry points:
  every loop guards its entity with isdefined, the tier / key / budget helpers are pure, and `test_sky_ships.js`
  interprets them under native (case-insensitive) local semantics.

**Proof (`test_sky_ships.js` v4, the build gate).** 336 whole flights (4 classes x 7 spots x 4 views: normal, through
rifts, and THE HIGH LAYER) through the SHIPPING director: every tick INSIDE / BEARING / CLEAR / SMOOTH, every flame a
real effect within 0.6..1.6x of its nozzle; high layer 110 flights passing 9,015..19,904 u over the player, seen >= 31
degrees up, 71 near overhead, 0 relaxed, 2 refused (pops); 28/28 convoy followers fly the lead's path clear, pop-free
and reach full size, a follower never overlaps its lead (gap x speed > ship + 400); 120 satellites high, on the ray,
inside the box, 0.2..0.5 deg/s, 2.7..7.1 px from every spot; 216/219 flights first appear out of view, 70 re-planned
+ 7 refused so nothing pops in or out big; the salute unchanged (crosses at ignite + 4.0 s); 240 drifts, 24 orbits,
299 streaks; the schedules (each high layer rarer than its low one, its own key), the expected fleet x1.59 inside
1.4..1.8, the budget's worst case 105 of 96, `ents_free` / `ents_add` exercised; lockstep (the 4 satellite effects
precached + zoned) + lifecycle; 19 negative controls (6 new: a satellite host never deleted, the high layer never
started, a drift that never uncounts, a convoy allowed while the lead is not alone, satellites allowed low, the high
layer flying low).

**Logs** `[TOD_SKY]` rev 4: READY (+ `high_layer=1 caps_low= caps_high= hi_alt= rocks_max= high_pct= sats_max= ent_max=`),
SORTIE (+ `tier= convoy= alt_over_player=`), CONVOY (lead, followers, gap), BUDGET (what was refused and the count),
SAT / SAT_DONE (`shown_ticks`, `flares`, `live`), DONE (+ `tier=`). In the user's next log: `rev=4` in READY, zero
script-error blocks while the sky is busy, `ents=` in any BUDGET line (none expected), and SORTIE `tier=high` lines
with `alt_over_player` >= 9000.

**Judge in play (knobs, one line each):** how high / how near overhead the high layer passes (`TOD_SKY_HI_ALT_*`,
`TOD_SKY_HI_NEAR` / `_FAR`); how much of it (`MOTION.hi` gaps and caps in gen_lanes.js: the gate prints the expected
fleet); convoys (`MOTION.convoy`); the high belt's share and band (`TOD_SKY_HIGH_PCT`, `TOD_SKY_HI_BELT_*`); rock /
star / fireball rates (`TOD_SKY_ROCKS_MAX`, `*_GAP_*`), orbiting rocks (`HOLE_ROCKS`); satellites (`TOD_SKY_SATS_MAX`,
`TOD_SKY_SAT_GAP_*`, `TOD_SKY_SAT_RAD`, `TOD_SKY_SAT_FLARE`); the safety net (`TOD_SKY_ENT_MAX`).

**Build.** -GscOnly BUILD OK 21:56:29 (tmp/sky_ships/gsc_v4.log; the watcher built the moment the game closed at 21:45): FF 225,991,104 B at 21:54:42; every fleet gate ran inside it (PASS sky fleet v4, SKY LANES OK 1482 bands, SKY FX OK 69, arity, native API); the ledger (21:54:42) carries the 4 satellite effects, 91 sky effects, `_tod_sky_ships.csc` + `_tod_sky_lanes.csc`; scripts / zone_source / ui diffs clean, the 4 effects + both scripts deployed = repo, nothing synced after the .ff, the 8 known-waived linker errors only (a -GscOnly: geom_key notes the map / sky moved since the 11:22 FULL build - peers' pending passes, not this one). SUPERSEDED AS THE TEST .ff by the Black Market voice session's -GscOnly BUILD OK 22:38:24 (tmp/black_market_vo/gsc10.log; FF 225,991,040 B at 22:36:23): it carries v4 whole (PASS sky fleet v4 ran inside it, deployed director + zone = repo, the 4 satellite effects in its 22:36 ledger, banks whole: loaded 132,233,728 B, streamed 291,417,984 B = the 277.9 MiB both logs print). That link overlapped Map One's publish language passes (its session asked every Tower II session at 22:37 to hold linkers until ~22:50; this session held and relayed it). UNPLAYED: the user judges the density, the height, the convoys and the satellites in game.
