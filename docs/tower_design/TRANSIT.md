# Top-floor transit bay

> **SUPERSEDED 2026-09-29 by [docs/196](../196_departure_hall_and_first_jump.md)**: the bay is now
> THE DEPARTURE HALL (a cruciform hall, pads at (-1080,-40) / (-1480,360) / (-1080,760), arrivals at
> (-620,360)). The routes, locks, costs and runtime below are unchanged; the room, its coordinates and
> its lights described here are the 2026-09-27 box, kept for history.

FULL build passed; unplayed. [Build evidence](BUILD_RESULT.md). Includes the prior lighting/material and
24-drop descent passes. [Visual review](transit/review.html) ·
[Build handoff](TRANSIT_HANDOFF.md).

The crown jump pad still lands on the main tower's top deck. A new covered
room joins the west edge of its terrace through a 160-unit opening. It has
cobalt tread flooring, violet wall panels, gold framing, city-facing windows,
three ceiling light pools and a fitted reflection probe. These are the existing
crown materials and native teleporter model; no new texture/FX assets.

Three pads link the top bay with the existing floor 30, 20 and 10 pads.
The newer arena pass replaces floor 40's ordinary link with its entry chamber.
Each regular floor pad returns upstairs. The hub's orange/green/blue insets
match those floor districts. Its entry apron is the shared arrival point,
outside every departure gather radius. The room shares roof_zone and has two
risers, so its pressure follows the top landing's existing activation.

The old bottom bay, four pads, enclosing walls, zone and paid door are removed.
A shorter open platform with low gold rails holds one crown-return pad and
shares base_zone. The crown's existing right-hand room now has a functional
pad linked back to this bottom platform. Its old duplicate prop is removed.
The left power room and straight-ahead jump-pad route retain their positions.

| Route | Availability after power |
|---|---|
| Top bay → floor 30 | Floor 30 reached through enter_lap31 |
| Top bay → floor 20 | Floor 20 reached through enter_lap21 |
| Top bay → floor 10 | Floor 10 reached through enter_lap11 |
| Each floor → top bay | Available once that pad is reached |
| Bottom → crown right-hand room | Available once the bottom is reached |
| Crown right-hand room → bottom | Bottom reached through enter_lap1 |

There is no new charge or room purchase at the top. The existing crown side
door keeps its purchase; a bottom return opens it from inside for free to
avoid trapping arrivals. The 0.8-second charge, per-pad 60-second cooldown,
fire-time gather, downed teammate ride-along, native pad states and sounds
remain. Destination flags fail closed if missing, and every destination zone
must already be enabled before the trip can start.

The first occupied bottom return reopens the crown's sealed main gate and
restores its zombie spawning and co-op respawns before moving riders. The
opening alarm phase stays completed. The seal watcher, sealed-zone watchdog,
ordinary-riser filter and Doppelghast relocation filter all recognize the
return opening. Empty charges do not unlock doors or reopen the crown.

Floor-arrival centres move 48 units toward their lounges (208 units from the
departure pad instead of 160), so the existing 48-unit co-op fan-out stays
outside its 120-unit gather. Their existing gantry risers follow the generated
arrival offset. A four-player landing and immediate opposite-direction charge
remain a native playtest case.

All eight regular route rows and their map markers are emitted from one layout table.
Source checks inspect actual emitted floor support and capsule headroom, pad
spacing and arrival fan-outs; they execute the shipping lock/zone/preparation
and crown-return functions with native calls stubbed. The navmesh build gate
also checks every pad and arrival fan-out against the appropriate compiled
walking component, without turning teleports into ordinary stair connections.

Passed: transit behavior/geometry, whole-map geometry, mirrored 49-floor
parity, broken-drop regression, jump-pad arc, hoop, GSC arity/native API,
teleporter FX, Doppelghast, crown preservation and surface/conduit audits.
Logs: tmp/transit_bay/source_checks.log, geometry.log, parity.log.
The preview uses actual map solids and the shipped teleporter binary with
studio lighting. The cutaway hides the ceiling for inspection. It does not
represent native lighting, FX, navmesh or game verification.

Automatic dev logs: `[TOD_TELEPORT] INIT rev=2`, `ROUTE`, `STATE`, `CHARGE`,
`DENY`, `FIRE`, `ARRIVE`, `PAD_FAILED`; and `[TOD_FALL] RETURN_OPEN`.
They include route ID, source/destination, zone, lock reason, riders and player
origin as appropriate. After the user's test, archive console_mp.log with
tools/capture_ai_logs.ps1. Check both directions of each link, destination locks,
co-op/downed transport, cooldown, crown gate access and enemy pressure after
return. Builds use the guarded scripts; Archer clearance is no longer required.
The user performs the native playtest; no game launch from this session.
