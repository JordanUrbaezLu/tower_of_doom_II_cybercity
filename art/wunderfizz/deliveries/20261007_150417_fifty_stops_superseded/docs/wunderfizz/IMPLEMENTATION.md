# Wunderfizz on every descent floor

Status: **Guarded FULL BUILD OK; compiled assets, audio, navigation and
source/deployment parity passed. User native playtest pending.** No game was
launched.

Final FF: `C:/BO3Tools/TOD2Cybercity/usermaps/zm_tod2_cybercity/zone/zm_tod2_cybercity.ff`; 2026-10-07T15:04:17.437771-04:00; 220,532,160 bytes; SHA256 `1f4f36b8028fdc1ced11f8d81e9e8fb0d502b3536f7257a00578942aad267ad4`.
Final delivery receipts: [build/deployment](../../art/wunderfizz/build.json), [compiled assets](../../art/wunderfizz/compiled_assets.json), [native audio](../../art/wunderfizz/native_audio.json).

## Implemented behavior

The nine individual perk vendors and their purchase triggers are retired. One
original BO6 Wunderfizz counter serves each spiral floor 1-50, including floor
50 immediately after the first jump. Pack-a-Punch and other amenities remain.
The original author-supplied BO3 port includes the off/on models, all fourteen
LODs, twenty original 4K PNGs, materials, animation, collision, effects and seven
original machine WAVs. See [ASSET_IMPORT.md](ASSET_IMPORT.md).

Holding USE opens the map's compact selector, showing the nine existing perks,
their effect descriptions, owned/locked state and that player's current price.
Keyboard arrows or controller D-pad select; Enter/A buys; Escape/B closes.
Mouse movement selects a row, and releasing a click inside the row buys it.
The world prompt uses four fixed strings and the existing perk icon/bind footer;
dynamic prices stay in the selector rather than consuming native hint slots.

| Perk | Engine specialty |
| --- | --- |
| Juggernog | `specialty_armorvest` |
| Speed Cola | `specialty_fastreload` |
| Quick Revive | `specialty_quickrevive` |
| Stamin-Up | `specialty_staminup` |
| Widow's Wine | `specialty_widowswine` |
| Death Perception | `specialty_combat_efficiency` |
| Double Tap | `specialty_doubletap2` |
| Wisp Tea | `specialty_nomotionsensor` |
| PhD Flopper | `specialty_electriccherry` |

These are the existing map effects and bottle weapons; the specialty slots do
not imply stock Electric Cherry or other additional perks.

## Price and purchase lifecycle

The authoritative server quote is **2,000 + 500 for each currently owned perk**
from that explicit roster. Zero through eight owned perks cost 2,000, 2,500,
3,000, 3,500, 4,000, 4,500, 5,000, 5,500 and 6,000. All nine owned means no
further purchase. Free grants count; actually lost perks lower the next price;
temporarily paused perks still count. Prices are per player and consistent
across floors. Lifetime purchases and another co-op player's inventory do not
set the quote.

Confirm rechecks session identity, perk, current quote/ownership, registration,
power, proximity, haven lock, player state and points before one reservation and
actual debit. Stock score and bottle/drink/grant APIs preserve perk events and
effects. Each player has one pending session; co-op buyers remain independent.
There is no yield between reservation and debit. Failed ungranted purchases
refund only the actual recorded score reduction once, including zero when
Shopping Free waived the payment.

The selector timeout is 20 seconds; the drink watchdog is eight seconds. Close,
range departure, down/death, respawn, disconnect, intermission/end-game and
other invalid player/machine states release the session. Detached level-owned
cleanup clears pending flags, removes the can and restores a living player's
weapon where appropriate without undoing a down state. A deleted disconnected
entity cannot receive a refund. Refusal/interruption uses existing sound cues
and visible HUD feedback even after the selector closes. UI input/HUD ownership
is released idempotently; a held USE must be released before it opens again.

Power enables the ordinary offers. Solo Quick Revive retains its pre-power
exception and three paid-use limit at the same ownership-based price. Free
Quick Revive keeps its existing one-grant exemption. Exhaustion locks only that
offer; it never removes the counter. Corrupted/locked havens refuse interaction
and cancel their active sessions.

## Layout, native hint and presentation

`tools/wunderfizz_layout.js` generates all fifty descriptors and original static
collision hulls; `_tod_wunderfizz_data.gsc` supplies model/standing anchors.
Forty-six ordinary floors use 120 by 160 side alcoves with clear entrances;
four haven floors face inward from the shared south-west pad. Model scale and
rear pivot remain original. Low visible rails have standing clip protection;
the models are NotSolid because the original hulls are stamped as world clip.
The existing service hall and three Dealer contexts remain byte-identical;
see `art/wunderfizz/dealer_context_parity.json`.

The generated `m.trig` is the purchaser standing/range/nav anchor, at original
local +X83.240486. Native use/look targets instead read the spawned model's
`GetTagOrigin("tag_hint")`, local `(50.192905,0,53.877693)`. The two points are
33.047581 units apart. Keeping them separate avoids aiming beneath the buyer's
eye. The hint tag is unchanged across off/on models and the original animation.

The single level watcher manages power and cleanup. Activation runs in a host
thread, so a stock animation helper cannot suspend other counters. Only visible
activation at the same counter queues; purchases and other counters continue.
The original frame-1 Sound/Play FX and frame-120 Stop FX notes own activation,
electricity and spark cues. Zero blend-out and the clip-length guard preserve
the final note; script timers do not duplicate authored sounds or effects.

The nearest six powered counters within the original 600-unit wet range own
hum loops, respecting the supplied alias's six-voice global cap. Idle FX are
different: all fifty powered hosts can retain a per-client idle handle through
the replicated field, while the untouched original EFX uses native distance
culling. There is no custom distance window limiting idle handles to six.
Original nearby perk jingles are intermittent. Power loss, host loss and
end-game stop owned presentation and clean up the corresponding sessions.
Actual native performance and delivery remain part of the user's playtest.

## Shared integration and verification

`_tod_perk_roster` supplies purchases and free-bottle grants independently of
physical vendors. The provider restores stock/custom perk precaching if the
stock no-vendor early return skipped it; existing hooks run once. This retains
player effects such as Widow's Wine's wrap. Custom effect registration remains
in the existing systems. Individual scatter/idle/loose-change threads are
retired; shared scatter utilities and Pack-a-Punch lighting remain available.

The source, audio, purchase, provider, layout and Lua gates are wired into
`tools/build_map.ps1`. The first native build at 14:16 passed all 150 purchaser
nav probes and all fifty own-landing connection checks. That attempt's coarse
BC7 glass alpha failed its independent gate; it was not accepted as delivery.
The completed final build uses uncompressed RGBA8 glass and passes native
assets, audio, navigation and source/deployment parity. All 150 purchaser
probes and fifty own-landing connections pass again; the final FF is pinned
by the receipts above.

Console diagnostics use `[TOD_WUNDERFIZZ]` and `[TOD_WF_MACHINE]` behind
`tod_dev || tod_diag`, with transaction/floor/client/quote/debit/refund and
presentation state fields. The entry enables console-only `tod_diag` while
gameplay dev mode remains off. See [PLAYTEST.md](PLAYTEST.md) for the
user's route and existing `tools/capture_ai_logs.ps1` capture command.

Native build receipts prove their stated compiled/source/nav checks. GSC/Lua
harnesses use doubles, Blender approximates shading, and animation/audio log
events do not prove native playback. Input, gameplay effects, appearance,
notetrack timing, sound and performance remain unplayed by the agent and await
the user's native observations.
