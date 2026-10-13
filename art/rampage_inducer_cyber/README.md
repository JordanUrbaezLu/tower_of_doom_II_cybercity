# Cyber Rampage Inducer

Since docs/208 (2026-10-04) this map's Rampage Inducer is map 1's **cyber
inducer** (its v19.68m, 2026-10-02), carried here byte for byte: an armoured
plinth with a RAMPAGE display and a 5-step meter, a copper power coil over a
glowing core, four bowed ribs caging a levitating Fury crystal cluster in a
scrolling plasma column, finned crown with four claws and a beacon. 44 x 44 x
67, front on local +X, one model with five animated bones (54,370 triangles,
one LOD, one 2048 atlas). It replaces BO6's essence canister (`tod_inducer`),
whose GDT and model files stay on disk, unzoned, as the rollback.

## Two states, one mesh

OFF wears cyan standby trims and a dim amber core; ON (`tod_inducer_cyber_on`,
a skinOverride of both materials) turns every trim rampage red and the core a
hot orange burn. Two looping clips run on its bones: idle 12 s (the crystal
turns and bobs, the shards orbit, the halos counter-spin, the beacon sweeps)
and on 3 s (four times faster, the crystal shivers, the beacon sweeps like an
alarm). `_tod_rampage.gsc` plays them (`#using_animtree( "tod_inducer" )`) and
re-plays after every model swap. Every flip plays the device's own ON / OFF
sting (`tools/rampage_sfx/`, map 1's v19.68x), from the device.

## Where it stands

On the crown's jump-pad BALCONY while the jump pad is live (the base arena's
south wall otherwise). The generator cuts its collision there: a 42 x 42 body
clip 40 tall and, 20 above it, a steep cap that rises away from the pad, so
nothing can stand on top of it; the centred use-trigger rides in the slot
between them (`crown_inducer_trig_lift()`).

## Files

| File | What |
|---|---|
| `install_manifest.json` | map 1's install manifest, copied whole (hashes, faces, bones, bounds, the clips) |
| `rampage_inducer_cyber.blend` | map 1's editable master (provenance) |
| `game_preview/`, `review/` | map 1's renders of the master and of the shipped binaries posed by the shipped clips (not game screenshots) |
| `model_export/tod_inducer_cyber/` | the xmodel_bin and nine images |
| `xanim_export/tod_inducer_cyber/` | the two clips (`.XANIM_BIN` linked, `.XANIM_EXPORT` their source) |
| `source_data/tod_inducer_cyber.gdt`, `animtrees/tod_inducer.atr` | the assets and the animtree |
| `tools/inducer_cyber/anim_spec.py` | the motion spec the clips were made from |

`python tools/inducer_cyber/verify.py` (a build gate) holds all of it to the
manifest and checks the zone, the script, both generated trigger lifts and the
body clip + cap; `--compiled-ledger` (post-link) proves both models linked whole.

## Rebuild

Map 1's `tools/inducer_cyber/` stages (the live Blender MCP studio, export,
install) hardcode map 1's repository and the shared Steam tools. NEVER run them
as they are from here: port them with their paths pointed at this tree and the
private tools root (`C:\BO3Tools\TOD2Cybercity`), then copy the new manifest with
the outputs. A model / GDT / clip change is a FULL build.
