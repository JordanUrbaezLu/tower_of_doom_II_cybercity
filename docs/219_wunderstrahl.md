# 219 - THE WUNDERSTRAHL (the laser wonder weapon)

STATUS: BUILT, UNPLAYED (FULL BUILD OK 2026-10-06 10:10, FF 213,508,864 B; the evidence is in docs/status_log.md).
This doc is the source of truth for the pass.

## The request

User, 2026-10-05: *"I want something like a laser. Like a really super strong laser gun ... maybe if like we could use the
Wonder Waffle, but it shoots like a crazy detailed, awesome laser. And it's like an automatic laser. So you can hold it
down ... like a bullet where it's like a laser down the middle, and then kind of swirls that swirl around that laser, with
little balls on the swirls. So you know, kind of like a, a like aura beam almost ... I want it to be unique here on this
map."*

Decisions (asked the same day):

| Question | Answer |
|---|---|
| How players get it | **Shares the Gift of Death drop**: the Death Machine slot hands out the Gift of Death OR the Wunderstrahl, 50/50. Big-weapon drops do not get more common. |
| Beam colour | **Yellow core.** The swirls and orbs stay in the same warm family (gold swirls, white-yellow orbs with amber halos): a golden aura beam. |
| Holding | **No overheat.** Hold it for the whole window. |
| Name | **Wunderstrahl** ("wonder beam", the DG-2's laser sibling). |

## The experience, moment by moment

1. **The drop.** When the Death Machine slot comes up, half the time a Wunderstrahl drop appears instead of the Gift of
   Death: a gold miniature of the gun (the drop family, stock `mtl_x2icon_gold`) with the stock power-up glow. The player
   can see which weapon they are about to take.
2. **The grab.** The stock grab sound plus a short power-up charge. The class gun goes away exactly as it does for the
   Gift of Death, and the Wunderstrahl rises with the DG-2's own first-raise animation, its bulbs and glass core lit
   yellow. The power-up tray shows the Wunderstrahl icon counting down 30 seconds and flashes near the end, like every
   timed power-up.
3. **Firing (hold the trigger).** Ignition: the DG-2 recoil kick, a bright flare at the lens, a rising charge sound. Then
   the beam: a thin white-yellow core, gold swirl strands spiralling around it, small glowing orbs riding the swirls
   outward, a continuous hum-scream (2D for the shooter, 3D for everyone else). The gun trembles while it fires.
4. **Hitting.** The beam reaches about 2400 units and stops at walls. At the wall: molten sparks, a scorch glow, orbs
   splashing, a sizzle loop. Zombies along the beam are **pierced**: every one in the line sizzles and dies after about
   0.3 seconds of contact, on any round, bursting into embers and ash with a yellow flash. Elites melt in about 3
   seconds. Bosses take heavy but capped damage. Normal hit markers (kill confirm) on every hit.
5. **Releasing.** The beam snaps off at once, with a power-down whine and a fading glow at the lens.
6. **The end.** At 0 seconds the gun powers down and the class gun comes back (the stock weapon power-up lane).

Every exit path: going down takes the gun (stock's spare Wunderwaffe last-stand hook), death, disconnect, a re-grab
refills the timer to 30, the class terminal refuses ("hands"), the PaP drop refuses, a card deal freezes the world (no
damage while paused), a jump-pad flyer deals no beam damage, a Black Market spin freezes the player. Co-op: every
player sees everyone's beam (the engine's third-person beam on the world model); damage belongs to the shooter.

## The technique

**The weapon is a native BO3 beam weapon** (`gasweapon.gdf`, `weaponType gas`), the type the Purifier and the
Gauntlet of Siegfried's dragon breath use. While the trigger is held the engine draws `flameBeamFirstPerson` from the
viewmodel's `tag_flash` and `flameBeamThirdPerson` from the world model's, stops it at the first solid, and plays its
effects. `unlimitedAmmo 1`, no overheat. The GDT deals no damage; the script does (below). Proven in-engine by the stock
gauntlet and by the community WaW flamethrower port (a primary-inventory gas weapon with `unlimitedAmmo 1`).

**The beam asset** (`beam.gdf`, `deffiles/beam.awi`; `tools/wunderstrahl/fx/make_fx.py`, its README has every
number): a camera-facing RIBBON core (every stock beam texture with a bright axis rides a ribbon; `BEAM_SHAPE` is the
one switch back to a hexagon tube) with our scrolling white-hot-to-yellow laser material, rigid (virtual target 2400,
no mass), launched at 6000 u/s and retracted instantly. `beamEffect` is the swirl (`fx_ws_aura_1p` / `_3p`): a gold
double helix with orbs spiralling along it, spawned every 36 u (68 u in 3P) and carried outward. `originEffect` is the
lens flare (`fx_ws_origin_*`), `blockedEffect` the wall burn (`fx_ws_impact` + the `tod_ws_impact_loop` sizzle),
`targetEffect` a fizzling tip at an open end (`fx_ws_tip`), `deathEffect` the lens cooling (`fx_ws_lens_cool`).
Collision mask `shot and not body`, so the visible beam passes through zombies (it pierces) and stops at walls,
which matches the damage. The weapon's flame table (`tod2_ws_flametable`) draws nothing and carries a warm travelling
light: both working player beam weapons on record fill that field, so an empty one is the unproven path.

**The kills' effects** ride the module's own carriers (`fx_at`: a tag_origin host, two frames to replicate, then
PlayFXOnTag, then the host deletes itself). They are authored as loops that land one round inside the carrier's life
(a server one-shot renders nothing). A kill streak is budgeted per holder per second: the lit disintegration four
times, then the unlit one (`fx_ws_disintegrate_nl`) eight times, then the zap sound alone. A twenty-kill line never
raises twenty lights.

**The damage** is script, authoritative and round-independent, like the Gift of Death. While the player `IsFiring()`
with the Wunderstrahl, every 0.1 s: a world trace from the eye along the view finds the wall; every enemy within the
beam radius of that segment takes a tick. Horde: max health / 3 per tick. Elites: max health / 30. Bosses: a small
fixed fraction. Insta-Kill multiplies the horde tick. Rampage stretches every time-to-kill by its HP multipliers
(rampage is the hard mode). The power scale exempts the weapon by name (the damage is already in the new units). No
damage while `level.tod_upgrade_pause`. Kills pay through the stock death path; hit markers come from kill confirm.

**The model** is the BO3 Wunderwaffe DG-2 (The Giant) from the T7 Assets V2.8 dump on this PC, remodelled through
Blender MCP into the Wunderstrahl: a focusing lens and emitter rings around the existing `tag_flash` (41, 0, 3.14), a
yellow laser core in the glass tube, yellow bulbs, neon conduits, finished worn surfaces. The view rig keeps the DG-2's
12 bones and the world rig its 4, so the DG-2's 26 first-person clips play unchanged (`tag_flash` stays where the clips
expect it: moving it would mean editing every clip).

## Names

| What | Name |
|---|---|
| Weapon | `tod2_wunderstrahl` |
| Power-up | `tod_wunderstrahl` (tray clientfield `tod_wunderstrahl`, vars `zombie_powerup_tod_wunderstrahl_on/_time`) |
| Models | `tod2_ws_view`, `tod2_ws_world` (+ LODs), `tod2_ws_pickup` (the gold drop) |
| Clips | `tod2_ws_vm_*` (the DG-2 clips, renamed) |
| Beams | `tod2_ws_beam_1p`, `tod2_ws_beam_3p` |
| Effects | `tod/wunderstrahl/fx_ws_*` |
| Sounds | `tod_ws_*` |
| HUD | `i_tod_pu2_wunderstrahl` (tray), `i_tod_hud_gun_wunderstrahl` (gun bay) |
| Script | `_tod_wunderstrahl.gsc` / `.csc`, log tag `[TOD_WS]` |

## How the pass lands

Every file under a synced or gated path (source_data, share/raw/fx, sound, sound_assets, scripts, ui, zone_source,
gamedata) is generated into the stage `tmp/wunderstrahl/stage/` (repo layout) first and landed in one step, with the
shared files (`_tod_powerups.gsc`, the entry scripts, the zone, `sync_to_modtools.ps1`, `build_map.ps1`, the HUD Lua)
wired last, right before the FULL build. New non-synced folders (`model_export/tod_wunderstrahl`,
`xanim_export/tod_wunderstrahl`, `art/wunderstrahl`, `tools/wunderstrahl`) are written directly.

Tools (`tools/wunderstrahl/`): `collect_sources.py` (the DG-2 kit out of the dump, hashed), the Blender MCP studio
(`mcp_bootstrap.py` / `mcp_call.py`, author / render / export steps), `make_fx.py`, `make_sounds.py`, `install.py`
(the GDT + zone), `test_wunderstrahl.js`. Each generator has a `--check` gate in `build_map.ps1`.

## Logs

`[TOD_WS]`, gated `( tod_dev || tod_diag )` plus `TOD_WS_LOG` for the user's run: INIT, DROP (which side of the shared
slot), GRAB, GRANT, REFILL, FIRE_ON / FIRE_OFF (with the firing lane and burst totals: ticks, hits, kills), END (reason),
LASTSTAND, REFUSE.

## The sounds (tools/wunderstrahl/sound/make_sounds.py)

14 aliases, 18 wavs, levelled against their stock analogues (the Gauntlet's held beam, the DG-2's own idle):
`tod_ws_fire_start_*` (ignition), `tod_ws_fire_loop_*` (the hold: a 65 Hz sine under a 130 Hz stack, a circling pan
for the swirl, the DG-2 hum and fizz under it), `tod_ws_fire_stop_*` (release), `tod_ws_impact_loop` (the wall burn),
`tod_ws_hit` / `tod_ws_kill` (3 variants each), `tod_ws_raise` / `tod_ws_putaway` (custom notes on those clips),
`tod_ws_grab`, `tod_ws_expire`, `tod_ws_idle_loop` (the held hum, on its own carrier). The review reel and levels:
`art/wunderstrahl/sound_review/`.

## Open risks (to read in the user's first log)

- `IsFiring()` on a gas weapon: stock calls it once. The damage loop logs which lane saw the beam and falls back to the
  attack button with the gun up if `IsFiring()` never reports.
- The `shot and not body` mask on a beam: if the beam stops at the first zombie, the visual is short of the damage.
- The one new `toplayer` clientfield (2 bits) for the tray, beside Zombie Blood's.
- The native look as a whole (tools/wunderstrahl/fx/README.md lists each assumption): the beam's brightness against
  this dark map, yellow vs white, whether the swirl's instances are born at the lens or fill the beam at ignition,
  the wall burn's orientation, whether the deathEffect plays, and whether the flame table stays invisible.
