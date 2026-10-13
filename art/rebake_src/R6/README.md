# art/rebake_src/R6 - the pinned inputs of tools/artgen/packs/r6_class_cards.py

These are **build inputs of a generator, not art to edit**. R6 re-bakes the four class draft cards in place (same
names), so it never reads its own output: it reads these copies of the cards as they stood before the pass
(2026-10-05, wave 3), each pinned by sha256 in the generator's `SOURCES`. Its `--check` (a build gate once R6
lands) fails if any of them changes.

| File | What it is | sha256 |
|---|---|---|
| `i_tod_card_class_necromancer.png` | The Necromancer draft card as shipped (docs/179 drop: cartoon skull + cyan beam, retired face) | `fff13f1c62f5d5bd803913c06a91d21984764bdc29a692f45aaecd3ab54c7e37` |
| `i_tod_card_class_assault.png` | The Archer card as PK01 left it (line-art bow, retired face) | `cff7ccb1325a9a48a66ea4648751098105b7052dbe335b64968f51f2c33ba69e` |
| `i_tod_card_class_heavy.png` | The Breacher card as PK01 + R2 left it (R2's Mozambique, retired face) | `01ad3fab98a623b31b3b6b92d9f1f1a7672cf44909c4c8a3a2f21d9efc8f2e7d` |
| `i_tod_card_class_slasher.png` | The Warrior card as PK01 left it (cartoon gold fist, retired face) | `c622470b366f4c9c2c95eae04a7fee1f6f8252342f4d80f4d07833c92b3f7a1e` |

R6 keeps every pixel of these outside the four word slots and the art window (the Theme B chassis), rebuilds the
slots and the window, and re-sets every word in the map's typeface. The render cache it draws the four weapons
from lives in `art/generated/R6-class-cards/src/` (`--render` rewrites it; PyCoD + the BO3 model bins needed).
