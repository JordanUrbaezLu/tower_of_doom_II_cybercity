// =============================================================================
// _tod_class_kit.gsc - WARRIOR and BREACHER equipment, ported from Hellbound.
//
// User 2026-09-25: "These classes should take from hellbound. Both warrior and
// breacher have lethal and tacticals. Please bring in" - and, asked, chose
// "From the start": both classes carry both items from the first spawn, like the
// Archer's Retriever + Grapple (_tod_archer.gsc). No upgrade cards gate them.
//
//   WARRIOR (key "slasher")  tactical BASH   sword swing + forward dash, stun cone,
//                                            2x blade damage, 1 charge, 12 s recharge
//                            lethal   GRAVITY SMASH  stock Gravity Spikes slam
//                                            (lift/gib 200 u, knockdown 400 u),
//                                            elites take a hit + 1.5 s stun, 45 s cooldown
//   BREACHER (key "heavy")   lethal   C4     tod_c4 = hb_c4 made STICKY (2026-09-25):
//                                            sticks to walls AND enemies, 3 charges,
//                                            detonate button / double-tap USE / shot -
//                                            stack several on one elite, pop them at once
//                            tactical CLUSTER  (2026-09-25, replaces Thermite) Fuse's
//                                            Knuckle Cluster: bursts on impact and
//                                            scatters bomblets that pop in a chain
//   NECROMANCER              lethal   SOUL BOMB (2026-09-26) a blast of souls from the
//                                            player (_tod_necro_summon.gsc); a grenade
//                                            stays in the slot at 0 ammo so the button
//                                            can be polled, like the Warrior's.
//                            tactical INVISIBILITY CLOAK (2026-09-27, class pass 2) -
//                                            earned by its card; the mechanics live in
//                                            _tod_class_cards (cloak_fire / cloak_hud)
//
// DONOR: tower_of_doom_II_hellbound scripts/zm/zm_tower_of_doom_ii/_tod_class_paths.gsc
// (Bash 836-1089, C4 403-470 + 1219-1255, Thermite 381-398 + 1258-1336, Gravity
// Smash 1437-1495). Each ability runs at its donor card's FIRST level, fixed.
// Donor weapon GDTs (hb_grenades / hb_thermite / hb_warrior_bash) are installed
// at the tools root; snapshots in donor_gdt/hellbound/.
//
// DAMAGE SCALE. Hellbound's "curve" is its own zombie health (~1/10 of stock);
// here it is this map's round zombie health, level.zombie_health, so every
// "x round zombies" number keeps its meaning: C4 = 5 zombies (half at the edge),
// a Cluster bomblet = 1 zombie at its centre, Smash on an elite = 2 zombies. Authored
// damage rides the tod_cleave_hit PASS-THROUGH (_tod_upgrades), so cards do not
// re-multiply it; BASH instead goes through the normal melee chain with the
// blade's identity, so the Warrior's damage cards apply to it once.
//
// HUD: the Archer's "tod_archer_abil" event, with a 4th arg naming the kit
// (1 warrior, 2 breacher) - AetheriumLoadout.lua setArcher draws the tiles.
// Logs: [TOD_KIT] (dev only).
// =============================================================================
#using scripts\codescripts\struct;
#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\weapons\_weaponobjects;
#using scripts\zm\_zm_utility;
#using scripts\zm\_zm_weap_gravityspikes;
#using scripts\zm\zm_tod2_cybercity\_tod_necro_summon;
#using scripts\zm\zm_tod2_cybercity\_tod_cyber_sword;
#using scripts\zm\zm_tod2_cybercity\_tod_warrior_melee;
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx;   // docs/203: the ability feedback (both views)
#insert scripts\shared\shared.gsh;

#precache( "model", "tag_origin" );
#precache( "fx", "dlc3/stalingrad/fx_raz_mc_shockwave_projectile_impact" );
#precache( "fx", "explosions/fx_exp_generic_lg" );
#precache( "fx", "zombie/fx_tesla_shock_zmb" );
#precache( "fx", "fire/fx_fire_ground_rubble_50x50" );
#precache( "fx", "explosions/fx_exp_grenade_default" );
#precache( "fx", "dlc5/tomb/fx_one_inch_punch_impact" );
#precache( "fx", "dlc3/stalingrad/fx_dragon_gauntlet_melee_impact" );
#precache( "fx", "hb/gold_sword/fx_smash" );
#precache( "fx", "hb/gold_sword/fx_smash_afterglow" );
#precache( "fx", "tod/fuse/fx_tod_fuse_bomblet_exp" );
#precache( "fx", "tod/abfx/fx_abfx_cl_pop_t3" );   // docs/206: the tier-3 cluster pop WITH a light
#precache( "fx", "tod/fuse/fx_tod_fuse_sizzle" );
#precache( "fx", "fire/fx_fire_single_loop_01_xsm_evb" );
#precache( "fx", "tod/breacher/fx_tod_cluster_glow" );
#precache( "fx", "tod/breacher/fx_tod_c4_blast_t1" );
#precache( "fx", "tod/breacher/fx_tod_c4_blast_t2" );
#precache( "fx", "tod/breacher/fx_tod_c4_blast_t3" );
#precache( "fx", "tod/breacher/fx_tod_cl_burst_t1" );
#precache( "fx", "tod/breacher/fx_tod_cl_burst_t2" );
#precache( "fx", "tod/breacher/fx_tod_cl_pop_t1" );
#precache( "fx", "tod/breacher/fx_tod_cl_pop_t2" );
#precache( "model", "tod_fuse_bomblet" );
#precache( "eventstring", "tod_archer_abil" );

#namespace tod_class_kit;

#define TOD_KIT_TICK              0.05
#define TOD_KIT_PIN_MS            500

// WARRIOR BASH (tactical). Card "bash" (domain 62, max 8, 2026-09-26, user: "add
// those upgrades") ports Hellbound's own ladder (its _tod_class_paths bash_*):
// rank = card level 0..9 (9 since 2026-09-27), rank 0 = what every Warrior has from spawn.
//   damage   2.0 + 0.5 / rank   (x2.0 -> x6.0 blade swing)
//   recharge 12 s - 0.5 s / rank (12 -> 8 s)
//   charges  1 + min(rank,6) / 3  (1, 2 at rank 3, 3 at rank 6; rank 9 = the wider burst)
// LOCKSTEP: add_domain( "bash", ..., 8 ) in _tod_upgrades.gsc and tod_upgrade.lua
// DOMAIN[62] / DETAIL[62].
#define TOD_BASH_RANGE            175     // record: the old cone burst (build 5), superseded by TOD_BASH_BURST_R
#define TOD_BASH_DOT              0.40    // record: the old cone (build 5)
#define TOD_BASH_STUN_MS          2500
#define TOD_BASH_RECHARGE_MS      12000
#define TOD_BASH_RECHARGE_STEP_MS 450     // 9 levels since 2026-09-27: 12 s -> 7.95 s at Lv9 (was 500 / Lv8)
#define TOD_BASH_DAMAGE_MULT      2.0
#define TOD_BASH_DAMAGE_STEP      0.45    // x2.0 -> x6.05 at Lv9 (was 0.5 / Lv8)
#define TOD_BASH_CHARGES          1
#define TOD_BASH_MAX_LV           9       // 2026-09-27: 9 levels, big steps at Lv3 (2nd dash) / Lv6 (3rd dash) / Lv9 (wider burst)
#define TOD_BASH_BURST_R_LV9      225     // the end burst at Lv9 (TOD_BASH_BURST_R 150 below it)
// 2026-09-26 build-6 playtest (user: the sword dash "should be more of like the
// Gauntlet's dash ... a single swing and then dash and then hit everything near
// it"): the dash is the gauntlet juke's (1000 u/s peak, ~400 ms, ~300 u), it hits
// what it runs through (TOD_BASH_PATH_R), and the burst lands at the END of the
// dash on everything around you (TOD_BASH_BURST_R), not a cone. Was 480 u/s /
// 300 ms / impact at 250 ms / a 175 u cone.
#define TOD_BASH_DASH             1000
#define TOD_BASH_ANIM_MS          550
#define TOD_BASH_IMPACT_MS        400
#define TOD_BASH_DASH_MS          400
#define TOD_BASH_BURST_R          150
// The sword's Bash proxy is tod_bash_sword_zm (build 16; user after build 14:
// "a single swing and a dash forward ... the baseball over the head lunge"): it
// raises on the bat's centred overhead lunge (vm_t9_bat_melee_out) with the Cyber
// Sword model - ONE blade pass - so it is shown whole like the fists' clips. Was
// Hellbound's hb_warrior_bash (the whole two-pass slash) cut at 280 ms.
#define TOD_BASH_SWORD_MS         600
// The fists' Bash hold (build-16 playtest, user: "the bash on it, there's no
// animation"; the log had the proxy up 50 ms after the press): the punch clip is
// 0.7 s and the hand-back at TOD_BASH_ANIM_MS 550 cut its last fifth. The fists
// now show the whole clip.
#define TOD_BASH_PUNCH_MS         700
#define TOD_BASH_MAX_TARGETS      16
// 2026-09-26 playtest (the log's only cast: hit=0 after 152 u of dash): the dash
// now TURNS toward the nearest zombie ahead and hits everything it runs through,
// not just the one 250 ms sample.
#define TOD_BASH_AIM_RANGE        360     // u: a zombie this close ahead steers the dash
#define TOD_BASH_AIM_DOT          0.87    // ~30 degrees each side
#define TOD_BASH_PATH_R           96      // u around the body, every tick of the dash (the gauntlet juke's radius)

// GRAVITY SMASH (lethal). Card "gravsmash" (domain 63, max 8, dealt from tier 3:
// _tod_upgrades set_tier_min). User 2026-09-26: "the gravity smash should only work
// for the final tier ... it's a move that needs to be charged up ... just like ...
// the necromancer's": TIER 3 ONLY and CHARGED BY KILLS (the Soul Bomb's rule), no
// longer a 45 - 2.5/Lv s cooldown. Any kill a tier-3 Warrior makes charges it
// (_tod_warrior_melee's death callback -> level.tod_gs_charge_fn); its own slam's
// kills do not.
//   kills      20 - 1 / Lv          (20 -> 12)
//   elite hit  2.0 + 1.75 / Lv round zombies (2 -> 16 = Hellbound's Lv8)
#define TOD_GS_TIER_MIN           3        // the Warrior's tier-3 move (the Gold Battle Sword)
#define TOD_GS_KILLS              20       // kills to charge it at card Lv0 (the Soul Bomb's 20)
#define TOD_GS_KILLS_STEP         1        // -1 kill to charge per card Lv (11 at Lv9)
#define TOD_GS_OWN_KILL_MS        2000     // ms from its own slam: those kills (stock's lift kills late) never charge it
#define TOD_GS_ELITE_ZOMBIES      2.0
#define TOD_GS_ELITE_STEP         1.55     // 2 -> 15.95 round zombies at Lv9 (was 1.75 / Lv8)
#define TOD_GS_MAX_LV             9        // 2026-09-27: 9 levels; the elite stun grows 1 s at Lv3 / Lv6 / Lv9
#define TOD_GS_STUN_STEP_MS       1000
#define TOD_GS_ELITE_STUN_MS      1500
// THE SWORD SMASH (user 2026-09-26: "the gravity smash for the sword is broken ...
// we lost that animation in the migration ... That should be in Hellbound"). With
// the Gold Battle Sword in hand the lethal plays Hellbound's slam: the cast proxy
// (tod_cyber_sword_cast_zm, installed at the tools root; its raise IS the slam clip)
// + Hellbound's leap arc, and the slam lands on the clip's impact frame. Timing =
// Hellbound's level-0 profile (_tod_gold_smash_timing: impact 967 ms, clip 1700 ms,
// arc 750 ms, 56 u high, up to 128 u forward). The hit itself is the same Gravity
// Smash as every other blade (stock knockdown + the elite hit), plus Hellbound's
// smash FX and sound. Since it became tier 3 only (2026-09-26) it is ALWAYS the sword
// slam; the instant stock slam is only the fallback (prone, or the proxy not linked).
#define TOD_GS_SWORD_PROXY        "tod_cyber_sword_cast_zm"
#define TOD_GS_SWORD_IMPACT_MS    967
#define TOD_GS_SWORD_ANIM_MS      1700
#define TOD_GS_ARC_MS             750
#define TOD_GS_ARC_HEIGHT         56
#define TOD_GS_ARC_DIST           128
#define TOD_GS_ARC_MAX_ERROR      40
// THE AIR SLAM (user 2026-09-27: "you can bash in the air and then use your cyber
// smash. I want the cyber smash to pull you down with force and land on impact
// whether you are super high or not ... calculate the floor distance"). A smash cast
// off the ground traces to the floor below, hangs a beat, then DRIVES the Warrior
// straight down (rewritten every tick, accelerating) and the slam lands the instant
// the feet touch - never mid-air. The hang is timed from the traced height so a short
// drop lands on the sword's own swing frame (TOD_GS_SWORD_IMPACT_MS); a long drop
// pulls at once and lands late. No fall damage from a dive. Smash pressed DURING a
// Bash cuts the Bash and slams (the Bash is spent, not refunded).
#define TOD_GS_DIVE_MIN_H         48       // u above the floor: lower than this lands on its own
#define TOD_GS_DIVE_TRACE         40000    // u traced down for the floor (the whole tower)
#define TOD_GS_DIVE_V0            1500     // u/s straight down when the pull starts
#define TOD_GS_DIVE_ACCEL         8000     // u/s^2 on top of that
#define TOD_GS_DIVE_VMAX          4000     // u/s cap
#define TOD_GS_DIVE_HANG_MIN_MS   120      // the beat in the air before the pull
#define TOD_GS_DIVE_HANG_MAX_MS   450
#define TOD_GS_DIVE_MAX_MS        6000     // a dive that never touches down slams anyway
#define TOD_GS_DIVE_FALL_GRACE_MS 750      // fall damage blocked this long after the landing
#define TOD_GS_QUEUE_MS           1500     // a smash queued behind a Bash goes stale after this

// BREACHER - Hellbound Lv1: one of each per round, refilled every round and on respawn
// tod_c4 (source_data/tod_breacher_kit.gdt) = hb_c4 with "Stick to all": the
// engine sticks it to an enemy's body and it rides along until detonated.
#define TOD_C4_WEAPON             "tod_c4"
// the C4 blast: stock large fireball (flame billows, smoke, a big flash) on top of the
// weapon's own grenade explosion. User 2026-09-26: "it should look like an actual explosion".
#define TOD_C4_FX_BLAST           "explosions/fx_exp_generic_lg"
// stick where it hits (c4_stick_watch): enemies this close to the throw listen for the
// stick, for this long; the charge sits this far out from the chosen bone
#define TOD_C4_STICK_SCAN         1200
#define TOD_C4_STICK_WAIT         3.0
#define TOD_C4_STICK_SKIN         6
// 2026-09-26 (user, the Breacher's cards): C4 and CLUSTER are EARNED, and each card
// is its item's WHOLE lane - more charges AND more damage (user: "the damage increases
// will be inside of sticky C4 and clusters own upgrade lanes. And those both need to
// go to eight"; the EXPLOSIVES card is gone). 8 levels each, LOCKSTEP with add_domain
// in _tod_upgrades and DOMAIN/DETAIL rows 60/61 in tod_upgrade.lua:
//   C4 charges/round      Lv1..9  1 1 2 2 2 3 3 3 4 (1 + Lv/3, from 2026-09-27)
//   CLUSTER charges/round Lv1..9  1 1 1 1 1 2 2 2 3 (from 2026-09-27)
//   damage, both          x(1 + 0.175 x (Lv-1)) -> x2.4 at Lv9
// Level 0 = an empty slot (HUD LOCKED). TOD_C4_CHARGES / TOD_CLUSTER_CHARGES are the
// old fixed start (3 / 1), kept as the record.
// 2026-09-27 (user: "level nine as max" / "standardize this 3,6,9 level process"): both
// cards are 9 levels. C4 charges 1 / 2 / 3 / 4 from Lv1 / 3 / 6 / 9 (tiers 1..4 the same);
// Cluster 1 / 2 / 3 per round from Lv1 / 6 / 9 (tiers 1..3), layers at Lv3 / Lv6 as before;
// damage x1.0 -> x2.4 at Lv9.
#define TOD_C4_MAX_LV             9
#define TOD_CLUSTER_MAX_LV        9
#define TOD_KIT_DMG_PER_LV        0.175
// DEMOLITIONIST - RETIRED 2026-09-27 (class pass 2); the defines below are history, read by nothing.
// It was the Breacher's kit-lane card (_tod_class_cards header): C4 and Cluster
// radius +3% / Lv (+27% at Lv9); an explosive KILL refunds a charge of that kind 5 / 10 / 15% of the
// time at Lv3 / Lv6 / Lv9 (never above the round's max, at most one refund per kind per 1.5 s).
// LOCKSTEP tod_upgrade.lua DETAIL[37].
#define TOD_DEMO_RADIUS_STEP      0.03
#define TOD_DEMO_REFUND_PCT       5
#define TOD_DEMO_REFUND_GAP_MS    1500
#define TOD_C4_CHARGES            3
#define TOD_C4_RADIUS             240
#define TOD_C4_ZOMBIES            5.0
#define TOD_C4_ELITE_ZOMBIES      1.5
// CLUSTER (user 2026-09-25: "remove the thermite ... build a cluster grenade that
// explodes on impact, kind of like Fuse's cluster grenade from Apex"; then "let's get
// those cluster grenades" = the real Apex assets). tod_cluster = Fuse's Knuckle Cluster
// canister, textures and sounds pulled from the installed Apex by
// tools/apex_weapons/import_fuse_cluster.py (source_data/tod_fuse_cluster.gdt). The
// script bursts it on its FIRST contact and throws visible bomblets that land, sizzle
// and pop in a chain. Effects are BO3's (Apex particles do not convert). Damage in
// round zombies, like C4.
#define TOD_CLUSTER_WEAPON        "tod_cluster"
#define TOD_CLUSTER_BOMBLET_MODEL "tod_fuse_bomblet"
#define TOD_CLUSTER_FX_BOMBLET    "tod/abfx/fx_abfx_cl_pop_t3"   // docs/206: the Fuse bomblet burst + an ember light (tools/ability_fx/gen_fx.py; was tod/fuse/fx_tod_fuse_bomblet_exp, the one pop in the kit with no light)
#define TOD_CLUSTER_FX_SIZZLE     "tod/fuse/fx_tod_fuse_sizzle"
// THE FLAME (user 2026-09-26: a red-orange flame "that follows the little clusters and the main grenade";
// after the build-11 test: "a little bit more orange ... contained more into a circle with like a flame going
// up ... right now it looks like a flare ... the flame to stay there until it actually explodes"). The stock
// looping orange flame billboard (12.5 x 22.5, one element; replaced the DOA red rpg trail = a red streak
// + red smoke). It stays on each bomblet until that bomblet pops (cluster_fire_on / cluster_fire_off);
// the bomblets land yaw-only so the linked fire stands upright.
// After build 14 (user: "I did kind of like the red glow ... a mixture of like the red glow and a flame ...
// somewhere in the middle"): the flame now burns WITH the old trail's red glow - its orange light and red
// flame cores, cut from the DOA trail minus the streak and the smoke by tools/breacher/make_cluster_glow.js.
#define TOD_CLUSTER_TRAIL         1       // 0 = no fire on the canister / bomblets
#define TOD_CLUSTER_FX_TRAIL      "fire/fx_fire_single_loop_01_xsm_evb"
#define TOD_CLUSTER_FX_GLOW       "tod/breacher/fx_tod_cluster_glow"
#define TOD_CLUSTER_FLIGHT_MIN    0.35    // s each bomblet is in the air
#define TOD_CLUSTER_FLIGHT_MAX    0.60
#define TOD_CLUSTER_GRAVITY       800     // the engine's; shapes the bomblet arcs
#define TOD_CLUSTER_CHARGES       1
#define TOD_CLUSTER_WAIT_MAX      3.0     // s in flight before we give up on a bounce
#define TOD_CLUSTER_BURST_RADIUS  128
#define TOD_CLUSTER_BURST_ZOMBIES 1.0
#define TOD_CLUSTER_BOMBLETS      8
#define TOD_CLUSTER_REACH_MIN     48      // bomblets land this far ahead of the impact ...
#define TOD_CLUSTER_REACH_MAX     256     // ... to this far
#define TOD_CLUSTER_SPREAD        96      // ... and up to this far to either side
#define TOD_CLUSTER_FIRST_DELAY   0.30    // s of sizzle after the last bomblet lands
#define TOD_CLUSTER_GAP_MIN       0.12    // s between bomblets
#define TOD_CLUSTER_GAP_MAX       0.28
// THE LAYERS (user 2026-09-26): a new layer every TOD_CLUSTER_LAYER_EVERY card levels
// (1 layer Lv1-2, 2 at Lv3-5, 3 at Lv6-8). A maxed Cluster pops 8 + 6 + 4 bomblets over
// ~6 s instead of 8 over ~2.5 s. Each layer's bomblets hop HOP_MIN..MAX from a crater.
#define TOD_CLUSTER_LAYER_EVERY   3
#define TOD_CLUSTER_LAYERS_MAX    3
#define TOD_CLUSTER_LAYER2_BOMBLETS 6
#define TOD_CLUSTER_LAYER3_BOMBLETS 4
#define TOD_CLUSTER_HOP_MIN       64
#define TOD_CLUSTER_HOP_MAX       176
#define TOD_CLUSTER_RADIUS        110
#define TOD_CLUSTER_ZOMBIES       1.0     // one bomblet, dead centre (half at the edge)
#define TOD_CLUSTER_ELITE         0.3
#define TOD_CLUSTER_ELITE_BURST   0.4
// HISTORICAL SMALLER-TIER ART (C4 superseded 2026-09-27: all C4 visuals use top tier).
// THE TIERS (user 2026-09-26, after build 16): "I like where we are as the max tier visuals ... tone it
// down each tier below, not each level, but like each tier where you start getting more clusters and more
// C4s ... less explosive, less big, less overwhelming, to kind of push players to keep upgrading."
// A TIER = the charge count (c4_max / cluster_max): C4 Lv1-2 / 3-5 / 6-8 / 9 = tiers 1..4, Cluster
// Lv1-5 / 6-8 / 9 = tiers 1..3 (2026-09-27). The TOP tier is exactly the build-16 look, sound and radius; each lower
// tier plays a shrunk copy of the same effect (tools/breacher/make_tier_fx.js: C4 x0.55 / 0.70 / 0.85 with
// tier 1 muted, Cluster x0.60 / 0.80), a smaller radius and a softer shake (c4_tier_* / cluster_tier_*).
// Damage still rides the card LEVEL (kit_dmg_mult), not the tier.
#define TOD_C4_TIERS              4
#define TOD_CLUSTER_TIERS         3
// DEV TEST: Cluster-only preview cycle. C4 must use its real card tier even in
// dev mode; cycling it made a maxed charge show the large blast only 1 in 4 times.
#define TOD_KIT_TIER_CYCLE        1

// BREACHER AIR STEERING (2026-09-29, user: "the Breacher needs better air steering like the
// Slasher has on map 1"; REWORKED 2026-10-01, user: "I want it to be like the athlete. Its not even
// close to as smooth or functional as athletes upgrade on map 1"). A class passive: every Breacher
// jump and every Fusion launch, from kit_loop's 0.05 s tick (breacher_air_steer). ONE lane owns a
// flight, chosen when it takes off (and again on an outside push or a Fusion launch):
//  ATHLETE MODE - a take-off with momentum (>= TOD_BAIR_MOMENTUM): map 1's ATHLETE lane 4
//    (tower_of_doom_cybercity _tod_athlete.gsc) at its Lv5 numbers, line for line: the STRAFE input
//    curves the flight toward that side (eased, analog), never more than BUDGET deg off the take-off
//    heading, the speed rotated never added, and the cone trims speed carried past 90 deg. The one
//    change: the budget clamp never turns the flight BACK (map 1's could snap toward the budget edge
//    when something else had moved the heading past it; nothing else does here).
//  LAUNCH MODE - a slow take-off (a near-vertical Fusion launch, a standing jump): no momentum to
//    curve, so the stick is air control: the flat velocity eases toward the stick direction (view-
//    relative) at DRIFT_ACCEL, up to DRIFT u/s along it (or the speed you already fly that way, if
//    faster: pushing the way you go never slows you). It never adds speed past max(that, DRIFT).
// THE 2026-09-29 BUG this replaces (the user's 17:56 + 11:2x logs: turned_deg 388..1859 in one 2-3 s
// launch against a 60-deg budget): the drift and the turn ran TOGETHER - the drift swung the heading
// toward the stick, the budget clamp snapped it back, every tick. One owner per flight cannot fight.
// No input = no write in either mode: the engine's own flight is untouched.
#define TOD_BAIR_MOMENTUM         200     // u/s flat at take-off: at least this = ATHLETE mode, under = LAUNCH mode
#define TOD_BAIR_TURN             240     // deg/s at full strafe (map 1: 90 + 30 x Lv5)
#define TOD_BAIR_BUDGET           60      // deg off the take-off heading (map 1: 20 + 8 x Lv5)
#define TOD_BAIR_EASE             0.6     // one tick closes at most 60% of the remaining turn
#define TOD_BAIR_DEADZONE         0.25    // stick magnitude below this steers nothing
#define TOD_BAIR_DEADBAND         3       // deg: a smaller gap is left alone
#define TOD_BAIR_REANCHOR         1.25    // a speed jump past cap x this = a new take-off
#define TOD_BAIR_CAP_FLOOR        200     // u/s: the speed cap never goes below this
#define TOD_BAIR_REVERSE_KEEP     0.35    // a full reversal keeps 35% of the take-off speed
#define TOD_BAIR_DRIFT            170     // u/s: LAUNCH mode's air-control speed along the stick
#define TOD_BAIR_DRIFT_ACCEL      900     // u/s per s (45 u/s a tick: full control in ~0.2 s)
#define TOD_BAIR_RIGHT_SIGN       1       // GetNormalizedMovement()[1] > 0 is RIGHT (map 1, confirmed in play)

#define TOD_KIT_WARRIOR           1
#define TOD_KIT_BREACHER          2
// NECROMANCER (2026-09-26): no grenades ("this class doesn't have ... any
// grenades"); the lethal BUTTON casts the SOUL BOMB. The lethal slot keeps a
// grenade at 0 ammo (the Warrior's recipe: the button is only polled while a
// lethal is held), the tactical is taken.
#define TOD_KIT_NECRO             3

function dev_log( msg )
{
	if ( !( IS_TRUE( level.tod_dev ) || IS_TRUE( level.tod_diag ) ) ) return;
	line = "[TOD_KIT] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function init()
{
	callback::on_spawned( &on_spawned );
	c4 = real_weapon( TOD_C4_WEAPON );
	th = real_weapon( TOD_CLUSTER_WEAPON );
	bash = real_weapon( "tod_bash_sword_zm" );
	bash_p = real_weapon( "tod_bash_punch_zm" );
	bash_g = real_weapon( "tod_bash_gauntlet_zm" );
	dev_log( "INIT c4_fx=always_large_1 c4_preview=0 unlimited=" + unlimited() + " warrior=bash+gravsmash breacher=c4(sticky)+cluster c4_linked=" + isdefined( c4 ) + " cluster_linked=" + isdefined( th ) + " bash_linked=" + isdefined( bash ) + " bash_punch_linked=" + isdefined( bash_p ) + " bash_gauntlet_linked=" + isdefined( bash_g ) );
	dev_log( "INIT_PROXY_NAMES sword=" + linked_as( "tod_bash_sword_zm" ) + " gold=" + linked_as( "tod_cyber_sword_bash_zm" ) + " punch=" + linked_as( "tod_bash_punch_zm" ) + " gauntlet=" + linked_as( "tod_bash_gauntlet_zm" ) + " sword_smash=" + linked_as( TOD_GS_SWORD_PROXY ) );
	// the air slam never takes fall damage (runs first; -1 passes everything else on)
	if ( !isdefined( level.player_damage_callbacks ) ) level.player_damage_callbacks = [];
	ArrayInsert( level.player_damage_callbacks, &gs_fall_guard, 0 );
	level.tod_gs_charge_fn = &gs_charge;   // Gravity Smash charges on kills (_tod_warrior_melee's death callback)
	dev_log( "INIT_GRAVSMASH tier_min=" + TOD_GS_TIER_MIN + " kills=" + TOD_GS_KILLS + "-" + TOD_GS_KILLS_STEP + "/Lv own_kill_ms=" + TOD_GS_OWN_KILL_MS );
	tod_warrior_melee::init();   // the Warrior's crowd swings (2026-09-26 playtest fix)
}

// DEV TEST (level.tod_dev_unlimited_offhand, armed in tod_resolve_dev_flags): no
// cooldowns and no spent charges for any class's lethal or tactical.
function unlimited()
{
	return IS_TRUE( level.tod_dev_unlimited_offhand );
}

function kit_of( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_class ) ) return 0;
	if ( player.tod_class == "slasher" ) return TOD_KIT_WARRIOR;
	if ( player.tod_class == "heavy" ) return TOD_KIT_BREACHER;
	if ( player.tod_class == "necromancer" ) return TOD_KIT_NECRO;
	return 0;
}

// THE ENGINE STRIPS A TRAILING "_zm" FROM A WEAPON ASSET NAME (the proven rule
// in _tod_classes::register_guns / weapon_or_zm). Until 2026-09-26 this looked
// the bash proxies up by their asset spelling ("tod_cyber_sword_bash_zm"), got
// weaponNone, and BASH refused every cast as proxy_not_linked (the user's log:
// INIT ... bash_linked=0). Try the name, then the name minus the suffix.
function real_weapon( name )
{
	w = GetWeapon( name );
	if ( isdefined( w ) && w != level.weaponNone ) return w;
	bare = weapon_bare_name( name );
	if ( bare != name )
	{
		w = GetWeapon( bare );
		if ( isdefined( w ) && w != level.weaponNone ) return w;
	}
	return undefined;
}

function weapon_bare_name( name )
{
	if ( !isdefined( name ) || name.size <= 3 ) return name;
	if ( GetSubStr( name, name.size - 3 ) == "_zm" ) return GetSubStr( name, 0, name.size - 3 );
	return name;
}

// dev: which spelling a proxy resolved under, or "none"
function linked_as( name )
{
	w = GetWeapon( name );
	if ( isdefined( w ) && w != level.weaponNone ) return name;
	bare = weapon_bare_name( name );
	w = GetWeapon( bare );
	if ( isdefined( w ) && w != level.weaponNone ) return bare;
	return "none";
}

// ---------------------------------------------------------------------------
// Per life: one input/state loop and one grenade watcher.
// ---------------------------------------------------------------------------
function on_spawned()
{
	self notify( "tod_kit_respawn" );
	self.tod_bash_busy = undefined;
	self.tod_bash_token = undefined;
	self.tod_bash_charges = undefined;
	self.tod_bash_next_ms = undefined;
	self.tod_gs_busy = undefined;
	self.tod_gs_token = undefined;
	self.tod_gs_diving = undefined;
	self.tod_gs_queued = undefined;
	if ( !isdefined( self.tod_gs_kills ) ) self.tod_gs_kills = 0;   // the charge survives a death; it starts empty
	self.tod_c4_charges = self c4_max();            // every life starts full (= the card level, 2026-09-26)
	self.tod_cluster_charges = self cluster_max();
	self.tod_c4_lv_seen = self c4_lv();
	self.tod_cluster_lv_seen = self cluster_lv();
	self.tod_kit_given = 0;
	self.tod_kit_hud = undefined;
	self thread kit_loop();
	self thread grenade_fire_watch();
}

function can_act()
{
	if ( !isdefined( self ) || !isplayer( self ) || !IsAlive( self ) ) return false;
	if ( self laststand::player_is_in_laststand() ) return false;
	if ( IS_TRUE( self.tod_menu_frozen ) || IS_TRUE( level.tod_upgrade_pause ) ) return false;
	if ( !IS_TRUE( level.tod_class_select_done ) ) return false;
	if ( IS_TRUE( self.tod_jumppad_flying ) ) return false;
	return true;
}

function kit_loop()
{
	self endon( "disconnect" );
	self endon( "tod_kit_respawn" );
	level endon( "end_game" );
	tac_was = true;    // require a release after spawn/menus: never fire a held key
	frag_was = true;
	next_pin = 0;
	last_round = level.round_number;
	for ( ;; )
	{
		wait TOD_KIT_TICK;
		if ( !isdefined( self ) ) return;
		kit = kit_of( self );
		// class change (station, promotion, respawn): hand over or take back
		if ( kit != self.tod_kit_given ) self kit_switch( self.tod_kit_given, kit );
		tac = self SecondaryOffhandButtonPressed();
		frag = self FragButtonPressed();
		tac_edge = ( tac && !tac_was );
		frag_edge = ( frag && !frag_was );
		tac_was = tac;
		frag_was = frag;
		if ( kit == 0 )
		{
			// dev test: the other classes' stock frag never runs out (the Archer's
			// lethal is the Retriever, which _tod_retriever handles)
			if ( unlimited() && GetTime() >= next_pin && isdefined( self.tod_class ) && self.tod_class != "assault" )
			{
				next_pin = GetTime() + TOD_KIT_PIN_MS;
				frag = self zm_utility::get_player_lethal_grenade();
				if ( isdefined( frag ) && frag != level.weaponNone && self HasWeapon( frag ) && self GetWeaponAmmoClip( frag ) < 4 )
					self SetWeaponAmmoClip( frag, 4 );
			}
			continue;
		}
		if ( kit == TOD_KIT_NECRO )
		{
			// a Max Ammo / round award / Widow's Wine re-dress can refill the slot: empty it again
			if ( GetTime() >= next_pin )
			{
				next_pin = GetTime() + TOD_KIT_PIN_MS;
				self necro_pin();
			}
			if ( frag_edge && self can_act() ) self tod_necro_summon::soul_bomb_fire( unlimited() );
			// TACTICAL = INVISIBILITY CLOAK (class pass 2, 2026-09-27; earned by its card,
			// _tod_class_cards). The button reads with the tactical slot empty, as the
			// Archer's grapple already proves.
			if ( tac_edge && self can_act() && isdefined( level.tod_cc_cloak_fire_fn ) ) self [[ level.tod_cc_cloak_fire_fn ]]( unlimited() );
			// PK18: the Cloak off cooldown has a sound (its HUD value N s -> 0 ready; LOCKSTEP cloak_hud)
			if ( isdefined( level.tod_cc_cloak_hud_fn ) )
			{
				cloak_now = self [[ level.tod_cc_cloak_hud_fn ]]( unlimited() );
				if ( cloak_now == 0 && isdefined( self.tod_kit_cloak_was ) && self.tod_kit_cloak_was > 0 ) tod_ability_fx::kit_ready( self, "cloak" );
				self.tod_kit_cloak_was = cloak_now;
			}
			self hud_send( kit );
			continue;
		}
		// new round: the Breacher's charges come back (= the card levels)
		if ( isdefined( level.round_number ) && level.round_number != last_round )
		{
			last_round = level.round_number;
			c4_was = self.tod_c4_charges;
			cl_was = self.tod_cluster_charges;
			self.tod_c4_charges = self c4_max();
			self.tod_cluster_charges = self cluster_max();
			if ( kit == TOD_KIT_BREACHER )
			{
				dev_log( "BREACHER_REFILL player=" + self GetEntityNumber() + " round=" + last_round + " c4=" + self.tod_c4_charges + " (lv " + self c4_lv() + ") cluster=" + self.tod_cluster_charges + " (lv " + self cluster_lv() + ")" );
				// PK18: the rig reloads with a rack you can HEAR - only when a charge actually came back
				if ( ( isdefined( c4_was ) && self.tod_c4_charges > c4_was ) || ( isdefined( cl_was ) && self.tod_cluster_charges > cl_was ) )
					tod_ability_fx::kit_ready( self, "refill" );
			}
		}
		// a press the engine will refuse (empty slot): say why, once per press - and (PK18) let the player hear it
		if ( kit == TOD_KIT_BREACHER && !unlimited() )
		{
			if ( frag_edge && self.tod_c4_charges <= 0 )
			{
				dev_log( "C4_DENIED player=" + self GetEntityNumber() + " reason=" + ( self c4_max() <= 0 ? "locked_no_card" : "empty_until_next_round" ) );
				if ( self can_act() ) tod_ability_fx::kit_deny( self, "c4", "empty" );
			}
			if ( tac_edge && self.tod_cluster_charges <= 0 )
			{
				dev_log( "CLUSTER_DENIED player=" + self GetEntityNumber() + " reason=" + ( self cluster_max() <= 0 ? "locked_no_card" : "empty_until_next_round" ) );
				if ( self can_act() ) tod_ability_fx::kit_deny( self, "cluster", "empty" );
			}
		}
		// a card just raised the level: a fresh full set right away (Hellbound's rule)
		if ( kit == TOD_KIT_BREACHER ) self breacher_level_sync();
		// the Breacher steers in the air (class passive, 2026-09-29) - and every action works there:
		// presses made in the air are counted for BAIR_LAND (an air press with no air throw = refused)
		if ( kit == TOD_KIT_BREACHER ) self breacher_air_steer();
		if ( kit == TOD_KIT_BREACHER && IS_TRUE( self.tod_bair_on ) )
		{
			if ( frag_edge ) self.tod_bair_c4_press++;
			if ( tac_edge ) self.tod_bair_cl_press++;
		}
		now = GetTime();
		if ( now >= next_pin )
		{
			next_pin = now + TOD_KIT_PIN_MS;
			self pin_clips( kit );
		}
		if ( kit == TOD_KIT_WARRIOR )
		{
			if ( self can_act() ) self bash_sync();
			// SMASH DURING A BASH (2026-09-27): queue it; bash_run cuts the dash and hands over
			if ( frag_edge && IS_TRUE( self.tod_bash_busy ) && self can_act() && self gs_ready() )
			{
				self.tod_gs_queued = GetTime();
				dev_log( "GS_QUEUED player=" + self GetEntityNumber() + " reason=bash_busy airborne=" + !( self IsOnGround() ) );
			}
			if ( ( tac_edge || frag_edge ) && self can_act() && !IS_TRUE( self.tod_bash_busy ) )
			{
				if ( tac_edge ) self thread bash_fire();
				else if ( frag_edge ) self thread gravsmash_fire();
			}
		}
		self hud_send( kit );
	}
}

// BREACHER AIR STEERING, one tick (see the TOD_BAIR_* defines). self = a Breacher. Writes the
// velocity only when a lane changed it, so with no input the engine's own flight is untouched.
// [TOD_KIT] BAIR_START / BAIR_MODE (the lane a flight is steered in, and why) / BAIR_LAND (the
// flight's summary: turn, drift, and what the player did in the air: shots, reload, C4 / Cluster
// presses against throws - an air press with no air throw is a refused action).
function breacher_air_steer()
{
	if ( !self can_act() || self IsMantling() || isdefined( self GetLinkedEnt() ) || self IsOnGround() )
	{
		if ( IS_TRUE( self.tod_bair_on ) )
		{
			self.tod_bair_on = undefined;
			dev_log( "BAIR_LAND player=" + self GetEntityNumber() + " air_ms=" + ( GetTime() - self.tod_bair_t0 ) + " mode=" + self.tod_bair_mode
			         + " turned_deg=" + Int( self.tod_bair_turned ) + " drift_peak=" + Int( self.tod_bair_drift_peak )
			         + " fire_ticks=" + self.tod_bair_fire + " reload_ticks=" + self.tod_bair_reload
			         + " c4_press=" + self.tod_bair_c4_press + " c4_air=" + self.tod_bair_c4_air
			         + " cluster_press=" + self.tod_bair_cl_press + " cluster_air=" + self.tod_bair_cl_air );
		}
		self.tod_bair_ref = 0;
		return;
	}
	if ( !IS_TRUE( self.tod_bair_on ) )
	{
		self.tod_bair_on = true;
		self.tod_bair_t0 = GetTime();
		self.tod_bair_turned = 0;
		self.tod_bair_drift_peak = 0;
		self.tod_bair_ref = 0;
		self.tod_bair_cap = TOD_BAIR_CAP_FLOOR;
		self.tod_bair_yaw = 0;
		self.tod_bair_mode = "none";
		self.tod_bair_fire = 0;
		self.tod_bair_reload = 0;
		self.tod_bair_c4_press = 0;
		self.tod_bair_c4_air = 0;
		self.tod_bair_cl_press = 0;
		self.tod_bair_cl_air = 0;
		dev_log( "BAIR_START player=" + self GetEntityNumber() + " speed=" + Int( Length( self GetVelocity() ) ) + ( IS_TRUE( self.tod_fjump_air ) ? " fusion_launch=1" : "" ) );
	}
	// what the player does in the air (the BAIR_LAND summary; reads only)
	if ( self AttackButtonPressed() ) self.tod_bair_fire++;
	if ( self IsReloading() ) self.tod_bair_reload++;
	if ( !isdefined( self.tod_bair_anchor_ms ) ) self.tod_bair_anchor_ms = 0;
	v = self GetVelocity();
	out_x = v[ 0 ];
	out_y = v[ 1 ];
	dirty = false;
	fwd_in = 0;
	right_in = 0;
	m = self GetNormalizedMovement();
	if ( isdefined( m ) )
	{
		fwd_in = m[ 0 ];
		right_in = m[ 1 ] * TOD_BAIR_RIGHT_SIGN;
	}
	yaw = self GetPlayerAngles()[ 1 ];
	f = AnglesToForward( ( 0, yaw, 0 ) );
	r = AnglesToRight( ( 0, yaw, 0 ) );

	// THE ANCHOR is the flight the engine hands us: the take-off heading and speed (map 1's rule),
	// re-taken on an outside push (x REANCHOR) or a Fusion launch - and with it, the MODE.
	sp0 = Sqrt( ( out_x * out_x ) + ( out_y * out_y ) );
	relaunch = ( isdefined( self.tod_fjump_launch_ms ) && self.tod_fjump_launch_ms > self.tod_bair_anchor_ms );
	if ( self.tod_bair_ref <= 0 || sp0 > ( self.tod_bair_cap * TOD_BAIR_REANCHOR ) || relaunch )
	{
		why = "takeoff";
		if ( relaunch ) why = "fusion";
		else if ( self.tod_bair_ref > 0 ) why = "push";
		self.tod_bair_yaw = yaw;
		if ( sp0 > 1 ) self.tod_bair_yaw = VectorToAngles( ( out_x, out_y, 0 ) )[ 1 ];
		self.tod_bair_ref = sp0;
		if ( self.tod_bair_ref < 1 ) self.tod_bair_ref = 1;
		self.tod_bair_mode = "launch";
		if ( sp0 >= TOD_BAIR_MOMENTUM ) self.tod_bair_mode = "athlete";
		self.tod_bair_cap = sp0;
		if ( self.tod_bair_mode == "launch" && self.tod_bair_cap < TOD_BAIR_DRIFT ) self.tod_bair_cap = TOD_BAIR_DRIFT;
		if ( self.tod_bair_cap < TOD_BAIR_CAP_FLOOR ) self.tod_bair_cap = TOD_BAIR_CAP_FLOOR;
		self.tod_bair_anchor_ms = GetTime();
		dev_log( "BAIR_MODE player=" + self GetEntityNumber() + " mode=" + self.tod_bair_mode + " why=" + why + " speed=" + Int( sp0 ) + " heading=" + Int( self.tod_bair_yaw ) );
	}

	if ( self.tod_bair_mode == "launch" )
	{
		// LAUNCH MODE: air control. The flat velocity eases toward the stick x DRIFT (or the speed
		// already carried that way, if faster), DRIFT_ACCEL at most per second; it never turns a flight
		// the stick is not asking for, and it can never end up faster than max(now, DRIFT).
		mag = Sqrt( ( fwd_in * fwd_in ) + ( right_in * right_in ) );
		if ( mag >= TOD_BAIR_DEADZONE )
		{
			if ( mag > 1 ) mag = 1;
			wx = ( f[ 0 ] * fwd_in ) + ( r[ 0 ] * right_in );
			wy = ( f[ 1 ] * fwd_in ) + ( r[ 1 ] * right_in );
			wl = Sqrt( ( wx * wx ) + ( wy * wy ) );
			if ( wl > 0.001 )
			{
				wx = wx / wl;
				wy = wy / wl;
				along = ( out_x * wx ) + ( out_y * wy );
				want = TOD_BAIR_DRIFT * mag;
				if ( along > want ) want = along;
				dx = ( wx * want ) - out_x;
				dy = ( wy * want ) - out_y;
				dl = Sqrt( ( dx * dx ) + ( dy * dy ) );
				if ( dl > 0.5 )
				{
					acc = TOD_BAIR_DRIFT_ACCEL * TOD_KIT_TICK;
					if ( dl > acc )
					{
						dx = dx * acc / dl;
						dy = dy * acc / dl;
					}
					out_x = out_x + dx;
					out_y = out_y + dy;
					dirty = true;
					drift = ( out_x * wx ) + ( out_y * wy );
					if ( drift > self.tod_bair_drift_peak ) self.tod_bair_drift_peak = drift;
				}
			}
		}
	}
	else
	{
		// ATHLETE MODE: map 1's ATHLETE lane 4 (strafe only), budget + cone
		sp = sp0;
		if ( sp > 1 )
		{
			c_yaw = VectorToAngles( ( out_x, out_y, 0 ) )[ 1 ];
			strafe = Abs( right_in );
			if ( strafe >= TOD_BAIR_DEADZONE )
			{
				if ( strafe > 1 ) strafe = 1;
				w_yaw = VectorToAngles( ( r[ 0 ] * right_in, r[ 1 ] * right_in, 0 ) )[ 1 ];
				gap = AngleClamp180( w_yaw - c_yaw );
				if ( Abs( gap ) >= TOD_BAIR_DEADBAND )
				{
					step_max = TOD_BAIR_TURN * strafe * TOD_KIT_TICK;
					ease = Abs( gap ) * TOD_BAIR_EASE;
					if ( step_max > ease ) step_max = ease;
					step = gap;
					if ( step > step_max ) step = step_max;
					else if ( step < ( 0 - step_max ) ) step = 0 - step_max;
					// THE STEER BUDGET: never further than BUDGET from the take-off heading, either way -
					// and the clamp only ever shortens a step, never turns it back the other way
					cur_dev = AngleClamp180( c_yaw - self.tod_bair_yaw );
					new_dev = cur_dev + step;
					if ( new_dev > TOD_BAIR_BUDGET ) step = TOD_BAIR_BUDGET - cur_dev;
					else if ( new_dev < ( 0 - TOD_BAIR_BUDGET ) ) step = ( 0 - TOD_BAIR_BUDGET ) - cur_dev;
					if ( ( step * gap ) < 0 ) step = 0;
					if ( Abs( step ) > 0.05 )
					{
						c_yaw = c_yaw + step;
						nf = AnglesToForward( ( 0, c_yaw, 0 ) );
						out_x = nf[ 0 ] * sp;
						out_y = nf[ 1 ] * sp;
						self.tod_bair_turned = self.tod_bair_turned + Abs( step );
						dirty = true;
					}
				}
			}
			// THE CONE: past 90 deg off the take-off line the speed cap shrinks toward REVERSE_KEEP
			dev = Abs( AngleClamp180( c_yaw - self.tod_bair_yaw ) );
			keep = 1;
			if ( dev > 90 )
			{
				t = ( dev - 90 ) / 90;
				if ( t > 1 ) t = 1;
				keep = 1 - ( t * ( 1 - TOD_BAIR_REVERSE_KEEP ) );
			}
			cap = self.tod_bair_ref * keep;
			if ( cap < TOD_BAIR_CAP_FLOOR ) cap = TOD_BAIR_CAP_FLOOR;
			self.tod_bair_cap = cap;
			if ( sp > cap )
			{
				out_x = out_x * cap / sp;
				out_y = out_y * cap / sp;
				dirty = true;
			}
		}
	}
	if ( dirty )
		self SetVelocity( ( out_x, out_y, v[ 2 ] ) );
}

// Take the other class's kit back first, then give this class's. The stock
// frag is the lethal every non-Breacher class carries; the Warrior keeps it in
// the slot with its clip pinned to 0 (the button is polled for GRAVITY SMASH).
function kit_switch( from, to )
{
	self tod_cyber_sword::update( false, "kit_switch" );
	if ( from == TOD_KIT_BREACHER ) self take_breacher();
	if ( to == TOD_KIT_BREACHER ) self give_breacher();
	if ( to == TOD_KIT_NECRO ) self necro_pin();
	if ( from == TOD_KIT_NECRO && to != TOD_KIT_NECRO && to != TOD_KIT_BREACHER ) self give_back_frag();
	// the frag the Warrior kept pinned at 0 is refilled ONLY for a kit-less class: a Breacher's
	// lethal is the C4 and a Necromancer's grenade is pinned empty, and both were given above, so
	// "!= WARRIOR" refilled THEIR slot (2026-10-01, the crown's class terminal: the first path
	// that switches a living player between two kits)
	if ( from == TOD_KIT_WARRIOR && to == 0 )
	{
		frag = self zm_utility::get_player_lethal_grenade();
		if ( isdefined( frag ) && frag != level.weaponNone && self HasWeapon( frag ) ) self SetWeaponAmmoClip( frag, 2 );
	}
	if ( to == TOD_KIT_WARRIOR ) self pin_clips( to );   // the frag clip to 0 now, not a pin tick later (a Necromancer's give_back_frag filled it)
	if ( to == 0 && from != 0 )
	{
		self.tod_kit_hud = undefined;
		self LuiNotifyEvent( &"tod_archer_abil", 4, 0, 0, 0, 0 );
	}
	dev_log( "SWITCH player=" + self GetEntityNumber() + " from=" + from + " to=" + to + " class=" + self.tod_class );
	self.tod_kit_given = to;
}

// THE CLASS TERMINAL (2026-10-01): a Breacher who changes class takes his charges back. Planted C4
// would otherwise sit armed on the walls with its detonate lane gone (take_breacher took the C4
// out of the slot). self = player. Returns how many were removed.
function clear_planted_c4()
{
	c4 = real_weapon( TOD_C4_WEAPON );
	if ( !isdefined( c4 ) ) return 0;
	watcher = self weaponobjects::getWeaponObjectWatcherByWeapon( c4 );
	if ( !isdefined( watcher ) || !isdefined( watcher.objectArray ) ) return 0;
	n = 0;
	foreach ( o in watcher.objectArray )
		if ( isdefined( o ) ) n++;
	watcher weaponobjects::deleteWeaponObjectArray();
	dev_log( "C4_CLEARED player=" + self GetEntityNumber() + " n=" + n + " (class change)" );
	return n;
}

function pin_clips( kit )
{
	if ( kit == TOD_KIT_WARRIOR )
	{
		frag = self zm_utility::get_player_lethal_grenade();
		if ( isdefined( frag ) && frag != level.weaponNone && self HasWeapon( frag ) && self GetWeaponAmmoClip( frag ) != 0 )
			self SetWeaponAmmoClip( frag, 0 );
		return;
	}
	// BREACHER: each clip IS its charge count. A stock Max Ammo or round grenade
	// award refills past it; this caps it back. A slot lost to anything else
	// (a script that re-gave the frag) is re-given.
	c4 = real_weapon( TOD_C4_WEAPON );
	th = real_weapon( TOD_CLUSTER_WEAPON );
	if ( ( isdefined( c4 ) && !( self HasWeapon( c4 ) ) ) || ( isdefined( th ) && !( self HasWeapon( th ) ) ) )
		self give_breacher();
	if ( isdefined( c4 ) && self HasWeapon( c4 ) && self GetWeaponAmmoClip( c4 ) != self.tod_c4_charges )
		self SetWeaponAmmoClip( c4, self.tod_c4_charges );
	if ( isdefined( th ) && self HasWeapon( th ) && self GetWeaponAmmoClip( th ) != self.tod_cluster_charges )
		self SetWeaponAmmoClip( th, self.tod_cluster_charges );
}

// ---------------------------------------------------------------------------
// NECROMANCER: no grenades at all (its Widow's Wine rides Burned Out instead -
// _tod_necro_skull.gsc).
// ---------------------------------------------------------------------------
// The lethal slot holds a grenade at 0 ammo (so FragButtonPressed reads, and so
// stock Widow's Wine's contact web - it needs a grenade - never fires); the
// tactical is taken.
function necro_pin()
{
	taken = "";
	tac = self zm_utility::get_player_tactical_grenade();
	if ( isdefined( tac ) && tac != level.weaponNone )
	{
		if ( self HasWeapon( tac ) ) self TakeWeapon( tac );
		self zm_utility::set_player_tactical_grenade( level.weaponNone );
		taken += " tactical=" + tac.name;
	}
	lethal = self zm_utility::get_player_lethal_grenade();
	if ( !isdefined( lethal ) || lethal == level.weaponNone )
	{
		lethal = GetWeapon( "frag_grenade" );
		if ( !isdefined( lethal ) || lethal == level.weaponNone ) return;
		self zm_utility::set_player_lethal_grenade( lethal );
		taken += " lethal_slot=frag";
	}
	if ( !( self HasWeapon( lethal ) ) ) self GiveWeapon( lethal );
	if ( self GetWeaponAmmoClip( lethal ) != 0 )
	{
		self SetWeaponAmmoClip( lethal, 0 );
		taken += " emptied=" + lethal.name;
	}
	if ( taken != "" ) dev_log( "NECRO_PIN player=" + self GetEntityNumber() + taken );
}

function give_back_frag()
{
	frag = GetWeapon( "frag_grenade" );
	if ( !isdefined( frag ) || frag == level.weaponNone ) return;
	if ( !( self HasWeapon( frag ) ) ) self GiveWeapon( frag );
	self zm_utility::set_player_lethal_grenade( frag );
	self SetWeaponAmmoClip( frag, 2 );
}

// ---------------------------------------------------------------------------
// BREACHER: C4 (lethal, sticky) + CLUSTER (tactical)
// ---------------------------------------------------------------------------
function give_breacher()
{
	c4 = real_weapon( TOD_C4_WEAPON );
	if ( isdefined( c4 ) )
	{
		self c4_watcher( c4 );
		old = self zm_utility::get_player_lethal_grenade();
		if ( isdefined( old ) && old != level.weaponNone && old != c4 && self HasWeapon( old ) ) self TakeWeapon( old );
		if ( !( self HasWeapon( c4 ) ) ) self GiveWeapon( c4 );
		self zm_utility::set_player_lethal_grenade( c4 );
		self SetWeaponAmmoClip( c4, self.tod_c4_charges );
	}
	th = real_weapon( TOD_CLUSTER_WEAPON );
	if ( isdefined( th ) )
	{
		old = self zm_utility::get_player_tactical_grenade();
		if ( isdefined( old ) && old != level.weaponNone && old != th && self HasWeapon( old ) ) self TakeWeapon( old );
		if ( !( self HasWeapon( th ) ) ) self GiveWeapon( th );
		self zm_utility::set_player_tactical_grenade( th );
		self SetWeaponAmmoClip( th, self.tod_cluster_charges );
	}
	dev_log( "BREACHER_GIVE player=" + self GetEntityNumber() + " c4=" + isdefined( c4 ) + " cluster=" + isdefined( th ) + " c4_clip=" + self.tod_c4_charges + " cluster_clip=" + self.tod_cluster_charges );
}

function take_breacher()
{
	c4 = real_weapon( TOD_C4_WEAPON );
	th = real_weapon( TOD_CLUSTER_WEAPON );
	if ( isdefined( c4 ) && self HasWeapon( c4 ) ) self TakeWeapon( c4 );
	if ( isdefined( th ) && self HasWeapon( th ) ) self TakeWeapon( th );
	frag = GetWeapon( "frag_grenade" );
	if ( isdefined( frag ) && frag != level.weaponNone )
	{
		if ( !( self HasWeapon( frag ) ) ) self GiveWeapon( frag );
		self zm_utility::set_player_lethal_grenade( frag );
		self SetWeaponAmmoClip( frag, 2 );
	}
	self zm_utility::set_player_tactical_grenade( level.weaponNone );
	dev_log( "BREACHER_TAKE player=" + self GetEntityNumber() );
}

// THE WATCHER (donor docs/97): stock _weaponobjects routes the detonate button
// and double-tap USE to the watcher owning the offhand. Without one the press is
// silently ignored. createWeaponObjectWatcher dedups by name.
function c4_watcher( w )
{
	watcher = self weaponobjects::getWeaponObjectWatcherByWeapon( w );
	if ( isdefined( watcher ) ) return;
	watcher = self weaponobjects::createUseWeaponObjectWatcher( TOD_C4_WEAPON, self.team );
	watcher.onDetonateCallback = &c4_detonate_cb;
	watcher.onDamage = &c4_on_damage;
	watcher.altDetonate = true;
	watcher.headIcon = false;
	watcher.detectable = false;
	watcher.playDestroyedDialog = false;
	watcher.ownerGetsAssist = false;
	dev_log( "C4_WATCHER player=" + self GetEntityNumber() + " created=1" );
}

function c4_detonate_cb( attacker, weapon, target )
{
	dev_log( "C4_DETONATE cause=press_or_use by=" + ( isdefined( attacker ) && isplayer( attacker ) ? attacker GetEntityNumber() : -1 ) + " origin=" + self.origin );
	self weaponobjects::weaponDetonate( attacker, weapon );
}

// Shot, or caught in another charge's blast, a planted C4 goes off. Only a
// PLAYER's damage counts: an enemy never defuses the trap.
function c4_on_damage( watcher )
{
	self endon( "death" );
	self endon( "detonating" );
	self SetCanDamage( true );
	self.maxhealth = 100000;
	self.health = self.maxhealth;
	for ( ;; )
	{
		self waittill( "damage", dmg, attacker, dir, point, mod, model_name, tag_name, part_name, weapon );
		if ( isdefined( attacker ) && isplayer( attacker ) ) break;
	}
	dev_log( "C4_DETONATE cause=shot by=" + attacker GetEntityNumber() + " weapon=" + ( isdefined( weapon ) ? weapon.name : "none" ) + " origin=" + self.origin );
	watcher thread weaponobjects::waitAndDetonate( self, 0.0, attacker, weapon );
}

function grenade_fire_watch()
{
	self endon( "disconnect" );
	self endon( "tod_kit_respawn" );
	level endon( "end_game" );
	for ( ;; )
	{
		self waittill( "grenade_fire", grenade, weapon );
		if ( !isdefined( grenade ) || !isdefined( weapon ) ) continue;
		th = real_weapon( TOD_CLUSTER_WEAPON );
		if ( isdefined( th ) && weapon == th )
		{
			if ( self.tod_cluster_charges > 0 && !unlimited() ) self.tod_cluster_charges--;
			fwd = AnglesToForward( self GetPlayerAngles() );
			tier = self kit_tier( "cluster" );
			air = !( self IsOnGround() );
			if ( air && IS_TRUE( self.tod_bair_on ) ) self.tod_bair_cl_air++;
			dev_log( "CLUSTER_THROW player=" + self GetEntityNumber() + " left=" + self.tod_cluster_charges + " tier=" + tier + " airborne=" + air );
			level thread cluster_watch( self, grenade, th, fwd, tier );
			continue;
		}
		c4 = real_weapon( TOD_C4_WEAPON );
		if ( isdefined( c4 ) && weapon == c4 )
		{
			if ( self.tod_c4_charges > 0 && !unlimited() ) self.tod_c4_charges--;
			planted = 0;
			watcher = self weaponobjects::getWeaponObjectWatcherByWeapon( c4 );
			if ( isdefined( watcher ) && isdefined( watcher.objectArray ) ) planted = watcher.objectArray.size;
			tier = self kit_tier( "c4" );
			air = !( self IsOnGround() );
			if ( air && IS_TRUE( self.tod_bair_on ) ) self.tod_bair_c4_air++;
			dev_log( "C4_PLANT player=" + self GetEntityNumber() + " left=" + self.tod_c4_charges + " watcher=" + isdefined( watcher ) + " planted=" + planted + " tier=" + tier + " airborne=" + air );
			level thread c4_real_watch( self, grenade, c4, tier );
			level thread c4_stick_watch( self, grenade );
		}
	}
}

function c4_real_watch( owner, grenade, weapon, tier )
{
	level endon( "end_game" );
	if ( !isdefined( level.tod_c4_fx_seq ) ) level.tod_c4_fx_seq = 0;
	level.tod_c4_fx_seq++;
	fx_id = level.tod_c4_fx_seq;
	planted_ms = GetTime();
	dev_log( "C4_FX_ARM rev=always_large_1 id=" + fx_id + " owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " card_tier=" + tier + " visual_tier=4 effect=" + c4_tier_fx( tier ) );
	grenade waittill( "explode", pos );
	if ( !isdefined( pos ) )
	{
		dev_log( "C4_LOST id=" + fx_id + " owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " after_ms=" + ( GetTime() - planted_ms ) + " (exploded with no position)" );
		return;
	}
	dev_log( "C4_EXPLODE owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " after_ms=" + ( GetTime() - planted_ms ) + " origin=" + pos );
	blast( pos, c4_tier_radius( tier ) * demo_radius_mult( owner ), owner, TOD_C4_ZOMBIES, TOD_C4_ELITE_ZOMBIES, weapon, "C4", tier, fx_id );
}

// STICK WHERE IT HITS (user 2026-09-26: "the C4, if we can get that to stick to the
// actual part of the body it hits, rather than just putting it on the right leg").
// The engine's "Stick to all" puts it on one bone; the charge is then moved to the bone
// its FLIGHT PATH passes closest to and re-linked there. [TOD_KIT] C4_STICK reports it.
// WHICH ENEMY IT STUCK TO, three lanes, first wins (via= in the log):
//   actor_notify  the actor's "grenade_stuck" - stock only listens for it on vehicles and
//                 destructibles, and the 16:08 run (37 plants) never saw it on a zombie;
//   stuck_notify  the GRENADE's own "stuck_to_player" (stock _weapons::checkStuckToPlayer);
//   linked_ent    polling the grenade's GetLinkedEnt() every 0.05 s.
// None within TOD_C4_STICK_WAIT = C4_STICK result=no_stick_signal with what it saw.
function c4_stick_watch( owner, grenade )
{
	level endon( "end_game" );
	grenade endon( "death" );
	near = enemies_within( grenade.origin, TOD_C4_STICK_SCAN );
	foreach ( z in near )
		z thread c4_stuck_listen( grenade );
	grenade thread c4_stuck_self();
	// the flight path, two samples deep: the frame before the stick is the impact side
	waited = 0;
	host = undefined;
	while ( waited < TOD_C4_STICK_WAIT && !IS_TRUE( grenade.tod_c4_stuck ) )
	{
		host = grenade GetLinkedEnt();
		if ( isdefined( host ) && IsActor( host ) )
		{
			c4_stuck_on( grenade, host, "linked_ent" );
			break;
		}
		// docs/206: ARMED the moment it comes to rest (a wall, the floor), not when the stick window ends: still
		// across two samples (0.1 s; a throw's apex never holds still that long). The user's 2026-10-03 run set
		// off every charge 0.1-0.35 s after the throw, inside the 3 s window, so the tell never played once.
		if ( !isdefined( grenade.tod_abfx_c4 ) && isdefined( grenade.tod_c4_prev2 ) && DistanceSquared( grenade.tod_c4_prev2, grenade.origin ) < 0.25 && DistanceSquared( grenade.tod_c4_prev, grenade.origin ) < 0.25 )
		{
			grenade.tod_abfx_c4 = tod_ability_fx::c4_armed( grenade );
			dev_log( "C4_TELL at=rest after_ms=" + int( waited * 1000 ) );
		}
		grenade.tod_c4_prev2 = grenade.tod_c4_prev;
		grenade.tod_c4_prev = grenade.origin;
		wait 0.05;
		waited += 0.05;
	}
	if ( !IS_TRUE( grenade.tod_c4_stuck ) )
	{
		// what it did land on: world (no link, no enemy close) or an enemy nothing reported
		nd = 99999;
		foreach ( z in enemies_within( grenade.origin, 128 ) )
		{
			d = Distance( z.origin + ( 0, 0, 36 ), grenade.origin );
			if ( d < nd ) nd = d;
		}
		still = ( isdefined( grenade.tod_c4_prev ) ? Distance( grenade.tod_c4_prev, grenade.origin ) : -1 );
		dev_log( "C4_STICK result=no_stick_signal near_at_throw=" + near.size + " linked=" + ( isdefined( host ) ? ( IsActor( host ) ? "actor" : "other" ) : "none" ) + " last_step=" + Int( still ) + "u nearest_enemy=" + ( nd < 99999 ? Int( nd ) + "u" : "none_in_128" ) + " origin=" + grenade.origin );
	}
	if ( isdefined( grenade ) && !isdefined( grenade.tod_abfx_c4 ) )
	{
		grenade.tod_abfx_c4 = tod_ability_fx::c4_armed( grenade );   // docs/206: stuck to a zombie, or still moving when the window closed
		dev_log( "C4_TELL at=" + ( IS_TRUE( grenade.tod_c4_stuck ) ? "stuck" : "window_end" ) + " after_ms=" + int( waited * 1000 ) );
	}
	grenade notify( "tod_c4_stick_done" );
}

function c4_stuck_on( grenade, actor, via )
{
	if ( !isdefined( grenade ) || !isdefined( actor ) || IS_TRUE( grenade.tod_c4_stuck ) ) return;
	grenade.tod_c4_stuck = true;
	grenade.tod_c4_via = via;
	grenade thread c4_rebone( actor );
}

function c4_stuck_listen( grenade )   // self = an enemy near the throw
{
	self endon( "death" );
	grenade endon( "death" );
	grenade endon( "tod_c4_stick_done" );
	for ( ;; )
	{
		self waittill( "grenade_stuck", missile );
		if ( isdefined( missile ) && missile == grenade ) break;
	}
	c4_stuck_on( grenade, self, "actor_notify" );
}

function c4_stuck_self()   // self = the C4
{
	self endon( "death" );
	self endon( "tod_c4_stick_done" );
	self waittill( "stuck_to_player", ent );
	if ( isdefined( ent ) && IsActor( ent ) )
		c4_stuck_on( self, ent, "stuck_notify" );
	else
		dev_log( "C4_STICK result=stuck_non_actor ent=" + ( isdefined( ent ) ? ent GetEntityNumber() : -1 ) );
}

function c4_rebone( actor )   // self = the stuck C4
{
	bones = array( "j_head", "j_neck", "j_spine4", "j_spineupper", "j_spinelower", "j_mainroot",
		"j_shoulder_le", "j_shoulder_ri", "j_elbow_le", "j_elbow_ri", "j_wrist_le", "j_wrist_ri",
		"j_hip_le", "j_hip_ri", "j_knee_le", "j_knee_ri", "j_ankle_le", "j_ankle_ri" );
	engine_at = self.origin;
	p1 = self.tod_c4_prev;
	p0 = self.tod_c4_prev2;
	if ( !isdefined( p1 ) ) p1 = engine_at;
	if ( !isdefined( p0 ) || DistanceSquared( p0, p1 ) < 1 ) p0 = p1 - VectorNormalize( actor.origin + ( 0, 0, 40 ) - p1 );
	dir = VectorNormalize( p1 - p0 );
	best = undefined;
	best_d = 99999;
	best_c = undefined;
	engine_bone = "none";
	engine_d = 99999;
	foreach ( b in bones )
	{
		if ( !( actor HasPart( b ) ) ) continue;
		o = actor GetTagOrigin( b );
		if ( !isdefined( o ) ) continue;
		de = Distance( o, engine_at );
		if ( de < engine_d ) { engine_d = de; engine_bone = b; }
		// the point on the flight ray (p1 on, 128 u) nearest this bone
		along = VectorDot( o - p1, dir );
		if ( along < 0 ) along = 0;
		if ( along > 128 ) along = 128;
		c = p1 + dir * along;
		d = Distance( o, c );
		if ( d < best_d ) { best_d = d; best = b; best_c = c; }
	}
	if ( !isdefined( best ) )
	{
		dev_log( "C4_STICK actor=" + actor GetEntityNumber() + " result=no_known_bones engine_near=" + engine_bone );
		return;
	}
	// sit on the body's surface on the side the charge came from, not inside the joint
	o = actor GetTagOrigin( best );
	off = best_c - o;
	if ( Length( off ) > TOD_C4_STICK_SKIN ) off = VectorNormalize( off ) * TOD_C4_STICK_SKIN;
	ang = actor GetTagAngles( best );
	local = ( VectorDot( off, AnglesToForward( ang ) ), 0 - VectorDot( off, AnglesToRight( ang ) ), VectorDot( off, AnglesToUp( ang ) ) );
	self Unlink();
	self LinkTo( actor, best, local, ( 0, 0, 0 ) );
	wait 0.05;
	if ( !isdefined( self ) || !isdefined( actor ) ) return;
	took = Distance( self.origin, o + off );
	dev_log( "C4_STICK via=" + self.tod_c4_via + " actor=" + actor GetEntityNumber() + " engine_near=" + engine_bone + " ("+ Int( engine_d ) + "u) picked=" + best + " ray_miss=" + Int( best_d ) + "u moved=" + Int( Distance( engine_at, self.origin ) ) + "u off_target=" + Int( took ) + "u result=" + ( took < 12 ? "relinked" : "engine_kept_it" ) );
}

// The impact mark lives on a struct, not the grenade: a direct hit on an enemy
// explodes the grenade on the engine side (sentientImpactExplode) and deletes it,
// so the watcher must still be able to read where.
function cluster_bounce_relay( mark )
{
	self endon( "death" );
	self waittill( "grenade_bounce", pos, normal, ent );
	if ( isdefined( mark.hit ) ) return;
	mark.hit = pos;
	mark.normal = normal;
	mark.lane = "impact";
}

function cluster_explode_relay( mark )
{
	self waittill( "explode", pos );
	if ( isdefined( mark.hit ) || !isdefined( pos ) ) return;
	mark.hit = pos;
	mark.lane = "explode";
}

// CLUSTER: Fuse's Knuckle Cluster. The canister bursts where it first lands, then
// throws its BOMBLETS: each is a real model on a gravity arc to a spot ahead of the
// throw, lands, sizzles (Apex fuse sound + spark), and they pop one after another.
function cluster_watch( owner, grenade, weapon, forward, tier )
{
	level endon( "end_game" );
	mark = SpawnStruct();
	grenade thread cluster_bounce_relay( mark );
	grenade thread cluster_explode_relay( mark );
	fire = cluster_fire_on( grenade );
	pos = grenade.origin;
	waited = 0;
	while ( isdefined( grenade ) && !isdefined( mark.hit ) && waited < TOD_CLUSTER_WAIT_MAX )
	{
		pos = grenade.origin;
		wait 0.05;
		waited += 0.05;
	}
	wait 0.05;   // one frame for an explode notify racing the grenade's deletion
	// no bounce, no explode: either the canister struck an enemy (the engine deletes
	// it with neither notify; burst where it last was) or it flew the whole wait
	lane = ( ( waited < TOD_CLUSTER_WAIT_MAX ) ? "direct_hit" : "timeout" );
	if ( isdefined( mark.hit ) )
	{
		pos = mark.hit;
		lane = mark.lane;
	}
	normal = ( 0, 0, 1 );
	if ( isdefined( mark.normal ) ) normal = mark.normal;
	cluster_fire_off( fire );
	if ( isdefined( grenade ) ) grenade Delete();
	// lift off the surface it hit, so a wall impact does not trace from inside the wall
	pos = pos + normal * 8;
	dev_log( "CLUSTER_IMPACT owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " lane=" + lane + " origin=" + pos + " after_s=" + waited );
	hits = cluster_pop( pos, cluster_tier_radius( TOD_CLUSTER_BURST_RADIUS, tier ) * demo_radius_mult( owner ), owner, TOD_CLUSTER_BURST_ZOMBIES, TOD_CLUSTER_ELITE_BURST, weapon, true, tier );

	// where the bomblets land: ahead of the throw, fanned, each on a floor that the
	// impact can see (never through a wall or a sealed door)
	flat = ( forward[ 0 ], forward[ 1 ], 0 );
	if ( LengthSquared( flat ) < 0.0001 ) flat = ( 1, 0, 0 );
	flat = VectorNormalize( flat );
	right = ( -flat[ 1 ], flat[ 0 ], 0 );
	froms = [];
	spots = [];
	for ( i = 0; i < TOD_CLUSTER_BOMBLETS; i++ )
	{
		target = pos + flat * RandomFloatRange( TOD_CLUSTER_REACH_MIN, TOD_CLUSTER_REACH_MAX ) + right * RandomFloatRange( -TOD_CLUSTER_SPREAD, TOD_CLUSTER_SPREAD );
		s = cluster_land_spot( pos, target, flat );
		if ( !isdefined( s ) ) continue;           // over the void: that bomblet is lost
		froms[ froms.size ] = pos;
		spots[ spots.size ] = s;
	}

	// THE LAYERS (user 2026-09-26: "the max out cluster grenades need to also last
	// longer ... adding more nested nades, like an extra layer ... for each tier").
	// Layer 1 = the fan above. Each further layer: some of the last wave's craters
	// throw fresh bomblets a short hop in any direction, which land, sizzle and pop.
	// 1 layer at Lv1-2, 2 at Lv3-5, 3 at Lv6-8 (cluster_layers).
	layers = cluster_layers( owner );
	start_ms = GetTime();
	popped = 0;
	thrown = 0;
	last = [];
	for ( layer = 1; layer <= layers; layer++ )
	{
		if ( layer > 1 )
		{
			if ( last.size == 0 ) break;           // nothing popped: no craters to throw from
			count = ( ( layer == 2 ) ? TOD_CLUSTER_LAYER2_BOMBLETS : TOD_CLUSTER_LAYER3_BOMBLETS );
			froms = [];
			spots = [];
			for ( i = 0; i < count; i++ )
			{
				parent = last[ RandomInt( last.size ) ] + ( 0, 0, 8 );
				dir = AnglesToForward( ( 0, RandomFloat( 360 ), 0 ) );
				s = cluster_land_spot( parent, parent + dir * RandomFloatRange( TOD_CLUSTER_HOP_MIN, TOD_CLUSTER_HOP_MAX ), dir );
				if ( !isdefined( s ) ) continue;
				froms[ froms.size ] = parent;
				spots[ spots.size ] = s;
			}
		}
		wave = cluster_wave( froms, spots, owner, weapon, tier );
		popped += wave.popped;
		thrown += spots.size;
		hits += wave.hits;
		last = wave.popped_spots;
		dev_log( "CLUSTER_LAYER owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " layer=" + layer + "/" + layers + " bomblets=" + wave.popped + "/" + spots.size + " hits=" + wave.hits );
	}
	dev_log( "CLUSTER_END owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " lv=" + ( isdefined( owner ) && isplayer( owner ) ? owner cluster_lv() : -1 ) + " tier=" + tier + " layers=" + layers + " bomblets=" + popped + "/" + thrown + " enemy_hits=" + hits + " chain_ms=" + ( GetTime() - start_ms ) );
}

// How many bomblet layers this owner's Cluster card buys (1 / 2 / 3).
function cluster_layers( owner )
{
	if ( !isdefined( owner ) || !isplayer( owner ) ) return 1;
	n = 1 + Int( owner cluster_lv() / TOD_CLUSTER_LAYER_EVERY );
	if ( n > TOD_CLUSTER_LAYERS_MAX ) n = TOD_CLUSTER_LAYERS_MAX;
	return n;
}

// Where a bomblet thrown from `from` toward `target` comes down: stopped short of
// whatever the throw met (never through a wall or a sealed door), then onto the
// floor under it. Undefined = over the void (that bomblet is lost).
function cluster_land_spot( from, target, dir )
{
	across = BulletTrace( from + ( 0, 0, 12 ), target + ( 0, 0, 12 ), false, undefined );
	land = across[ "position" ] - dir * 8;
	floor = BulletTrace( land + ( 0, 0, 12 ), land - ( 0, 0, 160 ), false, undefined );
	if ( floor[ "fraction" ] >= 1 ) return undefined;
	return floor[ "position" ] + ( 0, 0, 2 );
}

// One wave: bomblet i flies froms[ i ] -> spots[ i ] on its own arc, they all land
// and sizzle, then pop one after another. Returns popped / hits / popped_spots.
function cluster_wave( froms, spots, owner, weapon, tier )
{
	w = SpawnStruct();
	w.popped = 0;
	w.hits = 0;
	w.popped_spots = [];
	bomblets = [];
	longest = 0;
	for ( i = 0; i < spots.size; i++ )
	{
		t = RandomFloatRange( TOD_CLUSTER_FLIGHT_MIN, TOD_CLUSTER_FLIGHT_MAX );
		b = Spawn( "script_model", froms[ i ] );
		if ( !isdefined( b ) )
		{
			dev_log( "CLUSTER_BOMBLET_DROPPED reason=entity_pool_full" );
			continue;
		}
		if ( t > longest ) longest = t;
		b SetModel( TOD_CLUSTER_BOMBLET_MODEL );
		// yaw only (it was a random tumble): the fire linked to it must stand upright (2026-09-26)
		b.angles = ( 0, RandomInt( 360 ), 0 );
		b.tod_cl_spot = spots[ i ];
		b.tod_cl_fire = cluster_fire_on( b );   // linked BEFORE the throw, so it rides the arc exactly
		v = ( spots[ i ] - froms[ i ] ) / t + ( 0, 0, 0.5 * TOD_CLUSTER_GRAVITY * t );
		b MoveGravity( v, t );
		b thread cluster_bomblet_land( t, spots[ i ] );
		bomblets[ bomblets.size ] = b;
	}
	if ( bomblets.size == 0 ) return w;
	wait longest + TOD_CLUSTER_FIRST_DELAY;

	foreach ( b in bomblets )
	{
		while ( IS_TRUE( level.tod_upgrade_pause ) ) wait 0.1;   // a frozen world holds the chain
		if ( !isdefined( b ) ) continue;
		spot = b.tod_cl_spot;
		cluster_fire_off( b.tod_cl_fire );   // the fire burns right up to the pop
		b StopLoopSound( 0.05 );
		b Delete();
		w.hits += cluster_pop( spot, cluster_tier_radius( TOD_CLUSTER_RADIUS, tier ) * demo_radius_mult( owner ), owner, TOD_CLUSTER_ZOMBIES, TOD_CLUSTER_ELITE, weapon, false, tier );
		w.popped_spots[ w.popped_spots.size ] = spot;
		w.popped++;
		wait RandomFloatRange( TOD_CLUSTER_GAP_MIN, TOD_CLUSTER_GAP_MAX );
	}
	return w;
}

// THE FIRE on ent (the canister or a bomblet): two tag_origin hosts LINKED to it, so they ride
// its arc exactly (build 13 flew an unlinked twin arc and snapped it on at landing - user: "it
// doesn't look super smooth") -
//   the orange FLAME upright (angles 0; a billboard flipbook authored Z-up), and
//   the red GLOW pointed UP (pitch -90: the DOA trail it is cut from is authored along its
//   FORWARD axis, so pointing forward up makes its light and red flames rise with the flame).
// Each effect plays one frame after its host spawns (the client needs the entity first). End it
// with cluster_fire_off - never StopFXOnTag (the Retriever's crash, 2026-09-25). Returns a struct.
function cluster_fire_on( ent )
{
	if ( !TOD_CLUSTER_TRAIL || !isdefined( ent ) ) return undefined;
	fire = SpawnStruct();
	fire.flame = cluster_fire_host( ent, ( 0, 0, 0 ), TOD_CLUSTER_FX_TRAIL );
	fire.glow = cluster_fire_host( ent, ( -90, 0, 0 ), TOD_CLUSTER_FX_GLOW );
	return fire;
}

function cluster_fire_host( ent, angles, effect )
{
	h = Spawn( "script_model", ent.origin );
	if ( !isdefined( h ) )
	{
		dev_log( "FX_DROPPED fx=" + effect + " reason=entity_pool_full" );
		return undefined;
	}
	h SetModel( "tag_origin" );
	h.angles = angles;
	h LinkTo( ent );   // keeps this offset + these world angles relative to ent
	h thread cluster_fire_play( effect );
	h thread cluster_fire_reap( ent );
	return h;
}

function cluster_fire_play( effect )   // self = the host
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( effect, self, "tag_origin" );
}

// Backstop: ent gone by any other path takes its fire with it.
function cluster_fire_reap( ent )   // self = the host
{
	self endon( "death" );
	if ( isdefined( ent ) ) ent waittill( "death" );
	if ( isdefined( self ) ) self Delete();
}

function cluster_fire_off( fire )
{
	if ( !isdefined( fire ) ) return;
	if ( isdefined( fire.flame ) ) fire.flame Delete();
	if ( isdefined( fire.glow ) ) fire.glow Delete();
}

// self = a bomblet in flight. Settle it on its spot, then the fuse: spark + sizzle.
function cluster_bomblet_land( t, spot )
{
	self endon( "death" );
	// the fuse is lit from the burst: the spark rides the arc (2026-09-26 FX pass;
	// one frame after the Spawn so the client has the entity before its effect)
	wait 0.05;
	PlayFXOnTag( TOD_CLUSTER_FX_SIZZLE, self, "tag_weapon" );
	wait Max( t - 0.05, 0.05 );
	self.origin = spot;
	self PlayLoopSound( "tod_fuse_sizzle", 0.05 );
}

// One explosion: the burst (grenade fx + Apex impact) or a bomblet (the cluster
// fx + an Apex bomb pop); damage in round zombies with falloff.
function cluster_pop( org, radius, owner, zombie_mult, elite_mult, weapon, is_burst, tier )
{
	// pointed UP: both are authored along their forward axis (the bomblet pop spawns 30 u out on X),
	// so at angles 0 every pop went off to one side (2026-09-26, with the C4's fireball)
	// THE TIER (2026-09-26): a lower tier plays a shrunk copy and shakes less (cluster_tier_fx)
	fx = fx_at( cluster_tier_fx( is_burst, tier ), org, ( -90, 0, 0 ) );
	if ( isdefined( fx ) ) fx thread expire( 2.5 );
	sound_at( ( is_burst ? "tod_fuse_impact" : "tod_fuse_bomb" ), org, 4 );
	Earthquake( ( is_burst ? 0.25 : 0.15 ) * cluster_tier_scale( tier ), 0.3, org, radius + 150 );
	if ( IS_TRUE( level.tod_upgrade_pause ) ) return 0;
	// EXPLOSIVE FUSION (Breacher card, 2026-09-27): the burst / each bomblet heals the Breachers in it
	if ( isdefined( level.tod_cc_blast_heal_fn ) )
		[[ level.tod_cc_blast_heal_fn ]]( org, radius, ( is_burst ? "burst" : "pop" ) );
	base = curve() * owner_dmg_mult( owner, "cluster" );   // CLUSTER card (2026-09-26)
	hit = 0;
	foreach ( z in enemies_within( org, radius ) )
	{
		fall = 1.0 - 0.5 * ( Distance( z.origin, org ) / radius );
		hurt( z, base * ( is_elite( z ) ? elite_mult : zombie_mult ) * fall, owner, "MOD_GRENADE_SPLASH", weapon, org );
		hit++;
	}
	if ( hit > 0 ) dev_log( "CLUSTER_POP origin=" + org + " r=" + radius + " hit=" + hit + " zombie_hp=" + base + " burst=" + is_burst );
	return hit;
}

// ---------------------------------------------------------------------------
// WARRIOR BASH (tactical)
// ---------------------------------------------------------------------------
// A kit card's level, clamped 0..cap, read straight off the player's levels (the
// same table tod_upgrades::get_level reads). Shared by the Warrior and Breacher cards.
function card_lv( key, cap )
{
	if ( !isdefined( self.tod_levels ) || !isdefined( self.tod_levels[ key ] ) ) return 0;
	lv = Int( self.tod_levels[ key ] );
	if ( lv < 0 ) return 0;
	if ( lv > cap ) return cap;
	return lv;
}

function bash_rank()        { return self card_lv( "bash", TOD_BASH_MAX_LV ); }
function bash_capacity()    { return TOD_BASH_CHARGES + Int( Min( self bash_rank(), 6 ) / 3 ); }   // 2 at Lv3, 3 at Lv6 (BATTLE RHYTHM's +1 at Lv6 retired 2026-09-27)
function bash_burst_r()     { return ( ( self bash_rank() >= 9 ) ? TOD_BASH_BURST_R_LV9 : TOD_BASH_BURST_R ); }
function bash_damage_mult() { return TOD_BASH_DAMAGE_MULT + TOD_BASH_DAMAGE_STEP * self bash_rank(); }
function bash_recharge_ms() { return TOD_BASH_RECHARGE_MS - TOD_BASH_RECHARGE_STEP_MS * self bash_rank(); }
function gs_lv()            { return self card_lv( "gravsmash", TOD_GS_MAX_LV ); }
function gs_kills_need()    { return TOD_GS_KILLS - TOD_GS_KILLS_STEP * self gs_lv(); }
function gs_tier()          { return ( isdefined( self.tod_tier ) ? self.tod_tier : 1 ); }   // = tod_classes::tier (no import)
function gs_elite_zombies() { return TOD_GS_ELITE_ZOMBIES + TOD_GS_ELITE_STEP * self gs_lv(); }
function gs_stun_ms()       { return TOD_GS_ELITE_STUN_MS + TOD_GS_STUN_STEP_MS * Int( self gs_lv() / 3 ); }   // 1.5 / 2.5 / 3.5 / 4.5 s

// Sequential recharge; spending a charge never restarts a partial one. A card
// that raises the capacity grants only the new slot (Hellbound's rule).
function bash_sync()
{
	cap = self bash_capacity();
	if ( !isdefined( self.tod_bash_charges ) )
	{
		self.tod_bash_charges = cap;
		self.tod_bash_capacity = cap;
		self.tod_bash_next_ms = undefined;
	}
	if ( !isdefined( self.tod_bash_capacity ) ) self.tod_bash_capacity = cap;
	if ( cap > self.tod_bash_capacity )
	{
		self.tod_bash_charges += cap - self.tod_bash_capacity;
		dev_log( "BASH_CAPACITY player=" + self GetEntityNumber() + " rank=" + self bash_rank() + " capacity=" + self.tod_bash_capacity + "->" + cap + " charges=" + self.tod_bash_charges );
	}
	self.tod_bash_capacity = cap;
	if ( self.tod_bash_charges > cap ) self.tod_bash_charges = cap;
	now = GetTime();
	before = self.tod_bash_charges;
	while ( isdefined( self.tod_bash_next_ms ) && now >= self.tod_bash_next_ms && self.tod_bash_charges < cap )
	{
		self.tod_bash_charges++;
		self.tod_bash_next_ms += self bash_recharge_ms();
	}
	if ( self.tod_bash_charges >= cap ) self.tod_bash_next_ms = undefined;
	if ( self.tod_bash_charges > before )
	{
		dev_log( "BASH_READY player=" + self GetEntityNumber() + " charges=" + self.tod_bash_charges + "/" + cap + " rank=" + self bash_rank() );
		tod_ability_fx::kit_ready( self, "bash" );   // PK18: the blade rings when a charge comes back
	}
}

// This map's Warrior blades (2026-09-26): the One Inch Punch (cc_punch), the
// Gauntlet of Siegfried (cc_gauntlet) and Hellbound's Gold Battle Sword (cc_gold_sword).
function bash_is_blade( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) ) return false;
	return IsSubStr( weapon.name, "cc_punch" ) || IsSubStr( weapon.name, "cc_gauntlet" ) || IsSubStr( weapon.name, "cc_gold_sword" );
}

// One swing's damage (the blades' meleeDamage, _tod_classes.gsc / gen_tod_twins.js:
// punch 1600, gauntlet 3200, battle sword 5440; Pack-a-Punch doubles).
function bash_blade_damage( blade )
{
	d = 1600;
	if ( IsSubStr( blade.name, "cc_gauntlet" ) ) d = 3200;
	else if ( IsSubStr( blade.name, "cc_gold_sword" ) ) d = 5440;
	if ( IsSubStr( blade.name, "_up" ) ) d = d * 2;
	return d;
}

// Holding a blade uses that exact form; holding a sidearm uses the owned blade,
// preferring its Pack-a-Punched form.
function bash_blade( current )
{
	if ( bash_is_blade( current ) ) return current;
	result = undefined;
	foreach ( w in self GetWeaponsListPrimaries() )
	{
		if ( !bash_is_blade( w ) ) continue;
		if ( !isdefined( result ) || IsSubStr( w.name, "_up" ) ) result = w;
	}
	return result;
}

function bash_fire()
{
	if ( IS_TRUE( self.tod_bash_busy ) || IS_TRUE( self.tod_gs_busy ) ) return;
	if ( !( self can_act() ) ) return;
	previous = self GetCurrentWeapon();
	blade = self bash_blade( previous );
	if ( !isdefined( blade ) )
	{
		dev_log( "BASH_DENIED player=" + self GetEntityNumber() + " reason=no_blade" );
		tod_ability_fx::kit_deny( self, "bash", "no_blade" );
		return;
	}
	// The dash proxy draws the blade you hold (2026-09-26): the Cyber Sword on the
	// bat's lunge clip for the sword (build 16), our punch / gauntlet proxies (their
	// own swing clips as the raise) for the rest - all three in
	// source_data/tod_warrior_punch.gdt (tools/warrior/install_punch.py).
	if ( IsSubStr( blade.name, "cc_gold_sword" ) ) proxy_name = "tod_bash_sword_zm";
	else if ( IsSubStr( blade.name, "cc_gauntlet" ) ) proxy_name = "tod_bash_gauntlet_zm";
	else proxy_name = "tod_bash_punch_zm";
	proxy = real_weapon( proxy_name );
	if ( !isdefined( proxy ) )
	{
		dev_log( "BASH_DENIED player=" + self GetEntityNumber() + " reason=proxy_not_linked proxy=" + proxy_name );
		return;
	}
	if ( previous == level.weaponNone || self GetStance() == "prone" ) return;
	self bash_sync();
	now = GetTime();
	if ( self.tod_bash_charges <= 0 )
	{
		dev_log( "BASH_DENIED player=" + self GetEntityNumber() + " reason=recharging remaining_ms=" + ( self.tod_bash_next_ms - now ) );
		tod_ability_fx::kit_deny( self, "bash", "recharging" );
		return;
	}
	self.tod_bash_busy = true;
	self.tod_gs_queued = undefined;   // only a press DURING this Bash cuts it
	if ( !unlimited() )
	{
		self.tod_bash_charges--;
		if ( !isdefined( self.tod_bash_next_ms ) ) self.tod_bash_next_ms = now + self bash_recharge_ms();
	}
	self.tod_bash_token = now;
	self GiveWeapon( proxy );
	self ShouldDoInitialWeaponRaise( proxy, true );
	self DisableWeaponFire();
	self AllowMelee( false );
	self SwitchToWeaponImmediate( proxy );
	self PlaySound( "wpn_one_inch_punch_plr" );   // the cast's whoosh (2026-09-26; the dash had no sound until the hit)
	tod_ability_fx::bash_dash( self, blade );   // docs/203: the streak on the body (3p), the viewmodel light (1p), the dash whoosh in both ears
	level thread bash_run( self, previous, proxy, now, blade );
}

// Level-owned so cleanup survives a death; the token stops an old cast from
// restoring equipment over a newer life or cast.
function bash_run( owner, previous, proxy, token, blade )
{
	level endon( "end_game" );
	start = owner.origin;
	angles = owner GetPlayerAngles();
	ground_start = owner IsOnGround();
	// Latch the direction the player chose. Never steer toward a nearby zombie.
	// Air casts travel in the aimed direction; grounded casts follow the floor.
	// STRAIGHT BY CONSTRUCTION (2026-09-27, user: "the bash always goes straight ...
	// you can't turn left and right"): fwd is read ONCE here and every tick below
	// rewrites the whole velocity along it, so turning the view or strafing mid-dash
	// cannot bend the path. NEVER FreezeControls here: the 15:07 build did, and the
	// user's 18:25 log shows why that broke Bash - every cast travel=0 and
	// proxy_up_after_ms=-1. A frozen player ignores SetVelocity AND weapon switches,
	// so the dash never moved and the swing never came up (the 14:20 run, before the
	// lock: travel 300-360, proxy up in 50 ms). tools/warrior/test_bash.js models it.
	drive_angles = angles;
	if ( ground_start ) drive_angles = ( 0, angles[ 1 ], 0 );
	fwd = AnglesToForward( drive_angles );
	right = AnglesToRight( ( 0, angles[ 1 ], 0 ) );
	path_hits = 0;
	// BUILD-11 PLAYTEST (user: "the bash is kind of clunky on all of them"; the log:
	// BASH_START ~250 ms after every press): the dash no longer waits for the proxy
	// to finish switching in. It moves, hits and times its impact from the PRESS;
	// the proxy's clip plays over it as soon as the engine has it up (proxy_ms counts
	// from that moment, so the blade pass is still shown whole).
	started = GetTime();
	active = true;
	proxy_up_ms = undefined;
	impact = false;
	driving = true;
	if ( ground_start ) owner SetOrigin( owner.origin + ( 0, 0, 1 ) );
	is_sword = IsSubStr( blade.name, "cc_gold_sword" );
	proxy_ms = ( is_sword ? TOD_BASH_SWORD_MS : ( IsSubStr( blade.name, "cc_punch" ) ? TOD_BASH_PUNCH_MS : TOD_BASH_ANIM_MS ) );
	run_ms = ( proxy_ms > TOD_BASH_IMPACT_MS ? proxy_ms : TOD_BASH_IMPACT_MS + 50 );
	handed_back = false;
	cut = false;
	next_move_log = 100;
	dev_log( "BASH_START player=" + owner GetEntityNumber() + " token=" + token + " blade=" + blade.name + " ground=" + ground_start + " steer=latched angles=" + angles + " direction=" + fwd + " proxy_ms=" + proxy_ms + " dash_ms=" + TOD_BASH_DASH_MS + " press_to_start_ms=" + ( started - token ) );
	// the run lasts run_ms from the press, or until the proxy has shown proxy_ms of
	// its clip (it comes up late), never past 1 s
	while ( active && ( GetTime() - started < run_ms || ( !handed_back && isdefined( proxy_up_ms ) && GetTime() - proxy_up_ms < proxy_ms && GetTime() - started < 1000 ) ) )
	{
		if ( !isdefined( owner ) ) return;
		if ( !( owner can_act() ) || !isdefined( owner.tod_bash_token ) || owner.tod_bash_token != token ) break;
		if ( isdefined( owner.tod_gs_queued ) )
		{
			cut = true;   // Cyber Smash pressed mid-dash: the slam takes over
			dev_log( "BASH_CUT token=" + token + " reason=smash elapsed_ms=" + ( GetTime() - started ) + " travel=" + Distance2D( start, owner.origin ) );
			break;
		}
		cur = owner GetCurrentWeapon();
		if ( !isdefined( proxy_up_ms ) && cur == proxy ) proxy_up_ms = GetTime();
		// the Bash hands back to the RIGHT hand, never the gauntlet's left-hand twin
		// (_tod_warrior_melee alt_right_for swaps it in the holster once the proxy is up)
		if ( isdefined( proxy_up_ms ) && cur == proxy && isdefined( level.tod_wm_alt_right_fn ) ) previous = owner [[ level.tod_wm_alt_right_fn ]]( previous );
		if ( !handed_back && isdefined( proxy_up_ms ) && cur != proxy ) break;   // swapped away mid-cast
		elapsed = GetTime() - started;
		if ( !handed_back && isdefined( proxy_up_ms ) && GetTime() - proxy_up_ms >= proxy_ms && run_ms > proxy_ms )
		{
			// one blade pass, then the blade again while the dash carries on
			handed_back = true;
			if ( owner HasWeapon( previous ) )
			{
				owner ShouldDoInitialWeaponRaise( previous, false );
				owner SwitchToWeaponImmediate( previous );
			}
			dev_log( "BASH_HANDBACK token=" + token + " elapsed_ms=" + elapsed + " (single swing)" );
		}
		if ( driving && elapsed < TOD_BASH_DASH_MS )
		{
			clear = true;
			head = ( owner GetStance() == "crouch" ? 48 : 68 );
			foreach ( side in array( -16, 0, 16 ) )
			{
				foreach ( height in array( 28, head ) )
				{
					a = owner.origin + right * side + ( 0, 0, height );
					tr = BulletTrace( a, a + fwd * 30, false, owner );
					if ( tr[ "fraction" ] < 1 ) clear = false;
				}
			}
			if ( !clear )
			{
				driving = false;
				v = owner GetVelocity();
				owner SetVelocity( ( 0, 0, v[ 2 ] ) );
				dev_log( "BASH_STOP token=" + token + " reason=wall travel=" + Distance2D( start, owner.origin ) );
			}
			else
			{
				u = elapsed / ( TOD_BASH_DASH_MS * 1.0 );
				speed = TOD_BASH_DASH * ( 0.3 + 0.7 * 4 * u * ( 1 - u ) );
				v = owner GetVelocity();
				velocity = fwd * speed;
				if ( ground_start )
				{
					// A step is assistance, never a requirement for movement. Missing
					// ground (ledge/air) must not cancel a dash. Keep engine collision.
					vz = v[ 2 ];
					ahead = owner.origin + fwd * 24;
					step = BulletTrace( ahead + ( 0, 0, 24 ), ahead - ( 0, 0, 8 ), false, owner );
					if ( step[ "fraction" ] < 1 && step[ "normal" ][ 2 ] >= 0.7 )
					{
						rise = step[ "position" ][ 2 ] - owner.origin[ 2 ];
						if ( rise > 1 && rise <= 18 && vz < rise / 0.05 )
						{
							vz = rise / 0.05;
							dev_log( "BASH_STEP token=" + token + " rise=" + rise + " elapsed_ms=" + elapsed );
						}
					}
					velocity = velocity + ( 0, 0, vz );
				}
				owner SetVelocity( velocity );
			}
		}
		else
		{
			v = owner GetVelocity();
			owner SetVelocity( ( 0, 0, v[ 2 ] ) );   // no sideways drift during recovery
		}
		if ( !impact && elapsed < TOD_BASH_DASH_MS + 50 ) path_hits += owner bash_path( fwd, blade, token );
		if ( elapsed >= next_move_log && elapsed <= TOD_BASH_DASH_MS )
		{
			next_move_log += 100;
			dev_log( "BASH_MOVE token=" + token + " elapsed_ms=" + elapsed + " travel=" + Distance2D( start, owner.origin ) + " dz=" + ( owner.origin[ 2 ] - start[ 2 ] ) + " velocity=" + owner GetVelocity() + " view=" + owner GetPlayerAngles() );
		}
		if ( !impact && elapsed >= TOD_BASH_IMPACT_MS )
		{
			impact = true;
			owner bash_impact( fwd, blade, token, path_hits );
		}
		wait 0.05;
	}
	if ( !isdefined( owner ) ) return;
	if ( !isdefined( owner.tod_bash_token ) || owner.tod_bash_token != token ) return;
	if ( !impact && !cut && !unlimited() )
	{
		owner.tod_bash_charges++;   // interrupted before the hit: refund (a smash cut spends it)
		owner bash_sync();
	}
	if ( owner can_act() && owner GetCurrentWeapon() == proxy && owner HasWeapon( previous ) )
	{
		owner ShouldDoInitialWeaponRaise( previous, false );
		owner SwitchToWeaponImmediate( previous );
	}
	if ( owner HasWeapon( proxy ) ) owner TakeWeapon( proxy );
	owner EnableWeaponFire();
	owner AllowMelee( true );
	owner.tod_bash_busy = undefined;
	owner.tod_bash_token = undefined;
	if ( isdefined( owner.tod_gs_queued ) ) owner gs_after_bash( previous );
	dev_log( "BASH_END token=" + token + " impact=" + impact + " cut=" + cut + " travel=" + Distance2D( start, owner.origin ) + " proxy_up_after_ms=" + ( isdefined( proxy_up_ms ) ? proxy_up_ms - token : -1 ) + " total_ms=" + ( GetTime() - token ) );
}

// The nearest zombie ahead within reach and sight, or undefined (dash straight).
function bash_aim( fwd )
{
	best = undefined;
	best_d = TOD_BASH_AIM_RANGE;
	foreach ( z in enemies_within( self.origin, TOD_BASH_AIM_RANGE ) )
	{
		if ( Abs( z.origin[ 2 ] - self.origin[ 2 ] ) > 72 ) continue;
		to = z.origin - self.origin;
		d = Length( ( to[ 0 ], to[ 1 ], 0 ) );
		if ( d < 1 || d >= best_d ) continue;
		if ( VectorDot( VectorNormalize( ( to[ 0 ], to[ 1 ], 0 ) ), fwd ) < TOD_BASH_AIM_DOT ) continue;
		if ( !BulletTracePassed( self.origin + ( 0, 0, 40 ), z.origin + ( 0, 0, 40 ), false, self ) ) continue;
		best = z;
		best_d = d;
	}
	return best;
}

// One zombie, once per cast (tod_bash_hit = the cast's token).
function bash_hit( z, damage, blade, token )
{
	z.tod_bash_hit = token;
	stun_enemy( z, TOD_BASH_STUN_MS );
	// the blade's identity through the normal melee chain, once
	z DoDamage( damage, z.origin, self, self, "torso", "MOD_MELEE", 0, blade );
}

// Every tick of the dash: what the body is running through.
function bash_path( fwd, blade, token )
{
	damage = Int( bash_blade_damage( blade ) * self bash_damage_mult() );
	hit = 0;
	foreach ( z in enemies_within( self.origin + fwd * 32, TOD_BASH_PATH_R ) )
	{
		if ( isdefined( z.tod_bash_hit ) && z.tod_bash_hit == token ) continue;
		if ( Abs( z.origin[ 2 ] - self.origin[ 2 ] ) > 72 ) continue;
		self bash_hit( z, damage, blade, token );
		hit++;
	}
	if ( hit > 0 ) dev_log( "BASH_PATH token=" + token + " hit=" + hit );
	return hit;
}

function bash_impact( fwd, blade, token, path_hits )
{
	damage = Int( bash_blade_damage( blade ) * self bash_damage_mult() );
	self PlayRumbleOnEntity( "damage_heavy" );
	Earthquake( 0.3, 0.5, self.origin, 300 );
	// a physical shove, not an electric one (the lead 2026-09-26: the Raz shockwave
	// read as an EMP on the C4): the held blade's own impact burst
	impact_fx = ( IsSubStr( blade.name, "cc_gauntlet" ) ? "dlc3/stalingrad/fx_dragon_gauntlet_melee_impact" : "dlc5/tomb/fx_one_inch_punch_impact" );
	fx = fx_at( impact_fx, self.origin + fwd * 70 + ( 0, 0, 40 ), ( 0, 0, 0 ) );
	if ( isdefined( fx ) ) fx thread expire( 1.5 );
	// docs/203: the end burst sized to the burst radius (the Lv9 wider burst READS wider), a thump in
	// the caster's ear, the slam's camera arcs for the caster only - client-drawn, both views
	tod_ability_fx::bash_impact( self, self bash_rank() >= 9 );
	// THE HIT SOUND FOLLOWS THE BLADE (2026-09-27, user: "some of the punches sound like a
	// sword"): the fists' burst played the Cyber Sword's hit (hb_citadel_hit) on every Bash.
	hit_sound = ( IsSubStr( blade.name, "cc_gold_sword" ) ? "hb_citadel_hit" : "tod_punch_hit_npc" );
	sound_at( hit_sound, self.origin + fwd * 40, 3 );   // was PlaySoundAtPosition: the silent lane for a custom alias (2026-09-26)
	hit = 0;
	skipped = 0;
	foreach ( z in enemies_within( self.origin, self bash_burst_r() ) )   // all around (was a 175 u cone ahead)
	{
		if ( hit + path_hits >= TOD_BASH_MAX_TARGETS ) break;
		if ( isdefined( z.tod_bash_hit ) && z.tod_bash_hit == token ) { skipped++; continue; }
		if ( Abs( z.origin[ 2 ] - self.origin[ 2 ] ) > 72 ) continue;
		trace = BulletTrace( self.origin + ( 0, 0, 40 ), z.origin + ( 0, 0, 40 ), false, self );
		if ( trace[ "fraction" ] < 1 ) continue;
		self bash_hit( z, damage, blade, token );
		hit++;
	}
	dev_log( "BASH player=" + self GetEntityNumber() + " blade=" + blade.name + " rank=" + self bash_rank() + " mult=" + self bash_damage_mult() + " damage=" + damage + " burst_hit=" + hit + " burst_r=" + self bash_burst_r() + " path_hits=" + path_hits + " already_hit=" + skipped + " fx=" + impact_fx + " charges=" + self.tod_bash_charges + "/" + self bash_capacity() + " recharge_ms=" + self bash_recharge_ms() );
}

// ---------------------------------------------------------------------------
// WARRIOR GRAVITY SMASH (lethal) - the stock Gravity Spikes slam
// ---------------------------------------------------------------------------
// Kills still needed (0 = ready). The HUD's lethal tile shows it.
function gs_kills_left()
{
	kills = ( isdefined( self.tod_gs_kills ) ? self.tod_gs_kills : 0 );
	left = self gs_kills_need() - kills;
	return ( left > 0 ? left : 0 );
}

// level.tod_gs_charge_fn: a kill the player made (_tod_warrior_melee on_zombie_death,
// every kill whatever the weapon). self = the killer, victim = the dead zombie.
function gs_charge( victim )
{
	if ( !isdefined( self ) || !IsPlayer( self ) || kit_of( self ) != TOD_KIT_WARRIOR ) return;
	if ( self gs_tier() < TOD_GS_TIER_MIN ) return;
	if ( IS_TRUE( self.tod_gs_busy ) ) return;   // mid-smash: its own kills
	if ( isdefined( self.tod_gs_slam_ms ) && GetTime() - self.tod_gs_slam_ms < TOD_GS_OWN_KILL_MS ) return;
	if ( !isdefined( self.tod_gs_kills ) ) self.tod_gs_kills = 0;
	need = self gs_kills_need();
	if ( self.tod_gs_kills >= need ) return;   // full: nothing banks past ready
	self.tod_gs_kills++;
	dev_log( "GS_CHARGE +1 player=" + self GetEntityNumber() + " total=" + self.tod_gs_kills + " need=" + need );
	if ( self.tod_gs_kills >= need )
		dev_log( "GS_READY player=" + self GetEntityNumber() + " kills=" + self.tod_gs_kills + " lv=" + self gs_lv() );
}

// Ready to cast (the kit loop asks before it cuts a Bash for it).
function gs_ready()
{
	if ( IS_TRUE( self.tod_gs_busy ) ) return false;
	if ( self gs_tier() < TOD_GS_TIER_MIN ) return false;
	return ( unlimited() || self gs_kills_left() <= 0 );
}

// bash_run's hand-over: the Bash has put its proxy away, the smash starts now and
// returns to the blade the Bash came from.
function gs_after_bash( previous )
{
	queued = self.tod_gs_queued;
	self.tod_gs_queued = undefined;
	if ( GetTime() - queued > TOD_GS_QUEUE_MS )
	{
		dev_log( "GS_QUEUE_DROP player=" + self GetEntityNumber() + " reason=stale age_ms=" + ( GetTime() - queued ) );
		return;
	}
	self thread gravsmash_fire( previous );
}

function gravsmash_fire( return_to )
{
	self.tod_gs_queued = undefined;
	if ( IS_TRUE( self.tod_gs_busy ) ) return;
	now = GetTime();
	if ( self gs_tier() < TOD_GS_TIER_MIN )
	{
		dev_log( "GS_DENIED player=" + self GetEntityNumber() + " reason=tier tier=" + self gs_tier() + " need_tier=" + TOD_GS_TIER_MIN );
		return;
	}
	left = self gs_kills_left();
	if ( !unlimited() && left > 0 )
	{
		dev_log( "GS_DENIED player=" + self GetEntityNumber() + " reason=charging kills_left=" + left + " need=" + self gs_kills_need() );
		return;
	}
	if ( !( self can_act() ) )
	{
		dev_log( "GS_DENIED player=" + self GetEntityNumber() + " reason=cannot_act" );
		return;
	}
	self.tod_gs_busy = true;
	self tod_cyber_sword::update( false, "gravity_smash_cast" );
	if ( !unlimited() ) self.tod_gs_kills = 0;   // spent: charge it again with kills
	held = self GetCurrentWeapon();
	if ( isdefined( return_to ) ) held = return_to;   // after a Bash cut: its proxy is gone
	held_name = ( isdefined( held ) && isdefined( held.name ) ? held.name : "none" );
	proxy = real_weapon( TOD_GS_SWORD_PROXY );
	if ( isdefined( proxy ) && self GetStance() != "prone" )
	{
		dev_log( "GS_FIRE player=" + self GetEntityNumber() + " path=sword held=" + held_name + " proxy=" + proxy.name + " unlimited=" + unlimited() + " kills_left_was=" + left );
		level thread gravsmash_sword( self, held, proxy, now );
		return;
	}
	reason = ( isdefined( proxy ) ? "prone" : "sword_proxy_not_linked" );
	dev_log( "GS_FIRE player=" + self GetEntityNumber() + " path=spikes reason=" + reason + " held=" + held_name + " unlimited=" + unlimited() );
	self thread gravsmash_slam();
}

function slam_target_ok( ai )   // level.gravityspikes_target_filter_callback
{
	return !is_elite( ai );   // the stock lift ragdolls what it is handed: never an elite
}

// The instant slam (the fallback: prone, or the sword proxy not linked): the hit, then the button is free again.
function gravsmash_slam()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	d = self gs_dive_start( GetTime() );
	if ( isdefined( d ) ) tod_ability_fx::dive_start( self, d.floor );   // docs/206: the streak, the landing mark, the whistle
	while ( isdefined( d ) && !d.done )
	{
		if ( !( self can_act() ) ) { self gs_dive_end( d, "cancel" ); break; }
		self gs_dive_update( d );
		if ( d.done ) break;
		wait 0.05;
	}
	if ( isdefined( d ) ) tod_ability_fx::dive_end( self );
	if ( isdefined( d ) && d.reason == "cancel" ) { self.tod_gs_busy = undefined; return; }
	self gravsmash_hit( ( isdefined( d ) ? "spikes_dive" : "spikes" ) );
	wait 0.5;
	self.tod_gs_busy = undefined;
	dev_log( "GS_END player=" + self GetEntityNumber() + " path=spikes" );
}

// Level-owned (cleanup survives a death). Hellbound's _tod_gold_sword::smash, trimmed:
// switch to the cast proxy (its raise is the slam clip), leap on Hellbound's arc,
// land the Gravity Smash on the clip's impact frame, switch back. A switch the
// engine refuses still slams (never a dead button).
function gravsmash_sword( owner, original, proxy, token )
{
	level endon( "end_game" );
	owner.tod_gs_token = token;
	owner DisableWeaponFire();
	owner AllowMelee( false );
	owner GiveWeapon( proxy );
	owner ShouldDoInitialWeaponRaise( proxy, true );
	owner SwitchToWeaponImmediate( proxy );
	landed = false;
	for ( i = 0; i < 40; i++ )
	{
		if ( !isdefined( owner ) || !( owner can_act() ) ) break;
		cur = owner GetCurrentWeapon();
		if ( cur == proxy ) { landed = true; break; }
		owner SwitchToWeaponImmediate( proxy );
		wait 0.05;
	}
	if ( !isdefined( owner ) ) return;
	started = GetTime();
	fired = false;
	arc = undefined;
	arc_checked = false;
	dev_log( "GS_SWORD_CAST token=" + token + " switched=" + landed + " wait_ms=" + ( started - token ) );
	dive = undefined;
	if ( landed ) dive = owner gs_dive_start( token );   // off the ground: the air slam
	if ( isdefined( dive ) ) tod_ability_fx::dive_start( owner, dive.floor );   // docs/206
	if ( isdefined( dive ) ) arc_checked = true;         // no leap from the air
	while ( landed && ( GetTime() - started < TOD_GS_SWORD_ANIM_MS || ( isdefined( dive ) && !dive.done ) ) )
	{
		if ( !isdefined( owner ) ) return;
		if ( !( owner can_act() ) || owner GetCurrentWeapon() != proxy || !isdefined( owner.tod_gs_token ) || owner.tod_gs_token != token )
		{
			if ( isdefined( dive ) && !dive.done ) owner gs_dive_end( dive, "cancel" );
			dev_log( "GS_SWORD_CANCEL token=" + token + " elapsed_ms=" + ( GetTime() - started ) + " fired=" + fired );
			break;
		}
		elapsed = GetTime() - started;
		if ( !arc_checked && elapsed >= TOD_GS_SWORD_IMPACT_MS - TOD_GS_ARC_MS )
		{
			arc_checked = true;
			arc = owner gs_arc_start( token, TOD_GS_SWORD_IMPACT_MS - elapsed );
		}
		if ( isdefined( arc ) ) owner gs_arc_update( arc, token );
		if ( isdefined( dive ) )
		{
			owner gs_dive_update( dive );
			if ( !fired && dive.done )
			{
				fired = true;   // the slam lands where the feet touch
				tod_ability_fx::dive_end( owner );
				owner gravsmash_hit( "dive" );
				owner gs_sword_fx();
			}
		}
		else if ( !fired && elapsed >= TOD_GS_SWORD_IMPACT_MS && ( !isdefined( arc ) || !arc.driving || elapsed >= TOD_GS_SWORD_IMPACT_MS + 300 ) )
		{
			fired = true;
			owner gravsmash_hit( "sword" );
			owner gs_sword_fx();
		}
		wait 0.05;
	}
	if ( !isdefined( owner ) ) return;
	if ( isdefined( dive ) && !dive.done ) owner gs_dive_end( dive, "cancel" );
	if ( isdefined( dive ) ) tod_ability_fx::dive_end( owner );
	if ( !fired && owner can_act() )
	{
		dev_log( "GS_SWORD_FALLBACK token=" + token + " reason=" + ( landed ? "cast_cut_short" : "switch_refused" ) );
		owner gravsmash_hit( "sword_fallback" );
		fired = true;
	}
	if ( owner GetCurrentWeapon() == proxy && owner HasWeapon( original ) )
	{
		owner ShouldDoInitialWeaponRaise( original, false );
		owner SwitchToWeaponImmediate( original );
	}
	if ( owner HasWeapon( proxy ) ) owner TakeWeapon( proxy );
	if ( isdefined( owner.tod_gs_token ) && owner.tod_gs_token == token )
	{
		owner EnableWeaponFire();
		owner AllowMelee( true );
		owner.tod_gs_token = undefined;
	}
	owner.tod_gs_busy = undefined;
	dev_log( "GS_END player=" + owner GetEntityNumber() + " path=sword token=" + token + " fired=" + fired + " elapsed_ms=" + ( GetTime() - started ) + " proxy_left=" + owner HasWeapon( proxy ) );
}

// Hellbound's smash impact dressing (hb/gold_sword FX, zoned; the smash alias ships
// in tod_expected_roster.csv).
function gs_sword_fx()
{
	fx = fx_at( "hb/gold_sword/fx_smash", self.origin, ( -90, 0, 0 ) );
	if ( isdefined( fx ) ) fx thread expire( 3.0 );
	glow = fx_at( "hb/gold_sword/fx_smash_afterglow", self.origin + ( 0, 0, 6 ), ( 0, 0, 0 ) );
	if ( isdefined( glow ) ) glow thread expire( 4.5 );
	sound_at( "hb_gold_sword_smash", self.origin, 4 );
	Earthquake( 0.6, 0.7, self.origin, 600 );
}

// Hellbound's leap: forward if the landing is solid and the air is clear, shorter,
// then in place; skipped off the ground. Returns the motion or undefined.
function gs_arc_start( token, flight_ms )
{
	if ( flight_ms < 250 ) { dev_log( "GS_ARC_SKIP token=" + token + " reason=late_launch" ); return undefined; }
	if ( !( self IsOnGround() ) ) { dev_log( "GS_ARC_SKIP token=" + token + " reason=airborne" ); return undefined; }
	a = self GetPlayerAngles();
	fwd = AnglesToForward( ( 0, a[ 1 ], 0 ) );
	start = self.origin;
	head = ( self GetStance() == "crouch" ? 52 : 72 );
	foreach ( dist in array( TOD_GS_ARC_DIST, TOD_GS_ARC_DIST * 0.5, 0 ) )
	{
		dest = start + fwd * dist;
		floor = BulletTrace( dest + ( 0, 0, 72 ), dest - ( 0, 0, 72 ), false, self );
		if ( floor[ "fraction" ] == 1 || floor[ "normal" ][ 2 ] < 0.7 ) continue;
		if ( Abs( floor[ "position" ][ 2 ] - start[ 2 ] ) > 64 ) continue;
		dest = floor[ "position" ] + ( 0, 0, 1 );
		clear = true;
		foreach ( h in array( 8, head * 0.5, head + TOD_GS_ARC_HEIGHT ) )
		{
			if ( dist > 0 && !BulletTracePassed( start + ( 0, 0, h ), dest + ( 0, 0, h ), false, self ) ) clear = false;
		}
		if ( !BulletTracePassed( start + ( 0, 0, head ), start + ( 0, 0, head + TOD_GS_ARC_HEIGHT ), false, self ) ) clear = false;
		if ( !clear ) continue;
		m = SpawnStruct();
		m.start = start + ( 0, 0, 1 );
		m.delta = dest - m.start;
		m.started = GetTime();
		m.duration_ms = flight_ms;
		m.airborne = false;
		m.driving = true;
		m.max_rise = 0;
		v = self gs_arc_velocity( m, 0 );
		self SetOrigin( self.origin + ( 0, 0, 1 ) );   // stock _zm_jump_pad ground release
		self SetVelocity( v );
		dev_log( "GS_ARC_LAUNCH token=" + token + " grounded=1 vel=" + v + " dist=" + dist + " flight_ms=" + flight_ms );
		return m;
	}
	dev_log( "GS_ARC_SKIP token=" + token + " reason=no_clear_arc_or_landing" );
	return undefined;
}

function gs_arc_position( m, u )
{
	return m.start + m.delta * u + ( 0, 0, 4 * TOD_GS_ARC_HEIGHT * u * ( 1 - u ) );
}

// The velocity that reaches the next frame's point on the arc, against gravity.
function gs_arc_velocity( m, elapsed )
{
	next_u = ( elapsed + 50 ) / ( m.duration_ms * 1.0 );
	if ( next_u > 1 ) next_u = 1;
	v = ( gs_arc_position( m, next_u ) - self.origin ) * 20;
	return v + ( 0, 0, self GetPlayerGravity() * 0.025 );
}

function gs_arc_update( m, token )
{
	if ( !m.driving ) return;
	elapsed = GetTime() - m.started;
	rise = self.origin[ 2 ] - m.start[ 2 ];
	if ( rise > m.max_rise ) m.max_rise = rise;
	if ( !( self IsOnGround() ) && rise > 4 ) m.airborne = true;
	if ( m.airborne && self IsOnGround() )
	{
		m.driving = false;
		dev_log( "GS_ARC_LAND token=" + token + " elapsed_ms=" + elapsed + " max_rise=" + m.max_rise + " travel=" + Distance2D( self.origin, m.start ) );
		return;
	}
	if ( elapsed >= m.duration_ms )
	{
		m.driving = false;
		dev_log( "GS_ARC_LAND token=" + token + " elapsed_ms=" + elapsed + " reason=timeout max_rise=" + m.max_rise + " travel=" + Distance2D( self.origin, m.start ) );
		return;
	}
	if ( Distance( gs_arc_position( m, elapsed / ( m.duration_ms * 1.0 ) ), self.origin ) > TOD_GS_ARC_MAX_ERROR )
	{
		m.driving = false;
		dev_log( "GS_ARC_RELEASE token=" + token + " reason=blocked_or_displaced" );
		return;
	}
	v = self gs_arc_velocity( m, elapsed );
	if ( Length( v ) > 900 )
	{
		m.driving = false;
		dev_log( "GS_ARC_RELEASE token=" + token + " reason=velocity_bound" );
		return;
	}
	self SetVelocity( v );
}

// ---------------------------------------------------------------------------
// THE AIR SLAM (TOD_GS_DIVE_*). gs_dive_start traces the floor, gs_dive_update runs
// once per 50 ms tick (the hang, then the pull), gs_dive_end closes it. d.done and
// d.reason ("landed" / "blocked" / "timeout" / "cancel") tell the caller when to slam.
// tools/warrior/test_gs_dive.js runs these three against a falling-body mock.
// ---------------------------------------------------------------------------
// How long the pull takes to cover h units (the same per-tick steps as gs_dive_update).
function gs_dive_fall_ms( h )
{
	t = 0;
	y = 0;
	v = TOD_GS_DIVE_V0;
	while ( y < h && t < TOD_GS_DIVE_MAX_MS )
	{
		y = y + v * 0.05;
		v = Min( v + TOD_GS_DIVE_ACCEL * 0.05, TOD_GS_DIVE_VMAX );
		t = t + 50;
	}
	return t;
}

// The beat in the air: long enough that a short drop lands on the sword's swing frame.
function gs_dive_hang_ms( fall_ms )
{
	hang = TOD_GS_SWORD_IMPACT_MS - fall_ms;
	if ( hang < TOD_GS_DIVE_HANG_MIN_MS ) hang = TOD_GS_DIVE_HANG_MIN_MS;
	if ( hang > TOD_GS_DIVE_HANG_MAX_MS ) hang = TOD_GS_DIVE_HANG_MAX_MS;
	return hang;
}

function gs_dive_start( token )
{
	if ( self IsOnGround() ) return undefined;
	from = self.origin + ( 0, 0, 4 );
	to = self.origin - ( 0, 0, TOD_GS_DIVE_TRACE );
	tr = BulletTrace( from, to, false, self );
	if ( tr[ "fraction" ] >= 1 )
	{
		dev_log( "GS_DIVE_SKIP token=" + token + " reason=no_floor z=" + self.origin[ 2 ] );
		return undefined;
	}
	h = self.origin[ 2 ] - tr[ "position" ][ 2 ];
	if ( h < TOD_GS_DIVE_MIN_H )
	{
		dev_log( "GS_DIVE_SKIP token=" + token + " reason=low height=" + h );
		return undefined;
	}
	d = SpawnStruct();
	d.token = token;
	d.start_z = self.origin[ 2 ];
	d.height = h;
	d.floor = tr[ "position" ];   // docs/206: the landing mark goes here (tod_ability_fx::dive_start, called by the lanes)
	d.fall_ms = gs_dive_fall_ms( h );
	d.hang_ms = gs_dive_hang_ms( d.fall_ms );
	d.started = GetTime();
	d.pulling = false;
	d.pull_ms = 0;
	d.speed = 0;
	d.last_z = self.origin[ 2 ];
	d.stuck = 0;
	d.done = false;
	d.reason = "";
	self.tod_gs_diving = true;
	hold = self GetPlayerGravity() * 0.025;
	self SetVelocity( ( 0, 0, hold ) );   // the hang: stop the fall (and the Bash's carry) for a beat
	dev_log( "GS_DIVE_START token=" + token + " height=" + h + " floor_z=" + tr[ "position" ][ 2 ] + " hang_ms=" + d.hang_ms + " fall_ms_est=" + d.fall_ms + " land_ms_est=" + ( d.hang_ms + d.fall_ms ) + " surface=" + tr[ "surfacetype" ] );
	return d;
}

function gs_dive_update( d )
{
	if ( d.done ) return;
	now = GetTime();
	elapsed = now - d.started;
	if ( !d.pulling )
	{
		if ( elapsed < d.hang_ms )
		{
			hold = self GetPlayerGravity() * 0.025;
			self SetVelocity( ( 0, 0, hold ) );
			return;
		}
		d.pulling = true;
		d.pull_ms = now;
		d.speed = TOD_GS_DIVE_V0;
		d.last_z = self.origin[ 2 ];
		dev_log( "GS_DIVE_PULL token=" + d.token + " elapsed_ms=" + elapsed + " z=" + self.origin[ 2 ] );
	}
	if ( self IsOnGround() )
	{
		self gs_dive_end( d, "landed" );
		return;
	}
	if ( elapsed >= TOD_GS_DIVE_MAX_MS )
	{
		self gs_dive_end( d, "timeout" );
		return;
	}
	// held up by something that is not ground (a zombie's head, a rail cap): slam there
	if ( now - d.pull_ms >= 150 && d.last_z - self.origin[ 2 ] < 1 ) d.stuck++;
	else d.stuck = 0;
	if ( d.stuck >= 3 )
	{
		self gs_dive_end( d, "blocked" );
		return;
	}
	d.last_z = self.origin[ 2 ];
	down = d.speed * -1;
	self SetVelocity( ( 0, 0, down ) );
	d.speed = Min( d.speed + TOD_GS_DIVE_ACCEL * 0.05, TOD_GS_DIVE_VMAX );
}

function gs_dive_end( d, reason )
{
	d.done = true;
	d.reason = reason;
	self.tod_gs_diving = undefined;
	self.tod_gs_dive_land_ms = GetTime();
	pull = -1;
	if ( d.pulling ) pull = GetTime() - d.pull_ms;
	dev_log( "GS_DIVE_END token=" + d.token + " reason=" + reason + " fell=" + ( d.start_z - self.origin[ 2 ] ) + " height_est=" + d.height + " pull_ms=" + pull + " fall_ms_est=" + d.fall_ms + " total_ms=" + ( GetTime() - d.started ) + " speed=" + d.speed );
}

// level.player_damage_callbacks: no fall damage from an air slam.
function gs_fall_guard( eInflictor, eAttacker, iDamage, iDFlags, sMeansOfDeath, weapon, vPoint, vDir, sHitLoc, psOffsetTime )
{
	if ( sMeansOfDeath !== "MOD_FALLING" ) return -1;
	diving = IS_TRUE( self.tod_gs_diving );
	recent = ( isdefined( self.tod_gs_dive_land_ms ) && GetTime() - self.tod_gs_dive_land_ms <= TOD_GS_DIVE_FALL_GRACE_MS );
	if ( !diving && !recent ) return -1;
	dev_log( "GS_DIVE_FALL_BLOCK player=" + self GetEntityNumber() + " damage=" + iDamage + " diving=" + diving );
	return 0;
}

// THE GRAVITY SMASH HIT, shared by the instant slam and the sword slam.
function gravsmash_hit( path )
{
	level.gravityspikes_target_filter_callback = &slam_target_ok;
	self.tod_gs_slam_ms = GetTime();   // gs_charge: the slam's own kills never recharge it
	self PlayRumbleOnEntity( "damage_heavy" );
	Earthquake( 0.5, 0.8, self.origin, 500 );
	// SOUND (2026-09-26): the stock Gravity Spikes wavs (sound/aliases/tod_warrior.csv,
	// tools/warrior/make_punch_aliases.py). zmb_talon_electrocute_swt was a Talon
	// alias no CSV here ships = silent. The caster hears the swing + the hit 2D;
	// everyone hears the shockwave from the slam point (script_origin lane).
	v_pos = self.origin + AnglesToForward( self GetPlayerAngles() ) * 24;
	self PlaySound( "tod_gs_start_plr" );
	sound_at( "tod_gs_shockwave", v_pos, 4 );
	// the slam itself: stock's lift + knockdown + its slam FX (gravity_slam_fx /
	// gravity_slam_player_fx clientfields; the .csc half rides zm_tod2_cybercity.csc)
	self zm_weap_gravityspikes::knockdown_zombies_slam();
	self PlaySound( "tod_gs_hit_plr" );
	self PlaySound( "tod_gs_hit_lfe_plr" );
	base = curve();
	elite_hits = 0;
	elite_mult = self gs_elite_zombies();
	foreach ( z in enemies_within( v_pos, 200 ) )
	{
		if ( !is_elite( z ) ) continue;
		stun_enemy( z, self gs_stun_ms() );   // 1.5 s, +1 s at Lv3 / Lv6 / Lv9 (2026-09-27)
		hurt( z, base * elite_mult, self, "MOD_IMPACT", undefined, v_pos );
		elite_hits++;
	}
	dev_log( "GS_SLAM player=" + self GetEntityNumber() + " path=" + path + " lvl=" + self gs_lv() + " elite_hits=" + elite_hits + " elite_mult=" + elite_mult + " stun_ms=" + self gs_stun_ms() + " zombie_hp=" + base + " kills_to_recharge=" + self gs_kills_need() );
}

// ---------------------------------------------------------------------------
// HUD: the Archer's tiles, with the kit named in the 4th argument.
//   warrior:  lethal = SMASH: -2 locked (below tier 3), -1 active, 0 ready, N kills to charge
//             (LOCKSTEP AetheriumLoadout CLASS_KITS[1] kills); tactical = BASH recharge s (0 = ready)
//   breacher: lethal = C4 charges,       tactical = CLUSTER charges
// ---------------------------------------------------------------------------
function hud_send( kit )
{
	if ( kit == TOD_KIT_NECRO )
	{
		// lethal = the SOUL BOMB's souls still to charge (0 ready - it charges on
		// kills since 2026-09-26, not a timer); the tactical tile is the INVISIBILITY
		// CLOAK since 2026-09-27: -2 no card, -1 cloaked, 0 ready, N seconds
		// (LOCKSTEP _tod_class_cards::cloak_hud + AetheriumLoadout CLASS_KITS[3])
		lethal = self tod_necro_summon::soul_bomb_left();
		tac = -2;
		if ( isdefined( level.tod_cc_cloak_hud_fn ) ) tac = self [[ level.tod_cc_cloak_hud_fn ]]( unlimited() );
	}
	else if ( kit == TOD_KIT_WARRIOR )
	{
		now = GetTime();
		lethal = ( unlimited() ? 0 : self gs_kills_left() );
		if ( IS_TRUE( self.tod_gs_busy ) ) lethal = -1;
		if ( self gs_tier() < TOD_GS_TIER_MIN ) lethal = -2;
		tac = 0;
		if ( isdefined( self.tod_bash_charges ) && self.tod_bash_charges <= 0 && isdefined( self.tod_bash_next_ms ) ) tac = Int( ( self.tod_bash_next_ms - now ) / 1000 + 0.999 );
		if ( IS_TRUE( self.tod_bash_busy ) ) tac = -1;
	}
	else
	{
		// -1 = not earned yet (card level 0): the tile reads LOCKED (2026-09-26)
		lethal = ( self c4_max() > 0 ? self.tod_c4_charges : -1 );
		tac = ( self cluster_max() > 0 ? self.tod_cluster_charges : -1 );
	}
	// Share the actual tier/busy/kill-charge/dev decision, before HUD throttling.
	self tod_cyber_sword::update( kit == TOD_KIT_WARRIOR && lethal == 0, "hud_readiness" );
	tod_ability_fx::sword_ready( self, kit == TOD_KIT_WARRIOR && lethal == 0 );   // docs/206: the charged blade a teammate sees (change-gated inside)
	key = kit + ":" + lethal + ":" + tac;
	if ( isdefined( self.tod_kit_hud ) && self.tod_kit_hud == key && GetTime() < self.tod_kit_hud_refresh ) return;
	self.tod_kit_hud = key;
	self.tod_kit_hud_refresh = GetTime() + 2000;   // re-send so a rebuilt HUD recovers
	self LuiNotifyEvent( &"tod_archer_abil", 4, 1, lethal, tac, kit );
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------
function curve()   // one round zombie's health: this map's damage unit
{
	if ( isdefined( level.zombie_health ) && level.zombie_health > 0 ) return level.zombie_health;
	return 14;   // round 1 at the power scale (map 1: 135 / 10)
}

function fx_at( effect, org, facing )   // bare server PlayFX does not render: ride a carrier
{
	host = Spawn( "script_model", org );
	if ( !isdefined( host ) )   // entity pool full: drop the effect, never throw
	{
		dev_log( "FX_DROPPED effect=" + effect + " origin=" + org + " reason=entity_pool_full" );
		return undefined;
	}
	host SetModel( "tag_origin" );
	if ( isdefined( facing ) ) host.angles = facing;
	// ONE FRAME LATER (2026-09-26, user: the C4's fireball shows "maybe 75% of the time"): played in
	// the frame the host spawns, the effect can reach the client before the entity does and is lost.
	// Every other effect host in this map already waits a frame; this helper was the exception.
	host thread fx_at_play( effect );
	return host;
}

function fx_at_play( effect )   // self = the fx_at host
{
	self endon( "death" );
	wait 0.05;
	PlayFXOnTag( effect, self, "tag_origin" );
	if ( isdefined( self.tod_c4_fx_id ) )
		dev_log( "C4_FX_PLAY id=" + self.tod_c4_fx_id + " host=" + self GetEntityNumber() + " effect=" + effect + " origin=" + self.origin + " replicated_wait_ms=50" );
}

// A custom 3D alias plays from a spawned script_origin's PlaySound, never
// PlaySoundAtPosition: that lane played nothing audible for a custom alias in
// this map (CLAUDE.md v19.21c; _tod_perk_scatter::play_sound_at_origin).
function sound_at( alias, org, life )
{
	e = Spawn( "script_origin", org );
	if ( !isdefined( e ) )   // entity pool full: drop the sound, never throw
	{
		dev_log( "SOUND_DROPPED alias=" + alias + " origin=" + org + " reason=entity_pool_full" );
		return;
	}
	e PlaySound( alias );
	e thread expire( life );
}

function expire( seconds )
{
	level endon( "end_game" );
	wait seconds;
	if ( isdefined( self ) )
	{
		if ( isdefined( self.tod_c4_fx_id ) ) dev_log( "C4_FX_END id=" + self.tod_c4_fx_id + " host=" + self GetEntityNumber() + " life_s=" + seconds );
		self Delete();
	}
}

// Elites and bosses (zm_zod_robot::landing_splash_immune's list). (The armored
// sprinter's own flag, read here because it carried no boss flag, retired with
// it 2026-10-05.)
function is_elite( e )
{
	if ( !isdefined( e ) ) return false;
	return ( IS_TRUE( e.is_boss ) || IS_TRUE( e.acc_is_boss ) || IS_TRUE( e.acc_is_mini_boss )
	      || isdefined( e.tod_boss_kind ) );
}

// Real bosses take damage but are never stunned.
function is_true_boss( e )
{
	if ( !isdefined( e ) ) return false;
	if ( IS_TRUE( e.tod_doppelghast ) || IS_TRUE( e.tod_mangler ) ) return true;
	return isdefined( e.tod_boss_kind ) && ( e.tod_boss_kind == "doppelghast" || e.tod_boss_kind == "mangler" );   // (the Panzer's row retired with him, 2026-10-05)
}

function alive_enemies()
{
	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	out = [];
	foreach ( z in GetAITeamArray( team ) )
		if ( isdefined( z ) && IsAlive( z ) ) out[ out.size ] = z;
	return out;
}

function enemies_within( org, radius )
{
	out = [];
	r2 = radius * radius;
	foreach ( z in alive_enemies() )
		if ( DistanceSquared( z.origin, org ) <= r2 ) out[ out.size ] = z;
	return out;
}

// Authored damage through the cleave PASS-THROUGH: cards do not re-multiply it.
function hurt( victim, dmg, attacker, mod, weapon, org )
{
	if ( !isdefined( victim ) || !IsAlive( victim ) || dmg <= 0 ) return;
	if ( !isdefined( org ) ) org = victim.origin;
	victim.tod_cleave_hit = true;
	if ( isdefined( weapon ) )
		victim DoDamage( int( dmg + 0.5 ), org, attacker, attacker, "none", mod, 0, weapon );
	else
		victim DoDamage( int( dmg + 0.5 ), org, attacker, attacker, "none", mod, 0 );
	if ( isdefined( victim ) && IS_TRUE( victim.tod_cleave_hit ) ) victim.tod_cleave_hit = undefined;
	if ( mod === "MOD_GRENADE_SPLASH" && isdefined( weapon ) && isdefined( attacker ) && isplayer( attacker ) && ( !isdefined( victim ) || !IsAlive( victim ) ) )
		attacker demo_refund( weapon );
}

// DEMOLITIONIST was retired 2026-09-27 (class pass 2): both hooks are kept inert
// (identical to the card at level 0) so the C4 / Cluster call sites need no edit.
function demo_radius_mult( owner )
{
	return 1.0;
}

function demo_refund( weapon )
{
	return;   // retired 2026-09-27 (was DEMOLITIONIST's charge refund on an explosive kill)
}

// THE BREACHER'S CARD LEVELS (2026-09-26). self = player.
function c4_lv()
{
	return self card_lv( "c4", TOD_C4_MAX_LV );
}

function cluster_lv()
{
	return self card_lv( "cluster", TOD_CLUSTER_MAX_LV );
}

// charges per round for the current card level (0 = not earned)
function c4_max()
{
	lv = self c4_lv();
	if ( lv <= 0 ) return 0;
	return 1 + Int( lv / 3 );   // 1 / 2 / 3 / 4 from Lv1 / 3 / 6 / 9
}

function cluster_max()
{
	lv = self cluster_lv();
	if ( lv <= 0 ) return 0;
	n = 1;
	if ( lv >= 6 ) n++;
	if ( lv >= 9 ) n++;
	return n;   // 1 / 2 / 3 from Lv1 / 6 / 9
}

// damage multiplier for a card level (Lv1 = x1.0 = the old fixed kit)
function kit_dmg_mult( lv )
{
	if ( lv <= 1 ) return 1.0;
	return 1.0 + TOD_KIT_DMG_PER_LV * ( lv - 1 );
}

// THE TIER of this player's next C4 / Cluster (self = player; key "c4" / "cluster"): its charge count,
// 1..TOD_C4_TIERS / TOD_CLUSTER_TIERS. Only Cluster may use the dev preview override.
function kit_tier( key )
{
	top = ( ( key == "c4" ) ? TOD_C4_TIERS : TOD_CLUSTER_TIERS );
	tier = ( ( key == "c4" ) ? self c4_max() : self cluster_max() );
	if ( key != "c4" && TOD_KIT_TIER_CYCLE && IS_TRUE( level.tod_dev ) )
	{
		if ( !isdefined( self.tod_kit_tier_cycle ) ) self.tod_kit_tier_cycle = [];
		last = 0;
		if ( isdefined( self.tod_kit_tier_cycle[ key ] ) ) last = self.tod_kit_tier_cycle[ key ];
		preview = ( last % top ) + 1;
		self.tod_kit_tier_cycle[ key ] = preview;
		dev_log( "TIER_PREVIEW player=" + self GetEntityNumber() + " kit=" + key + " tier=" + preview + "/" + top + " card_tier=" + tier );
		self IPrintLn( ( ( key == "c4" ) ? "C4" : "CLUSTER" ) + " TIER " + preview + "/" + top );
		tier = preview;
	}
	if ( tier < 1 ) tier = 1;
	if ( tier > top ) tier = top;
	return tier;
}

function c4_tier_fx( tier )
{
	// User 2026-09-27: every C4 gets the huge blast. Card tier still sets damage
	// radius/charges; it never chooses a smaller visual variant.
	return TOD_C4_FX_BLAST;
}

// C4 radius 168 / 192 / 216 / 240 and shake 0.18 / 0.24 / 0.30 / 0.35 for tiers 1..4
function c4_tier_radius( tier )
{
	if ( !isdefined( tier ) ) return TOD_C4_RADIUS;
	return TOD_C4_RADIUS * ( 0.60 + 0.10 * Min( tier, TOD_C4_TIERS ) );
}

function c4_tier_quake( tier )
{
	if ( tier == 1 ) return 0.18;
	if ( tier == 2 ) return 0.24;
	if ( tier == 3 ) return 0.30;
	return 0.35;
}

function cluster_tier_fx( is_burst, tier )
{
	if ( isdefined( tier ) && tier == 1 ) return ( is_burst ? "tod/breacher/fx_tod_cl_burst_t1" : "tod/breacher/fx_tod_cl_pop_t1" );
	if ( isdefined( tier ) && tier == 2 ) return ( is_burst ? "tod/breacher/fx_tod_cl_burst_t2" : "tod/breacher/fx_tod_cl_pop_t2" );
	return ( is_burst ? "explosions/fx_exp_grenade_default" : TOD_CLUSTER_FX_BOMBLET );
}

// Cluster radius and shake x0.75 / 0.875 / 1.0 for tiers 1..3 (burst 96 / 112 / 128, pops 82 / 96 / 110)
function cluster_tier_scale( tier )
{
	if ( !isdefined( tier ) ) return 1.0;
	if ( tier == 1 ) return 0.75;
	if ( tier == 2 ) return 0.875;
	return 1.0;
}

function cluster_tier_radius( radius, tier )
{
	return radius * cluster_tier_scale( tier );
}

function owner_dmg_mult( owner, key )
{
	if ( !isdefined( owner ) || !isplayer( owner ) ) return 1.0;
	if ( key == "c4" ) return kit_dmg_mult( owner c4_lv() );
	return kit_dmg_mult( owner cluster_lv() );
}

// A level UP tops the charges to the new count; a level down (never, today) clamps.
function breacher_level_sync()
{
	c4 = self c4_lv();
	cl = self cluster_lv();
	if ( !isdefined( self.tod_c4_lv_seen ) || c4 > self.tod_c4_lv_seen )
	{
		self.tod_c4_charges = self c4_max();
		dev_log( "C4_LEVEL player=" + self GetEntityNumber() + " lv=" + c4 + " charges=" + self.tod_c4_charges + " dmg_mult=" + kit_dmg_mult( c4 ) );
	}
	if ( !isdefined( self.tod_cluster_lv_seen ) || cl > self.tod_cluster_lv_seen )
	{
		self.tod_cluster_charges = self cluster_max();
		dev_log( "CLUSTER_LEVEL player=" + self GetEntityNumber() + " lv=" + cl + " charges=" + self.tod_cluster_charges + " dmg_mult=" + kit_dmg_mult( cl ) );
	}
	self.tod_c4_lv_seen = c4;
	self.tod_cluster_lv_seen = cl;
	if ( isdefined( self.tod_c4_charges ) && self.tod_c4_charges > self c4_max() ) self.tod_c4_charges = self c4_max();
	if ( isdefined( self.tod_cluster_charges ) && self.tod_cluster_charges > self cluster_max() ) self.tod_cluster_charges = self cluster_max();
}

function blast( org, radius, owner, zombie_mult, elite_mult, weapon, what, tier, fx_id )
{
	// was the Raz shockwave: electric arcs read as an EMP (user 2026-09-26). POINTED UP (pitch -90): the
	// fireball is authored along its FORWARD axis (elements spawn 64-80 u out on X and fly X), so at
	// angles 0 it blew out sideways - user: "it triggers to the side of it ... being blown to the side".
	// Every charge now uses the complete top-tier presentation (2026-09-27).
	if ( !isdefined( tier ) ) tier = TOD_C4_TIERS;
	fx = fx_at( c4_tier_fx( tier ), org, ( -90, 0, 0 ) );
	if ( isdefined( fx ) )
	{
		fx.tod_c4_fx_id = fx_id;
		fx thread expire( 4.0 );
	}
	else dev_log( "C4_FX_FAIL id=" + fx_id + " effect=" + c4_tier_fx( tier ) + " reason=entity_pool_full" );
	fire = fx_at( "fire/fx_fire_ground_rubble_50x50", org, ( 0, 0, 0 ) );
	if ( isdefined( fire ) ) fire thread expire( 1.5 );
	sound_at( "tod_c4_explode", org, 4 );   // the user's own explosion wav (2026-09-27; was the Mangler impact)
	Earthquake( c4_tier_quake( TOD_C4_TIERS ), 0.6, org, radius + 100 );
	base = curve() * owner_dmg_mult( owner, "c4" );   // STICKY C4 card (2026-09-26)
	hit = 0;
	foreach ( z in enemies_within( org, radius ) )
	{
		fall = 1.0 - 0.5 * ( Distance( z.origin, org ) / radius );
		dmg = base * ( is_elite( z ) ? elite_mult : zombie_mult ) * fall;
		hurt( z, dmg, owner, "MOD_GRENADE_SPLASH", weapon, org );
		hit++;
	}
	// EXPLOSIVE FUSION (Breacher card, 2026-09-27): the blast heals the Breachers standing in it
	if ( !IS_TRUE( level.tod_upgrade_pause ) && isdefined( level.tod_cc_blast_heal_fn ) )
		[[ level.tod_cc_blast_heal_fn ]]( org, radius, "c4" );
	dev_log( what + "_BLAST id=" + fx_id + " owner=" + ( isdefined( owner ) ? owner GetEntityNumber() : -1 ) + " origin=" + org + " tier=" + tier + " visual_tier=4 fx_host=" + isdefined( fx ) + " r=" + radius + " hit=" + hit + " zombie_hp=" + base );
}

// STUN: the Electric Cherry recipe, restored by token. Real bosses are exempt.
function stun_enemy( e, ms )
{
	if ( !isdefined( e ) || !IsAlive( e ) || is_true_boss( e ) ) return;
	until = GetTime() + ms;
	if ( isdefined( e.tod_stun_until ) && e.tod_stun_until > until ) return;
	e.tod_stun_until = until;
	if ( !isdefined( e.tod_stun_token ) ) e.tod_stun_token = 0;
	e.tod_stun_token++;
	e thread stun_stock( e.tod_stun_token, ms );
}

function stun_stock( token, ms )
{
	self endon( "death" );
	level endon( "end_game" );
	self.zombie_tesla_hit = true;
	self.ignoreall = true;
	// docs/203: the shock tell lasts the WHOLE stun (the 1.2 s effect used to end 1.3 s before a
	// 2.5 s Bash stun did) - re-played every 1.2 s while the stun holds
	left = ms;
	while ( left > 0 )
	{
		fx = fx_at( "zombie/fx_tesla_shock_zmb", self.origin + ( 0, 0, 40 ) );
		if ( isdefined( fx ) )
		{
			fx LinkTo( self );
			fx thread expire( 1.2 );
		}
		step = ( left < 1200 ? left : 1200 );
		wait step / 1000.0;
		left -= step;
		if ( !isdefined( self ) || self.tod_stun_token != token ) return;
	}
	self.zombie_tesla_hit = false;
	if ( !IS_TRUE( self.tod_frozen ) && !IS_TRUE( level.tod_upgrade_pause ) ) self.ignoreall = false;
}
