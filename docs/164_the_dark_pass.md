# 164 — THE DARK PASS, part one: the crown hall (2026-09-24)

> **Status: BUILT — see §8 (the build record is appended there). UNPLAYED; the user
> tests.** Everything here is one full build behind a single generator switch
> (`DARK_HALL`) plus two sky numbers, and every number is a knob (§6).

The user, after the second Fall pass (docs/160 §10) and the lighting reference
(docs/162), on four questions asked before their playtest of the 13:56 build:

| Question | The user's answer |
|---|---|
| How dark should the crown hall read at spawn, before the alarm? | **Near-black, pools of light.** You only see what a light source touches: the alarm's red, the Pack-a-Punch, perk glows, a few fixtures. |
| Every Tron grid line and the crown's gold glow on their own. Should they? | **Keep edge lines only.** The thin edge lines keep glowing as guide lights; the large faces (gold, floor panels, walls) go dark so fixtures can light the room. |
| Should the sky darken with the map? | **Darken the sky too.** |
| Whole map or the crown hall first? | **Crown hall first.** Approve the spawn and alarm scene, then the same recipe goes down the tower. |

This pass does exactly those four things and nothing else. The circlet outside
the hall, the tower, the plaza and the Undercity are untouched except by the sky,
which is global.

## 1. Where the light came from before (measured, docs/162)

- Every visible world face was an emissive mirror: the hall floor `dark_blue_tinted`
  and the walls `purple_tinted` glowed over their whole surface at HDR 10, the
  gold at 15 (lines only), the ruby piers and the seams at 5; all of it
  `$white_diffuse` + gloss 15–16 + full reflection probe (docs/162 03 §11).
- The hall had ten point lights, all `stops 6`, radius 360–620, four of them the
  even-coverage quarter pools (docs/162 09 §3: The Giant's lights are median
  stops 7 / radius 150; ours were "weak and wide").
- The sky material baked at `skyStops 10.0` on a picture solved to sky-light
  score 0.324 — about 5.6 stops over stock `default_night`'s 4.4 (docs/162 05 §4.3).
- The exposure clamp was already the stock night one (EV 3..3.5, evcmp 2.5) and
  the previous build put the night SSI into the live state's slot (docs/162 T2),
  so a darker scene now stays darker instead of being re-exposed to daylight.

## 2. The materials: six dark clones, hall interior only

`tools/gen_tod_door_materials.js` gained a second family, generated into
`source_data/tod_materials.gdt` beside the five matte door hues and registered in
`tools/lint_tod_geometry.js` (LOCKSTEP: a name missing from the lint aborts the
build; a name missing from the GDT is a silently substituted white face):

| Material | Donor (plain grid) | Lint class | Faces (this regen) | Where in the hall |
|---|---|---|---|---|
| `tod_dark_floor` | `dark_blue` | DECK | 6 | the hall floor |
| `tod_dark_step` | `yellow` | DECK | 18 | sanctuary tiers 1–2, the uplink dais |
| `tod_dark_wall` | `purple` | BLOCK | 60 | the six wall runs, the gate lintel, the four corners |
| `tod_dark_gold` | `yellow` | BLOCK | 1302 | pier bases + capitals, the 80 arcade lofts, cornice, gate posts, shrine pilasters + canopies, reredos frame + crest, the upper-panel pilasters, the alarm gantry + pendant |
| `tod_dark_ruby` | `red` | BLOCK | 216 | the twelve pier shafts |
| `tod_dark_brass` | `orange` | BLOCK | 42 | the reredos field, the four upper wall panels |

Each clone is the donor's PLAIN grid texture — black tiles with one thin glowing
line per tile edge, the pack's own "edge lines only" look — with three changes:

- **matte**: the same zeroed specular / reflection block the door clones use
  (`specAmount 0`, `reflectionProbeAmount 0`, `glossRangeMax 0`) — no mirror;
- **`scaleRGB 8.0`** (the donor's 15): the Materials doc's 2^EV rule for this
  map's EV 3 clamp (docs/162 03 §3.2 called 15 "hot");
- **`colorTint 0.5 0.5 0.5 1`** (the donor's 1 1 1 1): the lit layer is half as
  bright, so a pool reads as light on a dark surface rather than white glare on a
  `$white_diffuse` face.

**What still glows in the hall, on purpose:** the two shrine panels behind the
altar and the Pack-a-Punch (`yellow_tinted_edge`, HDR 5 — the lit panel that
motivates each pool), the floor seams and the dais rims (1-unit `_tinted_edge`
lines — these ARE the edge lines the user asked to keep), the reredos stone and
monde (small ruby jewels), the parked extraction pad (`green_tinted_edge`, 160
square; the finale is parked and undesigned — the user's call), the alarm core
(plain red, the alarm), and the item shops (the peer's models). The underside
seen from below (`crown cap velvet` / `cap fillet`) and the whole circlet keep
their materials.

## 3. The lights: ten even lights → nine pools

`gen_tower_map.js`, the crown light block, behind `DARK_HALL`. Every pool passes
`lightingstate` (1,1,1,1) — power is on from the first frame, so there is no
state in which the hall should be unlit, and the pools do not hang on the T1
test's answer (the map-wide default is still (0,1,1,1); `light()` took a `mask`).

| Light | Before | After | Why |
|---|---|---|---|
| hall SW / SE / NW / NE (quarter points, +260) | 4 × warm, r620, s6 | **gone** | the even coverage |
| shrine W (altar) / shrine E (Pack-a-Punch), +160 under the canopies | warm, r360, s6 | warm, **r300, s7** | the key pools: strongest, tightest |
| crown gate (cyan, the way out) | r520, s6 | **r400**, s6 | wayfinding, kept |
| hall reredos (north wall wash) | r420, s6 | **r320, s5** | landmark |
| hall dais (under the alarm) | r520, s6 | **r260, s4** | dim: the alarm's flashing red FX light owns that spot once it fires |
| extraction (green, parked pad) | r460, s6 | **r240, s4** | landmark, dim |
| hall spawn (NEW) | — | cool `0.75 0.85 1`, r260, s4, on the west wall's spawn band | the party sees itself and its hands |
| hall shop 1–3 (NEW) | — | red `1 0.35 0.3`, r200, s4, 160 over each item shop | "buy here"; the peer's active shop carries its own sky marker |

The T1 test lights (docs/162; green = Radiant State 1, red = State 2) are still
on the west wall 48 apart beside the spawn until the user's log answers T1;
remove `LIGHT_TEST_T1` then — they sit inside the spawn pool.

## 4. The sky: −1 stop on the picture, −4 stops on its light

- `node tools/gen_tod_sky.js --theme evil --target-score 0.16` (was 0.324):
  gain solved 0.01285 (inside the 0.012..0.048 guard, so **0.16 is the floor
  for the picture through `--target-score`; below it, pin `--gain`**). EXR
  36.6 MB at 14:45:27, previews `docs/sky_preview/evil_*` refreshed.
- `source_data/tod_skybox.gdt` `skyStops` **10.0 → 6.0**. This is the bake's
  sky light (GI + the ambient that fills an open-top hall); it needs the full
  build's LED bake to show (docs/162 05 §4.3).
- Net: the sky throws about **5 stops less light** into the bake than the 13:56
  build; the picture you look up at is one stop dimmer. `sky_intensity_factor`
  (visible sky only) stays 1. The sun (`stops −2.2`, cool cyan moon) is untouched.
- Global by nature: the tower, the plaza and the spire lose the same sky light.
  Their emissive faces do not change, so they read as before minus the sky's fill.

## 5. How to judge it (shot list; docs/162 09 §7)

Same spot, same graphics config as the 13:56 screenshots. The user decides.

1. **Spawn, before the alarm, looking across the hall.** Expected: black floor
   with faint blue lines, dark walls with purple lines, the two shrine pools
   warm on the west and east walls, the cyan gate to the south, the reredos
   warm at the north end. Corners dark.
2. **At the altar and at the Pack-a-Punch.** Expected: a tight warm pool on a
   dark floor, the lit panel behind the machine, the machine's own glow.
3. **Looking up.** Expected: the evil sky one stop dimmer; the crown's gold
   band still lit (unchanged).
4. **The flood under the alarm.** Expected: the red flash on the dais and the
   nearest piers; zombies as silhouettes against the pools and the sky.
5. **A zombie in the west aisle between pools** — the readability check
   (docs/162 09 §2.1): if a zombie in the dark aisle is not readable, that is
   the first number to move (§6).

What to report: one of "too dark to play", "pools too hot / white", "grid lines
too bright", "sky too dark / not dark enough", "the rest of the tower is now too
dark", or "this is it".

## 6. The knobs, one per symptom

| Symptom | Knob | Where |
|---|---|---|
| hall still too bright overall | `skyStops` down again (each −1 = half the sky light) | `source_data/tod_skybox.gdt` |
| hall too dark to read zombies | `skyStops` up one; or raise the spawn pool / add one dim cool fill | `tod_skybox.gdt`; `HL(...)` in the crown light block |
| pools too hot / white | `stops` on the two shrine `HL` lines (7 → 6); or `colorTint` 0.5 → 0.35 in `DARK_FIELDS` | `gen_tower_map.js`; `gen_tod_door_materials.js` (re-run it) |
| grid lines too bright / too faint | `scaleRGB` in `DARK_FIELDS` (8; each doubling = +1 stop) | `gen_tod_door_materials.js` |
| sky picture too dark / bright | `--target-score` (0.16; the floor without `--gain`) | `tools/gen_tod_sky.js` |
| the tower outside reads too dark | the sky is global: accept, or split the sky (picture vs light) with `sky_intensity_factor` for the visible sky | worldspawn keys in `gen_tower_map.js` |
| want the old hall back for an A/B | `DARK_HALL = false` (materials AND lights revert); sky separately | `gen_tower_map.js` |

Every one of these is a FULL build (materials, lights, sky: docs/162).

## 7. Not in this pass (next)

- The descent: the same recipe for the terrace, the spiral, the plaza and the
  Undercity, once the hall is approved ("crown hall first").
- The reflection probes: still Radiant's default 144-unit cube, 53 of them
  (docs/162 06 — the fix plan). With the mirrors gone from the hall this matters
  less there, and everywhere else it still smears.
- T1's answer and the removal of the two test lights; then whether the other
  343 lights should carry (1,1,1,1) too.
- Bloom / grade (`pbg_box`) for the state the map runs in; fog banks for the
  alarm mood (docs/162 08 §11c) — mood, not brightness.

## 8. Build record

(appended below by the build that carries this pass)

### 2026-09-24 15:03:33 Eastern — FULL BUILD OK

| Check | Result |
|---|---|
| `.ff` | `zm_tod2_cybercity.ff` 210,979,392 B at 15:03:33 |
| repo vs deployed `diff -rq` scripts / zone_source / ui | clean |
| deployed inputs newer than the `.ff` | none |
| compiled `.map` | md5-identical to the repo's regen (the dark hall: 1,644 `tod_dark_*` faces, 9 pools, 0 quarter lights) |
| deployed GDTs / EXR | `tod_materials.gdt` carries the six clones; `skyStops 6.0`; EXR sha = repo's (14:45:27 render, score 0.160) |
| assetinfo ledger | six `material,tod_dark_*` rows; fresh content-hash sky `.iwi`; the alarm fx still present |
| LED | 100,163,699 B |
| navmesh | 3 components |
| sky image | fresh content-hash `i_skybox_tod_cybercity_MQKNV2FNFY73SVUK76KVNUCAW7.iwi` 20,124,631 B at 15:02:18 (ledger `image,i_skybox_tod_cybercity#d438aef5`); linker warnings = the established ten, none naming a `tod_dark_*`; log `tmp/dark_pass_build/build.log`, exit 0 |

No launch; UNPLAYED. The user tests against §5's shot list.

## 9. PART TWO: THE BLACKOUT (2026-09-25)

User, after a playtest: "the map to be dark and it should be really dark and
... the only thing that brings light or that you can see pretty well is maybe
the sky and then once power's on things will light up dynamically ... right now
the map is not dark enough, it doesn't bring that scary vibe enough." Asked:
ALMOST PITCH BLACK before the power; REMOVE THE GLOW EVERYWHERE (world glow
cannot switch with the power, so it must be what both states can live with); A
WAVE DOWN THE TOWER at the power. The veil fog is removed (`TOD_VEIL 0`).

| Lever | Before | Now | Where |
|---|---|---|---|
| world glow | every face emissive (the Tron grid) | none: every face wears `tod_black_<suffix>` (scaleRGB 0, matte, albedo = line hue x 0.35) | gen_tower_map.js `BLACKOUT`; tools/tod_black_materials.json; gen_tod_door_materials.js |
| placed lights | on in Radiant State 2 (the boot state) | on in Radiant State 1 ONLY | `LIGHTS_AT_POWER` in light() |
| the power | stock power-on | + the wave, then `util::set_lighting_state( 0 )` | `_tod_fall::power_wave` |
| sun before power | ssi2 = the night SSI (sun -2.2) | `tod_ssi_cybercity_dark` (sun -5.2; -7.2 after the user's 11:27 look: "I dont think its dark enough still") | `SSI_PREPOWER`; tod_skybox.gdt |
| sky light on the world | skyStops 6.0 | 4.0, then 1.0 after the 11:27 look (1/32 of the original) | tod_skybox.gdt |
| the visible sky | factor 6.5 | unchanged | worldspawn |

THE PROOF THE STATES WORK THIS WAY is the user's own log (archived
tmp/elite_tracking/runs/20260925_103800_982_ec8afb2e): `[TOD_LIGHTSTATE]
level=1 player=1` at spawn, blackscreen and power = script state 1 = Radiant
State 2, as docs/162 inferred. The wave's last line should read
`[TOD_LIGHTSTATE] at=wave_lit ... level=0 player=0`.

**Knobs, per symptom.** Pre-power too bright: skyStops lower, or the dark
SSI's `stops`. Pre-power too dark to move: skyStops up one. Powered too dark:
the `albedo` in tod_black_materials.json (0.35), or the lights' stops. Wave too
slow/fast: `TOD_FALL_WAVE_SECS`; full light too late: `TOD_FALL_WAVE_HOLD_SECS`.
A/B: `BLACKOUT = false` / `LIGHTS_AT_POWER = false` bring back the glow and the
always-on lights (a full build).

**Not in this pass.** Model glow (the altar, the PaP, perk machines' own
emissive parts) is untouched; the spire's trial-hall plates keep their art;
floor-by-floor BAKED light (exploders) is the upgrade path if the wave's FX
light plus the single state flip reads too sudden (docs/162 02 §14.2).

**Build record.** FULL BUILD OK 10:57:28 Eastern (tmp/blackout_build/build.log): FF 206,779,392 B, fresh BSP + LED 100,173,570 B, navmesh 3 components, 8 known-waived warnings (none a tod_black_*), all 24 tod_black_* materials the map uses in the linker ledger, banks 109.4 / 209.3 MB. It carries everything in this pass EXCEPT the 5000 gate (TOD_FALL_GATE_OPEN 0, edited after its sync): the -GscOnly meant to carry it halted before the linker on a PEER session's in-progress tools/art_cohesion/verify_surfaces.py (a crown-material pass that keeps world emission at zero); that crown session is a THIRD session (not the sky session). ITS OWN FULL BUILD then carried the gate: BUILD OK 11:20:25 Eastern (tmp/art_cohesion/full_build.log), FF 206,925,056 B, LED 100,170,906 B, navmesh 3 components, 8 known-waived; its sync ran after the gate edit (10:52:09), so the 11:20:25 .ff has EVERYTHING in this pass plus the crown's textured surfaces. That -GscOnly's sync did run, so the deployed SOURCE tree is newer than the .ff — the .ff itself is the 10:57 build.

**Second darkness step (user 11:27: "I dont think its dark enough still").** skyStops 4 -> 1 and the dark SSI's sun -5.2 -> -7.2. Built by the SKY session's full build (it also carried the v6 sky and the Retriever ammo-counter crash fix): BUILD OK 11:43:06 Eastern, FF 206,925,056 B, LED re-baked 11:41:42 (100,170,906 B), navmesh 3 components, 8 known-waived; deployed GDT verified skyStops "1.0" / dark SSI "-7.2", nothing synced after the .ff. UNPLAYED. NEXT LEVER if still too bright: the dark SSI's exposure (evmin/evmax up = darker, pre-power only, but it also dims the visible sky before the power); the crown session's hall surfaces (albedo up to 1.0 vs the blackout's 0.35) are the other suspect in the spawn room.
