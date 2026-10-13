# 179b — GUN-BAY ICONS: the Soul Staff, the Crown of the Damned, and the Cyber Sword redraw (PK06)

<!-- art-pack
name: gun_bay_icons_soulstaff_crownstaff_cybersword
refs:
  i_tod_hud_gun_skull.png | THE STYLE + THE TIER BEFORE. The Necromancer's tier-1 icon (the Skull of Nan Sapwe): three flat tones, thick navy outline, transparent background.
  i_tod_hud_gun_greatsword.png | BEING REPLACED. The old Gold Battle Sword broadsword silhouette; the weapon is now the Cyber Sword.
  i_tod_hud_gun_gauntlet.png | THE STYLE. The Warrior's tier-2 icon: chunky flat forms, lower part in the shade tone.
  i_tod_hud_gun_firebow.png | THE STYLE. The Archer's tier-3 icon: a spiky silhouette in the same three tones.
  i_tod_hud_gun_staff2.png | THE STYLE OF A STAFF GRIP. A staff icon whose grip wrap is bold shade-tone diagonal stripes.
  art/necro_staff/tier2_head.png | THE SUBJECT. The Soul Staff's head: a skull with glowing white eyes and an open jaw on a riveted socket.
  art/necro_staff/tier3_head.png | THE SUBJECT. The Crown of the Damned: the skull inside a studded ring, a sunburst of forged blades, a long spear finial.
  art/cyber_sword/native_oblique.png | THE SUBJECT. The Cyber Sword: long blade, dark circuit panel with glowing traces, horned base.
  art/cyber_sword/native_hilt.png | THE SUBJECT. The Cyber Sword's hilt: winged cross guard, reactor gem, wrapped grip, diamond pommel.
preview: 144x66
-->

> **2026-10-05 (wave 2, W2G): THE TIER-1 SKULL JOINS THIS PACK.** `i_tod_hud_gun_skull` (the
> 2026-09-26 drop: a rounded lump with one eye and a grin, which read as a reptile skull) is redrawn
> BY HAND by `nan_sapwe()` from the truth renders (`art/generated/R1-truth-renders/skull_side.png`,
> `skull_34.png`): the long swept crest with its tribal glyphs, one big eye socket, the jaw hanging
> OPEN with three upper fangs and three lower teeth, the ribbed back. The two staff skulls now hang
> their jaws open too (`JAW_DROP`), so the Necromancer's three tiers share one language. Bow, fire
> bow, fist and gauntlet were judged against their truth renders at 144 x 66 and kept. Review:
> `art/generated/W2G-icons-plate/_review.png`; landing kit `tmp/wave2/W2G-icons-plate/LAND.md`.
>
> **STATUS (PK06): GENERATED + STAGED 2026-10-04 (PK06); since landed - live in the repo, its --check a build gate.** The session
> that found the gap made the art (tools/artgen/README.md). Generator
> `tools/artgen/packs/gun_bay_icons.py`; output `art/generated/PK06-gun-bay-icons/` (review sheet
> `_review.png`); the landing kit (three PNGs, two GDT blocks, two zone lines, eight Lua rows) is
> staged under `tmp/asset_prod/PK06-gun-bay-icons/` with its `LAND.md`.

## The design (repo-facing)

**The gap.** The weapon panel's gun bay draws `"i_tod_hud_gun_" .. category`
(`AetheriumLoadout.lua` `refreshGunIcon`), the category resolved from the held weapon's DISPLAY
name (`TOD_NAME_CAT`), then its asset stem (`TOD_GUN_CAT`). A promotion gives the Necromancer
`tod_necro_staff2` "Soul Staff" and then `tod_necro_staff3` "Crown of the Damned" (+ the EX forms,
`source_data/tod_necro_staff.gdt`). Neither name was in `TOD_NAME_CAT` and both stems mapped to
`skull`, so a promoted player kept the tier-1 skull; after a respawn (`curCat` nil) the bay drew
the MR6 pistol. Every other live class has its own icon at each tier. Separately the Warrior's
tier-3 sword was renamed CYBER SWORD and re-modelled while `i_tod_hud_gun_greatsword` stayed the
plain Gold Battle Sword broadsword (CHANGELOG re-bake list).

**The style, measured.** The 2026-09-26 class-weapon icons (skull, fist, gauntlet, greatsword,
bow, crossbow, firebow, mozambique, rem870, peacekeeper) are EXACTLY three colours with binary
alpha: LIGHT `#E8EEF6`, SHADE `#62779C`, NAVY `#0A1020`; a 7 px outer outline, ~4 px internal part
lines, the lower part of every form in SHADE (light from above), hard pixel edges, 288 x 132, the
weapon pointing RIGHT. The generator reproduces that exactly (a 4x crisp render, 4x4 majority vote
to the palette), so its output holds only those three colours and is byte-deterministic.

**What the bay shows.** 96 x 44 canvas units = 144 x 66 px at 1080p, on the dark gun plate, where
the navy outline disappears and only the LIGHT + SHADE mass reads. Every detail is therefore drawn
to survive a 0.5x sample; three first-pass choices failed that test and were changed (recorded in
the generator): navy hairline strap seams on the staff (read as noise), a navy circuit panel on the
blade (read as a hole), navy bars on the guard arms (read as a ladder).

**The three icons.**
- `i_tod_hud_gun_soulstaff`: the straight iron staff horizontal (butt left), its spiral strap as
  bold SHADE stripes, two raised coil rings, a collar, the riveted socket and the skull upright and
  front-on at the right end: faceted cranium with the model's suture, deep sockets with glowing
  eyes, the jaw hanging open. Upright and front-on is the read that survives 144 x 66 and continues
  the tier-1 skull icon.
- `i_tod_hud_gun_crownstaff`: the same staff (the family read), the studded ring round a smaller
  skull, the sunburst of forged blades (the model's eleven, its low pair opened from 160 to 152
  degrees so they clear the collar), the long spear finial pointing right, the flared collar.
- `i_tod_hud_gun_greatsword` (same name): the Cyber Sword, pommel left: diamond pommel with its
  diamond plate, wrapped grip between ringed collars, the cross guard (reactor-gem boss, flared
  arms ending in three-point winged plates with a diamond inset), the horned blade base, the long
  blade with a SHADE circuit panel in a navy rim carrying the III charge cell and four stepped LIGHT
  traces, the two glow rails into the point. Drawn bolder than the model (guard +-45, blade +-20) to
  hold its weight beside the fist and gauntlet. Never the gold card2 tier_slasher_3 art.

**Wiring (staged, lands in one step).** Two GDT blocks cloned whole from `i_tod_hud_gun_skull`
(`compressed high color`, noMipMaps 1); two zone lines after `image,i_tod_hud_gun_skull`; in
`AetheriumLoadout.lua` four `TOD_NAME_CAT` rows (SOUL STAFF / SOUL STAFF EX -> soulstaff, CROWN OF
THE DAMNED / CROWN OF THE DAMNED EX -> crownstaff) and four `TOD_GUN_CAT` rows (the two staff stems
and the two Soul Pulse cast proxies `tod_necro_pulse2/3`). The image name is built at runtime, so
`lint_tod_assets` GATE A cannot see it; `gun_bay_icons.py --check` (a build gate once landed) checks
the bytes, the 3-tone style, both GDT blocks, both zone lines and every Lua row.

<!-- PACK:BEGIN -->
# Gun-bay icons: Soul Staff, Crown of the Damned, Cyber Sword

## The task

Draw three weapon icons for a game HUD's weapon panel. Each is a flat vector silhouette of one
weapon, drawn horizontally, pointing RIGHT, in exactly the style of the reference icons.

## Deliverables

| File | Size | Subject |
|---|---|---|
| `i_tod_hud_gun_soulstaff.png` | 288 x 132 RGBA | A straight iron staff with a skull on its head end |
| `i_tod_hud_gun_crownstaff.png` | 288 x 132 RGBA | The same staff crowned with a spiked halo round the skull |
| `i_tod_hud_gun_greatsword.png` | 288 x 132 RGBA | The Cyber Sword (replaces the file of the same name) |

## Hard rules

1. EXACTLY three colours plus transparency: light `#E8EEF6`, shade `#62779C`, outline navy
   `#0A1020`. No gradients, no glow, no anti-aliased fringe (alpha is 0 or 255).
2. A thick navy outline (about 7 px) round the whole silhouette, about 4 px between parts.
3. Light from above: the lower part of every form is the shade colour.
4. The weapon points RIGHT (staff head and sword tip on the right).
5. It is shown at 144 x 66 px on a dark panel: keep details bold. No thin lines, no tiny dots.
6. No text, no background, nothing outside the weapon.

## Subjects

- **Soul Staff**: a straight staff, butt cap at the left, a spiral leather strap (draw it as bold
  shade-tone diagonal stripes, like the grip of `i_tod_hud_gun_staff2.png`), two raised coil rings,
  a collar under the head, a riveted socket, and a SKULL seen from the front, upright: cranium with
  a zigzag suture, two deep eye sockets each with a small glowing light eye, the jaw hanging open.
  See `reference/tier2_head.png`.
- **Crown of the Damned**: the same staff. Round the skull, a studded ring; behind the ring a
  sunburst of leaf-shaped forged blades; a long spear finial pointing right. See
  `reference/tier3_head.png`.
- **Cyber Sword**: pommel left. A diamond pommel with a diamond plate set in it; a wrapped grip
  between two ring collars; a cross guard with a round boss holding a diamond gem, each arm ending
  in a three-point winged plate; the blade flares into two small horns at its base, then runs long
  and tapers to a point. Down its middle a dark panel (shade tone, navy rim) with a short III mark
  near the guard and stepped light circuit traces. See `reference/native_oblique.png` and
  `reference/native_hilt.png`. Do NOT draw a gold or plain broadsword.

## Checklist before delivery

- [ ] Three files, exact names, 288 x 132, RGBA.
- [ ] Only the three colours; alpha only 0 or 255.
- [ ] Each icon reads clearly when shrunk to 144 x 66 on a dark background.
- [ ] Each sits beside `i_tod_hud_gun_skull.png` and `i_tod_hud_gun_gauntlet.png` as one family.

## Do NOT

- Do not add text, glow, drop shadows or a background.
- Do not change the canvas size or the pointing direction.
- Do not copy the old broadsword or any gold sword art.
<!-- PACK:END -->
