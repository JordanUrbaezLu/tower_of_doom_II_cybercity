# Wunderfizz user playtest reference

Status: **Guarded FULL BUILD OK; compiled asset/audio/nav and source/deployment
checks passed. User native playtest pending.**
Final FF: `C:/BO3Tools/TOD2Cybercity/usermaps/zm_tod2_cybercity/zone/zm_tod2_cybercity.ff`; 2026-10-07T15:04:17.437771-04:00; 220,532,160 bytes; SHA256 `1f4f36b8028fdc1ced11f8d81e9e8fb0d502b3536f7257a00578942aad267ad4`.
Final receipts: [build/deployment](../../art/wunderfizz/build.json), [compiled assets](../../art/wunderfizz/compiled_assets.json), [native audio](../../art/wunderfizz/native_audio.json).
No game has been launched. GSC tests use native doubles and UI tests use a Lua
harness; they do not prove engine input, animation or playback. The first native
build passed 150 purchaser nav probes and fifty own-landing connections, but
its coarse BC7 glass alpha was rejected. The completed final build passes native nav, assets and audio with original
glass in uncompressed RGBA8 (format 14).
Compiled checks do not establish the user's experience.

## Short playtest route

1. **First jump and placement.** At floor 50, confirm one BO6 Wunderfizz is
   immediately reachable. Check ordinary north/south alcoves and a haven floor:
   clear entrance, grounded collision, readable facing and no obstruction to
   doors, descent, stairs, zombie risers or teleporters. The complete layout has
   one counter on each floor 1â€“50 and no individual perk vendors.
2. **Before power.** In solo, only an unowned Quick Revive is offered while
   fewer than three paid solo uses have been consumed. Its price follows the
   same ownership rule. In co-op, perks require power. The off machine should
   stay present and quiet; the solo exception should not turn on its idle
   electricity or hum. After power, unowned eligible perks become available.
3. **Price and grant.** With no perks, buy for 2,000; with one, the next costs
   2,500. Four owned perks mean 4,000; eight mean 6,000. Free bottle grants also
   increase the next price. Actually lost perks reduce it; temporarily paused
   perks still count. All nine owned means no further purchase or charge. Check
   the perk icon and effect after the drink, including the custom perks and
   Widow's Wine. Exhausting paid solo Quick Revive locks that offer only; the
   counter remains. A free solo Quick Revive retains its existing exemption.
4. **Controls and refusal.** Hold USE while facing the counter. Verify its
   hint binding appears in the prompt footer. Look at the front of the counter while holding USE. The selector hides the
   player's world prompt. Test keyboard arrows/Enter/Escape and controller D-pad/A/B as
   available. Mouse movement selects a row; releasing a click inside it buys.
   Selecting with arrows alone never spends points. Insufficient points or an
   unavailable/owned row should refuse clearly. Close without buying, reopen,
   and verify aim, movement, fire, HUD and other menus return normally. Holding
   USE through close should not repeatedly reopen it; release and hold again.
5. **Cancellation.** Let the uncharged selector reach its 20-second timeout.
   During a paid drink, test an ordinary interruption such as being downed.
   There must be no late grant, stuck bottle or duplicate refund. A living
   player's interrupted drink should restore their weapon and controls; a
   downed player's down state must remain intact. A failed paid grant refunds
   the recorded actual debit once. Shopping Free's zero debit must never create
   points. Death, disconnect, respawn and end-game must release the session;
   a deleted disconnected entity cannot be credited a refund.
6. **Co-op and haven lock.** Buyers at one counter have separate prices and
   sessions: one player's perk count never changes another's quote. Try two
   purchases at the same counter and purchases on different floors. Drinks
   continue independently; only the same machine's visible activation queues.
   A corrupted/locked haven refuses interaction and cancels its active session
   without granting. After the lock clears, the counter should work normally.
7. **Original presentation.** Inspect off/on surfaces and close/distant views
   for missing textures, incorrect transparency or popping. A purchase should
   show the original four-second animation, activation electricity/sparks and
   authored sounds, with its final effect stop intact. Check the transparent
   cover across distance/mips; source PNGs/shaders remain original. The final
   lossless glass texture adds about 64 MiB shared by all fifty counters.
   Power supplies idle FX
   and the original hum. Walk between floors: hum stays nearby and does not
   become fifty competing hum loops: only the nearest six voices are requested.
   Idle FX can retain handles on all fifty powered hosts and use the original
   EFX's native distance culling. Check repeated/co-op buys, off-machine solo
   Quick Revive, and the power-on transition for stuck effects or duplicated
   sound. Random existing perk jingles are intermittent, not immediate cues.

## Diagnostic reading

The current entry has `level.tod_diag = true` with `tod_dev = false`, so console
diagnostics do not require gameplay cheats. These are actual source event names,
not proof that any branch has run in the engine:

| Prefix and events | What to correlate |
| --- | --- |
| `[TOD_WUNDERFIZZ] INIT`, `OPEN` | Nine-perk roster; `client`, `floor`, `op`, `owned`, `cost` and available mask. |
| `BUY`, `GRANT`, `CLOSE` | Same `op`: quoted cost, actual `debit`, before/after score, one grant, then `reason=granted`. |
| `OPEN_REFUSED`, `BUY_REFUSED` | The source reason, such as `points`, `quote`, `offer`, `owned`, `haven`, `down`, `range` or `menu`. |
| `REFUND`, `REFUND_SKIPPED`, `CLOSE` | One actual debit/refund; `credited` versus `actual_debit`. Deleted entity reports `player_entity_gone`. |
| `[TOD_WF_MACHINE] INIT`, `SPAWN`, `PERK_PRECACHE` | Counter count, floor/model origin/purchaser `trig`/native `hint`/yaw/scale, and restored no-vendor precache. |
| `POWER`, `HUM`, `IDLE_REKICK`, `JINGLE` | Powered state and bounded nearby presentation. |
| `QUEUE`, `ACTIVATE`, `ACTIVATE_END` | Floor/client/perk, queue depth, `lag_ms`, duration, and scheduled final-note completion. These logs alone do not prove the native note played. |
| `USE_REFUSED`, `SPAWN_FAILED`, `QUEUE_FULL`, `RETIRE`, `SHUTDOWN` | Refusal/failure/cleanup reason; note the associated floor and operation. |

Preserve `console_mp.log` before the next launch. The existing capture helper
copies the raw log and a searchable extract without launching anything:

```powershell
powershell -NoProfile -File tools/capture_ai_logs.ps1 -OutputRoot tmp/wunderfizz/playtest_runs
```

When reporting an issue, give the floor, solo/co-op, owned perks, selected perk,
points before/after, power/haven state and input device. A screenshot or short
clip helps with textures, animation, sound timing and UI. The raw console log
provides the transaction and cleanup evidence; appearance and playback remain
the user's native observations.
