# 08 — Fixture cookbook: lamps, street lamps, neon, fire, alarms and the power-on reveal

**In short.** A lamp in Black Ops III is never one object. It is a model you can see, something that makes the bulb *look* lit (an emissive or "lampshade" material, or a glow sprite), a separate invisible light that actually lights the room (a Radiant `light` or an FX light), usually a reflection-only twin so that shiny floors show it, and a switch (lighting state, exploder or script) that decides when it is on. This chapter gives one recipe per fixture, built from those parts, with Treyarch's own numbers from The Giant wherever Treyarch built the same kind of fixture. Every value is a starting point read from stock data or community practice. None of it has been seen in game on Tower II, and every state mask here depends on one open question settled in [02](02_power_and_states.md): which Radiant State the game really shows while Tower II's sun volume has no `ssi2`. The last recipe, the power-on reveal, combines everything into the "a floor goes from dark to lit" moment.

**Read this when…** you are about to add any light fixture, want to know what Treyarch did for the same object, or are planning the power-on moment. New to BO3 lighting? Read the [README](README.md) first. For the theory behind each part, follow the links to [01 lights](01_lights.md), [02 power and states](02_power_and_states.md), [03 glow and perks](03_glow_and_perks.md), [04 FX lights](04_fx_lights.md), [05 sun, sky, exposure, fog](05_sun_sky_exposure_fog.md), [06 reflections and probes](06_reflections_probes.md) and [07 water](07_water.md); for design principles see [09](09_design_and_inspiration.md), and when something looks wrong see [10](10_troubleshooting_limits_history.md).

**Contents**
- [0. How every recipe is built](#0-how-every-recipe-is-built)
- [1. Ceiling downlight](#1-ceiling-downlight)
- [2. Hanging cage lamp and hurricane lantern](#2-hanging-cage-lamp-and-hurricane-lantern)
- [3. Street lamp: the full walkthrough](#3-street-lamp-the-full-walkthrough)
- [4. Wall sconce](#4-wall-sconce)
- [5. Fluorescent tube (area light)](#5-fluorescent-tube-area-light)
- [6. Neon sign](#6-neon-sign)
- [7. TV, monitor, hologram](#7-tv-monitor-hologram)
- [8. Spotlight and searchlight with a cookie](#8-spotlight-and-searchlight-with-a-cookie)
- [9. Fire: burning barrel, torch, candle, big fire](#9-fire-burning-barrel-torch-candle-big-fire)
- [10. Flickering broken light](#10-flickering-broken-light)
- [11. Emergency, alarm and status lights](#11-emergency-alarm-and-status-lights)
- [12. Lit window at night](#12-lit-window-at-night)
- [13. God-ray shaft](#13-god-ray-shaft)
- [14. Perk-machine light pool](#14-perk-machine-light-pool)
- [15. Teleporter pad light](#15-teleporter-pad-light)
- [16. Water caustics](#16-water-caustics)
- [17. The power-on reveal: a floor going from dark to lit](#17-the-power-on-reveal-a-floor-going-from-dark-to-lit)
- [18. Quick reference: which layers each fixture needs](#18-quick-reference-which-layers-each-fixture-needs)
- [For Tower of Doom II](#for-tower-of-doom-ii)
- [Sources](#sources)

---

## 0. How every recipe is built

### 0.1 The five layers of a fixture

Think of a real street lamp. You see the pole and head (the **model**). You see the glass glowing (the **visible source**). You see a pool of light on the pavement (the **light**). You see the lamp reflected in a wet road (the **reflection**). And it turns on at dusk (the **switch**). BO3 builds each of those separately.

| Layer | What it does | BO3 tools | Theory |
|---|---|---|---|
| 1. Model | The object you see | `misc_model` / `script_model`, or brushes | — |
| 2. Visible source | Makes the bulb, tube, screen or sign look lit | Emissive material (`lit_emissive*`), backlit "lampshade" material (`lit_backlit*`), glow sprite FX | [03](03_glow_and_perks.md), [04](04_fx_lights.md) |
| 3. Light | Lights the walls, floor, players and zombies | Radiant `light` (omni or spot), or an FX light (`dynamicLight2` element in an `.efx`) | [01](01_lights.md), [04](04_fx_lights.md) |
| 4. Reflection side | Makes the fixture show up in reflections and baked bounce | A fitted `reflection_probe`, plus a `PROBE_ONLY` twin light for FX-lit fixtures | [06](06_reflections_probes.md) |
| 5. Switch | Decides when the fixture is on | Lighting state (`lightingstate1..4`, `fxstate1..4`), Radiant exploder, script (model swap, FX play/stop) | [02](02_power_and_states.md) |

Two facts drive every recipe:
- **A glowing surface is not a light.** No doc, material field or `lit_emissive` render flag was found that makes an emissive surface a light source in the bake; the sky material is the one documented emissive light source [VERIFIED] (absence in docs_modtools, deffiles/material.awi, share/raw/techsetdefs_stable). Whether a big emissive surface feeds probe-based bounce is untested [TEST]. Treyarch's docs say the lampshade shaders "are meant to be used with a light placed behind them to provide the actual glow and illumination" (src: docs_modtools/Materials.pdf p.17) [VERIFIED]. So: **if it should light anything, pair it with a light.**
- **An emissive surface does not follow power by itself.** The same doc says the lampshade shaders exist so "we don't have to dial in and sync up a bunch of emissive materials" [VERIFIED], which implies emissive glow does not switch with lights [INFERRED]. Switchable glow must live on an entity (model swap or script-driven material), never on a world brush face, which is compiled into the BSP [INFERRED] (see [03](03_glow_and_perks.md)).

### 0.2 Notation used in the recipes

- **State masks.** "Mask `1011`" means `lightingstate1 1`, `lightingstate2 0`, `lightingstate3 1`, `lightingstate4 1` on the entity. The same notation is used for `fxstate1..4` on `fx` entities.
- **Radiant State N vs script state n.** "Radiant State N" is the `lightingstateN` checkbox. "Script state n" is the argument of `util::set_lighting_state(n)`. Script state n shows Radiant State n+1 [INFERRED] (strongly supported: The Giant's prefab worldspawn aliases Radiant State 2 `power_off`, `zm_usermap::main` boots script state 1 (share/raw/scripts/zm/zm_usermap.gsc:110), and The Giant calls `set_lighting_state(0)` at power-on (zm_giant.gsc:571)). Details and both working conventions: [02](02_power_and_states.md).
- **This chapter assumes the Giant convention** unless it says otherwise: the map boots in Radiant State 2 (pre-power), and one call `level util::set_lighting_state( 0 );` at power-on switches to Radiant State 1 (powered). So:
  - always on: mask `1111`
  - pre-power only (dim twin, emergency lamp): mask `0111`
  - powered only: mask `1011` (The Giant's most common power-gated mask, 119 lights) or `1000` (34 lights)
  (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map, parsed) [VERIFIED].
  - If you use the **Map One convention** instead (`set_lighting_state(0)` at start, `(1)` at power), swap the first two digits: pre-power only = `1011`, powered only = `0111` [INFERRED] (same mapping).
- **Stops.** Brightness unit. +1 stop is twice as bright [INFERRED] (about 400 of the Giant's 489 non-integer stops values are log2 of round numbers, e.g. 8.9658 = log2 500; the entity definition also describes `spec_comp` and `volumetricIntensityBoost` as "(in stops)", bin/t7.def.json). So Giant values like 4.64 / 5.64 / 8.97 / 9.97 are 25 / 50 / 500 / 1000.
- **Third-party data.** Some values come from community packs installed in the shared tools root (the vertigo neon pack, Map One's T7/T8 ports, Wraith-extracted effects). Their tag [VERIFIED] means the file was read; it does not make them Treyarch originals. Each such source is named where it is used.
- **FX intensity ≈ 2^stops.** An FX light with intensity graph 500 matches a Radiant light at stops ≈ 8.97 [INFERRED] (holds for 30 of 38 per-placement Giant fire FX lights and their Radiant twins, a strong pattern, not an invariant).

### 0.3 Calibrating stock numbers to a dark map

Brightness only means something against exposure (the camera's EV, which works like a camera's shutter and aperture). The same `stops` value reads strong under a dark map's low exposure and weak under a daylight exposure [INFERRED]. EV numbers describe how bright the place being exposed for is: Treyarch's MP doc puts sunlit exteriors at EV 12 and interiors at 11 or lower, the Materials doc's example interior is EV 3, and stock night SSIs clamp around EV 0.5–3.5 (src: Multiplayer_Lighting_Workflow.pdf; Materials.pdf p.18; source_data/ssi.gdt) [VERIFIED]. So a low EV is the camera opened up for a dark place, and raising the EV applied to a given scene renders it darker [INFERRED].

| Map | Exposure settings | Typical light stops | Source |
|---|---|---|---|
| The Giant (Treyarch ZM, night) | worldspawn `evmin 3`, `evmax 3.5`, `evcmp 2.5`; SSI `zm_factory` EV 0.5..3.5, evcmp 4; `volume_exposure` volumes EV 0.5..3.5, evcmp 3.75–4.87 | median 7 (p10 4.0, p90 10.6) | map_source/zm/zm_giant.map:57-60; source_data/ssi.gdt; zm_giant_light.map [VERIFIED] |
| Tower II | SSI `tod_ssi_cybercity` EV 3..3.5, evcmp 2.5 (a copy of stock `default_night`) | all 344 lights at stops 6 | source_data/tod_skybox.gdt; map_source/zm/zm_tod2_cybercity.map [VERIFIED] |
| mp_sector (MP, day) | MP rule: exposure "ALWAYS" 8–12 | median 15 | Multiplayer_Lighting_Workflow.pdf; mp_sector_light.map [VERIFIED] |

Which of worldspawn, SSI and exposure volume wins is undocumented [TEST]. Still, The Giant's clamp numbers sit close to ours, so **Giant light values are the best stock starting point for Tower II** [INFERRED]. Do not copy MP stops; they sit ~8 stops higher because MP exposes at EV 8–12 [INFERRED].

Two more calibration rules:
- **Emissive brightness.** Treyarch's shortcut: HDR Scale (`scaleRGB`) = 2^EV of the area, e.g. EV 3 gives 8 (src: Materials.pdf p.18) [VERIFIED]. For our EV 3–3.5 that is scaleRGB ≈ 8–11 [INFERRED] (arithmetic). Doubling scaleRGB is +1 stop of glow [INFERRED].
- **Use `stops`, not `bake_intensity_scale`, to set brightness.** The entity definition describes `bake_intensity_scale` as "Adjusts the brightness of a light for GI baking" and `stops` as "Controls how bright a light is" (src: bin/t7.def.json) [VERIFIED]. Whether `bake_intensity_scale` also changes the direct pool is untested [TEST]. The Giant never sets it (0 of 543 lights) [VERIFIED].

Our generator's lights are "weak and wide", Treyarch's are "strong and tight". The entity definition says `falloffdistance` (default 12) is the "Distance at which inverse square distance attenuation starts to take effect" (src: bin/t7.def.json) [VERIFIED]. Under that simple inverse-square model, our base omni (stops 6, falloffdistance 12) gives ≈ 64 × (12/240)² ≈ 0.16 at 240 units, while a Giant hanging-lamp spot (stops 8.97, falloffdistance 12) gives ≈ 7.2 at 100 units [INFERRED] (model; the engine's full falloff curve, including `far_edge`, is undocumented). That gap is why the recipes below use higher stops and much smaller radii than `tools/gen_tower_map.js` `light()`.

### 0.4 Rules that apply to every recipe

1. **In this repo, every light, probe, SSI, material or state-mask change is a FULL build.** Treyarch's doc says a new LED is needed "When Geo changes, or if Lighting has changed" (src: docs_modtools/Generate_LED.pdf) [VERIFIED]; this repo's `build_map.ps1` has no LED-only mode and `-GscOnly` skips cod2map and the LED bake (CLAUDE.md), and GDT edits are always full builds here. A script-only change (for example a new `set_lighting_state` call) is not. Build and stop; the user tests.
2. **New assets are map-owned.** Materials, models and `.efx` files for Tower II go into map-owned sources installed through the private workspace `C:\BO3Tools\TOD2Cybercity`, never the shared Mod Tools root (docs/154). Never edit a stock asset in place; clone it under a `tod_` name.
3. **Shadows are opt-in.** `PRIMARY_NOSHADOWMAP` defaults to true (src: bin/t7.def.json) [VERIFIED]. A shadowless light passes through walls and floors [COMMUNITY] (modme 2987, UGX 14935). For a cheap static shadow use `PRIMARY_NOSHADOWMAP 0` + `shadowUpdate Never` ("Only render the shadowmap once when missing", t7.def.json) [VERIFIED]; that characters then receive but do not cast these shadows is [INFERRED] from the Build_light doc's description of static shadows. `shadowUpdate Always` spends the live budget: about 12 live 512² shadows at scale 1 (src: Lighting_Parameters.pdf p.11) [VERIFIED]. FX lights cannot use `Never`: they are "either Always live, or Off" (src: FX_Lights.pdf p.2) [VERIFIED], so FX lights get `PRIMARY_NOSHADOWMAP 1` unless the shadow is the point (88% of stock FX lights do this) [VERIFIED].
4. **Start the light past the housing.** `cut_on` "is useful when you want to bury the origin of a light inside of a prop but want the effects of the light to start later" (src: Lighting_Parameters.pdf) [VERIFIED].
5. **Keep spot cones ≤ 120°.** "Lights larger than 120 degrees tend to suffer from artifacts and low-res shadows" (src: Lighting_Parameters.pdf) [VERIFIED].
6. **Cull every light.** `culling_cutoff` / `culling_falloff` in on-screen pixels at 1080p. Doc starting values 200/300, and 1/5 for lights under radius 10 (src: Culling_LOD_Lights.pdf) [VERIFIED]. The Giant uses 200/300 on 210 lights and 5/25 on 158 small ones [VERIFIED].
7. **A placed Radiant light does not flicker by itself.** Treyarch's documented workflow "for lights that flicker or change intensity" is an FX light (src: FX_Lights.pdf p.1) [VERIFIED]. The one Radiant-only trick is a scrolling cookie on a spot (recipes 8 and 10). A `scriptable` ServerSide light can be driven with `SetLightIntensity`, but no stock script does so [VERIFIED] and community threads call those calls deprecated [COMMUNITY] (modme 2029).
8. **Vet every stock effect before zoning it.** Grep the `.efx` for `gfx_debug_missing_fx` (a placeholder; zoning it is recorded by this project to pack a blank effect [COMMUNITY] (project record)), for `pcloud` (a project-recorded first-render crash class [COMMUNITY] (project record)) and for quoted child-effect paths (the linker's asset ledger shows children of zoned effects packed automatically, but for a weapon, viewmodel or projectile effect add the child's own `fx,` line as insurance and test it). Full checklist: [04](04_fx_lights.md).
9. **Judge on two graphics configs.** The user's own `players/config.ini` has `VolumetricLightingEnabled 0`, `DisableDynamicLightShadows 1`, `DisableDynamicSunShadows 1` and SSAO off [VERIFIED]. Volumetric beams and live light shadows will not show in the user's playtests. Readability must never depend on them.

### 0.5 Treyarch's lamp numbers at a glance

All from `map_source/_prefabs/zm/zm_giant/zm_giant_light.map` and its `light/` sub-prefabs unless noted [VERIFIED].

| Role | Type | Shape | Radius | Stops | Shadows | Culling |
|---|---|---|---|---|---|---|
| Bulb glow (inside a cage/shade) | omni | `falloffdistance 5`, `far_edge 0.75` | 15 | 4.64–5.64 | none | 5/25 |
| Hanging-lamp pool | spot, `volumetric 1`, `falloffdistance 12` | `fov_outer 50–55`, `cut_on 17–26` | 141–420 | 5.64–10.55 (most 7.6–10) | live (`shadowUpdate Always`) | 200/300 |
| IES-cookie downlight | spot, `def cuc_ies_029` | `fov_outer 60–80`, `cut_on 20–21` | 142–252 | 6.64–9.97 | live | 200/300 |
| Lantern reflection fill | omni, `PROBE_ONLY 1` | — | 60–700 | 3.64–9.23 | — | none |
| Burn-barrel reflection fill | omni, `PROBE_ONLY 1` | `falloffdistance 6–12` | 125–300 | 5.0–7.97 | — | none |
| Lantern FX light | FX omni | loop 1000/1000 | 208 | intensity 60 | live | — |
| Barrel FX light | FX omni | loop 600/600 | 150 | intensity 100 | live | — |
| Red/green status lamp | omni in an exploder | — | 20 | 5.64 (green), 6.64 (red) | — | — |
| Tesla flicker beam | spot, `def cookie_flicker02` | `fov_outer 120`, `cut_on 10` | 60–70 | 3.5–5 | none | 20/150 |
| Moonlight | spot, `ENABLE_FALLOFF 0`, `target moon` | `fov_outer 55–90`, about 18,000–40,000 units away | 12,000–22,000 | -1 to 6.73 | none | 200/300 |

---

## 1. Ceiling downlight

**What the player sees.** A fixture flush with (or just below) the ceiling, a bright lens, a clean pool of light on the floor, and walls that fall off into darkness above.

**Follows.** The Giant's hanging-lamp pool spot (recipe 2) with the lamp body removed; the IES-cookie spots in the Giant light prefab; VerK0's ceiling-light advice [COMMUNITY]. One deliberate difference: every Giant lamp-pool and IES spot uses live shadows (`shadowUpdate Always`) [VERIFIED]; this recipe suggests static shadows (`Never`) because live ones spend the ~12-shadow budget (rule 3). Switch one hero lamp to `Always` if moving shadows matter there.

| Part | Choice | Suggested keys | Why |
|---|---|---|---|
| Model | Recessed can, panel or brush with a lens face | — | The visible fixture |
| Lens | `lit_emissive` with an emissive map that is black except the lens, dark Color Map; or `lit_backlit` diffuser with the light behind it | `scaleRGB 8` (EV 3) | Emissive for an always-on lamp; backlit if the lamp must switch with the light (Materials.pdf p.17) |
| Main light | `PRIMARY_SPOT` aimed down | no `angles` or `angles 90 0 0` (step 2); `cut_on` just past the lens (4–10 for a flush can; Giant cage spots 20–25); `fov_outer 60–100`; `radius` ≈ 1.5 × ceiling height; `stops 8–10`; `roundness 1`; `PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`; `culling_cutoff 200`, `culling_falloff 300` | The pool on the floor |
| Optional shaping | Feathered or disc-shaped pool | lower the inner `superellipse` values (e.g. 0.75 → 0.1) [COMMUNITY] (VerK0); `ortho_effect` ("Creates an orthographic effect for spot lights", t7.def.json), Giant range 0.2–0.35 [VERIFIED], used for disc-shaped pools [COMMUNITY]; `far_edge` low (VerK0 uses 0.1) for a soft end [COMMUNITY] | Softer, less "cone-like" pool |
| Optional cookie | IES profile | `def cuc_ies_029` (Giant) or `cuc_ies_006/017/026/cust_02` | A realistic beam pattern [INFERRED] (from the `cuc_ies_*` names) |
| Reflection | Fitted room probe | see [06](06_reflections_probes.md) | Floors and fixtures reflect correctly |
| Switch | Powered `1011`; optional pre-power twin `0111` about 1 stop dimmer | Giant median gap between twins is +1 stop [VERIFIED] | Dim before power, bright after |

**Steps**
1. Place the fixture model. Put the lens material on a separate material slot or face.
2. Place a `light`, set `PRIMARY_TYPE PRIMARY_SPOT`, origin 2–4 units above the lens inside the fixture, aimed down. The Giant's IES downlights and most of its lamp-pool spots carry no `angles` key at all (98 of its 263 spots have none) [VERIFIED], which suggests an un-angled spot points straight down [INFERRED]; `angles 90 0 0` (pitch +90) should also aim down [INFERRED]. Confirm with the cone preview in Radiant.
3. Set `cut_on`, `fov_outer`, `radius` and `stops` from the table. Keep `fov_outer` ≤ 120.
4. Turn on static shadows (`PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`) so the pool stops at walls and does not leak through the floor into the room below.
5. Add culling keys. Set the state masks.
6. Full build. Judge from a same-spot screenshot.

**Placement tips.** Centre pools over the walking path, not over walls. In a dark map, leave dark gaps between pools; players move toward light [COMMUNITY] (Valve Left 4 Dead commentary). `roundness` 0 gives a rectangle and 1 a circle (t7.def.json) [VERIFIED].

**Dark-map notes.** The pool is the only lit thing, so the floor under it must not be pure black: Treyarch's PBR deck asks for albedo "No values below 40" (PhysicallyBasedRendering.pptx slide 10) [VERIFIED]. On Tower II the vertigo floors are `$white_diffuse` + white specular + `reflectionProbeAmount 1`, so a coloured pool will tint the floor strongly and reflections will depend on the probe [VERIFIED] (material values; look [INFERRED]).

---

## 2. Hanging cage lamp and hurricane lantern

### 2a. The Giant's electric cage lamp

**What the player sees.** A small bulb inside a metal shade or wire cage hanging from the ceiling; the bulb glows, the shade interior glows warm, and a pool of light spreads below.

**Follows exactly.** `map_source/_prefabs/zm/zm_giant/geo/zm_giant_light_cage_03.map` is models only: `p7_zm_der_light_shade`, `p7_zm_der_light_socket_02` (angles 180 0 0, origin 0 0 -3.5) and `p7_zm_der_light_bulb_small` (origin 0 0 -5) [VERIFIED]. Its lights live in the light prefab: `zm_giant_light.map` places the 38 `cage_03` prefabs itself (plus 25 `cage_06`, 6 `cage_01`, 2 `cage_04`, 2 `cage_05`) and puts the bulb omni and pool spot at each one [VERIFIED]. The wall-mounted version, `geo/zm_giant_light_cage_05.map`, is `p7_zm_der_light_wall_mount` plus the `cage_04` lamp prefab offset 29.75 units out [VERIFIED].

| Part | Treyarch value | Source |
|---|---|---|
| Bulb glow, powered | `PRIMARY_OMNI`, `radius 15`, `stops 5.64` (= 50), `_color 1 0.749 0.451`, `PRIMARY_NOSHADOWMAP 1`, `falloffdistance 5`, `far_edge 0.75`, `culling 5/25`, mask `1011` | zm_giant_light.map (9 lights) [VERIFIED] |
| Bulb glow, pre-power twin | same, `stops 4.64` (= 25, one stop dimmer), mask `0111` | zm_giant_light.map (6 lights) [VERIFIED] |
| Pool spot | `PRIMARY_SPOT` with no `angles` key, `fov_outer 50–55`, `cut_on 17–26`, `radius 141–420`, `stops 5.64–10.55` (most 7.6–10), warm `_color` ≈ `1 0.73 0.39`, live shadows (`PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Always`), `volumetric 1`, `falloffdistance 12`, `culling 200/300`. Twins at the same spot: `0111` 6.64 / `1011` 7.64 (radius 141), `0111` 8.97 / `1011` 9.97 (radius 420), `0111` 9.97 / `1011` 10.55 (radius 331); always-on examples at `1111` 9.97 | zm_giant_light.map (spots within ~15 units of the 38 placed `cage_03` prefabs) [VERIFIED] |

**Steps**
1. Place shade, socket and bulb models. Give the bulb an emissive material (`lit_emissive`, warm tint, scaleRGB 8–16; the ported Origins warning-lamp `_on` material in the shared tools root, `mtl_p7_zm_ori_light_warning_metal_on`, is `lit_emissive` at 8 [VERIFIED]). Give the shade `lit_backlit` if its interior should glow from the bulb light, which is what the lampshade shaders are for (Materials.pdf p.17) [VERIFIED] (doc intent; look [TEST]).
2. Place the **bulb glow** omni at the bulb with the values above. It lights the inside of the shade, not the room.
3. Place the **pool spot** at the bulb, aimed down. `cut_on` starts the light below the shade: the doc says it is for burying a light's origin inside a prop while the light starts later (Lighting_Parameters.pdf) [VERIFIED], which keeps the shade from casting a huge shadow over the pool [INFERRED]. Treyarch's pool spots cast live shadows; use `shadowUpdate Never` on all but a hero lamp (recipe 1).
4. For dim-before-power, duplicate each light: pre-power copy at mask `0111` one to two stops dimmer, powered copy at `1011` (the Giant's pattern) [VERIFIED].
5. Optional: `volumetric 1` for a visible cone (needs recipe 13's fog volume; invisible on the user's config).
6. Full build.

**Why two lights for one lamp.** One light cannot both glow tightly inside a shade and throw a wide pool with a clean start. VerK0 teaches the same pair (inner no-shadow light plus a room light with `cut_on`) and notes that an emissive bulb instead of the inner light saves an entity [COMMUNITY].

### 2b. The Giant's hurricane lantern (flame lamp)

**What the player sees.** A glass lantern with a flickering flame; warm light wobbling on nearby walls.

**Follows exactly.**
- `geo/lantern_lit.map`: `misc_model p7_zm_der2_light_hurricane_lamp` (mask `1111`) and an `fx` entity `fire/fx_fire_lamp_hurricane` with `delay -19855`, `fxstate1..4 1`, `primaryLightFraction 1`, `timescale 1` [VERIFIED]. The flame effect has no light element [VERIFIED] (0 `dynamicLight2`).
- In the light prefab, at each lantern: an `fx` entity `light/fx_light_lantern_factory_zmb` (FX omni, shadowed, intensity 60, radius 208, a hand-drawn wobbly intensity curve, loop interval = lifetime = 1000 ms) [VERIFIED], plus `PROBE_ONLY 1` omnis noted `GRP_lantern_probe` (`_color 1 0.4588 0.1608`, radius 60–700, stops 3.64–9.23, mask `1111`) [VERIFIED].
- Also `GRP_lantern_direct` Radiant omnis (radius 100–150, stops 5.64–7.97, `cut_on 6–7`, culling 200/300), most of them parked at mask `0000` [VERIFIED]. What an all-zero light does is undocumented; the room light here comes from the FX light [INFERRED].

**Steps**
1. Lantern model plus a flame FX at the wick.
2. Room light = an FX light with a flicker curve, loop interval = lifetime (recipe in [04](04_fx_lights.md)). Start from `light/fx_light_lantern_factory_zmb` (clean source: no placeholder, no pcloud) [VERIFIED]. Keep it shadowless unless it is a hero lantern.
3. Add a `PROBE_ONLY 1` omni at the same spot, same colour, radius about the FX radius or larger, stops ≈ log2(FX intensity) (Giant pattern: 67 of 94 light-FX placements have a PROBE_ONLY light within 12 units) [VERIFIED]. "If enabled this light will only be seen by the reflection probes" (t7.def.json) [VERIFIED]. Its purpose, making an FX-lit lamp show up in reflections and bounce, is [INFERRED].
4. Give each placed copy a different negative `delay` (Giant: −15,579 to −27,220 on its barrel fire lights) so identical lamps do not flicker in unison [VERIFIED] (values; purpose [INFERRED]).
5. Full build.

**Dark-map notes.** Flame lamps are the most "motivated" light a dark map can have (a visible source you believe) [COMMUNITY] (Level Design Book). Warm flicker against a cool ambient reads well [COMMUNITY]. Keep the count low: each shadowed FX light costs a live shadow.

---

## 3. Street lamp: the full walkthrough

**What the player sees.** A pole with a lamp head; the lens glows; a cone of light lands on the ground in a soft-edged pool; the pool shows in wet or shiny floors; moths of dust or snow drift in the beam; the lamp is dark, dim or flickering before power and comes on after.

**Follows.** The Giant has **no street lamp**: its utility pole prefab `geo/zm_giant_utility_pole_01.map` is models only, with no light [VERIFIED]. This recipe assembles Treyarch pieces that do exist: the cage-lamp pool spot (2a), the IES-cookie spots and their power twins, the bulb glow omni, the `PROBE_ONLY` fill (2b) and a sodium lens flare. A stock-named street-light effect also exists, `dlc1/castle/fx_light_castle_streetlgt` (an omni of intensity 1024, radius 10, plus a spot of intensity 2048, radius 300, both `PRIMARY_NOSHADOWMAP 1`, loop 500/500), but its source file is a community Wraith extraction, not a Treyarch original [VERIFIED] (file; render [TEST]).

### 3.1 The parts

| # | Part | Choice | Suggested keys (starting values) | Confidence |
|---|---|---|---|---|
| 1 | Pole and head | A model, or brushes for a blockout | Map One's plan named `p7_zm_tra_street_lamp_full`; its availability here is unverified | [COMMUNITY] |
| 2 | Lens / head glass | `lit_emissive` with black everywhere except the lens (always on), or `lit_backlit` lens with the light behind it (switches with the light) | `scaleRGB 8–11` for our EV 3–3.5; warm or cool tint | [VERIFIED] (rule; values [INFERRED]) |
| 3 | Main pool light | `PRIMARY_SPOT` inside the head, aimed down | aim as in recipe 1 step 2 (tilt 10–20° toward the path if you like); `cut_on` just past the lens (Giant lamp spots 16–26); `fov_outer 80–110` (≤120); `radius` ≈ 1.5–2 × lamp height; `stops 8–10`; `roundness 1`; `far_edge` 0.5–0.85 | [INFERRED] (from Giant pool and IES spots) |
| 4 | Beam pattern | Cookie | `def cuc_ies_029` (the Giant's IES spots: `fov_outer 60–80`, `cut_on 20–21`, `radius 142–252`) | [VERIFIED] (values; "IES" [INFERRED] from name) |
| 5 | Shadows | Static | `PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`; `Always` only for one hero lamp (the Giant's IES spots use `Always`) | [VERIFIED] (keys; budget choice [INFERRED]) |
| 6 | Culling | Normal | `culling_cutoff 200`, `culling_falloff 300` | [VERIFIED] |
| 7 | Head glow | Tiny omni at the lens | `radius 15`, stops 4.6–5.6, `PRIMARY_NOSHADOWMAP 1`, `falloffdistance 5`, `far_edge 0.75`, culling 5/25 | [VERIFIED] |
| 8 | Reflection fill | `PROBE_ONLY 1` omni | radius ≈ 2 × pool radius, stops 1–2 below the main light, same colour | [INFERRED] (from Giant lantern/barrel fills) |
| 9 | Probe | A `reflection_probe` whose box wraps the street, floor plane on the ground | see [06](06_reflections_probes.md) | [VERIFIED] (official guidance to fit boxes) |
| 10 | Lens flare (optional) | FX `lensflares/fx_lensflare_light_grime_md_yellow` → `lf_light_sodium_lamp_sm.klf` (the `.efx` names the flare by GUID) | spawn range limits apply (stock flares 500–2000) | [VERIFIED] (mapping; render [TEST]) |
| 11 | Beam atmosphere (optional) | `volumetric 1` + `volumetricSampleCount 1–4` + a local `volume_litfog`; or a sprite cone FX | recipe 13 | [VERIFIED] (keys; look [TEST]) |
| 12 | Particles in the beam (optional) | Lit motes or snow | The Giant places `dlc0/factory/fx_snow_lamp_flurry_50_factory` (15) and `_100_factory` (12) in its exterior FX prefab [VERIFIED]; that they sit under lamps is [INFERRED] from the name | |
| 13 | Switch | Twins by state, or an exploder per street | Giant IES twins: `0111` at 8.97 and `1011` at 9.97; `0100` at 6.64 and `1000` at 8.64 [VERIFIED] | |

### 3.2 Step by step

1. **Decide the lamp's job.** In a dark map a street lamp is a waypoint, not general illumination. Pick where the pool must land (a door, a junction, a buy spot) and work back to the lamp position.
2. **Place the pole and head.** A typical height is 250–400 units [INFERRED] (1 unit = 1 inch per Scale_Standards.pdf).
3. **Make the lens.** Separate material on the lens. For always-on: `lit_emissive`, emissive map pure black (0,0,0) outside the lens (Materials.pdf p.18) [VERIFIED], dark Color Map, `scaleRGB 8`. A `lit_emissive` material with no emissive map glows white over its whole surface (the emissive slot defaults to `$white_diffuse`) [VERIFIED]; always set the map. For switchable: `lit_backlit` lens with the light behind it, so the lens goes dark when the light is not in the active state [VERIFIED] (doc intent; look [TEST]).
4. **Place the main spot.** Origin inside the head, a few units above the lens, aimed down (recipe 1 step 2). Set `cut_on` so the cone starts just below the glass.
5. **Shape the cone.** `fov_outer` 80–110, `roundness 1`, `radius` so the cone reaches the ground plus a margin. If the edge looks hard, lower `far_edge` and feather the inner `superellipse` values [COMMUNITY] (VerK0).
6. **Set brightness.** Start at stops 9 on Tower II's exposure and move in whole stops. Colour: sodium orange (Giant warm lamps use `1 0.7311 0.3922` and `1 0.749 0.451`) [VERIFIED] or cool white/cyan for a cyber street.
7. **Add the IES cookie** (`def cuc_ies_029`). Stock cookie lights set `def` alone [VERIFIED] (zm_giant_light.map). Lighting_Parameters.pdf also says to set `ENABLE_COOKIE`, but that string appears nowhere in t7.def.json, the tool binaries or stock prefabs [VERIFIED] (absence), so it looks like dead doc text [INFERRED].
8. **Turn on static shadows** so the pool stops at kerbs, walls and the pole itself.
9. **Add the head glow omni** (radius 15) at the lens, so the underside of the head is not black.
10. **Add a `PROBE_ONLY` fill** at the head, radius about twice the pool, 1–2 stops dimmer. On mirror-like floors (all of Tower II's vertigo world) this is what makes the lamp appear in reflections and baked bounce [INFERRED].
11. **Fit a reflection probe** around the street area; do not leave the default box (72 units per side, a 144-unit cube) ([06](06_reflections_probes.md)).
12. **Set power behaviour.** Always-on: masks `1111`. Dark before power: `1011` (or `1000`). Dim before power: a `0111` twin 1–2 stops dimmer at the same origin. For per-street reveals put the lights in an exploder instead (recipe 17). If the lens is emissive, it will keep glowing whatever the lights do; switch it with a model swap (recipe 17, step 6).
13. **Optional atmosphere.** Lens flare FX at the lens (vet it; Map One zoned two flares and recorded no sighting [COMMUNITY] (project record)). Lit particles in the beam. A volumetric beam (recipe 13), remembering the user's config hides it.
14. **Full build**, then compare same-spot screenshots on a low and a high graphics config.

### 3.3 Placement tips
- Pools should just touch, or leave a dark gap, not overlap heavily; the dark gaps are what make the lamps read [COMMUNITY] (Level Design Book "make it feel dark, don't make it dark").
- Keep lamps a little away from walls. A shadowed light near a wall is fine; a shadowless one lights the other side of the wall too [COMMUNITY].
- Aim along the route. Radiator Blog: "The most common use of a spotlight is an elevated spotlight pointing down, de-emphasizing the ceiling and highlighting the floor" [COMMUNITY].
- Zombies should cross the pool on their way to the player, so they read as silhouettes against the lit ground [COMMUNITY] (Valve Left 4 Dead commentary).

### 3.4 Flickering street lamp variant
Replace the main Radiant spot with an FX spot light carrying a flicker curve (start from `light/fx_light_yellow_flicker2`: spot, shadowed, volumetric, intensity 1024, radius 400, FOV 34, loop 1000/1000, curves that drop to 0) [VERIFIED], keep the `PROBE_ONLY` twin, and give the lens a `lit_emissive_scroll` material with flicker (recipe 10). The two flickers will not be synchronised [INFERRED].

### 3.5 Cost per lamp
One static-shadow spot, one tiny omni, one `PROBE_ONLY` omni. A `PROBE_ONLY` light has no direct runtime light by definition [INFERRED] (from its description). Add a live-shadow spot or an FX light only where it matters: live shadows share the ~12-shadow budget, and a shadowed FX light is always live [VERIFIED].

---

## 4. Wall sconce

**What the player sees.** A lamp fixed to a wall, glowing, washing the wall above and below it with a fan of light.

**Follows.** The Giant's wall-mounted cage lamp (`geo/zm_giant_light_cage_05.map`, recipe 2a) [VERIFIED]. The Giant light prefab also holds 16 spots using the `gobo_spot_rings_001` cookie (`fov_outer 55–105`, `cut_on` 10–34 on 15 of them, radius 80–360, stops 4.5–10.97, mostly warm `1 0.73 …`; 13 with live shadows (`Always`) and 3 with static (`Never`); 15 `volumetric 1`) [VERIFIED]. Which fixtures they belong to was not traced; linking them to wall lamps is a guess [INFERRED].

**Steps**
1. Sconce model; `lit_backlit` shade or emissive glass.
2. Bulb glow omni (radius 15, recipe 2a values).
3. One spot aimed up and/or one aimed down along the wall, `cut_on` past the shade, `fov_outer 60–90`, radius 130–250, stops 7–9. A ring or smoke cookie (`gobo_spot_rings_001`, `gobo_smoke_01`, both stock defs) can break up the wash [VERIFIED] (defs; look [TEST]).
4. Static shadows on, because a sconce sits against a wall and a shadowless light would light the room behind it [COMMUNITY] (bleed reports).
5. Masks and culling as usual. Full build.

**Dark-map notes.** Sconces in a row are good wayfinding along corridors and stair walls. Vary the stops slightly so the row does not look copy-pasted [INFERRED].

---

## 5. Fluorescent tube (area light)

**What the player sees.** A long tube or panel light; an elongated, even pool rather than a round spot; often a slight buzz or flicker.

**Follows.** `mp_sector_light.map` (Treyarch MP): two omni area lights with `bulbLength 28.5`, e.g. `radius 5`, `stops 13`, `angles 270 0 0`, `PRIMARY_NOSHADOWMAP 1`, `_color 1 0.9198 0.8549` [VERIFIED]; the only other `bulbLength` values in that file are 0.01, on six spots [VERIFIED], i.e. effectively no bulb length [INFERRED]. The Giant uses no `bulbLength` [VERIFIED]. The key's definition: "Controls the length of the light bulb of an area light" (t7.def.json) [VERIFIED].

| Part | Choice | Keys | Confidence |
|---|---|---|---|
| Tube | Model or thin brush | emissive tube material, `scaleRGB` 8–16 | [INFERRED] |
| Diffuser | `lit_backlit` cover over the tube | Backlight Mask for any grille bars (Materials.pdf) | [VERIFIED] |
| Light A: area light | `PRIMARY_OMNI` with `bulbLength` = tube length | `angles` sets the tube axis (the MP example uses `270 0 0`); how `radius` and `bulbLength` combine is undocumented | [VERIFIED] (key; behaviour [TEST]) |
| Light B: rectangular spot | `PRIMARY_SPOT`, `roundness 0` (rectangle), elongated `superellipse` | mp_sector has a spot with `superellipse 0.14 0.21 0.9 1`, `fov_outer 95`, `cut_on 21` (at the default `roundness 0.5`) | [VERIFIED] (values; resulting shape [TEST]) |
| Lens flare (optional) | `lensflares/fx_lensflare_fluorescent` → `lf_light_fluorescent_streak.klf` | vet first | [VERIFIED] (mapping; render [TEST]) |

**Steps**
1. Build the tube and diffuser.
2. Choose light A (true area light, the documented key) or light B (a spot shaped into a rectangle, which also casts a static shadow). For long runs, several weak lights beat one strong one [COMMUNITY] (VerK0, Program115).
3. Our exposure is far below MP's, so start around stops 6–8 rather than MP's 13 [INFERRED] (from 0.3).
4. For a buzzing tube, add an FX light with a blackout curve (recipe 10) and a scroll-emissive tube with `flickerMin 0.9`, `flickerMax 1` (the Winslow monitor material's values, recipe 7) [VERIFIED].
5. Full build. `bulbLength` has never been used in this project; treat the first build as a test [TEST].

---

## 6. Neon sign

**What the player sees.** Bright coloured tubes forming letters or shapes on a dark backing plate, a coloured halo, and coloured light spilling onto the wall and ground in front.

**Follows.** Treyarch has no neon sign in the shipped prefabs; the recipe follows the emissive rules in Materials.pdf and the project's own vertigo neon library (`mwiii_vertigo_retro_synth_*`, `lit_emissive_advanced`: plain grid at scaleRGB 15, `_tinted` at 10, `_tinted_edge` at 5) [VERIFIED].

**Steps**
1. **Mesh.** A backing plate plus tubes as separate geometry, or shapes painted into the texture.
2. **Textures.** Emissive map (`colorMap00`): tube shapes bright, **pure black everywhere else** (Materials.pdf p.18) [VERIFIED]. Color Map (`colorMap`): the dark plate and unlit glass. Do not leave it `$white_diffuse` if the plate should stay dark: that lit layer takes on every nearby light's colour (the project's "olive pool" came from exactly this, per the base-light comment in `tools/gen_tower_map.js`) [COMMUNITY] (project record).
3. **Material.** `lit_emissive` (cheapest) or `lit_emissive_plus` (adds AO/gloss; no specular map slot) [VERIFIED]. `colorTint1` = the neon hue; `scaleRGB 8` to start. Double for +1 stop [INFERRED].
4. **Spill light.** The sign does not light the wall by itself (0.1). Add a small omni just in front of the sign in its hue, radius 64–160, or an omni with `bulbLength` along a long straight tube [VERIFIED] (key; look [TEST]). For animated spill use an FX light.
5. **Halo (optional).** A glow sprite FX (`gfx_light_phosphorous_em` style billboard) or rely on bloom. Very bright emissive pixels make white bloom halos [COMMUNITY] (project observation of the sky's halos, docs/104); lower `scaleRGB` to reduce them. There is no per-material bloom field: the word does not appear in deffiles/material.awi [VERIFIED] (absence).
6. **Flicker (optional).** Switch to `lit_emissive_scroll` and set `flickerSpeed 2`, `flickerPower 3`, `flickerMin 0.9`, `flickerMax 1` for a subtle buzz (the Winslow monitor material's values, recipe 7) [VERIFIED], or min 0.1–0.3 with higher harshness for a dying sign [INFERRED]. Plain `lit_emissive` has no flicker fields [VERIFIED].
7. **Switch (optional).** A sign on a world brush glows forever. To switch it at power, build the sign as a `script_model`/`script_brushmodel` and swap to an `_on` model (recipe 17, step 6).
8. Full build.

**Dark-map notes.** Neon reads by contrast: a strip at scaleRGB 5 next to surfaces at 10 read as "the dimmest blue in a room full of brighter blue" (CHANGELOG v17.28) [COMMUNITY] (project record). In a darker scene, smaller values stand out. Keep signs sparse; they are landmarks, not lighting.

---

## 7. TV, monitor, hologram

**What the player sees.** A screen glowing with an image or animation, maybe a faint flicker, and a soft glow on anyone standing in front of it.

**Follows.** No Giant screen; values come from the Winslow logo monitor (`t7_dlc1_decal_signage_winslow_logo_monitor`, a T7 DLC material ported into the shared tools root by Map One's `source_data/acc_t7_props_pilot.gdt`), ported T8 screen decals and the Materials doc's emissive rules.

**Steps**
1. Make the screen a separate material from the body.
2. **Static image:** `lit_emissive`, screen image in `colorMap00`, dark `colorMap`, `scaleRGB` 4–10 (ported T8 screen decals in the tools use 2–5; the Winslow logo monitor, a T7 `lit_emissive_scroll_transparent` material in `acc_t7_props_pilot.gdt`, uses 10) [VERIFIED].
3. **Animation:** `lit_emissive_scroll`. `uvMotionToggle1 1` for a flipbook sprite sheet (Row/Column Count, Image Time), or `0` for scroll/rotate (the vertigo `_pap` material, `lit_emissive_scroll_plus`, scrolls at U 0.2, V 0.1 via GDT keys `gUVScroll02_Angle` / `gUVScroll03_Angle`) [VERIFIED]. Layered holograms: `lit_emissive_scroll_2layer` / `_3layer` [VERIFIED].
4. **CRT feel:** flicker min 0.9, max 1 (the Winslow monitor: speed 2, harshness 3) [VERIFIED].
5. **Video:** community tests report `lit_emissive_mp4` shows only a static image [COMMUNITY] (modme 1565). Use a flipbook.
6. **Face glow (optional):** a weak omni in front of the screen at the screen's average colour, radius 64–128, low stops [INFERRED].
7. Transparent variants only for real holograms you see through; transparency costs overdraw ("the single fastest way to ruin our framerate", PBR deck slide 15) [VERIFIED].
8. Full build.

---

## 8. Spotlight and searchlight with a cookie

**What the player sees.** A hard-edged beam throwing a pattern (bars, rings, leaves, a fixture's IES shape) on a surface; a searchlight additionally sweeps.

### 8a. Static spot with a pattern

**Follows.** The Giant uses a non-default cookie on 62 lights, e.g. `gobo_spot_rings_001` (16), `cookie_flicker02` (7), `cookie_flicker` (6), `cookie_caustics_01` (6), `cuc_ies_029` (4), `gobo_smoke_01` (2) [VERIFIED].

1. `PRIMARY_SPOT`, aimed at the target, `cut_on` past the fixture, `fov_outer` ≤ 120.
2. `def` = a `light` asset (the cookie). Stock defs: `white_light` (default), `gobo_smoke_01` (t6_lights.gdt); `truck_head_lights`, `cookie_flicker`, `cookie_flicker02`, `cookie_caustic_ink`, `cookie_caustics_01`, `cookie_caustics_layered`, `cookie_sun_mp_apartments`, `cuc_black`, `cuc_fov70_pen30`, `cuc_grey_01`, `cuc_ies_006/017/026/029`, `cuc_ies_cust_02`, `cuc_plazma_falloff`, `cuc_smooth_180`, `cuc_white`, `gobo_spot_rings_001` (t7_light_gobo.gdt); two `cookie_mrt512_*` (t7_cookie.gdt) [VERIFIED].
3. Tiling and motion: `def_tile`, `def_offset`, `def_shear`, `def_angle`, `def_center`, `def_scroll`, `def_rotation` [VERIFIED]. The def describes `def_scroll` as "a time in seconds which is how long it will take for the texture to travel across the full width / height" and `def_rotation` as degrees per second; the PDF describes rotation as seconds per turn [VERIFIED]. Copy stock values first and judge the speed in game [TEST].
4. Static shadows on, so the pattern stops at geometry.
5. Volumetric beam with the pattern inside: `volumetric 1` + `volumetricCookies 1` + recipe 13's fog volume.
6. Custom cookies: a new `light` asset whose single field is `cookieImage`; every stock cookie image is 512×512 RGB, and Radiant errors on a wrong-size cookie [VERIFIED]. Radiant asserts a cookie index of 0–255, which suggests a 256-cookie cap [INFERRED].

### 8b. Sweeping searchlight

A Radiant light is compiled into the lighting export; the script API can change intensity, colour, radius (not above the compiled value) and FOV of a `scriptable` + `ServerSide` light, but not move or rotate it (bo3_scriptapifunctions.htm) [VERIFIED]. No stock script calls these functions [VERIFIED], and the community calls them deprecated [COMMUNITY] (modme 2029).

1. **Beam you can see:** a sprite beam FX (`dlc1/castle/fx_light_searchlight_single_castle`, Wraith-extracted source, no light element; or `light/fx_light_cone_metro_sm`, a ray-cone line element) [VERIFIED].
2. **Light where it lands:** an FX spot light (a `dynamicLight2` element) in the same effect or a second one. "You would have to use fx instead of lights" for a searchlight [COMMUNITY] (modme 1928).
3. **Motion:** play the effect with `PlayFXOnTag` on a `tag_origin` host `script_model` and rotate the host (`RotateYaw`); a tag-played effect follows its tag [INFERRED].
4. Keep the FX spot shadowless unless it is the one hero light; FX shadows are always live [VERIFIED].
5. Cookies inside an `.efx` light are unproven in this project's maps (Map One suspected them in a freeze; `white_light` is proven) [COMMUNITY] (project record).
6. There is an engine cap on FX spot lights (`FX_SPOT_LIGHT_LIMIT ... not spawning spot light effect`) whose value is unknown [VERIFIED] (string; value [TEST]).

---

## 9. Fire: burning barrel, torch, candle, big fire

### 9a. Burning barrel (The Giant, exactly)

**What the player sees.** A 55-gallon drum with flames and embers, warm flickering light on everything around it, and the fire showing in reflections.

The Giant builds it from four separate pieces [VERIFIED]:

| Piece | Where | Values |
|---|---|---|
| Barrel + charred boards | `geo/burn_barrel.map` | `p7_barrel_metal_55gal_green_drk` (scale 1.25) and burnt board models; no FX, no lights |
| Flame, embers, smoke | `fx/zm_giant_fx_ambient_interior.map` + `_exterior.map` | `fire/fx_fire_barrel_30x30` (11: 7 interior + 4 exterior), `fire/fx_fire_barrel_embers_30x30` (12: 7 + 5), `smoke/fx_smk_barrel_30x30` (11: 5 + 6) |
| Flickering room light | `zm_giant_light.map`, `fx` entities (11: 10 × `fx_light_barrel_fire_factory_zmb` + 1 × `_strong`) | `light/fx_light_barrel_fire_factory_zmb`: FX omni, shadowed (`PRIMARY_NOSHADOWMAP 0`), intensity graph 100, radius graph 150, loop 600/600; each placement has its own negative `delay` |
| Reflection fill | `zm_giant_light.map` | `PROBE_ONLY 1` omnis within 24 units of the barrel FX lights (13 of them, 11 at mask `1111`): radius 125–300, stops 5.0–7.97, `_color` mostly `1 0.358 0.161` (three `1 0.3818 0.2157`, one `1 0.4653 0.2549`), `falloffdistance` 6–12 |

One barrel also carries a direct Radiant omni switched off in Radiant States 1 and 2 (mask `0011`, radius 119, stops 6.64) and another an all-off (`0000`) omni [VERIFIED]; the live light comes from the FX [INFERRED].

**Steps**
1. Barrel model; flame FX; optional smoke.
2. Vet the flame effects: `fire/fx_fire_barrel_30x30` is clean; `fire/fx_fire_barrel_embers_30x30` carries a `pcloud` material, a project-recorded crash class, so skip it or test it alone [VERIFIED] (grep; risk [COMMUNITY], project record).
3. FX light from `light/fx_light_barrel_fire_factory_zmb`. Decide on shadows: Treyarch's barrel light is shadowed, which means live every frame; the Giant raised `numOmniShadowSlices` to 96 on its worldspawn (default 24) [VERIFIED] (keys; connection [INFERRED]). For Tower II use `PRIMARY_NOSHADOWMAP 1` unless the barrel is a set piece.
4. `PROBE_ONLY` omni twin with the values above.
5. Negative `delay` per placement (Radiant `fx` entity) or a random start (script) so barrels do not flicker in step.
6. Fire sound loop. In this project a custom 3D alias is played from a spawned `script_origin` with `PlaySound`, never `PlaySoundAtPosition` (CLAUDE.md) [COMMUNITY] (project rule).
7. Full build.

### 9b. Torch, candle, small flame
- Candle light: `light/fx_light_candle_zod` (omni, intensity 16, radius 50) [VERIFIED].
- Cheapest fire flicker: `light/fx_light_fire_flicker_noshad_small` (omni, no shadow, intensity 90, radius 150, loop 300/300); it is 5,092 bytes like the placeholder stubs but is a real light (no `gfx_debug_missing_fx`) [VERIFIED].
- Pair with a small flame FX at the wick and a `PROBE_ONLY` twin if reflections matter.

### 9c. Big fire / ceiling fire
`light/fx_light_ceiling_fire_factory_zmb` (FX spot, shadowed, volumetric, intensity 1500, radius 325, FOV 60) with a `PROBE_ONLY` Radiant twin at stops 10.551 (= log2 1500), radius 325, in the Giant [VERIFIED]. Use sparingly: shadowed and volumetric.

**Dark-map notes.** Fire is warm, moving and motivated; one barrel can anchor a whole dark room [COMMUNITY] (Valve lit its streets "from car headlights and oil barrel fires"). Always add the `PROBE_ONLY` twin, or mirror-like floors will reflect a dark spot where the fire is [INFERRED] (FX lights are runtime particles, probes are baked).

---

## 10. Flickering broken light

**What the player sees.** A lamp that stutters, drops out for a moment, buzzes, maybe sparks.

Three ways to flicker the light, cheapest first:

| Option | How | Stock example | Notes |
|---|---|---|---|
| A. Scrolling cookie on a Radiant spot | `def cookie_flicker` or `cookie_flicker02` with `def_scroll` | Giant: six tiny spots with `cookie_flicker`: radius 4–9, stops 9–12.5 (the radius-9 ones 12.29–12.5), `fov_outer 75–78`, `def_scroll` U 0.16–0.2, culling 5/25, mask `1000` (power only); seven Giant tesla spots with `cookie_flicker02`, `fov_outer 120`, radius 60–70, stops 3.5–5, `def_scroll 0.6–0.8`, `volumetric 1`, `volumetricIntensityBoost 4–5`, `volumetricSampleCount 4`, `volumetricCookies 1`, `spec_comp -3` to `-5` [VERIFIED] | Baked, no script, spots only. Community variant: set the cookie tiling to 0.001 in one axis and scroll it [COMMUNITY] (VerK0) |
| B. FX light with a flicker curve | Intensity curve with knots between 0.3 and 1, or brief drops to 0 | `light/fx_light_yellow_flicker2` (spot, shadowed, volumetric, 1024, radius 400); Wraith sources `light/fx_light_flickering_hat_light_sodium` and `light/fx_light_sgen_dayroom_rectangle_flicker` (Map One used both) | Treyarch's official route (FX_Lights.pdf). Interval = lifetime. Add a `PROBE_ONLY` twin |
| C. Exploder toggled from client script | `exploder::exploder` / `exploder::stop_exploder` in a CSC loop | — | Per-frame cost untested [TEST] |

**Steps**
1. Pick A for a static fixture, B for anything that must blink out fully or move.
2. Surface flicker: give the bulb or tube a `lit_emissive_scroll` material: `flickerSpeed` (rate), `flickerPower` ("Harshness of flicker transitions"), `flickerMin`/`flickerMax` (0.1–1 dramatic, 0.9–1 subtle), `flickerSeedU/V` to desync copies [VERIFIED]. The APE defaults are `flickerMin 0`, `flickerMax 1` (deffiles/material.awi) [VERIFIED], so a scroll material left at defaults may flicker unasked [TEST]. The vertigo pack's three scroll materials show all three choices: `light_pink_alpha` sets `flickerMin = flickerMax = 1` (steady), `light_pink_alpha_skydome` a slow deep flicker (speed 0.1, min 0.1), and `_pap` keeps the defaults [VERIFIED] (values).
3. Material flicker and light flicker are not linked, so tune them to a similar rhythm by eye [INFERRED].
4. Sparks: The Giant places `electric/fx_elec_gp_wire_sparking_xsml_thick_anim` (and `_v2`) at `fxstate 0011`, i.e. only in Radiant States 3 and 4 [VERIFIED].
5. Sound: an electrical buzz loop from a `script_origin`.
6. **Stutter to life at power-on:** stock perk machines play their light FX in bursts of growing length (0.1 s, then +0.2 s each) for about 3 s, on the client, only when `level.enable_magic` is set (`_zm_perks.csc` `perk_start_up`, lines ~195-262) [VERIFIED]. The same rhythm works for any lamp: toggle its FX or exploder in growing bursts before leaving it on [INFERRED].

---

## 11. Emergency, alarm and status lights

### 11a. Status lamp: red, flashing, green (The Giant)

**What the player sees.** A small coloured lamp that says what state something is in: red = locked or unpowered, flashing = in progress, green = ready.

**Follows exactly.** The Giant's teleporter map lights [VERIFIED]:
- Lights: tiny omnis, radius 20; red `_color 1 0 0` at stops 6.64, green `0 1 0` at stops 5.64; grouped into exploders `map_lgt_<pad>_red` / `_green` (the Giant's 48 exploder lights have median radius 20).
- Flash: three `fx` entities `light/fx_light_flashing_red_factory_zmb` in exploder `map_lgt_pap_flash`. That effect is an FX omni, no shadow, intensity 100, radius 20, with interval 1000 ms and lifetime 500 ms, so the light is dark for part of every second [VERIFIED] (file; intended blink [INFERRED]).
- Script (client, `zm_giant_fx.csc` ~225-292): wait for the server's `pl1` notify, play `map_lgt_<pad>_red`; when the pad links, `stop_exploder` red and play `_green`; the PaP receiver waits `wait( 1.5 ); // dramatic pause` before going green [VERIFIED].
- Stock traps swap `<name>_red` / `_green` exploders the same way (`_zm_traps.gsc:445-477`) [VERIFIED].

**Steps**
1. Place a red and a green light at the fixture (small omni, radius ~20). Give the lamp model an emissive lens.
2. Radiant: Exploder Manager → select the red light(s) → RMB "Create New Exploder from selection" → name `lgt_<thing>_red`; the same for green (FX_Lights.pdf) [VERIFIED]. Radiant refuses non-primary lights ("only primary lights can be added to exploders") [VERIFIED]; FX entities can also be exploder members [VERIFIED].
3. Copy the other keys from a stock exploder light rather than guessing: 45 of the Giant's 48 exploder lights carry `exploderDisabled 1`, and their masks are `1011` (24), `1000` (15), `1111` (7) and `1101` (2); 38 use live shadows (`Always`) and 10 static (`Never`) [VERIFIED]. That an exploder light must also be in the active lighting state is [INFERRED].
4. Script it from a **world clientfield callback** in CSC (stock trap pattern, `_zm_trap_electric.csc:20-37`), so a player who joins late gets the current colour; whether a server-activated Radiant exploder replays for a late joiner is unverified [TEST].
5. The lamp lens should change too: model swap to a red or green `_on` model, or three emissive models shown and hidden [INFERRED].

### 11b. Rotating or strobing alarm
- `light/fx_sgen_emergency_whiteflash_small`: 2 FX spots (intensity 2000, radius 550) + 2 FX omnis, all shadowless and volumetric, short lifetimes (100–200 ms) in a 1000 ms loop, i.e. a flash once a second [VERIFIED] (file; look [TEST]). Heavy: four dynamic lights per instance.
- Wraith-extracted alternatives: `light/fx_sgen_emergency_blueflash(_small/_long)`, `dlc3/stalingrad/fx_light_emergency_flash_loop_stalingrad`, `dlc2/island/fx_lgt_bunker_blink_red/_green` [VERIFIED].
- Avoid `light/fx_lotus_emergency_flash` until cookies inside effects are proven: it uses cookie `cuc_ies_017` [VERIFIED] (risk [COMMUNITY], project record).
- `light/fx_glow_blink_red_5` has **no light element**; it is a glow sprite that lights nothing (Map One used it) [VERIFIED].
- A rotating beacon: an FX spot on a `tag_origin` host rotated with `RotateYaw` (8b) [INFERRED].

### 11c. A whole-map alarm mood
- A spare lighting state can be an alarm look: the community map Alien Isolation Zombies has 22 lights only in Radiant State 4 (its red alert), one of its three sun volumes uses distinct spawn / lights-out / power-on SSIs, and its scripts drive `set_lighting_state` 0–3 for power-out, power-on and alarms [COMMUNITY] (read from its public .map and scripts, https://github.com/MattFiler/zm_alien_isolation). Whether each extra state with its own SSI adds bake time or `.led` data is unmeasured: the LED already lists an SSI for all four states even when only `ssi1` is set [TEST].
- A cheaper mood swap without relighting: fog banks (`SetLitFogBank`, `SetWorldFogActiveBank`) driven from a world clientfield, as stock parasite rounds do (`_zm_ai_wasp.csc:29-61`, field `toggle_on_parasite_fog`) [VERIFIED]; The Giant has the same pair in `ramp_fog_in_out()` (`zm_giant_fx.csc:165-180`), but no stock script calls it. Or a vision set blend. Details in [02 §11](02_power_and_states.md#11-fog-exposure-lut-and-grade-banks-as-mood-switches).
- Sound: alarm loop from a `script_origin`; stop it by deleting the origin.

**Dark-map notes.** Status colour is a cheap, readable light language: The Giant uses red for an unlinked pad and green for a linked one [VERIFIED] (zm_giant_fx.csc), and design writing recommends lighting as a signal for the player [COMMUNITY] (Level Design Book). Tower II already puts a red omni in every Vault window niche so the horde's windows read as a hazard (`tools/gen_tower_map.js`, Undercity block) [VERIFIED].

---

## 12. Lit window at night

### 12a. Seen from outside (facades, vista buildings)

**What the player sees.** Warm rectangles in dark buildings: "someone is home", or a building on fire.

**Follows.** The Giant's `geo/zm_giant_visfire_window_lit.map` is a mesh painted `t7_glass_window_warehouse_backlit`, which in `texture_assets/t7_glass.gdt` is the ordinary `t7_glass_window_warehouse` material with only `materialType` changed to `lit_backlit`; the prefab holds no light [VERIFIED]. The exterior FX prefab places `fire/fx_fire_vista_window_200x100_zmb` (6), `fire/fx_fire_window_embers_50x100` / `_100x100` and `smoke/fx_smk_window_*_black` for burning windows [VERIFIED].

Options, cheapest first:
1. **Emissive interior card.** An opaque quad inset behind the frame, `lit_emissive`, a painted interior or warm gradient in `colorMap00`, black `colorMap`, `scaleRGB 4–8` [INFERRED]. Always on.
2. **Backlit pane + light behind** (Treyarch's way). `lit_backlit` on the glass, a Radiant light inside the room. When the light is not in the active state the pane stops glowing, so the window switches with power for free [VERIFIED] (doc intent; look [TEST]).
3. **Fire windows.** A window-sized fire FX plus smoke, like the Giant's vista.

Avoid `lit_emissive_transparent` unless there is real interior geometry behind the glass (Materials.pdf warns about transparent emissives) [VERIFIED].

### 12b. Seen from inside (light coming through the window)

1. A spot outside the window aimed in, static shadows on so the frame and bars cast their shape on the floor. A blinds cookie shapes it further [INFERRED].
2. Moonlight: The Giant's moonlight is four distant spots (about 18,000–40,000 units away, `ENABLE_FALLOFF 0`, radius 12,000–22,000, `target moon`, `fov_outer 55–90`, stops -1 to 6.73, cool `_color 0.7529 0.8471 0.8471` on two and a darker blue on the other two), all `PRIMARY_NOSHADOWMAP 1` [VERIFIED], so they cast no window shapes [INFERRED]. A window shape needs its own shadowed spot [INFERRED].
3. Optional visible shaft: recipe 13.

### 12c. Spill out onto the street
A spot inside aimed out through the window, or an omni just inside the glass [INFERRED].

---

## 13. God-ray shaft

**What the player sees.** A visible beam of light in hazy air, with dust drifting through it.

**Follows.** The Giant's tesla-coil beams: seven `cookie_flicker02` spots with `volumetric 1`, `volumetricIntensityBoost 4–5`, `volumetricSampleCount 4` and `volumetricCookies 1`, inside two small `vol_litfog_teslacoils` volumes with `ENABLE_LIGHTS` [VERIFIED].

### 13a. Real volumetric shaft
1. A spot (Radiant or FX) with `volumetric 1` ("Enables rendering of light as volumetric", t7.def.json) [VERIFIED].
2. `volumetricSampleCount` ("Number of ray march samples"): 1–24, default 8. The Giant uses 1 on 513 of 543 lights, 4 on 8 (its seven tesla beams and one other) and leaves the default 8 on 22 [VERIFIED].
3. `volumetricIntensityBoost` (stops, −14..14) if the beam is faint (tesla beams 3–5) [VERIFIED]; `volumetricCookies 1` if a cookie should show in the beam.
4. A `volume_litfog` around the area with `ENABLE_LIGHTS` (spawnflag 64, default on) and a lit-fog `fsi`; the Giant's lit-fog volumes use `zm_factory_volumetric` [VERIFIED] (t7.def.json; zm_giant_light.map). Keep it local: Treyarch's MP workflow sets "probe look up" and "enable lights" false on the global lit fog because "We can't afford these features as a global setting. If these are needed make another volume for the isolated area" (Multiplayer_Lighting_Workflow.pdf) [VERIFIED]. The Giant has three `volume_litfog` entities: a map-wide one (about 7,500 × 9,100 × 3,000 units, Radiant States 1–2 only, with `ENABLE_LIGHTS` on and probe lookup off) and two small tesla-coil volumes (`vol_litfog_teslacoils_001/002`, about 130 units across, `ENABLE_LIGHTS` on, sun off) [VERIFIED] (parsed spawnflags). So the MP advice is a cost rule, not a hard limit [INFERRED].
5. **Players can switch it off.** `VolumetricLightingEnabled` in `players/config.ini` ("Enable volumetric sun and light shafts"); the user's is 0 [VERIFIED]. Community sources say lit fog (`volume_litfog`) goes with it; no primary source says so [COMMUNITY].

Tower II today: worldspawn `fsi zm_factory_volumetric`, but no `volume_litfog` and no light sets `volumetric`, so no shafts can appear [VERIFIED] (keys; result [INFERRED]).

### 13b. Fake shaft (works for everyone)
1. A sprite cone FX: `light/fx_light_cone_metro_sm` (a `line` element with `gfx_light_ray_cone_em_i2048` and a hot core sprite; no light element) [VERIFIED]. Others: `dlc5/tomb/fx_light_robot_foot_shafts`, `dlc5/zmhd/fx_mp_ray_spotlight_xlg` [VERIFIED].
2. A real light (spot or omni) where the beam lands, so the fake beam has a lit target.
3. Dust motes: `dirt/fx_dust_motes_200x200`, `dirt/fx_dust_motes_300x300_sm`, `dirt/fx_dust_motes_sphere_50` (Wraith-extracted, no placeholder, no pcloud) [VERIFIED]. Avoid `dirt/fx_dust_motes_150x150`, `_250x250`, `_200x200_pcloud` and the Giant's own `dlc0/factory/fx_dust_motes_tinhat_factory`: they reference pcloud materials [VERIFIED] (grep; crash risk [COMMUNITY], project record).
4. **Never** zone the `env/light/*` "god ray" effects: all five are 5,092-byte placeholders (`gfx_debug_missing_fx`) [VERIFIED]. Tower II currently zones `env/light/fx_light_god_rays_dust_motes` for its lounge motes (`zone_source/zm_tod2_cybercity.zone`) [VERIFIED]; by the project's stub rule that packs a blank effect [COMMUNITY] (project record).

**Dark-map notes.** Shafts are mood, never navigation: players can turn real volumetrics off, and the user's own config has them off [VERIFIED]; how many players run with them off is unknown [INFERRED].

---

## 14. Perk-machine light pool

**What the player sees.** A machine glowing in its colour, and a coloured pool on the floor around it that says "buy here".

### 14.1 How stock does it (and why stock machines look dark in custom maps)
- Stock machines do not change mesh at power: every stock perk `.gsh` sets the same model for DISABLED and ACTIVE [VERIFIED].
- 3 s after power, the server plays the perk's `level._effect["<perk>_light"]` with `playfxontag` on `tag_origin` (`_zm_perks.gsc` `perk_fx`, ~280-305) [VERIFIED]. Those `zombie/fx_perk_*_zmb` effects are billboard sprites only, no light element [VERIFIED].
- Client side, `zm_usermap.csc` `include_perks()` assigns the `*_factory_zmb` variants, which contain 6–15 `dynamicLight2` elements each; each perk's client init sets the non-factory effect back only when `level.enable_magic` is true, and these client entries feed the ~3 s power-on flicker. The server's `zm_usermap.gsc` `perk_init()` (factory swap) is never called by stock script [VERIFIED].
- The stock perk and PaP vending prefabs (`map_source/_prefabs/zm/zm_core/vending_*`) carry 2–11 small lights each (the GobbleGum machine prefab has none), all at mask `0000`. Juggernog's six are spots of radius 25–95, stops 2–4.81, pale red, several shadowed, i.e. lights on the machine itself rather than a floor pool [VERIFIED]. Only Quick Revive's lights are ever switched on by stock script, through exploder `quick_revive_lgts` (`_zm_perk_quick_revive.gsc:185`): at load in solo, at `revive_on` in co-op [VERIFIED].

### 14.2 How Tower II does it today
- Server: after `power_on`, a 4-bit scriptmover clientfield `todPerkGlow` (a colour index) on each machine; a rekick pulse when a player first comes within 700 units (`scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc`) [VERIFIED].
- Client: `PlayFXOnTag` of `acc/light/fx_perk_glow_<colour>` on `tag_origin` (`_tod_perk_lights.csc`) [VERIFIED].
- Each glow effect has one light element `light_small` (omni, no shadow, intensity graph 512, radius graph 60, 40 units up) plus three sprites. Its loop runs a 200 ms interval with a 1000 ms lifetime, so about five light particles overlap, against the doc's interval = lifetime rule [VERIFIED] (values; effect on look [INFERRED]).
- The BO7 machines swap to lit `_on` models through `level.machine_assets` [VERIFIED].
- The machines move (the 9-pad scatter), so baked lights cannot follow them [VERIFIED].

### 14.3 Recipe: a readable floor pool for a machine
1. **Glow on the machine:** the `_on` model with hotter emissive twins (`skinOverride`), as today.
2. **Floor pool:** the effective FX radius is about 60 units [INFERRED] (from the graph). For a pool that reads on the floor, add a second FX light element (or a second effect) aimed down: a spot at intensity 256–512, radius 120–200, `PRIMARY_NOSHADOWMAP 1`, interval = lifetime [INFERRED]. Keep it in the machine's colour.
3. **Loop timing A/B:** try `spawnLooping` = `lifeSpanMsec` on a copy and let the user compare it with the approved current look [TEST].
4. **Reflections:** the pads are fixed even though the machines move. A neutral or lounge-coloured `PROBE_ONLY` fill per pad would give the floor something to reflect without being wrong after a reshuffle [INFERRED].
5. **Keep the clientfield route.** It replays for late joiners (`!CF_CALLBACK_ZERO_ON_NEW_ENT`) [VERIFIED].
6. A stock-asset alternative, untested: set the server `level._effect["<perk>_light"]` handles to the `*_factory_zmb` variants after the perk precache (what `perk_init()` would do), so stock `perk_fx` plays real lights [INFERRED].

---

## 15. Teleporter pad light

**What the player sees.** A pad that is dim or unlit before power, lit and humming when ready, surging while it charges, flashing on teleport, and a status colour telling you whether it is linked.

**Follows exactly.** `map_source/_prefabs/zm/zm_giant/light/zm_giant_teleporter.map` (34 lights, 2 multiface reflection probes; its worldspawn aliases Radiant State 2 `power_off`) [VERIFIED]:

| Light group | Values |
|---|---|
| Overhead pad spots | narrow `PRIMARY_SPOT`, `fov_outer 17–20`, radius 175–225, warm `_color 1 0.9576 0.7882`, `volumetric 1`. **Twins: mask `0111` at stops 8.97, mask `1011` at 10.97 for the radius-200/225 spots (two stops brighter after power, static shadows `Never`); the radius-175 spots go 8.97 → 9.97 and are shadowless (`PRIMARY_NOSHADOWMAP 1`)** |
| Blue fill | omni, `_color 0.4784 0.7608 1`, radius 125, `0111` at 8.97 / `1011` at 9.97; one blue spot `fov_outer 90`, radius 200, 10.97 / 11.55 |
| Reflection fills | `PROBE_ONLY 1` omnis, radius 150: blue at stops 0 (both masks), white at 3.32 (mask `1000`) |
| Small detail lights | tiny omnis radius 10, stops 4.64 (`1011`); tiny spots radius 7, stops 4.64 (`1000`) |

Status: exploders `lgt_teleporter_<pad>_linked`, fired server side (`zm_giant_teleporter.gsc:744`) [VERIFIED]. Teleport flash: client visionsets (`cheat_bw_invert_contrast`, `flare`, `zombie_turned`) then restore (`zm_giant_teleporter.csc:107-143`) [VERIFIED]. Area grade: 15 `pbg_box` entities in the light prefab (named for the teleporter rooms, garage, furnace and so on) carry `zm_factory_tele_a/b/c` bloom and colour grades, all flagged `LIGHTSTATE_1` only [VERIFIED], i.e. active only in the powered state [INFERRED]. The separate `light/zm_giant_post.map` holds a map-wide pair: a `pbg_box` named `power_off` flagged `LIGHTSTATE_2` only and one named `power_on` flagged `LIGHTSTATE_1` only [VERIFIED], so Treyarch's own post grade switches with the power state [INFERRED] (from the names and the state mapping; this pair also supports "Radiant State 2 = before power").

**Tower II today.** The pad is FX-lit: `tod/teleporter/fx_tod_tp_ready` (light element intensity 150, radius 100, 26 units up, loop 1600/1600), `fx_tod_tp_charge_field` (900, radius 130, interval 5000 / life 700) and `fx_tod_tp_release_field` (1150, radius 155, interval 5000 / life 650), plus the emissive `tod_teleporter` model [VERIFIED]. The charge and release loops leave dark gaps if they loop; they behave correctly only as one-shots [INFERRED] (from the FX_Lights loop rule).

**Recipe**
1. **Baked base light:** narrow overhead spots on the pad, a pre-power twin (`0111`) and a powered twin (`1011`, +1–2 stops), like the Giant.
2. **Ready hum:** a looping FX light, interval = lifetime, shadowless.
3. **Charge and release:** FX lights with authored curves, played as one-shots on a `tag_origin` host (wait two server frames after spawning the host before playing, project practice from docs/143) [COMMUNITY] (project record).
4. **Status:** red/green exploders or FX driven by a clientfield (recipe 11a).
5. **Reflections:** `PROBE_ONLY` fills in the pad colour; a fitted probe on the pad.
6. **Flash:** a short vision set blend on the teleporting client.
7. If you add a `pbg_box` grade that should apply before power, tick `LIGHTSTATE_2`: `pbg_box` defaults to Radiant State 1 only, and a usermap boots in Radiant State 2 [VERIFIED] (def defaults; effect [INFERRED]).

---

## 16. Water caustics

**What the player sees.** Wavy, moving patterns of light on walls or ceilings near water (or near a molten, glowing surface).

**Stock example.** The Giant has six lights with `def cookie_caustics_01`, clustered in one spot next to furnace fire lights [VERIFIED]:
- 4 spots: `fov_outer 70`, `cut_on 101`, radius 325, stops 8.97, `_color 1 0.5098 0.2941` (warm orange), `PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`, `shadowmapScale 0.5`, `far_edge 0.85`, culling 200/300, mask `1111`; `def_scroll` values `0.05 0.1`, `-0.1 0.1`, `-0.1 0`, `0.05 0`; `def_rotation` `-0.1` or `0.2` (each copy different).
- 2 omnis with the same cookie: radius 83, stops 8.97, `PRIMARY_NOSHADOWMAP 1`, `far_edge 0.25`, `def_scroll 0.1 0.1`.
- What surface these imitate is not documented; their colour and neighbours suggest a hot or molten glow rather than water [INFERRED].

**Recipe**
1. A spot above or beside the water, aimed at the wall, floor or ceiling that should shimmer.
2. `def cookie_caustics_01` (or `cookie_caustics_layered`, `cookie_caustic_ink`; t7_light_gobo.gdt) [VERIFIED].
3. Animate with `def_scroll` and `def_rotation`, different per copy so overlaps do not move in lockstep (Giant practice) [VERIFIED]. Units are disputed (see 8a) [TEST].
4. Colour: cool cyan-white for water, orange for molten or fire [INFERRED].
5. Start at the Giant's stops 8.97 and adjust.
6. Optional `volumetricCookies 1` for patterned shafts in haze.
7. Full build. Water surfaces themselves: [07](07_water.md).

---

## 17. The power-on reveal: a floor going from dark to lit

This is the recipe for the user's main worry: "when you turn on power the whole tower lights up." The goal is a *staged* reveal: the switch, a beat, then lights coming on in a deliberate order, with glowing panels igniting and a sound and FX beat, instead of everything snapping on at once.

### 17.1 What the player should experience
1. Before power: the area is dim, lit by a few emergency or navigation lamps (never pitch black).
2. The switch: a clunk, a spark, a sound sting.
3. A pause (Treyarch literally writes `// dramatic pause`).
4. Light arrives: fixtures stutter to life, pools spread, panels and signs ignite, status lamps turn green.
5. Later floors or zones light up as the party reaches or powers them, not all at once.

### 17.2 The tools, and what each can and cannot do

| Tool | Scope | Can | Cannot | Theory |
|---|---|---|---|---|
| Lighting state (`set_lighting_state`) | Whole map, per player | Swap every state-gated light, the SSI (sun, sky, exposure), post and fog volumes, state-gated FX entities in one call; baked bounce per state [INFERRED] (Radiant keeps probe data per state) | More than 4 looks; per-floor switching; a fade for lights (none found; `volume_sun transitionTime`, "Time to transition between sun states", may blend the sun/sky only [TEST]) | [02](02_power_and_states.md) |
| Radiant exploder | One named group of lights and/or FX | Per-floor or per-device on/off by name | Smooth intensity (unless its fade fields work, untested); cap ~120 exploders [INFERRED] (from Radiant strings) | [02](02_power_and_states.md), [04](04_fx_lights.md) |
| FX lights from a clientfield | Anything | Per floor, per door, flicker, pulses, late-join safe | Baked bounce, static shadows | [04](04_fx_lights.md) |
| Emissive switch | One entity | Make panels, strips and signs look on or off (model swap, or a script-driven material) | Light anything; switch world brush faces | [03](03_glow_and_perks.md) |
| Post and atmosphere | Per client | Mask the pop with a vision blend; fog bank swaps | Local light pools | [05](05_sun_sky_exposure_fog.md) |

"The whole tower lights up" is exactly what a lighting state does: it is global by construction. A staged reveal therefore uses **one** global state flip for the base mood, and exploders or FX lights for everything that should arrive later.

### 17.3 How The Giant stages its power-on (the reference sequence)

From `share/raw/scripts/zm/zm_giant.gsc` `power_electric_switch()` (lines 524-590) and `bridge_init()` [VERIFIED]:
1. `trig waittill( "trigger", user );` — the player pulls the switch.
2. `level thread scene::play( "power_switch", "targetname" );` — the lever animation.
3. `level flag::set( "power_on" );`
4. Each machine's power notify, one per network frame: `sleight_on`, `revive_on`, `doubletap_on`, `juggernog_on`, `Pack_A_Punch_on`, … with `util::wait_network_frame()` between them. Each stock machine then calls `SetModel` with its "on" model (the same mesh as its "off" model for stock perks, see 14.1), plays `zmb_perks_power_on`, vibrates, and 3 s later plays its light FX; the client adds a ~3 s stutter-on flicker (`_zm_perks.gsc:113-161`, `_zm_perks.csc` ~195-262) [VERIFIED].
5. `level util::set_lighting_state( 0 );` — Radiant State 1, the powered look.
6. `util::clientNotify( "ZPO" );` — "Zombie Power On!" for client scripts.
7. `wait 1;` then `playfx( level._effect["switch_sparks"], s_switch.origin, forward );` — a spark burst at the switch (a server one-shot `PlayFX` in stock code).
8. 19 s later: `zm_audio::sndMusicSystem_PlayState, "power_on"` — the music sting.
9. Separately `bridge_init()` waits for `power_on`, sends `level util::clientnotify( "pl1" )`, which the client uses to start the red map lights (later green, after a 1.5 s pause for PaP) [VERIFIED].

Lessons: Treyarch spaced the beats (network frames, 1 s, 1.5 s, 19 s), used exploders for small accent lamps only, and did not make the Giant black before power (341 of 543 lights are on in the pre-power Radiant State 2, 219 of them direct lights rather than `PROBE_ONLY`; power brightens paired fixtures by a median of about one stop and adds extra fixtures) [VERIFIED].

### 17.4 Step by step

1. **Settle the runtime state first.** Before designing, confirm in a dev playtest which lighting state each player is in (`player GetLightingState()` logged at spawn and after power) and that the `volume_sun` has a real SSI for every state you use. The log shows the *script* state number only; it cannot by itself prove which Radiant State that selects [INFERRED]. Recipes: [02](02_power_and_states.md).
2. **Pick a convention and write it down.** Recommended: the Giant convention (boot in Radiant State 2 = pre-power; one call `level util::set_lighting_state( 0 );` at power). Label the worldspawn `state_alias_2 "power_off"` so Radiant's state menu documents itself [VERIFIED].
3. **Fill the sun volume for both states.** `ssi1` and `ssi2` both set to a real SSI (the same SSI is fine; The Giant uses `zm_factory` in both) [VERIFIED]. Optional `transitionTime` on the `volume_sun` ("Time to transition between sun states", default 0) [VERIFIED] (key; runtime effect [TEST]).
4. **Sort every light into a class** (masks under the Giant convention):
   - `ALWAYS` `1111`: a dim navigation layer (spawn, stairs, doors, hazards) so nothing is ever pitch black.
   - `PREPOWER` `0111`: emergency or dim twins.
   - `POWERED` `1011`: the powered twin of each pre-power light (+1 to +2 stops) and powered-only fixtures.
   - `STAGED`: lights that must arrive later than the global flip go in exploders named per area (`lgt_floor10_on`, `lgt_lounge_n_on`), usually mask `1011` or `1000` plus `exploderDisabled 1`, copied from a stock exploder light [VERIFIED].
5. **State-gate the other volumes.** Tick `LIGHTSTATE_2` on any `pbg_box`, `vlut_box`, `vbloom_box`, `vcolor_*` or `volume_performance` meant to apply before power (and `LIGHTSTATE_1` too if it should stay after power), because they default to Radiant State 1 only [VERIFIED] (def defaults; effect [INFERRED]). Treyarch did this for The Giant's whole-map grade: `pbg_box` `power_off` in Radiant State 2 only, `power_on` in Radiant State 1 only (`light/zm_giant_post.map`) [VERIFIED]. Fog volumes default to all four states [VERIFIED].
6. **Make the glow switch.** For every panel, strip or sign that should ignite, build it as an entity and choose:
   - **Model swap** (proven in this project): an `_on` xmodel that is the same mesh with a `skinOverride` to hotter material twins (the Rampage Inducer: scaleRGB 1.2 → 16, 1.5 → 22, glass 0.4 → 6, values in `source_data/tod_bo6_inducer.gdt` [VERIFIED]; the user approved the look in game per CLAUDE.md [COMMUNITY] (project record)). Server `ent SetModel( "tod_x_on" );` (precache the model), or client `SetModel` on a client-side model after a notify, as the Giant's `light_model_swap` does (`zm_giant_fx.csc:69-71, 184-197`; note the shipped Giant source has no entity with those targetnames) [VERIFIED].
   - **Script-driven material** (untested here): `lit_emissive_script` with tint states driven by client `MapShaderConstant` / `SetShaderConstant`, as stock Der Wunderfizz drives its machine glow states (`_zm_perk_random.csc:104` onward) [VERIFIED] (stock usage; exact constant mapping [INFERRED]).
   - **State-gated models** (untested anywhere): `misc_model`, `script_model` and `script_brushmodel` carry their own `lightingstate1..4` keys (default on) (bin/t7.def.json) [VERIFIED], so an unlit and a lit model at the same spot with opposite masks might switch with the global state. The Giant only ever uses these keys all-on, and whether an entity outside the active state is hidden in game or only left out of the bake is undocumented [TEST].
   - World brush faces cannot switch: they carry no entity keys [INFERRED]. The vertigo pack's unlit twin `mwiii_vertigo_retro_synth_off` (scaleRGB 0) exists for surfaces that should never glow [VERIFIED].
7. **Stage FX lights and FX entities.** Radiant `fx` entities can be state-gated with `fxstate1..4` (the Giant swaps `light/fx_light_pap_key` at `0100` for `light/fx_light_pap_key_on` at `1000`) [VERIFIED]. Script-played FX lights for per-floor reveals ride a world clientfield (step 9).
8. **Write the server sequence.** A sketch [INFERRED] (assembled from the stock calls cited here, never compiled or run; add the project's dev logs):

```c
// server GSC — after zm_usermap::main(); Giant convention
#using scripts\shared\flag_shared;
#using scripts\shared\util_shared;
#using scripts\shared\exploder_shared;
#using scripts\shared\clientfield_shared;

function power_reveal()
{
    level flag::wait_till( "power_on" );
    // beat 1: switch FX + sound (custom 3D alias from a script_origin, project rule)
    wait 0.5;                                   // the "dramatic pause"
    level util::set_lighting_state( 0 );        // Radiant State 1 = powered look
    util::clientNotify( "ZPO" );                // as The Giant does: stock client scripts turn this into "power_on"
    wait 1.0;
    level clientfield::set( "tod_lit_floors", 1 );  // floor 1 staged group (client side plays it)
}
```

   `util::set_lighting_state` stores `level.lighting_state` and applies it to every active player; `_globallogic_spawn.gsc:501` re-applies it on every spawn, so late joiners and respawns get it [VERIFIED]. `util::clientNotify` only sends when `level.clientscripts` is set (`util_shared.gsc:1390-1402`) [VERIFIED]; The Giant relies on it for `ZPO`, but for state a late joiner must see, prefer the world clientfield of step 9. Stock global power sets clientfield `zombie_power_on` to 0 (`_zm_power.gsc:731`), and the client handler only notifies `ZPO` on a non-zero value (`_zm.csc:390-396`); `_zm.csc` `ZPO_listener` is what turns `ZPO` into the client-side `power_on` notify that stock client scripts such as the perk flicker wait for [VERIFIED] (code). So with global power, client scripts get no power notify unless the map sends `ZPO` itself, as The Giant does [INFERRED] (not tested in a usermap). Among stock scripts only `zm_giant.gsc:573` sends it, and no Tower II script does [VERIFIED] (grep).

9. **Write the client side** for staged groups. A world clientfield (an int or bitmask of lit floors) whose CSC callback plays the floor's exploder or FX lights; the callback also runs on a late joiner's initial snapshot [VERIFIED] (stock pattern `_zm_trap_electric.csc:20-37`; replay [INFERRED]). Sketch [INFERRED] (never compiled):

```c
// client CSC — register the same field in both VMs (see _tod_perk_lights for this project's pattern)
function lit_floors_changed( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
    for ( i = 1; i <= newVal; i++ )
    {
        if ( i <= oldVal && !bInitialSnap )
            continue;
        exploder::exploder( "lgt_floor" + i + "_on", localClientNum );   // -> PlayRadiantExploder
    }
}
```

   Stopping an exploder from the server reaches the client only when `level.clientScripts` is set (`exploder_shared.gsc:762-767`), so turn groups off from client script when it must be reliable [VERIFIED].
10. **Stutter, don't snap.** For hero fixtures, toggle the FX or exploder in growing bursts (the stock perk flicker rhythm: 0.1 s, then +0.2 s each, about 3 s) before leaving it on [INFERRED].
11. **Mask the global pop.** No fade exists for switching lights between states [INFERRED] (none found in the API or keys). Map One sets a vision grade that matches the current darkness with `VisionSetNaked( <grade>, 0 )`, flips the state, then ramps back to default so the lights swell up over about 10 s instead of snapping; the code comment records the user's instruction there to "stay the same darkness, don't go darker" (`abandoned_cyber_city_zombies/scripts/zm/zm_abandoned_cyber_city.gsc` `CheckForPower`; its CHANGELOG "Power-on light WARM-UP") [COMMUNITY] (project record). Map One reads its grade names from dvars; this project forbids dev dvars, so hard-code them.
12. **Sound and FX beat.** Switch clunk, spark burst at the switch, per-machine power sound (`zmb_perks_power_on` in stock), a music sting after the lights settle (The Giant waits 19 s) [VERIFIED]. A seconds-long frame hitch at power-on reported by the community comes from registering perk hint strings, not from lighting [COMMUNITY] (modme 2118); keep hint strings within this project's budget rules (CLAUDE.md).
13. **Logs.** `[TOD_LIGHTS]` lines at each step: state before and after (`GetLightingState()`), each clientfield value with old/new and `bInitialSnap`, each exploder name played (dev-gated PrintLn pattern in CLAUDE.md).
14. **Full build. The user tests** with same-spot screenshots before and after power, in solo and in co-op with a late joiner.

### 17.5 Pitfalls specific to the reveal
- **Tower II today:** all 344 generator lights are mask `0111`. Adding `set_lighting_state( 0 )` at power now would move the level to Radiant State 1, where none of them is on, so the tower would get darker at power, and the level would also switch to Radiant State 1's SSI (`tod_ssi_cybercity`, the only one Tower II authors) [INFERRED]; what that looks like in game is untested [TEST]. Re-mask first (step 4).
- **Emissive world keeps glowing.** Every visible world brush face in Tower II (66,402 faces) uses an emissive-class material, and about half of them glow only on thin grid lines [VERIFIED] (map and GDT parse). That glow does not follow power or lighting states [INFERRED] (no `*_script` techset is used; see [03](03_glow_and_perks.md)). A reveal can only switch what is on entities.
- **Probes bake per state.** Radiant keeps probe data per lighting state [VERIFIED] (Radiant field names; SunSky_Light_SetUp.pdf); whether exploder lights feed the baked bounce while off is unknown [TEST]. Treyarch kept exploder lights small (median radius 20) [VERIFIED].
- **Four states only.** Whether each extra state with its own SSI adds bake time or `.led` data is unmeasured: the LED lists an SSI for all four states even when only `ssi1` is set, and Radiant has "NO BAKE STATE" skip/reuse paths whose triggers are unknown [TEST].

---

## 18. Quick reference: which layers each fixture needs

| Fixture | Visible source | Room light | Reflection side | Typical switch | Stock reference |
|---|---|---|---|---|---|
| Ceiling downlight | emissive or backlit lens | Radiant spot, static shadow | fitted probe | state twins | Giant pool spots, IES spots |
| Cage lamp | emissive bulb + backlit shade | bulb omni (r 15) + pool spot | fitted probe | state twins | `geo/zm_giant_light_cage_03` |
| Hurricane lantern | flame FX | FX omni (flicker) | `PROBE_ONLY` twin | always on | `geo/lantern_lit` + `light/fx_light_lantern_factory_zmb` |
| Street lamp | emissive/backlit lens (+flare) | spot + IES cookie, head omni | `PROBE_ONLY` fill + probe | twins or exploder | assembled (no stock street lamp) |
| Wall sconce | backlit shade | bulb omni + wash spot(s) | fitted probe | twins | `geo/zm_giant_light_cage_05` |
| Fluorescent | emissive tube + backlit cover | `bulbLength` omni or rectangle spot | fitted probe | twins; FX for flicker | mp_sector area light |
| Neon sign | emissive tubes | spill omni in hue | probe | model swap | vertigo library |
| TV / monitor | scroll emissive | optional face omni | — | model swap | Winslow monitor material (T7) |
| Spot with cookie | fixture | spot + `def` cookie | probe | twins | Giant cookie spots |
| Searchlight | sprite beam FX | FX spot on rotating host | — | script | modme 1928 |
| Burning barrel | flame FX | FX omni | `PROBE_ONLY` twin | always on | Giant barrels |
| Flickering light | scroll emissive | cookie spot or FX light | `PROBE_ONLY` twin | FX / exploder | Giant flicker cookies, `fx_light_yellow_flicker2` |
| Status lamp | emissive lens | tiny omnis in exploders, FX flasher | — | exploder via clientfield | Giant `map_lgt_*` |
| Lit window | backlit pane or emissive card | light behind pane | — | state (backlit follows the light) | `geo/zm_giant_visfire_window_lit` |
| God ray | sprite cone or volumetric | spot at the landing point | — | — | `light/fx_light_cone_metro_sm` |
| Perk pool | `_on` model | FX light via clientfield | pad `PROBE_ONLY` | clientfield | `_tod_perk_lights` |
| Teleporter pad | emissive model | spot twins + FX | `PROBE_ONLY` fills | twins + exploders | `light/zm_giant_teleporter` |
| Caustics | — | spot + caustic cookie | — | always on | Giant caustic spots |

---

## For Tower of Doom II

Recommendations only; nothing here changes code or data, and nothing is tested.

1. **Fix the foundation before adding fixtures.** Today the game boots in script state 1 (Radiant State 2), where all 344 generator lights are authored on, but the `volume_sun` sets only `ssi1`, so the live state is paired with `default_day` in the LED [VERIFIED] (map + .led); what that shows in game is untested [TEST]. Settle it first: give `ssi2` (and any other state you use) a real SSI such as `tod_ssi_cybercity`, and A/B the look (recipes in [02](02_power_and_states.md)). The sun volume's missing global-probe `target` (its probe sits inside the `mast tier 1` brush) is a related open item ([05](05_sun_sky_exposure_fog.md)). Every twin, mask and exploder in this chapter depends on that answer.
2. **Teach the generator more than one light.** `tools/gen_tower_map.js` `light()` emits one kind: a shadowless omni (`PRIMARY_NOSHADOWMAP 1`, `shadowUpdate Never`) at stops 6, `falloffdistance 12`, mask `0111`, ClientSide, with brightness varied through `bake_intensity_scale` [VERIFIED]. The recipes above need a spot emitter (`PRIMARY_SPOT`, `angles`, `fov_outer`, `cut_on`, `def`), a bulb-glow preset (radius 15), a `PROBE_ONLY` preset, static shadows (`PRIMARY_NOSHADOWMAP 0`, `shadowUpdate Never`), culling keys, and a mask argument for the ALWAYS / PREPOWER / POWERED / STAGED classes. Brightness should move with `stops`, not `bake_intensity_scale`.
3. **Start where the player starts.** The Vault spawn is the first thing every run sees: a few strong, tight pools (recipes 1–2) against a dark base, the red window lamps kept as hazard markers (11a), and one flame or caged lamp as a motivated source.
4. **Use status light as the tower's language.** Door gates and teleporter pads as red → green status lamps (11a, 15), in the district colours for everything else.
5. **Lounges and perks:** coloured `PROBE_ONLY` fills per lounge colour for reflections, a stronger downward FX light for each perk pool (14.3), and an A/B of the interval = lifetime loop fix on the perk glows and inducer, judged by the user.
6. **Keep the open spiral mostly sky- and emissive-lit.** Street-lamp-style pools (recipe 3) belong at landings and doors, not along every flight. The per-floor reveal (17) should use exploders or clientfield FX, because 4 lighting states cannot stage 50 floors.
7. **Replace the placeholder motes.** `env/light/fx_light_god_rays_dust_motes` is a stub; swap to `dirt/fx_dust_motes_200x200` or `_300x300_sm` (13b). The zone also carries `fx,zombie/fx_thundergun_smoke_cloud`, another stub source ([04](04_fx_lights.md)).
8. **Build switchable glow on entities.** The world grid's glow does not follow power [INFERRED]. Anything that should ignite at power (panels, signs, strips) must be a `script_model`/`script_brushmodel` with an `_on` twin, a script-driven material, or (untested) a state-masked model pair (17.4 step 6).
9. **Fit probes before judging any fixture's reflection.** The 53 probes are 144-unit default cubes today ([06](06_reflections_probes.md)); on mirror-like vertigo floors every fixture's reflection depends on them.
10. **Test on the user's config and a high config.** Volumetric beams and live light shadows will not appear in the user's playtests.
11. **Isolation and build rules.** New materials, models and effects go into map-owned sources in the private workspace (docs/154); every light change is a full build; build and stop, the user tests.

---

## Sources

Official Treyarch documentation (MODTOOLS/docs_modtools):
- Lighting_Parameters.pdf — stops, `cut_on`, `fov_outer` ≤ 120 warning, `far_edge`, shadow budget p.11, lighting states.
- Materials.pdf — lampshade (Lit Backlit) shaders p.16-17, Lit Emissive and the 2^EV HDR scale p.18, transparency warnings.
- FX_Lights.pdf — FX light workflow, loop timing rule, "Always live, or Off" shadows, per-instance limits, exploder creation.
- Culling_LOD_Lights.pdf — `culling_cutoff` / `culling_falloff` starting values.
- Build_light.pdf — static-shadow behaviour description.
- Generate_LED.pdf; SunSky_Light_SetUp.pdf; Multiplayer_Lighting_Workflow.pdf — LED rebuild rule, sun-volume states, exposure range and local lit-fog advice.
- bo3_scriptapifunctions.htm — `SetLightingState`, `GetLightingState`, `SetLight*`, Radiant exploder functions, `MapShaderConstant`.
- PhysicallyBasedRendering.pptx slides 10 and 15 — albedo floor ("No values below 40"), transparency cost.

Stock data (MODTOOLS):
- bin/t7.def.json — `light`, `fx`, `volume_sun`, `volume_litfog`, `pbg_box` keys, defaults and descriptions.
- map_source/_prefabs/zm/zm_giant/zm_giant_light.map — every Giant lamp, fire, flicker, caustic, status and moon light cited here.
- map_source/_prefabs/zm/zm_giant/geo/zm_giant_light_cage_03.map, zm_giant_light_cage_05.map, lantern_lit.map, burn_barrel.map, zm_giant_utility_pole_01.map, zm_giant_visfire_window_lit.map.
- map_source/_prefabs/zm/zm_giant/light/zm_giant_teleporter.map; light/zm_giant_post.map (`power_off` / `power_on` grades); map_source/_prefabs/zm/zm_giant/fx/zm_giant_fx_ambient_interior.map and _exterior.map.
- map_source/zm/zm_giant.map (worldspawn exposure and shadow slices).
- map_source/_prefabs/mp/mp_sector/mp_sector_light.map (area light, elongated spot).
- map_source/_prefabs/zm/zm_core/vending_*_struct.map (stock perk lights).
- texture_assets/t7_glass.gdt (`t7_glass_window_warehouse_backlit`), t6_lights.gdt, t7_light_gobo.gdt, t7_cookie.gdt (cookies).
- share/raw/fx/light/*, fire/*, dirt/*, lensflares/*, dlc*/ (effect contents and placeholders); share/raw/lensflares/*.klf.
- share/raw/scripts/zm/zm_giant.gsc:132, 420-432, 524-590; zm_giant_fx.csc:69-71, 164-292; zm_giant_teleporter.gsc:743-744; zm_giant_teleporter.csc:107-143; zm_usermap.gsc:110, 446; zm_usermap.csc:107; _zm_perks.gsc:113-161, 280-318; _zm_perks.csc ~195-262; _zm_perk_*.gsh (machine models); _zm_perk_quick_revive.gsc:155-190, 791; _zm_power.gsc:723-736; _zm.csc:335, 390-396; _zm_traps.gsc:445-477; _zm_trap_electric.csc:20-37; _zm_perk_random.csc:104; shared/util_shared.gsc:1390-1402, 2975-3005; shared/exploder_shared.gsc/.csc; zm/gametypes/_globallogic_spawn.gsc:501.
- source_data/ssi.gdt; deffiles/material.awi (scaleRGB, flicker fields).

Third-party data installed in the shared tools root (file contents read directly; not Treyarch originals):
- source_data/_emox/emox_mwiii_vertigo_assets.gdt (vertigo emissive, scroll and flicker values); source_data/acc_t7_props_pilot.gdt (Winslow monitor, Map One's port of a T7 DLC material); source_data/p7_zm_ori_light_warning_metal.gdt; share/raw/fx files whose source is a Wraith extraction (castle street light and searchlight, dust motes, `dlc5/*` shafts).

Project files (this repo unless noted):
- tools/gen_tower_map.js (`light()`, `probe()`, Undercity lights, `volume_sun`); map_source/zm/zm_tod2_cybercity.map; zone_source/zm_tod2_cybercity.zone.
- scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc/.csc, _tod_rampage.gsc, _tod_atmosphere.gsc; share/raw/fx/tod/*, share/raw/fx/acc/light/*; source_data/tod_bo6_inducer.gdt, tod_skybox.gdt.
- CLAUDE.md; docs/154; docs/143; CHANGELOG.md (v17.28).
- c:/Users/jorda/Repositories/abandoned_cyber_city_zombies/scripts/zm/zm_abandoned_cyber_city.gsc (`CheckForPower`), CHANGELOG.md ("Power-on light WARM-UP").
- C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III/players/config.ini (the user's graphics settings).

Community:
- VerK0 Lighting Tutorial Parts 1–5 (YouTube hPweAEu8zJY, 8j7_EjLVFJA, EyIqeAufdFc, HOa08arAXlk, VPT3TJzbQPc) — lamp technique, feathered spots, cookie flicker, `PROBE_ONLY` room glow.
- https://github.com/dtzxporter/ModmeForum (threads 1565, 1928, 2029, 2118, 2987) and https://www.ugx-mods.com/forum/help-desk/86/lights-leaking-through-walls/14935/ — video materials, searchlights, exploders, power-on hitch, light bleeding.
- https://github.com/MattFiler/zm_alien_isolation — a shipped community map with four lighting states and an alarm state.
- https://left4deadwiki.com/wiki/Developer_Commentary_(Left_4_Dead); https://book.leveldesignbook.com/process/lighting/darkness; https://www.blog.radiator.debacle.us/2018/03/gdc-2018-how-to-light-level-slides-and.html — dark-map design principles.
