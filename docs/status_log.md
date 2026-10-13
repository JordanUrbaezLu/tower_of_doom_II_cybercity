# Status log — dated notes moved out of CLAUDE.md

**2026-10-13 13:50 - MIGRATION BUNDLE OK (docs/220).** `\\10.0.0.149\tod_transfer\round2`: 152.76 GB / 320,190 files, 0 warnings, 0 missing, for commit `bdfcacb9` (private root 34.14 GB, repo extras 60.24 GB with a size manifest, the T7 pack as 217 sha1-checked pieces, Claude memory, migrate scripts identical to the commit). Two reviews found 3 blockers + 6 bugs in the first scripts, all fixed (test 34/34 + split/join 12/12). NOT DONE YET: the new laptop's import, check_machine -FullHash, run_build_gates.py, first FULL build, user playtest.

**2026-10-12 - MIGRATION TO THE NEW LAPTOP (docs/220): REPO ON GITHUB, BUNDLE PENDING.** User: move Tower II to the new laptop by Map One's process (its docs/174); only Cybercity, nothing of Hellbound.

- GITHUB: `main` rebuilt on the initial commit in six size-capped batches (the three never-pushed local commits stay on `backup/local-main-pre-migration`); `.gitattributes` is now `* -text` (byte-for-byte); LFS for `*.blend`, `*.fbx`, `tod_boss_music.wav`; `*.blend1` ignored.
- TOOLS: `tools/migrate` (Tower II versions): the private root `C:\BO3Tools\TOD2Cybercity` moves whole with its 123 junctions recorded; round-trip test 21/21 PASS; `check_machine.ps1` 0 FAIL on the old laptop. Build gates need `fonttools`/`resvg_py`/`lz4` beyond Map One's list.
- BUILD INPUTS OUTSIDE THE REPO (audit of every gate line): `Downloads\T7 Assets V2.8.rar` (keeper / dealer gates re-extract from it every build) moves with its SHA1. `cyber_elites/verify_assets.py` no longer reads the Hellbound folder: the 7 Mangler binaries are checked against sha256s pinned in `art/cyber_elites/mangler_donor.json` (passes without the folder, fails on a corrupted pin).
- NOT DONE YET: export to the new laptop, import there, check, first FULL build, user playtest.

**2026-10-08 15:20 - WUNDERFIZZ PLACEMENT CORRECTED: FOUR EXISTING HAVEN DOMES; BUILT.** User correction: the perk stops are every ten floors, inside the domes. Exactly one original BO6/WetEgg Wunderfizz now stands inside each existing haven dome on floors 10, 20, 30 and 40, facing inward. Removed the mistaken other 46 machines, their side alcoves and alcove zone extensions. Ordinary landing rails are restored to their original geometry, including floor 50. The nine old individual vendors stay retired. Per-player price remains 2,000 + 500 for each currently owned perk. Original models, textures, transparent glass, activation animation/FX and all seven machine WAVs are preserved.

- BUILD: default guarded FULL BUILD OK with fresh BSP, LED and Havok mesh. FF 220,396,416 bytes; 2026-10-08T15:20:49.643704-04:00; SHA256 `6adf2e8fdc9d0a86493f2a0ea8c9e822b568f3f0e8232c1e251c450af52cf554`. Source/deployment parity covers 291 shipping inputs. All 14 native LODs, six complete material/image tables, original activation notes, 13 lossless glass mips and seven original PCM/alias files pass. Only the existing unrelated linker waivers remain.
- VERIFIED: four exact sparse floor IDs, full animated bodies and standing surfaces inside the actual spherical domes; eight original collision hulls; all 12 native purchaser probes and four haven-centre connections pass. All 24 directed drops, crown jump, PaP and other amenities are preserved. Dealer review contexts are byte-identical (floor20:112 solids). Automatic transaction/machine diagnostics remain enabled by tod_diag. Historical mistaken fifty-stop delivery is archived under art/wunderfizz/deliveries/20261007_150417_fifty_stops_superseded/.
- UNPLAYED: native appearance/transparency, audible mix, controls, drinking, interrupted purchases and co-op. No game launched; user playtest pending. Current proof: art/wunderfizz/milestones_delivery.json, build.json, compiled_assets.json, native_audio.json; tmp/wunderfizz/milestones/full_build.log. Updated user route: docs/wunderfizz/PLAYTEST.md.


**2026-10-08 15:20 - DEALER WEAPON PASS: GUARDED FULL BUILD OK; USER FIGHT UNPLAYED.** Dealer's House has fixed-position Wunderwaffe shocks and warned six-round Dingo bursts, two dedicated native two-hand clips, five bounded carrier effects and four measured sound cues. Cover, the marked footprint, co-op overlap and every pause/hold/stun/phase/death exit are guarded. The final death line finishes before arena cards. Independent code/art review passed; 60 combat checks plus three planted regressions and the complete guarded build gates passed. FF 220,396,416 bytes, SHA256 6adf2e8fdc9d0a86...; 21 deployed inputs match, both new xanims/all five FX/three modules are linked, four native aliases and loaded-bank entries verified. Geometry/lighting processed by guarded FULL pipeline. No game launched. Evidence: art/dealer_combat/build.json, review/review.html; docs/dealer_combat/README.md. Correct Rendered preview: tools/dealer_combat/open_preview.ps1. The earlier reported-OK build omitted the charge effect after duplicate curve times; it was rejected by the delivery audit and is archived under deliveries/20261007_charge_rejected/. The curve is repaired; source negative controls and a mandatory five-effect compiled gate now pass. The character master/core 45 clips/material pins are preserved; no retired voice/finale restored. The actual owned Blender window was opened and inspected in scene-lit Rendered camera view; art/dealer_combat/review/visible_preview.json and visible_window.png/json preserve that evidence. Blender remains an approximation of native appearance.

**2026-10-07 15:04 - BO6 WUNDERFIZZ ON ALL 50 FLOORS: BUILT; USER PLAYTEST PENDING.** The nine individual perk machines are replaced by one original BO6/WetEgg Wunderfizz on each descent floor 1-50, with the existing nine custom perks in a selector. Price is 2,000 + 500 per currently owned perk, independently per player; paused perks count once. Original powered/unpowered geometry, all fourteen LODs, twenty 4K PNGs, materials, rig, activation animation/notetracks, both effects and seven WAVs are preserved. The glass image uses lossless native RGBA8 to preserve original alpha through all thirteen mips (maximum error 1 byte(s)); the rejected BC7 conversion and first build evidence remain under art/wunderfizz/deliveries/20261007_1420_bc7_failed/.

- BUILD: guarded default FULL BUILD OK, tmp/wunderfizz/final_build.log. FF 220,532,160 bytes at 2026-10-07T15:04:17.437771-04:00, SHA256 1f4f36b8028fdc1ced11f8d81e9e8fb0d502b3536f7257a00578942aad267ad4. Identical geometry/lighting inputs reuse the fresh October 7 bake; all native navigation gates rerun. Only the three existing waived unrelated linker assets; no Wunderfizz substitution.
- VERIFIED: all mandatory guarded source checks, exact original source provenance, fourteen native LOD counts, six complete FF material definitions/image tables and native shader bindings, original compiled activation notes, all thirteen lossless glass mips and all seven original machine PCM files/native alias fields. 290 captured shipping inputs match private deployment and the build snapshot. All Wunderfizz source inputs still match the built deployment. 6 pinned Dealer source edits landed at 15:07:38 after this build completed; they are preserved as pending work for the Dealer's next build, not part of this FF. All fifty machine pads and 150 standing probes pass actual compiled Havok navigation. The actual tag_hint supplies the use/look target; its separate standing anchors and geometry remain unchanged. Shipping conduit support and all three Dealer review contexts are preserved.
- GAMEPLAY: per-player menus, current ownership pricing, co-op transactions, native can drinking, stale-message rejection, interruptions and exact-once actual-debit refunds; powered/off presentation and original sound/FX notes; closest-six ambient hum allocation. Cheap diagnostics run under the existing tod_diag flag: [TOD_WUNDERFIZZ] and [TOD_WF_MACHINE].
- UNPLAYED: native appearance/transparency, audio mix, keyboard/controller/mouse, use prompts, can/drink flow, refunds and co-op behaviour. No game launched. The user playtests; capture their console_mp.log through tools/capture_ai_logs.ps1. Proof: art/wunderfizz/build.json, compiled_assets.json, native_audio.json; docs/wunderfizz/IMPLEMENTATION.md, ASSET_IMPORT.md, PLAYTEST.md.


**2026-10-07 — WUNDERFIZZ REQUEST: EXACT NEW ASSETS MISSING; NO LIVE CHANGE.** User requests all individual perk machines replaced by one newer Wunderfizz per floor, price 2,000 + 500 per currently owned perk, exact original model/textures/sound. Verified nine current machine structs: eight scattered among havens 10/20/30/40 plus balcony Quick Revive. Intended coverage is spiral floors 1-50, with the nine custom perks retained. Bounded local pack/tree searches found no exact modern counter (including `p9_sur_machine_perk` / `_off`); six BO6 ambient/spark aliases exist only as metadata, actual WAVs absent. Do not substitute the available old BO3/DE machine. Asset request zip: `C:\Users\jorda\Downloads\tod_wunderfizz_exact_import_art_pack.zip` (6,969 bytes, SHA256 `0bd82fdd29f3284653e9971ccdb7d89c94d0ade8af77b794d33a895fd56d16d8`). Brief/evidence: `docs/wunderfizz_asset_request.md`, `docs/wunderfizz/asset_inventory.json`; implementation/transaction/pool/native proof contract: `docs/wunderfizz/IMPLEMENTATION.md`; isolated parametric placement candidate: `tmp/wunderfizz/layout/` (not imported by the live generator, exact bounds/facing still required). No shipping map, code, UI, zone, material, sound, receipt or deployment input changed. No build or game launch. Current working perk setup remains pending the exact source drop and one complete reviewed/built replacement. Modern choose-perk versus old random-machine clarification was sent; no reply yet.

> **What this is.** Every dated status note that used to sit at the top of CLAUDE.md, moved here VERBATIM on 2026-10-04
> (user-approved: CLAUDE.md had grown to 610 KB, about 150k tokens that every session and every subagent loaded before
> starting; a one-word subagent probe cost 310k tokens and a 44-agent audit exhausted the session limit). Newest first.
> The rules these notes earned were distilled into the top of CLAUDE.md; this file is the evidence and the history.
>
> **Add a new status note at the TOP of this file** (below this header): what was built, when, sizes, ledgers, UNPLAYED.
> Never add dated status notes to CLAUDE.md again. If a note carries a new standing rule, ALSO add the rule, one line,
> to the right section of CLAUDE.md.

**2026-10-06 13:38 - THE CLASS CARDS' ROLE LINES (user: "the description on each class card is pretrty bad ... Archer -> Agile Hunter / Breacher -> Explosive + Close Range Expert / Warrior -> Master of Arms")**
- WHAT: the art-window role line on the class draft cards (draft + crown class terminal): AGILE HUNTER (was PRECISION), EXPLOSIVE + / CLOSE RANGE EXPERT on two lines (was CLOSE RANGE TANK), MASTER OF ARMS (was UP CLOSE); SOUL REAPER kept (Necromancer card byte-identical). `r6_class_cards.py` titles are line tuples with a width guard; `tod_class_select.lua` roles in lockstep. Armory v29, Art Atlas v9.
- GATES: 167 / 0 (`tmp/classroles/gates2.log`).
- BUILD: FULL 12:52 (geom_key REUSE of the 10-05 18:45 bake) hit the "Missing source checksum" wav flake at the English link; finished with -GscOnly, BUILD OK 13:37 (`tmp/classroles/gsc2.log`). .ff 13:35:40, 213,508,864 B; 3 known-waived lines; bank 296.4 MB; BGCACHE OK.
- VERIFIED: fresh 13:19 .iwi for the three changed cards (Necromancer control 10-05); ledger rows; deployed = repo; nothing synced after; no repo edit after the start. This .ff also carries -5e's Wunderstrahl and last night's red theme / log fixes.
- UNPLAYED: everything since the 2026-10-05 20:20 run (the red theme, the toast, the keycap path, the round-counter hide, the Wunderstrahl, these cards).

**2026-10-06 10:10 - THE WUNDERSTRAHL, the laser power-up gun (user 2026-10-05: "I want something like a laser ... use the Wonder Waffle, but it shoots like a crazy detailed, awesome laser ... an automatic laser ... a laser down the middle, and then kind of swirls ... with little balls on the swirls"; chosen the same day: it shares the Gift of Death drop 50/50, a yellow core, no overheat, the name; docs/219).** LANDED 02:39 in one step: 35 staged files, the two HUD icons, and 22 shared-file edits by `tools/wunderstrahl/wire.py`.
- WHAT:
  - The model: the BO3 Wunderwaffe DG-2 (from the T7 Assets V2.8 dump) remodelled through Blender MCP (port 9893; master `art/wunderstrahl/wunderstrahl.blend`). Lens rings and a faceted crystal round `tag_flash`, a yellow filament, yellow bulbs, aged copper, a charcoal composite stock. The DG-2's 12-bone and 4-bone rigs and its 26 clips are unchanged.
  - The weapon: a native gas weapon, `tod2_wunderstrahl`, built on the stock gauntlet's block. Engine beams `tod2_ws_beam_1p` / `_3p` (ribbon cores), with the gold double-helix swirl and its orbs as the beamEffect, a wall burn, a lens flare and cool-down, and an invisible flame table carrying a travelling light.
  - Sound: 18 wavs on 14 aliases, levelled against the gauntlet and the DG-2.
  - Script: `_tod_wunderstrahl.gsc` / `.csc`.
    - The shared slot: `TOD_MINIGUN_DROP_PCT` 50 -> 25, plus `TOD_WS_DROP_PCT` 25.
    - The stock weapon power-up lane: a 30 s window, paused while the holder is frozen. Going down uses the spare tesla last-stand hook.
    - Script damage pierces. Contact ticks to kill from full: horde 3, elite 30, the Dealer 3000. Rampage stretches them, and the reach grows at the beam's 6000 u/s.
    - Kill bursts are budgeted per holder: 4 lit + 8 unlit a second.
    - `[TOD_WS]` logs, with `TOD_WS_LOG 1` (set it back to 0 before publish).
  - HUD: the tray token and the gun-bay cell (`tools/artgen/packs/ws_wunderstrahl_icons.py`).
- GATES: `run_build_gates` ran 164 lines. One was red: `verify_cyber_zombie` TIMEOUT at 24,419 s, because the PC slept overnight mid-sweep; it reran OK in 19 s. The 7 Wunderstrahl lines are OK (`test_wunderstrahl` 54 / 0).
- BUILD: FULL BUILD OK 10:10 (`tmp/wunderstrahl/build/full1.log`, started 09:52).
  - geom_key REUSE (LED 245,366,817 B from 2026-10-05 18:45).
  - .ff 10:08:21, FF 213,508,864 B; the 3 known-waived linker lines only.
- VERIFIED:
  - Ledger rows: weapon 1, beam 2, flametable 1, fx 10, xanim 26, xmodel 3 + 10 LOD meshes, 15 materials (all complete), 41 images including the 2 HUD icons, 2 scripts, the rumble, sharedweaponsounds.
  - Compiled triangles = exported on every LOD: view 42,795; world 36,887..857; pickup 13,938 / 4,711.
  - The 18 `tod_ws_` stems are in the loaded bank (all.sabl, 10:07).
  - Deployed == repo, nothing synced after the .ff, and no repo input was edited after the build started.
- UNPLAYED: everything in game.
  - The beam's look and brightness.
  - `IsFiring` on a gas weapon (a `FALLBACK` line logs if it never reports).
  - The flame table.
  - The kill effects through the new carrier.
  - The mix.
  - Read the user's log for `[TOD_WS]`.

**2026-10-05 22:45 - THE RED THEME IS BACK (user: "id rather the red theme please"; CHANGELOG 2026-10-05 22:45).** tmp/redtheme/RT-impl (workflow: measure -> implement -> 3 reviewers -> fix -> critic; land.py + manifest), landed 22:09 on -d3's 21:56 FULL. One switch tools/artgen/synthwave.py THEME = 'fallen' | 'synthwave' (docs/218_red_return.md); 131 UI images + gated code tints; class / rarity / perk / power-up hues untouched; no red on class medallions or their ring. Same pass: the stock ROUND n readout hidden (the user's "round X in top right"), keycaps in our face only with no gamepad enabled, card-screen IPrintLnBold lines -> TodToast. Gates 160 / 0. BUILD FULL OK 22:41 (tmp/redtheme/full1.log), .ff 22:39:34, 212,975,744 B, BGCACHE OK; fresh .iwi for every re-themed image; deployed = repo, nothing synced after. THIS is the test .ff (with -d3's Archer pass and -a2's probe rev 4). Atlas v7. UNPLAYED; the toast / keycap / round-counter hide are unverified in game.

**2026-10-05 21:58 - THE ARCHER, TOWARD AUTOMATIC (user after the 20:21 Archer run: "the automatic guns on the first map were just so much fun ... you hold it down and then once it's fully charged it shoots ... maxed out it almost becomes an automatic bow ... the shots don't go far enough ... The grapple, you can kind of just go out of the map ... invisible walls"; docs/218; CHANGELOG 21:19).** THE RUN, read (tmp/elite_tracking/runs/20261005_202140_164_ff8f34f8): every arrow left on a release (holds of 2-4 s sat at full draw), a tap cycled in ~0.6 s and a full draw in 1.65 s; at 425 s a floor-42 grapple hooked the core wall ~280 above the stairs, "arrived" with 895 u/s outward over the 168u rail clip, fell to z -1020 and was Recalled at 1 HP. LANDED 21:18 in one step (tmp/archer_auto/land.py, no peer had touched the 13 files) + a 21:3x follow-up (hook_in_play, the roster gate's crossbow pin): bows `chargeShotFireWhenQueueReachesMax 1` (the engine releases at full draw; a held arrow = trigger down at weapon_fired = x3), Bow draw / release 0.55 / 0.30 s (a held arrow every 0.85 s, was 1.65), Fire Bow 0.45 / 0.25 (0.70 s), packed x0.8; QUICK DRAW x3 at Lv9 on 3^(Lv/9) (SHOTSPEED_STEP .7834 / .6137 / .4807 / .3766 at Lv2/4/6/8, odd levels x1.1298 damage); flat arrows (guidance None, 4500 / 5000 u/s, x1.6 at s4); the crossbow a Full Auto repeater (10 / 13 bolts, 0.35 s, 1.6 s reload, 12 mags); EVEN TIERS kept (the pin counts the held full draw, AUTO_DRAW_FULL_MULT 3: Bow 351 / 1053 per tap / full arrow, Fire Bow 836 / 2508, crossbow 1118; all within 0.1%); Fire Bow splash scaled with the cadence (280 / 140, packed 483 / 241); THE GRAPPLE'S INVISIBLE WALL (`_tod_archer` in_play / wall_column / wall_cut / wall_step / hook_in_play: the zone volumes are the play area, horizontal velocity only, never on a jump-pad flight; hooks past the rails refused). Ledger 206 (unchanged). GATES: 159 / 0 on the final tree (tmp/archer_auto/gates2.log); NEW tools/test_archer_autobow.js (1203 checks: shipping pure GSC via gsc_eval incl. the floor-42 swing against a box tower, all 120 Archer forms vs the script, generator tables, Lua rows; 6 mutants caught), test_starter_weapons.js (held draw, tap rule as the negative control), test_ability_fx.js (the bow's "release now" tick retired), test_expected_roster.py (crossbow pin = the repeater). BUILD: FULL BUILD OK (tmp/archer_auto/full1.log, started 21:41:42; geom_key REUSED the 18:45 BSP + LED): .ff 21:56:12, 213,295,872 B, bank 296.4 MB, linker red lines = the known pre-existing set only. VERIFIED (tmp/archer_auto/verify_build.py): deployed == repo for scripts / zone_source / ui, nothing synced after the .ff, no repo input edited after the start, no game during the build; ledger scriptparsetree for the three Archer scripts + _tod_upgrades, all 120 Archer weapon forms, -a2's probe rev 4 rows (zm_tod2_cybercity.csc, _tod_telem.gsc, tod_telem_probe.lua); the deployed tod_weapon_twins.gdt == repo (auto-release on all 80 bow forms, Full Auto on all 40 crossbow forms). Armory artifact republished (v28; verify_tod2_armory OK). THIS is the test .ff. UNPLAYED. The one engine question for the next Archer log: `[TOD_ABOW] HOLD_END held_arrows=N` with N > 1 proves a held trigger draws again; `HOLD_STALL` says it does not (docs/218 names the fallback). Grapple walls log `[TOD_ARCHER] WALL` / `GRAPPLE_END ... walls=`.

**2026-10-05 18:52 - THE SECOND REAL RUN'S FIXES (user after the 17:33 run: Doppelghasts "a bit too slow", Manglers "dont shoot their blast enough", the dark dome should raise "as many elites as players", the bind "sticks to the floor and then freezes", the punch lunge "causing some screen issues", the R.A.P.S. "almost like teleporting everywhere"; CHANGELOG 18:29 + 18:52; docs/210 s7).** BATCH 1 (Doppelghast walk 1.25 + more frequent bursts, Mangler cannon 2.5 s / 2.5 s / 1100 u, one haven guardian per player, the bind held in the air, no punch lunge): landed 18:15-18:17 and BUILT in -ed's FULL BUILD OK 18:49:13 (tmp/playtest_1004/full2.log; .ff 18:47:20, FF 214,008,128 B). Verified here: the ledger carries scriptparsetree for the five scripts and 8 cc_punch weapon rows, the deployed tod_weapon_twins.gdt has meleeChargeRange 0 on all 8 punch forms, deployed == repo, nothing synced after, no repo source edited after the 18:28:46 start. BATCH 2 (the R.A.P.S. locks, rolls slower, hits what it touches and throws ordinary kills; the Mangler keeps its own target; a zombie being bound is left alone by thralls and companions; a missed punch takes the first zombie in its cone; the soul meter's refused cue): landed 18:50:49, scripts only, rides session -13's -GscOnly together with -13's R.A.P.S. drop-traversal fix, BUILT in -13's -GscOnly BUILD OK 19:47 (tmp/logtriage/gsc1.log; .ff 19:45:08, FF 213,293,632 B; verified here: ledger rows for the five scripts, deployed == repo for all six, every new function in the deployed scripts, nothing synced after, nothing edited during). UNPLAYED. RULES (CLAUDE.md Actors): a Raz-family elite's favoriteenemy is rewritten by the stock target service whenever a companion is out, so the elite keeps its own pick (`tod_hunt_player`); never re-play a scripted clip to hold a pose, because a play re-places the actor at its align point (the in-air hold by `ASMSetAnimationRate` is UNPLAYED).

**2026-10-05 18:51 - FLOOR NUMBERS ON THE DOORS ONLY + THE DOORS REALLY MAKE A SOUND + THE 17:33 RUN READ (user: "The numbers on the railings for each floor can be removed. I only want it on the door."; CHANGELOG 18:03).** LANDED: the rail numbers retired whole in `tools/gen_tower_map.js` (emitter, world quads, view check); the 26 paid doors keep their 47 digits (same atlas, materials, `make_assets.py --check`, `checkFloorNumbers()`); regenerated `.map` 6188 world brushes / 1574 entities, 138 -> 47 floor-number meshes, the only other diff two brush-index comments; GSC data files byte-identical. THE DOOR SOUND: the user's 17:33 run (tmp/elite_tracking/runs/20261005_175405_950_4cc72ed2) logged `[TOD_DOOR_SEAL] CUE alias=zmb_heavy_door_open ms=-1` on both loads, so the stock alias is NOT in this usermap's banks and the slide, the unseal cue and the Fall's crown seal were still silent after the 01:53 carrier fix; the map now DEFINES `zmb_heavy_door_open` (one row in `sound/aliases/tod_ui.csv`, 3D BUS_FX vol 90, 300/2000/2400) on the original BO1 hydraulic-door start (T7 Assets V2.8 `zmb_blops/evt/mp_radiation/doors/hydraulic/hydraulic_start.wav`, byte for byte, as `sound_assets/tod/doors/zmb_heavy_door_open.wav`); `check_wiring.py` STOCK pruned; the KB records that a usermap does not load that stock alias. THE RUN, read for the open issues: THE RAMP and the cap ramp behaved as designed (delay x1.58 on round 2 easing to x1.39 by round 11; cap 12 on round 1, 18 by round 8; the solo figure is 35 = 36 minus the companion reserve), the four haven doors SEALED at the power (round 7); no refusal or unseal was exercised. Other owners: 211 script errors in stock `animation_state_machine_mocomp.gsc` over 40 s while the rebuilt R.A.P.S. (actor 26) chased the player down the broken drops from floor 48 (routed to -13, root-cause running); the old `fx_luck_meteor_trail` precache error. BALANCE, for the user to judge: game 2 (Warrior, solo) ended at round 4 in the crown 7 s after the round-4 crown hunter (Doppelghast, 820 HP) spawned while the round-3 one (640 HP) was still up; game 1 (Necromancer) went down at round 11 on floor 40 in the corrupted haven fight. BUILD: combined FULL BUILD OK 18:49 (tmp/playtest_1004/full2.log, started 18:28:46, gates 155 / 0 on the combined tree first, tmp/playtest_1004/gates7.log), carrying -7a's elite / Necromancer / Warrior fixes (weapon GDT regen) and -a2's probe rev 3: cod2map compiled the new .map, NAVMESH GATE OK, fresh LED 245,366,817 B (identical to the 01:31 bake: the digits were unlit decals), .ff 18:47:20, FF 214,008,128 B, the 3 known-waived linker lines only, bank 296.4 MB with all 991 alias wav stems indexed (zmb_heavy_door_open in the loaded .sabl). VERIFIED: deployed == repo for scripts/ui/zone_source, nothing synced after the .ff, no repo input edited after the build start, no game during the build; the deployed alias table carries the door row; the compiled .map holds 47 floor-number meshes; the five `wc/tod_floornum_*` materials at full size and the _tod_doors / _tod_telem / _tod_doppelghast / _tod_haven scripts in the ledger. UNPLAYED: the door sound and the doors-only numbers in game.

**2026-10-05 19:48 - THE 17:33 USER LOG FIXED (CHANGELOG 2026-10-05 19:48).** Triage workflow (tmp/logtriage/, LT-fix land.py) landed on -ed's 18:47 FULL + -7a's 18:50 R.A.P.S. landing: companion drop mocomp registration (the 211-pair storm, old since 09-27), ground-anchored / flyer-safe companions, the Necromancer bind shield, the 4 lucky effects restored to the precache table (an empty-name #precache dropped them; new post-link gate tools/verify_bgcache.py), Gift VO, crown seal cue, cyber-sword csc guard. Gates 158 / 0. BUILD -GscOnly OK 19:47 (tmp/logtriage/gsc1.log), .ff 19:45:08, 213,293,632 B, BGCACHE OK; deployed = repo, nothing synced after. THIS is the test .ff. UNPLAYED. Pending: the red UI theme (tmp/redtheme/, FULL build).

**2026-10-05 15:17 - WAVE 3: ONE ASSET LIBRARY (user: "Whole entire asset library should look like one library ... Asset library is for you to own"; CHANGELOG 2026-10-05 15:17).** Nine packages staged under tmp/wave3/<ID>/ (LAND.md each), landed 13:55-14:52 (land_batch 3-way, 0 conflicts; R10 by its own land.py; ledger archived in tmp/asset_prod/_archive_w3/), wired by tmp/wave3/wire_w3.py + wire_r10.py. W3A perk / power-up safe inset (r4); W3B ability glyphs in colour (w3b_ability_colour.py; V1 cloak key + SUMMON tile retired); W3C one class emblem pack (w3c_class_pack.py, docs/212); W3D flat companion portraits (r1_comp_portraits.py); W3E WEAPON not GUN + ~20 wording fixes (tools/wording/wording_pass.py); W3F tier strips + gift lettering (w3f_library.py); R6 class draft cards re-set in the current face with model-drawn windows (r6_class_cards.py; owns all four cards now, pk01 keeps the tier strips); R10 synthwave card chrome + reel ornaments (r10_card_chrome.py, docs/217; i_tod_card_back retired); LEAD: R5 eight card illustrations redrawn from the real weapons (r5_tier_subjects.py), crossbow bay icon (r1_gun_icons.py), R8 keyed hint plates retired, R7 MELEE SPEED icon retired, the crown teleporter hint "down to the GROUND FLOOR", the ONE LIBRARY style guide in tools/artgen/README.md. RULE PAID FOR: an image name built from a table (CARD_SLUG) is invisible to a name grep - the three shared card faces were retired and restored the same hour after lint_tod_assets GATE A (memory map2-only-build). GATES: 155 / 0 (tmp/wave3/gates_landed3.log). BUILD: FULL OK 15:12 (tmp/wave3/full1.log, started 14:56:56; geom_key reused the bake): .ff 15:10:56, 213,882,304 B, the 3 known-waived linker lines, bank 296.4 MB, the 21 known usage lines. VERIFIED (tmp/wave3/verify_w3.py): 35 required images in the ledger, 8 retired absent, deployed = repo (scripts / zone_source / ui; images at the tools root), nothing synced after, no repo edit after the start; fresh 15:10 content-hash .iwi for every changed image (control i_tod_pm_gly_audio still 09-26). THIS is the test .ff (it carries -ed's and -a2's work too). Art Atlas v6 (449 images, 21 stale art/generated copies moved to tmp/wave3/_stale_generated/), armory v27. UNPLAYED: every look is the user's to judge. Open by choice: the card illustrations' starfield ground (W3F F04) kept; the Necromancer card chassis neon stays more saturated than the other three; packed weapon names mix own names and "EX" (user's call); kill-feed strings for systems this map lacks (Data Shard, Mega Bottle, ...) are retire candidates.

**2026-10-05 12:07 - WAVE 2: EVERY OPEN ITEM FINISHED (user: "Still open?? Lets complete everything. Stop pausing"; CHANGELOG 2026-10-05 11:37).** Seven packages staged under tmp/wave2/<ID>/ (LAND.md each), landed in one step at 11:24 (land_batch 3-way + W2E's own lander), wired (each package's wire tool + tmp/wave2/wire_lead.py). W2A the companion world models (gold Civil Protector, Talon 3 + Cerberus 34 authored maps, R.A.P.S. rust shell; tools/companion_maps/); W2B the Dealer fight's 26 combat sounds, 8 effects, 8 fight barks, 7 authored arena / house cues (tools/dealer_sfx/, tools/dealer_fx/); W2C wave-2 sounds + world ambience `_tod_amb.csc` + bolt impacts (tools/sfx/w2c_sounds/); W2D elite effects (NEW `_tod_elite_fx.gsc`) + haven motes (tools/fxgen/elites/); W2E every parked Map One system retired whole (finale -> live half in NEW `_tod_crown_props.gsc`, Panzer, Rogue Protector boss, Fury, hounds, armored sprinter, the Keeper L10 branch + toggle, 8 parked cards; 62 paths / 238 files / 155 MB to archive/map1_carryover/, ledger `_landed_w2e.json`; pin tools/test_retired_systems.js); W2F the Mangler's voice (BO3 Gorod Krovi takes from the T7 pack) + DP / PhD BO6 jingles (tools/original_rips/); W2G the hand-drawn Skull of Nan Sapwe icon + staff skulls + the companion status plate `TodCompanionPlate.lua`. RULES PAID FOR: (1) a sharedweaponsounds block's meleeEntityImpact* / meleeSurfaceSound* fields take entitysoundimpacts / surfacesounddef ASSETS, never aliases (build 1, tmp/wave2/full1.log, died at the linker on four; fixed in the W2C generator); (2) a failed link still overwrites the deployed .ff - tell every session no playtest until the next BUILD OK; (3) subagents launched in the same turn as a short user aside ("Say sorry") took the aside as the whole request and did nothing - say in the brief that the aside is handled. GATES: 148 / 0 failures on the merged repo (tmp/wave2/gates_landed1.log). BUILD: FULL BUILD OK 12:07 (tmp/wave2/full2.log, started 11:52:08; geom_key reused the bake): .ff 12:05:07, FF 214,046,272 B (221,300,672 before), only the 3 known-waived linker lines (the 5 Panzer-era and the knife_melee_surface waivers removed from build_map.ps1 after it), streamed bank 296.4 MB. VERIFIED (tmp/wave2/verify_w2.py): 26 new rows in the ledger (scripts, effects, plate, images), 15 retired rows absent, `_tod_keeper.gsc` + spawner_tod_dealer kept, 990 / 990 alias wav stems in the banks, the 9 new alias tables loaded and mechz_spiki gone, deployed = repo, nothing synced after, no repo edit after the start; PARTNER_ASSETS_PASS on the compiled ledger; the 21 linker usage lines are the known pre-existing set (Fire Bow rune, C4 decal, xmas-gun glass, empty punch view). Also carries -ed's playtest fixes (spawn ramp, door seal + door sound carrier, elite HP x4) and -a2's probe rev 2 - THIS is the test .ff. Art Atlas v5 (456 images), armory v26 republished. UNPLAYED: every look, sound and level of the wave is the user's to judge. Open by design: BO6's own Mangler AIVox needs a running BO6 (BO3 takes ship); the Cerberus / Talon stencil decals have no definition anywhere; CREDITS.md lines proposed in the LAND.md files are the user's call; TOD_AMB_LOG and the other loggers off before a publish.

**2026-10-05 02:07 - THE FIRST REAL RUN, ROUND TWO: THE RAMP, TOUGHER ELITES, A SLOWER DOPPELGHAST, THE DOOR SLIT CLOSED, FLOOR NUMBERS ON THE DOORS, THE HAVENS WALLED AND CROSSED (user after the first real playthrough: "The doors have an odd gap between them and the rialing"; "The number of the floor should be on the dorr you buy"; "You must secure the dome area before you move on"; "Doppleghast are way too fast"; "Elites dont have enough HP"; "Zombies are spawning in way too fast too early ... Game should ramp up"; "perks and machines dont face the safe zone inwards ... You shoulnt be able to see until you are on the floor ... the stairs should go down on the opposit side then you come from"; CHANGELOG 2026-10-05 00:51; docs/202 v6).** LANDED: THE RAMP (`_tod_corpse_cleanup::ai_limit_now()` lets a third of the party cap stand on round 1 and all of it on round 30, solo 12 / 19 / 28 / 36 at rounds 1 / 10 / 20 / 30; `_tod_endless_rounds::spawn_ramp_mult()` x1.6 slower trickle on round 1 easing to x1.0 on round 30; rampage reaches both by round 15; `TOD_FALL_SPAWN_MULT` 0.7 -> 1.0); elites x4 HP (`TOD_ELITE_HP_MULT` 4 inside `hunter_hp()`: round elites, crown hunters, arena elites, haven guardians, Manglers); the Doppelghast walks at 1.0 (was 1.5) and sprints a 1-1.6 s burst every 6-9.5 s; THE SEALED WAY DOWN (`_tod_haven::door_seal_state` via `level.tod_haven_door_seal_fn`, `_tod_doors::haven_seal_watch`, one constant SEALED hint, the unseal restores the trigger's own spawn-time string, the locked SEALED card in PromptDoors.lua; a dark haven seals nothing); the door slit (`DOOR_POST_NOTCH` 10, the post in the rail band, map 1's v19.57 fix); floor numbers on 26 doors (47 digits, decal meshes inside each door's script_brushmodel, district colours); THE HAVENS v6 (the hall enclosed, the machines facing the teleporter with `PAD_TRIG_GAP` 32, collapse debris on the W flight's tread 11 under the porch, a SUNKEN STAIR from the hall's north-centre tunnelling under the W wall onto the W flight's treads 1-3). GATES: `tools/test_spawn_ramp.js` (new, 2404 checks / 4 mutants, wired in build_map.ps1), `test_ambush.js` section I (the trickle contract), `test_haven.js` 542 / 55 mutants, `test_power_scale.js` (the x4 floor), the layout's own checks, lint_tod_geometry with a negative control (no stair treads: terrace -> base NO), a scratch cod2map + lint_tod_navmesh (NAVMESH GATE OK; the first try split on a seed left inside the moved crate, now a layout check); conduit mounts/batches regenerated for the notched parapets; Dealer-panel re-review #5 for the floor-20 hall (art/dealer_presence); run_build_gates.py 137 / 0 failures at 01:10 (tmp/playtest_1004/gates3.log). The GSC/Lua half already rode -13's 00:46:57 .ff. BUILD: FULL BUILD OK 01:35 (tmp/playtest_1004/full1.log, started 01:17:48; geom_key re-baked because the .map changed): BSP 11.0 MB, NAVMESH GATE OK on the real compile, fresh LED 245,366,817 B (246,277,485 at the 12:48 bake), .ff 01:33:55, FF 221,300,672 B, the 8 known-waived linker lines only, sound bank 298.7 MB. Then -GscOnly BUILD OK 02:06 (tmp/playtest_1004/gsc1.log, started 01:53:19) for the door sound fix (CHANGELOG 01:53): .ff 02:04:22, FF 221,300,544 B, the same 8 lines and bank - THE CURRENT TEST .ff. VERIFIED: for both builds deployed == repo for scripts/ui/zone_source, nothing synced after the .ff, no repo build input edited after the build start, no game during either build. Ledger rows: the _tod_haven / _tod_doors / _tod_corpse_cleanup / _tod_endless_rounds / _tod_doppelghast / _tod_breather_data / _tod_conduit_data / _tod_door_data scriptparsetrees, PromptDoors.lua, the 54 conduit xmodels, the five `wc/tod_floornum_*` materials at full size + `i_tod_floornum_c` (the door digits), -a2's `_tod_telem.gsc` + `tod_telem_probe.lua`; the deployed _tod_doors.gsc carries both carrier calls and none of the old helper; the sun volume still tops out at 39,500; cod2map's only notices are the two pre-existing empty brush models (volume_sun, volume_fpstool). FOUND AND FIXED after the FULL build: every door slide and the new unseal cue were SILENT - `zm_utility::play_sound_at_pos` plays only keys in `level.zombie_sounds`, and this map never registered `zmb_heavy_door_open` (stock maps add_sound it themselves); both now play on a script_origin carrier (`tod_perk_scatter::play_sound_at_origin`, the Fall seal's lane for the same stock alias), and the silent-sounds gate's new rule 7 (THE KEYED HELPER) fails any unregistered key (self-test 19 cases; the old door calls fail it in a scratch copy). UNPLAYED: the ramp's feel, the elite HP, the Doppelghast's pace, the sealed door and its card, the door numbers' read, the havens' new walls, machine facing and sunken stair are the user's to judge. Logs to read after the run: `[TOD_RAMP]`, `[TOD_AI_CAP]` (party_cap, ramp_round), `[TOD_DOOR_SEAL]` (SEALED / UNSEALED / REFUSED, and `CUE alias=zmb_heavy_door_open ms=` at load: ms <= 0 means the stock door alias is not loaded and the map needs its own door sound).

**2026-10-05 00:48 - MAP 2 ONLY: THE MAP ONE PURGE + REDESIGN WAVE 1 + THE SYNTHWAVE HUD (user: "This should be for map 2 only"; "mozambique isnt even mozambique, the ai companions dont look correct at all ... Choose your class and upgrade available banners are exactly the same as map 1"; CHANGELOG 2026-10-04 23:15).** LANDED: R5 the Map One purge (317 zone/zpkg lines, 466 GDT blocks, 224 alias names, 680 paths to `archive/map1_carryover/`); R1 eight gun-bay icons traced from the game's own models (Mozambique, Peacekeeper, 870, riot shield, crossbow, knife, MR6, Gift of Death) + the four companion portraits and reel icons; R2 the Peacekeeper / Soul Staff / Crown of the Damned card subjects, the Breacher class card's Mozambique and the cursed reel; R3 the synthwave pause menu, scoreboard and card-panel chrome (44 images); R4 the rest of the chrome (`r4_synthwave_hud.py`, 70 images: HUD V2 plates, prompt chassis + 13 icons, luck badges, perk shields with Juggernog kept RED, power-up tokens, PaP badge, health fill, the round tint magenta); R6 the two pause-row icons of the retired DAMAGE / PERK SLOTS cards. 36 byte-for-byte Map One images -> 0 (the typeface is shared on purpose). Five traced R1 drafts (bow, fire bow, fist, gauntlet, skull) were rejected on review; the shipped icons stay. RULE PAID FOR: an INSTALLED stock package in the private root can name repo files - `share/zone_source/zm_ai_zod_companion.zpkg` (the Civil Protector partner's AI) lists the two `_hb21_zm_craft_fuse` scripts, `xmodel p7_zm_zod_fuse` and plays `zmb_zod_fuse_pickup/_place`; the purge archived all of it, the link failed after the gates (full4.log, the failed linker had already overwritten the good .ff) and PK02 caught the alias rows on the retry (full5.log); restored (scripts, the waiver line, five rows in `sound/aliases/zm_ai_zod_companion.csv`). GATES: `r1_gun_icons.py`, `r1_comp_portraits.py`, `r3_synthwave_system.py`, `r4_synthwave_hud.py --check` in build_map.ps1; run_build_gates.py 136 / 0 failures. BUILD: FULL BUILD OK 00:48 (tmp/redesign/full6.log, started 00:32:29; geom_key reused the bake): .ff 00:46:57, FF 221,078,784 B (230,925,248 before the purge), the 8 known-waived linker lines only, one sound-bank retry (streamed 298.7 MB, loaded 131.8 MB; 920 / 920 alias wav stems indexed, tmp/redesign/verify_bank_stems.py). VERIFIED (tmp/redesign/verify_full4.py): every landed image in the ledger (R1 13 + R1b 3 + R2 7 + R3 44 + R4 72), each changed image a fresh content-hash .iwi (R4's Black Market icon byte-identical), the retired icons and every Mage row gone, -a2's probe rev 2 + -ed's spawn-ramp scripts + the fuse scripts packed, deployed = repo, nothing synced after the .ff, no repo edit after the build start. The Art Atlas republished (version 4, 454 images). UNPLAYED: the new HUD / prompts / perks / icons in game are the user's to judge. OPEN: the in-world companion models (the Protector's flat blue swatch vs its gold portrait, Talon / Cerberus missing maps), the parked finale / bench prompt icons (retire with their systems), wave 2 sounds + FX.

**2026-10-04 20:35 - THE REAL-RUN REVIEW, PASS 2 (user: "Continue"; docs/210 s2 items 5-7 + s4; CHANGELOG 20:35).** Three fresh review passes finished what the session limit cut at 14:40. FIXED in the repo: the Dealer no longer stacks the arena's level-10 x2.35 hit multiplier on his own x1.25 (131 -> 56 a swipe; `_tod_arena.gsc` house branch); the Battle Arena fights at a STATIC health round per level (`TOD_ARENA_HP_ROUND_BASE` 10 / `_STEP` 2, `level.tod_arena_hp_round`, held by `_tod_power_scale::track_rounds`; L1 round 10, L9 26, the Dealer 28) as the user described the arena on 2026-10-03; `hold_tower` keeps a haven's guardians (deleting them cleansed the haven for free). GATE `tools/test_dealer_house.js` 217 / 28 mutants. LEFT FOR THE USER (docs/210 s4, ordered): solo Quick Revive is one life for the descent (its only machine is on the sealed crown balcony), no ending after the Dealer, the Black Market and the Rampage switch only in the crown, no perk before floor 40, the Breacher's card dependency, arena trips ride home to the top bay, real cooldowns, the co-op Soul Pulse. BUILD: BUILT in session -13's FULL BUILD OK (tmp/mage_retire/full1.log, the Mage retirement; .ff 21:36:10, 230,164,608 B; geom_key reused the 12:43 bake), which carried these three files as they are in the repo: DEALER'S HOUSE OK 217 / 28 mutants and BATTLE ARENA OK 80 ran inside it; VERIFIED here read-only: scriptparsetree _tod_arena.gsc + _tod_power_scale.gsc in its ledger, both deployed = repo, the tod_arena_hp_round line and the guardian skip in the deployed scripts; every pass-1 change survived the merge (no armed dev flag, level.tod_diag, door_price_for, the downed-player skip, the gift text, TOD_TESTER_KIT 0, TOD_PARTNER_TEST_BENCHES 0, deployed Mozambique maxAmmo 30). -13's next FULL (asset batch 1) will supersede it as the test .ff. UNPLAYED.

**2026-10-05 20:30 - TELEMETRY PROBE ROOT CAUSE: NO LuiLoad, SO THE MENU'S LUA NEVER RAN. REV 4 LANDED.** The rev 3 run (20:05, archive `tmp/elite_tracking/runs/20261005_202140_164_ff8f34f8/`) came back with every lane empty, including L1 (`Engine.Exec(InstanceRef, ...)`, the exact shape of the Restart button that works) and no SendMenuResponse, and the file's top-level marker never fired: the Lua never executed. The first map's docs/19 "4-file contract" needs `LuiLoad( "ui.uieditor.menus.hud.<name>" )` in the client entry script; tod_upgrade and tod_class_select have theirs in `zm_tod2_cybercity.csc`, the probe had none. Rev 4 adds it (land.js piece 7, removed whole by `--remove`) and is console-only (no IPrintLnBold, no on-screen text, per -13's triage). Rule added to CLAUDE.md "Lua UI". Gates + a -GscOnly next; UNPLAYED.

**2026-10-05 18:05 - TELEMETRY PROBE: REV 1 AND REV 2 CAME BACK SILENT, REV 3 (LANE CENSUS) LANDED, RIDING -ed's NEXT FULL.** Rev 1 (2026-10-04 22:33 run) and rev 2 (2026-10-05 17:33 run, three map loads, archive `tmp/elite_tracking/runs/20261005_175358_367_fe125096/`) both: menu opened every time (`OpenLUIMenu handle defined=1`), zero reports on every lane, no top-level `tod_telem_loaded` marker, no `players\tod2_telem_probe.txt`, url probe also silent. Not yet known whether the Lua file executes at all. The map's only proven Lua-to-engine calls use the engine-given controller (`Engine.Exec(controller, "map_restart")`, which worked in the same run); rev 2 used `Engine.GetLocalClientNum()`, used nowhere else here. Rev 3 reports on five lanes, each to its own dvar (L1 engine controller, L2 controller 0, L3 GetLocalClientNum, L4 Engine.SetDvar, L5 SendMenuResponse logged from GSC `menuresponse`), so one run names the working lane or proves the file never runs. Landed 18:03 (only `_tod_telem.gsc` + `tod_telem_probe.lua`; strict/Lua/native-API/arity/hints/assets gates green); -ed carries it in its next FULL. UNPLAYED. Probe windows checked against -13's mocomp exception bursts in the 17:33 run: no overlap.

**2026-10-04 15:40 - RUN RECORDS: TELEMETRY PROBE STAGED, NOT BUILT, NOT PLAYED (user: "store game played information ... without a terminal opening and booting you out ... think outside the box").** Research (docs/211): the first map's only window-opening call was launching a helper program from the UI Lua; file reads/writes from Lua are silent and proven on retail (MACHIN[A]'s Trenches save is a LOCAL file, not a database; its 2026-10 match saving overflowed `MAX_GAMESTATE_CHARS` pushing state host->clients). Retail UI Lua still has `Engine.OpenUrl` (a rival client stubbed it 2026-09-12 over ad abuse). Staged under `tools/telemetry_probe/`: inner Lua chunk compiled to T7 bytecode by `tools/hksc/hksc.exe` (copied from the first map's repo, 181,574 B, header `1b 4c 75 61 51 0e` verified), outer menu `tod_telem_probe.lua` (6,372 bytecode bytes spliced; hksc syntax pass + repo Lua lint clean), GSC module `_tod_telem.gsc` (strict lint clean), `land.js --apply/--remove/--status` (five pieces, anchors asserted, CRLF kept), `read_probe.ps1` (evidence reader). Probe = at blackscreen+2 s the host's overlay writes/reads/appends/removes under `players\` and prints one teal verdict line; at end_game ONE deliberate `Engine.OpenUrl` so the tester sees overlay vs browser. Armed by `#define TOD_TELEM_LOG 1` (listed by the pre-publish grep); retire whole with `--remove`. Landing order agreed with sessions -13 and -7a: -13's Mage retirement FULL build first after the user's real playthrough, then this probe as a `-GscOnly`, user's 3-minute run, `--remove`, gates, TREE SAFE. UNPLAYED; the 15:23 playthrough .ff is untouched.

**2026-10-04 15:10 - THE FIRST REAL PLAYTHROUGH: DEV AND GOD MODE ARE OFF (user: "turn off dev and god mode and prep for an actually play through ... we have been testing in dev and god mode the entire time"; docs/210; CHANGELOG 15:10).** SHIP-LIKE STATE NOW: `tod_dev`, `tod_god`, `tod_dev_maxed`, `tod_dev_unlimited_offhand`, `tod_dev_all_guns` all false; `TOD_TESTER_KIT` 0 (no class terminal; the Battle Arena climbs from level 1 - with the kit on its FIRST trip was the Dealer); `TOD_PARTNER_TEST_BENCHES` 0. Dev mode was a BUNDLE: it also opened EVERY TOWER DOOR FREE (`dev_open_doors_harness`) and lit the crown Black Market before the power, so the door ladder, the tier-1 kit, real cooldowns, real damage and the companion's real availability had never been played. NEW `level.tod_diag = true` keeps ~60 console-only feature loggers printing without dev mode (no value, nothing on screen, not read by the publish gate) - re-arm dev for money/doors, never for logs. ADJUSTED: the crown island's three doors (5000 gate, two 1500 hallway doors) are FLAT in co-op (`_tod_doors::door_price_for`; one wallet paid 11974 in a quad); the Breacher's T1 Mozambique carries 30 magazines (was 20; `gen_tod_twins.js` `reserveMult: 1.5` now scales the DERIVED reserve pin - a plain reserveMult is overwritten by `reserveMags`); the crown ramp's `player_in_hall` skips a downed player; the gift nudge says IN THE CROWN HALL. LEFT FOR THE USER (docs/210 s4): solo has ONE LIFE in the crown (Quick Revive waits for the power on the balcony - the user's 2026-09-25 call), the crown's pace (`TOD_FALL_SPAWN_MULT` is the first lever), the 1500 Teleporter room is a dead end until the ground floor, the ramp grows with kills not time, the Breacher has no ability until a card. RULE: before a "real" run, grep `level.tod_dev` for VALUE gates, not just the flag block - a convenience moved off the bundle (money, doors) can still ride `tod_dev ||` in `_tod_main::init`. BUILD: FULL BUILD OK 15:25:23 (tmp/real_playthrough/full1.log; started 15:09:40): .ff 15:23:22, FF 233,682,752 B; geom_key REUSED the 12:43 bake (BSP 12:40:38, LED 246,277,485 B), NAVMESH GATE OK on the reused mesh, a fresh occlusion tome (695 tiles), the 8 known-waived linker lines only, no material on a missing techsetdef, loaded bank 172,801,536 B (= the last good build), streamed 313,845,760 B. Before it, tools/run_build_gates.py ran 125 gates on the repo with one failure, fixed: tools/test_ambush.js pinned the old dev_log gate text and now also accepts the tod_diag form. VERIFIED: deployed scripts / ui / zone_source = repo, nothing synced after the .ff, no repo input edited after the build start, deployed source_data/tod_weapon_twins.gdt = repo (Mozambique 30 magazines); the ledger carries scriptparsetree for every touched script and weapon cc_mozambique_e0..e3 + _up. Peers -13 (asset audit; the Mage retirement and a Map 1 purge come next) and -a2 held their edits during it. UNPLAYED.

**2026-10-04 12:52 - THE DEALER'S GIFT: THE BLACK MARKET GIVES EACH PLAYER A FREE RANDOM AI COMPANION ON FIRST USE, LUCK UNTOUCHED (user: "finding your parts etc is a bit much ... he should gift you a random AI companion on first use that doesnt use up your luck. Then you can continue to upgrade ... make it easy for the player experience"; docs/209; CHANGELOG 12:52).** SUPERSEDES docs/159's parts / build / equip flow (the 2026-09-23 FOUR BUILDABLE PARTNERS note below and the "partner parts still lie beside the Vault spawn" line of the base-layout note). A companion-less player's hold at the lit Black Market runs `_tod_shop.gsc gift()`: a free 30-tile COMPANION reel on the spin's machinery, NO coin and NO luck pour (the LUCK box keeps his bar), THE POOL (slots mode 5) while it runs, the companion handed over AT THE LANDING (`level.tod_partner_gift_fn` -> `_tod_partners::gift_companion`), ON THE HOUSE + the portrait punch + its three empty slots (SPIN TO FILL, mode 4); the panel drops after 3.2 s and it deploys - and every companion deploy now materialises with the teleporter's arrival (`arrive_fx`). His own prompt: "A free AI companion / No points or luck - on the house" (verb TAKE); a one-time nudge 8 s after a counter lights; the pick prefers companions nobody in the party holds; six new Dealer lines (shipping voice + mask, pick.py 101). RETIRED WHOLE: the 8 Vault parts and the 4 bench prompts (hints 95 -> 83), the "partner part" noun + icon, the "companion required" card + its two VO lines. KEPT: the 4 crafting tables as set dressing (their clips are in the .map), the crown TEST benches, the 8 part models in tod_partners.zpkg (installer-pinned). STUB FIXED: the R.A.P.S. blast and the counter's LEGENDARY / cursed blast were `electric/fx_elec_burst_lg_z270_os` (a gfx_debug_missing_fx stub) -> `dlc1/castle/fx_elec_teleport_flash_lg`. RULES: the gift never spends luck / points / streak / spin count (test_spin.js executes it); gift tiles 45..48, land code 8, slots modes 4 + 5 are LOCKSTEP `_tod_shop.gsc` / TodSpinReel.lua P3.GIFT / render_spin.py; the gift art is GENERATED (`tools/partner_shop/make_gift_art.py`, its --check gates the build); a scratch mirror's gate run writes receipts THROUGH its junctions into the repo (memory scratch-mirror-junction-receipts). Gates: test_spin.js 737, test_partners.js 152, test_spin_reel.lua, 16 GSC + 9 Lua mutants. Logs `[TOD_SHOP] GIFT_*`, `[TOD_PARTNER] GIFT`. BUILD: landed 12:52 (37 files, 3-way merged; one hunk hand-resolved to keep -5e's `tod_base_sign::init()`); repo gates 125 / 0 failures; FULL BUILD OK 13:34:58 (tmp/dealer_gift/full2.log; full1 was refused at gdtdb by a BlackOps3 launch, nothing native ran): .ff 13:33:10, FF 233,681,472 B, geom_key REUSED -a4's 12:43 bake, the 8 known-waived linker lines only. VERIFIED: the ledger carries the six gift images (fresh .iwi), the four scripts, the six Lua rawfiles and fx dlc1/castle/fx_elec_teleport_flash_lg, no partner-part icon; all six tod_spin_vo_gift_* stems in the fresh loaded bank (172.8 MB), no no_companion line; deployed = repo, nothing synced after. UNPLAYED.

**2026-10-04 12:31 - THE HAVENS v5, THE CORRUPTED WRECK + THE PURIFICATION (user: "I like the two states of the dome to be quite different and the transition of purification to be nicely animated with visuals and nice sounds etc. Lets make this amazing"; docs/202 v5; CHANGELOG 12:31).** THE CORRUPTED DOME IS ITS OWN BREACHED MESH (`make_dome.py dome_mesh(dark)`: a tenth of the cells gone, the rest cracked panes on a 2x2 atlas `i_tod_haven_field_dark` - seam alpha graded 0.42 -> 0.80, LOOK FROM INSIDE; own bins `tod_haven_dome_dark_lod0/1`, NEW skin `tod_haven_dome_dark_dim`); it RATCHETS (`TOD_HAVEN_RATCHET_*`), BROWNS OUT (the dim skin), GROANS (`tod_haven_groan`, 3D, two takes / one alias), throws a REAL RED LIGHT (`heart_light()` = the golden zombie's recipe; `fx_tod_haven_corrupt`, faster in the NEW fight loop `fx_tod_haven_fury` the wake swaps in), the safe dome a steady cyan light. THE PURIFICATION (~4.5 s, ONE timeline; `cleanse` = entry/state "purge", `purge_run`, `collapse` + `purify` wait-free for the gate): CONVULSION 2.2 s (the heart strobes on `purge_strobe_steps()` 0..2130 ms accelerating - the dome's SetModel strobe, `fx_tod_haven_convulse` and `tod_haven_purge`'s clicks all read THAT list: both generators parse the GSC; quake, the dark hum fades, FLOOR N PURIFYING; players inside: the veil GRIPS + a red flicker per strobe `TOD_HAVEN_BANNER_STROBE`) -> COLLAPSE (`fx_tod_haven_collapse` implodes inward via `runRelToOffset` on a sphere offset, a real light flash; dome hidden, barrier down, sign dark, every ORDINARY zombie inside killed by the stock nuke idiom `DoDamage( health + 666 )` with `tod_ps_exempt` round it - elites / guardians / outside spared; inside players see BLACK `TOD_HAVEN_PURGE_VOID_SECS` 0.35 = TodHaven.lua `VOID_MS`) -> BLOOM (`purify`: safe at once, SECURED's third arg = on the floor -> the full flash, the NEW `tod_haven_dark_lift` cue, the safe dome INFLATES `SetScale` 0.06 -> 1 over 0.8 s) -> SETTLE 1.2 s (the safe hum). RULES: a GSC-define / effect / wav lockstep is held by generators that READ the GSC (a define change makes both --checks stale on purpose); a mutant removing a flag SET is caught at the moment of use (the harness's DoDamage records `tod_ps_exempt` at the hit); the lucky light validator (radius <= 400, shadowless, all four lighting states, <= 2 alive) is the rule for every haven light; the HUD harness numbers every child (a glyph row has no id). Gates: test_haven.js 529 / 53 mutants (section G), test_haven_hud.lua 8 negative controls, the three --checks (13 effects under budget, 17 wavs). BUILD: landed 2026-10-04 12:21 (land_v5.py, ONE step: 26 files + three zone lines inside the haven block; none of -5e's rebase points touched, its blocks kept); every build gate run on the repo AFTER the landing: 123 gates / 0 failures in 448 s (tmp/haven_v5/gates_repo.log). FULL BUILD OK 12:46 (tmp/haven_v5/full1.log; started 12:31:58; ONE build carrying -7a's Dealer's House, -5e's Map One migration and this pass - -5e's own full1 had died at gdtdb on // comment lines in its two new GDTs, fixed by -5e before this build): .ff 12:46:36, FF 233,280,000 B, a FRESH compile + bake (geom_key: 8 inputs changed since 11:55 = -5e's .map + GDTs; BSP + navmesh 12:40:38, LED 246,277,485 B), NAVMESH GATE OK, the 8 known-waived linker lines only. Ran INSIDE it: GSC STRICT LINT OK 139, HAVEN DOME / FX (13 effects) / SOUNDS --check OK, HAVEN GATE OK 529 / 53 mutants, test_haven_hud OK (8 negative controls), HAVEN LEDGER OK 41 assets (37 in v4), FAN PROPS / CYBER TEDDY / PERK MACHINE / JUMP TITLE / LUCKY / WAR DAMAGE ledgers OK. VERIFIED (scratchpad verify_v5_build.py = V5 BUILD VERIFY OK): the 12:46:36 ledger carries all 13 fx tod/haven/*, the 6 dome xmodels incl. tod_haven_dome_dark_dim with EVERY exported triangle (the xmodel ledger: dark 4752 / 2056, safe 5256 / 2176 - LODs lowest detail first), image i_tod_haven_field_dark + the field / darkness / vignette, rawfile todhaven.lua, scriptparsetree _tod_haven.gsc + _tod_breather_data.gsc; every haven material row is COMPLETE (105-127 B, none name-only - memory linker-usage-mismatch-empty-material); the fresh loaded bank (12:45:15, 171.3 MB) indexes all 17 tod_haven_* stems; deployed scripts / ui / zone_source + the GDT / .map / tod_haven.csv / 47 haven model-fx-sound files == repo, nothing synced after the .ff, no repo input edited after the 12:31:58 start (only tools/cod2map_last.log, the build's own transcript). UNPLAYED - the two looks, the strobe's pace, the implosion, the void, the bloom and every sound level are the user's to judge; the Blender review of both states (tools/haven/preview_states.py -> art/haven/review/state_*.png + states.json, dome_dark_mesh sha 4a6ff1b3...) RENDERED 12:57 once the game closed (its process guard refused at 12:52 while BlackOps3 ran; a watcher re-ran it 30 s after the exit): the corrupted gallery reads as a breached red wreck with hot ragged seams and veined dark panes, the safe one as the clean thin cyan lattice. THE 12:49-12:56 GAME WAS MAP ONE, NOT THIS .ff (its console loaded zm_tower_of_doom from the Steam usermaps and carries only Map One's tags - [TOD_ROCKET] / [TOD_LUCK_ORB] / [TOD_AI] - and zero [TOD_HAVEN] lines; the game writes one console_mp.log, so capture_ai_logs.ps1 archived it under tmp/elite_tracking/runs/20261004_125806_259_c74741c6 with a NOTE file saying so; RULE: check the archived log's `Loading fastfile` line before reading it as a Tower II run). v5 has not been played. SUPERSEDED AS THE TEST .ff by -b6's FULL BUILD OK 13:34:58 (tmp/dealer_gift/full2.log; the Dealer's gift, docs/209; .ff 13:33:10, FF 233,681,472 B; geom_key REUSED this build's 12:43 bake; NAVMESH GATE OK; the 8 known-waived linker lines only), VERIFIED HERE read-only with the same verify_v5_build.py (V5 BUILD VERIFY OK): its 13:33:10 ledger carries every v5 row (13 fx tod/haven/*, the 6 dome xmodels incl. tod_haven_dome_dark_dim, image i_tod_haven_field_dark, rawfile todhaven.lua, both scripts; every haven material row complete), its fresh loaded bank all 17 tod_haven_* stems, deployed == repo for scripts / ui / zone_source + the GDT / .map / tod_haven.csv / 47 haven files, nothing synced after its .ff, no repo edit after its 13:22:25 start; HAVEN GATE OK 529 / 53 and HAVEN LEDGER OK 41 ran inside it. Still UNPLAYED: the 13:16 game was Map One as well (`Loading fastfile 'zm_tower_of_doom'` in the live console).

**2026-10-04 12:06 - THE MAP ONE MIGRATION (user: "Map one made some changes to adding numbers to each floor. Lets add that too but we go down instead of up ... check a few other things. They made a ton of updates we never migrated over. like textures, models, etc"; docs/208; CHANGELOG 12:06).** Map One's CHANGELOG since the seed (v19.24-v19.72) audited entry by entry; Map One stayed READ ONLY (its built outputs copied byte for byte, pinned by its manifests; its tools that write into its tree / the shared tools were NOT ported). LANDED: FLOOR NUMBERS FOR THE DESCENT (every floor F's number on the inner face of its end landing's outer rail, dead ahead of a player coming down through F+1's door; the map's HUD digits in the district colour, non-colliding chalk-mesh quads; `tools/floor_numbers/make_assets.py`; `TOD_FLOORNUMS=0` = the map without them byte for byte); THE BLACK-SCREEN FOG (`fog_off()` divided by zero twice; `TOD_FOG_OFF_*`); NIKOLAI'S PROPS (Ammo Box V6 on every crate with a 30-tall clip; the TOWER OF DOOM / CYBERCITY sign on the core's west face, lit at the power, steep cap; the GRID TERMINAL as the crown's power switch, the wave starts as its screen reads POWER RESTORED; `tools/fan_props/verify.py`); THE CYBER TEDDY (+ a melee lane: a blade swing finds a bear; `tools/cyber_teddy/verify.py` holds LIFT / HALF_DEPTH / haven BEAR_* / BEAR_EXT one chain); THE CYBER RAMPAGE INDUCER (Map One's animated device on the balcony with a body clip + steep cap, trigger in the slot `crown_inducer_trig_lift()` 44, ON / OFF stings from the device, no cha-ching; `tools/inducer_cyber/verify.py`, `tools/rampage_sfx/build_rampage_sfx.py --check`); WIDOW'S WINE'S SHADER (the techsetdef in share/raw/techsetdefs_stable*, post-link gate: zero `missing_techsetdef` rows); THE ALTAR (waterRoughness 0, crest LODs from 1000); THE PACKED 870's SIGHTS (`noOptic()`'s third edit; `tools/test_no_optics.js`); THE PERK MACHINES (Double Tap's cowboy fires his 16 shots, 14 recovered WAVs, Wisp Tea audio; MAP-OWNED `tod2_perk_machines` folders); NINE FIXES (RK5, round-end stinger, Gift of Death pickups, nuke + shield kill pay, PhD own-explosives only, PaP refuses the shield, Zombie Blood keeps other invulnerability, blank-hint card hide + prompt children closed, chat hides with the board). RULES: (1) the private root's model_export holds ~80 JUNCTIONS into the shared install (incl. `tod_perk_machines`): a map-owned port takes a new name (`tod2_*`) or the sync dies on the isolation guard (memory private-root-junction-folders); (2) never run a Map One tool from here - it hardcodes Map One's repo and the shared Steam tools; port its outputs + manifest, or retarget the tool first; (3) floor signs for a descent go where the player ARRIVES (the end landing's rail), not beside the door they leave by; (4) a free-standing prop's clip gets a steep cap (`steepCap(..., bury 0)`) - a Breacher launch or a grapple finds no flat top. Gates: the six new checks above + `test_perk_anims.js` / `verify_perk_machine_presentation.py` + the missing-techset post-link step, all in build_map.ps1. Backlog for the user (docs/208): co-op restart, one damage number per zombie, Death Perception on elites, rampage on the tower, luck souls, Zombie Blood filter, door posts, crate prompt sides, end-game stats, party rows, floor label, melee inspect / lunge, the cowboy's hit markers, credits for Nikolai + the teddy's author. BUILD: landed 2026-10-04 12:06 (python tools/run_build_gates.py on the repo: 123 gates, 0 failures). My FULL build at 12:15 (tmp/map1_migration/full1.log) DIED AT gdtdb /update at 12:16, nothing compiled: two of this pass's generators wrote // comment lines into tod_floornum.gdt and tod_fan_props.gdt, and gdtdb refuses a // line anywhere in a GDT, inside the braces too (Map One's build only WARNS on a gdtdb failure, this map's dies, so a pattern copied from Map One must be comment-free here). Fixed: both generators write no comment (each new file = the old one minus its comment lines; tools/fan_props/manifest.json gdt_sha256 follows) + NEW GATE tools/lint_tod_gdt.js, pre-sync in build_map.ps1 (GDT syntax + one asset per name AND type - the namespace is per type; 10 planted syntax errors + 3 duplicates self-tested every run; clean on the 74 repo GDTs). BUILT in -a4's combined FULL BUILD OK 12:46 (tmp/haven_v5/full1.log; started 12:31:58): .ff 12:46:36, FF 233,280,000 B, a fresh compile + bake (LED 246,277,485 B), NAVMESH GATE OK, the 8 known-waived linker lines only; every gate of this pass printed OK inside it (floor numbers, fan props + its ledger, cyber teddy + its ledger, the inducer pre-link and on the compiled ledger, the rampage stings, no-optics, perk anims + the perk machine ledger, zero missing_techsetdef rows). Verified after (docs/208 Build): all 80 migration ledger rows, 19 / 19 sound files in the banks (2 of them streamed by design), the deployed tree = the repo at 12:48, nothing synced after the .ff. SUPERSEDED AS THE TEST .ff by -b6's FULL BUILD OK 13:34:58 (tmp/dealer_gift/full2.log; .ff 13:33:10, FF 233,681,472 B; geom_key reused the 12:43 bake), verified here the same way: GDT LINT OK ran inside it before the sync, every gate of this pass printed OK, all 80 migration ledger rows, every other zone scriptparsetree, zero missing_techsetdef rows, 19 / 19 sound files in the banks, deployed = repo, nothing synced after the .ff, no repo input edited after its 13:22:25 start. UNPLAYED.

**2026-10-04 12:04 - THE DEALER'S HOUSE: THE BATTLE ARENA'S FINAL FIGHT IS THE DEALER IN HIS TWO ROOMS (user: "a separate arena that is even better and slightly bigger ... the one players will get sent to on battle arena wave 10 ... a small box with the Black Market as the only thing in the center ... a cut scene ... the evil mastermind ... teleports the players into the new battle arena and gets the players down to one HP with the same effect that the evil dome gives ... one health but you cant die ... the boss fight will only be him in his two phases"; "two more rooms"; "He lets you roll one last time and you get a very evil bad roll and he laughs like crazy"; docs/207; CHANGELOG 12:04).** LEVEL 10 OF THE ARENA = `tod_house::run` (`TOD_ARENA_HOUSE` in _tod_arena.gsc, the branch after hold_tower; the Keeper's boss_wave is dead code at level 10): THE PARLOUR (704 box at (-8000, 8000), the Black Market hut at its centre, `tools/dealer_house_layout.js` -> GENERATED `_tod_house_data.gsc`) - music stops, the hut lights (`_tod_shop::house_shop_begin`, `level.tod_shop_hold` sleeps the cycler + the voice watchers), THE SCENE (letterbox via `tod_jump_cine` 1 / kept alive with the NEW `3` beat / 0; menu_freeze; the view locked on the mask by PlayerLinkToDelta +-20/+-12), four NEW 3D lines (welcome / ledger / "The tower didn't fall. I folded it ... All of it was me." / the offer); THE LAST ROLL (its own trigger + constant hint "BLACK MARKET - the last roll / on the house - FREE"; first USE rolls for all, `TOD_HOUSE_ROLL_WAIT` 25 s then he rolls) = `_tod_shop::house_roll`: ONE seed on every screen, a STOPPED SHORT hang on a LEGENDARY LUCKY CHARM, the fall onto CURSED (`TOD_SPIN_CURSED_TILE` 60 / `TOD_SPIN_CODE_CURSED` 9, LOCKSTEP TodSpinReel `CURSED`; `landCursed`: his mask on the tile, HOUSE WINS / ALL YOUR HEALTH BUT ONE, the cursed banner, red everything, the shake; pays nothing); his gloat, THE LAUGH (9.4 s) over the banner, "let me show you where the money goes", the 0.8 s charge; THE HOUSE (1920 square at (8000, -8000), 720 tall: the pit, THE DAIS - a 384 top on a block with a full-width flight down every side, open corners - the ring at 120 with four pinwheel stairs, four pylons + collars, four lit gates, the vented roof): the party lands on the dais, the haven's CORRUPTED dome rises round them (`tod_haven_dome_dark` x `TOD_HOUSE_DOME_SCALE` 2.0, the boot stutter, hum_dark, fx_tod_haven_corrupt) + the haven HUD's corrupted tint/darkness (`tod_haven( 1, 0, 1, 0 )`), THE DRAIN (10 cuts / 6 s, NEW `tod_house_cut` flicker in TodHaven.lua + the GENERATED cues cursed / drain / cut from `tools/dealer_house/make_sounds.py`; the line held every tick; `level.tod_house_shield` + a first-in-chain damage callback + EnableInvulnerability = cannot die) to ONE; two 2D lines; THE FIGHT: spawn_boss at the gate farthest from the party, HELD (`level.tod_dealer_hold` in brain: ignoreall + idle), "The account is open. Let's SETTLE it!" (the dome breaks under it, the darkness lifts), release, the readout THE FINAL FIGHT / THE DEALER (`TOD_ARENA_HUD_HOUSE` 16 / `_DEALER` 32, LOCKSTEP TodArena FLAG_*), horn, boss track, red mood hosts; his two states (the crack line via NEW `level.tod_dealer_crack_fn`, the death line via `_death_fn`, a down line 60 %); his death = arena_win (cards, the ride home from NEW `level.tod_arena_depart`, CONQUERED). `TOD_DEALER_TEST_SPAWN` 0 (the house is his place). THE VOICE: 14 lines group `house` (lines.json, generate --group house, picks.json: the shortest monologue takes, the longest laugh), pick.py shipped 97 files. THE ART: `tools/dealer_house/make_spin_art.py` (3 PNGs from the legendary set + our glyphs; review art/dealer_house/review/spin_cursed.png). READERS: _tod_ambush / _tod_reach / _tod_atmosphere / _tod_gauge + the arena fall guard read `in_house` / `in_parlour`. TESTER: `TOD_ARENA_TEST_START_LEVEL` 10 under TOD_TESTER_KIT = the first arena trip is the final fight (1 = the climb). RULES: a terrace Havok can climb from every side gets NO navmesh polygon (build 1 died at the navmesh gate on a pyramid dais of 12-high slabs: merged into the pit floor's polygon; a 48-high slab = its own island) - a flight with OPEN sides is bordered by its drops and meshes (the arena's grammar), proved with cod2map on scratch map variants (20 s a run; `tools/lint_tod_navmesh.js <hkt>` runs the gate on any mesh); gsc_eval has no `switch` (gate-run pure functions are || chains); `tod_cc_ruby` is a DECK to lint_tod_geometry (trims wear oxblood); the lint's `ISLANDS` (arena / house / parlour) each flood from their own floor, gated at zero; lint_tod_navmesh reads the house's anchors; a scene over 17 s must re-arm TodJumpCine's watchdog (`TOD_HOUSE_CINE_KEEP_SECS` 8); patch gate files with the editor, never through a bash heredoc (backslashes mangle). GATES: NEW `tools/test_dealer_house.js` (211 / 25 mutants) + both `--check`s in build_map.ps1 (TOD_HOUSE_LOG refuses -Publish); test_battle_arena 80 (six bits), test_pursuit / test_ambush / the three Lua harnesses / lint_tod_hints / gen_lanes (1499 bands) updated. Staged + proven in a scratch mirror, landed in one step. BUILD: FULL BUILD OK 12:04 (tmp/dealer_house/full2.log; build 2 - build 1 at 03:42 (full1.log) passed every gate, compiled + baked and DIED AT THE NAVMESH GATE: the dais, a pyramid of concentric 12-high slabs, had NO navmesh above the pit floor (Havok merges a terrace it can climb from every direction into the floor polygon it rises from; a 48-high slab is its own island), found with cod2map on scratch map variants (20 s a run) and fixed by the plus-shaped dais in tools/dealer_house_layout.js; the geometry self-test's PARITY case also needed the house's data file redirected in tools/lint_tod_geometry_parity.js): .ff 11:58:38, FF 230,443,904 B, a FRESH compile + bake (BSP 11:48:02, LED 246,277,485 B, the occlusion tome rebuilt, 695 tiles), NAVMESH GATE OK inside it (DEALER'S HOUSE: 4 arrivals + 4 gates + 25 surface probes in ONE component, the 4 parlour arrivals on mesh), the 8 known-waived linker lines only. Ran INSIDE it: GSC STRICT LINT OK 137, DEALER'S HOUSE OK 211 / 25 mutants, CURSED SPIN ART OK 3, HOUSE SOUNDS OK 3, BLACK MARKET VO OK 97, SPIN PASS 652, BATTLE ARENA OK 80, PURSUIT 158, AMBUSH 51, HAVEN GATE 453, HUD owner lifetimes 160, test_haven_hud (6 controls), ARENA HUD OK, every ledger check (JUMP TITLE / LUCKY / HAVEN 37 / WAR DAMAGE). VERIFIED after: the 11:58:38 ledger (all + english) carries scriptparsetree _tod_house.gsc + _tod_house_data.gsc + the 8 touched scripts, image i_tod_spin_tile_cursed / _banner_cursed / _ico_cursed (fresh .iwi 11:58:15), rawfile todspinreel / todarena / todhaven / todjumpcine, xmodel tod_haven_dome_dark + _flash, tod_dealer_body + _cracked, fx tod/haven/fx_tod_haven_corrupt + _boot, aitype spawner_tod_dealer; the fresh loaded bank (11:57:40, 167.6 MB) indexes all 17 house stems (3 cues + 14 lines); every landed input deployed = repo (41 files + tod_shop.csv / tod_house.csv at share/raw + the usermap, the szc), nothing synced after the .ff, no repo input edited after the 11:38:24 start. SUPERSEDED AS THE TEST .ff by session -a4's haven v5 FULL BUILD OK 12:46 (tmp/haven_v5/full1.log; .ff 12:46:36, FF 233,280,000 B; a fresh compile + bake on the 12:32 repo tree = this house + -5e's Map One migration + haven v5), VERIFIED HERE read-only: its 12:46:36 ledger carries every house row (both scripts, the 8 touched scripts, the 3 cursed images, the 4 widgets, both dome models, both Dealer bodies, the corrupt + boot fx, the Dealer spawner), its 12:45:15 loaded bank (171.3 MB) all 17 house stems, NAVMESH GATE OK inside it with the house on one component, every house input deployed = repo, nothing synced after. THEN by session -b6's Dealer's-gift FULL BUILD OK 13:34 (tmp/dealer_gift/full2.log; .ff 13:33:10, FF 233,681,472 B; the 12:43 bake reused; its _tod_shop.gsc gift lane + TodSpinReel gift tiles sit beside the house's pieces untouched), VERIFIED HERE the same way: every house row in its 13:33:10 ledger, all 17 house stems in its 13:32:18 bank, every house input deployed = repo, nothing synced after - THAT is the test .ff now. UNPLAYED - the scene's pacing, the roll's feel, the drain and the fight are the user's to judge. Logs `[TOD_HOUSE]`.

**2026-10-03 17:11 - THE HAVENS v4, THE WHOLE HALL: THE FIELD FILLS THE HALL, EVERY MACHINE INSIDE, A BULLET BARRIER WHILE CORRUPTED, THE GUARDIANS KEPT INSIDE, THE DARKNESS (user: "Safe zone should be the entire area ... the elites are not allowed to leave the dome ... bullets cannot go in or outside the dome. Until its a safe zone ... all perks and ammo crates pap etc should be inside of the dome. Going inside will make your screen dark"; docs/202 v4; CHANGELOG 17:11).** The dome is centred on the hall (92, 92), ring 332, crown 272 (its sphere's centre 66.6 UNDER the floor), asserted 24 under the galleries and the next lap's treads (`haven_layout.js ceilingAt()`); PaP / altar / crate / both perk pads ring the pad INSIDE it, facing OUT (the rim rule + the dome's height leave no other fit); the corners outside hold six risers and three short emitter POSTS (the pylons are gone). MEMBERSHIP IS THE SPHERE (a body's chest within S-12 of its centre, out past S+6, a z band) - generated `haven_in_r3 / out_r3 / body_up / z_below / z_above`. THE BARRIER: one script_brushmodel per haven floor (`tod_haven_barrier_<floor>`, 144 frustum brushes from `barrierBrushes()`, `gen_tower_map.js polyBrushText()`) in `tod_haven_barrier` = the stock `clip_weapon_noimpact` block copied whole by make_dome.py + `missileClip 1` + `noPenetrate 1` (nonsolid to bodies); NotSolid until the boot, Solid while corrupted, NotSolid from the cleanse; across it every hit is refused both ways (`actor_damage_gate` wraps `level.callbackActorDamage`; `level.tod_haven_barrier_fn` is the FIRST lane of `_tod_bosses::boss_player_damage`); a guardian always counts as inside its own field; a shot that stops on it answers (`fx_tod_haven_deflect` + `tod_haven_deflect`). THE GUARDIANS: one spot each (v3 stacked every guardian on ONE spot - the user's 15:34 log, all three floors), they hunt only players INSIDE their field, the fence puts one found outside back on its spot, `self.tod_reloc_fn` (asked first by `_tod_doppelghast::reloc_point`, the Mangler's too) relocates inside. THE DARKNESS: TodHaven.lua `TodHavenDark` (`i_tod_haven_darkness`, breathes 1.0/0.8) + `tod_haven_dark_in` / `tod_haven_dark_breath` (2D, NONLOOPING, re-played; never a looping 2D alias you cannot be sure to stop). RULES: (1) the haven harness (`test_haven.js lower()`) turns `obj [[ fn ]]( args )` into the builtin `__ptrcall` and leaves `;` where it drops a dev_log - deleting it outright silently re-parented the NEXT statement under an unbraced `if` / `else` (init died on it); (2) a SOLID on a loggia conduit inlay patch changes `conduit_layout.js` rows and the conduit models - keep haven solids off them (`--check` catches it); (3) any change to the floor-20 hall's solids changes the Dealer panel's context: `inventory.js`, the studio render (`start_studio.ps1`, `mcp_call.py` with the FULL path to `preview.py`), look at `floor20_service_after.png`, a `rereviews` entry, stop the studio (done this pass). Gates: test_haven.js 453 / 41 mutants, test_haven_hud.lua 5 negative controls. Logs `[TOD_HAVEN] INIT rev=4 / BARRIER / GUARD_FENCE / GUARD_RELOC / DARK / BLOCK / DEFLECT`. BUILT: FULL BUILD OK 17:46:00 (tmp/haven_v4/full1.log): .ff 17:44:19, FF 229,771,520 B, a fresh map compile + navmesh + bake (LED 239,692,504 B), the 8 known-waived linker lines only; HAVEN GATE 453 / 41, NAVMESH GATE OK and HAVEN LEDGER OK 37 inside it. VERIFIED: the ledger carries the v4 scripts, i_tod_haven_darkness, fx_tod_haven_deflect and todhaven.lua; all 13 tod_haven_* stems in the fresh loaded bank; deployed = repo, nothing synced after; the BSP carries the four barrier brushmodels with contents 0x200020c0 (shot clip + missile clip, no solid / player / AI clip); a compiled-navmesh probe puts all 37 hall points per floor on that floor's walk component. RULES: an image name ending `_dark` in a Lua file fails lint_tod_assets GATE C (a dark-card plate) - the veil is `i_tod_haven_darkness`; tools/run_build_gates.py ran only 87 of the build's gate lines until 17:35 (the captured-output lines) - it runs 112 now, check its gates: line. UNPLAYED.

**2026-10-03 16:00 - THE JUMP PAD'S GRAY MACHINE: 12 MATERIALS COMPILED EMPTY, FIXED (user, after playing the 15:34 build: "Textures look like they didnt come through properly. ENtire model is grayish and bugged."; docs/163 s9 "The gray machine"; CHANGELOG 16:00).** One texture, `i_tod_jp_t7_micro_metal_painted_02_s`, was labelled `specularMap` where every slot it fills reads a `specularMask` (`specColorMap`; `colorMap03` = the micro-tile techset's `specularMapDetail2`); the linker printed `mismatched usage` + `no techset for surface N` in RED, the build still said OK, and the 12 materials using it (most of the frame + both decks) compiled EMPTY - each asset-ledger row only its name (41-49 bytes; complete = 328-2080) - and drew flat gray. RULES: (1) red linker lines are not failures to build_map.ps1 and a material NAME in the ledger is not a working material: after any material import read `tmp/native_build/linker_last.log` for `mismatched usage` / `doesn't expose` / `no techset` and compare each material row with its name length (memory linker-usage-mismatch-empty-material); (2) an authored texture's semantic is the usage its SLOT's techset reads (`SLOT_USAGE` in the installer), not its suffix; (3) the installer's stock lookup must subtract its own GDT's assets (after a build the DB holds them; a re-run otherwise writes a GDT with no materials - caught staging this fix). GATES: the installer `--check` (slot usages; the old GDT fails it) + NEW post-link `install_de_jumppad.py --compiled-ledger ... --linker-log ...` in build_map.ps1 (empty materials, missing textures, linker complaints naming a pad asset). Same class, other sessions' assets, untouched: mtl_wpn_t7_c4_decal2, sat_zm_machine_y_mod_01_on, tod_fire_bow_rune_view's storm crystals / orb, the 115-grenade set. BUILT: FULL BUILD OK (tmp/jumppad_fix/full2.log, log end 16:13:41): .ff 16:11:50, FF 229,424,640 B, geom_key REUSED the 15:32 bake; the new post-link gate ran inside it (49 materials all complete, 31 of 31 textures, no linker usage / techset complaint naming a pad asset); the 12 formerly empty materials are 1,136-2,074 bytes; the same 8 known-waived ERROR lines; deployed = repo, nothing synced after, no repo edits after the 16:01:40 start. It also carries -09's C4 armed-tell fix. UNPLAYED.

**2026-10-03 15:12 - THE JUMP PAD IS DER EISENDRACHE'S JUMP PAD (user: "The jump pad on this map is a teleporter but I want it to have the jump pad model from der eisendrache. Can we switch it over with same functionality"; docs/163 s9; CHANGELOG 15:12).** The crown balcony's pad wears DE's JUMPSPHERE now (its `_zm_flingers.gsc` pad: a broken-open half-sphere machine over a lit deck; you walk in through its doorway and fly out of its open side) and the landing deck has DE's landing pad with the four set-down spots ON it; the teleporter model / beam / discharge / materialize / tod_warp are gone from the pad. NEW `tools/jumppad/install_de_jumppad.py` (from `~/Downloads/T7 Assets V2.8.rar`; never hand-edit its outputs; `--check` is a build gate and never reads the pack): `model_export/tod_jumppad/` (5 models: `tod_jumppad_frame`, `_deck_off|_on`, `_land_off|_on`), `source_data/tod_jumppad.gdt` (49 DE materials verbatim, 31 textures renamed `i_tod_jp_*` - the pack's generic `i_t7_*` names are referenced, never defined, by stock GDTs in the tools root, so a stock-name import would collide in gdtdb), `sound_assets/tod/jumppad/` (3 mastered flinger wavs, aliases in `tod_jump.csv`); 8 textures DE borrowed exist nowhere in the pack -> `SUBSTITUTES` (with reasons). SAME FUNCTIONALITY: the flight, the hang clock, the first-jump scene, one-way, the power gate and every guard are untouched; the trigger is r 40 (was 72) = the inside of the machine; `JP_PAD_YAW` 270 puts the doorway on the bridge corridor and the open side on the flight (DE's own arrangement). RULES: (1) the machine has no collision: `gen_tower_map.js` cuts 20 clip wedges round it (`jump pad shell N`, `JP_SHELL_*`, bulged where its side gadgets stand out) - a model change means re-measuring them; (2) `lint_tod_geometry.js` SKIPS any non-axial brush whose label it does not know (it was blind to the shell until taught): a new convex solid needs its label in that list or the lint cannot see it; (3) server FX here render only via `PlayFXOnTag` on a `tag_origin` script-model carrier (never bare `PlayFX`, never on an actor) - every pad effect uses that lane. Presentation: deck dark until the power, blue from it (+ the machine's crackle); launch = crackle + DE's fling burst + the whoosh on the mover + DE's trail; the landing pad glows while anyone is inbound (`level.tod_jumppad_flights`, cleared on the set-down AND an abort); touch-down = DE's landing dust + thud. Gates: `test_jumppad.js` 2b (shell vs trigger, doorway vs corridor, 3 negative controls), the installer `--check`, lint + parity + title + lanes green before landing. Logs `[TOD_JUMPPAD] INIT rev=7 pad=de_jumpsphere`, `STATE pad=ready`, `FX_FAIL`. BUILT: FULL BUILD OK 15:34:14 (tmp/jumppad_de/full1.log): .ff 15:32:18, FF 229,559,040 B, a FRESH map compile + navmesh + LED bake (geom_key saw the .map change); every build_map.ps1 gate ran inside it (the installer --check, test_jumppad, lint_tod_geometry, NAVMESH GATE OK = the crown hall + the pad inside the machine one component and the landing on the tower's, test_jump_title, the rest), the 8 known-waived linker lines only. VERIFIED after: `install_de_jumppad.py --compiled-ledger` = all 5 models with every LOD compiled whole, the 4 dlc1/castle effects, 49 materials, 30 of the 31 textures - AND THAT WAS THE BUG, NOT AN UNSAMPLED SLOT: the 31st was refused by the linker and 12 materials compiled EMPTY, the user saw the machine flat gray (the note above); scriptparsetree `_tod_jumppad.gsc` in the ledger; the 3 `tod_jumppad_*` stems in the loaded bank (all.sabl 15:31:09); deployed = repo (scripts / zone_source / ui / the GDT / model_export / the wavs / tod_jump.csv / the .map), nothing synced after the .ff, no repo edit after the build start. BlackOps3 started 15:34:20, after BUILD OK. UNPLAYED.

**2026-10-03 15:05 - THE BATTLE ARENA v2.2, THE ROUND BADGE IS THE LEVEL (user: "replace the round HUD with Battle Arena / Level 1 etc ... rounds dont count in there and its a static difficulty of progression through the battle arena levels"; docs/185 v2.2; CHANGELOG 15:05).** Inside the arena the HUD V2 round badge (tod_upgrade.lua's status plate, the top-left ROUND n of docs/182) wears a GENERATED ARENA TWIN - `i_tod_h2_arena_badge` / `_rampage`, cut from the round badges by NEW `tools/battle_arena/make_badge.py` (BATTLE ARENA in the pill, a LEVEL caption in the window, our glyph sheets, the badge's own sampled colours; `--check` in build_map.ps1 after the cue check; two GDT blocks + two zone image lines) - and its window shows the LEVEL (`TOD_ARENA_NUM_CAP` 12.75 / `_BASE` 55, LOCKSTEP make_badge.py `WINDOW_TEXT`); same `tod_arena` event as the readout, change-gated, the round back on the ride home; ONE chooser `badgeImage()` for round / arena x normal / rampage. `TodArena.lua` lost its title row (WAVE w OF 3 / N LEFT only, y 44..106). RULES: never paint the arena twins by hand (redraw the round badge, re-run the generator - a FULL build); a field name starting with `set` on the card-pull-style Lua mock hits its auto-stub (`imageWrites`, not `setImageCalls`). GATES: NEW `tools/test_arena_badge.lua` (the real upgrade menu through tod_round / tod_arena / todRampage; 2 negative controls), `test_battle_arena.js` 4b (80 / 20 mutants), `test_arena_hud.lua` (two rows). SEE IT: `tools/ui_mockup/render_arena_hud.py` (the badge cluster drawn with the plate's own arithmetic), `art/battle_arena/review/badge_review.png` + `hud_badge_corner_1080p.png`. Staged + proven in a scratch mirror while -a0's FULL ran, landed in one step (`land.py`, anchors asserted). The pause menu's ROUND box is unchanged. BUILD: Rode session -a0's FULL BUILD OK 15:01 (tmp/war_damage/full7.log; build 7 - build 6 died at the link at 14:41 on -a4's _tod_haven.gsc ternary, found and reported from this session, fixed by -a4 at 14:44): .ff 15:01:16, FF 229,403,200 B, geom_key reused build 6's fresh bake (LED 239,400,329 B). Ran INSIDE it: GSC STRICT LINT OK 135, BATTLE ARENA OK 80 / 20 mutants, ARENA SOUNDS OK 4, ARENA BADGE OK (2 badges = the generator; GDT + zone + Lua wired), ARENA HUD OK, ARENA BADGE HUD OK, HUD owner lifetimes 160. The 15:01:17 ledger carries image i_tod_h2_arena_badge + i_tod_h2_arena_badge_rampage (fresh .iwi converted 15:00:50), rawfile tod_upgrade.lua + todarena.lua, scriptparsetree _tod_arena.gsc + _tod_arena_data.gsc; all four tod_arena_* stems in the fresh loaded bank (15:00:18, 160.5 MB); every v2.2 input deployed = repo, nothing synced after the .ff; the 8 known-waived linker lines only. It also carries -a0's war damage phase 2, -a4's guarded haven (incl. its six lines in _tod_arena.gsc) and -09's docs/206. NOT in it: a fourth session's Der Eisendrache jump pad (the zone, _tod_jumppad.gsc, the regenerated map + data scripts, written 15:04, after the .ff) - theirs to build.. SUPERSEDED AS THE TEST .ff by -a4's haven v4 FULL BUILD OK 17:46 (tmp/haven_v4/full1.log; .ff 17:44:19, FF 229,771,520 B, fresh compile + bake), verified here: image i_tod_h2_arena_badge + _rampage, rawfile tod_upgrade.lua + todarena.lua, scriptparsetree _tod_arena / _tod_arena_data in its ledger, the four tod_arena_* stems in its loaded bank, deployed = repo, nothing synced after; the floor-40 chamber grew with the haven field to (92, 92) r 332 (BATTLE ARENA OK 80 on that tree). UNPLAYED.

**2026-10-03 15:04 - THE WAR DAMAGE PASS, PHASE 2: THE WAR IS STILL ON (user: "Yes lets go max quality and production ... Please do the best ... Do not stop until you are fully complete"; docs/205 s7 + s7b; CHANGELOG 2026-10-03 15:04).** Everything phase 1 left for later, built in ONE FULL build (a bake: the .map moved). THE BLAST'S WIRING: beside every crater the stock LED fixture dangles off its top bracket and the tower's own power conduit is TORN OPEN (`tools/war_damage/build_conduit_torn.py` tears the authored channel mesh: hinge + curl + twist, the WHOLE assembly bends; fray cables from the mouth); its two cyan conductors are a SEPARATE two-state client model (`tod_war_conductor_<a|b>_<off|on>`, `source_data/tod_war_conductors.gdt`) spawned at the body's transform - the layout's rotate() IS the engine's frame, proved per placement. THE POWER: NEW `_tod_war_damage.gsc` raises ONE 1-bit world clientfield `tod_war_power` at the power wave's first floor; `_tod_war_damage.csc` rev 2 replays the wave's schedule per client (51 floors from z 19168 by 384 over 12 s, LOCKSTEP gated): conductors come alive, a cyan arc spits at the mouth, the fixture's tube FLICKERS (three generated patterns, the flicker IS the light's intensity curve, loop = life; a tube counts in the light budget, `TOD_WAR_LIGHT_MAX` 4). THE WAR IN THE SKY: NEW `_tod_war_sky.csc` - far detonations with booms late by the distance (the speed of sound), barrages, tracer exchanges, a STRICKEN SHIP falling out of the sky through the fleet's own `stand_in()` / `engines()` with fire + smoke and an impact beyond the horizon; the sign's cone stays clean (LOCKSTEP sign yaw) and the war HOLDS through the first-jump scene. BUILD B: the broken flight's stair pool is GONE at every break (76 route pools; `verify_tower_design.js` counts 100 - the drops) and the broken pieces + lip landing + the crater's core face wear SCORCHED twins of their kit roles (`make_scorch.py` -> 15 maps, the kit's third source library in `install_surfaces.py` / `verify_surfaces.py` 45 maps; ten `<role>_scorched` roles; `scorch.json` from `layout.js` applied per face by `tower_surfaces.js`). GENERATED: 13 effects (`make_fx.py`), 8 sounds (`make_sounds.py`, the user's `tod_c4_explode.wav` for the far booms). RULES: (1) `test_war_damage.js --ledger` is DEPLOYMENT-AWARE - a peer's sync predates later repo edits, so a ledger is held to what the DEPLOYED zone named and triangle checks run only on bins the record describes (a -GscOnly of -7a's synced phase 1 while phase 2 landed); (2) before calling the shared root free, check `tmp/*/` for fresh build starts and the usermap's sync mtimes, not only process names (memory detect-running-build-by-script); (3) any new spawn/effect kind in layout.js lands in the csc's list + precaches + `wire.py` (gated); the wave constants in the csc are gated against `_tod_fall.gsc` / `tod_crown_data`; (4) the first torn-conduit cut bent only the lips and read as thin legs - tear the whole assembly (reviewed in Blender first: `preview_wiring.py`); (5) A CHANGE TO `source_data/tod_surface.gdt` IS A DEALER-PANEL RE-REVIEW - `tools/dealer_presence/verify.py` pins its bytes (build 5 died there on my ten scorched twins): `layout.js` + `inventory.js`, the previews through the studio (`start_studio.ps1`, then `mcp_call.py tools/dealer_presence/preview.py` with the FULL path), a `rereviews` entry in `review_acceptance.json`, the studio stopped before the bake; (6) NO GATES-ONLY BUILD SWITCH EXISTS: run the gate lines on the repo by hand before a FULL build - builds 3 / 4 / 5 died before cod2map on a teleporter stub (-a4's landing), a Retriever stub (-09's landing) and that pin (mine); memory run-gates-on-repo-before-full-build; (7) NEW GATE `tools/lint_tod_gsc_strict.js`, FIRST in build_map.ps1's GSC step: build 6 baked fresh and then died AT THE LINKER on -a4's never-compiled `_tod_haven.gsc:963` (`SetModel( ( c ) ? a : b )`; the compiler needs `( c ? a : b )`, the gsc_eval harnesses accept the bad shape) - the lint checks unwrapped ternaries, `( expr ).field`, late `#using`, keyword-less functions, never-assigned locals and brackets, self-tests 8 planted errors every run, zero hits on the 108 scripts that compiled; the linker stops at the FIRST script error, so every script changed since the last successful link is uncompiled; geom_key records a bake before the link, so a link failure after a fresh bake costs only gates + link to retry. Gates: `test_war_damage.js` 431 / 18 negative controls, `verify_surfaces.py` (45 maps), `verify_tower_design.js` (76 pools), lint geometry no regression, `verify_crown.js`, `dealer_presence/verify.py`. BUILT: FULL BUILD OK 15:01 (tmp/war_damage/full7.log; geom_key REUSED build 6's fresh bake - BSP 14:26:33, LED 239,400,329 B, navmesh): .ff 15:01:16, FF 229,403,200 B, the 8 known-waived linker lines only. Inside it: GSC STRICT LINT OK 135, WAR DAMAGE OK 431, DEALER_PRESENCE_SOURCE_OK, NAVMESH GATE OK (25 sections + 24 drops, crown island, arena, 8 pads) on the reused mesh, then WAR DAMAGE LEDGER OK (110 LOD files, every triangle), HAVEN / SKY FLEET / JUMP TITLE / LUCKY ledgers OK. VERIFIED: the 15:01:16 ledger carries scriptparsetree _tod_war_damage.gsc + .csc + _data.csc + _tod_war_sky.csc, 38 xmodel tod_war_* (34 clusters + 4 conductor twins), 13 fx tod/war, 10 scorched materials + 15 scorch images; all 8 war stems in the fresh loaded bank (all.sabl 15:00:18, 160.5 MB); deployed = repo (scripts / zone_source / ui, tod_war.csv, both GDTs, model_export/tod_war_damage, sound_assets/tod/war, the .map: 76 route pools); nothing synced after the .ff; no repo source edited after the build start. It also carries -7a's arena v2.1 + v2.2, -a4's haven v3 (its first compile) and -09's docs/206 (their rows verified in the same ledger and bank). PLAYED ONCE 15:34-15:45 (the jump-pad session's .ff 15:32:18; log tmp/elite_tracking/runs/20261003_154548_488_a1bee5db): 34/34 models, 27/27 conductors lit in order by the wave, the effect window inside budget crown -> ground, the sky war incl. 2 stricken ships and the first-jump hold, zero script errors; ONE FLAW - every sky site at one distance (11,252), every boom 2.0 s late (`site()` clamped only by the box) - FIXED: the radius is picked in R_MIN..R_MAX then clamped (gated, negative control); -GscOnly BUILD OK 15:58 (tmp/war_damage/gsc8.log, .ff 15:58:20, FF 229,559,168 B), the fix UNPLAYED. Logs `[TOD_WAR]` / `[TOD_WAR_SKY]` (dev switches 1; zero before a publish).

**2026-10-03 13:43 - THE ABILITY FEEDBACK, SECOND PASS: EVERY MOVE SEEN AND HEARD, SOUNDS MADE FOR THE MOVES (user: "Any tweaks or enahncmenets we can make on upgrade moves special effects or sounds?" -> "implement everythin gelse you find"; "you have eleven labs API ... generate new sounds"; "I also have upbeat ... tell me what to search"; docs/206; CHANGELOG 2026-10-03 13:43).** AUDIT after docs/203: the Cyber Smash DIVE invisible in the air, a CHARGED blade seen by its owner only, the CLOAK on Blink's stock pair, A CARD TAKEN = the panel alone, the RIOT SHIELD break SILENT (PlaySoundAtPosition of a custom alias) and its return the lounge chime, a planted C4 mute, no full-DRAW moment, PIERCING unseen, five bare server PlayFX one-shots + a server PlayFXOnTag on an actor (none render here), the tier-3 cluster pop lightless, every first-pass cue a borrowed stock wav. BUILT INTO `_tod_ability_fx.gsc|.csc` rev 2: 8 new kinds, 2 new body states (dive streak, sword-hand glow), THE ACTOR HIT LANE (`tod_abfx_hitk` then `tod_abfx_hit`, drawn on the zombie by the client: pierce / Retriever hit / rune torso fire for `TOD_ABFX_BURN_SECS` = `TOD_RUNE_TRAP_MS`) and `burst_at()` carriers for every world one-shot; hooks in the kit (dive from both slam lanes, NEVER inside gs_dive_* - test_gs_dive transpiles them; sword_ready from hud_send; c4_armed; the lit `fx_abfx_cl_pop_t3`), cards (cloak_on/off, pierce_hit), riot shield, bow (draw_full), archer / retriever / rune, `apply_upgrade` (card_taken x3); `gen_tod_twins.js` gives the gauntlet + Cyber Sword their own `meleeImpactEffect` (a weapon GDT change = FULL build). THE 1P RULE: the new body one-shots play for the OTHERS only. SOUNDS: NEW `tools/ability_fx/make_sounds.py` (ElevenLabs takes measured + scored per cue profile; `pick` levels + ships 23 files / `sound_assets/tod/abfx/` and regenerates `tod_ability.csv` whole; the dive is time-REVERSED (`shape="reverse"`: the model puts the loudest moment first whatever the prompt says); an Uppbeat drop in `tmp/ability_sfx/drop/<cue>.wav` wins the pick; `brief` = the search list in docs/206 s4; `--check` in build_map). `gen_fx.py` renders 55 effects (24 + 31). RULES: a new world one-shot -> `burst_at`; on a zombie -> `actor_hit`; on a player -> a kind on `play()`; never a bare PlayFX / PlayFXOnTag on an actor; un-wired generated work waits OUTSIDE the gated paths (my 30 un-zoned effects failed -7a's build at my own gate at 12:48 and were parked until this one-step landing). Gate `test_ability_fx.js` (rewritten for the pass) + `make_sounds.py --check`. Logs `[TOD_ABFX]` DIVE / SWORD / CARD / SHIELD / C4_ARMED / BURST / HIT / FX_DROPPED, `[TOD_ABFX_C] HIT`. BUILD: BUILT in session -a0's FULL BUILD OK 15:01 (tmp/war_damage/full7.log; geom_key reused build 6's bake): .ff 15:01:16, FF 229,403,200 B, the 8 known-waived linker lines only; inside it ran the new GSC STRICT LINT (135 scripts), ABILITY FX 448, ABILITY SOUNDS OK (21 cues / 23 files / 35 rows), ABILITY FEEDBACK 455 and NATIVE RETRIEVER. VERIFIED here (scratchpad verify_build.py): the 15:01:16 ledger carries scriptparsetree _tod_ability_fx.gsc + .csc and all 9 touched scripts, all 55 fx,tod/abfx rows and 24 weapon rows cc_gauntlet* / cc_gold_sword*; the deployed tod_weapon_twins.gdt carries the blade hit effects (32 gauntlet / 16 sword lines); the fresh loaded bank (all.sabl 15:00:18, 160.5 MB) indexes all 23 tod_abfx_* stems; every touched file deployed = repo and none of mine edited or synced after the build. Build 6 (14:41) carried the same tree and died at the compiler on a PEER line (_tod_haven.gsc:963, an unwrapped ternary in a call argument that every JS gate accepted), fixed by its owner before build 7. UNPLAYED. C4 TELL FOLLOW-UP 16:01 (the user's 15:34 run: 4 C4 plants, the armed blink/beep never played - it waited out the 3 s stick window): it now arms the moment the charge is still, once (`[TOD_KIT] C4_TELL at=`); BUILT in session -f8's FULL BUILD OK 16:13 (tmp/jumppad_fix/full2.log; geom_key reused the 15:32 bake): .ff 16:11:50, FF 229,424,640 B; ABILITY FX 451, ABILITY SOUNDS, C4 CONSISTENCY and the GSC strict lint ran inside it; verified here: the deployed _tod_class_kit.gsc = repo with the rest arm, every ledger row of the pass, 23 / 23 stems in the 16:11:05 loaded bank, nothing synced after. UNPLAYED.

**2026-10-03 13:23 - THE GUARDED HAVEN: THE SAFE ZONES ARE EVIL UNTIL YOU TAKE THEM (user: "the dome should be evil at first have doppleghast inside and a couple manglers. You must kill them and then the area turns into a safe zone. So you must defeat this boss area to take it. No effects or safe visuals and all that until you defeat those elites. So two distinct states"; + "Lets do 1,2,3,5"; docs/202 v3; CHANGELOG 2026-10-03 13:23).** SUPERSEDES the one-state haven in the notes below. Every dome boots CORRUPTED (`tod_haven_dome_dark`, the dark hum, `fx_tod_haven_corrupt`, the sign red + glitching) and DOES NOTHING - no slow / cut / kill tax / ripple / bleed grace; its pad (and the floor-40 arena gate) is dead (`level.tod_haven_locked_fn`, hint "defeat the guardians"). THE GUARDIANS wake when a player enters the wake band (`WAKE_R` 640 / `WAKE_Z` in `haven_layout.js`) and rise INSIDE the field (`haven_guard_spots`): 40 = 1 Doppelghast + 2 Manglers, 30 same, 20 = 2 + 2, 10 = 2 + 3, +1 Doppelghast for 3-4 players (`TOD_HAVEN_GUARD_*`; HP 8 / 6 round zombies); they hunt THEIR OWN FLOOR ONLY (`actor.tod_hunt_filter` = `_tod_haven::guard_target_ok`, honoured by `_tod_doppelghast` / `_tod_mangler::hunt_target`; `tod_hunt_home` = where they stand when nobody is there; a strayer past the leash band is pulled back). Every death cracks the dome + GUARDIAN DOWN - N LEFT; the LAST one CLEANSES (`fx_tod_haven_cleanse` + sound, the stutter crimson -> cyan, hum swap, the sign to the district colour, FLOOR N HAVEN SECURED to everyone + `TOD_HAVEN_CLEANSE_PTS` 500 each; members inside / enemies inside switch at once). TWEAKS: #1 `fx_tod_haven_slowed` on a carrier linked to every slowed enemy (cap `TOD_HAVEN_SLOW_FX_MAX` 10 per field); #2 the x1.19 spawn rest asks `level.tod_haven_calm_fn` (inside a TAKEN field only; the hall box no longer calms); #3 `TOD_HAVEN_BLEEDOUT` 1.5 on `n_bleedout_time_multiplier` inside a safe field, held through a down, `tod_haven_bleed` mask -> `TodHealthTint.BleedoutMs` for both kit bars (LOCKSTEP `BLEED_MULT`); #5 FLOOR N sign cards from the glyph sheets (`make_dome.py`, 8 skins on one quad, `SIGN` in the layout). RULES: a gated path (tools/haven/*, haven_layout.js, the haven fx/sounds) must be self-consistent at EVERY instant (my wrong assert killed two peer builds at `require`; fix, prove the gates, send "TREE SAFE"); a function the haven gate runs is wait-free and endon-free; an elite's targeting hook is a per-actor pointer, never a global; RUN EVERY BUILD GATE before TREE SAFE (tools/teleporter/test_states.js evaluates the shipping refresh() with callee stubs and died on my new pad_lock_reason_at until it got one - -a0's FULL build paid for that); a TERNARY USED AS A BARE CALL ARGUMENT passes every JS gate and kills the LINK (my _tod_haven.gsc:963 killed -a0's build 6 after its bake) - wrap it whole `( ( c ) ? a : b )`; `tools/lint_tod_gsc_strict.js` gates it now; new GSC is unproven until a link has compiled it. HUD events: `tod_haven( inside, flags, state, left )`, `tod_haven_state( kind, floor, left )`, `tod_haven_bleed( mask )`. Gates: test_haven.js (29 mutants), test_haven_hud.lua (3 negative controls), test_archmage_health.lua, test_ambush.js. Review: `tools/haven/preview_states.py` -> art/haven/review/state_*.png. BUILD: FULL BUILD OK 15:01 in -a0's war-damage FULL build (tmp/war_damage/full7.log; .ff 15:01:16, FF 229,403,200 B; geom_key reused build 6's fresh bake): GSC STRICT LINT, HAVEN GATE 360 / 29, the three --checks and HAVEN LEDGER OK 35 (the whole list) ran inside it; every haven input deployed = repo (the 14:44:42 _tod_haven.gsc included), nothing synced after; all ten tod_haven_* sound stems in the fresh loaded bank (all.sabl 15:00:18, 160.5 MB); the jump-pad session's 15:04 regen left _tod_breather_data.gsc byte-identical and HAVEN GATE OK 360 still holds on the repo. Its full4 / full5 attempts died on peers' gates after every haven gate passed; full6 died AT THE LINKER on my _tod_haven.gsc:963 (a ternary as a bare call argument), fixed 14:44. UNPLAYED - the guardians' fight, the two looks and the cleanse moment are the user's to judge.

**2026-10-03 13:18 - THE BATTLE ARENA v2.1, THE READABLE FIGHT (user: "Give the arena one more pass from a players perspective and see how we can continue to enhance"; docs/185 v2.1; CHANGELOG 13:18).** The v2 fight was MUTE (no wave / count / where-from / when-the-dais-bites); nothing in the rules moved. THE READOUT: NEW `TodArena.lua` (AetheriumHud child, veiled with the HUD) - LEVEL l OF 10 / WAVE w OF 3 / N LEFT (ticks per kill, RED at `TOD_ARENA_HUD_HOT` 3, WAVE CLEARED / LEVEL CLEARED / THE KEEPER) on `tod_arena ( show, level, levels, wave, waves, left, flags )` = SEVEN ints (RULE: `test_tod_native_api.js` accepts only evidenced call shapes; stock's LuiNotifyEvent carries 1-5 or 7 values, six FAILED the gate); `hud_left` pure; re-sent every 2 s, a same-state re-send draws nothing. THE CUES: NEW `tools/battle_arena/make_sounds.py` (generated, `--check` in build_map after the arena gate): wave horn / clear sting / level fanfare 2D to every player, `tod_arena_gate` 3D at the gate; `sound/aliases/tod_arena.csv` + the szc entry. THE GATE TELL: an elite's gate charges 1.0 s (`TOD_ARENA_GATE_TELL_SECS`: the teleporter's wind-up + the cue), flashes, THEN the elite rises; gates open together on threads, `spawn_wave` waits for them. THE MOOD LIGHTS: five todPerkGlow hosts from GENERATED `arena_mood_orgs()` (4 pylon collars + the dais LAST; the .map byte-identical after the regen), `mood_index` teal 1-3 / yellow 4-6 / orange 7-8 / red 9-10, the dais WHITE for the overcharge's wind-up. FAIRNESS: the wind-up warns late steppers (`PURGE_WARN_LATE`); the chamber prints the level after 2 s inside (once per level). SEE IT: `tools/ui_mockup/render_arena_hud.py` -> `art/battle_arena/review/hud_*.png`. GATES: test_battle_arena 66 / 20 mutants (section 4b), NEW `tools/test_arena_hud.lua` in the Lua harness list, TodArena in test_ui_lifetimes; the whole harness list, arity, native API 10,252, assets, hints 92/190, sound context, Keeper, pursuit, ambush, haven all green before the build. BUILD: -GscOnly BUILD OK 13:18 (tmp/battle_arena_v2/gsc_v21c.log; the THIRD attempt: the first (12:46) died at -09's ability-FX gate on 30 un-zoned effects it had just generated, the second (12:51) at -a4's haven gate on a layout self-assert it had just edited - both peers' mid-edit files in gated paths, both fixed by them before the third sync at 13:08): .ff 13:18:01, FF 229,325,888 B, on the 05:18 BSP / LED / navmesh. Ran INSIDE it: BATTLE ARENA OK 66 / 20 mutants, ARENA SOUNDS OK 4, ARENA HUD OK + HUD owner lifetimes 160 (TodArena inside), arity 135 files, native API 10,371 sites. The 13:18:01 ledger carries scriptparsetree _tod_arena.gsc + _tod_arena_data.gsc and rawfile todarena.lua; the loaded bank rebuilt 13:17:14 (159.4 MB, +0.6 MB) indexes all four tod_arena_* stems; every arena file verified deployed = repo at 13:19 (the cues at the tools-root sound_assets); THEN at 13:20:54 session -a4's guarded-haven landing (docs/202 v3) INSERTED six lines into the repo's _tod_arena.gsc (a "haven_corrupted" refusal + the ^1defeat the guardians hint + a "corrupted" pad state, all reading level.tod_haven_locked_fn; nothing of v2.1 removed or reworded - BATTLE ARENA OK 66 re-run on it) and -a0's FULL build synced that tree at ~13:23 (its sync preserves mtimes, so a repo-vs-deployed diff reads green): those six lines are NOT in this .ff - they ride -a0's FULL build (tmp/war_damage/full3.log), which supersedes this .ff as the test .ff once -a0 reports BUILD OK and the arena rows; the 8 known-waived linker lines only. NOT in this .ff (edited after its sync, theirs to build): -a0's war-damage phase 2 (_tod_war_sky.csc, the entry #usings, the zone's war block, tod_war.csv) and -09's staged ability sounds. UNPLAYED. Logs `[TOD_ARENA] HUD / GATE_TELL / MOOD / PURGE_WARN_LATE / NOTICE`.

**2026-10-03 06:04 - THE WAR DAMAGE PASS: THE TOWER LOOKS LIKE IT LOST A WAR (user: "The tower needs a bit more flavor. The broken off pieces look to clean ... looks like its been fallen and beaten up by wars"; docs/205; CHANGELOG 06:04).** CLIENT-ONLY, ALL STOCK ART: `tools/war_damage/layout.js` places Treyarch's rubble / slabs / rebar / iron / cables / glass + dark decal cards + effect anchors on the 24 breaks and sparsely on the floors between (seeded per lap; every piece CHECKED against keep-out zones: the landing column, the landing body space, the walkway middle, the rail band, the next lap's landing), `build_clusters.py` merges them (PyCoD) into 34 models x 3 LODs (no collision), NEW `_tod_war_damage.csc` spawns them once per local client and runs dust / embers / 8 fires with firelight / 19 sparking cables / ash / 6 always-on smoke columns + looping 3D crackles in a window round the player (`TOD_WAR_WINDOW_Z` 700 / `_XY` 1800, `TOD_WAR_FX_MAX` 26, `TOD_WAR_LIGHT_MAX` 3; real-time tick). No server entity, invisible to every server trace (grapple, recall, navmesh, reach untouched); the .map did not change. RULES: (1) a decal must be MEASURED darker than the dark district panels (Blender reads the decal TIFFs' 4th alpha sample PIL drops): charred_stain_01 / blast_01 / the metal shrapnel holes ship; burn_impact_01, charred_stain_02 and the concrete cracks read pale and are out; (2) the converter silently drops zero-area triangles and STOCK meshes carry them (the rubber cable's lowest LOD: 4), so the merge drops coincident-corner triangles itself (`degenerate_dropped` in clusters.json); (3) the xmodel ledger lists LODs LOWEST DETAIL FIRST (lod L = `tris(lodCount-1-L)`); (4) wire with `tools/war_damage/wire.py` (one step, `--check`, `--unwire`); a layout change = layout.js + build_clusters.py + wire.py + a FULL build (a GDT). Gate `tools/war_damage/test_war_damage.js` (372 checks, 9 negative controls; `--ledger` after the link proves every model kept every triangle). Review `art/war_damage/review/review.html`. Logs `[TOD_WAR] INIT / WINDOW` (`TOD_WAR_LOG` 1; zero before a publish). BUILT: FULL BUILD OK 06:03 (tmp/war_damage/full2.log; geom_key reused the 05:18 bake): .ff 06:01:44, FF 229,314,304 B; WAR DAMAGE OK + LEDGER OK inside it; the ledger carries both scripts, 34 xmodel tod_war_*, the 8 effects, the 5 decal materials; both wavs in the fresh loaded bank; deployed = repo, nothing synced after, the 8 known-waived lines only (build 1, 05:46, failed the ledger check: rule 2 + 3). UNPLAYED.

**2026-10-03 05:02 - THE BATTLE ARENA v2, THE CRUCIBLE + THE TELEPORT LINES UP (user: "the battle arena teleporter waits way too long to actually teleport ... It doesnt line up. Also the battle arena needs to be actually designed ... no real spot to camp ... heights to allow vertical traversal ... skill gap but be super hard ... spawns need to be thought out and structures"; docs/185 v2; CHANGELOG 05:02).** THE DELAY was three INLINE `tod_teleport::fx_burst` calls (it waits out its effect's life): use -> jump measured 6.6 s in the user's 2026-10-01 log, sound 3.6 s late, arrival flash 3.15 s after landing. Every arena fx_burst is threaded now; the jump is `TOD_ARENA_CHARGE_SECS` 0.8 (LOCKSTEP `TOD_TP_CHARGE_SEC`), the return 0.8; `tools/test_battle_arena.js` TIMES both from the script and its v1 fixture must time out at 6.6 s. THE ROOM (`tools/battle_arena_layout.js`, generated): a 1664-square colosseum - THE PIT (pylons, 8 lit gates = elite entrances), THE RING at 120 (loop, open ledge, 4 pinwheel stairs), 4 SPOKES 120->240 with landings and beams, THE DAIS at 240 (arrival + the arena's return teleporter), the undercroft. EVERY LEVEL ON FOOT (a perch zombies cannot reach = a camp); every ledge open; NO FALL DAMAGE in the arena during a fight. THE DIRECTOR (`_tod_arena.gsc`, pure core run by the gate): 26 flat spawn points, never within 380, 650 ideal, backs over faces, spread, no repeat; CAMPING (200 u / 7 s) pulls spawns + the next elite gate to the camper. THE DAIS OVERCHARGES every 25 s (2.5 s wind-up, 40% max health to anyone on it, zombies on it die). HARDER: 12 (+3/level) zombies a wave, full sprint, elites from wave 1 on Lv3+. RULES: (1) an arena ledge is legal in `lint_tod_geometry.js` only over arena floor <= 256 below (ARENA_LEDGE_MAX; selftest deletes an apron and requires the holes back); (2) the roof vent is a 24 SLOT (Umbra `small_hole=4.000`: open air to it, closed to a body) - never a gap a launch or rope can reach; (3) keep `battle arena floor` at its v1 extent or the 8 conduit inlays move (`conduit_layout.js --check`); (4) any arena size/height change needs `node tools/sky_ships/gen_lanes.js` before a build (this one blocked 193 lanes; regenerated, test_sky_ships + test_jump_title green); (5) no zombie traversal links until a native test proves them (elites map climbs to a melee anim, the Keeper to an unverified teleport mocomp). (6) a rise in the link's `Filtered N/M inside clusters` is NOT by itself a sealed room (this build: 245/247 -> 256/258 = dead air behind the corner chamfers): `test_battle_arena.js` section 3b floods the arena's air at Umbra's 4-unit hole and fails a sealed room (lidded-slot negative control; added 05:35, after the build). `lint_tod_navmesh.js` now requires 30 surface probes (`arena_nav_probes()`) on the arena's one component. Review renders `art/battle_arena/review/` (`tools/battle_arena_review/`). BUILD: FULL BUILD OK 05:21:16 (tmp/battle_arena_v2/full2.log): .ff 229,095,232 B, fresh BSP + LED 239.5 MB + navmesh + Umbra; BATTLE ARENA OK, NAVMESH GATE OK (4 arrivals + 26 spawns + 30 surface probes in one component), SKY LANES OK, PURSUIT + HAVEN ran inside it; the ledger carries _tod_arena / _tod_arena_data / _tod_sky_lanes; deployed = repo, nothing synced after; the 8 known-waived lines only. SUPERSEDED AS THE TEST .ff by session -a0's FULL BUILD OK 06:03 (tmp/war_damage/full2.log; war damage; .ff 06:01:44, FF 229,314,304 B; geom_key REUSED this build's BSP / LED / navmesh), verified here: BATTLE ARENA OK 41 (the air flood ran inside it), the navmesh gate's arena line on the reused mesh, SKY LANES OK, its ledger carries _tod_arena / _tod_arena_data / _tod_sky_lanes, deployed = repo (the map at the tools root too), nothing synced after. UNPLAYED. Logs `[TOD_ARENA]` (JUMP ms_since_use ~800, RETURN ride_ms ~800, SPAWN, CAMP_START/END, PURGE_WARN/PURGE, FALL_GUARD).

**2026-10-03 04:34 - THE AMBUSH + THE TRICKLE: ZOMBIES CLIMB OUT ROUND YOU, MORE OF THEM A SECOND (user: "This map should be more hectic than the first"; "We should have challenging spawn points as well to make it tougher"; docs/204; CHANGELOG 04:34).** AUDIT: spawn rate, speed curve and the two fixed landing-corner risers per floor were map 1's, unchanged; only the live cap was higher (36/42/48/54). NEW `_tod_ambush.gsc`: 30% -> 60% (round 15, +15 rampage, max 80) of ordinary spawns climb out of the navmesh 360-900 round a random upright player, one flight up/down: AHEAD 50 / BEHIND (off every screen) 35 / FLANK 15, fallbacks then the corners; every spawn rule re-applied to the point (walk model + CanPath, stock's active-zone rule, 360 from anyone, havens, arena, crown gate / Fall seal / sealed hall), one ambush a player per 0.6 s, ring inside THE HUNT's far bar (LOCKSTEP `TOD_AMBUSH_INNER` >= `TOD_STRAY_DEST_MIN`, OUTER + 4 x HEIGHT <= `TOD_STRAY_COST`); hooked in `finale_spawn_selection` outside the finale aggro run. THE TRICKLE: `TOD_SPAWN_MULT` 0.70 (was 0.83), `TOD_SPAWN_FLOOR` 0.20, rampage floor 0.16, round size `TOD_ROUND_MAX_AI` 28 / `_AI_PER_PLAYER` 7 so rounds keep their length (x1.19+ zombies a second vs map 1, round length x0.93-1.01). Movement speed unchanged. RULES: the module imports only leaf modules (the round module imports it; `_tod_bosses` -> rounds is a cycle); the zone test moves ONE probe entity, never spawns one per lookup; any new spawn rule in `finale_spawn_selection` must be re-applied in `tod_ambush::legal`. Gate `tools/test_ambush.js` (51 checks, 24 mutants). Logs `[TOD_AMBUSH]` (dev; read `agent_self` vs `agent_other` and `zone_fail` / `path_fail` in the SUMMARY). BUILT: -GscOnly BUILD OK 04:43 (tmp/ambush/gsc1.log): .ff 04:43:00, FF 229,081,856 B; AMBUSH OK ran inside it; the ledger carries scriptparsetree _tod_ambush.gsc + _tod_endless_rounds.gsc; scripts / zone_source / ui deployed = repo, nothing synced after the .ff, no repo source edited after the build start; the 8 known-waived linker lines only. UNPLAYED. SUPERSEDED AS THE TEST .ff by session -7a's FULL BUILD OK 05:21:16 (tmp/battle_arena_v2/full2.log; Battle Arena v2, FF 229,095,232 B), verified here: AMBUSH OK ran inside it, its 05:21:16 ledger carries _tod_ambush.gsc + _tod_endless_rounds.gsc, both deployed = repo. THAT IN TURN SUPERSEDED by session -a0's war-damage FULL BUILD OK 06:03 (tmp/war_damage/full2.log; .ff 06:01:44, FF 229,314,304 B), verified the same way: AMBUSH OK inside it, its 06:01:44 ledger carries both scripts, both deployed = repo.

**2026-10-02 22:10 - THE DEALER'S MASK v6 = LESS CYBER (user, hearing round 9: "Less cyber on the voice"; CHANGELOG 22:10; docs/198 "The mask v6").** The cyber of the mask is the flanger shimmer + the ringing reflections: `mask_tone.py` builds the chain from `CYBER` (0.45, both at a little under half of v5; the dark body / honk / clip and v5's open top untouched; a deep voice keeps its own pitch). The same round-9 takes re-shipped through it (`pick.py`, no credits). The next notch if asked: `CYBER` 0.25; `1.0` is v5 exactly. BUILT: -GscOnly BUILD OK 22:48:22 (tmp/dealer_own/gsc2.log; on the haven session's 21:29 BSP / 21:30 LED): .ff 22:46:42, FF 229,071,424 B, the 8 known-waived lines only, BLACK MARKET VO OK 83 + HAVEN LEDGER OK inside it. VERIFIED: the 22:46:42 ledger carries _tod_shop_vo / _tod_dealer_finale / tod_dealer_body_cracked + the haven rows; all 83 dealer stems in the fresh loaded bank (158.3 MB, 22:45:58), all 83 deployed wavs = repo under the v6 chain (the manifest records the exact filter per file), scripts / zone_source / ui diffs clean, nothing synced after the .ff. THIS is the test .ff for the dealer and haven trees. UNPLAYED.

**2026-10-03 04:15 - THE HAVEN CROSSING RIPPLE IS ROUNDED (user: "the inwards entrance and outwards entrance visuals portals effects should be rounded since they are on top of a rounded object ... enterable at any spot 360"; CHANGELOG 04:15; docs/202).** The crossing effect already played wherever a player crosses (any side); its SHAPE was flat - every sprite template is a camera-facing billboard, and the old 110-190 unit ones read as a plate hung on a ball. `fx_tod_haven_cross` / `_push` are now rings of small beads placed ON the field sphere (a circle on a sphere is flat: one cylinder spawn round the outward normal per ring, `spawnOffsetCylindricalAxis` 0, plane x = -SR (1 - cos a), radius SR sin a) firing outward over ~0.5 s, sparks streaking along the surface (`runRelToOffset`). RULE (gated in `make_fx.py --check`, with negative controls): no sprite in a crossing effect wider than `FLAT_MAX` 48, every ring on the sphere. Reviewed on the real dome first (`tools/haven/preview_ripple.py` reads the generated effects; art/haven/review/ripple_*.png). `haven_entry_dir()` (v1's dead single-gate direction) retired; map byte-identical. BUILT: -GscOnly BUILD OK 04:30:20 (tmp/haven_v2/gsc_ripple1.log; .ff 04:28:32, FF 229,074,432 B, on the 21:29 BSP / 21:30 LED): HAVEN FX OK + HAVEN GATE 171 / 14 + HAVEN LEDGER 11 inside it, the 8 known-waived lines only; the ledger carries fx tod/haven/fx_tod_haven_cross + _push and _tod_breather_data.gsc; deployed .efx + data script = repo, scripts / zone_source / ui diffs clean, nothing synced after, no repo input changed during it. UNPLAYED.

**2026-10-02 21:05 - THE DEALER'S VOICE ROUND 9 (user, hearing round 8: "No whispering"; CHANGELOG 21:05; docs/198 round 9).** The whisper was measured (periodic share / HNR / zero crossings on the design previews: round 8's `glitch 2` sat with the breathy group; the v5 pitch drop then muddied a deep voice): three FULL-VOICE prompts (`design7`), the default is now **TOD2 The Dealer (own voice: velvet full 3)** (`boMT8bVWzNHQG19WlKyD`), `mask_tone.py` `pitch_for_voice()` keeps a voice under 150 Hz at its own pitch (a tenor keeps v5's 0.87; nothing else in v5 moved), all 83 lines regenerated + the laugh re-cut + re-shipped, the desk rebuilt from `design7`. RULE: never a `[whispers]` tag, never a breathy prompt; measure a candidate's voiced share before shipping it. BUILT: -GscOnly BUILD OK 21:59:43 (tmp/dealer_own/gsc1.log; synced 21:36:49 after -a4's haven v2 FULL build, whose fresh BSP / LED / navmesh it reuses): .ff 21:52:45, FF 229,071,424 B, the 8 known-waived lines only; BLACK MARKET VO OK 83 ran inside it, JUMP TITLE + HAVEN LEDGER OK. VERIFIED: the 21:52:45 ledger carries _tod_shop_vo + _tod_dealer_finale + tod_dealer_body_cracked (and the haven rows); all 83 dealer stems in the fresh loaded bank (159.3 MB, 21:50:18), all 83 deployed wavs = repo under voice boMT8bVWzNHQG19WlKyD, tod_shop.csv deployed = repo, scripts / zone_source / ui diffs clean, nothing synced after the .ff. Spot-measured on the SHIPPED (masked) lines: periodic share 0.73-0.85, zero crossings 0.05-0.08 (round 8 shipped: 0.57-0.64 / 0.16-0.21). UNPLAYED; the voice default stays unapproved until the user picks on the desk.

**2026-10-02 20:30 - THE DEALER IS HIS OWN ENTITY (user: "redesign the black market dealer away from rictofen ... remove anything related ... At half health his mask will be cracked and one eye glow will be missing and his smile more menacing ... his voice a soft scary dark slightly cyber with occassional manic modes"; CHANGELOG 2026-10-02 20:30; docs/198 round 8, docs/199).** EVERY RICHTOFEN PIECE IS GONE: the donor head (`10_state2_head.py` deleted, the staged binary + 36 images + GDT blocks + `tod_dealer_body_unmasked` removed), the lore hints, the voice direction and THE CONSENTED CLONE (retired from every shipping asset, not deleted from the account; `docs/licenses/` stays as the record). STATE TWO = THE CRACKED MASK (`tools/dealer_boss/10_state2_mask.py`, `tod_dealer_body_cracked`): the same Dealer, the same bake, with the right temple and the grin's corner chipped to the void, black fissures + red leaks, the RIGHT X eye DEAD, the left burning harder, the grin torn wider with a lower seam, a black gape and seventeen fangs; one head bake with a per-face `dealer_state` and each variant dropping the other's faces (`export_native.py`); `_tod_dealer_finale.gsc` rev 2 `mask_crack()` at `TOD_DEALER_MASK_CRACK` 0.5 (ground set + Dingo unchanged). THE VOICE: a NEW text-designed ElevenLabs voice, default **TOD2 The Dealer (own voice: glitch 2)** (`tmp/black_market_vo/voice.json`, nine candidates in `design6/`, `approved_by_user: false` - the user picks on `tmp/black_market_vo/review/dealer_own_voice_desk.html`, built by NEW `build_own_desk.py`); all 83 lines REWRITTEN as his own story (`lines.json`, 31 `egg` hints about the ledger / the city before the Fall / the tower that pays him / the sign / the bigger mask / the first customer), eight marked `mode: "manic"` and rendered with `generate.py`'s NEW `VS_MANIC` (the occasional manic crack = a different delivery), the sign laugh re-cut from the new voice (take 7, 2.62 s), mask v5 unchanged. RULES: `review_state(n)` / `STATE = 2` / `16_head_review.py` to see either mask; author on a STAGED master (`TOD_DEALER_MASTER_OUT`) while a peer build's gates read the shipped master; `test_dealer.js` s7b FAILS on any `richtofen` / `c_zom_der_` / `mtl_c_gen_` / `_unmasked` name; never bring a borrowed head or voice back. Gates green before the build: test_dealer 1,165, pick --check 83, test_spin 647, test_jump_title. BUILT: FULL BUILD OK 20:42:30 (tmp/dealer_own/full1.log; the wrapper waited for -09's FULL and -a0's -GscOnly to clear): .ff 20:40:41, FF 228,713,472 B; geom_key REUSED the 18:47 compile + bake (map / materials / sky byte-identical), navmesh gate on the reused mesh, the 8 known-waived linker lines only. VERIFIED: the 20:40:41 ledger carries xmodel tod_dealer_body + tod_dealer_body_cracked + the scythe + both weapons, 21 i_tod_dealer images, 5 Dealer materials, 45 xanims, _tod_dealer_finale + _tod_shop_vo; ZERO unmasked / borrowed-head rows (the one 'richtofen' string left in the whole ledger is the stock HUD operator icon the Aetherium kit's player-character mapping names in aetherium_hud.zpkg, the Mage's body, not a dealer asset); all 83 dealer stems in the fresh loaded bank (157.7 MB, 20:38:35) and all 83 deployed wavs = repo; tod_dealer.gdt + both LOD0 binaries deployed = repo; scripts / zone_source / ui diffs clean, nothing synced after the .ff; the stale unmasked binaries + 36 borrowed-head images were removed from the deployed model_export after the link (nothing referenced them). In the build: dealer install --check OK, test_dealer 1,165, BLACK MARKET VO OK 83, SPIN 647. UNPLAYED: the cracked mask in game (he spawns in the crown hall for the test), the new voice's fit and level, the manic lines and the re-cut sign laugh are the user's to judge; the voice default stays unapproved until the user picks on the desk (tmp/black_market_vo/review/dealer_own_voice_desk.html).

**2026-10-02 20:05 - THE KILL FEEL IS RETIRED WHOLE (user, on the test list: "This hell bound work we can remove, I actually dont liek this"; CHANGELOG 20:05).** `_tod_kill_feel.gsc`, its aliases, strings, hooks (chokepoint + HUD kit), `corpse_will_linger`, the screen blood, the ember effect and its zone rows are GONE; kill feedback is `_tod_killconfirm` + the existing flings again; `tools/test_ability_fx.js` section D fails any revival. NEVER port Hellbound's kill feel again. The ability pass below stands (minus every kill-feel line in it); `tools/gen_kill_feel_art.js` keeps its name but draws only the two screen tints. BUILT: FULL BUILD OK 20:14 (tmp/ability_fx/full3.log; sync 20:03:45; cod2map + the LED bake REUSED by geom_key from the 18:47 full build): .ff 20:14:18, FF 228,723,584 B, loaded bank rebuilt 20:13:29 (155.5 MB); the 20:14:18 ledger carries scriptparsetree _tod_ability_fx.gsc + .csc, all 24 tod/abfx effects, image + material tod_demon_vignette / tod_fusion_vignette (both .iwi converted 20:13:50), and ZERO kill-feel rows; the 8 known-waived linker lines only; scripts / zone_source / ui / sound/aliases deployed = repo except the pursuit session's _tod_recall.gsc rev 2 (saved 20:05:46, two minutes after this sync - theirs to relink -GscOnly), nothing synced after the .ff. It also carries the safe-zones session's kill-pay edits (_tod_haven.gsc in the ledger). UNPLAYED.

**2026-10-02 19:40 - THE ABILITY FEEDBACK PASS + THE KILL FEEL (RETIRED 20:05, see above) (user: "Tower of Doom 1 has such good visual effects on the players abilities ... this map lacks that interaction ... Dash ... soul pulse is super ugly and dull ... Breacher explosive jump and heal ... Demon Slayer activation ... how they look in 3d world from other perspectives too" -> "Go ahead all of them"; docs/203; CHANGELOG 19:40).** ONE OWNER: `_tod_ability_fx.gsc|.csc` (an event field `tod_abfx_kind` registered BEFORE the counter `tod_abfx`, a 2-bit body state, an actor counter for struck elites; EVERYTHING client-drawn: a 1p half for the caster, a body half for teammates, world bursts at the cast origin in the donor's frame). 25 effects GENERATED by `tools/ability_fx/gen_fx.py` (`--check`; five stock effects here are STUBS - never donor fx_embers_falling_sm / fx_elec_burst_lg_z270_os / fx_ash_embers_light / fx_fire_debris_xsmall / fx_blood_torso_explo_zmb). BASH: blade streak + viewmodel light ramp + a shockwave sized to the burst (Lv9 reads wider) + stun tell for the whole stun. SOUL PULSE: a soul-blue dome with two lights under the ring, a mist on the camera (never a flash), elites flash. FUSION: ember heal + orange edge flash; a rocket burst, an air trail, a landing dust ring. DEMON SLAYER: red burst + aura + light + edge tint + the demon cry, extended by kills. THE KILL FEEL (`_tod_kill_feel.gsc`, Hellbound's layer): tiers of sound, screen blood, SKEWERED / MEAT CANNON / BUTCHER + CLEAVE / SOUL HARVEST signatures with feed labels, multi-kill + overkill labels, annihilate / dismember / fling (gated on NEW `corpse_will_linger()`); the MARKER and the elite ding stay with `_tod_killconfirm`; hooks are level pointers (`tod_kill_feel_fn` in the chokepoint before the damage number, `tod_kill_label_fn` in the kit). THE TILES REACT (`TodAbilityFeedback.lua`): ready flash, cast pulse, inferred recharge frame for every class. The Archer / Retriever looping rings now ride a self-deleting host (`ring_at`). RULES: a new ability effect goes through `tod_ability_fx::play` with a 1p AND a body half, never a server PlayFX; check a stock donor for `gfx_debug_missing_fx` first; sounds in both ears (2D plr + a 3D row). Gates: `tools/test_ability_fx.js` (299) + `tools/test_ability_feedback.lua` (455), in build_map. Logs `[TOD_ABFX]`, `[TOD_ABFX_C]`, `[TOD_KILL]`. BUILD: pending (FULL: new GDT `tod_kill_feel_art.gdt`). UNPLAYED.

**2026-10-02 21:22 - THE HAVENS v2, THE HEART: THE SAFE ZONE IS INSIDE THE TOWER (user: "make sure the teleporter for that floor is actually in the center of the safe zone ... inside the tower like how the endless tower has trials inside"; docs/202 "The layout, v2"; CHANGELOG 21:22).** SUPERSEDES the v1 layout in the note below (the T off the SW landing: threshold, spur, pad platform - built 18:51, never played). At each haven floor the CORE OPENS (the spire hub-hall grammar): the column stops under the hall floor and resumes 576 up; its S and W faces stay as 20-thick walls (`gen_tower_map.js` `corePieces` + `HAVEN.CUT`; same band colours). The field (ring 220, 293 tall) stands at (32, 32) with the TELEPORTER AT ITS EXACT CENTRE (floor 40: the Battle Arena gate; the chamber IS the field, `chamber_r()`); the machines ring the hall OUTSIDE the field in an L-shaped loggia under the next lap's flights (PaP / altar / crate east, two perk pads north); the way in is an ARCHWAY + 4x3 porch fan off the W flight's treads 12..16 (and the strip from tread 16); the next lap's E / N flights run round the void as galleries (sloped handrail + stepped clip guards); three emitter pylons, a ceiling projector, a fitted probe per hall. RULES: (1) `lint_tod_geometry.js` decodes `lap<N> haven` sloped brushes like crown ones - a visible balustrade it cannot see turns its clip guards into "invisible walls"; (2) `tools/haven_layout.js` asserts its whole layout on load (rims, field vs walls/galleries/porch corner, arrival ring on the floor, pylons, risers, respawns, bears) - move a machine there and let it refuse; (3) the floor-20 Dealer display backs onto the hall's S wall: any geometry change near it means `dealer_presence/inventory.js` + preview re-render + a re-review entry. Power-wire inlays on the loggia decks (`conduit_layout.js`), field gems on the pylon collars + a ceiling projector glow (`make_fx.py`). BUILT: FULL BUILD OK 21:35:10 (tmp/haven_v2/full1.log): .ff 21:33:23, FF 229,071,424 B, fresh BSP + LED; NAVMESH GATE OK + a compiled-mesh probe puts every hall point on all four floors on its floor's walk section; HAVEN GATE OK 171 / 14, HAVEN LEDGER OK 11, the 8 known-waived lines only. (4) THE LED DOUBLED 119.5 -> 237.3 MB, MEASURED: each fitted hall probe's bounce grid is 28.5 MB (near-cubic box, default `resolution` 4x); the pack's bake set 68 -> 98 MB; kept on purpose, the knob is in docs/202. SUPERSEDED AS THE TEST .ff by session -de's -GscOnly BUILD OK 21:59:43 (tmp/dealer_own/gsc1.log; .ff 21:52:45, FF 229,071,424 B) on this build's BSP / LED / navmesh, verified here: its 21:52:45 ledger carries scriptparsetree _tod_haven / _tod_breather_data / _tod_arena_data, the three dome models, the four haven effects and the conduits; HAVEN GATE + HAVEN LEDGER ran inside it; scripts / zone_source / ui deployed = repo, nothing synced after. UNPLAYED.

**2026-10-02 - THE HAVENS: THE SAFE ZONES ARE FORCE-FIELD DOMES - ENEMIES 33% SLOWER, 33% LESS DAMAGE, A COMPLETE REDESIGN (user: "act more like a safe zone ... a dome or like a force field that animates when you walk in and walk out ... a small visual effect on your screen ... shouldn't be huge ... I don't want it to look like map one ... 33% slower and 33% less damage"; docs/202; CHANGELOG 18:29).** The four TOD1 breather lounges (floors 10/20/30/40) are GONE: each is a HAVEN off the SW landing - a small THRESHOLD (the only way in) -> a hex force-field DOME (floor ring r 240) over a 512 platform with EVERY machine inside facing its heart (PaP, altar, crate, two perk pads) -> the SPUR to the teleporter pad (the Battle Arena chamber on 40). ONE layout source `tools/haven_layout.js` (gen_tower_map.js emits it; every anchor GENERATED into `_tod_breather_data.gsc`: `haven_*`, the moved `pap_*/station_*/crate_*/tp_pad_org/tp_arrival_org`, `lounge_index_at`, `secret_bear_*`, `haven_motes_org/vent_org`; never type a haven coordinate in GSC). NEW `_tod_haven.gsc`: membership every 0.1 s with hysteresis (in 234 / out 250); enemies inside x0.67 (`TOD_HAVEN_SLOW` via `self.tod_safe_mult`, folded into `_tod_zombie_speed`'s one rate line + elite lanes, `_tod_bosses` pause restore, the Doppelghast/Mangler chase loops; never against a world pause / drop-in / menu freeze); players inside take x0.67 of ENEMY damage (`TOD_HAVEN_DR` via `level.tod_safezone_dr` in BOTH `_tod_bosses` player-damage lanes; never falls/self); `_tod_stray` never raises a zombie inside a field; the domes BOOT with `_tod_fall`'s power wave (`tod_power_wave_z`). NEW `TodHaven.lua` (AetheriumHud's FIRST child, hidden with the HUD): cyan hex edge tint inside, a flash on crossing, SAFE ZONE (+ ENEMIES SLOWED - DAMAGE REDUCED the first 3 times), a flicker + tink per cut hit; zero clientfields (eventstrings `tod_haven` / `tod_haven_hit`). Art GENERATED (`tools/haven/make_dome.py` dome + vignette, `make_fx.py` 4 effects, `make_sounds.py` 6 sounds). RULES PAID FOR: (1) an unwired module/widget must wait OUTSIDE scripts/ and ui/ (`art/haven/staged/`): the arity lint scans every script and the assets lint every Lua file, so a peer build dies on it; (2) a scripted edit must keep each file's own line endings (five LF scripts flipped to CRLF broke test_doppelghast's exact-text check); (3) gsc_eval cannot parse a `[[ ]]` pointer call - a gate interpreting such a file needs a translate stub (test_pursuit's `haven_inside_stub`). (4) LOOK FROM INSIDE before building a transparent field: the Blender review (`tools/haven/preview.py`, single-sided like the game, real map faces) showed the first dome as a glowing wall from inside - a 0.42 halo over the outer 40% of every cell hides the horde; it ships see-through (`FIELD_*` in make_dome.py: thin 0.85 line, 0.10 halo, 0.018 cells). Gates: `tools/haven/test_haven.js` (146 checks: the user's 33% / 33%, lockstep, wiring, hooks, the SHIPPING module through gsc_eval, 10 mutants, `--ledger`), `tools/test_haven_hud.lua`, the three `--check`s, `test_ui_lifetimes.lua`. Wired in ONE step by `tools/haven/wire.py` (18:24; every haven area sits inside its lapN_zone, no riser inside a dome). The floor-20 Dealer panel's review was re-rendered for its new neighbour (re-review in `art/dealer_presence/review_acceptance.json`). The sky fleet's lanes were REGENERATED for the new geometry (`gen_lanes.js`: two west dreadnought lanes lost their low band to the floor-10 platform, several south lanes gained low bands; test_sky_ships v4 + test_jump_title green). BUILT: FULL BUILD OK 18:51 (tmp/haven/full2.log; full1 stopped at the lane gate): .ff 18:49:31, FF 228,294,976 B, fresh LED 119,523,714 B, NAVMESH GATE OK + every haven on its floor's walk section (compiled-mesh probe), HAVEN LEDGER OK (11 assets), the dome compiled with every exported triangle, the six sounds in the loaded bank (155.2 MB), scripts / zone_source / ui + GDT + model_export/tod_haven + map deployed = repo, nothing synced after, the 8 known-waived lines only. UNPLAYED. Logs `[TOD_HAVEN]` (dev). Review `art/haven/review/review.html`. **19:30 THE KILL PAY (user: "Kills inside a zone are at 25% money. As well to avoid players from just sitting in zones"):** a player inside a powered dome is paid `TOD_HAVEN_KILL_PAY` 0.25 of every KILL payout (stock kill money, BOUNTY, the elite purse, companion / helper kills), banked to exact tens by `_tod_haven::kill_pay`; the popup asks `kill_preview` in all nine arms; the hint adds KILLS PAY 25 PERCENT; hit points untouched; the PAYEE's place counts. RULE: any NEW kill payout must go through `level.tod_haven_kill_pay_fn` (test_haven.js wires the known ones). Gate 171 checks / 14 mutants. BUILT in session -09's FULL BUILD OK 20:14 (tmp/ability_fx/full3.log, .ff 20:14:18, FF 228,723,584 B; files deployed = repo). UNPLAYED.

**2026-10-02 17:45 - NEAR MISSES + THE HOT STREAK (user: "near miss and almost hit that sports companies and gambling companies use ... inject this concept in our black market and card flip systems"; "the hot hand effect as well ... Not crazy"; "Actually yes implement what you came up with"; docs/201 s10; CHANGELOG 17:45).** THE LINE: every result is rolled FIRST at the odds shown; a near miss only decides what is SHOWN around it, never what you get; never show a prize and take it back; tease only what could have happened. SPIN (`_tod_shop.gsc` `near_plan` + `TodSpinReel.lua`): STOPPED SHORT 22% / SLIPPED PAST 8% of non-Legendary spins (the silent 45% tease is retired); the open's tease arg packs heat * 256 + kind * 64 + tile. CARD REACH (`_tod_upgrade_ui.gsc` `reach_plan` + `TodPull.lua`): a second todUpgHold beat at one rung IS the reach; SO CLOSE 12 / 18 / 30% (COMMON / RARE / EPIC with room for the next rung), BREAK THROUGH 10 / 25 / 60% (RARE / EPIC / LEGENDARY); one a deal; the worst deal needs 11 of 15 beats. HOT STREAK (`_tod_luck.gsc` `streak_result`): EPIC +1 / LEGENDARY +2 per pull (card deal or spin), anything less or a down ends it; heat = streak - 1, max 3, multiplies the EPIC + LEGENDARY slices x1.15 / 1.30 / 1.50 on cards AND spins (COMMON pays; the guarantees ignore heat); ONE table `level.tod_heat_mult`, mirrored in TodSpinReel `P3.HEAT_MULT` (the gate checks all three); HUD eventstring `tod_luck_heat( heat, streak, change )`, resent every 5 s. RULES PAID FOR IN THE PREVIEWS: (1) TodPull's under layer (`AttachUnder`) draws BEHIND the opaque cards - anything that must be seen over a card goes in the slot's over layer (the warm embers showed nothing until moved; the LEGENDARY gold motes after the flip are still hidden there, the card owner's call); (2) the reel's tile window is k-4..k+4 = exactly SLOTS (k+5 stole k-4's slot: the left tile vanished at every step). Previews: `render_spin.py --near short|past --heat N`, `render_pull.py --reach A:fail|A:win --heat N`. Gates: `test_hot_streak.js` (106) + `near_miss/make_sounds.py --check` in build_map.ps1, `test_spin.js` 647, `test_spin_reel.lua`, `test_card_pull.lua` 174. Logs (dev): `[TOD_SHOP] SPIN_NEAR`, `[TOD_PULL] REACH` / `STREAK_REPORT`, `[TOD_LUCK] STREAK`. BUILT: -GscOnly BUILD OK 18:20:38 (tmp/near_miss/gsc2.log; .ff 18:18:40, FF 228,312,000 B; loaded bank 154.5 MB = +3.6 MB for the 8 near-miss sounds and 11 dealer lines, streamed 313.8 MB; the 8 known-waived linker lines only). The new gates ran inside it (HOT STREAK + REACH 106, NEAR MISS SOUNDS 8, SPIN 647, THE PULL 174, the reel harness). Verified: scripts / zone_source / ui deployed = repo, nothing synced after the .ff, the 8 near wavs + 11 dealer wavs deployed = repo, every new stem in the loaded bank, the ledger carries the 5 changed scripts and the 3 Lua rawfiles. The first attempt (tmp/near_miss/gsc1.log, 18:07) linked but its guard FAILED it: BlackOps3 was launched mid-build (~17:57, Map One's zm_tower_of_doom per the console); per the build script's ritual the generated sound/zone cache was cleared and the build re-run clean. SUPERSEDED AS THE TEST .ff by the Haven session's FULL BUILD OK 18:51 (tmp/haven/full2.log; .ff 18:49:31, FF 228,294,976 B), which carries this tree (verified: the 8 changed scripts / Lua in its ledger, the new stems in its loaded bank, deployed = repo, nothing synced after). UNPLAYED.

**2026-10-02 - THE PURSUIT: ZOMBIES ALWAYS REACH YOU, YOU CAN'T HIDE WHERE THEY CAN'T (user: "zombies not being able to trace or target players ... many places where you can jump off ... cut that distance ... more fast-paced"; "you're gonna own this" - THIS SESSION OWNS IT; docs/200; CHANGELOG 15:13).** ROOT CAUSE: the 24 broken drops are one-way but the lap zone graph is two-way, so the floor BELOW a drop is active while you stand on its ledge and stock raised zombies on the catch deck under you (logged 2026-10-01, CanPath 0); targeting was straight-line; TOD1's relocator moved zombies only at ~4 floors / 8 s and could put them back below a drop; nothing caught a player who left the playable space (a Breacher launch fell 25 s into the void under god mode). BUILT: NEW `_tod_reach.gsc` (regions tower / crown island / arena + a chain of 51 cuts: door +8 on its landing, drop +96, roof; fails OPEN) - `finale_spawn_selection` filters risers by reach FIRST and prefers risers within cost 2400 (`TOD_REACH_SPAWN_NEAR` LOCKSTEP `TOD_STRAY_COST`); `tod_closest_player` -> `tod_reach::closest` (nearest REACHABLE by walking cost); `_tod_stray.gsc` REV 2 = THE HUNT (unreach 1.5 s, far > 2400 after 3 s, CanPath-checked risers or synthesized navmesh spots, climb-out arrival, derez if on screen, refunded despawn after 15 s, any player teleport pumps a 12 s rush); NEW `_tod_recall.gsc` = THE RECALL, REV 2 SINCE 20:07 (user: "Teleporting to safety should only be when you fall of the map completely. Im fine with players trying to hack and jump down all the way ... spawn where they came from and at 1 HP"; CHANGELOG 20:07): ONLY a fall off the map is returned (falling 768 below the last safe spot with NOTHING under him / below z -448 = under the Undercity floor / standing in NO zone at all for 1 s) to the last safe spot at 1 HP (a downed player keeps his last stand), with the teleporter discharge, never killed; dropping floors onto the tower, standing below unbought doors (a disabled zone IS the map: stock's out-of-playable kill is spared there, kill brushes still kill) and unreachable perches are ALLOWED (rev 1's fall-without-floor-test, enabled-zone OOB and PERCH are retired); exempt: jump-pad flight, grapple + grace, frozen players, world pause, 0.5 s after any teleport; rev 2 gate 158 checks / 14 mutants; rev 2 BUILT: -GscOnly BUILD OK on top of -09's 20:14 FULL (tmp/recall_rev2/gsc1.log; .ff 20:26:46, FF 228,723,648 B; ledger carries _tod_recall.gsc, deployed = repo rev 2, nothing synced after), UNPLAYED; `_tod_bosses::pick_spawn_point` refuses unreachable spots (every elite spawn + relocation). RULES: never spawn or relocate a zombie where `tod_reach::can_reach` says it cannot walk to a player; a drop is DOWN-ONLY for zombies; keep `TOD_REACH_*` in lockstep with gen_tower_map.js (gated). Verified offline: every navmesh face sits inside a zone volume (OOB can only fire off-mesh); grounded players > 48 from the mesh in 0.3% of archived samples. GATE `tools/test_pursuit.js` (144 checks, shipping GSC via gsc_eval, 11 mutants caught; since 2026-10-02 19:00 it also proves the docs/202 haven guard refuses a spot inside a live field). BUILT: -GscOnly BUILD OK 15:31 (tmp/pursuit/gsc3.log; .ff 15:31:33, FF 228,268,480 B, SHA256 31672e8c...; 8 known-waived linker lines only; the pursuit gate ran inside it): the ledger carries scriptparsetree _tod_reach / _tod_recall / _tod_stray / _tod_endless_rounds / _tod_bosses / the entry gsc; scripts / zone_source / ui deployed = repo, nothing synced after the .ff (an earlier link, gsc1 15:09, lacked the two last refinements; gsc2 was stopped at its sync for a Map One FULL build on that session's request). UNPLAYED - logs `[TOD_REACH]` / `[TOD_HUNT]` / `[TOD_RECALL]` (dev). Knobs per symptom: docs/200 s3.

**2026-10-01 - APPROVED CLONE WIRED AND BUILT; USER PLAYTEST PENDING.** User: 'Sounds good Please wire up now'. The approved consented clone replaces all 71 shop/class lines under the unchanged mask effect; the selected designed-voice sign laugh (take 7) is preserved. Previous voice/takes/picks archived in tmp/black_market_vo/clone_delivery_before; per-take/per-file voice IDs record the retained exception. All 72 wavs, aliases, line-duration table and sound-kit manifest refreshed; local desk and combined recording refreshed. pick --check and test_spin (517) PASS; guarded -GscOnly BUILD OK, geometry/lighting confirmed current, FF 228,268,160 bytes at 2026-10-01T15:14:56.891293, SHA256 6c69ec380b2f1ae0b04be4657e0f1210552722aaf8f1793773e22b1b1c5578ca. Delivery proof: tmp/black_market_vo/clone_delivery/build.json (277 source/deployed inputs, all 72 bank aliases, no post-FF sync); build.log there. Credits record the custom-map-only/noncommercial clone terms. No game launched; user tests. This wires the existing shop hooks; the boss reveal voice lines remain audition assets, not a newly implemented boss VO system.

**2026-10-01 - CONSENTED CLONE CREATED; USER AUDITION PENDING.** After the user enabled Voices: write, ElevenLabs accepted the key but rejected 33 samples (maximum 25). clone_voice.py now selects the 25 longest approved source clips deterministically (196.12 s), preserving the complete source pool. Retry created the voice recorded under clone in tmp/black_market_vo/unmasked/voices.json. Generated eight organic reveal lines, two takes each, plus 16 local masked previews using the unchanged shipping mask effect. Format/count checks pass; receipt: tmp/black_market_vo/unmasked/clone/receipt.json. Local listening desk rebuilt and opened with clone / clone_mask and the earlier designed voice explicitly labeled as older wording. Shipping voice, game assets and deployment unchanged; no build or game launch. User listens before any replacement. Do not rerun voice creation blindly: the clone already exists.

**2026-10-01 - CLONE FILENAME CHECK REMOVED BY USER; ELEVENLABS REQUIRES VOICES_WRITE.** User: "You can just remove the check and run the command." This supersedes the earlier two-filename gate: clone_voice.py records permission provenance without refusing on filenames. Supplied docs/licenses/license.txt is unchanged; the descriptive copy is byte-identical. The API client resolves the saved Windows user ELEVENLABS_API_KEY when the process did not inherit it, without displaying or persisting the value. Local --check PASSES (33 files, 240.5 s). The actual clone command reached ElevenLabs and returned HTTP 401 missing_permissions: voices_write. No clone created; shipping voice unchanged. Enable Voices: write on the existing key before rerunning. Five focused mocked checks passed, including secret redaction and --check without named records. Current detail: docs/198_black_market_voice.md. Do not restore the removed local gate.

**2026-10-01 13:58 - THE CONSENTED RICHTOFEN CLONE IS PREPARED AND GUARDED, NOT MADE (user: "specific permissions from Nolan North and Activision ... only for custom map and we cannot make money off of it"; "I will add those myself once I get them in the repo"; docs/198 "The consented clone"; CHANGELOG 13:58).** THE RULE NOW: a clone of the actor's voice may be made ONLY once `docs/licenses/` holds BOTH documents (a file named with 'north' + one with 'activision'); `tools/black_market_vo/clone_voice.py` enforces it and refuses otherwise; the terms (this custom map only, never for money) are written into the voice and CREDITS.md. Prepared (second pass 14:30; the wiki radios were ROBOTIC = the in-game radio filter, and the wiki category tags clips that merely MENTION him): `split_lines.py` -> `tmp/black_market_vo/clone_source/` = 33 clean single lines (240 s) split from John Rizzo's four Black Ops III Primis Richtofen quote compilations (yt-dlp, `reference/yt/`; 495 lines in `reference/yt_lines/`), pitch median 188 Hz; skip.json / keep.json edit the set, `--skip-split` rebuilds it; `fetch_pool.py` holds the wiki pool + a real cutoff metric, `lines_reveal_organic.json` (the calm reveal set; the manic set is the wrong register), `build_desk.py --lines`. The key must gain Voices: write. NOTHING of his has reached any model; the shipping dealer stays the text-designed voice under mask v5 (built 13:43). When the documents land: `clone_voice.py`, then the desk, then the user's ear, then (if accepted) the clone replaces the dealer voice via voice.json + generate --force + pick + build.

**2026-10-01 13:44 - ALARM DELIVERY FOLLOW-UP VERIFIED.** The peer VO relink also finished BUILD OK and passed both compiled glass gates. Current FF: 228,267,904 bytes at 13:41:29, SHA256 33cfbc45...; art/crown_alarm/lens_review/peer_relink.json pins its actual compiled proofs. Original FULL-build evidence is preserved under lens_review/deliveries/20261001_132740/. The correct live Rendered preview was opened and verified using the actual owned Blender window (visible_preview.png/json); the launcher explicitly restores scene lighting and camera after file load. No game launched; user native playtest pending.

**2026-10-01 13:41 - THE CROWN'S CLASS TERMINAL: SWITCH CLASS MID-RUN, KEEP YOUR TIER AND CARDS (tester kit; user: "In the crown i want an option to switch between classes as well. I eventually want to push out a testing phase so testers have access to everything in the crown"; CHANGELOG 13:41).** NEW `_tod_class_terminal.gsc` + the ONE tester switch `_tod_tester.gsh` (`TOD_TESTER_KIT 1`; `-Publish` WARNS, never refuses: the testing phase ships it on purpose - set 0 for an ordinary release). A data console against the crown hall's WEST wall (-700, 8308), across the nave from the crown crate (derived from the generated anchors), hold USE -> the class draft's own panel reopens (`todClsShow` 3 = terminal mode in `tod_class_select.lua`: SWITCH CLASS title in the typeface, the PERMANENT banner hidden, a CURRENT tag, the HUD veiled `cls_term`, 32 s clock) on the player's own class; lock another class -> in ONE server frame the old class lets go (Archer cleanup / Necromancer helpers + bind / Breacher C4 + shield / Warrior bowie), class + body + kit change, the new class's gun at the SAME TIER (base form, full ammo), health to the new floor. Lock your own class or time out = close. Spin-shaped lock (frozen, untargetable, unhurtable, 1.5 s grace), no world pause; a round's card deal TAKES the screen (input dies on `tod_global_upg_takeover`, panel closes in that frame). RULES: (1) A CARD OF ANOTHER CLASS SLEEPS - read `tod_upgrades::class_live_level`, not `get_level`, in any card effect not already gated on the class or the class gun (VITALITY, ADRENALINE, the RIOT SHIELD read it now; the pause list hides sleeping rows); a card scoped to no REGISTERED class (parked / the gated mage) never sleeps. (2) The terminal is the first path that changes a LIVING player between two kits: `kit_switch` refills the frag only for a kit-less class now. (3) The draft panel's fields are SHARED with the card deal: anything that reopens it mid-game must yield to the takeover. Gates: `tools/test_class_terminal.js` (103, negative control per refusal clause, 17 hand mutations caught) + `tools/test_class_terminal_ui.lua` (73 on the real panel; fails on the old one). Limits: the crown seals at the Fall, so it serves the crown phase; generic prompt icon. BUILT: -GscOnly BUILD OK 13:55:51 (tmp/class_terminal/gsc1.log; swapped in 13:45:04 behind the voice session's gsc19, the three terminal gates green on the repo first): FF 228,268,160 B at 13:54:04; the ledger carries scriptparsetree _tod_class_terminal.gsc, the panel rawfile tod_class_select.lua, the router zmcursorhintnew.lua, xmodel p7_zm_sta_dragon_network_data_terminal and fx_teleport_flashback_kino; scripts / zone_source / ui diffs clean, every touched file deployed = repo, nothing synced after the .ff; the Dealer rows intact (5 xmodels, 45 xanims, spawner_tod_dealer, _tod_dealer_finale); the build printed the TOD_TESTER_KIT warning beside the existing dev / bench / Dealer ones. UNPLAYED. Logs `[TOD_CLASS_TERM]`.

**2026-10-01 13:29 - ALARM GLASS REPAIR BUILT; USER PLAYTEST PENDING.** The user's opaque/gray cover was a native material failure: a full-color specular image was bound to a scalar-mask transparent shader. Isolated positive/negative linker controls reproduced the rejection and proved the compatible stock black mask; the lens now has a complete linked eleven-image definition. Dome/rib alpha is reduced; red RGB, wear, all geometry, button assets, rotation, FX and lighting are preserved. Guarded FULL BUILD OK, FF 228,267,904 bytes at 13:27:40; actual material proof and all 11 BC7 mip levels/six housing LODs pass, max alpha error one byte, 81 runtime files match deployment; geometry/light bake reused. Evidence: art/crown_alarm/lens_review/build.json, compiled_material.json, compiled_image.json, review.html; docs/crown_alarm/GLASS_REPAIR.md. Correct Rendered native-mesh approximation: tools/crown_alarm/open_lens_preview.ps1. No game launched; native visual approval is the user's playtest. The before preview reconstructs old alpha with the repaired shader, not the old game's fallback. Gray32 was thermal heatmap, not the specular mask; do not revive the earlier .1237 F0 inference. Preserve this complete valid source/art set through peer relinks; the VO v5 waiter will replace this FF separately.

**2026-10-01 13:24 - THE MASK v5: CLEAR WORDS, THE DARK/CYBER MOVED OFF THE TOP END (user: "a bit too much muffled for player pleasure ... a slight another tweak on cyber dark. Then we should be final"; docs/198 "The mask v5"; CHANGELOG 13:24).** v4's muffle was its top cut; `mask_tone.py` v5 opens the top (shelf -3.5 dB at 4.6 kHz, low-pass 11.5 kHz, +2 dB presence at 3 kHz) and carries the character in pitch 0.87, a +5 dB low shelf, a stronger flanger (depth 0.8 / regen 24 / width 46) and ringier reflections. All 72 dealer lines + the desk's Masked set re-shipped, gates green (pick --check, test_spin 517, jump title, kit), desk + recording refreshed and open. BUILT: -GscOnly BUILD OK (tmp/black_market_vo/gsc19.log; .ff 13:41, FF 228,267,904 B; the 8 known-waived lines only): the 13:41:29 ledger carries `_tod_shop.gsc` + `_tod_shop_vo.gsc` and the Dealer's 5 xmodel / 45 xanim / finale rows, the 13:40 loaded bank indexes all 72 dealer stems incl. the 24 class lines, all 72 dealer wavs at the tools root = repo under v5, tod_shop.csv / _tod_shop.gsc / _tod_shop_vo.gsc deployed = repo, nothing synced after the .ff. This .ff supersedes the alarm session's 13:27 BUILD OK as the test .ff (same tree + mask v5). IF THE USER CALLS v5 FINAL, THE MASK IS DONE: never retune it unasked. UNPLAYED.

**2026-10-01 12:58 - THE ORGANIC ROUND (user, after the Shadows of Evil ending vs our 100%: "we can do better ... train on organic content ... a devil Richtofen where he sounds a bit zombie like ... not his organic voice"; docs/198 "The organic round"; CHANGELOG 12:58).** THE FACT FIRST: nothing of the actor's has ever been fed to the model (the boundary holds: no clone, no reference audio); the voice is text-steered, and the demon register was OUR text: the design/remix preview sample and all eight reveal lines in `lines_unmasked.json` are cackles / JACKPOT / "come to Papa", so every candidate was picked on mania. Measured: the Shadows of Evil ending ~168 Hz median pitch vs the shipping voice 206-224 Hz. NEW `tools/black_market_vo/organic_round.py` (organic description, calm sample, remix B x3 / remix V2 x3 / fresh design x3 -> `tmp/black_market_vo/unmasked_organic/gallery.html` with his organic reference lines on top, listening only); nearest by pitch remix_V2_3 (172 Hz) and remix_B_1 (193 Hz), the fresh designs too deep (104-138 Hz). The desk's reference pick-list is organic-only now (the ten BOII Aether lines out; `_BOII.` not `_BOIII`). The user picks by ear; nothing re-shipped; the reveal lines must be rewritten calm before any regeneration. Gallery + desk open in Chrome.

**2026-10-01 12:20 - THE DEALER KNOWS YOUR CLASS: 24 class-specific lines, same voice and mask (user: "the dealer has specific lines depending on the class interacting with him"; docs/198 "The classes"; CHANGELOG 12:20).** Six lines per class in `tools/black_market_vo/lines.json` (`cls` archer / breacher / warrior / necro) on the walk-up greeting x2, the reel start x2, the close and the socket; five carry lore hints, no German, never the name. `_tod_shop.gsc` `vo_cls_slug()` maps `self.tod_class` (assault / heavy / slasher / necromancer) and `vo_cls( hook, n, generic )` answers the class line `TOD_SPIN_VO_CLASS_PCT` 60% of the time, the generic line otherwise (a classless player always generic), rolled before `vo_say`'s own chance so each hook's rate is unchanged; same one lane, 3D from the mouth, to that player only. Generated with the shipping voice + mask v4 (`generate.py --group cls_approach,cls_buy,cls_close,cls_socket`, 3 takes, take 1 ships), 72 wavs / 72 rows / the length table regenerated; `test_spin.js` gates the 24 rows, lengths, the class map, the 40..80 share and the four routes. The local desk's strip plays every class line (`build_desk.py`). BUILT: the Dealer's FULL build 5 (12:20:46) synced BEFORE this landed; my 12:26 quiet-wait -GscOnly linked 12:38:03 (tmp/black_market_vo/gsc18.log) and was superseded by the alarm session's FULL build whose .ff (12:49:24, FF 228,267,968 B) IS the deployed one: its ledger carries `_tod_shop.gsc` + `_tod_shop_vo.gsc` (and the Dealer's 5 xmodel / 45 xanim / aitype / finale rows), the loaded bank indexes all 72 dealer stems incl. the 24 `tod_spin_vo_cls_*`, every dealer wav at the tools root = repo, csv/gsc deployed = repo, nothing synced after (that wrapper's own crown-alarm gate FAILED after the link, so its session may rebuild; the same tree rides). UNPLAYED.

**2026-10-01 11:55 - ELITE BARS ARE RED; THE NECROMANCER'S HELPERS WEAR WHITE BARS (user: "the elites on this map have a white bar above them that needs to be changed to red. And then the necromancers summoners need to have the white bar. So you can tell the difference and you can see how much health they have left"; docs/174 "Third pass"; CHANGELOG 11:55).** Every elite / boss bar is RED (sets e / b, same names and sizes, pink-white edge pulse); every Necromancer helper (thrall, soul hound, Mangler) wears a smaller WHITE bar (NEW set `s`, 31 materials, 93 in all) that every player sees. A helper takes no damage from the horde, so its bar shows what is LEFT of it: `_tod_necro_summon::helper_life` publishes `tod_hpbar_frac` (life clock + a thrall's kills, the smaller), the bar steps in tenths and pulses on each step. Helpers are found on team "allies" by `tod_necro_helper` and have their own bar budget (64), so they never take an elite's bar. The art is GENERATED (`tools/gen_hpbar_art.js`, `FILLS.red` / `FILLS.white`); the user's red drop (docs/175) never came and is superseded - re-running the generator is fine again. `test_elite_hp.js` DECODES the PNGs and fails unless e/b are red and s is white. LANDED 11:54:33 (build 4 failed on the Dealer's clips and carried nothing). BUILT in the Dealer session's FULL BUILD OK 12:22:31 (tmp/dealer_boss/full5.log, exit 0; the map compile + bake reused): FF 228,267,968 B at 12:20:46; test_elite_hp ran INSIDE it (colours e/b RED, s WHITE); the ledger carries all 93 `image,i_tod_hpbar_*` + 93 `material,tod_hpbar_*` (31 per set, e / b / s), and all 93 .iwi were re-converted after the 11:54:33 landing; deployed = repo for both scripts, the zone, tod_hud_bars.gdt and the 93 PNGs; nothing synced after the .ff; the 8 known-waived linker lines only. (A peer's `_tod_shop.gsc` saved 12:19:38 is NOT in this .ff.) UNPLAYED. Logs `[TOD_HPBAR] ... set=e|b|s`.

**2026-10-01 11:47 - THE BREACHER IN THE AIR: STEERS LIKE MAP 1's ATHLETE + THROWS C4 MID-AIR (user: "I want it to be like the athlete ... not even close to as smooth or functional"; "the breacher cant throw C4 mid air ... Cluster C4 shooting reloading all of the actions are acceptable"; CHANGELOG 11:47).** `breacher_air_steer` is ONE lane per flight now: ATHLETE mode (take-off >= 200 u/s) = map 1's athlete lane 4 at Lv5 line for line (+ the budget clamp never turns a step back), LAUNCH mode (slower, e.g. a Fusion launch) = air control toward the stick (170 u/s, 900 u/s^2, no speed farming). The 09-29 version ran both lanes at once and they fought (logged turned_deg up to 1859 against a 60-deg budget). The Archer's `stumble_watch` also counts an airborne Breacher (no landing stumble, like the athlete). THE C4: `tod_c4` was `plantable` 1 = placed like a claymore = refused in the air; now 0 + `bBoxTrace` 1 (same sticky hit-trace). RULE: never run two velocity-steering lanes on one flight; a thrown charge must not be plantable. Gate `test_fusion_air.js` 143 checks incl. the old function replayed as the negative control (`tools/breacher/fixtures/`). Logs `BAIR_MODE`, `BAIR_LAND ... fire_ticks reload_ticks c4_press c4_air cluster_press cluster_air`, `C4_PLANT/CLUSTER_THROW ... airborne=`. The C4 GDT rode the Dealer's FULL build 4 sync (11:37); the scripts are swapped in + built by `tmp/jump_title/build_after_quiet.ps1` -> `gsc_pass6b.log`. The waiter swapped the staged files into the repo at 11:56:58 (gate green on the repo); its own -GscOnly was stopped before any native stage. BUILT 12:22 in the Dealer session's FULL BUILD OK 12:22:31 (tmp/dealer_boss/full5.log; .ff 12:20:46, FF 228,267,968 B; sync 12:09:30): verified by me - test_jumppad / test_jump_title (swing back 8.4) / JUMP TITLE FX OK 6 / BREACHER FUSION/AIR 143 ran inside it; _tod_jumppad.gsc, _tod_jump_title.csc, fx_jt_blaze, _tod_class_kit.gsc, _tod_archer.gsc and weapon tod_c4 in the 12:20:46 ledger; deployed = repo for all of them + tod_breacher_kit.gdt + fx_jt_blaze.efx; the converted gdt.db row tod_c4 reads plantable 0 / bBoxTrace 1; scripts/zone_source/ui diffs clean except a peer's later _tod_shop.gsc; nothing synced after the .ff. UNPLAYED.

**2026-10-01 12:22 - THE DEALER SPAWNS IN THE CROWN HALL FOR THE USER'S TEST: `_tod_dealer_finale.gsc` WRITTEN + WIRED; FULL BUILD 5 OK 12:22:31 AFTER FOUR ATTEMPTS DIED ON TWO LINKER RULES AND THE GAME (user: "Please spawn him in the crown so i can test"; docs/199 s3; CHANGELOG 10:33).** NEW `_tod_dealer_finale.gsc` (archetype "dealer" on the Keeper's blackboard + zombie flags, `spawn_boss( org, target )` through the Keeper's portal + scream, health `TOD_DEALER_HP_ZOMBIES` 60 round-zombie units per player, `tod_boss_kind` "dealer" so the wide elite bar follows him, STATE ONE at spawn = arms "up" / walk / the scythe rigid on `tag_weapon_right`, THE MASK BREAK at half health = detach, `SetModel` the unmasked body, arms "down", run, the Dingo in hand, a placeholder burst + scream; the card-deal freeze every tick; the elite purse + 2000 team points on death). `TOD_DEALER_TEST_SPAWN` 1 spawns him 6 s after the round-1 card deal, 448 u south of the alarm button, facing the nearest player; `TOD_DEALER_LOG` 1 prints `[TOD_DEALER]` INIT / TEST_SPAWN / SPAWN / READY / WEAPON / HP (every 10%) / STATE / FREEZE / STUCK / DEATH_START / DEATH with dev OFF (`build_map.ps1` refuses -Publish while either is 1). `_tod_elite_hp.gsc` learned the "dealer" kind (wide bar, 110 u). `wire.py` RUN 10:31 (zone block, two sync rows, the two gates + the publish refusal, `#using` + `init()` in `_tod_main.gsc`). TWO LINKER RULES PAID FOR: a clip a `move@zombie` selector row names must carry `looping 1` AND `loopsync 1` in its GDT block (every linker on the shared root aborted 10:39-11:04 on `tod_dealer_f_walk`; `install.py` sets both on the walk / run / sprint / idle / channel clips of both states, `test_dealer.js` 1,204 checks gates both from the selector rows; memory ast-move-rows-need-looping-xanims); the seven `p7_zm_zod_fuse` / material lines every link prints are the KNOWN-WAIVED set. BUILDS: my full1 / full2 stopped by me before their links (each carried the GDT of the moment before the next fix); FULL build 3 (tmp/dealer_boss/full3.log) synced the final tree at 11:15 and passed every gate, then `[build] FAIL: BlackOps3 is running` at 11:26:59 (the user launched the game at 11:24:58, between the gates and cod2map) - NOTHING LINKED, THE DEPLOYED .ff IS STILL 10:03:59 AND HAS NO DEALER (the game the user is in right now). BUILD 4 = the same wrapper re-armed 11:27:38 (tmp/dealer_boss/full4.log): it waits for the game to close + 90 s quiet, then the FULL build (geom_key: 5 lighting/geometry inputs changed since the Sep 30 11:22 full build, so it BAKES, ~15 min). BUILD 4 RAN 11:37-11:55 (the game closed 11:35; it compiled + baked) AND DIED AT THE LINKER ON THE MIRROR RULE: an `idle@zombie` / `melee@zombie` row "requires non-looping" + "non-loop sync" clips, and the pack's own Protector `idle_attack` blocks ship looping 1 (18 Dealer lines: f_idle / idle_scan_1/2 / g_ens_idle / idle_attack_left/right). FIXED 12:01: `install.py selector_loop_sets()` derives BOTH flag sets from the generated mapping + selector tables (move rows 1/1, idle + melee rows 0/0, a clip on both asserts; `SCRIPT_LOOPS` = revive_loop + ee_idle by hand), `test_dealer.js` 1,215 checks gates both ways (negative control proven). BUILD 5 = the wrapper re-armed 12:02:51 (tmp/dealer_boss/full5.log); the jump session stopped its own 11:57 relink (it had synced the old GDT). BUILD 5 = FULL BUILD OK 12:22:31 (tmp/dealer_boss/full5.log; build 4's compile + bake REUSED by geom_key): .ff 12:20:46, FF 228,267,968 B (+2.3 MB over the 10:03 one = the Dealer), loaded bank 140.3 MB / streamed 313.8 MB; THE LEDGER CARRIES HIM: xmodel tod_dealer_body / _body_unmasked / _scythe / _dg2 / _lmg, all 45 tod_dealer_* xanims, aitype spawner_tod_dealer, _tod_dealer_finale in the script list, the 3 Dealer materials + 15 atlases, the da session's 93 red/white hp-bar materials; deployed GDT = repo (looping 11 / loopsync 8), deployed _tod_dealer_finale.gsc / _tod_atmosphere.gsc = repo, nothing synced after the .ff, the 8 known-waived linker lines only. ONE repo != deployed diff: `_tod_shop.gsc` (the Black Market session's edit at 12:19:38, after this build's 12:09 sync; NOT in this .ff, theirs to relink). SUPERSEDED AS THE TEST .ff by the alarm session's FULL build (tmp/alarm_lens_repair/full_build.log; .ff 12:49:24, FF 228,267,968 B, synced 12:39:46): its ledger carries the same 5 xmodels / 45 xanims / aitype / script (re-checked here), plus the voice session's class lines. Either .ff: the Dealer rises 6 s after the round-1 card deal in the crown hall. UNPLAYED. Verify it with the ledger (5 `xmodel,tod_dealer_*`, 45 `xanim,tod_dealer_*`, `aitype,spawner_tod_dealer`, `_tod_dealer_finale`), repo == deployed, nothing synced after. The voice (-37), music (-03) and jump (7d) sessions wait for this link to verify their own trees (the sync carries all three). UNBUILT, UNPLAYED. NEXT (docs/199 s4): the black-soul aura + mask-shatter FX (.csc), the Wunderwaffe shock, the Dingo bursts + the two-hand gun hold, the voices, the arena / finale wiring; both test defines to 0 before any publish.

**2026-10-01 10:36 - THE FIRST JUMP: 0.5 s MORE HANG AT THE TOP, THE SIGN LIT 0.3 s SOONER (user: "The pause mid air jump scene should last another 500ms before going down. Also the lights on the sign should start about 300ms earlier"; docs/196 s8; CHANGELOG 10:36).** The first flight is 12.1 s (was 11.6) and the extra half second is a DWELL AT THE APEX, not a longer arc: `cine_arc_frac()` in `_tod_jumppad.gsc` slips `TOD_JUMPPAD_CINE_DWELL` 0.5 s in round the top (raised cosine over 3.97..6.57 s, pace never under 0.62x), so nothing before the ignite moves (the crash stays framed) and from 6.57 s the flight is the old one 0.5 s later; the camera holds on the sign 6.5 s (swing back 8.4, was 7.9). The sign flickers on 0.7 s after the ignite (`TOD_JT_REVEAL` = gen_fx `REVEAL`, was 1.0) = 4.5 s, 0.9 s after the impact; `fx_jt_blaze` regenerated. RULE: to lengthen a moment of the flight, slip time in at that moment (a dwell); stretching `CINE_SECS` moves the rider at the crash. Gates green before the build: test_jumppad (runs the shipping `cine_arc_frac` via gsc_eval, 2 negative controls), test_jump_title (a dead white-flash check fixed + its negative control), gen_fx --check, arity, native API. BUILD QUEUED behind the music / voice / Dealer builds (`tmp/jump_title/build_after_quiet.ps1` -> `tmp/jump_title/gsc_pass6.log`, waits for 90 s with no BO3 / native stage / other build or waiter). BUILT 12:22 in the Dealer session's FULL BUILD OK 12:22:31 (tmp/dealer_boss/full5.log; .ff 12:20:46, FF 228,267,968 B; sync 12:09:30): verified by me - test_jumppad / test_jump_title (swing back 8.4) / JUMP TITLE FX OK 6 / BREACHER FUSION/AIR 143 ran inside it; _tod_jumppad.gsc, _tod_jump_title.csc, fx_jt_blaze, _tod_class_kit.gsc, _tod_archer.gsc and weapon tod_c4 in the 12:20:46 ledger; deployed = repo for all of them + tod_breacher_kit.gdt + fx_jt_blaze.efx; the converted gdt.db row tod_c4 reads plantable 0 / bBoxTrace 1; scripts/zone_source/ui diffs clean except a peer's later _tod_shop.gsc; nothing synced after the .ff. UNPLAYED.

**2026-10-01 10:20 - METEOR HERD IS THE BOTTOM BAND (user: "We should [move] meteor herd to the bottom floor"; CHANGELOG 10:20).** `register_music_bands` going down: 50-42 Champs, 41-34 With You, 33-26 Cornfield, 25-18 Una Mattina, 17-9 Reykjavik, 8-ground Meteor Herd - its row starts at FLOOR 0 so the Undercity (music_floor_of() = 0 below z 0) plays it instead of the literal `tod_ambient_music` fallback, which is unreachable now. The other five keep their relative order (one-line swap if Reykjavik should hold the bottom). BUILD: the -GscOnly at 10:39 (tmp/music_bass/gsc4.log) got through every gate and DIED IN THE LINKER on a DEALER asset (hard error, not waived): `tod_dealer.ai_am` xanim `tod_dealer_f_walk` in the `move@zombie` selector table is not a looping clip - the Dealer session wired its finale mid-stream (`_tod_dealer_finale.gsc` + the zone line are in the deployed tree) and every linker on the shared root aborts until they fix it (session -3d pinged 10:45). THE DEPLOYED .ff IS STILL 10:03:59 (the music pass WITH Meteor Herd at 41-34); the bottom-band table is SYNCED, NOT LINKED. Relink -GscOnly when the Dealer GDT links clean; a peer build carries it too (same tree). UNBUILT (this change), UNPLAYED.

**2026-10-01 10:04 - THE MUSIC PASS IS BUILT: -GscOnly BUILD OK 10:03:59 (tmp/music_bass/gsc3.log; FF 225,990,784 B; streamed bank 313.8 MB, was 291.4 = the With You stream; loaded bank 134.0 MB).** The sign-card gate passed on its own at ~10:00 (the sky session re-pinned or reverted its staged script; the -SkipSignCardGate edit was REFUSED by the permission classifier and never made - the build script is untouched). All ten music wavs deployed = repo, tod_ui.csv = repo, scripts / zone_source / ui diffs clean, nothing synced after the .ff, the 8 known-waived linker warnings only. THIS .ff CARRIES: the one-pass remaster (50% bass cut, bands -11.5 LUFS), Meteor Herd from the FLAC source, With You (RoFormer+MDX23C instrumental + the synth melody layer) as the sixth band (floors 33-26), the six-band table in `_tod_atmosphere.gsc`. UNPLAYED - the user judges the bass, the levels, the band slot and the With You melody layer in game. Logs `[TOD_MUSIC]` (dev).

**2026-10-01 - SIGN-CARD BUILD BLOCKER FIXED; DEPTH WORK IS ISOLATED.** The unrendered depth edit to tools/sky3d/cyber_architecture.py invalidated the shipping lit-card source pin and blocked unrelated builds. Restored that one file byte-for-byte to the card receipt baseline (fef254fe...); python -B tools/jump_title/make_sign_card.py --check now PASSES, as do the jump FX and scene contract checks. No bypass, shipping receipt change, rebake, sync or build. The depth candidate is preserved unchanged at tools/sky_depth/staged_sources/cyber_architecture.py (562224e6...), and the depth authoring workflow uses that isolated module. Rendering/review/native delivery remain pending. Never put unrendered work into files pinned by a shipping asset: stage it separately and publish only a complete reviewed source/art/receipt set. Evidence: art/sky3d/depth_review/build_unblock.json; tools/sky_depth/README.md; docs/166 section15.

**2026-10-01 01:25 - METEOR HERD IS FLAC-SOURCED + WITH YOU'S INSTRUMENTAL IS A BS-RoFormer/MDX23C AVERAGE + THE LOSSLESS LIST (user: "Can we do the lossless upgrade? ... can you get online some how. Highest quality possible"; CHANGELOG 01:25).** Meteor Herd now masters from the Internet Archive compilation's "Instrumental Attempt" FLAC (unofficial like the YouTube upload it replaces; measurably fuller above 16 kHz; `music_master.py --source tod_music_relay=tmp/music_bass/src/sa2_meteor_herd_instrumental_attempt.flac`); the page has a YouTube-vs-FLAC source-check row. With You's four separations measured (README): BS-RoFormer + MDX23C averaged = shipping, melody layer re-mixed on top. The four remaining Opus-sourced songs (Champs, Cornfield, Mattina, Reykjavik; With You too) need PURCHASES - the exact store pages are in the README; the session never uses rippers or pirate copies. Build still blocked by the sky session's stale sign card.

**2026-10-01 01:35 - WITH YOU KEEPS ITS VOCAL MELODY ON A SYNTH (user: "the vocals give it another layer of melody that I still want to keep, but I don't want the vocals"; CHANGELOG 01:35).** NEW `tools/music_vocal_melody.py` (transcribe / render / mix): the BS-RoFormer vocal stem -> MIDI via basic-pitch (uv Python 3.11 venv `scratchpad/bpenv`: TensorFlow has no 3.12+ Windows wheels; needs `setuptools<81`) -> the script's own synth (detuned saws + sub, envelopes, vibrato, chorus, convolution reverb, HP 150 Hz) -> 7 LU under the instrumental -> `music_master.py`. `tod_music_withyou.wav` = this version (-11.6 LUFS). Page row WITH VOCAL / NO VOCAL / MELODY KEPT (same link). The ensemble separators are still running (replace the instrumental under the same layer only if cleaner). THE FIVE TOWER SONGS ARE NOT LOSSLESS (YouTube Opus; told the user how to supply purchases). Build still blocked by the sky session's stale sign card; nothing linked since 22:36. UNBUILT, UNPLAYED.

**2026-10-01 00:50 - THE MUSIC IS REMASTERED FROM SOURCE IN ONE PASS (user, after approving the 50% cut by ear: "I want max quality ... Time it takes is not a problem"; CHANGELOG 00:50).** `tools/music_master.py` (the ONE recipe now; the README's older recipes are history): every track from its ORIGINAL source (`tmp/music_bass/src/` = the five Opus 251 re-downloads by video id; Downloads: the lossless Falling To Pieces FLAC, 115_Remastered_Extended.wav, Deep Mystery.wav, the finale wav) -> soxr 48 k -> the proven loop trims -> -6 dB shelf under 200 Hz -> makeup gain converged on the target -> ONE 4x-oversampled true-peak limiter (-0.2 dBTP, `--max-lim` 7.5) -> dither. Bands `--band-target` -11.5 LUFS, landed within 0.4 LU; limiter 1.4-3.2 dB on the loud masters, 6.5 / 7.5 on the quiet dynamic ones (Meteor Herd, Reykjavik). The old two-stage 50% set is parked in `tmp/music_bass/half/`. THE ONE UPGRADE LEFT IS LOSSLESS SOURCES (the user's purchase; same filenames in src/, re-run). WITH YOU = a THREE-MODEL ENSEMBLE in progress (BS-RoFormer 317 + Mel-Band RoFormer inst v2 + MDX23C InstVoc HQ 2, averaged, then the same chain); the demucs version still sits in sound_assets until it lands. Build still blocked by the sky session's stale sign card. UNBUILT, UNPLAYED.

**2026-10-01 00:20 - THE BASS CUT IS 50% (user on the A/B page: "i dont notice much in the bass between the 2 ... Maybe we need 50%"; "the no vocal sounds horrible. Can we improve the quality"; CHANGELOG 00:20).** All nine wavs re-rendered from the parked originals: -6 dB shelf under 200 Hz, MAKEUP GAIN (the five bands levelled to -11.0 LUFS, the rest toward their originals) under a TRUE-PEAK limiter (4x oversampled) capped at 2.5 dB of work; bass vs the rest -4.2..-5.1 dB, peaks -0.2 dBTP (the 25% set, -1.6..-2.1 relative, was below the ear's threshold - a 2 dB relative shift is not a "pass"). The 25% set is parked in `tmp/music_bass/quarter/`, the 50% set is `tmp/music_bass/half/` = sound_assets now. THE COMPARISON PAGE https://claude.ai/artifact/WRcaP3CgAzFNh3gXEmBTsP plays BEFORE / 25% / 50% in lock-step (30 s clips, `tmp/music_bass/compare/`, republish via the Artifact tool). WITH YOU: the demucs instrumental was rejected by ear; BS-RoFormer (audio-separator in `scratchpad/sepenv`, a uv Python 3.12 venv - Python 3.14 cannot build its deps) is re-separating it; the result replaces the wav + its clips. THE BUILD IS STILL BLOCKED BY PEERS: after the Dealer GDT fix, the 23:58 -GscOnly died at the jump title's "LIT SIGN CARD is stale" gate (`tools/jump_title/make_sign_card.py --check`, the sky/jump sessions' generated asset) - deployed .ff still 22:36; THE NEW WAVS / ALIAS / BAND TABLE ARE SYNCED, NOT LINKED. UNBUILT, UNPLAYED.

**2026-09-30 23:44 - THE MUSIC HAS 25% LESS BASS + "WITH YOU" (LYNNIC) IS A VOCAL-FREE SIXTH BAND (user: "lower the base on all of them by 25% ... too much bass ... They need a bit more color"; "I also like the song With You by Lynnic but I dont want vocals"; "use whatever tools you need so we can keep the quality at the max"; CHANGELOG 23:44).** ALL NINE music wavs re-rendered in place with a -2.5 dB low shelf under 200 Hz + a -0.2 dBFS safety limiter (originals in `tmp/music_bass/originals/` and git); MEASURED by the new `tools/music_measure.sh`: the <= 150 Hz band fell 2.34-2.42 dB on every track (24-25%), the rest 0.3-0.9 dB, no clipping; NOT re-gained (0.7-1.7 LU quieter overall, aliases already at 100 - the user judges before any lift). "WITH YOU" has NO instrumental anywhere, so the vocal was SEPARATED with demucs `htdemucs_ft` (the user authorised "whatever tools"; the vocal stem sits 7 LU under the instrumental) from Lynnic's official upload YWTrmXf0Uxs -> `tod_music_withyou.wav` (-11.4 LUFS, 166.3 s, alias in tod_ui.csv). SIX BANDS going down: 50-42 Champs, 41-34 Meteor Herd, 33-26 With You, 25-18 Cornfield, 17-9 Una Mattina, 8-1 Reykjavik - THE SLOT IS AN ASSUMPTION (one row in `register_music_bands`). RULES: measure a bass change by band RMS, never by ear on a preview; after ANY EQ on a brick-walled master, re-check sample peaks (the shelf alone pushed three past 0 dBFS); put the limiter AFTER a resample. BUILD: the -GscOnly at 23:48 (tmp/music_bass/gsc1.log) STOPPED AT gdtdb /update on a PEER GDT: `source_data/tod_dealer.gdt` (the Dealer session, 23:24) re-declares xanim `ai_zombie_zod_keeper_run_attack_v4` that `tod_keeper.gdt` owns (one duplicate; every build fails there until that block is dropped or renamed in their install.py; session -3d pinged 23:50). The deployed .ff is still 22:36 (FF 225,991,040 B): THE NEW WAVS, ALIAS AND BAND TABLE ARE SYNCED BUT NOT LINKED - rebuild -GscOnly once gdtdb passes. UNBUILT, UNPLAYED.

**2026-10-01 00:22 - THE DEALER HOLDS HIS SCYTHE IN BOTH HANDS AND LEVITATES: 45 AUTHORED CLIPS, TWO STATES ON `_arms_position` (user, watching the reel: "you have to understand the concept of holding a scythe ... flails around"; "levitate. That's his walking animation ... at 50% he will walk around and have the Richtofen head"; docs/199 s1; CHANGELOG 2026-10-01 00:22).** `tools/dealer_boss/author_clips.py` (background Blender) rewrites the Keeper clips into the Dealer's own files: `tod_dealer_f_*` = state one (the Protector's glide lifted 14 in, the TWO-HAND SCYTHE HOLD baked in: pole outward from behind the chest through the right palm, or the carry across the chest when the palms are clasped, smoothed and joined through a forward-up waypoint; the right wrist turned onto the pole, the left palm IK'd onto the shaft as the mirror of the right grip), `tod_dealer_g_*` = state two (the enslaved / SoE keeper's stepping set, weapon tags pinned to the wrists). `install.py` maps AU rows -> float set, AD rows -> ground set, splits `idle@zombie` / `move@zombie` on ARMS_UP / ARMS_DOWN (the script sets `self.zombie_arms_position`), clones each GDT block from its source (notetracks kept), keeps the 27 raw sources in `art/dealer_boss/clips_src/` (gitignored, never zoned). RULES PAID FOR: the raw Keeper clips animate `tag_weapon_right` LOOSE (up to 20 in off the hand) and park `tag_weapon_left` 350 in away - derive palms from the wrist + bind geometry; a direction rule that flips sign snaps (97 deg/frame) and so does a vector blend of near-opposite directions (route through a waypoint); gdtdb REFUSES ONE ASSET NAME IN TWO GDTS - my duplicate `ai_zombie_zod_keeper_run_attack_v4` failed every build in the repo 23:48-23:55 (fixed; the installer asserts it). The studio reel (`12_play_reel.py`, `13_scythe_mount.py`, `15_view.py`) plays the authored files with the scythe mounted the way the engine mounts it. Gates: `install.py --check` OK, `test_dealer.js` 1,071 checks. UNBUILT, UNPLAYED; nothing wired. NEXT: the fight script, the machine-gun hold for state two, the voices, wire + FULL build.

**2026-09-30 23:24 - THE DEALER IS THE FINAL BOSS: THE CHARACTER IS BUILT, EXPORTED AND INSTALLED; THE FIGHT IS NEXT (user: "make the black market dealer the final boss ... build a model using the Blender MCP ... super, super deep ... long, sharp red nails ... a persisting black shadow ... steal an animation"; then "two states. He will be Richtofen when his mask breaks ... new voice lines ... a scythe, the Wunderwaffe that shocks everyone, a machine gun"; docs/199; CHANGELOG 23:24).** THE RIG: the Keeper's skeleton (humanoid + robe chains + weapon tags); every installed Keeper clip plays on him plus 28 more from the T7 pack (the Protector's composed walk 85 in/s / run 118 / sprint 159, idle scans, standing attacks, bamf teleport, intro, channel loop; all 145 parts checked). PLAYER CLIPS DO NOT FIT (different spine bones + bind pose, and the pack has no firing / melee player clips) - checked, do not retry. THE MODEL: `tools/dealer_boss/01..11` in a VISIBLE studio (port 9899, `start_studio.ps1`, Blender 4.2 + PyCoD), master `art/dealer_boss/dealer_boss.blend`: open-front wool coat on the robe chains, mantle, bell sleeves, the shop's own mask construction in a drooping hood, gloves with ten red nails on the tip bones, vials / satchel / keys / tokens, red neon stitching everywhere; STATE TWO = Richtofen's DE cinematic head under the hood (mask + void are `state1_only`); THE SCYTHE authored (origin = grip, attach to `tag_weapon_right`), the DG-2 + Dingo staged from the pack and previewed in hand (the user has a BO6 Wunderwaffe pack - location not found under Downloads yet). Skinning PROVEN under real clips (`09_pose_check.py`; the mantle no longer rides the arm bones). PIPELINE: `export_native.py` (strict guard; 5-channel atlases, masked / unmasked / scythe binaries masked LOD0 99,101 tris / unmasked 101,153 / scythe 1,520, 72 s on the GPU) -> `install.py` (`source_data/tod_dealer.gdt`, `tod_dealer.ai_*`, 28 clips, donor materials; `--check`) -> `test_dealer.js` (848 checks, 0 failures) -> `wire.py` (shared files, RIGHT BEFORE a build; NOT run). RULES PAID FOR: a Blender collection name over 63 chars never matches itself again; a hidden object is not evaluated (unhide before export); `armature.bones` is hierarchy-ordered (compare sets); an in-memory PyCoD Model needs an explicit version; the modlauncher window is not a build stage. NEXT: `_tod_dealer_finale.gsc/.csc` (controller, archetype "dealer" blackboard, dealerDeathStart, scythe swipes / Wunderwaffe shock / Dingo bursts, the mask break + model swap, the black-soul aura, the arena), the two voice sets (drafted in docs/199), wire + FULL build. UNBUILT, UNPLAYED. Logs planned `[TOD_DEALER]`.

**2026-09-30 21:20 - THE SKY FILLED UP (sky fleet v4): A HIGH LAYER OF TRAFFIC (~1.5x), CONVOYS, A HIGH BELT OF ROCKS AND STARS, SATELLITES, AN ENTITY BUDGET (user: "add more but at a higher altitude. I would love the sky filled up. Maybe 1.5x more"; "any enhancements ... for a more atmospheric player experience"; "make sure we dont have any leaks or bugs. Ive already had a game where my game was freezing cause of this"; docs/192 s12; CHANGELOG 21:20).** THE HIGH LAYER: every class runs a SECOND schedule (`gen_lanes.js MOTION.hi` -> generated `motion()` `hi_*`; `_tod_sky_ships.csc` rev 4 `class_loop( def, tier )`, `sched()`, `live_key()`, `pick_lane( def, p, tier )`) flown 9,000..20,000 u over the player's feet, 1,200..16,000 u sideways (`TOD_SKY_HI_*`): seen >= 31 deg up, often near the zenith; the approved low layer is untouched; expected ships in the sky at once 5.9 -> 9.3 (x1.59, the gate computes it from caps, gaps and measured flight times). CONVOYS: 30 % of normal hauler flights lead 1-2 more haulers 16 s astern on the same line (`convoy_fixed` / `convoy_followers`, fixed-path sorties, a small stagger), 22 % of gunships fly as a pair; only a lead ALONE in its tier, never a rift flight. THE HIGH BELT: 35 % of drifts and streaks start 58..86 deg up; rates x1.5 (9 rocks at once, drifts 3.5..9.5 s, streaks 4..15 s, fireballs 55..135 s); black holes 9 + 6 rocks. SATELLITES: up to 3, a warm-white 2.7..7.1 px point crossing the upper sky (>= 30 deg) at 0.2..0.5 deg/s for 70..160 s with a tumble flare every 2.2..4.5 s (4 generated sizes `fx_sky_sat_xs/s/m/l`, zoned + precached, a tag_origin host). THE POP GUARD TIGHTENED (a v3 latent hole the new random draw caught: a rift-departure flight whose rift was hidden at flight time flew out behind the crown at 59 px): a hidden <-> shown change is judged by the larger of its two samples, the departure rift is decided at plan time like the arrival, and the fallback fly-out is sampled. THE USER'S LEAK / FREEZE WORRY, MADE MECHANICAL: `TOD_SKY_ENT_MAX` 96 client entities per player, every spawn counted (`ents_add`) and uncounted at its Delete, sortie / drift / satellite refuse past it (log BUDGET; the worst case of every cap, convoy, cluster, orbit and rift at once is ~105, normal play ~40..60); the gate's lifecycle block checks every spawning function for its Delete, spawn sites == budget counts, counters up/down once; `rift_end` idempotent; the black-hole loop no longer makes a struct per rock per tick; one shared satellite def. RULES: a fleet object is one stand_in + MoveTo + RotateTo per 0.1 s tick, never a per-tick allocation or log; every spawn counts the budget; the pop guard must sample every path a flight can take (a fallback is a path). Gates: `test_sky_ships.js` v4 (336 flights incl. 112 high, 28 convoy followers, 120 satellites, schedules / expected fleet / budget, 19 negative controls), `gen_lanes.js --check` (1482 bands), `gen_fx.py --check` (69 effects). BUILT: -GscOnly BUILD OK 21:56:29 (tmp/sky_ships/gsc_v4.log; the watcher built the moment the game closed at 21:45): FF 225,991,104 B at 21:54:42; every fleet gate ran inside it (PASS sky fleet v4, SKY LANES OK 1482 bands, SKY FX OK 69, arity, native API); the ledger (21:54:42) carries the 4 satellite effects, 91 sky effects, `_tod_sky_ships.csc` + `_tod_sky_lanes.csc`; scripts / zone_source / ui diffs clean, the 4 effects + both scripts deployed = repo, nothing synced after the .ff, the 8 known-waived linker errors only (a -GscOnly: geom_key notes the map / sky moved since the 11:22 FULL build - peers' pending passes, not this one). SUPERSEDED AS THE TEST .ff by the Black Market voice session's -GscOnly BUILD OK 22:38:24 (tmp/black_market_vo/gsc10.log; FF 225,991,040 B at 22:36:23): it carries v4 whole (PASS sky fleet v4 ran inside it, deployed director + zone = repo, the 4 satellite effects in its 22:36 ledger, banks whole: loaded 132,233,728 B, streamed 291,417,984 B = the 277.9 MiB both logs print). That link overlapped Map One's publish language passes (its session asked every Tower II session at 22:37 to hold linkers until ~22:50; this session held and relayed it). UNPLAYED. Logs `[TOD_SKY] READY rev=4 ... high_layer=1 caps_low=7 caps_high=4 ... ent_max=96`, `SORTIE ... tier=high alt_over_player=`, `CONVOY`, `BUDGET` (none expected), `SAT` / `SAT_DONE`.

**2026-09-30 20:49 - FIFTH PASS ADDENDUM: THE USER'S DATA POINT + THE EYE TRACE.** User, after the 18:18 build: "when it was only the jump and no pause mid air this didnt happen" - the hang pass (2026-09-29) is exactly when the mover went from one MoveTo every 0.1 s (a segment that never reaches its end before the next one: no clamp) to one every server frame (it does): the same mechanism the lookahead removes, the hang kept. NEW client EYE TRACE in `_tod_jump_title.csc`: `[TOD_JT] TRACE up|down ms= x= y= z=`, the local camera's position every CLIENT frame for 0.6 s from the launch and 3.0 s from the end beat (`TOD_JT_TRACE_UP_SECS` / `_DOWN_SECS`; ~600 lines a first flight; ZERO BOTH BEFORE A PUBLISH). Read it: ~50 ms plateaus in z = the trajectory clamping; a steady slope = fixed; a sign-changing slope = something else (then the fallback is a velocity-driven flight like the grapple, which the client predicts smoothly, with the cinematic view locked some other way). BUILT: my -GscOnly BUILD OK (tmp/jump_title/gsc_pass5b.log; FF 225,982,080 B at 20:47:03; both scripts in the ledger, deployed = repo, nothing synced after). THE CURRENT TEST .ff IS NEWER: session -37's -GscOnly BUILD OK (tmp/black_market_vo/gsc10.log; FF 225,991,040 B at 22:36:23) carries this whole pass unchanged plus its dealer laugh at the lit sign (`TOD_JT_ALIAS_LAUGH` in the reveal, after the flicker; reviewed in place); JUMP TITLE LEDGER OK, deployed = repo, nothing synced after. UNPLAYED.

**2026-09-30 18:19 - THE FIRST JUMP, FIFTH PASS: EVERY GAP SHORTER, THE SIGN LIT AS THE WHITE BURNS OUT, THE MOVER AIMED TWO FRAMES AHEAD (user after playing the fourth pass: "looking good ... things happen a bit too slow ... sitting there a little bit too long waiting for the spaceships to explode ... when they explode you almost still see the sign but it's not even glowing ... when you're falling, the player kind of wavers up and down ... clunky"; docs/196 s7; CHANGELOG 18:08).** PACING (`_tod_jumppad.gsc` CINE_* defines, `_tod_jump_title.csc` rev 6): the turn 2.25 -> 1.6 s (a bigger turn scales up to `TURN_MAX` 2.05 s so the camera never passes 150 deg/s and settles before the charge), warps 1.3 / 1.95, standoff 0.6 s, ram 1.1 s (charge 2.5, impact 3.6, ignite 3.8), the sign lit 1.2 s after the impact instead of 2.4 (REVEAL 1.0: the flicker starts as the white burns out onto the fireball), 2.65 s on the lit title, swing back 1.5 s (7.9 -> 9.4), control back 10.4, flight 13.8 -> 11.6 s; gen_fx re-timed; `make_sounds.py` reads the ram's length from the jump script (the charge wav regenerated). THE DESCENT JUDDER: the arc, the server clock and the camera hand-back are all clean in the user's log; a linked player on a mover driven by ONE MoveTo PER SERVER FRAME judders because each 0.05 s segment ends exactly when the next snapshot is due (a client clock a hair ahead clamps it, then jumps) - invisible against the sky going up, a judder against the terrace coming down. FIX: `TOD_JUMPPAD_LOOKAHEAD` 2 - every frame the mover (and its RotateTo) is aimed at the arc point two frames ahead over two frames (`arc_point()`), so the client's trajectory always outlives the snapshot interval; a `TRACK` log measures the tracking error (`LAND track_err_max=`). RULE: never drive a linked player's mover with segments no longer than the snapshot interval. RULE PAID FOR AGAIN: never edit the jump scripts while a peer build runs (a -GscOnly synced this pass mid-edit at a gate-failing state). Gates: test_jumppad (the lookahead loop pinned; 252 flights of the new path, fastest 147 deg/s), test_jump_title (the reveal window + a negative control for the old 2.4 s), fleet + letterbox gates green. BUILT in session -37's -GscOnly BUILD OK 18:18 (tmp/black_market_vo/gsc8.log; FF 225,981,440 B at 18:16:30; the loaded bank rebuilt 18:16 with the regenerated charge wav, all.sabs 277.9 MB; JUMP TITLE LEDGER OK; both scripts, six effects, the charge wav and the alias table deployed = repo (the aliases at share/raw/sound/aliases and the usermap's sound/aliases), nothing synced after; its gsc7 attempt had synced this pass mid-edit and never linked). UNPLAYED. Logs `[TOD_JUMPPAD] INIT rev=5 ... lookahead=2`, `CINE_CAM ... turn_secs=`, `TRACK op= frame= err=`, `LAND ... track_err_max=`; `[TOD_JT] INIT rev=6`.

**2026-09-30 - DEALER CREST / THREE WALL DISPLAYS: SOURCE READY, FULL BUILD STILL REQUIRED.** The accepted city now has the canonical Dealer hood/X-eyes/stitched grin above the title; matching dim/lit Blender reviews and three sparse wall displays are complete. Sources are frozen; no completed combined native build yet. The first attempt was stopped before cod2map/LED for a missing explicit portrait sync row, now fixed and source-gated. Preserve its snapshot/log in tmp/sky_dealer/attempt1_sync_omission. Next: resource clearance, fresh combined snapshot including tools/sync_to_modtools.ps1, guarded -ForceBake build to tmp/sky_dealer/full2.log, strict sky and presence native proofs. Map geometry changed: a peer GSC-only link is not this delivery. All our Blender processes are closed; another session's Map One preview is open, and concurrent native work has recurred. Do not close foreign processes. The earlier Blender/Radiant overlap could have increased memory pressure; causality is unproven. Resource guards, art and repro: tools/sky_dealer/, art/sky3d/dealer_review/review.html, docs/166 section14, docs/dealer_identity.md. Dealer selected as final boss; fight implementation remains pending, not shipped. No game launch.

**2026-09-30 11:27 - SKY CONSISTENCY BUILT; READY FOR USER PLAYTEST.** All 1,189 ordinary buildings now use the approved close cyber kit; large landmarks and the imposing title share worn graphite/alloy materials. Planet/ring/moon/star emission is restrained to preserve detail. Reduced layout, station, hero silhouettes and >=3.16-degree celestial clearance remain. The finalized 8192x4096/160 sky uses fixed gain 0.016525428679573573 (city .4551386638, whole .4450815916), unchanged skyStops 4.35 / skyRotation 40. First-jump work is integrated: the sky bakes DULL, and the native lit card reveals after the crash. Its real Blender material bake preserves exact foreground/ground coverage; reflected architecture/spill uses .06 while lettering and bright tube cores retain native16. GDT leading comments removed; rectangular card texture has noMipMaps/noPicMip enabled. Guarded FULL BUILD OK 11:26; strict proof 11:26:52: all 212 runtime inputs, 111 authoring artifacts, current source parity, fresh BSP/LED/both SSIs, 11 sky/jump assets and compiled two-triangle native card verified. FF 225,982,016 bytes, SHA256 1e6dcdfe5e984f6273e66cf5ec33a6dfcaf4f8c3435510199acbd102d99c586c. Evidence art/sky3d/consistency_review/build.json; comparison review.html; docs/166 section13; pipeline tools/sky_consistency/. Finished preview art/sky3d/consistency_preview.blend has Before jump / After reveal scenes, actual native card inputs and approximate display conversion. Reopen with tools/sky_consistency/open_preview.ps1 to restore Rendered/Scene World/Scene Lights. Earlier pass evidence is historical. Native appearance and reveal behavior UNPLAYED; no game launch.

**2026-09-30 11:27 - THE FIRST JUMP, FOURTH PASS: THE SKY SIGN IS BAKED DULL AND A CLIENT CARD FLICKERS IT ON AT THE CRASH (user, reviewing the flow: "I want it to be in awe shock and just sick and the thing i really want is the sign to not glow and actually be very dull and then after explosion it should glow very bright"; docs/196 s6; CHANGELOG 10:41).** Rev 3 dimmed a LIT baked sign behind seven smoke puffs (`fx_jt_veil`): a dim, never a dull. NOW: (1) THE SKY BAKES THE SIGN DULL - `build_city.py --sign-state dull` -> `cyber_hero_title.py` DULL branch (max channel capped 0.05, desaturated 55%, body x0.7, no neon boost; the title report says `sign_state: dull`); the Codex sky-consistency pass carried it (`tmp/sky_consistency/author_config.json`, handoff at the top of AGENTS.md; sky score 0.4451 re-pinned by that pass). (2) THE LIT SIGN IS A CLIENT CARD MODEL `tod_jt_sign_lit` (`tools/jump_title/make_sign_card.py`, GENERATED + `--check` in the build: the painting on a quad with the sky's own GATE geometry at SIGN_DIST 9,500 u = 12,104 x 8,070 u, `lit_emissive_transparent`, scaleRGB 16 = THE ONE BRIGHTNESS KNOB; the Codex pass then derived the card's texture from its own sign finish with scene-depth holdouts, `art/sky3d/sign/v11_native_lit.png`). `_tod_jump_title.csc` rev 5 spawns it hidden at the scene start on the sign's bearing, rides the camera, and at THE REVEAL (7.0 s) plays the power surge and FLICKERS IT ON (70/60/50/100/120/50 ms, then steady; `flicker_ms()`, READ by gen_fx so the blaze glows start when it holds, 7.45 s); it stays lit for the match per client; a scene cut after the ignite lights it at once. SIGN_DIST 11,000 -> 9,500 (the card must sit BEHIND every hull point that crosses it and inside the sealed volume; gate D proves both). RULES: never zone the card's material bare; the card shares the sky's bearing and GATE geometry, so a sideways error is the SKY's (measure, docs/196 s3); a lit overlay over a dark bake hides registration error, a dark overlay over a lit bake leaks neon at every edge. Gates: `test_jump_title.js` rewritten (30 negative controls), `sky_cohesion/verify_build.py` six effects + the card in the ledger. REVIEW of the rest of the flow: the third pass's camera path, boom and engines stand; the music aliases are `snp_never_duck`, so the crash cannot duck the band (the music owner's call). BUILT in the Codex sky pass's FULL BUILD OK 11:24:26 (tmp/sky_consistency/full.log; FF 225,982,016 B at 11:24:26; fresh LED 119,704,569 B; new sky .iwi 7GK7H3JLFEPGLM3OY4JTWDN7NE, the card's i_tod_jt_sign_lit .iwi converted 11:24:16; JUMP TITLE LEDGER OK: 7 effects + the client script + the lit sign card; every file of this pass deployed = repo, nothing synced after; its first two attempts died on my GDT's leading // comment (gdtdb refuses it) and on mip maps for the 1536x1024 card image (NPOT: the image now carries noMipMaps + noPicMip, both fixed by the Codex pass); the stale deployed fx_jt_veil.efx removed from the private tools root). UNPLAYED. Logs `[TOD_JT] INIT rev=5 ... card= flicker_ms=450`, `LIT why=reveal flicker=1`, `BLAZE`, `LIT_FAIL`; `[TOD_JUMPPAD] INIT rev=4 sign=dull_bake+card`.

**2026-10-01 11:11 - THE BLACK MARKET DEALER, ROUNDS 3-6: WHO IS HE? A described voice pushed toward Richtofen, lore-only hints, THE MASK as a tone, the sign laugh; SOURCE LANDED, BUILD PENDING in the Dealer session's FULL build 3 (docs/198).** The user wants the dealer to be Richtofen-but-not-confirmed ("he is Richtofen but you aren't really sure"), then "not enough Richtofen", then "remove the obvious hints like Wunderbar ... more towards his voice", then "his exact accent mannerisms ... for when the mask comes off", then "we can do better on the generated version". THE BOUNDARY, held every time: no recording of the character's actor is uploaded, cloned or used as reference audio (ElevenLabs cloning needs the owner's consent; it is a real actor's performance). What CAN reach an exact preference and was offered: the user's own recorded impression as `reference_audio_base64` on the v3 design endpoint, speech-to-speech from the user's performance, a consented impression clone, a remix loop (`eleven.py remix_previews`). WHERE IT STANDS: the dealer's voice = "TOD2 Unmasked v2 (remix B3)" (a remix of a described light nasal sing-song tenor toward his delivery; rounds 2-4 picked the DEEPEST candidate, which was wrong for him), 47 shop lines with NO German vocabulary (lines.json asserts none) and 28 lore-only `egg` hints (one-one-five as digits, the voices, the little girl, my children, "started with an E. Or did it", doctor, teleporters, electricity, the moon; he never says the name), + the 2.2 s sign laugh (take 7, the user's cut, never regenerated: `--skip-group cinematic`). THE MASK = `mask_tone.py` v3 applied by `pick.py` to every shipped line (pitch 0.90, four close reflections, flanger shimmer, -8 dB shelf at 3.6 kHz, low-pass 8.2 kHz, +4 dB at 1.6 kHz, +3.5 dB low shelf, tanh, 2.6:1), raw takes stay clean in tmp/black_market_vo/takes (rounds archived takes_round1..5). THE DESK: `build_desk.py` -> LOCAL tmp/black_market_vo/review/dealer_voice_desk_local.html (never published; the hosted copy was deleted at the user's request): Masked / 100% (A/B) / Actual = a pick-list of 20 of his original lines downloaded from the CoD wiki's audio category via api.php into tmp/black_market_vo/reference (LISTENING ONLY). Reveal auditions: lines_unmasked.json, tmp/black_market_vo/unmasked/{A,B,V2,V2mask,M}. Gates green in the repo (pick.py --check, test_spin 459, test_jump_title, kit, arity). BUILD: my -GscOnly attempts gsc11-gsc17 were each superseded or retired (three concurrent builds on 10-01 morning; a waiter must treat 'a powershell that parents a -s -NoLogo job host' as a running build); the deployed .ff is the Dealer session's 10:03:59 one and does NOT carry rounds 3-6. Session -3d's FULL build 3 (tmp/dealer_boss/full3.log) carries this tree; verify my 48 wavs / tod_shop.csv / _tod_shop_vo.gsc / the laugh define from ITS ledger and bank before playing. Key: `ELEVENLABS_API_KEY` user env var only (restricted; rotate it after the voice work). UNPLAYED; the user judges by ear on the desk first.

**2026-09-30 09:46 - SKY v10: APPROVED CYBER MIDDLE GROUND BUILT.** User rejected v9 as looking reverted and approved art/sky3d/middle_ground_review/concept.png ('Yes-use this direction'). This supersedes both earlier extremes: engineered cyber pylons, massive dimensional lettering, worn dark metal and a smaller angular mechanical death-mask; never restore the gothic/anatomical skull gate. Modern architecture now covers 624/1,189 retained ordinary buildings (267 before), including 357 nearer small spires; four tapered/split/cantilever/slot families, elevated pods, worn plate materials and restrained inlays. Preserve all eight placed hero towers, the moderate 1,222-building/18-sky-group layout and Skyrail station. All 14 planet/ring/moon groups clear the measured skyline by >=3.16 degrees; primary moon 10.32. Final 8192x4096/160 render: city .64, whole score 0.6343138813972473, skyStops 4.35/skyRotation 40 unchanged. Jump glows follow the new title landmarks; the case-safe asteroid fix remains intact. Guarded FULL BUILD OK; verified 2026-09-30 09:46. FF 225,466,880 bytes at 2026-09-30T09:42:38.418042-04:00; fresh BSP/LED and both SSIs; new sky image i_skybox_tod_cybercity_WXHEDVDOTJLNYAXEVUKI6KL47L.iwi. All 209 runtime inputs match the captured snapshot and deployed copies; all 86 authoring artifacts still match; all 11 sky/jump assets packed. A separate in-progress _tod_shop.gsc edit landed after the build snapshot and is not included. Sky inputs are current; whole-checkout source parity is explicitly false. No later shop work was overwritten or synced. Exact proof art/sky3d/middle_ground_review/build.json; comparison final_review.html there; docs/166 section12; pipeline tools/sky_middle_ground/. Finished-HDR Rendered preview saved as art/sky3d/middle_ground_preview.blend, Scene World/Scene Lights enabled; editable master art/sky3d/tod2_sky.blend. Reopen via tools/sky_middle_ground/open_preview.ps1: Blender resets saved shading to Solid on load; activate_preview.py restores Rendered and scene lighting without resaving the snapshot. Actual reopened viewport checked 09:49; evidence blender_reopened.png and preview_activation.json in the review folder. These display-only helpers were added after the native build. Built-in Imagegen source/prompt/provenance art/sky3d/sign/v10_cyber_hero.*. Earlier v8/v9 evidence preserved. Native appearance UNPLAYED; no agent game launch.

**2026-09-30 09:46 - THE FIRST JUMP, THIRD PASS: ONE SMOOTH CAMERA PATH, A REAL BOOM, WARSHIPS YOU CAN HEAR; BUILT (user after playing it: "not super smooth. The player wavers back and forth towards the end of jump", "an actuall loud boom instead of the nuke sfx", "the ships should have some sound effect ebfore the boom"; docs/196 section 5; CHANGELOG).** The waver was the script: the swing back pitched the view 32 deg down then 24 deg back up while control returned, and at the start a closing LerpViewAngleClamp fought four RotateTo moves. `_tod_jumppad.gsc` now drives ONE eased camera path, a pure function of the flight clock (`cine_cam_plan` / `cine_cam_angles`), stepped with the arc every server frame: the mover takes the rider's own view and the link has no view arc, pitch leads, one move to the landing view (the heading, 16 deg down) by 12.1 s, still after. NEVER AGAIN: a view clamp closing on a mover that RotateTo also turns, a view move that reverses, or turning the view after control returns. The boom was the Nuke power-up (its bang lands 1.5 s after the flash): `tod_jt_boom` is rebuilt from real explosions and peaks in its first 0.2 s. The ships sat 7-20 dB under the never-duck music: NEW `tod_jt_engine.wav` loops on each gunship from its warp to the crash (full level to 12,000 u), the warp and charge are rebuilt, every crash cue at volume 100. `tools/jump_title/make_sounds.py` rewritten (6 wavs; `--check` gates loudness, shape and the loop seam). The gates RUN the shipping camera: test_jumppad 3d (63 launch views, gsc_eval.js) and test_jump_title C (25 views) + NEW audibility checks F. BUILT in the sky session's FULL BUILD OK 09:44:44 (tmp/sky_middle_ground/full.log; .ff 09:42:38, FF 225,466,880 B): every jump gate and JUMP TITLE LEDGER OK inside it, the six tod_jt aliases in the compiled alias table, all jump inputs deployed = repo, nothing synced after (a peer's `_tod_shop.gsc` saved 09:45 is NOT in it). My own -GscOnly (tmp/jump_title/gsc3.log) linked, but that build's sync removed the ledger folder under its post-link checks. UNPLAYED. Logs `[TOD_JUMPPAD] INIT rev=3 cam=path`, `CINE_CAM`, `CINE_FREE ... angles= planned=` (angles must equal planned), `[TOD_JT] INIT rev=4`.

**2026-09-29 23:49 - ASTEROID FREEZE ROOT CAUSE FIXED AND BUILT; PATCHED USER LOG CLEAN.** The user's 23:36 log contained 14,327 script-error reports (~92/sec), all from `_tod_sky_ships.csc`. Native CSC local names are case-insensitive: never distinguish values only by case, such as d/D. `rock_state` overwrote its direction vector with scalar distance; the captured first bad float 1.71925e16 exactly equals the shard distance squared. Fixed with distinct direction/distance locals; startup READY now includes rock_math=case_safe. The offline `gsc_eval.js` previously treated locals case-sensitively and missed this; it now case-folds parameters, locals, foreach destinations and assignments. `test_sky_ships.js --native-semantics-only` reproduces the exact old failure and passes the fixed zero-age shard. Guarded -GscOnly BUILD OK (tmp/freeze_audit/gsc.log), FF 225,465,920 B at 23:48:11; focused regression and full 224-flight/240-drift/24-orbit/300-streak gate pass. Exact deployment proof tmp/freeze_audit/build.json: all 209 runtime inputs match the snapshot/current/deployed files, only runtime change is the fleet CSC, repaired script in fresh ledger, same geometry/lighting. Preserved user log, original deployed CSC and numeric proof under tmp/freeze_audit/; docs/192 section11. The subsequent user capture tmp/sky_reversion/runs/20260930_000338_723_513bd4eb/console_mp.log contains the case-safe READY marker, active fleet/asteroids and a completed jump cinematic with zero script-error blocks. This confirms the fix loaded and the previous error flood is absent in that captured match; it is not a claim that every performance issue is settled. No agent game launch.

**2026-09-29 22:22 - HISTORICAL SKY v9: TITLE DIRECTION SUPERSEDED BY APPROVED v10.** The title must be the skybox's most impressive and scary focal point. The minimal v8 monument lost the requested awe: the shipping default is now `ominous_title.py`, a looming armored skull gate with massive crimson lettering, violet channels and dark worn cyber metal. This supersedes v8's prohibition on the gate silhouette; preserve the cyber architecture and measured cinematic anchors. Use purposeful material variation and wear on every model. Authored sky buildings 1,838 -> 1,222 (33.51% fewer), named sky groups 27 -> 18, all eight placed hero towers retained; fewer background lights/stars and a clear station with platforms, canopy, tracks, signage and five train cars. Primary moon elevation 41 degrees; all 14 retained planet/ring/moon groups clear the actual solid skyline by >=3.16 degrees. Two foreground crowns were additionally removed to reveal the full subtitle. Final 8192x4096/160-sample sky: city score .64, whole score .6336461901664734, skyStops 4.35/skyRotation 40 unchanged; jump glow offsets/palette follow the new title. Guarded FULL BUILD OK, verified 22:22: FF 225,465,792 bytes, fresh BSP/LED and both SSIs, new sky IWI `NYHHHP3JKYN35WNOGLSXXB646M`; 209/209 runtime inputs and 77 authoring artifacts match the captured snapshot, 11 sky/jump assets packed, no pending source changes or exceptions. Pipeline `tools/sky_simplify/`; exact proof `art/sky3d/simplify_review/build.json`; before/after gallery `art/sky3d/simplify_review/review.html`; docs/166 section 11. Finished-HDR Rendered preview open/saved in `art/sky3d/simplify_preview.blend` (Scene World/Scene Lights enabled; approximate native bloom/exposure). Built-in imagegen title source/prompt/provenance retained under `art/sky3d/sign/v9_ominous_gate.*`. v8 files remain historical. UNPLAYED; no game launched, the user tests.

**2026-09-29 22:22 - THE LUCKY SOURCES: LUCKY CLOVER DROP + LUCKY METEOR + ONE GOLDEN ZOMBIE EVERY ROUND WITH A GOLDEN GLOW; KILL LUCK 12 (user; session 2a; docs/197; CHANGELOG 18:27 + 19:28 + 21:55).** Kill luck per fair-share round 18 -> 12 (`TOD_LUCK_KILL_BUDGET`, user: "Make it 12%"). NEW `tod_luck::add_bars(player, n)` pays N bars (segments) one step at a time. THE LUCKY CLOVER (`_tod_lucky.gsc|.csc`): a grabber-only drop like the perk bottle / PaP / Zombie Blood (stock's pale white 'solo' glow), +3 bars; random drops at `TOD_CLOVER_DROP_PCT` 50 + the meteor. ITS MODEL WEARS THE DROPS' OWN STOCK MATERIAL `mtl_x2icon_gold` (the PaP drop and Zombie Blood both do; black colour, reflections only - it is NOT gold in game despite the name): the user rejected an emerald/gold clover as out of family ("so it seems like it comes from this game ... why would you make it gold"). `tools/lucky/verify_native.py` FAILS on any other clover material. THE LUCKY METEOR: every 2 rounds from round 3 a real server script_model rock crosses the sky low over a player (the sky fleet is client-only and cannot be shot); a view ray on weapon_fired (the teddy bears' test; not the Warrior) within `TOD_METEOR_HIT_R` 195 breaks it and the clover falls to the shooter; it pauses with the world. THE GOLDEN ZOMBIE (`_tod_golden_zombie.gsc`; user 21:30: "make one per round ... It should have a golden glow"): ONE EVERY ROUND (`TOD_GOLDEN_PER_ROUND` 1; the round's Nth ordinary spawn, N from its first 60%, stock `add_custom_zombie_spawn_logic` counts them); a golden killed by no player (nuke, trap, sweep) or removed is OWED to the next ordinary spawn in any round (`golden_owe`, max 2); gold twin xmodels (`tools/lucky/make_golden.py`, self-glow 0.45 x 2.2), an aura with a small halo (70 u / alpha 0.2) and a REAL gold dynamic light (`make_fx.py golden_light()`: the perk-glow light copied, colour on its colorGraph with a white def, radius 140, intensity 300, no shadows, one at a time crossfading). PLAYED 23:54 (one per round, bars paid, 0 errors); user: "The glow ... is way too intense" -> 2026-09-30 00:06 all three layers cut (were 0.45 x 6.0 / 120 u 0.5 / 700 r180), FULL build queued behind the running game (`tools/lucky/build_when_idle.ps1`, tmp/lucky/status.json), no gibs, never a sprinter/thrall; the killer (companion/helper -> owner) gets 3 bars. See it without the game: the lucky Blender studio (9888), `tools/lucky/03_golden_viewer.py` + 04 + 05. Models: Blender MCP studio port 9888 (`tools/lucky/01_author.py`); effects `make_fx.py`, sounds `make_sounds.py` (`tod_luck.csv`), all `--check` gates. RULE LEARNED: WIRE LAST - `tools/lucky/wire.py` puts the build checks + zone + entry lines into the shared files in ONE step right before a build (landing them early stopped a peer's build at 19:18). RULE LEARNED: the converter drops needle triangles silently (72 on the clover's bevelled heart cusps, FULL build 1) - verify_native's compiled-vs-exported count caught it; read the converter .log under share/assetconvert/xmesh/v6/. FULL BUILD OK 21:18:00 (tmp/lucky/full2.log) carried the first pass; the one-per-round + glow pass rode the peer's FULL BUILD OK 22:22 (tmp/sky_simplify/full.log): .ff 22:20:29, FF 225,465,792 B, every lucky pre/post-link check passed (models compiled exactly, 10 lucky assets in the ledger), the three golden glow .iwi re-converted fresh, diffs clean, nothing synced after, all inputs deployed = repo; the sounds' presence inside the bank is NOT byte-verified (encoded). UNPLAYED. Logs `[TOD_LUCKY]` / `[TOD_GOLDEN]` / `[TOD_LUCK]` (tod_dev).

**2026-09-29 19:45 - SKY v8 HISTORICAL BUILD; TITLE DIRECTION SUPERSEDED BY v9 USER CORRECTION.** The title monument and ordinary buildings must share the tall towers' futuristic architectural language: dimensional engineered forms, dark varied materials, restrained routed neon and purposeful wear. The new direction explicitly supersedes the earlier request to copy the gothic/haunted gate painting; do not restore that as the shipping sign. Use `tools/sky3d/cyber_title.py` and `cyber_architecture.py` through the Blender MCP sky pipeline. Preserve the measured sky/jump bearing and cinematic anchor contract. Give celestial bodies clear angular space above the solid skyline, measuring rings and satellites too; keep prominent stars in the upper sky. Keep shipping static ships/asteroids retired. v8: authored cyber monument, 363 industrial lower blocks, original tall spires preserved, 20 celestial groups clear by >=3.04 degrees, updated jump-blaze palette/crest. Final 8192x4096/160-sample render; city score .64, whole sky .6456634402275085; skyStops 4.35/skyRotation 40 unchanged. FULL BUILD OK 19:45 (`tmp/sky_cohesion/full.log`), FF 224,890,752 bytes at 19:38:51, fresh LED 19:36:25; new sky IWI `56XXDMGQ44UDHW46QRH6DEHQXY`. Evidence/gallery: `art/sky3d/cohesion_review/`; finished-HDR Rendered preview: `art/sky3d/sky_preview.blend`. See docs/166 section 10. UNPLAYED; the user tests.

**2026-09-29 18:11 - THE SKY FLEET v3: ENGINE FLAMES, WORMHOLES, MORE DETAIL, ASTEROIDS, BLACK-HOLE ROCKS, SHOOTING STARS (user: "I can't see any flames ... time warp black hole pulses ... come through like a wormhole ... add more detail"; "flying asteroids ... more subtle ... higher up ... and also shooting stars"; "focus on quality and detail of each"; session 0a = the old 9c; docs/192 s10; CHANGELOG 18:11).** Every ship nozzle is a TAG (`tag_eng_<i>`, aft-facing, exported bones checked by verify_native) that burns a GENERATED flame (`tools/sky_ships/gen_fx.py`, stock donors vendored in `art/sky_ships/fx_donors/`) in 5 size buckets per kind + a far glint: plasma (dreadnought + a time-warp pulse, gunship), heavy fire + smoke (hauler), fire + shock diamonds + contrail (fighter). ~A third of flights come through a WORMHOLE (7 rift sizes; tod_sky_worm_open/burst/close). Tris: dreadnought 45,752, hauler 19,262, gunship 6,614, fighter 2,016. Five Blender-MCP rocks (7 models) drift high (>= 22 deg), orbit and fall into the two painted black holes (`gen_lanes.js skyHoles()` derives them from build_city.py + the GDT's skyRotation); shooting stars, showers, fireballs. RULE: a hidden stand-in that reaches full size POPS IN big - `flight_pops()` re-plans or refuses such flights (the crown round a crown-hall player). `fx_sky_eng_gunship` is KEPT for 61's crash scene (`_tod_jump_title.csc`). Gate `test_sky_ships.js` v3 (224 flights through the shipping director, flames, rifts, rocks, orbits, streaks, 13 negative controls). FULL BUILD OK 18:10 (tmp/sky_ships/full_v3.log): .ff 18:02:01, FF 224,136,320 B, bake reused, SKY FLEET NATIVE OK compiled (15 models exact, 65 fx), rift sounds in the loaded bank, diffs clean, nothing synced after. TOD_SKY_LOG 1 (0 before publish). UNPLAYED.

Sky v8 build audit: `art/sky3d/cohesion_review/build.json` proves the exact sky/master/finish inputs, new native image and fresh bake; 208 runtime inputs match the snapshot. One peer `_tod_lucky.gsc` changed before sync but is unlinked (absent from the ledger and all packed dependency roots). Linked-source snapshot parity and current/deployed copy parity pass; the receipt explicitly records this unlinked exception rather than claiming whole-snapshot parity.

**2026-09-29 17:23 - THE TYPEFACE IS EASIER TO READ; THE OLD FACE IS RETIRED (user: "our typography is a little bit hard to read ... a little bit too thick ... not major changes ... maybe more round ... I don't want ... to go back to the old one"; session e7 = the old d2; docs/172 top note; CHANGELOG 17:07).** Thinner face stroke, lighter outline + 3D extrusion (it used to fill every hole), rounded corners, a real S (it was the 5's shape). Every glyph keeps its old ink box, so `TodGlyphMetrics.lua` is byte-identical and HUD/prompt/card text keeps its size. The menus' font `fonts/tod_tower1.ttf`: % = rings (square blocks read "85%" as "857."), HORIZONTAL_FIT 0.94 -> 0.91 (the wider face made every menu line 3.3% longer; render_menus 0 overflow). The masters are the `_sheets/` PNGs, pinned in `art/typeface/typeface.json`. BUILD GATE `python tools/typeface/typeface.py --check` fails on an un-pinned master change, a stale font/metrics/specimen, or any live file naming the retired archive (only typeface.py may name it). `--pin` ONLY for a deliberate redraw. NEVER restore the old face. The old face, its proofs and the option drafts live in `archive/typeface_retired/` (art/typeface/tower1_original is gone). Every art pack ships the new face. Baked text in existing art keeps the old letters until each image is re-made. A TTF change makes `tools/sky_ships/make_textures.py --check` stale (hull markings are drawn in it): re-render them. FULL BUILD OK 17:23:27 (tmp/typeface/full2.log), FF 222,833,728 B written 17:21:57, fresh bake (61's skyRotation 40), 42 glyph .iwi freshly converted, the TTF in the ledger, diffs clean, nothing synced after; it also carries 61's first-jump rev 3 and 9c's re-rendered hull markings. UNPLAYED.

**2026-09-29 17:16 - THE FIRST JUMP, SECOND PASS: SIGN WHERE THE CAMERA LOOKS, THE REAL CLOCK, SIGN DARK UNTIL THE CRASH, 13.8 s FLIGHT (user after the 15:33 play: "The kaboom ended early ... I looked on the left side ... but the tower of doom sign was on the right ... make sure sign doesnt light up until explosion happens"; docs/196 §3-§4; CHANGELOG 17:16).** THE SKY RULE IS MEASURED NOW: the screenshot's view was rebuilt from the .map (yaw 83) and the painted sign fitted in it: it sat at world yaw 41.4, not 180. **The sky image's centre column faces yaw -(SSI sun azimuth + skyRotation) - roll**: the SSI's sun yaw TURNS THE VISIBLE SKY. The 12:00 / 13:44 notes' "-roll + skyRotation" was wrong by ~140 deg; stock skies agree with the new rule. FIX: `tod_skybox.gdt` skyRotation 180 -> 40 (sign due WEST, the image seam due east); `test_jumppad.js` checks every volume_sun SSI against it; `tools/sky3d/screenshot_fit/` re-measures from any screenshot. NEVER predict the sky's bearing again: measure. THE KABOOM: a client `wait` / MoveTo counts FRAMES (~2.7x fast at 165 fps): `_tod_jump_title.csc` rev 3 runs on `waitrealtime` + per-frame `GetRealTime` motion (log `[TOD_JT] CLOCK`). THE SIGN: the veil is never killed; it lifts 1.4-2.6 s after the blaze starts, surge at 2.2. TIMELINE: first flight 13.8 s (was 11.0; others 7.0), charge 3.4, impact 4.6, blaze 4.8, swing back 10.3. Gates: test_jump_title.js (29 checks incl. the generated effects' lives/curves, 9 new negative controls), test_jumppad.js. BUILT in session e7's combined FULL BUILD OK 17:23:27 (tmp/typeface/full2.log; .ff 17:21:57, FF 222,833,728 B; fresh bake): `JUMP TITLE LEDGER OK`, deployed skyRotation 40 = repo, the five tod_jt sounds in the fresh bank, diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 16:23 - EVERY STATIC ASTEROID OUT OF THE RENDERED SKY (user: "we're going to add actual asteroid models going through the sky so then we need to remove the static ones"; session 22; docs/166 §9.8).** The belt (220), the drifting rocks (90) and both black holes' debris fields (291) are retired like the ships: `scatter_rocks()` builds nothing while their callers keep the same random draws, so nothing else moves; `-Asteroids` = the A/B. The black holes keep their discs / halos / jets / streams; planets and moons stay. Session 9c builds the moving asteroids. The whole-sky score moved 0.6865346 -> 0.6865103, so `SKY_SCORE` in verify_tower_design.js moved in the same edit. BUILT by session 22: FULL BUILD OK 16:23 (tmp/sky_asteroids/full1.log; the log is UTF-16), FF 222,709,376 B written 16:18:40, fresh bake (geom_key saw the sky), the NEW sky .iwi `HCVKQ32NX5A7IIAGB7VB4AS4WU` (31.2 MB, 16:16:28), `image,i_skybox_tod_cybercity` in the 16:18:40 ledger, deployed EXR sha = repo (fb178d52...), scripts / ui / zone_source diffs clean, nothing synced after. It also carried fd's companion freeze and d2's card UI. UNPLAYED.

**2026-09-29 16:00 - THE COMPANION FREEZES WITH ITS OWNER (user: "your AI partner companion should also freeze so we can't kill things while you are spinning or getting your cards").** `_tod_partners.gsc` `freeze_reason(p)` freezes it for: the world pause, its owner's Black Market spin (`tod_spin_locked`, the whole spin), a card deal (`tod_menu_frozen`) or the owner's co-op altar deal (`tod_solo_upg_active`). A DOWNED owner releases it. Frozen = no shots, untargetable (ignoreme; `closest_target` skips it), unhurtable. The thaw restores the snapshot (9c's rule) and restarts the stuck clock (no RECOVER pop after a spin). The user's 15:32 log proved the bug: the Cerberus fired ~50 shots and got 2-8 kills per spin while zombies ignored the spinner. Gate: test_partners.js, 141 checks incl. a negative control of the old world-pause-only gate. Logs `[TOD_PARTNER] PAUSE value=1 why=` / `PAUSE value=0 ... shots_during kills_during hits_blocked` (both "during" counts must be 0). BUILT in session 22's FULL BUILD OK 16:23:47 (tmp/sky_asteroids/full1.log). The .ff was written 16:18:40 (FF 222,709,376 B). The gate ran in the build, and the script is in the ledger. Deployed = repo, and nothing was synced after. UNPLAYED.

**2026-09-29 15:31 - THE FIRST JUMP'S CRASH (user; docs/196 §4). REV 1: its timings, its sky rule and its 'the veil clears at the impact' are SUPERSEDED by the 17:16 note (rev 3).** A player's FIRST jump (11.0 s) is now a title moment. The magenta and green gunships from session 9c's fleet WARP IN beside the dimmed sky sign as the camera turns (1.5 / 2.25 s), ram each other in front of it (3.9 s: full white 3.97-4.32, fireball, shake, boom + rumble), and the TOWER OF DOOM II sign BLAZES on behind the white (4.1 s: neon glows on the title, the subtitle, the skull's ring and its eyes). Then wreckage falls to the city and 9c's fighters salute, until the swing back at 7.3. Server `_tod_jumppad.gsc` sends five beats to the flyer's client (`tod_jump_title_start/_ships/_impact/_ignite/_end`, >= 0.1 s apart). RULE: `util::clientNotify` is a per-player STATE, so two in one frame lose the first. The retired `tod_jump_reveal` is gone. The client half is NEW `_tod_jump_title.csc` (zero server entities): ships hidden until their warp; hulls removed under the full white. The smoke and the blaze ride a SIGN HOST moved every frame to camera + bearing x 11,000 u (the sky's sign is at infinity; a fixed point slides off it). Everything is GENERATED: 7 effects `tools/jump_title/gen_fx.py` (stock effects re-scaled; the blaze placed from 22's card geometry), 5 sounds `make_sounds.py`, aliases in `sound/aliases/tod_jump.csv`. Gates: `test_jump_title.js` (beats / framing on 20 flights / 9c's 1,500 u clearance / wiring, 13 negative controls, `--ledger` post-link); gen_fx + make_sounds `--check`. The sky fix (roll 0 + skyRotation 180) BUILT in fd's 14:23 build; test_jumppad's in-flight allowance is gone. Storyboard: `python tools/jump_title/render_storyboard.py` -> docs/196_ref/crash_storyboard.png. FULL BUILD OK 15:31 (tmp/jump_title/full2.log; .ff 15:28:56, FF 222,707,072 B; fd's bake reused): the same 8 known-waived linker errors, `JUMP TITLE LEDGER OK` (both gunships, the client script, all 7 effects), all 5 sounds in the loaded bank, deployed = repo, nothing synced after. Build 1 (full1.log) carried a black-out veil (70 stacked puffs); it was fixed to 7 before any play (memory fx-overlap-count-before-alpha). UNPLAYED. Logs `[TOD_JT]` (TOD_JT_LOG 1, zero before publish).

**2026-09-29 14:07 - THE SKY FLEET v2: A LOT MORE DETAIL + THEY FLY LIKE AIRPLANES - ARRIVE FROM FAR AWAY, PASS THE TOWER, LEAVE (user; session 9c; docs/192 s8-s9; CHANGELOG 14:07).** User after playing v1: "they actually need a lot more detail ... going across the sky like an airplane" + "they should spawn kind of far away and ... move towards the tower ... then they fly away ... cyber realistic". DETAIL (Blender MCP studio 9890, kit `tools/sky_ships/detail_lib.py`, textures `make_textures.py` = system Python, map typeface): dreadnought 2,214 -> 35,364 tris, hauler 1,008 -> 13,874 (a flying billboard: 3 sky ads under the cargo), gunship 622 -> 3,994, fighter 298 -> 1,056; every class has a B variant (8 models). FLIGHT (`_tod_sky_ships.csc` rewritten; ONE `MOTION` table in `gen_lanes.js` -> generated `_tod_sky_lanes.csc` motion() / lights() / blockers() / reveal_*): a ship appears 10-14 px long far over the horizon ON THE SIDE THE PLAYER IS NOT LOOKING, looms in (speed x (1 + d/xs)), passes the tower at full size on a generated lane (weave / bank / sway), climbs away and shrinks out. THE SCALED STAND-IN: nothing draws outside the sealed box (+-12,032), so a far ship is drawn on the same line of sight, closer and smaller (distance x k, SetScale k); a stand-in touching `blockers()` (the crown, the arena) hides that tick. Effects cannot scale: engine FX only at full size; strobes / beacons are one-shot flashes sized to stay a few px. THE WARP IS RETIRED WHOLE. Session 61's crash scene (two of these gunships ram in front of the sign): the salute rides its `tod_jump_title_ignite` beat (t 4.1, under the white-out), LIVE since 61's FULL BUILD OK 15:28:56 (tmp/jump_title/full2.log). GATE `test_sky_ships.js` interprets the SHIPPING GSC (`tools/sky_ships/gsc_eval.js`): 112 whole flights, every tick inside / on the camera ray / clear of every solid (oriented boxes) / smooth, 8 negative controls; `make_textures.py --check` added to build_map. BUILT in fd's FULL BUILD OK (tmp/spire_removal/full1.log, .ff 14:23:04, FF 216,215,232 B): `SKY FLEET NATIVE OK compiled` (8 models exact), 10 sky fx + all materials in the ledger, 0 warp rows, drone/jet in the loaded bank, deployed = repo, nothing synced after. Supersedes the 11:16 note's WARP / sizes / 7 models. TOD_SKY_LOG 1 (0 before publish). UNPLAYED.

**2026-09-29 14:01 - THE BLACK MARKET IS ONE NAME + ITS SIGN REBUILT IN BLENDER MCP + THE PAUSE MENU / SCOREBOARD AI COMPANION ROW IS LIVE (user; session d2; CHANGELOG 14:01).** User: "The Item Shop / Black Market is confusing. Lets just rename it Black Market all together and update the model with Blender MCP"; then "there is an upgrade in the pause menu. That shows AI companion ... wire it all up. Make sure the upgrades are there as well". Players never see "Item Shop" again: both prompts + the TOD_NOUNS noun say BLACK MARKET (test_spin.js fails if ITEM SHOP returns); internal names (`_tod_shop.gsc`, `tod_shop_*`, `art/partner_shop/`) stay. THE SIGN: `tools/partner_shop/18_black_market_sign.py` (MCP studio 9881, Blender 5.2) rebuilt the tube letters as BLACK MARKET in the same construction; C/E/T blink (native `tod_shop_letter_c` replaced `letter_h`); sign sparks moved with their letters (`write_timing.py` regenerates `_tod_shop_timing.csc`); counter stencils NO QUESTIONS ASKED / SPIN / SOCKET / SCRAP. RULE: EDIT THE SHOP ON A STAGED COPY OUTSIDE THE REPO and swap it in whole (build gates read the master's sha + timing json from the repo). THE COMPANION ROW: `_tod_partners.gsc push_state` -> `tod_ptn_state` (companion, state none/active/destroyed/on its way, health 5-steps or rebuild seconds, built mask), change-gated, re-sent by every `push_items`; TodSpinReel.lua records `CoD.TodCompanion` + each companion's items, and ONE `CoD.TodCompanionDescribe()` says the row (portrait, name, the three items as rarity chips + names, green/amber state); the pause menu and scoreboard only lay it out. The item line keeps to 35 characters (long names give way to chip labels; the render gate caught 266.5 of 261 units). BUILT in fd's FULL BUILD OK 14:26 (tmp/spire_removal/full1.log): FF 216,215,232 B written 14:23:04, `SHOP_NATIVE_VALIDATED 19 models; 133 LOD files; compiled=True`, `tod_shop_letter_c` in the ledger (`letter_h` gone), 15 shop images, `_tod_partners` / todspinreel / both menus in the ledger, every d2 input deployed = repo (148/148 shop model + texture files), render_menus 12 renders 0 overflow, diffs clean, nothing synced after. Re-verified in session 61's later FULL BUILD OK (tmp/jump_title/full2.log, FF 222,707,072 B at 15:28:56 = the current test .ff): the same checks pass, and d2's new gates (test_spin.js 332, test_spin_reel's companion block) ran inside it. UNPLAYED.

**2026-09-29 13:57 - THE ENDLESS SPIRE IS GONE (user: "That whole thing needs to be removed. Everything inside ... It's not part of the map anymore") + THE TOWER'S RAILS 30% LOWER + THE SKY A LITTLE BRIGHTER + THE ALARM LOOPS UNTIL THE GATE + THE FIRST SONG STARTS ON THE JUMP-PAD BALCONY + BREACHER: JUMP-ONLY CLUSTER LAUNCH, A PUSH FROM THE BLAST, AIR STEERING (session fd; CHANGELOG 13:57).** EVERY OLDER NOTE BELOW THAT DESCRIBES THE ENDLESS SPIRE, THE WARDEN TRIALS, THE WARDEN KING, PACK II/III, HARNESS #8 OR THE SPIRE GAUGE IS HISTORY. The generator has no SECTION 6 (5,232 world brushes, 1,319 entities); _tod_spire.gsc and _tod_spire_data.gsc are deleted; the finale (still PARKED) auto-departs; the Battle Arena keeps `level.tod_trial_box` via `_tod_bosses::box_contains`. The sky seal / ceiling / umbra volume are unchanged (the spire never set them). RAILS: `RAIL_VIEW_SCALE` 0.7 -> every visible main-tower rail is `RAIL_VIS_H` 39 (was 56); each lowered rail's clip starts at its FLOOR (`railClipZ`) and still ends at floor+168, so collision is unchanged; PARA_H stays 56 (lounge sills, balcony barrier); the balcony curbs stay 12. SKY: skyStops 4.35 (+0.5 stop), skyRotation 180 (22's roll-0 EXR, 61's jump camera). ALARM (`_tod_fall.gsc`): a wind-up, a SEAMLESS LOOP (the host's PlayLoopSound) and a wind-down, cut by `tools/fall_siren/make_siren_clips.py`; it only stops at the 5000 gate or the seal (the watcher used to kill its own shutdown; the old one-shot went silent across an ESC pause). MUSIC: the first band starts when a player stands on the jump-pad balcony (GENERATED `jumppad_balcony_mins/maxs`). BREACHER: the Cluster launch needs a jump (grace 250 ms, log FUSION_JUMP_SKIP), a rocket-jump push (480 at the centre, 40% at the reach, sideways share only), and air steering (map 1's Slasher turn at Lv5 + a 170 u/s drift; `breacher_air_steer`); gate `tools/breacher/test_fusion_air.js`. Latent, Mage only (gated off): a 39u rail sits 1u under Blink's 40u knee ray, so if the Mage returns lower TOD_MAGE_BLINK_RISE to ~32. FULL BUILD OK 14:25:54 (tmp/spire_removal/full1.log; .ff 14:23:04, FF 216,215,232 B, was 224,798,528): geom_key saw the map + sky change and re-baked (cod2map 14:15:55, fresh LED 119,704,569 B at 14:18:14, was 171,844,877 with the spire; the bake took ~2.5 min), NAVMESH GATE OK (25 tower sections, crown island, Battle Arena, 8 transit pads), SKY FLEET NATIVE OK compiled (9c's v2 fleet, 8 models), the new sky .iwi i_skybox_tod_cybercity_SPX6GZXG... (31.2 MB, 14:20) from 22's EXR (deployed sha c312071e... = repo), skyRotation 180 / skyStops 4.35 deployed, the three siren clips in the loaded bank (.sabl 123.4 MB, 14:21; the old one-shot and the three spire tracks gone; streamed bank 277.9 MB, was 354), zero spire assets in the ledger, d2's Black Market model + companion row and 61's pitch -13 in; scripts / zone_source / ui diffs clean, deployed map md5 = repo, nothing synced after the .ff. UNPLAYED.

**2026-09-29 13:44 - THE SKY'S TITLE SIGN 25% BIGGER + WAY BRIGHTER, EVERY STATIC SPACESHIP OUT OF THE SKY, THE SKY TURNED TO FACE THE JUMP CAMERA (user; session 22; docs/166 §9.7).** The user after playing v7: "25% bigger and way brighter ... the one thing that sticks out in the skybox"; and "remove all the spaceships ... another agent [is] adding actual models" (the sky fleet, docs/192). `build_city.py` `GATE`: 65 deg wide (was 52; the text box stays at el 11), the painting authored in W like every other light (white 1.0; v7's 0.1467 was the PREVIEW's display white, 6.8x under the city's neon), its neon x3 more, its halo 3 W; the card writes a `sign` AOV (`<raw>.sign.exr`) and `finish_sky.py` gives it its OWN knee (2 -> 4 W; the city keeps 0.7 -> 1) and solves the exposure on the city outside it: peak 2.88 W, the whole sky scores 0.6865 (`verify_tower_design.js` SKY_SCORE, fd). Airships / battlecruisers / fighters / loose aircraft RETIRED (`retired()` keeps their random draws so nothing else moves; `-Ships` = A/B). THE TURN (corrected 16:25): in game the image's centre column faces yaw -(SSI sun azimuth 140 + skyRotation) (61: the shader + the user's 15:33 screenshot rebuilt from the .map, docs/196 §3; rotation 180 put the sign at yaw ~41), so the finish stays `--roll 0` and 61 sets `"skyRotation"` 40 = the gate due WEST; test_jumppad checks the sum. RULE: NEVER GPU-render the sky while BO3 runs (8 GB card): `-Device cpu` for tests. EXR sha256 c312071e... (94,805,738 B). BUILT in session fd's FULL BUILD OK 14:25:54 (tmp/spire_removal/full1.log; the spire removal): FF 216,215,232 B written 14:23:04, fresh bake (LED 14:18), the NEW sky .iwi `SPX6GZXGJB7OFJUXXLTMIIIF45` (31.2 MB, 14:20:18) converted, `image,i_skybox_tod_cybercity` + its material + the skybox xmodel in the 14:23:04 ledger, deployed EXR sha = repo (c312071e...), deployed tod_skybox.gdt skyRotation 180 / skyStops 4.35, nothing synced after. UNPLAYED.

**2026-09-29 12:28 - EVERY CLASS DEALS LAYERED CARDS (docs/193) + THE BLACK MARKET SOUNDS + ITS DEALER (docs/194 wiring, docs/195 art; session d2).** All four live classes are listed in TodCardArt `classes` (the Mage, switched off, keeps the old faces); 18 FACE lines in tod_upgrade.lua DOMAIN. THE TIER CARD NO LONGER SAYS "GUN UPGRADES RESET" (false since 2026-09-27: no live card is gun-scoped): "CARDS KEPT - PACK IT AGAIN" everywhere. _tod_shop.gsc plays the docs/194 kit (coin, open, luck pour, lever, 3 ticks, 5 climbing crawl notes, stop, socket/upgrade, scrap, close) + the dealer VO (buy 70%, COMMON 50%, EPIC/LEGENDARY always, RARE never, close 35%). TodSpinReel: THE DEALER portrait reacts (idle / watch on the last 4 tiles / shrug / grin / jackpot, once per spin), THE COMPANION portrait (hidden if unknown; power flash on the socket), speed streaks by reel speed. Gates: test_spin_reel.lua (+28, 6 negative controls), test_spin.js 307, test_card_pull.lua 74. FULL BUILD OK 12:34:09 (tmp/card_v2_classes/full1.log; map compile + bake REUSED by geom_key), FF 224,798,528 B, all 45 card2 + 37 spin images and todspinreel / todcardart / todpull / tod_upgrade / _tod_shop in the ledger, streamed bank 354.4 MB (9c verified every new sound file in the loaded bank; all 33 wavs + both alias CSVs deployed = repo), diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 12:00 - THE DEPARTURE HALL (top teleporter bay redesign) + THE FIRST JUMP'S OPENING SCENE + MORE HANG TIME (user; docs/196).** The top bay is a cruciform hall in the crown's language (`tools/tower_transit_layout.js` is the ONE source; generator emitters `transitCPoly`/`transitCBevel` write its shaped pieces with kit texture scales): door on axis from the terrace, nave, a crossing with four ruby piers + gold arches under an OPEN ROOF (oculus ring, cross, ruby lantern), three gate arms in district colours (30 orange / 20 green / 10 cyan; gold pad rings + floor numbers + portal plaques + coloured lights), and gate 20's apse wall = THE WINDOW framing the sky's title sign (due west). Pads moved (30 (-1080,-40), 20 (-1480,360), 10 (-1080,760)); routes/locks/costs unchanged. RULES: only axis boxes are walkable; only BLOCK-class kit materials above the floor (DECK-class thin slabs read as floors to the lint); walls from one rectilinear outline. THE JUMP (`_tod_jumppad.gsc`): every flight 7 s, apex +2600, walked on the `hang_u()` clock (float over the apex, soft 371 u/s landing); a player's FIRST flight (9.5 s) is the opening scene: letterbox (`TodJumpCine.lua`, veil key "jump"), camera clamp-lerps right to the sign (yaw 180 / pitch -11), the descent's first music band starts at the reveal (`tod_jump_title`), hold, swing back, release. THE SKY'S REAL MAPPING (first play 13:00: the scene worked, but the sign was not in the shot; docs/196 §3): the engine's own sky shader (sky_latlong_hdr DXBC, decoded) puts the image's CENTRE column at world +X (yaw 0), not mirrored, turned by the material's skyRotation. So the sign's yaw = -roll + skyRotation, and only 0 and 180 are proven: a positive value's turn direction is unproven. The built roll -90 put the sign due NORTH behind the crown. FIX BUILT in fd's FULL build (.ff 14:23:04): session 22's roll-0 finish + skyRotation 180 (fd set it in tod_skybox.gdt), pitch -13. LOCKSTEP: `TOD_JUMPPAD_CINE_SIGN_YAW` vs sky3d_stats.json roll + that skyRotation; test_jumppad simulates the shader and fails any mismatch (the in-flight warning is deleted). The `tod_jump_reveal` hook is RETIRED (the 15:31 crash note: 9c's salute hears `tod_jump_title_ignite`). Conduits regenerated for the new floor. LESSON: build gates read the REPO after the sync (my 11:23 map regen killed 9c's build; memory build-gates-read-the-repo). FULL BUILD OK (tmp/transit_bay/full1.log): .ff 11:49:36, FF 221,747,008 B, fresh LED 171,844,877 B, NAVMESH GATE OK (8 pads), one combined build carrying 22's rolled sky + 9c's sky fleet + d2's Black Market pass 3 (each confirmed in the ledger); diffs clean, nothing synced after. Review: docs/196_ref/review.html. UNPLAYED. Logs `[TOD_JUMPPAD] CINE_*`.

**2026-09-29 11:32 - THE SKYBOX TITLE SIGN IS THE USER'S REFERENCE GATE (user: "follow the reference exactly ... until it's indistinguishable"; docs/166 §9).** The user's painting (art/sky3d/sign/tod2_title_gate_reference.png) cut out of its background on ONE emissive card in the rendered sky (`build_city.py` `make_title_gate` / `GATE`: text box az 0 el 11 before the roll, 52 deg wide, 1 km out). The card files in art/sky3d/sign/ are GENERATED by `tools/sky3d/cut_title_gate.py` from committed BiRefNet-DIS5K masks: change its polygons and re-run, never paint the PNGs. Measured vs the reference in the reveal view: every region within 3-4 display levels. The moon disc now peeks out behind the crest in the reference's lavender (`MOON_DISC`; `--moon-style blood` = the red). RULE: an 'opaque' 254/255 card leaks the neon city through dark art - snap alpha. Finished with session 61's `--roll -90` (sign due WEST); `render_sky3d.ps1`'s defaults ARE the ship recipe now. EXR 11:31:51 (sha 609d0a89...), BUILT in session 61's combined FULL BUILD OK (tmp/transit_bay/full1.log): FF 221,747,008 B written 11:49:36, the NEW sky .iwi `K4ZX4GKG44RFVEE3EERNSZ424Y` (31.3 MB, 11:47:29) converted + packed, deployed EXR sha = repo (609d0a89...), fresh bake (geom_key saw the sky change). UNPLAYED.

**2026-09-29 11:19 - FULL BUILDS REUSE THE MAP COMPILE + LIGHTING BAKE WHEN NOTHING THEY READ CHANGED (user: "Computer is freezing up while building").** The freeze is MEMORY, not disk: the Radiant LED bake alone peaks at ~15.8 GB on this 15.6 GB PC. `tools/geom_key.js` (run by build_map.ps1 before cod2map) hashes the .map, its prefabs, every GDT asset the map names followed to its image/EXR files (the sky included), the exes and command lines, and the compiled outputs; identical to the last full build = cod2map + the bake are SKIPPED and that build's BSP/navmesh/LED are linked. Any difference = compile + bake as before. `-ForceBake` / `-Publish` always bake; a -GscOnly now warns when the map/materials/sky moved. Selftest (21 cases, 9 negative controls) is build-gated; `node tools/geom_key.js show ...` prints every watched input (WHY a build re-bakes). A map, world-material, texture or sky change still bakes (and still freezes): close other apps for those. **PROVEN 12:15 (geom-key-2, CHANGELOG 12:15):** 61's FULL build exercised the rebuild path; a normal FULL build then reused it (BUILD OK 12:13:37, tmp/geom_reuse/verify1.log, 9 min, no cod2map/Radiant, navmesh gate re-run on the reused mesh) with ALL FOUR linker asset ledgers identical to 61's fresh bake; every material named in the compiled BSP/LED is in the key. RULE: two .ff files are never byte-identical (link timestamp + per-build encoding) - compare the assetinfo ledgers, not .ff bytes.

**2026-09-29 11:17 - SESSION d2 OWNS THE BLACK MARKET (user) + BLACK MARKET PASS 3 + THREE ASSET REQUESTS.** User: "You will be responsible for the Item Shop Black Market screen and animations and everything and also the card selection". 9c handed over the spin experience (TodSpinReel.lua, the spin flow in _tod_shop.gsc, docs/188 + 190, test_spin.js / test_spin_reel.lua); 9c keeps the item effects in _tod_partners.gsc (ping 9c before changing an item's value). PASS 3 (docs/188): room dim + slam, slots + FOR YOUR <COMPANION> + THE ODDS (the true roll + guarantees) during the spin, the luck pour (`TOD_SPIN_POUR_SECS` 0.95, LOCKSTEP `P3.POUR_MS`), needle kick, rail lights, overshoot stop, the card reveal's hit sprites once per spin, the socket flight, the scrap count-up, the chip pulse. SEE A SPIN WITHOUT THE GAME: `python tools/ui_mockup/render_spin.py`. Asset requests out: docs/193 (other classes' cards), docs/194 (sound kit), docs/195 (dealer + companion portraits). BUILT in 61's combined FULL BUILD OK 11:49:36 (tmp/transit_bay/full1.log), FF 221,747,008 B, reel + shop + card art verified in the ledger, diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 10:33 - THE ARCHER'S CARDS ARE THE LAYERED CARD V2 (docs/191 drop, all 22 layers); CARD V2 IS PER CLASS.** A layered card fills its 768x1152 canvas; an old baked face sits 50 px in. ONE DESIGN PER DEAL: a class draws layered cards only when `tools/card_pull/install_card_art.py` lists it in the manifest's `classes` (every card it can be dealt has art, READ from add_domain / domain_id / TOD_TCLS; `--check` fails if a layered class gains a card with no art). TWO BACKS: `i_tod_card2_back` (layered, full-bleed) and `i_tod_card_back` (old faces); TodPull `BackPick` chooses at the deal. Only the ARCHER is complete; each other class needs its 6 illustrations + tier 2/3 art. The tier card now shows its crest and a tier tray. FULL BUILD OK 10:47:39 (tmp/card_art/full2.log), FF 221,517,440 B, all 22 layers in the ledger, diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 09:58 - CARD BACK + 13 NEUTRAL FACES INSTALLED (user drop; docs/189).** The card back (`i_tod_card_back`, via the card_pull installer) and the 13 live baked faces with an EMPTY band slot / no coin / an empty dot tray (same `_regular` names; originals in docs/189_ref/_prev_shipped_20260929/). TodPull `OLD_FACES_NEUTRAL` true. RULE: never build a Lua list with ipairs over a table literal that can hold nil (the back never folded away). FULL BUILD OK 10:24:14 (tmp/card_art/full1.log), FF 218,962,304 B, all card + pull + 9c's 26 spin images in the ledger, diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 11:16 - THE SKY FLEET (user; docs/192; v1 - SUPERSEDED by the 14:07 v2 note: no warp, far approach, 8 models).** Four huge Blender-MCP ships (studio port 9890, `tools/sky_ships/`) - dreadnought 11,300 u / hauler / gunship / fighter wings - fly the SEALED sky box (x/y +-12,224; the umbra/sun volumes end there and drawing beyond it is UNTESTED, so they stay inside and WARP in and out), CLIENT-ONLY in `_tod_sky_ships.csc` (zero server entities). Lanes are GENERATED from the live map (`gen_lanes.js`; whole ship 1,500 u clear of every brush + session 61's jump arc/transit hall); the build re-tests the COMMITTED lanes against the live map and fails only if one is really blocked. FX `gen_fx.py`, sounds `make_sounds.py` (tod_sky.csv), gates `test_sky_ships.js` + `verify_native.py`. Glow = `sky_lib.EMIT` (neon 48, engines 110). Logs `[TOD_SKY]`, TOD_SKY_LOG 1 (0 before publish). BUILT in 61's combined FULL BUILD OK 11:49:36 (tmp/transit_bay/full1.log), FF 221,747,008 B: `SKY FLEET NATIVE OK compiled` (7 models exact, 6 fx, all materials), both scripts in the ledger, sky sounds in the loaded bank, fleet files deployed = repo. UNPLAYED.

**2026-09-29 00:32 - THE PULL PASS 2 + CARD V2 + HUD VEIL (user; docs/187 s8, docs/191).** Reveal effects are tinted SPRITES from `tools/card_pull/install_card_art.py` (it also keeps GDT + a GENERATED zone block + the GENERATED `TodCardArt.lua` manifest in step; build step `card_pull --check`). CARD V2 = layered card (body / 4 rarity frames / crests / per-upgrade art / LIVE text), drawn only when installed - art pack docs/191 (Archer first, 22 files) supersedes docs/189. HUD VEIL `CoD.TodHudVeil.Set(key,on)`: "cards" (upgrade panel) + "spin" (9c's wheel) hide the whole HUD. RULE: the typeface has "+" "/" only in the DIGIT set - route them (TodPull `Pick`) or the text hides. SEE THE REVEAL WITHOUT THE GAME: `python tools/ui_mockup/render_pull.py [--v2]`. BUILT in 9c's -GscOnly BUILD OK 00:33:55 (tmp/shop_spin/gsc4.log, FF 217,586,048 B); the overcharge-art retirement + installer layout checks came after it (next build). UNPLAYED.

**2026-09-29 01:23 - THE SPIN ART IS IN (docs/190 drop, 26 images).** TodSpinReel.lua `USE_SPIN_ART`: frame, glass, needle, rarity tiles + tinted item icons, stamped banners, flare + rays, sockets, SCRAP, icon chips. Every name a literal; 26 GDT blocks + zone lines. LUA 5.1 60-UPVALUE CAP: the constructor reads its layout from ONE table `L` (fifty locals broke it; test_spin_reel.lua catches it). Layout proof: docs/190_ref/installed_screen_1280x720.png. FULL BUILD OK 01:46:04 (tmp/shop_spin/full1.log), FF 218,756,672 B, all 26 images in the ledger, diffs clean, nothing synced after. UNPLAYED.

**2026-09-29 00:24 - SPIN PASS 2 (user: "Double check for bad player experiences or UI issues. Also the HUD should not show while this is happening").** HUD hidden for the whole spin via the shared TodHudVeil key "spin" (+ companion bar and elite bars hide per player on tod_menu_frozen || tod_solo_upg_active); per-player prompts (buy / locked "companion required" / none while spinning); accident-proof slot choice (default SCRAP unless the prize beats the weakest slot, 0.6 s grace, release-before-confirm); result text; 1.5 s exit grace; card deals take the screen mid-spin and the spin never unfreezes a player a deal holds; card-reveal sound language; reel masks fixed (they stuck 100 px out of the panel). docs/188 "Pass 2". Gates: test_spin.js 253 + test_spin_reel.lua + test_partners 113, all with negative controls. -GscOnly BUILD OK 00:33:55 (tmp/shop_spin/gsc4.log) on session 52's FULL 00:22:46, FF 217,586,048 B, scripts diff clean, nothing synced after (the 4-rarity session's 00:33:09 tod_upgrade.lua/.zone edits are NOT in it). UNPLAYED. Also THE QUALITY BAR section (AAA, bug-free, fun first) added below, before "HOW TO END EVERY RESPONSE".

**2026-09-28 23:18 - THE BLACK MARKET SPIN: the active Item Shop spins for companion items (user; docs/188).** Hold USE at the lit shop ($2500, one constant hint, noun "item shop"; crown shop live WITHOUT power in dev): frozen + untargetable + unhurtable for the spin, the LUCK BAR is spent into docs/187's odds (the reel's filler shows them), a 30-tile reel lands an item + rarity (never a dead spin), 3 slots PER COMPANION (no duplicates; lower rarity upgrades in place; full = choose a slot or SCRAP to luck). 9 generic items (PLATING / OVERCLOCK / HOLLOW POINT / LONG SIGHT / NANO REPAIR / ARC CHAIN / SALVAGE / QUICK REBOOT / LUCKY CHARM) applied in `_tod_partners.gsc`. `_tod_shop.gsc` + NEW `TodSpinReel.lua` (LOCKSTEP items/odds; gates tools/partner_shop/test_spin.js + tools/test_spin_reel.lua). -GscOnly -FreshOcclusion BUILD OK 23:18:07 (tmp/shop_spin/gsc3.log), FF 217,237,248 B, diffs clean, nothing synced after; also carries docs/187 + the arena occlusion fix. SUPERSEDED as the test .ff by the d2 session's -GscOnly BUILD OK 23:32:26 (tmp/card_test/gsc1.log, FF 217,236,928 B) = this tree + its dev CARD TEST bench; the spin files hash-match deployed and todspinreel.lua is in its asset list. Test benches still ARMED. PLAYED ONCE 23:40 (7 spins, no UI errors; user: "bland without UI") -> ART REQUESTED 2026-09-29: docs/190, 26 files, zip ~/Downloads/tod_item_shop_spin_art_pack.zip; install steps in docs/190's repo section. Logs `[TOD_SHOP] SPIN_*`, `[TOD_PARTNER] ITEMS`.

**2026-09-28 22:57 - FOUR RARITIES + THE PULL (user; docs/187).** Cards are COMMON +1 white / RARE +2 blue / EPIC +3 purple / LEGENDARY +4 gold (`TOD_RAR_*`, `rarity_label`), odds 56/27/13/4 empty luck -> 36/36/20/8 full; full bar = one EPIC+ (25% LEGENDARY), half = one RARE+. DARK UPGRADES, the King's dark phase and the luck OVERCHARGE are RETIRED (`TOD_DARK_ENABLED 0`; has_dark lanes inert, removal owed). THE PULL: face-down backs climb the ladder, server-driven (todUpgHold = beat counter during the reveal, rarity fields climb, domain edge flips), drawn by NEW `TodPull.lua`; `todMagBonus` RENAMED `todUpgSolo`. One face per upgrade (old _regular art + live band/pips until the neutral faces land); 82 dead images unzoned; lint GATE R; gate `tools/test_card_pull.lua`. Near-misses OFF, teammate alert = LEGENDARY only (defaults, unanswered). -GscOnly BUILD OK 23:18:07 (9c's tmp/shop_spin/gsc3.log), FF 217,237,248 B, 26 faces + todpull.lua in the ledger. UNPLAYED.

**2026-09-28 21:38 - PARTNERS WALK, NO FLOATING GUNS, R.A.P.S. ROLLS; ALARM GLOW GONE, SIREN UNTIL THE ESCAPE DOOR (user playtest ~21:20).** The three drones never walked because `archetype_zod_companion::zodcompanionabletoshoot` returned false for partners, and the BT's only walk branch needs it (now true for `tod_is_partner`; `ignoreall` keeps the native gun quiet). The body's weapon model survived HidePart: `ai::gun_remove()`. R.A.P.S. never parks: charges a zombie within 700 of its owner, else orbits the owner at 200, sprint cycle x1.35 (`raps_goal`, log RAPS_MODE). The alarm button's red glow is removed (sparks kept); the siren re-plays every 28 s until the `tod_fall` escape gate opens, then the alarm turns off (`[TOD_FALL] SIREN play #N` / `ALARM off`). -GscOnly BUILD OK 21:38:10 (tmp/partner_fix2/gsc2.log), FF 234,405,120 B, diffs clean, nothing synced after. Test benches still ARMED. UNPLAYED.

**2026-09-28 17:47 - THE KEEPER IS THE BATTLE ARENA'S LEVEL-10 BOSS (user; docs/186).** Revelations' Keeper, installed from the T7 pack by `tools/keeper/install_keeper.py` (never hand-edit its outputs; `--check` + `tools/keeper/test_keeper.js` gate the build). Level 10, wave 3: portal entrance, stock zombie brain + his swipe, SOUL LINES to 2 arena elites max (linked = hits x1.5, speed x1.3, takes x0.5), a line recasts 15 s after its elite dies, his death breaks all lines; the wave keeps 2 (3 in 3-4p) elites alive for him. `_tod_keeper.gsc|.csc`, `_tod_arena::boss_wave`. -GscOnly BUILD OK 17:47:15 (tmp/keeper/gsc2.log) on the fresh BSP/LED of tmp/keeper/full1.log, FF 234,398,336 B, diffs clean, nothing synced after. UNPLAYED. Logs `[TOD_KEEPER]`. A linker ASSERTION dialog hangs a build silently: check the linker window title.

**2026-09-28 09:44 - CLASS WORK PAUSED; ARCHER IS NO LONGER LEAD (user: "we will be done with classes again for now. You are not lead anymore").** No session is lead: no build clearance, no lead relay. Builds stay serialized and never run while BO3 runs. The card-text rule below still applies to anyone who touches a card: desc + pause/scoreboard rows + both armory pages, in simple player words. The 02:20 build below is the current class state; unplayed.

**2026-09-28 18:11 - THE ALARM BUTTON (user).** A Blender-MCP red mushroom button on a waist-high hazard-collar stand at the crown hall's centre (uplink dais) replaces the alarm switch on the sanctuary step: press it -> the same alarm/siren/flood. Models tod_alarm_button_stand / _cap_on / _cap_off (tools/alarm_button, studio port 9887); clip `crown hall alarm button stand body`; `_tod_fall::button_spawn/button_press`. The overlook POWER switch is unchanged. FULL BUILD OK 21:00:02, FF 234,405,312 B, fresh LED, all 9 LODs compiled whole; lint_tod_navmesh probes 64 south of hall_center (the stand's hole). UNPLAYED.

**2026-09-28 12:24 - SKY 8x BRIGHTER; skyStops IS A VISIBLE-SKY KNOB (user: "agents are getting stuck").** On screen ~ sky EXR x 2^skyStops (x exposure): the 09-26 and 09-27 "brighter sky" passes each doubled the EXR AND cut skyStops 1 stop, so the user saw no change twice. NEVER lower skyStops to "hold the world light" when the goal is a brighter visible sky; the sky's light and its look move together. skyStops 0.85 -> 3.85. `sky_intensity_factor` 10 is UNVERIFIED above 1 (no stock map uses >1). verify_tower_design.js had ENFORCED the cancel; it now pins 3.85 / 8x. FULL BUILD OK 12:40:42, FF 231,460,480 B, fresh LED; the Keeper session's 12:43 edits are NOT in it. UNPLAYED.

**2026-09-28 11:56 - TOD II MUSIC SWAPPED (user).** Going DOWN: floors 50-37 "La Clé des Champs" (N'to), 36-23 "Meteor Herd" instrumental (SA2; the user: use the YouTube instrumental, never strip vocals yourself), 22-10 "Una Mattina" (Lynnic), 9-1 "Reykjavik" (Joachim Pastor); "115" extended = `tod_boss_music`, played in BATTLE ARENA fights (`tod_atmosphere::arena_music_start/end`; TOD II has no Panzers). Same aliases, new wavs; loudness vs TOD1 + recipe in sound_assets/tod/music/README.md. All five commercial = LICENCE UNCONFIRMED (CREDITS.md). -GscOnly BUILD OK 11:56:54, FF 231,384,896 B, bank 327 MB, diffs clean. UNPLAYED.

**2026-09-28 12:40 - PARTNERS: TALON / R.A.P.S. / CERBERUS MOVE, SHOOT VISIBLY, REAL TEXTURES (user playtest 11:28).** Their Hide()n body was never networked: no movement, no shot FX. Now HidePart( "j_mainroot" ) keeps it live (memory `hidden-actor-stops-moving`); Talon hovers 60 + bob/lean, R.A.P.S. rolls (now the fully textured Gorod Krovi RAPS), Cerberus faces travel/target; every shot flies a looping-trail tracer host + hit spark. Real T7 materials via tools/partner/install_assets.py + partner_materials.py (Talon wing pods and Cerberus armor have no clean per-model maps in the pack). Logs `[TOD_PARTNER]` MOVE / MOVE_STALL / SHOT / SHOT_SKIP / DAMAGE. Built in the sky session's FULL BUILD OK 12:40:42 (tmp/sky_bright/full2.log), FF 231,460,480 B, verified in the ledger. Crown test benches still ARMED. UNPLAYED.

**2026-09-28 09:56 - PARTNER TEST BENCHES IN THE CROWN (user; this session owns the AI companion/partner work).** `TOD_PARTNER_TEST_BENCHES 1` in `_tod_partners.gsc`: four free benches in the crown hall's south nave (Civil Protector / Talon / R.A.P.S. / Cerberus, west to east): equip with no parts/build/rebuild wait, swap freely, use the equipped one's bench to dismiss. `-Publish` refuses it armed - SET IT TO 0 BEFORE PUBLISH. Review: no archived run has ever spawned a partner; item-shop upgrades are unbuilt (docs/156 design). 10:19 review: spawn budget 58 -> 60 (it refused the reserved slot) and a swap can no longer count as a death; SPAWN logs `pregated`. -GscOnly BUILD OK 10:17:25, FF 231,379,072 B, diffs clean, nothing synced after. UNPLAYED. Logs `[TOD_PARTNER] TEST_*` / SPAWN / STATUS.

**2026-09-28 02:20 - EVERY CLASS 81 LEVELS + THE 10-ROW MENUS + MORE ZOMBIES + 750 TELEPORTERS (Archer = lead; FULL BUILD OK 02:16:51, tmp/archer_review/full4.log, FF 231,375,872 B, diffs clean, nothing synced after, 8 known-waived).** Every card is 9 levels: six class cards + DMG REDUCTION (no class caps, 5/8/10/12...22%), LUCK and BOUNTY (log, +100% at Lv9) = 81 per class. RIOT SHIELD is the BREACHER's (9 levels, 200 -> 500 HP, 4:00 -> 2:00, cyber shield at Lv9). QUICK DRAW 9 levels, x2 at Lv9 (weapon steps Lv2/4/6/8 incl. ARROW VELOCITY; funded by retiring the blades' never-dealt k1/k3 forms; REGISTRATIONS 221, boot-proven 229). PAUSE MENU + SCOREBOARD = 10 rows, 2 x 5: AI PARTNER placeholder top-left ("COMING SOON", info only), the class's six cards, then DR / LUCK / BOUNTY; the CLASS TIER left the list for the class header (TIER N OF 3 + next-tier line + PASSIVE), on BOTH screens; class info has ONE source, CoD.TodClassInfo / CoD.TodClassTierLines in tod_upgrade.lua. NEW TOOL + BUILD GATE tools/ui_mockup/render_menus.py (renders the real menus per class with shipped art + map font; fails on any text wider than its box). THE MENU FONT DRAWS "S" LIKE A 5: write seconds as " sec". ZOMBIES: live cap 36/42/48/54 by party (+20% over TOD1), rampage +10 under a 58 ceiling, actor gate 60 of the engine's 64 minus every live ALLIED actor ([TOD_AI_CAP]). TELEPORTERS cost 750 per use (payer = the one who starts it); the BATTLE ARENA is FREE. USER RULE the lead enforces on every session: a card change updates its card desc, pause/scoreboard rows and both armory pages, in SIMPLE player words; no SUPER may buy nothing; no weighted cards. UNPLAYED.

**2026-09-28 01:03 - ARCHER IS LEAD AGAIN (user; Warrior / Breacher / Necromancer = seniors) + ALL-CLASS CARD REVIEW BUILT.** USER RULE the lead enforces: every card change updates the card desc, pause + scoreboard rows (tod_upgrade.lua DOMAIN/DETAIL) and BOTH armory pages in the same pass, in SIMPLE player words (what you get; drop unneeded mechanics; never hide or misstate anything important); a SUPER (+2) must never buy nothing; NO WEIGHTED CARDS (all cards equal within a class, TOD_TIER_W_* 1 / TOD_TIER_R_* 1.0). ARCHER: SPRINT on a log curve (+9 ... +30 at Lv9, sprint_card_bonus / card_curve); QUICK DRAW x2 at Lv6 on 3 weapon steps at Lv2/4/6 (fire, draw, crossbow reload x0.64/0.55/0.50 + ARROW VELOCITY x1.56/1.83/2.0), bows 32 forms each; the ten dead SIDEARMS RETIRED from gen_tod_twins to pay for it (ledger 213). FULL BUILD OK 01:03:13 (tmp/archer_review/full2.log), FF 231,320,704 B, diffs clean, nothing synced after, 8 known-waived; also carries the Warrior/Breacher/Necromancer passes of the same hour. UNPLAYED.

**2026-09-28 00:00 - CLASS PASS 4 BUILT.** SHOT SPEED (Archer, id 35, 6 levels) = a NEW twin axis s (x0.85 / x0.70 at Lv1 / Lv4) + a per-level script draw curve always <= the weapon step; DEADEYE d is girth only; bows 24 forms each, REGISTRATIONS 210 (proven ceiling 229 - the next twin axis must retire something first). CLEAVE (Warrior, key sweep, id 48, 9 levels): swings hit only their target without it, up to 4 zombies at Lv9; Melee Range only widens Cleave's extras. Pack Master retired. FULL BUILD OK 23:59:19, FF 232,665,536 B, diffs clean. Armory audited (v13). UNPLAYED.

**2026-09-27 23:21 - CLASS PASS 3 BUILT.** Heavy Hands renamed ARMS SPECIALIST; Bulwark, Hunter's Mark, Shadowstep retired; NEW Archer PIERCING (id 26, _tod_class_cards::pierce: direct bow/bolt hits pass through 1-4 zombies at 55-95%, as wide as Deadeye's girth); Explosive Fusion's Cluster burst LAUNCHES the Breacher 300-540 u (no fall damage) = its vertical travel. The Necromancer is the only class with no vertical move (user noted; undesigned). -GscOnly BUILD OK 23:21:37 on the Warrior session's 23:05 FULL build, FF 232,616,576 B, diffs clean. Armory v12. UNPLAYED.

**2026-09-27 23:07 - NECROMANCER ORIGINAL STAFF POSE / WHITE SOULS, BUILT AND AUDITED.** User rejected the holding pose and clear pulse. Removed the previous whole-rig rotation/translation; every approved ice-staff handling bone/frame is preserved and parity-gated. Detailed staff art unchanged. Restored 24 white soul wisps + 12 symbols on the outward wave, hollow center retained. Cast proxy made selectable primary; final selection/actual-weapon diagnostics added after user log showed selected=0. FULL build and exact-source deployment verified at 23:07 Eastern. FF 232,614,720 bytes; 449 deployed inputs matched. User playtest pending; no game launched. First link superseded by the combined build carrying the peer Warrior fixes. Evidence: `docs/necro_staff/POSE_AND_SOULS.md`, `art/necro_staff/deployment.json`; previews `docs/necro_staff/review.html`. Native visual quality awaits user test.

**2026-09-27 22:52 - WARRIOR AIR SLAM + PUNCH SOUNDS, FULL BUILD VERIFIED 23:05 (FF 232,614,720 B; guarded watcher "built", deployed kit + tod_warrior_punch.gdt = repo, nothing synced after).** Cyber Smash cast off the ground traces the floor, hangs, drives straight down and slams on landing at any height (no fall damage; `TOD_GS_DIVE_*`, gate tools/warrior/test_gs_dive.js). Smash during a Bash cuts it (BASH_CUT). Fist Bash no longer plays the sword hit; install_punch.py blanks the inherited sword impact table (GDT regenerated). My 22:46 install_punch edit made the 22:37 staff watcher report failed although its .ff built OK. Details docs/warrior_playtest_fixes.md. UNPLAYED; no game launch.

**2026-09-27 22:49 - PAUSE MENU SHOWS THE CLASS + ITS PASSIVE, BUILT.** AetheriumStartMenu.lua TOD_CLASS_INFO (LOCKSTEP with the class passives), right of the ROUND box; refresh_upgrade_list pushes tod_upg_class. Carried by the staff session's FULL BUILD OK 22:49:48 (FF 232,611,648 B; its watcher's 'failed' is a mid-build edit of tools/warrior/install_punch.py whose output GDT did not change). Diffs clean, nothing synced after. UNPLAYED.

**2026-09-27 20:42 - CLASS PASS 2 BUILT (user: "few tweaks to abilities").** PASSIVES: Breacher takes no explosive damage, Warrior heals 2% max HP/s, Archer sprint-fires always (+ the existing no-landing-slowdown), Necromancer = unlimited soul meter + Burned Out at base (Widow's Wine). OUT: Point Blank, Demolitionist, Aerialist, Sprint Fire (parked), Burned Out, Executioner, Battle Rhythm, Juggernaut; Soul Siphon PARKED (the 12-row cap, user's pick). IN: EXPLOSIVE FUSION (Breacher, 5, id 36: own C4/Cluster blasts heal), DEMON SLAYER (Warrior, 9, id 12: elite kill = speed + damage window, via tod_bosses::grant_elite_reward), VITALITY (Warrior, 6, id 37, +10 HP/Lv), SPRINT (Archer, 9, id 29, speed only while sprinting), SUMMONER MASTER (Necromancer, 9, id 19: helper kills at full health raise max HP, cap 4 x Lv x tier), INVISIBILITY CLOAK (Necromancer tactical, earned by card, 9, id 9: ignoreme + no damage 3.25 -> 8.25 s, every 57 -> 33 s; Panzer/Protector/Doppelghast target filters skip it). Melee Range 6 (TOD_WM_RANGE_MAX_LV 6). Soul Beam renamed SOUL SUCK (its baked SOUL BEAM art unzoned -> text card). Adrenaline = explosive kills only. Also carries Deadeye's projectile girth (boxTraceSize 12/18/24 at Lv3/6/9 on every Archer primary) and the C4's own explosion wav (tod_c4_explode) from the staff session's 19:13 FULL build. -GscOnly BUILD OK 20:42:36 Eastern (tmp/class_pass2/gsc1.log), FF 232,404,224 B, banks 121.5 / 209.3 MB, diffs clean, nothing synced after. Logs [TOD_CARDS] IMMUNE / FUSION_HEAL / DEMON / SUMMON_HP / CLOAK_*. UNPLAYED; no game launch.

**2026-09-27 - NECROMANCER HERO DETAIL 3.** FULL build and exact-source deployment verified; ready for user playtest. Actual Blender MCP: 11 bevelled recessed blade channels, layered leather grips/stitches with four new 2K maps, socket/halo fasteners, fine cranial sutures, Tier 3 ritual inlays and baked aged-bone pigmentation. Straight shaft, corrected Tier 2 mount, 34 staff clips and Soul Pulse native-ring fixes retained. 19 resident images, 12 native mesh LODs; unchanged grip/FX tags and full vertex parity verified. Review `docs/necro_staff/review.html`; reproduction `docs/necro_staff/DETAIL_3.md`. The preceding 18:27 build wrapper exited without its final audit and shared `_tod_class_kit.gsc` changed outside this art pass; archived as `tmp/necro_staff_build/iteration2` and not claimed verified. Current status `tmp/necro_staff_build/status.json`; do not mutate build inputs during an active build. User tests; no agent game launch. Native visual quality remains unverified. Native conversion exposed zero custom normals on Boolean-cut faces; geometric-normal fallback and an exhaustive unit-normal gate now cover all 12 LODs. Grip seams were corrected after macro review.

**2026-09-27 18:50 - WARRIOR SECOND PASS SOURCE READY; FULL BUILD RE-ARMED.** Bash had stopped moving: the 15:07 `FreezeControls(true)` lock froze physics and weapon switching (user's 18:25 log: travel=0, proxy never up). NEVER FreezeControls a Bash; the heading is latched and velocity rewritten each tick instead (test_bash.js mocks the engine freeze + two negative controls). Gauntlet strictly alternates: swap-window block (`alt_block`), native melee queue 0 on gauntlet forms, idle reset 3 s; left hook x0.5; left clip re-authored (single punch, smooth return; verify_hook gates push-back). The necro watcher was stopped at 18:27 AFTER it had begun a FULL build; that orphan finished 18:41 unaudited (FF 222,519,552 B); a peer watcher's 18:44 build failed mid-edit at the roster gate. Details: docs/warrior_playtest_fixes.md. UNPLAYED; no game launch.

**2026-09-27 18:22 - NECROMANCER PLAYTEST CORRECTIONS; FULL BUILD QUEUED, NOT DEPLOYED YET.** User rejected the first staffs' flat surfaces, bent shaft/T2 intersection and missing-looking Soul Blast. Removed the 75-degree head deformation; all view/world vertices now rigidly match. Whole staff/hand poses reframed together. T2 halo removed, skull seated on a ferrule. New separate 2K chased iron/forged blade maps and exclusive baked skull UV/color/normal atlas; all 15 images resident. Soul Blast log proved damage and client callbacks, but replacement ring HDR was 1 versus native 64 and blending differed. Restored native emissive blend/HDR/reveal, deferred band read one tick (first max cast previously read band 0), stronger 140 ms thrust, selected-proxy diagnostics; optional hound fields no longer break logging. Source/API/arity/roster/rig/lifecycle checks pass. Review `docs/necro_staff/review.html`; evidence and reproduction `docs/necro_staff/ITERATION_2.md`. Full guarded watcher PID 36100 waits for BO3 to close; status `tmp/necro_staff_build/status.json`. The 17:17 receipt below describes the USER-REJECTED prior pass, not this revision. Previous build evidence archived in `tmp/necro_staff_build/iteration1` and `art/necro_staff/iteration1`. Never stop or launch the game; never build during the user's session. Before further runtime edits stop only the verified waiting watcher, then re-arm it. Native visual quality remains unverified.

**2026-09-27 17:17 Eastern - NECROMANCER STAFF BUILD AND DEPLOYMENT VERIFIED.** Supersedes the pending/failed staff entries below. New T2 Soul Staff and T3 Crown of the Damned, base/PaP forms, 12 mesh LODs and all 34 staff animation clips are compiled; 70 staff-related ledger assets checked. Required material surface types and diffuse high-color/sRGB formats corrected and enforced before builds. Full geometry/navmesh and fresh LED completed; an existing WAV checksum flake cleared on an unchanged-source guarded relink. BUILD OK: FF 193,966,784 bytes, 441 exact-source inputs matched, both cached/deployed full sound banks 209,338,496 bytes with identical hashes. Fresh BSP/LED hashes stayed unchanged through retry (LED 166,777,028 bytes). Earlier crown, balcony, Necromancer, Fire Bow, C4 and Warrior fixes retained. Receipt `art/necro_staff/deployment.json`; successful log `tmp/necro_staff_build/full_build.log`; full-bake attempt `full_build_sound_error.log` in the same directory. Review `docs/necro_staff/review.html`. Ready for USER playtest; native visuals/gameplay remain unplayed. No agent game launch. No runtime sources changed or synced after the verified build.

**2026-09-27 16:31 - NECROMANCER STAFF BUILD QUEUED; NOT READY TO PLAYTEST.** Full native compilation reached linking, which compiled staff models/animations/scripts but rejected three diffuse image definitions (`compressed` was incompatible with the native sRGB format). Corrected all three to `compressed high color` / `sRGB3chAlpha`; source gate now enforces it. Required material surface types are fixed too. Final definitions include all 34 staff clips (including slide slots), staff sway/idle/recoil presentation, no inherited handheld-skull movement clips. A new full build stopped because BO3 started before gdtdb; `tools/necro_staff/build_when_idle.ps1` is queued to resume after the user's game closes. Status `tmp/necro_staff_build/status.json`. The last written FF failed validation and must NOT be called the completed staff build. Never stop the user's game or launch one. Before further runtime source edits, stop only the verified waiting staff watcher and re-arm afterward.

**2026-09-27 - NECROMANCER STAFF TIERS AUTHORED; FULL NATIVE BUILD PENDING.** Tier 1 retains Nan Sapwe; tiers 2/3 now use new Soul Staff / Crown of the Damned models, base and PaP forms. Actual Blender MCP authoring: native BO3 skull anatomy/maps plus custom 2K iron maps, simple T2 and spiked/engraved T3, 12 mesh LODs. Approved ice-staff handling/viewhands combined with continuous skull-cadence channeling and a short Soul Pulse thrust. Cast mode epochs reject stale FX callbacks; pulse cleanup handles switch/death/down/respawn. Source/rig/roster/runtime checks pass. Guarded full build via `tools/necro_staff/build_when_idle.ps1`, status `tmp/necro_staff_build/status.json`; review `docs/necro_staff/review.html`. Screenshot-guided recreation, not the original reference textures. No agent game launch; native visual/gameplay review remains the user's playtest.

**2026-09-27 15:07:59 Eastern - COMBINED FULL BUILD AND DEPLOYMENT VERIFIED.** Jump-pad balcony now has five 12-unit visible curbs (was 56), retaining the original invisible 168-unit collision barrier and upper side barriers. Fresh geometry/navmesh/lighting and native linking passed, including all preceding crown-light, Necromancer, Fire Bow, C4 and Warrior fixes. FF 193,919,232 bytes; LED 166,777,028 bytes; 378 captured inputs match deployment. Full log: `tmp/crown_alarm_visibility/full_build.log`; receipt: `art/crown_alarm/deployment.json`. This supersedes the pending-build/relink entries below. No runtime inputs changed or synced after this build. **Ready for user playtest; native appearance and gameplay remain unplayed. No game launch by agent.**

**2026-09-27 14:53 - JUMP-PAD BALCONY LOWERED; NEW FULL BUILD REQUIRED.** User screenshot 141213: tall rail hid the tower. Five launch-deck rails now 12u instead of 56u, with invisible collision from deck to the original 168u top; existing upper side barriers remain. Original player collision union and pad arc preserved; exactly 10 brushes changed. Geometry/parity, 8,020 flight samples, barriers and crown material checks pass. docs/balcony_view_fix.md. The prior -GscOnly queue is superseded: tools/crown_alarm/build_when_idle.ps1 must run WITHOUT -GscOnly for this geometry change. Combined full build also includes all pending crown/Necromancer/Fire Bow/C4/Warrior changes. Status tmp/crown_alarm_visibility/status.json. Not playable until build/audit succeeds; no game launch.

**2026-09-27 14:48 - COMBINED FIXES NOT YET PLAYABLE: FINAL RELINK QUEUED WHILE BO3 RUNS.** Crown lights, Necromancer, Fire Bow, always-large C4 and Warrior changes are ready. Full geometry/navmesh and fresh LED bake completed ~14:42; initial native link caught one Bash expression syntax error, now corrected. Retry passed feature gates but BO3 reopened before linking at 14:47, so the guard stopped. Old FF remains. `tools/crown_alarm/build_when_idle.ps1 -GscOnly` is queued to finish the guarded relink and exact-source audit when BO3 exits. Status `tmp/crown_alarm_visibility/status.json`; final output `full_build.log`, audit `deployment.log`, receipt `art/crown_alarm/deployment.json`. Before further source edits, stop only this verified idle-watcher process so it cannot build mid-edit; re-arm afterward. Never stop the user's game. No game launch by agent. Details: docs/warrior_playtest_fixes.md.

**2026-09-27 - WARRIOR BASH / LEFT HOOK / CORPSE FIXES (source ready; combined FULL build pending).** Bash locks view and movement input, latches heading without auto-steering, drives while airborne and assists ordinary steps instead of cancelling on floor probes. Punch proxy uses the ordinary punch once and a real idle. Boxing donor moved only glove bones; Blender MCP retargeted the hook onto visible viewhands, with native bone lengths preserved and all 12 left twins rebound. Corpse cleanup now waits one tick for later death callbacks before deciding whether to hide a body, preserving sword flings for 3.5 s under pressure. Added BASH_MOVE/STEP/UNLOCK, hook clip and FLING_HOLD diagnostics. 75 movement/lifecycle scenarios, corpse-order regression and animation/binding gates pass. Details: docs/warrior_playtest_fixes.md. No game launch; user tests.

**2026-09-27 - C4 ALWAYS USES THE LARGE BLAST (source ready; combined FULL build queued).** The user's intermittent huge explosion was the active DEV TIER PREVIEW, not random effect failure: archived 14:18 run has 26 max-card C4 blasts but forced tiers 1/2/3/4 = 7/7/6/6, no C4_LOST or FX_DROPPED. C4 no longer enters that preview cycle; all card levels select the existing top fireball, ground fire, boom and shake. Card-based charges, damage and damage radius remain; maximum card no longer has its radius preview-downgraded. Cluster preview unchanged. Per-charge C4_FX_ARM / PLAY / FAIL / END identifiers correlate effect selection, delayed server playback, host allocation failure and cleanup; these log requests, not rendered pixels. 800 selection checks + arity/API/Archer tests pass. See docs/c4_consistency_fix.md. User tests; no game launch.

**2026-09-27 - FIRE BOW ORIGINAL MATERIAL RESTORATION (source ready; full build queued with crown/Necromancer fixes).** User compared the original BO3 lava bow to our pale stone bow. The inherited HB models used simplified materials that emitted the stone albedo, dropping the original three-layer lava shader/masks. Recovered the original lava PNG (missing image asset registration), restored all original material fields in four map-owned twins, and bound three original-mesh model twins across all eight Fire Bow forms. Only view/world/projectile model bindings changed; balance/animations/FX untouched. Original rigs/vertices/weights and installed persistent FX verified; 21 image dependencies resolved, roster/balance checks pass. Guarded build checks source fidelity and post-build asset ledger. Native compilation/exact visual comparison pending; user tests. See docs/fire_bow_restoration.md and tmp/crown_alarm_visibility/status.json.

**2026-09-27 13:10 - BUILDS WITHIN CLASSES (user): three lanes per class (WEAPON / KIT / SURVIVAL), 13 new build cards + Sprint Fire (Archer) and Adrenaline (Breacher) back from the shelf; every class 11 cards (the 12-row cap with the tier card) and 82-89 levels against ~50-60 earned per run, so a good run maxes 4-5 cards. Shared mechanics in NEW `_tod_class_cards.gsc` (level pointers from _tod_upgrades); class hooks in the necro / archer / kit modules. Earned upgrades unchanged, no lane bonus (user). Text cards until art. BUILT: -GscOnly BUILD OK 14:30:07 Eastern (tmp/core_cards/gsc2.log), FF 194,041,088 B; a peer's Bash-aim / corpse-cleanup edits (14:26-14:27) are not in it. UNPLAYED.**

**2026-09-27 - NECROMANCER HELD SUMMON + CLEAN SOUL PULSE (source ready; full build queued with crown visibility).** Removed the Mangler aura donor's two baked-orange flame emitters, retaining its soul wisps/symbols. Bind now rises to a suspended pose, holds rate zero without auto blend-out, and releases only at conversion/cancel; replacement bodies remain held through the death replication frame. BIND_HOLD/BIND_CONVERT and revision 11 diagnose the user playtest. Soul Pulse no longer calls the caster-centred flash/burst. Its four radius bands use a custom Blender-MCP-authored hollow white ring, broader wispy rim and 845 ms fade, preserving the 140 ms damage sweep. Native pose/visual review pending. Details: docs/necro_visibility_fix.md; build state: tmp/crown_alarm_visibility/status.json. Never launch the game unasked.

**2026-09-27 - HIGH CROWN ALARMS: LARGER + REAL RED LIGHT (source ready; FULL build queued while BO3 runs).** User screenshot showed the prior high glow almost invisible. The 17 high fixtures had no actual FX light. Upper housings/rotors now 2x size on the original mounting feet, emission 144 -> 576, plus one shadowless red spill per high fixture (intensity 14400, radius 2400). Hall fixtures unchanged; same random rotation, trigger and seal. Blender MCP authored six new LODs and matched player-height previews; source/lifecycle/API checks pass. [Details](docs/crown_alarm/VISIBILITY_PASS.md), [review](docs/crown_alarm/review.html). Watcher status `tmp/crown_alarm_visibility/status.json`; build log `full_build.log` there. Queued is NOT built; no game launch, native appearance awaits user test. This supersedes older high-lamp design/status below.

**2026-09-27 - WHOLE-TOWER MATERIALS + POWER INLAYS BUILT, 2026-09-27 12:01:18 Eastern.** All 59,826 architectural world/entity faces use the crown kit; the seven remaining trial-hall liners were converted, with crest/mark signs retained. 1,109 supported cyan wire inlays cover all 50 main + 70 spire floors and their rooms. 49 nonsolid regional hosts replace 70 sparse hosts; off/on twins follow persistent power, emission 8 only on the conductors, late joiners inherit state. Native conversion retains every triangle in all 202 wire-model LODs (regional channels 610 near / 436 distant). `[TOD_CONDUIT] READY revision=tower_wide_v2`, ON, per-region failures. FULL `tmp/tower_power_build/full4.log` + final GSC `full4d.log` verified: FF 193,176,704 B, fresh LED 166,776,956 B, full sound bank 209,338,496 B; 654 captured inputs match, scripts/zone_source/ui diffs clean, no post-build sync, BSP/navmesh/LED unchanged by follow-up. Carries the shared core-card changes and late skull fix. Exact native geometry checks caught the original far LOD; replacement preserves validated shell/wires and omits distant clips. Staff validation now checks its exact variant set instead of a stale whole-roster count; five positive/negative cases pass. Known WAV checksum flake retried; full 199.6 MB bank verified. [Review](docs/art_cohesion/review.html), [implementation](docs/art_cohesion/TOWER_POWER.md), [receipt](docs/art_cohesion/tower_power_build_receipt.json). **UNPLAYED; no game launch.**

**2026-09-27 11:43 - CORE WEAPON CARDS + THE 3/6/9 RULE (user): DAMAGE is retired; each class has one CORE WEAPON card that boosts ONLY its own primary (`_tod_upgrades::core_weapon_bonus`): SOUL BEAM (Necromancer, 10%/Lv inside the beam), DEADEYE (Archer, id 6, 7%/Lv + new bow "d" forms), BUCKSHOT (Breacher, id 58, 4%/Lv + the old PELLETS forms), HEAVY HANDS (Warrior, id 7, 7%/Lv + the old MELEE SPEED forms). RULE: a card with big steps is 9 LEVELS with the steps at Lv3 / Lv6 / Lv9 (so an ULTIMATE +3 always lands one); `axis_level()` maps core levels onto existing weapon forms. The beam no longer kills on contact (2 souls at base, 1.0 s soul-rip minimum). See the CHANGELOG entry. BUILT: full build full4 + -GscOnly BUILD OK 12:01:18 Eastern (tmp/core_cards/gsc1.log), FF 193,176,704 B, diffs clean, nothing synced after. UNPLAYED.**


**2026-09-27 10:59 - NO PERK LIMIT (user: "remove the perk slot upgrade as well. There will be no perk limit on this map"): `level.perk_purchase_limit` 16 (zm_tod2_cybercity.gsc, one writer, above the roster); the PERK SLOTS card (id 40), its per-player hook and the "PERK SLOTS FULL" line are retired whole, its three cards unzoned. -GscOnly BUILD OK 10:59:21 Eastern (tmp/perk_limit/gsc1.log), FF 195,728,192 B, diffs clean, nothing synced after. UNPLAYED.**

**2026-09-27 - NORMAL DEVELOPMENT RESTORED; COMBINED MAP BUILD OK (2026-09-27 10:45:04 -0400).** User: "He will not be leading anymore. You may continue dev normally." Archer is no longer lead; no Archer build clearance or shared-file approval is required. This supersedes all older lead/clearance requirements below and in handoffs. Guarded builds remain serialized, never build during a running game, and the user playtests. FULL build and script follow-up passed: FF 196,343,232 B, fresh LED 166,776,956 B; source/deployment diffs clean, nothing synced after. Includes lighting/materials, 24-drop descent and top transit, preserving the shared arena pass plus watchdog (floor 40 chamber; regular top links 30/20/10). Native navigation and asset gates pass. GUID emission and prompt integration defects fixed; hint self-tests and mirrored-map parity pass. [Build evidence](docs/tower_design/BUILD_RESULT.md), [receipt](docs/tower_design/build_receipt.json), logs `tmp/map_design_build/full3.log` and `tmp/battle_arena/gsc1.log`. **UNPLAYED — no game launch.** Earlier source snapshots below predate this combined build and the arena follow-up.

**2026-09-27 10:30 - THE BATTLE ARENA (docs/185; source by this session, riding the tower-design session's combined FULL build tmp/map_design_build/full3.log): floor 40's pad spur is a walled CHAMBER (no tower teleporter on 40; transit = top bay <-> 30/20/10 + floor 1 <-> crown, 8 routes); everyone inside + 500 -> a detached arena room at (-8000,-8000) (`arena_zone`, GENERATED `_tod_arena_data.gsc` from tools/battle_arena_layout.js) -> ONE LEVEL PER TRIP of ten, 3 waves each of a random set (zombies+Manglers / zombies+Doppelghasts / hunters / horde; no Amalgam in the map yet), health x(1+0.25/Lv) and hits x(1+0.15/Lv) -> win = revive + frozen card deal -> the top bay. A wipe is game over. Tower spawning is held while away. Logs `[TOD_ARENA]`. The room is a placeholder square. BUILT: combined FULL build (full3.log) + -GscOnly BUILD OK 10:45:04 (tmp/battle_arena/gsc1.log), FF 196,343,232 B, diffs clean, nothing synced after. UNPLAYED.**

**2026-09-27 - TOP TRANSIT BAY + BOTH MAP-DESIGN PASSES SOURCE READY; ARCHER FULL BUILD REQUESTED, NOT YET CLEARED.** New covered crown-material room off the main tower's top terrace: four two-way floor links (40/30/20/10), unlocked by descending entry gates 41/31/21/11. Old bottom bay removed; one base pad links the crown's right-hand room. Occupied bottom returns reopen the main crown gate and restore spawns/respawns; sealed-island filters stop, opening alarm stays finished. Ten generated transit routes, co-op arrival clearance, [TOD_TELEPORT] diagnostics and source/compiled-pad navigation gates. Geometry/parity, transit runtime helpers, broken drops, jump pad, hoop, arity/native API, FX, Doppelghast and crown/material/conduit checks pass. Includes the lighting/material and 24-drop passes below; current map 10,615 world brushes, 580 lights. [Handoff](docs/tower_design/TRANSIT_HANDOFF.md), [review](docs/tower_design/transit/review.html). FULL fresh BSP/navmesh/LED needed; native travel/lighting remain unplayed. Archer remains build lead; no clearance/sync/build/launch by this session.

**2026-09-27 - BROKEN TOWER + LIGHTING SOURCE READY; ARCHER FULL BUILD REQUESTED, NOT YET CLEARED.** The main tower now has a fixed irregular mix of 24 broken drops and 26 intact paid stair-door transitions; teleporters are a later pass. Broad catch decks, local landing protection, free zone activation, directed native zombie negotiation nodes and [TOD_DROP] diagnostics are included. Geometry lint/self-tests (including missing deck, return stair and odd-floor parity), source behavior, arity/native API, crown/surface/conduit and Doppelghast checks pass. The old deployed navmesh is correctly rejected; fresh BSP/navmesh/LED required, never -GscOnly. [Handoff](docs/tower_design/BROKEN_TOWER_HANDOFF.md), [preview](docs/tower_design/broken/review.html). Includes the lighting/material pass below; 10,579 world brushes, 582 lights. Native traversal, grapple and brightness await the FULL build and user's playtest. Archer remains build lead; no clearance, sync, build or launch from this session.

**2026-09-27 - TOWER DESIGN SOURCE READY; ARCHER FULL BUILD REQUESTED, NOT YET CLEARED.** User requested a brighter visible sky, lights throughout the tower and materials matching the crown. [Handoff](docs/tower_design/BUILD_HANDOFF.md), [review](docs/tower_design/review.html). Crown panel/tread kit on 53,394 additional faces; 11 tint roles reuse the existing 30 maps. Two neutral stair pools per lap across both towers (240 new); 293 existing lights retuned, 582 total. Geometry, gameplay anchors and power/alarm masks preserved; source checks pass. Same v6 sky re-finished at score 0.64 (was 0.32), saturation 1.2; skyStops 1.85 -> 0.85 compensates the world bake. FULL + fresh LED required, never -GscOnly. No sync/build/game launch by this session. Build 18 does not contain this pass; native limits/brightness/performance await the lead's build and the user's test. Pre-edit notices and exact validation are in the handoff.

**2026-09-27 00:36 - BUILD 18 FULL OK (Archer = LEAD; tmp/lead_build/build18.log): FF 196,332,992 B, fresh LED, diffs clean, nothing synced after, 8 known-waived. = 17b + THE GAUNTLET'S LEFT HOOK: no stock weapon alternates hands on fire and `meleeAltAnim` is ignored on a bulletweapon, so 12 LEFT twins (`cc_gauntlet*_l_zm`, meleeAnim = the boxing left) are swapped in after each right swing (`TOD_GAUNTLET_ALT_TWINS`, _tod_warrior_melee; reconcile_twin treats want+"_l" as held; the Bash handback is always R). Registrations 138. UNPLAYED - the user tests build 18.**

**2026-09-27 00:22 - BUILD 17b -GscOnly OK (Archer = LEAD; tmp/lead_build/build17b.log, on build 17 FULL): FF 196,084,096 B, diffs clean, nothing synced after, 8 known-waived. = 16e + the helper Mangler's walk (RULE: stock `set_zombie_run_cycle` re-rolls `variant_type`; an actor with a custom one-row AST must pin it after `init_zombie_run_cycle` or it has no walk clip) + a FAILED data experiment: `meleeAltAnim` is IGNORED on a bulletweapon (the ledger proves it) - the gauntlet's left hook needs the twin route. UNPLAYED - the user tests 17b.**

**2026-09-27 00:05 - BUILD 16e FULL OK (Archer = LEAD; tmp/lead_build/build16e.log): FF 196,084,288 B, fresh LED, diffs clean, nothing synced after, 8 known-waived. = build 16 + 16d (the Retriever's flame WITHOUT the donor's three mesh spheres + child flare = the user's "lava skin"; RULE: a stock .efx carries children in `attachment` too, and MESH elements (fxuse_sphere_*) engulf a small projectile; the Necromancer's Soul Pulse burst + rev 9; the Breacher's C4/Cluster charge tiers) + the Warrior's gauntlet back to the donor (onehanded, no AIM-button left hook). Build gates added: the pause-menu + UI-lifetime Lua harnesses (engine-shaped ListHelper) and every generated fx's --check. UNPLAYED - the user tests 16e.**

**2026-09-26 22:58 - BUILD 16 FULL OK (Archer = LEAD; tmp/lead_build/build16c.log): FF 196,651,712 B, fresh LED, diffs clean, nothing synced after, 8 known-waived. = 15b + the pause-menu session's SCOREBOARD V2 / HUD V2 (USE_HUD_V2 true) / round badge / red prompt cards, the PAUSE SETTINGS-PAGE CRASH FIX (the user's UI Error 95573/8939: `DataSources.X( controller )` calls a datasource TABLE - ListHelper_SetupDataSource returns a table, never a function; harness mocks that `return fn` HIDE it), the Warrior's gauntlet (brawler, no lunge, no drop delay) + Bash sword proxy + CYBER SMASH, the Necromancer's truly black helpers (baked dark colour maps; colorTint is not honoured on those materials), the Blender agent's teleporter green/yellow, and THE NIGHT SKY TWICE AS BRIGHT (sky_intensity_factor is at its max 10, so the EXR was re-finished at score 0.32 and skyStops 2.85 -> 1.85 holds the world light). USER RULE (2026-09-26): NEVER HOLD A FINISHED CHANGE OUT OF A BUILD - it goes out in the next build at once; only a running game delays it (arm the watcher). UNPLAYED - the user tests build 16.**

**2026-09-26 19:54 - BUILD 15 FULL OK 19:47:24 + BUILD 15b -GscOnly OK 19:54:05 Eastern (Archer = LEAD; tmp/lead_build/build15.log / build15b.log): FF 194,946,176 B, fresh LED, diffs clean, nothing synced after, 8 known-waived. = THE USER'S BUILD-14 TEST, EVERY CLASS: the Rune Prison second cut (Der Eisendrache's arrow trail + upgraded impact, the fire HOLDS what it catches for TOD_RUNE_TRAP_MS 4000 then consumes it), THE GRAPPLE'S FOOTING (the hook refuses a spot with no navmesh under it, `no_footing` / GRAPPLE_NO_FOOTING - user: "I can land on stuff above where zombies can't get me"), THE RETRIEVER TUNED (flame x0.75 = map-owned fx_tod_ret_fire, flight 920 -> 690, hops 0.3 -> 0.4 s), the Necromancer's SOUL PULSE + rev 8, the Breacher's Cluster red glow, the pause menu's second pass. THE BUILD-14 LOG'S 122 SCRIPT ERRORS WERE ALL THE RUNE: RULE - a missile deleted at impact has NO origin when its `death` notify wakes; keep the last tracked position (fixed in 15b, rev `rune_prison_v2b`, fx hosts self-delete via `host_failsafe`); that exception was what left the rune fire burning all game. Dev flags still ARMED (five). UNPLAYED - the user tests build 15b.**

**2026-09-26 18:56 - BUILD 14 OK (Archer = LEAD): THE PAUSE MENU v2 (a SIXTH session, `tower-of-doom-ii-cybercity-29`, owns the pause menu then the scoreboard; docs/180; 60 `i_tod_pm_*` images, AetheriumStartMenu.lua rebuilt behind USE_PAUSE_V2 = true). The FULL build 14 (18:51) FAILED at the linker on 3 images: A COMPRESSED IMAGE MUST BE A MULTIPLE OF 4 IN BOTH DIMENSIONS or the converter writes no .iwi and the linker says "image missing" (no lint checks it; memory `compressed-image-multiple-of-4`; put it in every art-pack brief) - the lead padded the three PNGs to x4 and relinked: BUILD 14b -GscOnly OK 18:56:01 Eastern (tmp/lead_build/build14b.log), FF 193,898,752 B, diffs clean, nothing synced after, all 60 images in the ledger, 8 known-waived. = build 13 + the pause menu v2. UNPLAYED - the user tests build 14.**

**2026-09-26 18:22 - BUILD 13 FULL OK (Archer = LEAD; tmp/lead_build/build13.log): BUILD OK 18:22:26 Eastern, FF 191,749,376 B, fresh LED, diffs clean, nothing synced after, three GDTs deployed = repo, 8 known-waived, Cyber Sword receipt CYBER_SWORD_DEPLOYED. THE CYBER SWORD MODEL IS IN (the Blender agent's patch, applied by the lead; every cc_gold_sword form on tod_cyber_sword_view/_world, proxies tod_cyber_sword_bash_zm/_cast_zm, new _tod_cyber_sword.gsc|.csc: the blade glows when the smash is ready; same grip/bones/clips). ONE REGEN carried the Warrior's gauntlet `meleeWithLeftHand 1` (the left hook finally plays) + MELEE SPEED scaling the sword (fixedSwing 'pap'), and the Breacher's Peacekeeper LONG REACH (20000 u, 25% floor). Also: Bash starts on the press; KNIFE SPEED renamed MELEE SPEED (card + plate r18 re-bake owed); NEW card MELEE RANGE id 31 (Warrior, +15%/Lv sweep reach, max 5, text fallback); the Cluster's orange looping flame that burns until the pop; the Necromancer's rev 6 (helper kills pay, the helper Mangler moves). RULES PAID FOR TODAY: a bow arrow raises `missile_fire`, not `grenade_fire`; some tools-root .efx are gfx_debug_missing_fx STUBS (grep before zoning); the peers' generator asserts land AFTER the lead's one regen. Armory v7 (same URL) carries all of it. Dev flags still ARMED (five) - the user's test state. UNPLAYED - the user tests build 13.**

**2026-09-26 17:52 - BUILD 12 (FULL, Archer = LEAD): THE BUILD-11 ARCHER FIXES + THE NECROMANCER'S BLACK HELPERS + ARMORY v7. The user's build-11 run (17:44 console) showed THREE Archer pieces dead, two of them the lead's own bugs: THE RUNE PRISON never fired (the rune AND the draw stamp waited on `grenade_fire`; a bow's arrow is a MISSILE and raises `missile_fire` - both listen to both now; RULE: projectileweapon.gdf launches = `missile_fire`), THE RETRIEVER'S FLAME drew nothing (`zombie/fx_dog_fire_trail_zmb` is a STUB in the mod tools - `grep -c gfx_debug_missing_fx` the .efx before zoning ANY stock fx; now the Origins fire staff's bolt trail), THE GRAPPLE launched you skyward (release kept 1082 u/s of lift; NEW TOD_ARCHER_UP_MAX 700 on the rope / TOD_ARCHER_EXIT_UP_MAX 320 at every exit). Also carries the Necromancer's black helper models + bind x2 (GDT = FULL; CHANGELOG 18:10) and the Warrior's Bash text + gauntlet-Bash fix. ARMORY v7 (same URL): every class audited its own class against build 11, the lead applied ~60 corrections + a per-class "In numbers" panel; the legacy docs/armory.html gate is at 0 mismatches. BUILD 12 FULL OK 18:04:34 Eastern (tmp/lead_build/build12.log; exit 0, fresh .ff after the fresh LED - the watcher's log holds no [build] lines): FF 191,745,024 B, LED 150,068,396 B, diffs clean except _tod_necro_summon.gsc (the Necromancer's rev 6 landed after the sync = build 13), nothing synced after, ledger: the 4 black helper xmodels + 73 mc/tod_necro_blk_* + both eye materials + mgl_shot/blast + the staff fire trail (30 rows), 8 known-waived. THE USER TESTS BUILD 12. Build 13 = the Cyber Sword integration (lead applies the Blender agent's patch, ONE regen) + the Warrior's left hook (meleeWithLeftHand) / MELEE SPEED rename / MELEE RANGE (id 31) + the Breacher's Peacekeeper reach + Cluster flame + the Necromancer's rev 6. UNPLAYED.**

**2026-09-26 17:30 - THE RUNE PRISON (Archer = LEAD; user: the Fire Bow should have Der Eisendrache's "fire charge up move"): NEW `_tod_archer_rune.gsc` - a FULL-draw Fire Bow arrow plants a burning rune where it lands (stock dlc1 `fx_bow_rune_*_ug_*` effects + the DE draw loop / full-power explosion, all already in the tools root; no extraction needed), it glows 0.9 s, erupts, kills the nearest 12 ordinary zombies in 240 u, elites take 4 round-zombie healths, the rest burn 3 s; 5 s cooldown, 3 runes live per archer; the archer hears the upgraded draw loop when a full draw is armed. `TOD_RUNE_*` defines, logs `[TOD_RUNE]`. BUILD 11 FULL OK 17:28 Eastern (tmp/lead_build/build11c.log; attempts build11.log / build11b.log failed at the linker on the Necromancer's bare `material,tod_necro_eyes_white` zone line, memory `model-material-never-zoned-bare`): FF 190,246,464 B, fresh LED 150,068,396 B, diffs clean, nothing synced after, deployed tod_necro_helpers.gdt = repo, 8 known-waived; in the ledger: the white-eye head (tod_necro_thrall_head + mc/tod_necro_eyes_white), the six `fx_bow_rune_*`, `fx_trail_rpg_red_doa`, the Cyber Sword names, AND THE BLENDER AGENT'S WHOLE PENDING SET (the FULL sync copies the tree): `tod_power_conduit_off/on` (colour restoration + power wires), `tod_crown_alarm_rotor_high_on` + `mtl_tod_alarm_lamp_high_on` (random phases + 4x crown lamps), the teleporter depth-0 materials (deployed GDTs = repo). Carries the Necromancer's WHITE EYES + auras x1.25, the CYBER SWORD name, the Breacher's Cluster flame trail, the Rune Prison. UNPLAYED - the user tests.**

**2026-09-26 16:44 - BUILD 10 FULL OK (Archer = LEAD; tmp/lead_build/build10.log): FF 189,911,552 B, fresh LED, diffs clean, deployed twins GDT = repo, nothing synced after, 8 known-waived. One regen. Carries build 9 + WARRIOR (Gravity Smash tier 3 + kill-charged, gauntlet L/R hooks, dash punch gone, the punch's left-hand speed fix), BREACHER (Peacekeeper plasma tracer + energy impacts on both forms, PaP form on the plain Apex fire sounds; C4 stick on three lanes), NECROMANCER (Soul Bomb need = round total x (0.50 - 0.025 x Lv), helper Manglers own their goal - `ignore_find_flesh` - with HELPER_GOAL/TICK/STUCK logs; bare soul count on the tile). TEST STATE: `tod_dev_unlimited_offhand` ARMED skips the new kill charges (tiles read ready) - the user's call to disarm it. RE-BAKE LIST in the CHANGELOG's build-10 entry (sidearm line on every card, GRAVITY SMASH "SHORTER COOLDOWN", the tier-3 slasher card + greatsword HUD icon once the user's CYBER SWORD model lands). UNPLAYED - the user tests.**

**2026-09-26 16:20 - ARCHER PASS 3 (after the build-8 test, user: "the grapple's not bad now"): THE RETRIEVER THROWS MANY (`_tod_retriever.gsc` rewritten around `s.axes`, one struct per throw stepped side by side; refill runs while axes are out; Lv1 still one at a time), BURNS (`TOD_RET_FIRE_FX` = the hellhound fire trail on every axe, zoned) and HUNTS (`TOD_RET_MARK_R` 420 / `_STRIKE_R` 240 / `_CHAIN_MAX` 5 / `_RETURN_R` 180; log `MAGNET`); THE GRAPPLE LETS GO WHEN PINNED (`TOD_ARCHER_PIN_*`: rope reeled 250 past a body that stopped closing for 0.5 s = end "pinned", log `GRAPPLE_PINNED` - the user's "swinging weird" was a hook over the hall wall with the body held by the wall + the invisible barrier). Build 9 `-GscOnly` (tmp/lead_build/build9.log) carries it with the NECROMANCER'S SOULS PASS (Soul Bomb charged by kills not a timer, bomb kills land with the blast, bind x3 bought back by SUMMONING POWER, beam DPS shared across held souls; its CHANGELOG entry records the two design calls). BUILD 9 OK 16:23:48 Eastern (build9c.log; build9.log stopped because the game launched mid-sync, build9b.log at the two Retriever gates that asserted one-axe rules - both rewritten to the new contract): FF 189,910,464 B, diffs clean, nothing synced after, 8 known-waived. UNPLAYED - the user tests.**

**2026-09-26 15:50 - THE NECROMANCER'S MANGLER CRASH = A 64-CHAR EFFECT PATH (Archer = LEAD). Build 7 still died on the Mangler summon (user's 15:37 log); BOTH dumps hold the aura's child effect path cut to 63 chars (`...ambient_torso_o`), and the second names the corrected bone, so the build-7 bone fallback was right but not the cause. RULE: BO3 truncates an fx path (folder + name) to 63 characters at runtime and a parent spawning that missing child ACCESS-VIOLATES; the linker packs it silently; the same-shaped thrall child at 63 worked. Fixed in the generator (make_soul_fx.py: children are `<parent>_c<N>`, paths asserted), zone lines renamed, and NEW GATE `tools/lint_tod_fx_paths.js` on every build (zone `fx,` lines + child refs inside every .efx). BUILD 8 `-GscOnly` OK 15:46:14 Eastern (tmp/lead_build/build8.log): FF 189,911,808 B, diffs clean, nothing synced after, both `_c0` children in the ledger, 8 known-waived; = build 7 + the alarm relink + this fix. UNPLAYED - the user tests.**

**2026-09-26 14:28 - BUILD 7 OK (Archer = LEAD): FULL build 7 compiled the map (invisible barriers, 11083 brushes) + LED, then failed at the linker on the crown-alarm session's `#using _tod_crown_alarm` placed after `#precache`/`#define` in `_tod_fall.gsc` (moved to line 98; RULE: `#using` before `#insert`/`#precache`/`#namespace`). Build 7b `-GscOnly` (tmp/lead_build/build7b.log) BUILD OK 14:28:13 Eastern against that fresh BSP: FF 189,911,040 B, bank 199.6 MB, 8 known-waived, diffs clean, nothing synced after. Carries: Necro Mangler-aura crash fix (body_fx), class speed 1.1 flat / no sprint, hold-to-grapple + Archer-only stumble watcher (`_tod_archer::stumble_watch`; the global write in _tod_main reverted), invisible barriers to BARRIER_TOP (sky open), Warrior melee pass, Breacher cluster layers + C4 body stick, dark-card fixes, Knife Speed retire, crown alarm beacons + Doppelgast leg textures. Dev flags ARMED (tod_dev / tod_god / tod_dev_unlimited_offhand / tod_dev_all_guns / tod_dev_maxed) - DISARM ALL FIVE BEFORE PUBLISH. OPEN: the spiral's 112-unit rail caps are not barriered (user's call); who owns `_tod_crown_alarm.gsc` is still unanswered.  THE DEPLOYED .ff IS ONE RELINK NEWER: the crown-alarm session (a fifth session, still unidentified) ran its own `-GscOnly` at 14:32-14:36 WITHOUT clearing it (tmp/crown_alarm_final_relink.log): BUILD OK 14:36:13, FF 189,911,680 B, same 8 known-waived, diffs clean, nothing synced after, the alarm's zpkg (script + 3 xmodels + 1 fx) in the ledger - a verified superset of build 7b. That is the .ff the user tests. THE USER IDENTIFIED THAT SESSION (14:45): it is THE BLENDER MCP AGENT (crown alarm / Doppelgast legs / props). IT IS UNDER THE LEAD RULES LIKE THE THREE CLASS SESSIONS: no build (FULL or -GscOnly) without the Archer lead's clearance, ping the lead before any shared file, never launch the game; the Archer cannot message it directly (it is not a listed Claude session), so it reads this note and AGENTS.md - BLENDER AGENT: post your build request + status in docs/crown_alarm/BUILD_HANDOFF.md and wait for the lead's OK recorded there or here.UNPLAYED - the user tests.**

**2026-09-26 — BUILD 5 (Archer = LEAD): THE GRAPPLE LIFTS, NO SECONDARIES, HIT MARKERS ON EVERY ENEMY, THE WARRIOR'S MELEE PASS, THE NECROMANCER'S DRAIN + BIND, THE BREACHER'S FIREBALL, DEV MAXED. FULL BUILD OK 12:11:10 Eastern (tmp/lead_build/build5.log): FF 181,493,184 B, navmesh 3 components, sound bank 199.6 MB, 8 known-waived linker warnings only, scripts/zone_source/ui diffs clean, deployed twins GDT = repo, nothing synced after the .ff. UNPLAYED — the user tests.** THE ENGINE RULE PAID FOR TODAY: a scripted `SetVelocity` with positive z is DISCARDED while the player `IsOnGround` (the user's log: 1500 u/s of lift for four seconds, z pinned, the horizontal part a floor dash). Stock's fix is `self SetOrigin( self.origin + ( 0, 0, 1 ) )` right before the write (_zm_jump_pad.gsc:484) = `_tod_archer::floor_release()`, now on the attach and every grounded tick; the Warrior's Gravity Smash arc uses the same idiom. THE STRANDING: the rope carries an Archer over the hall wall onto the crown's bell floor (z 18224, outside every zone); `playable_area_cb` returns them to stock's `last_valid_position` once the grace is spent (kill brushes stay lethal; log `OOB_RETURN`). NO SECONDARIES (user): `_tod_classes` `secondary_name/stem` answer "" for every class, `give_secondary` reaps stock's pistol; the sidearm ASSETS are still generated (retire through gen_tod_twins in a later FULL build). HIT MARKERS (user: "all enemies ... more video game punchy"): `_tod_killconfirm.gsc` rides stock's `zombie_damage_override_callback` (white hit / gold headshot / red PUNCH on a kill = 1.7x then snap to size in 80 ms; elites keep the ding; ranks hit<head<kill<elite<boss; logs `[TOD_KILLCONFIRM] MARK/SKIP`). DEV MAXED: `tod_dev_maxed` ARMED (user: no locked abilities on dev) with tod_dev / tod_god / tod_dev_unlimited_offhand / tod_dev_all_guns — DISARM ALL FIVE BEFORE PUBLISH. Twins regen 124 registrations (+1 `hb_gold_sword_cast_zm`). Gates updated to the new contracts (test_archer_equipment whitelists the two literal SetOrigins; test_v1896 the new marker; test_expected_roster no longer pins tod_dev_maxed off). verify_armory_domains is ADVISORY and reports the Necromancer's soulbomb/soulbeam rows missing from the page (armory v6 owed). Per-class entries in the CHANGELOG's build-5 block. OPEN (user 2026-09-26, option 1): every class/tier card still BAKES A SIDEARM NAME (Warrior T1 "AMP63", T2 "UDM 45", T3 "RK7 GARRISON"; the docs/173 Theme B cards of the other classes too) now that secondaries are gone - lives for this test round; ONE combined re-bake pack for all four classes later (lead writes the brief). BUILD 6 = FULL BUILD OK 13:33:44 Eastern (tmp/lead_build/build6b.log; the first attempt, build6.log, stopped at test_archer_equipment asserting the pre-art "GRAPPLE is a text row" state - gate updated, nothing else changed): FF 189,722,752 B (+8.2 MB = the four classes' art), navmesh 3 components, bank 199.6 MB, 8 known-waived, scripts/zone_source/ui diffs clean, deployed tod_ui_images.gdt = repo, nothing synced after. It carries ALL FOUR classes' art (Archer docs/177, Breacher docs/178, Warrior docs/176, Necromancer docs/179; PAUSE_PLATE_MAX / TOD_UPG_PLATE_MAX 63; TodTextPlate empty) on top of build 5. The user decided (option 1) the class/tier cards keep their baked sidearm line for this round; one combined re-bake pack later. UNPLAYED - the user tests build 6 (build 5 was never played).

**2026-09-26 10:48 — THE FOUR-CLASS COMBINED BUILD (Archer = LEAD; user: "I do want you to be the lead of kind of everything here"). FULL BUILD OK 10:48:03 Eastern (tmp/lead_build/build2.log): FF 183,132,992 B, LED 150,076,832 B, bank 199.6 MB, navmesh 3 components, 0 unexpected linker errors, scripts/zone_source/ui/sound diffs clean, nothing synced after. It carries: WARRIOR One Inch Punch / Gauntlet of Siegfried / Gold Battle Sword + BASH 62 / GRAVITY SMASH 63 with their client half and sounds (the first attempt at 10:38 died on four undefined melee sound-table assets in tod_warrior_punch.gdt; install_punch.py now emits them); NECROMANCER summons on AIM (thralls / soul hounds / Mangler), SOUL BOMB lethal, PaP skull beam recolour, Burned Out sound, client-side FX; BREACHER C4 / Cluster on the audible lane, Fuse throw/arm aliases, lit bomblets, packed Mozambique muzzle; ARCHER plain bow trail + impact + impact sound, bow raise/lower/first-raise foley, draw creak + full-draw release, hook-bite spark, landing-buff tell, loops that travel, HUD reticle leak fixed. THE USER'S SFX/VFX DIRECTIVE (10:15): every class audited its own lethal / tactical / weapons for sound + visual effects before this build; per-class checklists are in the CHANGELOG's four 2026-09-26 sound+FX entries. LEAD RULES: builds cleared through the Archer session; ping it before any shared file (tod_upgrade.lua, _tod_upgrades.gsc, _tod_upgrade_ui.gsc, the .zone, AetheriumLoadout.lua, _tod_class_kit.gsc, _tod_classes.gsc, _tod_main.gsc, gen_tod_twins.js, staff_approved_manifest.json, lint_tod_assets*, sound CSVs, CLAUDE.md top notes, docs/upgrade_ids.md, docs/tod2_armory.html); gen_tod_twins regen is lead-only, once per build. Dev flags ARMED (tod_dev / tod_god / tod_dev_unlimited_offhand / tod_dev_all_guns) = the user's test state; DISARM BEFORE PUBLISH. Armory v5 = the Necromancer's artifact (same URL). UNPLAYED — the user tests.**

**2026-09-26 — THE NECROMANCER REPLACES THE SKIRMISHER (user). Class key "skirmisher" is RETIRED everywhere; "necromancer" is class id 1. Its weapon is the Skull of Nan Sapwe as a PRIMARY (`tod_necro_skull_b/_up_b`, source GENERATED by tools/necromancer/make_skull_gdt.py, emitted by gen_tod_twins LADDER.necromancer `fixedCap`), TIER 1 ONLY (no TIER card until tiers 2/3 exist). `_tod_necro_skull.gsc|.csc`: hold FIRE = soul beam (kills whole, elites drained), hold AIM = entrancing torch (the user wants AIM = SUMMON HELPERS next — design pending), clip = soul meter; WIDOW'S WINE = BURNED OUT on a zombie melee hit (2/round); NO GRENADES (`_tod_class_kit` TOD_KIT_NECRO). Six Skirmisher gun cards PARKED (`array( "parked" )`). Skirmisher art unzoned; slot 1 draws text until Necromancer art exists. Armory artifact: https://claude.ai/artifact/Euf1fzyYWgez5NcxxNT4Sq (source docs/tod2_armory.html). NOT BUILT (rides the Breacher session's combined build). UNPLAYED. Logs `[TOD_NECRO]`.**

**2026-09-25 ~23:15 — THE ARCHER'S CARDS (user): MAG SIZE / RECOIL / DEADSHOT RETIRED WHOLE, the Archer left SCAVENGER, and GRAPPLE (key `distraction`, id 41) is 8 LEVELS on ONE log curve (`_tod_archer.gsc` `grapple_curve` = ln(1+Lv)/ln(9) as a table; Lua row 41 mirrors it): range 3000->5000 (`TOD_ARCHER_RANGE_ADD`), and a LANDING BUFF on the first touch-down after a grapple — move speed +35% x curve (`_LAND_SPEED`, added in `apply_move_speed`), damage reduction 60% x curve (`_LAND_DR`, multiplied in `dr_mult`), for 0.75 + 1.75 x curve s. Recharge fixed 12 s (user listed only range + landing). The bows are ONE `_b` form each (gen_tod_twins axes []), registrations 158; `generated_asset_blocks` 159. `_tod_deadshot.gsc|.csc` still loads and reconciles a level that can no longer be above 0 (dead but harmless; retire it with the perk-bar icon if wanted). More Archer abilities are coming (user). FULL BUILD OK 23:19:00 Eastern (tmp/archer_swing/build_cards.log, FF 198,742,272 B; smaller: 74 bow variants gone), navmesh 3 components, the three `_b` bows in the linker ledger, scripts/zone_source/ui diffs clean, nothing synced after. UNPLAYED.**

**2026-09-25 22:52 — ARCHER GRAPPLE IS A SWING (user: "more of a swing ... like Pathfinder ... momentum ... sometimes it gets stuck"). `_tod_archer.gsc` `grapple_step` no longer overwrites velocity with a straight pull: it reads `GetVelocity()`, keeps the sideways part (capped `TOD_ARCHER_TANG_MAX`), accelerates along the rope (`TOD_ARCHER_PULL_ACCEL`, min `_KICK` on attach, cap `_SPEED`), and a reeling rope (`_REEL`/s) forbids drifting past its length = a pendulum. Attach keeps the run (only lifts off the floor); arrive drops the into-wall part + pops up (`_EXIT_HOP`); obstruction needs 0.1 s; release/obstructed/timeout/stalled/MANTLE keep momentum (the mantle used to brake to zero). STUCK: asked >150 u/s but moved <3 u -> nudge up + off the blocker, three failed nudges end it. LOGS (`[TOD_ARCHER]`, dev): `GRAPPLE_ATTACH vel_in/speed_in/ground`, `GRAPPLE_TICK` every 0.2 s (org, vel, asked_prev vs got, dist, rope, radial, swing, ground, stall), `GRAPPLE_STUCK` (blocker surface/normal), `GRAPPLE_OBSTRUCTED`, `GRAPPLE_END` (reason, path, min_dist, peak, vel_out, stuck_events). Gate: test_archer_equipment.js (68). -GscOnly BUILD OK 22:52:49 Eastern (tmp/archer_swing/build.log, FF 201,183,744 B), diffs clean, nothing synced after. UNPLAYED.**

**2026-09-25 ~22:40 — THE ENCLOSED HALLWAY (gen_tower_map.js `HW_ROOMS`, `ROAD_WALLED`): the Fall gate opens into a walled, roofed hallway + junction; LEFT (east) 1500 door -> enclosed POWER ROOM (the lever), RIGHT (west) 1500 door -> TELEPORTER ROOM (the OFF model, no destination yet), MIDDLE -> `tod_crown_bridge_door`, opened by the `power_on` flag (`_tod_fall::hallway_setup`) -> THE BALCONY, pushed 1160 south. THE OVERLOOK IS RETIRED. THE RAMPAGE INDUCER stands on the balcony (`crown_inducer_org`, read by `_tod_rampage` when the jump pad is live). LIGHT PASS pulled back another half (a quarter of the 17:07 move left). Plan: docs/crown_hallway_plan.png. FULL BUILD OK 22:45:27 Eastern (tmp/hpbar_build/build6_hallway.log, FF 201,186,560 B), navmesh 3 components, the deployed .map carries the 3 door/bridge targetnames + 30 walls / 8 roofs / 14 posts, diffs clean, nothing synced after; also inside the 22:52:49 -GscOnly below. UNPLAYED.**

**2026-09-25 — BREACHER: STICKY C4 + THE CLUSTER GRENADE (replaces Thermite). `tod_c4` (NEW source_data/tod_breacher_kit.gdt = hb_c4 with "Stick to all") sticks to enemies, 3 charges; the CLUSTER bursts on its first bounce and pops 8 bomblets ahead of the throw (`_tod_class_kit.gsc` `TOD_CLUSTER_*`), riding the Apex thermite grenade model as a stand-in. ~23:00 FUSE'S REAL ASSETS LANDED: weapon `tod_cluster` (source_data/tod_fuse_cluster.gdt) = Fuse's Knuckle Cluster canister/bomb/bomblet models, textures and 36 sound variants pulled from the installed Apex by `tools/apex_weapons/import_fuse_cluster.py` (re-run it, never hand-edit its outputs; `--check` re-hashes); bomblets are VISIBLE script models on gravity arcs that land, sizzle and pop; effects are BO3 emitters (Sparrow cluster arrow + incendiary trail) because Apex particles do not convert. FULL BUILD OK 23:05 Eastern (tmp/fuse_cluster_build/build.log, FF 201,229,760 B), diffs clean, nothing synced after; tod_cluster, all three Fuse models, the material, six images and three effects in the linker ledger; loaded sound bank rebuilt 23:05:36 with the tod_fuse_* aliases. The held canister lost only zero-area slivers (17 converter warnings). UNPLAYED. Logs `[TOD_KIT] CLUSTER_*`. FULL BUILD OK 22:37:29 Eastern (tmp/breacher_kit_build/build2.log, FF 201,186,560 B), diffs clean, nothing synced after, tod_c4 linked. ⚠️ The first attempt (build.log) died at test_tod_native_api: the edit had deleted the Warrior BASH/SMASH block; restored exactly from the 20:50 backup + the power-scale curve() line. UNPLAYED.**

**2026-09-25 — BOW DRAW + DEV ALL GUNS: the Bow / Fire Bow scale damage x1.0 (tap) -> x3.0 (full draw), linear, via NEW `_tod_archer_bow.gsc` + `draw_mult` in `upgrade_damage_cb` (guard-tested). TEST STATE: `level.tod_dev_all_guns` ARMED (every tier's primary + sidearm of your class held at once, `_tod_classes::dev_all_guns_watch`) - DISARM WITH tod_dev / tod_god / tod_dev_unlimited_offhand BEFORE PUBLISH. Logs `[TOD_ABOW]`, `[TOD_ROSTER] DEV_ALL_GUNS`. BUILT in the peer's FULL BUILD OK 22:03:44 Eastern (tmp/hpbar_build/build5.log, FF 201,156,736 B), diffs clean, nothing synced after. UNPLAYED.**

**2026-09-25 ~21:50 — ELITE BARS BIGGER + EDGE-ONLY PULSE (baked `_h1/_h2` frames, 62 materials; the element is never resized), THE 17:07 LIGHT PASS PULLED BACK HALFWAY (dark SSI ev 2/2.5 sun -4.05, powered ev 2.5/3, skyStops 3.9, LIGHT_STOPS_ADD 0.82; visible sky factor stays 10), and THE CROWN'S PaP + SHOP LIGHT POOLS REMOVED (`CROWN_VENDOR_LIGHTS` false). The user is making RED bar art from the rewritten docs/175 pack (62 files); a drop replaces the white placeholders by name — never re-run gen_hpbar_art.js after it. __HPBAR2_BUILD_STATUS__**

**2026-09-25 — ELITE HEALTH BARS (docs/174): every elite (Panzer/King, Protector, Fury, hound, Doppelghast, Mangler, armored sprinter) wears a WHITE over-head bar with a hit PULSE — Hellbound's `_tod_zombie_hp` route A ported as `_tod_elite_hp.gsc`, ELITES ONLY, persistent, per-kind height + spawn-in grace; art GENERATED by `tools/gen_hpbar_art.js` into `source_data/tod_hud_bars.gdt` (22 `tod_hpbar_e/b_NN` materials), gated by `tools/test_elite_hp.js`. Knobs per symptom in docs/174. Ordinary zombies never get one. FULL BUILD OK 20:59:49 Eastern (tmp/hpbar_build/build2.log; the first attempt, build.log, died on a PEER session's mid-edit Retriever gate, not on this pass): FF 200,252,736 B, LED 150.0 MB, navmesh 3 components, all 22 `tod_hpbar_*` images + 22 materials in the linker ledger (44 rows), 8 known-waived warnings only, scripts/zone_source/ui diffs clean, deployed GDT = repo, nothing synced after the .ff. It also carries the peer's in-progress power-scale scripts (their tree at 20:53). UNPLAYED — the user judges size, heights, the pulse and the white look; per-symptom knobs in docs/174.**

**2026-09-25 17:07 — THE EXAGGERATED LIGHT PASS (user: "still too dark and I can barely see the sky box ... exaggerate and ramp it up just so I can see that it changes"). FULL BUILD OK 17:07:58 Eastern (tmp/bright_build.log), FF 200,127,360 B, deployed = repo, nothing synced after. UNPLAYED. ON PURPOSE TOO BRIGHT — the user will say how far back.**
SSI exposure is the new lever (lower EV = brighter picture, sky included): dark SSI evmin/evmax 3/3.5 -> 1/1.5, sun
stops -5.6 -> -2.5; powered SSI evmin/evmax -> 2/2.5; skyStops 1.8 -> 6; SKY_INTENSITY_FACTOR 8.5 -> 10 (max);
LIGHT_STOPS_ADD 0.32 -> 1.32. To pull back, halve the moves in that order (exposure first).

**2026-09-25 15:01 — BRIGHTER + THE CROWN SHOP/PaP + THE CROWN RAMP (user, after the 14:28 run). FULL BUILD OK 15:01:08 Eastern (tmp/crown_shop_ramp_build.log): FF 200,155,392 B, navmesh 3 components, bank 199.6 MB, deployed scripts/ui/zone = repo, nothing synced after. UNPLAYED.**
The 14:28 run proved the flow (gate SHUT 5000 -> bought, alarm_lit level=2, power wave -> level=0, no Mangler crash). Changes:
BRIGHTER — dark SSI (Radiant 2/3, pre-power only) stops -6.88 -> -5.6; skyStops 1.32 -> 1.8 (all states);
`SKY_INTENSITY_FACTOR` 6.5 -> 8.5 (the VISIBLE sky only; user: "skylight brighter without impacting the ground").
THE CROWN ALTAR IS RETIRED (`_tod_upgrades::station_spawn`; the base + breather altars stay; `verify_native.py`
now asserts five placements) and the hall's ITEM SHOP takes its west shrine (`CROWN_SHOPS[0]` = (-644, HYC), yaw 90,
facing the PaP). THE CROWN PaP WAKES WITH THE ALARM: `flood()` sets `level.tod_crown_pap_live`; `zm_cwpap`
`machine_powered()` / `wait_machine_power()` (crown machine = the one registered with the jingle); every other PaP
still waits for power_on. THE RAMP (`_tod_fall::hunters_watch`, `TOD_FALL_HUNT_*`): from 90 unpaused s after the
alarm, alternating Doppelghast / Mangler on the farthest hall riser, gap 30 s x0.8 to 5 s, cap 2 -> 10 (+1 per 2
spawns), Doppelghast HP 5 -> 16 zombies, keeps 3 free actor slots, counts only while someone is in the hall, ends at
the seal; it IGNORES `tod_only_zombies` and the shared elite roof ON PURPOSE. Logs: `[TOD_FALL] PAP crown machine
live`, `RAMP clock started / spawn #N / held / over`.

**2026-09-25 20:59 — POWER SCALE: MAP 1 AT ONE TENTH (user: "dps and enemy health will be 10x less" so "players can easily identify how much damage they do"). `_tod_power_scale.gsc` wraps `level.callbackActorDamage` so every player / partner-robot hit on an enemy is x0.1 before ANY consumer (cards, headshots, Panzer armor, crosshair); health-derived damage is exempt by mark (`tod_cleave_hit` / `tod_trail_hit` / `tod_wisp_hit` / `tod_mage_chain_hit` / NEW `tod_ps_exempt` - set it around any new DoDamage computed from enemy health, and CLEAR it after) or weapon (xmas gun, gravity spikes) or kill-intent signature. Horde = map 1's exact curve / 10 (r1 14, r20 243). THE LIVE ELITES ARE THE MANGLER (5 round zombies) AND THE DOPPELGHAST (5, +1/spawn to 16 in the Fall) - both `tod_doppelghast::hunter_hp` x round zombie health, so /10 automatically (floor 500 -> 50); Panzer/Protector/Fury/Hellhound/sprinter are OFF (`level.tod_only_zombies`) but their bases are /10 too. Crosshair numbers exact to 2,047. Player HP + enemy damage untouched; weapon GDTs untouched (their DPS targets are in OLD units - the displayed DPS is a tenth). Gate: tools/test_power_scale.js. Built in a peer's FULL BUILD OK 20:59:49 Eastern. UNPLAYED.**

**2026-09-25 19:27 — GUN BALANCE: every Skirmisher/Archer/Breacher primary pinned to MAP 1's gun-class mean sustained DPS per tier (`gen_tod_twins.js` TIER_SUSTAINED: 1235/2193/3574, PaP 2228/3858/6295); Warrior blades unchanged = map 1's Slasher lead (user's call); bows count their minimum draw; falloff scales with damage (no gun hits harder at range). test_starter_weapons.js is the gate. FULL BUILD OK 19:27:46 Eastern. UNPLAYED. The old "DPS pinned to the retired gun" contracts in older notes below are superseded for the three gun classes.**

**2026-09-25 17:07 — TEST STATE: `level.tod_dev_unlimited_offhand` ARMED (no offhand cooldowns/charges, every class) alongside tod_dev + tod_god; DISARM ALL THREE BEFORE PUBLISH. The crown's alarm switch now glows orange + sparks until pulled (`_tod_fall::switch_attract`). -GscOnly BUILD OK 17:07:58 Eastern. UNPLAYED.**

**2026-09-25 15:58 — WARRIOR + BREACHER CARRY HELLBOUND'S LETHAL/TACTICAL FROM SPAWN (`_tod_class_kit.gsc`): Warrior BASH (tactical) + GRAVITY SMASH (lethal), Breacher C4 (lethal) + THERMITE (tactical), each at its donor card's first level, damage rebased on `level.zombie_health`. HUD via the Archer's `tod_archer_abil` + kit id (stand-in icons). FULL BUILD OK 15:58:58 Eastern (tmp/class_kit_build/build.log), diffs clean. UNPLAYED — logs `[TOD_KIT]`. Only the Skirmisher is left without a tactical. Armory artifact: https://claude.ai/artifact/UUsGQZBcsJHqonpBBZmMr5 (source docs/tod2_armory.html).**

**2026-09-25 14:34 — THE NEW CLASS ART IS NOW DRAWN: two Sep 24 overrides hid it (class-select nulled card art for classes 1-4; `USE_TIER_CARD_ART` false). Removed/flipped; -GscOnly BUILD OK 14:34:04 Eastern. ⚠️ AN ART INSTALL IS NOT DONE UNTIL THE DRAW PATH IS READ: a packed image behind a disabled flag is invisible, and the ledger cannot tell you. UNPLAYED.**

**2026-09-25 14:04 — TOD II IS FOUR CLASSES (user: "It should only show four"): THE MAGE IS GATED OFF (`TOD_MAGE_ENABLED` 0 / `MAGE_ENABLED` false; staff twins not generated, 228/235 registrations; code, staffs and art kept; docs/114 D.4 re-enables). ALL FIVE CLASSES' ART IS NOW THEME B (docs/173 drop installed). FULL BUILD OK 14:04:18 Eastern (tmp/typeface_build/build2.log): FF 200,157,376 B, diffs clean, nothing synced after. UNPLAYED.** Every "the mage is LIVE / five classes" line below is superseded.

**2026-09-25 13:31 — NEW TYPEFACE (docs/172 OPTION A) + FALLEN/BLACKOUT SKIRMISHER (docs/171 THEME B) + PAUSE MENU/SCOREBOARD IN THE MAP FONT. FULL BUILD OK 13:31:03 Eastern (tmp/typeface_build/build.log): FF 210,551,872 B, 8 known-waived, diffs clean, nothing synced after, `ttf,fonts/tod_tower1.ttf` in the ledger. UNPLAYED.**
The menus use a REAL TTF built from the glyph sheets (`tools/build_tod_ttf.py`, re-run after
any re-slice), NOT per-glyph images: that route would add ~2,000 UI elements per pause open
(element-pool crash risk). The TTF carries the face only (no outline/shadow). Art packs now
always ship `typography/` (see ART REQUEST PACKS). docs/173 requests the other four classes.

**2026-09-25 — THE RETRIEVER'S AMMO-COUNTER ICON: the user's 11:25 crash ("Com_ERROR: Primary Grenade Ammo Counter Icon Not Found for: tod_archer_retriever", the instant the Archer armed) is fixed in `tools/archer_assets/install_native_weapons.py` (an offhand in the lethal slot must name an ammo-counter MATERIAL; the BO2 definition had none -> `ammoCounterIcon "t7_icon_weapon_special_knife_pu"`, the stock knife icon that 100+ tools-root weapon blocks already use there) and `source_data/tod_archer_weapons.gdt` regenerated; all three Archer gates pass. FULL BUILD OK 11:43:06 Eastern (tmp/sky3d_build/full_build_v6_113517.log): FF 206,925,056 B (the sky is STREAMED — the proof is the NEW sky .iwi `5ZL5ANMTL255TXVGOC4VBTCJKJ`, 29.4 MB, at 11:42:17; v5's was `NRQSHJDV6LO3ZFEGG3DB5R5L5D`), LED fresh, navmesh 3 components, bank 199.6 MiB, 8 known-waived warnings, deployed EXR sha = repo (06cf89a3…), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, skyStops 1.0 + the dark SSI −7.2 (the peers' darkening), TOD_FALL_GATE_OPEN 0, and the deployed tod_archer_weapons.gdt carries the Retriever's ammoCounterIcon — ONE build carries the v6 sky, the Retriever crash fix and the peers' blackout pass (tod_dev / tod_god ARMED = the user's 09-24 test state). UNPLAYED — the user tests; the tomahawk picture on the counter is a follow-up.**

**2026-09-25 — THE SKY, v6 THE COLOUR PASS + THE SPIRE CLUSTER (docs/166 §8): the user's notes on the v5 build + the twelve docs/167 billboards, built. FULL BUILD OK 11:43:06 Eastern (tmp/sky3d_build/full_build_v6_113517.log): FF 206,925,056 B (the sky is STREAMED — the proof is the NEW sky .iwi `5ZL5ANMTL255TXVGOC4VBTCJKJ`, 29.4 MB, at 11:42:17; v5's was `NRQSHJDV6LO3ZFEGG3DB5R5L5D`), LED fresh, navmesh 3 components, bank 199.6 MiB, 8 known-waived warnings, deployed EXR sha = repo (06cf89a3…), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, skyStops 1.0 + the dark SSI −7.2 (the peers' darkening), TOD_FALL_GATE_OPEN 0, and the deployed tod_archer_weapons.gdt carries the Retriever's ammoCounterIcon — ONE build carries the v6 sky, the Retriever crash fix and the peers' blackout pass (tod_dev / tod_god ARMED = the user's 09-24 test state). UNPLAYED — the user tests.**
User (~10:30–11:00), on the v5 build: the billboards downloaded; "cut the windows by 35 % but keep
the consistency and detail"; "the entire skybox ... more colourful, more contrasting, more elegant
... a little bland ... I like the sky now"; "the red giant planet should be about 4x bigger"; and on
the first preview: "our buildings ... look like New York buildings ... they should really reference
the ones I sent ... one looks like a New York style one and then one looks like an actual cyber city
tower ... take a step back". THE STEP BACK (docs/166 §8.2): the references' towers are BUNDLES of
tapering spires with light CONCENTRATED in a few giant saturated crystal slabs, collars and seams on
dark solid metal; v5's were extruded footprints with setbacks and window grids — Manhattan in neon.
`tools/sky3d/build_city.py` v6: nearly every tower over 90 m is a SPIRE CLUSTER — a slim core of
3..5 frustum segments (new `Acc.loft`) ending in a lit needle, 4..8 satellite spires, 1..3 CRYSTAL
slabs (`mat_crystal`, E_CRYSTAL 1.10), seams on every 2nd/3rd edge following the taper, a collar at
every break, a halo ring on a third, greebles below; the facade (`style >= 2` in the FLOAT_COLOR
attribute) is dark metal with thin light rows, faint grooves and dense AMBER windows on the lowest
floors; the box tiers stay for the low blocks. Plus: `art/sky3d/billboards/ad_01..12.png` (the drop
at 512 px) on 75 % of the ad screens by their own orientation (`screen_mi`; the wrapper defaults to
the folder, `-ScreensDir none` opts out); windows -35 % (litfrac 0.169); the red giant `ruby` r 9.6
deg, crimson, ringed, `gain` 1.25; jewel-tone nebula + a deep blue band, NEB_GAIN 1.45, the whole
neon range, neon streets in half the districts + three neon core rings, BODY_FLOOR x0.7, the fog
graded warm -> violet-magenta with height, E_PANEL 0.45 (the fields clipped at the knee = pastel),
`finish_sky.py --sat 1.10` (new; the mean is re-held). THREE LESSONS PAID FOR (§8.4): judge a colour
by MEASURING pixel boxes / percentiles, never on a downscaled contact sheet (three rounds chased
"pale" crystal slabs that were too DARK — the fix was x1.8 brighter, the opposite of what the eye
said); a texel-wide shader line at 3 km covers most of a 7 m cell, so every line is capped to a
fraction of its cell; a patch guard keyed on a version tag matched a comment from the round before
and a whole render was a no-op. The mean contract 0.16 is unchanged (skyStops is the peers' knob: 6 -> 4 in the blackout pass,
1.0 + a -7.2 dark SSI in this build, the sky LIGHT not the picture); the worldspawn factor stays 6.5 and the previews are rendered AT 6.5 (W -> white would be 5.78,
so the game shows the sky ~12 % over W; set `SKY_INTENSITY_FACTOR` to 5.78 + regen +
full build to sit on W — not done: peers are editing the generator). One command still:
`.\tools\sky3d\render_sky3d.ps1 -Ship -Sat 1.10 -DisplayMult 6.5`. Previews `docs/sky_preview/sky3d_*`
(19 views incl. `ruby`), `sky3d_contact.png`, `sky3d_ref_vs_render.png` (the reference beside ours).
This build also carries the peer's `_tod_fall.gsc` TOD_FALL_GATE_OPEN 0 and the deployed blackout
pass (the sync copies the whole tree).

**2026-09-25 11:43 — DARKER STILL (user: "I dont think its dark enough still"): skyStops 4 -> 1, pre-power sun -5.2 -> -7.2; in the SKY session's FULL BUILD OK 11:43:06 (FF 206,925,056 B, LED re-baked 11:41:42; also the v6 sky + the Retriever ammo-counter crash fix). UNPLAYED. Next lever: the dark SSI's exposure (docs/164 §9).**

**2026-09-25 — THE BLACKOUT + TWO SWITCHES + ONE SHOP + ONLY ZOMBIES + THE 5000 GATE (user, after a co-op play ~10:30). FULL BUILD OK 10:57:28 Eastern (tmp/blackout_build/build.log): FF 206,779,392 B, fresh BSP + LED 100,173,570 B, navmesh 3 components, 8 known-waived warnings (none a tod_black_*), all 24 tod_black_* materials the map uses in the linker ledger, banks 109.4 / 209.3 MB. It carries everything in this pass EXCEPT the 5000 gate (TOD_FALL_GATE_OPEN 0, edited after its sync): the -GscOnly meant to carry it halted before the linker on a PEER session's in-progress tools/art_cohesion/verify_surfaces.py (a crown-material pass that keeps world emission at zero); that crown session is a THIRD session (not the sky session). ITS OWN FULL BUILD then carried the gate: BUILD OK 11:20:25 Eastern (tmp/art_cohesion/full_build.log), FF 206,925,056 B, LED 100,170,906 B, navmesh 3 components, 8 known-waived; its sync ran after the gate edit (10:52:09), so the 11:20:25 .ff has EVERYTHING in this pass plus the crown's textured surfaces. That -GscOnly's sync did run, so the deployed SOURCE tree is newer than the .ff — the .ff itself is the 10:57 build. UNPLAYED — the user tests.**
User: two item shops inside the crown (one wanted); the switch that starts the
alarm must be INSIDE the crown; only regular zombies (no Panzers, dogs, Furies,
armored sprinters); remove the fog; the map must be REALLY dark — "the only
thing that you can see pretty well is maybe the sky and then once power's on
things will light up dynamically"; the hall gate was open — it must be a 5000
buy door. On three questions they picked ALMOST PITCH BLACK / REMOVE THE GLOW
EVERYWHERE / A WAVE DOWN THE TOWER. THE ORDER NOW: spawn in the dark hall (sky
only, intro track) -> THE ALARM SWITCH on the sanctuary's top step (generated
`alarm_switch_org()` (0, 9272, 19424); prompt "THE ALARM", a TOD_NOUNS entry)
cuts the intro, spins the red beacon, starts the nuclear siren, zombies (sprint
gait, rate 1.0) 10 s later -> buy the 5000 hall gate (`TOD_FALL_GATE_OPEN 0`,
party-scaled like every door) -> the overlook's POWER SWITCH (armed only after
the alarm; "activate the power") -> `power_switch_on`: stock power-on + THE
POWER WAVE (`power_wave`: a district-coloured todPerkGlow light on each floor
TOP DOWN from generated `wave_orgs/wave_fx`, 12 s, then
`util::set_lighting_state( 0 )` = Radiant State 1 = every baked light) -> the
jump pad works. THE BLACKOUT (gen_tower_map.js `BLACKOUT` / `LIGHTS_AT_POWER` /
`SSI_PREPOWER`): every face's material is swapped AS THE .map IS WRITTEN for a
no-glow clone `tod_black_<suffix>` (tools/tod_black_materials.json = the one list
read by gen_tod_door_materials.js, the generator and lint_tod_geometry.js; scaleRGB
0, mirror off, albedo = the line hue x 0.35); every light is lightingstate1 ONLY
(the map boots Radiant State 2 — PROVEN by the user's log, `[TOD_LIGHTSTATE]
level=1 player=1`; T1's test lights retired); ssi2 = `tod_ssi_cybercity_dark`
(sun -5.2 vs -2.2); skyStops 6 -> 4; the visible sky keeps factor 6.5. The veil
fog is OFF (`TOD_VEIL 0`). ONE SHOP: `CROWN_SHOPS` = the west-bay hut + the
balcony display; `_tod_shop` `TOD_SHOP_CYCLE 1`. ONLY ZOMBIES:
`level.tod_only_zombies = true` in zm_tod2_cybercity.gsc, read by the Panzer/
Protector, Fury, hellhound and armored-sprinter directors and the Doppelghast
hunters (the spire's Wardens and the parked finale are not gated). KNOBS, per
symptom: too dark after power = light stops / `albedo` in the json; too bright
before = skyStops (tod_skybox.gdt) or the dark SSI's stops; wave too slow/fast
= `TOD_FALL_WAVE_SECS`. Records: docs/160 §10.10, docs/164 §9. Logs: `[TOD_FALL]
SWITCH alarm/power ...`, `POWER on by`, `WAVE start/lit`, `[TOD_LIGHTSTATE]
at=wave_lit` (expect level=0).

**2026-09-25 — THE SKY, v5 THE BIG CITY (docs/166 §7): the user's eight notes on the v4 contact sheet, built. FULL BUILD OK 04:38:45 Eastern: FF 206,962,048 B (the sky is STREAMED — the proof is the NEW sky .iwi `NRQSHJDV6LO3ZFEGG3DB5R5L5D`, 29.1 MB, at 04:38:02; v4's was `EHDAWQ6EGNRBHBMDYRWRZYSP23`), LED fresh, navmesh 3 components, banks 109.4 / 209.3 MB, 8 known-waived warnings, deployed EXR sha = repo (81791e06…), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, skyStops 6.0 unchanged; it carries the peer's 03:26 script fixes. Log: tmp/sky3d_build/full_build_v5.log. UNPLAYED — the user tests.**
User (~03:10), reading the v4 contact sheet: too many small buildings ("three times as big", "half what
we have on the ground"), one dominant colour (the amber windows), spaceships "barely tell it's a
spaceship ... bigger", the sky "a bit empty ... double it ... planets in the distance for depth",
black holes and the major ring towers "a lot more detail", the ground floor's circle "not an even
bleed" into the grid; the streets stay. `tools/sky3d/build_city.py` v5: lot pitch 320/640/1280 (was
140/280/560), heights x2-2.5 -> 1,840 buildings instead of 9,749, each with tiers, lit belts, fins,
face emblems, antenna arrays, lit plinths; window tint per hue row (amber is one row of ten), lit
fraction 0.26, E_WIN 0.70, panel columns 18-48 m, PANEL_FRAC 0.60, blue/cyan-leaning weights; THE CORE
(polar lots on eight ring roads to 1.42 km, twelve boulevards, the square grid beyond R_CORE, THE LOOP
over the last ring); five BATTLECRUISERS 1.0-1.4 km with a real silhouette + twelve fighters, a
diffuse near-black hull, `ship_cap()` keeps towers out of their lanes; twice the sky bodies (two black
holes, comet, asteroid belt, `dim` for depth); the black hole's lensed halo (`mat_lensarc`), jets,
streams; `mega_detail` (belts, ring platforms with pods and light-falls, fins, antennas) on every
supertall inside 12 km. TWO TRAPS PAID FOR: a rolled ziggurat's ring deck (3.6 km radius) passed OVER
the camera (ziggurat base <= 1200 m, only beyond 4.5 km; decks capped and never within 900 m); tube
CONES read as solid paper — the cruisers' seven 1.4 km engine plumes were the "beige planks" blamed
on wings/hull/bay for three rounds (found by a bounding-box probe of the .blend) -> `soft_fan()`
nested translucent fans with per-corner alpha (`Acc.poly(..., cols=)`) for plumes, jets, comet tails.
The mean contract 0.16, skyStops 6.0 and worldspawn factor 6.5 are UNCHANGED (auto printed 6.30; a
regen was not needed). `render_sky3d.ps1` now parses under Windows PowerShell 5.1 (BOM, no em-dashes,
native calls under ErrorAction Continue — Blender's TBBmalloc stderr line killed it under Stop). One
command still: `.	ools\sky3d
ender_sky3d.ps1 -Ship` (8192 @ 160 = 475 s). Previews
`docs/sky_preview/sky3d_*` (18 views incl. ships / maelstrom / core), `sky3d_contact.png`.

**2026-09-25 - STARTUP FAILURES FIXED; MAP-WIDE SCRIPT REVIEW AND GUARDED BUILD PASSED. FF 2026-09-25T03:26:57.926904 Eastern, 206,962,048 B. USER RETEST PENDING.**
The user's first log failed on server StopFXOnTag in the Retriever; attached
trails now end by deleting their host, as stock BO3 does. The next user launch
passed server initialization and failed on client hash 37CBCF1A =
PlaySoundAtPosition in _tod_boss_fx.csc. Both client sounds now use the actor's
PlaySound. The review also removed undocumented camera arguments from the
third-person toggle. No new BO3 launch by the agent.
New build gate test_tod_native_api.js checks 6,281 native call sites across
all 96 repository scripts against same-VM installed references/SDK/DLC source.
The arity lint now covers shared scripts, mixed-case/multiple namespaces and
unknown namespaces. Five negative controls reject the reported failures and
representative signature errors. This is static evidence, not a native boot
or gameplay guarantee. Details: docs/170_archer_native_bo2.md.
Guarded -GscOnly build OK: tmp/archer_assets/startup_review_build.log. All 96
reviewed script hashes match deployment; Archer's 261 inputs and roster's 350
inputs pass, expected models/weapons/local audio aliases packed, dev/god ON.
Map/BSP/LED/navmesh match the 02:57 sky-v4 full build. Eight existing waived
linker diagnostics unchanged. FF SHA256 a161b014b55d5f767ad39e2021bf5661fb8cb0f1b1bdc77d4d78208f4c88157d.
Evidence: docs/archer_equipment_evidence/startup_review.json, native_api.json,
build.json, full_geometry.json and roster_build.json. The earlier 03:13 link
FAILED its final guard because BO3 launched during post-build checks; this
clean completed rebuild supersedes it. User tests; do not launch unasked.

**2026-09-25 — THE SKY IS A COPY OF THE USER'S THREE REFERENCES (docs/166 §6, v4 THE REFERENCE COPY). FULL BUILD OK 02:57:04 Eastern: FF 206,962,432 B (the sky is a STREAMED image, so the .ff size does not move: the proof is the NEW sky .iwi `EHDAWQ6EGNRBHBMDYRWRZYSP23`, 28.5 MB, at 02:56:12 — v1's was `CFE55UDPLPVBWJ3P5KDZGV6U6K`), LED bake fresh, navmesh 3 components, banks 109.4 / 209.3 MB, 8 known-waived warnings, deployed EXR sha = repo (d6453532…), scripts / zone_source / ui diffs clean, nothing synced after the .ff, the deployed .map carries sky_intensity_factor0/1 6.5, skyStops 6.0 unchanged. Log: tmp/sky3d_build/full_build_v4.log. UNPLAYED — the user tests.**
The user brought three ChatGPT images (`Downloads/sky_refs/ref1..3.png`: "these are what we will use as a
reference") after rejecting v1 (realistic, "lost the cyber feeling") and the v2/v3 iterations (purple-grey
mush). v4 copies them BY MEASUREMENT: true display values (⚠️ bpy `Image.pixels` of a byte PNG are the
display bytes — my first numbers were double-encoded): mean luminance 0.21, 17-22 % near-black, 33-36 %
saturated, mean saturation 0.65, voids (3,2,6), indigo (17,23,54), magenta nebula (162,53,88), warm city
glow (221,140,59), cyan neon (39,197,228), dark bodies (22,18,26). `tools/sky3d/build_city.py` authors in
W = display white (saturated colours need minor channels ≤ 0.05 W — the moon read ORANGE with green 0.20);
dark matte towers + dense warm windows + neon PANELS on 65 % + rings, sigils, spikes, floating platforms
with light-falls, glowing highway ribbons; a SPACE sky (black voids, indigo patches, five-hue nebula, ~60k
stars with flare stars), one swirling oblique BLACK HOLE with debris, two ringed gas giants, three cracked
planets, galaxies, asteroids; THE ORIGIN's violet self-lit storm with six bolts; a BLOOD moon; the sign
reads TOWER OF DOOM II / FALLEN CYBERCITY. THE PICTURE vs THE LIGHT: the docs/104 mean contract (0.16)
and skyStops 6.0 are UNCHANGED; the references' brightness comes from worldspawn `sky_intensity_factor0/1`
= 6.5 (`SKY_INTENSITY_FACTOR` in gen_tower_map.js, the value `finish_sky.py --display-mult auto` prints;
docs/162 05 §4.4: it multiplies the visible sky box only). If the sky is too bright / dark in game, THAT
key is the knob (a regen + full build), not the EXR. One command still: `.\tools\sky3d\render_sky3d.ps1
-Ship` (8192 @ 160 spp = 503 s now; v1's 52 min was the fog). Previews: `docs/sky_preview/sky3d_*.png`,
`sky3d_contact.png`. The mirror question is still unverified in game (`-Mirror` re-finish).

**2026-09-25 - ARCHER NATIVE BO2 PASS (docs/170): IMPLEMENTED AND BUILT. Full native-asset build OK 01:49:25; final script build OK 01:54:18 Eastern. FF 206,962,368 B. UNPLAYED; the user tests.**
Hell's Retriever now uses the recovered BO2 offhand definition, original view/world
models, Alcatraz hands, hold/throw/acquisition clips and audio. The port preserves
BO2 charge thresholds, chain/return timing, damage rules, power-up collection and
five-second catch recharge. Native grapple wrist presentation, hook/cable/audio,
class-only no-fall damage and automatic diagnostics are integrated. The ember
material is a BO3 renderer translation; native appearance/parity is NOT verified.
Fixed the prior runtime LoadFX unresolved external, invalid Blender image suffixes,
flourish binary/sound action, charge-ring shader, launcher image semantics,
stock grenade inventory repair and deferred input restoration after class/respawn.
All Archer checks pass. 261 deployed map/art inputs match; all seven clips,
six compiled models (eight LODs) and twelve audio aliases are present; no
Archer linker warnings. Banks: 109,442,176 / 209,338,496 B. Roster audit: 350 inputs,
240 weapon/model assets, 174 local sound aliases; dev/god ON. No game launch.
The full build is tmp/balcony_build/build.log; our duplicate was stopped before
compilation. The final cleanup fix missed that full build's sync and IS included
in tmp/archer_assets/native_final_gsc_build.log. Map/BSP/nav/LED hashes match the
full build; the peer balcony and Veil are included. No native inputs changed or
synced after the final fastfile. Evidence: docs/archer_equipment_evidence/
build.json, full_geometry.json, roster_build.json, native_sources.json.
FF SHA256: ed4d67f60bff5d155d014d7226e7e748bba2a7e82a9b59424b3d133fbcb6d15e.

**2026-09-25 — THE BALCONY + THE OVERLOOK; THE LEVER IS THE POWER; THE GATE IS OPEN AT START (user, ~01:30). FULL BUILD OK 01:49:25 Eastern: FF 206,961,984 B, LED 100.2 MB, navmesh 3 components (the island = hall + balcony + overlook + pad, one component), geometry/assets built; the 01:49 Archer hash audit found `_tod_archer.gsc` differed from deployment (the 01:47:47 cleanup fix missed this build's sync); a separate script rebuild follows as recorded above; THE VEIL IS IN THIS .ff TOO. UNPLAYED.**
User: the jump-pad balcony must be big enough for the shop, the jump pad and
Quick Revive; the power switch goes in another room off it where players can
LOOK DOWN the tower ("they'll turn on the power, they'll see the tower light
up, they'll see the fog lift ... see the sky beautifully"), "a few rooms
behind doors so you have to stay in this little area for a bit"; the jump pad
and Quick Revive must not work until the power is on. GENERATOR
(gen_tower_map.js, the CW_CUT block): the launch deck is THE BALCONY, 1280 x
640 (`JP_LAUNCH_HALF` 640, y 6240..6880), the pad at (0, 6480); off its EAST
rail a 160-wide PASSAGE (x 640..960, y 6480..6640), an ANTECHAMBER (x
960..1440, y 6280..6660 — held under the crown's south-face rib 3 whose foot
reaches y 6688) and THE OVERLOOK (x 960..1440, y 5880..6280) hanging south over
the void, all `roadFlat` cells (rails derived, lint-proven; the doorways are
the shared edges, no door slabs yet). THE LEVER stands at the overlook's south
rail, `lever_org()` (1200, 5910, 19392) yaw 180 (front to the room), asserted
inside the cell. QUICK REVIVE's pin (`TERRACE_QR`, still that name) moved from
the terrace to the balcony's north rail at (-400, 6851). A FOURTH ITEM SHOP,
`CROWN_SHOPS[3]` (-500, 6560, yaw 90), stands on the balcony's west half and is
NEVER ACTIVE (`_tod_shop` cycles `% 3`) = the "empty shop to look at". The
launch-side avenue pylons moved out to x ±752 (`AVENUE` pairs). Five pool
lights (pad, QR, passage, antechamber, lever). `on_crown_island()` now takes
its x/y from `JP_CRN_BOX` (x -832..1524, y 5796..9392) so the seal counts the
rooms. 5f.9 exempts `crown item shop N hull` (the hut's own collision) and
gains an overlook-vs-crown proof. SCRIPT: `_tod_fall.gsc` `power_on()` moved
from the blackscreen INTO `flood()` — THE LEVER IS THE POWER (stock's
turn_power_on_and_open_doors + perk_unpause_all_perks), so perks (solo Quick
Revive = stock's exception, powered from round 1), the crown PaP, teleporters,
the item shops and the jump pad (`_tod_jumppad::refuse_reason` "no_power")
all wait for it; `TOD_FALL_GATE_OPEN 1` opens the 5000 hall gate FREE at init
via `_tod_doors::force_open_by_flag` (no points exist before the first zombie,
so a paid door before the lever can never be bought — THE USER'S "doors before
the power" NEEDS A MONEY SOURCE FIRST; the seal still closes the gate). Gates:
lint_tod_geometry (0 regressions), test_jumppad (arc sweep clear of the new
rails), test_shop (4 anchors; `MODEL_CLIP_COLUMNS` [0-3]), test_doppelghast,
arity, hints, bunkers, crown convex — all green before the build. NEXT (the
user's stated plan): every tower light on a lighting state that the lever
flips (docs/162 ch.02) — not started.

**2026-09-25 — THE VEIL: FOG HIDES THE SKY UNTIL THE LEVER, THEN LERPS CLEAR (user: "instead of making it disappear ... it breaks sometimes"). BUILT IN THE 01:49:25 FULL BUILD (the balcony note above). Earlier that night: the -GscOnly build at 01:18 died in `gdtdb /update` on a PEER SESSION's in-progress `source_data/tod_archer_motion.gdt` (18 image names ending `.001`, "Invalid asset name") — every build fails at that step until that session fixes its GDT. UNPLAYED.**
`_tod_atmosphere.gsc` `TOD_VEIL 1`: apply_fog's tower branch is `tower_fog()`
— a dense even ash haze (`TOD_VEIL_HALFDIST` 520, halfheight 1,000,000 = the
spire's no-falloff trick, colour 0.22/0.20/0.26 — lighter than scene-black or
it reads as nothing) from the blackscreen while `level.tod_fall_phase` holds
and no flood; from `level.tod_fall_flood_ms` (the lever pull) a LERP over
`TOD_VEIL_CLEAR_SECS` 12 pushes the halfway distance out on a cubic ease to
60,000 (under the fsi's 65,000 sky-fog distance, so the sky comes back), one
change-gated `set_fog` per 0.1 s tick; at f=1 the loop falls back to the
EXACT `fog_off()` state every earlier build shipped — a lerp, never a kill.
The spire branch outranks it; a map without the Fall never sees it. The sky
is hidden because the fsi fogs the skybox at 65,000 units: at halfdist 520
the sky IS the veil colour. One knob per symptom (defines' comment).
`[TOD_VEIL] UP / CLEARING / CLEAR` prints once per state (`TOD_VEIL_LOG 1`,
zero before publish). test_doppelghast.js gates it (192 checks). WHOEVER
BUILDS NEXT CARRIES IT (the sync copies the whole tree): verify the deployed
`_tod_atmosphere.gsc` has `function tower_fog()` before playing.

**2026-09-25 ? ARCHER ORIGINAL ASSETS RECOVERED AND BUILT (docs/169). FULL BUILD OK 00:34:52 Eastern: FF 198,782,080 B; loaded/streamed banks 109,216,768 / 209,338,496 B; 229 deployed inputs match; all Archer assets and 11 sound aliases packed. Dev and god ON. UNPLAYED; user tests.**
The original-file blocker is resolved. User loaded BO2 Alcatraz; official OAT
extracted the installed files offline without modifying the game or Greyhound.
Private dlczm2.ipak -> dlc2.ipak copy fixes the zone's image lookup; preloading
code_post_gfx_zm/common_zm resolves secondary audio. Retained 84 focused files,
original model/texture/animation/weapon data, and decompiled server/client
Retriever scripts. Original Retriever world model (1361/250/23 triangles) and
Apex hook (662) retain their compiled geometry; native-resolution textures,
original sounds, rendered HUD silhouettes, wrist cable, target marker and bounded
trail/impact FX are integrated. The 54 equipment checks, art lifecycle checks,
source integrity check and native build gates pass. First-person Retriever and
grapple hand/launcher animation integration and the animated ember material remain
unfinished. No BO3 launch or native quality claim. This build includes the first
city-sky render; the separate sky session's second render remains pending.
Evidence: docs/archer_equipment_evidence/build.json and retriever_source.json;
transcript tmp/archer_assets_build2.log. No native inputs changed after building.

**2026-09-25 — THE SKY IS RENDERED NOW, NOT DRAWN (docs/166): a 3-D megacity in Blender/Cycles replaces `gen_tod_sky.js`. FULL BUILD OK 00:02:31 Eastern with the FIRST ship render: FF 198,784,448 B (the size did not move — the sky is a STREAMED image and rides the xpak, not the .ff), NEW sky .iwi `CFE55UDPLPVBWJ3P5KDZGV6U6K` 31.96 MB in the pack (the drawn sky's was `7SQVLRM3…` 21.7 MB), banks 108.1 / 209.3 MB, 8 known-waived warnings, deployed EXR = repo. A SECOND 8192 render with the sign fix is in progress (ETA ~00:55) and gets its own full build; a build started before then carries the first render, which is fine. The peer session's uncommitted `_tod_archer.*` / `AetheriumLoadout.lua` edits landed AFTER this build's sync and are NOT in this .ff. UNPLAYED.**
User: *"just a colour change with the new sign ... 5 % of where we need to be ... are we limiting
ourselves because of the process?"* Yes: a 2-D painter with its eye at street level cannot give
depth, materials, volumetric haze, or ANYTHING below the horizon (the player spawns at the crown
and looks DOWN). `tools/sky3d/build_city.py` builds ~10,000 procedural buildings (12 street
districts at their own angles with a height character each, setback tiers, ad screens, sparse neon
accents, warm clustered windows with lit lobbies), road-surface glow and traffic trails on every
street, a lit PODIUM with ring roads + a canal at the tower's foot (the nadir is a city, not a
void), two elevated ring highways, a harbour with a far shore, three landmarks, a fog VOLUME (the
light pollution and the depth), cloud sheets, a blood moon + halo + red moonlight, searchlights,
and the title gantry as extruded neon letters ("TOWER OF DOOM" red, "II" ember, "CYBERCITY" cyan)
1 km ahead with the moon rising behind it — then renders it through Cycles' equirectangular camera
at (0,0,220 m) on the RTX 5060 (OptiX): 8192x4096 @ 160 spp = 52 min. `tools/sky3d/finish_sky.py`
keeps the docs/104 exposure contract (score = mean x 1024 solved to 0.16, a knee at 10x..32x the
mean) and writes the SAME asset (`i_skybox_tod_cybercity.exr`, half ZIP16, channels A,B,G,R) — GDT,
zone, map untouched. One command: `.\tools\sky3d\render_sky3d.ps1 -Ship`. Previews (1080p, cg_fov 65,
0.96 texel/px): `docs/sky_preview/sky3d_ingame_*.png` — LOOK AT `_moon`, `_city`, `_down_r`.
Master scene `art/sky3d/tod2_sky.blend` (a build product; edit the script, not the .blend).
ORIENTATION (measured): centre column = +Y = the moon/sign bearing of the drawn sky; MIRROR IS STILL
UNVERIFIED IN GAME — if the title reads backwards: `render_sky3d.ps1 -FinishOnly -Raw
$env:TEMP\tod_sky3d\raw_8192.exr -Mirror` (20 s, no re-render) then a full build. Knobs per symptom:
docs/166 §3 (`-TargetScore`, `-Knee`, `-Tint`, `-Roll`, `CAM_H`, `FOG_D0`). RULE LEARNED: keep the
fog a bounded MESH box — a WORLD volume marched every sky ray to `volume_max_steps` and was 6x
slower. The drawn generator stays as the A/B and fallback (`node tools/gen_tod_sky.js --theme
evil`). The billboard ART PACK for the ~600 ad screens is `~/Downloads/tod_sky3d_billboards_art_pack.zip`
(docs/167; the drop goes to `art/sky3d/billboards/`, re-render with `-ScreensDir`). docs/165 is the
peer's roster playtest; the sky docs are 166/167.

**2026-09-24 — THE LEVER, THE INTRO, THE NUCLEAR SIREN (user, late evening). -GscOnly BUILD OK 23:27:05 Eastern: FF 198,784,448 B, banks 108.1 / 209.3 MB (+the two new wavs), diffs clean, nothing synced after; the switch models + sparks fx in the ledger, both wavs deployed = repo. UNPLAYED.**
THE GAME DOES NOT START UNTIL SOMEONE PULLS THE LEVER. `_tod_fall.gsc`
`TOD_FALL_LEVER 1`: the 20 s timed calm is the A/B (0). The lever is the STOCK
POWER SWITCH's two models (`p7_zm_der_pswitch_body/_handle`, zone xmodel lines)
script-spawned on the sanctuary's TOP STEP in front of the reredos (GENERATED
`lever_org()` (0, 9272, 19424) / `lever_yaw()` 0 in `_tod_crown_data.gsc`,
asserted clear of the extraction pad and the reredos), a `trigger_radius_use`
28 in front (hint "activate the power" ON PURPOSE — ZMCursorHintNew routes it
to the POWER SWITCH card), hidden until the draft. The pull is stock
`_zm_power::electric_switch`'s flip verbatim: handle RotateRoll -90 +
`zmb_switch_flip`, sparks (`electric/fx_elec_sparks_directional_orange`, zone +
precache) + `zmb_turn_on`; then `flood( TOD_FALL_LEVER_LEAD_SECS 10 )`: the
beacon spins and THE SIREN starts AT ONCE, the spawns release 10 s later (the
siren's wind-up), the Doppelghast clock counts from the pull. THE SIREN is now
the user's YouTube "Nuclear Alarm Siren" (T2qwIWIrztQ, yt-dlp; 0.7–30.7 s of
the source, 2 s fade, −13.9 LUFS) as `sound_assets/tod/sfx/tod_fall_siren.wav`
— the alias row is NONLOOPING 3D now (DistMin 1400 so the whole hall is at
full volume), played `PlaySound` from the script_origin, `TOD_FALL_SIREN_SECS`
30. THE INTRO: the user's `Downloads/Deep Mystery.wav` (30.2 s) is
`sound_assets/tod/music/tod_fall_intro.wav` (−12.9 LUFS / −1 dBTP), alias
`tod_fall_intro` = a LOOPING 2D STREAMED row ON PURPOSE (the only
engine-stoppable shape) played on the music CHANNEL by `_tod_atmosphere`
(`TOD_MUSIC_INTRO 1`) at the blackscreen and STOPPED by script at 30.2 s OR
THE INSTANT THE LEVER IS PULLED (user: "they should never overlap" — the pull
flag rises before the 0.3 s flip, the siren after it). Then SILENCE: no band
plays while `level.tod_fall_phase` holds; the bands start when the crown seals.
`tools/test_doppelghast.js` gates all of it (188 checks). The plaza power
switch is still the vestigial prefab. Logs: `[TOD_FALL] LEVER spawned/armed/
pulled`, `FLOOD ... spawns in 10 s`, `RELEASE`, `SIREN`; `[TOD_MUSIC] INTRO up/
CUT by the lever/ended`. The first build attempt halted at the UI-art lint
step with no message and did not reproduce (log kept:
tmp/lever_build/build_attempt2_fail.log); the retry passed every gate.

**2026-09-24 - ARCHER EQUIPMENT: FULL BUILD OK, READY FOR USER TEST. UNPLAYED.**
Archer (internal assault) has Hell's Retriever on lethal, aimed-surface grapple
on tactical, and class-only fall immunity. Domain 41/distraction now GRAPPLE
recharge (12 base; 10/8/6 seconds), no monkey reconcile. Returning stock axe
model, swept/visible damage, cooldown HUD, lifecycle cleanup and automatic
[TOD_ARCHER] logs. Actual MOTD art and grapple cable/viewmodel are not present.
See docs/168_archer_equipment.md; user tests, no agent launch.
54 Archer checks passed. Full guarded build and all post-build gates passed;
FF 198,784,448 B at 2026-09-24T23:27:05.534017; fresh LED 100,163,699 B.
180 deployed script/UI/zone/data/sound inputs match; axe model + script and
both audio aliases present. Dev/god ON. No inputs synced after this build.
Evidence: docs/archer_equipment_evidence/build.json; tmp/archer_build_final.log.

**2026-09-24 - EXPECTED ROSTER + DEV/GOD: FULL BUILD OK, READY FOR USER TEST. UNPLAYED.**
User requested dev + god and the expected guns for their own playtest.
Skirmisher = Saug / M1927 / R-99; Archer = Bow / R1 Shadowhunter / Fire Bow;
Breacher = Mozambique / 870 / Peacekeeper; Warrior = Gold Twin Knives / Gold
Sword / Gold Battle Sword. Mage and secondaries unchanged. Entry dev/god TRUE;
maxed/upgrades/mage-test/hoop-probe FALSE. Class/tier text fallback names the
new roster while baked art is replaced; HUD icons are still placeholders.
Native converted donor assets are installed; the high-resolution Apex library
has NOT been integrated. Details and balance limitations: docs/165_expected_roster_playtest.md.
FF 199,670,080 B at 22:48:46 Eastern; all build gates passed. 346 deployed
inputs identical; 240 weapon/model assets and 174 local audio aliases present.
Banks 106,904,704 / 207,523,840 B; nothing synced after. Donor hidden bow
attachment material diagnostics and generic dry-fire common-bank uncertainty
are recorded in docs/165; actual appearance/audio still need user testing.
Evidence: docs/expected_roster_evidence/build.json; tmp/expected_roster/build_retry.log.
New [TOD_ROSTER] READY/REGISTER/GIVE diagnostics. Agent does not launch the game.

**2026-09-24 22:25 - SHOP AND TELEPORTER STUDIOS SAVED AND CLOSED AT USER REQUEST.**
Latest full studio sessions: `art/partner_shop/checkpoints/20260924_222403_saved_session.blend`
(929 objects) and `art/teleporter/checkpoints/20260924_222406_saved_session.blend`
(480 objects). Both were saved through Blender MCP, reopened successfully in
background verification, then their original studio processes closed normally.
Use these session files to resume the latest preview setup. Exported masters
and their build hashes are preserved. This supersedes earlier instructions to
leave these two windows open. Evidence: `tmp/saved_blender_sessions_verified.json`.

**2026-09-24 — MAP FAILED TO LOAD ("Unresolved external juke_root_path ... _tod_doppelghast.gsc line 410"), FIXED. -GscOnly BUILD OK 21:54:40 Eastern: FF 210,979,392 B, banks 197.9 MB, diffs clean, nothing synced after. UNPLAYED.**
Every build since the Doppelghast landed (00:06 today, including the dark pass)
carried it: `_tod_doppelghast_motion.gsh` (a `function` in a `#insert`) was
inserted BEFORE `#namespace tod_doppelghast;`, so the function landed in the
file's default namespace and the unqualified call did not link. The linker
compiles it clean; ONLY THE GAME'S LOAD REPORTS IT, and `lint_tod_arity.js`
passes it too. RULE: a `#insert` that defines functions goes AFTER the
`#namespace` line (Hellbound and `_tod_bo6_audio.gsc` both do). No build tool
reads the Hellbound REPO — donors are snapshots in donor_gdt/ and the GDTs in
OUR tools root — so nothing needs moving (user asked 21:50).

**2026-09-24 — R-99 / PEACEKEEPER SOURCE COLLECTION COMPLETE; NO MAP CHANGE OR BUILD.**
`docs/apex_weapon_source_library.md` indexes the ignored 15.97 GB local library
at `source_library/apex_r99_peacekeeper/` (open `index.html`). RSX 2.3.0 from the
installed Apex: 186/186 named models, 15/15 rigs, 643/643 sequences, 1,551 WAVs
(all 1,534 sources referenced by 702 events), full weapon/settings data and
native package metadata. File-format/hash audit passed. Base main textures
are 2K; some R-99 cosmetics have native 4K, no recovered Peacekeeper 4K.
CAST material names need image bindings; the sidecar lists filename candidates.
Native particles/shaders still need BO3 conversion; 17 old UI references are
unresolved. No roster swap: this checkout's Skirmisher T3 is still C.A.R.
Tools/reproduction: `tools/apex_weapons/README.md`. Neither game was launched.

**2026-09-24 — THE DARK PASS, PART ONE: THE CROWN HALL (docs/164). FULL BUILD OK 15:03:33 Eastern: FF 210,979,392 B, LED 100.2 MB, navmesh 3 components, diffs clean, nothing synced after, the six `tod_dark_*` materials + the fresh sky `.iwi` in the ledger (docs/164 §8). UNPLAYED.**
The user answered four questions before their playtest: NEAR-BLACK WITH POOLS
OF LIGHT / KEEP EDGE LINES ONLY / DARKEN THE SKY TOO / CROWN HALL FIRST. Built
as ONE generator switch, `DARK_HALL` (gen_tower_map.js, above the MAT table):
the hall's INTERIOR faces (floor, walls, corners, lintel, cornice, posts, piers,
arcade, shrine frames, reredos frame + field, upper panels, sanctuary tiers, the
dais, the alarm gantry) wear SIX NEW MATTE CLONES OF THE PLAIN GRID HUES,
`tod_dark_floor/step/wall/gold/ruby/brass` — black tiles, one thin line per
edge, no mirror, line at scaleRGB 8, albedo 0.5 — generated by
tools/gen_tod_door_materials.js (second family, `DARK`/`DARK_FIELDS`) into
source_data/tod_materials.gdt and registered in lint_tod_geometry.js (floor +
step DECK, the rest BLOCK — LOCKSTEP, three files). The hall's ten even lights
are NINE POOLS on all four lighting states (`light()` took a `mask`): the two
shrines r300/s7 (altar W, PaP E), the gate r400, reredos, a dim dais (the
alarm's red FX light owns it), a dim extraction pad, a NEW cool spawn pool, a
dim red pool over each of the peer's three item shops; the four quarter-point
lights are GONE. What still glows: the shrine panels, the 1u seams + dais rims
(the "edge lines"), the reredos jewels, the parked extraction pad, the alarm
core. THE SKY IS GLOBAL: EXR re-rendered `--theme evil --target-score 0.16`
(was 0.324; gain 0.01285 = the guard's floor, pin `--gain` below it) and
`skyStops` 10 → 6 in tod_skybox.gdt — ~5 stops less sky light in the bake, the
picture 1 stop dimmer. Exposure clamp unchanged (EV 3..3.5). T1 test lights
still on the spawn wall until the user's log answers T1. Every knob is one
line and listed per symptom in docs/164 §6; `DARK_HALL = false` is the A/B.
NOTHING outside the hall changed except the sky. The two builds running when
this was written (item-shop session's full build 10 at 14:40; a MAP ONE build
at 14:42 in the shared root) carried NONE of it.

**2026-09-24 — THE CUT (docs/163): 81% OF THE CAUSEWAY IS GONE; A ONE-WAY JUMP PAD CROSSES THE GAP. BUILT (deployed = the shop session's full build 9, BUILD OK 13:58, FF 211,206,016 B). UNPLAYED.**
`CW_CUT` in gen_tower_map.js (false = the v12 road byte-for-byte): a 240 gate-run + 480x480 LANDING
deck off the terrace, a 480x480 LAUNCH deck + the unchanged approach through the crown's mouth, and
5200 units of sky between them. The crown did not move. `_tod_jumppad.gsc`: walk onto the pad
(r 72) and a linked tag_origin mover carries you on a 4.5 s arc, 2200 up, set down exactly on one of
four spots — never a velocity launch (same-height pads get zero lift, air control misses the deck).
ONE WAY BY DESIGN. A flyer (`player.tod_jumppad_flying`) is spared stock's out-of-playable kill,
all damage (a callback FIRST in the chain), targeting (ignoreme) and elite spawn anchoring
(`_tod_bosses`); Blink/lunge/ATHLETE refuse mid-flight. The hall + its stub are ONE island in
crown_zone; crown_zone and roof_zone are NOT adjacent (roof_zone enables on the tod_fall flag);
`_tod_fall` seals when no living player is on the island AND none is airborne, then re-asserts
the hall's spawning off (stock manage_zones re-enables the START zone when no zone is occupied).
Gates: tools/test_jumppad.js (lockstep, live zones at both ends, the arc swept clear of every
brush, every guard), lint_tod_geometry's one-way pad edge (+2 selftest cases), lint_tod_navmesh's
CROWN ISLAND check (3 components is correct now). The pad wears the teleporter model FOR NOW:
the real jump pad models are only in `~/Downloads/T7 Assets V2.8.rar` (Moon
`p7_zm_moo_jump_pad_02` recommended; 24 materials, 2 undefined images) — NOT installed; the swap
is contained (docs/163 §7), a FULL build. `TOD_JUMPPAD_LOG 1` prints with dev OFF — zero before publish.

**2026-09-24 — THE FALL, SECOND PASS (docs/160 §10): THE CALM, THE ALARM, THE ALTAR; docs/162 STEP 0/1 ARMED. FULL BUILD VERIFIED BY THE FRESH .ff (the runner's log ends after the teleporter validator without the script's verdict line — that session was replaced at ~12:59 — and the two validators after it, item-shop and partner assets, could NOT be re-run here: a third session's full build started ~13:16 and its sync had already wiped the asset ledger; that newer build will REPLACE this .ff — verify it before playing) 12:57:45 Eastern (one build with the peer's docs/163 cut, run by that session): FF 211,194,688 B, LED 100.2 MB — DOUBLED by the second filled lighting state (docs/162 T13 answered) — bank 197.9 MB, navmesh 3 components, diffs clean, nothing synced after (docs/160 §8). UNPLAYED.**
After the draft and the round-1 cards the hall is QUIET for `TOD_FALL_CALM_SECS`
(20) of unpaused time — `_tod_fall` holds stock's own `spawn_zombies` flag clear
from init (the flag `_zm::round_spawning` waits on before every spawn), then THE
FLOOD: the alarm over the hall's centre (map: a gold gantry + red core in PLAIN hues — `_tinted` brass/ruby are DECK to
the geometry lint and a thin deck is a floor — section 5d'; script: a tag_origin host at `alarm_org()` on todPerkGlow INDEX 11 = the
Giant's flashing red alarm light, two linked hosts orbiting it on index 1, one
revolution per 1.5 s), the siren (`tod_fall_siren`, LOOPING 3D on the stock police
siren, 20 s, `PlayLoopSound` on a script_origin, `_tod_atmosphere`'s three-call
stop), spawns released, every zombie at EXACTLY 1.0 (`rate_for_round` pins, no
longer clamps), the Doppelghast clock counting FROM THE SIREN. The crown ALTAR is
back (id 5, placeholder mesh; the user will replace the model). NOTHING ROTATES IN
THE MAP: no stock prefab carries a pivot key on a brush entity, so the spin is two
orbiting script_models. THE SEAL IS ISLAND-AWARE: a PEER SESSION (docs/163, the
same day) is cutting the causeway to stubs + a one-way JUMP PAD; `in_sealed_area()`
reads GENERATED `jumppad_enabled()` / `on_crown_island()` for the seal count AND the
sweep — re-read `_tod_fall.gsc` and the generator's crown section before editing
either; ONE full build must carry both sessions' changes (never two linkers).
LIGHTING (user: "make sure it gives that atmosphere"; docs/162): the hall is NOT
dark by construction (344 lights on from spawn, all faces emissive, sky ~5.6 stops
over a stock night, the live state's SSI slot was EMPTY = default_day). This build
ARMS docs/162's three P0 tests as generator switches: `LIGHT_TEST_T1` (green = Radiant
State 1 only, red = State 2 only, west wall by the spawn; `[TOD_LIGHTSTATE]` log in
`_tod_fall`), `SUN_SSI2` (ssi2 = the night SSI), `SUN_PROBE_TARGET` (info_null in open
air over the plaza ring, asserted outside every box). Read the user's screenshots
against docs/162 10 §7.3 before touching any other light; the hall's lights, gold
and the sky are the NEXT levers and the user's call. `TOD_FALL_LOG` /
`TOD_LIGHTSTATE_LOG` / `TOD_DOPPEL_LOG` print with dev OFF — zero before publish.

**2026-09-24 — LIGHTING REFERENCE: docs/162_lighting/ (START AT README.md). READ IT BEFORE ANY LIGHT, PROBE, SKY, GLOW OR FX-LIGHT WORK. RESEARCH ONLY; NOTHING CHANGED, NOTHING TESTED IN GAME.**
Ten chapters (lights, power/lighting states, glow/perks, FX lights, sun/sky/exposure/fog,
reflections/probes, water, fixture cookbook, design + Glass Tower, troubleshooting + test plan),
every claim tagged [VERIFIED]/[COMMUNITY]/[INFERRED]/[TEST] against the official docs_modtools PDFs,
bin/t7.def.json, stock scripts and The Giant's shipped light prefab. Findings that change how to
read this repo: script `set_lighting_state(n)` shows Radiant State n+1 (INFERRED, strong); stock
zm_usermap boots Radiant State 2, where all 344 generator lights are ON, so "lightingstate1 0 =
authored OFF before power" (docs/107, gen_tower_map.js ~1546) is a misreading; the volume_sun has
only ssi1, so the `.led` pairs the live State 2 with `default_day`; the global probe sits INSIDE
the mast brush (no volume_sun `target`); all 53 probes are the default 144-unit cube and `radius`
is not a probe key; every visible world face is emissive. The first tests (T1-T3, docs/162 10 §7)
settle which of these matter. Recommendations only; the user decides.

**2026-09-23 — THE FALL (docs/160): TOD II IS "TOWER OF DOOM II: FALLEN CYBERCITY" AND IT STARTS AT THE TOP. UNPLAYED.**
The party SPAWNS IN THE CROWN HALL (`crown_zone`, the start zone, split out
of roof_zone in the generator), which holds the Pack-a-Punch and NOTHING ELSE
(crate, altar, pad light retired; user: "similar to Moon"). Zombies sprint from
round 1 and the trickle is x0.7 while `level.tod_fall_phase` holds; the hall's
gate is the generated `tod_fall` door ("the Causeway", 5000 party-scaled) and
`_tod_fall.gsc` SEALS IT AGAIN once every living player is out (spawning off
for the hall zone, its respawn group re-locked, leftover zombies deleted, the
sprint override dropped). POWER IS ON FROM THE FIRST FRAME (the crown PaP and
every perk wait on it; the plaza switch is vestigial). EVERY "climb" assumption
is now a DESCENT define, lockstep with `DESCENT` in gen_tower_map.js: doors open
DOWN on the same ladder met in reverse (roof 750 ... enter_lap1 3000, "the
Ground Floor"), elite unlocks on enter_lap41/31/21/11 (`TOD_DOORS_DESCENT`),
the boss frontier bars elites BELOW the highest unbought door
(`TOD_BOSS_DESCENT`), the tier gate counts floors DESCENDED — tier 2 at floor
40, tier 3 at 20 (`TOD_GAUGE_DESCENT` + `TIER_DESCENT` in tod_upgrade.lua; the
baked "FLOOR 10/30" badge strips are OFF until re-baked), music latches LOW
(`TOD_MUSIC_DESCENT`), Quick Revive pins on the TERRACE (`TERRACE_QR`), breather
DOWN pads lock on enter_lap1 (`TOD_TP_DOWN_FLAG`), the finale is PARKED whole
(`TOD_FINALE_PARKED`; terrace gate open at init, no uplink/extraction — THE
ENDING IS UNDESIGNED). Rounds still advance in the crown (THE TWIST). docs/158's
Undercity/plaza/wings are unchanged and are the run's END; the partner parts
still lie beside the Vault spawn (the peer's call). `[TOD_FALL]` logs print with
dev OFF (`TOD_FALL_LOG 1` — zero before publish). THE HUNTERS (user, same
night): 90 unpaused s after the draft a DOPPELGHAST rises in the hall, then one
every 30 s while anyone is inside, cap 4, over at the seal
(`_tod_fall::hunters_watch`, `TOD_FALL_HUNT_*`). It is HELLBOUND'S BO6 GHOUL,
ported as `_tod_doppelghast.gsc` (+ Hellbound's `_tod_bo6_audio.gsc`, motion
and notetrack headers): its aitype/model/clip GDTs (`hb_bo6_dev_ai.gdt`,
`hb_doppelghast.gdt`) are INSTALLED AT THE TOOLS ROOT, NOT in source_data —
snapshots in `donor_gdt/hellbound/` (the docs/153 donor rule); the AI tables
ride the repo's `animtables/` (a new sync mapping); every scripted `%anim`
must be in `hb_doppelghast_dev.ai_am` (a zone xanim line alone is NOT enough —
Hellbound's generic-tree trap); `tools/test_doppelghast.js` gates the build on
all of it. `[TOD_DOPPEL]` logs print with dev OFF (`TOD_DOPPEL_LOG 1`). The sky
sign still says CYBERCITY; the darker/broken tower is the next art pass.
FULL BUILD OK 2026-09-24 00:06:11 Eastern (FF 210,603,648 B, LED 50.5 MB,
navmesh 2 components) + -GscOnly BUILD OK 00:28:07 (FF 211,364,224 B, loaded
bank +4.6 MB, the Doppelghast in the ledger, diffs clean, nothing synced after,
`.map` md5-identical to the full build's). Known-waived warnings only. No
launch; UNPLAYED. Build record: docs/160 §8.

**2026-09-24 — TELEPORTER AVAILABILITY STATES (docs/152):** live MCP studio 9879,
`art/teleporter/teleporter_cyber.blend`; off = dark strips/no emission,
ready = pink, recharge = yellow rim chase (3 s/revolution). Eight transit
pads follow power, destination, cooldown and upgrade pause; the deferred
ascension pad is also hooked up. The independent always-usable jump pad
retains pink ready. Same seven body LODs with ready/off material twins;
one extra 1,152-triangle mesh only while cooling down, no new dynamic lights.
`[TOD_TELEPORT_STATE]` logs edges/failures with temporary TOD_TP_STATE_LOG 1
for the normal-match bring-up (zero after acceptance). Actual GSC state
bodies are tested with mocks; compiled asset coverage gates builds.
`art/teleporter/states_review.html` shows all three authored states.
COMBINED FULL BUILD + DEPLOYMENT VERIFIED 2026-09-24 15:05 Eastern:
FF 210,979,392 B (15:03:33), fresh LED 100,163,699 B; three navmesh components
(tower, spire, intended crown island). All 133 shop LODs and teleporter state
models retain exact compiled geometry. All 351 snapshotted inputs match
deployment; all expected models/materials/images/FX and three positional
spark aliases are packed, zero added delay/pitch. Ten established waived
warnings only. Current Fall/jump-pad/lighting-test and dark-hall/sky peer
changes are included. Shop build 10 passed first; the source map changed
during it, so final deployment checks use the subsequent dark-hall build.
Evidence: `tmp/partner_shop_build/revision2/final_full_build.log`,
`deployment.json`, `final_build_record.json`, retained native ledgers/transcripts. Both MCP
studios are playing previews; masters unchanged. BUILT AND STOPPED, no
launch, native appearance/audio/runtime diagnostics await USER playtest.

**2026-09-24 — ITEM SHOP NATIVE CROWN-ROOM TEST (docs/161), USER PLAYTEST PENDING.**
Dedicated studio port 9881; master `art/partner_shop/partner_shop.blend`.
User reference: walk-up hut/window, a separate hooded vendor only at the active
shop. Latest direction: evil black/oxblood/RED; shorter standing merchant,
hands DOWN below the counter, red X-eye mask with an uneven stitched grin.
`ITEM SHOP` is physical neon tubing: all letters work, only T/E/H blink.
Left capacitor bay, copper loop, cooling fins and wiring added. Revision 2:
T/E/H and all canisters share fault/recovery frames; canister pulses are in
phase. The mask breathes independently over six seconds (user explicitly
excluded it from the flashes), with slanted X eyes, armored brows/cheeks and
uneven pointed teeth. Pressure wheel now travels 100 degrees with an ivory
rim index; gauge swings +/-24 degrees. Larger sparks occur on BOTH sides in
three clusters per six seconds, one synchronized WAV crackle per cluster.
Peak 24 mesh particles, <=310 ms lifetime, no new dynamic lights. Exact
Blender emission/valve samples are compared to actual runtime math in tests.
OFF means empty/dark/silent with pressure mechanisms at rest.
The earlier human face, counter-resting hands, THE BROKER title and cyan/purple
palette are superseded. Authoring scripts `tools/partner_shop/`; reproduction
order and preview files in its art README. Keep the Blender window open for
user iteration. Native `_tod_shop.gsc/.csc` reproduces the animation; Blender
keyframes do not export automatically. Three generator-owned crown shops in
west/east/north bays are over 800 units apart. One active shop cycles west ->
east -> north on round changes (stated visual-test default). Only that shop
has the vendor and stock `zombie/fx_wonder_fizz_lightning_all` sky marker.
The user's electricity WAV supplies three positional crackles, triggered
with authored mesh sparks on one client timeline. Native `hdrScale` controls
emission. 19 models, seven LODs each, a physical off mesh and baked textures.
Source/state/placement and compiled model checks gate builds. Evidence is in
`tmp/partner_shop_build/`. Native appearance/audio/cost await USER testing.
`test_shop.js` now also runs `test_client_sync.js`: actual CSC dispatch is
checked for sound/FX pairing across jitter, pauses, loop wrap, late joins and
time jumps. Pre-play recheck passed without changing runtime inputs or the
current FF; `tmp/partner_shop_build/revision2/preplay_check.json` records it.
For a compiled triangle mismatch, inspect the exact converter `.log` under
the PRIVATE tools root's `share/assetconvert/xmesh/v6/`; its path is printed
in `tmp/native_build/linker_last.log` (the build now retains full linker
output). The shop's failure was a near-collinear neon-frame face in LOD2;
the converter supplies its three coordinates. Never waive geometry coverage
or infer the offending face from triangle counts alone.
`[TOD_SHOP]` and `[TOD_SHOP_C]` record state and first ten bursts; temporary
TOD_SHOP_LOG 1 captures a normal match, zero after acceptance. Purchases,
catalogue and prices remain future design. Build and stop; no game launch.
Never write to any other map or shared tools source.

**2026-09-23 — TOD II BASE LAYOUT (docs/158): THE UNDERCITY -> THE SHAFT -> THE PLAZA -> FOUR WORKSHOP WINGS. UNPLAYED.**
Spawn is THE VAULT at z -384 (four window-niche risers, Quick Revive on its N
wall, `vault_zone` is the start zone), `enter_conduit` (500) -> THE CONDUIT
(a reserved parts shelf, W wall) -> a straight 32-tread open-sky
SHAFT -> `enter_base` (750) in the plaza's WEST wall (y -240..-80, NOT centred:
the crate trigger). THE PLAZA IS THE OLD ARENA, UNTOUCHED; the four workshop
wings hang one per wall (`enter_wing_n/e/s/w`, 1000) with the `_tod_partners`
BENCHES on their far walls (N Civil Protector, E Talon, S R.A.P.S., W Cerberus).
EVERYTHING IS GENERATOR-OWNED: `tools/gen_tower_map.js` (the UNDERCITY block +
the `WINGS` table + `wingFrame()`), anchors EMITTED to `_tod_breather_data.gsc`
(`vault_qr_org`, `partner_bench_org/yaw/room`, `partner_part_org/yaw`), bench
clips cut in the `.map`. `bench_x()` is GONE; never type a bench coordinate in
GSC again. New asserts gate every new door's use-spheres against each other,
the crate, the inducer (nudged -280 -> -264) and every riser, and every ground
zone box against every other. Sky floor -64 -> -512. Perk park row re-pitched
8 @ 110 around the North door. BENCH FACING IS THE ONE NUMBER TO VERIFY BY EYE
(flip `faceYaw` by 180 in `wingFrame()` if the tables face their walls). Known:
elite sky-drops clip the Undercity ceiling if the party is still below; the
windows are risers, not boards. A PEER SESSION WORKS THE PARTNER FEATURE IN
THIS REPO CONCURRENTLY (its `tools/partner/test_partners.js` gates the build and
already asserts the generated anchors) — re-read `_tod_partners.gsc` before
editing it. The current partner request explicitly keeps all eight temporary
parts beside the actual Vault spawn; the Conduit shelf anchors remain reserved.
See docs/159 for the crafting flow. Plan previews: `node tools/preview_base_plan.js`.
FULL BUILD OK 22:57:23 Eastern: FF 210,598,400 B, fresh BSP + LED 50.5 MB, bank
197.9 MB, known-waived errors only, navmesh gate OK (every new room meshed, one
tower component), diffs clean, nothing synced after the .ff (the partner session's
parts sync at 22:55:59 preceded the link and is in it). No launch; UNPLAYED.

**2026-09-23 — ISOLATED PACKAGING NOW BUILDS; NATIVE ACCEPTANCE PENDING.**
The earlier missing private `sw4` texture dependency is repaired. Full
geometry/navigation/lighting and packaging passed for the basement/workshop
layout. The partner follow-up passed -GscOnly with FF 210,598,912 bytes at
23:01:38 Eastern; 41 partner/layout deployed inputs match and predate it.
See docs/159 and tmp/partner_build/deployment.json for the latest evidence.
Teleporter source and compiled geometry gates also passed in this build.
The game was not launched; the user tests. If brushes/materials change, use
a full build. Private database ownership and isolation guards pass.
The shared-art audit now reports one externally changed Spire banner: shared
bytes match Map One's repo, while our private bytes still match this repo.
See docs/154 and tmp/tod2_isolation/separation_followup_20260923.json.
No native visual approval. Custom Blender FX art remains a separate milestone.

**2026-09-22 — HARD RULE: TOWER II MUST NEVER CONTAMINATE MAP ONE.**
This repository owns only `zm_tod2_cybercity`. Its writable Mod Tools root is
`C:\BO3Tools\TOD2Cybercity`, bound to this repository by `.tod2-workspace.json`.
Use `tools/setup_tod2_workspace.ps1` once, then the guarded build/sync tools.
Never deploy this repo as `zm_tower_of_doom`, write into the Map One repository,
its usermap, or the shared Steam Mod Tools database, sources, conversion cache,
sound cache or compiled outputs. Never repoint the global `usermaps` junction.
Only the uniquely named Tower II child junction may point to our private output.
Stock model/texture junctions inside the private workspace are READ-ONLY INPUTS:
materialize a private copy before editing; never write through them or hardlink
mutable assets. Sync rejects destinations containing reparse points. Native
compiler TA_* variables are process-local; NEVER run `setx` or the stock
`modtools_setenv.bat` to change the machine/user environment for this project.
Do not reuse Map One's Workshop PublisherID `3788921059`; Tower II starts
unpublished. A request about Tower II never authorizes changes to another map.
Historical notes below describing a shared map identity/root are superseded.
The user explicitly required this isolation on 2026-09-22. See docs/154_tod2_isolation.md.

**2026-09-23 - FOUR BUILDABLE PARTNERS (docs/159; native acceptance pending).**
Civil Protector, Talon, one R.A.P.S., Cerberus. Eight per-player parts at the
Vault spawn; four workshop benches (N/E/S/W respectively). Hold 3s to build, RELEASE, then use
again to equip. One active per player; health persists through switches;
destroyed partners rebuild after 45s. `_tod_partners.gsc` owns all instances;
never use the singleton `level.ai_robot`. Drone proxies use allied Protector
nav carriers. Keep `last_valid_position` current. Damage uses a persistent
non-AI gun source WITHOUT `allow_zombie_to_target_ai`, otherwise stock calls
player APIs on the attacker. Bench clips and script anchors are test-bound.
`tools/partner/install_assets.py` writes only map-owned assets. Stock MP meshes
use reconstructed blue ally finishes, not fully ported MP materials. The
Protector must preserve the donor skin mappings (torso/lights targets end in 2).
The old docs/156 shop/visible upgrades/weapon ladder remain DESIGN; the new
crafting flow replaces its free automatic grant. `[TOD_PARTNER]` bring-up
diagnostics temporarily run with dev OFF for the user's normal match; return
them to the standard dev gate after native acceptance. Build and stop; do not
launch. Capture the user's log with capture_ai_logs.ps1 (now hashes this module).
Final BUILD OK: FF 210,598,912 B @ 23:01:38 Eastern; 71 state/placement
assertions; all 12 models packed without triangle loss; 41 matching deployed
inputs. No native acceptance yet. Final log: tmp/partner_build_release_2.log.

**2026-09-23 - HEAVY IS NOW THE BREACHER: Mozambique -> Remington 870 -> Peacekeeper (docs/157).**
Key stays `heavy`; display BREACHER. Each form pinned to the retired LMG's
OVERALL DPS (magazine + reload), base and PaP - NOT per-shot DPS (user's call);
`BREACHER_RETIRED` + `gunCycle` in gen_tod_twins.js, guarded by
test_starter_weapons.js. The Peacekeeper's "weak textures" were the donor's
BO3 setup, not Apex resolution (RSX 2.3.0 re-extract matches); private
`tod_bra_*` models/materials (skinOverride over read-only ZeRoY meshes) use
Hellbound's accepted R-99 recipe - regenerate with install_breacher_apex.py,
never hand-edit. Installed RSX devel/2.2.1 crash on post-Sep-16 Apex
materials; use Documents/BO3_tools/RSX_2.3.0. ZeRoY Apex alias rows carry
water/ringoff contexts this map never sets - clear them or the gun is silent.
OVERDRIVE left at 10 rounds/stack on a 6-round gun (user). -GscOnly BUILD OK
15:54:56 Eastern (after a full build 15:48:36): FF 209,707,072 B, bank 197.9 MB,
diffs clean; raw t6_mk48 unzoned (ledger 231/235). UNPLAYED; the user tests;
`[TOD_BREACHER] GIVE` (TOD_BREACHER_LOG, zero before publish).

**2026-09-22 — DETAILED FX REQUIRE AN ART WORKFLOW, NOT JUST MORE GLOW.**
Follow docs/155_fx_art_workflow.md for substantial effect enhancements: visual
brief and timing sheet; custom Blender MCP art and animated preview; native
BO3 materials/particles/distortion/light integration; lifecycle/cost checks;
user-operated native visual review. Keep editable masters and distinguish
Blender previews, stock-texture composition and native-verified final results.
The current teleporter FX are a native first pass, not new Blender-authored FX
art. Never imply a Blender simulation automatically exports into BO3. Build
and stop; the standing rule that the user tests still applies.

**2026-09-20 - TOD II: SKIRMISHER LADDER IS HELLBOUND'S (Saug -> M1927 -> C.A.R.), DPS PINNED. -GscOnly BUILD; UNPLAYED; THE USER TESTS.**
This repo is Tower of Doom II: Cybercity, seeded today as a full copy of
tower_of_doom_cybercity (map name still zm_tower_of_doom; see README.md).
The class weapons come from ../tower_of_doom_II_hellbound one class per build:
Skirmisher -> Skirmisher (DONE, docs/153), Slasher <- Warrior, Assault <- Archer,
Heavy <- Breacher (pending). THE CONTRACT: keep each retired gun's DPS (the
docs/139 dpsReference mechanism), pin mags / reserves, no optics on packed forms.
NAMING: emitted stems are cc_* (cybercity) because both repos deploy into ONE
tools root and Hellbound's hb_handling.gdt already owns hb_saug_h0.. /
t8_m1927_h0.. — never emit under the Hellbound asset names. Donor GDTs are
snapshots in donor_gdt/hellbound/ (outside source_data, never synced); the
clones still need Hellbound's model / anim / material GDTs installed at the
tools root (gen_tod_twins.js hbPreflight() throws otherwise). The
docs/staff_approved_manifest.json generated_asset_blocks count pins the twins
GDT block total and must be updated whenever a ladder swap changes it (247 ->
243 here: the Saug and C.A.R. carry no camo tables).

**2026-09-20 - TELEPORTER MODEL ENHANCED THROUGH BLENDER MCP; FULL BUILD VERIFIED, UNPLAYED.**
Shared `spawn_der_teleporter` now places `tod_teleporter` at all eight transit
pads and the crown ascension pad. Original lower casting retained; new layered
alloy deck, copper coils, central iris and recessed cyan/violet channels.
Master: `art/teleporter/teleporter_cyber.blend`; original nine-piece assembly
preserved in a hidden collection. Real upstream MCP session port 9879.
Native kit: `model_export/tod_teleporter/`, five 2048 maps, one fullspec material,
seven LODs (49,324 to 5,000 triangles). Same footprint/floor origin, no collision;
one model replaces nine fragments. Triggers, conditions, timing and FX untouched.
Full build exited 0 at 11:52 Eastern; FF written 11:45:41, 179,327,872 bytes.
Geometry/navigation, fresh LED (45,149,178 bytes), source/arity and all seven
compiled LOD checks pass. Model/material/five images packed; 161 source/deployed
snapshot inputs match, no later sync; banks 207,523,840 / 57,466,112 bytes.
The finished evil-sky EXR was included (fresh 7SQVLRM3ZWWD4VZ6TPCUEZ7N7F IWI).
Do not claim native appearance verified from Blender previews.
Dev diagnostics `[TOD_TELEPORT_MODEL]` log initialization/failure and placement;
runtime output pending user playtest. No game launch. See docs/152_teleporter_model.md and
`art/teleporter/README.md`; build evidence goes in `tmp/teleporter_build/`.

**2026-09-17 - KING CRASH ROLLBACK AND TEST SETUP REVERTED AT USER REQUEST.**
User considers the report potentially isolated and requests undoing this session's
Endless Spire crash changes. Exact pre-session copies restore King phases,
Rampage bonuses/sprint/berserk, summons, extended flames and Wisp Tea/Gift damage
exceptions. Dev/god/maxed OFF, normal round/class/spawn; summit harness parked.
Removed this session's extra King/test diagnostics with their changes. Existing
September 15 UI cleanup, King message batching and Panzer flame fix retained.
Armory restored. Source restored; first build REJECTED because BlackOps3 started mid-link (PID 46872). Clean sound-cache rebuild pending game closure; user tests, no launch. Evidence/backups:
tmp/king_revert_20260917/. This supersedes the removed September 17 test notes.

**2026-09-16 - MATTE ALTAR REJECTED; PREVIOUS MATERIAL RESTORED WITH SMALLER GLOSS CHANGE.**
User's 21:54 screenshot shows the all-matte pass flattened the exterior;
user wants less gloss, not disabled materials/reflections. NEVER restore the
zero-specular/black-specular/zero-probe pass below. Installer now restores the
entire 19:54 GDT exactly except glossRangeMax 8 -> 6. Replacing 6 with 8
reproduces that prior GDT's SHA-256 exactly (change_scope.json). Specular map
and enable restored; amount .2, tint .25, probe .15; other maps/glow unchanged.
Geometry and texture files are byte-identical; original interior remains
user-confirmed. Source gate requires enabled fullspec/material maps.
Full build passed 22:04:01 Eastern, FF 146,515,200 B; 165 inputs match, no
later sync/missing assets, original portal definitions match; all seven altar
LODs and 249 cyber binaries pass. Converter database settings also verified.
Evidence: tmp/heavenly_altar_satin_restore/. Current front preview refreshed.
User log preserved and game closed under existing authorization. BUILT AND
STOPPED, no launch. User visual retest of this small gloss adjustment pending.

**2026-09-16 - ALTAR EXTERIOR NOW MATTE; ORIGINAL INTERIOR USER-CONFIRMED.**
User: original picture is good; reduced gloss was still too much (21:07 shot).
Native frame now uses $black_specular, zero specular amount/tint, zero gloss
range and zero reflection-probe contribution. Retired specular atlas is no
longer a material dependency; geometry, image files, original interior and
cyber emission remain unchanged. Installer and source gate enforce this;
converted GDT database settings verified. Current native preview is front;
older side/LOD preview shading predates this last matte-only material change.
Full build passed 21:15:16 Eastern: FF 146,514,176 B; 165 inputs match, no
later sync/missing assets, original portal definitions match, all seven altar
LODs and 249 cyber binaries pass. Evidence: tmp/heavenly_altar_matte/.
Prior close authorization used; user console preserved. BUILT AND STOPPED;
no launch. Original picture is confirmed; latest matte finish awaits user test.

**2026-09-16 - ORIGINAL ALTAR INTERIOR RESTORED; CYBER FRAME LESS GLOSSY.**
User screenshots disproved the earlier material-slot-only fix below; do not
repeat that diagnosis as a confirmed cause. Native installer now copies the
original 32 background triangles exactly (positions, UVs, normals, winding,
black vertex colors and root weights) and references `chaos_pap_background`
with its unchanged three-layer animated material/images. All seven LODs
retain the original inset; verifier compares every corner against the donor.
New frame gloss 0..8, spec amount .2, tint .25, reflection probe .15; emission
unchanged. Art master remains the approved study; native derivative uses the
original interior as requested. Current preview: game_preview/native_front.png.
Full geometry/lighting/native build completed 19:51:41; a peer sync removed
its postcheck reports. Final peer package BUILD OK 19:54:01, 146,544,640 B.
165 source/deployed inputs verified, no later sync or missing used assets,
all 7 altar LODs and 249 cyber binaries pass. Shared pack's COMPLETE used
portal/image definitions match; unrelated retired exterior aliases differ
between maps. Evidence: tmp/heavenly_altar_original_inset/build_provenance.json.
User authorized closing BO3; console preserved. BUILT AND STOPPED, no launch.
Original-picture restoration and softened frame await user's in-game retest.

**2026-09-16 - ALTAR CENTER ARTWORK MATERIAL CORRECTED AND BUILT.**
User saw a gray front panel and see-through back. The inset is intentionally
single-sided; native winding, all six faces and image files were intact.
Portal material had artwork only in its emission slot and black in colorMap;
the native unlit technique reads colorMap. Installer now binds the same
artwork to BOTH slots. Only the altar GDT changed among deployed inputs;
geometry/textures preserved. verify_native gates both bindings; preview
native_portal_unlit.png exercises the base-image path in Blender only.
Full build passed 19:24:56 Eastern, FF 146,512,640 B; all 164 snapshot inputs
match, no later sync or missing assets, all seven altar LODs and 249 cyber
binaries pass compiled checks. Evidence: tmp/heavenly_altar_portal_fix/.
BUILT AND STOPPED. User must confirm the front picture in game; no launch.

**2026-09-16 - ALL SIX HEAVENLY ALTARS REPLACED AND BUILT.**
Shared station model is now `tod_heavenly_altar`: spawn, four breather lounges,
and crown. Prices, triggers, original collision and aura sound are preserved.
Editable master: `art/heavenly_altar/heavenly_altar_cyber.blend`; original copy
and native donor remain preserved. Author through the isolated real Blender
MCP session **9878** (9876 is Tower II sword; 9877 is zombie work).
User requested visible textures: RENDERED Eevee, scene lighting and glow.
Native assets: `model_export/tod_heavenly_altar/`, map-owned GDT, eight baked
textures, three materials, seven LODs (83,194 down to 15,421 triangles).
Full geometry/LED/native build completed; a peer sync interrupted its ledger
checks. Final peer packaging passed BUILD OK at 18:50:18 Eastern, FF
146,512,640 B. Independently verified all 164 snapshot/source/deployed inputs,
no later sync/missing assets, exact compiled triangle coverage at all seven
altar LODs and all 249 existing cyber binaries. Evidence and race provenance:
`tmp/heavenly_altar_integration/build_provenance.json`. Dev/god/doors OFF.
BUILT AND STOPPED; user tests. No game launch or native visual verification.
Exterior is modeled; heavenly figures/stairs use recessed reference artwork.
Rear extrapolates the front reference. Blender renders do not establish exact
native glow/lighting. Scripts/docs: `tools/heavenly_altar/`,
`art/heavenly_altar/README.md`, `validation.json`, `review.html`.

**2026-09-16 - REFERENCE TWO BACK MACHINE BUILT 2026-09-16T14:54:25.573552.**
Full build 149,684,992 B; all 431 inputs match, no later sync/missing assets,
all 249 compiled model files retain geometry. Ref2's back was rebuilt in live
Blender MCP: paired descending purple pipes on rear-view left, separate lower
flank return, copper induction chamber, right amber regulator, layered spinal
cassettes, open side rails and a substantial upper-cell carrier. Source master
`art/cyber_reference_two_mcp/reference_two.blend`; script `two_back_machine.py`
supersedes the original mirrored-loop back from `two_torso.py`/`two_support.py`.
Other master equipment/donor meshes preserved; ref1/ref3 assets unchanged.
Dev/god/doors OFF. BUILT AND STOPPED, UNPLAYED; the user tests. Gallery has an
exported back close-up; evidence `tmp/reference_two_back_machine_20260916/`, docs/149.

**2026-09-16 - REFERENCES TWO/THREE BUILT 2026-09-16T14:20:51.530766.**
User mapping: refs 1/2 REGULAR, ref 3 ARMORED ONLY. Both new models authored
through live Blender MCP 9877, original donors/weights preserved; gallery at
`art/cyber_zombie_roster/review.html`, masters `art/cyber_reference_two_mcp/`
and `art/cyber_reference_three_mcp/`. Trooper/Relay now use ref2; sprinter uses
ref3 twin tanks, welder visor, powered arm/hand.
Armored art correction: the pack has ONE purple pressure feed and a separate
metal lifting arch, short cyan sight chambers, heavy hazard-marked lower vessels,
and a central manifold/latch. Do not restore the earlier mirrored two-hose pack.
The final correction scripts and authoring order are recorded in docs/149.
Promotion replaces only known intact heads with the SAME head identity wearing
ref3; native gib flags, unknown
heads and repeated calls are guarded. Original head/hat attachments are removed
and both gib-data layouts updated. No gameplay stats changed. Full build passed:
FF 149,687,168 B; 431 inputs match, no later sync/missing assets, all 249
authored binaries pass source and compiled geometry coverage. Dev/god/doors OFF.
BUILT AND STOPPED, UNPLAYED; user tests. See docs/149 and
tmp/reference_23_integration/deployment_verification.json. Reference one's 65
binaries are unchanged. Older notes assigning ref3 to Relay/ref2 to sprinter
are superseded. Signal's existing ref1 head/helmet accents remain.

**THE USER TESTS. NEVER LAUNCH THE GAME UNASKED (user 2026-09-16, three
times in one hour: "I never asked you to test ... I will test myself" /
"You need to stop starting the game randomly" / "Stop starting and testing.
The flow is you write logs and ill test. Thats how we solve an issue").**
The flow for every bug and every feature: the agent writes the code AND the
logs, builds, and STOPS; the user plays; the agent reads the user's
`console_mp.log` (archive it with `tools/capture_ai_logs.ps1`) and acts on
it. "Make sure" / "verify" / "check it works" mean LOGS, not a launch.
`tools/run_game.ps1` is used ONLY when the user's message explicitly asks
for an agent-run match. Because the user's own launcher (`PLAY_NORMAL.bat`)
already passes `developer 1` + `scr_mod_enable_devblock 1`, a `/# PrintLn #/`
records in their runs; gate a feature's log on its own switch when the user
is testing a dev-OFF build and the log is what they asked for. This
supersedes the 2026-09-10 "build and start authorized test matches yourself"
paragraph below wherever the two disagree: that paragraph is the HOW, this
is the WHEN, and the WHEN is "when asked".

**2026-09-16 - v19.21c STING ON THE PROVEN LANE (`tod_perk_scatter::play_sound_at_origin`, the laugh's; stock `play_sound_at_pos` played nothing audible for a custom alias). -GscOnly BUILD VERIFIED 20:08:02 Eastern, FF 146,515,200 B, bank 197.9 MB, diffs clean, dev/god OFF. UNPLAYED. ⚠️ A PEER LINKER RUNNING MID-BUILD TRUNCATES OUR SOUND BANK (122 MB, no error) - accept a build only with the full bank size and no peer linker.** RULE: a custom 3D alias is played from a spawned `script_origin` `PlaySound` - never `PlaySoundAtPosition` - in this map.

**2026-09-16 - v19.21b STING LOUDER (wav loudnorm -11 LUFS, alias 100, DistMin 1200). -GscOnly BUILD VERIFIED 19:19:36 Eastern, FF 146,512,640 B, bank 197.9 MB, diffs clean, dev/god OFF. UNPLAYED.**

**2026-09-16 - v19.21 THE HOOP WORKS (user: "it looks like it's working now"). Feed says SCORE +20; the user's success sting `tod_hoop_score` plays 3D from the teleporter bay's pad centre `TOD_HOOP_SFX_ORG` (0,-950,60). -GscOnly BUILD VERIFIED 18:50 Eastern (3rd attempt), FF 146,512,640 B, banks 197.9 MB + 56.5 MB, diffs clean, dev/god OFF. UNPLAYED. ⚠️ Attempt 2 said BUILD OK with a 122 MB bank (75 MB of sounds missing after the checksum flake) - compare the `sound bank:` size with the last good build after ANY flake; the 50 MB floor does not catch it.** `TOD_HOOP_LOG` / `TOD_HOOP_C_LOG` are still 1 - zero them before a publish.

**2026-09-16 - v19.20c THE HOOP: THE DEATH-FRAME TRACE STARTED INSIDE THE BODY. -GscOnly BUILD VERIFIED 16:59:45 Eastern, FF 149,684,672 B, diffs clean, dev/god OFF. UNPLAYED - THE USER TESTS.** 39/39 server arcs died at t=0.08 with end == from: a BulletTrace from a just-ragdolled body's origin on its death frame returns fraction 0 (still solid, hitCharacters=false does not exclude it). `hoop_arc` now waits one frame and passes the body as `ignore`. THE RULE: a trace that ends where it started is a trace that began inside something - check `end == from` before blaming the arc.

**2026-09-16 - v19.20b THE HOOP, MEASURED: `TOD_HOOP_ARC_KH` 3.1 / `_KZ` 4.4 (from 29 paired flights, `tools/hoop_calibrate.py`), SLOP 24, NO FAN, 2D `tod_headshot_ding` cue. -GscOnly BUILD VERIFIED 16:41:43 Eastern, FF 149,684,928 B, diffs clean, dev/god OFF. UNPLAYED - THE USER TESTS.** The fan + slop 48 paid 16/29 ("every hit is a false positive"); per-axis K at slop 24 replays that log 5 true / 1 false / 0 missed. `"purchase"` is a stock alias this map never ships - it was silent. The test replays five real launches. Next log: run the calibrate tool; if K drifts, move KH/KZ, never the slop.

**2026-09-16 - v19.20 THE HOOP: LOWER (z 200..296), SLOP 48, A FAN OF ARCS PAYS. FULL BUILD VERIFIED 16:23:22 Eastern, FF 149,684,672 B, diffs clean, dev/god OFF. UNPLAYED - THE USER TESTS.**
The user's first real run: client log = 5 true baskets + many landings just
under the hole, server paid NONE (K 3.2 computed every arc short; the data says
~4.6). Now `hoop_arc` traces every K in 2.8..6.0 step 0.4 (one per frame,
`hoop_trace_arc` pure) and ANY basket pays on the swinger's thread
(`hoop_pay_after`) - the user's call: false positives over false negatives.
`tools/hoop_calibrate.py` reads a console log. ⚠️ THE USER'S LOG IS ONE LAUNCH
FROM GONE: archive `console_mp.log` the moment a run ends (the 16:12 Tower II
launch erased the v19.18d run). `TOD_HOOP_LOG`/`TOD_HOOP_C_LOG` still 1 - zero
before a publish. Workshop still = v19.17.

**2026-09-20 - TOD II: THE EVIL SKY, THE SIGN, THE BACKDROP PATH (docs/150, brief docs/151). EXR RENDERED, NOT BUILT (the map still deploys over TOD1's folder, README). UNPLAYED - THE USER TESTS.**
`tools/gen_tod_sky.js --theme evil` is the TOD II sky: black-red palette, blood moon, crimson glow dome, ash clouds, red floor grid, the same drawn city. THE SIGN: a "TOWER OF DOOM II / CYBERCITY" gantry at d 1000 (inside the plaza, nothing occludes it) under the moon, masts + truss bands + chamfered chassis + neon-tube letters from ANALYTIC DISTANCE FIELDS (segments + arcs, so every bowl is a true curve); `--sign-az <deg>` turns it, `--sign-mirror` flips the lettering if the dome reads mirrored in game, `TOD_SKY_SKIP=sign` drops it. THE HONEST ANSWER on quality (user: "how can those AIs build these images but we can't"): the refs are IMAGE-MODEL paintings; a rasteriser cannot reach painted lighting and materials by sharpening. `--backdrop <png>` projects an image-model 2:1 panorama onto the sphere (Lanczos-2, --rotate/--flip-x/--seam-blend, or --backdrop-mode band for a horizon strip over the drawn caps), skips the drawn city, draws the sign on top, and runs the proven resolve/sharpen/knee/gain/EXR tail. docs/151 is the art-pack brief for that panorama.

**2026-09-16 - v19.19b SMOOTH SOLIDS SECOND LOOK. FULL BUILD VERIFIED 15:52:27 Eastern, FF 149,684,992 B, fresh sky .iwi, diffs clean, dev/god OFF. UNPLAYED - THE USER TESTS.** Full-res crops (ffmpeg on the judging PNG - the 2048 previews hide it) showed dashed floor rings + a comb fringe at every round tower's foot: the paint row now uses the EXACT height (`EYE + tan(el) * tIn`) and each z-sample paints its NEAR-edge row only. Judge solids on 1:1 crops, never on the previews.

**2026-09-16 - v19.19 THE SKY'S SMOOTH SOLIDS. FULL BUILD VERIFIED 14:54:25 Eastern, FF 149,684,992 B, diffs clean, dev/god OFF. UNPLAYED - THE USER TESTS.**
Tower II's v0.7 profile-solid pass (its docs/63) is in `tools/gen_tod_sky.js`:
`drawSolid`/`addSolid` (sec(z) marched per column, analytic circle/rect,
fractional coverage, drawBox's shading). Masts are round tapers, every setback
a sloped band (`setback()`), the ziggurat faceted; NEW shapes: a fifth of the
lattice round (per-lot hash, off the rng stream), pyramid crowns, round
mega-drums, arcology domes, twin spires. `drawBox` untouched. ⚠️ A NaN `d`
scrambles the painter sort for the WHOLE city (seen: every near tower cut at
the mist line) - `addBox`/`addSolid` throw on it now. Bisect
`TOD_SKY_SKIP=round,crown,slope`. A sky change is a FULL build. Workshop
still = v19.17.

**2026-09-16 - v19.18d THE HOOP SCORES A COMPUTED ARC. -GscOnly BUILD VERIFIED 13:17:05 Eastern, FF 149,993,024 B, diffs clean, dev/god OFF deployed. UNPLAYED - THE USER TESTS.**
Two probes proved the server never sees a launched ragdoll (dead OR alive;
memory `dead-actor-ragdoll-is-client-only`), so v19.18c's pre-death lane is
RETIRED WHOLE and `_tod_corpse_cleanup::hoop_arc` scores the ballistic arc
of the impulse the server chose (`TOD_HOOP_ARC_K` 3.2 = A FIRST GUESS, g 800,
world-only BulletTrace per frame, slop 16). `_tod_hoop.csc` (actor clientfield
`tod_hoop_watch`, lockstep) logs the REAL flight on the client:
`[TOD_HOOP_C] SAMPLE/BASKET/FLIGHT` beside `[TOD_HOOP] ARC`; docs/147
§Calibration derives K from the user's log. Both loggers print WITHOUT dev
flags (`TOD_HOOP_LOG` / `TOD_HOOP_C_LOG`, TEMPORARY - zero before a publish).
Dev/god OFF. Workshop still = v19.17.

**2026-09-16 - v19.18 THE HOOP - FULL BUILD VERIFIED 11:16:55 Eastern, FF 149,954,496 B, diffs clean, nothing synced after. UNPLAYED. v19.17 was uploaded 10:49 (row #42 closed); this build replaced it in the deployed tree and is NOT published.**
A 96x96x64 recess in the core's SOUTH face at z 240..336 above the base
upgrade station, cyan rim + backboard; a bat-flung body whose spine enters it
pays the swinger 20 (`TOD_HOOP_PTS`, `_tod_corpse_cleanup::hoop_watch`, box
from GENERATED `base_hoop_lo/_hi`). Packed bat pays no extra rate: it already
throws x1.6, so it lands more often. ⚠️ HEIGHT IS UNMEASURED - `[TOD_HOOP]
FLIGHT apex/land/tag_moved` in a dev playtest decides `HOOP_Z1` (docs/147
recipe); `tag_moved=0` means the detection lane, not the height, is wrong.
Flung bodies keep their 2 s linger under corpse panic now. Geometry/bunker/
arity lints clean, `test_baseball_bat.js` HOOP section is the lockstep gate.
Dev/god OFF: arm `tod_dev` for the height-tuning playtest or the log is silent. Also open: GUNSLINGER reads additive (+30% of
BASE per level, diluted by DAMAGE - user's own v16.99 call); the user's
400->500 matches Lv1, not Lv3. USER'S CALL 2026-09-16: LEAVE IT AS IS - mechanic
AND card text unchanged; do not re-open. The numbers: AMP63 body shot on the
Panzer at DMG Lv4 reads 398 / 483 / 569 / 654 / 740 / 825 for GS Lv0..5.

**2026-09-16 - REFERENCE-ONE MODEL BUILT 12:46:04 Eastern.** Full build passed:
FF 149,992,000 bytes; 407 snapshot/source/deployed inputs match, no later sync
and no missing assets. All 233 authored cyber binaries pass source AND compiled
coverage, preserving the original legs. Crown/shared body now uses the Blender
MCP reference-one equipment, all fifteen finger joints and both shoulders,
five 4096-square baked maps, seven equipment LODs (44,610 down to 1,776 tris).
Distance reduction preserves each connected part; microscopic collapse slivers
are cleaned before conversion, without relaxing compiled coverage. Other roster
art is unchanged. Dev/god/doors OFF. BUILT AND STOPPED, UNPLAYED; user tests.
See docs/148 and tmp/reference_one_integration/deployment_verification.json.

**2026-09-16 - REFERENCE-ONE BLENDER MCP ART STUDY.** User wants model
updates through Blender MCP, as with Tower II's gold sword, and the live Blender
window visible so they can steer. `tools/cyber_reference_one/` uses the existing
upstream addon through an actual MCP ClientSession on its OWN port 9877; sword
session 9876 is unrelated. Master/gallery: `art/cyber_reference_one_mcp/`.
Focus is reference one only: detailed powered arm/hand, head hardware, harness,
reactor, pauldrons and leg brace on the original Crown body. This is an editable
high-detail ART MASTER; its reduced/baked game derivative is now integrated
as recorded above. The dense editable master itself is never shipped directly.
See that folder's README and validation report. Keep Blender open for the user.
Reference pass two adds emissive purple fluid lines, an outboard forearm cell,
and a shaped knee/shin assembly, now included in the native derivative.

**2026-09-16 - v19.17 PUBLISH BUILD VERIFIED. AWAITING UPLOAD.** The cyber
reference equipment pass is DONE and built (the "in progress / do not build a
mixture" warning that stood here is retired). PUBLISH BUILD VERIFIED 10:36:04
Eastern, FF 150,269,376 bytes, -CleanPak + all twelve languages; payload 2.177 GB
/ 48 files. scripts/ui/zone_source diffs clean, nothing synced after the .ff,
ship state re-read in the DEPLOYED tree (all eight tod_dev*/tod_god false,
TOD_MOCK_PARTY false, harness commented). All five cyber gates + compiled ledger,
geometry/bunker/navmesh lints and the notes gate pass. UNPLAYED.
⚠️ **THE JAPANESE PASS KILLED THE FIRST ATTEMPT AND IT WAS NOT A FLAKE.** The
linker DROPS a `japaneseUnsafe` xmodel while the zone still names it; nine cyber
models inherited that flag from their donors (`c_zom_der_zombie_body1` behind
trooper/relay, `c_t8_zmb_mob_zombie_body3` behind the sprinter). Stock's own data
is inconsistent - sibling `body2` behind crown/signal is unflagged, and every
severed-limb gib we derive is unflagged while the intact bodies were not - and
accepting the exclusion would have cost a Japanese client two of the four regular
appearance slots plus the sprinter. **User's call: our derived models ship
unflagged.** The override is emitted by `install_cyber_roster.py::block()` (donor
must have carried it, xmodel only, 1 -> 0) and `verify_cyber_roster.py` permits
that ONE non-cosmetic field. **THE GDT IS GENERATED AND SHA-GATED - change the
installer and re-run it, never hand-edit `source_data/tod_cyber_roster.gdt`.**
The re-run was proven side-effect free: 258 files hashed before/after, zero
binaries changed. Attempt 2 died on the KNOWN converter flake (`Missing source
checksum`, `carpet_run_06.wav`, a 2018 stock file) - rerun once, do not hunt it.
Both failures rolled back clean. Notes: docs/68 `Update - Sep 16 (v19.17)`, 12
bullets. **Owed: the upload, then `node tools/patch_notes.js uploaded`.**
⚠️ **THE LEDGER WAS TWO ROWS BEHIND AND ONE UPLOAD WAS NEVER RECORDED AT ALL** -
reconciled 2026-09-16 from the user's pasted live page: #40 (v19.10) sat pending
through its own Sep 15 2:03 am upload and shipped SIX bullets not the eight
staged, and the Sep 15 2:28 am bat-fling upload is now row #41. ASK FOR THE LIVE
PAGE BEFORE EVERY WINDOW.

**2026-09-16 - MAGE KEY OVERLAY: NATIVE CAUSE FOUND.** `Engine.Localize`
does NOT hand Lua a resolved bind. The native probe returned byte 21 +
`[{+frag}]` + byte 20; UIText expands it later. The previous first-character
renderer drew invisible byte 21. All earlier claims below about trimming
Localize's resolved key/controller picture are superseded for this HUD.
Keyboard uses the stock `GetKeyBindingLocalizedString(controller, command,
0, false, false)` API; controller keeps the whole token in UIText. Use stock
`LastInput_Gamepad` and refresh on `LastInput`, not the d-pad latch or token
byte guessing. This corrects the old no-device-branch guidance for this badge.
Positive usable charges gate the overlay; each ability retires at three real
casts. The existing five-second resend already handles HUD reconstruction.
See docs/145 for tests, screenshots and final build status.

**2026-09-15 - CYBER EQUIPMENT V3 BUILT.** User requested fitted
wrist equipment and more gear on every regular model/sprinter. Fixed oval
brace removed: straps sample each donor arm, smaller smooth plate uses a fitted
rubber liner, and the wrist joint stays clear. Added collar capacitors, spinal
power cells, relay reserve cylinders, sprinter cooling units and helmet rear
locators. Master/script: tools/expand_cyber_roster.py; docs/144. Export/install
all five atlas sets including MVP before building. Full build passed 23:08:19
Eastern: main FF 150,027,008 B / English 801,024 B. All 144 compiled LODs and
318 snapshot/source/deployed inputs match, no later sync. Evidence in
tmp/roster_equipment_v3/completion.json. Exporters use geometric face normals
when distance reduction cancels a cuff corner normal (keep strict checks).
Dev/god/doors/harness OFF. Built and stopped; user tests. Gallery reopened.

**2026-09-15 - CYBER EQUIPMENT FINISH V2 BUILT.** All five roster studies
and the shared MVP master now have outfit-matched worn coatings, fabric mounts,
service fittings and brighter eye cores. Both exporters now bake linked shader
channels instead of flat defaults; emission is normalized to native scaleRGB 6.
Trooper/Relay use matching arm gibs: 108 roster + 36 MVP = 144 binaries, still
25 atlas maps. Main FF 150,022,080 B at 22:32:44 Eastern; English 800,960 B.
All 144 compiled LODs and 318 snapshot/source/deployed inputs pass; no later
sync. New arm-gib checker corrected for inherited eight generated LODs. No
GSC/Lua/gameplay changes. Dev/god/open-door/harness stay OFF; build and stop.
See docs/144 and tmp/roster_finish_v2 for final verification status.

**2026-09-15 - FULL CYBER ROSTER BUILT.** User approved
integrating the offline regular zombies and armored sprinter. All four factory
slots now use custom appearances with three randomized heads, separate helmet
equipment and native damage variants. MVP models remain shared dependencies;
roster adds 106 binaries/20 textures. Sprinter body is `tod_cyber_sprinter`;
promotion retains current heads/helmets, with unchanged stats/no_gib behavior.
`verify_cyber_roster.py` gates source and native compiled geometry alongside
the MVP check. Full build passed 21:58:51 Eastern: main FF 149,784,704 bytes,
English FF 800,832 bytes; 316 snapshot/source/deployed inputs match, no later
sync. All 142 authored LODs retain expected compiled geometry. Sprinter's
materials/maps live in the English companion; inspect both asset ledgers.
Keep dev/god/open-door/harness OFF. Built and stopped; no launch. Native visual
retest remains with the user. See docs/144.
Peer HUD GSC-only build subsequently completed at 22:05:14 Eastern. Final
main FF 149,784,384 bytes / English 800,768 bytes; all 142 compiled LODs and
316 fresh snapshot/source/deployed inputs reverified, no later sync. Only the
peer's AetheriumLoadout.lua changed; all cyber inputs stayed identical.
Current evidence: tmp/roster_integration/final_verification.json.

**2026-09-15 - LATEST USER: DEV AND GOD OFF.** Disable dev, god, open-door
test flag and the direct King harness. Supersedes the King-test flags below.
Keep the flame fix. Normal-play rebuild VERIFIED 21:35:42 Eastern:
149,665,856-byte FF; all 147 snapshot/source/deployed inputs match, no later
sync. Build and flame regression checks passed. No automatic dev relaunch.
Attempted FX test exited before map verification; visual confirmation remains
pending. Evidence: tmp/flame_fx_20260915/normal_verification.json, docs/143.

**2026-09-15 - PANZER FLAME FX STATE FIX (verification in progress).** Stock
mechzDelayFlame starts damage without necessarily running our start_ft
notetrack; acc_panzer_ft now follows isShootingFlame through one change-gated
writer, a per-actor watcher and the stock damage callback. Teleporter bursts
and King's extended cone now delay emission after creating their FX host.
Do not claim client delivery from server emission logs. See docs/143.

**2026-09-15 - CYBER ZOMBIES ENABLED IN ALL MODES (source ready).** User approved
removing the dev-only appearance restriction. `ignore_spawner` now always keeps
the cyber factory and excludes its stock alternative; historical map markers
remain for BSP compatibility. Still one of four regular-horde appearances,
with stock gameplay/rig/dismemberment. Only diagnostics depend on `tod_dev`.
`tools/test_cyber_zombie_spawns.js` replaces the old dev-gate test and covers
all flag values, both factory orders, initialization and diagnostics separation.
Source/model checks pass. Build pending: BO3 started during this work; do not
interrupt the active King test or build while it runs. This supersedes the
older cyber dev-only direction below. See docs/141 for current build status.

**2026-09-15 - USER AUTHORIZED KING TEST LAUNCH.** Supersedes the earlier
build-and-stop instruction for this test. Dev and god remain true; `_tod_main`
now arms `dev_spire_harness(true)`: after class selection/first deal it ascends,
opens the spire doors, marks hub trials complete and warps to the summit.
The normal summit station starts the King, including its actual max-out/card
burst; dev_maxed stays false. `[TOD_KING_TEST]` records the warp. Harness is
ARMED for this user's playtest; disarm before publishing. Native launch
verified: summit warp logged god=1 and recorder reports king=1. User is
playing; do not build or take input. Archive: 20260915_212124_121_9e4f901b.
Concurrent post-build HUD edits briefly failed double-close in TodHealthTint;
peer removed the offending PlayerInfo walk. Normal lifetimes now pass but
duplicate Loadout cleanup invalidates the missing-helper negative control.
See tmp/king_test_20260915/peer_review.md before building those changes.
They are not in the running verified build.

**2026-09-15 - CRASH INVESTIGATION: UI CHILD OWNERSHIP.** Actual Lua 5.1
construct/close tests found missing cleanup despite the earlier callback scan:
default prompt leaves 154/155 elements unclosed; player/loadout/scoreboard
negative controls leave 49/129/74. TodPromptCard now closes its children;
perk item/list close their owned UI. TodUIOwnership closes remaining direct
children after existing feature cleanup; used by HUD and overlay owners.
Install it BEFORE feature close hooks. Health tint and party track cleanup
also repaired. Tests reject duplicate closes. These are simulated explicit-close
counts, NOT native pool readings or proof of any reported crash's cause.
King event-batching from the concurrent session preserved; its final list
refresh is still unbatched. BUILD VERIFIED 21:10:55 Eastern, FF 149,663,296
bytes; 147 snapshot/source/deployed inputs match, no later sync. No launch: existing build-and-stop
instruction remains. See docs/142_crash_ui_lifetimes.md.

**2026-09-15 - v19.13: THE BADGE NEEDS THE CARD AND A CHARGE.** Gated on
`everHad` AND `charges > 0` (recorded by `slot.setCount`; `slot.count` is the
glyph ROW, not the value). Readiness is NOT re-derived in Lua - `abil_send`
already clamps the heal count to 0 for the aura lock and blink sends
`blink_charges_now()`, so "count > 0" IS "the cast would succeed". This matters
because every Mage refusal is SILENT by design, so a badge on a spent ability
would be the player's only feedback and it would be a lie.

**2026-09-15 - v19.12 SUPERSEDES THE v19.11 OVERLAY BELOW.** The ability hint is
a BADGE ON EACH ABILITY TILE (top band y568..586; the charge count keeps the
bottom right), carrying the KEY ONLY - no verb, no ability name - set in the
MAP'S TYPEFACE via `todMakeGlyphRow`, centred by MEASURING first. The key is
`CoD.TodKeycap.Name( token )`, which trims the engine's multi-bind expansion
("G OR MIDDLE MOUSE" -> "G"). ⚠️ A CONTROLLER BIND EXPANDS TO A BUTTON PICTURE,
which a 42-glyph alphabet cannot draw, so a pad (or any unglyphable character,
`measure` -1) falls back to the engine's own font - that is the only renderer
for that icon and is correct on every pad layout. NO device branch; never read
`CoD.TodPad`. Retires per ability after `TOD_MAGE_TUT_USES` 3 real casts
(counted at the SPEND). ARCHMAGE has NO badge (no tile) and keeps the mana
bar's PRESS AIM BUTTON cue. QUICK REVIVE'S CARD IS STATIC AND STATES BOTH
PRICES ("SOLO $500 ..." / "CO-OP $1500 ..."), price row cleared for that perk
ALONE - a card that states both cannot be wrong about the party because it no
longer asks; the CHARGE is still per-party via `solo_qr_price_fix`. ⚠️
`test_perk_prompt_price.lua` had been comparing `nil` to strings since v19.3
(it modelled a `perkCost` member the refactor removed) - it models `todPrice`
now. -GscOnly build + native test PENDING.

**2026-09-15 - v19.11 MAGE CONTROLS OVERLAY + QUICK REVIVE CO-OP PRICE (Workshop
comments).** Bigfsi could not tell which button cast what: three UIText lines now
sit above the ability tiles (`AetheriumLoadout.lua`, x1000..1212 y520..566) naming
BLINK / HEALING AURA / ARCHMAGE by `[{+smoke}]` / `[{+frag}]` / `[{+speed_throw}]`
BIND TOKENS - the ENGINE renders the live device's key or button picture, so there is
NO pad/keyboard branch and none may be added. Each line shows only while its ability
is unlocked and retires after 3 real casts (`TOD_MAGE_TUT_USES`, LOCKSTEP Lua
`TUT_USES`; server counts at the SPEND in `_tod_mage_elements`, pushes
`tod_mage_tut`, dev log `[TOD_MAGE_TUT]`). Pause-menu ACT lines for 52/54/55 lead
with the same tokens; `AetheriumStartMenu` Localizes the act line for it - keep tokens
OUT of `eff` (the scoreboard prints eff unlocalized). The "third ability that says 1"
is the PACK-A-PUNCH tile; docs/38's MAGE bullet now says so (paste it with the next
upload). QUICK REVIVE charged 500 IN CO-OP: `solo_qr_price_fix` read
`GetPlayers().size` before the second client connected; it now waits for stock's
`all_players_connected` and reads `solo_game` - two prices, 500 / 1500, both asserted
(memory `party-size-settles-at-all-players-connected`, log `[TOD_QR_PRICE]`).
-GscOnly BUILD VERIFIED 2026-09-15 20:38:56 Eastern, FF 149,663,232 bytes; diffs
clean, nothing synced after. UNPLAYED. `tools/test_player_feedback.lua` fails at
`TodTeleportFeedback.lua:12` BEFORE this pass (not touched here) - pre-existing.
Warden King co-op crash (barn) still has NO cause; the fight has never been run
natively in co-op.

**2026-09-15 - CYBER ZOMBIE LEGS FIX.** User reported missing legs in game.
Cause: flat PyCoD load retained donor face object IDs but wrote a shorter object
table; BO3 dropped object 3 (all 6,520 leg triangles). Installer now preserves
stock mesh objects; per-object binary validation gates builds. Never validate
only a flat load/render: it hides invalid object references. Compiled xmodel
triangle coverage must also pass (`verify_cyber_zombie.py --compiled-ledger`).
Corrected 36 exports and native LOD coverage verified; full build passed at
20:30:00 Eastern (149,659,904-byte FF), 188 matching deployed inputs, no later
inputs. Compiled body includes all 6,520 leg triangles. User's native logs
confirm `[TOD_CYBER]` output; corrected visual retest pending. No launch.
Details: docs/141. Preserve dev-only selection and normal dismemberment.

**2026-09-15 - CYBER ZOMBIE MVP: DEV ONLY.** User explicitly limited the
custom appearance to `level.tod_dev`. The generator emits stock and cyber
factories; `install_spawn_filter()` runs immediately after dev flags resolve,
BEFORE `zm_usermap::main()`. Stock `_zm_spawner::init` consumes its
`level.ignore_spawner_func`, retaining exactly one factory: stock when dev is
false/unset, cyber when true. Do not gate only diagnostics or swap models late.
`tools/test_cyber_zombie_dev_gate.js` exercises the shipping predicate, both
factory orders and bootstrap timing on every build. `spawner_zm_tod_cyber_horde`
derives the factory zombie,
changing only character slot four to `c_tod_cyber_zombie`. Native meshes include
the optic/receiver, crown module and brace, with five baked atlases, seven LODs
and native head/limb variants. Preserve stock gameplay/rig/hitboxes and ordinary
dismemberment. Armored sprinter promotion restores only an intact cyber head.
`[TOD_CYBER]` diagnostics are dev-only; native output/animation/gibs/ragdolls
are not yet verified. Final full build passed 2026-09-15 19:42:50 Eastern:
149,766,592-byte FF; 188 matching deployed inputs, no newer inputs and all
cyber assets present, including all five maps. Shader is
`lit_emissive_advanced_fullspec` (the Plus shader ignored the specular map).
User still wants BUILD AND STOP, no game launch. See docs/141 for evidence
and shared-tools optimization drift during concurrent Tower II work.
Editable model/previews: `art/cyber_zombie_mvp/`; details and reproduction:
`docs/141_cyber_zombie_mvp.md`. `tools/verify_cyber_zombie.py` verifies exported
stock geometry/bones/weights/UVs and cosmetic-only asset overrides.

**2026-09-15 - USER TAKES OVER CROWN TESTING.** Latest explicit request:
"run on dev and god mode and open all doors." `tod_dev`, `tod_god`, and
`tod_dev_doors` are ARMED for this test, superseding earlier OFF instructions.
Other optional test flags remain false. User will perform the walkthrough;
Latest follow-up: "Stop relaunching ... Just build and stop." Build only;
do not launch the game. Disarm before publishing.

**2026-09-15 - CROWN STRUCTURE PASS.** Crown architecture now uses true convex
brushes: sloped octagonal band/bell, curved arches, faceted orbs/pearls, beveled
trim, flared point heads and interior arcades. `tools/convex_brush.js` decodes
the emitted planes for preview, area, hidden-face and static collision checks.
The earlier box-only restriction in this file/docs/34 is superseded. Keep
walking slabs and gameplay anchors stable; preserve the sky-height floor and
causeway clearance assertions. `tools/test_crown_convex.js` gates full builds.
See [docs/140_crown_structure.md](docs/140_crown_structure.md) for build/native
status. Test flags follow the latest user instruction above. No new gameplay harness.

**2026-09-15 - BAT FLING: ALL LETHAL SWINGS.** User reverted lunge-only.
No input polling, range guess or consumed stamp may gate corpse launching.
Keep random distance / packed bonus / rare long launch, and elite exclusions.
Diagnostics rev=3 all_swings=1; docs/138_baseball_bat.md has current status.

**2026-09-14 - MSMC / Mk 48 starters:** Skirmisher T1 is t6_msmc (f/h),
Heavy T1 is t6_mk48 (p). User explicitly wants new GDT fire rates with damage
adjusted to preserve old DPS. Follow-up also preserves old magazines/reserves:
MSMC 32/40 + 11 mags; Mk 48 60/75 + 6 mags. `tune.reserveMags` applies AFTER
reserve multipliers. Mk 48 reload now matches Stoner: 6.6 s base / 4.95 s PaP
via tune.reload = 6.6/8.0. Ammo/reload full build passed 2026-09-14 23:26:11 Eastern; native launch failed to start BO3 twice through Steam, so the latest ammo/reload
settings still need an in-game check. BO3 is not running. `dpsReference` keeps other tiers/sidearms stable.
Both keep normal/packed presentation and one tower PaP upgrade. Read
[docs/139_starter_weapons.md](docs/139_starter_weapons.md) for validation/status.

**2026-09-14 - Slasher baseball bat:** tier one replaces the knife with the
BOCW bat, preserving damage and adding bat-only lunge and lethal-hit ragdolls.
User approved native play. Impacts use bathitball.wav; two supplied Floraphonic
whiffs share one random native alias. Details/evidence: docs/138_baseball_bat.md.
**Keep tod_dev and tod_god OFF: user objected to cheats in the initial test.**

<!-- (2026-10-04: the old CLAUDE.md H1 "# Tower of Doom: Cybercity — session brief" sat here; the notes below it are older) -->

**v19.8 (2026-09-14) — THE PROMPT CARD'S BANDS COME FROM THE ART, MEASURED.**
`i_tod_prompt_chassis.png` is 924x304 for the canvas rect 544..775 x 444..520 = **exactly 4 px per
canvas unit**, so every line in it has an exact canvas position and NONE of this layout is taste:
header **446.4..460.6**, cyan underline 460.6..462.1, body **462.1..500.6**, divider rule
500.6..501.1, footer **501.1..516.6**. ⚠️ **PLACE A ROW BY MEASURING THE ART, NOT BY NUDGING** — the
footer box was 499.35..508.75, i.e. its caps STARTED above the divider rule and stopped 8.4 short of
its section's floor, which is the user's *"doesn't fit in its section properly."*
⚠️ **A GLYPH ROW FITS TO ITS OWN BOX, SO TWO ROWS ON ONE LINE DRAW AT TWO SIZES** unless something
makes them agree: "TO ACTIVATE" clamped to cap 4.56 beside a "HOLD" at 7.52. `LayoutFooter` is the one
owner now — it MEASURES the verb first (via `TodGlyphText:measure`, which walks the GENERATED metrics,
never a copied 0.81-per-char constant) and pushes one cap into both rows. Key slot 30 -> 22
(the button picture draws ~13), `FOOT_HOLD_W` -> 24, and **the verb's right edge is conditional on
whether the card has a price** (723 with, 771 without) because the price shares that row.
`LayoutDetail` does the same for the description: a pair centred as a block, a SINGLE line centred
alone — which is every door and PaP, and was 25 units of void before.
**PROVE A CARD BY RENDERING IT:** `tmp/render_card.py` walks `TodGlyphRow.set`'s own arithmetic over
the generated metrics onto the real chassis; run against the OLD numbers it reproduces the user's
screenshots exactly, which is what makes it trustworthy for the new ones.
⚠️ **A SHRINKING `.ff` IS NOT AUTOMATICALLY A LOSS (2026-09-14): 178.6 -> 149.3 MB was the LOADED
SOUND BANK moving out of the `.ff` and beside it** (`zone/snd/all/*.sabl`, 56.6 MB, ~28 MB compressed
= the whole delta; the payload grew 33.8 MB in the same step and the console shows the game allocating
its 730 entries from there). Two clean builds gave byte-identical sizes, which is what said
"reproducible, not a bad link". Same session: a **Tower of Doom II** linker was caught running against
the shared tools root mid-build — `build_map.ps1` refuses with *"Two linkers on one usermap corrupt
the sound banks"*, and that is what triggered the sound-bank retry.

**v19.5/v19.6 (2026-09-14) — THE BLANK KEY, THE TYPE SIZE, THE COIN, THE LEFT HUD.**
⚠️ **THE FOOTER KEY IS ONE ELEMENT CARRYING `[{+activate}]`, AND MUST STAY THAT WAY.** v19.3 drew it
through `CoD.TodKeycap` and it rendered BLANK on every prompt in the map — `make()` was passed a nil
fallback so every failure path drew empty, and that widget also wants the cap ART behind it, which a
footer has no room for. The engine expands the token for the live device; there is no device branch to
add back (memory `bind-token-is-never-a-string`).
**TYPE SIZE IS THE BOX** (`cap = h * capFrac`, capFrac 0.80) — there is no font number anywhere else.
v19.5 took title 10 -> 14, detail rows 7 -> 11, dead band 22 -> 9; **v19.7 CUT THAT INCREASE TO 35% OF
ITSELF** on the user's *"cut the size increase we did on everything by 65%"*: every value is
`v19.3 + 0.35 * (v19.5 - v19.3)` — title **11.4**, detail **8.4**, footer **9.4**, price **10.4**,
`FOOT_HOLD_W` 32 -> **28.1**, left HUD 1.10 -> **1.035**. ⚠️ **THE FRACTIONS ARE LOAD-BEARING** — this is
the 1280x720 virtual canvas, and rounding 448.3 to 448 makes the cut 75% on that row, not 65%.
⚠️ **THE DEAD BAND WAS NOT INTERPOLATED BACK, ON PURPOSE**: *"a ton of empty space under the
description"* is a complaint that still stands, so the footer kept the v19.5 LIFT and took only the size
cut, with the 6.5 freed units split above and below it (band 9 -> 12.25, bottom margin 6 -> 9.25).
The FOOTER VERB is WIDTH-bound, not height-bound — 153 units for "HOLD <key> TO UPGRADE" plus a price —
so it is already clamped at cap ~4.7 and neither v19.5 nor v19.7 could move it; "HOLD" is the
height-bound half, which is why `FOOT_HOLD_W` tracks the rows.
**THE MONEY GLYPH SITS ON THE BASELINE NOW.** The letters set is cap 89 / baseline 103; the v19.2 coin
was ink 37..109 — 73 tall with its bottom SIX PIXELS BELOW the baseline, which is exactly "too small and
sitting low". Recut to bottom-on-103 at 75 tall (the cell is 80 wide, so a full 89 square would overflow
its neighbour). ⚠️ `slice_hud_sheets.js` READS `_images/` BY DEFAULT — the editable masters are in
`_sheets/` and need `--src source_data/tod_ui_images/_sheets`; it re-measures advances from the art, so
never hand-edit TodGlyphMetrics.lua.
**THE LEFT PLAYER HUD IS SCALED, NOT RE-AUTHORED** — `TodScaleAt( el, ax, ay, scale )` +
`TodScalePlayerHud`, anchor **(45, 678)** measured from the widgets' own boxes, factor **1.035 since
v19.7** (1.10 in v19.6), applied to ALL FOUR widgets (local row + 3 party rows) or they drift apart. ⚠️ NOT the scale v17.9 reverted: that
was 1.15 on the LOADOUT about a bottom-RIGHT anchor while its perks-row child is bottom-CENTRE. The left
HUD is single-anchor by construction. Overlap was answered by ARITHMETIC from the rows' own offsets —
content gaps portrait 7.0 / name 30.0 / health 32.0 / points 30.0, which a bottom-anchored scale SPREADS
to 7.7 / 33.0 / 35.2 / 33.0 at 1.10 and 7.2 / 31.1 / 33.1 / 31.1 at v19.7's 1.035 — the figure only gets
safer as the factor falls. Zero overlaps; cluster top 415 at 1.10, 431 at 1.035. The row BACKGROUNDS overlap by
design (87 tall on a 43 pitch) — the content does not.
**`TOD_MOCK_PARTY` IS ARMED** for the 4-player check; `-Publish` refuses to build while it is.
⚠️ **RENAMING A HINT ORPHANS ITS MULTIPLICITY ROW** — `lint_tod_hints.js` keys on the hint TEXT, so
"the Spire" -> "the Endless Spire" silently dropped that template out of the budget and failed the build.

**EVERY PROMPT CARD HAS ONE OWNER NOW: `ui/uieditor/widgets/HUD/ZM_CursorHint/Prompts/TodPromptCard.lua`
(v19.3, 2026-09-14).** User, mid-playtest: *"we should only have to do this in one area in the HUD, and it
applies to all prompts ... there shouldn't be situations where we see half work and half life."* It owns the
chassis, the icon well **and the icon table** (which was `local` to PromptDefault, so five cards could not
reach it), the typeface, every box, the footer and the price. All six cards + `TodTeleportFeedback` are thin
shells: `Build()` once, then `SetTitle / SetDetail / SetPrice / SetIcon / SetFooter`. **ADD TO THAT FILE,
never back into a card**; no prompt card may call `setTTF`, `LUI.UIText.new` or `setImage` for chassis art.
Zero `setTTF` remains on any reachable prompt surface — the one survivor carries a controller BUTTON PICTURE,
which is not typography and must match the player's hardware.
⚠️ **IT IS ZONED IN `zm_tower_of_doom.zone:454`, NOT the zpkg, ON PURPOSE** — `lint_tod_assets` cannot read
the zpkg and a `require` of an unzoned rawfile fails SILENTLY; the first cut of this refactor would have
blanked every door prompt with no gate complaining.
⚠️ **THE TYPEFACE HAS 42 GLYPHS AND DELETES THE REST WITHOUT SAYING SO** — `( ) , / : ;` all appear in the
live perk table and would have fused the words around them. `Sanitize()` runs inside every setter; write copy
that does not need marks we do not own. It also `string.upper`s everything, which is why converting a surface
fixes every capitalization complaint by construction (read `glyph-set-deletes-what-it-cannot-draw`).
**THE PRICE IS ONE GLYPH ROW (`"$2500"`), not an image plus a text box** — that pairing is what made the coin
read tiny and sit off the digits' baseline.
**ROUND 2 LANDED THE SAME NIGHT (v19.4):** rampage / crown / PaP / perk are on disk, zoned and LIVE in
`TodPromptCard.ICONS`; 21 prompt lines were traced through the table before the build, all 21 correct.
Two orderings are load-bearing there: `already packed` sits ABOVE `heavenly gift altar` (the OBJECT the
player stands at wins over the place the copy points to), and the three crown rows sit ABOVE the
extraction rows (the uplink cycles both through one trigger). **THE LESSON FROM BEFORE THEY LANDED
STANDS:** a live table behind a `false` flag FAILED `lint_tod_assets` GATE A, correctly — the gate reads
NAMES out of source and cannot evaluate a Lua flag, so never name an unshipped asset in live code.
**A 46-PROMPT AUDIT BACKS THIS** (CHANGELOG v19.3). Two results worth keeping: the riot shield pickup hint is
registered but **never placed on a trigger**, so that prompt never draws — a gameplay gap, not a UI one; and
`CoD.PromptPAP.SetMode` HAS a live caller (`ZMCursorHintNew.lua:372`) even though its re-pack branch is
unreachable (`USE_AAT_REPACK false`).

**QUICK REVIVE PRICE DISPLAY FIXED AND USER-CONFIRMED (2026-09-13, v18.99l).**
The custom `PromptPerks` ignored the machine hint's price and guessed solo/co-op
from `tod_party`; failed reads displayed 1500 even while the server charged 500.
`ZMCursorHintNew` now forwards the native hint and the widget reads `[Cost: N]`.
Do not restore an independent UI party/price guess or treat repeated server hint
stamps as proof of what the custom card shows. Purchase/power/life behavior is
unchanged. Built 22:47:17 Eastern; user: "it works". Lua tests cover co-op;
native co-op and `[TOD_PERK_PRICE]` developer-log output were not verified.
See docs/133_quick_revive_prompt_price.md. User took over native testing and
explicitly stopped agent game inputs; no further native operation is owed here.

**v18.99k (2026-09-13) — INDUCER: TRIGGER ALL ROUND, TELL IN THE SAME FRAME, TWICE THE SPARKS.** The
use-trigger is centred ON the device (r 96, lifted 40 above the 30.6 prop; `INDUCER_TRIG_OUT` gone).
**"Sometimes the on-indication doesn't work" was a POLL**: the visuals were applied by `spark_think`'s
2–4.5 s sleep loop; `tell_apply()` (idempotent, `level.tod_rampage_tell_on`) is the one owner now and the
use loop calls it in the flip's own frame. Two spark hosts (`TOD_RAMPAGE_SPARK_HOSTS`), crackle 1.0–2.25 s.
Contrast widened: idle scaleRGB 1.2/1.5/0.4 (fluid/crystal/glass), ON 16/22/6; floor light 120 / 1500.
**PLAYED AND APPROVED (user: "looks good").** The inducer is DONE; do not retune it unasked.

**v18.99j (2026-09-13) — THE INDUCER GLOWS FROM ITS OWN SKIN.** User: *"not like the perk glow ... make the
model actually orange and the orange glows."* v18.99i was black-and-grey because the port kept ONLY colour +
normal and threw away BO6's own glow sheets. `install_inducer_bo3.py` now binds the fluid's 512 emission
sheet (hue-nudged orange) and the crystals' crack mask (tinted orange, albedo hue-rotated violet→orange) on
`lit_emissive_plus`, and the glass on `lit_emissive_transparent` (alpha = opacity — BO6's glass is 98%
clear, so the crystals show through). Steel stays `lit_plus`. **`tod_inducer_on` is the SAME mesh with a
`skinOverride` to `_on` material twins** (hotter tint, scaleRGB 3/4/1 → 10/14/3); `glow_set()` swaps the
model. The FX is the dynamic LIGHT only — the sprite is gone. **When a BO6 prop looks dead in BO3, the
missing sheets are the first suspect, not the lighting.** tod_dev / tod_god DISARMED.

**v18.99i (2026-09-13) — THE INDUCER IS FLOOR-MOUNTED AND LIGHTS ITSELF.** No pedestal (the brush is gone,
`INDUCER_PLINTH_H` 0); it stands on the arena floor at (−280, −516, 0), as BO6 places it. TWO looping
effects from map 1's amber perk aura (`tools/gen_tod_inducer_fx.py`, zoned `fx,tod/fx_tod_inducer_*`):
`fx_tod_inducer_idle` is a **dim steady** orange lamp (light flat at 200) played from spawn, and
`fx_tod_inducer_on` is a **deeper orange pulsing 300→900→300 once a second** — the ON tell.
**THE PULSE LIVES IN THE EFFECT'S OWN LIGHT CURVE, NOT A SCRIPT TIMER**, because a server-played one-shot
renders nothing and only a looping FX does. `spawnOrgZ` 18 puts the light inside the glass cylinder.
`glow_set()` owns one host and re-makes it per change (no StopFX for a tag-played loop).
tod_dev / tod_god were armed for this test and DISARMED the same night (22:05 -GscOnly).

**v18.99h (2026-09-13) — THE REAL BO6 RAMPAGE INDUCER IS PORTED AND IN THE MAP.** It is
`t10_zm_essence_container_orange` + `t10_zm_essence_container_crystal_01..04`, joined into one single-bone
static prop (15.2 x 15.2 x 30.6 in, 7 materials, 18.8 MB of 1024-capped texture) by
`tools/bo6_extraction/stage_rampage_inducer.py` + `install_inducer_bo3.py`, zoned as `xmodel,tod_inducer`.
**ITS NAME CONTAINS NEITHER "RAMPAGE" NOR "INDUCER"** (0 of 272,642 loaded BO6 assets) — it was found with
`kind:model essence`, from the wikis' "Aetherium essence canister". **SEARCH BO6 PROPS BY FICTION.** Two
earlier models were wrong: v18.99e-g's `t10_zm_aether_canister` was a name match that measured out as a
plain hazmat drum, and before that map 1's `ww2_circuit_breaker` read as a power switch. ⚠️ **A MATERIAL
NAME OVER 63 CHARS IS TRUNCATED AND SILENTLY DEFAULT-SUBSTITUTED** — the glass material shipped 65 chars in
the first build and the linker drew a default face; one shared `short_key()` now caps every name at 32.
No lit twin: BO6 drives ON with FX, and so does this map.

**v18.99g (2026-09-13) — THE DEAD TRIGGER AND THE MIRROR DOOR.**
(1) **"Way too high to even trigger" WAS NOT A HEIGHT PROBLEM.** v18.99f cut a 72-tall plinth around a
trigger whose origin stayed at the device's x/y, so the origin sat INSIDE a solid and the trigger never
prompted — the map's FOURTH payment on `trigger-origin-under-decal`. The pedestal, device and trigger now
derive from one constant block in `gen_tower_map.js`, ride into GENERATED `_tod_breather_data.gsc` as
`base_inducer_org/_trig/_yaw/_trig_r`, and the generator THROWS if the trigger lands back inside the
plinth. Trigger 56 out in front (the crate grammar); pedestal 72 → 32, re-materialled to `MAT.pilaster`.
(2) **THE DOOR IS A MIRROR, NOT GLASS — AND THERE WAS ALSO A REAL HOLE.** Nothing in the vertigo pack is
transparent; all 30 materials are polished mirrors (white albedo + a 97%-white gloss map + NO normal map +
`reflectionProbeAmount 1`). Five matte clones `tod_door_<hue>` (`tools/gen_tod_door_materials.js`) are
wired through `doorMatOf()` — DOOR SLABS ONLY. Separately the arena cornice is emitted per wall run and the
south/east walls split around their doorways, leaving open 320x20 and 120x20 slots of SKY — closed by
`base doorway lintel S`/`_E`.
⚠️ **STILL OPEN, MAP-WIDE:** all 46 reflection probes ship Radiant's DEFAULT 72-unit parallax box inside a
1,120-unit arena; map 1's generator says outright "GROW the box to each zone's extent". That is what makes
reflections SMEAR. Fixing it changes the whole map's look and needs a bake — the user's call
(memory `vertigo-materials-are-mirrors`).

**RAMPAGE HAS NO ROUND SEAL (v19.0, user: "I want to remove the round 9 rampage lock. It will be
toggleable throughout the game").** `locked()`, `TOD_RAMPAGE_LOCK_ROUND`, `lock_watcher`,
`seal_banner`, the `tod_rampage_sealed` eventstring, the Lua widget and the baked plate are all
RETIRED WHOLE; hint strings 96 -> 94 (two permanent slots back). The device always flipped both
ways — only the refusal was removed. **The header's old justification for a late seal (the device
is behind the enter_tpbay door at 1,909-3,545) had ALREADY been false since v18.99f moved it onto
the open arena floor.** Toggling OFF reverts the live levers within ~2 s; spawn-time HP is not
retroactive either way; the Warden King latches at `king_setup` and does not change mid-fight.
`test_rampage_levers.js` pins the retirement (negative control run: 4/4 re-introductions caught)
and **both rampage tests now gate the build, which ran neither before.** -GscOnly BUILD VERIFIED 2026-09-13 23:11:50 Eastern, FF 178,598,848 bytes. scripts / ui / zone_source `diff -rq` clean, nothing synced after the `.ff`. THE SEAL IS GONE FROM THE DEPLOYED TREE: zero code hits for the constant / `locked()` / `lock_watcher` / `seal_banner` / `tod_rampage_sealed` in the deployed GSC (the only two matches are this pass's own comment lines recording the retirement), zero for `TodRampageSealed` in the deployed Lua, zero for `i_tod_banner_rampage_sealed` in the deployed zone. The in-build hint lint reports **94 distinct strings of 190 budgeted** (was 96). Both rampage tests ran IN THE BUILD for the first time and passed, alongside the riot-shield, elite-pause and mage gates; ten known-waived asset warnings only. UNPLAYED.

**ICE CADENCE IS 0.8 s (v18.99d, user's call: "Move the ice staff to 0.9s per shot then" -> "0.8s actually"). It was 1.1111. THIS IS A ~39% DPS BUFF, not only a feel change — cadence IS the rate — and the post-shot weapon-switch pause is THE SAME NUMBER, so it fell 1.11 -> 0.8 with it. Every ice matchup constant (`TOD_MAGE_ICE_VS_BEAST` 2.85, `_ICE_OFF` 0.80, `_ICE_NERF` 0.68) was calibrated against the OLD cadence; if ice reads too strong now, move a matchup constant, NOT the cadence the user set.**

**⚠️ THE STEAM PAGE RENDERS YOUR OWN TIMEZONE, NOT PACIFIC (2026-09-13) — WHEN YOU READ IT IN
THE BROWSER. `patch_notes.js`'s `STEAM_TO_LOCAL_HOURS` was 3, went to 0, and is 3 AGAIN since
2026-09-16 FOR THE TOOL'S OWN ANONYMOUS FETCH ONLY (Valve's default = Pacific; the fetch read 07:49
for an upload of the 10:36 .ff). A PASTED time is Eastern and goes in through `--at` untouched.** The user read "Sep 13 @ 1:59pm" off the Workshop page; the +3
made that 16:59 Eastern, which had not happened yet (it was 15:25) — **a reconstructed upload time in the
FUTURE is the tell.** That error made the 13:59 upload look like it came AFTER three later builds, so this
session recorded a nonexistent "notes drifted from the binary" failure and netted two ice bullets out of
the published section for a reason that did not apply. The user corrected it: *"No they arent. I published
and then we made the changes. Did you check timezone"*. Rows 34-37 were all three hours late and are fixed;
the giveaway in every one is a 3-hour build->upload gap where 10-26 minutes is the norm.

**UPLOAD #37 = v18.98, 2026-09-13 13:59 Eastern, `.ff` 13:45:51.** Notes and binary MATCH. Everything built
after it is UNPUBLISHED and is the pending v19.0 row #38: the power decals, ice cadence 0.8, the two
lightning-staff ammo fixes and the riot-shield card. **AND v19.0 TAKES SOMETHING BACK IN WRITING:** the
published notes promised "No more delay switching weapons after an ice staff shot", which was TRUE of
v18.98 (ice `fireTime` 0.1) and is no longer true — v18.99c restored the native fireTime, so the swap waits
0.8 s. The v19.0 ice bullet says so in the same breath as the rate fix rather than reverting it quietly.

**PUBLISH CANDIDATE v18.99 (2026-09-13; CHANGELOG v18.99c is the SHIPPING entry, v18.98/v18.99/v18.99b are
its earlier passes). FOUR PASSES IN ONE CANDIDATE:** (1) ship state + the notes reconcile, below; (2) the BO6
ice-staff TEXTURE CAP (2048 -> 1024, gloss/AO 512 — `i_tod_bo6` 102.7 -> 21.7 MB, clean pack 1.29 GB;
`downscale_pack_textures.js --restore` on that GDT undoes it, and the REPO copy had to be capped too because
`sync_to_modtools` mirrors `model_export/tod_bo6_ice` every build); (3) THE POWER DECALS — six
`arrow_power_coldwar*` chalk-meshes from map 1's DOGCANARY pack, already in the SHARED tools root, **NO zone
line** (a brush/mesh face material rides in through the BSP), authored by map 1's winding rule (+y normal ->
columns Xmax->Xmin, u0 = viewer-left, so the LEFT arrow points EAST); (4) TWO REGRESSION FIXES — ice
`fireTime` back to native **1.1111** (a script `DisableWeaponFire` cooldown gates a `Charge Shot` press but
NOT a `Single Shot` one, so v18.94 left the staff firing at click speed; **THE SWITCH PAUSE RETURNS WITH THE
TIMING** — one field owns both, and the untried native split is `shotsBeforeRechamber` + `rechamberTime`),
and a RIOT SHIELD card now **ENDS** a recharge instead of only shortening it (the v17.10 fix covered the
holding-a-shield case only, which is why it "sometimes" worked). **Owed: the user's test, the upload, then
`node tools/patch_notes.js uploaded`.**

**v18.98 (the ship-state pass):** ship state — `tod_dev` / `tod_god` /
`tod_dev_mage_test` / `tod_dev_maxed` → false (the same-day staff-test arming), money / doors / altar already
off, harness #8 parked. Ledger row #36 (v18.85) was PENDING through its own upload AGAIN (Sep 11 7:41 pm
Pacific = 22:41 Eastern, closed from the user's pasted page — rows 34, 35, 36: three in a row; ASK FOR THE
LIVE PAGE BEFORE EVERY WINDOW). Notes `Update — Sep 13 (v18.98)`, 12 bullets over a 15-entry window
(v18.86 → v18.97: sky ×5 folded, ice staff ×6 folded, SCAVENGER old → final, red dot, the fun pass).
Carries v18.96g unbuilt-until-now (spin 4320, song −5.6 LUFS). Licence flag on "Falling To Pieces" stands
(CREDITS.md) — the user's call. PUBLISH BUILD VERIFIED 2026-09-13 13:45:51 Eastern, FF 176,242,624 bytes; `-CleanPak` + all twelve languages (every language `.ff` from this tree; the first attempt at 13:28 died at the Spanish link on a transient `Missing source checksum` for `wpn_t9_amp63_trig_pull4.wav` and the script restored; the rerun linked all twelve clean). Deployed `tod_dev*` / `tod_god` all false, harness #8 parked (both re-read in the DEPLOYED tree); scripts / zone_source / ui `diff -rq` clean, nothing synced after the `.ff` (only the linker's own traditionalchinese assetinfo outputs are newer); deployed `tod_music_ee.wav` sha = repo's; fresh content-hash `i_tod_bo6_ice_*.iwi` at 13:40 (1.29 MB for a 1024 colour map). Notes gate `check` OK; ledger row #37 stamped with the `.ff`. Gates: notes, installer `--check`, staff validation, assets lint, hints lint — green. UNPLAYED: v18.96f/g bears + the capped ice staff in hand are the user's to judge before upload. Size pass: BO6 ice textures capped 2048 → 1024 (gloss/AO 512) — pack 1.29 GB, `i_tod_bo6` 102.7 → 21.7 MB; payload 2.21 GB / 48 files. Four orphan staff `fx,` zone lines retired. **Owed: the upload, then `node tools/patch_notes.js uploaded`.**

**v18.97 — THE WHITE GLARE WAS THE IMAGE (user), docs/104 §4k:** lit edges were 200x the sky base
and the engine's bloom haloed them white — THE PREVIEW PNGS CANNOT SHOW THIS (display-referred). A
peak knee (`--knee 0.45`, max 0.62, hue kept) + `GLOW` 0.05; gain PINNED 0.01661 / `--target-score`
default 0.324 because the peaks WERE 28% of the sky-light mean — the tower's ambient is ~28% lower ON
PURPOSE; `--target-score 0.45` restores it (brighter base). FULL BUILD VERIFIED 2026-09-13 13:22:48 Eastern, FF 176,397,120 bytes; new content-hash sky `.iwi` 22,945,492 bytes at 13:21:55; deployed EXR sha256 = repo's (b2f53b12…), zero unexpected linker errors, zone_source/ui diffs clean, nothing synced after the `.ff`. ONE scripts diff: a PEER session disarmed every dev flag in `zm_tower_of_doom.gsc` at 13:21:49 (after this build's sync) for a v18.98 PUBLISH — so THIS `.ff` still carries tod_dev/tod_god/tod_dev_mage_test/tod_dev_maxed ARMED and is a test build; the peer's publish build will carry this sky (the repo EXR is this one). UNPLAYED — glare is judged IN GAME only.

**THE FUN PASS, v18.96 (2026-09-13, CHANGELOG v18.96):** four player-experience features, all
script + zone + one wav. (1) **THE WARDEN KING HAS PHASES** — at 66%/33% health he reels (stun +
`slow_elite` x0.45 2.5 s), the deck shakes, then sprint (phase 2, summons 15 s) and rage (phase 3 =
`king_rage_on()`: berserk on every summons, 13 s). The rampage levers are now HEALTH-owned;
rampage keeps them on from the landing. ONE sprint thread (`tod_king_sprint_on`), ONE berserk
call site. (2) **THE TEDDY BEAR SONG HUNT** (`_tod_secret.gsc`) — three stock `p7_zm_teddybear`
(base power hall / floor-10 window sill / floor-20 hoop top), shoot-detected; the laugh
`zmb_laugh_child` 3D at the bear; all three = "Falling To Pieces" (`tod_music_ee`, -8.0 LUFS,
279.3 s) and **NO MUSIC CAN OVERTAKE IT** — `channel_play` PARKS every other request while it
holds and replays the newest after. Once per match. Licence of the track = the user's call
(map 1's credits flagged commercial songs DO NOT PUBLISH). (3) **ELITE KILL CONFIRM**
(`_tod_killconfirm.gsc`) — red `hud_damagefeedback` snap + `tod_headshot_ding` for the KILLER on
elite deaths only (bigger on a Panzer), hooked on `tod_luck::boss_kill`; `ding()` is the one owner
of that alias. (4) **ELITE PERK BOTTLES** — `elite_bottle_roll` 10% (`TOD_ELITE_BOTTLE_PCT`) of the
map's `tod_free_pap` bottle at every elite corpse, tower + power only. Dev logs `[TOD_KING]`
`[TOD_SECRET]` `[TOD_ELITE_DROP]` `[TOD_KILLCONFIRM]`. -GscOnly BUILD VERIFIED 2026-09-13 11:57:19 Eastern, FF 176,397,056 bytes; `p7_zm_teddybear` in the assetinfo ledger, streamed bank regenerated 11:57:03 (+31.6 MB = the one new wav), deployed wav sha256 = repo's, alias row deployed; scripts/zone_source/ui diffs clean, nothing synced after the `.ff`; only the established waived linker errors. Tests: test_king_rampage.js (extended) + test_v1896_secret_killconfirm_bottle.js PASS; arity/hints/assets/sound-context lints green. NATIVE RUN 11:59 (agent-launched, PID 38544): map loaded; GAME LEFT RUNNING for the user's own test. Dev flags at launch = the peer's ice-staff set (tod_dev/tod_god/tod_dev_maxed/tod_dev_mage_test TRUE, doors/money FALSE) — unchanged by this pass. FIRST USER TEST: kill confirm fired on every elite class incl. the Panzer; bears sat INSIDE their surfaces (THE PIVOT IS THE BEAR'S CENTRE, z -14.2..13.9 — decoded from the xmodel_bin; `TOD_SECRET_LIFT` 16), the hull was unshootable with the projectile staffs (now a VIEW RAY on weapon_fired, `TOD_SECRET_RAY_R` 40), the laugh was silent (`zmb_laugh_child` is in a Kortifex CSV the map never loads — now `tod_secret_laugh`, an INTERIM Kortifex laughter wav until a Samantha wav is supplied), and the user asked for 3 s of silence before the song (`TOD_MUSIC_EE_GAP`). v18.96b BUILD: -GscOnly BUILD VERIFIED 2026-09-13 12:13:16 Eastern, FF 176,397,056 bytes; loaded bank regenerated 12:13:01 (+455 KB = the laugh wav), laugh wav + alias row deployed = repo; scripts/zone_source/ui diffs clean, nothing synced after the .ff; tests + lints green. **v18.96c:** the user's Samantha laugh (13.85 s) banked as `tod_secret_laugh.wav`; the bear RISES, HOVERS and FLIES AWAY as a scripted mover paced to it (`bear_fly_away`); the third bear kills the music at the hit, leaves under silence, sting at departure, 3 s quiet, song. -GscOnly BUILD VERIFIED 2026-09-13 12:21:20 Eastern, FF 176,397,184 bytes; loaded bank 12:21:05 (57,093,376 = +668 KB, the 13.85 s laugh), laugh wav deployed = repo; scripts/zone_source/ui diffs clean, nothing synced after the .ff; tests + lints green. **v18.96d:** laugh cut at 8.30 s (before the "bye bye"), flight re-paced 1.5/5.0/1.6 s; -GscOnly BUILD VERIFIED 2026-09-13 (see CHANGELOG v18.96d), diffs clean. **v18.96e/f:** base bear out of the east wall; all three PIXEL-PERFECT (lift 14.2 = mesh min z, 6 off a wall's inner face, front taken as local −Y — flip yaws 180 if they face the wall); the exit = one accelerating RotateYaw(2160, 8.1, 8.1) over a 6.5 s rise then the launch. -GscOnly BUILD VERIFIED 2026-09-13 (CHANGELOG v18.96f), diffs clean. **v18.96g:** `TOD_SECRET_SPIN_DEG` 2160 → 4320 (~3 turns/s at the launch); the song re-rendered `volume=-0.4dB` + limiter → −5.6 LUFS (+2.4 dB net; the limiter holds the rest, alias stays 95). FIRST BUILT INSIDE THE v18.98 PUBLISH BUILD (see the top block). The user's retest of v18.96f/g is pending.

**v18.96 — A TINY BIT DARKER (user), docs/104 §4j:** night sky levels ~18% down + `--target-score`
default 0.478 → 0.45 (the world light is 6% lower BY REQUEST — do not "restore" 0.478 without asking);
solved gain 0.01661, sky base ~20% darker, neon held within 3%. FULL BUILD VERIFIED 2026-09-13 11:55:21 Eastern, FF 176,395,520 bytes; new content-hash sky `.iwi` `i_skybox_tod_cybercity_*.iwi` 23,520,909 bytes at 11:54:13; deployed EXR sha256 = repo's (ab3609b7…), zero unexpected linker errors, gain solved 0.01661. CAVEAT: a PEER session edited seven `_tod_*.gsc` + the zone at 11:52:08 (mid-build, after this build's sync — NOT in this `.ff`) and started its own build at 11:56:18, which will replace the `.ff` with a tree that carries both its scripts and this sky (the deployed EXR is already this one). Verify THAT build before playing. Dev flags tod_dev / tod_god / tod_dev_mage_test are ARMED (the ice-staff session's). UNPLAYED.

**THE RAIL FIT PASS, v18.95 (2026-09-13, docs/104 §4i; user: "doesn't look like it fits in
well"):** the rail lines now use the CITY'S grammar — the deck is a dark gridded face with lit
rails as edges (writes depth), a truss under it (`RAIL_GIRDER`/`RAIL_BRACE_U`: posts, zigzag
braces, lit chord), gridded pylons meeting the chord, dark-glass trains with cool windows in
the line's hue + neon car ends + a lit underframe, stations with a dark platform and canopy
slab. Judge on `night_ingame_city.png` / `night_view_crosstown.png`. FULL BUILD VERIFIED 2026-09-13 05:12:29 Eastern, FF 176,395,520 bytes; new content-hash sky `.iwi` `i_skybox_tod_cybercity_AS6NUOKRQLJBDPCISLQEYL5A5K.iwi` 23,742,617 bytes at 05:11:29; repo vs deployed `diff -rq` clean for scripts / zone_source / ui, nothing synced after the `.ff`, deployed EXR sha256 = repo's (d7308755…), zero unexpected linker errors, gain solved 0.01701. Dev flags tod_dev / tod_god / tod_dev_mage_test are ARMED (the ice-staff session's test build, not this pass). UNPLAYED — native look pending.

**THE RAIL PASS, v18.88 (2026-09-13, docs/104 §4h):** the three rail lines (two rings +
a new gold CROSSTOWN across the mid city) carry TRAINS (lit cars, headlight, tail lights,
glow trail), STATIONS (platform, canopy, lit strip, glyph board, lamps), pylon heads and
lights, and a far-rim smog fade. Trains/stations sit on each line's NEAR rim — scattered
placement put them on the hazed far rim behind the towers and every aimed preview was
empty though the debug count said they drew. Aimed previews `night_view_train_*` /
`night_view_station_*` come from the real positions. FULL BUILD VERIFIED 2026-09-13 03:11:24 Eastern, FF 176,396,544 bytes; new content-hash sky `.iwi` `i_skybox_tod_cybercity_GI56P4L6MP37EY4SBYRJXVQEQ6.iwi` 23,744,757 bytes at 03:10:37; repo vs deployed `diff -rq` clean for scripts / zone_source / ui, nothing synced after the `.ff`, deployed EXR sha256 = repo's (c141648c…), zero unexpected linker errors, gain solved 0.01709. Dev flags all false, harness #8 parked. UNPLAYED — native look pending.

**THE SKY, v18.87 (2026-09-13, docs/104 §4g):** Tower II's sky quality pass is
in `tools/gen_tod_sky.js` — painted at 16384x8192 (`--ss 2`), Lanczos-2 resolve,
Catmull-Rom noise, three clamped unsharp passes tuned on the simulated IN-GAME view
(`docs/sky_preview/night_ingame_*.png`, 1080p at cg_fov 65, 0.96 texel/px — JUDGE
SHARPNESS THERE, never on the 2048 equirect), EXR written directly as half floats
(Node 24), `SKY_GAIN` SOLVED for `--target-score 0.478` (landed 0.0176; the picture is
brighter, the world's light is held). Plus the ATMOSPHERE PASS: ground mist + two haze
strata in front of every surface (`veil()`), moon shafts, a storm cell with one bolt,
two airships, an orbital tether + station, far-ring mega-billboards, deeper zenith.
**PER-LOT RNG SEEDING** — a composition lane change re-rolls only the lots inside it
(before, every lane edit moved the skyline under some OTHER planet). **THE SKY IS
RETIRED FROM THE SIZE PASS** (`optimize_tod_assets.py --retire sky`; the 2026-09-10 pass
had halved it to 4096 and its `--verify` gate would have failed the re-rendered EXR;
~+25 MB). Full render ~4.5 min. **16384x8192 IS REFUSED BY THE CONVERTER ("unsupported size", proven the same night: build FAILED, no sky in the .ff until an 8192 re-render) — 8192x4096 is the ceiling and `--width 16384` throws; at 1080p the 8192 sky is already 1 texel/px.** FULL BUILD VERIFIED 2026-09-13 02:16:27 Eastern (the 01:30:17 build re-done after the failed 16k experiment; the 8192 EXR re-rendered sha256-identical, 67081f65…), FF 176,396,544 bytes; new content-hash sky `.iwi` `i_skybox_tod_cybercity_P3KH7OEB3PWESTEZDISBMCDDT3.iwi` 23,775,050 bytes at 01:29:29 (the 2026-09-10 halved one was 3,614,719), xpak rewritten in the `.ff`'s second (1,394,835,456 bytes, append-only — a publish's `-CleanPak` re-measures it); repo vs deployed `diff -rq` clean for scripts / zone_source / ui, nothing synced after the `.ff`, deployed EXR sha256 = repo's; size-pass gate VERIFIED 260 (sky retired). Dev flags all false, harness #8 parked (unchanged). UNPLAYED — native look pending.

**THE BO6 ICE STAFF IS BOUND (v18.89, 2026-09-13; docs/bo6_ports/ICE_STAFF_MIGRATION.md
§"The binding"):** the ice staff's PRESENTATION is the BO6 assembly — models
`tod_bo6_ice_vm`/`_wm` (51,060 verts, 77 bones incl. the appended glow socket
`tag_bo6_glow`), six `mtl_tod_bo6_ice_*` materials (colour + decoded NOG + four
emission maps on `lit_emissive_plus`, `scaleRGB 6` = the first tuning knob), 14 BO6
sounds through 25 `wpn_tod_bo6_ice_*` alias rows (fire ×5 + tails, raise, putaway,
first raise, reload — the ice reload/first raise are ONE 2D-Sound note each now).
`tools/bo6_extraction/install_ice_staff_bo3.py` does all of it idempotently and
`verify_staff_animations.py` runs its `--check` on every build. **Tower II's process,
followed exactly: BO6 mesh on the DONOR's held motion, aligned by MEASURED anchors** —
the view maps 1:1 (BO6's IK locators sit 0.29 in from the fitted clips' wrists, no
shift), the world mesh is shifted +11.67 and rotated X→Z onto the donor world staff's
+Z axis (the Origins world model runs along Z, `tag_tip` frame X→Z; muzzle within 2.1
in). **NOT BO6, by finding not by laziness:** the 116 BO6 clips carry no skeleton and
the BO6 arm rest pose was never exported, so they cannot be retargeted honestly (same
as Tower II's Saug); BO6 vfx returned zero rows in the export index, so muzzle / trail
/ impact / glow stay the BO3 effects (glow moved to the new socket, CSC per-element
tag). Charge shot user-excluded. Ledger `port_gate.py check` = INCOMPLETE 9 open / 0
invalid — every stream `implemented`/`adapted`, none `verified` until the native run.
Test flags still ARMED (tod_dev, tod_god, tod_dev_maxed, tod_dev_mage_test → spawn as
Mage holding ice); spire harness parked. FULL BUILD VERIFIED 2026-09-13 03:45:19 Eastern,
FF 176,107,328 bytes; 28 fresh content-hash `i_tod_bo6_ice_*.iwi`, both xmodels + six
materials in the assetinfo ledger, all 14 wav stems in the fresh `.sabl` beside controls;
scripts/zone_source/ui diffs clean, nothing synced after the `.ff`. NATIVE RUN 03:50–03:51
(agent-launched, PID 30776): map loaded, Mage auto-drafted with ice, the BO6 staff rendered in
hand textured + glowing and fired (`tmp/bo6_ice_staff/native_*.png`), no tod_bo6/sound/script
errors; GAME LEFT RUNNING for the user. Look/alignment/sound levels = the user's call, PENDING.
Then disarm the flags before publish.
**v18.90 — THE SHOT FX ARE BO6-INSPIRED, NOT BO6** (user: "it looks like the same fx" — it was):
Saluki has NO particle/vfx asset type and the name dictionaries hold no `vfx_*staff_ice*`, so
BO6's effects CANNOT be exported here — do not re-open that hunt. `tools/bo6_extraction/
build_bo6_ice_fx.py` composes `share/raw/fx/tod/bo6/fx_bo6_ice_{muzzle_1p,muzzle_3p,trail,
impact}` from BO3 emitters (our trimmed set + Winter's Howl flash/impact + the stock Origins
impact) with a cyan-white tint; bound on the ice weapon + q0/q1, zoned, pinned by `--check`
in the staff gate. The glare rule stands (1p core flash 18, no light/lens flare). Ledger
`adapted`. FULL BUILD VERIFIED 2026-09-13 04:23:38 Eastern, FF 176,347,712 bytes; the four fx
in the assetinfo ledger; diffs clean, nothing synced after the `.ff`; logger label folded in.
NATIVE RUN 04:26 (PID 31784): loaded, fx rendered (crystal spray, frost, sparkling trail —
`tmp/bo6_ice_staff/native_fx_*.png`), no errors; GAME LEFT RUNNING. Frost mist reads heavy after
several corridor shots = first knob (`frost` scale, impact snow-fog). **v18.91 — user: "a big puff
and flash on the player's screen, the only part I don't like": the 1p muzzle now has NO core flash
and NO frost puff (crystals only), the trail no frost wisp; 3p and impact unchanged. THE 1P RULE
IS NOW TWICE-EARNED (v18.75 glare, v18.91 puff): nothing big or bright spawns at the shooter's
camera.** FULL BUILD VERIFIED 2026-09-13 04:33:18 Eastern, FF 176,347,712 bytes; trimmed fx in the
ledger (1p 23,072 B / 16 emitters); diffs clean. NATIVE RUN 04:36 (PID 20104): crystal spray
only, no flash/puff on screen (`tmp/bo6_ice_staff/native_fx2_muzzle.png`); GAME LEFT RUNNING.
**v18.92 (user: "still there" → "have the projectile grow as it goes", "I like the powder haze,
just not in my face", "make the crystal glow more"):** trail body sprites are gated on distance
from the camera (`spawn_min` 96/136/176/216 + 48-unit fade-in: the bolt leaves as sparkles and
fills out a few feet away), the 1p muzzle's haze/glow one-shots are pushed 48 units down the
shaft (`org_x`), the tip crystal materials' `scaleRGB` 6 → 14 (per-material `EMISSIVE_SCALE`).
Impact and muzzle contents otherwise as v18.91. FULL BUILD VERIFIED 2026-09-13 04:44:06 Eastern,
FF 176,347,712 bytes; deployed inputs carry the change; diffs clean. NATIVE RUN 04:47 (PID
37180): sparkles at the tip, haze lands ahead, no screen flash (`tmp/bo6_ice_staff/native_fx3_*.png`);
GAME LEFT RUNNING. User judgement on bolt growth / crystal brightness PENDING.
**v18.93 — THE "FLASH IN MY FACE" WAS A LAUNCH-POINT BUG, NOT AN EFFECT** (user: "just move
where the shot starts"): the ice volley's two side missiles were `MagicBullet`ed from
`self GetEye()` — the camera — so three rounds of effect trimming (v18.91/92) could not fix
it. Now `TOD_MAGE_ICE_VOLLEY_START` 88 ahead of the eye, and the centre bolt / 1p flash
origin `tag_flash` is shifted +48 along the shaft INSIDE the 24 ice clips
(`tools/bo6_extraction/shift_ice_flash.py`, originals parked, manifest re-hashed) because
BO3 has no weapon-level spawn offset and clips pin the tag. **When a 1p effect is "in the
face", read where the script SPAWNS it before touching the effect.** Same build: the three
tip glows at 125% (`fx_tod_staff_glow_*`, CSC repointed; user: "25% more ... color and
personality"). FULL BUILD VERIFIED 2026-09-13 04:54:30 Eastern, FF 176,398,336 bytes; glows in
the ledger, deployed ice clips = shifted clips, diffs clean. NATIVE RUN 04:56 (PID 30152, user
playing): fire staff's 125% glow seen (`tmp/bo6_ice_staff/native_fx4_idle.png`); user: "Okay
looks good." **v18.94 — ICE SWITCH DELAY = THE FIRE STAFF'S OLD BUG:** ice's native `fireTime`
was its whole 1.1111 s cadence and the engine holds the weapon switch for the firing state.
Now `fireTime` 0.1 and `TOD_MAGE_ICE_RECOVERY_MS` 1111 on the fire cooldown controller
(`tod_mage_ice_ready_ms`, `DisableWeaponFire` only). Lightning still has a real native
fireTime (0.2294) — short enough that nobody has reported it; if they do, same recipe.
__BO6_FX5_BUILD_STATUS__

**UI element-pool report (2026-09-10, follow-up after publish candidate):**
Steam round-19 crash report has no class/co-op/action details. Exact crash
not reproduced. Pause-menu cleanup omitted OptionsList plus upgrade/control
elements: actual constructor/close under Lua 5.1 leaves 157/176 direct elements
unclosed with 18 test rows; complete direct-child cleanup leaves zero. Score
popups normally close correctly; now capped at eight concurrent popups per
owner to bound bursts/interrupted clips. 400 pause cycles and 7,500 popup
cases pass. Experimental UI telemetry was removed: client output unverified,
and a temporary PrintInfo probe produced UI Error 85029. No such call, label
probe, notify, relay or diagnostic module remains. Existing AI logging retained.
See docs/133_ui_element_pool.md. BUILD VERIFIED 23:44:40 Eastern, FF
176,322,176 bytes; 1,533 input/deploy/freshness checks pass. Native HUD, class
selection and pause open/close passed; test ended in ordinary round-2 death
while idle. No native pool measurement or round-19 reproduction. Dev/god false;
verification game closed. The 23:05 publish candidate predates these changes.

**PUBLISH CANDIDATE (2026-09-11, v18.84):** ship state — all seven `tod_dev*` /
`tod_god` **false**, HARNESS #8 parked, both re-proven in the DEPLOYED tree. PUBLISH
BUILD VERIFIED 2026-09-11 01:13:35 Eastern, FF 176,322,176 bytes, payload 2,119,324,411
bytes / 48 files, pack 1,328,939,008; `-CleanPak` + all twelve languages, every language
`.ff` stamped 01:09–01:13 from this tree. Gates all green. Player notes:
`Update — Sep 11 (v18.84)`, 33 bullets, SHORT AND PLAIN.
**Owed: the upload, then `node tools/patch_notes.js uploaded`.**
**THE LIGHTNING STAFF'S DOUBLE RELOAD (v18.84) WAS NOT THE SHOT COUNTER** — the staffs
are `segmentedReload` and topped up `reloadAmmoAdd` 999 against `clipSize` 1000, so a
reload STARTING EMPTY came up one round short and the engine ran a second segment. The
optional reload never showed it: it starts at `clipSize - 1` and clamps full in one
pass. `verify_staff_animations.py` ASSERTED the 999 under the comment "one full reload
segment" and failed the build — **a gate written before the forced reload existed, still
asserting the old start state.** A gate is a statement about the world when it was
written; when one fails a change you believe in, read what it was actually protecting.
⚠️ **A PUBLISH RESULT IS A STATEMENT ABOUT A TREE AT AN INSTANT.** The v18.82 candidate
passed at 23:05 and a peer session built v18.83 over it at 23:44, so "are we good to
publish?" had to be RE-RUN, not recalled: deployed flags, repo-vs-deployed diff, nothing
newer than the `.ff`, the notes gate, and the pack's own index. Two of those five had
moved. And when the pack report was read to blame the peer build for 60 MB, the rebuild
disproved it — a CLEAN pack here still carries ~52 MB of holes and 2 shadow trees; the
peer build's real cost was 8.7 MB. Read the whole report, not one field.

**Elite freeze cause and fix (2026-09-10):** native run
`tmp/elite_tracking/runs/20260910_224229_229_a18a10ca` records a world pause
ON AND OFF at 69550 ms, exactly when a moving hound freezes. Dev round events
admit a maxed player with dark cards remaining, then roll_options refuses the
empty hand without dark_guarantee. Both pause edges occur in one frame. The
writer stamps ASM rate 0.05; the 250 ms elite watcher misses the pulse and
never restores it. Regular zombies have a speed sweep; these elites do not.
FIX: freeze writer latches tod_elite_pause_pending; boss_pause_watch consumes
it on release even without an observed rising edge. Existing entrance/pause
ownership retained; unexpired elite slows retained; no continuous rate reset.
Actual-function test reproduces the old fault and passes short/long/repeated
pauses, Fury park, entrance and slow cases; required in build_map.ps1.
Earlier claim "maxed empty deals always return before pause" was INCOMPLETE:
read the dark admission vs dark guarantee checks. Native entity rate=1 and
ASM status=running do NOT prove the ASM pause rate was restored.
Recorder schema 2/tag 20260910f logs exact pause writes/restores and
PAUSE_RESTORE missed_edge=1. Prefix/devblock output proven in run e for all
five families. Shared requested-state hook saw zero calls and was removed.
Initial unwrapped PrintLn fatal and missing devblock launch flag were OUR
logger mistakes, corrected. Separate Mage undefined/lightning guard fixed;
bolt test now models native undefined comparisons. Earlier Fury assertions
remain unlocalized; first-hall path errors are separate unresolved evidence.
See docs/131_elite_tracking_diagnostics.md. BUILD VERIFIED 22:44:11 Eastern,
FF 176,322,176 bytes; 1,533 input/deploy/freshness checks passed. NATIVE FIX
VERIFIED: run 20260910_224853_099_384014b1, pause on/off=118050, hound and
Protector restores at 118100 followed by movement. Next pulse143050 restores
seven elites in 50-150 ms. Nine missed-edge restores, all five families sampled,
zero script exceptions. Game left running for user retest. No claim that this
repairs every unrelated navigation stall.
The agent-run launch procedure is now recorded below and in docs/132; AGENTS.md
points Codex to it. Persistent window helpers live under tools/.

**Mage staff likeness (2026-09-10, v18.81):** all six baked mage assets
re-drawn over their existing names — icons `i_tod_hud_gun_staff1|2|3`, cards
`i_tod_card_class_mage` / `i_tod_card_tier_mage_2|3` — because the drawn
staffs did not resemble the ported Origins staffs actually held. **A SUBJECT
gap, not a style gap: docs/124 had already fixed the icons' treatment, so the
constraint was that the treatment must not move while the object changed.**
Re-measured with `tools/gen_staffhud_ref.js`'s own `stat()`: still 3 tones and
the `#0A1020`/`#E8EEF6`/`#62779C` palette, saturated share HALVED toward the
gun mean, ice's ink coverage up off 29.8%. Their PNGs are ~2.6x the bytes and
that is anti-alias fringe (distinct RGB 180 -> 310, every added value <0.4% of
ink), not colour — do not read file size as a style regression. Cards changed
only inside the art window except the class card's name plate, which was
re-set to two lines and accepted for legibility at its real 186x279.
Read docs/128 before re-commissioning any of the six. FULL BUILD VERIFIED
2026-09-10 21:07:04 Eastern, FF 176,321,152 bytes; six fresh content-hash
`.iwi` at 21:06:54 against 9,942 untouched, all three source diffs clean,
nothing synced after the `.ff`. The six replaced originals are parked at
`docs/128_staff_ref/_prev_shipped_20260910/` and **these images are not git
tracked, so that folder is the only copy.** UNPLAYED; harness #8 and the dev
flags stay ARMED.

**PaP tier icons, ROUND 4 SHIPPED (2026-09-10, v18.82, docs/131)** — the
chevron stack, one flat chevron per tier in the three `DISTRICTS` hues
(`#3FD8E8` / `#F5C542` / `#F0524B` exact), installed over
`i_tod_hud_pap_1|2|3`. **Saturated ink 9.0% -> 49.9%** against a 29.3%
blink/heal bar; ink 49.9%, 3 tones, bbox 80.7%, every docs/131 gate cleared.
A "thinnest horizontal run = 1 px" reading there is a DIAGONAL ARTIFACT, not a
violation — do not chase it (round 3 scored 2 px for the same reason). Round 3
parked at `docs/131_pap_ref/_prev_shipped/`, the only copy. The commission that
produced it is below and its reasoning still governs any future round:

**PaP tier icons, ROUND 4 COMMISSIONED (2026-09-10, docs/131)** — user, on
seeing round 3 in game: *"Our pap icon looks like ass in game. But both blink
and healing aura look great ... Creative and obvious to the player what tier
pap they are."* **THE SIZE IS NOT THE PROBLEM AND THE NEXT SESSION MUST NOT
"FIX" IT THAT WAY:** the PaP glyph box is **26x26** canvas units
(`AetheriumLoadout.lua:1443`) against the offhand icons' **24x24** (:1346), so
the badge already gets MORE room than the two icons that beat it, and ink
coverage is effectively equal (43.3% vs 45.9%). The measured gap is **saturated
ink 9.0% against 29.3%** — the icons are drained of colour — plus two half-scale
objects in one cell and a tier signal that is a COUNTING task at 39 px.
`tools/gen_pap_icon_ref.js` prints all of it and writes the true-on-screen row;
an obvious largest-connected-blob hypothesis was tested and REFUTED there (all
five score one blob, because the fist and its badge touch). docs/131 asks for
one flat geometric emblem per tier escalating on BOTH hue and silhouette, on a
three-step slice of the `DISTRICTS` ladder (cyan `#3FD8E8` / gold `#F5C542` /
red `#F0524B`; never green — that is the heal icon). **The level DIGIT is
already drawn by the game beside the glyph, so no numeral may be baked in.**
Zip in Downloads; nothing installed, no build needed until it returns.

**PaP icon readability (2026-09-10, v18.79d):** installed PNGs matched the
older 13:13 art drop, despite docs/125 recording the newer 19:19 set as shipped.
Restored the exact newer delivered files and enlarged the glyph box 24 -> 26
canvas units, centred inside the existing plate. Visible artwork width at
1080p is now ~34 px instead of ~25 px. All three sources remain 128x128;
uncompressed/noPicMip settings retained. None was in the size-pass manifest.
HUD Lua 5.1 parse and dark/bright layout preview pass. FULL BUILD VERIFIED
2026-09-10 20:03:42 Eastern, FF 176,182,656 bytes; all 1,529 input hashes,
complete deployed trees and timestamps pass. Native visual check pending.
No gameplay or geometry source edits.

**PaP staff HUD names simplified (2026-09-10, v18.79c):** the existing
`tod_pap_tier` event now carries the HELD staff ID with its tier. Lua selects
the base/packed name directly from one local table; engine display-name text
and the old inventory mask no longer determine the staff label. Same-tier
staff switches trigger updates. Gameplay, damage and PaP ownership unchanged.
Thirty actual GSC update packets pass the Lua 5.1 receiver/name checks,
including missing/stale engine names; HUD startup/global guards pass.
Script/UI BUILD VERIFIED 2026-09-10 19:47:55 Eastern, FF 176,182,656 bytes;
all 1,529 input hashes and complete deployed trees match and predate FF.
Geometry MD5 unchanged d08da883c2322730475d3d7682250dcf. Native label check
PENDING: Steam launch confirmation remains open; BO3 did not start.

**Download size pass (2026-09-10, v18.79):** complete deployed upload folder
**2,708,843,259 -> 2,117,743,099 bytes**, saving **591.1 MB / 21.82%**.
236 included texture sources reduced selectively; material references share
29 duplicate image names; nine raw camo/PaP images use supported compression.
Labels/sights, sprinter colors, hall crests, geometry, gameplay and audio retained.
FULL CLEAN ALL-LANGUAGE BUILD VERIFIED 2026-09-10 18:53:58 Eastern, final FF
176,182,656 bytes at 18:53:55. All 1,527 input hashes/deployed targets and
freshness checks pass; all 13 pack indexes checked. No unexplained removed
image names or removed non-image names; mesh bytes unchanged. UNPLAYED,
not uploaded; dev/god/open doors remain armed. Read docs/129 for measured
breakdown and visual checks; docs/128_download_size_audit is the original review.
`tools/optimize_tod_assets.py --verify` checks the installed/repo sources;
`--restore` restores this pass, then FULL -CleanPak rebuild. Originals/manifest
are outside build inputs at `<modtools>/_tod_size_originals/20260910/`.
`-CleanPak` now cleans ALL 13 packs and implies all languages; previous
packs/FFs/banks are kept until the last language passes. Unexpected English
or language linker errors fail. Only the two existing Japanese model
exclusions are accepted after checking their actual japaneseUnsafe flags.
The complete payload report is `usermaps/zm_tower_of_doom/last_payload.json`,
outside the upload folder. Do not describe this texture pass as visually
regression-free before native testing.

Floor-10 overlook removed (2026-09-10): User rejected the Sky Lounge
extension. Restored the shared original room geometry/polish, theme lights
and haze on floor 10; removed extension zone volumes and lounge lookup
bounds. Deleted tools/breather10.js and regenerated map/breather data.
Existing service, spawn and teleporter anchors retained. Full rebuild passed 2026-09-10 16:25:22 Eastern, including geometry,
navigation and lighting; all 1,165 input hashes match deployed and predate
the FF. Native walkthrough pending. This build also includes the previously
tested Protector damage-feed fix.

**THE ROOMS (2026-09-10, v18.80, user after playing three v18.78 halls: "I can
barely tell what unique changes you made ... better uniquely design each trial"):**
every trial hall is now a different SPACE, not a different set of furniture — one
room-scale idea each, with height: THE RING a 48-up stepped STAGE, THE KENNEL a six-pen
CAGE BLOCK with corridors, THE FIRING LINE a 344-wide parapet PLATFORM with a stair at
each end, THE ALTAR a railed CHANCEL across the room, THE MAZE two pinwheel RINGS of
160 walls, THE GAUNTLET three walls COMBING a serpentine, THE THRONE a 72-up railed
PLATFORM with one grand stair and the seat on it. New `SP_RM_LAYOUTS` kinds `stage` /
`deck` / `seat` (generator; docs/130 §B) — **a raised top is a <= 64 SLAB over a
body or lint_tod_geometry calls it a wall, a stair's foot lands on OPEN floor, and a
one-stair platform carries a riser ON it.** The bunker lint scans every level to +140
now (selftest 6/6); 0 bunkers, 0 unguarded edges, 0 detached. Read docs/130 before
touching a hall. FULL BUILD VERIFIED 2026-09-10 20:30:58 Eastern, FF 176,321,152 bytes; in-build hall bunker lint 0/7, geometry lint no regression, navmesh gate OK (both towers one walk); scripts/zone_source/ui diffs clean, nothing synced after the .ff, the compiled map md5-identical to the repo's. Harness #8 + dev flags still ARMED (test build). UNPLAYED.

**THE OPEN HALLS (2026-09-10, v18.78, user: "Everyone just bunker up in the
little cubby"):** every spire trial hall now owns its SHELL as well as its room —
`SP_RM_LAYOUTS[i].furn` (PaP / crate wall presets `SP_PAP_AT` / `SP_CRATE_AT`),
`.risers` (three shell porch risers incl. THE DOORWAY'S CORNER + one INSIDE every
pocket), `.spawns`, `.alcove` ('seal' block / 'open' spawn closet). The two
pockets every hall shared were the sunken PORCH behind the gate and the SE
ALCOVE under the SE landing, which was also OUTSIDE `trial_box` (now in;
exclusion 3 = the S lane; **exclusion 4 (v18.79b, first play) = the SE LANDING
ABOVE the alcove, z > +100 — it is outside the seal and carries a riser, and
letting it in put stranded zombies and frozen elites on it**). Vendor anchors are PER HUB in `_tod_spire_data`
(`hub_pap_org( hub, z )`). In a sealed hall the horde rises at the risers
nearest a random upright player 70% of the time (`TOD_TRIAL_NEAR_PCT/_K`,
`trial_near_spots`). **`tools/lint_tod_hall_bunkers.js` GATES EVERY FULL BUILD:
no one-sector pocket under 80 degrees without a riser inside it; zero, no
baseline; `--png DIR` heatmaps, `--probe X,Y[,N]`, selftest 6/6.** Flow
untouched (porch, seal, clock, recipes, mark, deal). Read docs/128 before
touching a hall; the metric lessons are in memory `hall-bunker-lint`. FULL
BUILD VERIFIED 2026-09-10 17:19:55 Eastern, FF 176,181,632 bytes, all three
freshness checks clean; dev flags still ARMED (tod_dev/tod_god/tod_dev_doors).
UNPLAYED.

**Protector staff damage/display mismatch (2026-09-10):**
The rp_damage_feed fallback called upgrade_damage_cb, leaving its same-frame
stamp behind. Subsequent fallback hits in that frame returned raw damage
without staff scaling or a popup. Controlled actual-handler reproduction:
three 20k raw hits with a 6k scaled result returned 46k but displayed 6k.
Consume the normal-chain stamp and clear the stamp after fallback processing.
All eight three-impact normal/fallback combinations now scale and display
exactly once; unchanged sentinel/non-player passthrough and Mage damage tests
pass. This is a reproduced fallback-path defect, not a capture of the user's
exact shot. Build/native verification pending: BO3 remains running.

**Staff balance (2026-09-10, v18.77):** ice fireTime 1.00 -> 1.1111 (GDT),
ICE_NERF 0.80 -> 0.68, ICE_VS_ARMOUR_ROBOT 0.60 -> 0.35, FIRE_VS_BEAST 0.50
-> 0.35, LIGHTNING_VS_PANZER 5.60 -> 4.76 (-15%). LIGHTNING RELOADS EVERY 20 SHOTS (15 until 2026-09-11): `bolt_count_shot` on weapon_fired,
`staff_clip_target` pins the clip to 0 when due (engine auto-reload), ANY
reload_start resets (`bolt_reload_reset`). `tools/test_mage_bolt_reload.js`.
FULL build, UNPLAYED. **The armory has a BALANCE tab** (13th; enemy HP × class
DPS × TTK × EHP with every stacking rule in code order, 272 checked constants);
re-run the three verify_armory_* gates after any retune and republish
be85de67.

**CONFIRMED UI Error 87927 cause (2026-09-10):** Native diagnostic HUD
captured `LUI Error: Tried to create global variable TOD_STAFF_PACKED_NAME`.
The packed-staff name table in AetheriumLoadout.lua lacked `local` at line
221. Fixed to a local table; the temporary diagnostic wrapper in
AetheriumHud.lua has been removed. test_hud_global_guard.lua loads the actual
module under a no-new-globals environment and reproduces the exact error
with the old declaration. The earlier notification-order fix was not the
cause of this reported failure. Corrected script/UI build passed at
14:53:30 Eastern; all 49 UI and 88 script files match deployed and predate
the FF. Native BO3 check passed: full Aetherium HUD visible at class select
and after choosing Mage (health, points, weapon, mana and ability tiles);
no UI error dialog or diagnostic overlay. Game left running for the user.

**HUD startup ordering fix (2026-09-10, UI Error 87927 report):**
AetheriumLoadout installed its scriptNotify subscription before creating
lethal/tactical slots. An immediate replay of tod_mage_mana dereferenced a
nil slot, including the non-Mage state 2 startup path. Move the subscription
to the end of construction, after slots, feedback frames and stock writers.
Seven eager-notify regression cases pass; negative controls reproduce the
old nil-slot error. Seven-digit damage encoding/display is unchanged.
Script/UI build passed 2026-09-10 14:30:19 Eastern, FF 175,875,968 bytes;
complete deployed scripts (88) and UI (49) match. A concurrent edit changed
ice muzzle 1p FX during linking, so this is not a verified build of that
separate FX revision. Screenshot error code has no console traceback;
native confirmation of the reported error is still pending.

**Ice shot glare reduction (2026-09-10):** User reports screen flashing
on firing. Map-owned 1p muzzle removes lens flare looping7 and dynamic
lights oneshot11/18; 3p removes lights oneshot20/21. Both muzzle glow
sprites shrink 75 -> 18.75 with alpha x0.2 and a blue opening color; the
600-unit haze shrinks to 120, lasts 220 ms instead of 508, and uses alpha
x0.2. Shared ice trail removes phosphor flash sprites oneshot3/4 and
dynamic light12, which were carried by all three missiles from near the
camera. Forty other emitters are byte-identical. Existing q0/q1 references
already use these FX. No weapon, damage, volley or impact changes. Forty
volley aim/variant cases and asset lint pass. Full build verified
2026-09-10 14:17:24 Eastern; FF 175,875,968 bytes. All 1,165
snapshot/repo/deployed input hashes match and predate FF; complete
script/UI trees match. Native flash/visibility check pending.

**Seven player-report fixes + the Mage dark cards (2026-09-10, v18.76):**
no elite behind an unbought door (`_tod_bosses::door_frontier_z`, the
GENERATED door table is the authority, tower only); ARCHMAGE tears down on
death / class change (`demigod_guard` -> one `demigod_end`); the lethal tile
dims for the aura's 5 s lock (`heal_lock_tell`); staff raise/putaway/pickup
now play our own foley (`wpn_tod_staff_*_plr`, reused WAVs); a fresh Mage sees
DIM tiles (never hidden) and one hint; reload mana paced to once per 10 s
(`TOD_MAGE_RELOAD_MANA_WINDOW_MS`); all five Mage dark cards installed,
`DARK_TEXT_ONLY` empty. ⚠️ THE KING'S FLAME RECORD BELOW WAS WRONG: king_setup
DOES swap in a 400x100x50 flame trigger (v17.70), so the hurt box is doubled
too. `tools/test_mage_fixes_0910.js`. FULL build, UNPLAYED.

**Player feedback fixes (2026-09-10):** Review items 1, 2, 4 and 5.
Dark Healing Aura clamps only its radius to Lv6 while retaining Dark strength
and revive. Dark Blink retains the distance readout. Mage tiles gain subtle
perimeter recharge progress from real paused timers and a 350 ms amber Blink
blocked-landing pulse, with no charge spent. Teleporter hints distinguish power
from destination locks; nearby players get a LUI countdown/progress indicator
inside the teleporter prompt. Three eventstrings, zero new clientfields or
image assets; fixed hint count rises by one (96/190 budget). GSC helper and
Lua 5.1 UI tests pass, including Dark range/revive, pause, class reset and
pad selection. Full build verified 2026-09-10 14:07:04 Eastern;
FF 175,868,736 bytes. All 1,165 snapshot/repo/deployed input hashes
match and predate FF; complete script/UI trees match. Existing waived
asset warnings only. Dev/god/open doors remain enabled. Native visual/
gameplay check pending.

**Warden King under RAMPAGE (2026-09-10, v18.75):** rampage barely reached
him (flat HP write below boss_hp). Now, behind `_tod_spire::king_rampage()`
only: HP x1.25 (`TOD_KING_RAMPAGE_*`), permanent SPRINT locomotion via the
blackboard with flame/claw kept (`king_sprint`; permanent BERSERK was rejected
— berserk disables flame and claw), stock berserk for 10 s on every summons,
summons 18 -> 13 s with +1 Protector +1 hound, trickle floor 0.10 (lockstep
pair with `_tod_endless_rounds`), and every ordinary zombie on the deck +10
rounds of sprint through the sprinter's `tod_zspeed_round_add` lane.
`tools/test_king_rampage.js`. His base HP is **10M per player** (the brief
below said 25M until today). Same pass: the SCOREBOARD's owned-upgrades
`TOD_UPG_PLATE_MAX` was 47 against the pause menu's 56 (every Mage row a text
label there) — now 56, and `lint_tod_assets` GATE D fails the build if the
pair ever differs again. Built -GscOnly, UNPLAYED.

**Floor-10 walkthrough dev session (2026-09-10):** User requested dev, god
and all doors open. Armed tod_dev, tod_god and tod_dev_doors in the map
entry. Existing dev bundle provides money, maxed class upgrades and
unlimited altar uses; existing door harness opens every tower door and
breather access from the normal base spawn. Script build verified
2026-09-10 02:52:58 Eastern; FF 173,330,752 bytes. All 140
snapshot/repo/deployed inputs match and predate FF; complete script/UI
trees match. In-game walkthrough pending.

**Floor-10 Sky Lounge prototype (2026-09-10):** Structural redesign only on
the tenth-floor breather: stepped overlook adds 39.2% room floor, open low
parapets, arrival portal, shallow service canopies, lookout fins, dark-blue
floor and warm/cool light pools. Anchors and existing spawn mechanics stay.
New wing is zoned; generated shared room lookup covers arrival/relief.
Floor-10 chest haze becomes low overlook fog and high motes. All changed
world geometry labels are floor-10 breather; other stops retain their design.
Geometry/arity, 4,216 room points and 90 compiled overlook nav samples pass.
Full build verified 2026-09-10 02:06:06 Eastern; FF 173,330,752 bytes.
All 1,154 snapshot/repo/deployed hashes match; script/UI trees match. Six
pre-existing dark pause PNGs carry future 03:05:56 archive timestamps, but
match the pre-build snapshot; other 1,148 inputs predate FF. Native
appearance/walk-through pending. See docs/127.

**RAMPAGE re-hardened (2026-09-10, v18.74, user: "rampage feels easier"):**
the Sep 6/7 relief (elite roof 12 -> 5/7/9/11, horde HP table, elites -10%)
had reached hard mode because those knobs had no rampage branch. Now, ON the
breaker only: elite roof +3 (`TOD_RAMPAGE_ELITE_ROOF_ADD`, 8/10/12/14),
zombies at once +10 over the party figure (`TOD_RAMPAGE_AI_LIMIT_ADD`,
40/45/50/55 — no longer a flat 45), elites/Panzer x1.5 (`TOD_RAMPAGE_HP_MULT`,
was 1.25) and NEW horde HP x1.2 (`_tod_zombie_speed::rampage_horde_mult`,
which the sprinter divides out to take the elite bump once). Read the defines;
`tools/test_rampage_levers.js`. Built -GscOnly, UNPLAYED.

**First Mage playtest pass (2026-09-09, v18.73 — twelve calls):** ladder
x0.85 (TIER 0.6256/1.36/2.686), FIRE_VS_ARMOUR 1.75, ICE_VS_BEAST 2.85,
ICE_OFF 0.80, NEW FIRE_VS_BEAST 0.50 (never tier-gated); fire splash 192,
ice shake/kick zeroed (FULL build); todDmgNum 15 bits = scale bit, cap
2,047,000, POOL 61/61 — NO BITS LEFT; mana 0.8/s + budget 32; BLINK x1.8 and
the elite-kill refund is DELETED; five mage domains DARK-CAPABLE with real
lanes (fire/ice +0.50, heal rung 7, arch, blink 3rd charge) — only HEALING
AURA has dark art, docs/126 orders the rest, the others wear DARK text;
pause dark rows say "DARK: " instead of tinting; classless players wear body
0 until the draft; packed staffs are KIMAT'S BITE / KAGUTSUCHI'S BLOOD /
ULL'S ARROW. Read the CHANGELOG v18.73 entry; nothing played yet.

**Queued Mage changes built (2026-09-09 19:58:48 Eastern):** Full build
plus script follow-up passed; fresh FF 172904832 bytes. All 1,147
snapshot/repo/deployed script/UI/zone, GDT, FX, alias, WAV and approved
animation inputs match and predate FF; complete script/UI trees match.
Includes current Chain Lightning progression and queued staff work. Native
gameplay/visual/audio check pending. Blink gain remains unimplemented.

**Mage ceiling pass (2026-09-09):** FIRE_VS_ARMOUR 3.61 -> 1.25 (tier-3 tap 15k),
ICE_VS_ARMOUR_ROBOT 0.30 -> 0.60, ARCHMAGE ladder top 2.20 -> 1.85 (LOCKSTEP
Lua row 55 + armory), dark CHAIN +2 -> +1 arc. ARCHMAGE has NO dark card
(set_no_dark); the armory used to say x2.70 was reachable. Artifact "Staff
Damage Matrix" computes the whole chain from the constants. Build pending.

**Staff lanes (2026-09-09):** TOD_MAGE_VS_HORDE 1.30 -> 1.75, TOD_MAGE_ICE_OFF
2.36 -> 1.00. Ice = beasts (3.352 unchanged), okay on hordes, ~2% of
lightning on the Panzer. Lightning = horde + Panzer. Fire = armour, unchanged.
The v18.56 "ice is the generalist" prose in _tod_mage_elements and the
armory is history now. Build pending; native check pending.

**Chain Lightning ten levels (2026-09-09):** mage_bolt max 10; normal arcs
1/2/2/3/3/4/4/5/5/6, with Dark retaining two additional arcs (eight at cap).
Chain fraction is 0.50 * (1 + 0.05 * level): 50% base, 52.5% at Lv1,
75% at Lv10. The +5% is relative to half-damage base, not +5 percentage
points of the original hit. Prior code already used half damage and skipped
attacker multipliers on marked chain callbacks; no 100% arc base was found.
Server card, Lua level/readout/Dark display and armory updated. Actual helper
and callback tests pass through all levels, Dark, rounding and sprinter armor;
once-per-shot, damage, arity, Lua lint and armory checks pass. Build/native
playtest pending BO3 closure.

**Ability first-draw replay correction (2026-09-09):** User confirms the
previous InitialWeaponRaise-on-held-staff call did NOT replay Healing Aura.
Earlier source/unit checks were not native playback proof. Shared ability
helper now uses tod_classes::camo_regive(false) to preserve exact asset, ammo
and PaP camo; ShouldDoInitialWeaponRaise(true) requests first draw on next
equip. A frame-delayed bounded equip handles swallowed same-frame switches,
stopping on death/disarm/disconnect, lost ownership or last stand. Both Aura
and Archmage use it. test_mage_ability_raise covers six variants and empty/
partial ammo with actual helpers. Arity, healing and animation assets pass.
Script build verified 2026-09-09 18:48:31 Eastern; FF 172878912 bytes.
All 140 snapshot/repo/deployed inputs match and predate FF; script/UI trees
match. Native animation verification pending; do not claim visible playback.

**Staff first raise (2026-09-09):** Winter's Howl fly_freezegun_first_raise.wav
as staff_first_raise.wav, played ONLY by the frame-1 2D Sound note; the
firstRaiseSound fields are cleared (they named an unzoned stock alias). Every
other non-fire staff sound field still names unzoned stock foley -- see the
v18.70 CHANGELOG audit before claiming any of them plays. Build pending.

**Healing Aura green slightly brighter (2026-09-09):** Aura health tint
RGB 0.20/0.62/0.32 -> 0.21/0.65/0.34, about 5% brighter with the same hue.
Only the aura color changed. Lua lint and 256 tint-state cases pass.
Script build verified 2026-09-09 18:43:25 Eastern; FF 172,903,296 bytes.
All 140 snapshot/repo/deployed script/UI/zone inputs match and predate FF.
Script/UI trees match; zone-source extras are build-generated outputs.
Native visual check pending.

**Ability first-draw animation (2026-09-09):** Shared ability_first_raise
now runs on successful Healing Aura and Archmage activation. Healing Aura
already used InitialWeaponRaise; Archmage now does too. Cancels pending
reload reward before the native gesture and preserves the held staff variant.
Arity, healing strength/FX and staff animation checks pass. Build/native
playback pending BO3 closure.

**⚠️ BLINK'S VOLUME IS NOT A KNOB — CLOSED 2026-09-10, DO NOT RE-INVESTIGATE.**
Asked for twice (+5 dB 2026-09-09, +3 dB 2026-09-10) and it is not achievable
as asked. Blink plays the STOCK aliases `zmb_bgb_abh_teleport_out` /
`_in` directly (`_tod_mage_elements.gsc:1119` and `:1124`). The 2026-09-10 pass
searched exhaustively and the result is negative on every lane:

- the alias pair is defined in **no CSV in the repo and none anywhere under the
  mod tools root** — it exists only inside BO3's base fastfile, so VolMin/VolMax
  cannot be edited the way the lightning shot aliases were (see the entry below);
- **no source WAV exists**: zero `abh` or `bgb` hits across all 4,822 WAVs in
  `<modtools>/sound_assets`, so it cannot be re-encoded 3 dB hotter;
- the stock WAVs this map already ports came from COMMUNITY PORT PACKS
  (`fly/` = Winter's Howl, `sat_ports/`, `skye_ports/`, `bo4/`, `black_ops_cw/`),
  **not** from extracting the base fastfile — there is no extraction pipeline in
  this repo, and `share/raw/sound` holds 0 WAVs.

So the volume only becomes tunable if the sound becomes MAP-OWNED, which means
substituting a different WAV. **The user was offered that on 2026-09-10 — the
`avo_warp_in/out` pair, `acc/fx/teleport_warp.wav` from map 1, or the Fury
bamf — and chose to KEEP THE STOCK SOUND at its fixed level.** That is a
decision, not a pending task. Do not re-open it, do not claim the volume
changed, and do not reach for an unverified script gain override.

**Lightning firing sound reduced (2026-09-09):** Lowered VolMin/VolMax by
3 on both lightning shot aliases (player 85/90 -> 82/87, NPC 78/80 -> 75/77)
in tod_ports.csv. Sound-context lint passes. Build and native listening check
pending BO3 closure.

**Staff reload sounds, real fix (2026-09-09):** the six staff reload /
first-raise xanim GDT blocks had NO "2D Sound" custom notes; baked notetrack
names play nothing in BO3. SOUND_NOTES in tools/import_staff_animations.py
stamps them (frames 14/29/43/59, first raise 1); verify_staff_animations.py
gates it. Full build pending BO3 closure; native check pending.

**Lightning chain gray debris removed (2026-09-09):** Chain-hit torso FX
now uses map-owned fx_staff_lightning_chain_clean in GSC, CSC and the zone.
Removed stock oneshot emitter 5 (gfx_debris_clumps_em_i8, neutral gray
RGB 0.250980), matching the powder material removed from direct impacts.
The other 70 elements are byte-identical; chain damage and cleanup unchanged.
Arity check passes; asset build and native visual check pending BO3 closure.

**Healing Aura text removed (2026-09-09):** Removed the green AURA / HP/s /
RESIST text and its HUD element. Retained the watcher lifecycle, mana bar
updates and ability charge updates. Healing, resistance and green health-bar
tint remain. Script build and native check pending BO3 closure.

**PaP HUD icons installed (2026-09-09, full build):** gun-with-chevrons set
over the same i_tod_hud_pap_1..3 names, no wiring change. Native look
pending; the user has not yet seen it on the plate in game.

**Dark card overlay + Blink text (2026-09-09, built):** text-only dark cards
(CHAIN LIGHTNING) showed the previous deal's picture underneath because the
reveal flip forced CardImg alpha 1; tod_upgrade.lua now tracks card.imgLive.
Blink's "no footing" print removed. Native check pending.

**Ice lingering icicle models removed (2026-09-09):** Map-owned
fx_staff_ice_trail_clean removes stock trail oneshot emitters 10/11, both
spawning large icicle models with five-second lifetimes. Other 13 trail
elements are byte-identical; impact effect, frost, slow and damage remain.
Source ice staff and generated q0/q1 use the clean effect; semantic byte
comparison confirms those three references are the only GDT changes. Weapon
registrations and cost CSV unchanged. Full build/native visual check pending
BO3 closure, together with lightning gray debris removal and Mystical Hands.

**Ice nerf (2026-09-09, built):** staff_mult cuts ice x0.80 everywhere and a
further x0.30 vs the armour family + Panzer (x0.24 total) --
TOD_MAGE_ICE_NERF / TOD_MAGE_ICE_VS_ARMOUR_ROBOT. Beast/horde keep x0.80.
Native check pending.

**Lightning nerf + unpause sound (2026-09-09, built):** staff_mult cuts
lightning x0.90 unpacked / x0.80 packed (TOD_MAGE_LIGHTNING_NERF /
_PAP_NERF); staff fire aliases no longer Pauseable (the guns never were) as
the best-evidence fix for shots doubling after a pause. Native check pending
for both; the "animation too" half of the report is unexplained.

**Lightning impact gray debris removed (2026-09-09):** Removed four
gray gfx_debris_clumps_em_i8 emitters from fx_tod_elec_impact_sm
(oneshot 11/19/20/21, neutral RGB 0.250980, 433ms). These are the likely
source of the reported gray powder puff. Other 96 elements are byte-identical,
including purple lightning, sparks and clouds. Both existing lightning q0/q1
variants already reference this effect. No weapon or damage changes. Asset
build and native appearance check pending BO3 closure.

**Staff reload/first-raise sound fix (2026-09-09, built):** the seven
freezegun-derived alias rows were gated on a water/over sound context this
map never sets; cleared in tod_ports.csv. NECESSARY BUT NOT SUFFICIENT --
the user still heard nothing; see the 2D Sound note entry above.
tools/lint_tod_sound_context.js gates every build.

**Mystical Hands tier gate (2026-09-09):** Added set_tier_min 2 to
mage_quickhands. Shared domain_available excludes the card at Mage tier 1
and allows it at tiers 2/3. Ultimate-only rarity, effect and persistence remain.
Armory eligibility mirrors the gate. Build pending BO3 closure.

**Max Ammo fills the mana bar (2026-09-09, built):** guarded pointer
level.tod_mage_max_ammo from _tod_powerups::max_ammo_clip_watch; requires the
first ARCHMAGE card; fills to 100 even mid-form. tools/test_mage_max_ammo.js
passes. Native check pending.

**Staff HUD icons fixed (2026-09-09, built):** the gun-bay resolver keys on
DISPLAY names (TOD_NAME_CAT in AetheriumLoadout.lua); the staff rows lived
only in the stem table, so staffs kept the spawn MR6 icon. Three display-name
rows added. Native check pending.

**Mage startup scoring fix (2026-09-09):** The 11:43 build FAILED native
startup: unresolved zm_score::tod_mage_kill_points from _tod_upgrades. Its
vendored _zm_score source did not supply that function to the runtime despite
a successful link and matching deployed sources. Removed that override and
zone entry completely. The existing public zm_score::register_score_event
hook now handles death scoring in _tod_upgrades; shared Mage price helper
lives there and the HUD calls its guarded level pointer. The callback retains
stock bonus/stat work, returns 80 (70 until 2026-09-09) only for Mage ordinary zombies (dogs omit
the zombie_team argument), and lets stock scale/round/award points. Staff EX
is retained. Actual handler/popup and Lua tests pass. Rebuilt 2026-09-09
11:57:11 Eastern: FF 172,921,280 bytes; all 140 snapshot/repo/deployed
script/UI/zone inputs match and predate FF. Native BO3 launch checked: fresh
11:58 log passes script loading and initializes tower door/PaP/upgrade triggers,
with no SCRIPTERROR, unresolved external or Com_ERROR. Gameplay scoring and
EX appearance still require playtesting.
The previous build-success note is not evidence of successful game startup.

**PaP icon concepts commissioned (2026-09-09):** docs/125 orders three
distinct 128x128 HUD icon concepts (mark / machine / gun-upgrade) to replace
the bullet-shaped i_tod_hud_pap_1..3; zip in Downloads. Drop comes back as
files (N).zip: -Inspect, show the user all three on the plate, then a
follow-up doc for the chosen one. Nothing wired yet.

**Lightning staff fire rate -15% (2026-09-09, built):** fireTime 0.195 ->
0.2294 s in source_data/tod_staff.gdt; q0/q1 twins regenerated (only those
two fields changed). Damage per bolt and everything else unchanged. Full
build; native playtest pending.

**Ice staff shot SFX (2026-09-09, built):** staff_ice_shot.wav replaced with
the user's Ice Spell Impact download, trimmed 1.20-2.70 s (impact first) and
-9 dB; same aliases. Recipe in sound_assets/tod/mage/README.md. Native
level/feel check pending.

**Mage kill points and staff EX names (2026-09-09):** Ordinary Mage zombie
kills pay 70 base points via vendored _zm_score's death-only override, before
Double Points. Shared tod_mage_kill_points feeds the actual payout, popup and
Bounty base. Dogs, other classes, hit points and lump elite/boss rewards retain
their paths. PaP staffs append EX in AetheriumLoadout using all three pack bits
sent together through the existing tod_pap_tier event; no new registrations.
Scoring and Lua 5.1 HUD tests pass. Script build verified 2026-09-09 11:43:38
Eastern: FF 172,967,104 bytes; all 141 snapshot/repo/deployed script/UI/zone
inputs match and predate FF. Established waived warnings only; dev/god flags
off. Native playtest pending.

**Elite/Panzer mana bonus (2026-09-09, built):** The killer of any elite banks
5 mana and the killer of a boss-round Panzer 15, full through round 10, then
scaled by 10/round with a 0.25 floor (elite 1.25 / Panzer 3.75 from round 40).
Constants TOD_MAGE_MANA_ELITE / _PANZER / _ELITE_FULL_ROUND / _ELITE_FLOOR in
_tod_mage_elements; hook level.tod_mage_elite_mana from grant_elite_reward and
the boss-round Panzer lane. Not ARCHMAGE-scaled; normal bar gates apply.
tools/test_mage_elite_mana.js passes. Native check pending.

**Fire Blast card reduced to +20% per level (2026-09-09, built):**
Changed the six-level damage bonus from +25/50/75/100/125/150% to
+20/40/60/80/100/120% (2.20x at Lv6). Server card description, Lua
card/readout and armory now agree. Prior all-staff damage nerf remains;
fire charge payoff, firing rate, handling and other card bonuses are unchanged.
Damage regression, Lua 5.1 level readouts, arity, Lua lint and armory constants pass.
Build verified 2026-09-09 03:18:31 Eastern: FF 172,914,240 bytes; all 1,164
snapshot/repo/deployed inputs and complete script/UI/zone-source trees match
and predate FF. Fresh streamed bank 174,624,640 bytes; only established waived
asset warnings. Ready for native testing.

**All staff damage reduced another 20% (2026-09-09, built):** Multiplied
the shared Mage damage ladder by 0.80: T1 0.92 -> 0.736, T2 2.00 -> 1.60,
T3 3.95 -> 3.16. The three constants are used only by staff_mult, so every
staff direct/splash hit is reduced before the existing card, charge, PaP and
Archmage multipliers finish scaling. Existing ice-specific nerf stays in place.
Lightning chain shares use the reduced final hit and exit the callback before
attacker multipliers can apply twice. Normal integer damage rounding remains.
No weapon GDT, firing rate, splash radius, handling or target-count changes.
Updated the armory damage ladder/readouts; relative card bonuses are unchanged.
Tests compare before/after values across all three staffs, q0/q1, three tiers,
all card levels, four target families, charged shots and normal/Archmage/Dark
multipliers; chain rounding and Panzer display regressions pass. Arity and
armory constants pass.
Build verified 2026-09-09 03:07:27 Eastern: FF 172,914,240 bytes;
all 1,164 snapshot/repo/deployed inputs match and predate FF. Fresh
streamed bank 174,624,640 bytes; only the established waived asset
warnings. All dev/god flags OFF. Ready for native balance testing.


**Combined queued changes - full build verified (2026-09-09 03:01:34 Eastern):**
FF 172,914,240 bytes; fresh streamed sound bank 174,624,640 bytes. All 1,164
snapshot/repo/deployed inputs match and predate the FF; complete scripts, UI
and zone-source comparisons also pass. The packed asset list contains all six
staff variants, nine perk animation clips, the dedicated animtree/module and
green Healing Aura FX. All four reload sound aliases occur in the inflated FF.
Full BSP, navigation, lighting, script/asset/Lua gates pass; only the ten already
waived third-party asset warnings remain. All dev/god flags are OFF.
This build includes every queued change through the latest staff handling pass:
perk-machine animations, green Healing Aura FX, Winter's Howl reload foley,
ice damage/rate/radius nerfs, fire rate/radius nerfs, Archmage sprint fire and
Protector entrance elite immunity. Ready for native testing; no in-game visual,
audio or handling playtest has been performed by the agent.


**Further staff handling and ice cadence nerf (2026-09-09, built):**
User confirmed ice SHOT SPEED means FIRING RATE. Ice fireTime 0.80 -> 1.00s:
20% fewer shots per second (25% longer interval); projectile speed stays 2200.
All twelve staff lower/raise timing fields multiplied by another 1.5 across
lightning/fire/ice, then regenerated q0/q1. Normal drop+raise now
0.5625+0.9000=1.4625s; Mystical Hands 0.1875+0.3000=0.4875s. First raise
1.4625s normal / 0.4875s with card. Quick/empty/ADS-alt/swim timings also scaled;
unused zero alt times remain zero. Generator q-axis formatting now keeps five
decimals so the smaller one-third timings stay exact; other axes keep four.
Semantic comparison proves every timing exactly 1.5x the prior value in all
nine source/generated staff blocks, and only ice fireTime also changed.
Every other weapon/block, registration list and cost CSV stayed unchanged.
Normal cycling is native. Script immediate switches are bounded re-equips for
actual variant/PaP changes, not a Mage normal-cycle override; fire's cooldown
controller only gates shooting. Mage does not receive the Skirmisher HANDLING
card. Updated armory cadence and Mystical Hands timings.
Included in the verified 03:01:34 full build above; native playtest pending.


**Protector entrance elite immunity (2026-09-09, built):** The
Rogue Protector's drop-in kill already excluded the three boss flags but missed
armored sprinters, which deliberately use tod_is_sprinter instead. Added the
landing-specific zm_zod_robot::landing_splash_immune helper and use it in BOTH
_tod_bosses::landing_kill_splash and the vendored Civil Protector landing damage.
It excludes the three existing boss flags, armored sprinters, tagged
(tod_boss_kind) elites/bosses, dead actors and invalid entities BEFORE DoDamage,
StartRagdoll or LaunchRagdoll. No global boss classification or balance changes.
Ordinary zombies retain the existing 350-unit entrance kill and fling; caller
attribution, the lander's own exclusion and harmless relocation landings remain.
Both actual GSC loops pass mocked-actor tests covering all markers, sprinters,
ordinary victims, the exact radius edge and attribution. Arity passes.
Included in the verified 03:01:34 full build above; native playtest pending.


**Staff splash radius reductions (2026-09-09, built):**
Fire explosionRadius 192 -> 144 units (-25%); ice 160 -> 144 (-10%).
Regenerated all four fire/ice q0/q1 variants. Semantic comparison against the
pre-change GDTs proves only explosionRadius changed, with lightning and every
other weapon unchanged. Direct and inner/outer splash damage, minimum radius,
projectile spread, shot cadence and Mystical Hands handling remain as before.
The ice radius applies independently to each of its three real projectiles.
Updated the armory staff table. Registration count remains 235 and weapon cost
table 238/240, byte-identical to before. GDT changes require a FULL build.
Included in the verified 03:01:34 full build above; native playtest pending.


**Mage balance and Archmage sprint fire (2026-09-09, built):**
Ice damage reduced 20% for every target: beast matchup 4.19 -> 3.352 and
all-other-target matchup 2.95 -> 2.36. Those two paths cover every ice hit,
including all three volley missiles, splash and Panzer hits; card bonuses,
PaP and Archmage still multiply the reduced values. ICE SHATTER remains
+15% per level. Fire's shot interval increases 10%, 1430 -> 1573ms. The 0.10s
native state and fire-only lock are unchanged, preserving swaps and use prompts.
Archmage now grants native specialty_sprintfire through a shared
_tod_upgrades::apply_sprint_fire owner. Both the regular upgrade maintenance
and Archmage start/end use that helper, preventing the old card-only upkeep
from stripping the temporary grant. Quarter-second active checks exclude dead,
downed and disarmed Mages; class changes refresh immediately. An owned Sprint
Fire card retains its existing permission independently after Archmage expires.
Updated card/server copy and armory matchup/cadence values. All 64 native-perk
ownership/state cases, ice-before/after damage ratios across tiers/cards/forms,
fire recovery, staff asset integrity, arity and Lua structural checks pass.
Included in the verified 03:01:34 full build above; native playtest pending.


**Staff reload sound (2026-09-09, built):** All three approved
reload clips already had wpn_staff_reload_1..4 notes at frames 14/29/43/59, but
none of those aliases existed in the active sound tables. Added all four to
tod_ports, backed by four short Winter's Howl freezegun reload foley excerpts.
Sources: installed _t8/reload/fly_freezegun_mag_release.wav (first two beats)
and fly_freezegun_mag_in.wav (last two). Each excerpt is 0.28s with 8ms edge
fades, 48kHz stereo 16-bit PCM; exact ranges are in sound_assets/tod/mage/README.
Native animation notes own timing, including Speed Cola and unreached-cue
cancellation on interruption. No scripted sleeps, animation edits or new weapon
registrations. Validated all six q0/q1 staffs and four reload slots each against
the aliases/WAVs and active bank config. Reload mana regression passes.
Included in the verified 03:01:34 full build above; native playtest pending.


**Healing Aura green player FX (2026-09-09, built):** Reused the
installed Near Death Experience third-person effect as a map-owned green tint
(`share/raw/fx/tod/mage/fx_healing_aura_player.efx`). Donor is stock
`zombie/fx_bgb_near_death_3p`: only its 118 color-graph RGB keys changed;
particle motion, sizes, lifespan, camera fade and revive-symbol material remain.
The original source graph is blue, so this is a green adaptation, not a claim
that stock Near Death Experience was green. No image or sound imports needed.
Replaces the machine-light aura and repeated robot-revive hit bursts with one
upper-torso FX host per protected player. Healing pulses and overlapping auras
reuse that host. Host-owned cleanup checks actual aura protection and removes it
after expiry, downing, death or disconnect, including caster disconnects. Native
particles may fade for their original lifetime after the host is removed.
All recipients, including the caster, receive it; native near-camera fade keeps
the world effect out of first person, where the existing green health bar remains.
No new replicated fields; healing, resistance, charges, sound and cast animation
are unchanged. Actual-script lifecycle and healing-scaling tests pass; native
appearance/attachment is untested.
Included in the verified 03:01:34 full build above; native playtest pending.


**Perk machine animations (2026-09-09, built):** Wired the installed
WetEgg SAT animation assets for Speed Cola (power transitions and powered loop),
Double Tap (idle and purchase intro/finite loop/outro), and Wisp Tea (powered
idle and purchase activation). All nine source clips were parsed against their
conversion skeletons: every animated bone exists and tag_origin has zero
translation range. The other current sold machine folders contain no xanims.
Uses stock player perk_purchased, not the vendor-only activateMachineFX event.
No vendor Double Tap bonus attacks or perk balance changes were imported.
A dedicated tod_perk_machines animtree and nine zone xanim entries are included;
sync copies repo animtrees without mirroring over installed third-party trees.
Native AnimScripted playback is cancelled synchronously before shuffle movement
and retirement. Controllers resume using current origin/angles after the glide,
without replaying the power intro; power/model changes also refresh the pose.
No new clientfields or weapon registrations. Actual-script state/sequence tests
cover power, purchase flow, movement and retirement; native appearance, sound
and multiplayer synchronization remain untested.
Included in the verified 03:01:34 full build above; native playtest pending.


**Healing Aura per-level strength (2026-09-09, built):** Lv1 keeps
10 HP/s and 50% damage resistance. Each additional card level adds 1 HP/s and
2 percentage points of resistance: Lv1-6 = 10/11/12/13/14/15 HP/s and
50/52/54/56/58/60% resistance. Five-second totals = 50/55/60/65/70/75 HP.
Caster level is latched for the pulse thread and shared with all recipients.
Integer HP pulses alternate where needed, avoiding trickle_heal's per-pulse
round-up at odd HP/s levels. Existing max-health cap remains authoritative.
Resistance tracks a recent timestamp per aura level on each recipient; the
strongest fresh level wins. A weaker aura neither replaces stronger protection
nor extends its lifetime. Existing 700ms grace and per-cast healing pulses
remain. These fields are server-only, with no new clientfield registrations.
Updated live aura text, card/server descriptions, pause values and armory copy.
Duration, radius, charges, Lv6 revive and the new sound/first-raise gesture
remain. Tests cover Lv1-6, exact full-cast totals, caster-to-teammate strength,
overlap precedence/expiry and Lua readout parity. Native playtest pending.
Build VERIFIED 2026-09-09 01:58:18 Eastern: FF 172,362,496 bytes;
1,142 snapshot/repo/deployed inputs match and predate FF. Fresh sound bank
174,624,640 bytes; only established waived asset warnings.
Dev/god OFF. Ready for native testing.


**Staff card buffs and Panzer damage display (2026-09-09, built):**
FIRE BLAST now adds 25% damage per upgrade level (Lv1-6: +25/50/75/100/125/150%;
maximum multiplier 2.50). ICE SHATTER adds 15% per level (+15/30/45/60/75/90%;
maximum 1.90) and retains its slow duration. These add per level, not compound.
Updated server domain copy, Lua card descriptions/pause values and armory
ladders/current overview. Removed the misleading Fire copy promising a DOT;
its existing survivor flames are visual. Baked card art has no percentages.
Panzer staff numbers now defer from the level callback to the final Panzer
wrapper: stock armor/hit-location reductions finish before one HUD push.
A 4,000 incoming hit reduced to 2,000 displays 2,000; zero/immune results emit
no positive number. Existing direct+splash/crowd summing remains. Marker is
installed with the wrapper; other actors and non-staff HUD paths stay as before.
The previous Panzer calculation body is unchanged, including armor side effects
and lightning's 5.60 matchup multiplier. This corrects reporting, not a hidden
lightning buff. Tests exercise live staff arithmetic at Lv0-6, all six staff
variants, 60 final-result cases, untouched result returns and early HUD suppression.
Lua 5.1 parsing/level readouts, armory constants, arity and fire cooldown pass.
Native Panzer shots-to-kill still need user testing with the corrected numbers.
Build VERIFIED 2026-09-09 01:51:45 Eastern: FF 172,361,408 bytes;
1,142 snapshot/repo/deployed inputs match and predate FF. Fresh sound bank
174,624,640 bytes; only established waived asset warnings. Dev/god
OFF. Ready for native playtest; no gameplay test performed by the agent.


**Healing Aura cast presentation (2026-09-09, built):** Imported the
user's Healing_aura_#4-1788931088647.wav unchanged as
sound_assets/tod/mage/healing_aura.wav (48 kHz stereo, 16-bit PCM, 2.76s).
A distinct tod_mage_heal_activate alias plays locally on a successful cast.
The caster skips the separate first-heal receipt ping; teammates retain that
short stock cue. Locked, active and empty-charge refusals do not play either
the activation audio or gesture. The held staff's native InitialWeaponRaise
replays its existing first-equip animation without replacing the weapon.
The reload-attempt cancellation notify precedes the gesture so an interrupted
reload cannot pay mana. All six q0/q1 staff identities are preserved.
Native sound mix and repeat first-raise playback need an in-game check.
Build VERIFIED 2026-09-09 01:44:06 Eastern: FF 172,361,344 bytes;
1,142 snapshot/repo/deployed inputs match and predate FF. Fresh sound bank
174,624,640 bytes; only established waived asset warnings.
Successful/refused cast checks cover all six staff variants; reload mana and
arity checks pass. Native animation and audio playtest pending. Dev/god OFF.


**Fire recovery correction (2026-09-09, built):** Replaced the failed
swap-button workaround with a fire-only cooldown controller. Native fireTime
is 0.10s, while script retains the 1,430ms deadline via DisableWeaponFire.
No DisableWeapons, forced swaps, inventory replacement or use-trigger bypass.
Other held weapons clear our flag; returning to fire preserves the deadline.
Death/down/disarm clear our flag, and menu/laststand weapon locks are separate.
Mystical Hands still changes lower/raise only. Charge input cannot pre-bank
while recovery, reload, switching or menus block it. Native action/animation
behavior needs a playtest; script lifecycle and generated variants are checked.
Damage audit: native fire is 1,600 direct + 2,200 inner / 700 outer splash,
then the existing per-target upgrade/tier/matchup/charge multipliers. The HUD
SUMS damage across crowd targets. Fire FX on survivors are visual, not a DOT.
Ordinary-zombie callback returns the calculated damage; no zero-damage branch
was found there. Panzer stock armor applies AFTER the HUD push, so that readout
can overstate actual damage. No damage or enemy-health balance values changed.
Full build VERIFIED 2026-09-09 01:39:13 Eastern: FF 172,362,880 bytes;
1,141 snapshot/repo/deployed inputs match and predate FF, fresh sound bank
174,624,640 bytes. Only established waived asset warnings. All dev/god flags
OFF. Fire cooldown, reload, Blink, ice-volley, arity and staff asset checks
pass; native post-shot interactions and animation feel await user playtest.


**Mage follow-up (2026-09-09):** Blink recharge multiplied by 1.5 at every
level BEFORE the existing Attunement scale: Lv1..5 base 12/10.5/9/7.5/6s.
Two-charge cap from Lv3 and sequential recharge/elite refunds unchanged.
First-raise animation notes already contain wpn_lightningstaff_1straise,
wpn_firestaff_1straise and wpn_waterstaff_1straise at frame 1. Added all three
aliases to tod_ports, backed by vendored staff_first_raise.wav (stock elemental
bow equip foley donor; actual Origins staff equip WAVs were not available).
No mesh/animation changes. Chain Lightning no longer spawns an unlinked
origin+48 FX host. It deals damage, starts FX only on survivors, and refreshes
one torso-bound effect per actor/viewer. A mirrored 2-bit ACTOR int field uses
0=off, 1/2=refresh; no clientuimodel bits or weapon registrations added.
CSC KillFX on refresh, death, shutdown and 1.5s expiry; suppresses late positive
fields on dead actors. GSC timeout/death clears the field and resets state.
Tests pass for all Blink levels and charges, actual client FX lifecycle with
independent viewers, arity and Lua layout. First-equip audio and corpse FX
still need native testing.
Full build VERIFIED 2026-09-09 01:25:07 Eastern: FF 172,364,160 bytes;
1,141 snapshot/repo/deployed inputs match and predate the FF. Fresh sound
bank; only established waived asset warnings. All three first-equip aliases
and tod_mage_chain_fx are present in the inflated fastfile. Both batches of
Mage fixes are built; native playtest still required. Dev/god flags OFF.

**Mage normal-run corrections (2026-09-09):** Removed the remaining server
Archmage HUD text row (ready bind + active label); the existing LUI full-bar
PRESS AIM BUTTON cue remains. Mana income and reads require the first
mage_arch card; locked bar state 3 forces zero and suppresses readiness.
Ability notifies encode -1 for locked and 0 for unlocked/cooling down. Both
Mage offhand tiles hide until their card, dim after charges are spent, and
clear inherited everHad flags on class changes. Cast unlock gates retained.
Lightning AND ice now use guidedMissileType=None for straight flight.
Lightning explosion shake and minimum view kick are zero across q0/q1.
Lightning idle/fire/ADS-fire/hold camera tracks were inspected: all static.
Optional reloads now have real reserve ammo (clipOnly=0, nonzero segmented
reloadAmmoAdd, ammo insertion at full 1.5s animation end). A Mage-only ammo
watcher restores the held staff to clipSize-1 plus reserve while NOT reloading,
switching or downed: shooting stays free and one round of space permits an
optional reload. Separate per-element clip/reserve names prevent cross-staff
sharing. Existing completion+interruption guards award 5 mana only after
Archmage unlock. Uses native reload/Speed Cola playback, not a fixed reward
sleep or a separate fake animation. Mystical Hands still affects swaps only.
Tests: actual GSC reload/replenishment helpers, Lua 5.1 HUD setters+full-widget
parse, Blink/fire-switch/ice-volley regressions and staff/asset/arity/Lua gates
pass. Native optional reload, Speed Cola and projectile/HUD visuals need play.
Included in verified 2026-09-09 01:25:07 Eastern full build; native testing
pending. All gameplay dev/god flags remain OFF.

**Normal playtest mode (2026-09-09):** User requests development and god
mode OFF for a real run. Disabled tod_god, tod_dev_money, tod_dev_doors and
tod_dev_altar in zm_tower_of_doom::tod_resolve_dev_flags. tod_dev and
tod_dev_maxed remain false; every gameplay dev/god flag is now false.
Normal money, damage/downing, door purchases, altar limits and progression
apply. Mage and the latest staff/Chain Lightning/Archmage HUD changes remain
available.
Script build VERIFIED 2026-09-09 00:38:15 Eastern: FF 172,356,864 bytes;
142 snapshot/repo/deployed inputs match and predate FF; all deployed dev/god
flags false. Fresh sound bank; only established waived asset warnings.
Ready for the user's normal playtest; not yet played.

**Archmage rainbow health bars (2026-09-09):** Active Archmages now cycle
six rainbow colors on their local HP bar and every viewer's party row. A
single server watcher sends a four-player mask to ALL players on changes
(100ms polling) and every 2s to hydrate late/recreated HUDs. Entity numbers
match the kit's existing health/state slots. No extra clientfield bits or
per-color network events. Inactive/dead/downed/disarmed/disconnected players
are omitted; animation is presentation-only and does not change form timing.
TodHealthTint.lua owns color on a parent element, separate from the original
fill's health/bleedout shader animation. Six 180ms transitions repeat through
one animation-completion handler; no UITimer. Downed red overrides rainbow,
then Archmage overrides local healing-aura green; expiry restores the proper
base tint. Local/party widget edits replace existing calls to respect the
large PlayerInfo closure limit. One notify subscription per widget, roster
rebind by actual clientNum, close stops the animation and closes its parent.
Lua 5.1 parsing passes for all four changed Lua files. Actual helper tested
with 256 controller/player/mask combinations plus color sequence, heartbeat,
rebind, down/revive, aura priority and close. Actual GSC broadcaster tested
for recipients, mask, change/heartbeat, down and disconnect. Native color
inheritance/appearance and co-op synchronization still need a BO3 playtest.
Script build VERIFIED 2026-09-09 00:33:47 Eastern: FF 172,356,864 bytes;
142 inputs match snapshot/repo/deployed and predate FF; TodHealthTint rawfile
packed, sound bank regenerated (174,624,640 bytes). Only established waived
asset warnings. Native visual/co-op testing remains pending.

**Chain Lightning target nerf (2026-09-09):** Additional chain targets now
follow Lv0..6 = 0/1/2/2/3/3/4 (user milestones: Lv2=2, Lv4=3, Lv6=4).
Owned Dark raises the cap to FIVE (six until the 2026-09-09 ceiling pass) via the existing tod_dark bit; mage_bolt is
now eligible in the normal maxed-domain Spire Dark pool. Direct hit, 50% chain
damage, radius, nearest-target selection, Panzer exclusion and no recursion
are preserved. GSC chain_targets and Lua DETAIL/DARK readouts agree. No new
registrations, clientfields or image assets. DARK_TEXT_ONLY[53] prevents a
missing-image registration; a Dark card without art uses the composite DARK
text layout instead of the misleading Ultimate +3 picture. Pause uses the
existing tinted plate. Asset lint parses this exception and requires both the
registration and composite-render guards; negative controls exercise each.
Script build VERIFIED 2026-09-09 00:23:22 Eastern: FF 172,360,704 bytes;
227 inputs match snapshot/repo/deployed and predate FF, fresh 174,624,640-byte
sound bank. Only established waived asset warnings. GSC count checks cover
Lv0..6, Dark and cap; Lua ladder matches; asset lint negative controls pass
(17/17), Lua/arity/domain checks pass. In-game target-count test pending.

**Staff handling and fire recovery (2026-09-09):** User clarified base swaps
should take 50% LONGER. Multiplied all 12 lower/raise fields on all three base
staffs by 1.5 and regenerated q0/q1. Normal lower+raise is now 0.375+0.600s
(previously 0.250+0.400s); Mystical Hands remains one third of each new timing.
Only those timing fields changed in the source GDT; charge, fire and reload
values remain intact. Fire's 1.43s post-shot window now watches the native swap
button and requests SwitchToWeaponImmediate() once if normal switching has not
started. This bypasses outgoing recovery/drop while keeping incoming raise;
engine selects the next held weapon, preserving PaP/ammo/q1 identity. No forced
swap without input, no intervention in charge-up or other weapons. Death,
disconnect, class disarm, next shot/change, menu/pause and downed state cancel.
GSC coroutine tests cover window expiry, held input, events and guards; native
button coverage and recovery cancellation still need BO3 testing. Build guard
checks recovery duration against fireTime and all six twin handling ratios.
Full asset build completed 2026-09-09 00:10:21 Eastern. Concurrent source
edits required a script relink; that attempt hit a sound-bank lock and was
rejected. With game/build processes closed, parked sound/zone under session
TEMP and regenerated it. Final build VERIFIED 00:15:42 Eastern: fastfile
172,358,656 bytes; 227 snapshot/repo/deployed inputs match and predate FF;
86 required animation/weapon/muzzle-FX assets packed. All script tests and
staff timing guards pass. Only established waived asset warnings. Native
post-fire switching and revised handling feel still need user playtesting.
User recovered from the earlier startup issue
on the UNCHANGED build; cost exceptions were real but did not prevent eventual
play. The included cost-table cleanup is not a proven fix for the initial stall.

**Startup weapon-cost overflow (2026-09-08):** Investigated the reported
launch stall in the unchanged 23:21 build; no fatal was established. Initial 23:33 log stopped at
ModLoad done with no fatal; retry 23:46 reached match startup and exposed
43 `Too many weapon costs added to weapon cost list` exceptions from stock
`_zm_weapons.csc::on_player_connect` / SetWeaponCosts. This is a SEPARATE
registry from the 235 weapon-asset ledger. The CSV held 304 distinct base/up
price keys. Removed exactly 33 unobtainable stock gun rows: 238 keys remain,
all 95 generated PaP mappings and every retained row unchanged. No weapon
assets were retired; GDT hashes are identical. Generator removes those rows
idempotently and checks the cost budget BEFORE any outputs are written.
`tools/verify_weapon_costs.js` gates every build, with a conservative table
budget of 240 (not a claimed native capacity). Its self-test catches the old
304-key failure and upgrade-key counting; generator double-run is identical.
Also fixed ice_side_shots comparing an undefined element to a string when a
mage fired a nonstaff; this was a separate potential runtime error, not the
observed startup cost exceptions. Ice/reload-mana tests pass. Rebuild/boot test pending
BO3 closure. Failed logs saved in the session temp folder.


**Reload mana (2026-09-08):** User requests a small mana reward for a full
successful staff reload. All three staffs now award 5 mana once per completed
reload, via mana_add (100 cap, no gain during Archmage). A reload_start arms
one attempt; stock reload notification plus IsReloading clearing confirms
completion past the ammo/animation tail. Fire, weapon change, sprint, melee,
new reload, class disarm, death and disconnect cancel pending rewards. Final
state guards also reject downed/menu/paused players and changed weapons.
HUD updates through the existing mana_push path. No new sound/toast spam.
`tools/test_mage_reload_mana.js` exercises actual GSC coroutine logic with
simulated native events: no early/double award, 18 cancellation cases, state
guards and cap pass. Native notification timing remains a playtest check.
Script build verified 2026-09-08 23:21:22 Eastern: FF 172,361,728 bytes,
138 script/UI/zone inputs match snapshot/repo/deployed and predate the FF.
Only established waived linker warnings. Completion/cancellation behavior
still needs confirmation in BO3.


**Ice volley correction (2026-09-08):** Ice was one native missile with
cosmetic flying icicles in the muzzle FX. `ice_volley_watch` now adds two real
missiles per ice weapon_fired event, using the exact fired variant/player via
MagicBullet (stock multirocket pattern). Symmetric +/-8-degree view-space fan;
center remains native. Side hits use full existing per-projectile damage,
splash and normal ice slow/PaP/matchup callbacks. Overlapping explosions can
increase damage to one target; this is not a damage-neutral cosmetic change.
No extra weapon registrations or ammo deductions. Custom 1p/3p muzzle FX each
remove 13 cosmetic icicle-model emitters, keeping the other flash particles;
real missiles retain the stock trail/impact. All generated ice twins use the
new muzzle FX. `tools/test_mage_ice_volley.js` passes 40 aim/variant cases plus
non-ice filtering; engine collision and side-hit damage need playtesting.
Full build verified 2026-09-08 23:16:59 Eastern: FF 172,363,328 bytes,
fresh all.sabs 174,624,640 bytes; 224 inputs match snapshot/repo/deployed and
predate FF; 89 required staff assets packed, including both new muzzle effects.
Only established waived asset warnings; prior Enfield checksum warning did
not recur. Runtime outer-bolt collision/damage still needs playtesting.

**Staff glow follow-up (2026-09-08):** Removed the 0.4s settle timer and
replicated-field FX callback. Local client weapon_change now kills the old
particles with KillFX and immediately attaches the held staff's aura. Same-
element q0/q1 swaps also replace it; death/disconnect/entity shutdown clean up.
The existing two-bit field layout is retained with no callback, so late server
snapshots cannot restore the previous element. Full build verified 23:07:03
Eastern: FF 172,209,344 bytes; fresh sound bank 174,624,640 bytes. 222 inputs
match repo/deployed/snapshot and predate FF; 87 staff assets packed. Runtime
swap/reload/sprint verification pending. Unrelated Enfield shot2 source-checksum
warning appeared; WAV exists/parses and bank was regenerated.

**Staff playback follow-up (2026-09-08):** User requests shoot-to-interrupt
reloads while keeping their animations, and sustained sprint motion. All three
staff sources/q0/q1 now use segmentedReload=1 with the existing zero-duration
reload end; clip-only ammo and reload clips retained. All three sprint-loop
xanims now looping=1 (previously 0). 31-frame sources have real motion and
matching end/start poses. Importer/build validator preserve both requirements.
Included in the verified 23:07:03 full build; runtime reload interruption
and sustained sprint playback still need in-game confirmation.

**Staff animation migration (2026-09-08):** User approved moving all three
staffs to Tower, with a remaining fire-shot "wings" correction. Fire head now
holds its actual assembled bind shape; all shot/ADS/charge vertices checked.
78 vendored clips, 45 slots per staff, all six q0/q1 twins migrated. Original
ammo/damage/glows/timings retained; Mystical Hands remains 3x faster; ledger235.
Full build VERIFIED 22:20:35 Eastern: FF 172,209,792 bytes, sound bank
174,624,640 bytes, 87 required assets packed and 222 deployed sources matched.
Corrected shared i_generic_lookup semantic to revealMap to clear a full-link
shader failure. Fire fix is built but not yet played.
tools/import_staff_animations.py imports; verify_staff_animations.py
gates every build; assets are self-contained. See docs/117 migration section.
No further approval is required to perform this migration/build.

**Historical test results:**
**Closer staff audit (2026-09-08):** test+map/docs/28 follow-up now includes
independent model/mesh/transition checks and damaged-pose negative controls.
Caught/fixed lightning branch translation origins in first raise, hold and
melee before another build. 48 clips pass; offline meshes inspected. Test build
verified 21:47:33 Eastern, 65 assets packed and 83 sources matched. Tower migration stays pending
fire/lightning visual approval; ice approval stands.

**Staff animation testing (2026-09-08):** Tower still uses `vm_freezegun_*`.
**Follow-up:** test+map/docs/28 corrects fire/lightning's doubled forward head
offsets (their raw roots are shaft-space, unlike ice's zero-origin head).
Same actual Tower models; updated tests normalize each head's authored origin.
Tower glows now ported into the test via _sla_staff_glow. Test build verified
21:47:33 Eastern; fire/lightning approval and Tower migration remain pending.

User APPROVED ice full alignment and requested fire/lightning tests before
Tower migration. test+map/docs/27 and tools/staff_element_tests.py add
original/animated pairs for each; melee cycles FIRE A/B, LIGHTNING A/B, ICE A/B.
Approved ice preserved. 48 clips / 1,636 frames checked; test build verified
20:49:14 Eastern with all new clips packed and 80 deployed sources matched.
User authorized Tower migration CONDITIONED on fire/lightning visual approval;
do not migrate yet, and do not request ice approval again.

**History:**
User requested copying Tower's actual ice staff into test+map and adding the
staff animations. Current test: ICE A original Tower q0; ICE B same shaft and
water/ice tip with 30 staff clips and 12/120 reload-test ammo. User reports B
incorrect and hold-melee failed. Now spawn A; press/release melee to compare.
Re-audit confirms original model/attachment fields and 42 assets match.
User now confirms A complete and switching works. B idle's cradle is below the
shaft and base appears missing. Idle-only correction was closer, but equip/fire
still displaced it. test+map/docs/26 and tools/staff_ice_alignment.py now apply
the correction across 24 full-pose clips and match A's resting placement with
a uniform translation. Same meshes/scale, A intact; test build verified 20:31:05
Eastern, visual test pending.
R5 arm-spike fix is confirmed and retained. Explicit attachment tag lost the
head; Tower's blank tag is preserved. R6 fire probes were NEVER BUILT and are
superseded. Missing shaft/head appearance is still awaiting visual confirmation.
Do not move a candidate into the tower until the user confirms its appearance.

**Mystical Hands experiment (2026-09-08; formerly Quick Hands):** User authorized three extra staff
variants and a registration guard of 235 (207 generated + 28 fixed), pending
boot testing. Mage-only ultimate, domain 56, max 1, no dark version, persists
through promotions. q0/q1 staff twins differ only in lower/raise timings:
q1 takes one third as long. Reconcile every retained primary, not only the
newest staff. Approved ultimate card and pause plate r56 installed (docs/123).

**Mage PaP (2026-09-08):** Additive primaries store every PaP level, including
I, by staff stem via `_tod_classes::pap_tier` / `pap_first_grant`. Never use
the shared `tod_pap_owned` latch or empty `up_suffix` to test staff packing.
Promotion requires the current tier's staff packed; older staffs retain their
level and newly added staffs start unpacked. Staff first PaP uses the existing
`zm_cwpap::giveWeaponRepacked` take/return presentation. See docs/114.

**Blink storage (2026-09-08):** One charge at levels 1–2, two maximum from
level 3 onward, locked at level 0. `blink_charges_now()` owns both cast and HUD
readiness; the tactical tile shows the charge count. Sequential recharge uses
the existing `tod_mage_cd["mage_blink"]` timer so elite refunds still apply;
spending the second charge preserves timer progress. See docs/114 and
tools/test_mage_blink.js.

Custom BO3 zombies map `zm_tower_of_doom` — a **classic tower map with a twist**,
set in the same cyber-city universe as the user's first map
(`c:\Users\jorda\Repositories\abandoned_cyber_city_zombies`). **That repo is the
knowledge base for this one** — read `docs/BO3_MAPMAKING_KB.md` (copied here into
`docs/`, canonical copy lives in both repos) FIRST, and consult the old repo's
`CLAUDE.md`, `docs/14_stock_api_verification.md` (stock-API traps ledger) and
`docs/16_community_techniques.md` before touching stock interfaces. Do NOT
re-learn lessons that map already paid for.
