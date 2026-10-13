# Four buildable partners

> **RETIRED 2026-10-04 by docs/209 (THE DEALER'S GIFT).** The parts, the bench builds and the equip step are
> gone: a player's first use of the Black Market gives him a random companion for free (his luck untouched).
> The crafting tables stay in the workshop wings as set dressing; the crown TEST benches are unchanged.
> Everything below is history.

Requested 2026-09-23. Implemented for `zm_tod2_cybercity` only. Native playtest
acceptance is pending; the agent must not launch a match. Build results are
recorded in CHANGELOG.md after packaging finishes.

## Player flow

Eight pieces are visible in a row beside the Vault spawn (currently
x=-2496..-2048, y=-892, z=-374). They are deliberately available immediately;
the map generator's Conduit shelf anchors remain available for a later move.
Each player collects their own copy of the two pieces for each partner. A
pickup disappears only for that player. Inventory and completed builds persist
across player deaths within the match; a fresh match starts empty.

Four labeled crafting benches occupy the new workshop wings: North = Civil
Protector, East = Talon, South = R.A.P.S., West = Cerberus. Their origins and
facing come from the map generator, shared with the bench collision clips.
The concurrent basement/workshop layout replaces the initial north-wall row.
Hold use for three seconds with both pieces. Walking away, releasing, going
down, dying, or an upgrade pause cancels assembly and keeps the pieces. After
assembly, release use and interact again to equip. Building never auto-equips.

One equipped partner per player. Built partners can be switched at their
benches. Switching preserves each partner's health. A destroyed partner rebuilds
automatically after 45 seconds; its bench cannot bypass that cooldown. Player
death removes the actor, and the selected partner returns after respawn. There
is no companion revive. A small cyan HUD bar shows health or rebuild progress.

| Partner | Role | Integrity | Attack |
|---|---|---:|---|
| Civil Protector | Armed ground escort | 1800 | AR shot every 0.48s; 750-unit range |
| Talon | Hovering escort | 1000 | Shot every 0.30s; 850-unit range |
| R.A.P.S. | One rolling crowd-control unit | 1400 | 170-unit blast, 5-second recharge; remains alive after attacking |
| Cerberus | Tracked gun platform | 2200 | Shot every 0.20s; 650-unit range |

Damage scales from round zombie health, with a 3500 per-hit ceiling. R.A.P.S.
must approach within 115 units to start a blast. All damage requires visibility;
blast victims behind solid walls are excluded. Player/partner damage is rejected.
Ordinary partner kills award the owner 50 points, full normal luck, Mage kill
mana, and the stock eligible powerup roll. Elite kills pay half the normal
elite points, normal elite luck/mana, and the existing bottle chance. Player
weapon multipliers and on-kill procs do not run for partner shots. The existing
scheduled Panzer team reward remains unchanged.

## Assets and behavior

The three scorestreak meshes are the complete BO3 models, sourced locally from
the T7 Assets V2.8 archive. Cerberus is `veh_t7_drone_amws_armored_mp_dark`.
The archive lacks some required stock multiplayer material/image dependencies.
`tools/partner/install_assets.py` therefore applies a map-owned blue enamel,
steel, dark metal, rubber, brass and cyan sensor finish. This is a reconstructed
ally finish, **not** a claim that the original MP materials were fully ported.
The Protector keeps its original skeleton, stock animations and UV materials
where available, with blue armor and an attached AK-47 world model.

Each recipe's two visible pieces are actual sections of its mesh, reduced to
34-unit pickup bounds. `model_export/tod_partner/manifest.json` pins all twelve
binaries and their bounds/triangle counts. Models/materials/aitype live in
`source_data/tod_partners.gdt`, zoned by `zone_source/tod_partners.zpkg`.
The installer writes only the repo. Guarded sync copies the one physical
`model_export/tod_partner` directory into the private tools root.

All four use an allied Protector navigation actor. Talon/R.A.P.S./Cerberus
show their own model over a hidden carrier; Talon hovers with ceiling clearance,
R.A.P.S. rolls with distance traveled, Cerberus turns toward its target. They
follow tower navmesh rather than requiring the multiplayer vehicle controllers
or a flying navigation volume (this map has none). Stuck/teleported escorts
recover to a visible point on their owner's current floor, never to a floor
behind an unopened gate. Native locomotion/pose/turning still need playtesting.

The shared companion archetype recognizes only the `tod_partner` targetname.
For these actors it disables stock reviving, powerup collecting, shooting and
dismemberment; enemy Protectors retain their existing behavior. Enemy-removal
sweeps exclude partners. Nearby zombies can target the carrier, whose
`last_valid_position` is maintained explicitly. A separate persistent invisible
shot source carries owner attribution without the aggro flag; otherwise stock
damage scoring tries player-only APIs on the robot. Death/drop callbacks are
left native, with a narrow partner reward lane.

The map's actor ceiling reserves one allied slot per player. All entities are
owned by one level manager; switches, death, disconnect and game end delete
the actor and cosmetic proxy. The attribution source survives partner swaps
and is deleted on disconnect/game end. No `level.ai_robot` singleton is used.
Upgrade pauses freeze movement and suppress outgoing/incoming damage.

## Validation and playtest

`node tools/partner/test_partners.js` executes the shipping GSC state routines
with native input calls stubbed: both parts, all four recipes, co-op ownership,
three-second hold, release-before-equip, five cancellation causes, cooldown,
cleanup, damage immunity, and generated workshop/spawn placement. The 71
assertions include native actor deletion before the manager poll: the death
notification preserves its cooldown and the orphan visual is removed immediately.
It does not emulate
BO3's runtime. `python tools/partner/verify_assets.py` validates mesh hashes,
faces, object indices, materials, bone weights, pickup bounds and the ally
aitype. Both are build gates. The asset checker accepts `--ledger <csv>` to
prove the twelve models and actor type were packed.

The geometry lint has an exception for the four measured bench clip
columns. Its destructive-negative-control selftest still catches holes,
misplaced walls and severed routes. Native nav must keep both towers connected.

`[TOD_PARTNER]` records INIT, STATIONS, PLAYER, PICKUP, BUILD_START/DONE/CANCEL,
BUILD_REFUSED, EQUIP/REFUSED, SPAWN/RETRY, DEATH, STATUS, PAUSE, RECOVER,
RAPS_BLAST and RETIRE. Cancellation logs include alive/down/pause/touch/use
state, and spawn retries report owner, location or actor count.
Records include entity IDs, type, part masks, HP, distance, target and attack/kill
counts as appropriate. During initial integration these narrow diagnostics run
in normal matches too, since `tod_dev` is false for the user's playtest; restore
the standard dev-only log gate after acceptance. Developer blocks use the
existing launcher settings. No debug menu, console command, god mode or automatic
launch was added. Capture the user's next `console_mp.log` with
`tools/capture_ai_logs.ps1`; its uppercase TOD filter already includes this tag.

First native checks: collect/build/equip each type; cancel a build; switch while
injured; watch shots/blasts and rewards; ascend stairs/teleport; pause on an
upgrade; allow a companion to die/rebuild; test two players collecting the same
pieces and equipping separately. Inspect native logs before claiming any of
these gameplay/visual outcomes verified.

This implements the user's four-choice crafting request. The separate upgrade
shop/visible armor/weapon ladder proposal in docs/156 remains future work; its
automatic free Protector grant is superseded by this crafting flow.

## Build evidence (2026-09-23)

Full map build: `tmp/partner_build_layout.log`, BUILD OK 22:56:39 Eastern.
The new basement/workshop map compiled, fresh lighting was 50,489,869 bytes,
and both towers remained connected in their respective navigation components.
All twelve partner models retained their exact authored triangle counts in
the native ledger. There were only the ten established waived asset warnings;
no partner warning was added or waived.

Final script package: `tmp/partner_build_release_2.log`, BUILD OK, fastfile
210,598,912 bytes written 23:01:38 Eastern. The final source includes the
Vault directions, destruction notification guard, orphan-visual cleanup and
cancellation diagnostics. `tools/partner/verify_deployment.py --record` passed:
41 repo/deployed files match, all predate the fastfile, and the game resolves
to the private Tower II output. Evidence: `tmp/partner_build/deployment.json`.
The fastfile SHA-256 is
`955c1c9cac7bf21911f364228e63d792ecbb5391dee6614f0f9d19eaacff99a6`.

No game launch. No gameplay, animation, visual or co-op acceptance claimed.
