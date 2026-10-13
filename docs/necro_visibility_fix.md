# Necromancer visibility and held summon — 2026-09-27

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

User brief: summoned Manglers keep the white soul aura without orange flames;
bound zombies stay suspended until transformation; Soul Pulse emphasizes the
outgoing wave and does not flash at the caster.

The Mangler aura donor contains two `gfx_fire_flame_base_2_anim_em_i1024`
emitters. Remove those complete emitters; preserve its three smoke wisps and
two soul-symbol emitters. This is a correction to the stock aura composition.

The stock animation helper blends out by clip time, not real time. A .3-second
blend on a .2083-rate clip releases about 1.44 seconds early. Rise for one second
to clip fraction .55, then replay that pose at rate zero, without automatic
blend-out. Cancellation stops the pose thread before restoring AI. A thrall
releases at conversion; a body replacement stays held through the death thread's
network frame. Log BIND_HOLD and BIND_CONVERT (scripted must be 1).

Pulse art brief: one dominant white annulus with a blue-white feathered interior
and fine broken filaments. Hollow centre. Ground height 8 units, player camera
64 units, radii 360/440/520/600. Preserve the 140 ms gameplay sweep; the wider
rim and its short trailing echo fade over 845 ms instead of 490 ms. No caster
burst, distortion, flash light or lens flare. Victim soul pulls remain.

Author the mask and editable scene through Blender MCP; inspect an oblique,
player-height preview on the crown geometry. Native integration uses two
rotated sprites, one custom 512-square RGBA texture and one additive material.
Zero dynamic lights, no loop or server host. Maximum two particles per cast;
each activation completes within 845 ms. Co-op overlap scales with casts.

Source and preview review do not prove the native look, transparency cost or
pose quality. Full guarded build follows the user's active match. The user
playtests; do not launch the game. Native verification pending.

## Source review

- `node tools/necromancer/test_visibility.js`: passed pose coroutine scenarios at
  all ten power levels, cancel/death/owner-loss cleanup, conversion guard, flame
  removal, all four pulse bands. Included in the guarded build checks.
- `python -B tools/necromancer/make_soul_fx.py --check`: passed reproducibility.
- Arity and same-VM native API checks passed (115 scripts / 8406 call sites).
- Blender MCP authored `art/necromancer/pulse/pulse.blend`; player-height phases,
  low-angle dark/bright previews and `pulse.gif` exported. No preview bloom.
- Texture centre and outer alpha edges checked. Two sprites, one material/image;
  no centre burst or light (even the legacy precached root is now a safe ring).
- The pending full build watcher snapshots these scripts, all Necromancer FX and
  the new material/texture along with the crown changes. Post-build audit requires
  the exact synced files and all four rings, material and image in the ledger.
- BO3 remained open during source work. Build/native review still pending;
  inspect `tmp/crown_alarm_visibility/status.json` for live build state.
