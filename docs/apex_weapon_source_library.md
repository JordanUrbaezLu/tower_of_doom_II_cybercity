# R-99 / Peacekeeper source collection — 2026-09-24

Requested: collect all available data, high-resolution assets, and sounds for
both guns from the installed Apex game. This pass collects sources only;
it does not change the map's weapon roster, balance, or deployed build.

Open the local **[searchable catalog](../source_library/apex_r99_peacekeeper/index.html)**.
The full [library readme](../source_library/apex_r99_peacekeeper/README.md)
documents paths, coverage, resolutions and conversion limits. The large source
library is ignored by git; back it up separately when preserving these assets.

| Recovered | Coverage |
|---|---|
| Models | 186/186 named model assets, including view/world, cosmetic and related prop models |
| Motion | 15/15 named rigs, 643/643 named sequences; original clip hierarchy preserved |
| Images | 13,945 PNG files / 1,222 distinct payloads, including 113 resolved UI images |
| Audio | 1,551 WAV files; all 1,534 source choices from 702 weapon-related events present |
| Data | Five weapon variants, three shared behavior/pattern definitions, 284 settings and two impact tables |
| Native metadata | Loaded common/UI RPaks and patch files, original sound metadata bank/project, raw event actions |

Total exported payload: **15.97 GB**, including repeated per-model texture and
animation files. The archive contains 4,510 CAST files; neither that figure nor
the model count is a count of unique skins. There are 1,129 distinct animation
payloads, including authored blend variants and clips reached through rigs.

The base R-99 and Peacekeeper main textures are **2048 × 2048**. Some R-99
cosmetics contain native **4096 × 4096** maps: Vampire Hunter's main set,
Halloween accessory maps, and two epic camouflage color maps. No Peacekeeper
4K image was recovered. Nothing was upscaled. The old doc 157 conclusion about
native base Peacekeeper resolution still applies; this extraction alone does
not establish a fix for its appearance in BO3.

Validation passed on actual files: PNG structure/CRC, WAV structure and sample
frame lengths, bounded CAST structure, JSON parse, and selected-asset coverage.
The [tracked report](apex_weapon_evidence/summary.json) records the exact build,
counts and remaining references. Full file hashes and extraction commands live
in the local library's `evidence/` directory. This is not native-game testing.

Limits: 17 mostly historical promotional UI references did not resolve. Native
Apex particle systems and shaders are retained as package metadata, not
converted to BO3. CAST material slots have names but no image links in this
RSX build; `material_texture_candidates.json` provides explicitly inferred
filename matches. Copied RPaks still need external game StarPak streams for
fresh extraction; exported PNG/CAST/WAV files are separately available.

Reproduction: [tools/apex_weapons/README.md](../tools/apex_weapons/README.md).
Input game version `v3.0.1.28`, build
`R5pc_r5-301_J28_CL11570498_FSv30_1_2026_09_16_17_18`; extractor RSX 2.3.0.

Roster note: the current Skirmisher T3 in this checkout is C.A.R. (`cc_car`);
Breacher T3 is Peacekeeper. The user specifically requested R-99 sources,
which are collected without making an unrequested C.A.R. replacement.

No build, deployment, game launch, or gameplay changes in this pass.
