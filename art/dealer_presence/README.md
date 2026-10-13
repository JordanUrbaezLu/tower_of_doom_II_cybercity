# The Dealer watches the descent

**Status: source ready (`wired=true`); guarded full build and native playtest
pending.** The true 1024px portrait and seven matched views are complete and
reviewed. The exact reviewed PNG/GDT are installed; the marked map insertion,
zone image row and automatic source gate are active. The source/support checks,
exact map-change audit and static geometry lint pass. No build, sync or game
launch was performed by this authoring task. The dedicated studio is closed.

Three small, fixed surveillance panels foreshadow the same Dealer seen at the
Black Market and on the sky monument. The user established him as the final
boss; this pass adds visual presence, not a fight, dialogue or new encounters.

| Existing support | Portrait centre (native units) | Panel size |
| --- | --- | --- |
| Crown junction west wall | -318, 6360, 19480 | 96 x 112 |
| Floor 20 core service face beside the SW lounge approach | -192, -258, 7592 | 64 x 80 |
| Lower power corridor north wall | 1040, -422, 64 | 64 x 80 |

The wall plates share the existing graphite and worn bronze material library.
The image is a new 1024px photograph of the **actual exported shop vendor and
mask**, with the same red X eyes, uneven grin, armored brows and black hood.
Its normal mip chain is retained. The screen has fixed .65 emission; the frame
has none. No light entities, collision, runtime scripts, animation or sounds
are added. Total cost: 42 small mesh quads, 84 triangles, one 1024 image and one
screen material; existing frame materials are reused.

`tools/dealer_presence/layout.js` owns placement, geometry and UVs. The map's
marked `DEALER PRESENCE` block calls that module. `geometry.json` is the exact
reviewed output. `context.json` comes from actual emitted local map surfaces;
the support check tests all four panel corners against opaque native walls.

Authoring uses a tiny separate Blender MCP studio on port 9897. It never opens
or writes the shop or sky masters. Launch only with `start_studio.ps1`, which
refuses existing Radiant, BlackOps3, cod2map, linker, gdtdb or Blender processes
before starting Blender. Native guards also run inside MCP and before each
render. Run through `mcp_call.py`:

1. `author_portrait.py`: imports only native vendor and mask meshes/maps; writes
   `dealer_surveillance.blend`, `dealer_surveillance_1024.png` and provenance.
2. Keep the final candidate PNG/GDT outside converter sources during review.
   The preview validates their hashes against the recorded installation recipe.
3. `node tools/dealer_presence/layout.js`, then `inventory.js`: captures the
   generated geometry and actual map context.
4. MCP `preview.py`: paired before/after player cameras and material detail.
   It can read identical candidate bytes from staging before installation.
   After review, `python -B tools/dealer_presence/install.py` validates canonical
   sources and installs the exact reviewed image/GDT bytes.
5. `python -B tools/dealer_presence/wire.py --check`: nonmutating prerequisites.
6. `python -B tools/dealer_presence/wire.py`: inserts only the owned marked
   block, image row and automatic guarded-build source check into current shared
   files, regenerates the current map,
   then runs the source gate. This does not sync, build or launch anything.
7. `python -B tools/dealer_presence/verify.py --check`: nonmutating active source
   gate, or a strict proof of absent runtime wiring while `wired=false`.

The preview uses actual native maps, gloss ranges, frame geometry, UVs and
player positions under neutral review lighting. It approximates BO3 shading;
it does not reproduce the game's probes, exposure or stock props. Portrait
studio lighting is photographed screen content, not baked model albedo.

`changes.json` and the two `.diff` files record the exact shared-source changes.
The current map minus these 42 patches matches its pre-edit version after
ignoring GUID/brush renumbering. The wire-last receipt preserves the current
shared files immediately before activation, including the guarded build script.
Static geometry lint passes. The user playtests.

After a guarded full build, run:

```
python -B tools/dealer_presence/verify_native.py --build-snapshot art/sky3d/dealer_review/build_inputs.json --build-log <full.log> --output art/dealer_presence/native_build.json
```

The combined build snapshot must include this GDT, installed PNG, generated map
and zone. The post-build proof requires their deployed hashes, fresh material
and image ledger entries, actual private database bindings, and fresh BSP/LED
receipts consuming the exact reviewed map. It does not claim decoded compiled
BSP vertex UVs or user-verified native appearance.
