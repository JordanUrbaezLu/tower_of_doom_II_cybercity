# 10 — Troubleshooting, limits, build rules, lessons and the test plan

**In short.** Start here when lighting looks wrong, and check here before you change anything. This chapter turns the gotchas from chapters 01–09 into symptom tables, lists the hard limits and budgets with how sure we are of each, and states the build and bake rules this repo enforces. It then records the lessons Map One, Tower of Doom and Tower II already paid for, including repo records that this reference now contradicts. It ends with every open question turned into a prioritised test plan. Nothing in this reference was tested in game, and the first two builds of that plan decide whether Tower II's 344 lights and its sun settings are doing what everyone assumed.

**Read this when…** something looks wrong in a build or in game; before a lighting change, to know which build it needs and what it can break; before you claim how something works; or when you pick the next lighting test.

Tags used on every non-obvious claim: **[VERIFIED]** read in an official Treyarch doc, stock script, stock data file or the engine API list (or measured from our own files); **[COMMUNITY]** forum, tutorial or other mapper — written **[COMMUNITY: project record]** when the source is this project's own recorded observation (a doc, CHANGELOG or memory entry, not an official source); **[INFERRED]** reasoned, not seen; **[TEST]** needs an in-game or bake test to settle.

> **Current map state (2026-09-24).** Since THE FALL (docs/160_the_fall.md; full build 2026-09-24 00:06 Eastern, unplayed) the party spawns in the **crown hall** and descends; the Vault is the bottom of the run, the finale is parked and the Endless Spire is not reached. **Power is on from the first frame**: `_tod_fall::power_on()` calls stock `zm_power::turn_power_on_and_open_doors()`, which changes no lighting state [VERIFIED scripts]. So the current build has no "before power" period at all. Tests below that need a lighting moment use a scripted trigger instead of the power switch.

## Contents

1. [Triage: six questions before you change anything](#1-triage-six-questions-before-you-change-anything)
2. [Symptoms, likely causes and fixes](#2-symptoms-likely-causes-and-fixes)
3. [Limits and budgets](#3-limits-and-budgets)
4. [Build and bake rules in this repo](#4-build-and-bake-rules-in-this-repo)
5. [Lessons this project already paid for](#5-lessons-this-project-already-paid-for)
6. [Records this reference contradicts](#6-records-this-reference-contradicts)
7. [Open questions and the test plan](#7-open-questions-and-the-test-plan)
8. [For Tower of Doom II](#8-for-tower-of-doom-ii)
9. [Sources](#9-sources)

---

## 1. Triage: six questions before you change anything

**Plain version.** A BO3 frame gets its light from several separate systems: baked `light` entities, emissive (self-glowing) materials, FX lights played by script, reflection probes (which carry both reflections and bounce light), the sky and sun, and a final colour grade. This project has mixed them up several times. The yellow tower (docs/107) cost six builds of the wrong fixes. Before touching a value, answer these six questions. Each one rules out a whole family of causes.

1. **Is the bake fresh?** A `-GscOnly` build never relights [VERIFIED, tools/build_map.ps1:913-915]. After a full build, the log must say `fresh LED: N bytes`. The script refuses a `.led` that is missing, older than the bake start or under 1 MB [VERIFIED, tools/build_map.ps1:897-909]. The file is `C:\BO3Tools\TOD2Cybercity\share\raw\maps\zm\zm_tod2_cybercity.led`. On 2026-09-24 00:03 (THE FALL's full build) it was 50,487,469 bytes. A sudden size change with no lighting edit is a fingerprint worth chasing (docs/107 used exactly that). A stale or deleted `.led` produces black or white surfaces (§2.8).
2. **Which lighting state is live?** Stock `zm_usermap::main` sets script state 1 and nothing in Tower II changes it [VERIFIED: share/raw/scripts/zm/zm_usermap.gsc:110; grep of our `scripts/`], so the game sits in script state 1 all match. By the strongly supported mapping, that is Radiant State 2 [INFERRED; see [02 §2](02_power_and_states.md#2-radiant-state-n-and-script-state-n)]. Do not guess this in a playtest: log it (test T1).
3. **What does the sun volume give that state?** The `volume_sun` sets only `ssi1` (plus a key `ssi` that is not in the entity definition). The compiled `.led` lists `default_day` for Radiant States 2–4 [VERIFIED decode]. What the engine actually shows in Radiant State 2 is [TEST] (T2).
4. **Which source is it?** Ask what the thing does when the lighting changes (a state switch, an exploder, the power in a build that gates on it), and whether it moves.
   - A glow on a surface that never changes with the lighting state is the **emissive material** ([03 §4](03_glow_and_perks.md#4-does-an-emissive-surface-light-up-the-room)).
   - A pool that changes with the state is a **baked light** ([01](01_lights.md)).
   - Something that flickers, pulses or moves is an **FX light** ([04](04_fx_lights.md)).
   - Colour that shows only in reflections, or tints guns and zombies everywhere, is a **probe or the global probe** ([06](06_reflections_probes.md)).
   - A whole-map tint that follows the sky is the **sky light, sun or exposure** ([05](05_sun_sky_exposure_fog.md)).
5. **Same spot, same state, against a known-good build.**
   - docs/107's reference spot (TOD1) is beside the ammo crate against the base's east wall, round 1, before power. In Tower II today that plaza is the end of the descent and power is already on, so use it as a fixed spot, not a "before power" one.
   - Also take the crown hall, where Tower II now spawns (docs/160_the_fall.md), and the Vault at the bottom (docs/158).
   - Tower II is unpublished, so the "good" reference is the previous build's screenshots.
   - For the TOD1 look, the published TOD1 build is on disk (docs/107 "Lessons").
6. **Which graphics settings?** The user's own `players/config.ini` has these values [VERIFIED, read 2026-09-24]:
   - `VolumetricLightingEnabled 0`
   - `DisableDynamicSunShadows 1`
   - `DisableDynamicLightShadows 1`
   - `SSAOTechnique Disabled`
   - `TextureQualityBakedSunShadows 2`, the lowest of 0–2

   The file's own comment says the sun-shadow value is a mip drop where lower numbers are higher quality, so 2 is the lowest. The user's playtests therefore never show volumetrics, dynamic shadows or SSAO. Judge lighting on a low **and** a high config ([09 §7](09_design_and_inspiration.md#7-how-to-judge-lighting)).

---

## 2. Symptoms, likely causes and fixes

Each row gives the most likely cause first. The last column names the chapter that explains the mechanism. Test IDs (T1…) point to §7.

### 2.1 Lights and lighting states

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| Lights meant to be "off before power" are on from spawn and never change (Tower II today, [INFERRED]; T1 settles it) | `zm_usermap::main` calls `level util::set_lighting_state( 1 )` (share/raw/scripts/zm/zm_usermap.gsc:110) [VERIFIED]. By the mapping, script state 1 = Radiant State 2 [INFERRED]. Every Tower II light is `lightingstate1 0 / 2–4 1`, and no Tower II script changes the state [VERIFIED]. Stock power (`_zm_power.gsc`, also what THE FALL calls at the first frame) changes no lighting [VERIFIED] | Pick one convention (Giant or Map One), author masks to match, and confirm with T1 first | [02](02_power_and_states.md) |
| Power flips the wrong set: lit before power, dark after | Off-by-one: someone read "script state 1" as Radiant State 1 | Script state n shows Radiant State n+1 [INFERRED, strongly supported by The Giant and Map One] | [02](02_power_and_states.md) |
| Adding `set_lighting_state( 0 )` at power makes Tower II darker | None of the 344 lights is in Radiant State 1. The same call also switches the level's global lighting to Radiant State 1's sun-volume entry [INFERRED] | Remap the masks first (Giant: powered lights in Radiant State 1, pre-power lights in Radiant State 2) | [02](02_power_and_states.md) |
| A state switch does nothing, or a state's lights never appear | Community reports: the `volume_sun` had no real SSI for that state [COMMUNITY]. Unset slots are written into the `.led` as `default_day` [VERIFIED] | Fill `ssiN` for every state you use with a real SSI. The same SSI in two states is fine (The Giant: `zm_factory` in ssi1 and ssi2; Map One: `acc_ssi_night_dim80`) [VERIFIED] | [05](05_sun_sky_exposure_fog.md), T2 |
| Radiant camera shows `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE` | The string exists in Radiant [VERIFIED]. Reading it as "that state has no SSI" is [INFERRED] | Fill `ssiN` for that state | [05](05_sun_sky_exposure_fog.md) |
| Light shines through walls, or a pool spills onto the floor above or below | `PRIMARY_NOSHADOWMAP` defaults to 1 = no shadow map [VERIFIED def]. Shadowless lights are not blocked by walls [COMMUNITY, modme 2987]. All 344 Tower II lights are shadowless with radius 200–900 against a 384-unit lap rise [VERIFIED data; spill INFERRED] | Static shadows (`PRIMARY_NOSHADOWMAP 0` + `shadowUpdate Never`), a tighter `radius`, `cut_on` / `far_edge` | [01](01_lights.md) |
| A light seems to do nothing | Its origin sits inside a solid brush (caught twice on the crown) [COMMUNITY: project record]. Or its radius is tiny next to the object (a 900-unit light on a 4096-unit crown). Or `stops` is far below exposure (day SSIs need ~14 [COMMUNITY]). Or it is in no active state (stock perk prefabs are all `0000` [VERIFIED data]). Or `culling_cutoff` is too aggressive | Move the origin into open air; compare `stops` with the exposure; tick the live state | [01](01_lights.md) |
| Raising `bake_intensity_scale` barely changes the pool | The def calls it "brightness of a light for GI baking" [VERIFIED]. Whether it leaves the direct light alone is [TEST]. Treyarch never sets it (0 of 543 Giant lights) [VERIFIED] | Use `stops` for the direct pool (+1 stop = 2× [INFERRED from stock values]) | [01](01_lights.md), T5 |
| Lights pop or fade out at distance | Screen-space LOD `culling_cutoff/falloff`, or an FX light's `spawnRange` | Doc starting values: 200/300 px, and 1/5 for radius < 10 [VERIFIED Culling_LOD_Lights] | [01](01_lights.md), [04](04_fx_lights.md) |
| Everything looks like shiny plastic | Light specular highlights | Negative light `spec_comp`: The Giant uses −1..−6 on 38 lights [VERIFIED], community used −10 [COMMUNITY, modme 293] | [01](01_lights.md) |
| Spot light is blocky or has artifacts | `fov_outer` above 120° [VERIFIED Lighting_Parameters p.2] | Keep ≤ 120, or use two spots | [01](01_lights.md) |
| The power-on flip is an instant pop | No fade exists for a light-state switch [INFERRED: no argument or key found]. `volume_sun transitionTime` exists for sun states [VERIFIED key; effect TEST] | Map One's trick: `VisionSetNaked(dark grade, 0)` just before the flip, then lerp back over ~10–15 s. Or use FX lights with authored ramps | [02](02_power_and_states.md), T15 |
| "The whole tower lights up at once" at power | A lighting state covers the whole map, and the level call applies it to every player (share/raw/scripts/shared/util_shared.gsc:2975-3002) [VERIFIED] | Use per-floor exploders or FX lights driven by a world clientfield | [02](02_power_and_states.md), [04](04_fx_lights.md) |
| Stock perk-prefab lights never light | All 49 lights in `zm_core/vending_*` are `lightingstate 0000` [VERIFIED data]. Quick Revive, Mule Kick and Stamin-Up lights sit in exploders, but stock script fires only `quick_revive_lgts` (`_zm_perk_quick_revive.gsc:185`; in solo it fires at load, not at power) [VERIFIED]. Whether a fired exploder light with all four states off shows at all is not documented [TEST] | Enter the prefab and tick states, or fire the exploder yourself [COMMUNITY]. Tower II uses its own FX glow instead | [03](03_glow_and_perks.md) |
| `SetLightIntensity` and friends have no effect | The light must be `scriptable` + `client_server ServerSide`. All Tower II lights are `ClientSide` [VERIFIED]. No stock script calls the API, and the community calls it deprecated [COMMUNITY] | Prefer states, exploders or FX; T26 before relying on it | [01](01_lights.md) |
| A per-player lighting state reverts | `_globallogic_spawn.gsc:501` re-applies `level.lighting_state` on every spawn [VERIFIED] | Re-apply in an on-spawned callback, or keep lighting level-wide | [02](02_power_and_states.md) |
| A co-op player who joins late lacks exploder lights | A server `exploder::exploder` is a one-shot command. Replay for joiners is unverified [INFERRED] | Drive client exploders from a world clientfield callback (the stock trap pattern, `_zm_trap_electric.csc:20-37`) | [02](02_power_and_states.md), T12 |
| Cookie (gobo) never appears | `ENABLE_COOKIE` (named in the docs) does not exist in the shipped tools or stock data [VERIFIED absence]. Stock cookie lights set `def` alone [VERIFIED data], so `def` is the whole switch [INFERRED]. Radiant errors on a wrong-size or missing light def [VERIFIED strings]. All 21 stock cookie images are 512² [VERIFIED] | Set `def` to a light asset whose image is 512²; read the Radiant error | [01](01_lights.md), T22 |

### 2.2 Brightness, exposure and colour cast

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| Map too bright, washed out, flat | Several stacked causes:<br>(a) every visible face is emissive-class [VERIFIED]<br>(b) all 344 lights are on [INFERRED]<br>(c) sky light: `skyStops 10.0` against stock `default_night`'s 4.4 [VERIFIED values; the 5.6-stop comparison INFERRED, image content matters]<br>(d) the global probe lights almost everything [INFERRED]<br>(e) Radiant State 2 may run on `default_day` (EV 1–16, sun stops 14) [TEST] | Run the P0 tests before you touch anything. Then: less emissive area, lower `skyStops` or `--target-score`, a clamped exposure, fitted probes | [03](03_glow_and_perks.md), [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md) |
| Yellow-olive cast on everything, including gun, hands and zombies | docs/107: the sun volume shrank when the spire went from 100 to 70 laps, and the whole tower turned yellow [COMMUNITY: project record, bisected]. Its mechanism was never found. Candidates:<br>- the untargeted global probe sits at the volume centre and moved [VERIFIED doc rule; cause INFERRED]<br>- the grid spacing changed [INFERRED]<br>- the Radiant State 2 `default_day` entry (warm `1 0.976 0.949`) [TEST]<br>Other known olive sources: a warm light on `$white_diffuse` (docs/104 §4d), and a sky-light score of ~4.0 on dark albedos (docs/104 §4) | Keep `SUN_VOLUME_TOP_MIN`; read the generator's `ceiling` print; diff the worldspawn and the derived numbers; T3 | [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md) |
| A dark area reads grey and muddy | Auto-exposure brightens darkness when the clamp is wide [INFERRED from the MP doc and the stock night SSIs] | Clamp `evmin/evmax` on every state's SSI. Stock nights: `zm_factory` 0.5–3.5, `default_night` 3–3.5, `zm_zod` 4–6 [VERIFIED] | [05](05_sun_sky_exposure_fog.md) |
| Zombies can't be seen; black crush | Lights far under exposure; no fill; black `global_fill_color`; a heavy grade | Fill 2–3 stops under the key [INFERRED]; keep a bright background for silhouettes ([09](09_design_and_inspiration.md)); stock eye-glow overrides exist [VERIFIED `_zm.csc`] | [05](05_sun_sky_exposure_fog.md), [09](09_design_and_inspiration.md) |
| Pure-black pockets in occluded places | `volume_sun global_fill_color` defaults to `0 0 0` ("should match the average ground color") [VERIFIED def; as the cause, INFERRED] | A/B it near the average ground colour in its own build [TEST]; every shipped Treyarch sun volume keeps `0 0 0` | [05](05_sun_sky_exposure_fog.md) |
| Interior as bright as outdoors; sun leaking under walls | No fitted probe; coarse sun shadows; shadowless lights | Fit a probe into the walls; use `caulk_shadow` / shadowcaster brushes; lower `shadowSplitDistance` (a dynamic-shadow setting: the Giant uses 900, Map One 800 [VERIFIED data]; community values 250–750, and "it stops sun bleeding" is community-only [COMMUNITY]). The user's config turns dynamic sun shadows off | [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md) |
| Probes make a dark outdoor area brighter in game than in Radiant | Unresolved in community threads (modme 329/383) [COMMUNITY] | Try a negative probe `brightnessAdjust` (bounce darker, range −5..5). The community dark map zm_alien_isolation uses `brightnessAdjust −5` on 12 probes and `evcomp −5` on 11 [COMMUNITY: its published map source]. Treyarch's MP doc says to avoid `evcomp` on probes [VERIFIED] | [06](06_reflections_probes.md) |
| Screen goes grey after a revive, or a tint keeps returning | The client keeps re-applying the map-name `.vision` [VERIFIED `visionset_mgr_shared.csc`] | Keep `vision/zm_tod2_cybercity.vision` neutral; grade through another vision or a LUT | [05](05_sun_sky_exposure_fog.md) |
| White halos around neon or the sky | Lit edges in the sky picture sat ~200× above the sky's base brightness, and the engine's bloom turned each into a white halo (TOD1, v18.97) [COMMUNITY: project record, docs/104 §4k]. Emissive scale far above 2^EV of the area [INFERRED] | Keep the sky knee (`--knee 0.45 --knee-max 0.62`); set emissive `scaleRGB` near 2^EV of the area | [03](03_glow_and_perks.md), [05](05_sun_sky_exposure_fog.md) |
| An olive or tinted pool under one light | The light's colour paints the `$white_diffuse` colour map under the emissive layer [COMMUNITY: project record, docs/104 §4d] | Neutral key lights, or a dark albedo where the surface should stay black | [03](03_glow_and_perks.md) |
| A new SSI has no sun | `ssi.awi` defaults `colorSRGB` to `0 0 0` [VERIFIED] | Clone a stock SSI instead of starting blank | [05](05_sun_sky_exposure_fog.md) |
| Placed lights vanish under a daytime sky | Day exposure is far higher; lights need ~14 stops [COMMUNITY, modme 477] | Raise `stops` or use a darker SSI | [05](05_sun_sky_exposure_fog.md) |
| Lighting or sky broken on a fresh tools install | Windows decimal separator set to a comma [COMMUNITY, UGX 12772] | Set `.` and reinstall the tools | [05](05_sun_sky_exposure_fog.md) |

### 2.3 Glow, emissive and perks

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| The tower cannot be made dark before power | Every visible brush face uses an emissive-class material (66,390 in the current map) [VERIFIED]. The glow is constant; no `*_script` techset is used [VERIFIED]. World brush faces carry no entity keys, so they cannot be state-gated [INFERRED]. About half glow only on thin grid lines; the rest have a ~0.2 grey fill that glows across the face [VERIFIED measurement] | Move large surfaces to non-emissive or dim map-owned materials; keep emissive for accents; put anything that must switch on an entity | [03](03_glow_and_perks.md) |
| Emissive glow does not switch with power | Emissive does not follow lighting states on its own [INFERRED; the Materials doc's lampshade advice implies it, p.16-17] | Three routes:<br>- entity `SetModel` to an `_on` twin made with `skinOverride` (the inducer; BO7 perks) [COMMUNITY: project record, user-approved]<br>- `lit_emissive_script` + client `MapShaderConstant` / `SetShaderConstant` (stock Der Wunderfizz, `_zm_perk_random.csc:104`) [VERIFIED stock use; ours TEST]<br>- a backlit lampshade material with a real light behind it [VERIFIED doc] | [03](03_glow_and_perks.md), T16 |
| A sign or strip glows, but the wall around it stays dark | No doc, material field or `lit_emissive` render flag makes an emissive surface a bake light source [INFERRED from absence]. The sky material is the one documented emissive light source [VERIFIED]. Whether a probe that sees emissive picks it up as bounce is [TEST] | Pair every glow that should light things with a light or an FX light | [03](03_glow_and_perks.md), T4 |
| A `lit_emissive` material glows white over its whole surface | A blank emissive map defaults to `$white_diffuse`, so the whole face glows at `scaleRGB` (default 8) [VERIFIED `emissive_base`] | Paint non-glowing parts full black (Materials.pdf p.18) | [03](03_glow_and_perks.md) |
| Glow too strong or blooming | `scaleRGB` above 2^EV of the area. Tower II's SSI clamps EV 3–3.5 (→ ≈8–11) while plain grid faces use 15 [VERIFIED values; comparison INFERRED] | Halve `scaleRGB` for about −1 stop [INFERRED from the 2^EV rule] | [03](03_glow_and_perks.md) |
| Flicker fields do nothing | Flicker parameters exist only on `flicker_base` techsets (the `lit_emissive_scroll*` family and some decals/specialty) [VERIFIED] | Switch to a scroll type, or flicker with an FX light | [03](03_glow_and_perks.md) |
| A scroll material flickers when it should not | Defaults are `flickerMin 0 / flickerMax 1`; the vertigo pack sets min = max = 1 on its steady scroll materials [VERIFIED data; behaviour TEST] | Set min = max = 1 | [03](03_glow_and_perks.md), T25 |
| The spec map is ignored on an emissive prop | `lit_emissive_plus` has no `specColorMap` slot [VERIFIED techsets] | `lit_emissive_advanced` or `_advanced_fullspec` | [03](03_glow_and_perks.md) |
| Glowing floors or doors show a smeared mirror | Vertigo materials use `$white_specular`, gloss up to 15–16 and `reflectionProbeAmount 1` [VERIFIED], and our probe boxes are tiny | Map-owned matte clones (the `tod_door_*` pattern) plus fitted probes. Lower gloss, never zero it (the altar lesson L27) | [03](03_glow_and_perks.md), [06](06_reflections_probes.md) |
| A stock perk "glow" lights nothing around the machine | Stock server `_zm_perks.gsc::perk_fx` plays `level._effect[<perk>_light]` with `playfxontag` 3 s after power; those `zombie/fx_perk_*_zmb` effects are billboard sprites with 0 `dynamicLight2` [VERIFIED], so they light nothing [INFERRED]. The `*_factory_zmb` variants hold 6–15 lights each [VERIFIED]. `zm_usermap.gsc` `perk_init()` would swap them in server-side but is never called; client-side, `zm_usermap.csc` `include_perks()` assigns the factory variants to the handles the ~3 s client power-on flicker uses, and each perk's `.csc` init sets them back when `level.enable_magic` is true [VERIFIED code; call order INFERRED] | Use a glow FX that carries a light (our `acc/light/fx_perk_glow_*`), or add lights | [03](03_glow_and_perks.md), [04](04_fx_lights.md) |
| A stock perk machine looks the same after power | Stock `off_model == on_model` for every perk [VERIFIED `.gsh`] | Supply a real `_on` model | [03](03_glow_and_perks.md) |
| A new material renders as the default | Names over 63 characters are truncated and silently substituted; invented names are substituted [COMMUNITY: project record]. `lint_tod_geometry.js` fails the build on a face material missing from its `MATERIALS` map [VERIFIED tools/lint_tod_geometry.js:114] | Short, verified names (the project caps at 32); add them to the lint | [03](03_glow_and_perks.md) |
| A transparent emissive tanks the frame rate | Overdraw and OIT: "Transparency is the single fastest way to ruin our framerate" [VERIFIED PBR deck] | Opaque, alpha-test or backlit instead | [03](03_glow_and_perks.md) |

### 2.4 FX lights

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| An effect is zoned and precached but shows nothing | The source `.efx` is a placeholder stub. 241 local `.efx` use `gfx_debug_missing_fx` (238 identical 5,092-byte files) [VERIFIED]. Zoning one packs a blank [COMMUNITY: project record — TOD1's zoned Trailblazer stub was blank]. Tower II zones two: `zombie/fx_thundergun_smoke_cloud` (zone:431) and `env/light/fx_light_god_rays_dust_motes` (zone:451, the lounge motes) [VERIFIED] | Grep before zoning; swap in a vetted real source | [04](04_fx_lights.md), T9 |
| `PlayFX` / `PlayFXOnTag` silently does nothing | Missing zone `fx,` line or `#precache` [COMMUNITY recipe; "silently" is the project's observation]. The zone line is needed only for effects no base-game zone already loads [COMMUNITY: project record] | Always add all three: the `fx,` zone line, `#precache` (`fx` in GSC, `client_fx` in CSC), and the `level._effect` entry | [04](04_fx_lights.md) |
| A server-played effect is invisible | "A server one-shot PlayFX renders nothing" is a project heuristic from a confounded Map One test, not an engine rule [INFERRED]. Stock uses server `PlayFX` at 72 live call sites [VERIFIED]. A same-frame host spawn is a suspected risk (docs/143) [COMMUNITY: project record] | Proven lanes: a looping FX on a server-spawned `tag_origin` host, emitted two frames after spawning it; or a clientfield → CSC `PlayFXOnTag` | [04](04_fx_lights.md), T14 |
| A far-away glow never appears as you walk up | A latched clientfield FX spawned far from the viewer [COMMUNITY: project record] | Re-pulse the field on first approach (`TOD_GLOW_REKICK_DIST 700`) | [04](04_fx_lights.md) |
| A looping FX light is too bright or its pulse is mushy | Spawn interval shorter than lifetime overlaps particles. All 17 `acc/light/fx_perk_glow_*` (10 of them copied into this repo) and both inducer FX loop every 200 ms with a 1000 ms life, so ~5 lights at once [VERIFIED files; effect INFERRED]. About 78% of stock looping FX lights (1,489 of ~1,906) use interval = lifetime [VERIFIED count] | Set `spawnLooping` = `lifeSpanMsec` (FX_Lights.pdf). The user approved the current inducer look, so A/B it first | [04](04_fx_lights.md), T10 |
| An FX light randomly goes black | Interval longer than lifetime [VERIFIED doc rule]. The teleporter charge/release fields (5000/700, 5000/650) are fine only as one-shots | Match interval to lifetime | [04](04_fx_lights.md) |
| FX light brightness or size is not what its KVPs say | The Visuals graphs override the KVP block for intensity, radius and FOV [VERIFIED doc: "main" controls]. The perk glow's radius graph is 60 while its KVP says 100 [VERIFIED file] | Tune `lightIntensityGraph` / `lightRadiusGraph` / `lightFovGraph` | [04](04_fx_lights.md) |
| Frame-rate loss or dropped shadows with FX lights | FX lights cannot use `Never` shadows; they are Always live or Off [VERIFIED FX_Lights p.2]. 88% of stock FX lights set `PRIMARY_NOSHADOWMAP 1` [VERIFIED count] | `PRIMARY_NOSHADOWMAP 1` by default | [04](04_fx_lights.md) |
| Some FX spot lights or elements don't spawn under load | `FX_SPOT_LIGHT_LIMIT` (value unknown) and `FX_ELEM_LIMIT(4096)` [VERIFIED Radiant strings; game behaviour INFERRED] | Fewer, larger effects; enable per zone [COMMUNITY, modme 3280] | [04](04_fx_lights.md) |
| A reflection shows no lamp where an FX light flickers | FX lights are runtime particles and not in the baked probes [INFERRED] | Add a `PROBE_ONLY` primary twin. The Giant does this: 67 of its 94 light-FX placements have a PROBE_ONLY light within 12 units — a strong pattern, not an invariant [VERIFIED count] | [04](04_fx_lights.md), [06](06_reflections_probes.md) |
| A looping tag FX won't stop from server script | There is no server StopFX for tag-played effects [VERIFIED API list] | Delete the host; on the client, `StopFX` (lets particles finish) or `KillFX` | [04](04_fx_lights.md) |
| Freeze or `Com_ERROR` on first render near a new FX | `pcloud` materials [COMMUNITY: project record, not a veto: Tower II renders several pcloud effects]; a weapon/projectile effect naming a child effect (one TOD1 black-screen hang, cause never isolated; the linker ledger shows children of zoned effects are packed automatically) [COMMUNITY] | Run the vetting greps in [04](04_fx_lights.md) | [04](04_fx_lights.md) |
| FX lights stop after `fast_restart` | [COMMUNITY, modme 496] | Restart from the menu | [04](04_fx_lights.md) |
| A lens-flare effect links but never shows | Three stock flare `.efx` reference UUIDs with no `.klf` [VERIFIED]; `spawnRange`; occlusion | Use a flare whose UUID maps to a `.klf` | [04](04_fx_lights.md) |

### 2.5 Reflections and probes

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| Reflections smear or look the same everywhere; guns, zombies and walls share one cast | The 53 probes are the template default: `size_min/size_max 72` are half-extents, so each is a 144-unit cube [VERIFIED]. Most float ~140–150 above their floors (the crown and shaft probes differ), and no box reaches a floor. There are no reflection planes [VERIFIED]. So nearly every surface takes ambient and reflection from the global probe [INFERRED]. That probe sits at the box centre (0,0,19478), inside the brush `mast tier 1` [VERIFIED location; effect INFERRED] | Fit boxes to rooms and add reflection planes; target the global probe at an `info_null` in open air | [06](06_reflections_probes.md), T3, T18 |
| Coverage reasoned from `radius 2048` on a probe | `radius` is not a `reflection_probe` key in `bin/t7.def.json` [VERIFIED]; it is most likely inert [INFERRED] | Size with `size_min/size_max` | [06](06_reflections_probes.md) |
| "The whole lighting goes super bright outside a probe" | Leaving local coverage exposes the global probe; one mapper's centre was inside a building [COMMUNITY, modme 3307] | Overlap probes by their blend; move the global probe | [06](06_reflections_probes.md) |
| Neon reflections weak on a wet floor in a dark room | Treyarch's reflection brightness correction is a soft cap: where the pixel's baked diffuse GI is low compared with the reflected brightness, the reflection is strongly damped; where GI is high it passes almost unchanged [VERIFIED SIGGRAPH 2016 talk; that retail BO3 runs it exactly so, INFERRED]. A point light has no visible body in a cubemap [INFERRED] | An emissive fixture the probe can see; `PROBE_ONLY` lights or probe `brightnessAdjust` nearby | [06](06_reflections_probes.md) |
| Zombies and moving things never appear in reflections | Reflections are baked cubemaps. SSR flags exist only on the `lit_water_sim*` family and `water_shore*_igc` [VERIFIED flags; "no SSR elsewhere" INFERRED] | Accept it; use water SSR only where it matters. A script-driven mirror route exists (`specialty/lit_extracam_reflection` + client `SetExtraCam`), unused by any stock material and untested in a usermap [VERIFIED techset; TEST] | [06](06_reflections_probes.md), [07](07_water.md) |
| A probe change does not show | Probes are baked by Radiant's Lighting Export, which writes the LED [VERIFIED SunSky doc] | FULL build | §4 |
| Reflections or bounce carry a fog tint the scene doesn't have | Fog is baked into probes (`probebakeworldfogdensityscaler`, default 1) [VERIFIED keys]. Tower II's worldspawn fsi is `zm_factory_volumetric` while script turns tower fog off at runtime [VERIFIED; the tint effect INFERRED] | T19 | [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md) |
| Frame cost rises where probes overlap | Shader variants for 1 / 2 / 3+ visible probes; override probes still count [VERIFIED Priority_Probes, deferred.csdef] | Small blends; few overrides | [06](06_reflections_probes.md) |
| A subtract child has no effect | `subtract` is ignored on the parent probe [VERIFIED] | Put it on a child that targets the parent | [06](06_reflections_probes.md) |
| Radiant runs out of memory after probe debugging | Debug rays stored on many probes [VERIFIED doc] | The doc says to set `debug_render_index_x` back to zero afterwards, but (0,0,0) is itself a valid grid point and the def's default is 64, its maximum [VERIFIED def]. An out-of-range value such as our 64 probably stores no rays [INFERRED] | [06](06_reflections_probes.md) |
| After a lighting-state switch (for example at power), reflections look unbaked or wrong | Radiant keeps probe data per lighting state [VERIFIED field names; meaning INFERRED], and the state may lack an SSI | Set `ssiN` for every state; check both states after gating | [06](06_reflections_probes.md), T11 |
| Light leaks through the solid core | GI voxels inside geometry are invalidated and in-painted [VERIFIED talk] | Multiface or subtract shapes; virtual probes for visibility | [06](06_reflections_probes.md) |

### 2.6 Volumes, fog, post and exposure

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| A new `pbg_box` / `vlut_box` / `vbloom_box` / `vcolor_*` has no effect | These default to `LIGHTSTATE_1` only [VERIFIED def], and a usermap runs Radiant State 2 [INFERRED] | Tick `LIGHTSTATE_2`, and every state the volume should apply in | [02](02_power_and_states.md), [05](05_sun_sky_exposure_fog.md), T7 |
| `volume_performance` seems ignored | Same default: `LIGHTSTATE_1` only [VERIFIED def] | Same fix | [01](01_lights.md) |
| An exposure volume does not change with the lighting state (or power) | `volume_exposure` has no LIGHTSTATE flags. It uses `BANK_1..4` plus client `SetExposureActiveBank` [VERIFIED def/API; no stock ZM caller] | Use banks, or per-state SSI exposure | [05](05_sun_sky_exposure_fog.md) |
| An exposure volume changes compensation but not the clamp | `evmin/evmax` are "only used if not set to the default" −32/31 [VERIFIED def] | Set them explicitly | [05](05_sun_sky_exposure_fog.md) |
| An exposure volume works in Radiant but not in game | Lighting not rebuilt and exported [COMMUNITY] | Full build | §4 |
| Lit fog or light shafts show nothing | Needs all of:<br>- `volumetric 1` on the light<br>- a `volume_litfog` with `ENABLE_LIGHTS` and a lit-fog fsi<br>- the player's volumetric setting on<br>[keys VERIFIED; setup COMMUNITY]. Tower II lights carry no `volumetric` key [VERIFIED], and the user's config has volumetrics off [VERIFIED] | Never rely on shafts for readability | [01](01_lights.md), [05](05_sun_sky_exposure_fog.md) |
| Fog still visible after "turning it off" | Zero opacity does not disable fog [COMMUNITY: project record] | Push the start plane to 1e8 (Tower II's `fog_off()`) | [05](05_sun_sky_exposure_fog.md) |
| Console spam `setVolFog: Old syntax used` | The 8-argument form called every 0.1 s [COMMUNITY: project record] | Change-gate the call (done in `_tod_atmosphere.gsc`) | [05](05_sun_sky_exposure_fog.md) |
| A sun-volume edit is refused, or the lighting breaks | A sun volume cannot be rotated, cut or split, or overlap another [VERIFIED SunSky doc] | One six-sided box per volume | [05](05_sun_sky_exposure_fog.md) |

### 2.7 Water and wet surfaces

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| Water renders black | Lighting and probes not compiled [COMMUNITY, modme 3557] | Full build; make sure a probe covers the water | [07](07_water.md) |
| Neon gives no glints on the water | The `*_only_sun` variants and `lit_transparent_water_flow` define `DISABLE_FORWARD_NON_SUN_LIGHTS` [VERIFIED define; effect INFERRED] | Use `lit_water_sim`, `_flow_normal` or `_flow_normal_color` | [07](07_water.md) |
| You walk through "water" with no splash or slowdown | Look and behaviour are separate. Behaviour is a `clip_water` / `clip_water_shallow` brush [VERIFIED GDT]. `clip_water_player` is solid to players and AI [VERIFIED flags; in-game INFERRED] | Pair a clip brush with a water surface at the same height | [07](07_water.md) |
| Zombies walk along the pool bottom | No swim behaviour in shipped AI scripts [VERIFIED absence; COMMUNITY observation] | Keep water shallow, over navmeshed floor | [07](07_water.md) |
| A puddle decal draws nothing on a brush face | `_puddle_blend` is revealed by painted vertex alpha [VERIFIED data; failure INFERRED] | Use `t7_decal_grunge_water_puddle_02` | [07](07_water.md) |

### 2.8 Build, bake and pipeline

| Symptom | Likely cause | Fix or next check | See |
|---|---|---|---|
| The LED bake hangs ~200 s and writes no `.led` | Lightmap-atlas overflow asserting at `brush.cpp:1860`. The cause is the project's own diagnosis, not a Treyarch doc [COMMUNITY: project record, KB §1] | Revert over-budget geometry; check `measure_lit_area.js`; gate with `_bake_test.ps1` | §4 |
| The world renders fullbright white | `.led` missing or deleted [COMMUNITY: project record, KB §1] | Full build | §4 |
| New or changed surfaces draw black or not at all | A stale `.led` after a `.map` change [COMMUNITY: project record, KB §1] | Full build; never relink an old LED onto new geometry | §4 |
| Linker prints `Falling back to preview lighting` | Radiant is a GUI exe and was not awaited [COMMUNITY: project record, docs/107] | `Start-Process -Wait` (`build_map.ps1` does this) | §4 |
| A light, probe or SSI edit didn't show after `-GscOnly` | `-GscOnly` skips cod2map64 and the LED bake [VERIFIED build_map.ps1:913-915] | FULL build | §4 |
| A `-GscOnly` build right after `_bake_test.ps1` shows unexpected lighting or geometry | `_bake_test.ps1` copies its test `.map` over the private workspace's `.map` and rewrites that workspace's `.d3dbsp` and `.led` [VERIFIED script]; a later `-GscOnly` links whatever it left there [INFERRED] | Follow any bake test with a FULL build before a `-GscOnly` | §4 |
| Every lighting state renders the same, or fullbright | Map One: the linker packed a `.led` older than the `.d3dbsp` [COMMUNITY: project record] | Confirm the LED is fresh | §4 |
| Radiant crash `Allocator <Gfx::LightingStateInst, 1024> has outstanding allocations` | Map One: a second baked instance of a light-carrying model [COMMUNITY: project record] | Give baked `misc_model`s the full `lightingstate1..4` set; avoid duplicate light-carrying instances; bisect | §4 |
| `Dropped N SSTs. Tune sun quality` or `Sun FAILED needs more than N MB` | Sun shadow data too large, e.g. a low split distance on a big volume [strings VERIFIED; cause COMMUNITY] | Raise `shadowSplitDistance`; bake-test | [05](05_sun_sky_exposure_fog.md) |
| Bake time jumps from ~31 s to 126 s with no change | Host state; the 126 s never reproduced [COMMUNITY: project record] | Never conclude from one timing; bake twice | §4 |
| The published map is pitch black | Lighting not exported, or the `.xpak` was deleted before upload [COMMUNITY] | Never delete packs; `-CleanPak` rebuilds them | §4 |
| The pack grows every build | The xpak is append-only; old probe sets and shadow trees stay [COMMUNITY: project record] | `-CleanPak` on publish | §4 |
| A hitch of seconds at power-on | New perk hint strings registered on demand, not lighting [COMMUNITY, modme 2118] | Register them during the black screen | [02](02_power_and_states.md) |
| A build refuses to start | Another linker, cod2map or Radiant, or the game, is running [VERIFIED build_map.ps1:155-158, :177-186; _bake_test.ps1:10] | Wait; never interrupt a peer's bake | §4 |

---

## 3. Limits and budgets

### 3.1 Engine and tool limits

"Value unknown" means Radiant contains the error message but not the number. In those rows, the string's presence is [VERIFIED] and the number is [TEST].

| Item | Limit / default | What happens past it | Tag | Source |
|---|---|---|---|---|
| Lighting states | 4 per map. Radiant State 1–4; script `0–3` (script n shows Radiant State n+1) | — | Count [VERIFIED]; mapping [INFERRED] | Lighting_Parameters; t7.def.json; zm_giant.gsc:571 |
| Live (dynamic) shadows | ~12 at `shadowmapScale 1` (512²); 3 at scale 2; ~4× more at 0.5. Scale is not supported on omni lights | Radiant has `Too many shadowing %s lights ... Shadow ... is being dropped` | Doc [VERIFIED]; drop in game [INFERRED] | Lighting_Parameters p.11 |
| `volume_performance maxDynamicShadows` | Default 12, range 0–24 | — | Def [VERIFIED]; that it is the same 12 [INFERRED] | t7.def.json |
| Shadow atlas slices (worldspawn) | `numOmniShadowSlices` 24 (8–256); `numSpotShadowSlices` 64 (8–1024). The Giant's main worldspawn uses omni 96 | — | [VERIFIED] | t7.def.json; zm_giant.map:63,72 |
| FX light shadows | Always live or Off only; no `Never` | Every shadowed FX light spends the live budget | [VERIFIED] | FX_Lights p.2 |
| Map light count | A maximum exists: `Map contains %u lights, max %u supported. This map won't link.` Value unknown. The shipped Giant has at least 645 light entities (543 in its light prefab + 3 placements of a 34-light teleporter prefab); Tower II has 344 | The map won't link | String and Giant count [VERIFIED]; value [TEST] | Radiant strings; zm_giant_light.map |
| Lights per sun volume | `Sun volume contains %u lights, max %u supported.` Value unknown | — | String [VERIFIED]; value [TEST] | Radiant strings |
| FX elements | `FX_ELEM_LIMIT(4096)` | "not spawning fx elem" | [VERIFIED] string; game [INFERRED] | Radiant strings |
| FX spot lights | `FX_SPOT_LIGHT_LIMIT`, value unknown | "not spawning spot light effect" | [VERIFIED] string; value [TEST] | Radiant strings |
| Exploders | Radiant counter reads `Total Exploders: 0/120`; `Too Many Exploders` | Refused in Radiant | 120 cap [INFERRED] | Radiant strings |
| Exploder slots per `fx` entity | `exploder_index_0..31` (32) | — | [VERIFIED] | t7.def.json `fx` |
| Cookies | Stock cookies are 512² [VERIFIED]; Radiant asserts `cookieIndex` 0–255 | Radiant size error | 256 cap [INFERRED] | light.awi; Radiant strings |
| Exported reflection probes | ≈254 (dvar text `r_updateSingleDynamicProbe` "1-254"). Virtual probes take no slot [VERIFIED]. Giant 176 (159 non-virtual); Tower II 53 | — | Cap [INFERRED] | cod2map strings; Reflection_Probes p.5 |
| Probes per volume / probe blends | `Only %u probes are supported per volume`; `GFX_MAX_CODE_PROBE_BLENDS`. Values unknown | "Ran out of room for probe blends in the shader!" | Strings [VERIFIED]; values [TEST] | Radiant strings |
| Probes over one pixel | Shader variants for 1 / 2 / 3+; override probes still count | Slower shading | [VERIFIED] | Priority_Probes; deferred.csdef |
| Probe cubemap | "multiple, 256x256, blended reflection probes" | — | [VERIFIED]; "per face" [INFERRED] | PBR deck slide 5 |
| Probe shape | 6 reflection planes (`targetPlane0..5`); a multiface probe has up to 24 faces and is still processed in groups of 6 (a full 24-face probe costs about what a box parent with 3 box children does) | — | [VERIFIED] | t7.def.json; Multiface_Probes |
| GI colour gathering | Only the 8 closest probes feed a GI voxel | Voxels no probe sees are in-painted | [VERIFIED] | Reflection_Probes p.5 |
| Sun volume shape | One six-sided box: no rotation, cut or overlap | — | [VERIFIED] | SunSky doc |
| `volume_sun grid_density` | 4–64 (step 4), default 32. Points span the whole volume; costs memory, not frame time. Tower II ≈ 764 × 764 × 1,251 units per cell | Very coarse global ambient | Def/doc [VERIFIED]; arithmetic [INFERRED] | t7.def.json; SunSky doc |
| `shadowSplitDistance` | 100–5000 inches, default 2000. Lower = better dynamic sun shadows and more memory. Runtime `SetSunShadowSplitDistance` exists | Memory; community reports dropped SSTs | [VERIFIED]; bake-cost claims [COMMUNITY] | t7.def.json; SunSky doc; API |
| Sun bake memory | `Sun FAILED needs more than %d MB` | Bake fails | String [VERIFIED] | Radiant strings |
| Sky image | 8192×4096 maximum in this pipeline | The image converter refuses it (`unsupported size`); the build fails with no sky in the `.ff` | [COMMUNITY: project record — a 16384-wide build failed] | docs/104 §4g |
| Spot cone | `fov_outer` ≤ 120 recommended | Artifacts, low-res shadows | [VERIFIED] | Lighting_Parameters p.2 |
| Light keys | `stops` −32..32 (default 11); `bake_intensity_scale` 0..100 (1); `volumetricSampleCount` 1..24 (8; the Giant uses 1 on 513 of 543) | — | [VERIFIED] | t7.def.json |
| Light LOD | Starting points `culling_cutoff/falloff` 200/300 px; radius < 10 lights 1/5 | Lights fade or pop | [VERIFIED] | Culling_LOD_Lights |
| Emissive brightness | `scaleRGB` ("HDR Scale", default 8) ≈ 2^EV of the area; Tower II EV 3–3.5 → ≈ 8–11 | Hot, blooming glow above that | Rule [VERIFIED]; arithmetic [INFERRED] | Materials.pdf p.18; material.awi:1543 |
| Albedo range | sRGB 40–238 | Room left for lighting | [VERIFIED] | PBR deck slide 10 |
| Gloss | Range 0–17 (max gloss 2^17) | — | [VERIFIED] | material.awi; PBR deck |
| Banks | `BANK_1..4` on fog, exposure, LUT and PBG volumes | — | [VERIFIED] | t7.def.json |
| LUT atlas | 1024² holding 32 LUTs of 32³ (`lut_index` 1–32) | — | [VERIFIED] file decode | texture_assets/t7_luts |
| MP exposure doctrine | Scene exposure 8–12 in MP; interiors ~1 stop darker; visibility problems at ≥ 2 stops under scene exposure. ZM night SSIs sit far lower (0.5–6) | Readability | [VERIFIED] (MP doc) | Multiplayer_Lighting_Workflow §5 |
| Transparency | "the single fastest way to ruin our framerate" | Frame time | [VERIFIED] | PBR deck slide 15 |
| Player options | Volumetrics, dynamic sun and light shadows, SSAO, probe mip drop (`TextureQualityProbes`) are user settings | Those players never see the effect | [VERIFIED] | players/config.ini |

### 3.2 This map's budgets and current values (Tower II, 2026-09-24)

| Item | Value | Why it matters | Tag / source |
|---|---|---|---|
| Light entities | 344, all `PRIMARY_OMNI`, shadowless (`PRIMARY_NOSHADOWMAP 1`, `shadowUpdate Never`), `ClientSide`, `stops 6`, `falloffdistance 12`, spawnflags 82, `lightingstate` (0,1,1,1). Brightness is tuned with `bake_intensity_scale` (1 on 320 lights, 1.35 on 24) | Every light shares one emitter, `light()` in `tools/gen_tower_map.js` (~7166 on 2026-09-24; the generator is edited often, so search for the name) | [VERIFIED] map parse |
| Reflection probes | 53, all 144-unit cubes, no planes; keys copied from the Mod Tools template (`probe()` ~7303) | Nearly all ambient comes from the global probe | [VERIFIED]; effect [INFERRED] |
| Sun volume | x/y ±12,224, z −544..39,500; `ssi` + `ssi1` only; `grid_density 32`; `shadowSplitDistance 2000`; no `target` (~7376) | Global probe at (0,0,19478), inside `mast tier 1` | [VERIFIED] |
| Sun-volume floor | `SUN_VOLUME_TOP_MIN = 39168` (generator :1557); `SKY_TOP` = that `max()` + 300, so the printed `ceiling` should read 39,468 and the `volume_sun` brush top 39,500 | Shrinking it turned the tower yellow (docs/107) | [VERIFIED] generator; effect [COMMUNITY: project record] |
| SSI | `tod_ssi_cybercity`, equal to stock `default_night` except the sky model: ev 6, evcmp 2.5, EV 3–3.5, sun stops −2.2, pitch 130, yaw 140 | Exposure is almost fixed — if this SSI is the one in use at runtime (T2) | [VERIFIED] |
| Sky light | `skyStops 10.0`; EXR solved to sky-light score 0.324 (gain 0.02603, linear RGB share 67/16/17) | The sky is ambient light | [VERIFIED] docs/150 |
| Emissive world | Every visible brush face uses an emissive-class material: 66,390 of 66,390 in the current map (66,402 before THE FALL cleared the crown hall) | Lights and states cannot darken the architecture | [VERIFIED] map parse |
| Lit surface area | 1,328.0M u²; the crown is 64% (849M). The tool's groups predate the spire, Undercity and wings, so those land in "other" (17.8%) | The LED atlas ceiling is content-specific | [VERIFIED] run of `measure_lit_area.js`, 2026-09-24 |
| LED | 50,487,469 B (2026-09-24 00:03) | Freshness and fingerprint | [VERIFIED] file stat |
| Zoned FX | 95 `fx,` lines (zone file of 2026-09-24 00:18), 2 of them placeholder stubs | Blank effects | [VERIFIED] |
| Server entities | ~1024 gentities; binding on the spire (CLAUDE.md). Every ServerSide scriptable light or server FX host costs one | Prefer client-side hosts for many lights | [COMMUNITY: project record]; per-light cost [INFERRED] |

These values move with every generator run. The face count, the zone count and the line numbers above were re-read on 2026-09-24 against the map and zone behind THE FALL's build; re-measure before quoting them.

---

## 4. Build and bake rules in this repo

**Plain version.** Treyarch moved light entities out of the BSP into a separate lighting export, the `.led`. You need a new one "when Geo changes, or if Lighting has changed" [VERIFIED Generate_LED]. Treyarch's docs let the Radiant GUI refresh some things cheaply: most SSI fields live-update in Radiant; only pitch, yaw, `skyStops` and anything that changes bounce need a rebake [VERIFIED SunSky doc]. This repo builds headless, though, and `build_map.ps1` has no LED-only mode. So in practice **every lighting change is a FULL build** [VERIFIED tools/build_map.ps1].

### 4.1 Which build does a change need?

| Change | Build | Why / tag |
|---|---|---|
| A `light` entity: add, move, colour, `stops`, radius, state flags, exploder membership | FULL | Lights live in the LED [VERIFIED Generate_LED] |
| A `reflection_probe`, the `volume_sun`, a worldspawn key (`fsi`, `lutmaterial`, sky, shadow slices) | FULL | Baked by the LED export or compiled into the BSP [VERIFIED docs; KB §4] |
| Any GDT: SSI, sky material or EXR, emissive `scaleRGB`, gloss, a new material | FULL | A GDT edit is always a full build in this project (CLAUDE.md) [COMMUNITY: project record] |
| Brush geometry, including lamp fixtures | FULL, gated by `_bake_test.ps1` first | Lightmap-atlas ceiling [COMMUNITY: project record] |
| Radiant `fx` entities, post, fog or exposure volumes | FULL | Map entities; whether the LED is needed for each [INFERRED] |
| GSC/CSC only: `set_lighting_state`, `exploder::` calls, `VisionSetNaked`, `SetVolFog`, clientfield logic | `-GscOnly` | Linker only; `-GscOnly` reuses the last BSP and LED [VERIFIED build_map.ps1:913-915] |
| A `.vision` rawfile | `-GscOnly` | Linker only [COMMUNITY: project record, KB §4] |
| A new `.efx` built from existing materials, plus its zone and precache lines | `-GscOnly` by project practice | [COMMUNITY: project record]. If it brings new images or materials (GDT), it is FULL |

### 4.2 The rules

1. **Every lighting change is a FULL build.** Never `-GscOnly` after a light, probe, sun, SSI, sky, material or geometry change. `-SkipLED` is a red flag that hides a broken bake [VERIFIED build_map.ps1 header].
2. **The bake is a gate.** Radiant runs as `-ledSilent +medium +forceclean +recompute` [VERIFIED build_map.ps1:899]. The script refuses a missing, stale or under-1 MB `.led` [VERIFIED :904-906]. The KB's `+localprobes` is not passed. It is also not among the command words found in the Radiant binary (`forceclean` and `ledSilent` are), so it is probably ignored [INFERRED].
3. **Gate geometry and fixture passes with `.\tools\_bake_test.ps1`.** It prints BAKED or CRASHED with a 120 s default timeout [VERIFIED script]. It is **not read-only**: it copies the test `.map` over the private workspace's `.map`, runs cod2map and Radiant, and so rewrites that workspace's `.d3dbsp` and `.led` [VERIFIED script]. Follow it with a full build before any `-GscOnly`. It refuses to run while BO3 or any build is active [VERIFIED :10]. **Read it as pass/fail only.** Bake time has swung 31–126 s on near-identical input; never decide anything from one timing, and bake twice if a number matters [COMMUNITY: project record, KB §1].
4. **Answer budget questions with `node tools/measure_lit_area.js`.** It is deterministic, instant and read-only. It measures input surface area and predicts nothing about frame time or bake duration [VERIFIED tool header]. Use `node tools/audit_hidden_faces.js` for faces buried in other brushes, which are wasted bake. The KB's rule: new lamp geometry must be small; prefer models or FX to large brushes [COMMUNITY: project record].
5. **After any generator run, read the printed `ceiling`.** It must stay ≥ 39,468 (`SUN_VOLUME_TOP_MIN` 39,168 + 300), because the sun-volume height changed the whole map's colour once [COMMUNITY: project record, docs/107].
6. **Prove the build is yours.** Use the CLAUDE.md check: the `scripts`, `zone_source` and `ui` diffs are clean, and nothing was synced after your `.ff`. For lighting, also check a fresh LED (rule 2) and compare its size with the last one. Geometry freshness is proven only by the full build's own regen counts (CLAUDE.md).
7. **Isolation (docs/154).**
   - Tower II builds only through `C:\BO3Tools\TOD2Cybercity`.
   - Every new lighting asset (SSI, sky, material, `.efx`, cookie) goes in a map-owned GDT or source.
   - Never write into the shared Steam Mod Tools root or Map One.
   - Stock junctions are read-only inputs. Never edit the shared vertigo GDT: clone it, as `tools/gen_tod_door_materials.js` does.
   - **Note:** the control map `Repositories/test+map` builds into the *shared* Mod Tools root (`test+map/build.ps1:6-25`) [VERIFIED]. Using it for a Tower II test is a decision for the user, not a default.
8. **The user tests.**
   - Agents build and stop, and never launch the game unless the user asks in that message (CLAUDE.md).
   - Every test ships with dev logs under a feature tag. Assemble the string outside the devblock and call `PrintLn` inside it. Gate the log on its own switch when the user's build is dev-OFF.
   - Archive the user's console with `tools/capture_ai_logs.ps1` before any relaunch.
   - CLAUDE.md also forbids asking the user to type console dvars, so tests must not depend on `r_exposureTweak` or `r_bloomEnable`.
9. **Never build while BO3 runs, and never start while a peer's linker, cod2map or Radiant runs.** The sync at the start of a build would rewrite that build's inputs, and two linkers corrupt the sound banks [VERIFIED build_map.ps1:155-158, :177-186].
10. **Evidence rules.**
    - One change per A/B.
    - Same spot, same lighting state, same round.
    - Low and high graphics configs.
    - The published build and its Workshop screenshots are the "before" for any "it used to look right" question (docs/104 §4d, docs/107).
    - Preview PNGs of the sky are display-referred; judge glare only in game or on the 1:1 `*_ingame_*` crops (docs/104 §4k).
11. **New materials:** add each to `lint_tod_geometry.js` `MATERIALS`, or the build aborts [VERIFIED lint:114]. Keep names short [COMMUNITY: project record].
12. **New FX:**
    - Vet the source for stub material, `pcloud`, child FX paths, custom cookies and interval vs lifetime.
    - Add the zone line, the precache and the `level._effect` entry.
    - Follow docs/155 for any substantial effect. A Blender preview is not native proof.
13. **Publishing:** `-Publish` implies `-CleanPak`, because the xpak is append-only [VERIFIED build_map.ps1 header]. Once measured, it held 221 probe sets for 55 probes and 47 shadow trees (CLAUDE.md, docs/86) [COMMUNITY: project record].

---

## 5. Lessons this project already paid for

Numbered so other chapters and the test plan can cite them. Where a later finding changes a lesson, the correction is stated in place.

### 5.1 Bake and build pipeline

- **L1 — The LED bake is pass/fail, not a meter.** Script-generated faces carry the placeholder `lightmap_gray 16384 16384 0 0 0 0` (every brush face: 79,332 of 79,332 in the current map) [VERIFIED grep]. Past a fragile surface budget, Radiant asserts at `brush.cpp:1860` and hangs under `-ledSilent`. Rewriting lightmap offsets in the `.map` is inert. (KB §1) [COMMUNITY: project record]
- **L2 — A deleted `.led` renders fullbright white; a stale one after a `.map` change draws surfaces black or not at all.** (KB §1) [COMMUNITY: project record]
- **L3 — Radiant is a GUI exe.** If you don't wait for it, the linker prints "Falling back to preview lighting". (docs/107) [COMMUNITY: project record]
- **L4 — Build success is a fresh `.ff`, not an exit code, and a lighting build also needs a fresh LED.** The LED's size is a fingerprint. TOD1's good bake wrote 45,041,494 B and every yellow bake 44,592,07x B; Tower II's LED is ~50.5 MB today. (docs/107; build_map.ps1) [VERIFIED]
- **L5 — The xpak only grows.** Old probe sets and sun-shadow trees ship unless the pack is rebuilt (`-CleanPak`). (CLAUDE.md, docs/86) [COMMUNITY: project record]
- **L6 — A control map settles "is it us or the tools" in one look. Build it first, not sixth.** (docs/107) [COMMUNITY: project record] The isolation caveat is in rule 4.2.7.

### 5.2 Sun volume, sky and exposure

- **L7 — The sun volume must never shrink.** `SKY_TOP` is a `max()` over the tallest geometry. When the spire went from 100 to 70 laps, the winner changed and `SKY_TOP` fell 39,468 → 29,196 (the `volume_sun` brush top 39,500 → 29,228) [VERIFIED generator arithmetic]. The whole tower then lit yellow-olive, honouring the base lights' positions but not their colour [COMMUNITY: project record, bisected]. Fix: `SUN_VOLUME_TOP_MIN = 39168`. The mechanism was never identified. (docs/107; gen_tower_map.js:1540-1558; CHANGELOG v17.80)
  - *New candidates from this reference:* the untargeted global probe sits at the volume centre and moved with it [VERIFIED doc rule; cause INFERRED], and the `grid_density` cell spacing changed [INFERRED].
  - Both TOD1 builds, good and yellow, had a buried centre, so "buried" alone does not explain the difference [INFERRED]. T3 tests it.
- **L8 — When every direct lever fails, diff the DERIVED numbers and the worldspawn.** The yellow was not a typed value. (docs/107; docs/104 §4c) [COMMUNITY: project record]
- **L9 — Establish the "before" first.** The Workshop screenshots showed the olive base already existed before the sky change. Five builds went into the wrong cause. (docs/104 §4d) [COMMUNITY: project record]
- **L10 — The sky picture IS ambient light.** `skyStops` is the sky-light gain (one stop = 2×). A score of ~4.0 turned every wall, gun and zombie olive-yellow. `SKY_GAIN` is now solved to `--target-score` (0.324 today), so a picture change cannot move the world's light. (docs/104 §4, §4b; docs/150) [that skyStops feeds the baked bounce: VERIFIED SunSky doc; the rest COMMUNITY: project record]
- **L11 — Tower II's evil sky is red-dominant (linear RGB 67/16/17),** so its ambient reads warmer. `--tint 1,1.1,1.1` pulls it back. (docs/150 §5.4) [COMMUNITY: project record]
- **L12 — Bright sky pixels bloom white in game, and the previews cannot show it.** Keep the peak knee (`--knee 0.45 --knee-max 0.62`). (docs/104 §4k) [COMMUNITY: project record]
- **L13 — 8192×4096 is the sky ceiling.** A 16384-wide EXR was refused by the image converter ("unsupported size") and the build failed. (docs/104 §4g) [COMMUNITY: project record]
- **L14 — A `material,` zone line for a `sky_latlong_hdr` material broke the build.** The sky rides in through its `xmodel,` line. This contradicts the KB's general "custom sky needs xmodel/material/image lines" (KB:200); docs/104 §1 is the later finding. [COMMUNITY: project record]
- **L15 — Never adopt the Nastian `t9_*` SSIs for a night map.** They sit ~9 EV brighter (evmin 5.5–8, evmax 12–14). `tod_ssi_cybercity` is `default_night` with our sky model. (docs/104 §1; MODTOOLS/source_data/acc_nastian_t9_skyboxes.gdt) [VERIFIED values]
- **L16 — Map One dimmed its night sun 20%** by moving SSI `stops` −2.2 → −2.52 (`acc_ssi_night_dim80`). [VERIFIED values; intent INFERRED]
- **L17 — The worldspawn sky and SSI keys cannot change at runtime.** The spire's mood is done with fog. The only runtime SSI switch is a lighting-state change to a state whose `ssiN` differs [INFERRED from the SunSky doc]. (gen_tower_map.js comment at ~1848-1851)
- **L18 — "The yellow was sun-lit fog" (docs/104 §4c) was wrong for the yellow.** Reverting the fsi changed nothing (docs/107 table). The fsi `zm_factory_volumetric` does carry `litfog 1` and `sunintensityscale 2` [VERIFIED], and it is still the live worldspawn fsi. [COMMUNITY: project record]
- **L19 — Zero opacity does not disable fog.** Push the start plane to 1e8 instead. Calling the 8-argument `SetVolFog` every 0.1 s spams "Old syntax used" (1,957 lines in 5 minutes), so change-gate it. (`_tod_atmosphere.gsc`) [COMMUNITY: project record]
- **L20 — The map-name `.vision` must stay neutral.** The client re-applies it, and that caused Map One's grey screen on revive. [re-apply: VERIFIED script; the grey-screen cause: COMMUNITY: project record]

### 5.3 Materials, emissive and reflections

- **L21 — Every vertigo material is self-lit, so geometry does not self-shadow.** Relief reads only through silhouette or a material change. (docs/34 §11.1) [COMMUNITY: project record]
- **L22 — The vertigo materials are near-mirrors:** `$white_diffuse`, `$white_specular`, a gloss map 96.6% above half, no normal map, `reflectionProbeAmount 1`. Big flat faces showed a smeared skyline, so doors got map-owned matte clones (`tod_door_*`). Never edit the shared GDT. [VERIFIED measurement]
- **L23 — The two emission textures differ.** The plain `_e` grid is 92.4% black (mean 0.048). `_tinted_e` has no black pixels (mean 0.253). [VERIFIED measurement]
- **L24 — Light colour paints a `$white_diffuse` colour map.** The warm spawn light (`1 0.9 0.78`) made the olive pool. (docs/104 §4d) [COMMUNITY: project record]
- **L25 — "The floor stopped lighting the room" (v17.28) is an inference, not a measurement.** No bake A/B was recorded. `BASE_LIGHT_BAKE` has since been treated as "the only real brightness knob", on a key the def describes as a GI-bake control. (gen_tower_map.js:7188-7201) Tested by T4 and T5.
- **L26 — A BO6 or BO7 port that looks dead is usually missing its emission sheets, not its lighting.** (the inducer) [COMMUNITY: project record]
- **L27 — To reduce gloss, lower it; never disable reflections.** The user rejected the all-matte altar (glossRangeMax 8 → 6, spec .2, tint .25, probe .15 was the fix). (CLAUDE.md) [COMMUNITY: project record]
- **L28 — `lit_emissive_plus` ignores a spec map** because it has no slot for one; use `_advanced_fullspec`. [VERIFIED techsets]
- **L29 — Invented material names are substituted silently, and names over 63 characters are truncated and substituted.** `_tinted_edge` exists for only five hues. (CLAUDE.md; generator MAT comments) [COMMUNITY: project record]
- **L30 — The probe diagnosis in CLAUDE.md was half right.** Reflections do smear. But there are 53 probes, not 46. The 72 is a half-extent *influence* box, not a parallax box. There are no reflection planes. And most surfaces sit outside every box, so the global probe is the likelier smear source (§6). [VERIFIED def and map]

### 5.4 Lights and lighting states

- **L31 — The lighting-state number is off by one, and Map One proved it in game.**
  - Map One calls `set_lighting_state(0)` at start and `(1)` at power (`zm_abandoned_cyber_city.gsc:957/972`, inside `CheckForPower`). Its user saw the map "truly dark until the power switch" (Map One CHANGELOG ~17570) [COMMUNITY].
  - The Giant boots in Radiant State 2, aliased `power_off`, and calls `set_lighting_state(0)` at power [VERIFIED data].
  - Tower II never ported Map One's `CheckForPower`, so its lights are on from spawn [INFERRED]. Under THE FALL, power itself is also on from the first frame.
  - docs/107's reading, that `lightingstate1 0` means "authored OFF before power", is contradicted (§6).
- **L32 — The flip is binary.** Map One fakes a swell: a dark `VisionSetNaked` grade at the flip, then a lerp to default over ~10–15 s (`_acc_atmosphere.gsc:490-530`). [COMMUNITY: project record]
- **L33 — A light whose origin is inside a solid brush lights nothing** (the entombed crown beacons and the girandole). No lint catches it yet. [COMMUNITY: project record, arithmetic]
- **L34 — A 900-unit light does nothing visible for a 4096-unit object.** The crown's read is carried by material. [COMMUNITY: project record]
- **L35 — Map One found even `bake_intensity_scale 0.02` "still too light" before power, and asked for zero.** The whole DIM set was then dropped (`EMIT_DIM_PREPOWER = false`). (gen_room_roofs.js:44-60) [COMMUNITY: project record]
- **L36 — Map One's LED crash `LightingStateInst` came from a duplicate light-carrying model instance.** [COMMUNITY: project record]

### 5.5 FX

- **L37 — Every FX needs `#precache`, a zone `fx,` line and a `level._effect` entry. Miss one and the device sits dark with no error.** (`_tod_rampage.gsc:95-101`) [COMMUNITY: project record] The zone line matters only for effects not already loaded by a base-game zone.
- **L38 — Zoning a placeholder stub packs a blank effect.** (TOD1 memory: the zoned Trailblazer stub was blank; a real source fixed it) [COMMUNITY: project record]
- **L39 — "Server one-shot PlayFX renders nothing" is a heuristic, not a rule.** The Map One evidence is confounded: the fix also moved the host out of the pad assembly. The proven lanes are a looping FX on a `tag_origin` host emitted after two frames, and clientfield → CSC. (§6) [INFERRED rule status]
- **L40 — A clientfield FX spawned far away may not appear on approach;** re-pulse it (`TOD_GLOW_REKICK_DIST 700`). [COMMUNITY: project record]
- **L41 — A pulse belongs in the FX intensity curve, not a script timer.** A server one-shot tell rendered nothing, and a looping curve did (inducer v18.99i). [COMMUNITY: project record]
- **L42 — Detailed FX need the docs/155 art workflow.** Blender renders do not establish native glow, bloom or lighting. [COMMUNITY: project record]
- **L43 — `pcloud` materials gave a first-render `Com_ERROR`, and a weapon trail effect with an unzoned child gave a black-screen hang after ModLoad.** (project memory) [COMMUNITY: project record]. Both are warnings to test, not rules: Tower II zones and renders several `pcloud` effects, and the linker's asset ledger shows child effects of zoned effects packed automatically; the TOD1 hang was fixed by swapping effects, so its real cause was never isolated ([04](04_fx_lights.md)).

### 5.6 Process

- **L44 — The user tests; the agent writes logs.** "Verify" means logs, not a launch. (CLAUDE.md, 2026-09-16)
- **L45 — Cheap to change is not cheap to be wrong about.** Read the site that produces a value before claiming what it does. The state index, `radius 2048` and "authored OFF" were all asserted without reading their consumer. (CLAUDE.md)
- **L46 — A record that quotes a number goes stale.** Name the constant and the file; quote a value only with a date on it. (CLAUDE.md)

---

## 6. Records this reference contradicts

These are recommendations for whoever owns each file. This chapter changes nothing. Fix the lighting-state records only after T1 confirms the mapping.

| Record | What it says | What the evidence says | Tag |
|---|---|---|---|
| docs/107_sun_volume_yellow_postmortem.md:28-31 and the "lighting states" table row; tools/gen_tower_map.js:1545-1547; CHANGELOG.md v17.80 and v17.78 entries (~11512, ~11567, ~11638 on 2026-09-24) | `lightingstate1 0` = "authored OFF before power"; the yellow build "did not honour" the lighting state | The game runs in Radiant State 2, where all lights are on, so nothing is off before power. docs/107:57 also checked only the LED's index-0 (Radiant State 1) SSI entry, not the live Radiant State 2 entry (`default_day`) | [INFERRED], strongly supported |
| CLAUDE.md, v18.99g "STILL OPEN, MAP-WIDE" note (~line 860 on 2026-09-24) | "all 46 reflection probes ship Radiant's DEFAULT 72-unit parallax box … That is what makes reflections SMEAR" | 53 probes; 72 is a half-extent influence box (144-unit cube); no reflection planes; most surfaces are outside all boxes | [VERIFIED def/map] |
| tools/gen_tower_map.js:6091 and :7365 | Probe coverage reasoned from `radius 2048` | `radius` is not a `reflection_probe` key; coverage is `size_min/size_max` | [VERIFIED def]; inert [INFERRED] |
| tools/gen_tower_map.js:7188-7201 (`BASE_LIGHT_BAKE`) | "the only real brightness knob"; the floor "stopped lighting the room" | Unmeasured; the def calls `bake_intensity_scale` a GI-bake control | T4, T5 |
| docs/BO3_MAPMAKING_KB.md:65 | Radiant `+localprobes` | Not among the Radiant command words found; `build_map.ps1` doesn't pass it | [INFERRED] |
| docs/BO3_MAPMAKING_KB.md:170, :377 | The stock template ships `ssi1/ssi2 = mp_havoc` | The installed template has `ssi`/`ssi1 = default_day` only. Its mtime suggests it may have been edited locally. Do not cite "the template" either way | [VERIFIED file] |
| docs/104_cybercity_sky.md §4 table | `skyScaleRGB` is a "display multiplier — never touch" | `material.awi:634` marks it obsolete; values in the installed GDTs run 0.75–9000; its meaning is undocumented | [VERIFIED] |
| docs/104_cybercity_sky.md §4d | The spawn light is "now cool white `0.72 0.84 1`" | Reverted to `1 0.9 0.78` in v17.78 and still is | [VERIFIED] |
| docs/104_cybercity_sky.md §4c | "The yellow was never the sky — it was sun-lit fog" | Superseded by docs/107 (the fsi revert changed nothing) | [COMMUNITY: project record] |
| CLAUDE.md (v18.99i and related notes) | "a server-played one-shot renders nothing" | A project heuristic from a confounded test; stock uses server one-shots at 72 sites | [INFERRED] |
| scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc:31, :958 | The 18-argument `SetVolFog` is "used NOWHERE in the entire mod tools install" | Stock `zm/_art.gsc:226` uses it inside a dev block | [VERIFIED] |
| docs/107 LED size fingerprint | 45,041,494 good / 44,592,07x yellow | Those are TOD1's; Tower II's LED is ~50.5 MB | [VERIFIED] |
| `tools/measure_lit_area.js` GROUPS | Region table | Predates the spire, Undercity and wings (all in "other", 17.8%) | [VERIFIED run] |
| `_tod_perk_lights.csc` colour-table comments | Index 5 "Mule Kick", 7 "Deadshot" | The server maps 5 = Death Perception (plus the retired Mule Kick case), 7 = Wisp Tea; comments only | [VERIFIED] |

---

## 7. Open questions and the test plan

**Plain version.** Every chapter ends with things nobody has checked in game. They fall into three groups:
- a few that decide what the map is doing *today*,
- a few that must be settled before the dark-map rework,
- many that only matter for one fixture type or edge case.

The plan runs them in that order and changes one thing per build. The first three builds (A, B, D below) answer the four P0 questions.

### 7.1 How every test runs

1. **One change per build,** named in the build note. Record the LED size and the generator's `ceiling` print.
2. **Where.** Prefer Tower II's own guarded pipeline, with the test geometry or keys behind a generator test switch that ships OFF. `Repositories/test+map` writes into the shared Mod Tools root (rule 4.2.7), so use it only with the user's OK. Its HEAD commit, step 2 (one green omni with Tower's key set, `lightingstate1 0`; recorded as unbuilt), is half of T1; its commit message repeats the "off before power" reading that §6 contradicts.
3. **The agent builds and stops; the user plays.** Fixed screenshot spots:
   - the crown hall, where the party now spawns (round 1);
   - one tower lap landing;
   - one breather lounge;
   - the plaza by the base's east wall (docs/107's TOD1 crate spot);
   - the Vault.

   The Endless Spire is not reached while THE FALL parks the finale, so no spire hub. Power is on from the first frame in the current build, so "before and after power" shots only exist in a build whose test hook changes the lighting at a scripted moment (T8, T15). Shoot on the user's normal (low) config and, where volumetrics or shadows matter, a high config.
4. **Logs.** Use one tag per test. Build the string outside the devblock and gate it on its own switch (CLAUDE.md). The lighting-state logger that several tests share is sketched below; it is not built or tested:

```c
// Sketch only. Temporary switch per CLAUDE.md; zero it before a publish.
#define TOD_LIGHTSTATE_LOG 1

function lightstate_log( at )
{
    if ( !TOD_LIGHTSTATE_LOG && !IS_TRUE( level.tod_dev ) ) return;
    lvl = ( isdefined( level.lighting_state ) ? level.lighting_state : -1 );
    cs  = GetDvarString( "cg_usingClientScripts" );
    foreach ( p in GetPlayers() )
    {
        line = "[TOD_LIGHTSTATE] ms=" + GetTime() + " at=" + at
             + " ent=" + p GetEntityNumber() + " level=" + lvl
             + " player=" + p GetLightingState() + " cgcs=" + cs;
        /#
        PrintLn( line );
        #/
    }
}
// Call after flag initial_blackscreen_passed, one frame after flag power_on,
// and from an on-spawned callback (spawnPlayer re-applies the state).
```

5. **Record the result** in the table in §7.4, then update the chapter named in the test. Retag the claim: [TEST] becomes [VERIFIED] only when the user saw it in game or the file shows it.

### 7.2 The plan at a glance

| ID | Question | Priority | Build | Unblocks |
|---|---|---|---|---|
| T1 | Which Radiant State is live, and does script state n show Radiant State n+1? | P0 | FULL (build A; optional C) | Every power-on design ([02](02_power_and_states.md)) |
| T2 | What does Radiant State 2 show with `ssi2` unset, versus set? | P0 | FULL (build B) | The sun, exposure and SSI plan ([05](05_sun_sky_exposure_fog.md)) |
| T3 | Does targeting the global probe at open air change the cast? | P0 | FULL (build D) | The docs/107 mechanism; the probe plan ([06](06_reflections_probes.md)) |
| T13 | What does each baked state cost (LED size, BAKED/CRASHED)? | P0 rider | None extra (reads builds A/B) | The state budget |
| T4 | Does a large emissive surface add bounce or reflection light? | P1 | FULL ×2 | The emissive re-skin plan ([03](03_glow_and_perks.md)) |
| T5 | Does `bake_intensity_scale` change the direct pool or only bounce? | P1 | FULL | The brightness knob ([01](01_lights.md)) |
| T6 | Which way does `evcmp` move the image? | P1 | FULL ×2 | Exposure clamps ([05](05_sun_sky_exposure_fog.md)) |
| T7 | Do post volumes with default flags apply in Radiant State 2? | P1 | FULL (two boxes, one build) | Any pbg/LUT/bloom work |
| T8 | Does a server `stop_exploder` turn a light group off? | P1 | FULL | Per-floor exploder lighting ([02](02_power_and_states.md), [04](04_fx_lights.md)) |
| T9 | Are the two zoned stub FX blank in game? | P1 | `-GscOnly` | Lounge ambience ([04](04_fx_lights.md)) |
| T11 | After gating, do probes and reflections switch with the state? | P1 (after gating) | Comes with the gating build | Power-on reflections ([06](06_reflections_probes.md)) |
| T18 | Fitted-probe build: planes, dead keys, sign convention | P1 | FULL | The reflection rework ([06](06_reflections_probes.md)) |
| T10 | Interval = lifetime on perk glows and the inducer | P2 | `-GscOnly` | FX light quality ([04](04_fx_lights.md)) |
| T12 | Does a pre-join exploder replay for a hot-joining client? | P2 | Uses T8's build | Co-op safety |
| T15 | Does `volume_sun transitionTime` blend a state switch? | P2 | FULL | A power-on fade ([02](02_power_and_states.md)) |
| T16 | `lit_emissive_script` + `MapShaderConstant` on an entity | P2 | FULL | Switchable glow ([03](03_glow_and_perks.md)) |
| T17 | Do `lightingstate` keys hide a `misc_model` / `script_model`? | P2 | FULL | No-script on/off models ([03](03_glow_and_perks.md)) |
| T22 | Cookies on baked spots: `def`, `def_scroll`, `def_rotation` units | P2 | FULL | Street lamps and caustics ([08](08_fixture_cookbook.md)) |
| T29 | Does the stock `_zmb` sprite aura still play on our machines? | P2 | `-GscOnly` (log) or none (look) | Perk glow ([03](03_glow_and_perks.md)) |
| T30 | Does a Radiant `fx` entity need a zone line? | P2 | FULL | Generator-emitted FX ([04](04_fx_lights.md)) |
| T14 | Controlled server one-shot `PlayFX` vs host vs CSC | P3 | `-GscOnly` | FX lanes ([04](04_fx_lights.md)) |
| T19 | Is the worldspawn fog baked into our probes? | P3 | FULL | Reflection tint |
| T20 | Volumetrics and lit fog on a high config | P3 | FULL | Shafts ([01](01_lights.md)) |
| T21 | Hard ceilings: lights, FX spot lights, probes, exploders | P3 | As approached | Budgets (§3) |
| T23 | SSI pitch convention | P3 | Radiant only | Sunsets ([05](05_sun_sky_exposure_fog.md)) |
| T24 | `shadowSplitDistance` on our tall volume | P3 | FULL + bake test | Sun leaks |
| T25 | Emissive fields: flicker defaults, `emissiveIncompetence`, `emissiveFalloff` | P3 | FULL | Glow authoring ([03](03_glow_and_perks.md)) |
| T26 | `SetLight*` on ServerSide scriptable lights | P3 | FULL | Script-dimmed lights |
| T27 | Water: clip names, swimming default, glints | P3 (only if water is planned) | FULL | [07](07_water.md) |
| T28 | Which Glass Tower does the user mean? | P3 | None; ask the user | [09](09_design_and_inspiration.md) |

### 7.3 The tests

#### T1 — Which Radiant State is live, and does script state n show Radiant State n+1? (P0)

- **Why:** Every power-on design in [02](02_power_and_states.md) rests on this, and the repo's own records assume the opposite (§6). The `GetLightingState()` log reports only the *script* number. It cannot prove the Radiant mapping by itself [VERIFIED API shape], so the test pairs the log with two coloured lights.
- **Change (build A):** behind a test switch, add at the spawn (the crown hall since THE FALL), on a wall the party faces:
  - a GREEN small omni with mask `1,0,0,0` (Radiant State 1 only);
  - a RED one with mask `0,1,0,0` (Radiant State 2 only).
  - Use the same radius and `stops`, about 48 units apart on one wall.
  - Add `lightstate_log` at blackscreen, one frame after `power_on` (which THE FALL sets in the first seconds) and on spawn.
  - Nothing else changes, so `ssi2` stays unset.
- **Build:** FULL.
- **User:** spawn, look at the two pools, die and respawn once in co-op if possible. There is no power switch to flip in this build: THE FALL turns power on at the start, and stock power changes no lighting anyway.
- **Log:** `[TOD_LIGHTSTATE]`. Expected today: `level=1 player=1` throughout.
- **Read it:**
  - RED lit and GREEN dark confirms script 1 = Radiant State 2. It also shows that Radiant State 2 lights render even with `ssi2` unset. TOD1's visible spawn-light gradient already hints at this (docs/107, docs/104 §4d) [INFERRED].
  - Both dark would mean Radiant State 2 lights do not render with `ssi2` unset. Every Tower II light has then never lit anything, and the look was emissive + sky + probes. Run T2 next.
  - GREEN lit means the mapping is not n+1.
- **Optional build C (after B):** add `level util::set_lighting_state( 0 );` right after `zm_usermap::main()`. Expect GREEN on and RED off. The whole tower's 344 lights should go off in this build, which also shows whether any of their baked bounce remains [TEST].
- **Update:** [02](02_power_and_states.md), [01](01_lights.md), README, and the §6 records.

#### T2 — What does Radiant State 2 show with `ssi2` unset, versus set? (P0)

- **Why:** The `.led` records `default_day` for Radiant State 2 [VERIFIED]. Community reports say states misbehave without an SSI [COMMUNITY]. `default_day` is a warm daytime sun: `1 0.976 0.949`, pitch 125, yaw 150, stops 14, EV 1–16 [VERIFIED ssi.gdt]. If the game uses it, our exposure and sun were never `tod_ssi_cybercity`. Counter-evidence to weigh: stock `mp_sector_light.map` ships lights at (0,1,1,1) with `ssi1` only and no state call [VERIFIED data], and TOD1 had our exact setup yet recorded a visible spawn-light gradient (docs/107) [COMMUNITY: project record] — so Radiant State 2 lights may well render regardless.
- **Change (build B = A +):** on the `volume_sun`, add `ssi2 = tod_ssi_cybercity` (one `kv` in the generator's `volume_sun` block, ~7376).
- **Build:** FULL. Then read the LED's per-state SSI table offline ([02](02_power_and_states.md) covers the table). Its layout is: a count of 4, then per state `[uint32 length][SSI name, no terminator][uint32 state index][16 bytes]`; index 0 = Radiant State 1 [VERIFIED decode, re-read 2026-09-24 on the current LED at byte ~12,424,824]. Expect `[tod_ssi_cybercity, tod_ssi_cybercity, default_day, default_day]`. Today it reads `[tod_ssi_cybercity, default_day, default_day, default_day]` [VERIFIED].
- **User:** the fixed screenshot spots in A and B.
- **Read it:** Any visible change in overall exposure, sun colour or the gun and zombie tint means Radiant State 2 had been running on `default_day` values. No change means the engine fell back to something else, or the entry is unused at runtime [TEST either way].
- **Update:** [05](05_sun_sky_exposure_fog.md), [02](02_power_and_states.md).

#### T3 — Does targeting the global probe at open air change the cast? (P0)

- **Why:** The global probe lights nearly every Tower II surface [INFERRED], and it sits inside `mast tier 1` [VERIFIED]. The official doc warns that a buried global probe gives "very very different" bounce colour [VERIFIED]. All three stock sun volumes use a `target` [VERIFIED]. This is the best remaining candidate for docs/107's mechanism.
- **Change (build D = B +):**
  - Emit an `info_null` in open air, at an "ideal average location" for the lighting (the doc's words), not high above the map. The generator should assert that it is outside every brush. The Giant's is `auto11353318` at (−131, 49.5, 1812.5) in its light prefab [VERIFIED].
  - Give the `volume_sun` `target` = that info_null's `targetname`.
  - Nothing else changes.
- **Build:** FULL. Record the LED size.
- **User:** the same spots; also look at the gun and a zombie at the crate spot.
- **Read it:**
  - A clear cast or brightness change means the probe position is a live lever. docs/107's mechanism is then likely, and the target stays (with a chosen spot).
  - No change means the grid spacing or the Radiant State 2 `default_day` entry is the next suspect.
- **Update:** [06](06_reflections_probes.md), [05](05_sun_sky_exposure_fog.md), docs/107 (by its owner).

#### T13 — What does each baked state cost? (P0 rider)

- **Why:** Radiant keeps probe and sun-shadow data per state [VERIFIED field names]. Whether leaving `ssi2..4` unset avoids baking them is unknown, because unset slots are still listed as `default_day`.
- **How:** Compare builds A and B: LED bytes, BAKED/CRASHED for two bakes each (`_bake_test.ps1`, followed by a full build), and the probe and sun-shadow asset sizes from `node tools/xpak_report.js`. The pack is append-only, so compare per-asset sizes, never the pack total. No extra build.
- **Update:** [02](02_power_and_states.md) (cost of a state).

#### T4 — Does a large emissive surface add bounce or reflection light? (P1)

- **Why:** The dark-map plan depends on it ([03](03_glow_and_perks.md)). No doc says emissive feeds the bake [INFERRED absence], but GI grid points read colour from the 8 closest probes' cube maps [VERIFIED Reflection_Probes doc]; whether those captures include emissive surfaces is [TEST].
- **Change:** a closed room with **no light entities** and a fitted probe.
  - Build 1: a filled emissive floor (vertigo `_tinted`, scaleRGB 10).
  - Build 2: the same brush in a non-emissive dark `lit` map-owned material.
  - Use a Tower II test cell behind a switch, or test+map with the user's OK.
- **Build:** FULL ×2.
- **User:** the walls, a prop and a zombie in the room, both builds. If the user opens Radiant, the *Diffuse GI Only* and *Specular GI Only* render flags help. The in-game shot decides.
- **Read it:** Lit walls in build 1 only means emissive feeds GI. Removing emissive area will then also darken bounce. Identical walls means emissive is a look only.
- **Update:** [03](03_glow_and_perks.md), L25, `BASE_LIGHT_BAKE` comment (by its owner).

#### T5 — Does `bake_intensity_scale` change the direct pool or only bounce? (P1)

- **Why:** The generator uses it as its brightness knob; the def calls it a GI-bake control [VERIFIED]. Map One's pre-power set at 0.02 still read "too light" to its user (L35), which fits either reading, since bounce is visible too [INFERRED].
- **Change:** two identical omnis side by side on a matte wall (same colour, radius and `stops`), one at `bake_intensity_scale 0`, one at `4`.
- **Build:** FULL.
- **Read it:** Equal direct pools with different surrounding bounce confirms "GI only": use `stops` for brightness. Different pools means it scales both.
- **Update:** [01](01_lights.md).

#### T6 — Which way does `evcmp` move the image? (P1)

- **Why:** No primary source states the sign [VERIFIED absence]. Stock nights pair low clamps with positive `evcmp`, which suggests positive = darker [INFERRED].
- **Change:** a map-owned clone of the live SSI, identical except `evcmp +2` in build 1 and `−2` in build 2, keeping the shipping clamp EV 3–3.5.
- **Build:** FULL ×2. No console dvars (rule 4.2.8).
- **Read it:** Brighter at −2 means negative brightens. Identical means the clamp overrides `evcmp` at this range. That is useful in itself: it tells us whether to move the clamp or the compensation.
- **Update:** [05](05_sun_sky_exposure_fog.md).

#### T7 — Do post volumes with default flags apply in Radiant State 2? (P1)

- **Why:** `pbg_box`, `vlut_box`, `vbloom_box`, `vcolor_*` and `volume_performance` default to `LIGHTSTATE_1` only [VERIFIED def].
- **Change:** in one build, two identical `pbg_box` volumes with an obvious effect (for example `USE_LUT` with a strongly graded stock LUT band). Box 1 keeps default flags; box 2 has `LIGHTSTATE_1` + `LIGHTSTATE_2`.
- **Build:** FULL.
- **User:** walk into each box (both sit in the live Radiant State 2).
- **Read it:** Only box 2 grading confirms that every post volume must tick Radiant State 2 while the map runs in Radiant State 2.
- **Update:** [05](05_sun_sky_exposure_fog.md), [02](02_power_and_states.md).

#### T8 — Does a server `stop_exploder` turn a light group off? (P1)

- **Why:** The server stop path reaches `DeactivateClientRadiantExploder` only when `level.clientScripts` is true. That flag is set from the dvar `cg_usingClientScripts` (`load_shared.gsc:55/60` writes `level.clientscripts`; GSC names are case-insensitive, so it is the same variable; `exploder_shared.gsc:761-790`) [VERIFIED code]. Its value in a usermap is [TEST]. Exploders are also a new lane for the generator.
- **Change:**
  - One exploder `lgt_tod_test` holding one small primary light, with membership keys copied from a stock prefab (`exploder_count`, `exploder_index_0 "ver=2 … name=lgt_tod_test"`, `exploderDisabled 1`). Keep the light enabled in the live Radiant State 2; Treyarch's exploder lights also carry state masks.
  - Server script: `exploder::exploder( "lgt_tod_test" )` at a fixed time after `initial_blackscreen_passed` (power is already on under THE FALL), `exploder::stop_exploder` 15 s later, `exploder::exploder` again, then `exploder::kill_exploder` 15 s after that.
  - Log each call and `cgcs`.
- **Build:** FULL.
- **Read it:** If the light stays on after stop, use client-side stop (`exploder_shared.csc`) or `kill_exploder` for anything that must turn off. Also note whether the hand-written keys worked at all.
- **Update:** [02](02_power_and_states.md), [04](04_fx_lights.md).

#### T9 — Are the two zoned stub FX blank in game? (P1)

- **Why:** Both zoned sources are the 5,092-byte stub (md5 12186140…) [VERIFIED]. The "zoned stub = blank" rule rests on one project observation [COMMUNITY: project record].
- **Change:** none for build 1. The user looks at a breather lounge for the motes and triggers the effect that uses `tod_thor_cloud`. Build 2 swaps the motes to a vetted real source, with zone, precache and `level._effect` updated. For example, `dirt/fx_dust_motes_200x200` (17,229 B in both the shared tools and the private workspace) has no stub material, no `pcloud` and no child FX paths [VERIFIED grep, 2026-09-24]. How it looks in game is [TEST].
- **Build:** none, then `-GscOnly`.
- **Read it:** Motes absent in build 1 and present in build 2 confirms the stub rule.
- **Update:** [04](04_fx_lights.md); remove or replace both zone lines.

#### T11 — After gating, do probes and reflections switch with the state? (P1, rides on the first state-switching build)

- **Why:** Per-state probe arrays exist in Radiant [VERIFIED field names; meaning INFERRED]. If reflections did not switch, puddles and mirrors would show "lights on" neon while the lights are off.
- **How:** In the first build that switches lighting states at runtime ([02](02_power_and_states.md); at power only if the user reverses THE FALL's power-at-start decision, otherwise at the chosen scripted beat), take the same glossy-floor shot before and after the switch.
- **Update:** [06](06_reflections_probes.md), [07](07_water.md).

#### T18 — The fitted-probe build (P1)

- **Why:** This is the biggest reflection lever. It was flagged as a map-wide look change and the user's call (CLAUDE.md).
- **Change:** the `probe()` rewrite in [06](06_reflections_probes.md):
  - room-fitted `size_min/size_max`;
  - `targetPlane0..5` (convention `nx ny nz d`, normal into the room, 2-unit inset [INFERRED from stock]);
  - captures ~72 above floors;
  - `resolution 4x`;
  - drop `radius`, `exploderFade` and `grid_density`.
  Before emitting, check the plane sign by pressing W on one generated probe in Radiant and reading back what it writes.
- **Build:** FULL, with before/after screenshots.
- **Read it:** Less smear and room-coloured reflections. Watch the frame rate in overlap zones.
- **Update:** [06](06_reflections_probes.md); retire L30's open part.

#### T10 — Interval = lifetime on the perk glows and the inducer (P2)

- **Change:** `spawnLooping 1000` to match `lifeSpanMsec 1000` on the light element of one perk glow and on `fx_tod_inducer_on`.
- **Build:** `-GscOnly` (project practice for `.efx`).
- **Read it:** A visible once-per-second pulse and a dimmer steady level would confirm the ~5-light stacking. The user approved the current inducer look, so keep whichever the user prefers.
- **Update:** [04](04_fx_lights.md).

#### T12 — Does an exploder started before a client joins replay for that client? (P2)

- Reuse T8's build. Host plays, power on, the exploder is running; a second player joins. If the joiner sees no light, drive exploders from a world clientfield callback (the stock trap pattern). Update [02](02_power_and_states.md).

#### T15 — Does `volume_sun transitionTime` blend a state switch? (P2)

- Needs two states with visibly different SSIs (for example a dimmer clone), `transitionTime 3`, and a state switch at a scripted moment. Check whether the sun, sky light and probes blend or snap, and whether light entities blend (expected: snap [INFERRED]). Update [02](02_power_and_states.md), [05](05_sun_sky_exposure_fog.md).

#### T16 — Switchable glow with `lit_emissive_script` (P2)

- A `script_model` with a `lit_emissive_script` material. Client script, as stock Der Wunderfizz does it: `self MapShaderConstant( localClientNum, 1, "ScriptVector0" )` once, then `self SetShaderConstant( localClientNum, 1, x, y, z, w )` steps at the chosen moment (`_zm_perk_random.csc:104`, `:116`) [VERIFIED stock]. That `lit_emissive_script`'s `cg00` "Tint (Brightness, State)" preview is what `ScriptVector0` drives is [INFERRED]; no shader source was read. A working result gives one-model power glows without `_on` twins. Update [03](03_glow_and_perks.md).

#### T17 — Do `lightingstate` keys hide models? (P2)

- One `misc_model` at `1,0,0,0` and one `script_model` at `0,1,0,0`, then switch states. The Giant uses these keys only as `1111` [VERIFIED], and Map One recorded the semantics as unverified. Hidden, still visible but unlit, and unchanged each tell us something. Update [03](03_glow_and_perks.md), [02](02_power_and_states.md).

#### T22 — Cookies on baked spot lights (P2)

- A spot with `def cookie_caustics_01`, `def_scroll 0.05 0.1` and `def_rotation −0.1` (the Giant's caustics values) [VERIFIED], `shadowUpdate Never`. Check that it animates and whether `def_rotation` is degrees per second (def) or seconds per turn (doc) [TEST]. Map One suspected cookie defs inside `.efx` in a freeze; this tests a Radiant light, not an FX. Update [01](01_lights.md), [08](08_fixture_cookbook.md), [07](07_water.md).

#### T29 — Does the stock `_zmb` sprite aura still play on our machines? (P2)

- Nothing overrides stock `perk_fx` [VERIFIED grep], so the sprite halo probably plays alongside `todPerkGlow` [INFERRED]. The user looks at a machine after power, or a log is added at `perk_fx`. Update [03](03_glow_and_perks.md).

#### T30 — Does a Radiant `fx` entity need a zone line? (P2)

- One `fx` entity with no `fx,` zone line; check the linker's assetinfo `.csv` and the game. The Giant's light prefab places 96 `fx` entities (94 of them light effects); only 6 carry exploder membership, so most play with no script at all [VERIFIED count]. Update [04](04_fx_lights.md).

#### T14, T19–T21, T23–T28 — the long tail (P3)

- **T14:** the same zoned, real one-shot FX at the same origin, played three ways: bare server `PlayFX`, `PlayFXOnTag` on a host after two frames, and CSC. Settles L39.
- **T19:** the fsi `zm_factory_volumetric` vs a no-fog fsi, same build otherwise. Compare reflection tint.
- **T20:** `volumetric 1` light + `volume_litfog` (ENABLE_LIGHTS) on a high config. Confirms shafts, and that the user's config hides them.
- **T21:** read the Radiant export messages when approaching light, probe or exploder counts. Nothing to do while far below (344 lights, 53 probes, 0 exploders).
- **T23:** in Radiant, pitch 10 vs 170 at the same yaw; watch shadow direction. Needed only for a sunset.
- **T24:** `shadowSplitDistance` 800 vs 2000, bake-tested twice. Judge on a high config, because the user's config disables dynamic sun shadows.
- **T25:** one scroll material at defaults vs min = max = 1; `emissiveIncompetence` 0 vs 1; `emissiveFalloff` 0/2/10 viewed head-on and grazing.
- **T26:** one `scriptable` + `ServerSide` light driven by `SetLightIntensity`, with a log.
- **T27:** only if water is planned. Texture-browser clip names; a deep `clip_water` pool with an `IsPlayerSwimming()` log; neon glints on `lit_water_sim` vs an `_only_sun` variant.
- **T28:** ask the user to confirm Workshop item 3801980290 (GLASS TOWER[HARD] by vuflub_) and which moments they like ([09](09_design_and_inspiration.md)).

### 7.4 Result log

Fill one row per completed test. A [TEST] tag elsewhere in the reference changes only when a row here backs it.

| ID | Date | Build (time, `.ff` bytes, LED bytes) | What the user saw / what the log said | Verdict | Chapters updated |
|---|---|---|---|---|---|
| T1 | 2026-09-24 | armed in the generator (`LIGHT_TEST_T1`) with the `[TOD_LIGHTSTATE]` log in `_tod_fall.gsc`; build record in docs/160 §8 | awaiting the user (green = Radiant State 1 only, red = State 2 only, hall west wall by the spawn) | pending | — |
| T2 | 2026-09-24 | armed (`SUN_SSI2`: `ssi2 = tod_ssi_cybercity`); FULL build 12:57:45, LED 100,163,686 B | the LED's per-state table reads `[tod_ssi_cybercity, tod_ssi_cybercity, default_day, default_day]` [VERIFIED decode]; the look is awaiting the user | data landed; look pending | — |
| T13 | 2026-09-24 | same build (A+B+D in one) | the LED went 50,487,469 → 100,163,686 B when `ssi2` was filled: a second filled state costs a second full bake (~+49.7 MB). BAKED (one bake; the timing rule says never read one bake's clock). | **answered**: ~50 MB LED per filled state | 02 (cost of a state) — pending edit |
| T3 | 2026-09-24 | armed (`SUN_PROBE_TARGET`: `info_null tod_sun_probe_target` at (490, −120, 200), `target` on the sun volume), same build | awaiting the user | pending | — |

The three ran in ONE build on purpose (the user asked for the atmosphere, not a
bisect); if the look moves in a way nobody expected, flip one switch OFF per
follow-up build.

---

## 8. For Tower of Doom II

Recommendations only. Nothing here was changed, built or played.

1. **Run the P0 builds before designing anything.** Build A (test lights + state log), then build B (`ssi2`), then build D (global probe target): three full builds, one change each, following the §7.1 rules. They answer T1, T2, T3 and T13 and tell us what the map actually does today. Every design chapter ([02](02_power_and_states.md), [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md)) depends on those answers.
2. **Then correct the records in §6,** starting with docs/107's "authored OFF before power" and the generator comment beside `SUN_VOLUME_TOP_MIN`, so the next session does not re-learn the off-by-one.
3. **Treat darkness as a budget of emissive area, sky light and exposure first, and lights second.**
   - Today the architecture glows on every face.
   - The sky light sits ~5.6 stops above stock `default_night` [INFERRED].
   - `tod_ssi_cybercity` clamps auto-exposure to EV 3–3.5 [VERIFIED], but it is only Radiant State 1's SSI; the live Radiant State 2's entry is `default_day` (EV 1–16) [VERIFIED], and which one the game actually applies is T2 [TEST].
   - Lights and states cannot fix the first two. T4 decides whether cutting emissive area also cuts bounce.
4. **Decide the lighting beats with THE FALL in mind.** Power now comes on at the first frame, so a "tower lights up at power" reveal has no dark period to contrast with. Either the user reverses that decision (docs/160_the_fall.md §6 lists it as reversible), or the beats key to events the descent does have: the Fall gate's seal, doors opening downward, the arrival at the plaza. [02 §14](02_power_and_states.md#14-architecture-choosing-a-mechanism) has the mechanisms.
5. **Do the probe rework (T18) as its own build.** It is the largest reflection lever and a map-wide look change. The user decides.
6. **Replace or remove the two stub zone lines** after T9, and vet every new effect with the [04 §17](04_fx_lights.md#17-the-placeholder-stub-trap-and-how-to-vet-an-effect) checklist.
7. **Keep the bake alive.**
   - Run `measure_lit_area.js` before and `_bake_test.ps1` after any fixture pass.
   - The crown is already 64% of lit area.
   - New lamps should be models or FX, not large brushes [COMMUNITY: project record].
8. **Add the missing tools when the rework starts:**
   - a lint for light origins inside solid brushes;
   - an FX lint (stub material, `pcloud`, precache ↔ zone line);
   - a lighting-state mask report;
   - a probe-coverage report (which rooms fall outside every box);
   - the LED per-state SSI reader as a repo tool;
   - an update to `measure_lit_area.js` groups for the spire, Undercity and wings.
9. **Judge every lighting build on the user's low config and a high config,** from the fixed spots, before and after any lighting switch. Keep new assets map-owned in the private workspace, and ask before using the shared-root control map.

---

## 9. Sources

**Official Treyarch docs** (MODTOOLS = `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`)

- **Lights:**
  - MODTOOLS/docs_modtools/Lighting_Parameters.pdf: stops, shadow budget p.11, fov_outer, exposure keys, PCSS disabled.
  - Culling_LOD_Lights.pdf: 200/300, 1/5.
  - Build_light.pdf.
  - Generate_LED.pdf: "When Geo changes, or if Lighting has changed".
- **Sun, sky and probes:**
  - SunSky_Light_SetUp.pdf: sun volume limits, live-update vs rebake, Export Local Probes, shadowSplitDistance.
  - Lighting_Probe_Workflow.pdf: global probe at the centre, target an info_null, buried warning.
  - Probe/Reflection_Probes.pdf: 8 closest probes, virtual probes, debug_render_index memory.
  - Probe/Priority_Probes.pdf.
  - Probe/Multiface_Probes.pdf.
  - Probe/Subtract_Probes.pdf.
- **FX:** FX_Lights.pdf (loop rule, no Never shadows, per-instance overrides, exploders).
- **Materials:** Materials.pdf (lampshade p.16-17, emissive 2^EV p.18); PhysicallyBasedRendering.pptx (probes 256², transparency cost, albedo 40–238).
- **Workflow and API:** Multiplayer_Lighting_Workflow.pdf (exposure doctrine, bake override); Mini_Map_Setup.pdf; bo3_scriptapifunctions.htm (SetLightingState, GetLightingState, exploder and bank functions, SetSunShadowSplitDistance).
- Text copies used for re-checking are in the session scratchpad `lightdocs/*.txt`.

**Entity and asset definitions**

- MODTOOLS/bin/t7.def.json:
  - `light`, `volume_sun`, `reflection_probe`, `volume_exposure`, `volume_litfog` / `volume_worldfog`, `pbg_box`, `vlut_box`, `vbloom_box`, `vcolor_*`, `volume_performance`, `fx`;
  - worldspawn shadow slices (numOmniShadowSlices 24 / 8–256, numSpotShadowSlices 64 / 8–1024);
  - maxDynamicShadows 12 / 0–24.
- MODTOOLS/deffiles/material.awi (scaleRGB "HDR Scale" :1543, skyScaleRGB obsolete :634, gloss 0–17), ssi.awi, fog.awi, light.awi, lightdescription.awi.
- MODTOOLS/bin/Radiant_modtools.exe and cod2map64.exe strings: light, sun, probe, exploder (`Total Exploders: 0/120`) and FX limit messages; `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE`; `NO BAKE STATE %d using %d`; the `Diffuse GI Only` / `Specular GI Only` render flags.

**Stock scripts and data**

- MODTOOLS/share/raw/scripts:
  - zm/zm_usermap.gsc:110;
  - zm/gametypes/_globallogic_spawn.gsc:501;
  - shared/util_shared.gsc:2975-3006;
  - zm/zm_giant.gsc:132,428,571;
  - zm/zm_giant_fx.csc:69-71,184-293;
  - shared/exploder_shared.gsc:275-285,663-668,761-819 and .csc:297-424;
  - shared/load_shared.gsc:55,60;
  - zm/_zm_perks.gsc:113-161,280-316;
  - zm/_zm_perk_quick_revive.gsc:185,791;
  - zm/_zm_trap_electric.csc:20-37;
  - zm/_zm_perk_random.csc:104,116;
  - zm/zm_usermap.csc (include_perks), zm/_zm_power.gsc (no lighting calls), zm/_zm_perk_*.gsh (disabled model == active model);
  - zm/_zm.csc (eye-glow overrides);
  - shared/visionset_mgr_shared.csc;
  - zm/_art.gsc:226.
- MODTOOLS/map_source/_prefabs/zm/zm_giant/zm_giant_light.map (543 lights, 176 probes, 96 fx, state_alias_2 power_off, volume_sun target auto11353318; three placements of light/zm_giant_teleporter.map, 34 lights each); map_source/zm/zm_giant.map (worldspawn exposure, omni slices 96); map_source/_prefabs/zm/zm_core/vending_*.map (perk prefab lights 0000).
- MODTOOLS/source_data/ssi.gdt (default_night, default_day, default_sunset, zm_factory, zm_zod), fog.gdt, acc_nastian_t9_skyboxes.gdt (the t9 SSI exposure ranges); MODTOOLS/share/raw/fx (stub and loop-rule scans; dirt/fx_dust_motes_200x200).
- Player settings: `Call of Duty Black Ops III/players/config.ini` (VolumetricLightingEnabled, DisableDynamic*Shadows, SSAOTechnique, TextureQualityBakedSunShadows, TextureQualityProbes).

**This repo**

- Generator and map: tools/gen_tower_map.js (`light()` ~7166, `BASE_LIGHT_BAKE` ~7188-7201, `probe()` ~7303, `volume_sun` ~7376, `SUN_VOLUME_TOP_MIN` :1557, comments :1545-1547, :6091, :7365); map_source/zm/zm_tod2_cybercity.map.
- Build tools:
  - tools/build_map.ps1 (:155-158, :177-186, :897-915);
  - tools/_bake_test.ps1;
  - tools/measure_lit_area.js (run 2026-09-24);
  - tools/lint_tod_geometry.js:114;
  - tools/audit_hidden_faces.js;
  - tools/xpak_report.js;
  - tools/capture_ai_logs.ps1.
- Zone and scripts: zone_source/zm_tod2_cybercity.zone:431,451; scripts/zm/zm_tod2_cybercity.gsc:247; scripts/zm/zm_tod2_cybercity/_tod_fall.gsc (power_on), _tod_atmosphere.gsc, _tod_perk_lights.gsc/.csc, _tod_rampage.gsc.
- Docs:
  - docs/BO3_MAPMAKING_KB.md (§0, §1 LED ceiling, §4, :65, :170, :200, :377);
  - docs/104_cybercity_sky.md (§1, §4, §4b-§4d, §4g, §4k);
  - docs/107_sun_volume_yellow_postmortem.md;
  - docs/150_tod2_evil_sky.md;
  - docs/154_tod2_isolation.md;
  - docs/155_fx_art_workflow.md;
  - docs/158_tod2_base_layout.md;
  - docs/160_the_fall.md (spawn in the crown hall, power on from the first frame; §6 lists that as reversible);
  - CLAUDE.md.
- Private workspace: C:\BO3Tools\TOD2Cybercity\share\raw\maps\zm\zm_tod2_cybercity.led (size, SSI state table).

**Map One and the control map**

- c:/Users/jorda/Repositories/abandoned_cyber_city_zombies: scripts/zm/zm_abandoned_cyber_city.gsc:955-973 (CheckForPower; state calls at :957 and :972); tools/oneshots/gen_room_roofs.js:26-60; _acc_atmosphere.gsc:490-530; CHANGELOG.md (~17229-17245, ~17570, 18275-18285, 55-68); docs/20_atmosphere_and_materials.md; docs/44.
- c:/Users/jorda/Repositories/test+map (build.ps1:6-25 writes to the shared root; commit 1db8a3f step 2 unbuilt).

**Community**

- modme forum archive (github.com/dtzxporter/ModmeForum), threads:
  - 293 (spec_comp), 304 and 2987 (light bleed), 329/383 (probes brighten outdoors);
  - 360/510/2061 (shadowSplitDistance), 459 (distance culling), 472/1950 (perk prefab lights), 477 (day SSI stops), 496 (fast_restart);
  - 571, 1077 and 3395 (lighting states and ssi2), 2029 (exploders), 2118 (power-on hitch);
  - 3280 (FX limits), 3307 (buried sun centre), 3557 (black water).
- Steam Mod Tools discussions 2592234299570231550, 340412619134508371, 350543951935346956, 135514507322573601, 3424437779948829805.
- UGX 12772 (decimal comma), 13226 (perk prefab lights).
- VerK0 Lighting Tutorial parts 1–5 (YouTube).
- Treyarch SIGGRAPH 2016 "Volumetric Global Illumination at Treyarch" (https://www.activision.com/cdn/research/Volumetric_Global_Illumination_at_Treyarch.pdf).
