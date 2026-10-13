# 156 — The Civil Protector partner: architecture and upgrade pipeline

**2026-09-23 implementation update:** the later four-partner collect/build/equip
request is implemented in [docs/159](159_buildable_partners.md). It supersedes
the free automatic Protector grant below. The shop, armor upgrades and weapon
ladder remain a design proposal, not shipped features.

**STATUS 2026-09-23: DESIGN, REVISION 3.3, NOT BUILT.** Nothing in the game has
changed. Revision 3 applies the user's four answers (§2). Revision 3.1 folds in
a second review round (a robustness attacker and a completeness verifier).
Revision 3.2 adds the user's weapon requirement: the robot can be upgraded to
hold different guns (AR, SMG, shotgun and more), §3.7a. Revision 3.3 applies
the user's call that the guns are a LADDER, where each later gun is stronger
(D12). §11 records what changed across revisions and why.

Requested 2026-09-22 by the user. This is one of Tower of Doom II's two headline
gameplay differences from TOD1 (the other is the gift shop):

- every player gets a **friendly Civil Protector**, **blue**, the same robot the
  Rogue Protector wore in TOD1, **paired to that player**;
- **no Rogue Protectors** on this map;
- the player upgrades **their character AND their partner** as the match goes;
- every partner upgrade is **visible on the robot in the 3D world** (an armor
  upgrade adds armor) as well as functional;
- the robot can be upgraded to **hold different weapons** (user 2026-09-23:
  *"it holds an AR, holds a submachine gun, holds a shotgun"*);
- adding an upgrade later has to be a **streamlined process**, covering Blender
  MCP, the art-pack zip, "all of it".

User's framing, 2026-09-23: *"this map will change a lot, this is just a
starting point."* So this doc aims for a solid, extensible core and keeps the
balance numbers as placeholders.

Effects follow [docs/155](155_fx_art_workflow.md). The isolated tools root and
the `zm_tod2_cybercity` names follow [docs/154](154_tod2_isolation.md).

---

## 1. The whole shape on one page

```
                              ONE HUMAN-WRITTEN SOURCE
                           tools/partner/registry.json
   (upgrades: name, shop text, price per level, effect ladder, per-level visual
    stage, slot; weapons: fire profile, gun model, price; shops; body tint;
    budgets.  Tools READ it, never write it.)
                                        |
      donor_gdt/zod_robot/*.json        |        per-upgrade install manifests
      (committed snapshots of the  -----+-----   (written by the model pipeline;
       pack's robot rows + rig)         |         their existence = "installed")
                                        v
                         node tools/partner/gen_partner.js
                         (--check runs before the sync in EVERY build)
     +---------------+-------------+--------------+----------------+
     v               v             v              v                v
 _tod_partner_   TodPartner    cc_partner.gdt  tod_partner.zpkg  tod_partner.
 data.gsc        Data.lua      (body twin,     (included by one  generated.json
 (GENERATED)    (GENERATED)     LODs, stage     hand line in the (lint input)
                                models, tiles)  main .zone)

 ONE FRONT DOOR:  .\tools\partner\ptn.ps1 <verb>
   new | studio | stage | approve | ship-model | preview | art | check | status | retire | rollback

 BLENDER MCP (port 9880)               ART PACK                        RUNTIME
 art/partner/robot_base.blend (RO)     ptn art <key> pack -> zip   ->  _tod_partner.gsc          lifecycle, follow, death, recharge, slam
 art/partner/upgrades/<key>.blend      user sends to the generator     _tod_partner_combat.gsc   targets, fire, damage, integrity, aggro
   stage scripts own the geometry      ptn art <key> install --latest  _tod_partner_upgrades.gsc store, grant funnel, stats, reconcile
   fit_check on the robot's 440 anims                                  _tod_shop.gsc             item shops (catalogue-driven)
   ship-model: save, bake, LODs,                                       TodShopPanel.lua          the shop panel
   xmodel_bin, verify, preview                                         TodPartnerChip.lua        HUD chip
```

The promise: **a new upgrade or a new gun is a registry row plus assets.** Code
is written only when an upgrade needs a behaviour no existing effect kind
provides (§3.7), or a gun needs a fire mode or a rung needs a gate kind that
does not exist yet (§3.7a). Every other step is one `ptn` verb.

---

## 2. Decisions

### 2.1 Decided by the user (2026-09-23)

| # | Question | The user's answer | What it means here |
|---|---|---|---|
| D1 | How are partner upgrades earned? | *"There will be item shops around the map where you can upgrade your protector."* | Partner upgrades are **bought with points at item shops** (§3.9). Card deals stay player-only. No partner card kind, no card id, no card-panel changes. |
| D2 | Can it be hurt? | *"Yes. It will need to recharge and spawn in with the slam animation. It can die."* | Zombies attack it; its integrity drops; at 0 it is **destroyed**, **recharges** for a while, then **drops back in with the sky-trail slam** beside its owner (§3.3, §3.6). |
| D4 | Revives? | *"No revives."* | The vendored companion revive stays disabled, and no revive upgrade exists. |
| D6 | Floor 40's new enemy | *"Leave it empty, this map will change a lot."* | Floor 40 introduces nothing. |
| D12 | Are the robot's guns sidegrades or a ladder? | *"Ladder"* | Each later gun is stronger. The ladder's assumed shape is under §2.2. |

### 2.2 Defaults assumed until the user says otherwise

| # | Default | Why |
|---|---|---|
| D3 | Partner kills give the owner full fair-share luck and mana credit and normal powerup drop rolls. A partner last hit on an elite or boss counts as the owner's (luck jackpot, kill confirm). Points are banked quietly at 50% and shown as one popup every couple of seconds. Player-only procs (BOUNTY, SCAVENGER, LEECH, ADRENALINE) never fire. | The luck bar and mana are defined against the whole round's kills, so an uncredited partner kill would quietly tax the owner. Stock drops need a player killer. |
| D5 | Rogue Protector slots are replaced per §4.2 (unlock ladder 10 sprinter, 20 reaver, 30 hound, 40 empty). | The smallest change that keeps every hall and the finale working. It is a starting point. |
| D7 | Every robot's body is blue; its light strips and eyes glow in its owner's party colour. | Four identical robots in a quad would be unreadable. |
| D8 | Blue arms (the pack's gold robot overrides its arms back to silver; we drop that). | The user asked for a blue robot. |
| D9 | Upgrades are behaviours and visible parts, not copies of player cards. | Player cards already cover DAMAGE, FIRE RATE, HEADSHOT, DR. |
| D10 | The shop freezes the world in solo and not in co-op, the same rule as the personal upgrade station. | That rule already exists and was earned the hard way (`station_freeze_wanted`). |
| D11 | Shops sit at the base, every breather lounge, the crown hall and every spire hub. | "Around the map", on the same furniture grammar as crates and stations. |
| D13 | A gun is bought once. Every gun you own stays owned, and any kiosk re-equips an owned gun for free. The AR is owned from the start. Buying a rung equips it. | Lower rungs stay useful for reach, and for future guns that share a rung. |

**The gun ladder's shape (D12 is the user's; this shape is assumed until the
user says otherwise):**
- **Rungs:** 1 AR (free), 2 SMG, 3 shotgun, in the order the user listed them.
- **Step:** each rung is ×1.5625 trash-killing power, the same step as the class
  guns' tier ladder (`TIER_DPS` 1 / 1.5625 / 2.4414).
- **Unlock:** a rung costs points, needs the rung below it owned, and needs the
  owner to have reached floor 10 (rung 2) or floor 30 (rung 3). Those are the
  class-tier promotion floors.
- **ARMAMENT** adds at most one rung step on whatever gun is held.
- **Same-rung guns are sidegrades.** A future gun either adds a new top rung or
  joins an existing rung as an equal-power alternative, so adding one never
  rebalances an existing gun.

Two parts of that shape are the user's to change: which gun is the top rung,
and whether rungs unlock by tower floor or by the owner's class tier.

**Open question for the user:** are these item shops the same thing as the
gift shop, or a separate kiosk? §3.9 builds a catalogue-driven shop core either
way. The Protector catalogue is its first customer, and gift-shop items can
become a second catalogue in the same kiosk.

---

## 3. Runtime architecture

### 3.1 Modules and who owns what

| Module | Owns | Never does |
|---|---|---|
| `_tod_partner.gsc` | spawn and despawn per owner, owner binding, the state machine (§3.3), follow, warps, death, recharge, the slam entrance, pause follower, actor budget, `[TOD_PARTNER]` log | damage numbers, levels |
| `_tod_partner_combat.gsc` | target choice, script fire through the gun proxy, the fire-mode handlers (§3.7a), the damage NUMBER, kill credit, integrity, zombie aggro, ability handlers | movement |
| `_tod_partner_upgrades.gsc` | the partner level store, the owned and equipped guns, the ONE grant funnel and the equip call, derived stats, the visual reconcile (upgrade parts AND the held gun), the Protector shop catalogue | writing player domain levels |
| `_tod_shop.gsc` | item shops: kiosk placement from generated data, triggers, the shop session (open, focus, buy, close), the freeze policy, catalogue registration | knowing what any item does |
| `_tod_partner_data.gsc` | GENERATED: registry rows as pure accessors, shop positions, `#precache` of every installed stage model (after every `#using`/`#insert`). Eventstrings are precached beside the hand-written module that SENDS them, as every existing eventstring is | anything hand-written |
| `_tod_boss_fx.gsc/.csc` | existing actor FX fields. The partner reuses the ones the Rogue Protector frees (§3.8). One registration changes: `todBossShot` widens from 2 to 4 bits in both VMs, to carry the held gun's flash style (§3.8) | new fields |
| `TodPartnerData.lua` | GENERATED: names, shop text, prices, detail rows, full literal image names for installed art only | |
| `TodShopPanel.lua` | the shop panel (display only, driven by server events) | reading buttons |
| `TodPartnerChip.lua` | the HUD chip | |
| pause menu | a PROTECTOR section listing owned partner upgrades | |

**Dependency rule.** Partner and shop modules may `#using` `_tod_upgrades`
(`menu_freeze`, `set_world_pause`, `station_freeze_wanted`) and `_tod_bosses`
(`drop_in`, `ground_snap`, `landing_kill_splash`). The reverse never happens.
Other modules reach the partner only through guarded level pointers set in the
partner's init (the style of `level.tod_shield_reconcile`):

| Pointer | Called from | Purpose |
|---|---|---|
| `level.tod_partner_hit_dmg` | `upgrade_damage_cb`, between the pause `return 0` and the non-player `return -1` | the damage number |
| `level.tod_partner_owner_kill` | every credit site in the §3.5 table | owner credit (D3) |
| `level.tod_partner_follow` | teleporter ride, ascension, trial and King seals, finale gather and containment, the perk-machine shuffle's `unstick_players` | explicit warps |
| `level.tod_partner_max_all` | ONCE from `king_max_out`, after its player loop (NOT from `king_max_player`, which only ever runs for living players); `dev_grant_maxed` | summit max-out and dev grant. It loops every CONNECTED owner, alive or not, with its own `TOD_SYNC_BURST` yields, because the King's sync burst is the suspected King crash. Levels live on the player entity, so a stowed or recharging partner picks them up at its next ARRIVING reconcile; no latch is needed. |

### 3.2 Identity and the safety contract

A partner is recognised by **one field**, `ai.tod_partner = true`, plus
`ai.tod_owner = <player>` and `owner.tod_partner_ent = <ai>`. Every exclusion
anywhere tests `IS_TRUE( e.tod_partner )`.

**Stamped at spawn, then RE-ASSERTED after `waittillframeend`.** The archetype's
own spawn setup runs as a threaded spawn function, and nothing proves it
finishes before SpawnActor returns. The SPAWN log line reports the re-asserted
values.

- **Damage is script-owned.** `AiUtility::ClearAIOverrideDamageCallbacks`, then
  ONE partner callback. It debits the integrity pool from zombie-team attackers
  only, scaled by armor. It ignores players and other partners, and always
  returns 0, so the engine never kills or gibs the robot. Death is a decision
  the partner code makes (§3.3), never a side effect of damage.
  - One hole remains: stock passes attacker-less damage through RAW, before
    the callback runs. So `allowdeath` stays false except inside the death
    decision.
  - A death watcher routes any unexpected death into DESTROYED, so the
    lifecycle never loses the robot.
- `b_robot_finished = 1` **and** `reviving_a_player = 1`. The first stops the BT
  movement service (follow, revive, powerup chase). The second is the only gate
  on the separate `manage_companion` thread. That thread otherwise runs
  `FindPath` and `pathDistance` to every player every 0.5 s and re-picks a
  leader. The vendored services serve one shared robot: a global leader, a
  revive of ANY downed player, and a global `level.reviving_a_player` that a
  bailed revive never clears. That last one suppresses the all-down game over.
- `allow_zombie_to_target_ai = 1`. This is the stock lane that lets zombies
  DoDamage an AI, and it is how the robot gets hurt (§3.6). Stock ALSO reads
  that flag on an ATTACKER, and treats such an attacker's hits on zombies as a
  player's hits for scoring. So the partner never shoots as itself: every shot
  is credited to its **gun proxy** (§3.5).
- `combatmode = "no_cover"`, an explicit small `goalradius` (the aitype default
  is 2048), `ignore_enemy_count`, `ignore_nuke`, and `tod_boss_custom_speed`
  (exempts the speed curve and `slow_the_crowd`).
- `SetPlayerCollision( 0 )`, required: a robot must never body-block a 160-wide
  stair flight or a teleporter bay.
- `ignoreme = 0` while ACTIVE (the archetype stamps 1). The aggro lane (§3.6)
  needs it. The spike measures whether clearing it also lets the engine's own
  enemy choice send zombies at the robot past `aggro_cap`.
- **Never strip or swap out the robot's ENGINE weapon**, not even to show a
  state or a gun change. The pack's target service
  (`archetype_zod_companion.gsc:205-253`) returns early only while
  `zodcompanionabletoshoot` holds (engine weapon not `none`, right arm not
  gibbed). When it does not hold, the service adds PLAYERS as enemy candidates,
  with no team test. The engine weapon is the pack's
  `ar_standard_upgraded_companion_zm`, and it has **no world model**: it is an
  invisible stand-in the robot has always carried. The gun the player SEES is a
  separate script attachment (§3.7a, §3.8), so changing guns never touches the
  engine weapon.

**Never set on a partner:** `tod_boss_kind`, `is_boss`, `acc_is_boss`,
`acc_is_mini_boss`, `tod_is_sprinter`, `level.ai_robot`, `level.b_robot_leader`.
Each one enrols it in enemy-elite counters, spawn clearance, rewards or the
pack's global game-end overrides.

**Map-wide changes the partner needs, in the same change that adds it:**

| Site | Change |
|---|---|
| `wipe_all_zombies`, `island_sweep` (`_tod_spire.gsc`), `wipe_the_map` (`_tod_finale.gsc`) | an explicit `IS_TRUE( e.tod_partner )` skip. These three Kill() whatever `GetAISpeciesArray( "all" )` returns: at ascension, at every trial seal and the King seal, and in the finale. Whether that one-argument call includes a robot is itself unverified (docs/131 says the species defaults to human), so the skip goes in regardless and the `SPAWN` log records the robot's species. `road_cull_run` and `slow_the_crowd` get the explicit skip too, so no exclusion depends on a side effect. |
| `hoop_probe` (`_tod_corpse_cleanup.gsc`, dev builds) and the spire dev nearest-AI metric | skip partners. The hoop probe DoDamages the living non-elite AI nearest player 0 every 6 s. |
| `zm_zod_robot::zod_robot_player_damage_override` | `return 0` for a partner or gun-proxy attacker. This is safe wherever it sits in the chain, because mechz_spiki's callback returns -1 for non-mechz attackers. |
| `upgrade_damage_cb`, `xmas_fixed_shots_cb`, `wispTeaDamageMonitor` | a partner VICTIM returns -1, so a player's insta-kill or Gift of Death never produces a lethal number, crosshair numbers or procs. The partner's own callback then ignores player attackers. |
| actor budget | `level.zombie_actor_limit = TOD_ACTOR_LIMIT - connected owners`. Every connected player holds one slot whether their robot is active, recharging or stowed, so a slot is always free for the respawn. It is written by a new line in `ai_limit_watch`'s 2 s poll (that poll writes only `zombie_ai_limit` today). `corpse_remove`'s panic test reads the same live value, and `elites_over_roof` subtracts connected owners too, because elites spawn by direct SpawnActor and bypass the stock gate. Retiring the Rogue Protector frees up to 8 standing elites. |
| `_tod_bosses::dev_ai_watch` | a separate "partner" class: logged, not counted as an elite, no per-elite route detail |

### 3.3 Lifecycle: live, die, recharge, slam back in

```
       draft done / owner (re)spawn / recharge complete
 (none) -----------------------------------------------> ARRIVING
                                                         spawn hidden, reconcile upgrade models
                                                         FIRST (the falling proxy copies them),
                                                         drop_in sky trail + SLAM beside the owner
                                                                     |
                  +--------------------------------------------------v--------------+
                  |                            ACTIVE                               |
                  |  follow owner, fire, draw zombie aggro, feed HUD, reconcile     |
                  +---+--------------+----------------+-----------------+-----------+
                      |              |                |                 |
         integrity 0  |       pause  |   owner warp   |  owner dead /   |  owner
                      v       flag   v   or strand    v  spectating     v  disconnects
                  DESTROYED     PAUSED          WARPING           STOWED          DESPAWNED
                  death anim,   (ignoreall,     (ForceTeleport    (no robot;      (Delete; frees
                  sparks,       no fire)        or a visible      re-arrives      the engine slot
                  body deleted                  drop_in)          with the slam   and the reserved
                  after ~3 s                                      on respawn)     slot)
                      |
                      v
                  RECHARGING  -- owner's chip counts down recharge_secs --> ARRIVING

   level end_game (any state) --> END: ignoreall, fire loop and broadcaster stopped, frozen in place
```

**Presence and activity are two variables, not one enum.** Presence is
arriving, present, stowed or gone. Activity is active, paused or low integrity.
A warp applies to any PRESENT robot whatever its activity, and every timer
(recharge, abilities) pauses with the world. A single enum would, for example,
strand a robot whose owner teleports while it is paused.

**ONE arrival owner per player.** A single level thread per owner owns every
ARRIVING:
- It waits by POLLING `level.tod_class_select_done`. That flag is set on both
  of the draft's exits, including the dev mage-test early return, which never
  reaches `_tod_class_select.gsc:176`.
- It ignores `on_spawned` until then. Every player's initial spawn is also an
  `on_spawned` dispatch, and it arrives during the draft.
- It takes its per-owner latch (a spawn serial) synchronously, before any
  yield. The co-op bleed-out double dispatch and the draft-end sweep can then
  never both spawn a robot.
- Each drop is stamped with that serial, not `GetTime()`. Two same-frame
  arrivals would share a GetTime stamp, and `drop_janitor` could not tell
  them apart.

| Event | Hook | Partner action |
|---|---|---|
| match start | the arrival owner sees `level.tod_class_select_done` | ARRIVING for every owner |
| late join | `callback::on_spawned` after the draft, through the arrival owner's latch | ARRIVING |
| owner downed | stock `player_downed` | stays near the owner and keeps fighting |
| owner bled out or spectating | stock `bled_out`, `spawned_spectator` | STOWED: the robot is removed (a recharge in progress keeps its timer) |
| owner respawns | `callback::on_spawned` | ARRIVING with the slam |
| owner disconnects | stock `disconnect`, watched from a LEVEL thread (an endon runs no cleanup) | DESPAWNED, in this order: write the FX state field to 0; notify the partner's kill-event, which every partner loop endons; delete the gun proxy; then `Delete` the actor directly. `corpse_remove` is only for a dead body; it lingers 2 s, and the robot's loops would run on without an owner. |
| game over | `level end_game` (the restart menu holds intermission open for 120 s) | END. Every partner thread carries `level endon( "end_game" )`. |
| perk-machine shuffle | `_tod_perk_scatter.gsc` `unstick_players` (it moves players only) | WARPING for any partner within the unstick radius of a landing pad; the scatter pads are also excluded from follow-point candidates |
| integrity reaches 0 | the partner damage callback | DESTROYED, then RECHARGING |
| teleporter ride | `_tod_teleport.gsc` `do_teleport`, after the rider SetOrigin loop | WARPING to the rider ring |
| spire ascension | `ascend_run`, after the player move and before the wipe | WARPING (a separate navmesh island). A STOWED or RECHARGING partner simply arrives on the spire later. |
| trial and King seals | `trial_run` and `king_run`, between the state flags and the gate Show; add `level notify( "tod_trial_begin", hub )` | WARPING into the sealed box. A partner that ARRIVES while a hall is sealed lands inside the box if its owner is inside. |
| finale gather and containment | `gather_to_centre`, `crown_containment_watch` | WARPING |
| any pause | poll `level.tod_upgrade_pause` every 0.25 s (the finale choice sets the flag directly, so hooking `set_world_pause` would miss it); a RECHARGING timer does not count down while paused | PAUSED |
| owner "jumped" | an explicit teleport STAMP changed (`level.tod_tp_stamp` for pads, plus a new per-player `tod_blink_ms` stamp written by `cast_blink`), or no path to the owner for N s | WARPING. A single distance-per-tick threshold is NOT used: a Mage with 2-3 stored Blink charges moves 960+ u inside one 0.25 s tick, which would fire a false warp. |

**Why death is safe for the engine pool.** A dead actor keeps its engine slot
until it is deleted, and a SpawnActor into a full pool fails. So: the body is
deleted through `corpse_remove` about 3 s after the death animation; the slot
stays reserved for the whole recharge (the actor-budget row in §3.2); and a
failed respawn retries with backoff and a `SPAWN_FAIL` log.

**The death itself.** The partner code sets `allowdeath`, plays one of the
pack's robot death animations, and fires a sparks burst through a clientfield.
No reward or death callback routes it. Never the pack's
`cin_zod_robot_companion_exit_death` scene: the matching entrance scene spawned
a duplicate robot in map 1.

**The slam.** Every ARRIVING, including the first one and each respawn, plays
the shared `drop_in`: the sky trail, the landing FX and a quake.

- The kill ring is a NEW `partner_slam( org, radius, proxy )`. The shared
  `landing_kill_splash` stays untouched: it hard-codes 350 u, and it deals its
  damage with no attacker. It is also used by every elite entrance, so changing
  its arity would touch all of them.
- `partner_slam` kills trash within the slam radius and skips elites
  (`landing_splash_immune`). It marks each victim so the partner damage branch
  passes a LETHAL amount through, instead of one volley's damage. It
  ragdolls only victims that are actually dead. The attacker is the gun proxy,
  so the owner gets the kill credit.
- `drop_in` gains ONE partner flag, honoured in both `drop_in` and
  `drop_janitor`. The flag:
  - skips their forced `SetCanDamage(true)`;
  - skips their ignoreall and anim-rate restores, and their `Show`;
  - skips the global rumble;
  - hands state back to the partner state machine.
- A visible catch-up warp uses `b_relocate`, which already skips the splash and
  rumble. Warps at a seal or the ascension use a plain ForceTeleport: each
  drop costs 3 entities for about 2 s, and four partners dropping beside the
  Wardens would press the spire's ~1024-entity table.
- The falling proxy copies attachments at the START of the drop. A purchase
  that lands mid-fall pops in on reveal, which is cosmetic only.

**Client FX lifetime.** The server writes the FX state field to 0 before any
Ghost, Hide, drop_in or Delete. The `.csc` state callback also threads a
cleanup on `death` / `entityshutdown` (the `chain_fx_cleanup` shape in
`_tod_mage_elements.csc`). The field is registered
`!CF_CALLBACK_ZERO_ON_NEW_ENT`, so no zero callback ever arrives on its own,
and a looping FX would otherwise keep playing where the robot used to be.

### 3.4 Movement and warps

- **Follow.** Re-goal only when the owner has moved meaningfully or the goal is
  stale; each SetGoal fires a level `update_nav_triggers` notify. Stagger the
  four partners' 0.25 s ticks. The follow point comes from
  `positionQuery_Source_Navigation` around the owner, **constrained to
  |dz| < 64 and preferring points behind the owner along the stair.** Flights
  are 192 u apart, so an unconstrained query lands on the flight above or below
  and the robot walks a whole lap. Feed `v_robot_land_position = owner.origin`
  so the BT's own walk/sprint chooser works.
- **Warp** = `GetClosestPointOnNavMesh` near the destination, then
  `ForceTeleport`, then `ground_snap`. A visible catch-up uses `drop_in` with
  `b_relocate` and the partner flag.

### 3.5 Combat

- **The gun proxy.** Each partner owns one `script_origin` linked to
  `tag_weapon_right`, with `tod_partner_gun = true` and `owner = <partner>`
  (the stock Fire Works AAT pattern: MagicBullet credited to a spawned entity
  with an owner). Every shot is `MagicBullet( carrier, muzzle, aim, gun )`.
  The **carrier** is the robot's own engine weapon OBJECT (`self.weapon`): map
  1 learned that `GetWeapon` on the AI-only companion AR's name returns `none`
  and MagicBullet with `none` throws (`_tod_bosses.gsc:2988-2995`). A gun row
  may name a different carrier (§3.7a). The **muzzle** is the held gun's
  `tag_flash`, falling back to `tag_weapon_right` plus the gun's registry
  muzzle offset. The fire-mode handler of the held gun decides the cadence,
  pellets and spread.
  This keeps stock's "AI attacker with allow_zombie_to_target_ai scores like a
  player" lane from ever seeing the partner, and it gives the damage branch an
  unambiguous key. If the allied archetype also fires natively (nobody has
  measured that), those bullets carry the partner itself as the attacker. The
  damage branch returns 0 for them and logs `NATIVE_FIRE`. The proxy costs one
  entity per partner and is deleted with its partner.
- **Gates:** range, a world-only sight trace, a z-delta, and **a second trace
  with characters on that rejects the shot if a player or another partner is
  in the line.** Sight traces are bounded to the nearest few candidates per
  tick.
- **Target priority:** zombies attacking the robot or its owner, then the
  owner's current target, then the nearest. An elite is fired on only if the
  owner has damaged it in the last few seconds; this stops kill-stealing.
- **The damage NUMBER** (`level.tod_partner_hit_dmg`, keyed on
  `attacker.tod_partner_gun`) is REAL damage that follows the owner's gun
  power (revision 3.3; it was a fraction of `victim.maxhealth` before):

  `dmg_per_volley = owner_index × HP_REF / trash_volleys`, per victim, then
  × the gun's `elite_mult` and `budgets.elite_damage_mult` against elites and
  bosses.

  - `owner_index` is the owner's paper gun power relative to their class's
    tier-1 gun: `TIER_DPS[ tier ]` × pack × DAMAGE card × extra packs (for the
    Mage, `TOD_MAGE_TIERn_MULT / TIER1`). The owner's tier appears ONLY here,
    so nothing is scaled twice. It is an estimate from the owner's upgrades,
    not measured skill, so it is logged (`SCALE`, §3.11).
  - `HP_REF` is the stock trash health at the registry's `ref_round`
    (placeholder 5), solo, no rampage.
  - `trash_volleys` is how many volleys kill one `HP_REF` zombie for an owner at
    `owner_index` 1. It is a reference, not a fixed count: the robot kills
    faster in early rounds and slower in late ones, in step with its owner.

  **Why real damage.** The robot and its owner now fight the SAME health, so
  every health multiplier applies to both alike: round growth (135 +90 per
  round, compounding from round 10, `_tod_endless_rounds.gsc:263`), party size
  and rampage (`_tod_zombie_speed.gsc` `health_mult()`, 1.20 to 1.50 and ×1.20),
  trial HP and the elites' compounding `boss_hp` curve
  (`_tod_bosses.gsc:2072-2074`). The robot-to-owner kill ratio is set only by
  the robot's rung and ARMAMENT, and by the owner's class, at every round,
  party size and mode, against trash and elites alike. The maxhealth-fraction
  model it replaces kept the robot's kill time CONSTANT while its owner's grew,
  so it needed a separate correction per axis, and the review of 3.3's first
  draft found three axes (party size, rampage, elites) that correction missed.

  | Victim | Damage |
  |---|---|
  | trash | `dmg_per_volley` |
  | armored sprinter | the same; the sprinter's armour applies (the TRAILBLAZER precedent); fire stays the anti-armour answer |
  | elite (reaver, hound, Fury) | `dmg_per_volley × elite_mult × elite_damage_mult` |
  | Panzer / Warden | the same, plus a same-frame passthrough in `tod_mechz_damage_calc` so stock armour does not rescale it |
  | Warden King | the exception, in TIME units: damage per volley = `maxhealth × ( cycle_eff / KING_REF_CYCLE ) / ( TOD_PARTNER_KING_SEGMENTS × connected owners )`. The partners' share of his fight takes the same time whatever gun, ARMAMENT level or party size, and does not depend on the round the party arrives. Without the cycle term, the slow-firing shotgun would be the worst gun against him. |

  Damage is dealt per **volley**, not per pellet: a victim takes at most one
  volley's damage per volley, however many pellets land on it, so a shotgun
  cannot multiply its damage by its pellet count. The number shown is summed
  per victim per volley (the Mage crowd-sum precedent). A pellet gun's edge is
  that one volley hits several zombies; its power counts `ref_victims`, the
  average number of zombies one volley hits. Its `elite_mult` covers a lone
  target, where that crowd edge does not exist. `gen_partner.js` checks every
  gun's trash AND elite power against its rung (§5.1).

  **Rounding.** A gun with few volleys per kill loses more power when a
  zombie's health just passes a multiple of its damage (a 1-volley gun at 1.01
  times the health needs 2 volleys, half its power). So `budgets.min_trash_volleys`
  (2) is a refusal, and the fire-mode test sweeps health continuously and
  checks that the rung order never inverts (§5.6).

  No attacker multipliers apply. During the upgrade pause the branch returns 0.
  During insta-kill, partner hits kill trash (decided explicitly and logged).
  The result is clamped to avoid int overflow at deep rounds.
- **Kill credit (D3).** A partner kill should pay its owner the same way a
  player's own kill does, minus the player-only procs. Today every site below
  bails on (or mis-credits) a non-player killer:

  | Site | Today | The owner gets | The owner does NOT get |
  |---|---|---|---|
  | Panzer / Warden / King last-hit ledger (`tod_mechz_damage_calc`, `_tod_bosses.gsc:2334`) | records PLAYER attackers only. After a partner last hit, the "killer" is whichever player hit last, often a teammate. | the ledger remaps the gun proxy to its owner, so the Panzer's luck jackpot and kill confirm go to the right player | |
  | `tod_luck::boss_kill` (reaver, hound and sprinter death watches pass the raw attacker) | bails on non-player | the elite luck jackpot, kill confirm | |
  | `tod_luck::on_zombie_death` | bails on non-player | fair-share luck credit (no headshot bonus) | |
  | `on_class_gun_kill` (trash mana, BOUNTY, SCAVENGER) | bails on non-player | Mage mana (by calling the mana function with the owner) | BOUNTY, SCAVENGER, LEECH, ADRENALINE |
  | stock `zombie_death_points` (the powerup drop roll sits after its player test) | returns before the drop roll | a drop roll: the partner's own zombie-death callback calls `zombie_can_drop_powerups` and `powerup_drop` itself | |
  | `grant_elite_reward` | bails on non-player | NOT called with the owner. It pays 100% at once, multiplies by BOUNTY and fires the shield cut, Attunement, elite mana and the bottle roll. It gets a `partner` flag that pays the banked 50% only. | the procs |
  | `grant_boss_reward` (the boss-round Panzer's team-wide 1000) | team-wide; takes no killer and never bails | unchanged | |
  | points | stock pays only players | 50%, banked quietly, one popup every couple of seconds | the per-hit 10 |
- **Presentation.** The muzzle flash comes through `tod_boss_fx::shot_pulse`,
  which now carries the held gun's **flash style** (§3.8), so a shotgun flashes
  like a shotgun. The **shot sound** is the held gun's own alias, played by the
  gun proxy with `PlaySound` (a spawned `script_origin` playing a 3D alias is
  this map's proven lane), so a new gun's sound costs no client bits. Each gun
  alias is voice-limited and attenuated for robots that are not yours. The
  Rogue Protector fired every 4.5 s; a companion fires about ten times as
  often, and there are four of them.

### 3.6 Durability: how it gets hurt (D2)

- **Integrity** `tod_ptn_hp` is a script pool, with its maximum from stats
  (ARMOR raises it).
- **Zombies really attack it (lane A, the engine lane).** Stock's
  `level.closest_player_targets_override` supplies the candidate list every
  zombie's target pick uses. The map's `tod_closest_player` then picks the
  nearest.
  - **Who gets offered the robot.** The override returns the players plus each
    ACTIVE partner, but offers a partner only to zombies within `aggro_radius`
    of it, and only while fewer than `aggro_cap` zombies already target it. The
    cap is a per-partner counter, updated on assign, retarget and zombie death.
    It is never a scan of all zombies: the override runs on every zombie's
    find-flesh tick, so a scan would be O(n²) per tick.
  - **Two stock prerequisites.** First, the partner keeps `ignoreme = 0`.
    Second, it maintains its own `last_valid_position` every tick, using the
    `player_shared` recipe (`GetClosestPointOnNavMesh`). A zombie only re-goals
    toward a `favoriteenemy` whose `last_valid_position` is defined, and stock
    maintains that field for players only. Without it, a zombie that picked
    the robot would just stand there.
  - **How the damage lands.** Stock zombie melee DoDamages the robot through
    `allow_zombie_to_target_ai`, and the partner callback debits integrity,
    reduced by `armor`.
  - The `AGGRO` log records `zombie.enemy == partner`.
  - The caps keep the robot a partner, not a lightning rod that empties the
    players' side of the fight. The TAUNT upgrade raises both caps.
- **Lane B (fallback, if lane A misbehaves in the spike):** a scripted aggro
  director steers up to `aggro_cap` nearby zombies onto the robot, and debits
  integrity when one is within melee range on its attack beat.
- Elite splash and other zombie-team damage reach the same callback and are
  debited the same way.
- **At 0: DESTROYED, then RECHARGING** (§3.3). The owner's chip counts down
  `recharge_secs`, which the REACTOR upgrade shortens, and the robot slams back in.
- The Mage's HEALING AURA restores partner integrity (a synergy, not a new card).

### 3.7 Upgrades: data model

A partner upgrade is a registry row with a level ladder and a **price per
level**. Each purchase is +1 level. Levels are stored per owner in
`owner.tod_ptn[key]`, never in `tod_levels`:
- The store is initialised at CONNECT, so no reader ever sees it undefined.
- Levels survive class change, tier promotion, the partner's own deaths and the
  owner's deaths by construction. A disconnect clears them.
- A grant landing while the robot is recharging or stowed is simply stored.
  The next ARRIVING reconcile shows it. The funnel never assumes a live robot.

**Every write goes through ONE funnel**, `tod_partner_upgrades::grant( owner,
key, levels, source )`: a shop purchase, the King max-out, the dev grant, and a
future gift-shop or reward source. The funnel clamps, recomputes the derived
stats, runs the visual reconcile, syncs the HUD and logs. That closes the bug
class the riot shield header documents, where three writers skipped the apply
path.

**Effect kinds** decide whether an upgrade needs code:

| Kind | Needs code? | Meaning |
|---|---|---|
| `stat` | no, data only | per-level values for fixed channels the partner code already reads: `max_hp`, `armor`, `interval_pct`, `range_pct`, `move_rate`, `recharge_secs`, `slam_radius`, `aggro_radius`, `aggro_cap`. `interval_pct` scales the HELD gun's interval AND reload time; it is ARMAMENT's only channel, so one ARMAMENT ladder works on every gun (§3.7a). `range_pct` scales the held gun's range; no upgrade in the first catalogue uses it, and any upgrade that does must be added to the power check, because range is outside the power formula. There is no damage or volleys channel: gun power comes only from the rung and the firing cycle. |
| `ability` | once per ability | one handler in `_tod_partner_combat.gsc`, registered by name; the registry supplies per-level parameters |

`partner_stats( owner )` is the ONE derivation, cached at every grant.

**Proposed first catalogue** (placeholder names, prices and numbers). Each
upgrade owns a distinct slot, and every level shows a change (a new or bigger
stage model per level):

| Upgrade | Kind | Function | Slot, and what grows each level |
|---|---|---|---|
| ARMOR | stat | integrity +, armor + | torso shell: chest plate, then shoulder pauldrons, back plate, heavier shell, glowing trim |
| ARMAMENT | stat | faster fire and reload for WHICHEVER gun is held: each level multiplies the firing cycle by `1.5625^(-1/5)` (0.914610; stored as the expression, not a rounded decimal), so level 5 is exactly one rung step, ×1.5625 (the PaP rule, `gen_tod_twins.js:486-491`). It carries across guns. | right forearm and shoulder, never the gun itself: a gauntlet, an ammo feed, forearm heat sinks, a shoulder capacitor, a glowing power coil. The parts sit on the arm so they fit every gun (§3.7a). |
| REACTOR | stat | faster recharge, bigger slam radius | back pack: a reactor core that grows and glows brighter |
| TAUNT | stat | more zombies may target it, from further away (a decoy for its owner) | left arm: a beacon that grows and gains lamps |
| SALVAGE | ability | partner kills sometimes drop an ammo or points mote | hips: collector pods |
| OVERWATCH | ability | marks the elite you are shooting, and partners focus it | helmet: visor, then a sensor array, then a crest |

### 3.7a The weapon slot: the robot holds different guns

The user's requirement (2026-09-23): the robot can be upgraded to hold an AR,
an SMG, a shotgun, and more later. The guns are **a ladder of rungs in one
exclusive slot** (D12): the robot holds exactly one gun at a time, each rung
is stronger than the one below, and the player chooses which owned gun to hold.

**What the files say about the robot today** (measured 2026-09-23):
- The pack's engine weapon, `ar_standard_upgraded_companion_zm`, has no world
  model (its GDT row sets only a view model, `vm_t9_ak47`).
- The robot body has no gun geometry. Its right hand is a normal hand with
  fingers, and `tag_weapon_right` hangs off `j_wrist_ri` with no geometry.
- The robot is human scale: its bind pose is 73.7 units tall.

So there is no built-in gun to cut away. A held gun is a plain rigid model
attached at `tag_weapon_right`, the way every BO3 soldier holds a weapon. And
because the robot is human scale, any existing player gun's world model fits
its hand at 1:1, which gives every new gun a **placeholder model on day one**.

**Data.** A registry `weapons` table, separate from `upgrades` (§5.1). Each row:

| Field | Meaning |
|---|---|
| `key`, `index`, `name`, `shop_text` | as for upgrades; `index` is append-only |
| `rung` | its place on the ladder (1 = the starting AR). Separate from `index`, so a gun added later can join any rung without renumbering anything |
| `price` | one price; 0 for the starting AR (D13). Never below the highest price on the rung beneath |
| `ref_victims` | optional; the average number of zombies one volley hits, used only to measure power. Defaults per mode (1.0 for `auto` and `burst`, 1.5 for `pellets`); overriding it needs a `why`. Real play replaces the guess: `VOLLEY victims=` logs the measured average |
| `mode` | the fire-mode handler: `auto`, `burst` or `pellets` to start |
| `profile` | the mode's numbers: `interval`, `burst`, `pellets`, `spread`, `range`, `falloff_start`, `trash_volleys` (volleys to kill one `HP_REF` zombie for an owner at `owner_index` 1; it sets the damage per volley, §3.5; at least `min_trash_volleys`), `elite_mult` (damage multiplier against elites and bosses, default 1.0; how a pellet gun keeps its rung on a lone target), `reload_every`, `reload_secs` |
| `model` | the robot gun model (`cc_ptn_gun_<key>`), installed through the same model pipeline as stage models |
| `placeholder_model` | an ALREADY-ZONED world model shown until `model` is installed (for example the map's own SMG or shotgun world model) |
| `muzzle` | `tag_flash` if the model has one, else an offset from `tag_weapon_right` |
| `flash_style` | 0..3, an index into the four muzzle-flash styles the client knows (§3.8) |
| `sound` | the shot alias, played by the gun proxy |
| `carrier` | optional. A weapon already in the zone, used for MagicBullet's tracer, impacts and gib behaviour (a shotgun carrier gibs like a shotgun). Absent means the robot's own engine weapon. The carrier never decides damage; the partner damage branch does (§3.5). |

**The ladder table.** A top-level registry `ladder` lists every rung with its
power and its gate:

| Rung | Power (trash) | Gate |
|---|---|---|
| 1 | 1.0 | none (owned at connect) |
| 2 | 1.5625 | `{ "floor": 10 }` and rung 1 owned |
| 3 | 2.4414 | `{ "floor": 30 }` and rung 2 owned |
| 4+ | written explicitly, never computed by a formula | `{ "trial": <n> }`: the tower has only 50 floors (`tier_floor_req( 4 )` would ask for 60), so higher rungs gate on a won spire trial. The `trial` gate kind does not exist until the first rung 4 is added (below). |

- **Power** is sustained trash killing, measured the same way for every mode:
  `ref_victims / ( trash_volleys × ( interval + reload_secs / reload_every ) )`,
  divided by the AR's figure. Elite power is the same with one victim, times
  `elite_mult`. Rung powers are exact (`1.5625^(rung-1)`), and every power
  comparison allows a 1e-4 relative rounding tolerance on top of
  `rung_tolerance`.
- **Gates are data** (`{ "floor": 10 }`), each kind read by one named handler
  (`floor` reads `tod_gauge::floor_reached`, the per-player high-water mark the
  class tiers use). The generator refuses a gate kind with no handler, and
  refuses rung 2 or 3 floors that differ from `TOD_TIER2_FLOOR` /
  `TOD_TIER3_FLOOR` (`_tod_upgrades.gsc:730-731`), so the two ladders cannot
  drift apart. Phase 1 ships the `floor` kind only. A new gate KIND is code,
  written once: the handler, its locked shop state (for `trial`,
  `locked_trial`, drawn "TRIAL IV"), its refusal reason and its `RUNG_UNLOCK`
  field. Every later rung using that kind is data again.
- **A rung unlocking is announced once** with a free `IPrintLnBold` toast, the
  `tier_gate_toasts` pattern (`_tod_upgrades.gsc:5585`).

**Store.** `owner.tod_ptn_guns[key]` (owned) and `owner.tod_ptn_gun` (held),
initialised at CONNECT with the AR owned and held. Like levels, they survive
the partner's deaths, the owner's deaths, class changes and promotions, and a
disconnect clears them.

**Writes.** Buying a gun goes through the same funnel,
`grant( owner, "gun_<key>", 1, source )`: it checks the rung's gate, marks the
gun owned and equips it. Re-equipping an owned gun is
`equip( owner, key, source )` in the same module. Both recompute stats, run the
reconcile, sync the HUD and log. The King max-out and the dev grant own every
gun and equip the top rung, unless a top-rung gun is already held.

**Behaviour: fire modes are code, guns are data.** `_tod_partner_combat.gsc`
registers a small set of fire-mode handlers by name. `auto` covers the AR, SMG
and LMG; `burst` covers burst rifles; `pellets` covers shotguns (N pellets in a
cone, one volley). A gun that fits an existing mode is **only a registry row
plus a model**. A genuinely new behaviour, such as a projectile launcher, a
beam or an energy cannon, is one new handler plus a test case, written once;
every later gun of that kind is data again.

**How it composes with the upgrades.**
- ARMAMENT improves the held gun: it shortens that gun's own firing cycle
  (interval and reload) by a percentage, so it works on any gun. Its maximum
  is one rung step, so the top rung at full ARMAMENT is
  1.5625² × 1.5625 = 1.5625³, about 3.8147 (`budgets.power_max`), and buying the next rung
  always matters. Between floor gates, ARMAMENT is where points go.
- ARMAMENT's parts sit on the arm, not the gun (§3.7 table). Gun-mounted parts
  would need every ARMAMENT stage remade for every gun, which is guns times
  stages models; arm-mounted parts are guns plus stages.
- `fit_check` checks every installed gun against every ARMAMENT stage.

**What a gun change looks like.** At the kiosk, the reconcile Detaches the old
gun and Attaches the new one immediately. The robot does not need to be
present: a gun bought while the robot is recharging is shown when it slams
back in.

### 3.8 Visuals

**The blue body is a GDT twin plus generated LODs.** In `source_data/cc_partner.gdt`:

- The xmodel `cc_partner_body` reuses the pack's gold robot geometry, with a
  skinOverride that maps the four gold materials, plus the lights material, to
  cloned `mtl_cc_partner_*`. The gold look is only `specColorTint 0.988 0.779
  0.349` on `lit_advanced` over a black colour map, so blue is the same
  material with a blue tint. The arm override is dropped (D8). Two base
  materials are absent from gdtdb (`lights`, `chassis_torso`), so the twin
  keeps the pack's overrides for those pairs.
- The pack body has ONE LOD at 47,574 triangles, and four robots stay near the
  camera all match. The cyber-roster reducer generates LODs 1..6 for the twin,
  so the twin has binaries, not only GDT rows.
- Four light-material twins, one per party colour, are chosen at SPAWN (D7).
  No SetModel runs after parts are attached.
- A character `cc_partner` and an aitype chain `archetype_/variant_/spawner_cc_partner`,
  written from the donor snapshot of `spawner_ally_zod_robot_companion_gold_ar`
  (already team allies) with only `character1` changed. The zone lists the
  `spawner_` form, because SpawnActor resolves through it.

**Upgrade visuals are ONE model per upgrade STAGE, attached at runtime.**

- Each stage of an upgrade is one skinned model (for example `cc_ptn_armor_s3`),
  baked to one atlas per upgrade. The reconcile swaps at most one model per
  owned upgrade, so a robot carries at most as many attachments as the upgrades
  it owns (6 in the first catalogue), plus its one held gun.
- **The held gun is Lane B**, a rigid model attached with
  `Attach( model, "tag_weapon_right" )`, because a gun does not bend. Every gun
  is authored in ONE grip frame: the pistol grip at the origin of
  `tag_weapon_right`, a `tag_flash` joint at the muzzle, and the foregrip where
  the robot's rifle animations put its LEFT hand. That point is measured once
  from the xanims (a spike row, §8), recorded in the registry, and checked by
  `fit_check` for every gun, so a long gun never leaves the left hand floating
  and a short one never swallows it. Pistols are out of scope: the robot's
  animation set is a rifle set (`primaryWeaponType rifle`).
- **Lane A (preferred): a skinned attachment by bone name.** The stage model
  carries the anchor bones it uses, each with the robot's EXACT bind offset and
  matrix copied from the robot binary (the stock helmet stores J_Head at its
  world bind, z 64.53, not at the origin). Its GDT type is `animated`, and it is
  attached with `Attach( model, "" )`. `verify` asserts each bone's transform
  against the robot's. Lane B (the fallback) is a rigid bone-local model with
  `Attach( model, tag )`.
- Anchor bones (geometry-free leaves of the 186-bone rig): `j_helmet`,
  `j_spine4_dam`, `j_chest_door_dam`, `j_shoulder_le/ri_rot_dam`,
  `j_inner_shoulder_pack_le/ri_trans_dam`, `j_hip_*_dam`, `j_knee_*_dam`,
  `tag_jets_*`, `tag_weapon_right`.
- **The reconcile** runs on every grant and equip, on every ARRIVING (BEFORE
  the drop, so the falling proxy copies the attachments) and on a slow maintain
  loop. It Detaches what should not be there, Attaches what is missing, never
  stacks duplicates, and only attaches INSTALLED models, so an upgrade can ship
  working before its model exists. For the gun, "installed" falls back to the
  row's `placeholder_model`, so the robot always holds something.
- **FX without new bits:** retiring the Rogue Protector frees `todBossShot`
  (partner muzzle), `todBossZap` (a pulse: ability proc, death sparks) and
  `todBossMahem`. `todBossMahem` becomes a **state** field (0 normal, 1 low
  integrity, 2 taunting). Its `.csc` callback is rewritten to honour the initial
  snapshot and to KillFX on change, so late joiners see the right state.
- **One field widens, for the flash style.** `todBossShot` goes from 2 to 4
  bits in both VMs: the low 2 bits stay the shot counter
  (`_tod_boss_fx::pulse`, which wraps modulo 4 so every shot changes the
  value), and the high 2 bits carry the held gun's `flash_style` (0..3: rifle,
  SMG, shotgun, energy). The client picks the flash FX from the style and plays
  it on `tag_flash`, falling back to `tag_weapon_right`. This +2 bits is the
  only new actor-field cost of the feature. A fifth flash style costs one more
  bit in both VMs; guns SHARE styles, and shot sounds need no bits at all
  (§3.5).
- An optional "PROTECTOR" label rides `todBossName` values 3..7 (the Panzer
  keeps value 2).

### 3.9 The item shops (D1)

**A catalogue-driven shop core, `_tod_shop.gsc`.** Kiosks come from generated
data. Each catalogue registers a provider: a list of items, each item's
current level, next price and availability for a given player, and a buy
callback. The Protector catalogue (in `_tod_partner_upgrades.gsc`) is the first
provider. Its buy callback is the grant funnel. Gift-shop items can become a
second provider later without touching the core.

- **Placement (D11)** follows the generator's furniture grammar. Each kiosk is a
  new furniture kind in `tools/gen_tower_map.js`, placed like crates and
  stations: one origin and yaw, a derived trigger in front
  (`CRATE_TRIG_OUT`-style), and the existing trigger-gap asserts. The kiosks
  ride into GENERATED data. The kiosk model is a Blender MCP asset of its own;
  an existing prop stands in until then.
- **Prompt.** One constant hint string led by a new `TOD_NOUNS` noun (for
  example "PROTECTOR SHOP"), with a prompt-card icon. Prices never go into the
  hint (the triggerstring rule). This costs one or two of the 95 free strings
  of the 190-string budget.
- **The panel is display-only, and the server reads the buttons.** In this map
  (and in stock and map 1) an `OpenLUIMenu` menu is display-only: a HUD-layer
  menu is not on the focused menu stack, so it never receives button callbacks.
  The shop session therefore reuses the card panel's proven server-side input
  loop:
  - tactical and lethal move the focus;
  - hold USE buys;
  - jump, or walking away, closes.
  The panel advertises one lane per action, and the key names come from engine
  bind tokens, never literals.
  The server pushes the panel state with int-only eventstrings (open/close,
  focus index, the player's points bucket, and a purchase result). Item names,
  text, prices and art come from `TodPartnerData.lua`. Owned levels come from
  `tod_ptn_sync( idx, lvl, max )`.
- **Guns in the shop.** The provider API gives every item a STATE as well as a
  level and price: `buy`, `maxed`, or `locked` for upgrades, and five states
  for guns: `held`, `equip` (owned, free), `buy` (with its price),
  `locked_floor` ("FLOOR 30") and `locked_prev` ("NEEDS SMG"). The panel draws
  the state from an int code; the floor number and gun names come from
  `TodPartnerData.lua`, so no name or price ever travels as text. The rung
  numeral is drawn by the panel, never baked into tile art. Hold USE on an
  owned gun re-equips it for nothing (D13). Guns are a separate section below
  the upgrades in the same panel, ordered by rung and then `index`, so the
  focus keys walk through both without a tab switch. The shop opens focused on
  the next rung the player can buy.
- **Freeze (D10):** `station_freeze_wanted()`, so solo freezes the world and the
  buyer through the same `set_world_pause` / `menu_freeze` pair, and co-op does
  not. The shop claims pause ownership the way a station does
  (`level.tod_station_pause_owner`).
- **Round-event takeover CLOSES the shop.** A round event arriving while a shop
  is open closes the session, and the player re-opens it afterwards. The shop
  does not copy the station's defer-and-re-present machinery, and a purchase is
  atomic per buy, so nothing is ever lost. That deliberately avoids the
  station's known trap: a deferred pick that waits on `tod_upg_event_over` can
  sleep until the NEXT event.
- **Purchase:** validated on the server BEFORE any points move: points, the
  item's provider state (an upgrade below its cap; a gun in state `buy`, which
  means its rung gate is met and the rung below is owned), proximity, not
  paused by someone else. Then `zm_score` minus the price, then the grant
  funnel. The funnel's own gate check is a second guard; if it ever refuses
  after the charge, the price is refunded in the same frame and logged
  `REFUND`. A refusal is audible and logged. The shop never interpolates a
  number into a hint.
- **Down or death while shopping** closes the session through the same
  release path `menu_freeze` uses.

### 3.10 HUD and pause

- **Chip** (`TodPartnerChip.lua`, its own zoned module, closes its own
  elements):
  - an integrity bar;
  - a state icon: active, taunting, destroyed, or **RECHARGING with seconds**;
  - the held gun's glyph (from its shop tile; its name in the map typeface
    until the tile is installed) with its rung numeral. The gun index rides
    the snapshot int beside the state, and the rung is looked up from the
    index in `TodPartnerData.lua`, so it costs no bits. (Revision 3.2 listed
    "rank pips" here; no rank was ever defined, and the rung replaces it.)
  It sits in the confirmed free 53-unit gap above the local player row
  (y 575..612, x 90..220), so it inherits the left-HUD scale anchor.
- **Teammates:** a small state glyph beside each party row's name. There is no
  room for a bar under a party row's health track.
- **Feed:** a four-player snapshot broadcaster (the `arch_bar_watch` pattern).
  Integrity is packed two slots per int, and state plus held gun two per int.
  It is change-gated, with a 2 s hydrate and a re-arm on respawn.
  A 1 Hz recharge countdown is modelled on `tod_tp_recharge`.
  All ints stay under 2^24.
- `AetheriumPlayerInfo.lua` gains no statements (it is at its closure ceiling).
- **Pause menu:** a PROTECTOR section listing each owned partner upgrade with
  its level and live value.
- Copy uses the map typeface's 42 glyphs only (for example "RECHARGE 12").

### 3.11 Diagnostics

`[TOD_PARTNER]` and `[TOD_SHOP]` use the CLAUDE.md dev_log pattern, gated on
`level.tod_dev`. Every line carries the owner entnum, a partner lifetime id
(entity slots are reused) and the game time.

- **Spawn:** `SPAWN` (with the re-asserted stamps), `SPAWN_FAIL` (pool count).
- **Movement and state:** `STATE old->new reason`, `WARP site from to`,
  `PAUSE on/off`, `DEATH cause`, `RECHARGE secs`, `SLAM kills=`.
- **Upgrades:** `GRANT key +lv source`, `RECONCILE want= have= attach_size=`,
  `STAGE_ON/OFF model`, `EQUIP gun from->to source placeholder=0|1`,
  `RUNG_UNLOCK rung floor`.
- **Scaling:** `SCALE owner idx= tier= pack= dmg_card= gun= arm= dmg_per_volley=
  cycle=`, logged when any input changes. This is where a wrong `owner_index`
  estimate shows.
- **Combat:** `HIT victim tier dmg gun`, `VOLLEY gun mode pellets hits
  victims`, `CARRIER gun weapon` (once per gun, and a `CARRIER_FALLBACK` if a
  named carrier resolves to `none`), `NATIVE_FIRE`, `SHOT_BLOCKED friendly`,
  `DRAIN attacker amt hp`, `AGGRO targeting=`.
- **Credit:** `KILL credit luck= mana= pts_banked=`.
- **Shop:** `[TOD_SHOP] OPEN / FOCUS / BUY ok|refused reason / CLOSE`, where a
  gun refusal's reason is `points`, `floor` or `prev`.
- **Per round:** `ROUND_SUMMARY owner_kills= partner_kills= deaths= pts_spent_shop= gun= rung= arm= class= elite_share=`,
  where `elite_share` is the partner's share of all damage its owner and it
  dealt to elites and bosses that round. With these on the summary, the rung
  step and the kill share are measured from real play, not assumed.
- **The kill-share target (placeholder).** The partner's share of the kills it
  and its owner make together: about `share_start` (8%) with the AR at
  ARMAMENT 0, rising with rung and ARMAMENT to at most `share_max` (25%) at the
  top rung with full ARMAMENT. The two are linked: the top is 3.8147 times the
  start's robot-to-owner ratio, so a 25% ceiling puts the start at 8%. Because
  damage follows the owner's gun (§3.5), the share does not drift with round,
  party size, rampage or the owner's tier; it varies with the owner's CLASS,
  which the test and the summary both report. (Revision 3.2 said "15-25% at
  equal investment", which a single ceiling across the whole ladder could not
  deliver for the starting robot.)

---

## 4. Retiring the Rogue Protector

### 4.1 Order (dependency-safe)

There are seven unguarded reads of `level.tod_protector_debt`:
`_tod_bosses.gsc:1503, 1591, 1623, 1707, 1767` and `_tod_spire.gsc:2240, 2789`.
There is also a write in `king_run` (`_tod_spire.gsc:1945`). Steps 1 and 3 ship
in one build.

1. **Retarget every debt writer** per §4.2: trial recipes and `trial_adds`,
   King summons, the `king_run` write, finale arm 1, `finale_pressure_start`
   and the flare beat. In the same change:
   - update `tools/test_king_rampage.js` (build-gated) and the armory page (its
     Gate C names `TOD_PROTECTOR_HP_BASE/_EXP`);
   - delete the ungated `test_protector_damage_feed.js`;
   - fix `test_v1896_secret_killconfirm_bottle.js:89`.
2. **Remove `protectors_alive()`** from every elite sum
   (`_tod_bosses.gsc:901, 1688, 1703, 1748`, `_tod_hellhounds.gsc:341`).
3. **Delete the RP-only code in `_tod_bosses.gsc`**:
   - functions: spawn_protector, hunt_players, fire_loop (copied into the
     partner first), zap_loop, death_watch, rp_damage_feed, rp_knockback,
     protector_due, rp_max_alive, protectors_alive, finale_beat_protectors;
   - the director and round_watch branches, and the debt init;
   - the `acc_is_rogue_protector` lanes;
   - the `TOD_RP_*`, `TOD_PROTECTOR_*` and `TOD_XMAS_RP_SHOTS` defines.
4. **Zone:** drop `archetype_acc_zod_robot_boss` / `spawner_acc_zod_robot_boss`
   and the dead `tod_bosses.csv` rows.
5. **Leftovers:**
   - rename `TOD_LUCK_PROTECTOR` to a neutral catch-all;
   - drop the protector arms in `ww_attacker_unwebbable` and mage `victim_family`;
   - retire `i_tod_banner_protectors` whole;
   - re-bake FIRE BLAST ("BURNS ROBOTS AND ARMOR" is baked into its art) and fix
     the pause copy at `tod_upgrade.lua:744, 747`.

**Keep:** `zm_zod_robot.gsc/.csc`, `archetype_zod_companion*`, the fuse
craftable, the robot FX (the Panzer and Reaver entrances play them) and
`zm_ai_zod_companion.csv`. Never edit the install-side
`c_zom_zod_robot_protector.gdt`: TOD1, map 1 and Hellbound share it.

### 4.2 Replacement table (D5, a starting point)

Protectors were the flattest elite HP curve (x1.05 per round from r3), so a raw
count swap raises HP a lot. Substitutes are HP-normalised with a per-recipe
add-HP factor.

**HP anchors are ROUNDS, not floors.** `boss_hp( round, anchor, base, exp )`
compounds upward from the anchor round and is FLAT at `base` below it. A
floor's unlock stamps whatever round the party happens to reach it on. So when
a family unlocks on an earlier floor, pick a new anchor ROUND from the expected
round at that floor, solo and quad, and solve `base` so the old curve is
unchanged from the old anchor on.
- Example: the hound, which moves from floor 40 to floor 30. Today it is
  anchor round 30, base 11,200, exp 1.09. At anchor round 20 the base becomes
  11,200 / 1.09^10 = 4,731, and it still reads 11,200 at round 30.
- Change the per-family defines only, never `boss_hp` itself: the Panzer and
  the King share it, and the Panzer's `level.mechz_health` must equal its
  spawn HP.

| Consumer | Today | Proposed |
|---|---|---|
| Unlock ladder | 10 protector, 20 reaver, 30 sprinter, 40 hound | 10 sprinter, 20 reaver, 30 hound, 40 nothing (D6). Sprinter HP is trash-relative, so it scales down when unlocked early. |
| Mage fire family | protector + armored sprinter | armored sprinter; re-rank the fire/ice matchup constants and re-verify in the armory BALANCE tab |
| Trial I THE RING | prot 2 (its only add family) | reaver 1 or sprint 2, HP-normalised |
| Trial II | prot 1, hound 4 | hound 5 |
| Trial III THE FIRING LINE | prot 3, reaver 1 | +1 extra Warden (the Panzer shoots grenades down the lanes) + reaver 1 |
| Trial IV | prot 1, reaver 2, hound 1 | reaver 2, hound 2 |
| Trial V | prot 1, hound 2, sprint 3 | hound 3, sprint 3 |
| Trial VI THE GAUNTLET | prot 3, reaver 1, sprint 2 | 6 slots kept, HP-normalised |
| Trial VII | prot 3, reaver 2, hound 3, sprint 3 | reaver 3, hound 4, sprint 3, HP-normalised |
| King summons | prot 2 (3 on rampage) | +1 reaver, +1 hound |
| Finale rotation | 4 arms; arm 1 = protectors | 4 arms kept (a second, smaller hound arm); the opening-wave clamp moves to the hound debt |
| Finale flare beat | 2 protectors dropped at the gate | a reaver drop with a new force-origin lane |

---

## 5. Asset pipeline and tooling

### 5.1 The registry: `tools/partner/registry.json`

Human-written; no tool writes it. Commentary goes in `why` and `note` fields.

```json
{
  "schema": 1,
  "body": { "tint": [0.30, 0.58, 1.00], "arms": "blue",
            "owner_light_colours": ["cyan", "gold", "magenta", "green"] },
  "base_stats": { "max_hp": 1000, "armor": 0, "recharge_secs": 45,
                  "slam_radius": 200, "aggro_radius": 160, "aggro_cap": 3 },
  "budgets": { "robot_tris_lod0_max": 60000, "attachments_per_robot": 7,
               "materials_per_robot": 16, "upgrade_texture_bytes": 4194304,
               "stage_tris_lod0": { "torso_shell": 6000, "right_arm": 3000,
                                    "back_pack": 2500, "left_arm": 2000,
                                    "hips": 2000, "helmet": 1500 },
               "stage_lods": 4, "atlas": 1024,
               "power_max": "1.5625^3", "rung_tolerance": 0.10,
               "share_start": 0.08, "share_max": 0.25, "min_trash_volleys": 2,
               "elite_damage_mult": 1.0, "ref_round": 5, "king_ref_cycle": 0.4167 },
  "upgrades": [
    { "key": "armor", "index": 0, "name": "ARMOR",
      "shop_text": "HEAVIER PLATING FOR YOUR PROTECTOR",
      "max": 5, "price": [1500, 2500, 3500, 5000, 7000],
      "slot": "torso_shell",
      "effect": { "kind": "stat",
                  "per_level": { "max_hp": [0, 400, 800, 1300, 1900, 2600],
                                 "armor":  [0, 10, 20, 30, 40, 50] } },
      "stages": [ { "at": 1, "model": "cc_ptn_armor_s1", "anchors": ["j_chest_door_dam"] },
                  { "at": 2, "model": "cc_ptn_armor_s2", "anchors": ["j_chest_door_dam", "j_shoulder_le_rot_dam", "j_shoulder_ri_rot_dam"] } ],
      "detail": { "eff": "INTEGRITY +%V", "act": "ARMOR ON YOUR PROTECTOR" },
      "why": "the user's own example: extra armor must look and act like armor" }
  ],
  "grip": { "left_hand_from_right": [0, 0, 0],
            "note": "measured from the rifle xanims in the spike; every gun's foregrip sits here" },
  "flash_styles": ["rifle", "smg", "shotgun", "energy"],
  "modes": { "auto": { "ref_victims": 1.0 }, "burst": { "ref_victims": 1.0 },
             "pellets": { "ref_victims": 1.5 } },
  "ladder": [
    { "rung": 1, "power": 1.0,    "gate": null },
    { "rung": 2, "power": 1.5625, "gate": { "floor": 10 } },
    { "rung": 3, "power": 2.44140625, "gate": { "floor": 30 } }
  ],
  "weapons": [
    { "key": "ar", "index": 0, "rung": 1, "name": "RIFLE", "shop_text": "THE STANDARD ISSUE RIFLE",
      "price": 0, "mode": "auto",
      "profile": { "interval": 0.35, "spread": 2, "range": 1400, "falloff_start": 900,
                   "trash_volleys": 6, "reload_every": 30, "reload_secs": 2.0 },
      "model": "cc_ptn_gun_ar", "placeholder_model": "<an already-zoned rifle world model>",
      "muzzle": "tag_flash", "flash_style": 0, "sound": "cc_ptn_shot_ar",
      "why": "cycle 0.35 + 2.0/30 = 0.4167 s; the reference every rung is measured against; 6 volleys set share_start" },
    { "key": "smg", "index": 1, "rung": 2, "name": "RAPID", "shop_text": "A FAST SMG FOR CLOSE WORK",
      "price": 4000, "mode": "auto",
      "profile": { "interval": 0.15, "spread": 4, "range": 800, "falloff_start": 500,
                   "trash_volleys": 8, "reload_every": 40, "reload_secs": 2.0 },
      "model": "cc_ptn_gun_smg", "placeholder_model": "<an already-zoned SMG world model>",
      "muzzle": "tag_flash", "flash_style": 1, "sound": "cc_ptn_shot_smg",
      "why": "cycle 0.20 s; 1/(8 x 0.20) against the AR's 1/(6 x 0.4167) = 1.5625, trash and elite" },
    { "key": "shotgun", "index": 2, "rung": 3, "name": "SCATTER", "shop_text": "A SHOTGUN FOR CROWDS UP CLOSE",
      "price": 8000, "mode": "pellets",
      "profile": { "interval": 0.52, "pellets": 8, "spread": 9, "range": 450, "falloff_start": 250,
                   "trash_volleys": 2, "elite_mult": 1.5, "reload_every": 8, "reload_secs": 2.0 },
      "model": "cc_ptn_gun_shotgun", "placeholder_model": "<an already-zoned shotgun world model>",
      "muzzle": "tag_flash", "flash_style": 2, "sound": "cc_ptn_shot_shotgun",
      "why": "cycle 0.77 s; trash 1.5 victims/(2 x 0.77) and elite 1.5 x 1/(2 x 0.77) both = 2.435 against the AR" }
  ],
  "shops": { "catalogues": ["protector"], "noun": "PROTECTOR SHOP" }
}
```

The generator refuses to write anything if any of these hold:
- an `index` is not unique, not append-only, or reused;
- a name is longer than 32 characters (63 truncates silently);
- a price or stat ladder has the wrong length;
- two upgrades share a slot;
- a stage exceeds its slot's triangle cap;
- the whole robot at max level exceeds `robot_tris_lod0_max`;
- any text uses characters outside the typeface's 42 glyphs;
- an anchor is not a robot bone (checked against the donor snapshot);
- a gun names a `mode` with no registered handler, a `flash_style` outside the
  style list, or a `placeholder_model` / `carrier` that is not already zoned;
- the ladder has a gap in its rungs, or its power does not strictly rise;
- a gun's trash or elite power is more than `rung_tolerance` away from its
  rung's power, unless the row carries `rung_exempt` with a `why`;
- a gun's `trash_volleys` is below `min_trash_volleys`;
- there is not exactly one price-0 gun, on rung 1 (the robot must start holding
  something);
- a gun's price is below the highest price on the rung beneath it;
- a rung above 1 has no gate, or a gate of a kind with no handler, or a rung 2
  or 3 floor that differs from `TOD_TIER2_FLOOR` / `TOD_TIER3_FLOOR`;
- ARMAMENT's maximum is more than one rung step, or the top rung times
  ARMAMENT's maximum exceeds `power_max` (both with the 1e-4 relative rounding
  tolerance, since the doc's own factors are irrational);
- using the class guns' generated DPS figures, the median class's share with
  the AR at ARMAMENT 0 is more than `rung_tolerance` from `share_start`, or ANY
  class's share at the top rung with full ARMAMENT exceeds `share_max`;
- a gun overrides `ref_victims` without a `why`;
- a SHIPPED gun's rung or profile changes without a `rebalance_why` (a gun
  already in players' hands is only rebalanced on purpose).

It prints every budget's use on every run.

**Status is derived, never typed.**
- A stage model is **installed** when its `install_manifest.json` exists and
  `verify` passes.
- Shop art is **installed** when its PNGs exist with the recorded hashes.
- A model is **approved** when `approval.json` holds the user's words.

### 5.2 `node tools/partner/gen_partner.js`

The one writer of generated text. Inputs: the registry, the committed donor
snapshots in `donor_gdt/zod_robot/`, and the install manifests. It never reads
the live gdtdb, which changes in every build. `tools/partner/snapshot_donors.py`
(the existing sqlite reader) writes the snapshots once. They hold every
materialised field of the donor spawner, variant, archetype, character, xmodel
and materials, plus the 186 bone names and bind transforms.

| Output | Content |
|---|---|
| `scripts/zm/zm_tod2_cybercity/_tod_partner_data.gsc` | GENERATED header, pure accessors (upgrades, prices, stats, stages, kiosk positions come from the map generator's own data), `#precache` of installed stage models and the partner/shop eventstrings |
| `ui/.../TodPartnerData.lua` | names, shop text, prices, detail rows, and FULL literal image names (for example `"i_tod_shop_ptn_armor"`) for installed art only, so lint GATE A checks their zoning once it follows `include,` lines (§5.6) |
| `source_data/cc_partner.gdt` | whole file, no comments (GDT comments are unsafe): body twin, LODs, light twins, character, aitype chain, installed stage models and materials, installed shop images (BC7 blocks) |
| `zone_source/tod_partner.zpkg` | whole file, included by ONE hand line `include,tod_partner` in the main zone (the `tod_twins.zpkg` precedent). No read-modify-write of a file peers edit. |
| `tools/tod_partner.generated.json` | the manifest the lints read |

`--check` generates in memory and compares with LF normalisation. It writes
nothing and exits 1 listing stale files. It runs before the sync in
`build_map.ps1` (next to `verify_weapon_costs.js`), so drift fails every build,
`-GscOnly` included. Every run prints the build it owes: FULL when the GDT or
models moved, `-GscOnly` when only data moved.

**Text/binary rule for every partner tool:**
- Text artifacts (GDT, JSON, `.gsc`, `.lua`, `.zpkg`) are written with LF and
  hashed after CRLF-to-LF normalisation.
- Binaries (`.xmodel_bin`, `.png`) are hashed raw.
- `.gitattributes` declares `*.xmodel_bin binary` and `*.blend binary`.

Today's roster and altar GDTs are pinned by raw SHA and are CRLF on disk but LF
in git, so a fresh checkout fails their gates.

### 5.3 Blender MCP

**`ptn studio setup|start|status|stop`:**
- `setup` builds a TOD II-owned venv from `tools/partner/requirements.txt`
  (pinned `mcp` and `blender-mcp`), with the addon vendored into
  `tools/vendor/blender_mcp/` along with its licence. Today the whole chain
  lives in Hellbound's gitignored `tmp/`.
- `start` refuses if anything already listens on 9880, then launches Blender
  4.2 with the master. It waits for a READY that is printed only when the
  server is really listening, then does a round-trip that checks a scene
  marker unique to the partner master. A wrong port therefore cannot drive
  another project's Blender. `tools/mcp_ports.json` lists every repo's port
  (9876 to 9879 are taken).

**Files:**
- `art/partner/robot_base.blend` is read-only. The robot-specific Stage 00
  builds it from the donor snapshots: the MVP armature code, plus a material
  resolver that reads the pack GDT rows instead of a folder, skips
  `$`-placeholders, and builds a preview shader that reproduces the blue
  specular tint. The existing importer would KeyError on this robot and would
  draw it black.
- Each upgrade has its own `art/partner/upgrades/<key>.blend` that LINKS the
  base. This keeps every file far under GitHub's 100 MB limit (the repo already
  tracks one 127.6 MB blend), and keeps history and SHAs per upgrade. Use Git
  LFS for `*.blend` before Phase 2.
- The kiosk model gets the same treatment: `art/partner/kiosk.blend`.
- Each gun has `art/partner/guns/<key>.blend`, linking the base so it is always
  judged in the robot's hand. Stage 00 of a gun imports its
  `placeholder_model` (or any zoned gun world model named as its donor) in the
  grip frame, so a robot gun can start as a restyled player gun rather than
  from nothing.

**Working rules:**
- **Stage scripts own the geometry.** `tools/partner/upgrades/<key>/sNN_*.py`
  are re-runnable. The user's direction is applied by editing the script, not
  the mesh; the one exception is a `user/` sub-collection that scripts never
  touch.
- **`ptn stage <key>`** runs the upgrade's stage scripts through MCP and takes a
  screenshot. It then runs **`fit_check`**, which replays the robot's real
  walk, sprint, aim-walk and shoot xanims (440 are on disk, and 362 key the
  `*_dam` anchors), reports how deep any part vertex goes into the body, and
  fails above the slot tolerance. For a gun it also checks the grip frame (the
  foregrip within tolerance of the measured left-hand point on every frame),
  and clearance against every installed ARMAMENT stage. `ptn stage` takes
  `gun:<key>` as well as an upgrade key.
- **`ptn approve <key> "<the user's words>"`** writes `approval.json`.
  Installing refuses a model without it (the staff precedent: nothing moves in
  until the user confirms its look).

### 5.4 Ship, verify, preview

`ptn ship-model <key>` runs these steps in order:

1. **Save.** Saves the live session through MCP, reads back "not dirty" and the
   file hash, and asserts that the on-disk master matches it. Background export
   opens the file from disk, so unsaved steering would otherwise be lost.
2. **Export (background).** Bakes 5 maps (c/n/s/g/e) into one atlas per
   upgrade, with normal green DirectX (-Y), and makes 4 component LODs per
   stage. It works in a staging folder per upgrade
   (`art/partner/engine_kit/<key>/`), because a shared folder lets one export
   overwrite another's LOD counts.
3. **Install.** Writes `model_export/cc_partner/<model>_lod0..3.xmodel_bin` with
   PyCoD WriteFile_Bin. Each stage model carries its anchor bones with the
   robot's bind transforms, and weights of 1.0. It writes
   `install_manifest.json` with LF.
4. **Verify (source).** Checks the hashes; bone names and transforms against the
   robot; finite normals and UVs; the slot envelope; the budgets; that names
   start with `cc_`; and that registry, GSC table, zpkg and precache agree.
5. **Preview.** Renders the INSTALLED binaries on the blue body at every stage:
   the exporter's emission scale, gameplay FOV 65, third-person cameras at 150,
   400 and 800 u, neutral and dark-cyber light. Output goes to
   `art/partner/renders/<key>_s<n>_<view>.png`, plus a contact sheet. These are
   also the art brief's references.
6. **Regenerate** (`gen_partner.js`).

After linking, `verify --compiled-ledger` checks that every LOD's triangle count
survived conversion. Every report carries `native_visual_verified: false`,
because Blender renders are previews. The user judges the look in game.

- The shared helpers (`native_geometry.clean`, `reduce_game_lods`,
  `cyber_material_bake`) move to `tools/lib/`, so partner output does not shift
  when an unrelated art folder is edited.
- One `Copy-Tree model_export\cc_partner` line goes into
  `sync_to_modtools.ps1`. A folder created after the isolated workspace's setup
  is allowed, and it is created physically.

### 5.5 Shop art

Each upgrade and each gun needs a **shop tile**: a square icon of the upgrade
(or of the robot holding the gun) on the blue robot, plus its name, drawn in
the card family's chassis style. A gun's tile also supplies its HUD chip glyph.
The kiosk gets its own prompt icon.

1. `ptn new` writes the brief ONCE, from a template, to
   `docs/partner/<key>_shop_art_prompt.md`, with the `<!-- art-pack -->` header.
   Its refs are a shipped card (chassis and style), the `ptn preview` renders,
   and the target on-screen size. After that the brief belongs to people: it is
   tuned after a bad drop, and its STATUS is flipped to SHIPPED. `gen --check`
   only verifies that every upgrade still pending has a brief whose refs exist.
2. `ptn art <key> pack` re-renders stale refs and runs `make_art_pack.ps1`.
   `make_art_pack.ps1` gains a `-Prefix` parameter (it hard-codes `tod_` today),
   so partner zips are named `tod2_partner_<key>_art_pack.zip`.
3. The user sends the zip to the generator.
4. `ptn art <key> install --latest`:
   - picks the newest `files*.zip` by modification time (the browser has
     stopped numbering them; the newest look like
     `files - 2026-09-22T152105.980.zip`), prints its name and time, and
     refuses a drop older than the pack;
   - runs `-Inspect` and opens a contact sheet;
   - after the user confirms, copies the PNGs and regenerates, which emits the
     BC7 image blocks, the zpkg lines and the Lua literals together.

A pending tile names no image, so it can never draw a white square. The panel
falls back to text.

### 5.6 Gates in `build_map.ps1`

| When | Gate |
|---|---|
| before sync | `gen_partner.js --check`; `verify` source mode (repo files only, so it fails before anything deploys) |
| pre-link | `node tools/test_partner_reconcile.js` (mocked Attach/Detach, the `test_cyber_zombie_spawns.js` shape, including gun swaps and the placeholder fallback); `node tools/test_partner_fire_modes.js` (every registered mode against every gun row: each gun's trash and elite power matches its rung, and power strictly rises by rung; sweeping victim health continuously, with the game's own whole-volley rounding, the rung order never inverts; every ARMAMENT level scales every gun by the same factor; at most one volley's damage per victim per volley; the King's damage per second is identical for every gun, ARMAMENT level and party size; per class, the kill share sits at `share_start` for the AR at ARMAMENT 0 and at or below `share_max` at the top, and is unchanged across rounds 5, 15, 30 and 50, party sizes 1 to 4 and rampage on or off; and negative controls that must fail: a gun off its rung, a 1-volley gun, ARMAMENT above one step, a missing gate, an unknown gate kind); `node tools/test_partner_lifecycle.js` (death, recharge, slot reservation, stow and re-arrive, disconnect); `node tools/test_shop.js` (buy validation, freeze policy, takeover) |
| every build | `lint_tod_assets.js`, extended in three ways, each with a selftest case whose scratch copy carries the zpkg. (1) It expands repo-local `include,<name>` zpkgs; three implementations already exist to copy, in `audit_zone_usage.js`, `lint_tod_weapons.js` and `gen_tod_twins.js`. Without this, every installed partner image fails GATE A, because the lint reads only the main zone. (2) It reads `tod_partner.generated.json`. (3) It checks that every zoned `cc_ptn_*` xmodel is precached. GATE B already exempts Lua literals, so no declared-slug step is needed. `lint_tod_hints.js` learns the shop noun and its expected route. |
| post-link | `verify --compiled-ledger` |

`verify_tod2_database.py` and `verify_tod2_separation.py` will read the partner
manifest instead of hard-coded model names.

One latent gate bug the partner relies on: `lint_tod_arity.js` never exits
non-zero, so its gate cannot fail. The fix (`process.exit( bad ? 1 : 0 )`)
needs the user's OK, because it could newly fail peer sessions' builds.

---

## 6. RUNBOOK: adding a new partner upgrade

Everything goes through `.\tools\partner\ptn.ps1`. Each verb is idempotent and
logs to `tmp/partner/`. Steps 3 to 6 can come later: an upgrade can ship
working in the shop with a text tile and no model, then gain its model and art
as they land.

1. **`ptn new <key> --kind stat|ability --max 5 --slot <slot>`.** Prints the
   registry row to paste (the next free index, placeholder price and stat
   ladders, stages). Writes the stage-script stubs, a test fixture and the art
   brief, runs gen, and prints the owed build. Fill in the numbers by hand.
2. **Behaviour, only for a new ability:** one handler in
   `_tod_partner_combat.gsc`, registered by name, plus a test case. A `stat`
   upgrade needs no code.
3. **Model.** `ptn studio start`, then `ptn stage <key>` while the user watches
   the live Blender window; direction goes into the stage scripts. When the
   user likes it: `ptn approve <key> "<their words>"`.
4. **`ptn ship-model <key>`:** saves, exports, installs, verifies, previews and
   regenerates.
5. **`ptn art <key> pack`,** then send the zip to the generator.
6. **`ptn art <key> install --latest`** when the drop comes back.
7. **`ptn check`** runs exactly what the build runs.
8. **Build and stop:** `.\tools\build_map.ps1` (FULL when models or art moved).
   Write the CHANGELOG entry; the patch-notes window reads only the CHANGELOG.
9. **The user playtests.** Read `[TOD_PARTNER]` / `[TOD_SHOP]` from the
   archived `console_mp.log`.

### 6a. RUNBOOK: adding a new gun

Same verbs, with `gun:<key>` in place of an upgrade key. A gun that fits an
existing fire mode needs **no code at all**, and it can ship playable before
its model exists, holding its placeholder.

1. **`ptn new gun:<key> --mode auto|burst|pellets --rung next|<n> [--like <gun>]`.**
   Prints the `weapons` row to paste: the next free index; a profile that
   picks a whole-number `trash_volleys` of at least `min_trash_volleys`, then
   solves the interval so the gun lands on its rung's power, then `elite_mult`
   so its lone-target power does too (starting from `--like`'s
   feel if given); a placeholder model and carrier suggestion; the next flash
   style that fits. `--rung <n>` joins an existing rung as an equal-power
   alternative. `--rung next` also writes a TODO `ladder` entry, which
   `--check` refuses until its power and gate are filled in and `power_max` is
   raised on purpose. Writes the Stage 00 stub, a test fixture, the art brief,
   and a sound brief if no alias exists yet. Runs gen, which prints the gun's
   measured power against its rung.
2. **Sound.** Point `sound` at an existing alias, or add the wav and one alias
   row through `gen_tod_sounds.js`'s normal path (a `-GscOnly` build ships a
   new alias row; a new wav is FULL).
3. **Behaviour, only for a new fire mode:** one handler in
   `_tod_partner_combat.gsc` and a test case. Every later gun of that mode is
   data only.
4. **At this point the gun is playable** with its placeholder model. Build and
   stop, and the user can try it before any art exists.
5. **Model:** `ptn studio start`, `ptn stage gun:<key>`, and
   `ptn approve gun:<key> "<their words>"`, then `ptn ship-model gun:<key>`.
6. **Shop tile:** `ptn art gun:<key> pack`, send the zip, then
   `ptn art gun:<key> install --latest`.
7. `ptn check`, build and stop, CHANGELOG entry, the user playtests (the
   `VOLLEY` and `ROUND_SUMMARY gun= rung=` lines show whether it is pulling
   its weight).

Other verbs:
- **`ptn status`** prints a table per upgrade and per gun: code, model, art,
  approved, budget use, and the build owed.
- **`ptn retire <key>`** marks the row retired (its index is never reused),
  deletes that upgrade's binaries, images and manifests, regenerates, and prints
  the private-root paths to clean (the sync never deletes).
- **`ptn rollback <key>`** restores the previous install from git and
  re-verifies.

---

## 7. Budgets

| Budget | State today | Partner plan |
|---|---|---|
| engine actor pool, 64 | the script gate of 60 leaves 4; direct-spawned elites already use that headroom | zombie limit = 60 minus CONNECTED owners (active, recharging and stowed robots all hold their slot, so the respawn always has one); elite roof minus connected owners; the retired Rogue Protector frees up to 8 elites |
| entities | spire budget about 1024 | +1 gun proxy per partner, drop_in proxies during a fall, one trigger per kiosk |
| clientuimodel bits | 61/61, full | none; eventstrings instead |
| actor clientfield bits | ceiling unknown; map 1 overflowed | reuse the Rogue Protector's freed fields; +2 bits for the gun flash style (`todBossShot` 2 to 4 bits, the only addition) |
| triggerstrings | 95 of 190 budgeted | 1-2 constant shop strings |
| card ids and owned-upgrade rows | 7 free ids; 2 free rows for skirmisher and heavy | not used |
| weapon registrations | 233 of 235 | none, for any number of guns: every gun fires through the robot's own companion AR or a carrier that is already zoned, and the held gun is a model, not a weapon. A gun that insists on its own weapon asset (a real projectile, say) costs one registration and needs the user's OK against this ledger. |
| sound | the loaded bank | one alias per gun; reuse is free |
| robot triangles | the body is 47,574 at ONE LOD | a generated LOD chain for the body; a registry cap on the whole robot at max level |
| attachments per robot | engine cap unknown | at most one per owned upgrade (6), plus one gun |
| UI art | BC7 tiles | one tile per upgrade and per gun, installed art only |
| repo size | one tracked blend is already over GitHub's 100 MB | per-upgrade blends; LFS before Phase 2 |

---

## 8. Unknowns, and the Phase 0 spike that settles them

A short build whose only job is to answer these with logs in one user playtest.

| Unknown | How the spike settles it |
|---|---|
| Does `SpawnActor( "spawner_cc_partner" )` spawn an allied robot? Does the blue twin render? | the `SPAWN` log, and the user's eyes |
| Does the archetype's spawn setup undo our stamps? | the re-asserted values in `SPAWN` |
| Aggro lane A: do zombies offered the robot through `closest_player_targets_override` walk to it and swing, and does the damage reach the partner callback? | `AGGRO` and `DRAIN` logs; the user sees zombies attack it |
| Does the gun proxy keep stock scoring away from the partner, and does its damage branch fire? | `HIT` log with the proxy as attacker; no stock score events for partner hits |
| Death and respawn: does the reserved slot always let the respawn spawn? Does the slam kill trash and credit the owner? | `DEATH`, `RECHARGE`, `SPAWN`, `SLAM kills=` logs |
| Lane A attachments: does a stage model rooted at robot bones, with copied bind transforms, follow the animation on the `*_dam` bones, and does it ride the drop_in proxy? | one test model written with PyCoD (no Blender yet) on `j_spine4_dam` and `j_helmet`; `STAGE_ON attach_size=`; the user's eyes |
| Does the allied archetype fire natively? | `NATIVE_FIRE` |
| Goal radius and the \|dz\| follow constraint on stair ramps | `[TOD_AI]` lines of the "partner" class |
| Does anything still kill, freeze or strand the partner (sweeps, pads, pauses, seals)? | `STATE` / `WARP` / `PAUSE` across a teleporter ride, a card event and one trial |
| Do the robot's own behaviour-tree services fight the script goal? The collision service walks every zombie per tick per robot; reacquire and juke steps move the robot on their own; Shadows of Evil only ever ran ONE of these robots. | server frame-time and `WARP`/NAV lines with four robots. If the services fight or cost too much, run ACTIVE with `ignoreall = 1` and a script-owned `OrientMode`, since firing is scripted anyway. |
| Does clearing `ignoreme` let the engine's own enemy choice send zombies at the robot past `aggro_cap`? | the `AGGRO` counter against `zombie.enemy == partner` |
| Does a placeholder gun (an already-zoned player world model) attached at `tag_weapon_right` sit in the hand, and follow the aim and walk animations? Does it ride the drop_in proxy? | the user's eyes; `EQUIP ... placeholder=1` |
| Where do the rifle animations put the LEFT hand relative to the right? This fixes the grip frame every gun is authored in. | measured offline from the 440 xanims (no build needed); recorded as `grip.left_hand_from_right` |
| Do the server's `GetTagOrigin( "tag_flash" )` and the client's `PlayFxOnTag` on the actor find the `tag_flash` of a script-attached model? | the `VOLLEY` muzzle position against `tag_weapon_right`; the flash in the right place. If not, the registry muzzle offset is used, which is why every gun row carries one |
| A second gun and a swap: does `equip` Detach/Attach cleanly with no stacked models, and does the widened `todBossShot` pick the right flash? | `EQUIP`, `RECONCILE attach_size=`, the user's eyes |

---

## 9. Delivery phases

| Phase | Contents | Build |
|---|---|---|
| 0 spike | Rogue Protector retired (§4); blue body twin with LODs and owner-colour lights; spawn, follow, fire through the gun proxy; zombie aggro, death, recharge, slam; pause; sweeps filtered; warps; one PyCoD test stage model; a placeholder gun in its hand and one dev-triggered swap to a second placeholder; all logs | FULL; the user playtests |
| 1 system | the registry, snapshots, generator, `ptn` core verbs (new, check, status) and gates; the grant funnel, equip, stats, reconcile; the shop core with one kiosk at the base and the Protector catalogue (text tiles), guns included; HUD chip and pause section; ARMOR and ARMAMENT working; the AR, SMG and shotgun working on placeholder models (`auto` and `pellets` modes) as a three-rung ladder, with the floor gates, the locked shop states, the unlock toasts and the `SCALE` log | FULL |
| 2 looks | the studio and model verbs; ARMOR and ARMAMENT models and the three robot guns through Blender MCP; the kiosk model; shop tile art packs; kiosks around the map; REACTOR, TAUNT | FULL per batch |
| 3+ | SALVAGE, OVERWATCH, and new upgrades through the §6 runbook | per upgrade |

**Before Phase 0: a checkpoint commit.** Everything since commit `1890e6b` is
uncommitted, including a peer session's whole `zm_tod2_cybercity` rename and
the isolation work. A peer's checkout or stash could drop all of it. Committing
is the user's call.

---

## 10. Evidence index (read 2026-09-22/23)

- **Companion services and the revive leak:** `scripts/zm/archetype_zod_companion.gsc:354-451, 577-671, 854-949` (manage_companion gated only on `reviving_a_player`, :885-897)
- **Pack game-end overrides:** `scripts/zm/zm_zod_robot.gsc:65-66, 96-110`
- **Rogue Protector spawn, flags, fire loop, drop_in:** `scripts/zm/zm_tod2_cybercity/_tod_bosses.gsc:1076-1245, 2767-2913, 2984-3063`
- **Zombie targeting:**
  - stock `zombie_utility.gsc:50-70` (`closest_player_targets_override`)
  - `zm_tod2_cybercity.gsc` `tod_closest_player`
  - stock `zombie.gsc:398-405` (zombies damage an AI with `allow_zombie_to_target_ai`)
  - stock `_zm_spawner.gsc:104-159` (the same flag on an attacker scores like a player)
- **Gun proxy precedent:** stock `zm/aats/_zm_aat_fire_works.gsc:97-131, 190-213`
- **Menus are display-only:** `_tod_upgrade_ui.gsc:1092-1096`
- **Server-read input loop:** `_tod_upgrade_ui.gsc` `wait_for_choice` (:1031)
- **Station freeze policy:** `_tod_upgrades.gsc:8311` (`station_freeze_wanted`), :3311 (`menu_freeze`), :6053 (`set_world_pause`)
- **Furniture grammar:** `tools/gen_tower_map.js:649-699` (crates, `CRATE_TRIG_OUT`), `BR_FURN`
- **Prompt routing:** `ui/uieditor/widgets/HUD/ZM_CursorHint/ZMCursorHintNew.lua:228` (`TOD_NOUNS`)
- **Kill sweeps:** `_tod_spire.gsc:915-957`; `_tod_finale.gsc:1305-1379`; `_tod_corpse_cleanup.gsc:490-529` (hoop_probe)
- **Actor limits:** `_tod_corpse_cleanup.gsc:115-134, 257-300, 631`; `_tod_bosses.gsc:124-166, 896-936`
- **Damage chain:** stock `_zm.gsc:5625-5862`; `_tod_upgrades.gsc:6192-6368`; Wisp Tea segments `_zm_perk_wisp_tea.gsc:709-735`
- **Economy:** `_tod_luck.gsc:241-269, 350-365`; `_tod_mage_elements.gsc:1459-1470`; `_tod_bosses.gsc:2605-2652, 3640-3701`; stock `_zm_spawner.gsc:1585-1611`
- **Trials, King, finale, ladder:** `_tod_spire.gsc:2474-2519, 2216-2255`; `_tod_bosses.gsc:1620-1790`; `_tod_finale.gsc:777, 1639-1662`; `_tod_doors.gsc:456-496`
- **Robot rig:** install-side `model_export/black_ops_3/c_zom_zod_robot_protector/c_zom_zod_robot_protector_gold_fb.xmodel_bin` (186 bones, 47,574 tris, 1 LOD, 11 materials); 440 xanims under `xanim_export/black_ops_3/c_zom_zod_robot_protector/`
- **The robot holds no gun today (read 2026-09-23):** install-side `source_data/c_zom_zod_robot_protector.gdt`, the `ar_standard_upgraded_companion_zm` row (from :24740) has no world model, only `gunModel vm_t9_ak47`; the aitype row sets `primaryweapon1` to it and `primaryWeaponType rifle` (:26308). A PyCoD read of the gold body: no geometry on `tag_weapon_right` (child of `j_wrist_ri`), `j_gun_1` or `j_gun_1_tr`; the right hand is a fingered hand; bind height 73.7. Map 1's fire loop reads the weapon object from `self.weapon` (`_tod_bosses.gsc:2984-3063`). The target-service gate: `archetype_zod_companion.gsc:205-263`.
- **Helmet bind precedent:** `model_export/tod_cyber_zombie/tod_cyber_helmet_signal_lod0.xmodel_bin` (J_Head at its world bind, z 64.53)
- **Pipeline templates:** `tools/teleporter/`, `tools/install_cyber_roster.py`, `tools/verify_cyber_roster.py`, `tools/cyber_references/review.py`, `tools/cyber_references/render_native.py`, `tools/test_cyber_zombie_spawns.js`, `zone_source/tod_twins.zpkg`
- **Lints:** `tools/lint_tod_assets.js:98-111, 156, 213-218, 262-295, 370-401`; `lint_tod_arity.js` (no exit code)
- **Art packs:** `tools/make_art_pack.ps1:199, 292`

---

## 11. Revision history

**Revision 3.3 (2026-09-23): the guns are a ladder.**
Asked whether guns should be sidegrades or a ladder, the user answered
*"Ladder"*. A four-agent design pass (balance, player experience, systems,
then a judge that checked the cited code) worked out the shape, and a
two-agent review (consistency; math and citations) checked the result; its
12 findings are folded in below. What changed:
- D12 now records the user's decision. The ladder's shape is a default: rungs
  1 AR, 2 SMG, 3 shotgun; ×1.5625 per rung (`TIER_DPS`); unlocked with points,
  the rung below, and floor 10 or 30 (the class-tier floors, checked against
  their defines); higher rungs gate on spire trials. Same-rung guns are
  sidegrades, so a new gun never rebalances an old one.
- A registry `ladder` table, a `rung` field separate from `index`, and one
  power formula for every fire mode (`ref_victims` counts a pellet volley's
  crowd).
- **The damage model changed from maxhealth fractions to REAL damage that
  follows the owner's gun power** (§3.5): `owner_index × HP_REF /
  trash_volleys` per volley. The robot and its owner fight the same health, so
  the robot-to-owner kill ratio holds at every round, party size, rampage and
  trial, against trash and elites alike. The design pass first proposed a
  rounded volley-count correction on top of maxhealth fractions. Its review
  showed that correction let the shotgun fall below the SMG through rounding,
  ignored the party-size and rampage health multipliers, and left elites
  running away late in a match. Real damage removes all three at the source.
- Per-gun `elite_mult` replaces `elite_volleys`, so a pellet gun keeps its
  rung on a lone target. `min_trash_volleys` (2) and a continuous health sweep
  in the test keep rounding from inverting the ladder.
- The King's share is set in time units, so every gun, ARMAMENT level and party
  size gives the same fight length.
- ARMAMENT speeds up the firing cycle only, by the exact factor
  `1.5625^(-1/5)` per level; its maximum is one rung step, and it carries
  across guns. The volleys channel is gone, and `range_pct` belongs to no
  upgrade yet.
- The kill-share target is restated as 8% at the start, rising to at most 25%
  fully upgraded, since one 25% ceiling over a ×3.81 ladder cannot also give
  the starting robot 15%.
- Purchases validate the rung gate BEFORE taking points; a gate kind beyond
  `floor` (the spire `trial` gate for rung 4+) is one-off code, and the §1
  promise now says so.
- Gun shop states `locked_floor` and `locked_prev`; the shop opens on the next
  buyable rung; unlock toasts; the chip shows the rung, replacing the "rank
  pips" that were never defined.
- New generator refusals and test assertions replace the parity gate; the
  add-a-gun runbook takes `--rung`; new `SCALE` and `RUNG_UNLOCK` logs.
- The example registry now has an SMG row, and the shotgun is on rung 3. The
  revision 3.2 shotgun measured only 1.39 against the AR, which is below the
  SMG's rung.
- Two points left for the user: which gun is the top rung, and whether rungs
  unlock by tower floor or by the owner's class tier.

**Revision 3.2 (2026-09-23): the robot holds different guns.**
The user asked whether the architecture covers upgrades that make the robot
hold an AR, an SMG or a shotgun. It did not: guns had no place in the data
model, and ARMAMENT's parts were mounted on the gun. What changed:
- A new exclusive slot, §3.7a: a registry `weapons` table, an owned set and a
  held gun per owner, `grant` and `equip` through the same funnel.
- Fire modes are code and guns are data: `auto`, `burst` and `pellets` handlers;
  a gun that fits a mode is a registry row plus a model.
- Hits to kill are counted per volley, so a shotgun cannot multiply elite and
  King segments.
- The held gun is a script attachment at `tag_weapon_right` (Lane B, one grip
  frame). The engine weapon never changes, which keeps the §3.2 rule. The
  evidence: the pack's companion AR has no world model and the body has no gun
  geometry, so there is nothing to cut away.
- Placeholder models: the robot is human scale, so an already-zoned player gun
  model fits its hand, and a new gun is playable before any Blender work.
- ARMAMENT's parts moved from the gun to the forearm and shoulder, so they fit
  every gun.
- `todBossShot` widens from 2 to 4 bits for four flash styles; shot sounds come
  from the gun proxy and cost no bits.
- New decisions D12 (guns are sidegrades) and D13 (buy once, re-equip free);
  a new §6a runbook; new spike rows, gates, logs and budget lines.

**Revision 3.1 (2026-09-23): second review round (robustness attacker, completeness verifier).**
- The King max-out hook moved to `king_max_out`, over every connected owner; `king_max_player` never runs for dead players.
- The full owner-credit site table. The Panzer ledger remap was missing, and a partner last hit would have credited a teammate. `grant_elite_reward` is not reused for partner kills, because its procs break D3.
- One arrival owner polls `tod_class_select_done`. Otherwise partners would have arrived during the draft AND at its end, and never in the dev mage-test harness.
- The actor slot is reserved per CONNECTED owner, so stowed robots hold theirs too.
- The Blink false warp: explicit teleport stamps replace the 768 u distance rule.
- A separate `partner_slam`: the shared splash has no attacker, a fixed radius and every elite caller, and with the gun proxy it would have stopped killing and ragdolled live zombies.
- The aggro lane needs `ignoreme = 0`, a maintained `last_valid_position`, and a per-partner counter.
- New lifecycle rows: an END state at game over; the disconnect teardown order; the perk-shuffle unstick; client state-FX lifetime; presence and activity as separate variables.
- Plain ForceTeleport for seal and ascension warps, because of the entity budget.
- Attacker-less damage and the never-strip-the-weapon rule.
- Eventstrings are precached beside their senders.
- Lint GATE A needs include-following, and three implementations already exist to copy.
- HP anchors are rounds, not floors; the worked example is now the hound.
- The shop closes on a round-event takeover instead of copying the station's defer machinery.
- The checkpoint-commit warning.

**Revision 3 (2026-09-23): the user's answers.**

| Revision 2 said | The user said | Revision 3 |
|---|---|---|
| partner cards in a second phase of each upgrade event | item shops around the map | a catalogue-driven shop core; the Protector catalogue is its first customer; the card system is untouched |
| hurt only through ARMOR's bodyguard soak and TAUNT; reboots in place | it can die, recharges, and spawns back in with the slam | zombies attack it through the stock aggro lane; at 0 it dies, the slot stays reserved, and it recharges and slams back in beside its owner |
| `SetCanDamage( false )` | (follows from "it can die") | damage is on, but one partner callback owns all of it and always returns 0; death is the partner code's decision |
| FIELD MEDIC revives in co-op | no revives | dropped; REACTOR (recharge and slam) takes its slot |
| floor 40: a partner milestone | leave it empty | empty |
| shots credited to the partner | (follows from zombies attacking it) | a gun proxy per partner, so the aggro flag never turns partner hits into player scoring |

**Revision 2 (2026-09-23): fixes from three code-checking reviewers.**
- The card phase's timeout blocker.
- The leader thread's real gate (`reviving_a_player`).
- The actor-limit writer, plus the elite roof.
- Damage as `maxhealth` segments, not `level.zombie_health`.
- Owner kill credit through every non-player bail-out.
- Stage models carry copied bind transforms, not an identity root.
- One model per upgrade stage.
- A generated zpkg, not a spliced zone block.
- Full literal image names for the lints.
- Briefs written once, then owned by people.
- Derived status.
- The `ptn` front door.
- Studio port safety and the vendored addon.
- `fit_check` against the real animations.
- Previews from installed binaries.
- LF hashing.
- Per-upgrade blends under GitHub's size limit.
- The re-ordered unlock ladder with re-solved HP anchors.
- 4 finale arms kept.
- The party-row glyph.

**Revision 1 (2026-09-22):** the first draft, from seven parallel code reads.
