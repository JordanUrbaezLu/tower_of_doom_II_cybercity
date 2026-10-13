# Dealer weapon pass

The Dealer's House encounter now has two additional attacks. State one carries the
Wunderwaffe, marks up to four fixed player positions, warns for 1.8 seconds and shocks
the marked ground. State two raises the Dingo, warns for 1.3 seconds, then fires six
rounds at a fixed aim point. Moving out of the ring dodges either attack. Walls block
damage; a barrel through cover cannot fire. Only the marked footprint can receive a
burst hit, including in co-op. Overlapping shock marks hit each player once.

Base damage is 30 for shock and 8 per bullet before player defenses. Dealer's House
leaves the generic arena damage multiplier off. The Dealer's 1.25 swing multiplier
applies only to melee. New ranged
attacks wait six seconds after dialogue or a pause/stun releases, then use eight-second
shock or five-second burst cooldowns after recovery. Existing melee behavior remains.

The native animation clips author both hands onto the firearms and preserve his
floating first state and grounded second state. They play at authored speed; recoil,
weapon reports and effect replication use the same timing. The shipping character
master, core 45 clips and material/export receipts are preserved.

Pause, dialogue hold, EMP, Bash stun, freezing, phase change and death withdraw an
attack. Old generations cannot restore the new phase's weapon. Every effect uses
the existing finite carrier pool. Failed warning, impact or tracer allocation causes
no invisible damage. Cloaked, downed, disconnected and cinematic players are excluded.

The warning/discharge/muzzle/tracer compositions use existing native stock sprites.
The editable Blender review adds matching geometry to show footprint and timing; it
does not emulate BO3 particles or its lighting. One small shadowless charge light is
added. At four players, a shock adds at most 104 warning or 152 impact particles,
separate from the existing aura. Runtime cost and appearance remain unplayed.

Four new measured, finite sound cues have two retained generated takes each. There
is one shock report per cast so overlapping co-op marks cannot stack identical audio.
No voice clone or Dealer voice change belongs to this pass. The full death line now
finishes before the arena victory/cards screen.

## Authoring and review

`tools/dealer_boss/18_combat_clips.py` authors the two native binaries through the owned
Blender MCP studio into `tmp/dealer_combat_stage/`. It derives transforms from the
actual skeleton, raw clips and weapon muzzle tags, solves both arms, and round-trips
the native files. `17_combat_review.py` poses those exact binaries with real weapon
meshes. The shipping master is never saved over. Source/binary/preview pins are in
`xanim_export/tod_dealer/combat_clips.json`.

`tools/dealer_combat/gen_fx.py` reproduces the five native effect files;
`make_sounds.py --check` validates the selected WAVs and aliases without API access.
The initial `prepare.py`, `stage_wiring.py` and `land.py` stage and land this complete
change, checking all shared originals and refusing active builds/native stages.
They are initial delivery helpers, not commands to rerun over an already landed tree.

Review: `art/dealer_combat/review/review.html`, four contact frames and
`dealer_combat.blend`. Open the correct scene-lit Rendered camera with
`tools/dealer_combat/open_preview.ps1`. The separate reviewer approved code/art
evidence; this is not a native playtest.
The actual owned Rendered window is recorded in `review/visible_window.png/json`
and `review/visible_preview.json`; the accepted native delivery is archived under
`art/dealer_combat/deliveries/20261008_152049/`.

## Validation and playtest

The guarded build runs `test_combat.js` (60 checks, including actual shipping math
and three planted regressions), `check_assets.py`, sound and FX gates. Every effect
curve must have strictly increasing key times; two negative controls reject repeated
or reversed keys. A mandatory post-link gate requires all five resident effect
definitions and no linker complaint naming this set. The old Dealer
installer also reproduces the new mapping aliases; its core asset contract includes
the independent combat sidecar GDT. Source guidance and all native gates stay active.

Logs use the existing `[TOD_DEALER]` dev lane: `ATTACK_BEGIN`, `ATTACK_TELL`,
`ATTACK_FIRE`, `ATTACK_HIT`, `ATTACK_END`, with generation, operation, kind and
failure/cancellation reason. `[TOD_HOUSE] DEATH_LINE_COMPLETE` confirms the final
word before rewards. Capture a user test with `tools/capture_ai_logs.ps1`.

The user should check both weapons, move out of a warning, use cover, pause/stun
during a warning, cross half health during an attack and hear the complete death
line before the cards. No game was launched by the authoring session.

Delivery evidence is recorded in `art/dealer_combat/build.json` after the guarded
FULL build and native ledger, source parity and sound-bank audit succeed. Frozen
inputs are pinned in `art/dealer_combat/delivery_inputs.json`. The earlier build
reported success but omitted the charge effect after a curve rejection; that
unaccepted delivery and its error log are preserved under
`art/dealer_combat/deliveries/20261007_charge_rejected/`.
