# Teleporter status color correction — September 26

The user accepted the repaired metal surface and explicitly rejected pink:
power off means no light, ready is green, pending is animated yellow.
The prior pink-ready texture and cyan/violet status effects are superseded.

BUILT AND DEPLOYED in Archer's FULL build 16c, completed September 26 at 23:00
Eastern (FF 196,651,712 bytes). `record_palette_build.py --build-log
tmp/lead_build/build16c.log` passed: native yellow tints/brightness/depth,
packed status FX, all compiled LODs and source/deployed hashes agree, with no
post-FF sync. Receipt: `deployment.json`; audit log:
`tmp/teleporter_green_deployment.log`. No build or game launch by this session.
New colors remain unplayed; the user tests. The old build fails the receipt
gate, recorded in `tmp/teleporter_old_palette_negative.log`.

`../states_review.html` shows three native-input Blender renders and a six-second
clip with one complete yellow revolution. The editable master was corrected
through actual Blender MCP on port 9879. `native_states.blend` reconstructs the
shipping model, atlas and recharge mesh; shading is an approximate fullspec
preview, not native game lighting. It is open in the teleporter studio.

The palette source is `tools/teleporter/state_palette.json`. Ready strips,
ready FX and release overlays are green; the charge overlay and chase are yellow.
The original stock electrical teleport bursts remain. Model shapes, all seven
body LODs, recharge mesh, original five body maps, satin finish, explicit zero
emissive depth, trigger/placement and 0.8-second charge/60-second cooldown stay
unchanged. Reproduction: MCP 04_power_states, MCP 05_export_states,
install_states.py, generate_fx.py, MCP 11_palette_preview, background
12_render_palette, then encode status_colors/frames at 10 fps.

Power or explicit shutdown hides all model emission and the chase. Powered
destination locks, cooldown and card-pick pause use the same pending animation.
Only one extra chase model exists per pending pad; reason changes reuse it.
Ready/off delete it. Models spawn dark before their availability owner runs.
The shared spawn_beam helper remains compatible with the always-live jump pad;
the transit/crown controllers retain power gating. Automatic transition logs:
`[TOD_TELEPORT_STATE] rev=2 palette=green_yellow`, with origin, from/to, reason
and chase presence. No per-frame logs.

Checks passed: native source/LOD/material manifests, actual GSC state transitions
and host lifecycle, all 4,194,304 atlas pixels, green hue and original glow mask,
native yellow tints, all status FX color curves, accepted mesh/map hashes, arity,
native API and FX paths. `before.json` retains pre-change hashes. A compression
backend difference initially rewrote the recharge binary identically in geometry;
the installer now preserves its original bytes when decoded content is identical.

The preceding console is archived at
`tmp/elite_tracking/runs/20260926_224522_687_07c8f71f/console_mp.log`. Its old logs
show all eight pads off at 26,450 ms and ready at 62,450 ms. Those records support
the existing state flow; they are not a test of this new palette/revision.

User test after the build: view an unpowered pad, power it on, use it and watch
the yellow chase through recharge until green returns. Check a locked destination
and a card-pick pause, then inspect the console for rev=2 palette=green_yellow.
