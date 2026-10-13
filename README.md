# Tower of Doom II: Fallen Cybercity

Custom Black Ops 3 zombies map — the sequel to
[Tower of Doom: Cybercity](../tower_of_doom_cybercity), built on the same
blueprint and set in the same universe as
[Abandoned Cyber City](../abandoned_cyber_city_zombies).

Current source update: Necromancer summons remain suspended until conversion, Mangler aura flames are removed, and Soul Pulse uses an authored outward white ring without the caster flash. Full build queued with the high crown lamps while BO3 is open; user playtest pending. [Details](docs/necro_visibility_fix.md).

Fire Bow source update: original lava texture and three-layer materials restored across all eight variants. Full build and native comparison pending. [Details](docs/fire_bow_restoration.md).

C4 source update: disabled the C4 developer size cycle and selected the full explosion for every charge, with correlated playback logs. [Details](docs/c4_consistency_fix.md). Combined build waits for BO3 to close.

## Where this repo came from

Seeded 2026-09-20 as a full working-tree copy of `tower_of_doom_cybercity`
(TOD1 HEAD `57f565f` plus its uncommitted working-tree state — everything
on disk except `.git`, `tmp/` scratch and `local_sync_cache/`). At the seed
commit this repo builds and plays as Tower of Doom 1, byte for byte; TOD II
is iterated from that starting point.

**Tower II is isolated as `zm_tod2_cybercity`.** Its compiler, asset database,
conversion cache and output live in `C:\BO3Tools\TOD2Cybercity`. Build/sync
reject the shared tools root. The game sees only a new, uniquely named map
folder; Map One stays untouched. Setup: `tools/setup_tod2_workspace.ps1`.
See [the isolation rule](docs/154_tod2_isolation.md). Tower II has no Workshop ID.

## The twist (inherited)

The rounds never stop. There is no pause between rounds — the moment the last
zombie of a round spawns, the next round begins. One unbroken siege while you
fight your way DOWN the tower.

## The Fall (TOD II)

You start **inside the crown**, at the top of the tower. Pick a class, take
your first cards, and you get twenty quiet seconds to look around: a
Pack-a-Punch, the altar, and a 5,000-point gate. Then the alarm over the hall
lights and spins, a siren wails, and the horde comes in at a full sprint.
Linger past ninety seconds of that and a Doppelghast comes up through the
floor, then another every thirty. Once everyone is out the gate seals behind
you for good, the horde drops back to its normal pace, and the run really
starts: the causeway, the terrace (Quick Revive), then fifty floors DOWN
through the lounges to the plaza. Design record: [docs/160](docs/160_the_fall.md).

## The bottom (docs/158)

**The Tower Plaza** — the square arena with the tower in its middle — is the
foot of the descent. Each plaza wall has a door to a **Workshop wing** with a
partner bench (Civil Protector, Talon, R.A.P.S., Cerberus); below the plaza a
long open-sky stair drops into **the Undercity** (the Conduit, then the Vault
with its four windows, where the partner parts lie). Plan previews:
[docs/158](docs/158_tod2_base_layout.md).

## Build & play

```powershell
.\tools\build_map.ps1          # full build (geometry + LED bake + linker)
.\tools\build_map.ps1 -GscOnly # fast path for script/zone-only changes
.\PLAY_NORMAL.bat              # launch through Steam
```

The `.map` is **generated** — edit the layout tables in
`tools/gen_tower_map.js` and re-run `node tools/gen_tower_map.js`; never
hand-edit the `.map`.

Working notes and conventions: [CLAUDE.md](CLAUDE.md) (inherited from TOD1 in
full; its dated log entries describe TOD1 history). Portable BO3 mapmaking
reference: [docs/BO3_MAPMAKING_KB.md](docs/BO3_MAPMAKING_KB.md).
