# Teleporter surface correction - September 26

BUILT by Archer in build 11; the user accepted the repaired metal surface at
22:40 on September 26. The exact cause of the old sampling artifact remains
inferred. The user now rejects the pink status color; the separate
[green-ready / yellow-pending correction](../status_colors/README.md) supersedes
the palette in these historical previews. No game launched by this session.

The user's 16:05 screenshot shows pink breakup across metal plates. The current
exported binary renders clean, narrow strips in Blender, and the archived user
log has one model per transit-pad origin. The private native database confirms
both ready/off materials inherit `waterRoughness=0.1`. The installed fullspec
techset binds that field to emissive `layerDepth`; material.awi defaults it to
0.1. The lighting reference documents it as parallax depth. The Blender atlas
preview uses no parallax offset. On a tightly packed atlas this is a material
mismatch and a likely cause of pink sampling outside the intended strips.
The material explanation remains an inference; the user now confirms that the
surface looks fine. No agent-run game test occurred.

The ready/off body materials now explicitly set depth to zero and lower the
gloss range from 0..8 to 0..6 for a less shiny metal finish. Other fields, all
six textures, seven body LODs, recharge mesh, master and gameplay script retain
their bytes during that repair. It retained pink emission at 6 on the ready
twin and 0 on the off twin; the subsequent status-color correction replaces
pink with green. Yellow recharge and travel timing were unchanged here.

`review.html` compares the user's native screenshot with the intended current
exported-mesh preview. Both `binary_before.png` and `binary_after.png` are
Blender approximations; neither simulates the old native parallax problem.
They use the actual shipped binary, atlas, UVs and native gloss range. They do
not reproduce BO3's reflections, lighting, exposure or tone mapping.

Evidence:

- `before.json`: original source fields and hashes of 16 unchanged inputs.
- `deployed_before.json`: read-only database evidence from build 8.
- `source_validation.json`: corrected fields and source hashes; not deployed.
- MCP logs in `tmp/teleporter_mcp/`; isolated Blender 5.2 studio on port 9879.
- User log: `tmp/elite_tracking/runs/20260926_161021_505_1f7738e6`.
- `engine_kit/source_validation.json` and state/image checks: seven body LODs,
  power/lock/cooldown/cleanup and all 4,194,304 emission-mask pixels pass.

Reapply only these materials with `tools/teleporter/repair_surface.py`. The
shared finish profile also feeds the normal native installer; the off twin
inherits it through `install_states.py`. `verify_native.py` requires explicit
zero depth, preventing default inheritance on a future regeneration.

Deployment update: Archer's build 10 passed `record_surface_build.py`;
`deployment.json` records matching inputs, native depth=0/gloss=6 and seven LODs.
This establishes inclusion, not visual correction in the user's game.

After any later cleared build:

    python -B tools/teleporter/record_surface_build.py --build-log <build-log>

This checks native database values, deployed hashes/timestamps, packed images
and materials, all seven ready/off LODs and the recharge mesh. The old build 8
fails it. Coordination: docs/crown_alarm/BUILD_HANDOFF.md.

User retest: inspect a ready pad close up and from a low angle. Pink should stay
on the strip geometry as the camera moves. Check the dark state and yellow
recharge chase too. If metal still shows pink after the deployment audit passes,
investigate the compiled image sampling next; do not assume this preview proves
native appearance.
