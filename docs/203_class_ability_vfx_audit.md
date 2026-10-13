# 203 - Class ability VFX audit (2026-10-02)

**Status: BUILT FROM (2026-10-02 19:40, "Go ahead all of them"). Sections 1-4 are the
audit as found; section 5's proposals 1-4 and 6 are IMPLEMENTED (CHANGELOG 2026-10-02 19:40);
proposal 5 (the Hellbound kill-feel layer) was implemented and then REJECTED BY THE USER the
same evening ("This hell bound work we can remove, I actually dont liek this") and removed
whole (CHANGELOG 20:05) - never port it again:
`_tod_ability_fx.gsc|.csc` (one owner, both views), `tools/ability_fx/gen_fx.py` (25
generated effects), `_tod_kill_feel.gsc` (Hellbound's layer ported), `TodAbilityFeedback.lua`
(the tiles react), the landing-ring fix; the bare server one-shots in s4 are NOT changed
(check them in a playtest log first). The smaller items in proposal 7 are still open.**
**Original status: FINDINGS ONLY.** User: "Tower of Doom 1
has such good visual effects on the players abilities and I feel this map lacks
that interaction and awesome visuals ... Dash upgrade could use some, The soul
pulse is super ugly and dull ... Breacher explosive jump and heal ... Demon
Slayer activation ... how they look in 3d world from other perspectives too."

Three static audits (code, .efx element dumps, zones; no game run): this map,
Tower of Doom 1 (`../tower_of_doom_cybercity`), and the Hellbound donor
(`../tower_of_doom_II_hellbound`). Script paths below are under
`scripts/zm/zm_tod2_cybercity/` unless stated.

## 1. The verdict

The gap is real and it has a shape. This map's **weapons** carry strong effects
(the Soul Suck beam, the Cluster, the C4 blast, the Rune Prison, the Cyber Smash
slam) because most of them ride stock or donor weapon assets. The map's
**abilities and buffs** are where it goes flat: the things a card gives you
mostly happen as a number change with nothing to see, nothing to hear, and
nothing a teammate can read on your body.

What Tower of Doom 1 does that this map does not:

- **World forms with two halves.** Archmage is a spinning rune circle + mote
  column + cycling dynamic light on the Mage's body, with a separate
  first-person variant (`_1p`) so the caster is not blinded, a start one-shot,
  a fade one-shot, and on/off sounds. Healing Aura is a ground area that
  FOLLOWS the caster for its whole life, a body effect on every recipient,
  green health bars on everyone's HUD, and a glyph shower on a revive. That
  pattern (world fx + 1p fx + light + HUD tint + edge sounds) is the bar.
- **Buff tells.** Full Steam is a screen wash + a wind loop. Trailblazer leaves
  burning ground behind a sprint with ignite + loop sounds. Blink marks both
  ends of the teleport and pulses the tile amber when blocked.
- **HUD that reacts.** Recharge frames around tiles, a blocked-cast pulse, the
  mana bar breathing when full, rainbow bars on an Archmage. Here the
  `TodAbilityFeedback` frames and pulse only work for the gated-off Mage; the
  live classes' tiles never flash on ready or on cast.

What Hellbound had that was never ported:

- **The kill-feel layer** (`_tod_kill_feel.gsc` there): per-class kill
  signatures (SKEWERED bow headshot = 0.13 s slow motion + head gib + ember
  heat ripple + ragdoll along the arrow; MEAT CANNON close shotgun kill =
  torso burst + annihilate + quake; BUTCHER/CLEAVE melee = dismember by hit
  location, feet ripple on a multi-kill), screen blood within 110 u, custom
  hit shaders and three-layer kill sounds. None of it exists here; this map's
  kill feedback is the recoloured stock hit marker + ragdoll flings.
- **Gold sword viewmodel aura** (`fx_charge_light_1p` + `_ramp_1p` on the
  blade's glyphs, an aura loop sound) and the **1p camera effect on the slam**
  (`fx_smash_1p`). All three .efx are in the tools root, unzoned and unused.
  The only piece that crossed is the shader brightness ramp in
  `_tod_cyber_sword.csc`.

## 2. Per ability: what exists today

Columns: what the CASTER sees / what a TEAMMATE sees on the caster / verdict.
"bare PlayFX" = a server one-shot the map's own notes say does not render
(`_tod_class_kit.gsc:2289`, `_tod_necro_summon.gsc:1514`); unverified in game
either way, and listed in section 4.

### Warrior (`slasher`)

| Ability | Caster (1p) | Teammate (3p) | Verdict |
|---|---|---|---|
| **BASH** (the dash card) | proxy swing clip, whoosh sound; NOTHING during the 400 ms dash; at impact one 3-sprite dust puff (`fx_one_inch_punch_impact`, same for every blade and level), quake, rumble | body slides with blade drawn, the same puff | **WEAK** |
| Bash stun on zombies | `fx_tesla_shock_zmb` 1.2 s on a 2.5 s stun (tell ends early) | same | weak |
| **CYBER SMASH** slam | stock spike ground hit + `_1p` camera fx + `hb/gold_sword/fx_smash` (doubles the same shockwave) + afterglow arcs, 4 sounds, quake | same world fx; lifted zombies get surge/spark/trail fx | **RICH** |
| Cyber Smash leap / air dive | nothing in flight, no landing tell before the slam | nothing | none |
| Cyber Smash ready glow | blade brightness ramp (shader constant), 1p only | world blade always emissive, no change | weak |
| **DEMON SLAYER** activation / expiry | nothing (`_tod_class_cards.gsc:343-374`, dev log only) | nothing | **NONE** |
| ARMS SPECIALIST / CLEAVE / VITALITY | nothing | nothing | none |
| Gauntlet + sword primary hits | no `meleeImpactEffect` on `cc_gauntlet` / `cc_gold_sword` forms (only `cc_punch` has one); extra Cleave targets get the punch puff | ragdoll on kill | weak |
| 2%/s passive heal | nothing | nothing | none |

### Necromancer (`necromancer`)

| Ability | Caster (1p) | Teammate (3p) | Verdict |
|---|---|---|---|
| **SOUL PULSE** | 650 ms staff thrust (tiers 2/3 only; the tier-1 skull has NO cast clip), scream, quake, rumble; one world ring: two faint near-white rotated sprites (`i_tod_necro_pulse.png` is a thin pale circle), 24 smoke puffs + 12 glyphs for 0.8 s; NO light, NO distortion, NO decal, NO caster flash (removed on purpose, it whitened the view: `_tod_necro_skull.csc:219-220`) | same ring; nothing on the caster's body | **WEAK** |
| Soul Pulse victims | per-zombie `fx_necro_soul_rip` (hot sprites + flare + light, 200 ms) + breathe sound; **elites show nothing** | same | adequate (carries the whole cast) |
| SOUL SUCK beam | 1p + 3p beam/side fx, PaP recolour + idle loop, homing wisps with lights, eye shock on targets | 3p beam on `tag_flash` | **RICH** |
| REAPER'S REACH | range math only, beam fx not scaled | | none |
| Summons / bind / arrival | drain eyes, aura, wisps in, deathray lift pose, `fx_necro_summon` arrival with 3 lights, per-type aura, white eyes, black models | same (all world) | **RICH** |
| Hound bites | sound only | | weak |
| SUMMONER MASTER | nothing | | none |
| INVISIBILITY CLOAK | vision set + postfx on own screen, teleport in/out sounds | thrall aura on `j_spine4`; body never see-through; no activation burst | adequate |
| Burned Out (melee) | stock BGB 1p/3p fire + torso fire on victims | same | rich (stock) |

### Archer (`assault`)

| Ability | Caster (1p) | Teammate (3p) | Verdict |
|---|---|---|---|
| GRAPPLE | grapple view weapon raise clip, hook model, 5 sounds, corner-bracket reticle; cable = `tod_archer_cable` beam with zero wobble / no sheen / no end fx; bite spark = **bare PlayFX**; nothing on the body in flight | cable from wrist to hook; nothing else | adequate |
| GRAPPLE landing buff tell | `tod/archer/fx_tod_archer_charge` ring on `tag_origin` + rumble. **The ring's elements are LOOPING and nothing ever KillFX's it** (`_tod_archer.gsc:667`, `_tod_retriever.gsc:343`): check in game whether rings pile up | same | weak, possible bug |
| HELL'S RETRIEVER | charge ring at 1 s / 2 s hold, trail + fire on the axe, spin loop, flourish on first grant; each hit = **bare PlayFX** `fx_tod_archer_impact` (looping elements) + sound; nothing links ricochet targets | axe + trails (world) | adequate/rich |
| RUNE PRISON | full Der Eisendrache set (arrowhead, trail, glow, fire, aoe, end) + 5 sounds; impact / aoe / end are **bare PlayFX**; torso fire is a server `PlayFXOnTag` on actors (`_tod_boss_fx.gsc:8` says that lane does not render) | world fx | rich on paper, needs an in-game check |
| Bow draw | creak + full-release sounds only; plain bow has no full-draw glow | | weak |
| DEADEYE / QUICK DRAW / PIERCING / SPRINT | twin swaps, DoDamage, speed latch. Pierce has no through-hit tracer | | none |

### Breacher (`heavy`)

| Ability | Caster (1p) | Teammate (3p) | Verdict |
|---|---|---|---|
| STICKY C4 blast | `fx_exp_generic_lg` + ground fire + own wav + quake | same | **RICH** |
| C4 plant / stuck / armed | plain stock world model, no blink light, no stick fx | same | none |
| CLUSTER | canister + bomblet glow with lights, sizzle, tiered burst/pop fx, two sounds, quake (top-tier pop has no light) | same | **RICH** |
| **EXPLOSIVE FUSION heal** | nothing (`_tod_class_cards.gsc:528-551`, trickle_heal + dev log) | nothing | **NONE** |
| **EXPLOSIVE FUSION launch** | nothing: a `SetVelocity` (`:610-623`); no launch burst, no air tell, no landing tell | nothing | **NONE** |
| BUCKSHOT / explosive immunity / air steering | nothing | | none |
| RIOT SHIELD | Lv9 model swap; break sound on the silent `PlaySoundAtPosition` lane; return sound = the lounge chime; no break fx | | weak |
| ADRENALINE | heartbeat sound only | | none visually |

### Shared

- Ability tiles: ready = red tile twin, otherwise alpha 0.4. No flash on
  becoming ready, no pulse on cast, no recharge frame (those exist only for
  the Mage in `TodAbilityFeedback.lua`).
- Hit markers: recoloured stock marker, red punch on kills, ding on elites.
  Adequate. No kill signatures.
- Card deal / class draft / Black Market: UI-rich, and taking a class card has
  no effect on the player in the world.

## 3. Dead and unused assets worth knowing before adding anything

- `tod/necro/fx_necro_soul_bomb`: precached, registered, never played;
  byte-identical to `pulse_ring0`.
- `tod/breacher/fx_tod_c4_blast_t1/t2/t3`: zoned, never played
  (`c4_tier_fx` always returns the top blast).
- `hb/gold_sword/fx_smash_1p`, `fx_charge_light_1p`, `fx_charge_light_ramp_1p`
  (tools root, from Hellbound): the viewmodel glyph aura + the slam camera
  effect, unused here.
- `dlc3/stalingrad/fx_raz_mc_shockwave_projectile_impact`: precached by the
  class kit, only the enemy Mangler uses it.
- Tower of Doom 1's generators are reusable as-is: `tools/gen_archmage_fx.py`
  (world form with 1p/3p halves + lights) and `tools/gen_heal_area_fx.py`
  (ground area per radius). Its retired Thunder Smash
  (`_tod_thunder_smash.gsc:343-371`) is a ready pattern for a ground pulse
  (spike ground hit + elec burst + a 6-strike ring + shock on victims +
  quake + clap/storm sounds).

## 4. Render-lane risks found on the way (not the user's ask; check in game)

- Bare server `PlayFX` one-shots: Archer hook bite (`_tod_archer.gsc:733`),
  Retriever hit (`_tod_retriever.gsc:512`), Rune Prison impact / aoe / end
  (`_tod_archer_rune.gsc:183, 235, 239`). The map's own rule is that these do
  not render; `_tod_perk_electric_cherry.gsc:58` says one stock one-shot does.
  Nobody has confirmed either way for these four.
- Rune Prison torso fire = server `PlayFXOnTag` on an actor
  (`_tod_archer_rune.gsc:308`).
- The looping landing ring never killed (section 2, Archer).
- Riot shield break sound on the `PlaySoundAtPosition` lane
  (`_tod_riotshield.gsc:564`), which this map has proven silent for custom
  aliases.

## 5. Proposals (design, not built)

The rule for every one: **a first-person half the caster sees without being
blinded, a third-person half on the body that a teammate reads from across the
hall, a dynamic light where the effect is a light source, a sound at each edge
(start / end), and a HUD tell on the tile.** Effects are GENERATED from stock
donors by a python tool with `--check` (the map's established way:
`make_soul_fx.py`, `gen_fx.py`, Tower of Doom 1's `gen_archmage_fx.py`).

1. **BASH** (the user's first ask). During the dash: a blade-coloured speed
   streak behind the body (3p, on `j_spine4`) and a short viewmodel light
   ramp (1p, the Cyber Sword ready-glow lane already exists); a brief FOV kick.
   At impact: a blade-coloured shockwave sized to `bash_burst_r` (so the Lv9
   wider burst READS wider), a ground scorch decal, a light flash; victims
   ragdoll outward (the melee module already launches on kills) and the stun
   tell lasts the whole stun. 2nd/3rd charge = two/three streak layers.
2. **SOUL PULSE** (the user's second ask). Replace the thin pale ring with a
   soul-blue expanding shock dome + a ground decal + a dynamic light that
   flares and dies with the wave + 24 outgoing souls that are actual soul
   sprites (not smoke); keep the "no caster flash" lesson by putting the 1p
   half as a short blue vignette / postfx instead of sprites at the camera;
   staff tier-1 gets a cast clip or at least a viewmodel light; elites hit get
   a soul-rip style flash scaled up. Band 0..3 scale the dome.
3. **EXPLOSIVE FUSION**: heal = a short orange ember shower on the body +
   green/orange health tint on the bar + a heal sound (one per blast, not per
   tick); launch = a fire-and-smoke rocket burst under the feet at the launch
   frame, an ember trail on the body while `tod_fjump_air`, and a landing
   dust ring + thud, so a teammate sees the Breacher rocket off the floor.
4. **DEMON SLAYER**: activation = a red flash + a looping red aura on the body
   (3p) + a short screen edge tint (1p) + a sting; the aura fades out over the
   last second so the end is readable; tile pulses.
5. **The kill-feel layer** from Hellbound, ported: per-class kill signatures
   (Warrior dismember, Breacher meat cannon, Archer skewer with a solo-only
   slow-mo, Necromancer soul harvest) + screen blood close up + the three-layer
   kill sounds. This is the single biggest "punchiness" lever and it is
   class-wide.
6. **Ability tile feedback** for the live classes: ready flash, cast pulse,
   recharge frame, blocked pulse (the Mage's `TodAbilityFeedback.lua` lanes,
   generalised).
7. Smaller: Cyber Smash dive streak + ready aura on the world blade; Grapple
   cable sheen + launch puff + flight wind; hound bite fx; Cloak activation
   burst; Riot Shield break shards + a real break/return sound; Piercing
   through-hit tracer; a C4 blink light while armed.
