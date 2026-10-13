# 196 — The Departure Hall (the top teleporter bay) and the first jump's opening scene

2026-09-29, session 61. Two user requests, one build; then the first play's fix (§3) and THE CRASH (§4).

1. *"Please redesign the teleporter bay so it looks a lot nicer on this map."*
2. *"There is a jump from crown to tower. Can we make that more cinematic some how. Maybe we can rotate
   the skybox so that the tower of doom sign shows on the right and the camera can force the player to
   view it like an opening scene but only on the first time they use the jump pad. And we need the jump
   pad to have more hang time so players can feel that they are entering the real map now."*
   Then: *"Don't touch the sign yet. Someone is working on it. You can coordinate with them"* and
   *"Make sure you are communicating with each other and work as a team."*

Teamwork record: session **22** owns the sky EXR and re-rendered the title sign (roll 0 since §3).
Session **fd** added `skyRotation 180` and built the fix. Session **9c**'s sky fleet salutes the blazing
sign from THE CRASH's ignition beat (`tod_jump_title_ignite`, §4: a fighter wing over the sign, a hauler
far off), and §4 reuses 9c's gunships and engine glow. Session **d2** confirmed no overlap. (The first
build's `tod_jump_reveal` / `_end` hook is retired.)

**Status: BUILT, UNPLAYED.** One combined FULL build (`tmp/transit_bay/full1.log`): .ff written
2026-09-29 11:49:36, FF 221,747,008 B, fresh LED 171,844,877 B, NAVMESH GATE OK (TRANSIT 8 pads,
0 problems), 8 known-waived linker warnings. It carries this hall + jump, session 22's rolled sky
(deployed EXR sha 609d0a89...), 9c's sky fleet and d2's Black Market pass 3; each session confirmed
its own part in the ledger. scripts / zone_source / ui deployed = repo, nothing synced after the .ff.
No game launched; the user tests. Review page: `docs/196_ref/review.html`.

**FIRST PLAY 2026-09-29 ~13:00 (user: "your cinematic jump actually looks pretty good ... the way you're
facing doesn't have the actual Tower of Doom sign ... rotate the skybox so it fits your exact
measurement").** The log (`tmp/elite_tracking/runs/20260929_130328_358_02ca098f`) shows the scene ran as
designed (`CINE_TURN to_yaw=180 pitch=-11`, `CINE_REVEAL angles=(-10.0, -172.2)`). The sky was the
broken link: its image had never been measured in the engine, and the "centre column = +Y" assumption
was wrong. **§3 has the engine's real mapping and the fix** (session 22's roll-0 finish + `skyRotation
180`). **The fix is BUILT:** session fd's FULL BUILD OK 14:25:54 (`tmp/spire_removal/full1.log`, .ff
14:23:04): deployed `skyRotation 180`, the roll-0 EXR (sha c312071e...), a fresh sky .iwi
(`SPX6GZXG...`, 14:20:18) and this scene's pitch -13, nothing synced after. The sign is due west, in the
shot. **SECOND PLAY 15:33 (user: "when I jump padded I looked on the left side ... but the tower of doom
sign was on the right"): it was not.** The engine turns the sky by the SSI's SUN azimuth as well as
skyRotation, so 180 put the sign at yaw ~41, behind the rider's left shoulder. Measured from the user's
screenshot and fixed with skyRotation 40 (**§3**, rewritten). The same play found the client clock running
2.7x fast and the explosion cut after 1.2 s (**§4**, rev 3).

**THE CRASH (§4, user: "the skybox sign is like dimmed then there are two of the spaceships going at each
other ... they crash into each other they do a huge explosion so you can't see anything and then behind
is actually the tower of doom sign all lit up completely bright").** Status in §4.

Previews: `docs/196_ref/` (Blender renders of the ACTUAL emitted brushes, the shipped pad mesh, the
map's own lights as stand-ins, under the game's sky). They are previews, not native bakes.

---

## 1. The Departure Hall (the top transit bay)

**Before:** an 840 x 800 box off the terrace: flat ceiling, low purple walls, orange posts, three pads on
coloured mats (`docs/tower_design/transit/top_bay.png`).

**After:** a cruciform hall in the crown's own language, `tools/tower_transit_layout.js` (the one
source: geometry, pads, lights, FX, seeds; the generator emits the routes, markers and data from it).

```
                 N ARM — GATE 10 (cyan floor, blue panel)
                      |
   APSE — GATE 20 — CROSSING — NAVE — door — the terrace (the jump pad lands north of it)
   (green floor,      |
    THE WINDOW)  S ARM — GATE 30 (orange floor, bronze panel)
```

| piece | what the player sees |
|---|---|
| **The door** | on axis from the terrace: ruby pilasters on gold bases, a gold plate, a ruby keystone, a warm entrance light. 192 wide with 16u gold jambs (160 clear, as before), 240 clear high. |
| **The nave** | cobalt floor with two gold axis lines leading in, violet panelled walls with gold-framed windows (the north pair looks at the crown), a gold head band. |
| **The crossing** | four bevelled ruby piers on gold bases carrying four gold arches; above them an **open roof**: an octagonal gold oculus ring on four struts, a gold cross over it and a ruby lantern hanging from the cross; a jewel on the ring for each gate's colour (+ ruby for the door). A gold medallion ring on the floor. |
| **Each gate** | its own arm with a floor in the destination district's colour (30 orange, 20 green, 10 cyan), a gold ring round the pad, a gold floor number in front of it, and a portal on the back wall: bevelled ruby pilasters, a gold arch, a district-colour panel with a gold-on-graphite numeral plaque. A light in the gate's colour. |
| **The apse (gate 20)** | its back wall is **THE WINDOW** (312 x 340 above a 56u sill, clip glazing): the sky's TOWER OF DOOM II sign stands due west (the §3 fix, built: roll 0 + skyRotation 180), so it sits in the window at the end of the axis. From the door you see its centre; walk into the crossing and the whole title fills it. |
| **The roof** | open. Gold ribs crest every arm (over each pad); the sky, the mast and the crown stay in view (the user took the breather lounges' roofs off for the same reason). |
| **Underneath** | a stepped graphite keel under the crossing with a gold band and a ruby pendant (the crown's bell in miniature), graphite ribs under the arms. |
| **Ambience** | the lounges' three stock loops at generated anchors: motes falling through the oculus, haze in the crossing, wind-fog at the window (`tod_crown_data::transit_hall_fx`). |

**Lights** (all powered-state only, like every light in the map): one per gate in its district colour,
a warm key under the oculus, a cool nave fill, a warm door light on the terrace side. Label rule
`^transit hall ` in `tools/art_cohesion/tower_lighting.js` keeps the colours saturated but takes the
room profile's soft falloff and no-specular-hotspot settings. A fitted reflection probe spans the hall.

### Gameplay contract (unchanged unless noted)

- Routes, destination locks, hints ("down to FLOOR N" / "up to the TOP BAY"), costs, cooldowns and FX
  are the teleporter system's (`_tod_teleport.gsc`), untouched. The pads moved (they are emitted from
  `PADS`): 30 at (-1080,-40), 20 at (-1480,360), 10 at (-1080,760); arrivals from the floors land at
  (-620,360) inside the door.
- Two risers in the nave, >= 165 from the arrival. Nav seeds on every region (`SEEDS`).
- The terrace's two west rail stubs by the old door are no longer emitted: the hall's east wall now runs
  the whole terrace edge (the generator asserts it covers the edge, and that the door opens onto it).

### Rules this geometry keeps (and the gates that prove them)

- **Only axis boxes are walkable**; every shaped piece (arches, rings, struts, jewels, bevelled piers) is
  a convex brush emitted by `transitCPoly` / `transitCBevel` with the kit's texture scale per face.
- **Walls come from one rectilinear outline**: horizontal walls own the corner squares, vertical walls
  are trimmed at reflex corners (the layout asserts no two walls overlap).
- **Only BLOCK-class kit materials above the floor** (the geometry lint reads a thin DECK-class slab —
  brass, gold_line, the crystals — as a floor: the first draft's brass cornice crest and ruby keystone
  made 454 "unguarded edges" on top of the walls).
- **Floor decals never overlap** (asserted), the pads stand flush, nothing within 84 of a pad below 72.
- Gates: `lint_tod_geometry.js` (0 misplaced / 0 unguarded / 0 detached), `test_tower_transit.js`
  (routes, pad + arrival support and headroom, spacing, texture scales), `test_jumppad.js` (the arc
  sweep), `lint_tod_navmesh.js` in the FULL build (every pad on the roof_zone walk).

---

## 2. The jump: more hang time, and the first jump's opening scene

`scripts/zm/zm_tod2_cybercity/_tod_jumppad.gsc`, `ui/.../TodJumpCine.lua`.

### The hang (every flight)

- The arc's SHAPE is the same parabola (so `test_jumppad`'s sweep proves it), higher: apex +2600 (was
  +2200). Every flight 7.0 s (was 4.5); a player's first flight 13.8 s (9.5 until THE CRASH, 11.0 until
its second pass, §4: a real standoff, a visible fireball and ~3 s on the blazing title; the user: "if we
need the jump to last longer ... You can do that").
- It is walked on a warped clock, `hang_u()` (the integral of a speed profile, so it always ends exactly
  on the spot): a punchy launch (1.6x the mean speed), a float over the apex (0.5x), a dive, and a soft
  catch (0.25x). Time in the top fifth of the arc: 2.0 s -> 3.6 s (7 s flights) / 4.9 s (the first);
  touch-down speed 1956 -> 371 / 274 u/s. One MoveTo per server frame (0.05 s, was 0.1 s).
- A 3D wind loop rides the rider's own mover (`tod_jump_wind`, the existing `tod_full_steam_wind.wav`),
  fading out 1.2 s before the touch-down.

### The opening scene (each player's FIRST flight only)

| t (s) | what happens |
|---|---|
| 0.0 | launch (the pad's discharge, shake, rumble); letterbox bars close to 2.35:1 and the HUD hides (`TodHudVeil` key "jump"); the gun goes down and hides. The camera LOCKS ON THE RIDER'S OWN VIEW (the mover is set to it before a no-arc `PlayerLinkToDelta`: nothing jumps). THE CRASH's client scene opens (`tod_jump_title_start`): dark smoke gathers over the sign, the two warships load hidden. The music is already up: the descent's first band starts when a living player steps onto the jump-pad balcony (user: "the first song starts up once you enter the crown balcony ... No mid air on the jump pad"; session fd's change, `_tod_atmosphere::balcony_player` on the generated `jumppad_balcony_mins/maxs`). |
| 0.35 | THE CAMERA PATH starts turning (second pass, §5): the pitch eases up to the sign's 13 deg first (level with it by 1.35 s, longer for a bigger tilt), the yaw eases round to due west the short way (settled at 2.6 s); one path stepped with the arc every server frame. |
| 1.5 / 2.25 | the magenta gunship, then the green one, WARP IN on either side of the dark sign as the turn brings them into frame (§4). |
| 2.6 – 3.4 | the camera settles on the dark sign: THE STANDOFF; a slow 4 deg drift keeps the frame alive through the hold. |
| 3.4 – 4.6 | THE CHARGE and THE CRASH: the engines flare, they ram, a quarter second of white (§4). |
| 4.8 | THE IGNITION behind the white: the sign's glows come on unseen; the scene counts as seen (`tod_jump_title` is the music's fallback cue; 9c's salute launches). |
| ~5.0 – 7.4 | the fireball fills the frame and burns; the smoke over the sign lifts (6.2 – 7.4); THE REVEAL at ~7.0: the title emerges all lit up with its power surge. |
| 7.4 – 10.3 | ~3 s on the clear, blazing title; wreckage falling to the city; 9c's fighters crossing; the apex rides through it. |
| 10.3 – 12.1 | the swing back: ONE eased move from the sign to the landing view, the flight's heading 16 deg down (`tod_jump_title_end`: the blaze fades as the sign leaves the frame). The first pass went 32 deg down here and back up to 8 after control returned: the user's "wavers back and forth". |
| 12.1 | free: the camera has STOPPED; the clamp opens over 1 s, the bars open, the HUD returns, the gun comes up. Nothing turns the view after this. |
| 13.8 | the soft landing on the terrace. |

Where the sign is: **§3** (MEASURED in game): the sign's world yaw = -(the SSI sun azimuth + skyRotation) -
roll = -(140 + 40) - 0 = 180. **LOCKSTEP**: `TOD_JUMPPAD_CINE_SIGN_YAW` vs `docs/sky_preview/sky3d_stats.json`
"roll", `source_data/tod_skybox.gdt` `mtl_skybox_tod_cybercity` "skyRotation" and the yaw / pitch of every SSI
the map's sun volume uses. `test_jumppad` applies the rule and fails the build on any mismatch. (Two readings
before it were wrong and passed their gates: `yaw = 90 - roll`, then `yaw = -roll + skyRotation`. Neither had
been measured in game.) Pitch -13: the text box is at elevation 11 (`build_city.py` GATE `box_el`); 2 deg
higher fits the whole v7b gate (65 deg wide) with the hold's drift inside the letterboxed frame.

**Exits:** a card deal or any menu freeze tears the scene down at once (the clamp opens, the bars go,
the gun is handed back only if no menu holds it); death / disconnect run `cine_end` through `finish()`;
the Lua widget has a 17 s watchdog and releases the veil on close. The scene only counts as seen once
the reveal happened (a deal during the turn replays it on the next flight).

### Knobs, per symptom

| symptom | knob (`_tod_jumppad.gsc`) |
|---|---|
| too long / too short in the air | `TOD_JUMPPAD_FLIGHT_SECS` (every flight), `TOD_JUMPPAD_CINE_SECS` (the first) |
| the arc too high / low | `TOD_JUMPPAD_APEX` (test_jumppad re-sweeps it) |
| the float too floaty / the launch too violent | `TOD_JUMPPAD_WARP_*` (the gate proves any change is monotonic, smooth and ends on the spot) |
| the reveal too short | `TOD_JUMPPAD_CINE_HOLD_SECS` (+ `_SECS`; regenerate the effects) |
| the turn too fast / too slow | `TOD_JUMPPAD_CINE_TURN_AT`, `_TURN_SECS` (yaw), `_PITCH_SECS` / `_PITCH_REF` (the pitch lead); test_jump_title proves both warps stay in frame from 25 launch views |
| the swing back too fast | `TOD_JUMPPAD_CINE_BACK_SECS` (gen_fx reads it: regenerate the effects) |
| the landing view too low / too high | `TOD_JUMPPAD_CINE_LAND_PITCH` (16) |
| the impact shake too long / weak | `TOD_JUMPPAD_CINE_QUAKE` / `_QUAKE_SECS` / `_QUAKE_R` (the reach must cover the ~800 u the rider flies while it rolls) |
| the sign off-centre | up/down: `TOD_JUMPPAD_CINE_SIGN_PITCH`; sideways: the SKY, not the camera (the material's `skyRotation`, §3: the sign sits at -(sun + skyRotation) - roll; the yaw is lockstepped) |
| want to see the scene every jump while tuning | `TOD_JUMPPAD_CINE_EVERY 1` (the gate refuses to ship it armed) |
| no scene at all | `TOD_JUMPPAD_CINE 0` |
| the wind too loud | `tod_jump_wind` VolMin/VolMax in `sound/aliases/tod_ui.csv` |

### Diagnostics (print with dev OFF while `TOD_JUMPPAD_LOG` is 1)

`[TOD_JUMPPAD] INIT rev=3 cam=path ... flight= cine= apex= scene= every= sign_yaw= sign_pitch=`,
`LAUNCH ... secs= cine=`, `CINE_START`, `CINE_CAM view= sign= land= pitch_secs= still_at=` (the camera path's plan:
the rider's launch view is where it starts), `CINE_TURN from= to=`, `CINE_RETURN from= to=`, `CINE_FREE left= angles=
planned= player_angles=` (the camera when control comes back: `angles` should equal `planned`),
`CINE_SHIPS` / `CINE_IMPACT` / `CINE_IGNITE player= at= angles=` (the crash's beats, §4),
`CINE_REVEAL music_cue= at= angles=`, `CINE_RETURN`, `CINE_FREE`, `CINE_END why=done|world_pause|flight_end|flight_over`,
`LAND ... flight_ms= cine=`; `[TOD_MUSIC] BAND cued by the first jump's title reveal` (dev); the client's
`[TOD_JT]` lines (§4).

### Gates

`tools/test_jumppad.js` (the arc sweep; the hang clock replayed from the script's own defines:
monotonic, ends on the spot, launch/apex/touch-down speeds, hang time, touch-down speed, segment
smoothness; THE CAMERA PATH (§5): the shipping `cine_cam_plan` / `cine_cam_angles` RUN by
`tools/sky_ships/gsc_eval.js` from 63 launch views to every spot, at the server's step: no jump at the
lock, no step over 7.5 deg a frame, no jolt, one way through the turn and the return, still from
control-back to the touch-down, on the sign mid-hold, landing on the heading; two negative controls
(the first pass's dip-and-rise, a snapping lock); the path's wiring; the sky lockstep; the scene's
timeline fits the flight; the eventstring precache; the
client crash opened once and the retired reveal hook gone; `cine_end` restores everything and ends the
client scene; `finish()` runs it; a card deal tears it down; CINE_EVERY 0; the music wiring; the wind
alias is a 3D loop on a real wav), `tools/test_jump_cine.lua` (the letterbox and the white-out under
BO3's no-new-globals rule: veil held for exactly the scene, the flash's in / hold / out chain, an
interrupted hold, watchdog, close releases, bad args; negative controls) and THE CRASH's own gate
(§4).

### What only the playtest can tell

The feel of the float and the reveal, the wind level against the music, how the native lighting reads
in the hall (the previews use Blender stand-ins), and the new sign as rendered in game.

---

## 3. The sky's real mapping (MEASURED in game, 2026-09-29 second play)

### The second play proved the first reading wrong

After the first play this session decoded the engine's sky shader (`sky_latlong_hdr`, the mod tools'
compiled DXBC, `D3DDisassemble`) and concluded: the image's centre column faces world +X at skyRotation
0, so the sign's yaw = -roll + skyRotation, with 0 and 180 "safe whichever way the rotation turns". The
fix built on it (roll 0 + skyRotation 180, session fd's 14:23 build) was played at 15:33. The jump camera
faced yaw 180 exactly as designed (`CINE_TURN to_yaw=180`, `CINE_IMPACT angles=(-13.24, -179.24)`), and
the sign was not there. The user found it afterwards and sent a screenshot
(`tmp/jump_title/play1/screenshot_153629.png`, log `tmp/jump_title/play1/console_mp.log`).

**The lesson: the shader shows how a rotation is APPLIED, not what feeds it.** The float2 it rotates by is
set by the engine, and the engine puts the SUN in it too.

### The measurement (tools/sky3d/screenshot_fit/)

1. **Where the screenshot was taken.** The HUD shows 115 HP; the log's `[TOD_AI] PLAYER` lines at 115 HP put
   the eye at (-6, 628, 19452): the causeway landing deck, just past the portal.
2. **Which way it looked.** The view was rebuilt from the `.map`'s own brushes (every convex hull near the
   eye, ray-cast per pixel) and fitted to the screenshot's sky / geometry mask: yaw 83, pitch ~0, hfov
   ~104 (the user plays wide). The crown, both avenue pylons and the deck's rails line up.
3. **Where the sign is in that view.** Six painted features (the left spire's tip and ring, the T and the W
   of TOWER, the F of FALLEN) were matched between the screenshot and the reference painting, and turned
   into angles with session 22's card geometry (`build_city.py` GATE: 65 deg wide, D 1000, box_el 11). The
   sign's centre sits 41.6 deg right of the view: **world yaw 41.4 +- 1.5.**
4. **The check.** Rendering the rebuilt view with the finished equirect turned so its centre faces yaw 41
   reproduces the screenshot: the crown and its ruby, both pylons, the spire and ring, TOWE / FA, DOO /
   BERC behind the right pylon, and the cyan ringed city on the left. The old rule's render (the sign at
   180) shows none of it.

### The rule

**The image's centre column faces world yaw -(SSI sun azimuth + material skyRotation) - roll**. Image-right
is the viewer's right (not mirrored) and row 0 is straight up. The sun azimuth is the SSI's `yaw` when its
`pitch` is past 90 (the light travels down the far side, so the sun sits at `yaw`), else `yaw` + 180.

| evidence | sun azimuth | skyRotation | the rule predicts | measured |
|---|---|---|---|---|
| our 15:33 build (roll 0) | 140 | 180 | the sign at yaw 40 | yaw 41.4 |
| Nastian `zm_tungsten` | 173.96 | 0 | its painted sun at u 0.5336 | u 0.5338 |
| Nastian mp skies (sun 0) and zm skies (sun 180) | 0 / 180 | 0 | the sun on the centre column | u 0.49-0.53, all of them |
| Treyarch `mp_sector` | 244 | 236 | the sun at u 0.489 | u 0.49-0.52 |
| Treyarch `default_day` | 150 | 75 | u 0.458 | u 0.482 |
| Treyarch `default_sunset` | 300 | 110 | u 0.528 | u 0.557 |
| Treyarch `zm_factory` (the eclipse) | 120 | 85 | u 0.597 | u 0.528 (the brightest blob, not the disc) |

The old reading (no sun term) misses Treyarch's skies by 100-150 deg and our screenshot by 139. Artists
line the painted sun up with skyRotation, so the Treyarch rows are within an artist's tolerance, and the
Nastian rows (suns painted at the centre with SSIs pointing both ways) only line up with the sun term in.

### The fix

`mtl_skybox_tod_cybercity` **skyRotation 180 -> 40**: -(140 + 40) - 0 = -180 = due WEST. The EXR, its roll 0
and both SSIs are unchanged. The whole picture turns 140 deg, so the sky's light on the bake turns with it
(the full build re-bakes). The engine's image seam (u 0/1) is now due east, behind the jump camera. Session
22 (the sky) and fd (the GDT's owner) agreed.

### The gate now

`tools/test_jumppad.js` reads the roll (`sky3d_stats.json`), skyRotation, and the yaw / pitch of EVERY SSI
the map's `volume_sun` names (`ssi`, `ssi1`..`ssi4`: `tod_ssi_cybercity` and `_dark`, both yaw 140 pitch
130). It computes the sign's yaw with the rule and fails if any live SSI puts it more than 1 deg off
`TOD_JUMPPAD_CINE_SIGN_YAW`, printing the skyRotation that would fix it. Its self-checks re-derive the
screenshot (40 vs 41.4), `zm_tungsten` and `mp_sector` from the rule, and prove the old reading misses.
Negative controls: the played skyRotation 180, and an SSI yaw turned 10 deg, must both fail.

**A consequence to remember:** changing an SSI's yaw now turns the visible sky. The gate catches it.

### If the sky ever moves again

Measure it on a screenshot, never predict it: `tools/sky3d/screenshot_fit/README.md`.

---

## 4. THE CRASH (the first jump's title moment, 2026-09-29)

User: *"the skybox sign is like dimmed then there are two of the spaceships going at each other during the
cinematic scene they crash into each other they do a huge explosion so you can't see anything and then
behind is actually the tower of doom sign all lit up completely bright um, really kind of emphasizing the
map title ... reuse their spaceships ... build it end to end ... sounds and huge explosion effect"*.

After the first play of it (15:33): *"THe kaboom ended early. ALso when I jump padded I looked on the left
side in the screenshot but the tower of doom sign was on the right. Please perefct this and make sure sign
doesnt light up until explosion happens. Please double check all your work here."* Then: *"Im wondering if
we need the jump to last longer. You cando that as well. You have levels to pull of rthe best player
experience"*.

**Now: THIRD PASS (camera path, a real boom, audible warships) in §5.**
**Status: SECOND PASS (rev 3) BUILT in session e7's combined FULL BUILD OK 17:23:27 (tmp/typeface/full2.log; .ff 17:21:57, FF 222,833,728 B; fresh bake: geom_key saw the sky material change). Verified: `JUMP TITLE LEDGER OK` (8 effects + the client script), deployed `tod_skybox.gdt` skyRotation 40 = repo, `mtl_skybox_tod_cybercity` in the ledger, the five `tod_jt_*` sounds in the fresh loaded bank, scripts / ui / zone_source diffs clean, nothing synced after the .ff. UNPLAYED.**
The first pass (rev 2) BUILT at 15:31 (`tmp/jump_title/full2.log`) and was played once at 15:33.

### What the first play showed (`tmp/jump_title/play1/`)

1. **The sign was not where the camera looked.** The sky's rule was wrong (§3). The fix is skyRotation 40.
2. **"The kaboom ended early": a CLIENT `wait` is not real time.** It counts frames. On the user's ~165 fps
   machine `wait 14` (the watchdog) finished after 5.12 real seconds, so the watchdog cut every effect and
   sound 1.2 s after the impact (`WATCHDOG t=5.123`, `CLEANUP why=watchdog`). `wait 1.5` (the first warp)
   finished at 0.55 s, before the camera had even turned. The server's beats arrived on time (2.70 / 3.89 /
   4.11 s by `GetRealTime`), so only the client clock ran fast: 2.73x. Session 9c's sky fleet shows the
   same ratio (a 20.7 s flight, 207 ticks of `wait 0.1`, took 7.7 real seconds). A `MoveTo` rides the same
   script clock. Stock uses `waitrealtime` for real time (`util::server_wait`, `fx_shared.csc`).
3. **The fireball was never seen.** Its bright phase ended 0.9 s after the impact, entirely under a 1.5 s
   white-out, and the watchdog cut the rest.
4. **The sign would have read lit.** The smoke over it left ~1/6 of its neon.

### What the player sees and hears (rev 3, the first flight 13.8 s)

| t (s) | picture | sound |
|---|---|---|
| 0.0 | (facing the tower) dark smoke gathers over the sky sign, full by 0.75 s, out of view | the wind |
| 0.35 | the camera (locked on the rider's own view since the launch) starts its one eased turn onto the DARK sign (about 1/12 of its light gets through the smoke); its pitch leads | |
| 1.5 | the MAGENTA gunship warps in left of the sign: lightning, a white-hot core cooling to blue plasma, shock rings | a deep warp bamf from the left and its engines lighting, then its engine roar (3D, full level out to 12,000 u) |
| 2.25 | the GREEN gunship warps in on the right, bow to bow | the bamf from the right; now TWO engine roars, left and right, each pitched its own way |
| 2.6 - 3.4 | THE STANDOFF: the camera settles; two warships hover in front of the dark sign | the engines carry the shot (the wind has dropped) |
| 3.4 | both engines flare white-hot with long cyan streaks; they RAM, accelerating all the way (1.2 s) | THE CHARGE: an afterburner kick from each side, then both rocket roars climbing seven semitones as they sweep to the centre, a turbine scream rising under them and a jet-wash whoosh, building to the impact |
| 4.6 | nose to nose in front of the title: a quarter second of full WHITE, a shake that rolls with the rider (1.8 s), the controller rumbles | THE BOOM, loudest in its first 0.2 s (a real blast: crack, body, sub), rolling off into the thunder rumble |
| 4.8 | (behind the white) the sign's glows come on, hidden by the fire and the smoke over it | |
| ~5.0 - 7.2 | the white burns out through orange onto THE FIREBALL: an orange bloom ~120 deg across, fire billows, tendrils, dark smoke, shock rings, two reactor blasts a beat apart, burning wreckage starting to fall | the boom's fire and tail, the rumble |
| 6.2 - 7.4 | the fire thins and the smoke over the sign lifts | |
| 7.0 | THE REVEAL: the TOWER OF DOOM II sign emerges ALL LIT UP | the power surge: a zap, a machine power-up, a neon hum, the stock "power on" |
| 7.2 / 7.6 | the skull's ring flares, then its eyes; sparks rain off the letters | |
| 7.4 - 10.3 | ~3 s on the clear, blazing title; the wreckage falls to the city; 9c's fighters cross | the rumble rolls out |
| 10.3 | the swing back to the tower; the blaze fades as the sign leaves the frame | the wind returns |
| 12.1 | free: the bars open, the HUD returns | |
| 13.8 | the soft landing on the terrace | |

### How it is built

- **Server** (`_tod_jumppad.gsc`): owns the camera, the white flash (`TodJumpCine.lua` state 2: in 60 ms,
  full white 250 ms, out through orange 750 ms), the shake (`TOD_JUMPPAD_CINE_QUAKE` 0.42 for 1.8 s) and
  the rumble; sends five beats to the flyer's client only (`util::clientNotify`): `tod_jump_title_start`
  (launch), `_ships` (3.4), `_impact` (4.6), `_ignite` (4.8), `_end` (10.3, or AT ONCE on any cut-short
  scene). `util::clientNotify` is a per-player STATE (stock `setClientSysState`): two in one frame and the
  first is lost, so the beats are >= 0.1 s apart and `cine_reveal` sends none.
- **Client** (`_tod_jump_title.csc` rev 3, zero server entities, 9c's rule): the ships, the effects, the
  sounds. **Every delay is `waitrealtime`, and the ships' hover and ram are set every frame from
  `GetRealTime`** (the ram follows the same 85%-acceleration curve the gate and the storyboard fly). The
  one script `wait` left is `clock_probe`, which logs the two clocks side by side once per scene. The
  reveal (ignite + `TOD_JT_REVEAL` 2.2 s) plays the power surge. Each beat plays once; a watchdog (17 real
  seconds) clears everything if `_end` never comes; a cut scene kills every effect and sound at once, a
  finished one lets the particles fade.
- **Two kinds of place.** The ships and the crash are fixed in the WORLD, 6,000 u west of the rider at the
  impact, in front of the title, a shallow X (12 deg) across the frame. The dark smoke and the blaze belong
  to the SKY sign, at infinity: they play on a host the client moves every frame to camera + the sign's
  bearing x 11,000 u. The glows' offsets are the painting's features turned into angles with session 22's
  card geometry.
- **The effects follow the jump's own clock.** `gen_fx.py` READS `_tod_jumppad.gsc`'s beats: the smoke over
  the sign lives until ignite + `CLEAR_DONE` and starts lifting at ignite + `CLEAR_FROM`; the blaze holds
  full to the swing back and fades through it; the ring flares at `RING_AT`, the eyes at `EYES_AT`, the
  sparks at `REVEAL`. Retime the jump and the next generation re-times them (`--check` fails until then).
- **No pop-in.** The ships load hidden at the launch and appear only with their own warp flash; the hulls
  go 0.12 s after the impact, inside the full white. The smoke over the sign is never killed: it lifts on
  its own curve, so the sign can never be seen switching on.
- **Dark, not hidden.** Seven slow dark puffs (one each, never re-seeded) at 0.7 leave ~1/12 of the sign's
  light: the shape is still faintly there, the neon does not read as lit (0.55 left ~1/6, which did).
- **The fire you see.** The flash-length bursts keep their stock timing; the hot glow lingers x2.4 through
  the flash's burn-out; the fire billows and tendrils burn x1.5 (~2.6 s average), the dark smoke x0.8; a new
  orange bloom (`jt_fireball`, 9,000 -> 12,500 u, 2.3 s) carries the fireball's light over the frame.
- **Reused:** 9c's `tod_sky_gunship` (magenta) and `_b` (green) and their engine glow; the fleet's jet loop
  under its own alias.

### Assets (all GENERATED; never hand-edit the outputs)

| thing | source | tool |
|---|---|---|
| 7 effects `share/raw/fx/tod/jump/fx_jt_*` | stock effects, read-only, re-scaled for the sky (one space factor k and one time factor tau per element): the mid-air explosion x3.2 + the mothership's falling debris + Der Eisendrache's moon-blast shock rings + the fireball bloom (boom); the same blast x1.6 (the reactor blasts); the helicopter streamer's fire on falling arcs (wreckage); Gorod Krovi's dragon-strike portal flash at 60% (warp); glows on the manifest's nozzles (burn); the mothership's dark smoke (veil); glows in the sign's tube colours (blaze) | `python tools/jump_title/gen_fx.py` (`--check` also validates every element) |
| 6 sounds `sound_assets/tod/jump/tod_jt_*.wav` | layered from real recordings on this machine (§5: the launcher ports' explosions and rocket motor, the user's C4 explosion, stock blasts, the Fury bamf, map 1's warp and thunder) + synthesised whines and jet wash; numpy/scipy shape them, ffmpeg masters (boom, rumble, charge, warp, ENGINE loop, ignite) | `python tools/jump_title/make_sounds.py` (`--check` = shape, loudness, where the energy sits, the loop seam) |
| 6 aliases `sound/aliases/tod_jump.csv` | 2D cues on BUS_FX; `tod_jt_warp` and `tod_jt_jet` (the engine loop) 3D, full level to 12,000 u; the crash's cues at volume 100; `zmb_turn_on` is stock | loaded by `sound/zoneconfig/zm_tod2_cybercity.szc` |

### Gates

`tools/jump_title/test_jump_title.js` (every number READ from the live sources by `scene_live.js`, the
effects' lives and alpha curves read from the GENERATED `.efx`):
- A. lockstep: the run time = the beat gap, the bow = the manifest, the sign's bearing / elevation / layout
  distance, the wreck points = the contact, `TOD_JT_REVEAL` = gen_fx `REVEAL`.
- B. the beats: order, one per frame, the ignition and the hull removal inside the full white; the fireball
  seen >= 1 s before the reveal; the smoke over the sign full before the turn brings it in and lifting only
  >= 1 s after the impact; the reveal inside the lifting, the ring and eyes after it; >= 2.5 s of the clear
  blazing title; the veil >= 0.6; the .efx lives and curves on THIS timeline; the watchdog; the host
  outliving the blaze.
- C. the frame (5 take-offs x 4 landings, a 65-deg letterboxed frame): each ship at its warp, the bows at
  the settle and the charge, the crash within 6 deg of the centre, the sign central through the hold.
- D. the sky: both ships inside the sealed volume and >= 1,500 u from every brush and keep-out (9c's map
  reader); the sign host inside the volume.
- E. the wiring: the five beats once each, the client listening, every effect generated + precached +
  zoned, every alias + wav, the ships hidden until their warp, the host following the camera, the veil
  never re-seeding and <= 0.7; THE CLOCK (no script `wait <seconds>` outside `clock_probe`, no MoveTo /
  RotateTo in the client scene, the watchdog on `waitrealtime`); the smoke over the sign never killed
  early; the surge at the reveal, not the ignition.
- 24 negative controls. `--ledger` after the link: every effect and the client script are in the fastfile.

Re-solve the placement after a pad / sign / timing change: `node tools/jump_title/solve_scene.js` (on rev 3
its best pick is 6,500 u out and 0.9 deg off centre; the scene keeps 6,000 u, 1.8 deg off centre, for a
bigger fireball).

### Knobs, per symptom

| symptom | knob |
|---|---|
| the crash too early / late | `TOD_JUMPPAD_CINE_SHIPS_AT` / `_IMPACT_AT` / `_IGNITE_AT` (+ `TOD_JT_RUN_SECS` = the gap; the gate enforces it); then regenerate the effects |
| too little / too much time on the blazing title | `TOD_JUMPPAD_CINE_HOLD_SECS` + `TOD_JUMPPAD_CINE_SECS` (the gate wants >= 2.5 s after the smoke clears); regenerate |
| the explosion too small / big | `gen_fx.py` K (3.2) on `fx_jt_boom`; `jt_fireball` size / alpha |
| the fire gone too soon / lingering over the title | `gen_fx.py` `TAU` (per layer) and the `jt_smk_thick` factor (0.8) |
| the white flash too long / short | `TodJumpCine.lua` `FLASH_HOLD_MS` / `FLASH_OUT_MS` (the ignition must stay inside the hold) |
| the sign too dark / too lit before the crash | `gen_fx.py` `VEIL_ALPHA` (0.7 = ~1/12 of its light; the gate keeps it 0.6..0.7) |
| the sign emerging too early / late | `gen_fx.py` `CLEAR_FROM` / `CLEAR_DONE`, `REVEAL` (+ `TOD_JT_REVEAL`), `RING_AT` / `EYES_AT` |
| the ships arrive too early / late | `TOD_JT_WARP_A` / `_WARP_B` (the gate keeps each in frame at its warp) |
| a sound too loud / quiet | `sound/aliases/tod_jump.csv` VolMin / VolMax (or the layer volumes in `make_sounds.py`) |

### Diagnostics

Server `[TOD_JUMPPAD] CINE_SHIPS / CINE_IMPACT / CINE_IGNITE player= at= angles=`. Client `[TOD_JT] INIT rev=3
...`, `START client= cam= a= b= ships= host= veil= load_secs=`, **`CLOCK script_wait_1s_took_real=`** (the
two clocks: ~0.37 on the user's machine if the diagnosis holds), `WARP ship= t= at= dist=` (expect t ~1.5 /
~2.25), `CHARGE t=` (~3.4), `IMPACT t= cam= dist=` (~4.6), `IGNITE t=` (~4.8), `REVEAL t= after_ignite=`
(~7.0 / ~2.2), `END t= full=` (~10.3), `CLEANUP why=cut|watchdog|replaced`, `WATCHDOG`. `TOD_JT_LOG 1`
prints in the user's launcher (dev block); zero it before a publish.

### What only the playtest can tell

How big and bright the fireball reads at 6,000 u, whether the quarter-second flash plus the fire reads as
"you can't see anything", whether the sign at ~1/12 reads dark enough, the glows against the sign's own
neon, and every sound level against the balcony music.

---

## 5. THE THIRD PASS (2026-09-30): one smooth camera path, a real boom, warships you can hear

User, after playing the scene (log `tmp/elite_tracking/runs/20260930_000748_649_9b84b8c7`, first jump 433 s into the
match): *"The cinematic view jump is okay but its not super smooth. The player wavers back and forth towards the end
of jump and the explosion should use an actuall loud boom instead of the nuke sfx. And the ships should have some
sound effect ebfore the boom of flying spaceships."*

**Status: BUILT, UNPLAYED. It rode the sky session's FULL BUILD OK 09:44:44 (`tmp/sky_middle_ground/full.log`; .ff 09:42:38, FF 225,466,880 B; fresh BSP + LED for their sky change). Inside it: `test_jumppad OK` (the camera path, 252 flights x 276 frames), `JUMP TITLE FX OK 7`, `JUMP TITLE SOUNDS OK 6`, `test_jump_title OK`, and after the link `JUMP TITLE LEDGER OK` (8 effects + the client script). Checked after it: the six `tod_jt_*` rows in the linker's compiled alias table (`tod_jt_jet` plays `tod_jt_engine.wav`, volume 100, full level to 12,000 u), the six wavs, `tod_jump.csv` and both scripts deployed = repo, ui / zone_source clean, nothing synced after the .ff; the one scripts difference is a peer's `_tod_shop.gsc` saved at 09:45 (after this .ff, not this pass). This session's own -GscOnly (`tmp/jump_title/gsc3.log`) linked the same sources, but that full build's sync removed the ledger folder mid-way through its post-link checks; the full build re-ran them all.**

### What was wrong (measured, not guessed)

1. **The waver was in the script.** The swing back pitched the view 32 deg DOWN (10.3 - 12.1 s), then a second
   RotateTo pulled it 24 deg back UP to 8 (12.1 - 13.7 s) while the clamp was already opening: down, then up, under
   the player's own hand. The turn at the start was two systems at once: a `LerpViewAngleClamp` squeezing the rider's
   own look while four separate RotateTo moves turned the mover. The user launched looking 27 deg down and 23 deg
   right (`CINE_START angles=(27.35, -114.62)`), so the squeeze only bit late in the turn, and at 1.5 s the camera
   was still looking down: the magenta warship most likely warped in above the frame.
2. **The boom was the Nuke.** `tod_jt_boom` was built on the zombies Nuke power-up; its loudest moment was 1.50 s
   AFTER the flash (the recording's own lead-in), with the Nuke's tonal bands on top.
3. **The ships were under the music.** The balcony music plays at -9..-11 LUFS and sits in the never-duck group
   (no duck can lower it). The ships' engines were the fleet's jet hiss at alias volume 74, fading from 3,000 u,
   with the ships 6,900 - 9,000 u away; the charge was -15.5 LUFS. 7 - 20 dB under the music.

### THE CAMERA PATH (`_tod_jumppad.gsc`)

One path, a pure function of the flight clock, stepped with the arc every server frame (`cine_cam_plan`,
`cine_cam_angles`; each step is wrapped next to the mover's own angles so a RotateTo always takes the short way):

| t (s) | the camera |
|---|---|
| 0 | the mover is set to the rider's own view, then linked with NO view arc: the lock closes on exactly what they looked at |
| 0 - 0.35 | held |
| 0.35 - 1.35 | the pitch eases onto the sign's 13 deg (a bigger tilt takes longer: 45 deg per second, capped at the turn), so both warships warp in on screen |
| 0.35 - 2.6 | the yaw eases onto the sign's bearing, the short way |
| 2.6 - 10.3 | the hold's slow drift (4 deg, 1.5 deg), as before |
| 10.3 - 12.1 | ONE eased move to the landing view: the flight's heading, 16 deg down |
| 12.1 - 13.8 | STILL: the clamp opens over a camera that has stopped; nothing turns it after |

Every piece is a smoothstep: no step, no jolt, and no angle ever turns back inside the turn or the return. For the
user's own launch view the fastest moment is 75 deg/s (the swing back). The beats, the white-out and the effects'
timeline are unchanged (gen_fx reads the same TURN_AT + TURN_SECS + HOLD and BACK). The impact's shake now reaches
2,000 u (`TOD_JUMPPAD_CINE_QUAKE_R`, was 160): the rider flies ~800 u during its 1.8 s and left the old one after
~0.3 s.

### THE SOUNDS (`tools/jump_title/make_sounds.py`, rewritten; all real recordings on this machine + synthesis)

| cue | now |
|---|---|
| `tod_jt_boom` | a real blast that hits ON the flash: Skye's T6 rocket explosion (the crack of the hulls meeting), the S2 Bazooka's blast a tone lower (the body and its roll), the user's "explosion large distant" (their C4) four semitones lower and spread wide (the size), the S1 Mahem blast under 150 Hz and an LFE drop (the chest hit), the stock 'firey' blast (burning debris); soft-clipped; loudest 400 ms -6.2 LUFS inside the first 0.2 s, -9 dB by 1 s, then the thunder rumble takes it. No Nuke. |
| `tod_jt_engine` | NEW: each gunship's engines from its warp to the crash, a seamless 8 s loop (the fleet's capital-ship drone, the Bazooka's rocket motor flattened a fourth lower and laid round the loop, a turbine whine, jet wash); 3D on each ship, full level out to 12,000 u, each ship pitched its own way (-11.8 LUFS each) |
| `tod_jt_warp` | the bamf, the electric tear and the sub hit, plus the engines lighting as the ship drops out of the warp (the Stinger's ignition); full level out to 12,000 u |
| `tod_jt_charge` | an afterburner kick from each side, then both rocket roars climbing seven semitones as they sweep to the centre, a turbine scream rising under them, a jet-wash whoosh sweeping up the spectrum: -17 -> -8 dB into the impact (loudest 400 ms -6.7 LUFS) |
| `tod_jt_rumble` / `tod_jt_ignite` | unchanged recipes (the rumble now at alias volume 100) |

The one-shots are mastered by their loudest 400 ms with the limiter capped (so a hit keeps its punch), the loops
by their average; the true peak is trimmed under -0.8 dBFS. `--check` gates the length, channels, loudness, where
the energy sits (the boom peaks in its first 0.25 s; the charge builds) and the engine loop's seam.

### Gates

- `tools/test_jumppad.js` 3d **runs** the shipping camera functions (`tools/sky_ships/gsc_eval.js`) from 63 launch
  views to every landing spot at the server's step: no jump at the lock, <= 7.5 deg a frame, no jolt over 1.6,
  one way through the turn and the return, still from control-back (12.1 s) to the touch-down, on the sign
  mid-hold, landing on the heading. Negative controls: the first pass's dip-and-rise ending and a snapping lock
  both fail it. Plus the wiring (the plan before a no-arc link, the per-frame step, nothing rotated in `cine_run`).
- `tools/jump_title/test_jump_title.js` C frames the scene on that real path from 25 launch views (500 flights);
  NEW F: the warp and the engine loop play at full level past the farthest ship (8,958 u), the ship loop is the
  gunship engine, every crash cue at volume 100 (2 new negative controls). `scene_live.js` `L.cam` is the shipping
  path; the hand-written copy in `scene_geometry.js` is gone; the solver and the storyboard use the real path
  (`docs/196_ref/crash_storyboard.png` re-rendered).

### Diagnostics

`[TOD_JUMPPAD] INIT rev=3 cam=path`, `CINE_CAM view= sign= land= pitch_secs= still_at=`, `CINE_TURN from= to=`,
`CINE_RETURN from= to=`, `CINE_FREE left= angles= planned= player_angles=` (`angles` must equal `planned`: the
camera stopped where the path ends); the client's `[TOD_JT] INIT rev=4`.

### What only the playtest can tell

Whether the boom reads as a real, loud explosion in the engine's mix, the engines and the charge over the balcony
music, the feel of the 16 deg landing view, and the rolling shake.

---

## 6. THE FOURTH PASS (2026-09-30): the sign is DULL until the crash, then it flickers on and blazes

User, reviewing the flow: *"I want it to be in awe shock and just sick and the thing i really want is the sign to not
glow and actually be very dull and then after explosion it should glow very bright"*.

### What was wrong

Rev 3 hid a LIT sign behind seven near-black smoke puffs (`fx_jt_veil`) and lifted them at the reveal. That is a
dim, not a dull: the baked sign kept its neon and halo, the smoke read as smoke, and the darkness moved with the
puffs. The user's own words are the spec: the sign itself must be unlit, and then light up.

### What it is now

| piece | before | now |
|---|---|---|
| the sky's sign | baked LIT (v10) | **baked DULL**: `tools/sky3d/build_city.py --sign-state dull` -> `cyber_hero_title.py` caps every pixel's max channel to `DULL_CAP` 0.05 (the tubes become dark tinted glass), desaturates by `DULL_DESAT` 0.55 (the metal loses the neon's rim light), emits the body at `DULL_BODY` 0.7 of the lit level, no neon boost. Same painting, same alpha, same tiles, same finish. The sky pass's `author_config.json` carries `"sign_state": "dull"`; the title report says so. |
| the lit sign | the bake | **a client CARD MODEL** `tod_jt_sign_lit` (`tools/jump_title/make_sign_card.py`, GENERATED with `--check` in the build): the same painting on a two-triangle quad with the sky's own GATE geometry at `SIGN_DIST` 9,500 u (65 deg wide -> 12,104 x 8,070 u, the DOOM II centre on the bearing), `lit_emissive_transparent` (the painting's alpha is the card's opacity; colorTint black so it is only its own light; `scaleRGB` 16 = THE ONE BRIGHTNESS KNOB). The client spawns it hidden at the scene start on the sign's bearing, moves it with the camera every frame (it is 'at infinity' like the bake, so it sits over the dull sign from any position), and keeps it for the match. |
| the reveal | the smoke lifting 6.2..7.4 s | at 7.0 s (ignite + 2.2) the power surge plays and the card **FLICKERS ON** like a neon sign taking power (`flicker_ms()`: on 70 / off 60 / on 50 / off 100 / on 120 / off 50 ms, then steady), the blaze glows ramp up over the held card from 7.45 s, the crest's ring flares +0.25 s and its eyes +0.65 s, sparks rain off the letters; the glows hold to the swing back (10.3) and fade as the sign leaves the frame; the card stays lit. |
| a cut scene | the veil killed | a scene cut after the ignite beat lights the sign at once (never a dull sign after the crash); a scene cut before it leaves the sign dull and replays next flight (unchanged). |
| the veil | 7 puffs, 30,000 u box | RETIRED whole (generator, zone, precache, gate). |
| SIGN_DIST | 11,000 | **9,500**: the card must sit BEHIND every hull point that can cross its extent (a hull behind the card would be hidden by it: the sign is opaque now) and keep its centre inside the sealed sky volume; the gate proves both. The blaze sizes scale with it. |

Why a lit card over a dull bake, not a dark card over the lit bake: the sky's mapping is measured to ~1.5 deg
(section 3). A dark overlay would leak lit neon at every letter edge on any registration error; a lit overlay over
a dark bake hides its own error (a dark tube next to a lit tube on a dark sky is invisible). And the halo comes for
free: the lit card's soft edges blend over the bake as light should.

### Files

- `scripts/zm/zm_tod2_cybercity/_tod_jump_title.csc` rev 5: `lit_card()` (one per client, `level.tod_jt_lit`),
  `sign_on()` (the flicker in real time, idempotent), `reveal()` (surge -> flicker -> blaze), `cleanup()` lights
  after the ignite; the veil is gone. `_tod_jumppad.gsc`: header / INIT text only (`INIT rev=4 ... sign=dull_bake+card`).
- `tools/jump_title/make_sign_card.py` (NEW): the model (PyCoD, BO3 winding), the texture (the painting, BC7),
  `source_data/tod_jump_title.gdt`, the receipt `art/jump_title/sign_card.json`. `zone_source`: `xmodel,tod_jt_sign_lit`
  (its material and image ride the xmodel line, never zoned bare). `tools/sync_to_modtools.ps1` copies
  `model_export/tod_jump_title`. `tools/build_map.ps1` runs `make_sign_card.py --check` with the other jump gates.
- `tools/jump_title/gen_fx.py`: the veil block removed; `SIGN_DIST` 9500 + `BLAZE_REF_DIST`; `flicker_ms()` READ from
  the client script; `BLAZE_AT` = ignite + reveal + the flicker; the blaze's life / hold / fade from it; `RING_AT` /
  `EYES_AT` relative to the card's hold.
- `tools/sky3d/build_city.py` (`--sign-state`), `tools/sky3d/cyber_hero_title.py` (the DULL branch, the report's
  `sign_state`), `tools/sky_consistency/author.py` + `tools/sky_middle_ground/*` (the `sign_state` config key;
  `TOD_SKY_PASS` for a later pass on the middle-ground pipeline). `tools/sky_cohesion/verify_build.py`: six effects,
  the card's three files as runtime inputs, the xmodel in the ledger check.
- Gates: `test_jump_title.js` (A: the card's distance / model / elevation / width against the live GATE; B: the sign
  lit >= 1 s after the impact and the white's burn-out, the flicker 0.2..0.8 s, >= 2.5 s of the held title, the blaze
  on the card's hold; D: the card behind every hull corner over the flight, the host / card inside the volume; E: no
  veil anywhere, the card generated + zoned + synced + gated, shown only by the reveal / a cut after the ignite, never
  deleted by a scene, hidden at spawn, following the camera; the ledger check wants the xmodel + its material + image;
  30 negative controls).

### Knobs, per symptom

| symptom | knob |
|---|---|
| the lit sign too bright / too dull | `SIGN_LIT_SCALE` in `make_sign_card.py` (scaleRGB; regenerate, FULL build) |
| the dull sign still reads lit / too invisible | `DULL_CAP` / `DULL_DESAT` / `DULL_BODY` in `cyber_hero_title.py` (a sky re-render + FULL build) |
| the flicker too long / too nervous | `flicker_ms()` in `_tod_jump_title.csc` (gen_fx re-times the blaze: regenerate) |
| the lit card off the dull sign sideways / up | the SKY's bearing (section 3), never the card: it shares the bearing and the GATE geometry |
| the card hides a ship | `TOD_JT_SIGN_DIST` / gen_fx `SIGN_DIST` (the gate refuses a card in front of a hull) |

### Diagnostics

`[TOD_JT] INIT rev=5 ... dist=9500 card=tod_jt_sign_lit flicker_ms=450`, `START ... card=1 already_lit=0`,
`IGNITE ... card=1`, `REVEAL ... after_ignite=2.2`, `LIT client= why=reveal flicker=1 card=1` (or `why=cut|watchdog
flicker=0` for a scene cut after the ignite), `BLAZE ... blaze=1`, `LIT_FAIL` if the entity pool refused the card.

### What only the playtest can tell

Whether the dull bake reads as an unlit gate in the engine's exposure, whether scaleRGB 16 is "very bright" against
the sky and the fireball, and whether the card sits over the bake to the eye (the measured bearing is the only
registration; a screenshot re-measures it, section 3).

---

## 7. THE FIFTH PASS (2026-09-30): every gap shorter, the sign lit as the white burns out, a mover that never judders

User, after playing the fourth pass: *"it is looking good. My main issue is that ... things happen a bit too slow, so
it's almost like you're waiting at each step a little bit too long ... you're kind of sitting there a little bit too
long waiting for the spaceships to explode. Then when they explode, you almost still see the sign, but it's not even
glowing. So it's like taking a little bit too long to light up ... when you're falling, the player kind of wavers up
and down ... when you're going up, it's smooth. But when you're going down, he's kind of wavering up and down, up and
down, up and down. And it just looks clunky."*

### The pacing (the same beats, every gap shorter)

| beat | fourth pass | fifth pass |
|---|---|---|
| the turn onto the sign | 0.35 -> 2.6 s (2.25 s) | 0.3 -> 1.9 s (1.6 s for a turn up to 110 deg; a bigger turn takes up to 2.05 s, `TURN_REF` / `TURN_MAX`, so the camera never steps past 150 deg/s and always settles before the charge) |
| the warps | 1.5 / 2.25 | 1.3 / 1.95 |
| the standoff | 0.8 s | 0.6 s |
| the charge -> impact | 3.4 -> 4.6 (a 1.2 s ram) | 2.5 -> 3.6 (a 1.1 s ram; the charge sound's hit moved with it: `make_sounds.py` reads the ram's length from the jump script) |
| the sign lights | ignite 4.8 + 2.2 = 7.0 (2.4 s after the impact, the fire mostly gone) | ignite 3.8 + 1.0 = 4.8 (1.2 s after the impact: the flicker starts as the white burns out onto the fireball, through the fire) |
| the held, lit title | 7.45 -> 10.3 (2.85 s) | 5.25 -> 7.9 (2.65 s) |
| the swing back | 10.3 -> 12.1 (1.8 s) | 7.9 -> 9.4 (1.5 s) |
| control back -> touch-down | 13.1 -> 13.8 | 10.4 -> 11.6 |
| the flight | 13.8 s | 11.6 s |

`gen_fx.py` re-timed the blaze from the jump script's beats; `test_jump_title.js` now wants the sign lit >= 0.5 s after
the full white ends, <= 1 s after the white's burn-out and >= 0.9 s after the impact (a new negative control catches
the fourth pass's 2.4 s).

### The descent judder (the mover's trajectory)

Nothing in the arc's maths wavers (one sign change in the per-frame vertical motion, at the apex; second differences
under 1.1 u), the server clock is right (`LAND flight_ms=13800`), and the camera path hands control back on the
planned angles (`CINE_FREE angles= planned=` equal in the user's log). What is left is how the client shows a linked
player on a mover driven by one `MoveTo` per server frame: each 0.05 s segment ends exactly when the next snapshot is
due, so whenever the client's clock runs a hair ahead it clamps the stale segment and jumps on the next one. That is
invisible against the sky on the way up and a judder against the terrace on the way down, where the view faces near
geometry and the motion is mostly vertical. THE TRAJECTORY FIX: every frame the mover is aimed at the arc's point
`TOD_JUMPPAD_LOOKAHEAD` (2) frames ahead over as many frames, so the trajectory the client extrapolates always
outlives the snapshot interval; the mover still reaches every frame's point (the segment's midpoint is the next
point on a smooth curve; the `TRACK` log prints the error a few times per flight and `LAND` its maximum). The camera's
`RotateTo` takes the same lookahead. `test_jumppad.js` pins the loop's form.

This is the diagnosis the code allows; the playtest decides it (the log's `TRACK err=` should stay under a unit or two).

The user's own data point, after the fifth pass was built: *"when it was only the jump and no pause mid air this didnt
happen"*. The hang pass (2026-09-29) is exactly when the mover went from one `MoveTo` every 0.1 s to one every server
frame: a 0.1 s segment issued every 0.1 s never reaches its end before the next one arrives (no clamp), a 0.05 s segment
issued every 0.05 s does. That is the same mechanism the lookahead removes, with the hang kept.

THE EYE TRACE (the proof either way): `_tod_jump_title.csc` logs the local camera's position every CLIENT frame for 0.6 s
from the launch and for 3.0 s from the end beat (`[TOD_JT] TRACE up|down ms= x= y= z=`, ~600 lines a first flight;
`TOD_JT_TRACE_UP_SECS` / `_DOWN_SECS`, zero before a publish). Plateaus of ~50 ms in `z` = the trajectory clamping;
a steady slope = fixed; a sign-changing slope = something else.

### Files, gates, diagnostics

`_tod_jumppad.gsc` (the CINE_* defines, `TOD_JUMPPAD_LOOKAHEAD`, `arc_point()`, the flight loop, `cine_cam_plan`'s
`c.ty`), `_tod_jump_title.csc` rev 6 (RUN_SECS 1.1, WARP_A/B, REVEAL 1.0), `gen_fx.py` REVEAL 1.0, `make_sounds.py`
(the charge's hit READ from the jump script), `test_jumppad.js` (the lookahead loop pinned), `test_jump_title.js`
(the reveal window). Logs: `[TOD_JUMPPAD] INIT rev=5 ... lookahead=2`, `CINE_CAM ... turn_secs=`, `TRACK op= frame=
err=`, `LAND ... track_err_max=`; `[TOD_JT] INIT rev=6`.


## 8. THE DWELL + THE EARLIER SIGN (2026-10-01): 0.5 s more at the top, the sign lit 0.3 s sooner

The user: *"The pause mid air jump scene should last another 500ms before going down. Also the lights on the sign
should start about 300ms earlier then they do now."*

### Why a dwell, not a longer flight

Lengthening `CINE_SECS` alone stretches the WHOLE arc: the rider would sit somewhere else at the crash (the crash point
`TOD_JT_CRASH` is solved for the rider's position at the impact) and the float near the top would grow by only ~0.3 s
while the climb and the dive slowed too. Instead the first flight walks the SAME 11.6 s arc on the SAME hang clock and
`cine_arc_frac()` slips 0.5 s in round the apex:

    shift(x) = DWELL * ( x / SPAN - sin(2 pi x / SPAN) / 2 pi ),  x = t - (DWELL_AT - SPAN / 2) clamped to 0..SPAN
    arc share walked = ( t - shift ) / ( CINE_SECS - DWELL )

a raised-cosine slow-down (the arc's pace dips to 1 - 2 DWELL / SPAN = 0.62x at the apex, never a stop, no kink).
`DWELL_AT` 5.27 = the apex of the arc's own clock (hang_u 0.5 at 5.02 s) + DWELL / 2; `DWELL_SPAN` 2.6 = 3.97..6.57 s,
after the ignite (3.8) and before the swing back (8.4). Before 3.97 s nothing moves; from 6.57 s the flight is the old
one exactly 0.5 s later. Measured: 2.34 -> 2.84 s within 50 u of the peak, 3.28 -> 3.77 s within 100 u.

### The timeline now

| beat | before | now |
|---|---|---|
| the dwell | - | 3.97 .. 6.57 s |
| the sign flickers on (the reveal) | 4.8 s (ignite + 1.0) | 4.5 s (ignite + 0.7) |
| the card holds lit, the blaze starts | 5.25 s | 4.95 s |
| the swing back (`_end`) | 7.9 s | 8.4 s |
| the return ends | 9.4 s | 9.9 s |
| control back | 10.4 s | 10.9 s |
| touch-down | 11.6 s | 12.1 s |

The reveal at 4.5 s is 0.59 s after the full white ends (3.91) and just before it has burnt out (4.66): the flicker
reads through the thinning white onto the fireball.

### Files, gates, diagnostics

`_tod_jumppad.gsc` (`CINE_SECS` 12.1, `CINE_HOLD_SECS` 6.5, `CINE_DWELL` / `_DWELL_AT` / `_DWELL_SPAN`,
`cine_arc_frac()`, `arc_point( src, d, i, n, cine )`), `_tod_jump_title.csc` rev 7 (`TOD_JT_REVEAL` 0.7), `gen_fx.py`
REVEAL 0.7 (`fx_jt_blaze` regenerated), `scene_live.js` + `scene_geometry.js` (`cineArcFrac` in `eyeAt`),
`test_jumppad.js` (the dwell's contract + the shipping `cine_arc_frac()` run through gsc_eval + two negative controls),
`test_jump_title.js` (the white-end check fixed: it compared an absolute time to one measured from the impact and could
never fail; a negative control now proves it fires; the after-impact floor 0.9 -> 0.8). Logs: `[TOD_JUMPPAD] INIT rev=6
... move=lookahead+dwell ... dwell=0.5@5.27 hold=6.5`, `[TOD_JT] INIT rev=7 ... reveal=+0.7`. Knobs: the hang's length is
`CINE_DWELL` (keep `CINE_SECS` = 11.6 + it); the sign's timing is `TOD_JT_REVEAL` + gen_fx `REVEAL` together.
