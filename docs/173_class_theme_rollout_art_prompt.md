<!-- art-pack
name: class_theme_rollout
refs:
  art/class_theme/theme_b_fallen/skirmisher/_overview.png | THE STYLE MASTER. The approved theme (FALLEN / BLACKOUT) on the Skirmisher: every piece together. Match this.
  art/class_theme/theme_b_fallen/skirmisher/i_tod_card_class_skirmisher.png | APPROVED Skirmisher draft card in the new theme. Match its chassis exactly.
  art/class_theme/theme_b_fallen/skirmisher/i_tod_card_tier_skirmisher_2.png | APPROVED Skirmisher tier 2 card (amber hazard UNPACKED ribbon, cyan aura).
  art/class_theme/theme_b_fallen/skirmisher/i_tod_card_tier_skirmisher_3.png | APPROVED Skirmisher tier 3 card (red hazard UNPACKED ribbon, stronger aura).
  art/class_theme/theme_b_fallen/skirmisher/i_tod_class_skirmisher.png | APPROVED Skirmisher glyph in the new theme.
  art/class_theme/theme_b_fallen/skirmisher/i_tod_class_medallion_skirmisher.png | APPROVED Skirmisher medallion in the new theme.
  art/class_theme/theme_b_fallen/skirmisher/i_tod_upg_class_skirmisher.png | APPROVED Skirmisher name plate in the new theme.
  i_tod_card_class_assault.png | OLD-STYLE Archer card - for its slot layout only. Its text is out of date; use the text in INSTRUCTIONS.md.
  i_tod_card_class_heavy.png | OLD-STYLE Breacher card - layout only; text out of date.
  i_tod_card_class_slasher.png | OLD-STYLE Warrior card - layout only; text out of date.
  i_tod_card_class_mage.png | OLD-STYLE Mage draft card. The Lightning Staff's DESIGN here is correct and must be kept.
  i_tod_card_tier_mage_3.png | OLD-STYLE Mage tier 3 card. The three staff DESIGNS (lightning, fire, ice) are correct and must be kept.
  i_tod_class_assault.png | OLD-STYLE Archer glyph (symbol idea only).
  i_tod_class_heavy.png | OLD-STYLE Breacher glyph (symbol idea only).
  i_tod_class_slasher.png | OLD-STYLE Warrior glyph (symbol idea only).
  i_tod_class_mage.png | OLD-STYLE Mage glyph (symbol idea only).
preview: 186x279 234x351 64x56 56x56 280x60
-->

# 173 — Class art THEME ROLLOUT: Archer, Breacher, Warrior, Mage in FALLEN / BLACKOUT

**Status: SHIPPED (docs/176-179 delivered every class; noted 2026-10-04 in the Map 1 purge, R5).** Was: REQUESTED 2026-09-25.

The user picked docs/171's **Theme B, FALLEN / BLACKOUT** and the docs/172 **Option A**
typeface the same day; the Skirmisher's six are installed. This brief is the other four
classes in that theme: 4 x 6 = **24 files**, same names as shipped (no wiring, FULL build).
First pack built with the typography rule: every pack now carries `typography/` and the
"all text in our face" section (tools/art_pack_typography.md).

## Text is TOD II's roster (read from source 2026-09-25)

| key (filename) | Display | Role line | T1 / T2 / T3 primary | T1 / T2 / T3 sidearm |
|---|---|---|---|---|
| assault | ARCHER | PRECISION | BOW / R1 SHADOWHUNTER / FIRE BOW | MAGNUM / MOG 12 / EXECUTIONER |
| heavy | BREACHER | CLOSE RANGE TANK | MOZAMBIQUE / REMINGTON 870 / PEACEKEEPER | MR6 / RPG / NAIL GUN |
| slasher | WARRIOR | UP CLOSE | GOLD TWIN KNIVES / GOLD SWORD / GOLD BATTLE SWORD | AMP63 / UDM 45 / RK7 GARRISON |
| mage | MAGE | SPELLCASTER | LIGHTNING STAFF / FIRE STAFF / ICE STAFF (additive) | none |

Sources: `tod_class_select.lua` CLASSES (names, roles, accents), `tod_upgrade.lua`
TIER_LADDER, `_tod_classes.gsc` TOD_SEC_* (sidearms). The shipped old cards still say
ASSAULT / HEAVY / SLASHER with TOD1 guns.

Accents (class_select `accent`): Archer amber (1.00,0.75,0.25) ~#FFBF40, Breacher red
(1.00,0.35,0.30) ~#FF594D, Warrior violet (0.75,0.45,1.00) ~#BF73FF, Mage mint #59FFCC.
**Breacher clash:** Theme B's secondary accent is emergency red; on the Breacher the class
is red, so the brief swaps that card's emergency side to hazard amber.

## After the drop (repo-facing)

`-Inspect`, look at all 24, proofread every name against the table, copy over the shipped
names, FULL build, prove with fresh content-hash `.iwi`s. Archive the drop beside the
Skirmisher's in `art/class_theme/theme_b_fallen/<class>/`.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — class art: the FALLEN / BLACKOUT theme for the other four classes

**24 PNG files.** We already chose the theme, and the Skirmisher class is done in it. Now
the other four classes — **ARCHER, BREACHER, WARRIOR, MAGE** — need the same six pieces
each, in the **same theme**, so all five classes look like one set.

**Consistency with the approved Skirmisher set is the whole job.** Open
`reference/_overview.png` first: that is the master. Every card, glyph, medallion and plate
you make must look like it came from the same hand, on the same day, as those.

---

## 1. What is in the zip

- `reference/_overview.png` + the six `*_skirmisher.png` files — the APPROVED theme. Match
  the chassis, materials, scratches, hazard stripes, glow, pips, ribbon treatment, layout
  and spacing exactly. Only the class colour, the weapon art and the text change.
- `reference/*_assault.png`, `*_heavy.png`, `*_slasher.png`, `*_mage.png` — the OLD-STYLE
  art for these four classes. Use them ONLY for which slots exist and for symbol ideas.
  **Their text is out of date** (they say ASSAULT, HEAVY, SLASHER and old gun names) — use
  the text in section 3 of this file, never the text on those images.
  Exception: on the two Mage cards, **the staff designs are correct and must be kept**.
- `typography/` — the game's own typeface. **All text must be set in it** (see the
  TYPOGRAPHY section at the end of this file).
- `preview_onscreen_*/` — the references at their real on-screen sizes.

---

## 2. Deliverables

Exact filenames and sizes, PNG with transparency. The filenames use the game's internal
class names (assault = ARCHER, heavy = BREACHER, slasher = WARRIOR) — keep them as written.

| Class | Draft card 768x1152 | Tier 2 card 768x1152 | Tier 3 card 768x1152 | Glyph 224x196 | Medallion 512x512 | Name plate 420x90 |
|---|---|---|---|---|---|---|
| ARCHER | `i_tod_card_class_assault.png` | `i_tod_card_tier_assault_2.png` | `i_tod_card_tier_assault_3.png` | `i_tod_class_assault.png` | `i_tod_class_medallion_assault.png` | `i_tod_upg_class_assault.png` |
| BREACHER | `i_tod_card_class_heavy.png` | `i_tod_card_tier_heavy_2.png` | `i_tod_card_tier_heavy_3.png` | `i_tod_class_heavy.png` | `i_tod_class_medallion_heavy.png` | `i_tod_upg_class_heavy.png` |
| WARRIOR | `i_tod_card_class_slasher.png` | `i_tod_card_tier_slasher_2.png` | `i_tod_card_tier_slasher_3.png` | `i_tod_class_slasher.png` | `i_tod_class_medallion_slasher.png` | `i_tod_upg_class_slasher.png` |
| MAGE | `i_tod_card_class_mage.png` | `i_tod_card_tier_mage_2.png` | `i_tod_card_tier_mage_3.png` | `i_tod_class_mage.png` | `i_tod_class_medallion_mage.png` | `i_tod_upg_class_mage.png` |

On screen: draft card 186 x 279, tier cards 234 x 351, glyph 64 x 56, medallion 56 x 56,
name plate 280 x 60.

Plus one `_overview_<class>.png` per class (archer, breacher, warrior, mage), laid out like
the Skirmisher's `_overview.png`. For choosing only.

---

## 3. Each class: colour, text and weapons

The Skirmisher's cyan is its CLASS colour: it is the ribbon text, the nameplate glow, the
pips, the tier aura, the glyph and the medallion ring. Each class swaps cyan for its own
colour in exactly those places. Everything else (black steel, scratches, hazard stripes,
the red emergency side-rail, the amber tier 2 / red tier 3 UNPACKED ribbons) stays as on
the Skirmisher.

### ARCHER — class colour AMBER `#FFBF40`
- Draft card: **TIER 1** / role line **PRECISION** / ribbon **ARCHER** / **BOW** over **MAGNUM**
- Tier 2: **R1 SHADOWHUNTER** over **MOG 12**
- Tier 3: **FIRE BOW** over **EXECUTIONER**
- Weapons: T1 a sleek modern recurve/compound bow; T2 a futuristic crossbow; T3 a bow
  wreathed in flame (fire along the limbs and string).
- Glyph idea: an archer drawing a bow, or a drawn bow with arrow. Name plate: **CLASS ARCHER**.

### BREACHER — class colour RED `#FF594D`
- Draft card: **TIER 1** / **CLOSE RANGE TANK** / **BREACHER** / **MOZAMBIQUE** over **MR6**
- Tier 2: **REMINGTON 870** over **RPG**
- Tier 3: **PEACEKEEPER** over **NAIL GUN**
- Weapons: T1 a stubby triple-barrel shotgun pistol; T2 a classic pump-action shotgun;
  T3 a chunky sci-fi lever-action energy shotgun.
- **Because this class is red, its emergency side-rail becomes hazard AMBER** (where the
  Skirmisher has a red rail) so the class red still reads as the identity.
- Glyph idea: a shotgun blast / a boot kicking through a door. Plate: **CLASS BREACHER**.

### WARRIOR — class colour VIOLET `#BF73FF`
- Draft card: **TIER 1** / **UP CLOSE** / **WARRIOR** / **GOLD TWIN KNIVES** over **AMP63**
- Tier 2: **GOLD SWORD** over **UDM 45**
- Tier 3: **GOLD BATTLE SWORD** over **RK7 GARRISON**
- Weapons (all gold, glinting against the dark card): T1 a crossed pair of gold combat
  knives; T2 a gold one-handed sword; T3 a large ornate gold two-handed battle sword.
- Glyph idea: crossed blades or a figure mid-slash. Plate: **CLASS WARRIOR**.

### MAGE — class colour MINT `#59FFCC`
- Draft card: **TIER 1** / **SPELLCASTER** / **MAGE** / **LIGHTNING STAFF** — no sidearm
  line (the nameplate carries only the staff name, as on the old Mage card)
- Tier 2: **FIRE STAFF**, art shows the lightning and fire staffs crossed (the Mage KEEPS
  every staff, so tier 2 shows two and tier 3 shows three)
- Tier 3: **ICE STAFF**, art shows all three staffs
- **Keep the staff designs from the old Mage cards** (bronze-banded shafts; lightning =
  purple crystal in a ring head, fire = flaming bronze claw head, ice = blue crystal in a
  tall frame). Re-render them in the new theme's lighting; do not redesign them.
- Glyph idea: a staff with a glowing head, or a hooded caster. Plate: **CLASS MAGE**.

---

## 4. What must NOT change

- The chassis: the same frame, header, art window, ribbon, nameplate and pips as the
  approved Skirmisher cards, in the same positions and sizes.
- Pips: tier 1 one lit, tier 2 two lit, tier 3 three lit, in the class colour.
- Tier cards carry the UNPACKED ribbon (amber hazard on tier 2, red hazard on tier 3) and
  the outer aura in the class colour; tier 3 reads a step above tier 2.
- Weapons side-on, same scale and angle as the Skirmisher cards, recognisable at 186 px.
- Medallion readable at 56 x 56; glyph one clean shape at 64 x 56; plate text legible at
  280 x 60.

## 5. Delivery checklist

- [ ] 24 PNGs, names and sizes exact, transparent background
- [ ] Every name and number exactly as section 3 (proofread each card)
- [ ] All text set in the provided typeface
- [ ] Each class uses only its own class colour where the Skirmisher uses cyan
- [ ] Breacher's emergency rail is amber, not red
- [ ] Mage staffs match the old Mage cards' designs; Mage cards have no sidearm line
- [ ] Medallions checked at 56 x 56, plates at 280 x 60
- [ ] One `_overview_<class>.png` per class
- [ ] Laid beside the Skirmisher overview, all five classes look like one set

## 6. Do NOT

- Do not change the theme, the chassis, or the layout — this is a rollout, not a redesign.
- Do not copy text from the old-style reference images.
- Do not rename files to ARCHER / BREACHER / WARRIOR — keep the filenames in section 2.
- Do not use any font other than the provided typeface.

<!-- PACK:END -->
