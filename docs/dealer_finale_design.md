# The Dealer: finale encounter draft

**Status: design only, 2026-09-30.** The user has chosen the Black Market Dealer
as the final boss and recurring identity. His combat form is pending: a colossal
Dealer looming above the arena, or a human-sized moving fighter. No gameplay,
map, native character or build changes are authorized by this draft. All encounter
numbers below are proposed starting values, not tested balance or user decisions.

The intended experience is recognition followed by betrayal: the same mask and
voice that welcomed the player at the shop now control the final room. The fight
rewards reading his gestures and surviving his machinery. It does not confiscate
earned weapons, companions, cards or points. The existing shop and the Keeper's
Battle Arena encounter remain intact.

## What exists now

| Source fact | Consequence for this encounter |
|---|---|
| `_tod_finale.gsc` has `TOD_FINALE_PARKED=1`; Crown is the start of the descent. | Do not re-enable the old Crown run by flipping its flag. |
| The dormant `tod_finale_boss_fn` has no writer and its caller treats any return as success. | A new controller needs explicit victory, abort and wipe results. A failed spawn must never win the map. |
| The route ends Plaza -> Shaft/Conduit -> Vault; zone adjacency uses `enter_base` and `enter_conduit`. | Put the finale invitation at the bottom, after legitimate descent progress. |
| Vault interior is x[-2592,-1952], y[-1028,-468], floor z=-384, ceiling z=-192: **640×560×192**. Its four window niches are active enemy routes. | Use it as the approach/gather area. It is too small for either proposed boss fight. Preserve its windows, respawns, partner-part access and existing door use volumes. |
| Battle Arena is a separate 1024-square room at (-8000,-8000,0), with four arrivals, eight spawns and a vented roof. | Reuse its integration lessons, not its room, progression or Keeper. |
| Shop vendor is rigid, one `tag_origin` bone; LOD0 has 25,999 triangles. Separate luminous mask has 760 triangles. | Neither form can be implemented by setting the shop model on an existing AI. Character deformation/animation or articulated giant parts are a separate art deliverable. |
| Five Dealer reaction portraits and 47 voiced shop lines exist. | Preserve that likeness and voice; finale dialogue needs appropriate new lines, not random purchase remarks. |

Sources: [The Fall](160_the_fall.md), [Battle Arena](185_battle_arena.md),
[Keeper](186_keeper_boss.md), [Dealer portraits](195_black_market_art_prompt.md),
[Dealer voice](198_black_market_voice.md), `tools/gen_tower_map.js`,
`tools/battle_arena_layout.js`, `_tod_finale.gsc`, `_tod_arena.gsc`,
`_tod_shop.gsc`, and the actual exported shop binaries. Historical prices and
layout descriptions in older docs are superseded by current source.

## Player sequence

1. **Recognition during the run.** Keep the shop's hood, red X eyes and stitched
   grin consistent with the sky crest and portraits. Propose only two short,
   once-per-party progression lines before the finale, at existing descent
   milestones. Deliver them after a safe transition, never over a card deal,
   another Dealer line or the first-jump reveal. No repeated unsolicited taunts.
2. **The invitation.** A finished Dealer device in the Vault becomes available
   after `enter_lap1`, `enter_base` and `enter_conduit` are open and `vault_zone`
   is enabled. Power alone cannot unlock it because power starts on. Proposed
   cost is zero: the descent is the investment. Proposed clear prompt:
   **Confront the Dealer — final encounter**. No requirement to buy shop items
   or complete the separate Battle Arena.
3. **Party commitment.** All currently playing, living teammates must be in a
   generated gather volume. Downed teammates count as participants but must be
   revived before the charge can commit; show a specific refusal. The standing
   activator holds USE, then a three-second visible and audible charge begins.
   Leaving, becoming downed, starting a menu, or changing party membership
   cancels before transport. A cancel spends nothing and changes no world state.
4. **Arrival and reveal.** Validate the destination and required encounter
   objects before moving anyone. Move the party to four separated landing spots,
   carry/reposition companions deliberately, stamp `tod_tp_stamp`, and delay
   arrival FX by the existing two-server-frame convention. Give three seconds
   with no attacks or damage on arrival. The camera remains under player control.
   A short gesture and voice line reveal the Dealer; show one boss bar.
5. **The fight.** Three health phases introduce and combine readable attacks.
   Guns, melee, class abilities and companions remain useful. Strong builds may
   finish quickly; no forced minimum fight duration or regeneration to erase DPS.
6. **Defeat and escape.** Confirm the authoritative boss death once. Cancel all
   attacks and remove encounter adds before the death performance. Revive downed
   survivors using the stock supported path, play a short final line/death cue,
   and show the custom victory screen after a proposed six-second safe departure.
   This replaces neither the map's ordinary wipe behavior nor the Keeper reward.

The victory music is presentation, not a countdown. The old 191-second Crown
song contract must not be used as a boss timer or win condition.

## Pending form decision

| | Colossal Dealer above the arena | Human-sized moving Dealer |
|---|---|---|
| Presence | Looming hood and mask, hands controlling the floor; silhouette readable without filling the screen with glow. | Recognizable Dealer enters physically, circles, casts and visibly recovers between attacks. |
| Authoritative combat | One server-owned health state; validated native damage targets connected to that state. Client art alone cannot own hits. | A dedicated native actor/spawner, character, skeleton and animation tables with normal actor damage. |
| Fair target access | Hand/gauntlet targets descend to reachable platforms. At least one target is continuously reachable by every class; recovery exposes a better target. Never require shooting only a distant face. | Full body is vulnerable except a clearly shown transition; ordinary movement and recovery support melee approaches. |
| Animation needs | Authored idle, hand placement, beam tell, floor-command cast, recoil and defeat. A scaled static shop body is insufficient. | Deforming body with verified idle, walk/run, turn, cast, stagger and death clips; cloak, mask and hands must survive extreme poses. |
| Arena implications | Larger sightlines and overhead clearance; giant parts must remain inside the actual sky/occlusion volume. | A walkable chase loop with broad turns, usable cover and no narrow passages that snag the actor. |

Both forms use the shared attack and phase design below. Final dimensions,
hit-target arrangement and movement timings wait for the user's form decision.
Do not hide a form choice inside the implementation.

## Combat contract and starting values

All timings use an encounter clock that stops while the world is paused.
Only one damaging boss action is active at a time. Target positions lock before
impact; the last part of a tell never follows the player. No invisible collision
damage, unannounced teleports or attacks through cover.

| Attack | What players see/hear and can do | Starting timing/damage |
|---|---|---|
| Collection beam | Hand/mask aim gesture, rising electrical tone, a narrow floor line. Step sideways or use genuine solid cover. | 1.5 s tell; target locks for the final 0.6 s; one 35-damage hit maximum per target per cast; 2.0 s recovery. |
| Marked floor strike | Dealer points/slams; outlined floor panels illuminate with a distinct ticking cue. Move to unmarked floor. Safe regions must connect and remain reachable at normal movement speed. | 1.8 s tell; one 45-damage impact; no lingering damage after the visible strike; 2.5 s recovery. |
| Collection call | A clear summon gesture and two visible entry effects. Adds create pressure while the Dealer recovers. | Up to 2 encounter-owned ordinary adds solo / 3 co-op, one arrival per second; at least 12 s before another call; zero direct cast damage. |

These are player-damage units sent through the existing player damage callback
and defensive-card rules, not raw health subtraction and not another `/10` pass.
Give each player at least 0.75 s between this boss's damaging events. Adds use
normal enemy rules; reduce their pressure before shortening boss telegraphs.
Never start a floor strike that eliminates every safe route or traps a revival.
Markers need shape/motion as well as color. Neither attack requires jumping,
sprinting, a particular perk or a particular class.

Proposed phases: **100–70%** teaches the beam; **70–35%** adds floor strikes and
the collection call; **35–0%** sequences the learned attacks more decisively.
The final phase does not shorten the minimum tells or overlap damaging actions.
Transitions last at most two seconds, cancel outstanding hits, and have a clear
mask/pose/audio change. Preserve damage crossing a threshold; do not silently
discard overkill to force a scripted phase. A killing hit wins even if several
thresholds were crossed in that hit.

Proposed first HP calibration is **120 current-round zombie HP units** at
commit, multiplied once by the current party/Rampage health factor. Existing
`tod_zombie_speed::health_mult()` combines party factors 1/1.20/1.35/1.50 and
Rampage's 1.20; do not apply either twice. Use the same power-scale path as
`hunter_hp`, with a recorded entry snapshot. This is only a starting benchmark:
test actual end-of-descent class damage and target a roughly 2.5–4 minute fight
for a representative loadout, without enforcing that length. Do not independently
boost outgoing damage every round as well as incoming HP.

A disconnect does not heal the boss. For a permanent party reduction, recompute
the party component downward while retaining the health fraction; downing or
temporary death does not rescale it. Late joiners spectate this committed
encounter rather than changing HP or appearing inside an active strike. Log the
decision. Class attacks, summons, companions, kill-intent exceptions and
multi-projectile damage need explicit audit; no blanket immunity added merely
to make the fight last longer.

## Room and progression integration

Propose a separate generated combat room reached from the Vault device. Keep
the Vault footprint intact and the Battle Arena exclusive to its existing
ten-level mode. Room world coordinates are **not chosen**: the generator must
prove separation from the tower, Crown, workshops and Battle Arena and inclusion
inside the existing sky, sun and Umbra volumes. Never shrink those volumes.

Use one new layout source to emit geometry, room/gather bounds, arrival and
fallback-return positions, boss anchors, spawn points, cover and zone data.
Candidate playable space should support a continuous loop and at least four
unobstructed paths between floor regions; final scale depends on form. Avoid
roofed sealed pockets: the current Battle Arena uses a vented roof because
closed pockets failed native occlusion. Each arrival, target platform and add
spawn needs native navmesh coverage, player-hull clearance and safe separation.
Do not substitute a Blender render for those checks.

Give the new room its own generated containment predicate. Music-floor tracking,
gauge/tier progress, ordinary enemy directors, stuck relocation, transit,
respawns and companions must recognize this encounter explicitly. Do not pretend
it is `arena_zone`, advance `tod_arena_level`, or take ownership of its
`tod_trial_box` without a coordinated shared interface.

## Lifecycle and recovery

Controller states: `locked -> ready -> charging -> preparing -> reveal -> combat
-> defeated -> departing -> complete`. Any operational failure transitions to
`aborting -> ready`; a genuine party wipe remains stock game over. One encounter
generation owns all threads, actors, damage targets, FX handles and state claims.

| Event | Required behavior |
|---|---|
| Double activation | Acquire the start claim before any wait; subsequent requests refuse without charging or spawning. |
| Preparation failure / exhausted actor pool | Bounded attempts before transport. No blank fight and no victory. Release only this generation's claims and report a useful refusal. |
| Party changes during charge | Cancel and require a fresh commitment from the remaining party. |
| World hold | Snapshot the stock spawn flag and applicable zone/director state; pause ordinary spawning and account for removed ordinary enemies using the arena's refund convention. Restore only state actually owned/changed by this encounter. |
| Card deal or world pause | Freeze AI, attack clock, impacts and relevant looping tells. On resume restart any interrupted tell, with at least one second before damage. Do not unfreeze a player or companion still owned by another menu/deal. |
| Player down/death | Target living eligible players; preserve revival opportunities and stock laststand rules. No forced teleport of a downed body at entry. |
| Stuck boss / unreachable target | Pause combat, clear hazards, move to a generated clear anchor and replay the arrival tell; preserve HP and phase. Repeated recovery failure aborts, never awards a win. |
| Boss disappears without verified death | Technical abort, not defeat. |
| Technical abort after transport | Stop all damage first, restore room/respawn/music/director claims, return surviving participants and companions to separated validated Vault positions, stamp transit and give three seconds of exit safety. Retain earned inventory. |
| Defeat | Atomic success latch; remove hazards/adds, stop attack loops, deliver one death/reward sequence, then end the run. |
| End game / disconnect shutdown | Cleanup must be idempotent and must not depend on a gameplay thread surviving its own `endon`. No post-game sounds, FX or stale state writer. |

Adapt `_tod_arena::hold_tower`/`release_tower` and teleport practices only after
auditing their assumptions. The existing arena's Keeper spawn-failure fallback
and its top-bay return are not suitable finale behavior. Likewise, old
`_tod_finale::depart` contains Crown-specific presentation; extract only a
reviewed generic victory handoff rather than invoking the dormant route whole.

## Sound, HUD and identity

Use the current Dealer voice identity from `tmp/black_market_vo/voice.json`,
as recorded in docs/198 round 8 (2026-10-02): **TOD2 The Dealer (own voice)**,
a soft, scary, dark, slightly cyber baseline with occasional manic modes
(`mode: "manic"` lines). He is his own entity: nothing of any other character.
At half health the mask cracks (one eye dark, the grin torn wider); it never
comes off.
Never duplicate the credential into a new file. Proposed new lines: invitation,
recognition, two phase changes, three attack calls, defeat, and a quiet recovery
line. Keep mandatory attack information in SFX/animation even if VO is dropped.
Use one shared per-player voice lane, with measured line lengths, cancellation
and a small explicit priority policy for finale announcements. Shop mutters
must not continue speaking over the fight.

Author a short reveal sting, three distinct tells, impacts, a restrained room
loop and a death/escape cue. Inspect loudness against the real music mix; current
music uses `snp_never_duck`, so do not promise automatic ducking or change the
global music mix to hide weak cues. The teddy-bear EE song explicitly outranks
all music and must keep that priority. Encounter music requests/restoration use
the existing channel owner, never a second overlapping stream. Combat works
correctly even while the EE song holds the channel.

One readable boss bar identifies **THE DEALER** and its phase. Hide it with the
existing HUD veil during full-screen UI; avoid covering reticles, damage feedback
or cooperative revival information. Native materials follow the shared realism
rules: worn cloth, graphite mask, purposeful normal/gloss variation and restrained
localized red emission. Matching the shop likeness matters more than adding
unrelated armor or another monster face.

## Implementation boundary and acceptance

After form approval, proposed new owners are `_tod_dealer_finale.gsc/.csc`, a
generated `_tod_dealer_data.gsc`, `tools/dealer_finale/` and isolated Dealer
character assets. Shared integration is a coordinated, reviewable change to the
generator, entry scripts, zone, damage/AI/companion/music/UI consumers and guarded
build gates. This document changes none of them.

Before a native build, execute actual controller/attack logic in the project's
case-insensitive GSC test harness. Cover solo/four-player flow, double triggers,
missing assets, actor exhaustion, simultaneous damage/death, disconnect,
pause/resume, late join, stuck recovery, abort and exact ownership restoration.
Geometry gates must prove safe routes for every supported floor pattern, arrival
clearance, hitbox/visual alignment, and attack line-of-sight. Add negative controls
for false victory and an attack landing after its cancellation.

Native gates must verify every LOD, skeleton/weight/clip binding, material/map,
compiled triangle coverage, clientfield registration, character/aitype dependency,
sound alias and packed asset. The first complete delivery includes reviewed art,
animations, cues and bounded effects under docs/155, not a placeholder reskin.
Run the guarded serialized FULL build only when BO3 is absent. Do not launch it.

Automatic `[TOD_DEALER]` dev logs should record revision and generation, entry
gates, roster/HP snapshot, state transitions, telegraph/lock/impact/cancel,
phase crossing, recovery, spawn failure, victory and restoration counts. Keep
periodic output bounded. The user tests readability, movement, class fairness,
revival, native animation/alpha/glow, audio and performance; preserve and inspect
their console log before claiming runtime verification.

Existing audit baseline: Keeper contract 243 checks, spin contract 392 checks,
and shop lifecycle/client synchronization checks pass. They protect existing
features but do not prove this proposed finale. The next decision is the Dealer's
combat form; implementation remains pending.
