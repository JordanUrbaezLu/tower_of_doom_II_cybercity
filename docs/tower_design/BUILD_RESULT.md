# Combined map build — September 27, 2026

FULL build and script follow-up passed. The game was not launched; native gameplay and appearance
still need the user's playtest. Fastfile written **2026-09-27 10:45:04 -0400**.

The user retired Archer's lead role. Normal development no longer requires
Archer approval. Guarded builds remain serialized and respect a running game.

This build includes the brighter sky, crown-family tower materials, 240 new
powered stair light pools, 24 fixed broken drops, the top transit bay and the
bottom-to-crown pair. Shared arena changes are preserved: floor 40 is its
chamber, with regular top-bay links at 30, 20 and 10 (eight directed routes).

Map: 10,624 world brushes, 2,756 entity records,
584 lights. Crown geometry and existing class work are preserved.

| Compiled output | Bytes | Written (UTC) |
|---|---:|---|
| fastfile | 196,343,232 | 2026-09-27T14:45:04.539191+00:00 |
| bsp | 19,969,160 | 2026-09-27T14:28:30.316150+00:00 |
| navmesh | 139,118 | 2026-09-27T14:28:30.265380+00:00 |
| lighting | 166,776,956 | 2026-09-27T14:35:50.756194+00:00 |

Native navigation gate:

```text
TOWER: 25 connected walk sections, 24 directed stock drop traversals; every takeoff/landing has compiled navmesh
SPIRE: all 70 floors in component 1 — connected
CROWN ISLAND (jump pad): hall + pad in component 0 (88 faces), landing in the tower's 3 — connected
BATTLE ARENA: 4 arrivals + 8 spawns in component 27; floor-40 chamber checked.
TRANSIT: 8 pads and arrival fan-outs checked; 0 problem(s).
NAVMESH GATE OK: main descent sections and endpoints verified; spire is one connected walk. Stock traversal playback remains a native playtest check.
```

These checks establish compiled walking surfaces and directed source links;
they do not establish in-game zombie animation playback or grapple behavior.

The guarded build completed geometry, fresh lighting, GSC/linking, sound-bank
and native-asset checks. Scripts, zone source and UI match deployment byte for
byte; no deployed source is newer than this fastfile. Map/surface/sky input
hashes also match. The exact artifacts and SHA-256 values are recorded in
[build_receipt.json](build_receipt.json). The source-only audit remains separate
and does not itself certify a native build.

Build logs: `tmp/map_design_build/full3.log` and `tmp/battle_arena/gsc1.log`. The script follow-up includes the arena watchdog
added after the FULL build's sync; the compiled geometry and lighting are
hash-identical to the successful FULL build. Initial attempts are preserved as `full.log` and
`full2.log` in the same directory. The first caught bare GUID declarations in
the drop entities; these now use native `guid "{...}"` syntax. The second
caught the new arena prompt before registration was complete. The prompt
router now recognizes it; hint checks expand generated transit destinations
and string constants. The ten hint regression cases and mirrored-map check pass.
The parity runner copies the new arena module and redirects its generated data
into its scratch directory.

Both sessions began the script follow-up close together. This session stopped
its duplicate waiting retry (`full3b.log`, not a successful build). The arena
session completed `tmp/battle_arena/gsc1.log`. The final sound-bank, source/deployment
and compiled-asset checks passed; no new linker error was waived.

The refreshed [transit review](transit/review.html) shows actual source geometry
and the shipped pad model with Blender studio lighting. It is not a game capture.

During the user's test, automatic `[TOD_DROP]`, `[TOD_TELEPORT]`, `[TOD_FALL]`,
`[TOD_LIGHTSTATE]` and existing dev logs provide the relevant state changes.
Archive the completed `console_mp.log` with `tools/capture_ai_logs.ps1`.
