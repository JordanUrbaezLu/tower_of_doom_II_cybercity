# 202 — THE HAVENS: the safe zones (floors 10 / 20 / 30 / 40)

**Status: v5 (THE PURIFICATION + THE CORRUPTED LOOK: the corrupted dome is its own breached mesh that ratchets, browns out and groans under a throbbing red light; the cleanse is a 4.5 s choreographed convulsion -> collapse -> bloom -> settle with its own effects, sounds, quakes and screen beats) - built on v4 (THE WHOLE HALL, FULL BUILD OK 2026-10-03 17:46); v5 landed 2026-10-04, build pending below; UNPLAYED - the user tests.**
v3 (THE GUARDED HAVEN: evil until you take it; + tweaks #1/#2/#3/#5) was FULL BUILD OK 15:01 (tmp/war_damage/full7.log, -a0's build; .ff 15:01:16) and PLAYED once (floors 40 / 30 / 10 woke; see v4).
v2 (THE HEART, the hall inside the tower) was FULL BUILD OK 2026-10-02 21:35 (tmp/haven_v2/full1.log); its rounded crossing ripple -GscOnly BUILD OK 2026-10-03 04:30.
v1 (a platform beside the landing) was BUILT 2026-10-02 18:51 and never played; v2 replaced it the same evening.

## The request (user, 2026-10-02)

> "Our safe zones on this map need to act more like a safe zone and maybe have like an aura around them ...
> a dome or like a force field that animates when you walk in and walk out. And maybe has a small visual effect
> on your screen ... these safe zones shouldn't be huge, which also means we need to redesign the current safe
> zones. I don't want it to look like map one anymore ... its own unique feel ... match the theme and match what
> the safe zone should actually feel like ... zombies ... 33% slower and ... 33% less damage ... do a complete
> redesign."

The "safe zones" are the four rest stops on floors 10/20/30/40 (TOD1's walled breather lounges until this pass).

## v6 THE WAY THROUGH (user, 2026-10-04, after the first real playthrough): the hall closed in, the machines facing in, the way down across the field, the door sealed until it is taken

> "You must secure the dome area before you move on or else door cannot be bought" ... "perks and machines dont face
> the safe zone inwards. They face it outwards which is just wrong. And the zone has these open areas where you can see
> inside. You shoulnt be able to see until you are on the floor. Also the stairs should go down on the opposit side then
> you come from. So you have to at least cross the dome to continue going down"

### What the player experiences

1. **You do not see the haven until you reach its floor.** Coming down the floor above (its N and E flights run round
   the hall's void) you walk beside solid walls, not handrails over the dome; the loggias' open edges are walls up to
   the stairs over them, so nothing shows from outside the tower either. The first look is through the porch's arch,
   on the haven's own floor.
2. **The old way down is collapsed.** At the porch, the W flight carries on down for one tread and then stops at a heap
   of collapse debris (a clip over it, so it cannot be hopped). The way on is across the hall.
3. **The way down is across the field.** A SUNKEN STAIR is cut into the hall floor along the north side: its mouth at
   the north-centre, between the teleporter and the up-riders' landing, with a lit sill on its lip; ten stock-pitch
   steps (16 up, 24 deep) running west under the floor between two walls; its foot tunnels under the W wall and comes
   out on the W flight's lowest treads, a few steps above the floor's door. Everything stays walkable both ways: whoever
   walks down to a sealed door can always walk back up into the hall.
4. **The door is sealed until the haven is taken.** The floor's door (`enter_lap<floor>`, at the foot of that W flight)
   reads SEALED / SECURE THE DOME ON THIS FLOOR FIRST on the locked card, with no price and no key, and a press only
   gives the refusal sound; the moment the last guardian falls and the haven is purified, the prompt turns into the
   ordinary door prompt (the very string it was minted with) and the heavy-door cue plays at the door.
5. **The machines face the teleporter.** Pack-a-Punch (south-south-east), the upgrade altar (east), the ammo crate
   (west) and the two perk machines (north-east, south-west) stand round the pad with their fronts to it; you use
   them from inside the ring, your back to the pad.

### What changed, file by file

- `tools/haven_layout.js` v6:
  - VEND_POLAR: every machine `face` = its angle + 180 (asserted within 1 degree). PaP 285 deg r 226 (its real buy
    trigger, zm_cwpap's 40 x 40 unitrigger box, r 32, 48 in front), altar 0 deg r 243 (trigger 36 in front, r 64),
    crate 180 deg r 276 (the crate contract: 56 / r 72), perks 50 / 240 deg r 232.
  - PAD_TRIG_GAP 32 between a machine's trigger rim and the pad's (the 64-unit stride rule stays between machines):
    a buyer faces the machine with their back to the pad, and 32 is a whole player, so no spot is in both triggers.
  - TRENCH (the sunken stair), TRENCH_CUT (exported as CUT.trench), the two side walls (one block from the cut's floor
    to rail height, the tower rail's clip over them), the ramp clip on the nosings (`k.rampX`, labelled
    `lap<L> sunken stair ramp` so the geometry lint models it by its treads like every flight), seeds on its steps.
  - DEBRIS on the W flight's tread 11 (a block + a cap + a clip to 300 over the hall floor).
  - ENCLOSE / enclose(postAbove): the loggia's walls from the slab's underside to the next lap's E / N parapets, its
    NE landing, its E flight's first tread and its N flight's last tread; `opts.postAbove` stops the east wall's first
    10 units at the next door's gate post. The galleries' sloped handrails became walls from under the flights up to
    the void's ceiling, with a cyan trim line along their feet.
  - HALL_FLOORS split round the stair; RESPAWN 190 / 215 / 315 / 335 at 205; GUARD_SPOTS 25 / 75 / 105 / 130 / 205 /
    262 / 310 / 335 at 272; the checks for all of it (the facing, the pad gap, the stair's steps, foot, head room,
    mouth and lanes, the debris between the porch's treads and the foot's, the walls' continuity and the trims' ceiling,
    every spot off the stair).
- `tools/gen_tower_map.js`: `boxMinusParts` (addBoxMinus's split, shared) and the haven band's second cut; the haven
  emitter's `rampX`; `opts.postAbove = doorPostAt(lap + 1)`; the floor-number check's second eye on a haven-above
  floor stands where you step out of the stair's tunnel.
- `_tod_haven.gsc`: `door_seal_state(flag)` (-1 / 1 / 0) published as `level.tod_haven_door_seal_fn`;
  `TOD_HAVEN_SEAL_DOORS`. A dark haven seals nothing (a pre-power descent cannot strand anyone).
- `_tod_doors.gsc`: `haven_seal_watch` (the prompt, both ways), the refusal in `buy_trigger_wait`, each trigger keeps
  its own `tod_hint_dest` / `tod_hint_price`; `[TOD_DOOR_SEAL]` logs.
- `PromptDoors.lua`: the SEALED card (locked chassis, no footer, no price; reset for the next door).
- Gates: `test_haven.js` (+ the seal: the pointer, dark / corrupted / booting / taken / other doors, the door wiring,
  the card; 2 more mutants), the layout's own checks, `lint_tod_geometry` (a negative control without the stair's
  treads reads terrace -> base NO), the floor numbers.

### Logs (dev or diag)

`[TOD_DOOR_SEAL] SEALED flag=enter_lap40 ...`, `UNSEALED ...`, `REFUSED flag=... player=...`. The haven's own
`[TOD_HAVEN]` lines are unchanged.

### Not verified (the user's playtest)

The look of the walled hall and the sunken stair in game, the navmesh through the stair (proved by the build's
navmesh gate), zombies following players down it, the sealed prompt and its refusal, the unseal at the purification.

Then, the same evening (v2): "We could give it one more design enhancement run through and also make sure the
teleporter for that floor is actually in the center of the safe zone. And maybe the safe zone can actually be inside
the tower like how the endless tower has trials inside." The retired Endless Spire opened its core at every hub into a
trial hall; v2 does the same at every haven floor.

Then, the same evening (v2): "We could give it one more design enhancement run through and also make sure the
teleporter for that floor is actually in the center of the safe zone. And maybe the safe zone can actually be inside
the tower like how the endless tower has trials inside." The retired Endless Spire opened its core at every hub into a
trial hall; v2 does the same at every haven floor.

## v5 THE PURIFICATION + THE CORRUPTED LOOK (user, 2026-10-04): two states you cannot mistake, one transition worth watching

User: "give it one more look ... make any qol updates or enhancements in this area and any improvements at all. I like
the two states of the dome to be quite different and the transition of purification to be nicely animated with visuals
and nice sounds etc. Lets make this amazing". v4's corrupted dome was the safe lattice in red with one stutter and a
flash between the states; v5 makes the corrupted dome a different object and the cleanse a scene.

### What the player experiences

- THE CORRUPTED DOME is its own BREACHED MESH (`tools/haven/make_dome.py`, `dome_mesh(freq, dark=True)`): a tenth of its
  hexagons are GONE (never the apex, a pentagon or a floor-cut cell; 42 holes at LOD0, 10 at LOD1) and every cell left is
  a CRACKED PANE mapped onto a 2x2 atlas of four tiles (`i_tod_haven_field_dark`, 512 square: a dark smoky pane at alpha
  0.09, a ragged crust seam from 0.42 at its molten lip to 0.80 at the corners, dark veins with hot cores running in from
  the seam and hot spots where they meet it). Its skirt wears the seam. The safe dome is the clean lattice (unchanged).
- IT MOVES AND SOUNDS BROKEN: it turns in RATCHETS (5..14 degrees over 0.22 s, then a hold of 1.6 s - 0.55 s while its
  guardians are up) where the safe dome revolves smoothly; it BROWNS OUT (the new `tod_haven_dome_dark_dim` skin for
  110 ms, every 1.4..4.2 s dormant / 0.5..1.8 s in the fight: a dying tube); it GROANS (3D, from a random point of its
  rim 110 up, two takes behind one alias, every 6..12 s / 3..6 s); its heart throws a REAL RED LIGHT on the hall (a
  dynamic light in the corrupt loop, a slow throb; faster and hotter in THE FURY); the floor sign stutters every 0.9..2.4 s
  in the fight (2.5..5 s dormant); the wake swaps the dormant loop for THE FURY (`fx_tod_haven_fury`: blazing gems, arcs at
  every glint site, embers pouring up, a fast throbbing heart, a soot vortex); every guardian death shakes the floor
  (`Earthquake` 0.14 for 0.6 s). The safe dome keeps its heartbeat pulse and gains a steady cyan light at its heart.
- THE PURIFICATION, ~4.5 s from the last guardian's death, ONE timeline (`cleanse` = the entry, `purge_run` = the clock):
  1. THE CONVULSION (`TOD_HAVEN_PURGE_CONVULSE_SECS` 2.2): the heart STROBES on an accelerating schedule
     (`purge_strobe_steps()`: 0, 470, 860, 1190, 1460, 1680, 1860, 2010, 2130 ms - the dome's own skin strobe
     (`dome_convulse`), the effect's flashes (`fx_tod_haven_convulse`) and the sound's clicks (`tod_haven_purge`) ALL ride
     that one list), arcs snap over the whole sphere in two thickening waves, lightning cracks late, embers blow out of
     the heart, the heart swells white, a soot vortex is drawn into it, the gems flare; the floor QUAKES (0.22, radius
     1100), the dark hum FADES OUT (1.5 s), the sign goes out on every strobe. FLOOR N PURIFYING / THE LAST GUARDIAN HAS
     FALLEN on the floor. Players INSIDE: the veil GRIPS (the breath stops, the darkness holds full) and the screen's
     edges flicker red with EVERY strobe (`TOD_HAVEN_BANNER_STROBE`, sent per step to the players inside).
  2. THE COLLAPSE (`collapse`, wait-free): the field IMPLODES (`fx_tod_haven_collapse`: ~100 beads spawned on the whole
     sphere rush INWARD along their own normals - `runRelToOffset` on a sphere offset - and turn white as they converge),
     a white-hot flash + a one-shot real light flash, a shock ring, a column to the projector, white sparks up, the last
     soot blown out along the floor; the floor kicks (0.5 for 0.5 s). The dome is HIDDEN, the barrier goes, the sign goes
     dark, and every ORDINARY zombie inside DIES (`purge_zombies`: the stock nuke's idiom `DoDamage( health + 666, origin )`,
     no attacker so nobody is paid, `tod_ps_exempt` round it; elites, bosses and guardians are spared; a zombie outside is
     spared). Players inside see BLACK for `TOD_HAVEN_PURGE_VOID_SECS` 0.35 (TodHaven.lua's void: a plain fill, in 40 ms,
     held, out in 260). The convulsion's banner clears.
  3. THE BLOOM (`purify`, wait-free): the field is SAFE from this instant - `fx_tod_haven_cleanse` (re-read as the bloom)
     + the recut `tod_haven_cleanse` (a chord blooming from nothing; the rise is the purge sound's), the safe ambient,
     FLOOR N HAVEN SECURED to everyone (its third argument says whether YOU are on the floor: the FULL white-cyan flash
     for those who took it, the ordinary pulse elsewhere), 500 each, the players inside become members at once (the kill
     tax, the bleed grace, the tint; the darkness lifts with its own cue `tod_haven_dark_lift`), every enemy inside is
     slowed at once; the safe dome INFLATES from a point (`dome_inflate`: `SetScale` 0.06 -> 1 over 0.8 s, eased out, in
     the flash skin) as the sign flickers back in the district's colour.
  4. SETTLE (`TOD_HAVEN_PURGE_SETTLE_SECS` 1.2): flash -> pulse -> base through `dome_visuals`, then the safe hum starts.
- QoL: the darkness lifting is now HEARD (`tod_haven_dark_lift`, 2D, on every lift - leaving a corrupted dome too).

### What changed, file by file

- `tools/haven/make_dome.py`: `DARK_*` constants, `dark_cell_tile` / `dark_cell_atlas` / `dark_tile_uv`, `dome_mesh(freq,
  dark)` (holes + 2D atlas UVs), `build_model(freq, dark)`, the GDT (the atlas as `i_tod_haven_field_dark`, the
  `mtl_tod_haven_field_dark_dim` material at scaleRGB 1.4, `tod_haven_dome_dark` on its OWN bins
  `tod_haven_dome_dark_lod0/1.xmodel_bin`, `tod_haven_dome_dark_dim` + `_dark_flash` as skinOverride twins of it), the
  manifest (`dark_lods` with holes, `dark`, `states.corrupted` = 3 skins).
- `tools/haven/make_fx.py`: reads `TOD_HAVEN_PURGE_CONVULSE_SECS` + `purge_strobe_steps()` OUT OF `_tod_haven.gsc`;
  `heart_light()` (the golden zombie's light recipe) in `ambient` (steady cyan), `corrupt` (slow red throb) and the new
  `fury` (fast); new `convulse` and `collapse` (`inward()` = runRelToOffset); `cleanse` re-read as the bloom. 13 effects,
  every one under the 200-particle budget (fury 150, convulse 136, collapse 172).
- `tools/haven/make_sounds.py`: reads the same clock; `tod_haven_purge` (composed: clicks measured ON the strobe steps,
  louder toward the end; the drone climbing; the suck; the thump + burst; the void's ring), `tod_haven_groan` (`VARIANTS`:
  two files, one alias), `tod_haven_dark_lift`, `tod_haven_cleanse` recut as the bloom. 16 aliases / 17 files.
- `scripts/zm/zm_tod2_cybercity/_tod_haven.gsc` rev 5: the defines above, `spin_forever( h )` (ratchet), `dome_model` +
  `dome_visuals` (the dim skin, the flicker clock), `sign_glitch` by state + `sign_glitch_done`, `groan_loop`, the wake's
  `ambient_start( h, FX_FURY )`, `guard_down`'s quake, the purification (`purge_strobe_steps`, `cleanse` entry,
  `purge_run`, `dome_convulse`, `strobe_tell`, `collapse`, `purge_zombies`, `purify`, `dome_inflate`), `banner`'s SECURED
  near flag, `dark_set( false )`'s lift cue, STATS `purged`. v4's `cleanse_dome` is gone.
- `ui/uieditor/widgets/HUD/AetheriumWidgets/TodHaven.lua`: the void element (a bare black fill over the tint and the
  pulse, under the text), `grip()`, the void chain, banner kinds 4 / 5 / 6, the SECURED near flag.
- `zone_source/zm_tod2_cybercity.zone`: `xmodel,tod_haven_dome_dark_dim` + the three fx lines.
- `tools/haven/preview_states.py`: the corrupted state shows the shipping breached mesh (not a recolour of the lattice).
- Gates: `tools/haven/test_haven.js` (section G THE PURIFICATION; the suite drives cleanse -> collapse -> purify with
  SetScale / Earthquake / DoDamage / StopLoopSound builtins; 529 checks, 53 mutants incl. 13 new), `tools/test_haven_hud.lua`
  (the grip, the strobes, the void, the near flash, outside-the-dome negatives; 8 negative controls).

### Knobs, per symptom (v5)

- The corrupted dome too holey / too whole: `DARK_HOLE_FRACTION` (0.11) in make_dome.py. Seams too heavy from inside:
  `DARK_SEAM_A` (0.42 -> 0.80), `DARK_SEAM_IN` (0.395). Too few / many cracks: `DARK_VEINS`.
- Ratchet too jerky / too tame: `TOD_HAVEN_RATCHET_*`. Brown-outs too often: `TOD_HAVEN_FLICKER_*`. Groans too often:
  `TOD_HAVEN_GROAN_*` (level: `make_sounds.py` SOUNDS 72).
- The red light too strong / weak: `CORRUPT_LIGHT` / `FURY_LIGHT` / `SAFE_LIGHT` in make_fx.py (intensity, radius <= 400).
- The purification too long / short: `TOD_HAVEN_PURGE_CONVULSE_SECS` (re-run make_fx.py AND make_sounds.py: both --checks
  go stale on purpose), `TOD_HAVEN_PURGE_VOID_SECS` (LOCKSTEP TodHaven.lua `VOID_MS`), `_INFLATE_SECS`, `_SETTLE_SECS`.
  The strobe's rhythm: `purge_strobe_steps()` (must climb, accelerate and end inside the convulsion - gated).
- The quakes: `TOD_HAVEN_PURGE_QUAKE` / `_QUAKE_R` / `_SLAM` / `TOD_HAVEN_DOWN_QUAKE`.
- The collapse should spare / kill more: `purge_zombies`' exclusions (`tod_boss_kind`, the elite markers).

### Logs (dev): `[TOD_HAVEN]` (v5 additions)

`INIT rev=5 ... purge=2.2+0.35+0.8/1.2s strobes=9`, `PURGE floor=N phase=convulse secs= guards=`, `PURGE ...
phase=collapse kills=K ms=`, `CLEANSE ... purge_kills=K`, `PURGE ... phase=settled total_ms=`, `STATS ... purged=`.

### The build (v5)

Landed 2026-10-04 12:21 in ONE step (`land_v5.py`: 26 files + three zone lines inside the haven block) between -7a's
Dealer's House build and -5e's Map One migration build (-5e's own attempt died at gdtdb on `//` comment lines in its two
new GDTs; it fixed them and held, and ONE build then carried all three trees). Every build gate ran on the repo after the
landing: 123 gates / 0 failures in 448 s (`tmp/haven_v5/gates_repo.log`).

FULL BUILD OK 12:46 (`tmp/haven_v5/full1.log`; started 12:31:58): `.ff` 12:46:36, FF 233,280,000 B, a FRESH compile +
bake (geom_key saw 8 changed inputs: -5e's `.map` + GDTs; BSP + navmesh 12:40:38, LED 246,277,485 B), NAVMESH GATE OK,
the 8 known-waived linker lines only. Inside it: GSC STRICT LINT OK 139, the three haven `--check`s (13 effects, 17
wavs, the dome), HAVEN GATE OK 529 / 53 mutants, `test_haven_hud` OK (8 negative controls), HAVEN LEDGER OK 41 assets
(37 in v4: + `tod_haven_dome_dark_dim` + the fury / convulse / collapse effects).

Verified after the link (`verify_v5_build.py`, V5 BUILD VERIFY OK): the 12:46:36 ledger carries all 13 `fx,tod/haven/*`,
the 6 dome xmodels, `image,i_tod_haven_field_dark`, `rawfile todhaven.lua` and both scripts; the xmodel ledger shows the
breached mesh compiled with EVERY exported triangle (dark 4752 / 2056, safe 5256 / 2176; LODs lowest detail first);
every haven material row is complete (105-127 B, none name-only); the fresh loaded bank (12:45:15, 171.3 MB) indexes all
17 `tod_haven_*` stems; deployed scripts / ui / zone_source + the GDT / `.map` / `tod_haven.csv` / 47 haven model, fx
and sound files == repo; nothing synced after the `.ff`; no repo input edited after the build start. UNPLAYED - the game
the user ran 12:49-12:56 right after this build was MAP ONE (`Loading fastfile 'zm_tower_of_doom'` in its console, zero
`[TOD_HAVEN]` lines; the archive under `tmp/elite_tracking/runs/20261004_125806_259_c74741c6` carries a NOTE saying so).

SUPERSEDED AS THE TEST `.ff` by session -b6's FULL BUILD OK 13:34:58 (`tmp/dealer_gift/full2.log`; the Dealer's gift,
docs/209; `.ff` 13:33:10, FF 233,681,472 B; geom_key REUSED this build's 12:43 bake; NAVMESH GATE OK; the 8 known-waived
linker lines only). Verified here read-only with the same `verify_v5_build.py` (V5 BUILD VERIFY OK): its 13:33:10 ledger
carries every v5 row (13 `fx,tod/haven/*`, the 6 dome xmodels incl. `tod_haven_dome_dark_dim`, `image,i_tod_haven_field_dark`,
`rawfile todhaven.lua`, both scripts; every haven material row complete), its fresh loaded bank indexes all 17 `tod_haven_*`
stems, deployed == repo for scripts / ui / zone_source + the GDT / `.map` / `tod_haven.csv` / 47 haven files, nothing synced
after its `.ff`, no repo edit after its 13:22:25 start; HAVEN GATE OK 529 / 53 and HAVEN LEDGER OK 41 ran inside it. Still
UNPLAYED: the 13:16 game was Map One as well.

### Not verified (the user's playtest)

The in-game look of the breached dome (the Blender review `tools/haven/preview_states.py` rendered it at 12:57 once the
game closed - `art/haven/review/state_*.png`, `states.json` dome_dark_mesh sha 4a6ff1b3...: a breached red wreck with hot
ragged seams and veined panes against the clean cyan lattice - but it shows the mesh, not the lights, the effects or the
bake), how the
red / cyan heart lights read on the machines, the ratchet and
the brown-outs, the groans' level and spacing, the whole purification's pacing and legibility (the strobe in step with
the clicks, the implosion's direction - `runRelToOffset` on a sphere offset with a NEGATIVE X: stock's blood
explosions (`blood/fx_blood_impact_exp_robot_lg.efx`) use the same pair with a positive X flying OUTWARD, so inward is
the sign flip, but it has not been seen here - the void's length, the inflation), the sound mix of the purge against the bloom, the collapse's kills in a
real horde (and that no elite dies), co-op: who sees the void (inside only) and who gets the full SECURED flash (the floor).

## v4 THE WHOLE HALL (user, 2026-10-03): the field fills the hall, the guardians stay in it, bullets stop at it, the darkness

> "Safe zone should be the entire area. All things should be encompassed by it. So the radius should bigger and also
> the elites are not allowed to leave the dome. They are stuck inside so you must go inside and kill them. And bullets
> cannot go in or outside the dmoe. Until its a safe zone. Then bullets can shoot through and kill things both ways.
> But yes all perks and ammo craztes pap etc should be inside of the dome. Going inside will make your screen dark like
> you are being taken over by the darkness. Not crazy but for sure noticable and sligtly annoying. But of course once
> its a safe zone its fine"

What the user's own v3 run showed (15:34-15:45, archived tmp/elite_tracking/runs/20261003_154548_488_a1bee5db):
floor 40 woke at round 6 and every guardian of every haven ROSE ON ONE SPOT (`GUARD_SPAWN ... at=(-112.889,
-6.823)` three times on 40, three on 30, five on 10: v3's `guard_spot` always chose the one spot farthest from the
player); the player crossed the small field's ring seven times in 25 s and killed the last two guardians from OUTSIDE
it; the cleanse, the kill pay and the slow carriers all worked; zero script errors.

### What the player experiences

1. **The field is the whole hall.** A low dome centred on the hall (92, 92), its floor ring touching all four sides
   (it disappears into the S and W walls and the E and N rails), its crown 272 up: as wide as the hall can hold and
   still pass under the galleries (the next lap's flights) with room to spare. Only the four corners stay outside:
   the porch (the way in) and three corners under the stairs, where the horde climbs out and the field's three
   EMITTER POSTS stand (short lit columns, their gems facing the field).
2. **Everything is inside it.** The teleporter stays at the exact centre; Pack-a-Punch (south), the upgrade altar
   (east), the ammo crate (west) and the two perk pads (north-east, north-west, either side of the up-riders'
   landing) ring the pad, backs to it, faces to the dome. They have to face out: the pad's 110 trigger and the rim
   rule put every vendor trigger 222+ from the centre, and the dome is only tall enough for a machine's body ~270
   from it.
3. **The corrupted field is a wall to bullets.** From the boot to the cleanse a shell of brushes on the dome's
   sphere is solid: bullets, arrows and grenades stop on it in both directions (a crimson ripple + a zap where a shot
   lands); bodies walk through it. Splash, a swing over the rim and every scripted hit are refused across it too, both
   ways (`BLOCK`). The guardians always count as inside their own field.
4. **The guardians never leave.** They rise each on their own spot round the field (eight spots, spread), hunt only
   players INSIDE it, walk back to their spot when nobody is in, and one found outside it (a leap, a chase over the
   rim) is put back on its spot (`GUARD_FENCE`); a stuck one relocates inside (`GUARD_RELOC`). So you must go in.
5. **The darkness.** Step into a corrupted field and the screen is taken over: a near-black smoky veil creeps in from
   the edges over a second (the centre stays fightable), then BREATHES (full, 80%, full, ...) for as long as you stay;
   you hear it take you (a reversed swell swallowed into a low thump, a breath of whispers) and a slow heartbeat under
   a whisper bed while you stay. It lifts the instant you leave or the haven is taken.
6. **The cleanse** is v3's, plus: the barrier goes ("then bullets can shoot through and kill things both ways") and
   the darkness lifts for everyone inside.

### What changed, file by file

- `tools/haven_layout.js` v4: C (92, 92), DOME_R 332, DOME_TOP 272 -> the sphere (S 338.618, its centre 66.618 under
  the floor); membership on the SPHERE (BODY_UP 36, in at S - 12, out at S + 6, a z band -48 .. +312); VEND as polar
  placements round the pad; three short POSTS (POST_H 160, collars at 132) in the SE / NE / NW corners; six HALL_RISERS
  in the corners outside; eight GUARD_SPOTS at 272; RESPAWN at 205 in the two open quarters; the PROJ_RING shrunk to
  [96, 112] (under the core); `ceilingAt()` (the next lap's treads, its NE landing, the galleries' handrails) and the
  asserts that keep the dome 24 under all of it, past the walls only where they are solid, past the rails only under
  their visible 39; `barrierBrushes()` (24 x 6 frustum facets, 8 thick, from 40 under the floor to the crown);
  `haven_barrier_name()` and the sphere data in the generated `_tod_breather_data.gsc`.
- `tools/gen_tower_map.js`: `polyBrushText()` + one script_brushmodel per haven floor (`tod_haven_barrier_<floor>`,
  144 brushes in `tod_haven_barrier`).
- `tools/haven/make_dome.py`: the bigger dome (Goldberg 10 / 6), `i_tod_haven_darkness` (the darkness veil), the
  `tod_haven_barrier` material = the stock `clip_weapon_noimpact` block copied whole from the tools' clip GDT +
  `missileClip 1` + `noPenetrate 1` (refuses a donor whose flags moved).
- `tools/haven/make_fx.py`: glints on height rings above the floor, the volumes scaled to the field, the posts' gems,
  `fx_tod_haven_deflect` (the rounded rule applies).
- `tools/haven/make_sounds.py`: `tod_haven_dark_in`, `tod_haven_dark_breath` (2D, NONLOOPING: the module re-plays
  it, so nothing can stick), `tod_haven_deflect` (3D); the ten v3 wavs byte-identical.
- `_tod_haven.gsc` v4: the sphere membership, `barrier_set` (boot on / cleanse off), `side_of` / `barrier_blocks` /
  `actor_damage_gate` (wraps `level.callbackActorDamage`) / `level.tod_haven_barrier_fn`, the spread `guard_spot`,
  `guard_target_ok` (inside only), `guard_fence` / `guard_home` / `guard_reloc`, `dark_set` / `dark_breath`,
  `shot_watch` / `deflect_feedback`.
- `_tod_bosses.gsc`: `boss_player_damage` refuses an enemy's hit across a corrupted barrier (first lane).
- `_tod_doppelghast.gsc`: `reloc_point` asks `self.tod_reloc_fn` first (the Mangler relocates through it too).
- `TodHaven.lua`: the `TodHavenDark` layer under the tint (in 900 ms, breathe 1800 ms each way, out 600 ms); the
  corrupted tint 0.30 -> 0.24.
- The zone: `fx,tod/haven/fx_tod_haven_deflect`, `image,i_tod_haven_darkness` (the barrier material rides the BSP).
- Gates: `test_haven.js` (453 checks, 41 mutants), `test_haven_hud.lua` (5 negative controls).

### Knobs, per symptom (v4)

- The dome too low / too high: `DOME_TOP` (the asserts stop it under the galleries); too narrow: `DOME_R` (the asserts
  stop it at the walls and rails).
- "I'm inside but the screen says outside" (or the reverse): `IN_PAD` / `OUT_PAD` (the sphere's hysteresis), `BODY_UP`.
- The darkness too strong / too weak: `DARK_CENTRE` / `DARK_EDGE` in make_dome.py (the image), `DARK_HI` / `DARK_LO`
  in TodHaven.lua (the breath); too annoying: `TOD_HAVEN_DARK_BREATH_SECS` (how often the heartbeat re-plays) or the
  alias volumes in make_sounds.py.
- Guardians yanked back too eagerly: `TOD_HAVEN_FENCE_OUT` / `TOD_HAVEN_FENCE_SECS`.
- Too many deflect ripples: `TOD_HAVEN_DEFLECT_GAP_MS`.

### Logs (dev): `[TOD_HAVEN]` (v4)

`INIT rev=4 ... sphere= in3= out3= barriers=4 gate=1`, `BARRIER floor= solid=`, `GUARD_SPAWN ... spot=`,
`GUARD_FENCE`, `GUARD_RELOC`, `DARK player= on|off`, `BLOCK` (the first 12 refused hits), `DEFLECT` (the first 12
barrier shots), `BARRIER_MISSING` (an old map), and the STATS line's `blocked= deflects= fenced= dark=`.

### The build (v4)

FULL BUILD OK 17:46:00 (tmp/haven_v4/full1.log, started 17:31:09): .ff 17:44:19, FF 229,771,520 B; a fresh map
compile + navmesh + bake (LED 239,692,504 B); the 8 known-waived linker lines only. Inside it: every pre-build gate
(HAVEN GATE 453 / 41 mutants, test_haven_hud, the three --checks, GSC strict lint, lint geometry), NAVMESH GATE OK,
then HAVEN LEDGER OK 37 and every other post-link ledger. Checked after it:

- the 17:44:19 ledger carries the five v4 scripts, `i_tod_haven_darkness`, `fx_tod_haven_deflect` and
  `todhaven.lua`; all 13 `tod_haven_*` stems are in the fresh loaded bank; every haven input deployed = repo and
  nothing synced after the .ff;
- THE BARRIER IS IN THE BSP: four `tod_haven_barrier_<floor>` script_brushmodels (floor 10 = `*99` at (92, 92,
  3764)); its material's compiled contents are 0x200020c0 = shot clip (0x2000) + missile clip (0x80) + 0x40, with no
  solid bit, no player clip (0x10000: `clip_player` carries it) and no AI clip (0x20000: `clip` carries it);
- THE HALLS STAYED WHOLE: the navmesh lint's descent check already requires one walk component per band of the
  tower (the halls are in it), and a direct probe of the compiled mesh (the lint's own decoder) puts all 37 hall points
  per floor (the pad, rings at 140 / 250 / 300 in eight directions, the eight guardian spots, the four respawns) on
  that floor's walk component on all four floors.

Found on the way and fixed before the build: `verify_tower_design.js` counts the barrier material as a tool surface;
the veil image is `i_tod_haven_darkness` (an `_dark"` literal in a Lua file reads as a dark-card plate to
`lint_tod_assets` GATE C); `tools/run_build_gates.py` now runs all 112 gate lines (it skipped every captured-output
line before).

### Not verified (the user's playtest)

The barrier's collision is a copy of the stock weapon clip with missile clip and no penetration added, and its
compiled contents carry exactly the shot-clip and missile-clip bits (above): that the engine lets bodies through and
stops bullets, arrows and grenades at it is what those bits mean, not yet seen in game. Whether a guardian's own melee reaches over the rim (the damage lane refuses it either way), how the
darkness reads in the real lighting, and the big dome's look from inside and from the galleries are the user's to
judge.

## v3 THE GUARDED HAVEN (user, 2026-10-03): two states - evil until you take it

> "And actually a huge change I want is the dome should be evil at first have doppleghast inside and a couple
> manglers. You must kill them and then the area turns into a safe zone. So you must defeat this boss area to take
> it. No effects or safe visuals and all that until you defeat those elites. So two distinct states. One when its
> not safe and one when it is after defeating them."

Plus, the same morning, the four tweaks picked from the review list ("Lets do 1,2,3,5"): **#1** the slow made
visible on the enemy it slows, **#2** the spawn calm only inside the field, **#3** a slower bleed-out inside the field
(bars in step), **#5** a glowing floor-number sign per hall in the district's colour.

### What the player experiences

1. **The power wave boots the dome CORRUPTED.** The same stutter and flash as before, then a **crimson lattice**
   (`tod_haven_dome_dark`, the field texture's dark twin), a **dark hum** (`tod_haven_hum_dark`, a throbbing detuned
   drone, seamless by construction), **the corrupt ambient** (`fx_tod_haven_corrupt`: the gems smoulder red, embers
   drift up through the field, soot crawls its floor, red arcs crawl the lattice, the projector drips red, a dark
   heart glows at the centre) and **the floor sign in red, glitching** (`tod_haven_sign_N_dark`, a stutter every
   2.5-5 s). The corrupted field does NOTHING: no slow, no damage cut, no kill tax, no ripple, no sound on a crossing.
   Standing inside it your screen's edges go **red** with **CORRUPTED HAVEN** and **DEFEAT THE GUARDIANS - N LEFT**.
   Its **teleporter pad is dead** (`^1defeat the guardians`; floor 40's Battle Arena gate refuses the same way).
2. **The guardians wake.** The first player to come within the wake band (640 round the heart: the hall, its porch,
   the galleries over it; never a player one floor down, never a downed one) convulses the field: a red shock ring, a
   dark flash, embers blown out of the heart, every gem flaring (`fx_tod_haven_wake`), a sub boom with a falling snarl
   (`tod_haven_wake`), the banner **FLOOR N GUARDIANS RISE - DEFEAT THEM TO SECURE THE HAVEN** to everyone on that
   floor. Then the roster rises INSIDE the field on a ring 150 from the heart (`haven_guard_spots`, the spot farthest
   from the nearest player), 0.6 s apart, each through its own ghosted tell: floor 40 **1 Doppelghast + 2 Manglers**,
   30 the same, 20 **2 + 2**, 10 **2 + 3**; a party of three or four gets one more Doppelghast. A guardian
   Doppelghast has 8 round zombies of HP, a guardian Mangler 6 (the round director's are 5). A full actor pool
   denies a spawn (3 slots are kept for the horde) and the haven retries every 2 s for up to 60 s, then wants only
   what it raised - a full pool can never leave a haven untakeable.
3. **The fight.** The guardians hunt **their own floor only** (`tod_hunt_filter`, honoured by `_tod_doppelghast` and
   `_tod_mangler`'s `hunt_target`: the leash band is 1,100 round the heart, from 200 below the floor to the next
   lap's landings 620 above). A player who runs a floor down is not followed; the guardians **walk home** to their
   spots (`tod_hunt_home`). One that still ends up past the leash band for 3 s is pulled back to a guardian spot
   (`guard_leash`, a red crack at the spot). Every guardian death **cracks the dome** (a red flash, arcs snapping
   over the field, sparks; `tod_haven_guard_down`) and the banner says **GUARDIAN DOWN - N LEFT**; the red tint's
   line counts down for anyone inside. Their bars are the elite red bars; their kills pay the elite purse as ever.
4. **THE CLEANSE.** The last guardian falls and the field purges **white-cyan**: a big flash at the heart, a cyan
   shock ring, light racing up to the crown and a column up to the projector, sparkles washing over the whole dome,
   the last red embers dying as they fall (`fx_tod_haven_cleanse`); a rising sweep into a bright chord with a long
   shimmering tail (`tod_haven_cleanse`). The dome **stutters from crimson to cyan** (six quick swaps between the two
   flash skins) and settles into the safe field; the dark hum stops and the field's hum starts; the corrupt ambient
   gives way to the safe one; the sign goes out and **flickers back in the district's colour**. Everyone, anywhere,
   sees **FLOOR N HAVEN SECURED - SAFE ZONE ONLINE - ENEMIES SLOWED - DAMAGE REDUCED** with a cyan flash and is
   paid **500**. Players standing inside become members of a safe field at once (the kill tax, the bleed grace, the
   cyan tint in place with a pulse); every enemy inside is slowed at once and gets its crackle. The pad and the arena
   gate come alive on their next tick.
5. **The safe field** is v2's, plus the four tweaks: **(#1)** an enemy inside wears **thin cyan arcs round its body
   and frost sifting off it** (`fx_tod_haven_slowed` on a small carrier linked to it, at most 10 per field at once;
   the rest are slowed without one); **(#2)** the x1.19 spawn-delay rest applies only while a living player stands
   **inside** a taken field (`level.tod_haven_calm_fn`) - the loggia, where kills pay in full, calms nothing;
   **(#3)** a player downed inside bleeds out **1.5x slower** (`n_bleedout_time_multiplier`, held through the down
   even if the membership drains, so stock's early cut-off never fires) and both HUD bleed bars drain at that rate
   (`tod_haven_bleed`, a four-player mask like the ARCHMAGE bars, `TodHealthTint.BleedoutMs`); **(#5)** the sign
   reads **FLOOR N** in the district's colour (blue 10, green 20, orange 30, yellow 40).

### The module's two states (`_tod_haven.gsc`)

`h.live` (booted), `h.safe` (taken), `h.state` = `dark` -> `corrupt` -> `fight` -> `safe`. `haven_at()` counts any LIVE
field (the HUD shows a corrupted one too); every gameplay effect asks `h.safe`: `dr_for`, the kill tax (`player_enter`),
the bleed grace, the slow (`ai_update`), the sanctuary test `point_inside_live` (the hunt and the ambush may use a
corrupted hall), the calm (`calm_any`). `point_locked( org )` (the pad / arena lock) is the HALL box, not the field: a
dead pad reads as dead from the whole hall. `wake_watch` (0.25 s) fires `wake()`; `spawn_guardians` raises the roster
through the elite modules' public spawners (`tod_doppelghast::spawn_hunter`, `tod_mangler::spawn_at`, the Mangler's HP
overridden after); `guard_watch` -> `guard_down` -> `maybe_cleanse` (`cleanse_due`) -> `cleanse` (wait-free, so the gate
runs it) + `cleanse_dome` (the stutter + the hum swap). `tod_haven( inside, flags, state, left )` now carries four
ints; `tod_haven_state( kind, floor, left )` is the banner; `tod_haven_bleed( mask )` the bars.

### The art (generated)

| what | tool | files |
|---|---|---|
| the corrupted field strip + 2 dark skins | `tools/haven/make_dome.py` | `i_tod_haven_field_dark`, `mtl_tod_haven_field_dark[_flash]`, `tod_haven_dome_dark[_flash]` |
| the 8 floor signs (4 floors x safe/dark) | `make_dome.py` (from `source_data/tod_ui_images/_sheets`, the typeface) | `i_tod_haven_sign_N[_dark]`, `mtl_tod_haven_sign_N[_dark]`, `tod_haven_sign_N[_dark]` on one 360x180 quad |
| the 5 new effects | `tools/haven/make_fx.py` | `fx_tod_haven_corrupt`, `_wake`, `_guard_down`, `_cleanse`, `_slowed` |
| the 4 new sounds | `tools/haven/make_sounds.py` | `tod_haven_hum_dark` (loop), `_wake`, `_guard_down`, `_cleanse` |
| the anchors | `tools/haven_layout.js` -> `_tod_breather_data.gsc` | `haven_guard_spots`, `haven_wake_*`, `haven_leash_*`, `haven_sign_org/yaw` |

The sign textures are composed from the glyph sheets and recoloured by luminance (the face, the 3D extrusion and the
outline keep their relationship), with a soft glow and a fine scanline; the dark ones carry glitch slices. Both are
1024x512 (POT, mips on) on a 2:1 card hung one unit proud of the hall's S wall above the liner (`SIGN` in the layout,
asserted clear of the pylons and the galleries' slot). `scaleRGB` 5 (safe) / 3.5 (dark) is the one brightness knob.

### Knobs, per symptom (v3)

| symptom | knob |
|---|---|
| the guardians are too many / too few | `TOD_HAVEN_GUARD_D_*` / `_M_*` per floor, `TOD_HAVEN_GUARD_PARTY_D` |
| a guardian dies too fast / too slow | `TOD_HAVEN_GUARD_DOPPEL_UNITS` / `_MANGLER_UNITS` (round zombies of HP) |
| they wake too early / too late | `WAKE_R` / `WAKE_Z` in `tools/haven_layout.js` (regen) |
| they follow too far / give up too soon | `LEASH_R` / `LEASH_Z` (regen); `TOD_HAVEN_LEASH_SECS` |
| the purse | `TOD_HAVEN_CLEANSE_PTS` |
| the corrupted dome too dim / too hot | `DARK_BRIGHT` in make_dome.py; `PALETTES['dark']` |
| the sign too dim / too hot | `SIGN_BRIGHT` / `SIGN_DARK_BRIGHT` in make_dome.py |
| too many crackles on a horde | `TOD_HAVEN_SLOW_FX_MAX` |
| the bleed grace | `TOD_HAVEN_BLEEDOUT` (LOCKSTEP `TodHealthTint.lua` BLEED_MULT) |

### Gates (v3)

`tools/haven/test_haven.js` (the two states through gsc_eval: the corrupted field does nothing, the wake raises the
roster inside the field with the hunt filter, the count comes down, the last one cleanses, the bleed grace is held
through a down, the slow carriers cap; 29 mutants), `tools/test_haven_hud.lua` (both states + the three banners, 3
negative controls), `tools/test_archmage_health.lua` (the bleed mask per player), `tools/test_ambush.js` (the rest is
the field), the elite modules' own gates, `make_dome.py --check` (now 11 images, 13 materials, 13 models), `make_fx.py
--check` (9 effects), `make_sounds.py --check` (10 sounds), the post-link ledger (`--ledger`: 35 assets). The teleporter's own
harness (`tools/teleporter/test_states.js`) evaluates the shipping `refresh()` and now stubs `pad_lock_reason_at` and checks
lock reason 3 (dark pad, the guardians hint, no chase host) - it is the gate that caught the first landing.

### Logs (dev): `[TOD_HAVEN]` (v3 additions)

`BOOT ... state=corrupt guards=Nd/Nm`, `WAKE floor= by= guards=`, `GUARD_SPAWN floor= kind= hp= at= target= n=`,
`GUARD_DENIED floor= kind= why=actor_reserve|no_target|spawn_failed`, `GUARD_GIVE_UP`, `GUARD_LEASH floor= kind= from=
to=`, `GUARD_DOWN floor= kind= killer= down= left=`, `CLEANSE floor= secs= guards= pay= players_in= ai_in=`, `SIGN
floor= state=dark|safe`, `SLOWFX floor= n= on=`, `BLEED player= on mult=|off`, and `STATS` now carries the state per
busy haven plus `guards=`, `cleansed=`, `slowfx=`. The pad says `DENY ... lock_reason=3`; the arena `DENY reason=haven_corrupted`.

### The review (Blender)

`tools/haven/preview_states.py` renders the two states from the porch, the north loggia and the gallery above
(`art/haven/review/state_{corrupt,safe}_*.png`): the crimson field with the red sign and the guardians' spots marked
inside it, against the safe field with the blue sign. Approximate emissive view, no bake, no effects.

## What the player experiences

1. **Coming down the tower**: on the flights above a haven floor (the next lap's E and N flights) the inner rail is a
   sloped handrail over a void: the tower's core is OPEN below you, and the field glows in the hall at its bottom.
2. **Before the power**: the hall is dark with a dead hex lattice at its heart.
3. **The power wave** (`_tod_fall::power_wave`, top down): as the wave passes a haven floor, its dome **boots** —
   an electrical stutter, a flash at the centre, light racing up the field, the three emitter gems on the pylons
   burst, the ignite sound, then the field's hum. A fallback boots any dome the wave never reached (15 s after
   `power_on`).
4. **Approach**: on the floor's SW landing (or the W flight's last treads) an **archway** opens east in the old
   core's wall; a stepped **porch** (the spire hall's fan, every step 12) leads up into **the hall**: the force
   field at its heart with the **teleporter at its exact centre** (the Battle Arena gate on floor 40), three
   floor-to-ceiling **emitter pylons** at its edge, and the machines round the hall in an L-shaped **loggia** under
   the next lap's flights: Pack-a-Punch, the Heavenly Altar and the ammo crate on the east, two perk pads on the
   north, every one facing the field and standing **outside** it — shopping is a step out of the safe zone.
4. **Walking in** (from ANY side - the field stands free in the hall): a ROUNDED RIPPLE where you cross the
   field: a small flash at the point, then rings of light running outward OVER THE DOME'S CURVE, sparks streaking
   along its surface and a crackle (other players see it; it fades out near your own camera so it never flashes in
   your face), the dome flashes, the enter sound plays at the field, and your
   screen's edges take the field's cyan tint with a brief bright flash. **SAFE ZONE** rises at the top of the
   screen in the map's typeface; the first three times it adds **ENEMIES SLOWED - DAMAGE REDUCED**.
5. **Inside**: zombies and elites move **33% slower** (`TOD_HAVEN_SLOW` 0.67); you take **33% less enemy damage**
   (`TOD_HAVEN_DR` 0.67). Each hit the field cuts flickers your screen tint and plays a small glassy tink.
   A zombie forcing its way in sets off the same rounded ripple in the field's hostile red, tighter, with
   red-orange sparks thrown off the field and a crackle. The dome breathes (a soft
   pulse every 4.8 s) and turns slowly (one revolution per 96 s).
6. **Walking out**: the rounded ripple where you leave, the exit sound, one last flash of your screen's edges as the tint drains.
   Leaving by a teleport or by dying drains the tint silently; arriving inside by a respawn skips the world
   ripple and the sound but still gives your screen the flash and SAFE ZONE (you need to know where you are).

## The layout, v2 THE HEART (one source: `tools/haven_layout.js`)

Every haven sits on an EVEN lap (absolute even-frame coordinates; `m` = the floor's mid-landing top, the hall floor).
At a haven floor the **core column stops under the hall floor and resumes 576 higher** (`VOID_H` = the next lap's NW
landing, two band seams up). `gen_tower_map.js`'s core-band loop (`corePieces`, `HAVEN.CUT`) keeps the core's **S and
W faces as 20-thick walls** cut from the same seven band pieces, so the S and W flights outside read exactly as before
and the floor-20 Dealer display keeps its wall; the W wall is open below the arch top over the porch, and the column is
cut down to `m - 64` under the porch fan so every fan cell sits one step above its tread.

| piece | where | notes |
|---|---|---|
| the hall floor | x[-236,256] y[-236,256] (velvet deck) | over the old core; the porch fan carved out of its SW corner |
| the loggia | E arm x[256,416] y[-236,416], N arm x[-236,256] y[256,416] (district deck) | under the next lap's E / N flights (188-368 headroom), railed to the parapet line |
| the field | centre (32, 32), floor ring radius 220 (`DOME_R`), a sphere of radius 229.1 centred 64 up, 293 tall | 45 off the tower axis so the porch fan stays outside its ring and the S / W walls clear it |
| the teleporter | the field's centre | transit `spurX/spurY` = -32/-32 (odd-frame convention); up-riders land 208 north, still inside the field |
| the porch | x[-256,-160] y[-224,-96], 4 rows x 3 cells | treads 12..16 of the W flight step up into the hall through the archway (y[-236,-96], lintel at 176-192) |
| the pylons | NE (216,216), NW (-152,216), SE (216,-152), 40 square, floor to ceiling | lit collars at 180-212 carry the emitter gems; each stands under a gallery's inner edge |
| the galleries | the next lap's E and N flights round the void | a sloped graphite handrail per flight (30..42 over each tread, a cyan cap line) over stepped clip guards |
| the ceiling | the core band two laps up | a projector pyramid over the teleporter and a projector ring (r 180-196) |

The machines (measured footprints, `VEND`; each faces the field, every trigger rim clears the next by a stride,
`MIN_TRIG_GAP` 64, and no vendor trigger or body is inside the field): Pack-a-Punch (364,-120), the altar (393,100),
the ammo crate (374,336) — the E loggia; perk pads (130,382) and (-110,382) — the N loggia. Six hall risers stand
outside the field (none on the porch), 165+ from the arrival; the four co-op respawns stand inside it round the
teleporter. A fitted box reflection probe covers each hall.

Everything the scripts need is **GENERATED** into `_tod_breather_data.gsc` by `gen_tower_map.js` from this file:
`haven_center/radius/in_r/out_r/sphere_r/sphere_c/top/entry_dir`, the perk pads (`haven_perk_org/yaw/front`), the
furniture anchors (`pap_*`, `station_*`, `crate_*`), the pad (`tp_pad_org/tp_arrival_org`), the room box
(`lounge_index_at`, z band -64..+160 so the next lap's E flight is not "in the lounge"), the emitter gems
(`haven_gem_offsets`), the bears (`secret_bear_org/yaw`) and the ambient anchors (`haven_motes_org/vent_org`); the
Battle Arena data gains `chamber_r()` (floor 40: the chamber IS the field, the gate at its centre, "everyone inside"
= inside the field). Never type a haven coordinate in GSC.

v1 (THE T, a 512-square dome platform off the SW landing with a threshold, a spur and a pad platform) is in git
history and CHANGELOG 18:29; it was built and never played.

## The field (`scripts/zm/zm_tod2_cybercity/_tod_haven.gsc`)

- **Membership**: every 0.1 s every player and enemy AI is tested against each live dome (horizontal distance
  to the centre + a z band of floor-48..floor+320) with **hysteresis**: in once within 234 (`haven_in_r`), out
  only past 250 (`haven_out_r`), so standing on the ring never flickers.
- **The slow**: an enemy inside carries `self.tod_safe_mult = 0.67`. `_tod_zombie_speed` multiplies it into the
  horde's ONE rate line (`apply_speed_for_round`), the elite slow lanes (`slow_elite` / its expiry) and
  `_tod_bosses::boss_pause_watch`'s restore; the Doppelghast and Mangler chase loops read it while they move
  (their attacks keep their timing). The edge re-applies the rate at once; an elite inside is re-asserted every
  tick (a bamf end or a drop reveal writes a bare base rate) — never while a world pause, the drop-in or a menu
  freeze owns the rate (`elite_rate_owned`).
- **The damage cut**: `level.tod_safezone_dr` (→ `dr_for`) is folded into BOTH player-damage lanes in
  `_tod_bosses` (the normal fold beside DMG REDUCTION and the Panzer-melee short-circuit), for **enemy damage
  only** (never a fall, never self-damage). It multiplies with DR, the mage aura and the armor cards.
- **The hunt** (`_tod_stray`) never raises a relocated zombie inside a live field (`level.tod_haven_inside_fn`):
  the horde has to walk in through it.
- **Zero new clientfields** (the clientuimodel pool is full): the HUD rides the eventstrings `tod_haven`
  (inside, flags: bit 0 = crossing pulse, bit 1 = hint line) and `tod_haven_hit`, re-sent every 2 s to hydrate a
  rebuilt HUD (a re-send never re-pulses); world feedback rides short-lived `tag_origin` carriers.

## The kill pay (user 2026-10-02: "Kills inside a zone are at 25% money. As well to avoid players from just sitting in zones")

- A player standing inside a powered dome carries `tod_haven_pay` = `TOD_HAVEN_KILL_PAY` (0.25), set on the way in and
  cleared on the way out (death and a teleport out included). Every payout of KILL money to them goes through
  `_tod_haven::kill_pay`: the stock kill money (`_tod_upgrades::zombie_death_score`), BOUNTY's bank (its popup preview
  too), the elite purse (`grant_elite_reward`: the killer, or the owner of the companion that got it), a companion's
  kill paid to its owner, a Necromancer helper's swing kill. Where the PAYEE stands counts: shooting out of a dome
  pays a quarter, shooting into one from outside pays in full.
- Banked to exact tens (stock rounds every award UP to ten; a flat quarter of 60 would pay 20). Over a stay the
  player is paid exactly a quarter; Double Points still applies on top.
- The score popup asks `kill_preview` (read-only, the same bank) in every arm, right before Double Points, so the
  number on screen is the money banked. The SAFE ZONE hint's second line says KILLS PAY 25 PERCENT (first 3 entries).
- Not cut: hit points (10 a hit; not kill money), the luck bar and mana from kills, the team boss rewards (the Panzer
  is off under ONLY ZOMBIES; the Keeper's arena and the Dealer's crown hall have no dome).

## The art (all generated; re-run, never hand-edit)

| asset | generator | notes |
|---|---|---|
| `tod_haven_dome` / `_pulse` / `_flash` | `tools/haven/make_dome.py` | a Goldberg (true hex) dome, two shells, fan-UV'd cells over ONE strip texture (`i_tod_haven_field`), `lit_emissive_transparent`, scaleRGB 4 / 7 / 13 via `skinOverride`; LOD1 past 2600 u; no collision. SEE-THROUGH: a thin bright lattice line (alpha 0.85 at the border), a faint halo (0.10) and nearly clear cells (0.018), so a player inside sees the horde coming (`FIELD_*`) |
| `i_tod_haven_vignette` | `tools/haven/make_dome.py` | 1280x720 white art (tinted in Lua): a rounded-rect edge glow + the dome's hex lattice + a fine scanline; BC7, no mips |
| `fx_tod_haven_ambient/cross/push/boot` | `tools/haven/make_fx.py` | built on the sky fleet's builder through the lucky set's helpers; every big sprite near-fades so the crosser never gets a flash in the face. THE ROUNDED RULE (2026-10-03): every sprite template is a camera-facing billboard, so the crossing ripples are rings of small beads placed ON the field sphere - a circle on a sphere is flat, so each ring is one cylinder spawn round the outward normal (`spawnOffsetCylindricalAxis` 0) in the plane x = -SR (1 - cos a), radius SR sin a; no sprite wider than `FLAT_MAX` 48 |
| `tod_haven_enter/exit/push/absorb/ignite/hum` | `tools/haven/make_sounds.py` | seeded synthesis + the stock ritual-barrier loop for the hum; `sound/aliases/tod_haven.csv` |
| HUD widget | `ui/.../TodHaven.lua` | the first child of AetheriumHud (every readout draws over it); hidden with the HUD (scoreboard, menus, the card-deal veil) |

## Knobs, per symptom

| symptom | knob |
|---|---|
| the slow / the damage cut feels wrong | `TOD_HAVEN_SLOW` / `TOD_HAVEN_DR` (`_tod_haven.gsc`; the gate pins both at 0.67 — change the gate with them) |
| the screen tint too strong / weak | `IDLE_A` 0.34 in `TodHaven.lua`; the flash `PULSE_A` 0.72 |
| the dome too bright / dim | `BRIGHT` in `make_dome.py` (base 4 / pulse 7 / flash 13), re-run + FULL build |
| the dome hides what is outside / reads too faint | `FIELD_*` in `make_dome.py` (the cell / halo / line alphas across a cell; the first cut's 0.42 halo over the outer 40% of every cell read as a wall), re-run + FULL build |
| sitting inside still pays too well / too little | `TOD_HAVEN_KILL_PAY` 0.25 (`_tod_haven.gsc`; the gate pins it - change both) |
| the hint line shows too often | `TOD_HAVEN_HINT_ENTRIES` 3 |
| standing on the ring flickers | `IN_PAD` / `OUT_PAD` in `haven_layout.js` (regen) |
| the hall too dark / bright | `lights()` in `haven_layout.js` (the key over the field, the loggia pools, the pylon spills), regen + FULL build |
| a machine in the wrong spot / facing | `VEND` in `haven_layout.js` (the asserts re-check rims, floor, field and arrival), regen + FULL build |
| the gallery handrail blocks / exposes too much | `GAL_TOP` 42 (over the nosing line), regen + FULL build; the guards are the stepped clips |
| the hum too loud | `SOUNDS['tod_haven_hum']` volume in `make_sounds.py` |
| the dome boots too late / never | `TOD_HAVEN_WAVE_REACH` 240, `TOD_HAVEN_FALLBACK_SECS` 15 |
| the crossing ripple too big / small / fast / faint, or too dotty | `CROSS_RINGS` / `PUSH_RINGS` in `make_fx.py`: per ring (angle on the sphere, beads, delay ms, bead size, peak alpha); more or bigger beads merge into a band (the effect's particle budget is 200; cross is 178). Re-run `make_fx.py` + a -GscOnly build |
| the hall's bounce light, or its cost (each hall probe = 28.5 MB of LED, ~7 MB of pack) | the `probe lap<N> haven hall` entity in `gen_tower_map.js` has no `resolution` key, so it bakes at the def's 4x: `kv('resolution','2x')` cuts its grid by 8; or shrink `PROBE.half` in `haven_layout.js` (regen + FULL build). Measure with the LED section table, never by guessing |

## Gates

- `tools/haven/test_haven.js` (build, every build): the numbers, lockstep (generated data ↔ layout ↔ dome
  manifest), wiring (zone, precache, eventstrings, Lua flags, aliases + wavs, effects, GDT, sync, main, HUD,
  build gates), the hooks in every consumer, the **shipping module run through `gsc_eval`** (membership +
  hysteresis + z band, the field point, the damage cut and its throttled tell, the whole crossing flow incl.
  re-send / teleport / death / the hint's first three, the AI edge on/off incl. risers and elites under a pause)
  and **10 mutants that must each be caught**. `--ledger` post-link: the dome, effects, both images, the
  script and the widget are in the linker ledger.
- `tools/test_haven_hud.lua` (build's Lua harness list): the real widget under the no-new-globals rule —
  enter / re-send / hit / exit / teleport, two negative controls.
- The kill pay (in `test_haven.js`): the 0.25, every payout and all nine popup arms wired, the death hook run in a vm,
  the shipping bank through gsc_eval (exactly a quarter over 320 kills, whole tens, the preview equal to the pay),
  and four kill-pay mutants (14 in all).
- `make_dome.py` / `make_fx.py` / `make_sounds.py --check` (build). `make_fx.py` also enforces THE ROUNDED RULE on
  the two crossing effects (`field_shape_problems`: no sprite over `FLAT_MAX`, every ring ON the sphere round the
  normal, at least three rings) and runs its own negative controls (the first cut's 150-unit flat ring and a ring
  7.8 units off the sphere must both fail).
- v2: `tools/haven_layout.js` asserts its own layout on load (rims, the field inside the walls and under the
  galleries, the ring on the floor, the porch wall corner clear of the sphere, the arrival's co-op ring on the floor,
  pylons, risers, respawns, bears). `lint_tod_geometry.js` decodes `lap<N> haven` sloped brushes like the crown's
  (the handrail is the visible balustrade in its guards' columns); `test_tower_transit.js` proves the pad and the
  arrival clear; `dealer_presence/verify.py` proves the floor-20 display's support and its re-reviewed context.
- The widget joins `tools/test_ui_lifetimes.lua`'s HUD-owner loop (20 construct/close cycles, no leaks).

## Logs (dev): `[TOD_HAVEN]`

`INIT havens= r= in= out= slow= dr= floors=`, `BOOT floor= why=wave|fallback at=`, `ENTER player= floor= at=
teleported= entries=`, `EXIT player= floor= at= teleported= state=`, `STATS floorN=<p>p/<ai>ai enter= exit= ai_in=
hits= absorbed=` every 10 s while anyone is inside, `SPAWN_FAILED` / `FX_DROPPED` (entity pool).

## The review (Blender, before the native build)

`art/haven/review/review.html`: `tools/haven/preview.py` renders the real emitted floor-10 faces of the WIRED map
(`tools/haven/review_scene.js`), the map's kit materials, the shipping dome drawn single-sided like the game draws
it (from inside you look through one shell, from outside through two) and the floor's own lights, from player
height; `tools/haven/render_tint_preview.py` draws the screen tint from `TodHaven.lua`'s own colours and alphas;
`tools/haven/preview_ripple.py` places the crossing ripples on the real dome from the GENERATED effect files (each
ring's plane, radius, beads, delay and alpha) at a crossing point the way `_tod_haven.gsc` picks it, and renders
moments of them face on, along the curve and from inside the field.
v2's views: through the archway from the landing, across the hall from the loggia, inside the field, at the
arrival, from the stairs above (over the sloped handrail) and a section plan. What the review taught the design:
the stepped 39 gallery rails (51 over the lower tread) hid the hall from the stairs, so they became one sloped
handrail per flight; the field's ring clipped the porch wall's corner, so the wall stops 10 short. The floor-20
Dealer wall panel now backs onto the hall's S wall: its matched reviews were re-rendered and the re-review is in
`art/dealer_presence/review_acceptance.json`.

## Build record (2026-10-02)

v3 (THE GUARDED HAVEN, 2026-10-03): FULL BUILD OK 15:01 in session -a0's war-damage phase-2 build (tmp/war_damage/full7.log; started 14:50:53; geom_key REUSED build 6's fresh bake for -a0's .map change: BSP 14:26:33, LED 239,400,329 B, navmesh): .ff 15:01:16, FF 229,403,200 B, the 8 known-waived linker lines only. Ran inside it: GSC STRICT LINT OK, HAVEN GATE OK 360 checks / 29 mutants, HAVEN DOME / FX / SOUNDS --check, HAVEN LEDGER OK 35 assets. The ledger carries scriptparsetree _tod_haven.gsc + _tod_breather_data.gsc, rawfile todhaven.lua, 13 xmodel tod_haven_* (the dome / _flash / _pulse / _dark / _dark_flash + the 8 tod_haven_sign_* skins) on 3 meshes, all 9 fx tod/haven effects, 11 haven images and 13 haven materials; deployed = repo for every haven input (the 14:44:42 _tod_haven.gsc: the slow carrier + the compile fix), nothing synced after the .ff; all ten tod_haven_* sound stems in the fresh loaded bank (all.sabl 15:00:18, 160.5 MB); the jump-pad session's 15:04 regen left _tod_breather_data.gsc byte-identical and HAVEN GATE OK 360 still holds on the repo. Its earlier attempts: full4 (13:43) and full5 (13:55) passed every haven gate and died on peers' gates (a missing Retriever harness stub; a re-reviewed surface-kit pin); full6 (14:13, after its bake) died AT THE LINKER on MY _tod_haven.gsc:963, a ternary passed straight into SetModel's argument list, which gsc_eval and every gate accepted - fixed 14:44:42 (wrapped whole), and -a0's NEW gate tools/lint_tod_gsc_strict.js now catches the shape. UNPLAYED.

The rounded crossing ripple (2026-10-03): BUILT: -GscOnly BUILD OK 04:30:20 (tmp/haven_v2/gsc_ripple1.log; .ff 04:28:32, FF 229,074,432 B, on the 21:29 BSP / 21:30 LED): HAVEN FX OK + HAVEN GATE 171 / 14 + HAVEN LEDGER 11 inside it, the 8 known-waived lines only; the ledger carries fx tod/haven/fx_tod_haven_cross + _push and _tod_breather_data.gsc; deployed .efx + data script = repo, scripts / zone_source / ui diffs clean, nothing synced after, no repo input changed during it. UNPLAYED.

v2 (THE HEART):

- FULL BUILD OK 21:35:10 (tmp/haven_v2/full1.log; started 21:21:35): .ff 21:33:23, FF 229,071,424 B. geom_key saw
  the map change and rebuilt: cod2map 21:29:14 (BSP 10.0 MB) and a fresh LED (237,297,922 B, see below). The 8
  known-waived linker lines only; sound bank 299.3 MB.
- NAVMESH GATE OK (535 faces, 27 components, the tower's 25 walk sections, the floor-40 chamber checked against its
  landing). A probe of the compiled mesh (the shipping lint plus points read from `haven_layout.js`) puts every hall
  point on every haven floor - the field centre, the arrival, the heart, both loggias, the porch - in the same
  component as that floor's SW landing and the W flight's top, so the horde walks in.
- Inside the build: HAVEN GATE OK (171 checks, 14 mutants), HAVEN LEDGER OK (11 assets), the conduit inlays (489 on
  27 hosts) compiled, the floor-20 Dealer display's support is the hall's S wall (DEALER_SUPPORT_CHECK).
- THE LED DOUBLED (119,523,714 -> 237,297,922 B) AND THE CAUSE IS MEASURED. The LED's `volumes` section is the whole
  file (the probes' bounce grids); attributing it by each probe's origin gives 28.5 MB for each fitted hall probe
  (four = 114 MB), 15.2 MB for the transit bay's and 2.1 MB for each 144-unit template probe. A hall probe's box is
  near-cubic (692 x 692 x 576) at the def's default `resolution` 4x, so its grid is dense on all three axes; the
  transit bay's flatter box costs half. In the pack, this build's bake set is 98 MB against the previous build's 68
  MB (the probe-volume texture 2.2 -> 9.9 MB per lighting state, the cubemaps 18.4 -> 20.2 MB per state, the
  sun-shadow tree 6.7 -> 8.0 MB): about +30 MB of download, the price of real bounce light in four rooms the player
  rests in. The knob is in the table above.
- Deployed = repo for every input of this pass at its sync: the map md5, `model_export/tod_haven` and
  `tod_haven.gdt`; every repo file changed after 21:21:35 is the Dealer session's round-9 voice (21:32). That
  session's -GscOnly (tmp/dealer_own/gsc1.log) synced at 21:36:49, AFTER this .ff: BUILD OK 21:59:43, .ff
  21:52:45, FF 229,071,424 B, on this build's BSP / LED / navmesh. It is the test .ff for both trees, verified here:
  its ledger carries the haven scripts, the three dome models, the four haven effects and the conduits; HAVEN GATE
  and HAVEN LEDGER ran inside it; scripts / zone_source / ui deployed = repo, nothing synced after.
- UNPLAYED.

v1:

- Wired 18:24 by `tools/haven/wire.py`. The first FULL build (tmp/haven/full1_lanes_fail.log) stopped at the sky
  fleet's lane gate: the floor-10 platform sits inside the 1,500-unit clearance of two dreadnought lanes west of the
  tower. `node tools/sky_ships/gen_lanes.js` regenerated the lanes (those two lost their low band; several south
  lanes gained one now the old lounges' southern walls are gone); `test_sky_ships.js` and `test_jump_title.js` pass.
- FULL BUILD OK 18:51 (tmp/haven/full2.log): .ff 18:49:31, FF 228,294,976 B, fresh BSP + LED (119,523,714 B).
  NAVMESH GATE OK; a probe of the compiled mesh puts each haven's heart, threshold, spur, arrival point and pad (the
  chamber on 40) on its floor's tower walk section, so the horde walks in (the crate's footprint has no mesh, as it
  should). HAVEN LEDGER OK (11 assets). The dome compiled with every exported triangle (3,966 / 1,536); the
  converter's 256 "texture stretching" notes per LOD are the base skirt (its UVs run along one texture row on
  purpose), nothing dropped. The six sounds are indexed in the loaded bank. scripts / zone_source / ui, the GDT,
  `model_export/tod_haven`, the aliases, the wavs and the map deployed = repo; nothing synced after the .ff.
- Every haven area sits inside its floor's `lapN_zone` volume (THE RECALL keeps players there); no riser or dog
  spawn is inside a dome (nearest 369 u from the centre; the co-op respawn points are inside, on purpose).

## Not verified (the user's playtest)

The kill pay in a real match (the +10 / +20 popups inside, the hint's second line, co-op payees in and out of a dome).

The in-game look of the dome and the screen tint (the Blender review in `art/haven/review/` is an approximation),
the sound mix, how the 33% slow reads on every elite type, co-op crossing feedback, the Battle Arena gate at the
field's centre on floor 40 ("everyone inside the field"), the hall's lighting and the view from the stairs, the
horde walking in through the porch fan and the strip, the teleporter's arrival inside the field.
