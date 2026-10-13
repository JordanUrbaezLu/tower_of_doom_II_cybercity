# Fire Bow material restoration — 2026-09-27

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

User supplied an original BO3 fire-bow screenshot and the Tower II comparison.
Target is the original lava/black-rock appearance, not a new interpretation.

## Cause and correction

Tower II inherited `hb_fire_bow_rune_*` models. Their vertices, weights and
skeletons match the original bow, but four surfaces use replacement materials:
`lit_emissive_advanced`, `colorMap00 = stone albedo`, `scaleRGB = 3`. This makes
the stone itself glow grey/orange and removes the original lava layers.

The original `wpn_t7_zmb_bow.gdt` uses `lit_emissive_scroll_3layer_plus`, two lava
layers, a separate `_e` mask, original UV/motion constants and HDR scales of
256 (body/handle/rocks) or 1024 (arrow). Its `i_t7_camo_zod_pap_e3` image is absent
from the private asset database. The PNG is present in the original downloaded
`hb21_elemental_bows_v1.0.0.rar`.

`tools/archer_assets/restore_fire_bow.py` writes four map-owned material twins,
preserving every original field except the name of the recovered lava image.
That image is registered with its original PNG bytes. Three map-owned model
twins use the original meshes and skin those four surfaces with the restored
materials. No original source or shared tool input is modified.

All eight base/PaP/Deadeye forms select the restored view, world and projectile
models. Before/after weapon comparisons show exactly those three binding changes
per form; damage, timing, animations, sounds, quiver and effects are unchanged.
The two installed persistent rock/ambient FX match the archived package byte
for byte. The lower/upper rock attachment bones exist in the original view rig.

This is a restoration of original native assets, not custom-authored effect art.
No additional emitter, script loop, light, host or clientfield is introduced.

## Evidence and status

- Original package extracts: `source_library/fire_bow/original/`.
- Generator: `tools/archer_assets/restore_fire_bow.py`; output
  `source_data/tod_fire_bow.gdt`, `model_export/tod_fire_bow/`.
- `verify_fire_bow.py`: exact material recipes, 21 resolved image files, original
  rigs/vertices/weights and persistent effects, eight weapon forms. Required by
  the guarded build; post-build mode requires all restored assets in the ledger.
- `art/fire_bow/source_receipt.json` records actual source/image/model hashes.
- Expected roster and starter-weapon balance checks pass.
- User console archived at
  `tmp/elite_tracking/runs/20260927_141311_082_54c4c963/console_mp.log`.
- Full build queued with the crown and Necromancer changes while BO3 is open;
  `tmp/crown_alarm_visibility/status.json` reports the actual state.

Native compilation and the user's in-game comparison are still pending. The
source restoration does not establish an exact screenshot match: map exposure,
render settings and the original port's fidelity can still affect the result.
Build and stop; never launch the game unasked.
