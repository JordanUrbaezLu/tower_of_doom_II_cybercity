# 02 — Power, lighting states and switching lights

**In short.** A BO3 map can hold up to four global lighting setups, called lighting states (which lights exist, plus a sun/sky setting for each), and script picks one; the whole map swaps to it at once, per player. Radiant numbers the states 1-4 but script counts 0-3, and by all the stock evidence a stock usermap boots into script state 1, which shows the lights ticked for Radiant State 2. Stock power changes no lighting at all: a map that wants "the lights come on at power" must author its lights per state and make the call itself, as Treyarch's The Giant does. For anything smaller than the whole map (one floor, one door, one lamp) use named exploder groups, FX lights driven by a clientfield, or switchable glow on entities, not states. Tower of Doom II never changes its state today, every one of its 344 lights is authored ON in the state it boots into, and THE FALL now turns the power on in the first seconds anyway, so power changes none of its lights; that conclusion is inferred and has not been tested in game.

**Read this when…** you want lights, glow or mood to change during a match (power-on, a door opening, an alarm, a finale, a floor "coming alive"), or when a light is on or off when it should not be.

**Contents**
1. [The mental model](#1-the-mental-model)
2. [Radiant State N and script state n](#2-radiant-state-n-and-script-state-n)
3. [The boot state, spawns and per-player state](#3-the-boot-state-spawns-and-per-player-state)
4. [The two working conventions](#4-the-two-working-conventions)
5. [The sun volume in each state](#5-the-sun-volume-in-each-state)
6. [Everything else a state can switch](#6-everything-else-a-state-can-switch)
7. [What each extra state costs](#7-what-each-extra-state-costs)
8. [Transitions: instant or blended](#8-transitions-instant-or-blended)
9. [Exploders: named light groups](#9-exploders-named-light-groups)
10. [Scriptable server lights](#10-scriptable-server-lights)
11. [Fog, exposure, LUT and grade banks as mood switches](#11-fog-exposure-lut-and-grade-banks-as-mood-switches)
12. [Switching emissive glow](#12-switching-emissive-glow)
13. [How stock perk machines power on](#13-how-stock-perk-machines-power-on)
14. [Architecture: choosing a mechanism](#14-architecture-choosing-a-mechanism)
15. [Tower of Doom II today: the diagnosis](#15-tower-of-doom-ii-today-the-diagnosis)
16. [Minimal test plan in the control map](#16-minimal-test-plan-in-the-control-map)
17. [For Tower of Doom II](#for-tower-of-doom-ii)
18. [Sources](#sources)

Conventions used below:
- **MODTOOLS** is `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`; paths under it are written relative to it.
- **Map One** is the user's first map, `c:/Users/jorda/Repositories/abandoned_cyber_city_zombies`.
- **Radiant State N** means the light key `lightingstateN` (N = 1..4), the numbering Radiant shows. **Script state n** means the argument of `util::set_lighting_state(n)` / `SetLightingState(n)`.
- Tags: [VERIFIED] read in an official Treyarch doc, stock script, stock data file or the engine API list; [COMMUNITY] forum, tutorial, video or another mapper (including Map One's own recorded observations); [INFERRED] reasoned, not seen; [TEST] needs an in-game test to settle. Nothing in this chapter was tested in game.

---

## 1. The mental model

**Plain version.** Think of a lighting state as one complete "photograph" of how the map is lit: which lamps exist, what the sun and sky are, how bright the bounced light is, and which grade and fog volumes apply. Radiant keeps up to four of these photographs, and when it bakes the map it most likely computes the bounce light once per photograph [INFERRED, section 7]. During a match, script says "show photograph 2 now", and every lamp, the sun, the bounce light and the grade switch together; there is no fade argument, so the switch is instant [VERIFIED API; the bounce/grade part INFERRED].

**A zombies example.** In The Giant, before power the lamps glow dimly. When a player throws the switch, the map changes to its "powered" state: many fixtures come back about one stop (roughly twice) brighter, extra lamps turn on, and the colour-grade boxes switch on. Treyarch built about 58 fixtures as pairs of lights: a dim copy that exists only in the pre-power state and a brighter copy at the same spot that exists only in the powered state [VERIFIED data, parsed from `map_source/_prefabs/zm/zm_giant/zm_giant_light.map`; the "one stop" is the median of the pairs; what a stop means is in [01_lights.md](01_lights.md)].

**Why "the whole tower lights up".** A state is global. There is no "state 2 on floor 10 only". If every light in a map is authored as a "powered" light and script flips the state at power, then everything changes at once, which is exactly the effect the user is worried about. Per-area lighting has to come from other mechanisms (sections 9-12) [VERIFIED: four states, one active per player; src: docs_modtools/Lighting_Parameters.pdf p.10; `SetLightingState` takes one number, bo3_scriptapifunctions.htm].

**What a state carries** [VERIFIED keys in bin/t7.def.json unless marked]:

| Carried by the state | How |
|---|---|
| Placed `light` entities | `lightingstate1..4` checkboxes on each light |
| Radiant-placed `fx` entities (including FX lights) | `fxstate1..4` on each `fx` entity |
| Sun, sky light and SSI exposure | `volume_sun` `ssi1..ssi4` (one SSI per state) |
| Baked probe bounce light and probe exposure | Stored per state in the bake [INFERRED from Radiant field names, section 7] |
| Fog volumes, grade/bloom/LUT/PBG volumes, performance volumes | `LIGHTSTATE_1..4` flags on those volumes |
| Models (`misc_model`, `script_model`, `script_brushmodel`) | `lightingstate1..4` keys exist, but what they do is unproven (section 6) |

**What a state does not do:** switch only part of the map; fade placed lights smoothly (section 8); change emissive (self-glowing) materials [INFERRED, section 12]; stop or start effects that script plays (an FX light's own `dynamicLight2` block carries `lightingstate1..4` keys too, but whether they gate a script-played light is unknown [TEST]); change world brush faces, which carry no entity keys at all [VERIFIED: world brushes belong to `worldspawn`, which has no `lightingstate` keys in bin/t7.def.json].

**The six ways light changes during a match:**

| # | Mechanism | Plain words | Scope | Main section |
|---|---|---|---|---|
| A | Lighting state | Swap the whole baked "photograph" | Whole map, per player | 2-8 |
| B | Radiant exploder | A named group of placed lights/FX that script plays, stops or kills | One named group | 9 |
| C | Scriptable server light | One placed light that server script can dim, recolour or shrink | One light | 10 |
| D | FX light | A light inside an effect (`.efx`), played anywhere by script | One effect | [04_fx_lights.md](04_fx_lights.md) |
| E | Emissive switching / model swap | Make a lamp or sign *look* on or off | One entity | 12, [03_glow_and_perks.md](03_glow_and_perks.md) |
| F | Banks and vision | Whole-screen mood per client: fog, exposure, LUT, grade | Per client | 11 |

Of these six, only placed lights are known to feed the baked bounce light: A yes (the GI bake reads placed lights; `bake_intensity_scale` "Adjusts the brightness of a light for GI baking", bin/t7.def.json [VERIFIED def text]), B and C possibly (whether an exploder light's bounce is baked is unknown, section 9.5). D and E are most likely live only [INFERRED: no doc says an FX light feeds the bake, and FX-light shadows can only be "Always live, or Off", FX_Lights.pdf p.2; emissive is not a documented light source, see [03_glow_and_perks.md](03_glow_and_perks.md)].

## 2. Radiant State N and script state n

**The rule.** Script state n shows Radiant State n+1. In plain words: the number you type in script is one less than the checkbox number on the light. A light with only `lightingstate2` ticked is on when script has called `set_lighting_state( 1 )`.

| Script call | Shows lights ticked | Stock use |
|---|---|---|
| `set_lighting_state( 0 )` | `lightingstate1` (Radiant State 1) | The Giant's power-on call |
| `set_lighting_state( 1 )` | `lightingstate2` (Radiant State 2) | `zm_usermap::main()`, the boot state of every usermap |
| `set_lighting_state( 2 )` | `lightingstate3` | none in stock ZM |
| `set_lighting_state( 3 )` | `lightingstate4` | none in stock ZM |

There is no `lightingstate0` key anywhere in bin/t7.def.json or in Radiant's strings [VERIFIED].

**Confidence: [INFERRED], strongly supported.** No Treyarch document states the mapping. It is the only reading consistent with the stock data:

1. The Giant's light prefab names Radiant State 2 `"state_alias_2" "power_off"` (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map worldspawn). Note that this alias is on the light prefab's worldspawn; the parent `zm_giant.map` worldspawn keeps the default names [VERIFIED].
2. The Giant boots through `zm_usermap::main()`, which calls `level util::set_lighting_state( 1 )` (src: share/raw/scripts/zm/zm_giant.gsc:132, share/raw/scripts/zm/zm_usermap.gsc:110), and it calls `level util::set_lighting_state( 0 )` inside `power_electric_switch()` after the `power_on` flag (src: zm_giant.gsc:571) [VERIFIED].
3. 119 of The Giant's 543 lights are `(1,0,1,1)`, off only in Radiant State 2. About 57-58 dim State-2-only lights have a brighter State-1-only twin within a few units (two independent counts), median about +1 stop brighter [VERIFIED counts]. That only makes sense if script 1 = Radiant 2 = "power_off" and script 0 = Radiant 1 = powered.
4. Map One recorded the same mapping ("GSC `set_lighting_state(N)` displays Radiant State N+1") while fixing a power flip that did nothing, split its lights by state to match, and its user then saw the map go "truly dark until the power switch is flipped" (src: Map One CHANGELOG.md, entries of 2026-06-19 and 2026-06-21) [COMMUNITY].
5. Community threads say the same: "1-4 in Radiant, & 0-3 in Scripting" (src: https://forum.modme.co/wiki/threads/1077.html) [COMMUNITY].

**Do not cite the engine API note as proof.** `SetLightingState( <new light state> )` says "Lighting state defaults to 1 at start of game", with the example `SetLightingState( 2 )` (src: docs_modtools/bo3_scriptapifunctions.htm). That sentence does not say which numbering it uses [VERIFIED text; its meaning is ambiguous].

**Dissent.** A few community posts use `set_lighting_state(2)` after power or say the map "starts in state 1" (modme threads 571 and 1950; UGX thread 13041) [COMMUNITY]. A post using (2) works only because those lights are ticked in States 2-4. "Starts in state 1" is only true after the map's own script calls `set_lighting_state(0)` [INFERRED from the stock code above].

## 3. The boot state, spawns and per-player state

**Boot.** `zm_usermap::main()` runs `level util::set_lighting_state( 1 )` (src: share/raw/scripts/zm/zm_usermap.gsc:110) [VERIFIED]. Every map built from the stock template calls `zm_usermap::main()`, and the template script itself contains no lighting call [VERIFIED: rex/templates/ZM Mod Level/usermaps/template/scripts/zm/template.gsc]. So **every usermap runs in Radiant State 2 unless its own script changes it** [INFERRED from the mapping].

**How the utility works** (src: share/raw/scripts/shared/util_shared.gsc:2968-3005) [VERIFIED]:

```
function set_lighting_state( n_state )        // CallOn: level or player
{
    if ( isdefined( n_state ) ) self.lighting_state = n_state;
    else                        self.lighting_state = level.lighting_state;
    ...
    if ( self == level )        foreach( player in level.activePlayers ) player set_lighting_state( level.lighting_state );
    else if ( IsPlayer( self ) ) self SetLightingState( self.lighting_state );
}
```

- Called on `level`, it stores `level.lighting_state` and applies it to each player in `level.activePlayers`, which holds only alive players whose session state is "playing" (src: share/raw/scripts/zm/gametypes/_globallogic.gsc:1764-1812) [VERIFIED].
- **Every spawn re-applies it.** `spawnPlayer()` ends with `self util::set_lighting_state();` with no argument, which copies `level.lighting_state` to that player (src: share/raw/scripts/zm/gametypes/_globallogic_spawn.gsc:501) [VERIFIED]. Spectator respawns, the way a dead player (or one who joined mid-round) comes back, call `level.spawnPlayer`, which is that same `globallogic_spawn::spawnPlayer` (src: share/raw/scripts/zm/_zm.gsc:3253-3263; share/raw/scripts/zm/gametypes/_globallogic.gsc:258) [VERIFIED]. The utility's own summary says it "handles hot-join" (util_shared.gsc:2970) [VERIFIED text].
- **The state is per player.** The utility calls the engine's `SetLightingState(n)` on each player (`self SetLightingState( self.lighting_state )`, util_shared.gsc:3000) [VERIFIED code], although the API page lists `SetLightingState` without a call-on entity; `<player> GetLightingState()` reads the state back (src: bo3_scriptapifunctions.htm) [VERIFIED]. You can give one player a different state with `player util::set_lighting_state( k )`, but their next spawn resets it to the level value [VERIFIED code path]. To keep a per-player state, re-apply it in an on-spawned callback [INFERRED].
- **Streaming ahead of a switch.** `CreateStreamerHint( <origin>, <factor>, [lightingState] )` creates a streamer hint that can stream a given lighting state, and `SetLightingOnly( true )` makes a hint stream lighting data only (src: bo3_scriptapifunctions.htm) [VERIFIED API]. Using one before a state switch or teleport to avoid a pop is [INFERRED]; no stock usage was checked.

**Stock power never touches lighting.** The stock switch (`use_elec_switch`) ends in `zm_power::turn_power_on_and_open_doors()`, which sets the `power_on` flag, sets the world clientfield `zombie_power_on` to 0 and opens electric doors (src: share/raw/scripts/zm/_zm_power.gsc:723-760) [VERIFIED]. `_zm_power.gsc` contains no lighting-state, exploder or vision call [VERIFIED]. A map must author its own power-on lighting.

**Client-side gotcha.** The client handler for `zombie_power_on` only sends the client notify `"ZPO"` (which becomes the client `"power_on"` notify) when the new value is non-zero (src: share/raw/scripts/zm/_zm.csc:353-370, 390-396) [VERIFIED]. Global power sets the field to 0, its default, so client scripts waiting on the client-side `"power_on"` notify get nothing from stock global power: even if a callback fires, a 0 sends no `"ZPO"` [VERIFIED code path]. The Giant sends `util::clientNotify( "ZPO" )` itself right after its state call (src: zm_giant.gsc:573), and it is the only stock script that does [VERIFIED grep of share/raw/scripts]. `util::clientNotify` only sends when `level.clientscripts` is true (src: share/raw/scripts/shared/util_shared.gsc:1390-1398) [VERIFIED]; see section 9.5 for what that flag is.

## 4. The two working conventions

Both conventions work. Pick one per map, write it down, and author every light to match.

| | **Giant convention** (Treyarch) | **Map One convention** (template threads, Map One) |
|---|---|---|
| Pre-power runs in | script 1 = Radiant State 2 | script 0 = Radiant State 1 |
| Powered runs in | script 0 = Radiant State 1 | script 1 = Radiant State 2 |
| Startup call | none (`zm_usermap::main()` already sets 1) | `level util::set_lighting_state( 0 );` after `zm_usermap::main()` |
| Power call | `level util::set_lighting_state( 0 );` | `level util::set_lighting_state( 1 );` |
| Evidence | zm_giant.gsc:132, :571; prefab alias `power_off` [VERIFIED] | Map One `CheckForPower()`, scripts/zm/zm_abandoned_cyber_city.gsc:956-973 [COMMUNITY, played] |
| `volume_sun` | `ssi1` and `ssi2` both `zm_factory` [VERIFIED] | `ssi`, `ssi1`, `ssi1_runtime_override`, `ssi2` all `acc_ssi_night_dim80` [VERIFIED map data] |
| Radiant preview default | State 1 = the powered look [INFERRED advantage] | State 1 = the dark look |

**Light masks for each convention** (states 3/4 set deliberately, or copied from the state they should resemble):

| Light class | Giant masks `(1,2,3,4)` | Map One masks | Example |
|---|---|---|---|
| Always on (navigation floor, spawn, hazards) | `1,1,x,x` | `1,1,x,x` | a dim cool pool at every stair turn |
| Pre-power only (emergency, red) | `0,1,x,x` | `1,0,x,x` | a red lamp that dies when power comes on |
| Powered only (fixtures, signs, accents) | `1,0,x,x` | `0,1,x,x` | the room's real ceiling lights |
| Dim/bright twins | dim `0,1`; bright `1,0`; same origin, radius and colour | dim `1,0`; bright `0,1` | Giant median +1 stop between twins [VERIFIED] |

**What the stock data teaches** [VERIFIED counts; the design reading is INFERRED]:
- The Giant is not black before power. 341 of its 543 lights are on pre-power, 435 after. Power (a) brightens paired fixtures by about a stop, (b) adds fixtures and colour indicator lamps, (c) switches its grade boxes (all 15 `pbg_box` volumes are `LIGHTSTATE_1` only).
- Giant light patterns: `1111` ×261, `1011` ×119, `0111` ×55, `0000` ×39, `1000` ×34, other ×35.
- Map One went further: interior rooms "pure black until power", with only the 15 Plaza lights always on as a lit safe-haven spawn (src: Map One CHANGELOG.md, 2026-06-21 entry) [COMMUNITY]. Its first dim pre-power set, even at a tiny intensity, still read "too light" to its user [COMMUNITY].
- A shipped community map, MattFiler's Alien Isolation Zombies, uses all four states (spawn, lights-out, power-on, red alert) and scripts `set_lighting_state` 0-3 for power and alarms. One of its three sun volumes has distinct spawn / lights-out / power-on SSIs; the other two use one SSI for all four states (src: https://github.com/MattFiler/zm_alien_isolation) [COMMUNITY].

**Label the states.** Set worldspawn `state_alias_1..4` (for example `state_alias_2 "power_off"`) so Radiant's state menu names them [VERIFIED key: bin/t7.def.json worldspawn, group STATE_ALIASES; display-only meaning INFERRED]. "Global lighting states can be toggled from the camera window" (src: docs_modtools/Lighting_Parameters.pdf p.10) [VERIFIED], so preview both states there before baking.

## 5. The sun volume in each state

The `volume_sun` holds one set of sun/sky settings per lighting state. "You can have up to 4 lighting states (additional Global Lighting scenarios) that can be accessed & switched through script during run time. Each lighting state has runtime lighting and an optional baked lighting override" (src: docs_modtools/SunSky_Light_SetUp.pdf p.1) [VERIFIED]. Sun, sky and exposure details are in [05_sun_sky_exposure_fog.md](05_sun_sky_exposure_fog.md).

**Keys** (src: bin/t7.def.json `volume_sun`) [VERIFIED]:

| Key | Default | Meaning |
|---|---|---|
| `ssi1` | `default_day` | SSI for Radiant State 1 (group "Light State 1") |
| `ssi2`, `ssi3`, `ssi4` | empty | SSI for States 2-4 |
| `ssi1_runtime_override` .. `ssi4_runtime_override` | empty | "ssi_runtime_override is what will be displayed in game and ssi is what will bake into the reflection probes" (SunSky_Light_SetUp.pdf p.1) |
| `override_reflections` | false | "Use the run-time override SSI in the reflection probe final renders." |
| `transitionTime` | 0 | "Time to transition between sun states." |
| `target` | — | points the global probe at an `info_null` (see [06_reflections_probes.md](06_reflections_probes.md)) |
| `streamLighting` | true | "Stream the lighting data for this volume" |

The bare `ssi` key that the stock template and our generator put on `volume_sun` is not in the definition; it is probably legacy or ignored [INFERRED].

**What the bake records.** The exported `.led` stores a four-entry table, one SSI per state, and **an unset `ssiN` is written as `default_day`** [VERIFIED, decoded from four LEDs]:

| LED | Radiant State 1 | State 2 | State 3 | State 4 |
|---|---|---|---|---|
| `zm_giant.led` (ssi1 = ssi2 = zm_factory) | zm_factory | zm_factory | default_day | default_day |
| Map One (ssi1 = ssi2) | acc_ssi_night_dim80 | acc_ssi_night_dim80 | default_day | default_day |
| **TOD II** (ssi1 only; the LED on disk, written 2026-09-24 00:03 by THE FALL's full build; the 2026-09-23 22:56 LED read the same) | tod_ssi_cybercity | **default_day** | default_day | default_day |
| zm_test_map template (ssi1 = default_day) | default_day | default_day | default_day | default_day |

`default_day` is a stock daytime sun: `stops 14`, `ev 15`, `evmin 1`, `evmax 16`, `pitch 125`, `yaw 150`, `colorSRGB 1 0.976 0.949` (src: source_data/ssi.gdt) [VERIFIED]. Since `ssi2..4` default to empty in the definition, the `default_day` in those slots comes from Radiant's export step [VERIFIED data; the mechanism is INFERRED].

**What the engine shows in a state whose `ssiN` is empty is unknown [TEST].** Evidence both ways:
- Radiant contains the strings `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE`, `NO BAKE STATE %d using %d`, `Active lighting state is no bake` and `volume.lightStateMask` (src: bin/Radiant_modtools.exe strings) [VERIFIED strings; meaning INFERRED: a state can go unbaked and reuse another state's data].
- Three community reports say a state switch did nothing, or perk lights never showed, until the sun volume had a real SSI for that state (src: https://forum.modme.co/wiki/threads/3395.html; https://steamcommunity.com/app/455130/discussions/0/340412619134508371/; https://steamcommunity.com/app/455130/discussions/0/2592234299570231550/) [COMMUNITY].
- Counter-evidence: Treyarch's `map_source/_prefabs/mp/mp_sector/mp_sector_light.map` sets `ssi1` (plus `ssi1_runtime_override`) only and has 5 of its 275 lights at `(0,1,1,1)`; no MP script ever assigns `level.lighting_state`, so which state MP runs in, and what those lights do, is not shown [VERIFIED data; the reading is INFERRED]. The installed ZM and MP templates (`rex/templates/*/map_source/*/template.map`) also set `ssi1` only, but the ZM template's file time is 14 minutes later than the other stock files, so it may have been edited locally; do not cite it either way [VERIFIED file data; the edit is INFERRED]. TOD1 shipped with `ssi1` only, and project records describe visible light at its spawn light's position before power (src: docs/107_sun_volume_yellow_postmortem.md; docs/104_cybercity_sky.md §4d) [COMMUNITY].

**The supported rule:** fill `ssiN` with a real SSI (not `default_day`) for **every state the game can enter**. The same SSI in two states is fine: The Giant and Map One both do it, and Satsuma's fix was `zm_factory` in ssi1 AND ssi2 [VERIFIED stock data + COMMUNITY]. The community warning about "distinct SSIs per state" concerns runtime overrides only: "if you have the same override in two separate states Radiant ... will not let you build light in the other states" (VerK0, lighting tutorial part 1, https://www.youtube.com/watch?v=hPweAEu8zJY) [COMMUNITY, untested here]. Give each state its own `ssiN_runtime_override` only if you use overrides.

**A darker pre-power sky.** Because each state has its own SSI, a state can carry a different sun, sky light and exposure; the SSI's own `evmin/evmax/evcmp` are the practical per-state exposure control [INFERRED; section 6]. Treyarch's MP recipe uses an `_bake` SSI in `ssiN` and the displayed look in `ssiN_runtime_override`, and warns that going too far makes reflections stop matching the visible sky (src: SunSky_Light_SetUp.pdf p.17; Multiplayer_Lighting_Workflow.pdf p.2) [VERIFIED].

**`transitionTime`** exists, but nobody has seen what it blends (sun only, or probes and exposure too) at a state switch [TEST].

**The sky you see proves nothing about the state's SSI.** Our worldspawn carries its own `skyboxmodel` and `ssi` keys, which survive into the compiled BSP, so the visible sky may come from worldspawn rather than the active state's SSI [VERIFIED key presence; engine use INFERRED].

## 6. Everything else a state can switch

All keys and defaults below are from bin/t7.def.json [VERIFIED]; behaviour notes are tagged separately.

| Entity | State keys | Default | Notes |
|---|---|---|---|
| `light` | `lightingstate1..4` | all true | The core mechanism. Details in [01_lights.md](01_lights.md) |
| `build_light` | `lightingstate1..4` (hidden) | all true | Blockout light; probably cannot join exploders [INFERRED] |
| `fx` (Radiant-placed effect) | `fxstate1..4` | all true | Per-instance state switch. FX_Lights.pdf p.2: the only per-instance overrides are "Origin and Angles, and Lighting State" |
| FX light element inside an `.efx` (`dynamicLight2` block) | `lightingstate1..4` in the block's KVPs | all 1 in our `fx_perk_glow_*.efx` | [VERIFIED key presence, e.g. this repo's share/raw/fx/acc/light/fx_perk_glow_amber.efx]; effect on a script-played FX [TEST] |
| `misc_model`, `script_model`, `script_brushmodel` (+ destructible/scriptbundle templates) | `lightingstate1..4` | all true | **Unproven.** May hide the model per state, or only gate its baked-lighting contribution [TEST] |
| `volume_worldfog`, `volume_litfog` | `LIGHTSTATE_1..4` (spawnflags 4096/8192/16384/32768) + `BANK_1..4` | all four states on; BANK_1 on | Fog per state and per bank (section 11) |
| `vbloom_box`, `vlut_box`, `vcolor_box/_omni/_spot`, `pbg_box/_omni/_spot` | `LIGHTSTATE_1..4` (16/32/64/128) + `BANK_1..4` | **only `LIGHTSTATE_1`** | See the gotcha below |
| `volume_performance` | `LIGHTSTATE_1..4` (1/2/4/8) | **only `LIGHTSTATE_1`** | carries `maxDynamicShadows` (12), `sunShadowSplitCount` (3) |
| `volume_exposure`, `lut_volume`, `volume_worldfogmodifier` | `BANK_1..4` only, no state flags | BANK_1 on | switched by bank, not by state (section 11) |
| `reflection_probe` | none | — | Probes bake in every state [INFERRED, section 7] |
| `worldspawn` | `state_alias_1..4` | "State 1".."State 4" | names only |

**Gotcha: post volumes default to Radiant State 1 only.** A `pbg_*`, `vlut_box`, `vbloom_box`, `vcolor_*` or `volume_performance` placed with default flags is active only in Radiant State 1. A usermap boots in Radiant State 2, so such a volume would do nothing all match unless `LIGHTSTATE_2` is ticked [INFERRED from the def + the mapping; TEST]. The Giant's 15 `pbg_box` volumes are `LIGHTSTATE_1` only, which fits its "powered = State 1" convention [VERIFIED].

**State-gated FX lights, the stock example.** The Giant places two `fx` entities at the same origin for the Pack-a-Punch key light: `light/fx_light_pap_key` with `fxstate 0,1,0,0` (pre-power) and `light/fx_light_pap_key_on` with `fxstate 1,0,0,0` (powered) (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map) [VERIFIED data; runtime behaviour INFERRED]. That switches an animated FX light with power and no script. FX lights themselves are covered in [04_fx_lights.md](04_fx_lights.md).

**Model state flags.** Map One's audit found no stock use of model `lightingstate` flags other than all-true (21,217 misc_models in 503 stock ZM sources) [COMMUNITY], and The Giant's light prefab has 22 misc_models, 2 script_brushmodels and 1 script_model, all `1111` [VERIFIED]. Do not rely on them to hide geometry until tested. Map One also found that a baked misc_model carrying only a partial `lightingstate1..3` key set was one of the suspects in an LED-bake crash (`Allocator <Gfx::LightingStateInst, 1024> has outstanding allocations`; the real cause was a second baked instance of a light-carrying model), and now always writes the full `lightingstate1..4` set (src: Map One CHANGELOG.md:52-70) [COMMUNITY].

**Per-state exposure keys.** Lighting_Parameters.pdf p.12 documents worldspawn `evmin1..4`, `evmax1..4`, `evcmp1..4` "of lighting state 1, 2, 3, or 4" [VERIFIED text]. They are absent from bin/t7.def.json and unused in every stock `.map` inspected [VERIFIED absence]. Treat them as documented but unproven, and use each state's SSI exposure instead [INFERRED]. Exposure behaviour is in [05_sun_sky_exposure_fog.md](05_sun_sky_exposure_fog.md).

## 7. What each extra state costs

**Strong evidence that each state has its own baked data; no measurement of the cost.**
- Radiant indexes probe data per state: `probe.irradianceXArray[ledState]`, `probe.exposures[ledState]`, `probe.avgCubeColors[ledState]`, and keeps sun-shadow data per state (`lightState.ssi`, `lightState.sst.*`), with the log line `processing outdoor occlusion for state %d` (src: bin/Radiant_modtools.exe strings) [VERIFIED strings; INFERRED meaning: probe bounce, probe exposure and sun shadows are computed and stored once per state].
- The official doc agrees in outline: each state has runtime lighting and an optional bake override, and "ssi is what will bake into the reflection probes" (SunSky_Light_SetUp.pdf p.1) [VERIFIED].
- But the LED lists an SSI for all four states even when only `ssi1` is set, and Radiant has explicit skip/reuse paths (`NO BAKE STATE %d using %d`, `no outdoor occlusion for state %d`). Whether leaving `ssi2..4` empty avoids baking them, and how much bake time and `.led`/pack size each extra filled state adds, are **unmeasured** [TEST].

**Practical rules** [INFERRED]:
- Give an SSI only to the states you actually use, and measure the `.led` size and bake result before and after adding one (bake twice; timing is noisy on this host, see [10_troubleshooting_limits_history.md](10_troubleshooting_limits_history.md)).
- Any change to state flags, SSIs or state-gated volumes needs a new LED. The doc says a new LED is needed "When Geo changes, or if Lighting has changed" (src: docs_modtools/Generate_LED.pdf) [VERIFIED]. In this repo that always means a FULL build, because `-GscOnly` skips both cod2map and the LED bake [VERIFIED: tools/build_map.ps1].
- For exploder-only edits Radiant can save time with "only checking Export Local Probes" (SunSky_Light_SetUp.pdf p.16) [VERIFIED], but our headless bake may not expose that choice [INFERRED].
- **If a state switch looks like a no-op, check the bake before the script.** Map One's "bright before AND after power" was a `.ff` linked against a BSP recompiled after the LED bake, so "every lighting state rendered identically"; its rule became "the `.led` must be newer than the `.d3dbsp`" (src: Map One CHANGELOG.md:17571-17577) [COMMUNITY]. This repo's full build refuses a stale `.led` ([10_troubleshooting_limits_history.md](10_troubleshooting_limits_history.md)).

## 8. Transitions: instant or blended

| Thing | Blends? | Evidence |
|---|---|---|
| Placed lights at `set_lighting_state` | **No fade found** | No fade argument on `SetLightingState` or `util::set_lighting_state` [VERIFIED API/code]. Map One observed an instant pop [COMMUNITY] |
| Sun/sky between states | Possibly: `volume_sun transitionTime` | Key exists, default 0 [VERIFIED]; effect never seen [TEST] |
| Fog banks | Yes | `SetLitFogBank( lcn, scriptid, bank, time )`, time -1 uses the volume's `fogtime` [VERIFIED API]; Giant fog volumes use `fogtime` 0.5-2.5 [VERIFIED data] |
| Exposure adaptation | Yes (engine auto exposure) | `SetExposureInstantSnap` "snap exposure to base calculated probe value, ignore iris adaption and damping" [VERIFIED API]; Giant worldspawn `secondsLerpToDarker/Lighter 1`, keys not in the def [INFERRED meaning] |
| Exploders | Possibly | membership strings carry `fin`/`fout`, Radiant has "Edit Fade In" / "Edit Fade Out" menu items; every stock value is 0 [INFERRED, TEST] |
| FX lights | Yes, by authoring | intensity/radius/colour/FOV curves over the particle life (FX_Lights.pdf p.1) [VERIFIED] |
| Vision grade | Yes | `VisionSetNaked( name, seconds )` (server) [VERIFIED API] |

**Faking a fade at power (Map One's recipe)** [COMMUNITY, played]: mask the snap with a vision grade applied *before* the flip, then ramp the grade back.

```
// Map One CheckForPower(), shortened (Map One convention: (0) at start, (1) at power)
level util::set_lighting_state( 0 );
level flag::wait_till( "power_on" );          // "power_on" is a FLAG; a bare waittill misses an already-set flag
VisionSetNaked( "acc_grade_warm1", 0 );       // dark grade that matches the current pre-power look
wait 0.05;
level util::set_lighting_state( 1 );
// _acc_atmosphere::apply_vision then ramps the grade back to "default" over ~15 s
```

Map One learned two details the hard way: both `VisionSetNaked` calls in one frame made the lerp a no-op (it added a `wait 0.25`), and a linear ramp read "instant" until it held dark for the first ~55% and then surged through intermediate grades (src: Map One CHANGELOG.md:17225-17250) [COMMUNITY].

**Power-on stutter is usually not lighting.** Community reports say the frame drop at power comes from registering new perk hint strings, fixed by registering them early on a throwaway trigger (src: https://forum.modme.co/wiki/threads/2118.html) [COMMUNITY]. That ties into this project's hint-string budget rules in CLAUDE.md.

## 9. Exploders: named light groups

### 9.1 What they are

An exploder is a **named group** of Radiant-placed entities that script can play, stop or kill by name. Despite the name, it has nothing to do with explosions: it is how BO3 switches individual groups of placed lights. The Giant uses exploders for its red/green map lamps, trap lamps and teleporter lights; stock Quick Revive uses one for its machine lights [VERIFIED, 9.7].

Members can be:
- **primary lights** (`light` entities; Radiant warns "only primary lights can be added to exploders") [VERIFIED string, bin/Radiant_modtools.exe];
- **`fx` entities**, including FX lights (FX_Lights.pdf p.1 "Set up a light inside an exploder") [VERIFIED];
- **reflection probes**: 2 stock prefab probes carry exploder membership [VERIFIED data; what that does is unknown].

Stock prefabs store membership on 127 fx entities, 87 lights and 2 probes [VERIFIED counts].

### 9.2 Making one in Radiant

1. Select the lights and/or FX.
2. Open the **Exploder Manager** window (community tutorials open it from a toolbar right-click menu [COMMUNITY]).
3. Right-click, **"Create New Exploder From Selection"** (the doc spells it "from selection"), and name it, e.g. `lgt_floor10_on`.
4. Test with **Play Exploder**, **Stop Exploder** and **Kill Exploder**. "'Stop Exploder' will stop playback, but leave the time where it is. Kill will reset to the start" (FX_Lights.pdf p.1) [VERIFIED].
5. Several entities can share one name; to toggle lights one at a time you need one exploder each (src: https://forum.modme.co/wiki/threads/3642.html) [COMMUNITY].
6. FULL build (the membership lives in the map and the LED) [INFERRED from section 7].

Radiant also has menu items "Edit Delay On", "Edit Delay Off", "Edit Fade In", "Edit Fade Out", "Toggle On/Off Role", "Edit Exploder Sound Alias" and "Copy To Opposite State" [VERIFIED strings, bin/Radiant_modtools.exe; what each does is INFERRED from the names or unknown].

### 9.3 Membership keys

In bin/t7.def.json only the `fx` entity declares `exploder_count` and `exploder_index_0..31` (hidden), and only `trigger_once` declares the trigger keys. Lights and probes carry the membership keys in stock map data anyway, written there by the Exploder Manager [VERIFIED def and data].

| Key | On | Format / values seen in stock data [VERIFIED] |
|---|---|---|
| `exploder_count` | fx (def, hidden); light and probe (map data only) | int; an fx can list up to 32 (`exploder_index_0..31` in the def) |
| `exploder_index_N` | light, fx, probe | old: `"0 0 quick_revive_lgts"`; new: `"ver=2 don=0 doff=0 fin=0 fout=0 off=0 name=lgt_vending_stamina_up"`; also `"ver=1 don=0 doff=0 fin=0 fout=0 off=1 name=lgt_vending_mulekick_on"`; Radiant's format strings include `ver=%d don=%i doff=%i fin=%i fout=%i off=%i name=%s` and `ver=%d don=%i doff=%i snd=%s off=%i name=%s` |
| `exploderDisabled` | light, efx light blocks | `1` on 45 of The Giant's 48 exploder lights and on the Quick Revive and Stamin-Up prefab lights |
| `exploderFade` | light, probe, efx light blocks | `1` on 518/543 Giant lights and 161/176 Giant probes; the generator writes it on all 53 of our probes |
| `script_exploder_radiant`, `script_stop_exploder_radiant` (string); `script_exploder`, `script_stop_exploder` (int) | `trigger_once` (def); the script reads them on every trigger | a trigger that plays/stops an exploder when touched (src: share/raw/scripts/shared/exploder_shared.gsc:237-263, a loop over `trigger::get_all()`) |

**Meanings are not documented** [INFERRED]: `don`/`doff` read like delay on/off, `fin`/`fout` like fade in/out, `snd=` a sound, `off=` the "on/off role" (Mule Kick's `off=1` may mean "this member turns OFF when the exploder plays"). The zeroy wiki says an exploder light "will start OFF and switch ON when called via script" [COMMUNITY]. Neither `exploderFade` nor `exploderDisabled` is a key in bin/t7.def.json, and neither appears as a string in Radiant, cod2map or the linker [VERIFIED absence], so their effect is unknown; on probes `exploderFade` is probably a dead template key [INFERRED]. **Copy these keys from a stock example rather than typing them.**

### 9.4 Script API

A string id is a Radiant exploder; an integer id takes the legacy createfx path. Use strings. (src: share/raw/scripts/shared/exploder_shared.gsc and .csc; engine functions from bo3_scriptapifunctions.htm) [VERIFIED]

| Call | Side | Does |
|---|---|---|
| `exploder::exploder( "name" )` | server (`#using scripts\shared\exploder_shared;`) | `level notify( "exploder" + name )`, then `ActivateClientRadiantExploder( name )` ("Activates a client side radiant exploder") (gsc:275-285, 663-668) |
| `exploder::stop_exploder( "name" )` | server | `DeactivateClientRadiantExploder( name )`, **only if `level.clientScripts`** (gsc:762-791) |
| `exploder::kill_exploder( "name" )` | server | `KillClientRadiantExploder( name )`; asserts on a non-string id (gsc:810-819) |
| `exploder::exploder_duration( "name", secs )` | server | plays, then stops after `secs` (gsc:897-908) |
| `exploder::exploder( "name", localClientNum )` | client | `PlayRadiantExploder( lcn, name )`; with no `lcn` it loops every local player (csc:297-366) |
| `exploder::stop_exploder( "name", localClientNum )` | client | `StopRadiantExploder` (csc:368-400) |
| `exploder::kill_exploder( "name" )` | client | `KillRadiantExploder` for every local player; no `lcn` argument (csc:412-424) |
| numeric ids, e.g. `exploder::exploder( 101 )` | both | legacy; `ActivateClientExploder` "is sent as a reliable command, and will not work with killcam or demos" (API) |

### 9.5 Gotchas

- **Server stop can be a silent no-op.** Server `stop_exploder` sends the stop only when `level.clientScripts` is true. `load_shared.gsc` sets `level.clientscripts = ( GetDvarString( "cg_usingClientScripts" ) != "" )` (src: share/raw/scripts/shared/load_shared.gsc:55, 60) [VERIFIED]. GSC field names are case-insensitive, so the two spellings are one field [INFERRED]. `util::clientNotify`, which The Giant's power flow depends on, has the same gate, which suggests the dvar is set in zombies [INFERRED]. Still, for a group that must turn OFF reliably, stop it from client script, or log the dvar in a test [TEST]. Server `exploder()` and `kill_exploder()` call the engine unconditionally [VERIFIED].
- **Server calls are one-shot.** Nothing in `exploder_shared.gsc` records active radiant exploders to replay for a player who joins later [VERIFIED absence]. Whether the engine replays them itself is unknown [TEST]. The Giant's `pl1` client-notify lamps (9.7) are the same kind of one-shot: a late joiner's client never receives `pl1` [INFERRED].
- **Interplay with lighting-state flags is unknown [TEST].** Does a light inside a played exploder show if its `lightingstateN` for the active state is 0? The Giant's exploder lights mostly carry state masks that include the powered state: `(1,0,1,1)` ×24, `(1,0,0,0)` ×15, `(1,1,1,1)` ×7, `(1,1,0,1)` ×2 [VERIFIED], and their exploders are played after power, which fits "must be enabled in the active state" but does not prove it. Stock Quick Revive's prefab lights are `0000` and in the exploder that stock plays [VERIFIED], and community threads report stock perk lights not working until states are ticked [COMMUNITY]. Until tested, **tick the exploder light in every state it may be played in** [INFERRED].
- **Count cap.** Radiant shows `Total Exploders: %d/%d` with the initial text `Total Exploders: 0/120`, and has "Too Many Exploders" and "There are too many individual exploders in the top-level map." (src: bin/Radiant_modtools.exe strings) [VERIFIED strings]. A cap of 120 exploders is [INFERRED]; whether prefab exploders count is unknown [TEST].
- **Baked bounce is unknown [TEST].** Whether an exploder light's bounce is baked into the probes (leaving glow on the walls while the exploder is off) is undocumented. Treyarch kept exploder lights tiny (median radius 20, median ~5.6 stops, against a median radius of 171 for its other lights) [VERIFIED data; the reason INFERRED].
- **Exploder lights are still ordinary primary lights at runtime**: shadows, culling and volumetric settings apply as for any light ([01_lights.md](01_lights.md)). The Giant keeps them cheap: 40 of its 48 exploder lights have no shadow map at all (`PRIMARY_NOSHADOWMAP 1`); 38 carry `shadowUpdate Always`, but only 3 of those actually have a shadow map, so just 3 cast live shadows [VERIFIED data, zm_giant_light.map].

### 9.6 The hot-join-safe pattern: a world clientfield drives client exploders

The Giant drives its teleporter-console lamps from **world clientfield callbacks** (src: share/raw/scripts/zm/zm_giant.csc:54-149) [VERIFIED]. A world clientfield's current value is sent to a client when it joins, and the callback runs with `bInitialSnap` set [INFERRED from the callback signature and the `CF_CALLBACK_ZERO_ON_NEW_ENT` convention]. That makes the lamp state correct for late joiners. Sketch for a progress-driven group (untested):

```
// SERVER (__init__): one integer = how far the lighting has progressed
clientfield::register( "world", "tod_lit_step", VERSION_SHIP, 7, "int" );
// later, when a door opens:
level clientfield::set( "tod_lit_step", n );

// CLIENT (__init__)
clientfield::register( "world", "tod_lit_step", VERSION_SHIP, 7, "int", &lit_step_cb, !CF_HOST_ONLY, !CF_CALLBACK_ZERO_ON_NEW_ENT );

function lit_step_cb( localClientNum, oldVal, newVal, bNewEnt, bInitialSnap, fieldName, bWasTimeJump )
{
    from = oldVal;
    if ( bInitialSnap || !isdefined( from ) ) from = 0;   // a joiner: light everything up to newVal
    for ( i = from + 1; i <= newVal; i++ )
        exploder::exploder( "lgt_step_" + i, localClientNum );   // PlayRadiantExploder for this client
}
```

Add a dev log line per change (`[TOD_LIGHTS]`, old/new value, whether it was an initial snapshot), following the CLAUDE.md logging pattern.

### 9.7 The Giant's exploder examples [VERIFIED]

- **Map lamps as status lights** (share/raw/scripts/zm/zm_giant_fx.csc:225-292). The server sends `level util::clientnotify( "pl1" )` after power (zm_giant.gsc:427-428). Each pad's client thread then plays `map_lgt_<pad>_red`; when that pad links it runs `stop_exploder( red )` then `exploder( "map_lgt_<pad>_green" )`. The Pack-a-Punch lamp plays `map_lgt_pap_red`, switches to the flashing `map_lgt_pap_flash` while players link, and turns green after `wait( 1.5 ); // dramatic pause`.
- **Teleporter-linked lights** from the server: `exploder::exploder( "lgt_teleporter_" + pad + "_linked" )` (share/raw/scripts/zm/zm_giant_teleporter.gsc:744).
- **Console lamps** from world clientfields: `console_blue/green/red/start` callbacks kill the red exploder and play `teleporter_controller_light_N` (zm_giant.csc:90-149).
- **Trap lamps**: `trap_lights_red()` / `trap_lights_green()` swap `<light targetname>_red` / `_green` with `stop_exploder` + `exploder` (share/raw/scripts/zm/_zm_traps.gsc:445-477).
- **Quick Revive**: `exploder::exploder( "quick_revive_lgts" )` when the machine turns on, `stop_exploder` after the third solo life (share/raw/scripts/zm/_zm_perk_quick_revive.gsc:185, 791). In co-op this waits for `revive_on`; in solo it runs at load (lines 159-185).

## 10. Scriptable server lights

**Plain version.** A normal light belongs to the client and script cannot touch it. Tick `scriptable` and set it to ServerSide, and it becomes a script entity whose brightness, colour and size server script can change, but never above what was baked.

**Keys** (src: bin/t7.def.json `light`) [VERIFIED]: `scriptable` (spawnflag 8): "Makes a light show up as an entity to script. NOTE: default is client side so you must choose the server side drop down to grab on the server"; `client_server` `ClientSide` (0) / `ServerSide` (spawnflag 32); `targetName`. Fetching it with `GetEnt( "<targetname>", "targetname" )` is [INFERRED].

**API** (src: bo3_scriptapifunctions.htm; all listed as Server) [VERIFIED]:

| Function | Note from the API page |
|---|---|
| `<light> SetLightIntensity( f )` | "1 is fullbright, but values can be larger than 1" |
| `<light> SetLightColor( (r,g,b) )` | components 0..1 |
| `<light> SetLightRadius( r )` | "cannot be larger than the radius when the map was compiled" |
| `<light> SetLightFovRange( outer, [inner] )` | cannot exceed the compiled FOV, or be less than 1 |
| `<light> SetLightExponent( 0..100 )` | legacy falloff exponent |
| `GetLightIntensity / Color / Radius / FovOuter / Exponent` | getters |
| `<entity> MakeLight( primaryLightIndex )` | Client, "Create a light"; no stock usage |

**Evidence it works is weak.** No stock script under share/raw/scripts calls any `SetLight*` [VERIFIED grep]. Community opinion is split: "the light functions in the api are now deprecated" (Harry Bo21, https://forum.modme.co/wiki/threads/2029.html); one thread reports no effect (871); one moved a light with an elevator (3412) [COMMUNITY]. Alien Isolation Zombies ships 21 ServerSide scriptable lights; whether its scripts drive them was not checked [COMMUNITY].

**Costs** [INFERRED]: each ServerSide light is a server entity, and CLAUDE.md names the ~1024-gentity budget as the spire's binding constraint; changes travel as entity state; the baked bounce stays at the compiled intensity. All 344 TOD II lights are ClientSide and not scriptable (`spawnflags 82` has neither bit 8 nor bit 32) [VERIFIED data], so by the def's own note no server script can reach them.

## 11. Fog, exposure, LUT and grade banks as mood switches

Banks are a second, independent switch system. A fog, exposure, LUT or grade volume can belong to up to four **banks** (`BANK_1..4` flags), and client script chooses which banks are active, per local client, sometimes with a blend time [VERIFIED keys and API]. Unlike lighting states, banks carry no baked light: they change fog, exposure and colour grade, not which lamps exist or how much bounce light there is [INFERRED from the volume types].

| API (bo3_scriptapifunctions.htm) | Side | Does |
|---|---|---|
| `SetLitFogBank( lcn, scriptid \| -1, bank 0-3, time \| -1 )` | client | picks the lit-fog bank; `time -1` uses the volume's `fogtime` |
| `SetWorldFogActiveBank( lcn, mask )` / `<client> SetWorldFogActiveBank( mask )` | client / server | world-fog bank mask. The API page lists only the server form; the client form is what stock `_zm_ai_wasp.csc` and `zm_giant_fx.csc` call |
| `SetExposureActiveBank( lcn, mask )` | client | exposure-volume bank mask |
| `SetExposureInstantSnap( lcn, bool )` | client | snap exposure, "ignore iris adaption and damping" |
| `SetLutVolumeActiveBank( lcn, mask )`, `SetLutScriptIndex( lcn, idx )` | client | LUT volumes |
| `SetPBGActiveBank( lcn, mask )` | client | position-based grade boxes |
| `VisionSetNaked( name, [duration] )` | server | global vision grade with a blend |

**The stock examples.** The wired one is the parasite-round fog in `_zm_ai_wasp.csc:29-61`: a **world clientfield** `toggle_on_parasite_fog` (2 bits, `!CF_CALLBACK_ZERO_ON_NEW_ENT`) whose client callback switches the banks, 1 = parasite fog on, 2 = back to normal [VERIFIED]:

```
// client callback for the world field "toggle_on_parasite_fog"
if ( newVal == 1 )   // for every local client:
{
    SetLitFogBank( localClientNum, -1, 1, -1 );   // lit fog -> bank index 1 (BANK_2), blend by each volume's fogtime
    SetWorldFogActiveBank( localClientNum, 2 );   // world fog -> bank mask 2 (BANK_2)
}
if ( newVal == 2 )
{
    SetLitFogBank( localClientNum, -1, 0, -1 );
    SetWorldFogActiveBank( localClientNum, 1 );
}
```

The Giant carries the same pair in a helper, `ramp_fog_in_out()` (bank 2 for 2.5 s, then back; share/raw/scripts/zm/zm_giant_fx.csc:165-180), and its fog volumes have "dogs" fog in bank 2 (e.g. `fsi_2 "zm_factory_dogs_afog"`) with `fogtime` 0.5-2.5 [VERIFIED data]. No stock script calls that helper, though [VERIFIED grep of share/raw/scripts], so treat it as authoring intent, not a working example. That bank index 0-3 means `BANK_1..4`, and that the mask bits are the `BANK_n` spawnflag values, is [INFERRED] from these call pairs and the def.

**For a dark map** [INFERRED]: banks are a cheap way to add an "alarm", "boss" or "power restored" mood without a new baked state, and they blend. Drive them from a world clientfield callback so late joiners match. Treyarch's MP guidance warns that "as soon as exposure drops 2 or more stops below the scene exposure, visibility will start to become a problem" (Multiplayer_Lighting_Workflow.pdf p.3) [VERIFIED]. Our tower has no fog or exposure volumes at all; its fog is scripted with `SetVolFog` / `fog_off()` in `_tod_atmosphere.gsc`, on the worldspawn fog asset `fsi zm_factory_volumetric` [VERIFIED].

## 12. Switching emissive glow

### 12.1 Why this is its own problem

An emissive material makes a surface glow by itself (screens, neon, the vertigo grid). Lighting states switch lights, not materials, so emissive glow does not follow power on its own [INFERRED]. Treyarch's Materials doc gives the reason its "lampshade" (backlit) shaders exist: they are "meant to be used with a light placed behind them", which "makes switching lights on and off easier because we don't have to dial in and sync up a bunch of emissive materials" (docs_modtools/Materials.pdf p.17) [VERIFIED]. Emissive families and fields are covered in [03_glow_and_perks.md](03_glow_and_perks.md). The ways to switch glow at runtime:

### 12.2 Script-driven emissive: `lit_emissive_script` + shader constants

- The `lit_emissive_script` techset adds "Tint State 2/3/4" (`colorTint2..4`), a "Script Preview" control "Tint (Brightness, State)" (`cg00_x`, `cg00_y`, range 0-4) and the define `USE_SCRIPT_CONTROLS` (src: share/raw/techsetdefs_stable/geometry/lit_emissive_script.techsetdef) [VERIFIED]. Variants exist in `geometry_plus/` (`lit_emissive_script_plus`, `_vectorpick_plus`) and `geometry_advanced/` (`lit_emissive_script_advanced`, `_advanced_fullspec`), plus `geometry/lit_emissive_script_vectorpick` and `_bloat` [VERIFIED file names].
- Client script drives an **entity's** material vectors: `MapShaderConstant( localClientNum, index, "<constant>", [x..w] )` maps a constant to an index, and `setshaderconstant( localClientNum, index, x, y, z, w )` sets it; both are client-only (src: bo3_scriptapifunctions.htm) [VERIFIED].
- **Stock Der Wunderfizz does exactly this** (src: share/raw/scripts/zm/_zm_perk_random.csc:104-116, 257, 275, 346, 367; values from _zm_perk_random.gsh) [VERIFIED]:

```
self MapShaderConstant( localClientNum, 1, "ScriptVector0" );          // once per entity
self SetShaderConstant( localClientNum, 1, artifact, 0, machine, 0 );   // x = artifact glow, z = machine lights
// machine lights (ScriptVector0.z): OFF 0.00, POWERED 0.40, AVAILABLE 0.70, ACTIVATED 1.00
// artifact glow   (ScriptVector0.x): ARTIFACT_GLOW 0, ARTIFACT_DIM 1
```

- That `ScriptVector0` is the constant `lit_emissive_script` reads, and that `cg00` in the GDT previews it, are [INFERRED]; the shader source is not shipped.
- In principle this dims a perk panel or sign before power and ramps it after, without a second model [INFERRED, TEST].

### 12.3 Material override (client)

`<entity> SetMaterialOverride( <material> )` and `<entity> ClearMaterialOverride()` are client functions (src: bo3_scriptapifunctions.htm; example `self SetMaterialOverride("water")`) [VERIFIED API]. Swapping a lamp entity to an "off" material this way is plausible but untested [INFERRED, TEST].

### 12.4 Model and skin swaps

- **An `_on` model.** Make the lit look a second xmodel, usually the same mesh with an xmodel `skinOverride` pointing at hotter material twins, and `SetModel` it at power. This project's Rampage Inducer (`tod_inducer` / `tod_inducer_on`) and BO7 perk machines (`off_model` / `off + "_on"`) already work this way (src: scripts/zm/zm_tod2_cybercity/_tod_rampage.gsc, _tod_perk_lights.gsc) [VERIFIED code; the inducer look is user-approved per CLAUDE.md].
- **The Giant's client lamp swap.** `light_model_swap( name, model )` waits for `pl1`, then client-`SetModel`s every lamp with that targetname to its `_on` model (src: share/raw/scripts/zm/zm_giant_fx.csc:184-197) [VERIFIED]. No entity with those targetnames exists in the shipped Giant map source, so this code has nothing to act on there [VERIFIED absence].
- **Stock perk machines do not swap meshes**: every stock perk `.gsh` sets the disabled and active model to the same name (e.g. `_zm_perk_juggernaut.gsh:7-8`) [VERIFIED].

### 12.5 What cannot switch

- **World brush faces.** Their materials are compiled into the BSP and they have no entity to call `SetModel`, `SetMaterialOverride` or `MapShaderConstant` on [INFERRED from the API shapes: all are called on entities]. A glow that must change with power has to live on an entity (`script_model`, `script_brushmodel`, `misc_model` with a model) [INFERRED].
- **Model `lightingstate` flags** might hide a glowing model per state, but that is unproven (section 6) [TEST].

## 13. How stock perk machines power on

The full stock chain [VERIFIED unless marked]:

1. The power switch sets flag `power_on` and the world clientfield `zombie_power_on` = 0 (`_zm_power.gsc:723-735`).
2. Each perk's `<alias>_on` notify arrives. Stock `_zm_power.gsc` registers every vending machine as a powered item, and when global power comes on its `perk_power_on` sends `level notify( <alias> + "_on" )` and unpauses the perk, one powered item per network frame (`_zm_power.gsc:157-170, 184, 474-487, 692-698`). So a map does not have to send these notifies itself. The Giant also sends each one explicitly, one network frame apart (zm_giant.gsc:550-568).
3. `perk_machine_think` sets `on_model` (the same model as `off_model` in stock), vibrates the machine, plays `zmb_perks_power_on`, starts the loop sound and threads `perk_fx( machine_light_effect )` (`_zm_perks.gsc:113-161`).
4. `perk_fx` waits 3 s, then the **server** runs `playfxontag( level._effect[ fx ], self, "tag_origin" )` (`_zm_perks.gsc:280-316`). On the server, most `_zm_perk_*.gsc` set `level._effect[<perk>_light]` to a `zombie/fx_perk_*_zmb` effect (e.g. `_zm_perk_juggernaut.gsc:70`; Deadshot and Electric Cherry use older `_t6/misc/fx_zombie_cola_*` effects), and those are billboard sprites only (3-4 each), with no light element. The `*_factory_zmb` variants (which The Giant precaches itself, zm_giant.gsc:95-101) contain 6-15 `dynamicLight2` elements each [VERIFIED file contents; "the sprite versions cast no light" is INFERRED].
5. Client side, `init_perk_machines_fx` returns at once unless `level.enable_magic` is true; otherwise `perk_start_up` waits for the **client** `power_on` notify and plays the machine light FX in bursts of growing length for about 3 s, on client-spawned `tag_origin` models 50 units below the machine (`_zm_perks.csc:193-262`) [VERIFIED]. Because of the clientfield gotcha in section 3, this flicker needs the map to send `"ZPO"` [INFERRED].
6. `zm_usermap.csc` `include_perks()` assigns the `*_factory_zmb` variants client-side (`zm_usermap.csc:84, 107-116`), but each perk's client init thread sets the sprite version back when `level.enable_magic` is true (e.g. `_zm_perk_juggernaut.csc:32-38`); the server-side equivalent `perk_init()` (`zm_usermap.gsc:446-455`) is never called by stock script [VERIFIED code]. Which variant a given usermap's client finally plays depends on that flag and on load order [INFERRED].
7. Quick Revive also plays exploder `quick_revive_lgts` (section 9.7).
8. **All 49 light entities in the 8 stock perk/PaP prefabs in `map_source/_prefabs/zm/zm_core/` (seven `vending_*_struct.map` plus `vending_weapon_upgrade_spawnable.map` for Pack-a-Punch) are `lightingstate1..4 = 0`** (jugg 6, sleight 11, double tap 4, deadshot 2, marathon 8, mule kick 8, revive 5, PaP 5). Mule Kick (`lgt_vending_mulekick_on`) and Stamin-Up (`lgt_vending_stamina_up`) lights sit in exploders that no stock script plays [VERIFIED]. What an all-zero light does at runtime is unknown [TEST].

**The community fix** for stock perk prefab lights: enter the prefab, select its lights, tick the lighting states in which the machine should glow (for example Radiant State 1 under the Giant convention), for Mule Kick/Stamin-Up delete `exploder_count`, save, full build (src: https://www.ugx-mods.com/forum/mapping/92/perk-lighting-effects-fix-video-tutorial/13226/ ; https://steamcommunity.com/app/455130/discussions/0/2333276539589995175/) [COMMUNITY].

**TOD II does not use the stock vending prefabs.** Its machines are scattered script entities with their own glow: at `power_on` the server sets the scriptmover clientfield `todPerkGlow` (4 bits, colour index) on each machine, and the client callback plays an `acc/light/fx_perk_glow_*` loop with `PlayFXOnTag` after `util::waittill_dobj`, registered with `!CF_CALLBACK_ZERO_ON_NEW_ENT` so late joiners get it; a "rekick" re-pulses the field when a player first comes within 700 units (src: scripts/zm/zm_tod2_cybercity/_tod_perk_lights.gsc:34-38, 234-245, 383-461; _tod_perk_lights.csc:54-83) [VERIFIED code]. Each of those effects has one `dynamicLight2` element, so the perks do cast a little live light [VERIFIED file contents]. This is already the per-object, hot-join-safe pattern recommended in section 14. The FX-light details (including their overlapping 200/1000 ms loop) are in [04_fx_lights.md](04_fx_lights.md).

## 14. Architecture: choosing a mechanism

| Option | Can do | Cannot do | Runtime cost | Build | Hot-join | Main risks |
|---|---|---|---|---|---|---|
| **A. Global lighting state** | Swap the whole baked look in one call: lights, state-gated FX, sun/sky/exposure SSI, probe bounce, fog/post volumes; correct bounce on players and zombies per state [INFERRED] | More than 4 looks; per-area switching; smooth fades of placed lights | ~none; no entities | FULL build; unknown bake cost per filled state | Built in (every spawn re-applies) | Off-by-one; a real `ssiN` for every used state; post volumes default to State 1; model flags unproven |
| **B. Radiant exploder groups** | On/off per named group (per floor, door, room); status colours (red → green) | Smooth dimming (unless `fin`/`fout` work); whether their bounce is baked is unknown [TEST] | Members render as normal lights/FX; no server entities | FULL build to edit membership | Only if driven from a world clientfield callback | ~120 cap [INFERRED]; state-flag interplay [TEST]; server stop gate |
| **C. Scriptable server lights** | Per-light intensity, colour, radius (down only) from GSC | Exceed baked radius/FOV; proven stock use (none) | 1 server entity each + network updates | FULL build to add | Entity state replicates [INFERRED] | Untested; entity budget; "deprecated" per community |
| **D. FX lights via clientfield** (the `todPerkGlow` pattern) | Anything dynamic: per floor/door/zone, pulses, flicker, colours; no bake | Baked shadows (FX-light shadows are "either Always live, or Off", FX_Lights.pdf p.2); baked bounce (no doc says an FX light feeds the bake) [INFERRED] | Client FX + dynamic-light cost; a host per instance (server scriptmover, or a client-spawned model) | GSC/CSC + `fx,` zone lines + precache. A new `.efx` built from existing materials has gone out `-GscOnly` by project practice [COMMUNITY]; new images or materials need a FULL build ([10](10_troubleshooting_limits_history.md)) | Clientfield value replays on join | Keep `PRIMARY_NOSHADOWMAP 1`; loop interval = lifetime; culling values can hide the light from a distance; zone the effect or it may not play (see [04_fx_lights.md](04_fx_lights.md)) |
| **E. Emissive switching** (`lit_emissive_script` + shader constants, or material override) | A sign or panel dims/brightens smoothly | Light anything around it | Cheap | New material(s): FULL build | Drive from a clientfield | Untested in this project; world brush faces cannot use it |
| **F. Model/skin swaps** | A lamp or machine *looks* off/on | Light anything around it | Cheap | New xmodel(s): FULL build | Drive from a clientfield or server `SetModel` | Pair with B or D for real light |
| **G. Banks and vision** | Whole-screen mood per client, blendable | Local pools of light | Cheap | Volumes need BANK flags: FULL build; vision/script: `-GscOnly` | Drive from a clientfield | >2 stops darker than scene exposure hurts visibility (MP doc) |

### 14.1 Recommended design: dark before power, lights at power

This is the pattern for a map that really has a pre-power phase. All of it is INFERRED design from the evidence above and untested.

1. **Pick the Giant convention.** No startup call; `zm_usermap::main()` already selects Radiant State 2 = pre-power; Radiant's default preview (State 1) is the powered look. Set `state_alias_1 "power_on"`, `state_alias_2 "power_off"`.
2. **Fill `volume_sun ssi1` and `ssi2`** with real SSIs (the same one is fine, or a darker SSI in `ssi2` for a gloomier pre-power sky). Fill `ssi3/ssi4` only if those states will be used.
3. **Author four light classes**, each an explicit mask constant in the generator:
   - `ALWAYS` `(1,1,…)`: a dim navigation floor so nothing is pitch black (spawn, stairs, doors, hazards). Map One needed exactly this safe-haven layer.
   - `PREPOWER` `(0,1,…)`: dim or red emergency lights, often the dim twin of a powered fixture 1-2 stops lower (Giant median +1 stop).
   - `POWERED` `(1,0,…)`: the fixtures, signs and accent pools the power "feeds".
   - Exploder groups for staged or local reveals (below).
4. **Tick `LIGHTSTATE_2`** (and `_1`) on every grade, bloom, LUT or performance volume that must work before power.
5. **Power handler** (server):

```
level flag::wait_till( "power_on" );
// optional: mask the snap with a dark grade first (section 8)
level util::set_lighting_state( 0 );               // Radiant State 1 = powered
level clientfield::set( "tod_power_lights", 1 );   // world field: client exploders / FX / glow swaps (9.6)
```

6. **Stage the reveal**, as The Giant does: perk notifies one network frame apart, then the state, then colour lamps with a deliberate pause (its `wait( 1.5 ); // dramatic pause`). Power is a reward moment; decide what the power plausibly feeds (machines, door gates, signs) rather than lighting everything.
7. **Switch the glow too**: entity glow via `_on` models or shader constants (section 12). World emissive faces cannot switch, so they must already be dim enough for the pre-power look (see [03_glow_and_perks.md](03_glow_and_perks.md)).
8. **Logs**: a dev-gated `[TOD_LIGHTS]` line at boot, at power and after a respawn, with `level.lighting_state` and each player's `GetLightingState()`:

```
function lights_log( msg )
{
    if ( !IS_TRUE( level.tod_dev ) ) return;
    line = "[TOD_LIGHTS] ms=" + GetTime() + " " + msg;   // assemble OUTSIDE the devblock
    /#
    PrintLn( line );
    #/
}
// foreach ( p in GetPlayers() ) lights_log( "ent=" + p GetEntityNumber() + " level=" + level.lighting_state + " player=" + p GetLightingState() );
```

9. FULL build; preview both states in Radiant's camera window before baking; the user judges the look in game.

### 14.2 Recommended design: progressive per-floor lighting in a 50-floor tower

A tower where floors "come alive" as the party progresses cannot be done with lighting states: there are only four and each is global [VERIFIED]. The recommended layering (INFERRED design, untested):

1. **Base layer, baked and always on.** A dim navigation floor of ordinary baked lights (mask `ALWAYS`) plus whatever emissive trim is kept. This is what every floor looks like before the party reaches it.
2. **One world clientfield carries progress.** This project's doors open in a fixed order (under THE FALL, downward from the crown hall through floors 50..1 and the plaza to the Vault; see docs/160_the_fall.md §2), so a single integer ("how far the party has come") describes the lit set. 7 bits cover 0-127. The spire can use a second field. Set it from the door-purchase code; the client callback lights every step from `oldVal+1` to `newVal`, and from 0 on an initial snapshot (section 9.6).
3. **The progress lights are FX lights on client-spawned hosts** (option D). The client callback spawns a client `tag_origin` model per lit fixture and plays a looping FX light on it, the pattern stock `_zm_perks.csc` uses for its flicker (`spawn( client_num, origin, "script_model" )` + `playfxontag`) [VERIFIED pattern]. This spends **no server entities**, which matters because CLAUDE.md names the ~1024-entity budget as a binding constraint (on the spire) [INFERRED]. Keep `PRIMARY_NOSHADOWMAP 1` and interval = lifetime in the effect; consider playing only the floors within a few laps of the local player to cap the number of live lights [INFERRED].
4. **Or exploders, grouped** (option B), when a floor's light must be a baked primary light with proper shaping. One exploder per lap would need 50 for the tower and 70 more if the spire (parked under THE FALL) comes back, which hits the inferred 120 cap; group by district (5), by lounge, or by door instead.
5. **Glow follows the same field**: signage and panels on entities switch with `_on` models or shader constants in the same callback (option E/F).
6. **Optionally one global state for the big beat** (for example a "grid restored" or "alarm" look), with the SSI filled for that state and its bake cost measured.

## 15. Tower of Doom II today: the diagnosis

**Facts** [VERIFIED, read from the repo on 2026-09-24]:
- `map_source/zm/zm_tod2_cybercity.map` has **344 `light` entities**, all emitted by `light()` in `tools/gen_tower_map.js` (~line 7166 at the time of writing): all `PRIMARY_OMNI`, `PRIMARY_NOSHADOWMAP 1`, `shadowUpdate Never`, `ClientSide`, not scriptable, `stops 6` (def default 11; The Giant's median ~7), `falloffdistance 12`, `spawnflags 82`, brightness tuned through `bake_intensity_scale` (1 on 320 lights, 1.35 on 24), which the entity def describes as a GI-bake control ([01_lights.md](01_lights.md)).
- **Every light is `lightingstate1 0`, `lightingstate2..4 1`.**
- The `volume_sun` sets only `ssi` (a non-def key) and `ssi1` = `tod_ssi_cybercity`; no `ssi2..4`, no runtime overrides, no `target`.
- The top-level map has no `fx` entities, no exploders, no misc_models, and no fog, exposure or post volumes. Its two `misc_prefab`s (stock `_prefabs/zm/zm_core/power_switch.map` and `_prefabs/ALXS/alxs_cwpap_prefab.map`) add a switch misc_model, the switch handle and the PaP `script_model` (`1111`), but no lights, fx or exploders. Worldspawn keeps the default state aliases.
- No TOD II script calls `set_lighting_state` / `SetLightingState`; the only exploder calls come from the vendored Shadows of Evil robot (`zm_zod_robot.csc`), whose `lgt_robot_callbox_*` names do not exist in this map. The entry script calls `zm_usermap::main()` (`scripts/zm/zm_tod2_cybercity.gsc:247`).
- The LED on disk (`C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.led`, 50,487,469 bytes, written 2026-09-24 00:03 by THE FALL's full build) records per-state SSIs `[tod_ssi_cybercity, default_day, default_day, default_day]`, as did the 2026-09-23 22:56 build's.
- **THE FALL** (built 2026-09-23, unplayed) turns the power on at the initial blackscreen: `_tod_fall::power_on()` calls `zm_power::turn_power_on_and_open_doors()` + `zm_perks::perk_unpause_all_perks()`, and the plaza switch "flips nothing new" (src: scripts/zm/zm_tod2_cybercity/_tod_fall.gsc:78, 101, 183-193; docs/160_the_fall.md §3, §6, where it is listed as a decision the user may reverse).
- What changes at `power_on` today: the BO7 perk machines swap to their `_on` models, the `todPerkGlow` FX (with one dynamic light each) start on every machine, the Pack-a-Punch glow host appears (section 13), and the vendored CW Pack-a-Punch, which waits on `power_on`, starts working (docs/160_the_fall.md §6). Under THE FALL all of that happens in the first seconds.

**Inference** [INFERRED, untested]: the game boots in script state 1 = Radiant State 2, where all 344 lights are authored ON, and nothing ever changes the state. **Every light is on from spawn, and power changes none of them.** The masks match Map One's convention, but TOD never ported Map One's `CheckForPower()` startup call.

**The open doubt** [TEST]: the running state (Radiant State 2) has no `ssi2`, and its LED slot holds `default_day` (pitch 125, yaw 150, stops 14, warm `colorSRGB 1 0.976 0.949`). What the engine renders in that case is untested. Community reports say such a state may not take visible effect (section 5); TOD1 had the identical setup and its records describe visible light at the spawn light's position, which argues the lights do render. Either way, the one SSI this map authors sits in a state it never enters.

**The project's own records contradict the inference.** docs/107_sun_volume_yellow_postmortem.md:30-31, a comment near tools/gen_tower_map.js:1546 and the v17.80 CHANGELOG.md entry of 2026-09-05 ("authored OFF pre-power") describe `lightingstate1 0` as off before power. Under the stock-supported mapping, Radiant State 1 is simply never activated, so that reading (and docs/107's argument that the yellow bake did not honour the lights' "lighting state") rests on the off-by-one [INFERRED]. docs/107 itself records that `zm_usermap::main` boots state 1 and nothing flips it (docs/107:62). It also checked only the LED's State 1 SSI entry (pitch 130 / yaw 140, docs/107:57), not the State 2 entry the game uses; that is a lead the yellow investigation never examined [INFERRED]. A second candidate mechanism for the yellow tower, the global probe buried inside the "mast tier 1" brush because the `volume_sun` has no `target`, is covered in [05_sun_sky_exposure_fog.md](05_sun_sky_exposure_fog.md) and [06_reflections_probes.md](06_reflections_probes.md).

**What adding the Giant power call alone would do** [INFERRED]: `level util::set_lighting_state( 0 )` at power would move every player to Radiant State 1, where none of the 344 lights exists, so the tower would lose all its placed lights at power, and the level's sun, sky, exposure and probe data would switch to State 1's `tod_ssi_cybercity` bake at the same moment. It is a whole-level switch, not a light switch. What that looks like, including any baked bounce left behind, is untested. Remap the masks first (section 14.1).

**What this means for a dark map** [INFERRED]: today the tower has no dark pre-power look to reveal, and under THE FALL it has no pre-power period at all. Lighting states still offer one clean global beat (for example the crown phase versus after the seal, or an alarm), and the per-floor reveal the user describes fits the descent: one progress clientfield driving FX lights or grouped exploders (section 14.2).

## 16. Minimal test plan in the control map

The control map is `c:/Users/jorda/Repositories/test+map`. At commit `1db8a3f` ("Step 2: one green omni light, off before power (lightingstate1 0), tower key set") it is `zm_test_map`: the Mod Tools ZM template minus perks, PaP, box and power, plus one green omni `test_light_green` at `0 0 200` with **exactly TOD II's light key set** (`stops 6`, `spawnflags 82`, mask `0,1,1,1`), and a `volume_sun` with `ssi` / `ssi1 default_day` only [VERIFIED git history]. Its working tree has since been converted to `zm_shadowlight_arena` (a staff-test map, 23 lights all `1,1,1,1`, `ssi1` only) with uncommitted renames [VERIFIED `git status`].

**Ground rules.** This is a separate project: it builds through its own `build.ps1` into the shared Mod Tools root, which Tower II's isolation rule (docs/154) never allows a Tower II session to do on its own. Run it only with the user's go-ahead, from a separate worktree or branch at `1db8a3f` so the staff work is not disturbed. Build and stop; the user plays and takes same-spot screenshots; the agent reads `console_mp.log`. Change one thing per build. Log with the section 14.1 pattern (in the control map the log can be unconditional). The user's own graphics config turns off volumetrics, dynamic shadows and SSAO, so judge the screenshots on both that config and a high one ([09_design_and_inspiration.md](09_design_and_inspiration.md)).

**Baseline B0** (built once): step 2, plus a red omni `(1,1,1,1)` 300 units away with the same keys, `ssi1` switched to a night SSI, the stock `default_night` or the `acc_ssi_miami_night` the working tree already uses, and a server thread that logs `level.lighting_state` and each player's `GetLightingState()` 5 s after spawn and after every spawn. The night SSI matters because a stops-6 light may not read at all under `default_day`'s daytime exposure [INFERRED]. Note that in B0 and T1 the running state's LED slot (State 2, `ssi2` empty) still holds `default_day`, exactly like TOD II today; the night SSI only reaches State 2 once T2 fills `ssi2`.

| Test | Change from B0 | Expected if the model in this chapter holds | Settles |
|---|---|---|---|
| **T1** numbering and boot | none | log `level=1 player=1`; **green and red both lit** at spawn. Red lit and green dark would mean script 1 = Radiant 1 (the mapping is wrong). Neither readable means the empty-`ssi2` slot is doing something (or its day exposure hides a stops-6 light); T2 then settles the mapping | the boot state and the n → n+1 mapping (green is off only in Radiant State 1) |
| **T2** empty `ssi2` | add `ssi2` = the same SSI as `ssi1` | if T1 already showed green lit and nothing changes: an empty `ssi2` is harmless. If the scene changes (sun, exposure, green appearing), an empty `ssi2` was live `default_day` or unbaked | the TOD II doubt in section 15; also compare `.led` size (cost, section 7) and check Radiant's camera window in State 2 for `BOUNDING SUN VOLUME DOES NOT SUPPORT ACTIVE LIGHTING STATE` |
| **T3** the flip | T2 + `wait 20; level util::set_lighting_state( 0 );` | green turns off, red stays, instantly; log `level=0` | what a Giant-style power call does to TOD-style lights |
| **T4** per-player and respawn | T3, but call it on the host player only; 2 clients | host sees green off, client sees it on; after the host dies and respawns, green is back on | per-player state and the spawn reset (section 3) |
| **T5** exploders | add light `lgt_a` in exploder `test_a` (mask `1111`) and light `lgt_b` in exploder `test_b` (mask `0000`); play both at 20 s from a world clientfield callback; a second client joins after | whether `0000` exploder lights show when played; exploder lights off before play; whether a late joiner sees them; stop from server vs client | section 9.5 open questions |
| **T6** volumes and models | add a `pbg_box` with a strong grade at default flags, and a misc_model with `lightingstate 1,0,0,0` | grade inactive in State 2 (flip to State 1 to see it); model visible or hidden | post-volume default gotcha; model flag meaning |
| **T7** `transitionTime` | `ssi1 default_night`, `ssi2 zm_factory`, `transitionTime 3`, flip at 20 s | sun/sky/exposure blend over 3 s, or snap | section 8 |
| **T8** scriptable light (optional) | one `scriptable` `ServerSide` light, `SetLightIntensity` 1 → 0.2 → 2 over time | visible change, or none | section 10 |

Then, in Tower II's own private workspace and only through the guarded build script: add `ssi2` = `ssi1` in the generator's `volume_sun`, FULL build, and have the user compare same-spot screenshots (for example the crown-hall spawn and the plaza, round 1) against the current build, with the `[TOD_LIGHTS]` log. That answers the section 15 doubt for this map directly.

## For Tower of Doom II

Recommendations only; nothing here changes code or data.

1. **Correct the record before designing.** docs/107, the comment near `tools/gen_tower_map.js:1546` and the v17.80 CHANGELOG.md entry say the 344 lights are "authored OFF before power". The stock evidence says they are ON in the state the game runs in. Fix the wording (and consider re-reading docs/107's conclusions with the State 2 `default_day` slot in mind) so the next session does not build on the misreading.
2. **Measure first.** Run T1-T2 in the control map (with the user's go-ahead), then the in-place `ssi2 = ssi1` A/B with a `[TOD_LIGHTS]` log. Filling `ssi2` is cheap insurance either way, but measure its bake cost.
3. **Decide the power story with THE FALL in mind.** Power now comes on at the start, so a "lights at power" reveal has no pre-power period to contrast with. Either reverse that decision (docs/160_the_fall.md §6 lists it as reversible) and build section 14.1, or key the lighting beats to events the descent does have: the Fall gate's seal, doors opening downward, and the ending once it is designed (the finale and the spire are parked under THE FALL, docs/160_the_fall.md §6).
4. **Adopt one convention and make it mechanical.** Recommend the Giant convention, with named mask constants (`ALWAYS`, `PREPOWER`, `POWERED`) in `light()` instead of one hard-coded `0,1,1,1`, `state_alias_1/2` labels in worldspawn, and a generator assert that every state a script can select has an SSI.
5. **Do progressive floor lighting with one progress clientfield** driving client-side FX lights (preferred: they spend no server entities) or grouped exploders (well under ~120), not with lighting states.
6. **Remember what states cannot touch.** The world's emissive faces glow the same in every state and at any power level; a dark look needs the emissive decision in [03_glow_and_perks.md](03_glow_and_perks.md), and switchable glow must live on entities.
7. **Tick `LIGHTSTATE_2`** (and whatever state the powered look uses) on every post, grade or performance volume ever added; their default is State 1 only.
8. **Keep it hot-join safe.** Drive every client-side light, exploder, glow swap and bank change from a clientfield callback, as `todPerkGlow` already does; never rely on one-shot server calls or client notifies for lasting state.
9. **Every state, light, SSI, volume or material change is a FULL build** in the private workspace (C:\BO3Tools\TOD2Cybercity), never the shared Mod Tools root; build and stop, the user tests.

## Sources

Official Treyarch documentation (MODTOOLS/docs_modtools):
- Lighting_Parameters.pdf p.10 (Lighting States), p.12 (auto-exposure keys incl. evmin1..4/evmax1..4/evcmp1..4)
- SunSky_Light_SetUp.pdf p.1 (sun volume as global probe; lighting states; ssi vs ssi_runtime_override), p.16 (Export Local Probes), p.17 (bake override recipe)
- FX_Lights.pdf p.1 (FX light setup, exploders, Stop vs Kill), p.2 (Never shadows unavailable; per-instance overrides)
- Generate_LED.pdf (when a new LED is needed)
- Materials.pdf p.17 (lampshade/backlit rationale), p.18 (HDR scale 2^EV)
- Multiplayer_Lighting_Workflow.pdf p.2 (overrides), p.3 (exposure and visibility)
- bo3_scriptapifunctions.htm (SetLightingState, GetLightingState, CreateStreamerHint, SetLightingOnly, SetLight*, MakeLight, radiant exploder functions, bank functions, VisionSetNaked, MapShaderConstant, setshaderconstant, SetMaterialOverride, ClearMaterialOverride)

Stock data and scripts (MODTOOLS):
- bin/t7.def.json (light, build_light, fx, volume_sun, misc_model/script_model/script_brushmodel, volume_worldfog/litfog, vbloom/vlut/vcolor/pbg volumes, volume_performance, volume_exposure, reflection_probe, worldspawn)
- bin/Radiant_modtools.exe strings (per-state probe/sun data, NO BAKE STATE, sun volume state support, exploder manager, Total Exploders 0/120)
- share/raw/scripts/zm/zm_usermap.gsc:110, 446-455; zm_usermap.csc:84, 107-116
- share/raw/scripts/shared/util_shared.gsc:1390-1398, 2968-3005; load_shared.gsc:55, 60
- share/raw/scripts/zm/gametypes/_globallogic_spawn.gsc:206, 501; _globallogic.gsc:258, 1764-1812; _zm.gsc:3253-3263; _zm.csc:335, 353-370, 390-396
- share/raw/scripts/zm/_zm_power.gsc:54-125, 157-170, 184, 474-517, 692-698, 723-760
- share/raw/scripts/zm/zm_giant.gsc:95-101, 132, 420-432, 524-590; zm_giant.csc:54-149; zm_giant_fx.csc:160-292; zm_giant_teleporter.gsc:744
- share/raw/scripts/zm/_zm_ai_wasp.csc:29-61 (world clientfield `toggle_on_parasite_fog` switching fog banks)
- share/raw/scripts/shared/exploder_shared.gsc:237-263, 275-285, 655-672, 755-830, 890-912; exploder_shared.csc:295-425
- share/raw/scripts/zm/_zm_traps.gsc:445-477; _zm_perk_quick_revive.gsc:155-190, 791; _zm_perks.gsc:113-161, 280-318; _zm_perks.csc:193-262; _zm_perk_juggernaut.gsh; _zm_perk_juggernaut.gsc:70; _zm_perk_juggernaut.csc:32-38; _zm_perk_deadshot.gsc:61; _zm_perk_electric_cherry.gsc:97; _zm.csc:114 (`level.enable_magic`)
- share/raw/scripts/zm/_zm_perk_random.csc:95-120 and _zm_perk_random.gsh (Wunderfizz shader constants)
- share/raw/techsetdefs_stable/geometry/lit_emissive_script.techsetdef
- map_source/_prefabs/zm/zm_giant/zm_giant_light.map (543 lights, state patterns, twin pairs, exploder lights, fxstate PaP key, state_alias_2 power_off, volume_sun ssi1/ssi2)
- map_source/_prefabs/zm/zm_core/vending_*_struct.map and vending_weapon_upgrade_spawnable.map (49 perk/PaP prefab lights, all 0000; exploder memberships); power_switch.map
- map_source/_prefabs/mp/mp_sector/mp_sector_light.map (ssi1 only; 5 of 275 lights at 0111)
- rex/templates/ZM Mod Level/ (template volume_sun ssi1 only, file possibly edited locally; template.gsc has no lighting call)
- source_data/ssi.gdt (default_day, default_night values); share/raw/maps/zm/zm_giant.led, zm_test_map.led (per-state SSI tables)

This repo:
- tools/gen_tower_map.js (`light()`, `volume_sun`, worldspawn state aliases, the comment near line 1546)
- map_source/zm/zm_tod2_cybercity.map (344 lights, masks, volume_sun keys, the two misc_prefabs; parsed 2026-09-24)
- share/raw/fx/acc/light/fx_perk_glow_*.efx (one `dynamicLight2` each, with `lightingstate1..4` keys)
- scripts/zm/zm_tod2_cybercity.gsc:247; scripts/zm/zm_tod2_cybercity/_tod_fall.gsc; _tod_perk_lights.gsc/.csc; _tod_rampage.gsc; _tod_atmosphere.gsc
- docs/107_sun_volume_yellow_postmortem.md:30-31, 57, 62; docs/160_the_fall.md §2, §3, §6; docs/154 (isolation); CHANGELOG.md (v17.80 entry, 2026-09-05); CLAUDE.md
- C:/BO3Tools/TOD2Cybercity/share/raw/maps/zm/zm_tod2_cybercity.led (per-state SSI table)

Map One and the control map:
- c:/Users/jorda/Repositories/abandoned_cyber_city_zombies/scripts/zm/zm_abandoned_cyber_city.gsc:956-973 (CheckForPower); map_source/zm/zm_abandoned_cyber_city.map:10071-10083 (volume_sun); CHANGELOG.md:52-70, 17225-17250, 17565-17595 (incl. the stale-BSP lesson at 17571-17577), 18266-18290
- c:/Users/jorda/Repositories/test+map, commit 1db8a3f (zm_test_map step 2)

Community:
- https://forum.modme.co/wiki/threads/1077.html (script 0-3 = Radiant 1-4)
- https://forum.modme.co/wiki/threads/3395.html (state 2 worked once ssi2 was set)
- https://steamcommunity.com/app/455130/discussions/0/340412619134508371/ (ssi2 = ssi1; power-light recipe)
- https://steamcommunity.com/app/455130/discussions/0/2592234299570231550/ (default_day blocked state changes; zm_factory in ssi1 and ssi2)
- https://steamcommunity.com/app/455130/discussions/0/350543951935346956/ (set_lighting_state 0 at start, 1 at power)
- https://www.ugx-mods.com/forum/mapping/88/how-to-get-lights-to-activate-by-power-being-turned-on/13041/ (dissenting account)
- https://www.ugx-mods.com/forum/mapping/92/perk-lighting-effects-fix-video-tutorial/13226/ ; https://steamcommunity.com/app/455130/discussions/0/2333276539589995175/ (perk prefab light fix)
- https://forum.modme.co/wiki/threads/2029.html, 871, 3412, 3642, 571, 1950 (exploders vs light API; per-light exploders; dissent)
- https://forum.modme.co/wiki/threads/2118.html (power-on stutter is hint strings)
- https://wiki.zeroy.com/index.php?title=Call_of_duty_bo3%3A_ZM_Exploders (exploder tutorial)
- https://www.youtube.com/watch?v=hPweAEu8zJY (VerK0 lighting part 1: SSIs, overrides per state)
- https://github.com/MattFiler/zm_alien_isolation (four-state community map)
