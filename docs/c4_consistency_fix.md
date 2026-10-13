# C4 full explosion every time — 2026-09-27

**Build status (2026-09-27 15:07:59 Eastern): full build and exact-source deployment passed.** Includes the balcony, crown lights, Necromancer, Fire Bow, C4 and Warrior fixes. Fresh BSP/navmesh/lighting; FF 193,919,232 bytes; 378 captured inputs matched. Evidence: `tmp/crown_alarm_visibility/full_build.log` and `art/crown_alarm/deployment.json`. This supersedes earlier queue/relink notes below. Native visuals and gameplay await the user's playtest; the agent did not launch the game.

The user reported that the huge explosion only appeared about 35% of the time,
especially confusing with a maxed C4 card, and requested consistent large blasts
plus logs. C4 is implemented in `_tod_class_kit.gsc` (Breacher kit).

## Confirmed cause

Archived run: `tmp/elite_tracking/runs/20260927_141825_824_d08b07f5/console_mp.log`.
There are 26 `TIER_PREVIEW kit=c4` entries, all with `card_tier=4`, and matching
26 `C4_BLAST` entries. The preview forces tiers 1, 2, 3, 4 in order:

| Selected tier | Blasts | Visual |
| --- | ---: | --- |
| 1 | 7 | 55% scale, muted |
| 2 | 7 | 70% scale |
| 3 | 6 | 85% scale |
| 4 | 6 | Full large explosion |

No `C4_LOST` or `FX_DROPPED` entries occurred. This establishes a deterministic
developer preview override, not a random choice of explosion animation. The
large donor has normal particle variation, but its emitter spawn counts are
positive; the variant selection was the source of the four different sizes.

## Change and diagnostics

C4 is excluded from the developer tier cycle and always chooses
`explosions/fx_exp_generic_lg`. Every charge gets the existing complete top-tier
presentation: upward fireball, ground fire, impact boom and shake. The previous
request for smaller low-tier C4 art is superseded by this request. The card still
sets charges, damage and damage radius; max-card radius is no longer artificially
reduced by preview cycling. Cluster preview behavior is unchanged.

Each planted charge receives an ID. Dev logs correlate:

- `C4_FX_ARM`: revision, ID, owner, card tier, visual tier 4 and chosen asset.
- `C4_BLAST`: ID, origin, damage tier/radius, hits and host allocation result.
- `C4_FX_PLAY`: ID, host, asset and origin, after the existing 50 ms replication wait.
- `C4_FX_FAIL`: ID and allocation-failure reason, if no host can be created.
- `C4_FX_END`: ID, host and four-second lifetime at cleanup.
- `C4_LOST`: ID and elapsed time if the native explosion provides no position.

These confirm selection and server playback calls, not pixels rendered by the
client. A native visual failure despite ARM/BLAST/PLAY remains a rendering issue
to investigate from the user's next playtest. No extra particles, effect assets,
network fields or per-frame logging are introduced beyond the existing full blast.

## Validation and deployment

`node tools/breacher/test_c4_consistency.js` executes shipping tier selection for
800 throws, all tiers with dev mode on/off, and verifies card radii, unchanged
Cluster preview, delayed playback and correlated logging. It is a guarded build
gate. Arity, same-VM native API and Archer equipment tests pass.

Full build queued with crown, Necromancer and Fire Bow work while BO3 runs.
Live state: `tmp/crown_alarm_visibility/status.json`. No game launch; user tests.
