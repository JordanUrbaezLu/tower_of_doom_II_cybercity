# 158 — The TOD II base: the Undercity, the Tower Plaza, the Workshop Wings

> **2026-09-23, later:** superseded in part by [docs/160 THE FALL](160_the_fall.md) — the party spawns in the crown hall and DESCENDS; the Vault is the run's end, not its start, and Quick Revive moved to the terrace. The geometry below is unchanged.


Requested 2026-09-23. The user's brief, in their words: *"it's kinda gonna
start in a cyber basement ... you're gonna have to open up a few doors, not
just going up but laterally and up ... zombies will spawn at four windows at
spawn and then you'll make your way to the tower zone ... it'll be square-ish
and then in each direction there will be a door that branches out to another
section ... a hallway that branches out to another room and each one of those
rooms will have a crafting bench where you can then create your protector ...
four different protectors ... the tower will be right in the middle of this
open area room."* The design was left to me.

**STATUS:** generated, lint-clean, BUILD RESULT RECORDED AT THE END OF THIS
DOC. UNPLAYED — the user tests. Plan previews (drawn from the emitted `.map`,
`node tools/preview_base_plan.js`): `docs/158_base_plan/plan_undercity.png`
and `plan_plaza.png`.

**Partner integration update:** the eight temporary collectible parts are now
beside the actual Vault spawn, as requested in the partner task. The Conduit
shelf and its generated anchors remain available for later placement. Bench
locations stay in the four wings. [Partner implementation](159_buildable_partners.md)
is authoritative for the pickup positions, prompts and diagnostic records;
the shelf placement described below records the original layout proposal.

---

## 1. The route

```
                      z = -384                              z = 0
   ┌──────────────┐  enter_conduit  ┌───────────┐          ┌─────────────────┐
   │  THE VAULT   │───(500)────────▶│THE CONDUIT│═══shaft══▶│   TOWER PLAZA   │──▶ enter_lap1 ...
   │  spawn       │  (lateral)      │ parts     │ 32 treads │ (the old arena, │
   │  4 windows   │                 │ shelf     │ enter_base│  untouched)     │
   │  Quick Revive│                 └───────────┘  (750)    │  core in centre │
   └──────────────┘                                          └────┬──┬──┬──┬──┘
                                        enter_wing_n/e/s/w (1000) │  │  │  │
                                                       N Civil Protector, E Talon,
                                                       S R.A.P.S., W Cerberus
```

| Stop | What it is | Why it is there |
|---|---|---|
| **THE VAULT** | The spawn room, one tower floor DOWN (z −384, floor 640 × 560, 192 ceiling, cyan seam band, four cyan pilasters, two ceiling beams). Four **window niches** — 160-wide, 96-deep recesses through the walls with a lit red back panel, a 12u cyan sill and a `clip_player` mouth — one on the W wall, one on the E, two on the S. Each holds a riser: the horde climbs out of the windows and walks into the room; players cannot climb in. **Quick Revive** backs the N wall east of the door. A cyan floor trace runs from the spawn rows to the door. | "Cyber basement ... zombies spawn at four windows." The solo Quick Revive carve-out (a self-revive before the first door) moves with the spawn. |
| **enter_conduit** | The LATERAL door, in the wall the Vault shares with the Conduit. 500 points. | "Not just going up but laterally." |
| **THE CONDUIT** | The second basement room (512 × 576), two risers flanking the stair mouth, two ceiling beams, a trace from the door to the stair foot. The generator emits a **parts shelf** along its west wall (`partner_part_org`, eight anchors 64 apart) — currently UNUSED: the peer's partner session placed the eight parts in a row beside the Vault spawn instead (docs/159), keeping the shelf anchors for a later move. | The fetch: parts on the way in, benches in the wings. |
| **THE SHAFT** | One straight 32-tread flight climbing EAST (the tower's own 12/32 stair scale, RISE × 32 = LAP_RISE, a ramp clip over it) between 128-tall banded walls, **open to the night sky** — you climb out of the dark into the neon. A 240-deep top landing. | "And up." The reveal. |
| **enter_base** | The UP door, in the plaza's WEST wall (south half, y −240..−80). 750 points. | The Tower Plaza reads as the thing you earn. |
| **THE TOWER PLAZA** | The old base arena, **byte-for-byte in place**: core, lap-1 door, Heavenly Gift Altar, hoop, crate, rampage inducer (nudged 16u east), teleport bay (S), power hall (SE), perk parking on the N wall. | A dozen scripts read absolute base coordinates (teleport pads, station, hoop, crate, inducer, perk pads, secret bears, music emitter). Building around it costs nothing; moving it would touch all of them. |
| **THE WORKSHOP WINGS** | Four, one door per plaza wall: a 160-wide hallway (364 long, a hue band at eye height) into a 512-square open-sky room; a **partner bench** on the far wall facing the door, a hue panel behind it, a hue floor ring, two risers by the entrance corners. N green / E orange / S purple / W red. 1000 points each. | "In each direction there will be a door that branches out ... a hallway ... a room ... a crafting bench." |

## 2. Where every door went, and why (the plaza's walls)

Every placement was measured against the LIVE use triggers on that wall — the
map's standing "no two use-triggers overlap" rule (door spheres are r96 at
org ± off; the generator now ASSERTS this for every new door, against every
other ground door, the base crate trigger, the inducer trigger and every
ground riser).

| Wall | Opening | Note |
|---|---|---|
| W | `enter_base` y[−240,−80] | NOT centred: the base ammo crate's trigger (−376,0) r72 reaches x=−448 and a centred door's inner sphere (−490,0) r96 reaches x=−394. |
| W | West Workshop y[320,480] | |
| N | North Workshop x[−80,80] | The perk park row is re-pitched 8 machines at 110, 4 each side; Quick Revive parks in the Vault (its pad). |
| E | East Workshop y[300,460] | In the NE gutter, north of the lap-1 flight's anti-bypass wall; the power hall keeps the SE. |
| S | South Workshop x[−540,−380] | Hugs the SW corner: the bay door owns the centre and the rampage inducer's r96 trigger owns x[−360,−168]. `INDUCER_X` −280 → −264 so both clear by 4u. The room is offset west of its hallway (the teleport bay is in the way); its east wall abuts the bay's west wall. |

The plaza's own risers moved off the new door mouths: SW (−470,−470) →
(−470,−380); NW (−470,470) → (−380,440). NE (470,470) stays (115u from the East
Workshop's inner sphere).

## 3. Coordinates (all in `tools/gen_tower_map.js`, the one source)

| Thing | Value |
|---|---|
| `UC_Z` (Undercity floor) | −384 = −LAP_RISE |
| Vault interior | x[−2592,−1952] y[−1028,−468]; ceiling underside −192 |
| Vault windows | W (y −748), E (y −748), S (x −2432, −2112); riser 58 past the inner face |
| Quick Revive pad | (−2060, −497, −384), faces south (`vault_qr_org`) |
| Initial spawns | 4 × 2 at x −2464..−2080, y −800 / −836, facing north |
| `enter_conduit` | slab x[−2352,−2192] in the shared band y[−468,−448]; org (−2272,−458,−344) off (0,40,0) |
| Conduit interior | x[−2528,−2016] y[−448,128]; stair mouth y[−288,−32] in its E wall |
| Parts shelf | (−2503, −400 + 64n, −374), n = 0..7 |
| Shaft | foot landing x[−1996,−1824]; treads x[−1824,−800] (32 × 32), top z 0 at x −800; top landing x[−800,−560]; y[−288,−32] |
| `enter_base` | slab x[−560,−540] y[−240,−80]; org (−550,−160,40) off (40,0,0) |
| Wing frame | u outward from the arena centre, v across: door u[540,560], hallway u[560,924], room interior u[944,1456], bench origin u 1429, risers (u 1000, v rc±200) |
| Benches (partner id → org, yaw) | 0 N (0,1429) 270 · 1 E (1429,380) 180 · 2 S (−536,−1429) 90 · 3 W (−1429,480) 0 |
| Sky floor | −512 (was −64), so the seal sits under the Undercity |
| Zones | `vault_zone` (start), `conduit_zone` (room + shaft), `base_zone`, `wing_n/e/s/w_zone` |
| Prices | `CONDUIT_DOOR_COST` 500, `BASE_DOOR_COST` 750, `WING_DOOR_COST` 1000 (-GscOnly to change) |

Generated outputs consumed by scripts: `_tod_door_data.gsc` (59 doors),
`_tod_breather_data.gsc` (`vault_qr_org`, `partner_bench_org/yaw/room`,
`partner_part_org/yaw`, `undercity_z`), and the bench collision clips are cut
in the `.map` from the same anchors (`wing <k> partner bench body`).

## 4. What changed outside the generator

- `_tod_partners.gsc` (a peer session's buildables, 2026-09-23): `stations()`
  reads every bench and part anchor from the generated data; `bench_x()` is
  gone. Trigger geometry is unchanged (57 in front of a bench, 31 in front of
  a part). The "both pieces are by the spawn wall" print now says the Conduit.
- `_tod_perk_scatter.gsc`: the Quick Revive pad is `vault_qr_org()`.
- `zm_tod2_cybercity.gsc`: `init_zones[0]` is `vault_zone`; the zone graph
  gains Vault → Conduit → plaza and plaza → each wing.
- `tools/lint_tod_geometry.js`: `MODEL_CLIP_COLUMNS` also exempts
  `partner bench body` (the crafting table ships no collision, like the
  crates). Self-test re-run: OK.
- The plaza's respawn group (`tod_respawn_base`, gated on `base_zone`) keeps
  co-op respawns beside the tower once the plaza is open; the start-room group
  is in the Vault.

## 5. What the user should look at first (UNPLAYED)

1. Spawn: you are in the Vault facing the Conduit door; four windows glow red;
   zombies climb out of them and over the sills. Quick Revive on the N wall.
2. Buy the Conduit (500): the parts shelf along its west wall (eight props
   with prompts), the stair mouth on the east side.
3. Climb the shaft (open sky above) to the plaza door (750).
4. The plaza is the old arena. Each wall has a Workshop door (1000); each
   room has one bench with its scale model preview. **Bench facing is the one
   number to verify by eye**: yaw 270 on the N wall meant "faces south" in the
   peer's placement; if a bench faces its wall, flip `faceYaw` by 180 in
   `wingFrame()` — one line, every bench.
5. Perk machines: eight park on the plaza's N wall at pitch 110 (they scatter at
   load); Quick Revive never moves.

Dev logs (`tod_dev`): `[TOD_PARTNER] BENCH id=.. room=.. org=.. yaw=..` at
startup, `[TOD_PARTNER] STATIONS ready conduit_shelf_parts=8 workshop_benches=4`.

## 6. Known limits and follow-ups

- **Elite sky-drops under a ceiling.** Rogue Protector waves (every 3rd round)
  and the Panzer land from above; if the party is still in the Undercity they
  will drop through the ceiling visually. Mechanically fine. A follow-up can
  hold elite debts until someone is above z 0.
- **The windows are risers, not boards.** The stock board barricade prefab
  (`barricade_reciever_wood.map`) is in the tools root; wiring real boards is a
  separate, stock-trap-laden feature.
- **Door prices are placeholders** for the user's economy call.
- **Music, gauge, luck** all treat z < 0 as floor 0 (checked: `floor_of`,
  `real_floor_of`, `music_floor_of` clamp).
- The parts are all on one shelf; scattering them across the base complex is a
  one-table change (`PART_SHELF_*`).
- A pre-existing pair, `enter_lap1`'s south sphere and `enter_power`'s east
  sphere, overlap by 28u (shipped since v10); the new overlap assert is scoped
  to the new doors so it does not fail on it.

## 7. Build record

FULL BUILD OK 2026-09-23 22:57:23 Eastern (`tmp/base_layout_20260923/build.log`):

| Check | Result |
|---|---|
| `.ff` | `zm_tod2_cybercity.ff` 210,598,400 B @ 22:57:23; English 232,128 B @ 22:57:25 |
| BSP / lighting | `.d3dbsp` 21,658,148 B @ 22:55:41; fresh `.led` 50,489,869 B @ 22:56:42 (45.1 MB before the rooms) |
| sound bank | `.all.sabs` 197.9 MB (full); `.all.sabl` 58,154,496 B @ 22:57:07 |
| linker errors | the ten known-waived substitutions only (mechz.zpkg, knife_melee_surface x2, gfx_teleport_tube, mtl_glass, the four 115-grenade / bgb materials, p7_zm_zod_fuse) |
| navmesh gate | OK: 1,138 faces, 2 components (tower + crown road, spire). Probe: vault 13 faces, conduit 2, shaft 2, wings 5 / 5 / 7 / 7, plaza 16 — ALL in the tower's component |
| repo vs deployed | `diff -rq` scripts / zone_source / ui clean; `.map` identical; nothing synced after the `.ff` |
| gates in the build | geometry lint 0/0/0 (+ self-test OK), hall bunkers 0, hints 113/190, arity OK, cyber roster, partner test 66/66 |
| dev flags | unchanged from the tree (`tod_resolve_dev_flags`); no launch |

Mid-build note: the peer partner session synced its parts move (parts beside the
Vault spawn, docs/159) at 22:55:59, between my sync and the linker, so the
`.ff` carries that version — which is also the repo's current one. Radiant's
usual "NavVolume generation is skipped" warning only.

UNPLAYED — the user tests.
