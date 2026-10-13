# Warrior - 2026-09-27 22:52 (third pass): air slam + sword-sounding punches

**Status: BUILT (guarded FULL build 23:05, FF 232,614,720 B); unplayed.**

- **Cyber Smash from the air** traces the floor, hangs a beat, then pulls you straight down and
  slams where your feet touch, whatever the height (no fall damage). Short drops are timed to
  land on the sword's swing. Knobs: `TOD_GS_DIVE_*` in `_tod_class_kit.gsc`.
- **Smash during a Bash** cuts the Bash and slams (the Bash is spent).
- **Punches sounded like a sword**: the Bash burst always played the sword hit, and the fist Bash
  proxies carried the sword's impact-sound table. Both fixed.
- Read the playtest log for `GS_DIVE_START` / `GS_DIVE_END reason=landed` (`land_ms_est` vs
  `total_ms`), `BASH_CUT`, and no `GS_DIVE_END reason=blocked` on open floor.

# Warrior playtest fixes — 2026-09-27 evening (second pass)

**Status: source ready, FULL build re-armed (`tools/necro_staff/build_when_idle.ps1`); unplayed.**
Evidence: the user's live console at 18:25 (`[TOD_KIT] BASH_*`, `[TOD_WMELEE]`).

- **Bash didn't move.** Every cast logged `travel=0 proxy_up_after_ms=-1`. The first pass's
  `FreezeControls(true)` "input lock" freezes the player's physics and weapon switching too, so
  the dash velocity did nothing and the swing never came up. It's removed. The dash direction is
  still read once at the press, and the whole velocity is rewritten along it every tick, so
  turning the view or strafing can't bend it. The camera stays free to look around.
- **Right twice.** Two causes in the log: (1) the engine queued a press from the last 0.2 s of a
  swing and started it on the same hand the instant the clip ended, before the twin swap (every
  repeat was exactly one clip later); (2) the 0.9 s idle reset returned the right hand between
  punches at the user's own 1.0–1.8 s rhythm. Fixed with a swap-window block (fire + melee off
  from the clip's last frame until the other hand is in, 400 ms watchdog), native queue 0 on all
  gauntlet forms, and a 3 s idle reset (a new combo after a real pause still starts right).
  If presses feel eaten at the end of a swing, the knobs are `TOD_WM_ALT_BLOCK_LEAD_MS` and the
  queue time in `gen_tod_twins.js`.
- **Left = half damage.** `TOD_WM_HOOK_LEFT_MULT` 0.75 → 0.5 (engine hit and crowd sweep both).
- **Jiggle after the left.** The boxing donor throws a double pump; on the way back the arm
  pushed out again (shoulder 44.8° → 38.5° → 41.0°). Re-authored through Blender MCP: the first
  punch, then a smooth ease to the idle pose by frame 16, held to the end. `verify_hook.py` now
  fails any push-back on the return; the previous clip fails it.

New logs: `ALT_BLOCK` / `ALT_UNBLOCK` (held_ms, whether locks were restored), `PRESS_BLOCKED`
(a press during the swap window). `BASH_START` now says `steer=latched`; `BASH_UNLOCK` is gone.
What to look for next log: `SWING ... hand=` alternating with no `SAME_HAND_TWICE`, Bash
`BASH_END travel=` in the hundreds, `proxy_up_after_ms` ~50.

---

# Warrior playtest fixes — 2026-09-27

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

Source ready; final script relink queued while BO3 runs. The full geometry and
fresh 166,776,956-byte lighting bake completed at about 14:42 Eastern. The native
compiler then caught an unparenthesized conditional in Bash's direction call;
that is corrected with an explicit assignment and the regression tests pass.
The guarded retry stopped at 14:47 when BO3 was reopened, before native linking.
The latest fixes are **not yet in the playable fastfile**. The idle watcher will
run the guarded `-GscOnly` relink and deployment audit when BO3 exits. No agent-run
match. Build status: `tmp/crown_alarm_visibility/status.json`.

Completed geometry/bake evidence: `full_build_attempt2_lighting.log` in that
directory. `relink_attempt3_game_reopened.log` records the safety stop. The
current attempt will write `full_build.log` and `deployment.log`. The final
deployment receipt will include BSP/LED hashes, timestamps, exact-source matches
and the new animation's compiled asset entry. User verifies native movement and
appearance after packaging succeeds.

## Evidence and changes

- **Punch Bash:** the proxy's four raise lanes already named the normal punch,
  but both idle lanes also named the attack. Removed that attack-as-idle override.
  Raise plays the ordinary 0.7-second punch once, then returns to the actual idle.
- **Facing/strafe:** Bash had no input lock and could silently steer toward a
  nearby enemy. The cast now latches the player's heading, calls native
  `FreezeControls(true)`, and releases it after the animation or interruption.
  Respawn clears an old lock; token ownership prevents an old cast unlocking a new one.
- **Air/stairs:** `driving = IsOnGround()` prevented every airborne dash. The
  floor probe also cancelled movement at ledges and uneven steps. Propulsion now
  starts in both states; air follows the latched view direction. Grounded casts
  retain vertical velocity, with assistance for walkable rises of 1–18 units.
  Wall probes and native player collision remain; absent ground is never a stop.
- **Gauntlet hook:** the imported boxing clip has 38 frames, but all visible
  `j_wrist_le`/arm tracks are static. Only separate `j_glove_*` bones move. This
  explains successful left-weapon swaps and damage with no visible hook in the
  archived run. Blender MCP retargets its shoulder/elbow/wrist rotations onto the
  native gauntlet viewhands rig. Parent-relative sleeve/finger poses preserve arm
  lengths and the fist. The new 19-frame / 30-fps clip is bound to all 12 left
  twins; the gauntlet itself stays in its own idle pose. Same lighter left damage.
- **Sword corpses:** cleanup registers its death callback before Warrior. Its
  coroutine could `Ghost()` a body under actor pressure before Warrior set
  `tod_bat_launched`. It now removes collision immediately, yields one server
  tick, then reads the launch marker. Flung bodies receive the intended 3.5-second
  visible lifetime even under pressure, then are deleted. Existing fling impulse,
  elite exclusions, ragdoll cap and ordinary corpse pressure cleanup remain.

## Diagnostics and checks

Archived input: `tmp/elite_tracking/runs/20260927_142051_666_4451e3d3/console_mp.log`.

`[TOD_KIT] BASH_START` records ground/air, locked angles and direction;
`BASH_MOVE` samples travel, vertical displacement, velocity and actual view every
100 ms during propulsion; `BASH_STEP` identifies stair assistance; `BASH_STOP`
reports a wall; `BASH_UNLOCK` records release. `[TOD_WMELEE] HOOK` names the selected
animation. `[TOD_BAT] FLING_HOLD` correlates the corpse entity with `[TOD_WMELEE] FLING`.
These report requested state and observed script values, not rendered pixels.

- `node tools/warrior/test_bash.js`: executes shipping coroutines through 75
  weapon/terrain/interruption cases, plus callback-order/actor-pressure cases.
- `python -B tools/warrior/verify_hook.py`: checks moving visible arm tracks,
  fixed arm/finger lengths, idle seams, source hashes and all native bindings.
- `python tools/warrior/install_punch.py --check`: reproducible punch assets.
- Both new regression checks are guarded build gates. Native API/arity checks
  pass. Final native compile and user appearance/physics judgment are separate.

Authoring: `tools/warrior/author_hook.py` through `tools/warrior/mcp_call.py`.
Editable scene and six phase renders: `art/warrior_hook/left_hook.blend` and
`frame_00/03/06/09/12/18.png`. MCP records: `tmp/warrior_hook_mcp`. The neutral
first-person preview uses native skinned geometry; it is not an in-game screenshot.

Test each weapon's Bash on flat ground, stairs and while jumping; try turning
and strafing throughout. Alternate gauntlet hooks, then kill a packed group with
the sword and observe body flings. The agent does not launch the game.
