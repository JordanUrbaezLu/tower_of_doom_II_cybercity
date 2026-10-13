# Jump-pad balcony view — 2026-09-27

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

User reference: Screenshot 2026-09-27 141213.png. The 56-unit visible parapet
hid the tower below the horizon. The five launch-balcony rail runs now form a
12-unit curb. Each has a separate invisible collision brush from deck height
to the original 168-unit top. West/east/north protection still continues upward;
the south side retains the original clearance above 168 units for the jump pad.

The change affects exactly five visible brushes and their five clip brushes.
The player collision union, deck, hallway opening, shop, Quick Revive, pad,
landing positions and flight arc are unchanged. No geometry baseline was reset:
the crown material check permits only these five top faces to move down by 44.

Checks passed: whole-map geometry (zero misplaced walls or unguarded edges),
mirrored crown layout, unchanged crown floor/wall geometry, material coverage,
five continuous balcony barriers and 8,020 sampled jump-pad flight positions.
Before/after geometry receipt: `tmp/balcony_visibility/geometry_receipt.json`.
This is static verification; native appearance awaits the user's playtest.

Requires a **new full build**, including fresh geometry/navmesh and lighting.
The previous script-only retry is superseded. The combined build also carries
the pending crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Status:
`tmp/crown_alarm_visibility/status.json`; build log: `full_build.log` there.
The agent does not launch the game.
