# 01 — Lights: every kind of light and every key

**In short.** In Black Ops III a "light" is an invisible Radiant entity (`classname light`) that shines from a point (omni) or in a cone (spot). The lamp the player sees is a separate model, and the glow on the bulb is a separate material or effect. One light entity does three jobs: it lights surfaces directly, it can be blocked by a shadow map, and it feeds the baked bounce light stored in the reflection probes. Brightness is set in **stops**, where +1 stop is (very probably) twice as bright; reach is set by `radius`; shadows are **off unless you turn them on**. There is really only one placed light entity (plus a stripped-down `build_light`), and everything else in this chapter is a key on it: cone shape, soft edges, cookies (projected patterns), visible beams, level of detail, lighting-state membership and script access.

**Read this when…** you are placing or tuning a light, deciding how bright or how big a light should be, making a light dimmer, deciding whether it needs shadows, or reading or changing the generator's `light()` function.

**How the tags work.** `[VERIFIED]` = read in an official Treyarch doc, a stock script, stock data or the engine API list. `[COMMUNITY]` = forum, tutorial, video, another mapper, or a record from this project's own earlier map (Map One). `[INFERRED]` = reasoned, not seen. `[TEST]` = needs an in-game test. Statements about this repo's own files were read directly from those files and carry a `(src: …)` citation instead of a tag. Nothing in this chapter was tested in game. MODTOOLS means `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`.

**Words used for lighting states** (full story in [02 — Power and states](02_power_and_states.md)): "Radiant State N" is the light key `lightingstateN` (N = 1..4, what Radiant shows). "Script state n" is the argument of `util::set_lighting_state(n)`. Script state n shows Radiant State n+1 [INFERRED] (strongly supported by The Giant's data). Stock `zm_usermap::main` boots script state 1, which is Radiant State 2.

## Contents

1. [What a light is](#1-what-a-light-is)
2. [The three jobs of a light](#2-the-three-jobs-of-a-light)
3. [Every kind of light](#3-every-kind-of-light)
4. [Every key on a light](#4-every-key-on-a-light)
5. [Brightness: stops](#5-brightness-stops)
6. [Reach and shape](#6-reach-and-shape)
7. [How to make a dimmer light and how to size one](#7-how-to-make-a-dimmer-light-and-how-to-size-one)
8. [Colour and specular](#8-colour-and-specular)
9. [Shadows and the shadow budget](#9-shadows-and-the-shadow-budget)
10. [Bounce: bake_intensity_scale and PROBE_ONLY](#10-bounce-bake_intensity_scale-and-probe_only)
11. [Area lights (bulbLength)](#11-area-lights-bulblength)
12. [Cookies and gobos](#12-cookies-and-gobos)
13. [Volumetric lights](#13-volumetric-lights)
14. [Culling, LOD and limits](#14-culling-lod-and-limits)
15. [Lighting states and exploders on a light](#15-lighting-states-and-exploders-on-a-light)
16. [Script control of a light](#16-script-control-of-a-light)
17. [build_light](#17-build_light)
18. [spawnflags and hidden keys](#18-spawnflags-and-hidden-keys)
19. [What Treyarch does: The Giant](#19-what-treyarch-does-the-giant)
20. [Our generator's light()](#20-our-generators-light)
21. [For Tower of Doom II](#for-tower-of-doom-ii)
22. [Sources](#sources)

---

## 1. What a light is

**Plain version.** Think of a street lamp in a zombies map. What you see is a pole and a lamp head: that is a **model** (a `misc_model` or `script_model`). The lamp head looks bright because its lens uses a glowing (**emissive**) material, or because an effect sprite sits on it ([03](03_glow_and_perks.md), [04](04_fx_lights.md)). The pool of light on the street, the light on the zombie walking under it and the lamp's shadow come from a third thing you never see in game: a **light entity** placed inside the lamp head. Move the model and the light stays where it was. Delete the light and the lamp still "looks" on but throws no light onto the street.

**Treyarch builds lamps this way.** The Giant's hanging cage lamp geometry prefab (`map_source/_prefabs/zm/zm_giant/geo/zm_giant_light_cage_03.map`) contains only the shade, socket and small bulb models and no light. The lighting prefab `zm_giant_light.map` (543 lights) places that lamp prefab as a nested `misc_prefab` (73 cage lamps in all) and puts the light entities beside it as separate entities [VERIFIED]. The Level Design Book puts the same idea in one line: "A single fixture may actually motivate multiple invisible in-engine light sources" [COMMUNITY].

**One real lamp, several lights.** At one cage lamp in The Giant (light origin about `1551.8 -1830.4 1514`, where the prefab places a `geo/zm_giant_light_cage_03` lamp model) the prefab stacks these lights [VERIFIED] (parsed from `zm_giant_light.map`):

| Light at the lamp | Type | Radiant States 1-4 | stops (linear) | radius | Other keys | Its job |
|---|---|---|---|---|---|---|
| Powered pool | spot, `fov_outer 55` | 1 0 1 1 | 10.97 (≈2000) | 341 | `def gobo_spot_rings_001` (a ring-pattern cookie), `cut_on 22`, shadowed `Always`, `volumetric 1` (1 sample), `superellipse 0.1 1 0.1 1`, `roundness 1`, `culling 200/300`, `_color 1 0.7334 0.3922` | The lit floor pool once the power is on |
| Pre-power pool | same spot | 0 1 1 1 | 8.97 (≈500) | 341 | the same shaping, shadow, volumetric and culling keys, but no pattern (`def white_light`) | The same pool 2 stops dimmer, before power |
| Two probe copies | spot | 0 0 0 0 | 10.97 and 8.97 | 341 | `PROBE_ONLY 1`, notes `was_ssi_1` / `was_ssi_2` | Parked in no state |
| Bulb glow | omni, 27 units below | 0 0 0 0 | 6.64 (≈100) | 15 | no shadow, `falloffdistance 5`, `far_edge 0.75`, `culling 5/25` | Parked in no state |
| Shade light | spot, 29 units below, `angles 0 0 180`, `fov_outer 125` | 1 1 1 1 | 4.64 (≈25) | 16 | shadowed `Never`, `superellipse 0.05 1 0.05 1`, `falloffdistance 5`, `far_edge 0.75`, `culling 5/25` | A tiny always-on light at the bulb; that it lights the inside of the shade is [INFERRED] |

What a light that belongs to no lighting state does at bake or at runtime is not documented; The Giant parks 39 lights that way and the likely reading is "never lit" [INFERRED]. The pre-power/powered twin pattern is covered in [02 — Power and states](02_power_and_states.md#4-the-two-working-conventions).

**Where you place one.** In Radiant, from the Entity Browser under "unsorted > light" (not the separate `build_light`) [COMMUNITY] (Uptownpapi25). Radiant's F7/F8/F9 views are fullbright, baked ("real") lighting and game view [COMMUNITY]. In this repo nobody places lights by hand: `tools/gen_tower_map.js` emits all of them (section 20).

## 2. The three jobs of a light

| Job | Plain meaning | Keys that control it | Confidence |
|---|---|---|---|
| **Direct light** | The bright pool on floors, walls, players, zombies and the gun | `stops`, `_color`, `radius`, `ENABLE_FALLOFF`, `falloffdistance`, `cut_on`, `far_edge`, `PRIMARY_TYPE`, `fov_outer` | Keys [VERIFIED] (`bin/t7.def.json`). That the direct light is evaluated at runtime is [INFERRED]: it can be faded by screen size at runtime (Culling_LOD_Lights.pdf), switched by lighting state and exploder, and scripted |
| **Shadows** | Walls and objects block the light | `PRIMARY_NOSHADOWMAP`, `shadowUpdate`, `shadowmapScale`, `penumbraRadius`, `cull_dist` | [VERIFIED] (t7.def.json; Lighting_Parameters.pdf p.11) |
| **Bounce (GI)** | Soft reflected light and the colour it spreads, baked at lighting export | `bake_intensity_scale`, `PROBE_ONLY` | Descriptions [VERIFIED]: "Adjusts the brightness of a light for GI baking" and "this light will only be seen by the reflection probes" (t7.def.json). "Reflection probes ... provide both bounce lighting and reflections" (Probe/Reflection_Probes.pdf) |

The PBR slide deck describes the renderer as "Full HDR Lighting pipeline", "Global specular lighting in multiple, 256x256, blended reflection probes" and "GI lighting from point cloud diffuse bake" (src: docs_modtools/PhysicallyBasedRendering.pptx) [VERIFIED]. The probe grid that stores the bounce also lights moving objects such as players and zombies [INFERRED] (from Treyarch's 2016 talk; see [06](06_reflections_probes.md)). Whether any direct light is also baked onto world surfaces is not documented [TEST].

**Every light change needs a new lighting export.** "Lighting entities have been moved out of the BSPs ... When do you need to make a new LED? When Geo changes, or if Lighting has changed." (src: docs_modtools/Generate_LED.pdf) [VERIFIED]. In this repo the LED bake runs only in a FULL build; `-GscOnly` skips it, so every light edit is a full build (src: CLAUDE.md, tools/build_map.ps1).

## 3. Every kind of light

**Is there only one kind of light?** Almost. There is one placed light entity, `light`, with two shapes (omni and spot), plus a simplified `build_light`. Everything else that makes a map look lit is either a key on that entity (area tube, cookie, beam, probe-only, exploder, scriptable), a different system (FX lights, the sun, emissive materials, probes), or a sprite (corona, lens flare).

| Kind | What it is and when to use it | Defined in | More |
|---|---|---|---|
| **Omni light** (`PRIMARY_OMNI`) | Shines in every direction from one point: bare bulbs, fire, room fill. Doc: "Shines light in 360 and casts shadows (this option is very useful but can be expensive to shadow)" [VERIFIED] | t7.def.json `light`; Lighting_Parameters.pdf p.1 | Sections 5-9 |
| **Spot light** (`PRIMARY_SPOT`) | A cone: downlights, street lamps, searchlights, projected patterns. "Classic shadow casting spot-light" [VERIFIED] | same | Section 6 |
| **Area light** (`bulbLength` > 0) | Stretches the light source into a tube: fluorescent tubes, neon strips [VERIFIED] (the key; the look is [TEST]) | t7.def.json | Section 11 |
| **`build_light`** | A simplified light for blocking out a level; static shadows; can be left out of the lighting export [VERIFIED] | Build_light.pdf; t7.def.json `build_light` | Section 17 |
| **PROBE_ONLY light** | Seen only by the reflection probes: adds bounce/fill colour and shows in reflections without a visible direct pool [VERIFIED] (def; the effect is [INFERRED]) | t7.def.json | Section 10 |
| **Exploder light** | A primary light put into a named Radiant exploder group so script can switch it on and off [VERIFIED] | Radiant Exploder Manager; `share/raw/scripts/shared/exploder_shared.gsc/.csc` | Section 15; [02](02_power_and_states.md) |
| **Scriptable light** | A light exposed to script (`scriptable` + `client_server ServerSide`) for `SetLightIntensity` and friends [VERIFIED] (API; no stock use) | t7.def.json; bo3_scriptapifunctions.htm | Section 16 |
| **FX dynamic light** | A light element inside an `.efx` effect: flicker, pulses, moving lights, lights you spawn from script. Cannot use `Never` shadows [VERIFIED] | FX_Lights.pdf; `deffiles/lightdescription.awi` | [04 — FX lights](04_fx_lights.md) |
| **Sun and sky light** | The global light from the `volume_sun` SSI (sun) and the sky material, one set per lighting state [VERIFIED] | SunSky_Light_SetUp.pdf | [05 — Sun, sky, exposure, fog](05_sun_sky_exposure_fog.md) |
| **Emissive surfaces** | Materials that look lit (screens, neon, perk "on" skins). No doc, material field or `lit_emissive` render flag was found that makes such a surface a light source in the bake [INFERRED] (from a search of the docs and techsets); the sky material is the one documented emissive light source [VERIFIED]. Whether probe-captured emissive feeds bounce is [TEST] | Materials.pdf | [03 — Glow and perks](03_glow_and_perks.md#4-does-an-emissive-surface-light-up-the-room) |
| **Lampshade / backlit materials** | "meant to be used with a light placed behind them to provide the actual glow", which "makes switching lights on and off easier" [VERIFIED] (Materials.pdf p.17) | Materials.pdf | [03](03_glow_and_perks.md) |
| **Reflection probes** | Store bounce light and reflections; not light sources themselves [VERIFIED] | Probe/Reflection_Probes.pdf | [06 — Reflections and probes](06_reflections_probes.md) |
| **`info_corona`** | A glare sprite around a light: `radius` (default 20), `color`, `intensity` 0..1; material from worldspawn `coronamaterial`. cod2map has a cap ("More than %i light coronas"), value unknown [VERIFIED] | t7.def.json | [04](04_fx_lights.md) |
| **`lensflare`** | Places a lens flare asset (`assetname`) [VERIFIED] | t7.def.json | [04](04_fx_lights.md) |
| **Cookie / gobo** | A texture projected through a light (`def` = a `light` asset) [VERIFIED] | t7.def.json; `deffiles/light.awi` | Section 12 |
| **Volumetric beam** | A visible shaft of light in lit fog (`volumetric 1` + a `volume_litfog`) [VERIFIED] | t7.def.json | Section 13 |
| **Lighting states** | Four global light setups swapped by script, e.g. power off / on [VERIFIED] | Lighting_Parameters.pdf p.10 | [02](02_power_and_states.md) |

`PRIMARY_DIR` (a directional light) exists in the FX `lightdescription` asset and in cod2map strings, but the Radiant `light` entity's type list is only `PRIMARY_OMNI,PRIMARY_SPOT`, so you cannot place one [VERIFIED].

## 4. Every key on a light

Source for every row: `MODTOOLS/bin/t7.def.json`, entry `"classname": "light"` [VERIFIED], with doc text from `docs_modtools/Lighting_Parameters.pdf` where it adds something. Units: 1 Radiant unit = 1 inch (src: Scale_Standards.pdf) [VERIFIED]. Where the PDF and the def disagree, the def is what Radiant uses today; both are noted.

| Key | Group | Type / range | Default | What it does (plain) |
|---|---|---|---|---|
| `origin` | | vec3 | | Position |
| `angles` | | vec3 | 0 0 0 | Rotation; aims a spot (Radiant rotate handles: select and press R, per Build_light.pdf) |
| `target` | | string | | Name of an entity the spot points at. Def: "A light pointed at a target will be a spotlight facing the target. They default to having a circle with 64 unit radius around the target." |
| `PRIMARY_TYPE` | LIGHT TYPE | `PRIMARY_OMNI` / `PRIMARY_SPOT` (spawnflag 2 / 4) | OMNI | Point or cone |
| `PRIMARY_NOSHADOWMAP` | LIGHT TYPE | bool (spawnflag 16) | **true** | "Prevents a primary light from ever having a shadowmap." Shadows are OFF by default |
| `PROBE_ONLY` | LIGHT TYPE | bool | false | "If enabled this light will only be seen by the reflection probes" |
| `NO_CULL` | LIGHT TYPE | bool | false | "will not calculate a culling volume" |
| `_color` | INTENSITY | colour | 1 1 1 | Colour of the light |
| `stops` | INTENSITY | float −32..32, step 0.1 | **11** | "Controls how bright a light is." Doc: "Lighting units are in stops" |
| `bake_intensity_scale` | INTENSITY | float 0..100 | 1 | "Adjusts the brightness of a light for GI baking." (section 10) |
| `spec_comp` | INTENSITY | float −14..14, step 0.25 | 0 | "Specular boost (in stops)": the shiny highlight the light makes |
| `fov_outer` | SHAPING | 0..180 degrees | 90 | Full cone angle: 90 = ±45°. Doc: above 120° "tend to suffer from artifacts and low-res shadows" |
| `ENABLE_FALLOFF` | SHAPING | bool (spawnflag 64) | true | Turns distance fading on |
| `falloffdistance` | SHAPING | 0..100000 | 12 | "Distance at which inverse square distance attenuation starts to take effect" |
| `cut_on` | SHAPING | 0..65504 | 0 | Distance from the origin where the light starts, so the origin can sit inside a lamp model |
| `radius` | SHAPING | 0..65504 | 100 | "Controls the distance at which the light will end" |
| `near_edge` | SHAPING | 0..1 | 0 | Softness of the start at `cut_on` (doc: 0 hard, 1 very soft) |
| `far_edge` | SHAPING | 0..1 | 0.95 | Fade at the far end. Doc: "1 ... hard edge ... 0 would give a very long fade"; def calls it a "width" (section 6) |
| `min_light_cutoff` | PERFORMANCE | 0..100000 | 0 | Radiant computes the radius from a minimum intensity. Doc: "A value of 100 would result in the radius being positioned at the distance from the light where the intensity hit 100" |
| `cull_dist` | PERFORMANCE | 0..100000 | 0 | "Distance at which the light stops casting a run-time shadow" |
| `bulbLength` | SHAPING | 0..1000 | 0 | "Controls the length of the light bulb of an area light" |
| `roundness` | SHAPING | 0..1 | 0.5 | Spot cross-section: 0 rectangle, 1 circle |
| `superellipse` | SHAPING | vec4, each 0.05..1 | 0.75 1.0 0.75 1.0 | Spot shape and edge softness: inner/outer width, inner/outer height (doc p.4-7 has pictures) |
| `ortho_effect` | SHAPING | 0..1 | 0 | "Creates an orthographic effect for spot lights" |
| `def` | COOKIE | name of a `light` asset | none in def; doc says `white_light` | The cookie (projected texture) |
| `def_tile` | COOKIE | vec2 | 1 1 | How many times the cookie repeats across the beam |
| `def_offset` | COOKIE | vec2 −1..1 | 0 0 | Shifts the cookie |
| `def_shear` | COOKIE | vec2 −5..5 | 0 0 | Shear; the def's description text is a copy of `def_offset`'s, so its exact effect is [TEST] |
| `def_angle` | COOKIE | −360..360 | 0 | Static rotation of the cookie |
| `def_center` | COOKIE | vec2 −1..1 | 0 0 | Centre of rotation |
| `def_scroll` | COOKIE | vec2 −10..10 | 0 0 | Animated scroll: "a time in seconds which is how long it will take for the texture to travel across the full width / height" |
| `def_rotation` | COOKIE | −720..720 | 0 | Animated rotation. Def: degrees per second. Doc: seconds per full turn. They disagree |
| `lightingstate1`..`4` | LIGHTING_STATES | bool | **true** each | Which Radiant States this light exists in (section 15) |
| `volumetric` | LIGHTING | bool | false | "Enables rendering of light as volumetric" (a visible beam) |
| `volumetricCookies` | LIGHTING | bool | false | "Enables cookies on volumetrics" |
| `volumetricSampleCount` | LIGHTING | int 1..24 | 8 | "Number of ray march samples used in calculating volumetrics for light" |
| `volumetricIntensityBoost` | LIGHTING | −14..14 stops | 0 | Beam-only brightness |
| `shadowUpdate` | SHADOWS | `AlwaysNoCache` / `Always` / `Never` | **Never** | Def: "Only render the shadowmap once when missing." |
| `excludeDedicated` | SHADOWS | On / Off | Off | "Disable the dedicated shadow for a light set as never update" |
| `shadowmapScale` | SHADOWS | 4 / 2 / 1 / 0.5 | 1 | Shadow resolution (1 = 512×512); not supported on omni lights (doc p.11) |
| `penumbraRadius` | SHADOWS | 1..128 px | 1.5 (def) / 3 (doc) | Shadow softness: "Larger number creates softer shadows. High values will result in some performance loss" |
| `culling_use_pure_radius` | LOD | bool | false | "For spot lights, ignore the cone angle and use the radius as a diameter for the enclosing sphere" |
| `culling_falloff` | LOD | ≥0 px at 1080p | 0 | Fade starts when the light's on-screen radius drops below this |
| `culling_cutoff` | LOD | ≥0 px at 1080p | 0 | Light (and its shadow) is clipped below this |
| `targetName` | Scripting | string | | Script name (the def spells it `targetName`) |
| `scriptable` | Scripting | bool (spawnflag 8) | false | "Makes a light show up as an entity to script. NOTE: default is client side so you must choose the server side drop down to grab on the server." |
| `client_server` | Scripting | `ClientSide` / `ServerSide` (spawnflag 0 / 32) | ClientSide | Which script VM can see a scriptable light |
| `name` | | string | light | "used to identify a light" |

## 5. Brightness: stops

**Plain version.** Photographers count light in "stops": one stop more is twice the light, one stop less is half. BO3 lights use the same unit. So `stops 7` is twice as bright as `stops 6`, and `stops 4` is a quarter of `stops 6`.

**The evidence.**
- The doc says "Lighting units are in stops. Default Value: 11" (Lighting_Parameters.pdf p.1) [VERIFIED], and Radiant's UI has the strings "Light Intensity (in Stops)" and "+3 Stops" (Radiant_modtools.exe) [VERIFIED].
- Treyarch's own values are exact base-2 logarithms of round numbers. In The Giant, 405 of the 489 non-whole `stops` values satisfy "2 to the power stops is a whole number": 4.6439 = log2 25, 5.6439 = log2 50, 6.6439 = log2 100, 7.9658 = log2 250, 8.9658 = log2 500, 9.9658 = log2 1000, 10.9658 = log2 2000 [VERIFIED]. The old linear `intensity` field was clearly converted with log2. No official text states "+1 stop = 2×", so the rule is [INFERRED], strongly supported.

| stops | linear (2^stops) | stops | linear |
|---|---|---|---|
| 0 | 1 | 7 | 128 |
| 3.32 | 10 | 7.97 | 250 |
| 4.64 | 25 | 8.97 | 500 |
| 5.64 | 50 | 9.97 | 1000 |
| 6 | 64 (every Tower II light today) | 10.97 | 2000 |
| 6.64 | 100 | 11 | 2048 (the default) |

`stops -32` is 2^-32, effectively off; one stock light in The Giant and one in mp_sector sit at −32, kept in the map but muted [VERIFIED].

**Brightness only means something against exposure.** Exposure is the game's camera setting, measured in EV. An EV number describes how bright the place is: Treyarch's MP doc treats a sunlit exterior as about EV 12 and the Materials doc uses "an interior at EV 3" as its example [VERIFIED]. The higher the EV the camera is set for, the darker a given light looks [INFERRED] (from the Materials doc's 2^EV rule for emissive brightness, see [03](03_glow_and_perks.md)). So a light that looks blinding at a night exposure can be invisible at a daylight one. Stock pairs [VERIFIED] (data; the conclusion is [INFERRED]):
- MP maps expose at EV 8-12 ("Exposure will ALWAYS be set within the range of 8 - 12 stops", Multiplayer_Lighting_Workflow.pdf), and mp_sector's lights sit at a median of **15** stops.
- The Giant's worldspawn sets `evmin 3`, `evmax 3.5`, `evcmp 2.5` (src: map_source/zm/zm_giant.map); its exposure volumes use `evmin 0.5`, `evmax 3.5`, `evcmp 3.75-4.87`; and its lights sit at a median of **7** stops (p10 4.0, p90 10.6).
- Community rule of thumb: on a day SSI lights need about 14 stops to show; on a night map about 1 [COMMUNITY] (modme 477).

Set the exposure for a dark map first, then tune lights against it; exposure is covered in [05 — Exposure](05_sun_sky_exposure_fog.md#5-exposure). Tower II's SSI `tod_ssi_cybercity` carries stock `default_night`'s exposure values, `evmin 3`, `evmax 3.5`, `evcmp 2.5` (src: source_data/tod_skybox.gdt), the same numbers as The Giant's worldspawn [VERIFIED]; how SSI, worldspawn and volume exposure values combine is not documented. Every Tower II light is at stops 6: one stop under The Giant's median and 5 stops (1/32) under the def default [INFERRED] (arithmetic, if +1 stop = 2×).

## 6. Reach and shape

### Radius: where the light ends

`radius` is a hard cut-off distance in inches, not a brightness. With falloff on, a bigger radius mostly adds a long, dim tail and makes the light cover more of the screen, which costs more [INFERRED]. The Giant's radii: p10 15, p25 20, median 150, p75 250, p90 350 [VERIFIED]. Many Treyarch lights are 15-20-unit bulb glows. Tower II's are 200-900, median 420 (src: map_source/zm/zm_tod2_cybercity.map).

### Falloff: how fast the light fades

`ENABLE_FALLOFF 1` turns on "inverse square distance attenuation", which "starts to take effect" at `falloffdistance` [VERIFIED]. The formula is not documented. A model consistent with that wording [INFERRED]:

- up to `falloffdistance`, the light is about 2^stops;
- beyond it, about 2^stops × (falloffdistance / distance)²;
- `far_edge` then fades it to zero by `radius`.

Two rules of thumb follow from the inverse-square wording [INFERRED]:
1. **Twice as far = a quarter of the light = −2 stops.** To light something twice as far away equally well, add 2 stops.
2. **`falloffdistance` is a brightness knob at range.** Doubling it (12 → 24) gives 4× (+2 stops) everywhere beyond 24 units. Treyarch uses 12 on 315 Giant lights, 5 on 102 (small bulb glows whose light should die fast) and 0.75 on 36 (indicator lamps) [VERIFIED].

`ENABLE_FALLOFF 0` removes the inverse-square fade. The Giant uses that for its moonlight: spots about 40,000 units away with radius 12,000-22,000, which gives an even, near-parallel wash (section 19) [VERIFIED] (data; the "even wash" is [INFERRED]).

A worked comparison under this model [INFERRED] (arithmetic; cone, `cut_on` and exposure ignored): a Tower II base light hangs 240 units above the floor; at stops 6 (= 64) with falloff 12 it gives about 64 × (12/240)² ≈ 0.16 there. The Giant's powered cage-lamp pool (stops 10.97 ≈ 2000, the same falloff 12) gives about 5 at the same 240 units, which is simply the 5-stop difference in `stops`, and about 29 at 100 units.

### cut_on and near_edge: where the light starts

`cut_on` is "useful when you want to bury the origin of a light inside of a prop but want the effects of the light to start later" (doc p.2) [VERIFIED]. Put the origin at the bulb and set `cut_on` so the light starts just outside the shade or housing; otherwise the lamp's own model catches (and shadows) the light. The Giant sets `cut_on` on 242 lights; the pool spots at its cage lamps use 16-26 [VERIFIED]. Community tutorials use about 8-12 for small lamps [COMMUNITY] (VerK0, Program115). `near_edge` softens that start: "0 give you a hard edge at the start of your light, a value of 1 would give you a very soft transition" [VERIFIED].

### far_edge: the fade at the end

The doc (p.2-3) and the def disagree about what the number means [VERIFIED]:
- Doc: "A value of 1 will give you a hard edge at the end of your light if your radius is too small for the falloff / intensity you have created. A value of 0 would give a very long fade at the end of the light." It adds that the ideal is a large-radius light with falloff, and `far_edge` is for "tastefully" fading a light whose radius had to be kept small for performance.
- Def: "Define the width of the transition region for cut-off, valid value is between 0.0 and 1.0 which is mapped to equal the cuton and radius(cutoff) range."

Reading `far_edge` as "the fraction of the range where the fade begins" fits the doc (0.95 = fade in the last 5%, 0 = fade over the whole range) [INFERRED]. Treyarch's values: 0.75 (144 lights), 0.95 (122), 0.25 (102), 0.5 (67), 0.1 (40) [VERIFIED]. The community lowers it to about 0.1 to soften a harsh cut-off [COMMUNITY] (VerK0), which also fits the doc reading.

### min_light_cutoff: let Radiant pick the radius

`min_light_cutoff` computes the radius from the intensity you want at the edge, "dependent on ENABLE_FALLOFF and falloffdistance" [VERIFIED]. Under the model above the radius would be about falloffdistance × √(2^stops / cutoff); for stops 6, falloff 12 and cutoff 1 that is about 96 units [INFERRED]. Treyarch never sets it in The Giant and uses it on only 2 mp_sector lights (value 25) [VERIFIED]. Check the result in Radiant before relying on it [TEST].

### Spot shape: fov_outer, roundness, superellipse, ortho_effect

- `fov_outer` is the full cone angle. Keep it at or below 120° (doc p.2) [VERIFIED]. Giant spots mostly use 50, 55, 60, 65, 75 and 90; ten use 125 [VERIFIED]. For two wide pools, use two spots.
- `roundness`: 0 = rectangular cross-section, 1 = circle [VERIFIED]. The Giant uses 1 on 318 lights [VERIFIED].
- `superellipse` (four numbers): "The first two values control the inner and outer length of the spot-shape. The second two numbers control the inner and outer height" (doc p.4) [VERIFIED]. Lowering the inner values feathers the edge: The Giant's hanging-lamp pool uses `0.1 1 0.1 1` with `roundness 1` [VERIFIED], which by the doc's description gives a very soft round pool [INFERRED]. An mp_sector fluorescent spot uses `0.14 0.21 0.9 1`, narrow in one direction, to make a strip [VERIFIED] (the values; the strip look is [INFERRED]). The community lowers the inner values (0.75 → 0.1) to feather [COMMUNITY] (VerK0).
- `ortho_effect`: "Creates an orthographic effect for spot lights" [VERIFIED]; The Giant uses 0.2-0.35 on 14 lights, including its tesla-coil beams [VERIFIED]. The community describes it as widening the point the cone starts from [COMMUNITY].

### Aiming a spot

Use `angles` (Radiant rotate handles, R) or `target`. 98 of The Giant's 263 spots, including the hanging-lamp pools that light the floor, carry neither `angles` nor `target` [VERIFIED], so an unrotated spot most likely points straight down [INFERRED]. Check the cone in Radiant's camera view rather than typing angles by hand [INFERRED].

## 7. How to make a dimmer light and how to size one

### Making a light dimmer

There is no separate "dim light" type. Dimness is set with these levers, in rough order of preference [INFERRED]:

| Lever | Effect | Notes |
|---|---|---|
| Lower `stops` | −1 = half, −2 = quarter, −3 = eighth | The main knob. At The Giant's cage lamps the pre-power twins sit 0.4-2 stops (most often 1-2) under their powered copies [VERIFIED] (data) ([02](02_power_and_states.md#4-the-two-working-conventions)) |
| Lower `falloffdistance` | Dimmer everywhere past the new value (12 → 6 ≈ −2 stops at range) [INFERRED] | Treyarch uses 5 for small glows |
| Smaller `radius` | Removes the dim tail; the core stays the same | Also cheaper |
| Lower `far_edge` | Longer, softer fade toward the edge | Softer, not dimmer at the core |
| Negative `spec_comp` | Weaker shiny highlight; the diffuse light stays | Useful on reflective materials (section 8) |
| `PROBE_ONLY 1` | No direct pool at all, only baked fill and reflection | The dimmest "light" that still tints a room (section 10) |
| Darker `_color` | Probably dims, since the colour multiplies the light [INFERRED] | Stock practice keeps the brightest channel at 1 and dims with `stops` (section 8) |
| Exposure | Darkens or brightens everything at once | [05](05_sun_sky_exposure_fog.md); not a per-light tool |
| `bake_intensity_scale` below 1 | Dims the baked bounce; whether the direct pool also changes is [TEST] | Section 10 |
| Runtime `SetLightIntensity` | Script dimming of a scriptable light | Untested; see section 16 |

### Sizing a light, step by step

1. **Decide what it must light.** A pool on the floor, one wall, a whole small room, a bulb's own glow.
2. **Pick the shape.** A spot for a pool from above (downlight, street lamp, spotlight). An omni for a bulb hanging in space, fire, or room fill.
3. **Spot cone.** `fov_outer ≈ 2 × atan(pool radius / height)`. Example: a lamp head 160 above the floor lighting a pool 240 across gives 2 × atan(120/160) ≈ 74°, so use 75 [INFERRED].
4. **Radius.** Distance from the light to the farthest surface it should reach, plus a little. In the example, the slant distance to the pool edge is √(160² + 120²) = 200, so a radius of about 220-250. Compare the 64 pool spots at The Giant's cage lamps: radius 134-420, `fov_outer` 50-84, `cut_on` 16-26, many with an IES-profile or ring cookie (`cuc_ies_029`, `cuc_ies_cust_02`, `cuc_ies_017`, `gobo_spot_rings_001`) [VERIFIED]. For an omni with no shadows, keep the radius inside the room, or the light passes through the walls and floors (section 9).
5. **Start and end.** `cut_on` just past the housing; `far_edge` 0.5-0.75 for a softer end (0.75 is The Giant's most common value).
6. **Brightness.** Set `stops` for the level you want at the working distance. Use "twice as far = +2 stops" to move between distances [INFERRED].
7. **Shadows.** Turn shadows on (`PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`) if the light is near a wall it must not pass (section 9).
8. **LOD.** `culling_cutoff 200` / `culling_falloff 300` for normal lights; `5/25` (Treyarch) or `1/5` (doc) for tiny ones (section 14).
9. **Preview** in Radiant F8, then full build. In this repo: change the generator, regenerate, full build, and the user judges it in game.

## 8. Colour and specular

- `_color` is an RGB colour, 0..1 per channel [VERIFIED]. **No stock light has a channel above 1**, and The Giant keeps the brightest channel at exactly 1 on 505 of its 543 lights, putting brightness in `stops` [VERIFIED]. mp_sector has more colours below 1 (163 of 275) [VERIFIED]. Our generator's `tintLight()` follows the same rule: it renormalises a colour to a maximum of 1 and moves any overflow into `stops` (src: tools/gen_tower_map.js:7154-7165; `LIGHT_TINT` is `null`, i.e. off, at :1898).
- Treyarch's warm lamp colour is about `1 0.73 0.39`; fire about `1 0.36 0.16`; moonlight `0.75 0.85 0.85` [VERIFIED].
- `spec_comp` is a per-light "Specular boost (in stops)", −14..14 [VERIFIED]. The Giant sets −1 to −6 on 38 lights; mp_sector sets −10 once [VERIFIED]. The community fix for lights that make everything look like "shiny plastic" is a negative `spec_comp` such as −10 [COMMUNITY] (modme 293). This matters in Tower II because the Vertigo world materials are mirror-like (`reflectionProbeAmount 1`, high gloss, white specular; see CLAUDE.md and [03](03_glow_and_perks.md)), so a light's highlight on those surfaces may read strongly [INFERRED].

## 9. Shadows and the shadow budget

**Plain version.** A light without a shadow map does not know walls exist. It lights everything within its radius, including the other side of a wall, the floor above and the floor below. Turning shadows on makes walls block it, at a cost.

- **Shadows are opt-in.** `PRIMARY_NOSHADOWMAP` defaults to true, "Prevents a primary light from ever having a shadowmap" [VERIFIED]. Mappers report shadowless lights "bleeding" through walls (a house light lighting the grass outside), fixed by setting `PRIMARY_NOSHADOWMAP` to false [COMMUNITY] (modme 2987 confirmed; modme 304, UGX 14935). Treyarch turns shadows on for 353 of The Giant's 543 lights, and for 110 of mp_sector's 275 [VERIFIED].
- **`shadowUpdate`** (def default `Never`; the def's description for the key is "Only render the shadowmap once when missing") [VERIFIED]:
  - `Never`: the shadow map is drawn once and cached, a static shadow [INFERRED] (from the description). For build lights the doc says static shadows come "only from static objects. Dynamic objects will receive shadows from these lights but you will not see live shadows cast from things like characters" (Build_light.pdf) [VERIFIED]; the same most likely holds for `Never` on a regular light [INFERRED], and the player option `ActorShadows`, "Number of lights with otherwise static shadows to force characters shadows on", fits that reading [INFERRED]. Cheap.
  - `Always`: a live shadow updated as things move, so characters and movers cast shadows [INFERRED] (from the name and the budget doc). Expensive.
  - `AlwaysNoCache`: in the enum; undocumented.
- **The budget** (Lighting_Parameters.pdf p.11) [VERIFIED]: "default value is 512x512, (scale 1) ... Scale 2 = 1024x1024. Setting the scale to double res will eat 4 times the shadow maps. At normal res we can update 12 live shadows, with double res you could update 3 live shadows. Conversely you could do 4x as many shadows at half-scale. Shadowmap Scale is not currently supported on omni-lights." Also: "PCSS is currently disabled due to performance constraints."
- **How the engine picks which lights get live shadows.** cod2map carries the dvar help text "When picking shadows for primary lights, measure distance from a point this far in front of the camera" (`sm_lightScore_eyeProjectDist`) and a spot variant (`sm_lightScore_spotProjectFrac`) [VERIFIED]. So many lights can be marked `Always` (The Giant has 198 shadowed `Always` lights and 155 shadowed `Never`) while only the budgeted number, those scored nearest the camera, update live at any moment [INFERRED].
- **`volume_performance`**: `maxDynamicShadows` default 12, range 0..24, and `sunShadowSplitCount` default 3 [VERIFIED]. That this 12 is the doc's "12 live shadows" is [INFERRED]. Its lighting-state flags default to `LIGHTSTATE_1` only, so in a zombies map that boots Radiant State 2 a volume placed with default flags would be inactive unless `LIGHTSTATE_2` is ticked [INFERRED] (from the def and the state mapping) [TEST].
- **Omni versus spot.** The doc: omni "can be expensive to shadow" [VERIFIED]. The worldspawn sizes the shadow atlases: `numSpotShadowSlices` default 64 (8..1024) and `numOmniShadowSlices` default 24 (8..256) [VERIFIED]; The Giant uses 64 / 24 [VERIFIED], and so does Tower II (src: map_source/zm/zm_tod2_cybercity.map worldspawn). An omni shadow needs a cube of six views, which is why it costs more [INFERRED].
- **`penumbraRadius`**: softness in pixels; def default 1.5, doc default 3 ("High values will result in some performance loss") [VERIFIED]. The Giant uses 3 on 504 lights [VERIFIED].
- **`cull_dist`** stops the runtime shadow beyond a distance; **`excludeDedicated`** drops the per-model "dedicated shadow" for a `Never` light [VERIFIED]. Script has `SetDedicatedShadow` and `GiveDedicatedShadow` [VERIFIED]. Both keys are rare in stock data: The Giant sets `excludeDedicated On` on 1 light and `cull_dist` on none; mp_sector sets `excludeDedicated On` on 2 and `cull_dist 12` on 2 [VERIFIED].
- **FX lights** "do not have the ability to use 'Never' shadows. They are either Always live, or Off. This will blow your shadow budget very quickly" (FX_Lights.pdf) [VERIFIED]. Give FX lights `PRIMARY_NOSHADOWMAP 1`, as 88% of stock FX light blocks do [VERIFIED] (count of `share/raw/fx`); see [04 — Shadows on FX lights](04_fx_lights.md#7-shadows-on-fx-lights).
- **Shadow-shaping brushes.** The Giant's light prefab contains 11 brushes textured `shadowcaster` (5 of them on the layer `000_Global/Shadow_casters`, mostly `contents nonColliding`) and 12 textured `caulk_sun_shadow` [VERIFIED]. All three tool materials `shadowcaster`, `caulk_shadow` and `caulk_sun_shadow` exist in the stock GDTs (`texture_assets/code.gdt`, `tools.gdt`) [VERIFIED]. That they are invisible occluders that shape light and sun shadows is [INFERRED] (from the names). The community puts `caulk_shadow` brushes behind thin walls for the same purpose [COMMUNITY]; one mapper reports it did not stop a light bleeding until the light's `PRIMARY_NOSHADOWMAP` was set to false (modme 2987) [COMMUNITY], which fits: a light with no shadow map ignores every occluder [INFERRED].
- **The `shadowUpdate_was_Always` note.** 109 Giant lights carry it [VERIFIED], but 102 of those still have `shadowUpdate Always` and only 7 are `Never` [VERIFIED], so the note does not record a switch to static shadows. Its meaning is unknown.

**What players can turn off.** BO3's `players/config.ini` has `DisableDynamicLightShadows`, `DisableDynamicSunShadows`, `SpotShadowTextureSize` (128-8192), `OmniShadowTextureSize` (128-2048), `ShadowFiltering` and `ActorShadows` ("Number of lights with otherwise static shadows to force characters shadows on", 0-16) [VERIFIED]. The user's own config has `DisableDynamicLightShadows 1`, `DisableDynamicSunShadows 1`, `SpotShadowTextureSize 512`, `OmniShadowTextureSize 256` and `ActorShadows 0`, so the user's playtests will not show live light shadows. Whether `DisableDynamicLightShadows` also removes cached `Never` shadows is [TEST]. Judge shadows on both a low and a high config ([09 — two graphics configs](09_design_and_inspiration.md#73-judge-on-two-graphics-configs)).

## 10. Bounce: bake_intensity_scale and PROBE_ONLY

### bake_intensity_scale

- Def: "Adjusts the brightness of a light for GI baking." 0..100, default 1 [VERIFIED]. `stops`, by contrast, "Controls how bright a light is" [VERIFIED].
- Treyarch never sets it: 0 of 543 Giant lights and 0 of 275 mp_sector lights [VERIFIED].
- **What it does NOT do is unproven.** That it leaves the runtime direct pool unchanged is [INFERRED] from the wording; no source says so either way.
- This matters for Tower II: the generator calls `bake_intensity_scale` "THE ONLY REAL BRIGHTNESS KNOB IN THE BASE" and uses 1.35 on the 24 lights of the base plaza, the Undercity (Vault, Conduit, shaft) and the workshop wings (src: tools/gen_tower_map.js:7187-7201, 7324-7350). Map One also used it as its dim/bright control (0.02 / 1.3, all at stops 6) and its users reported visible changes [COMMUNITY] (project record). Those reports fit either reading, because bounced light is visible too. If it is a linear multiplier, 1.35 is about +0.43 stop of bounce [INFERRED].
- **Settle it with one A/B test [TEST]:** two identical lights in a test room, one at `bake_intensity_scale 0`, one at 1, same `stops`; compare the direct pools in game.
- Until then: use `stops` for brightness, and treat `bake_intensity_scale` as a bounce-only adjustment.

### PROBE_ONLY

- Def: "If enabled this light will only be seen by the reflection probes" [VERIFIED]. Probes carry bounce light and reflections [VERIFIED], so a probe-only light adds soft baked fill and colour, and shows up in reflections, without drawing a direct pool [INFERRED].
- The Giant has 149 of them (112 on in all four states; radius median 250, range 40-700) [VERIFIED]. Its hurricane lanterns pair a probe-only fill with a small direct light (section 19), and 67 of its 94 placed light FX have a probe-only light within 12 units ([04 — the Giant pattern](04_fx_lights.md#11-the-giant-pattern-fx-light-plus-a-probe_only-twin)).
- Community use: a purple probe-only light for a coloured perk room "with no light source to be seen" [COMMUNITY] (VerK0, 47 Berkerly Lane).
- It only works where probes cover the space, and it is baked: every change is a full build [INFERRED]. Tower II's probes are 144-unit cubes today, so fitting probes comes first ([06](06_reflections_probes.md)).

## 11. Area lights (bulbLength)

- `bulbLength` "Controls the length of the light bulb of an area light", 0..1000 [VERIFIED]. A value above 0 stretches an omni's source into a tube.
- Stock example (mp_sector) [VERIFIED]: 8 lights carry the key, but only 2 use a real tube; the other 6 have `bulbLength 0.01`. The tube: omni, `bulbLength 28.5`, `radius 5`, `stops 13`, `angles 270 0 0`, no shadow, `_color 1 0.9198 0.8549`, plus the hidden key `bulbRadius 2`. The Giant uses none.
- The tube's direction presumably follows `angles` [INFERRED]. How `radius` is measured for a tube (from the centre or from the tube surface; the example's `radius 5` is tiny next to a 28.5 tube) is undocumented [TEST].
- Community use: neon strips and fluorescent tubes; for long runs, several weak lights rather than one strong one [COMMUNITY] (VerK0, Program115).
- Stock MP also fakes a fluorescent with a narrow spot: `superellipse 0.14 0.21 0.9 1`, `cut_on 21`, `radius 22.5`, `stops 14`, shadowed `Never` [VERIFIED]. The look of both is [TEST]. Recipes: [08](08_fixture_cookbook.md).

## 12. Cookies and gobos

**Plain version.** A cookie (also called a gobo) is a black-and-white picture the light shines through, like a stencil in front of a theatre light: window blinds, a grate, a ring pattern, water ripples. Animate it and you get flicker or moving caustics without an FX light.

- **The asset.** `def` names an asset of type `light` [VERIFIED]. That asset has ONE field, `cookieImage` (src: `MODTOOLS/deffiles/light.awi`) [VERIFIED]. "These entries are created in APE" (doc p.8) [VERIFIED].
- **Stock cookies (21)** [VERIFIED] (`MODTOOLS/texture_assets/*.gdt`):

| GDT | Cookie names |
|---|---|
| `t6_lights.gdt` | `white_light` (plain, the doc's default), `gobo_smoke_01` |
| `t7_light_gobo.gdt` | `truck_head_lights`, `cookie_flicker`, `cookie_flicker02`, `cookie_caustic_ink`, `cookie_caustics_01`, `cookie_caustics_layered`, `cookie_sun_mp_apartments`, `cuc_black`, `cuc_fov70_pen30`, `cuc_grey_01`, `cuc_ies_006`, `cuc_ies_017`, `cuc_ies_026`, `cuc_ies_029`, `cuc_ies_cust_02`, `cuc_plazma_falloff`, `cuc_smooth_180`, `cuc_white`, `gobo_spot_rings_001` |
| `t7_cookie.gdt` | `cookie_mrt512_r100_e075_100_075_100`, `cookie_mrt512_r100_e010_100_010_100` |

  The `cuc_ies_*` images (files `ies_cuc_*.tif`) are presumably real light-fixture beam profiles (IES), useful for street lamps and downlights [INFERRED] (from the names). The Giant also references `cuc_grey_05`, which no GDT in the Mod Tools defines [VERIFIED]: stock maps can use assets the Mod Tools do not ship.
- **Image rules.** All 21 stock cookie images (`texture_assets/lights/*.tif`) are 512×512 RGB TIFFs [VERIFIED]. Radiant has the errors "COOKIE LightDef '%s' doesn't have the correct size (%ix%i)", "COOKIE LightDef '%s' can't find associated image '%s'" and "COOKIE Lightdef '%s' not found in GDT" [VERIFIED]. So 512×512 is the safe size [INFERRED]; an internal `cookieIndex` assert suggests at most 256 cookies [INFERRED].
- **Spots, mostly.** 60 of The Giant's 62 cookie lights are spots [VERIFIED].
- **`ENABLE_COOKIE` is stale.** The doc says to set it to true (p.11), but the key does not exist in Radiant, cod2map, the linker or any stock prefab; stock lights project a cookie with `def` alone [VERIFIED] (absence; the meaning is [INFERRED]).
- **Animated cookies.** `def_scroll` and `def_rotation`. Treyarch examples [VERIFIED]:
  - tesla-coil flicker: `def cookie_flicker02`, `def_tile 0.04 0.04`, `def_scroll 0.7 0.7`;
  - water caustics: `def cookie_caustics_01`, `def_scroll 0.05 0.1`, `def_rotation -0.1`.
  A tiny `def_tile` means the whole beam samples a small patch of the texture, so the pool reads as one brightness that changes over time as the texture scrolls, i.e. a flicker [INFERRED]. The community trick is the same: tile about 0.001 in one axis and scroll [COMMUNITY] (VerK0). Both texts describe `def_scroll` as "seconds to cross the full width" (smaller = faster), yet Treyarch uses 0.05-0.1 on its water caustics, where a slow drift would be expected [INFERRED]; and `def_rotation` is degrees per second in the def but seconds per turn in the doc. Preview in Radiant F8 before trusting either direction [TEST].
- **Sun gobo.** The SSI has `sunCookieLightDefName`, `sunCookieScroll`, `sunCookieScale` and more; "These same sun gobo materials and parameters can be used on lights in game. Material goes in 'def'" (doc p.11) [VERIFIED]. See [05](05_sun_sky_exposure_fog.md).
- **A new cookie for Tower II** is a new `light` asset plus image in a map-owned GDT in the private workspace `C:\BO3Tools\TOD2Cybercity`, never the shared Mod Tools root (docs/154), and a full build.

## 13. Volumetric lights

**Plain version.** A volumetric light draws the beam itself: the visible shaft of light in dusty air under a street lamp or through a window. It needs three things, and players can switch it off.

1. **`volumetric 1` on the light** (default false) [VERIFIED]. Spots are typical: The Giant has 177 volumetric lights, 156 spots and 21 omnis [VERIFIED].
2. **A `volume_litfog` around the beam** with `ENABLE_LIGHTS` (spawnflag 64, default true) and a lit-fog `fsi` [VERIFIED]. The community says to use an fsi with "volumetric" in its name, such as `zm_factory_volumetric` [COMMUNITY] (modme 2106, 1880).
3. **The player's "Enable volumetric sun and light shafts" setting** (`VolumetricLightingEnabled` in `players/config.ini`) [VERIFIED]. The user's own config has it at 0, so the user will not see shafts in their playtests. Whether this setting also disables lit fog is [COMMUNITY] only.

**Keys:** `volumetricSampleCount` (1-24, default 8), `volumetricIntensityBoost` (beam-only brightness in stops), `volumetricCookies` (the cookie pattern inside the beam) [VERIFIED].

**Cost.** Treyarch's MP doc: volumetric fog "was a problem for performance"; "Notice that the 'probe look up' and 'enable lights' is set False for the litfog volume. We can't afford these features as a global setting. If these are needed make another volume for the isolated area with these toggled true." (Multiplayer_Lighting_Workflow.pdf) [VERIFIED]. The Giant's own global lit-fog volume does have `ENABLE_LIGHTS` and `ENABLE_SUN` on (spawnflags 14435), and two small `vol_litfog_teslacoils_00x` volumes add `ENABLE_LIGHTS` with the sun off for the hero beams [VERIFIED]. The Giant sets `volumetricSampleCount 1` on 513 of 543 lights, 4 on 8 lights (7 of them the tesla-coil cookie beams, which also get `volumetricIntensityBoost 4-5` and `volumetricCookies 1`) and leaves the default 8 on 22 [VERIFIED].

**Tower II today:** the worldspawn names `fsi zm_factory_volumetric`, but there is no `volume_litfog` and no light sets `volumetric`, so no light shafts can appear (src: map_source/zm/zm_tod2_cybercity.map) [INFERRED]. Fog is covered in [05](05_sun_sky_exposure_fog.md).

## 14. Culling, LOD and limits

**Screen-space LOD** (Culling_LOD_Lights.pdf) [VERIFIED]:
- `culling_cutoff`: "# of onscreen pixels at which your light is completely cut off"; `culling_falloff`: "# of onscreen pixels at which your light starts to fade off". Pixels are the light's radius on screen at 1080p.
- "Good generic starting values": 200 / 300. "Good starting values for smaller lights (radius under 10)": 1 / 5. "Larger values ... will result in more aggressive cutoff of lights as distance increases." "Be prepared to spot fix many lights which fade off too aggressively after your initial pass."
- The Giant sets culling on 427 of 543 lights: 200/300 on 210, 5/25 on 158 (note `lod_very_tolerant`), 50/100 on 34 (`lod_tolerant`) [VERIFIED].
- Lights that switch off at a distance are this LOD, or an FX light's visibility range [COMMUNITY] (modme 459). A Map One FX light culled at 75/150 lit only its lamp, not the room [COMMUNITY] (project record).
- `culling_use_pure_radius` (spots use the radius as a bounding-sphere diameter), `NO_CULL` (no culling volume) [VERIFIED]. Radiant builds light culling at export ("Building light culling...") [VERIFIED]. The `volume_sun` key `respectLightLods` (default true): "When this is false, lights will never LOD out in probe bounce and reflections" [VERIFIED].

**Hard limits** [VERIFIED] (strings in Radiant_modtools.exe; the numbers are not in the strings):
- "Map contains %u lights, max %u supported. This map won't link." and "Too Many Lights". The cap is unknown; The Giant's light prefab alone holds 543 lights, so it is at least that [INFERRED]. Tower II has 344.
- "Sun volume contains %u lights, max %u supported." and "Vista volume contains %u lights ...": per-volume caps, values unknown.
- Coronas: "More than %i light coronas" (cod2map), value unknown.
- No per-surface or per-pixel limit on overlapping lights is documented. The PBR deck says deferred lighting applies "the lights to the whole screen in one pass" [VERIFIED]; treat the cost as screen coverage × overlap [INFERRED].

**Cost levers, cheapest first** [INFERRED] (ranking from the docs): small radius plus culling values; `cut_on` and `far_edge` to trim; no shadow or `Never` shadows; low `volumetricSampleCount`; `Always` shadows (they eat the 12-live budget); `shadowmapScale 2` (4× the cost).

## 15. Lighting states and exploders on a light

This section covers only the keys on the light. The power-on logic, the two working conventions and the Tower II diagnosis are in [02 — Power and states](02_power_and_states.md) (see its sections [4](02_power_and_states.md#4-the-two-working-conventions), [9](02_power_and_states.md#9-exploders-named-light-groups) and [15](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis)).

### lightingstate1..4

- Each light has four booleans, `lightingstate1..4`, all default true: "Each map can have up to 4 lighting states. The lighting-state toggles will control which lights belong to which state" (Lighting_Parameters.pdf p.10) [VERIFIED]. Radiant can toggle the global state from the camera window [VERIFIED].
- `lightingstateN` = **Radiant State N**. Script state n shows Radiant State n+1 [INFERRED] (strongly supported). The boot state of every usermap is script state 1 = **Radiant State 2** (`zm_usermap.gsc:110`) [VERIFIED] (the call; the mapping is [INFERRED]).
- So a light authored `0 1 1 1` (every Tower II light) is **ON in the boot state**, and a light authored `1 0 1 1` is off at boot and on after `set_lighting_state(0)` [INFERRED]. docs/107 and a generator comment call `lightingstate1 0` "authored OFF before power"; the stock evidence contradicts that reading.
- The Giant's patterns (Radiant States 1-4) [VERIFIED]: `1111` 261, `1011` 119 (on after power), `0111` 55 (before power only), `0000` 39 (in no state), `1000` 34 (powered state only), `1100` 14, others 21.
- `misc_model`, `script_model` and `script_brushmodel` carry the same four keys; what they do on a model (hide it, or only gate its baked lighting) is undocumented [TEST]; see [02](02_power_and_states.md).
- Stock perk-machine prefab lights (`zm_core/vending_*.map`, 49 lights) are all `0000` [VERIFIED]; see [03](03_glow_and_perks.md).

### Exploder membership

An exploder is a named group of Radiant-placed entities that script plays or stops by name [VERIFIED]. On lights:
- "Warning: only primary lights can be added to exploders" (Radiant) [VERIFIED], so among light entities only omni/spot lights qualify. Exploders are not light-only: stock prefabs also store membership on FX entities and a few reflection probes [VERIFIED].
- Radiant: Exploder Manager, select the lights, right-click "Create New Exploder from selection", test with Play / Stop / Kill Exploder ("'Stop Exploder' will stop playback, but leave the time where it is. Kill will reset to the start", FX_Lights.pdf) [VERIFIED].
- Membership is stored on the light as `exploder_count` + `exploder_index_N`, in the old form `"0 0 <name>"` or the new form `"ver=2 don=0 doff=0 fin=0 fout=0 off=0 name=<name>"`, often with `exploderDisabled 1` (45 of The Giant's 48 exploder lights) [VERIFIED]. The meaning of `don/doff/fin/fout/off` (probably delays and fades), `exploderDisabled` and `exploderFade` is undocumented [INFERRED]. Copy these keys from a stock example rather than guessing.
- Treyarch's exploder lights are small status lamps: The Giant's 48 have median radius 20 and median stops 5.6, and they keep lighting-state masks (`1011` ×24, `1000` ×15, `1111` ×7, `1101` ×2) [VERIFIED]. 38 of the 48 carry `shadowUpdate Always`, but only 8 have a shadow map at all (`PRIMARY_NOSHADOWMAP 0`), so most are shadowless [VERIFIED]. Whether an exploder light must also be enabled in the active lighting state is untested [TEST]; the Giant's masks fit that reading [INFERRED], so tick the light in every state it may be played in.
- Script (server): `exploder::exploder("name")` → `ActivateClientRadiantExploder`; `exploder::stop_exploder("name")` → `DeactivateClientRadiantExploder`, but only when `level.clientScripts` is true (`exploder_shared.gsc:764`), so a server stop can silently do nothing; `exploder::kill_exploder("name")` → `KillClientRadiantExploder` [VERIFIED]. `load_shared.gsc:55`/`:60` sets that field from `GetDvarString( "cg_usingClientScripts" ) != ""` [VERIFIED]; whether the dvar is set in a usermap is [TEST], so stop groups that must reliably turn off from client script. Client: the same names with a `localClientNum` call `PlayRadiantExploder` / `StopRadiantExploder` / `KillRadiantExploder` [VERIFIED]. Use string names: a string id is the Radiant path, an integer id takes the older createfx path, and `kill_exploder` asserts on anything but a string [VERIFIED].
- Radiant shows "Total Exploders: 0/120", so there is probably a cap of 120 [INFERRED]. Whether an exploder activated before a player joins replays for that player is unknown [TEST]. The Giant drives its teleporter-console lamps from world clientfield callbacks in client script (`zm_giant.csc:91-148`), whose current value reaches a late joiner [INFERRED], and its map lamps from a one-shot `util::clientnotify( "pl1" )` (`zm_giant.gsc:428` → `zm_giant_fx.csc:229`) [VERIFIED] (details in [02 — Exploders](02_power_and_states.md#9-exploders-named-light-groups)). Every exploder membership edit is a full build.

## 16. Script control of a light

**Making a light reachable.** Tick `scriptable` (spawnflag 8) and set `client_server ServerSide` (spawnflag 32): "default is client side so you must choose the server side drop down to grab on the server" [VERIFIED]. Give it a `targetName` and fetch it with `GetEnt( "<name>", "targetname" )` [INFERRED]. The doc calls the first key `PRIMARY_SCRIPTABLE`; the def uses `scriptable` (no stock prefab light sets either), and both strings exist in the binaries [VERIFIED], so which one wins is unknown [TEST].

**The engine API** (src: docs_modtools/bo3_scriptapifunctions.htm) [VERIFIED]:

| Function | Side | API notes |
|---|---|---|
| `<light> SetLightIntensity( <intensity> )` | Server | "1 is fullbright, but values can be larger than 1" (a linear scale, not stops) |
| `<light> SetLightColor( <color> )` | Server | RGB 0..1; "The given values get rounded before they are stored" |
| `<light> SetLightRadius( <radius> )` | Server | "This cannot be larger than the radius when the map was compiled" |
| `<light> SetLightFovRange( <fov_outer>, [fov_inner] )` | Server | Outer "cannot be larger than the fov when the map was compiled, or less than 1"; inner ≤ outer |
| `<light> SetLightExponent( <exponent> )` | Server | Integer 0..100; no light key sets an exponent, so it is probably a leftover from an older falloff model [INFERRED] |
| `GetLightIntensity`, `GetLightColor`, `GetLightRadius`, `GetLightFovOuter`, `GetLightExponent` | Server | Getters |
| `<entity> MakeLight( <primaryLightIndex> )` | Client (Gfx) | "Create a light" |
| `<entity> SetDedicatedShadow( <flag> )`, `GiveDedicatedShadow` | Server | "Enabled or Disables dedicated shadow for a model"; `GiveDedicatedShadow`'s summary reads "Sets the model lod bias", evidently a copy error [INFERRED] |
| `<entity> OverrideLightingOrigin()` | Client | "Uses the entity origin as the lighting origin instead of the center of the entity's bounding area" |

**Does it work?** Unknown here.
- No stock script under `share/raw/scripts` calls any `SetLight*`, `GetLight*` or `MakeLight` [VERIFIED].
- The community mostly says it does not work: "the light functions in the api are now deprecated", use exploders (Harry Bo21, modme 2029); "doesn't seem to work, even when I set it to scriptable", with a reply that "in bo3 all light functions have been deprecate and no longer work" (modme 871). One reply suggests making a light ServerSide + scriptable so it can move with an elevator, with no confirmation that it worked (modme 3412) [COMMUNITY].
- A ServerSide scriptable light is presumably a server entity, so each one spends from the map's scarce entity budget [INFERRED]. The baked bounce stays at the compiled values whatever script does [INFERRED].
- All 344 Tower II lights are ClientSide and not scriptable, so no script can reach them (src: tools/gen_tower_map.js:7176).

**Recommendation** [INFERRED]: use lighting states, exploders or FX lights ([02 — Scriptable server lights](02_power_and_states.md#10-scriptable-server-lights), [04](04_fx_lights.md)). Rely on the `SetLight*` API only after a native test with dev logs.

## 17. build_light

- "A Build_light is a simplified and distinct version of the light entity, allowing builders a means of quickly laying down lighting, independent of lighting department workflow" (Build_light.pdf) [VERIFIED]. Entity Browser > Unsorted > Build_light.
- The doc lists only `_color`, `angles`, `fov_outer`, `origin`, `PRIMARY_TYPE`, `radius` and `stops`. The def carries every other light key too, but hidden, and its `shadowUpdate` offers only `Always` / `Never` [VERIFIED].
- "Build lights are currently set with static shadows ... Dynamic objects will receive shadows from these lights but you will not see live shadows cast from things like characters" [VERIFIED]. The def's hidden `PRIMARY_NOSHADOWMAP` defaults to true; which of the two wins is [TEST].
- They can be left out of the lighting export with the "Export build lights" checkbox (File > Lighting Export) and hidden with the "Use Build Lights" render flag [VERIFIED].
- They probably cannot join exploders, since Radiant accepts only primary lights [INFERRED].
- Use: blocking out a new area quickly. Not for final lighting. Tower II's generator never emits one.

## 18. spawnflags and hidden keys

**spawnflags** are the entity's bit field; Radiant writes them from the named keys [VERIFIED]. In every one of the 1,183 light entities in the stock prefabs, the spawnflags match the named keys [VERIFIED].

| Bit | Meaning |
|---|---|
| 2 | `PRIMARY_OMNI` |
| 4 | `PRIMARY_SPOT` |
| 8 | `scriptable` |
| 16 | `PRIMARY_NOSHADOWMAP` |
| 32 | `client_server ServerSide` |
| 64 | `ENABLE_FALLOFF` |

| Total | Decoded | Where it appears [VERIFIED] |
|---|---|---|
| 82 | falloff + no shadow + omni | Tower II (all 344); The Giant 154; mp_sector 15 |
| 68 | falloff + spot, shadowable | The Giant 227; mp_sector 87 |
| 66 | falloff + omni, shadowable | The Giant 124; mp_sector 9 |
| 84 | falloff + no shadow + spot | The Giant 32; mp_sector 146 |
| 20 | no shadow + spot, no falloff | The Giant 4 (its far moonlight spots); mp_sector 4 |

**Keys to leave alone.** Stock data and the compilers use keys the entity def does not expose. Do not author them without a test [INFERRED]:
- cod2map parses `intensity` (the legacy linear brightness), `attenuation`, `pcss_max`, `pcss_min`, `bulbRadius` and `targetOrigin` [VERIFIED]. PCSS "is currently disabled due to performance constraints" [VERIFIED].
- Stock prefabs also carry `dirSpan`, `animmode`, `animscale`, `exploderFade`, `exploderDisabled` and Treyarch's bookkeeping notes (`note`, `note_stops`, `note_prev_color` …, e.g. `shadowUpdate_was_Always`, `lod_very_tolerant`, `GRP_lantern_direct`) [VERIFIED]. Their runtime meaning is undocumented.
- Doc-only names that do not match the tools: `PRIMARY_SCRIPTABLE` (def: `scriptable`), `ENABLE_COOKIE` (exists nowhere; section 12), and `fov_inner` (only in the FX `lightdescription` asset and `SetLightFovRange`) [VERIFIED].

## 19. What Treyarch does: The Giant

The Giant ships with the Mod Tools with its full lighting source (`map_source/_prefabs/zm/zm_giant/zm_giant_light.map`). Its numbers, next to mp_sector (whose light prefab is byte-identical to mp_combine's), are the best available reference for "what normal looks like" [VERIFIED] unless marked.

| Statistic | The Giant (zombies, night), 543 lights | mp_sector, 275 lights |
|---|---|---|
| Omni / spot | 280 / 263 | 24 / 251 |
| Shadowed (`PRIMARY_NOSHADOWMAP 0`) | 353 (198 `Always`, 155 `Never`) | 110 (68 `Always`, 42 `Never`) |
| `stops` median (p10-p90) | 7 (4.0-10.6) | 15 (12.5-17.9) |
| `radius` median (p25-p90) | 150 (20-350) | 40 (21.5-225) |
| `falloffdistance` | 12 ×315, 5 ×102, 0.75 ×36, 6 ×34 | 12 ×258 |
| Cookie other than `white_light` | 62 | 39 |
| `volumetric 1` | 177 (sample count 1 on 513 lights) | 0 |
| `PROBE_ONLY 1` | 149 | 21 |
| Culling values set | 427 | 232 |
| `bake_intensity_scale` set | 0 | 0 |
| `cut_on` > 0 | 242 | 160 |
| `penumbraRadius` | 3 on 504 | 1.5 on 265 |
| `shadowmapScale` | 1 ×480, 0.5 ×61, 2 ×2 | 1 ×270, 0.5 ×5 |
| Exploder lights | 48 | 8 |
| Lighting-state masks | 11 different patterns (section 15) | `1111` ×270, `0111` ×5 |
| `client_server` | ClientSide ×543, none scriptable | ClientSide ×275, none scriptable |

**Real lights, with their keys** [VERIFIED]. Keys left out are at their defaults.

1. **Hanging cage lamp.** See the table in section 1: a shadowed, volumetric spot pool with `cut_on 22` and a soft round edge, powered (`1011`, stops 10.97, ring cookie) and pre-power (`0111`, stops 8.97) copies, a tiny always-on shade light, plus parked probe and bulb copies.
2. **Hurricane lantern, fill.** `PRIMARY_OMNI`, `PROBE_ONLY 1`, `PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Always`, `stops 8.23`, `radius 250`, `far_edge 0.75`, `falloffdistance 12`, `_color 1 0.4588 0.1608`, states `1111`, spawnflags 66, note `GRP_lantern_probe`.
3. **Hurricane lantern, direct** (2.5 units away). `PRIMARY_OMNI`, shadowed `Never`, `stops 5.64` (≈50), `radius 100`, `cut_on 7`, `falloffdistance 6`, `far_edge 0.5`, `culling 200/300`, same colour, states **`0000`** (parked), note `GRP_lantern_direct`. 8 of the 10 `GRP_lantern_direct` lights are parked this way, while all 13 `GRP_lantern_probe` fills are on in every state [VERIFIED]. If a `0000` light is never lit, the lantern's light in play comes from the probe-only fill (and its FX) [INFERRED].
4. **Moonlight.** `PRIMARY_SPOT`, `ENABLE_FALLOFF 0`, `PRIMARY_NOSHADOWMAP 1`, spawnflags 20, `origin -39426.5 32750.3 57115.5`, `target moon`, `radius 22000`, `fov_outer 55`, `stops 6.73`, `_color 0.7529 0.8471 0.8471`, `far_edge 0.2`, `superellipse 0.5 1 0.5 1`, `roundness 1`, `culling 200/300`, states `1111`, note `moon_light`. Three more `moon_light` spots at the same distance act as fills: radius 12,000 at stops −1, −0.4 and 0.5.
5. **Tesla-coil beam (power-only, flickering, volumetric).** `PRIMARY_SPOT`, no shadow, `def cookie_flicker02`, `def_tile 0.04 0.04`, `def_scroll 0.7 0.7`, `fov_outer 120`, `radius 60`, `cut_on 10`, `near_edge 0.4`, `far_edge 0.5`, `falloffdistance 5`, `stops 3.5`, `_color 0.6863 0.7306 1`, `volumetric 1`, `volumetricCookies 1`, `volumetricIntensityBoost 5`, `volumetricSampleCount 4`, `spec_comp -5`, `ortho_effect 0.2`, `superellipse 0.3 0.7 0.4 1`, `roundness 0.75`, `culling 20/150`, states `1000`.
6. **Water caustics.** `PRIMARY_SPOT`, shadowed `Never`, `shadowmapScale 0.5`, `angles 0 0 180`, `def cookie_caustics_01`, `def_scroll 0.05 0.1`, `def_rotation -0.1`, `cut_on 101`, `radius 325`, `fov_outer 70`, `far_edge 0.85`, `stops 8.97`, `_color 1 0.5098 0.2941`, `culling 200/300`, states `1111`.
7. **Ring-pattern gobo spot.** `PRIMARY_SPOT`, shadowed `Always`, `shadowmapScale 0.5`, `def gobo_spot_rings_001`, `fov_outer 65`, `cut_on 10`, `radius 350`, `stops 9.97`, `superellipse 0.25 1 0.25 1`, `roundness 1`, `volumetric 1` (1 sample), `_color 1 0.7334 0.3922`, `culling 200/300`, states `1011`.
8. **Furnace glow.** `PRIMARY_OMNI`, shadowed `Never`, `stops 5.97`, `radius 200`, `far_edge 0.5`, `_color 0.7961 0.3371 0`, `culling 200/300`, states `1111`, note `furnace_lights` / `probes_stops_was_9pt97`.
9. **Trap indicator lamp (exploder).** `PRIMARY_OMNI`, no shadow, `_color 0 1 0`, `stops 4.64` (≈25), `radius 20`, `falloffdistance 0.75`, `far_edge 0.1`, `culling 5/25`, states `1000`, `exploder_count 1`, `exploder_index_0 "0 0 trap_b_green"`, `exploderDisabled 1`.
10. **MP comparisons (mp_sector).** Fluorescent: spot, shadowed `Never`, `superellipse 0.14 0.21 0.9 1`, `cut_on 21`, `radius 22.5`, `fov_outer 95`, `stops 14`, `culling 50/100`. Tube area light: omni, `bulbLength 28.5`, `radius 5`, `stops 13`, no shadow.

**Patterns worth copying** [INFERRED] (from the data): a fixture is several lights with one job each; small bulb glows are tiny (radius 15-20, falloff 5) with tolerant culling (5/25); room light comes from shaped, shadowed spots with `cut_on`; colour bounce comes from probe-only lights; power-dependent lights come as dim/bright twins; status lamps are tiny exploder lights; everything big has culling values.

## 20. Our generator's light()

Every one of the 344 lights in `map_source/zm/zm_tod2_cybercity.map` comes from ONE function, `light(label, x, y, z, color, radius, stops, bake)` (src: tools/gen_tower_map.js:7166-7186). The map groups them as: 128 on the spiral laps and breather lounges, 117 on the spire, 32 on the crown causeway, 16 in the workshop wings, 10 in the Vault, 7 in the teleport bay, 6 on the crown, 5 in the base plaza, 5 in the crown hall, 4 each in the Conduit and the shaft, 3 in the power hall, and a handful of single lights (src: parse of the .map by targetname). Parsed values: all omni, all `stops 6`, radius 200-900 (median 420), `bake_intensity_scale` 1 on 320 lights and 1.35 on 24, no culling keys, no exploder keys.

| Key the generator writes | Value | What it means | Consequence |
|---|---|---|---|
| `classname` | `light` | a primary light | |
| `targetname` | the label, with runs of non-word characters turned into `_` | a name | The def spells it `targetName`; inert anyway, since the lights are not scriptable [INFERRED] |
| `origin` | per call | position | |
| `PRIMARY_TYPE` | `PRIMARY_OMNI` | point light | No spots anywhere; no cone or cookie shaping |
| `PRIMARY_NOSHADOWMAP` | 1 | never a shadow map | Light passes through walls, slabs and doors. With `LAP_RISE` 384 and radius 420 a lap light can reach the floors above and below and into sealed rooms [INFERRED] (from the def and community bleed reports) [TEST] |
| `ENABLE_FALLOFF` / `falloffdistance` | 1 / 12 | inverse-square from 12 units | A long, dim tail over a 420 radius (about 0.16 at 240 units under the section 6 model) [INFERRED] |
| `_color` | district colour, via `tintLight()` | hue | `LIGHT_TINT null` = no tint |
| `radius` | 200-900 | cut-off | Large next to The Giant's median 150 |
| `stops` | 6 | 2^6 = 64 | One stop under The Giant's median, 5 under the def default [INFERRED] |
| `bake_intensity_scale` | 1, or 1.35 (`BASE_LIGHT_BAKE`) | GI bake brightness per the def | Used as "the only real brightness knob in the base"; its effect on the direct pool is [TEST] (section 10) |
| `client_server` | ClientSide | default | No server script can reach them |
| `far_edge` | 0.95 | default fade | Fine |
| `def_tile`, `excludeDedicated`, `fov_outer 90`, `penumbraRadius 1.5`, `roundness 0.5`, `shadowmapScale 1`, `shadowUpdate Never`, `superellipse 0.75 1 0.75 1`, `volumetricSampleCount 8`, `name light` | defaults | spot, cookie, shadow and volumetric settings | Inert on a shadowless, non-volumetric, cookie-less omni [INFERRED] |
| `lightingstate1..4` | 0, 1, 1, 1 | off in Radiant State 1, on in Radiant States 2-4 | ON in the boot state (Radiant State 2); see below |
| `spawnflags` | 82 | 64 + 16 + 2 | Consistent with the keys |
| culling keys | not written (0) | no screen-space LOD | All 344 are evaluated whenever in view; Treyarch sets culling on 79% [INFERRED] |

**Where the template came from.** The key set is byte-for-byte Map One's light template (its `gen_room_roofs.js`, labelled a "Verified kelson8 PRIMARY_OMNI light entity"), i.e. one community example, not Treyarch's lights [COMMUNITY] (project record).

**Are these lights on?** All 344 are authored ON in Radiant State 2, the state `zm_usermap::main` boots, and no Tower II script changes the state, so every light is on from spawn and power changes none of them [INFERRED] [TEST]. Two open questions sit on top of that, both covered in [02 — the diagnosis](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis): the `volume_sun` sets only `ssi1` (plus a bare `ssi` key the def does not define), so the compiled `.led` pairs Radiant State 2 with `default_day`, and what the engine shows in that case is [TEST]; and TOD1 had the same setup yet project records describe visible light at light positions [COMMUNITY] (project record), which is counter-evidence to the idea that nothing renders. Treyarch's own mp_sector light prefab also ships 5 lights at `0111` with a `volume_sun` that sets only `ssi1` (and `ssi1_runtime_override`) [VERIFIED]; that shows the setup was shipped, not that those lights render.

## For Tower of Doom II

Recommendations only; nothing here changes code or data. Every item is a full build, and the user judges the result in game.

1. **Answer the "are they on?" question before retuning anything.** Follow the test plan in [02](02_power_and_states.md#16-minimal-test-plan-in-the-control-map) and [10](10_troubleshooting_limits_history.md#7-open-questions-and-the-test-plan): a dev-gated log of `player GetLightingState()` plus a same-spot A/B with `ssi2` filled. Retuning 344 lights whose runtime state is unknown wastes builds.
2. **Run the `bake_intensity_scale` A/B (section 10).** Until it is settled, move brightness decisions into `stops`, which is documented as the brightness control.
3. **Give `light()` real parameters instead of one template.** At minimum: type (omni/spot), angles or "down", `fov_outer`, `cut_on`, `far_edge`, shadow mode, `spec_comp`, `PROBE_ONLY`, culling pair and lighting-state mask. Keep the single emission path; the generator should own every value, the same way it owns bench anchors.
4. **Shape light instead of flooding it.** A dark map wants pools with edges. Use spots with `cut_on` and soft `superellipse` values under real fixtures, smaller radii, and falloff tuned per fixture. Treyarch's median radius is 150 against our 420 (section 19).
5. **Stop light from leaking between floors and rooms.** Our shadowless 420-radius omnis on a 384-unit lap rise can light the floors above and below (section 9). In enclosed spaces (the Vault, the Conduit, the lounges, the wings) prefer shadowed lights with `shadowUpdate Never`, keep `Always` for a few hero lights, and remember the user's own config shows no live light shadows.
6. **Add culling values** (200/300 normal, 5/25 small) to every light; a 50-floor tower has very long sight lines.
7. **Use `PROBE_ONLY` fills for district colour** in the lounges and wings once the probes are fitted to the rooms ([06](06_reflections_probes.md)). It tints the ambience without extra visible pools.
8. **Try a negative `spec_comp`** (−2 to −6, Treyarch's range) on lights near the mirror-like Vertigo surfaces if highlights read as plastic.
9. **Build fixtures, not naked lights.** Every visible pool should have a visible source (a lamp model, an emissive panel, a sign). Recipes: [08 — Fixture cookbook](08_fixture_cookbook.md); design: [09](09_design_and_inspiration.md).
10. **Keep switchable light small and scripted the proven way.** Power-on and per-floor reveals go through lighting states, client exploders or FX lights ([02](02_power_and_states.md), [04](04_fx_lights.md)), not the untested `SetLight*` API.
11. **Assets stay private.** Any new cookie `light` asset or lamp material goes into a map-owned GDT in `C:\BO3Tools\TOD2Cybercity` (docs/154), never the shared Mod Tools root.

## Sources

**Official Treyarch docs and data (MODTOOLS)**
- `bin/t7.def.json`: entity definitions for `light`, `build_light`, `info_corona`, `lensflare`, `volume_performance`, `volume_litfog`, `volume_sun` (`respectLightLods`), `worldspawn` (shadow slices, `coronamaterial`, `state_alias_N`).
- `docs_modtools/Lighting_Parameters.pdf` (p.1 intensity and type; p.2-7 shaping; p.8-10 cookies and lighting states; p.10-11 LOD and shadows; p.11 sun gobo; p.12 exposure keys).
- `docs_modtools/Build_light.pdf`, `Culling_LOD_Lights.pdf`, `FX_Lights.pdf`, `Generate_LED.pdf`, `Scale_Standards.pdf`, `Multiplayer_Lighting_Workflow.pdf`, `Materials.pdf` (p.17 lampshade shaders), `Probe/Reflection_Probes.pdf`, `SunSky_Light_SetUp.pdf`, `PhysicallyBasedRendering.pptx`.
- `docs_modtools/bo3_scriptapifunctions.htm`: `SetLight*`/`GetLight*`, `MakeLight`, `SetLightingState`/`GetLightingState`, exploder functions, `SetDedicatedShadow`, `OverrideLightingOrigin`.
- `deffiles/light.awi` (cookie asset: `cookieImage`); `deffiles/lightdescription.awi` (FX light fields, `PRIMARY_DIR`).
- `texture_assets/t6_lights.gdt`, `t7_light_gobo.gdt`, `t7_cookie.gdt`, `texture_assets/lights/*.tif`.
- `map_source/_prefabs/zm/zm_giant/zm_giant_light.map` and `geo/zm_giant_light_cage_03.map`: 543 Treyarch zombies lights, parsed for every statistic and example above, plus the shadow-caster brushes; `map_source/zm/zm_giant.map` worldspawn (exposure keys).
- `map_source/_prefabs/mp/mp_sector/mp_sector_light.map` (byte-identical to `mp_combine_light.map`): 275 Treyarch MP lights and its `volume_sun`.
- `map_source/_prefabs/zm/zm_core/vending_*.map`: stock perk prefab lights.
- `texture_assets/code.gdt` (`shadowcaster`) and `texture_assets/tools.gdt` (`caulk_shadow`, `caulk_sun_shadow`).
- `share/raw/scripts/zm/zm_usermap.gsc:110`, `zm/gametypes/_globallogic_spawn.gsc:501`, `zm/zm_giant.gsc:428, 571`, `zm/zm_giant.csc:91-148`, `zm/zm_giant_fx.csc:225-292`, `shared/util_shared.gsc:2975-3004`, `shared/load_shared.gsc:55, 60`, `shared/exploder_shared.gsc` (:275-285, 663-668, 762-819) and `exploder_shared.csc` (:297-424).
- `bin/Radiant_modtools.exe` and `bin/cod2map64.exe` strings: light and volume caps, exploder rule and 0/120 counter, cookie errors, `sm_lightScore_*` help text, "Building light culling", "+3 Stops", hidden cod2map keys, absence of `ENABLE_COOKIE`.

**Player settings**
- `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III\players\config.ini`: the user's shadow, shadow-resolution, `ActorShadows` and volumetric settings.

**This repo**
- `tools/gen_tower_map.js:7154-7186` (`tintLight`, `light`), `:7187-7216` (`BASE_LIGHT_BAKE`, base lights), `:1540-1557` (docs/107 comment), `:1898` (`LIGHT_TINT`).
- `map_source/zm/zm_tod2_cybercity.map`: 344 lights, worldspawn, `volume_sun` (parsed).
- `source_data/tod_skybox.gdt`: the `tod_ssi_cybercity` exposure values.
- `share/raw/fx/tod/fx_tod_inducer_on.efx`: an FX light block for comparison.
- `docs/107_sun_volume_yellow_postmortem.md`, `docs/154_tod2_isolation.md`, `CLAUDE.md`.

**Community**
- The Level Design Book, lighting: https://book.leveldesignbook.com/process/lighting
- VerK0, Lighting Tutorial parts 1-5 (lights: https://www.youtube.com/watch?v=VPT3TJzbQPc); Program115, "Lighting Basics (Omni & Spot)": https://www.youtube.com/watch?v=beP7zrpUCwI; Uptownpapi25: https://www.youtube.com/watch?v=nYCPEJfmuS4
- Modme forum archive (https://github.com/dtzxporter/ModmeForum), threads 293 (spec_comp), 304 and 2987 (light bleed), 459 (lights vanish at distance), 477 (day vs night stops), 871, 2029 and 3412 (script light API), 1880 and 2106 (lit fog), 1077 (state numbering).
- UGX, lights leaking through walls: https://www.ugx-mods.com/forum/help-desk/86/lights-leaking-through-walls/14935/
- Map One (`c:/Users/jorda/Repositories/abandoned_cyber_city_zombies`): light template origin and `bake_intensity_scale` use (`tools/oneshots/gen_room_roofs.js:43-45`), the culled FX light (`CHANGELOG.md` ~6445) (project records).
