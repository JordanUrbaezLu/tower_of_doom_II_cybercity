# 163 — THE CUT: the causeway is gone, a jump pad crosses the gap

*2026-09-24. Built, unplayed. The user tests.*
*2026-10-03: the pad wears **Der Eisendrache's jump pad** now (§9) — the
teleporter model and FX described in §3 are history for the pad.*

## 1. The ask

> "On this map, there's a start at the crown. And they will need to get out of
> the crown ... to actually start the game. The door costs like 5,000. ... at
> the ... there's a bridge that goes from the tower to the crown. This entire
> bridge most of like 80% of it needs to be removed and there needs to be a
> jump pad from one side to the other ... it needs to functionally work with no
> bugs ... for now we can use the teleporter model to act as the jump pad and
> it'll trigger as soon as you walk onto it. ... the player should be launched
> through the sky. I think Black Ops 3 has some of these jump pad models
> already ... if you can find those models and how that functionally works.
> Let's just do that right now, as well."

## 2. What is there now

```
CROWN HALL ── Fall gate (5000) ── courtyard ── the crown's mouth (tunnel) ── LAUNCH DECK
 (crown_zone)                                                                  │  the PAD
                                                                               │
                        5200 units of sky — 81% of the old bridge, gone       ╎  4.5 s arc,
                                                                               ╎  2200 up
                                                                               ▼
                                          TERRACE ── gate-run ── LANDING DECK (roof_zone)
```

| piece | odd-frame footprint | zone | notes |
|---|---|---|---|
| gate-run | x ±80, y 480..720 | roof_zone | the road's first 240 units; portal 1 at y 600; the (parked) causeway gate at its mouth |
| landing deck | x ±240, y 720..1200 | roof_zone | 4 set-down spots (±80, 900/1020); 2 risers at the far corners (±200, 1160), ≥165 from every spot |
| **gap** | y 1200..6400 | none | nothing in it; the two old mid-road pylon pairs moved to the launch deck |
| launch deck | x ±240, y 6400..6880 | **crown_zone** | the pad at (0, 6640), trigger radius 72; 2 avenue pylon pairs flank it |
| approach + flare | y 6880..7840 | **crown_zone** | unchanged — the tunnel through the crown's band and the courtyard to the hall gate |

The crown did not move: the hall's south face is still `TER_Y2 + CW_LEN`.
Only deck was removed. All of it is `CW_CUT` in `tools/gen_tower_map.js`
(section 5c): `false` regenerates the v12 road **byte-for-byte** (checked:
.map, door/breather/spire data identical; crown data differs only by the
added functions).

## 3. The pad (`scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc`)

* **Trigger:** no entity — every server frame each living player is tested
  against the pad circle (r 72, within 48 of the deck, on the ground). Walk on
  and you go. Refused (logged, throttled): downed (a crawler never flies),
  world paused / card menu, already linked to something, airborne (fires on
  touch-down).
* **Flight:** the player is linked (`PlayerLinkToDelta`, free look) to a
  `tag_origin` mover that walks the arc in 45 `MoveTo` steps of 0.1 s: the
  straight line between the two feet positions plus a parabola peaking
  `TOD_JUMPPAD_APEX` (2200) above it. Exact at both ends; nothing the player
  presses changes where they land. You can look around and shoot.
  **Why not a velocity launch** (stock `_zm_jump_pad.gsc`, Moon's pads): same
  height both ends → stock's maths gives zero lift, air control can strafe
  off the arc over a 19,000-unit drop, and a ~2000-unit fall onto the deck is
  fall damage.
* **Set-down:** unlink, `SetOrigin` on the spot, zero velocity. The spot is the
  free one farthest from every living player; a spot is reserved for its
  flight + 1.5 s.
* **Presentation (all existing assets):** the teleporter model
  (`tod_teleporter`) as the pad, its idle "ready" field always on, the
  teleporter discharge (flash + derez + `tod_warp`) at launch with a small
  quake and a rumble, the kino materialize beam + `tod_warp` at the landing.
* **One way, by design.** There is no pad back up; the Fall only descends.

### What a flyer is spared (the flag is `player.tod_jumppad_flying`)

| stock/map system | what it would do mid-air | the guard |
|---|---|---|
| `_zm.gsc` out-of-playable-area monitor (3 s poll) | the arc is outside every zone volume for ~4 s → Samantha laugh + kill | `level.player_out_of_playable_area_monitor_callback` spares flyers, defers to any earlier callback |
| player damage chain | a down while linked to a mover | a callback inserted FIRST in `level.player_damage_callbacks` returns 0 |
| AI targeting | zombies/elites chase a point over the void | `zm_utility::increment_ignoreme` for the flight (paired once) |
| elite spawn anchors | the Panzer anchors on the HIGHEST player = the flyer; a navmesh query in mid-air finds nothing | `_tod_bosses::anchor_player` / `pick_target_player` skip flyers |
| Mage Blink / bat lunge / ATHLETE | `SetOrigin` / `SetVelocity` fighting the link | one field check in each |
| stock `manage_zones` failsafe | no occupied zone → re-enables the START zone's spawning (crown_zone), sticky | `_tod_fall` counts a flyer as still inside, and re-asserts the hall's spawning off after the seal (peer session) |
| boss stuck watch / stray relocation | a player moved 5000+ units | the teleporter's two signals: `level.tod_tp_stamp++`, `tod_stray_pump` |

## 4. The Fall, island-aware

The hall + its stub are one island (`tod_crown_data::on_crown_island`). The
Fall gate seals when no living player is on the island **and nobody is in the
air**; the sweep at the seal clears every ordinary zombie and Doppelghast left
on the island (both done in `_tod_fall.gsc` by the peer session, which owns
that file). `crown_zone` covers the stub, so a player waiting at the pad keeps
the hall's risers live — the launch deck is never a safe camp.

**Zones:** `crown_zone` and `roof_zone` are **no longer adjacent** (they do not
touch on foot). With adjacency, the terrace's risers woke whenever anyone
stood in the hall and every zombie they raised stood on the far stub,
pathless, holding a slot. `roof_zone` is enabled directly when the Fall gate
is bought (`zm_tod2_cybercity.gsc::fall_enables_roof_zone`; the pad re-checks
at every launch). After the seal, `_tod_endless_rounds::finale_spawn_selection`
drops any island riser as a backstop.

**Navmesh:** the island is its own component now, so it rests on its own
seeds: the hall's four riser seeds plus two new ones (launch deck, crown
throat).

## 5. Gates

| gate | what it proves | runs |
|---|---|---|
| `gen_tower_map.js` roadEmit | each stub whole from its own mouth, the pad/landing on them, the two stubs NOT connected | every regen |
| `lint_tod_geometry.js` | reads the `tod_jumppad_launch/land` structs as a ONE-WAY edge; proves citadel → terrace through the pad; 0 holes / 0 invisible walls / 0 detached | every full build |
| `lint_tod_geometry_selftest.js` | +2 cases: no pad markers → severed; landing marker deleted → loud failure. 13/13 incl. parity | when the lint changes |
| `lint_tod_navmesh.js` | NEW crown-island check: hall meshed, pad in the hall's component, landing in the tower's | every full build (after cod2map) |
| `tools/test_jumppad.js` | NEW: struct ↔ GSC lockstep; both ends inside a live zone volume; the arc swept clear of every brush (5 take-offs × 4 spots × 401 samples, a standing player's box, real brush planes); wiring + every guard present | every build |

Side fix: `lint_tod_geometry_parity.js` redirected only 3 of the generator's 5
outputs, so every self-test run rewrote the repo's `_tod_breather_data.gsc` and
`_tod_spire_data.gsc` with LAPS=49 values. All five are redirected now and a
missed redirect throws.

## 6. Logs (dev OFF while `TOD_JUMPPAD_LOG` is 1 — zero before publish)

`[TOD_JUMPPAD] INIT pad= r= land= spots= model_ok= beam_ok= damage_cbs=` ·
`LAUNCH op= player= src= dst= spot= round= roof_zone_on= fall_sealed=` ·
`LAND op= player= at= spot= flight_ms= zone=` (zone must read `roof_zone`) ·
`REFUSE player= why=` · `ABORT op= why=` · `ZONE roof_zone was disabled at a launch`.
With `[TOD_FALL] EMPTY` / `SEAL` from `_tod_fall`, a co-op run shows the whole
crossing.

## 7. The real jump pad models (found 2026-09-24; Der Eisendrache's INSTALLED 2026-10-03, §9)

No jump pad model is installed in either tools root, and the game install has
no DLC map fastfiles to extract from. The only source is MidgetBlaster's
`~/Downloads/T7 Assets V2.8.rar` (58 GB; single files extract fast):

* **Moon — `p7_zm_moo_jump_pad_02`** (recommended): round, lit, hazard-striped
  launcher, 175 wide, base 26 below its origin; 35,434 tris at LOD0, 8 LODs,
  24 materials, ~12 map-specific textures (~8.5 MB). `_cushion` (160 wide) is a
  matching landing mat. Risk: 2 images its materials name are defined nowhere
  (`i_mtl_p7_wall_mobile_dep_decal_details_01_normal_m`,
  `i_mtl_p7_zm_zod_gatestone_set_metal02_m`) — they need substituting.
* Revelations `p7_zm_gen_jumping_pad` (a floating Apothicon rock island,
  animated variant + anims in the pack), Der Eisendrache
  `p7_zm_ctl_launch_pad_ring` + grate/panel kit and the snowy jumpsphere set.
* Effects already in both roots' `share/raw/fx`: `dlc5/moon/fx_moon_jump_pad_*`,
  `dlc1/castle/fx_elec_jumppad*` (incl. a player trail), `fx_dust_landingpad`.
  Sounds: none installed; the pack has Der Eisendrache's flinger wavs and alias
  rows.
* Scripts: stock `_zm_jump_pad.gsc` (velocity launch — see §3 for why not);
  a decompiled Der Eisendrache `_zm_flingers.gsc` (vehicle-spline ride, the
  invulnerable-while-flung damage callback this module mirrors).

**The swap is contained:** `TOD_JUMPPAD_MODEL` + its `#precache` in
`_tod_jumppad.gsc`, one `xmodel,` zone line, and a map-owned GDT
(`model_export/` + `source_data/`, renamed `tod_*`, private-root rules per
docs/154). `tools/test_jumppad.js` already checks the model is zoned and
precached. It is a FULL build.

## 8. Build record

* **This session's full build, 12:50 Eastern** (one build for this cut and the
  crown session's docs/160 §10 pass, on the tree after the alarm-gantry fix):
  the jump pad gate OK; geometry lint OK — 0 holes / 0 invisible walls / 0
  detached, `citadel -> terrace (jump pad): YES`; navmesh **3 components**
  (spire 776 faces; tower + landing 265; the crown island 90) and the new
  CROWN ISLAND check connected; fresh LED 100,163,686 B (doubled by the crown
  session's second lit state, not by this cut); bank 197.9 MB; English link
  verified at 12:57:45 (FF 211,194,688 B). The session ended during the
  post-link validators, so its log has no verdict line. Log:
  `tmp/jumppad_20260924/build.log`.
* **The build that is deployed now: the item-shop session's full build 9,
  BUILD OK 13:58 Eastern**, FF 211,206,016 B (13:56:30). It carries this cut
  whole and re-ran every gate above in its own log: test_jumppad OK, the
  one-way route YES, navmesh 3 components with the crown island connected,
  fresh LED, bank 197.9 MB. Log: `tmp/partner_shop_build/full_build_9.log`.
* Verified afterwards: the deployed `.map` is md5-identical to the repo's
  (`76cf024e…`), and every file this cut touched is byte-identical to its
  deployed copy (`_tod_jumppad.gsc`, `_tod_crown_data.gsc`, the entry script,
  `_tod_fall.gsc`, the zone). The only repo≠deployed files are three
  `_tod_shop*` scripts the shop session edited after its build — not part of
  this feature.
* **Superseded 15:03:33 Eastern by the dark-pass full build (docs/164 §8),
  FF 210,979,392 B**, which carries this cut unchanged: re-checked here — the
  deployed `.map` is md5-identical to the repo's (`1cf7f708…`, jump pad
  structs present), every file of this cut deployed == repo, and
  `test_jumppad` passes on it.
* No launch. UNPLAYED — the user tests. Read the `[TOD_JUMPPAD]` lines in
  the user's console log (§6).

## 9. Der Eisendrache's jump pad (2026-10-03)

> "The jump pad on this map is a teleporter but I want it to have the jump pad
> model from der eisendrache. Can we switch it over with same functionality"

**What DE's jump pad is.** DE calls it the *jumpsphere* (its script is
`_zm_flingers.gsc`): a broken-open half-sphere machine (`p7_zm_ctl_jumpsphere_snow`,
~210 wide, 139 tall, 80k tris) on a round plinth over a lit deck disc
(`..._combined_snow`, 215 wide, 5 tall). You walk in through a doorway on its local
-x side and are flung out of its broken-open local +x side; you land on a matching
landing pad (`..._landing_pad_snow`, 145 wide). The deck and the landing pad come in
plain / `_blue` / `_red` — the light material is the only difference on the deck
(`set_light` scaleRGB 0.05 = dark, `_blue` 5). MidgetBlaster's prefab
`castle_flinger_01.map` (in the T7 pack) shows DE's assembly: machine + deck at one
origin and yaw, the doorway facing AWAY from the destination.
(The `p7_zm_ctl_launch_pad_*` kit §7 also listed is the V-R11 rocket's launch
structure, not the player pad.)

**What the player sees now.**

| moment | before (teleporter) | now (DE's flinger) |
|---|---|---|
| before the power | the teleporter, lit pink, a ready beam (it refused anyway) | DE's machine, deck lights **dark** |
| power on | — | deck lights turn **blue** + the machine's crackle (`tod_jumppad_charge`) |
| walking up | step onto a flat deck | walk **into the machine through its doorway** (it faces the bridge corridor) |
| launch | teleporter flash + derez + warp boom | the crackle + DE's **fling burst** at the pad (`fx_elec_jumppad`), the **fling whoosh** riding with you (`tod_jumppad_launch`), DE's **electric trail** on you for the climb; the wind loop and the kick unchanged |
| in the air | — | the **landing pad glows** (`fx_elec_landingpad_glow`, re-pulsed while anyone is inbound) |
| touch-down | teleporter materialize beam + warp boom | DE's **landing dust** (`fx_dust_landingpad`) + the **thud** (`tod_jumppad_land`); the kick unchanged |

**Same functionality.** The flight is untouched: the arc, the hang clock, the
opening scene (first jump), one-way, the power gate, every guard (§3 table). Two
numbers moved because the model needed them: the trigger is **r 40** (was 72) —
the inside of the machine, so whoever walks through the doorway launches and nobody
outside its wall can; and the four set-down spots are **on the landing pad**
(±24, ±22 round its centre; were ±80, ±60 on the bare deck).

**Its body.** The machine is a script_model with no collision (CollisionMap ""), so
`gen_tower_map.js` cuts a ring of 20 clip wedges round it (`jump pad shell N`):
`JP_SHELL_R1` 52 (just inside its innermost posts) .. `JP_SHELL_R2` 98 (its plinth),
150 tall (over the dome), open `JP_SHELL_DOOR_HALF` 27° either side of the doorway
(the model's own doorway is ±20°; the margin keeps the gap wide for the navmesh),
and bulged to 118 where its side gadgets stand out (`JP_SHELL_BULGE`, local
215..285°: measured r 104-115 at knee to head height). `JP_PAD_YAW` 270 turns the
doorway onto the bridge corridor and the open side onto the flight.

**Files.**
* `tools/jumppad/install_de_jumppad.py` — copies from the T7 pack into
  `model_export/tod_jumppad/` (5 models × their LODs, 31 textures renamed
  `i_tod_jp_*`), writes `source_data/tod_jumppad.gdt` (5 xmodels, 49 DE materials,
  31 image blocks) and masters the three fling wavs into `sound_assets/tod/jumppad/`;
  `--check` (build gate) re-hashes every output and proves the GDT self-consistent.
  Never reads the pack at build time.
* `_tod_jumppad.gsc` rev 7 — the props, `power_watch` (dark → blue), the effects and
  sounds, `level.tod_jumppad_flights` (cleared on the set-down AND on an abort).
* `gen_tower_map.js` — `JP_PAD_YAW`, `JP_PAD_R` 40, `JP_SHELL_*`, `JP_LAND_YAW`,
  `JP_LAND_SPOTS`, the shell emitter + its clearance asserts; generated
  `jumppad_land_yaw()`.
* zone: 5 `xmodel,` + 4 `fx,dlc1/castle/...` lines; `sound/aliases/tod_jump.csv`:
  3 rows; `sync_to_modtools.ps1`: the `model_export\tod_jumppad` row;
  `build_map.ps1`: the installer's `--check` beside `test_jumppad.js`.

**Eight textures DE's materials name exist nowhere in the pack** (borrowed from
Zurich / Zetsubou / Cairo sets): wear masks → the jumpsphere set's own masks, two
normal maps → flat `$normal`, a snow decal colour → the stock snow its siblings use
(`SUBSTITUTES` in the installer, each with its reason). The `p7_common` decals have
PNGs but no image blocks anywhere: their blocks are cloned from a castle block of
the same semantic (`SIBLINGS`). DE's red (recharging) variants are not installed:
this pad never recharges. The model carries DE's snow; that is DE's look.

**Gates.** `test_jumppad.js` (new 2b: 20 clip wedges, the ring never cuts into the
trigger and leaves no dead corner inside it, the opening is the doorway and faces
the corridor; the arc sweep skips the ring — invisible clip round the take-off, the
rider is linked; every model / effect zoned + precached, every alias a 3D one-shot
on its wav, the inbound flight cleared on both exits, no `tod_teleport::` left).
Negative controls run: wedges by the door removed, the whole ring removed, the
machine turned 90° — each FAILS. `lint_tod_geometry.js` now decodes the wedges
(`MODEL_CLIP_COLUMNS`); without that exemption it reports 44 invisible walls.
Parity lint OK (the ring mirrors with the crown). `test_jump_title` (the crash
framing from r-40 take-offs), `gen_lanes --check`, arity, native API, FX paths,
hints: all green before landing.

**Logs** (`TOD_JUMPPAD_LOG` 1): `INIT rev=7 pad=de_jumpsphere ... frame_ok= deck_ok=
landpad_ok=`, `STATE pad=ready deck= landpad=` (the power), `FX_FAIL` (a prop or FX
host could not spawn), and the unchanged LAUNCH / LAND / REFUSE / ABORT / CINE_*.

**Knobs, per symptom.**

| symptom | knob |
|---|---|
| can walk into the machine's wall, or blocked at its doorway | `JP_SHELL_R1` / `R2` / `DOOR_HALF` / `BULGE` (gen_tower_map.js) — FULL build |
| launches too early at the doorway / not deep enough inside | `JP_PAD_R` (must stay ≥ `JP_SHELL_R1` − 16 and < `JP_SHELL_R1`: asserted) |
| a fling sound too loud / quiet | `SOUNDS` gains in the installer (re-run it) |
| the landing glow too long / short | `TOD_JUMPPAD_FX_GLOW_EVERY` / `_SECS` (_tod_jumppad.gsc) |
| a part draws flat gray / untextured | read `tmp/native_build/linker_last.log` for the pad's materials (the post-link gate names them); a shipped texture's usage = `SLOT_USAGE` in the installer |

**Build:** FULL BUILD OK 15:34:14 (`tmp/jumppad_de/full1.log`; .ff 15:32:18, 229,559,040 B; a fresh map compile + navmesh + lighting bake). The navmesh gate puts the pad (inside the machine) on the crown hall's component and the landing on the tower's; the compiled ledger carries all 5 models with every LOD whole, the 4 effects and the 49 material NAMES - but 12 of those materials compiled EMPTY and the 31st texture was refused (see "The gray machine" below: the user saw the machine flat gray); the 3 sounds are in the loaded bank; deployed = repo, nothing synced after the .ff. UNPLAYED — the user tests.

### The gray machine (the user's first look, 2026-10-03)

User, after playing the 15:34 build: *"Textures look like they didnt come through
properly. ENtire model is grayish and bugged."* The flight worked (the run log
has every LAUNCH / CINE / LAND line); the MATERIALS did not. The 15:32 link's own
transcript (kept: `tmp/jumppad_fix/evidence_1532/linker_last.log`) says why, in red:

    Material 'mc/mtl_p7_zm_ctl_jumpsphere_set_painted_red' (mc/lit_alphatest_advanced): Image
      'i_tod_jp_t7_micro_metal_painted_02_s' (specColorMap) has a mismatched usage ( 'specularMap' expected: [specularMask] )
    The model (tod_jumppad_frame) uses material (mtl_p7_zm_ctl_jumpsphere_set_painted_red) but there is no techset for surface 11

One texture, the micro-tile spec map, had no image block in the pack, and the
installer authored it from the castle's FULL-COLOUR `specularMap` block (one of
2 such blocks; the castle's other 22 `_s` blocks are `specularMask`). Every slot
it fills - `specColorMap`, and `colorMap03` (the micro-tile techset's
`specularMapDetail2`) on `lit_micro_tile_blend_advanced`, `lit_alphatest_advanced`,
`lit_transparent_advanced` and `lit_backlit_advanced` - reads a `specularMask`.
The linker refused it, and the **12 materials** that use it (the painted metal,
the copper coils, the red paint, the generator, the signage, the backlit panel:
most of the frame and both decks) compiled **EMPTY**: each one's asset-ledger row
is its name and 2 bytes (41-49), where a complete material is 328-2080. Empty
materials draw flat gray. The build said OK (red linker lines are not failures to
`build_map.ps1`), and my post-build check called the missing texture "a slot the
materials do not sample" - wrong.

THE FIX is one GDT line (`"semantic" "specularMask"`), made by the installer
(`SIBLINGS['specColorMap']` = the castle's `i_mtl_p7_zm_ctl_trunk_wood_vintage_metal_s`
block). Models, textures, sounds: byte-identical. A SECOND installer bug, caught
while staging: after a build the tools DB holds `tod_jumppad.gdt`'s own 85 assets,
and the stock lookup counted them as stock, so a re-run wrote a GDT with no
materials at all; `stock_sets()` now subtracts the assets its own GDT owns
(`_entity` -> `_gdt` in gdt.db) and the install refuses when every material reads
as stock.

GATES: `--check` (pre-build) now proves every shipped texture carries the usage
its slot's techset reads (`SLOT_USAGE`; negative control: the old GDT fails with
all 12 slots named). NEW post-link step in `build_map.ps1`, after the war-damage
ledger: `install_de_jumppad.py --compiled-ledger <xmodel csv> --linker-log
tmp/native_build/linker_last.log` fails on an EMPTY pad material (ledger row <=
name + 64 bytes), on any shipped texture missing (the old "4 may be culled" slack
is gone) and on any linker usage / techset complaint naming a pad material or
model.

The same red-but-not-fatal class sits elsewhere in that transcript (other
sessions' assets, not touched here): `mtl_wpn_t7_c4_decal2`,
`sat_zm_machine_y_mod_01_on`, `tod_fire_bow_rune_view`'s storm crystals and
missile orb, and the 115-grenade set compile EMPTY too.

**Build:** FULL BUILD OK (tmp/jumppad_fix/full2.log, log end 16:13:41): .ff 16:11:50, FF 229,424,640 B, geom_key REUSED the 15:32 bake; the new post-link gate ran inside it (49 materials all complete, 31 of 31 textures, no linker usage / techset complaint naming a pad asset); the 12 formerly empty materials are 1,136-2,074 bytes; the same 8 known-waived ERROR lines; deployed = repo, nothing synced after, no repo edits after the 16:01:40 start. It also carries -09's C4 armed-tell fix. UNPLAYED.
