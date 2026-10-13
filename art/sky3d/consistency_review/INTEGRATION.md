# Dull sky and native sign-card integration

**Resolved source integration:** the root authored the derived card
through Blender MCP using `tools/sky_consistency/bake_native_card.py`; the
background render helper is `render_native_card.py`. Its target is
`tmp/sky_consistency/native_card_finished.png`, with provenance in
`art/sky3d/consistency_review/native_card_art.json`. The native generator now
consumes those finalized bytes while preserving original source artwork
provenance, native geometry/UVs and the agreed native emission knob. Both the
color/alpha and emissive bindings use the derived image so the
foreground visibility holds. The consistency snapshot rejects an original-PNG
card when it differs from the reviewed derived bake.

The root's final bake applies the shared frame material with saturation/energy
1, then normalizes all architectural reflected spill to **0.06**. The shared
lettering rectangle stays protected, as do bright saturated tube cores selected
by a smooth chroma gate from 0.35 to 0.75 multiplied by the highlight gate.
Those protected regions retain full native scale 16. The earlier 0.12 response
left the frame washed out in the actual Blender render and was superseded.
This separates reflected frame brightness from tube emission instead of
changing the common preview exposure. The material response is an artistic
approximation, recorded as `native_frame_response` in the bake receipt. The bake
uses the same panorama camera plus 27 opaque scene holdouts, including ground.
Corner and title-anchor projection checks were within 0.002 pixels. The original
source PNG remains untouched. The bake receipt binds the authored master,
source files, blend, original image and rendered output; final native brightness
and transparency still need the user's playtest.

The parallel first-jump work changes the sign from permanently lit sky artwork
to two states: the shipping HDR contains a dull sign, and a client model lights
the sign after the crash. Preserve that authorized behavior. `author_config.json`
selects `sign_state: dull`; a source/config change invalidates earlier masters
and renders and requires reauthoring rather than overriding their receipts.

The isolated consistency installer and snapshot now require the actual final
title report to say `dull`. The snapshot also requires the master's explicit
authoring option, pins the native card generator and receipt, and includes
`native_card_art.json` plus the native model/image/GDT inputs. The final build
audit checks the card's packed model, material and images, exact compiled
triangle coverage, and database bindings. Missing or stale inputs fail.

`preview.py` keeps the finished dull HDR as its world and imports the actual
exported card binary, UVs, GDT texture bindings, tint and emission scale through
`native_card_preview.py`. It saves two scenes:

- **01 Before jump - dull sky**: shipping sky alone.
- **02 After reveal - native sign card**: the same sky plus the generated card;
  this is the default visible scene.

Choose a scene from Blender's Scene selector, or run `before_jump_preview.py` /
`after_reveal_preview.py` through the existing MCP wrapper. These state helpers
do not resave the blend. The reopening helper checks the recorded sky and card
hashes and restores Rendered mode while preserving the selected scene.

Native geometry and material inputs are source-accurate. The preview's emissive
display conversion is explicitly approximate: `1/(preview_gain*2^skyStops)` per
native HDR unit, with the existing 1/2.2 display gamma. The sky's display multiplier
is applied to the sky only. Native tone mapping, bloom, transparency, transient
crash FX and persistent-card runtime behavior still need the user's playtest.

The main comparison PNGs are projections of the shipping sky alone, so their
new sign is intentionally dull. The gallery labels that distinction and includes
`blender_after_reveal.png` / `blender_before_jump.png` when the root captures them.
Do not present a dull panorama as the final after-reveal appearance.

Two visual integration concerns have been resolved in the source art by the
root and the jump owner:

1. The first native-card generator copied the original source PNG directly.
   That bypassed the sky shader's graphite-frame highlight correction and could
   restore the appearance mismatch after the reveal. The derived native card
   now retains the agreed frame treatment while keeping the title dominant.
2. Original source alpha includes sign regions hidden by authored foreground
   buildings in the sky render. A runtime card cannot depth-test against those
   painted buildings. Its derived visibility/alpha now preserves their occlusion
   so sign feet or other concealed portions do not draw over the skyline.

The preview reads the generated texture path and receipt, so finalized derived
RGBA flows through automatically. The root owns the derived-art bake and its
`native_card_art.json` receipt. This note records coordination requirements;
it does not claim any native visual playtest is complete. The current generator
now consumes the derived bake. Its permanent copy is
`art/sky3d/sign/v11_native_lit.png`; the art validator pins both that copy and
the temporary bake output and requires identical hashes.

## Native-card display audit

The native card's scale remains 16. No extra factor of 10 should be removed from
its preview conversion under the existing sky bracket. Let `E` be finished EXR
radiance, `p = 0.0176`, `s = 4.35`, and `m = 10`. The existing preview displays
sky radiance as `E*m/p`. If native sky radiance is `E*2^s*m`, the common camera
conversion that matches that bracket is `1/(p*2^s) = 2.7861651204`; `m` cancels.
For the fixed sky gain `g = 0.016525428679573573`, one raw authored W is
`g*2^s*m = 3.3700257191` native units and `g*m/p = 9.3894481134` display-linear
units. A white card texel at native 16 is therefore 4.747738247 raw W or
44.578641926 display-linear units by either derivation.

The bake transfer also matches its declared encoding: the shared material at
energy 1 is rendered through Standard/sRGB into PNG, then loaded as sRGB and
decoded to linear before the native multiplier. The preview's Raw view and
explicit 1/2.2 gamma match the existing panorama bracket. No duplicate gamma or
missing fixed sky gain was found. The card is a native emissive model and does
not itself receive the sky-file finishing gain.

This is a conditional relative-brightness derivation, not measured native
exposure. `emissiveIncompetence=1` maps to the undocumented `relativeHDR` shader
option (docs/162 chapter 03 section 2.3); the preview does not emulate its
unknown exposure behavior. The worldspawn sky multiplier's behavior above 1 is
also unverified, as recorded in `finish_sky.py`. BO3's exposure compensation,
tone curve, bloom and transparency remain unverified here. An additional
division by 10 would be a separate artistic display bracket, not a proven
conversion correction.

A read-only calculation over 830,796 derived PNG pixels with alpha at least 0.95
predicted all three channels clipping for 33.76% and at least one channel
clipping for 67.00% before the frame response correction. The intermediate 0.12
response lowered these to 19.43% and 53.98%. With the final **0.06 response and
refined tube mask**, they fall to **10.85%** and **27.54%**; median display-linear
luma falls from the original 1.104 to **0.127**. The native scale 16 and preview
conversion remain identical. The regenerated card passes
`make_sign_card.py --check`. The rendered After reveal view now retains dark
frame detail while the lettering remains very bright. These percentages are
source-texel statistics before filtering/compositing, not screenshot or runtime
measurements. Thus a bright/white Blender card alone cannot establish that the
native material is too bright; it does establish that this approximate bracket
loses some surface detail. Keep the source inputs exact and the preview caveat
visible, and let the user's native playtest settle final intensity.
