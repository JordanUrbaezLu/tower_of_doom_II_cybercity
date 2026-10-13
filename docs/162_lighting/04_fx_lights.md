# 04 — FX lights, halos, lens flares and god rays

**In short.** An FX light is a light that lives inside a particle effect (an `.efx` file): one element of the effect is a `dynamicLight2` instead of a picture. It really lights walls, floors, players and zombies, but only while the effect plays, and nothing shows that it reaches the baked lighting or the reflection probes. Treyarch's documented workflow makes any light that flickers, pulses or moves an FX light, while a light that just sits there stays a normal Radiant light. An FX light's brightness, size and colour come from curves in the effect, not from the light settings block inside it, and a looping FX light should re-spawn exactly as often as each copy lives, or copies stack up. Halos, lens flares and fake light cones are separate FX elements that only look bright; they light nothing.

**Read this when…** you want a light that flickers, pulses or blinks; a perk machine, device or lamp should throw light that follows power or a moving object; you are adding a halo, lens flare, god ray or dust motes; or an effect is zoned and precached but shows nothing in game.

## Contents

1. [What an FX light is, and when to use one](#1-what-an-fx-light-is-and-when-to-use-one)
2. [Anatomy of an FX light in an .efx file](#2-anatomy-of-an-fx-light-in-an-efx-file)
3. [Curves, not the settings block, set brightness, size and colour](#3-curves-not-the-settings-block-set-brightness-size-and-colour)
4. [Units: how bright is "intensity 512"?](#4-units-how-bright-is-intensity-512)
5. [The looping rule, and why it matters](#5-the-looping-rule-and-why-it-matters)
6. [Flicker, pulse and blink](#6-flicker-pulse-and-blink)
7. [Shadows on FX lights](#7-shadows-on-fx-lights)
8. [Radiant fx entities and exploders](#8-radiant-fx-entities-and-exploders)
9. [Playing FX from script](#9-playing-fx-from-script)
10. [FX lights and power-on](#10-fx-lights-and-power-on)
11. [The Giant pattern: FX light plus a PROBE_ONLY twin](#11-the-giant-pattern-fx-light-plus-a-probe_only-twin)
12. [Halos and glow sprites](#12-halos-and-glow-sprites)
13. [Lens flares](#13-lens-flares)
14. [God rays and dust motes](#14-god-rays-and-dust-motes)
15. [Limits and cost](#15-limits-and-cost)
16. [Stock light-FX catalog](#16-stock-light-fx-catalog)
17. [The placeholder-stub trap, and how to vet an effect](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)
18. [Our FX lights today: perk glow, inducer, teleporter](#18-our-fx-lights-today-perk-glow-inducer-teleporter)
19. [Recipes](#19-recipes)
- [For Tower of Doom II](#for-tower-of-doom-ii)
- [Sources](#sources)

Paths without a prefix are under MODTOOLS (`C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`). Paths marked **repo** are in this repository. Most `.efx` files under `share/raw/fx` in this install are community (Wraith) reconstructions, not Treyarch's own sources (see [section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)). Where this chapter quotes counts from that library, they describe the local files, not necessarily Treyarch's originals.

---

## 1. What an FX light is, and when to use one

**Plain version.** An `.efx` is a recipe for particles. Most particles are flat pictures (sprites). One kind of particle is a light: while it lives, the engine adds a real dynamic light at its position. Because a particle has a life with a start and an end, its brightness, radius and colour can follow a curve over that life. That is how you get a flicker or a pulse without a single line of script.

**Zombies example.** Look at the hanging lanterns on The Giant. The lamp is a model. The visible flame is a sprite effect (`fire/fx_fire_lamp_hurricane`) [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/geo/lantern_lit.map). The wobbling orange light on the walls is a separate placed effect, `light/fx_light_lantern_factory_zmb`, whose single `dynamicLight2` element has a hand-drawn wobble in its intensity curve and a 208-unit radius [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map; share/raw/fx/light/fx_light_lantern_factory_zmb.efx).

**Treyarch's rule, word for word:** "Currently, the workflow for lights that flicker or change intensity, or that are animated in their motion or other parameters, is to create an FX light in Radiant (as a .efx file)." The same page says to start from a normal Radiant light that looks right, then "transfer those settings to the parameters of the FX light. This applies to either an omni or spot." [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1)

### The things that look like light

| Thing | What it is | Lights walls and zombies? | Can it animate? | Seen by baked bounce / reflections? | Where it is authored |
|---|---|---|---|---|---|
| Radiant `light` entity | A placed light, baked by the LED export | Yes | Only through lighting states, exploders or script-controlled lights ([01](01_lights.md), [02](02_power_and_states.md)) | Yes | Radiant; our generator's `light()` (repo tools/gen_tower_map.js) |
| **FX light** (`dynamicLight2` element) | A particle that is a light | Yes, at runtime [VERIFIED] (src: docs_modtools/FX_Lights.pdf) | Yes, that is its purpose | No evidence it is; The Giant adds a `PROBE_ONLY` twin for reflections [INFERRED] ([section 11](#11-the-giant-pattern-fx-light-plus-a-probe_only-twin)) | Radiant FX editor, or a text edit of the `.efx` |
| Emissive surface | A material that draws itself bright | No evidence it does ([03](03_glow_and_perks.md)) | Only with scroll/flicker or script material types | Unresolved ([03](03_glow_and_perks.md)) | APE / GDT |
| Glow sprite (halo) | A flat camera-facing picture of a glow | No, it is a picture | Yes (size, alpha, colour curves) | No [INFERRED] | `.efx` sprite element |
| Lens flare | Screen-space streaks and ghosts | No | Re-spawned about every frame | No | `.efx` `lensFlare` element → `.klf` asset |
| Light shaft | A volumetric light in fog, or a sprite "cone" card | Volumetric: scatters the light in fog. Cone card: no | Yes | No | light keys + fog volume; or `.efx` sprite/line |

A good-looking lamp normally uses three or four of these at once: a model with a glowing material, a small flame or glow sprite, an FX or Radiant light that actually lights the room, and sometimes a flare. The recipes for full fixtures are in [08](08_fixture_cookbook.md).

### When to pick an FX light, a Radiant light, or both

- **Use an FX light** when the light must flicker, pulse, blink or strobe; when it must move with something (a machine that relocates, a boss, a player); when script decides where it appears at runtime; or when you want it on and off without touching the map's lighting state [INFERRED] (from the doc's rule and the stock usage below).
- **Use a Radiant light** when the light is steady. It is baked into bounce and the probes, and it can use `shadowUpdate Never`. The definition's text for the `shadowUpdate` key as a whole reads "Only render the shadowmap once when missing", which describes the Never mode: a shadow drawn once and cached [INFERRED]. An FX light cannot use Never ([section 7](#7-shadows-on-fx-lights)) [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.2; bin/t7.def.json light `shadowUpdate`).
- **Use both** when an animated light should also show in reflections: the FX light carries the animation and a `PROBE_ONLY` Radiant light at the same spot feeds the probes. That is The Giant's pattern ([section 11](#11-the-giant-pattern-fx-light-plus-a-probe_only-twin)).
- **For Tower II specifically:** our perk machines scatter to new pads every few rounds (repo CLAUDE.md, perk scatter), so a baked light cannot follow them. An FX light played on the machine goes wherever the machine goes. That is why our perk glow is an FX light ([section 18](#18-our-fx-lights-today-perk-glow-inducer-teleporter)).

---

## 2. Anatomy of an FX light in an .efx file

**Plain version.** An `.efx` is a text file. It starts with a few settings for the whole effect, then lists **elements** (also called emitters). Each element says when to spawn particles, how long they live, how they move, and what they look like. The last block of an element names its visual type. For a light, that block is `dynamicLight2 { ... }` and contains a copy of a Radiant light's settings.

**Where files live.** Effects are stored as `share/raw/fx/<folder>/<name>.efx` and are named without the extension in scripts and zone lines, for example `fx,tod/fx_tod_inducer_on` [VERIFIED] (src: repo zone_source/zm_tod2_cybercity.zone:353; zone line numbers drift as the file is edited, so search for the line). For Tower II, our own sources live in **repo** `share/raw/fx/...` and `tools/sync_to_modtools.ps1` copies them into the resolved Mod Tools root's `share/raw/fx` on every build [VERIFIED] (src: repo tools/sync_to_modtools.ps1:174-179); for Tower II that root is the private workspace `C:\BO3Tools\TOD2Cybercity` (repo docs/154_tod2_isolation.md). So new effect sources are written in the repo and reach the private tree through the sync; nothing is ever written into the shared Steam tools tree (repo docs/154_tod2_isolation.md).

**Visual types in the local library** (scan of 6,775 `.efx`): `billboardSprite` about 27,400, `line` about 7,200, `tail` about 3,400, `dynamicLight2` about 3,200, `rotatedSprite` about 1,700, `model`, `cloud`, `runner`, `lensFlare` about 700, `decal`, `orientedSprite`, `trail`, and 7 legacy `dynamicLight` blocks [VERIFIED] (count from a parse of share/raw/fx). A parser or tool that reads lights must accept both `dynamicLight2` and the legacy `dynamicLight` [VERIFIED]. Author new lights as `dynamicLight2` [INFERRED] (that is what Treyarch-authored files use). Note that `light` also appears as a bare word inside some `dynamicLight2` blocks; there it is the template name, not a visual type [VERIFIED] (e.g. share/raw/fx/animals/fx_bio_raven_dni_rez_in_dirty.efx).

### Effect-level header

The top of the stock lantern effect [VERIFIED] (src: share/raw/fx/light/fx_light_lantern_factory_zmb.efx):

```
iwfx 3
	efFlags efUseBoundingBox efLocalBoundingBox efSpawnCullBoundingBox efPortalledBoundingBox;
	efPriority 100;
	efBoundingBoxMin -50 -50 -50;
	efBoundingBoxMax 50 50 60;
	occlusionQueryDepthBias 0;
	occlusionQueryFadeIn 0; occlusionQueryFadeOut 0; occlusionQueryScaleRange 1 0;
	lodDefault0 0 0; ... lodDefault3 0 0;
```

The `occlusionQuery*` fields probably tune how flares and glows fade when something blocks them [INFERRED] (from the names). The bounding box is used for culling the whole effect [INFERRED] (from the flag names). Make it cover the light's radius, or the effect may be culled while its light still reaches the screen [INFERRED] [TEST].

### Element fields that matter for a light

| Field | Example | Meaning |
|---|---|---|
| `name` | `"light_small"` (our perk glow), `"0_exp_light"` (the lantern) | Element name shown in FX Outline |
| `editorFlags` | `looping useRandIntensity useBackCompatVel absVel1` | `looping` = re-spawn forever. `useRand<X>` lets each particle pick between the two curves of graph X [INFERRED] (from names and stock use) |
| `flags` | `spawnRelative spawnFrustumCull spawnOffsetNone runRelToEffect` | Spawn and cull behaviour. `spawnFrustumCull` probably skips spawning while the effect is off-screen [INFERRED] |
| `spawnFrustumCullRadius` | `1000` (lantern), `100` (our perk glow) | Radius used by that frustum test [INFERRED] |
| `spawnRange` | `0 3000` | Min/max viewer distance for spawning; `0 0` = no limit [INFERRED] (from name and stock values) |
| `spawnLooping` | `1000 0` | **Interval** in ms between spawns (+ random) when looping. The FX_Lights doc calls it "Interval" [VERIFIED] |
| `spawnLoopingSpawnCount` | `1 0` | Particles per interval |
| `spawnOneShot` | `1 0` | Particle count for a one-shot element |
| `lifeSpanMsec` | `1000 0` | **Lifetime** min (+ random). The doc calls it "Lifetime min and max" [VERIFIED] |
| `spawnDelayMsec` | `0 0` | Delay before the first spawn (+ random) |
| `spawnOrgX/Y/Z` | `0 0`, `40 0` | Offset from the host point. The doc's "Generation -> Origin" [VERIFIED] |
| `spawnAnglePitch/Yaw/Roll` | | Aim of a spot. The doc's "Movement -> Rotation Geometry" [VERIFIED] |
| `colorGraph` | `1 { {0 r g b  1 r g b} {…} }` | Light colour over life |
| `lightIntensityGraph` | `60 { {…} {…} }` | Intensity = base × curve(t) |
| `lightRadiusGraph` | `208 { {…} {…} }` | Radius in world units × curve(t) |
| `lightFovGraph` | `100 { … }` | Spot cone angle in degrees × curve(t) |
| `spotLightFovInnerFraction`, `spotLightStartRadius`, `spotLightEndRadius` | `0.5`, `36`, `196` | Spot shaping values present in every element [VERIFIED] present; meaning [INFERRED] |
| `dynamicLight2 { <template> { KVPs } }` | | The light itself |

**Graph syntax.** `key <base> { { t v  t v … } { t v … } };` Each graph has two curves. `t` runs from 0 (birth) to 1 (death) over the particle's life. Colour rows are `t r g b`. The value used is base × curve [INFERRED] (from stock files, for example flat-1 curves with a meaningful base). The lantern's intensity graph, trimmed:

```
lightIntensityGraph 60
{
	{ 0 1   0.132919 0.78656   0.210125 0.702803   ...   0.792111 0.570934   1 1 }
	{ 0 1   0.407494 0.366025   0.495182 0.286025   0.593187 0.370544   1 1 }
};
lightRadiusGraph 208 { { 0 1  1 1 } { 0 1  1 1 } };
```

### The `dynamicLight2` settings block

It holds a full Radiant light key set, for example from the lantern [VERIFIED] (src: share/raw/fx/light/fx_light_lantern_factory_zmb.efx; keys reordered and trimmed; the `//` comments are this chapter's notes: the shadow ones follow FX_Lights.pdf p.2, the "NOT the live" ones are [INFERRED], see [section 3](#3-curves-not-the-settings-block-set-brightness-size-and-colour)):

```
dynamicLight2
{
	zm_factory_lantern                    // the Lighting Description template it was filled from
	{
		PRIMARY_TYPE PRIMARY_OMNI
		PRIMARY_NOSHADOWMAP 0             // 0 = casts a shadow (live every frame for FX lights)
		shadowUpdate Never                // not honoured for FX lights (section 7)
		shadowmapScale 0.5
		_color 1 0.4588 0.1607            // NOT the live colour (section 3)
		radius 125                        // NOT the live radius
		stops 11                          // NOT the live brightness
		def white_light
		volumetric 0
		lightingstate1 1 ... lightingstate4 1
		...
	};
};
```

Keys you will meet inside it that the Radiant light definition lists, with its ranges: `PRIMARY_TYPE` (`PRIMARY_OMNI` or `PRIMARY_SPOT`), `PRIMARY_NOSHADOWMAP`, `shadowUpdate` (`AlwaysNoCache`, `Always`, `Never`), `shadowmapScale` (`4`, `2`, `1`, `0.5`), `volumetric`, `volumetricSampleCount` (1–24, default 8), `volumetricIntensityBoost` (stops, −14..14), `volumetricCookies`, `def` (cookie), `def_*`, `cut_on`, `near_edge`, `far_edge`, `falloffdistance`, `ENABLE_FALLOFF`, `fov_outer`, `roundness`, `superellipse`, `culling_cutoff`, `culling_falloff`, `spec_comp`, `ortho_effect`, `PROBE_ONLY`, `NO_CULL`, `lightingstate1..4` [VERIFIED] (key list and ranges) (src: bin/t7.def.json, `light` class). Their meanings are covered in [01](01_lights.md).

Stock blocks also carry keys that the definition does **not** list. The lantern's block has `exploderDisabled`, `pcss_max`, `pcss_min`, `dirSpan` and the entity keys `classname light`, `origin`, `angles`, `name` [VERIFIED] (src: share/raw/fx/light/fx_light_lantern_factory_zmb.efx). It looks like a copied Radiant light entity [INFERRED]. `pcss_*` does nothing today: "PCSS is currently disabled due to performance constraints" [VERIFIED] (src: docs_modtools/Lighting_Parameters.pdf). Wraith-reconstructed files (see [section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)) write `PRIMARY_TYPE OMNI` or `SPOT` instead of the definition's `PRIMARY_OMNI` / `PRIMARY_SPOT`, and usually have no `def` line [VERIFIED] (e.g. share/raw/fx/zombie/fx_perk_juggernaut_factory_zmb.efx). Such files link in this map (for example `tod/fx_tod_elec_impact_sm`), but whether the engine reads the short spelling as the intended light type is [TEST]. When you write a light by hand, use the definition's spelling [INFERRED].

**The template name** (`zm_factory_lantern`, `gfx_dlight_gen_omni_r200`, `New`) is the Lighting Description chosen from a dropdown "if you want to populate KVPs from a template" [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1 step 5). Once the keys are written into the file, the name is probably only a label [INFERRED].

---

## 3. Curves, not the settings block, set brightness, size and colour

**Plain version.** The settings block inside an FX light looks like a full Radiant light, but Treyarch's FX-light page says brightness, radius and cone angle are set in the effect's Colour section and its curves, not in the block [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1). Stock files agree (see the table below). So if you edit `stops` or `radius` in the block and nothing changes in game, that is the likely reason [INFERRED].

**What the doc says.** Step 6: "some parameters are NOT read from the Visuals KVPs, they are overridden by other parameters. The main options controlled here are: LIGHT TYPE; SHAPING (except Radius and FOV)." Step 7: "In Visuals -> Color section: edit Intensity, Radius, FOV. In the 'FX Graph' -> Color: select a knot on the curves, RMB -> Set color for knot (both knots)." [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1). Note the word is "main", not "only". The doc never says whether `stops` in the block is read at all.

**What the data shows** [VERIFIED] values; that the block values are ignored is [INFERRED]:

| Effect | Settings block | Curves (live values) |
|---|---|---|
| Stock lantern `light/fx_light_lantern_factory_zmb` | `stops 11`, `radius 125`, `_color 1 0.4588 0.1607` | intensity 60, radius 208, colour 1 0.5585 0.3176 |
| Our perk glow `acc/light/fx_perk_glow_amber` (repo) | `stops 11`, `radius 100`, `_color 1.8 1.116 0.396` | intensity 512, radius 60, colour 0.459 0.284 0.101 |
| Stock `zombie/fx_perk_juggernaut_factory_zmb` (a Wraith reconstruction, so its block may not be Treyarch's own) | seven spot lights, all `stops 11`; `radius` 50 or 100; `fov_outer` 60–130 | intensities 8–128; radii 40–140; FOV 28–115 |
| Stock Giant fire `light/fx_light_zm_fire_omni_13` | `stops 11` | intensity 251, which matches its Radiant twin's `stops 7.97` (2^7.97 ≈ 251), not the block |

Our own generator treats the curves as the live values: `tools/gen_tod_inducer_fx.py` retints only `colorGraph` and rewrites only `lightIntensityGraph`, and the inducer's colour and brightness changed in game (user-approved) [VERIFIED] code; the in-game change is a project observation [COMMUNITY] (src: repo tools/gen_tod_inducer_fx.py; repo CLAUDE.md v18.99k).

**What the settings block still controls** [VERIFIED] for type and shaping per the doc's step 6; which individual shaping keys are honoured is [INFERRED]: omni or spot (`PRIMARY_TYPE`), shadow on/off (`PRIMARY_NOSHADOWMAP`), shaping such as `roundness`, `superellipse`, edges and falloff, the cookie (`def`), and the volumetric switches.

---

## 4. Units: how bright is "intensity 512"?

**Plain version.** A Radiant light's `stops` is a logarithmic brightness: each +1 stop doubles the light ([01](01_lights.md#5-brightness-stops)). An FX light's intensity is a plain number. Treyarch's own data suggests the two line up as intensity ≈ 2^stops [INFERRED] (evidence below). So `stops 6` ≈ intensity 64, `stops 9` = 512, `stops 10.55` ≈ 1500.

**Evidence.** Treyarch's Giant places many fire FX lights exactly on top of a Radiant light. For 30 of the 38 per-placement `fx_light_zm_fire_*` effects (37 under `light/`, one under `dlc0/light/`), the FX intensity equals 2^stops of the `PROBE_ONLY` Radiant light at the same spot and the radii match (31 of 38 if any light at the spot counts), for example `fx_light_zm_fire_omni_1` intensity 63, radius 100 against a light with `stops 5.97` (2^5.97 ≈ 62.7), radius 100, and `fx_light_zm_fire_spot_4` intensity 251 against `stops 7.966` (≈ 250). The ceiling fire follows the same habit: `fx_light_ceiling_fire_factory_zmb` intensity 1500 against `stops 10.551` (2^10.551 ≈ 1500) [VERIFIED] arithmetic on stock data; that the units are equivalent is [INFERRED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map; share/raw/fx/light/fx_light_zm_fire_*.efx). Radiant even stores values like `stops 6.64385618977473`, which is log2(100) [VERIFIED]. Seven placements match no light at their spot ([section 11](#11-the-giant-pattern-fx-light-plus-a-probe_only-twin) lists them), so this is a strong authoring habit, not a law.

**Typical values.** Across about 3,000 FX-light elements in stock-named folders, the intensity bases run (10th to 90th percentile) 8 / 23 / 64 / 128 / **256 (median)** / 724 / 1024 / 2048 / 10000; radius median 100, 90th percentile 350 [VERIFIED] (count from a parse of share/raw/fx).

**Same scale as glowing sprites.** The Effect Lit Emissive material's Intensity (0–12,000) "is the same value that lights use to determine how bright they are": "Light glows are set at 16. Fires are set at 256. The sun would have a value of 10,000." [VERIFIED] (src: docs_modtools/Materials.pdf, Effect Lit Emissive section). Stock material names like `gfx_light_ray_cone_em_i2048` and `gfx_light_incandescent_hot_em_i128` appear to encode that value [INFERRED] (from naming).

**Radius** is in world units; "1in = 1unit" [VERIFIED] (src: docs_modtools/Scale_Standards.pdf p.1). **Colour** in the curves is a 0–1 RGB triple [VERIFIED] (format); whether values above 1 are honoured in the curve is untested [TEST].

**Our numbers in stops terms** [INFERRED] (arithmetic): map lights `stops 6` ≈ 64 ([01](01_lights.md)); perk glow 512 ≈ 9 stops; inducer idle 120 ≈ 6.9 stops; inducer ON 1500 ≈ 10.55 stops at the top of its pulse.

---

## 5. The looping rule, and why it matters

**Plain version.** A looping FX light is not one light. It is a chain of short-lived lights, spawned one after another. If each one lives exactly as long as the gap between spawns, there is always exactly one light. If each lives longer than the gap, several overlap and their light adds up. If each lives shorter, there are dark moments between them.

**The official rule:** "Set Lifetime min and max, and Interval. In most cases, they will all be the same. If Interval is lower than the min, it will spawn extra particles, and the light may build up too bright at the end of its life. If it is higher than the max, you may get it randomly going black. [if your light is a One Shot, the Interval only matters for test purposes]" [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1, "Set up animation" step 3).

**What stock files do.** About 78% (1,489 of about 1,906) of the looping FX lights in the local library's stock-named folders have interval equal to lifetime [VERIFIED] (count from a parse of share/raw/fx). Typical pairs: 1000/1000 (lantern, yellow flicker), 600/600 (barrel fire, window fire), 300/300 (small fire flicker), 1500/1500 (Giant Pack-a-Punch key light) [VERIFIED].

**Deliberate exceptions exist, and they are useful:**

| Effect | Interval / life | What it achieves [INFERRED] (from the numbers) |
|---|---|---|
| `light/fx_light_flashing_red_factory_zmb` | 1000 / 500 | On half a second, off half a second: a blink |
| `light/fx_sgen_emergency_whiteflash` | 1000 / 100–200, second light delayed 160 ms | A double strobe each second |
| `light/fx_light_flickering_hat_light_sodium` | 5000 / 1000, first spawn delayed 0–3900 ms at random | Mostly dark, an occasional one-second flicker |

So "interval higher than life" is how you make a blink on purpose. "Interval lower than life" has no stock use that we can point to as a style, and the doc warns against it.

**Why it matters for us: overlap arithmetic.** Our perk glows and the Rampage Inducer spawn a light every 200 ms and let each live 1000 ms, so about five copies are alive at once [VERIFIED] (values) (src: repo share/raw/fx/acc/light/fx_perk_glow_*.efx and share/raw/fx/tod/fx_tod_inducer_*.efx; all 17 `fx_perk_glow_*` in the tools tree share it). For the inducer's ON curve, a single hump 0.3 → 1.0 → 0.3 per life, five copies offset by 0.2 of a life sum to between 3.18× and 3.32× the base, which is nearly flat around ~3.25× [INFERRED] (arithmetic, assuming overlapping FX lights add). That predicts a steady light of roughly 4,800 rather than a 450 ↔ 1,500 pulse. The perk glow's two-hump curve stacks the same way, to a near-steady 1.6–2.3× its 512 base [INFERRED] (same arithmetic; the range comes from its two random curves). The user played and approved the inducer's look (repo CLAUDE.md v18.99k), so this is a prediction to A/B, not a known bug [TEST].

**Where the 200/1000 came from.** The perk-glow file has the same four elements (`exp`, `glow`, `glow_spikes`, `light_small`) and the identical intensity curve as the stock powerup glow `zombie/fx_powerup_on_green_zmb`, whose `light_small` is **200 / 200** (compliant) and whose sprites live 120–250 ms [VERIFIED] (values) (src: share/raw/fx/zombie/fx_powerup_on_green_zmb.efx; repo share/raw/fx/acc/light/fx_perk_glow_amber.efx). The perk glow's lifetimes are about five times longer (light 1000, sprites 600–1250) while its intervals stayed at 200 / 30 / 40 ms, and its elements sit 40 units higher [VERIFIED]. It looks like the perk glow was made from the powerup glow by stretching lifetimes without stretching intervals [INFERRED]. The inducer then inherited it from the perk glow (repo tools/gen_tod_inducer_fx.py docstring names the donor). The same stretch raises the sprite count per effect about five-fold too [INFERRED].

---

## 6. Flicker, pulse and blink

The animation lives in the curves. No script timer is needed, which is also why our inducer's pulse is in the effect, not in GSC (repo scripts/zm/zm_tod2_cybercity/_tod_rampage.gsc `glow_set` comment).

**Curve shapes seen in stock files** [VERIFIED] shapes; the visual result is not documented:

| Look | Curve | Example |
|---|---|---|
| Wobbling flame or lantern | Many knots between ~0.3 and 1.0; the second curve different, with `useRandIntensity` on so cycles do not repeat exactly [INFERRED] (purpose) | `light/fx_light_lantern_factory_zmb` (1000/1000) |
| Failing tube, brief blackouts | Knots that drop to 0 for tens of ms | `light/fx_light_yellow_flicker` |
| Steady lamp | Flat 1 → 1 | repo `fx_tod_inducer_idle` |
| Slow pulse | One hump 0.3 → 1 → 0.3 per life, with interval = life | repo `fx_tod_inducer_on` (but see the overlap note above) |
| Blink or strobe | Short life, longer interval | `light/fx_light_flashing_red_factory_zmb` |

**De-sync identical lamps.** A Radiant `fx` entity has `delay` ("Time to delay before playing. Can be a negative number", an integer from −600,000 to 600,000) and `timescale` ("Time scale applied to this fx instance", default 1) [VERIFIED] (src: bin/t7.def.json `fx` class). The definition gives no unit; milliseconds is likely, since FX timings are in ms [INFERRED]. The Giant gives 94 of its 96 fx entities a negative delay, spread from −1,000 to −29,962 [VERIFIED] (data) (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map). The likely purpose is that neighbouring lamps do not flicker in step [INFERRED]. For script-played effects there is no per-instance delay key; stagger the play calls instead [INFERRED].

**Omni versus spot flicker.** One forum user reported they could flicker a spot but not an omni (forum.modme.co thread 3170, unanswered) [COMMUNITY]. Stock files contain flickering omni FX lights (`light/fx_light_fire_flicker_noshad_small`, the lantern), so the data supports omni flicker [VERIFIED] data; in-game behaviour [TEST].

**Other ways to animate light** (for comparison; each belongs to another chapter):

| Method | Notes | Chapter |
|---|---|---|
| FX light curves | Official route; client-rendered; no script | this chapter |
| Exploder on/off from script | Good for state changes (power, red → green) | [section 8](#8-radiant-fx-entities-and-exploders), [02](02_power_and_states.md#9-exploders-named-light-groups) |
| Script-controlled Radiant light (`SetLightIntensity`, `SetLightColor`) | Needs a scriptable, ServerSide light; cannot exceed the compiled radius | [01](01_lights.md#16-script-control-of-a-light) |
| Scrolling light cookie | Community flicker trick; cookie packing in usermaps is unproven | [01](01_lights.md) |
| Material flicker (`lit_emissive_scroll*`) | Changes how a surface glows, lights nothing | [03](03_glow_and_perks.md) |

---

## 7. Shadows on FX lights

**Plain version.** A normal Radiant light can draw its shadow once and reuse it. An FX light cannot. Its shadow is either redrawn every frame or not drawn at all, and there is a small budget for shadows redrawn every frame.

- "FX lights do not have the ability to use 'Never' shadows. They are either Always live, or Off. This will blow your shadow budget very quickly." [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.2, Known issues 1)
- **How stock turns them off:** `PRIMARY_NOSHADOWMAP 1` ("Prevents a primary light from ever having a shadowmap") is set on about 88% (2,629 of 2,983) of the stock-named FX lights [VERIFIED] (count; key text from bin/t7.def.json). Most stock blocks also literally say `shadowUpdate Never` (2,582 of 2,983), which the doc says FX lights cannot use, so that key is not what switches the shadow off [INFERRED]. The stock lantern has `PRIMARY_NOSHADOWMAP 0` with `shadowUpdate Never`, so by the doc it casts a live shadow [INFERRED].
- **The budget:** "At normal res we can update 12 live shadows, with double res you could update 3 live shadows. Conversely you could do 4x as many shadows at half-scale. Shadowmap Scale is not currently supported on omni-lights." [VERIFIED] (src: docs_modtools/Lighting_Parameters.pdf, ShadowmapScale)
- **Atlas size:** worldspawn keys `numOmniShadowSlices` (default 24, range 8–256) and `numSpotShadowSlices` (default 64, range 8–1024) [VERIFIED] (src: bin/t7.def.json worldspawn). The Giant's main map raises omni slices to 96 [VERIFIED] (src: map_source/zm/zm_giant.map); it has dozens of shadowed omni fire and lantern FX. Tower II uses 24 / 64 [VERIFIED] (src: repo map_source/zm/zm_tod2_cybercity.map). What these slices mean for how many live shadows can run at once is not documented [INFERRED].
- **Over budget:** Radiant's binary contains "Too many shadowing %s lights. Shadow for light at %.2f %.2f %.2f is being dropped" [VERIFIED] (string). That the game behaves the same is [INFERRED].
- **Players may never see them.** The user's own graphics config has `DisableDynamicLightShadows 1` (and `DisableDynamicSunShadows 1`), so live FX-light shadows will not show in the user's playtests [VERIFIED] config value; its effect on FX lights [INFERRED]. Judge on a high config too ([09](09_design_and_inspiration.md)).

**Rule of thumb:** `PRIMARY_NOSHADOWMAP 1` on every FX light unless the shadow is the point of the fixture (one hero lamp, one swinging bulb), and never many shadowed FX lights in view together [INFERRED] (from the doc's warning).

---

## 8. Radiant fx entities and exploders

**Plain version.** You can place an effect in Radiant like any other entity. It then plays by itself when the map loads, with no script. You can also group placed effects and lights into a named **exploder**, which script turns on and off by name. None of the user's three maps places either: their `.map` files have zero `fx` entities and zero exploder members [VERIFIED] (src: repo map_source/zm/zm_tod2_cybercity.map; tower_of_doom_cybercity and abandoned_cyber_city_zombies map_source/zm/*.map). (Map One carries a vendored stock `zm_zod_robot.csc` that calls exploder names no entity in that map carries.) The Giant uses both.

### The `fx` entity

Place one by dragging from the FX Browser (View > Toggle > FX Browser; type words with spaces instead of underscores) [VERIFIED] (src: docs_modtools/FX_QuickStart.pdf). Keys [VERIFIED] (src: bin/t7.def.json `fx` class):

| Key | Type / default | Meaning |
|---|---|---|
| `fxdef` | string | "Specify which fx file to play" (path without `.efx`) |
| `origin`, `angles` | vec3 | Position and aim |
| `delay` | int, 0, −600000..600000 (unit not stated; ms [INFERRED]) | "Time to delay before playing. Can be a negative number." |
| `timescale` | float, 1 | "Time scale applied to this fx instance." |
| `fxstate1`..`fxstate4` | bool, all true | Which lighting states it plays in [INFERRED] (from the name, the doc's "Lighting State" per-instance note and Giant usage) |
| `primaryLightFraction` | float 0–1, 1 | No description in the def; The Giant leaves it at 1 on all 96 [VERIFIED] data; meaning unknown |
| `lightingOriginOffset` | vec3, 0 0 0 | No description; meaning unknown |
| `outdoor` | bool, false | No description; the client API's `SetFXOutdoor` "Flag[s] the FX as one that only plays outdoors" [VERIFIED] API text; that the key does the same is [INFERRED] |
| `SCRIPTABLE` | bool, false | No description |
| `exploder_count`, `exploder_index_0`..`_31` | hidden | Exploder membership, written by the Exploder Manager |

"The fx entities are instanced, from the EFX file. You can't override anything - you will have to save as a new effect. The only things you can change per-instance are whats in the Entity Info KVPs. (only individual Origin and Angles, and Lighting State)" [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.2, Known issues 2). So a brighter copy of a lamp needs its own `.efx` (that is why our perk glows are one file per colour).

**Lighting states on fx entities.** The Giant switches its Pack-a-Punch key light with power using `fxstate` alone: `light/fx_light_pap_key` (intensity 100) is placed with only `fxstate2` on, and `light/fx_light_pap_key_on` (intensity 512) at the same spot with only `fxstate1` on [VERIFIED] (data) (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map, entities 824–825). The Giant boots in script state 1, which shows Radiant State 2, the state its prefab aliases "power_off"; at power it calls `set_lighting_state( 0 )`, which shows Radiant State 1 (the script-n → Radiant n+1 mapping is [INFERRED], strongly supported; see [02](02_power_and_states.md#2-radiant-state-n-and-script-state-n)). So this is a no-script stock pattern for "FX light dim before power, bright after" [VERIFIED] data; runtime behaviour [INFERRED]. 91 of The Giant's 96 fx entities are simply on in all four states; the other five are `1000`, `0100`, `0011` (two) and `0000` [VERIFIED].

**For Tower II today:** the map boots in script state 1 (Radiant State 2) and no Tower II script changes it ([02](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis)) [INFERRED] (the state mapping). An fx entity left at the default (all states on) would play all match; one marked `fxstate1` only would never play [INFERRED].

**Does a placed fx entity need a zone line?** The linker might pack effects named by the map; community guides say to add the `fx,` line anyway. Not verified either way [COMMUNITY] [TEST].

### Exploders

**Plain version.** An exploder is a named group of placed effects and lights. The name is what script uses to switch the group on and off.

**How to make one** [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1): open the Exploder Manager; with the FX light selected, RMB → "Create New Exploder from selection"; test with Play Exploder; "'Stop Exploder' will stop playback, but leave the time where it is. Kill will reset to the start." After an exploder change, a Lighting Export with only "Export Local Probes" checked is enough to see it, and much faster than a full export, as long as the reflection probes do not need updating [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf, Lighting Export). This repo's build script has no such partial export; any `.map` change here is a full build ([10](10_troubleshooting_limits_history.md#41-which-build-does-a-change-need)).

**What goes in:** Radiant warns "only primary lights can be added to exploders", so among lights only primary omni/spot lights qualify; `fx` entities and even reflection probes also carry membership in stock prefabs (127 fx entities, 87 lights, 2 probes) [VERIFIED] (data and string). The Exploder Manager shows "Total Exploders: 0/120", which suggests a cap of 120 exploders [INFERRED].

**How membership is stored** [VERIFIED] format; field meanings [INFERRED]: `"exploder_count" "1"` plus `"exploder_index_0" "ver=2 don=0 doff=0 fin=0 fout=0 off=0 name=<name>"` (older form `"0 0 <name>"`, as on the Giant's `map_lgt_pap_flash` fx entities). Lights that should start off also carry `exploderDisabled 1`. The fields are probably delay-on, delay-off, fade-in, fade-out and "starts off" [INFERRED]. Copy the exact keys from a stock example rather than guessing them ([02](02_power_and_states.md#93-membership-keys) has the Giant's exploder-light key patterns). Note that `exploderDisabled` and `exploderFade` appear on stock lights but are not in bin/t7.def.json's `light` class [VERIFIED], so Radiant's property panel may not show them [INFERRED].

**Script calls** [VERIFIED] (src: share/raw/scripts/shared/exploder_shared.gsc, exploder_shared.csc; docs_modtools/bo3_scriptapifunctions.htm):

| Side | Call | What it does |
|---|---|---|
| Server | `exploder::exploder( "name" )` | A string id routes to `activate_radiant_exploder` → `level notify( "exploder" + name )` + `ActivateClientRadiantExploder( name )` (gsc:275-285, 663-668) |
| Server | `exploder::stop_exploder( "name" )` | Reaches `DeactivateClientRadiantExploder` only `if ( level.clientScripts )` (gsc:762-790) |
| Server | `exploder::kill_exploder( "name" )` | `KillClientRadiantExploder`; asserts on non-string ids (gsc:810-819) |
| Client | `exploder::exploder( name, [lcn] )`, `stop_exploder`, `kill_exploder` | `PlayRadiantExploder` / `StopRadiantExploder` / `KillRadiantExploder` for each local client (csc:297-420) |

`level.clientScripts` is set from `GetDvarString( "cg_usingClientScripts" ) != ""` (src: share/raw/scripts/shared/load_shared.gsc:55,60, spelled `level.clientscripts` there; GSC names are case-insensitive [INFERRED]) [VERIFIED]. Whether that dvar is set in a usermap run is untested, so a server-side stop could be a silent no-op [TEST]. For a group that must reliably turn off, stop it from client script [INFERRED]. (The API's summary text for `KillClientRadiantExploder` is a copy of `DeactivateClientRadiantExploder`'s, so do not read a difference into it [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm).)

**Late joiners.** Stock electric traps do not call exploders directly from the server. They register a `world` clientfield in both VMs and play or stop the exploder in the CSC callback (src: share/raw/scripts/zm/_zm_trap_electric.csc:20-37) [VERIFIED]. Clientfields registered without `CF_CALLBACK_ZERO_ON_NEW_ENT` replay their value on a joining client's first snapshot, so the lights come back for a hot-joiner [INFERRED]. Whether a Radiant exploder activated before a client connected replays for that client is untested [TEST].

---

## 9. Playing FX from script

### Two lines are needed for any scripted effect

1. A zone line in `zone_source/<map>.zone`: `fx,<path>` (no `.efx`).
2. A precache in the script that plays it: `#precache( "fx", "<path>" );` in GSC, `#precache( "client_fx", "<path>" );` in CSC (stock: share/raw/scripts/zm/zm_giant_fx.csc:9-28) [VERIFIED] (syntax).

The zone requirement is a community recipe (forum.modme.co threads 1241, 3644; ugx-mods.com thread 13761), not in any Treyarch doc [COMMUNITY]. This project records that a precache without the zone line made `PlayFX` do nothing with no error (repo scripts/zm/zm_tod2_cybercity/_tod_rampage.gsc:96-101 and 180-183, comments; the lesson dates from the TOD1 rampage spark) [COMMUNITY] (project record). The zone line is needed for effects the base game does not already load; an effect the map never zones can still render from base-game zones (project memory, `zombie/fx_fire_torso_zmb`) [COMMUNITY] (project record). Child effects that an `.efx` names are packed by the linker along with their zoned parent ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)).

**Which build?** A script-played `.efx` made from materials that already exist, plus its zone and precache lines, only needs the linker, which a `-GscOnly` build also runs (project practice) [COMMUNITY]. Anything placed in the `.map` (fx entities, exploder members, `PROBE_ONLY` twins) and anything that adds a GDT (new images or materials) is a full build ([10](10_troubleshooting_limits_history.md#41-which-build-does-a-change-need)).

### The four ways an effect gets played

| Lane | How | Who renders it | How to stop it | Status here |
|---|---|---|---|---|
| A. Radiant `fx` entity | Placed in the map ([section 8](#8-radiant-fx-entities-and-exploders)) | Automatic | Lighting state or exploder | None placed in the user's maps |
| B. Radiant exploder | Named group, played from script | `ActivateClientRadiantExploder` → clients | `stop_exploder` / `kill_exploder` | None authored in the user's maps |
| C. Server script | `PlayFX( fx, origin, [fwd], [up], [ignorePause] )`, `PlayFXOnTag( fx, ent, tag, [ignorePause] )`, `PlayLoopedFX( fx, repeat, origin, [cullDist], [fwd], [up] )`, `SpawnFX` + `TriggerFX( ent, [delay] )` — all Server [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm) | Server sends it to clients | For a tag FX, delete the host entity (our pattern). The API lists these calls as returning an entity; whether deleting that stops a `PlayFX` loop is untested [TEST] | Used (inducer, teleporter, lounges) |
| D. Client script (CSC) | `self.fx = PlayFXOnTag( localClientNum, fx, self, "tag_origin" )` after `self util::waittill_dobj( localClientNum )`; `PlayFX( localClientNum, fx, origin, [fwd] )` (stock: `_zm_perk_random.csc:84`) | Each client | `StopFX( lcn, id )` "Stops a given fx"; `KillFX( lcn, id )` "Force kills a given fx" [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm) | Used (perk glow) |

Related client calls [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm): `SetFXIgnorePause( lcn, fxId, 1 )` ("whether or not to respect a paused world state"), `SetFXOutdoor( lcn, fxId )` ("only plays outdoors"). Server: `<entity> SetForceNoCull()` ("Entity will not be culled by portals"); stock `fx::play()` calls it on its host when `b_no_cull` is set (src: share/raw/scripts/shared/fx_shared.gsc:91-133) [VERIFIED].

**The stock helper** `fx::play( str_fx, v_origin, v_angles, time_to_delete_or_notify, b_link_to_self, str_tag, b_no_cull, b_ignore_pause_world )` has three paths: linked to `self` with a tag and no lifetime, it plays `PlayFXOnTag` on `self`'s tag; with a lifetime, it spawns a `tag_origin` model, `PlayFXOnTag`s on it in the same frame, and deletes it later; otherwise it plays a bare `PlayFX` [VERIFIED] (src: share/raw/scripts/shared/fx_shared.gsc:91-133).

### "A server one-shot PlayFX renders nothing": what we actually know

This project's notes say a one-shot effect played by server `PlayFX` renders nothing, and only looping server effects or effects on a host entity render (repo CLAUDE.md v18.99i; repo tools/gen_tod_inducer_fx.py docstring; repo `_tod_perk_lights.gsc` header). Treat that as a **project heuristic, not an engine rule**:

- The engine API documents server `PlayFX` with no rendering caveat, and stock zombies scripts call it at 72 live sites across 25 files, mostly for one-shots (gibs, board breaks, `switch_sparks` at zm_giant.gsc:582) [VERIFIED] (src: share/raw/scripts/zm/*.gsc).
- Stock plays the perk-machine aura with a **server** `playfxontag` (src: share/raw/scripts/zm/_zm_perks.gsc:280-315) [VERIFIED].
- Map One's evidence is an uncontrolled before/after: its teleporter change from bare `PlayFX` to `PlayFXOnTag` on a host also raised the effect from +6 to +40 units because it was "hidden at floor level inside the sunken assembly" [COMMUNITY] (project record) (src: abandoned_cyber_city_zombies/docs/44_scientist_boss_and_teleport_fx.md). The pre-fix code is not in that repo's history. If the effect names stayed the same, a missing zone line or a placeholder source is unlikely for that case, which leaves the height change as the documented confound [INFERRED].
- The "same-frame host spawn" worry (repo docs/143) is about effects played on a freshly spawned host, not about bare `PlayFX` at a point, so it does not explain that result either [INFERRED].

**Proven-safe lanes in this project** [COMMUNITY] (project record):

1. **Looping effect, server `PlayFX` at a fixed point.** Map One placed about 40 ambient loops this way; our lounge haze/fog/vent use it (repo `_tod_atmosphere.gsc` `lounge_fx_at`).
2. **Server `PlayFXOnTag` on a spawned `tag_origin` host, two server frames after spawning it.** Our teleporter `fx_burst` waits `WAIT_SERVER_FRAME` twice "to replicate before its one-shot FX event" (repo scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc:545-586); docs/143 calls this "timing hardening, not proof of client delivery". The inducer uses a host without the wait and was approved in game (repo `_tod_rampage.gsc:347` `glow_set`). Stock `fx::play` also emits in the same frame, so the two project records disagree on whether the wait is needed [INFERRED].
3. **Clientfield → CSC `PlayFXOnTag`.** Our perk glow; replays for late joiners (repo `_tod_perk_lights.csc:54`, registered `!CF_CALLBACK_ZERO_ON_NEW_ENT`).

To settle the heuristic, run one build with the same real, zoned one-shot effect played three ways at the same point (bare server `PlayFX`, host `PlayFXOnTag` after two frames, CSC `PlayFX`), with a dev log on each [TEST].

**Stopping.** The server API has no `StopFX`; to remove a server tag effect, delete its host entity (repo `_tod_rampage.gsc` `glow_set` and `spark_fx_stop`). On the client, `StopFX` stops spawning and lets live particles finish; `KillFX` removes them at once [VERIFIED] API text; the "particles finish" detail is [INFERRED] from the two summaries.

---

## 10. FX lights and power-on

**Plain version.** FX lights only exist where something plays them, so "turn on with power" and "turn on floor by floor" are just a question of when you play each one. This is easier than switching baked lights, which move together with the map's lighting state ([02](02_power_and_states.md)).

**How The Giant does it** [VERIFIED] (src: share/raw/scripts/zm/zm_giant.gsc:428,571; zm_giant_fx.csc:69-71, 184-198, 227-240):

1. Server: `level flag::wait_till( "power_on" ); level util::clientnotify( "pl1" );` and, at the switch, `level util::set_lighting_state( 0 );`.
2. Client, on `pl1`: swaps lamp script models to their lit `_on` models (`light_model_swap( "smodel_light_electric", "lights_indlight_on" )` and two more). No entity with those targetnames or models exists anywhere in the shipped map sources, so in the files we have this is code with nothing to act on: treat it as a pattern, not a proven effect [VERIFIED absence].
3. Client: plays area exploders such as `map_lgt_<pad>_red`, later stops red and starts green (zm_giant_fx.csc:231-237). Each `map_lgt_a/b/c/pap_red` and `_green` exploder holds three primary lights; the three flashing `light/fx_light_flashing_red_factory_zmb` fx entities sit in a separate exploder, `map_lgt_pap_flash`, which the Pack-a-Punch code swaps with `map_lgt_pap_red` (zm_giant_fx.csc:254-292) [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map).
4. Traps: a `world` clientfield per trap; the CSC callback plays or stops `trap_electric_<name>`.
5. Pack-a-Punch key light: swapped by `fxstate` with the lighting state ([section 8](#8-radiant-fx-entities-and-exploders)).

**Stock perk machines** are covered in [03](03_glow_and_perks.md#9-perk-machine-glow-stock-and-ours) and [02](02_power_and_states.md#13-how-stock-perk-machines-power-on). The FX part in short [VERIFIED] (src: share/raw/scripts/zm/_zm_perks.gsc:280-315, _zm_perks.csc:202-275, zm_usermap.gsc:446-455, zm_usermap.csc:84,107-116; share/raw/fx/zombie/fx_perk_*.efx):

- `perk_fx()` waits 3 s after the machine powers on, then **server** `playfxontag( level._effect[ "<perk>_light" ], self, "tag_origin" )`, or plays it on a spawned `tag_origin` model when the machine has `b_keep_when_turned_off` set. Those `zombie/fx_perk_*_zmb` effects contain only 3–4 billboard sprites and no light element, so the lasting aura lights nothing [INFERRED] (from the element census).
- The client runs a ~3 s stutter-on, only when `level.enable_magic` is true: `perk_start_up` waits for `power_on`, then `play_perk_fx_on_client` spawns a client `tag_origin` 50 units below the machine and plays the machine light effect in bursts of growing length (_zm_perks.csc:192-265).
- The `*_factory_zmb` variants carry 6–15 real `dynamicLight2` elements each, all with interval = life. `zm_usermap.csc include_perks()` assigns them client-side before `load::main`; each perk's CSC init sets the sprite-only effect back when `level.enable_magic` is true (e.g. `_zm_perk_juggernaut.csc:34-37`) [VERIFIED]. Which assignment wins depends on call order, which was not traced [INFERRED]. `zm_usermap.gsc perk_init()` would swap the factory variants in server-side, but no stock script calls it [VERIFIED] (grep of share/raw/scripts).
- Quick Revive's prefab lights sit in exploder `quick_revive_lgts`, fired at `_zm_perk_quick_revive.gsc:185`; in solo they come on at load, because solo skips the co-op wait for `revive_on` (gsc:160-167) [VERIFIED].

**Avoiding "the whole tower lights up at once."** Give each floor or zone its own trigger: its own exploder name (`lgt_floor10_on`, …) or its own clientfield value, and play them in sequence from a door buy, a zone flag or a timed cascade [INFERRED] (stock precedent: The Giant's per-area `map_lgt_*` names). A lighting-state flip changes every state-gated light at once ([02](02_power_and_states.md)).

---

## 11. The Giant pattern: FX light plus a PROBE_ONLY twin

**Plain version.** Reflections and bounce light come from baked probes ([06](06_reflections_probes.md)). An FX light only exists while the game runs, so nothing shows that the bake ever sees it. A shiny floor next to a flickering lantern could therefore reflect a dark spot [INFERRED]. Treyarch's answer is to place a normal Radiant light at the same spot with `PROBE_ONLY` on, which "If enabled this light will only be seen by the reflection probes" [VERIFIED] (definition) (src: bin/t7.def.json `light` class). The FX light lights the room at runtime; the twin puts the lamp into the probes. The purpose is [INFERRED] from the pairing.

**The data** [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map, parsed with each fxdef's `.efx`):

- The Giant's light prefab has 96 `fx` entities; 94 play effects from `light/` folders. Of those 94, **67 have at least one `PROBE_ONLY 1` light within 12 units**, and for 56 the nearest light within 12 units is the probe-only one.
- 149 of the prefab's 543 lights are `PROBE_ONLY`.
- For **30 of the 38** per-placement fire effects, FX intensity = 2^stops of the `PROBE_ONLY` twin and the radii match. One more, `fx_light_zm_fire_spot_2`, matches an ordinary (non-probe) light at the same spot instead. The other seven do not match: `omni_2`, `omni_9`, `spot_1` (no light within 12 units), `spot_7`, `spot_9`, `spot_22`, `spot_25`. The matches follow the doc's workflow: tune a Radiant light, then copy its values into the FX light (src: docs_modtools/FX_Lights.pdf p.1).
- The lantern twins are hand-tuned rather than copied. Four sampled lanterns (FX intensity 60, radius 208) have probe-only twins at stops 5.97 / 5.64 / 9.23 / 3.64 with radius 400 / 200 / 120 / 300, all in the lamp's colour `1 0.4588 0.1608` and shadowed.
- Each sampled lantern also has a tiny ordinary omni with radius 10–27 at the bulb, and some have a radius 100–150 light with all four lighting states off (parked) [VERIFIED] (data). The small light probably lights the lamp's own glass [INFERRED]; the parked lights' purpose is unknown.

**A stock animated lamp therefore has four layers** [INFERRED] (synthesis): (1) a model whose light surface is emissive or a backlit "lampshade" material ([03](03_glow_and_perks.md)); (2) a small flame or glow sprite for the visible source; (3) an FX light carrying the flicker; (4) a `PROBE_ONLY` twin in the lamp's colour for reflections. A steady street lamp needs no FX light at all; a baked spot does the job and saves the dynamic budget ([08](08_fixture_cookbook.md)).

Our FX lights (perk glows, inducer, teleporter) have no probe twins, and they could not have fixed ones anyway: the perk machines move [VERIFIED] absence in repo map_source; consequence [INFERRED].

---

## 12. Halos and glow sprites

**Plain version.** A halo is a picture of glow drawn facing the camera. It adds brightness to the screen but no light to the world. It is the cheapest way to make a small source read as "on" from far away.

**Element types:** `billboardSprite` (always faces the camera), `orientedSprite` / `rotatedSprite` / `line` / `tail` (can turn away from the camera) [VERIFIED] (types present).

**Materials most used for light halos in the local library:** `gfx_light_phosphorous_em` (about 1,600 references across the whole library) and `gfx_light_incandescent_hot_em` (about 1,200), then `gfx_light_orb_hot_em` (+ `_i512`), `gfx_light_core_hot_em`, `gfx_light_glow_square`, and `gfx_light_ray_*` for beams [VERIFIED] (count from a grep of share/raw/fx; counts restricted to stock-named folders are lower). The base names are stock compiled materials with no local GDT source; a few suffixed variants, such as `gfx_light_incandescent_hot_em_i128` and `_nocull`, do have source blocks in source_data/black_ops_3_fx.gdt [VERIFIED] (grep).

**Material rules** [VERIFIED] (src: docs_modtools/Materials.pdf, Effect Lit Blend and Effect Lit Emissive sections):

- `effect_lit_blend` / `_nocull`: particles that are lit but emit nothing (smoke, dust).
- `effect_lit_emissive_blend` / `_nocull`: particles that "emit their own light, such as fire, lasers, tracers and light glows"; Emissive Mask + Intensity 0–12,000 (glows 16, fires 256). Here "emit" means the sprite draws itself bright; nothing in the doc says such a sprite lights the world around it [INFERRED].
- "Physically Based Emissive behavior": "emit light at one consistent value instead of adjusting to remain visible across EV values."
- The scroll variants "are not compatible with compute sprites, so FX Properties > Visuals > General > Don't use compute sprites must be enabled."
- For sprites that can turn in 3D, Falloff (Begin, End) fades them by view angle: "A good starting value is (45, 75)."

**Soft edges and shimmer.** Element `zFeather` softens where a sprite cuts into geometry (our perk glow sprite uses 40) [VERIFIED] (value). A steady halo is a looping sprite with a short interval and random size and rotation; flatten `alphaGraph` for no shimmer (repo tools/gen_tod_inducer_fx.py `alpha_flat`) [VERIFIED] (code).

**Cost.** "Transparency is the single fastest way to ruin our framerate because you open the door to having to light a pixel multiple times." [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 15; the slide is about transparent surfaces in general, such as glass). Halos are transparent sprites, and a big halo near the camera covers many pixels, so the same cost applies [INFERRED]. This project has already paid for it twice: "nothing big or bright spawns at the shooter's camera" (repo CLAUDE.md v18.75 / v18.91 ice-staff glare notes) [COMMUNITY] (project record).

**Sprite-only "light" effects** (they contain no light element, so they light nothing [INFERRED]) [VERIFIED] (element census): `light/fx_glow_blink_red_5` and `_10` (1–2 billboards; `_5` uses `gfx_light_orb_hot_em`), `light/fx_light_blink_com_strip_red` (one rotated sprite), `light/fx_light_robot_set_blink_yellow`, and every stock `zombie/fx_perk_*_zmb` aura.

**`info_corona`** is a Radiant entity ("Corona around a light"; `radius` default 20, `color`, `intensity` 0–1) [VERIFIED] (def) (src: bin/t7.def.json). No local stock map source uses it, and whether it renders in BO3 is unknown [TEST].

---

## 13. Lens flares

**Plain version.** A lens flare is the streak or ghosting a bright light makes in a camera lens. It is drawn on the screen, lights nothing, and is set up to disappear when something blocks the source [INFERRED] (from its occlusion flags below).

**How it is built** [VERIFIED] (src: share/raw/fx/lensflares/fx_lensflare_light_bulb_basic.efx; share/raw/lensflares/lf_light_bulb_basic.klf):

- An `.efx` element whose visual block is `lensFlare { "<uuid>" };`, with `editorFlags looping`, `spawnLooping 16 0` and `lifeSpanMsec 16 0` (re-spawned about every frame), `extraFlags lfOccludeGeometry lfOccludeParticles` (by the names, hidden when geometry or particles block it [INFERRED]), and `spawnRange 0 1300`.
- The UUID points at a `.klf` text asset in `share/raw/lensflares/` (22 installed, for example `lf_light_bulb_basic.klf`, uuid `fa73328f-…`, `type FX_LENSFLARE_RADIAL`, a grime texture and a list of streak/ghost elements).
- Radiant also has `lensflare` and `klf` point entities with an `assetname` key [VERIFIED] (def); stock prefabs use `klf` twice (mp_sector_fx.map, mp_combine_fx.map) [VERIFIED].
- Radiant's binary contains `MAX_VISIBLE_LENSFLARE_INSTANCE` / `MAX_VISIBLE_LENSFLARE_ELEM` overflow warnings [VERIFIED] (string); the numbers are unknown.

**Stock flare effects and their `.klf`** [VERIFIED] (mapping by UUID):

| Effect (`lensflares/…`) | `.klf` | Use |
|---|---|---|
| `fx_lensflare_fluorescent` | `lf_light_fluorescent_streak` | Tubes |
| `fx_lensflare_light_bulb_basic`, `fx_lensflare_light_apartments` | `lf_light_bulb_basic` | Plain bulbs |
| `fx_lensflare_light_cool_lg`, `fx_lensflare_light_yellow_lg` | `lf_light_bulb_cool` | Larger fixtures |
| `fx_lensflare_light_warm_sm` | `lf_light_bulb_warm_sm` | Small warm lamps |
| `fx_lensflare_light_grime_md` | `lf_light_grime_md_white` | Dirty white lamp |
| `fx_lensflare_light_grime_md_yellow` | `lf_light_sodium_lamp_sm` | Sodium street lamp |
| `fx_lensflare_light_cool_xlg` | `lf_light_cool_grime_sector` | Big cool floodlight |
| `fx_lensflare_light_sector` | `lf_light_direction_basic` | Directional |
| `fx_lensflare_light_china` | `lf_light_spot_vtol` | Spotlight |
| `fx_lensflare_fire_grime` | `lf_flash_fire_grime` | Fire |
| `fx_lensflare_grime01` | `lf_light_grime01` | Grime |

**Avoid** `fx_lensflare_bulb_white`, `fx_lensflare_light_spot` and `fx_lensflare_light_square`: their UUIDs have no `.klf` in `share/raw/lensflares` [VERIFIED].

**The sun flare** is an SSI field (`lensFlare`, `lensFlarePitchOffset`, `lensFlareYawOffset`; deffiles/ssi.awi) with a stock example `lf_sun_mp_sector.klf` [VERIFIED]; see [05](05_sun_sky_exposure_fog.md). A community tip for a dark map is to keep the sun flare off, or use it only temporarily to find where the SSI sun sits [COMMUNITY].

**History:** Map One zoned `lensflares/fx_lensflare_fluorescent` and `fx_lensflare_light_cool_lg`; they linked, but no in-game sighting was recorded [COMMUNITY] (project record). The community FX-library authors wrote "We currently do not know much about porting the lensflares" (forum.modme.co thread 2403) [COMMUNITY]. A usermap flare is unproven here [TEST].

---

## 14. God rays and dust motes

**Plain version.** A "god ray" is a visible shaft of light in dusty air. BO3 offers three different things that look like it: a real volumetric light, a fake beam made of a picture, and floating dust that only shows where light falls.

### 1. Real volumetric light

- On a Radiant light, or inside an FX light's settings block: `volumetric 1` ("Enables rendering of light as volumetric"), `volumetricSampleCount` (1–24, default 8, "Number of ray march samples"), `volumetricIntensityBoost` (stops, −14..14), `volumetricCookies` [VERIFIED] (src: bin/t7.def.json).
- About 340 local stock FX lights are volumetric, for example `light/fx_light_yellow_flicker2` (spot, shadowed), `light/fx_light_ceiling_fire_factory_zmb`, `light/fx_light_ground_fire_spot_factory_zmb`, `dlc2/island/fx_lgt_bunker_surgery_spot` [VERIFIED] (count from a parse). An FX light's shaft presumably flickers with its intensity curve [INFERRED].
- Community steps: "set the KVP volumetric to true … spawn a volume>litfog … Edit fsi_1 … zm_factory_volumetric … Rebuild lights if F8 doesn't update"; "looks good with a night SSI" (ugx-mods.com thread 12832, 2016) [COMMUNITY]. The Giant's light prefab ships three `volume_litfog` entities [VERIFIED] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map). Fog volumes are in [05](05_sun_sky_exposure_fog.md#6-fog).
- **Players can switch it off.** BO3's `players/config.ini` has `VolumetricLightingEnabled` "Enable volumetric sun and light shafts" [VERIFIED] (config text), and the user's own config sets it to 0 [VERIFIED]. So the user's playtests will not show shafts [INFERRED]. Whether lit fog itself also disappears with that setting is unknown [TEST]. Our generator sets no `volumetric` key, so no Tower II light is volumetric today [VERIFIED] (absence in repo map_source/zm/zm_tod2_cybercity.map). It does write `volumetricSampleCount 8` on every light (repo tools/gen_tower_map.js `light()`), which should do nothing while `volumetric` is off [INFERRED].

### 2. Fake beams (sprite cards)

A `line` or oriented sprite with a ray material. Cheap, lights nothing, needs no player setting [INFERRED]. Stock examples [VERIFIED] (census): `light/fx_light_cone_metro_sm` (a `line` with `gfx_light_ray_cone_em_i2048` + a `gfx_light_incandescent_hot_em_i128` core billboard), `dlc1/castle/fx_light_searchlight_single_castle` (`gfx_light_ray_cone_em` oriented sprite), `dlc5/tomb/fx_light_robot_foot_shafts` (lines and rotated sprites with `gfx_light_ray_wide_soft_em`, plus 2 lens flares), `dlc5/zmhd/fx_mp_ray_spotlight_xlg`. Add a real light where the beam lands if the floor should brighten [INFERRED].

### 3. Dust motes

Lit particles (`*_lit` materials) that show where light falls and fade where it does not [INFERRED] (from the lit-shader description in docs_modtools/Materials.pdf). BO3 lights particles per vertex: Treyarch's PBR overview lists "Vertex lighting/shadowing on particles" [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 5). So a mote cloud picks up nearby lights, FX lights included [INFERRED], which makes motes a good way to show off a light pool in a dark room. Clean candidates [VERIFIED] (real sources, no placeholder, no `pcloud`, no child effects, identical in the tools tree and the private workspace): `dirt/fx_dust_motes_200x200` and `dirt/fx_dust_motes_300x300_sm` (`gfx_dust_mote_01_lit`), `dirt/fx_dust_motes_sphere_50` (`gfx_dust_light_lit`), and `dirt/fx_dust_linger_int_sector` (already used for our lounge haze). The first three are Wraith reconstructions (one `wraith_looping_def0` element) [VERIFIED].

**Avoid** every `env/light/*` effect (`fx_light_god_ray_sm_single`, `fx_light_god_rays_dust_motes`, `fx_ray_ceiling_amber_dim_sm`, `fx_glow_hanginglamp`, `fx_dlight_fire_glow`) and `maps/zombie/fx_zm_asylum_godray_md`: all are 5,092-byte placeholder sources [VERIFIED] ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)). Also be careful with `dirt/fx_dust_motes_150x150`, `_250x250` and `_200x200_pcloud`, which use a `*_pcloud_lit` material ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)).

---

## 15. Limits and cost

| Limit or cost | Value | Source / confidence |
|---|---|---|
| Live shadows | ~12 at `shadowmapScale 1`, 3 at scale 2, ~48 at 0.5; scale unsupported on omnis | [VERIFIED] docs_modtools/Lighting_Parameters.pdf |
| FX-light shadow modes | Always (live) or off; no cached "Never" | [VERIFIED] FX_Lights.pdf p.2 |
| Shadow atlases | `numOmniShadowSlices` 24 (8–256), `numSpotShadowSlices` 64 (8–1024); Giant 96 omni | [VERIFIED] bin/t7.def.json; zm_giant.map |
| FX elements | `FX_ELEM_LIMIT(4096) exceeded - not spawning fx elem` | [VERIFIED] string in bin/radiant_modtools.exe; same limit in game [INFERRED] |
| FX spot lights | `FX_SPOT_LIGHT_LIMIT … exceeded - not spawning spot light effect`; the number is not exposed | [VERIFIED] string; value unknown [TEST] |
| Unique FX handles | `Max fx unique handles (%i) exceeded` | [VERIFIED] string; value unknown |
| Map lights (Radiant lights, not FX lights) | `Map contains %u lights, max %u supported. This map won't link.`; also `Sun volume contains %u lights, max %u supported` | [VERIFIED] strings; values unknown |
| Exploders | "Total Exploders: 0/120" in the manager | [INFERRED] cap of 120 |
| Lens flares | `MAX_VISIBLE_LENSFLARE_INSTANCE` / `_ELEM` warnings | [VERIFIED] strings; values unknown |
| Distance | `spawnRange` max distance per element (our perk glow light 3000, sprites 5000); `culling_cutoff/falloff` in pixels at 1080p for Radiant lights (starting values 200/300; 1/5 for radius under 10) | [VERIFIED] values and docs_modtools/Culling_LOD_Lights.pdf; whether FX lights honour the culling keys is unknown [TEST] |
| Frame cost of FX lights | No published figure | Measure in game |
| Transparency | "the single fastest way to ruin our framerate" | [VERIFIED] PhysicallyBasedRendering.pptx slide 15 |

**Community reports** [COMMUNITY]: dynamic-light FX "not showing consistently" under load, fixed with fewer, larger effects and zone-based on/off (forum.modme.co thread 3280); FX lights stop working after `fast_restart`, so restart from the menu when judging them (thread 496, Harry Bo21); lights "turning off" at distance is intended, from FX visible ranges (thread 459); Radiant stops drawing some FX when many are placed, an editor-only effect (steamcommunity.com/app/455130/discussions/0/1457328392112627908).

**The "far FX never appears" problem.** Map One found that a glow started far from the player at power-on did not reliably appear when the player approached, so our perk glow re-pulses its clientfield once when a player first comes within 700 units (repo `_tod_perk_lights.gsc:14-17, 28, 422-461`) [COMMUNITY] (project record). Candidate causes, none tested: the element's `spawnRange` / `spawnFrustumCull`, the effect's bounding-box cull, portal culling of the host (`SetForceNoCull` exists for that) [INFERRED] [TEST].

---

## 16. Stock light-FX catalog

All entries were read from share/raw/fx: real source (no placeholder), no `pcloud` material, no child effect, looping, with a light element, unless noted. Notation: OMNI/SPOT, **SH** = `PRIMARY_NOSHADOWMAP 0`, which for an FX light means a live shadow ([section 7](#7-shadows-on-fx-lights)), **VOL** = `volumetric 1`, I = intensity base, R = radius, interval/life in ms. (w) = Wraith reconstruction. None has been tested in this map [TEST].

**Lamps and lanterns (warm)**

| Effect | Light |
|---|---|
| `light/fx_light_lantern_factory_zmb` | OMNI SH, I 60, R 208, 1000/1000 wobble (The Giant's lantern) |
| `light/fx_light_lantern_factory_higher_zmb` | OMNI SH, I 60, R 350, 1000/1000 |
| `light/fx_light_lantern_factory_zmb_spot_2` / `_3` | SPOT SH VOL, I 2504 / 1003, R 346 / 150 |
| `dlc0/light/fx_light_lantern_factory_zmb0_spot_1` | SPOT SH VOL, I 2048, R 250, FOV 50 |
| `dlc1/castle/fx_light_lantern_castle` (w) | OMNI I 1024 R 10 (bulb) + OMNI SH I 128 R 200 (room) |
| `dlc1/castle/fx_light_castle_streetlgt` (w) | OMNI I 1024 R 10 (bulb) + SPOT I 2048 R 300 FOV 75 (street-lamp shape), 500/500 |
| `dlc5/sumpf/fx_light_lanterns_sm` (w) / `_spot` (w) | OMNI VOL R 35 / SPOT SH R 280 |

**Candles and small flames:** `light/fx_light_candle_zod` (OMNI I 16 R 50, no shadow), `light/fx_light_candle_cathedral` (I 5000 R 75), `light/fx_light_candle_ramses` (I 5000 R 200).

**Fire light (pair with a flame sprite effect)**

| Effect | Light |
|---|---|
| `light/fx_light_fire_flicker_noshad_small` | OMNI, **no shadow**, I 90, R 150, 300/300: the cheapest fire flicker |
| `light/fx_light_barrel_fire_factory_zmb`, `_strong`, `light/fx_light_barrel_fire_zod_01` | OMNI SH, I 100 / 500 / 724, R 150, 600/600 |
| `light/fx_light_window_fire` | SPOT, no shadow, I 500, R 150, 600/600 |
| `light/fx_light_ceiling_fire_factory_zmb` | SPOT SH VOL, I 1500, R 325 |
| `light/fx_light_ground_fire_spot_factory_zmb` | SPOT SH VOL, I 750, R 400 |
| `light/fx_light_zm_fire_omni_1…13`, `…_spot_1…25` | Each tuned to one Giant placement. Map One removed `fx_light_zm_fire_spot_1` during a freeze hunt that ended up blaming another effect; unresolved [COMMUNITY] (project record) |

**Electrical flicker and failing tubes**

| Effect | Light |
|---|---|
| `light/fx_light_yellow_flicker` / `_flicker2` | SPOT SH VOL, I 1024, R 300–400, 1000/1000, brief blackouts |
| `light/fx_light_zm_furnace_flicker` / `2` | SPOT SH VOL, I 16 / 200, R 241 / 210, 600/600 |
| `light/fx_light_flickering_hat_light_sodium` (w) | SPOT SH VOL I 1024 R 175 + small SPOT; 5000/1000 with random 0–3900 ms start (occasional flicker). Map One used it |
| `light/fx_light_sgen_dayroom_rectangle_flicker` (w) | SPOT SH, I 256, R 185, 500/480±20. Map One used it |
| `light/fx_light_sgen_dniroom_flicker` (w) | OMNI, no shadow, I 28, R 150 |
| `light/fx_light_sgen_silo_flicker` (w) | SPOT VOL, I 3250, R 350 |
| `dlc4/genesis/fx_lgt_gen_flicker_asylum` (w) | 3 SPOTs (two SH VOL), I 512, R 221, 6000/6000 |
| `light/fx_sgen_light_lowflicker` (w) | Tiny SPOT, I 20, R 10 |

**Blink, strobe and alarm**

| Effect | Light |
|---|---|
| `light/fx_light_flashing_red_factory_zmb` | OMNI, no shadow, I 100, R 20, 1000/500 (The Giant's `map_lgt_pap_flash` exploder) |
| `dlc2/island/fx_lgt_bunker_blink_red` / `_green` (w) | OMNI VOL, I 128, R 200, 1000/1000 |
| `light/fx_sgen_emergency_whiteflash`, and `_blueflash` (w) (+ `_small`, `_long` variants) | 2 SPOT SH VOL I 15000 R 550 + 2 OMNI fills; 1000/100–200 double strobe. Expensive |
| `dlc3/stalingrad/fx_light_emergency_flash_loop_stalingrad` (w) | OMNI SH, I 35000, R 150, 1000/100 |
| `light/fx_light_jet_wingstrobe` (w) | OMNI VOL, I 240, R 170 |
| `light/fx_lotus_emergency_flash` | SPOT SH VOL I 16384; uses cookie `def cuc_ies_017`: avoid until custom cookies are proven [COMMUNITY] (project record) |

**Spot beams that really light:** `dlc2/island/fx_lgt_bunker_surgery_spot` (w) (SPOT SH VOL, I 2048, R 400), `light/fx_light_landingspot_vtol_dropship` (w) (SPOT SH VOL, R 2000), `light/fx_light_turret_sentry_spot` (w) (SPOT SH VOL, R 1400, 16/16).

**Sprite-only beams:** see [section 14](#14-god-rays-and-dust-motes).

**Coloured glows and bulbs:** `dlc2/island/fx_greenbulb` / `fx_redbulb` (w) (OMNI VOL, I 1024, R 30, 100/100), `dlc1/castle/fx_glow_panel_green_castle` / `_red_castle` (w) (tiny, R 8), the stock powerup auras `zombie/fx_powerup_on_green/red/solo/caution_zmb` (`light_small` OMNI, I 512, R 60, 200/200 + 3 sprites; client_fx in share/raw/scripts/zm/_zm_powerups.csc:13-16), and the project-authored `acc/light/fx_perk_glow_<colour>` (17 in the tools tree, 10 in the repo).

**Sprite-only glows (light nothing):** `light/fx_glow_blink_red_5` / `_10` (despite the names, they have no light element), `light/fx_light_blink_com_strip_red`, `light/fx_light_robot_set_blink_yellow` [VERIFIED] (census).

---

## 17. The placeholder-stub trap, and how to vet an effect

**Plain version.** Many `.efx` files in the Mod Tools are not real effects. They are empty stand-ins for effects whose source Treyarch did not ship [VERIFIED] (the scan below). The real, compiled effect still exists inside the base game, so if your map never zones that name, the game uses the real one. If your zone lists it, the linker packs the empty stand-in into your map, where it replaces the real one, and the effect shows nothing, with no error. That second half rests on one project observation, not a Treyarch source [COMMUNITY] (project record; details below).

**Where the library comes from.** The local `share/raw/fx` holds 6,775 `.efx`. About 5,860 of them name their elements `wraith_*` (about 5,560 if the 298 placeholder files below are left out; for example dlc2 496 of 496, zombie 658 of 707, light 113 of 188) and carry 2018 file dates [VERIFIED] (scan). The community "Harry Bo21 / Scobalula / DTZxPorter FX library" was "extracted using Wraith", covers every zombies map, and warns that "some are using the default missing material to signify its not complete … Some FX crash radiant" (forum.modme.co thread 2403) [COMMUNITY]. So `wraith_*` files are reconstructions, not Treyarch sources [INFERRED]. Files with element names like `0_exp_light` look Radiant-authored [INFERRED].

**The stubs** [VERIFIED] (scan):

- 241 files contain the material `gfx_debug_missing_fx`; 238 of those are the same 5,092-byte file (md5 `12186140ea48c0fbb26652875b09a844`).
- A second family of 60 files, all under `_t6/`, uses `gfx_debug_deleted_fx` (59 are 5,092 bytes, md5 `c3533a73…`).
- 298 files are exactly 5,092 bytes, but size alone is not a test: `light/fx_light_fire_flicker_noshad_small.efx` is also 5,092 bytes and is a real light. Test for the two material names.
- Stubs worth knowing about include everything in `env/light/`, `maps/zombie/fx_zm_asylum_godray_md`, `maps/zombie/fx_zombie_light_glow_green` / `_red` (The Giant's CSC precaches these names; the base game presumably has the real ones [INFERRED]), `maps/zombie/fx_zombie_light_elec_room_on`, `maps/zombie/fx_zombie_theater_projector_beam`, `light/fx_light_body_glow_warlord`, `weapon/fx_betty_light_blue` / `_orng`, `zombie/fx_fire_torso_zmb`, `zombie/fx_dog_fire_trail_zmb`.

**What zoning a stub does** rests on one project observation, not on a Treyarch source [COMMUNITY] (project record): the zoned `zombie/fx_dog_fire_trail_zmb` drew nothing and a real-sourced swap fixed it, while the never-zoned stub `zombie/fx_fire_torso_zmb` (the nuke burn) rendered from the base game (TOD1 memory `stub-efx-in-mod-tools`).

**Tower II zones two stubs right now** [VERIFIED] (src: repo zone_source/zm_tod2_cybercity.zone:431 and :451 as of 2026-09-24; both files are the 5,092-byte stub in MODTOOLS and in C:\BO3Tools\TOD2Cybercity, with no repo override). The linker's own records confirm the stubs are what gets packed: the private workspace's latest `zone_source/all/assetinfo/zm_tod2_cybercity.deps` lists both 5,092-byte sources as read, and its `.csv` shows the placeholder material `ei/gfx_debug_missing_fx` and image `fxt_misc_missing_fx` packed as children of `env/light/fx_light_god_rays_dust_motes` [VERIFIED] (src: C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\zone_source\all\assetinfo\, dated 2026-09-24).

| Zone line | Used as | Likely result |
|---|---|---|
| `fx,zombie/fx_thundergun_smoke_cloud` | `level._effect[ "tod_thor_cloud" ]`, THOR'S THUNDER's lingering cloud (repo `_tod_upgrades.gsc:1053, 1113`) | Blank [COMMUNITY] (project rule) [TEST] |
| `fx,env/light/fx_light_god_rays_dust_motes` | `level._effect[ "tod_lounge_motes" ]`, the motes falling into each breather lounge (repo `_tod_atmosphere.gsc:160, 230, 242`) | Blank [COMMUNITY] (project rule) [TEST]. TOD1's project memory calls its lounge motes "blank since v16.7"; that note was written after the stub was found and records no in-game check |

Every other `fx,` line in the zone (95 in all) resolves to a non-placeholder source [VERIFIED] (scan, 2026-09-24).

**Other hazards this project has recorded** [COMMUNITY] (project records) unless noted:

- **`pcloud` materials.** Map One traced a first-render `Com_ERROR … 'particlecloud'` to one effect whose sparks used `gfx_fxt_spark_2_pcloud_em` (`fire/fx_fire_barrel`). But Tower II zones 10 effects whose sources reference other `*_pcloud_*` materials, used on `cloud` elements where checked: the Mage staff effects (`tod/fx_tod_elec_impact_sm` with `gfx_spark_01_pcloud_em`, `tod/bo6/fx_tod_staff_glow_ice` with `gfx_dust_mote_*_pcloud_em`, the four `tod/bo6/fx_bo6_ice_*` effects, `tod/mage/fx_staff_lightning_chain_clean`) and three stock ones (`dlc5/tomb/fx_tomb_mech_death`, `dlc4/genesis/fx_apothicon_fury_spawn_in`, both `_pcloud_em`, and `dlc1/castle/fx_mech_jump_landing`, which uses `gfx_dirt_pcloud_0*_lit`). The ice-staff effects were recorded rendering in native runs [VERIFIED] scan of the zone and sources; the run record is repo CLAUDE.md v18.90–v18.93 [COMMUNITY]. So `pcloud` is a warning to test, not an automatic veto [INFERRED].
- **Child effects.** An effect can name other effects (a quoted `"folder/name"` path: a `runner` element, an on-impact or on-death effect; FX_QuickStart.pdf calls the tab "Child Effects"). **The linker packs those children automatically with the zoned parent.** In the latest linker record, all 21 distinct child effects that Tower II's zoned effects name without their own `fx,` line are packed, each with its parent in the `parentStack` column. Examples: `zombie/fx_tesla_shock_ground` under `zombie/fx_tesla_shock_zmb`; `electric/fx_elec_sparks_burst_xsm_omni_orange_os`, which the inducer's spark loop `electric/fx_elec_spark_loop_sm` names, under `destruct/fx_dest_robot_body_sparks` [VERIFIED] (src: C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\zone_source\all\assetinfo\zm_tod2_cybercity.csv). The ledger seems to list each asset once, under the first parent that pulled it in [INFERRED]. TOD1 once recorded a black-screen hang after ModLoad when a weapon's `projTrailEffect` named an effect with an unzoned child. That case was fixed by switching to a child-free effect, so its real cause was never isolated [COMMUNITY] (TOD1 memory `stub-efx-in-mod-tools`, v18.31). Given the ledger, "every child needs its own zone line" is not a general rule [INFERRED]. For an effect on a weapon, viewmodel or projectile, still prefer a child-free effect or add the child's `fx,` line as insurance, and test it [TEST].
- **Light cookies.** Map One suspected explicit `def` cookie lines inside an effect of causing a freeze. Every TOD and Map One perk glow and the inducer carry `def white_light` and render, so plain `white_light` is safe in practice; custom cookies (`cuc_ies_017`, `cookie_caustic_ink`, `gobo_*`) remain unproven in usermaps.
- **Filenames with spaces** (for example `light/fx_light_red flash_sml_sector.efx`, `zombie/fx_perk_juggernaut_zmb .efx`) are unsafe in zone lines [INFERRED].

---

## 18. Our FX lights today: perk glow, inducer, teleporter

Every value below is read from the repo sources [VERIFIED]; how each looks in game is the user's call.

| Effect (repo `share/raw/fx/…`) | Played by | Light element | Interval / life | Against the loop rule |
|---|---|---|---|---|
| `acc/light/fx_perk_glow_<colour>` (10 colours) | Client, clientfield `todPerkGlow` → CSC `PlayFXOnTag` on the machine (repo `_tod_perk_lights.gsc/.csc`) | `light_small`: OMNI, no shadow, I 512 × a two-hump curve, R 60, 40 units up, `spawnRange 0 3000` | 200 / 1000 | ~5 overlapping lights. Stock parent `fx_powerup_on_green_zmb` is 200 / 200 |
| `tod/fx_tod_inducer_idle` | Server `PlayFXOnTag` on a spawned `tag_origin` host, re-made on every change (repo `_tod_rampage.gsc` `glow_set`) | OMNI, no shadow, I 120 flat, R 60, 18 up (inside the glass) | 200 / 1000 | ~5 overlapping; flat curve, so only brighter, not mushier [INFERRED] |
| `tod/fx_tod_inducer_on` | same | OMNI, no shadow, I 1500 × 0.3 → 1 → 0.3, R 60, 18 up | 200 / 1000 | ~5 overlapping; predicted near-flat ~3.25× base instead of a pulse [INFERRED] [TEST] |
| `tod/teleporter/fx_tod_tp_ready` | Server host at each ready pad (repo `_tod_teleport.gsc:267, 312`) | `ready_floor_light`: OMNI, no shadow, I 150, R 100, 26 up | 1600 / 1600 | Compliant |
| `tod/teleporter/fx_tod_tp_charge_field` | `fx_burst` overlay for 1.3 s (0.8 s charge + 0.5) (repo `_tod_teleport.gsc:645`) | `charge_floor_light`: OMNI, I 900, R 130 | 5000 / 700 | Gap, but the host is deleted before the second spawn, so it is one 700 ms flash [INFERRED] (from the timing) |
| `tod/teleporter/fx_tod_tp_release_field` | `fx_burst` overlay for 2.0 s (repo `_tod_teleport.gsc:602`) | `release_floor_light`: OMNI, I 1150, R 155 | 5000 / 650 | Same: one 650 ms flash |
| `tod/fx_tod_elec_impact_sm`, `tod/bo6/fx_bo6_ice_impact` | Weapon impacts | One-shot OMNI, I 128 / 1024, R 100 / 50, life 150 | one-shot | Interval irrelevant |
| `tod/bo6/fx_tod_staff_glow_elec` / `_fire` / `_ice` | Staff tip glows (client) | Tiny OMNIs and SPOTs, I 8–32, R 8–30 | mostly 1 / 1; `wraith_looping_def14` 100 / 50 | Continuous; def14 blinks by design of its donor [INFERRED] |

**Perk colour map** (repo `_tod_perk_lights.gsc` `perk_color_index`): 1 red Juggernog, 2 green Speed Cola, 3 yellow Double Tap, 4 orange Stamin-Up, 5 amber Death Perception, 6 blue Quick Revive, 7 blacklight Wisp Tea, 8 white Widow's Wine, 9 purple PhD Flopper, 10 teal Pack-a-Punch and default. (The comments beside the CSC table are stale: they name retired perks for 5 and 7 and call 9 a spare.)

**What the perk glow adds up to** [INFERRED]: a radius-60 omni 40 units above the machine origin mostly lights the machine's own front and the floor right in front of it. A single copy would pulse between 0.15× and 0.63× of 512; the five stacked copies sum to a near-steady 1.6–2.3× of 512, roughly 830–1,190, depending on which of the two random curves each copy takes (arithmetic, assuming overlapping FX lights add; [section 5](#5-the-looping-rule-and-why-it-matters)). The stock `zombie/fx_perk_*_zmb` sprite aura is probably still played by stock `perk_fx` on our machines too, since nothing overrides `level._effect[ "<perk>_light" ]` [INFERRED]; open question in [03](03_glow_and_perks.md).

---

## 19. Recipes

### A. Author an animated FX light in Radiant (the official route)

1. Place a normal `light` entity and tune it until it looks right: type, colour, radius, `stops`, cone, falloff (src: docs_modtools/FX_Lights.pdf p.1).
2. Fx → New effect. Turn on Fx → Fx Rendering Enabled, View → Render Flags → Render Always, and Real Lighting in the camera (src: docs_modtools/FX_QuickStart.pdf).
3. Put the effect at the light's position. In FX Outline, rename the element (for example `Light`).
4. FX Properties → Visuals: Type = Dynamic Light; Add a visual; Edit; optionally pick a Lighting Description; set the keys for **type and shaping**.
5. Visuals → Color: set Intensity (≈ 2^stops of your light), Radius and FOV. In FX Graph → Color, right-click each knot → Set color.
6. Aim with Movement → Rotation Geometry; offset with Generation → Origin.
7. Generation: Looping. **Lifetime min = max = Interval** (for example 1000 ms), unless you want a blink (interval longer than life).
8. FX Graph: draw the Intensity curve (Shift + middle mouse adds a knot). Flicker = many knots between 0.3 and 1; blackout = brief drops to 0; pulse = one hump per life.
9. Keep `PRIMARY_NOSHADOWMAP 1` unless a live shadow is the point.
10. FX Outline → right-click the name → Save effect as. For Tower II, save it as a map-owned source under repo `share/raw/fx/tod/…`; the sync installs it into the private workspace (repo docs/154, docs/155).
11. Wire it: a placed fx entity or exploder (full build), or script plus `fx,<path>` zone line and `#precache` (linker only, so `-GscOnly` is enough by project practice, unless the effect brings new GDT materials or images: [section 9](#9-playing-fx-from-script)). Build and stop; the user tests.

### B. Make or change an FX light by text (the generator route)

1. Pick a real donor with a `dynamicLight2` element and vet it (recipe E). Our precedent: repo tools/gen_tod_inducer_fx.py from `acc/light/fx_perk_glow_amber.efx`.
2. Keep only the elements you need (split on `\n{\n\tname "`).
3. Retint `colorGraph` rows (`t r g b`); rewrite `lightIntensityGraph <base> { {…} {…} };`; adjust `lightRadiusGraph` / `lightFovGraph`; set `spawnOrgZ` for the light's height.
4. **Set `spawnLooping` equal to `lifeSpanMsec`** unless you want a deliberate blink.
5. Leave `PRIMARY_TYPE`, `PRIMARY_NOSHADOWMAP 1` and shaping in the settings block; its `stops`, `radius` and `_color` are not the live values.
6. Write to repo `share/raw/fx/tod/<name>.efx`; add `fx,tod/<name>` to the zone and `#precache( "fx", "tod/<name>" )` (or `client_fx` in CSC); add a dev log for play/stop; build (`-GscOnly` is enough for a script-played effect with existing materials, per [section 9](#9-playing-fx-from-script); full if anything in the `.map` or a GDT changed); stop; the user tests.

### C. Turn FX lights on with power, per floor (script routes proven here)

**Server host lane** (looping effects; the inducer and teleporter pattern):

```c
#precache( "fx", "tod/fx_tod_lamp_on" );       // + zone line: fx,tod/fx_tod_lamp_on
// in the module's init: level._effect[ "tod_lamp_on" ] = "tod/fx_tod_lamp_on";
// (needs #using scripts\shared\flag_shared and #insert scripts\shared\shared.gsh)
function lamp_on( org, ang )
{
    level flag::wait_till( "power_on" );
    e = Spawn( "script_model", org );
    e SetModel( "tag_origin" );
    e.angles = ang;
    WAIT_SERVER_FRAME; WAIT_SERVER_FRAME;       // let the host replicate (repo docs/143)
    PlayFXOnTag( level._effect[ "tod_lamp_on" ], e, "tag_origin" );
    return e;                                   // to switch off: e Delete();
}
```

**Client lane** (late-join safe; our perk glow and stock powerups): register the same `scriptmover` (or `world`) clientfield in both VMs; in the CSC callback call `self util::waittill_dobj( localClientNum )`, stop any previous handle with `StopFX`, then `self.fx = PlayFXOnTag( localClientNum, fx, self, "tag_origin" )`; on value 0 call `StopFX` (or `KillFX` to cut at once). Precache with `client_fx` (repo `_tod_perk_lights.csc:38-83`; share/raw/scripts/zm/_zm_powerups.csc:96-126).

For staging, give each floor its own host or clientfield value and set them from that floor's door or zone flag. Log each state edge with the feature's `[TOD_*]` tag (repo CLAUDE.md dev-log rule).

### D. Turn FX lights on with power: Radiant exploder route (stock; never tried in the user's maps)

1. Place the fx entities and/or primary lights; select them; Exploder Manager → "Create New Exploder from selection"; name it (for example `lgt_floor10_on`). Primary lights that start off get `exploderDisabled 1`.
2. Export lighting. In the Radiant GUI, Export Local Probes alone is enough when the probes need no update; in this repo that means a full build ([section 8](#8-radiant-fx-entities-and-exploders)).
3. Drive it from a `world` clientfield: server sets the field at power; the CSC callback calls `exploder::exploder( name )` or `exploder::stop_exploder( name )` (stock: `_zm_trap_electric.csc:20-37`).
4. For a generated map, an fx entity needs `"classname" "fx"`, `fxdef`, `origin`, `angles`, `fxstate1..4`, `exploder_count "1"`, `exploder_index_0 "ver=2 don=0 doff=0 fin=0 fout=0 off=0 name=<name>"` (format copied from stock prefabs; field meanings unverified). This would be a new, untested lane for our generator.

### E. Vet a stock effect before zoning it

Read-only checks on `share/raw/fx/<path>.efx`:

1. `gfx_debug_missing_fx` or `gfx_debug_deleted_fx` present → placeholder; do not zone.
2. `pcloud` present → note it and test it in a short run ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)).
3. Quoted `"folder/name"` paths → child effects. The linker packs them with the parent, but vet each child with these same checks (a stub child is still a stub). For weapon, viewmodel or projectile effects, prefer a child-free effect or give the child its own `fx,` line as insurance ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)).
4. A `def` other than `white_light` → unproven in usermaps.
5. `wraith_*` element names → community reconstruction.
6. For each light element: `PRIMARY_NOSHADOWMAP` (0 = live shadow cost), `volumetric`, `spawnRange`, and interval against lifetime.
7. No spaces in the filename.
8. After the build, confirm the effect is listed in the deployed usermap's `zone_source/all/assetinfo/<map>.csv` and `.deps` (for Tower II under `C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\`). The `.deps` entry names the exact `.efx` file the linker read, and the `.csv` `parentStack` column shows which children came with it, so together they show whether a stub or an unexpected child was packed [VERIFIED] (format). Only the user's playtest shows whether it draws.

### F. A light shaft

1. **Real shaft:** a spot light (Radiant or FX) with `volumetric 1`, `volumetricSampleCount` 8, `volumetricIntensityBoost` a stop or two if faint, inside a `volume_litfog` with an `fsi` set ([05](05_sun_sky_exposure_fog.md)). Copy `light/fx_light_yellow_flicker2` for a flickering shaft. Remember players with volumetrics off see no shaft.
2. **Cheap fake:** a cone sprite effect (`light/fx_light_cone_metro_sm`) plus a real light where it lands.
3. **Motes:** `dirt/fx_dust_motes_200x200` / `_300x300_sm` / `_sphere_50`, never an `env/light/*` name.

---

## For Tower of Doom II

Recommendations only; nothing here has been changed or tested.

1. **Fix the two stub zone lines.** Replace `env/light/fx_light_god_rays_dust_motes` (lounge motes) with a real source such as `dirt/fx_dust_motes_200x200` or `dirt/fx_dust_motes_sphere_50`, and replace or drop `zombie/fx_thundergun_smoke_cloud`. Either way, remove the stub lines. The linker record already shows it packing the placeholder sources and their debug material ([section 17](#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)), so they very probably draw nothing [INFERRED].
2. **A/B the loop timing of the perk glow and the inducer.** Make `spawnLooping` equal `lifeSpanMsec` (1000 / 1000). Removing the overlap cuts the average light to about a fifth. To make the new pulse *peak* at today's stacked level, raise the intensity base about 3.2× for the inducer (stack ≈ 3.25×, curve peak 1.0) and about 2.6–3.7× for the perk glow (stack 1.6–2.3×, curve peak 0.63). To keep the same *average*, raise both about 5× [INFERRED] (the overlap arithmetic in [section 5](#5-the-looping-rule-and-why-it-matters), which assumes overlapping FX lights add). Only the user can judge whether the restored pulse is better. Their look is currently approved, so this is a test build, not a fix.
3. **Use FX lights for everything that moves or animates** in the dark tower: perk machines (already done), devices, alarm strobes at doors, the power-on "wake-up" per floor. Use baked Radiant lights for steady fixtures ([01](01_lights.md)), since FX lights add nothing to bounce or probes.
4. **Stage power-on with FX, not one switch.** One host or clientfield value per floor or district, triggered by that floor's door or a timed cascade (recipe C). This gives "the tower wakes up floor by floor" without touching lighting states. The lighting-state side is in [02](02_power_and_states.md).
5. **Keep FX lights shadowless** (`PRIMARY_NOSHADOWMAP 1`). The map's omni shadow slices are the default 24, and the user's own config turns dynamic light shadows off anyway.
6. **For reflections of fixed animated lamps**, add a `PROBE_ONLY` Radiant twin in the lamp's colour (the Giant pattern). The `.map` is generated, so the twin belongs in tools/gen_tower_map.js, and it is a full build. Not possible for the scattering perk machines.
7. **Halos and flares are optional seasoning.** On a dark map a small halo reads from far away cheaply; keep halos small and off the player's camera. Lens flares are unproven in a usermap: try one in the test map first.
8. **Before any new effect,** run the vetting checklist (recipe E), author map-owned `.efx` under repo `share/raw/fx/tod/`, zone and precache it, and add a dev log. Build (the right build type is in [section 9](#9-playing-fx-from-script)) and stop. Never build while BO3 is running. The user tests.

Open questions for the in-game test plan ([10](10_troubleshooting_limits_history.md#7-open-questions-and-the-test-plan)): the numeric FX spot-light limit; whether overlapping FX lights add; whether bare server one-shot `PlayFX` renders (controlled A/B); whether placed fx entities need zone lines; whether Radiant exploders replay for hot-joiners; whether `cg_usingClientScripts` is set in usermaps (server `stop_exploder`); whether FX lights honour `culling_cutoff/falloff`; why far-away effects did not appear on approach; whether `info_corona` and lens flares render; whether the engine honours the Wraith spelling `PRIMARY_TYPE OMNI/SPOT`; and what actually caused TOD1's child-FX hang, given that the linker packs child effects on its own.

---

## Sources

Official Treyarch documents (MODTOOLS/docs_modtools):
- FX_Lights.pdf — FX-light workflow, curves versus keys, loop rule, exploders, shadow and per-instance limits.
- FX_QuickStart.pdf — creating, placing and previewing effects.
- Lighting_Parameters.pdf — light keys, cookies, ShadowmapScale and the 12-live-shadow budget.
- Culling_LOD_Lights.pdf — `culling_cutoff` / `culling_falloff` starting values.
- Materials.pdf — Effect Lit Blend / Effect Lit Emissive (intensity scale, physically based emissive, compute sprites, falloff angles).
- SunSky_Light_SetUp.pdf — Export Local Probes to see exploders.
- Scale_Standards.pdf — 1 inch = 1 unit.
- PhysicallyBasedRendering.pptx — particle vertex lighting (slide 5); transparency cost (slide 15).
- bo3_scriptapifunctions.htm — PlayFX, PlayFXOnTag, PlayLoopedFX, SpawnFX, TriggerFX, StopFX, KillFX, SetFXIgnorePause, SetFXOutdoor, SetForceNoCull, radiant exploder functions.

Stock data and scripts (MODTOOLS):
- bin/t7.def.json — `fx`, `light`, `worldspawn`, `lensflare`, `klf`, `info_corona` classes.
- bin/radiant_modtools.exe (strings) — FX element, spot-light, shadow, lens-flare and exploder limits.
- share/raw/fx — `light/*`, `lensflares/*`, `zombie/fx_perk_*`, `zombie/fx_powerup_on_*`, `dirt/fx_dust_*`, `env/light/*` (stubs) and the rest of the catalog.
- share/raw/lensflares/*.klf — lens-flare assets.
- share/raw/scripts/shared/exploder_shared.gsc/.csc, fx_shared.gsc, load_shared.gsc.
- share/raw/scripts/zm/zm_giant.gsc, zm_giant_fx.csc, _zm_perks.gsc/.csc, _zm_perk_quick_revive.gsc, _zm_trap_electric.csc, _zm_powerups.csc, _zm_perk_random.csc, zm_usermap.gsc/.csc.
- map_source/_prefabs/zm/zm_giant/zm_giant_light.map, geo/lantern_lit.map; map_source/zm/zm_giant.map; map_source/_prefabs/zm/zm_core/vending_*.map; map_source/_prefabs/mp/mp_sector/fx/mp_sector_fx.map and mp_combine/fx/mp_combine_fx.map (`klf` entities).
- deffiles/ssi.awi — the SSI sun lens-flare fields.
- source_data/black_ops_3_fx.gdt — the few halo-material variants that have local source.

Build output and local config:
- C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\zone_source\all\assetinfo\zm_tod2_cybercity.csv and .deps (2026-09-24) — what the linker packed, with parent chains; proves the two stubs and the child effects were packed.
- Call of Duty Black Ops III\players\config.ini (the user's game config) — `VolumetricLightingEnabled 0`, `DisableDynamicLightShadows 1`.

This repository:
- share/raw/fx/acc/light/fx_perk_glow_*.efx, share/raw/fx/tod/*.efx, share/raw/fx/tod/teleporter/*.efx, share/raw/fx/tod/bo6/*.efx.
- tools/gen_tod_inducer_fx.py, tools/sync_to_modtools.ps1.
- scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc/.csc, _tod_rampage.gsc, _tod_teleport.gsc, _tod_atmosphere.gsc, _tod_upgrades.gsc.
- zone_source/zm_tod2_cybercity.zone; map_source/zm/zm_tod2_cybercity.map.
- CLAUDE.md; docs/143_panzer_flame_fx.md; docs/154_tod2_isolation.md; docs/155_fx_art_workflow.md.

Project history and memory:
- abandoned_cyber_city_zombies/docs/44_scientist_boss_and_teleport_fx.md; _acc_perk_lights.gsc; _acc_atmosphere.gsc; its map_source/zm/zm_abandoned_cyber_city.map and TOD1's map_source/zm/zm_tower_of_doom.map (no fx entities or exploder members).
- Project memories: `stub-efx-in-mod-tools`, `ambient-fx-server-loop-lane`, `fx-embedded-light-def-freeze`, `server-playfx-does-not-render`.

Community:
- https://forum.modme.co/wiki/threads/2403.html — the Wraith-extracted FX library and its placeholders.
- https://forum.modme.co/wiki/threads/1241.html, https://forum.modme.co/wiki/threads/3644.html, https://www.ugx-mods.com/forum/scripting/87/trigger-fx-after-turning-on-power/13761/ — zone line + precache.
- https://www.ugx-mods.com/forum/mapping/88/cant-get-light-shafts-god-rays-to-work/12832/ — volumetric shafts with `volume_litfog`.
- https://github.com/dtzxporter/ModmeForum (archived threads 459, 496, 1883, 1928, 3170, 3280) — FX-light draw distance, `fast_restart`, flashing omni FX, searchlights, omni flicker, FX limits.
- https://steamcommunity.com/app/455130/discussions/0/1457328392112627908/ — Radiant hides FX when many are placed.
