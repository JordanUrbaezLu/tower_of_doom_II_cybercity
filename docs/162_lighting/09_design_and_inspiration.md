# 09 — Designing light for a dark zombies map — and what Glass Tower does

**In short.** A dark map is not a map with the lights turned down. It is a map where the camera is held at a set exposure, where most of the screen sits a little below that exposure, and where a few deliberate, motivated pools, glows and silhouettes sit at or above it. In zombies the first job of light is readability: the player has to see a zombie coming, and has to know where to go next. This chapter turns the design principles into concrete choices, with numbers from Treyarch's own dark maps and from Tower of Doom II as it stands today. It then takes Glass Tower apart: what the map is, what its look is built from, and what we can borrow. The chapter ends with a list of maps and tutorials worth studying and a repeatable way to judge lighting, including the fact that the user's own graphics settings hide several lighting features. Nothing here was tested in game.

**Read this when…** you are deciding *what* the map should look like before touching keys: planning the power-on moment, choosing colours per floor, placing lamps, reacting to "it looks like Glass Tower, can we do that?", or setting up a lighting playtest.

## Contents

1. [The design problem in plain words](#1-the-design-problem-in-plain-words)
2. [Ten principles, made concrete for zombies](#2-ten-principles-made-concrete-for-zombies)
3. [What Treyarch's own dark maps do, in numbers](#3-what-treyarchs-own-dark-maps-do-in-numbers)
4. [Glass Tower](#4-glass-tower)
5. [Other maps praised for lighting](#5-other-maps-praised-for-lighting)
6. [Community tutorials and threads](#6-community-tutorials-and-threads)
7. [How to judge lighting](#7-how-to-judge-lighting)
8. [For Tower of Doom II](#for-tower-of-doom-ii)
9. [Sources](#sources)

Tags used: [VERIFIED] read in an official Treyarch doc, stock script, stock data file, or the engine API list (in §4.1 and §5 it also covers facts read directly from Steam's own Workshop API or from a map's published source file; "by parse" means counted by a script over the file); [COMMUNITY] forum, tutorial, video, other mapper, or this project's own recorded observation ("project record"); [INFERRED] reasoned, not seen; [TEST] needs an in-game test. MODTOOLS = `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130`.

---

## 1. The design problem in plain words

**Darkness is relative to the camera.** BO3's camera auto-exposes like a phone camera: it measures the scene and picks an exposure value (EV) inside a clamp, `evmin..evmax`, pushed "up or down" by `evcmp` [VERIFIED] (src: docs_modtools/Lighting_Parameters.pdf, auto-exposure section; deffiles/ssi.awi). Read EV the photographer's way: it names how bright a place is (Treyarch's sunlit exterior is EV 12, an interior 11 or lower), so exposing the *same* scene at a *higher* EV makes the picture *darker* [VERIFIED] (src: docs_modtools/Multiplayer_Lighting_Workflow.pdf §5; Materials.pdf p.18). Which way a positive `evcmp` pushes, and whether the clamp applies before or after it, is not documented [TEST] (see [05 §5.5](05_sun_sky_exposure_fog.md#55-which-way-does-evcmp-push-unverified)). If the clamp is wide, a dark room is simply brightened back up and reads grey and flat [INFERRED; the stock night SSIs all clamp narrow, see §3]. So a dark map is made of two decisions: hold the exposure, then place light relative to it. The mechanics are in [05 — sun, sky, exposure, fog](05_sun_sky_exposure_fog.md).

**"Make it feel dark, but don't actually make it dark."** The Level Design Book calls this "Hollywood darkness" [COMMUNITY] (src: https://book.leveldesignbook.com/process/lighting/darkness). The feeling of darkness comes from contrast: deep shadow next to a lit pool, a dark figure against a bright sky. A uniformly dim map is not scary; it is just hard to see.

**Treyarch's own tolerance is small.** In its multiplayer lighting workflow, Treyarch keeps the whole map within about 1.5 stops of exposure (some maps 2.5, with gradual transitions), makes the main gameplay space of an interior only about 1 stop darker than the exterior ("corners and occluded areas will go darker"), and says: "as soon as exposure drops 2 or more stops below the scene exposure, visibility will start to become a problem" [VERIFIED] (src: docs_modtools/Multiplayer_Lighting_Workflow.pdf §5). That is a multiplayer rule: MP exposure is always set within EV 8–12, while the stock zombies night SSIs clamp far lower (`default_night` 3–3.5, `zm_factory` 0.5–3.5, `zm_zod` 4–6) [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf §5; source_data/ssi.gdt). But the visibility warning is about the *gap* between a space and the exposure, and that part carries over to zombies [INFERRED].

**What one "stop" means.** Light brightness in BO3 is written in stops [VERIFIED] (src: Lighting_Parameters.pdf, "Lighting units are in stops. Default Value: 11"). The Materials doc converts exposure to a linear scale as 2^EV [VERIFIED] (src: docs_modtools/Materials.pdf p.18), and stock prefab light values are exact log2 of round numbers, for example 7.9658 = log2 250 (40 lights in `zm_giant_light.map`) and 8.9658 = log2 500 (`light/zm_giant_teleporter.map`) [VERIFIED values] (src: map_source/_prefabs/zm/zm_giant/). So +1 stop almost certainly means twice as bright [INFERRED]. Every design number below uses that reading.

---

## 2. Ten principles, made concrete for zombies

Each principle below gives the idea in plain words, what it means in a zombies round, the evidence, and the BO3 lever. The TOD II notes describe the map as it stands in `map_source/zm/zm_tod2_cybercity.map` and `tools/gen_tower_map.js`.

### 2.1 Players must see zombies (readability comes first)

**The idea.** Every lighting choice is judged first by one question: can a player spot a zombie at the distance where it matters (a sprinter at 20 m on a stair, a crawler at a doorway)?

**Evidence.**
- Valve, Left 4 Dead commentary (Chris Chin): "We had to find a light level that was atmospheric without striking players as frustrating or unfair … This simplified lighting also made it easier to read silhouettes, so that players could more easily tell Survivors from Infected." [COMMUNITY] (src: https://left4deadwiki.com/wiki/Developer_Commentary_(Left_4_Dead))
- Valve (Lars Jensvold): "We used a realistic dark fog, but this obscured character silhouettes … Once we lightened up the fog … the readability of characters greatly improved … Fog also helped players spot important events like zombies climbing over distant fences." [COMMUNITY] (same source)
- Treyarch: 2+ stops below scene exposure is where visibility becomes a problem [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf §5).
- Albedo floor: "No values below 40, none above 238. This leaves room for lighting" [VERIFIED] (src: docs_modtools/PhysicallyBasedRendering.pptx slide 10). Darkness should come from light, not from black textures. The Level Design Book says the same: "don't rely on dark albedo textures to darken the scene" [COMMUNITY].
- The global probe's `global_fill_color` defaults to `0 0 0`, "Occluded parts of the global probe will be filled with this color. Should match the average ground color." [VERIFIED] (src: bin/t7.def.json, volume_sun). The Giant also leaves it at `0 0 0`, and TOD II does not set it [VERIFIED] (src: zm_giant_light.map volume_sun; map_source/zm/zm_tod2_cybercity.map). A black fill is a candidate cause of pure-black occluded pockets on a map whose ground is not black [INFERRED].

**Zombie-specific levers.**
- **Eye glow.** In a dark map, glowing eyes are the cheapest way to show zombies approaching [INFERRED]. Stock gives two separate levers:
  - *The eye FX.* Stock zombies carry a client FX on `j_eyeball_le`; `zm_usermap.gsc:112` sets the default `zombie/fx_glow_eye_orange`. It can be overridden map-wide with `level._override_eye_fx`, or per zombie with `self._eyeglow_fx_override` (and the tag with `self._eyeglow_tag_override`) [VERIFIED] (src: share/raw/scripts/zm/_zm.csc:450-470).
  - *The eyeball material.* It is driven through the shader constant `scriptVector2` with an on/off luminance and a colour value, which script can override with `level.eyeball_on_luminance_override` / `level.eyeball_off_luminance_override` and `level.zombie_eyeball_color_override` / `self.zombie_eyeball_color_override` [VERIFIED] (src: _zm.csc:561-629, 660-697).
  - *Alternative effects.* `fx_glow_eye_blue`, `_green` and `_red` ship with the Mod Tools. A `_white` variant is also installed, but its file date (2026-07-24, the same day as a batch of third-party DLC-port effects) says it did not come with the base tools [VERIFIED file dates; origin INFERRED]. All are real effects, not placeholder stubs, and none contains a light element: they are sprite and line elements only [VERIFIED by file parse] (src: share/raw/fx/zombie/fx_glow_eye_*.efx).
- **Self-lit zombie art.** TOD's cyber zombie roster uses emissive-capable shaders (`lit_emissive_advanced_fullspec`) with "brighter eye cores" and emission normalised to scaleRGB 6 [COMMUNITY: project record] (src: CLAUDE.md, "CYBER EQUIPMENT FINISH V2" and cyber zombie MVP entries). How they read in a dark room has not been judged in game [TEST].
- **Do not count on shadows or ambient occlusion.** The user's own config has dynamic light and sun shadows off, SSAO off and `ActorShadows 0` (§7.3). Zombies will not get contact shadows on that setup, so readability has to come from brightness and colour contrast [INFERRED].

### 2.2 Pools and contrast, not even coverage

**The idea.** A few strong, well-placed pools separated by real shadow beat many weak lights spread evenly. Players read the pools; the gaps between them are where the dread lives.

**Evidence.**
- "Playtests proved that in a dark game, players will go wherever there's light. All we had to do was set up a few critical lights, and players are drawn to them like a moth to a bug zapper." [COMMUNITY] (src: L4D commentary, Chris Chin)
- "Don't apply flat ambient to all shadows; you want SOME shadows to terminate into 0% black" [COMMUNITY] (src: The Level Design Book, darkness page).
- Robert Yang (GDC 2018 "How to Light a Level"): "Don't light everything the same"; light the route and the set-pieces [COMMUNITY] (src: https://www.blog.radiator.debacle.us/2018/03/gdc-2018-how-to-light-level-slides-and.html).
- Radiator Blog: "The perceived brightness of a light depends on … the relative light level / darkness in the areas around that light." [COMMUNITY] (src: https://www.blog.radiator.debacle.us/2015/07/lighting-theory-for-3d-games-part-4.html)
- Map One (`abandoned_cyber_city_zombies`) worked to a palette rule of "~85% dark base; neon <15%" [COMMUNITY: project record] (src: Map One docs/20).

**What it looks like in numbers.** The Giant's lights are small and varied: radius median 150 (10th percentile 15, 90th percentile 350) and stops median 7 (10th–90th percentile about 4.0–10.6, with a few outliers from −32 to 14.6) [VERIFIED by parse] (src: map_source/_prefabs/zm/zm_giant/zm_giant_light.map). TOD II's 344 lights are all stops 6, and most are radius 420 (211 of them; the rest run 200–900) [VERIFIED by parse] (src: map_source/zm/zm_tod2_cybercity.map). The tower gets two identical r420 pools per lap, at the mid and end landings, in the district colour [VERIFIED] (src: tools/gen_tower_map.js:7217-7226). That is closer to even coverage than to pools [INFERRED].

**Pool arithmetic (starting points, not rules).** Put the key pool of a space near the exposure the camera will settle on; keep the main gameplay floor within about 1 stop under it and never 2 or more stops under; let corners and places nobody fights in fall darker than that [INFERRED from the Treyarch MP doctrine in §1 and the stock night numbers in §3]. How a light's `stops` value maps onto the scene's EV is not documented, so check the result with a locked-exposure comparison (§7.4), not by arithmetic [INFERRED]. Keys and units: [01 — lights](01_lights.md). Exposure: [05](05_sun_sky_exposure_fog.md).

### 2.3 Motivated light: every light has a visible source

**The idea.** A "motivated" light has a plausible fixture: a lamp, a sign, a screen, a fire, a window [COMMUNITY] (src: https://book.leveldesignbook.com/process/lighting). Players trust light they can explain. A glowing pool on a floor with nothing above it reads as a game marker, not as a place.

**Evidence.**
- Valve (Matt Campbell) removed the lit windows and streetlights from Left 4 Dead's city and lit scenes "from lower angles than they would expect — from car headlights and oil barrel fires. These dramatic angles really enhance the sense of a creepy, desolate, almost hopeless environment." [COMMUNITY] (src: L4D commentary)
- The Level Design Book: "A single fixture may actually motivate multiple invisible in-engine light sources." [COMMUNITY] One visible lamp can justify a key light, a fill light and a PROBE_ONLY bounce light.

**In BO3.** A lamp is three separate things that only look like one: the fixture model, something that makes the bulb glow (emissive material or glow FX), and a light entity for the surroundings [COMMUNITY] (src: VerK0 Lighting Tutorial Part 5). The step-by-step recipes are in [08 — fixture cookbook](08_fixture_cookbook.md). Treyarch's documented way to make a lamp cover that switches cleanly is a backlit "lampshade" material with a real light behind it, so that switching the light switches the look without having to "dial in and sync up a bunch of emissive materials" [VERIFIED] (src: docs_modtools/Materials.pdf p.17). See [03 — lampshades](03_glow_and_perks.md#6-lampshades-the-backlit-family).

**TOD II today.** No TOD II light is paired with a fixture. The map has zero `misc_model` entities, no Radiant `fx` entities and only two prefabs (the stock power switch and the Pack-a-Punch); machines and props are spawned by script. The lights sit at pool positions such as landing corners and room centres [VERIFIED] (src: classname tally of map_source/zm/zm_tod2_cybercity.map; tools/gen_tower_map.js `light()` call sites). In a cyber tower, the motivation can be neon trim, signs, screens, perk machines, teleporter pads, the Vault's window niches, the moon and the sky [INFERRED].

### 2.4 Colour that guides

**The idea.** Colour is a language. If red always means danger and green always means ready, players learn it in one round and read the map faster.

**Evidence.**
- Treyarch uses light as status. The Giant's teleporter map lights are exploders (`map_lgt_<pad>_red` / `_green`): they come on red when the power lights come on (`level waittill( "pl1" )`) and switch to green when each pad links. The Pack-a-Punch receiver light flashes while a link is attempted, and after the last link it waits `wait( 1.5 ); // dramatic pause` before going green [VERIFIED] (src: share/raw/scripts/zm/zm_giant_fx.csc:225-295). Shadows of Evil's robot call boxes use green, red and yellow exploder lights (`lgt_robot_callbox_green/red/yellow`) [VERIFIED] (src: our vendored scripts/zm/zm_zod_robot.csc:66-89).
- "If one kind of set-piece is lit a certain way, light every one like that" (paraphrase of Robert Yang's GDC 2018 talk) [COMMUNITY].

**TOD II today.** The tower already has a colour language. `DISTRICTS` gives each ten floors one hue (blue 1-10, green 11-20, orange 21-30, yellow/gold 31-40, red 41-50), and the generator comment says the door you buy is "the FIRST thing in the new colour — the 'one more floor' tell for free" [VERIFIED] (src: tools/gen_tower_map.js:1604-1621). The Vault puts "a RED lamp inside every window niche (the horde's door reads as a hazard from across the room)" [VERIFIED] (src: tools/gen_tower_map.js:7317-7319). The mechanism for switching status colours is exploders: [02 — exploders](02_power_and_states.md#9-exploders-named-light-groups).

**A caution.** Hue alone does two jobs here: district identity *and* hazard. Red is both "floors 41-50" and "the horde's door". When one colour means two things, the player cannot read either one [INFERRED]. Section 2.5 adds a second reason to be careful with red in TOD II.

### 2.5 Warm against cool (and what a red sky does to that)

**The idea.** The classic night scheme is cool ambient (navy, blue) with warm sources (fire, sodium lamps, headlights) that pop against it. Radiator Blog: the ambient is "often a dark navy color" [COMMUNITY]. The Level Design Book warns against "vanilla blorange" and suggests "introducing a third color or tweak hue ranges" [COMMUNITY].

**Treyarch does exactly this.** The Giant's sun SSI `zm_factory` is a dim, cool blue-grey (`colorSRGB 0.527 0.687 0.687`, stops -2) [VERIFIED] (src: source_data/ssi.gdt). Of its 543 lights, 469 are warm (red channel at least 0.2 above blue), mostly ambers like `1 0.7311 0.3922` and `1 0.749 0.451` [VERIFIED by parse] (src: zm_giant_light.map).

**TOD II inverts the ambient.** TOD II's sky is the "evil" theme: black-red, blood moon, solved to a sky-light score of 0.324 with a linear RGB share of 67/16/17, red-dominant [COMMUNITY: project record of the sky generator's output] (src: docs/150_tod2_evil_sky.md status line). The sky light is "a spherical light projected into the scene using the sky texture for value and color" [VERIFIED] (src: docs_modtools/SunSky_Light_SetUp.pdf; see [05 §4.3](05_sun_sky_exposure_fog.md#43-the-sky-as-a-light-skystops-and-skyrotation)), so the ambient on the open spiral will lean red [INFERRED]. Against red ambient, the colour that pops is the complement: cyan, teal, cold white. Red pools, red hazard lamps and the red 41-50 district will have less contrast against that ambient than against a navy one [INFERRED]. The Undercity already pairs cyan pools (`0.3 0.9 1`) with a warm spawn pool, an amber shelf light and red window lamps [VERIFIED] (src: tools/gen_tower_map.js:7320-7334). That is the right shape of palette for a red-lit world [INFERRED].

### 2.6 Silhouettes

**The idea.** A dark figure against a bright background reads instantly. A lit figure against a lit background disappears.

**Evidence.**
- Valve (Sean Keegan) "flip[ped] the typical lighting scheme, to put a bright sky behind dark buildings" [COMMUNITY] (src: L4D commentary). The same flip works for characters: The Level Design Book describes characters as "darker silhouettes vs. brighter horizon" and uses "Rim lighting to emphasize silhouettes while leaving most of the subject in shadow" [COMMUNITY].
- Glass Tower's own gameplay screenshots show zombies as dark shapes against a bright sunset and a glowing block (§4.2) [INFERRED: a reading of promotional screenshots].

**In a tower.** The spiral runs up the outside of the core, open to the sky [VERIFIED] (src: CLAUDE.md, "SPIRAL TOWER"). A zombie climbing the stair toward the player is seen against either the core wall or the sky, depending on the angle. Keep the sky band and the glowing parapet line *brighter* than the stair deck, so zombies silhouette against them [INFERRED]. Avoid lighting the stair treads so brightly that zombies are front-lit to the same level as their background [INFERRED].

### 2.7 Landmarks

**The idea.** In a dark map, the brightest thing on screen is where the eye goes. Use that: make the goal the brightest thing, and keep it visible from far away.

**TOD II has landmarks already.**
- The crown's exterior read "is carried by MATERIAL"; its three red lights exist only to make the red axis (beacon, great ruby, girandole) bloom, plus one warm wash in its mouth. The generator's reasoning: "A 900-unit light does nothing for a 4096-unit object" [COMMUNITY: project reasoning] (src: tools/gen_tower_map.js:7283-7298; CLAUDE.md "THE CROWN").
- The Endless Spire's beacon (mast top z=27584, its light at 27608) is "visible from the whole climb, deliberately" [COMMUNITY: project design record] (src: CLAUDE.md, Endless Spire; map_source/zm/zm_tod2_cybercity.map `spire_light_beacon`).
- TOD II's sky image carries a "TOWER OF DOOM II / CYBERCITY" neon sign under the moon [VERIFIED in the sky generator] (src: tools/gen_tod_sky.js:1270; docs/150_tod2_evil_sky.md). How it reads in game is untested [TEST].

**Rule of thumb.** A landmark must read in every lighting state, so it belongs to the always-on group when lights are split by power (see [02](02_power_and_states.md)) [INFERRED]. Large landmarks are carried by emissive material and bloom, not by light entities [COMMUNITY: project lesson above].

### 2.8 Power-on as a reward beat

**The idea.** Turning on the power is the first big reward in a zombies match. It should feel like an event: something the player caused, that changes the space. But if the whole map floods with light, the dread is gone and the rest of the match has nowhere to go.

**What Treyarch actually does (The Giant).**
1. Pre-power is **not** black. The Giant's own scripts set no lighting state at boot; the stock `zm_usermap::main` it calls sets script state 1, so it runs in script state 1 until power [VERIFIED] (src: zm_giant.gsc:132; zm_usermap.gsc:110). Under the strongly supported mapping (script state n shows Radiant State n+1) that is Radiant State 2 [INFERRED], the state its light prefab names `power_off` (`state_alias_2`) [VERIFIED] (src: zm_giant_light.map:31). At power it calls `set_lighting_state( 0 )`, i.e. Radiant State 1 [VERIFIED call; mapping INFERRED] (src: zm_giant.gsc:571). 261 of its 543 lights are on in every state [VERIFIED by parse]. 61 lights are on in Radiant State 2 but not State 1 (pre-power lights). 58 of those sit within 16 units of a light that is on in State 1 but not State 2 (a powered twin), and 54 of the 58 pairs have the identical colour. The powered twin is brighter by a median **1.0 stop** (the spread runs from −0.74 to +4.64) [VERIFIED by parse] (src: zm_giant_light.map). So Treyarch's "power on" mostly *raises* existing lamps by about a stop and adds new ones: 155 lights are on in State 1 but not State 2, of which the 58 twins are one part [VERIFIED by parse]. The design reading is "the room wakes up", not "the room appears" [INFERRED].
2. The power-on script is a staged, multi-sense sequence. When the `power_on` flag is set, a server thread sends client notify `pl1` [VERIFIED] (src: zm_giant.gsc:427-428). On `pl1` the client code swaps three families of lamp models to their lit versions (`light_model_swap`, e.g. `smodel_light_electric` to `lights_indlight_on`) [VERIFIED code] (src: zm_giant_fx.csc:69-71, 184-198), although no entity with those names exists in the shipped Giant map sources, so that swap has nothing to act on in the files we have [VERIFIED absence], and turns the teleporter map lights red [VERIFIED] (src: zm_giant_fx.csc:229-231). The sound side plays a 2D power-up sound (`evt_power_up_2d`), a start click plus a looping electrical buzz at every lamp position (`evt_light_start`, `amb_light_buzz` on the `dyn_light` structs), switch, generator and breaker sounds, and "crazy power" and "flip sparks" sounds at fixed spots [VERIFIED] (src: zm_giant_amb.csc:9, 35-95, 283-320). A PA power-on announcement exists (`pa_power_on`, :299-306) but its thread is commented out (:179), so it does not play [VERIFIED]. The server notifies each perk's power-on one network frame apart, *then* sets the lighting state, then fires the switch sparks one second later, and changes the music state 19 seconds later [VERIFIED] (src: zm_giant.gsc:550-590).
3. Status lights then change over the following minutes as the player links teleporters, including the 1.5 s "dramatic pause" (§2.4) [VERIFIED].

**Other evidence.**
- Stock usermap power changes no lighting at all. `_zm_power.gsc` has no lighting-state, exploder or vision call [VERIFIED] (src: share/raw/scripts/zm/_zm_power.gsc). A custom map has to author its own power-on lighting.
- Map One hid the instant lighting-state swap by dropping to a dark vision grade and lerping back to default over about 15 seconds [COMMUNITY: project record] (src: Map One `_acc_atmosphere.gsc:500-520`, docs/20). Its user walked the pre-power room light down from `bake_intensity_scale` 0.30 to 0.02, found even 0.02 "still too light... just do 0 until power", and the roofed rooms were then baked pure black until power. At the same time the open plaza was lit in every state as a "safe haven" ("almost pitch black INSIDE; feel safe OUTSIDE until power is on") [COMMUNITY: project record] (src: Map One tools/oneshots/gen_room_roofs.js:43-68). That is the clearest evidence of how dark this user likes a pre-power room, and of the shape they liked: a lit refuge next to black rooms.
- A frame hitch at power-on is usually the perk hint strings being registered, not the lighting [COMMUNITY] (src: https://forum.modme.co/wiki/threads/2118.html). This project already runs a triggerstring budget (CLAUDE.md, "TRIGGERSTRING BUDGET").

**How to build it.** A lighting state is set per player, but it switches every state-flagged light in the whole map at once, so it cannot light one area [VERIFIED for per-player; map-wide effect INFERRED] (src: share/raw/scripts/shared/util_shared.gsc:2975-3002; share/raw/scripts/zm/gametypes/_globallogic_spawn.gsc:501). Per-area reveals use exploders. Both are covered, with the two working conventions (Giant and Map One), in [02 — the two working conventions](02_power_and_states.md#4-the-two-working-conventions) and [02 — dark before power](02_power_and_states.md#141-recommended-design-dark-before-power-lights-at-power). A full reveal sequence is in [08 — the power-on reveal](08_fixture_cookbook.md#17-the-power-on-reveal-a-floor-going-from-dark-to-lit).

### 2.9 Per-floor identity in a 50-floor tower

**The idea.** On floor 37 the player should know roughly where they are without a HUD: by colour, by the kind of fixtures, by how dark it is. Each stretch of the climb should feel like a new district.

**What already exists.**
- Five colour districts of ten floors (`DISTRICTS`). Treads alternate `_tinted` / `_tinted_edge` per floor, and each breather lounge (floors 10/20/30/40) caps its district in its own colour (`BREATHER_THEME`) [VERIFIED] (src: tools/gen_tower_map.js:1615-1630, 2200-2205).
- Every lap's two pools are in its district hue (`lapPal(lap).light`) [VERIFIED] (src: tools/gen_tower_map.js:7217-7226).

**Levers for stronger identity (design options, all [INFERRED]).**
1. **A signature fixture per district**, not just a hue. For example: fluorescent tube strips (blue), hanging cage lamps (green), sodium street lamps (orange), sconces or chandeliers (gold), rotating alarm beacons (red). Recipes: [08](08_fixture_cookbook.md).
2. **A darkness curve.** Let the light budget per lap fall as the tower rises: denser pools low down, sparser and harsher toward floor 50, with the breather lounges as bright, warm havens between them. "Safe room bright, climb dark" is a pacing tool.
3. **One wayfinding colour that never changes.** If the "next door" cue is the district hue, it changes meaning every ten floors. A constant cue (for example a cold-white or cyan lintel light over every buyable door) stays readable in every district, and the district hue is then free to be pure identity.
4. **Lighting rhythm.** Light every landing in the low districts and every other landing higher up, so the rhythm itself changes.
5. **Budget.** Only four lighting states exist and each one is map-wide, so per-district reveals need exploders (see [02 — progressive per-floor lighting](02_power_and_states.md#142-recommended-design-progressive-per-floor-lighting-in-a-50-floor-tower)). Radiant's Exploder Manager holds the default text "Total Exploders: 0/120" next to a live format "Total Exploders: %d/%d" [VERIFIED strings] (src: bin/Radiant_modtools.exe), which suggests a cap of 120 exploders [INFERRED]. Plan groups per district or per lounge, not per floor. New fixture *geometry* costs lightmap atlas and the LED bake is a pass/fail gate here, so prefer models and FX over large brushes [COMMUNITY: project lesson] (src: docs/BO3_MAPMAKING_KB.md §1; CLAUDE.md).

### 2.10 Do not rely on what players can switch off

**The idea.** Volumetric shafts, dynamic shadows, SSAO and screen-space effects are graphics options. A map whose readability depends on them breaks for anyone who turns them off.

**Evidence.**
- BO3's `players/config.ini` has `VolumetricLightingEnabled` under the comment "Enable volumetric sun and light shafts", plus `DisableDynamicLightShadows`, `DisableDynamicSunShadows` and `SSAOTechnique` [VERIFIED] (src: the user's players/config.ini, §7.3). A community answer says lit fog (`volume_litfog`) also needs players to have volumetric lighting enabled [COMMUNITY] (src: https://forum.modme.co/wiki/threads/1869.html); no Treyarch source says so [TEST].
- A light is only volumetric if its own `volumetric` key is true (default false) [VERIFIED] (src: bin/t7.def.json, `light`). TOD II's generator never sets it, so no TOD II light is volumetric on any setting [VERIFIED] (src: tools/gen_tower_map.js `light()`).
- `shadowSplitDistance` on the sun volume controls the *dynamic* sun shadows ("Distance in inches that the split shadows (dynamics) render cover") [VERIFIED] (src: bin/t7.def.json, volume_sun). A player with `DisableDynamicSunShadows 1`, which is the user's setting, will not see changes to it [INFERRED].

**Rule.** Mood can use these features. Readability must survive them being off [INFERRED].

---

## 3. What Treyarch's own dark maps do, in numbers

These are the real values, side by side with TOD II, so a design conversation can start from data. The full key meanings are in [05](05_sun_sky_exposure_fog.md), [01](01_lights.md) and [06](06_reflections_probes.md).

| | The Giant (stock ZM) | Shadows of Evil (stock SSI) | stock `default_night` | TOD II today |
|---|---|---|---|---|
| Sun colour / stops | `0.527 0.687 0.687` (cool), −2 | `0.643 0.745 1` (cool blue) but sun **off** (`enablesun 0`), stops −2.5 | `0.791 1 1` (cool cyan), −2.2 | `0.791 1 1`, −2.2 (`tod_ssi_cybercity`, a `default_night` clone) — but only in `ssi1`; see the sun-volume row |
| Exposure clamp / evcmp (SSI) | EV 0.5..3.5, evcmp 4 | EV 4..6, evcmp 3 | EV 3..3.5, evcmp 2.5 | EV 3..3.5, evcmp 2.5 (in `ssi1` only) |
| Other exposure control | worldspawn `evauto 1, evmin 3, evmax 3.5, evcmp 2.5`; 3 `volume_exposure` zones (EV 0.5–3.5, evcmp 4.87/4.87/3.75) | – | – | none |
| Sun volume | `ssi1` = `ssi2` = `zm_factory`; `target` → an `info_null` (places the global probe); `shadowSplitDistance` 900 | – | – | `ssi1` only (plus a non-def key `ssi`); no `ssi2`, and the compiled `.led` pairs the unset states with `default_day`. The map boots in script state 1 = Radiant State 2 [INFERRED], so what it actually shows is [TEST]. No `target`: the global probe sits at the box centre (0, 0, 19478), inside the brush `mast tier 1` |
| Sky light (`skyStops`) | 3 | – | 4.4 | 10.0 (image solved to score 0.324) |
| Lights | 543: 280 omni, 263 spot; 353 shadow-mapped; 177 volumetric; 149 PROBE_ONLY | – | – | 344 omni, 0 spot, 0 shadowed, 0 volumetric, 0 PROBE_ONLY |
| Light stops / radius | median 7 (10th–90th percentile ~4.0–10.6) / median 150 | – | – | all 6 / mostly 420 |
| Light colour | 86% warm, mostly ambers | – | – | saturated district and theme hues |
| Lighting-state masks | 11 patterns; pre-power twins ~1 stop dimmer | – | – | one pattern, (0,1,1,1) |
| Reflection probes | 176, fitted to rooms, 102 with reflection planes | – | – | 53, all the default 144-unit cube |
| Fog / grade volumes | 3 `volume_litfog`, 4 `volume_worldfog` (per-state `fsi_1..4`, bank 2 = dog-round fog), 15 `pbg_box` all flagged `LIGHTSTATE_1` only, LUT `luts_t7_zm_factory` | – | – | none; tower fog forced off (`fog_off()`) |

Sources: source_data/ssi.gdt; model_export/t7_skybox.gdt and t7_techart_props.gdt; map_source/zm/zm_giant.map worldspawn; map_source/_prefabs/zm/zm_giant/zm_giant_light.map (parsed); map_source/zm/zm_tod2_cybercity.map (parsed); the compiled `share/raw/maps/zm/zm_tod2_cybercity.led` in the private workspace (SSI names); source_data/tod_skybox.gdt; scripts/zm/zm_tod2_cybercity/_tod_atmosphere.gsc — all [VERIFIED] as data. The Giant's worldspawn exposure keys are documented in Lighting_Parameters.pdf but are not declared in bin/t7.def.json, and how worldspawn, SSI and `volume_exposure` values take precedence is not documented [INFERRED].

What the numbers say [INFERRED]:
- Treyarch's night recipe is **a cool, weak moon, a dim sky, a narrow exposure clamp, and many small warm pools**. Shadows of Evil goes further and switches the sun off. The Giant's grade boxes are flagged for Radiant State 1 only, which under the mapping means they switch on with the power.
- TOD II has the stock night *sun and exposure* in `ssi1`, but its sky light is about 5.6 stops higher than `default_night`'s (10.0 vs 4.4). How much light the sky actually throws also depends on the image content, so that comparison is approximate [INFERRED] (src: sun-sky data above; docs/104 §4 on the sky-light score). And because the map probably runs in Radiant State 2, whose SSI slot is empty, even the sun and exposure numbers in this column may not be what players see [TEST] (details: [05 §2.5](05_sun_sky_exposure_fog.md#25-lighting-states-on-the-sun-volume), [05 §2.4](05_sun_sky_exposure_fog.md#24-the-global-probe-and-target)).
- Where The Giant shapes light with spots, shadows, fitted probes and volumes, TOD II has one kind of light, no shadows, and probes that do not cover their rooms. TOD II's look comes mostly from its all-emissive architecture and the sky (see [03](03_glow_and_perks.md) and [06](06_reflections_probes.md)).

---

## 4. Glass Tower

### 4.1 Which map it is

The user almost certainly means **GLASS TOWER[HARD] by vuflub_**. The user should confirm by opening the link.

| Field | Value | Confidence |
|---|---|---|
| Workshop link | https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290 | [VERIFIED] (Steam Web API `GetPublishedFileDetails`) |
| Author | vuflub_ (SteamID64 76561198830040576, `steamcommunity.com/id/vuflub`) | [VERIFIED] |
| Created | 2026-09-15 05:37:13 UTC (the page shows "Sep 14 @ 10:37pm" Pacific) | [VERIFIED] |
| Size / reach | 1,640,878,004 B; about 6,040 current subscribers on 2026-09-23 and 6,067 (7,282 lifetime) on 2026-09-24; 10 author screenshots | [VERIFIED] |
| Status | API reports `visibility 0` (public) and `banned 0` | [VERIFIED] |
| Description | Difficulty, BO2 weapons, buyable ending, timed gameplay, two custom weapons, a credits list. **Nothing about lighting.** | [VERIFIED] |
| Installed on this PC | No (`steamapps/workshop/content/311210/3801980290` does not exist) | [VERIFIED] |

Why this one:
- MitchyPoo's video "The NEW Glass Tower Custom Zombie Map is SICK! (Black Ops 3)" (2026-09-15, ~21k views) links to this item and is the most likely origin of the user's "really really sick" [COMMUNITY] (src: https://www.youtube.com/watch?v=nvQY3ThaI3c).
- Satchino's "The Glass Tower Zombies Map Is AGONY" (~23k views) also links to it. Its only visual comment is "The skybox looks beautiful" [COMMUNITY] (src: https://www.youtube.com/watch?v=bDsOuc3zSHM).
- A commenter under MitchyPoo's video asked him whether he had played "Tower of Doom: Cybercity", the user's own map [COMMUNITY].

The other candidate, "Glass Tower Challenge" by "Missing" (id 3260903112, 2024, 52 subscribers, marked WIP), is very unlikely [VERIFIED facts; the conclusion is INFERRED].

Note for future agents: every Workshop page's HTML contains a hidden `bannedNotification` block ("This item has been removed…") with `style="display: none"`. Reading that text as "the item was removed" is a misreading; use the API's `banned` and `visibility` fields [VERIFIED] (src: saved page HTML).

### 4.2 What its look is built from

The visual evidence read for this chapter is the author's 10 promotional screenshots (the YouTube footage in §6 was not studied frame by frame). At least one (the title card) has overlay text, and one is an end-of-game score screen, so colour grading or other post-processing cannot be ruled out. Everything in this list is a reading of those images [INFERRED], not a statement about how the map renders on a given PC.

1. **The sky does most of the work.** A sunset-and-space skybox: a low sun behind orange and gold lit clouds, a dark teal zenith, a large Earth-like planet, a large gold moon, and a smaller moon. Nearly every good shot is framed against it.
2. **Mirror-like surfaces repeat the sky.** Floors and tower faces reflect the sunset almost like mirrors. In one shot a platform floor shows the full sun with cloud shapes and the reflection of a nearby prop. The "glass" in the name reads as smooth, highly reflective surfaces.
3. **A water plane** surrounds the base, carrying a sun-glint streak and magenta reflections of the trim.
4. **Saturated emissive edge trim.** Magenta and violet lines outline every zigzag platform and the tower edges, on otherwise dark grey surfaces with blue grid lines.
5. **Heavy bloom and a violet cast.** The trim has wide glow halos, and weapons, hands and zombies carry a violet tint.
6. **Warm against cool.** The orange sun and sky against magenta, violet and blue trim and faces: complementary colours.
7. **Landmark props.** Giant glowing rainbow-gradient perk bottles stand in the water and on platforms.
8. **Readable zombies.** In the gameplay shots, zombies read as dark shapes against the bright sky and a glowing block.

The author's other towers (AURORA ASCENSION with a lava sky, NEBULA TOWER with cyan neon in space, SPACE TOWER in Earth orbit, BATTLE TOWER with a cloudy sunset) suggest a house style: **one strong themed skybox plus neon edge outlines on a narrow tower in a void** [INFERRED from the Workshop preview images].

### 4.3 What it does not have to solve

Glass Tower is an open void with almost no interiors [INFERRED from screenshots]. It never has to deal with dark rooms, light leaking through walls, or a staged power-on. So its lessons apply to TOD II's **open-air spiral, crown and sky**, not to the Undercity, the Vault or the workshop wings. Its style is still close to ours: TOD II's spiral is also an open-air tower in a sky void with Tron-grid neon trim (the glowing-seam `_tinted_edge` floors) [VERIFIED in the generator] (src: tools/gen_tower_map.js:1600-1640; CLAUDE.md "Tron Grid look"). A stylistic match only: nothing shows that Glass Tower uses the same vertigo material pack, and its credits do not list that pack's author [INFERRED].

### 4.4 What we can borrow, and how

| Glass Tower ingredient | BO3 lever | TOD II today | Where to read |
|---|---|---|---|
| A dramatic sky that carries the frame | sky image + SSI sun direction/colour + `skyStops` | Self-rendered sky (`tools/gen_tod_sky.js`, themes `night`, `evil`, `sunset`); `skyStops 10.0`; the image gain is solved so the sky light lands at score 0.324 (`--target-score` default) [VERIFIED] (src: tools/gen_tod_sky.js:147; source_data/tod_skybox.gdt) | [05](05_sun_sky_exposure_fog.md) |
| Bright visible sky without a bright world | Keep the *sky light* low (`skyStops`, image gain) and control the *visible* sky separately with worldspawn `sky_intensity_factor0/1` (0..10; "sky color will be multiplied by this value", interpolated by view angle between `sky_intensity_angle0/1`) [VERIFIED key] (src: bin/t7.def.json worldspawn). Or bake with a neutral SSI in `ssiN` and show the look through `ssiN_runtime_override` ("ssi_runtime_override is what will be displayed in game and ssi is what will bake into the reflection probes") [VERIFIED] (src: SunSky_Light_SetUp.pdf). Treyarch warns that pushing the override too far makes "your reflections … not match the visible sky" [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf §3) | `sky_intensity_factor` 1/1; no runtime override. Whether raising the factor above 1 brightens the visible sky without touching the bake is [TEST] | [05 §4.4](05_sun_sky_exposure_fog.md#44-dimming-the-visible-sky-only-sky_intensity_factor), [05 §2.6](05_sun_sky_exposure_fog.md#26-bake-one-look-display-another-the-override-trick) |
| Mirror floors that repeat the sky crisply | Reflective materials plus reflection probes **fitted to each space** (box probes are parallax-corrected to their box) | The vertigo materials are already mirrors (`lit_emissive_advanced`, `colorMap $white_diffuse`, `specColorMap $white_specular`, no normal map, `reflectionProbeAmount 1`) [VERIFIED] (src: source_data/_emox/emox_mwiii_vertigo_assets.gdt), but all 53 probes are the default 144-unit cube [VERIFIED]. The project reads that as the cause of smeared reflections [COMMUNITY: project record]; untested [TEST] | [06 — the fix plan](06_reflections_probes.md#153-the-fix-plan) |
| Neon edge trim on dark surfaces | Emissive materials; HDR Scale (`scaleRGB`) ≈ 2^EV of the area [VERIFIED rule] (src: Materials.pdf p.18) | All 66,402 visible faces are emissive-class. About half glow only on thin grid lines; the other half have a grey fill that glows over the whole face [VERIFIED]. The vertigo materials run `scaleRGB` up to 15 against the SSI's EV 3–3.5 (2^EV ≈ 8–11.3), so the brightest sit above the doc's value [INFERRED comparison] | [03 §3](03_glow_and_perks.md#3-how-bright-hdr-scale-and-the-2ev-rule), [03 §11](03_glow_and_perks.md#11-tod-iis-all-emissive-world) |
| Heavy bloom | `pbg_box` with `USE_BLOOM` and a shipped `.lvi` preset; emissive HDR scale; bright peaks in the sky image. No `.lvi` editor ships [INFERRED]. The Giant's 15 bloom/grade boxes are all flagged `LIGHTSTATE_1` only [VERIFIED by parse]. A worldspawn `bloom` key appears in The Giant's `zm_giant.map` (`bloom zm_factory`) and in VerK0's tutorial, but it is not in t7.def.json; its effect is [TEST] | No bloom volume. The sky has a peak knee because bright pixels bloomed white [COMMUNITY: project record, docs/104 §4k] | [05 §7](05_sun_sky_exposure_fog.md#7-colour-lut-grade-boxes-bloom-vision) |
| Water with sun glint | `lit_water_sim` family materials; material screen-space reflection exists only on the water family [VERIFIED] | No water | [07](07_water.md) |
| Complementary colours | Sun colour vs trim colour | Red-dominant sky; the complement is cyan/teal (§2.5) | this chapter |
| Glowing landmark props | Emissive models, optionally with an FX light | The crown, the mast beacons, the sky sign | [03](03_glow_and_perks.md), [04](04_fx_lights.md) |

**A sunset is a mood decision.** The user asked for a *dark* map and also asked how to do sunsets. Glass Tower is a sunset map. A sunset reads well because the sun is low and warm, sun and sky are close in brightness (`default_sunset`: sun stops 11 vs sky 10.15), and the exposure clamp is wide and bright (EV 8..12.5) [VERIFIED values] (src: source_data/ssi.gdt; t7_techart_props.gdt). That is the opposite of a night map. A sunset on TOD II would be a new SSI and a new sky, not a tweak, and the user should choose it deliberately [INFERRED]. The sky generator already has a `sunset` theme next to `night` and `evil` [VERIFIED] (src: tools/gen_tod_sky.js:166-214). Recipe: [05 — a sunset](05_sun_sky_exposure_fog.md#8-recipe-a-sunset).

**The user's taste on reflections.** On the heavenly altar the user rejected an all-matte pass (zero specular, zero reflection-probe contribution) and wanted *less* gloss, not none; the project rule since then is never to restore that all-matte pass [COMMUNITY: project record] (src: CLAUDE.md, 2026-09-16 altar entries). That fits a Glass Tower-style reflective finish.

### 4.5 What we cannot know yet

- The map's SSI, exposure, probe and material values. It is not installed, and a compiled fastfile would not expose them readably anyway [INFERRED].
- Whether its mirror floors are probe cubemaps, a water-family material with screen-space reflection, or both. Material SSR (`useScreenspaceReflection`) is exposed only by the `lit_water_sim` family and the `water_shore` techsets [VERIFIED] (src: share/raw/techsetdefs_stable; see [07](07_water.md)), and a floor that reflects a nearby prop sharply could be either [TEST].
- Whether the screenshots were post-processed [TEST].

How to find out: the user confirms the link, subscribes, and takes same-spot screenshots on both graphics configs (§7). Point at the exact moments they love. The agent can then compare those against the stock SSI tables.

---

## 5. Other maps praised for lighting

| Map | What people said | Documented technique | Confidence / source |
|---|---|---|---|
| **47 Berkerly Lane** (VerK0, ws 2061599899) | "This level by far has probably the best lighting I have ever seen from a custom map"; the top floor "extremely bright and warm", the sewer "slightly bright while making it not too bright" | The author made the five-part lighting tutorial series in §6. He bakes with an SSI 1.5 stops brighter than the runtime override (12.5 vs 11) to lift bounce and soften shadows, uses `shadowSplitDistance` 750, and puts a purple `PROBE_ONLY` light in the PhD Flopper room | [COMMUNITY] (src: https://ga663404929.wordpress.com/2020/05/30/47-berkerly-lane-the-best-custom-map-of-all-time/ ; VerK0 Parts 1 and 5) |
| **Leviathan** (JBird632, HexZombies, Awesome Pie) | "a visual identity that's simply breathtaking" (GameRant, 2025) | JBird632: "my map's a dark map"; lens flare off; a much brighter second SSI swapped in from script for lightning flashes | [COMMUNITY] (src: https://gamerant.com/black-ops-3-bo3-zombies-best-custom-maps-2025/ ; https://www.youtube.com/watch?v=jAmmmDvZp_A) |
| **Alien Isolation Zombies** (MattFiler, 2016, source on GitHub) | No lighting praise found; included because it is a shipped map with public source | 342 lights (238 spot, 104 omni; 158 shadowed; 169 volumetric); 4 lighting states (22 lights only in state 4, the red alert); one sun volume with distinct `ssi1/2/3` (spawn, lights-out, power-on) while two others use one SSI for all states; 23 room-fitted probes at `brightnessAdjust -5` / `evcomp -5`; custom LUT `luts_ayz` | [VERIFIED] as data (src: https://github.com/MattFiler/zm_alien_isolation, `map_source/zm/zm_alien_isolation.map`) |
| **Gasse der Toten – Remastered** (NonSpecific, ws 2613398867) | "This is One Of The Best Looking BO3 Custom Zombies Maps I've Ever Played" (Spuddley video title) | none documented | [COMMUNITY] (src: https://www.youtube.com/watch?v=FdgW7EHSloA) |
| **Halle Der Toten** (h00dedsn1per177) | "everything's dark, dreary, and terrifying" | none documented | [COMMUNITY] (src: GameRant 2025, above) |
| **Lostplace** (dreamzyy) | "such a beautiful map" | The author released his usable flashlight (FX, scripts, sounds) | [COMMUNITY] (src: modme thread 1213) |
| **Elevation** ("Jay") | The skybox moon "shine[s] a nice white volumetric light" | Cover the map with `volume_litfog`; players must enable volumetrics | [COMMUNITY] (src: https://forum.modme.co/wiki/threads/1869.html) |
| Maps by **Madgaz** and **Xela** | Named as using LUTs in "professional BO3 maps": "LUT can make a HUGE difference" | LUT colour grading | [COMMUNITY] (src: https://forum.modme.co/wiki/threads/3135.html) |
| **The 115 Caves** (Zindea) | "creates genuinely scary moments when your flashlight is the only thing…" | flashlight-driven darkness | [COMMUNITY], weak (an unsourced listicle, https://www.ofzenandcomputing.com/best-custom-bo3-zombies-maps/) |

Stock references you already own (data, not praise): **The Giant**, whose full light prefab ships at `map_source/_prefabs/zm/zm_giant/zm_giant_light.map`, and **Shadows of Evil**'s sunless SSI `zm_zod` [VERIFIED].

Not included because it could not be verified: a search summary claimed "1938: Full Circle" asks players to enable volumetric lighting; the page was not found.

---

## 6. Community tutorials and threads

One line each. Tags: [COMMUNITY] throughout. The chapter that uses each link is in brackets.

**Video tutorials**
- https://www.youtube.com/watch?v=hPweAEu8zJY — VerK0 Part 1: sun volume, vista volume, SSI vs runtime override, shadow split, per-state overrides. [05, 02]
- https://www.youtube.com/watch?v=8j7_EjLVFJA — VerK0 Part 2: LUT colour correction and bloom through a pbg box. [05]
- https://www.youtube.com/watch?v=EyIqeAufdFc — VerK0 Part 3: world, atmospheric and lit (volumetric) fog. [05]
- https://www.youtube.com/watch?v=HOa08arAXlk — VerK0 Part 4: reflection probes (fitting, subtract/override, density, bounce count). [06]
- https://www.youtube.com/watch?v=VPT3TJzbQPc — VerK0 Part 5: lights (two-light lamp, spot shaping, `bulbLength`, cookies, PROBE_ONLY, culling). [01, 08]
- https://www.youtube.com/watch?v=jAmmmDvZp_A — JBird632 Part 21 "SSI and Lighting": a dark map's SSI, omni/spot, volumetrics, SSI swap for lightning. [05]
- https://www.youtube.com/watch?v=beP7zrpUCwI — Program115: omni and spot light basics. [01]
- https://www.youtube.com/watch?v=nYCPEJfmuS4 — Uptownpapi25: fixing light leaks at edges and corners. [10]
- https://www.youtube.com/watch?v=yA7_oukGY9o — Uptownpapi25: fixing lights and adding reflection probes. [06]
- https://www.youtube.com/watch?v=HHB_EReWtCw — Graffiti Designs: perk lights via `set_lighting_state` (0 then 1). [02]
- https://www.youtube.com/watch?v=6tNSZxBgsc0 — Madgaz: volumetric lights for beginners. [01, 05]
- https://www.youtube.com/watch?v=ybzQQ0tZxV4 — UGO/Wakka: sun cloud-caustic cookie for moving cloud shadows. [05]
- https://www.youtube.com/watch?v=RpHr5Np5rTc — IceGrenade: custom skybox import (EXR, HDRI sources). [05]

**Written guides and archives**
- https://github.com/IceGrenade/bo3/blob/master/wiki/lightstates — IceGrenade wiki: "0=1, 1=2" lighting-state mapping and "give it an ssi 2". [02]
- https://icegrenade.co.uk/tutorials — index of IceGrenade's lighting, sky and LUT tutorials (not individually checked). [05]
- https://wiki.zeroy.com/index.php?title=Call_of_duty_bo3:_ZM_Exploders — Exploder Manager to script, step by step. [02]
- https://forum.modme.co/wiki/threads/2642.html — AnUncleanHippy's Advanced Lighting Tutorial and sample map (the body did not load when fetched). [01]
- https://wiki.modme.co/wiki/black_ops_3/basics/Setting-up-water.html — modme wiki water setup (three-part model; see the corrections in [07](07_water.md)). [07]
- https://github.com/dtzxporter/ModmeForum — the whole modme forum archived as markdown (~3,400 threads); grep it. [all]
- https://github.com/MattFiler/zm_alien_isolation — a shipped map's full source with multi-state lighting. [02, 06]

**Forum threads**
- https://forum.modme.co/wiki/threads/330.html — lighting-state recipe (three light groups, `ssi1`/`ssi2`) and "states seem really glitchy". [02]
- https://forum.modme.co/wiki/threads/1077.html — script state 0–3 = Radiant 1–4 explained. [02]
- https://forum.modme.co/wiki/threads/2029.html — Harry Bo21: exploders are how you script lights. [02]
- https://forum.modme.co/wiki/threads/472.html — ticking lighting states inside perk prefabs. [02, 03]
- https://forum.modme.co/wiki/threads/477.html — Psh: under a day SSI a light needs about 14 stops to show at all, while a night map sits around 1 (numbers as posted). [01]
- https://forum.modme.co/wiki/threads/360.html — sun bleed fixed with `shadowSplitDistance` 250–300. [10]
- https://forum.modme.co/wiki/threads/2118.html — the power-on hitch is hint strings, not lights. [02]
- https://forum.modme.co/wiki/threads/3135.html — colour correction: SSI knobs vs LUT. [05]
- https://forum.modme.co/wiki/threads/1883.html — flashing omni lights with custom FX. [04]
- https://forum.modme.co/wiki/threads/1928.html — sweeping searchlights must be FX, not lights. [04, 08]
- https://forum.modme.co/wiki/threads/2868.html — darkening a night sky with smaller stops / exposure comp. [05]
- https://steamcommunity.com/app/455130/discussions/0/2592234299570231550/ — `default_day` in the sun volume blocked state changes; `zm_factory` in ssi1 and ssi2 (the same SSI in both) fixed it. [02]
- https://steamcommunity.com/app/455130/discussions/0/350543951935346956/ — `set_lighting_state(0)` at start, `(1)` at power. [02]
- https://steamcommunity.com/app/455130/discussions/0/135514507322573601/ — pitch black after publishing (export lighting; keep the .xpak). [10]
- https://steamcommunity.com/app/455130/discussions/0/3424437779948829805/ — making a fully dark room (probes plus `caulk_shadow`). [10]
- https://www.ugx-mods.com/forum/mapping/88/how-to-get-lights-to-activate-by-power-being-turned-on/13041/ — "state 2 appears to load by default". [02]
- https://www.ugx-mods.com/forum/mapping/92/fixing-lightingsun-in-a-new-map/12772 — the Windows decimal-comma bug that breaks sky and lighting. [10]
- https://www.ugx-mods.com/forum/help-desk/86/lights-leaking-through-walls/14935/ — no-shadow lights pass through walls. [01, 10]

**Design theory**
- https://left4deadwiki.com/wiki/Developer_Commentary_(Left_4_Dead) — Valve on lighting a dark zombie game: the most on-topic design source.
- https://book.leveldesignbook.com/process/lighting/darkness — "make it feel dark, but don't actually make it dark".
- https://book.leveldesignbook.com/process/lighting — motivated lights, key/fill/rim.
- https://www.blog.radiator.debacle.us/2018/03/gdc-2018-how-to-light-level-slides-and.html — Robert Yang, GDC 2018 "How to Light a Level".
- https://www.blog.radiator.debacle.us/2015/07/lighting-theory-for-3d-games-part-4.html — light types, contrast, emissives, bloom and fog for night scenes.
- https://gdcvault.com/play/1025360/Level-Design-Workshop-Invisible-Intuition — Shaver and Yang: guiding players with blockout and lighting.

**Glass Tower footage**
- https://www.youtube.com/watch?v=nvQY3ThaI3c — MitchyPoo, "The NEW Glass Tower Custom Zombie Map is SICK!".
- https://www.youtube.com/watch?v=bDsOuc3zSHM — Satchino, "The Glass Tower Zombies Map Is AGONY".
- https://www.youtube.com/watch?v=JXDggadvcnE — Lubed Ramen, round 207: long uncut footage for studying the lighting in motion.
- https://steamcommunity.com/id/vuflub/myworkshopfiles/?appid=311210 — vuflub_'s other towers (the house style).

---

## 7. How to judge lighting

The standing project rule applies: agents write code and logs, build, and stop; **the user plays and judges** (CLAUDE.md, top block). This section is how to make that judgement repeatable, so two builds can be compared fairly.

### 7.1 Same spot, same state, same settings

The project already paid for this lesson twice. docs/107: "Same-spot, same-state screenshots or nothing. The first useful comparison of the day was the one taken beside the crate at round 1." docs/104 §4d: "before hunting a cause, establish what the thing looked like BEFORE" — the Workshop page carries screenshots of every published build [COMMUNITY: project records] (src: docs/107_sun_volume_yellow_postmortem.md; docs/104_cybercity_sky.md §4d).

A comparison screenshot is valid only if all of these match between the two shots:

| Must match | Why |
|---|---|
| Spot and facing (use a fixed landmark, e.g. "on the crate's front, facing the core") | Light falls off with distance and angle |
| Power state and lighting state | Lighting states change which lights exist (see [02](02_power_and_states.md)) |
| Time since arriving (wait a few seconds) | Auto-exposure adapts over time [INFERRED; The Giant's worldspawn carries `secondsLerpToDarker 1` / `secondsLerpToLighter 1`, keys that bin/t7.def.json does not declare] |
| Held weapon | The viewmodel is lit too and fills part of the frame |
| FOV | The user plays at 120 (§7.3); a wider view includes more sky and changes auto-exposure [INFERRED] |
| Graphics config (low or high, §7.3) and the in-game brightness slider | Several lighting features are switched off on the low config; the brightness setting is not stored in config.ini [VERIFIED absence] |
| The build (the .ff timestamp) | Otherwise the comparison is about something else |

Name each file with build, spot, state and config, for example `v2_crate_prepower_low.png`.

### 7.2 A shot list for TOD II

Pick fixed spots once and reuse them for every lighting build (a proposal, [INFERRED]):

1. Vault spawn, facing the Quick Revive wall (pre-power).
2. Vault, facing a window niche (the red lamp; the horde's entry).
3. Conduit, facing the parts shelf.
4. Shaft, mid-flight, looking up at the sky opening.
5. Plaza, beside the crate, facing the core (the docs/107 spot).
6. Each workshop wing, facing its bench.
7. A lap-5 landing looking along the flight (district 1), and the same framing at laps 15, 25, 35, 45.
8. Lounge 10 interior, and the lounge 10 teleporter spur.
9. Crown hall, and the causeway looking at the crown.
10. One spire hub hall (the spire is reached only after the finale's ascension, so this shot is always post-power and usually needs a dev harness).

Take the pre-power set, turn the power on, wait, and take the post-power set. Today the two sets are expected to be identical, because no TOD II script calls `set_lighting_state` and every TOD II light is on in Radiant States 2–4 [INFERRED] (see [02 — TOD II today](02_power_and_states.md#15-tower-of-doom-ii-today-the-diagnosis)).

### 7.3 Judge on two graphics configs

The user's own BO3 `players/config.ini` (modified 2026-09-23 20:35) [VERIFIED] (src: `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III\players\config.ini`):

| Setting | User's value | What that hides | Suggested "high" value for a second pass |
|---|---|---|---|
| `VolumetricLightingEnabled` | 0 | "volumetric sun and light shafts" | 1 |
| `DisableDynamicSunShadows` | 1 | dynamic sun shadows (so `shadowSplitDistance` changes are invisible) | 0 |
| `DisableDynamicLightShadows` | 1 | dynamic shadows from lights | 0 |
| `SSAOTechnique` | Disabled | screen-space ambient occlusion | GTAO High Quality |
| `TextureQualityBakedSunShadows` | 2 (drops 2 mips: the lowest quality on its 0–2 scale) | baked sun shadow resolution | 0 |
| `ShadowFiltering` | 0 | soft multi-sampled shadows | 1 |
| `ActorShadows` | 0 | forced character shadows from static-shadow lights | 4 or more |
| `SpotShadowTextureSize` / `OmniShadowTextureSize` | 512 / 256 | shadow resolution | 2048 / 1024 |
| `AATechnique` | None | edge smoothing (neon lines alias) | SMAA T2x |
| `TextureQualityProbes` | 0 (best) | nothing: reflections are at full resolution | 0 |
| `FOV` | 120 | – (a wide view; see 7.1) | 120 (keep it the same) |
| `RestrictGraphicsOptions` | 1 | the menu hides options "too demanding for the user's video card" | – |

Meaning for judging [INFERRED]:
- On the user's config, volumetrics, dynamic shadows, SSAO and character shadows will not show. Many players run similar settings, so this "low" config is a realistic floor. A lighting change that only shows on a high config did not really happen for those players.
- TOD II's lights cast no shadows at all today (`PRIMARY_NOSHADOWMAP 1` on all 344) [VERIFIED], so the shadow settings only matter once shadowed lights are added.
- The user can keep two copies of the file (for example `config_low.ini` and `config_high.ini`) and swap them with the game closed. The file is outside the repository; agents do not edit it unless the user asks.
- Screen-space reflection is not a setting in `config.ini` [VERIFIED absence]. Community sources call SSR a player option [COMMUNITY] (src: modme thread 1557); where it lives in the menu is [TEST].

### 7.4 Locking exposure

Auto-exposure makes two screenshots hard to compare, because the camera re-balances the brightness. Treyarch lights with the exposure locked: "work with the exposure locked at the value that looks good … light everything relative to that" [VERIFIED] (src: Multiplayer_Lighting_Workflow.pdf §5).

- **In Radiant:** the Exposure toolbar has lock and unlock icons (`exposure_locked.png` / `exposure_unlocked.png`), an `Exposure Bank` menu, "Show Exposure Zones", and a camera readout `Exposure EV: %.2f (%.2f GPU)` [VERIFIED strings] (src: bin/Radiant_modtools.exe). Community tutorials use F7 (fullbright), F8 (baked lighting) and F9 (game view) [COMMUNITY] (src: Uptownpapi25, nYCPEJfmuS4). The Radiant preview is not the game: judge the final look in game [INFERRED; the water shaders, for one, render a different technique in Radiant, see [07](07_water.md)].
- **In game:** Treyarch documents three dvars for taking clean map screenshots: `r_bloomEnable 0` (disables bloom), `r_exposureTweak 1` (enables manual exposure) and `r_exposureValue [4-10]` (sets the exposure) [VERIFIED] (src: docs_modtools/Mini_Map_Setup.pdf, step 9). Whether they are accepted in a usermap session, and whether they need cheats or developer mode, is [TEST].
- **Project doctrine:** this project does not ask the user to type console dvars for tests (CLAUDE.md, "Dev/test = ONE compile-time flag"). Use these dvars only if the user chooses to run a comparison session with them. Use locked-exposure shots **only to compare light values between builds**; judge the mood on normal auto-exposed shots, because that is what players see [INFERRED].
- A client script API removes the adaptation delay: `SetExposureInstantSnap(localClientNum, enable)`, "snap exposure to base calculated probe value, ignore iris adaption and damping" [VERIFIED] (src: docs_modtools/bo3_scriptapifunctions.htm). It does not fix the exposure at a chosen value; it only makes the camera settle instantly, which still helps same-spot shots. A dev-only comparison harness could use it; untested in a usermap [TEST]. More exposure tools: [05 §5.9](05_sun_sky_exposure_fog.md#59-tools-runtime-api-radiant-check-dvars).

### 7.5 Readability checks (zombies, not scenery)

Run these in every lighting playtest [INFERRED, proposed protocol]:
1. **Stair approach.** Stand at a landing and let zombies come up the flight. Can you see each one at the flight's foot, both looking toward the sky and toward the core?
2. **Darkest spot.** Find the darkest spot on each shot-list floor. Can you see a zombie standing in it from 10 m and from 25 m?
3. **Doorway entry.** In the Vault, watch a window niche. Do zombies read as they step through?
4. **Sprinters and elites.** Do the armored sprinter and the elites read against the district colour (for example red elites in the red district)?
5. **Downed teammate.** In co-op, can you find a downed player in the darkest room?
6. **After power.** Repeat 1–3 after power-on. If readability got *worse* after power (glare, bloom), that is a finding too.

### 7.6 What does not count as evidence

- Blender renders and preview images: "Do not claim native appearance verified from Blender previews" [COMMUNITY: project rule] (src: CLAUDE.md; docs/155).
- Sky preview PNGs are display-referred and cannot show engine bloom; judge sharpness on the `*_ingame_*` 1:1 crops and glow only in game [COMMUNITY: project record] (src: docs/104 §4k).
- A single bake time (the bake is pass/fail here) [COMMUNITY: project record] (src: CLAUDE.md, LED bake gate).
- Other maps' Workshop screenshots, including Glass Tower's, which may be edited (§4.2).
- A successful build. The build proves the files linked, not how it looks.

### 7.7 Logs that help

A lighting playtest is easier to read with a dev-gated log of the live script lighting state. The engine API has a per-player `GetLightingState()` next to `SetLightingState` [VERIFIED] (src: bo3_scriptapifunctions.htm). A `[TOD_LIGHTSTATE]` line at blackscreen, at the power flip and at each spawn would confirm what state each player is in. It cannot by itself prove the script-to-Radiant numbering [INFERRED]. Follow the project's dev-log pattern (CLAUDE.md, "Dev-mode diagnostics") and archive the user's log with `tools/capture_ai_logs.ps1`.

---

## For Tower of Doom II

Recommendations only. Nothing in this chapter changed code or data. In this repo every light, probe, SSI, `volume_sun` or material change is a FULL build: `build_map.ps1` has no LED-only mode, and `-GscOnly` skips both cod2map and the LED bake. Everything is generator-owned (`tools/gen_tower_map.js`), and any new lighting asset goes into map-owned GDTs in the private workspace `C:\BO3Tools\TOD2Cybercity`, never the shared Mod Tools root (docs/154). The user tests; agents build and stop.

1. **Write the target down before touching keys.** A one-page brief: which spaces are dark (the climb, the Undercity before power), which are havens (lounges, wings after power), the readability rule (the main gameplay floor within about 1 stop of the scene exposure and never 2 or more stops under it; zombies silhouette against the sky and trim), and what power changes. Get the user's yes on it.
2. **Establish the "before".** Take the §7.2 shot list on the current build, pre- and post-power, on both configs (§7.3). Expect the two power states to look identical today [INFERRED].
3. **Settle the foundations first**, because the power-on design depends on them: the lighting-state numbering with the one-light test in [02 §16](02_power_and_states.md#16-minimal-test-plan-in-the-control-map); a real SSI in `ssi2` (and in every other state the map will use) instead of the empty slot, for which the compiled `.led` lists `default_day`; and a `target` on the `volume_sun` pointing at an `info_null` in open air, so the global probe is no longer buried in the mast ([05 §2.4](05_sun_sky_exposure_fog.md#24-the-global-probe-and-target)). All three are [TEST] until the user compares same-spot shots.
4. **Make power-on a local, staged beat, not a flood** (§2.8). Copy The Giant's shape: pre-power is dim, not black; power raises some lamps about a stop and adds new ones; model swaps, sounds and status lights fire in order with a pause. Keep the open spiral lit mainly by sky and emissive trim in both states, and let the power feed what it plausibly feeds (Undercity, plaza, wings, perks, doors, teleporter bay). Soften the instant switch with Map One's vision ramp. This user's Map One precedent is stronger than The Giant's: roofed rooms baked pure black until power, next to an always-lit "safe haven" plaza. Offer both shapes and start pre-power *very* dim either way.
5. **Turn even coverage into pools.** Replace some of the identical r420 / stops-6 landing pools with smaller, fixture-motivated lights (a lintel lamp over each door, a strip light at the parapet) and leave mid-flights darker [INFERRED; compare The Giant's median radius 150].
6. **Fix the colour logic for a red sky.** Use a cool wayfinding colour (cyan or cold white) that means "next door" on every floor. Keep the district hue for identity. Make danger read by flicker or pulse as well as by red, because red has little contrast against red ambient [INFERRED].
7. **Give each district a signature fixture type and a darkness curve**, with the four lounges as bright havens (§2.9). Group exploders per district or per lounge (≤120, [INFERRED] cap).
8. **Decide the emissive architecture deliberately.** About half the visible faces glow over their whole surface [VERIFIED], and that glow does not follow power or lighting states on its own [INFERRED; Treyarch's lampshade shaders exist precisely because emissive materials have to be synced by hand, Materials.pdf p.17]. The glowing faces are worldspawn brushes, which carry no `lightingstate` keys; entities such as `script_brushmodel` and `misc_model` do have them, but what they do to an entity is undocumented [TEST] (see [02 §12](02_power_and_states.md#12-switching-emissive-glow)). Moving large surfaces to the thin-line look (bright edges on dark faces) is the single change closest to Glass Tower's read and to a darker tower. It is also a map-wide look change, so it is the user's call.
9. **Borrow from Glass Tower in this order**, cheapest and most certain first: fit the reflection probes to their spaces ([06 — the fix plan](06_reflections_probes.md#153-the-fix-plan)); keep the sky dramatic while holding its light low (`skyStops`/target score for the light, `sky_intensity_factor` for the visible sky, [TEST]); pick a trim colour complementary to the sky; consider bloom only with a `pbg_box` flagged for the state the map actually runs in. The def defaults those volumes to `LIGHTSTATE_1` only [VERIFIED] (src: bin/t7.def.json), and The Giant leaves all 15 of its boxes that way, so they come on with its power [VERIFIED by parse; mapping INFERRED]; in a map that boots Radiant State 2, a default-flagged box would do nothing until the state changes [INFERRED; untested] (see [02](02_power_and_states.md#6-everything-else-a-state-can-switch)). Water ([07](07_water.md)) and a sunset theme ([05 — a sunset](05_sun_sky_exposure_fog.md#8-recipe-a-sunset)) are mood choices for the user.
10. **Strengthen zombie readability with stock hooks** before adding light: an eye-glow FX override (`level._override_eye_fx` with the stock blue/green/red effects, or the installed third-party white one) or the eyeball material's luminance/colour overrides, plus the cyber zombies' emissive eyes. Do not rely on volumetrics, dynamic shadows or SSAO, which the user's own config switches off.
11. **Ask the user to confirm Glass Tower** (link in §4.1) and to point at the moments they love.

---

## Sources

Official Treyarch documentation (MODTOOLS/docs_modtools)
- Multiplayer_Lighting_Workflow.pdf §3, §5 — exposure range, dynamic range, "2 or more stops" visibility rule, lock exposure, sun bake override.
- Lighting_Parameters.pdf — stops as the light unit (default 11); auto-exposure keys.
- Materials.pdf p.17 — lampshade/backlit shaders; p.18 — emissive HDR scale = 2^EV.
- PhysicallyBasedRendering.pptx slide 10 — albedo 40..238.
- SunSky_Light_SetUp.pdf — runtime override vs bake SSI; the sky light uses the sky texture for value and colour.
- Mini_Map_Setup.pdf step 9 — `r_bloomEnable`, `r_exposureTweak`, `r_exposureValue`.
- bo3_scriptapifunctions.htm — `SetLightingState`, `GetLightingState`, `SetExposureInstantSnap`.

Stock data and scripts (MODTOOLS)
- bin/t7.def.json — `light` (`volumetric`, `lightingstate1..4`), `volume_sun` (`global_fill_color`, `shadowSplitDistance`, `ssi1..4`, `target`), worldspawn (`sky_intensity_factor0/1`; no exposure, `bloom` or lerp keys), `pbg_box` / `vbloom_box` (`LIGHTSTATE_1` default), `misc_model` / `script_model` / `script_brushmodel` (`lightingstate1..4`).
- bin/Radiant_modtools.exe — exposure toolbar strings and icons; "Total Exploders: 0/120" and "Total Exploders: %d/%d".
- deffiles/ssi.awi — `evmin`, `evmax`, `evcmp`.
- source_data/ssi.gdt — `zm_factory`, `zm_zod`, `default_night`, `default_sunset`.
- source_data/_emox/emox_mwiii_vertigo_assets.gdt — the vertigo mirror materials (third-party pack in the tools root).
- model_export/t7_skybox.gdt, t7_techart_props.gdt — sky materials and `skyStops`.
- map_source/zm/zm_giant.map — worldspawn exposure, bloom, LUT and lerp keys.
- map_source/_prefabs/zm/zm_giant/zm_giant_light.map — 543 lights (parsed: types, masks, twins, colours, radii), 176 probes, volumes, the `volume_sun` and its `info_null` target; light/zm_giant_teleporter.map for log2 stop values.
- share/raw/scripts/zm/zm_giant.gsc:132, 427-428, 540-590 — boot, power-on sequence, `set_lighting_state( 0 )` at :571.
- share/raw/scripts/zm/zm_giant_fx.csc:69-71, 184-198, 225-295 — lamp model swaps, red/green status exploders, "dramatic pause".
- share/raw/scripts/zm/zm_giant_amb.csc:9, 35-95, 170-180, 283-320 — power-on sounds; the commented-out PA announcement.
- share/raw/scripts/zm/zm_usermap.gsc:110 — boot lighting state (script state 1); :112 — default eye FX.
- share/raw/scripts/shared/util_shared.gsc:2975-3002; zm/gametypes/_globallogic_spawn.gsc:501 — `set_lighting_state` on level or player, re-applied at spawn.
- share/raw/scripts/zm/_zm_power.gsc — no lighting calls.
- share/raw/scripts/zm/_zm.csc:450-470, 550-700 — zombie eye FX and eyeball-material hooks.
- share/raw/fx/zombie/fx_glow_eye_*.efx — eye FX (parsed for element types; file dates).
- share/raw/techsetdefs_stable — `useScreenspaceReflection` only in the `lit_water_sim` include and the `water_shore` techsets.

This repository
- map_source/zm/zm_tod2_cybercity.map (parsed: lights, probes, prefabs, `volume_sun`, worldspawn, the `mast tier 1` brush); tools/gen_tower_map.js (`DISTRICTS` 1615, `BREATHER_THEME` 2200, `light()` 7166, lap lights 7217-7226, crown lights 7283-7298, Undercity lights 7317-7341); source_data/tod_skybox.gdt; tools/gen_tod_sky.js (themes 166-214, sign 1270); scripts/zm/zm_zod_robot.csc:66-89.
- The compiled `C:\BO3Tools\TOD2Cybercity\share\raw\maps\zm\zm_tod2_cybercity.led` (SSI names only).
- docs/104_cybercity_sky.md §4, §4d, §4k; docs/107_sun_volume_yellow_postmortem.md; docs/150_tod2_evil_sky.md; docs/154_tod2_isolation.md; docs/155_fx_art_workflow.md; docs/BO3_MAPMAKING_KB.md §1; CLAUDE.md.
- Map One (`abandoned_cyber_city_zombies`): docs/20_atmosphere_and_materials.md; `_acc_atmosphere.gsc:500-520`; tools/oneshots/gen_room_roofs.js:25-68.

User's machine
- `C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III\players\config.ini` (read-only).

Glass Tower
- https://steamcommunity.com/sharedfiles/filedetails/?id=3801980290 and the Steam Web API `ISteamRemoteStorage/GetPublishedFileDetails`.
- The 10 author screenshots and vuflub_'s preview images (viewed).
- YouTube nvQY3ThaI3c, bDsOuc3zSHM, JXDggadvcnE.

Design theory and community (see §6 for the full list)
- Left 4 Dead developer commentary (Chin, Jensvold, Keegan, Campbell), left4deadwiki.com.
- The Level Design Book, lighting and darkness pages.
- Robert Yang, Radiator Blog (GDC 2018; lighting theory part 4).
- VerK0 Lighting Tutorial Parts 1-5; JBird632; MattFiler/zm_alien_isolation; modme threads 330, 1077, 1213, 1557, 1869, 2029, 2118, 3135.
