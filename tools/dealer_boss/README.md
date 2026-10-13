# tools/dealer_boss - THE DEALER, the final boss (docs/199)

Everything here authors, reviews, exports and installs the Dealer boss character. The record of
decisions is `docs/199_dealer_boss.md`; the encounter rules are `docs/dealer_finale_design.md`.

## The studio (visible Blender 4.2, MCP port 9899)

    .\tools\dealer_boss\start_studio.ps1          # guard, then a VISIBLE window; nothing opened yet
    python tools\dealer_boss\mcp_call.py tools\dealer_boss\00_open_master.py   # after a restart: load the master

`mcp_call.py` sends one script at a time (`python mcp_call.py screenshot` grabs the viewport). Use the
MCP python environment named inside it. Every step saves `art/dealer_boss/dealer_boss.blend`.

| Step | Builds / does |
|---|---|
| `01_rig_reference.py` | the Keeper skeleton from its XMODEL_BIN, the Keeper ghost, stage, cameras, `skeleton.json` (RESETS the scene) |
| `02_coat.py` | trousers, boots, the open-front coat, front panel + toggles, mantle, sleeves, cuffs, straps, belt |
| `03_head.py` | the void, neck, THE MASK (the shop's construction), the hood, drawstrings |
| `04_hands.py` | gloves along the finger bones, knuckles, the ten red nails |
| `05_gear.py` | bandolier + vials, satchel, belt chain + keys, tokens, throat chain |
| `06_lighting.py` | the stage lights and the six review cameras (re-runnable) |
| `08_review.py` | renders every camera to `art/dealer_boss/review/` (`CAMS`, `TAG`, `SAMPLES`, `STATE` globals; `STATE = 2` = the cracked mask) |
| `09_pose_check.py` | poses the rig with real Keeper clips and renders (`POSES` global) |
| `10_state2_mask.py` | STATE TWO = THE CRACKED MASK (2026-10-02): chipped shell, dead right eye, burning left eye, fissures, the torn fanged grin, the snapped strap; tagged `state2_only` (`SHOW_STATE = 2` shows it; `review_state(n)` in studio.py) |
| `11_weapons.py` | the scythe (ours) + DG-2 and Dingo previews at `tag_weapon_right` (`SHOW_WEAPON` global) |
| `16_head_review.py` | head close-ups of both mask states aimed at the posed head bone (`art/dealer_boss/review/head/`; `TOD_REVIEW_OUT` overrides) |
| `anim_preview.py` | `pose_frame` / `load_action`: an XANIM_BIN onto the armature, root motion removed |

Set `TOD_DEALER_MASTER_OUT=<path>` to make `save()` write a STAGED copy instead of the master (author while a peer build's
gates still read the shipped master's sha; swap it in afterwards). Pass a global by prepending a line, e.g. `printf 'SHOW_WEAPON = "dg2"\n' | cat - 11_weapons.py > _11b.py`
and send `_11b.py` (scratch files are deleted afterwards). Steps 02-05 rebuild their own collection
from scratch; 02 purges the material library only when it is missing or `REBUILD_MATERIALS = True`.

## Native pipeline

    python tools\dealer_boss\stage_donors.py                 # DG-2, Dingo out of the T7 pack -> art/dealer_boss/donors (nothing else: he is his own face)
    blender -b art\dealer_boss\dealer_boss.blend --python tools\dealer_boss\export_native.py   # one bake -> masked + cracked bodies + scythe, 7 LODs each
    python tools\dealer_boss\install.py                      # source_data/tod_dealer.gdt, AI tables, 28 clips, donor materials
    node  tools\dealer_boss\test_dealer.js                   # the contract gate
    python tools\dealer_boss\wire.py                         # SHARED files - run right before the build (WIRE LAST)

`export_native.py` and `start_studio.ps1` run `process_guard.py`: a Radiant bake, cod2map, gdtdb or the
game holds everything; a linker holds exports and renders only. Never close another map's process.
