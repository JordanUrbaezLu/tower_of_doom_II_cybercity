# donor_gdt — source GDTs the twin generator reads, NOT synced to Mod Tools

`tools/gen_tod_twins.js` clones weapon blocks out of these files and emits the
renamed variants into `source_data/tod_weapon_twins.gdt`. This folder is
deliberately OUTSIDE `source_data/` so `tools/sync_to_modtools.ps1` never copies
it: the Hellbound repo already installs the same files at the Mod Tools root
`source_data\`, and a second copy of the same asset names would double them in
gdtdb.

- `hellbound/hb_saug.gdt`, `hellbound/hb_car_progression.gdt` — snapshots of
  `../tower_of_doom_II_hellbound/source_data/` taken 2026-09-20 for the
  Skirmisher ladder swap (docs/153). The emitted `cc_*` weapons still reference
  the xmodel / xanim / material / image entries of those files and of
  `hb_apex_mythic_*.gdt`, which must be installed at the Mod Tools root (the
  generator preflights this and throws if they are missing).
- `hellbound/hb_apex_mythic_weapons.gdt` - snapshot taken 2026-09-23 for the
  Breacher (docs/157): the packed Peacekeeper is its `hb_am_peacekeeper` block.
  Its models / anims / tracer live in `hb_apex_mythic_models.gdt` /
  `_motion.gdt` / this file's installed copy at the Mod Tools root.
- `t7/wpn_t7_zmb_dlc3_gauntlet_dragon.gdt` - snapshot taken 2026-09-26 of the
  Mod Tools root's copy (the T7 asset pack's Dragon Gauntlet) for the Warrior's
  tier 2, the GAUNTLET OF SIEGFRIED (`gen_tod_twins.js` LADDER.slasher, read
  through `T7()`). The generator preflights BOTH copies: this snapshot is the
  source it reads, the root copy is what gdtdb converts (its clips / meshes /
  images sit under the root's `xanim_export|model_export\black_ops_3\...`).
  The Warrior's tier 1 (One Inch Punch) is NOT a donor: `tools/warrior/
  install_punch.py` pulls its clips / model / WAVs out of the T7 pack rar into
  repo-owned folders and writes `source_data/tod_warrior_punch.gdt`.
