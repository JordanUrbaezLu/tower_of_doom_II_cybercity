# 05 — Sun, sky, exposure, fog and colour — sunsets and dark maps

**In short.** The settings in this chapter apply to the whole map at once. One `volume_sun` box holds the sun and the sky light. It is also the "global probe" that supplies bounce light and reflections wherever no local probe reaches. Each lighting state names an SSI asset, which sets the sun's colour, angle and strength and clamps the camera's auto-exposure. The sky material's `skyStops` sets how much light the sky picture throws onto the world. Fog, the LUT and the vision file then grade what the camera sees. Whether a map reads **dark** depends on the **gap** between the light sources and the exposure, not on the light values alone: a dark map needs its exposure clamped so the camera cannot brighten it back up. Treyarch shipped real night, zombies and sunset SSIs (`default_night`, `zm_factory`, `zm_zod`, `default_sunset`) that are the best starting points. Tower of Doom II today runs a stock `default_night` clone, but its sky material's light gain (`skyStops 10`) is about 5.6 stops above the stock night sky's (4.4). It fills only `ssi1`, although the game probably runs in Radiant State 2, and its global probe is buried inside the mast. Settle those three before any fine lighting work.

**Read this when…** you want to change how bright or what colour the whole map is, build a sunset or a night, stop the camera brightening your dark rooms, add fog or a colour grade, or chase a colour cast that survives every light change.

**Contents**
1. [The mental model: what lights a frame](#1-the-mental-model-what-lights-a-frame)
2. [The sun volume (`volume_sun`)](#2-the-sun-volume-volume_sun)
3. [The SSI asset (sun settings)](#3-the-ssi-asset-sun-settings)
4. [The sky: picture and light](#4-the-sky-picture-and-light)
5. [Exposure](#5-exposure)
6. [Fog](#6-fog)
7. [Colour: LUT, grade boxes, bloom, vision](#7-colour-lut-grade-boxes-bloom-vision)
8. [Recipe: a sunset](#8-recipe-a-sunset)
9. [Recipe: a night / dark map that stays readable](#9-recipe-a-night--dark-map-that-stays-readable)
10. [Power-on: the global side](#10-power-on-the-global-side)
11. [Tower of Doom II: facts and history](#11-tower-of-doom-ii-facts-and-history)
12. [Open questions and in-game tests](#12-open-questions-and-in-game-tests)
13. [For Tower of Doom II](#for-tower-of-doom-ii)
14. [Sources](#sources)

Terms used in this chapter: **Radiant State N** is the light/volume key `lightingstateN` or `LIGHTSTATE_N` (N = 1..4, what Radiant shows). **Script state n** is the argument of `util::set_lighting_state(n)`. Script state n shows Radiant State n+1 [INFERRED] (strongly supported; full evidence in [02 — power and states](02_power_and_states.md)). Paths under the Mod Tools root are written relative to it; the root is called MODTOOLS (`C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`). Nothing in this chapter was tested in game.

---

## 1. The mental model: what lights a frame

A BO3 frame is lit by four layers, then photographed by an auto-exposing camera, then colour graded.

| Layer | Plain meaning | Where it is set | Chapter |
|---|---|---|---|
| **Sun** | One directional light for the whole map (can be switched off) | the SSI asset: `enablesun`, `colorSRGB`, `pitch`, `yaw`, `stops` | this one, §3 |
| **Sky light** | "a spherical light projected into the scene using the sky texture for value and color" [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf p.2) | the sky **material**: `skyStops`, `skyRotation` | this one, §4 |
| **Local light** | light entities, emissive materials, FX lights | Radiant, APE | [01](01_lights.md), [03](03_glow_and_perks.md), [04](04_fx_lights.md) |
| **Bounce + reflections** | local reflection probes plus the global probe that every `volume_sun` creates | probes, `volume_sun` | [06](06_reflections_probes.md), §2.4 here |
| **Camera exposure** | how bright the camera makes the scene: it picks an EV, shifted by `evcmp` and held inside `evmin..evmax` (which is applied first is unverified, §5.5) | SSI, worldspawn, `volume_exposure` | §5 |
| **Post** | LUT colour cube, position-based grade boxes, the map-name `.vision` file, bloom | worldspawn `lutmaterial`, `pbg_box`, `vision/` | §7 |

**Units: stops.** Light strength is measured in stops. One stop is a factor of 2, so +1 stop doubles the light and −1 stop halves it. A light's `stops` "Controls the starting intensity of a light. Lighting units are in stops. Default Value: 11" [VERIFIED] (src: docs_modtools/Lighting_Parameters.pdf p.1). SSI `stops` defaults to 15 (range −32..32), and sky `skyStops` defaults to 3 [VERIFIED] (src: deffiles/ssi.awi; deffiles/material.awi:633). The Materials doc turns an exposure value into a linear brightness as 2^EV: "an interior at EV 3 … two to the third power … gives us 8" [VERIFIED] (src: docs_modtools/Materials.pdf p.18).

**Why "dark" is relative.** Picture a Der Riese-style room lit by one hanging lamp. If the camera may adapt freely, it raises its sensitivity until the dark corners look grey, and the room reads flat. If the exposure is clamped, the lamp pool stays bright and the corners stay dark. A dark map therefore needs two things: (1) an exposure clamp the camera cannot escape, and (2) sun and sky light many stops below that exposure, with local lights near or above it [INFERRED] (from the stock night SSIs in §3.3 and the MP doc's exposure text in §5.6).

---

## 2. The sun volume (`volume_sun`)

### 2.1 What it is

The sun volume is a large invisible box brush (tool material `sun_volume`) drawn around the whole playable space. It has three jobs:

- It **contains the global lighting**: "The Sun Volume is a Global Reflection Probe. A Sun Volume is an object you place in the scene and use the shape to define where the Global Lighting is contained. A Sun Volume will contain the sun and sky lights that you define in APE." [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf p.1)
- It **creates the global probe**, the fallback source of bounce light and reflections (§2.4).
- It **holds the four lighting states**: one SSI slot per state (§2.5).

### 2.2 Every key

Source: MODTOOLS/bin/t7.def.json, class `volume_sun` [VERIFIED].

| Key | Type / range / default | Meaning (def text in quotes) |
|---|---|---|
| `ssi1` … `ssi4` | SSI name; `ssi1` = `default_day`, `ssi2..4` = empty | "Name of .ssi file to use for sun settings", grouped "Light State 1..4". "ssi is what will bake into the reflection probes" (SunSky p.1) |
| `ssi1_runtime_override` … `ssi4_runtime_override` | SSI name, empty | "ssi_runtime_override is what will be displayed in game" (SunSky p.1) |
| `override_reflections` | bool, false | "Use the run-time override SSI in the reflection probe final renders." |
| `grid_density` | enum 4, 8 … 64 (steps of 4), default 32 | "number of probe points in each dimension" of the global probe grid; "This resolution is based on the size of the Sun Volume not world units" (SunSky p.1) |
| `global_fill_color` | colour, `0 0 0` | "Occluded parts of the global probe will be filled with this color. Should match the average ground color." |
| `global_fill_intensity` | 0..30, 1.0 | "The global fill color will be multiplied by this value for an HDR result." |
| `shadowSplitDistance` | 100..5000 inches, 2000 | "Distance in inches that the split shadows (dynamics) render cover" |
| `shadowBiasScale` | −10..10, 1 | "Scale applied to shadow biasing (can be negative)" |
| `shadowVistaDetail` | 0.01..1, 1 | "Detail of vista shadows. Lower values drops fine details but saves space." |
| `shadowHiQualityContact` | bool, false | "Improves contact shadow quality but increases the size of the bake" |
| `transitionTime` | float, 0 | "Time to transition between sun states." |
| `streamLighting` | bool, true | "Stream the lighting data for this volume"; the doc: toggle it "to keep this Sun Volume always in memory … to avoid popping when the camera is moving across Sun Volumes" (SunSky p.1) |
| `respectLightLods` | bool, true | "When this is false, lights will never LOD out in probe bounce and reflections." |
| `previewShadows` | bool, false, hidden | "Preview quality shadows" |
| `min_occlusion` | float 0, hidden | "Obsolete". The older Reflection_Probes.pdf p.6 still describes a "minimum occlusion parameter" that "will prevent unlit and fully occluded areas from going completely dark". Treat it as retired; `global_fill_color` is the current control for occluded areas [INFERRED]. |
| `target` | string | points at an entity (stock: an `info_null`) that **positions the global probe** (§2.4) |

Keys seen in data but not in the def: `shadowSplitCount` (The Giant 2, mp_sector and mp_combine 3; effect unverified) [VERIFIED] (presence) (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map; _prefabs/mp/mp_sector/mp_sector_light.map). Also a bare `ssi` key, which the Mod Tools template and our generator write. Radiant shows it under "User-Defined", and it is probably ignored on the volume [INFERRED] (src: bin/t7.def.json; SunSky_Light_SetUp.pdf screenshot).

### 2.3 Limits

- **A plain box.** "Sun Volume cannot be rotated. Sun Volume cannot be cut or split. It must be a box with six sides. Sun Volume cannot overlap other Sun Volumes." [VERIFIED] (src: SunSky_Light_SetUp.pdf p.4)
- **Several sun volumes are allowed** as long as they do not overlap. The community dark map zm_alien_isolation uses three, one of them with separate spawn / lights-out / power-on SSIs [COMMUNITY] (src: https://github.com/MattFiler/zm_alien_isolation). A `volume_sun_extension` class exists in the def, but no stock map source uses it [VERIFIED] (absence) (src: bin/t7.def.json; grep of MODTOOLS/map_source).
- **The grid is relative to the box size.** `grid_density` is a fixed number of points per axis spread over the box, so a bigger volume gets **coarser** global-probe cells, not more of them [VERIFIED] (wording, SunSky p.1). "The grid density does not affect performance but it does eat more memory" [VERIFIED] (src: Lighting_Probe_Workflow.pdf p.3). Example: Tower II's volume is 24,448 × 24,448 × 40,044 units at density 32, so each cell is about 764 × 764 × 1,251 units [INFERRED] (arithmetic).
- **Radiant messages** that show the limits exist: `LEVEL CONTAINS NO SUN VOLUME LIGHTING CANNOT BE PROCESSED`, `Sun volume contains %u lights, max %u supported.`, `Sun FAILED needs more than %d MB`, `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE`, `NO BAKE STATE %d using %d` [VERIFIED] (strings); meanings [INFERRED] from wording (src: bin/Radiant_modtools.exe string scan). The light cap per volume is unknown. The Giant's one sun volume holds 543 lights and Tower II's 344, so the cap is at least 543 [INFERRED].

### 2.4 The global probe and `target`

**Plain version.** Imagine a chrome ball floating at one point in the map, photographing the world in every direction. Everywhere a local reflection probe does not cover, surfaces take their bounce light and their reflections from that one photo, shaded by a coarse 3D occlusion grid. If the ball sits inside a wall, it photographs the inside of a wall.

**What the docs say** [VERIFIED] (src: docs_modtools/Lighting_Probe_Workflow.pdf p.1-2; Probe/Reflection_Probes.pdf p.6):
- "When you create a sun-volume a global probe is created at the center of the sun-volume. All reflections and bounce lighting are generated from this global probe unless you override areas with a local probe."
- "If you do not like the location of the global probe you can move it by targeting another object. In the example below the sun volume is targeting an info_null. I have placed a chrome sphere next to it."
- "Its very important to place the global probe in an ideal average location for each sun-volume … Problems can occur when the global probe's position is buried inside of geometry or at too high of an altitude. You can see in my example how the bounce color is very very different."
- "The global probe only blends in outside of the attenuation range of all other probes." "The global probe provides ambient lighting based on how visible the sky is to surfaces."
- "The global probe doesn't quite look as good as the local probes so we try to avoid using it at close distances unless you're in a very non-shiny environment, like an open field." (Lighting_Probe_Workflow p.1)

**Stock practice.** All three stock sun volumes target an `info_null` [VERIFIED] (src: zm_giant_light.map; mp_sector_light.map; mp_combine_light.map). mp_combine's `volume_sun` is an exact copy of mp_sector's (same keys, same `target`), so there are really two Treyarch setups to learn from. The Giant's is `target auto11353318`, an `info_null` at prefab coordinates (−131, 49.5, 1812.5) with a `test_sphere_silver` chrome ball beside it [VERIFIED]. The light prefab is stamped into `zm_giant.map` at (−1048, −696, −1103), which puts the probe near z 710 in the level, in open air above the play area [INFERRED] (arithmetic; the play-area height was not measured). mp_sector's targets `auto3`, an `info_null` at prefab coordinates (2848, 76, −205) [VERIFIED].

**A community case.** One mapper found that "when I go outside a reflection probe the whole lighting becomes super bright". The sun volume's centre was inside a building, and enlarging the sun volume in one direction fixed it [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3307.html).

**How to place it (recipe).**
1. Put an `info_null` with a `targetname` in open air at an "average" spot for the lighting: never inside a brush, never at an extreme height.
2. Give the `volume_sun` the key `target` with that name.
3. Optionally put a small chrome sphere model beside it and look at its reflection in Radiant.
4. Re-bake (full build in this repo) and compare same-spot screenshots against the old build.

**`global_fill_color`** defaults to black. It fills the *occluded* parts of the global probe, and the def says it "should match the average ground color" [VERIFIED]. Treyarch does not follow that advice in the shipped data: The Giant, mp_sector and mp_combine all write `global_fill_color "0 0 0"` explicitly, and so does Map One [VERIFIED] (src: each file's `volume_sun`). Pure-black pockets in occluded corners are a plausible result of the black default [INFERRED]. For a dark map, a dark colour near the average ground colour is the documented choice, but whether it improves anything here is untested [TEST]: change it as an A/B, not as a known fix.

Probes, their boxes and the brightness correction are in [06 — the global probe](06_reflections_probes.md#8-the-global-probe). One point matters here: Treyarch's 2016 GI talk describes one probe-grid lighting system built as an alternative to lightmaps so that the same indirect light also applies to moving objects and effects [VERIFIED] (talk abstract). Applying that to players, zombies and the viewmodel is an [INFERRED] reading of it, so what the global probe captures may colour them too (src: https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf; see [06 §2.1](06_reflections_probes.md#21-what-lights-a-moving-object-player-zombie-viewmodel-script-model-fx)).

### 2.5 Lighting states on the sun volume

"You can have up to 4 lighting states (additional Global Lighting scenarios) that can be accessed & switched through script during run time. Each lighting state has runtime lighting and an optional baked lighting override." [VERIFIED] (src: SunSky_Light_SetUp.pdf p.1)

| Setting | Effect |
|---|---|
| `ssiN` only | used for the bake (GI and probes); presumably also what is displayed [INFERRED] |
| `ssiN` + `ssiN_runtime_override` | `ssiN` bakes the GI and probes; the override is "what will show up in game" [VERIFIED] (SunSky p.16-17) |
| + `override_reflections 1` | probe reflection renders use the runtime SSI instead of `ssiN` [VERIFIED] (def text) |
| `transitionTime` | "Time to transition between sun states" [VERIFIED] (def); whether it smooths a script state change in a usermap is [TEST] |

**What happens when a state has no SSI** is not documented. The facts:
- The def default is `ssi1 = default_day` and `ssi2..4` empty [VERIFIED].
- Radiant carries `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE` and `NO BAKE STATE %d using %d` [VERIFIED] (strings).
- Every compiled `.led` lists one SSI per state, and unset slots are exported as `default_day` [VERIFIED] (byte scan):
  - Tower II: `tod_ssi_cybercity`, then `default_day` ×3 (src: C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.led);
  - The Giant: `zm_factory` ×2, then `default_day` ×2 (src: MODTOOLS/share/raw/maps/zm/zm_giant.led);
  - Map One: `acc_ssi_night_dim80` ×2, then `default_day` ×2 (src: MODTOOLS/share/raw/maps/zm/zm_abandoned_cyber_city.led);
  - mp_sector: `mp_sector_override`, then `default_day` ×3 (src: MODTOOLS/share/raw/maps/mp/mp_sector.led). The runtime-override name is what gets recorded when one is set [INFERRED] (from this one case).
- Community threads report that state switches did nothing until the sun volume had an SSI for that state [COMMUNITY] (src: IceGrenade wiki https://github.com/IceGrenade/bo3/blob/master/wiki/lightstates "give it an ssi 2"; modme/Steam threads cited in [02 §5](02_power_and_states.md#5-the-sun-volume-in-each-state)). In one of them the fix was the same SSI (`zm_factory`) in `ssi1` and `ssi2`, not a different one per state [COMMUNITY].
- Counter-evidence: the installed ZM and MP templates and `mp_sector_light.map` set `ssi1` only [VERIFIED]. TOD1 shipped with `ssi1` only, and project records describe light visible at light positions [COMMUNITY] (project record, docs/107). So "a state only works with its own SSI" stays [COMMUNITY]/[INFERRED].

**Working rule.** Fill **every state you use** with a real SSI, not `default_day`. Using the same SSI in several states is fine: The Giant puts `zm_factory` in `ssi1` and `ssi2`, and Map One puts `acc_ssi_night_dim80` in `ssi1`, `ssi1_runtime_override` and `ssi2` [VERIFIED] (src: zm_giant_light.map; MODTOOLS/map_source/zm/zm_abandoned_cyber_city.map). Distinct `ssiN_runtime_override` values per state only matter if you use overrides: one mapper reports Radiant would not build lighting in a second state that reused the same override [COMMUNITY] (VerK0).

Whether each state given an SSI adds bake time or data size is **not established**. Radiant keeps probe irradiance, exposure and sun-shadow data per state [VERIFIED] (field names), but it also has skip/reuse paths (`NO BAKE STATE %d using %d`, `Active lighting state is no bake`) [VERIFIED] (strings); behaviour unknown.

### 2.6 Bake one look, display another (the override trick)

Treyarch's MP maps use the runtime override "to display a sun and sky intensity different from what is baked into the probes. Note that going to far with this can start to look bad as your reflections will not match the visible sky." Later on the same page: "it also makes since to add some compensation to the sun. This has varied from map to map but in general +1-2 stops of sun bake has produced a good look and has greatly increased player visibility." [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.2). The stock data mostly matches: 14 of the 15 stock override SSIs have a sun 0.5–2 stops dimmer than their bake SSI (`mp_sector` 13.3 bake vs 12.8 override). The exception is `mp_spire_override`, about 6 stops brighter (4.58 bake vs 10.75) [VERIFIED] (src: source_data/ssi.gdt). mp_sector also bakes from a different sky picture (`skybake_mp_sector_08_ll.exr`) from the one it displays (`skybox_mp_sector_08_ll.exr`) [VERIFIED] (src: model_export/t7_skybox.gdt).

The SunSky doc's own example is a colour case: "art direction would like a very saturated blue sky in game. This saturated sky will cause the level to look very blue when the GI is baked", so bake from a neutral `<name>_bake` SSI in `ssi1` and put the saturated look in `ssi1_runtime_override` [VERIFIED] (src: SunSky_Light_SetUp.pdf p.16-17).

**For a dark map** this is a readability lever: bake the bounce a little brighter than the sun you display, so shadows are not black while the direct light stays low [INFERRED].

### 2.7 Sun shadows

- `shadowSplitDistance` sets the reach of the **dynamic** sun shadow cascades. "Lower numbers = higher quality and a larger memory footprint. Be careful!" [VERIFIED] (src: SunSky_Light_SetUp.pdf p.1). The doc compares 2000 and 250 (p.14). Stock values: The Giant 900, mp_sector and mp_combine 1200, Map One 800 [VERIFIED]. No primary source says it raises bake cost. "Lower it to stop sun bleeding" is community advice only [COMMUNITY] (src: https://steamcommunity.com/app/455130/discussions/0/3424437779948829805/).
- It can be changed per player at runtime with `player SetSunShadowSplitDistance( dist )` (0 reverts) [VERIFIED] (API) or `util::set_sun_shadow_split_distance`, which `_globallogic_spawn.gsc:502` re-applies on every spawn [VERIFIED] (src: share/raw/scripts/shared/util_shared.gsc:3016).
- SSI `penumbra_inches` (0..8, default 1) sets sun-shadow softness; `dynamicShadow` enables dynamic sun shadows [VERIFIED] (src: deffiles/ssi.awi). `volume_performance` has a declared `sunShadowSplitCount` (0..3, default 3) [VERIFIED] (def).
- Players can switch dynamic sun shadows off. The user's own `players/config.ini` has `DisableDynamicSunShadows 1`, so the user's playtests will not show them [VERIFIED] (file).

### 2.8 Sun volumes compared

| Map | `ssi1` | `ssi1_runtime_override` | `ssi2` | `target` | split distance | grid |
|---|---|---|---|---|---|---|
| The Giant (Treyarch ZM prefab) | zm_factory | – | zm_factory | info_null | 900 | 32 |
| mp_sector (Treyarch MP prefab; mp_combine is identical) | mp_sector | mp_sector_override | – | info_null | 1200 | 64 |
| Mod Tools ZM template (`rex/templates/ZM Mod Level/…/template.map`, same in `map_source/zm/zm_test_map.map`) | default_day | – | – | – | 2000 | 32 |
| Map One (`zm_abandoned_cyber_city.map`) | acc_ssi_night_dim80 | acc_ssi_night_dim80 | acc_ssi_night_dim80 | – | 800 | 32 |
| Tower II (`map_source/zm/zm_tod2_cybercity.map`) | tod_ssi_cybercity | – | **empty** | – | 2000 | 32 |

(src: each file's `volume_sun`, parsed) [VERIFIED]

Tower II's `volume_sun` is the Mod Tools template's key set (`ssi`, `ssi1`, `grid_density 32`, `shadowBiasScale 1`, `shadowSplitDistance 2000`, `streamLighting 1`) with only the SSI name changed [VERIFIED]. The Treyarch-authored volumes add a `target`, a second state and a tighter split distance.

---

## 3. The SSI asset (sun settings)

### 3.1 Every field

Source: MODTOOLS/deffiles/ssi.awi [VERIFIED]. Everything from `colorSRGB` to `lensFlare` appears in the editor only while `enablesun` is ticked. `skyboxmodel` and the exposure fields sit outside that block, so they stay editable with the sun off; `zm_zod` (sun off) still sets them, which suggests they still apply [INFERRED].

| Field | Editor title | Default / range | Notes |
|---|---|---|---|
| `enablesun` | Enable the Sun | 1 | Shadows of Evil's `zm_zod` ships 0 |
| `colorSRGB` | Color | **0 0 0** | tooltip: "the default color is (0, 0, 0)". **A new SSI starts with a black sun.** Clone a stock SSI instead. |
| `pitch` | Pitch | 0, −180..180 | sun elevation (convention in §3.2) |
| `yaw` | Yaw | 0, 0..360 | sun direction |
| `lensFlarePitchOffset` / `lensFlareYawOffset` | | 0 (−180..180 / −360..360) | offsets the flare from the sun direction [INFERRED] (tooltip: "Controls the lens flare pitch offset") |
| `stops` | Stops | 15, −32..32 | sun intensity in stops |
| `spec_comp` | Specular Comp | 0, −14..14 | "Specular boost (in stops)" |
| `penumbra_inches` | Penumbra inches | 1, 0..8 | sun shadow softness |
| `dynamicShadow` | Enable dynamic shadows | 1 | |
| `sunCookieIntensity`, `sunCookieLightDefName`, `sunCookieScale`, `sunCookieAngle`, `sunCookieRotation`, `sunCookieOffsetX/Y`, `sunCookieScrollX/Y` | Sun Cookie … | 0 / empty | a gobo on the sun, e.g. moving cloud shadows (§4.6) |
| `sunVolumetricCookie` | Enable the Sun Volumetric Cookie | 0 | |
| `lensFlare` | Lens Flare | "" | GUID of a `.klf` lens flare |
| `skyboxmodel` | SkyBox Model | xmodel | the sky dome this SSI shows |
| `ev` | Ev (hidden, marked `// REMOVE`) | 0, 0..20 | "Controls the global exposure"; legacy, but stock SSIs still write it |
| `evcmp` | Ev Comp | 0, −32..31 | exposure compensation (§5) |
| `evmin` | Ev Min | −32 | "Sets the minimum exposure" |
| `evmax` | Ev Max | 31 | "Sets the maximum exposure" |
| `bounceCount` | Bounce Count | 4, 1..10 | "Controls the number of light bounces" in the bake |

`evmin −32 / evmax 31` means unclamped. Because each lighting state has its own SSI, **the SSI's `evmin`/`evmax`/`evcmp` is the practical per-state exposure control** [INFERRED] (the doc's per-state worldspawn keys are discussed in §5.3).

### 3.2 Pitch and yaw

`ssi.awi` only says "Controls the pitch" / "Controls the yaw". Stock data suggests **elevation above the horizon ≈ `pitch` when pitch ≤ 90, else `180 − pitch`** [INFERRED]. The evidence is loose [VERIFIED] (values) (src: source_data/ssi.gdt):
- the SSIs named for a low sun sit at 158–165 (`default_sunset` 158, `default_morning` 165, `cp_sh_singapore_safehouse_predawn` 165), and several orange-sunned ones at 169–174 or at 18–25 (`cp_mi_cairo_infection_intro` 169, `cp_mi_sing_vengeance` 18, `cp_mi_cairo_aquifer` 20);
- `default_day` sits at 125 and most day and MP SSIs at 125–150;
- there are exceptions: `mobile_safehouse_twilight` is pitch 125 with a neutral colour, and some warm suns sit at 125–145 (`mp_freerun_04` 125, `cp_mi_cairo_ramses_3` 145).

Check the convention in Radiant before relying on it: set pitch 10 and then 170 at the same yaw and compare shadow direction and length [TEST].

### 3.3 Stock reference SSIs

All values from MODTOOLS/source_data/ssi.gdt (93 SSIs) and the paired sky materials in model_export/t7_skybox.gdt and t7_techart_props.gdt [VERIFIED].

**Night and dark**

| SSI | sun | colorSRGB | pitch / yaw | sun stops | evcmp | evmin..evmax | sky / skyStops |
|---|---|---|---|---|---|---|---|
| `default_night` | on | 0.79 1 1 (cool cyan) | 130 / 140 | −2.2 | 2.5 | 3..3.5 | skybox_default_night / 4.4 |
| `zm_factory` (The Giant) | on | 0.53 0.69 0.69 | 130 / 120 | −2 | 4 | 0.5..3.5 | skybox_zm_factory / 3 |
| `zm_zod` (Shadows of Evil) | **off** | 0.64 0.75 1 | 130 / 134 | −2.5 | 3 | 4..6 | skybox_zm_zod |
| `cp_infection_foy_cathedral_night` | on | 0.62 0.76 1 | 130 / 140 | 5 | 2 | 3..3.5 | |
| `cp_mi_sing_sgen_emergency` (its sky is named `…_pblack`, probably "pitch black" [INFERRED]) | off | ~0.003 grey | 80 / 0 | −2 | 0 | 3..4 | skybox_cp_mi_sing_sgen_pblack |

**Sunset, dawn and low sun**

| SSI | colorSRGB | pitch / yaw | sun stops | evcmp | evmin..evmax | sky / skyStops |
|---|---|---|---|---|---|---|
| `default_sunset` | 1 0.768 0.546 | 158 / 300 | 11 | 0 | 8..12.5 | skybox_default_sunset / 10.15 |
| `default_morning` | 1 0.894 0.741 | 165 / 263 | 11.3 | 0 | unclamped | skybox_default_day_clear_0700 / 10.1 |
| `cp_sh_singapore_safehouse_predawn` | 0.918 0.670 0.428 | 165 / 250 | 5 | 0 | 1..16 | |
| `cp_mi_cairo_infection_intro` | 1 0.570 0.310 | 169 / 85 | 7 | 0 | unclamped | |
| `cp_mi_sing_vengeance` | 0.882 0.441 0.225 | 18 / 250 | 1 | 0 | 6.5..10 | |
| `mp_spire` | 1 0.682 0.502 | 165 / 40 | 4.58 | 1 | 5.25..8 | |

**Day, for contrast**: `default_day` 1 0.976 0.949, 125 / 150, stops 14, EV 1..16, sky 13.5. `mp_sector` stops 13.3, EV 11.5..13, sky 13.

### 3.4 Community and project SSIs

| SSI | Where | Values | Note |
|---|---|---|---|
| `tod_ssi_cybercity` (Tower II) | `source_data/tod_skybox.gdt` | identical to `default_night` except `skyboxmodel skybox_tod_cybercity` | [VERIFIED] key-by-key |
| `acc_ssi_night_dim80` (Map One) | MODTOOLS/source_data/acc_ssi.gdt | `default_night` with stops −2.52 | −0.32 stop ≈ ×0.8, matching the name [INFERRED] (intent) |
| Nastian T9 pack (`t9_mp_miami` …, 16 SSIs) | MODTOOLS/source_data/acc_nastian_t9_skyboxes.gdt | evmin 5.5–8, evmax 12–14, ev 15 | a **daytime** clamp; docs/104 §1 warns against using it for a night map. The same GDT also carries Map One's `acc_ssi_miami_night` / `acc_ssi_dark_night`, which are `default_night` values with a T9 sky [VERIFIED] |
| `hb_ssi_hell` (Hellbound) | C:/BO3Tools/TOD2Cybercity/source_data/hb_skyboxes.gdt | 1 0.6 0.32, pitch 20, stops 1.5, EV 7..14 | a hellscape, not a night |

### 3.5 What Treyarch's numbers teach [INFERRED] (from §3.3)

- **Night** = a cool blue/cyan "moon" colour with the sun 5–7 stops **below** the sky light (default_night −2.2 vs sky 4.4; zm_factory −2 vs 3), or no sun at all (zm_zod). The night SSIs closest to zombies (default_night, zm_factory, zm_zod, and the campaign's cathedral night) clamp exposure narrow (0.5–3 stops wide) with a **positive** `evcmp` (+2..+4).
- Not every stock night does that: `cp_sh_cairo_night` locks exposure at 8..8 with `evcmp 0`, and `cp_sh_singapore_safehouse_night` leaves it at 1..16 with `evcmp 0`. So there are several working recipes; the zombies ones are the relevant ones for a zombies map.
- **Day and sunset** = the sun within about one stop of the sky light (sunset 11 vs 10.15; day 14 vs 13.5), with the exposure clamped around the sky stops minus 0–2.
- Nine stock SSIs **lock** exposure (`evmin = evmax`), two of them nights (`cp_sh_cairo_night` 8, `cp_mi_cairo_infection_bastogne_night` 13.25). A locked SSI makes the MP doc's "work with the exposure locked" permanent (§5.6).

---

## 4. The sky: picture and light

### 4.1 Plain version

The sky is two things at once. It is the **picture** you see behind the map, and it is a **light**: the engine wraps the picture around the world and uses its colours to light everything that can see the sky [VERIFIED] (SunSky p.2). So changing the sky picture can recolour the world even when no light entity changes. Tower of Doom saw exactly this: after a too-bright sky, "every wall, gun and zombie went olive-yellow" [COMMUNITY] (project record) (src: docs/104 §4; §11.2 here).

### 4.2 The asset chain

The doc names three sky assets (image, material, model) that are then "added to the SSI asset"; the SSI then goes into the `volume_sun`. All are made in APE [VERIFIED] (src: SunSky_Light_SetUp.pdf p.5-12 and its screenshots; model_export/t7_skybox.gdt):

1. **Image**: the sky `.exr`. Tutorial settings: Image Usage **HDR** (GDT `semantic HDR`), **compressed**, Image Type Texture, **Mipmap Disable** ticked, **Streamable** ticked. The stock sky images carry the same GDT values (`semantic HDR`, `compressionMethod compressed`, `noMipMaps 1`, `streamable 1`; `imageType Cube` for the cube-face skies), and so does ours [VERIFIED] (src: model_export/t7_skybox.gdt; source_data/tod_skybox.gdt). "In a real production you MUST MAKE A UNIQUE .exr FILE! … do not directly reference any other asset that is used in another map." [VERIFIED] (p.8)
2. **Material**: category Geometry. Type `sky_latlong_hdr` for a 2:1 equirectangular image, or `sky_hdr` for cube faces (stock `skybox_default_night`, `_default_black`, `_default_day_clear_0700`). Colour Map = the image. Keys `skySize`, `skyHalfSpace`, `skyRotation`, `skyStops`.
3. **Model**: a rigid xmodel whose LOD0 is the stock sky dome, with a material override. Every sky xmodel in the shipped GDTs (8 stock, 16 in the Nastian pack, and ours) uses `t6_props\vista\skybox\t6_skybox.xmodel_bin` with `skinOverride "mtl_skybox_default <your material>"` [VERIFIED] (src: model_export/t7_skybox.gdt; model_export/t7_techart_props.gdt; source_data/acc_nastian_t9_skyboxes.gdt; source_data/tod_skybox.gdt).
4. **SSI**: `skyboxmodel` = that xmodel. Then put the SSI in the `volume_sun` `ssi1` (and every other state you use).

Two project rules on this install:
- **Zone only the sky xmodel** (`xmodel,<sky model>`). A standalone `material,` line for a `sky_latlong_hdr` material failed the techset compile; the material and image ride in through the xmodel [COMMUNITY] (project record) (src: zone_source/zm_tod2_cybercity.zone:44-62; docs/104_cybercity_sky.md §1). Community notes that ask for `xmodel`, `material` and `image` lines do not hold here.
- **8192 × 4096 is the ceiling.** A 16384-wide EXR failed the linker with "unsupported size" [COMMUNITY] (project record: a failed build) (src: docs/104 §4g).

Our generator also writes worldspawn `skyboxmodel` and `ssi` (and `wsi default_night`) (src: tools/gen_tower_map.js:8693-8695). None of these three is a worldspawn key in `t7.def.json` [VERIFIED]. All three survive into the compiled `.d3dbsp` worldspawn (src: C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.d3dbsp) [VERIFIED], but the compiler copies worldspawn keys through, so that does not show that anything reads them. `cod2map64.exe` contains `skyboxmodel` only inside its list of SSI field names [VERIFIED] (string scan). Map One writes the same three keys; The Giant's worldspawn writes none of them [VERIFIED] (src: MODTOOLS/map_source/zm/zm_giant.map, zm_abandoned_cyber_city.map). So a stock map gets its sky from the SSI alone, and the worldspawn keys are probably a Mod Tools template habit [INFERRED]. The SSI carries its own `skyboxmodel`, so always change the sky model and the SSI **as a pair** (src: tools/gen_tower_map.js:1845-1893 comment).

### 4.3 The sky as a light: `skyStops` and `skyRotation`

"There are only two parameters to adjust for the sky light. skyRotation is used to rotate the sky around the up axis … Use skyRotation to line the sky up to the sun direction. skyStops is used to adjust the brightness of the sky light." [VERIFIED] (src: SunSky_Light_SetUp.pdf p.2-3)

**What needs a rebake.** "Most variables will live update to radiant. Some variables require that you rebake to see the result. These include: Pitch, Yaw, skyStops. Changing the Stops on the ssi & skyStops on the Sky Material will live update to Radiant but to see the effect of the bounced (GI) light you need to rebake." [VERIFIED] (src: SunSky_Light_SetUp.pdf p.14-15). In this repo every such change is a FULL build anyway, because `build_map.ps1` has no LED-only mode.

**Sky material keys** (src: deffiles/material.awi:632-640) [VERIFIED] (definitions):

| Key | Default | Status |
|---|---|---|
| `skyStops` | 3 (−32..32) | sky-light brightness, in stops |
| `skyRotation` | 0 (0..360) | turns the sky about the vertical axis |
| `skyScaleRGB` | 8 | **marked `// obsolete`** in material.awi. Stock values still range 0.75–9000. Project docs/104 §4 calls it a "display multiplier — never touch"; that is unverified. Leave it as the clone source has it. |
| `skySize` | 8000 | undocumented (probably the dome size) [INFERRED] |
| `skyFogFraction` | 1 (0..1) | undocumented (probably how much fog applies to the sky) [INFERRED] |
| `skyHalfSpace` | true | undocumented |
| `skyCenterX` / `skyCenterY` / `skyCenterZ` | 0 | undocumented; every stock sky material and ours write 0 [VERIFIED] |

**Stock sky materials** [VERIFIED] (src: model_export/t7_skybox.gdt, t7_techart_props.gdt):

| Sky material | Type | skyStops | skyRotation | skySize |
|---|---|---|---|---|
| `mtl_skybox_default_day` | sky_latlong_hdr | 13.5 | 75 | 65000 |
| `mtl_skybox_default_sunset` | sky_latlong_hdr | 10.15 | 110 | 65000 |
| `mtl_skybox_default_day_clear_0700` | sky_hdr (cube) | 10.1 | 0 | 8000 |
| `mtl_skybox_default_night` | sky_hdr (cube) | 4.4 | 70 | 8000 |
| `mtl_skybox_zm_factory` | sky_latlong_hdr | 3 | 85 | 2000 |
| `mtl_skybox_default_black` | sky_hdr | 0 | 0 | 8000 |
| `mtl_skybox_mp_sector` (bake) / `_override` (display) | sky_latlong_hdr | 13 / 13.5 | 236 | 65000 |
| `mtl_skybox_tod_cybercity` (ours) | sky_latlong_hdr | **10.0** | 0 | 8000 |

`skyStops` is only half the story: the light also depends on the picture's own brightness. The project measures a **sky-light score** = mean linear pixel × 2^skyStops, and the Nastian pack sits near 1.3 on it (src: docs/104 §4) [COMMUNITY] (project metric). Comparing `skyStops` values across different pictures is therefore only a gain comparison [INFERRED].

### 4.4 Dimming the visible sky only: `sky_intensity_factor`

Worldspawn `sky_intensity_angle0/1` (−90..90) and `sky_intensity_factor0/1` (0..10, default 1): "The game engine will use the player's view angle to interpolate between angle0 and angle1 … The sky box's color will be multiplied by this interpolated intensity factor." [VERIFIED] (src: bin/t7.def.json worldspawn). The text speaks of the sky box's **colour**, so this dims the sky you see, and probably not the sky light that lit the bake [INFERRED]. Map One ships 0.6 / 0.6; Tower II ships 1 / 1 [VERIFIED].

### 4.5 The sun lens flare

The SSI `lensFlare` field takes the GUID of a `.klf`. The only sun flare shipped in `share/raw/lensflares/` is `lf_sun_mp_sector.klf` (22 `.klf` files in total, the rest light-bulb and FX flares) [VERIFIED] (listing). `cp_mi_cairo_infection_intro` names a flare GUID that matches no shipped file [VERIFIED]. Community tips: add a flare temporarily to see where the SSI sun actually is, then line the sun up with the bright spot painted in the sky; keep flares off on a dark map [COMMUNITY] (VerK0; JBird632). Whether the MP flare links in a usermap is [TEST].

### 4.6 Sun cookies (moving cloud shadows)

The sun can take a gobo. Lighting_Parameters lists the sun-gobo keys with example values (`sunCookieIntensity [1.0]`, `sunCookieLightDefName [cookie_sun_mp_apartments]`, `sunCookieScale [0.001]`, `sunCookieScroll [0.1 0.1]`): "Sun Gobo material examples can be found in t7_light_gobo.gdt … These same sun gobo materials and parameters can be used on lights in game" [VERIFIED] (src: Lighting_Parameters.pdf p.11). A new SSI starts with `sunCookieIntensity 0` [VERIFIED] (ssi.awi), so expect no cookie until you raise it [INFERRED]. A community mapper duplicated a stock sunset SSI, set its cookie and used a scroll of about 0.05 ("0.25 is fairly fast") [COMMUNITY]. On a night map with the sun many stops down, a sun cookie has little light to shape [INFERRED].

---

## 5. Exposure

### 5.1 Plain version

The game camera works like a phone camera in auto mode. In a dark room it raises its sensitivity and the room looks brighter. Pointed at a bright sky, it lowers its sensitivity and the sky stops blowing out. BO3 describes that setting with an **exposure value (EV)**:

- EV numbers track **how bright the lit place is**: Treyarch's MP doc exposes a sunlit exterior at EV 12 and an interior at 11 or lower [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.3).
- So **raising the EV applied to a given scene renders it darker**, and lowering it renders it brighter [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.3; Materials.pdf p.18, where an emissive needs HDR scale 2^EV to read correctly at that EV). Never read "higher EV = brighter" as "raise EV to brighten the picture".
- In a dark area the camera wants a **low** EV (to brighten). `evmin` is the floor: if `evmin` is high, the camera cannot go low enough, and the dark area stays dark [INFERRED] (from the MP doc's "when looking out from the darkness the exposure will not dive down").
- In a bright area the camera wants a **high** EV. `evmax` is the ceiling: bright neon cannot be darkened past it [INFERRED].
- A narrow `evmin..evmax` (the stock zombies nights: 0.5–3 stops wide) is close to a **locked** exposure.

An illustration, not a measured case: picture a dark back room in a Kino-style map before power. An unclamped camera would push its EV down to lift the black corners toward grey. A night SSI with `evmin 3 / evmax 3.5` does not allow that, so the only bright things are what the lights and glowing surfaces make bright [INFERRED].

### 5.2 The three numbers

| Key | Meaning (official text) |
|---|---|
| `evmin` | "minimum global exposure value" / SSI: "Sets the minimum exposure" |
| `evmax` | "maximum global exposure value" / SSI: "Sets the maximum exposure" |
| `evcmp` | "global exposure compensation amount pushes the auto exposure target value up or down by the x number of stops" |
| `evauto [1]` | "set only in the worldspawn / This turns on the Auto Exposure in your map. Eventually this will be automatically set and go away" |
| `evmin1..4` / `evmax1..4` / `evcmp1..4` | "minimum exposure value of lighting state 1, 2, 3, or 4" / "maximum exposure value of …" / "exposure compensation value of …" |
| `feather [0.0]` | "feather the interior of an exposure volume by x number of radiant units" |

(src: Lighting_Parameters.pdf p.12, "AUTO EXPOSURE PARAMETERS") [VERIFIED] (text)

Status on this install:
- `evauto` and the per-state `evmin1..4 / evmax1..4 / evcmp1..4` appear in no def file and not in `cod2map64.exe`, `Radiant_modtools.exe` or `linker_modtools.exe` (ASCII and UTF-16 search) [VERIFIED] (absence). The game executable is packed and cannot be searched. Treat them as legacy, and use one SSI per state for per-state exposure [INFERRED]. Whether auto-exposure runs without `evauto 1` is [TEST]. The Giant sets it; Tower II and the Mod Tools template do not.
- `cod2map64.exe` contains `evmin`, `evmax` and `evcmp`, but only inside its list of SSI field names (next to `penumbra_inches`, `dynamicShadow`, `skyboxmodel`). It also prints `LIGHTING WORLDSPAWN: global exposure compensation EV:%.02f` [VERIFIED] (strings). So some worldspawn exposure value is reported, but the strings do not prove that the worldspawn keys `evmin/evmax/evcmp` are read [INFERRED]. The Giant's main worldspawn sets them (§5.4), which suggests Treyarch expected them to work [INFERRED].
- `feather` has become `blend_mins` / `blend_maxs` on `volume_exposure` (§5.3).

### 5.3 Where exposure is set

| Place | Keys | Notes |
|---|---|---|
| **The active SSI** (one per lighting state) | `evmin`, `evmax`, `evcmp` (+ hidden `ev`) | the practical per-state control (§3.1) |
| **Worldspawn** | `evmin`, `evmax`, `evcmp`, (`evauto`) | documented in Lighting_Parameters p.12 but undeclared in `t7.def.json`'s worldspawn; whether they are read is unproven (§5.2) [TEST] |
| **`volume_exposure`** (brush) | `evcmp` (−32..31, "Exposure compensation when auto exposure is enabled."), `evmin` / `evmax` ("Only used if not set to the default" −32 / 31), `blend_mins` / `blend_maxs` (fade distance per side), `priority` (highest wins), `AUTO_PRIORITY` (spawnflag 2048: "a volume completely inside another volume is higher priority"), `BANK_1..4` (spawnflags 1/2/4/8, BANK_1 on) | **No LIGHTSTATE flags**: it cannot follow a lighting state by itself. A volume with only `evcmp` shifts compensation and leaves the clamp alone. (src: bin/t7.def.json `volume_exposure`) [VERIFIED] |
| **Reflection probes** | `evcomp` "EV compensation to final probe exposure" | Treyarch: "avoid evcomp on probes. Pretend it doesn't exist" (src: Multiplayer_Lighting_Workflow.pdf p.3) [VERIFIED]; see [06](06_reflections_probes.md) |

**The precedence between worldspawn, SSI and volume values is not documented** (open question §12). The Giant sets all three, so it does not show which one wins.

### 5.4 The Giant's real exposure setup

The Giant sets exposure at several levels at once [VERIFIED] (src: MODTOOLS/map_source/zm/zm_giant.map worldspawn; _prefabs/zm/zm_giant/zm_giant_light.map; source_data/ssi.gdt):

| Level | Values |
|---|---|
| main map worldspawn (`zm_giant.map`) | `evauto 1`, `evmin 3`, `evmax 3.5`, `evcmp 2.5`, plus `secondsLerpToDarker 1`, `secondsLerpToLighter 1`, `lutmaterial luts_t7_zm_factory`, `bloom zm_factory`, `vcolor zm_factory`, `vsky zm_factory_lightning_ukko`, `numOmniShadowSlices 96` |
| light prefab worldspawn (`zm_giant_light.map`) | `evmin −32`, `evmax 31` (unclamped). A prefab's worldspawn is presumably not the level's worldspawn once stamped [INFERRED]. |
| SSI `zm_factory` (states 1 and 2) | `evmin 0.5`, `evmax 3.5`, `evcmp 4` |
| three `volume_exposure` (in the light prefab) | `evmin 0.5`, `evmax 3.5`, `evcmp 4.87` / `4.87` / `3.75`, blends 40–272 units on some sides, BANK_1, priority 1–2 |
| probes | 5 of 176 carry `evcomp −5`, 1 carries `0.5` |

`secondsLerpToDarker/Lighter`, `bloom`, `vcolor` and `vsky` are undeclared worldspawn keys. `secondsLerpToDarker/Lighter` and `vsky` appear in none of the three tool binaries. `bloom` appears once in cod2map64 and `bloom`/`vcolor` appear in Radiant, possibly for other uses such as the grade boxes [VERIFIED] (counts); their use [INFERRED]. They look like adaptation speed and grade selection, but whether a usermap honours them is [TEST].

The Giant's lights sit at a median of `stops 7` under this setup, with 80% of them between 4 and about 10.5 (one is parked at −32) [VERIFIED] (src: zm_giant_light.map, 543 lights parsed).

### 5.5 Which way does `evcmp` push? (UNVERIFIED)

No primary source states the direction. The official text says only "up or down by the x number of stops" (Lighting_Parameters p.12), and the def says "Exposure compensation when auto exposure is enabled." [VERIFIED].

The circumstantial evidence says **positive `evcmp` raises the effective EV, i.e. darkens the image** [INFERRED]:
- the zombies night SSIs pair a low clamp with a **positive** `evcmp` (default_night +2.5, zm_factory +4, zm_zod +3); campaign nights that lock or open the clamp use `evcmp 0` (§3.5);
- The Giant's lights (median stops ~7) read as normal pools only if the effective EV is near 7, i.e. clamp 3.5 + `evcmp` ~4;
- mp_sector's `volume_exposure` entities that set `evcmp` use **negative** values (−0.75, −0.75, −1, −1.5) [VERIFIED] (values). If they cover interiors (not checked), that matches the MP doc's rule of keeping interiors only about one stop darker than outside, i.e. brightening them [INFERRED].

It is also unproven whether `evmin`/`evmax` clamp before or after `evcmp` is applied. **Test:** the same view with SSI `evcmp +2` and then `−2` (or a `volume_exposure`), with same-spot screenshots [TEST].

### 5.6 Treyarch's exposure doctrine, and why zombies nights differ

From Multiplayer_Lighting_Workflow.pdf p.3 [VERIFIED]:
- "Exposure will ALWAYS be set within the range of 8 - 12 stops. This is a hard number to prevent fx from having to create fx specific to every map." That is an **MP** rule. Stock zombies nights sit far below it: default_night 3–3.5, zm_factory 0.5–3.5, zm_zod 4–6. Effects authored for one exposure range can read differently in another [INFERRED].
- "work with the exposure locked at the value that looks good while in the sunlight … if your exterior sunlight exposure is EV 12, then you will make a dark interior look dark at EV 12."
- "The average dynamic range for all mp maps is 1.5 stops … Some maps get up to 2.5 stops of range, but the transition is gradual."
- "Usually the interior to exterior exposure shift is only 1 stop … another interior inside of that one … can drop again to 10 - 10.5."
- "as soon as exposure drops 2 or more stops below the scene exposure, visibility will start to become a problem."
- "start with probe brightness = 2 on the interior probes."

The prefab the doc tells you to stamp first (`_prefabs\lights\mp_default\mp_default_lighting.map`) is **not shipped** in this Mod Tools install [VERIFIED] (absence).

### 5.7 A working model for sizing lights and glow against exposure [INFERRED]

This is a rule of thumb built from the documented units, not a documented formula:
- A light at `stops S` has a linear strength of about 2^S (the units are stops, §1).
- The Materials doc says an emissive surface glows "correctly" in an area at EV *e* when its HDR scale (`scaleRGB`) is 2^*e* (Materials.pdf p.18). So, roughly, the camera maps a scene value of 2^EV to a normal bright level.
- Hence a surface lit by a light of about the effective EV in stops reads normally lit, and every stop below that reads half as bright. Radius, falloff and colour all change the real number.
- Worked numbers: The Giant has lights ~7 against an effective EV of perhaps 7.5 (clamp 3.5 + `evcmp` 4). Tower II has lights at 6 against perhaps 5.5–6 (clamp 3–3.5 + `evcmp` 2.5). Both depend on the `evcmp` direction in §5.5.
- Emissive: at Tower II's clamp of EV 3–3.5 the doc's rule gives an HDR scale of 8–11.3. Tower II's faces use 4, 5, 10 and 15 (see [03](03_glow_and_perks.md)).

Use Radiant's exposure readout (§5.9) to check the effective EV of a spot instead of trusting this arithmetic.

### 5.8 Exposure and lighting states

Each state has its own SSI, so each state has its own `evmin`/`evmax`/`evcmp` [INFERRED]. `volume_exposure` has no LIGHTSTATE flags. To swap exposure zones at runtime, put volumes in banks (for example your own convention `BANK_1` = pre-power, `BANK_2` = post-power) and call `SetExposureActiveBank( localClientNum, bankMask )` from client script. The function is documented [VERIFIED] (API), but no stock script calls it and it is untested in a usermap [TEST] (src: docs_modtools/bo3_scriptapifunctions.htm).

### 5.9 Tools: runtime API, Radiant, check dvars

**Client script API** [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm, Gfx category, all Client):

| Function | Summary |
|---|---|
| `SetExposureActiveBank( localClientNum, bankMask )` | "Set exposure volumes active bank bit mask." |
| `SetExposureInstantSnap( localClientNum, enable )` | "snap exposure to base calculated probe value, ignore iris adaption and damping" |
| `SetExposureIgnoreTeleport( localClientNum, enable )` | "Always do fully adaptive exposure and ignore teleports" (relevant for a map with many teleporters) |

No stock ZM script calls any of these [VERIFIED] (grep).

**Radiant** has exposure lock/unlock icons (`exposure_locked`), an `Exposure Bank` entry, `Show Exposure Zones`, a camera readout `Exposure EV: %.2f (%.2f GPU)`, and a render flag described as "Disables evcmp on probes, and probe-only lights and geometry" [VERIFIED] (strings, src: bin/Radiant_modtools.exe); where each sits in the UI is [INFERRED]. The matching dvar name `r_showExposureZones` appears in `bin/cod2map64.exe`, not in Radiant [VERIFIED] (string scan). The SunSky tutorial screenshot reads `Exposure EV: 6.36` for a test scene with sun stops 6 and `skyStops` 3 [VERIFIED] (screenshot). Lock the exposure while you light, as the MP doc says.

**In-game check dvars.** Mini_Map_Setup.pdf p.5 documents `r_bloomEnable 0` (disables bloom), `r_exposureTweak 1` (enables manual exposure) and `r_exposureValue [4-10]` [VERIFIED] (doc text). Whether they work in the retail client with a usermap is [TEST]. **Project rule:** CLAUDE.md forbids telling the user to set console dvars as a test method. These are listed so you know they exist, and any use needs the user's explicit agreement.

---

## 6. Fog

### 6.1 Plain version

Fog in BO3 is four separate models in one asset:
- **world fog**: distance and height fog in a flat colour;
- **sun fog**: a glow in the fog toward the sun;
- **atmosphere fog**: a physically based sky haze; with its default colours it is blue (Rayleigh) away from the sun and orange (Mie) toward it;
- **lit fog**: volumetric fog that lights, shadows and the sun can shine through (shafts).

You pick the fog with an **fsi** asset, placed on the worldspawn or on fog volumes, and change it with banks or script.

### 6.2 The fsi asset (asset type `fog`)

Source: MODTOOLS/deffiles/fog.awi [VERIFIED].

| Block | Switch (default) | Fields and defaults |
|---|---|---|
| Density, shared | – | `basedist` ("Distance at which fog density is 0"), `halfdist` ("… is 0.5"), `baseheight`, `halfheight`, `skyhalfheightoffset`, `probebakeworldfogdensityscaler` 1, `probebakelitfogdensityscaler` 1, `worldfogskysize` 65000 ("the distance at which the skybox gets fogged for world fog") |
| World fog | `worldfog` 1 | `fogcolor` 0 0 0, `fogopacity` 0 (0..1), `fogintensity` 0 (0..8192) |
| Sun position | used by sun or atmosphere fog | `sunpitchoffset`, `sunyawoffset`: "offset from the active Sun pitch/yaw", so sun fog **follows the SSI sun** |
| Sun fog | `sunfog` 1 | `sunfogcolor`, `sunfogopacity`, `sunfogintensity`, `sunfoginner`, `sunfogouter` (0..100) |
| Atmosphere fog | `atmospherefog` 0 | `atmospheresunenabled` 1, `atmospherefogcolor` "Fog color (Raleigh)" 0.11 0.49 0.84, `atmospherehazecolor` "Sun haze color (Mie)" 0.87 0.49 0.08, `atmospherehazebasedist`, `atmospherehazefadedist`, `atmospherehazedensity` 0.5, `atmospherehazespread` 0.01 ("relationship between the sun direction and haze distribution"), `atmospherefogdensity` 1, `atmosphereinscatterstrength` 17, `atmosphereextinctionstrength` 0 ("Fog Opacity"), `atmospherepbramount` 1 |
| Lit (volumetric) fog | `litfog` 1 | `extcolor`, `distribution` −1..1 (back / isotropic / forward scattering), `albedo` 1, `densityscaler` 1, `probecontributionscaler` 1, `suncoloroverridenenabled` / `suncoloroverride`, `sunintensityscale` −14..14 ("Sun Light Scatter Intensity Boost (in stops)"), `maxlitsunfogdistance` 2000, `maxlitomnispotfogdistance` 2000 |

Stock fog assets (MODTOOLS/source_data/fog.gdt) [VERIFIED]:

| fsi | Key values |
|---|---|
| `default` | world and sun fog on but `fogopacity 0`, `sunfogopacity 0`, litfog 0: it draws nothing through the asset |
| `zm_factory_afog` (The Giant) | atmosphere fog on, world fog off, `fogopacity 0.5`, `halfdist 3358`, `basedist 700`, `halfheight 264`, cool haze colour 0.73 0.93 1 |
| `zm_factory_volumetric` (The Giant) | lit fog on, `fogopacity 1`, `halfdist 1250`, `halfheight 300`, `basedist 50`, `sunintensityscale 2` |
| `zm_factory_dogs_volumetric` | lit fog, `halfdist 650`, `halfheight 1500`, `fogintensity 5` |

### 6.3 Where fog is referenced

| Entity | Keys (src: bin/t7.def.json) [VERIFIED] |
|---|---|
| worldspawn | `fsi` "The fog settings file.", default `default` |
| `volume_worldfog` | `fsi` + `fsi_1..fsi_4` (one per bank), `fogtime` ("Time to lerp from the old fog settings", 1.0), `DISABLE_FOG` (spawnflag 256, **default ticked**; meaning undocumented), `ENABLE_SUN_FOG` (512, on), `AUTO_PRIORITY` (2048, on), `priority`, `LIGHTSTATE_1..4` (4096/8192/16384/32768, **all on by default**), `BANK_1..4` (1/2/4/8, BANK_1 on) |
| `volume_litfog` | as above plus `ENABLE_SUN` (32, on), `ENABLE_LIGHTS` (64, on), `ENABLE_PROBE_LOOKUP` (128, off), `HOLDOUT` (512), `SCRIPT_ID` 0..255, `ambientColor`, `ambientIntensity` |
| `volume_worldfogmodifier` | `depthscale` ("Scale fog half distance"), `heightscale`, `_color` tint, `opacity`, `time`, banks |

Because fog volumes carry LIGHTSTATE flags, **fog can change with the lighting state** on its own [INFERRED] (from the flags). The Giant's fog volumes [VERIFIED] (src: zm_giant_light.map):
- `volume_worldfog` ×4: LIGHTSTATE 1+2 on, 3+4 off, `DISABLE_FOG 0` set explicitly, `fsi_1 zm_factory_afog` / `zm_factory_animal_testing_afog`, `fsi_2 zm_factory_dogs_afog`, `fogtime` 1–2.5.
- `volume_litfog` ×3: one map-wide (`fsi_1 zm_factory_volumetric`, `fsi_2 zm_factory_dogs_volumetric`, BANK_1 + BANK_2, LIGHTSTATE 1+2, ENABLE_SUN and ENABLE_LIGHTS on), and two small ones named `vol_litfog_teslacoils_001/002` (ENABLE_SUN 0, ENABLE_LIGHTS 1, all states, `fogtime 0.5`) around the tesla-coil lights.

Treyarch's MP note: "the 'probe look up' and 'enable lights' is set False for the litfog volume. We can't afford these features as a global setting. If these are needed make another volume for the isolated area with these toggled true" [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.4). The Giant shows the ZM version of that advice: its map-wide volume keeps lights on, but the per-light scattering around the tesla coils sits in its own small volumes.

### 6.4 Banks and script control

- **Lit fog, client:** `SetLitFogBank( localClientNum, scriptid, bank, time )`. `scriptid` is the volume's `SCRIPT_ID` ("(0-255). -1 = all"); `bank` is "Bank selection (0-3)"; `time` "-1 to use the 'fogtime' parameter set in the volume" [VERIFIED] (src: bo3_scriptapifunctions.htm). Bank 0 = BANK_1 is [INFERRED] from stock use (The Giant switches to 1 for its `fsi_2` dog fog and back to 0).
- **World fog:** the API page lists only a server player method, `player SetWorldFogActiveBank( bankMask )`, "Sets world fog volumes active bank mask" [VERIFIED] (API). Stock **client** scripts also call a two-argument form, `SetWorldFogActiveBank( localClientNum, bankMask )` [VERIFIED] (src: zm_giant_fx.csc:170; _zm_ai_wasp.csc:49). Either way the argument is a **mask** (1 = BANK_1, 2 = BANK_2) [INFERRED] (from the stock pairs 2 / 1).
- **Stock example:** `zm_giant_fx.csc:165-180` defines `ramp_fog_in_out()`, which switches to bank 2 (`SetLitFogBank( lcn, -1, 1, -1 )` + `SetWorldFogActiveBank( lcn, 2 )`), waits 2.5 s and switches back. No shipped script calls it. The stock parasite AI does the same swap from a clientfield (`_zm_ai_wasp.csc:44-60`) [VERIFIED]. This is a way to change mood by script with no relighting.
- **Script fog:** `SetVolFog(...)` (server) and `SetExpFog( startDist, halfwayDist, r, g, b, time )`. Stock callers: `load_shared.gsc:807` (8 arguments) and `zm/_art.gsc:226` (the long form, inside a `/# … #/` dev block). Stock's own fog kill sits in the same dev block: `setExpFog( 100000000, 100000001, 0, 0, 0, 0 ); // couldn't find discreet fog disabling other than to never set it in the first place` (`_art.gsc:231`) [VERIFIED]. The 8-argument `SetVolFog` prints `setVolFog: Old syntax used`, and a map that re-asserts it every 0.1 s spams the console [COMMUNITY] (project record) (src: scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc set_fog comment).
- Also available: `SetClientVolumetricFog`, `SetServerVolumetricFogDensity( lcn, density, time )`, `GetWorldFogScriptID( lcn )` ("current active .fsi fog volumes script identity value -1 = global volume") [VERIFIED] (API).
- **Cost at height (MP doc):** "Volumetric Fog was a problem for performance as we got higher in elevation and were rendering the entire map." Treyarch put volumetric fog in bank 1 only and moved high-altitude views to bank 2, which "saves us nearly 1ms" [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.4). A tall tower whose players look down over the whole map is the same situation [INFERRED].

### 6.5 Fog is in the bake

The fog asset has "Scaler to adjust density of world fog in probe bakes" (`probebakeworldfogdensityscaler`) and the lit-fog equivalent, and lit fog has `probecontributionscaler` [VERIFIED] (src: deffiles/fog.awi). So the worldspawn fsi present at bake time can tint probe captures even if script turns fog off at runtime [INFERRED].

### 6.6 Volumetric fog and player settings

BO3's `players/config.ini` has `VolumetricLightingEnabled // 0 or 1` under the comment "Enable volumetric sun and light shafts" [VERIFIED]. The user's own config has it at **0**. Whether this also switches off `volume_litfog` scattering is not documented [TEST]. Plan every dark-map read so it still works with volumetrics off. A light entity is only volumetric if its own `volumetric` key is ticked (see [01](01_lights.md)).

---

## 7. Colour: LUT, grade boxes, bloom, vision

### 7.1 The LUT (global colour cube)

- Worldspawn `lutmaterial`: "Material that contains all the LUT materials", default `luts_t7_default` [VERIFIED] (src: bin/t7.def.json).
- The stock material is `materialType create_lut2dv`, category Filters, LUT image in slot **`colorMap14`**. The image uses `semantic LutTpage`, uncompressed, `colorSRGB 0` [VERIFIED] (src: MODTOOLS/texture_assets/luts.gdt).
- The stock atlas `texture_assets/t7_luts/lut_curve.tif` is 1024 × 1024, 16-bit RGB: 32 bands of 32 px, each a 32³ cube laid out as 32 slices of 32 × 32. That gives **32 LUTs per atlas**, matching `lut_index` 1..32 [VERIFIED] (decoded); meaning of each band [INFERRED].
- `luts_t7_zm_factory` is the same material pointing at `t7_mp_apartments_lut.tif` [VERIFIED].
- Tower II zones `material,luts_t7_default` (src: zone_source/zm_tod2_cybercity.zone:63). A custom LUT = a second LUT material + its zone line + the worldspawn key [COMMUNITY] (MattFiler zm_alien_isolation via Map One docs/16).
- **`lut_volume`** (brush): `index` 0..1024, `time`, `blend_mins/maxs`, `priority`, `BANK_1..4`. Client: `SetLutScriptIndex( lcn, index )`, `SetLutVolumeActiveBank( lcn, mask )` [VERIFIED] (def + API). mp_sector ships one `lut_volume index 1`.

### 7.2 Position-based grade boxes: `pbg_box`, `vlut_box`, `vbloom_box`, `vcolor_*`

These are box-shaped post-effect modifiers (point entities with a size), keyed like probes (`size_min`/`size_max` per side, default 72; `blend_mins/maxs` default 4) [VERIFIED] (src: bin/t7.def.json).

| Class | Keys |
|---|---|
| `pbg_box` / `pbg_omni` / `pbg_spot` | flags `BANK_1..4` (1/2/4/8), `LIGHTSTATE_1..4` (16/32/64/128), `AS_OVERLAY` (256), `USE_UKKO` (4096), `USE_BLOOM` (8192), `USE_LUT` (16384), `USE_COLOR` (32768), `USE_UNDERWATER` (65536); `ukko_index` 1..32 + `ukko_mix`, `bloom_lvi` + `bloom_mix`, `lut_index` 1..32 + `lut_mix`, `color_lvi` + `color_mix`, `underwater_mix`, `underwater_halfdistance` 450, `underwater_absorptionRGB` 0.34 0.0325 0.0114 (underwater: [07](07_water.md)) |
| `vlut_box` | `index` 1..32, `mix` |
| `vbloom_box` / `vcolor_box` / `_omni` / `_spot` | `lvi` ("lvi file to extract bloom/color from"), `mix` |

**Gotcha: these default to Radiant State 1 only.** `LIGHTSTATE_1` is on and 2–4 are off for `pbg_*`, `vlut_box`, `vbloom_box` and `vcolor_*`; `volume_performance` does the same [VERIFIED] (def). A zombies map that boots into script state 1 runs in Radiant State 2, so a box placed with the defaults would be **inactive all match** unless `LIGHTSTATE_2` is ticked [INFERRED] (from the def + the state mapping) [TEST]. Fog volumes default to all four states.

The Giant shows how Treyarch used these flags [VERIFIED] (data, and bit arithmetic from the def) (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map; map_source/_prefabs/zm/zm_giant/light/zm_giant_post.map):
- **Map-wide grade, one box per state.** `zm_giant_post.map` has two `pbg_box` entities with the `zm_factory` grade. Spawnflags **61457** = BANK_1 + LIGHTSTATE_1 + USE_UKKO + USE_BLOOM + USE_LUT + USE_COLOR. Spawnflags **61473** = the same with LIGHTSTATE_2 instead of LIGHTSTATE_1. So each lighting state gets its own copy of the grade.
- **Teleporter grades, powered state only.** 15 `pbg_box` entities in `zm_giant_light.map` (grades `zm_factory_tele_a/b/c`) carry spawnflags **45329** = BANK_1 + LIGHTSTATE_1 + AS_OVERLAY + USE_UKKO + USE_BLOOM + USE_COLOR. They are active only in Radiant State 1, which is The Giant's **powered** state, when the teleporters work. That fits the state mapping [INFERRED].

**The `.lvi` / `.lvx` grade files** in `share/raw/grades/` (26 files: `mp_*`, `zm_factory`, `zm_factory_tele_a/b/c`, `zm_factory_lightning_ukko.lvx`, `*_water`) are binary, made by a Treyarch internal tool. No editor for them ships in MODTOOLS/bin [VERIFIED] (listing). Custom bloom and colour grades through `.lvi` are therefore effectively not authorable; only the shipped files can be reused [INFERRED].

### 7.3 UKKO: The Giant's lightning

The Giant's lightning flash steps `SetUkkoScriptIndex( lcn, index, 1 )` through 1→3→1→4→3→1→3→1 over about 0.9 s, starting with the thunder sound `amb_lightning_dist_low` [VERIFIED] (src: share/raw/scripts/zm/zm_giant.csc:152-172). It runs on each client when a per-player counter clientfield `lightning_strike` ticks, which the server bumps from `periodic_lightning_strikes()` [VERIFIED] (src: zm_giant.csc:60; zm_giant.gsc:209, 223). The grade file is presumably `zm_factory_lightning_ukko.lvx`, selected by the main-map worldspawn key `vsky zm_factory_lightning_ukko` [INFERRED]. This is the stock pattern for a global "flash" that needs no relighting.

### 7.4 Vision files

- The client re-applies the **map-name** vision continuously: `visionset_mgr_shared.csc` `finalize_initialization()` calls `init_fog_vol_to_visionset_monitor( GetDvarString("mapname"), 0 )`, and the monitor re-issues `VisionSetNaked` whenever no visionset-manager set is active [VERIFIED] (src: share/raw/scripts/shared/visionset_mgr_shared.csc:219-227, 853-1010). **Keep `vision/<mapname>.vision` neutral.** Any tint in it comes back on every revive: Map One's "grey screen on revive" was exactly this [COMMUNITY] (project record).
- Tower II also learned that a **missing** map-name vision renders a warm-orange fallback wash on the whole screen, which no script grep can find. The fix was to ship `vision/zm_tod2_cybercity.vision` byte-identical to stock `default.vision` [COMMUNITY] (project record) (src: zone_source/zm_tod2_cybercity.zone:68-79).
- Grade on purpose with a separate vision file: server `VisionSetNaked( name, duration )` [VERIFIED] (API); on the client, stock scripts call `VisionSetNaked( localClientNum, name, time )` and the API lists `VisionSetNakedLerp( localClientNum, to, from, fraction )` [VERIFIED] (src: visionset_mgr_shared.csc:1007; API). The Giant's teleporter flashes save the current set, switch to stock `cheat_bw_invert_contrast` or `zombie_turned` over 0.4 s, and restore it (`zm_giant_teleporter.csc:107-143`) [VERIFIED].
- Vision keys (`vkTT`, `vkTS`, `vkTC`, `vkTO`, `vkRGB0..4`, `vkL0..4`, `vkM0..4`, `vkRM`) are not documented by Treyarch; Map One's docs/20 §7b records its reading of them [COMMUNITY] (project reading).

### 7.5 What controls bloom

The knobs a mapper can reach are: pbg/vbloom boxes with a shipped `.lvi`; the vision curve; emissive HDR scale (the 2^EV rule, [03](03_glow_and_perks.md)); and the peak brightness of the sky picture itself. Tower II's white halos were bright sky pixels ~200× the base, fixed with a soft knee in the image (docs/104 §4k) [COMMUNITY] (project record). `t7.def.json`'s worldspawn declares no bloom or tonemap key [VERIFIED], although The Giant's worldspawn carries an undeclared `bloom zm_factory` (§5.4).

### 7.6 Treyarch's advice: colour in the lighting, not the post

"Doing more of the color work in the baked / dynamic lighting has produced a cleaner look than the use of heavy post fx color grading. Do the heavy lifting with the overrides." [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.2)

---

## 8. Recipe: a sunset

**What makes it read as a sunset** (from the stock numbers) [INFERRED]: a low sun that casts long shadows, a warm sun colour, the sun and sky light close together in stops (soft, bright sky fill), a sky picture whose glow sits exactly where the sun is, horizon-coloured haze, and an exposure clamp placed around the sky's brightness.

1. **Pick or make the sky picture.** For a quick test, the stock `skybox_default_sunset` (`skyStops 10.15`, `skyRotation 110`). For anything shipped, make a unique EXR (SunSky doc rule). For Tower II, `node tools/gen_tod_sky.js --theme sunset` renders a sunset with the sun at 7° elevation in the centre of the panorama (src: tools/gen_tod_sky.js theme table). Its gain solve holds the sky-light score at `--target-score`, so the world's sky light does not jump.
2. **Clone the SSI.** Copy stock `default_sunset` into a map-owned GDT (for Tower II, one that syncs to the private workspace, never the shared tools root) and rename it, e.g. `tod_ssi_sunset`. Start values: `colorSRGB 1 0.768 0.546`, `pitch 158`, `yaw 300`, `stops 11`, `evcmp 0`, `evmin 8`, `evmax 12.5`, `penumbra_inches 1.5`, `bounceCount 4`, `skyboxmodel` = your sky model. Never start from a blank SSI, whose sun is black.
3. **Keep the sun low and warm.** Pitch about 155–170 (or 10–25), per the §3.2 convention [TEST]. Colour: R 1, G 0.44–0.77, B 0.22–0.55 (the stock warm suns in §3.3); a redder sun reads as later in the evening [INFERRED] (`cp_mi_sing_vengeance` 0.88 0.44 0.22 at pitch 18).
4. **Keep sun and sky close in stops.** `default_sunset` has the sun only about 0.85 stop above the sky (11 vs 10.15), against 5+ stops apart at night.
5. **Line up sun and picture.** Turn the sky with `skyRotation` until its glow sits at the SSI yaw ("Use skyRotation to line the sky up to the sun direction"). Optionally add a lens flare temporarily to see where the SSI sun is [COMMUNITY]. Pitch, yaw and `skyStops` need a rebake to show.
6. **Exposure around the sky.** `default_sunset` clamps EV 8..12.5 for a sky at 10.15. Keep `evmax` near `skyStops` + 2 so the bright west does not force the camera to crush the east [INFERRED].
7. **Fog.** Make an fsi with atmosphere fog on: Mie haze warm (default 0.87 0.49 0.08) with a small `atmospherehazespread` so it hugs the sun, Rayleigh colour cool for the far side, world-fog colour matched to the sky's horizon so geometry dissolves into the sky, not into a grey band. Sun and atmosphere fog follow the SSI sun automatically (`sunpitchoffset`/`sunyawoffset` are offsets). Reference values: The Giant's `zm_factory_afog` (§6.2).
8. **If the orange sky over-tints the GI**, bake from a neutral `<name>_bake` SSI in `ssi1` and put the sunset in `ssi1_runtime_override` (§2.6).
9. **Long shadows:** if they alias, lower `shadowSplitDistance` (quality up, memory up).
10. **For the Glass Tower look** (mirror floors repeating the sky): reflective low-roughness floors plus reflection probes fitted to each space; see [06](06_reflections_probes.md) and [09 §4](09_design_and_inspiration.md#4-glass-tower). Glass Tower's look is driven mostly by a sunset/space skybox, mirror-like floors and faces, and water [COMMUNITY] (the author's Workshop screenshots, per 09); how it was built is unknown.
11. **Full build**, then same-spot screenshots facing toward and away from the sun, on a low and a high graphics config ([09 §7.3](09_design_and_inspiration.md#73-judge-on-two-graphics-configs)).

A sunset is a **mood choice**: it is not a dark map. For Tower II it would suit a single moment, such as the crown finale, better than the whole climb [INFERRED]. Whether a lighting state can change the visible sky picture is [TEST]. The project records that the skybox and SSI are baked in and cannot be swapped by script (src: tools/gen_tower_map.js:1845-1860 comment), but each state's SSI names its own `skyboxmodel`.

---

## 9. Recipe: a night / dark map that stays readable

### 9.1 The idea

The look is the **gap** between each light source and the exposure [INFERRED] (anchored on the stock numbers):
- keep sun and sky light well **below** the effective exposure (stock zombies nights: sun 5–7 stops under the sky, EV clamped within ~0.5–3 stops, `evcmp` +2..+4);
- put local lights **near or above** the exposure, so they make readable pools (The Giant: lights ~7 against an effective ~7.5);
- **clamp** the exposure narrow, so the camera cannot re-brighten the dark.

### 9.2 Steps

1. **Start from a stock night SSI.** `default_night` (the tower's current base), `zm_factory` (even lower clamp) or `zm_zod` (sun switched off). Put it in the SSI slot of **every** lighting state you use.
2. **Sun:** cool colour (`0.79 1 1` or `0.53 0.69 0.69`), `stops` 5–7 below the sky (−2..−2.5 against `skyStops` 3–4.4), or `enablesun 0`. With the sun down at −2.2, `dynamicShadow 1` still costs shadow work while adding almost nothing [INFERRED].
3. **Exposure:** narrow `evmin`/`evmax` (3..3.5, 0.5..3.5, 4..6), `evcmp` like the stock zombies nights (+2.5, +4, +3). An `evmin` of −32 lets the camera brighten darkness into grey [INFERRED]. Use `volume_exposure` only for exceptions, e.g. `evcmp` on a room.
4. **Sky light:** low `skyStops` and/or a dim picture. Stock nights use 3–4.4. For Tower II's generator: `--target-score`. Dim the **visible** sky separately with worldspawn `sky_intensity_factor0/1` (Map One 0.6). Community advice for a night sky that is too bright is the same: smaller stops, or exposure compensation [COMMUNITY] (src: https://forum.modme.co/wiki/threads/2868.html).
5. **Local lights:** key pools near the effective exposure in stops; fill lights 2–3 stops below the key; emissive HDR scale ≈ 2^EV of the area (EV 3 → 8, 3.5 → ~11.3). A few strong, well-placed pools read darker than many weak ones [COMMUNITY] (Map One's palette rule "~85% dark base; neon <15%", docs/20).
6. **Probes:** fit local probes to rooms so the sky-fed global probe does not light the interiors ([06](06_reflections_probes.md)).
7. **Readability (never pitch black):**
   - no playable space more than ~2 stops under the scene exposure (Treyarch MP rule, §5.6);
   - albedo within sRGB 40..238, "This leaves room for lighting" (src: docs_modtools/PhysicallyBasedRendering.pptx slide 10) [VERIFIED]: make darkness with light, not with black textures;
   - try `global_fill_color` near the average ground colour instead of the black default, as an A/B (the def recommends it; Treyarch's shipped volumes keep black, §2.4) [TEST];
   - optionally bake bounce 1–2 stops brighter than the displayed sun (§2.6);
   - enemies read as silhouettes against brighter backgrounds (see [09](09_design_and_inspiration.md));
   - any fog colour must stay lighter than scene black, or it reads as nothing [COMMUNITY] (project lesson) (src: scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc header).
8. **Grade:** keep the map-name `.vision` neutral; grade with a LUT or a separate vision file.
9. **Build and judge:** full build; same-spot, same-state screenshots against the previous build; read Radiant's `Exposure EV` with the exposure locked; judge on both a low and a high graphics config.

### 9.3 Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Dark areas look grey, flat, washed out | exposure unclamped (`evmin −32`), so the camera brightens darkness; or too much sky light | raise `evmin` / lock EV; lower `skyStops` or the sky gain |
| Olive or yellow cast on everything, including gun and zombies | strong sky light on white or dark albedos (Tower v17.73 score ~4.0); sun-lit fog (`litfog` + `sunintensityscale`); a warm key light; the docs/107 sun-volume height problem | solve the sky gain; an fsi without sun-lit fog; neutral key lights; keep `SUN_VOLUME_TOP_MIN`; test a global-probe `target` |
| Black crush, zombies invisible | lights far under exposure, no fill, possibly the black `global_fill_color`, heavy vision curve | fill lights 2–3 stops under the key; try a non-black `global_fill_color` [TEST]; neutral vision |
| Everything the same brightness | wide exposure range, evenly spread lights, sky dominating ambient | narrow clamp; fewer, stronger pools; less sky light |
| White halos on neon and sky | sky picture peaks far above its base; emissive HDR scale far above 2^EV | knee the sky picture (docs/104 §4k); emissive scale ≈ 2^EV |
| Grey or tinted screen after revive | tinted map-name `.vision` re-applied per client | neutral map-name vision (§7.4) |
| Flash when the power comes on | instant lighting-state swap [COMMUNITY] (Map One project record, §10) | vision hold-then-lerp (Map One, §10) or `transitionTime` [TEST] |
| Interior as bright as outdoors | missing local probe, so the global probe lights it; sun leaking | probes per room; `caulk_shadow`; lower `shadowSplitDistance` [COMMUNITY] |
| Map-wide lighting broken on some PCs after a fresh tools install | Windows decimal separator set to a comma | set it to `.`, reinstall the tools [COMMUNITY] (src: https://www.ugx-mods.com/forum/mapping/92/fixing-lightingsun-in-a-new-map/12772) |

---

## 10. Power-on: the global side

Full treatment: [02 — power and states](02_power_and_states.md), especially [the two working conventions](02_power_and_states.md#4-the-two-working-conventions) and [the recommended dark-before-power design](02_power_and_states.md#141-recommended-design-dark-before-power-lights-at-power). The sun/sky/exposure parts:

- Stock `_zm_power.gsc` makes no lighting-state, exploder or vision call [VERIFIED] (grep), so nothing global changes at power unless the map scripts it.
- A lighting state switches the **whole map** at once. That is why "the whole tower lights up". Per-area power-ups need exploder- or script-driven lights ([02 §9](02_power_and_states.md#9-exploders-named-light-groups), [04](04_fx_lights.md)).
- Give each state you use an SSI. Each can differ, e.g. a darker pre-power SSI with its own exposure clamp. `transitionTime` on the `volume_sun` is the documented blend between sun states [VERIFIED] (def); effect [TEST] ([02 §8](02_power_and_states.md#8-transitions-instant-or-blended)).
- Fog volumes follow `LIGHTSTATE_n` flags. `volume_exposure` does not: use exposure banks + `SetExposureActiveBank` from client script [TEST]. `pbg_*`/`vlut`/`vbloom`/`vcolor` boxes default to Radiant State 1 only (§7.2). Banks as mood switches: [02 §11](02_power_and_states.md#11-fog-exposure-lut-and-grade-banks-as-mood-switches).
- Probes are baked per state [INFERRED] (from Radiant's per-state arrays), so post-power bounce and reflections come from the post-power bake.
- The swap is instant. Map One hides it with `VisionSetNaked( <dark grade>, 0 )` right before `set_lighting_state(1)`, then lerps back to default over about 15 s [COMMUNITY] (project record) (src: Map One `scripts/zm/zm_abandoned_cyber_city.gsc:955-975` for the hold, `scripts/zm/zm_abandoned_cyber_city/_acc_atmosphere.gsc:490-530` for the ramp).
- `util::set_lighting_state` also works on a single player, `player GetLightingState()` reads it back, and `_globallogic_spawn.gsc:501` re-applies the level's state on every spawn [VERIFIED] (src: share/raw/scripts/shared/util_shared.gsc:2967-3006).

---

## 11. Tower of Doom II: facts and history

### 11.1 Current setup (read from the generated map and GDTs)

| Item | Value | Source |
|---|---|---|
| `volume_sun` box | x, y ±12,224; z −544..39,500 (24,448 × 24,448 × 40,044) | map_source/zm/zm_tod2_cybercity.map (volume_sun entity) [VERIFIED] |
| `volume_sun` keys | `ssi` + `ssi1` = `tod_ssi_cybercity`, `grid_density 32`, `shadowBiasScale 1`, `shadowSplitDistance 2000`, `streamLighting 1` | tools/gen_tower_map.js:7376-7382 [VERIFIED] |
| missing | `ssi2..4`, runtime overrides, `target`, `global_fill_color/intensity`, `transitionTime` | same [VERIFIED] |
| global probe | box centre (0, 0, 19,478), **inside** worldspawn brush `mast tier 1` (x/y ±256, z 19,392..19,712, material `mwiii_vertigo_retro_synth_pap`) | map lines ~54447 and ~141505 [VERIFIED] (arithmetic) |
| global-probe cells | about 764 × 764 × 1,251 units | [INFERRED] (arithmetic) |
| compiled state SSIs | `tod_ssi_cybercity`, then `default_day` ×3 | .led byte scan [VERIFIED] |
| SSI `tod_ssi_cybercity` | `default_night` values: sun 0.791 1 1, pitch 130 / yaw 140, stops −2.2, `ev 6`, `evcmp 2.5`, `evmin 3`, `evmax 3.5`, penumbra 1.5, bounceCount 4 | source_data/tod_skybox.gdt [VERIFIED] |
| sky material | `sky_latlong_hdr`, `skyStops 10.0` (default_night 4.4, zm_factory 3), `skyScaleRGB 1097.5`, `skyRotation 0`, `skySize 8000`, `skyFogFraction 1` | source_data/tod_skybox.gdt [VERIFIED] |
| sky picture | "evil" theme, 8192 × 4096 half EXR, gain 0.02603 solved for sky-light score 0.324, linear RGB share 67/16/17 (red-dominant) | docs/150 status [COMMUNITY] (project record) |
| worldspawn | `skyboxmodel skybox_tod_cybercity`, `ssi tod_ssi_cybercity`, `wsi default_night`, `fsi zm_factory_volumetric`, `lutmaterial luts_t7_default`, `sky_intensity_factor0/1 1`, `state_alias_1..4 "State N"`; **no exposure keys**. The same keys are in the compiled `.d3dbsp` | tools/gen_tower_map.js:8691-8752; C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.d3dbsp [VERIFIED] |
| exposure / fog / grade volumes | none (no `volume_exposure`, `volume_worldfog`, `volume_litfog`, `pbg_box`, `lut_volume`) | map parse [VERIFIED] |
| script fog | `apply_fog()` keeps the tower at `fog_off()` = `set_fog( 100000000, 100000001, 0,0,0,0,0,0 )`; `set_fog()` is change-gated, so the 8-argument `SetVolFog` runs only when the wanted state changes; only the spire gets fog | scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc:688, 755, 968 [VERIFIED] |
| vision | `vision/zm_tod2_cybercity.vision`, neutral, zoned | zone:79 [VERIFIED] |
| lighting state | no TOD II script calls `set_lighting_state` [VERIFIED] (grep of scripts/); `zm_usermap::main()` (called at scripts/zm/zm_tod2_cybercity.gsc:247) sets script state 1 [VERIFIED], which shows Radiant State 2 [INFERRED] (mapping) | MODTOOLS/share/raw/scripts/zm/zm_usermap.gsc:110 |
| lights | 344, all `stops 6`, all `lightingstate` 0/1/1/1 (off only in Radiant State 1) | map parse [VERIFIED]; see [01](01_lights.md) |

Unused but present: `tod_fsi_cybercity` in source_data/tod_skybox.gdt (world fog, sun fog and lit fog all off, `fogopacity 1`, colour 0.16 0.14 0.30). Nothing references it.

### 11.2 History: lessons already paid for

- **The sky is a light** (docs/104 §4) [COMMUNITY] (project record). The first cybercity sky (v17.73) scored about 4.0 on the sky-light score, three times the pack, "and every wall, gun and zombie went olive-yellow". Since then `SKY_GAIN` is **solved** to a target score (0.478 → 0.45 → 0.324), so a picture change cannot move the world's light. The user saw white glare in game that the display-referred previews could not show; the cause was sky pixels far above the base, so a soft knee now clips the peaks (docs/104 §4k). Judge sharpness only on the `*_ingame_*` 1:1 crops.
- **The yellow tower** (docs/107) [COMMUNITY] (project record). When the spire was cut from 100 to 70 laps, `SKY_TOP` dropped from 39,468 to 29,196, the `volume_sun` shrank with it, and the whole tower (walls, gun, hands, zombies) lit yellow-olive. Six builds of sky, fog, light and vision reverts changed nothing. The empirical fix is `SUN_VOLUME_TOP_MIN = 39168` as an extra `max()` term (tools/gen_tower_map.js:1541-1558). The generator says outright "The mechanism inside Radiant is not known".
- **Candidate mechanisms from this reference** [INFERRED] (untested):
  - (a) **The global probe moved.** Untargeted, it sits at the box centre. TOD1's sun volume runs from z −96, so in the yellow builds (top 29,228) the centre was (0, 0, 14,566), and in the good build (top 39,500) it is (0, 0, 19,702). On TOD1's current map, 14,566 lies inside the core brush `core band lap38 spine NS` (x ±16, y ±256, z 14,208..14,592), textured `mwiii_vertigo_retro_synth_yellow`, and 19,702 lies inside `mast tier 1` (PaP material) [VERIFIED] (point-in-brush test) (src: ../tower_of_doom_cybercity/map_source/zm/zm_tower_of_doom.map; docs/107 table). That the core geometry at 14,566 was the same in the yellow builds is [INFERRED]. A global probe buried in a yellow brush would explain a map-wide warm bounce that "honoured positions but not colour". Caveat: **both** builds had a buried probe, so "buried" alone does not separate them; the material it was buried in, or its height, might.
  - (b) **The grid changed.** 32 points over the height gave ~916-unit cells in the yellow build and ~1,237 in the good one.
  - (c) **The state-2 slot.** The game probably runs Radiant State 2, whose compiled SSI is `default_day` (pitch 125, yaw 150, stops 14, warm `1 0.976 0.949`). That was the same in good and yellow builds, so it cannot explain the difference alone, but it has never been examined: docs/107 checked only the State 1 entry of the `.led` (pitch 130 / yaw 140).
  - The Treyarch-sanctioned way to take (a) off the table is a `target` on an open-air `info_null`, tested by A/B builds that differ only in `target`.
- **"Authored OFF before power" was a misreading.** docs/107 and the generator comment (tools/gen_tower_map.js:1545-1547) call `lightingstate1 0` "authored OFF before power". Under the stock-supported mapping the game never enters Radiant State 1, so every light is on from spawn and power changes none of them [INFERRED] (see [02](02_power_and_states.md)).
- **Sun-lit fog** (docs/104 §4c, docs/107). `fsi zm_factory_volumetric` carries `litfog 1` and `sunintensityscale 2` [VERIFIED] (src: MODTOOLS/source_data/fog.gdt), and the project's reading is that the 8-argument `SetVolFog` fog-off cannot touch its sun-fog lane [COMMUNITY] (project record). Its world-fog colour is a cool blue (0.67 0.74 0.99); the only orange in it is the default Mie haze colour (0.87 0.49 0.08) on its atmosphere lane, which is switched off (`atmospherefog 0`) [VERIFIED] (fog.gdt). v17.75 blamed it for the yellow and swapped in `tod_fsi_cybercity`; the tower stayed yellow, and v17.78 went back to `zm_factory_volumetric` for the A/B. It is still the live fsi, and it is present at bake time (§6.5). The Giant's own worldspawn uses `fsi default` and puts its fog in volumes instead [VERIFIED] (zm_giant.map).
- **Never adopt the Nastian T9 SSIs** for a night. Their clamps sit far higher (evmin 5.5–8 / evmax 12–14, hidden `ev 15`) than the night clamp (3 / 3.5, `ev 6`). A higher EV exposes for daylight, so on night lighting it renders the scene much darker; docs/104 §1 says the ~9-EV jump "would crush the neon look" [COMMUNITY] (project record) [INFERRED] (direction, §5.1).
- **Diff the worldspawn** when a tint survives every change: the baked sky, fog and LUT keys live there (docs/104 §4c) [COMMUNITY] (project lesson). Diff the `volume_sun` too, because the per-state SSIs and the global-probe `target` live on it. **Establish the "before" first**: same-spot, same-state screenshots, and build the control map (`Repositories/test+map`) first, not sixth (docs/107).
- **Radiant is a GUI exe**: wait for it, or the linker prints "Falling back to preview lighting" (docs/107) [COMMUNITY] (project record).
- **The evil sky is red-dominant** (docs/150 §5) [COMMUNITY] (project record). If the world looks red-lit rather than red-skied, `--tint 1,1.1,1.1` pulls the light back without changing the picture's exposure.

### 11.3 How TOD II compares with the stock night

| | default_night (stock) | zm_factory (The Giant) | Tower II |
|---|---|---|---|
| sun stops / colour | −2.2 / cool cyan | −2 / cool teal | −2.2 / cool cyan |
| sky gain (`skyStops`) | 4.4 | 3 | **10.0** |
| exposure clamp / `evcmp` | 3..3.5 / 2.5 | 0.5..3.5 / 4 (+ worldspawn 3..3.5 / 2.5, volumes 4.87 / 3.75) | 3..3.5 / 2.5, no worldspawn keys, no volumes |
| states with an SSI | – | 1 and 2 | 1 only |
| global probe | – | targeted, open air | untargeted, buried |

Tower II's sky-light gain is about 5.6 stops above default_night's. The pictures differ, so this is a gain comparison only [INFERRED].

---

## 12. Open questions and in-game tests

Every item needs an in-game look or an A/B bake. The user tests; agents build and stop. Where chapter 10 already has a numbered test, the ID is given ([10 §7.3](10_troubleshooting_limits_history.md#73-the-tests)).

| # | Question | How to settle it |
|---|---|---|
| 1 | Does a usermap really boot in Radiant State 2? | T1: the two-coloured-light test in the control map ([02 §16](02_power_and_states.md#16-minimal-test-plan-in-the-control-map)) |
| 2 | What does the engine show for a state whose `ssiN` is empty? | T2: control-map A/B, `ssi2` empty vs `ssi2 = ssi1`; same-spot screenshots; watch Radiant for the "DOES NOT SUPPORT ACTIVE LIGHTING STATE" line |
| 3 | Which way does `evcmp` push, and does the clamp apply before or after it? | T6: SSI `evcmp +2` vs `−2` |
| 4 | Precedence of worldspawn vs SSI vs `volume_exposure` exposure | controlled A/B builds |
| 5 | Is auto-exposure on without `evauto 1`? | A/B with worldspawn `evauto 1` |
| 6 | SSI pitch convention | Radiant: pitch 10 vs 170 at the same yaw |
| 7 | Does the buried global probe (and its position) cause the docs/107 cast? | T3: A/B with a `target` on an open-air `info_null`, all else identical; compare `.led` size and same-spot screenshots |
| 8 | What `skyScaleRGB`, `skySize`, `skyFogFraction` do | vary one at a time in the control map |
| 9 | Do the undeclared worldspawn keys work (`evmin/evmax/evcmp`, `evauto`, `secondsLerpToDarker/Lighter`, `bloom`, `vcolor`, `vsky`, `ssi`, `skyboxmodel`, `wsi`, `evmin1..4`)? | A/B, one key at a time |
| 10 | Does `transitionTime` blend a script state change? | T15: set it, flip states, watch |
| 11 | Do `SetExposureActiveBank` / `SetLutScriptIndex` / `SetPBGActiveBank` work in a usermap? | client-script test |
| 12 | Does `fsi default` (fogopacity 0) suppress script `SetVolFog` fog? The project notes disagree | control-map test |
| 13 | Does `VolumetricLightingEnabled 0` also remove `volume_litfog` scattering? | compare configs |
| 14 | The light cap per sun volume (`max %u supported`) | read a Radiant bake log |
| 15 | Do `pbg_*` / `vlut_box` / `vbloom_box` / `vcolor_*` boxes with default flags apply in Radiant State 2? | T7: one box with defaults, one with `LIGHTSTATE_2` ticked |
| 16 | Does a non-black `global_fill_color` lift occluded corners on this map? | A/B bake, same-spot screenshots in a covered corner |

---

## For Tower of Doom II

Recommendations only. Nothing here has been changed or tested. Each item is a FULL build, because the LED bake runs only in a full build. New lighting assets go in map-owned GDTs that sync to the private workspace `C:\BO3Tools\TOD2Cybercity`, never into the shared Mod Tools root (docs/154).

1. **Settle the state question first** (open question 1, test T1). Everything about "dark before power" depends on it: [02 §15](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis).
2. **Fill every state you use with a real SSI.** Add `ssi2` (and `ssi3`/`ssi4` if they will ever be used) in the `volume_sun` block at tools/gen_tower_map.js:7376. Today the live state is paired with `default_day` in the compiled LED. The same SSI in both slots is the stock pattern (Giant, Map One). If the power plan wants a darker pre-power look, the pre-power state can get its own dimmer SSI (e.g. Map One's −2.52-stop approach) with its own exposure clamp.
3. **Relocate the global probe.** Emit an `info_null` with a `targetname` and a `target` key on the `volume_sun`, placed in open air clear of every brush and away from the extremes of height. Because play spans the Undercity at z −384 to the crown and spire, test two candidates by A/B: just above the base plaza, and mid-tower in open air beside the spiral. This also tests the docs/107 mechanism (§11.2, test T3). Keep `SUN_VOLUME_TOP_MIN` either way.
4. **Test `global_fill_color` as an A/B.** The def says it "should match the average ground color", but The Giant, mp_sector and Map One all keep `0 0 0`, so a dark colour near the average ground colour (with `global_fill_intensity 1`) is a candidate improvement for occluded corners, not a known fix (open question 16).
5. **Reduce the sky light's gain before touching the picture.** `skyStops 10.0` is well above stock night skies (4.4, 3). Try one or two stops lower in source_data/tod_skybox.gdt, or a lower `--target-score` in tools/gen_tod_sky.js, and compare same-spot screenshots. Remember the evil sky is red-dominant (docs/150 §5).
6. **Keep the exposure clamp narrow.** The current `default_night` clamp (3..3.5, `evcmp 2.5`) is already a stock night clamp. Do not widen it. After the `evcmp` direction test, decide whether the worldspawn needs keys like The Giant's, and whether dark rooms (Vault, Conduit, workshop wings) need a `volume_exposure`.
7. **Consider a separate sun volume for the roofed Undercity** (from the sky floor at z −544 up to just under the plaza floor at z 0), with its own global probe and a darker SSI. The open-sky shaft would cross the boundary between the two volumes. Sun volumes may not overlap and must be boxes, and the doc suggests `streamLighting` to avoid popping when the camera crosses between them [INFERRED] (bake A/B needed).
8. **Decide the fog on purpose.** The live fsi `zm_factory_volumetric` probably bakes lit, sun-boosted fog into the probes although the tower turns fog off in script [INFERRED] (§6.5). Test `tod_fsi_cybercity` (all fog lanes off) or stock `default` (The Giant's worldspawn choice) against it. If a pre-power mood is wanted, use fog **volumes** with `LIGHTSTATE_n` flags or banks rather than per-frame script fog.
9. **Any grade box should tick `LIGHTSTATE_2`** (and every other state the map uses), or it will probably never be active (§7.2) [INFERRED]; test T7 settles it. For a grade that should differ before and after power, copy The Giant's pattern: one box per state.
10. **Keep `vision/zm_tod2_cybercity.vision` neutral**; do any power-on ramp with a separate vision file (§7.4).
11. **Correct the record after the tests**: docs/107's "authored OFF before power" and the generator comment at tools/gen_tower_map.js:1545-1547.
12. **A sunset** is a separate mood from the dark tower. If wanted, reserve it for a moment such as the crown finale, and build it from §8.
13. **Judge on two configs.** The user's config has volumetrics, dynamic shadows and SSAO off; check a high config too ([09 §7.3](09_design_and_inspiration.md#73-judge-on-two-graphics-configs)).
14. **Mind volumetric fog at height.** If lit fog is ever added: Treyarch found volumetric fog costly for high views that render the whole map, and switching it off for those views with a second bank "saves us nearly 1ms" (§6.4). The tower's upper floors are that case [INFERRED].

---

## Sources

**Official Treyarch documents** (MODTOOLS/docs_modtools)
- SunSky_Light_SetUp.pdf: sun volume = global probe, lighting states, runtime override, limits (p.4), sky light (p.2-3), rebake list (p.14-15), bake override (p.16-17), shadowSplitDistance (p.1, p.14)
- Lighting_Probe_Workflow.pdf: global probe at the volume centre, "doesn't quite look as good", `target` → info_null (p.1), burial warning (p.2), grid density memory (p.3)
- Probe/Reflection_Probes.pdf: global probe blends only outside local probes; sky visibility; the old minimum-occlusion parameter (p.6)
- Lighting_Parameters.pdf: stops units (p.1); sun gobo (p.11); AUTO EXPOSURE PARAMETERS (p.12)
- Multiplayer_Lighting_Workflow.pdf: missing default prefab (p.1); sun/sky overrides, "+1-2 stops of sun bake", colour in the lighting (p.2); exposure 8–12, dynamic range, interiors, probe evcomp (p.3); fog banks, volumetric fog cost at height, litfog "probe look up"/"enable lights" (p.4)
- Materials.pdf: emissive HDR scale = 2^EV (p.18)
- Mini_Map_Setup.pdf: `r_bloomEnable`, `r_exposureTweak`, `r_exposureValue` (p.5)
- PhysicallyBasedRendering.pptx: albedo 40..238 (slide 10)
- bo3_scriptapifunctions.htm: SetLightingState, GetLightingState, SetExposureActiveBank / InstantSnap / IgnoreTeleport, SetLitFogBank, SetWorldFogActiveBank, SetVolFog, SetExpFog, SetClientVolumetricFog, SetServerVolumetricFogDensity, GetWorldFogScriptID, SetLutScriptIndex, SetLutVolumeActiveBank, SetPBGActiveBank, SetUkkoScriptIndex, VisionSetNaked, VisionSetNakedLerp, SetSunShadowSplitDistance

**Stock definitions and data** (MODTOOLS)
- bin/t7.def.json: worldspawn, volume_sun, volume_exposure, volume_worldfog, volume_litfog, volume_worldfogmodifier, lut_volume, vbloom_box, vlut_box, vcolor_box, pbg_box, volume_performance
- deffiles/ssi.awi, deffiles/fog.awi, deffiles/material.awi:632-640
- source_data/ssi.gdt (93 stock SSIs), source_data/fog.gdt, source_data/acc_ssi.gdt, source_data/acc_nastian_t9_skyboxes.gdt
- model_export/t7_skybox.gdt, model_export/t7_techart_props.gdt (sky materials)
- texture_assets/luts.gdt, texture_assets/t7_luts/lut_curve.tif
- share/raw/grades/ (26 .lvi/.lvx), share/raw/lensflares/ (22 .klf)
- map_source/zm/zm_giant.map (worldspawn exposure, `fsi default`, light-prefab origin), map_source/_prefabs/zm/zm_giant/zm_giant_light.map (volume_sun, info_null, volume_exposure, fog volumes, pbg_box, probes, lights), map_source/_prefabs/zm/zm_giant/light/zm_giant_post.map (per-state grade boxes), _prefabs/mp/mp_sector/mp_sector_light.map, _prefabs/mp/mp_combine/mp_combine_light.map, map_source/zm/zm_test_map.map, rex/templates/ZM Mod Level and MP Mod Level template.map, map_source/zm/zm_abandoned_cyber_city.map
- share/raw/maps: zm/zm_giant.led, zm/zm_abandoned_cyber_city.led, mp/mp_sector.led (per-state SSI lists)
- share/raw/scripts: zm/zm_usermap.gsc:110; shared/util_shared.gsc:2967-3006, 3016; zm/gametypes/_globallogic_spawn.gsc:501-502; zm/zm_giant.csc:60, 152-172; zm/zm_giant.gsc:209, 223; zm/zm_giant_fx.csc:165-180; zm/_zm_ai_wasp.csc:44-60; zm/zm_giant_teleporter.csc:107-143; zm/_art.gsc:226-231; shared/load_shared.gsc:807; shared/visionset_mgr_shared.csc:219-227, 853-1010
- bin/Radiant_modtools.exe, bin/cod2map64.exe, bin/linker_modtools.exe (string scans)
- The user's BO3 graphics config: `Call of Duty Black Ops III/players/config.ini`

**This repo and the private workspace**
- tools/gen_tower_map.js (1540-1558 SUN_VOLUME_TOP_MIN and its comment; 1845-1893 sky/SSI pair; 7375-7382 volume_sun; 8691-8752 worldspawn); tools/gen_tod_sky.js (themes incl. `sunset` sunEl 7, `--target-score`, knee)
- map_source/zm/zm_tod2_cybercity.map (volume_sun ~141505, `mast tier 1` ~54447, 344 lights, 53 probes); source_data/tod_skybox.gdt; zone_source/zm_tod2_cybercity.zone:40-79; vision/zm_tod2_cybercity.vision; scripts/zm/zm_tod2_cybercity.gsc:247; scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc:688, 755, 968
- docs/104_cybercity_sky.md, docs/107_sun_volume_yellow_postmortem.md, docs/150_tod2_evil_sky.md, docs/154_tod2_isolation.md
- C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.led (state SSI list) and .d3dbsp (compiled worldspawn); C:/BO3Tools/TOD2Cybercity/source_data/hb_skyboxes.gdt
- TOD1: ../tower_of_doom_cybercity/map_source/zm/zm_tower_of_doom.map (sun volume, `core band lap38 spine NS`, `mast tier 1`)
- Map One: abandoned_cyber_city_zombies docs/20_atmosphere_and_materials.md, docs/16_community_techniques.md, scripts/zm/zm_abandoned_cyber_city.gsc:955-975, scripts/zm/zm_abandoned_cyber_city/_acc_atmosphere.gsc:490-530

**Community and other**
- Treyarch SIGGRAPH 2016, "Volumetric Global Illumination at Treyarch": https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf
- IceGrenade lighting-state wiki: https://github.com/IceGrenade/bo3/blob/master/wiki/lightstates
- MattFiler zm_alien_isolation (multi-state sun volumes): https://github.com/MattFiler/zm_alien_isolation
- UGX, decimal-comma lighting bug: https://www.ugx-mods.com/forum/mapping/92/fixing-lightingsun-in-a-new-map/12772
- Steam, light bleeding and shadowSplitDistance: https://steamcommunity.com/app/455130/discussions/0/3424437779948829805/ and https://steamcommunity.com/app/455130/discussions/0/135509472110841959/
- modme, buried sun-volume centre: https://forum.modme.co/wiki/threads/3307.html
- modme, darken a night sky via stops / ev comp: https://forum.modme.co/wiki/threads/2868.html
- VerK0 and JBird632 lighting tutorials (as summarised in [09](09_design_and_inspiration.md))
- Glass Tower [HARD], Workshop item 3801980290: https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290
