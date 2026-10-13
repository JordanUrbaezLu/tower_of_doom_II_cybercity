# 184e — THE WHITE GLYPH ICONS: 13 upgrade rows, the AI COMPANION well, the CLOAK tile, SOUL PULSE (PK05)

<!-- art-pack
name: white_glyph_icons
refs:
  i_tod_pm_ico_grapple.png | THE STYLE. A shipped row icon: flat white glyph, soft white glow, transparent background, tinted at runtime.
  i_tod_pm_ico_bash.png | THE STYLE. A wide, short shipped glyph (a fist).
  i_tod_pm_ico_c4.png | THE STYLE. A solid object glyph with transparent cut-outs.
  i_tod_pm_ico_bounty.png | THE STYLE. A shipped skull (BOUNTY): every new skull must read differently from it.
  i_tod_h2_ab_summon.png | THE STYLE. The HUD ability tile glyph (the same style as the row icons).
  i_tod_hud_off_summon.png | THE V1 KIT STYLE for i_tod_hud_off_cloak only: navy outline, light/shade, one green accent, hard pixels.
  i_tod_card2_art_cloak.png | THE SUBJECT of the cloak glyphs.
  i_tod_card2_art_soul_pulse.png | THE SUBJECT of the SOUL PULSE redraw.
  i_tod_card2_art_sprint.png | THE SUBJECT of the sprint icon (each icon takes its card's motif).
  i_tod_pm_ico_generic.png | BEING REPLACED in these rows: the hexagon every unmapped row draws today.
preview: 41x41
-->

> **STATUS: GENERATED + STAGED 2026-10-04 (PK05), NOT LANDED, NOT BUILT, UNPLAYED.** The session
> that found the gap made the art (tools/artgen/README.md). Generator
> `tools/artgen/packs/pk05_glyph_icons.py`; output `art/generated/PK05-white-glyph-icons/`
> (`_review.png` each icon beside its card and its shipped neighbours, `_context.png` every class's
> pause + scoreboard list and the Necromancer's HUD tiles at true 1080p size, `_zoom.png` each icon
> at 128 / 64 / 41 / 36 px). The landing kit is staged under
> `tmp/asset_prod/PK05-white-glyph-icons/` with its `LAND.md`.

## The design (repo-facing)

**The gaps.**
1. `PM_ICON` (AetheriumStartMenu.lua) and `SB_ICON` (AetheriumScoreboard.lua) had no row for 13
   live cards, so they drew `i_tod_pm_ico_generic` (a hexagon with an up arrow): 2-4 rows per class
   shared one placeholder. The AI COMPANION row's empty well drew the same hexagon and read as "an
   upgrade".
2. The Necromancer's tactical tile (the INVISIBILITY CLOAK, `CLASS_KITS[3]`) had no glyph: it
   printed the word CLOAK in the engine font over an empty tile.
3. The SOUL PULSE glyphs (`i_tod_h2_ab_soul_bomb`, `i_tod_pm_ico_soulbomb`) still drew the retired
   lit-fuse SOUL BOMB. The ability is a skull throwing a flat ring of souls.

**The fix.** 16 new images + 2 same-name redraws, all 128x128 RGBA:

| Image | Drawn for | Motif (from the card) |
|---|---|---|
| `i_tod_pm_ico_sprint` | SPRINT 29 (Archer) | a running boot leaning into the stride, speed lines |
| `i_tod_pm_ico_deadeye` | DEADEYE 6 (Archer) | a drawn bow aimed into a reticle with an eye in it |
| `i_tod_pm_ico_quickdraw` | QUICK DRAW 35 (Archer) | a fast arrow across a stopwatch |
| `i_tod_pm_ico_piercing` | PIERCING 26 (Archer) | one arrow through three X-eyed heads on a diagonal |
| `i_tod_pm_ico_adrenaline` | ADRENALINE 25 (Breacher) | three chevrons charging out of a burst |
| `i_tod_pm_ico_fusion` | EXPLOSIVE FUSION 36 (Breacher) | a blast with a healing cross cut through it |
| `i_tod_pm_ico_vitality` | VITALITY 37 (Warrior) | a heart with a healing cross |
| `i_tod_pm_ico_armsspecialist` | ARMS SPECIALIST 7 (Warrior) | a spiked gauntlet's fist round a sword's grip |
| `i_tod_pm_ico_cleave` | CLEAVE 48 (Warrior) | one blade trail slicing three X-eyed heads |
| `i_tod_pm_ico_demonslayer` | DEMON SLAYER 12 (Warrior) | a horned skull with a sword across its jaw |
| `i_tod_pm_ico_reapersreach` | REAPER'S REACH 5 (Necromancer) | the skull on its staff throwing a long forked beam |
| `i_tod_pm_ico_summonermaster` | SUMMONER MASTER 19 (Necromancer) | a summoned hand rising from its ring to a heart |
| `i_tod_pm_ico_cloak` = `i_tod_h2_ab_cloak` | INVISIBILITY CLOAK 9 + the HUD tactical tile | a hooded figure dissolving into vertical streaks |
| `i_tod_hud_off_cloak` | the V1 kit key (never drawn while `USE_HUD_V2`) | the same, in the V1 four colours |
| `i_tod_pm_ico_companion` | the AI COMPANION row with no companion held | a robot head (antenna, visor, two eyes, grille) |
| `i_tod_pm_ico_soulbomb` = `i_tod_h2_ab_soul_bomb` (redraws) | SOUL PULSE 59 + the HUD lethal tile | a skull inside a solid ring and a wider breaking ring |

`i_tod_pm_ico_knifespeed` (a fist with speed lines, zoned, orphaned since MELEE SPEED retired) was
NOT reused for ARMS SPECIALIST: the Warrior's list already holds two fist glyphs (BASH, CYBER
SMASH), and the card is about the blades.

**The style is measured.** The shipped row icons are RGB 255 wherever alpha > 0, the core alpha 255,
and a soft glow that is a Gaussian of the core. The generator renders each drawing at 8x, box-averages
it, adds the glow (sigma 5 px, gain 0.66), and lands within a few alpha units of the references' glow
profile (`--measure`). Each drawing is FITTED: scaled and centred so its longest side is 102 px, so the
glow never touches the canvas edge (a clipped glow shows as a hard line in the row's well).

**The sizes they are read at.** Pause row: 40 x 67/63 canvas units = 64 px at 1080p. Scoreboard row:
24 x 43/38 = 41 px. HUD V2 tile: 24 units = 36 px. Every drawing is a few bold shapes; every cut
survives 41 px.

<!-- PACK:BEGIN -->
# White glyph icons — 16 new + 2 redrawn (fallback brief)

These are normally GENERATED by `tools/artgen/packs/pk05_glyph_icons.py`. Use this brief only if
the generator cannot be used.

## Deliverables (all 128 x 128 PNG, RGBA, transparent background)

`i_tod_pm_ico_sprint`, `i_tod_pm_ico_deadeye`, `i_tod_pm_ico_quickdraw`, `i_tod_pm_ico_piercing`,
`i_tod_pm_ico_adrenaline`, `i_tod_pm_ico_fusion`, `i_tod_pm_ico_vitality`,
`i_tod_pm_ico_armsspecialist`, `i_tod_pm_ico_cleave`, `i_tod_pm_ico_demonslayer`,
`i_tod_pm_ico_reapersreach`, `i_tod_pm_ico_summonermaster`, `i_tod_pm_ico_cloak`,
`i_tod_pm_ico_companion`, `i_tod_h2_ab_cloak` (same drawing as the cloak row icon),
`i_tod_hud_off_cloak` (the V1 kit style), `i_tod_pm_ico_soulbomb` and `i_tod_h2_ab_soul_bomb`
(the same drawing: the SOUL PULSE).

## Hard rules

- A flat WHITE silhouette (RGB 255 everywhere) with transparent cut-outs, and a soft white outer
  glow. No colour, no gradient, no outline. The game tints it.
- The glyph's longest side is about 100 px, centred. Nothing within 12 px of the canvas edge.
- Bold shapes only: it is read at 41 px. Cut-outs at least 5 px wide.
- No text, letters or numbers.
- `i_tod_hud_off_cloak` only: copy `reference/i_tod_hud_off_summon.png` exactly (navy outline, light
  top, shade bottom, the green accent, hard 2-pixel steps).

## Subjects

See the table in the repo brief above: each icon takes its card illustration's motif. Every skull
must read differently from `reference/i_tod_pm_ico_bounty.png` (horns, a beam, rings).
<!-- PACK:END -->
