# 07 — Water

**In short.** In Black Ops III, "water" is not one object. It is up to three separate pieces that you stack in the same place: a water **material** for the look, an invisible **clip-water brush** for the behaviour (wading, swimming, splashes, `DepthInWater()`), and a **`pbg_box`** with the `USE_UNDERWATER` flag for the blurred, colour-absorbed view under the surface. Treyarch's own zombies map The Giant uses only the first piece for its vats: a flat patch painted with a water material that nobody can enter. Water looks like water mostly because it reflects, and in BO3 those reflections come from baked reflection probes plus, on the water materials only, an optional screen-space reflection. For a dark cyber tower the cheapest and safest "water" is a wet, glossy look under neon with properly fitted probes; real water is worth adding only where the story needs it, and it should stay shallow. Nothing in Tower of Doom II uses water today, and nothing in this chapter was tested in game.

**Read this when…** you want a puddle, a pool, a flooded floor, a sewer or coolant channel, a waterfall, rain-slick floors, dancing caustic light on a wall, or an underwater view, or when water in a build renders black, has no splash, or shows no neon highlights.

## Contents

1. [Water is three separate things](#1-water-is-three-separate-things)
2. [The behaviour layer: clip-water brushes and wave_water](#2-the-behaviour-layer-clip-water-brushes-and-wave_water)
3. [The look: water material techniques](#3-the-look-water-material-techniques)
4. [Field reference for the lit_water_sim family](#4-field-reference-for-the-lit_water_sim-family)
5. [The stock water materials to copy](#5-the-stock-water-materials-to-copy)
6. [How water is lit and how it reflects](#6-how-water-is-lit-and-how-it-reflects)
7. [What Radiant shows you is not the game](#7-what-radiant-shows-you-is-not-the-game)
8. [The underwater look](#8-the-underwater-look)
9. [Script API for water](#9-script-api-for-water)
10. [Players and zombies in water](#10-players-and-zombies-in-water)
11. [Surface types, splashes and footsteps](#11-surface-types-splashes-and-footsteps)
12. [Wet surfaces without water](#12-wet-surfaces-without-water)
13. [Moving water: flow, waterfalls, drips, rising water](#13-moving-water-flow-waterfalls-drips-rising-water)
14. [Caustics: light that ripples like water](#14-caustics-light-that-ripples-like-water)
15. [Recipes](#15-recipes)
16. [Troubleshooting](#16-troubleshooting)
17. [Open questions and tests](#17-open-questions-and-tests)
18. [For Tower of Doom II](#for-tower-of-doom-ii)
19. [Sources](#sources)

Tags used: [VERIFIED] read in an official Treyarch doc, stock script, stock data file, or the engine API list; [COMMUNITY] forum, tutorial, video, other mapper, or this project's own recorded observation; [INFERRED] reasoned, not seen; [TEST] needs an in-game test. MODTOOLS = `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`. Repo paths are relative to the repo root.

---

## 1. Water is three separate things

**Plain version.** Think of a swimming pool in a zombies map. What you *see* is a rippling, reflective surface. What you *feel* is that you slow down as you walk in, your footsteps splash, and deep enough you swim. What happens when your head goes under is a blurry, blue-green view. BO3 builds those three things with three different tools, and you only add the ones you need:

| Part | What it does | What you place | Needed for |
|---|---|---|---|
| **Look** | The visible surface: ripples, colour, refraction of what is under it, reflections | A patch, brush face or model painted with a water material (GDT `usage water`) | Anything the player should see as water |
| **Behaviour** | Tells the engine "this space is water": depth, wading, swimming, water splashes on impact | A brush whose faces use a clip-water tool material (`clip_water`, `clip_water_shallow`) | Wading, swimming, `DepthInWater()` |
| **Underwater look** | Blur, colour absorption and fog when the camera is below the surface | A `pbg_box` with the `USE_UNDERWATER` spawnflag | Only if a player's head can go under |

This three-part model comes from the modme wiki and forum [COMMUNITY] (src: https://wiki.modme.co/wiki/black_ops_3/basics/Setting-up-water.html; https://forum.modme.co/wiki/threads/298.html), and it matches the stock data below. Two corrections to the community wording: there is **no material called `water_clip`** in any GDT; the stock tool materials are `clip_water`, `clip_water_shallow` and `clip_water_player` [VERIFIED] (src: art_assets/t6_legacy/texture_assets/clip.gdt). And the wiki's underwater key `underwater_absorbtion` is really `underwater_absorptionRGB` [VERIFIED] (src: bin/t7.def.json, pbg_box).

**The look works on its own.** The Giant's vat (prefab `zoneb_vat_1`) is a single curve patch with `contents nonColliding;` painted `t7_water_zm_der_vats`. The prefab contains no water clip and no volume [VERIFIED] (src: MODTOOLS/map_source/_prefabs/zm/zm_giant/geo/zoneb_vat_1.map:1246-1253; the only other "clip" hits in that file are `weaponClip` trim patches). So decorative water that nobody enters needs only a material.

**Two more layers people usually add:** dressing FX (drips, splashes, mist, steam; see [13](#13-moving-water-flow-waterfalls-drips-rising-water) and [04 — FX lights](04_fx_lights.md)), and wet surfaces that are not water at all (glossy materials and puddle decals; see [12](#12-wet-surfaces-without-water)).

**Where this repo stands.** Nothing in Tower of Doom II uses water: zero hits for `lit_water`, `clip_water`, `wave_water`, `pbg_box` or `puddle` in `map_source/zm/zm_tod2_cybercity.map`, `tools/`, `scripts/` or `source_data/`, and the only `_wet` hits are `_wetegg` perk-pack paths, not wet materials [VERIFIED by grep, 2026-09-24]. The only related precedent is a comment in `tools/gen_tower_map.js` (just above `doorMatOf()`, ~line 1645) saying the landings, breather floors, terrace and causeway "are supposed to keep their wet-neon reflection". That reflection comes from the mirror-like vertigo world materials, not from water [VERIFIED] (see [12](#12-wet-surfaces-without-water)).

---

## 2. The behaviour layer: clip-water brushes and wave_water

**Plain version.** The behaviour layer is an invisible brush. In Radiant it looks like a blue grid; in game it draws nothing. Its job is to tell the engine that anything inside it is in water.

### 2a. The three clip-water tool materials

They are ordinary GDT tool materials in the stock `art_assets/t6_legacy/texture_assets/clip.gdt` (present in the private workspace `C:\BO3Tools\TOD2Cybercity` too), all `materialType tools_blend`, `usage clip`, `noDraw 1`, `noCastShadow 1` [VERIFIED]:

| Material | Line | `nonSolid` | `playerClip` | `aiClip` | `surfaceType` | Editor image | Use it for |
|---|---|---|---|---|---|---|---|
| `clip_water` | 46604 | 1 | 0 | 0 | `water` | `water` | Deeper water players walk or swim into |
| `clip_water_shallow` | 8255 | 1 | 0 | 0 | `watershallow` | `water_shallow` | Ankle-to-knee water (puddle zones, shallow channels) |
| `clip_water_player` | 47516 | **0** | **1** | **1** | `water` | `water` | **Not** a swim volume: it is solid to players and AI |

`clip_water_player` blocks players and AI while reporting a water surface. Using it for a pool would stop anyone entering [INFERRED from the flags]. For walk-in water use `clip_water` or `clip_water_shallow`.

Treyarch's one shipped example is a single `clip_water_shallow` brush **16 units thick** (bottom z 92, top z 108) under the MP Sector water [VERIFIED] (src: MODTOOLS/map_source/_prefabs/mp/mp_sector/geo/mp_sector_terrain_north.map:7722-7730; the same brush is in mp_combine). The community pattern is "a brush with all sides being water clip ... a patch on top with the water texture" [COMMUNITY] (src: modme thread 298, Exofile).

How deep the clip brush must be, and whether `clip_water_shallow` ever lets a player swim, is not documented [TEST]. What the engine does with `nonSolid 1` + `surfaceType water` to create a water volume is not documented either; the compiler binary contains the strings `clip_water`, `clip_water_player` and `isWater` [VERIFIED strings] (src: bin/cod2map64.exe).

### 2b. The legacy "water" trigger and the undertow volume

- `shared/load_shared.gsc:88` threads `water_think` on every entity with `targetname "water"`. That trigger must `target` an entity whose origin Z marks the water height. It forbids prone deeper than 8 and crouch deeper than 33; the speed change is commented out [VERIFIED] (src: share/raw/scripts/shared/load_shared.gsc:88, 590-676). This is an old stance limiter, not a water volume.
- `undertow_volume` has one key, `force` (default `0 0 -200`): "specify a direction that the undertow_volume will pull the player" [VERIFIED] (src: bin/t7.def.json). Its tool material is `undertow` (`tools_blend`, `noDraw 1`, `nonSolid 1`) in `texture_assets/tools.gdt` [VERIFIED]. Untested here [TEST].

### 2c. wave_water: a simulated wave surface

**Plain version.** `wave_water` makes a surface that actually moves: waves ripple outward when players or objects disturb it. It is a surface simulation, not the thing that makes water swimmable.

`wave_water` is a **brush** entity (Radiant warns "wave_water entity with no brushes") [VERIFIED string] (src: bin/Radiant_modtools.exe). Its definition describes only surface and simulation settings. It is **not documented as a swim or behaviour volume**, and **no shipped Treyarch map source uses it**, so whether it gives any swim behaviour on its own is unverified [VERIFIED absence; behaviour TEST]. The community pairs it with a same-size clip-water brush [COMMUNITY] (src: modme thread 3780).

Keys and defaults [VERIFIED] (src: bin/t7.def.json, `wave_water`):

| Key | Default | Range | Definition text (quoted or summarised) |
|---|---|---|---|
| `min_grid_size` | 200 | 10–1000 | "smallest water tile size" |
| `max_grid_size` | 1000 | 100–10000 | "largest water tile size" |
| `grid_detail_scale` | 1.0 | 0.01–5 | "smaller -> more detail at a given distance" |
| `interaction_scale` | 1.0 | 0–100 | "larger -> water reacts more" |
| `damping` | 0.2 | −1–100 | "increase to have waves die out faster" |
| `time_scale` | 0.5 | 0–10 | "1.0 is regular time which sometimes looks too fast" |
| `water_depth` | 1000000 | 0–1e6 | wave speed depends on depth when shallow; "Make large to ignore depth effects" |
| `min_clamp` / `max_clamp` | −2000 / 2000 | | height limits for waves |
| `player_radius_scale`, `physics_radius_scale`, `other_radius_scale` | 1.0 | 0–10 | interaction radii |
| `emergency_damping_level` | 100 | 0–1000 | height at which extra damping starts |
| `opaque` | false | | "water can be assumed to completely hide anything under it" |
| `cast_shadow` | false | | "casts a translucent shadow (opacity specified in material)" |
| `align_to_top` | false | | water level = Z of the top brush surface |
| `targetname` | `placeholder` | | name used by script (`SetWaveWaterHeight`, `SetWaveWaterEnabled`) |

Companions [VERIFIED] (src: bin/t7.def.json):
- `wave_generator` (point): `radius` 20, `amplitude` 10 (± `amplitude_variation` 5), `period` 2 s (± 0.5), `change_time` 2 (± 0.5), `target` = the wave_water's targetname.
- `wave_clamp`: `height` (relative to the wave_water, default 0), `target`.
- `dyn_model` has `splashEfxUp0..2`: "An effect that plays when a wave water line crosses the entity from below to above".

Community notes: floating props need a `dyn_model` with a floating physpreset plus `SetDvar("phys_buoyancy", 1)`, and "This can be costly on FPS if large surface" [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3780.html). An engine string `r_waveWaterActors` ("Enable water interaction with AI Actors") also exists [VERIFIED string; default unknown] (src: bin/cod2map64.exe).

**Recommendation for this project:** skip `wave_water`. It has no stock example, an FPS warning, and nothing in a dark tower needs real waves [INFERRED].

---

## 3. The look: water material techniques

**Plain version.** A material's *Material Type* (its technique set) decides which shader draws it. BO3 ships several water-specific ones. The source definitions are in `MODTOOLS\share\raw\techsetdefs_stable\`; precompiled shader caches for them are in `share\assetconvert\preshader\pc\v7\` (named after the HLSL source, e.g. `lit_water_sim.hlsl` 1,980 files, `water_shore.hlsl` 4,680, `lit_waterfall.hlsl` 1,080, `gbuffer_decal_normal_gloss_reveal.hlsl` 400, `specialty_lit_emissive_lava_flow.hlsl` 360) [VERIFIED counts]. Whether every permutation is precompiled cannot be checked because the file names are hashes; no water build was run [INFERRED that the converter can build these].

| Material type | Folder | What it is for | Key render facts |
|---|---|---|---|
| `lit_water_sim` | geometry | Still water: normal map, colour ramps, refraction, optional SSR | Opaque *water* pass (below). **No flow, noise or foam slots** |
| `lit_water_sim_flow_normal` | geometry | Moving water driven by a flow map, with noise and optional foam | as above + `USE_FLOW_ANY` |
| `lit_water_sim_flow_normal_color` | geometry | Flow water plus a colour decal map and Albedo Tint (murky/tinted water) | as above + `USE_FLOW_COLOR` |
| `lit_water_sim_flow_normal_only_sun` | geometry | Cheaper outdoor flow water | lit technique **replaces** its defines with `USE_FLOW_ANY`, `DISABLE_FORWARD_NON_SUN_LIGHTS 1`; comment: "removing ALLOW_DOUBLE_SIDED 1" |
| `..._only_sun_and_only_global_probe` | geometry | Cheapest | also `DISABLE_FORWARD_NON_GLOBAL_PROBES 1` |
| `..._only_sun_expensive`, `..._expensive_bugfix` | geometry | Better sun-shadow sampling | `SHADOW_TAP_COUNT 3`; bugfix uses `lit_water_sim_bugfix.hlsl` |
| `lit_transparent_water_flow`, `_nocull` | geometry | Truly see-through, **non-flat** flowing water (sloped streams) | `blend + depth`, OIT technique; defines `DISABLE_FORWARD_NON_SUN_LIGHTS`, `USE_NONFLAT_REFRACTION`, `USE_NONFLAT` |
| `water_shore` (+ `_flow`, `_nonflat`, `_nonflat_backlit`, `_backlit_bloat`, `_flow_nonflat_backlit_nocull`, `_igc`) | geometry | Ocean/lake with shoreline | Opaque; "Use vertex (Gerstner) waves", shallow/deep/scatter/horizon colours, shore map, foam mask. No material in the top-level stock GDTs (`texture_assets`, `model_export`, `source_data`) uses it |
| `lit_backlit_waterfall`, `_reveal_alphatest` (+ `_plus` in geometry_plus) | geometry | Opaque falling sheet of water | "lit deferred opaque animating"; UV scroll + flag (vertex) motion, thickness map, backlight tint |
| `lit_transparent_backlit_waterfall`, `_reveal` (+ `_plus`) | geometry | See-through waterfall | "lit semi transparent animating" |
| `lit_decal_normal_gloss_reveal` | decal | Water flowing over an opaque surface; stock puddles | Two scrolling normal layers + gloss + reveal map |
| `lit_decal_normal_gloss_reveal_flow` | decal | Same, following a flow map | |
| `lit_decal_raindrops` | decal | Animated rain-drop rings on the ground | Ripple normal hard-wired to image `rain_hit_n` |
| `lit_decal_specular_fullspec` | decal | Oily sheen over any material (replaces only the spec map) | |
| `lit_emissive_lava_flow`, `_script` | specialty | A **glowing** liquid: neon coolant, toxic sludge | "lit forward opaque"; emissive + flicker + scroll + flow; `_script` adds Tint State 2–4 and `USE_SCRIPT_CONTROLS` |
| `lit_transparent` (core) | geometry | The simplest see-through water | Stock `t7_water_sector_opacity_40` / `t7_water_variant_opacity_5` are just this |
| `effect_lit_scroll_emissive_blend(_specular)(_nocull)` | effect | "fake flowing water" on particles | Needs FX "Don't use compute sprites" |
| `water_dive`, `water_sheeting`, `underwater_blur_*` | 2d / fullscreen | Screen overlays | Not for world surfaces |

All [VERIFIED] from the techsetdef files (src: share/raw/techsetdefs_stable/{geometry,geometry_plus,decal,specialty,include}; Materials.pdf p.19-20, p.25 for the decal and effect descriptions).

**How the `lit_water_sim` family renders in game** [VERIFIED] (src: geometry/lit_water_sim.techsetdef; include/lit_water_sim_base.techsetdef:365-440):
- Render flags `isOpaque = true`, `isWater = true`, `castsShadows = false`, `requiresPrepass = true`, `needOpaqueResolve = true`, `needOpaqueDepthResolve = true`. It is **not** an alpha-blended transparent surface.
- Its lit pass is `replace + depth + nocull + clear stencil` with `ALLOW_DOUBLE_SIDED 1`, and it samples the code textures `resolvedPostSun`, `floatZSampler` and `floatZDownscaledSampler`. So "refraction" is a distorted copy of the already-rendered scene under it, and the soft edge where water meets geometry comes from scene depth.
- A "build shadowmap depth" technique with multiply blend gives a translucent shadow.
- Plain meaning [INFERRED]: this water avoids order-independent transparency (OIT) and its overdraw, but costs a scene resolve and a prepass. It never blocks light (`castsShadows false`).

**Transparency is the expensive route.** Treyarch: "Beyond the Glass and Foliage, transparency should be a rare occurrence" and "overdraw is the number one killer of performance" [VERIFIED] (src: docs_modtools/Materials.pdf p.10-11). The PBR deck adds "Transparency is the single fastest way to ruin our framerate" and suggests decals for "water on a surface" [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 15). Also: the user's own `players/config.ini` has `OIT = "0"` (order-independent transparency off) [VERIFIED, file dated 2026-09-23]. How `lit_transparent` water sorts with OIT off is untested [TEST]. Prefer the `lit_water_sim` family or opaque wet materials.

**Plain Lit also counts.** The Materials doc says the plain Lit family covers "Almost Everything ... including non-colored glass, and water!" [VERIFIED] (src: Materials.pdf p.1). A very glossy, dark `lit` surface is a legitimate still-water look when you do not need refraction.

---

## 4. Field reference for the lit_water_sim family

**Plain version.** Water materials store most settings in generic GDT slots (`cg01_x`, `colorMap02` and so on); the technique file gives each slot its name in APE (the asset editor). This section decodes them. "Default" is the technique's `Tweak()` default; "vats" is Treyarch's `t7_water_zm_der_vats` (used by The Giant); "sector" is `t7_water_sector_flow` (MP Sector). All [VERIFIED] (src: share/raw/techsetdefs_stable/include/lit_water_sim_base.techsetdef, flow_base.techsetdef, lit_water_sim_flow_base.techsetdef, foam_base.techsetdef; MODTOOLS/texture_assets/t7_water.gdt:2 and :1319).

### 4a. Base slots (every lit_water_sim* technique)

| GDT key | APE title | Default | vats | sector |
|---|---|---|---|---|
| `colorMap` | Backscatter Color Ramp | `$white` | `i_t7_water_stream_small_backscatter_ramp` | `i_t7_water_mp_redwood_backscatter_c` |
| `colorMap01` | Refraction Color Ramp | `$white` | `img_refraction_zfeather_small_ramp` | `img_refraction_ramp` |
| `normalMap` | Normal Map | `$identitynormalmap` | `i_mtl_p7_eth_vista_water_n` | same |
| `cg02_x` | Normal Tile | 251 | 0.3 | 30 |
| `cg02_y` | Normal Scale | 1.0 | 0.5 | 0.3 |
| `cg01_x` | Specular Roughness Lobe A | 0.05 | 0.05 | 0.125 |
| `cg01_y` | Specular Roughness Lobe B | 0.5 | 0.005 | 0.005 |
| `cg01_z` | Specular Roughness **Lobe A Weighting** (a weight, not a third lobe) | 0.35 | 0.1 | 0.1 |
| `cg02_z` | Refraction Distortion Amount | 0 | 5 | 20 |
| `cg02_w` | Reflection Gloss | 0.5 | 1 | 1 |
| `overwaterOpacityScale` | Overwater Opacity Scale | 1.0 | 0.98 | 0.8 |
| `underwaterOpacityScale` | Underwater Opacity Scale | 1.0 | 1 | 0.75 |
| `zFeather` | Use Z Feather For Specular (checkbox) | off | on | on |
| `zFeatherDepth` | Specular Z Feather Depth (the shader uses 1/x) | 10 | 1000 | 20 |
| `useScreenspaceReflection` | Use Screenspace Reflection (tooltip: "Enable dynamic reflection from screen") | off | **on** | off |
| `useLoopedScreenspaceReflection` | Use Looped (HQ) SSR (tooltip: "Enable higher quality dynamic reflection from screen") | off | **on** | off |
| `maxRayDepth` / `ssrRayDepthScale` / `ssrRayStepSize` | SSR maximum ray depth / ray depth scale / ray step size | 500 / 1 / 40 | 500 / 250 / 50 | 600 / 1 / 30 |
| `doubleSidedLighting` | Allow double-sided lighting | off | 0 | 0 |
| `translucentShadowOpacity` | ShadowTransparency | — | 0.5 | 0.5 |

`deffiles/material.awi` carries different fallback defaults for some of these (overwater/underwater 0.75, `maxRayDepth` 1000, `ssrRayStepSize` 20, `zFeatherDepth` 40) [VERIFIED] (src: deffiles/material.awi:1041, 1171-1177). Copy values from a stock material rather than trusting either default.

### 4b. Flow, noise and foam slots (flow family only)

These slots **do not exist on plain `lit_water_sim`**, which includes only `lit_water_sim_base`. They come from `lit_water_sim_flow_base` (which includes `flow_base` and `foam_base`) and are used by `_flow_normal`, `_flow_normal_color`, the `_only_sun*` variants and `lit_transparent_water_flow` [VERIFIED].

| GDT key | APE title | Default | vats | sector |
|---|---|---|---|---|
| `colorMap02` | Flow Map | `$white` | `i_t7_water_cp_nw_vat_flow_2` | `i_t7_water_sector_flow_c` |
| `cg04_x` | Flow tile density | 20 | 20 | 150 |
| `cg04_y` | Flow rate scale | 0.15 | **0.01** (nearly still) | 0.8 |
| `colorMap04` | Noise Map | `$white` | `flow_map_noise_test` | `$white_multimask` |
| `cg05_x` / `_y` / `_z` / `_w` | Noise shift scale X / Y, Noise map scale, Noise effect scale | 0.002 / 0.003 / 0.1 / 1.0 | 0.1 / 0.1 / 0.1 / 0.2 | 0.1 / 0.1 / 10 / 0 |
| `orientNormalsToFlow` | Orient normals to flow | off | on | on |
| `scaleNormalsWithFlow` / `normalsFlowScaleMin` | Scale normals with local flow rate / minimum multiplier | off / 0 | on / 0 | on / 0.125 |
| `foamMapEnable` | Use foam map ("Add foam on top of water") | off | off | **on** |
| `colorMap14` | Foam Base | `$white` | `i_t7_water_foam_r` | `i_t7_water_foam_r` |
| `foamColor` | Foam color (a separate colour field) | — | 0.76 0.72 0.62 | 0.76 0.80 0.79 |
| `cg16_x` / `cg16_y` | Foam Minimum / Maximum Spacing | 1.0 / 6.0 | 0.1 / 9 | 0.001 / 10 |
| `cg16_w` | Foam Color Scale (×0.25 inside the shader) | 1.0 | 0.8 | 1 |
| `gFoamScrollAngle0-3`, `gFoamScrollSpeed0-3`, `gFoamUVScale0-3` | Foam UV Scroll 0–3 (angle, speed, scale) | see techset | stock values in t7_water.gdt | stock values in t7_water.gdt |
| `gDepthFeather` | Foam Z Feather (1/x) | 10 | 10 | 10 |

`_flow_normal_color` alone adds `colorMap03` **Color Decal Map** (vats: `i_t7_water_variant_opacity_100_c`) and `colorTint` **Albedo Tint** (vats: `1 1 1 1`) [VERIFIED].

### 4c. Other fields both stock flow materials set

`usage water`, `surfaceType water` (vats) or `watershallow` (sector), `glossSurfaceType <custom>` with `glossRangeMin 0` / `glossRangeMax 13`, `reflectionProbeAmount 1`, `specColorTint 0.76 0.76 0.76`, and a block of `gCustomReflectionProbe*` fields left at neutral values [VERIFIED] (src: t7_water.gdt).

### 4d. The stock textures, and how to import your own

- **Backscatter ramps are tiny.** `texture_assets/water/dirtywater_stream.tif` (the vats ramp) is 32×32, average RGB about 62/59/51 (brown-grey); `texture_assets/t7_materials/t7_water_mp_redwood_backscatter_c.tif` (the Sector ramp) is 32×32, teal fading to dark violet [VERIFIED measurement].
- **Refraction ramps** (`texture_assets/water/water_refraction_ramp.tif`, `..._zfeather_small_ramp.tif`) are 128×1 strips from white to deep blue [VERIFIED measurement].
- **Flow maps** are 1024×1024 16-bit RGB, blue channel 0 or nearly so, red/green near 128 where there is no flow [VERIFIED measurement]. The encoding (RG = direction, 0.5 = still) is the standard one [INFERRED].
- **Opacity colour maps** `t7_water_variants_01_color_{100,40,5}.tif` share one murky green-grey colour and differ only in alpha (about 255 / 96 / 45 average) [VERIFIED measurement].
- **Import rules** [VERIFIED] (src: t7_water.gdt and model_export/t7_props_water.gdt image blocks): flow maps `compressionMethod uncompressed`, `semantic 2d`; foam as a `revealMap` (compressed); backscatter ramps as `diffuseMap` (the Sector ramp "compressed high color", the vats ramp "compressed no alpha"); water normal as `normalMap`, compressed. Compressing a flow map would quantise its directions [INFERRED].

---

## 5. The stock water materials to copy

**Plain version.** Treyarch shipped only a handful of real water materials. Copy one of them in APE into our own GDT and change what you need; do not start from an empty material and do not edit the stock one.

**The four stock materials that use the water-sim family** [VERIFIED] (src: grep of `materialType` across MODTOOLS GDTs):

| Material | Material type | Defined in | What it is | Notes |
|---|---|---|---|---|
| `t7_water_zm_der_vats` | `lit_water_sim_flow_normal_color` | `texture_assets/t7_water.gdt:2` | Near-still vat water, used in The Giant | Flow rate 0.01, SSR + looped SSR on, `zFeatherDepth 1000`, overwater opacity 0.98, `surfaceType water`. **Every image it uses is defined in GDTs present in both the shared tools and the private workspace** (t7_water.gdt, art_assets/t6_legacy/texture_assets/water.gdt, model_export/t7_props/p7_eth_vista_water/p7_eth_vista_water.gdt) [VERIFIED on disk; link untested] |
| `t7_water_sector_flow` | `lit_water_sim_flow_normal` | `texture_assets/t7_water.gdt:1319` | Flowing shallow water with foam (MP Sector/Combine) | Flow rate 0.8, foam on, SSR off, `surfaceType watershallow`. ⚠ Its unused slots name images defined in **no** local GDT (`karma_rock_01_tiled_wet_c`, `river_1_n`, `waterfall_01_n`, `karma_falling_water_drip_pattern`, `i_water_sim_test_foam_m`, `compass_objpoint_airstrike_busy`) [VERIFIED]; whether the linker tolerates that is untested [TEST] |
| `mtl_p7_cai_waterfall_01` | `lit_transparent_water_flow` | `model_export/t7_props_water.gdt:47` | Material of the stock waterfall model `p7_cai_waterfall_01` | Foam on, SSR off, overwater/underwater opacity 0.5, gloss max 6, `usage "<not in editor>"` (a model material, not for painting brushes) |
| `mtl_p7_cai_waterfall_01_small` | `lit_transparent_water_flow` | `model_export/t7_props_water.gdt:959` | Same, for `p7_cai_waterfall_01_small` | as above |

The same `t7_props_water.gdt` also defines the **xmodels** `p7_cai_waterfall_01` and `p7_cai_waterfall_01_small`, and their `XMODEL_BIN` sources exist under `model_export/t7_props/p7_cai_waterfall_01/` [VERIFIED on disk; the GDT is present in the private workspace]. Whether they convert and render in a usermap is untested [TEST].

**The two simple see-through ones** in `t7_water.gdt` [VERIFIED]:

| Material | Material type | Colour map (alpha = opacity) | Other |
|---|---|---|---|
| `t7_water_sector_opacity_40` | `lit_transparent` | `i_t7_water_variant_opacity_40_c` (alpha ≈ 96/255) | gloss 6–17, `translucentShadowOpacity 32`, `surfaceType water` |
| `t7_water_variant_opacity_5` | `lit_transparent` | `i_t7_water_variant_opacity_5_c` (alpha ≈ 45/255) | same |

**Which one to start from.** For anything in this map, start from `t7_water_zm_der_vats`: it is the only one proven in a zombies map, its dependencies are all present, and it keeps non-sun lights (see [6](#6-how-water-is-lit-and-how-it-reflects)). Clone it under a `tod_water_*` name into a map-owned GDT (for example `source_data/tod_water.gdt`, synced to the private workspace by the guarded tools), never into the shared Mod Tools root (docs/154 isolation rule).

---

## 6. How water is lit and how it reflects

**Plain version.** Real water is mostly a mirror with a little colour. What makes BO3 water look right is what it reflects, and BO3 has no automatic real-time mirror. Water gets its look from four sources:

1. **Reflection probes (always).** Probes are cubemap snapshots baked during the lighting build: "Global specular lighting in multiple, 256x256, blended reflection probes" [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 5). The water reflects the probe whose box covers it, and the probe's reflection planes decide how that reflection lines up with the room: "Reflection planes tell the probe where the walls are, so reflections will parallax correctly" [VERIFIED] (src: docs_modtools/Probe/Reflection_Probes.pdf p.2). Everything about fitting probes is in [06 — reflections and probes](06_reflections_probes.md#4-shapes-boxes-blends-reflection-planes-multiface-subtract-override-virtual).
2. **Screen-space reflection (SSR), optional.** The checkbox `useScreenspaceReflection` (plus `useLoopedScreenspaceReflection`, "higher quality") and its three ray settings exist **only** on the `lit_water_sim` family and `water_shore(_flow)_igc`, not on ordinary materials; among stock materials only `t7_water_zm_der_vats` turns it on [VERIFIED] (src: deffiles/material.awi:1165-1177; grep of techsetdefs and GDTs). SSR can only reflect what is on screen, so it catches moving things (zombies, muzzle flashes, FX) but loses anything that leaves the frame [INFERRED from how SSR works]. The user's `players/config.ini` has no SSR setting; its only reflection setting is `TextureQualityProbes` ("Number of mips to drop on reflections") [VERIFIED].
3. **Forward highlights from lights.** `lit_water_sim`, `_flow_normal` and `_flow_normal_color` do not define `DISABLE_FORWARD_NON_SUN_LIGHTS`; the `_only_sun*` variants and `lit_transparent_water_flow(_nocull)` do [VERIFIED define placement] (src: geometry/lit_water_sim_flow_normal_only_sun.techsetdef:35-37; lit_transparent_water_flow.techsetdef:23). By the define's name, those variants drop the forward lighting of every light except the sun, so a point light such as a neon omni would give them no highlight [INFERRED; no shader source ships, only compiled blobs]. Outside water the define appears only on `lit_transparent_cheap(_offsets)`, which suggests it is a cheapness switch [VERIFIED placement]. **In a map lit by `light` entities rather than a sun, use a variant without it** [INFERRED].
4. **Refraction and colour by depth.** The shader distorts the scene under the surface (Refraction Distortion Amount) and tints it with the backscatter and refraction ramps; the Z feather softens where water meets geometry [VERIFIED slot names; look untested].

**The physical numbers** [VERIFIED] (src: deffiles/material.awi):
- The Specular Color palette lists `Water` at sRGB 0.149 (line 882) and `Everything` at 0.2196 (line 864). In linear terms that is about 0.02 against 0.04, the textbook reflectance of water versus ordinary non-metals [INFERRED arithmetic]: water reflects about half as much head-on.
- The `water` gloss preset is **6..17** (lines 270-274); 17 is the maximum gloss the engine supports ("Maximum glossiness of 2^17", PBR deck slide 5). Note that both stock flow materials override this with a custom 0..13.
- The **Occlusion** map controls "the amount of ambient light that will light the surface and the amount of reflection probe that will visible on the surface" [VERIFIED] (src: Materials.pdf p.1). Use it to stop a wet corner glowing with a reflection it should not have.

**What a dark map does to reflections.** Treyarch's 2016 talk describes a *reflection brightness correction*: a soft cap that strongly damps a reflection where the pixel's baked diffuse light is dark compared with the reflected colour, and passes it almost unchanged where the diffuse light is high [VERIFIED as described in the talk] (src: https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf). That it runs in retail BO3 exactly as on the slide is [INFERRED]. The consequence for a dark map [INFERRED, TEST]: water in a pitch-black room may show weak neon reflections even when its probe captured the neon brightly. Two levers are worth trying, both [INFERRED; TEST]: a `PROBE_ONLY` light near the neon ("this light will only be seen by the reflection probes"), and the probe's `brightnessAdjust` (−5..5, "scale the brightness of the bounce during bake"). The definition puts `brightnessAdjust` in its diffuse-GI (bounce) group, not with reflections [VERIFIED] (src: bin/t7.def.json), so it could only help by raising the baked light the correction compares against [INFERRED]. Details are in [06 §9](06_reflections_probes.md#91-reflection-brightness-correction) and [01 — lights](01_lights.md#10-bounce-bake_intensity_scale-and-probe_only).

**A point light has no body in a cubemap.** For a lamp or sign to show up *in* the water, the probe must see something bright: an emissive lamp head, sign or strip [INFERRED] (see [03 — glow](03_glow_and_perks.md)). The runtime light adds a highlight on top.

**Why water renders black.** A modme user's water was black because lighting had not been compiled: "you need to compile light in the launcher... Your character is white so i see you didnt" [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3557.html). In this repo that means a FULL build; `-GscOnly` never re-bakes probes (src: CLAUDE.md build rules).

**A real mirror exists only as a scripted route.** There is no automatic planar or mirror technique [VERIFIED: none in techsetdefs_stable]. There is a script-driven render-to-texture route: `specialty/lit_extracam_reflection.techsetdef` ("lit forward opaque") samples `extracamTexture1..4`, with a material "Camera Index" of 1–4, a wobble normal and "ExtraCam Warp Amount". It is fed by the client API `<entity> SetExtraCam( index, width, height )` on a camera entity, whose index runs 0–3 [VERIFIED] (src: techsetdef; bo3_scriptapifunctions.htm). That script index n feeds material Camera Index n+1 is [INFERRED]. No stock material uses it and it is untested in a zombies usermap [TEST]. The community says true mirrors are not achievable [COMMUNITY] (src: https://forum.modme.co/wiki/threads/2946.html), which is consistent with this being an advanced, uncommon route. Details belong to [06](06_reflections_probes.md#11-screen-space-reflections-and-real-mirrors).

**Shadows.** `lit_water_sim` has `castsShadows = false`, so water never blocks light [VERIFIED]. `wave_water`'s `cast_shadow` gives a translucent shadow whose opacity comes from the material [VERIFIED def text].

**Water and lighting states (power off / on).** Radiant keeps probe irradiance, exposure and sun-shadow data indexed per lighting state, and the SunSky doc says each lighting state has its own runtime lighting and an optional baked-lighting override [VERIFIED field names and doc wording] (src: SunSky_Light_SetUp.pdf; Radiant_modtools.exe strings). So water most likely reflects the probe data of the state that is running [INFERRED]. Which states actually get baked is open: the compiled `.led` lists `default_day` for sun-volume slots that were left empty. In Tower of Doom II every light is `lightingstate` 0,1,1,1 (off only in Radiant State 1) and no script changes the state, so all lights are most likely on from spawn and water would see a single state [INFERRED] (see [02 — power and states](02_power_and_states.md)). Once states are used, compare a puddle before and after power [TEST].

---

## 7. What Radiant shows you is not the game

- In the Radiant build (`TOOLSGFX`), `lit_water_sim` uses render flags `"lit transparent distortion"` and a `blend + depth` lit pass, instead of the in-game opaque water pass [VERIFIED] (src: geometry/lit_water_sim.techsetdef; include/lit_water_sim_base.techsetdef). The editor preview is a different render path from the game.
- The community says water materials only display with Radiant's **Realtime Rendering** on [COMMUNITY] (src: modme wiki Setting-up-water).
- The clip-water brushes show their editor images (`water`, `water_shallow`), a blue grid; "they don't look like water in radiant but when you compile they will" (that post is about World at War, same idea) [COMMUNITY] (src: https://www.ugx-mods.com/forum/mapping/12/invisible-water-i-want-it-visible-to-players/11066).
- Probes and SSR only exist after a lighting bake and in game.

Judge water only in game, after a full build, from the same spots every time (see [09 — how to judge lighting](09_design_and_inspiration.md#7-how-to-judge-lighting)).

---

## 8. The underwater look

**Plain version.** When the camera goes below the surface you want blur and colour loss. BO3 does this with a *position-based grade* box (`pbg_box`), placed and sized like a reflection probe, with one flag switched on.

`pbg_box` ("position based grade box modifier") keys [VERIFIED] (src: bin/t7.def.json):

| Key | Spawnflag / default | Meaning |
|---|---|---|
| `USE_UNDERWATER` | spawnflag **65536**, default off | turns the underwater block on |
| `underwater_mix` | 1 (0–1) | "underwater blend" |
| `underwater_halfdistance` | 450 (1–20000) | "underwater 50% blur distance" (lower = murkier) |
| `underwater_absorptionRGB` | `0.34 0.0325 0.0114` (0–1 each) | "underwater color absorption coefficients"; the default absorbs red fastest, so the view turns blue-green |
| `size_min` / `size_max` | `72 72 72` | area of effect on the negative / positive side (half-extents) |
| `blend_mins` / `blend_maxs` | `4 4 4` | distance to blend out |
| `LIGHTSTATE_1..4` | 16 / 32 / 64 / 128; **only LIGHTSTATE_1 on by default** | which lighting states the box works in |
| `BANK_1..4` | 1 / 2 / 4 / 8; BANK_1 on by default | |
| `USE_UKKO`, `USE_BLOOM`, `USE_LUT`, `USE_COLOR` | 4096 / 8192 / 16384 / 32768 | the same box can also swap grades (The Giant uses pbg_boxes for its grades) |

`pbg_omni` has no `USE_UNDERWATER` [VERIFIED]. **Do not read the keys as proof the grade is on:** The Giant has 17 pbg_boxes. The 15 in `zm_giant_light.map` all carry the default `underwater_*` keys, but none of the 17 sets bit 65536 (spawnflags 45329 on the 15; 61457 and 61473 on the two in `light/zm_giant_post.map`) [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map, light/zm_giant_post.map). No stock prefab enables the underwater grade.

⚠ **The lighting-state gotcha.** Because `LIGHTSTATE_1` is the only default, and a zombies usermap boots in script state 1 = Radiant State 2 (see [02](02_power_and_states.md#2-radiant-state-n-and-script-state-n)), a default-flagged pbg_box would be inactive for the whole match unless `LIGHTSTATE_2` is ticked [INFERRED from the def and the state mapping; TEST]. The Giant's own grade boxes are flagged per state: its 15 boxes (45329) are `LIGHTSTATE_1` only, and its two post boxes are a same-sized pair, one `LIGHTSTATE_1` (61457) and one `LIGHTSTATE_2` (61473) [VERIFIED bits]. Example spawnflags for underwater in Radiant States 1 and 2, bank 1: 1 + 16 + 32 + 65536 = **65585** [INFERRED arithmetic from the def bits].

Other underwater levers:
- Client API `<entity> SetUnderwaterVisionSet( "visionName" )`: "Set the vision when underwater" [VERIFIED] (src: bo3_scriptapifunctions.htm).
- Stock `shared/water_surface.csc` (loaded by `load_shared.csc:8`) waits for `underwater_begin` / `underwater_end` and plays postfx bundles `pstfx_watertransition` / `pstfx_water_t_out` plus 1p FX `player/fx_plyr_water_jump_in_bubbles_1p` / `..._jump_out_splash_1p`; `level.disableWaterSurfaceFX = true` turns it off [VERIFIED script] (src: share/raw/scripts/shared/water_surface.csc:26-129). That the engine sends those notifies is [INFERRED]; whether the postfx assets load in a usermap without zone lines is [TEST].
- Engine string `player_disableUnderwaterVisionset` [VERIFIED string; INFERRED to be a dvar].
- Audio: `snd_underwater` in `shared/audio_shared.csc:927` (driven by `IsUnderwater( localClientNum )`) and underwater/emerge-breath VO in `zm/_zm_audio.gsc:1855-1868` [VERIFIED].

---

## 9. Script API for water

From the engine function list (src: MODTOOLS/docs_modtools/bo3_scriptapifunctions.htm) [VERIFIED text and side; behaviour untested]. No shipped script in `share/raw/scripts` calls the wave-water, underwater-vision, disturbance, ripple, water-drop or sheeting-FX functions; the stock screen sheeting in `water_surface.csc` goes through `filter::` post-process filters instead [VERIFIED by grep].

| Function | Side | Summary (quoted or close) |
|---|---|---|
| `<entity> DepthInWater()` | Server | depth in inches, 0 if not in water; "Will work for all water types" |
| `<player> DepthOfPlayerInWater()` | Server | same, "More effecient ... but will only work for players" |
| `GetWaterHeight( pos )` | Server | "Returns the height of the water at this position" |
| `<player> IsPlayerSwimming()`, `IsPlayerUnderwater()` | Server | swim / underwater state |
| `<entity> IsPlayerSwimmingOnSurface()`, `IsPlayerSwimmingUnderwater()` | Client | swim state |
| `<player_actor> Underwater()` | Client | "checks if the player or actor is underwater" |
| `IsSwimming( lcn )`, `IsUnderwater( lcn )` | Client | local player state |
| `<player> GetLastOutWaterTime()` | Server | "last time the player was not completely submerged" (the drown system uses it) |
| `<entity> GetPlayerLastOutWaterTime()` | Client | same idea, client side |
| `<player> WalkUnderwater( bool )` | Server | "true if player should walk underwater. False if player should swim" |
| `SetWaveWaterEnabled( name, enable )` | Client | "Makes a water completely appear or disappear" (`""` = all) |
| `SetWaveWaterHeight( name, height )` | Client | "Sets the height of one or all waters in a level" (world Z) |
| `SetWaveWaterGeneratorAmplitude( name, amp )` | Server | amplitude of a `wave_generator` |
| `<entity> SetWaterDisturbanceParams( force, length, width, damping, angle )` | Client | wave disturbance made by a script mover; example `(0.5, 500, 1500, 0.2, 70)` |
| `<player> SetWaterDrops( count )` | Server | "Sets water drops equal to the count" |
| `StartWaterSheetingFX( lcn, [duration], [magnitude] )` / `StopWaterSheetingFX( lcn, [duration] )` | Client | "Play a fullscreen water effect" (duration 0 = until stopped) |
| `SetRippleWave( lcn, x, y, width, speed, ampRatio, fadeInStart, fadeInEnd, fadeOutStart, fadeOutEnd )` | Client | "Trigger vertex ripple wave for material set to use it" |
| `<entity> SetUnderwaterVisionSet( name )` | Client | underwater vision |
| `<vehicle> SetBuoyancyOffset( offset )` | Server | vehicle float height |

---

## 10. Players and zombies in water

**Players.** The engine has a full swim model. The compiler binary contains these player strings, which look like the game's water dvars [VERIFIED strings; INFERRED to be dvars; of this list, stock script reads only `player_swimHeightRatio` (`shared/bots/bot_traversals.gsc:53`), while `drown.gsc` reads three others with `GetDvarFloat`, see below]: `player_swimming_enabled`, `player_shallowWaterHeightRatio` ("Ratio of player standing hieght player is considered in shallow water"), `player_swimHeightRatio` ("If the water level is above this ratio of player height player will be in swimming state"), `player_swimUnderwaterHeightRatio`, the friction scales `player_shallowWaterFrictionScale` / `player_waistWaterFrictionScale` / `player_chestWaterFrictionScale` / `player_deepWaterWadeScale`, `player_disableWeaponsInWater`, `player_underwaterWalkSpeedScale`, `player_swimSpeed`, `player_swimallowshooting`, `player_swimAllowGrenades`, `phys_waterDragLinear/Angular` (src: bin/cod2map64.exe string extraction).

- Zombies sets `level.swimmingFeature = false;` (`_zm.gsc:274`, `_zm.csc:108`) but **no shipped script reads it** [VERIFIED grep]. The default of `player_swimming_enabled` in a zombies usermap is unknown [TEST].
- **Drowning is live in zombies.** `shared/drown.gsc` is `#using`'d by `load_shared.gsc:21`, which zombies loads. While `isplayerunderwater() && isplayerswimming()`, it counts from `getlastoutwatertime()` and after `player_swimTime` deals `player_swimDamage` every `player_swimDamagerInterval` as `MOD_DROWN`, with an overlay [VERIFIED] (src: share/raw/scripts/shared/drown.gsc:23-105). The values of those dvars in zombies are unknown [TEST].
- **Revive in water.** `_zm_laststand.gsc:891` reads the downed player's `depthinwater()`; when a secondary revive trigger exists, depth over 20 is enough to show the revive prompt. With `level.can_revive_use_depthinwater_test` set, depth over 10 makes `can_revive` return true (`:1073`) [VERIFIED].
- Zetsubou No Shima brought swimming to zombies, but its scripts are not shipped: only `zm_giant*` and `zm_usermap*` map scripts exist in `share/raw/scripts/zm` [VERIFIED ls; Zetsubou fact COMMUNITY].

**Zombies cannot swim.**
- No swim behaviour exists in the shipped AI (no swim or water entries in `share/raw/behavior` or `animstatemachines`) [VERIFIED absence]. A mapper reports "The zombies and dogs still treat the pond like a normal pit however, and run around on the bottom of it" [COMMUNITY] (src: modme thread 298, Abnormal202).
- AI walk the navmesh, so water must sit over walkable, navmeshed floor, or zombies cannot reach players standing in it [INFERRED]. In this repo the navmesh is a hard build gate (`tools/lint_tod_navmesh.js`, CLAUDE.md).
- `shared/ai/zombie.gsc:86, 907-958` registers a behaviour-tree condition `zombieShouldJumpUnderwaterMelee`: zombie at least 48 in. deep (`DepthInWater`), enemy off the ground and more than 48 above it (dvar `zmMeleeJumpUnderwaterHeightDifference`), within 64 horizontally (dvar `zmMeleeWaterJumpDistance`) [VERIFIED script]. No shipped `.ai_bt` references it [VERIFIED absence]; whether the compiled zombie tree uses it is unknown [TEST].
- Risers: a spawner struct with `script_parameters "in_water"` sets the `zombie_riser_fx_water` clientfield unless `level._no_water_risers` is true (`_zm_spawner.gsc:3090`) and plays `rise_dust_water` from the server (`:3141`) [VERIFIED]. On the server that "water" dust is just the ordinary dirt effect (`_zm.gsc:1702-1704`). On the client the clientfield plays the sound `zmb_zombie_spawn_water`, but the burst/billow effects are defined only when `level.use_new_riser_water` is true (`_zm.csc:282-287`); otherwise they stay undefined and `rise_dust_fx` skips them. The effects that flag would select (`_t6/maps/zombie/fx_mp_zombie_hand_water_burst`, `fx_mp_zombie_body_water_billowing`, `fx_zombie_body_wtr_falling`) are **all 5,092-byte placeholder stubs** [VERIFIED script and size]. Per this project's stub rule, never zone them (see [04](04_fx_lights.md#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)). A map can supply its own effects through `level.zombie_custom_riser_fx_handler`, which `rise_dust_fx` checks first [VERIFIED script].
- `self.in_water` is only read in the damage path (`_zm.gsc:5757`) and never set; `level.zombie_melee_in_water` is set true (`_zm.gsc:276`) and never read [VERIFIED grep]. Both are dead lanes unless the map writes them.

---

## 11. Surface types, splashes and footsteps

**Plain version.** A material's Surface Type decides its footstep sounds and bullet-impact effects. Water has two: `water` and `watershallow`.

| What | Stock mapping | Source |
|---|---|---|
| Bullet impacts | `Surface20` (water) and `Surface38` (watershallow) → `impacts\fx_bul_impact_water_lg.efx` (enter and exit), `_sm` in the small table | source_data/surfacefximpacts.gdt; deffiles/surfacefxtable.awi [VERIFIED] |
| Player footstep sounds | `fly_step_{run,walk,sprint,crouch_*,prone,ladder_hand}_plr_water` / `_watershallow` aliases | source_data/defaultplayerfootstep.gdt:41-300 [VERIFIED] |
| Player footstep / land / jump **particles** | ⚠ Surface20 and Surface38 map to **dust** FX (`fx_plyr_footstep_dust`, `fx_plyr_land_dust_md`, `fx_plyr_jump_dust`...) | source_data/surfacefxtables.gdt [VERIFIED] |
| Player splashes | `player\fx_plyr_water_splash_{sm,md}.efx`, `fx_plyr_swim_bubbles_body.efx` | source_data/playerfxtables.gdt:16-20 (`splashSmall` … `splashMassive`, `underWaterBreathing`) [VERIFIED] |
| Zombie footsteps in water | `setFootstepEffect( "water", "_t6/bio/player/fx_footstep_water" )` | zm/_load.gsc:134 [VERIFIED]; the source is a 5,092-byte stub [VERIFIED size]: do not zone it |

So in stock data, water surfaces give correct sounds and bullet splashes but dusty footstep particles [VERIFIED data; in-game result TEST]. Changing that means authoring a custom surface FX table.

Note that the stock `_wet` materials keep their dry surface type (`asphalt`, `concrete`, `brick`, `metal`, `rock`...) [VERIFIED] (src: texture_assets/t7_*.gdt): a wet-look floor sounds and splashes like the dry material. The stock puddle decals carry `surfaceType water` [VERIFIED].

---

## 12. Wet surfaces without water

**Plain version.** Most of the "rain-slick neon street" look in games is not water at all. It is a very glossy floor that mirrors the lights and signs around it, plus a few puddle patches. In BO3 that means high-gloss ordinary materials, gloss decals and good reflection probes. It is cheap, it cannot trap zombies, and it needs no volume.

### 12a. How Treyarch makes a surface wet

There are **26** stock `t7_*` materials with `_wet` in the name [VERIFIED count] (src: texture_assets/t7_{asphalt,brick,concrete,decal_grunge,glass,metal,mud,stone}.gdt). If you count only names that *end* in `_wet` you get 15, which is why other counts of "15 wet materials" exist; the other 11 are `_wet_nw`, `_wet_blend`, `_wet_0N` and similar. No technique implements "wetness": no techsetdef does it, and the `gWetnessNormalStrength` / `gWetnessRoughnessLobe0` fields in `material.awi` are read by no techset [VERIFIED]. Stock "wet" is **ordinary materials with a raised gloss range and sometimes a wet-specific normal map**:
- 16 of the 26 are plain `lit`; the other 10 are `lit_detail`, `lit_decal_reveal` (2), `lit_micro_tile_blend`, `lit_micro_tile_blend_advanced`, `lit_decal_metallic_fullspec` (3), `lit_decal_diffuse_spec_gloss` and `lit_backlit_plus` [VERIFIED].
- `glossRangeMax` is 17 on only 7 of them; the rest use 4 to 15 (bricks 11–12; `t7_concrete_bare_wet_warm` is 0..4) [VERIFIED]. The editor range tops out at 17, default 0..13 (material.awi:904) [VERIFIED].
- Several reuse the **dry** normal map (e.g. `t7_concrete_bare_dark_01_wet`, `t7_concrete_floor_garage_cracked_wet_nw`, `t7_concrete_trim_beveled_01_wet`); others use a dedicated `*_wet_n` [VERIFIED].
- Worked example: `t7_concrete_bare_dark_01` is `lit_plus`, gloss 0–2; its `_wet` twin is `lit`, gloss **0–17**, same colour, normal, AO and `$spec_simple`, `reflectionProbeAmount 1` [VERIFIED] (src: texture_assets/t7_concrete.gdt:3737, 4649).

Good floor candidates to paint by name: `t7_asphalt_damaged_dark_wet` (lit, 0–17, wet normal), `t7_concrete_floor_garage_cracked_wet_nw` (lit, 16–17), `t7_stone_cobblestone_01_wet_nw` (lit, 0–17), `t7_concrete_bare_dark_01_wet` (lit, 0–17), `t7_metal_diamond_plate_worn_wet` (lit, 8–15, metal) [VERIFIED fields].

**Stock zombies precedent.** The Giant paints thousands of faces with stock wet materials, e.g. 2,170 faces of `t7_brick_worn_dirty_red_wet`, 1,817 of `t7_concrete_trim_beveled_01_wet`, 1,253 of `t7_concrete_poured_bunker_dirty_01_wet` [VERIFIED count] (src: MODTOOLS/map_source/_prefabs/zm/zm_giant), and The Giant's scripts (`share/raw/scripts/zm/zm_giant*.gsc|csc`) contain no rain or water logic [VERIFIED by grep]. Map One uses `t7_asphalt_damaged_dark_wet` as its dominant ground (285 faces in `MODTOOLS/map_source/zm/zm_abandoned_cyber_city.map`) [VERIFIED count] and recorded adding 15 reflection probes "so neon mirrors in the wet ground" [COMMUNITY] (src: abandoned_cyber_city_zombies/docs/20_atmosphere_and_materials.md).

**Why the probe matters more than the material.** A wet floor is a mirror of its probe. A mis-sized probe makes it smear or reflect the wrong room [INFERRED; project memory `vertigo-materials-are-mirrors`]. Fit the probe first ([06](06_reflections_probes.md)).

### 12b. Puddles

- Stock `t7_decal_grunge_water_puddle_02` and `t7_decal_grunge_water_puddle_blend` are `lit_decal_normal_gloss_reveal` decals with an `alphaRevealMap` puddle shape, no normal map, `glossRangeMin 6` / `Max 17`, `surfaceType water`, `layerSortDecal Water`, `colorTint 0.749` (the "Albedo Darken") and zero scroll [VERIFIED] (src: texture_assets/t7_decal_grunge.gdt:47399, 48311).
- `_02` is shaped by its reveal map, so it works on a flat face. `_blend` is revealed by **vertex alpha**: The Giant places it as a coplanar 10×9 patch mesh with `contents nonColliding;`, `decalLayerSort "Water"` and per-vertex alpha 0 or 150 painting where the puddle shows (90 vertices: 65 at 0, 25 at 150) [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/geo/zm_giant_hotel.map:14900-15022). On a plain brush face with no painted alpha it would likely draw nothing [INFERRED].
- **Decal rule:** decals "should be authored on coplanar geometry", and "Deferred decals (all shaders with lit_decal in the name) will only layer properly over other deferred surfaces. So, do not try to stack decals on top of transparent shaders" [VERIFIED] (src: Materials.pdf p.2).
- ⚠ **This matters for our world kit.** Plain `lit`, `lit_plus` and `lit_advanced` are `"lit deferred opaque"` (`isGbuffer = true`), but `lit_emissive`, `lit_emissive_plus` and `lit_emissive_advanced` are `"lit forward opaque"` (no gbuffer flag) [VERIFIED] (src: share/raw/techsetdefs_stable/renderFlags.techsetdef; geometry/lit.techsetdef, geometry_plus/, geometry_advanced/). Every visible Tower of Doom II brush face except the sky uses a forward-rendered emissive material (66,402 faces when counted on 2026-09-23: the vertigo kit plus the `tod_door_*` / `tod_hall_*` clones, all `lit_emissive_advanced`; see [03](03_glow_and_perks.md)) [VERIFIED], so a `lit_decal_*` puddle painted onto them would probably not layer correctly [INFERRED from the doc rule; TEST].
- Alternative placement: a `misc_volume_decal` (`decalsize` = half size, `modeloverridematerial`, `edgeFeatherX/Y/Z`) [VERIFIED def]. The Giant places 407 of them, mostly snow and blood [VERIFIED count]. Whether a volume decal layers over a forward-rendered surface any better than a painted decal is unknown [TEST].

### 12c. Water running over a surface

The documented stock route: **Lit Decal Normal Gloss Reveal** "was created for adding flowing water on opaque surfaces. With that in mind, it only uses a normal, gloss, and reveal map", and its normal map "is tiled and scrolled twice to proved [provide] the water surface with its ripply appearance" [VERIFIED] (src: Materials.pdf p.19). Four stock Treyarch materials use it: the two puddles and `t7_decal_grunge_scratch_pockmark` in `t7_decal_grunge.gdt`, and one in `model_export/t7_props_industrial_small.gdt` [VERIFIED count]. Three more in the shared tools root belong to BO4/BO6 ports installed later (`p8_*`, `t10_materials.gdt`), not to the stock kit.

| APE control | GDT keys | Doc meaning |
|---|---|---|
| Reveal Map | `alphaRevealMap` | height map; white = most persistently visible (the wet shape) |
| Normal Map | `normalMap` | the ripple texture |
| Scale (U, V) | `gNormalScale00/01` | how many times the normal map tiles |
| Layer1 Scroll (U, V) | `gUVScroll02_Angle`, `gUVScroll03_Angle` | speed and direction of layer 1 |
| Layer2 Scroll (U, V) | `gUVScroll00_Angle`, `gUVScroll01_Angle` | speed and direction of layer 2 |
| Layer1 / Layer2 Height | `cloudLayer1Blend0/1` | normal strength per layer |
| Gloss Range | `glossRangeMin/Max` | |
| Albedo Darken | `colorTint` | darkens the surface under the water |

[VERIFIED] (src: share/raw/techsetdefs_stable/decal/lit_decal_normal_gloss_reveal.techsetdef:18-120). The `_flow` version follows a flow map instead of straight scrolls.

### 12d. Oil sheen, rain ripples and weather

- **Oily sheen:** `lit_decal_specular_fullspec` "replaces only the spec map of the material that is underneath"; use it "if you just need to add an oily sheen onto an existing material" [VERIFIED] (src: Materials.pdf p.20). Stock `t7_decal_grunge_oil_stain_wet_0{1,2,3}` are `lit_decal_metallic_fullspec` [VERIFIED].
- **Rain rings:** `lit_decal_raindrops` has a ripple normal hard-wired to image `rain_hit_n`, plus Mask Map, Albedo Darken, Scale, Ripple Speed (1–1024), Ripple Scale (1–1024), Gloss Range and Normal Flattening [VERIFIED] (src: decal/lit_decal_raindrops.techsetdef). The image `rain_hit_n` and the decals `t7_decal_raindrops` / `_fast` named on the zeroy wiki [COMMUNITY] are in **no local GDT** [VERIFIED absence]; whether they exist in the game's fastfiles is [TEST].
- **Weather volumes:** `volume_weathergrime` key `rain` (0–1): "Scales the amount of ripples on the wet materials (outdoors)", plus `windDirection` and `windSpeed` ("Direction/Speed of the ripple flow on wet materials") and weather colour/normal/gloss maps [VERIFIED def]. `volume_outdoor` decides what counts as outdoors with `pitch0..3`, `yaw0..3`, `filterRadius0..3` and `enabled0..3`, **all `enabledN` false by default**. These keys are numbered from 0: the definition calls them "light state 0" to "light state 3" [VERIFIED def]. How that numbering lines up with Radiant States 1–4 is not documented [INFERRED: probably enabledN = Radiant State N+1; TEST]. The Giant sidesteps the question: its one `volume_outdoor` ticks all four (`enabled0..3 1`, pitch 25, yaw 290) [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_geo.map). Which materials respond to `rain` is not documented [TEST]. MP Sector's weathergrime (`map_source/mp/mp_sector.map`) also carries `wetness 0.8`, `puddles`, `grimeAmount`, `weatherAmount`, which are absent from the current definition and treated as legacy [VERIFIED absence].
- **Screen rain:** `shared/filter_shared.csc` has rain-drop, sprite-rain and water-sheeting filters, and the engine has `StartWaterSheetingFX` [VERIFIED]; their materials are not in the local `genericfilters.gdt`, so availability in a usermap is [TEST].

---

## 13. Moving water: flow, waterfalls, drips, rising water

**Flow maps.** A flow map is a texture that says which way each part of the surface flows. Paint or generate one (16-bit RGB, red/green = direction, mid-grey = still [INFERRED encoding]), import it `semantic 2d`, `compressionMethod uncompressed` like the stock ones [VERIFIED], put it in `colorMap02`, and set Flow tile density (`cg04_x`) and Flow rate scale (`cg04_y`). Stock values: 150 / 0.8 for a fast shallow stream, 20 / 0.01 for a near-still vat [VERIFIED]. Use the noise map (`colorMap04`) to break repetition, and tick Orient normals to flow and Scale normals with local flow rate as both stock materials do [VERIFIED].

**Waterfalls.** Three ingredients, all stock:
- *Material:* `lit_backlit_waterfall` (opaque, cheaper) or `lit_transparent_backlit_waterfall` (see-through, OIT cost). Its "UV Motion" controls are Scroll Rate (`flagRipple1ScrollU/V`), "Rotation, Spin Rate" (`uvScrollAngle`, `uvRotationRate`), Scale (`detailScaleX/Y`), Offset (`uScroll`/`vScroll`), Zoom (Min, Max) and Zoom Rate, Perceived Depth (`detailScaleHeight`), Clamp U/V; the flag (vertex) motion is Flag Speed (`flagX`), Flag Phase (`flagY`), Backlight Bleed (`flagZ`), Wind Direction1–3 (`gFoamScrollAngle0-2`); and the "Backlight" group adds a Thickness Map (`alphaRevealMap`) and a Tint (`backlightScatterColor`) so lights behind it glow through [VERIFIED] (src: include/scroll_base, include/flag_motion_base, geometry/lit_backlit_waterfall.techsetdef).
- *Model:* the stock `p7_cai_waterfall_01` / `_small` xmodels with the `lit_transparent_water_flow` materials in [5](#5-the-stock-water-materials-to-copy) [VERIFIED defined; render TEST].
- *FX:* MP Sector places `water/fx_water_fall_sector` as a Radiant `fx` entity (`fxdef`, `delay -20453`, `fxstate1..4 1`, `primaryLightFraction 1`, `timescale 1`) [VERIFIED] (src: map_source/_prefabs/mp/mp_sector/fx/mp_sector_fx.map:1960-1971). Other stock options: `fx_water_fall_top_mist` at the lip, `fx_water_splash_fountain_line(_dark)` where it lands.
- *Walking through it (MP only):* `mp/_waterfall.csc` watches client triggers `targetname waterfall` / `waterfall_mist`, plays postfx `pstfx_waterfall`, a rumble and a sound on entry, `water_surface::startWaterSheeting()` on exit, and the sprite-rain filter for mist [VERIFIED script]. Porting it means copying it into our own namespace; asset availability in zombies is [TEST].

**Drips, leaks and sheets.** `MODTOOLS/share/raw/fx` holds 161 `.efx` in `water/`, 28 `weather/fx_rain*` and 13 water impacts [VERIFIED count]. Only three of those 202 are 5,092-byte placeholder stubs: `water/fx_water_drips_hvy` and the two `weather/fx_rain_system_{lite,med}_se_runner_blackstation` [VERIFIED size]. Useful real ones for a wet undercity: `water/fx_water_drip_line_25`, `_100`, `_100_lit`, `_200_lit`, `fx_water_drip_ceiling(_lg)`, `fx_water_drip_point_1x1`, `fx_water_drip_point_slow`, `fx_water_drip_edge_line_100`, `fx_water_leak_squirt_sm`, `fx_water_leak_torrent_md`, `fx_water_sheet_line_100`, `fx_water_stream_falling_thin_15x200` / `_15x500`, plus the 33 `steam/fx_steam_*` [VERIFIED present; none is stub-sized]. Map One shipped `water/fx_water_drip_line_25` and `water/fx_water_drip_ceiling` [COMMUNITY] (src: abandoned_cyber_city_zombies/docs/20_atmosphere_and_materials.md). How to place and zone FX, the placeholder-stub trap and the project's server-PlayFX heuristic are in [04 — FX lights](04_fx_lights.md). Scripted FX need a `fx,<path>` zone line and a `#precache` unless a base-game zone already loads the effect [COMMUNITY recipe; see 04].

**Rising or draining water.**
- For `wave_water`, the client API `SetWaveWaterHeight( name, z )` moves the level [VERIFIED API; TEST].
- For plain water, a UGX tutorial moves a `script_brushmodel` in steps with `MoveTo( origin + (0,0,15), 5 )` [COMMUNITY] (src: https://www.ugx-mods.com/forum/scripting/91/tutorial-rising-water/13844/). Whether a clip-water brush inside a moving `script_brushmodel` moves its water volume is unverified [TEST]. Remember that anything script-spawned and solid needs `DisconnectPaths()` / `ConnectPaths()` for the navmesh (CLAUDE.md).

**Glowing liquid.** For neon coolant or toxic sludge, use `lit_emissive_lava_flow`: an emissive material with flicker, scroll and flow, rendered "lit forward opaque" [VERIFIED]. It glows; it does not light the room. Pair it with a real `light` for the spill light (see [03](03_glow_and_perks.md), [01](01_lights.md)). The `lit_emissive_lava_flow_script` variant adds Tint State 2–4, a "Tint (Brightness, State)" control and `USE_SCRIPT_CONTROLS` [VERIFIED] (src: specialty/lit_emissive_lava_flow_script.techsetdef), the same family of controls stock script drives with `MapShaderConstant` / `SetShaderConstant` for Der Wunderfizz (src: share/raw/scripts/zm/_zm_perk_random.csc:104-176); so a coolant trough could plausibly brighten at power [INFERRED; TEST] (see [03 — switching a glow](03_glow_and_perks.md#8-switching-a-glow-on-and-off)).

---

## 14. Caustics: light that ripples like water

**Plain version.** Caustics are the moving bright lines light makes on a wall or floor near water. BO3 fakes them with a **cookie** (a projected texture, also called a gobo) on a light, scrolled or rotated so it moves.

**The keys** on a `light` entity [VERIFIED] (src: bin/t7.def.json; Lighting_Parameters.pdf p.8-9); the general cookie section is [01 §12](01_lights.md#12-cookies-and-gobos):

| Key | Default | Meaning |
|---|---|---|
| `def` | `white_light` | the light-definition asset used as the cookie ("created in APE") |
| `def_scroll` | `0 0` (−10..10) | scroll; the definition text: "you enter a time in seconds which is how long it will take for the texture to travel across the full width / height of the light"; negative reverses |
| `def_rotation` | 0 (−720..720) | t7.def.json: "Rotate the texture in degrees per second"; Lighting_Parameters.pdf: "Rotate the texture 360 degrees in the seconds time specified". **The two sources disagree** |
| `def_tile` | `1 1` | tile the cookie x/y times so a small texture can repeat |
| `def_offset`, `def_shear`, `def_angle`, `def_center` | 0 | alignment; `def_angle` is a static rotation |
| `volumetricCookies` | false | "Enables cookies on volumetrics" (needs `volumetric`, which the user's config disables) |

**Stock caustic cookies** in `texture_assets/t7_light_gobo.gdt` [VERIFIED]: `cookie_caustics_01` (`gobo_caustics_512.tif`), `cookie_caustics_layered` (`gobo_caustics_layered_512.tif`), `cookie_caustic_ink` (`cookie_caustics_ink_01.tif`). The GDT is present in the private workspace [VERIFIED].

**How Treyarch actually uses them** [VERIFIED] (src: MODTOOLS/map_source/_prefabs/zm/zm_giant/zm_giant_light.map; mp/mp_sector/mp_sector_light.map; mp/mp_combine/mp_combine_light.map):

| Map | Type | Colour | Stops | Radius / FOV | `def_scroll` | `def_rotation` | `def_tile` | Shadows |
|---|---|---|---|---|---|---|---|---|
| The Giant (4 lights) | `PRIMARY_SPOT` | `1 0.51 0.29` (warm orange) | 8.97 | 325 / 70 | 0.05–0.1 on one or both axes, some negative | ±0.1 to 0.2 | `1 1` | `shadowUpdate Never`, spawnflags 68 |
| The Giant (2 lights) | `PRIMARY_OMNI` | same | 8.97 | 83 | `0.1 0.1` | — | `1 1` | Never, `PRIMARY_NOSHADOWMAP 1` |
| Sector / Combine (5 each) | `PRIMARY_SPOT` | pale green `0.72 0.77 0.58` (one warm white) | 15 | 78 / 130 (one 275 / 60) | `0.15`–`0.3 0` | — | `2 2` or `3 3` | mixed Never / Always |

The Giant uses `cookie_caustics_01` only; Sector and Combine mix `cookie_caustics_01` and `cookie_caustics_layered`; no stock prefab light uses `cookie_caustic_ink` [VERIFIED]. The Giant's six caustic lights are on in all four lighting states [VERIFIED].

Lessons from that table:
- Stock caustics are almost all **spot lights**. Two Giant omnis carry a caustic `def`, but whether an omni projects a cookie is not documented [TEST]. Use a spot.
- Stock sets only `def`. **No `ENABLE_COOKIE` key** appears in `t7.def.json` or in any stock map source, even though Lighting_Parameters.pdf p.11 says a sun-gobo material can be used on lights with `"ENABLE_COOKIE" set to "true"` [VERIFIED absence]. Do not author it.
- Stock uses cookies on `shadowUpdate Never` lights, so a cookie does not need live shadows [INFERRED from stock use].
- The stock `def_scroll` and `def_rotation` values are small (0.05–0.3). Under the "seconds to cross" reading, 0.05 would be very fast; under a speed reading it would be slow. Copy the stock values as a starting point and judge in game [TEST].

---

## 15. Recipes

Every recipe below is untested in game. Every one is a FULL build (materials, lights and probes bake in the LED pass; `-GscOnly` is not enough), built and stopped; the user judges the result (CLAUDE.md). In this repo the `.map` is generated: add geometry and entities in `tools/gen_tower_map.js`, never by hand-editing the `.map`. New materials go in a map-owned GDT in `source_data/` that the guarded sync places in the private workspace, never in the shared Mod Tools root (docs/154).

### 15.1 Puddle on a floor

1. Make sure the floor under it is a deferred material (`lit`, `lit_plus`, `lit_advanced`...), not a `lit_emissive*` one. Deferred decals only layer over deferred surfaces (Materials.pdf p.2); see [12b](#12b-puddles).
2. On a flat brush face: add a coplanar face (or `misc_volume_decal`) with `t7_decal_grunge_water_puddle_02`. On a patch where you want to paint the shape: use `t7_decal_grunge_water_puddle_blend` and paint vertex alpha (The Giant uses 0 and 150).
3. Make sure a reflection probe box covers the puddle and can see something bright (a sign, a lamp head); see [06](06_reflections_probes.md).
4. For a moving ripple, clone the decal, give it a ripple normal map (the stock puddles have none, so scrolling alone would change nothing) and small Layer1/Layer2 Scroll values; or use `lit_decal_raindrops` if its image turns out to exist ([TEST]).

### 15.2 Still pool or vat (look only, nobody enters)

1. Emit a flat patch or a single brush face at the water height, `nonColliding` like The Giant's vat. Put it a few units above any floor it covers so the two never z-fight [INFERRED].
2. Material: clone `t7_water_zm_der_vats` into `tod_water_*` in a map-owned GDT. Keep flow rate `cg04_y` about 0.01 for still water, SSR and looped SSR on, `zFeatherDepth` large (vats: 1000), `cg02_z` small (vats: 5).
3. For a dark map, author a 32×32 blue-black backscatter ramp for `colorMap` and a darker refraction ramp for `colorMap01`; keep Overwater Opacity high (0.95–1.0) so it reads as a dark mirror, not a window [INFERRED].
4. Build a dark bottom under the surface; refraction shows it, and a black bottom sells depth [INFERRED].
5. Place a `reflection_probe` whose `size_min`/`size_max` wrap the room around the pool, with a reflection plane on the water surface (ALT+Left Click snaps bounds, ALT+Right Click snaps reflection planes, at most six planes, Reflection_Probes.pdf p.1-2). Not the default `72 72 72` half-extents, which make a 144-unit cube.
6. Put coloured lights and emissive fixtures near the edge so the probe and the forward highlights have something to show. Use a non-`only_sun` technique.
7. FULL build. If the water is black, the bake did not happen or no probe covers it.

### 15.3 Shallow flooded floor or channel players wade through

1. Build the channel floor as normal walkable geometry that gets navmesh. Zombies will walk on it; they cannot swim.
2. Behaviour: one `clip_water_shallow` brush filling the flooded volume, its top face at the water surface (the stock example is 16 units thick). Use `clip_water` if you want the full water surface type. Never `clip_water_player`.
3. Look: a patch or face at the same height with a clone of `t7_water_sector_flow` (`lit_water_sim_flow_normal`, rebuilt without its dangling image slots) or of `t7_water_zm_der_vats`. `surfaceType watershallow` for shallow footsteps and splashes.
4. Flow map in `colorMap02` (16-bit, `semantic 2d`, uncompressed). Start from 150 / 0.8 (fast) or 20 / 0.15 (the technique default).
5. Optional foam against walls: `foamMapEnable 1`, `colorMap14 i_t7_water_foam_r`, foam scroll values copied from `t7_water_sector_flow`.
6. Optional: a riser struct in the water with `script_parameters "in_water"`. By default the server plays the ordinary dirt dust and the client plays a water spawn sound with no burst effect; do not set `level.use_new_riser_water`, because the water FX it switches to are stubs. For a real splash, supply map-owned effects through `level.zombie_custom_riser_fx_handler` (see [10](#10-players-and-zombies-in-water)).
7. FULL build. Ask the user to note wading speed, footstep sound, splashes on bullets, and whether zombies path through. Record which clip material was used.

### 15.4 River, sewer or coolant channel (dark cyber look)

1. Do 15.3, or skip the clip if the channel sits behind a rail out of reach.
2. Murky water: `lit_water_sim_flow_normal_color` with a dark Albedo Tint (`colorTint`) and a dark Color Decal Map (`colorMap03`). Glowing coolant instead: `lit_emissive_lava_flow` (or `_script` if it should change with power), plus a real spot or omni light along it for the spill light.
3. Oily banks: `lit_decal_specular_fullspec` or stock `t7_decal_grunge_oil_stain_wet_0{1,2,3}` over a deferred bank material.
4. Dress with FX: `fx_water_drip_line_25` / `_100_lit` under ledges, `fx_water_drip_ceiling`, `fx_water_leak_squirt_sm` from pipes, `steam/fx_steam_*` from vents; as Radiant `fx` entities or script (see [04](04_fx_lights.md)). Zone only real `.efx`, never the 5,092-byte stubs.
5. A caustic spot light on the wall above (15.9).
6. FULL build and stop.

### 15.5 Flooded floor over a glowing grid

For this map's world kit specifically [INFERRED; TEST]:
1. Leave the vertigo floor as it is and place a `nonColliding` water patch a few units above it, with a clone of `t7_water_zm_der_vats`.
2. The water pass refracts the already-rendered scene, so the glowing grid should show through, bent by the ripples, while the surface reflects the probe and (with SSR) moving zombies.
3. Keep Overwater Opacity below 1 so the grid reads through; judge the balance in game.
4. Add `clip_water_shallow` only if the flood should splash and slow players.

### 15.6 Waterfall or wall cascade

1. A sheet: the stock `p7_cai_waterfall_01` model, or your own strip with `lit_backlit_waterfall` (opaque) and a Thickness Map + Backlight Tint so a light behind it glows through.
2. Water running down an existing wall: a coplanar `lit_decal_normal_gloss_reveal` decal with a streak-shaped reveal map and Layer1/Layer2 scrolls (the doc's stated purpose). The wall must be a deferred material.
3. FX: `water/fx_water_fall_sector` at the base, `fx_water_fall_top_mist` at the lip.
4. Optional walk-through feedback: port `mp/_waterfall.csc` into our namespace.
5. FULL build and stop.

### 15.7 Wet sheen floor (the primary dark-map recipe)

1. Floor material: a stock wet material by name (`t7_asphalt_damaged_dark_wet`, `t7_concrete_floor_garage_cracked_wet_nw`, `t7_concrete_bare_dark_01_wet`, `t7_metal_diamond_plate_worn_wet`), or a clone in our own GDT: `lit`, `glossSurfaceType <custom>`, `glossRangeMax 15–17`, `glossRangeMin` 0–16, dark albedo, a real normal map so the reflection breaks up, `reflectionProbeAmount 1`.
2. Give the neon an emissive body the probe can see (sign, strip, lamp head).
3. Add a real light near it for the runtime highlight; if it looks like plastic, lower that light's `spec_comp` ([01](01_lights.md)).
4. Fit a probe to the room, with reflection planes on floor and walls ([06](06_reflections_probes.md)). This step is most of the look.
5. If the room's baked ambient is near-black and the reflections look weak, add a PROBE_ONLY light near the neon or raise the probe's `brightnessAdjust` ([06](06_reflections_probes.md)).
6. Add puddle decals where lights pool (15.1). If dark corners glow unnaturally, use an Occlusion map.

### 15.8 Rain-slick neon streets

1. Do 15.7 on every outdoor floor.
2. Drips and sheets from ledges and awnings: `fx_water_drip_line_*`, `fx_water_sheet_line_100`, `weather/fx_rain_ground_sheeting`, `fx_rain_prop_sheeting`.
3. Optional falling rain: `weather/fx_rain_system_{lite,med}_{1,2}` (real sources). How a rain system follows the player in a usermap is not covered by the docs [TEST].
4. Optional ripples: `volume_outdoor` (tick all four `enabled0..3`, as The Giant does, so the zero-based numbering cannot bite) plus `volume_weathergrime rain 0.5–1`; which materials respond is unknown [TEST].
5. Judge on both a low and a high graphics config ([09](09_design_and_inspiration.md)).

### 15.9 Caustic light on a wall near water

1. Place a `PRIMARY_SPOT` light above or beside the water, aimed at the wall or ceiling that should shimmer.
2. `def cookie_caustics_01` (or `cookie_caustics_layered`, `cookie_caustic_ink`).
3. Start from stock values: `def_tile 2 2`, `def_scroll 0.15 0`, optionally `def_rotation 0.2`, `shadowUpdate Never`, colour matching the water (pale green in Sector, orange in The Giant; cyan or magenta for us).
4. Keep the radius small (stock 78–325) and cull it ([01](01_lights.md)).
5. FULL build; ask the user whether it moves, and how fast.

### 15.10 Underwater look for a pool deep enough to put your head under

1. `pbg_box` whose `size_min`/`size_max` wrap the water volume below the surface; small `blend_mins`/`blend_maxs` so it does not leak above the surface.
2. Tick `USE_UNDERWATER` (65536) and the `LIGHTSTATE_n` flags for **every** state the map runs in (in a usermap that includes Radiant State 2). Set `underwater_mix 1`, `underwater_halfdistance` (default 450; lower = murkier) and `underwater_absorptionRGB` (for neon-green toxic water, absorb red and blue instead of the default red).
3. Optional client script `SetUnderwaterVisionSet( "<vision>" )`; the stock surface postfx already run unless `level.disableWaterSurfaceFX` is true.
4. Drowning is live: players swimming underwater take `MOD_DROWN` damage after `player_swimTime`.
5. FULL build; whether players can swim at all in a zombies usermap is untested.

---

## 16. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Water renders black | Lighting/probes not baked, or no probe covers it | FULL build; make sure a probe box covers the water [COMMUNITY; modme 3557] |
| Water material invisible or odd in Radiant | The editor uses a different render path; community says realtime rendering is needed | Turn on Realtime Rendering; judge in game [VERIFIED techset / COMMUNITY] |
| Players walk through "water" with no splash or slowdown | Look without behaviour | Add a `clip_water(_shallow)` brush, top at the surface [VERIFIED materials] |
| Players cannot enter the water | `clip_water_player` used (solid to players and AI) | Use `clip_water` or `clip_water_shallow` [VERIFIED flags] |
| Invisible water players wade through | Behaviour without look | Add the water surface at the same height |
| Zombies ignore players in water or walk on the pool bottom | AI have no swim behaviour and follow the navmesh | Keep water shallow over navmeshed floor; never design fights that need swimming [VERIFIED absence / COMMUNITY] |
| Neon lights give no highlights on the water | An `_only_sun*` variant or `lit_transparent_water_flow` (non-sun lights compiled out) | Use `lit_water_sim`, `_flow_normal` or `_flow_normal_color` [VERIFIED define; effect INFERRED] |
| Reflections smear or slide with the camera | Probe box far too small (ours are the 144-unit default cube) | Fit probe boxes and reflection planes ([06](06_reflections_probes.md)) |
| Neon reflections weak in a very dark room | Reflection brightness correction damps reflections where baked diffuse light is dark | Emissive fixtures the probe sees; PROBE_ONLY lights or `brightnessAdjust` ([06](06_reflections_probes.md)) [INFERRED] |
| Zombies and moving things never appear in wet floors | Reflections are baked cubemaps; SSR exists only on the water-sim materials | Accept it, or use a water-sim patch with SSR where it matters |
| Puddle decal draws nothing | `_blend` on a face with no vertex alpha, or the base surface is forward-rendered (`lit_emissive*`) | Use `_02` on faces; put decals only on deferred surfaces [INFERRED; TEST] |
| Frame rate drops near water | Transparent water adds overdraw/OIT; `nocull` doubles it | Prefer `lit_water_sim` or opaque wet materials [VERIFIED doc] |
| A water FX added to the zone renders empty | The source is a 5,092-byte placeholder stub | Check the `.efx` size before zoning ([04](04_fx_lights.md)) [COMMUNITY: project rule] |
| Flow looks banded or goes the wrong way | Flow map compressed or wrongly encoded | Import `uncompressed`, `semantic 2d` like stock [VERIFIED import; cause INFERRED] |
| `t7_water_sector_flow` fails to link | Its unused slots name images defined nowhere locally | Clone it and clear those slots, or start from `t7_water_zm_der_vats` [VERIFIED names; link TEST] |
| Footsteps on water kick up dust | Stock footstep/land/jump FX tables map water surfaces to dust | Accept it, or author a custom surface FX table [VERIFIED data] |
| Underwater grade never appears | `USE_UNDERWATER` not set, or the box is not flagged for the running lighting state | Set 65536 and tick `LIGHTSTATE_2` (and any other state used) [VERIFIED def; state gotcha INFERRED] |
| Cookie rotation speed is not what you set | The two sources disagree on `def_rotation` units | Test once and record the true unit [TEST] |
| Weathergrime `wetness`/`puddles` keys do nothing | Legacy keys, not in the current definition | Use `rain`, `windDirection`, `windSpeed` [VERIFIED absence] |
| Deep pool breaks the map | Undercity floor is z −384, sky floor −512; below z −1000 the stock below-world failsafe fires | Keep water shallow and above those levels (docs/158; CLAUDE.md) |

---

## 17. Open questions and tests

None of these has been run. Each needs a FULL build and a user playtest; log evidence under a dev-gated tag (e.g. `[TOD_WATER]`) per CLAUDE.md's diagnostics rule.

1. **Swimming in a zombies usermap.** Is `player_swimming_enabled` on by default, and does a deep `clip_water` pool let players swim with no script? Test: a deep clip pool; dev-log `IsPlayerSwimming()` / `DepthOfPlayerInWater()` once a second while inside.
2. **Clip depth.** How thick must `clip_water_shallow` / `clip_water` be for wading slowdown, and does `clip_water_shallow` ever allow swimming?
3. **Puddles on emissive floors.** Does a `lit_decal_*` puddle layer over a `lit_emissive_advanced` vertigo floor at all?
4. **Only-sun variants.** Does a neon omni light really give no highlight on `lit_water_sim_flow_normal_only_sun`? (A/B two patches under one light.)
5. **Per-state water.** Do puddles and water show different reflections before and after a lighting-state change?
6. **`volume_weathergrime rain`.** Which materials show ripples (stock `_wet`, any `lit`, none)? And which `volume_outdoor` `enabledN` matches which Radiant State?
7. **Rain assets.** Do `t7_decal_raindrops(_fast)` and `rain_hit_n` exist in the game's fastfiles?
8. **`t7_water_sector_flow` by name.** Does it link despite the missing images?
9. **Moving water volume.** Does a clip-water brush inside a moving `script_brushmodel` move its water?
10. **Postfx availability.** Do `pstfx_watertransition`, `pstfx_water_t_out`, `pstfx_waterfall` and the `generic_filter_*` rain materials load in a usermap without zone lines?
11. **Deferred SSR.** Is the deferred SSR compute variant (`USE_DEFERRED_SSR` in `compute/deferred.csdef`) active for opaque glossy floors on PC? [VERIFIED variant exists; use unknown]
12. **Cookies.** Does a caustic cookie project from an omni? Which `def_rotation` unit is right?
13. **Waterfall models.** Do `p7_cai_waterfall_01(_small)` convert and render?
14. **Drowning speed.** What are `player_swimTime`, `player_swimDamage` and `player_swimDamagerInterval` in zombies?
15. **The zombie underwater-jump condition.** Does the compiled zombie behaviour tree use `zombieShouldJumpUnderwaterMelee`?
16. **Water lightmap strings.** The compiler contains `waterlightmapsamplesize`, `waterlightmapsunonly` and "LIGHTING: Constant water light map sample size", suggesting a compile-time water lighting option (perhaps sun-only lighting on water). They appear in no def and no stock map; their role and where they are set are unknown.
17. **Extracam mirror.** Does `lit_extracam_reflection` + `SetExtraCam` work in a zombies usermap, at what cost, and does script index 0 feed material Camera Index 1?

---

## For Tower of Doom II

Recommendations only; nothing here has been changed or tested.

1. **We have no water, and the world already looks wet.** Almost every visible world face uses a vertigo material, and those are `lit_emissive_advanced` with `$white_specular`, gloss up to 15–16, no normal map and `reflectionProbeAmount 1` [VERIFIED] (src: source_data/_emox/emox_mwiii_vertigo_assets.gdt, byte-identical in the shared tools and the private workspace). These are near-mirrors, which is where the "wet-neon reflection" on landings comes from. So the biggest "wet" improvement available is not water at all: it is fitting the 53 reflection probes, which today are the 144-unit default cube, most of them floating 140–150 units above the floor so no box reaches a floor [VERIFIED, see [06](06_reflections_probes.md)], plus giving the `volume_sun` a `target` so its global probe leaves the `mast tier 1` brush it is buried in ([06 — the global probe](06_reflections_probes.md#8-the-global-probe)). Do that before adding any water [INFERRED priority].
2. **Puddle decals will probably not work on our floors.** Deferred decals only layer over deferred surfaces, and our whole world kit is forward-rendered emissive [VERIFIED doc rule and render flags; outcome TEST]. Where a puddle matters, give that patch of floor a deferred wet material (15.7) or float a thin water patch over the emissive floor (15.5).
3. **If real water is wanted, keep it shallow and place it where the fiction fits:** a coolant trough or flooded channel in the Undercity/Vault (floor z −384; sky floor −512; nothing near the z −1000 failsafe), a leaking reservoir in a workshop wing, or a reflecting strip in the plaza. Emit it from `tools/gen_tower_map.js` as a `nonColliding` patch plus, only if players should wade, a `clip_water_shallow` brush over navmeshed floor. Clone `t7_water_zm_der_vats` (not an `_only_sun` variant; our light comes from point lights) into a map-owned `source_data/tod_water.gdt` with blue-black ramps, SSR on, high overwater opacity.
4. **The flooded-grid floor (15.5) is the most "Tower II" water we could make**: dark water whose refraction shows the glowing grid underneath, with SSR catching zombies. It is also the least proven idea here; test it on one landing first.
5. **About Glass Tower's water.** The author's promotional screenshots of GLASS TOWER[HARD] (the map the user admires) show a large water plane carrying the sun's glint and the neon trim [COMMUNITY: screenshots]; how it was built is unknown ([09 — Glass Tower](09_design_and_inspiration.md#4-glass-tower)). Water like that reads because it has something bright to reflect: a sunset sky and emissive trim. In a dark tower the same surface would reflect darkness unless its probe sees bright neon, which is another reason to fit probes first [INFERRED].
6. **Glowing coolant** fits the cyber theme and can join the power beat: `lit_emissive_lava_flow_script` has tint states and script controls [VERIFIED techset]; driving them at power follows the switchable-glow route in [03](03_glow_and_perks.md) and needs a real light beside it for the spill light [INFERRED; TEST].
7. **Caustics are the cheap "water" light:** one spot light with `cookie_caustics_layered` on the wall above a coolant trough, copied from Treyarch's values (15.9). Our generator emits only `PRIMARY_OMNI` lights today, so this needs a spot-light path in `light()` [VERIFIED current generator; see [01](01_lights.md)].
8. **Avoid:** swimming and deep pools (zombies cannot follow), `wave_water` (no stock example, FPS warning), `lit_transparent*` water (overdraw; the user plays with `OIT = "0"`), the `_only_sun*` variants, and zoning the 5,092-byte water FX stubs.
9. **Lighting states.** Any `pbg_box` (underwater or grade) we add must have `LIGHTSTATE_2` ticked, because Radiant State 2 is the state a usermap boots in, or it may do nothing [INFERRED; TEST] ([02](02_power_and_states.md)). For a `volume_outdoor`, whose keys are numbered from 0, tick all four `enabled0..3` as The Giant does.
10. **Process.** Every water change is a FULL build (materials, probes and lights bake in the LED pass). New assets go in map-owned GDTs synced to `C:\BO3Tools\TOD2Cybercity`, never the shared Mod Tools root (docs/154). Build and stop; the user tests; add a dev-gated `[TOD_WATER]` log for any scripted water (depth, swim state, state changes) so a playtest leaves evidence.

---

## Sources

**Official Treyarch documentation and data (MODTOOLS)**
- `docs_modtools/Materials.pdf` — p.1 (Lit covers water; Occlusion map and reflection probe), p.2 (coplanar deferred decals, not over transparent), p.10-11 (transparency and overdraw), p.19 (Lit Decal Normal Gloss Reveal, flowing water), p.20 (oily sheen decals), p.25 (fake flowing water on particles).
- `docs_modtools/PhysicallyBasedRendering.pptx` — slide 5 (256×256 blended probes, gloss 2^17), slide 15 (transparency cost; decals for water on a surface).
- `docs_modtools/Probe/Reflection_Probes.pdf` — p.1-2 (box snapping, reflection planes).
- `docs_modtools/Lighting_Parameters.pdf` — p.8-9 (cookie parameters), p.11 (sun gobo / `ENABLE_COOKIE` note).
- `docs_modtools/SunSky_Light_SetUp.pdf` — per-state lighting and probe bake.
- `docs_modtools/bo3_scriptapifunctions.htm` — water, wave-water, underwater, sheeting, ripple and extracam functions.
- `bin/t7.def.json` — `wave_water`, `wave_generator`, `wave_clamp`, `undertow_volume`, `pbg_box`, `light` cookie keys, `volume_weathergrime`, `volume_outdoor`, `misc_volume_decal`, `dyn_model` splash keys.
- `bin/cod2map64.exe`, `bin/Radiant_modtools.exe` (string extraction) — clip-water names, swim dvars, `r_waveWaterActors`, `waterlightmap*`, "wave_water entity with no brushes".
- `deffiles/material.awi` — SSR, flow and foam fields; water gloss preset 6..17; Water specular 0.149; gloss range default 0..13.
- `share/raw/techsetdefs_stable/` — `geometry/lit_water_sim*.techsetdef`, `lit_transparent_water_flow*.techsetdef`, `water_shore*.techsetdef`, `lit_(transparent_)backlit_waterfall*.techsetdef`; `include/lit_water_sim_base`, `flow_base`, `foam_base`, `lit_water_sim_flow_base`, `water_shore_base`; `decal/lit_decal_normal_gloss_reveal(_flow)`, `lit_decal_raindrops`, `lit_decal_specular_fullspec`; `specialty/lit_emissive_lava_flow(_script)`, `lit_extracam_reflection`; `renderFlags.techsetdef`; `compute/deferred.csdef`.
- `share/assetconvert/preshader/pc/v7/` — precompiled shader counts.
- `texture_assets/t7_water.gdt` — `t7_water_zm_der_vats`, `t7_water_sector_flow`, `t7_water_sector_opacity_40`, `t7_water_variant_opacity_5`.
- `model_export/t7_props_water.gdt` — `mtl_p7_cai_waterfall_01(_small)`, `p7_cai_waterfall_01(_small)` xmodels.
- `art_assets/t6_legacy/texture_assets/clip.gdt` — `clip_water`, `clip_water_shallow`, `clip_water_player`.
- `art_assets/t6_legacy/texture_assets/water.gdt`; `model_export/t7_props/p7_eth_vista_water/p7_eth_vista_water.gdt` — remaining image dependencies of the vats material.
- `texture_assets/t7_{asphalt,brick,concrete,decal_grunge,glass,metal,mud,stone}.gdt` — the 26 stock `_wet` materials, puddle and oil decals.
- `texture_assets/t7_light_gobo.gdt` — caustic cookies.
- `source_data/{surfacefximpacts,surfacefxtables,defaultplayerfootstep,playerfxtables}.gdt`; `deffiles/surfacefxtable.awi` — water surface FX and footsteps.
- `source_data/_emox/emox_mwiii_vertigo_assets.gdt` — our world kit's material fields.
- `map_source/_prefabs/zm/zm_giant/geo/zoneb_vat_1.map:1246-1253` (vat water patch), `geo/zm_giant_hotel.map:14900-15022` (vertex-alpha puddle), `zm_giant_geo.map` (`volume_outdoor`, `volume_weathergrime`), `zm_giant_light.map` and `light/zm_giant_post.map` (caustic lights, pbg_boxes); `map_source/_prefabs/mp/mp_sector/geo/mp_sector_terrain_north.map:7722-7730` (clip_water_shallow), `mp_sector_light.map`, `mp_combine_light.map` (caustic lights), `mp_sector/fx/mp_sector_fx.map` (waterfall FX); `map_source/mp/mp_sector.map` (legacy weathergrime keys).
- `texture_assets/t7_decal_grunge.gdt`, `model_export/t7_props_industrial_small.gdt` — the four stock `lit_decal_normal_gloss_reveal` materials.
- `texture_assets/water/` and `texture_assets/t7_materials/` — the measured ramp, flow and opacity TIFFs.
- `share/raw/scripts/shared/{load_shared.gsc,load_shared.csc,drown.gsc,water_surface.csc,filter_shared.csc,audio_shared.csc,ai/zombie.gsc}`; `share/raw/scripts/zm/{_zm.gsc,_zm.csc,_zm_spawner.gsc,_zm_laststand.gsc,_load.gsc,_zm_audio.gsc}`; `share/raw/scripts/mp/_waterfall.csc`.
- `share/raw/fx/{water,weather,impacts,player,_t6}` — stock water FX and the placeholder stubs.
- Treyarch, "Volumetric Global Illumination at Treyarch" (SIGGRAPH 2016): https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf — reflection brightness correction.

**Community**
- https://wiki.modme.co/wiki/black_ops_3/basics/Setting-up-water.html — three-part water setup; Realtime Rendering note.
- https://forum.modme.co/wiki/threads/298.html — Exofile's recipe; Abnormal202 on zombies running on the pond bottom.
- https://forum.modme.co/wiki/threads/3780.html — wave_water + clip, buoyancy, FPS warning.
- https://forum.modme.co/wiki/threads/3557.html — black water from uncompiled lighting.
- https://forum.modme.co/wiki/threads/2946.html — no true mirrors; use gloss/probe materials.
- https://wiki.zeroy.com/index.php?title=Call_of_duty_bo3:_Rain — rain setup, raindrop decal names.
- https://www.ugx-mods.com/forum/scripting/91/tutorial-rising-water/13844/ — rising water via a moving script_brushmodel.
- https://www.ugx-mods.com/forum/mapping/12/invisible-water-i-want-it-visible-to-players/11066 — water clip is invisible behaviour (World at War).

**This project**
- `tools/gen_tower_map.js` — `probe()` (~line 7321), `light()` (~line 7184), the wet-neon comment (~line 1645), `UC_Z` / `SKY_FLOOR` (line numbers as of 2026-09-24; a peer session edits this file).
- `map_source/zm/zm_tod2_cybercity.map` — 53 reflection probes, 344 lights, no water.
- `source_data/tod_materials.gdt` — the `tod_door_*` / `tod_hall_*` material clones (`lit_emissive_advanced`).
- The GLASS TOWER[HARD] Workshop page, https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290 — author screenshots (see [09](09_design_and_inspiration.md)).
- `docs/104_cybercity_sky.md` §5 (probes bake from the sky, sun and lights), `docs/154_tod2_isolation.md`, `docs/158_tod2_base_layout.md`, `CLAUDE.md` (build rules, navmesh gate, below-world failsafe, diagnostics).
- The user's game config, `steamapps/common/Call of Duty Black Ops III/players/config.ini` (dated 2026-09-23) — `OIT = "0"`, `TextureQualityProbes`, no SSR setting.
- Map One (`abandoned_cyber_city_zombies`): `docs/20_atmosphere_and_materials.md` (wet ground, 15 probes, drip FX); `MODTOOLS/map_source/zm/zm_abandoned_cyber_city.map`.
