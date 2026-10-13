# docs/218 - THE RED RETURN: the Fallen UI theme, behind one switch (2026-10-05)

**User 2026-10-05:** *"We changes the red theme? ... id rather the red theme please"*, after *"Whole entire asset
library should look like one library"* and *"Asset library is for you to own"*. In the same message: *"the round X in
top right still shows when we should have our assets actually replace that"* and *"the upgrade and choose class
banners should be in our typography"*.

STATUS: STAGED by RT-impl (tmp/redtheme/RT-impl, two passes: the return, then a three-reviewer round), landed by
`land.py`, UNBUILT until the next FULL build, UNPLAYED.

## What the player sees

The whole UI is back in the red **Fallen** look of docs/171 Theme B and docs/180-183 (the pause menu, the scoreboard,
HUD V2, the prompt cards), drawn by the same generators as the synthwave pass, so every layout, size, slot and word
of the last two days stays where it is:

- **Neutral charcoal glass** (panel `#121119`, plate `#0F0E15`, header `#1C1B26`), never violet. The HUD V2 plates are
  ~85 % opaque again (docs/182 s3: the world shows faintly through).
- **Grey scratched steel** hairlines (`#6B7589`, bright `#8A93A8` on secondary frames), scratches visible again.
- **RED is the one accent** (`#F2203A`), lit where the red era lit it: the big pause / scoreboard panels are a STEEL
  frame with the red on the sides the red era measured (pause left: both sides + the notch; pause right: the top run
  and the bottom; scoreboard top: the header notch, the right side, the bottom; scoreboard bottom: both sides),
  focus, ready, the headline accent word (solid red, our glyph cells), rules, slashes, lit pips, the round number and
  game time. The red is a tight line (centre `#FF5E73`), never a white-hot tube. Header rules are unlit steel.
- **Ice blue for info** (`#9DD0FF`): UPGRADE CARDS, the column titles, an idle button's bottom edge, the timers, the
  Black Market's luck count and status line.
- **Backdrops:** crimson corner haze at the red era's strength, ~100 glowing red embers in the outer ring, no horizon
  grid; the skyline is dark. **Panels:** sparse red splatter in a corner (kept off the scoreboard's tagline).
- **The pause titles** are crisp white over a hard dark extrusion (no neon halo); the skull's contour is dim steel, so
  its red eyes carry it; the secondary text grey is lifted to `#A0A8BF` (7.5:1 on the panel).
- **The deal panel's luck badge** steps up in LIGHT, in the one accent: unlit steel with a white number at 10-30 %, a
  dim red line at 40-60 %, full red at 70-100 %.
- **The round badge's RAMPAGE** is a pale face over the red halo (the red era's `#FF8292`), readable at 108 px.
- **The power-up toast** has the HUD's one reward colour on its edge: gold (docs/182 table E).
- **The power-ups** wear the red library's content colours: Insta-Kill a bone-white skull with red eyes, Zombie Blood
  blood red, Max / Infinite Ammo brass, Carpenter wood orange, Free PaP the HUD's PaP gold, Time Warp ice, Gift of
  Death the red era's violet. Double Points (gold), Fire Sale and the Nuke (fire) are unchanged.
- **The violet (dark-card) pip** is pure violet again (centre hue 266, nothing in the pink band).
- **The card back** is the red era's: dark scratched glass, a faint steel ring behind the spire, the dark city, no
  outrun sun, no grid floor.
- **THE PULL's reveal stamp** ("LEGENDARY / +4 LEVELS") is a chamfered dark-glass plate with one rim of the rarity's
  light (R10's grammar), the word in the rarity's colour; the folded-tail ribbon is gone. Unlit level pips are dim
  steel, not navy.
- **The Black Market screen** is red too: the machine's frame and BLACK MARKET title in the red, its rails unlit
  steel, the needle and the focused slot in the red, the SCRAP plate steel with an ice-blue mark, charcoal glass.
  (It was the one magenta / cyan screen left; docs/188 / 190 briefed its chrome in the synthwave palette - theme
  chrome, not the Dealer's identity, which is black / oxblood / red.) The companion's cyan, the Dealer and companion
  portraits, the item icons, the rarity tiles and banners and the CURSED red are untouched.
- **The companion plate** reads DEPLOYING in the red era's dark-card violet and HOLDING in steel.
- **The class draft / card deal** confirm flash is the theme's WHITE on the chosen card's strips (the red flash was
  the Breacher's own accent, so locking the Breacher flashed nothing).
- **Kept untouched:** the class accents, rarity hues, perk hues, the points gold, the amber reset mark, the pad-A
  green, the haven cyan, TodArena's colours, the card illustrations, the class emblems (no red arc on a medallion),
  R10's "rarity steps up with light", the safe inset, every layout and word.

## The switch

`tools/artgen/synthwave.py` line `THEME = 'fallen'`. Set it to `'synthwave'` and every pack re-renders the shipped
synthwave bytes (proved: all 18 theme-touching gates byte-identical in `tmp/redtheme/RT-impl/mirror_sw`, plus the w2g /
r10 / bm selftests and r4's fit selftest). The palette is `THEMES[theme]['PAL']`: every role has a value in both
themes; the fallen column is measured off the red-era art (`art/generated/RT-palette/fallen.json`), and a dark the
red era never drew keeps its synthwave luma with the red era's neutral cast (`_neutral`). `LOOK` carries the
non-colour differences (the word face, glow ceilings per role, scratch strength, focus wash, grid, skyline, splatter,
sparkles, the GAME OVER fringe, the HUD plates' opacity, the big panels' lit runs, the title halo, the backdrop embers
and their premultiplied glow, the corner haze).

The rule every helper follows: **a ROLE name is theme chrome, a literal `#RRGGBB` is content.** `tube()` caps a
role's halo by the theme, `scratches()` / `embers()` theme only role-coloured calls, and identity hues that must
never move are literal hexes (PERK_HUE, class / rarity hues) or `id_*` roles (W3B's fire and brass; Double Points,
Fire Sale, the Nuke). A pack with nothing to generate in one theme PARKS the delivered art and returns its exact bytes
there: r10's PULL stamp (`docs/217_ref/_prev_shipped/i_tod_pull_banner.png`) and `bm_chrome.py`
(`docs/218_ref/_prev_shipped/`, the six reel chrome pieces).

The code half follows the same switch and is gated, each with a planted-other-theme control:
- `r3 --check` CODE_TINTS: PM_RED, the focused glyph, the round number and game time (pause menu / scoreboard), THE
  PULL's unlit pip and its stamp word.
- `r4 --check` ROUND2_TINT on the HUD round number; PK07's arena accent reads THEME.
- `pk09 --check` GSC_TINTS: the GAME OVER readout + survived line in `_tod_gameover.gsc`.
- `w2g --check` CP_TINTS: the companion plate's VIOLET / STEEL / TEXT.
- `bm_chrome --check` LUA_TINTS: `TodSpinReel.lua` P3.THEME (focus / info / title / rails / caption) and EMPTY_RIM.

Reverting: set THEME, run every pack's `--install` (tmp/redtheme/RT-impl/install_fallen.py lists the order), and swap
the code lines each gate names (the synthwave values are written next to each one).

## The other notes

- **"ROUND X in the top right"**: `AetheriumRoundCounter.lua` hid itself with one container `setAlpha( 0 )`, and
  `AetheriumHud.lua` writes that element's alpha back to 1 twice, so every match showed the round twice. The widget
  now hides its own glyph row and never paints it; `CoD.TodRound` stays published. `tools/test_round_counter_v2.lua`.
- **"banners in our typography"**: the baked banners were already our glyph cells (proved in
  `art/generated/RT-hunt/banner_vs_typeface.png`); the accent word is now a SOLID red glyph fill. The engine-font text
  a keyboard player saw on the deal panel and the class draft was the KEYCAPS (Engine.Localize returns the unexpanded
  token live, docs/145): `TodKeycap.Resolve` asks GetKeyBindingLocalizedString first, as the pause menu does
  (`tools/test_keycap_resolve.lua`). The card menus' no-art fallback texts and live-bind hint lines use our TTF too.
- **THE TOAST** (`TodToast.lua`, `tools/test_toast.lua`): the stock-font IPrintLnBold lines that crossed the deal
  banner - a teammate's PULLED A LEGENDARY (card and Black Market), IS ON FIRE, CLASS TIER n UNLOCKS AT FLOOR f, FLOOR f
  REACHED - CLASS TIER n UNLOCKED (- PACK-A-PUNCH TO PROMOTE), NEW WEAPONS ARE NOT PACK-A-PUNCHED and the Archer's arm
  line - are ONE int event now (`tod_toast`: kind, who, code; `_tod_upgrade_ui.gsc` team_toast / self_toast), drawn in
  our glyph cells on the title plate above the deal banner and the Black Market frame. Same words; the teammate's
  name on top (a name we cannot draw falls back to our face's TTF). A new toast replaces the showing one; it rides
  over the card deal and the reel and hides under any other veil owner (the jump cine, the class terminal).
- **The pause legend's SPACE key** fits its cap (it needed 38.5 of 37.3; the review mocks now bind a key per command,
  which is how it was found).
- **The scoreboard's ROUND number and POINTS value show again**: under V2 they were added before the panel chrome,
  so the opaque ROUND box and the points capsule painted over them (later children paint on top - the V2 block's own
  comment). They are added after the chrome now.

## Evidence

`art/generated/RT-impl/_review_*.png` (RED ERA | SYNTHWAVE | FALLEN per family at the 1080p draw size, the Black
Market and the PULL stamp included) and `_review_ctx_*.png` (the real Lua under the mocks: pause and scoreboard with
the ROUND box filled (a review-only shim, `tmp/redtheme/RT-impl/review_menus.py`), four deals with the real keycaps,
the Black Market, the companion plate, the arena HUD, THE TOAST over a deal and the HUD, the class draft LIVE through
`tod_class_select.lua` (`_review_ctx_draft_live.png`); composed: HUD V2, the prompt cards, the pause right panel).
A mock is not the engine: every UIText draws in our TTF there, so the native look is the user's playtest.
