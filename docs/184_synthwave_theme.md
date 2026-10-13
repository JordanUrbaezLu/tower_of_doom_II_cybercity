# 184 — THE UI THEME IS NEON SYNTHWAVE (supersedes the red "Fallen" UI)

> **SUPERSEDED AS THE DEFAULT 2026-10-05 (docs/218_red_return.md).** User: *"id rather the red theme please"*. The red Fallen UI is
> back, drawn by the same generators; this theme is one line away (`tools/artgen/synthwave.py` `THEME =
> 'synthwave'`, every pack re-renders its shipped bytes). The record below stays as the synthwave design.

> **STATUS: REQUESTED 2026-09-26. NOTHING INSTALLED.** User, on the red prompt-card drop
> (`files - 2026-09-26T213433.116.zip`, clean, NOT installed): *"I kinda want a different
> theme tho"*, then picked **Neon synthwave** for the **whole UI**. The red pause menu,
> scoreboard and HUD stay installed (and ride build 16) until the synthwave drops land; the
> red prompt-card drop is parked in Downloads as a fallback.

## Why this is a file swap

Every red surface was built as baked chrome + EMPTY live areas, with white glyphs tinted
by code. So the theme lives in two places only:
1. **The chrome PNGs**, redrawn under the SAME names, sizes and slots (four packs below).
2. **A short list of code tints** (below), changed in one pass when the art lands.
No layout number moves. The 62 white glyphs (`i_tod_pm_ico_*`, `i_tod_pm_gly_*`,
`i_tod_h2_ab_*`, gauge segments, fills) are theme-neutral and are NOT redrawn.
(2026-10-05, W3B, user: "add some color to give it more personality": the 12 HUD ability tile
glyphs `i_tod_h2_ab_*` left this list. They are drawn IN COLOUR by
`tools/artgen/packs/w3b_ability_colour.py` in R4's neon-glyph language - white-hot ink, one
part in its ability's / class's hue, a hue halo - and the HUD never tints them (alpha only).
The pause / scoreboard row twins `i_tod_pm_ico_*` stay white: their tint is the row's state.)

## Palette (style board: docs/184_synthwave_ref/style_board.png)

| Role | Hex | LUI RGB |
|---|---|---|
| plate / panel / header | `#0C0716` / `#140C24` / `#1F1336` | - |
| frame steel | `#4A3A70` | - |
| MAGENTA (frame light, "ready", headline words) | `#FF2BD1` | 1.00, 0.17, 0.82 |
| CYAN (rules, focus, lit pips, info text) | `#1FE5FF` | 0.12, 0.90, 1.00 |
| VIOLET (secondary frames, dark-card twins) | `#7A46FF` | 0.48, 0.27, 1.00 |
| SUNSET (rampage inner line only) | `#FF8A3D` | 1.00, 0.54, 0.24 |
| GOLD (points only) | `#F5D742` | unchanged |
| lavender-grey (secondary text) | `#B8AED8` | 0.72, 0.68, 0.85 |

## The four packs (all in ~/Downloads)

| Pack | Brief | Files | Skips |
|---|---|---|---|
| `tod_synthwave_pause_menu_art_pack.zip` | docs/184a | 20 | 40 white glyphs |
| `tod_synthwave_scoreboard_art_pack.zip` | docs/184b | 8 | - |
| `tod_synthwave_hud_art_pack.zip` | docs/184c | 23 | 22 white pieces |
| `tod_synthwave_prompt_cards_art_pack.zip` | docs/184d | 17 | - |

Each brief = the theme override + the exact redraw list + the original red-era spec
(docs/180..183) verbatim for shapes, baked words and empty areas. The HUD brief carries
the round badge / luck plate rows (the status plate is retired). Suggested order: prompt
cards first (the smallest, and the new theme's pilot), then the other three.

## Code tints to change on install (one pass, then the lint + lifetime gates)

- **Red digits and values → MAGENTA**: `0.98, 0.11, 0.22` in AetheriumStartMenu (round
  number, game time), AetheriumScoreboard (round number), tod_upgrade.lua (`Round2Row`).
- **`PM_RED` (0.95, 0.13, 0.23)** in AetheriumStartMenu and the scoreboard's lit-pip tint
  → CYAN (lit pips). The dark-card pip (0.71, 0.36, 1.0) → VIOLET.
- **Reset / warning plates `1.0, 0.34, 0.36`** (pause + scoreboard) → SUNSET.
- **Gauge** (tod_upgrade.lua V2): `G2_SPIRE_RGB` red → MAGENTA; the tower keeps its five
  district colours (they ARE the city's neon); boss marker stays orange.
- **KEEP**: gameplay-signal tints (downed red health, aura green, Archmage rainbow, shield
  health colours, `G2_DOWN_RGB`). "No red" is an art rule, not a rule against a danger
  signal.
- **Prompt cards**: wire `i_tod_prompt_chassis_locked` (SetLocked) and the four new icon
  rows (partner bench / partner part / the alarm / generic fallback), per docs/183.

Install per drop: `-Inspect`, look at every image, sizes x4, render over the real canvas,
same-name copy (new names: GDT block clone of `i_tod_pause_pip` + zone line), FULL build,
fresh content-hash `.iwi` proof. Shared files: ping the Archer lead first.
