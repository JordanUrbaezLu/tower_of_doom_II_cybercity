// =============================================================================
// _tod_upgrades.gsc — the upgrade tower system (the map's progression core).
//
// At rounds 1, 4, 8, 12... (dev: every round) the world PAUSES and every
// player gets TWO upgrade options for their class, each rolled with a RARITY:
//   REGULAR = +1 level    SUPER = +2 levels    ULTIMATE = +3 levels
// Rarity odds ride the 0..100% LUCK BAR (_tod_luck.gsc — kills/headshots/
// revives/doors/boss LAST HITS): 80/15/5 at 0% -> 20/50/30 at 100%, and the
// bar fully resets after each event. Choice UI: _tod_upgrade_ui.gsc
// (D-pad/stick moves focus, HOLD JUMP locks; 15s timeout locks the focused card).
//
// THE "NO TWIN MATRIX" ARCHITECTURE (the scalability answer):
// A 10-level × N-domain × M-class matrix of weapon variants would be thousands
// of weapon-table registrations — map 1 measured the engine hard-AVs past
// ~230 twins (docs/21 §A, silent 0xC0000005 at boot). So NO upgrade ever
// creates a weapon asset. One gun asset per class (+_up), and every domain is
// SCRIPT-side per-player state applied through engine levers:
//   DAMAGE   — zm::register_actor_damage_callback: scale the player's damage
//              when the hitting weapon is their class primary (+12%/Lv).
//   FIRERATE — same callback: 10%/Lv chance a bullet double-hits (an "echo"
//              round — DPS-equivalent; true ROF is baked into the weapon
//              asset, the one thing script cannot touch without twins. This
//              is the Double Tap 2 mechanism, stock-blessed).
//   MAGSIZE  — a virtual bottomless-mag pool (+20% of base clip per level):
//              when the clip runs dry mid-fight the pool instantly refeeds it
//              without a reload; a real reload refills the pool. No clip-size
//              field exists to edit at runtime — this is the lever that does.
// Adding a domain = one entry in register_domains + an apply hook here.
// Adding a class = _tod_classes::register_class. Nothing else scales with it.
// =============================================================================

#using scripts\shared\array_shared;
#using scripts\shared\callbacks_shared;
#using scripts\shared\flag_shared;
#using scripts\shared\hud_util_shared;
#using scripts\shared\laststand_shared;
#using scripts\shared\util_shared;
#using scripts\zm\_zm;
#using scripts\zm\_zm_score;
#using scripts\zm\_zm_stats;
#using scripts\zm\_zm_spawner;
#using scripts\zm\_zm_equipment;   // is_equipment (map 1's v19.58 equipment_kill_pay: riot shield kills pay)
#using scripts\shared\ai\zombie_utility;
// in_revive_trigger (the station: a revive press is not a purchase). NOT a
// cycle — scripts\zm\_zm_utility is stock, resolved from the modtools raw tree,
// and nothing under share/raw imports a zm_tod2_cybercity module.
// NAMESPACE CARE: zombie_utility (imported directly above) ships an
// identically-shaped is_player_valid, so EVERY call into this module must be
// written zm_utility:: and never bare.
#using scripts\zm\_zm_utility;

#using scripts\zm\zm_tod2_cybercity\_tod_classes;
// max_ammo_clip_watch — no cycle: _tod_powerups imports _tod_upgrade_ui, never
// this module (the KB cycle rule).
#using scripts\zm\zm_tod2_cybercity\_tod_powerups;
#using scripts\zm\zm_tod2_cybercity\_tod_upgrade_ui;
// crown terminal anchor (GENERATED leaf module — no #usings of its own, no cycle)
#using scripts\zm\zm_tod2_cybercity\_tod_breather_data;   // GENERATED — lounge station anchors (v13)
#using scripts\zm\zm_tod2_cybercity\_tod_crown_data;
#using scripts\zm\zm_tod2_cybercity\_tod_zombie_speed; // SUPPRESSING FIRE's slow (it imports no tod module — no cycle)
// CLASS TIER floor gate — the per-player floor high-water (it imports only
// flag_shared + util_shared, no tod module, so no cycle).
#using scripts\zm\zm_tod2_cybercity\_tod_gauge;
#using scripts\zm\zm_tod2_cybercity\_tod_archer_bow; // THE DRAW multiplier (imports no tod module - no cycle)
#using scripts\zm\zm_tod2_cybercity\_tod_ability_fx; // docs/206: A CARD TAKEN (a leaf module - no cycle)

#insert scripts\shared\shared.gsh;

// Upgrade cadence (user 2026-08-20): round 1 ALWAYS (dealt by the class
// draft the moment everyone locks — _tod_class_select calls
// run_upgrade_event directly), then DEV = every round / SHIP = every 4th
// round. Full ship sequence: 1, 4, 8, 12, ...
// ---------------------------------------------------------------------------
// UPGRADE TIERS (user 2026-08-21: "add a rarity on each upgrade ... which
// upgrades can make you OP — we want those to be S").
//
// A tier does TWO things, so an S upgrade is rare AND rarely stacked:
//   1. DRAW WEIGHT — how often the domain is even OFFERED as a card. B shows
//      up 3x as often as S (was 5x until 2026-09-08).
//   2. RARITY GATE — S/A cards shrink their SUPER+ULTIMATE slice toward
//      REGULAR, so "S domain at ULTIMATE (+3 levels)" is the rarest event in
//      the game even on a full luck bar.
//
// THE GAP NARROWED 2026-09-08 (user: "decrease the gap in general between S, A,
// B. Maybe something like 6%, 12%, 18%"). THOSE NUMBERS ARE A RATIO, NOT A
// SHARE, and the distinction matters if you retune this again: the weights are
// relative, so 6/12/18 is exactly 1:2:3, and the share a card actually gets
// depends on how many cards sit in its pool. With ~13 cards a pool lands near
// 4% / 8% / 12% per card, not 6 / 12 / 18. Ratios moved B:S 5.00 -> 3.00 and
// A:S 2.50 -> 2.00, so an S card is offered about 44% more often than before
// and a B card about 13% less.
//
// ⚠️ THIS IS THE DRAW HALF ONLY. The RARITY GATE below (TOD_TIER_R_*) is the
// band's other half and was NOT touched — an S card still halves its
// SUPER/ULTIMATE slice. If S still feels too rare after playing this, that is
// the second lever and it changes a different thing: how GOOD the S cards you
// do see are, rather than how often they appear.
// ---------------------------------------------------------------------------
#define TOD_CLASS_SPEED_ALL 1.1   // every class's move-speed scale, all tiers (user 2026-09-26; see class_speed_base)
#define TOD_TIER_B   1     // utility / incremental — common
#define TOD_TIER_A   2     // strong
#define TOD_TIER_S   3     // game-defining
// NO WEIGHTED CARDS (user 2026-09-28: "we're not doing any kind of like weighted card
// system. All cards will be equal for a class"): every band draws at the same weight and
// rolls SUPER/ULTIMATE at the same odds. The S/A/B tags stay on the cards (they cost
// nothing) but no longer change the deal. Was 18/12/6 and R_A 0.85 / R_S 0.65.
#define TOD_TIER_W_B 1     // draw weight (RELATIVE — only the ratio matters). 18/12/6 until 2026-09-28
#define TOD_TIER_W_A 1
#define TOD_TIER_W_S 1
// THE RARITY GATE — the band's SECOND job, softened 2026-09-08 (user, after
// reading what luck actually buys: "Apply a small change"). S 0.50 -> 0.65 and
// A 0.75 -> 0.85. DELIBERATELY SMALL: the shape is unchanged, S is still the
// hardest card to roll well, and this is one define pair to walk back.
//
// WHY THIS ONE AND NOT THE DICE. A band does two jobs and BOTH taxed S: it is
// offered less often AND its good rolls were halved. The draw half was narrowed
// to 1:2:3 earlier the same day, so this is the matching half — it leaves the
// luck curve everyone already has a feel for completely alone and only stops S
// being penalised twice for the same reason.
#define TOD_TIER_R_A 1.0   // SUPER/ULTIMATE slice multiplier: 1.0 = no band penalty (2026-09-28; 0.85 before, 0.75 until 2026-09-08)
#define TOD_TIER_R_S 1.0   //                                 (2026-09-28; 0.65 before, 0.50 until 2026-09-08)

// ---------------------------------------------------------------------------
// LUCK GUARANTEES (user 2026-08-26: "max luck needs to guarentee at least one
// ultimate upgrade. And 50% guarentees one super").
//
// A FLOOR ON THE DEAL, NOT A REPLACEMENT FOR THE ROLL. Both cards still roll
// independently through roll_rarity exactly as before; guarantee_rarity() then
// looks at what came out and, if the bar earned better than the dice gave,
// promotes ONE card up to the floor. A deal that already beat the floor is left
// completely alone — this can only ever raise a card, never lower one.
//
// v14.6 — AND THE FLOOR CAN REDEAL (user 2026-08-30, after a max-luck game
// with no ULTIMATE): when neither dealt card has the HEADROOM to absorb the
// owed rarity (low-cap domains — PENETRATION/RECOIL max 2, SPRINT FIRE max 1
// — or anything near its cap), guarantee_rarity swaps the weakest dealt card
// for a pool domain that CAN absorb it, then promotes that. The full ladder
// of outcomes at a full bar: dice ultimate > promoted ultimate > redealt
// ultimate > (only when NO domain anywhere has +3 of headroom) the old
// clamped-and-honest label. Details at guarantee_rarity.
//
// THE THRESHOLDS MATCH THE HUD EXACTLY, and that is deliberate. The luck bar is
// drawn as 10 segments via set_luck_pct's int(pct/10), so the 10th segment lights
// at >= 100 and the 5th at >= 50 — the same two numbers below. A player who can
// see a full bar gets the ULTIMATE, and one who can see five segments gets the
// SUPER. Do not "helpfully" loosen these to 99.5 or 49.5: that would fire the
// guarantee on a bar the player can still see is short, which is a worse lie
// than the one it would be trying to fix.
//
// 100 IS REACHABLE — set_bar clamps anything over TOD_LUCK_MAX to exactly 100,
// so a full bar is exactly 100.0 and not 99.9997.
// 2026-09-28 FOUR RARITIES (docs/187, user): COMMON +1 / RARE +2 / EPIC +3 / LEGENDARY +4.
// o.rarity is 1..4 and equals the levels a card pays (before the headroom clamp).
#define TOD_RAR_COMMON          1
#define TOD_RAR_RARE            2
#define TOD_RAR_EPIC            3
#define TOD_RAR_LEGENDARY       4
#define TOD_UPG_GUAR_EPIC_BAR 100  // bar >= this: one card is EPIC or better (+3)
#define TOD_UPG_GUAR_RARE_BAR  50  // bar >= this: one card is RARE or better (+2)
// the full bar's guaranteed card comes up LEGENDARY this often (user: "can be legendary")
#define TOD_UPG_GUAR_LEG_PCT   25
// v14.9 THE OVERCHARGE PAYOUT (user 2026-08-30: at 150% "both options are
// guaranteed to be ultimates rarity"). The luck bar secretly tracks 100..150
// now (_tod_luck TOD_LUCK_OVERMAX — LOCKSTEP PAIR, the two defines must move
// together); at the ceiling the deal guarantees EVERY non-tier card ULTIMATE,
// not just one. The band between the two thresholds is deliberately invisible
// (same full-bar HUD) but still real: roll_rarity keeps riding the raw value,
// so 100..149 quietly improves both dice before the 150 floor takes over.
// The 105..111 "thresholds match the HUD" doctrine above still holds for THESE
// two numbers; 150 is the exception BY DESIGN — its tell is not a segment, it
// is the overcharge zap animation + sound, which fire at exactly this value.
// TOD_UPG_GUAR_BOTH_BAR RETIRED 2026-09-28 with the overcharge (user: "I dont want overcharge anymore").
// v16.56 THE FULL-BAR PROMOTION (user 2026-09-02: "When you have max luck and
// your gun is pap and you are eligible for a class upgrade you should be
// guaranteed one. That means you must fulfill the floor condition as well").
// At or above this bar a deal to a FULLY tier-eligible player (PaP'd, floor
// gate cleared, next gun linked — tier_card_eligible, never the but-for-floor
// half) carries the TIER card 100% of the time instead of TOD_TIER_CARD_PCT.
// "Max luck" is the FULL VISIBLE BAR — the same 100 the ULTIMATE floor keys
// on, per the doctrine above (the 150 overcharge is a secret band; a guarantee
// the player cannot see they have earned is not a guarantee). A floor-blocked
// player keeps the ordinary 20% draw-and-show-locked path; the bar buys the
// promotion only once the climb is done. One owner: tier_card_guaranteed().
#define TOD_UPG_GUAR_TIER_BAR  100  // bar >= this + fully tier-eligible: the TIER card is dealt

// THE OPENING HAND (user 2026-08-26: "the first upgrade in the game for the
// player that comes after picking a class should always have at least one super
// card"). That is the round-1 deal the class draft hands out the moment everyone
// locks (_tod_class_select.gsc:106 calls run_upgrade_event directly).
//
// WHY IT NEEDS ITS OWN FLOOR: the luck bar is the ONLY thing that lifts rarity,
// and at that moment it is exactly 0 — nobody has killed anything yet. So the
// opening deal rolls the base 80/15/5 and comes up REGULAR+REGULAR about 64% of
// the time. The one hand that sets the tone for the whole run was the worst hand
// in the game.
//
// PER PLAYER, ONCE PER RUN, latched on player.tod_first_deal_done. Per-player
// rather than a level flag so a co-op late joiner still gets an opening hand,
// and so one player's deal cannot consume another's.
#define TOD_UPG_GUAR_FIRST      2   // first deal of the run: at least RARE (+2)

#define TOD_UPG_EVERY_N_SHIP    4
#define TOD_UPG_CHOICE_TIMEOUT  15  // 15s window, then the focused card auto-locks
// DAMAGE: +10% per level (v15, user 2026-08-31: "Can we lower damage upgrade to
// 10% instead of 12%"). At the 10-level cap that is +100%, down from +120%, so
// the peak additive multiplier falls 2.20x -> 2.00x = -9.1% on everything.
// ⚠️ THE LITERAL COPY IN _tod_bosses::rp_damage_feed MUST MOVE WITH IT — a GSC
// #define is file-local and that lane cannot see this symbol. Its HEADSHOT twin
// was already stale once and overpaid 2.5x on the Rogue Protector for a day.
// Grep TOD_UPG_DMG_PER_LVL, never a line number.
// The CARD ART carries "+12/+24/+36%" baked in and MUST be re-baked (docs/33).
#define TOD_UPG_DMG_PER_LVL     0.10   // +10% damage per level (was 0.12 until 2026-08-31)
// THE CORE WEAPON CARDS (2026-09-27, user: "remove the damage card altogether ...
// each class will have its own specific ... core primary ... upgrade" / "a damage
// increase on each level, and then we have buckets ... level three should be a
// big upgrade" / "level nine as max"). Damage per level on the class's OWN primary
// (core_weapon_bonus), plus a big step at Lv3 / Lv6 / Lv9 (see axis_level and each
// class module). THE STEPS DIFFER ON PURPOSE so a maxed class lands near the same
// single-target gain (~x2.2 at Lv9), because each bucket already adds damage in
// its own shape:
//   ARCHER  deadeye    7% / Lv  (x1.63) x the "d" forms' fire cadence (~x1.33) = ~x2.2
//   BREACHER buckshot  4% / Lv  (x1.36) x the pellets at Lv9 (Moz x2.0, 870 x1.62, PK x1.64) = ~x2.2-2.7
//   WARRIOR heavyhands 7% / Lv  (x1.63) x the swing-speed forms at Lv9 (-26% swing, x1.35) = ~x2.2
//   NECROMANCER soulbeam 10% / Lv (x1.9), applied INSIDE the beam (_tod_necro_skull) because the
//                      soul-rip test must see the real number; its buckets add souls, not damage.
// The old DAMAGE card was x2.0 on every weapon for every class (the Breacher's
// pellets on top made it x4). LOCKSTEP: tod_upgrade.lua DETAIL rows 6 / 58 / 7 / 39.
#define TOD_CORE_DMG_ARCHER     0.07
#define TOD_CORE_DMG_BREACHER   0.04
#define TOD_CORE_DMG_WARRIOR    0.07
#define TOD_CORE_BUCKET         3      // the big steps land every 3 levels: Lv3 / Lv6 / Lv9
#define TOD_UPG_ECHO_PCT_PER_LVL 10    // +10%/level chance to double-hit
#define TOD_UPG_MAG_PCT_PER_LVL 0.20   // +20% of base clip per level
#define TOD_UPG_BOUNTY_PER_LVL  0.05   // RECORD: +5%/Lv (user 2026-08-20, was 3%); since 2026-09-28 BOUNTY is bounty_rate() (log, +100% at Lv9)
#define TOD_UPG_BOUNTY_MAX      1.00   // BOUNTY at Lv9 (user 2026-09-28: "Max both at +100% at level 9"), on card_curve
// HEADSHOT: +12% per level over FIVE levels (user 2026-09-08: "change headshot
// upgrade to 12% per tier and only 5 tiers"). History of the RATE:
// 0.10 -> 0.04 (2026-08-22 nerf) -> 0.03 (v9.45, 2026-08-23) -> 0.04
// (2026-08-26 assault buff) -> 0.05 (2026-08-30) -> 0.12 here. History of the
// CAP: 10 -> 5 in this same pass, and the max lives on the add_domain call, not
// here — change both or the card offers levels the ladder no longer prices.
//
// THE CAP AND THE RATE MOVED TOGETHER AND THAT IS THE WHOLE POINT: +50% at ten
// levels becomes +60% at five. The ceiling barely moves (+10pp); what changes
// is the SHAPE — a card is worth 2.4x what it was, and the domain finishes in
// five picks instead of ten. This is a pacing change wearing a buff's clothes.
//
// WHAT IT IS ACTUALLY WORTH — quote this, never the headline. Every damage
// domain adds into ONE unclamped sum and DAMAGE alone contributes +1.00 at cap,
// so a maxed assault headshotting a boss moves 3.10x -> 3.20x = +3.2% real
// damage, and a headshot on the horde moves 2.50x -> 2.60x = +4.0%. "5% -> 12%"
// reads like +140% and is not. Same trap as the 2026-08-26 and 08-30 passes.
//
// THE HAND-COPIED LITERAL IN _tod_bosses::rp_damage_feed IS GONE (2026-09-08).
// It was the one this comment used to warn about — a GSC #define is file-local,
// that lane could not see this symbol, and it went stale once (0.10 there while
// this said 0.04) and paid 2.5x on the Rogue Protector for a day. It now calls
// headshot_bonus(), which owns the rate AND the dark add, exactly as
// boss_damage_bonus already did for GIANT SLAYER. Do not re-introduce a copy.
//
// STILL HAND-MAINTAINED, so change these in the same commit:
//   * tod_upgrade.lua DOMAIN[6].desc AND .max, DETAIL[6].val, dark DETAIL[6].val
//   * the CARD ART bakes "+5% HEADSHOT DMG" as pixels — a re-bake is OWED, and
//     per the generic-card-text rule it should come back NUMBERLESS so the next
//     retune owes nothing. The pause plate (i_tod_pause_r06) is name-only and
//     needs no re-bake.
//   * docs/armory.html (the DOMAINS row, the Ceilings term, the Verdict row)
#define TOD_UPG_HS_PER_LVL      0.12
// MOVE SPEED IS A DIMINISHING LADDER, NOT A FLAT PER-LEVEL RATE (v15,
// 2026-08-31 — user: "We also need to nerf the speed boost upgrade in general.
// It should be 5%, 4%, 3%, then 3% each level after").
//
// Per-level INCREMENTS: 5, 4, 3, 3, 3, 3, ...  ->  cumulative totals
//   Lv1 +5%  Lv2 +9%  Lv3 +12%  Lv4 +15%  Lv5 +18%
//   Lv6 +21% Lv7 +24% Lv8 +27%  Lv9 +30%  Lv10 +33%
// (was a flat 5%/Lv, i.e. +50% at Lv10 — so the ceiling falls by a third.)
//
// ⚠️ THE CARD ART CONSEQUENCE, and it is the whole reason this is not a
// one-line change: the value is no longer LINEAR, so a card can no longer print
// "+5% / +10% / +15%" and be true at every rarity. Per the domain-retune
// checklist a stage-table domain must either print the whole ladder or say
// nothing — and the user chose nothing: "the assets probably need to be
// upgraded so they are generic. And the pause menu can show the exact upgrade
// number." So SPRINT and FORCED MARCH cards get GENERIC copy (no number) and
// the exact figure is served per-player by the pause menu (item 26).
//
// TOD_UPG_SPEED_PER_LVL IS GONE ON PURPOSE. Leaving it would have let a future
// reader multiply by it and silently get the old flat curve back; every caller
// must go through speed_pct_for_level().
#define TOD_UPG_SPEED_L1        0.05   // the first level's increment
#define TOD_UPG_SPEED_L2        0.04   // the second's
#define TOD_UPG_SPEED_LN        0.03   // every level from the third on
#define TOD_SPRINT_CARD_MAX     0.30   // SPRINT (Archer) at Lv9, on card_curve (log) - 2026-09-28
// SPRINT ARMOR (v9.28, user 2026-08-23: "take less damage when you are
// running, 5% each level, 5 levels max, only for melee and skirmisher"):
// incoming damage x (1 - this*Lv) WHILE the engine says the player is
// sprinting (IsSprinting, server builtin). Applied in _tod_bosses' two
// player-damage lanes right after DMG REDUCTION — the two stack
// multiplicatively (Lv5 of both while sprinting = x0.75 x 0.75).
#define TOD_UPG_SPRINT_ARMOR_PER_LVL 0.05
// DMG REDUCTION — THE DIMINISHING LADDER (v16, 2026-09-01, user: "damage
// reduction should go +6%, +5%, 4%, 3%, 2%"). PER-LEVEL INCREMENTS, so the
// CUMULATIVE reduction is 6 / 11 / 15 / 18 / 20% at Lv1..Lv5.
//
// This is a NERF AT THE CAP and a BUFF AT THE BOTTOM: the old flat 5%/Lv paid
// 5/10/15/20/25, so the first card is now worth +1pp more and the fifth is
// worth 5pp less. Paired in the same commit with the band move S -> A below,
// which makes the domain ~2.5x more likely to be dealt. Read together, DR stops
// being a rare game-definer you hoard and becomes a common early pick whose
// last two levels are deliberately not worth chasing.
//
// ⚠️ THIS KILLED THE HAND-COPIED-LITERAL PROBLEM, ON PURPOSE. Until v16 the two
// application lanes in _tod_bosses.gsc carried bare 0.05 literals, because a GSC
// #define is FILE-LOCAL and cannot reach across files — and this file used to
// carry a comment instructing the next person to edit both copies by hand. A
// diminishing ladder cannot be expressed as a literal multiply at all, so that
// arrangement was not merely fragile, it had stopped being possible. Both lanes
// now CALL dr_mult() instead, which is the same shape sprint_armor_mult and
// back_armor_mult have always had, and is what boss_damage_bonus already does.
// DO NOT reintroduce a per-level constant here for anyone to copy.
#define TOD_UPG_DR_L1           5    // 2026-09-28 (user): 5 / 3 / 2 / 2 / 2 ... = 5 8 10 12 14 16 18 20 22% at Lv1..9 (was 6/5/4/3 then 2)
#define TOD_UPG_DR_L2           3
#define TOD_UPG_DR_L3           2
#define TOD_UPG_DR_L4           2
#define TOD_UPG_DR_LN           2    // every level past 5, if the cap ever rises
// GIANT SLAYER (v9.45, user 2026-08-23: "an upgrade where they do more damage
// to boss and elites. 3% per level, can go to level 5"; BUFFED to 4%/Lv
// 2026-08-26; BUFFED to 5%/Lv 2026-08-30; BUFFED to 8%/Lv 2026-08-31, user: "buff the headshot and boss
// damage upgrades for the assault class from 4% to 5% each level"). ASSAULT.
// +5%/Lv, added into the SAME additive mult sum as DAMAGE and HEADSHOT rather
// than multiplying on top of it — so Lv5 is +25% of BASE damage, not +25% of
// the already-multiplied total.
//
// WHAT COUNTS AS A BOSS OR ELITE: the map-wide triad is_boss / acc_is_boss /
// acc_is_mini_boss, which the Panzer, the Rogue Protector AND the Reaver all
// set synchronously on their spawn frame. Eight other systems already gate on
// exactly those three fields (the zombie speed curve, IMPACT ROUNDS,
// SUPPRESSING FIRE, THOR'S THUNDER, the powerup drop roll, the floor gauge,
// CHAIN LUNGE, Electric Cherry), so a future elite that sets the triad is
// covered by this card for free, and one that does not is invisible to all
// nine at once. Read it through is_boss_or_elite() — never re-spell the triad.
#define TOD_UPG_BOSSDMG_PER_LVL 0.12   // 15% -> 12% v16.50 (user 2026-09-02: "nerf giant slayer to 12% each tier") = +60% at the Lv5 cap
// MELEE vs THE BOSS/ELITE TRIAD (user 2026-08-24: "we need to nerf melee. They
// will do 50% damage against bosses and elites"). WHY IT WAS NEEDED: melee
// damage is a FLAT per-weapon number (_tod_classes::register_melee_dmg —
// knife 2000/4000, wakizashi 4000/8000, Stormbreaker 6800/13600) that does not
// scale with the target, while boss HP compounds per round. A PaP'd
// Stormbreaker under DAMAGE Lv10 + DRAW CUT Lv3 + GIANT SLAYER swings for
// ~52k, which deletes a round-30 Panzer (129k) in three hits.
// Applied MULTIPLICATIVELY to the FINAL, so it scales the base hit, every
// damage domain and the insta-kill window alike, and it is read through
// melee_boss_mult() — never re-spelled — for the same reason the triad test is
// (see is_boss_or_elite above).
// 0.5 -> 0.33 (user 2026-08-30, alongside the -20% melee damage pass): melee
// now deals ONE THIRD against the triad. Compounded with that pass a blade
// swing lands at 0.264x its pre-2026-08-30 value against a Panzer / Rogue
// Protector / Reaver, and is unchanged in that ratio against ordinary zombies
// (which pay only the -20%).
// TWO RATES SINCE v18.3, split by the ATTACKER'S CLASS (user 2026-09-06,
// clarifying the +75% they had just asked for: "when i said melee i
// specifically meant slasher").
//
// v18.2 raised the SHARED constant to 0.5775 and so handed the buff to every
// class's bare knife as well - an assault player knifing a Panzer got the
// slasher's compensation. The knob is now two:
//
//   TOD_MELEE_BOSS_MULT           0.33    every other class's melee. Exactly
//                                         where it has sat since 2026-08-30 -
//                                         v18.3 restores it, it is not a nerf.
//   TOD_MELEE_BOSS_MULT_SLASHER   0.5775  the SLASHER only: 0.33 x 1.75, the
//                                         +75% as asked.
//
// Both are picked by melee_boss_mult(), which now takes the ATTACKER as its
// first argument. Never re-spell either value or the class test - the same
// rule the triad test has always carried, and this file has already shipped a
// stale hand-copied melee constant once.
#define TOD_MELEE_BOSS_MULT     0.33
#define TOD_MELEE_BOSS_MULT_SLASHER 0.5775
// THE SLASHER'S SIDEARM vs THE BOSS/ELITE TRIAD (v16, 2026-09-01 — user: "the
// secondaries of slasher should be 2.25x damage on elites and bosses").
//
// WHY THE SLASHER SPECIFICALLY NEEDED THIS. Its blade already pays
// TOD_MELEE_BOSS_MULT 0.33 against the triad, and of the eleven domains a T3
// slasher can roll exactly ONE raises boss damage: THOR'S THUNDER skips the
// triad outright, CLEAVE is splash onto other zombies, LEECH is kill-gated, and
// GIANT SLAYER and HEADSHOT are assault-only. So the class's answer to a Panzer
// was "swing fifteen times inside the flames". This turns the sidearm — the one
// tool it carries that is NOT scaled down against bosses — into the real answer,
// which is a play pattern (swap off the blade for the boss) rather than a
// number.
//
// MULTIPLICATIVE ON THE FINAL, not a term in the additive sum. Same placement
// and same reasoning as melee_boss_mult: it scales the base hit, DAMAGE and
// every other domain together instead of fighting them one at a time, and the
// crosshair number is pushed after it so what the player reads is what the boss
// took. "2.25x" in the ask is a multiplier, not a percentage to add.
#define TOD_SLASHER_SEC_BOSS_MULT  2.25
// GUNSLINGER (domain 44, v16.51 — user 2026-09-02: "Slashers need an ability
// that make their secondary do more boss and elite damage. 30% each tier up to
// 5 tiers. This will be B tier"). The DOMAIN half of the same lane: the
// slasher's class secondary vs the triad pays +30%/Lv.
//
// ADDITIVE SINCE v16.99 (user, after the balance review: "Yes make gunslinger
// additive"). gunslinger_bonus() returns lvl x TOD_UPG_GUNSLINGER_PER_LVL as a
// TERM IN THE SHARED mult SUM, next to DAMAGE and every other additive domain;
// slasher_sidearm_boss_mult() keeps ONLY the class baseline
// TOD_SLASHER_SEC_BOSS_MULT. Two callers, and both must add the term or the
// domain silently does nothing on that path: upgrade_damage_cb here, and
// _tod_bosses::rp_damage_feed (the aiOverrideDamage fallback).
//
// THE OLD COMMENT'S ARITHMETIC WAS RIGHT AND THAT WAS THE PROBLEM. It argued
// for multiplying because an additive term is "worth a third of that against a
// 2.25x hit" — true, and precisely the effect being removed. Compounding on the
// baseline made Lv5 a 5.625x hit, so one domain outran the whole additive pool
// and the slasher's boss damage stopped being readable against any other
// class's. Additive costs the domain its ceiling on purpose. Do NOT restore the
// multiply because the number "looks small": it is small, measured against a
// baseline that is already the largest single multiplier a class gets.
//
// The three gates (slasher, class secondary, boss/elite) live in
// slasher_sidearm_vs_boss() and are shared by both halves, so the baseline and
// the domain can never disagree about what counts as a qualifying hit.
#define TOD_UPG_GUNSLINGER_PER_LVL 0.30
// BACK ARMOR (v9.45, user 2026-08-23: "for AR and LMG we need a new upgrade
// where getting hit from behind does 10% less damage and can go 3 levels").
// ASSAULT + HEAVY, -10%/Lv, so Lv3 = -30% from behind.
//
// "BEHIND" = the attacker sits in a rear ARC around the player's VIEW forward,
// flattened to 2D (a zombie on the flight below you is not behind you, it is
// under you). The DOT is the cosine measured from the player's FORWARD vector:
// -0.34 opens a 140-degree rear arc, i.e. 70 degrees either side of due back.
// Wider than a literal "behind" cone on purpose — the horde surrounds you on a
// landing and a 90-degree cone would almost never pay out. Still strictly
// narrower than a hemisphere, so a hit square on the shoulder is not "behind".
//
// Applied MULTIPLICATIVELY after DMG REDUCTION in both of _tod_bosses'
// player-damage lanes, exactly like SPRINT ARMOR — see back_armor_mult().
#define TOD_UPG_BACK_ARMOR_PER_LVL 0.10
#define TOD_BACK_ARC_DOT           -0.34
// ---------------------------------------------------------------------------
// TIRELESS — REMOVED 2026-08-26. (user: "for sprint we are saying skirmisher
// gets unlimited. That does work and we tried to implement multiple times.
// Lets just remove that benefit so skirmisher doesnt get that extra benefit".)
//
// SPRINT is now +5% move speed per level and NOTHING ELSE, for both classes
// that can roll it. There is no Lv5 rider, no class gate on the domain, and no
// script anywhere sets `specialty_staminup` — Stamin-Up the perk machine is the
// only thing in the map that grants it again.
//
// WHAT WAS TRIED, so nobody spends a fourth session on it:
//   1. grant `specialty_staminup` only .......... no meter change at all
//   2. + server-side SetSprintDuration(60) ...... no meter change at all
//   3. + SetClientPlayerSprintTime(999) ......... the documented per-client
//      lever (docs_modtools/bo3_scriptapifunctions.htm: "Sets player_sprintTime
//      dvar only on this client"), set on grant AND re-sent on every spawn by a
//      dedicated watcher — and the user still reported the meter draining.
// The diagnosis in (3) is almost certainly right: the meter is PREDICTED ON THE
// CLIENT from that client's own `player_sprintTime` dvar, which stock writes
// once at connect (zm/gametypes/_globallogic_player.gsc:125), so the server-side
// duration can never reach it. What was never established is whether the setter
// actually sticks for a usermap client. If this is ever revived, THAT is the
// experiment to run first — print the client's live `player_sprintTime` after
// the call and confirm it reads 999 — not another round of re-asserting it from
// a new callback. Three passes have now re-sent the same value more often
// without once checking whether it landed.
//
// The card art carried "LV 5 TIRELESS · SKIRMISHER" on all three rarities and
// was re-baked without it in the same pass.
// ---------------------------------------------------------------------------
// SCAVENGER — v16.40 (user 2026-09-02: "Scavenger needs a nerf at higher
// levels so it needs to diminish enhancements every tier like most upgrades.
// The high tier is way too good."). THE SHAPE FLIPPED. The kill-counter
// ladder recorded below paid 0.20 / 0.25 / 0.33 / 0.50 / 1.00 / 1.50 rounds
// per kill — each level added MORE than the last, and Lv5-6 were infinite
// ammo whenever a kill cost a bullet or two. Now every primary kill BANKS a
// fraction of a round and a whole round pays out of the bank. THE LADDER IS
// AUTHORED IN KILLS PER ROUND (v16.42, the user's own numbers: "Lets do 4, 3,
// 2.4, 2, 1.8" ... "and 1.6"), stored as TENTHS so the bank stays integer
// (1 per 3 kills is not a whole percent — v16.40/41 kept a percent bank and
// could not express it):
//   Lv1 2.8  Lv2 2.3  Lv3 2.0  Lv4 1.8  Lv5 1.6  Lv6 1.4 (assault only)
//   kills per round; steps 0.5 / 0.3 / 0.2 / 0.2 / 0.2 — diminishing.
//   = 0.36 / 0.43 / 0.50 / 0.56 / 0.63 / 0.71 rounds per kill.
// v18.86 (2026-09-13) THE FRONT OF THE LADDER SHIFTED UP, THE TOP DID NOT
// (user: "early on it's almost not noticeable ... but we also don't want it
// to be super, super OP when it's maxed out ... shift over the earlier
// tiers"). Lv1 4.0 -> 3.0, Lv2 3.0 -> 2.5, Lv3 2.4 -> 2.2; Lv4/5/6 were
// UNTOUCHED in that pass.
// v18.88 (2026-09-13, same session, user: "Lets shift all by another 0.2")
// THEN SHIFTED THE WHOLE LADDER, TOP INCLUDED: every rung loses 0.2 kills,
// so Lv1 3.0 -> 2.8 and the assault capstone 1.6 -> 1.4 — the first time
// the ceiling has moved since v16.42. A UNIFORM shift, which is why the step
// table above is IDENTICAL to v18.86's: subtracting a constant cannot change
// the gaps. That is why the shape survived a retune nobody re-derived — the
// diminishing-step rule (0.5 / 0.3 / 0.2 / 0.2 / 0.2, never growing) is a
// property of the DIFFERENCES, not the values. Do not "fix" the three equal
// 0.2 steps at the top by re-accelerating them; that shape IS the v16.40
// nerf and it is deliberate. And WATCH THE FLOOR on any further shift: Lv6
// is 1.4 kills now, and no rung may reach 1.0 without becoming a round per
// kill, which is the exact thing v16.40 was written to kill. Past that point
// a shift has to become a re-shape.
// HISTORY OF THE DAY: v16.40 flipped the accelerating kill counter into a
// diminishing percent bank (20/30/38/44/48/52 per 100 kills = 5.0/3.3/2.6/
// 2.3/2.1/1.9 kills); v16.41 raised the anchor to 1 per 4 (25/35/43/49/53/57
// = 4.0/2.9/2.3/2.0/1.9/1.8; user: "The top end is pretty bad too"); v16.42
// is the user's ladder verbatim. Against the pre-v16.40 ladder: Lv1 +0.05,
// Lv2 +0.08, Lv3 +0.08, Lv4 level, Lv5 1.00 -> 0.56, capstone 1.50 -> 0.63.
// The two rules that always held it still do: ONE round per shot (the
// same-frame latch in on_class_gun_kill; a multi-kill banks, it never stacks
// payouts — the bank re-arms one kill short after a payout, the old "held at
// need-1" rule in fractional form) and maxAmmo. It is a refund, never a
// multiplier. The card art carries no numbers (docs/33, user: "our asset is
// generic enough"), so this owes only the pause-menu row (tod_upgrade.lua [8])
// and the armory row. scav_kills10() is the one reader.
// DEAD 2026-10-05 (W2E): SCAVENGER retired whole (parked since 2026-09-26, dealt to no class); every
// TOD_SCAV_* below stays as the tuning record, read by nothing.
#define TOD_SCAV_KILLS10_L1    28     // kills per refunded round x10 at Lv1 (= 1 per 2.8 kills) ...
#define TOD_SCAV_KILLS10_L2    23     // 1 per 2.3
#define TOD_SCAV_KILLS10_L3    20     // 1 per 2.0
#define TOD_SCAV_KILLS10_L4    18     // 1 per 1.8
#define TOD_SCAV_KILLS10_L5    16     // 1 per 1.6
#define TOD_SCAV_KILLS10_L6    14     // 1 per 1.4 — the assault's capstone rung (bonus_max 6)
//
// ⚠️ EVERYTHING FROM HERE TO TOD_SCAV_CAP_ROUNDS IS HISTORY (v9.10 → v16.39),
// kept as the tuning record in the file's "echo" pattern. Nothing reads the
// five DEAD defines; the live ladder is the six TOD_SCAV_KILLS10_* above.
//
// SCAVENGER (v9.10, user 2026-08-22: "max 1 bullet back on one shot ... 1
// bullet every N kills, N shrinking per level, 2 kills is the most it'll
// go"): a KILL COUNTER paid ONE round at a time. Kills per round =
// LV1 - (lvl-1), floored at MIN:
//   Lv1 6 / Lv2 5 / Lv3 4 / Lv4 3 / Lv5 2 / Lv6 (assault only) 1.
// History: 2 rounds/kill/Lv -> 1 (2026-08-20 "unlimited ammo") -> 0.25 banked
// fractionally (2026-08-21 "too strong") -> the 7..2 ladder -> 2026-08-26 BUFF
// (user: "we need a buff on scavenger. Move it down by 1 kill on each level"),
// shipped alongside the +1 magazine on every gun — the same ammo-scarcity
// complaint answered from both ends.
//
// BOTH CONSTANTS HAD TO MOVE, and that is the whole subtlety of this retune.
// `need` is LV1 - (lvl-1) CLAMPED UP to MIN, and the old MIN of 2 was not a
// safety rail — it was the exact Lv6 value (7-5 = 2). Dropping LV1 alone would
// have bought Lv1-Lv4 a kill each and then let the clamp eat the buff at
// exactly the two levels players grind for: Lv5 and the assault Lv6 would both
// have stayed at 2. MIN moves in lockstep so every level really does come down
// by one, which is what was asked for.
//
// Lv6 = 1 kill per round is the strongest this has ever been, and it is still
// bounded by the two rules that have always held it: ONE round per shot (the
// same-frame latch in on_class_gun_kill, so a penetrating multi-kill still pays
// exactly one) and maxAmmo (a refund cannot exceed the reserve cap). It is a
// refund, never a multiplier.
#define TOD_SCAV_KILLS_LV1      5      // DEAD (v16.40) — was kills per refunded round at Lv1
#define TOD_SCAV_KILLS_MIN      1      // DEAD (v16.40) — was the floor (Lv5: 1 kill, 1 round)
// THE CAPSTONE (user 2026-08-26, second buff of the night: "buff again by one
// kill. The final stage should be 3 bullet every 2 kills"). Shrinking `need`
// one more step per level runs out of room — Lv5 reaches 1 kill and Lv6 would
// need 0, which is not a thing. So the LAST rung stops shrinking the kill count
// and starts GROWING the payout instead: 2 kills -> 3 rounds, a rate of 1.5
// rounds/kill against Lv5's 1.0.
//
// IT IS ASSAULT-ONLY, because level 6 is. add_domain gives SCAVENGER max 5 with
// bonus_class "assault" at 6, so the 6th rung has always been the assault's
// alone — the capstone lands on the class whose signature this domain already
// is. Every other class tops out at Lv5 = one round per kill. If the capstone is
// ever wanted for everyone, the change is `TOD_SCAV_CAP_LVL 5` plus a new value
// for the assault's 6th; do NOT just lower the cap level and leave Lv6 equal to
// Lv5, or the assault's bonus rung silently becomes worthless.
#define TOD_SCAV_CAP_LVL        6      // DEAD (v16.40) — was the capstone rung (assault's bonus level)
#define TOD_SCAV_CAP_KILLS      2      // DEAD (v16.40) — was capstone: 2 kills...
#define TOD_SCAV_CAP_ROUNDS     3      // DEAD (v16.40) — ...paid 3 rounds
// (TOD_UPG_HP_PER_LVL removed 2026-08-20 — HEALTH became DMG REDUCTION,
// -4%/Lv, applied in _tod_bosses' player-damage chain.)
// REGEN REMOVED 2026-08-30, v14.11 (user: "Remove regen upgrade from Heavy
// class"). The define stays as the tuning record, the "echo" pattern; the
// body-loop hook and the add_domain call are gone. The heavy's sustain is now
// VITALITY (+max HP) and RECOVERY (regen starts sooner) below.
#define TOD_UPG_REGEN_PER_LVL   0.005  // DEAD — was +0.5% max HP/s per level (HEAVY)
// VITALITY (HEAVY, v14.11 — user 2026-08-30: "extra health. 5 levels and
// player keeps it for whole game. S tier. increase health by 10 for each
// [level]"). +10 max HP per level, 5 levels => +50 at cap on the 150 base.
// Scope "class" (set_scope below): survives every tier promotion, per the ask.
//
// ⚠️ THE "JUGG-SAFE BECAUSE JUGG IS ADDITIVE" CLAIM THAT USED TO LIVE HERE WAS
// WRONG, and shipped a live bug (v14.28, user: "Vitality upgrade breaks when
// you get jugg. I have 210 but level 3 vitality... went back down to 200").
// Jugg's PURCHASE is additive — but stock ALSO rebuilds max FROM SCRATCH via
// perk_set_max_health_if_jugg("health_reboot") on every ROUND TRANSITION
// (_zm.gsc:4521), on laststand revive, and on jugg loss, computing
// player_base_health (+jugg) and discarding vitality entirely. The trap's
// asymmetry: without jugg the rebuilt 100 sat BELOW the maintain floor and was
// silently repaired; with jugg the rebuilt 200 sat ABOVE a jugg-blind floor,
// so it looked like "vitality breaks when you get jugg" specifically.
// THE ACTUAL MECHANISM NOW (v14.28, two halves): entry main() pins
// level.zombie_vars["player_base_health"] = 150 (so stock's own rebuild lands
// on our base), and max_hp_floor() — the ONE owner of the minimum-max formula,
// used by the spawn grant and the body-loop maintain — counts an ACTIVE jugg,
// so the floor for a jugg holder is 250 + 10xVIT and any stock clobber is
// repaired within a second (raise-only, no free heal).
// THE SHARED 5-TIER DIMINISHING LADDER (v16, 2026-09-01 — user gave the same
// shape for RECOVERY, BACK ARMOR and VITALITY: "10%, 18%, 24%, 28%, 32%").
// Increments 10, +8, +6, +4, +4 — front-loaded, so the first card is the big
// one and the last two are top-ups. Same design language as the v15 move-speed
// ladder (5,4,3,3,3) but NOT a multiple of it; they are separate tables on
// purpose and must not be merged.
//
// UNIT-AGNOSTIC BY DESIGN. It returns a plain NUMBER and each caller decides
// what it means: RECOVERY and BACK ARMOR divide by 100 for a percentage,
// VITALITY uses it as FLAT HP (user's explicit call — "Flat HP", so Lv5 is
// +32 HP, not +32%). Do not bake a /100 in here.
//
// ⚠️ THE CARD ART FOR ALL THREE IS DELIBERATELY GENERIC (v16 doctrine, user:
// "lets make the prompts give generic assets so if we ever need to tweak
// numbers we dont need new assets"). A stage table cannot be printed as one
// honest number per rarity, and re-baking three cards every time a value moves
// is what docs/33 has recorded going wrong five times. The exact figure lives
// in the pause menu, which is server-fed and always current.
#define TOD_LADDER5_L1  10
#define TOD_LADDER5_L2  18
#define TOD_LADDER5_L3  24
#define TOD_LADDER5_L4  28
#define TOD_LADDER5_L5  32
#define TOD_UPG_VITALITY_HP_PER_LVL 10   // ⚠️ SUPERSEDED by ladder5() — kept only for the v14.28 stock-reboot comment that cites it by name
// RECOVERY (HEAVY, v14.11 — user 2026-08-30: "start regen faster 10% faster
// at each tier and goes to 3 tiers at 30% faster at max. A tier"). Stock zm
// regen is SCRIPT-side (_zm_playerhealth.gsc::playerHealthRegen): above the
// 20% healthOverlayCutoff it waits playerHealth_RegularRegenDelay (2400ms)
// after the last hit and then SNAPS to full; below the cutoff it waits
// longRegenTime (5000ms) and then climbs 0.1 ratio/frame. The delay var is
// LEVEL-GLOBAL, so it cannot be set per player — instead recovery_loop()
// EMULATES the stock outcome at the REDUCED delay: after
// stock_delay x (1 - 0.10 x Lv) without damage it delivers exactly what stock
// would deliver at the full delay (snap above the cutoff, the 0.2/tick climb
// below it). Stock's own loop still runs untouched and simply finds the
// player already healed. Both stock numbers are read LIVE off the level vars
// (fallbacks mirror the stock inits) so a stock retune propagates.
#define TOD_UPG_RECOV_PCT_PER_LVL 0.10
#define TOD_RECOV_TICK_SECS       0.1     // emulation cadence; 0.1s error max on the poll-stamp lane
#define TOD_RECOV_CLIMB_PER_TICK  0.2     // veryHurt band: ratio climbed per tick (stock: 0.1/50ms frame)
// SECOND WIND (MP7, skirmisher T3 unique — user 2026-08-23: "you heal as you
// run. 5% health per second. starts at 1% up to level5 at 5%"). 1% of MAX HP
// per level per second WHILE SPRINTING, 5 levels => Lv1 1%/s .. Lv5 5%/s.
// Against TOD_UPG_BASE_HP 150 that is 1.5 HP/s at Lv1 and 7.5 HP/s at Lv5, so a
// full heal from near-death takes ~20s of sustained sprinting at cap.
// Gated on IsSprinting() rather than mere movement, which makes it a real
// decision: BO3 will not let you fire while sprinting, so healing costs you all
// your damage output. That is the trade — disengage and recover, or stand and
// shoot. It is also uncopyable by the other classes: SECOND WIND is the MP7's
// own T3 unique, so no other class can train it at all.
#define TOD_UPG_SECONDWIND_PER_LVL 0.01   // DEAD 2026-10-05 (W2E): SECOND WIND retired whole; the tuning record

// MOMENTUM REMOVED 2026-08-30, v14.11 (user: "Remove momentum upgrade").
// Was the MP5's unique (a skirmisher class domain until the 2026-08-24
// binding): up to +5%/Lv damage scaled linearly across 120..190 u/s 2D speed.
// Defines stay as the tuning record ("echo" pattern); the add_domain call,
// the set_guns binding and the unique_damage_mult hook are gone. Its niche —
// damage for moving — is RUN AND GUN's second half now (below), and the MP5
// inherits SECOND WIND off the MP7 in the same pass.
#define TOD_UPG_MOMENTUM_PER_LVL   0.05  // DEAD
#define TOD_MOMENTUM_MIN_SPEED     120   // DEAD — u/s 2D, no bonus below
#define TOD_MOMENTUM_FULL_SPEED    190   // DEAD — u/s 2D, full bonus at/above
// RUN AND GUN's DAMAGE HALF (v14.11 — user 2026-08-30: "Run and gun should
// increase damage while running too. At the same rates"; v16.50, user
// 2026-09-02: "make run and gun 5 tiers. 16% 28% 38% 46% 52%"). Flat while
// moving, not MOMENTUM's ramp — the ammo half is flat, so the card stays ONE
// condition with ONE ladder. The ladder is a STAGE TABLE (steps 12/10/8/6,
// diminishing), read through rng_dmg_add() — never a base + per-level rate.
// The percentages and the movement test are LOCKSTEP MIRRORS of
// _tod_runandgun.gsc (TOD_RNG_PCT_L1..L5 = these x100, TOD_RNG_MIN_SPEED 120,
// and is_running(): IsSprinting() OR 2D speed >= MIN_SPEED) — that module
// cannot be #used from here (it imports us; the KB cycle rule), so the numbers
// are duplicated on purpose. Change one file and you MUST change the other
// (and DETAIL[23] in tod_upgrade.lua), or the card's two halves trigger on
// different definitions of "moving" or pay different ladders.
// DEAD 2026-10-05 (W2E): RUN AND GUN retired whole; TOD_UPG_RNG_* stay as the tuning record.
#define TOD_UPG_RNG_DMG_L1         0.16
#define TOD_UPG_RNG_DMG_L2         0.28
#define TOD_UPG_RNG_DMG_L3         0.38
#define TOD_UPG_RNG_DMG_L4         0.46
#define TOD_UPG_RNG_DMG_L5         0.52
#define TOD_UPG_RNG_MIN_SPEED      120   // u/s 2D — LOCKSTEP with TOD_RNG_MIN_SPEED
#define TOD_UPG_LEECH_PER_LVL   4      // +4 HP per class-gun kill per level (SLASHER)
// SCAVENGER feedback throttle (user 2026-08-22 asked for a sound).
// The refund is at most ONE round per shot (v9.10), but a Lv6 assault on a
// dense train can still cross its 2-kill threshold shot after shot — only
// the SOUND is throttled to one per this many ms, per player; ammo always
// lands.
//
// MUST STAY ABOVE THE CLIP LENGTH. The wav is the user's gun-reload sample
// (tod\sfx\tod_scavenger.wav): the clink itself is ~370ms and the file is
// cut at 500ms (v9.10 — the old 945ms file carried 575ms of dead silence,
// which is what forced the old 1100ms gap). At a gap BELOW the clip length
// it retriggered ON TOP OF ITSELF and smeared. If the clip is ever swapped,
// re-check this.
#define TOD_SCAV_SND_GAP_MS     600
// BULLET FEED (user 2026-08-21): ONE round per tick, always — the LEVEL buys
// RATE, not amount. Lv1 every 3.0s ... Lv10 every 0.75s (floored).
// v8.9 buff (user 2026-08-21: "starts at 2s then improves linearly all the
// way to 0.4s"): Lv1 = 2.0s/round, linear over the 10 levels to 0.4s at Lv10.
// v14.14 2x BUFF (user 2026-08-30: "can you 2x buff bullet feed upgrade"). All
// three constants HALVED, so throughput exactly doubles at EVERY level — the
// amount is still ONE round per tick (that is what reads as a belt feeding);
// only the RATE moved, which is the domain's whole design. Ladder is now
// Lv1 1.0s/round -> Lv10 0.2s/round (was 2.0 -> 0.4).
// KEEP THESE THREE IN LOCKSTEP: base - step*(maxLv-1) must land ON min, or the
// floor clamps early and the top levels stop paying. 1.0 - 0.0889*9 = 0.1999.
#define TOD_UPG_FEED_BASE_SECS  1.0    // seconds per round at Lv 1... (3.0 -> 2.0 -> 1.0)
#define TOD_UPG_FEED_STEP_SECS  0.0889 // ...minus this per level (1.0 -> 0.2 across 9 steps)
#define TOD_UPG_FEED_MIN_SECS   0.2    // floor — Lv10 lands here (never zero: would spin the catch-up loop)
#define TOD_UPG_BASE_HP         150    // base player max HP (user 2026-08-20; stock 100; jugg stacks additively on top)
#define TOD_VITALITY_HP_LV      10     // RECORD: VITALITY was flat +10 / Lv (2026-09-27, 6 levels); since 2026-09-28 it is vitality_hp()'s falling ladder
// CLASS TIERS (docs/25, user 2026-08-22): once the class gun is PaP'd AND the
// player has climbed high enough (the FLOOR GATE below), this percent of card
// deals carry a TIER card (the right slot; never auto-locked).
// Dev flag -> 100 (tier_card_pct) so the whole promotion flow is testable in
// one session. LUCK does NOT move it (user).
// v9.42 (user 2026-08-23: "Increase this to 20%. 10% was too low") — 10 -> 20.
#define TOD_TIER_CARD_PCT       20
// ---- THE CLASS TIER FLOOR GATE (v14.35, user 2026-08-30) ------------------
// "You must also reach floor 10 to get 2nd tier class upgrade and floor 20 for
// 3rd. I dont want players able to be tier 2 or 3 before even opening the first
// door to the tower."
//
// WHY IT WAS POSSIBLE AT ALL: the PaP requirement below was doing this job by
// accident, because the first Pack-a-Punch you can reach while climbing IS the
// floor-10 breather vendor (the crown machine sits above all 50 laps). The
// FREE-PAP POWERUP is the hole — it sets player.tod_pap_owned wherever it
// drops, so one lucky drop in the base arena made a tier-1 player eligible for
// the promotion without touching a door. This gate closes that, and for the
// normal route it costs nothing: floors 10 and 30 are the FIRST and THIRD
// breathers, which is where the PaP machines are anyway (T3 was the second
// breather, floor 20, until 2026-09-02 — user: "move tier 3 upgrade to floor
// 30"; every number below moved with it, incl. the Lua floor->tier table).
//
// Numbers, not a formula, because they are the user's numbers. A tier past 3
// (none exists — tod_classes::tier_max() is 3) keeps the ladder's own spacing
// rather than arriving ungated; see tier_floor_req().
#define TOD_TIER2_FLOOR         10
#define TOD_TIER3_FLOOR         30   // 2026-09-02 (user): T3 moved 20 -> 30; docs/72 re-baked the badge
// ---- CLASS TIER UNIQUES (docs/25 §9) — one per tier gun, script-side -----
// ADRENALINE (domain 25, skirmisher — bound to the MP7, NOT the MP5; the old
// comments here said MP5 and were wrong from 2026-08-24, when set_guns moved it).
//
// REWORKED v16 (2026-09-01, user: "5 tiers 3% each tier and it gives a speed
// boost when you get multi kills. It has a cool down as well. Each tier lowers
// the cool down a bit. 10s, 9s, 8s, 7s, 6s and it lasts for 3s everytime it
// triggers.")
//
// IT IS NO LONGER A STACKING SYSTEM. It was: every kill added a stack, up to 3,
// inside a rolling 4s window, worth +4/6/8% per stack. It is now a single
// cooldown-gated PROC: a multi-kill fires one fixed burst, then the domain is
// locked out for the cooldown. TOD_ADREN_STACKS and self.tod_adren_stacks are
// DELETED rather than stubbed to 1 — this file's own doctrine, stated twice
// (the retired MOBILITY term and the removed class_hs_scale): a term that can
// only ever be one value is how the next reader loses an hour.
//
// THE PERCENT IS POINTS OF SCALE, NOT A PERCENTAGE OF THE CLASS BASE. Move
// speed has been an ADDITIVE sum since v15, so "+3%/tier" means +0.03 of scale
// per tier, identical for every class. Writing it as 0.03 * class_speed_base()
// would quietly pay the skirmisher 0.033 and re-open the gap v15 closed.
#define TOD_ADREN_PCT_PER_LV    0.03   // +3% of SCALE per tier -> Lv5 = +0.15
// v17.67 (2026-09-05, user: "buff adrenaline so that it does extra damage
// while active as well. Same levels as the speed % increases"): the SAME
// adren_bonus() value is also added to the bullet-damage sum in
// unique_damage_mult while the burst is live -> +3%/tier damage, Lv5 = +15%,
// DARK = +25%.
//
// v17.85 (2026-09-05, user: "for adrenaline we need to add healing on trigger.
// It will match the percentage"): a THIRD lane -- the proc heals a percentage
// OF MAX HEALTH, once, at the moment it fires.
//
// AT DOUBLE THE OTHER TWO, same session, once it had been seen written down:
// "the health gain you get on trigger should be double the percentage. So 50%
// health gain one time on adrenaline trigger" -- then, on being shown the
// ladder, "thats for dark but of course its dynamic depending on % for that
// tier". So the heal is 2x adren_bonus() at every level:
//
//   Lv1 6%   Lv2 12%   Lv3 18%   Lv4 24%   Lv5 30%   DARK 50%
//
// THE MULTIPLIER IS A DEFINE, NOT A 2 IN THE EXPRESSION, and this file already
// said why before the ask arrived: one function feeds all three lanes so they
// cannot drift, and the moment one lane needs its own number it gets its own
// NAME rather than a second copy of the ladder. TOD_ADREN_HEAL_MULT is that
// name. Retune the percent and all three still move together; retune this and
// only the heal does.
//
// THE HEAL IS A PERCENTAGE, THE OTHER TWO ARE POINTS. Same source number,
// different units, and that is not sloppiness: move speed is points of additive
// scale (see the note below), bullet damage is a multiplier addend, and the
// heal is read against self.maxhealth -- so it follows Juggernog and VITALITY
// without anything here knowing they exist.
//
// AND IT IS ONE-SHOT, NOT A HEAL-TANK. A 30% top-up sounds enormous next to
// LEECH's flat 25 HP per blade kill, but LEECH pays on EVERY kill while this
// pays once per proc behind a 3-kill trigger AND a 12-20 s cooldown, i.e. at
// best once every 12 s. Read those two together before judging the number.
#define TOD_ADREN_HEAL_MULT     2.0    // the heal is DOUBLE the speed/damage percent (user 2026-09-05)
#define TOD_ADREN_MS            3000   // the burst lasts 3s, every time it fires
// MULTI-KILL = N kills inside a rolling window. THE DEFINITION IS A DESIGN
// CHOICE, NOT A DETAIL, so it is written down here.
//
// WHY A ROLLING WINDOW AND NOT "SAME SERVER FRAME": the death callback fires
// once per zombie, so a penetration or shotgun kill delivers several callbacks
// sharing one GetTime(). SCAVENGER already exploits that — to SUPPRESS extra
// payouts (its tod_scav_pay_ms frame stamp). Copying that shape here would
// invert its purpose and, worse, would make this domain nearly unproccable for
// the class that owns it: same-frame multi-kills come from PENETRATION (heavy),
// CLEAVE and THOR (slasher) and IMPACT (assault). A skirmisher holding the MP7
// has almost no way to produce one by shooting. A rolling window covers the
// same-frame case for free — kills sharing a frame share the timestamp — and
// also rewards what a player actually means by a multi-kill.
#define TOD_ADREN_MK_NEED       3      // kills required... (user: "3 kills within 1.5s")
#define TOD_ADREN_MK_WINDOW_MS  1500   // ...inside this window
// COOLDOWN LADDER: 20/18/16/14/12s at Lv1..Lv5. DOUBLED from the first spec
// (10/9/8/7/6s) on 2026-09-01 — user: "lets double the delay on the retrigger.
// I dont want it to proc too often". Same shape as
// thor_cooldown_ms — MAX minus STEP per level, with a FLOOR so a future 6th
// level is safe by construction rather than by nobody adding one.
#define TOD_ADREN_CD_MAX_MS    20000
#define TOD_ADREN_CD_STEP_MS    1000   // 2026-09-28 (user: Adrenaline to Lv9): 20 s at Lv1 -> 12 s at Lv9, one second a level
#define TOD_ADREN_CD_MIN_MS    12000
// 3 synth heartbeats decaying, 1.42s, 2d/player-only.
// ⚠️ INAUDIBLE ON FIRST SHIP (user 2026-09-01: "on adrenaline trigger i cant hear
// the heartbeat"), and the cause was TWO COMPOUNDING ATTENUATIONS, neither of
// which is obviously wrong alone:
//   * the alias sat at vol 70 - the LOWEST row in tod_ui.csv, against 88-95 for
//     every other per-proc cue (tod_scavenger, tod_headshot_ding, tod_thor_zap)
//   * the wav peaked at -9.0 dBFS, from the trim pass that removed its lead-in
// Together ~11 dB under a comparable cue, i.e. masked by the player own gunfire.
// Fixed by raising BOTH: alias 70 -> 92, wav peak-normalised to -1.0 dBFS.
// The asset chain was never the problem - alias present, CSV in the .szc, wav in
// the .sabl, pointer set, call site reached. When a cue is "not playing", MEASURE
// THE LEVEL before re-checking the wiring.
#define TOD_ADREN_SFX          "tod_adren_pulse"
// KILL RELOAD (assault) — RETIRED 2026-09-01 (user: "Lets remove it. No one
// likes it"). Its three TOD_KILLRELOAD_KILLS_LV* defines (55/40/30 kills per
// free magazine), killreload_kills_needed() and the block in unique_on_kill
// went with it, on the IMPACT ROUNDS form — see the note at its old add_domain.
// IMPACT ROUNDS (assault, all three guns since v9.38). v9.45 (user 2026-08-23:
// "impact rounds can be 10 levels but each level needs to be nerfed. Smaller
// steps per level"): 3% PER LEVEL over TEN levels — 3/6/9 ... 30% of hits burst.
// The Lv10 ceiling is exactly the old Lv3 ceiling, so the card got no stronger;
// what changed is that reaching it costs ten levels instead of three and each
// individual level is a third of the proc rate it used to buy.
// SUPPRESSING FIRE NERF (user 2026-08-24: "nerf supressing fire to 12%, 24%,
// 36%"): was 25/40/55 (base .25 + .15/Lv), now a clean 12/24/36 — base AND step
// are both .12, so the ladder is linear instead of front-loaded. Three places
// carry these numbers as TEXT and all three moved with it: the add_domain
// description, tod_upgrade.lua DOMAIN[29].desc, and its DETAIL[29].val.
#define TOD_SUPPRESS_BASE       0.12   // SUPPRESSING FIRE (HK21): slow 12/24/36%...
#define TOD_SUPPRESS_PER_LV     0.12
#define TOD_SUPPRESS_MS         1500   // ...for 1.5s
#define TOD_GRINDER_PER         5      // MEAT GRINDER (Death Machine): one stack per 5 consecutive rounds
// (TOD_UPG_LUCK_CAP removed 2026-08-20 — rarity odds ride the 0..100% luck
// bar, see roll_rarity + _tod_luck.gsc.)

// LuiNotifyEvent REQUIRES its event string precached (stock does this for
// "zombie_notification") — without it the pause-menu owned-upgrades sync
// silently never fires and CoD.TodOwned stays empty (bug 2026-08-20).
#precache( "eventstring", "tod_upg_sync" );
#precache( "model", "p8_zm_crafting_table" );   // the dev CARD TEST bench (docs/187); packed by tod_partners.zpkg
// v14.35 — the CLASS TIER floor requirement for the deal about to be shown
// (0 = the floor is not what is stopping this player). Same zero-bit int lane;
// same precache trap, which is why it is here and not left implicit.
#precache( "eventstring", "tod_upg_tier_need" );
#precache( "eventstring", "tod_upg_class" );   // v16: the deal panel's CLASS badge (docs/59)
// v14.13 — the SURVIVES-PROMOTION bit rides INSIDE the max arg of the
// tod_upg_sync event: sync_max() adds this flag when THIS player's copy of
// the domain survives a tier card, and the Lua receiver strips it back off
// (m >= 100 -> safe, m -= 100). Packed rather than sent as a 4th int because
// no 4-arg LuiNotifyEvent exists anywhere in this tree — the 3-arg shape is
// the proven one (stock-API doctrine: never be the first caller of an
// unverified arity). Must stay ABOVE every real max (caps top out at 10).
#define TOD_SYNC_SAFE_FLAG 100
// DARK UPGRADES (v17.10): the SECOND bit packed into the same tod_upg_sync max
// arg, so the pause menu can print the dark value. 200 rather than another 100
// so the two are separable, and the Lua MUST strip this one FIRST — a row at
// 10 + 100 + 200 = 310 read safe-first would come out as safe + 210.
// Caps top out at 10, so 310 is the ceiling and the int stays small.
#define TOD_SYNC_DARK_FLAG 200
// DARK UPGRADES (v17.10): the sentinel written into the 4-bit todUpg<slot>L
// clientfield to mark a dealt card as DARK. Domain levels top out at 10, so
// 11..15 are unreachable as real values and 15 is unambiguous. This is why the
// feature costs ZERO clientfield bits against a pool already at 60 of its 61
// proven-booted bits — see the DARK UPGRADES block above set_no_dark(), and
// note the TIER card packs class+tier into this same field already.
// LOCKSTEP: tod_upgrade.lua reads the same 15 (DARK_L) to pick the dark card
// art. Change both or neither.
#define TOD_UPG_DARK_L 15
// Chance the SECOND slot is also a dark card, when the player has more than one
// maxed domain and the tier card is not using that slot. Was 35 under the
// 2026-09-03 rule ("possible to get both ... the only guarantee is that one
// must be"). **100 since v17.46** — user 2026-09-04: "in no situation where you
// are eligible for two dark upgrades should you only get one." An EMPTY right
// slot is filled regardless of this number (deal_dark), so this knob only
// decides whether a second dark card displaces a REGULAR card.
#define TOD_DARK_BOTH_PCT 100
// ---- DARK UPGRADE VALUES (user 2026-09-04; docs/92 THE NUMBERS is the record).
// Every one is an ADDITIVE step on top of the domain's MAXED value, never a
// replacement for it — a dark bit implies the domain is already at its cap.
#define TOD_DARK_DMG_ADD        0.50   // DAMAGE       +100% -> +150%
#define TOD_DARK_HS_ADD         0.25   // HEADSHOT      +60% ->  +85%  (cap was +50% until the 2026-09-08 12%/Lv x 5 pass; the dark STEP is unchanged)
#define TOD_DARK_BOSSDMG_ADD    0.20   // GIANT SLAYER  +60% ->  +80% (was +85, user 2026-09-05)
#define TOD_DARK_GUNSLINGER_ADD 0.30   // GUNSLINGER   +150% -> +180% (cut from +100 on the 2026-09-04 balance pass)
#define TOD_DARK_BOUNTY_ADD     0.50   // BOUNTY        +50% -> +100%
// LUCK: NO DARK STEP since 2026-09-05 (user: "Remove dark luck"). Was TOD_DARK_LUCK_ADD 0.50 (x1.50 -> x2.00).
#define TOD_DARK_DR_ADD         10     // DMG REDUCTION +10 percentage points on the class cap (25/30/34/40)
#define TOD_DARK_VITALITY_HP    18     // VITALITY     +32HP -> +50HP (was +57, user 2026-09-05)
#define TOD_DARK_LADDER5_ADD    13     // RECOVERY and BACK ARMOR: 32% -> 45%
#define TOD_DARK_LEECH_HP       25     // LEECH        FLAT 25HP per blade kill, REPLACES the ladder value (was 10+8, user 2026-09-05)
#define TOD_DARK_SPEED_ADD      0.15   // SPRINT        +33% ->  +48% of move scale (cut 5 points, user 2026-09-04)
#define TOD_DARK_MARCH_ADD      0.17   // FORCED MARCH  +18% ->  +35% (was +38, user 2026-09-05)
#define TOD_DARK_ADREN_ADD      0.10   // ADRENALINE    +27% ->  +37% burst (Lv9)
// DEAD 2026-10-05 (W2E): RUN AND GUN and SCAVENGER retired whole; the next two stay as the tuning record.
#define TOD_DARK_RNG_ADD        0.48   // RUN AND GUN    52% ->  100% (was 77, user 2026-09-05) -- LOCKSTEP: _tod_runandgun.gsc adds the integer 48
#define TOD_DARK_BULLETFEED_RPS 7.0    // BULLET FEED   5.0/s ->  7.0/s
#define TOD_DARK_ATHLETE_LEVELS 2      // ATHLETE      computes as level 7
#define TOD_DARK_SCAV_MULT      0.60   // SCAVENGER    -40% of the kills you currently need (user: "40% reduction of what you are at")
// RIOT SHIELD: 700 HP / 1:30 — defined in _tod_riotshield.gsc beside its own
// ladder (TOD_DARK_SHIELD_HP / TOD_DARK_SHIELD_RECHARGE_SECS), not here.
// TRAILBLAZER: absolute values — 10%/s burn, a 50% slow, 100u radius. LIFE IS
// DELIBERATELY NOT RAISED (the node cap binds first, and the trail is meant to
// be attrition rather than a weapon). Units match the helpers they replace:
// trail_pct is an INTEGER PERCENT, trail_slow_mult is a playback MULTIPLIER.
#define TOD_DARK_TRAIL_PCT        10     // was 6 at Lv5
#define TOD_DARK_TRAIL_SLOW_MULT  0.625  // a 37.5% slow; Lv5 base is 0.745 = 25.5%. MOVES WITH THE BASE LADDER, ALWAYS (v18.6 took both down 25%, user 2026-09-07: "trail blazer needs a nerf on slowing down enemies ... 25%"; v17.84 doubled both, and the note it left is the reason this one is not left behind: a dark card that does not track the base is either a downgrade or an outlier).
#define TOD_DARK_TRAIL_RADIUS     100    // was 88 at Lv5
// TRAILBLAZER dark also BURNS BOSSES (user 2026-09-05: "Mega Trail Blaze impacts
// bosses"). DEAD 2026-10-05 (W2E): TRAILBLAZER retired whole with its lane; the three
// TOD_DARK_TRAIL_* above stay as the tuning record.
// PERK SLOTS base cap — RETIRED 2026-09-27 with the domain (user: "no perk
// limit on this map"); zm_tod2_cybercity.gsc owns the limit (16, above the roster).
#precache( "model", "tod_heavenly_altar" );   // shared cyber altar: base, four breathers, crown

#namespace tod_upgrades;

function init()
{
	level.tod_upgrade_pause = false;

	// PERSONAL UPGRADE STATION (user 2026-08-20): buy a solo upgrade at the
	// base — cost 2000 +250 per purchase (PER PLAYER), 15s timer, scheduled
	// rounds override + the same cards re-present. CO-OP has no world pause
	// (that is the risk); SOLO freezes the world like a round event as of
	// v16.84 — see station_freeze_wanted for why the risk model was always a
	// co-op argument.
	level thread station_spawn();
	level thread dev_card_test_spawn();   // docs/187: DEV ONLY - the crown's CARD TEST bench

	register_domains();

	// Damage + fire-rate + headshot ride the actor damage chain (read-modify;
	// returns -1 when not ours — the KB chain contract).
	zm::register_actor_damage_callback( &upgrade_damage_cb );

	// Bounty/reserve/leech ride the per-zombie death callback (KB: the REAL
	// death hook — callback::on_ai_killed is register-only, never dispatched).
	zm_spawner::register_zombie_death_event_callback( &on_class_gun_kill );

	// Score-popup BOUNTY preview, exposed to the vendored Aetherium HUD as a
	// LEVEL FUNCTION POINTER rather than a #using — the same cycle-dodge the
	// mechz melee hook uses (level.tod_player_mitigations_fn). The kit must
	// never import a tod module.
	level.tod_bounty_preview_fn = &bounty_preview;
	// Use the stock public hook. A usermap copy of _zm_score did not replace
	// the runtime's stock script, so adding public functions to it boot-fataled.
	zm_score::register_score_event( "death", &zombie_death_score );
	// BOUNTY as a flat multiplier on a lump-sum payout (v14.5) — same pointer
	// pattern, first consumer _tod_bosses::grant_elite_reward (the killer-only
	// elite 500). See bounty_mult below.
	level.tod_bounty_mult_fn = &bounty_mult;

	// LMG SPRINT (domain 42, v15 item 24): the same pointer pattern again, for
	// the same reason. _tod_uniques.gsc owns the 20 Hz sprint poll and imports
	// NO tod module by design — that is precisely what lets THIS file read its
	// fields without a cycle — so it cannot #using its way to apply_move_speed.
	// It calls through here instead, on the frame the 1.5 s latch flips.
	//
	// WHY NOT JUST LET THE 1 s BODY TICK NOTICE: because a movement boost that
	// arrives up to a second after it is earned reads as broken, and the latch
	// it is watching flips in ~0.1 s. The pointer costs nothing and makes the
	// boost land on the arming frame.
	level.tod_apply_speed_fn = &apply_move_speed;
	// ADRENALINE proc cue (v16) — same pointer pattern; the kill hook calls it
	// through this so the sound and the speed land on the same frame.
	level.tod_adren_fx_fn = &adren_fx;

	// PERK SLOTS — RETIRED 2026-09-27: no cap and no per-player hook. The
	// limit is zm_tod2_cybercity.gsc's constant, above the whole roster.

	callback::on_spawned( &player_upgrade_setup );

	// MAX AMMO also tops the CLIP (user 2026-08-21). Lives in _tod_powerups
	// but is threaded here because this module already owns the spawn hook.
	callback::on_spawned( &tod_powerups::max_ammo_clip_watch );

	level thread event_scheduler();
}

// Order here = the domain ids the Lua DOMAIN table mirrors (1-based). APPEND
// ONLY — reordering desyncs every card the client renders.
// class_key undefined = SHARED (every class rolls it); otherwise only that
// class sees the card. max = the domain's level cap (depths vary by design:
// deep 10-level grinds vs short punchy ladders — user 2026-08-19).
// Gun-bound domains scope themselves to the CURRENT class gun automatically
// (is_class_primary); body domains (sprint/mobility/health/regen) stay
// trained on the PLAYER even after a class switch.
// v4 matrix (user 2026-08-19). Ids 1..14 mirrored in _tod_upgrade_ui.gsc
// domain_id AND tod_upgrade.lua DOMAIN — keep all three in lockstep.
// PENDING (twin-swap phase, NOT registered so no dead cards): FIRE RATE +
// HANDLING (skirmisher), RECOIL (assault), KNIFE SPEED (slasher).
function register_domains()
{
	level.tod_domains = [];
	// TIERS (v8.9): the last arg. S = wins the run on its own (universal
	// multipliers, effective-HP doublers, the melee nukes, and LUCK — which
	// compounds into every future roll). A = strong but conditional or
	// capped low. B = economy / quality-of-life.
	//
	// -- shared core (all classes) --
	// add_domain( "damage", "DAMAGE", "+10% damage / Lv", 10 ) — RETIRED 2026-09-27 (user: "remove the damage card
	// altogether ... each class will have its own ... core primary ... upgrade"). Each class's CORE WEAPON
	// card (deadeye / buckshot / heavyhands / soulbeam) carries the damage now, on its own primary only.
	// DR CAPS AT 5 FOR EVERY CLASS (v15, 2026-08-31 — user: "Damage Reduction
	// needs a nerf"). It was the strongest survivability item in the map by a
	// wide margin: -5%/Lv x 10 = x2.00 effective HP, worth more than a second
	// Juggernog, and unlike Jugg it is class-agnostic, promotion-proof (scope
	// "class", below) and death-proof. Halving the CEILING rather than cutting
	// the per-level step was the deliberate choice — the card art prints a
	// per-card increment ("-5% / -10% / -15%") and the pips come from the server,
	// so -5%/Lv stays literally true at every rarity and NOTHING NEEDS RE-BAKING.
	// Cutting the step to -4% or -3% would have been three card re-bakes and a
	// full build for the same effect.
	//
	// WHAT WENT AWAY WITH IT: the bonus_class/bonus_max pair. Slasher (v14.11)
	// and skirmisher (v14.33) were each capped at 5 individually, using
	// bonus_class/bonus_max as a per-class OVERRIDE rather than a bonus
	// (domain_max() returns bonus_max for the named class and has never required
	// it to be higher — SCAVENGER still uses that lane UPWARD, so the mechanism
	// is alive and this is not the place to learn it from). With 5 now universal
	// those two args said nothing, so they are gone rather than left as a
	// no-op that reads like a live carve-out.
	// v17.3 — MAX IS 10 (the ceiling) BUT NO CLASS REACHES IT EXCEPT THE HEAVY.
	// The per-class caps are declared in set_class_max below: 3 / 5 / 7 / 10.
	// The desc carries no ladder any more BECAUSE the ladder now ends in a
	// different place for every class — the pause row prints the player's own.
	add_domain( "dr",         "DMG REDUCTION", "take less damage, always on: 5% at Lv1 up to 22% at Lv9", 9, undefined, TOD_TIER_A );   // 2026-09-28 (user): 9 levels for EVERY class, +5/3/2/2/2/2/2/2/2 (no class caps)   // v16: flat 5%/Lv -> diminishing ladder, and S -> A band (user: "move damage reduction to A tier")
	add_domain( "bounty",     "BOUNTY",      "more points per kill: +30% at Lv1 up to +100% at Lv9", 9, undefined, TOD_TIER_S );   // 2026-09-28 (user): 9 levels, log, +100% at Lv9 (bounty_rate)
	add_domain( "luck",       "LUCK",        "your luck bar fills faster: +30% at Lv1 up to +100% at Lv9", 9, undefined, TOD_TIER_A );   // 2026-09-28 (user): 9 levels, log, +100% at Lv9 (_tod_luck::add)
	// PERK SLOTS (id 40) — RETIRED 2026-09-03 (v16.80, user: "remove the perk
	// limit so revert back how it use to be"). v14.56 (2026-08-31) capped perks
	// at stock's 4 and sold the way past it as this universal A-band card
	// (+1 slot / Lv, max 5 = the 9-machine roster). It shipped without a change
	// note, and the Workshop thread's verdict was blunt (Bobby, 09-01..09-03:
	// "wasting these awesome upgrades on a DAMN PERK SLOT"): at 50 of ~650-780
	// per-class draw weight it surfaced about once in seven deals, so the cap
	// read as a hard 4 and every offer of it was a card spent on nothing. The
	// cap is gone (zm_tod2_cybercity.gsc sets the limit above the roster), so
	// the domain has nothing to do; the id stays mapped in domain_id() and the
	// Lua tables (key-keyed, same form as 27/28/32/34), the r40 pause plate
	// stays zoned, the three card images are unzoned.
	// add_domain( "perkslots", ... ) — RETIRED AGAIN 2026-09-27 (user: "remove the
	// perk slot upgrade as well. There will be no perk limit on this map"). Id 40
	// stays mapped in domain_id() and the Lua tables; its three cards are unzoned.
	// -- SKIRMISHER + SLASHER --
	// Move speed and nothing else since 2026-08-26 — the Lv5 TIRELESS rider was
	// removed (see the block comment where TOD_UPG_TIRELESS_SECS used to live).
	// Both classes that roll SPRINT now get exactly the same thing from it.
	// RETIRED 2026-09-26 (user: "warrior from the sprinting upgrade as well. And sprint should also be removed for necromancer") - the Archer and Breacher had already left it, so no class holds SPRINT and the domain is retired whole (id 5 stays mapped; speed lanes read level 0). Was:
	add_domain( "sprint",     "SPRINT",      "sprint faster / Lv",                   9, array( "assault" ), TOD_TIER_A );   // 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"): the ARCHER's card ("Add Sprint ability for this class"; user picked "faster sprint per level"). The shared speed ladder, counted ONLY while sprinting (apply_move_speed; _tod_class_cards latches tod_sprint_hot). Was:
	// add_domain( "sprint",     "SPRINT",      "move faster on foot / Lv",            10, array( "necromancer", "slasher" ), TOD_TIER_S );   // v16: A -> S band (user: "sprint needs to be moved to S tier"). Desc carries NO number since v15 - the ladder is 5/4/3/3/3... via speed_pct_for_level
	// SPRINT FIRE (user 2026-08-21): promoted from a skirmisher INNATE to an
	// earned card — but still SKIRMISHER-ONLY (user, same day: "sprint fire is
	// only for smg class upgrades"). So it stays the SMG's identity; you just
	// have to earn it now instead of starting with it.
	// BINARY — the engine specialty is on/off, so max 1 (a SUPER/ULTIMATE roll
	// still just grants the single level).
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-27 (CLASS PASS 2: sprint fire is the ARCHER's passive, apply_sprint_fire), dealt to no class. Id 21 stays mapped (append-only). Was: add_domain( "sprintfire", "SPRINT FIRE", "fire your weapon while sprinting",     1, array( "parked" ), TOD_TIER_A );
	// SPRINT ARMOR (user 2026-08-23): -5%/Lv damage taken WHILE SPRINTING, 5
	// levels — the mobile class gets tougher in motion, never standing still.
	// Tier A: strong but conditional. Scope "class" below (it is damage
	// resistance, the one thing the user said survives a tier-up). The hook
	// lives in _tod_bosses' two damage lanes via sprint_armor_mult();
	// domain_id 32.
	// SKIRMISHER-ONLY since v14.11 (user 2026-08-30: "Remove sprint armor on
	// slasher" — with the DR cap above, the slasher's whole defensive stack is
	// deliberately shallower: max mitigation falls from x0.375 to x0.75).
	// SPRINT ARMOR REMOVED 2026-08-31 (user: "Retire sprint armor entirely").
	// Was: add_domain( "sprintarmor", "SPRINT ARMOR",
	//        "-5% damage taken while sprinting / Lv",
	//        5, array( "skirmisher" ), TOD_TIER_A );
	// Id 32 stays mapped in domain_id() and the Lua tables (key-keyed). Its
	// set_scope("sprintarmor","class") is gone with it. CARD_SLUG[32] and the
	// three i_tod_card_sprint_armor_* zone lines are removed on the CHAIN LUNGE
	// form; the PNGs stay in source_data.
	// sprint_armor_mult() SURVIVES as a permanent 1.0 — see its header. It is
	// called from two _tod_bosses damage lanes, and deleting it would mean
	// editing that file's damage chain on the eve of a publish build to remove a
	// call that is already a no-op. Not worth the risk; the header says so.
	// -- ASSAULT signatures --
	// RETIRED 2026-09-26 (user: Archer card cut, "shouldn't even be in the game"). Id 6 stays mapped (append-only); get_level returns 0 so the damage lanes that read it go inert. Was: add_domain( "headshot",   "HEADSHOT",    "+12% headshot damage / Lv",            5, array( "assault" ), TOD_TIER_A );   // v9.45 nerf 4%->3%; RESTORED to 4% 2026-08-26; 4%->5% 2026-08-30 (user: assault buff); 5%->12% AND max 10->5 on 2026-09-08 (user: "change headshot upgrade to 12% per tier and only 5 tiers") — cap +50% -> +60%, but the domain now finishes in five picks. THE MAX LIVES HERE, the rate lives on TOD_UPG_HS_PER_LVL: move both or the card offers a level the ladder does not price
	// MAG SIZE = REAL twin variants now (user 2026-08-20: "no bottomless —
	// directly impact the gun's mag size"); 3 levels by the gun-data rule.
	// CLASS KEYS widened to the SKIRMISHER (review 2026-08-22): domain_available
	// is an AND of gun_keys and class_keys, so "assault"-only left the MP7's
	// m-ladder (T3 skirmisher) unreachable. gun_keys (set below) is what keeps
	// it off the MSMC/MP5 — every ASSAULT gun carries an m-ladder now (user
	// 2026-08-23), only the skirmisher half is partial.
	// RETIRED 2026-09-25 (user: the Archer "shouldn't even be" offered this; its bows have one form now). Id stays mapped (append-only). Was: add_domain( "magsize",    "MAG SIZE",    "real mag +20/+40/+60%",                3, array( "assault" ), TOD_TIER_S );   // v9.44: skirmisher dropped (user: "Magsize we can remove from class"); +30 -> +20%/Lv 2026-09-01 (user: "mag size needs a nerf") — MAG_STEP in gen_tod_twins.js is the truth; this string, the Lua rows and the card art are its mirrors. BAND A -> S 2026-09-02 (user: "We need to move mag size upgrade to s tier"): weight 50 -> 20 and the SUPER/ULTIMATE slice x0.75 -> x0.50, same shape as SPRINT's v16 move. The LADDER IS UNTOUCHED, so no card re-bake — band is draw odds only, it is never drawn
	// GIANT SLAYER (v9.45, user 2026-08-23) — the assault class's answer to the
	// two things it cannot out-DPS with headshots: the Panzer and the Rogue
	// Protector wave. +8%/Lv against anything carrying the boss/elite triad,
	// five levels, so a maxed card is +40% on the only enemies with real HP.
	// Tier A, not S: it is worth nothing at all on the horde, which is the
	// literal definition of the A band ("strong but conditional").
	// Applied in BOTH boss-damage lanes — see boss_damage_bonus().
	// RETIRED 2026-09-26 (user: Archer card cut). Id 35 stays mapped. Was: add_domain( "bossdmg",    "GIANT SLAYER", "+12% damage to bosses and elites / Lv",  5, array( "assault" ), TOD_TIER_A );   // 3% -> 4% 2026-08-26; 4% -> 5% 2026-08-30 (user: assault buff); 5% -> 8% 2026-08-31; 8% -> 15% 2026-08-31 v15 (user: "boss damage should be 15% instead of 8%") = +75%; 15% -> 12% 2026-09-02 v16.50 (user: "nerf giant slayer to 12% each tier") = +60% at the Lv5 cap. Card art carries the number: re-bake owed per retune (docs/77)
	// BACK ARMOR (v9.45, user 2026-08-23) — the slow class gets the defence
	// the fast ones have. SPRINT ARMOR pays you for outrunning the horde; this
	// pays the class that cannot, for the hits it takes precisely because it
	// cannot turn around fast enough. -10%/Lv from a 140-degree rear arc, 3
	// levels. Scope "class" below — it is damage resistance, the one family
	// the user's tier rule says survives a promotion (with DR and SPRINT ARMOR).
	// HEAVY-ONLY since v14.11 (user 2026-08-30: "Remove back armor upgrade
	// from assault class"). The assault keeps no rear-arc defence — its
	// mitigation stack is DR alone now, which also un-does the "both slow
	// classes" symmetry above by design.
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "backarmor",  "BACK ARMOR",  "take less damage from behind",            5, array( "heavy" ), TOD_TIER_A );   // v16: max 3 -> 5, ladder5() 10/18/24/28/32%
	// RESERVE (user 2026-08-22): the ammo-back-on-kills mechanic STAYS as-is
	// (a real capacity twin would blow the ~230-twin boot ceiling — see the
	// CHANGELOG v9.1 hold). Opened from assault-only to EVERY GUN CLASS at
	// max 5, with ASSAULT alone reaching 6 — the first per-class cap on this
	// map, see add_domain's bonus_class/bonus_max.
	// Slasher excluded: its primary is a knife with no reserve to refund.
	// DISPLAY NAME "SCAVENGER" (user 2026-08-22: "Reserve doesn't make sense").
	// It never increased your reserve CAPACITY — it refunds ammo off kills, so
	// the old name promised the wrong thing (and collided with the S-tier
	// capacity upgrade that got held on the twin ceiling). INTERNAL KEY STAYS
	// "reserve" on purpose: domain_id 8, CARD_SLUG[8] and every existing image
	// filename key off it, so a rename here costs zero wiring.
	// v18.88 rate (kills per round): a round every 2.8 / 2.3 / 2 / 1.8 / 1.6
	// primary kills, the assault-only Lv6 capstone every 1.4. Two moves the
	// same day off the v16.42 ladder (4 / 3 / 2.4 / 2 / 1.8 / 1.6): v18.86
	// raised the first three rungs only (user: Lv1 was "almost not
	// noticeable"), then v18.88 took another 0.2 kills off EVERY rung
	// ("Lets shift all by another 0.2"), moving the ceiling with them —
	// TOD_SCAV_KILLS10_* (tenths), read by scav_kills10. (v16.40 20/30/38/44/48/
	// 52 per 100 kills and v16.41 25/35/43/49/53/57 each lasted one build;
	// 2026-08-26 → v16.39 it was ONE round per 5 / 4 / 3 / 2 / 1 kills and 3
	// per 2 at the capstone — an accelerating ladder.)
	// The payout is CLASS PRIMARY ONLY since 2026-08-26; a sidearm kill pays
	// nothing and does not even feed the bank.
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): SCAVENGER, parked since 2026-09-26 (the Breacher and the Archer both left it), dealt to no class. Id 8 stays mapped (append-only). Was: add_domain( "reserve",    "SCAVENGER",   "primary kills bank ammo: a round per 2.8 / 2.3 / 2 / 1.8 / 1.6 kills", 5, array( "parked" ), TOD_TIER_B );
	// -- HEAVY signatures --
	// MOBILITY RETIRED 2026-08-31, v15 (user: "We can remove mobility upgrade
	// from the lmg class but lets make its base speed 0.8 instead of 0.75").
	// Was: add_domain( "mobility", "MOBILITY", "+5% move speed / Lv",
	//                  5, array( "heavy" ), TOD_TIER_A );
	// Heavy was MOBILITY's only class, so unscoping it retires the domain
	// outright. Two things went with it and one did not:
	//   * class_speed_base() heavy 0.75 -> 0.80, so the floor rises even though
	//     the card is gone — a heavy who never draws a speed card is FASTER
	//     than before, which is the trade the user asked for.
	//   * LMG SPRINT (below) is the replacement: conditional, not passive.
	//   * Id 9 STAYS MAPPED in domain_id() and in the Lua DOMAIN/DETAIL tables.
	//     Those are KEY-keyed maps, so a stale entry is inert, and removing one
	//     risks disturbing ids the pause plates depend on. Same treatment as
	//     echo/regen/lunge/grinder/momentum/impact before it.
	// REMOVED WITH IT, on the IMPACT ROUNDS precedent (2026-08-31): CARD_SLUG[9]
	// and the three i_tod_card_mobility_* zone lines — an unreachable art slug
	// is dead weight in the .ff, where a Lua row costs nothing. The PNGs stay in
	// source_data.
	//
	// LMG SPRINT (domain 42, v15 — user 2026-08-31: "We also need an LMG upgrade
	// where when you run max speed for 1.5s you get a speed boost").
	// The heavy's signature movement card and the mirror of ADRENALINE: where the
	// skirmisher's burst is paid by KILLS, the heavy's is paid by COMMITMENT —
	// keep running in a straight line and the freight train winds up. Nothing at
	// a standstill; the full ladder after TOD_LMGS_ARM_MS of unbroken sprint.
	// Effect lives in lmg_sprint_bonus(); the latch is armed by the 20 Hz
	// watcher in _tod_uniques.gsc.
	// A-tier, matching ADRENALINE: strong, but conditional and capped.
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "lmgsprint",  "FULL STEAM",  "sprint 0.8s without stopping for a speed boost", 5, array( "heavy" ), TOD_TIER_A );
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "bulletfeed", "BULLET FEED", "reserve trickles into the mag: 1.0s -> 0.2s / round", 10, array( "heavy" ), TOD_TIER_A );
	// ECHO ROUNDS REMOVED 2026-08-23 (user: "we need to remove echo rounds").
	// Was: add_domain( "echo", "ECHO ROUNDS", "+10% / Lv chance to strike twice",
	//                  10, array( "heavy" ), TOD_TIER_S );
	// At Lv10 it was a FLAT DOUBLING of the heavy's damage (100% chance to strike
	// twice) stacked on top of DAMAGE's +120%, which is why the heavy's ceiling
	// ran away from the other three classes.
	// NOT deleted from domain_id() (_tod_upgrade_ui.gsc case "echo" -> 11) or
	// from the Lua DOMAIN[11] row, and that is deliberate: those two are a
	// KEY-KEYED map, not an ordered list, so leaving the entries costs nothing
	// and keeps every OTHER domain's id stable. Removing the add_domain call is
	// what takes it out of the pool — it can never be offered, rolled or held.
	// REGEN REMOVED 2026-08-30, v14.11 (user: "Remove regen upgrade from Heavy
	// class"). Was: add_domain( "regen", "REGEN", "+0.5%/s self-heal / Lv",
	//                           10, array( "heavy" ), TOD_TIER_A );
	// Same treatment as "echo"/"grinder"/"lunge": the add_domain call is what
	// puts a domain in the draw pool, so dropping this line removes it. Its
	// id 12 stays mapped in _tod_upgrade_ui::domain_id and in the Lua DOMAIN
	// table on purpose (key-keyed maps — disturbing them shifts ids the pause
	// plates depend on), and the card art stays zoned as dead .ff bytes. The
	// body-loop trickle hook is gone too. The heavy's sustain story is now
	// VITALITY + RECOVERY, registered directly below in its place (order in
	// this function is presentation only — ids live in _tod_upgrade_ui's
	// key-keyed domain_id map, where these two are 38 and 39).
	add_domain( "vitality",   "VITALITY",    "more max health: +10 at Lv1, a little less each level after (+57 at Lv9)", 9, array( "slasher" ), TOD_TIER_A );   // 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"): the WARRIOR's, 6 levels, flat +10 HP / Lv (vitality_hp) - id 37 now
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "vitality",   "VITALITY",    "more max health",                      5, array( "heavy" ), TOD_TIER_S );   // v16: ladder5() as FLAT HP — 10/18/24/28/32 (user: "Flat HP")   // v14.11 — id 38; scope "class" set below
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "recovery",   "RECOVERY",    "health regen starts sooner",           5, array( "heavy" ), TOD_TIER_A );   // v16: max 3 -> 5, ladder5() 10/18/24/28/32%   // v14.11 — id 39; see the define block for the emulation contract
	// PENETRATION (user 2026-08-21): REAL twin — walks the Stoner's
	// penetrateType small -> medium -> large. 2 levels by the gun-data rule.
	// HEAVY-ONLY AGAIN 2026-08-23: the AK-47 traded its p-ladder for r+m so the
	// whole ASSAULT class could roll RECOIL and MAG SIZE (see set_guns below).
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "penetration", "PENETRATION", "shoot through more: small > medium > large", 2, array( "heavy" ), TOD_TIER_B );
	// THOR'S THUNDER (user 2026-08-21): every melee hit calls lightning down on
	// the victim — radius, damage and LOUDNESS all grow per level. Slasher.
	// TIER S -> B (user 2026-08-23: "can we make thors thunder common pull when
	// you have stormbreaker. This is the main power up and its a shame players
	// can get the storm breaker but never the actual power up for it").
	// Draw weight 20 -> 100, so it is offered 5x as often, and its SUPER/ULTIMATE
	// slice stops being halved (tier_rarity_factor 0.50 -> 1.00) — a thunder card
	// can now arrive worth +2 or +3 levels instead of almost always +1.
	// Safe to make common BECAUSE it is gun-bound: set_guns( "thunder",
	// array( "cc_gold_sword" ) ) below means it is only ever in the pool of a player
	// actually holding the Stormbreaker, so a common weighting cannot dilute any
	// other class's deals. It stays a 5-level ladder and still arrives at Lv1
	// free with the gun (register_gun's grant field) — what changes is that
	// levels 2-5 are now reachable inside one run.
	// RETIRED 2026-09-26 (user: Warrior card cut - "let's remove ... Thor's Thunder"). Id 20 stays mapped (append-only); get_level returns 0 so the melee-hit lane goes inert; the T3 blade's register_gun grant is cleared too. Was: add_domain( "thunder",    "THOR'S THUNDER", "melee hits call down lightning on the 2-6 nearest zombies, bigger & more often / Lv", 5, array( "slasher" ), TOD_TIER_B );
	// -- SLASHER signatures --
	// LOG-SCALED (v10.13). The desc no longer quotes a per-level number because
	// there is no longer a per-level number — see leech_hp_for_level (4/6/8/9/10).
	// The card says STAGE, the pause menu discloses the actual amount for the
	// level you hold (tod_upgrade.lua DETAIL[13]) — the user's own split.
	// RETIRED 2026-09-26 (user: Warrior card cut). Id 13 stays mapped. Was: add_domain( "leech",      "LEECH",       "blade kills heal you (+1 stage)",      5, array( "slasher" ), TOD_TIER_B );
	// CLEAVE v8.9 (user 2026-08-21 nerf): a CHANCE ladder, not a guaranteed
	// count — +33%/Lv for one extra target, every 3 levels banks it.
	// MAX 6 -> 3 (v14.11, user 2026-08-30: "Cleave can only go to tier 3 now.
	// It was 6 but this is too OP"): the ladder now ENDS at the first banked
	// extra — Lv3 = one guaranteed extra target, and the second block (Lv4-6,
	// +2 extras) is unreachable. The cb's arithmetic is untouched (int(3/3)=1
	// extra; the old `extra > 2` clamp is dead but harmless belt). Card art
	// says "33% CHANCE PER LEVEL" — level-agnostic, verified by opening the
	// PNG 2026-08-30, so no re-bake.
	// RETIRED 2026-09-26 (user: Warrior card cut). Id 14 stays mapped. Was: add_domain( "cleave",     "CLEAVE",      "+33% / Lv chance to hit an extra zombie (max +1)", 3, array( "slasher" ), TOD_TIER_S );
	// -- TWIN domains (REAL gun-data changes via variant swap; 3 levels by
	//    rule — any upgrade touching gun data caps at 3) --
	// "TRULY fires faster" until 2026-09-11 (user: "We don't need the word truly
	// there. That's confusing. It just needs to be fire faster"). The word was
	// drawing a contrast with ECHO ROUNDS (id 11) — a proc that fired a second
	// bullet rather than raising the rate — and ECHO ROUNDS was REMOVED
	// 2026-08-23 (v9.35; see its own `// Was:` block ~70 lines above), so for
	// the 19 days since, the sentence has been distinguishing this domain from
	// nothing a player can see. The baked cards carried the same word and were
	// re-copied in the same pass (docs/134).
	//
	// THAT DATE WAS WRONG HERE FOR ONE AFTERNOON — written as v14.11 off
	// tod_upgrade.lua:272, whose REGEN note says "REMOVED v14.11 (2026-08-30,
	// with 11/22/30/34)" and sweeps id 11 in with a batch it predates by a
	// week. The SAME Lua file has it right at :558. v14.11 removed REGEN and
	// MOMENTUM; ECHO ROUNDS was already gone. Both Lua lines are corrected.
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-26 (a Skirmisher gun card; the class is retired), dealt to no class. Id 15 stays mapped (append-only). Was: add_domain( "firerate",   "FIRE RATE",   "fires faster (-8% fire time / Lv)",         3, array( "parked" ), TOD_TIER_A );
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-26 (a Skirmisher gun card; the class is retired), dealt to no class. Id 16 stays mapped (append-only). Was: add_domain( "handling",   "HANDLING",    "faster reload, swap & ADS / Lv",            3, array( "parked" ), TOD_TIER_B );
	// RECOIL v9.45 (user 2026-08-23: "recoil should be two levels only. 8% and
	// 16%"), BUFFED 2026-08-26 (user: "Recoil will go to 10% per level") to
	// -10/-20%. History: -25/-45/-65% (2026-08-19) -> halved to -10/-20/-30%
	// (2026-08-21) -> -8/-16% (v9.45) -> this. THE LEVEL COUNT IS A GENERATOR
	// FACT, not just a cap: gen_tod_twins.js AXIS.r must drop to levels 2 in the
	// same commit or the r3 forms it emits become dead weapon assets and a Lv3
	// that this cap can never reach. THE PERCENTAGES ARE A GENERATOR FACT TOO —
	// they live in RECOIL_STEP, so a change here without regenerating the twins
	// (and a FULL build, because that rewrites weapon GDT data) is display-only
	// and the card will lie.
	// RETIRED 2026-09-25 (user: the Archer "shouldn't even be" offered this; its bows have one form now). Id stays mapped (append-only). Was: add_domain( "recoil",     "RECOIL",      "kick reduced -15/-30%",                     2, array( "assault" ), TOD_TIER_B );   // -10/-20 -> -15/-30 v16.50 (user 2026-09-02: "buff recoil to 15%"); the number lives in gen_tod_twins.js RECOIL_STEP (a twin domain: regen + FULL build), this string and the card art only mirror it (docs/78)
	// LOG-SCALED (v10.13). The swing-speed ladder lives in the GENERATOR
	// (tools/gen_tod_twins.js KNIFE_STEP, now 1/.90/.84/.80/.77/.74), so the
	// numbers here are display only — keep them in step with that table or the
	// card lies. Pause-menu actuals: tod_upgrade.lua DETAIL[18] (10/16/20/23/26%).
	// add_domain( "knifespeed", "MELEE SPEED" ) — RETIRED 2026-09-27 into HEAVY HANDS (the Warrior's core card):
	// the "k" swing-speed forms now follow heavyhands' 3/6/9 steps (axis_level).
	add_domain( "heavyhands", "ARMS SPECIALIST", "your melee weapons hit harder and reach further / Lv; swing faster at Lv3, Lv6 and Lv9", 9, array( "slasher" ), TOD_TIER_A );   // WARRIOR CORE WEAPON CARD (2026-09-27)
	// ATHLETE (v16, id 43, user 2026-09-01: "slide faster and jump higher ...
	// 5 tiers 10% slide speed each tier and 25% jump height increase each tier").
	// The WHOLE mechanic lives in _tod_athlete.gsc as per-player VELOCITY writes
	// (slide start speed x(1+0.10/Lv), jump z x sqrt(1+0.25/Lv), the jump edge
	// keeping exactly the pre-jump speed, and — v16.23, 2026-09-02 — AIR
	// STEERING: the velocity heading turns toward the movement stick at
	// 360 deg/s per level, speed unchanged). NOTHING of it touches the
	// move-speed scale — v16.1 (2026-09-01) retired the "+0.10 scale while
	// IsSliding" lane: SetMoveSpeedScale scales INPUT-driven movement, the
	// engine's slide is not input-driven, and two lanes for one number was a
	// double-count waiting to happen. This add_domain line is the domain's only
	// footprint in this file. Fills the mobility hole the retired chain lunge
	// (id 22) left in the kit.
	// RETIRED 2026-09-26 (user: Warrior card cut). Id 43 stays mapped; _tod_athlete.gsc stays linked and reads level 0 = inert. Was: add_domain( "athlete",    "ATHLETE",     "+10% slide speed, +25% jump height and air steering / Lv", 5, array( "slasher" ), TOD_TIER_A );
	// GUNSLINGER (v16.51, id 44, user 2026-09-02: "Slashers need an ability that
	// make their secondary do more boss and elite damage. 30% each tier up to 5
	// tiers. This will be B tier"). The mechanic is ONE line in
	// slasher_sidearm_boss_mult(): the slasher's class secondary vs the
	// boss/elite triad pays the class baseline x(1 + 0.30/Lv). Both boss lanes
	// (upgrade_damage_cb and _tod_bosses::rp_damage_feed) call that function,
	// so there is one number, TOD_UPG_GUNSLINGER_PER_LVL. Scope class (the
	// default) — the sidearm changes with the tier, the bonus follows the
	// player. Card art PENDING (docs/79): ships on the text fallbacks
	// (CARD_SLUG[44] unset, PAUSE_PLATE_MAX/TOD_UPG_PLATE_MAX stay 43) until the
	// four PNGs land.
	// RETIRED 2026-09-26 (user: Warrior card cut). Id 44 stays mapped; slasher_sidearm_boss_mult reads level 0 = the class baseline only. Was: add_domain( "gunslinger", "GUNSLINGER",  "+30% sidearm damage to bosses and elites / Lv",   5, array( "slasher" ), TOD_TIER_B );
	// CHAIN LUNGE REMOVED 2026-08-24 (user: "we need to remove chain lunge from
	// the game. It doesnt work"). Same treatment as "echo" and "grinder": the
	// add_domain call is what puts a domain in the draw pool, so dropping this
	// line removes it. Its id 22 stays mapped in _tod_upgrade_ui::domain_id and
	// in the Lua DOMAIN table on purpose — those are key-keyed maps and
	// disturbing them would shift ids the pause plates depend on. _tod_lunge.gsc
	// is unlinked from the zone and the on_class_gun_kill hook is gone.
	// RUN AND GUN (user 2026-08-22: "shoot while you run, take up less bullets")
	// — id 23 in _tod_upgrade_ui::domain_id + tod_upgrade.lua DOMAIN. Mechanics
	// live in _tod_runandgun.gsc (it imports us for get_level; we never import
	// it). Skirmisher-only; tier B = the ammo-economy band (RESERVE, BULLET FEED).
	// v14.11 (user 2026-08-30): the card gained a DAMAGE half — same ladder,
	// same "moving" test, applied in unique_damage_mult. One card, one
	// condition, two payouts. v16.50 (user 2026-09-02): FIVE levels on a
	// stage table, 16/28/38/46/52% (was 20/35/50 over 3) — LOCKSTEP trio:
	// TOD_RNG_PCT_L* / TOD_UPG_RNG_DMG_L* / DETAIL[23]; max 5 here and in
	// DOMAIN[23]. Card art: the value line is generic (no number), so only the
	// pip row (3 -> 5) is owed — docs/76. Still tier B: it shares the ammo-economy band's
	// weight even though the damage half nudges it toward A — the user set the
	// rates, the band stays until they say otherwise. Card art re-bake PENDING
	// ("FREE SHOTS ON THE MOVE" is now half the story — see the v14.11 art
	// prompt doc); the desc + Lua rows carry the full text meanwhile.
	// v16.36: REQUIRES SPRINT FIRE — set_requires( "runandgun", "sprintfire" )
	// at the bottom of this function; the card never rolls before it is owned.
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-26 (a Skirmisher gun card; the class is retired), dealt to no class; its watcher _tod_runandgun.gsc is archived. Id 23 stays mapped (append-only). Was: add_domain( "runandgun",  "RUN AND GUN", "moving: 16/28/38/46/52% free shots, and that much more damage", 5, array( "parked" ), TOD_TIER_B );
	// ---- CLASS TIER UNIQUES (docs/25 §9; ids 25..31 in _tod_upgrade_ui::domain_id
	//      + tod_upgrade.lua DOMAIN). Each is bound to ONE tier gun by gun_keys
	//      (set below) and resets on a tier-up like every gun domain. All
	//      script-side — zero weapon assets. Effects: unique_damage_mult /
	//      unique_on_hit (damage chain), on_class_gun_kill (kills),
	//      adren_bonus (move speed); inputs: _tod_uniques.gsc watchers.
	add_domain( "adrenaline", "ADRENALINE",       "3 quick explosive kills heal you and give a 3 sec burst of speed and damage; more of each and a shorter cooldown / Lv", 9, array( "heavy" ), TOD_TIER_A );   // v16: 5 tiers, +3%/tier, 3 kills in 1.5s. 2026-09-27 UN-PARKED for the BREACHER (the build-cards pass: shotgun multi-kills), any weapon, class scope, cd 20/18/16/14/12s; v17.67: the same % is also bullet damage during the burst; v17.85: and the same % of max health, healed on trigger   // 2026-09-26 PARKED: a Skirmisher gun card; the class is retired (the Necromancer replaced it) and "parked" matches no class
	// OVERDRIVE MOVED skirmisher/MP7 -> heavy/DEATH MACHINE (user 2026-08-23:
	// "overdrive should be an upgrade of the death machine. Remove meat grinder
	// and replace with overdrive"). OVERDRIVE and MEAT GRINDER were always the
	// same mechanic — "keep the trigger down, hit harder" — so the roster
	// carried a duplicate; the minigun is the natural home for it and the MP7
	// now needs an identity of its own.
	// This is also a real HEAVY NERF, which is the point: MEAT GRINDER capped at
	// +100% and a 150-round belt reached that cap trivially, so the heavy ran a
	// near-permanent x2 on top of the (now removed) ECHO ROUNDS x2. OVERDRIVE
	// tops out at +60%.
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "overdrive",  "OVERDRIVE",        "hold the trigger: damage ramps up over 3 seconds",                    5, array( "heavy" ), TOD_TIER_S );   // v16: max 3 -> 5, ramps to +5/10/15/20/25%
	// SECOND WIND — the MP5's unique since v14.11 (user 2026-08-30: "guve
	// second wind upgrade to the MP5 only instead of Mp7"; it was the MP7's
	// replacement unique from 2026-08-23). Gun-bound below.
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-27 (the Warrior is at the 12-row class cap), dealt to no class. Id 33 stays mapped (append-only). Was: add_domain( "secondwind", "SECOND WIND",      "sprint to heal: 1% of your health per second per level",              5, array( "parked" ), TOD_TIER_S );
	// MOMENTUM REMOVED 2026-08-30, v14.11 (user: "Remove momentum upgrade").
	// Was: add_domain( "momentum", "MOMENTUM",
	//        "damage scales with your speed: up to +5% per level while moving",
	//        5, array( "skirmisher" ), TOD_TIER_A );
	// Id 34 stays mapped in domain_id() and the Lua tables (key-keyed maps);
	// its card art stays zoned. The set_guns binding and the
	// unique_damage_mult hook are gone — RUN AND GUN's damage half is the
	// moving-damage card now, and SECOND WIND (above) takes the MP5 slot.
	// KILL RELOAD REMOVED 2026-09-01 (user asked "Didint we remove mag reload on
	// kill?" — it had NOT gone, IMPACT ROUNDS had — then: "Lets remove it. No one
	// likes it"). Same form as IMPACT ROUNDS below: id 27 stays mapped in
	// domain_id() and in the Lua tables (key-keyed, nothing renumbers, the id
	// cannot be reused); CARD_SLUG[27] and the three i_tod_card_kill_reload_*
	// zone lines are gone (an unreachable art slug is dead weight in the .ff, a
	// Lua row costs nothing; PNGs + GDT rows stay in source_data); the effect is
	// gone too (the block in unique_on_kill, killreload_kills_needed and the three
	// TOD_KILLRELOAD_KILLS_LV* defines) — a dead lane that still looks live is how
	// the next reader loses an hour. It was the assault's only B-band ammo card:
	// a magazine topped up FROM RESERVE every 55th/40th/30th kill (v9.43 frequency
	// ladder, buffed 2026-08-27 from 100/75/50 because nobody took it; still
	// nobody did). The assault pools go 12/12/13 -> 11/11/12 cards.
	// Was: add_domain( "killreload", "KILL RELOAD",
	//        "every 55th/40th/30th kill refills your magazine from reserve",
	//        3, array( "assault" ), TOD_TIER_B );
	// IMPACT ROUNDS REMOVED 2026-08-31 (user: "remove impact rounds from assault
	// class. Lets completely retire this upgrade. No one likes it").
	// Was: add_domain( "impact", "IMPACT ROUNDS",
	//        "3% of hits burst nearby zombies for 40% of the hit, per level",
	//        10, array( "assault" ), TOD_TIER_S );
	// Id 28 stays mapped in domain_id() and in the Lua tables (key-keyed maps),
	// so nothing renumbers. REMOVED WITH IT, unlike the MOMENTUM/REGEN form:
	// CARD_SLUG[28] and the three i_tod_card_impact_rounds_* zone lines, on the
	// CHAIN LUNGE precedent — an unreachable art slug is dead weight in the .ff,
	// where a Lua row costs nothing. The PNGs stay in source_data.
	// The effect is gone too (impact_splash + the block in unique_on_hit + the
	// four TOD_IMPACT_* defines): leaving it would have been inert, since
	// get_level returns 0 for an unrollable domain, but a dead lane that still
	// LOOKS live is how the next reader loses an hour.
	// RETIRED 2026-09-26 (user: Breacher card cut, "shouldn't even be in the game"). Id stays mapped (append-only). Was: add_domain( "suppress",   "SUPPRESSING FIRE", "hits slow the horde 12/24/36% for 1.5s",                              3, array( "heavy" ),      TOD_TIER_A );
	// THE BREACHER'S CARDS (2026-09-26, user: "they should have pellets ... more explosive
	// damage, definitely ... the upgrades for their actual tactical/lethal ... the more you
	// upgrade the more you get them"; on asking: C4 and Cluster are EARNED by the card).
	// Ids 58-61 (claimed across sessions; 62/63 are the Warrior's - the 6-bit field is full).
	// PELLETS is a twin axis ("e", gen_tod_twins.js gun.pellets) on all three Breacher guns;
	// C4 / CLUSTER are each their item's whole lane: charges AND damage, 8 levels
	// (_tod_class_kit c4_max / cluster_max / kit_dmg_mult). The EXPLOSIVES card (59)
	// was cut the same day (user: the damage lives in these two lanes) - 59 is FREE.
	// add_domain( "pellets", "PELLETS", 3 ) — RETIRED 2026-09-27 into BUCKSHOT (the Breacher's core card):
	// the "e" pellet forms now follow buckshot's 3/6/9 steps (axis_level).
	add_domain( "buckshot",   "BUCKSHOT",    "your shotguns hit harder / Lv; more pellets at Lv3, Lv6 and Lv9", 9, array( "heavy" ), TOD_TIER_A );   // BREACHER CORE WEAPON CARD (2026-09-27)
	add_domain( "c4",         "STICKY C4",   "earn the sticky C4: more damage / Lv; another charge per round and a bigger blast at Lv3, Lv6 and Lv9", 9, array( "heavy" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	add_domain( "cluster",    "CLUSTER",     "earn the Cluster grenade: more damage / Lv; a bomblet layer at Lv3, a layer + a 2nd grenade + bigger blasts at Lv6, a 3rd grenade + bigger blasts at Lv9", 9, array( "heavy" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	// MEAT GRINDER REMOVED 2026-08-23 — superseded by OVERDRIVE on the same gun.
	// Was: add_domain( "grinder", "MEAT GRINDER",
	//        "keep firing, hit harder: +2/+3/+4% per 5 rounds, up to +50/75/100%",
	//        3, array( "heavy" ), TOD_TIER_S );
	// As with "echo", the key stays in domain_id() and in the Lua DOMAIN table
	// on purpose — those are key-keyed maps, so leaving the entries costs
	// nothing and keeps every other domain's id stable. Dropping the add_domain
	// is what removes it from the pool.
	// RETIRED 2026-09-26 (user: "remove draw cut from the upgrades as well"; Warrior card cut #2). Id 31 stays mapped; the swing-window lane reads level 0. Was:
	// add_domain( "drawcut",    "DRAW CUT",         "swings within 0.4s of a sprint deal +50/+100/+150%",                  3, array( "slasher" ),    TOD_TIER_B );
	// FORCED MARCH — the AK-47's unique (user 2026-08-24: "AK 47 will need a
	// speed boost. The only AR that gets a speed upgrade and it only goes 3
	// levels"). Assault had NO speed domain at all: SPRINT is skirmisher +
	// slasher, MOBILITY is heavy. Gun-bound to cc_fire_bow below, so it is the
	// assault's T3 reward and not a class-wide one — and 3 levels at the shared
	// +5%/Lv caps it at +15%, taking the assault from 0.9 to 1.035: just past the
	// skirmisher's BASE, still short of a skirmisher who has spent anything on
	// SPRINT. It rides the SAME lane as SPRINT/MOBILITY in apply_move_speed()
	// rather than inventing a second speed multiplier — one owner for move speed.
	// RETIRED 2026-09-26 (user: Archer card cut). Id 37 stays mapped. Was: add_domain( "march",      "FORCED MARCH",     "+5% move speed / Lv",                                                 5, array( "assault" ),    TOD_TIER_A );   // max 3 -> 5 (user 2026-08-29); card text is LINEAR so no re-bake needed (domain-retune checklist), pips clamp at 3 by design

	// Archer tactical is always available. Keep append-only id 41 / key
	// distraction. 2026-09-25 (user): EIGHT levels, each LOGARITHMICALLY
	// longer grapple range, and a LANDING BUFF (move speed + damage reduction
	// for a second or two after a grapple touches down) whose strength and
	// length grow on the same curve. The recharge no longer scales (fixed 12 s).
	// All numbers: _tod_archer.gsc grapple_curve() and the TOD_ARCHER_LAND_*
	// defines; the Lua row 41 mirrors them.
	add_domain( "distraction", "GRAPPLE", "longer grapple; landing gives a burst of speed and damage reduction / Lv", 9, array( "assault" ), TOD_TIER_S );   // 8 -> 9 levels (2026-09-27): the curve is ln(1+Lv)/ln(10)
	add_domain( "deadeye",    "DEADEYE",     "your bows hit harder / Lv; fatter arrows at Lv3, Lv6 and Lv9", 9, array( "assault" ), TOD_TIER_A );   // ARCHER CORE WEAPON CARD (2026-09-27)
	// HELL'S RETRIEVER (id 57, 2026-09-26, user): the Archer's lethal is EARNED
	// by this card now (Lv0 = no lethal; a tod_dev build treats Lv0 as Lv1).
	// Eight levels: more stored throws (1 / 2 at Lv3 / 3 at Lv6) and more damage
	// (x1.0 at Lv1 -> x3.0 at Lv8 on the grapple's log curve). Numbers live in
	// _tod_retriever.gsc (TOD_RET_*); the Lua row 57 mirrors them.
	add_domain( "retriever",  "HELL'S RETRIEVER", "throwing axe that chains and returns; more damage / Lv; another stored throw at Lv3, Lv6 and Lv9", 9, array( "assault" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27); band A: it is the class lethal
	// WARRIOR KIT CARDS (ids 62 / 63, 2026-09-26, user: "add those upgrades" - the
	// Warrior's tactical and lethal never improved). Hellbound's own 8-level
	// ladders; every Warrior has both abilities at level 0 from spawn, so a card
	// only ever makes them better. Numbers live in _tod_class_kit.gsc
	// (TOD_BASH_* / TOD_GS_*); the Lua rows 62 / 63 mirror them. Class scope (the
	// default): they survive promotions, like the abilities themselves.
	add_domain( "bash",       "BASH",           "dash and strike: hits harder and recharges faster / Lv; a 2nd dash at Lv3, a 3rd at Lv6, a wider burst at Lv9", 9, array( "slasher" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	add_domain( "gravsmash",  "CYBER SMASH",    "fewer kills to charge and a bigger hit on elites / Lv; a longer elite stun at Lv3, Lv6 and Lv9", 9, array( "slasher" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	// MELEE RANGE (id 31, reusing DRAW CUT's number; user 2026-09-26 after build 11:
	// "one upgrade for ranged, increasing your range ... for hitting what the melee
	// is"): every Warrior swing's crowd sweep reaches +15% / Lv further (script,
	// _tod_warrior_melee TOD_WM_RANGE_*; the engine's single-target hit is unchanged).
	// Class scope: it survives promotions. No dark card. Text fallback until art.
	// RETIRED 2026-09-28 (user: "move melee range upgrade inside of arms specialist"): its reach is ARMS SPECIALIST's now (+10% / Lv, _tod_warrior_melee reach_mult). Id 31 stays mapped. Was: add_domain( "meleerange", "MELEE RANGE",    "your swings reach further (+15% / Lv): a swing that misses hits the nearest zombie in reach, and CLEAVE's extra hits reach further too",           6, array( "slasher" ), TOD_TIER_A );   // 5 -> 6 levels (2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"))
	// NECROMANCER CLASS CARDS (ids 59 / 38 / 39, 2026-09-26, user: "complete the
	// upgrades ... this is your responsibility"). The Soul Bomb and the helpers are
	// the class's kit from spawn (level 0 works), so every card only makes them
	// better. Numbers live in _tod_necro_summon.gsc (TOD_BOMB_* / TOD_POWER_* /
	// TOD_BEAM_*); the Lua rows 59 / 38 / 39 mirror them. Class scope (the default):
	// they survive promotions. 38 / 39 REUSE the retired VITALITY / RECOVERY ids
	// under NEW keys (docs/upgrade_ids.md), 59 is the never-shipped EXPLOSIVES id.
	add_domain( "soulbomb",    "SOUL PULSE",      "fewer souls to charge and a harder hit on elites / Lv; a wider pulse at Lv3, Lv6 and Lv9", 9, array( "necromancer" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	add_domain( "summonpower", "SUMMONING POWER", "faster binds, longer-lived helpers that hit elites harder / Lv; a helper slot at Lv3 and Lv6, a 2nd Mangler at Lv9", 9, array( "necromancer" ), TOD_TIER_A );   // 8 -> 9 levels, 3/6/9 steps (2026-09-27)
	add_domain( "soulbeam",    "SOUL SUCK",       "Soul Suck hits harder and costs less / Lv; one more soul at once and a faster soul-rip at Lv3, Lv6 and Lv9", 9, array( "necromancer" ), TOD_TIER_A );   // NECROMANCER CORE WEAPON CARD (2026-09-27): 5 -> 9 levels
	// THE CLASS BUILD CARDS (2026-09-27, user: "building builds within classes ... more
	// upgrades so that you can go into your own lane"). Three lanes per class - WEAPON /
	// KIT / SURVIVAL - and four new cards each (three here + one un-parked card above), all
	// band A, 9 levels, big steps at Lv3 / Lv6 / Lv9. Mechanics: _tod_class_cards.gsc and
	// the class modules named in its header. LOCKSTEP tod_upgrade.lua rows 5 / 10 / 17 / 19 /
	// 26 / 29 / 35 / 36 / 37 / 42 / 12 / 48 / 9 and docs/upgrade_ids.md.
	// -- NECROMANCER
	add_domain( "reaperreach", "REAPER'S REACH", "longer beam / Lv; a wider beam at Lv3, Lv6 and Lv9", 9, array( "necromancer" ), TOD_TIER_A );   // weapon lane
	// RETIRED 2026-09-27 class pass 4 (user) (id 10 free; pack_lv reads 0). Was: add_domain( "packmaster",  "PACK MASTER",    "helpers hit elites harder / Lv; faster hound bites at Lv3, a faster Mangler cannon at Lv6, thralls burst when they fall at Lv9", 9, array( "necromancer" ), TOD_TIER_A );   // kit lane
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-27 (CLASS PASS 2, the 12-row cap), dealt to no class; its lane left _tod_class_cards the same build. Id 17 stays mapped (append-only). Was: add_domain( "soulsiphon",  "SOUL SIPHON",    "every soul the beam rips heals you / Lv; then you take less damage for 3 s at Lv3, Lv6 and Lv9", 9, array( "parked" ), TOD_TIER_A );
	// add_domain( "burnedout", "BURNED OUT", ... ) RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"): Burned Out is the Necromancer's PASSIVE (Widow's Wine) at its base numbers; get_level reads 0. Id 19 -> SUMMONER MASTER.
	add_domain( "summonmaster", "SUMMONER MASTER", "kills by your helpers raise your max health while you are at full health; a higher cap / Lv and per tier", 9, array( "necromancer" ), TOD_TIER_A );   // survival lane (2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"))
	add_domain( "cloak",       "INVISIBILITY CLOAK", "earn the cloak on tactical: enemies lose you and nothing hurts you; longer and more often / Lv", 9, array( "necromancer" ), TOD_TIER_A );   // kit lane (2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"))
	// -- ARCHER
	// RETIRED 2026-09-27 CLASS PASS 3 (user) (id 26 -> PIERCING). Was: add_domain( "huntersmark", "HUNTER'S MARK",  "full-draw arrows and crossbow bolts mark their target: everyone hits it harder / Lv; the mark lasts longer at Lv3, Lv6 and Lv9", 9, array( "assault" ), TOD_TIER_A );   // weapon lane
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities") (id 29 -> SPRINT). Was: add_domain( "aerialist",   "AERIALIST",      "the grapple recharges faster / Lv; a landing refills a Retriever throw at Lv3, sends a shockwave at Lv6, refills every throw at Lv9", 9, array( "assault" ), TOD_TIER_A );   // kit lane
	add_domain( "shotspeed",   "QUICK DRAW",     "draw, shoot and reload faster, and arrows fly faster; 3 times as fast at Lv9, an almost automatic bow", 9, array( "assault" ), TOD_TIER_A );   // 2026-09-27 class pass 4 (user): split out of DEADEYE, 6 levels (id 35); x3 at Lv9 since 2026-10-05 (the automatic bow, _tod_archer_bow). LOCKSTEP tod_upgrade.lua DOMAIN[35]
	add_domain( "pierce",      "PIERCING",       "arrows and bolts go through zombies: pierced hits land harder / Lv; one more zombie at Lv3, Lv6 and Lv9", 9, array( "assault" ), TOD_TIER_A );   // 2026-09-27 CLASS PASS 3 (user): "Archer needs a piercing ability ... with the increased girth combined with piercing" (_tod_class_cards::pierce)
	// RETIRED 2026-09-27 CLASS PASS 3 (user) (id 35 freed). Was: add_domain( "shadowstep",  "SHADOWSTEP",     "when a zombie hits you the horde loses you for a moment and you speed up; longer and more often / Lv", 9, array( "assault" ), TOD_TIER_A );   // survival lane
	// -- BREACHER
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities") (id 36 -> EXPLOSIVE FUSION). Was: add_domain( "pointblank",  "POINT BLANK",    "your shotguns hit harder up close / Lv; close kills put 1 / 2 / 3 shells back at Lv3, Lv6 and Lv9", 9, array( "heavy" ), TOD_TIER_A );   // weapon lane
	add_domain( "fusion",      "EXPLOSIVE FUSION", "your C4 and Cluster explosions heal you when you stand in them, and jumping as your Cluster bursts launches you high into the air (more / Lv)", 9, array( "heavy" ), TOD_TIER_A );   // kit lane, 9 levels (2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"); 2026-09-29: the launch needs a jump)
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities") (id 37 -> VITALITY). Was: add_domain( "demolition",  "DEMOLITIONIST",  "bigger C4 and Cluster blasts / Lv; explosive kills can refund a charge at Lv3, Lv6 and Lv9", 9, array( "heavy" ), TOD_TIER_A );   // kit lane
	// RETIRED 2026-09-27 CLASS PASS 3 (user) (id 42 freed). Was: add_domain( "bulwark",     "BULWARK",        "take less damage while 3+ zombies are close / Lv; a bigger step at Lv3, Lv6 and Lv9", 9, array( "heavy" ), TOD_TIER_A );   // survival lane
	// -- WARRIOR
	add_domain( "sweep",       "CLEAVE",         "your swings hit more zombies: a 33% chance of one more zombie per level; always 2 at Lv3, 3 at Lv6, 4 at Lv9", 9, array( "slasher" ), TOD_TIER_A );   // 2026-09-27 class pass 4 (user): the Warrior's crowd card (_tod_warrior_melee cleave_extra); key "sweep" so the retired "cleave" lane stays off
	add_domain( "demonslayer", "DEMON SLAYER",   "killing an elite heals you a little and makes you faster and hit harder for a while / Lv; lasts longer at Lv3, Lv6 and Lv9", 9, array( "slasher" ), TOD_TIER_A );   // weapon lane (2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"))
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities") (id 12 -> DEMON SLAYER). Was: add_domain( "executioner", "EXECUTIONER",    "your blades hit elites harder / Lv; an elite you finish heals you at Lv3, Lv6 and Lv9", 9, array( "slasher" ), TOD_TIER_A );   // weapon lane
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities"). Was: add_domain( "rhythm",      "BATTLE RHYTHM",  "melee kills bring the next Bash sooner / Lv; kills count twice for Cyber Smash at Lv3, +1 stored Bash at Lv6", 9, array( "slasher" ), TOD_TIER_A );   // kit lane
	// RETIRED 2026-09-27 CLASS PASS 2 (user: "few tweaks to abilities") (id 9 -> INVISIBILITY CLOAK). Was: add_domain( "juggernaut",  "JUGGERNAUT",     "take less damage for 2 s after a melee hit / Lv; a bigger step at Lv3, Lv6 and Lv9", 9, array( "slasher" ), TOD_TIER_A );   // survival lane
	// TRAILBLAZER (v16.62, id 46, docs/80; user 2026-09-02: "Can the fire fx go on the
	// ground? And the higher tier the larger and more effective it is?"): the
	// skirmisher sprint leaves BURNING GROUND PATCHES behind it; any zombie that
	// runs through one burns for a fraction of the ROUND zombie health per
	// second (12..28%/Lv — the PhD-nova scaling rule, so it never one-shots
	// early and never falls off late). Per level it is LONGER (2..4 s), WIDER
	// (56..88 u radius; 1/2/3 fire patches across the trail) and HOTTER.
	// Mechanic: trail_loop() (end of file); the burn passes upgrade_damage_cb
	// on the tod_trail_hit mark. Class scope (the default) — survives
	// promotions; skirmisher only. Card art PENDING (docs/83): text fallbacks
	// (CARD_SLUG[46] unset, PAUSE_PLATE_MAX stays 44).
	// RETIRED 2026-10-05 W2E (user: "Just dont include assets not on this map in the build"): parked since 2026-09-26 (not a Necromancer card), dealt to no class; its lane (trail_loop .. trail_burn_tick) left this file the same build. Id 46 stays mapped (append-only). Was: add_domain( "trailblazer", "TRAILBLAZER", "sprinting leaves burning ground that slows everything on it and burns all but elites / Lv", 5, array( "parked" ), TOD_TIER_A );

	// -- RIOT SHIELD (v16.63, id 45, 2026-09-02 — user: "add a riot shield to the map.
	// It is for all classes and has 5 levels. Each level increasing the health
	// and decreasing the recharge. Once it breaks it needs to be recharged and
	// you will get it back automatically.") ---------------------------------
	// UNIVERSAL (class_keys undefined), max 5, scope "class" (the default: a
	// promotion never takes your shield). The LADDER is the user's table,
	// verbatim: 200 / 300 / 370 / 450 / 500 shield HP, recharge 4:00 / 3:30 /
	// 3:00 / 2:30 / 2:00. The numbers live in _tod_riotshield.gsc
	// (TOD_SHIELD_HP_L1..L5 / TOD_SHIELD_RECHARGE_L1..L5) and are MIRRORED in
	// tod_upgrade.lua's SHIELD_HP / SHIELD_RECHARGE tables — this desc and the
	// armory row are copies. Band A: it is survivability like DMG REDUCTION (A
	// since v16), not a run-winner on its own — a broken shield is gone for
	// minutes, and the first level is a 200 HP shield with a four-minute hole.
	// The whole weapon lane (give / break / recharge / re-give) is a RECONCILE
	// in _tod_riotshield.gsc, the DISTRACTION shape: the domain level is the
	// only input, so every path that writes a level (card, tier, dev)
	// lands by construction. Pool registration ONLY here.
	add_domain( "riotshield", "RIOT SHIELD", "earn a riot shield that recharges after it breaks: more health and a faster recharge / Lv; the cyber shield at Lv9", 9, array( "heavy" ), TOD_TIER_B );   // 2026-09-28 (user): out of the shared pool, BREACHER ONLY, 9 levels (was 5, every class)   // A -> B 2026-09-08 (user: "move riot shield to B tier for all classes"). It stays UNIVERSAL (class_keys undefined) — "for all classes" is the existing scope, not a change. Band is DRAW ODDS ONLY and is never drawn: weight 50 -> 100 (offered ~2x as often) and the SUPER/ULTIMATE slice x0.75 -> x1.00, so the copies you see also skew rarer. No card re-bake, no Lua row, no pause change

	// DEADSHOT (v16.64, 2026-09-02 — user: "we would need a deadshot upgrade
	// now. Basically its perma deadshot. Itll show up in your perk bar as well
	// and only way to pull it is an Ultimate card ... Name on top will be
	// Deadshot. Aim bot will be the description").
	//
	// ASSAULT ONLY, max 1, band S (the rarest draw), scope class (default —
	// survives promotions). ONE level = the engine's Deadshot head-snap aim
	// assist (UseAlternateAimParams, gamepad only) switched on for the rest of
	// the match: perma through downs and respawns, drawn in the perk bar with
	// the Deadshot crest, and it does NOT spend a perk slot (raw SetPerk +
	// our own toplayer field, never zm_perks::give_perk — num_perks untouched).
	// The whole effect lane is _tod_deadshot.gsc|.csc (a 1 s reconcile loop
	// reads get_level, so every grant path — the deal, the station, the dev
	// grant-all — lands without a hook here). The card is ALWAYS
	// ULTIMATE: set_rarity_lock( "deadshot", 3 ) below. Deadshot the PERK stays
	// retired (v14.16, roster at cap 9); this is the UPGRADE. The stair-bounce
	// it used to have was the zombies' stepped climb, fixed in v16.61a.
	// Art: ONE card, docs/84 (i_tod_card_deadshot_ultimate). Pause row stays
	// text (no plate requested).
	// RETIRED 2026-09-25 (user: the Archer "shouldn't even be" offered this; its bows have one form now). Id stays mapped (append-only). Was: add_domain( "deadshot",   "DEADSHOT",    "aim bot: aim assist locks onto zombie heads, permanently", 1, array( "assault" ), TOD_TIER_S );

	// ---- CLASS TIERS: WHAT A PROMOTION COSTS YOU ---------------------------
	// (docs/25 §2.3, §3. Rule REVERSED 2026-08-31, v15 — user: "We should remove
	// the idea of reseting upgrades unless its a gun specific upgrade. So if you
	// class tier upgrade your upgrades will stay. Things like draw cut since its
	// specific to a weapon would need to be removed.")
	//
	// THE DEFAULT IS NOW "class" (add_domain stamps it), i.e. PERSISTENCE IS THE
	// RULE AND RESETTING IS THE EXCEPTION. Everything below is the exception list.
	// Before v15 this was inverted and the list was the persisting ten; if you are
	// reading an older comment elsewhere that says "gun (default)", it is stale.
	//
	// WHAT A PROMOTION COSTS NOW — 13 domains, of which only 9 are ever really
	// losable (see the gun_keys note at the bottom of this block):
	//   6 REAL WEAPON-VARIANT LADDERS. These are not flavour — each is a literal
	//     per-gun stat axis the generator emitted (gen_tod_twins.js AXIS), so a
	//     level in one names a variant asset of ONE gun. Two independent reasons
	//     they must reset: a persisted level would be meaningless on a gun without
	//     that axis (the MP5/MP7 have no f-axis, the HK21 has no axes at all), and
	//     the pause menu would print a level that does nothing.
	//   7 GUN-BOUND UNIQUES. ⚠️ THIS IS THE LOAD-BEARING HALF. gun_keys gates what
	//     you can ROLL, never what FIRES — unique_damage_mult and unique_on_hit do
	//     no weapon test at all (see the comment on unique_damage_mult). So a
	//     persisted DRAW CUT would keep paying +150% on the STORMBREAKER, and
	//     SUPPRESSING FIRE would keep slowing the horde off the Death Machine.
	//     That is exactly the case the user named. DO NOT move one of these to
	//     "class" without first giving its effect a weapon test.
	//
	// KEEP tod_upgrade.lua's TIER_SAFE IN STEP. It is only the nil-fallback now
	// (sync_max packs a server-computed survives bit into every row), but a
	// fallback that disagrees with this list is a UI that lies when it is used.
	// ---- DMG REDUCTION: THE ONE DOMAIN WITH FOUR DIFFERENT CAPS (v17.3) ----
	// User 2026-09-03, on the finding that capping DR at 5 universally had left
	// the skirmisher, assault and slasher on IDENTICAL effective HP: "Yes lets
	// do 3, 5, 7, 10 as the max / Skirm, slash, assault, heavy".
	//
	// DR was the only mitigation three of the four classes had, so a shared cap
	// meant they differed by exactly nothing on defence — the fast, high-damage
	// classes were no squishier than the slow one. Now the cap IS the trade:
	//
	//   skirmisher 3   -15%   176.5 e-HP      the glass cannon
	//   slasher    5   -20%   187.5 e-HP
	//   assault    7   -24%   197.4 e-HP
	//   heavy     10   -30%   214.3 e-HP  (260.0 with VITALITY 5's 182 base)
	//
	// NO LADDER WORK WAS NEEDED: dr_pct_for_level already ran past 5 on
	// TOD_UPG_DR_LN, a tail its own comment describes as "every level past 5,
	// if the cap ever rises". It diminishes 6/5/4/3 and then pays a flat 2 per
	// level, so the extra rungs are deliberately the cheapest ones.
	// 2026-09-28 (user: "all classes should have equal upgrade level counts" + DR "5%, 3%, 2%, 2 ... " to Lv9):
	// NO class caps any more; every class takes DMG REDUCTION to 9. Was:
	// set_class_max( "dr", array( "necromancer", 3, "slasher", 5, "assault", 7, "heavy", 10 ) );
	// `pairs` is a FLAT class,max list -- see set_class_max's header for why --
	// and domain_max() reads this table BEFORE bonus_class, so sync_max and the
	// pause row's own max follow for free.
	//
	// DAMAGE NEEDS NO LINE, and that is verified rather than assumed (user:
	// "damage will go to ten like it always does"). add_domain registers
	// "damage" with max 10, class_keys undefined, and NO class_max and NO
	// bonus_class/bonus_max pair, so domain_max() falls through to d.max and
	// returns 10 for every class. A set_class_max( "damage", ... ) would be a
	// no-op that reads like a live carve-out.
	// BOUNTY (max 10) and LUCK (max 5) likewise: both are class_keys undefined,
	// so domain_available returns true on its FIRST test before the player's
	// class is ever consulted. No edits.

	// ---- DARK UPGRADES: THE EXCEPTIONS (v17.10; LUCK joined 2026-09-05) ----
	// Everything else gets one. Six are the user's own call (2026-09-03/04);
	// four are blocked and cannot be un-blocked by a number.
	//
	set_no_dark( "knifespeed" );    // 2026-09-26: the dark rung was "the PaP sword at -46%"; the sword ignores Knife Speed now (fixedSwing), so the rung did nothing - retired whole (Lua DARK_NONE[18], DARK row commented)
	set_no_dark( "distraction" );   // user: NONE
	set_no_dark( "retriever" );     // HELL'S RETRIEVER: no dark card (2026-09-26)
	set_no_dark( "bash" );          // Warrior kit cards (2026-09-26): no dark step designed
	set_no_dark( "gravsmash" );
	set_no_dark( "meleerange" );    // MELEE RANGE (2026-09-26): no dark step designed
	set_no_dark( "soulbomb" );      // Necromancer class cards (2026-09-26): no dark step designed
	set_no_dark( "summonpower" );
	set_no_dark( "soulbeam" );
	set_no_dark( "deadeye" );       // the four CORE WEAPON cards (2026-09-27): no dark step designed yet
	set_no_dark( "buckshot" );
	set_no_dark( "heavyhands" );
	foreach ( k in array( "reaperreach", "packmaster", "burnedout", "huntersmark", "aerialist", "shadowstep", "pointblank", "demolition", "bulwark", "executioner", "rhythm", "juggernaut", "pierce", "shotspeed", "sweep", "sprint", "vitality", "fusion", "demonslayer", "summonmaster", "cloak" ) )
		set_no_dark( k );   // the build cards (2026-09-27): no dark step designed
	set_no_dark( "pellets" );       // Breacher cards (2026-09-26): no dark cards, and pellets is a twin axis with no dark rung
	set_no_dark( "c4" );
	set_no_dark( "cluster" );
	set_no_dark( "suppress" );      // user: NONE (confirmed 2026-09-04)
	// set_no_dark( "drawcut" ) retired 2026-09-26 with DRAW CUT (Warrior card cut #2)
	set_no_dark( "luck" );          // user: NONE (2026-09-05, "Remove dark luck"; shipped x2.00 v17.10..v17.65)
	set_no_dark( "penetration" );   // blocked: penetrateType enum already emits its top value "large" at Lv2

	// v17.10 — MAG SIZE, HANDLING, KNIFE SPEED and RECOIL are UNPARKED. Their
	// dark rungs are real weapon variants now: gen_tod_twins.js axisMaxUp puts
	// one on the PACKED form of each class TIER 3 gun only (AK-47 r3/m4, MP7 h4,
	// Leviathan k6), paid for by the Enfield and Krig 6 dropping the r axis.
	// Ledger 220 -> 198 against the 224 guard.

	set_scope( "knifespeed", "gun" );
	set_scope( "penetration","gun" );
	// set_scope( "adrenaline", "gun" ) retired 2026-09-27: a Breacher class card now (keeps through tiers)
	set_scope( "overdrive",  "gun" );   // Peacekeeper (breacher T3, docs/157)
	// set_scope( "secondwind", "gun" ) retired 2026-09-27: a Warrior class card now (keeps through tiers)
	set_scope( "suppress",   "gun" );   // Remington 870 (breacher T2, docs/157)      — likewise
	// set_scope( "drawcut", "gun" ) retired 2026-09-26 with DRAW CUT (Warrior card cut #2)
	set_scope( "march",      "gun" );   // AK-47 (assault T3)
	// set_scope( "thunder", "gun" ) retired 2026-09-26 with THOR'S THUNDER (Warrior card cut)
	//
	// EVERYTHING ELSE PERSISTS, including several that used to reset: DAMAGE,
	// BOUNTY, GIANT SLAYER, BULLET FEED, RECOVERY, LEECH, CLEAVE, RUN AND GUN
	// and FULL STEAM (the new heavy domain; KILL RELOAD sat on this list until
	// its 2026-09-01 retirement). No set_scope call is
	// needed for any of them — that is the point of flipping the default.
	//
	// SCAVENGER WIDENED TO EVERY CLASS THAT ROLLS IT. The v14.13 line was
	// set_scope("reserve","class","assault") — a scope_class carve-out so it
	// survived for the assault ALONE. Under the v15 rule the domain is not
	// gun-specific for anybody, so the carve-out is gone and a skirmisher or heavy
	// keeps it through a promotion too. The 3-arg scope_class LANE still exists in
	// set_scope/domain_survives_tier and is still correct; it simply has no user
	// right now. Do not delete it.
	//
	// KNOWN CONSEQUENCE, flagged rather than discovered: a promotion is now nearly
	// free (a skirmisher's worst case falls from ~42 levels lost to <=11), so the
	// TIER card is close to strictly better than any other draw. That is the
	// user's call, made with the numbers in hand.
	// GUN_KEYS: a domain bound to specific gun STEMS — rollable only while the
	// player's current-tier gun is one of them. The twin ladders exist only on
	// the guns the generator built them for (a T2 SMG must never roll a dead
	// FIRE RATE card); THOR'S THUNDER is the STORMBREAKER's alone (the T3
	// slasher = the Leviathan port, stem "cc_gold_sword") — it leaves the knife's
	// pool now (user 2026-08-22 #5/#9). Add a stem here when a new tier gun
	// gets the same ladder (docs/25 §9 "reuse rule").
	// SMG CLASS UPDATE (user 2026-08-23, v9.44): FIRE RATE is the MSMC's alone
	// (the MP5's f-ladder is retired in gen_tod_twins.js). HANDLING is every
	// SMG — all three carry an h-ladder now and no gun outside the class does,
	// so its class_keys ( "skirmisher" ) is the exact gate and it needs NO
	// set_guns list (the RECOIL precedent: one less list to keep in sync).
	// MAG SIZE: every ASSAULT gun carries an m-ladder now (user 2026-08-23:
	// "mag size should be for all assault guns not just krig"). gun_keys stays
	// only because of the SKIRMISHER half — the MP7 has an m-ladder but the
	// MSMC and MP5 do not (they spend their axis budget on f/h), so dropping
	// the list would offer a dead card on two guns.
	// MAG SIZE: v9.44 the MP7 lost its m-ladder with the skirmisher class, so
	// the three assault guns are the only m-guns and class_keys ( "assault" )
	// gates it exactly — the old set_guns list existed only to keep it off the
	// MSMC/MP5 and is gone.
	// RECOIL: NO gun_keys any more (user 2026-08-23: "recoil upgrade should be
	// for all assault not just enfield and krig"). All three assault guns carry
	// an r-ladder and no gun outside the class does, so class_keys alone is the
	// exact gate. Re-add a list here only if a non-assault gun ever grows one.
	// PENETRATION IS HEAVY-ONLY AGAIN (2026-08-23): the AK-47 gave up its
	// p-ladder to pay for r+m. Three axes on one gun is 3 x 4 x 4 = 48 combos x
	// 2 forms = 96 registrations for the AK alone, which blows the boot ceiling
	// (see the LEDGER note in tools/gen_tod_twins.js). The AK loses nothing at
	// level 0 — every source GDT ships penetrateType "medium" and the p-ladder
	// STARTS at "small", so a p0 AK actually shot through LESS than every gun
	// with no ladder at all.
	// PENETRATION MOVED HK21 -> DEATH MACHINE (user 2026-08-24: "remove
	// penetration from HK21 and add to the death machine"). The p-ladder itself
	// moved with it in tools/gen_tod_twins.js and _tod_classes::register_gun —
	// this list must name exactly the guns that HAVE the axis, or the card rolls
	// on a gun with no variant to swap to.
	set_guns( "penetration", array( "cc_mozambique", "cc_peacekeeper" ) );   // TOD II (docs/157): both p-ladder guns (the 870 has no axes)
	set_guns( "knifespeed",  array( "cc_punch", "cc_gauntlet", "cc_gold_sword" ) );   // every k-ladder blade (2026-09-26: punch / gauntlet / sword)
	// set_guns( "thunder", array( "cc_gold_sword" ) ) retired 2026-09-26 with THOR'S THUNDER (Warrior card cut)
	// the uniques: one gun each (the tier ladders' T2/T3 guns)
	// v14.11 (user 2026-08-30): MOMENTUM is gone and SECOND WIND moves
	// MP7 -> MP5, so each skirmisher rung is back to ONE unique — ADRENALINE
	// on the MP7 (T3), SECOND WIND on the MP5 (T2), and the MSMC keeps its
	// f-ladder as the T1 identity. (History: 2026-08-24 swapped ADRENALINE to
	// the MP7 and narrowed MOMENTUM to the MP5; the MP7 carried two uniques
	// from then until this pass.)
	// set_guns( "adrenaline", ... cc_r99 ) retired 2026-09-27 (any weapon, Breacher)
	set_guns( "overdrive",  array( "cc_peacekeeper" ) );   // TOD II (docs/157): the Peacekeeper, rules unchanged at the user's call (was the Death Machine)
	// set_guns( "secondwind", ... cc_m1927 ) retired 2026-09-27 (any weapon, Warrior)
	// (KILL RELOAD and IMPACT ROUNDS were un-bound here on 2026-08-23 — class-
	// wide, not gun-bound, so no set_guns line for either. Both are RETIRED now:
	// IMPACT ROUNDS 2026-08-31, KILL RELOAD 2026-09-01. Nothing left to bind.)
	set_guns( "suppress",   array( "cc_rem870" ) );   // TOD II (docs/157): the 870 (was the HK21)
	// (grinder binding removed 2026-08-23 with the domain — the Death Machine
	// now carries OVERDRIVE instead.)
	// set_guns( "drawcut", array( "cc_gauntlet" ) ) retired 2026-09-26 with DRAW CUT (Warrior card cut #2)
	set_guns( "march",      array( "cc_fire_bow" ) );   // FORCED MARCH is the AK-47's alone (user 2026-08-24)
	// GRAVITY SMASH is the Warrior's tier-3 move (user 2026-09-26: "should only work
	// for the final tier"): _tod_class_kit refuses it below tier 3, so its card is not
	// dealt before then either.
	set_tier_min( "gravsmash", 3 );
}

function add_domain( key, display, desc, max, class_keys, tier, bonus_class, bonus_max )
{
	d = SpawnStruct();
	d.key = key;
	d.display = display;
	d.desc = desc;
	d.max = max;
	d.class_keys = class_keys;   // undefined = shared (every class)
	d.tier = ( ( isdefined( tier ) ) ? tier : TOD_TIER_B );
	// PER-CLASS CAP (user 2026-08-22): ONE class may out-level the domain —
	// RESERVE caps at 5 but ASSAULT reaches 6. Both undefined = same cap for
	// everyone. Read through domain_max(player,d), NEVER d.max directly in a
	// per-player context, or the bonus class silently loses its extra level.
	d.bonus_class = bonus_class;
	d.bonus_max = bonus_max;
	// CLASS TIERS: scope + gun binding (set after registration, see above)
	// v15: PERSISTENCE IS THE DEFAULT. Was "gun" (reset on a tier promotion)
	// until 2026-08-31; the exception list lives in register_domains's CLASS
	// TIERS block. A new domain therefore SURVIVES a promotion unless you say
	// otherwise — if it is gun-specific, add a set_scope(key,"gun") line there.
	d.scope = "class";
	d.scope_class = undefined;   // v14.13 — scope "class" limited to ONE class (see set_scope)
	d.gun_keys = undefined;
	d.requires = undefined;      // v16.36 — key of a domain the player must OWN before this one can roll (see set_requires)
	d.tier_min = undefined;      // docs/114 -- class-tier FLOOR before this can roll (see set_tier_min)
	d.rarity_lock = undefined;   // v16.64 — DEADSHOT: when set, make_option forces the dealt card's rarity (frame + sting) to this value AFTER its headroom clamp (see set_rarity_lock)
	level.tod_domains[ level.tod_domains.size ] = d;
}

function find_domain( key )
{
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		if ( level.tod_domains[ i ].key == key )
			return level.tod_domains[ i ];
	}
	return undefined;
}

// v14.13: the optional third arg limits a "class" scope to ONE class — the
// domain survives a tier promotion only for that class and resets like any
// gun domain for everyone else who rolls it. undefined = every class.
// GSC pads missing args with undefined, so the old 2-arg calls are unchanged.
function set_scope( key, scope, scope_class )
{
	d = find_domain( key );
	if ( isdefined( d ) )
	{
		d.scope = scope;
		d.scope_class = scope_class;
	}
}
// v16.64 (user 2026-09-02: "only way to pull it is an Ultimate card ... so we
// only need an Ultimate asset"). RARITY LOCK: every deal of `key` presents at
// rarity `r` — the ULTIMATE frame, sting and card art — regardless of the
// dice, the luck bar or the band. It is applied in make_option AFTER the
// band-honesty clamp, so a max-1 domain (DEADSHOT) keeps its +1 payout and
// still draws the ULTIMATE card; the TWO luck guarantees leave it alone by
// construction (both test `o.rarity >= want` BEFORE the headroom test, so a
// locked-3 card reads as "the dice already paid this slot" and is never
// redealt away — verified in guarantee_rarity / guarantee_both_ultimate).
// The draw FREQUENCY is not this: that is the band weight (DEADSHOT is S,
// the rarest draw).
function set_rarity_lock( key, r )
{
	d = find_domain( key );
	if ( isdefined( d ) )
		d.rarity_lock = r;
}

// =============================================================================
// DARK UPGRADES (v17.10, user 2026-09-03/04) — ONE step past a MAXED domain,
// once dealt only in the Endless Spire (both retired). docs/92_dark_upgrades_design.md is the
// record; THE NUMBERS section there is the authority for every value.
//
// THREE THINGS THAT ARE NOT NEGOTIABLE, each paid for by a trap in this file:
//
// 1. A DARK UPGRADE IS **NOT A LEVEL**. It is a per-player BIT,
//    `player.tod_dark[ key ]`. Storing it as level max+1 breaks at six sites
//    that assume `o.levels == o.rarity`, and past those at ladder5's >= 5
//    clamp, leech_hp_for_level's `default: return 10`, overdrive_total_pct's
//    `if ( lvl > 5 ) lvl = 5`, speed_pct_for_level's deceleration (a level 11
//    SPRINT pays +0.03, a quarter of the intent) and twin_suffix's unclamped
//    concatenation — every one of which fails SILENTLY and in the player's
//    disfavour.
//
// 2. IT COSTS ZERO CLIENTFIELD BITS. The pool sits at 60 of the 61
//    PROVEN-BOOTED bits (see _tod_upgrade_ui::__init__), so a per-slot rarity
//    widening does not fit. Instead the 4-bit LEVEL field carries the sentinel
//    TOD_UPG_DARK_L — levels only ever reach 10, so 11..15 are free. This is
//    the TIER card's own idiom (id 24 packs (class-1)*2 + (tier-2) into the
//    same field), not a new trick.
//
// 3. TEN DOMAINS HAVE NO DARK STEP and are marked by set_no_dark() below.
//    Six are the user's call; four are blocked (three weapon-variant ladders
//    whose rung is an ASSET against a spent registration ledger, one saturated
//    engine enum, one no-op in the retired spire). The EXCEPTIONS are listed, not the
//    27 that qualify — same shape as the set_scope block.
// =============================================================================

// A domain with no dark step. Called for the exceptions only.
function set_no_dark( key )
{
	d = find_domain( key );
	if ( isdefined( d ) )
		d.no_dark = true;
}

// Does this player hold the dark upgrade for `key`?
function has_dark( player, key )
{
	if ( !isdefined( player ) || !isdefined( player.tod_dark ) )
		return false;
	return IS_TRUE( player.tod_dark[ key ] );
}

// self = player. The read every effect lane uses, so a lane never has to know
// how the bit is stored.
function dark( key )
{
	return has_dark( self, key );
}

// Every domain this player could take a dark upgrade on RIGHT NOW: available,
// MAXED, dark-capable, and not already dark.
//
// THE MAX TEST MUST GO THROUGH domain_max(), never d.max — DMG REDUCTION is
// per-class 3/5/7/10 and SCAVENGER gives the assault a 6th level, so d.max
// would report the wrong ceiling for exactly the domains most likely to be
// maxed first.
function dark_pool( player )
{
	pool = [];
	if ( !isdefined( level.tod_domains ) )
		return pool;

	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		if ( IS_TRUE( d.no_dark ) )
			continue;
		if ( !domain_available( player, d ) )
			continue;
		if ( has_dark( player, d.key ) )
			continue;
		if ( get_level( player, d.key ) >= domain_max( player, d ) )
			pool[ pool.size ] = d;
	}
	return pool;
}

// Are dark cards live at all?
//
// ⚠️ TOD_DARK_ENABLED IS 0 WHILE THE FEATURE IS HALF-WIRED, AND THAT IS THE
// POINT. The deal path is complete — a dark card rolls, presents, and stores its
// bit correctly — but only the domains whose EFFECT LANE reads has_dark() are
// actually paid. Every other one would hand the player a card that does nothing,
// silently, which is this repo's signature failure mode and worth a hard gate
// rather than a note in a doc.
//
// FLIP IT TO 1 when the last effect lane lands. The wired list lives in one
// place only — grep has_dark( in this file — deliberately not duplicated here,
// because a hand-kept list of what is wired is exactly the thing that goes stale
// and then lies.
// 2026-09-28 (docs/187, user: "No more dark upgrades"): DARK UPGRADES ARE RETIRED. This gate
// is 0 so no dark card can ever be dealt; every has_dark() effect lane below reads a
// player.tod_dark table nothing can write, so those lanes are inert (removal pass owed).
#define TOD_DARK_ENABLED 0
function dark_allowed()
{
	if ( !TOD_DARK_ENABLED )
		return false;
	return false;   // dark cards were dealt only in the Endless Spire, retired 2026-09-29
}

// A dark card. Deliberately NOT built through make_option: every clamp in that
// function is keyed on headroom, and a dark card is by definition dealt on a
// domain with ZERO headroom — make_option would compute levels 0, the band
// clamp would demote the card to REGULAR, and apply_upgrade would refuse it.
function make_dark_option( player, domain )
{
	o = SpawnStruct();
	o.domain = domain.key;
	o.display = domain.display;
	o.desc = domain.desc;
	o.tier = domain.tier;
	o.dark = true;
	// The frame, sting and reveal HOLD all key off rarity, and a dark card
	// should build like an ultimate. The CARD ART is chosen by the sentinel
	// level, not by this.
	o.rarity = 3;
	o.rarity_name = "DARK UPGRADE";
	o.cur = get_level( player, domain.key );
	o.max = o.cur;
	o.levels = 0;   // it pays a BIT, not levels — see apply_upgrade's dark branch
	return o;
}

// THE GUARANTEE (user 2026-09-04): *"If you have an upgrade maxed then you must
// get the dark upgrade as an option after you defeat a trial and get upgrade
// rewards. If you have multiple it is possible to get both cards as dark
// upgrades but the only guarantee is that one must be a dark upgrade."*
//
// So: dark cards appeared on the TRIAL deal only (the retired spire's), and
// `level.tod_dark_guarantee` was the latch that said this deal is one; nothing
// sets it now. ONE slot was forced when the player had anything maxed.
//
// SLOT CHOICE. The dark card takes the LEFT slot. Focus starts left and a
// timeout locks the focused card, which is exactly right here — a dark upgrade
// is a pure buff, so taking it by timeout can never cost the player anything
// (the reason the TIER card is pinned to the right slot is that a weapon swap
// CAN). It also means a tier card in the right slot survives untouched, and the
// player gets the choice the design wants: promotion, or go dark.
function deal_dark( player, opts )
{
	if ( !dark_allowed() || !IS_TRUE( level.tod_dark_guarantee ) )
		return opts;

	dpool = dark_pool( player );
	if ( dpool.size == 0 )
		return opts;

	// Accepts an EMPTY hand on purpose: the fully-maxed player reaches this with
	// nothing rolled at all (roll_options' pool.size == 0 path), and they are the
	// audience the whole feature exists for.
	if ( !isdefined( opts ) )
		opts = [];
	had_tier = ( isdefined( opts[ 1 ] ) && opts[ 1 ].domain == "tier" );

	// Weighted like any other draw so a rare band stays rare even here.
	first = weighted_draw( dpool );
	opts[ 0 ] = make_dark_option( player, dpool[ first ] );

	// A SECOND dark card — never over the tier card, which owns the right slot
	// when it is dealt at all.
	//
	// v17.46 (user 2026-09-04): *"when you have max upgrades only one Dark
	// Upgrade shows up. There should still be two cards ... in no situation
	// where you are eligible for two dark upgrades should you only get one."*
	// Two rules, both enforced here:
	//  (1) STRUCTURAL — if the right slot is EMPTY (the fully-maxed player, who
	//      arrives with no regular card at all) and a second dark exists, it is
	//      dealt, full stop. Before this, the 35 % roll left that player looking
	//      at a one-card panel two times in three.
	//  (2) THE USER'S RULE — eligible for two means dealt two: TOD_DARK_BOTH_PCT
	//      is 100 now, so a regular card in the right slot is replaced by the
	//      second dark card as well. The knob is kept as a knob; the empty-slot
	//      guarantee above does NOT depend on it, so lowering it again can never
	//      bring the one-card panel back.
	if ( dpool.size > 1 && !had_tier && ( !isdefined( opts[ 1 ] ) || RandomInt( 100 ) < TOD_DARK_BOTH_PCT ) )
	{
		rest = [];
		for ( i = 0; i < dpool.size; i++ )
		{
			if ( i == first )
				continue;
			rest[ rest.size ] = dpool[ i ];
		}
		opts[ 1 ] = make_dark_option( player, rest[ weighted_draw( rest ) ] );
	}
	return opts;
}

// v16.36 (user 2026-09-02: "you may not have the upgrade that allows shooting
// while running ... sequence it correct where you cant get those specific
// upgrades until you have [sprint fire]"). PREREQUISITE: `key` can only be
// ROLLED once the player owns at least one level of `prereq_key`. Read by
// domain_available, which is the single gate under eligible_pool (the deal and
// the luck-floor redeal), player_has_domains_left (the station's "anything to
// sell?" test) and the deferred-card revalidation — so the dependent card
// never appears anywhere before the prerequisite is owned.
//
// REGISTRATION ORDER IS LOAD-BEARING: the grant-all lane (dev_grant_maxed
// here) walks level.tod_domains in
// registration order through domain_available, so the prerequisite must be
// registered BEFORE its dependent or the grant skips the dependent on the one
// pass it gets. Checked here, at init, rather than trusted.
function set_requires( key, prereq_key )
{
	d = find_domain( key );
	p = find_domain( prereq_key );
	if ( !isdefined( d ) || !isdefined( p ) )
	{
		/# PrintLn( "^1[tod] set_requires( " + key + ", " + prereq_key + " ): unknown domain — prerequisite NOT installed" ); #/
		return;
	}
	if ( domain_index( prereq_key ) > domain_index( key ) )
	{
		/# PrintLn( "^1[tod] set_requires( " + key + ", " + prereq_key + " ): prerequisite registered AFTER its dependent — the grant-all lanes would skip " + key ); #/
	}
	d.requires = prereq_key;
}

// PUBLIC (docs/114) -- declare a CLASS-TIER FLOOR: this domain cannot be ROLLED
// until the player's class tier reaches `t`. Read only by domain_available,
// which is the single gate under eligible_pool, dark_pool,
// player_has_domains_left, dev_grant_maxed and
// solo_refresh_option -- so a floored card never appears anywhere before the
// tier that earns it.
//
// WHY THIS AND NOT set_guns. gun_keys gates on the CURRENT-TIER gun stem, so
// a card bound to one tier's gun becomes UNROLLABLE the moment the player is
// promoted. This is a floor: a card earned at tier 2 is still rollable at
// tier 3.
//
// A floor can never strand a level. Levels persist across a promotion by
// default (the v15 rule) and tier() only ever rises.
//
// tod_classes::tier() returns 1 for a classless or un-promoted player, so an
// unset floor and a pre-draft player both fall through unchanged. One caller
// today: GRAVITY SMASH ( set_tier_min( "gravsmash", 3 ) in register_domains ).
function set_tier_min( key, t )
{
	d = find_domain( key );
	if ( isdefined( d ) )
		d.tier_min = t;
}

function domain_index( key )
{
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		if ( level.tod_domains[ i ].key == key )
			return i;
	}
	return -1;
}

// v14.13 — does THIS player's copy of the domain survive a tier promotion?
// The single authority: tier_up's reset loop skips on it, and sync_max()
// stamps it into every pause-menu row so the reset badge can never disagree
// with what tier_up will actually do. A classless player (pre-draft) fails
// the scope_class test and keeps nothing — irrelevant in practice, since no
// promotion can happen before the draft.
function domain_survives_tier( player, d )
{
	if ( !isdefined( d.scope ) || d.scope != "class" )
		return false;
	if ( isdefined( d.scope_class ) )
		return ( isdefined( player.tod_class ) && player.tod_class == d.scope_class );
	return true;
}

// v14.13 — the max arg every tod_upg_sync send must carry: the per-player cap
// plus TOD_SYNC_SAFE_FLAG when the domain survives promotion FOR THIS PLAYER.
// One owner. Reset rows come out plain
// by construction (they are being reset precisely because survives is false).
function sync_max( player, d )
{
	mx = domain_max( player, d );
	if ( domain_survives_tier( player, d ) )
		mx += TOD_SYNC_SAFE_FLAG;
	if ( has_dark( player, d.key ) )
		mx += TOD_SYNC_DARK_FLAG;   // v17.10 — the pause row needs to print the DARK value, not the maxed one
	return mx;
}

function set_guns( key, stems )
{
	d = find_domain( key );
	if ( isdefined( d ) )
		d.gun_keys = stems;
}

// PUBLIC (v17.3) — declare a PER-CLASS level cap for a domain. Read by
// domain_max BEFORE bonus_class, and by sync_max, so the pause menu's own max
// readout follows it for free.
//
// `pairs` is a FLAT list — class, max, class, max — because GSC's array()
// builds a NUMERIC-INDEXED array, not a keyed map: array( "heavy", 10 ) is
// [0]="heavy", [1]=10, and a lookup by class name on it returns undefined.
// The keyed map is built here instead, which keeps the call site one line and
// puts the one place that could get this wrong behind a function.
//
// The domain's own `max` stays the CEILING across all classes — the
// All-domains table and any player-less caller read that — so keep it equal to
// the largest entry here or the registry will under-report the domain.
function set_class_max( key, pairs )
{
	d = find_domain( key );
	if ( !isdefined( d ) || !isdefined( pairs ) )
		return;
	caps = [];
	for ( i = 0; i + 1 < pairs.size; i += 2 )
		caps[ pairs[ i ] ] = pairs[ i + 1 ];
	d.class_max = caps;
}

// (killreload_kills_needed() lived here until KILL RELOAD was retired 2026-09-01.)

// The cap for THIS player (honours a domain's per-class bonus).
function domain_max( player, d )
{
	// PER-CLASS CAP TABLE (v17.3) — checked FIRST, and it is the general form
	// the bonus_class/bonus_max pair below could never express: that lane maps
	// ONE alternate max onto a set of classes, so it cannot say
	// "3 / 5 / 7 / 10, one per class". DMG REDUCTION is the first domain that
	// needs four different numbers; set_class_max() is how a domain declares
	// them. A class absent from the table falls through to the rules below, so
	// a partial table is legal.
	if ( isdefined( d.class_max ) && isdefined( player.tod_class )
	  && isdefined( d.class_max[ player.tod_class ] ) )
		return d.class_max[ player.tod_class ];

	// bonus_class is EITHER a single key OR an array of keys (v14.33 — the DR
	// cap now covers slasher AND skirmisher). Array form first; a bare string
	// still works, which is what SCAVENGER's "assault" uses.
	if ( isdefined( d.bonus_class ) && isdefined( d.bonus_max ) && isdefined( player.tod_class ) )
	{
		if ( IsArray( d.bonus_class ) )
		{
			foreach ( c in d.bonus_class )
			{
				if ( player.tod_class == c )
					return d.bonus_max;
			}
		}
		else if ( player.tod_class == d.bonus_class )
			return d.bonus_max;
	}
	return d.max;
}

// Can this player roll this domain right now?
function domain_available( player, d )
{
	// GUN-BOUND domains (twin ladders, per-gun uniques, Thor's Thunder): only
	// while the player's current-tier gun is one of the listed stems.
	if ( isdefined( d.gun_keys ) )
	{
		stem = tod_classes::gun_stem( player );
		if ( !isdefined( stem ) )
			return false;
		ok = false;
		foreach ( s in d.gun_keys )
		{
			if ( s == stem )
				ok = true;
		}
		if ( !ok )
			return false;
	}
	// PREREQUISITE (v16.36): not rollable until the player OWNS the domain it
	// builds on — RUN AND GUN after SPRINT FIRE (see set_requires). Checked
	// before the class test so a dependent domain is dark for every lane that
	// asks this question, not just the deal.
	if ( isdefined( d.requires ) && get_level( player, d.requires ) <= 0 )
		return false;
	// CLASS-TIER FLOOR (docs/114) -- set_requires' sibling. Checked here, beside
	// the prerequisite, so a floored domain is dark for EVERY lane that asks
	// this question and not just the deal.
	if ( isdefined( d.tier_min ) && tod_classes::tier( player ) < d.tier_min )
		return false;
	if ( !isdefined( d.class_keys ) )
		return true;
	if ( !isdefined( player.tod_class ) )
		return false;
	foreach ( k in d.class_keys )
	{
		if ( k == player.tod_class )
			return true;
	}
	return false;
}

// ---------------------------------------------------------------------------
// Per-player state
// ---------------------------------------------------------------------------

// self = player (on_spawned; fields persist across respawns, only init once)
function player_upgrade_setup()
{
	self thread ensure_upgrade_list();

	// THE TIER GATE TOASTS (2026-09-02) — once per player; the thread endons
	// only on disconnect, so it rides through every respawn.
	if ( !IS_TRUE( self.tod_tier_toasts_on ) )
	{
		self.tod_tier_toasts_on = true;
		self thread tier_gate_toasts();
	}

	if ( !isdefined( self.tod_levels ) )
	{
		self.tod_levels = [];
		for ( i = 0; i < level.tod_domains.size; i++ )
			self.tod_levels[ level.tod_domains[ i ].key ] = 0;
		// (the LUCK BAR — player.tod_luck_bar — is owned by _tod_luck.gsc)
	}
	if ( !isdefined( self.tod_tier ) )
		self.tod_tier = 1;   // CLASS TIERS: everyone starts at tier 1 (survives respawns like tod_levels)

	// (mag_watcher REMOVED 2026-08-20 — MAG SIZE is real twin variants now,
	// no virtual pool; the todMagBonus clientfield stays registered but 0.)

	// BASE 150 HP (user 2026-08-20) + VITALITY (v14.11: +10/Lv rides the same
	// floor). Stock jugg is ADDITIVE on the current maxhealth and restores
	// preMaxHealth on loss (_zm_perks.gsc:801/848), so raising the base
	// BEFORE jugg stacks cleanly (jugg = floor + bonus). The body loop below
	// maintains it against stock 100-resets; only the spawn grant heals the
	// difference (the maintain never free-heals) — so a respawning heavy
	// comes back with their vitality HP filled, same doctrine as the base 150.
	// (tod_levels is initialised above, so get_level is safe here.)
	want = self max_hp_floor();
	if ( self.maxhealth < want )
	{
		self.maxhealth = want;
		self SetMaxHealth( want );
		if ( self.health < want )
			self.health = want;
	}

	if ( !IS_TRUE( self.tod_body_systems_on ) )
	{
		self.tod_body_systems_on = true;
		self thread body_systems_loop();
		self thread recovery_loop();          // RECOVERY (v14.11) — its own 0.1s cadence
		self thread recovery_damage_watch();  // exact last-hit stamps for it
		// v14.16 — runs for EVERY player, not just RECOVERY holders: VITALITY's
		// purchase heal desyncs the same vignette. See the block comment.
		self thread health_overlay_sync();
		// (tireless_spawn_watch removed 2026-08-26 with TIRELESS itself.)
	}

	// move scale must be re-applied on every spawn (it resets)
	self apply_move_speed();
}

// ---------------------------------------------------------------------------
// self = player. THE ONE OWNER of "what should this player's max HP be at
// minimum, right now" (v14.28) — the spawn grant and the body-loop maintain
// both read it; never re-spell the sum at a call site (the jugg term is the
// part a copy silently drops).
//
//   150 base + 10 x VITALITY level + (active jugg ? its bonus : 0)
//
// THE JUGG TERM IS THE v14.28 FIX (user: "I have 210 but level 3 vitality...
// went back down to 200"): stock's health_reboot rebuilds max from
// player_base_health on every round flip / revive / jugg loss, discarding
// vitality. A jugg-blind floor (180 at Lv3) sat BELOW the rebuilt 200, so the
// raise-only maintain was satisfied while 80 real HP were missing. Counting
// the active jugg makes the floor 280 there, and the maintain repairs within
// a second of any stock clobber. Entry main() pins player_base_health to 150
// (v14.28, lockstep with TOD_UPG_BASE_HP) so the reboot itself now lands at
// 250 with jugg — the floor covers what stock cannot know about: VITALITY.
//
// HasPerk only — a PAUSED jugg (power down, machine moved) reads false here,
// which is correct: stock restored the pre-jugg max on pause, and raise-only
// means resume's re-add is never fought. The bonus rides the zombie_var so a
// future jugg retune has one owner too (isdefined-guarded: the var is seeded
// by _zm_perk_juggernaut's autexec init, which beats every caller of this).
// VITALITY's max health for a level (user 2026-09-28: "It should go up by 10,9,8,7,6,5,4,4,4 HP
// each level"): 10 / 19 / 27 / 34 / 40 / 45 / 49 / 53 / 57. LOCKSTEP tod_upgrade.lua DETAIL[37].
function vitality_hp( lv )
{
	steps = array( 10, 9, 8, 7, 6, 5, 4, 4, 4 );
	if ( !isdefined( lv ) || lv <= 0 ) return 0;
	if ( lv > steps.size ) lv = steps.size;
	hp = 0;
	for ( i = 0; i < lv; i++ ) hp += steps[ i ];
	return hp;
}

function max_hp_floor()
{
	// VITALITY is the WARRIOR's since 2026-09-27 (class pass 2): 9 levels on a falling ladder
	// since 2026-09-28 (vitality_hp; it rode ladder5 as the Breacher's 5-level card until 2026-09-26).
	floor = TOD_UPG_BASE_HP + vitality_hp( class_live_level( self, "vitality" ) );   // asleep in another class (2026-10-01)
	// SUMMONER MASTER (Necromancer, 2026-09-27): max health earned from helper kills,
	// banked by _tod_class_cards (tod_summon_hp, already capped by level and tier).
	if ( isdefined( self.tod_class ) && self.tod_class == "necromancer" && isdefined( self.tod_summon_hp ) )
		floor += self.tod_summon_hp;
	// DARK UPGRADE (v17.10): +25 flat HP. Applied HERE and not inside ladder5(),
	// which is shared with RECOVERY and BACK ARMOR -- moving the table would drag
	// both of those with it, and BACK ARMOR multiplies with DR.
	if ( has_dark( self, "vitality" ) && class_live_level( self, "vitality" ) > 0 )
		floor += TOD_DARK_VITALITY_HP;
	if ( self HasPerk( "specialty_armorvest" ) )   // PERK_JUGGERNOG (_zm_perks.gsh — not #insert'd here)
	{
		jugg = 100;
		if ( isdefined( level.zombie_vars ) && isdefined( level.zombie_vars[ "zombie_perk_juggernaut_health" ] ) )
			jugg = level.zombie_vars[ "zombie_perk_juggernaut_health" ];
		floor += jugg;
	}
	return floor;
}

// ---------------------------------------------------------------------------
// BODY DOMAINS (persist across class switches — trained on the player):
// SPRINT/MOBILITY (move scale), HEALTH (max HP maintain,
// jugg-aware), REGEN (trickle heal), BULLET FEED (reserve -> mag). 1s cadence.
// ---------------------------------------------------------------------------

function apply_move_speed()
{
	// Menu soft-freeze pins movement (see menu_freeze below).
	if ( IS_TRUE( self.tod_menu_frozen ) )
	{
		self SetMoveSpeedScale( 0.001 );
		return;
	}
	// THIS SUM IS SPRINT + FORCED MARCH ONLY, and that pair is what "summing the
	// levels is safe" refers to: SPRINT is skirmisher/slasher, FORCED MARCH is
	// assault, so no player can hold both and adding their levels can never
	// double-count. The other speed sources are SEPARATE TERMS in the scale
	// expression below, each with its own gate — LMG SPRINT (heavy,
	// conditional) and ADRENALINE (skirmisher, timed burst).
	// ATHLETE (slasher) is NOT in this expression at all since v16.1: it is a
	// pure VELOCITY mechanic in _tod_athlete.gsc (slide start speed, jump z, the
	// slide-jump carry) and never touches the scale. It used to add +0.10/Lv
	// here while IsSliding(); that lane was retired because the engine's slide
	// is not input-driven, so a scale term could not honestly be "+10% slide
	// speed" — see the header of _tod_athlete.gsc.
	//
	// DO NOT ADD A DOMAIN TO THIS SUM WITHOUT CHECKING CLASS OVERLAP. The old
	// wording here said the speed domains were per-class "so no player can hold
	// two", which was true when only SPRINT/MARCH/MOBILITY existed and is FALSE
	// now: a slasher can hold SPRINT and ATHLETE at once. Nothing is broken by
	// that — ATHLETE never enters this sum — but the sentence was one edit away
	// from inviting someone to fold a same-class domain in here on the strength
	// of a guarantee that had quietly stopped holding.
	// (MOBILITY was the heavy's entry here until v15; it is retired, replaced by
	// the conditional LMG SPRINT below. get_level on a retired domain returns 0,
	// so dropping it from this sum is cosmetic — but a term that can only ever
	// be zero is how the next reader loses an hour.)
	//
	// ⚠️ SPEED BONUSES ARE ADDED TO THE SCALE, NOT MULTIPLIED INTO IT (v15,
	// 2026-08-31 — user: "if lmg has 80 speed then should boost up to .85 if
	// they get 5% it shouldnt be 5% of 0.8"). So "+5%" means +0.05 of SCALE, a
	// flat five points, identical for every class. It used to be
	// base * (1 + bonus), which paid the fast classes more for the same card:
	// +5% was worth 0.055 to a skirmisher and 0.0375 to a heavy, quietly
	// widening the gap the speed cards are supposed to help close.
	//
	// CEILINGS UNDER THIS MODEL (base + max ladder), for anyone recomputing
	// balance: heavy 0.80 + 0.216 = 1.016 while rolling (FULL STEAM = ladder x TOD_LMGS_MULT, v16.8) · assault 0.90 + 0.18 =
	// 1.08 · slasher 1.00 + 0.33 = 1.33 · skirmisher 1.10 + 0.33 = 1.43, plus
	// ADRENALINE's burst on top of that.
	// SPRINT is the ARCHER's since 2026-09-27 (class pass 2, user: "faster sprint per
	// level"): the same ladder, counted ONLY while tod_sprint_hot (_tod_class_cards
	// latches it on IsSprinting edges and re-applies this function).
	// 2026-09-28 (user: "the sprint ladder, make sure it's logarithmic ... 30 points at level 9 ... the
	// increase in speed shouldn't be linear"): SPRINT has its own log curve (sprint_card_bonus) and no
	// longer rides the shared 5/4/3/3... ladder, which was linear from Lv2.
	lvl = get_level( self, "march" );
	scale = self class_speed_base()
	      + speed_pct_for_level( lvl )
	      + self sprint_card_bonus()
	      + self dark_speed_bonus()
	      + self adren_bonus()
	      + self archer_land_speed_bonus()    // ARCHER grapple landing burst (2026-09-25)
	      + self class_card_speed_bonus();    // SHADOWSTEP (2026-09-27, _tod_class_cards writes the fields)
	// (the boss zap slow was removed 2026-08-20 — no player stuns)
	self SetMoveSpeedScale( scale );
}

// PUBLIC — the MOVE SPEED LADDER (v15 item 25). Cumulative bonus for `lvl`
// levels of any speed domain, as an ADDITIVE offset to the move-speed scale.
//
// Increments are 5, 4, 3, 3, 3, ... so the totals run
//   Lv1 .05 · Lv2 .09 · Lv3 .12 · Lv4 .15 · Lv5 .18 · ... · Lv10 .33
// A closed form rather than a table so it cannot go out of range: SPRINT caps
// at 10 today but nothing here breaks if a domain is ever given more.
//
// THE ONE OWNER. Every speed domain routes through this — do not reintroduce a
// per-level constant, and do not let a caller multiply by it.
// (ONE sanctioned exception, v16.8: lmg_sprint_bonus() multiplies the result by
// TOD_LMGS_MULT - FULL STEAM's own +20%, a user order - mirrored by
// fullSteamPct() in tod_upgrade.lua. SPRINT and FORCED MARCH stay raw.)
function speed_pct_for_level( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 0 )
		return 0;
	if ( lvl == 1 )
		return TOD_UPG_SPEED_L1;
	return TOD_UPG_SPEED_L1 + TOD_UPG_SPEED_L2 + ( lvl - 2 ) * TOD_UPG_SPEED_LN;
}

// PUBLIC - the 9-level card curve ln( 1 + lvl ) / ln( 10 ): 0 at Lv0, 1 at Lv9, big early steps and every
// level still worth something (Lv1 .30 / Lv2 .48 / Lv3 .60 ... Lv8 .95). Tabulated (no log native).
// The same numbers as tod_archer::grapple_curve and the Lua CARD_CURVE.
function card_curve( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 0 ) return 0;
	if ( lvl >= 9 ) return 1;
	c = array( 0, 0.301, 0.4771, 0.6021, 0.699, 0.7782, 0.8451, 0.9031, 0.9542, 1 );
	return c[ lvl ];
}

// SPRINT (the ARCHER's, 9 levels; LOGARITHMIC since 2026-09-28): points of move-speed scale while sprinting,
// TOD_SPRINT_CARD_MAX x card_curve = 9.0 / 14.3 / 18.1 / 21.0 / 23.3 / 25.4 / 27.1 / 28.6 / 30.0 at Lv1..9
// (was 5 / 9 / 12 ... +3 a level, linear from Lv2). LOCKSTEP tod_upgrade.lua sprintPct.
function sprint_card_bonus()
{
	if ( !IS_TRUE( self.tod_sprint_hot ) )
		return 0;
	return TOD_SPRINT_CARD_MAX * card_curve( get_level( self, "sprint" ) );
}

// PUBLIC — THE SHARED 5-TIER LADDER (v16). Cumulative value at `lvl`:
//   Lv1 10 · Lv2 18 · Lv3 24 · Lv4 28 · Lv5 32
// Unit-agnostic (see the #define block): percent for RECOVERY and BACK ARMOR,
// FLAT HP for VITALITY. THE ONE OWNER — do not re-spell the table.
function ladder5( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 0 ) return 0;
	if ( lvl == 1 ) return TOD_LADDER5_L1;
	if ( lvl == 2 ) return TOD_LADDER5_L2;
	if ( lvl == 3 ) return TOD_LADDER5_L3;
	if ( lvl == 4 ) return TOD_LADDER5_L4;
	return TOD_LADDER5_L5;
}

// LMG SPRINT (domain 42, v15 item 24 — user 2026-08-31: "an LMG upgrade where
// when you run max speed for 1.5s you get a speed boost"). The heavy's
// replacement for MOBILITY: nothing at a standstill, the full ladder once the
// party's slowest class has been running flat out for TOD_LMGS_ARM_MS.
//
// Shaped exactly like adren_bonus() — a level lookup plus a latch this function
// only READS. The latch is armed by the 20 Hz sustained-sprint watcher in
// _tod_uniques.gsc, which also edge-calls apply_move_speed() so the boost
// arrives on the frame it is earned rather than on the next 1 s body tick.
//
// FREIGHT-TRAIN IDENTITY, deliberately: the heavy is the slowest class from a
// standstill (0.80) and one of the fastest once rolling (1.016 at Lv5 since v16.8 - the ladder x TOD_LMGS_MULT). Losing
// sprint — a corner, a hit, a reload-strafe — drops the whole bonus and the
// 1.5 s clock restarts.
// (ATHLETE's athlete_slide_bonus() + TOD_ATH_SLIDE_PER_LV lived here from v16
// until v16.1, 2026-09-01. The slide-speed number now lives in _tod_athlete.gsc
// as a velocity multiply on the slide-start edge, and the self.tod_athlete_sliding
// flag no longer exists — nothing in this file should read it.)

// DARK UPGRADES (v17.10) — SPRINT and FORCED MARCH, as a SEPARATE ADDEND rather
// than extra levels in the sum above. That is not a style choice: this ladder
// DECELERATES (TOD_UPG_SPEED_LN is 0.03 against L1's 0.05), so a dark step
// expressed as levels would pay a fraction of its intent and would do it
// silently. Points of SCALE, matching the model documented above.
//
// The two can never both be held — SPRINT is skirmisher/slasher, FORCED MARCH is
// assault — but they are summed rather than branched so that stops being a
// correctness assumption the next class change could quietly break.
function dark_speed_bonus()
{
	b = 0;
	if ( has_dark( self, "sprint" ) )
		b += TOD_DARK_SPEED_ADD;    // +33% -> +48% of move scale
	if ( has_dark( self, "march" ) )
		b += TOD_DARK_MARCH_ADD;    // +18% -> +35%
	return b;
}

// PUBLIC — ADRENALINE's proc cue (v16). self = player.
// PlayLocalSound, NOT PlaySound: the user asked for "a 2d sound only heard by
// the player". PlaySound emits from the player ENTITY and carries to teammates
// in earshot; PlayLocalSound plays only for that client, which is what a sound
// representing your OWN pulse should do. The alias is 2d for the same reason —
// it has no world position to attenuate from.
// Pitch variation lives in the alias row (0.94/1.06), not here: this fires
// every 6-10s for a whole run and identical repeats are what turn a cue into
// an irritant.
function adren_fx()
{
	if ( !isdefined( self ) || !isplayer( self ) )
		return;
	self PlayLocalSound( TOD_ADREN_SFX );
}

// DMG REDUCTION — THE LADDER. Returns the CUMULATIVE percent reduction at
// `lvl`: 6 / 11 / 15 / 18 / 20 at Lv1..Lv5, from increments 6/5/4/3/2.
//
// A closed form rather than a table so it cannot go out of range if the cap is
// ever raised — same discipline as speed_pct_for_level(), and note this is a
// SEPARATE table from ladder5() (10/18/24/28/32, used by RECOVERY / BACK ARMOR
// / VITALITY). The two look alike and must not be merged: they were given
// different shapes by the user on purpose.
//
// UNIT-AGNOSTIC: returns a plain number of PERCENT. dr_mult() below is the only
// thing that turns it into a multiplier.
function dr_pct_for_level( lvl )
{
	if ( !isdefined( lvl ) || lvl <= 0 )
		return 0;
	if ( lvl == 1 )
		return TOD_UPG_DR_L1;
	if ( lvl == 2 )
		return TOD_UPG_DR_L1 + TOD_UPG_DR_L2;
	if ( lvl == 3 )
		return TOD_UPG_DR_L1 + TOD_UPG_DR_L2 + TOD_UPG_DR_L3;
	if ( lvl == 4 )
		return TOD_UPG_DR_L1 + TOD_UPG_DR_L2 + TOD_UPG_DR_L3 + TOD_UPG_DR_L4;
	return TOD_UPG_DR_L1 + TOD_UPG_DR_L2 + TOD_UPG_DR_L3 + TOD_UPG_DR_L4
	     + ( lvl - 4 ) * TOD_UPG_DR_LN;
}

// PUBLIC — DMG REDUCTION: the incoming-damage multiplier for `player` right
// now. 1.0 unless they own the domain. Both of _tod_bosses' player-damage lanes
// multiply by this: boss_player_damage for the normal chain, and
// apply_player_mitigations for Panzer melee, which short-circuits that chain.
//
// ⚠️ THIS FUNCTION EXISTS TO END A HAND-COPY. Until v16 those two lanes carried
// bare `1.0 - 0.05 * dr_lvl` literals, because a GSC #define is FILE-LOCAL and
// the constant in this file could not reach them — so the constant was
// "documentation" and the real numbers lived in two places that had already
// drifted once (one of them still said "-4%" months after the retune). The v16
// diminishing ladder cannot be written as a literal multiply at all, which
// forced the fix that should always have been here. Call this; never re-derive.
// Floored so a future cap raise can never reach zero or invert.
function dr_mult( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return 1.0;
	// ARCHER LANDING (2026-09-25): a grapple touch-down grants a short window of
	// damage reduction (_tod_archer sets the two fields). It MULTIPLIES with
	// DMG REDUCTION rather than adding, so it can never push the total to zero.
	land = archer_land_mult( player );
	// THE CLASS BUILD CARDS (2026-09-27): BULWARK / JUGGERNAUT / SOUL SIPHON's window,
	// multiplied like the landing window (_tod_class_cards::taken_mult, a level pointer).
	if ( isdefined( level.tod_cc_dr_fn ) )
		land = land * [[ level.tod_cc_dr_fn ]]( player );
	lvl = get_level( player, "dr" );
	if ( lvl <= 0 )
		return land;
	pct = dr_pct_for_level( lvl );
	// DARK UPGRADE (v17.10): a flat +10 POINTS on top of the class cap, so every
	// class gets the same step off a different base -- 15/20/24/30 -> 25/30/34/40.
	if ( has_dark( player, "dr" ) )
		pct += TOD_DARK_DR_ADD;
	m = 1.0 - ( pct / 100.0 );
	if ( m < 0.05 )
		m = 0.05;
	return m * land;
}

// Archer landing window: fields written by _tod_archer (no #using either way).
function archer_land_active( player )
{
	return isdefined( player.tod_archer_land_until ) && GetTime() < player.tod_archer_land_until;
}

function archer_land_mult( player )
{
	if ( !archer_land_active( player ) || !isdefined( player.tod_archer_land_dr ) )
		return 1.0;
	return 1.0 - ( player.tod_archer_land_dr / 100.0 );
}

// SHADOWSTEP's burst (fields written by _tod_class_cards; no #using either way).
function class_card_speed_bonus()
{
	b = 0;
	now = GetTime();
	if ( isdefined( self.tod_cc_speed_until ) && now < self.tod_cc_speed_until && isdefined( self.tod_cc_speed ) )
		b += self.tod_cc_speed;
	// DEMON SLAYER (Warrior, 2026-09-27): an elite kill's window
	if ( isdefined( self.tod_demon_until ) && now < self.tod_demon_until && isdefined( self.tod_demon_speed ) )
		b += self.tod_demon_speed;
	return b;
}

function archer_land_speed_bonus()
{
	if ( !archer_land_active( self ) || !isdefined( self.tod_archer_land_speed ) )
		return 0;
	return self.tod_archer_land_speed / 100.0;
}

// PUBLIC — SPRINT ARMOR (v9.28): the incoming-damage multiplier for `player`
// right now. 1.0 unless the player owns the domain AND the engine says they
// are sprinting at this instant (IsSprinting — the server-side builtin). Both
// of _tod_bosses' player-damage lanes (boss_player_damage for the normal
// chain, apply_player_mitigations for Panzer melee) multiply by this right
// after DMG REDUCTION. Floored so a future level bump can never reach zero.
// ⚠️ ALWAYS RETURNS 1.0 SINCE 2026-08-31 — the SPRINT ARMOR domain was retired
// and get_level can no longer report a level for it. Kept, not deleted, because
// _tod_bosses calls it from both player-damage lanes; the multiply is now a
// permanent identity. Delete the function and its two call sites together, or
// not at all.
function sprint_armor_mult( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return 1.0;
	lvl = get_level( player, "sprintarmor" );
	if ( lvl <= 0 )
		return 1.0;
	if ( !( player IsSprinting() ) )
		return 1.0;
	m = 1.0 - TOD_UPG_SPRINT_ARMOR_PER_LVL * lvl;
	if ( m < 0.05 )
		m = 0.05;
	return m;
}

// PUBLIC — the map's ONE definition of "is this hit a HEADSHOT". Returns
// "loc"       the ENGINE already scored it as a head hit (hitLoc head/helmet/
//             neck) and has therefore ALREADY applied the 3.0 hit-location
//             multiplier before any script saw the damage;
// "none"      anything else.
// (The third answer, "faceplate" — a hit on the PANZER's visor, which stock
// scores as torso_upper — retired with the Panzer, 2026-10-05: no other enemy
// carries j_faceplate. The note below is its history.)
//
// WHY THIS EXISTS (user 2026-08-24: "some guns will get headshots even when
// [the faceplate] is on"). Two guns aimed at the SAME point on the Panzer's
// face can produce different hitLocs, and the map then paid them differently:
// a "head" hit was worth 2.7x base while a visor hit was worth 0.9x — a silent
// 3x gap between weapons, plus no crit number, no HEADSHOT domain and no 1.5x
// luck on the visor hit. Callers must treat "faceplate" as a headshot and
// supply the missing 3.0 themselves (the Panzer's own damage wrap did).
function headshot_kind( victim, hitloc, point )
{
	if ( isdefined( hitloc ) && ( hitloc == "head" || hitloc == "helmet" || hitloc == "neck" ) )
		return "loc";
	return "none";
}

// PUBLIC — the map's ONE definition of "boss or elite". The triad is set
// synchronously on the spawn frame by the Mangler, the Doppelghast and the Dealer
// (the Panzer, the Rogue Protector and the Reaver that first set it retired whole
// 2026-10-05), and nine systems gate on it. Call this instead of re-spelling three fields.
function is_boss_or_elite( ent )
{
	if ( !isdefined( ent ) )
		return false;
	return ( IS_TRUE( ent.is_boss ) || IS_TRUE( ent.acc_is_boss ) || IS_TRUE( ent.acc_is_mini_boss ) );
}

// PUBLIC — HEADSHOT (domain 6): the ADDITIVE damage bonus this attacker gets on
// a HEAD HIT. The CALLER owns the "was this a head hit" test — both lanes have
// already answered it by the time they add this, and neither has a hitLoc to
// hand over — so this function owns the RATE and the DARK step and nothing else.
//
// IT EXISTS BECAUSE THE ALTERNATIVE ALREADY FAILED. _tod_bosses::rp_damage_feed
// carried a literal copy of TOD_UPG_HS_PER_LVL (a GSC #define is file-local, so
// that lane could not see the symbol), the 2026-08-22 nerf missed it, and a
// headshot on the Rogue Protector paid 2.5x for a day. GIANT SLAYER dodged the
// same fate by being a function from the start — boss_damage_bonus, right
// below. This is that fix applied to the one domain still doing it by hand
// (2026-09-08, the +12%/Lv x 5-level pass). Do not re-introduce a literal.
function headshot_bonus( attacker )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) )
		return 0;
	b = get_level( attacker, "headshot" ) * TOD_UPG_HS_PER_LVL;
	if ( has_dark( attacker, "headshot" ) )
		b += TOD_DARK_HS_ADD;   // DARK: +60% -> +85% on a head hit
	return b;
}

// PUBLIC — GIANT SLAYER (domain 35, v9.45): the ADDITIVE damage bonus this
// attacker gets against this victim. 0 unless the victim carries the boss/elite
// triad AND the attacker owns the domain, so every call site can add it
// unconditionally. BOTH boss-damage lanes call it — upgrade_damage_cb (the
// actor chain, which is what fires for the Panzer and the Reaver) and
// _tod_bosses::rp_damage_feed (the Rogue Protector's aiOverrideDamage
// fallback). Exposing it as a function instead of a constant is deliberate:
// rp_damage_feed cannot see a file-local #define, and every hand-copied
// literal in that lane has gone stale at least once.
function boss_damage_bonus( attacker, victim )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) )
		return 0;
	if ( !is_boss_or_elite( victim ) )
		return 0;
	b = get_level( attacker, "bossdmg" ) * TOD_UPG_BOSSDMG_PER_LVL;
	if ( has_dark( attacker, "bossdmg" ) )
		b += TOD_DARK_BOSSDMG_ADD;   // DARK: +60% -> +80% vs the boss/elite triad
	return b;
}

// PUBLIC — MELEE vs the boss/elite triad (user 2026-08-24). The MULTIPLIER a
// melee hit on `victim` pays: TOD_MELEE_BOSS_MULT_SLASHER if `attacker` is a
// SLASHER, TOD_MELEE_BOSS_MULT for every other class, 1.0 against a non-triad
// victim and 1.0 for any non-melee hit. See the #defines for the split.
//
// ⚠️ THE ATTACKER PARAMETER IS v18.3 AND ALL FOUR CALL SITES PASS IT. It was
// (victim, is_melee) for two years of sessions, so a hand-written call copied
// from an old file will silently pass the VICTIM as the attacker - which fails
// the isplayer test and quietly hands back the non-slasher rate rather than
// throwing. The arity lint catches the shape; nothing catches the meaning.
//
// PUBLIC for the same reason boss_damage_bonus is: _tod_bosses::rp_damage_feed
// is a SECOND damage lane in another file, a GSC #define is file-local, and
// every hand-copied literal in that lane has gone stale at least once. Call
// this; never re-spell the 0.5 or the triad test.
//
// THREE CALL SITES, and all three are needed:
//   1. upgrade_damage_cb   — the main actor chain (covers the Panzer, whose
//                            hit-location wrap passes melee through untouched,
//                            and the Reaver, which has no lane of its own).
//   2. cleave_splash       — a CLEAVE extra target re-enters upgrade_damage_cb
//                            already marked tod_cleave_hit, which passes through
//                            untouched by design, so the splash has to scale
//                            itself or a slasher could tag a normal zombie and
//                            splash a boss for the full swing.
//   3. rp_damage_feed      — the Rogue Protector's fallback lane, for the hits
//                            that do not go through the actor chain.
// PUBLIC — the multiplier a SLASHER'S SIDEARM pays against the boss/elite
// triad: TOD_SLASHER_SEC_BOSS_MULT, or 1.0 for anyone and anything else.
//
// Three gates, all of which must hold, and each is doing real work:
//   * the attacker's class is SLASHER — this is a class answer, not a weapon
//     buff; the same pistols on another class are untouched.
//   * the weapon is that player's CURRENT-TIER class secondary
//     (tod_classes::is_class_secondary — a STEM match, so the PaP'd AMP63's
//     dual-wield '_rdw' form still counts).
//   * the victim carries the boss/elite triad. Read through is_boss_or_elite,
//     never re-spelled — the same rule the other eight consumers use.
//
// NOT gated on melee: a melee hit is never the class secondary, so the two
// lanes cannot both fire on one hit by construction.
// THE ONE GATE both halves below share: is this a SLASHER hitting a boss or
// elite with the CLASS SIDEARM? Split out in v16.99 so the baseline and the
// GUNSLINGER term can never disagree about when they apply.
function slasher_sidearm_vs_boss( attacker, victim, weapon )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) )
		return false;
	if ( !isdefined( attacker.tod_class ) || attacker.tod_class != "slasher" )
		return false;
	if ( !is_boss_or_elite( victim ) )
		return false;
	return ( tod_classes::is_class_secondary( attacker, weapon ) );
}

// THE CLASS BASELINE — still MULTIPLICATIVE on the final, unchanged since v16.
// This is the slasher's compensation for the blade's x0.33 boss tax, not an
// upgrade, and nothing a player buys moves it.
function slasher_sidearm_boss_mult( attacker, victim, weapon )
{
	if ( !slasher_sidearm_vs_boss( attacker, victim, weapon ) )
		return 1.0;
	return TOD_SLASHER_SEC_BOSS_MULT;
}

// GUNSLINGER (domain 44) — ADDITIVE SINCE v16.99 (user 2026-09-03: "Yes make
// gunslinger additive").
//
// IT USED TO MULTIPLY THE FINAL, and that is why it was the largest outlier in
// the map. As `baseline x (1 + 0.30*Lv)` a maxed level turned the whole boss
// multiplier into x5.625 AFTER every other term had already been summed — so
// it scaled DAMAGE, the head crit and the baseline all at once and was diluted
// by nothing. Measured at the cap that put a maxed slasher's sidearm at ~220k
// boss DPS against the ASSAULT's ~82k, and the assault is the class whose whole
// identity is boss damage.
//
// It now returns an ADDITIVE term that joins the same sum GIANT SLAYER lives in
// (mult = 1 + DAMAGE + headshot + uniques + boss bonus + this), so a level of
// GUNSLINGER is worth the same KIND of thing as a level of GIANT SLAYER and is
// diluted by the same denominator. Same +0.30/Lv rate, same three gates, same
// max 5 — only the arithmetic changed, so no card, ladder or pause row moves.
//
// The 2.25 baseline is deliberately left multiplicative: it is the class's
// structural compensation for the blade tax, not something a card buys. If the
// slasher still reads too strong on bosses after this, THAT constant is the
// next lever, not this rate.
function gunslinger_bonus( attacker, victim, weapon )
{
	if ( !slasher_sidearm_vs_boss( attacker, victim, weapon ) )
		return 0.0;
	g = get_level( attacker, "gunslinger" ) * TOD_UPG_GUNSLINGER_PER_LVL;
	if ( has_dark( attacker, "gunslinger" ) )
		g += TOD_DARK_GUNSLINGER_ADD;   // DARK: +150% -> +180%. Deliberately the smallest step in the set: this lane was reshaped in v16.99 and moved again in v17.4
	return g;
}

function melee_boss_mult( attacker, victim, is_melee )
{
	if ( !IS_TRUE( is_melee ) )
		return 1.0;
	if ( !is_boss_or_elite( victim ) )
		return 1.0;
	// THE CLASS TEST (v18.3). Keyed on the attacker's CLASS and not on the
	// weapon, for the same reason slasher_sidearm_vs_boss is: a slasher's melee
	// is its class primary at every tier, and a bare-knife swing while the
	// sidearm is out is the same class's swing. The gun classes keep the shared
	// tax on the knife they all carry.
	if ( isdefined( attacker ) && isplayer( attacker )
	     && isdefined( attacker.tod_class ) && attacker.tod_class == "slasher" )
		return TOD_MELEE_BOSS_MULT_SLASHER;
	return TOD_MELEE_BOSS_MULT;
}

// PUBLIC — BACK ARMOR (domain 36, v9.45): the incoming-damage multiplier for a
// hit on `player` from `attacker`. 1.0 unless the domain is owned AND the
// attacker is inside the rear arc of the player's view. Same contract and the
// same two call sites as sprint_armor_mult (boss_player_damage for the normal
// chain, apply_player_mitigations for Panzer melee), floored the same way.
//
// The attacker may legitimately be undefined (world damage, a fall, splash with
// no owner) — that is NOT from behind, so it pays nothing.
function back_armor_mult( player, attacker )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return 1.0;
	lvl = get_level( player, "backarmor" );
	if ( lvl <= 0 )
		return 1.0;
	if ( !isdefined( attacker ) || !isdefined( attacker.origin ) )
		return 1.0;

	// 2D only: the spiral stacks enemies vertically and a Panzer two flights
	// below is not behind you. Zeroing z before normalizing is what makes the
	// arc a compass bearing rather than a sphere.
	to = attacker.origin - player.origin;
	to = ( to[ 0 ], to[ 1 ], 0 );
	if ( LengthSquared( to ) < 1 )
		return 1.0;                       // standing inside you — no bearing to read
	to = VectorNormalize( to );

	// VIEW angles, not the body's: "behind" means behind where the player is
	// LOOKING. GetPlayerAngles is the server-side view; a player who spins round
	// to shoot loses the bonus the moment the enemy is in front of them, which
	// is the whole point of the card. YAW ONLY (stock's colors_shared idiom) —
	// building the forward vector from a zeroed pitch is exact, where flattening
	// a full 3D forward degenerates to nothing when you look straight down.
	ang = player GetPlayerAngles();
	fwd = AnglesToForward( ( 0, ang[ 1 ], 0 ) );

	if ( VectorDot( fwd, to ) > TOD_BACK_ARC_DOT )
		return 1.0;                       // in front of, or beside, the player

	pct = ladder5( lvl );
	if ( has_dark( player, "backarmor" ) )
		pct += TOD_DARK_LADDER5_ADD;   // DARK: -32% -> -45% from behind
	m = 1.0 - ( pct / 100.0 );
	if ( m < 0.05 )
		m = 0.05;
	return m;
}

// ADRENALINE (MP7 unique): the live burst bonus — a FLAT +3%/tier while a
// proc is live, otherwise nothing. No stacks — one burst, one value. Read by
// THREE lanes, all the same number on purpose: the move-speed sum
// (apply_move_speed), the bullet-damage sum (unique_damage_mult, v17.67) and
// the on-trigger heal (v17.85, at the proc site, x TOD_ADREN_HEAL_MULT).
//
// THE HEAL READS IT THROUGH THE SAME LIVE-BURST TEST as the other two, which
// is why the proc site must set tod_adren_until BEFORE calling this — it
// returns 0 outside a burst by design, and a heal computed one line too early
// would silently be zero. That ordering is asserted by comment at the call.
// self = player.
function adren_bonus()
{
	lvl = class_live_level( self, "adrenaline" );   // the Breacher's; asleep in another class (2026-10-01)
	if ( lvl <= 0 || !isdefined( self.tod_adren_until ) )
		return 0;
	if ( GetTime() > self.tod_adren_until )
		return 0;
	b = lvl * TOD_ADREN_PCT_PER_LV;
	if ( has_dark( self, "adrenaline" ) )
		b += TOD_DARK_ADREN_ADD;   // DARK: +10% on top for the 3s burst (+37% at Lv9)
	return b;
}

// One-shot: wait out the burst then re-apply move speed ONCE, so the 3s is
// really 3s. Notify-cancelled so a proc landing inside an existing burst does
// not leave two threads racing to un-apply it.
function adren_expire()
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self notify( "tod_adren_expire" );      // newest proc owns the clock
	self endon( "tod_adren_expire" );
	wait ( TOD_ADREN_MS / 1000 );
	self apply_move_speed();
}

// The per-tier cooldown: 10/9/8/7/6 seconds at Lv1..Lv5. Shaped like
// thor_cooldown_ms and floored for the same reason — the floor, not the level
// cap, is what makes a future 6th tier safe.
function adren_cooldown_ms( lvl )
{
	cd = TOD_ADREN_CD_MAX_MS - ( lvl - 1 ) * TOD_ADREN_CD_STEP_MS;
	if ( cd < TOD_ADREN_CD_MIN_MS )
		cd = TOD_ADREN_CD_MIN_MS;
	return cd;
}

// Per-class BASE move speed (user 2026-08-20, retuned same day: 0.65-1.05
// felt too punishing): HEAVY/LMG 0.8, ASSAULT/AR 0.9, SKIRMISHER/SMG 1.0,
// SLASHER/melee 1.1. Script-side via the speed owner (the weapon-GDT
// moveSpeedScale fields are install-side and SHARED with map 1 — never edit
// those). SPRINT/MOBILITY multiply on top.
//
// 2026-08-23 (user, from the first ship-state run): "Lower the speed of AR and
// LMG by 0.05" — ASSAULT/AR 0.9 -> 0.85, HEAVY/LMG 0.8 -> 0.75. Speed is keyed
// on the CLASS, not the gun, so this holds across the whole tier ladder
// (Enfield/Krig/AK-47 and Stoner/HK21/Death Machine) and survives any roster
// swap.
//
// 2026-08-23 LATER (user: "Make assault move speed multiplier 0.9 instead of
// 0.85"): ASSAULT reverted to 0.9 — HALF the cut above is undone. HEAVY stays
// at 0.75, so the two heavy-weapon classes no longer move as one block: the AR
// sits midway between the LMG and the SMG rather than next to the LMG.
//
// 2026-08-30 (user: "we need to switch base speed of the skirmisher class and
// melee. Melee is too fast and skirmisher should be the fastest"): SKIRMISHER
// and SLASHER SWAPPED — skirmisher 1.0 -> 1.1, slasher 1.1 -> 1.0. A straight
// exchange, not a retune: the pair still occupies the same two rungs, so the
// spread and every relative gap in the map are unchanged and only the two
// labels moved. The SMG class is now the fastest thing in the map, which is
// what the class fantasy always said it was.
// Knock-on worth knowing rather than discovering: SPRINT (+5%/Lv, max 10) is
// scoped to BOTH of these classes, so the top speed the map can reach follows
// the swap too — the skirmisher's ceiling goes 1.50 -> 1.65 and the slasher's
// 1.65 -> 1.50. Nothing else keys on these numbers; class_speed_base is the
// single source and apply_move_speed is its only caller.
// Current spread, slowest to fastest: HEAVY 0.80 · ASSAULT 0.9 ·
// SLASHER 1.0 · SKIRMISHER 1.1.
// ⚠️ SPEED DOMAINS ADD TO THESE, THEY DO NOT MULTIPLY THEM (v15) — see
// apply_move_speed. So a "+5%" card is +0.05 of scale for every class alike.
function class_speed_base()   // self = player
{
	c = tod_classes::get_class( self );
	if ( !isdefined( c ) )
		return 1.0;   // classless (pre-draft)
	// ONE SPEED FOR EVERY CLASS (user 2026-09-26: "make the speed of each class
	// 1.1 ... there should be no classes with the sprint ability yet ... every
	// class will be 1.1, and it'll stay that no matter what tier until I say we
	// want to change that"). The per-class ladder that stood here (heavy 0.80 /
	// assault 0.9 / necromancer 1.1 / slasher 1.0) is retired; every
	// speed CARD (SPRINT, FORCED MARCH, MOBILITY, ATHLETE, FULL STEAM) was
	// already retired or parked, SPRINT FIRE is parked, so the scale is this
	// number plus only the Archer's grapple LANDING burst (a card, timed).
	// Tier never enters: nothing in the tier-up path touches the scale.
	if ( isdefined( c.key ) )
		return TOD_CLASS_SPEED_ALL;
	return 1.0;
}

// HEADSHOTS ARE 3x FOR EVERY CLASS. There was a class_hs_scale() here for one
// build (2026-08-24) giving the ASSAULT 4x; the user reverted it the same day
// after playing it ("Assault class had a 3x and we moved headshot to 4x. Lets
// move that back down to 3x actually"). Removed rather than stubbed to 1.0 — it
// was called from two per-hit damage callbacks and a multiply-by-one in that
// path earns nothing.
//
// To bring it back: one function keyed on tod_classes::get_class( player )
// returning ( wanted / 3.0 ), multiplied into the RAW damage in
// upgrade_damage_cb and in _tod_bosses::rp_damage_feed, on each lane's own
// existing headshot test. The 3.0 divisor is LOC_NORM in tools/gen_tod_twins.js
// — every generated gun ships locHead/locHelmet/locNeck 3.0 and the ENGINE has
// applied it before any callback sees the hit, so script only ever supplies the
// RATIO. Differentiation today comes solely from the HEADSHOT upgrade domain.

// PUBLIC — the MENU SOFT-FREEZE (live-test find 2026-08-19: FreezeControls
// zeroes the ENTIRE input snapshot — D-pad/stick/jump reads all go dead, the
// menus were unnavigable and timeouts random-picked). Instead: movement
// pinned via the move-speed owner above + weapons disabled so nav inputs
// can't fire/aim — but the raw button/stick reads STAY LIVE for the menu
// loops. self = player. (Jumping in place while locking is possible — known
// and accepted; JUMP is the lock button.)
function menu_freeze( on )
{
	if ( on )
	{
		// Never freeze a downed player (frozen laststand = stuck).
		if ( self laststand::player_is_in_laststand() )
			return;
		self.tod_menu_frozen = true;
		self DisableWeapons();
		self DisableOffhandWeapons();
		self AllowJump( false );   // JUMP is the lock button — the press must
		                           // not hop the player (stock builtin,
		                           // _zm.gsc:2508; reads still work)
		self apply_move_speed();
	}
	else
	{
		if ( !IS_TRUE( self.tod_menu_frozen ) )
			return;
		self.tod_menu_frozen = undefined;
		self EnableWeapons();
		self EnableOffhandWeapons();
		// DON'T HAND JUMP BACK TO A CRAWLING PLAYER (audit 2026-08-26). This ran
		// unconditionally, so unfreezing a player who went DOWN while the cards
		// were up undid stock's own last-stand restriction (_zm.gsc:2497) and
		// left them hopping around while crawling until revived or bled out.
		// Safe to skip: stock restores jump itself on every revive path
		// (_zm_laststand.gsc:965 — its comment is literally "player couldn't
		// jump - allow this again now that they are revived" — and :1372), so
		// there is no path where a revived player is left unable to jump.
		// EnableOffhandWeapons above is deliberately NOT guarded the same way:
		// it would need its own stock-restore audit for a smaller payoff, and
		// stock's revive_give_back_weapons already calls it (:400-401).
		if ( !( self laststand::player_is_in_laststand() ) )
			self AllowJump( true );
		self apply_move_speed();
	}
}

// (tireless_apply / tireless_clear / stock_sprint_time / tireless_spawn_watch
// all REMOVED 2026-08-26 with the TIRELESS feature — see the block comment
// where TOD_UPG_TIRELESS_SECS used to live for the full history and for what to
// try first if it is ever revived. Nothing in the map now calls
// SetSprintDuration or SetClientPlayerSprintTime, so both sprint knobs stay at
// the gametype's stock 4s for every player, which is what they read as anyway.)

// Native Gung-Ho permission: the Archer's class passive (the SPRINT FIRE card that
// shared this lane retired whole 2026-10-05). One owner, so the 1 s upgrade loop
// never strips a grant it did not make.
function apply_sprint_fire()   // self = player
{
	// THE ARCHER'S PASSIVE (2026-09-27 class pass 2): "can shoot while sprinting" - the
	// SPRINT FIRE card is parked, the class carries it.
	archer = ( isdefined( self.tod_class ) && self.tod_class == "assault" );
	if ( archer )
	{
		if ( !( self HasPerk( "specialty_sprintfire" ) ) )
			self SetPerk( "specialty_sprintfire" );
	}
	else if ( self HasPerk( "specialty_sprintfire" ) )
		self UnsetPerk( "specialty_sprintfire" );
}

function body_systems_loop()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	self.tod_feed_t = 0;

	for ( ;; )
	{
		wait 1;

		if ( !IsAlive( self ) || ( self laststand::player_is_in_laststand() ) )
			continue;

		// MOVE SPEED: re-assert every tick — the scale now depends on the
		// CLASS (station switches change it), and stock respawn/perk code
		// stomps SetMoveSpeedScale (last-writer-wins). Idempotent.
		self apply_move_speed();

		// BASE 150 HP + VITALITY maintain — the floor is max_hp_floor(), and
		// since v14.28 that floor COUNTS AN ACTIVE JUGG. It has to: stock's
		// health_reboot (round transitions, revives, jugg loss) rebuilds max
		// from player_base_health, and before v14.28 a jugg holder's rebuilt
		// 200 sat ABOVE the old jugg-blind floor (150+10xVIT), so a raise-only
		// maintain could never see the stolen vitality — that was the user's
		// "210 back down to 200". Still raise-only, still no free healing.
		want = self max_hp_floor();
		if ( self.maxhealth < want )
		{
			self.maxhealth = want;
			self SetMaxHealth( want );
		}

		// (The TIRELESS grant/clear pair lived here until 2026-08-26. It was the
		// only thing in the map that called SetPerk("specialty_staminup"), so
		// with it gone the specialty is once again purely the perk machine's —
		// no script grants it, and nothing needs to strip it. See the block
		// comment where TOD_UPG_TIRELESS_SECS used to live.)

		// One owner for the SPRINT FIRE card and the Archer's passive.
		self apply_sprint_fire();

		// (HEALTH became DMG REDUCTION 2026-08-20 — applied in the player
		// damage chain (_tod_bosses::boss_player_damage + the panzer-melee
		// mitigation hook), not here; maxhealth is stock's again.)

		// (REGEN's trickle hook lived here until 2026-08-30 — removed with the
		// domain, v14.11. RECOVERY replaces the heavy's sustain and runs on
		// its own faster thread, recovery_loop — a 1s tick is too coarse for
		// a 240..1500ms delay reduction.)

		// TWIN RECONCILE: keep the held class gun on the exact variant the
		// player's twin levels demand (covers respawn re-gives, class
		// switches, and PaP — the CSV maps every variant to its _up twin).
		self reconcile_twin();

		// CLASS-GUN WATCHDOG (2026-08-22). The class gun is only ever GIVEN at
		// spawn (tod_classes::give_class_loadout), so ANY path that takes it
		// strands the player on the pistol for the rest of the run — and with
		// god mode on there is no down/respawn to re-give it. That is exactly
		// what the stock too-many-weapons confiscation did (now disabled in
		// zm_tod2_cybercity.gsc), but a box trade, a powerup-gun restore that
		// misses, or any future stock path would do the same. Belt and braces:
		// if no form of the class gun is in the inventory for 3 consecutive
		// ticks, give it back at the form the player's levels + PaP latch
		// demand. Never mid-swap, never in last stand, never while a powerup
		// gun is out (its own restore would fight us).
		// (powerup-gun check reads the same per-player var tier_card_eligible and
		// grab_pap use — a plain zombie_vars field, no helper call)
		if ( IS_TRUE( self.tod_swap_busy ) || IS_TRUE( self.tod_tier_busy )
		  || self laststand::player_is_in_laststand()
		  || ( isdefined( self.zombie_vars ) && ( IS_TRUE( self.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( self.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) ) )
		{
			self.tod_noclassgun_ticks = 0;
		}
		else if ( isdefined( self class_primary_in_inventory() ) )
		{
			self.tod_noclassgun_ticks = 0;
		}
		else
		{
			if ( !isdefined( self.tod_noclassgun_ticks ) )
				self.tod_noclassgun_ticks = 0;
			self.tod_noclassgun_ticks++;
			if ( self.tod_noclassgun_ticks >= 3 )
			{
				self.tod_noclassgun_ticks = 0;
				g = tod_classes::gun( self );
				if ( isdefined( g ) )
				{
					// variant_name() + weapon_or_zm(), never hand-concatenation or a
					// bare GetWeapon — see the naming block in _tod_classes.
					want = tod_classes::weapon_or_zm( tod_classes::variant_name( g, IS_TRUE( self.tod_pap_owned ), self twin_suffix( IS_TRUE( self.tod_pap_owned ) ) ) );
					if ( !isdefined( want ) || want == level.weaponNone )
						want = tod_classes::base_weapon( g );   // fall back to the level-0 form
					if ( isdefined( want ) && want != level.weaponNone )
					{
						self tod_classes::give_camo_weapon( want );   // the PaP camo rides in the give
						self GiveStartAmmo( want );
						self SwitchToWeapon( want );
					}
				}
			}
		}

		// BULLET FEED (heavy) — REWORKED AGAIN 2026-08-21 (user): "should pull
		// in 1 bullet at a time but the upgrade will make it go faster and
		// faster. It will work when gun is away too."
		//   * ALWAYS exactly ONE round per tick — the amount never scales, the
		//     RATE does. That is what reads as a belt feeding.
		//   * Interval = TOD_UPG_FEED_BASE_SECS - TOD_UPG_FEED_STEP_SECS*(Lv-1)
		//     -> Lv1 every 1.0s ... Lv10 every 0.2s, floored so it can never
		//     hit zero. (This comment said 3.0s/0.75s until 2026-08-30 — it was
		//     never updated through the v8.9 retune OR the 2x buff. The DEFINES
		//     are the source of truth; distrust the prose.)
		//   * Runs on the CLASS GUN whether or not it is in hand — we look the
		//     weapon up in the player's inventory instead of reading
		//     GetCurrentWeapon, so the belt keeps loading while the pistol (or
		//     the Gift of Death) is out.
		// This loop ticks once a second, so the sub-second rates at high level
		// are reached by feeding on consecutive ticks; tod_feed_t carries the
		// fractional debt.
		feed = get_level( self, "bulletfeed" );
		if ( feed > 0 )
		{
			w = self class_primary_in_inventory();
			if ( isdefined( w ) )
			{
				iv = TOD_UPG_FEED_BASE_SECS - TOD_UPG_FEED_STEP_SECS * ( feed - 1 );
				floor_iv = TOD_UPG_FEED_MIN_SECS;
				// DARK UPGRADE (v17.10): 5.0 -> 7.0 rounds/s. Expressed as an INTERVAL
				// floor because that is this lane's unit; 1/7 = 0.142857s. The floor has
				// to move with it -- Lv10 already sits exactly on TOD_UPG_FEED_MIN_SECS,
				// so scaling the interval alone would be eaten by the clamp (the same
				// trap as THOR'S THUNDER's cooldown).
				// v18.9 — AND THE INTERVAL ITSELF, which is what the card was always
				// supposed to buy. Lowering the floor alone bought 0.05%: at the cap
				// iv = 1.0 - 0.0889*9 = 0.1999, which is already ABOVE the dark floor
				// 0.142857, so the clamp never fired and dark BULLET FEED delivered
				// 5.003 rounds/s against the plain card's 5.000. The comment above
				// names this exact trap and then fell into it; thor_cooldown_ms is the
				// lane that does it right, and this now matches it — scale the value
				// AND lower the floor. Safe at every level because dark_pool only ever
				// offers a MAXED domain and tier_up clears the dark bit in lockstep
				// with the level, so no path reaches here with dark on a sub-cap feed.
				if ( has_dark( self, "bulletfeed" ) )
				{
					floor_iv = 1.0 / TOD_DARK_BULLETFEED_RPS;
					iv = floor_iv;
				}
				if ( iv < floor_iv )
					iv = floor_iv;

				if ( !isdefined( self.tod_feed_t ) )
					self.tod_feed_t = 0;
				self.tod_feed_t += 1.0;   // this loop's period

				// Feed one round per whole interval elapsed (catches up the
				// sub-second rates without ever batching more than the debt).
				while ( self.tod_feed_t >= iv )
				{
					self.tod_feed_t -= iv;
					clip = self GetWeaponAmmoClip( w );
					stock = self GetWeaponAmmoStock( w );
					if ( clip >= w.clipSize || stock <= 0 )
					{
						self.tod_feed_t = 0;   // full or dry — no debt to bank
						break;
					}
					self SetWeaponAmmoClip( w, clip + 1 );
					self SetWeaponAmmoStock( w, stock - 1 );
				}
			}
		}
	}
}

function trickle_heal( amount )   // self = player
{
	if ( self.health >= self.maxhealth )
		return;
	n = self.health + int( amount + 0.5 );
	if ( n > self.maxhealth )
		n = self.maxhealth;
	if ( n > self.health )
		self.health = n;
}

// ---------------------------------------------------------------------------
// RECOVERY (HEAVY, v14.11) — "health regen starts 10% sooner / Lv", 3 levels.
// Stock zm regen is script-side in _zm_playerhealth.gsc::playerHealthRegen and
// its delay is LEVEL-GLOBAL, so it cannot be shortened for one player. This
// pair EMULATES the stock outcome at the reduced delay instead — see the
// contract at the TOD_UPG_RECOV_* defines. Stock's loop is untouched: when it
// wakes at the full delay it finds the player already healed and idles.
//
// Two damage stamps feed tod_last_dmg_ms, belt and braces:
//   * recovery_damage_watch — the engine's own "damage" notify, the same
//     input stock's playerHurtcheck trusts. Exact timing, every source
//     (Panzer flame, falls, everything that actually costs health).
//   * the poll below — any health DROP between ticks stamps too, so a
//     damage path that somehow skipped the notify is still caught within
//     one 0.1s tick. Our own heals only ever raise health, never re-stamp.
// ---------------------------------------------------------------------------

// self = player. One thread per player for the whole game (started once from
// player_upgrade_setup, same lifetime contract as body_systems_loop).
function recovery_loop()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	self.tod_last_dmg_ms = 0;
	last_hp = ( ( isdefined( self.health ) ) ? self.health : 0 );

	for ( ;; )
	{
		wait TOD_RECOV_TICK_SECS;

		// poll-stamp BEFORE any gating — a drop is a drop even at level 0
		// (levels can arrive mid-fight; the stamp must already be honest)
		hp = ( ( isdefined( self.health ) ) ? self.health : 0 );
		if ( hp < last_hp )
			self.tod_last_dmg_ms = GetTime();
		last_hp = hp;

		lvl = get_level( self, "recovery" );
		if ( lvl <= 0 )
			continue;
		if ( !IsAlive( self ) || ( self laststand::player_is_in_laststand() ) )
			continue;   // never heal the downed — stock's own regen never does
		if ( !isdefined( self.maxhealth ) || self.maxhealth <= 0 )
			continue;
		if ( self.health <= 0 || self.health >= self.maxhealth )
			continue;

		// Which band? Mirrors stock's healthOverlayCutoff split: above it a
		// finished delay SNAPS to full; below it the (longer) delay gates a
		// climb. Read the stock numbers LIVE so a retune there propagates.
		ratio = self.health / self.maxhealth;
		cutoff = ( ( isdefined( level.healthOverlayCutoff ) ) ? level.healthOverlayCutoff : 0.2 );
		if ( ratio > cutoff )
			delay = ( ( isdefined( level.playerHealth_RegularRegenDelay ) ) ? level.playerHealth_RegularRegenDelay : 2400 );
		else
			delay = ( ( isdefined( level.longRegenTime ) ) ? level.longRegenTime : 5000 );

		rec_pct = ladder5( lvl );
		if ( has_dark( self, "recovery" ) )
			rec_pct += TOD_DARK_LADDER5_ADD;   // DARK: regen starts 32% -> 45% sooner
		if ( ( GetTime() - self.tod_last_dmg_ms ) < int( delay * ( 1.0 - ( rec_pct / 100.0 ) ) ) )
			continue;

		// Window earned early — deliver what stock would deliver at the full
		// delay. SetNormalHealth takes a RATIO (stock's own idiom in this
		// exact spot, _zm_playerhealth.gsc:243).
		if ( ratio > cutoff )
			self SetNormalHealth( 1 );
		else
		{
			nr = ratio + TOD_RECOV_CLIMB_PER_TICK;
			if ( nr > 1.0 )
				nr = 1.0;
			self SetNormalHealth( nr );
		}
		last_hp = self.health;   // our heal is a rise; never let it read as anything else
	}
}

// self = player. The exact-timing stamp lane (see the block comment above).
function recovery_damage_watch()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "damage", amount, attacker );
		// FRIENDLY FIRE DOES NOT OPEN A REGEN WINDOW — mirrors stock's own
		// filter in playerHurtcheck (_zm_playerhealth.gsc:101) and map 1's
		// qr_damage_time_watcher. Without it a teammate's splash (or your own
		// PHD dive) would delay your regen where stock would not.
		if ( isdefined( attacker ) && isplayer( attacker )
		  && isdefined( attacker.team ) && attacker.team == self.team )
			continue;
		self.tod_last_dmg_ms = GetTime();
	}
}

// ---------------------------------------------------------------------------
// RED-VIGNETTE SYNC (v14.16) — the downstream cost of ANY recovery modifier.
//
// PORTED FROM MAP 1, WHERE IT WAS A USER-REPORTED BUG (acc _acc_perks.gsc
// health_overlay_sync, 2026-07-25: "the screen keeps flashing red for seconds
// at 100% HP"). Their Mega Quick Revive shortens the same stock regen delay
// RECOVERY does, so they hit this first and paid for the diagnosis.
//
// THE MECHANISM (verified in the stock tree, not assumed): the red vignette
// (_zm_playerhealth.gsc::redFlashingOverlay) is TIME-based and NEVER re-reads
// self.health — once you dip under healthOverlayCutoff it pulses until
// hurtTime + longRegenTime plus a fixed fade tail. Stock got away with that
// because stock's "very hurt" regen ALSO waits exactly longRegenTime, so the
// overlay ending and the heal completing land together BY CONSTRUCTION.
//
// WE BREAK THAT ALIGNMENT TWICE OVER:
//   * RECOVERY starts the heal at longRegenTime x (1 - 0.10 x Lv) — at Lv3
//     that is 3.5s, and the 0.2/tick climb tops off ~0.4s later, while the
//     vignette runs on past 5s + its tail. Seconds of red screen at full HP.
//   * VITALITY's apply_upgrade HEALS on purchase, which can top a critical
//     player off instantly — same desync, no RECOVERY required.
//
// THE LEVER IS STOCK'S OWN KILL SWITCH: "clear_red_flashing_overlay", which
// watchHideRedFlashingOverlay waits on (:396) and redFlashingOverlay endons
// (:414); _zm_laststand.gsc:1370 fires it on revive, so this is a blessed
// lane rather than a hack. Fired EDGE-TRIGGERED on not-full -> full.
//
// DELIBERATELY NOT GATED on the player_has_red_flashing_overlay flag: stock's
// regen loop clears that flag at full health WITHOUT stopping the visual, so
// "flag off, overlay still pulsing" is precisely the broken state being fixed.
// A notify with no overlay up is a no-op (fades an alpha-0 element).
//
// THREAD LIFETIME — one difference from map 1, and it is deliberate. They
// re-thread per life and needed a custom "acc_perk_life" notify to kill the
// previous copies, because a BO3 ZM player NEVER notifies "death" during play
// so endon("death") leaks a loop per respawn (their 2026-06-27 crash-hunt).
// OURS CANNOT LEAK: player_upgrade_setup latches on tod_body_systems_on and
// starts these threads exactly ONCE per player (the latch is set and never
// cleared — grep-verified), so they simply survive death and respawn. Do NOT
// "fix" this by re-threading on spawn without adding a kill notify first.
// ---------------------------------------------------------------------------

// self = player.
function health_overlay_sync()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	was_full = true;   // spawns land at full — only a real recovery may edge-trigger

	for ( ;; )
	{
		wait TOD_RECOV_TICK_SECS;

		if ( !isdefined( self.maxhealth ) || self.maxhealth <= 0 )
			continue;
		if ( self.health <= 0 )
			continue;   // downed/dead — laststand's revive path clears the overlay itself

		is_full = ( self.health >= self.maxhealth );
		if ( is_full && !was_full )
			self notify( "clear_red_flashing_overlay" );
		was_full = is_full;
	}
}

// ---------------------------------------------------------------------------
// TWIN SWAP — the REAL gun-data upgrades (fire rate / handling / recoil).
// The generator (tools/gen_tod_twins.js) authors a variant weapon per level
// combo; this reconciles the player's held class gun onto the exact variant
// their levels demand, preserving clip/reserve/PaP-form/held state. Naming
// contract: <base>[_up]_f{F}h{H} (skirmisher) / <base>[_up]_r{R} (assault).
// self = player. Runs every body tick (self-healing) + instantly on upgrade.
// ---------------------------------------------------------------------------

// self = player -> the variant suffix its class gun must be on.
//
// GENERIC since CLASS TIERS (2026-08-22): the suffix is built from the gun's
// registered axes (_tod_classes::register_gun) — one letter + level per axis,
// in registration order: "_f1h2" (mp5 fire x handling), "_r0m3" (krig recoil
// x mag), "_p1" (stoner penetration), "_k4" (knife swing). An axis-less gun
// returns "_b" — its single base-tuned form. A new gun never touches this.
//
// NO EARLY-OUT (user 2026-08-21): the level-0 variants (_f0h0 / _r0m0 / _p0 /
// _k0 / _b) are REAL assets — they carry the base tune that cannot go in the
// shared install GDT (move 1.0, LOC_NORM, recoil/ADS bumps, per-gun clips).
// Returning "" would hand the player the untuned stock asset.
// `is_up` = is the PACKED form in hand. DARK UPGRADES (v17.10) live one rung
// past the ladder and exist ONLY on the packed form of the class TIER 3 gun
// (gen_tod_twins.js axisMaxUp), so the bump is applied only when packed.
//
// THIS FUNCTION DOES NOT KNOW WHICH GUN HAS WHICH RUNG, ON PURPOSE. Mirroring
// the generator's axisMaxUp table here would be a second source of truth that
// nothing regenerates -- the exact drift this repo keeps paying for. Instead
// the caller ASKS FOR the dark name, and falls back to the plain one when the
// asset does not link (see reconcile_twin). A Krig 6 holder with dark MAG SIZE
// therefore keeps working: m4 exists on the AK only, the lookup misses, and the
// plain suffix is used.
function twin_suffix( is_up )
{
	g = tod_classes::gun( self );
	return self twin_suffix_for( g, is_up );
}

function twin_suffix_for( g, is_up )
{
	if ( !isdefined( g ) )
		return "";
	if ( !isdefined( g.axes ) || g.axes.size == 0 )
		return "_b";
	s = "_";
	for ( i = 0; i < g.axes.size; i++ )
	{
		lvl = self axis_level( g.axes[ i ].domain );   // the core cards drive their forms in 3/6/9 steps (2026-09-27)
		if ( IS_TRUE( is_up ) && has_dark( self, g.axes[ i ].domain ) )
			lvl++;
		s += g.axes[ i ].letter + lvl;
	}
	return s;
}

// self = player -> the class primary from the player's INVENTORY (held or
// holstered), or undefined. BULLET FEED needs this: the belt keeps loading
// while another weapon is out (user 2026-08-21 "it will work when gun is away
// too"), so we cannot read GetCurrentWeapon.
function class_primary_in_inventory()
{
	g = tod_classes::gun( self );   // the CURRENT tier's gun
	if ( !isdefined( g ) )
		return undefined;
	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		if ( isdefined( w ) && IsSubStr( w.name, g.stem ) )
			return w;
	}
	// ADDITIVE CLASS (v18.30; inert today - no registered class sets .additive):
	// a kept lower-tier gun still counts as the class primary -- for the
	// watchdog, the PaP latch and the tier gate.
	foreach ( w in weapons )
	{
		if ( isdefined( w ) && tod_classes::name_is_class_stem( self, w.name ) )
			return w;
	}
	return undefined;
}

// ---------------------------------------------------------------------------
// DEV ONLY — SPAWN STRAIGHT INTO A MAXED CLASS (user 2026-09-01: "in dev mode
// spawn me in with maxed out mp7 skirmisher class").
// ---------------------------------------------------------------------------
// WHY THIS EXISTS: a balance change is judged at its CEILING, and reaching the
// ceiling honestly is a 40-minute climb. Every number retuned this session —
// the DR ladder, the SPRINT and DR band swap, the class-tier DPS steps — only
// becomes visible with the domains actually maxed.
//
// It is a POLICY over the same PRIMITIVES the card system uses: tier_up,
// domain_max, sync_max, apply_move_speed, reconcile_twin. The caps and ladders
// live in those and nowhere here, so a retune reaches this path for free.
//   * NO PERKS. They would be a CONFOUND — Juggernog changes max HP, which is
//     exactly what a DMG REDUCTION test is measuring. Buy them if you want them.
//
// ⚠️ THE FLOOR GATE IS STAMPED, NOT WAIVED. tier_up refuses a promotion until
// the player's own climb high-water clears floor 10 / 20 (v14.35), and that gate
// is deliberately NOT waived by tod_dev. So this stamps mark_top_reached() —
// going through the real gate rather than
// around it, which is what keeps this path honest about the shipping rules.
//
// Gated by its callers, all dev-only in _tod_main (dev_maxed_harness). It does
// not re-check level.tod_dev, so do not call it from anywhere unguarded.
function dev_grant_maxed( player )
{
	// Threaded on the player, so self == player. The endons matter because this
	// function WAITS (for the loadout, and between promotions) and a disconnect
	// or game end mid-grant would otherwise run the rest against a dead entity.
	self endon( "disconnect" );
	level endon( "end_game" );

	if ( !isdefined( player ) || !isplayer( player ) )
		return;
	if ( !isdefined( player.tod_class ) )
		return;   // classless: nothing to promote or scope domains against

	// The class loadout is threaded off the spawn callback and waits 0.5s for
	// stock's own give to finish. tier_up resolves the CURRENT primary out of
	// inventory and bails if it is not there yet, so wait for the gun rather
	// than racing it.
	for ( i = 0; i < 40 && !isdefined( player class_primary_in_inventory() ); i++ )
		wait 0.05;

	// TIER to the top (skirmisher: MSMC -> MP5 -> MP7; slasher: Combat Knife
	// -> Katana -> Stormbreaker — the class comes from the caller). tier_card_eligible
	// wants the current gun PaP'd; the tod_pap_owned latch satisfies it and
	// reconcile pulls the _up form within a second.
	tod_gauge::mark_top_reached( player );
	for ( guard = 0; guard < 4 && tod_classes::tier( player ) < tod_classes::tier_max(); guard++ )
	{
		tod_classes::pap_first_grant( player, player class_primary_in_inventory() );
		if ( !( tier_up( player ) ) )
			break;
		wait 0.1;
	}

	// PaP the promoted primary, then the sidearm — which needs its own call,
	// because the latch is consumed by reconcile_twin and that stem-matches the
	// class PRIMARY only.
	tod_classes::pap_first_grant( player, player class_primary_in_inventory() );
	player tod_classes::pap_secondary();

	// EVERY eligible domain to this player's cap, through the same fields and
	// the same LUI sync the card system uses, so the pause list stays truthful.
	if ( isdefined( level.tod_domains ) && isdefined( player.tod_levels ) )
	{
		for ( i = 0; i < level.tod_domains.size; i++ )
		{
			d = level.tod_domains[ i ];
			if ( !( domain_available( player, d ) ) )
				continue;
			cap = domain_max( player, d );
			if ( get_level( player, d.key ) >= cap )
				continue;
			player.tod_levels[ d.key ] = cap;
			player LuiNotifyEvent( &"tod_upg_sync", 3, tod_upgrade_ui::domain_id( d.key ), cap, sync_max( player, d ) );
		}
	}

	player apply_move_speed();
	player reconcile_twin();
	// DISTRACTION writes a level with no inventory; the guarded pointer is the
	// same lane the two shipping call sites use.
	if ( isdefined( level.tod_distract_reconcile ) )
		player [[ level.tod_distract_reconcile ]]();
	// RIOT SHIELD (domain 45): same lane, same reason — equipment is inventory
	// and this path writes a level. Pointer set in _tod_riotshield::init.
	if ( isdefined( level.tod_shield_reconcile ) )
		player [[ level.tod_shield_reconcile ]]();
	player refresh_upgrade_list();

	if ( IS_TRUE( level.tod_dev ) )
		player IPrintLnBold( "^2DEV^7: maxed " + player.tod_class + " T" + tod_classes::tier( player ) );
}

function reconcile_twin()   // self = player
{
	// SWAP LATCH (2026-08-22): a swap in flight (this walk from another thread,
	// or a tier-up) waits up to 1s for the switch to take — the body loop's
	// tick must not start a SECOND swap on the same player meanwhile (a third
	// primary = the engine silently drops one: the inventory-overflow trap).
	if ( IS_TRUE( self.tod_swap_busy ) || IS_TRUE( self.tod_tier_busy ) )
		return;
	g = tod_classes::gun( self );   // the CURRENT tier's gun (CLASS TIERS)
	if ( !isdefined( g ) )
		return;

	weapons = self GetWeaponsListPrimaries();
	foreach ( w in weapons )
	{
		g = tod_classes::gun_for_weapon( self, w );
		if ( !isdefined( g ) )
			continue;

		// PaP suffix differs per gun family ("_up" skye / "_upgraded" ballistic).
		// tod_pap_owned is the FREE-PaP DROP's latch (_tod_powerups::grab_pap):
		// once set, reconcile pulls the class gun to its _up form on the next
		// tick. Routing PaP through here instead of the stock upgrade path is
		// deliberate — the stock path worked on the PISTOL but not the class
		// guns (user 2026-08-21), and this builds a variant name we KNOW is
		// generated, then reuses the proven swap order below.
		is_up = tod_classes::pap_tier( self, w ) > 0;

		// DARK UPGRADES (v17.10): ask for the dark variant, and FALL BACK to the
		// plain one when it does not link. The dark rung only exists on the packed
		// TIER 3 gun of each class, so a player holding dark MAG SIZE on a Krig 6,
		// or dark anything while un-packed, asks for a name with no asset.
		//
		// THE FALLBACK IS THE WHOLE POINT. The bail below is "never take the
		// player's gun", which is right for a genuinely missing asset but would
		// FREEZE a dark holder on their old variant forever -- no error, no log
		// line, the pause menu reporting an upgrade that never applied. This is
		// also why no axisMaxUp mirror lives in GSC: the lookup IS the check.
		suffix = self twin_suffix_for( g, is_up );
		want_name = tod_classes::variant_name( g, is_up, suffix );
		if ( w.name == want_name )
			continue;
		// THE GAUNTLET'S LEFT-HAND TWIN (build 18, _tod_warrior_melee): "<form>_l" is
		// the same rung held in the other hand for one punch - never walk it. A rung
		// or pack change still differs and swaps (a PaP on the left lands on the right).
		if ( w.name == want_name + "_l" )
			continue;

		want = tod_classes::weapon_or_zm( want_name );
		if ( !isdefined( want ) )
		{
			plain = self twin_suffix_for( g, false );
			if ( plain == suffix )
				return;   // variant not linked and no dark rung was asked for — never take the player's gun
			suffix = plain;
			want_name = tod_classes::variant_name( g, is_up, suffix );
			if ( w.name == want_name )
				return;
			want = tod_classes::weapon_or_zm( want_name );
			if ( !isdefined( want ) )
				return;   // neither links — never take the player's gun
		}

		// PAP CROSSING = FULL AMMO (v13.18, Workshop report "Yikes" 2026-08-29:
		// "i pap the stoner and my bullet size went from 60-25"). The delta
		// copy below preserved his 10 remaining rounds: 10 + (75-60) = the
		// exactly-25 on his screen, read as a capacity nerf. The delta is the
		// RIGHT rule for twin LEVEL walks — an upgrade card must never mint
		// free ammo — but base->_up here is the player's paid Pack-a-Punch,
		// and stock PaP has returned a FULL gun in every zombies title: the
		// 5000 buys the refill too. Detected as: the wanted form is _up while
		// the HELD form is not. (_up-to-_up level walks and base-to-base walks
		// keep the delta; the tier-up path already passes fresh=true itself.)
		crossing = ( is_up && !IsSubStr( w.name, g.up_suffix ) );
		self swap_primary( w, want, crossing );
		return;
	}
}

// self = player. THE swap: replace primary `w` with `want` — the twin walk
// (fresh = false, ammo DELTA-copied) and the tier-up (fresh = true, full
// start ammo: a promotion is a gift). Returns false if the player vanished
// mid-swap.
//
// MAP 1's PROVEN SWAP ORDER (_acc_weapon_variants.gsc:775-848): GIVE first
// (old form still in hand), IMMEDIATE switch, ammo set AFTER the switch (mag
// twins change clipSize — the delta keeps the copy from clamping), TAKE the
// old form LAST (take-first made the engine auto-raise another gun).
//
// THE HOLE THAT ORDER STILL HAD (user 2026-08-21: "it takes away your gun and
// places it in your inventory... always switches to my pistol"):
// SwitchToWeaponImmediate is silently EATEN in several player states
// (mid-sprint, mid-raise, mid-reload, ADS transition). When it is, `want`
// lands holstered, TakeWeapon(w) then removes the CURRENT gun, and the engine
// falls back to the pistol — and nothing ever corrects it, because the next
// reconcile sees the right twin already owned and returns early. Map 1
// survived this only because its reconcile re-fired on weapon_change_complete.
// FIX: VERIFY the switch took, retrying every frame BEFORE we take the old
// form (so the pistol never even flashes), and keep a short trailing
// re-assert after the take as the last line of defence.
function swap_primary( w, want, fresh )
{
	self.tod_swap_busy = true;   // reconcile_twin skips while a swap is in flight (cleared on EVERY exit)
	clip  = self GetWeaponAmmoClip( w );
	stock = self GetWeaponAmmoStock( w );
	cur   = self GetCurrentWeapon();
	// HELD = the engine's current weapon is the old form. A transitional
	// "none" (mid weapon-change) is treated as held too: if the player is
	// between weapons while we swap their CLASS primary, raising the new
	// form is the only outcome that never strands them on the pistol.
	// (If they are genuinely holding the pistol, cur == pistol -> not
	// held -> the swap happens silently in the holster, as it should.)
	held  = ( cur == w || cur == level.weaponNone );

	// THE CAMO RIDES IN THIS GIVE (v17.35). Weapon options are per-give and
	// nothing re-reads them, so a one-argument GiveWeapon here is what stripped
	// the packed look off the class primary on every twin swap — i.e. on every
	// gun-scoped level-up after the pack.
	self tod_classes::give_camo_weapon( want );
	if ( held )
	{
		for ( i = 0; i < 20; i++ )   // up to 1s of frames
		{
			self SwitchToWeaponImmediate( want );
			if ( self GetCurrentWeapon() == want )
				break;
			wait 0.05;
			if ( !isdefined( self ) )
				return false;   // player gone mid-swap (the latch dies with the entity)
			// WENT DOWN MID-SWAP (audit 2026-08-26): the ENGINE owns the weapon in
			// last stand — it has just forced the crawl pistol — so re-issuing
			// SwitchToWeaponImmediate here is a fight we cannot win and would only
			// yank the pistol out of a downed player's hands.
			// `break`, NEVER `return false`: the swap must still complete
			// atomically through the TakeWeapon( w ) below, or the player is left
			// holding BOTH gun forms, which is strictly worse than the status quo.
			// ensure_equipped already bails on laststand, so nothing downstream
			// fights the pistol either.
			if ( self laststand::player_is_in_laststand() )
				break;
			if ( !( self HasWeapon( want ) ) )
			{
				self.tod_swap_busy = undefined;
				return false;   // weapon stripped mid-swap — bail clean
			}
		}
	}
	if ( IS_TRUE( fresh ) )
	{
		self GiveStartAmmo( want );
	}
	else
	{
		new_clip  = clip  + ( want.clipSize - w.clipSize );
		new_stock = stock + ( want.maxAmmo  - w.maxAmmo );
		if ( new_clip < 0 )
			new_clip = 0;
		if ( new_stock < 0 )
			new_stock = 0;
		self SetWeaponAmmoStock( want, new_stock );
		self SetWeaponAmmoClip( want, new_clip );
	}
	self TakeWeapon( w );
	if ( held )
		self thread ensure_equipped( want );
	self.tod_swap_busy = undefined;
	return true;
}

// self = player. Trailing re-assert after a twin swap: if the engine STILL
// ended up on another gun (it can auto-raise a fallback in the same frame as
// the take), pull the twin back up. Bounded, frame-paced, stops the moment
// it lands; never fights last stand (the engine owns the weapon there).
function ensure_equipped( want )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	self notify( "tod_ensure_equipped" );   // newest swap wins
	self endon( "tod_ensure_equipped" );

	for ( i = 0; i < 30; i++ )   // up to 1.5s
	{
		wait 0.05;
		if ( !isdefined( want ) || !( self HasWeapon( want ) ) )
			return;
		if ( self laststand::player_is_in_laststand() )
			return;
		if ( self GetCurrentWeapon() == want )
			return;
		self SwitchToWeaponImmediate( want );
	}
}

// PUBLIC - A CARD OF ANOTHER CLASS SLEEPS (2026-10-01, the crown's CLASS TERMINAL,
// _tod_class_terminal.gsc). A player who changes class there keeps every card; the
// ones add_domain scoped to another REAL class (class_keys naming a registered class
// that is not theirs now) are dormant until they are that class again. A domain
// scoped to no registered class ("parked") and a shared one
// (class_keys undefined) never sleep, so nothing changes for a player who never
// switches: their only class-scoped cards are their own class's.
function domain_dormant( player, d )
{
	if ( !isdefined( player ) || !isdefined( d ) || !isdefined( d.class_keys ) || !isdefined( player.tod_class ) )
		return false;
	owned_by_a_class = false;
	foreach ( k in d.class_keys )
	{
		if ( k == player.tod_class )
			return false;
		if ( isdefined( level.tod_classes ) && isdefined( level.tod_classes[ k ] ) )
			owned_by_a_class = true;
	}
	return owned_by_a_class;
}

// PUBLIC - THE LEVEL A CARD IS WORTH RIGHT NOW. get_level() is what the player OWNS;
// this is what APPLIES (0 while the card sleeps, see domain_dormant). Read it, not
// get_level, in any effect that is not already gated on the class or on the class
// gun: VITALITY and its dark rung (max_hp_floor), ADRENALINE (the proc and
// adren_bonus), the RIOT SHIELD (_tod_riotshield reconcile / recharge_loop).
function class_live_level( player, key )
{
	lvl = get_level( player, key );
	if ( lvl <= 0 )
		return lvl;
	if ( domain_dormant( player, find_domain( key ) ) )
		return 0;
	return lvl;
}

function get_level( player, key )
{
	if ( !isdefined( player.tod_levels ) || !isdefined( player.tod_levels[ key ] ) )
		return 0;
	return player.tod_levels[ key ];
}

// THE CORE WEAPON CARD'S damage term (self-less; attacker = player). Only on the
// class's own primary (tod_classes::gun_for_weapon), never a kit or a powerup gun.
// The Necromancer returns 0 here: the skull's beam applies SOUL BEAM itself.
function core_weapon_bonus( attacker, weapon )
{
	if ( !isdefined( attacker ) || !isplayer( attacker ) || !isdefined( attacker.tod_class ) )
		return 0;
	key = undefined;
	step = 0;
	if ( attacker.tod_class == "assault" )      { key = "deadeye";    step = TOD_CORE_DMG_ARCHER; }
	else if ( attacker.tod_class == "heavy" )   { key = "buckshot";   step = TOD_CORE_DMG_BREACHER; }
	else if ( attacker.tod_class == "slasher" ) { key = "heavyhands"; step = TOD_CORE_DMG_WARRIOR; }
	else return 0;
	lv = get_level( attacker, key );
	if ( lv <= 0 )
		return 0;
	if ( !isdefined( tod_classes::gun_for_weapon( attacker, weapon ) ) )
		return 0;
	return lv * step;
}

// PUBLIC — how many of a core card's big steps (Lv3 / Lv6 / Lv9) a level has reached: 0..3.
function core_bucket( lv )
{
	if ( !isdefined( lv ) || lv <= 0 )
		return 0;
	b = Int( lv / TOD_CORE_BUCKET );
	if ( b > 3 ) b = 3;
	return b;
}

// THE WEAPON-FORM LEVEL for a twin axis (self = player). The core cards drive the
// forms that already exist, in their 3/6/9 steps, instead of adding new ones:
//   "e" pellets    <- BUCKSHOT   : e1 / e2 / e3 at Lv3 / Lv6 / Lv9 (the old PELLETS 1..3)
//   "k" knifespeed <- HEAVY HANDS: k2 / k4 / k5 at Lv3 / Lv6 / Lv9 (-15 / -24 / -30% swing time, user 2026-09-28)
//   "d" deadeye    <- DEADEYE    : d1 / d2 / d3 at Lv3 / Lv6 / Lv9 (gen_tod_twins AXIS.d)
// Every other axis reads its own card level, as before.
function axis_level( domain )
{
	if ( domain == "pellets" )
		return core_bucket( get_level( self, "buckshot" ) );
	if ( domain == "deadeye" )
		return core_bucket( get_level( self, "deadeye" ) );
	// QUICK DRAW (key shotspeed; 2026-09-28, user: "max quick draw ... two times as fast" + no SUPER that
	// buys nothing): 6 levels on 3 weapon steps at Lv2 / Lv4 / Lv6 (s1 / s2 / s3), so every +2 crosses one.
	// LOCKSTEP gen_tod_twins AXIS.s / SHOTSPEED_STEP; Lv1 / 3 / 5 are the script draw curve (_tod_archer_bow).
	// 2026-10-05 (the automatic bow): x3 at Lv9 on 3^(Lv/9); the steps stay at Lv2 / 4 / 6 / 8 and an odd level is
	// paid as damage by _tod_archer_bow::quickdraw_mult (the script draw no longer runs ahead of the weapon).
	if ( domain == "shotspeed" )
	{
		l = get_level( self, "shotspeed" );
		if ( l >= 8 ) return 4;   // 2026-09-28: 9 levels (user), steps at Lv2 / 4 / 6 / 8 so every +2 crosses one
		if ( l >= 6 ) return 3;
		if ( l >= 4 ) return 2;
		if ( l >= 2 ) return 1;
		return 0;
	}
	if ( domain == "knifespeed" )
	{
		// 2026-09-28: the blades carry k0..k3 only (the never-dealt k1 / k3 retired to fund QUICK DRAW's
		// s4); the bucket IS the form now: -15 / -24 / -30% swing at Lv3 / 6 / 9 (LOCKSTEP KNIFE_STEP)
		return core_bucket( get_level( self, "heavyhands" ) );
	}
	return get_level( self, domain );
}

// (add_luck REMOVED 2026-08-20 — the integer event-luck became the 0..100%
// LUCK BAR, owned by _tod_luck.gsc; sources call tod_luck::add/boss_kill.)

// ---------------------------------------------------------------------------
// UPGRADE LIST — PAUSE MENU ONLY (user 2026-08-20: the always-on hudelem
// column cluttered the play HUD). Channel = map 1's PROVEN per-player
// LuiNotifyEvent lane (its kill feed: LuiNotifyEvent -> scriptNotify
// PerController model -> CoD.GetScriptNotifyData). SetClientDvar does NOT
// exist in T7 (stock has it commented "TODO T7 - function port if needed"),
// and host SetDvar never replicates to co-op peers — this lane does.
// INT-ONLY args (domain id / level / max): string args ride the
// CS_LOCALIZED_STRINGS config-string table, and unique dynamic strings
// would leak slots forever on an endless map. tod_upgrade.lua accumulates
// the pairs into CoD.TodOwned; AetheriumStartMenu.lua renders that table
// (same client Lua VM) on every pause-menu open.
// ---------------------------------------------------------------------------

function ensure_upgrade_list()   // self = player
{
	self endon( "disconnect" );
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	wait 1;   // the HUD menu hosts the scriptNotify listener — let it open first
	self tod_upgrade_ui::ensure_menu();
	self refresh_upgrade_list();
}

function refresh_upgrade_list()   // self = player
{
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		lvl = get_level( self, d.key );
		// A SLEEPING CARD (2026-10-01, the crown's class terminal) is sent at level 0, which the
		// pause menu and scoreboard hide; switching back sends its real level again.
		if ( lvl > 0 && domain_dormant( self, d ) )
			lvl = 0;
		if ( lvl > 0 || get_level( self, d.key ) > 0 )
			self LuiNotifyEvent( &"tod_upg_sync", 3, tod_upgrade_ui::domain_id( d.key ), lvl, sync_max( self, d ) );
	}
	// CLASS TIER row (id 24): pips = the tier. Same int-only lane.
	//
	// SENT FROM TIER 1 SINCE v14.35 (was tier 2 on, "tier 1 is the baseline,
	// not an upgrade"). The row is no longer just a trophy — its detail line
	// now states what the NEXT promotion costs (Pack-a-Punch + the floor gate),
	// and a tier-1 player is precisely the one who needs to read it. A missing
	// row cannot explain anything.
	//
	// SAFE FOR THE PANEL'S atTopTier TEST, checked rather than assumed: that
	// test is `lvl >= max` with an explicit nil path documented as "ABSENT
	// MEANS TIER 1". Sending 1 of 3 takes the same branch the nil path took,
	// so the reset badges still show for a tier-1 player exactly as before.
	// THE CLASS (2026-09-27): the pause menu shows the class name + its passive from
	// CoD.TodClass; before this it was only pushed with a card deal and the draft.
	self LuiNotifyEvent( &"tod_upg_class", 1, tod_classes::class_id( self.tod_class ) );
	t = tod_classes::tier( self );
	self LuiNotifyEvent( &"tod_upg_sync", 3, tod_upgrade_ui::domain_id( "tier" ), t, tod_classes::tier_max() + TOD_SYNC_SAFE_FLAG );   // the tier row IS the promotion — always "safe"
}

// ---------------------------------------------------------------------------
// Event scheduling — every Nth round boundary (rounds 4, 7, 10, ...)
// ---------------------------------------------------------------------------

function event_scheduler()
{
	level endon( "end_game" );

	last = 1;
	for ( ;; )
	{
		wait 0.5;
		r = level.round_number;
		if ( !isdefined( r ) || r == last )
			continue;
		last = r;
		// DEV: an upgrade every round from round 2. SHIP: every 4th round.
		// [tod v19.9] tod_dev_upgrades, not tod_dev — see the flag block in
		// zm_tod2_cybercity::tod_resolve_dev_flags. A dev session that wants god +
		// money + doors does not want a card panel every round on top.
		if ( IS_TRUE( level.tod_dev_upgrades ) )
		{
			if ( r > 1 )
				run_upgrade_event();
		}
		else if ( r >= TOD_UPG_EVERY_N_SHIP && ( r % TOD_UPG_EVERY_N_SHIP ) == 0 )
		{
			run_upgrade_event();
		}
	}
}

function run_upgrade_event()
{
	// Only players with something left to upgrade participate. If NOBODY has
	// (late-game, everything maxed) skip the whole event — no pause, no spam.
	participants = [];
	players = GetPlayers();
	foreach ( p in players )
	{
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		// A CRAWLER PARTICIPATES; A DEAD/SPECTATING PLAYER DOES NOT (v15 item 9,
		// user 2026-08-31: "When you are down and an upgrade round comes by you
		// should still be able to select a card").
		//
		// LAST STAND WAS EXCLUDED HERE FROM 2026-08-23, and that reason has since
		// been paid off. The original argument was that stock's bleedout loop does
		// not pause with the world, so a crawler dealt a card burned up to 20s of
		// a ~30s clock while every teammate stood frozen at
		// SetMoveSpeedScale(0.001) and could not reach them. That is now REFUNDED
		// explicitly further down this same function (the bleedout_time += waited
		// line), so the freeze costs a crawler nothing and the exclusion was
		// outliving its justification. The pause is capped at
		// TOD_UPG_CHOICE_TIMEOUT either way.
		//
		// IsAlive() IS TRUE IN LAST STAND (stock contract), so !isalive(p) alone
		// is exactly the dead/spectating test and nothing more.
		//
		// DEAD PLAYERS STAY OUT, for a reason no refund can fix: the engine
		// closes a player's LUI menus on death->spectate, so there is no panel to
		// draw a card on. Dealing to them would be the 2026-08-23 bug in a new
		// costume — a card nobody can pick, holding the world open.
		//
		// menu_freeze still refuses to freeze a laststand player (see it above),
		// which is now a FEATURE rather than a mismatch: the crawler keeps
		// crawling — and keeps being revivable — while they read their two cards.
		if ( !isalive( p ) )
			continue;
		p.tod_tier_deal_pre = undefined;
		if ( player_has_domains_left( p ) )
			participants[ participants.size ] = p;
		// DARK UPGRADES (v17.10) — THE THIRD ARM, and the feature does not work
		// without it. A player who has maxed everything they can reach falls
		// straight past the first test, and before this line the only thing that
		// could still admit them was a tier-card roll. That is precisely the
		// player a dark card was for (the retired spire's trial deal would have
		// dealt them nothing at all).
		else if ( dark_allowed() && dark_pool( p ).size > 0 )
			participants[ participants.size ] = p;
		else if ( tier_card_eligible( p ) && tier_card_roll( p ) )   // v16.56: full bar = guaranteed, else TOD_TIER_CARD_PCT
		{
			// CLASS TIERS: a MAXED player is only here for the tier chance — it is
			// rolled NOW (consumed by roll_options) so a miss never pauses the
			// world for an empty deal.
			p.tod_tier_deal_pre = true;
			participants[ participants.size ] = p;
		}
		else
		{
			// DEV ONLY (v16.70): a maxed player dealt nothing — say WHY the tier
			// card did not come (the reason ladder in tier_deny_reason).
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( p.name + ": no deal - tier card: " + tier_deny_reason( p ) );
			if ( !IS_TRUE( p.tod_upg_maxed_told ) )
			{
				p.tod_upg_maxed_told = true;   // tell them ONCE, not every round
				// (on-screen text removed 2026-08-20 — user: no floaty text)
			}
		}
	}
	if ( participants.size == 0 )
		return;

	set_world_pause( true );

	// The round event OWNS the shared card UI: any in-flight PERSONAL STATION
	// pick dies on this notify (synchronous — its thread is dead before our
	// per-player flows below touch the fields) and re-presents after we end.
	//
	// AND IT OWNS THE WORLD PAUSE TOO (v16.84). A SOLO station pick now freezes
	// the world itself, so a takeover can land on a pause this function did not
	// open — and the set_world_pause( false ) at the bottom would then clear a
	// station's freeze out from under a player still reading cards. Claiming it
	// here, before any yield and in the same synchronous block as the notify,
	// turns that station's station_pause_end() into a no-op: this event now
	// owns both lanes, and its player_choice_flow re-freezes and unfreezes the
	// player like any other participant. (Solo only ever has ONE owner, so
	// there is nothing to iterate.)
	level.tod_station_pause_owner = undefined;
	level notify( "tod_global_upg_takeover" );

	level.tod_upg_pending = 0;
	foreach ( p in participants )
	{
		p.tod_upg_done = false;
		level.tod_upg_pending++;
		p thread player_choice_flow();
	}

	// Co-op: everyone sees who is still deciding.
	if ( participants.size > 1 )
		level thread waiting_display( participants );

	// Wait for every participant (each flow decrements; 15s timeout inside).
	waited = 0;
	while ( level.tod_upg_pending > 0 && waited < ( choice_timeout() + 5 ) )
	{
		wait 0.25;
		waited += 0.25;

		// A PLAYER WHO LEAVES MID-PICK NEVER DECREMENTS (audit 2026-08-26).
		// player_choice_flow carries `self endon( "disconnect" )` and does its
		// level.tod_upg_pending-- as the LAST thing it does, so a disconnect
		// anywhere in the pick loses that decrement and this loop then burns the
		// FULL TOD_UPG_CHOICE_TIMEOUT + 5 = 20s with the world frozen: zombies
		// standing still, spawning halted, and every pause-gated device
		// (teleporters, ammo crate, the stations) refusing. Nothing on screen
		// explains it, because the leaver's card panel left with them.
		//
		// Re-derive the count from who is actually still here and still
		// deciding. This is the sibling of the downed/dead participant filter
		// above: both say "only wait on players who can actually answer".
		//
		// CLAMP DOWN ONLY, never assign — that keeps the counter authoritative
		// against any future path that increments it, and it cannot resurrect a
		// pause that has already ended. tod_upg_done is set immediately before
		// each decrement with no yield in between, so `live` equals the counter
		// for every connected player.
		//
		// player_choice_flow, both its endons and both decrement sites are
		// deliberately left byte-identical — no pick behaviour changes. Do NOT
		// "fix" this by replacing the disconnect endon with a watcher (double
		// decrement), and do NOT add endon( "end_game" ) to this function: that
		// would skip the set_world_pause( false ) below and freeze the world
		// permanently.
		live = 0;
		foreach ( p in participants )
		{
			if ( isdefined( p ) && !IS_TRUE( p.tod_upg_done ) )
				live++;
		}
		if ( live < level.tod_upg_pending )
			level.tod_upg_pending = live;
	}

	level notify( "tod_upg_event_over" );

	players = GetPlayers();
	foreach ( p in players )
	{
		if ( !isdefined( p ) )
			continue;
		// GIVE THE PAUSED SECONDS BACK TO ANYONE STILL DOWN (audit 2026-08-26).
		// Stock's Laststand_Bleedout decrements self.bleedout_time on a REAL-TIME
		// wait(1) and knows nothing about our world pause, so a player who was
		// already crawling when the event fired just burned up to 20s of a ~30s
		// clock during a window in which every living teammate was frozen at
		// SetMoveSpeedScale( 0.001 ) and could not physically reach them.
		//
		// SAFE AGAINST STOCK'S ANTI-CHEESE CLAMP: Laststand_Bleedout captures
		// n_bleedout_time = self.bleedout_time ONCE (_zm_laststand.gsc:538),
		// before either of its loops, so the snap-back at :545-551 — which fires
		// only when that CAPTURED value exceeds the dvar default and no
		// multiplier is set — cannot be tripped by a later write to the field.
		// Both loops re-read self.bleedout_time each iteration, so raising it
		// simply extends the timer.
		//
		// KNOWN COSMETIC LIMIT, ACCEPTED: the Aetherium bleedout bar animates a
		// fixed linear tween client-side, so credited seconds do not show — the
		// bar can read empty while the player is still revivable. Do NOT extend
		// the Lua to chase this.
		if ( p laststand::player_is_in_laststand() && isdefined( p.bleedout_time ) )
			p.bleedout_time += waited;
		// clear the waiting line (the display thread may have died mid-loop)
		if ( isdefined( p.tod_upg_wait_elem ) )
		{
			p.tod_upg_wait_elem Destroy();
			p.tod_upg_wait_elem = undefined;
		}
		p.tod_upg_wait_text = undefined;
	}

	// THE LUCK BAR IS SPENT BY PARTICIPANTS ONLY (audit 2026-08-26). This used
	// to ride the GetPlayers() loop above, so a player who was DOWN or DEAD when
	// the event fired — and was therefore deliberately excluded from it at the
	// participant filter, dealt no cards and given no roll — still had their
	// entire luck bar zeroed. Going down at a round boundary silently cost them
	// everything they had banked toward the next event's odds.
	//
	// `participants` is already in scope and is exactly the right set; do NOT
	// invent a per-player "was a participant" marker, which would go stale
	// across events.
	foreach ( p in participants )
	{
		if ( isdefined( p ) )
			p.tod_luck_bar = 0;   // fully spent on this event's rolls (user: full reset)
	}

	set_world_pause( false );
}

// The pick window for a deal.
function choice_timeout()
{
	return TOD_UPG_CHOICE_TIMEOUT;
}

// LEECH — LOGARITHMIC, not linear (user 2026-08-23: "the leech HP ... increase
// logorithimcally for both instead of linearly per level. It ends up getting
// crazy"). WAS TOD_UPG_LEECH_PER_LVL * lvl = 4/8/12/16/20 HP per blade kill —
// at Lv5 that is a full fifth of a base health bar PER KILL, and the slasher
// one-hits into the teens, so it healed faster than the horde could hurt it.
// NOW round( 4 * log2(1+Lv) ), tabulated: 4 / 6 / 8 / 9 / 10.
// LEVEL 1 IS UNCHANGED at 4 on purpose — the first point spent feels exactly as
// it did; the TAIL is halved (20 -> 10). Same shape as the k-ladder nerf in
// tools/gen_tod_twins.js (KNIFE_STEP), and the two were tuned together.
// A TABLE, not a log() call: GSC has no reliable log2, the shipped numbers
// should be readable here, and the pause-menu detail row in tod_upgrade.lua
// DETAIL[13] must mirror these exactly.
function leech_hp_for_level( lvl )
{
	switch ( lvl )
	{
		case 0:  return 0;
		case 1:  return 4;
		case 2:  return 6;
		case 3:  return 8;
		case 4:  return 9;
		default: return 10;   // Lv5 (and any future cap raise clamps here)
	}
}

// Any rollable DOMAIN below its cap?
function player_has_domains_left( player )
{
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		if ( !domain_available( player, d ) )
			continue;
		if ( get_level( player, d.key ) < domain_max( player, d ) )
			return true;
	}
	return false;
}

function player_has_upgrades_left( player )
{
	if ( player_has_domains_left( player ) )
		return true;
	// DARK UPGRADES (v17.10): a player with every domain maxed is exactly who
	// the feature exists for, and without this they are dropped from the event
	// by run_upgrade_event's participant filter BEFORE the roll ever happens.
	if ( dark_allowed() && dark_pool( player ).size > 0 )
		return true;
	// CLASS TIERS: a player with every domain maxed still has the promotion to
	// play for — they can still buy at a station for the tier chance alone
	// (run_upgrade_event pre-rolls that chance before pausing the world).
	return tier_card_eligible( player );
}

// self = player
function player_choice_flow()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	opts = roll_options( self );
	if ( !isdefined( opts ) )   // belt+braces (participants are pre-filtered)
	{
		self.tod_upg_done = true;
		level.tod_upg_pending--;
		return;
	}

	// (card luck banner now reads player.tod_luck_bar directly in
	// present_choice — the old combined event+domain integer is gone)

	self push_panel_hints();   // v14.35 — "CLASS TIER 2 - REACH FLOOR 10" under the cards, or nothing
	self menu_freeze( true );
	choice = self tod_upgrade_ui::present_choice( opts, choice_timeout() );
	self menu_freeze( false );

	picked = opts[ 0 ];
	other = opts[ 1 ];   // may be undefined (single-card deal)
	if ( choice == 2 && isdefined( opts[ 1 ] ) )
	{
		picked = opts[ 1 ];
		other = opts[ 0 ];
	}

	// (timeout text removed 2026-08-20 — user: no floaty text)

	// A REFUSED TIER PICK (timed out on the tier card, or the promotion could
	// not land) must not forfeit the deal — the other card pays out instead.
	ok = apply_upgrade( self, picked );
	if ( !ok && picked.domain == "tier" && isdefined( other ) && other.domain != "tier" )
		apply_upgrade( self, other );
	self.tod_upg_done = true;
	level.tod_upg_pending--;
}

// One small line on every player's screen: who is still deciding. Server
// hudelems + SetText is safe here — the distinct strings are subsets of at
// most 4 player names (bounded, nowhere near the 2048 string-cache cap).
function waiting_display( participants )
{
	level endon( "end_game" );
	level endon( "tod_upg_event_over" );

	for ( ;; )
	{
		wait 0.3;

		names = "";
		n = 0;
		foreach ( p in participants )
		{
			if ( !isdefined( p ) || IS_TRUE( p.tod_upg_done ) )
				continue;
			if ( n > 0 )
				names += ", ";
			names += p.name;
			n++;
		}
		if ( n == 0 )
			return;

		text = "^3CHOOSING:^7 " + names;
		players = GetPlayers();
		foreach ( viewer in players )
		{
			if ( !isdefined( viewer ) )
				continue;
			if ( !isdefined( viewer.tod_upg_wait_elem ) )
			{
				viewer.tod_upg_wait_elem = viewer hud::createFontString( "objective", 1.1 );
				if ( isdefined( viewer.tod_upg_wait_elem ) )
					// y 96 -> 74 (audit 2026-08-25). The baked UPGRADE AVAILABLE banner
					// occupies 122..215 of the 720-tall safe area, so at 96 this line
					// landed INSIDE the artwork and read as part of it. There is no gap
					// below the banner either — the cards start at 230 — so it moves
					// ABOVE instead, ending just clear of the banner top.
					viewer.tod_upg_wait_elem hud::setPoint( "TOP", "TOP", 0, 74 );
			}
			if ( isdefined( viewer.tod_upg_wait_elem ) &&
			     ( !isdefined( viewer.tod_upg_wait_text ) || viewer.tod_upg_wait_text != text ) )
			{
				viewer.tod_upg_wait_elem SetText( text );
				viewer.tod_upg_wait_text = text;
			}
		}
	}
}

// ---------------------------------------------------------------------------
// Rolls
// ---------------------------------------------------------------------------

// Returns array of 1-2 option structs { domain, display, desc, rarity,
// rarity_name, levels, cur }, or undefined if everything is maxed.
function roll_options( player )
{
	pool = eligible_pool( player );
	// CLASS TIER card (docs/25 §4.2): once the class gun is PaP'd, this deal
	// carries the promotion TOD_TIER_CARD_PCT of the time — rolled ONCE per
	// deal, here, so a maxed-out player (empty pool) gets exactly the same
	// chance as anyone else.
	if ( isdefined( player.tod_tier_deal_pre ) )
	{
		tier_deal = IS_TRUE( player.tod_tier_deal_pre );   // pre-rolled by run_upgrade_event (maxed player)
		player.tod_tier_deal_pre = undefined;
	}
	else
	{
		// v14.39 — the roll asks tier_card_ready_but_for_floor, NOT the full
		// eligibility, so a floor-blocked player still DRAWS the promotion and
		// is shown it locked. Everything else about the roll is unchanged: the
		// same TOD_TIER_CARD_PCT, once per deal. What the floor decides now is
		// whether the dealt card is takeable, not whether it exists.
		tier_deal = ( tier_card_ready_but_for_floor( player ) && tier_card_roll( player ) );   // v16.56: full bar + fully eligible = guaranteed (tier_card_roll)
	}
	// DEV ONLY (v16.70, user 2026-09-03: "when you have max luck and are
	// eligible ... guaranteed the class upgrade card. I think that's not working
	// properly"): the card's ABSENCE looks the same for every reason it can be
	// withheld, so name the reason on every dev deal that lacks it.
	if ( IS_TRUE( level.tod_dev ) && !tier_deal )
		tod_quiet_print( "tier card not dealt: " + tier_deny_reason( player ) );

	if ( pool.size == 0 )
	{
		if ( !tier_deal )
			return undefined;
		// A LOCKED CARD CANNOT BE THE WHOLE DEAL. With no domains left and the
		// promotion out of reach, presenting it alone would freeze the world for
		// a panel with nothing selectable on it — the player would sit through
		// the full timeout unable to answer, which is the leaver-stall bug's
		// shape with a different cause. Deal nothing instead; the round event's
		// participant filter already declines to pause for this player
		// (player_has_upgrades_left asks the FULL eligibility), and this guards
		// the station path that does not go through that filter.
		if ( tier_floor_pending( player ) > 0 )
			return undefined;
		opts = [];
		opts[ 0 ] = make_tier_option( player );   // the only card left — still opt-in (a timeout never takes it)
		return opts;
	}

	// v8.9 TIER DRAW (user 2026-08-21): no longer a flat shuffle — each domain
	// is offered in proportion to its tier weight, so S cards surface ~5x less
	// often than B. Drawn WITHOUT replacement so the two cards stay distinct.
	opts = [];
	first = weighted_draw( pool );
	opts[ 0 ] = make_option( player, pool[ first ] );
	if ( pool.size > 1 )
	{
		rest = [];
		for ( i = 0; i < pool.size; i++ )
		{
			if ( i == first )
				continue;
			rest[ rest.size ] = pool[ i ];
		}
		opts[ 1 ] = make_option( player, rest[ weighted_draw( rest ) ] );
	}

	// The TIER card ALWAYS takes the RIGHT slot: the left card is focused by
	// default and a timeout locks the focused card — a weapon swap the player
	// did not choose must never happen (apply_upgrade also refuses a timed-out
	// tier pick, belt and braces).
	if ( tier_deal )
		opts[ 1 ] = make_tier_option( player );

	// DARK UPGRADES (v17.10) — after the tier card so it can never be spent on a
	// slot the tier card is about to overwrite, and BEFORE the luck floor so the
	// floor sees the final hand. Both luck guarantees skip dark cards outright.
	opts = deal_dark( player, opts );

	// THE LUCK FLOOR — LAST, and it has to be last. The tier card overwrites
	// slot 1 directly above, so a guarantee applied any earlier could be spent
	// on a card that no longer exists by the time the deal is presented.
	//
	// The OPENING-HAND latch is read and set here rather than inside
	// guarantee_rarity, so it is spent exactly once even on the paths where the
	// guarantee itself returns early (dice already cleared the floor, or every
	// candidate was maxed). Reading it inside and setting it outside would let a
	// satisfied first deal hand the floor to the second one as well.
	first = !IS_TRUE( player.tod_first_deal_done );
	player.tod_first_deal_done = true;
	// v14.6: the pool rides along so the guarantee can REDEAL a slot when
	// neither dealt card has the headroom to absorb the owed rarity.
	guarantee_rarity( player, opts, first, pool );

	return opts;
}

// The LUCK GUARANTEE (see TOD_UPG_GUAR_ULT_BAR). opts = the 1-2 card structs,
// already rolled. Promotes ONE card up to the floor the bar has earned, or does
// nothing at all if the dice already met it.
//
// THE TIER CARD IS NOT AN ULTIMATE FOR THIS PURPOSE, on both sides of the test.
// It carries rarity 3 so it draws the ULTIMATE frame and sting, but it is a gun
// promotion, not "an ultimate upgrade" — so it neither SATISFIES the guarantee
// nor is eligible to be promoted (there is nothing to promote it to; its levels
// mean a tier, not a count). The player who draws one on a full bar gets a
// genuine choice: the promotion, or a guaranteed ULTIMATE in the other slot.
//
// HEADROOM IS REQUIRED WHEN THE POOL CAN SUPPLY IT (v14.6, user 2026-08-30:
// "if you have max luck you should get an ultimate at least 1 of the cards
// 100% of the time. And at 50% luck at least 1 super 100% of the time" —
// after a max-luck game dealt no ULTIMATE). The old behavior promoted only
// WITHIN the dealt cards: a deal of low-cap/near-cap domains (PENETRATION and
// RECOIL cap at 2, SPRINT FIRE at 1, anything one level from its cap) had no
// card that could hold a +3, so the promotion clamped and the band-honesty
// pass relabeled it DOWN — a full bar paying out as "SUPER". Honest, but it
// broke the promise the bar makes. NOW: when no dealt card can absorb the
// owed rarity, ONE slot is REDEALT (weighted draw, same as the original
// deal) from the pool's domains that CAN absorb it, then promoted — so the
// guarantee is met with a real, full-paying card. The redeal replaces the
// dealt card with the LEAST headroom (keeping the stronger card and the tier
// card untouched) and never duplicates the kept card's domain. Only when NO
// available domain has the headroom (deep late-game, everything near max)
// does it fall back to the old clamped-and-honest promotion — at that point
// a full ULTIMATE is arithmetically impossible, not merely unlucky. Among
// equal candidates every pick is RANDOM, so the floor never trains players
// to expect it in a fixed slot.
function guarantee_rarity( player, opts, first_deal, deal_pool )
{
	if ( !isdefined( player ) || !isdefined( opts ) )
		return;

	// Field-read, never #using — _tod_luck imports this module (the KB cycle
	// rule), the same way roll_rarity reads the bar.
	b = 0;
	if ( isdefined( player.tod_luck_bar ) )
		b = player.tod_luck_bar;

	// (the v14.9 OVERCHARGE pass that stood here is retired with the overcharge, 2026-09-28)

	want = 0;
	if ( b >= TOD_UPG_GUAR_EPIC_BAR )
		want = TOD_RAR_EPIC;
	else if ( b >= TOD_UPG_GUAR_RARE_BAR )
		want = TOD_RAR_RARE;
	// THE OPENING HAND floors the run's first deal at RARE. Raises `want`,
	// never lowers it — a full bar on a first deal (only reachable at a station,
	// never at the round-1 draft) still guarantees the EPIC+.
	if ( IS_TRUE( first_deal ) && want < TOD_UPG_GUAR_FIRST )
		want = TOD_UPG_GUAR_FIRST;
	if ( want == 0 )
		return;

	// `want` is the FLOOR the dice are tested against; `promote` is what a card is
	// raised to when they miss it. A full bar's promotion is LEGENDARY
	// TOD_UPG_GUAR_LEG_PCT of the time (docs/187), and needs 4 levels of room.
	promote = want;
	if ( want == TOD_RAR_EPIC && RandomInt( 100 ) < TOD_UPG_GUAR_LEG_PCT )
		promote = TOD_RAR_LEGENDARY;

	cands = [];
	full = [];
	for ( i = 0; i < opts.size; i++ )
	{
		o = opts[ i ];
		// DARK UPGRADES (v17.10): skipped for the same reason the tier card is —
		// it is not a rarity the floor can raise or should be spent on. It carries
		// rarity 3 for its FRAME, so without this the "o.rarity >= want" test one
		// line below would read a dark card as "the dice already cleared the floor"
		// and silently cancel the ULTIMATE the other slot was owed.
		if ( !isdefined( o ) || o.domain == "tier" || IS_TRUE( o.dark ) )
			continue;
		if ( o.rarity >= want )
			return;                      // the dice already cleared the floor
		room = o.max - o.cur;
		if ( room <= 0 )
			continue;                    // maxed while deferred — nothing to raise
		cands[ cands.size ] = o;
		if ( room >= promote )
			full[ full.size ] = o;
	}

	// THE REDEAL (v14.6 — the user quote in the header). No dealt card can
	// absorb the whole promotion, so swap the weakest one for a domain that
	// can, IN PLACE (the struct is aliased by the caller's opts array, so
	// field-overwrite propagates without relying on array-reference
	// semantics). The kept card's domain is excluded so the two cards stay
	// distinct; the victim's own domain excludes itself by headroom (if it
	// could absorb `want` it would be in `full` and we would not be here).
	if ( full.size == 0 && cands.size > 0 && isdefined( deal_pool ) )
	{
		// victim = the dealt card with the LEAST headroom; ties random.
		victim = cands[ 0 ];
		for ( i = 1; i < cands.size; i++ )
		{
			ri = cands[ i ].max - cands[ i ].cur;
			rv = victim.max - victim.cur;
			if ( ri < rv || ( ri == rv && RandomInt( 2 ) == 0 ) )
				victim = cands[ i ];
		}
		// the kept non-tier card's domain (at most one — deals are 2 cards)
		kept_key = undefined;
		for ( i = 0; i < opts.size; i++ )
		{
			o = opts[ i ];
			if ( isdefined( o ) && o.domain != "tier" && o != victim )
				kept_key = o.domain;
		}

		sub = [];
		for ( i = 0; i < deal_pool.size; i++ )
		{
			d = deal_pool[ i ];
			if ( domain_max( player, d ) - get_level( player, d.key ) < promote )
				continue;
			if ( isdefined( kept_key ) && d.key == kept_key )
				continue;
			sub[ sub.size ] = d;
		}
		if ( sub.size > 0 )
		{
			no = make_option( player, sub[ weighted_draw( sub ) ] );
			victim.domain      = no.domain;
			victim.display     = no.display;
			victim.desc        = no.desc;
			victim.tier        = no.tier;
			victim.cur         = no.cur;
			victim.max         = no.max;
			victim.rarity      = no.rarity;
			victim.levels      = no.levels;
			victim.rarity_name = no.rarity_name;
			full[ 0 ] = victim;          // absorbs `want` by construction
		}
	}

	// HEADROOM FIRST: a promotion clamped down to +1 by the level cap would
	// defeat the guarantee outright, so cards that can absorb the whole thing
	// win over cards that cannot. Fall back to the clamped ones rather than
	// doing nothing (only reachable now when NO available domain has the
	// headroom — see the redeal above).
	pool = full;
	if ( pool.size == 0 )
		pool = cands;
	if ( pool.size == 0 )
		return;                          // tier-card-only deal: nothing to promote

	// THEN THE LOWEST RARITY, which is what stops the floor wasting itself.
	// Promoting a card that ALREADY rolled SUPER spends the guarantee on the
	// half of the deal that was already good and leaves the player holding
	// ULTIMATE + REGULAR; promoting the REGULAR instead leaves ULTIMATE + SUPER,
	// which is strictly better and costs nothing. This is not a rare corner: at
	// a full bar, 36% of deals come up one SUPER and one REGULAR, so picking
	// blind between them degraded almost 18% of ALL max-luck deals.
	lo = 5;                              // above every real rarity (1..4)
	for ( i = 0; i < pool.size; i++ )
	{
		if ( pool[ i ].rarity < lo )
			lo = pool[ i ].rarity;
	}
	best = [];
	for ( i = 0; i < pool.size; i++ )
	{
		if ( pool[ i ].rarity == lo )
			best[ best.size ] = pool[ i ];
	}

	pick = best[ RandomInt( best.size ) ];   // random among true ties only

	pick.rarity = promote;
	// Re-clamp exactly as make_option does — the per-class cap still wins.
	pick.levels = promote;
	if ( pick.cur + pick.levels > pick.max )
		pick.levels = pick.max - pick.cur;

	// ...AND THE SAME BAND-HONESTY CLAMP, or this function would be the one hole
	// left in it. The headroom preference above means we normally promote a card
	// that can absorb the whole thing, but when NO candidate can (everything on
	// the deal is near its cap) it deliberately falls back to a clamped one — and
	// without this the guarantee would stamp "ULTIMATE +3" on a card paying +1,
	// which is exactly the label this pass exists to remove. A floor that has to
	// lie to hit its number is not a floor worth having; showing the best rarity
	// actually deliverable is the honest outcome.
	if ( pick.levels >= 1 && pick.levels < pick.rarity )
		pick.rarity = pick.levels;

	pick.rarity_name = rarity_label( pick.rarity );
}


// -> an INDEX into `pool`, picked with probability proportional to tier weight.
function weighted_draw( pool )
{
	total = 0;
	for ( i = 0; i < pool.size; i++ )
		total += tier_weight( pool[ i ] );
	if ( total <= 0 )
		return RandomInt( pool.size );

	roll = RandomInt( total );
	acc = 0;
	for ( i = 0; i < pool.size; i++ )
	{
		acc += tier_weight( pool[ i ] );
		if ( roll < acc )
			return i;
	}
	return pool.size - 1;   // float/rounding belt+braces
}

function tier_weight( d )
{
	if ( !isdefined( d ) || !isdefined( d.tier ) )
		return TOD_TIER_W_B;
	if ( d.tier == TOD_TIER_S )
		return TOD_TIER_W_S;
	if ( d.tier == TOD_TIER_A )
		return TOD_TIER_W_A;
	return TOD_TIER_W_B;
}

// S/A cards shrink their SUPER+ULTIMATE slice (the rest falls back to REGULAR).
function tier_rarity_factor( tier )
{
	if ( !isdefined( tier ) )
		return 1.0;
	if ( tier == TOD_TIER_S )
		return TOD_TIER_R_S;
	if ( tier == TOD_TIER_A )
		return TOD_TIER_R_A;
	return 1.0;
}

function make_option( player, domain )
{
	o = SpawnStruct();
	o.domain = domain.key;
	o.display = domain.display;
	o.desc = domain.desc;
	o.tier = domain.tier;

	o.rarity = roll_rarity( player, domain.tier );

	o.cur = get_level( player, domain.key );
	o.max = domain_max( player, domain );   // per-class cap (RESERVE: assault 6)
	o.levels = o.rarity;
	if ( o.cur + o.levels > o.max )
		o.levels = o.max - o.cur;

	// THE BAND NEVER PROMISES MORE THAN IT PAYS (user 2026-08-27).
	//
	// `levels` has always been clamped to the headroom; `rarity` was not, so the
	// two could disagree and the card said so out loud. A domain capped below 3
	// could deal an "ULTIMATE +3" that paid +2 every single time it appeared:
	// PENETRATION and RECOIL are max 2, SPRINT FIRE is max 1, and near its cap
	// ANY domain does it — a player at Lv9 of a 10-level domain drawing an
	// ULTIMATE got "+3" and one level. The value line stayed truthful about the
	// EFFECT (that is why RECOIL could ship saying `· MAX`), but the number on
	// the band was simply wrong, and the band is the thing players compare two
	// cards on.
	//
	// CLAMPS DOWN ONLY, NEVER UP. rarity follows levels, so the card shows the
	// rarity it can actually deliver — a 2-level payout presents as SUPER, a
	// 1-level payout as REGULAR. Nothing is taken from the player: the LEVELS
	// paid are identical either way, and this only ever relabels a card that was
	// going to underdeliver. It also picks the right art, since the frame/sting
	// key off `rarity`.
	//
	// CONSEQUENCE, DELIBERATE: four card files become unreachable —
	// penetration_ultimate, recoil_ultimate, sprint_fire_super and
	// sprint_fire_ultimate. They stay zoned and installed on purpose: they cost
	// nothing but .ff bytes, they cannot render, and if a cap is ever raised the
	// art is already there. Do NOT "clean them up" — unzoning them is real risk
	// (a CARD_SLUG miss) for no gain.
	//
	// THE TIER CARD IS EXEMPT BY CONSTRUCTION: it is built by make_tier_option,
	// never here, and its `levels` means a tier rather than a count.
	if ( o.levels >= 1 && o.levels < o.rarity )
		o.rarity = o.levels;

	// v16.64 RARITY LOCK (DEADSHOT): the frame is fixed by the domain, not the
	// dice — placed AFTER the clamp on purpose (the clamp would demote a max-1
	// domain's ULTIMATE to REGULAR; the lock is the one exception the user asked
	// for). `levels` is untouched: the card still pays exactly its headroom.
	if ( isdefined( domain.rarity_lock ) )
	{
		o.rarity = domain.rarity_lock;
		o.rarity_locked = true;   // THE REACH (docs/201): a card whose rarity is fixed never reaches for another rung
	}

	o.rarity_name = rarity_label( o.rarity );

	return o;
}

// FOUR RARITIES (2026-09-28, docs/187) — 1 COMMON / 2 RARE / 3 EPIC / 4 LEGENDARY,
// rolled PER CARD. The user's odds ("meet in the middle", Legendary cut to 4%),
// a straight line from an empty luck bar to a full one:
//   bar   0% -> COMMON 56 / RARE 27 / EPIC 13 / LEGENDARY 4
//   bar 100% -> COMMON 36 / RARE 36 / EPIC 20 / LEGENDARY 8
// LOCKSTEP: docs/187 section 2 and the armory's odds table. The S/A tier factor
// still shrinks the three upper slices toward COMMON.
#define TOD_RAR_ODDS_RARE_0    27
#define TOD_RAR_ODDS_RARE_100  36
#define TOD_RAR_ODDS_EPIC_0    13
#define TOD_RAR_ODDS_EPIC_100  20
#define TOD_RAR_ODDS_LEG_0      4
#define TOD_RAR_ODDS_LEG_100    8
function roll_rarity( player, tier )
{
	// Field-read, never #using — _tod_luck imports this module (the KB cycle rule).
	b = 0;
	if ( isdefined( player.tod_luck_bar ) )
		b = player.tod_luck_bar;
	t = b / 100.0;
	if ( t < 0 )
		t = 0;
	if ( t > 1 )
		t = 1;

	rare = TOD_RAR_ODDS_RARE_0 + ( TOD_RAR_ODDS_RARE_100 - TOD_RAR_ODDS_RARE_0 ) * t;
	epic = TOD_RAR_ODDS_EPIC_0 + ( TOD_RAR_ODDS_EPIC_100 - TOD_RAR_ODDS_EPIC_0 ) * t;
	leg  = TOD_RAR_ODDS_LEG_0  + ( TOD_RAR_ODDS_LEG_100  - TOD_RAR_ODDS_LEG_0  ) * t;

	f = tier_rarity_factor( tier );
	if ( f < 1.0 )
	{
		rare = rare * f;
		epic = epic * f;
		leg  = leg  * f;
	}

	// THE HOT STREAK (docs/201 section 5): heat multiplies the EPIC and LEGENDARY slices; COMMON pays (it is the
	// remainder below; at a full bar ON FIRE the three slices still sum to 78). The guarantee never reads heat.
	hm = heat_mult_of( player );
	epic = epic * hm;
	leg  = leg  * hm;

	roll = RandomFloat( 100 );
	if ( roll < leg )
		return TOD_RAR_LEGENDARY;
	if ( roll < leg + epic )
		return TOD_RAR_EPIC;
	if ( roll < leg + epic + rare )
		return TOD_RAR_RARE;
	return TOD_RAR_COMMON;
}

// THE HOT STREAK's multiplier for this player (docs/201 section 5): _tod_luck's one table, read as fields (never
// #using: _tod_luck imports this module, the cycle rule). 1.0 when cold, or before _tod_luck has set the table.
function heat_mult_of( player )
{
	if ( !isdefined( player ) || !isdefined( player.tod_luck_heat ) || !isdefined( level.tod_heat_mult ) )
		return 1.0;
	h = player.tod_luck_heat;
	if ( h < 0 )
		h = 0;
	if ( h > level.tod_heat_mult.size - 1 )
		h = level.tod_heat_mult.size - 1;
	return level.tod_heat_mult[ h ];
}

// The one rarity -> word table (docs/187). "" for an unknown value.
function rarity_label( r )
{
	if ( r == TOD_RAR_LEGENDARY )
		return "LEGENDARY";
	if ( r == TOD_RAR_EPIC )
		return "EPIC";
	if ( r == TOD_RAR_RARE )
		return "RARE";
	if ( r == TOD_RAR_COMMON )
		return "COMMON";
	return "";
}

// ---------------------------------------------------------------------------
// CLASS TIERS — the TIER card (docs/25 §4; user 2026-08-22)
// ---------------------------------------------------------------------------

function tier_card_pct()
{
	// [tod v19.9] tod_dev_upgrades, not tod_dev — the 100% tier card is a
	// promotion-flow test, not something a normal-play dev session wants.
	if ( IS_TRUE( level.tod_dev_upgrades ) )
		return 100;   // DEV: every deal carries it — the promotion flow is testable in one session
	return TOD_TIER_CARD_PCT;
}

// v16.56 — is the promotion OWED rather than rolled? See TOD_UPG_GUAR_TIER_BAR.
// Asks the FULL eligibility on purpose: the user's rule is "max luck + PaP +
// eligible, floor included". A floor-blocked player is not owed anything here
// and falls through to the ordinary roll (which may still deal them the card
// LOCKED, v14.39 — that path is unchanged).
function tier_card_guaranteed( player )
{
	if ( !tier_card_eligible( player ) )
		return false;
	// Field-read, never #using — _tod_luck imports this module (the KB cycle
	// rule), the same way roll_rarity and guarantee_rarity read the bar.
	b = 0;
	if ( isdefined( player.tod_luck_bar ) )
		b = player.tod_luck_bar;
	return ( b >= TOD_UPG_GUAR_TIER_BAR );
}

// THE ONE TIER-CARD ROLL (v16.56). Both deal paths — roll_options and the
// maxed-player pre-roll in run_upgrade_event — ask this and nothing else, so
// the guarantee cannot hold on one path and miss on the other. Callers still
// own the eligibility test in front of it (but-for-floor on the deal so a
// locked card can be shown; full eligibility on the pre-roll, where a locked
// card alone would be an empty pause). READ THE BAR BEFORE IT IS SPENT: both
// callers run before the participants' post-event reset, and the station
// resets only after a successful pick.
function tier_card_roll( player )
{
	if ( tier_card_guaranteed( player ) )
		return true;
	return ( RandomInt( 100 ) < tier_card_pct() );
}

// THE DRAFTABLE-DOMAIN RULE, IN ONE PLACE (v14.24). Returns every domain this
// player could still be dealt: available to them, and not yet at its max.
// roll_options and has_upgrade_headroom both call this — deliberately ONE
// owner rather than two copies kept in step by discipline, which is the exact
// shape that has burned this codebase before (the hand-copied 0.04 in
// _tod_bosses, the RUN AND GUN constants across two files). Change what makes
// a domain draftable HERE and both callers follow by construction.
function eligible_pool( player )
{
	pool = [];
	if ( !isdefined( level.tod_domains ) )
		return pool;

	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		if ( !domain_available( player, d ) )
			continue;
		if ( get_level( player, d.key ) < domain_max( player, d ) )
			pool[ pool.size ] = d;
	}
	return pool;
}

// TRUE when an upgrade deal could still GIVE this player something: a domain
// with headroom, or the class-tier promotion.
//
// WHY IT EXISTS (v14.24, user: "player has no more upgrades so they cant even
// get rid of the luck sfx"): a fully-maxed player's luck bar can reach the
// overcharge ceiling and then never spend, because the thing that clears the
// bar is taking a card and there is no card to take. _tod_luck's
// overcharge_driver polls this so the zap SFX goes quiet in that state instead
// of firing every ~3 seconds for the rest of the run. Polled live, never
// latched: a tier promotion resets the gun-scoped domains and hands the player
// real headroom again, and the cue must come back on its own when it does.
//
// *** IT IS NOT THE SAME TEST AS roll_options, AND THAT IS DELIBERATE — DO NOT
// "CORRECT" IT TO MATCH. *** roll_options returns undefined when the pool is
// empty AND its tier_deal ROLL missed (RandomInt(100) < tier_card_pct()); this
// asks the roll-free question tier_card_eligible( player ). The difference is
// the whole point: a maxed-but-tier-eligible player WILL draw the promotion
// eventually and clear their bar, so the cue must keep playing for them even
// though any single deal may hand them nothing. Gating on the random roll
// would silence the zap for players who can still spend it. (Caught in review
// by a peer session, 2026-08-30 — the divergence was intended but undocumented,
// which is how it would have been "fixed" into a bug.)
function has_upgrade_headroom( player )
{
	if ( !isdefined( player ) || !isplayer( player ) )
		return false;

	pool = eligible_pool( player );
	if ( pool.size > 0 )
		return true;

	return tier_card_eligible( player );
}

// THE FLOOR REQUIREMENT for a promotion INTO next_tier. 0 = none.
//
// Read by tier_floor_ok only. Kept as its own function so the two numbers the
// user gave live in exactly one place; the fallthrough extends the ladder's
// own spacing (t4 -> 30) so a fourth tier can never arrive ungated by silence.
function tier_floor_req( next_tier )
{
	if ( next_tier < 2 )
		return 0;                                          // tier 1 is where everyone starts
	if ( next_tier == 2 )
		return TOD_TIER2_FLOOR;
	if ( next_tier == 3 )
		return TOD_TIER3_FLOOR;
	return ( next_tier - 1 ) * ( TOD_TIER3_FLOOR - TOD_TIER2_FLOOR );
}

// Has this player CLIMBED far enough for their next promotion?
//
// The high-water is a per-player, alive-only, monotonically rising record of
// the real floor they have stood on (_tod_gauge). It never falls, so the gate
// asks "have you been up there", not "are you up there now" — you can promote
// at a base station or on a teleporter pad, as long as you earned it. It is
// also NOT re-checked by anything after a card is dealt for the same reason:
// a card that was legal when dealt stays legal.
//
// NOT waived by level.tod_dev. A dev session that skips its own gate cannot
// test it, and the dev build already gets there fast (money loop + 100% tier
// odds); the climb to floor 10 is the thing being verified.
function tier_floor_ok( player )
{
	need = tier_floor_req( tod_classes::tier( player ) + 1 );
	if ( need <= 0 )
		return true;
	// docs/160: tier_progress is floors CLIMBED on the climb layout and
	// floors DESCENDED on the descent (TOD_GAUGE_DESCENT in _tod_gauge) —
	// the requirement is the same number of floors either way.
	return tod_gauge::tier_progress( player ) >= need;
}

// Can this player be dealt a TIER card right now? ALL of: below the top tier,
// HIGH ENOUGH UP THE TOWER for the tier they are promoting into (v14.35 — see
// the TOD_TIER2_FLOOR block), a next gun registered AND its level-0 asset
// linked (never deal a card that cannot pay out), the CURRENT class gun PaP'd
// (by name, or the free-PaP latch that reconcile turns into the _up form
// within 1s), and no powerup gun in hand (its restore would fight the swap).
//
// tier_up() re-asks this whole question before promoting, which is what makes
// the floor gate hold on every path into a promotion rather than just on the
// deal — including the personal station's deferred cards.
function tier_card_eligible( player )
{
	return ( tier_card_ready_but_for_floor( player ) && tier_floor_ok( player ) );
}

// Everything a TIER card needs EXCEPT the climb.
//
// Split out so the panel hint can ask the one question it actually cares about
// — "is the FLOOR the only thing stopping this player?" — without a second copy
// of the other four conditions drifting away from this one. There is still
// exactly ONE implementation of each rule: this function owns the four, and
// tier_floor_ok owns the floor. Never inline either back into a caller.
//
// v16.70: the rules themselves moved into tier_not_ready_reason (one string per
// refusal, "" when ready) so the dev deny-print can NAME the refusal without a
// second copy of the ladder — this is now the boolean view of that one owner.
function tier_card_ready_but_for_floor( player )
{
	return ( tier_not_ready_reason( player ) == "" );
}

// DEV ONLY — why is this player NOT being dealt the TIER card? Composes the
// not-ready ladder, then the floor, then the bar/odds, in the order the deal
// asks them. Free lane (IPrintLn — no triggerstring, no art); never shown to
// a player in a shipping build.
function tier_deny_reason( player )
{
	why = tier_not_ready_reason( player );
	if ( why != "" )
		return why;
	if ( !tier_floor_ok( player ) )
		return "floors " + tod_gauge::tier_progress( player ) + " < " + tier_floor_req( tod_classes::tier( player ) + 1 ) + " (dealt LOCKED at most)";
	b = 0;
	if ( isdefined( player.tod_luck_bar ) )
		b = player.tod_luck_bar;
	return "eligible; luck " + int( b ) + "/" + TOD_UPG_GUAR_TIER_BAR + " -> " + ( ( b >= TOD_UPG_GUAR_TIER_BAR ) ? "GUARANTEED" : ( "rolled at " + tier_card_pct() + "%" ) );
}

// THE ONE OWNER of "everything a TIER card needs except the climb" (the header
// above tier_card_ready_but_for_floor). Returns "" when every rule passes, or
// the first failing rule as a short reason string.
function tier_not_ready_reason( player )
{
	if ( !isdefined( player ) || !isplayer( player ) || !isdefined( player.tod_class ) )
		return "no class";
	// NEVER PROMOTE A CRAWLER (v15, shipped with item 9 — the change that first
	// let a downed player be dealt cards at all).
	//
	// Normal last stand does NOT take your weapons (_zm_laststand.gsc:212-228
	// only calls TakeAllWeapons on the is_zombie branch) — it leaves the whole
	// inventory and SwitchToWeapon's the last-stand pistol, then re-asserts that
	// switch a second later via wait_switch_weapon. So without this test
	// class_primary_in_inventory() still finds the class gun and a crawler looks
	// perfectly eligible, while tier_up's swap_primary would be taking and
	// giving primaries underneath stock's pistol handling. Two systems writing
	// the same inventory a second apart is not a race worth having for a card
	// that will still be there when they are revived.
	//
	// This sits in tier_card_ready_but_for_floor rather than tier_card_eligible
	// ON PURPOSE: this function owns the "everything except the climb" rules, so
	// putting it here ALSO suppresses the "TIER 2 AT FLOOR 10" badge for a
	// downed player — the floor is not what is stopping them, and saying so
	// would be exactly the misdirection this function's header warns about.
	if ( player laststand::player_is_in_laststand() )
		return "in last stand";
	if ( IS_TRUE( player.tod_tier_busy ) || IS_TRUE( player.tod_swap_busy ) )
		return "weapon swap in progress";
	if ( tod_classes::tier( player ) >= tod_classes::tier_max() )
		return "already top tier";
	next = tod_classes::next_gun( player );
	if ( !isdefined( next ) )
		return "no next gun registered";
	if ( !isdefined( tod_classes::base_weapon( next ) ) )
		return "next gun not linked";
	g = tod_classes::gun( player );
	w = player class_primary_in_inventory();
	if ( !isdefined( g ) || !isdefined( w ) )
		return "class gun not in inventory";
	if ( !IsSubStr( w.name, g.stem ) || tod_classes::pap_tier( player, w ) == 0 )
		return "class gun not Pack-a-Punched (" + w.name + ")";
	if ( isdefined( player.zombie_vars ) && ( IS_TRUE( player.zombie_vars[ "zombie_powerup_minigun_on" ] ) || IS_TRUE( player.zombie_vars[ "zombie_powerup_tod_wunderstrahl_on" ] ) ) )
		return "powerup gun in hand";
	return "";
}

// -> the floor this player still has to REACH before a TIER card can be dealt,
// or 0 when the floor is not what is stopping them.
//
// THE PANEL LINE ANSWERS EXACTLY ONE QUESTION — "I Pack-a-Punched, so where is
// my tier card?" — and it has to stay silent for every other reason or it
// becomes noise that misdirects: a player who has not PaP'd yet would be told
// to climb, which is true and useless, and a top-tier player would be told to
// climb toward a promotion that does not exist. So this returns non-zero ONLY
// when every other condition is already satisfied.
function tier_floor_pending( player )
{
	if ( !tier_card_ready_but_for_floor( player ) )
		return 0;
	if ( tier_floor_ok( player ) )
		return 0;
	return tier_floor_req( tod_classes::tier( player ) + 1 );
}

// ---------------------------------------------------------------------------
// THE TIER GATE TOASTS (2026-09-02, user: "make sure players are somehow aware
// of this through UI triggers on pap or some way").
//
// Two per-player toasts on the FREE lane (RT 2026-10-05: THE TOAST, _tod_upgrade_ui self_toast kinds 4 / 5,
// drawn in our typeface by TodToast.lua; they were IPrintLnBold lines): no triggerstring slot
// (the PaP prompt is a DEAD lane for custom copy — isPAPHint, see
// _tod_powerups' REQUIRES POWER note) and no art. Each fires AT MOST ONCE PER
// TIER per player, latched on the tier it was said for, so a revive (which
// flips tier_card_ready_but_for_floor off and back on) cannot repeat it:
//   (a) "CLASS TIER 3 UNLOCKS AT FLOOR 30" — the moment the class gun is
//       PaP'd (or the free-PaP latch lands) while the climb is still short.
//       Same rule as the panel badge: tier_floor_pending() > 0.
//   (b) "FLOOR 30 REACHED - CLASS TIER 3 UNLOCKED" — the moment the
//       high-water clears the next promotion's floor; "- PACK-A-PUNCH TO
//       PROMOTE" is appended while the gun is still dry. It also fires right
//       after a promotion for a player already above the NEXT floor, which is
//       simply true at that moment.
// Held while the upgrade panel is up (tod_menu_frozen): the panel carries the
// badge, and a toast under the cards would fight the deal. 0.5 s poll on the
// same functions the panel reads — ONE authority (tier_floor_req /
// tier_floor_pending / tier_card_ready_but_for_floor), never a second copy.
// self = player; threaded once from player_upgrade_setup.
function tier_gate_toasts()
{
	self endon( "disconnect" );

	told_a_tier = 0;   // the next_tier line (a) was said for
	told_b_tier = 0;   // the next_tier line (b) was said for

	while ( true )
	{
		wait 0.5;
		if ( !isdefined( self.tod_class ) || IS_TRUE( self.tod_menu_frozen ) )
			continue;
		next_tier = tod_classes::tier( self ) + 1;
		if ( next_tier > tod_classes::tier_max() )
			continue;
		need = tier_floor_req( next_tier );
		if ( need <= 0 )
			continue;

		// (a) packed, climb short (docs/160: the floor SHOWN is the one the
		// player will stand on when the requirement clears — 40/20 going down)
		if ( told_a_tier != next_tier && tier_floor_pending( self ) > 0 )
		{
			told_a_tier = next_tier;
			// THE TOAST, kind 4, in our typeface (RT 2026-10-05; it was a stock-font IPrintLnBold)
			self tod_upgrade_ui::self_toast( 4, next_tier * 1000 + tod_gauge::tier_floor_display( need ) );
		}

		// (b) climb cleared
		if ( told_b_tier != next_tier && tod_gauge::tier_progress( self ) >= need )
		{
			told_b_tier = next_tier;
			// THE TOAST, kind 5: "FLOOR f REACHED - CLASS TIER n UNLOCKED", + "PACK-A-PUNCH TO PROMOTE" while the gun
			// is still dry (+ 100000), in our typeface (RT 2026-10-05; it was a stock-font IPrintLnBold)
			code = next_tier * 1000 + tod_gauge::tier_floor_display( need );
			if ( !( self class_gun_packed() ) )
				code = code + 100000;
			self tod_upgrade_ui::self_toast( 5, code );
		}
	}
}

// self = player. Is the class primary Pack-a-Punched (or latched as packed by
// the free-PaP drop)? The same test tier_card_ready_but_for_floor applies,
// without its laststand / powerup-gun / top-tier terms — so the toast's
// "PACK-A-PUNCH TO PROMOTE" suffix answers only the question it names.
function class_gun_packed()
{
	g = tod_classes::gun( self );
	w = self class_primary_in_inventory();
	if ( !isdefined( g ) || !isdefined( w ) )
		return false;
	return ( IsSubStr( w.name, g.stem ) && tod_classes::pap_tier( self, w ) > 0 );
}

// self = player. Push the panel's tier-requirement line for the deal that is
// about to be presented.
//
// ZERO-BIT LANE, deliberately: the clientuimodel pool is at its PROVEN 61-bit
// ceiling (18 fields, APPEND ONLY), so this rides the int-only LuiNotifyEvent
// channel the tower gauge, the max-HP feed and the owned-upgrades sync already
// use. tod_upgrade.lua parks it in CoD.TodTierNeed and the choice panel reads
// it while it paints.
//
// SENT UNCONDITIONALLY, INCLUDING 0, before EVERY deal — that is what keeps a
// stale value from surfacing on a later deal, and it is why nothing has to
// clear the line when the panel closes. Called from the two present_choice
// sites (the round event and the personal station); a third presenter must
// call it too.
function push_panel_hints()
{
	self LuiNotifyEvent( &"tod_upg_tier_need", 1, tier_floor_pending( self ) );

	// v16: the CLASS BADGE, docs/59. Same zero-bit lane and the same
	// unconditional-every-deal rule as the line above -- the clientuimodel pool
	// is at 60 of its PROVEN 61, so a new field was not affordable and is not
	// needed. class_id() returns 0 for a classless (pre-draft) player, which
	// tod_upgrade.lua reads as "hide the plate", so no case needs special-casing.
	//
	// RENAMED from push_tier_hint(): it pushes two facts now, and a name that
	// says "tier" would be the next reader's wrong turn. Two call sites, both
	// present_choice presenters; a third presenter must call this too.
	self LuiNotifyEvent( &"tod_upg_class", 1, tod_classes::class_id( self.tod_class ) );
}

// The card's "level" field (todUpgAL/BL, 4 bits) carries
// (class_id - 1) * 2 + (target_tier - 2) -> 0..7, so tod_upgrade.lua can name
// the gun the promotion hands out (its TIER_LADDER table).
function tier_card_code( player )
{
	cid = tod_classes::class_id( player.tod_class );
	nt = tod_classes::tier( player ) + 1;
	code = ( cid - 1 ) * 2 + ( nt - 2 );
	if ( code < 0 )
		code = 0;
	if ( code > 15 )
		code = 15;
	return code;
}

function make_tier_option( player )
{
	o = SpawnStruct();
	o.domain = "tier";
	o.display = "CLASS TIER";
	o.desc = "promote your class: a new weapon, unpacked; every upgrade card stays";   // 2026-09-29: "gun upgrades reset" was false (no live card is gun-scoped)
	if ( isdefined( player.tod_class ) && player.tod_class == "necromancer" )
		o.desc = "promote your class: a new staff and stronger summoned helpers; every upgrade card stays";   // W3E 2026-10-05: tiers 2/3 hand out the Soul Staff / Crown of the Damned (register_gun), not a stronger skull
	o.tier = TOD_TIER_S;
	o.rarity = 3;               // the ULTIMATE frame + sting carry it until the tier art lands
	o.rarity_name = "TIER";
	o.cur = tier_card_code( player );
	o.max = tod_classes::tier_max();
	o.levels = 1;
	// THE LOCK (v14.39, user 2026-08-31: "a design where you get the card but
	// you cant select it"). A floor-blocked player is now DEALT the promotion
	// and shown which gun it is — the card just cannot be taken, and the Lua
	// draws it dimmed with the gate badge under it. Seeing the thing you are
	// climbing toward beats an absence you have to infer.
	//
	// The user was told, and accepted, that this spends the deal's right slot:
	// on the ~20% of deals where the tier card rolls below the gate floor they
	// get one real card instead of two. It is bounded by that roll and by how
	// few events happen below floor 10 — it is NOT every deal.
	o.locked = ( tier_floor_pending( player ) > 0 );
	return o;
}

// THE PROMOTION. self = nothing; player = the promoted player. Order matters:
//   1. every GUN-scoped domain to 0 (CLASS-scoped — DMG REDUCTION, LUCK — kept)
//      + the live effects those levels were driving un-applied;
//   2. tier++ and the free-PaP latch CLEARED (mandatory — reconcile would
//      otherwise pull the new gun straight to its _up form on the next tick
//      and skip the "PaP it again" step the whole design rests on);
//   3. the weapon: the next gun's level-0 form, given with FULL start ammo
//      (a tier-up is a gift), via the proven swap order; alt weapons swapped
//      if they differ; a `grant` domain (the Stormbreaker's THOR'S THUNDER)
//      set to Lv1 the moment the gun arrives;
//   4. the pause list re-synced and the sting.
// Returns false if nothing happened (not eligible / assets missing).
function tier_up( player )
{
	if ( !tier_card_eligible( player ) )
		return false;
	g_old = tod_classes::gun( player );
	g_new = tod_classes::next_gun( player );
	want = tod_classes::base_weapon( g_new );
	if ( !isdefined( g_old ) || !isdefined( g_new ) || !isdefined( want ) )
		return false;

	player.tod_tier_busy = true;   // holds the body loop's reconcile off until the promotion has fully landed
	// An in-flight twin swap (the body loop's walk, up to 1s) must finish
	// first — two GIVE-before-TAKE swaps at once could leave 3-4 primaries
	// and the engine silently drops one. Bounded wait, then bail if still busy.
	for ( i = 0; i < 30 && IS_TRUE( player.tod_swap_busy ); i++ )
		wait 0.05;
	if ( !isdefined( player ) || IS_TRUE( player.tod_swap_busy ) )
	{
		if ( isdefined( player ) )
			player.tod_tier_busy = undefined;
		return false;
	}
	old = player class_primary_in_inventory();   // resolve AFTER the wait, BEFORE the tier changes
	if ( !isdefined( old ) )
	{
		player.tod_tier_busy = undefined;
		return false;
	}

	player notify( "tod_tier_up" );

	// 1. THE WEAPON FIRST — if the swap cannot land (player stripped mid-swap)
	//    nothing else is committed: no reset, no tier, no latch change.
	if ( IS_TRUE( level.tod_classes[ g_new.class_key ].additive ) )
	{
		// ADDITIVE CLASS (v18.30; inert today - no registered class sets
		// .additive): the promotion ADDS the next gun and takes nothing.
		// Raised in hand so the player sees what they got.
		if ( !( player HasWeapon( want ) ) )
		{
			player tod_classes::give_camo_weapon( want );
			player GiveStartAmmo( want );
		}
		player SwitchToWeapon( want );
	}
	else if ( want != old )
	{
		ok = player swap_primary( old, want, true );
		if ( !ok || !isdefined( player ) )
		{
			if ( isdefined( player ) )
				player.tod_tier_busy = undefined;
			return false;
		}
	}
	else
		player GiveStartAmmo( old );   // same asset (cannot happen past the null ladder) — still a refill

	// 2. reset every domain that does not survive for THIS player —
	// domain_survives_tier is the one authority (v14.13: scope "class" can be
	// limited to a single class; SCAVENGER survives for the assault alone)
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		if ( domain_survives_tier( player, d ) )
			continue;
		// DARK UPGRADES (v17.10): the dark BIT dies with the levels. Cleared
		// BEFORE the level test below, because a domain can hold a dark bit while
		// sitting at level 0 is impossible today but the ordering costs nothing and
		// a stale bit would be worse than a stale level: twin_suffix would keep
		// asking for a dark rung on a gun that has none.
		if ( isdefined( player.tod_dark ) && IS_TRUE( player.tod_dark[ d.key ] ) )
			player.tod_dark[ d.key ] = undefined;
		if ( get_level( player, d.key ) <= 0 )
			continue;
		player.tod_levels[ d.key ] = 0;
		// the pause list hides level-0 rows (AetheriumStartMenu.lua filters lvl > 0)
		player LuiNotifyEvent( &"tod_upg_sync", 3, tod_upgrade_ui::domain_id( d.key ), 0, sync_max( player, d ) );
	}
	player reset_gun_state();

	// 3. promote + clear the latch
	player.tod_tier = tod_classes::tier( player ) + 1;
	player.tod_pap_owned = undefined;
	if ( g_new.stem == g_old.stem ) tod_classes::pap_tier_forget( player, g_new.stem );   // the Necromancer's skull: same gun, new tier (2026-09-26)
	player.tod_upg_maxed_told = undefined;   // there is a whole new ladder to climb

	// alt weapons: swap if they differ between the two guns
	if ( isdefined( g_old.alt ) && ( !isdefined( g_new.alt ) || g_new.alt != g_old.alt ) )
	{
		a = GetWeapon( g_old.alt );
		if ( isdefined( a ) && a != level.weaponNone && ( player HasWeapon( a ) ) )
			player TakeWeapon( a );
	}
	if ( isdefined( g_new.alt ) && ( !isdefined( g_old.alt ) || g_new.alt != g_old.alt ) )
	{
		a = GetWeapon( g_new.alt );
		if ( isdefined( a ) && a != level.weaponNone && !( player HasWeapon( a ) ) )
			player GiveWeapon( a );
	}
	if ( isdefined( g_new.grant ) && isdefined( player.tod_levels[ g_new.grant ] ) && player.tod_levels[ g_new.grant ] < 1 )
		player.tod_levels[ g_new.grant ] = 1;

	// THE SIDEARM IS PART OF THE PROMOTION (user 2026-08-24: "every tier for
	// every class needs its own secondary"). Before this, tier_up moved the
	// primary, the alt and the grant and left the sidearm alone — which was
	// correct while there was one sidearm per class and wrong the moment there
	// were three.
	//
	// AFTER player.tod_tier is written, not before: give_secondary resolves the
	// name from the tier, so running it any earlier hands back the sidearm the
	// player is being promoted OUT of. It is also after the primary swap has
	// already committed (step 1 returns false and changes nothing if that fails),
	// so the sidearm can never be the only thing that moved.
	//
	// The NEW sidearm arrives in its BASE form even if the old one was
	// Pack-a-Punched — the same rule the primary follows, where a TIER card
	// hands you the new gun at its level-0 form. take_foreign_secondaries inside
	// give_secondary reaps the old one in either form.
	player tod_classes::give_secondary( g_new.class_key, player.tod_tier );

	// 4. feedback
	player.tod_tier_busy = undefined;
	player apply_move_speed();
	player refresh_upgrade_list();
	player notify( "tod_tier_up_done", player.tod_tier );
	// v18.9 — SAY WHAT IT COST, because nothing else does. Three separate
	// Workshop reports describe the same surprise (.vers 2026-09-02 "taking the
	// kit upgrade wipes your PaP on your guns"; Nello 2026-08-29 "a class upgrade
	// can actually feel like a downgrade"). The card art carries no warning, the
	// LUI fallback that once did is dead behind USE_TIER_CARD_ART, and
	// "tod_tier_up_done" has no listener anywhere. This is the free lane: an
	// IPrintLnBold costs no triggerstring slot and no clientfield bit.
	//
	// It names BOTH weapons because the sidearm is swapped in the same breath
	// (give_secondary, a few lines up) and arrives in its base form too.
	// RT 2026-10-05: THE TOAST, kind 6, in our typeface (it was a stock-font IPrintLnBold, read as the deal closed)
	player tod_upgrade_ui::self_toast( 6, 0 );
	// DISTRACTION (domain 41): a grenade is INVENTORY, and this path writes a
	// LEVEL without touching inventory. Guarded level pointer, set in
	// _tod_distraction::init - never a #using (that module imports us for
	// get_level; importing it back is the KB cycle rule). Undefined = the module
	// is not in the build, and the grenade simply reconciles on next spawn.
	// Ours SURVIVES the promotion (set_scope "class"), so this is not a re-grant
	// but a re-assert: the reconcile re-stamps the tactical slot pointer, which
	// nothing else in tier_up touches.
	if ( isdefined( level.tod_distract_reconcile ) )
		player [[ level.tod_distract_reconcile ]]();
	// RIOT SHIELD (domain 45): same lane, same reason — equipment is inventory
	// and this path writes a level. Pointer set in _tod_riotshield::init.
	if ( isdefined( level.tod_shield_reconcile ) )
		player [[ level.tod_shield_reconcile ]]();
	player PlayLocalSound( "tod_tier_sting" );   // PK17: the promotion's own sting (a lock-in, a swell, a sub drop; tod_stings.csv)
	return true;
}

// self = player. Un-apply the live effects the reset levels were driving —
// the 1s body loop only ever SETS most of them.
function reset_gun_state()
{
	// ⚠️ v15 AUDIT (item 19). This function clears RUNNING COUNTERS, not levels
	// — tier_up's loop above owns the levels. When persistence became the
	// default, four of the six lines here were quietly clearing progress toward
	// a payout on a domain the player now KEEPS, which reads in play as "my
	// upgrade got reset" even though the level survived.
	//
	// KEPT (the domain still resets, so its counter must too):
	//   tod_thor_next_ms  — THOR'S THUNDER is Leviathan-bound, still "gun".
	// KEPT FOR A DIFFERENT REASON (not a progress counter):
	//   tod_feed_t        — BULLET FEED's DEBT, i.e. fractional ammo owed
	//                       against the OLD gun's fire rate. The domain
	//                       persists now, but carrying a debt across a weapon
	//                       swap would pay it at the new gun's rate. Zeroing
	//                       loses at most one round.
	//   tod_scav_pay_ms   — a same-frame de-dupe stamp, meaningless after a
	//                       promotion; clearing it can only ever be correct.
	// NO LONGER CLEARED (the domain persists, so the progress does too):
	//   tod_bounty_bank      — BOUNTY's sub-10-point remainder. Confiscating it
	//                          was always odd; now the domain survives, it is
	//                          simply theft.
	//   tod_scav_bank        — SCAVENGER's bank (tenths of a kill toward the
	//                          next round, v16.42; the kill counter before). A player one
	//                          kill from a reserve round lost it to a promotion.
	//   (tod_killreload_kills was the third and the worst case — a 55-kill
	//   accumulator at Lv1 — until KILL RELOAD was retired 2026-09-01.)
	self.tod_thor_next_ms = undefined;
	// ADRENALINE (v16): the domain is scope "gun", so tier_up wipes its LEVEL —
	// a cooldown stamp or a half-built multi-kill streak must not outlive it.
	// Listed here under the same rule as thor above: the domain still resets, so
	// its counters must too.
	self.tod_adren_next_ms = undefined;
	self.tod_adren_mk_n = 0;
	self.tod_adren_mk_ms = undefined;
	self.tod_adren_until = undefined;
	self.tod_feed_t = 0;              // BULLET FEED debt — see the audit note above
	self.tod_scav_pay_ms = undefined;
	// (The TIRELESS un-apply lived here until 2026-08-26. Nothing to undo now:
	// no script touches the sprint knobs or grants specialty_staminup.)
	// SPRINT FIRE: the body loop's UnsetPerk branch strips it within 1s.
}

// Returns true when the card actually paid out, false when it did not (a
// refused TIER pick, a dead/maxed card). Callers fall back to the OTHER card
// on a refused tier pick so a deal (or a station buy) is never forfeited.
function apply_upgrade( player, o )
{
	// DARK UPGRADE (v17.10) — FIRST, above every levels test. A dark card is
	// dealt on a domain with ZERO headroom by definition, so `o.levels` is 0 and
	// every branch below would refuse it. It pays a BIT, not levels; see the
	// DARK UPGRADES block for why it must never be stored as level max+1.
	if ( IS_TRUE( o.dark ) )
	{
		if ( !isdefined( player.tod_dark ) )
			player.tod_dark = [];
		if ( IS_TRUE( player.tod_dark[ o.domain ] ) )
			return false;   // already held — the pool should have filtered it, but a concurrent deal can race
		player.tod_dark[ o.domain ] = true;
		player notify( "tod_upgrade_applied", o.domain );
		player notify( "tod_dark_applied", o.domain );
		// Inventory domains reconcile off a LEVEL write; a dark bit is not one,
		// so poke the same two pointers by hand. Both are guarded — undefined
		// means the module is not in this build.
		if ( isdefined( level.tod_distract_reconcile ) )
			player [[ level.tod_distract_reconcile ]]();
		if ( isdefined( level.tod_shield_reconcile ) )
			player [[ level.tod_shield_reconcile ]]();
		// AND RE-SYNC THE PAUSE ROWS (fix 2026-09-04, user: "I have both dark
		// luck and dark riot shield and neither of them are in the pause menu
		// showing the dark version"). The dark bit reaches the client ONLY as
		// sync_max()'s +200 on a tod_upg_sync row, and this early return skipped
		// the refresh_upgrade_list() every other apply path ends with — so a dark
		// pick was invisible until some OTHER domain gained a level and re-sent
		// the whole table. In the retired spire that could be a long time or
		// never: a won trial was the only deal, and a dark card is by definition
		// dealt on a domain with no headroom left.
		//
		// THE LESSON: an early return past the tail of a function inherits none
		// of its obligations. Every payout lane owes the same three — the level
		// write (here, the bit), the inventory reconcile, and the client sync.
		player refresh_upgrade_list();
		tod_ability_fx::card_taken( player, o.rarity );   // docs/206: the rarity burst + sting
		return true;
	}
	if ( o.levels <= 0 )
		return false;
	// CLASS TIER card: OPT-IN only. A timeout locks the focused card for every
	// other domain, but a weapon swap the player did not choose must never
	// happen — a timed-out tier pick is refused (docs/25 §4.2) and the caller
	// applies the other card instead.
	if ( o.domain == "tier" )
	{
		if ( IS_TRUE( player.tod_upg_timed_out ) )
			return false;
		ok = tier_up( player );
		if ( ok ) tod_ability_fx::card_taken( player, 4 );   // docs/206: the promotion bursts like a LEGENDARY
		return ok;
	}
	// MONOTONIC (verify 2026-08-20): never trust o.cur — it was snapshotted
	// at roll time, and a concurrent apply (personal-station pick landing in
	// the same window a round event rolled, or vice versa) makes it stale.
	// Re-read, add ON TOP, clamp at max, and never write downward.
	cur = get_level( player, o.domain );
	lv = cur + o.levels;
	if ( isdefined( o.max ) && lv > o.max )
		lv = o.max;
	if ( lv <= cur )
		return false;   // the domain already advanced past this card — nothing to add
	player.tod_levels[ o.domain ] = lv;
	player notify( "tod_upgrade_applied", o.domain );
	tod_ability_fx::card_taken( player, o.rarity );   // docs/206: the rarity burst + sting
	// DISTRACTION (domain 41): a grenade is INVENTORY, and this path writes a
	// LEVEL without touching inventory. Guarded level pointer, set in
	// _tod_distraction::init - never a #using (that module imports us for
	// get_level; importing it back is the KB cycle rule). Undefined = the module
	// is not in the build, and the grenade simply reconciles on next spawn.
	if ( isdefined( level.tod_distract_reconcile ) )
		player [[ level.tod_distract_reconcile ]]();
	// RIOT SHIELD (domain 45): same lane, same reason — equipment is inventory
	// and this path writes a level. Pointer set in _tod_riotshield::init.
	if ( isdefined( level.tod_shield_reconcile ) )
		player [[ level.tod_shield_reconcile ]]();
	player refresh_upgrade_list();

	// body domains apply instantly, not on the next spawn/tick
	if ( o.domain == "sprint" || o.domain == "mobility" )
		player apply_move_speed();
	// VITALITY (v14.11): the new max HP lands NOW, additively — the same
	// shape stock jugg uses (+= on the current max), so it composes with an
	// active jugg instead of being swallowed by it. The gained HP is also
	// HEALED in (a card is a payoff, the jugg-purchase precedent), unlike the
	// body loop's floor, which only ever raises the ceiling. If stock later
	// clobbers the max (jugg loss restore, spawn reboot), the body-loop floor
	// re-raises it within a second.
	if ( o.domain == "vitality" )
	{
		// flat +10 / Lv since 2026-09-27 (class pass 2), the same number max_hp_floor pays
		// (it was ladder5, which stops at Lv5 - Lv6 would have landed only on the floor tick)
		hp_add = vitality_hp( lv ) - vitality_hp( cur );   // the falling ladder since 2026-09-28
		player.maxhealth = player.maxhealth + hp_add;
		player SetMaxHealth( player.maxhealth );
		if ( IsAlive( player ) && !( player laststand::player_is_in_laststand() ) )
		{
			player.health = player.health + hp_add;
			if ( player.health > player.maxhealth )
				player.health = player.maxhealth;
		}
	}
	// twin domains swap the gun in place immediately — reconcile is generic
	// now (it compares the held variant to the axes' levels), so every apply
	// may call it; it returns in one compare when nothing changed.
	player reconcile_twin();

	// (apply print removed 2026-08-20 — the card flash IS the confirmation)
	return true;
}

// ---------------------------------------------------------------------------
// World pause — spawning halts via the stock world_is_paused flag
// (round_spawning waits on it, _zm.gsc:3747); live zombies get frozen +
// ignoreall so they stand down while everyone chooses.
//
// AND EVERY UPRIGHT PLAYER IS INVULNERABLE FOR AS LONG AS IT HOLDS (v17.94,
// user 2026-09-05: "During these upgrades we should make players invincible
// as well just in case"). The freeze is built from per-actor writes — rate,
// ignoreall, a parked tree — and the Fury just proved that an actor with its
// own writers can slip one for a while. The engine's invulnerability is the
// net UNDER all of that: no melee notetrack, no flame tick, no splash and no
// script DoDamage lands while it is on. It is the same call the zombie-blood
// window and the finale's depart already lean on. Applied to
// players alive and upright (a downed player was never frozen and is
// bleeding, not being hit); released only for players THIS function armed
// (tod_pause_invuln) and only when no other lane still holds the flag —
// stock uses the same call for its out-of-bounds kill and nothing else in
// play, so the lanes to respect are ours: zombie blood, depart.
// Symmetric with upgrade_damage_cb's return 0: nobody hits anybody.
// A player who spawns INTO a pause is not covered (the world is frozen around
// them); the next set_world_pause( true ) covers them — the arena's win and
// run_upgrade_event both call it, idempotently.
// ---------------------------------------------------------------------------

function set_world_pause( on )
{
	// Keep both edges even when an entire pause falls between recorder samples.
	if ( IS_TRUE( level.tod_dev ) )
	{
		if ( on ) level.tod_ai_diag_pause_on = GetTime();
		else level.tod_ai_diag_pause_off = GetTime();
	}
	if ( on )
	{
		level.tod_upgrade_pause = true;
		if ( !( level flag::exists( "world_is_paused" ) ) )
			level flag::init( "world_is_paused" );
		level flag::set( "world_is_paused" );
	}

	players = GetPlayers();
	foreach ( p in players )
	{
		if ( !isdefined( p ) || !isplayer( p ) )
			continue;
		if ( on )
		{
			if ( !isalive( p ) || ( p laststand::player_is_in_laststand() ) )
				continue;
			p EnableInvulnerability();
			p.tod_pause_invuln = true;
		}
		else if ( IS_TRUE( p.tod_pause_invuln ) )
		{
			p.tod_pause_invuln = undefined;
			if ( !( p pause_invuln_held_elsewhere() ) )
				p DisableInvulnerability();
		}
	}

	team = ( isdefined( level.zombie_team ) ? level.zombie_team : "axis" );
	zombies = GetAITeamArray( team );
	foreach ( z in zombies )
	{
		if ( !isdefined( z ) || !isalive( z ) )
			continue;
		if ( on )
		{
			z.tod_frozen = true;
			z.ignoreall = true;
			z ASMSetAnimationRate( 0.05 );
			// Empty dev/dark deals can open and close in one frame. Latch the
			// write so the elite's 250 ms watcher cannot miss its restore.
			if ( isdefined( z.tod_elite_base_rate ) ) z.tod_elite_pause_pending = true;
			if ( IS_TRUE( level.tod_dev ) ) z.tod_ai_diag_pause_write = GetTime();
		}
		else
		{
			z.tod_frozen = undefined;
			z.ignoreall = false;
			// anim rate restored by _tod_zombie_speed's keep-alive sweep...
			// ...EXCEPT FOR A ZOMBIE MID-CLIMB-OUT (2026-09-04). That sweep
			// early-returns on `in_the_ground` (_tod_zombie_speed.gsc:313,
			// correctly — it must not fight a scripted animation), and
			// _tod_stray::eligible refuses the same field, so NOTHING restored
			// the 0.05 this function stamped on a riser that was mid-rise when
			// the pause began. The freeze half is symmetric and stays; only the
			// restore was missing, and the cost of missing it is severe out of
			// all proportion to the write: while `in_the_ground` holds, stock's
			// zombie_think is still blocked on waittill("risen")
			// (_zm_spawner.gsc:581), so `zombie_think_done` is never set, and
			// the ROOT of the behaviour tree runs `idlespawnbehavior` — a
			// looping idle@zombie gated on condition_script_negate
			// zombieisthinkdone (behavior/zm_zombie.ai_bt:117-137) that sits
			// ABOVE the playable-area branch carrying findfleshservice (:552).
			// The zombie therefore has NO enemy, NO goal and NO FindFlesh tick
			// — and hide_pop already Show()ed it half a second into the rise
			// (zombie_utility.gsc:1592-1607). That is a fully visible zombie
			// standing still and never targeting anyone: the reported bug,
			// verbatim. 1 is the neutral clip rate; the keep-alive sweep takes
			// the zombie back over the moment the climb-out completes.
			// ...but never over a slow effect the player paid for: Widow's Wine's
			// cocoon and Time Warp both own the rate, and every other anim-rate
			// writer in the tree checks this before touching it.
			if ( IS_TRUE( z.in_the_ground ) && !( z tod_zombie_speed::under_anim_slow() ) )
				z ASMSetAnimationRate( 1 );
		}
	}

	if ( !on )
	{
		if ( level flag::exists( "world_is_paused" ) )
			level flag::clear( "world_is_paused" );
		level.tod_upgrade_pause = false;
	}
}

// self = player. True while another lane owns this player's invulnerability,
// so the pause's release must not clear it: the zombie-blood window
// (_tod_powerups, tod_in_blood), the Black Market spin and the class terminal.
// (The finale's depart retired whole with the ending, 2026-10-05.)
// Each of those clears or never clears the
// flag on its own terms; the pause only ever undoes its own arm.
function pause_invuln_held_elsewhere()
{
	if ( IS_TRUE( self.tod_in_blood ) )
		return true;
	// the Item Shop spin (docs/188, session 9c): a round deal ending while this
	// player is mid-spin or in the spin's exit grace must not drop their protection
	if ( IS_TRUE( self.tod_spin_locked ) || IS_TRUE( self.tod_spin_grace ) )
		return true;
	// the crown's CLASS TERMINAL (2026-10-01): the same contract as the spin, for the same reason
	if ( IS_TRUE( self.tod_cls_term_locked ) || IS_TRUE( self.tod_cls_term_grace ) )
		return true;
	return false;
}

// ---------------------------------------------------------------------------
// DAMAGE + FIRE RATE — the actor damage chain. self = the zombie victim.
// Return -1 = untouched (lets later callbacks run); returning a value is the
// final damage (legitimate here — we ARE the modifier).
// ---------------------------------------------------------------------------

function upgrade_damage_cb( inflictor, attacker, damage, flags, meansofdeath, weapon, vpoint, vdir, sHitLoc, psOffsetTime, boneIndex, surfaceType )
{
	// Allies own their integrity callback. Partner shots bypass player weapons,
	// perks and on-hit procs, but still respect victim armor and world pauses.
	if ( IS_TRUE( self.tod_is_partner ) ) return -1;
	if ( isdefined( attacker ) && IS_TRUE( attacker.tod_is_partner ) )
	{
		if ( IS_TRUE( level.tod_upgrade_pause ) ) return 0;
		return damage;
	}
	// Event stamp: this chain handled the hit THIS frame (self = the damaged
	// actor). The Warrior's melee lane reads it (_tod_warrior_melee); the Rogue
	// Protector's aiOverrideDamage feed that it was first written for retired
	// with him, 2026-10-05.
	self.tod_actor_cb_ms = GetTime();

	// No free hits on the frozen horde while everyone picks upgrades — a
	// zero-risk damage window every round would be THE degenerate strategy.
	if ( IS_TRUE( level.tod_upgrade_pause ) )
		return 0;

	// The Double Tap machine credits its buyer, but its authored shots are
	// independent of the buyer's held weapon and upgrade procs. No remote
	// melee/Thor/chain effects or crosshair numbers.
	// (docs/208, map 1's v19.32; _tod_perk_anims::doubletap_shot sets the mark.
	// The power scale has already taken its tenth at the front door.)
	if ( IS_TRUE( self.tod_perk_machine_hit ) )
	{
		self.tod_perk_machine_hit = undefined;
		return int( Max( 1, damage ) );
	}

	// INSTA-KILL 3x window (user 2026-08-20): all players deal 3x while the
	// map's insta-kill is active (level.tod_dmg_mult; default 1) — applied to
	// the FINAL of every path so it lifts class, non-class, and knife alike.
	dmult = ( isdefined( level.tod_dmg_mult ) ? level.tod_dmg_mult : 1 );

	// A cleave splash re-enters this callback — consume the mark, pass through
	// untouched (the splash already carries the final damage). IMPACT ROUNDS
	// splash borrows the same mark for the same reason. (The armored sprinter's
	// carve-out below retired with the sprinter, 2026-10-05.)
	//
	// HISTORY — SPRINTER ARMOR (v14.20). "Pass through untouched" was written
	// against the ATTACKER's multipliers — the splash already carries them, so
	// re-applying them would square the bonus. The armor is the VICTIM's, it
	// was never in the splash figure, and skipping it here handed both splash
	// lanes a silent full bypass: a slasher's CLEAVE dealt 3x what the swing
	// that caused it dealt, which is the sharpest edge of the "melee is too
	// strong against it" the user reported. Returning a value instead of -1 is
	// the normal contract (FIRST-NON-(-1)-WINS = this is the final damage).
	// Floor at 1, same as the main lane. push_dmg_num is deliberately still
	// skipped — a splash has never drawn its own crosshair number — so the
	// RICOCHET is the whole feedback that the hit was deflected.
	if ( IS_TRUE( self.tod_cleave_hit ) )
	{
		self.tod_cleave_hit = undefined;
		return -1;
	}
	// A WISP TEA hit re-enters here WEARING THE OWNER'S NAME — consume the
	// mark and pass through untouched (v14.24; user report: "the wisp will
	// call down lightning ... some bug with thors thunder where it randomly
	// triggers").
	//
	// THE BUG, and it was a live one the moment Wisp Tea shipped: the perk's
	// companion damages with `DoDamage( dmg, wisp.origin, PLAYER, PLAYER,
	// "none", "MOD_MELEE", ... )`. Attacker is the OWNER and the means is
	// MELEE — so every wisp tick arrived at this chain indistinguishable from
	// the player swinging a knife, at a zombie the player may be nowhere near.
	// Everything melee-gated then fired off it:
	//   * THOR'S THUNDER — a Slasher with the Stormbreaker called lightning
	//     down on whatever the wisp touched, which is exactly the "randomly
	//     triggers" the user saw: real strikes, correct code, wrong cause.
	//   * CLEAVE — wisp ticks rolled splash hits of their own.
	//   * the melee CLASS-TIER uniques (DRAW CUT et al) and melee_boss_mult.
	//   * push_dmg_num — crosshair damage numbers for hits the player never
	//     made.
	// It also broke the perk's OWN balance: the wisp's damage is a fraction of
	// the victim's max health (WISP_TEA_*_SEGMENTS = hits-to-kill), so letting
	// the upgrade multipliers scale it made the tier ceilings — including
	// "a wisp can never solo a Panzer" — silently untrue.
	//
	// A companion's damage is not the player's swing. It passes through raw,
	// which makes the .gsh's hits-to-kill numbers mean exactly what they say.
	// The mark rides the VICTIM for one hit, same idiom as tod_cleave_hit
	// above; _zm_perk_wisp_tea sets it immediately before the DoDamage and
	// clears it immediately after, so it can never swallow a real swing.
	//
	// NOT ARMORED AGAINST THE SPRINTER, unlike the cleave/impact mark above,
	// and this is a decision rather than an oversight (v14.20). The wisp deals
	// a FRACTION OF THE VICTIM'S MAX HEALTH — WISP_TEA_*_SEGMENTS is literally
	// hits-to-kill — so it already pays the sprinter's x20 health in full and
	// kills it in exactly the tier's advertised number of ticks. Layering the
	// 1/3 armor on top would make it 3x that, i.e. the sprinter would become
	// the most wisp-proof thing in the map, ahead of the Panzer, off a knob
	// that was never meant to touch percentage damage. Flagged to the user with
	// the v14.20 change; if they want the wisp armored too it is one call to
	// sprinter_armor_frac() here, and the .gsh hits-to-kill numbers stop being
	// true for this one enemy.
	if ( IS_TRUE( self.tod_wisp_hit ) )
	{
		self.tod_wisp_hit = undefined;
		return -1;
	}

	if ( !isdefined( attacker ) || !IsPlayer( attacker ) || !isdefined( weapon ) )
		return -1;

	// HEADSHOT — one owner, headshot_kind(). Two things changed here 2026-08-24,
	// both from "only some guns can hit panzer for headshots":
	//   NECK now counts. LOC_NORM stamps locNeck 3.0 on every generated gun, so
	//   the ENGINE had already paid a full 3x crit on a neck hit before this
	//   callback ran — but the old test omitted it, so the HEADSHOT domain paid
	//   nothing and push_dmg_num drew a plain number on an already-tripled hit,
	//   on EVERY enemy in the map. _tod_bosses::rp_damage_feed's b_head has
	//   always included "neck", so the two lanes openly disagreed.
	//   THE PANZER VISOR now counts. A visor hit arrives as `torso_upper`, so
	//   this callback used to call it a body shot: no crit, no domain, no luck —
	//   while _tod_bosses' wrap was separately treating it as a head hit for
	//   damage. The two halves of our own code disagreed about the same bullet.
	// The wrap supplies the 3.0 the engine skipped, so a visor hit and a true
	// head hit now come out to exactly the same number.
	headshot = ( headshot_kind( self, sHitLoc, vpoint ) != "none" );

	// INSTA-KILL = A REAL ONE-HIT ON THE TRASH HORDE (user 2026-08-30: "make
	// instakill a one hit on normal zombies but keep the 3x for everything
	// else"). While the window is live (dmult > 1), any player hit on a
	// non-boss actor is simply lethal; the boss triad — Panzer, Rogue
	// Protector, Reaver, AND the hellhounds (they carry all three flags,
	// _tod_hellhounds.gsc:345-347) — falls through to the normal math below,
	// where dmult still multiplies the final: that IS the kept 3x. Armored
	// sprinters carry no boss flag, so they one-hit too — "insta-kill treat
	// them as the zombies they are" was accepted at their design
	// (_tod_sprinter.gsc:41), and returning the lethal value directly is what
	// lets the hit bypass their 1/4 bullet armor further down.
	// Placed AFTER the cleave-consume (a splash must pass through untouched,
	// mark cleared) and AFTER the player-attacker guard (a boss clubbing a
	// zombie is not an insta-kill). Skipping the rest of the chain skips
	// on-hit procs (SUPPRESSING FIRE et al.) for the window — irrelevant, the
	// victim is dead. The crosshair number is pushed here because the normal
	// push site is never reached on this path (the xmas_fixed_shots_cb
	// pattern).
	if ( dmult > 1 &&
	     !IS_TRUE( self.is_boss ) && !IS_TRUE( self.acc_is_boss ) && !IS_TRUE( self.acc_is_mini_boss ) )
	{
		kill = ( ( isdefined( self.health ) && self.health > 0 ) ? self.health : 32767 ) + 666;
		// the crosshair shows what the zombie actually lost (its health), not the +666 kill margin
		attacker tod_upgrade_ui::push_dmg_num( kill - 666, headshot );
		return kill;
	}

	// GUN BALANCE PASS (user 2026-08-20: "pistol was doing like 6 damage a
	// shot while m60 was doing 100+ — apply an evenly spread balance"):
	// per-gun multipliers on the RAW damage, script-side ONLY — the Skye GDTs
	// are install-side and SHARED with map 1, never edit them. GDT bases:
	// ak74u 180 / krig 195 / m60 290(no falloff) / stock pistol ~25 w/ heavy
	// falloff. Applied to every weapon before the class multipliers.
	balance = gun_balance_mult( weapon );
	damage = damage * balance;

	// THE DRAW (2026-09-25): a bow arrow x1.0 at a tap up to x3.0 at full draw,
	// linear (_tod_archer_bow). Captured for the guard at the bottom.
	// 2026-10-05: x QUICK DRAW's odd-level term (x1.13) on every Archer arrow AND crossbow bolt
	// (_tod_archer_bow quickdraw_mult), so a crossbow hit can read != 1.0 here too.
	draw_mult = tod_archer_bow::charge_mult( attacker, inflictor, weapon, meansofdeath );
	damage = damage * draw_mult;

	// THE WARRIOR'S LEFT HOOK (2026-09-26, user: "a right left hook ... the left hook
	// will be a little bit weaker"): the gauntlet's left-hand swing lands x0.75
	// (_tod_warrior_melee hook_mult, a level pointer - no import). 1.0 for every
	// other hit. Captured for the guard at the bottom.
	hook_mult = 1.0;
	if ( isdefined( level.tod_wm_hit_mult_fn ) )
		hook_mult = [[ level.tod_wm_hit_mult_fn ]]( attacker, weapon, meansofdeath );
	damage = damage * hook_mult;

	// THE CLASS BUILD CARDS (2026-09-27, _tod_class_cards through a level pointer -
	// no import): HUNTER'S MARK, POINT BLANK, EXECUTIONER. After the draw, so a
	// full-draw arrow can mark its target. Captured for the guard at the bottom.
	cc_mult = 1.0;
	if ( isdefined( level.tod_cc_damage_fn ) )
		cc_mult = [[ level.tod_cc_damage_fn ]]( attacker, self, weapon, meansofdeath, draw_mult );
	damage = damage * cc_mult;

	// PACK-A-PUNCH TIERS (v17.33) — what a pack is worth (pap_tier_mult). The
	// retired spire's PACK II / III re-packs are gone, so a gun reads 1.0 (its
	// first pack rides the _up twin's GDT). See
	// the define block at the top of _tod_classes.gsc for why this is a
	// multiplier and not a weapon asset (the twin ledger is at 229 of 229).
	//
	// APPLIED HERE, BESIDE gun_balance_mult, AND NOT IN THE `mult` SUM BELOW.
	// The sum is where DAMAGE, HEADSHOT, GIANT SLAYER and the dark adds live;
	// dropping a +50% into it would make the tier worth progressively less the
	// more DAMAGE levels a player owns (against a maxed +100% it would land as
	// +25% real), which is not what a 50,000-point pack should feel like.
	// Multiplying the raw damage scales the base hit AND every one of those
	// domains together, exactly the way the stock pack's own +25% does.
	//
	// Returns 1.0 at tier 0 and tier 1, so this line is inert for the whole
	// tower and costs one array lookup per hit there.
	//
	// CAPTURED, because the "nothing modified -> return -1" guard at the bottom
	// has to test it. Without that test a PACK II/III gun with no
	// attacker-side term (dmg_lvl 0, no Insta-Kill, ordinary victim) hits the
	// guard, `final` is discarded and stock applies the UNAMPLIFIED damage --
	// the pack silently doing nothing for exactly the players who have not
	// drawn DAMAGE yet. Same shape as the v16.3 sprinter_armor_frac miss below.
	pap_mult = tod_classes::pap_tier_mult( attacker, weapon );
	damage = damage * pap_mult;


	// ONE DAMAGE LANE FOR EVERY WEAPON (user 2026-08-23: "there is a damage
	// upgrade. Your secondary should get that upgrade as well" -> "lets widen as
	// much as we can without twins"). The non-class-primary branch that used to
	// sit here applied DAMAGE and nothing else; it is GONE. A sidearm — and a
	// powerup gun — now runs the SAME lane as the class gun, which hands it
	// DAMAGE, HEADSHOT, GIANT SLAYER, the script-side uniques (MOMENTUM,
	// OVERDRIVE) and unique_on_hit (SUPPRESSING FIRE, IMPACT ROUNDS). Every one
	// of those is arithmetic over levels the player already owns, so opening the
	// lane costs zero weapon assets — which is the whole reason it can be done.
	//
	// WHAT STAYS CLASS-GUN-ONLY, and why neither is an oversight:
	//   * the TWIN domains (FIRE RATE, HANDLING, RECOIL, MAG SIZE, PENETRATION,
	//     KNIFE SPEED) are weapon-VARIANT ladders. gen_tod_twins.js builds those
	//     forms for the class guns alone, and building them for four more
	//     sidearms multiplies registrations straight into the ~230-twin boot
	//     ceiling. The NO-TWIN rule forbids it, not this function.
	//   * CLEAVE and THOR gate on MELEE further down, which no sidearm deals.
	//     The mechanic is its own gate; it needs no weapon test.
	//
	// One consequence to know rather than discover: the gun_keys comment below
	// ("a level > 0 here means the right gun is in hand") was true only while
	// this branch existed. gun_keys gates what you can ROLL, never what fires —
	// so a heavy holding OVERDRIVE now gets it on the pistol too. Intended.

	// THE CORE WEAPON CARD (2026-09-27, user: "remove the damage card altogether
	// ... each class will have its own ... core primary ... upgrade"). DAMAGE is
	// retired; each class's core card adds its per-level step ON THAT CLASS'S OWN
	// PRIMARY ONLY (core_weapon_bonus). dmg_lvl keeps its name for the guard below.
	core_bonus = core_weapon_bonus( attacker, weapon );
	dmg_lvl = ( core_bonus > 0 ? 1 : 0 );
	hs_lvl = get_level( attacker, "headshot" );

	mult = 1.0 + core_bonus;
	// headshot_bonus owns the rate AND the dark step (2026-09-08) — the dark add
	// that used to sit in the block below has moved inside it, so this one call
	// is the whole HEADSHOT contribution on this lane. hs_lvl stays because the
	// silent-return fast path at the end of this function still tests it.
	if ( headshot )
		mult += headshot_bonus( attacker );
	// DARK UPGRADES (v17.10) — flat adds into the SAME additive sum, so they are
	// worth exactly what their table row says and cannot double-apply. There is
	// no upper clamp anywhere on the path from here to `swing`, so the whole step
	// lands. A dark bit implies the domain is MAXED, so these stack on top of
	// dmg_lvl 10 / hs_lvl 10, never instead of them.
	// (DARK DAMAGE retired 2026-09-27 with the DAMAGE card.)
	// (DARK HEADSHOT moved into headshot_bonus() on 2026-09-08, so the boss lane
	// gets it too — it never did while this was an inline add here.)
	// (ECHO ROUNDS removed 2026-08-23 — see the note at its old add_domain.)

	// CLASS TIER UNIQUES (docs/25 §9): OVERDRIVE / MEAT GRINDER (sustained
	// fire) and DRAW CUT (a swing out of a sprint). gun_keys already bind each
	// domain to its gun, so a level > 0 here means the right gun is in hand.
	is_melee = ( isdefined( meansofdeath ) && IsSubStr( meansofdeath, "MELEE" ) );
	umult = unique_damage_mult( attacker, is_melee );
	mult += umult;

	// GIANT SLAYER (domain 35, v9.45; 12%/Lv since v16.50): +12%/Lv, and ONLY against the boss/elite
	// triad. This is the lane that fires for the Panzer (his actor_damage_func
	// wrap runs after us and re-scales by hit-location ratios, so a bonus
	// applied here survives it) and for the Reaver. The Rogue Protector's own
	// aiOverrideDamage fallback carries the same call — see rp_damage_feed.
	bmult = boss_damage_bonus( attacker, self );
	mult += bmult;

	// GUNSLINGER (v16.99) — the slasher's sidearm-vs-boss ladder joins the sum
	// HERE, beside GIANT SLAYER, instead of multiplying the final further down.
	// See gunslinger_bonus for why it moved. The 2.25 class baseline is still
	// applied multiplicatively below; only the per-level term is additive.
	gmult = gunslinger_bonus( attacker, self, weapon );
	mult += gmult;

	// MELEE vs BOSSES (user 2026-08-24): halved, and applied to the FINAL so it
	// scales the base hit, DAMAGE, GIANT SLAYER, DRAW CUT and the insta-kill
	// window together rather than fighting them one at a time. Non-melee hits
	// and non-boss victims both return 1.0, so this line is inert everywhere
	// else. The crosshair number below is pushed AFTER it, so what the player
	// reads is what the boss actually took.
	//
	// TWO VALUES ON PURPOSE. `swing` is the swing BEFORE the boss scale;
	// `final` is what THIS victim takes. CLEAVE is handed `swing`, because each
	// splash victim applies its OWN melee_boss_mult in cleave_splash — pass
	// `final` and a boss standing next to another boss would be scaled twice
	// (0.25x). Every other consumer wants `final`.
	swing = int( damage * mult * dmult + 0.5 );   // round, not truncate (power scale 2026-09-25)
	final = int( swing * melee_boss_mult( attacker, self, is_melee ) + 0.5 );

	// THE SLASHER'S SIDEARM vs BOSSES AND ELITES (v16, 2026-09-01): x2.25.
	// Applied to `final` for exactly the reasons melee_boss_mult is — it scales
	// the base hit and every damage domain together, and the crosshair number is
	// pushed after it, so what the player reads is what the boss took.
	//
	// NOT applied to `swing`, deliberately, and the distinction is the same one
	// the CLEAVE note above is about: `swing` is what splash consumers are
	// handed so each victim can apply its OWN boss scale. A sidearm deals no
	// splash today, so passing either would work — but putting it on `final`
	// keeps the rule uniform ("swing is pre-boss-scale, final is what THIS
	// victim takes") instead of creating an exception the next reader has to
	// notice.
	//
	// The two boss multipliers cannot both fire: melee_boss_mult needs a MELEE
	// hit and this needs the class SECONDARY, which is never melee.
	final = int( final * slasher_sidearm_boss_mult( attacker, self, weapon ) + 0.5 );

	// SPRINTER ARMOR (v13.7, user 2026-08-29: "bullets do 1/4 damage on them
	// ... you can hear bullets bouncing off" — spec'd for the Reaver rework,
	// re-scoped the same hour to the NEW Armored Sprinter, lap-30 door; the
	// Fury Reaver is back at lap 20 and never reads these fields). It lives
	// HERE and not in a second register_actor_damage_callback because stock's
	// dispatch (_zm.gsc:5822) is FIRST-NON-(-1)-WINS — this callback returns a
	// final for every player hit, so anything registered after it never runs.
	// Same integration point as melee_boss_mult above, same reason: applied
	// BEFORE push_dmg_num so the crosshair number is what the sprinter took.
	// Fields, not an import (_tod_sprinter sets tod_is_sprinter and publishes
	// level.tod_sprinter_dmg_frac) — the KB cycle rule.
	//
	// (THE ARMORED SPRINTER's armor, its RICOCHET and its RED number retired whole
	// with the sprinter, 2026-10-05; the red "reduced" flag has no writer now.)
	attacker tod_upgrade_ui::push_dmg_num( final, headshot );

	// SUPPRESSING FIRE + IMPACT ROUNDS ride bullet hits only (never the cleave
	// re-entry above, never melee).
	//
	// `swing`, NOT `final` — the same two-value rule cleave_splash follows, and
	// for the same reason (v14.29 follow-up, fixing a defect this change itself
	// introduced). IMPACT ROUNDS builds its splash as a FRACTION of what it is
	// handed, and each splash victim then applies its OWN sprinter armor in the
	// pass-through at the top of this callback. Handing it `final` — which is
	// already armored when the DIRECT victim is a sprinter — made a
	// sprinter→sprinter burst pay the 1/3 twice: ~11% of the raw hit instead of
	// the intended 33%. Exactly the double-scale the "TWO VALUES ON PURPOSE"
	// note above warns about for melee_boss_mult; cleave was written against
	// that trap on purpose and this lane was not.
	// Free of side effects by construction: this call is gated on `!is_melee`,
	// and melee_boss_mult returns 1.0 for non-melee, so `swing` and the
	// pre-armor `final` are the SAME NUMBER — nothing changes except that the
	// armor is no longer applied twice. SUPPRESSING FIRE never reads the value
	// at all (it is a level-scaled slow), so IMPACT ROUNDS is the only consumer.
	if ( !is_melee )
		self unique_on_hit( attacker, swing );

	// PIERCING (Archer, 2026-09-27 CLASS PASS 3 (user)): a direct arrow / bolt hit carries on into the
	// zombies behind this one (_tod_class_cards::pierce, a level pointer). `swing` is
	// this hit's damage before the victim's armor; the pierced hits ride the
	// tod_cleave_hit pass-through, so they never pierce again or re-apply cards.
	if ( !is_melee && isdefined( level.tod_cc_pierce_fn ) && isdefined( attacker ) && isplayer( attacker )
	  && isdefined( attacker.tod_class ) && attacker.tod_class == "assault" )
		self thread [[ level.tod_cc_pierce_fn ]]( attacker, weapon, swing, vdir, meansofdeath );

	// MELEE vs BOSSES must be part of this test (user 2026-08-24). The halving
	// is the ONE multiplier here that fires on a player holding zero upgrades —
	// a fresh slasher swinging at a Panzer has dmult 1, balance 1.0 and every
	// level at 0, so without this clause the guard below would return -1 and the
	// chain would keep the UNHALVED stock damage. The nerf would then apply only
	// to players who already had upgrades, which is exactly backwards.
	//
	// v16.3 (repo review 2026-09-01): the two VICTIM-side terms applied above —
	// sprinter_armor_frac (v13.7) and slasher_sidearm_boss_mult (v16) — were
	// missing from this test. A player with no attacker-side term active
	// (dmg_lvl 0, no headshot level, no unique, no bounty: every fresh player,
	// and every player right after a promotion until v15) hit the -1 here and
	// stock applied the UNARMORED damage — while the crosshair had already
	// pushed the red one-third number. Same shape as the melee clause, same fix.
	// v18.59 (2026-09-09): the script-paid PACK II/III was the next term to be
	// applied above and left out of this test — the same omission as v16.3.
	// It is captured at its application site (pap_mult); read the comment
	// there for what it silently discarded.
	if ( dmult == 1 && balance == 1.0 && dmg_lvl == 0 && ( hs_lvl == 0 || !headshot ) && umult == 0 && bmult == 0
	  && pap_mult == 1.0
	  && draw_mult == 1.0
	  && hook_mult == 1.0
	  && cc_mult == 1.0
	  && melee_boss_mult( attacker, self, is_melee ) == 1.0
	  && slasher_sidearm_boss_mult( attacker, self, weapon ) == 1.0
	  && gunslinger_bonus( attacker, self, weapon ) == 0.0 )
		return -1;   // nothing modified — stay silent in the chain
	return final;
}

// ---------------------------------------------------------------------------
// CLASS TIER UNIQUES — the effects (docs/25 §9). The fire-streak inputs (_tod_uniques.gsc) and the
// OVERDRIVE / DRAW CUT lanes they fed left with the Map 1 purge (2026-10-04).
// ---------------------------------------------------------------------------

// DEAD as of 2026-08-23 — MEAT GRINDER was removed and the Death Machine now
// carries OVERDRIVE. grinder_pct/grinder_cap and TOD_GRINDER_PER are kept,
// unreferenced, purely as the record of its tuning (+2/3/4% per 5 rounds,
// capped +50/75/100%) in case it is ever wanted back. Nothing calls them.
function grinder_pct( lvl )     // per stack — DEAD, see above
{
	if ( lvl >= 3 ) return 0.04;
	if ( lvl == 2 ) return 0.03;
	return 0.02;
}

function grinder_cap( lvl )     // total cap
{
	if ( lvl >= 3 ) return 1.0;
	if ( lvl == 2 ) return 0.75;
	return 0.5;
}

function unique_damage_mult( attacker, is_melee )
{
	add = 0;
	if ( is_melee )
		return add;   // (DRAW CUT, the only melee unique, retired 2026-09-26; its lane left with the Map 1 purge)
	// (MOMENTUM removed 2026-08-30, v14.11; RUN AND GUN's damage half, which took
	// its slot, retired whole 2026-10-05 with the parked card.)
	// ADRENALINE's damage half (v17.67): while the 3s burst is live, bullets
	// also hit +3%/tier harder (+25% dark) — the SAME adren_bonus() value the
	// move-speed sum reads, so speed and damage can never drift apart. Not gated
	// on a trigger-hold streak: the burst is a kill-streak proc.
	if ( isplayer( attacker ) )
		add += attacker adren_bonus();
	return add;
}

// self = the zombie that took a BULLET hit from its killer-to-be. Bosses are
// exempt from both (the map's boss-damage doctrine + no boss slows).
// `swing` is the PRE-victim-multiplier damage. IMPACT ROUNDS was its only
// reader and was retired 2026-08-31, so THE PARAMETER IS NOW UNUSED — kept
// rather than dropped because the arg is free, the call site's two-value note
// still governs CLEAVE next door, and changing an arity in the damage chain to
// delete an unused name is a worse trade than an explained spare parameter.
// (History, still load-bearing for cleave: it used to be `final`, which
// double-armored sprinter→sprinter bursts — v14.29.)
function unique_on_hit( attacker, swing )
{
	if ( !isdefined( self ) || !isalive( self ) )
		return;
	if ( IS_TRUE( self.is_boss ) || IS_TRUE( self.acc_is_boss ) || IS_TRUE( self.acc_is_mini_boss ) )
		return;
	// SUPPRESSING FIRE (HK21): a timed playback-rate slow (_tod_zombie_speed owns the rate)
	lvl = get_level( attacker, "suppress" );
	if ( lvl > 0 )
		self tod_zombie_speed::slow( 1.0 - ( TOD_SUPPRESS_BASE + TOD_SUPPRESS_PER_LV * ( lvl - 1 ) ), TOD_SUPPRESS_MS );
	// (IMPACT ROUNDS' burst was the second consumer here and was REMOVED
	// 2026-08-31 — see the retirement note at its old add_domain.)
}

// (IMPACT ROUNDS' impact_splash() was removed 2026-08-31 with the domain —
// see the retirement note at its old add_domain call.)

// The tower's per-gun balance table (see the balance-pass comment above).
// Tune HERE — one number per gun family, applies to base + PaP + twins
// (substring match covers all variant names).
function gun_balance_mult( weapon )
{
	if ( !isdefined( weapon ) || !isdefined( weapon.name ) )
		return 1.0;
	n = weapon.name;
	// CLASS GUNS ARE AT STOCK GDT DAMAGE (user 2026-08-20: "restore back to
	// original GDT — we will tweak from there. Only thing I want to keep is
	// speed with gun"). The v6 balance pass (m60 x0.85 / ak74u x1.1 / krig
	// x1.05) is retired along with the ak74u and m60 themselves; the per-class
	// MOVE SPEED is untouched and lives in class_speed_base(), keyed on the
	// class rather than the gun, so it carried across the roster swap.
	// The starter PISTOL keeps its multiplier — it is not a class gun, and
	// without it the opening rounds are unplayable (stock base ~25 damage).
	// Starter pistol (the MR6) — the HEAVY class's sidearm since secondaries
	// went per-class. ×9.6 (user 2026-08-23: "buff the original pistol that LMG
	// class use by 20% damage"; was ×8.0 from 2026-08-20). Its stock GDT is not
	// in the tools tree, so this multiplier is the only damage number anyone
	// can actually verify about it.
	// PAP FORM NERFED 40% (user 2026-08-23: "mr6 needs a nerf... 40% damage
	// nerf. Only the pap version"): 9.6 × 0.6 = 5.76. The BASE pistol is
	// untouched — it is what carries the opening rounds. This is a split of one
	// family, so it MUST be tested before the generic "pistol_standard"
	// substring: "pistol_standard_upgraded" matches both, and the base branch
	// would swallow the PaP form if it came first.
	// SECONDARY SLOT -25% (user 2026-08-24: "the current secondaries need an all
	// around 25% nerf ... make sure they are all pretty weak compared to the
	// primary slot"). 9.6 x 0.75 = 7.2 base, 5.76 x 0.75 = 4.32 PaP. The PaP
	// form's own 40% nerf is UNTOUCHED and still folded in here — 4.32 is
	// 9.6 x 0.6 x 0.75, so the two nerfs compose rather than replacing each
	// other. THE OPENING ROUNDS RIDE ON THE BASE NUMBER: this is the gun every
	// player holds before the first door, so if round 1-3 starts feeling like
	// chip damage, 7.2 is the digit to move, not the twins' knob.
	// PaP FORM NERFED A FURTHER 50% (user 2026-08-28: "The MR6 pap needs a 50%
	// damage nerf"): 4.32 x 0.5 = 2.16. THE NERFS COMPOSE, they do not replace —
	// 2.16 is 9.6 x 0.6 (the 2026-08-23 40%) x 0.75 (the secondary-slot 25%)
	// x 0.5 (this one). Read the chain before changing any single factor: each
	// one was asked for separately and the product is the shipped number.
	// The BASE pistol stays at 7.2, untouched again — it is the gun every player
	// holds before the first door and it is what carries rounds 1-3. Only the
	// PaP form was named, both times.
	// PaP FORM NERFED A FURTHER 50% (user 2026-09-01: "Death and Taxes need a
	// 50% damage nerf. They are just too good"): 2.16 x 0.5 = 1.08. "Death &
	// Taxes" is the PaP MR6's in-game name (ZMWEAPON_PISTOL_STANDARD_UPGRADED in
	// stock's zombie.str), so the ask names THIS branch and not the base.
	//
	// ⚠️ A CLAIM THAT LIVED HERE FOR THREE DAYS WAS FALSE, AND THE USER'S PLAY
	// REPORT IS WHAT DISPROVED IT. This comment used to read: "NOTE THIS IS NOW
	// BELOW THE BASE: a Pack-a-Punched MR6 does LESS damage than an un-packed one
	// (2.16 vs 7.2)." docs/armory.html repeated it as fact.
	//
	// It does not follow. These multipliers scale each form's OWN GDT damage, and
	// the two forms do not share one — a stock PaP weapon ships a substantially
	// higher base damage than its un-packed form. So comparing 2.16 against 7.2
	// only tells you the PaP is weaker IF the two GDT numbers are equal, which
	// was never checked and is almost certainly untrue. The comment silently
	// assumed it.
	//
	// AND IT CANNOT BE CHECKED FROM HERE. pistol_standard is stock; its GDT is
	// not in this mod-tools install (verified 2026-09-01 — no .gdt in the tools
	// root defines it). So the multiplier really is the only damage number
	// anyone can verify about this gun, which is exactly why an unstated
	// assumption about the other factor survived unchallenged.
	//
	// The user has now played it twice and called it "too good" both times. A
	// play report beats an unverifiable inference: the ratio between the forms
	// is whatever the stock GDTs make it, and the only honest statement is that
	// 1.08 is HALF of what was there yesterday. Do not re-derive "the PaP is
	// weaker than the base" from these two numbers again.
	if ( IsSubStr( n, "pistol_standard" ) )
	{
		if ( IsSubStr( n, "_upgraded" ) ) return 1.08;
		return 7.2;
	}

	return 1.0;
}

// ---------------------------------------------------------------------------
// BOUNTY — +5%/Lv money per kill with the class gun (TOD_UPG_BOUNTY_PER_LVL;
// this comment said 3% until 2026-08-26 — stale since the 2026-08-20 buff).
// self = the dead zombie,
// attacker = the killer. Stock kill money varies by hit type, so the bonus is
// computed off the matching nominal value (melee 120 / headshot 100 / bullet
// 60) and BANKED: zm_score::add_to_player_score rounds UP to multiples of 10
// (KB trap), so fractional bonuses accumulate on the player and pay out in
// exact 10s — over time the payout is exactly 3%/Lv, never inflated.
// ---------------------------------------------------------------------------

// self = scorer, via stock player_add_points' registered-event invocation.
// Mirror its death branch's stats/bonus work; stock still owns point scaling,
// rounding, score splitting and the actual award after this returns.
// Stock team points are always zero. zombie_team is unused here (dogs omit it at
// their call site); the parameter stays because it is stock's event signature.
function zombie_death_score( event, mod, hit_location, zombie_team, damage_weapon )
{
	player_points = zm_score::get_zombie_death_player_points();
	points = self zm_score::player_add_points_kill_bonus( mod, hit_location, damage_weapon, player_points );
	if ( level.zombie_vars[self.team]["zombie_powerup_insta_kill_on"] == 1 && mod == "MOD_UNKNOWN" )
		points *= 2;
	player_points += points;
	if ( mod == "MOD_GRENADE" || mod == "MOD_GRENADE_SPLASH" )
	{
		self zm_stats::increment_client_stat( "grenade_kills" );
		self zm_stats::increment_player_stat( "grenade_kills" );
	}
	// THE HAVENS (docs/202, user 2026-10-02: "Kills inside a zone are at 25% money"):
	// a scorer standing inside a safe-zone field is paid a quarter, banked to exact
	// tens; stock's Double Points still applies on top. Guarded pointer: the haven
	// module owns the rule and is never imported here.
	if ( isdefined( level.tod_haven_kill_pay_fn ) )
		player_points = [[ level.tod_haven_kill_pay_fn ]]( self, player_points );
	return player_points;
}

// The kill's NOMINAL money, shared by BOUNTY's payout and the score-popup
// preview below so they can never drift apart. `attacker` is unused today; the
// third parameter stays because both callers pass it.
function bounty_kill_value( mod, hitloc, attacker = undefined )
{
	// 130 -> 120 (user 2026-08-26: "knife kills go down from 130 to 120"). This
	// number is NOT the source of truth — the engine pays
	// get_zombie_death_player_points() 50 + zombie_vars["zombie_score_bonus_melee"],
	// and that bonus is set to 70 in zm_tod2_cybercity.gsc::main(). This mirror
	// exists so BOUNTY's percentage and the HUD's popup preview are computed off
	// the same number the player is actually paid. THE TWO MOVE TOGETHER OR THE
	// HUD LIES: 50 + the zombie_var must always equal what is returned here.
	if ( isdefined( mod ) && IsSubStr( mod, "MELEE" ) )
		return 120;
	if ( isdefined( hitloc ) && ( hitloc == "head" || hitloc == "helmet" ) )
		return 100;
	return 60;
}

// PUBLIC, via the level.tod_bounty_preview_fn pointer — what BOUNTY is about to
// pay for THIS kill. READ-ONLY: it does not bank, does not award, and changes
// no state, so calling it can never affect the economy.
//
// WHY A PREVIEW AND NOT THE REAL PAYOUT (user 2026-08-23: "the points display
// in center of screen should take into account if you have a money upgrade. So
// im getting 110 on headshot but it shows +100. It should show +110"):
// the Aetherium kit draws that popup from a zm::register_zombie_damage_override
// callback, which fires on the KILLING BLOW — while BOUNTY pays from a
// zm_spawner::register_zombie_death_event callback, which fires AFTER. So at
// popup time the bonus does not exist yet and no same-frame stash can reach
// backwards for it. Rather than move the payout across callbacks (which would
// migrate live economy state to a different event and risk double-paying), the
// popup asks what is coming. The prediction is exact: the bank is deterministic
// given its current value plus this kill, and on_class_gun_kill runs the
// identical arithmetic off the same helper milliseconds later.
//
// Returns 0 for anything that will not pay — wrong weapon, no levels, or a
// bank that has not yet reached the 10-point granularity that
// add_to_player_score rounds to.
function bounty_preview( attacker, weapon, mod, hitloc )
{
	if ( !isdefined( attacker ) || !IsPlayer( attacker ) )
		return 0;
	// ANY weapon, matching on_class_gun_kill since BOUNTY was widened — these
	// two run the same arithmetic and the header above says outright that the
	// HUD lies if they ever disagree.
	if ( !isdefined( weapon ) )
		return 0;

	lvl = get_level( attacker, "bounty" );
	if ( lvl <= 0 )
		return 0;

	bank = ( ( isdefined( attacker.tod_bounty_bank ) ) ? attacker.tod_bounty_bank : 0 );
	rate = bounty_rate( lvl );
	if ( has_dark( attacker, "bounty" ) )
		rate += TOD_DARK_BOUNTY_ADD;   // DARK -- LOCKSTEP with the real bank below; a preview on a different rate is a visible lie
	bank += bounty_kill_value( mod, hitloc, attacker ) * rate * haven_pay( attacker );   // THE HAVENS: LOCKSTEP with the bank above
	if ( bank < 10 )
		return 0;
	return int( bank / 10 ) * 10;
}

// PUBLIC via level.tod_bounty_mult_fn (the tod_bounty_preview_fn pattern —
// consumers must not import this module). BOUNTY as a FLAT MULTIPLIER for a
// lump-sum payout: 1.0 + 5%/Lv, the same TOD_UPG_BOUNTY_PER_LVL rate the
// per-kill bank pays — so the card's "+5% money per kill / Lv" promise holds
// for lump rewards too. First consumer: the killer-only elite 500
// (_tod_bosses::grant_elite_reward, v14.5). Weapon-agnostic on purpose,
// matching the widened domain (see bounty_preview above).
// BOUNTY's rate at a level (2026-09-28, user: 9 levels, logarithmic, +100% at Lv9):
// TOD_UPG_BOUNTY_MAX x card_curve = +30 / 48 / 60 / 70 / 78 / 85 / 90 / 95 / 100%. LOCKSTEP tod_upgrade.lua DETAIL[3].
function bounty_rate( lvl )
{
	return TOD_UPG_BOUNTY_MAX * card_curve( lvl );
}

function bounty_mult( player )
{
	if ( !isdefined( player ) || !IsPlayer( player ) )
		return 1;
	b = bounty_rate( get_level( player, "bounty" ) );
	if ( has_dark( player, "bounty" ) )
		b += TOD_DARK_BOUNTY_ADD;   // DARK: +50% -> +100% money
	return 1.0 + b;
}

// THE HAVENS (docs/202): the fraction of kill money this player is paid right now.
// _tod_haven sets tod_haven_pay while they stand inside a live safe-zone field
// (0.25) and clears it on the way out. A field read, so BOUNTY's bank and its popup
// preview can never use two different numbers.
function haven_pay( player )
{
	if ( isdefined( player ) && isdefined( player.tod_haven_pay ) )
		return player.tod_haven_pay;
	return 1.0;
}

// Every class-gun kill funnels through here: BOUNTY (shared), SCAVENGER
// (assault), LEECH (slasher). self = the dead zombie, attacker = the killer.
// z = the dead zombie: killed by an explosion (the kit's C4 / Cluster hurt()
// raises MOD_GRENADE_SPLASH with the kit weapon).
function is_explosive_kill( z )
{
	m = z.damagemod;
	if ( isdefined( m ) && ( m == "MOD_GRENADE" || m == "MOD_GRENADE_SPLASH" || m == "MOD_EXPLOSIVE" || m == "MOD_PROJECTILE_SPLASH" ) )
		return true;
	w = z.damageweapon;
	return ( isdefined( w ) && isdefined( w.name ) && ( w.name == "tod_c4" || w.name == "tod_cluster" ) );
}

// NUKE-CAUGHT KILLS PAY (map 1's v19.58, ported 2026-10-04, docs/208; its user: "getting
// kills during a nuke says you get money on the display but doesnt actually give you money").
// Stock's nuke stamps every zombie `.nuked` the moment it goes off and then kills them one at
// a time over ~0.1-0.7 s each; a zombie a PLAYER finishes inside that window hits stock's
// "nuked zombies don't give points" branch (_zm_spawner zombie_death_animscript) and pays
// nothing, while the kill popup (_zm_aetherium_hud) has already shown the full kill value.
// This pays exactly what stock's zombie_death_points would have: the same player_add_points
// call, whose registered "death" event is zombie_death_score above (so double points, the
// point scalar and THE HAVENS' quarter, docs/202, all apply as in the popup), guarded by
// stock's own deathpoints_already_given latch. It skips zombie_death_points itself on purpose:
// that also rolls a powerup drop, and the nuked branch has already rolled one. Kills made BY
// the nuke carry no attacker and still pay nothing (stock's flat 400 per player covers them).
// BOUNTY already pays on these kills (it rides this same death hook).
// Dev log `[TOD_NUKE_PAY]` (tod_dev).
function nuke_kill_pay( attacker )   // self = the dead zombie
{
	if ( !isdefined( self.nuked ) )
		return;
	if ( IS_TRUE( self.deathpoints_already_given ) )
		return;
	if ( !IS_EQUAL( self.team, level.zombie_team ) )
		return;
	if ( !( attacker zm_spawner::player_can_score_from_zombies() ) )
		return;
	self.deathpoints_already_given = true;
	weapon = attacker.currentweapon;
	if ( isdefined( self.damageweapon ) )
		weapon = self.damageweapon;
	before = attacker.score;
	attacker zm_score::player_add_points( "death", self.damagemod, self.damagelocation, undefined, self._race_team, weapon );
	if ( IS_TRUE( level.tod_dev ) )
	{
		mod = "none";
		if ( isdefined( self.damagemod ) )
			mod = self.damagemod;
		loc = "none";
		if ( isdefined( self.damagelocation ) )
			loc = self.damagelocation;
		line = "[TOD_NUKE_PAY] ms=" + GetTime() + " ent=" + attacker GetEntityNumber() + " mod=" + mod + " loc=" + loc + " score " + before + " -> " + attacker.score;
		/# PrintLn( line ); #/
	}
}

// RIOT SHIELD KILLS PAY (map 1's v19.58, ported 2026-10-04). Both of the Breacher's shields
// (zod_riotshield Lv1..8, log_riotshield_zm Lv9, _tod_riotshield) are registered EQUIPMENT,
// and stock's zombie_death_points returns before paying for any equipment kill (_zm_spawner:
// `if ( zm_equipment::is_equipment( zombie.damageweapon ) ) return;`), while the kill popup
// showed the value. This pays exactly what stock pays a weapon kill (player_add_points
// "death": double points, the scalar, the havens' quarter), once (tod_equip_paid). A nuked
// victim is nuke_kill_pay's. (Map 1 also skips a victim stamped tod_popup_points, its
// Trailblazer popup lane; this tower has no such stamp - its trail kills carry no weapon.)
function equipment_kill_pay( attacker )   // self = the dead zombie
{
	if ( IS_TRUE( self.tod_equip_paid ) || isdefined( self.nuked ) )
		return;
	if ( !isdefined( self.damageweapon ) || !zm_equipment::is_equipment( self.damageweapon ) )
		return;
	if ( !IS_EQUAL( self.team, level.zombie_team ) )
		return;
	if ( !( attacker zm_spawner::player_can_score_from_zombies() ) )
		return;
	self.tod_equip_paid = true;
	attacker zm_score::player_add_points( "death", self.damagemod, self.damagelocation, undefined, self._race_team, self.damageweapon );
}

function on_class_gun_kill( attacker )
{
	if ( !isdefined( attacker ) || !IsPlayer( attacker ) )
		return;
	self nuke_kill_pay( attacker );
	self equipment_kill_pay( attacker );
	if ( !isdefined( self.damageweapon ) )
		return;
	// WIDENED TO EVERY WEAPON (user 2026-08-23: "lets widen as much as we can
	// without twins"). This hook used to return early unless the kill came from
	// the class primary, which silently switched OFF four upgrades the moment
	// you drew your sidearm. BOUNTY, SCAVENGER and ADRENALINE (and KILL RELOAD,
	// until its 2026-09-01 retirement) are
	// all weapon-agnostic script — SCAVENGER even refunds onto self.damageweapon,
	// so it was already written to pay whichever gun made the kill.
	// LEECH is the one hold-back and it keeps this flag: "blade kills heal you"
	// is the SLASHER's risk model — healing must cost you the range the blade
	// costs. is_primary rather than a MELEE test on purpose, so the gate cannot
	// regress if the Stormbreaker ever reports a non-MELEE damagemod.
	// (CHAIN LUNGE needs no flag — it already gates on MELEE at the bottom.)
	is_primary = tod_classes::is_class_primary( attacker, self.damageweapon );

	// THE CLASS BUILD CARDS (2026-09-27): POINT BLANK shells, EXECUTIONER heals,
	// BATTLE RHYTHM (_tod_class_cards::on_kill; self = this zombie).
	if ( isdefined( level.tod_cc_kill_fn ) )
		self [[ level.tod_cc_kill_fn ]]( attacker );

	// --- BOUNTY: % of the kill's nominal money, banked, paid in exact 10s ---
	lvl = get_level( attacker, "bounty" );
	if ( lvl > 0 )
	{
		// Base value via the SHARED helper — the score popup previews the same
		// number, and if these two ever disagreed the HUD would lie.
		kill_value = bounty_kill_value( self.damagemod, self.damagelocation, attacker );

		if ( !isdefined( attacker.tod_bounty_bank ) )
			attacker.tod_bounty_bank = 0;
		rate = bounty_rate( lvl );
		if ( has_dark( attacker, "bounty" ) )
			rate += TOD_DARK_BOUNTY_ADD;   // DARK: +50% more money per kill on top
		attacker.tod_bounty_bank += kill_value * rate * haven_pay( attacker );   // THE HAVENS (docs/202): a quarter from inside a field

		if ( attacker.tod_bounty_bank >= 10 )
		{
			pay = int( attacker.tod_bounty_bank / 10 ) * 10;
			attacker.tod_bounty_bank -= pay;
			attacker zm_score::add_to_player_score( pay );
		}
	}

	// --- LEECH (slasher): the blade feeds you ------------------------------
	// LEECH DOES NOT STACK (user 2026-09-05: "Leach goes to 25HP but doesnt
	// stack. This is a change to leech overall." and "it can stack healing if it
	// kills multiple zombies like thors thunder. That cant happen"): ONE heal per
	// swing. Every CLEAVE-splash and THOR-shock victim carries tod_no_leech (set
	// at the splash/strike, never cleared -- tod_cleave_hit is consumed by the
	// damage callback before death, so it cannot serve) and pays no heal.
	lvl = get_level( attacker, "leech" );
	if ( is_primary && lvl > 0 && !IS_TRUE( self.tod_no_leech ) && IsAlive( attacker ) && !( attacker laststand::player_is_in_laststand() ) )
	{
		heal = leech_hp_for_level( lvl );
		if ( has_dark( attacker, "leech" ) )
			heal = TOD_DARK_LEECH_HP;   // DARK: a FLAT 25 HP per blade kill (replaces, never adds)
		attacker trickle_heal( heal );
	}

	// --- ADRENALINE (MP7 unique): a MULTI-KILL fires a 3s speed burst ------
	// v16. Count kills in a rolling window; when the count reaches
	// TOD_ADREN_MK_NEED and the cooldown has expired, fire one fixed burst.
	//
	// ⚠️ NO WEAPON GATE, AND THAT IS INHERITED RATHER THAN CHOSEN. This block
	// has never tested is_primary (the 2026-08-23 widening deliberately made
	// BOUNTY / SCAVENGER / ADRENALINE / KILL RELOAD weapon-agnostic; KILL RELOAD
	// itself retired 2026-09-01), and
	// gun_keys gates what you can ROLL, never what FIRES. So the proc counts
	// sidearm, grenade and even Panzer kills. Left as-is because for a
	// skirmisher those are most of the multi-kill lanes the class has — but it
	// is now load-bearing for the trigger rather than incidental to a per-kill
	// stack, so it is written down instead of being rediscovered.
	// 2026-09-27 class pass 2 (user: "Adrenaline you can keep but only applies to
	// explosive kills"): only a C4 / Cluster / grenade / explosion kill counts.
	lvl = class_live_level( attacker, "adrenaline" );   // the Breacher's; asleep in another class (2026-10-01)
	if ( lvl > 0 && is_explosive_kill( self ) )
	{
		now = GetTime();
		// Rolling window: a gap longer than the window restarts the count.
		// Same shape as _tod_uniques::fire_streak_watch's gap test.
		if ( !isdefined( attacker.tod_adren_mk_ms ) || ( now - attacker.tod_adren_mk_ms ) > TOD_ADREN_MK_WINDOW_MS )
			attacker.tod_adren_mk_n = 0;
		if ( !isdefined( attacker.tod_adren_mk_n ) )
			attacker.tod_adren_mk_n = 0;
		attacker.tod_adren_mk_n++;
		attacker.tod_adren_mk_ms = now;

		// The !isdefined arm is what removes the need for any spawn-time init —
		// thor_next_ms's trick. Stamp the cooldown BEFORE firing.
		ready = ( !isdefined( attacker.tod_adren_next_ms ) || now >= attacker.tod_adren_next_ms );
		if ( attacker.tod_adren_mk_n >= TOD_ADREN_MK_NEED && ready )
		{
			attacker.tod_adren_next_ms = now + adren_cooldown_ms( lvl );
			attacker.tod_adren_mk_n = 0;               // consume the streak
			attacker.tod_adren_until = now + TOD_ADREN_MS;
			attacker apply_move_speed();               // instant onset

			// THE HEAL (v17.85) — DOUBLE the speed/damage percent, once, now.
			// It reads adren_bonus(), so it MUST come after tod_adren_until is
			// stamped above: outside a live burst that function returns 0 and the
			// heal would be a silent no-op. Percentage OF MAX HEALTH, so it follows
			// Juggernog and VITALITY without naming either.
			//
			// trickle_heal is the map's one heal lane (LEECH uses it too): it clamps
			// to maxhealth, never lowers, and only ever RAISES health -- which is
			// what keeps RECOVERY's health-drop poll from reading a heal as damage.
			//
			// THE LASTSTAND GUARD IS LEECH'S, AND IT IS NOT OPTIONAL. A downed
			// player can still kill with a pistol and so can still fire this proc;
			// self.health in last stand belongs to the down system, and writing it
			// from here would be a partial self-revive nobody designed. The speed and
			// damage halves are left ungated exactly as they have always been -- they
			// write no health.
			if ( IsAlive( attacker ) && !( attacker laststand::player_is_in_laststand() ) )
			{
				heal_pct = attacker adren_bonus();
				if ( heal_pct > 0 && isdefined( attacker.maxhealth ) )
					attacker trickle_heal( attacker.maxhealth * heal_pct * TOD_ADREN_HEAL_MULT );
			}
			// EXACT 3s EXPIRY. Without this the burst ends only when the 1s body
			// tick next runs, so a nominal 3s proc really lasts 3-4s — a 33%
			// overrun, and far more visible against a 6s cooldown than the old
			// 4s window ever was. One-shot thread, self-cancelling if a new proc
			// lands first.
			attacker thread adren_expire();
			// SOUND HOOK — WIRED SINCE v16 (2026-09-01). The pointer is set in
			// register_domains beside level.tod_lmgs_fx_fn; adren_fx() PlayLocalSounds
			// TOD_ADREN_SFX (3 synth heartbeats, 1.42s, 2d/player-only). Called through
			// the pointer so the cue and the speed land on the SAME frame.
			//
			// This comment said "DELIBERATELY UNWIRED TODAY" for a day after the wiring
			// landed, and that cost real debugging time: the user reported the cue
			// inaudible, and a comment at the call site saying the hook does not exist
			// points the next reader at the one part that was fine. The cause was
			// ATTENUATION, not wiring — see the TOD_ADREN_SFX #define.
			if ( isdefined( level.tod_adren_fx_fn ) )
				attacker [[ level.tod_adren_fx_fn ]]();
		}
	}

	// --- KILL RELOAD (assault): REMOVED 2026-09-01 with the domain -----------
	// (user: "Lets remove it. No one likes it"). The proc lived here: every Nth
	// kill (55/40/30 by level) topped the magazine back up FROM RESERVE, never
	// creating ammo. Its two 2026-08-23 reworks (v9.41 reserve-fed, v9.43
	// frequency ladder) and the arithmetic for why 10/7/5 was still broken are
	// in the CHANGELOG under those versions.

	// (The CHAIN LUNGE hook that used to close this function was removed
	// 2026-08-24 with the domain — see the note at its old add_domain.)
}

// ---------------------------------------------------------------------------
// MAG SIZE — REMOVED as a virtual pool 2026-08-20 (user: "I don't want
// bottomless magsize — this should be a twin and directly impact the gun's
// mag size"). It is now REAL twin variants: the krig r{R}m{M} matrix in
// gen_tod_twins.js scales clipSize/startAmmo/maxAmmo (+50/+100/+150%), and
// twin_suffix/reconcile_twin swap the asset in place. The todMagBonus
// clientfield stays registered (budget stability) but is never set — the
// MAG +N HUD chip simply never shows.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// PERSONAL UPGRADE STATION (user 2026-08-20)
// ---------------------------------------------------------------------------
// A buyable terminal at the base (Chaos PaP mesh against the core's south
// face): pay 2000 +250 per PURCHASE — the escalation is PER PLAYER, not
// team — to roll a solo upgrade menu on the spot.
//
// WHETHER THE WORLD FREEZES NOW DEPENDS ON PARTY SIZE (v16.84, 2026-09-03 —
// the full argument is on station_freeze_wanted, below). CO-OP is unchanged
// and is what the rest of this comment describes: the world does NOT pause,
// the buyer is NOT frozen (user 2026-08-20), full movement + weapons while
// the cards are up, the horde keeps coming (that is the risk) and the 15s
// auto-lock timer still runs. SOLO freezes the world and the buyer exactly
// like a round event does — one player has no teammate to absorb that risk —
// with the FINALE as the single carve-out, since the closing song is a clock
// no freeze can stop. If a SCHEDULED
// upgrade round starts mid-pick, the round event OVERRIDES: the takeover
// notify (fired inside run_upgrade_event) kills the solo menu synchronously,
// the round event runs normally (the buyer participates like everyone else),
// then the SAME solo cards re-present with a fresh timer. Cards deferred
// across a round event re-clamp vs CURRENT levels at apply time — the event
// may have advanced the same domain, and a stale cur must never LOWER a
// level; if both cards die maxed, the purchase refunds and the price steps
// back one notch.
//
// PER-STATION USE CAP (user 2026-08-21: "each player can only use a specific
// upgrade station 3 times; after that they need to go up and use the next
// one — to push players up the tower"). Every terminal gets an id at spawn
// (base 0, breathers 1-4, crown 5) and each player carries a per-id use
// count; a depleted terminal refuses that player (hint says so) while
// staying live for everyone else. The PRICE ladder is untouched — it keeps
// counting across stations — so the cap changes WHERE you buy, not what
// you pay. A refunded buy (both cards dead) gives the use back.
// Per-PLAYER, per-STATION buy cap. 5 (user 2026-08-23: "lets make that increase
// by 2"; was 3). Six terminals — base 0, breathers 1-4, crown 5 — so a full
// climb now offers 30 station buys per player instead of 18. Still capped per
// terminal on purpose: the station is a reason to keep climbing, not a farm you
// can park at. NOTE this cap has only actually been enforceable since ship state
// went in (v9.22) — station_depleted() returns false outright while
// level.tod_dev is on, so every dev build had unlimited uses.
#define TOD_STATION_USES_PER  5

// THE CROWN ALTAR IS CAPPED AT 3 (user 2026-09-04: "max alter use on the
// crown room should be 3"). It was UNLIMITED from 2026-08-29 ("The heavenly
// alter in the crown room shouldnt have a limit") — but that call was made
// while the altar still had the price LADDER binding it economically, and the
// ladder went FLAT 3000 with the triggerstring-250 crash fix, leaving the one
// vendor at the top of the map uncapped AND flat-priced. Three, not the
// terminals' five: the crown altar is the LAST vendor of the run and the only
// one nothing further up can push you off, so it buys a finish, not a farm.
#define TOD_STATION_USES_CROWN  3
#define TOD_STATION_CROWN_ID    5

// THE CROWN ALTAR FIX (v16.27, 2026-09-02) — THE TRIGGER ORIGIN FLOATS 32u OFF
// THE FLOOR. The crown altar had never shown a buy prompt in any build (user,
// 2026-08-30: "never had the buy prompt and still doesnt"), through two
// "fixes" that never cleared it (the v14.1 slab cut and the manager
// reordering above). The static audits all read SCRIPT; the answer was in the
// .map: station_trig_org() = (-624, 8308, 19392) lies INSIDE the hall's
// 'crown ring inlay W' brush — x[-632..-584] y[8024..9192] z[19392..19393],
// a 1u glowing floor decal that has ringed the hall since the v9 crown, the
// same release that placed this station. This map has paid for exactly that
// twice before: a solid brush on a trigger_radius_use ORIGIN kills the buy
// (the extraction obelisk and the hall crate's clip column, both recorded in
// _tod_finale::spawn_props). The BASE station's origin sits on the bare
// ground slab's top face with nothing above it, which is why it always
// worked — and the point query that found this (a 60-line node script over
// the .map's axis-aligned brushes) also found that the v16.7 lounge inlay
// SPOKES run under every breather station trigger (spoke s, 40u from the
// machine — the trigger is 56u out) and every breather PaP trigger (spoke
// e), so the four lounge stations were on course to die the same way in the
// first build anyone bought at them after v16.7. Every other script vendor in
// the map already floats its origin (ammo crates +40, doors +40, teleporters
// +32 — "raised 32u so the cursor lands" — uplink/exfil +30); the stations
// were the last at floor level. 32 is the teleporter's
// proven number. The player's bounding box, not their origin, is what the
// cylinder [z, z+100] tests (the +40 crate is the standing proof), so a
// crouched buyer still reaches it. The Pack-a-Punch stubs lift too
// (zm_cwpap, TOD_PAP_TRIG_LIFT).
// TEST AT SPAWN FIRST: the base station is the live canary for "a lifted
// station trigger still prompts"; the crown is the proof of the diagnosis.
#define TOD_STATION_TRIG_LIFT  32

function station_spawn()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	level.tod_station_count = 0;

	// BASE station — backed on the core south face, facing spawn. yaw ~0 =
	// front toward -y is the LIVE-VERIFIED vending convention (same as the
	// perk pads; 270 faced WEST).
	station_place( ( 0, -320, 0 ), ( 0, -360, 0 ), 359.999 );

	// ONE PER BREATHER (user 2026-08-21: "add a card update station on each
	// platform"). v13: the terminal owns the lounge's NORTH wall — the
	// entrance side — facing south into the room, so it is the first fixture
	// an arriving player walks past (the W wall it used to back now belongs
	// to the Pack-a-Punch). Anchors are GENERATED (_tod_breather_data.gsc);
	// the generator asserts every lounge trigger pair clears by both radii
	// + 64. Yaw convention on this map (live-verified): 0/359.999 = front
	// toward -y, 180 = +y, 90 = +x, 270 = -x; the trigger sits 56u in front
	// of the machine face, same as the base station below.
	zs = tod_breather_data::breather_zs();
	foreach ( z in zs )
		station_place( tod_breather_data::station_org( z ), tod_breather_data::station_trig( z ), tod_breather_data::station_yaw() );

	// THE CROWN (v9): one terminal inside the citadel, on the west wall south
	// of the pilaster — the last chance to spend before the uplink. Anchors
	// are GENERATED (parity-mirrored with the rest of the crown).
	// TOD II (docs/160): the hall is the SPAWN. Retired for one build on
	// 2026-09-23 ("clean out the crown so there's no ammo crates or anything")
	// and BACK the next day (user 2026-09-24: "Pap will be here and the alter
	// will be here as well. We will change the alter model later but we can
	// reuse for now") — same west-shrine anchors, same 3-use cap (id 5), the
	// heavenly-altar mesh as the placeholder until the new model lands.
	// RETIRED AGAIN 2026-09-25 (user: "in the crown, there is a altar. I want
	// that removed. And in that spot, I want the item shop"). The west shrine is
	// the hall's ITEM SHOP now (gen_tower_map.js CROWN_SHOPS[0]); the base
	// altar and the four breathers keep theirs. station_org() is still emitted.
	// (The 2026-08-29 diagnosis instruments — floating anchor marker,
	// "stations placed" bold print, per-second trig-state heartbeat — were
	// REMOVED for the v14.1 publish. If the crown altar needs diagnosing
	// again, the recipe: bold-print level.tod_station_count here; thread a
	// spinning chaos_pack_a_punch mesh 160u above station 5's trig_org; and
	// in station_triggers_manager bold-print "trig=UP/none d=N" once a
	// second for any player above z=19000. Ships-dormant diagnostics that
	// STAY: the manager's spawn-fail retry print, the use-loop press/deny
	// narration, the manager's station-5 trigger-up print.)
}

// One terminal: the model plus its own use trigger. Every station charges the
// same FLAT 3000 (station_cost, 2026-08-30 — the escalating per-player ladder
// is gone), so building more of them never makes upgrades cheaper — only
// closer. The per-station use cap is what still pushes players UP the tower.
function station_place( model_org, trig_org, yaw )
{
	// THE TRIGGER MANAGER LAUNCHES FIRST — BEFORE ANY OTHER SPAWN IN THIS
	// FUNCTION (2026-08-29, the crown altar's second no-trigger report, made
	// AFTER the entity-relief build). The manager is the only thing the
	// altar's USABILITY depends on, yet it used to launch LAST — below one
	// model spawn and three clip spawns, none of them guarded. Any of those
	// four Spawn() calls returning undefined killed this thread on the very
	// next line's method call, and the manager then never started: a station
	// with a VISIBLE MESH and NO TRIGGER, forever, with nothing to self-heal
	// it (the guard added earlier today lives INSIDE the manager and cannot
	// help a manager that never ran). That is the crown altar's exact
	// signature — the last station placed, standing at the entity-pressure
	// peak, model present, untriggerable. Launched first, the trigger's
	// existence now depends on nothing but the manager's own guarded,
	// 1s-retrying spawn loop; the mesh and clips below are cosmetics and
	// collision, and a failure there costs looks, not function.
	level thread station_triggers_manager( trig_org, level.tod_station_count );   // base 0, breathers 1-4, crown 5
	level.tod_station_count++;

	m = Spawn( "script_model", model_org );
	if ( !isdefined( m ) )
	{
		// Pool pressure ate the mesh. The trigger manager above is already
		// running and unaffected — the station works, it just has no prop.
		if ( IS_TRUE( level.tod_dev ) )
			tod_quiet_print( "station " + ( level.tod_station_count - 1 ) + ": MODEL SPAWN FAILED" );
		return;
	}
	m.angles = ( 0, yaw, 0 );
	m SetModel( "tod_heavenly_altar" );

	// THE HEAVENLY AURA (user 2026-08-29: "a awwwwwww heanly aura sounds on loop
	// always so when you get close you hear it ... very subtle but adds
	// atmosphere"). One looping 3D emitter per altar, played ON THE MODEL rather
	// than a spawned script_origin: the model already lives for the whole game at
	// exactly the right spot, and a loop that dies with its machine is the
	// behaviour we want anyway. Placed HERE, in the shared placer, so all six
	// altars — base + four breathers + crown — get it by construction, and any
	// altar added later inherits it without a second edit.
	//
	// THE ALIAS IS WHERE THE TUNING LIVES, not this line: DistMin 64 (the altar's
	// own trigger radius, so full level exactly where the buy prompt appears)
	// falling to nothing by 320, at volume 68. Widening the audible ring or
	// changing the level is a one-row CSV edit and a -GscOnly.
	//
	// LimitCount is set to 8 ON THE ROW, deliberately overriding the UIN_MOD
	// template's default of 2 — six of these loop simultaneously for the whole
	// game, and at the default the emitters would steal each other's voices
	// (LimitType oldest) and some altars would fall silent.
	m PlayLoopSound( "tod_altar_aura" );

	// COLLISION (user 2026-08-23: "the Heavenly Altar doesnt have a clip. In all
	// locations its walk through"). A script_model is a VISUAL ONLY — the xmodel
	// carries no collision the player can stand against, which is why every
	// stock vendor spawns a SECOND entity to be its solid. This is stock’s own
	// recipe, copied field for field from the two places that use it:
	//   _zm_pack_a_punch.gsc:113-118  (the PaP — the same machine shape as ours)
	//   _zm_perks.gsc:1551-1555       (every perk machine)
	// both spawn a script_model at the vendor’s origin+angles, SetModel
	// "zm_collision_perks1", tag it script_noteworthy "clip" and DisconnectPaths.
	// The model needs no #precache here: it is already in the fastfile because
	// stock spawns one of these for each of our eight perk machines (we never set
	// level._no_vending_machine_auto_collision, and _tod_perk_scatter is built
	// around those clips existing).
	// DisconnectPaths is MANDATORY, not decoration — the navmesh ignores entity
	// collision entirely (KB: "Navmesh ignores ALL entity collision"), so without
	// it zombies path INTO the altar footprint and grind on a prop they cannot
	// walk through. Stock disconnects on the same line for the same reason.
	// Safe to solidify at spawn: station_spawn runs at init, long before a player
	// can be standing in the footprint (the crush-safety rule that governs door
	// slabs applies to things that solidify DURING play).
	// THE FLARE (user 2026-08-24: "please double check the clips of the heavenly
	// alter ... The top flares out and I dont think we took that to acconut").
	// MEASURED, not guessed: chaos_pack_a_punch.xmodel_bin is an LZ4-wrapped
	// binary xmodel; decompressed, its 957,902 vertex records binned by height
	// give this profile (scale 1, so model units ARE game units) —
	//     z   0..24   x +-44   the plinth
	//     z  36..84   x +-52   <<< THE FLARE, and it sits at PLAYER CHEST HEIGHT
	//     z  96..120  x +-36   the crown taper
	// i.e. 104 units across at its widest (z=60) against 89 at the base, and
	// 127 tall overall. zm_collision_perks1 is sized for a stock VENDING
	// MACHINE, so the 8-16 units of overhang per side at chest height had NO
	// collision on it at all — which is precisely the "talking through parts of
	// it" that was reported.
	//
	// THREE clips instead of one, spaced along the machine's WIDE axis. The
	// mesh's local +X is its width (extent 104) and local Y its depth (53), and
	// an entity with angles (0,yaw,0) maps local +X onto AnglesToForward — so
	// the row lies ACROSS the machine's face whichever way a station is turned.
	// Do not "simplify" this to world-axis offsets: the six stations do not
	// share a yaw.
	//
	// +-32 IS DELIBERATELY ROBUST RATHER THAN EXACT. zm_collision_perks1 is a
	// packed stock asset with no source in the mod-tools raw tree, so its true
	// width cannot be measured here the way the altar's was; whatever its half
	// width W is, the union spans W+64 and therefore covers the measured 104 for
	// any W >= 20. Over-covering slightly is safe — every station backs a wall,
	// a core face or a terrace edge — while under-covering is the bug being
	// fixed. It also uses ONLY the asset already proven resident (see above), so
	// this needs no new zone line and no precache.
	fwd = AnglesToForward( m.angles );
	clip_offs = array( -32, 0, 32 );
	clips = [];
	for ( ci = 0; ci < clip_offs.size; ci++ )
	{
		c = Spawn( "script_model", model_org + VectorScale( fwd, clip_offs[ ci ] ), 1 );
		if ( !isdefined( c ) )           // pool-guard: a lost clip is a cosmetic
			continue;                    // hole, never a dead thread (see header)
		c.angles = m.angles;             // same yaw as the mesh, so the boxes line up
		c SetModel( "zm_collision_perks1" );
		c.script_noteworthy = "clip";
		c DisconnectPaths();
		clips[ clips.size ] = c;
	}
	if ( clips.size == 0 )
		return;                          // no clips spawned; trigger manager unaffected
	m.tod_clip = clips[ 0 ];             // a surviving clip — handle kept because
	                                     // anything that later hides a station must
	                                     // NotSolid + ConnectPaths it (Hide() !=
	                                     // NotSolid — the QR invisible wall bug,
	                                     // docs/KB and qr_clip_watch)
	m.tod_clips = clips;                 // ...and the full set, which is what such a
	                                     // teardown actually has to walk now

	// PER-PLAYER TRIGGERS (2026-08-27). The altar used to run ONE shared trigger
	// whose hint showed the NEAREST player's price — and when two players in
	// range owed different amounts it fell back to a priceless generic
	// ("HEAVENLY GIFT ALTAR - per player"), because a single global hint showing
	// one player's number would lie to the other. The user read that generic as
	// a bug ("It just says something like heavenly alter. No price or anything"),
	// and they were right that it is a worse experience, honest or not.
	//
	// THE FIX IS MAP 1'S MEGA-BOTTLES PATTERN (_acc_mega_bottles.gsc:687 /
	// _acc_perk_scatter.gsc:651): N overlapping triggers at the same origin,
	// each SetInvisibleToPlayer-hidden from everyone except its OWNER. An
	// invisible trigger shows no hint and takes no use from the hidden player,
	// so every player sees exactly one prompt — theirs — carrying THEIR price,
	// THEIR spent state, THEIR maxed state. The mixed-party generic is dead
	// because the situation it papered over no longer exists.
	//
	// The altar is the only per-player-priced buyable in the map (doors and
	// extraction are party-wide prices), which is why only this vendor needs it.
	// (The trigger manager itself launches at the TOP of this function — see
	// the header comment: its start must not sit downstream of any Spawn.)
}

// One manager per station: keeps one live trigger per connected player, spawns
// for late joiners, prunes when an owner disconnects. 6 stations x 4 players =
// 24 triggers at most — nothing by entity-count standards.
function station_triggers_manager( trig_org, station_id )
{
	level endon( "end_game" );

	trigs = [];
	for ( ;; )
	{
		// prune triggers whose owner left (entity refs go undefined on disconnect)
		alive = [];
		for ( i = 0; i < trigs.size; i++ )
		{
			t = trigs[ i ];
			if ( !isdefined( t ) )
				continue;
			if ( !isdefined( t.tod_owner ) )
			{
				t Delete();
				continue;
			}
			alive[ alive.size ] = t;
		}
		trigs = alive;

		players = GetPlayers();
		foreach ( p in players )
		{
			if ( !isdefined( p ) )
				continue;
			have = false;
			for ( i = 0; i < trigs.size; i++ )
			{
				if ( isdefined( trigs[ i ].tod_owner ) && trigs[ i ].tod_owner == p )
					have = true;
			}
			if ( have )
				continue;
			t = spawn( "trigger_radius_use", trig_org + ( 0, 0, TOD_STATION_TRIG_LIFT ), 0, 64, 100 );   // lifted: see the define (the crown altar fix)
			// ENTITY POOL GUARD (the 2026-08-29 crown-altar failure: G_Spawn
			// returned undefined at init pressure and the unguarded method call
			// below KILLED this manager thread — that altar then never got a
			// trigger for the whole game). Skip and retry on the next 1s pass:
			// the pool frees as temp ents die, and the manager self-heals.
			if ( !isdefined( t ) )
			{
				// LOUD in dev (2026-08-29 second report): a silent skip here
				// is indistinguishable from a healthy station to the tester.
				if ( IS_TRUE( level.tod_dev ) )
					tod_quiet_print( "altar " + station_id + ": TRIG SPAWN FAILED (pool) - retrying" );
				continue;
			}
			t TriggerIgnoreTeam();      // REQUIRED for a script-spawned use-trigger
			t SetCursorHint( "HINT_NOICON" );
			t.tod_station_id = station_id;
			t.tod_owner = p;
			// DEV: prove the crown altar's trigger EXISTS and where (the
			// 2026-08-29 "cant trigger it" diagnosis lane — no spawn print +
			// no press print = station_place never ran; spawn print but no
			// press = the trigger is not receiving).
			if ( IS_TRUE( level.tod_dev ) && station_id == 5 )
				tod_quiet_print( "altar 5: trigger up at " + trig_org[ 0 ] + " " + trig_org[ 1 ] + " " + trig_org[ 2 ] );
			t thread station_visibility_loop();
			t thread station_hint_loop();
			t thread station_use_loop();
			trigs[ trigs.size ] = t;
		}
		wait 1;
	}
}

// self = trigger. RE-ASSERTED on a cadence rather than set once, exactly as map
// 1 does — visibility is per-(trigger,player) state the engine can lose on a
// roster change, and a new joiner must be hidden from every trigger that is not
// theirs before they can wander into range of six stations' worth of them.
function station_visibility_loop()
{
	level endon( "end_game" );

	for ( ;; )
	{
		if ( !isdefined( self.tod_owner ) )
			return;   // manager will Delete() us on its next pass
		players = GetPlayers();
		foreach ( p in players )
		{
			if ( !isdefined( p ) )
				continue;
			self SetInvisibleToPlayer( p, p != self.tod_owner );
		}
		wait 0.25;
	}
}

// FLAT 3000, ALWAYS (user 2026-08-30: "Make the alter 3000 then all the time").
//
// THE ESCALATING LADDER IS GONE, AND IT WAS THE LAST UNBOUNDED TRIGGERSTRING
// ACCUMULATOR IN THE MAP. History: +1000/buy -> +500 -> +250 (2026-08-23), as
// `2000 + 250 * n` with n a GLOBAL per-player lifetime buy count and no clamp.
// station_hint_loop:4050 interpolates this straight into the prompt, so EVERY
// purchase minted a hint string no previous purchase had produced — one
// permanent BG-cache 'triggerstring' slot each, cap 250 match-wide, never freed
// (see the shipped crash two players reported 2026-08-29/30). It was
// structurally identical to map 1's 2026-06-25 soul-box crash: a live counter
// baked into a hint and re-set per event. The crown altar's 5-use cap coming
// off on 2026-08-29 removed the last thing bounding it.
//
// A flat price makes the prompt ONE string for the whole match, so the map's
// entire hint budget is now STATIC — run length no longer moves it at all,
// which is what actually fixes the crash rather than deferring it. Unlimited
// buys are UNTOUCHED (station_depleted exempted the crown altar at the time —
// v17.37 caps it at 3, which is a use cap and still touches no hint string);
// only the escalation is gone. Economically this is a straight buff — buy #10 was 4,250
// and every buy past #5 now costs less than it did.
//
// player.tod_station_buys is still counted (and still decremented on a refunded
// buy at :4415); it simply no longer prices anything. Left in place rather than
// ripped out — it is harmless and something may want the tally later.
//
// IF THIS EVER GOES BACK TO A LADDER: the price must NOT go back into the hint
// literal. Bound it, bucket what is DISPLAYED, or move the number to
// IPrintLnBold / a clientfield. Memory: triggerstring-250-cap.
function station_cost( player )
{
	return 3000;
}

// How many times this player has bought at terminal `id` (per-player, per-station).
function station_uses( player, id )
{
	if ( !isdefined( player ) || !isdefined( player.tod_station_uses ) || !isdefined( player.tod_station_uses[ id ] ) )
		return 0;
	return player.tod_station_uses[ id ];
}

function station_depleted( player, id )
{
	// DEV: no per-station cap (user 2026-08-21) — test any terminal endlessly.
	// tod_dev_altar (2026-09-07) is the same lane on its own flag, because
	// tod_dev is a BUNDLE nobody wants armed just to buy a second upgrade —
	// same split, and same publish gate, as tod_dev_money and tod_dev_doors.
	// [tod v19.9] tod_dev_altar ONLY — the bundle half is gone, same reason as
	// the maxed loadout and the upgrade cadence. Arm tod_dev_altar for it.
	if ( IS_TRUE( level.tod_dev_altar ) )
		return false;
	// Station ids: base 0, breathers 1-4, crown 5 (station_place call order).
	// v17.37: the crown altar is CAPPED AT 3 — it ran unlimited from
	// 2026-08-29 to today. See TOD_STATION_USES_CROWN for why that reverted.
	return ( station_uses( player, id ) >= station_use_cap( id ) );
}

// -> how many buys THIS terminal allows one player. The crown altar's own
// number is the only exception, and it lives here so nothing has to test the
// id twice (the hint loop reads depletion through station_depleted).
function station_use_cap( id )
{
	if ( id == TOD_STATION_CROWN_ID )
		return TOD_STATION_USES_CROWN;
	return TOD_STATION_USES_PER;
}

// self = trigger. One shared trigger, PER-PLAYER price -> show the NEAREST
// player's cost (map 1's shared-trigger hint rule). Only re-set the hint
// when the shown cost actually changes — every distinct hint string costs a
// config string (bounded here: one per price tier ever displayed).
function station_hint_loop()
{
	level endon( "end_game" );

	// -999, NOT -1 (audit 2026-08-25). The state codes are >=0 price, -1 mixed
	// party, -2 spent, -3 all maxed — so a sentinel of -1 is a VALUE THE LOOP CAN
	// LEGITIMATELY COMPUTE. If the first evaluation of a given altar landed on
	// the mixed-party case, "cost == shown" was already true and the loop
	// skipped before ever calling SetHintString: that altar then had NO hint
	// at all, permanently, because shown never changes again either. Every other
	// sentinel-guarded loop in this map (uplink_hint_loop, teleport refresh —
	// and _tod_doors::door_price_watch, until it was deleted 2026-08-30 for the
	// 250-triggerstring cap) seeds outside its own domain; this one did not.
	// PER-PLAYER SINCE 2026-08-27: self.tod_owner is the ONE player who can see
	// this trigger (station_visibility_loop hides it from everyone else), so
	// the hint answers one question for one person — no nearest-player search,
	// and the mixed-party -1 state is GONE because two players can no longer be
	// reading the same hint. STATE CODES now: >=0 a live price, -2 this station
	// is spent for them, -3 they have nothing left to buy anywhere.
	//
	// -3 IS CHECKED AFTER -2 AND WINS (live report 2026-08-25: "When you hit
	// max it should tell you"): "nothing left to buy anywhere" outranks "you
	// have spent this particular one".
	shown = -999;
	for ( ;; )
	{
		wait 0.3;

		if ( !isdefined( self.tod_owner ) )
			return;   // owner disconnected; the manager will Delete() us

		cost = station_cost( self.tod_owner );
		if ( station_depleted( self.tod_owner, self.tod_station_id ) )
			cost = -2;
		if ( !player_has_upgrades_left( self.tod_owner ) )
			cost = -3;
		if ( cost == shown )
			continue;
		// Wording is deliberate (2026-08-21). It must NOT collide with the
		// Aetherium hint dispatcher's keyword routing (ZMCursorHintNew.lua):
		// "door"/"open" -> the door card, "pack"+"punch" or "upgrade"+"weapon"
		// -> the PaP card, "[cost:" WITH an icon -> the wall-buy card. We use
		// HINT_NOICON and never say "weapon", so this lands on the default
		// prompt — which now renders the live text (it used to show the
		// hardcoded placeholder "Hint text here").
		shown = cost;
		// THE HEAVENLY GIFT ALTAR (user 2026-08-23: "We can call it the heavnly
		// gift alter"), and a COPY BUG fixed with it.
		//
		// THE BUG: PromptDefault.lua strips the leading "Hold [{+activate}]"
		// before drawing, because it renders its own button glyph. The old line
		// "Hold [{+activate}] for an Upgrade Card [Cost: N]" therefore reached the
		// screen as the fragment **"for an Upgrade Card [Cost: 2000]"** — a
		// dangling preposition, which is the "copy bugs" the user reported.
		// So the visible text has to READ CORRECTLY WITH "Hold [btn]" REMOVED:
		// lead with the noun, never with "for"/"to"/"at".
		//
		// Two routing constraints this wording also has to satisfy
		// (ZMCursorHintNew.lua): isWallBuyHint needs BOTH "[cost:" AND an icon,
		// and the trigger is HINT_NOICON, so the price bracket is safe to keep.
		// isPerkHint needs "hold" AND "for" AND a perk-name word — dropping "for"
		// takes us further from that collision than the old wording was.
		if ( cost == -3 )
			self SetHintString( "^1ALL UPGRADES MAXED^7" );
		else if ( cost == -2 )
			self SetHintString( "^1ALTAR SPENT^7 - try another" );
		else
			// (The mixed-party "- per player" generic died with the shared
			// trigger, 2026-08-27 — this hint is visible to exactly one player,
			// so the price is always THEIRS.)
			// v14.58 — the shared prompt grammar, "Hold [btn] <TITLE> - <detail>
			// [Cost: N]" (PromptDefault.lua). The card splits on the FIRST
			// " - ", so the title band reads HEAVENLY GIFT ALTAR and the line
			// under it finally says what the 3000 points buy. Note the
			// paragraph above is now WRONG about one thing and kept only as
			// history: the claim that "[cost:" is safe because the wallbuy
			// router "needs [cost:] AND an icon" was FALSE — the icon guard
			// never fired and this altar drew the "Wall Weapon" card in game
			// (user 2026-08-31). The router no longer has a wallbuy route at
			// all, and "heavenly gift altar" is in its TOD_NOUNS list, so this
			// prompt is claimed by name before any keyword test runs. Keep the
			// noun if you reword this.
			self SetHintString( "Hold ^3[{+activate}]^7 ^5HEAVENLY GIFT ALTAR^7 - take an upgrade card ^2[Cost: " + cost + "]" );
	}
}

// self = trigger
function station_use_loop()
{
	level endon( "end_game" );

	for ( ;; )
	{
		self waittill( "trigger", player );

		// DEV DIAGNOSIS LANE (live report 2026-08-29: the crown altar "doesnt
		// even work. I cant trigger it" — none of the six guards below says
		// which one ate the press, so an armed run now narrates. Behind
		// tod_dev like every debug print on this map; ships silent.)
		if ( IS_TRUE( level.tod_dev ) )
			tod_quiet_print( "altar " + self.tod_station_id + ": press" );

		if ( !isdefined( player ) || !isplayer( player ) )
			continue;
		// PER-PLAYER TRIGGER (2026-08-27): only the owner may buy through this
		// one. SetInvisibleToPlayer should already stop anyone else using it,
		// but that is an engine behaviour this loop does not get to assume —
		// a charge landing on the wrong player's ladder would be a real bug.
		if ( !isdefined( self.tod_owner ) )
			return;   // owner disconnected; manager will Delete() us
		if ( player != self.tod_owner )
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny NOT-OWNER" );
			continue;
		}
		if ( !IS_TRUE( level.tod_class_select_done ) )    // never during the draft
			continue;
		// MID-PICK NOW OUTRANKS THE PAUSE DENY (v16.84). A SOLO pick freezes the
		// world, so this player's own two cards make level.tod_upgrade_pause
		// true — and in the old order the branch below would answer a second
		// press with the round-event deny sound: the wrong reason, and a noise
		// in the ear of someone who is only holding a key while they read. The
		// more specific state wins, and it stays SILENT for the same reason the
		// laststand branch is.
		if ( IS_TRUE( player.tod_solo_upg_active ) )      // already mid-pick
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny MID-PICK" );
			continue;
		}
		// A round event is live — refuse, but SAY SO. Mute refusals read as dead
		// triggers (the 2026-08-26 "teleporter wasn't activated" report; the full
		// note lives on _tod_teleport.gsc's copy of this branch). Note the
		// laststand branch below stays SILENT on purpose: a downed player is
		// holding the use key trying to get revived, and a deny sound there would
		// machine-gun in their ear for the whole crawl.
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny PAUSE" );
			player PlaySound( "zmb_no_purchase" );
			continue;
		}
		if ( player laststand::player_is_in_laststand() )
			continue;
		// A revive press is not a purchase (_zm_blockers.gsc:307). Reviving polls
		// the raw USE button (_zm_laststand.gsc:1129), so without this the press
		// that revives a teammate at a terminal also spends 2000+ points AND
		// burns one of this station's limited uses. Silent, like the branch
		// above: the player is holding use.
		if ( player zm_utility::in_revive_trigger() )
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny REVIVE-TRIG" );
			continue;
		}
		if ( !player_has_upgrades_left( player ) )        // everything maxed
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny ALL-MAXED" );
			player PlaySound( "zmb_no_purchase" );
			continue;
		}
		if ( station_depleted( player, self.tod_station_id ) )   // per-station cap (5, crown altar 3)
		{
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		cost = station_cost( player );
		if ( !( player zm_score::can_player_purchase( cost ) ) )
		{
			if ( IS_TRUE( level.tod_dev ) )
				tod_quiet_print( "altar " + self.tod_station_id + ": deny POOR (" + cost + ")" );
			player PlaySound( "zmb_no_purchase" );
			continue;
		}

		player PlaySound( "zmb_cha_ching" );
		player zm_score::minus_to_player_score( cost );
		if ( !isdefined( player.tod_station_buys ) )
			player.tod_station_buys = 0;
		player.tod_station_buys++;
		player.tod_station_paid = cost;   // held for the both-cards-dead refund
		// per-station use count (the cap); remember WHICH terminal so a refund
		// can hand the use back to the right one
		if ( !isdefined( player.tod_station_uses ) )
			player.tod_station_uses = [];
		player.tod_station_uses[ self.tod_station_id ] = station_uses( player, self.tod_station_id ) + 1;
		player.tod_station_last_id = self.tod_station_id;

		player thread solo_upgrade_flow();
		wait 0.5;
	}
}

// ---------------------------------------------------------------------------
// THE SOLO STATION FREEZE (v16.84, user 2026-09-03: "on solo when you use the
// alter can we freeze the game like on the round based upgrades. I only want
// this applied on solo")
// ---------------------------------------------------------------------------
// The station shipped deliberately UNFROZEN from 2026-08-20 — "the world does
// NOT pause; that is the risk" is written into this file's header, into init(),
// into CLAUDE.md and into two release notes. That risk was always a CO-OP
// argument: with a teammate up, fifteen seconds of standing still is a cost
// somebody else absorbs. Alone it is nobody's, so the solo buyer paid 3000
// points for a choice they could not afford to read — and the map's own
// concession to that (the reveal runs at half speed while the world is live,
// TOD_REVEAL_LIVE_SCALE) only ever shortened the exposure instead of removing
// it.
//
// SOLO NOW GETS THE ROUND-EVENT TREATMENT, both lanes, through the SAME two
// functions the round event uses — no second implementation of a freeze:
//   set_world_pause( true )  — stock's world_is_paused (round_spawning waits on
//                              it, _zm.gsc:3747) plus every tod boss director
//                              and spawner that reads level.tod_upgrade_pause,
//                              plus ignoreall + a 0.05 anim rate on live AI.
//   menu_freeze( true )      — weapons off, jump off, movement pinned.
// THREE THINGS FOLLOW FOR FREE, all already keyed on level.tod_upgrade_pause
// and all of them wanted here:
//   * the reveal plays at FULL speed (_tod_upgrade_ui::reveal_deal stops
//     applying TOD_REVEAL_LIVE_SCALE) — the show was only rushed because the
//     world was live;
//   * upgrade_damage_cb returns 0, so nobody farms a frozen horde through the
//     card panel;
//   * EVERY input lane opens on the panel (_tod_upgrade_ui, v16.81) — the
//     d-pad-only station rule was earned by the player being mid-fight, and
//     they are not mid-fight any more.
// CO-OP IS BYTE-FOR-BYTE UNCHANGED: station_freeze_wanted() is the only gate,
// and with two or more players connected it answers false before anything in
// this block runs.
//
// NO self: the three questions this asks are all LEVEL state (party size, the
// finale flag, who owns the pause), and a "self = the buying player" line on a
// function that never reads self is a comment that will be believed and is
// false. Every other function in this block does take a player.
function station_freeze_wanted()
{
	// SOLO = ONE CONNECTED PLAYER. Deliberately not "one player ALIVE": a
	// partner who bled out is still in the match, still watching this screen and
	// still waiting on the round-change respawn, and freezing the world under
	// them is a behaviour change they never asked for and cannot see the cause
	// of. Read at present time, so a late joiner mid-pick cannot flip it —
	// station_pause_end releases whatever was actually claimed either way.
	if ( GetPlayers().size != 1 )
		return false;

	// Somebody else already owns a pause — a round event. Unreachable today (station_use_loop refuses
	// a buy outright in that state), and kept so set_world_pause can never get
	// a second owner if a future path ever arrives here.
	if ( IS_TRUE( level.tod_upgrade_pause ) )
		return false;

	return true;
}

// self = player. TRUE while THIS player's own station pick is the thing holding
// the world pause open. It is the one question that separates "a round event
// took the UI over" from "I froze the world myself" — before v16.84 a raw
// level.tod_upgrade_pause read answered both, because only one of them existed.
function station_owns_pause()
{
	return ( isdefined( level.tod_station_pause_owner ) && level.tod_station_pause_owner == self );
}

// self = player
function station_pause_begin()
{
	level.tod_station_pause_owner = self;
	if ( !isdefined( level.tod_station_pause_seq ) )
		level.tod_station_pause_seq = 0;
	level.tod_station_pause_seq++;

	set_world_pause( true );
	self menu_freeze( true );   // refuses on a laststand player, by its own rule

	level thread station_pause_watchdog( self, level.tod_station_pause_seq );
}

// self = player. Releases ONLY what we still own. A round event that took over
// cleared the owner at its takeover notify and now owns BOTH lanes, and calling
// set_world_pause( false ) here would unfreeze the world in the middle of its
// deal — which is the same rule the "never call menu_freeze(false) on the
// takeover path" corollary in solo_upgrade_flow has always stated, now enforced
// in one place instead of asserted in a comment.
function station_pause_end()
{
	if ( !( self station_owns_pause() ) )
		return;

	level.tod_station_pause_owner = undefined;
	self menu_freeze( false );
	set_world_pause( false );
}

// A PERMANENTLY FROZEN WORLD IS THE WORST THING THIS FILE CAN LEAVE BEHIND —
// run_upgrade_event's wait loop carries the same warning in capitals. Its own
// caller, solo_upgrade_flow, carries self endon( "disconnect" ), so a
// disconnect between begin and end kills the only thread that would ever have
// released the pause. In SOLO that disconnect is the match ending anyway, which
// is precisely the kind of reasoning that stops being true the day somebody
// adds a path — so this is the belt to that argument's braces.
//
// KEYED ON A SEQUENCE, NOT ON THE PLAYER: buy, release, buy again inside the
// ceiling and a player-keyed watchdog would tear down the SECOND pick's pause.
// Every begin mints a new seq and only that seq may release.
function station_pause_watchdog( player, seq )
{
	level endon( "end_game" );

	// The 15s pick window, the reveal and the confirm flash, with room to spare.
	wait( TOD_UPG_CHOICE_TIMEOUT + 12 );

	if ( !isdefined( level.tod_station_pause_seq ) || level.tod_station_pause_seq != seq )
		return;                                   // a later pick owns the pause now
	if ( !isdefined( level.tod_station_pause_owner ) )
		return;                                   // released normally, or a round event claimed it

	level.tod_station_pause_owner = undefined;
	if ( isdefined( player ) && isplayer( player ) )
		player menu_freeze( false );
	set_world_pause( false );
}

// self = player
function solo_upgrade_flow()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	self.tod_solo_upg_active = true;

	opts = roll_options( self );
	if ( !isdefined( opts ) )
	{
		// NOT belt+braces (repo review 2026-09-01): this is the NORMAL exit for a
		// player whose every domain is maxed but who is still tier-eligible —
		// player_has_upgrades_left() admits them for the promotion chance, and
		// roll_options deals nothing on the (100 - TOD_TIER_CARD_PCT)% of buys
		// where the tier card is not drawn (v16.56: a FULL luck bar makes that
		// 0% — tier_card_guaranteed — so a maxed, eligible player who banks the
		// bar never buys silence here). It used to be cha-ching, -3000,
		// +3000, silence: the Workshop report "hold F to buy, I do and nothing
		// happens" (2026-08-30). The refund stands; the refusal is now AUDIBLE
		// (map doctrine: a deny is the sound, no floaty captions).
		self solo_refund();
		self PlaySound( "zmb_no_purchase" );
		if ( IS_TRUE( level.tod_dev ) )
			tod_quiet_print( "altar: no card drawn (domains maxed, promotion not rolled) - refunded" );
		self.tod_solo_upg_active = false;
		return;
	}

	for ( ;; )
	{
		// A scheduled round event owns the shared card UI — hold until it is
		// fully over, then re-present the SAME cards with a fresh timer.
		//
		// THE RAW FLAG IS THE RIGHT READ *HERE*, unlike the poll inside
		// solo_present_interruptible (v16.84): we can never own the pause at
		// the top of this loop. First pass, nothing has begun; and both
		// `continue` paths that come back here have already relinquished — the
		// takeover branch below is entered only when the pause is somebody
		// else's, and the choice == -1 path runs station_pause_end first. No
		// station_owns_pause() guard is added for that reason: a guard nobody
		// can watch fire is not a guard.
		if ( IS_TRUE( level.tod_upgrade_pause ) )
		{
			level waittill( "tod_upg_event_over" );
			wait 0.5;   // let the event's unfreeze/unpause settle

			// The event may have advanced/maxed the SAME domains these cards
			// hold — refresh both NOW and drop any dead card (verify
			// 2026-08-20: never present a card that can no longer pay out).
			// Both dead -> refund without presenting anything.
			alive = [];
			if ( self solo_refresh_option( opts[ 0 ] ) )
				alive[ alive.size ] = opts[ 0 ];
			if ( isdefined( opts[ 1 ] ) && ( self solo_refresh_option( opts[ 1 ] ) ) )
				alive[ alive.size ] = opts[ 1 ];
			if ( alive.size == 0 )
			{
				// TAKE THE PANEL DOWN — this is the ONE exit that can leave it lit
				// (audit 2026-08-26). The round event's takeover killed the
				// in-flight present_choice with todUpgShow still 1, and normally
				// the event's OWN present_choice repaints/clears the fields for
				// this player a moment later. But a player who was DOWN when the
				// event fired is excluded from it entirely, so no repaint ever
				// comes, and this branch refunds and breaks without clearing —
				// leaving a lit card panel until their next deal.
				//
				// SAFE HERE AND NOWHERE ELSE: this runs AFTER the
				// waittill( "tod_upg_event_over" ) + wait 0.5 above, so the
				// event's own field writes are finished. Do NOT "fix" this
				// instead by clearing on the pause check's early return, or by
				// reordering the pause and laststand checks — that fires while
				// run_upgrade_event has only just threaded its choice flows and
				// would blank the event's freshly painted cards, which is exactly
				// what the takeover comment above warns about.
				self tod_upgrade_ui::set_field( "todUpgShow", 0 );
				self solo_refund();
				break;
			}
			opts = alive;
			continue;
		}

		// CO-OP: NO FREEZE (user 2026-08-20: "it pauses you but doesn't pause
		// zombies so you are helpless") — but JUMP IS LOCKED (user 2026-08-21:
		// "when using the manual card upgrade you should not be able to jump"),
		// since jump is the hold-to-lock button and hopping while choosing both
		// fires the lock and launches you off a balcony. Movement and weapons
		// stay fully live; only the jump input is taken, and it is restored on
		// every exit path below including the takeover.
		// That is the whole risk model: you fight WHILE you choose, or you let
		// the 15s timer auto-lock the focused card. The lock button is HOLD
		// jump, so an ordinary hop never locks a card by accident.
		//
		// SOLO: THE WORLD FREEZES, EXACTLY LIKE A ROUND EVENT (v16.84, user
		// 2026-09-03: "on solo when you use the alter can we freeze the game
		// like on the round based upgrades. I only want this applied on solo").
		// The risk model above is a CO-OP argument that never applied to one
		// player: with a teammate up, fifteen seconds of standing still is a
		// cost somebody else absorbs; alone it is nobody's, so the solo buyer
		// either read their cards or survived, never both. station_freeze_wanted
		// owns the "is this solo" question and the finale carve-out; the
		// station_pause_begin/end pair owns the two lanes.
		//
		// Corollary that SURVIVES the freeze: we must never call
		// menu_freeze(false) on the takeover path — on a round-event takeover
		// the EVENT's own flow owns the freeze flag (it is flat, not nested)
		// and unfreezes at its end. station_pause_end() is a NO-OP once the
		// event has claimed the pause, which is exactly what keeps that true.
		// Jump is taken for exactly the duration of the card prompt and given
		// back the instant it returns — a tight window on EVERY path (normal
		// lock, timeout, down, takeover), so a thread that dies mid-present
		// can never strand the player unable to jump. In the frozen lane
		// menu_freeze owns jump instead, and it deliberately does NOT hand it
		// back to a player who went down mid-pick (stock's revive restores it).
		froze = station_freeze_wanted();
		if ( froze )
			self station_pause_begin();
		else
		{
			self AllowJump( false );
			// v18.9 — AND THE OFFHANDS, which this lane never took. The card panel
			// advertises the offhand PAIR as its switch control (tod_upgrade.lua
			// draws "[{+smoke}] < SWITCH > [{+frag}]" unconditionally), and the
			// comment in _tod_upgrade_ui.gsc's focus lane asserted that menu_freeze
			// held DisableOffhandWeapons() so a press could never throw one — true
			// in the FROZEN lane and false here, because the co-op arm was
			// AllowJump( false ) and nothing else. Switching cards in co-op threw a
			// lethal and a tactical. Live from any Max Ammo onward, and immediately
			// with Widow's Wine or DISTRACTION's monkey.
			//
			// This is a small, deliberate softening of the co-op risk model — you
			// still fight while you choose, you just keep your grenades.
			self DisableOffhandWeapons();
		}
		choice = self solo_present_interruptible( opts );
		if ( froze )
			self station_pause_end();   // no-op if a round event claimed the pause
		else
		{
			// GUARDED, both of them (v18.9). A scheduled round event can take the
			// UI over and thread menu_freeze( true ) synchronously before this
			// lane's 0.05 s poll wakes — handing jump and offhands back here would
			// undo the freeze that is now holding the player. menu_freeze's own
			// exit guards the identical call for the identical reason.
			//
			// AND NOT TO A DOWNED PLAYER: solo_present_interruptible returns from
			// inside last stand, and the 2026-08-26 audit already fixed this exact
			// shape in menu_freeze ("left them hopping around while crawling").
			// Stock's revive restores both. The altars sit on open balconies and
			// the crown terrace, so a crawler with jump back is a fall, not a joke.
			if ( !IS_TRUE( self.tod_menu_frozen ) && !( self laststand::player_is_in_laststand() ) )
			{
				self AllowJump( true );
				self EnableOffhandWeapons();
			}
		}

		if ( choice == -1 )
			continue;   // takeover — the event owns the UI; re-present after

		picked = opts[ 0 ];
		other = opts[ 1 ];   // may be undefined (only one domain was left)
		if ( choice == 2 && isdefined( opts[ 1 ] ) )
		{
			picked = opts[ 1 ];
			other = opts[ 0 ];
		}

		// Deferred cards re-clamp vs current levels (see header comment).
		if ( !( self solo_refresh_option( picked ) ) )
		{
			picked = undefined;
			if ( isdefined( other ) && ( self solo_refresh_option( other ) ) )
				picked = other;
		}

		ok = false;
		if ( isdefined( picked ) )
		{
			ok = apply_upgrade( self, picked );
			// a refused TIER pick (timed out / could not land) falls back to the
			// other card — the buy must pay out or be refunded, never vanish
			if ( !ok && picked.domain == "tier" && isdefined( other ) && other.domain != "tier"
			  && ( self solo_refresh_option( other ) ) )
				ok = apply_upgrade( self, other );
		}
		if ( ok )
		{
			self.tod_luck_bar = 0;   // solo rolls spend the luck bar too (the odds rode it)
			self.tod_station_paid = 0;
		}
		else
			self solo_refund();

		break;
	}

	self.tod_solo_upg_active = false;
}

// self = player -> 1|2, or -1 = a round event took the UI over. The takeover
// notify fires synchronously inside run_upgrade_event BEFORE it threads its
// per-player flows, so the solo present thread is already dead when the
// event's present_choice first touches the shared fields — never two writers.
function solo_present_interruptible( opts )
{
	self.tod_solo_result = undefined;
	self thread solo_present_run( opts );

	for ( ;; )
	{
		if ( isdefined( self.tod_solo_result ) )
			break;
		// A ROUND EVENT TOOK THE UI OVER — unless the pause is OUR OWN. v16.84
		// gave the solo station a world freeze, so the raw flag stopped being a
		// takeover test the moment it became self-inflicted: read like that, a
		// solo pick would hand back -1 on its very first poll and re-present
		// itself forever. station_owns_pause() is the whole difference.
		if ( IS_TRUE( level.tod_upgrade_pause ) && !( self station_owns_pause() ) )
			return -1;
		if ( self laststand::player_is_in_laststand() )
		{
			// Downed mid-pick. GRACE FIRST (verify 2026-08-20): if the down
			// landed during present_choice's 0.7s confirm flash the pick is
			// already DECIDED — wait out the flash and take the real result
			// instead of stomping a locked card 2 with the default.
			for ( g = 0; g < 16; g++ )
			{
				if ( isdefined( self.tod_solo_result ) )
					break;
				wait 0.05;
			}
			if ( isdefined( self.tod_solo_result ) )
				break;
			// Truly mid-browse: kill the menu, clear the stranded card UI,
			// lock the DEFAULT card — they paid, they keep the upgrade.
			self notify( "tod_solo_down_abort" );
			self tod_upgrade_ui::set_field( "todUpgShow", 0 );
			return 1;
		}
		wait 0.05;
	}

	r = self.tod_solo_result;
	self.tod_solo_result = undefined;
	return r;
}

// self = player
function solo_present_run( opts )
{
	self endon( "disconnect" );
	level endon( "end_game" );
	level endon( "tod_global_upg_takeover" );
	self endon( "tod_solo_down_abort" );

	self push_panel_hints();   // v14.35 — the station deals the same cards, so it owes the same line
	r = self tod_upgrade_ui::present_choice( opts, TOD_UPG_CHOICE_TIMEOUT );
	self.tod_solo_result = r;
}

// self = player. Refresh a rolled option vs the CURRENT level and re-clamp;
// false = the domain maxed while we were deferred (the card is dead).
function solo_refresh_option( o )
{
	// A deferred TIER card is alive only while the promotion is still possible
	// — and never for a downed player (the solo down-abort locks the default
	// card; a swap must not ride that path). Re-encode the class/tier code.
	if ( o.domain == "tier" )
	{
		if ( self laststand::player_is_in_laststand() )
			return false;
		// v14.39 — asks the floor-blind question, then RE-STAMPS the lock. A
		// card that was dealt locked must come back locked, not vanish: the
		// deferred path re-presents the same deal after a round event takes
		// over, and a card disappearing between the two showings would read as
		// the takeover having stolen it. Re-stamped rather than carried so a
		// player who CLIMBED during the takeover gets it back unlocked, which
		// is the one direction this can legitimately change.
		if ( !tier_card_ready_but_for_floor( self ) )
			return false;
		o.locked = ( tier_floor_pending( self ) > 0 );
		o.cur = tier_card_code( self );
		return true;
	}
	// A deferred card is dead if its domain is no longer ROLLABLE — a tier-up
	// during the takeover changes the gun, and gun-bound domains (the twin
	// ladders, Thor's Thunder) may have gone dark with it.
	d = find_domain( o.domain );
	if ( !isdefined( d ) || !domain_available( self, d ) )
		return false;
	o.max = domain_max( self, d );
	o.cur = get_level( self, o.domain );
	if ( o.cur + o.levels > o.max )
		o.levels = o.max - o.cur;

	// BAND HONESTY on the deferred path too — the third and last place `levels`
	// can shrink out from under `rarity`. This card was rolled BEFORE a scheduled
	// round event took over, and the player may have levelled this very domain in
	// that event; re-presenting it still wearing its original band would show
	// "ULTIMATE +3" over a payout the takeover just cut to +1. Same clamp-down
	// rule as make_option, and the TIER card never reaches here (it returns
	// above).
	if ( o.levels >= 1 && o.levels < o.rarity )
	{
		o.rarity = o.levels;
		o.rarity_name = rarity_label( o.rarity );
	}
	return ( o.levels > 0 );
}

// self = player
function solo_refund()
{
	if ( !isdefined( self.tod_station_paid ) || self.tod_station_paid <= 0 )
		return;
	self zm_score::add_to_player_score( self.tod_station_paid );
	self.tod_station_paid = 0;
	if ( isdefined( self.tod_station_buys ) && self.tod_station_buys > 0 )
		self.tod_station_buys--;   // that buy never happened — the price steps back
	// ...and the per-station use comes back too (the cap counts real buys only)
	if ( isdefined( self.tod_station_last_id ) && station_uses( self, self.tod_station_last_id ) > 0 )
		self.tod_station_uses[ self.tod_station_last_id ]--;
}

// ---------------------------------------------------------------------------
// v17.97 — DEV PRINTS ARE MUTABLE. level.tod_dev_quiet (set beside tod_dev in
// zm_tod2_cybercity::tod_resolve_dev_flags) silences every bottom-left IPrintLn
// in this file — screenshot sessions want dev + god with a clean HUD. Each
// print site's own tod_dev gate is unchanged; this is one extra gate under it.
// IPrintLnBold (real game toasts) is not routed here.
function tod_quiet_print( msg )
{
	if ( IS_TRUE( level.tod_dev_quiet ) )
		return;
	IPrintLn( msg );
}

function tod_quiet_print_to( msg )   // self = the player to print to
{
	if ( IS_TRUE( level.tod_dev_quiet ) )
		return;
	self IPrintLn( msg );
}

// ---------------------------------------------------------------------------
// THE CARD TEST BENCH (DEV ONLY, user 2026-09-28: "In dev mode add a button in
// the crown to trigger the cards so i can test animations. You will need to
// disregard current upgrades cause im full in dev mode").
//
// A crafting table between the crown hall's uplink dais and the sanctuary steps.
// Every press deals a REAL panel through the station's own lane (freeze, THE
// PULL reveal, pick, the down / takeover aborts) but with cards built for the
// test, NOT rolled from the player's pool:
//   - the domains are any the player's class can hold, IGNORING their level
//     (tod_dev_maxed has every domain full, so the real pool is empty);
//   - each card shows a random low "current" level so the new pips have room
//     to light;
//   - the rarities walk a fixed script first, so every rarity and every
//     reveal case is seen within nine presses (the first three force THE
//     REACH, docs/201), then roll at random;
//   - THE PICK IS NEVER APPLIED, the luck bar is not spent, nothing is paid.
// Spawned only when level.tod_dev is true. Logs [TOD_CARD_TEST].
// ---------------------------------------------------------------------------
#define TOD_CARD_TEST_ORG      ( 0, 8860, 19392 )   // hall_center (0, 8608) + 252 north: clear of the dais (+112) and the sanctuary foot (y 8952)
#define TOD_CARD_TEST_YAW      270                  // the table faces south, toward the dais
#define TOD_CARD_TEST_TRIG_R   48

function card_test_log( msg )
{
	if ( !IS_TRUE( level.tod_dev ) )
		return;
	line = "[TOD_CARD_TEST] ms=" + GetTime() + " " + msg;
	/#
	PrintLn( line );
	#/
}

function dev_card_test_spawn()
{
	level endon( "end_game" );
	level flag::wait_till( "initial_blackscreen_passed" );
	if ( !IS_TRUE( level.tod_dev ) )
		return;

	org = TOD_CARD_TEST_ORG;
	fwd = AnglesToForward( ( 0, TOD_CARD_TEST_YAW, 0 ) );
	table = Spawn( "script_model", org );
	if ( isdefined( table ) )
	{
		table SetModel( "p8_zm_crafting_table" );
		table.angles = ( 0, TOD_CARD_TEST_YAW, 0 );
		table NotSolid();
	}
	t = Spawn( "trigger_radius_use", org + fwd * 57 + ( 0, 0, 36 ), 0, TOD_CARD_TEST_TRIG_R, 64 );
	if ( !isdefined( t ) )
	{
		card_test_log( "SPAWN_FAIL reason=trigger (entity pool?)" );
		return;
	}
	t TriggerIgnoreTeam();
	t SetCursorHint( "HINT_NOICON" );
	// ONE constant string (the hint budget; never interpolate)
	t SetHintString( "Hold ^3[{+activate}]^7 ^5CARD TEST^7 - Deals every rarity in turn / No upgrade is applied" );
	card_test_log( "READY org=" + org + " trig=" + t.origin + " table=" + isdefined( table ) );

	level.tod_card_test_n = 0;
	for ( ;; )
	{
		t waittill( "trigger", p );
		if ( !isdefined( p ) || !isplayer( p ) || !isalive( p ) )
			continue;
		if ( p laststand::player_is_in_laststand() )
			continue;
		if ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( p.tod_solo_upg_active ) || IS_TRUE( p.tod_card_test_busy ) )
		{
			card_test_log( "REFUSED player=" + p GetEntityNumber() + " reason=" + ( IS_TRUE( level.tod_upgrade_pause ) ? "world_paused" : "deal_open" ) );
			p PlaySound( "zmb_no_purchase" );
			continue;
		}
		p thread dev_card_test_run();
		wait 0.5;
	}
}

// The press script: THE REACH first (docs/201 section 4: an EPIC that comes SO CLOSE to gold, a LEGENDARY that
// BREAKS THROUGH from purple, a COMMON that comes SO CLOSE to blue), then every rarity pair worth watching, then
// random. 0 in the second slot = a ONE-card deal (its own reveal path). The third number forces the left card's
// reach: 0 none (the normal reach odds), 1 SO CLOSE at its final rung, 2 BREAK THROUGH from the rung below.
function card_test_pair( n )
{
	pairs = array( array( 3, 1, 1 ), array( 4, 2, 2 ), array( 1, 2, 1 ),
		array( 1, 2, 0 ), array( 3, 4, 0 ), array( 4, 4, 0 ), array( 2, 3, 0 ), array( 4, 0, 0 ), array( 1, 1, 0 ) );
	if ( n < pairs.size )
		return pairs[ n ];
	return array( 1 + RandomInt( 4 ), 1 + RandomInt( 4 ), 0 );
}

// self = player. One test card for `d` at rarity `r`, ignoring the player's level. room (optional): levels of
// headroom it must keep above its "current" level (a forced SO CLOSE needs room for the rung above).
function card_test_option( d, r, room_needed )
{
	o = SpawnStruct();
	o.domain = d.key;
	o.display = d.display;
	o.desc = d.desc;
	o.tier = d.tier;
	o.max = domain_max( self, d );
	o.rarity = r;
	if ( o.rarity > o.max )
		o.rarity = o.max;             // a max-3 card cannot show +4; it shows what it could pay
	if ( o.rarity < 1 )
		o.rarity = 1;
	o.levels = o.rarity;
	keep = o.levels;
	if ( isdefined( room_needed ) && room_needed > keep )
		keep = room_needed;
	room = o.max - keep;              // levels already "owned" so the gain (or the forced reach) fits under the cap
	o.cur = 0;
	if ( room > 0 )
		o.cur = RandomInt( room + 1 );
	o.rarity_name = rarity_label( o.rarity );
	o.dev_test = true;                // THE HOT STREAK (docs/201) never counts a test deal
	return o;
}

// self = player
function dev_card_test_run()
{
	self endon( "disconnect" );
	level endon( "end_game" );

	// every domain this class can hold, level ignored; the one-rarity domains
	// (set_rarity_lock) are left out - their card cannot change rarity
	pool = [];
	for ( i = 0; i < level.tod_domains.size; i++ )
	{
		d = level.tod_domains[ i ];
		if ( isdefined( d.rarity_lock ) || !domain_available( self, d ) )
			continue;
		pool[ pool.size ] = d;
	}
	if ( pool.size == 0 )
	{
		card_test_log( "NO_DOMAINS player=" + self GetEntityNumber() + " class=" + ( isdefined( self.tod_class ) ? self.tod_class : "none" ) );
		self PlaySound( "zmb_no_purchase" );
		return;
	}

	n = level.tod_card_test_n;
	level.tod_card_test_n++;
	pair = card_test_pair( n );

	// THE REACH (docs/201): a forced reach needs a left card whose domain can hold it - its own rarity, and for
	// SO CLOSE the rung above too. With no such domain the press falls back to the normal reach odds.
	force = pair[ 2 ];
	need = 0;
	if ( force == 1 )
		need = pair[ 0 ] + 1;
	else if ( force == 2 )
		need = pair[ 0 ];
	pool_a = pool;
	if ( need > 0 )
	{
		pool_a = [];
		foreach ( d in pool )
		{
			if ( domain_max( self, d ) >= need )
				pool_a[ pool_a.size ] = d;
		}
		if ( pool_a.size == 0 )
		{
			pool_a = pool;
			force = 0;
			need = 0;
		}
	}
	a = RandomInt( pool_a.size );
	opts = [];
	opts[ 0 ] = self card_test_option( pool_a[ a ], pair[ 0 ], need );
	if ( force > 0 )
		opts[ 0 ].tod_reach_force = force;
	if ( pair[ 1 ] > 0 && pool.size > 1 )
	{
		rest = [];
		foreach ( d in pool )
		{
			if ( d.key != opts[ 0 ].domain )
				rest[ rest.size ] = d;
		}
		if ( rest.size > 0 )
			opts[ 1 ] = self card_test_option( rest[ RandomInt( rest.size ) ], pair[ 1 ] );
	}
	msg = "DEAL n=" + n + " player=" + self GetEntityNumber() + " reach=" + force + " a=" + opts[ 0 ].domain + ":" + opts[ 0 ].rarity_name + " cur=" + opts[ 0 ].cur + "/" + opts[ 0 ].max;
	if ( isdefined( opts[ 1 ] ) )
		msg = msg + " b=" + opts[ 1 ].domain + ":" + opts[ 1 ].rarity_name + " cur=" + opts[ 1 ].cur + "/" + opts[ 1 ].max;
	else
		msg = msg + " b=none";
	card_test_log( msg );

	// THE STATION'S OWN LANE: the same freeze rule, the same interruptible
	// present (round-event takeover and going down both end it cleanly)
	self.tod_card_test_busy = true;
	self.tod_solo_upg_active = true;
	froze = station_freeze_wanted();
	if ( froze )
		self station_pause_begin();
	else
	{
		self AllowJump( false );
		self DisableOffhandWeapons();
	}
	choice = self solo_present_interruptible( opts );
	if ( froze )
		self station_pause_end();
	else if ( !IS_TRUE( self.tod_menu_frozen ) && !( self laststand::player_is_in_laststand() ) )
	{
		self AllowJump( true );
		self EnableOffhandWeapons();
	}
	self.tod_solo_upg_active = false;
	self.tod_card_test_busy = false;
	// NOTHING IS APPLIED - a test deal changes no level, luck or points
	card_test_log( "END n=" + n + " player=" + self GetEntityNumber() + " choice=" + choice + " froze=" + froze + " applied=0" );
}

