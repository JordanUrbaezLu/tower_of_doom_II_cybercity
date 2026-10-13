# Charcoal horde and normal-round elites

User direction, September 25, 2026: use Hellbound's charcoal zombies with a
gray/black/red palette, red eyes and no orange in their own textures or emission.
Add the default Hellbound Mangler and a black Doppelgast with original eyes and
robotic legs, mixed into normal rounds. Earlier spoken names were corrected to
**Doppelgast**. Existing `doppelghast` code/asset identifiers retain their spelling.

[Blender art preview](review.html) · [Saved Blender scene](../../art/cyber_elites/cyber_elites.blend)
· [Export manifest](../../art/cyber_elites/manifest.json)

## Shipping behavior

- Ordinary zombies use `archetype_tod_charcoal_zombie` in every mode. The
  historical `tod_cyber_dev` factory marker now selects this charcoal character.
  Body, head and all twelve damage/detached models preserve Hellbound's native
  geometry, UVs and weights. Three incorrect donor limb bindings are corrected:
  `legDmg2` uses the body with its right leg removed; detached left arm/leg use
  their `s_*spawn` pieces, rather than the retained damaged torso/lower body.
  Three albedo maps are grayscale;
  the eye albedo/emission map has zero green and blue. Both eye tints are pure
  red, with the donor's HDR scale of 16. No additional eye light/FX host is used.
  **The eye-glow PARTICLES (PK04, 2026-10-04):** stock `zombie_spawn_init` lights
  `level._effect["eye_glow"]` on `j_eyeball_le` for every zombie, and stock sets
  that to `zombie/fx_glow_eye_orange` - so until PK04 orange particles floated over
  these red eyes. `_tod_eye_glow.csc` now sets `level._override_eye_fx` to the
  GENERATED `tod/cyber/fx_tod_charcoal_eye_glow_red` (the stock orange's shape, hue
  0 in every key) and gives the golden zombie `tod/cyber/fx_tod_golden_eye_glow`
  (`tools/fxgen/horde_eyes/`, gated by `make_fx.py --check` + `test_eye_glow.js`).
- `tod_doppelgast_black_robot` retains the original upper body, both heads,
  original eye materials, complete skeleton and existing animation set. Its
  organic legs are removed below the hip collars. Blender-authored mechanical
  thighs, hinges, actuators, shins, ankles and toes follow the existing hip,
  knee, ankle and ball joints. Body albedo is near-black with neutral highlights;
  legs use black coated metal, darker rubber and dark piston hardware.
- Manglers use `hb_bo6_mangler`, Hellbound's default skin and six native clips.
  Model, animation and texture dependencies are unchanged. Default cannon FX
  and audio are preserved. Rare skins and Hellbound's unrelated class-path
  player slows are not enabled. Cybercity's existing rule remains no player stuns.
- The round director introduces one Doppelgast on round 3 and one Mangler on
  round 5. From round 6 it alternates them, allowing one elite per round, two
  from round 14, and three from round 22. It waits 25 active seconds between
  deliveries and allows at most two of these elites alive together. Unused
  budget expires on round change; kills do not queue replacements.
- The existing combined elite ceiling and two free actor slots are respected.
  Upgrade pauses, world pauses, disabled spawning, spire trials and finale
  sequences hold delivery. Positions use the existing enabled-zone/door
  frontier checks and player clearance; crown-island boundaries are enforced.
  Sealing the emptied crown removes any remaining new elite without a reward.
- Both elites use this map's killer reward/luck hooks and stock death callbacks.
  `tod_only_zombies` continues to disable the previous special-enemy directors;
  this new director is the explicit exception for the requested pair.

## Authoring and verification

`tools/cyber_elites/mcp_bootstrap.py` starts an isolated upstream Blender MCP
server on loopback port 9884. `mcp_call.py` uses the MCP SDK's real ClientSession
and records the response in `tmp/cyber_elites_mcp`. `01_author.py` creates the
scene, derived textures, native binaries and map-owned GDT through that server.
The preview is a neutral studio render with approximate native materials.

`02_integrate.py` records the initial donor-port procedure; the shipping GSC
is maintained directly after that import. Donor inputs are read-only. The
guarded sync copies only map-owned outputs to `C:\BO3Tools\TOD2Cybercity`.

`verify_assets.py` checks export hashes, full rig preservation, untouched upper
body/eyes, original charcoal geometry and weights, and unchanged Mangler
dependencies. `--palette` additionally decodes every pixel with Pillow; the
standard build pins those verified texture hashes. `--compiled-ledger` checks
native triangle coverage for all fifteen custom models and the default Mangler.
`test_cyber_elites.js` executes the shipping director with a controlled clock to
check pauses, actor/position/target failures, budget growth and debt expiry.

The Blender/source checks and a successful build do not establish native visual
or gameplay acceptance. The user performs that playtest; no game was launched.

The final full build passed on September 25, 2026: fastfile **209,794,304 bytes**,
fresh lighting data **150,000,159 bytes**, all fifteen custom models plus the
default Mangler passed compiled triangle coverage, and the build reported the
same eight known-waived asset warnings. Source/deployed script, UI, zone, sound,
AI-table, custom-model and GDT hashes match; nothing was synced after the fastfile.
Exact timestamps, hashes, sound-bank sizes and native model rows are retained in
[deployment.json](../../art/cyber_elites/deployment.json).

### First user run: missing Mangler cannon animation

The user's 13:07 run failed during server load: `animation 'hb_mangler_cannon'
not defined in anim tree 'generic'`. Archived console:
`tmp/elite_tracking/runs/20260925_130758_272_059e6e76/console_mp.log`, lines
3568–3581. The xanim was packed, but its entry was absent from `hb_mangler.ai_am`.
The map's table now includes `anim_zombie_mangler_cannon,hb_mangler_cannon`.
The importer preserves this correction, and the director build test checks every
scripted `%animation` against each elite's mapping table. Its negative control
removes the cannon row and must identify exactly the user's missing clip.
The initial successful build was not proof of runtime animation-tree resolution.

## Playtest diagnostics

### Robotic leg material repair, September 26

The user reported missing textures on the Doppelgast's robotic legs. The first
export used constant image bindings and one collapsed UV coordinate per face.
`04_robot_materials.py`, executed through Blender MCP, replaces those with twelve
real color/normal/specular/gloss images and UVs across the 152 authored parts.
The native materials explicitly use the project's full-specular shader with
emission disabled. Charcoal armor, dark steel pistons and rubber retain the black
cyber theme; the original skeleton, organic upper body and eye materials remain.
The original authoring recipe now calls this repair so regeneration preserves it.
Source checks reject collapsed UVs, missing image bindings and unexpected glow.
Preview: [alarms and legs](../crown_alarm/review.html). Native build passed
September 26 at 14:36:13 Eastern (FF 189,911,680 bytes). All twelve leg maps and
their three materials are present in the compiled ledger; compiled model coverage
and 341 deployed input hashes pass. Evidence: `art/cyber_elites/leg_texture_deployment.json`.
Native appearance and animation still await the user's playtest; no game launched.

The September 26 console was archived at
`tmp/elite_tracking/runs/20260926_135956_263_3b5c2894/console_mp.log`. It reaches
Mangler initialization and records Doppelgast spawn/ready/sprint/juke/death; it
does not repeat the missing-cannon server compile failure. The corrected table
and compiled mapping evidence are in `art/cyber_elites/animation_fix_deployment.json`.

Existing dev mode automatically records `[TOD_CHARCOAL]` appearance and gib
states (first 24 tracked zombies), `[TOD_ELITES]` budgets/hold reasons/spawns,
`[TOD_DOPPEL]` motion/attacks/deaths, `[TOD_MANGLER]` rig checks/cannon/cleanup,
and `[TOD_BO6_AUDIO]` source events. Repeated delivery hold reasons are logged
only when they change. After the user tests, archive the console with
`tools/capture_ai_logs.ps1` before investigating.

Check the charcoal eyes in blackout and powered lighting, detached heads/limbs,
both elite introductions, robotic leg animation during running/jukes/death,
Mangler cannon timing, upgrade pause/resume, door progression and crown sealing.
