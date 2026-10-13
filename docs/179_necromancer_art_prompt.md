# 179 — NECROMANCER: every missing piece of art for the class

<!-- art-pack
name: necromancer
refs:
  art/class_theme/theme_b_fallen/skirmisher/_overview.png | THE STYLE MASTER for the six class pieces (the approved FALLEN / BLACKOUT theme on the old class in this slot). Match it.
  i_tod_card_class_skirmisher.png | APPROVED draft card chassis (theme B). The Necromancer's draft card uses this exact chassis.
  i_tod_card_tier_skirmisher_2.png | APPROVED tier 2 card chassis (amber hazard UNPACKED ribbon, class-colour aura).
  i_tod_card_tier_skirmisher_3.png | APPROVED tier 3 card chassis (red hazard UNPACKED ribbon, stronger aura).
  i_tod_class_skirmisher.png | APPROVED class glyph (theme B). Same treatment, new symbol.
  i_tod_class_medallion_skirmisher.png | APPROVED class medallion (theme B). Same ring, new symbol.
  i_tod_upg_class_skirmisher.png | APPROVED class name plate (theme B). Same plate, new name.
  i_tod_card_damage_regular.png | UPGRADE CARD, a max-10 card: the THREE-socket pip row (first lit) that SOUL BOMB and SUMMONING POWER copy.
  i_tod_card_mage_heal_regular.png | UPGRADE CARD chassis, REGULAR rarity (a class ability card): the FIVE-socket pip row that SOUL BEAM copies.
  i_tod_card_mage_heal_super.png | UPGRADE CARD chassis, SUPER rarity.
  i_tod_card_mage_heal_ultimate.png | UPGRADE CARD chassis, ULTIMATE rarity (gold frame, sparkles).
  i_tod_pause_r18.png | PAUSE-MENU row plate: the exact style for the three new plates.
  i_tod_hud_off_blink.png | ABILITY TILE glyph (shipped): the style, palette and framing for the two new ability glyphs.
  i_tod_hud_off_frag.png | ABILITY TILE glyph (shipped): second example of the same style.
  i_tod_hud_gun_katana.png | HUD WEAPON icon (shipped): the style for the skull's weapon icon.
  docs/99_hud_ref/art_direction_board.png | the art direction for every HUD weapon icon. Attach to the weapon-icon prompt.
preview: 186x279 234x351 213x320 64x56 56x56 280x60 144x66 24x24 300x44
-->

> **STATUS: SHIPPED in build 6 (FULL BUILD OK 2026-09-26 13:33:44, tmp/lead_build/build6b.log). Drop `files - 2026-09-26T125221.075.zip`, all 21 wired; all 21 converted fresh (content-hash .iwi 13:33:34-36) and in the linker ledger; r38 / r39 carry NEW hashes (MH4AYDM5... / W5BZIKZ2..., were BPNBZNMC... / SKEBLGJL...); control i_tod_card_damage_regular untouched (D6TCNNJB..., 2026-09-23). UNPLAYED. REQUESTED 2026-09-26.** The Necromancer replaced the Skirmisher as
> class 1 on 2026-09-26 and has NO art of its own: the draft card, class glyph,
> medallion, name plate and both tier cards draw the text fallback
> (`tod_class_select.lua` / `tod_upgrade.lua` leave slot 1 out); the skull has no
> HUD weapon icon (`AetheriumLoadout.lua` TOD_GUN_CAT has no `tod_necro_skull`
> row); the two ability tiles (SUMMON, SOUL BOMB) draw their names
> (`CLASS_KITS[3]` imgs nil); the three class cards added the same day, SOUL BOMB
> (id 59), SUMMONING POWER (38) and SOUL BEAM (39), have no card art or pause
> plate (no `CARD_SLUG`; 38/39/59 in `CoD.TodTextPlate`). This brief orders all of
> it: **21 files + 1 overview**. The Pack-a-Punch skull CAMO is NOT in it: a camo
> is a texture on the skull model's own UV layout, which a 2-D generator cannot
> author blind (a later material pass; the PaP skull already fires a recoloured
> beam, `fx_necro_pap_beam_*`).

## Install (when the drop lands)

1. `.\tools\make_art_pack.ps1 -Inspect 'files (N).zip'`; look at all 21 at true
   size, proofread every baked word against section 3 of the PACK, lay the
   overview beside the Skirmisher's.
2. Copy into `source_data/tod_ui_images/_images/`. ALL 21 NAMES ARE NEW, so each
   needs a GDT image block (copy a sibling's; cards and class pieces as
   `compressed high color`, not uncompressed — the v19.8 resident-RAM lesson), a
   zone `image,` line, and wiring:
   - **class set:** `tod_class_select.lua` `art.cards[1]` =
     `i_tod_card_class_necromancer`, `art.icons[1]` = `i_tod_class_necromancer`;
     `tod_upgrade.lua` upg-class `[1]` = `i_tod_upg_class_necromancer` and the
     tier-card class table (`TCLS[1]`) = `"necromancer"`; the medallion mapping in
     `AetheriumCharacters.lua` (the necromancer body's `char` slot) =
     `i_tod_class_medallion_necromancer`.
   - **upgrade cards:** `CARD_SLUG[59] = "soul_bomb"`, `[38] = "summoning_power"`,
     `[39] = "soul_beam"` (`tod_upgrade.lua`). No dark cards (all three are
     `set_no_dark`).
   - **pause plates:** r38 / r39 replace the old VITALITY / RECOVERY plates under
     the same names, and r59 is new; zone all three and remove `[38]` / `[39]` /
     `[59]` from `CoD.TodTextPlate` in the SAME edit (ping the lead first:
     `tod_upgrade.lua` is shared). `PAUSE_PLATE_MAX` / `TOD_UPG_PLATE_MAX` are
     already 63 (the lead raised them 2026-09-26 with the Archer art, and put
     `[59]` in TodTextPlate so lint GATE A passes until the plate exists).
   - **ability glyphs:** `AetheriumLoadout.lua` `CLASS_KITS[3].imgs` =
     `{ "i_tod_hud_off_summon", "i_tod_hud_off_soul_bomb" }`.
   - **weapon icon:** `TOD_GUN_CAT[ "tod_necro_skull" ] = "skull"` plus the
     display-name rows (SKULL OF NAN SAPWE / SKULL OF THE DAMNED -> skull), and
     the skull cell in `TOD_NO_MAG` if its meter should not read as a magazine.
3. `node tools/lint_tod_assets.js` (every new name must have a zone line), FULL
   build, prove with fresh content-hash `.iwi`s beside an untouched control. Read
   each draw path after install (memory `art-install-means-wired`). Archive the
   drop in `art/class_theme/theme_b_fallen/necromancer/`. Flip STATUS to SHIPPED.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — the NECROMANCER: all of its art

**21 PNG files + 1 overview.** The Necromancer is a new class. It raises the
dead to fight for it and tears souls out of zombies with a cursed skull. It has
no art yet, so the game shows plain text in its place. This pack is every
missing piece:

- **A. The class set (6):** draft card, tier 2 card, tier 3 card, glyph,
  medallion, name plate, in the FALLEN / BLACKOUT theme.
- **B. Three upgrade cards (9):** SOUL BOMB, SUMMONING POWER, SOUL BEAM, each in
  REGULAR / SUPER / ULTIMATE.
- **C. Three pause-menu plates (3).**
- **D. Two ability glyphs (2):** SUMMON and SOUL BOMB.
- **E. One HUD weapon icon (1):** the skull.

**Consistency is the whole job.** Each group has shipped references in
`reference/`. Every piece must look like it came from the same hand as its
references. Only the subject, the text and (for the class set) the class colour
change.

---

## 1. What is in the zip

- `reference/_overview.png` + the six `*_skirmisher.png` files: the APPROVED
  class-set theme (the class that used to hold this slot). Match chassis,
  materials, scratches, hazard stripes, glow, pips, ribbons, layout and spacing.
  Their TEXT and WEAPONS are the old class's: never copy them.
- `reference/i_tod_card_mage_heal_regular/super/ultimate.png`: the UPGRADE CARD
  chassis in all three rarities. Match it exactly; only the title, the picture
  and the description change.
- `reference/i_tod_pause_r18.png`: the pause plate style.
- `reference/i_tod_hud_off_blink.png`, `i_tod_hud_off_frag.png`: the ability
  glyph style.
- `reference/i_tod_hud_gun_katana.png` + `art_direction_board.png`: the HUD
  weapon icon style.
- `typography/`: the game's own typeface. **All text must be set in it.**
- `preview_onscreen_*/`: the references at their real on-screen sizes.

---

## 2. The subject

**The Necromancer** is a soul reaper. Its weapon is the **SKULL OF NAN SAPWE**:
a heavy, ancient skull held in one hand like a lantern. It is carved bone and
stone, cracked with age, with a hinged jaw and deep eye sockets. Its eyes and
mouth glow, and a beam of pale soul-light pours from its mouth.

**Soul colour** is a cold **BLUE-GREY / pale ice blue** (`#A8C7FF`, wisps fading
to white). Use it for every soul, spirit, aura and beam in the art.

**Class colour** (the theme's "class colour" slot, where the approved references
use cyan) is **SOUL GREEN `#8CFF73`**. It goes on the ribbon text, the
name-plate glow, the pips, the tier aura, the glyph and the medallion ring.
Everything else in the theme (black steel, scratches, hazard stripes, the red
emergency side-rail, the amber tier 2 / red tier 3 UNPACKED ribbons) stays
exactly as on the references.

**Its helpers**, raised from the dead, glow with the blue-grey soul aura:
- tier 1: **THRALLS**, ordinary zombies with white glowing eyes;
- tier 2: **SOUL HOUNDS**, lean hellhound-shaped spirit dogs made of blue-grey
  soul smoke, **never fire**;
- tier 3: **THE MANGLER**, a hulking armoured zombie brute with a heavy cannon
  arm, wreathed in the blue-grey soul aura.

---

## 3. Deliverables

Exact filenames and sizes, PNG with transparency.

### A. Class set (FALLEN / BLACKOUT theme; match the six Skirmisher references)

| file | size | text to bake | art |
|---|---|---|---|
| `i_tod_card_class_necromancer.png` | 768 x 1152 | header **TIER 1** / feature line **SOUL REAPER** / ribbon **NECROMANCER** / big name **SKULL OF NAN SAPWE** alone (NO sidearm line) / 1 pip lit | the skull, side-on, a soul beam pouring from its mouth |
| `i_tod_card_tier_necromancer_2.png` | 768 x 1152 | **TIER 2** / amber **UNPACKED** ribbon / ribbon **NECROMANCER** / **SOUL HOUNDS** alone (NO sidearm line) / 2 pips lit | the skull with two blue-grey soul hounds lunging out of its light |
| `i_tod_card_tier_necromancer_3.png` | 768 x 1152 | **TIER 3** / red **UNPACKED** ribbon / ribbon **NECROMANCER** / **THE MANGLER** alone (NO sidearm line) / 3 pips lit | the skull with the soul-wreathed Mangler rising behind it |
| `i_tod_class_necromancer.png` | 224 x 196 | none | one clean symbol: a skull with soul wisps rising from it (or a raised hand with a spirit above it). Must read at 64 x 56 |
| `i_tod_class_medallion_necromancer.png` | 512 x 512 | none | the glyph's symbol inside the approved medallion ring, ring in SOUL GREEN. Must read at 56 x 56 |
| `i_tod_upg_class_necromancer.png` | 420 x 90 | **CLASS NECROMANCER** | the approved plate, glyph on the left, SOUL GREEN glow |

Tier 2 and tier 3 show the helper as the big name on purpose: the Necromancer
keeps the same skull at every tier, and its promotion upgrades its helpers.

**NO SIDEARM LINE.** The reference cards print a small second weapon name under
the big name (the old sidearm). This class carries no sidearm: leave that line
out entirely and let the big name stand alone, vertically centred in the same
name band. Do not print BULLDOG, SG12, SPAS-12 or any other second weapon.

### B. Upgrade cards (match the three mage_heal references exactly)

Nine files, **768 x 1152** each (drawn at 213 x 320 on screen):
`i_tod_card_<slug>_regular.png`, `_super.png`, `_ultimate.png`. The chassis,
rarity ribbon (**REGULAR +1** / **SUPER +2** / **ULTIMATE +3**), medal and frame
treatment come straight from the references. Only the title, picture, value
line and pip row change.

**Pips:** SOUL BOMB and SUMMONING POWER have **THREE round sockets** (copy the
row on `i_tod_card_damage_regular.png`); SOUL BEAM has **FIVE** (copy the row on
`i_tod_card_mage_heal_regular.png`). On every card: regular **1 lit**, super **2
lit**, ultimate **3 lit**.

**Accent:** these are the Necromancer's own cards, so the illustration's accent
glow is the class colour **SOUL GREEN `#8CFF73`** (sample it from your finished
Necromancer draft card), with the souls themselves blue-grey.

**Value line:** the exact line below, identical on all three rarities, **no
number**.

| slug | title bar | value line (exact) | pips | picture |
|---|---|---|---|---|
| `soul_bomb` | **SOUL BOMB** | **FASTER RECHARGE, WIDER BLAST** | 3 sockets | a shockwave ring of blue-grey souls bursting outward from a glowing skull at the centre, ghostly faces in the wave |
| `summoning_power` | **SUMMONING POWER** | **MORE HELPERS, STRONGER HELPERS** | 3 sockets | three glowing-eyed thralls and a soul hound rising from a ring of blue-grey light in the ground |
| `soul_beam` | **SOUL BEAM** | **FASTER DRAIN, MORE SOULS** | 5 sockets | the skull's beam splitting into several streams, each pulling a wispy soul out of a zombie silhouette |

### C. Pause-menu plates (match `i_tod_pause_r18.png`)

**300 x 44** each, the card title in the plate:

| file | text |
|---|---|
| `i_tod_pause_r38.png` | **SUMMONING POWER** |
| `i_tod_pause_r39.png` | **SOUL BEAM** |
| `i_tod_pause_r59.png` | **SOUL BOMB** |

### D. Ability glyphs (match `i_tod_hud_off_blink.png` / `_frag.png`)

**128 x 128** each, same flat two-tone palette, framing and edge treatment as
the references. Shown on the HUD at about 24 x 24, so one bold shape each.

| file | what it shows |
|---|---|
| `i_tod_hud_off_summon.png` | SUMMON: a zombie hand or a ghostly figure rising out of a glowing ring |
| `i_tod_hud_off_soul_bomb.png` | SOUL BOMB: a small skull at the centre of an expanding burst ring |

### E. HUD weapon icon (match `i_tod_hud_gun_katana.png`)

| file | size | what it shows |
|---|---|---|
| `i_tod_hud_gun_skull.png` | **288 x 132** | the SKULL OF NAN SAPWE side-on, facing RIGHT, as a pure white silhouette with dark cut-lines (the eye socket, the jaw hinge, the cracks), exactly the katana icon's style: white on transparency, no colour, no glow |

### F. Overview

`_overview_necromancer.png`: every piece laid out like the Skirmisher's
`_overview.png`. For choosing only.

---

## 4. Paste-ready prompts

Attach the named `reference/` files to each.

1. **Class set** (attach `_overview.png`, `i_tod_card_class_skirmisher.png`,
   `i_tod_card_tier_skirmisher_2.png`, `i_tod_card_tier_skirmisher_3.png`,
   `i_tod_class_skirmisher.png`, `i_tod_class_medallion_skirmisher.png` and
   `i_tod_upg_class_skirmisher.png`): "Make
   the six class pieces for a NECROMANCER class in exactly the attached FALLEN /
   BLACKOUT theme: same black scratched steel chassis, hazard stripes, red
   emergency side-rail, pips and ribbons. Swap the cyan class colour for soul
   green #8CFF73. The weapon is an ancient carved bone-and-stone skull held like
   a lantern, glowing eyes and mouth, a pale blue-grey soul beam from its mouth.
   Text per the table (NECROMANCER, SOUL REAPER, SKULL OF NAN SAPWE,
   SOUL HOUNDS, THE MANGLER, CLASS NECROMANCER), all in the attached typeface.
   Unlike the references, print NO sidearm name under the big name: no second
   weapon line at all."
2. **Upgrade cards** (attach `i_tod_card_mage_heal_regular.png`,
   `i_tod_card_mage_heal_super.png`, `i_tod_card_mage_heal_ultimate.png` and
   `i_tod_card_damage_regular.png`): "Three new upgrade cards on exactly this card
   chassis, each in regular, super and ultimate like the attached three: SOUL
   BOMB, SUMMONING POWER, SOUL BEAM, with the pictures, value lines and pip rows
   in the table (three sockets on the first two, copied from the damage card;
   five on SOUL BEAM). Accent glow soul green #8CFF73; souls and spirits pale
   blue-grey #A8C7FF fading to white. Title and value line in the attached
   typeface."
3. **Pause plates** (attach `i_tod_pause_r18.png`): "Three pause-menu row
   plates exactly like the attached, 300 x 44, reading SUMMONING POWER, SOUL
   BEAM, SOUL BOMB in the attached typeface."
4. **Ability glyphs** (attach both `i_tod_hud_off_*.png`): "Two 128 x 128
   ability icons in exactly the attached flat two-tone style: SUMMON (a figure
   rising from a glowing ring) and SOUL BOMB (a small skull in an expanding
   burst ring). One bold shape each, readable at 24 px."
5. **Weapon icon** (attach `i_tod_hud_gun_katana.png` + `art_direction_board.png`):
   "Flat white silhouette icon of an ancient skull seen side-on, facing right,
   dark cut-lines for the eye socket, jaw hinge and cracks, transparent
   background, 288 x 132 pixels, same line weight and style as the attached
   katana icon, no colour, no shading, no glow."

---

## 5. What must NOT change

- The chassis of every group: the same frame, positions and sizes as its
  references. This pack adds content; it is not a redesign.
- Class-set pips: tier 1 one lit, tier 2 two, tier 3 three, in SOUL GREEN.
- Upgrade-card pips: THREE sockets on SOUL BOMB / SUMMONING POWER, FIVE on SOUL
  BEAM; regular 1 lit, super 2, ultimate 3.
- Souls are blue-grey, never fire and never electricity.
- The weapon icon is white on transparency only.

## 6. Delivery checklist

- [ ] 21 PNGs + `_overview_necromancer.png`, names and sizes exact, transparent
- [ ] Every word exactly as in section 3 (proofread each card and plate)
- [ ] All text set in the provided typeface
- [ ] No sidearm name on any class or tier card (the big name stands alone)
- [ ] SOUL GREEN only where the references use their class colour
- [ ] Glyph read at 64 x 56, medallion at 56 x 56, plate at 280 x 60, ability
      glyphs at 24 x 24, weapon icon at 144 x 66
- [ ] Laid beside the Skirmisher overview, the class set looks like the same set

## 7. Do NOT

- Do not copy text, weapons or the running-man symbol from the Skirmisher
  references; only their chassis and treatment.
- Do not draw fire, lightning or green souls: souls are blue-grey.
- Do not add numbers or percentages to the upgrade cards' value lines.
- Do not rename files or change sizes.
- Do not use any font other than the provided typeface.

<!-- PACK:END -->
