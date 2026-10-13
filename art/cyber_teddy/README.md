# Cyber Teddy (the song-hunt bear)

Since docs/208 (2026-10-04) the three teddy bears of the song hunt
(`_tod_secret.gsc`: the base power hall, the floor-10 haven hall, the floor-20
haven loggia) wear a fan's **Cyber Teddy**, `tod_cyber_teddy`, instead of the
stock mystery-box bear `p7_zm_teddybear`. It was made for map 1 (its v19.64,
2026-09-30) and is carried here byte for byte.

## Source

- `source/cyber_teddy_walking.fbx`, md5 `0cdea9bee11f5360fe6cd63c51f4e619`: a
  fan's model pack (`3D Models/Random Ideas/Cyber Teddy and animations/`), made
  with Meshy AI (auto-rigged, one walk, one 2048 colour texture, 9,919 triangles).
  The fan's note grants permission to alter any model. Credit: CREDITS.md (their
  name and the Meshy plan are still to confirm before a public upload).

## What the game gets (map 1's `tools/cyber_teddy/build_cyber_teddy.py` made it)

| File | What |
|---|---|
| `model_export/tod_cyber_teddy/tod_cyber_teddy.xmodel_bin` | the REST pose, baked; one bone `tag_origin`; pivot at the bounding-box centre; 22.6 wide x 15.7 deep x 28 tall; FRONT = local -Y |
| `.../_images/i_tod_cyber_teddy_c.png` | the fan's texture, byte for byte |
| `.../_images/i_tod_cyber_teddy_e.png` | a glow map cut from its own blue-to-violet lights (eye, chest core, arm panels) |
| `source_data/tod_cyber_teddy.gdt` | image, material (`lit_emissive_plus`, glow scaleRGB 4) and model blocks; BulletCollisionLOD None like the stock bear |
| `manifest.json` | map 1's manifest, copied whole: size, lift, half_depth, hashes |
| `preview_*.jpg` | map 1's renders of the written binary |

The rig and the walk are not used: the hunt's rise, spin and flight are scripted
movers.

## The numbers are one chain

`manifest.json` `lift` (14.0) and `half_depth` (7.9) are `TOD_SECRET_LIFT` /
`TOD_SECRET_HALF_DEPTH` in `_tod_secret.gsc` and `BEAR_LIFT` / `BEAR_HALF` in
`tools/haven_layout.js` (whose `BEAR_EXT` = the bounds, so the floor-20 corner bear
keeps its arm out of the loggia's east rail: `BEAR_SIDE` 11.4). The generated
`_tod_breather_data.gsc` carries the lift into the haven anchors.
`python tools/cyber_teddy/verify.py --check` (a build gate) fails if any of them
drift, if a shipped file stops matching the manifest, or if the stock bear comes
back; `--compiled-ledger` (post-link) proves the model compiled whole and its
material is not empty.

## Rebuild

Map 1's `tools/cyber_teddy/build_cyber_teddy.py` hardcodes map 1's repository and
the shared Steam tools. NEVER run it as it is from here: copy it in with `REPO`
pointed at this tree and its tools root at the private one, then copy the new
`manifest.json` with the outputs. A model or GDT change is a FULL build. Blender
previews do not establish the in-game glow or lighting: judge that in game.
