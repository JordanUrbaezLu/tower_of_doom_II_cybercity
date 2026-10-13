# 162 — Lighting reference: start here

Requested 2026-09-23: *"I need you to become an expert at lighting ... this map is
especially going to be unique because it's going to be dark ... write up what you
find so that moving forward we can use your write-up as a reference."*

This folder is that reference. It covers every way light gets into a Black Ops III
custom zombies map, how Treyarch did it on a real zombies map (The Giant, whose full
lighting source ships with the Mod Tools), what the community learned, and what it
all means for **Tower of Doom II: Cybercity**. It was researched on 2026-09-23 and
2026-09-24 from the official Treyarch Mod Tools documents, the stock scripts and map
data, this repo, Map One's repo and community sources. Every load-bearing claim was
checked a second time against the primary sources, and each chapter was then
accuracy-edited against them.

> **Nothing in this reference was tested in game.** Every statement carries a tag:
> **[VERIFIED]** read in an official doc, stock script, stock data or the engine API
> list; **[COMMUNITY]** from other mappers or this project's own records;
> **[INFERRED]** reasoned, not seen; **[TEST]** needs an in-game or bake test to
> settle. The user tests; agents build and stop.

## The chapters

| # | File | Read it when you want to know... |
|---|---|---|
| 01 | [Lights](01_lights.md) | what kinds of lights exist, every setting on a light, how to make a light dimmer or brighter, shadows |
| 02 | [Power and lighting states](02_power_and_states.md) | how lights turn on with the power, why "the whole tower lights up", how to light one floor at a time |
| 03 | [Things that glow](03_glow_and_perks.md) | glowing materials, perk-machine glow, neon, screens, glow that switches on with power |
| 04 | [FX lights](04_fx_lights.md) | flickering or pulsing light, halos around bulbs, lens flares, god rays, which stock effects are safe to use |
| 05 | [Sun, sky, exposure and fog](05_sun_sky_exposure_fog.md) | sunsets, night, keeping the map dark without the camera brightening it, fog and colour grading |
| 06 | [Reflections and probes](06_reflections_probes.md) | reflections, shiny or wet floors, why reflections smear, the ambient light on players and zombies |
| 07 | [Water](07_water.md) | how to make water, how it looks and reflects, wading and swimming, puddles, rain-slick streets |
| 08 | [Fixture cookbook](08_fixture_cookbook.md) | step by step: ceiling light, hanging lamp, **street lamp**, sconce, neon, fire, alarm, window, god ray, the power-on reveal |
| 09 | [Design and inspiration](09_design_and_inspiration.md) | how to light a dark zombies map well, what makes **Glass Tower** look good, community tutorials |
| 10 | [Troubleshooting, limits, lessons, test plan](10_troubleshooting_limits_history.md) | "something looks wrong", hard limits and budgets, what this project already learned, the tests to run |

**Quick answers to the original questions**

| You asked | Short answer | Where |
|---|---|---|
| Is there only one kind of light? | No. There are placed light entities (omni bulbs and spot cones, area tubes, reflection-only fill lights), FX lights inside effects, the sun and sky, and glowing materials, which look lit but do not light things. | [01 §3](01_lights.md#3-every-kind-of-light), [03 §1](03_glow_and_perks.md#1-the-five-ways-an-object-lights-up) |
| Dimmer lights? | Lower `stops` (each −1 halves it), shrink the radius, use falloff; for "dim before power, bright after", place a dim twin and a bright twin at the same spot in different lighting states, as Treyarch does. | [01 §7](01_lights.md#7-how-to-make-a-dimmer-light-and-how-to-size-one) |
| Objects and perks that light up? | Glowing materials make the object look lit, and a real light or FX light lights the room around it. Perk glow is an effect played at power. | [03](03_glow_and_perks.md), [04](04_fx_lights.md) |
| Power lights up the whole tower? | A lighting state is global by design. Use states for a few map-wide moods; light floors one by one with exploders or FX lights driven by a progress clientfield. | [02 §14](02_power_and_states.md#14-architecture-choosing-a-mechanism) |
| Making it dark without issues? | Low light against a clamped exposure, a dim always-on wayfinding layer, zombies readable as silhouettes, dim or matte world materials, probes fitted to rooms. | [05 §9](05_sun_sky_exposure_fog.md#9-recipe-a-night--dark-map-that-stays-readable), [09](09_design_and_inspiration.md) |
| A lamp / a street lamp? | Model + glowing lens + a spot light that lights the ground + a tiny bulb glow + a reflection-only fill + a switch. Full walkthrough with Treyarch's numbers. | [08 §2-3](08_fixture_cookbook.md#3-street-lamp-the-full-walkthrough) |
| Reflections? | Reflection probes provide reflections and bounce light; fit each box to its room. | [06](06_reflections_probes.md) |
| Water? | A water material for the look, a water clip brush to wade or swim, an underwater grade box. Four stock water materials to copy. | [07](07_water.md) |
| Glass Tower? | Almost certainly *GLASS TOWER[HARD]* by vuflub_ (Workshop 3801980290). Its look comes mostly from a low-sun sunset/space sky, mirror-like floors and water reflecting it, and neon edge trim with bloom, not from many placed lights. Please confirm it is the right map. | [09 §4](09_design_and_inspiration.md#4-glass-tower) |
| Sunsets? | A low, warm sun (SSI pitch/colour), a sunset sky image lined up with it, sun and sky light close in strength, horizon-matched fog, exposure clamped around the sky. Treyarch ships `default_sunset` to start from. | [05 §8](05_sun_sky_exposure_fog.md#8-recipe-a-sunset) |

## How light gets into a BO3 map (the whole picture on one page)

A map's picture comes from **five kinds of light** and **one camera setting**:

1. **The sun and the sky.** One `volume_sun` box around the whole map holds the
   global lighting. It names which **SSI** is used: the sun settings asset (sun
   colour, angle and strength, exposure limits, skybox). It also holds a "global
   probe" that lights every place no local probe covers. The sky image is itself a
   light source: its material's `skyStops` sets how much light the sky throws onto
   the world. Chapter 05.
2. **Light entities.** These are invisible Radiant `light` entities: an omni is a
   bulb shining in every direction, a spot is a cone. The lamp you *see* is a separate
   model; the light entity is what lights the room. Brightness is `stops`, a doubling
   scale where +1 stop is twice as bright. Chapter 01.
3. **Reflection probes.** Baked cubes that provide BOTH the reflections on shiny
   surfaces AND the soft bounced "ambient" light. Treyarch's own talk indicates this
   baked light also reaches players, zombies and the gun in your hands [INFERRED for
   our map]. A probe's box decides where it applies. Chapter 06.
4. **FX lights.** A light inside a particle effect. It exists only at runtime, can
   flicker, pulse and move, and casts no baked shadow. This project's perk-machine
   pools and the Rampage Inducer's pulse work this way. Chapter 04.
5. **Emissive (glowing) materials.** A surface that lights itself and blooms: neon,
   screens, the Tron-grid lines. **No doc or material setting shows a glowing surface
   lighting what is around it** (the sky is the one documented exception; a bake A/B
   would settle it), and **glow does not switch with the power** by itself. Chapter 03.

**The camera: exposure.** Like a real camera, the game decides how bright the final
picture is. Auto-exposure is clamped by `evmin`/`evmax`, set on the SSI, the worldspawn
or an exposure volume. A dark map is **low light against a clamped exposure**, not a
camera left free to adapt; an unclamped camera brightens the darkness back into grey
mud. Chapter 05.

**The switches.** Light can change during a match in several ways, and they do
different jobs (chapter 02):

| Switch | What it changes | Scope |
|---|---|---|
| Lighting state (`util::set_lighting_state`) | every placed light's on/off, the sun/sky SSI, the probe bake, state-flagged FX and volumes | the whole map at once; 4 states per map |
| Exploder (`exploder::exploder( "name" )`) | a named group of placed lights and FX | one group |
| FX light driven by a clientfield (our perk-glow pattern) | runtime light anywhere, flicker and pulses | anything; safe for players who join late |
| Glow switching (`lit_emissive_script` + shader constants, material override) | how a model's surface glows | one entity |
| Model swap (`_on` twin) | how an object looks | one entity |
| Fog / exposure / grade banks, vision | whole-screen mood per player | whole screen |

**Every change to lights, probes, the sun volume, the SSI or materials is a FULL build**
in this repo (the lighting bake runs only in a full build), and the user judges the result
in game.

## Golden rules

1. **A lamp is at least two things:** a model you can see and a light entity that
   lights the room. Add a glowing lens or bulb material and, where it earns its place,
   an FX halo or flicker and a reflection-only fill light. Treyarch builds every lamp
   this way. (01, 08)
2. **A lighting state is global.** A map has four, and switching one changes the whole
   map at once. That is why "the power lights up the whole tower". Use states for a few
   map-wide moods; use exploders or FX lights for anything local or progressive. (02)
3. **Script numbers are one lower than Radiant's.** `set_lighting_state( 0 )` shows
   Radiant **State 1**, and `set_lighting_state( 1 )` shows **State 2** [INFERRED,
   strongly supported by The Giant]. Stock `zm_usermap` boots every usermap in script
   state 1, which is **Radiant State 2**, and stock power never changes it. (02)
4. **Give the sun volume a real SSI for every state you use** (`ssi1` ... `ssi4`). An
   empty slot is written into the bake as Treyarch's daytime `default_day` sun
   [VERIFIED in the `.led`]. (02, 05)
5. **Glow is not light.** Pair any glowing surface that should light something with a
   real light. Set glow strength to about 2^EV of the area's exposure (EV 3 means HDR
   scale 8), and never leave the emissive map blank: a blank map glows **white** over
   the whole surface. (03)
6. **Probes light everything, so fit them.** Probe box sizes are *half*-sizes, and each
   box should reach its room's walls and floor. Point the sun volume's global probe
   (`target` → an `info_null`) at open, average-lit air, never inside a brush. (06, 05)
7. **Dark does not mean black.** Keep a dim, always-on wayfinding layer. Zombies must
   read as silhouettes, and players go where the light is. Visibility suffers once a
   place is about 2 stops below the scene exposure. Make darkness with light, not with
   black textures. (05, 09)
8. **Shadows cost.** Light shadows are opt-in, and the live budget is about 12 at the
   default resolution. Static (`shadowUpdate Never`) shadows are the cheap way to stop
   light leaking through walls. FX lights cannot have static shadows, so give them
   `PRIMARY_NOSHADOWMAP 1`. (01, 04)
9. **A looping FX light repeats at the same interval as its own lifetime.** A shorter
   interval stacks copies and builds up too bright. (04)
10. **Grade, bloom, LUT and performance volumes default to Radiant State 1 only.** A
    zombies map runs in State 2, so tick that state or the volume may do nothing
    [INFERRED]. (02, 05)
11. **Judge lighting on a low AND a high graphics setting,** comparing same-spot,
    same-state screenshots. Players can turn off volumetrics, dynamic shadows and SSAO,
    and the user's own config has them off. (09)
12. **New lighting assets for Tower II are map-owned** in the private workspace
    (`C:\BO3Tools\TOD2Cybercity`), never written into the shared Mod Tools root. Every
    lighting change is a full build, and the user tests it (CLAUDE.md, docs/154). (10)

## Tower of Doom II today: what the research found

This is a read-only audit of the generated map and its assets, taken on 2026-09-24.
Nothing was changed.

| Area | Today | What it means | Confidence |
|---|---|---|---|
| **The 344 lights** | Every one comes from `light()` in `tools/gen_tower_map.js`: omni, no shadows, client-side, `stops 6`, radius 200-900. The lighting states are `(0,1,1,1)`: off in Radiant State 1, on in 2-4. Brightness is tuned with `bake_intensity_scale`, which the entity definition describes as a bounce-bake control. | The map boots in Radiant State 2 and no Tower II script ever changes it, so **every light is on from spawn**. | Facts [VERIFIED]; the consequence [INFERRED], settled by test T1 |
| **Power** | THE FALL (docs/160_the_fall.md) turns the power on in the first seconds, and stock power changes no lighting anyway. | There is **no power-on lighting moment today**. The perk machines' `_on` models and glow FX are the only things that "switch on", and they do it at the start. | [VERIFIED] code |
| **The sun volume** | Only `ssi1 = tod_ssi_cybercity` is set; `ssi2..4` are empty. The compiled `.led` pairs Radiant State 2, the state the game runs in, with **`default_day`**: a warm, bright daytime sun (stops 14, colour `1 0.976 0.949`, exposure 1-16). | Either the map runs State 2 on `default_day` sun and exposure settings, or State 2 misbehaves without its own SSI. The one SSI this map authors sits in a state it never enters. | Data [VERIFIED]; runtime [TEST] (T2) |
| **The global probe** | The sun volume has no `target`, so its global probe sits at the box centre (0, 0, 19,478), **inside the mast brush**. All three stock sun volumes target an `info_null`. | Treyarch's doc warns that a buried global probe changes the bounce colour. This is a strong candidate for the unexplained "yellow tower" of docs/107. | Location [VERIFIED]; effect [TEST] (T3) |
| **Reflection probes** | 53 probes, all the Radiant default: a 144-unit cube (the 72 is a half-size). Each also writes `radius 2048`, which is not a probe key. No box reaches its floor. | Nearly every surface, player and zombie takes its bounce light and reflections from the coarse global probe, which smears reflections. The Giant fits 176 probes to its rooms. | Data [VERIFIED]; effect [INFERRED] |
| **The world's materials** | All ~66,400 visible brush faces use glowing (emissive) materials. About half glow only on thin grid lines; about half have a dim ~0.2 grey fill that glows over the whole face. They are also white-albedo mirrors (`reflectionProbeAmount 1`). | The tower lights itself regardless of lights or power. Darkness needs material changes, not only light changes, and world brush faces cannot switch their glow at runtime. | [VERIFIED] |
| **Sky and exposure** | The SSI copies stock `default_night` (exposure EV 3 to 3.5). The sky material's `skyStops` is 10, against 4.4 on `default_night`'s own sky. The worldspawn sets no exposure keys. Fog is off in the tower. | The sky is a strong ambient source for an open-air tower. | Values [VERIFIED]; look [INFERRED] |
| **Perk glow and the inducer** | Clientfield plus client FX with one dynamic light each (proven in this project). The FX loop every 200 ms with a 1000 ms life, so several copies overlap. | Works, but part of its brightness is stacking; matching the loop to the lifetime means re-tuning brightness. | [VERIFIED] timing |
| **Two blank effects** | The zone carries `env/light/fx_light_god_rays_dust_motes` (used as the lounge motes) and `zombie/fx_thundergun_smoke_cloud`. Both resolve to placeholder stub files in the local FX library. | Per this project's own record, stubs pack as blank effects. | Files [VERIFIED]; render [TEST] (T9) |
| **Old records** | docs/107, a generator comment (~line 1546) and the v17.80 CHANGELOG entry call `lightingstate1 0` "authored OFF before power". | That reading is contradicted by the stock evidence: the game never enters Radiant State 1. Details in [10 §6](10_troubleshooting_limits_history.md#6-records-this-reference-contradicts). | [INFERRED], strong |

## Recommended plan (for the user to decide)

> **2026-09-24, later the same day:** Step 0 and Step 1 are BUILT into the map
> behind three generator switches, all ON (`LIGHT_TEST_T1`, `SUN_SSI2`,
> `SUN_PROBE_TARGET` in `tools/gen_tower_map.js`; the `[TOD_LIGHTSTATE]` log in
> `_tod_fall.gsc`). docs/160 §10.5 and the result log in [10 §7.4](10_troubleshooting_limits_history.md#74-result-log)
> carry the record; the user's screenshots decide the rest of this plan.
>
> **2026-09-24, later:** the user chose the target (near-black with pools of
> light, edge lines only, a darker sky, crown hall first) and docs/164 executed
> items 5, 8 and 9's sky half for the crown hall: matte plain-grid clones on the
> hall's faces, nine pools instead of even coverage, the sky one stop dimmer and
> its bake light four stops lower. Unplayed as written; the shot list is
> docs/164 §5.

**Step 0: settle what the game really shows (three small builds).** Test T1 adds two
coloured test lights at the crown-hall spawn, one lit only in Radiant State 1 and one
only in State 2, plus a dev log of each player's lighting state. T2 adds `ssi2` to the
sun volume. T3 points the global probe at open air. Each is one change behind a test
switch that ships OFF, built through Tower II's own guarded pipeline. The user compares
same-spot screenshots. This answers the numbering question, the empty-`ssi2` question,
whether our lights render at all, and the likely yellow-tower cause. Full procedure:
[10 §7](10_troubleshooting_limits_history.md#7-open-questions-and-the-test-plan).

**Step 1: fix the sun volume.** Put a real SSI in every state the game uses, and target
the global probe at an `info_null` in open air. Compare with today's look before going
further.

**Step 2: decide where the "lights come on" moments are.** Under THE FALL the power is on
from the start, so a classic power-on reveal needs either the power decision reversed
(docs/160_the_fall.md §6 lists it as reversible) or a different trigger. The descent
has natural beats: the Fall gate's seal, doors opening downward floor by floor, and
the Undercity at the bottom. Whatever the trigger, pick one lighting-state convention
(the recommended one is The Giant's: the boot state is "off", and one
`set_lighting_state( 0 )` call switches to "on") and write it into the generator as
named light classes: a dim **always-on** wayfinding layer; **dim/bright twins** at the
same spots about 1-2 stops apart; and **"on"-only** accents. (02 §14)

**Step 3: light the tower progressively, not all at once.** Fifty floors cannot share
four states. Keep any global state for the one big beat, and light each floor or lounge
as the party reaches it: FX lights on client-spawned hosts, or grouped exploders, driven
by one world clientfield that counts lit floors. That makes it safe for players who join
late, and it spends no server entities. (02 §14.2, 04, 08 §17)

**Step 4: tame the glowing world.** Move structure to dim or non-glowing variants
(map-owned clones), and keep strong glow for accent trims and fixtures. Glow that should
switch on belongs on models (`_on` twins or script-driven glow materials), not world
brushes. (03)

**Step 5: fit the probes.** One per room, lap segment and lounge, with boxes sized to the
walls and reaching the floor, reflection planes where rooms are boxy, and the dead
`radius` key dropped. (06 §15)

**Step 6: set the darkness deliberately.** Lower the sky's light (`skyStops` or the sky
gain), clamp exposure (per state if the moods differ), and keep the sun far below the
sky or off. (05 §9)

**Step 7: build fixtures from the cookbook.** Street lamps, sconces, neon, alarm and
status lights, lit windows. Keep new lit geometry small, because the lighting bake has a
ceiling. (08, 10 §3)

**Step 8: small fixes.** Match the perk-glow and inducer FX loop interval to its lifetime
(then re-tune brightness), and replace the two stub effects. (04)

**Decisions only the user can make:** where the "lights come on" beats go under THE FALL
(or whether to reverse its power-at-start); which state convention to use; how dark each
area should be; whether to use fog in dark areas; how far the emissive world should be
dimmed; and whether a sunset (the Glass Tower look) belongs anywhere in a dark map.

## Glossary

| Term | Meaning |
|---|---|
| **stops** | Light brightness on a doubling scale: +1 stop = 2× the light. Also used for exposure and the sky. |
| **EV / exposure** | The camera's brightness setting. A higher EV applied to the same scene renders it darker. |
| **SSI** | Sun settings asset: sun colour, angle and strength, exposure clamps, skybox. One per lighting state on the sun volume. |
| **volume_sun** | The map-wide box that holds the global lighting and the global probe. |
| **lighting state** | One of 4 global lighting setups. Lights, FX entities and some volumes are flagged per state. |
| **Radiant State N / script state n** | Radiant's numbering 1-4 against the script call's 0-3; script state n shows Radiant State n+1. |
| **exploder** | A named group of placed lights and FX that script turns on and off. |
| **reflection probe** | A baked cube that gives reflections and bounced ambient light inside its box. |
| **global probe** | The sun volume's probe; it lights everything outside all probe boxes. |
| **emissive** | A material that glows by itself. |
| **HDR Scale (`scaleRGB`)** | An emissive material's glow strength; about 2^EV of the area. |
| **backlit / lampshade material** | A material that glows from a real light placed behind it, so it switches with that light. |
| **FX light** | A dynamic light inside a particle effect (a `dynamicLight2` element). |
| **PROBE_ONLY light** | A light only the probe bake sees: it adds coloured reflection and bounce without a direct pool. |
| **cookie / gobo** | A texture projected through a light: window bars, leaves, caustics, IES patterns. |
| **LED** | The lighting bake file Radiant writes (`.led`), consumed by the linker. |
| **clientfield** | A server-to-client value used to trigger client effects safely for players who join late. |

## Where the evidence lives

- Official Treyarch documents: `docs_modtools/` under the Mod Tools root
  (Lighting_Parameters, SunSky_Light_SetUp, FX_Lights, Materials, Lighting_Probe_Workflow,
  Probe/*.pdf, bo3_scriptapifunctions.htm, PhysicallyBasedRendering.pptx).
- Entity and asset definitions: `bin/t7.def.json` and `deffiles/*.awi` under the Mod Tools root.
- Treyarch's zombies lighting example: `map_source/_prefabs/zm/zm_giant/zm_giant_light.map`
  (543 lights, 176 probes, 96 FX) and `share/raw/scripts/zm/zm_giant*.gsc|csc`.
- Stock usermap boot and power: `share/raw/scripts/zm/zm_usermap.gsc:110`,
  `shared/util_shared.gsc` (`set_lighting_state`), `zm/_zm_power.gsc`.
- This project: `tools/gen_tower_map.js` (`light()`, `probe()`, `volume_sun`), docs/104,
  docs/107, docs/150, docs/155, docs/160_the_fall.md, docs/BO3_MAPMAKING_KB.md; Map One's docs/20.
- Each chapter ends with its own source list.
