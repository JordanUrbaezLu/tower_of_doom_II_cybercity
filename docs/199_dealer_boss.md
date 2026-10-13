# 199 - THE DEALER, the final boss (model, rig, animation set, weapons, two states)

> **2026-10-04: HIS FIGHT IS WIRED - docs/207 THE DEALER'S HOUSE.** The Battle Arena's level 10 spawns him in his own arena after
> the parlour scene and the drain (`_tod_house.gsc`, through `spawn_boss`); `level.tod_dealer_hold` holds him while he talks;
> `level.tod_dealer_crack_fn` / `_death_fn` are his voice's hooks; the crown-hall test spawn (`TOD_DEALER_TEST_SPAWN`) is 0.
> The shock, the gun bursts and the adds (s4) are still open: "we will continue enhancing after".

> **2026-10-05 (W2B, asset packs PK10 / PK11 / PK14): HIS LOOK, HIS SOUND AND HIS FIGHT VOICE.** Section 5 below.

User, 2026-09-30: *"make the black market dealer the final boss ... build a model using the
Blender MCP. Build it super, super deep ... long, sharp red nails ... the red Xs on his eyes and
the mask ... a persisting black shadow coming off of his character ... steal an animation ...
pick the right set of animations ... his stride, his speed."* Later the same night: *"two states ...
New voice lines during the fight. Multiple weapons: melee you with a scythe, shoot the Wunderwaffe
and shock everyone, and shoot a machine gun."*

**2026-10-02 - HIS OWN FACE.** User: *"Lets redesign the black market dealer away from rictofen. We can
remove anything related to rictofen. He will be his own entity. At half health his mask will be cracked and
one eye glow will be missing and his smile more menacing."* Every Richtofen piece is GONE: the donor head
(`10_state2_head.py`, the staged `c_zom_der_richtofen_cin_fb` binary + 36 images, their GDT blocks, the
`tod_dealer_body_unmasked` model), the fight lines drafted for him (s4) and the voice (docs/198 round 8).
STATE TWO is now **THE CRACKED MASK** (`10_state2_mask.py`, `tod_dealer_body_cracked`): the same Dealer,
the same bake, with a chip torn from the right temple and the grin's right corner (the black void shows
through), black fissures across the brow, cheek, nose and jaw with two red leaks where the wiring is cut,
the RIGHT X eye DEAD (dark red glass, no glow; the stroke that was already failing in state one), the LEFT
eye burning harder, and THE GRIN torn wider: both corners pulled up the cheeks, a sagging lower seam, a
black gape and seventeen long uneven fangs, the stitches whole on the left and dangling on the right, the
right strap snapped. Where this page says "Richtofen's head" below, read "the cracked mask".

This document is the record of what was built and decided on 2026-09-30, what is proven, and
what the fight still needs. The encounter rules (phases, telegraphs, lifecycle, HP) stay in
`dealer_finale_design.md`; this page supplies its missing form decision and the assets.

## 1. The decision: a human-sized, striding Dealer on the Keeper's skeleton

The form question in `dealer_finale_design.md` is settled by the request itself: a MOVING
fighter with a stride, not a colossus. The rig is **the Keeper's skeleton**
(`model_export/tod_keeper/c_zom_dlc4_keeper_fb.XMODEL_BIN`, 145 bones): the stock humanoid
zombie rig (`j_mainroot` spine, legs, arms, three-joint fingers, `j_head`) plus eight robe-skirt
chains hanging from the hips and knees, a jaw, and weapon tags in both hands, at the chest and
on the back. Why it wins over every alternative:

| Rig | Verdict |
|---|---|
| Keeper (chosen) | Humanoid, a robe skirt that already animates, 82 clips installed and a proven AI chain in this map (`tools/keeper/`); the pack carries 28 more Keeper clips with a composed walk, standing attacks, a teleport, an intro and a channel loop. |
| Player bodies (the user's "same shape" idea, checked) | The limbs and fingers share names, but the spine is six different bones (`pelvis`, `back_low`, `back_mid`, `neck`, `head`, `torso_stabilizer`) and all 102 shared bones sit at different bind positions. The pack's player clips are lobby idles, staff locomotion and specialist runs: no firing, no melee. Would need a retargeting tool and still lack the motions. |
| Mangler / zombie base | Walks are shambles or armored lumbering; nothing composed. |

### The motion set: HIS OWN CLIPS, authored from the Keeper's (`tools/dealer_boss/author_clips.py`, 2026-10-01)

User, watching the first reel: *"you have to understand the concept of holding a scythe ... a lot
of these positions the scythe doesn't seem smooth and flails around"*, and *"one thing I would
like him to do is levitate. That's his walking animation. And then when he breaks his mask at 50%
he will walk around and have the Richtofen head."* The Keeper clips were animated for empty
claws: a scythe pinned to one wrist whips with every twist of that wrist and the other hand never
touches it. So the Dealer ships **45 clips of his own** (`xanim_export/tod_dealer/tod_dealer_f_*` /
`_g_*`), written by `author_clips.py` (background Blender: mathutils + PyCoD) from the raw Keeper
clips (`install.py` extracts the 27 pack sources into `art/dealer_boss/clips_src/`, gitignored;
the enslaved / SoE sources are the installed Keeper's own files):

| | STATE ONE `tod_dealer_f_*` (22 clips) | STATE TWO `tod_dealer_g_*` (23 clips) |
|---|---|---|
| Who | the masked Dealer, LEVITATING, the scythe | the CRACKED-MASK Dealer, ON THE GROUND, the machine gun (2026-10-02; was a borrowed head) |
| Sources | the Keeper PROTECTOR's glide clips (its legs never step; walk 85 in/s, run 118, sprint 159), idle + two scans, swipes left / right / up / combo, bamf in / out, intro, outtro, channel intro / loop / outtro, ee idle, walk / run / sprint "attack" (hands-clasped channels while moving) | the enslaved Keeper's stepping idle, run v1 / v2, sprint v1 / v2, attacks v1-4, run attacks v1-4, deaths v1-4; the SoE keeper's attacks v1 / v2 / v4, run attack v4, front death; the companion kneel |
| Baked in | every part but `tag_origin` / `tag_sync` / `tag_aim` rises **14 in** (the root stays on the ground: navmesh placement and delta root motion are untouched); **the two-hand scythe hold** (below); both weapon tags rigid to their wrists | both weapon tags rigid to their wrists (the raw clips animate `tag_weapon_right` loose, up to 20 in from the hand, and park `tag_weapon_left` 350 in away: a bone-attached gun floated beside him) |
| Selected by | the zombie blackboard's `_arms_position`: the script sets `self.zombie_arms_position = "up"` | ... `= "down"` at the mask break |

**The scythe hold, per frame (so the game attaches the scythe as a plain rigid model on
`tag_weapon_right` and nothing is aimed at runtime):**
1. The pole direction is OUTWARD: from a point 8 in behind the chest through the right palm (a
   swipe of the arm becomes a sweep of the blade; it can never point into the body and never
   flips - the first rule, "past whichever hand is farther out", snapped 97 deg in one combo frame).
   When the palms are within 14 in (the Protector's clasped glide measures 11.4..13.3) it is THE
   CARRY instead: up and across the chest to the left, the blade rising over the shoulder. The
   carry weight and the sweep direction are each smoothed over time (a Gaussian, sigma 3 frames,
   wrapped on looping clips), then joined on the great circle THROUGH A FORWARD-UP WAYPOINT (a
   direct blend of two near-opposite directions passes through zero and snaps).
2. The right wrist turns about its joint so the tag's -X runs along that pole and the blade plane
   stays upright (world up for a sweep, backward for the upright carry, blended).
3. The left hand goes ON the shaft: its palm slides to the nearest point within the grip range
   (12 in behind the right hand to 32 ahead), the hand is turned as the mirror image of the right
   hand's grip (hand frames built from the finger bones, no rig-convention guessing), and a
   two-bone IK bends the left arm to reach it keeping the clip's own elbow plane; the forearm
   twist helpers share the wrists' turn.

Measured on the written files (`clips_report.json`): every locomotion / idle / channel clip turns
the pole at most 0.5-1.7 deg per frame with the left palm within 1.5 in of the shaft; the swipes
sweep at up to 11 deg per frame (left) and 39 (the raised cast, where the left hand cannot reach
and floats); only the easter-egg idle and the outtro keep gaps the fight never shows. The reel
(`12_play_reel.py` + `13_scythe_mount.py`) plays these files in the live studio with the scythe
mounted exactly as the engine mounts it: preview = game.

| Moment | State one (`anim_zombie_*_au`, `ARMS_UP`) | State two (`*_ad`, `ARMS_DOWN`) |
|---|---|---|
| WALK / RUN / SPRINT (+ the pain overlays) | `f_walk` / `f_run` / `f_sprint` | `g_ens_run_v1` (the enslaved Keeper has no walk; the Keeper's own table does the same) / `g_ens_run_v1` / `g_ens_sprint_v1` |
| Super sprint | `f_sprint` | `g_ens_sprint_v1` (`anim_dealer_super_sprint_ground`) |
| Melee walk / run | `f_idle_attack_left`, `f_idle_attack_right` (two scythe cuts) | the seven ground swipes / the five run-swipes |
| Idle | `f_idle`, `f_idle_scan_1`, `_2` | `g_ens_idle` (`anim_dealer_idle_ground`) |
| Death (the tree's one row; `dealerDeathStart`) | - (the mask breaks at 50%: he only dies in state two) | `g_ens_dth_v1..4` |
| Scripted gestures | `anim_dealer_intro`, `_bamf_in` / `_out`, `_cast_up` / `_combo` / `_left` / `_right`, `_idle_attack`, `_channel_intro/loop/outtro`, `_ee_idle`, `_walk/run/sprint_attack` (all `f_`) | `anim_dealer_kneel` (`g_cmpn_revive`), `_death_front` (`g_zod_dth_f_v1`) |

The selector table (`animtables/tod_dealer.ai_ast`, written by `install.py`) is the Keeper's with
`idle@zombie` and `move@zombie` split on `_arms_position` (`ARMS_UP` rows -> the AU aliases,
`ARMS_DOWN` rows -> the AD aliases, a trailing `*` row keeps the default). The melee selector
already keyed on it. Every authored clip's GDT block is cloned from its source's (the notetracks
- melee fire, the teleport's sound and fx - ride along) and points at the authored file; no raw
pack clip is zoned (`ai_zombie_zod_keeper_run_attack_v4` was declared twice, once here and once
in the Keeper's GDT, and gdtdb refused EVERY build in the repo until it was dropped, 23:48-23:55).

**The linker's rule (paid for 2026-10-01 10:39, every linker on the shared root aborted on it):** a clip a
`move@zombie` row names must be a looping, loop-synced xanim (`"looping" "1"` AND `"loopsync" "1"` in its GDT block; the second link said "requires loop sync animations"). The mirror holds too: a clip an `idle@zombie` or `melee@zombie` row names must carry NEITHER flag (build 4, 11:55). The pack's Protector
locomotion blocks and the Keeper's enslaved run / idle blocks carry 0, so `install.py` flags every authored
locomotion clip of both states, the idles and the channel loop (`LOOPING`) with both flags, and `test_dealer.js`
checks both from the selector rows.

Every clip was loaded with PyCoD and checked part by part against the body's bones before it
was chosen; the one Keeper clip with a different rig (`corrupted_keeper_float_emerge`, 105
parts) is excluded.

## 2. The model (`tools/dealer_boss/`, master `art/dealer_boss/dealer_boss.blend`)

Authored live in a visible Blender MCP studio (port 9899, Blender 4.2, PyCoD in-process) so
the user can watch; every part is skinned the moment it exists and the rig can be posed with
any real clip (`anim_preview.py`, `09_pose_check.py`). BO3 model space: +X forward, +Y left,
inches.

| Step | What it builds |
|---|---|
| `01_rig_reference.py` | the Keeper skeleton as an armature from the XMODEL_BIN, the Keeper body as a translucent proportion ghost, collections, stage, six review cameras; writes `skeleton.json` |
| `02_coat.py` | trousers tucked into buckled boots; a floor-length heavy wool coat OPEN from the belt down (lining and striding legs show), torn dragging hem, a left front panel with brass toggles on red stitched loops, a draped shoulder mantle longer at the back, deep bell sleeves with wool cuffs folded over oxblood lining, forearm straps, a wide belt with a steel buckle |
| `03_head.py` | the shop merchant's OWN mask construction (slanted red X eyes with one failing stroke, overhanging brow plates, hollow cheeks, split nose bridge, jagged grin seam with nine uneven teeth, scar, torn corner) plus a brow fracture and temple rivets with straps; the black void behind it; a drooping executioner's hood with a tall oval opening, rolled rim binding, crown seam and drawstrings |
| `04_hands.py` | black leather gloves built along the finger bones (palm, knuckles, cuff with a stitched hem, back-of-finger seams) and ten LONG SHARP RED NAILS curving past the fingertips, each on its tip bone |
| `05_gear.py` | a leather bandolier of five glowing essence vials, a locked satchel on the hip, a belt chain with three keys, a string of tarnished tokens, the ledger chain and seal at the throat |
| `06_lighting.py`, `08_review.py` | theatre-scale three-point lighting (the scene is in inches, lights fall off as metres) and the six-camera review renders in `art/dealer_boss/review/` |
| `10_state2_head.py` | STATE TWO: Richtofen's Der Eisendrache cinematic head (face, hair, eyes, teeth, lashes) lifted 4.8 in and scaled 1.08 so his eyes sit on the mask's eye line; every face bone collapsed onto `j_head` (the rig has no face bones) |
| `11_weapons.py` | the Wunderwaffe DG-2 and Dingo world models previewed at `tag_weapon_right`, and THE SCYTHE authored in the Dealer's language (blackened snath, leather grip wraps with red stitching, brass ferrule and pommel, a hooked blade with a red neon edge and etched lit channels, a chain and token) |

Materials are one procedural library (`studio.py`: heavy black wool with weave and edge wear,
oxblood satin lining, worn and glove leather, graphite molded mask with scuffs, red neon wire
and a weak stroke, lacquered red nails, aged brass, blackened steel, dark glass, red essence,
boot leather, rubber sole, tarnished silver), each tagged with the atlas it bakes into. Every
seam on the clothes is a faint red neon thread: the mask's stitched grin carried onto the coat.

**Review evidence** (`art/dealer_boss/review/`): `cam01..06_*_final.png` (bind pose, six views)
and `pose_*` (walk frame 40, sprint frame 20, swipe frame 25, raised-hands frame 30). The
pose check caught and fixed one real skinning fault: the mantle had been weighted to the
upper-arm bones and rose with the arms like puffed sleeves; it now hangs from the clavicles
and upper spine only.

## 3. Native pipeline (RUN 2026-09-30 23:24: export OK, install --check OK, test_dealer PASS 848 checks; wire.py deliberately NOT run)

- `export_native.py` (background Blender, strict workstation guard): applies every modifier,
  joins the parts into three skinned meshes (body / head / hands), unwraps and bakes five
  channels each (colour, tangent normal, fullspec, gloss, emissive; the cyber kit's channel
  wiring, 4096 body / 2048 head and hands), writes seven LOD skinned XMODEL_BINs with the
  Keeper's bone table byte-copied and every vertex on its best four bones, and asserts a
  round-trip read of each binary. Manifest: `art/dealer_boss/engine_kit/export_manifest.json`.
- `author_clips.py` (background Blender) writes the 45 authored clips + `clips_report.json`
  (sources, measurements, sha256 per file); re-run it after any change to the hold rules.
- `install.py` (plain Python, `--check` is the build gate): `source_data/tod_dealer.gdt`
  (15 images, 3 `lit_emissive_advanced_fullspec` materials with scaleRGB 6/10/6, the body xmodel
  with converter-generated distance LODs like the cyber roster, character `c_tod_dealer`, one
  xanim block per authored clip cloned from its source's, the aitype chain
  `archetype/variant/spawner_tod_dealer` with archetype `dealer`), the AI tables
  `tod_dealer.ai_am/ast/asm/bt` (the Keeper's with the two-state mapping and selector rows above
  and the death StartFunction renamed), CRLF like every AI table. It refuses an authored clip whose
  hash is not the report's and deletes any raw pack copy beside the authored files.
- Exported and installed (2026-10-02, his own face): `tod_dealer_lod0.xmodel_bin` (masked) and
  `tod_dealer_cracked_lod0` (the cracked mask), both from ONE head bake - every face carries a `dealer_state`
  (0 both / 1 masked only / 2 cracked only) and each variant drops the other state's faces, so the two
  bodies share the three Dealer materials and atlases and differ only in the mask faces; `tod_dealer_scythe_lod0`;
  `source_data/tod_dealer.gdt` = the Dealer's own images and materials + the two weapons' donor materials
  ONLY (no borrowed head: `install.py donor_blocks` emits only what the DG-2 / Dingo models name), 5 xmodels
  (both bodies, the scythe, `tod_dealer_dg2`, `tod_dealer_lmg`), 45 xanims, the character and the aitype
  chain. `test_dealer.js` s7b fails on any `richtofen` / `c_zom_der_` / `mtl_c_gen_` / `_unmasked` name in
  the GDT, the manifests or the zone, and proves body + hands identical across the states. The counts are
  in `export_manifest.json` / `install_manifest.json`. `test_dealer.js`:
  1,071 checks, 0 failures (every Dealer row names an authored clip, the selector rows per state,
  every authored file's hash, no raw pack clip shipped or zoned).
- `_tod_dealer_finale.gsc` (2026-10-01, the first pass of the fight module; the user: "spawn him in the crown
  so i can test"): the archetype "dealer" registers the Keeper's blackboard + zombie flags (same skeleton, same
  tree), `dealerDeathStart`, `spawn_boss( org, target )` (the Keeper's portal + scream, `spawner_tod_dealer`,
  health `TOD_DEALER_HP_ZOMBIES` 60 round-zombie units per playing player, `tod_boss_kind` "dealer" so the
  wide elite bar follows him, the elite purse + 2000 team points on death), STATE ONE at spawn (arms "up",
  walk, the scythe rigid on `tag_weapon_right`), THE MASK CRACK at half health (`TOD_DEALER_MASK_CRACK`;
  detach, `SetModel` the cracked body, arms "down", run, the Dingo in hand, a placeholder burst + scream), the card-deal freeze
  every tick, HP / STUCK / DEATH logs (`[TOD_DEALER]`, printing with dev OFF while `TOD_DEALER_LOG` is 1).
  `TOD_DEALER_TEST_SPAWN` 1 spawns him in the crown hall 6 s after the round-1 card deal, 448 units south
  of the alarm button on the hall's axis, facing the nearest player; `build_map.ps1` refuses `-Publish`
  while that or the log define is 1.
- `wire.py` RUN 2026-10-01 10:31 (zone block, the two sync rows, the two build gates + the publish refusal,
  the `#using` + `init()` in `_tod_main.gsc` after the Keeper's); builds through
  `tmp/dealer_boss/build_detached.ps1`: full1 / full2 stopped before their links (each carried the GDT of the moment
  before the next linker-rule fix), full3 passed every gate on the final tree and was refused at cod2map because the
  user launched BO3 (11:26:59; nothing linked), full4 reached the linker (11:55) and died on the mirror rule (idle@zombie / melee@zombie rows
  require NON-looping, non-loop-synced clips; the pack's idle_attack blocks ship looping 1): `selector_loop_sets()`
  now derives both flag sets from the generated tables and test_dealer gates both ways; full5 = FULL BUILD OK 12:22:31 (.ff 12:20:46,
  FF 228,267,968 B; the five xmodels, all 45 xanims, the aitype and the script in its ledger; details in the CLAUDE.md top note).
- The Wunderwaffe shock and Dingo bursts/two-hand attack holds are now implemented and built (docs/dealer_combat/README.md); native fight unplayed. Adds remain a design item (section 4). The aura,
  the mask shatter, his sounds and his fight barks shipped in W2B (section 5); the arena is docs/207.

## 4. The fight as now specified (design, not shipped)

Two states, one actor, one health bar:

1. **THE DEALER (masked).** Scythe in hand. Calm stride; swipes become scythe cuts (the seven
   swipe clips with the scythe attached to `tag_weapon_right`); the bamf teleport repositions him;
   the raised-hands cast is the WUNDERWAFFE discharge: he raises the DG-2 and chain lightning
   arcs to every player in range, shocking them (a short stun plus damage through the player
   damage callback, telegraphed by the 1.5 s raise and a rising whine, dodged by cover); the
   channel loop is the collection call (adds). The black shadow aura rides him the whole fight
   (a dark-tinted soul-wisp effect: the Necromancer's white souls, inverted).
2. **THE MASK CRACKS.** At half health the mask takes the hit it cannot shrug off: a burst at the
   face (fragments, sparks, the right eye's wire dies), the body swaps to the cracked variant (one
   eye dark, the grin torn wide), the voice drops its manners (the manic mode becomes the baseline
   for the rest of the fight), and he draws the machine gun: walk/run-attack clips with the Dingo
   attached, bursts of `MagicBullet` from its muzzle, sprint locomotion, shorter recovery.

Voice: ONE voice (docs/198 round 8: his own, soft and dark with the manic cracks) in two registers
through the existing ElevenLabs pipeline (`tools/black_market_vo/`): the soft register for state one
(invitation, recognition, three attack calls, the crack), the manic register (`mode: "manic"`) for
state two (the crack's aftermath, machine-gun taunts, the sprint phase, defeat). The key stays in
the environment variable only.

### Fight lines, first draft (for the user's edit before any generation)

State one, THE DEALER (the shop's soft dark voice; manic cracks marked *):
- invitation: "Come down. The shop is closed. Let's settle your account."
- recognition: "Every card you drew, every spin ... I was counting."
- scythe call: "A cut. Just a small cut, for the house."
- waffe call: "Hold still. This is the expensive part." *
- summon call: "I never hunt alone. I have stock."
- teleport: "Behind you is also for sale."
- player downed: "No refunds." *
- mask crack: "You ... scratched the merchandise."
- mask cracks: "You ... cracked the merchandise." *

State two, THE DEALER UNMASKED OF HIS MANNERS (the same voice in its manic register; the eye is dead, the grin is open):
- the crack's aftermath: "One eye is plenty. [laughs] I only ever needed one for you."
- machine gun: "Hold still. This one does not haggle."
- machine gun burst: "MORE! Put it on the account!"
- sprint phase: "Faster. The house always collects faster."
- waffe (if kept in state two): "Lightning. Older than the city. Mine before the city."
- player downed: "Paid in full. Next."
- low health: "That ... was not on the price list."
- defeat: "The shop ... stays ... open. It always ... does."
- recovery (abort): "We will finish this later. Your page is still open."

Weapons and attacks are design until the scripts exist; nothing in this page is playable yet.

## 5. His look, his sound, his fight voice (W2B, 2026-10-05; source + gates, UNBUILT, UNPLAYED)

| Beat | Look (`tools/dealer_fx/gen_fx.py`, `tod/dealer/`) | Sound (`tools/dealer_sfx/make_sounds.py`, `tod_dealer.csv`, 3D) |
|---|---|---|
| He rises at the gate | `fx_tod_dealer_arrive`: black mist floods the floor, a black column tears up and swallows the moment he appears, a red neon flare in its heart, a dark shock ring, embers, one short red light | `tod_dealer_spawn` (a rift tearing open, a dark synthetic choir, a sub boom); a failed `SpawnActor` withdraws the rift before it plays and sounds no tear (the house retries every 2 s) |
| The whole fight | `fx_tod_dealer_aura` on a carrier linked to `j_spine4`: black lit smoke peeling off the coat and rising, a dark veil off the hem, faint oxblood souls, a few embers (no light); `fx_tod_dealer_aura_trail` on his `tag_origin`: a black mist pool he leaves behind | state one: `tod_dealer_levitate_lp` (his levitation hum, 3D loop, stopped at the crack / death; its row's `StopOnEntDeath` ends it on any other exit) |
| His blows | - | his clips' own Sound notes, remapped by `install.py` NOTE_ALIASES: `tod_dealer_scythe_swing` (4) + `tod_dealer_attack_vox` (3 efforts in HIS voice through the shipping mask, 65 %) on the scythe cuts; `tod_dealer_bash` (3) on the state-two swings; `tod_dealer_step` (4) on his state-two boots; `tod_dealer_bamf_out / _in` on the bamf clips; a blow that LANDS rings on the player (`dealer_hit_cb`, read-only): the blade `tod_dealer_scythe_hit` (3) in state one, the gun's blunt stock `tod_dealer_bash_hit` (3, no ring) in state two |
| The mask cracks (50 %) | `fx_tod_dealer_mask_shatter` on `tag_eye` (+X out of the face): a red-white flash, charcoal shards and chips, red sparks, a black puff, a short light; `fx_tod_dealer_eye_die` at the RIGHT socket: five dying spark spits over ~1.5 s; the aura swaps to `fx_tod_dealer_aura_cracked` (hotter, red soul-flame at the chest, one small red light) | `tod_dealer_mask_crack` (the crack, sparks shorting, a brief distorted shriek); the levitation hum dies; his crack line comes 0.7 s later (`TOD_HOUSE_CRACK_LINE_DELAY`) |
| He dies | `fx_tod_dealer_death` at the floor: a red flash, the mask's last shards, a BLACK SOUL COLUMN tearing up, red souls racing up inside it, embers, a dark shock ring, a black dust wave, a short light; 2 s before the 6 s delete `fx_tod_dealer_dissolve` burns the body away and its last black billow lands ON the delete (`TOD_DEALER_DISSOLVE_SECS` LOCKSTEP `DISSOLVE_DELETE_MS`) | `tod_dealer_death` (a short glitching scream collapsing into a rumble, eased -8 dB under his words from 1.0 s); his last line comes 1.0 s after it (`TOD_HOUSE_DEATH_LINE_DELAY`) |

**His fight voice (PK14):** eight lines in his own voice (group `house`, `tools/black_market_vo`, the mask applied by `pick.py`):
three soft scythe calls (`tod_house_vo_swipe_1..3`: a landed state-one hit, 45 %, never twice in 14 s, never on a hit that may
down), four manic chase taunts (`tod_house_vo_taunt_1..4`: state two, first ~6 s after the crack line, then every 14-22 s) and
the low line (`tod_house_vo_low`, once at a fifth of his health). A deck never repeats the line just said; no bark starts
within 6 s of the last or 2.5 s of any line still on a lane; the crack and the death cut a bark still speaking.

Rules kept: every effect on a `tag_origin` carrier (never a bare `PlayFX`, never `PlayFXOnTag` on the actor), bone-guarded,
carriers die with their owner (polled) or their life; black smoke is a LIT material (an additive sprite cannot darken);
every light shadowless, in all four lighting states, one at a time; <= 200 live particles per effect (the two loops on him
~70 at most). Gates: `test_dealer.js` s9 (no Keeper alias left on his clips, every note's alias defined, negative controls)
and s10 (precache / generated / zoned / carriers / the beats / LOCKSTEP); `test_dealer_house.js` s2b (the barks, the beats,
6 new mutants); `gen_fx.py --check`, `make_sounds.py --check`, the arena / house generators' authored lane.
Design previews (NOT the in-game look): `art/generated/W2B-dealer-av/_review_fx.png`, `_review_sounds.png`.

The user has a downloaded BO6 Wunderwaffe pack; its location was not found under Downloads
(no file named waffe/wunder/dg2 there or in the 3D Models zips) - it replaces the BO3 DG-2
stand-in once pointed at.
