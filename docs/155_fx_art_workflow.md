# Detailed effects: author, integrate, judge in game

Requested 2026-09-22: use a repeatable process for detailed, striking effects.
Blender MCP is the art-authoring and preview tool. BO3's native FX system is
the final particle, material, timing and lighting implementation. A Blender
simulation or compositor effect is not automatically an exportable BO3 effect.

## 1. Write the visual brief before adding emitters

Record the reference, purpose, colors, footprint, camera distance, start/stop
conditions and exact gameplay timing. Sketch the sequence as a timing sheet.
Choose one dominant shape, supporting motion and small detail; do not make
every layer equally bright. Detail should remain legible at normal play distance.

Teleporter direction: machined alloy and copper remain visible beneath cyan
energy and violet accents. Energy follows the deck's real channels and emitter.
Quiet ready state; inward motion during the existing 0.8-second charge; a clear
release at transfer; a short expanding arrival pulse that clears the player's view.
Preserve all trigger, cooldown, rider and destination rules.

## 2. Author custom art through Blender MCP

Use an isolated Blender scene/collection and preserve the original asset.
Build at native scale and origin, with the actual model and a first-person-height
camera. Make the large energy shape, medium filaments/arcs, and small ions as
separate controllable layers. Use curves/meshes and procedural shaders where
they give precise control; use particles/simulation when their motion earns it.

Create an editable `.blend`, a contact sheet of the phases and an animated
preview. Check low and oblique angles, against light and dark backgrounds.
Keep the model readable; inspect the effect both with and without preview bloom.
Avoid treating a beautiful studio render as proof of native game quality.

Bake/render only what the native renderer can consume: emissive/alpha masks,
loopable sprite sheets, distortion/normal textures, and small native effect
meshes where useful. Keep fine filament cores and soft falloff separate; avoid
clipped white discs, hard alpha edges and motion that jumps at the loop seam.
Choose texture resolution and frame count from the on-screen size, and verify
the atlas layout against a working native donor before export.

## 3. Assemble and tune in BO3

Create map-owned image/material/FX definitions in the private Tower II workspace.
Combine the custom art into separate layers: core shape, filaments, moving
particles, restrained distortion, release wave and brief environment light.
Use working native effect templates for renderer conventions; do not substitute
a stock recolor for the custom art pass when the brief calls for a new signature.
Preserve correct sprite orientation, deck clearance and camera-distance fading.

Time visual peaks to the actual gameplay event. Use existing host entities when
possible, keep loops bounded, and always define stop/delete behavior. Preserve
the server-host replication delay. Never make gameplay wait on the art.

## 4. Review quality and cost together

Record custom emitter count, spawn period, particle lifetime, maximum overlap,
dynamic lights, material/texture count, atlas memory and host ownership. Inspect
near-camera transparency/overdraw and overlapping activations in co-op. Start
with restrained idle cost and reserve the visual peak for activation. Measure
the final effect in game before making frame-rate claims.

Before a build, require reproducible sources, resolved assets, native compilation,
and lifecycle checks for normal completion, early host loss and missing assets.
Log state edges, failures and cleanup in dev mode without per-frame spam.

## 5. The user performs the native visual review

Build and stop. Do not launch BO3 unless the user explicitly requests an
agent-operated match. The user checks ready/charge/departure/arrival at ordinary
play distance, near the deck, at a low angle and with multiple players.
Archive their console through `tools/capture_ai_logs.ps1` and correlate FX
lifetime IDs with the report. Iterate on one stated visual issue at a time.

An effect is finished when the native playtest meets the brief: coherent shape
and motion, visible surface detail, a clear timing peak, readable surroundings,
no clipping/loop seams/orphaned emitters, and acceptable measured cost.
Source checks and Blender renders alone do not establish that result.

## Current teleporter status

The enhanced model was authored through Blender MCP. The September 22 FX pass
uses native effect composition and existing stock sprite materials: low cyan/
violet ready fields, charge contraction and release pulses. It is a first pass,
not a newly Blender-authored FX art package or a visually approved final effect.
Custom Blender FX art and native visual approval remain separate milestones.
Do not describe those milestones as completed until their artifacts/evidence exist.
