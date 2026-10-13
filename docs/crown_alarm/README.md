# Current: September 27 high crown visibility pass

Upper fixtures are now doubled on their original mounting feet, with emission 576 and actual red spill lights on all 17 high mounts. Full build queued while BO3 runs; not yet native-tested. [Current notes](VISIBILITY_PASS.md). The historical statuses and high-fixture emission-only design below are superseded.

# Crown rotating alarms

**Newest follow-up: 4x high-crown glow, source READY / NOT BUILT.** The 16 outer
points and apex use `tod_crown_alarm_rotor_high_on`: the same three rotor meshes
with only `mtl_tod_alarm_lamp_on` replaced by `mtl_tod_alarm_lamp_high_on`.
Emission is 144 instead of 36. All existing materials, images, base models and
hall FX are unchanged. Existing random phases and the shared off model remain.
Source lifecycle/variant/LOD checks pass. Matched Blender MCP view is at the top
of [review](review.html). Build request is in BUILD_HANDOFF.md for Archer.

**Latest, September 26: random start angles ready, NOT BUILT.** User says the
brightness looks better and requests independent starting directions. The stronger
light settings reached Archer's build 8; they stay unchanged. Each of the 30 rotors
now draws one server-side random angle during initialization. Housing orientation,
pendant inversion, common activation and 1.5-second speed stay intact. Duplicate
init/start calls preserve each angle; MOUNT logs include phase_degrees.
Updated Blender MCP motion is at the top of [review](review.html).
Details: [intensity and phase passes](INTENSITY_PASS.md). The phase change awaits
Archer build clearance under AGENTS.md. Earlier build notes are historical.

User brief, 2026-09-26: replace the two floating red lights with a real modeled
rotating emergency beacon, using Blender MCP. Red only. Mount a fixture on every
hall pillar, keep the central alarm, and add fixtures to the crown's top points.
All activate on the existing alarm trigger; the separate power switch and siren
timing retain their existing behavior.

Visual brief before authoring: a bolted charcoal cast-metal base, machined steel
retaining rings, a ribbed translucent ruby lens, protective metal struts, and a
motor-driven silver reflector with a red lamp. Soft bevels and surface wear must
read at player distance. The lens and lamp have no blue or orange emission.
The same fixture family is used throughout: 12 pillar caps, one inverted pendant
at the original central location, 16 crown points, and the apex (30 total).
Exterior fixtures are four times the hall fixture's size. Off means a stationary,
unlit lamp; on means a rotating physical reflector and red emission.

Native plan: generator-derived mount transforms; static housing and moving rotor
xmodels with explicit LODs; off/on rotor materials; one bounded, shadowless red
spot light per nearby hall fixture through the established clientfield lane.
Exterior fixtures use the physical emissive lamp, avoiding distant banks of
dynamic lights. Activation and shutdown have one owner in the existing fall
alarm lifecycle; duplicate calls are harmless. Diagnostics record placement,
activation, shutdown, and failures, without per-frame logging.

Blender previews demonstrate authored geometry, materials and motion. They do
not prove BO3 rendering. A successful native build verifies packaging only;
the user tests the trigger, rotation, red light, and shutdown in the game.

Implementation: `_tod_crown_alarm.gsc` owns 30 persistent housings and 30 rotors.
The Fall calls its init/start/stop functions. Models switch from off to on before
the clientfield snapshot; a seal during that snapshot cancels startup. Repeated
start/stop calls do not stack loops. The clientfield remains latched for joining
clients. Only the 13 hall fixtures get a shadowless, red, 900-unit spot with a
2,400-unit spawn range, attached to the rotating model. Its 1,000 ms interval
matches its lifetime. No stock aura sprites or free-orbit hosts remain.

Mount coordinates derive from `PIER_Y`, the beam cap height, `CR_POINTS` and their
actual stone heights, the pendant bottom, and `CROWN_TOP`. The four existing
finale progress props move up 194 units to clear the new exterior housings;
their gameplay behavior is unchanged. The old central dummy cube is removed.

Review: [off/on, rotation, hall/exterior placement, robotic legs](review.html).
Native sources: four xmodel assets, nine unique mesh files shared across twelve
LOD references, and 28 texture images. The fourth is the exterior-only skin twin.
`tools/crown_alarm/01_author.py` runs through `mcp_call.py` on isolated port 9885.
`02_integrate.py` wires the map-owned sources. `03_mount_review.py` brings the
current generated geometry and mount transforms into Blender. Render scripts
only create local preview files. Art is authored; final BO3 quality is unverified.
`04_tune_light.py` updates only the alarm's material/FX/manifest from
`light_profile.json`, so tuning does not run the shared integration writer.
`05_intensity_review.py` is the MCP authoring step for the current comparison;
`06_render_intensity.py` and `07_review_media.py` produce its stills and motion.

Validation: `test_alarm.js` exercises the shipping GSC activation/shutdown code,
including duplicate calls and seal-during-start. It rejects a truncated native
light block, with a negative control reproducing the original parser failure.
`verify_native.py` checks native mesh/image bindings and, after linking, every
LOD's compiled triangle count plus the actual spotlight FX asset in the ledger.
Both run in the guarded build. Existing elite checks also validate real robotic
leg image bindings and noncollapsed UVs. The corrected Mangler cannon mapping
remains in the same build.

The first combined link (7b) printed BUILD OK but omitted the spotlight:
the FX generator's multiline `name` replacement had swallowed the embedded
light's closing brace. Native `MatchToken` / `Unknown editor elem` messages did
not match the builder's ERROR filter. The post-build asset audit caught it.
The generator now matches only a single element-field line, preserves the
embedded light, and is repeatable. Compiled FX presence is a required build
gate, so the same omission cannot pass through the alarm validation again.

Native build passed September 26, 14:36:13 Eastern: FF 189,911,680 bytes.
The full geometry/LED bake is build 7; the final FX correction is in
`tmp/crown_alarm_final_relink.log`. All nine alarm LODs, the spotlight and twelve
robot-leg maps are compiled; the eight existing waived asset warnings remain.
277 alarm/shared input hashes and 341 elite/shared input hashes match deployment;
no sources were synced after the final FF. Evidence: `art/crown_alarm/deployment.json`
and `art/cyber_elites/leg_texture_deployment.json`. No game launched; user playtest
pending. A negative-control ledger with only the root spotlight omitted now
fails the compiled guard, as recorded in `missing_fx_negative_control.json`.

Dev diagnostics: `[TOD_CROWN_ALARM] MOUNT` (once per mount), `READY`, `ON`, `OFF`,
and missing-rotor shutdown failures. In the user test, confirm all lamps are dark
before the alarm switch, all rotate and glow red afterward, and all stop at the
crown seal. Check the central pendant from below and the exterior from the
balcony. Check the robotic leg surfaces while the Doppelgast runs and dies.
Archive the console with `tools/capture_ai_logs.ps1` after that test.
