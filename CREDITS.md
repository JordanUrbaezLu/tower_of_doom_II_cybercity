# CREDITS — required before any PUBLIC release

Beta (Friends-Only) does not gate on this; the PUBLIC flip does. Compiled
2026-08-23 from the release audit; all author handles VERIFIED from the pack
readmes 2026-08-24 (GentlemanCheeseMan, HarryBo21). No open items.

## Music
- 2026-09-30: every music wav carries a -2.5 dB low shelf under 200 Hz ("25% less bass", user) — see sound_assets/tod/music/README.md; the recordings are otherwise unchanged.
- "Falling To Pieces" — user-supplied 2026-09-13 (the teddy bear song, `tod_music_ee`). ⚠️ LICENCE UNCONFIRMED: a commercial recording; map 1's credits marked its commercial EE songs DO NOT PUBLISH. Confirm before a public upload.
- ⚠️ 2026-09-28 — THE TOD II TRACKS BELOW ARE COMMERCIAL RECORDINGS, LICENCE UNCONFIRMED (same flag as "Falling To Pieces"; confirm before a public upload). Sources: the official YouTube Music "Topic" uploads, except Meteor Herd (a fan instrumental upload).
- "La Clé des Champs" — N'to (floors 50-42, `tod_music_eclipse`)
- "Space Trip Steps ...for Meteor Herd" (instrumental) — Tomoya Ohtani / SEGA, Sonic Adventure 2; since 2026-10-01 the FLAC "Instrumental Attempt" from the unofficial Internet Archive compilation `sonic-adventure-2-hip-hop-soundtrack` (was the CG Instrumentals YouTube upload) (floors 8-1 and the ground, `tod_music_relay`; moved to the bottom band 2026-10-01)
- "Cornfield Chase" — ItsArius & Lynnic (floors 33-26, `tod_music_cornfield`; added 2026-09-29, official upload on Lynnic's YouTube channel TFEdFXArQz0; ⚠️ LICENCE UNCONFIRMED like the rest of this list)
- "With You" — Lynnic, ItsArius & Dinia (floors 41-34, `tod_music_withyou`; added 2026-09-30 with the VOCAL REMOVED by source separation (demucs) from the official upload on Lynnic's YouTube channel YWTrmXf0Uxs; ⚠️ LICENCE UNCONFIRMED like the rest of this list, and a derived instrumental edit of a commercial recording)
- "Una Mattina" — Lynnic (floors 25-18, `tod_music_city`)
- "Reykjavik" — Joachim Pastor (floors 17-9, `tod_ambient_music`)
- "115" (extended edit made for this map) — Elena Siegman / Kevin Sherwood, Call of Duty: Black Ops (the boss track, `tod_boss_music`, played in the Battle Arena)
- (retired 2026-09-28 from TOD II, still in TOD1: "Password Infinity" — Evgeny Bardyuzha; "Cyberpunk Futuristic City" — lnplusmusic; "Cyber Relay" — Psychronic; "Cyber Eclipse" — bykenneth; "Data Spike" — Psychronic)
- "You See Big Girl" — Hiroyuki Sawano / Gemie (finale)
- `tod_music_gameover` (the loss sting) and `tod_house_victory` (beating the Dealer) — 2026-10-04, original instrumental music generated for this map with ElevenLabs Music (music_v2_5, a paid Creator plan) by tools/sfx/end_of_run_music/make_sounds.py; no samples, no vocals, no third-party recordings.

## BO6 Wunderfizz

- Original Wunderfizz model, textures, rig, animation and sounds: Treyarch / Activision, Call of Duty: Black Ops 6.
- BO3 machine port: WetEgg, supplied in Kingslayer Kyle's [BO6Overhaul Assets v1.0](https://github.com/KingslayerKyle/BO6Overhaul). Original labels, geometry, texture maps, animation and PCM are preserved; native paths and alpha-compatible image conversion are documented in [ASSET_IMPORT.md](docs/wunderfizz/ASSET_IMPORT.md).

## Sound effects
- Baseball bat whiffs: user-supplied Floraphonic clips `swing-whoosh-5-198498`
  and `swing-whoosh-weapon-1-189819`, copied unchanged from the downloaded WAVs.
- Baseball bat impact — user-supplied `bathitball.wav`, September 14, 2026.
  Used unchanged for every bat contact; source author not provided.
- `tod_full_steam_wind` — generated for this map (FULL STEAM, the heavy's
  sustained-sprint speed boost). Source file trimmed to its steadiest 7.25 s and
  closed into a seamless 7.000 s loop with a constant-power crossfade; the
  generator's fade-in and fade-out were removed, since either one pulses audibly
  once a bed is looped.
- Retired 2026-10-04 with the Mage (no longer shipped): the staff shot / first-raise / reload sounds; their credits stay in git history (this file before 2026-10-04) and the files are in archive/mage_retired/sound_assets/tod/mage/.
- The first jump's crash (`tod_jt_*`, docs/196; `tools/jump_title/make_sounds.py`
  generates every file, so re-run it rather than editing a wav). Since 2026-09-30
  the boom and the ships are built from real recordings: Skye's (TheSkyeLord)
  launcher ports - the T6 rocket explosion, the S2 Bazooka's explosion and shot
  (its rocket motor carries the gunships' engines and their charge), the S1 Mahem
  explosion, the S1 Stinger shot (the engines lighting after a warp) - with the
  user's "explosion large distant" (GFX Sounds via Pixabay, already the C4's blast)
  under the boom, the stock BO3 'firey' blast and LFE hits, the Fury's bamf, and
  map 1's teleport warp and thunder. Pitched, filtered, layered and mastered by the
  script; the turbine whines and the jet wash are synthesised. The zombies Nuke
  power-up is no longer in it.

## Art / UI
- pmr360 — BOCW Baseball Bat port (Treyarch/Raven Software originals), including
  models, materials, animations and sound setup. Port readme credits the T9-to-T7
  rig by Thomas Cat / TheBlackDeath / DamianoTBM; Scobula, DTZxPorter, ID-Daemon,
  Eric Maynard, JBird632, Logical Edits, Harry Bo21, TheSkyeLord, lilrobot,
  Ray1235, MakeCents and MikeyRay for extraction, tooling and support.
- WetEgg / SAT — Black Ops 6/7 perk machine models, the perk icon set, and
  the Wisp Tea perk script (SATPerksAssets + SATPerksCode packs: all nine
  machines incl. Death Perception and the BO7 Wisp Tea, the crest HUD icons
  since 2026-08-29, and the vendored `_zm_perk_wisp_tea` module since
  2026-08-30). Per the code pack's instructions.txt (found 2026-08-30 — it IS
  the readme the assets pack lacked), credit also: Scobalula, DTZxPorter,
  Dest1yo, echo000 (Saluki and Cordycep); Kingslayer Kyle (vertex color
  materials); Rex (PHD Slider script and FX); Sphynx (original Death
  Perception script); rayjiun, shidouri, XcDylan93 (script assistance);
  garrett (improved Wisp Tea wisp FX); TNT, MoiCestTOM, Midgetblaster,
  Syndikate, Nastian, eMoX (testing).
- Nastian — T9 skybox pack: the map's sky was its Miami night (skybox_t9_mp_miami
  + acc_ssi_miami_night) through v17.70; since v17.71 our own sky still rides
  on a clone of that pack's sun/sky info (tod_ssi_cybercity) and the T6 dome
  mesh the pack installed
- emox — MWIII Vertigo material/asset pack (the Tron Grid look)
- DOGCANARY — "Images arrow coldwar dogcanary" power-direction wall decals
  (11 `arrow_power_coldwar*` materials / 11 images). 🔴 The art is Treyarch **BOCW**
  dark-aether wall scrawl (`i_mtl_t9_powerarrows_dark_aether_*` rips). Used since
  v18.99 for the six POWER / arrow decals that point players at the power switch.
  The same pack map 1 uses, installed in the SHARED tools root, not in either repo
  (`model_export/codimages/arrow_coldwar_dogcanary/`). **Credit DOGCANARY +
  Treyarch (BOCW) before Public** — map 1's CREDITS carries the identical flag.
- Owen-C137 — Aetherium HUD kit, with KingsLayerKyle, Shidouri & Madgaz (the
  kit renders all FOUR author signatures in the pause menu,
  AetheriumStartMenu.lua:1035-1060 — credit all four, publish-sweep find
  2026-08-29)
- Westchief596 & ZeRoY — [West] Ammo Crates (the ammo crate model,
  west_ammo_crate_model, built on ZeRoY's S4 crate) + [West] Community Perk
  Collection v2.7 (electric_cherry_model). Both force-packed; map 1's ledger
  recorded the pack's crediting request — publish-sweep find 2026-08-29.
- Unknown author — the "Chaos" Pack-a-Punch mesh worn by the six Heavenly
  Gift Altars (chaos_pack_a_punch.gdt; ximage_* extraction-named textures).
  No recorded author here or in map 1; shipped 2026-08-29 with an open
  "reach out to be credited" line in the Workshop description (user
  decision). If the source pack is ever identified, replace this entry.

- Logical — the cyberpunk Riot Shield mesh (`logical_m_shield_full` and its
  PBR set, the pack's own `log_riotshield_zm` weapon def): the RIOT SHIELD
  upgrade's level-5 "new model" since v16.63 (2026-09-02). Logical's ORIGINAL
  art (map 1 used the same mesh as a reskin; the pack's BO4 crafting bench is
  installed on the build box but NOT used or packed). Credit Logical.
- Treyarch — the level 1-4 shield is the stock Shadows of Evil rocket shield
  (`zod_riotshield`), same-game asset.

## Weapons / enemies
- Skye (TheSkyeLord) — the weapon ports (MSMC, Mk 48, MAC-10, MP5, Enfield, Krig 6, AK-47,
  Stoner 63, HK21, Magnum, AMP63, Ghosts Bulldog, Five-Seven, BO2 MP7,
  IW UDM...). Per the packs' README condition ("add the people on my modme
  post"), the Master Hub credits (recovered 2026-08-29 from the modme
  archive, thread 2565): Azsry (maya scripts, rigs), Scobalula (Greyhound,
  CoD Image Util, Camo Chairs, CoD Maya Tools), TomBMX (.ff exporter), Jari &
  Blak (mix map materials), raptroes, Thomas Cat (MW rig, IK help), JBird632
  (tutorials), .115 Cal (game shares), DTZxPorter (Kronos/ExportX, SE Tools,
  Wraith Archon, modme itself), Collie (IW7/WW2 conversion rigs),
  Ray1235 (CoD Maya Tools), xSanchez78 (IW7 conversion rig), lilrobot
  (inspectable weapons script)
- pmr360 — BOCW Wakizashi (KATANA)
- WetEgg / M5_Prodigy / J.G. / DeLeon / Santa Monica Studio — Leviathan Axe
  (STORMBREAKER)
- Kingslayer Kyle — the ARMORED SPRINTER's body (c_t8_zmb_mob_zombie_body3,
  Blood of the Dead character pack; readme's "Make sure you credit me" per
  map 1's ledger — publish-sweep find 2026-08-29)
- Spiki — mechz pack (the Panzer)
- HB21 — Apothicon Fury (the Reaver)
- ZoekMeMaar — thunderstorm FX + free-Pack-a-Punch powerup
- NSZ — Zombie Blood powerup
- Logical + NateSmithZombies — Time Warp + Infinite Ammo powerups (vendored
  2026-08-20; the zone file's credit-before-publish note — this line was the
  one gap in the 2026-08-23 audit, closed 2026-08-26 when the Workshop
  description gained its credits section)
- GentlemanCheeseMan — "Gift of Death" Xmas Gun pack (per its INSTRUCTIONS.txt;
  gun model Gerardo Justel, ornaments/bow Saritasa, sounds Orvani Sounds, some
  assets from MidgetBlaster's T7 pack; readme grants reuse permission)
- HarryBo21 — Civil Protector v2.0.0 companion pack (the Rogue Protector; pack
  CREDITS.txt lists ~40 contributors incl. TheSkyeLord, Scobalula, DTZxPorter;
  robot model/anims Treyarch, BO3 Shadows of Evil)

## Engine / tools
- Treyarch — Black Ops III Mod Tools + stock assets

## ALXS CW/BO6 Pack-a-Punch (v13.6)
- PaP model and anims: Madgaz, Owen C137
- PaP script: RiDD_Alexis31, JoaoSlideCancelo, Prov3ntus, Shidouri, Resxt, CF4_99, Rayjiun, devraw, and mod tools servers support
- PaP sounds: Owen C137
- Pack: "ALXS - CW-BO6 PAP" v1.1.2

## Pack-a-Punch camos (v17.50 onward)
- The three tier camos (gold / red anodized hex / Element 115) are stock
  Black Ops III camo materials, reached through the weapon camo tables each
  ported pack ships (Skye's packs, and WetEgg's Leviathan axe for the
  Stormbreaker). No custom camo art ships. The v17.35-v17.49 custom camo
  attempt (procedural art over Madgaz's `mtl_origins_camo_alt` material
  recipe) never rendered and is retired; the generator stays in the repo as
  a record only.
- THE BLACK MARKET DEALER'S VOICE (2026-10-02): an ElevenLabs text-designed voice (no clone, no reference audio, no actor), generated in-repo by tools/black_market_vo (docs/198 round 8). The 2026-10-01 consented clone of Edward Richtofen as performed by Nolan North (permission text: docs/licenses/) was retired the next day when the dealer became his own character; it no longer ships in any asset and the licence terms (this custom map only, noncommercial) are kept on file for the record.
