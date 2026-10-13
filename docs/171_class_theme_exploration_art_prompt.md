<!-- art-pack
name: class_theme_exploration
refs:
  i_tod_card_class_skirmisher.png | CURRENT draft card (class select screen). Keep its layout and every text slot; restyle everything else.
  i_tod_card_tier_skirmisher_2.png | CURRENT tier 2 promotion card. Same chassis as the draft card plus the outer glow and the UNPACKED ribbon.
  i_tod_card_tier_skirmisher_3.png | CURRENT tier 3 promotion card. Read it beside tier 2 to see how a ladder step is shown.
  i_tod_class_skirmisher.png | CURRENT class glyph (small landscape line-art figure). Sits on the draft card area / class select.
  i_tod_class_medallion_skirmisher.png | CURRENT HUD portrait medallion. Round, ringed, must read at thumbnail size.
  i_tod_upg_class_skirmisher.png | CURRENT class name plate on the upgrade panel. Wide strip with baked type.
  art/theme_refs/ref1.png | MOOD reference for the new map (not a UI piece). The world these cards now live in.
  art/theme_refs/ref2.png | MOOD reference 2.
  art/theme_refs/ref3.png | MOOD reference 3.
preview: 186x279 234x351 64x56 56x56 280x60
-->

# 171 — Class art THEME EXPLORATION (Skirmisher as the test subject): art request

**Status: THEME CHOSEN 2026-09-25 — THEME B, FALLEN / BLACKOUT. Its Skirmisher set is installed over the six shipped names (drop archived in `art/class_theme/theme_b_fallen/skirmisher/`, incl. `_overview.png`). The other four classes are requested in docs/173.**

User, 2026-09-25: *"we want to change the theme of the assets a little bit ... give me the
class assets ... just one of them, maybe Skirmisher, and then I'm going to have the LLM
create me four different versions of the new theme. And we'll use one of those as the new
theme for this map."*

So this pack is a **style audition**, not a delivery: four complete re-themes of the
Skirmisher's six class images. The user picks one, and that direction then becomes the
brief for re-baking every class (and later the rest of the UI).

## Why these six files

The Skirmisher's per-class art is exactly five families (docs/116's sweep):
draft card, tier 2/3 cards, glyph, HUD medallion, upgrade name plate. Six PNGs. Sending the
whole set, not only the card, is on purpose: a theme that works on a 768x1152 card and
falls apart on a 56x56 medallion is not a theme we can adopt.

## Text on the cards is the CURRENT roster (TOD II)

The shipped Skirmisher cards still say MSMC / MP5 / MP7 (TOD1). TOD II's ladder is
**SAUG -> M1927 -> R-99** (docs/153, docs/165); secondaries unchanged (BULLDOG / SG12 /
SPAS-12). The pack asks for the new names so the winning theme's Skirmisher set is also
the corrected set.

## Mood references

`art/theme_refs/ref1..3.png` are the user's three ChatGPT sky references (the same files
the sky render copies, docs/166). They are the clearest statement of the map's new look:
dark metal spires, saturated crystal slabs, cyan / magenta / amber neon, deep-space void.

## After the drop (repo-facing, not in the pack)

`.\tools\make_art_pack.ps1 -Inspect "files (N).zip"`, show the user all four themes side by
side at on-screen size. Install NOTHING. The chosen theme gets its own follow-up brief for
all five classes (Skirmisher, Archer, Breacher, Warrior, Mage) — same filenames, so no
wiring changes; FULL build then.

<!-- PACK:BEGIN -->

# TOWER OF DOOM II — class art: FOUR NEW THEMES (style audition)

**24 PNG files: the same 6 images, re-themed 4 different ways.**

This is a zombies map set in a **fallen cyber-city**: a black megacity under a deep-space
sky, towers of dark metal wrapped in glowing crystal and neon, a giant crown floating at
the top of the tower where the game begins. The in-game UI art (cards, badges, plates) was
drawn for an earlier, brighter, cartoonier version of the map. We want to **change the
theme** so the UI belongs to this darker, richer world.

You are producing an **audition**. We will look at your four themes side by side and pick
ONE to become the look of every class in the game. So the four must be **genuinely
different from each other** — not four colour swaps of one idea.

---

## 1. What is in `reference/`

- **The six CURRENT Skirmisher images** (`i_tod_*.png`). These define the *function and
  layout* of each piece: what goes where, what text it carries, how big things are. They
  do **not** define the style — the style is what we are replacing.
- **`ref1.png`, `ref2.png`, `ref3.png`** — MOOD references for the new world. Not UI.
  Read them for palette, materials and atmosphere.

`preview_onscreen_*/` shows the current images at the size a player actually sees them.
Judge your work at those sizes too.

---

## 2. Deliverables

One folder per theme: `theme_a/`, `theme_b/`, `theme_c/`, `theme_d/`. Inside each, these
six files with **exactly these names and sizes** (PNG, transparent background):

| # | File | Size (px) | Seen on screen at |
|---|---|---|---|
| 1 | `i_tod_card_class_skirmisher.png` | 768 x 1152 | 186 x 279 |
| 2 | `i_tod_card_tier_skirmisher_2.png` | 768 x 1152 | 234 x 351 |
| 3 | `i_tod_card_tier_skirmisher_3.png` | 768 x 1152 | 234 x 351 |
| 4 | `i_tod_class_skirmisher.png` | 224 x 196 | 64 x 56 |
| 5 | `i_tod_class_medallion_skirmisher.png` | 512 x 512 | 56 x 56 |
| 6 | `i_tod_upg_class_skirmisher.png` | 420 x 90 | 280 x 60 |

Plus, per theme, **one overview sheet** `theme_X/_overview.png` (any size, ~1600 wide):
all six pieces laid out together on a dark background, with a one-line name for the theme
written on it. This is only for choosing; it is never used in the game.

Plus one short `THEMES.md`: for each theme, its name, 2-3 sentences on the idea, and its
palette as hex codes.

Same filename in every folder is on purpose — the winner drops straight into the game.

---

## 3. What must NOT change (the function)

Every theme keeps the job each piece does. Restyle freely; do not re-plan.

**Draft card (file 1)**, top to bottom, same slots as the reference:
1. Header band: **TIER 1**
2. Art window: the perk line **RUN AND GUN** above the weapon picture
3. Class ribbon: **SKIRMISHER**
4. Nameplate: primary gun **SAUG** (big), secondary **BULLDOG** (small, under a divider)
5. Three tier pips, **first lit**, two dark

**Tier cards (files 2, 3):** same stack as the draft card, plus
- Header **TIER 2** / **TIER 3**
- The ribbon across the bottom of the art window reading **UNPACKED**
- Nameplate: tier 2 = **M1927** / **SG12**; tier 3 = **R-99** / **SPAS-12**
- Pips: tier 2 = two lit; tier 3 = three lit
- An outer glow/aura that the tier 1 card does not have (it says "promotion")
- Tier 3 must read as a clear step above tier 2, in the same theme

**Weapons in the art windows** (side-on, same angle as the reference):
- Tier 1 **SAUG** — a compact bullpup SMG: magazine behind the grip, short stubby body.
- Tier 2 **M1927** — a Thompson-style drum/stick-mag submachine gun, wooden stock and
  foregrip, finned barrel.
- Tier 3 **R-99** — a sleek sci-fi SMG: angular boxy receiver, magazine under the front,
  skeletal stock.
Draw them in your theme's rendering style, but they must be recognisable as three
different guns and clearly weapons at 186 px tall.

**Glyph (file 4):** a small emblem that means "fast, runs while shooting". The current one
is a running figure firing a pistol, with speed lines. You may redesign the symbol, but it
must read at 64 x 56 and be one clean shape.

**Medallion (file 5):** round, ringed disc with the class symbol inside. It sits beside the
player's health bar all match. Must read at **56 x 56** — test it.

**Name plate (file 6):** wide strip with a small icon on the left and the words
**CLASS SKIRMISHER**. Text must be legible at 280 x 60.

**Class colour:** the Skirmisher's identity colour is **cyan**. Keep a cyan-family accent
somewhere in every theme (the other classes will get their own accent colours in the
same theme later — so the theme itself must not *depend* on cyan everywhere; the frame
and materials carry the theme, the accent carries the class).

---

## 4. What SHOULD change (the theme)

Everything else: frame shape, materials, lighting, rendering style, type style, ornament,
background of the art window, how glow is used.

**The current look, which we are moving away from:** thick black cartoon outlines,
rounded toy-like navy panels, candy-orange header, flat bubble lettering, screws in the
corners. Friendly and bright. It belongs to a different map.

**Where we want to go**, taken from the mood references:
- Mostly **dark** — black, gunmetal, deep indigo — so the glowing parts pop.
- Light comes from **glowing edges, crystal, and neon**, not from bright flat panels.
- Richer materials: brushed metal, glass, crystal facets, engraved detail.
- Palette of the world: void black, deep indigo, magenta/violet nebula, **cyan neon**,
  warm amber/orange city glow, occasional hot pink and emerald green.
- Still a GAME UI: bold, readable shapes, strong silhouettes. Not a photo, not noise.

### Four directions (use these, or propose better ones — but keep four distinct ideas)

- **A — CRYSTAL SPIRE.** Dark metal frame with sharp, tapering, cathedral-spire geometry;
  light concentrated in a few saturated crystal slabs set into the frame; thin neon seams.
  The closest match to the mood references.
- **B — FALLEN / BLACKOUT.** Near-black, damaged, emergency-lit: scratched steel, a red
  alarm accent beside the class cyan, flickering or cracked neon, warning stripes used
  sparingly. The city after the power died.
- **C — DEEP SPACE.** The frame as a window onto the void: nebula colour, stars and a
  subtle black-hole swirl inside the art windows, dark glass panels with holographic
  type. Cosmic and elegant.
- **D — THE CROWN.** Regal cyber: dark gunmetal with aged brass/gold filigree, jewel
  inlays, crest shapes — as if forged for the floating crown at the tower's top. Premium,
  heavy, ornate, but still readable.

All four should still feel like the same *world*; they differ in attitude.

---

## 5. Hard rules

- Exact filenames and pixel sizes above. PNG with alpha. Nothing outside the art.
- All text exactly as written in section 3, spelled exactly, in capitals.
- Every piece readable at its on-screen size. **Check each one shrunk down** before
  delivering. Thin type and fine linework that vanish at 56 px / 186 px are failures.
- Within one theme, all six pieces must obviously belong together.
- The tier 1 / 2 / 3 cards within one theme share one chassis.
- No logos, trademarks, real brand names, or text other than what is specified.
- No characters or faces.

---

## 6. Delivery checklist

- [ ] 4 folders `theme_a` .. `theme_d`, 6 PNGs each, names and sizes exact
- [ ] One `_overview.png` per theme with the theme name on it
- [ ] `THEMES.md` with names, ideas and hex palettes
- [ ] Every card: TIER N header, RUN AND GUN (tier 1), SKIRMISHER ribbon, correct
      gun + secondary names, correct number of lit pips, UNPACKED on tiers 2 and 3
- [ ] Three different, recognisable guns (SAUG, M1927, R-99)
- [ ] Medallion checked at 56 x 56, plate text checked at 280 x 60
- [ ] The four themes look clearly different from each other

## 7. Do NOT

- Do not just recolour the current cartoon cards. The style itself is what changes.
- Do not make four versions of the same idea.
- Do not drop any text slot or move the layout around.
- Do not make it so dark or so detailed that nothing reads at small size.
- Do not add extra files or rename files.

<!-- PACK:END -->
