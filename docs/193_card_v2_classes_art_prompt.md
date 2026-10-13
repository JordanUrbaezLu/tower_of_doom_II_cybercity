<!-- art-pack
name: card_v2_classes
refs:
  docs/193_ref/finished_card_example_legendary.png | HOW AN ILLUSTRATION SITS IN THE FINISHED CARD (real game layers; the game writes the title, band, lines and dots). Attach to EVERY prompt.
  docs/193_ref/finished_card_example_epic.png | the same card at EPIC rarity. Attach to EVERY prompt.
  docs/193_ref/illustration_guide_576x448.png | THE SAFE ZONES: red = 24 px edge margin (no detail), yellow + circle = the crest corner (no subject), green = where the subject lives. Attach to EVERY prompt.
  i_tod_card2_art_luck.png | STYLE TARGET 1 (an approved illustration): chunky dark outlines, bold simple subject, deep blue starfield window, soft neon rim light. Attach to EVERY prompt.
  i_tod_card2_art_retriever.png | STYLE TARGET 2 (approved). Attach to EVERY prompt.
  i_tod_card2_art_piercing.png | STYLE TARGET 3 (approved): how zombies are drawn. Attach to prompts that show zombies.
  i_tod_card2_art_tier_assault_3.png | STYLE TARGET 4 (approved): how a WEAPON is drawn for a tier card. Attach to the six tier prompts.
  i_tod_card_class_necromancer.png | the NECROMANCER's look (skull staff, green soul light). Attach to every Necromancer prompt.
  i_tod_card_tier_necromancer_2.png | the current Necromancer TIER 2 card: SOUL HOUNDS. Attach to N7.
  i_tod_card_tier_necromancer_3.png | the current Necromancer TIER 3 card: THE MANGLER. Attach to N8.
  i_tod_card_summoning_power_regular.png | current SUMMONING POWER card: keep its subject. Attach to N4.
  i_tod_card_soul_bomb_regular.png | current SOUL PULSE card (it was called SOUL BOMB): keep its subject. Attach to N6.
  i_tod_card_soul_beam_regular.png | current SOUL SUCK card (it was called SOUL BEAM): keep its subject. Attach to N5 and N1.
  i_tod_card_class_heavy.png | the BREACHER's look (shotguns, explosives, red accents). Attach to every Breacher prompt.
  i_tod_card_tier_heavy_2.png | the current Breacher TIER 2 card: REMINGTON 870. Attach to B7.
  i_tod_card_tier_heavy_3.png | the current Breacher TIER 3 card: PEACEKEEPER. Attach to B8.
  i_tod_card_adrenaline_regular.png | current ADRENALINE card: keep its subject. Attach to B1.
  i_tod_card_riot_shield_regular.png | current RIOT SHIELD card: keep its subject. Attach to B3.
  i_tod_card_sticky_c4_regular.png | current STICKY C4 card: keep its subject. Attach to B5.
  i_tod_card_cluster_regular.png | current CLUSTER card: keep its subject. Attach to B6.
  i_tod_card_class_slasher.png | the WARRIOR's look (blades, gauntlet, purple accents). Attach to every Warrior prompt.
  i_tod_card_tier_slasher_2.png | the current Warrior TIER 2 card: GAUNTLET OF SIEGFRIED. Attach to W7.
  i_tod_card_tier_slasher_3.png | the current Warrior TIER 3 card: the sword (now the CYBER SWORD). Attach to W8.
  i_tod_card_bash_regular.png | current BASH card: keep its subject. Attach to W5.
  i_tod_card_gravity_smash_regular.png | current CYBER SMASH card (it was called GRAVITY SMASH): keep its subject. Attach to W6.
  i_tod_card_vitality_regular.png | current VITALITY card: keep its subject. Attach to W3.
  i_tod_card_cleave_regular.png | current CLEAVE card: keep its subject. Attach to W4.
preview: 176x136 264x204
-->

# 193 — Card v2 illustrations for the NECROMANCER, BREACHER and WARRIOR (art request)

STATUS: INSTALLED 2026-09-29 12:25 (the user's drop, all 24 illustrations, 0 layout warnings) by `tools/card_pull/install_card_art.py`: every live class now deals the layered cards ("layered-card classes: assault, heavy, necromancer, slasher"). Face lines in tod_upgrade.lua DOMAIN; the tier card says CARDS KEPT - PACK IT AGAIN. Zip of the request: `~/Downloads/tod_card_v2_classes_art_pack.zip`.

Repo side (not in the pack): docs/191 made the layered card and gave the ARCHER every card
(installed 2026-09-29 10:27). Card v2 is PER CLASS: a class draws its cards as layered cards
only when every card it can be dealt has its illustration (tools/card_pull/install_card_art.py
reads the list from the game script). The body, the four rarity frames, the crests, the back,
the banner and the three shared illustrations (DMG REDUCTION / LUCK / BOUNTY) are already
installed, so each remaining class needs only its 6 card illustrations + its tier 2 and tier 3
weapon = 24 files. When this lands:
1. `-Inspect` it, LOOK at every image; `render_pull.py --art-dir <unzipped> --class N` previews
   a class's deal before installing (1 Necromancer, 3 Breacher, 4 Warrior).
2. Copy the PNGs into `source_data/tod_ui_images/_images/`, run
   `python tools/card_pull/install_card_art.py` (ART_SLUGS / TIER_ART already carry these names).
   It lists each class it completes; a class with a missing file keeps the old cards.
3. Write each new card's two short face lines (tod_upgrade.lua DOMAIN `face`), render, FULL build.
The old baked faces of these classes carry stale numbers (LUCK "+10%", etc.); they retire
with this drop, class by class.

<!-- PACK:BEGIN -->
# Card v2: the illustrations for three more classes

## What this is for
Our zombies game shows upgrade cards. Each card is built by the game from layers: a dark card
body with a picture WINDOW, a rarity frame (silver, blue, purple or gold), a round rarity gem
in the window's bottom-right corner, and text the game writes itself. The frames, gems and
body are done. This pack is ONLY the pictures that sit in the window: 24 illustrations, one
per card, for three character classes (the NECROMANCER, the BREACHER and the WARRIOR).

The look is already set: the four `STYLE TARGET` references are approved illustrations for a
fourth class. Match them exactly: same line weight, same colours, same starfield window, same
level of detail. `finished_card_example_legendary.png` and `finished_card_example_epic.png`
show a finished card, so you can see how small the picture is and what covers its corner.

## Deliverables: 24 PNGs, exactly 576 x 448, RGBA, fully opaque

| # | File | Card | Subject |
|---|---|---|---|
| N1 | `i_tod_card2_art_reapers_reach.png` | REAPER'S REACH | The Necromancer's skull staff firing its soul beam an extra-long way across the whole picture, the beam's far end splitting wide, a tiny zombie hit far away. The idea: a longer, wider beam. |
| N2 | `i_tod_card2_art_cloak.png` | INVISIBILITY CLOAK | A hooded figure half faded into shimmering see-through light, two zombies nearby with question marks, looking the wrong way. The idea: enemies lose you. |
| N3 | `i_tod_card2_art_summoner_master.png` | SUMMONER MASTER | A dark summoned helper (a hunched shadow thrall with green eyes) striking a zombie, and a glowing green heart above it growing bigger with a "+" spark. The idea: your helpers' kills raise your max health. |
| N4 | `i_tod_card2_art_summoning_power.png` | SUMMONING POWER | Keep the current card's subject: a glowing green summoning circle with dark helper silhouettes and a spectral hound rising from it. |
| N5 | `i_tod_card2_art_soul_suck.png` | SOUL SUCK | Keep the current SOUL BEAM card's subject: the skull staff drawing glowing white soul wisps out of zombies in a beam. |
| N6 | `i_tod_card2_art_soul_pulse.png` | SOUL PULSE | Keep the current SOUL BOMB card's subject: the skull at the centre of an expanding ring of white soul energy. |
| N7 | `i_tod_card2_art_tier_necromancer_2.png` | NECROMANCER TIER 2 | SOUL HOUNDS: two spectral green-flamed hounds bounding out of the skull staff's glow. |
| N8 | `i_tod_card2_art_tier_necromancer_3.png` | NECROMANCER TIER 3 | THE MANGLER: a hulking black robot-zombie brute with a glowing arm cannon, green soul light in its eyes (it fights FOR the player). |
| B1 | `i_tod_card2_art_adrenaline.png` | ADRENALINE | Keep the current card's subject: glowing speed chevrons bursting out of an explosion with three small skulls (quick explosive kills = a burst of speed). |
| B2 | `i_tod_card2_art_explosive_fusion.png` | EXPLOSIVE FUSION | An orange explosion with a bright green healing cross in its core, and a small figure launched high into the air above it. The idea: your own blasts heal you and launch you. |
| B3 | `i_tod_card2_art_riot_shield.png` | RIOT SHIELD | Keep the current card's subject: a big white riot shield with an orange stripe, bullets bouncing off it. |
| B4 | `i_tod_card2_art_buckshot.png` | BUCKSHOT | A pump shotgun's muzzle blast throwing a wide cone of glowing pellets. The idea: your shotguns hit harder. |
| B5 | `i_tod_card2_art_sticky_c4.png` | STICKY C4 | Keep the current card's subject: a C4 charge with a blinking red light and its detonator. |
| B6 | `i_tod_card2_art_cluster.png` | CLUSTER | Keep the current card's subject: a canister bursting open into a spray of small glowing bomblets. |
| B7 | `i_tod_card2_art_tier_heavy_2.png` | BREACHER TIER 2 | The REMINGTON 870 pump shotgun, three-quarter view, red accents. |
| B8 | `i_tod_card2_art_tier_heavy_3.png` | BREACHER TIER 3 | The PEACEKEEPER: a heavy sci-fi energy shotgun with a glowing red-pink core, three-quarter view. |
| W1 | `i_tod_card2_art_arms_specialist.png` | ARMS SPECIALIST | A glowing gold blade and a spiked armoured gauntlet crossed, crackling with power. The idea: your blades hit harder and reach further. |
| W2 | `i_tod_card2_art_demon_slayer.png` | DEMON SLAYER | A sword cleaving through a big horned red demon skull, a red speed aura trailing the blade. The idea: killing an elite powers you up. |
| W3 | `i_tod_card2_art_vitality.png` | VITALITY | Keep the current card's subject: an armoured warrior figure with a big glowing red heart and a long health bar. |
| W4 | `i_tod_card2_art_cleave.png` | CLEAVE | Keep the current card's subject: one wide glowing sword arc sweeping through three zombies at once. |
| W5 | `i_tod_card2_art_bash.png` | BASH | Keep the current card's subject: an armoured fist or blade dashing forward with speed streaks and an impact star. |
| W6 | `i_tod_card2_art_cyber_smash.png` | CYBER SMASH | Keep the current card's subject: two glowing spikes slamming into the ground, a purple shockwave ring bursting out. |
| W7 | `i_tod_card2_art_tier_slasher_2.png` | WARRIOR TIER 2 | The GAUNTLET OF SIEGFRIED: a spiked golden dragon gauntlet, three-quarter view. |
| W8 | `i_tod_card2_art_tier_slasher_3.png` | WARRIOR TIER 3 | The CYBER SWORD: a big gold battle sword with glowing cyan circuit lines in the blade, three-quarter view. |

## Hard rules
1. Exactly **576 x 448**, PNG, RGBA, **fully opaque** (full bleed: the starfield fills the whole
   image, no transparent edges, no border).
2. **No text, no numbers, no letters** anywhere. The game writes every word.
3. **Keep the bottom-right 150 x 150 corner free of the subject** (the round rarity gem covers
   it: the yellow zone and circle in `illustration_guide_576x448.png`). Starfield only there.
4. Keep a **24 px margin** on every side free of important detail (the red band in the guide):
   the window's bevel covers it.
5. The subject is **big, centred in the green box, and readable when the image is shown at
   176 x 136** (see `preview_onscreen_176x136/`). One clear idea per card; nothing fussy.
6. **Match the style targets exactly**: chunky dark outlines, flat bold colours with one soft
   highlight, a deep blue starfield background with a few sparkles and soft blue nebula shapes,
   a soft neon rim light on the subject.
7. Each class keeps its own accent colour on its own subjects: NECROMANCER green souls, white
   wisps, bone skulls; BREACHER orange fire and red accents; WARRIOR gold metal and purple
   energy. The window background stays the same deep blue for everyone.
8. Where the table says **"keep the current card's subject"**, redraw that SAME subject (attach
   its reference) in the new style and the new 576 x 448 shape. Do not copy the old card's
   frame, title or text.

## Which references to attach
- **Every prompt:** `finished_card_example_legendary.png`, `finished_card_example_epic.png`,
  `illustration_guide_576x448.png`, `i_tod_card2_art_luck.png`, `i_tod_card2_art_retriever.png`;
  add `i_tod_card2_art_piercing.png` when the subject shows zombies, and
  `i_tod_card2_art_tier_assault_3.png` for the six tier weapons (N7, N8, B7, B8, W7, W8).
- **Necromancer (N1-N8):** `i_tod_card_class_necromancer.png`; N1 and N5 `i_tod_card_soul_beam_regular.png`;
  N4 `i_tod_card_summoning_power_regular.png`; N6 `i_tod_card_soul_bomb_regular.png`;
  N7 `i_tod_card_tier_necromancer_2.png`; N8 `i_tod_card_tier_necromancer_3.png`.
- **Breacher (B1-B8):** `i_tod_card_class_heavy.png`; B1 `i_tod_card_adrenaline_regular.png`;
  B3 `i_tod_card_riot_shield_regular.png`; B5 `i_tod_card_sticky_c4_regular.png`; B6 `i_tod_card_cluster_regular.png`;
  B7 `i_tod_card_tier_heavy_2.png`; B8 `i_tod_card_tier_heavy_3.png`.
- **Warrior (W1-W8):** `i_tod_card_class_slasher.png`; W3 `i_tod_card_vitality_regular.png`;
  W4 `i_tod_card_cleave_regular.png`; W5 `i_tod_card_bash_regular.png`; W6 `i_tod_card_gravity_smash_regular.png`;
  W7 `i_tod_card_tier_slasher_2.png`; W8 `i_tod_card_tier_slasher_3.png`.

The old cards' words and numbers are out of date (and their small weapon names under the class
name are wrong now): take only the SUBJECT from them.

## Prompt (one per file; attach the files listed above for that file)
"An illustration for a collectible game card, 576x448, full bleed, fully opaque. In the exact
style of the attached STYLE TARGET images: chunky dark outlines, bold simple readable subject,
deep blue starfield background with a few sparkles and soft nebula shapes, a soft neon rim light.
Subject: <the table's Subject>. Big and centred; the bottom-right 150x150 corner shows only the
starfield; nothing important within 24 px of the edges. No text, no letters, no numbers."

## Delivery checklist
- [ ] 24 PNGs, names EXACTLY as the table, 576 x 448, RGBA, fully opaque
- [ ] no text anywhere; the bottom-right 150 x 150 corner is starfield only
- [ ] every subject reads at 176 x 136 (check the preview folder's size)
- [ ] the style matches the four STYLE TARGETs side by side
- [ ] zip them flat (no folders)

## Do NOT
- add frames, borders, titles, rarity words, gems or dots (the game draws all of those)
- use a different background colour per class
- put the subject in the bottom-right corner
- deliver any size other than 576 x 448
<!-- PACK:END -->
