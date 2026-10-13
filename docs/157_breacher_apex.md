# The Breacher: Mozambique -> Remington 870 -> Peacekeeper (Apex)

Requested 2026-09-23. The HEAVY class becomes Hellbound's BREACHER (docs/153's
pending "Heavy <- Breacher" row), with two Apex guns replacing Hellbound's ends:

| Tier | Gun | Base form | PaP form | Retired gun it is pinned to |
|---|---|---|---|---|
| 1 | Mozambique (single-wield) | ZeRoY `apex_mozambique_zm`, private quality model | ZeRoY legendary 02 skin (white / black / red), "Mozambique Here" | Mk 48 |
| 2 | Remington 870 MCS | Skye BO2 port (Hellbound's T2) | port's PaP, reflex removed | HK21 |
| 3 | Peacekeeper | ZeRoY `apex_peacekeeper_zm`, private quality model | Hellbound's mythic "Breach SWAT" `hb_am_peacekeeper`, "Peacemaker" | Death Machine |

User decisions (2026-09-23): match OVERALL DPS; keep OVERDRIVE's rules as they
are; legendary Apex skins for PaP; the class is called BREACHER. The internal
class key stays `heavy`, so ids, domains, VITALITY / RECOVERY / BULLET FEED and
the class speed are unchanged.

## Why the Peacekeeper's textures looked weak

Measured, not guessed:

- The donor pack's textures ARE Apex's native textures. RSX 2.3.0 re-extracted
  `peacekeeper_base_v` / `mozambique_base_v` from the installed game (evidence
  below): same resolution (Peacekeeper 2048, Mozambique 1024), mean absolute
  pixel difference 0.2-5.7 / 255. No sharper native maps were recovered for
  these base models; upscaling would invent detail. This is not a claim about
  every cosmetic: the [2026-09-24 source collection](apex_weapon_source_library.md)
  includes native 4K maps for some R-99 cosmetics, while base Peacekeeper
  remains 2048.
- The weakness was the donor's BO3 setup: images allowed picmip and streaming
  (`noPicMip 0`, `doNotResize 0`, `streamable 1`), so the view model could sit a
  whole mip down; colour/normal filtered at aniso2x and specular / gloss / AO at
  "linear (mip nearest)"; gloss range 0..17 (tight plastic highlights); the
  Peacekeeper's glow mask at `scaleRGB 1`; the Mozambique on plain `lit_weapon`.

Fix: Hellbound's ACCEPTED R-99 ID34 recipe (user: "Looks great"), applied to
private copies by `tools/install_breacher_apex.py` ->
`source_data/tod_breacher_apex.gdt`: `lit_emissive_advanced_fullspec`,
aniso8x (mip linear), gloss 0..13, emission scale 4, every image resident at
full size (`noPicMip 1`, `doNotResize 1`, `streamable 0`) with its supported
compression unchanged. The private xmodels (`tod_bra_{pk,moz,moz_pap}_{view,world}`)
point at the donor XMODEL_BINs and swap materials with `skinOverride`; nothing
donor-side is written (`model_export/apex` is a read-only junction). The
Mozambique has no glow mask, so it binds a private black one
(`model_export/tod_breacher_apex/black_ilm.png`). The PaP Peacekeeper is
Hellbound's mythic, already on this recipe. The build gates the GDT with
`install_breacher_apex.py --check`.

What this does NOT claim: native appearance. Resident textures cost texture
memory (six 2048 maps for the Peacekeeper, ten 1024 maps plus two tiny black
masks for the two Mozambique skins): 33.3 MiB measured, below. Apex shader effects are not recreated.

### RSX note

The installed RSX devel build (9de16da) and RSX 2.2.1 both crash on the
Sep 16 2026 Apex update's materials (`--loadwhitelist matl` -> 0xC0000409).
Official RSX 2.3.0 (github.com/r-ex/rsx release, zip sha256
589efc4ce8eb7185bfc936dce7def89e4b563404b3ee1112b60d60d26d3c2397) works:
`Documents/BO3_tools/RSX_2.3.0/rsx.exe`. Export and command:
`Downloads/TOD2_Apex_Breacher_Source/` (`command.txt`, `extraction.log`).

## Balance contract: overall DPS

The Skirmisher pinned per-shot DPS (dpsReference). An LMG belt -> shotgun
swap cannot: matching firing rate alone would give the class a reload every
few shots. Each form is pinned to its retired form's damage over one full
cycle (empty the magazine, reload from empty):

    sustained = damage x pellets x clip / (clip x interval + reload)

`interval` includes `rechamberTime` on the pump guns (870, Peacekeeper).
Reserves keep the retired gun's seconds of fire. Pellet falloff stays the
port's own. Emitted (generator log, checked again by
`tools/test_starter_weapons.js` from the emitted blocks):

| Form | per pellet x pellets | clip | interval | reload | overall DPS | retired |
|---|---|---|---|---|---|---|
| Mozambique | 545 x3 | 3 | 0.358 | 2.60 | 1335 | Mk 48 1335 |
| Mozambique Here | 621 x3 | 4 | 0.286 | 1.95 | 2407 | 2409 |
| Remington 870 | 562 x8 | 8 | 0.742 | 5.70 (shells) | 3091 | HK21 3089 |
| Refitted-870 | 356 x12 | 10 | 0.594 | 2.21 | 5243 | 5242 |
| Peacekeeper | 606 x11 | 6 | 0.860 | 3.50 | 4618 | Death Machine 4619 |
| Peacemaker | 736 x11 | 8 | 0.688 | 2.63 | 7968 | 7965 |

Reserves: 20 / 7 / 6 magazines. The PaP pump guns rechamber 25% faster
(the generator never scaled `rechamberTime`; the pin sets it to base x 0.8).
Consequence the user accepted: much harder hits per pull, paid back in reloads.

The heavy's sidearm ceiling is untouched: the Mozambique carries the Mk 48's
recorded T1 reference (`capReference`), and the RPG / Nail Gun blocks came
back byte-identical (every non-Breacher block in the twins GDT is unchanged).

## Everything that moved together

- `tools/install_breacher_apex.py` (new) -> `source_data/tod_breacher_apex.gdt`,
  `model_export/tod_breacher_apex/black_ilm.png`,
  `docs/breacher_evidence/install_manifest.json`; synced by `sync_to_modtools.ps1`
- `tools/gen_tod_twins.js` - LADDER.heavy (three rungs), `BREACHER_RETIRED` +
  `gunCycle` + the sustained branch in `computeTierOverrides`, per-form
  `form.src` (`formText`), retired stems in the CSV sweep (and the sweep's
  `.sort` moved out of the comment that had swallowed it)
- `donor_gdt/hellbound/hb_apex_mythic_weapons.gdt` - snapshot (docs/153 rule)
- generated: `source_data/tod_weapon_twins.gdt` (243 -> 239 blocks; 207
  generated, and 24 fixed once the raw Mk 48 zone lines went = 231 / 235), `zone_source/tod_twins.zpkg`, weapons CSV
- `_tod_classes.gsc` - register_class "BREACHER", three register_gun lines,
  `[TOD_BREACHER]` give log (`TOD_BREACHER_LOG`, zero before a publish)
- `_tod_upgrades.gsc` - set_guns penetration (Mozambique + Peacekeeper),
  overdrive (Peacekeeper), suppress (870)
- `sound/aliases/tod_ports.csv` - 51 Mk 48 / HK21 / Death Machine rows out; the
  Mozambique, Peacekeeper, mythic Peacekeeper, 870 and their shotgun decay
  tails in. The Apex rows were gated on `water over/under` and the decay tails
  on `ringoff_plr` - contexts this map never sets (the staff-reload trap), so
  the `over` / `outdoor` takes keep their rows with the gate cleared and the
  rest are dropped. WAVs vendored under `sound_assets/`.
- UI: class picker text, tier card ladder, pause detail rows (870 / Peacekeeper),
  HUD icon + display-name tables (placeholder shotgun cells: executioner /
  spas12 / mog12)
- `docs/armory.html` data rows; `docs/staff_approved_manifest.json` 239;
  `tools/test_starter_weapons.js`; `tools/build_map.ps1` gate

## Known placeholders

- Class card / medallion / tier-card art still show HEAVY and LMGs.
- HUD gun icons borrow the Executioner / SPAS-12 / Mog 12 pictures.
- `docs/armory.html` analysis prose (rank tables, "the heavy is fine") still
  reasons about the LMGs.
- OVERDRIVE counts 10 rounds per stack; on a 6-round Peacekeeper it barely
  ramps (user's call to leave it).

## Build and test status

- Full build (geometry, navmesh, fresh LED 45,149,178 B, link) BUILD OK
  2026-09-23 15:48:36 Eastern, after a peer Map One build in the shared
  install had exited. Then the raw `t6_mk48` / `_up` zone lines were retired
  (nothing named them; their sounds were gone): -GscOnly BUILD OK 15:54:56,
  FF 209,707,072 B, sound bank 197.9 MB (full size), ledger 207 + 24 = 231 / 235.
- Only the 10 known-waived linker errors. scripts / ui / zone_source / sound
  diffs clean against the deployed tree; nothing synced after the `.ff`;
  repo GDTs == deployed GDTs.
- Asset list: 14 `cc_*` Breacher weapons, all 27 `tod_bra_*` assets, the
  mythic `hb_am_peacekeeper_*` set, zero `t6_mk48` / `t5_hk21` /
  `t6_death_machine` rows.
- Compiled images: all 18 `i_tod_bra_*` maps resident at full size, 0 bytes
  streamed (Peacekeeper colour 5,592,521 B = 2048 + mips; Mozambique colour
  1,398,218 B = 1024 + mips). Cost: 33.3 MiB resident texture memory.
  Evidence: `docs/breacher_evidence/` (compiled_images.json, both build logs,
  install manifest).
- No game launch. UNPLAYED - the user tests.
Look for `[TOD_BREACHER] GIVE` lines in console_mp.log: one per hand-out, with
the form, ammo after the give and the camo index.
