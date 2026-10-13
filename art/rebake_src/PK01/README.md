# art/rebake_src/PK01 - the pinned inputs of tools/artgen/packs/pk01_card_text_rebake.py

These are **build inputs of a generator, not art to edit**. The PK01 generator re-bakes five shipped
images in place (same names). So it can never read its own output, it reads these copies of the files
as they stood before the pass, each pinned by sha256 in the generator's `SOURCES`. Its `--check` (a
build gate once PK01 lands) fails if any of them changes.

| File | What it is | sha256 |
|---|---|---|
| `i_tod_card_class_assault.png` | The Archer draft card as shipped (BOW / rule / MAGNUM) | `29b4c59fc8665f29bb75ae4f24f7ebb9abb9fd29af03ee1248b043f7ef9e6a18` |
| `i_tod_card_class_heavy.png` | The Breacher draft card as shipped (MOZAMBIQUE / rule / MR6) | `4346814b2e4e83f1169a1abdcfdaa6f9c5e312241a10a71bd0b4906b89f7d55d` |
| `i_tod_card_class_slasher.png` | The Warrior draft card as shipped (ONE INCH PUNCH / rule / AMP63) | `72d33f32151467e9e9aec7b4f04d3ced7c7662a70d4e22415c509baca2224743` |
| `i_tod_tier_gate_2.png` | The tier-2 floor-gate strip as shipped (Anton, TIER 2 AT FLOOR 10, chevron up) | `52b9c506c5a0a4c4a2396b1d7d8d1f41d699dd574ed2a0107b7d74234539128b` |
| `i_tod_tier_gate_3.png` | The tier-3 strip as shipped (TIER 3 AT FLOOR 30) | `aba60d3301d64a590a82ae82d57ef01a431c11d366ee8d63911c893fdc2a3dc4` |
| `i_tod_card_chassis_namebox.png` | DERIVED: the name box's shared background (see below) | in `i_tod_card_chassis_namebox.sha256` |

## The chassis

`i_tod_card_chassis_namebox.png` is a 560x183 RGBA crop covering rows 763..945 and x 104..663 of a
768x1152 card. It is the background every card on this frame shares: a flat (8, 8, 10) with six
faint hairline scratches and a lit top row.

`python -B tools/artgen/packs/pk01_card_text_rebake.py --derive-chassis` builds it from the 18 cards
listed (and sha-pinned) in the generator's `DONORS`. It takes the median per pixel over the cards
whose text, rules, brackets and inner lines are far from that pixel. Alpha 0 marks the centre band
that every card's text covers; the generator fills that band from a flat fill and three modelled
hairlines (`SCRATCHES` A, B and - since the 2026-10-04 review - C, the line just above the rule that
had been riding down with the names).

`--derive-chassis` is a one-time provenance step. The normal run and `--check` read only this PNG
and its pin. If a donor card is later re-baked, `--derive` refuses (its sha changed), but the pinned
chassis stays valid.

Never hand-edit anything here. To change an output, change the generator and re-run it.
