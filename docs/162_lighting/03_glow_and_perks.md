# 03 — Things that glow: emissive materials, perk glows, screens and neon

**In short.** In BO3 a glowing object is usually two things: a surface that *looks* bright (an emissive or "lampshade" material, or a glow sprite) and a light that actually brightens the walls, floor and zombies around it (a Radiant light or an FX light). No source shows an emissive surface lighting anything else, so a neon sign that should wash its wall needs a light beside it. Glow strength is the material's **HDR Scale** (`scaleRGB`); Treyarch's shortcut is HDR Scale = 2^EV of the area it sits in. Emissive glow does not follow power or lighting states on its own: to switch it you swap the model, hide or show an entity, drive a script-controlled emissive material, or put a lampshade material in front of a switchable light. Tower of Doom II builds its whole world from emissive materials and makes its perks glow with a client-side FX light, and both facts shape what a dark version of the map can do.

**Read this when…** you are making anything that should look lit (a bulb, a street-lamp head, a neon sign, a screen, an LED strip, a lit window, a perk machine, a glowing device), or when you are deciding what in the tower stays dark before the power comes on.

Nothing in this chapter was tested in game for this reference. Where the project holds an in-game record from the user's own playtests, it is tagged [COMMUNITY] (project record).

**Contents**
1. [The five ways an object lights up](#1-the-five-ways-an-object-lights-up)
2. [Emissive materials: the family and every field](#2-emissive-materials-the-family-and-every-field)
3. [How bright: HDR Scale and the 2^EV rule](#3-how-bright-hdr-scale-and-the-2ev-rule)
4. [Does an emissive surface light up the room?](#4-does-an-emissive-surface-light-up-the-room)
5. [Bloom: why bright glow gets a halo](#5-bloom-why-bright-glow-gets-a-halo)
6. [Lampshades: the backlit family](#6-lampshades-the-backlit-family)
7. [Moving glow: flicker, scroll, flipbooks, screens](#7-moving-glow-flicker-scroll-flipbooks-screens)
8. [Switching a glow on and off](#8-switching-a-glow-on-and-off)
9. [Perk machine glow: stock and ours](#9-perk-machine-glow-stock-and-ours)
10. [Other glowing things in TOD II](#10-other-glowing-things-in-tod-ii)
11. [TOD II's all-emissive world](#11-tod-iis-all-emissive-world)
12. [Recipes](#12-recipes)
13. [Gotchas](#13-gotchas)
14. [Open questions and tests](#14-open-questions-and-tests)
- [For Tower of Doom II](#for-tower-of-doom-ii)
- [Sources](#sources)

---

## 1. The five ways an object lights up

Take a lit lamp in The Giant (BO3's remake of Der Riese, whose lighting prefabs ship with the Mod Tools). What the player sees as "a lit lamp" is several separate things placed together: a bulb model with a bright material, a tiny light inside the shade, a bigger light that throws a pool on the floor, and, for lanterns, a flickering flame effect. Each part is a different engine system, and each does one job. Getting a dark map right mostly means knowing which system does what.

| # | Mechanism | What it does | Does it light the walls, floor and zombies around it? | Can it switch with the power? | Examples |
|---|---|---|---|---|---|
| 1 | **Emissive material** (`lit_emissive*`, `decal_emissive*`) | The surface adds its own brightness on top of normal lighting. Very bright values bloom. | **Not shown to.** No doc, material field or render flag makes a `lit_emissive*` surface a light source in the bake. Design as if it lights nothing ([§4](#4-does-an-emissive-surface-light-up-the-room)). | Not by itself. On an **entity** you can swap the model, hide/show it, or drive a script-emissive material. **World brush faces cannot change at runtime.** | Every TOD II world face; the Rampage Inducer; the heavenly altar; the teleporter; cyber-zombie eyes |
| 2 | **Backlit "lampshade" material** (`lit_backlit*`) | Lit from both front and back, so a light placed behind it shows through | No. The light behind it does the lighting. | Yes, with the light behind it. That is why Treyarch built it ([§6](#6-lampshades-the-backlit-family)). | A community-ported Electric Cherry machine body (`lit_backlit_plus`) |
| 3 | **Radiant `light` entity** (omni or spot) | A real light, baked into the lighting and/or drawn live | **Yes.** | Yes: lighting states, a Radiant exploder, or a scriptable light ([02](02_power_and_states.md)) | The Giant's 543 lights; TOD II's 344 omnis |
| 4 | **FX light** (a `dynamicLight2` element inside an `.efx`) | A live light carried by an effect. Its brightness, size and colour can animate: pulse, flicker, blink. | **Yes** (live only, not baked) | Yes: play or stop the effect, or use `fxstate1..4` on a Radiant `fx` entity ([04](04_fx_lights.md)) | TOD II perk glows (`acc/light/fx_perk_glow_*`), the inducer's light (`tod/fx_tod_inducer_*`) |
| 5 | **Model or material swap** | `SetModel` to an `_on` version, usually the same mesh with hotter material twins | No. It is still mechanism 1. | Yes, by design | TOD II's BO7 perk machines, `tod_inducer_on`, The Giant's client lamp-swap code (`lights_indlight_on`) |

**The fake one: sprite halos.** A camera-facing sprite with a glowing material looks like light but lights nothing. The perk auras stock *server* script plays, `zombie/fx_perk_*_zmb`, are only this: 3–4 `billboardSprite` elements and no light element [VERIFIED] (src: share/raw/fx/zombie/fx_perk_juggernaut_zmb.efx and siblings); that they therefore light nothing is [INFERRED]. The variants that do carry lights are covered in [§9.1](#91-how-stock-bo3-perk-machines-turn-on). Sprites, lens flares and fake light cones are covered in [04](04_fx_lights.md).

**Rule of thumb** [INFERRED] (consistent with Treyarch's lampshade guidance): the visible **source** (bulb, tube, screen, sign) is mechanism 1 or 2. The **light it throws** is mechanism 3 or 4. If an object should both look lit and light its surroundings, it needs one of each.

---

## 2. Emissive materials: the family and every field

### 2.1 What an emissive surface is: two layers added together

The official doc says: "These shaders are also lit, they will behave properly in multiple lighting environments. These can be used for computer screens, glowy tech read-outs, etc." [VERIFIED] (src: docs_modtools/Materials.pdf p.18; the Lit Emissive heading starts at the foot of p.17). An emissive material is therefore two layers [INFERRED] (from that wording and the techset slots):

- a normal **lit layer**: Color Map × Albedo Tint, shaded by lights, baked lighting, reflection probes, gloss and specular;
- an **emissive layer**: Emissive Map × Emissive Tint × HDR Scale, which ignores lighting.

**The lit layer is still there, and that causes trouble.** The MWIII "vertigo" pack that TOD II's world is built from uses `$white_diffuse` as its Color Map, `$white_specular`, a high gloss range and `reflectionProbeAmount 1` [VERIFIED] (src: MODTOOLS/source_data/_emox/emox_mwiii_vertigo_assets.gdt). So the "black" tiles are really white, glossy, reflective surfaces with black glow. Any light paints them in its own colour. The project hit exactly this: a warm spawn omni turned the spawn, the core's face, hands, guns and zombies olive-yellow because "the floor's colourMap is $white_diffuse" [COMMUNITY] (project record) (src: tools/gen_tower_map.js:7210-7213). For a surface that should stay black where it does not glow, give it a dark Color Map. Treyarch's Origins portal materials use `$black_color` [VERIFIED] (src: MODTOOLS/source_data/p7_zm_ori_tomb_portal_screen.gdt).

### 2.2 The emissive family

All opaque `lit_emissive*` geometry techsets render on the **forward** path (`renderFlags = "lit forward opaque"`). Plain `lit` and the backlit family render **deferred** [VERIFIED] (src: share/raw/techsetdefs_stable/geometry/lit_emissive.techsetdef, geometry/lit_backlit.techsetdef, renderFlags.techsetdef).

| `materialType` | Adds on top of the lit layer | Use for | Examples with values |
|---|---|---|---|
| `lit_emissive` | emissive map, tint, HDR scale, falloff, depth | cheapest glowing prop or sign | stock `mtl_p7_zm_ori_light_warning_metal_on`, HDR 8 (Treyarch's `_on` lamp naming) [VERIFIED] |
| `lit_emissive_plus` | + AO and gloss maps. **No specular-map slot.** | props that need AO/gloss but not a spec map | TOD II inducer body and crystals [VERIFIED] |
| `lit_emissive_advanced` | + specular map and spec tint | glowing metal | the whole vertigo pack, i.e. TOD II's world [VERIFIED] |
| `lit_emissive_advanced_fullspec` | + full-colour specular map | multi-metal props with glow | TOD II heavenly altar, teleporter, cyber zombies [VERIFIED] |
| `lit_emissive_transparent` (+ `_advanced`, `_script` …) | see-through glow; the doc warns "BE VERY CAREFUL WHEN USING THE TRANSPARENT VERSIONS" | glass, holograms | inducer glass; altar wings [VERIFIED] |
| `lit_emissive_scroll*` (`_plus`, `_alphatest`, `_transparent`, `_2layer`, `_3layer`, `_advanced_fullspec` …) | + **UV scroll/rotate/zoom**, **flipbook**, **flicker** | screens, holograms, flowing energy, flickering neon | vertigo `_pap` (`lit_emissive_scroll_plus`, scroll 0.2/0.1); Origins portal (`_3layer_transparent`); Winslow monitor [VERIFIED] |
| `lit_emissive_script*` (`_plus`, `_advanced`, `_advanced_fullspec`, `_vectorpick`; also `lit_emissive_5tint_script`) | + four tint states and a script control | glow driven by script | T5 Thundergun port glow, HDR 50 (community port GDT) [VERIFIED] |
| `lit_emissive_mp4` | reads the engine's cinematic stream at runtime; its emissive map is only a "PREVIEW" | video on a surface | needs a script `VideoStart`; a community test saw only a still image; untested here ([§7.3](#73-video-on-a-surface)) |
| `decal_emissive*` (`_mask`, `_scroll`, `_script`, `_digits` …) | glowing decal laid on existing geometry | glowing signage or runes on a wall | techsets exist [VERIFIED] (src: share/raw/techsetdefs_stable/decal) |
| `emissive_add`, `specialty/emissive_passthrough*` | additive / pure self-illumination; render flag `emissive …` | halos, special cases | none in local GDTs; behaviour [INFERRED] |
| `lit_backlit*`, `lit_transparent_backlit*` | lampshade family: deferred, `nocull` | lamp covers, lit panels | [§6](#6-lampshades-the-backlit-family) |

The `_plus` / `_advanced` / `_fullspec` difference is real: `lit_emissive_plus` is built on `lit_base_mid` (colour, normal, AO, gloss), while `lit_emissive_advanced` adds `specular_base` and `_advanced_fullspec` adds a full-colour `specColorMap` [VERIFIED] (src: share/raw/techsetdefs_stable/geometry_plus/lit_emissive_plus.techsetdef; geometry_advanced/lit_emissive_advanced*.techsetdef; include/lit_base*.techsetdef). The project rediscovered this when the cyber zombies' spec map had no effect under the Plus shader (src: CLAUDE.md, cyber zombie notes).

### 2.3 Every emissive field

GDT key = what the `.gdt` stores. APE label = what the material editor shows. Sources: share/raw/techsetdefs_stable/include/emissive_base.techsetdef, include/flicker_base.techsetdef, include/flipbook_base.techsetdef, geometry/lit_emissive_scroll.techsetdef, geometry/lit_emissive_script.techsetdef; deffiles/material.awi.

| GDT key | APE label | Default / range | What it does | Tag |
|---|---|---|---|---|
| `colorMap00` | Emissive → **Emissive Map** | blank → `$white_diffuse` | Full-colour glow picture. The doc says: make glowing parts as bright as allowed and "parts that have no glow should be full-on black (0, 0, 0)" (Materials.pdf p.18). | [VERIFIED] |
| `colorTint1` | Emissive → **Tint** | 1 1 1 1 (converted sRGB → linear) | Multiplies the whole emissive map | [VERIFIED] |
| `scaleRGB` | Emissive → **HDR Scale** | **8**, 0–999999 (material.awi:1543) | Brightness of the brightest emissive pixel ([§3](#3-how-bright-hdr-scale-and-the-2ev-rule)) | [VERIFIED] |
| `emissiveFalloff` | Emissive → **Falloff** | 0, 0–128 (material.awi:803) | A power term paired with "Invert falloff (brighter edges)", so probably a view-angle falloff | field [VERIFIED], meaning [INFERRED] |
| `invertFalloff` | "Invert falloff (brighter edges)." | false | Flips the falloff | [VERIFIED] |
| `emissiveIncompetence` | "**Use gameplay intensity.**" (shader bool `relativeHDR`; the APE entry is titled "Failure to achieve.") | false | Undocumented. Possibly makes the glow relative to exposure. Every vertigo material except `_off`, and TOD II's own world and prop glow materials (`tod_door_*`, `tod_hall_*`, inducer, altar, teleporter, cyber zombies), set it to 1; Treyarch's `_on` warning lamp and a few imported materials use 0. | field [VERIFIED], meaning [INFERRED] |
| `waterRoughness` | Emissive → **Depth** | doc: start at 0.1 | Parallax depth, so the glow seems to come from under the surface. "If you try a crazy number, you'll probably poke your eye out." | [VERIFIED] |
| `colorMap`, `colorTint` | Color Map, Albedo Tint | `$white_diffuse`, 1 1 1 1 | The ordinary lit layer ([§2.1](#21-what-an-emissive-surface-is-two-layers-added-together)) | [VERIFIED] |
| `colorTint2/3/4` | Tint State 2/3/4 (`*_script` only) | | Alternative emissive tints picked by the script "State" | [VERIFIED] |
| `cg00_x`, `cg00_y` | Script Preview → "Tint (Brightness, State)" (`*_script` only) | 1.0, range 0–4 | Editor preview of the script control (the techset parameter is named `scriptControl`) | [VERIFIED] |
| `gUVScroll02_Angle`, `gUVScroll03_Angle` | Scroll (U, V) (`*_scroll`) | | Scroll speed of the emissive map | [VERIFIED] |
| `uvScrollAngle`, `uvRotationRate` | UV Rotation, Spin Rate | | Rotate the emissive map | [VERIFIED] |
| `detailScaleX/Y`, `uScroll/vScroll` | Scale (U, V), Offset (U, V) | | Tiling and offset | [VERIFIED] |
| `zoomMin/zoomMax`, `zoomRate`, `clampU/V` | UV Zoom, Zoom Rate, Clamp | | Pulsing zoom, clamping | [VERIFIED] |
| `uvMotionToggle1` | "UV Toggle (Flipbook - 1, Scroll/Rotate - 0)" | 0 | Picks flipbook or scroll | [VERIFIED] |
| `rowCount`, `columnCount`, `imageTime` | Flipbook Row Count / Column Count / Image Time | 1 / 1 / 1 | Sprite-sheet animation. GDTs also carry `textureAtlasRowCount/ColumnCount/FrameRate`, but the scroll techset reads `rowCount`, `columnCount` and `imageTime`. | [VERIFIED] |
| `flickerLookupMap` | Flicker Lookup Map | `i_generic_lookup` (image semantic `revealMap`) | Texture that shapes the flicker | [VERIFIED] |
| `flickerSeedU`, `flickerSeedV` | Seed (Style, Time) | 0, 0 (0–1) | Flicker style / time offset, to desync copies | [VERIFIED] |
| `flickerSpeed` | Speed | 1 (0–128) | Flicker rate | [VERIFIED] |
| `flickerPower` | Harshness | 1 (0–128) | "Harshness of flicker transitions" | [VERIFIED] |
| `flickerMin` / `flickerMax` | Range (Min, Max) | 0 / 1 (max up to 2) | "Darkest the flicker will get" / "Brightest" | [VERIFIED] |
| `areaLight` | "Area Light" | false | material.awi:1268 marks it `// NOT USED`. It does not make a surface cast light. | [VERIFIED] |

**The flicker fields only work on the scroll family** (plus some decal and specialty techsets). Plain `lit_emissive`, `_plus`, `_advanced` and `_advanced_fullspec` include `emissive_base` but not `flicker_base` [VERIFIED] (src: grep of share/raw/techsetdefs_stable for `flicker_base`). The vertigo GDT stores `flickerMin 0 / flickerMax 1` on plain `lit_emissive_advanced` materials too. Those values are never read [INFERRED] (from the techset includes). One exception to watch: the six `effect_lit_scroll_emissive_blend*` particle techsets read `flickerLookupMap` as an **Alpha Mask**, not as a flicker lookup [VERIFIED].

### 2.4 Trap: a blank emissive map glows white

`emissive_base` reads `Image( <colorMap00, $white_diffuse> )` [VERIFIED] (src: share/raw/techsetdefs_stable/include/emissive_base.techsetdef). If you pick a `lit_emissive*` type and forget the Emissive Map, the **whole surface** glows at HDR Scale (default 8) in the tint colour. On a dark map that is a bright, flat, self-lit object. Always fill `colorMap00`, and paint the non-glowing parts pure black.

The same default can be used on purpose. The inducer's glass sets `colorMap00 $white_diffuse` so the whole pane glows evenly at HDR 0.4 (idle) / 6 (on) [VERIFIED] (src: source_data/tod_bo6_inducer.gdt). That is a choice, not an accident.

---

## 3. How bright: HDR Scale and the 2^EV rule

### 3.1 The rule

Treyarch's doc on HDR Scale: "This corresponds to the HDR brightness of the brightest part of your emissive map. Talk to the lighters … If you know the exposure for the area … 1. Get the exposure value for the area you are placing this prop (An interior at EV 3, for example) 2. Evaluate 2 ^ EV … the interior with EV 3 would mean that we need to raise two to the third power, which gives us 8. Eight is our HDR scale." [VERIFIED] (src: docs_modtools/Materials.pdf p.18).

In plain terms: the glow should match how bright the place is exposed for. It is a shortcut, not a law. Two things follow from the arithmetic [INFERRED]: **doubling `scaleRGB` = one stop brighter glow**, halving = one stop dimmer; and HDR 8 is "correct" for an area exposed at EV 3, which is also the material default.

Careful with the direction of EV: a place exposed at a higher EV is a *brighter* place (sunlit exterior ≈ EV 12), so an emissive there needs a *higher* HDR Scale to still read as glowing ([05](05_sun_sky_exposure_fog.md) covers exposure).

### 3.2 What that gives on this map

TOD II's SSI `tod_ssi_cybercity` carries `ev 6`, `evcmp 2.5`, `evmin 3`, `evmax 3.5` (the stock `default_night` values) [VERIFIED] (src: source_data/tod_skybox.gdt). The Giant's worldspawn clamps `evmin 3` / `evmax 3.5` too [VERIFIED] (src: MODTOOLS/map_source/zm/zm_giant.map). If our areas really settle at EV 3–3.5, the formula says an "honest" glow is **HDR 8–11** [INFERRED]. Whether auto-exposure is actually active here, and how `evcmp` shifts it, is unexamined ([05](05_sun_sky_exposure_fog.md)). By that yardstick, the vertigo grid lines at 15 sit about 1.3–1.9× above the doc value, and the filled faces at 10 and 5 sit near it and below it [INFERRED].

### 3.3 Real values to calibrate against

"Stops" here is log2(scaleRGB), for comparison only.

| Material | Type | HDR Scale | ≈ stops | Notes |
|---|---|---|---|---|
| vertigo `<colour>` (plain grid) | lit_emissive_advanced | 15 | 3.9 | TOD II world; thin grid lines on black |
| vertigo `<colour>_tinted` | lit_emissive_advanced | 10 | 3.3 | filled faces |
| vertigo `<colour>_tinted_edge` / `tod_door_*` | lit_emissive_advanced | 5 | 2.3 | same texture as `_tinted` at half strength; `tod_door_*` are matte clones (spec and probe 0) |
| vertigo `_off` | lit_emissive_advanced | 0 | – | the unlit twin; tint 0 0 0; **unused** |
| `tod_hall_*` | lit_emissive_advanced | 4 | 2.0 | spire trial halls |
| inducer body/crystal idle → ON | lit_emissive_plus | 1.2 / 1.5 → 16 / 22 | ≈0.3/0.6 → 4.0/4.5 | ~3.5–4 stops brighter when ON; tint deepens `1 0.40 0.08` → `1 0.24 0.03` |
| inducer glass idle → ON | lit_emissive_transparent | 0.4 → 6 | | `emissiveFalloff 1.0` |
| `mtl_tod_altar` | lit_emissive_advanced_fullspec | 8 | 3 | wings `lit_emissive_transparent` 3 |
| `mtl_tod_teleporter`, cyber zombies | lit_emissive_advanced_fullspec | 6 | 2.6 | |
| stock warning lamp `_on` | lit_emissive | 8 | 3 | `emissiveIncompetence 0` |
| stock Origins portal | lit_emissive_scroll_3layer_transparent | 5 | 2.3 | Color Map `$black_color`, falloff 1 |
| stock Maxis essence bubble | lit_emissive_scroll_3layer_layerfade | 32 | 5 | falloff 10 |
| Winslow logo monitor (T7 DLC1 material in a Map One GDT) | lit_emissive_scroll_transparent | 10 | 3.3 | flicker speed 2, harshness 3, min 0.9, max 1 |
| T5 Thundergun glow (community port) | lit_emissive_script | 50 | 5.6 | script-driven, so not comparable |

All [VERIFIED] (src: MODTOOLS/source_data/_emox/emox_mwiii_vertigo_assets.gdt; repo source_data/tod_materials.gdt, tod_bo6_inducer.gdt, tod_heavenly_altar.gdt, tod_teleporter.gdt, tod_cyber_roster.gdt; MODTOOLS/source_data/p7_zm_ori_light_warning_metal.gdt, p7_zm_ori_tomb_portal_screen.gdt, p7_zm_gen_maxis_essence.gdt, acc_t7_props_pilot.gdt, night_t5_thundergun.gdt).

### 3.4 Glow reads by contrast

In TOD1 a Workshop player reported that the blue buyable door on floor 1 was hard to pick out against the blue walls and floor. The door slab was `blue_tinted_edge` (HDR 5) set in a room of `_tinted` faces at HDR 10: the same texture at half the brightness. The project summed it up as "the dimmest blue in a room full of brighter blue" and moved the ground level to the mostly black plain grid [COMMUNITY] (project record) (src: CHANGELOG.md v17.28). The eye judges glow against its neighbours. On a dark map a modest value stands out; on a bright map the same value disappears [INFERRED]. Plan a **brightness ladder** (for example: trims 4–6, signs 8–10, hero objects 16–22) instead of setting every glow high.

### 3.5 Particle glow uses a different scale

Glow sprites in effects use the Effect Lit Emissive materials, whose Intensity runs 0–12,000: "Light glows are set at 16. Fires are set at 256. The sun would have a value of 10,000. This is the same value that lights use" [VERIFIED] (src: docs_modtools/Materials.pdf p.23-24). There is also a particle option "Physically Based Emissive behavior", which makes the material "emit light at one consistent value instead of adjusting to remain visible across EV values" [VERIFIED]. See [04](04_fx_lights.md).

---

## 4. Does an emissive surface light up the room?

**Short answer: no source shows that it does. Design as if it does not.** If the wall next to a glowing sign should be lit, put a light (mechanism 3) or an FX light (mechanism 4) there. Treat this as a question to settle with a test [TEST].

The evidence:

1. **Treyarch's own design points the other way.** The lampshade shaders "are meant to be used with a light placed behind them to provide the actual glow and illumination. Hopefully, this makes switching lights on and off easier because we don't have to dial in and sync up a bunch of emissive materials" [VERIFIED] (src: docs_modtools/Materials.pdf p.17). The docs present emissive as a surface look ("computer screens, glowy tech read-outs").
2. **No bake setting or field makes it a light.** No doc, material field or `lit_emissive*` render flag was found that turns such a surface into a light source in the LED bake [VERIFIED] (absence, in the files searched). The render-flag file does define `isEmissive = true`, but only on the flag sets `emissive opaque/sky/decal/transparent` (used by `emissive_add`, `decal_emissive*`, sky techsets). The `lit_emissive`, `_plus`, `_advanced` and `_advanced_fullspec` techsets use `lit forward opaque`, which has no such flag. No doc says what `isEmissive` does in the bake [VERIFIED] (src: share/raw/techsetdefs_stable/renderFlags.techsetdef). The material field named `areaLight` is marked `// NOT USED` [VERIFIED] (src: deffiles/material.awi:1268).
3. **One emissive material is documented to light the bake: the sky.** "A sky light is defined in APE as a material", and changing `skyStops` needs a rebake "to see the effect of the bounced (GI) light" [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf). That is a separate material class (`sky_latlong_hdr`), covered in [05](05_sun_sky_exposure_fog.md).
4. **A possible indirect path exists and is untested.** Bounce light is built from reflection-probe captures: grid points cast rays, and "if these rays are at all visible to any nearby probe, then color data is read from them and used to calculate bounce lighting" [VERIFIED] (src: docs_modtools/Probe/Reflection_Probes.pdf). If probe captures include emissive surfaces, a large glowing surface could raise bounce light and show up in reflections [INFERRED]. Whether it does is unknown [TEST]. See [06](06_reflections_probes.md).
5. **Community practice matches.** Map One dropped a planned emissive neon kit for baked coloured light pools, because "a light entity casts the colored pool with no visible on-map source, which reads better than a flat emissive plane" [COMMUNITY] (src: Map One repo abandoned_cyber_city_zombies/docs/20_atmosphere_and_materials.md §12.2).

**Our own unmeasured claim.** The generator says that after the base floor went from a filled emissive to the plain grid texture, "the floor stopped lighting the room and the four corner lights are now most of what is down here" (src: tools/gen_tower_map.js:7187-7190). No bake A/B, probe comparison or measurement is recorded for it, in that comment or in the v17.28/v17.32 CHANGELOG entries [VERIFIED] (absence). The darkening the user saw has other explanations: the floor pixels themselves got darker, less glow in probe captures, less bloom [INFERRED]. Treat the comment as unproven.

**How to settle it** [TEST]: in the control map (`Repositories/test+map`), build two identical closed rooms with no lights. Give one a filled emissive floor (vertigo `_tinted`, HDR 10) and the other the same floor in a plain dark `lit` material. Full build with LED, then compare wall and prop brightness in game with `r_bloomEnable 0` to take bloom out of the comparison (src: docs_modtools/Mini_Map_Setup.pdf).

---

## 5. Bloom: why bright glow gets a halo

Bloom is the engine's post-process glow around very bright pixels. There is **no per-material bloom switch**: `material.awi`, `ssi.awi` and `postfxbundle.awi` have no bloom field [VERIFIED] (absence). The levers are volumes and presets:

| Lever | What it is | Tag |
|---|---|---|
| `vbloom_box` | a volume with key `lvi` ("lvi file to extract bloom from") and `mix` ("vbloom modifier maximum blend weight", default 1) | [VERIFIED] (src: bin/t7.def.json) |
| `pbg_box` with `USE_BLOOM` | the post-process volume's bloom flag, with `bloom_lvi` and `bloom_mix` keys | [VERIFIED] (src: bin/t7.def.json) |
| worldspawn `"bloom" "zm_factory"` | set in The Giant's map, but **not defined** for worldspawn in bin/t7.def.json, so its effect is unknown | key seen [VERIFIED] (src: MODTOOLS/map_source/zm/zm_giant.map); effect [TEST] |

Our worldspawn has no `bloom` key and the map has no bloom volume [VERIFIED]. `vbloom_box` and `pbg_box` default to `LIGHTSTATE_1` only, so in a map that boots Radiant State 2 such a volume may need `LIGHTSTATE_2` ticked [INFERRED] ([02](02_power_and_states.md), [05](05_sun_sky_exposure_fog.md)).

The project has seen bloom respond to brightness: sky pixels about 200× the sky base produced white halos in game, and a brightness knee fixed it [COMMUNITY] (project record) (src: CLAUDE.md v18.97; docs/104 §4k). **Lever: to reduce a halo, lower `scaleRGB` or darken the hottest pixels of the emissive map.** Do not remove the emissive. For screenshots without bloom use `r_bloomEnable 0` [VERIFIED] (src: docs_modtools/Mini_Map_Setup.pdf).

---

## 6. Lampshades: the backlit family

This is Treyarch's answer to "a lamp that switches on and off". The shade is not self-lit. It is lit from behind by a real light, so when the light turns off the shade goes dark with it.

The doc, under **Special Cases** [VERIFIED] (src: docs_modtools/Materials.pdf p.16–17):
- Types: Lit Backlit, Lit Backlit Advanced, Lit Transparent Backlit, Lit Transparent Backlit Reveal, Lit Transparent Backlit Advanced. They "have also been referred to as the 'lampshade shaders' … to accurately model the covers of lights, lamps, and light fixtures".
- "These shaders receive lighting from both their front and their back sides, but do not cast shadows from back faces. These materials are meant to be used with a light placed behind them to provide the actual glow and illumination."
- "Only use the transparent version of these shaders if you absolutely have to create a torn and tattered lampshade, or need to be able to see through this surface. Most of the time these surfaces should be opaque, they will naturally let the light shine through."
- Special slots: **Backlight Mask Map** ("any bars, wire, or internal structure that can occlude the light that comes through") and **Reveal Map**.

What the stock techset exposes [VERIFIED] (src: share/raw/techsetdefs_stable/geometry/lit_backlit.techsetdef; deffiles/material.awi:798-802):

| GDT key | APE label | Default | Notes |
|---|---|---|---|
| `alphaRevealMap` | Backlight → "Thickness Map" (material.awi also calls it "Reveal Map (Optional)") | `$thickness` | How much light gets through. Where the doc's "backlight mask" lives in this key is [INFERRED]. |
| `backlightScatterColor` | Backlight → "Tint" ("Sub-surface scatter: Color of the light coming through the material.") | 1 1 1 1 | Colour of the light that passes through |

Other facts:
- `lit_backlit` renders `lit deferred opaque nocull`, i.e. two-sided [VERIFIED]. The doc warns that no-cull shaders double the cost (src: Materials.pdf p.10).
- A community-ported Electric Cherry machine installed with Map One uses `lit_backlit_plus` for its body, with a `_t` thickness map and white scatter colour [VERIFIED] (src: MODTOOLS/source_data/acc_west_electric_cherry.gdt).
- Variants exist for flipbooks, scrolling and waterfalls (`lit_backlit_flipbook`, `_scroll`, `_waterfall` …) [VERIFIED] (src: share/raw/techsetdefs_stable/geometry).
- No TOD II world surface or prop uses a backlit material. The only one in the repo's GDTs is an effect material, `mtl_p7_window_glass_shard_snow_backlit_x` (`lit_backlit`, in source_data/xmas_gun_fx.gdt) [VERIFIED].

**How it switches:** put a light behind the shade whose lighting state or exploder follows the power ([02](02_power_and_states.md)). The shade follows the light. No material swap is needed [INFERRED] (from the doc's stated purpose). How strongly a baked (not live) light shows through a backlit surface is untested [TEST].

---

## 7. Moving glow: flicker, scroll, flipbooks, screens

### 7.1 Material flicker

The flicker fields work only on `lit_emissive_scroll*` and a few decal/specialty types ([§2.3](#23-every-emissive-field)).
- **Subtle buzz** (screen or healthy neon): Winslow monitor values, `flickerSpeed 2`, `flickerPower 3`, `flickerMin 0.9`, `flickerMax 1` [VERIFIED] (src: MODTOOLS/source_data/acc_t7_props_pilot.gdt).
- **Slow deep pulse:** the vertigo skydome material uses `flickerSpeed 0.1`, `flickerMin 0.1`, `flickerMax 1` [VERIFIED] (src: emox_mwiii_vertigo_assets.gdt).
- **No flicker on a scroll material:** the vertigo pack sets `flickerMin = flickerMax = 1` on a scroll material it wants steady (`light_pink_alpha`) [VERIFIED]. That suggests the defaults (min 0, max 1) do flicker [INFERRED]. The evidence is mixed: Treyarch's own Origins portal (`flickerSpeed 0.25`, `flickerPower 0.15`) and Maxis essence bubble (`flickerPower 0`) ship scroll materials at min 0 / max 1, and so does our world's `_pap` material [VERIFIED] (src: p7_zm_ori_tomb_portal_screen.gdt, p7_zm_gen_maxis_essence.gdt, emox_mwiii_vertigo_assets.gdt). Whether those shimmer on purpose or the range does nothing at low harshness is unknown. Set min = max = 1 on a scroll material that must be steady, and check in game [TEST].
- **Keep `flickerLookupMap`'s image semantic `revealMap`.** A wrong semantic on the shared `i_generic_lookup` caused a full-link shader failure in this project [COMMUNITY] (project record) (src: CLAUDE.md, staff animation migration notes).
- Desync identical signs with `flickerSeedU/V`.

### 7.2 Scroll and flipbook

- **Scroll or rotate** (data streams, energy flow, scanlines): `uvMotionToggle1 0`, then Scroll (U, V) in `gUVScroll02_Angle` / `gUVScroll03_Angle`. The vertigo `_pap` material scrolls at 0.2 / 0.1 [VERIFIED].
- **Flipbook** (an animated sign or screen from a sprite sheet): `uvMotionToggle1 1`, then `rowCount`, `columnCount`, `imageTime` [VERIFIED].
- **Layered holograms:** `lit_emissive_scroll_2layer` / `_3layer`. The Origins portal is `_3layer_transparent` [VERIFIED].
- A community thread reports `lit_emissive_scroll` as the working route for animated textures [COMMUNITY] (src: https://forum.modme.co/wiki/threads/1565.html). A second thread reports an unresolved shader-source link error with `lit_emissive_scroll_transparent` [COMMUNITY] (src: https://forum.modme.co/wiki/threads/1942.html). Test any new scroll type in a small build first.

### 7.3 Video on a surface

`lit_emissive_mp4` and `decal_emissive_mp4` exist [VERIFIED]. The mp4 techset labels its emissive map "PREVIEW Emissive Map", has a "Visible Rectangle" (`cg01`, `cg02`) and, in game, reads the engine's cinematic stream (`cinematicYSampler` / `cinematicCrSampler`) instead [VERIFIED] (src: share/raw/techsetdefs_stable/geometry/lit_emissive_mp4.techsetdef). The engine API has server calls to drive that stream: `VideoPrime( name, [loop] )` ("Preload the first second of a movie"), `VideoStart( name, [loop] )` ("Start a video for playback on an in-game surface"), plus `VideoStop`, `VideoPause` and `VideoUnpause` [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm). No stock script calls them [VERIFIED] (grep of share/raw/scripts).

A community test showed only a still image [COMMUNITY] (src: https://forum.modme.co/wiki/threads/1565.html). That may simply be the preview image shown when no video has been started [INFERRED]. How a usermap packages a movie, and whether `VideoStart` works in one, is untested [TEST]. Until that is tested, a flipbook ([§7.2](#72-scroll-and-flipbook)) is the dependable way to make a moving screen.

### 7.4 Flicker on the light itself

A flickering *material* lights nothing. The flicker on the room must come from an **FX light**: "the workflow for lights that flicker or change intensity, or that are animated … is to create an FX light in Radiant (as a .efx file)" [VERIFIED] (src: docs_modtools/FX_Lights.pdf p.1). A failing bulb is therefore a scroll-emissive bulb material **plus** an FX light with a flicker curve (for example, based on stock `light/fx_light_yellow_flicker2`). Nothing synchronises the two [INFERRED], so make the material flicker subtle and let the FX light carry the drama. Authoring details are in [04 §6](04_fx_lights.md#6-flicker-pulse-and-blink) and the loop-timing rule in [04 §5](04_fx_lights.md#5-the-looping-rule-and-why-it-matters).

---

## 8. Switching a glow on and off

Emissive glow does not follow power or lighting states by itself [INFERRED] (Treyarch's lampshade wording is indirect evidence). These are the ways to make something visibly switch (the same options, seen from the power side, are in [02 §12](02_power_and_states.md#12-switching-emissive-glow)):

| Option | How | Works on | Status |
|---|---|---|---|
| **A. Model swap to an `_on` twin** | Two xmodels with the same mesh; the `_on` one has an xmodel `skinOverride` mapping each material to a hotter twin ("Enter the name of the new material next to the one you want replaced", deffiles/xmodel.awi:379). The GDT stores one `old new` pair per line. Then `SetModel`. | script_model (server `SetModel`); client-side script models (client `SetModel`, as The Giant's CSC does) | **Proven here:** Rampage Inducer, user-approved [COMMUNITY] (project record). Stock code pattern: The Giant's client script swaps lamp models to `lights_indlight_on` etc. on client notify `pl1` [VERIFIED] (src: share/raw/scripts/zm/zm_giant_fx.csc:69-71, 184-197). No entity with those targetnames exists in the shipped Giant map sources, so it is a code example, not a working stock setup [VERIFIED] (absence, grep of MODTOOLS/map_source) |
| **B. Hide/Show an emissive entity** | Author the glowing panel as a `script_brushmodel` or `script_model` and `Hide()` / `Show()` it (or pair a dark one and a lit one) | entities | Hide on emissive door slabs is already used by the door system [VERIFIED]; using it as a glow switch is [INFERRED]. Each entity costs gentity budget (the spire's binding constraint, CLAUDE.md). |
| **C. Script-driven emissive** | `lit_emissive_script*` material (Tint States 1–4 + a script control). At runtime, client `MapShaderConstant( localClientNum, index, name, x, y, z, w )` and `SetShaderConstant( localClientNum, index, x, y, z, w )` on the entity | entities, client script | Engine functions exist (client only) [VERIFIED] (src: bo3_scriptapifunctions.htm). Stock Der Wunderfizz switches glow states this way: `MapShaderConstant( localClientNum, 1, "ScriptVector0" )` then `SetShaderConstant( … )` for dim / off / available / activated [VERIFIED] (src: share/raw/scripts/zm/_zm_perk_random.csc:104, 116, 257, 275, 346, 367). The techset calls the parameter `scriptControl` (previewed by the GDT's `cg00`); that script feeds it through `ScriptVector0` at runtime is [INFERRED], because the shader source is not shipped. Untested in our maps [TEST]. Could dim a machine before power and brighten it after, with no second model. |
| **D. Material override** | client `SetMaterialOverride( <material> )` / `ClearMaterialOverride()` on an entity | entities, client | Exists [VERIFIED] (API example `SetMaterialOverride("water")`); what it accepts and whether it suits a glow switch is [TEST] |
| **E. Lighting-state keys on models** | `misc_model`, `script_model` and `script_brushmodel` all carry `lightingstate1..4` bools (default true) | Radiant-placed entities | Keys exist [VERIFIED] (src: bin/t7.def.json). What they do at runtime (hide the model? bake only?) is undocumented; The Giant only ever sets them all true [VERIFIED]. [TEST] |
| **F. Backlit shade + switched light** | [§6](#6-lampshades-the-backlit-family) | models or brushes | Treyarch's documented design [VERIFIED] (doc); untested here |
| **G. Glow FX played at power** | Sprite halo + FX light, started by script at power ([§9](#9-perk-machine-glow-stock-and-ours)) | anywhere | **In use here** for the perk glows ([§9.3](#93-how-tod-ii-does-it-today)) [VERIFIED] (code); their look in TOD II is not separately recorded [TEST] |
| ✗ **World brush faces** | – | – | **Cannot switch.** Face materials are compiled into the BSP, no script call targets a world face, and worldspawn faces carry no entity keys [INFERRED] (src: docs/BO3_MAPMAKING_KB.md "Materials, sky & fog"; bo3_scriptapifunctions.htm). |

---

## 9. Perk machine glow: stock and ours

### 9.1 How stock BO3 perk machines "turn on"

All [VERIFIED] in stock scripts and data unless tagged.

1. **The model does not change.** Every stock perk `.gsh` defines the same model for "disabled" and "active", e.g. `p7_zm_vending_jugg` for both; Electric Cherry uses `p7_zm_vending_nuke` for both (src: share/raw/scripts/zm/_zm_perk_*.gsh:6-8; _zm_perk_electric_cherry.gsc:33-34). The swap code still runs: `perk_machine_think` does `SetModel( off_model )`, waits for `<alias>_on`, then `SetModel( on_model )`, `vibrate`, plays `zmb_perks_power_on`, threads `perk_fx`, and starts the machine loop sound (src: share/raw/scripts/zm/_zm_perks.gsc:113-161). With stock models the swap changes nothing visible. A custom perk *can* ship distinct off/on models through `level.machine_assets[key].off_model / .on_model`, and stock's host-migration handler even reads "model == on_model" as "this machine is on" when it restarts the aura (src: _zm_perks.gsc:1723).
2. **A server aura effect after 3 seconds.** `perk_fx()` waits 3 s, then server `playfxontag( level._effect[fx], self, "tag_origin" )`, or on a spawned `tag_origin` model if `b_keep_when_turned_off` (src: _zm_perks.gsc:280-318). Each perk's precache sets `level._effect["<perk>_light"]` to `zombie/fx_perk_*_zmb`, e.g. Juggernog `zombie/fx_perk_juggernaut_zmb`. These are **sprites only**: 3–4 `billboardSprite` and zero light elements (checked: doubletap2, juggernaut, mule_kick, quick_revive, sleight_of_hand, stamin_up, widows_wine). So they light nothing [INFERRED]. Stock Deadshot and Electric Cherry use `_t6/misc/fx_zombie_cola_dtap_on` / `fx_zombie_cola_revive_on`, one billboard each.
3. **The client "flicker to life".** On the client, `perk_start_up` waits for the client-side `power_on` notify, then plays the machine light effect in bursts of growing length (0.1 s, +0.2 s each) for about 3 s. Each burst spawns a client `tag_origin` model at the `zm_perk_machine` struct's origin − 50 on z (src: share/raw/scripts/zm/_zm_perks.csc:193-259). It runs only if `level.enable_magic` (src: _zm_perks.csc:195). The client `power_on` notify comes from `"ZPO"`, which the `zombie_power_on` clientfield handler sends only for a non-zero value, and stock global power sets that field to 0; The Giant sends `util::clientNotify( "ZPO" )` itself (src: share/raw/scripts/zm/_zm.csc:353-396; zm_giant.gsc:573). So on a map that does not send `ZPO`, this flicker probably never runs [INFERRED] ([02 §3](02_power_and_states.md#3-the-boot-state-spawns-and-per-player-state)).
4. **Two FX families, and only one carries real light.** The `*_factory_zmb` variants (The Giant's) contain 6–15 `dynamicLight2` elements each (daiquiri 9, doubletap2 6, juggernaut 7, mule_kick 14, quick_revive 9, sleight 15, stamin_up 13). `zm_usermap.gsc:446-455 perk_init()` would put the factory variants on the server, but **no stock script calls it** (grep). On the client, `zm_usermap.csc:84` calls `include_perks()` (:107-116), which assigns the factory variants, and the per-perk client init threads put the sprite-only versions back when `level.enable_magic` is true (src: _zm_perk_juggernaut.csc:32-38). The exact call order is [INFERRED].
5. **Radiant lights in the vending prefabs.** Each `map_source/_prefabs/zm/zm_core/vending_*_struct.map` (and the Pack-a-Punch prefab `vending_weapon_upgrade_spawnable.map`) carries 2–11 ClientSide lights, 49 in all: Mule Kick 8, Deadshot 2, Double Tap 4, Juggernog 6, Stamin-Up 8, Quick Revive 5, Speed Cola 11, Pack-a-Punch 5. Juggernog's are six spots, radius 25–95, stops 2–4.81, colours such as `1 0.451 0.451` and `1 0.8545 0.8392`, several with `shadowUpdate Always`. **Every one of them has `lightingstate1..4 = 0`.** Quick Revive's lights sit in exploder `quick_revive_lgts` (`exploderDisabled 1`); Mule Kick's in `lgt_vending_mulekick_on`; Stamin-Up's in `lgt_vending_stamina_up`.
6. **Only Quick Revive's lights are ever switched by stock script:** `exploder::exploder( "quick_revive_lgts" )` when the machine turns on, and `stop_exploder` after the last solo life (src: share/raw/scripts/zm/_zm_perk_quick_revive.gsc:185, 791). The script waits for `revive_on` only in co-op, so **in solo those lights come on at load** (src: _zm_perk_quick_revive.gsc:163-167). No stock script fires the Mule Kick or Stamin-Up exploders (grep of share/raw/scripts).

**So the stock "perk glow" = a sprite halo that lights nothing + a scripted flicker-on + prefab lights that, except Quick Revive's, never switch on.** Only prefab lights (or FX lights) would light the floor around a machine [INFERRED].

### 9.2 Why "my perk lights don't work"

This follows directly from point 5: a light with all four states unticked is probably never active [INFERRED] (the doc does not say what an all-false light does; [TEST]). Community fixes: enter the prefab, delete `exploder_count`, tick a lighting state, and switch state at power, e.g. `level flag::wait_till("power_on"); level util::set_lighting_state(2);` in the map script [COMMUNITY] (src: https://www.ugx-mods.com/forum/mapping/92/perk-lighting-effects-fix-video-tutorial/13226/ ; https://forum.modme.co/wiki/threads/1950.html ; https://steamcommunity.com/app/455130/discussions/0/2333276539589995175/). The modme author noted that the Radiant state numbers differed from the numbers the script needed, which fits script state n = Radiant State n+1 [COMMUNITY] ([02 §2](02_power_and_states.md#2-radiant-state-n-and-script-state-n)). Another user found perk lights would not switch while the sun volume used `default_day`, and fixed it with a real SSI in `ssi1` and `ssi2` [COMMUNITY] (src: https://steamcommunity.com/app/455130/discussions/0/2592234299570231550/). A community note also says the frame hitch when flipping power comes from registering perk hint strings, not from lighting [COMMUNITY] (src: https://forum.modme.co/wiki/threads/2118.html).

### 9.3 How TOD II does it today

The code is a port of Map One's `_acc_perk_lights`. All [VERIFIED] in the repo; how it looks in game is only partly recorded.

**The lit mesh (mechanism 5).** `bo7_machine_assets_pass` rewrites `level.machine_assets[spec].off_model` to the ported machine model (`t10_zm_machine_*`, and `sat_zm_machine_y_mod` for Widow's Wine) and `.on_model` to `off + "_on"`. Stock `perk_machine_think` then swaps to the lit mesh by itself at power. The pass also re-stamps live machines, because stock's `SetModel( off_model )` ran before the table changed. Solo Quick Revive is powered from spawn (src: scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc:261-383). Wisp Tea's vendored module writes its own off/on entry (comment at :270-276). The `_on` models' material definitions were not found in any local GDT, so their HDR values are unknown.

**The aura and the light (mechanisms 4 + sprites).**
- Server: waits for `initial_blackscreen_passed`, then for the `power_on` flag, then sets a 4-bit **scriptmover clientfield `todPerkGlow`** on each `zombie_vending` trigger's `.machine` to a colour index. Pack-a-Punch gets a spawned `tag_origin` host at its trigger origin − 50 on z, index 10 (src: _tod_perk_lights.gsc:38, 234-245, 383-421).
- Colour indices: Juggernog 1 red, Speed Cola 2 green, Double Tap 3 yellow, Stamin-Up 4 orange, Death Perception 5 amber, Quick Revive 6 blue, Wisp Tea 7 blacklight, Widow's Wine 8 white, PhD Flopper 9 purple, PaP/unknown 10 teal (src: _tod_perk_lights.gsc:466-497). The client file's comments still say "Mule Kick" (5) and "Deadshot" (7); the server mapping is the truth.
- Client: `glow_cb` waits for the model's dobj, stops the previous handle, and `PlayFXOnTag( localClientNum, level._effect["tod_glow_" + n], self, "tag_origin" )`. Registered with `!CF_CALLBACK_ZERO_ON_NEW_ENT` so the latched value replays for late joiners (src: scripts/zm/zm_tod2_cybercity/_tod_perk_lights.csc:54-83).
- **Rekick:** an effect started far from the viewer did not reliably appear on approach (a Map One finding) [COMMUNITY] (project record). So the server pulses the field 0 → index once, the first time a living player comes within 700 units (`TOD_GLOW_REKICK_DIST`) (src: _tod_perk_lights.gsc:424-461).
- **The effect:** `acc/light/fx_perk_glow_<colour>` (10 colours in the repo and zoned with `fx,acc/light/…` lines; Map One's install in MODTOOLS has 17, incl. `_dim` variants). Each has three sprite elements (spawn range 5000) and **one light element `light_small`**: `PRIMARY_OMNI`, `PRIMARY_NOSHADOWMAP 1`, intensity graph 512, radius graph 60, 40 units above the host, spawn range 3000, `culling_cutoff 75` / `culling_falloff 150` (src: share/raw/fx/acc/light/fx_perk_glow_amber.efx). The KVP block's `radius 100` and `stops 11` are probably not the live values: the doc says the light's KVPs mainly control light type and shaping "(except Radius and FOV)", and that Intensity, Radius and FOV are edited in Visuals → Color and animated with FX Graph curves (src: docs_modtools/FX_Lights.pdf p.1). That the graph values win is [INFERRED] ([04 §3](04_fx_lights.md#3-curves-not-the-settings-block-set-brightness-size-and-colour)). **So our perks do light their surroundings a little, through the FX light**, which the stock sprite auras cannot do.
- **Loop timing:** `light_small` spawns every 200 ms with a 1000 ms life, so about five light particles overlap [INFERRED] (arithmetic). That breaks the FX_Lights doc rule (interval = lifetime), under which a light "may build up too bright" [VERIFIED] (the rule, FX_Lights.pdf p.1; the effect in game is [TEST]) ([04 §5](04_fx_lights.md#5-the-looping-rule-and-why-it-matters)).

**Things we do not know yet** [TEST]:
- The stock server `perk_fx` is not overridden, so the stock sprite halo probably also plays on our machines 3 s after power, at least for Quick Revive, whose `zombie/fx_perk_quick_revive_zmb` is zoned (src: zone_source/zm_tod2_cybercity.zone) [INFERRED].
- The stock client flicker-on runs from the `.map`'s `zm_perk_machine` structs, which sit at the park positions (base north wall; Quick Revive's at z 19392). The scatter moves the machines, not the client structs. Anything the flicker plays would appear at the park spots, not at the machines [INFERRED] (from _zm_perks.csc and the map). It may not run at all: it waits for the client `power_on` notify, and no TOD II script sends `ZPO` [VERIFIED] (grep of scripts/) ([§9.1](#91-how-stock-bo3-perk-machines-turn-on) point 3).
- The code comment that "server-side PlayFX does NOT render in this build" (_tod_perk_lights.gsc:7) is a project heuristic from an uncontrolled Map One before/after, not an engine rule. Stock uses server `playfxontag` for perk auras ([04 §9](04_fx_lights.md#a-server-one-shot-playfx-renders-nothing-what-we-actually-know)).

### 9.4 Why an FX light is the right lane for our machines

TOD II's machines **move**: they scatter to random pads at load and reshuffle every 4 rounds (CLAUDE.md, perk scatter). A baked Radiant light or a `PROBE_ONLY` twin sits at a fixed spot, so it would light an empty pad after a reshuffle [INFERRED]. An FX light rides the machine. The cost is that FX lights are live only: nothing is baked and the reflection probes do not see them [INFERRED] ([04](04_fx_lights.md), [06](06_reflections_probes.md)).

---

## 10. Other glowing things in TOD II

### 10.1 The Rampage Inducer: the reference "idle glow / hot ON" device

The user asked for "a dim orange … lamp" when off and a deeper orange pulse when on, and approved the result in game ("looks good") [COMMUNITY] (project record) (src: CLAUDE.md v18.99i–k). It uses three mechanisms at once:

| Layer | OFF | ON | Source |
|---|---|---|---|
| Model | `tod_inducer` | `tod_inducer_on`: same `filename`, `skinOverride` swapping 5 materials to `_on` twins | source_data/tod_bo6_inducer.gdt:433-456 |
| Body/fluid emissive (`lit_emissive_plus`) | HDR 1.2, tint `1 0.40 0.08` | HDR 16, tint `1 0.24 0.03` | same |
| Crystals (`lit_emissive_plus`) | HDR 1.5 | HDR 22 | same |
| Glass (`lit_emissive_transparent`, `colorMap00 $white_diffuse`, falloff 1.0) | HDR 0.4 | HDR 6 | same |
| Steel | `lit_plus` (no glow) | unchanged | same |
| FX light (looping, `tag_origin` host, 18 units up inside the glass) | `tod/fx_tod_inducer_idle`: intensity graph 120, flat | `tod/fx_tod_inducer_on`: intensity 1500 × curve 0.3 → 1.0 → 0.3 over a 1 s life | share/raw/fx/tod/fx_tod_inducer_{idle,on}.efx |

How the script drives it (src: scripts/zm/zm_tod2_cybercity/_tod_rampage.gsc:294-374):
- `tell_apply()` is **the one owner** of the visual state. It is idempotent and is called in the same frame as the toggle, so the tell never waits on a poll.
- `glow_set( on )` deletes the old FX host, `SetModel`s the ON or OFF model, spawns a new `tag_origin` host and server-`PlayFXOnTag`s the matching loop. There is no server StopFX for a tag-played loop, so deleting the host is how the effect stops.
- **The pulse lives in the effect's own light curve, not in a script timer.**
- Lesson recorded with it: "When a BO6 prop looks dead in BO3, the missing sheets are the first suspect, not the lighting." The first port had dropped the donor's emission maps [COMMUNITY] (project record) (src: CLAUDE.md v18.99j).
- Two notes. The inducer FX has the same 200 ms / 1000 ms overlap as the perk glows, which by arithmetic would flatten the designed pulse [INFERRED]; the user approved the look as it is, so any change must be an A/B. And `glow_set` spawns the host and plays in the same frame, while the teleporter code waits two server frames first (docs/143); the project's records disagree on whether same-frame is safe [COMMUNITY] (project record).
- (The `_tod_rampage.gsc` comment "THERE IS NO LIT TWIN, deliberately" at :121 is stale; v18.99j added the twin.)

### 10.2 The heavenly altar

`tod_heavenly_altar` is a script_model placed by `station_spawn` at the base, the four breathers and the crown (src: scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc:7732-7830). Material `mtl_tod_altar`: `lit_emissive_advanced_fullspec`, HDR 8, spec amount 0.2, spec tint 0.25, `glossRangeMax 6`, `reflectionProbeAmount 0.15`; wings `lit_emissive_transparent` at HDR 3 [VERIFIED] (src: source_data/tod_heavenly_altar.gdt). It is **always glowing**: no power link, no FX light, only a looping aura sound [VERIFIED].

History worth keeping: the user rejected an all-matte pass (zero specular, zero probe) because it flattened the exterior. The rule since then is: to reduce gloss, **lower** it; never disable reflections [COMMUNITY] (project record) (src: CLAUDE.md 2026-09-16 entries). Also, a material-slot diagnosis ("the unlit technique reads colorMap") was later disproved by the user's screenshots; do not cite it as a cause [COMMUNITY] (project record).

Because the altars stand at fixed spots, a baked light or a `PROBE_ONLY` light could make each one light its alcove, which its emissive alone does not [INFERRED].

### 10.3 Teleporter, cyber zombies, zombie eyes

- `tod_teleporter`: `lit_emissive_advanced_fullspec`, HDR 6 [VERIFIED] (src: source_data/tod_teleporter.gdt). Its charge/release/ready effects carry their own FX lights; see [04](04_fx_lights.md) for their loop timings.
- Cyber zombies: `lit_emissive_advanced_fullspec`, emission normalised to HDR 6, with "brighter eye cores" [VERIFIED] (src: source_data/tod_cyber_roster.gdt; CLAUDE.md). Glowing parts on zombies are the cheapest way to show them coming in the dark [INFERRED].
- Stock zombie eyes are a client FX on the eye bone, overridable map-wide with `level._override_eye_fx` or per zombie with `self._eyeglow_fx_override` [VERIFIED] (src: share/raw/scripts/zm/_zm.csc:456-470). A readability lever for a dark map ([09](09_design_and_inspiration.md)).

---

## 11. TOD II's all-emissive world

### 11.1 The facts

Every visible brush face in `map_source/zm/zm_tod2_cybercity.map` uses an emissive-class material: 66,402 faces at the audit, 66,390 in the `.map` regenerated 2026-09-24 00:18. The count moves with every generator run; the conclusion does not [VERIFIED]. The rest are tool, clip, trigger, volume and sky faces. Current census:

| Group | Faces | HDR Scale | Emissive map |
|---|---|---|---|
| vertigo plain colours `mwiii_vertigo_retro_synth_<colour>` | 32,296 | 15 | `i_mwiii_vertigo_retro_synth_e`: black with a thin grid line. Measured about 92% pure black pixels, mean luminance 0.048. |
| vertigo `_tinted` | 21,830 | 10 | `i_mwiii_vertigo_retro_synth_tinted_e`: dark-grey fill (~0.2) with brighter edges, no black pixels, mean 0.253 |
| vertigo `_tinted_edge` | 10,770 | 5 | same tinted map |
| `tod_door_*` (matte clones, spec/probe 0) | 1,116 | 5 | tinted map |
| `tod_hall_*` (spire trial halls) | 354 | 4 | their own `tod_hall_*_e` maps |
| vertigo `_pap` (`lit_emissive_scroll_plus`, scroll 0.2/0.1) | 24 | 10 | its own `_pap_e` |

All are `lit_emissive_advanced` except the 24 `_pap` faces [VERIFIED] (src: face-material census of the `.map`; emox_mwiii_vertigo_assets.gdt; source_data/tod_materials.gdt; the emissive-map measurements come from the two texture sources in MODTOOLS/texture_assets/_zm_synth_escape). Every opaque vertigo material except `_pap` is also a white, glossy mirror: `colorMap $white_diffuse`, `specColorMap $white_specular`, `glossRangeMax` 15–16, `reflectionProbeAmount 1`, no normal map [VERIFIED]. The `tod_hall_*` clones keep the same lit layer; the `tod_door_*` clones zero gloss, spec amount and probe amount [VERIFIED] (src: source_data/tod_materials.gdt). The pack ships an unlit twin, `mwiii_vertigo_retro_synth_off` (HDR 0, tint 0 0 0, still a white mirror), used on **zero** faces [VERIFIED]. No world face uses a `*_script` material, so no script can drive the world's glow [VERIFIED]. The only flicker-capable world material is `_pap` (24 faces, `lit_emissive_scroll_plus` at the default flicker range 0–1); whether it visibly flickers is [TEST] ([§7.1](#71-material-flicker)).

### 11.2 What it means for a dark map

1. **About half the faces glow across their whole surface, at a constant level.** The tinted families (~33,700 faces with the doors: `_tinted` on stair treads and the core's band rings, `_tinted_edge` on landings, breather floors, the terrace and the causeway deck; `dark_blue_tinted` alone is 13,602 faces) glow the same with or without lights, states or power (src: tools/lint_tod_geometry.js palette comment; face census). No lighting state or power flip dims an emissive [INFERRED]. These set a floor on how dark the tower can get.
2. **The other half are mostly dark tiles**: only their thin grid lines glow. Their look comes mostly from the lit layer, which is a white mirror, so it is set by lights, reflection probes and the sky [INFERRED]. Making the map darker there means fewer or dimmer lights, fitted probes and a darker sky ([01](01_lights.md), [05](05_sun_sky_exposure_fog.md), [06](06_reflections_probes.md)), not changing the emissive.
3. **The world cannot "turn on" at power.** World faces cannot change at runtime ([§8](#8-switching-a-glow-on-and-off)). A power-on reveal has to come from lights that switch ([02](02_power_and_states.md)) and from glowing **entities**.
4. **Brightness against exposure:** the grid lines at 15 run hot compared with the 2^EV value (8–11 at EV 3–3.5), and the filled faces at 10 and 5 are about right to dim [INFERRED]. On a darker map, where the eye adapts to less, the same values will read brighter relative to their surroundings [INFERRED].
5. **Mirrors multiply whatever light exists.** In a dark map that gives wet-look highlights, a feature for neon, but it also lifts overall brightness. The door slabs were already cloned to matte for exactly this reason (smeared skyline reflections) [COMMUNITY] (project record) (src: tools/gen_tod_door_materials.js header; CLAUDE.md v18.99g).

### 11.3 A note on Glass Tower

The map the user admires is almost certainly GLASS TOWER[HARD] by vuflub_ (Steam Workshop item 3801980290). Its screenshots show saturated magenta/violet emissive edge trim on a tower standing in a void, mirror-like floors and faces that repeat a sunset/space sky, a water plane with a sun glint, and heavy bloom [INFERRED] (from the author's screenshots; nothing published describes its lighting) (src: https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290). That is the same family as our vertigo look: glow from trim, most of the rest from the sky and reflections, not from many placed lights. It is an open void with no dark interiors and no power-on moment, so it does not solve our problems. The full analysis is in [09](09_design_and_inspiration.md).

---

## 12. Recipes

Common rules for every recipe in TOD II: new materials go in a **map-owned GDT** (repo `source_data/`, installed into the private workspace `C:\BO3Tools\TOD2Cybercity` by the guarded sync), never the shared Mod Tools root (docs/154). Keep material names short: the project caps them at 32 characters, because names over 63 are truncated and silently replaced with a default [COMMUNITY] (project record, CLAUDE.md v18.99h). Any new material on a **brush** must be added to `tools/lint_tod_geometry.js` `MATERIALS`, or the build fails. Every material, model or light change is a **full build**. The user judges the look in game; the agent builds and stops (CLAUDE.md). Full fixture assemblies (with light placement) are in [08](08_fixture_cookbook.md).

### 12.1 Neon sign (always on, lights the wall behind it)

1. **Shape.** A model or a thin brush/mesh plate. Tubes are real geometry, or clearly separate shapes in the texture.
2. **Emissive map (`colorMap00`).** Tube shapes in full-bright colour (or white, if the tint carries the hue). **Pure black everywhere else** (Materials.pdf p.18).
3. **Color Map (`colorMap`).** The dark backing plate and unlit tube glass. Do not leave `$white_diffuse` if the backing should stay dark ([§2.1](#21-what-an-emissive-surface-is-two-layers-added-together)).
4. **Material type.** `lit_emissive` (cheapest) or `lit_emissive_plus` (AO/gloss). Use `_advanced_fullspec` only for a metal backing that needs a spec map.
5. **Brightness.** `colorTint1` = the neon hue. `scaleRGB` start at **8** (EV 3 → 2^3). Double for +1 stop (16 = hot), halve for −1 stop. Set `emissiveIncompetence 1` to match the rest of the map (its effect is undocumented).
6. **Spill light.** A small omni or spot just in front of the sign, in its hue, gated by lighting state if it should follow the power ([01](01_lights.md), [02](02_power_and_states.md)). Or a coloured `PROBE_ONLY` light for bounce with no visible direct light [COMMUNITY] (VerK0's tutorial, via [09](09_design_and_inspiration.md); the key is in [01 §10](01_lights.md#10-bounce-bake_intensity_scale-and-probe_only)). The emissive alone does not light the wall ([§4](#4-does-an-emissive-surface-light-up-the-room)).
7. **Buzz (optional).** Switch to `lit_emissive_scroll`, `flickerSpeed 2`, `flickerPower 3`, `flickerMin 0.9`, `flickerMax 1`. For a failing sign, try min 0.1–0.3 with higher harshness, and pair it with a flickering FX light ([12.6](#126-flickering-glow-a-failing-light)).
8. Full build. Judge brightness in game, never in an editor or Blender preview.

### 12.2 TV, monitor or hologram screen

1. Give the screen its own material, separate from the casing.
2. **Still image:** `lit_emissive`, picture in `colorMap00`, dark `colorMap`, `scaleRGB` 4–10 (the Winslow monitor uses 10).
3. **Animated:** `lit_emissive_scroll` with a sprite sheet: `uvMotionToggle1 1`, `rowCount`, `columnCount`, `imageTime`. For scanlines or scrolling data use `uvMotionToggle1 0` and Scroll (U, V). Layered holograms: `_2layer` / `_3layer`.
4. CRT feel: `flickerMin 0.9`, `flickerMax 1`.
5. Use a `_transparent` variant only if the scene must show through (a hologram); transparency is expensive (Materials.pdf).
6. Treat `lit_emissive_mp4` as an experiment, not a recipe: it needs a server `VideoPrime` / `VideoStart` call and a movie the map can load, and neither has been tried in a usermap here ([§7.3](#73-video-on-a-surface)) [TEST].
7. Glow on faces in front of the screen: a weak omni just in front, in the screen's average colour, small radius and low stops. Tune in game.

### 12.3 LED strip, edge line or trim

1. A thin brush or mesh strip, slightly proud of the wall. **Never coplanar** with another material (z-fighting; `node tools/audit_hidden_faces.js` flags coplanar two-material faces).
2. The vertigo pack is a ready library: plain `<colour>` 15 (grid), `_tinted` 10, `_tinted_edge` 5. `_tinted_edge` exists only for blue, green, orange, red and yellow; an invented name is silently substituted (CLAUDE.md). These are mirrors: for a matte strip, clone with lower `glossRangeMax` / `reflectionProbeAmount`, as `tools/gen_tod_door_materials.js` does for `tod_door_*`.
3. A strip that must turn on at power has to be an **entity** (`script_brushmodel` or `script_model`) with option A, B or C from [§8](#8-switching-a-glow-on-and-off). A world brush cannot switch.
4. To light along the strip: omnis spaced along it, or one omni stretched with `bulbLength` ("Controls the length of the light bulb of an area light", bin/t7.def.json) [VERIFIED] (the key); its use for neon tubes is [COMMUNITY] ([01 §11](01_lights.md#11-area-lights-bulblength)). Or accept it as a visual line only.
5. Contrast carries the read ([§3.4](#34-glow-reads-by-contrast)).

### 12.4 Lit window at night

1. **Cheapest:** an opaque plate inset behind the frame, `lit_emissive`, with a painted lit interior or a warm gradient in `colorMap00`, black `colorMap`, HDR 4–8 (a warm interior around EV 2–3).
2. **Treyarch's way for a translucent pane:** `lit_backlit` / `lit_backlit_plus` (opaque; "they will naturally let the light shine through") with a real light **behind** it, so switching the light switches the window (Materials.pdf p.17). `lit_transparent_backlit*` only if the pane must be see-through.
3. Avoid `lit_emissive_transparent` unless real interior geometry sits behind it.
4. Light spilling out onto the street or stair: a spot aimed outward through the window, or an omni just inside.
5. TOD II example: each Vault window niche already has a red `_tinted_edge` back panel ("the lit red panel the zombie stands against") and a red r220 omni inside it (src: tools/gen_tower_map.js:1827, 2788, 7330). That is the "emergency glow" version of this recipe.

### 12.5 Lamp: bulb, shade, and a street-lamp head

The Giant's recipe (src: MODTOOLS/map_source/_prefabs/zm/zm_giant/geo/zm_giant_light_cage_03.map; zm_giant_light.map):

1. **Models:** shade/cage, socket and bulb are separate meshes (`p7_zm_der_light_shade`, `p7_zm_der_light_socket_02`, `p7_zm_der_light_bulb_small`) [VERIFIED].
2. **Bulb material:** emissive, warm tint, HDR about 8–16. Treyarch's own `_on` lamp material is `lit_emissive` at 8 [VERIFIED].
3. **Shade:** `lit_backlit` (opaque lampshade shader), with the thickness/mask map blocking light where wires or bars are [INFERRED] (mapping, §6).
4. **Bulb light:** a tiny ClientSide `PRIMARY_OMNI` at the bulb: radius 15, a warm colour such as `1 0.749 0.451`, `PRIMARY_NOSHADOWMAP 1`. The Giant often stacks **two** such omnis on one bulb: one on in Radiant States 1, 3, 4 (`1011`) and one on in Radiant States 2, 3, 4 (`0111`). 16 of its 25 radius-15 `1011` bulb omnis have a `0111` twin within 8 units. In 8 of those 16 pairs the `1011` light is one stop brighter (for example stops 5.64 vs 4.64); in the other 8 the two are equal or nearly so [VERIFIED] (survey of zm_giant_light.map). Radiant State 2 is The Giant's `power_off` state, so where the pair differs, the bulb is one stop brighter after power [INFERRED] (from the state mapping, [02 §2](02_power_and_states.md#2-radiant-state-n-and-script-state-n)). The Giant's non-probe omnis are mostly bulbs: median radius 20, middle half of stops 4.6–6.6 [VERIFIED] (survey of zm_giant_light.map).
5. **Pool light:** a separate `PRIMARY_SPOT` throws the pool. Giant non-probe spots: median radius 193 (middle half 136–300), median stops 7.97 (middle half 6–10) [VERIFIED] (survey of zm_giant_light.map). **A street lamp is this spot aimed down at the street**, under a lamp head whose lens is emissive or backlit. Shadows only for hero lamps (budget; [01](01_lights.md)).
6. **Power:** put the lights in the right lighting states or a named Radiant exploder, and swap the bulb/shade model to an `_on` twin at power (client `SetModel` like `zm_giant_fx.csc::light_model_swap`, or server `SetModel` on a script_model).
7. **Flicker:** replace the static bulb omni with an FX light with an animated intensity curve, and optionally use a scroll-emissive bulb with a subtle flicker ([12.6](#126-flickering-glow-a-failing-light)).
8. A community tip: one emissive bulb costs less than a second light entity, so do not add a light only to make the bulb itself look lit [COMMUNITY] (VerK0, via [09](09_design_and_inspiration.md)).

### 12.6 Flickering glow (a failing light)

1. **Surface:** `lit_emissive_scroll*`. `flickerSpeed` for rate, `flickerPower` for harshness (higher = snappier), `flickerMin/Max` 0.1–1 for dramatic or 0.9–1 for subtle, `flickerSeedU/V` to desync copies. Leave `flickerLookupMap` on `i_generic_lookup` (semantic `revealMap`).
2. **Light:** an FX light. In Radiant: FX → New effect → element Type = Dynamic Light; set Intensity/Radius in Visuals → Color; draw the flicker in the FX Graph intensity curve; Generation Looping with **lifetime min = max = interval** (FX_Lights.pdf). Start from stock `light/fx_light_yellow_flicker2` (a blackout flicker) or `light/fx_light_fire_flicker_noshad_small` (cheap, unshadowed). Details: [04](04_fx_lights.md).
3. **Placement:** a Radiant `fx` entity (`fxstate1..4` to gate by state) or script-played on a `tag_origin` host. Our proven lanes are a clientfield → client `PlayFXOnTag`, and a server `PlayFXOnTag` of a **looping** effect on a host.
4. **Shadows:** FX lights are "either Always live, or Off", so use `PRIMARY_NOSHADOWMAP 1` unless it is one hero light (FX_Lights.pdf p.2).

### 12.7 Perk machine: dark before power, glowing after

This is how TOD II already works. Use it for any new machine.

1. **Two models.** `<machine>` (off) and `<machine>_on`: the same mesh, with an xmodel `skinOverride` listing `old_material new_material_on`, one pair per line (deffiles/xmodel.awi:379; source_data/tod_bo6_inducer.gdt:449 shows the stored form). The `_on` materials raise `scaleRGB` by roughly 3–4 stops and can deepen `colorTint1`. Off materials at HDR ≈1–2 give a "dead but not black" idle (the inducer's idle values, which the user approved as its dim-lamp look [COMMUNITY] (project record)).
2. **Register them.** After the perk registers, set `level.machine_assets[specialty].off_model` / `.on_model`, and re-stamp machines already spawned, because stock `SetModel( off_model )` has already run (`_tod_perk_lights.gsc::bo7_machine_assets_pass` and `bo7_stamp_sweep`). Stock `perk_machine_think` then swaps to `on_model` itself when the perk's `<alias>_on` notify fires (_zm_perks.gsc:113-161).
3. **Aura + real light.** At `power_on`, set a scriptmover clientfield on the machine. In the CSC callback: `self util::waittill_dobj( localClientNum );` then `PlayFXOnTag( localClientNum, <glow FX that contains a dynamicLight2>, self, "tag_origin" )`, stopping the previous handle first (`_tod_perk_lights.csc`). Register with `!CF_CALLBACK_ZERO_ON_NEW_ENT` for late joiners. Keep the approach rekick. For a new glow effect, set the light element's interval equal to its lifetime ([04](04_fx_lights.md)).
4. **Stock extras (optional).** For a machine that never moves: Radiant lights at the machine in a named exploder fired at power (`exploder::exploder( "my_perk_lgts" )`, as Quick Revive does), or lights gated by lighting state. Our scattered machines move, so they use the FX light that rides with them ([§9.4](#94-why-an-fx-light-is-the-right-lane-for-our-machines)). If you rely on stock's client flicker-on, the map must send the client `ZPO` notify at power ([§9.1](#91-how-stock-bo3-perk-machines-turn-on) point 3) [INFERRED].
5. **Solo Quick Revive** is powered from spawn in stock; OR the trigger's own `.power_on` into any "is it powered" check (`bo7_stamp_sweep`).
6. **Logs:** a dev-gated `[TOD_PERK_GLOW]`-style line at each state edge (power seen, field set, rekick fired) per the project's diagnostics rule (CLAUDE.md). Then build and stop; the user tests.

### 12.8 Device with a dim idle glow and a hot ON pulse (the inducer template)

1. Emissive materials at idle HDR ~1–1.5, plus `_on` twins at ~16–22 with a more saturated tint. `lit_emissive_plus` unless you need a spec map (then `_advanced_fullspec`).
2. `tod_x` / `tod_x_on` xmodels: same `filename`; `_on` has the `skinOverride`.
3. Two looping FX, one `dynamicLight2` each: idle = flat intensity (e.g. graph 120); ON = the pulse baked into the intensity curve (e.g. 1500 × 0.3 → 1.0 → 0.3 over a 1 s life). **Put the pulse in the curve, not in a script timer**, and set interval = lifetime.
4. One owner function: on each change, `SetModel` on/off, delete the old `tag_origin` host, spawn a new one, `PlayFXOnTag` the matching loop. Call it in the same frame as the state flip (`_tod_rampage.gsc::tell_apply` / `glow_set`).
5. Zone line `fx,<path>` + `#precache( "fx", "<path>" )` + `level._effect` entry for each effect. "Miss any one of the three and the device sits there dark with no error" [COMMUNITY] (project record, src: _tod_rampage.gsc:95-99). The zone line is needed for any effect the map itself must pack; an effect that a base-game zone already loads can render without it [COMMUNITY] (project record, [04 §9](04_fx_lights.md#9-playing-fx-from-script)). Vet the effect's source first: some stock `.efx` sources in the Mod Tools are placeholder stubs [VERIFIED], and the project has seen a zoned stub pack as a blank effect [COMMUNITY] (project record) ([04 §17](04_fx_lights.md#17-the-placeholder-stub-trap-and-how-to-vet-an-effect)).

---

## 13. Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| The tower cannot be made dark before power; lights and states barely change it | About half the world faces glow across the whole face (tinted vertigo, HDR 5–10), and world face materials cannot change at runtime | Re-skin large surfaces in non-glowing or dimmer map-owned materials; keep emissive for accents; put switchable glow on entities ([§11](#11-tod-iis-all-emissive-world)) |
| A sign or strip looks lit but the wall and floor around it stay dark | Emissive surfaces are not shown to light anything | Add a Radiant light or an FX light at every source that should light its surroundings ([§4](#4-does-an-emissive-surface-light-up-the-room)) |
| The "black" parts of a glowing floor turn the colour of nearby lights (the olive spawn pool) | The lit layer's Color Map is `$white_diffuse` | Dark Color Map where the surface should stay black, or choose light colours knowing they paint it |
| A glowing prop glows flat all over | `colorMap00` left blank → `$white_diffuse` | Fill the emissive map; black where there is no glow ([§2.4](#24-trap-a-blank-emissive-map-glows-white)) |
| Glowing floors and doors look like smeared mirrors | Vertigo materials: white specular, gloss 15–16, `reflectionProbeAmount 1`, and 144-unit default probe boxes | Matte map-owned clones (as `tod_door_*`); fit probes to rooms ([06](06_reflections_probes.md)) |
| Specular map on an emissive prop has no effect | `lit_emissive_plus` has no specular-map slot | Use `lit_emissive_advanced` or `_advanced_fullspec` |
| Flicker settings do nothing | Flicker fields only work on `lit_emissive_scroll*` (and some decal/specialty types) | Switch to a scroll type, or flicker the FX light instead |
| A scroll or flipbook emissive may flicker when you did not ask for it | Flicker defaults are min 0 / max 1 | Set `flickerMin = flickerMax = 1` on scroll materials that must be steady; check in game [TEST] |
| Stock perk machines do not visibly change at power | Stock off and on models are the same model | Ship a real `_on` model and set `level.machine_assets[spec].on_model`; add an FX light |
| Stock perk prefab lights never turn on | All their lights have `lightingstate1..4 = 0`; only Quick Revive's exploder is fired by stock | Tick states and switch state at power, fire the exploder yourself, or use FX glows ([§9.2](#92-why-my-perk-lights-dont-work)) |
| The stock perk "glow" lights nothing around the machine | `zombie/fx_perk_*_zmb` are sprites with no light element | A glow effect with a `dynamicLight2` (e.g. `acc/light/fx_perk_glow_*`), or Radiant lights |
| A looping glow light looks too bright or its pulse looks mushy | Spawn interval shorter than lifetime overlaps light particles (our 200 / 1000 ms) | Interval = lifetime; A/B in game, because the user approved the current inducer look |
| White halos around bright glow | Engine bloom on very bright pixels | Lower `scaleRGB` or darken the hottest pixels; no per-material bloom control exists |
| New emissive material shows as a default grey/white face | Name over 63 characters (truncated and substituted) or an invented name the linker cannot find | Short names (≤32 in this project), real names only |
| Transparent glow tanks frame rate or sorts badly | Transparency adds overdraw; `nocull` doubles cost | Opaque emissive, alpha-test, or opaque backlit; transparent only if you must see through |
| A decal placed on a glowing surface looks wrong | `lit_emissive*` is forward; deferred decals "only layer properly over other deferred surfaces" (Materials.pdf p.2) [INFERRED] | Bake the detail into the emissive textures, or use `decal_emissive*` |

---

## 14. Open questions and tests

All [TEST]. The consolidated test plan is in [10](10_troubleshooting_limits_history.md).

1. **Does a large emissive surface add bounce light or show in reflections?** Two sealed rooms, emissive floor vs plain dark floor, no lights, full bake, compare in game with `r_bloomEnable 0` ([§4](#4-does-an-emissive-surface-light-up-the-room)).
2. **What does `emissiveIncompetence` ("Use gameplay intensity") do?** Same material at 0 and 1 in areas at different exposure.
3. **What does `emissiveFalloff` (0–128, with `invertFalloff`) do?** A flat panel at 0, 2 and 10, seen head-on and at a grazing angle.
4. **Do scroll materials flicker at the defaults (min 0, max 1)?** One at defaults, one at min = max = 1. The world's 24 `_pap` faces are an existing case to look at.
5. **Does `MapShaderConstant` / `SetShaderConstant` drive a `lit_emissive_script` material on a `script_model`?** Does the GDT's `cg00` correspond to `scriptVector0`?
6. **Do `lightingstate1..4` keys on `misc_model` / `script_model` hide a model per state?** (A no-script off/on model pair would follow.)
7. **Does the stock sprite halo still play on our BO7 machines?** Does the stock client flicker-on run at all without a `ZPO` notify, and if it does, does it play anything at the park structs? A dev log or an in-game look at power-on.
8. **What HDR values do the BO7 `t10_zm_machine_*_on` materials use?** Their GDTs were not found locally.
9. **How strongly does a baked light behind a `lit_backlit` shade show through?**
10. **Does matching interval to lifetime on the perk-glow and inducer light elements restore a visible pulse, and at what brightness?** User-judged A/B.
11. **What does `SetMaterialOverride` accept on an entity?**
12. **Does `VideoStart` play a movie on a `lit_emissive_mp4` surface in a usermap,** and how is the movie packaged? Try it in the control map before promising any "live screen".

---

## For Tower of Doom II

Recommendations only. Nothing here changes code or data. Each item is a full build and a user test.

1. **Decide the glow budget before the light budget.** List what should glow **always** (trims, signs, beacons, the altars), what should glow **only after power** (perk machines, door gates, lounge accents, the teleporter bay: [09](09_design_and_inspiration.md) recommends lighting only what the power plausibly feeds), and what should be **dark**. Only entities can be in the second group.
2. **Take the constant glow floor down where darkness matters.** The tinted vertigo faces (treads, landings and floors; `dark_blue_tinted` alone covers 13,602 faces) are the brightest constant glow. Options, from cheap to thorough: (a) move selected surfaces from `_tinted` (10) to `_tinted_edge` (5) or to dimmer map-owned clones at HDR 2–4; (b) move large surfaces to the plain grid (15, mostly black) and keep the filled faces for accents; (c) map-owned non-emissive or `_off`-style materials for structure. Use the `tools/gen_tod_door_materials.js` pattern (map-owned GDT, drift check). Never edit the shared vertigo GDT. Add every new brush material to `tools/lint_tod_geometry.js`.
3. **Darken the lit layer for surfaces that should stay black.** A map-owned clone with a dark `colorMap` (like the Origins portal's `$black_color`) and lower gloss/probe amount stops every light and the sky from painting the "black" tiles. Lower gloss; do not zero reflections (the altar lesson).
4. **Use a brightness ladder tied to exposure.** If exposure really sits at the SSI's EV 3–3.5 clamp, treat HDR 8–11 as "honest" glow, 4–6 for quiet trims, 16–22 for hero or ON states. Recheck once exposure is actually decided ([05](05_sun_sky_exposure_fog.md)).
5. **Pair every source that should light something with a light.** Lamps and signs at fixed spots: a baked light gated by lighting state, or a coloured `PROBE_ONLY` light for bounce with no visible source. Moving or animated things (the scattered perks, the inducer): FX lights. The altars stand at fixed spots and could each get a small baked light.
6. **Build the power-on reveal from entities.** Lamp heads, signs and strips that switch should be `script_model` / `script_brushmodel` entities using the `_on` skinOverride twin (proven by the inducer) or Hide/Show, plus a light that switches. Stage it floor by floor rather than all at once ([02](02_power_and_states.md)). Watch the gentity budget.
7. **Perk glows: keep the lane, test the timing.** The clientfield → client `PlayFXOnTag` lane with the rekick is right for machines that move. Two A/Bs are worth one build: interval = lifetime on `light_small`, and whether the stock `perk_fx` sprite halo also plays (dev log or look).
8. **Fill in the unknowns cheaply.** Tests 1 and 5 in [§14](#14-open-questions-and-tests) decide whether big emissive surfaces must be treated as light sources, and whether a single script-emissive machine can replace model twins. Both fit in the `Repositories/test+map` control map.
9. **Judge on two graphics configs.** The user's own config disables volumetric lighting, dynamic sun and light shadows, and SSAO. Nothing in that list turns off emissive glow or bloom [INFERRED], but any FX-light shadow or volumetric light will not show in the user's playtests ([09 §7.3](09_design_and_inspiration.md#73-judge-on-two-graphics-configs)).

---

## Sources

Mod Tools root = MODTOOLS (`C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`). Repo paths are relative to the repo root.

**Official Treyarch docs (MODTOOLS/docs_modtools)**
- Materials.pdf: p.2 (deferred decals), p.10 (transparency, alpha test, nocull cost), p.16–17 (Special Cases: Lit Backlit "lampshade shaders", Backlight Mask Map), p.18 (Lit Emissive: "computer screens"; Emissive Map, Depth, HDR Scale = 2^EV), p.23–24 (Effect Lit Emissive intensity scale, Physically Based Emissive)
- FX_Lights.pdf (FX lights for flicker/animation; loop rule; Always-or-Off shadows)
- SunSky_Light_SetUp.pdf (sky material as a light; skyStops rebake)
- Probe/Reflection_Probes.pdf (GI bounce from probe captures)
- Mini_Map_Setup.pdf (`r_bloomEnable 0`, `r_exposureTweak`, `r_exposureValue`)
- bo3_scriptapifunctions.htm (MapShaderConstant, SetShaderConstant, SetMaterialOverride, ClearMaterialOverride, SetLightingState, SetModel, VideoPrime, VideoStart, VideoStop, VideoPause, VideoUnpause)

**Stock definitions and data (MODTOOLS)**
- share/raw/techsetdefs_stable: include/emissive_base, flicker_base, flipbook_base, lit_base_basic, lit_base_mid, lit_base; geometry/lit_emissive*, lit_backlit*, lit_emissive_scroll, lit_emissive_script, lit_emissive_mp4; geometry_plus/lit_emissive_plus, lit_emissive_scroll_plus, lit_backlit_plus; geometry_advanced/lit_emissive_advanced(_fullspec); decal/decal_emissive*; specialty/emissive_passthrough*; renderFlags.techsetdef
- deffiles/material.awi (lines 798, 802, 803, 805, 1001–1017, 1061, 1268, 1543); deffiles/xmodel.awi:379
- bin/t7.def.json (light `bulbLength`, `PROBE_ONLY`, `stops`, `bake_intensity_scale`; model `lightingstate1..4`; `vbloom_box` (`lvi`, `mix`, `LIGHTSTATE_n`); `pbg_box` (`USE_BLOOM`, `bloom_lvi`, `bloom_mix`); worldspawn (no `bloom` key); `info_corona`)
- share/raw/scripts/zm: _zm_perks.gsc (113-161, 280-318, 1723), _zm_perks.csc (193-259), _zm_perk_*.gsh, _zm_perk_juggernaut.csc (32-38), _zm_perk_quick_revive.gsc (163-167, 185, 791), _zm_perk_electric_cherry.gsc (33-34), _zm_power.gsc (723-737), zm_usermap.gsc (446-455), zm_usermap.csc (84, 107-116), zm_giant.gsc (427-428, 571, 573), zm_giant_fx.csc (69-71, 184-197), _zm_perk_random.csc (104-367), _zm.csc (353-396 ZPO / power_on, 456-470 eye FX); shared/shaderanim_shared.csc (49-68)
- share/raw/fx: zombie/fx_perk_*_zmb.efx, zombie/fx_perk_*_factory_zmb.efx, light/fx_light_yellow_flicker2.efx, light/fx_light_fire_flicker_noshad_small.efx, acc/light/fx_perk_glow_*.efx
- map_source/_prefabs/zm/zm_core/vending_*_struct.map and vending_weapon_upgrade_spawnable.map; map_source/_prefabs/zm/zm_giant/zm_giant_light.map, geo/zm_giant_light_cage_03.map; map_source/zm/zm_giant.map
- source_data/_emox/emox_mwiii_vertigo_assets.gdt; p7_zm_ori_light_warning_metal.gdt; p7_zm_ori_tomb_portal_screen.gdt; p7_zm_gen_maxis_essence.gdt; acc_t7_props_pilot.gdt; acc_west_electric_cherry.gdt; night_t5_thundergun.gdt; ssi.gdt (`default_night`)
- texture_assets/_zm_synth_escape/ximage_70da2c37da534be.png and ximage_3581b748b3b29cd_e.png (the two vertigo emissive maps, measured)

**This repo**
- scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc, _tod_perk_lights.csc, _tod_rampage.gsc, _tod_upgrades.gsc (7732-7830)
- source_data/tod_bo6_inducer.gdt, tod_heavenly_altar.gdt, tod_teleporter.gdt, tod_cyber_roster.gdt, tod_materials.gdt, tod_skybox.gdt
- share/raw/fx/acc/light/fx_perk_glow_*.efx, share/raw/fx/tod/fx_tod_inducer_{idle,on}.efx
- map_source/zm/zm_tod2_cybercity.map (face census, 2026-09-24 regeneration); zone_source/zm_tod2_cybercity.zone
- scripts/zm/zm_tod2_cybercity/_tod_perk_scatter.gsc (the move and re-glow after a reshuffle)
- tools/gen_tower_map.js (1827, 2788, 7166-7215, 7330), tools/gen_tod_door_materials.js, tools/lint_tod_geometry.js (MATERIALS table, palette comment)
- CLAUDE.md (inducer v18.99i–k, altar 2026-09-16 entries, door matte clones v18.99g, sky bloom v18.97); CHANGELOG.md (v17.28, v17.32); docs/104, docs/143, docs/154, docs/BO3_MAPMAKING_KB.md

**Other project and community**
- Map One repo: abandoned_cyber_city_zombies/docs/20_atmosphere_and_materials.md §12.2
- https://forum.modme.co/wiki/threads/1565.html (lit_emissive_scroll works; mp4 shows a still image)
- https://forum.modme.co/wiki/threads/1942.html (scroll_transparent link error, unresolved)
- https://forum.modme.co/wiki/threads/1950.html (perk lights via lighting states + set_lighting_state at power)
- https://www.ugx-mods.com/forum/mapping/92/perk-lighting-effects-fix-video-tutorial/13226/ (perk prefab light fix)
- https://steamcommunity.com/app/455130/discussions/0/2333276539589995175/ and https://steamcommunity.com/app/455130/discussions/0/2592234299570231550/ (perk light fixes; default_day sun volume)
- https://forum.modme.co/wiki/threads/2118.html (power-on hitch from perk hint-string registration)
- https://www.youtube.com/watch?v=VPT3TJzbQPc (VerK0, "Lighting Tutorial" Part 5: lights; emissive bulb vs a second light; PROBE_ONLY coloured bounce), details in [09](09_design_and_inspiration.md)
- https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290 (GLASS TOWER[HARD] by vuflub_; author screenshots)
