# 186 — The Keeper: the Battle Arena's level-10 boss

User, 2026-09-28: *"lets add him in. As the boss. He is the wave 10 in the battle
arena. His ability is he can have a soul line connected to an elite that makes
that elite way more stronger, and aggressive, and tankier. He can have 2 max.
Takes 15 seconds to cast another soul line once that elite is killed."*

The enemy is Revelations' Keeper (the robed, floating Apothicon servant). The
user picked him from the Call of Duty wiki; he is not a reskin.

## The fight

- **When:** the Battle Arena's **level 10**, **last wave** (wave 3). Waves 1 and 2
  of level 10 run exactly as on any level. `_tod_arena::boss_wave`.
- **He arrives** out of his own purple portal (stock SoE effect) at the arena
  corner farthest from the party, with a skull scream, and floats in for 1.3 s
  before he moves. On screen: `THE KEEPER HAS COME`.
- **He fights** with the stock zombie brain: chases the nearest player and
  swipes (his only stock attack). His swipe hits x1.25 on top of the arena's
  level multiplier (`TOD_KEEPER_MELEE_MULT`).
- **Health:** 36 round zombies x the level multiplier (x3.25 at level 10) x the
  party health table, through the same `hunter_hp` every arena elite uses. A wide
  boss health bar floats over him.
- **His escort:** while he lives, the wave keeps **2 elites** alive (3 with 3-4
  players), alternating Mangler and Doppelghast, one every 8 s — so he always has
  something to link. The wave's own zombies and set elites come as on any level.
- **He dies** in his native dissolve (the stock dissolve body + fade), which
  **breaks every soul line at once** and removes every buff. Every player gets
  **2000** points; the killer also gets the elite purse and a boss's luck.
- **The wave ends** as every wave does, when everything in it is dead. Then the
  normal arena win: revive, the card, back to the top bay; level 10 cleared = the
  arena is conquered.
- **If he gets stuck** (not moved for 20 s with nobody within 300), he portals to
  an arena spawn spot about 600 from his target.

## The soul lines

| Rule | Value | Define |
|---|---|---|
| Lines at once | **2** | `TOD_KEEPER_LINKS_MAX` |
| After a linked elite dies, that line may be cast again after | **15 s** | `TOD_KEEPER_RELINK_MS` |
| First line after he lands | 3 s | `TOD_KEEPER_FIRST_LINK_MS` |
| Reach | 2600 (the whole room) | `TOD_KEEPER_LINK_RANGE` |
| **Stronger:** a linked elite's hits on players | **x1.5** | `TOD_KEEPER_LINK_DMG` |
| **Aggressive:** a linked elite's move + attack speed | **x1.3** | `TOD_KEEPER_LINK_RATE` |
| **Tankier:** damage a linked elite takes from players | **x0.5** (half) | `TOD_KEEPER_LINK_DR` |

Each of the two slots links the **nearest** unlinked arena elite as soon as it is
ready. A slot's 15 s starts the moment ITS elite dies; the other line is not
affected. The buffs live on the elite as three fields and are read where they
take effect — one line each:

- `tod_keeper_dmg` — `_tod_bosses::boss_player_damage`, right after the arena's own
  "stronger hits" lane (so defensive cards still reduce it).
- `tod_keeper_rate` — the Mangler's and Doppelghast's chase loops, the one place
  each writes its animation rate every quarter second.
- `tod_keeper_dr` — `_tod_power_scale`'s front door, on the divided player hits
  only (health-derived hits and kill-intent hits stay exact, as they do for the
  /10 itself).

**What the player sees:** a steady stream of souls flying from the Keeper's chest
into each linked elite, and the Keeper's own torso glow wrapped around it. Client
side, the Necromancer's soul-stream recipe (`_tod_keeper.csc`): one actor
clientfield (`tod_keeper_link`, 1 bit) on the elite, nothing else networked.

## The assets (from the T7 asset pack)

`tools/keeper/install_keeper.py` copies everything out of
`~/Downloads/T7 Assets V2.8.rar` into repo-owned folders and writes
`source_data/tod_keeper.gdt`. **Never hand-edit its outputs; `--check` is a build
gate.** It brings: the full-body model (head included) and the dissolve body, 16
materials, 17 textures, 82 animation clips, and his own AI tables (anim mapping,
selector, state machine, behavior tree). The shared stock pieces he borrows (the
base-zombie clips, three generic textures, physics presets, his effects) were
checked against the private tools root's asset database and are already there.

What differs from the pack, and why:

- **The behavior tree loses its procedural-traversal branch.** It calls four
  functions only `shared/ai/archetype_robot.gsc` registers, which this map does
  not load (it would bring the R.A.P.S. vehicle and robot clientfields with it).
  The animated-traversal branch stays; the arena is one flat room.
- **One character, not two.** The hooded Keeper has only its preview mesh in the
  pack. The footstep FX bundle is dropped; the mist trail is played by script.
- **The glow is played by script.** A character's `fxDef` bundle only plays when a
  script calls `FxClientUtils::PlayFxBundle`; the pack's own keeper client script
  plays the three effects directly, and so does ours.
- **Three textures** (two normal maps and one colour map) have PNGs but no image
  blocks in the pack; they are written from a same-kind sibling block.
- The names are ours (`spawner_tod_keeper`, `c_tod_keeper`, `tod_keeper_body`,
  `tod_keeper_dissolve`, `tod_keeper.ai_*`); the material, texture and clip names
  stay the pack's, because the model files and the anim table name them.

His state machine and behavior tree are synced to the tools share tree
(`share/raw/animstatemachines`, `share/raw/behavior`, beside stock's
`zm_zombie.ai_asm`); his anim tables ride the usermap `animtables/` mapping like
the Mangler's.

## Diagnostics

`[TOD_KEEPER]` (dev): `INIT`, `SPAWN` (hp, spot, target), `LINK` (slot, elite, its
kind and health, distance, lines up), `LINK_LOST` (slot, the 15 s), `LINK_BROKEN`
(why, how many released), `RELOCATE` (from, to), `DEATH` (killer, team payout).
`[TOD_ARENA]`: `KEEPER` (hp, spot, party), `KEEPER_ESCORT` (alive before, wanted,
lines up), `KEEPER_FAILED` (free actor slots).

**Read after the first play:** did `SPAWN` print, did the arena log `KEEPER` then
`LINK` within ~4 s, does `LINK_LOST` fire when a linked elite dies and a new
`LINK` follow 15 s later, and did `DEATH` then `LINK_BROKEN reason=keeper_died`
fire together.

## Open / first-pass knobs

- His look is stock Revelations (dark robe, orange-red glow). A cyber recolour
  through the Blender agent is the obvious next pass if wanted.
- His only attack is the stock swipe. A ranged move, teleport or summon would be
  scripted on top of his existing clips (the pack has an unused teleport-out and
  float-emerge clip).
- Sounds are the map's own (the skull scream on arrival and death, the skull
  beam start on a new line); the pack's Keeper voice lines are not installed.
- Balance first guesses: HP 36 units, escort 2/3, gap 8 s, x1.5 / x1.3 / x0.5.
