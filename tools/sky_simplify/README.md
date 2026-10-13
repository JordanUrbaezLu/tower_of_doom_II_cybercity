# v9 sky simplification pipeline

This pass uses `tmp/sky_simplify/` and `art/sky3d/simplify_review/`. It never writes the v8 `sky_cohesion` or `cohesion_review` folders. The existing studio on port 9896 belongs to this sky task. No wrapper starts a native build or launches BO3.

## Author and review

Use the existing MCP Python environment with `mcp_call.py` and the full repository-relative script path. The client accepts only scripts under `tools/sky_simplify`. `author.py` calls current `build_city.py`, reloads its local modules, saves `tmp/sky_simplify/simplify.blend`, and records geometry source, used image/font and master hashes in `author.json`.

Optional `tmp/sky_simplify/author_config.json` selects only `sign_style` and `moon_style`; omit it to follow generator defaults. Choose the actual new title route before authoring. A fresh title report is copied alongside later renders only when the author actually wrote it. The old cyber title writes one; a new title implementation must supply its actual report rather than reuse a stale report.

```powershell
<mcp-python> tools/sky_simplify/mcp_call.py tools/sky_simplify/author.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_simplify/render.ps1 -Width 4096 -Samples 96
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_simplify/finish.ps1 -Width 4096 -Review preview4096
```

GPU rendering refuses an active BO3 match and stops its own render if a match starts. The master and geometry/art sources must still match `author.json`. Finishing stays independent, so finish-only changes do not demand another geometry render. `finish.json` pins the finish script and raw/mask/finished/stats hashes. Use `-Views` only for intermediate reviews.

After authoring, run `skyline.py` then `clearance.py` through the same MCP client. They write only `tmp/sky_simplify/skyline.json` and `clearance.json`, include station/title geometry, and never change the scene. Clearance separates `checked` active planet/ring/moon groups from policy `retired` groups, rejects missing active meshes or still-visible retired bodies, and reports the actual minimum and the 3-degree composition target. The sparse title cards are a conservative bound of their nonempty alpha tiles, not a per-pixel silhouette oracle.

Before the production render, execute `finalize_master.py` through MCP. It saves 8192 x 4096 / 160-sample settings and updates the master hash in `author.json`.

```powershell
<mcp-python> tools/sky_simplify/mcp_call.py tools/sky_simplify/finalize_master.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_simplify/render.ps1 -Width 8192 -Samples 160
powershell -NoProfile -ExecutionPolicy Bypass -File tools/sky_simplify/finish.ps1 -Width 8192 -Review final
```

Review the final panorama and views before installation. Reduced luminous area can increase the finish's solved gain: city score stays 0.64, with city knees 0.7/1 W and sign knees 2/4 W. Record the new whole-sky score and update `SKY_SCORE` through the owning integration task. Preserve roll 0, no mirror, skyRotation 40 and skyStops 4.35 unless deliberately coordinating their contracts. SSI/exposure/probe retuning is separate from composition.

## Install and build proof

`install.py` checks provenance and the complete current `VIEWS` table before writing anything. It preserves the prior installed EXR, editable master, canonical stats and v8 lightweight preview in this new pass's `before/` folder, then installs reviewed files and records `install.json`. It does not sync to Mod Tools.

```powershell
python -B tools/sky_simplify/install.py
python -B tools/sky_simplify/verify_build.py --snapshot --title-report <actual-report.json> --title-version <exact-version> --receipt <station-or-composition-report.json>
# The build owner now runs the normal serialized guarded FULL build.
python -B tools/sky_simplify/verify_build.py --build-log tmp/sky_simplify/full.log
```

Supply an actual title report with `version`, `sign_aov: sign`, `lights_city: false`, `reference_width_deg: 65`, and `title_anchor_deg: [0,11]`. Version must match the explicit argument exactly. Camera/AOV fields stay strict; a changed layout needs a coordinated cinematic update.

Leave final image conversion to the guarded build after the snapshot: proof identifies the new compiled `.iwi` against the old cache inventory. The verifier reuses v8 native checks under new receipt paths, adds new module/pipeline/art source hashes, and disables v8's historical Lucky exception. It requires fresh LED/BSP, exact geometry input/output hashes, native database bindings, both SSIs, the sky image/material/model/techset and all seven jump effects. Archive a failed attempt's log and snapshot before another attempt; never replace a snapshot to conceal a later source change.

After installation, `preview.py` creates `art/sky3d/simplify_preview.blend` and `simplify_review/preview.json`. It uses the finished HDR panorama in Rendered mode with Scene World enabled and preserves v8's `sky_preview.blend`. These previews remain approximate; native quality awaits the user.

## Dependent gates

- `jump_title/gen_fx.py --check`, `test_jump_title.js`, `test_jumppad.js`: literal GATE width/distance/elevation, title feature/color contract, reveal timing, roll and measured SSI/material bearing. The GATE regex ends at its `sat=` line. Coordinate title changes and regenerate stale art data without retiming the flight.
- `sky_ships/gen_lanes.js --check`, `test_sky_ships.js`: actual map collision lanes and the two literal black-hole definitions. Keep holes unchanged while reducing secondary sky elements.
- `art_cohesion/verify_tower_design.js`: canonical final stats and measured whole-sky `SKY_SCORE`, plus existing exposure/material rules.
- Fresh silhouette/clearance evidence must include the new station and actual title, and explicitly distinguish policy-retired bodies from unexpectedly missing active bodies. The old v8 helpers assume every listed body exists and omit the station.
- Guarded full builds also run concurrent feature gates. Respect the Lucky owner's edits; do not remove or bypass their checks.

Lighting references: [chapter 05](../../docs/162_lighting/05_sun_sky_exposure_fog.md), [chapter 06](../../docs/162_lighting/06_reflections_probes.md). The sky's distribution and color feed GI/reflections: equal mean energy does not preserve the bake. A changed image requires fresh lighting. Historical current-map tables predate today's SSIs/probes; `[TEST]` statements are not runtime evidence.
