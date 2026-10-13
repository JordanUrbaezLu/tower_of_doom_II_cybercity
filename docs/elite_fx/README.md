# The elites' effects (PK26) and the haven motes (PK43)

Wave 2 package W2D, 2026-10-05. Source packs: `tmp/asset_prod/packs/PK26-elite-vfx.json`, `PK43-haven-motes.json`.

## What the player sees and hears

| Moment | Before | Now |
|---|---|---|
| A Doppelghast dies (round elite, haven guardian, arena) | A blood spray, then 2.9 s of nothing, then a gore burst that hurts (25 in 128 u) | **THE CHARGE**: from the spray to the blast the body charges up - a red core in the torso swelling to white, an accelerating heartbeat of flashes, sparks rushing in, red arcs, soot, a red light pulsing on the floor, and a rising whine whose thumps land on the flashes. **THE BLAST**: the gore burst plus a flash, needles, embers, a light, and **the hurt zone drawn on the floor** - a wave of beads that stops exactly at the 128-unit radius and an edge ring that glows there |
| A Doppelghast jukes | A plain sidestep | A dark smear along the dodge (charcoal ribbon, soot afterimages, a faint red core) and red sparks, from the clip's frame 11 |
| A Doppelghast swipes | No visual windup | A red-hot claw with a ribbon tracing the swipe and a few sparks, for the clip's own effect window (frames 2-22) - the tell before the hit at 0.6 s |
| A Mangler dies | It lay still and vanished at 3 s | Its cannon arm thuds down (BO6 ground impact at 1.7 s), then at the clip's end it breaks up - flash, fire, hot scrap, spark tails, venting steam, orange arcs, sputtering sparks, smoke, a smouldering light, the BO6 death impact - and the body hides under the flash |
| The haven thresholds and the departure hall's oculus | A zoned Treyarch placeholder (`env/light/fx_light_god_rays_dust_motes`, one `gfx_debug_missing_fx` sprite) | A soft column of lit dust motes drifting down, taking the district's light |

## Where it lives

- Effects: `tools/fxgen/elites/make_fx.py` (GENERATED `share/raw/fx/tod/elites/*.efx`, `--check`, `--selftest`, `--vendor`),
  donors vendored in `tools/fxgen/elites/donor/` (sha-pinned). The motes: the 14th effect of `tools/haven/make_fx.py`
  (`fx_tod_haven_motes`, donor `tools/haven/fx_donors/`).
- Sounds: `tools/fxgen/elites/make_sounds.py` -> `sound/aliases/tod_elite_fx.csv`, `sound_assets/tod/elite_fx/`, and the
  seven BO6 Mangler death wavs restored to `sound_assets/hb/bo6_enemies/` (the R5 purge had archived them as unused).
- Script: `scripts/zm/zm_tod2_cybercity/_tod_elite_fx.gsc` (the one owner; a leaf that imports only
  `tod_ability_fx::burst_at`), hooked from `_tod_doppelghast.gsc` (death_burst, play_juke, attacks) and `_tod_mangler.gsc`
  (corpse_cleanup). The motes: `_tod_atmosphere.gsc` (`level._effect[ "tod_lounge_motes" ]`, which also feeds the
  GENERATED departure-hall FX list).
- Gate: `tools/fxgen/elites/test_elite_fx.js` (hooks at the right moments, the carrier lane, caps, zone, sounds,
  negative controls); `tools/haven/test_haven.js` (the motes). Review sheet: `tools/fxgen/elites/preview.py` ->
  `art/generated/W2D-elite-haven-fx/_review.png` (a schematic, not the engine).

## Knobs

- `TOD_ELITE_FX_*` in `_tod_elite_fx.gsc`. The CLOCK defines (charge / juke / claw / carrier lives / the claw bone) are
  READ by the generator: change one, re-run `make_fx.py` (and `make_sounds.py pick` for the charge length).
- Brightness / size / counts: the tables in `make_fx.py` (`charge()`, `blast()`, `juke()`, `claw()`, `mangler()`).
- The charge whine's mix: `MIX_DB` in `make_sounds.py`; the alias volume in `CHARGE['vol']`.
- `TOD_ELITE_FX_LINKED_MAX` (6): juke / claw carriers alive map-wide; past it the moment plays no effect (logged).

## Logs

`[TOD_ELITE_FX]` (console only, `tod_dev` or `tod_diag`): `INIT`, `CHARGE phase=start|end generation= host= at=`,
`BLAST generation= torso= floor= drop=`, `LINK kind=juke|claw actor= host= tag= secs= live=`, `CUT kind= why=death|pause|carrier_gone`,
`MANGLER generation= at=`, `DROPPED kind= reason=cap|missing_tag|entity_pool`, `SOUND_DROPPED`. The first 12 of each kind
print; the counts keep running. The Mangler adds `[TOD_MANGLER] DEATH_BURST generation= torso=`.

## Open (native checks only the user's playtest can make)

- The impact frame (local +X up, carriers at angles -90 0 0) and the cylinder axis (0 = local X) are read off the stock
  library, not seen in game: if the hurt-zone ring or the flat shock stands VERTICAL, the frame is wrong (flip the
  carriers to angles 0 and the rings to axis 2).
- After the frame-61 ragdoll the server's j_spine4 may drift from the client's ragdoll: the charge could hover a little
  off the body in its last second.
- Sprite sizes are read as radii in the review sheet; the hurt-zone ring is placed by spawn offset (unambiguous units).
