# 06 — Reflections, probes and ambient light

**In short.** In Black Ops III one entity, the `reflection_probe`, supplies two things at once: the picture that shiny surfaces reflect, and the soft bounced ("ambient") light that fills everything a lamp does not hit directly. Wherever no local probe covers a spot, both come from one map-wide fallback, the **global probe**, which the `volume_sun` creates at its own centre unless its `target` key moves it. So probes decide how dark a dark map really looks, not only how shiny its floors are. How much of the probe a surface shows is a material setting: gloss range, reflection amount, metal mask and occlusion. Tower of Doom II's 53 probes are the Mod Tools template probe copied everywhere: a 144-unit cube floating above the floor. Four of its spire probes capture from inside or on a solid brush, and its global probe sits inside the mast. As a result, almost every surface, gun and zombie in the map is probably lit and reflected by one buried global probe.

**Read this when:** a shiny floor smears or reflects the wrong thing; a room is brighter or darker than its lights explain; the whole map takes a colour cast; you add or reshape a room; you plan power-on lighting; you want a wet floor, glass or a mirror.

## Contents

1. [What a probe is](#1-what-a-probe-is)
2. [How the engine uses probes at runtime](#2-how-the-engine-uses-probes-at-runtime)
3. [Every reflection_probe key](#3-every-reflection_probe-key)
4. [Shapes: boxes, blends, reflection planes, multiface, subtract, override, virtual](#4-shapes-boxes-blends-reflection-planes-multiface-subtract-override-virtual)
5. [Where to put probes](#5-where-to-put-probes)
6. [Editing and debugging probes in Radiant](#6-editing-and-debugging-probes-in-radiant)
7. [How probes are baked, and lighting states](#7-how-probes-are-baked-and-lighting-states)
8. [The global probe](#8-the-global-probe)
9. [Brightness, darkness and exposure](#9-brightness-darkness-and-exposure)
10. [The material side: how much a surface reflects](#10-the-material-side-how-much-a-surface-reflects)
11. [Screen-space reflections and real mirrors](#11-screen-space-reflections-and-real-mirrors)
12. [Recipes](#12-recipes)
13. [Symptoms, causes, fixes](#13-symptoms-causes-fixes)
14. [Open questions and tests](#14-open-questions-and-tests)
15. [For Tower of Doom II](#for-tower-of-doom-ii)
16. [Sources](#sources)

---

## 1. What a probe is

**Plain version.** A reflection probe is an invisible camera you place in a room. When the lighting is baked, it takes a 360-degree photo of the room from where it stands (a *cubemap*: six square pictures, one per direction). Shiny surfaces inside the probe's box show that photo as their reflection. At the same time, the bake fills the probe's box with a 3D grid of "how much light arrives here from each direction" values. That grid is the bounce light that makes a shadowed corner dark blue instead of pitch black.

A zombies example: Treyarch gave The Giant 176 probes, almost all of them sized to one room or corridor; only 6 keep the default box [VERIFIED count] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map). So a concrete floor in one room reflects that room's own lamps and takes that room's bounce light, and a different probe takes over as you walk through the doorway into the next space.

Treyarch's own words: "Reflection probes, which provide both bounce lighting and reflections, consist of two major parts: The actual reflection cube map. The occlusion and diffuse compensation grid." [VERIFIED] (src: docs_modtools/Probe/Reflection_Probes.pdf p.1)

**Why this matters more in BO3 than in older CoD.** Treyarch's 2016 talk presents its system as an alternative to traditional lightmaps: diffuse bounce is kept in probe-grid volume textures ("ambient cubes", BC6H-compressed) baked from the probes, so the same indirect light also applies to moving objects and effects ("Lightmap Downsides: Doesn't work at all on dynamic geometry"; "Works on all geometry") [VERIFIED as the talk's content] (src: https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf p.2, p.6, p.27, p.70; abstract at https://advances.realtimerendering.com/s2016/index.html). That this is the system that shipped in BO3 rests on an Activision engineer's blog post ("after we shipped Black Ops 3"), which also goes further than the slides ("the only representation of baked irradiance", "all the lighting is unified, regardless of the object type") [COMMUNITY] (src: http://c0de517e.blogspot.com/2016/08/activision-siggraph-2016.html). Treyarch's Mod Tools PBR deck agrees in outline: BO3 has "Global specular lighting in multiple, 256x256, blended reflection probes" and "GI lighting from point cloud diffuse bake", where BO1 had "GI lighting baked into light maps" [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slides 4-5). That players, zombies and your gun take their ambient light from the same probe volumes as the walls is a reading of that talk, not a documented statement [INFERRED]. This project's own notes call the `.led` a "lightmap" and record a "lightmap-atlas" bake crash. That is the project's wording, and whether BO3 world brushes also carry some per-surface baked data is unresolved (src: docs/BO3_MAPMAKING_KB.md).

**What you author:**

| Thing | What it is | Where |
|---|---|---|
| Local probe | a `reflection_probe` entity: one cubemap + one bounce grid for one room-shaped volume | Radiant (in this repo: `tools/gen_tower_map.js` `probe()`) |
| Global probe | created by the `volume_sun`; covers everything no local probe covers | the `volume_sun` entity ([05 §2.4](05_sun_sky_exposure_fog.md#24-the-global-probe-and-target)) |
| Material response | how much of the probe a surface shows, and how sharp: gloss, reflection amount, metal mask | the material asset in APE (a GDT) |

**What a probe changes on screen in a zombies map:**
- the shine on floors, walls, glass and metal props;
- the ambient light in every shadow and dark corner;
- probably the ambient light on your gun, hands and the zombies [INFERRED, see above];
- probably the auto-exposure: the engine API describes `SetExposureInstantSnap` as "snap exposure to base calculated probe value" [VERIFIED text] (src: docs_modtools/bo3_scriptapifunctions.htm), so probes store exposure information the camera uses [INFERRED].

---

## 2. How the engine uses probes at runtime

These mechanics come from Treyarch's SIGGRAPH 2016 talk "Volumetric Global Illumination at Treyarch" unless noted. The talk is an official Treyarch source [VERIFIED as what the talk says]. That retail BO3 runs every formula exactly as on the slides is [INFERRED] from its timing and authorship (src: https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf).

1. **One cubemap, two uses.** The lowest mip of the cubemap is the diffuse irradiance; the higher mips are pre-blurred ("convolved") specular. Rough surfaces read blurrier mips of the same picture (p.10).
2. **The bounce grid.** Each grid point gathers colour by re-projecting from existing probe cubemaps. The talk says 4096 rays per voxel and 15 neighbouring probes considered, with missed rays in-painted (its "In Practice" slide, p.16). The Mod Tools doc says "only the 8 closest probes are used to collect this color data" (src: Reflection_Probes.pdf p.5). Treat the doc's 8 as the mod-tools behaviour [INFERRED].
3. **Storage.** An "Ambient Cube", BC6H-compressed, sampled with hardware trilinear filtering: three volume reads (X, Y, Z), each weighted by the square of that component of the surface normal (p.27-29).
4. **Probe volumes are convex shapes** built from groups of six planes, which can be added or subtracted. Blends are pre-multiplied into the planes. At runtime the engine culls volumes by bounding box, works out each visible volume's attenuation per pixel, samples it, and blends the results between all volumes (p.44-47, p.49).
5. **Override is a two-level priority.** "Override Volumes: Like priority. Only two levels." (p.43; also docs_modtools/Probe/Priority_Probes.pdf p.1).
6. **Parallax correction uses reflection planes** and fades as surfaces get rougher: `reflectionMip = (1-gloss)*numMips`, then the intersection planes are pushed outward by up to 100 units once the mip passes 2.5. So parallax only matters on glossy surfaces (p.63-64).
7. **Reflection brightness correction.** See [§9.1](#91-reflection-brightness-correction): dark bounce light damps reflections (p.65-67).
8. **Cost.** "Less than 2ms for reflections and GI"; "Works on all geometry" (p.69-70).

The stock deferred-lighting compute shader is built in permutations labelled by probe count (`DEFERRED_PERMUTE_DESC_PROBES_PLUS_ONE [0;3]`, "0,1,2,3"); the file's own comment says these `DESC` defines only describe a permutation rather than change what it does [VERIFIED] (src: share/raw/techsetdefs_stable/compute/deferred.csdef). That is consistent with the doc's warning that going from 1 to 2 to 3+ visible probes per pixel switches to "a slower, slightly less efficient shader" [VERIFIED doc text] (src: Priority_Probes.pdf p.1); that the permutations are chosen by per-pixel probe count is [INFERRED].

### 2.1 What lights a moving object (player, zombie, viewmodel, script model, FX)

| Component | Source | Confidence |
|---|---|---|
| Bounce / ambient | the probe grid at that position: a local probe if inside one, else the global probe | talk: one system for all geometry [VERIFIED]; applied to our zombies and viewmodel [INFERRED] |
| Reflections | probe cubemaps, blended, parallax-corrected by that probe's planes | [VERIFIED] talk + PBR deck |
| Direct light | runtime `light` entities (not `PROBE_ONLY`) and the sun | [VERIFIED] (src: bin/t7.def.json light `PROBE_ONLY`: "only be seen by the reflection probes") |
| Particles | "Vertex lighting/shadowing on particles" | [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 5) |

There is no separate "light grid" entity to author. `lightgrid_sky` still exists in the entity definitions, but no stock map source uses it, nor `volume_reflection`, `build_probe` or `volume_sun_extension` [VERIFIED absence in MODTOOLS/map_source]. When someone says "the light grid" for BO3, the real thing is the global probe's grid: `volume_sun` `grid_density`, "number of probe points in each dimension" [VERIFIED] (src: bin/t7.def.json).

docs/107 recorded the gun, the hands and the zombies taking the same yellow cast as the walls. That fits the global probe lighting everything, but it is [INFERRED], not tested.

### 2.2 What a probe can never show

A cubemap is a photo taken at bake time. Anything that is not in the bake is not in the reflection [INFERRED from how capture works]:
- zombies, players, weapons, moving script models and FX;
- a light turned on later by script or an exploder (lighting-state lights are different, see [§7.3](#73-probes-and-lighting-states));
- an emissive model swapped to its `_on` twin at power-on;
- `script_model` entities in general: their `static` key defaults to **false**, "Include in the baked shadows and probes", so a script model is left out of probe bakes unless you set it [VERIFIED] (src: bin/t7.def.json script_model; misc_model's `static` defaults to true).

Among the materials you can author, only water materials with screen-space reflection switched on can reflect moving things ([§11](#11-screen-space-reflections-and-real-mirrors)).

---

## 3. Every reflection_probe key

The authority is Radiant's entity definition, `bin/t7.def.json`, class `reflection_probe`: "Capture a cube map from origin and apply to contents of volume with calculated occlusion." [VERIFIED]. Types, ranges, defaults, groups and quoted meanings below are the def's [VERIFIED def]. The "Giant usage" column counts the 176 probes in `map_source/_prefabs/zm/zm_giant/zm_giant_light.map` [VERIFIED counts]. Where a key's name was also searched for in `bin/cod2map64.exe` and `bin/Radiant_modtools.exe`, the text says so; a name found in a binary shows only that a tool mentions it [INFERRED use].

| Key | Type / range | Default | Def group | Meaning (def text, or plain) | Giant usage |
|---|---|---|---|---|---|
| `origin` | vec3 | 0 0 0 | 3_SHAPE | where the cubemap is captured. "the probe location doesn't even need to be within the box" (Reflection_Probes.pdf p.1) | per probe |
| `angles` | vec3 | 0 0 0 | 3_SHAPE | rotates the box to fit an off-grid room | 6 / 176 |
| `size_min` | vec3, ±32000, step 4 | **72 72 72** | 3_SHAPE | "area of effect on the negative side". A HALF-extent: distance from origin toward −X/−Y/−Z, written as positive numbers (its Radiant manipulator is `-halfbox.xyz`) | fitted per room |
| `size_max` | vec3, ±32000, step 4 | **72 72 72** | 3_SHAPE | "area of effect on the positive side". Half-extent toward +X/+Y/+Z (manipulator `halfbox.xyz`) | fitted per room |
| `blend_mins` / `blend_maxs` | vec3, min 1 | 3 3 3 | 3_SHAPE | "Distance to blend out" on each side | mostly `3 3 3` or `4 4 4`; per-axis values from 1 to 10 (e.g. `5 5 10`, `10 10 10`) |
| `resolution` | 0.125x … 8x | **4x** | 2_DIFFUSE_GI | "relative number of probe points in each dimension" of the bounce grid | 4x on 170, 2x on 3, 1x on 3 |
| `grid_density` | 4 … 64, hidden | 0 | — | the older grid-resolution key, now hidden; superseded by `resolution` | always `0` |
| `override` | bool | false | 2_DIFFUSE_GI | "Override other overlapping probes that are not marked override." | 14 |
| `subtract` | bool | false | 2_DIFFUSE_GI | "Removes from the probe attenuation shape instead of adding to it. Ignored on the parent probe." | 2 |
| `virtual` | bool | false | 2_DIFFUSE_GI | "Probe doesn't export, but it does contribute to light bake data for other probes." | 17 |
| `box` | bool | true | 2_DIFFUSE_GI | "Probe is represented as a box instead of arbitrary planes." False = multiface | `box 0` on 10; 12 probes carry multiface face keys (2 of them with `box 1`), up to 18 faces |
| `ao_range` | 1–64 | 8 | 2_DIFFUSE_GI | "Ambient occlusion range (in voxels)" | 16 on 168 |
| `ao_strength` | 0–1 | 1 | 2_DIFFUSE_GI | "(0 to disable AO)" | 1 |
| `ao_strength_double_sided` | 0–1 | 0.2 | 2_DIFFUSE_GI | AO for double-sided materials such as foliage | 1 |
| `ao_power` | 0.25–8 | 1 | 2_DIFFUSE_GI | "Ambient occlusion power (gamma)" | 1 on 173 |
| `evcomp` | −5 … 5 | 0 | 2_DIFFUSE_GI | "EV compensation to final probe exposure" | −5 on 5, +0.5 on 1 |
| `brightnessAdjust` | −5 … 5 | 0 | 2_DIFFUSE_GI | "scale the brightness of the bounce during bake" (units undocumented) | unused (mp_sector: 31 probes at 0.5–3) |
| `inpaint_occluded_rays` | bool | true | 2_DIFFUSE_GI | "Inpaint rays that are occluded from any probe." | 1 |
| `smooth_post_process` | bool | false | 2_DIFFUSE_GI | "This probe will smooth with its neighbors at the end of baking." | — |
| `adaptive_quality_boost` | Off/Low/Medium/High | Off | 2_DIFFUSE_GI | slower bake; "uses more samples where it thinks it will enhance quality" | Off |
| `adapt_better` | bool | false | 2_DIFFUSE_GI | "Use the new, better method of adaptive quality boosting." | — |
| `volumetric` | bool | false | 2_DIFFUSE_GI | "Use probe in volumetric fog." | — |
| `targetPlane0` … `targetPlane5` | vec4 | 0 0 0 0 | 5_REFLECTIONS | the six reflection planes, colour-coded Red, Green, Blue, Yellow, Purple, Cyan | 102 / 176 set them |
| `high_detail` | bool | true | 4_MISC | "high-detail lighting that's part of a sun volume" | 1 |
| `low_detail` | bool | false | 4_MISC | "low-detail lighting that's part of a vista volume" | — |
| `in_play_space` | bool | true | 4_MISC | "Probe is in play space and should boost sun shadow quality. This is unavailable if all sides are larger than 1000" | 173 true |
| `scriptable` | bool (spawnflag 8) | false | 4_MISC | "Makes a probe show up as an entity to script" | — |
| `client_server` | ClientSide / ServerSide (0 / 32) | ClientSide | 4_MISC | which VM sees a scriptable probe | ClientSide |
| `debug_render_index_x/y/z` | int 0–64, noExport | 64 / 0 / 0 | 4_MISC | grid point whose bake rays are stored for debugging | — |
| `debug_render_phase` | 0–32, noExport | 0 | 4_MISC | "up to 2 for Low quality, 8 for Medium, and 32 for High" | — |
| `debugColor` | color | 1 1 1 | 4_MISC | colour in the probe-blend debug view | mostly 1 1 1 |
| `target` / `targetname` | string | — | 1_NAMING / 4_MISC | def: "any assoicated reflection_volume". In stock data a child probe targets its parent ([§4.5](#45-parents-children-and-subtract)) | 23 links |
| `name` | string | probe | 1_NAMING | a label | probe |
| `placement_offset` | float, hidden | 72 | — | probably the auto-placement height above the floor [INFERRED] | 72 |

**Multiface keys not in the def.** `facePlane<N>` / `faceBlend<N>` hold the faces of a multiface probe, up to 24; both `cod2map64.exe` and `Radiant_modtools.exe` contain the format string `facePlane%d` [VERIFIED string]. You never type them: Radiant writes them when you Alt-click faces ([§4.4](#44-multiface-probes)).

**Keys found on probes that no tool defines** [INFERRED dead]:
- `radius`: a *light* key. It is not a `reflection_probe` key in the def, and none of The Giant's 176 probes has it. It rides along in the Mod Tools template probe (`rex/templates/ZM Mod Level/map_source/zm/template.map`). **The influence volume is `size_min`/`size_max`, never `radius`.** A missing def entry does not prove a key is ignored, so this stays [INFERRED].
- `exploderFade`: in the template and in 161 of The Giant's probes, but in no def entry and no tool binary string [VERIFIED absence; meaning INFERRED].
- `occlusion_threshold` (17 probes in each of the mp_sector and mp_combine light prefabs, 4 of The Giant's) and `grid_dimensions` (26 in each MP prefab): present in stock data, absent from the def [VERIFIED counts; probably legacy, INFERRED].
- `note_evcomp`: six Giant probes carry `"note_evcomp" "not_0"`: one beside `evcomp 0.5`, three beside `evcomp -5`, two with no `evcomp`. It looks like a lighter's reminder, not a key [INFERRED].

**Exploder membership on a probe.** Two stock MP light prefabs put one probe each into an exploder (`exploder_index_0 … name=exploder_mp_endgame_lights`) [VERIFIED] (src: map_source/_prefabs/mp/mp_sector/mp_sector_light.map, mp_combine/mp_combine_light.map). What exploder membership does to a probe at runtime is undocumented [INFERRED/TEST].

**`grid_density` versus `resolution`.** The older Reflection_Probes doc still describes `grid_density` as the grid's maximum resolution along the longest side, with shorter sides rounding to the closest power of two (p.5). The current def hides `grid_density` (default `0`) and exposes `resolution`. Every Giant probe uses `grid_density 0` plus an explicit `resolution` [VERIFIED]. Whether a non-zero `grid_density` (ours is 16) is still honoured is unknown [TEST]. How `resolution` maps to voxel spacing in world units is also undocumented [TEST].

### 3.1 Keys on other entities that change what probes see

| Entity / key | Default | Def text | Use |
|---|---|---|---|
| `light` `PROBE_ONLY` | false | "If enabled this light will only be seen by the reflection probes" | extra bounce and reflection highlights with no runtime light cost. The Giant: 149 of 543 lights [VERIFIED count]. See [01 §10](01_lights.md#10-bounce-bake_intensity_scale-and-probe_only) |
| `light` `bake_intensity_scale` | 1 | "Adjusts the brightness of a light for GI baking." | bounce strength of one light; whether it also changes the direct light is [TEST] (see [01](01_lights.md#10-bounce-bake_intensity_scale-and-probe_only)) |
| `light` `spec_comp` | 0 | "Specular boost (in stops)." | the light's own highlight on glossy surfaces ([§10.4](#104-the-lights-own-highlight-spec_comp)) |
| `misc_model` `static` | **true** | "Include in the baked shadows and probes." | static props are in the probes by default |
| `script_model` / `script_brushmodel` `static` | **false** | same | script entities are NOT in probe bakes unless set |
| `probes_only` (misc_model, script_model, script_brushmodel) | false | "Only export in probes." | invisible in game, seen by the bake: bounce cards and blockers. The Giant has a `core_50_grey` script_brushmodel with `probes_only 1`, `static 1` (src: zm_giant_light.map entity 685) [VERIFIED] |
| `dont_reflect` | false | "Don't include in reflections, though it may still contribute to GI." | hide an object from reflections |
| `dynamic_probes_only` | false | "Include in dynamic probes." | for moving probes; semantics undocumented [INFERRED] |

(src: bin/t7.def.json) [VERIFIED def text]

**Legacy classes** in the def that no stock map uses: `build_probe` ("Build-only version of reflection probe"), `volume_reflection` (targets a probe, `featherdist`), `lightgrid_sky` [VERIFIED def; VERIFIED absence in stock map_source]. Do not build on them.

---

## 4. Shapes: boxes, blends, reflection planes, multiface, subtract, override, virtual

**Two separate things.** The **box** (`size_min`/`size_max`, or multiface faces) decides *which pixels* use this probe, and so where its bounce light and reflections apply. The **reflection planes** (`targetPlane0..5`) tell the shader *where the walls are*, so the reflection lines up with the room. A probe can have a perfect box and no planes (reflections slide as you walk), or planes and a tiny box (almost nothing uses it) [VERIFIED distinction] (src: Reflection_Probes.pdf p.1-2; t7.def.json groups 3_SHAPE and 5_REFLECTIONS).

### 4.1 The box: half-extents

`size_min` and `size_max` are distances from the origin, one per side. The default `72 72 72` / `72 72 72` is a **144 × 144 × 144 cube** centred on the origin, not a 72-unit cube [VERIFIED def: "area of effect on the negative/positive side", Radiant manipulator `halfbox`; the doc: "The probe size is adjusted by the size_max (x,y,z) and size_min (-x,-y,-z)"]. "Probes can be asymmetrical, and the probe location doesn't even need to be within the box." [VERIFIED] (src: Reflection_Probes.pdf p.1)

**Worked example: fitting TOD II's Vault.** The Vault's interior is x −2592…−1952, y −1028…−468, floor top z −384, ceiling underside z −192 (src: `tools/gen_tower_map.js` `VT_X1/VT_X2/VT_Y1/VT_Y2`, `UC_Z`, `UC_TOP`). Capture 72 above the floor at the room centre:

| Key | Value | Why |
|---|---|---|
| `origin` | `-2272 -748 -312` | room centre, floor + 72 |
| `size_min` | `320 280 72` | −2272 − (−2592) = 320; −748 − (−1028) = 280; −312 − (−384) = 72 |
| `size_max` | `320 280 120` | −1952 − (−2272) = 320; −468 − (−748) = 280; −192 − (−312) = 120 |

Today's Vault probe is `origin -2272 -748 -244` with the default 72s, so its box spans x −2344…−2200, y −820…−676, z −316…−172: it covers a 144-unit square in the middle of a 640 × 560 room, starts 68 units above the floor, and its top passes 20 units beyond the ceiling's underside, through the whole 16-unit ceiling slab (src: map_source/zm/zm_tod2_cybercity.map) [VERIFIED arithmetic].

### 4.2 Blends and who wins an overlap

"Probes fade from fully blended in to fully blended out between the inner and outer box." The inner box is the size box; `blend_mins`/`blend_maxs` extend it outward to the outer box [VERIFIED] (src: Reflection_Probes.pdf p.3-4; Probe_Editing_Handles.pdf: handles set the inner box, Ctrl+Shift sets the outer box). Stock blends are small: most Giant probes use `3 3 3` or `4 4 4`, and per-axis values run from 1 to 10 [VERIFIED counts].

When probes overlap: "probes that have a higher grid_density, are smaller, or are less occluded will blend over other overlapping probes." [VERIFIED] (src: Reflection_Probes.pdf p.4). Use `override` when you need a hard winner ([§4.6](#46-override)).

**Practice** [INFERRED, matching the COMMUNITY advice below]: fit neighbouring inner boxes so they meet at the doorway plane, and let their blend regions overlap across it. Then no pixel falls back to the global probe in the doorway. A mapper reports that inner boxes should not overlap and that capture points should not sit inside another probe's box [COMMUNITY] (src: VerK0 Part 4, https://www.youtube.com/watch?v=HOa08arAXlk; modme 403). The modme thread 3307 fix for "outside a reflection probe the whole lighting becomes super bright" was, first, adjacent probes that touch, "so you never really go outside a probe" [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3307.html).

### 4.3 Reflection planes

"Reflection planes tell the probe where the walls are, so reflections will parallax correctly. There are only six planes, so it is necessary to choose the six most important walls around the probe." "Planes will snap with an inset of 2 units to place them right in front of walls." [VERIFIED] (src: Reflection_Probes.pdf p.2)

**Plain version.** Without planes, the reflection is drawn as if the room were infinitely far away. A floor then reflects a lamp that slides around as you walk, and a wall's reflection looks painted on. With planes, the shader knows the room's real walls and bends the lookup so the reflected lamp stays over the real lamp. Planes matter most on mirror-like surfaces, and the correction fades out on rough ones ([§2](#2-how-the-engine-uses-probes-at-runtime) item 6).

**Format** [INFERRED convention, derived from stock data]. Each `targetPlaneN` is `nx ny nz d`, the plane **n · p = d** in map (world) coordinates, with the normal pointing **into the room**, towards the probe. Worked example, The Giant probe entity 15 (prefab placed at −1048 −696 −1103 in `zm_giant.map`; its world box is x −885…−385, y −1481…−1029, z 199…431) [VERIFIED values]:

| Key | Value | Plane |
|---|---|---|
| `targetPlane0` | `0 0 1 201` | floor at z = 201, facing up |
| `targetPlane1` | `1 4.37e-08 0 -882` | west wall at x = −882, facing +x |
| `targetPlane2` | `-4.37e-08 1 0 -1478` | south wall at y = −1478, facing +y |
| `targetPlane3` | `-1 -4.37e-08 0 390` | east wall at x = −390, facing −x |
| `targetPlane4` | `0.0016 3.3e-07 -0.99999 -335.8` | ceiling at z ≈ 336, facing down |
| `targetPlane5` | `5.6e-08 -1 0 1034.37` | north wall at y ≈ −1034, facing −y |

(src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map entity 15; map_source/zm/zm_giant.map, `misc_prefab` origin `-1048 -696 -1103`). The planes are written in world coordinates even though the probe lives in a prefab: the floor plane (z 201) sits 2.4 units above the box bottom (z 198.6), and the wall planes sit 3–5 units inside the box faces [VERIFIED arithmetic]. A plane does not have to match the box: this probe's ceiling plane (z ≈ 336) is about 95 units below its box top (z 431). The small offsets fit the doc's 2-unit inset from the clicked wall [INFERRED]. Confirm the convention before generating planes: open one generated probe in Radiant, press **W** on a copy, and compare the numbers Radiant writes [TEST].

**For the TOD II Vault example**, the same convention gives: floor `0 0 1 -382`, ceiling `0 0 -1 194`, west `1 0 0 -2590`, east `-1 0 0 1954`, south `0 1 0 -1026`, north `0 -1 0 470` [INFERRED from the convention]. In an open-top room (plaza, lounges, wings) leave the ceiling plane out: there is no wall there to correct against [INFERRED].

### 4.4 Multiface probes

Set `box` to false and the probe becomes a convex shape of up to 24 planes, added by Alt-clicking surfaces that face *into* the probe [VERIFIED] (src: docs_modtools/Probe/Multiface_Probes.pdf p.1). Clicking a surface that faces away "will add a face that hides all the other faces". "Under the hood, in the shader, the probe is still split up into multiples of 6 faces, so a full 24-face probe is roughly equivalent in performance to a box-shaped parent with 3 box-shaped children." "make sure your probe is aligned to the room before creating the faces" [VERIFIED]. Use it for L-shaped rooms, angled walls and ramps. The Giant has 10 probes with `box 0` and 12 that carry `facePlane` keys (up to 18 faces) [VERIFIED count]. Radiant's own doc example went "from two probes with 7 multi-boxes each, to a single probe with 18 faces" [VERIFIED].

### 4.5 Parents, children and subtract

A probe can have child boxes that extend its shape (a "multibox"), or cut holes in it. In The Giant, 23 probes are linked, and the **child carries `target` = the parent's `targetname`** [INFERRED direction from the stock data, well supported: both of The Giant's `subtract` probes, which the doc says only work on a child, are among the 23 that carry `target`] (src: zm_giant_light.map).

**Subtract.** "When the 'subtract' KVP on reflection probes is set on a child probe, the shape of the child will be subtracted from the area that the parent effects. This overrides and cancels out all other multiboxes that it overlaps. The subtract KVP will not function if it is set on the parent probe." Subtract shapes may be open-ended; "you pay for the first six planes, performance-wise, all in one go" [VERIFIED] (src: docs_modtools/Probe/Subtract_Probes.pdf p.1). Use it to cut a solid column or a neighbouring room out of a big box.

### 4.6 Override

"Any probe marked as 'override' will completely replace any probe it overlaps with that is not marked 'override' instead of blending with it." It is "essential for allowing dynamic probes to move through the space already lit by other probes" and can add local "detail" probes. It is not free: the probes underneath still push the shader to a slower variant, so "it shouldn't become common practice to use override probes on every surface" [VERIFIED] (src: Priority_Probes.pdf p.1). The Giant uses 14 [VERIFIED count].

### 4.7 Virtual probes

"Probes can be flagged as 'virtual' and will appear with a red surface. These probes will contribute visibility data to other probes during baking, but do not have an accompanying volume and do not apply reflections to the scene themselves. For this reason they do not take up a probe slot in game, either." [VERIFIED] (src: Reflection_Probes.pdf p.5). They exist because a bounce-grid point is only lit well if "at least one nearby probe" can see it ([§5](#5-where-to-put-probes)). The Giant uses 17, mp_sector 81 [VERIFIED counts].

---

## 5. Where to put probes

### 5.1 Treyarch's rules

- "it is important to have almost every surface in your level covered with some sort of probe. The global probe is intended as a catch-all … The global probe doesn't quite look as good as the local probes so we try to avoid using it at close distances unless you're in a very non-shiny environment, like an open field." [VERIFIED] (src: docs_modtools/Lighting_Probe_Workflow.pdf p.1)
- "it is important that all areas where accurate lighting are required are visible to the center point of at least one nearby probe. Also, only the 8 closest probes are used to collect this color data, so if too many probes are provided, Radiant may give up looking before finding a probe with decent visibility." [VERIFIED] (src: Reflection_Probes.pdf p.5)
- MP defaults: "All Probes are set to a resolution of 4x … Ambient Occlusion settings worked in most cases at Power=1, Range=8 and strength=1 … A very broad global ambient occlusion has proven to be a problem for visibility." [VERIFIED] (src: docs_modtools/Multiplayer_Lighting_Workflow.pdf p.2-3)

### 5.2 What Treyarch actually built

Non-virtual probes; box size = `size_min + size_max` per axis [VERIFIED counts; medians from our analysis of the stock files]:

| Map | Probes (non-virtual) | Median box x / y / z | Capture height above box bottom (median, p25–p75) | Typical blend |
|---|---|---|---|---|
| zm_giant (Treyarch) | 176 (159) | 239 / 285 / 226 | 90 (72–133) | 3–4 |
| mp_sector (Treyarch) | 245 (164) | 289 / 323 / 161 | 75 (60–112) | 3–4 |
| zm_alien_isolation (community, dark) | 23 | 434 / 460 / 160 | 61 (50–86) | 3 |
| zm_tod2_cybercity (ours) | 53 (53) | 144 / 144 / 144 | 72 (always the centre); the box bottom starts 16–152 above the floor below it (5,272 for `probe crown upper`) | 3 |

Only 6 of The Giant's 176 probes keep the default 72/72/72 box [VERIFIED]. So Treyarch builds **many room-sized probes, captured roughly 72–90 units above the floor** (src: zm_giant_light.map; mp_sector_light.map; https://github.com/MattFiler/zm_alien_isolation).

### 5.3 A placement method [INFERRED from the rules above]

1. **One probe per enclosed room or distinct space.** Fit the box to the inside faces of the walls, the floor and the ceiling.
2. **Capture point** near the room's visual centre, about 64–90 units above the floor, with a clear view of every surface the box covers. It must not be inside a brush or a prop.
3. **Reflection planes** on the real floor and the up-to-five most important walls. Drop the ceiling plane in open-top rooms.
4. **Doorways:** inner boxes meet at the doorway; blends overlap across it.
5. **Rooms one box cannot fit** (L-shapes, a ring around a solid column): use multiface, a parent with children, or a subtract child for the hole.
6. **Hidden corners:** where one capture point cannot see everything (behind a column, around a solid core), add **virtual** probes so the bounce grid has a probe that can see those voxels. They cost no runtime slot.
7. **Huge exterior surfaces** (a crown seen from the road, a skyscraper face): a box larger than 1000 on every side cannot use `in_play_space` (def). Consider leaving far exterior surfaces to the global probe, which is its documented job for "a very non-shiny environment, like an open field".
8. **The global probe** goes in open air at an average spot ([§8](#8-the-global-probe)).

### 5.4 Budget

| Item | Fact | Confidence |
|---|---|---|
| Cubemap size | 256 × 256 ("multiple, 256x256, blended reflection probes"); that the figure is per cube face is [INFERRED] | [VERIFIED] (src: PhysicallyBasedRendering.pptx slide 5) |
| Probe count limit | the dvar text "update only one probe, 1-254" (`r_updateSingleDynamicProbe`) hints at an 8-bit index, about 254 exported probes; virtual probes take no slot | string [VERIFIED] (src: bin/cod2map64.exe); limit [INFERRED]; virtual rule [VERIFIED] |
| Blend slots | Radiant error "Ran out of room for probe blends in the shader! Bump the limit: GFX_MAX_CODE_PROBE_BLENDS." The limit's value is unknown | [VERIFIED string] |
| Shader cost | rises at 2 and at 3+ probes overlapping a pixel; override probes still count; multiface costs per 6 planes | [VERIFIED] (src: Priority_Probes.pdf; Multiface_Probes.pdf; deferred.csdef) |
| Grid memory | the global grid "does not affect performance but it does eat more memory as you increase density" | [VERIFIED] (src: Lighting_Probe_Workflow.pdf p.3) |
| Player setting | `players/config.ini` `TextureQualityProbes`: "Number of mips to drop on reflections" (0–16). The user's is 0 (full) | [VERIFIED] |
| Pack growth | the linker appends each full build's probe sets to the `.xpak`; `-CleanPak` on publish | project record (CLAUDE.md, docs/86) |

---

## 6. Editing and debugging probes in Radiant

### 6.1 Fitting controls

| Action | How | Source |
|---|---|---|
| Snap the box to a surface | select only the probe, **Alt + left-click** each wall, the floor and the ceiling | Reflection_Probes.pdf p.1 [VERIFIED] |
| Snap a reflection plane | **Alt + right-click** the surface | p.1-2 [VERIFIED] |
| Snap to other probes | View → *Show Unselected Probe Boxes* (bind it to a key; toggle it on only as needed) | p.1; Probe_Editing_Handles.pdf [VERIFIED] |
| Auto-fit box and planes | **W** ("Auto Target"): box or multiface; asks for a face count for multiface | Reflection_Probes.pdf p.2; Bouncy_Betty_Probes.pdf [VERIFIED] |
| Drop a self-fitting probe | bind **Create Auto Probe**, hover over a floor or ceiling, press it: the probe "will jump up from the floor or down from the ceiling, but then it will orient and expand to fill the space", and sets reflection planes | Bouncy_Betty_Probes.pdf p.1 [VERIFIED] |
| Move the capture point without the box | **Ctrl + Shift** + drag the move handle (3D) or drag inside the box (2D) | Probe_Editing_Handles.pdf [VERIFIED] |
| Edit the outer (blend) box | **Ctrl + Shift** + drag the size handles | Probe_Editing_Handles.pdf [VERIFIED] |
| Nudge a plane | select the W component of the plane key and scroll the mouse wheel | Reflection_Probes.pdf p.3 [VERIFIED] |
| Rotate to match a surface | **Shift + Alt + R** over the surface | p.4 [VERIFIED] |
| Edit / rotate multiface faces | Ctrl-drag a face; in rotate mode (R), Ctrl-drag pivots it; Ctrl + Alt + right-drag edits a face's blend | Multiface_Probes.pdf [VERIFIED] |
| Find probes whose walls moved | View → Debug → Reflection Probes → *Check Probe Geometry Changes* (a red line points at the stale click); *Approve Selected Probe Changes*; *Generate Probe Geometry Data* | Probe_Geometry_Change_Tracking.pdf [VERIFIED] |

The docs' example GIFs are in `docs_modtools/probe_gifs/` (probeBlends, probe_nonBox, probe_snap, probe_snap_angles, probe_snap_planes). Geometry-change tracking only remembers Alt-click points, and "will only catch changes where the geometry that was clicked on has been moved or removed. That means if something else has been put in front of it … it won't catch the changes." So a generated probe has nothing to track until *Generate Probe Geometry Data* is run, and a new wall built through a probe's capture point is not what it looks for [VERIFIED doc text; INFERRED for generated maps] (src: Probe_Geometry_Change_Tracking.pdf). One community tutorial uses Ctrl-click to fit instead; the official binding is Alt [COMMUNITY vs VERIFIED].

### 6.2 Debug views

Radiant's render-flag strings (menu location not verified) [VERIFIED strings in bin/Radiant_modtools.exe]:

| Flag | Tooltip |
|---|---|
| Show Probe Blends | "Display the generated probe blending field." |
| Specular GI Only | "Ignore the probe volume data and only use cube maps." |
| Diffuse GI Only | "Ignore probe cube maps and only use volumetric data." |
| Hide Local Probes | "Disables local probe lighting, leaving only the global probe." |
| Hide Global Probe | — |
| Disable Artist GI Controls | "Disables evcmp on probes, and probe-only lights and geometry. Lighting has to be built to see results." |
| Debug Voxel Visibility | "Sets irradiance voxels to white if visible from a probe, and red otherwise." |
| Disable AO Baking | "Disables the Ambient Occlusion from baking into the Probe Grid." |
| Hide Direct Lighting | "Disables direct lighting, leaving only bounce lighting." |
| Show Lighting Only | "Rendering lighting with no diffuse textures." |
| GI - Pause Each Bounce | "Pauses the lighting after every probe bounce" |

"Disable Artist GI Controls" names the set of hand-tuning tools: probe `evcomp`, PROBE_ONLY lights and probes-only geometry [VERIFIED string].

**Ray debugging.** Set `debug_render_index_x/y/z` to a valid grid point, build lighting, scroll the mouse wheel through the grid points: red rays are occluded, yellow visible. "Once done it is a good idea to set 'debug_render_index_x' back to zero because if debug rays are stored for all the probes in a level Radiant might run out of memory." [VERIFIED] (src: Reflection_Probes.pdf p.5). The doc contradicts itself here: 0,0,0 is a valid coordinate, and the def default is 64 (out of range). Use 64 to switch it off [INFERRED].

**A chrome sphere.** Treyarch's own way to judge a probe is a chrome ball next to it: The Giant has a `test_sphere_silver` beside its global-probe `info_null` [VERIFIED] (src: Lighting_Probe_Workflow.pdf p.1; zm_giant_light.map).

**In game.** The Priority_Probes doc shows "Active Probes Per Pixel" and "Visible Probes Per Pixel" overlays, but the dvars that enable them were not found [VERIFIED images; dvar names unknown]. The script API has two server functions useful for a dev log: `GetReflectionLocs()` ("Gets array of the locations of all of the reflection_probes in the level") and `GetReflectionOrigin( pos )` ("Given a position, returns the position of the reflection probe in use there") [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm). What `GetReflectionOrigin` returns where only the global probe applies is untested [TEST]. Recipe in [§12.9](#129-log-which-probe-a-player-stands-in).

---

## 7. How probes are baked, and lighting states

### 7.1 The bake step

**Probes are baked by Radiant's lighting export, the `.led` (LED), not by `cod2map` or the linker** [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf p.13-16; Generate_LED.pdf).
- GUI: File → Lighting Export. The dialog offers a quality level and *Force Clean Rebuild* ("deletes the LED and creates a new one from scratch"); the doc adds that if you only need updated lights or an exploder and "know you don't need to update the reflection probes", *Export Local Probes* saves time [VERIFIED] (src: SunSky_Light_SetUp.pdf p.13-16). Radiant's binary also holds the option names *Export Local Probes*, *Force Clean Rebuild*, *Recompute Cached Lighting*, *Export Build Lighting* and *Run Export In Backgrond* (sic) [VERIFIED strings]. The lightning-bolt button bakes; "Left Click and hold on the Lighting Bolt Icon" bakes only certain aspects [VERIFIED doc]; the binary holds *Rebuild Sun*, *Rebuild Probes* and *Rebuild All*, probably that menu [VERIFIED strings; menu INFERRED].
- This repo runs it headless: `Radiant_modtools.exe -ledSilent +medium +forceclean +recompute <map>` (src: tools/build_map.ps1, the LED step). The KB's older command line adds `+localprobes`, a word not found among the Radiant binary's command-line strings, so it is probably ignored [INFERRED] (src: docs/BO3_MAPMAKING_KB.md; strings of bin/Radiant_modtools.exe). Local probes do export from our CLI bakes: docs/107 records 24.5–29.3 MB of probe data in the pack.
- Bake phases shown by Radiant include `PROCESSING SUN SHADOWS`, `PROCESSING PROBES`, `SMOOTHING PROBES`, `FINAL REFLECTION RENDER`; a stale map shows `%d of %d probes need raytracing` or `UNBUILT LIGHTING - Hit lightning bolt to update` [VERIFIED strings].

**What needs a re-bake:** any geometry, light, probe or `volume_sun` change; the SSI's pitch, yaw and the sky material's `skyStops` ("to see the effect of the bounced (GI) light you need to rebake") [VERIFIED] (src: SunSky_Light_SetUp.pdf p.15); and any material change that alters what the probes see [INFERRED]. **In this repo every such change is a FULL build**: `build_map.ps1` has no LED-only mode, and `-GscOnly` skips both `cod2map64` and the LED (project rule, CLAUDE.md). A `-GscOnly` build keeps the old probes.

**Bounces.** The SSI field `bounceCount` ("Controls the number of light bounces", default 4, range 1–10) sets how many bounces the bake computes [VERIFIED] (src: deffiles/ssi.awi:40). The talk describes bounces as re-rendering the probes ("Re-render to get bounces", p.23) [VERIFIED talk]. Our `tod_ssi_cybercity` uses 4. One community tutorial advises never below 4 and not above about 6 [COMMUNITY] (src: VerK0 Part 4).

**Fog is baked into probes.** The fog asset carries `probebakeworldfogdensityscaler` and `probebakelitfogdensityscaler` ("Scaler to adjust density of world fog in probe bakes", default 1.0, range 0–1, so they can only thin the fog in the bake), and lit fog has `probecontributionscaler` ("Probe Light Scatter Intensity", 0–50) [VERIFIED] (src: deffiles/fog.awi:18-19, :85). Our worldspawn names `fsi zm_factory_volumetric` while the tower turns fog off in script, so the probes may carry a fog tint the playable scene does not show [INFERRED] ([05 §6.5](05_sun_sky_exposure_fog.md#65-fog-is-in-the-bake)).

**Bake errors worth knowing.** Radiant can print `Probe at %.2f %.2f %.2f out of range. Color %.2f %.2f %.2f exposure …` [VERIFIED string]. A modme thread shows it with astronomically large colours, in areas that also had light bleeding through brushes [COMMUNITY] (src: https://forum.modme.co/wiki/threads/290.html). Treat it as "this probe sees something broken", often light leaking through a gap [INFERRED].

### 7.2 Probes are not per-entity switchable

`reflection_probe` has **no** `lightingstate1..4` keys [VERIFIED] (src: bin/t7.def.json). Lights, models and several volumes do; probes do not. You cannot hide one probe in one state.

### 7.3 Probes and lighting states

Radiant keeps probe data per lighting state: its lighting-export code names `probe.irradianceXArray[ledState]`, `probe.exposures[ledState]` and `probe.avgCubeColors[ledState]` [VERIFIED strings]. The SunSky doc says each lighting state "has runtime lighting and an optional baked lighting override", and "ssi is what will bake into the reflection probes" [VERIFIED] (src: SunSky_Light_SetUp.pdf p.1). So **each state gets its own probe bake**, built from that state's lights and that state's SSI [INFERRED meaning of the field names].

That is how "the whole tower lights up at power" works when done through states: the lights authored for the powered state are baked into that state's probes, and switching state switches the bounce and the reflections along with the lights [INFERRED]. Naming used in this reference: **Radiant State N** is the light key `lightingstateN`; **script state n** is the argument of `util::set_lighting_state(n)`; script state n shows Radiant State n+1 [INFERRED, strongly supported]. See [02 §2](02_power_and_states.md#2-radiant-state-n-and-script-state-n).

Consequences:
- **Fill every state you use with a real SSI** on the `volume_sun` (`ssi1`, `ssi2` …), or that state's probes are baked against whatever the LED puts there. For unset states our compiled `.led` lists `default_day` [VERIFIED byte scan, see [05 §2.5](05_sun_sky_exposure_fog.md#25-lighting-states-on-the-sun-volume)]. Whether an unset state's probes are then baked under `default_day`'s bright warm sun, or reuse another state's data (Radiant has `NO BAKE STATE %d using %d`), is unknown [TEST].
- **Runtime override.** With `ssiN_runtime_override` set, the override is what shows in game while `ssiN` is what bakes GI and probes; `override_reflections` (default false, "Use the run-time override SSI in the reflection probe final renders") makes the probes' reflection renders use the runtime SSI instead [VERIFIED] (src: SunSky_Light_SetUp.pdf p.1, p.16-17; t7.def.json). With no override set (the default is empty), `ssiN` is presumably what is displayed as well [INFERRED]. Our `volume_sun` sets no override. Treyarch warns that pushing the two too far apart makes "your reflections … not match the visible sky" [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.2).
- **Area-by-area power** (one floor at a time) cannot be done with states, which switch the whole map. Exploder lights do not re-bake probes, so a floor lit by exploders keeps the probes of the unchanged state [INFERRED]. Design options are in [02 §14](02_power_and_states.md#14-architecture-choosing-a-mechanism).
- The installed Radiant can preview each state's bake from the camera window's lighting-state control [INFERRED from the per-state data; exact UI not verified].

---

## 8. The global probe

**Plain version.** The `volume_sun` is also a probe: "The Sun Volume is a Global Reflection Probe." [VERIFIED] (src: SunSky_Light_SetUp.pdf p.1). Imagine one chrome ball floating at a single point, photographing the whole map. Everywhere a local probe does not cover, every surface takes its reflections and bounce light from that one photo, shaded by a coarse occlusion grid that spans the whole sun volume. If the ball sits inside a wall, it photographs the inside of a wall. Placement and SSI questions are covered in [05 §2.4](05_sun_sky_exposure_fog.md#24-the-global-probe-and-target); this section covers the probe side.

### 8.1 What the docs say [VERIFIED]

- "When you create a sun-volume a global probe is created at the center of the sun-volume. All reflections and bounce lighting are generated from this global probe unless you override areas with a local probe." (src: Lighting_Probe_Workflow.pdf p.1)
- "If you do not like the location of the global probe you can move it by targeting another object … the sun volume is targeting an info_null." (p.1)
- "Its very important to place the global probe in an ideal average location for each sun-volume … Problems can occur when the global probe's position is buried inside of geometry or at too high of an altitude … the bounce color is very very different." (p.2)
- "The global probe has its own 3d texture for occlusion … Without the grid everything in the sun volume would roughly get the same bounce lighting." (p.2)
- "The global probe provides ambient lighting based on how visible the sky is to surfaces … The global probe only blends in outside of the attenuation range of all other probes." (src: Reflection_Probes.pdf p.6)

### 8.2 The keys that matter for the probe

| `volume_sun` key | Default | Meaning |
|---|---|---|
| `target` | — | the `targetname` of an `info_null` that becomes the global probe's capture point |
| `grid_density` | 32 (4…64) | "number of probe points in each dimension"; "based on the size of the Sun Volume not world units"; memory, not frame time |
| `global_fill_color` | 0 0 0 | "Occluded parts of the global probe will be filled with this color. Should match the average ground color." |
| `global_fill_intensity` | 1.0 (0–30) | "The global fill color will be multiplied by this value for an HDR result." |
| `ssi1..4`, `ssi1..4_runtime_override`, `override_reflections` | `ssi1 default_day`, the other SSI slots empty; `override_reflections` false | the per-state sun and sky that bake into all probes ([§7.3](#73-probes-and-lighting-states)) |
| `respectLightLods` | true | "When this is false, lights will never LOD out in probe bounce and reflections." |
| `min_occlusion` | 0, hidden | "Obsolete" in the def, though Reflection_Probes.pdf p.6 still describes a minimum-occlusion parameter |

(src: bin/t7.def.json volume_sun; SunSky_Light_SetUp.pdf p.1) [VERIFIED]

### 8.3 Grid spacing: bigger volume, coarser grid

The point count is fixed by `grid_density`; the points are spread over the whole sun volume. So a taller volume gives coarser shading [VERIFIED doc wording; spacing arithmetic INFERRED]:

| Map | Sun volume (x × y × z) | grid_density | Approx. cell size |
|---|---|---|---|
| The Giant | 6,839 × 9,686 × 3,072 | 32 | ~214 × 303 × 96 |
| TOD II | 24,448 × 24,448 × 40,044 | 32 | ~764 × 764 × 1,251 |

(src: zm_giant_light.map volume_sun brush; map_source/zm/zm_tod2_cybercity.map volume_sun brush). Our whole 1,080-unit plaza spans about 1.4 global cells horizontally, and one cell is taller than three floors of the tower. Where our map falls back to the global probe, its bounce shading is close to "everything gets the same bounce", the case the doc says the grid was added to avoid [INFERRED].

### 8.4 Stock practice

All three stock light prefabs that contain a sun volume pin the global probe with `target` → `info_null` (The Giant: `auto11353318`; mp_sector and mp_combine: `auto3`) [VERIFIED] (src: zm_giant_light.map; mp_sector_light.map; mp_combine_light.map). The Giant's `volume_sun`: `ssi1 zm_factory`, `ssi2 zm_factory`, `target auto11353318`, `global_fill_color 0 0 0`, `global_fill_intensity 1`, `grid_density 32` [VERIFIED] (src: zm_giant_light.map lines ~14205-14217). The `info_null` sits at prefab position (−131, 49.5, 1812.5), world z ≈ 710 once the prefab's −1103 offset is applied [VERIFIED arithmetic]; it has been described as about 300 units above the playable roofs [INFERRED, not measured here]. The Mod Tools ZM template's `volume_sun` has no `target` (src: rex/templates/ZM Mod Level/map_source/zm/template.map) [VERIFIED].

A community mapper saw "when I go outside a reflection probe the whole lighting becomes super bright", and fixed it when he found "the suns X, Y and Z axis … were inside a building" and expanded the sun volume so they were not [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3307.html). That is the doc's buried-probe warning seen in a real map.

---

## 9. Brightness, darkness and exposure

### 9.1 Reflection brightness correction

The 2016 talk describes a correction credited to [LAZAROV13]: the reflection sampled from the cubemap is capped against the pixel's baked diffuse bounce light [VERIFIED as the talk's formula; that retail BO3 runs it exactly so is INFERRED] (src: talk p.65-67):

```
adjustedMaxSpec = diffuseGILum * maximumSpecValue(mip, nDotV)   // maximumSpecValue: an experimentally fitted term
reflection      = cubeMapSample * adjustedMaxSpec / (adjustedMaxSpec + luminance(cubeMapSample))
```

It is a **soft cap**, not a straight multiplier. Where a pixel's bounce light is low compared with the reflected picture, the reflection is strongly damped; where bounce is high, the reflection passes almost unchanged. In the talk's words: "Assume a maximum specular brightness that created this diffuse brightness. Adjust the sampled specular against the theoretical maximum."

**Why a dark map cares** [INFERRED; in-game look untested]: a pitch-black room can mute the reflections on its own floor even when its probe captured a bright neon sign. Remedies, all inside one room's probe:
- a `PROBE_ONLY` light or two near the neon, which raises the bounce there at no runtime cost ([01 §10](01_lights.md#10-bounce-bake_intensity_scale-and-probe_only));
- a positive `brightnessAdjust` on that probe;
- a stronger `bake_intensity_scale` on the real light.

### 9.2 Knobs that darken or brighten bounce

| Knob | Where | Effect | Guidance |
|---|---|---|---|
| `brightnessAdjust` | probe, −5…5 | "scale the brightness of the bounce during bake"; units undocumented | Treyarch MP starts interiors at "probe brightness = 2" (probably this key [INFERRED]); mp_sector uses 0.5–3 on 31 probes [VERIFIED]; a community lighter uses it only to darken, saying raising it gives "splotchy" bounce [COMMUNITY, VerK0 Part 4]; zm_alien_isolation uses −5 on 12 probes [COMMUNITY] |
| `evcomp` | probe, −5…5 | "EV compensation to final probe exposure" | "avoid evcomp on probes. Pretend it doesn't exist, unless you have a special case where it is needed. The artifacts and look of evcomp on probes is not desired." [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.3). The Giant uses −5 on 5 probes; the sign's effect is [TEST] ([05 §5.5](05_sun_sky_exposure_fog.md#55-which-way-does-evcmp-push-unverified)) |
| `probes_only` geometry | model / brushmodel | "Only export in probes": cards that only the bake sees [VERIFIED def] | black cards should block unwanted bounce and bright cards add it [INFERRED]; The Giant has one grey card (`core_50_grey`, [§3.1](#31-keys-on-other-entities-that-change-what-probes-see)) |
| `PROBE_ONLY` lights | light | bounce and reflection highlights only | The Giant: 149 of 543 lights, median radius ~250, stops ~7.6 [VERIFIED counts] |
| `ao_*` | probe | contact darkening in the bounce | "A very broad global ambient occlusion has proven to be a problem for visibility" [VERIFIED] |
| `global_fill_color` / `_intensity` | volume_sun | what the global probe's occluded parts turn into | default black; "should match the average ground color" [VERIFIED] |
| runtime override | volume_sun | bake the bounce from a brighter SSI than the one shown | Treyarch MP: "+1-2 stops of sun bake … greatly increased player visibility" [VERIFIED] ([05 §2.6](05_sun_sky_exposure_fog.md#26-bake-one-look-display-another-the-override-trick)) |

### 9.3 Exposure reads the probes

Probes store exposure values (`probe.exposures[ledState]` [VERIFIED string]), `SetExposureInstantSnap` snaps "to base calculated probe value" [VERIFIED], and a probe's `evcomp` is "EV compensation to final probe exposure" [VERIFIED def]. So the camera's auto-exposure takes its target from the probe the player stands in [INFERRED]. If exposure is not clamped, auto-exposure will try to brighten a dark room back to grey. Our `tod_ssi_cybercity` clamps EV to 3–3.5 (`evcmp` 2.5) (src: source_data/tod_skybox.gdt), so probe-driven exposure changes are limited to about half a stop [INFERRED]. Treyarch MP: visibility suffers once exposure drops "2 or more stops below the scene exposure"; interiors are usually only 1 stop darker [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf p.3). Exposure itself is covered in [05 §5](05_sun_sky_exposure_fog.md#5-exposure).

### 9.4 Dark-map rules for probes

1. **A probe captures darkness.** A cubemap baked in a dark room is dark; its reflections show mostly the bright things it can see: emissive signs, lamp heads, lit walls. That is the "wet neon" look [INFERRED].
2. **A point light has no visible body in a cubemap.** For a lamp to appear in a wet floor you need an emissive lamp head (or sign or strip) the probe can see, plus the light's own highlight on the glossy floor ([§10.4](#104-the-lights-own-highlight-spec_comp)) [INFERRED].
3. **Give dark rooms their own probe.** Otherwise they inherit the global probe's average, which in an open-sky map is brighter than any closed room [INFERRED].
4. **Emissive surfaces and bounce.** No doc, material field or `lit_emissive*` render flag makes an emissive surface a light source in the bake; the one documented emissive light source is the sky material (`skyStops`; "to see the effect of the bounced (GI) light you need to rebake") [VERIFIED] (src: SunSky_Light_SetUp.pdf; deffiles/material.awi; techsetdefs_stable/renderFlags.techsetdef). But bounce voxels read colour from probe cubemaps, so a large glowing panel that a probe can see might still add bounce there. Whether it does is unknown [INFERRED, TEST]. See [03 §4](03_glow_and_perks.md#4-does-an-emissive-surface-light-up-the-room).
5. **Adding a probe can brighten a dark outdoor area.** Two community threads report exactly that, unresolved [COMMUNITY] (src: https://forum.modme.co/wiki/threads/329.html; /383.html). Candidates: the new probe's capture sees more sky than the global probe does; try negative `brightnessAdjust` [INFERRED].

---

## 10. The material side: how much a surface reflects

**Plain version.** The probe supplies the picture. The material decides three things: how *sharp* the reflection is (gloss), how *strong* it is (reflection amount, occlusion, the metal/non-metal mask), and whether the lamps also paint a highlight on it (specular). A mirror is maximum gloss with full reflection. Rough concrete is low gloss, so it takes only a blurry wash of the probe. Treyarch's PBR rule underneath: "The light that comes off of a surface cannot exceed the light that hits the surface." [VERIFIED] (src: PhysicallyBasedRendering.pptx).

### 10.1 The fields

| GDT key (APE label) | Range / default | What it does |
|---|---|---|
| `glossRangeMin` / `glossRangeMax` ("Gloss Range") | 0–17, default 0 / 13 | "Maps relative gloss (from the gloss map) to absolute gloss range." 17 is the engine's maximum glossiness ("Maximum glossiness of 2^17", PBR deck), i.e. a mirror [VERIFIED] |
| `glossSurfaceType` (Gloss Range preset) | e.g. carpet, paper, plaster 0–2; asphalt, brick, concrete, rock 0–4; wood 2–5; paint 2–7; skin 2–10; plastic, mud 4–13; snow 4–12; ice 4–17; glass, water 6–17; metal, ceramic, `<full>` 0–17; `<custom>` = manual | sets the range for you |
| `cosinePowerMap` ("Gloss Mask") | image | the gloss map: white = the top of the range, black = the bottom. "Paint this values full range regardless of glossiness" |
| `reflectionProbeAmount` ("Reflection Amount") | 0–1, default 1 | "Controls how much reflection map is shown on surface: 1 = full amount 0 = none." |
| `specAmount` ("Specular Amount") | 0–1, default 1 | "Use this to suppress specularity: 0 is fully suppressed" |
| `specColorMap` (Specular Map) | image; `$white_specular`, `$spec_simple`… | the metalness mask: "White will fully use the metallic color in the Specular Tint color picker, black will use specular simple." Metals reflect in their own colour and have almost no diffuse |
| `specColorTint` ("Specular Color") | sRGB | the metal's reflectance colour; stock metals sit above 187 brightness except gold, copper and brass |
| `occMap` ("Ambient Occlusion Map") | image | "Values in this texture only affect two things, the amount of ambient light that will light the surface and the amount of reflection probe that will visible on the surface." |
| `specReflectionMap` ("Reflection Occlusion Map") | image | "used to reduce the brightness of the reflection - so it is useful for masking or reducing slots and cavities" |

(src: deffiles/material.awi lines ~139-289 presets, 884-907, 917, 958-959; docs_modtools/Materials.pdf p.1, p.3, p.8-9) [VERIFIED]. Also from Treyarch's PBR deck: albedo "No values below 40, none above 238. This leaves room for lighting", and "AO only affects the indirect lighting: reflection and bounced diffuse" [VERIFIED] (src: PhysicallyBasedRendering.pptx slides 10, 13). Make darkness with light and probes, not with black textures.

### 10.2 Three materials from this project, compared

| Material | Type | Gloss | Reflection amount | Spec | Metal mask | Occlusion | Normal map | Reads as |
|---|---|---|---|---|---|---|---|---|
| vertigo `mwiii_vertigo_retro_synth_*` (the whole tower) | lit_emissive_advanced (27 of 30) | 0–15 or 0–16 over a gloss map averaging 246/255 (96.6% white) | 1 | 1 | `$white_specular` (fully metallic [INFERRED from the PBR deck's "white where metal"]), tint 0.25–0.35 | `$occlusion_50` | none | a polished dark mirror [INFERRED from the values] |
| `mtl_tod_altar` frame | lit_emissive_advanced_fullspec | 0–6 | 0.15 | 0.2 | baked `i_tod_altar_s` map, tint 0.25 | — | yes | satin; user-approved after a matte pass was rejected |
| `tod_door_*` slabs | lit_emissive_advanced | 0–0 | 0 | 0 | `$white_specular`, tint 0 | `$occlusion_50` | none | fully matte glow |

(src: MODTOOLS/source_data/_emox/emox_mwiii_vertigo_assets.gdt; source_data/tod_heavenly_altar.gdt; source_data/tod_materials.gdt) [VERIFIED values; gloss-map average VERIFIED by measurement]. Of the other three vertigo materials, two `light_pink_alpha` variants are `lit_emissive_scroll_transparent_nocull`, and `mwiii_vertigo_retro_synth_pap` (on, among others, the brush `mast tier 1`) is `lit_emissive_scroll_plus` with gloss 0–8 and `$black_spec_illegal` [VERIFIED]. All 30 vertigo materials carry `occMap $occlusion_50`, and so do the `tod_door_*` and `tod_hall_*` clones. By the name and the doc's occlusion rule, that likely halves both their ambient light and their probe reflection [INFERRED].

**Two lessons this project already paid for:**
- A mirror material exposes every probe error. The vertigo pack's "white albedo + 97%-white gloss map + no normal map + reflectionProbeAmount 1" is exactly the setup that makes a 144-unit template probe smear (CLAUDE.md v18.99g; memory `vertigo-materials-are-mirrors`).
- **The user wants less gloss, not dead reflections.** On the heavenly altar, an all-matte pass (zero specular, black specular, zero probe) was rejected ("flattened the exterior"), and the kept fix lowered `glossRangeMax` 8 → 6 with `specAmount 0.2`, `reflectionProbeAmount 0.15` (CLAUDE.md, 2026-09-16 altar entries). Tone a surface down; do not switch it off wholesale.

### 10.3 Wet surfaces

**Stock wet is not a shader.** Treyarch's `_wet` materials are ordinary materials with a raised gloss range and sometimes a wet-specific normal map; no techset implements wetness, and the `gWetness*` fields in `material.awi` are read by no techset [VERIFIED] (src: texture_assets/t7_*.gdt; techsetdefs_stable; material.awi). Examples:
- `t7_concrete_bare_dark_01`: `lit_plus`, gloss 0–2 → `_wet`: `lit`, gloss **0–17**, same colour/normal/`$white_ao`/`$spec_simple`, `reflectionProbeAmount 1` [VERIFIED] (src: texture_assets/t7_concrete.gdt).
- `t7_concrete_tiles_2x2_dirty_01_wet`: a dedicated `_wet_n` normal map and gloss min raised to 3; `wall_blocks_wet` and `wall_weathered_01_wet` also use `_wet_n` normals [VERIFIED]. So a wet variant does not always keep the dry maps.
- The 15 stock materials whose names end in `_wet` (8 in `t7_concrete.gdt`) have `glossRangeMax` 11–17: 11 on three, 12 on one, 13 on three, 15 on five, 17 on only three [VERIFIED count] (src: texture_assets/t7_*.gdt). Counting every stock material with "wet" in its name (26, including decals and `_wet_nw` / `_wet_warm` / `_wet_blend` variants), the range is 4–17, with 17 on seven; `t7_concrete_bare_wet_warm` keeps the concrete preset 0–4 [VERIFIED count].

Wet = smooth, so the surface mirrors its probe and catches every light's highlight.

**Wet and water decals** (techsets exist; in-game look untested):
- `lit_decal_normal_gloss_reveal`: "This shader was created for adding flowing water on opaque surfaces." Normal, gloss and reveal maps only; the normal is tiled and scrolled twice [VERIFIED] (src: Materials.pdf p.19).
- `lit_decal_raindrops` techset: rain-ripple map plus an "Albedo Darken" tint [VERIFIED techset].
- `lit_decal_specular_fullspec`: "you can put an oily sheen on any other material" [VERIFIED] (src: Materials.pdf p.19-20).
- `volume_weathergrime` `rain`: "Scales the amount of ripples on the wet materials (outdoors)" [VERIFIED def]; which materials respond is unknown [TEST].

Full water is in [07](07_water.md).

### 10.4 The light's own highlight: `spec_comp`

A glossy surface gets two different shines: the probe's reflection, and each runtime light's direct highlight (GGX specular). A light's `spec_comp` ("Specular boost (in stops)", −14…14, default 0) scales only that highlight [VERIFIED def]. When "every light does this to every surface nearby and it looks as if everything is made of shiny plastic", a community fix was `spec_comp` about −10 on all lights [COMMUNITY] (src: https://forum.modme.co/wiki/threads/293.html). The Giant uses −1 to −6 on 38 lights [VERIFIED count]. The SSI has the same field for the sun. More in [01 §8](01_lights.md#8-colour-and-specular).

### 10.5 Glass and mirrors

"Note that opaque glass is really a mirror." Clean glass: diffuse "gloss black (40,40,40)", gloss preset "Glass" (6–17); tinted glass puts its colour in the spec colour [VERIFIED] (src: Materials.pdf p.8-9). A glass or mirror surface still reflects only its probe's cubemap, so it can never show the player or zombies ([§2.2](#22-what-a-probe-can-never-show)).

---

## 11. Screen-space reflections and real mirrors

**Screen-space reflection (SSR)** reflects what is on screen right now, including zombies. In the Mod Tools it can be switched on only through material flags on water:
- `useScreenspaceReflection` ("Enable dynamic reflection from screen"), `useLoopedScreenspaceReflection` ("higher quality"), `maxRayDepth` (default 1000), `ssrRayDepthScale` (1), `ssrRayStepSize` (20) [VERIFIED] (src: deffiles/material.awi lines ~1165-1177).
- They are read by the `lit_water_sim*` family and `water_shore(_flow)_igc` techsets [VERIFIED] (src: share/raw/techsetdefs_stable/include/lit_water_sim_base.techsetdef). The only stock material with SSR on is `t7_water_zm_der_vats` (`lit_water_sim_flow_normal_color`; both SSR flags on, `maxRayDepth 500`, `ssrRayDepthScale 250`, `ssrRayStepSize 50`), which is The Giant's vat water (used in `map_source/_prefabs/zm/zm_giant/geo/zoneb_vat_1.map`) [VERIFIED] (src: texture_assets/t7_water.gdt).
- No SSR option exists in the PC `players/config.ini` [VERIFIED on the user's file].
- The stock deferred-lighting compute shaders do have `USE_DEFERRED_SSR` variants (`deferred_lighting_ssr`, `deferred_lighting_permuted_ssr`) [VERIFIED] (src: share/raw/techsetdefs_stable/compute/deferred.csdef). So the engine has a deferred SSR path, but no material field, config option or doc found here turns it on for ordinary surfaces. That ordinary floors and walls never get SSR is [INFERRED; TEST].

So for floors, walls, glass and weapons, plan on reflections being probe cubemaps and nothing else [INFERRED]. Water setup is in [07](07_water.md).

**A true mirror (render-to-texture), untested.** The stock techset `specialty/lit_extracam_reflection.techsetdef` samples `extracamTexture1..4` (a "Camera Index" tweak, range 1–4), with a wobble normal map and a warp amount [VERIFIED] (src: share/raw/techsetdefs_stable/specialty/lit_extracam_reflection.techsetdef). A client script feeds it by making a camera entity an extra cam: `cameraEnt SetExtraCam( index, width, height )`, whose index is documented as "Valid values are 0 - 3" [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm). No stock material uses the techset (none in source_data, texture_assets or model_export), and the only stock scripts that call `SetExtraCam` are the generic extra-cam helpers `share/raw/scripts/core/_multi_extracam.csc` and `share/raw/scripts/mp/_multi_extracam.csc` [VERIFIED absence/presence]. How the techset's index 1–4 maps to `SetExtraCam`'s 0–3, the frame cost of a second scene render, and whether it works in a zombies usermap are all [TEST]. Two modme posters disagree about whether true mirrors are possible at all [COMMUNITY] (src: modme 2946).

---

## 12. Recipes

### 12.1 Fit a box probe to a room in Radiant

1. Place a `reflection_probe`, or bind *Create Auto Probe* and press it with the mouse over the floor.
2. Put the capture near the room's visual centre, about 72 above the floor (Treyarch median 75–90).
3. With only the probe selected, **Alt + left-click** each wall, the floor and the ceiling. Turn on *Show Unselected Probe Boxes* to snap against a neighbour's box.
4. **Alt + right-click** the floor and the five most important walls for reflection planes, or press **W** (box).
5. Blends 3–10. Inner boxes meet at doorways; blends overlap.
6. Keep `resolution 4x`, `ao_power 1`, `ao_range 8`, `ao_strength 1` unless there is a reason.
7. Full bake (Force Clean Rebuild), link, look at a chrome sphere or a glossy test surface from several angles.

(src: Reflection_Probes.pdf; Bouncy_Betty_Probes.pdf; Multiplayer_Lighting_Workflow.pdf)

### 12.2 Generate fitted probes from `gen_tower_map.js` (proposal, untested)

Our map is generated, so the fit has to come from the room tables.
1. Change `probe(label, x, y, z)` to take a room: `{ x1, x2, y1, y2, zFloor, zCeil | null }` (inside faces).
2. `origin` = (centre x, centre y, zFloor + 72); `size_min` = (ox − x1, oy − y1, 72); `size_max` = (x2 − ox, y2 − oy, top − (zFloor + 72)), where top = zCeil, or wall top + margin for open-top rooms.
3. `targetPlaneN` from the same bounds ([§4.3](#43-reflection-planes)): floor, walls, ceiling only if closed.
4. Emit `resolution 4x`, `ao_power 1`, `ao_range 8`, `ao_strength 1`, `ao_strength_double_sided 0.2`, `inpaint_occluded_rays 1`, `blend_mins/maxs` (start `8 8 8`), `box 1`, `high_detail 1`, `in_play_space 1` (0 if all sides exceed 1000), `client_server ClientSide`, `name probe`, `placement_offset 72`, `debug_render_index_x 64`.
5. Stop emitting `radius`, `exploderFade`, `grid_density`.
6. **Asserts** (the generator already throws on similar layout mistakes): every probe origin is outside every emitted solid; every box contains its room's floor; boxes are not degenerate; the probe count stays under a set ceiling (start at 200, below the ~254 hint); a printed per-probe report.
7. FULL build. Verify the plane convention on one probe in Radiant (press W on a copy and compare).

### 12.3 Pin the global probe and A/B it

1. Choose an open-air, representative spot, never inside a brush and not at an extreme height ([§15.3](#153-the-fix-plan) has TOD II candidates).
2. Emit an `info_null` with a `targetname` (e.g. `tod_global_probe`) and add `target tod_global_probe` to the `volume_sun`.
3. Add a small chrome sphere beside the `info_null` for Radiant checks. Leave `global_fill_color` at its default in this build; changing it is a separate A/B (Phase 5 below), because every shipped Treyarch sun volume keeps `0 0 0` even though the def says it "should match the average ground color" ([05](05_sun_sky_exposure_fog.md)).
4. Change nothing else in that build. FULL build.
5. Compare same-spot, same-state screenshots against the previous build ([09 §7.1](09_design_and_inspiration.md#71-same-spot-same-state-same-settings)), and compare the `.led` size (docs/107's fingerprint method).
6. In Radiant, toggle *Hide Local Probes* / *Hide Global Probe* to see which one lights a spot.

(src: Lighting_Probe_Workflow.pdf p.1-2; zm_giant_light.map)

### 12.4 Cover a spiral stair around a solid core

The tower's laps climb two sides of a 512-wide solid core per lap (odd laps E + N, even laps W + S), with the lap probe already at the mid landing where the two flights meet (±336, ±336) [VERIFIED positions].
1. One real probe per lap. Box x/y to the parapet line (±436), z from the lap's start to the next lap's start (384 tall). The core inside the box is solid; its voxels are probably invalidated and filled from their neighbours [INFERRED from the talk's slide titles "Invalidate Near Geometry" and "Volume Smoothing", p.53, p.56].
2. Capture at the mid landing, 72 above it: from there it sees along both of that lap's flights.
3. Planes: the landing floor and the two core faces the capture sees (odd lap: `1 0 0 258` and `0 1 0 258`; even lap: `-1 0 0 258` and `0 -1 0 258`, under the [INFERRED] convention). No outer walls: the stair is open to the sky.
4. Add virtual probes at the other two core corners if the bounce behind the core looks wrong.
5. Count: 50 tower laps + 70 spire laps = 120 real probes. With the rooms, the total stays below the ~254 hint ([§15.3](#153-the-fix-plan)).

### 12.5 A wet neon floor that shows the neon

1. Floor material: a real normal map; `$spec_simple` or a dark metal mask; gloss about 3–15 up to 0–17; `reflectionProbeAmount 1`. Optionally a `lit_decal_normal_gloss_reveal` or raindrop decal for puddles.
2. The neon needs a body the probe can see: emissive geometry or a `misc_model` (not a plain `script_model`, which is not in the bake by default).
3. A real light near the neon for the runtime highlight; tune its `spec_comp` if it looks plastic.
4. A fitted local probe that covers the floor, can see the neon, and has floor and wall planes.
5. If the room's bounce is near-black, add a `PROBE_ONLY` light near the neon or raise that probe's `brightnessAdjust` ([§9.1](#91-reflection-brightness-correction)).
6. FULL build; check from several angles.

### 12.6 Keep a dark room dark without breaking it

1. Give it its own fitted probe so it does not inherit the global probe.
2. Try a negative `brightnessAdjust` (−1 to −5); use `evcomp` only if needed and test it (Treyarch warns about artifacts).
3. Black `probes_only` cards at openings to stop bounce leaking in; keep `global_fill_color` dark.
4. Keep the playable floor readable: no more than ~2 stops under the scene exposure (Treyarch MP). Clamp exposure in the SSI rather than crushing the probes.
5. Re-bake; compare with *Show Lighting Only* and *Diffuse GI Only*.

### 12.7 Tone down a mirror material without killing it

1. Never edit a shared third-party GDT. In this repo, clone the material into a map-owned GDT in the private workspace (`C:\BO3Tools\TOD2Cybercity`, docs/154), the way `tod_door_*` clones the vertigo pack.
2. First lower `glossRangeMax` (for example 15/16 → 10–12) so reflections blur and parallax errors hide [INFERRED values]. Then, if needed, lower `reflectionProbeAmount` a little (the altar kept 0.15).
3. Consider a normal map, so the reflection breaks up instead of mirroring flat.
4. Do not zero specular, gloss and reflection together: that is the rejected matte-altar look.
5. FULL build; same-spot screenshots.

### 12.8 Power-on reflections

1. Choose the convention and author lights per Radiant state ([02 §4](02_power_and_states.md#4-the-two-working-conventions)).
2. Fill `volume_sun` `ssiN` for every state used.
3. FULL bake: each state gets its own probe data ([§7.3](#73-probes-and-lighting-states)).
4. Call `util::set_lighting_state(n)` at power, as `zm_giant.gsc:571` does [VERIFIED stock call].
5. Place probes so that the rooms that change at power have their own probes; a room covered only by the global probe changes only as much as the global probe's view changes [INFERRED].

### 12.9 Log which probe a player stands in

A dev-gated server log, following CLAUDE.md's diagnostic pattern (`[TOD_PROBE]` tag, `level.tod_dev` gate, `PrintLn` inside `/# #/`):
1. At `initial_blackscreen_passed`, log `GetReflectionLocs().size` once.
2. On each player's spawn and when the player's floor or zone changes, log `GetReflectionOrigin( player.origin )` with the player's position and zone.
3. Log only on change, never per frame.

This tells a playtest which probe (or the global probe) served each area. What the function returns outside all local probes is itself the first thing to learn [TEST]. Recommendation only; nothing is implemented.

---

## 13. Symptoms, causes, fixes

| Symptom | Likely cause | Fix | Source |
|---|---|---|---|
| Reflections smear, or look the same everywhere; walls, gun and zombies share one colour cast | local probe boxes too small or floating, so most pixels use the global probe (which has no planes and one capture point) | fit a box to every space, capture ~72 above the floor, set planes; pin the global probe | Reflection_Probes.pdf p.6; our audit |
| The whole map changes colour when the sun volume is resized (docs/107) | the global probe sits at the volume centre and its grid scales with the volume; resizing moves the capture point, here into a different brush | `target` an `info_null` in open air; keep `grid_density` fixed | Lighting_Probe_Workflow.pdf; docs/107 [INFERRED mechanism] |
| "Outside a probe the lighting becomes super bright" | leaving local coverage exposes a bad global probe | adjacent probes that touch; move the global probe out of geometry | modme 3307 [COMMUNITY] |
| Coverage reasoned from `radius` on a probe | `radius` is a light key | size the box with `size_min`/`size_max` | t7.def.json |
| Everything looks like shiny plastic under lights | light highlights at full strength on glossy materials | lower `spec_comp` on lights, or lower gloss / `specAmount` | modme 293 [COMMUNITY]; Giant data |
| Zombies and players never appear in reflections | reflections are baked cubemaps | expected; the only authorable SSR is on water materials | material.awi; t7_water.gdt |
| Neon reflections weak in a dark room | brightness correction caps reflection by the bounce; point lights have no body in a cubemap | emissive fixtures the probe sees; `PROBE_ONLY` lights; `brightnessAdjust` | talk p.65-67 [INFERRED effect] |
| Probe edits don't show in game | probes bake in the LED; `-GscOnly` keeps the old bake | FULL build | SunSky p.15-16; build_map.ps1 |
| After power the lighting looks unbaked or wrong | that state's SSI slot is empty, or its lights were never assigned | `ssiN` for every used state; re-bake; preview the state in Radiant | t7.def.json; 02 |
| Reflections carry a fog tint the scene does not have | fog is baked into probes even when script turns it off | lower the fsi's probe-bake scalers, or bake with the fog you ship | fog.awi [INFERRED effect] |
| A subtract child does nothing | `subtract` is ignored on the parent | put it on a child that targets the parent | Subtract_Probes.pdf |
| Radiant runs out of memory after probe debugging | debug rays stored for many probes | `debug_render_index_x` back to 64 | Reflection_Probes.pdf p.5 |
| Frame cost rises around many overlapping probes | 2 and 3+ probes per pixel use slower shaders; overrides still count | smaller blends; multiface or subtract instead of stacked boxes | Priority_Probes.pdf |
| `Probe at … out of range` during the bake | the probe sees something broken, often light leaking through gaps | seal the leak; check the capture point is not in or against a brush | Radiant string; modme 290 [COMMUNITY] |
| One room reflects the inside of a wall or reads black | its capture point is inside or touching a solid brush | move the capture into open air; assert it in the generator | [INFERRED]; our audit ([§15.1](#151-audit)) |
| A dark outdoor area got brighter after adding a probe | the new capture sees more sky than the global probe did | negative `brightnessAdjust`; check the capture point | modme 329, 383 [COMMUNITY, unresolved] |

---

## 14. Open questions and tests

Every item needs a FULL build; the user runs the game (CLAUDE.md).

1. **What a buried global probe captures, and whether it explains docs/107.** A/B: `volume_sun` `target` → open-air `info_null` versus today, same-spot same-state screenshots, plus Radiant *Hide Local Probes*. [TEST]
2. **Unset `ssi2` and the probes of the live state.** Is Radiant State 2's probe data (the state the map boots into, by the [INFERRED] mapping) baked under `default_day`, reused from State 1, or skipped? Radiant has a `NO BAKE STATE %d using %d` message, so reuse is possible. A/B: `ssi2 = tod_ssi_cybercity` only, compare screenshots and `.led` size. [TEST]
3. **`radius`, `exploderFade`, non-zero `grid_density` on probes.** Inert or not: A/B one probe with and without them, compare the probe-blend view. [TEST]
4. **`resolution` in world units.** Measure in Radiant's probe-blend view on a probe of known size. [TEST]
5. **The ~254 probe limit.** Only a dvar-text hint. Test a scratch map with more than 254 non-virtual probes, or find the error string. [TEST]
6. **The `targetPlane` convention** for non-prefab entities: press W on a generated probe and read what Radiant writes. [TEST]
7. **Emissive in the bake.** One emissive panel in a black room, baked with and without; compare *Diffuse GI Only* and *Specular GI Only*. [TEST]
8. **CLI local-probe export.** Change one probe box and confirm the `.led` changes (the CLI has no `+localprobes` switch). [TEST]
9. **`GetReflectionOrigin` outside local probes**: what it returns, via the §12.9 log. [TEST]
10. **`evcomp` sign on a probe.** Same view with a probe at +2 and −2. [TEST]
11. **In-game probe overlays** ("Active/Visible Probes Per Pixel"): dvar names not found. [TEST]
12. **The extracam mirror** in a zombies usermap: index mapping, cost, whether it renders. [TEST]
13. **Deferred SSR on ordinary surfaces.** The deferred lighting shader has `USE_DEFERRED_SSR` variants ([§11](#11-screen-space-reflections-and-real-mirrors)); whether anything turns them on in a PC usermap is unknown. [TEST]

---

## For Tower of Doom II

### 15.1 Audit

All numbers from `map_source/zm/zm_tod2_cybercity.map` (as generated 2026-09-24) and `tools/gen_tower_map.js` `probe()` and the `volume_sun` emitter [VERIFIED data; arithmetic by point-in-box tests on axis-aligned brushes; the ~900 non-axis-aligned brushes, mostly the crown's convex ones, were not tested]. The generator is being edited, so re-run the audit before acting on a number.

**The probes.**
- **53 probes**: base 1; vault, conduit, shaft 3; wings 4; tower laps 1, 4, 7 … 49 (17); crown 5 (terrace, hall, ring S, ring N, upper); spire base 1; spire laps 1, 6 … 66 (14); spire hubs 10 … 70 (7); spire summit 1.
- **Every one is the Mod Tools template probe**, byte for byte apart from its origin: `radius 2048`, `ao_power 2`, `ao_range 16`, `ao_strength 1`, blends `3 3 3`, `box 1`, `exploderFade 1`, `grid_density 16`, `debug_render_index_x 64`, `high_detail 1`, `in_play_space 1`, `placement_offset 72`, `size_min`/`size_max 72 72 72`. There is no `resolution` (so presumably 4x), **no reflection planes**, and AO power/range differ from Treyarch's 1 / 8 guidance. (src: template.map; t7.def.json)
- **Each box is a 144-unit cube around its capture point.** `radius 2048` is not a probe key and presumably does nothing [INFERRED]. Two generator comments reason from that dead key: the crown one ("`probe crown hall` has radius 2048 and the circlet now reaches +-2048 …") and the spawn one ("'probe base' has radius 2048 and covers the whole 1080-wide arena from anywhere in it") (src: tools/gen_tower_map.js, near `probe()` and the docs/158 spawn block).
- **No box reaches the floor it serves.** Measured straight down from each capture point to the nearest axis-aligned solid: about 150 above the floor for the base, wings, laps and most spire probes; 140 for the vault and conduit (139 over the 1-unit floor trace); 88 for the shaft (over a tread); 102–134 for spire hub 10, hub 40 and the summit; 184 and 224 for the crown hall and crown ring S; 5,344 for crown upper. So box bottoms are 16–152 units above the walking surface below (16 for the shaft, 30 over hub 40's altar deck, 54 over hub 10's stage, 62–78 for most), and 5,272 for crown upper. The one place a floor enters a box is an 8-unit sliver of one tread (`shaft step 19`, top z −156) at the shaft box's east edge. `probe crown ring N` has no axis-aligned floor under it at all (the crown's convex brushes were not tested). The base probe covers z 78–222 over a floor at 0, about 2% of the plaza's floor area in plan and none of the floor itself.
- **Four spire probes capture from inside or on a solid brush** [VERIFIED arithmetic; effect INFERRED: the cubemap photographs the inside of the brush and the capture point sees no room]:

| Probe | Origin | Brush it is in |
|---|---|---|
| `probe spire base` | 10240 0 150 | inside `spire core column below hub 10` (x 9984–10496, y ±256, z 0–3632) |
| `probe spire hub50` | 10240 0 19158 | on the south face of `spire hub lap50 the maze twall 1` (x 10230–10330, y 0–20, z 19008–19168) |
| `probe spire hub60` | 10240 0 22998 | inside `spire hub lap60 the gauntlet twall 1` (x 10230–10250, y −236–100, z 22848–23008) |
| `probe spire summit` | 10240 0 27222 | inside `spire summit mast t1` (x 10192–10288, y ±48, z 27088–27264) |

  The hub probes sit on the spire's centre line, and the v18.80 trial-hall rooms later put walls there. Radiant's *Check Probe Geometry Changes* would not have caught this (it tracks only Alt-click points on box faces, and the doc says new geometry put in front of them is not caught; [§6.1](#61-fitting-controls)). A generator assert that every capture point is in open air would have.
- **Result** [INFERRED]: since "the global probe only blends in outside of the attenuation range of all other probes", nearly every floor, wall, weapon and zombie in the map takes its bounce and its reflections from the global probe. CLAUDE.md's note ("all 46 reflection probes ship Radiant's DEFAULT 72-unit parallax box … That is what makes reflections SMEAR") needs three corrections: there are 53, 72 is the influence box's half-size (not a parallax box, and the probes have no planes at all), and most surfaces are outside every local box anyway, so the likelier smear source is the single global probe.

**The global probe.**
- The `volume_sun` has no `target`. Its brush spans x/y ±12,224 and z −544…39,500, so its centre and the global probe's capture point are at **(0, 0, 19,478)**. That point is inside the worldspawn brush `mast tier 1` (x/y ±256, z 19,392–19,712, material `mwiii_vertigo_retro_synth_pap`) [VERIFIED arithmetic]. Treyarch warns that a buried global probe makes the "bounce color … very very different" [VERIFIED].
- Its grid cells are about 764 × 764 × 1,251 units ([§8.3](#83-grid-spacing-bigger-volume-coarser-grid)).
- No `global_fill_color` (so black), no runtime override, and `ssi1` only plus a non-def `ssi` key; the Mod Tools template's `volume_sun` has the same shape (`ssi`, `ssi1`, no `target`), so ours inherited it [VERIFIED] (src: template.map). The map boots in script state 1, which shows Radiant State 2 [INFERRED mapping, see [02](02_power_and_states.md#2-radiant-state-n-and-script-state-n)]; that state has no SSI of its own, and the compiled `.led` lists `default_day` for the unset states ([05 §2.5](05_sun_sky_exposure_fog.md#25-lighting-states-on-the-sun-volume)). What the engine then shows is [TEST].
- **The docs/107 link** [INFERRED; geometry VERIFIED on TOD1's current map]. In TOD1's yellow builds (volume top 29,228) the centre (0, 0, 14,566) fell inside `core band lap38 spine NS` (x ±16, y ±256, z 14,208–14,592), a brush textured `mwiii_vertigo_retro_synth_yellow`. In the good build (top 39,500, bottom −96) the centre (0, 0, 19,702) fell inside `mast tier 1`, the same brush it sits in today (src: the TOD1 repository `tower_of_doom_cybercity`, map_source/zm/zm_tower_of_doom.map, point-in-brush test). A global probe buried in a yellow brush is a concrete candidate for "every surface … carried a warm yellow-olive cast" that "honoured the base lights' positions but not their colour". It is not proven: both builds had a buried probe, and the `SUN_VOLUME_TOP_MIN` fix moved the probe only as a side effect. docs/158 moved the sky floor again (to −544); the centre moved 224 units and stayed inside the same brush. **One more change to the sky's top or bottom could move it into a different brush and a different colour.** Pinning it with `target` removes that risk.

**The materials.** Every visible world face uses a vertigo-family emissive material; about half glow only on thin grid lines and the other half have a dim grey fill that glows across the face ([03 §11](03_glow_and_perks.md#11-tod-iis-all-emissive-world)). Those materials are also lit and near-mirrors ([§10.2](#102-three-materials-from-this-project-compared)), the kind that shows probe errors first; the spire's `tod_hall_*` clones are the same (gloss 0–16, `reflectionProbeAmount 1`) [VERIFIED] (src: source_data/tod_materials.gdt). The `tod_door_*` slabs are the only fully matte world surfaces.

### 15.2 What this means for the dark map

- **Probes are the ambient light of a dark map.** Today the tower's ambient comes from one photo taken inside a mast, spread over 1,251-unit cells. No amount of light tuning makes rooms read as distinct places while that holds [INFERRED].
- **Fitted probes give each room its own darkness and its own reflections:** the Vault reflecting its red window niches, a wing reflecting its hue panel, a lounge reflecting its district colour. Glass Tower's screenshots show mirror-like floors repeating a crisp sunset sky, the kind of look fitted probes are for; how that map actually builds its reflections is unknown ([09 §4.4](09_design_and_inspiration.md#44-what-we-can-borrow-and-how)). Fitting is the step that could make the vertigo mirrors an asset instead of a smear [INFERRED].
- **Order matters.** Fix the probes before judging materials, lights or exposure: every other lighting change is currently seen through the buried global probe.

### 15.3 The fix plan

Recommendations only. Each phase is a FULL build (the LED bake), is built into the private workspace (docs/154), and is judged by the user in game; agents build and stop. Change one thing per build so each result can be read.

**Phase 0: evidence, no geometry change.**
1. Add the §12.9 `[TOD_PROBE]` dev log, so the next normal playtest records which probe serves each area.
2. Add a generator report and asserts for probes ([§12.2](#122-generate-fitted-probes-from-gen_tower_mapjs-proposal-untested) item 6). It would flag the four spire probes today. The point-in-box check used for this audit is simple enough to port (axis-aligned solids, tool materials excluded).
3. Optionally, in Radiant, look at *Hide Local Probes* / *Hide Global Probe* / *Show Probe Blends* on the current map.

**Phase 1: pin the global probe (one A/B build).**
1. `info_null` with `targetname tod_global_probe` and `volume_sun` `target tod_global_probe`. Nothing else changes.
2. Candidate spots, all open air [INFERRED; check against the geometry with the assert]: (a) over the plaza between the core and the south wall, around (0, −400, 200), a gameplay-representative view of the base; (b) outside the stair ring at mid-tower, around (0, −1200, 9,600), a view of tower, stairs and city, which is what the global probe will light once the rooms have local probes. Treyarch's "ideal average location" favours (b) for the final state [INFERRED]. Both points are at least 48 units clear of every axis-aligned solid in the current `.map` [VERIFIED arithmetic; convex brushes and models not checked].
3. Compare against the current build with docs/107's same-spot method (beside the ammo crate against the base's E wall, round 1, before power) plus one stair shot, on a low and a high graphics config ([09 §7.3](09_design_and_inspiration.md#73-judge-on-two-graphics-configs)).
4. In a separate build, test `ssi2 = tod_ssi_cybercity` (question 2 in §14). That decision belongs to the lighting-state plan ([02 §15](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis)).

**Phase 2: the base first (where every match starts).**
1. Rewrite `probe()` as in §12.2 and fit: the Vault (the §4.1 numbers), the Conduit (x −2528…−2016, y −448…128, z −384…−192), the Shaft (one long box over the flight and top landing, or two; open top), the four wing rooms (512 square, 128-tall walls, open top) and their hallways, the teleport bay and the power hall.
2. The plaza: a 1,080-square open-top ring around the 512-wide solid core. Either four side boxes (full-width N and S bands, E and W bands between them) or one box with a `subtract` child for the core. Lap 1's flights rise through the E and N bands, so those boxes and the lap-1 box overlap; the smaller box wins, or use `override` [INFERRED].
3. Planes: floors and walls; no ceilings in open-top rooms.
4. Judge the vertigo floors now, before any material change.

**Phase 3: the climb.**
1. One probe per lap for both towers ([§12.4](#124-cover-a-spiral-stair-around-a-solid-core)): 120 probes.
2. The four breather lounges (544 × 576, walled, open-top) and their teleporter spurs; the crown terrace, the crown hall and the causeway as a chain of boxes along its lanes (it is 160 wide and 7,360 long); the spire base (capture moved out of the core column), the seven hub halls (captures moved off the trial-hall walls), the summit arena (capture moved out of the mast).
3. Leave the crown's and the towers' outer faces to the global probe; they are exterior surfaces seen from afar.
4. Expected total: 120 laps + roughly 40–55 rooms and segments, about 160–175 real probes. That is under the ~254 hint [INFERRED limit]. Keep the generator's count ceiling and log the count on every run.

**Phase 4: materials, only after Phases 1–3 are judged.**
1. If the fitted probes still smear on the vertigo floors, clone the floor materials into map-owned GDTs with a lower `glossRangeMax` (and, only if needed, a slightly lower `reflectionProbeAmount`), following the altar lesson ([§12.7](#127-tone-down-a-mirror-material-without-killing-it)). Floors first; walls last.
2. Consider whether `$occlusion_50` should stay once the probes carry real bounce.

**Phase 5: dark-map tuning.**
1. A/B `global_fill_color` near the average ground colour (a dark navy, for example `0.02 0.03 0.05`, to be tuned [INFERRED value]) against the default `0 0 0`, in its own build [TEST]. The def recommends it, but The Giant, mp_sector and Map One all ship black, so keep it only if the same-spot screenshots show occluded corners lifting without the dark look going grey.
2. Per-room `brightnessAdjust` for rooms that should read darker or lighter; `PROBE_ONLY` lights beside neon features whose reflections need lifting ([§9.1](#91-reflection-brightness-correction)); `evcomp` last and only with an A/B.
3. Readability first: every playable space within about 2 stops of the scene exposure ([09 §7.5](09_design_and_inspiration.md#75-readability-checks-zombies-not-scenery)).

**Keep:** `SUN_VOLUME_TOP_MIN` and the volume's size (moving the volume re-grids the global probe), the private-workspace isolation for any new GDT, and same-spot screenshots on two graphics configs for every comparison.

---

## Sources

**Official Treyarch documentation (MODTOOLS = C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130)**
- docs_modtools/Probe/Reflection_Probes.pdf: two parts of a probe; sizing and snapping (p.1); reflection planes and the 2-unit inset (p.2-3); blending and precedence (p.3-4); rotation (p.4); GI calculation, 8 closest probes, virtual probes, debug rays (p.5); the global probe (p.6).
- docs_modtools/Probe/Priority_Probes.pdf, Multiface_Probes.pdf, Subtract_Probes.pdf, Bouncy_Betty_Probes.pdf, Probe_Editing_Handles.pdf, Probe_Geometry_Change_Tracking.pdf; docs_modtools/probe_gifs.
- docs_modtools/Lighting_Probe_Workflow.pdf p.1-3: the global probe at the sun-volume centre, `target` → `info_null`, the burial warning, the occlusion grid, grid density and memory.
- docs_modtools/SunSky_Light_SetUp.pdf p.1 (the sun volume as global probe; states; "ssi is what will bake into the reflection probes"), p.13-17 (baking, rebake triggers, Lighting Export dialog, bake override).
- docs_modtools/Multiplayer_Lighting_Workflow.pdf p.2-3: sun/sky overrides, probe resolution 4x, AO 1/8/1, "probe brightness = 2", avoid evcomp on probes, exposure range.
- docs_modtools/Materials.pdf p.1, p.3, p.8-9, p.19-20: occlusion affects ambient and probe reflection; the metalness mask; glass and "opaque glass is really a mirror"; flowing-water and oily decals.
- docs_modtools/PhysicallyBasedRendering.pptx slides 3-5, 10-11, 13: the core PBR rule, GGX, 2^17 gloss, 256 × 256 blended probes, point-cloud GI bake, albedo 40–238, specular mask white where metal, AO affects indirect only.
- docs_modtools/bo3_scriptapifunctions.htm: `GetReflectionLocs`, `GetReflectionOrigin`, `SetExposureInstantSnap`, `SetExtraCam`.
- Treyarch, "Volumetric Global Illumination at Treyarch", SIGGRAPH 2016: https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf (p.2, 6, 10, 16, 23, 27-29, 43-47, 63-67, 69-70); abstract: https://advances.realtimerendering.com/s2016/index.html

**Stock data and definitions (MODTOOLS)**
- bin/t7.def.json: `reflection_probe`, `build_probe`, `volume_reflection`, `volume_sun`, `light` (`PROBE_ONLY`, `bake_intensity_scale`, `spec_comp`), `misc_model` / `script_model` / `script_brushmodel` probe keys, `info_null`.
- deffiles/material.awi (gloss presets ~139-289; spec and gloss 884-907; occlusion 917; reflection 958-959; SSR 1165-1177), deffiles/ssi.awi:40 (`bounceCount`), deffiles/fog.awi:18-19, :85 (probe-bake scalers).
- share/raw/techsetdefs_stable: compute/deferred.csdef (probe-count permutations; `USE_DEFERRED_SSR` variants); include/lit_water_sim_base.techsetdef; specialty/lit_extracam_reflection.techsetdef.
- map_source/_prefabs/zm/zm_giant/zm_giant_light.map (176 probes, planes, virtual/override/subtract, `probes_only` card, sun volume + `info_null`); map_source/_prefabs/zm/zm_giant/geo/zoneb_vat_1.map (the SSR vat water); map_source/zm/zm_giant.map; map_source/_prefabs/mp/mp_sector/mp_sector_light.map; map_source/_prefabs/mp/mp_combine/mp_combine_light.map; rex/templates/ZM Mod Level/map_source/zm/template.map.
- texture_assets/t7_concrete.gdt, t7_*.gdt (wet materials); texture_assets/t7_water.gdt (SSR); source_data/_emox/emox_mwiii_vertigo_assets.gdt (vertigo values).
- share/raw/scripts/core/_multi_extracam.csc; share/raw/scripts/zm/zm_giant.gsc:571.
- String scans of bin/Radiant_modtools.exe and bin/cod2map64.exe (render flags, bake messages, export and rebuild option names, per-state LED fields, probe error, `facePlane%d`, `r_updateSingleDynamicProbe`; no `localprobes`, no `exploderFade`).
- Call of Duty Black Ops III/players/config.ini (`TextureQualityProbes`; no SSR option).

**This repository**
- tools/gen_tower_map.js: `probe()`, the `volume_sun` emitter, `VT_*` / `CD_*` / `SHAFT_*` / `WING_*` / `ARENA` / `CORE` / `PARA` constants, the two `radius 2048` comments.
- The TOD1 repository `tower_of_doom_cybercity`, map_source/zm/zm_tower_of_doom.map (global-probe burial points for the docs/107 comparison).
- map_source/zm/zm_tod2_cybercity.map: the 53 probes, the `volume_sun`, and the brushes named in §15.1.
- source_data/tod_skybox.gdt, source_data/tod_heavenly_altar.gdt, source_data/tod_materials.gdt; tools/build_map.ps1; docs/107_sun_volume_yellow_postmortem.md; docs/104_cybercity_sky.md; docs/158_tod2_base_layout.md; docs/154_tod2_isolation.md; docs/BO3_MAPMAKING_KB.md; CLAUDE.md (v18.99g mirror door, 2026-09-16 altar entries).

**Community**
- https://forum.modme.co/wiki/threads/3307.html (global-probe axes inside a building); /293.html (`spec_comp` −10); /290.html (probe out-of-range errors); /403.html (probes touching walls, not inside each other); /329.html and /383.html (probes brightening dark outdoor areas); /2946.html (mirrors).
- VerK0, Lighting Tutorial Part 4 (reflection probes): https://www.youtube.com/watch?v=HOa08arAXlk
- http://c0de517e.blogspot.com/2016/08/activision-siggraph-2016.html (summary of the 2016 talk).
- https://github.com/MattFiler/zm_alien_isolation (a community dark map's probe values).
