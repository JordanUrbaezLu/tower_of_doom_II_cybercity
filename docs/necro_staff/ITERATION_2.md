# September 27 playtest corrections

The user rejected the first staff pass: flat-looking surfaces, a bent first-person
shaft, intersecting Tier 2 skull/collar, and a missing-looking Soul Blast.
Compilation success did not establish acceptable visual quality.

Evidence: `tmp/elite_tracking/runs/20260927_180409_494_78758139/console_mp.log`.
The server recorded eight Soul Blasts and client playback callbacks. The first
600-unit blast incorrectly read radius band 0 on the client; later casts read 3.
The ring replacement had HDR scale 1 and additive blending; the native donor
`gfx_ring_thin` uses scale 64 and emissive blend. The repeated helper exceptions
came from concatenating undefined hound movement fields into diagnostic strings.
These errors are distinct from the ring's confirmed playback requests.

Changes:

- Removed the exporter's 75-degree position-dependent head bend. View/world
  vertices now differ only by one rigid axis conversion, enforced for all LODs.
  Reframed both hands and the whole staff together in the animation poses.
- Removed Tier 2's intersecting halo and seated its skull on a short ferrule.
- Authored separate 2K chased-shaft and forged-blade maps. The old normal map
  differentiated height per pixel without resolution scaling, producing almost
  no relief. Cylindrical shaft UVs now preserve complete interlace patterns.
- Baked an exclusive 2K skull UV atlas through Blender MCP/Cycles, using native
  bone color/normal inputs plus cavity shading and fine pores. Enlarging the
  source alone is not counted as new detail. All 15 staff images are resident.
- Restored the donor's ring material type, HDR scale and reveal mask. The hollow
  ring still has no center flash, light or lens flare. Client playback waits one
  network tick before reading the band and retains the original cast position.
- Strengthened the outward thrust, peaking around the 140 ms wave expansion.
  `STAFF_PULSE_POSE selected=` checks the proxy actually became current; existing
  lifecycle cleanup remains. Client `PULSE rev=native_ring_2` logs allocation and
  radius band, not a claim that rendered pixels were observed.
- Guarded optional helper movement fields in logs to prevent script exceptions.

Reproduction: actual Blender MCP on the isolated studio runs `author.py`,
`refine_bone.py`, `export_preview.py`, `animations.py`, `motion_preview.py` and
`motion_sequence.py` under `tools/necro_staff`. Then run `install.py` and
`node tools/gen_tod_twins.js`. `refine_mount.py` applies the final author-script
collar heights to an already baked master without rebaking its unchanged skull.

Validation: native API/arity checks, all exported vertices rigidly matched,
resident texture definitions and non-flat 2K inputs, tier/PaP bindings, grip
distances, casting seams and lifecycle tests. Build through the guarded FULL
path because GDT/model/image definitions changed. User visual review remains
required; no game launch by the agent.
