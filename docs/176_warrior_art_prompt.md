# 176 — WARRIOR: the complete art request (everything the class still draws as text or a stand-in)

<!-- art-pack
name: warrior
refs:
  art/class_theme/theme_b_fallen/warrior/_overview_warrior.png | THE CLASS-CARD STYLE MASTER. The approved Warrior set in the FALLEN / BLACKOUT theme. The two class-card re-bakes (1e) must match it. NOT the style for the upgrade cards or plates.
  i_tod_card_class_slasher.png | RE-BAKE SOURCE. The shipped Warrior draft card (FALLEN / BLACKOUT). Keep everything; only its weapon art and weapon name change.
  i_tod_card_tier_slasher_2.png | RE-BAKE SOURCE. The shipped Warrior tier 2 card. Its weapon art and weapon name are out of date.
  i_tod_card_tier_slasher_3.png | APPROVED Warrior tier 3 card (NOT a deliverable). The GOLD BATTLE SWORD drawn here is the real tier 3 weapon; match its rendering for the two re-baked class-card weapons.
  i_tod_card_knife_speed_regular.png | THE UPGRADE-CARD CHASSIS at REGULAR, on a WARRIOR-ONLY card: copy this frame exactly. Its lavender swoosh is the Warrior's card ACCENT colour - sample it from the image.
  i_tod_card_damage_regular.png | The same chassis at REGULAR on a card with THREE pip sockets (1 lit) - the pip row the two new cards use.
  i_tod_card_damage_super.png | The chassis at SUPER: purple rails, ribbon and outer glow, gold medal, 2 of 3 pips lit.
  i_tod_card_damage_ultimate.png | The chassis at ULTIMATE: gold border, rails, ribbon and glow, sparkles, 3 of 3 pips lit.
  i_tod_pause_r18.png | THE PAUSE-PLATE CHASSIS, 300x44 (KNIFE SPEED, the Warrior's own plate): the pill, the cyan tab and the lettering to copy exactly with new words.
  i_tod_pause_r45.png | A second plate (RIOT SHIELD) showing a two-word name at this size - judge GRAVITY SMASH's fit against it.
  i_tod_hud_gun_blade.png | HUD WEAPON ICON STYLE - the shipped knife cell. Steel-white face, one blue-grey shade, heavy near-black outline.
  i_tod_hud_gun_katana.png | HUD WEAPON ICON STYLE - the shipped katana cell.
  i_tod_hud_gun_axe.png | HUD WEAPON ICON STYLE - the shipped axe cell. The tier 3 sword borrows it today; the new sword cell replaces that borrowing.
  docs/99_hud_ref/art_direction_board.png | The art direction for every HUD icon: palette, the six rules, good and bad examples.
  i_tod_hud_off_frag.png | ABILITY ICON STYLE - a shipped ability icon (a grenade).
  i_tod_hud_off_blink.png | ABILITY ICON STYLE - a shipped ability icon (a dash chevron). BASH borrows it today.
  i_tod_hud_offhand_tile.png | The tile the two ability icons sit inside. Not a deliverable - it shows the box and the dark plate they must read against.
  docs/176_warrior_ref/t7_hud_mp_weapon_hero_gravityspikes_available.png | SUBJECT ONLY - what the Gravity Spikes look like (two heavy spiked pylons). Do not copy its rendering style.
preview: 186x279 234x351 144x66 24x24
-->

> **STATUS: SHIPPED in BUILD 6 - FULL BUILD OK 2026-09-26 13:33:44 Eastern (lead; tmp/lead_build/build6b.log,
> FF 189,722,752 B).** Verified independently: all 15 images (6 cards, 2 plates, 3 gun cells, 2 kit tiles,
> 2 class cards) are in the linker's assetinfo ledger at 13:33:44; repo = deployed for the GDT, the PNGs, the
> zone and both Lua files. UNPLAYED.
>
> Was: **STATUS: INSTALLED IN THE TREE 2026-09-26 (lead's go), NOT BUILT - rides the lead's ART build 6.**
> 15 PNGs into `_images/` (2 replace the class / tier-2 cards in place), 13 image blocks in
> tod_ui_images.gdt, 13 zone lines, `CARD_SLUG[62/63]`, `DARK_NONE` 62/63, AetheriumLoadout
> cats fist / gauntlet / greatsword (+ TOD_NO_MAG) and `CLASS_KITS[1].imgs`. The r62/r63 plates
> draw once the lead raises PAUSE_PLATE_MAX past 63. USER CALL: the baked sidearm line stays for
> this test round; one combined re-bake without it comes later for all four classes.
>
> Was: **STATUS: DROP RECEIVED 2026-09-26 12:39** (`files - 2026-09-26T123917.860.zip`), all 17 at the
> right names/sizes, text proofread, icons checked at 144x66 and 24x24; STAGED in
> `art/warrior_art/drop_20260926_1239/` for the lead's batched ART build 6 (not installed).
> Known: the two re-baked class cards still name a sidearm (AMP63 / UDM 45) and the shipped
> tier 3 names RK7 GARRISON; secondaries were retired for every class the same day.
>
> Was: **STATUS: REQUESTED 2026-09-26** (user, via the lead: *"zip up whatever is remaining
> for each class in its own zip"*). Supersedes this doc's first version (the two HUD
> gun cells only). Pack: `~/Downloads/tod_warrior_art_pack.zip`.

## What is missing today (read from source 2026-09-26)

| Piece | Today | Deliverable |
|---|---|---|
| BASH card (id 62) | text-only card, no `CARD_SLUG` | `i_tod_card_bash_{regular,super,ultimate}` |
| GRAVITY SMASH card (id 63) | text-only card | `i_tod_card_gravity_smash_{regular,super,ultimate}` |
| Pause rows 62 / 63 | text rows (above `PAUSE_PLATE_MAX`) | `i_tod_pause_r62`, `i_tod_pause_r63` |
| T1 HUD gun cell | borrows the KNIFE cell (`cc_punch` -> "blade") | `i_tod_hud_gun_fist` |
| T2 HUD gun cell | borrows the KATANA cell | `i_tod_hud_gun_gauntlet` |
| T3 HUD gun cell | borrows the Stormbreaker AXE cell | `i_tod_hud_gun_greatsword` |
| BASH kit tile | borrows the Mage's BLINK icon | `i_tod_hud_off_bash` |
| SMASH kit tile | NO image, draws the word "SMASH" | `i_tod_hud_off_smash` |
| Draft card | says GOLD TWIN KNIVES, draws two knives | re-bake `i_tod_card_class_slasher` |
| Tier 2 card | says GOLD SWORD, draws a sword | re-bake `i_tod_card_tier_slasher_2` |

Kept: tier 3 card (Gold Battle Sword / RK7 Garrison, still true), glyph, medallion and
name plate (they name no weapon). No DARK cards: both domains are `set_no_dark`. Pips:
three sockets, 1/2/3 lit (the lead's max-8 convention, 2026-09-26, after docs/33).

**Two design calls, both settled by the lead for all four class packs:**
1. The new UPGRADE cards and pause plates use the SHIPPED upgrade-card chassis (docs/82's
   template + rarity ladder), NOT Theme B. LEAD'S RULING 2026-09-26: a deal shows two or
   three classes' cards side by side and the Archer / Breacher / Necromancer packs are all
   on the shipped chassis. Theme B is the class-identity set only (class card, tier cards,
   glyph, medallion, plate); "same pattern as the class assets" = one pack per class.
   Card accent = the Warrior's lavender, sampled from the KNIFE SPEED card's swoosh
   (~`#A090F0`; the blue behind it is the art window, not the accent).
2. HUD icons stay in the HUD set's style, not Theme B (docs/124: a HUD icon is briefed
   against the HUD set it joins). docs/176 v1 described them as "pure white with no
   outline"; the shipped cells have a heavy dark outline and a blue-grey shade, and that
   is what this version asks for.

## Install (when the drop lands)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`; look at all 17, proofread every
   word against the tables below, check the icons at 24x24 and 144x66, and the new cards beside KNIFE SPEED.
2. Copy into `source_data/tod_ui_images/_images/`. The two re-bakes keep their names (no
   wiring). Every other file is a NEW name: an image block in the right UI GDT (copy a
   sibling block: card / pause / gun cell / offhand), an `image,` zone line each.
3. Wiring: `tod_upgrade.lua` `CARD_SLUG[62] = "bash"`, `[63] = "gravity_smash"`; the lead
   raises `PAUSE_PLATE_MAX` past 63 in one edit (all four classes' plates). In
   `AetheriumLoadout.lua`: `cc_punch` -> "fist", `cc_gauntlet` -> "gauntlet",
   `cc_gold_sword` -> "greatsword", the six display-name rows likewise, all three in
   `TOD_NO_MAG`; `CLASS_KITS[1].imgs = { "i_tod_hud_off_bash", "i_tod_hud_off_smash" }`.
   Add 62 and 63 to `DARK_NONE` in `tod_upgrade.lua` (the mirror of `set_no_dark`), or
   the dark-card registration names two images that do not exist.
   The lint (GATE A) must stay green: never name an image before its zone line exists.
4. FULL build; proof = fresh content-hash `.iwi`s beside an untouched control.

<!-- PACK:BEGIN -->
# TOWER OF DOOM II — the WARRIOR class: upgrade cards, plates, HUD icons, two class cards

**17 PNG files.** The Warrior is one of the game's playable classes. Its art is partly
missing: two upgrades have no card, three weapons and two abilities have no HUD icon, and
two class cards show weapons the class no longer carries. This pack fills every gap.

**Consistency with the reference images is the whole job.** Every file joins a set that
is already in the game, and there are THREE different sets in this pack. Keep them apart:

| Deliverables | Joins this set | Match these references |
|---|---|---|
| 1a upgrade cards, 1b pause plates | the UPGRADE DECK (bright navy cartoon cards) | `i_tod_card_knife_speed_regular.png`, the three `i_tod_card_damage_*`, `i_tod_pause_r18.png` |
| 1c weapon icons, 1d ability icons | the in-game HUD icons | the `i_tod_hud_*` files + `art_direction_board.png` |
| 1e class-card re-bakes | the CLASS cards, **FALLEN / BLACKOUT** theme | `_overview_warrior.png`, the three `i_tod_card_*slasher*` |

Do not carry one set's look into another: no black steel on an upgrade card, no navy
cartoon frame on a class card, no card styling on a HUD icon.

---

## 0. Who the WARRIOR is

A melee fighter. Everything is up close. Its weapon changes as it ranks up:

| Tier | Weapon | What it is |
|---|---|---|
| 1 | **ONE INCH PUNCH** | bare fists, wrapped hands, devastating short punches |
| 2 | **GAUNTLET OF SIEGFRIED** | a heavy armoured dragon gauntlet over the right forearm: dark iron plates, dragon-scale fingers, clawed fingertips, a segmented cuff |
| 3 | **GOLD BATTLE SWORD** | the big gold sword on `reference/i_tod_card_tier_slasher_3.png` |

Two abilities:
- **BASH** — the Warrior dashes forward and slams whatever is in front of it.
- **GRAVITY SMASH** — the Warrior leaps and drives two heavy spiked pylons (the "gravity
  spikes", see `reference/t7_hud_mp_weapon_hero_gravityspikes_available.png` for the
  object) into the ground; a shockwave ring blasts every zombie around it.

Class colour: **VIOLET `#BF73FF`** on the class cards (1e) and the ability icons (1d).
On the upgrade cards (1a) the Warrior's accent is the lighter **lavender** of the KNIFE
SPEED card (section 3).

---

## 1. Deliverables

### 1a. Two NEW upgrade cards — 768 x 1152, three rarities each (6 files)

| Upgrade | Regular | Super | Ultimate |
|---|---|---|---|
| BASH | `i_tod_card_bash_regular.png` | `i_tod_card_bash_super.png` | `i_tod_card_bash_ultimate.png` |
| GRAVITY SMASH | `i_tod_card_gravity_smash_regular.png` | `i_tod_card_gravity_smash_super.png` | `i_tod_card_gravity_smash_ultimate.png` |

### 1b. Two pause-menu plates — 300 x 44 (2 files)

| File | Word on it |
|---|---|
| `i_tod_pause_r62.png` | `BASH` |
| `i_tod_pause_r63.png` | `GRAVITY SMASH` |

### 1c. Three HUD weapon icons — 288 x 132 (3 files)

| File | Weapon |
|---|---|
| `i_tod_hud_gun_fist.png` | ONE INCH PUNCH — a clenched fist |
| `i_tod_hud_gun_gauntlet.png` | GAUNTLET OF SIEGFRIED — the armoured gauntlet |
| `i_tod_hud_gun_greatsword.png` | GOLD BATTLE SWORD — the big sword |

### 1d. Two ability icons — 128 x 128 (2 files)

| File | Ability |
|---|---|
| `i_tod_hud_off_bash.png` | BASH |
| `i_tod_hud_off_smash.png` | GRAVITY SMASH |

### 1e. Two RE-BAKED class cards — 768 x 1152 (2 files, same names as in `reference/`)

| File | What changes |
|---|---|
| `i_tod_card_class_slasher.png` | weapon art + weapon name (section 6) |
| `i_tod_card_tier_slasher_2.png` | weapon art + weapon name (section 6) |

Exact filenames, exact pixel sizes, PNG with alpha. **17 total.** Plus, for choosing
only, one `_overview_warrior_new.png` showing all 17 together.

---

## 2. The reference folder

`reference/` holds every shipped file this pack sits beside. `preview_onscreen_*/` holds
them shrunk to the size a player actually sees — **that is the real test**:
`186x279` draft card, `234x351` upgrade + tier cards, `144x66` weapon
icons, `24x24` ability icons. A detail that vanishes there does not exist.

---

## 3. The two upgrade cards (1a) — the SHIPPED upgrade-card chassis

These are dealt beside other upgrade cards, often from other classes, so their frame must
be indistinguishable from the cards already in the game.

**Frame:** copy `reference/i_tod_card_knife_speed_regular.png` exactly: the rounded navy
chassis with a thick outer border and a screw head in each corner, the gold title band
with seven small dots along its top edge, the scanlined navy art window, the round star
medal overlapping the art window's bottom-right corner, the rarity capsule with chevrons
at each end, the recessed description panel with its outlined box, the thin vertical rail
inside each side edge.

**Pip row:** **THREE** round sockets along the bottom, exactly as on
`reference/i_tod_card_damage_regular.png` (not the five on the KNIFE SPEED card).

**Rarity ladder**: read the exact values off the three DAMAGE references.

| | REGULAR | SUPER | ULTIMATE |
|---|---|---|---|
| Chassis / rails | navy, cyan rails | navy, purple rails, soft purple outer glow | black with a gold border, gold rails, warm gold outer glow |
| Rarity capsule | silver, `REGULAR +1` | purple, `SUPER +2` | orange-gold, `ULTIMATE +3` |
| Medal | silver ring and star | gold | gold |
| Description text | light grey in a teal-outlined box | purple | gold in a gold-outlined box |
| Pips lit | 1 of 3 | 2 of 3 | 3 of 3, gold |
| Extra | none | none | small gold chevrons and sparkles in the art window and margin |

**The Warrior's ACCENT colour** is the lavender of the speed swoosh on the KNIFE SPEED
card (about `#A090F0`; sample it from the image). Use it in each illustration the way
that card does: on the motion trails and energy, never on the frame.

**Draw each illustration ONCE and reuse it pixel-identical in all three rarities.** Only
the dressing in the table above changes.

### 3a. NO NUMBERS

No number, percentage, level or time anywhere on a card except the rarity plate's
`+1 / +2 / +3`. The game shows the values live; a baked number goes stale.

### 3b. The two subjects

Render exactly like the knife on `reference/i_tod_card_knife_speed_regular.png`: bold
flat vector-cartoon shapes, strong dark outlines, bright rim light, the lavender accent on
the motion, one central object filling the art window.

**BASH** — title `BASH`. A clenched fist in a steel-banded hand wrap driving **left to
right**, knuckles first, with three or four hard lavender speed streaks trailing behind it and a small impact
starburst just ahead of the knuckles. It must read as *charging forward and hitting*.
Description (two lines): `HARDER HITS` / `FASTER RECHARGE`.

**GRAVITY SMASH** — title `GRAVITY SMASH`. Two heavy steel-and-gold spiked pylons (the
object in `reference/t7_hud_mp_weapon_hero_gravityspikes_available.png`) driven point-down
into cracked ground, with a flat lavender shockwave RING spreading out from them across the
floor and debris flying. It must read as *a slam that hits everything around you*.
Description (two lines): `BIGGER SLAM` / `SHORTER COOLDOWN`.

---

## 4. The two pause plates (1b)

Match `reference/i_tod_pause_r18.png` (KNIFE SPEED, the Warrior's own plate) **exactly**:
the same dark navy pill, the same bright cyan tab at the left end, the same heavy white
lettering with its dark outline, the same padding. Only the words change: `BASH` and
`GRAVITY SMASH`. `reference/i_tod_pause_r45.png` shows a two-word name at this size; if
GRAVITY SMASH does not fit, tighten the letter spacing, never shrink the cap height or
move the tab.

---

## 5. The HUD icons (1c, 1d) — the HUD set's style, not a card style

These sit in the in-game HUD beside ~30 existing icons. Match those, not the cards.
Read `reference/art_direction_board.png` (the six rules).

### 5a. Weapon icons, 288 x 132 (1c)

Match `reference/i_tod_hud_gun_blade.png`, `_katana.png`, `_axe.png` exactly:
- a **steel-white face** (`#E8EEF6`), **one blue-grey shade** for the lower/shadow side,
  and a **heavy near-black outline** (`#0A1020`) round the whole silhouette;
- side-on, facing **RIGHT**, filling most of the width, centred, small margin all round;
- flat: no gradient, no glow, no colour accent, no background, no text.

| File | Drawing |
|---|---|
| `i_tod_hud_gun_fist.png` | a clenched bare fist seen from the side, knuckles pointing right, a short wrapped forearm entering from the left. The raised knuckles are the biggest, clearest feature. |
| `i_tod_hud_gun_gauntlet.png` | the SAME fist pose in an armoured gauntlet: blocky plated fingers ending in short claws, a heavy segmented cuff over the forearm. The claws and the ridged cuff are what tells it apart from the fist. |
| `i_tod_hud_gun_greatsword.png` | the Gold Battle Sword (tier 3 card) as a silhouette: pointing right, broad straight blade with a pointed tip, a heavy crossguard, short grip and round pommel at the left. In steel white like every other cell — the game tints it. |

The three must read as one family: same stroke, same shade, same outline weight. Put
them side by side at 144 x 66 before sending: fist / gauntlet / sword must be three
obviously different shapes.

### 5b. Ability icons, 128 x 128 (1d)

Match `reference/i_tod_hud_off_frag.png` and `reference/i_tod_hud_off_blink.png`: a single
object, a **very heavy dark navy outline**, a pale near-white body, one blue-grey shade,
**one** accent colour (violet `#BF73FF`), flat, transparent background.
`reference/i_tod_hud_offhand_tile.png` is the box they sit in. **They are drawn 24 pixels
square in play** — check `preview_onscreen_24x24/`; two shapes is the budget.

| File | Drawing |
|---|---|
| `i_tod_hud_off_bash.png` | a bold fist pointing right with two thick violet streaks behind it. Fist + streaks, nothing else. Must NOT look like the dash chevron it replaces. |
| `i_tod_hud_off_smash.png` | one thick spike stabbing straight down into a flat violet ring (an ellipse lying on the ground). Spike + ring, nothing else. |

---

## 6. The two class-card re-bakes (1e)

**These are not new cards.** Reproduce each source in `reference/` exactly — chassis,
header, tier number, role line, `WARRIOR` ribbon, pips, rails, hazard stripes, glow,
UNPACKED ribbon on tier 2 — and change ONLY the weapon art and the weapon name. The
sidearm line under the rule stays as it is.

| File | Header | Weapon art | Weapon name | Sidearm (unchanged) |
|---|---|---|---|---|
| `i_tod_card_class_slasher.png` | `TIER 1` | a gold-wrapped clenched fist, side-on, knuckles right | `ONE INCH PUNCH` (two lines if needed: `ONE INCH` / `PUNCH`) | `AMP63` |
| `i_tod_card_tier_slasher_2.png` | `TIER 2` | the GAUNTLET OF SIEGFRIED: dark iron dragon-scale gauntlet with gold trim, clawed fingertips, heavy segmented cuff, a faint ember glow in the knuckle joints; side-on, claws right | `GAUNTLET OF` / `SIEGFRIED` (two lines, like `GOLD BATTLE` / `SWORD` on tier 3) | `UDM 45` |

Same scale, angle and lighting as the sword on the tier 3 card: the three cards are a
set, and fist -> gauntlet -> sword should read as one climb.

---

## 7. Hard rules

1. Exact filenames and sizes (section 1). PNG with alpha.
2. **No numbers on the upgrade cards** except `+1 / +2 / +3`.
3. One illustration per upgrade, identical in all three rarities.
4. Upgrade cards: THREE pip sockets, 1 / 2 / 3 lit.
5. No DARK rarity of anything.
6. The re-bakes change the weapon art and the weapon name only.
7. Three sets, three looks: upgrade cards + plates = the shipped upgrade deck; HUD icons =
   the HUD style; class re-bakes = FALLEN / BLACKOUT. Never mix them.
8. All text in the provided typeface (see TYPOGRAPHY below). No commas, colons or `%`.
9. Check every piece in `preview_onscreen_*/`.
10. No watermark, signature or border of your own.

## 8. Paste-ready prompts

Attach the named `reference/` files to each. Add `typography/` to every prompt that
bakes text.

**A — BASH card, three rarities.** *Attach `i_tod_card_knife_speed_regular.png`,
`i_tod_card_damage_regular.png`, `i_tod_card_damage_super.png`,
`i_tod_card_damage_ultimate.png`.*
> Make one game upgrade card in three rarities, 768x1152 PNG each, transparent outside the
> card. Copy the first attached card's frame exactly (rounded navy chassis with corner
> screws, gold title band with seven dots, scanlined art window, star medal overlapping
> the art window's bottom-right corner, rarity capsule, description panel, side rails)
> but with THREE round pip sockets along the bottom as on the DAMAGE cards. Title `BASH`.
> Description, two lines: `HARDER HITS` / `FASTER RECHARGE`. Illustration, identical in all
> three: a clenched fist in a steel-banded hand wrap driving left to right knuckles first,
> three or four hard lavender speed streaks behind it (the lavender of the first card's
> swoosh), a small impact starburst ahead of the knuckles, bold flat vector-cartoon
> rendering with heavy dark outlines like the knife on the first card. Dress the three
> exactly as the DAMAGE cards do: REGULAR +1 (1 of 3 pips lit), SUPER +2 (purple rails and
> glow, 2 of 3 lit), ULTIMATE +3 (gold border and glow, sparkles, 3 of 3 lit). All text in
> the attached typeface. No numbers except the rarity capsule.

**B — GRAVITY SMASH card, three rarities.** *Same attachments plus
`t7_hud_mp_weapon_hero_gravityspikes_available.png` (the object only).*
> Same frame, pip row and rarity dressing as prompt A. Title `GRAVITY SMASH`. Description,
> two lines: `BIGGER SLAM` / `SHORTER COOLDOWN`. Illustration, identical in all three: two
> heavy steel-and-gold spiked pylons like the attached gravity spikes, driven point-down
> into cracked ground, a flat lavender shockwave ring spreading across the floor around
> them, debris flying.

**C — the two pause plates.** *Attach `i_tod_pause_r18.png`, `i_tod_pause_r45.png`.*
> Match the first attached name plate exactly: same dark navy pill, same bright cyan tab
> at the left end, same heavy white lettering with its dark outline, same padding and
> margins. Make two, 300x44 PNG each, transparent background, reading `BASH` and
> `GRAVITY SMASH`, set in the attached typeface. The second attachment shows a two-word
> name at this size; if GRAVITY SMASH is long, tighten the spacing, never shrink the
> letters or move the tab.

**D — the three weapon icons.** *Attach `i_tod_hud_gun_blade.png`,
`i_tod_hud_gun_katana.png`, `i_tod_hud_gun_axe.png`, `art_direction_board.png`,
`i_tod_card_tier_slasher_3.png` (the sword's shape only).*
> Three HUD weapon icons, 288x132 PNG each, transparent background, in exactly the style
> of the first three attachments: steel-white #E8EEF6 face, one blue-grey shade for the
> lower side, a heavy near-black #0A1020 outline, flat, no glow, no colour, no text,
> side-on facing right, filling most of the width. (1) `i_tod_hud_gun_fist.png`: a
> clenched bare fist from the side, knuckles right, short wrapped forearm from the left,
> big clear knuckles. (2) `i_tod_hud_gun_gauntlet.png`: the same pose in an armoured
> gauntlet, blocky plated fingers with short claws, heavy segmented cuff. (3)
> `i_tod_hud_gun_greatsword.png`: the gold battle sword from the last attachment as a
> silhouette, pointing right, broad straight blade, heavy crossguard, short grip, round
> pommel. All three share stroke, shade and outline weight.

**E — the two ability icons.** *Attach `i_tod_hud_off_frag.png`,
`i_tod_hud_off_blink.png`, `i_tod_hud_offhand_tile.png`.*
> Two ability icons, 128x128 PNG each, transparent background, matching the first two
> attachments: very heavy dark navy outline, pale near-white body, one blue-grey shade,
> one violet #BF73FF accent, flat, no gradient or glow, readable at 24x24 pixels.
> (1) `i_tod_hud_off_bash.png`: a bold fist pointing right with two thick violet streaks
> behind it. (2) `i_tod_hud_off_smash.png`: one thick spike stabbing straight down into a
> flat violet ring lying on the ground. Two shapes each, nothing else.

**F — the two class-card re-bakes.** *Attach `i_tod_card_class_slasher.png`,
`i_tod_card_tier_slasher_2.png`, `i_tod_card_tier_slasher_3.png`.*
> Reproduce the first two attached cards exactly, 768x1152 PNG, same names, changing ONLY
> the weapon illustration and the weapon name. (1) The TIER 1 card: a gold-wrapped
> clenched fist, side-on, knuckles right; name `ONE INCH PUNCH`; sidearm line stays
> `AMP63`. (2) The TIER 2 card: an armoured dragon-scale gauntlet in dark iron with gold
> trim, clawed fingertips, a heavy segmented cuff, a faint ember glow in the knuckle
> joints, side-on, claws right; name on two lines `GAUNTLET OF` / `SIEGFRIED`; sidearm
> line stays `UDM 45`. Match the scale, angle and lighting of the sword on the third
> attachment. All text in the attached typeface.

## 9. Delivery checklist

- [ ] 17 PNGs, exact names and sizes
- [ ] Upgrade cards: one illustration per upgrade, identical across rarities; three pip
      sockets lit 1 / 2 / 3; no numbers except `+1 / +2 / +3`
- [ ] Every word proofread: BASH, GRAVITY SMASH, HARDER HITS, FASTER RECHARGE, BIGGER
      SLAM, SHORTER COOLDOWN, ONE INCH PUNCH, GAUNTLET OF SIEGFRIED, AMP63, UDM 45
- [ ] All text in the provided typeface
- [ ] Weapon icons match the knife / katana / axe cells; face right; readable at 144x66
- [ ] Ability icons readable at 24x24; BASH does not look like the dash chevron
- [ ] Upgrade cards and plates indistinguishable in frame from KNIFE SPEED / DAMAGE
- [ ] Re-bakes differ from their sources only in weapon art + weapon name
- [ ] One `_overview_warrior_new.png` with all 17

## 10. Do NOT

- Do not draw DARK cards.
- Do not draw the upgrade cards or plates in the black-steel class-card style.
- Do not put any card styling on the HUD icons.
- Do not put colour or glow on the weapon icons.
- Do not change anything on the re-bakes except weapon art and weapon name.
- Do not redraw the tier 3 card, the glyph, the medallion or the name plate.
- Do not use any font but the provided typeface; no lowercase; no commas.
- Do not rename any file.
<!-- PACK:END -->
