# The Black Market hut (was the Item Shop): live Blender art and native crown-room test

**2026-09-29: RENAMED THE BLACK MARKET, SIGN REBUILT (user: "The Item Shop / Black Market is
confusing. Lets just rename it Black Market all together and update the model with Blender MCP").**
The neon sign reads BLACK MARKET, rebuilt in the MCP studio (port 9881) by
`tools/partner_shop/18_black_market_sign.py`, in the same tube, electrode, standoff and clip
construction as before, on the unchanged carrier and border. C, E and T blink on the shared fault
bus. Native slots: `tod_shop_letter_t` and `_e` keep their letters; `tod_shop_letter_c` replaces
`_h`. The sign sparks moved with their letters. The counter stencils read NO QUESTIONS ASKED and
SPIN / SOCKET / SCRAP. The prompt, its noun and the spin screen all say BLACK MARKET (docs/188).
Evidence: the art README, `art/partner_shop/validation.json` (revision 3), `engine_kit/`. BUILT in fd's FULL BUILD OK 14:26 (tmp/spire_removal/full1.log, FF 14:23:04): all 19 shop models / 133 LODs compiled with full triangle coverage (`engine_kit/compiled_validation.json`), `tod_shop_letter_c` in the ledger. UNPLAYED.


September 24, 2026. Master, references and reproduction:
[art README](../art/partner_shop/README.md). Electrical preview includes the
user's downloaded electricity WAV, synchronized to the authored sparks.

Current direction: black/oxblood/red industrial hut; all BLACK MARKET letters
work, only C/E/T flicker (ITEM SHOP with T/E/H until 2026-09-29); shorter hooded merchant with lowered arms and a
slow red mask pulse independent of the power faults. The mask now has slanted
X eyes, angular armored brows/cheeks and uneven pointed teeth.
New left service panels, capacitor and cabling. Canister pulses share a phase;
T/E/H and the canisters share every dropout and recovery. A 100-degree indexed
pressure wheel and +/-24-degree gauge replace the small former movements.
Larger sparks discharge at both side containers on each major fault. Off state leaves
an empty, dark, silent hut. Dead E/O and the cyan palette are superseded.

## Native implementation

Three generator-owned west/east/north crown placements are separated by over
800 units. Their collision is contained in the visible models. The north copy
stands east of the old extraction pad on the upper sanctuary step, clear of
the central route. One active location cycles west -> east -> north each round
as the stated test default. Power loss and end-game shut it down.
Purchases, catalogue and prices are not part of this art/state/audio pass.

`_tod_shop.gsc` owns model lifetimes and pressure movement.
`_tod_shop.csc` owns shader emission, native mesh sparks, positional audio
and the stock Wunderfizz marker. Lockstep clientfields replay for late joiners;
all components use the shared server clock. Shader constant `hdrScale` is
defined in shipped `include/emissive_base.techsetdef`: emission can change
without altering surface lighting. Blink lookup is generated from Blender.

The original WAV is preserved with SHA-256 provenance. Three transient cuts
are 48 kHz mono PCM. No randomized pitch or delay; sound and FX share one call
site/event. Each simultaneous cluster plays one sound, preventing stacked
transients. Audio stops on shutdown; particles expire within 310 ms.
The arc and fleck meshes are authored Blender art, not a stock sprite recolor.
Two native emitters, six particles/event, at most twenty-four overlapping particles,
zero custom dynamic lights. Stock Wunderfizz cost is additional and unmeasured.

Seven distance LODs per model; off mesh retains body/glass geometry without
vendor or emission. 19 models, 133 LOD files.
The installer cleans final clamped positions before recording triangle
coverage. In the initial export, the native converter identified one nearly
collinear neon-frame triangle in steady LOD2 as degenerate before bone
processing; its normalized area was .00032455. A .0005 normalized-area guard
on distant steady meshes rejects such slivers and their off-mesh copies.
Close-up art and small lettering
are retained. Palette triangles receive stable UVs inside their original
uniform swatches, preventing half-float corner collapse without changing
their color. Compiled counts must match source exactly; the gate is not waived.
Converter evidence: `tmp/partner_shop_build/native_triangle.log`.
`test_shop.js` executes the actual activation body and timing functions with
a mocked scheduler: on/off/handoff, allocation rollback, missing body,
transition guard, loop seams and placement/collision contracts. The actual
evaluated Blender emissions and valve angles agree with runtime math on all
181 sampled frames, including independent mask breathing during faults. Source and
compiled model checks gate builds. `verify_deployment.py` checks exact input
hashes, deployed files, packed assets and timestamps.
The linked `test_client_sync.js` also runs the actual CSC event dispatcher
against steady and irregular client clocks. It checks sound/FX pairing,
one crackle per cluster, pauses, loop wrap, late joins, time jumps and a
second local client. These are source simulations, not native listening tests.

## September 24 build result

Revision 2 and the concurrent dark-hall pass are verified together at
15:05 Eastern. FF 210,979,392 bytes (15:03:33); fresh 100,163,699-byte LED and validated navigation,
including the intended separate crown island. All 19 models / 133 LOD
files retain exact triangle coverage. Models, four materials, fifteen maps,
custom sparks and the stock Wunderfizz marker are packed. All three spark
aliases are in the converted bank: positional, loaded, zero delay/pitch
offset, pauseable and stopped on entity deletion. Loaded/streamed banks:
63,287,040 / 207,523,840 bytes. The combined shop/teleporter snapshot has
351 matching source/deployed inputs, including the new hall materials and sky,
no missing assets and nothing newer
than the FF. Only ten established waived linker warnings remain.

Evidence: `tmp/partner_shop_build/revision2/final_full_build.log`,
`deployment.json`, `final_build_record.json`, copied asset ledgers and
converter transcripts. The shop-only full build 10 also passed; the source
map changed during it, so final verification uses the subsequent
`tmp/dark_pass_build/build.log` build. Both build records are retained.
The WAV preview's actual sound windows start at 1, 3 and 5 seconds, with no
clipping or stray sound between clusters (`audio_onset_check.json`).
Both Blender MCP previews are running; neither master was resaved after
export. BUILT AND STOPPED, no game launch or native visual/audio approval.

Follow-up pre-play verification rechecked the current compiled shop and
teleporter geometry, their state tests, all 351 deployed inputs, converted
sound aliases, exact preview WAV onsets and the game's map junction. The new
client-dispatch timing test passed. No runtime inputs changed, so the same
15:03:33 build remains current; another build was unnecessary. Evidence:
`tmp/partner_shop_build/revision2/preplay_check.json`.

## User playtest

Build evidence: `tmp/partner_shop_build/`. No BO3 launch or native approval
is implied by Blender renders. `[TOD_SHOP]` logs server ownership/state edges;
`[TOD_SHOP_C]` logs marker creation and the first ten audio/FX events per
activation. Normal dev mode enables logs; temporary `TOD_SHOP_LOG 1` also
captures this normal-match bring-up. Zero it after acceptance.

Check positions, empty off shops, marker ownership, three blinking letters,
slow mask pulse, pressure movement and localized spark sounds across a round
transition. Preserve the console with `tools/capture_ai_logs.ps1`.
Native art, sound level, lifecycle and measured cost await that playtest,
per docs/155. The agent builds and stops; the user plays.
