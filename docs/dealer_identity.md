# The Dealer: one identity throughout Fallen Cybercity

2026-09-30. User direction: the skull above the title should resemble the
Black Market dealer; the same character should recur around the map and be
the **final boss**. The user explicitly chose final boss over an optional
encounter. This establishes the character; it does not make the existing
rigid shop prop an animated enemy.

**Current status: source ready; combined native build pending.** The new
8192x4096 sky, matching bright reveal card and three wall displays are authored,
reviewed and installed in repository sources. Both sign states and seven panel
views passed review. The displays use the actual native vendor/mask, a 1024
portrait, existing worn frame materials and 84 noncolliding triangles. They add
no entities, dynamic lights or runtime threads. Final-boss gameplay is still a
design draft; the combat-form and encounter-scope questions remain pending.

The first combined build was stopped before cod2map/lighting because the guarded
sync omitted the new portrait folder. That one-row omission is fixed and covered
by the automatic source gate. The original snapshot and log are preserved in
`tmp/sky_dealer/attempt1_sync_omission`; no new fastfile came from that attempt.
A fresh snapshot and guarded FULL build, followed by both native proofs, remain
required. Do not use a GSC-only link as proof that these changed map surfaces and
sky lighting have been built. No game was launched by this pass.

The user's Radiant report interrupted rendering. Read-only inspection identified
Map One's `Radiant_modtools.exe` under the shared Steam tools. This pass did not
launch it. Our earlier denoise overlapped it and could have increased memory
pressure; the reported problem's root cause remains unproven. All our Blender
processes are closed. Guards now cover native build stages and other Blender
studios; a real later gdtdb event stopped only our owned, already-saved preview.
See `art/sky3d/dealer_review/resource_guard.json` and the incident receipts there.
A separate Map One `cyber_teddy_review.blend` preview remains open, and another
Cybercity session has linked meanwhile. Root is holding the combined build for
resource coordination; do not close or alter another session's processes.

## Visual identity

The canonical likeness is `art/partner_shop/merchant.png` and its authored
shop model, supported by the shipped dealer portraits in docs/195. Preserve
the deep black hood, long angular charcoal mask, red X eyes, faceted nose
and cheeks, and an uneven stitched red grin. One eye stroke is weaker in
the shop model; the grin is asymmetrical and slightly damaged. Avoid a
generic anatomical skull or changing his face between appearances.

The sky crest translates his hood into a worn armored shroud that belongs
to the title's existing cyber architecture. Preserve the accepted frame,
massive lettering, cinematic alignment, restrained metal finish and the
dull-before-jump / bright-after-crash reveal. The sky remains the largest
and most imposing depiction of the character. Nearby and distant buildings,
planet detail, station and reduced clutter retain the accepted direction.

Use a few smaller sightings along the playable descent, integrated into
existing wall/service surfaces. They should imply that he has been watching
the player across the city. Do not fill the skyline or every floor with
extra faces, lights or floating holograms. Preserve navigation, readable
wayfinding and quiet space around landmarks.

## Voice and characterization

**2026-10-02: the Dealer is his own entity.** Nothing of any existing
character is part of him any more: no borrowed likeness under the mask, no
borrowed voice, no borrowed lore. His voice (docs/198 round 8) is a soft,
scary, dark, slightly cyber voice with occasional manic modes, text-designed in
ElevenLabs; his hints are about his own story (the ledger, the city before the
Fall, the tower that pays him, the sign in the sky, the bigger mask under the
mask). At half health in the fight his mask CRACKS: one eye glow dies, a chip
opens the temple, the grin tears wider (docs/199). The mask never comes off. Existing shop lines share
one voice lane per player; any future story/fight speech needs an explicit
priority and interruption policy so the Dealer never talks over himself.

## Finale boundary

The Dealer is the selected final antagonist. The active Battle Arena Keeper
remains a separate encounter. Do not rename or replace it to imply that a
Dealer finale exists. `_tod_finale.gsc` is currently parked under the descent
layout; its old Crown road/holdout ending must not be re-enabled blindly.
Its dormant callback treats any return as completion and is not a safe new
boss integration point without explicit success/failure handling.

The shop vendor and mask are rigid one-bone models. A moving combat form
requires a real animation/rig pipeline; a colossal form needs its own
authored motions, readable attacks and reachable targets for every class.
The proposed finale experience and lifecycle live in
`docs/dealer_finale_design.md`; proposals there are not shipped gameplay.

## Art provenance and verification

The crest edit is `art/sky3d/sign/v12_dealer.png`, generated with the built-in
imagegen tool from the accepted title and the actual merchant render. Its
exact prompt is `v12_dealer.prompt.txt`; the sky authoring pipeline records
source hashes, transparency, spatial registration and measured light anchors.
The frame/text are visually retained, not claimed to be pixel-identical:
image generation also changes surface pixels outside the edited face.

Build status, native packed-asset proof and preview evidence belong in the
dealer review receipts. Blender previews establish authored appearance and
alignment, not final BO3 brightness or performance. The user playtests.
