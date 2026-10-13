<!-- art-pack
name: sound_kit
typography: off
refs:
  sound_assets/tod/sfx/tod_pull_rung_1.wav | TIMING PLACEHOLDER for C1 (synthesized): the length and the moment it plays are right, the sound itself is what we are replacing.
  sound_assets/tod/sfx/tod_pull_rung_2.wav | placeholder for C2 (same length).
  sound_assets/tod/sfx/tod_pull_rung_3.wav | placeholder for C3.
  sound_assets/tod/sfx/tod_pull_rung_4.wav | placeholder for C4.
  sound_assets/tod/sfx/tod_pull_beat.wav | placeholder for C5.
  sound_assets/tod/sfx/tod_pull_legendary.wav | placeholder for C6.
  sound_assets/tod/sfx/tod_pull_alert.wav | placeholder for C7.
  sound_assets/tod/sfx/tod_super_sting.wav | KEEP (for loudness and flavour only): the sting a RARE or EPIC card already plays. Your set must sit at this loudness.
  sound_assets/tod/sfx/tod_ultimate_sting.wav | KEEP (for loudness and flavour only): an existing big sting.
  art/partner_shop/electrical_preview.wav | the Black Market shop's own crackle in the world (its sound palette: dirty neon electricity).
  docs/190_ref/installed_screen_1280x720.png | THE BLACK MARKET SCREEN (what M1-M13 accompany): a slot-machine reel of item tiles under a centre needle.
  docs/194_ref/card_reveal_sequence.png | THE CARD REVEAL (what C1-C7 accompany): a face-down card climbs white, blue, purple, gold, then flips.
  art/partner_shop/merchant.png | the masked black-market dealer (for the optional voice lines V1-V10).
-->

# 194 — The sound kit: the card reveal + the Black Market (sound request)

STATUS: the Part V dealer voice is SUPERSEDED 2026-09-30 by docs/198 (a designed ElevenLabs v4 voice generated in-repo by tools/black_market_vo, 47 lines; the ten V files keep their names and the kit manifest entries are refreshed by pick.py). Parts C and M stand. DELIVERED 2026-09-29 12:05 (`~/Downloads/files - 2026-09-29T120517.688.zip`, all 30 files incl. the
optional voice) and INSTALLED by `tools/sound_kit/install.py` (session 9c, the asset side; session d2 wires the
spin hooks in _tod_shop.gsc / test_spin.js). Every file passed the format/length/sample-0 checks; C and M go in
as delivered (already at tod_super_sting's -8.6 LUFS, the reveal ladder rising -11.5 -> -9.4 by design); the
dealer VO is lifted to ~-11 LUFS (latency-compensated -1 dBFS limiter). Alias PITCH IS IN CENTS: the crawl is
tod_spin_crawl_1..5 at 0/100/200/300/400. `install.py --check` re-verifies files + rows. WIRED 2026-09-29 12:28 by d2: `_tod_shop.gsc` plays M1-M13 + V1-V10 (docs/188 "Pass 3 art + sound"); `test_spin.js` pins every alias the spin can play. Zip of the request:
`~/Downloads/tod_sound_kit_art_pack.zip`. `typography: off` because a sound brief has no visual asset.

Repo side (not in the pack): the card reveal's seven `tod_pull_*` sounds are SYNTHESIZED
placeholders (docs/187), and the Black Market spin has no sounds of its own: its reel tick
(`tod_ui_tick`) and the COMMON landing (`tod_card_land`) are both the stock `glass_cling.wav`,
and the rest are borrowed card stings (docs/188 section 4). C1-C7 replace files by name (same
aliases, no wiring). M1-M13 are new aliases in sound/aliases/tod_ui.csv that TodSpinReel /
_tod_shop.gsc will play (the Black Market pass 3, docs/188). Install: `-Inspect`, LISTEN to every
file, check the format with Python's wave module (48 kHz / 16-bit / stereo), loudness-match against
tod_super_sting (sound_assets/tod/music/README.md recipe), copy into sound_assets/tod/sfx/, alias
rows, FULL build (the sound bank is rebuilt), then compare the bank size with the last good build.

<!-- PACK:BEGIN -->
# Sound kit: the card reveal + the Black Market slot machine

## What this is for
Two "gamble" moments in our cyberpunk zombies game need real sound design.

1. **THE CARD REVEAL** (`card_reveal_sequence.png`): after each round the player is dealt
   upgrade cards FACE DOWN. Each card's back glows and CLIMBS a rarity ladder, one rung at a
   time: COMMON (white) -> RARE (blue) -> EPIC (purple) -> LEGENDARY (gold). Between rungs there
   is a short heartbeat pause. Then the card flips. The rarer the card, the more the moment
   should feel like hitting a jackpot. The placeholders in `reference/` have the right LENGTHS
   and play at the right moments; the sounds themselves are what we are replacing.
2. **THE BLACK MARKET** (`installed_screen_1280x720.png`): a masked dealer (`merchant.png`)
   runs a neon slot machine. The player pays, their LUCK is poured into the machine, a reel of
   item tiles spins past a centre needle, slows down tile by tile, and stops on a prize. The
   prize is then socketed into one of their robot companion's three slots (or scrapped for
   luck). It should feel like a dirty, electric, underground slot machine: mechanical reel,
   buzzing neon, heavy coins.

Mood for both: punchy, satisfying, modern arcade / gacha-game juice, with a dark cyberpunk edge.
Clean transients, no mud, no long reverb tails on the short sounds. Listen to
`electrical_preview.wav` for the Black Market's palette (the shop's own dirty-neon crackle in the
world), and to `tod_super_sting.wav` and `tod_ultimate_sting.wav` for the loudness and weight
the game already uses (those two stay; they are not part of this request).

## Format (every file)
- **WAV, PCM 16-bit, 48000 Hz, stereo.**
- Peak at or below **-1 dBFS**; loudness matched to `tod_super_sting.wav` (short UI sounds can
  sit a little lower; the big stings a little higher).
- **The sound starts at sample 0**: no silence at the start (the game times these to the frame).
- End on silence (a natural short fade), no clicks, no loops unless the table says LOOP.
- File names EXACTLY as the tables.

## Part C: the card reveal (7 files, REPLACE the placeholders, keep each length within 10%)

| # | File | Length | What it is |
|---|---|---|---|
| C1 | `tod_pull_rung_1.wav` | 0.45 s | The card lights up at COMMON (white): a soft, clean chime with a small mechanical tick. The first step on a ladder. |
| C2 | `tod_pull_rung_2.wav` | 0.45 s | It climbs to RARE (blue): the same family, a clear step UP in pitch and brightness. |
| C3 | `tod_pull_rung_3.wav` | 0.45 s | EPIC (purple): higher again, with a crystalline shimmer. The player should lean in here. |
| C4 | `tod_pull_rung_4.wav` | 0.45 s | LEGENDARY (gold): the brightest and biggest rung, a swelling choir-like shimmer. Played back to back, C1-C4 must sound like one rising ladder. |
| C5 | `tod_pull_beat.wav` | 0.40 s | The HEARTBEAT between rungs: one deep, tense heartbeat thump with a sub-bass pulse. Plays up to three times per card, so it must not annoy. |
| C6 | `tod_pull_legendary.wav` | 2.0 s | The LEGENDARY card flips: a huge golden jackpot hit (impact + choir/brass swell + a long sparkle tail). The best sound in the game. |
| C7 | `tod_pull_alert.wav` | 0.9 s | Heard by the OTHER players when someone pulls a LEGENDARY: a short distinctive fanfare, clearly "something great happened to a teammate". |

## Part M: the Black Market (13 files, new)

| # | File | Length | When it plays / what it is |
|---|---|---|---|
| M1 | `tod_spin_coin.wav` | 0.6 s | The player pays: a heavy metal coin dropping into a slot and rattling down, then a mechanical clunk. |
| M2 | `tod_spin_open.wav` | 0.8 s | The machine's screen slams on: an electrical power-up hum rising, a neon buzz flickering on, one solid clack. |
| M3 | `tod_spin_luck.wav` | 0.7 s | The player's LUCK pours into the machine: a rising, shimmering cascade (like many small coins or glass beads streaming in, climbing in pitch). |
| M4 | `tod_spin_start.wav` | 0.9 s | The dealer yanks the lever and the reel releases: a ratchet crank, a spring release, a reel whoosh spinning up. |
| M5 | `tod_spin_tick_1.wav` | 0.08 s | The reel's flapper clicking past ONE tile: short, crisp, mechanical. Plays up to 10 times a second, so it must be tight and never harsh. |
| M6 | `tod_spin_tick_2.wav` | 0.08 s | A slight variation of M5 (the game alternates them so it never sounds like a machine gun). |
| M7 | `tod_spin_tick_3.wav` | 0.08 s | A third variation. |
| M8 | `tod_spin_crawl.wav` | 0.25 s | One of the LAST five clicks as the reel crawls to a stop: the same click with a clear musical note on it. The game plays it five times, raising the pitch each time, so make it at ONE pitch (a mid note) with a clean tail. |
| M9 | `tod_spin_stop.wav` | 0.4 s | The reel locks onto the prize: a heavy, satisfying mechanical CLUNK with a short metallic ring. |
| M10 | `tod_spin_socket.wav` | 0.6 s | The prize snaps into one of the companion's slots: a precise click-in plus a short rising energy hum (power flowing in). |
| M11 | `tod_spin_upgrade.wav` | 0.8 s | The prize upgrades an item the companion already has: the click-in plus a brighter, bigger power-up swell. |
| M12 | `tod_spin_scrap.wav` | 0.8 s | The player scraps the prize for luck: a glassy shatter / digital dissolve, then a short bright chime (luck coming back). |
| M13 | `tod_spin_close.wav` | 0.5 s | The machine powers down as the screen closes: a descending hum and a soft neon flicker-off. |

## Part V (OPTIONAL): the dealer's voice (10 short lines)
The masked dealer (`merchant.png`): a sly, raspy, amused black-market voice behind a mask (a
slight muffled / electronic filter). Keep every line under 2 seconds. Same WAV format.

| # | File | Line |
|---|---|---|
| V1 | `tod_spin_vo_buy_1.wav` | "Let's see what your luck buys." |
| V2 | `tod_spin_vo_buy_2.wav` | "Feeling lucky?" |
| V3 | `tod_spin_vo_buy_3.wav` | a low amused chuckle (no words) |
| V4 | `tod_spin_vo_common_1.wav` | "Hm. Next time." |
| V5 | `tod_spin_vo_common_2.wav` | a short unimpressed "tch" (no words) |
| V6 | `tod_spin_vo_epic_1.wav` | "Ooh... now that's nice." |
| V7 | `tod_spin_vo_epic_2.wav` | "Well, well." |
| V8 | `tod_spin_vo_legendary_1.wav` | "JACKPOT!" followed by a delighted laugh |
| V9 | `tod_spin_vo_legendary_2.wav` | a long, gleeful, slightly unhinged laugh |
| V10 | `tod_spin_vo_close.wav` | "Come back soon..." |

## Delivery checklist
- [ ] 20 files (C1-C7, M1-M13), plus V1-V10 if you make the voice; names EXACTLY as the tables
- [ ] every file WAV, 16-bit, 48000 Hz, stereo; peak at or below -1 dBFS; sound starts at sample 0
- [ ] C1-C4 played back to back sound like one rising ladder; C5 does not annoy on repeat
- [ ] M5-M7 are tight enough to play 10 times a second; M8 is at one pitch with a clean tail
- [ ] loudness sits with `tod_super_sting.wav`
- [ ] zip them flat (no folders)

## Do NOT
- add silence at the start of any file
- make the short sounds (M5-M8) longer than the table says
- use music or melodies that are copyrighted, or recognisable samples from other games
- bake reverb tails that run past the lengths above
<!-- PACK:END -->
