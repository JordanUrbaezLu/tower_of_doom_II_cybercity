# Archer equipment asset pass

## Current result

The original BO2/MOTD Retriever is now a native lethal offhand with its original
view/world models, Alcatraz hands, hold/throw/acquisition animations, sounds,
charge stages, chained attacks, power-up retrieval and catch cooldown.
The simplified manual axe has been replaced. The grapple includes native
first-person raise/hold/lower presentation, an authored wrist housing with a
recovered Apex component, anchor hook, braided cable, five cues and aim marker.
Archer's aimed-surface pull and class-only fall immunity remain enabled.

The blade's recovered reveal/ember/heat textures are translated into a native
BO3 animated emissive material. The source textures keep their original
resolution; the 4096 atlas contains 64 animation frames at 512 pixels each.
This is a renderer translation, not pixel-identical BO2 shader execution.
See [native implementation and exact behavior](170_archer_native_bo2.md).

Build/deployment evidence: `docs/archer_equipment_evidence/build.json`.
Dev and god are enabled. The user performs the native playtest. The previous
00:34 build's compile success was superseded by an archived runtime failure:
`LoadFX` was unresolved in server GSC. That blocker is fixed and regression
checked. The 03:07 playtest exposed a second unresolved call, `StopFXOnTag` in
Retriever cleanup. Both calls are removed; cleanup now deletes the trail host
using BO3's stock pattern. A new build gate checks all Archer engine calls
against the correct stock script VM. See docs/170 for the archived log and
current rebuild evidence. Source checks and Blender previews are not runtime proof.

## Source collection and the Greyhound question

The user loaded BO2 Alcatraz on 2026-09-25. The executable is now available at
`C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops II/t6zm.exe`:
Steam build 24784239, SHA256
`f6f7104af2bd0c2b931ea1e739969e85845e499affbf686144c6b490b344ab1e`.
The local Greyhound is 1.46.3.2. Its official GitHub release page is marked outdated.
No Greyhound compatibility failure was reproduced: extraction succeeded offline
with official OpenAssetTools 0.33.0 instead. Neither game was started by the agent.

OAT needed two concrete corrections in our collection workflow:

- Alcatraz requests `dlc2.ipak`, while this Steam Zombies install supplies
  `dlczm2.ipak`. A private copy with the requested name in the repository's
  extraction folder fixes the lookup. The original game is never changed.
  Image extraction then completed with zero errors.
- Preloading `code_post_gfx_zm` and `common_zm` makes the loaded common banks
  available while dumping Alcatraz. This recovered the three secondary gore
  samples referenced by the Retriever's impacts; all 22 selected alias rows
  now resolve to samples.

The focused library is `source_library/archer_equipment/retriever/`: 84 files,
13,868,997 bytes at collection time, including seven model LOD files, 23 animation
files, 20 DDS images, 19 WAV/FLAC samples, material/model definitions and the
zone GDT containing the original weapon definitions. The count includes the
ordinary hatchet reference and event music, not only the main Retriever.
`manifest.json` records each source path/hash and the original sound alias rows.

The original server/client Retriever scripts were extracted from
`zm_prison_patch.ff` and decompiled successfully with official GSC Tool 1.5.1.
Raw binaries, readable references, commands and logs are retained in
`source_library/archer_equipment/retriever_scripts/`. They are BO2 references,
not installed as BO3 gameplay scripts.

The user's [HarryBo21 thread](https://zombiemodding.com/index.php?topic=20366.0)
also contains pasted WaW port scripts. A snapshot and dependency-name inventory
are retained under `source_library/archer_equipment/research/`. Its Mega archive
is removed (-9); the SG4Y BO3 port's Google Drive returns 404, and seven archived
HarryBo21 BO3 weapon-pack links also return -9. These dead downloads no longer
block the original source collection.

Greyhound's public BO2 loader was inspected: it tries fixed pool/string addresses,
then signature searches, and validates model/string data. A changed executable
may need updated addresses/signatures or structure readers. Such a patch would
need the exact binary and a reproduced failure; no guessed offsets or removed
validation are presented as a fix. The offline extraction route avoided it here.

Apex sources were extracted read-only with RSX 2.3.0 from installed build
`R5pc_r5-301_J28_CL11570498_FSv30_1_2026_09_16_17_18`. The retained library includes
85 CAST files (models/rigs/motion), 72 PNGs, 230 WAVs and 129 decoded audio events;
all 212 referenced audio source names resolve. Not every grapple-name match is
Pathfinder-specific. Full inventory: `art/archer_assets/source_library_manifest.json`.

## Native assets and presentation

The Retriever world model retains all three source LODs: 1,361 / 250 / 23
triangles, plus a tag_knife_fx attachment. The 2,501-triangle first-person model
and 7,240-triangle Alcatraz hands use four converted original clips. Body
textures are 1024x512, blade 512x512 and fringe 512x256. The two differently
named view/world fringe specular textures have identical pixel payloads.

The Apex anchor hook is 662 triangles with original 512px textures. The
2,012-triangle Pathfinder component and its 1024px textures are incorporated
into the 2,200-triangle first-person wrist housing. No upscaled-detail claim
is made. Normal RG reconstructs XYZ; DirectX Y stays native for BO3.

The native animated ember material uses the original reveal/ember/heat maps;
its BO3 shader translation is described in docs/170. Trail, hit, charge and
charged-trail effects use recovered T7 tomahawk emitters and source textures;
this is converted source FX, with no dynamic lights. The charge ring's missing
material is now defined under the map's own prefix with its original texture.
Trail intervals are bounded and impact bursts are capped at eight particles
per emitter. The original BO2 chain rules replace the former three-victim cap.

The sound bank includes 16 samples: five grapple cues and eleven original
Retriever samples, including the acquisition flourish's native sound action.
Custom 3D cues use script_origin emitters. Loops have dedicated tracked emitters:
grapple ends stop its pull loop; axe ends stop its spin loop; menus silence the
paused axe and resume its loop when movement resumes. Death, downing, class
change, disconnect and slot reuse clean up hosts/loops; catch plays only on an
actual return. Recharge cues play once when their timer reaches zero.

Each client draws a native hexagonal cable from the owner's left wrist to the
replicated hook host. Snapshot zero, refresh and entity shutdown stop it. Model
lookup waits are bounded to 1.5 seconds. Dev diagnostics include server
`[TOD_ARCHER] ART_ATTACH / ART_FAIL`, the existing movement/projectile logs, and
`[TOD_ARCHER_C] CABLE_ATTACH / CABLE_END / CABLE_FAIL`. The ready-target marker
traces at most every 150ms and sends state changes plus a two-second refresh.

## Editable art and validation

`art/archer_assets/archer_equipment.blend` was authored with real Blender MCP on
isolated loopback port 9883. The studio includes the original hook, Retriever,
a native-scale cable phase preview, and the first-person hold/throw/flourish/grapple scenes. Still/animated previews are in
`art/archer_assets/preview/`; the original Retriever render was visually inspected.
The cable scene uses a 64-unit-high camera and native geometry dimensions.
These renders do not establish native visibility, first-person alignment,
collision or multiplayer behavior.

54 equipment checks and executable art cleanup/replication checks pass, including
independent local viewers and idempotent sound/host deletion. Source verification
checks all 84 hashes, resolved audio, unchanged model geometry and preserved
texture dimensions (`docs/archer_equipment_evidence/retriever_source.json`).
Native compilation, deployment hashes, compiled triangle counts and final build
status are recorded in `docs/archer_equipment_evidence/build.json`. Runtime
appearance, audio, movement and multiplayer remain unplayed.

## Native integration

The first-person/offhand, grapple presentation and ember-material work are
implemented. The original BO2 scripts contain no separate catch-hand animation;
catch uses audio and recharge. Per-throw hit ownership, class cleanup and
native inventory repair protect co-op and respawn paths.

Native appearance, hand attachment, cable alignment, collision and co-op still
require the user's playtest. No agent-run match is authorized. The current
build's output and all source/deployment evidence are linked in docs/170.

## Reproduction and credits

See `tools/archer_assets/README.md` for the pinned extraction tools and commands.
The complete staged-native order and the official-converter sound-note fix are
listed in `tools/archer_assets/README.md`. Source/native checks and all three
Archer tests precede the guarded full build and deployment audit.

Sources: Treyarch/Activision BO2 assets; EA/Respawn Apex assets; OpenAssetTools by
Laupetin/contributors; RSX by r-ex contributors; Greyhound by Scobalula/dest1yo;
GSC Tool by xensik. Earlier generic tomahawk impacts from ShortStak's
[BO2 Weapon Sounds](https://www.devraw.net/approved-assets/shortstak/bo2-weapon-sounds)
remain archived but the final aliases use the installed MOTD originals.
The T7 tomahawk FX library is retained as source with its provenance record.
