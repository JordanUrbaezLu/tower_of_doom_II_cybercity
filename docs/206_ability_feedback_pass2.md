# 206 — The ability feedback, second pass: every move seen and heard, sounds made for the moves

**Status: BUILT in session -a0's FULL BUILD OK 15:01 (tmp/war_damage/full7.log; geom_key reused build 6's bake): .ff 15:01:16, FF 229,403,200 B, the 8 known-waived linker lines only; inside it ran the new GSC STRICT LINT (135 scripts), ABILITY FX 448, ABILITY SOUNDS OK (21 cues / 23 files / 35 rows), ABILITY FEEDBACK 455 and NATIVE RETRIEVER. VERIFIED here (scratchpad verify_build.py): the 15:01:16 ledger carries scriptparsetree _tod_ability_fx.gsc + .csc and all 9 touched scripts, all 55 fx,tod/abfx rows and 24 weapon rows cc_gauntlet / cc_gold_sword; the deployed tod_weapon_twins.gdt carries the blade hit effects (32 gauntlet / 16 sword lines); the fresh loaded bank (all.sabl 15:00:18, 160.5 MB) indexes all 23 tod_abfx_ stems; every touched file deployed = repo and none of mine edited or synced after the build. Build 6 (14:41) carried the same tree and died at the compiler on a PEER line (_tod_haven.gsc:963, an unwrapped ternary in a call argument that every JS gate accepted), fixed by its owner before build 7**
Follows docs/203 (the first pass). The user judges the feel in a playtest; the dev logs `[TOD_ABFX]` /
`[TOD_ABFX_C]` record every decision (section 8).

User, 2026-10-03: *"Any tweaks or enhancements we can make on upgrade moves special effects or sounds?"*, then
*"implement everything else you find will improve the experience"*, *"you have eleven labs API ... generate new
sounds ... I also have Uppbeat ... tell me what to search"*, *"Do not stop until you are fully complete and don't
leave anything pending."*

## 1. The audit: what was still missing after the first pass

| Ability / moment | What the player got | What was wrong |
|---|---|---|
| CYBER SMASH, the air dive | nothing between the cast and the slam | the fastest, most committed move in the kit was invisible in the air; no mark on the floor it was about to hit |
| CYBER SMASH charged | the caster's blade brightens (a 1p shader ramp) | a teammate could not tell a charged Warrior from a spent one; no moment when it charged |
| INVISIBILITY CLOAK | Blink's stock teleport pair | borrowed cues; no burst on the body when a teammate vanished or came back |
| A CARD TAKEN | the panel only | the party never saw or heard a LEGENDARY land on a teammate |
| RIOT SHIELD break | `PlaySoundAtPosition` of a custom alias | silent (the lane the map proved dead for custom aliases, 2026-09-16) and no visual |
| RIOT SHIELD return | the lounge chime | a shared alias: "your shield is back" and "you reached a lounge" were one sound |
| STICKY C4 planted | the model | nothing said "armed" to anyone standing next to it |
| THE BOW full draw | a release layer at the shot | nothing at the moment the draw became full |
| PIERCING | damage | the pierced zombies showed nothing |
| The hook bite, the Retriever's hit, the Rune Prison's impact / eruption / end | bare server `PlayFX` | drew nothing (docs/203 s4: a bare server one-shot does not render here) |
| The Rune Prison's torso fire | server `PlayFXOnTag` on the zombie | the same lane, on an actor |
| The tier-3 cluster pop | the Fuse burst | the one burst in the kit with no light |
| The Bash impact and the Fusion landing | one borrowed LFE sweep for both | borrowed, shared |
| Every first-pass cue | stock wavs re-used | nothing was made for the move |

## 2. The design: what the player sees and hears

One owner still: `_tod_ability_fx.gsc` / `.csc` (docs/203). Every new moment has a first-person half for the
caster and a body half for the others, and a sound in both ears. THE 1P RULE (twice earned: v18.75 glare, v18.91
puff) governs the new one-shots: a sprite burst at the chest sits inches from the local camera, so the cloak /
card / shield / charged bursts play on the BODY for the others only; the caster has the sound, the HUD, the
vision set or a viewmodel half.

| Moment | The caster | The others | Both ears |
|---|---|---|---|
| CYBER SMASH dive | the falling whistle | a cyan streak behind the body (a state, re-triggered every 0.3 s), a looping cyan ring on the floor the dive traced (dies with the dive) | `tod_abfx_dive` |
| CYBER SMASH charged | the blade brightens (unchanged) + a sting | a soft glow + light on the sword hand while the slam is ready (a state); a flash the moment it charges | `tod_abfx_charged` (caster) |
| CLOAK on / off | In Plain Sight (unchanged) | a soul-mote burst on the body at the vanish and the reappear | `tod_abfx_cloak_on` / `_off` |
| A CARD TAKEN | the panel (unchanged) | a rarity-coloured burst on the body: COMMON white, RARE blue, EPIC purple, LEGENDARY gold + a gold light on the floor | `tod_abfx_card_1..4` (3D at the body, so the party hears which) |
| RIOT SHIELD break | the crack | a shard burst on the body | `tod_abfx_shield_break` |
| RIOT SHIELD return | its own cue | a cold glow pulse on the body | `tod_abfx_shield_back` (caster) |
| STICKY C4 planted | - | a red light blinking once a second on the charge + a soft beep loop, until it goes | `tod_abfx_c4_loop` (3D, 80..700) |
| THE BOW full draw | a green glow on the viewmodel + a tick, once per draw | - | `tod_abfx_draw` (caster) |
| PIERCING | - | a flesh hit at each pierced zombie's chest | `tod_abfx_pierce` (3D at the zombie) |
| Bash impact / Fusion landing | their own impact / landing cues (were one borrowed sweep) | the same bursts as docs/203 | `tod_abfx_impact`, `tod_abfx_land` |
| Hook bite, Retriever hit, Rune impact / eruption / end, torso fire | drawn now (carriers / the actor lane) | drawn now | unchanged sounds |
| Tier-3 cluster pop | the Fuse burst WITH an ember light | same | unchanged |
| Gauntlet / Cyber Sword hit | ember sparks / cold sparks on every hit (the weapon's own `meleeImpactEffect`; the punch keeps its Origins fist puff) | same | unchanged |

Every borrowed stock cue of the first pass (the Fury whoosh, the LFE sweep, the soul steal, the sky jet, the demon
gate, the perk pop, the near-miss heat) is gone from `sound/aliases/tod_ability.csv`.

## 3. Two lanes that replace every bare server one-shot

- **`tod_ability_fx::burst_at( fx, org, angles, life )`**: a `tag_origin` carrier at the point, the effect on its
  tag one frame later, deleted after `life` (the first pass's `ring_run`). The hook's bite (the surface normal),
  the Rune Prison's impact / eruption / end (forward up: angles `( -90, 0, 0 )` for a donor authored along +Z).
- **The actor hit lane**: `tod_abfx_hitk` (the kind, 2 bits) then `tod_abfx_hit` (a counter) on the ACTOR, the
  kind registered BEFORE the counter (docs/203's rule); the client reads the kind after the snapshot settles and
  draws it on the zombie: `pierce_hit` (the flesh hit), `axe_hit` (the archer impact), `burn` (the torso fire for
  `TOD_ABFX_BURN_SECS` = `TOD_RUNE_TRAP_MS`, then `KillFX`). Zero server entities.

RULE: a new one-shot in the world goes through `burst_at`; a new one-shot ON A ZOMBIE goes through `actor_hit`
(a wrapper per kind); a new one-shot on a PLAYER is a kind on `play()`. Never a bare `PlayFX` / `PlayFXOnTag` on an
actor again (the gate fails the rune's and the retriever's old lines, section 7).

## 4. The sounds: made for the moves

`tools/ability_fx/make_sounds.py` (docs/206's tool):

1. **`generate [--cue N] [--takes N]`**: ElevenLabs `/v1/sound-generation` (`tools/black_market_vo/eleven.py`;
   the key from `ELEVENLABS_API_KEY`, never printed) renders takes from a prompt per cue into
   `tmp/ability_sfx/takes/<cue>/`.
2. **The score**: every take is MEASURED (`features`: onset, peak position, decay, tail level, flat-top clipping,
   low / high energy, smoothness) and scored against the cue's PROFILE (impact / burst / whoosh / rising / shatter /
   swell / sting / sweep / fade / tick / synth); the user's own ear said ElevenLabs "doesn't always produce a nice
   sound", so the pick is the best-measured take, and `rescore` re-measures after a profile change.
3. **Shaping**: the dive is `shape="reverse"`: the model puts the loudest moment first whatever the prompt says
   (nine takes, every one impact-first); a time-reversed take IS the rise that stops dead at the floor. Shaping is
   applied before scoring AND rendering, so the pick reflects the shipped sound.
4. **`pick`**: trims, DC-blocks, fades, levels to the cue's LUFS under a soft limiter at -1 dBFS, encodes mono 48
   kHz 16-bit into `sound_assets/tod/abfx/`, writes `tools/ability_fx/sounds_manifest.json` (sha256 per file) and
   REGENERATES `sound/aliases/tod_ability.csv` whole (a 2D `_plr` row, a 3D `_3d` row, a 3D looping row, the shapes
   copied from the first pass's own rows). The C4 beep is synthesised.
5. **The Uppbeat lane** (the user: "upbeat has the highest quality sounds"): a download dropped as
   `tmp/ability_sfx/drop/<cue>.wav` (or `.mp3`) WINS the pick automatically; `picks.json` overrides a take by name.
   `desk` builds `tmp/ability_sfx/desk.html` (every take, the pick, the drops); `brief` prints the search list:

| Cue | ~length | Uppbeat search |
|---|---|---|
| dash | 0.7 s | sword whoosh swing fast; energy blade swipe |
| impact | 0.9 s | shockwave impact bass; heavy slam metal thud |
| pulse | 1.5 s | ghost whoosh ethereal; dark magic burst spectral |
| launch | 0.9 s | rocket launch blast whoosh; jetpack boost |
| land | 0.8 s | heavy landing thud metal; body land impact |
| heal | 0.9 s | healing chime magic; health restore glow |
| demon_on | 1.2 s | demon roar power up; dark energy surge |
| demon_off | 1.0 s | power down dissipate dark; energy fade out |
| dive | 1.1 s | falling whoosh rising; dive wind rush |
| charged | 1.0 s | energy charge complete ping; weapon ready sci-fi |
| cloak_on | 1.0 s | cloak activate shimmer; stealth phase sci-fi |
| cloak_off | 0.9 s | decloak shimmer reverse; teleport in sci-fi |
| shield_break | 1.1 s | shield shatter glass break; armor crack |
| shield_back | 1.1 s | shield recharge power up; energy shield activate |
| card_1 | 0.9 s | ui confirm chime soft; select pickup |
| card_2 | 1.0 s | rare item sting; level up chime short |
| card_3 | 1.1 s | epic reward sting; power up fanfare short |
| card_4 | 1.4 s | legendary reward fanfare; jackpot sting choir |
| pierce | 0.5 s | arrow flesh impact; stab wet crunch short |
| draw | 0.6 s | bow string tension creak; bow draw click |

6. **`--check`** (the build gate, in `build_map.ps1` after `test_ability_fx.js`): every manifest file present with
   its sha, mono 48 kHz 16-bit, 0.1..4 s, the csv byte-equal to the generated table, the table loaded by the szc.
   No API, no DSP.

Shipped picks (2026-10-03): 23 files, 20 cues from ElevenLabs takes (scores 0.86..1.00; the dive 1.00 after the
reversal, the dash three variants), the beep synthesised. A rise is mostly quiet, so the dive lands ~7 LU under
its target at the same peak ceiling: its alias rows carry +8 (92 / 88).

## 5. The effects

`tools/ability_fx/gen_fx.py` renders 55 effects now (24 + 31): from the first pass's stock donors plus the
Archer's charge ring (the dive mark), the perk glow (the blade glow, the C4 blink), the burned-out burst (cloak /
card / shield-back / charged, tinted), the Gravity Spikes hit's light alone (the LEGENDARY light, the cluster pop's
light), the glass shard burst without its xmodel shards (the shield break), the knife flesh hit (the pierce), the
blue spark burst (the two blade hits), the castle jump-pad trail (the dive streak), the sword's charge ramp (the
draw glow). New transforms: `blink_light` (a 120 ms flash each second on a light's intensity graph),
`splice_elements` (extra elements from a second donor), `tint=None` (keep the donor's colours), `glow_only` /
`no_models` / `light_only` keep predicates. Children keep the `<parent>_c<N>` short names (the 63-char rule).

## 6. Knobs per symptom

| Symptom | Knob |
|---|---|
| The dive streak reads thin / thick | `TOD_ABFX_DIVE_STEP` (.csc), `fx_abfx_dive_trail` alpha / size (gen_fx) |
| The landing mark is too bright | `fx_abfx_dive_ring` light / alpha (gen_fx) |
| The blade glow is loud on a teammate | `fx_abfx_sword_glow` size / light (gen_fx) |
| The charged sting fires on every respawn | `TOD_ABFX_SWORD_QUIET_MS` (2000; the state is re-sent on spawn) |
| A card burst is too big / small | `fx_abfx_card_N` size (gen_fx); the gold light `fx_abfx_card_light` light |
| The C4 beep is annoying / inaudible | `c4_loop` vol / dist in `make_sounds.py` CUES; the blink `fx_abfx_c4_blink` light |
| A cue is too loud / quiet | the cue's `lufs` or `vol` in CUES, then `pick` |
| A cue sounds wrong | drop an Uppbeat file (`tmp/ability_sfx/drop/<cue>.wav`) or `generate --cue <cue> --takes 3`, then `pick` |
| The torso fire outlives the prison | `TOD_ABFX_BURN_SECS` (LOCKSTEP `TOD_RUNE_TRAP_MS`, gated) |
| A carrier lingers | `TOD_ABFX_BURST_LIFE`, the per-call `life`; the C4 carrier dies with its charge or after 180 s |

## 7. The gates

- `tools/test_ability_fx.js` (in build_map): A the 55 effects rendered fresh / zoned / no stub / under 63 chars,
  every effect key bound to a precached effect; B the lockstep (20 kinds + 4 state bits, the hit kinds, the bits,
  `TOD_ABFX_BURN_SECS` = `TOD_RUNE_TRAP_MS`, six clientfields in the same order, the hit kind registered before the
  hit counter, the 1p rule on every new body one-shot, every looping effect's `KillFX`); C the wiring (every hook
  above, the alias rows incl. the 3D rows and the C4 looping row, no borrowed stock cue in the table, the carriers'
  deaths, no namespaced call inside the three dive functions `tools/warrior/test_gs_dive.js` transpiles, the
  blades' `meleeImpactEffect` in the twins GDT: 4 gauntlet + 2 sword forms, the punch untouched); E negative
  controls (a bare rune one-shot, the silent shield lane, a borrowed cue, a missing hit-kind registration).
- `tools/ability_fx/make_sounds.py --check` (NEW in build_map, section 4.6).
- `tools/ability_fx/gen_fx.py --check` (inside A).

## 8. Diagnostics (dev)

`[TOD_ABFX]`: `INIT rev=2 kinds=24 states=15 hits=3`; `DIVE player= floor=`; `SWORD player= charged=1 quiet=`;
`CARD player= rarity=`; `SHIELD player= break|back`; `C4_ARMED grenade=`; `BURST fx= at= life=` and `HIT kind=
zombie=` for the first 20; `FX_DROPPED` (the entity pool refused a carrier); the first pass's PLAY / STATE / DEFER.
`[TOD_ABFX_C]` (`TOD_ABFX_C_LOG` 1, zero before a publish): `EVENT kind=`, `STATE ... dive= sword=`, `HIT kind= ent=`.

What to read in the user's log: a `DIVE` with `floor=none` means the dive started with no traced floor (no mark,
streak only); `SWORD ... quiet=1` on spawn is expected (no sting); `FX_DROPPED` means the server entity pool is
full at that moment (the sky fleet is client-only, so this should not happen).

## 9. Not verified

Native behaviour has not been seen: the look of every new effect in game (the 1p rule is by construction, not by
eye), the sound levels against the music and the first pass's cues, the `tag_weapon_right` glow's position on the
body, the `tag_flash` viewmodel glow on the bows, the blink light's visibility on a stuck charge, the hit lane's
timing on a zombie that dies of the hit, and above all the feel. The gates prove the decisions, not the experience.

## 10. Playtest follow-ups

- **2026-10-03 16:01, the C4 tell.** FOLLOW-UP 2026-10-03 16:01 (the user's 15:34-15:45 run on the Breacher: 4 C4 plants, 0 C4_ARMED lines): the armed tell was called only after `c4_stick_watch`'s 3 s stick window and every charge was set off 0.1-0.35 s after the throw, so it never played. It now arms the moment the charge is still across two samples (0.1 s; a throw's apex never holds still that long); the stuck / window-end call is the fallback and skips a charge already armed. Log `[TOD_KIT] C4_TELL at=rest|stuck|window_end after_ms=`. test_ability_fx 451 (+ arm-at-rest, arm-once, a negative control); 87 build_map gate lines green on the landed repo (`tools/run_build_gates.py`, new; that first version skipped ~25 captured-output lines - -a4 fixed it at 17:25 - and -f8's FULL build ran the whole list on this fix). The rest of that run read clean for this pass: 58 server events = 58 client events, the AIR state on/off 22 / 22, one RARE card, no FX_DROPPED, no script error of ours (its 3 script errors are the lucky meteor trail's `not precached`, in every run since 2026-09-30). BUILD: BUILT in session -f8's FULL BUILD OK 16:13 (tmp/jumppad_fix/full2.log; geom_key reused the 15:32 bake): .ff 16:11:50, FF 229,424,640 B; ABILITY FX 451, ABILITY SOUNDS, C4 CONSISTENCY and the GSC strict lint ran inside it; verified here: the deployed _tod_class_kit.gsc = repo with the rest arm, every ledger row of the pass, 23 / 23 stems in the 16:11:05 loaded bank, nothing synced after. UNPLAYED.
