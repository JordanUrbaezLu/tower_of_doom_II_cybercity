"""THE WUNDERSTRAHL'S SOUNDS (docs/219, 2026-10-05): every cue the laser wonder weapon plays, one owner.

The user: "a really super strong laser gun ... like an automatic laser. So you can hold it down ... kind of like a
aura beam almost". The Wunderstrahl is the DG-2's laser sibling, so every cue is built from THREE sources on one
deterministic pipeline, and each one is audibly a descendant of the Wunderwaffe:

  * THE DG-2 ITSELF (read-only, tmp/wunderstrahl/src/T7 Assets V2.8/sound_assets, each file's sha256 pinned in the
    manifest): its idle hum (a 32.5 Hz electrical series: 65 / 97.6 / 195 Hz), the projectile flux fizz, the two
    tesla bounce zaps, the projectile impact and the projectile crackle loop.
  * ELEVENLABS sound generation (eleven_text_to_sound_v2, lossless pcm_48000) for the organic layers no oscillator
    makes well: the ignition crack, the crackle and burn-through beds, the flesh sizzle, the disintegration, the bulbs,
    the switch, the dying sputter, the sparkle. Every take is cached under tmp/wunderstrahl/sound_raw/ (a re-run
    makes NO new API call), measured and scored against its layer's profile; the best ships, picks.json overrules.
    The model puts the loudest moment first, so the one RISING layer (the charge) asks for a discharge and is reversed.
  * SYNTHESIS where a machine beats a model: THE BEAM. A 65 Hz pure-sine fundamental (the DG-2 hum's own 65.1 Hz
    partial, so the laser sings in the DG-2's key, C) under a 130 Hz harmonic stack - an octave up so its pitch pulse
    sits above the band where a drone reads as rough buzz (a 30 s hold must not tire the ear) - Schroeder-phased for a
    low crest, with a travelling spectral emphasis and a circling stereo pan (the gold orbs swirling round the core) and
    slow chorus beating. Every partial and every modulation completes a whole number of cycles in the loop, so the
    loops are seamless BY CONSTRUCTION; the sampled beds are cross-faded round the seam and the whole bus (filters,
    saturation, limiter) is circular.

THE MIX (measured, never guessed): every alias row copies the alias VOLUME of its stock analogue (the Gauntlet of
Siegfried - stock BO3's own held beam weapon - for the fire set and the wall-hit loop; the DG-2's own idle; the map's
own raise / ability / luck rows for the rest), and every wav is levelled against that analogue's wav at the SAME alias
volume, so the comparison holds whatever the engine's volume curve is. The targets (REFS / CUES below) carry the
reference's measured value and the offset chosen; tools/wunderstrahl/sound/manifest.json records what each file
reached. One-shots are levelled by their loudest 300 ms K-weighted window, loops by BS.1770 integrated loudness. A
look-ahead brickwall (circular on the loops) holds every sample peak at or under -1 dBFS.

FORMAT: mono 48 kHz 16-bit, EXCEPT the three 2D player fire cues (start / loop / stop), which are STEREO - the stock
convention for a 2D weapon loop (the Gauntlet's and the Necromancer's skull-gun player loops are stereo wavs; their
3D npc twins are mono) and the lane the swirl's circling pan rides on. Their low partials are identical in both
channels, so the mono fold-down keeps the beam's body.

THE TABLE sound/aliases/tod_wunderstrahl.csv is GENERATED whole (the stock Gauntlet rows' shape, sound context
cleared, nothing Pauseable). Every LOOPING row is preceded by a "# OWNER" comment row naming what starts and stops it:
a 2D loop with no owner is a loop nobody can stop. Never hand-edit it; re-run build.

  python tools/wunderstrahl/sound/make_sounds.py build   [--out-root DIR] [--offline]   API (missing takes only) + render
  python tools/wunderstrahl/sound/make_sounds.py --check [--out-root DIR]               the gate: no API, no DSP
  python tools/wunderstrahl/sound/make_sounds.py --selftest [--out-root DIR]            planted faults must be caught
  python tools/wunderstrahl/sound/make_sounds.py verify  [--out-root DIR]               re-render offline, byte-compare
  python tools/wunderstrahl/sound/make_sounds.py review  [--out-root DIR]               art/wunderstrahl/sound_review/
  python tools/wunderstrahl/sound/make_sounds.py stt     [--out-root DIR]               speech-to-text over the shipped
                                                                                        wavs (API; no hidden words)

DIR (default the repo) is any tree laid out like the repo; this pass stages into tmp/wunderstrahl/stage. The key is
ELEVENLABS_API_KEY, read only by tools/black_market_vo/eleven.py (never printed, never written anywhere).

WIRING (the lander's, not this tool's):
  * sound/zoneconfig/zm_tod2_cybercity.szc loads the table once: SZC_ENTRY below (--check fails without it in the repo).
  * the weapon file (gasweapon.gdf) wires the fire trio the way stock BO3's own gas beam weapon does (hero_flamethrower in
    the T7 dump): startFireSound / startFireSoundPlayer = tod_ws_fire_start_npc / _plr, loopFireSound / loopFireSoundPlayer
    = tod_ws_fire_loop_npc / _plr, loopFireEndSound / loopFireEndSoundPlayer = tod_ws_fire_stop_npc / _plr. Use the
    native start field OR a frame-0 "2D Sound" note on the fire clip, never both (the ignition would double).
  * the beam asset's blockedEffectSound = tod_ws_impact_loop; raise / putaway ride "2D Sound" notes on the raise /
    putaway clips (baked notetrack names are silent); tod_ws_hit / _kill / _grab / _expire / _idle_loop are script
    plays - on an entity or a script_origin carrier, never PlaySoundAtPosition (custom aliases are silent there).
"""
import argparse, csv, hashlib, io, json, os, shutil, subprocess, sys, tempfile, wave

sys.dont_write_bytecode = True
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
MANIFEST = os.path.join(HERE, 'manifest.json')
RAW = os.path.join(REPO, 'tmp', 'wunderstrahl', 'sound_raw')
TAKES_JSON = os.path.join(RAW, 'takes.json')
PICKS_JSON = os.path.join(RAW, 'picks.json')
REF_CACHE = os.path.join(REPO, 'tmp', 'wunderstrahl', 'sound_ref')
DG2_ROOT = os.path.join(REPO, 'tmp', 'wunderstrahl', 'src', 'T7 Assets V2.8', 'sound_assets')
REVIEW = os.path.join(REPO, 'art', 'wunderstrahl', 'sound_review')
T7_ARCHIVE = os.path.join(os.path.expanduser('~'), 'Downloads', 'T7 Assets V2.8.rar')
T7_PREFIX = 'T7 Assets V2.8'
SEVEN_ZIP = r'C:\Program Files\7-Zip\7z.exe'
WAV_DIR = 'sound_assets/tod/wunderstrahl'
FILESPEC_DIR = 'tod\\wunderstrahl\\'
CSV_REL = 'sound/aliases/tod_wunderstrahl.csv'
SZC_REL = 'sound/zoneconfig/zm_tod2_cybercity.szc'
SZC_ENTRY = {'Type': 'ALIAS', 'Name': 'tod_wunderstrahl', 'Filename': 'tod_wunderstrahl.csv', 'Specs': []}
SR = 48000
CEIL_DB = -1.0
TP_MAX_DB = -0.5                 # the 4x-oversampled true peak a cue may reach before its ceiling is lowered
MODEL = 'eleven_text_to_sound_v2'
PROMPT_INFLUENCE = 0.6
FIX = 'run: python tools/wunderstrahl/sound/make_sounds.py build --out-root <the tree>'
F0 = 65.0                        # THE BEAM'S FUNDAMENTAL: the DG-2 idle hum's 65.1 Hz partial (C2); the laser is in C

# ---- THE DG-2 (read-only originals) ------------------------------------------------------------------------------------
DG2 = {
    'idle': 'wpn/energy/dg2/idle/tesla_idle_00.wav',
    'flux': 'wpn/energy/dg2/projectile/flux/wpn_tesla_flux_l.wav',
    'bounce0': 'wpn/energy/dg2/effects/bounce/bounce_00.wav',
    'bounce1': 'wpn/energy/dg2/effects/bounce/bounce_01.wav',
    'impact': 'wpn/energy/dg2/projectile/impact/proj_impact.wav',
    'impact_zb': 'zmb/zmb_blops/wpn/energy/dg2/projectile/impact/proj_impact.wav',
    'projloop': 'zmb/zmb_blops/wpn/energy/dg2/projectile/loop/proj_loop.wav',
}

# ---- THE REFERENCES: measured 2026-10-05 (BS.1770 integrated "lufs"; loudest 300 ms K-weighted window "k300"; a stereo
# file's figures sum both channels, "k300_mono" / "lufs_mono" fold it down). "t7:" = the stock BO3 dump (extracted
# read-only into tmp/wunderstrahl/sound_ref), "repo:" = this map's shipped wav. vol = the alias volume its row plays at.
REFS = {
    'gauntlet_start_plr': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_start.wav', vol=80, ch=2, lufs=-8.55, k300=-8.00,
                               what="the Gauntlet of Siegfried's ignition (stock BO3's held beam weapon), 2D"),
    'gauntlet_loop_plr': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_loop.wav', vol=72, ch=2, lufs=-8.05, k300=-7.63,
                              what="the Gauntlet's held flame loop, 2D"),
    'gauntlet_stop_plr': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_stop.wav', vol=70, ch=2, lufs=-15.82, k300=-14.57,
                              what="the Gauntlet's release (0.15 s), 2D"),
    'gauntlet_start_npc': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_start_mn.wav', vol=80, ch=1, lufs=-11.64, k300=-11.12,
                               what="the Gauntlet's ignition for others, 3D"),
    'gauntlet_loop_npc': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_loop_mn.wav', vol=72, ch=1, lufs=-11.24, k300=-10.70,
                              what="the Gauntlet's flame loop for others, 3D"),
    'gauntlet_stop_npc': dict(src='t7:zmb/level/zm_stalingrad/dragon/gauntlet/fire/wpn_dragon_gauntlet_stop_mn.wav', vol=70, ch=1, lufs=-19.08, k300=-17.83,
                              what="the Gauntlet's release for others, 3D"),
    'gauntlet_hit_loop': dict(src='t7:wpn/hero/flame_thrower/hit/wpn_flamethrower_hit_loop_00.wav', vol=95, ch=2, lufs=-13.63, lufs_mono=-16.94, k300=-11.83,
                              what="the Gauntlet's flame-on-a-surface loop (its beam's blocked sound), 3D"),
    'skull_loop_plr': dict(src='t7:zmb/level/zm_island/skull/gun/zmb_skullgun_loop_plr.wav', vol=77, ch=2, lufs=-9.67, k300=-8.63,
                           what="the Necromancer's skull gun held loop (this map's other held beam), 2D"),
    'skull_stop_plr': dict(src='t7:zmb/level/zm_island/skull/gun/zmb_skullgun_stop_plr.wav', vol=80, ch=2, lufs=-12.39, k300=-8.79,
                           what="the Necromancer's skull gun release, 2D"),
    'tesla_idle': dict(src='t7:wpn/energy/dg2/idle/tesla_idle_00.wav', vol=30, ch=1, lufs=-14.97, k300=-14.51,
                       what="the DG-2's own held-gun hum (stock wpn_tesla_idle, vol 30), 3D"),
    'abfx_pierce': dict(src='repo:sound_assets/tod/abfx/tod_abfx_pierce.wav', vol=80, ch=1, lufs=-16.42, k300=-15.18,
                        what="the Archer's arrow-through-flesh tick (tod_abfx_pierce_3d), 3D"),
    'abfx_impact': dict(src='repo:sound_assets/tod/abfx/tod_abfx_impact.wav', vol=84, ch=1, lufs=-14.77, k300=-10.73,
                        what="the Warrior's shockwave slam (tod_abfx_impact_3d), 3D"),
    'archer_bow_raise': dict(src='repo:sound_assets/tod/archer/bow_raise.wav', vol=70, ch=2, lufs=-15.43, k300=-11.92, k300_mono=-15.34,
                             what="the Archer's bow raise (tod_archer_bow_raise_plr), 2D"),
    'archer_bow_lower': dict(src='repo:sound_assets/tod/archer/bow_lower.wav', vol=68, ch=2, lufs=-19.27, k300=-18.07, k300_mono=-21.44,
                             what="the Archer's bow lower (tod_archer_bow_lower_plr), 2D"),
    'golden_jackpot': dict(src='repo:sound_assets/tod/luck/tod_luck_golden_jackpot.wav', vol=86, ch=1, lufs=-15.06, k300=-11.05,
                           what="the golden zombie's jackpot sting (tod_luck_golden_jackpot), 2D"),
    'abfx_demon_off': dict(src='repo:sound_assets/tod/abfx/tod_abfx_demon_off.wav', vol=82, ch=1, lufs=-18.00, k300=-13.89,
                           what="Demon Slayer running out (tod_abfx_demon_off_plr: a power ending), 2D"),
    'powerup_grab': dict(src='t7:zmb/_zhd/powerups/grab/evt_powerup_grab_00.wav', vol=83, ch=2, lufs=-9.31, k300=-6.77,
                         what="stock zmb_powerup_grabbed (plays WITH the grab sting), 3D"),
}

# ---- THE RAW LAYERS (ElevenLabs): what each is asked for, how many takes, the profile a take is scored against --------
LAYERS = {
    'crackle_loop': dict(secs=5.0, loop=True, takes=3, profile='bed', prompts=[
        'continuous crackling and fizzing of a powerful electric energy beam, dense tiny sparks sizzling and snapping, '
        'steady and seamless, close, no hum, no music, no voice',
        'a steady stream of high voltage electrical crackle, fizzing static sparks and popping arcs, constant intensity, '
        'seamless loop, no music, no voice']),
    'burn_loop': dict(secs=5.0, loop=True, takes=3, profile='bed', prompts=[
        'a laser beam burning into a metal wall: continuous intense sizzling, molten metal spitting and crackling, '
        'steady, seamless loop, no music, no voice',
        'hot plasma cutting through steel, a constant searing hiss with popping sparks and bubbling molten metal, '
        'steady, seamless, no music, no voice']),
    'ignite_crack': dict(secs=1.0, takes=4, profile='crack', prompts=[
        'one single sharp crisp electric ignition crack, a powerful energy weapon igniting with a bright snap and a '
        'short sizzling fizz tail, close, dry, no music, no voice',
        'a high voltage arc striking once: a loud clean electric crack with a quick buzzing tail, sci-fi weapon '
        'ignition, close, dry, no music, no voice']),
    'charge_zap': dict(secs=1.2, takes=3, profile='rise', reverse=True, prompts=[
        'a high voltage energy weapon discharging: one bright electric zap that falls in pitch and fades away to '
        'complete silence, sci-fi, dry, no music, no voice',
        'a capacitor releasing its charge: a sharp electric burst sliding down in pitch and dying out to silence, '
        'no music, no voice']),
    'powerdown': dict(secs=1.2, takes=3, profile='fall', prompts=[
        'a sci-fi energy weapon powering down: a falling electronic whine with a soft steam hiss, fading to silence, '
        'close, no music, no voice',
        'an electric generator winding down quickly: a descending whine and a gentle hissing release, ends in '
        'silence, no music, no voice']),
    'flesh_sizzle': dict(secs=0.6, takes=4, profile='tick', prompts=[
        'a very short sizzle of a hot laser touching flesh, one quick searing hiss tick, close, dry, no music, no voice',
        'a brief electric sear on a body, a tiny crackling hiss burst, short, dry, no music, no voice']),
    'disintegrate': dict(secs=1.0, takes=4, profile='burst', prompts=[
        'a zombie disintegrating into glowing ash: a bright electric zap pop, crackling embers and a soft whoosh of '
        'ash blowing away, short, no music, no voice',
        'a body vaporized by an energy beam: a crisp electric pop, burning embers crackling and a quick dusty whoosh '
        'fading out, short, no music, no voice']),
    'bulbs_on': dict(secs=1.0, takes=3, profile='clicks', prompts=[
        'old vacuum tube lamps switching on: two quick small electrical relay clicks and a soft rising electric buzz, '
        'close, dry, no music, no voice',
        'a retro sci-fi gadget powering up: a couple of crisp mechanical clicks and a little electric hum swelling in, '
        'close, no music, no voice']),
    'switch_off': dict(secs=0.7, takes=3, profile='click', prompts=[
        'a heavy electrical switch clicked off with a short electric whine dropping away, close, dry, no music, no voice',
        'a powered device shutting off: one solid click and a quick falling electronic blip, close, dry, no music']),
    'dying_sputter': dict(secs=1.4, takes=3, profile='sputter', prompts=[
        'a powerful electric device dying: sputtering crackles and a fading electrical whine as the power runs out, '
        'stuttering, ends in silence, no music, no voice',
        'an overloaded energy weapon failing: flickering electric stutters and a sagging hum that dies out, no music, '
        'no voice']),
    'sparkle': dict(secs=1.2, takes=3, profile='shimmer', prompts=[
        'a soft glittering magical shimmer sparkle, bright and airy, rising, brief, no music, no voice',
        'a twinkling golden sparkle, delicate high chimes and fairy dust shimmer, short, no music, no voice']),
}
LAYER_ORDER = list(LAYERS)

# ---- THE ROW SHAPES (the stock rows, every set field verbatim except: sound context cleared, Pauseable no) ------------
# the Gauntlet of Siegfried's _plr fire rows (stock t7_hero_weapon_sounds.csv, wpn_drag_flame_thrower_*_plr)
SHAPE_PLR_FIRE = dict(Storage='loaded', Bus='BUS_FX', VolumeGroup='grp_weapon', DuckGroup='snp_wpn_1p_shot', ReverbSend='65',
                      CenterSend='0', DistMin='0', DistMaxDry='10000', DistMaxWet='10000', DryMinCurve='allon', DryMaxCurve='default',
                      WetMinCurve='allon', WetMaxCurve='default', LimitCount='8', LimitType='priority', EntityLimitCount='1',
                      EntityLimitType='oldest', PitchMin='0', PitchMax='0', PriorityMin='90', PriorityMax='90',
                      PriorityThresholdMin='0.25', PriorityThresholdMax='1', AmplitudePriority='no', PanType='2d',
                      Pan='front_mostly', Probability='1', StartDelay='0', EnvelopMin='0', EnvelopMax='0', EnvelopPercent='0',
                      OcclusionLevel='0.25', IsBig='no', DistanceLpf='yes', FluxTime='0', Doppler='no', Timescale='yes',
                      IsMusic='no', IsCinematic='no', Pauseable='no', StopOnEntDeath='no', VoiceLimit='no', IgnoreMaxDist='no',
                      NeverPlayTwice='no', ContinuousPan='yes', DistanceLpfMin='800', DistanceLpfMax='3000',
                      RestartContextLoops='no', SilentInCPZ='no', ContextFailsafe='no', GPAD='no', GPADOnly='no', MuteVoice='no',
                      MuteMusic='no')
# the Gauntlet's _npc fire rows (wpn_drag_flame_thrower_*_npc): 3D, grp_weapon_3p, 1000 / 6000
SHAPE_NPC_FIRE = dict(SHAPE_PLR_FIRE, VolumeGroup='grp_weapon_3p', DuckGroup='snp_wpn_3p', ReverbSend='60', DistMin='1000',
                      DistMaxDry='6000', DistMaxWet='6000', DryMinCurve='defaultmin', WetMinCurve='alloff', WetMaxCurve='rcurve3',
                      PriorityMin='40', PriorityMax='90', PriorityThresholdMax='0.8', PanType='3d', Pan='default',
                      EnvelopMin='1500', EnvelopMax='12000', OcclusionLevel='0.5', DistanceLpfMin='1500', DistanceLpfMax='6000')
# the Gauntlet's flame-on-a-surface loop (wpn_drag_flame_thrower_hit_loop), reach widened for a 2400-unit beam
SHAPE_HIT_LOOP = dict(SHAPE_NPC_FIRE, DistMin='300', DistMaxDry='1800', DistMaxWet='2000', StopOnEntDeath='yes')
# the DG-2 projectile's own impact row (stock wpn_mgun_dual_impact: BUS_FX, grp_weapon_3p, reverb 65), reach per cue
SHAPE_IMPACT_3D = dict(SHAPE_NPC_FIRE, ReverbSend='65', LimitType='oldest', EntityLimitCount='1', RandomizeType='variant')
# the weapon foley 2D row (stock zmb_wpn_skullgun_raise_plr / hb_thermite_throw: grp_foley, snp_foley, priority 70)
SHAPE_FOLEY_2D = dict(SHAPE_PLR_FIRE, VolumeGroup='grp_foley', DuckGroup='snp_foley', ReverbSend='61', PriorityMin='70', PriorityMax='70')
# the player's own power cue 2D row (tools/ability_fx PLR_ROW: BUS_HDRFX, grp_hdrfx, centre send 92, wpn_all), pitch fixed
SHAPE_STING_2D = dict(SHAPE_PLR_FIRE, Bus='BUS_HDRFX', VolumeGroup='grp_hdrfx', DuckGroup='snp_hdrfx', ReverbSend='10', CenterSend='92',
                      PriorityMin='40', PriorityMax='90', Pan='wpn_all')
# the DG-2's own idle row (stock wpn_tesla_idle: vol 30, grp_set_piece, 3D, 50..300), one hum per gun, not one per world
SHAPE_IDLE = dict(SHAPE_NPC_FIRE, VolumeGroup='grp_set_piece', DuckGroup='snp_scripted_moment', ReverbSend='30', DistMin='50',
                  DistMaxDry='400', DistMaxWet='400', LimitCount='4', LimitType='oldest', StopOnEntDeath='yes', OcclusionLevel='0.25',
                  EnvelopMin='0', EnvelopMax='0')

# ---- THE CUES ------------------------------------------------------------------------------------------------------------
# alias -> what it is, its file stem(s), channels, the shipped length window, the loudness target, the row.
#   target = (metric, value, reference key, why); metric 'lufs' = integrated (loops), 'k300' = loudest 300 ms window.
#   loop = the exact loop length in seconds (every synthesized partial lands on its 1/L grid).
#   owner = what starts / stops a LOOPING row (written as the "# OWNER" comment row above it).
CUES = {
    'tod_ws_fire_start_plr': dict(stem='tod_ws_fire_start_plr', variants=1, ch=2, keep=(0.50, 0.75),
        target=('k300', -8.0, 'gauntlet_start_plr', "the Gauntlet ignition's 300 ms level at the same alias volume; ours is a sharper "
                'crack (a transient reads stronger than the flame whoomp at equal K300), so it is not squashed to match its density'),
        row=dict(SHAPE_PLR_FIRE, VolMin='80', VolMax='80', Looping='nonlooping', FadeIn='0', FadeOut='100', StopAlias='tod_ws_fire_stop_plr'),
        what='ignition: a trigger thunk, a 0.15 s rising charge (the beam\'s own harmonics gliding up + a reversed DG-2-flux / '
             'ElevenLabs discharge) into a crisp crack (ElevenLabs crack + the DG-2 impact zap + a sub thump), then the fizz settling'),
    'tod_ws_fire_start_npc': dict(stem='tod_ws_fire_start_npc', variants=1, ch=1, keep=(0.50, 0.75),
        target=('k300', -11.1, 'gauntlet_start_npc', "the Gauntlet npc ignition's 300 ms level at the same alias volume"),
        row=dict(SHAPE_NPC_FIRE, VolMin='80', VolMax='80', Looping='nonlooping', FadeIn='0', FadeOut='100'),
        what='the same ignition folded to mono for everyone else'),
    'tod_ws_fire_loop_plr': dict(stem='tod_ws_fire_loop_plr', variants=1, ch=2, keep=(3.99, 4.01), loop=4.0,
        target=('lufs', -8.8, 'gauntlet_loop_plr', '0.75 dB under the Gauntlet flame loop at the same alias volume (it may run 30 s); '
                '~0.3 dB over the Necromancer skull-gun loop once both alias volumes apply'),
        row=dict(SHAPE_PLR_FIRE, VolMin='72', VolMax='72', Looping='looping', FadeIn='150', FadeOut='100'),
        owner='the tod2_wunderstrahl weapon file (its native player loop-fire sound field): the engine starts it when the beam fires '
              'and stops it on release - never played by script',
        what='the held beam: the 130 Hz harmonic stack over a pure 65 Hz fundamental, with a travelling emphasis + circling stereo '
             'pan (the orbs) + chorus beating; '
             'the DG-2 idle hum under it; a crackle bed (ElevenLabs crackle + the DG-2 projectile loop + the DG-2 flux fizz)'),
    'tod_ws_fire_loop_npc': dict(stem='tod_ws_fire_loop_npc', variants=1, ch=1, keep=(3.99, 4.01), loop=4.0,
        target=('lufs', -12.0, 'gauntlet_loop_npc', '0.75 dB under the Gauntlet npc flame loop at the same alias volume'),
        row=dict(SHAPE_NPC_FIRE, VolMin='72', VolMax='72', Looping='looping', FadeIn='150', FadeOut='100', StopOnEntDeath='yes'),
        owner='the tod2_wunderstrahl weapon file (its native loop-fire sound field): the engine starts / stops it with the beam; '
              'StopOnEntDeath is the failsafe',
        what='the held beam in mono for others: less sub, more 1-3 kHz presence and crackle so it carries at distance'),
    'tod_ws_fire_stop_plr': dict(stem='tod_ws_fire_stop_plr', variants=1, ch=2, keep=(0.60, 0.85),
        target=('k300', -11.5, 'gauntlet_stop_plr', "its loudest 300 ms ~3.5 dB under the held loop's (heard), so the beam ends "
                'DOWN, never with a bump; 3 dB over the Gauntlet release blip at the same volume, 3.9 dB under the skull-gun release (heard)'),
        row=dict(SHAPE_PLR_FIRE, VolMin='70', VolMax='70', Looping='nonlooping', FadeIn='0', FadeOut='60', StopAlias='tod_ws_fire_start_plr'),
        what='release: the beam cut (a snap and a few crackle pops), the beam stack falling 1.0 -> 0.28 with the swirl winding '
             'down and a thin coil whine falling with it, and a soft hiss (ElevenLabs power-down + filtered air)'),
    'tod_ws_fire_stop_npc': dict(stem='tod_ws_fire_stop_npc', variants=1, ch=1, keep=(0.60, 0.85),
        target=('k300', -14.7, 'gauntlet_stop_npc', 'the player release 3.2 dB down, the Gauntlet plr -> npc step'),
        row=dict(SHAPE_NPC_FIRE, VolMin='70', VolMax='70', Looping='nonlooping', FadeIn='0', FadeOut='60'),
        what='the release folded to mono for everyone else'),
    'tod_ws_impact_loop': dict(stem='tod_ws_impact_loop', variants=1, ch=1, keep=(2.99, 3.01), loop=3.0,
        target=('lufs', -16.5, 'gauntlet_hit_loop', '0.4 dB over the Gauntlet surface loop (folded to mono) at the same alias volume; '
                '~5 dB under the held beam when the wall is close'),
        row=dict(SHAPE_HIT_LOOP, VolMin='95', VolMax='95', Looping='looping', FadeIn='120', FadeOut='150'),
        owner="the beam asset's blockedEffectSound: the engine plays it where the beam meets a wall and stops it when the beam is "
              'released or unblocked; StopOnEntDeath is the failsafe',
        what='burn-through: an ElevenLabs burn bed + the DG-2 projectile crackle + a thread of the beam tone + seeded molten spits'),
    'tod_ws_hit': dict(stem='tod_ws_hit', variants=3, ch=1, keep=(0.14, 0.40),
        target=('k300', -16.5, 'abfx_pierce', '1.3 dB under the Archer pierce tick at its alias volume (heard: between it and the '
                'crossbow flesh hit) - many of these overlap'),
        row=dict(SHAPE_IMPACT_3D, VolMin='80', VolMax='80', DistMin='100', DistMaxDry='1600', DistMaxWet='1800', LimitCount='6',
                 PitchMin='-80', PitchMax='80', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='a sizzle tick: an ElevenLabs sear + a sliver of a DG-2 bounce zap + a tonal tick on the beam\'s harmonics'),
    'tod_ws_kill': dict(stem='tod_ws_kill', variants=3, ch=1, keep=(0.40, 0.75),
        target=('k300', -12.5, 'abfx_impact', '1.8 dB under the Warrior slam at its alias volume - satisfying, never a wall in a crowd'),
        row=dict(SHAPE_IMPACT_3D, VolMin='84', VolMax='84', DistMin='150', DistMaxDry='2400', DistMaxWet='2600', LimitCount='4',
                 PitchMin='-60', PitchMax='60', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='disintegration: a bright zap-pop (the DG-2 impact + a synth chirp), ember crackle and an ash whoosh (ElevenLabs + '
             'filtered air), a DG-2 bounce sliver'),
    'tod_ws_raise': dict(stem='tod_ws_raise', variants=1, ch=1, keep=(0.70, 0.95),
        target=('k300', -12.5, 'archer_bow_raise', '2.8 dB over the Archer bow raise folded to mono at the same alias volume'),
        row=dict(SHAPE_FOLEY_2D, VolMin='70', VolMax='70', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='powering up: a thin C6 charge whine rising two octaves with the swirl spinning up, the bulbs clicking on (ElevenLabs), '
             'the beam stack arming at full pitch at the end, the DG-2 idle swelling in'),
    'tod_ws_putaway': dict(stem='tod_ws_putaway', variants=1, ch=1, keep=(0.40, 0.60),
        target=('k300', -16.0, 'archer_bow_lower', '5.4 dB over the Archer bow lower folded to mono at the same alias volume (a switch '
                'reads; a bow lowered is a whisper)'),
        row=dict(SHAPE_FOLEY_2D, VolMin='68', VolMax='68', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='a short power-down click: an ElevenLabs switch, the coil whine dropping out (C6 falling), the DG-2 idle cut'),
    'tod_ws_grab': dict(stem='tod_ws_grab', variants=1, ch=1, keep=(1.10, 1.40),
        target=('k300', -10.5, 'golden_jackpot', '0.55 dB over the golden jackpot sting at the same alias volume; under the stock '
                'grab it plays beside'),
        row=dict(SHAPE_STING_2D, VolMin='86', VolMax='86', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='the pickup sting: a warm golden C-major swell voiced on the beam\'s own harmonic series, a sparkle (ElevenLabs), the '
             'DG-2 tesla zap tuned to C landing on the crest'),
    'tod_ws_expire': dict(stem='tod_ws_expire', variants=1, ch=1, keep=(0.90, 1.20),
        target=('k300', -12.0, 'abfx_demon_off', '1.9 dB over the Demon Slayer end at the same alias volume: the player must notice '
                'the gun leaving'),
        row=dict(SHAPE_STING_2D, VolMin='82', VolMax='82', Looping='nonlooping', FadeIn='0', FadeOut='0'),
        what='the window ending: the beam harmonics sagging a fifth and flickering out, an ElevenLabs sputter, the DG-2 flux '
             'crackle fading, a last soft thunk'),
    'tod_ws_idle_loop': dict(stem='tod_ws_idle_loop', variants=1, ch=1, keep=(2.99, 3.01), loop=3.0,
        target=('lufs', -15.0, 'tesla_idle', 'the DG-2\'s own idle hum level at the same alias volume (30)'),
        row=dict(SHAPE_IDLE, VolMin='30', VolMax='30', Looping='looping', FadeIn='150', FadeOut='150', PriorityMin='40', PriorityMax='90'),
        owner='_tod_wunderstrahl.gsc: played on the holder while the gun is out, stopped on putaway / expiry / down / death; '
              'StopOnEntDeath is the failsafe',
        what='the held gun: the DG-2 idle twice round (seam cross-faded), warmed, with a quiet thread of the beam harmonics swirling'),
}
ORDER = list(CUES)

# the alias header, verbatim (102 columns; asserted against sound/aliases/tod_ability.csv when building in the repo)
HEADER = ('Name,Behavior,Storage,FileSpec,FileSpecSustain,FileSpecRelease,Template,Loadspec,Secondary,SustainAlias,'
          'ReleaseAlias,Bus,VolumeGroup,DuckGroup,Duck,ReverbSend,CenterSend,VolMin,VolMax,DistMin,DistMaxDry,DistMaxWet,'
          'DryMinCurve,DryMaxCurve,WetMinCurve,WetMaxCurve,LimitCount,LimitType,EntityLimitCount,EntityLimitType,PitchMin,'
          'PitchMax,PriorityMin,PriorityMax,PriorityThresholdMin,PriorityThresholdMax,AmplitudePriority,PanType,Pan,Futz,'
          'Looping,RandomizeType,Probability,StartDelay,EnvelopMin,EnvelopMax,EnvelopPercent,OcclusionLevel,IsBig,'
          'DistanceLpf,FluxType,FluxTime,Subtitle,Doppler,ContextType,ContextValue,ContextType1,ContextValue1,ContextType2,'
          'ContextValue2,ContextType3,ContextValue3,Timescale,IsMusic,IsCinematic,FadeIn,FadeOut,Pauseable,StopOnEntDeath,'
          'Compression,StopOnPlay,DopplerScale,FutzPatch,VoiceLimit,IgnoreMaxDist,NeverPlayTwice,ContinuousPan,FileSource,'
          'FileSourceSustain,FileSourceRelease,FileTarget,FileTargetSustain,FileTargetRelease,Platform,Language,'
          'OutputDevices,PlatformMask,WiiUMono,StopAlias,DistanceLpfMin,DistanceLpfMax,FacialAnimationName,'
          'RestartContextLoops,SilentInCPZ,ContextFailsafe,GPAD,GPADOnly,MuteVoice,MuteMusic,RowSourceFileName,'
          'RowSourceShortName,RowSourceLineNumber').split(',')
CONTEXT_COLS = ('ContextType', 'ContextValue', 'ContextType1', 'ContextValue1', 'ContextType2', 'ContextValue2',
                'ContextType3', 'ContextValue3')


# ======================================================================================================================
# audio helpers (numpy / scipy; deterministic)
# ======================================================================================================================
def as2d(x):
    return x[:, None] if x.ndim == 1 else x


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def read_wav(path):
    """any wav -> float64 [n, ch] at SR"""
    import soundfile as sf
    from scipy.signal import resample_poly
    y, sr = sf.read(path, always_2d=True, dtype='float64')
    if sr != SR:
        y = resample_poly(y, SR, sr, axis=0)
    return y


def dg2(name):
    return mono(read_wav(os.path.join(DG2_ROOT, DG2[name])))


def encode(x):
    x = as2d(np.asarray(x, dtype=np.float64))
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


def decode_wav_bytes(b):
    with wave.open(io.BytesIO(b)) as w:
        ch, sr, sw, n = w.getnchannels(), w.getframerate(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        return None, (ch, sr, sw, n)
    x = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768.0
    return x.reshape(-1, ch), (ch, sr, sw, n)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def db(v):
    return 20.0 * np.log10(np.maximum(v, 1e-12))


def peak_db(x):
    return float(db(np.max(np.abs(x))))


def true_peak_db(x, loop=False):
    from scipy.signal import resample_poly
    x = as2d(x)
    if loop:
        x = np.concatenate([x[-256:], x, x[:256]])
    return float(db(np.max(np.abs(resample_poly(x, 4, 1, axis=0)))))


def kweight(x, loop=False):
    """BS.1770 K-weighting per channel (48 kHz coefficients); a loop is filtered as three tiles (no start transient)"""
    from scipy.signal import lfilter
    x = as2d(x)
    n = x.shape[0]
    if loop:
        x = np.concatenate([x, x, x])
    y = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585], x, axis=0)
    y = lfilter([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621], y, axis=0)
    return y[n:2 * n] if loop else y


def _blocks(k, win, hop, loop=False):
    if loop:
        k = np.concatenate([k, k[:win]])
    n = k.shape[0]
    if n < win:
        k = np.concatenate([k, np.zeros((win - n, k.shape[1]))])
        n = win
    c = np.concatenate([np.zeros((1, k.shape[1])), np.cumsum(k ** 2, axis=0)])
    st = np.arange(0, n - win + 1, hop)
    return ((c[st + win] - c[st]) / win).sum(axis=1)


def lufs(x, loop=False):
    """BS.1770-4 integrated loudness (400 ms blocks, 75 % overlap, -70 abs / -10 rel gates); channels summed"""
    k = kweight(x, loop)
    ms = _blocks(k, int(0.4 * SR), int(0.1 * SR), loop)
    l = -0.691 + 10 * np.log10(ms + 1e-20)
    ms = ms[l > -70]
    if ms.size == 0:
        return -70.0
    rel = -0.691 + 10 * np.log10(ms.mean()) - 10
    ms = ms[(-0.691 + 10 * np.log10(ms)) > rel]
    return float(-0.691 + 10 * np.log10(ms.mean())) if ms.size else -70.0


def k300(x, loop=False):
    """the loudest 300 ms K-weighted window (dB): how loud a short cue FEELS (integrated under-reads a 0.4 s bite)"""
    ms = _blocks(kweight(x, loop), int(0.3 * SR), int(0.005 * SR), loop)
    return float(-0.691 + 10 * np.log10(ms.max() + 1e-20))


def st_var(x, loop=False):
    """the spread (dB std) of 400 ms K-weighted windows: how much a loop moves"""
    ms = _blocks(kweight(x, loop), int(0.4 * SR), int(0.1 * SR), loop)
    return float(np.std(10 * np.log10(ms + 1e-20)))


def metric(name, x, loop=False):
    return lufs(x, loop) if name == 'lufs' else k300(x, loop)


def zero_phase(x, mag_fn, loop=False, pad_s=0.5):
    """filter by a real (zero-phase) magnitude response; a loop is filtered CIRCULARLY (its period is kept exactly),
    a one-shot is zero-padded first so nothing wraps"""
    x2 = as2d(x)
    n = x2.shape[0]
    p = 0 if loop else int(pad_s * SR)
    xp = np.concatenate([np.zeros((p, x2.shape[1])), x2, np.zeros((p, x2.shape[1]))]) if p else x2
    f = np.fft.rfftfreq(xp.shape[0], 1.0 / SR)
    H = mag_fn(np.maximum(f, 1e-6))
    y = np.fft.irfft(np.fft.rfft(xp, axis=0) * H[:, None], xp.shape[0], axis=0)
    y = y[p:p + n] if p else y
    return y[:, 0] if x.ndim == 1 else y


def hp(x, fc, order=2, loop=False):
    return zero_phase(x, lambda f: 1.0 / np.sqrt(1.0 + (fc / f) ** (2 * order)), loop)


def lp(x, fc, order=2, loop=False):
    return zero_phase(x, lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order)), loop)


def bp(x, lo, hi, order=2, loop=False):
    return zero_phase(x, lambda f: 1.0 / np.sqrt(1.0 + (lo / f) ** (2 * order)) / np.sqrt(1.0 + (f / hi) ** (2 * order)), loop)


def shelf(x, fc, gain_db, high=True, loop=False):
    """a smooth first-order-shaped shelf (gain_db above fc when high, below fc when not)"""
    def m(f):
        s = 1.0 / (1.0 + (fc / f) ** 2) if high else 1.0 / (1.0 + (f / fc) ** 2)
        return 10 ** (gain_db * s / 20.0)
    return zero_phase(x, m, loop)


def bell(x, fc, gain_db, width_oct=1.0, loop=False):
    return zero_phase(x, lambda f: 10 ** (gain_db * np.exp(-0.5 * (np.log2(f / fc) / (width_oct / 2.355)) ** 2) / 20.0), loop)


def resample(x, ratio):
    """play `ratio` times faster (2**(st/12) = up st semitones, and shorter), polyphase"""
    from fractions import Fraction
    from scipy.signal import resample_poly
    if abs(ratio - 1.0) < 1e-9:
        return x.copy()
    fr = Fraction(1.0 / ratio).limit_denominator(240)
    return resample_poly(x, fr.numerator, fr.denominator, axis=0)


def fades1(x, fin, fout):
    """fades on a 1-D or 2-D signal (keeps its shape)"""
    y = as2d(x).copy()
    a, b = int(fin * SR), int(fout * SR)
    if 0 < a < y.shape[0]:
        y[:a] *= (np.linspace(0, 1, a) ** 2)[:, None]
    if 0 < b < y.shape[0]:
        y[-b:] *= (np.linspace(1, 0, b) ** 2)[:, None]
    return y[:, 0] if x.ndim == 1 else y


def envelope(x, frame=0.005):
    x = mono(x)
    n = max(1, int(frame * SR))
    k = len(x) // n
    if k == 0:
        return np.array([np.sqrt(np.mean(x ** 2) + 1e-20)])
    return np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-20)


def trim(x, head_db=-50.0, tail_db=-56.0, pre=0.003, post=0.05):
    e = envelope(x)
    pk = e.max()
    if pk <= 1e-7:
        return x
    above = np.where(db(e / pk) > head_db)[0]
    tail = np.where(db(e / pk) > tail_db)[0]
    n5 = int(0.005 * SR)
    a = max(0, above[0] * n5 - int(pre * SR))
    b = min(len(x), (tail[-1] + 1) * n5 + int(post * SR))
    return x[a:b]


def onset_index(x, rel_db=-12.0):
    """the first sample where the 1 ms envelope reaches rel_db under its peak"""
    e = envelope(x, 0.001)
    i = int(np.argmax(db(e / (e.max() + 1e-20)) > rel_db))
    return i * int(0.001 * SR)


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)) + 1e-12)


def norm(x, target_rms=0.1):
    return x * (target_rms / rms(x))


def tanh_sat(x, drive):
    """memoryless soft saturation, unity small-signal gain (keeps a loop's period exactly)"""
    return np.tanh(drive * x) / drive


def place(dst, src, at_s, gain=1.0):
    """mix src into dst starting at at_s seconds (both 1-D or both 2-D), clipped to dst"""
    i = int(round(at_s * SR))
    if i >= dst.shape[0]:
        return dst
    j = min(dst.shape[0], i + src.shape[0])
    if i < 0:
        src = src[-i:]
        j = min(dst.shape[0], src.shape[0])
        i = 0
    dst[i:j] += gain * src[:j - i]
    return dst


def limit(x, ceil_db=CEIL_DB, radius_ms=10.0, loop=False):
    """look-ahead brickwall: each sample's gain is the smoothed minimum of what its neighbourhood needs, then never more
    than that sample needs, so the ceiling holds exactly; channels are linked; a loop's gain wraps (circular).
    -> (signal, deepest gain reduction in dB)"""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    x2 = as2d(x)
    c = 10 ** (ceil_db / 20.0)
    a = np.max(np.abs(x2), axis=1)
    need = np.minimum(1.0, c / np.maximum(a, 1e-12))
    if need.min() >= 1.0:
        return x.copy(), 0.0
    r = max(1, int(radius_ms * SR / 1000.0))
    if loop:
        pad = 3 * r + 2
        npad = np.concatenate([need[-pad:], need, need[:pad]])
        g = uniform_filter1d(minimum_filter1d(npad, size=2 * r + 1, mode='nearest'), size=r, mode='nearest')
        g = np.minimum(g[pad:pad + len(need)], need)
    else:
        g = np.minimum(uniform_filter1d(minimum_filter1d(need, size=2 * r + 1, mode='nearest'), size=r, mode='nearest'), need)
    y = x2 * g[:, None]
    return (y[:, 0] if x.ndim == 1 else y), float(db(g.min()))


def level(x, name, target, loop=False, max_gr=4.5, radius_ms=10.0):
    """gain onto the target (metric `name`) under the -1 dBFS brickwall, re-measured and corrected; a cue that cannot get
    there with at most max_gr dB of limiting stops short (what it reached is recorded). A cue whose 4x true peak would
    pass TP_MAX_DB gets its ceiling lowered by the excess. -> (signal, info)"""
    ceil = CEIL_DB
    for _ in range(3):
        m0 = metric(name, x, loop)
        g = target - m0
        y, gr = limit(x * 10 ** (g / 20.0), ceil, radius_ms, loop)
        for _ in range(8):
            err = target - metric(name, y, loop)
            if abs(err) < 0.02:
                break
            g += err
            y, gr = limit(x * 10 ** (g / 20.0), ceil, radius_ms, loop)
        reached = target
        if gr < -max_gr:
            lo, hi = target - 12.0, target
            for _ in range(24):                              # the loudest level that needs <= max_gr of limiting
                mid = 0.5 * (lo + hi)
                gg = g + (mid - target)
                yy, grr = limit(x * 10 ** (gg / 20.0), ceil, radius_ms, loop)
                if grr >= -max_gr:
                    lo = mid
                else:
                    hi = mid
            y, gr = limit(x * 10 ** ((g + lo - target) / 20.0), ceil, radius_ms, loop)
            reached = metric(name, y, loop)
        tp = true_peak_db(y, loop)
        if tp <= TP_MAX_DB + 1e-6:
            break
        ceil -= (tp - TP_MAX_DB) + 0.05
    return y, dict(metric=name, target=target, reached=round(metric(name, y, loop), 2), limit_db=round(gr, 2),
                   ceiling_db=round(ceil, 2), short_of_target=round(target - metric(name, y, loop), 2) if reached != target else 0.0)


def xfade_weights(F):
    """EQUAL-POWER cross-fade amplitudes (fade-in, fade-out): sin / cos, so two uncorrelated beds keep their power
    through the join (sin^2 / cos^2 amplitudes are equal-GAIN: a 3 dB hole mid-fade, a breath on every loop pass)"""
    u = np.linspace(0, np.pi / 2, F)
    return np.sin(u)[:, None], np.cos(u)[:, None]


def extend(x, n, xfade=0.15):
    """tile x to at least n samples, every join an equal-power cross-fade (never a hard splice)"""
    x = as2d(x)
    F = min(int(round(xfade * SR)), x.shape[0] // 3)
    win, wout = xfade_weights(F)
    out = x.copy()
    while out.shape[0] < n:
        join = out[-F:] * wout + x[:F] * win
        out = np.concatenate([out[:-F], join, x[F:]])
    return out


def make_loop(x, L, xfade=0.35, start=0.0):
    """an L-second circular loop from a bed: L seconds from `start`, the following xfade seconds cross-faded (equal
    power) back over the head, so the last sample flows into the first; a short bed is first extended by cross-faded
    tiling"""
    n, F = int(round(L * SR)), int(round(xfade * SR))
    a = int(round(start * SR))
    x = as2d(x)
    if x.shape[0] < a + n + F:
        x = extend(x, a + n + F, min(0.15, xfade))
    seg = x[a:a + n].copy()
    win, wout = xfade_weights(F)
    seg[:F] = seg[:F] * win + x[a + n:a + n + F] * wout    # sample 0 = x[a+n]: it follows the last sample, x[a+n-1]
    return seg


# ======================================================================================================================
# THE BEAM (synthesis)
# ======================================================================================================================
def snap(f, L):
    """the nearest frequency that completes a whole number of cycles in L seconds (a seamless loop by construction)"""
    return round(f * L) / L if L else f


BEAM_F = 2 * F0                  # the harmonic stack's spacing: 130 Hz (C3). Its pitch pulse sits above the ~20-80 Hz band
SUB_GAIN = 0.35                  # where the ear hears a drone as rough buzz; the 65 Hz fundamental rides under it as a PURE
                                 # sine (no envelope pulse) at this RMS against the stack's (measured: roughness 0.59 -> 0.03)


def beam_amp(f):
    """the beam's spectrum at frequency f: falling 0.92 per harmonic of 65 Hz, a body formant at 715 Hz (the laser's
    'voice'), a softer presence formant at 1.95 kHz, a roll-off above 4.2 kHz (rich, never harsh)"""
    n = f / F0
    a = n ** -0.92
    a *= 1.0 + 2.1 * np.exp(-0.5 * (np.log2(n / 11.0) / 0.45) ** 2)
    a *= 1.0 + 0.95 * np.exp(-0.5 * (np.log2(n / 30.0) / 0.32) ** 2)
    a /= 1.0 + (f / 4200.0) ** 4
    if n < 2.5:
        a *= 0.8                                             # the 130 Hz partial is felt; it must not eat the headroom
    return a


def beam_stack(N, L=None, stereo=True, seed=1, fmax=5800.0, swirl=0.5, pan_rate=0.25, chorus=0.33, glide=None, swirl_depth=0.42,
               amp_env=None, trem=None, fmin=0.0, tilt_db=0.0, sub=SUB_GAIN):
    """THE BEAM, N samples: harmonics of BEAM_F from fmin to fmax, plus the 65 Hz pure-sine fundamental (sub x the stack's
    RMS; 0 = none).
    L      : loop length (every partial + modulation snapped onto its 1/L grid) or None for a one-shot
    swirl  : Hz of the emphasis travelling up the spectrum (the swirl's pass rate); pan_rate: Hz the orbs circle L-R
    glide  : None or an array (N) of frequency multipliers (a pitch glide for one-shots); trem: None or (rate_fn, depth)
    amp_env: None or an array (N) of gains; tilt_db: extra dB per octave above 65 Hz (a darker / brighter stack)
    Partials up to 400 Hz are identical in both channels (a mono-safe core); higher ones circle and chorus."""
    rng = np.random.default_rng(seed)
    t = np.arange(N) / SR
    out = np.zeros((N, 2))
    if glide is not None:
        gphase = 2 * np.pi * np.cumsum(glide) / SR           # phase of a 1 Hz partial under the glide
    sw = snap(swirl, L)
    pr = snap(pan_rate, L)
    count = int(fmax // BEAM_F)
    for n in range(1, count + 1):
        f = snap(BEAM_F * n, L)
        if f < fmin or f > 9000.0:
            continue
        a = beam_amp(f) * 2 ** (tilt_db * np.log2(f / F0) / 6.0206)
        ph0 = np.pi * n * n / float(count)                   # Schroeder phases: a low crest factor
        if glide is None:
            phase = 2 * np.pi * f * t + ph0
        else:
            phase = f * gphase + ph0
        g = 1.0 + swirl_depth * np.cos(2 * np.pi * sw * t - 2 * np.pi * f / 715.0)
        s = a * g * np.sin(phase)
        if f <= 400.0 or not stereo:
            out[:, 0] += s
            out[:, 1] += s
        else:
            p = 0.5 + 0.3 * np.cos(2 * np.pi * pr * t + 2 * np.pi * rng.random())
            out[:, 0] += s * np.sqrt(2.0 * (1.0 - p))
            out[:, 1] += s * np.sqrt(2.0 * p)
        if f >= 195.0 and chorus > 0:
            k = 1 + (n % 2)                                  # 1 or 2 grid steps: slow beating
            d = (k / L) if L else 0.25 * k
            for side, sign in ((0, 1.0), (1, -1.0)):
                fd = f + sign * d
                if glide is None:
                    phd = 2 * np.pi * fd * t + 2 * np.pi * rng.random()
                else:
                    phd = fd * gphase + 2 * np.pi * rng.random()
                cs = chorus * a * g * np.sin(phd)
                if stereo:
                    out[:, side] += cs * 1.2
                    out[:, 1 - side] += cs * 0.25
                else:
                    out[:, 0] += cs
                    out[:, 1] += cs
    if sub > 0 and fmin <= F0:
        ph = (2 * np.pi * snap(F0, L) * t) if glide is None else (F0 * gphase)
        s = sub * rms(out) * np.sqrt(2.0) * (np.sin(ph) + 0.08 * np.sin(2 * ph + 0.7))
        out += s[:, None]
    if trem is not None:
        rate_fn, depth = trem
        tp = 2 * np.pi * np.cumsum(rate_fn(t)) / SR
        out *= (1.0 - depth * 0.5 * (1.0 - np.cos(tp)))[:, None]
    if amp_env is not None:
        out *= amp_env[:, None]
    return out if stereo else out[:, 0]


def whine(N, f0, glide=None, amp_env=None, seed=0, partials=((1, 1.0), (2, 0.32), (3, 0.12)), vib=(5.5, 0.004), trem=None):
    """a THIN electronic whine (a charging capacitor / relay coil): a few partials of a HIGH fundamental (C6 family),
    gliding, with a hair of vibrato. Never a low harmonic stack gliding through the voice range - that reads as a
    groan or a word (speech-to-text heard "What?" / "Oh" in the first raise / putaway)"""
    rng = np.random.default_rng(seed)
    t = np.arange(N) / SR
    gl = np.ones(N) if glide is None else glide
    base = 2 * np.pi * np.cumsum(gl * (1.0 + vib[1] * np.sin(2 * np.pi * vib[0] * t))) / SR
    out = sum(a * np.sin(k * f0 * base + 2 * np.pi * rng.random()) for k, a in partials)
    if trem is not None:
        rate_fn, depth = trem
        tp = 2 * np.pi * np.cumsum(rate_fn(t)) / SR
        out = out * (1.0 - depth * 0.5 * (1.0 - np.cos(tp)))
    return out if amp_env is None else out * amp_env


def exp_glide(N, k0, k1, curve=1.0):
    """frequency multipliers gliding exponentially k0 -> k1 over N samples (curve > 1: lingers, < 1: rushes)"""
    u = np.linspace(0.0, 1.0, N) ** curve
    return k0 * (k1 / k0) ** u


def noise_burst(n, seed, lo, hi, attack=0.002, tau=0.03):
    rng = np.random.default_rng(seed)
    x = bp(rng.standard_normal(n), lo, hi, order=2)
    t = np.arange(n) / SR
    return x * np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / tau)


def stereo_bed(x, offset_s=0.37):
    """a decorrelated stereo pair from a mono bed: the right channel is the same bed read offset_s later (circular)"""
    k = int(offset_s * SR) % len(x)
    return np.stack([x, np.roll(x, -k)], axis=1)


# ======================================================================================================================
# ELEVENLABS (cached takes)
# ======================================================================================================================
def load_takes():
    return json.load(open(TAKES_JSON, encoding='utf-8')) if os.path.exists(TAKES_JSON) else {}


def save_takes(data):
    os.makedirs(RAW, exist_ok=True)
    with open(TAKES_JSON, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')


def take_signal(row):
    """a cached take -> mono float64 at SR (the pcm_48000 stream is interleaved s16le; its channel count is recorded)"""
    p = os.path.join(REPO, row['file'])
    b = open(p, 'rb').read()
    if sha256(b) != row['sha256']:
        sys.exit('WUNDERSTRAHL SOUNDS: cached take %s changed since it was scored (sha mismatch) - delete it and re-run build' % row['file'])
    x = np.frombuffer(b, dtype='<i2').astype(np.float64) / 32768.0
    if row.get('channels', 2) == 2 and len(x) % 2 == 0:
        x = 0.5 * (x[0::2] + x[1::2])
    if LAYERS[row['layer']].get('reverse'):
        x = np.ascontiguousarray(x[::-1])
    return x


def generate_take(layer, i):
    sys.path.insert(0, os.path.join(REPO, 'tools', 'black_market_vo'))
    import eleven                                            # reads ELEVENLABS_API_KEY; never prints or stores it
    spec = LAYERS[layer]
    prompt = spec['prompts'][i % len(spec['prompts'])]
    body = {'text': prompt, 'duration_seconds': max(0.5, float(spec['secs'])), 'prompt_influence': PROMPT_INFLUENCE, 'model_id': MODEL}
    if spec.get('loop'):
        body['loop'] = True
    try:
        raw = eleven.call('POST', '/v1/sound-generation', body=body, query={'output_format': 'pcm_48000'})
    except RuntimeError as e:                                # a model / plan without the loop option: ask plainly
        if not body.pop('loop', None):
            raise
        print('  (%s: the loop option was refused, %s; asking without it - the seam is cross-faded here anyway)' % (layer, str(e)[:80]))
        raw = eleven.call('POST', '/v1/sound-generation', body=body, query={'output_format': 'pcm_48000'})
    if not isinstance(raw, (bytes, bytearray)) or len(raw) < 4800:
        sys.exit('WUNDERSTRAHL SOUNDS: %s take %d: unexpected response (%s)' % (layer, i + 1, type(raw).__name__))
    ch = 2 if abs(len(raw) / 4.0 / SR - body['duration_seconds']) <= abs(len(raw) / 2.0 / SR - body['duration_seconds']) else 1
    d = os.path.join(RAW, layer)
    os.makedirs(d, exist_ok=True)
    name = 'take_%d' % (i + 1)
    p = os.path.join(d, name + '.pcm')
    open(p, 'wb').write(raw)
    meta = dict(layer=layer, name=name, file=os.path.relpath(p, REPO).replace('\\', '/'), sha256=sha256(raw), channels=ch, prompt=prompt,
                model=MODEL, secs=spec['secs'], loop=bool(spec.get('loop')), prompt_influence=PROMPT_INFLUENCE)
    with open(p[:-4] + '.json', 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(meta, fh, indent=1)
    return meta


def features(x):
    x = trim(x)
    if len(x) < int(0.04 * SR):
        return None
    e = envelope(x, 0.010)
    pk = e.max()
    dur = len(x) / SR
    t = np.arange(len(e)) * 0.010
    ip = int(np.argmax(e))
    onset = float(t[np.where(e >= 0.5 * pk)[0][0]])
    low = np.where(e[ip:] <= 0.1 * pk)[0]
    decay = float(low[0] * 0.010) if low.size else float(dur - t[ip])
    tail = float(db(e[-5:].mean() / pk))
    hot = (np.abs(x) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), 'valid') >= 4
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    tot = spec.sum() + 1e-12
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    e100 = envelope(x, 0.1)
    mid = e100[max(1, len(e100) // 10):max(2, len(e100) - len(e100) // 10)]
    e20 = db(envelope(x, 0.02) / pk)
    peaks = int(np.sum((e20[1:-1] > e20[:-2] + 4) & (e20[1:-1] >= e20[2:]) & (e20[1:-1] > -20)))
    ps = spec ** 2                                           # POWER shares: what a layer contributes once it is levelled
    ptot = ps.sum() + 1e-20
    return dict(p_low=round(float(ps[f < 200].sum() / ptot), 3), p_mid=round(float(ps[(f >= 200) & (f < 2000)].sum() / ptot), 3),
                p_hi=round(float(ps[f >= 2000].sum() / ptot), 3), crest=round(float(db(np.max(np.abs(x)) / rms(x))), 1),
                dur=round(dur, 3), onset=round(onset, 3), peak_at=round(float(t[ip] / max(dur, 1e-6)), 3), decay=round(decay, 3),
                tail_db=round(tail, 1), clip=round(float(np.mean(runs)) if runs.size else 0.0, 4),
                low=round(float(spec[f < 180].sum() / tot), 3), hi=round(float(spec[f > 4000].sum() / tot), 3),
                flat=round(float(np.exp(np.mean(np.log(s))) / np.mean(s)), 3),
                steady=round(float(np.std(db(mid / (mid.max() + 1e-12)))) if mid.size > 2 else 99.0, 2),
                jagged=round(float(np.std(np.diff(e20[e20 > -40]))) if np.sum(e20 > -40) > 3 else 0.0, 2), transients=peaks,
                late_db=round(float(db(e[int(len(e) * 0.7):].mean() / pk)), 1) if len(e) > 8 else 0.0,
                early_db=round(float(db(e[:max(1, int(len(e) * 0.3))].mean() / pk)), 1) if len(e) > 8 else 0.0)


def closeness(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(layer, ft):
    if ft is None:
        return -1.0, {'dead': 1.0}
    p = LAYERS[layer]['profile']
    want = LAYERS[layer]['secs']
    s = {'clip': 1.0 - min(1.0, ft['clip'] * 50)}
    if p == 'bed':
        s['length'] = closeness(ft['dur'], 0.8 * want, 1.3 * want, 0.4 * want)
        s['steady'] = closeness(ft['steady'], 0.0, 2.5, 4.0)
        s['fizz'] = closeness(ft['hi'], 0.12, 1.0, 0.12)
    elif p == 'crack':
        s['length'] = closeness(ft['dur'], 0.15, 1.1, 0.4)
        s['onset'] = closeness(ft['onset'], 0.0, 0.03, 0.08)
        s['decay'] = closeness(ft['decay'], 0.12, 0.45, 0.3)           # a crack with a body, not a 80 ms click
        s['body'] = closeness(ft['crest'], 6.0, 16.0, 6.0)             # it has to carry loudness, not only a peak
        s['peak_at'] = closeness(ft['peak_at'], 0.0, 0.2, 0.3)
        s['bright'] = closeness(ft['hi'], 0.08, 1.0, 0.1)
        s['tail'] = closeness(ft['tail_db'], -90, -26, 14)
    elif p == 'rise':                                        # scored REVERSED: the discharge read backwards
        s['length'] = closeness(ft['dur'], 0.35, 1.3, 0.4)
        s['peak_at'] = closeness(ft['peak_at'], 0.65, 1.0, 0.3)
        s['build'] = closeness(ft['onset'] / max(ft['dur'], 1e-6), 0.35, 0.98, 0.3)
        s['stops'] = closeness(ft['tail_db'], -12, 0, 14)
    elif p == 'fall':
        s['length'] = closeness(ft['dur'], 0.45, 1.3, 0.4)
        s['onset'] = closeness(ft['onset'], 0.0, 0.15, 0.2)
        s['peak_at'] = closeness(ft['peak_at'], 0.0, 0.35, 0.3)
        s['decay'] = closeness(ft['decay'], 0.25, 1.1, 0.4)
        s['tail'] = closeness(ft['tail_db'], -90, -28, 14)
        s['whine'] = closeness(ft['p_mid'] + ft['p_hi'], 0.5, 1.0, 0.3)   # the release uses its whine + hiss, not a sub rumble
    elif p == 'tick':
        s['length'] = closeness(ft['dur'], 0.08, 0.45, 0.3)
        s['onset'] = closeness(ft['onset'], 0.0, 0.03, 0.08)
        s['decay'] = closeness(ft['decay'], 0.02, 0.25, 0.25)
        s['bright'] = closeness(ft['hi'], 0.15, 1.0, 0.15)
    elif p == 'burst':
        s['length'] = closeness(ft['dur'], 0.3, 1.0, 0.4)
        s['onset'] = closeness(ft['onset'], 0.0, 0.06, 0.12)
        s['decay'] = closeness(ft['decay'], 0.1, 0.7, 0.4)
        s['bright'] = closeness(ft['hi'], 0.08, 1.0, 0.1)
        s['tail'] = closeness(ft['tail_db'], -90, -26, 14)
    elif p == 'clicks':
        s['length'] = closeness(ft['dur'], 0.3, 1.1, 0.4)
        s['onset'] = closeness(ft['onset'], 0.0, 0.2, 0.25)
        s['transients'] = closeness(ft['transients'], 2, 6, 2)
        s['bright'] = closeness(ft['hi'], 0.06, 1.0, 0.08)
    elif p == 'click':
        s['length'] = closeness(ft['dur'], 0.15, 0.75, 0.3)
        s['onset'] = closeness(ft['onset'], 0.0, 0.05, 0.1)
        s['decay'] = closeness(ft['decay'], 0.02, 0.45, 0.3)
        s['tail'] = closeness(ft['tail_db'], -90, -26, 14)
        s['audible'] = closeness(ft['p_mid'] + ft['p_hi'], 0.4, 1.0, 0.3)  # a switch you can hear on any speaker
    elif p == 'sputter':
        s['length'] = closeness(ft['dur'], 0.7, 1.5, 0.4)
        s['jagged'] = closeness(ft['jagged'], 3.0, 30.0, 2.5)
        s['dies'] = closeness(ft['early_db'] - ft['late_db'], 4.0, 60.0, 4.0)
        s['tail'] = closeness(ft['tail_db'], -90, -26, 14)
    elif p == 'shimmer':
        s['length'] = closeness(ft['dur'], 0.5, 1.3, 0.4)
        s['bright'] = closeness(ft['hi'], 0.25, 1.0, 0.2)
        s['airy'] = closeness(ft['low'], 0.0, 0.12, 0.15)
        s['tail'] = closeness(ft['tail_db'], -90, -26, 14)
    return float(sum(s.values()) / len(s)), {k: round(v, 3) for k, v in s.items()}


def ensure_takes(offline=False):
    """every layer holds LAYERS[layer]['takes'] scored takes; only MISSING takes call the API"""
    data = load_takes()
    calls = 0
    for layer in LAYER_ORDER:
        rows = data.get(layer, [])
        want = LAYERS[layer]['takes']
        for i in range(len(rows), want):
            if offline:
                sys.exit('WUNDERSTRAHL SOUNDS: --offline but %s has %d of %d takes cached (%s)' % (layer, len(rows), want, RAW))
            meta = generate_take(layer, i)
            calls += 1
            rows.append(meta)
            data[layer] = rows
            save_takes(data)
            print('  generated %s %s' % (layer, meta['name']), flush=True)
        for r in rows:                                       # (re)measure: a profile edit rescoring needs no API
            ft = features(take_signal(r))
            r['features'] = ft
            r['score'], r['parts'] = score(layer, ft)
        data[layer] = rows
    save_takes(data)
    return data, calls


def picked(data, layer, k=1):
    """the k best takes of a layer (picks.json first, then by score)"""
    picks = json.load(open(PICKS_JSON, encoding='utf-8')) if os.path.exists(PICKS_JSON) else {}
    rows = [r for r in data.get(layer, []) if r.get('features')]
    out = [r for name in picks.get(layer, []) for r in rows if r['name'] == name]
    for r in sorted(rows, key=lambda r: (-r['score'], r['name'])):
        if r not in out:
            out.append(r)
    if len(out) < k:
        sys.exit('WUNDERSTRAHL SOUNDS: layer %s has %d usable takes, %d needed' % (layer, len(out), k))
    return out[:k]


# ======================================================================================================================
# THE CUES (render)
# ======================================================================================================================
class Ctx:
    """the render's inputs: the picked takes (signals + provenance) and the DG-2 originals"""
    def __init__(self, data):
        self.data = data
        self.used = {}
        self.dg = {k: dg2(k) for k in DG2}

    def take(self, layer, rank=0):
        r = picked(self.data, layer, rank + 1)[rank]
        self.used['%s/%s' % (layer, r['name'])] = dict(file=r['file'], sha256=r['sha256'], prompt=r['prompt'], score=round(r['score'], 3))
        return trim(take_signal(r), head_db=-45.0, tail_db=-60.0)


def crackle_bed(ctx, L, seed, mono_out=False):
    """the beam's crackle: the ElevenLabs crackle loop + the DG-2 projectile crackle + the DG-2 flux fizz, each made
    circular at L, soft-clipped (no spike drives the limiter); stereo = two offset reads of one bed"""
    el = hp(ctx.take('crackle_loop'), 900.0)
    pl = hp(ctx.dg['projloop'], 1200.0)
    fx = hp(ctx.dg['flux'], 2500.0, order=3)
    a = make_loop(norm(el, 0.1), L, 0.4, start=0.2)
    b = make_loop(norm(pl, 0.1), L, 0.25)
    c = make_loop(norm(fx[int(0.6 * SR):int(2.0 * SR)], 0.1), L, 0.3)
    bed = mono(a) * 1.0 + mono(b) * 0.55 + mono(c) * 0.35
    bed = tanh_sat(norm(bed, 0.1), 4.0)
    bed = hp(bed, 700.0, loop=True)
    bed = bell(bed, 4000.0, 5.0, 1.6, loop=True)             # the fizz lives at 2.5-6 kHz, where it reads as electricity
    bed = lp(bed, 9500.0, order=2, loop=True)                 # not as air: the takes carry most of their power over 8 kHz
    return bed if mono_out else stereo_bed(bed, 0.37 + 0.11 * (seed % 3))


def idle_hum(ctx, L):
    """the DG-2 idle hum made circular at L (its own seam cross-faded), DC removed, kept to its hum (< 600 Hz)"""
    x = hp(ctx.dg['idle'], 25.0)
    return lp(make_loop(norm(x, 0.1), L, 0.3)[:, 0], 600.0, loop=True)


def render_fire_loop(ctx, stereo):
    L = CUES['tod_ws_fire_loop_plr']['loop']
    N = int(round(L * SR))
    core = norm(beam_stack(N, L=L, stereo=True, seed=11, swirl=0.5, pan_rate=0.25, chorus=0.33), 0.1)
    crack = norm(crackle_bed(ctx, L, 3), 0.1)
    hum = norm(idle_hum(ctx, L), 0.1)
    if stereo:
        mix = core * 1.0 + crack * 0.48 + hum[:, None] * 0.22
        mix = tanh_sat(mix / (np.max(np.abs(mix)) + 1e-9) * 0.9, 1.6)
        mix = hp(mix, 32.0, loop=True)
        mix = shelf(mix, 130.0, -2.0, high=False, loop=True)
        mix = shelf(mix, 6500.0, -3.0, loop=True)
    else:
        mix = mono(core) * 1.0 + mono(crack) * 0.55 + hum * 0.16
        mix = tanh_sat(mix / (np.max(np.abs(mix)) + 1e-9) * 0.9, 1.6)
        mix = hp(mix, 70.0, loop=True)
        mix = bell(mix, 1800.0, 2.0, 1.6, loop=True)
        mix = shelf(mix, 7000.0, -2.5, loop=True)
    return mix


def render_fire_start(ctx, stereo):
    N = int(0.66 * SR)
    T_CRACK = 0.15
    out = np.zeros((N, 2))
    # the trigger thunk (t = 0): the first 50 ms of the DG-2 impact, low-passed - the capacitor engaging
    th = lp(ctx.dg['impact_zb'][:int(0.05 * SR)], 900.0)
    th = fades1(th, 0.001, 0.02)
    place(out, np.stack([th, th], 1), 0.0, 0.22 / (np.max(np.abs(th)) + 1e-9))
    # the rising charge (0 -> T_CRACK): the beam's own partials gliding up into the beam's pitch
    nr = int(T_CRACK * SR)
    env = np.linspace(0.0, 1.0, nr) ** 2.2
    rise = beam_stack(nr, L=None, stereo=True, seed=21, fmax=2600.0, chorus=0.2, glide=exp_glide(nr, 0.32, 1.0, 0.8), amp_env=env, swirl=6.0)
    place(out, rise, 0.0, 0.7 / (np.max(np.abs(rise)) + 1e-9))
    # + the reversed ElevenLabs discharge and the DG-2 flux swelling into its own peak, both landing on the crack
    cz = ctx.take('charge_zap')
    seg = cz[-nr:] if len(cz) >= nr else np.concatenate([np.zeros(nr - len(cz)), cz])
    seg = hp(seg, 400.0) * (np.linspace(0, 1, nr) ** 1.5)
    place(out, np.stack([seg, seg * 0.9], 1), 0.0, 0.45 / (np.max(np.abs(seg)) + 1e-9))
    fx = hp(ctx.dg['flux'][int(1.0 * SR) - nr:int(1.0 * SR)], 2000.0)   # the flux swelling into its own peak (1.0 s)
    fx = fx * np.linspace(0, 1, nr) ** 2
    place(out, np.stack([fx * 0.8, fx], 1), 0.0, 0.25 / (np.max(np.abs(fx)) + 1e-9))
    # the crack (T_CRACK): the ElevenLabs crack, the DG-2 projectile impact zap, a 55 -> 40 Hz sub thump
    ck = ctx.take('ignite_crack')
    ck = ck[max(0, onset_index(ck) - int(0.002 * SR)):]
    ck = fades1(ck[:int(0.5 * SR)], 0.0, 0.12)
    ck = tanh_sat(ck / (np.max(np.abs(ck)) + 1e-9), 3.0)     # the crack's needle peak rounded: its snap stays, its spike goes
    ck = lp(ck, 9000.0)
    place(out, np.stack([ck, ck], 1), T_CRACK, 1.0 / (np.max(np.abs(ck)) + 1e-9))
    zp = hp(ctx.dg['impact_zb'][:int(0.35 * SR)], 120.0)
    zp = fades1(zp, 0.0, 0.12)
    place(out, np.stack([zp * 0.95, zp], 1), T_CRACK, 0.8 / (np.max(np.abs(zp)) + 1e-9))
    nt = int(0.09 * SR)
    tt = np.arange(nt) / SR
    thump = np.sin(2 * np.pi * np.cumsum(55.0 - 15.0 * tt / 0.09) / SR) * np.minimum(1, tt / 0.002) * np.exp(-tt / 0.03)
    place(out, np.stack([thump, thump], 1), T_CRACK, 0.75)
    # the settle: the beam at full pitch blooming then fading (the held loop has faded in under it by now)
    ns = N - int(T_CRACK * SR)
    env2 = np.exp(-np.arange(ns) / SR / 0.18) * np.minimum(1.0, np.arange(ns) / (0.004 * SR))
    st = beam_stack(ns, L=None, stereo=True, seed=22, fmax=3900.0, chorus=0.3, amp_env=env2, swirl=2.0)
    place(out, st, T_CRACK, 0.45 / (np.max(np.abs(st)) + 1e-9))
    fz = crackle_bed(ctx, 1.0, 5)[:ns] * np.exp(-np.arange(ns) / SR / 0.14)[:, None]
    place(out, fz, T_CRACK, 0.3 / (np.max(np.abs(fz)) + 1e-9))
    out = hp(out, 30.0)
    out = shelf(out, 9000.0, -3.0)
    out = fades1(out, 0.001, 0.06)
    return out if stereo else mono(out)


def render_fire_stop(ctx, stereo):
    N = int(0.74 * SR)
    out = np.zeros((N, 2))
    t = np.arange(N) / SR
    # the beam cut: a snap + crackle pops dying in 80 ms
    sn = noise_burst(int(0.03 * SR), 31, 1500.0, 9000.0, 0.0005, 0.006)
    place(out, np.stack([sn, sn], 1), 0.0, 0.28 / (np.max(np.abs(sn)) + 1e-9))
    pops = crackle_bed(ctx, 1.0, 7)[:int(0.12 * SR)] * np.exp(-np.arange(int(0.12 * SR)) / SR / 0.035)[:, None]
    place(out, pops, 0.0, 0.22 / (np.max(np.abs(pops)) + 1e-9))
    # the power-down whine: the stack falling 1.0 -> 0.28 with the swirl winding down (12 Hz -> 2 Hz flutter)
    env = np.exp(-t / 0.2) * np.minimum(1.0, t / 0.004)
    wh = beam_stack(N, L=None, stereo=True, seed=32, fmax=3250.0, chorus=0.3, glide=exp_glide(N, 1.0, 0.28, 0.75), amp_env=env,
                    trem=(lambda tt: 12.0 - 10.0 * np.minimum(1.0, tt / 0.6), 0.35), swirl=3.0)
    place(out, wh, 0.0, 1.0 / (np.max(np.abs(wh)) + 1e-9))
    # the coil's thin whine falling with it (130 x 10 Hz -> 0.28): the power-down reads as a machine, never a groan
    cw = whine(N, F0 * 20, glide=exp_glide(N, 1.0, 0.28, 0.75), seed=34, partials=((1, 1.0), (2, 0.25)),
               amp_env=np.exp(-t / 0.26) * np.minimum(1.0, t / 0.006))
    place(out, np.stack([cw, cw], 1), 0.0, 0.32 / (np.max(np.abs(cw)) + 1e-9))
    # the soft hiss: the ElevenLabs power-down (its whine + hiss above 600 Hz) + a little filtered air, from 20 ms
    pdn = hp(ctx.take('powerdown'), 600.0)
    pdn = fades1(pdn[:int(0.68 * SR)], 0.01, 0.2) * np.exp(-np.arange(min(len(pdn), int(0.68 * SR))) / SR / 0.3)
    place(out, np.stack([pdn, pdn * 0.95], 1), 0.02, 0.24 / (np.max(np.abs(pdn)) + 1e-9))
    na = int(0.6 * SR)
    air = bp(np.random.default_rng(33).standard_normal(na), 3000.0, 9000.0) * np.exp(-np.arange(na) / SR / 0.18) * \
        np.minimum(1.0, np.arange(na) / (0.03 * SR))
    place(out, np.stack([air, np.roll(air, 311)], 1), 0.02, 0.05 / (np.max(np.abs(air)) + 1e-9))
    out = hp(out, 30.0)
    out = tanh_sat(out / (np.max(np.abs(out)) + 1e-9) * 0.95, 1.5)   # the cut's snap rounded so the whine carries the level
    out = shelf(out, 8000.0, -5.0)
    out = fades1(out, 0.0015, 0.12)
    return out if stereo else mono(out)


def render_impact_loop(ctx):
    L = CUES['tod_ws_impact_loop']['loop']
    N = int(round(L * SR))
    bed = make_loop(norm(hp(ctx.take('burn_loop'), 150.0), 0.1), L, 0.4, start=0.3)[:, 0]
    bed = lp(bed, 9000.0, loop=True)
    pl = make_loop(norm(hp(ctx.dg['projloop'], 100.0), 0.1), L, 0.25)[:, 0]
    tone = beam_stack(N, L=L, stereo=False, seed=41, fmin=390.0, fmax=1560.0, chorus=0.25, sub=0, swirl=snap(1.0, L), swirl_depth=0.5)
    tone = hp(norm(tone, 0.1), 400.0, loop=True)
    # the molten body: 70-420 Hz noise bubbling at 1.0 and 1.67 Hz (both on the loop's grid) - the wall is boiling
    tt = np.arange(N) / SR
    roar = bp(np.random.default_rng(43).standard_normal(N), 70.0, 420.0, loop=True)
    roar *= 0.65 + 0.2 * np.sin(2 * np.pi * snap(1.0, L) * tt) + 0.15 * np.sin(2 * np.pi * snap(1.67, L) * tt + 1.3)
    spits = np.zeros(N)
    rng = np.random.default_rng(42)
    tcur = 0.0
    while True:
        tcur += rng.exponential(1.0 / 7.0)
        if tcur >= L:
            break
        n = int(rng.uniform(0.006, 0.018) * SR)
        b = noise_burst(n, int(rng.integers(1 << 30)), 2000.0, 11000.0, 0.0005, n / SR / 3.0) * rng.uniform(0.4, 1.0)
        i = int(tcur * SR)
        idx = (np.arange(n) + i) % N                       # circular placement: a spit across the seam wraps
        spits[idx] += b
    mix = norm(bed, 0.1) * 0.8 + norm(pl, 0.1) * 0.5 + tone * 0.3 + norm(roar, 0.1) * 0.55 + norm(spits, 0.1) * 0.3
    mix = tanh_sat(mix / (np.max(np.abs(mix)) + 1e-9) * 0.9, 2.0)
    mix = hp(mix, 55.0, loop=True)
    mix = bell(mix, 3000.0, 2.0, 1.5, loop=True)
    mix = shelf(mix, 8000.0, -6.0, loop=True)
    return mix


def render_hit(ctx, v):
    N = int(0.30 * SR)
    out = np.zeros(N)
    sz = ctx.take('flesh_sizzle', v)
    sz = lp(bell(hp(sz, 700.0), 3500.0, 4.0, 1.5), 9000.0)  # the sear in its 2-6 kHz band, not as air
    sz = fades1(sz[:int(0.26 * SR)], 0.001, 0.08)
    place(out, sz, 0.0, 0.85 / (np.max(np.abs(sz)) + 1e-9))
    b0 = ctx.dg['bounce0']
    off = [0.0, 0.40, 0.43][v]
    sl = hp(b0[int(off * SR):int((off + 0.06) * SR)], 400.0)
    sl = fades1(sl, 0.001, 0.03)
    place(out, sl, 0.0, 0.8 / (np.max(np.abs(sl)) + 1e-9))
    n = int(0.08 * SR)
    tt = np.arange(n) / SR
    f = F0 * [16, 18, 20][v]                                  # a tick on the beam's own harmonics (1040 / 1170 / 1300 Hz)
    tick = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * np.minimum(1.0, tt / 0.002) * np.exp(-tt / 0.022)
    place(out, tick, 0.0, 0.65)
    out = resample(out, 2 ** ([0.0, 1.5, -1.5][v] / 12.0))
    out = trim(out, tail_db=-60.0)
    out = shelf(hp(out, 150.0), 9000.0, -5.0)
    return fades1(out, 0.0005, 0.04)


def render_kill(ctx, v):
    N = int(0.68 * SR)
    out = np.zeros(N)
    # the zap-pop: the DG-2 projectile impact's first 140 ms + a bright synth chirp 2.4 -> 0.9 kHz
    zp = ctx.dg['impact_zb'][:int(0.14 * SR)]
    zp = fades1(hp(zp, 60.0), 0.0005, 0.06)
    place(out, zp, 0.0, 1.0 / (np.max(np.abs(zp)) + 1e-9))
    n = int(0.09 * SR)
    tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(90.0 - 40.0 * tt / 0.09) / SR) * np.minimum(1, tt / 0.0015) * np.exp(-tt / 0.03)
    place(out, body, 0.0, 1.0)                                # every kill pops with weight, whichever take rides on it
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    ch = np.sin(2 * np.pi * np.cumsum(2400.0 * (900.0 / 2400.0) ** (tt / 0.06)) / SR) * np.minimum(1, tt / 0.001) * np.exp(-tt / 0.018)
    place(out, ch, 0.0, 0.45)
    cl = noise_burst(int(0.012 * SR), 51 + v, 2000.0, 12000.0, 0.0003, 0.003)
    place(out, cl, 0.0, 0.4 / (np.max(np.abs(cl)) + 1e-9))
    # the embers + the ash: the ElevenLabs disintegration (its pop aligned to ours) + a filtered-air whoosh
    ds = ctx.take('disintegrate', v)
    ds = ds[max(0, onset_index(ds) - int(0.002 * SR)):]
    ds = fades1(lp(ds, 10000.0)[:int(0.62 * SR)], 0.0005, 0.15)
    place(out, ds, 0.005, 0.6 / (np.max(np.abs(ds)) + 1e-9))
    nw = int(0.5 * SR)
    tw = np.arange(nw) / SR
    wenv = np.minimum(1.0, tw / 0.11) * np.exp(-np.maximum(0.0, tw - 0.11) / 0.13)
    wh = bp(np.random.default_rng(55 + v).standard_normal(nw), 500.0, 4000.0) * wenv
    place(out, wh, 0.03, 0.22 / (np.max(np.abs(wh)) + 1e-9))
    b1 = hp(ctx.dg['bounce1'][int(0.08 * SR):int(0.26 * SR)], 200.0)
    place(out, fades1(b1, 0.002, 0.06), 0.02, 0.18 / (np.max(np.abs(b1)) + 1e-9))
    out = resample(out, 2 ** ([0.0, 2.0, -2.0][v] / 12.0))
    out = trim(out, tail_db=-60.0)
    out = tanh_sat(out / (np.max(np.abs(out)) + 1e-9) * 0.95, 1.5)   # a little grit, a rounder peak: loud without the limiter
    out = shelf(hp(out, 45.0), 8500.0, -4.0)
    return fades1(out, 0.0005, 0.08)


def render_raise(ctx):
    N = int(0.85 * SR)
    out = np.zeros(N)
    t = np.arange(N) / SR
    nw = int(0.62 * SR)
    env = np.minimum(1.0, (np.arange(nw) / nw) ** 1.6 * 1.25) * np.exp(-np.maximum(0, np.arange(nw) / SR - 0.5) / 0.08)
    # the charge whine: C6 rising from two octaves down, the swirl spinning up (2 -> 16 Hz flutter)
    wh = whine(nw, F0 * 16, glide=exp_glide(nw, 0.25, 1.0, 0.9), amp_env=env, seed=61,
               trem=(lambda tt: 2.0 + 14.0 * np.minimum(1.0, tt / 0.55), 0.3))
    place(out, wh, 0.0, 0.55 / (np.max(np.abs(wh)) + 1e-9))
    # the beam arming underneath in the last 0.3 s: its own stack (above the voice range) blooming at full pitch
    na = int(0.42 * SR)
    aenv = np.minimum(1.0, (np.arange(na) / (0.3 * SR)) ** 2) * np.exp(-np.maximum(0, np.arange(na) / SR - 0.3) / 0.05)
    arm = beam_stack(na, L=None, stereo=False, seed=62, fmin=260.0, fmax=2600.0, chorus=0.25, sub=0, amp_env=aenv, swirl=3.0)
    place(out, arm, 0.25, 0.4 / (np.max(np.abs(arm)) + 1e-9))
    bl = ctx.take('bulbs_on')
    bl = fades1(lp(bl, 7000.0)[:int(0.8 * SR)], 0.001, 0.15)
    bl = tanh_sat(bl / (np.max(np.abs(bl)) + 1e-9), 4.0)     # the clicks keep their edge, lose their needle peaks
    bl = lp(bl, 9000.0)                                       # and the clip's corners (no inter-sample overs)
    place(out, bl, 0.05, 0.45 / (np.max(np.abs(bl)) + 1e-9))
    hum = make_loop(norm(hp(ctx.dg['idle'], 25.0), 0.1), 1.2, 0.2)[:, 0]
    hum = lp(hum, 900.0) * np.minimum(1.0, np.maximum(0.0, np.arange(len(hum)) / SR - 0.0) / 0.4)
    place(out, hum[:N - int(0.3 * SR)], 0.3, 0.3 / (np.max(np.abs(hum)) + 1e-9))
    out = hp(out, 30.0)
    return fades1(out, 0.002, 0.12)


def render_putaway(ctx):
    N = int(0.5 * SR)
    out = np.zeros(N)
    sw = ctx.take('switch_off')
    sw = fades1(sw[:int(0.45 * SR)], 0.001, 0.12)
    sw = tanh_sat(sw / (np.max(np.abs(sw)) + 1e-9), 4.0)     # the click keeps its edge, loses its needle peak
    place(out, sw, 0.0, 0.7 / (np.max(np.abs(sw)) + 1e-9))
    nb = int(0.36 * SR)
    env = np.exp(-np.arange(nb) / SR / 0.09) * np.minimum(1.0, np.arange(nb) / (0.003 * SR))
    bl = whine(nb, F0 * 16, glide=exp_glide(nb, 1.0, 0.35, 0.7), amp_env=env, seed=71)   # the coil dropping out: C6 falling
    place(out, bl, 0.0, 0.6 / (np.max(np.abs(bl)) + 1e-9))
    hum = lp(hp(ctx.dg['idle'][:int(0.4 * SR)], 25.0), 900.0) * np.exp(-np.arange(int(0.4 * SR)) / SR / 0.07)
    place(out, hum, 0.0, 0.25 / (np.max(np.abs(hum)) + 1e-9))
    out = hp(out, 30.0)
    out = lp(tanh_sat(out / (np.max(np.abs(out)) + 1e-9) * 0.95, 1.6), 12000.0)
    return fades1(out, 0.001, 0.1)


def render_grab(ctx):
    N = int(1.28 * SR)
    out = np.zeros(N)
    t = np.arange(N) / SR
    # the golden swell: C major on the beam's own harmonic series (n = 2 3 4 5 6 8 10 12 16 + air at 20 24), each
    # partial a slow chorus pair; swell to 0.55 s, held to 0.75 s, then a 0.5 s release
    swell = np.where(t < 0.55, (t / 0.55) ** 1.8, np.where(t < 0.75, 1.0, np.exp(-(t - 0.75) / 0.17)))
    rng = np.random.default_rng(81)
    chord = np.zeros(N)
    for n, a in ((2, 0.5), (3, 0.45), (4, 0.55), (5, 0.45), (6, 0.42), (8, 0.42), (10, 0.38), (12, 0.32), (16, 0.24), (20, 0.14),
                 (24, 0.1), (32, 0.06)):
        f = F0 * n
        for d in (-0.45, 0.0, 0.5):
            chord += a * (1.0 if d == 0 else 0.45) * np.sin(2 * np.pi * (f + d) * t + 2 * np.pi * rng.random())
        for h, ha in ((2, 0.18), (3, 0.08)):                 # a little warmth above each voice
            chord += a * ha * np.sin(2 * np.pi * f * h * t + 2 * np.pi * rng.random())
    chord = lp(chord, 7000.0) * swell
    place(out, chord, 0.0, 0.55 / (np.max(np.abs(chord)) + 1e-9))
    # the glint: the white-yellow orbs - high C partials (n = 32 40 48) twinkling at 9 Hz as the swell crests
    glint = np.zeros(N)
    for n, a in ((32, 1.0), (40, 0.7), (48, 0.45)):
        glint += a * np.sin(2 * np.pi * F0 * n * t + 2 * np.pi * rng.random())
    glint *= (0.6 + 0.4 * np.sin(2 * np.pi * 9.0 * t)) * np.clip((t - 0.3) / 0.25, 0, 1) * np.exp(-np.maximum(0.0, t - 0.6) / 0.22)
    place(out, glint, 0.0, 0.12 / (np.max(np.abs(glint)) + 1e-9))
    # a reversed ElevenLabs discharge rising into the crest, quiet: the electric swell under the gold
    cz = ctx.take('charge_zap', 1)
    nr = int(0.5 * SR)
    seg = cz[-nr:] if len(cz) >= nr else np.concatenate([np.zeros(nr - len(cz)), cz])
    seg = hp(seg, 600.0) * np.linspace(0, 1, nr) ** 2
    place(out, seg, 0.05, 0.16 / (np.max(np.abs(seg)) + 1e-9))
    # the sparkle (ElevenLabs) from 0.18 s, above 2 kHz
    sp = lp(hp(ctx.take('sparkle'), 2000.0), 11000.0)
    sp = fades1(sp[:int(1.0 * SR)], 0.02, 0.3)
    place(out, sp, 0.18, 0.5 / (np.max(np.abs(sp)) + 1e-9))
    # the DG-2 tesla zap, tuned from its 144.5 Hz to C3 (130 Hz), landing on the crest
    zb = resample(ctx.dg['bounce1'], 130.0 / 144.5)        # played 0.9x: down from its 144.5 Hz to C3
    zb = fades1(hp(trim(zb), 90.0)[:int(0.6 * SR)], 0.002, 0.2)
    place(out, zb, 0.5, 0.5 / (np.max(np.abs(zb)) + 1e-9))
    out = hp(out, 40.0)
    return fades1(out, 0.002, 0.15)


def render_expire(ctx):
    N = int(1.06 * SR)
    out = np.zeros(N)
    t = np.arange(N) / SR
    rng = np.random.default_rng(91)
    # the flicker: a seeded on/off gate (5..22 ms segments) whose gaps grow longer and more frequent as it dies
    gate = np.ones(N)
    i = int(0.12 * SR)
    while i < N:
        u = i / N
        seg = int(rng.uniform(0.005, 0.022) * SR)
        if rng.random() < 0.15 + 0.6 * u:
            gate[i:i + seg] = rng.uniform(0.0, 0.25)
        i += seg
    from scipy.ndimage import uniform_filter1d
    gate = uniform_filter1d(gate, size=int(0.002 * SR))
    env = np.minimum(1.0, t / 0.01) * np.exp(-t / 0.45) * gate
    wh = beam_stack(N, L=None, stereo=False, seed=92, fmax=1950.0, chorus=0.3, glide=exp_glide(N, 1.0, 0.5, 1.4), amp_env=env, swirl=1.5)
    place(out, wh, 0.0, 0.75 / (np.max(np.abs(wh)) + 1e-9))
    sp = ctx.take('dying_sputter')
    sp = sp[:int(1.0 * SR)] * np.exp(-np.arange(min(len(sp), int(1.0 * SR))) / SR / 0.5)   # it dies WITH the beam
    sp = fades1(lp(sp, 10000.0), 0.005, 0.25)
    place(out, sp, 0.0, 0.6 / (np.max(np.abs(sp)) + 1e-9))
    fx = hp(ctx.dg['flux'][int(0.6 * SR):int(1.5 * SR)], 2000.0) * np.exp(-np.arange(int(0.9 * SR)) / SR / 0.3)
    place(out, fx, 0.05, 0.22 / (np.max(np.abs(fx)) + 1e-9))
    tk = lp(ctx.dg['impact'][:int(0.12 * SR)], 300.0)
    tk = fades1(tk, 0.001, 0.08)
    place(out, tk, 0.86, 0.22 / (np.max(np.abs(tk)) + 1e-9))
    out = hp(out, 30.0)
    return fades1(out, 0.003, 0.08)


def render_idle(ctx):
    """the DG-2 idle (1.54 s, itself a near-loop) tiled twice round with cross-faded joins and made circular at 3.0 s,
    warmed (a gentle top cut, a little low shelf), with a quiet thread of the beam's low harmonics swirling inside"""
    L = CUES['tod_ws_idle_loop']['loop']
    N = int(round(L * SR))
    raw = norm(hp(ctx.dg['idle'], 22.0), 0.1)
    x = make_loop(raw, L, 0.25, start=0.11)[:, 0]
    warm = lp(x, 2500.0, order=1, loop=True)
    warm = bell(warm, 200.0, 3.0, 1.2, loop=True)            # its 195 Hz partial lifted: the hum reads on small speakers
    thread = beam_stack(N, L=L, stereo=False, seed=101, fmin=130.0, fmax=650.0, chorus=0.3, sub=0, swirl=snap(0.67, L), swirl_depth=0.5)
    mix = norm(warm, 0.1) + norm(thread, 0.1) * 0.22
    mix = tanh_sat(mix / (np.max(np.abs(mix)) + 1e-9) * 0.8, 1.3)
    return hp(mix, 25.0, loop=True)


RENDER = {
    'tod_ws_fire_start_plr': lambda c, v: render_fire_start(c, True),
    'tod_ws_fire_start_npc': lambda c, v: render_fire_start(c, False),
    'tod_ws_fire_loop_plr': lambda c, v: render_fire_loop(c, True),
    'tod_ws_fire_loop_npc': lambda c, v: render_fire_loop(c, False),
    'tod_ws_fire_stop_plr': lambda c, v: render_fire_stop(c, True),
    'tod_ws_fire_stop_npc': lambda c, v: render_fire_stop(c, False),
    'tod_ws_impact_loop': lambda c, v: render_impact_loop(c),
    'tod_ws_hit': render_hit,
    'tod_ws_kill': render_kill,
    'tod_ws_raise': lambda c, v: render_raise(c),
    'tod_ws_putaway': lambda c, v: render_putaway(c),
    'tod_ws_grab': lambda c, v: render_grab(c),
    'tod_ws_expire': lambda c, v: render_expire(c),
    'tod_ws_idle_loop': lambda c, v: render_idle(c),
}


def is_loop(alias):
    return CUES[alias]['row']['Looping'] == 'looping'


def seam_stats(x):
    """the listen-proxy for a loop seam, in the gate's own terms (loop_seam_fault): the 30 ms level step across the wrap
    against the largest step between neighbouring windows inside the loop, the sample jump at the wrap against the
    largest sample step inside it, and the wrap's percentile among every sample step (a seamless wrap is ordinary)"""
    m = mono(as2d(x))
    w = int(0.03 * SR)
    k = len(m) // w
    lv = db(np.sqrt((m[:k * w].reshape(k, w) ** 2).mean(axis=1)))
    d = np.abs(np.diff(m))
    jump = abs(m[0] - m[-1])
    return dict(level_step_db=round(float(abs(lv[0] - db(rms(m[-w:])))), 2), level_step_inside_max_db=round(float(np.max(np.abs(np.diff(lv)))), 2),
                jump=round(float(jump), 4), jump_inside_max=round(float(d.max()), 4),
                jump_percentile=round(float(np.mean(d < jump) * 100.0), 1))


def fit(x, keep):
    """a one-shot inside its window: one that rings past the end is faded at the edge, one that is short is padded"""
    lo, hi = keep
    n_hi, n_lo = int((hi - 0.004) * SR), int((lo + 0.004) * SR)
    if x.shape[0] > n_hi:
        x = fades1(x[:n_hi], 0.0, 0.08)
    if x.shape[0] < n_lo:
        pad = np.zeros((n_lo - x.shape[0],) + x.shape[1:])
        x = np.concatenate([x, pad])
    return x


def render_all(data):
    """-> ({rel path under sound_assets: (bytes, info, alias)}, takes used)"""
    ctx = Ctx(data)
    res = {}
    for alias in ORDER:
        spec = CUES[alias]
        loop = is_loop(alias)
        for v in range(spec['variants']):
            stem = spec['stem'] + ('' if spec['variants'] == 1 else '_%d' % (v + 1))
            x = RENDER[alias](ctx, v)
            if loop:
                assert x.shape[0] == int(round(spec['loop'] * SR)), alias + ': the loop is not its exact length'
            else:
                x = fit(x - x.mean(axis=0), spec['keep'])
            metric_name, target, ref, why = spec['target']
            # a one-shot keeps its transient: at most 3 dB of limiting, and a cue that cannot get there stops short
            y, info = level(x, metric_name, target, loop=loop, max_gr=(4.5 if loop else 3.0), radius_ms=(12.0 if loop else 8.0))
            y = as2d(y)
            y = y - y.mean(axis=0)                           # the limiter's gain dips can leave a hair of DC: none ships
            pk = float(np.max(np.abs(y)))
            if pk > 10 ** (info['ceiling_db'] / 20.0):
                y = y * (10 ** (info['ceiling_db'] / 20.0) / pk)
            if spec['ch'] == 1:
                y = y[:, :1] if y.shape[1] == 1 else mono(y)[:, None]
            b = encode(y)
            dec, _ = decode_wav_bytes(b)
            rel = '%s/%s.wav' % (WAV_DIR.split('/', 1)[1], stem)
            info.update(file=stem + '.wav', path=rel, sha256=sha256(b), bytes=len(b), channels=dec.shape[1], frames=dec.shape[0],
                        secs=round(dec.shape[0] / SR, 4), lufs=round(lufs(dec, loop), 2), k300=round(k300(dec, loop), 2),
                        peak_db=round(peak_db(dec), 2), true_peak_db=round(true_peak_db(dec, loop), 2),
                        dc=round(float(np.abs(dec.mean(axis=0)).max()), 6), st_var_db=round(st_var(dec, loop), 2) if loop else None,
                        reference=ref, why=why)
            info['reached'] = info['lufs'] if metric_name == 'lufs' else info['k300']   # measured on the shipped file
            info['short_of_target'] = round(target - info['reached'], 2) if target - info['reached'] > 0.03 else 0.0
            if loop:
                info['seam'] = seam_stats(dec)
            if dec.shape[1] == 2:
                info['lr_corr'] = round(float(np.corrcoef(dec[:, 0], dec[:, 1])[0, 1]), 3)
                info['mono_fold_db'] = round(lufs(mono(dec), loop) - lufs(dec, loop), 2)
            res[rel] = (b, info, alias)
    return res, ctx.used


# ======================================================================================================================
# THE TABLE
# ======================================================================================================================
def comment_row(text):
    assert ',' not in text and '"' not in text and '\n' not in text, text
    return text + ',' * (len(HEADER) - 1)


def csv_rows(files_by_alias):
    """the generated table's lines (header first); files_by_alias = {alias: [wav file names]}"""
    lines = [','.join(HEADER),
             comment_row('# THE WUNDERSTRAHL (docs/219) - GENERATED by tools/wunderstrahl/sound/make_sounds.py - never hand-edit; '
                         'no row carries a sound context and no fire row is Pauseable')]
    col = {h: i for i, h in enumerate(HEADER)}
    for alias in ORDER:
        spec = CUES[alias]
        if spec['row']['Looping'] == 'looping':
            assert spec.get('owner'), alias + ': a looping row needs an owner'
            lines.append(comment_row('# OWNER %s: %s' % (alias, spec['owner'].replace(',', ' -'))))
        for f in files_by_alias.get(alias, []):
            r = [''] * len(HEADER)
            for k, v in spec['row'].items():
                r[col[k]] = v
            r[col['Name']] = alias
            r[col['FileSpec']] = FILESPEC_DIR + f
            if spec['variants'] > 1:
                r[col['RandomizeType']] = 'variant'
            assert not any(c in v for v in r for c in ',"\r\n'), alias + ': a field would need csv quoting'
            lines.append(','.join(r))
    return lines


def csv_text(files_by_alias):
    return '\n'.join(csv_rows(files_by_alias)) + '\n'


def files_from_manifest(man):
    return {a: [f['file'] for f in man['cues'].get(a, {}).get('files', [])] for a in ORDER}


# ======================================================================================================================
# THE REFERENCES (re-measured when present; the frozen REFS figures are what the targets were set from)
# ======================================================================================================================
def ref_path(src):
    kind, rel = src.split(':', 1)
    if kind == 'repo':
        return os.path.join(REPO, rel)
    return os.path.join(REF_CACHE, '_x', T7_PREFIX, 'sound_assets', rel.replace('/', os.sep))


def extract_refs():
    todo = [k for k, r in REFS.items() if r['src'].startswith('t7:') and not os.path.exists(ref_path(r['src']))]
    if not todo:
        return []
    if not (os.path.exists(T7_ARCHIVE) and os.path.exists(SEVEN_ZIP)):
        return todo
    members = [T7_PREFIX + '\\sound_assets\\' + REFS[k]['src'].split(':', 1)[1].replace('/', '\\') for k in todo]
    os.makedirs(os.path.join(REF_CACHE, '_x'), exist_ok=True)
    subprocess.run([SEVEN_ZIP, 'x', '-y', '-o' + os.path.join(REF_CACHE, '_x'), T7_ARCHIVE] + members, capture_output=True, text=True)
    return [k for k in todo if not os.path.exists(ref_path(REFS[k]['src']))]


def measure_refs():
    missing = extract_refs()
    out = {}
    for k, r in REFS.items():
        p = ref_path(r['src'])
        if not os.path.exists(p):
            out[k] = dict(r, measured=None)
            continue
        y = read_wav(p)
        m = dict(lufs=round(lufs(y), 2), k300=round(k300(y), 2), k300_mono=round(k300(mono(y)), 2), lufs_mono=round(lufs(mono(y)), 2),
                 sha256=sha256(open(p, 'rb').read()))
        drift = max(abs(m[key] - r[key]) for key in ('lufs', 'k300', 'k300_mono', 'lufs_mono') if key in r)
        out[k] = dict(r, measured=m, drift_db=round(drift, 2))
    return out, missing


# ======================================================================================================================
# BUILD / CHECK / SELFTEST / VERIFY / REVIEW
# ======================================================================================================================
def build(out_root, offline=False):
    hdr = open(os.path.join(REPO, 'sound', 'aliases', 'tod_ability.csv'), encoding='utf-8-sig').readline().rstrip('\r\n')
    assert hdr.split(',') == HEADER, 'the alias header moved (sound/aliases/tod_ability.csv)'
    missing_src = [k for k, rel in DG2.items() if not os.path.exists(os.path.join(DG2_ROOT, rel))]
    if missing_src:
        sys.exit('WUNDERSTRAHL SOUNDS: the DG-2 originals are missing (%s) under %s' % (', '.join(missing_src), DG2_ROOT))
    data, calls = ensure_takes(offline)
    print('takes: %d layers, %d new API calls' % (len(LAYER_ORDER), calls))
    res, used = render_all(data)
    wdir = os.path.join(out_root, WAV_DIR)
    os.makedirs(wdir, exist_ok=True)
    for rel, (b, info, alias) in res.items():
        p = os.path.join(out_root, 'sound_assets', rel)
        if not os.path.exists(p) or open(p, 'rb').read() != b:
            open(p, 'wb').write(b)
    for f in sorted(os.listdir(wdir)):                       # this tool owns the folder: no stray wav survives
        if 'tod/wunderstrahl/' + f not in res:
            os.remove(os.path.join(wdir, f))
            print('removed stray', f)
    cues = {}
    for rel, (b, info, alias) in res.items():
        cues.setdefault(alias, dict(alias=alias, what=CUES[alias]['what'], channels=CUES[alias]['ch'], looping=is_loop(alias),
                                    pan=CUES[alias]['row']['PanType'], vol=int(CUES[alias]['row']['VolMin']),
                                    owner=CUES[alias].get('owner'), files=[]))['files'].append(info)
    fba = {a: [f['file'] for f in cues[a]['files']] for a in ORDER}
    text = csv_text(fba)
    cp = os.path.join(out_root, CSV_REL)
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    if not os.path.exists(cp) or open(cp, 'rb').read() != text.encode('utf-8'):
        open(cp, 'wb').write(text.encode('utf-8'))
    refs, ref_missing = measure_refs()
    srcs = {k: dict(path='tmp/wunderstrahl/src/T7 Assets V2.8/sound_assets/' + rel,
                    sha256=sha256(open(os.path.join(DG2_ROOT, rel), 'rb').read())) for k, rel in DG2.items()}
    man = dict(tool='tools/wunderstrahl/sound/make_sounds.py',
               about='GENERATED - never hand-edit. The Wunderstrahl sound set (docs/219): every staged wav with its sha256, '
                     'format, measured loudness and what it was levelled against; the alias table sha; the DG-2 originals and '
                     'the ElevenLabs takes it was rendered from. --check pins the staged files to this.',
               csv=dict(path=CSV_REL, sha256=sha256(text.encode('utf-8')), rows=sum(len(v) for v in fba.values())),
               szc_entry=SZC_ENTRY, cues={a: cues[a] for a in ORDER}, sources=dict(dg2=srcs, takes=used),
               refs={k: dict(what=v['what'], vol=v['vol'], src=v['src'], lufs=v['lufs'], k300=v['k300'],
                             measured=v.get('measured'), drift_db=v.get('drift_db')) for k, v in refs.items()},
               ref_missing=ref_missing)
    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(man, fh, indent=1)
        fh.write('\n')
    for a in ORDER:
        for f in cues[a]['files']:
            s = f.get('seam')
            print('%-28s %dch %5.2fs  lufs %6.2f  k300 %6.2f  peak %5.2f  tp %5.2f  lim %5.2f  %s%s' % (
                f['file'], f['channels'], f['secs'], f['lufs'], f['k300'], f['peak_db'], f['true_peak_db'], f['limit_db'],
                ('short %.2f ' % f['short_of_target']) if f['short_of_target'] else '',
                ('seam: level step %.2f dB (inside max %.2f), jump %.4f (inside max %.4f, %.0fth pct)' % (
                    s['level_step_db'], s['level_step_inside_max_db'], s['jump'], s['jump_inside_max'], s['jump_percentile'])) if s else ''))
    drift = [k for k, v in refs.items() if v.get('drift_db') and v['drift_db'] > 0.1]
    if drift:
        print('WARNING: references re-measured away from the frozen REFS figures: %s' % drift)
    print('wrote %d wavs + %s (%d rows) under %s; manifest %s' % (len(res), CSV_REL, man['csv']['rows'], out_root,
                                                                  os.path.relpath(MANIFEST, REPO)))
    return man


def check(out_root, man=None):
    """the gate: no API, no DSP. -> [failures]"""
    bad = []
    if man is None:
        if not os.path.exists(MANIFEST):
            return ['no manifest (%s) - %s' % (os.path.relpath(MANIFEST, REPO), FIX)]
        man = json.load(open(MANIFEST, encoding='utf-8'))
    cues = man.get('cues', {})
    if set(cues) != set(ORDER):
        bad.append('the manifest ships %s, the tool defines %s' % (sorted(cues), sorted(ORDER)))
    have = set()
    for alias in ORDER:
        spec = CUES[alias]
        files = cues.get(alias, {}).get('files', [])
        if len(files) != spec['variants']:
            bad.append('%s ships %d files, wants %d' % (alias, len(files), spec['variants']))
        lo, hi = spec['keep']
        for f in files:
            have.add(f['file'])
            p = os.path.join(out_root, WAV_DIR, f['file'])
            if not os.path.exists(p):
                bad.append('missing %s/%s' % (WAV_DIR, f['file']))
                continue
            b = open(p, 'rb').read()
            if sha256(b) != f.get('sha256'):
                bad.append('changed %s (sha256 differs from the manifest)' % f['file'])
            try:
                x, (ch, sr, sw, n) = decode_wav_bytes(b)
            except (wave.Error, EOFError) as e:
                bad.append('%s unreadable: %s' % (f['file'], e))
                continue
            if (ch, sr, sw) != (spec['ch'], SR, 2):
                bad.append('%s format is %d ch / %d Hz / %d-bit, wants %d ch / 48000 Hz / 16-bit' % (f['file'], ch, sr, sw * 8, spec['ch']))
            secs = n / float(SR)
            if not lo - 0.005 <= secs <= hi + 0.005:
                bad.append('%s is %.3f s, outside %.2f..%.2f' % (f['file'], secs, lo, hi))
            if x is not None and x.size:
                pk = float(db(np.max(np.abs(x))))
                if pk > CEIL_DB + 0.01:
                    bad.append('%s peaks at %.2f dBFS, over the %.1f dBFS ceiling' % (f['file'], pk, CEIL_DB))
                if is_loop(alias):
                    why = loop_seam_fault(x)
                    if why:
                        bad.append('%s does not loop: %s' % (f['file'], why))
    wdir = os.path.join(out_root, WAV_DIR)
    if os.path.isdir(wdir):
        for fn in sorted(os.listdir(wdir)):
            if fn not in have:
                bad.append('stray %s/%s (no manifest row: dead weight in the bank or a hand edit)' % (WAV_DIR, fn))
    cp = os.path.join(out_root, CSV_REL)
    if not os.path.exists(cp):
        bad.append('%s missing' % CSV_REL)
    else:
        raw = open(cp, 'rb').read()
        want = csv_text(files_from_manifest(man)).encode('utf-8')
        if raw != want:
            bad.append('%s differs from the generated table (a hand edit or a stale table)' % CSV_REL)
        bad += check_rows(raw.decode('utf-8', errors='replace'), out_root, have)
    szc = os.path.join(out_root, SZC_REL)
    if os.path.exists(szc):
        try:
            s = json.load(open(szc, encoding='utf-8-sig'))
            n = sum(1 for e in s.get('Sources', []) if e.get('Type') == 'ALIAS' and e.get('Filename') == SZC_ENTRY['Filename'])
            if n != 1:
                bad.append('the sound zone config loads tod_wunderstrahl.csv %d times (want 1: %s in %s)' % (n, json.dumps(SZC_ENTRY), SZC_REL))
        except (OSError, ValueError) as e:
            bad.append('szc unreadable: %s' % e)
    return bad


def loop_seam_fault(x):
    """a seamless loop's wrap is just another point inside it: the 30 ms level step across the wrap may not exceed the
    largest step between neighbouring 30 ms windows inside the loop (+1 dB), and the sample jump at the wrap may not
    exceed 1.5x the largest sample step inside it. -> '' or why not (no DSP: reads samples)"""
    m = x.mean(axis=1)
    w = int(0.03 * SR)
    k = len(m) // w
    if k < 4:
        return 'shorter than four 30 ms windows'
    lv = 20 * np.log10(np.sqrt((m[:k * w].reshape(k, w) ** 2).mean(axis=1)) + 1e-9)
    inner = float(np.max(np.abs(np.diff(lv))))
    last = 20 * np.log10(np.sqrt(np.mean(m[-w:] ** 2)) + 1e-9)
    seam = abs(lv[0] - last)
    if seam > inner + 1.0:
        return 'its level steps %.1f dB across the wrap, its largest step inside is %.1f dB' % (seam, inner)
    d = np.abs(np.diff(m))
    jump = abs(m[0] - m[-1])
    if jump > 1.5 * float(d.max()) + 1e-4:
        return 'the wrap jumps %.4f, its largest sample step inside is %.4f' % (jump, float(d.max()))
    return ''


def check_rows(text, out_root, have):
    """the table's structure: header verbatim, 102 columns a row, known names, the row contract, an OWNER note above every
    looping row, every FileSpec a staged wav"""
    bad = []
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]
    if not lines or lines[0].split(',') != HEADER:
        bad.append('%s header is not the 102-column alias header' % CSV_REL)
        return bad
    col = {h: i for i, h in enumerate(HEADER)}
    owners = set()
    seen = {}
    for i, ln in enumerate(lines[1:], start=2):
        if '\r' in ln:
            bad.append('%s line %d carries a CR (the table is LF)' % (CSV_REL, i))
            ln = ln.replace('\r', '')
        c = next(csv.reader([ln])) if ln else ['']
        if ln.startswith('#'):
            if ln.startswith('# OWNER '):
                owners.add(ln[len('# OWNER '):].split(':', 1)[0].strip())
            continue
        if len(c) != len(HEADER):
            bad.append('%s line %d has %d columns (want %d)' % (CSV_REL, i, len(c), len(HEADER)))
            continue
        r = dict(zip(HEADER, c))
        name = r['Name']
        if name not in CUES:
            bad.append('%s line %d defines %s, which this tool does not own' % (CSV_REL, i, name))
            continue
        seen.setdefault(name, []).append(r)
        for k in CONTEXT_COLS:
            if r[k].strip():
                bad.append('%s line %d %s carries %s=%s (this map sets no sound context: silent)' % (CSV_REL, i, name, k, r[k]))
        if r['Pauseable'].strip().lower() not in ('', 'no'):
            bad.append('%s line %d %s is Pauseable=%s (fire / weapon cues never pause: a held shot replays on resume)' % (CSV_REL, i, name, r['Pauseable']))
        pan, loop = r['PanType'].lower(), r['Looping'].lower()
        if pan not in ('2d', '3d') or loop not in ('looping', 'nonlooping'):
            bad.append('%s line %d %s has PanType=%s Looping=%s' % (CSV_REL, i, name, r['PanType'], r['Looping']))
        if (pan, loop) != (CUES[name]['row']['PanType'], CUES[name]['row']['Looping']):
            bad.append('%s line %d %s is %s %s, the cue is %s %s' % (CSV_REL, i, name, pan, loop, CUES[name]['row']['PanType'], CUES[name]['row']['Looping']))
        if loop == 'looping' and name not in owners:
            bad.append('%s line %d: LOOPING %s row %s has no "# OWNER %s:" note above it (a loop nobody starts and stops)' % (
                CSV_REL, i, pan.upper(), name, name))
        fs = r['FileSpec']
        if not fs.startswith(FILESPEC_DIR) or fs[len(FILESPEC_DIR):] not in have:
            bad.append('%s line %d %s points at %s, which is not a staged wav' % (CSV_REL, i, name, fs))
        for k in ('VolMin', 'VolMax'):
            try:
                v = float(r[k])
                if not 0 < v <= 100:
                    raise ValueError
            except ValueError:
                bad.append('%s line %d %s %s=%r' % (CSV_REL, i, name, k, r[k]))
        if r['StopAlias'] and r['StopAlias'] not in CUES:
            bad.append('%s line %d %s StopAlias %s is not a Wunderstrahl alias' % (CSV_REL, i, name, r['StopAlias']))
    for a in ORDER:
        if a not in seen:
            bad.append('%s has no row for %s' % (CSV_REL, a))
    return bad


def _plant_peak(d):
    p = os.path.join(d, WAV_DIR, 'tod_ws_hit_1.wav')
    b = bytearray(open(p, 'rb').read())
    with wave.open(io.BytesIO(bytes(b))) as w:
        hdr = len(b) - w.getnframes() * w.getnchannels() * 2
    b[hdr + 200:hdr + 202] = (32700).to_bytes(2, 'little', signed=True)    # one sample at -0.02 dBFS
    open(p, 'wb').write(bytes(b))


def _sed(path, old, new):
    t = open(path, encoding='utf-8', newline='').read()
    if old not in t:
        raise AssertionError('selftest plant: %r not in %s' % (old[:70], path))
    open(path, 'w', encoding='utf-8', newline='').write(t.replace(old, new, 1))


def _set_field(path, alias, field, value):
    """rewrite one column of the first row of `alias` (a hand edit, as a person would make it)"""
    lines = open(path, encoding='utf-8', newline='').read().split('\n')
    i = next(k for k, l in enumerate(lines) if l.startswith(alias + ','))
    c = lines[i].split(',')
    c[HEADER.index(field)] = value
    lines[i] = ','.join(c)
    open(path, 'w', encoding='utf-8', newline='').write('\n'.join(lines))


def selftest(src_root):
    man = json.load(open(MANIFEST, encoding='utf-8'))
    csvp = lambda d: os.path.join(d, CSV_REL)
    owner_line = next(l for l in csv_rows(files_from_manifest(man)) if l.startswith('# OWNER tod_ws_fire_loop_plr:'))
    cases = [
        ('clean', None, None),
        ('a missing wav', lambda d: os.remove(os.path.join(d, WAV_DIR, 'tod_ws_kill_2.wav')), 'missing'),
        ('a bad csv row', lambda d: open(csvp(d), 'a', encoding='utf-8', newline='').write('tod_ws_bogus,,loaded,tod\\wunderstrahl\\x.wav\n'), 'columns'),
        ('a looping 2D alias without an owner note', lambda d: _sed(csvp(d), owner_line + '\n', ''), 'no "# OWNER tod_ws_fire_loop_plr:"'),
        ('a peak above the ceiling', _plant_peak, 'over the -1.0 dBFS ceiling'),
        ('a changed wav', lambda d: open(os.path.join(d, WAV_DIR, 'tod_ws_grab.wav'), 'r+b').write(b'RIFX'), 'changed'),
        ('a stray wav', lambda d: shutil.copy(os.path.join(d, WAV_DIR, 'tod_ws_raise.wav'), os.path.join(d, WAV_DIR, 'tod_ws_raise_old.wav')), 'stray'),
        ('a context-gated row', lambda d: (_set_field(csvp(d), 'tod_ws_hit', 'ContextType', 'water'),
                                           _set_field(csvp(d), 'tod_ws_hit', 'ContextValue', 'over')), 'sound context'),
        ('a Pauseable fire row', lambda d: _set_field(csvp(d), 'tod_ws_fire_loop_plr', 'Pauseable', 'yes'), 'Pauseable'),
        ('a 3D cue made 2D', lambda d: _set_field(csvp(d), 'tod_ws_kill', 'PanType', '2d'), 'the cue is 3d'),
        ('a loop that does not loop', lambda d: _break_loop(os.path.join(d, WAV_DIR, 'tod_ws_impact_loop.wav')), 'does not loop'),
        ('a mono wav where stereo ships', lambda d: _to_mono(os.path.join(d, WAV_DIR, 'tod_ws_fire_loop_plr.wav')), 'format'),
    ]
    fails = 0
    for label, plant, expect in cases:
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(os.path.join(src_root, WAV_DIR), os.path.join(d, WAV_DIR))
            os.makedirs(os.path.dirname(csvp(d)), exist_ok=True)
            shutil.copy(os.path.join(src_root, CSV_REL), csvp(d))
            if plant:
                plant(d)
            bad = check(d, man)
            ok = (not bad) if expect is None else any(expect in b for b in bad)
            if not ok:
                fails += 1
                print('  SELFTEST FAIL [%s]: expected %s, got %s' % (label, expect or 'a pass', bad[:4]))
            else:
                print('  ok [%s]%s' % (label, '' if expect is None else ' -> ' + next(b for b in bad if expect in b)[:110]))
    print('WUNDERSTRAHL SOUNDS SELFTEST %s: %d cases' % ('OK' if not fails else 'FAILED', len(cases)))
    return fails == 0


def _break_loop(p):
    """the classic broken loop: a one-shot render whose tail fades to silence before the wrap"""
    x, (ch, sr, sw, n) = decode_wav_bytes(open(p, 'rb').read())
    x = x.copy()
    k = int(0.12 * SR)
    x[-k:] *= np.linspace(1.0, 0.0, k)[:, None] ** 3
    open(p, 'wb').write(encode(x))


def _to_mono(p):
    x, _ = decode_wav_bytes(open(p, 'rb').read())
    open(p, 'wb').write(encode(x.mean(axis=1)))


def verify(out_root):
    data, _ = ensure_takes(offline=True)
    res, _ = render_all(data)
    bad = []
    for rel, (b, info, alias) in res.items():
        p = os.path.join(out_root, 'sound_assets', rel)
        if not os.path.exists(p) or open(p, 'rb').read() != b:
            bad.append('%s does not re-render byte for byte' % rel)
    return bad


def stt_check(out_root):
    """ElevenLabs speech-to-text (tools/black_market_vo/score_takes.stt, read-only) over every SHIPPED wav: a generated
    sizzle must not hide a word. Writes art/wunderstrahl/sound_review/stt.json (the review reports it). API, not a gate."""
    sys.path.insert(0, os.path.join(REPO, 'tools', 'black_market_vo'))
    import score_takes
    man = json.load(open(MANIFEST, encoding='utf-8'))
    res = {}
    for a in ORDER:
        for f in man['cues'][a]['files']:
            r = score_takes.stt(os.path.join(out_root, WAV_DIR, f['file']))
            toks = r.get('words', []) or []
            res[f['file']] = dict(sha256=f['sha256'], text=r.get('text', ''), words=[w['text'] for w in toks if w.get('type') == 'word'],
                                  events=[w['text'] for w in toks if w.get('type') == 'audio_event'])
            print('%-28s words %s  events %s' % (f['file'], res[f['file']]['words'] or '-', res[f['file']]['events'] or '-'))
    os.makedirs(REVIEW, exist_ok=True)
    with open(os.path.join(REVIEW, 'stt.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(dict(tool='tools/wunderstrahl/sound/make_sounds.py stt', model='scribe_v1', files=res), fh, indent=1)
        fh.write('\n')
    return res


def review(out_root):
    """art/wunderstrahl/sound_review/: the reel (every cue in order, each after a short silence; loops twice round; then a
    held-beam scene at approximate alias volumes) + levels.txt"""
    man = json.load(open(MANIFEST, encoding='utf-8'))
    os.makedirs(REVIEW, exist_ok=True)
    gap = int(0.6 * SR)
    parts, index, tcur = [], [], 0.0

    def add(x, label):
        nonlocal tcur
        x = as2d(x)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1)
        parts.append(np.zeros((gap, 2)))
        tcur += gap / SR
        index.append((round(tcur, 2), label))
        parts.append(x)
        tcur += x.shape[0] / SR

    wav = {}
    for a in ORDER:
        for f in man['cues'][a]['files']:
            x, _ = decode_wav_bytes(open(os.path.join(out_root, WAV_DIR, f['file']), 'rb').read())
            wav[f['file']] = x
            if is_loop(a):
                add(np.concatenate([x, x]), '%s (twice round: listen for the seam at +%.2f s)' % (f['file'], x.shape[0] / SR))
            else:
                add(x, f['file'])
    # THE SCENE: grab -> raise -> fire (start + loop with its 150 ms alias fade-in, the wall sizzle, hits and kills down
    # the beam) for 6 s -> release -> a quick tap -> expire. Alias volumes applied as 20*log10(vol/100) dB (approximate).
    vol = {a: int(CUES[a]['row']['VolMin']) for a in ORDER}
    g = lambda a: 10 ** (20 * np.log10(vol[a] / 100.0) / 20.0)
    S = np.zeros((int(13.5 * SR), 2))

    def put(x, at, a, gain=1.0):
        x = as2d(x)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1) * 0.7071
        place(S, x, at, g(a) * gain)

    t0, hold = 2.6, 6.0
    t1 = t0 + hold + 1.3
    put(wav['tod_ws_grab.wav'], 0.2, 'tod_ws_grab')
    put(wav['tod_ws_raise.wav'], 1.2, 'tod_ws_raise')
    idle = wav['tod_ws_idle_loop.wav']                      # the script's hum: from the raise to the putaway
    n_idle = int((t1 + 2.75 - 1.9) * SR)
    ix = np.concatenate([idle] * (n_idle // idle.shape[0] + 1))[:n_idle].copy()
    ix[:int(0.15 * SR)] *= np.linspace(0, 1, int(0.15 * SR))[:, None]
    ix[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))[:, None]
    put(ix, 1.9, 'tod_ws_idle_loop')
    put(wav['tod_ws_fire_start_plr.wav'], t0, 'tod_ws_fire_start_plr')
    lp_ = wav['tod_ws_fire_loop_plr.wav']
    n = int(hold * SR)
    loopx = np.concatenate([lp_] * (n // lp_.shape[0] + 1))[:n].copy()
    fi, fo = int(0.15 * SR), int(0.10 * SR)
    loopx[:fi] *= np.linspace(0, 1, fi)[:, None]
    loopx[-fo:] *= np.linspace(1, 0, fo)[:, None]
    put(loopx, t0, 'tod_ws_fire_loop_plr')
    im = wav['tod_ws_impact_loop.wav']
    imx = np.concatenate([im] * (n // im.shape[0] + 1))[:n - int(0.2 * SR)].copy()
    imx[:int(0.12 * SR)] *= np.linspace(0, 1, int(0.12 * SR))[:, None]
    imx[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))[:, None]
    put(imx, t0 + 0.1, 'tod_ws_impact_loop', 0.6)          # the wall ~600 units away: about -4.4 dB down its curve
    rng = np.random.default_rng(7)
    for k in range(14):
        put(wav['tod_ws_hit_%d.wav' % (1 + k % 3)], t0 + 0.4 + k * 0.37 + rng.uniform(0, 0.1), 'tod_ws_hit', 0.8)
    for k, tk in enumerate((1.1, 2.0, 2.15, 3.4, 4.6, 4.75, 5.5)):
        put(wav['tod_ws_kill_%d.wav' % (1 + k % 3)], t0 + tk, 'tod_ws_kill', 0.75)
    put(wav['tod_ws_fire_stop_plr.wav'], t0 + hold, 'tod_ws_fire_stop_plr')
    put(wav['tod_ws_fire_start_plr.wav'], t1, 'tod_ws_fire_start_plr')
    nn = int(0.4 * SR)
    lx = lp_[:nn].copy()
    lx[:fi] *= np.linspace(0, 1, fi)[:, None]
    lx[-fo:] *= np.linspace(1, 0, fo)[:, None]
    put(lx, t1, 'tod_ws_fire_loop_plr')
    put(wav['tod_ws_fire_stop_plr.wav'], t1 + 0.4, 'tod_ws_fire_stop_plr')
    put(wav['tod_ws_expire.wav'], t1 + 1.6, 'tod_ws_expire')
    put(wav['tod_ws_putaway.wav'], t1 + 2.75, 'tod_ws_putaway')
    pk = np.max(np.abs(S))
    scaled = 1.0
    if pk > 10 ** (CEIL_DB / 20.0):
        scaled = 10 ** (CEIL_DB / 20.0) / pk
        S *= scaled
    add(S, 'THE SCENE at alias volumes (approx.): grab 0.2 / raise 1.2 / fire %.1f-%.1f with hits, kills, wall sizzle / '
           'tap %.1f / expire %.1f / putaway %.1f%s' % (t0, t0 + hold, t1, t1 + 1.6, t1 + 2.75,
                                                       (' (scene scaled %.2f dB to stay under -1 dBFS)' % db(scaled)) if scaled < 1 else ''))
    parts.append(np.zeros((gap, 2)))
    reel = np.concatenate(parts)
    reel_path = os.path.join(REVIEW, 'wunderstrahl_sound_reel.wav')
    open(reel_path, 'wb').write(encode(reel))
    L = ['THE WUNDERSTRAHL - SOUND REVIEW (generated by tools/wunderstrahl/sound/make_sounds.py review)',
         '',
         'Every staged wav: length, BS.1770 integrated loudness (LUFS-I; channels summed), loudest 300 ms K-weighted window',
         '(K300), sample peak, 4x true peak, the limiter depth, and what it was levelled against. Each row plays at the alias',
         'volume of its stock analogue and its wav is levelled against that analogue\'s wav at the SAME volume, so the',
         'comparison does not depend on the engine\'s volume curve. "heard" = metric + 20*log10(vol/100): the repo\'s usual',
         'approximation, for comparing rows of DIFFERENT volumes only. The in-game mix is UNVERIFIED until a build and a playtest.',
         '']
    hdr = '%-26s %3s %3s %5s %7s %7s %7s %6s %6s %6s %6s  %s' % ('file', 'ch', 'vol', 'secs', 'pan', 'LUFS-I', 'K300', 'heard', 'peak', 'TP',
                                                                'limit', 'levelled against')
    L += [hdr, '-' * len(hdr)]
    for a in ORDER:
        c = man['cues'][a]
        for f in c['files']:
            ref = man['refs'].get(f['reference'], {})
            m = f['metric']
            rv = ref.get('lufs') if m == 'lufs' else ref.get('k300')
            heard = (f['lufs'] if m == 'lufs' else f['k300']) + 20 * np.log10(c['vol'] / 100.0)
            L.append('%-26s %3d %3d %5.2f %7s %7.2f %7.2f %6.2f %6.2f %6.2f %6.2f  %s %s %.2f (vol %s) -> target %.2f%s' % (
                f['file'], f['channels'], c['vol'], f['secs'], c['pan'] + ('/loop' if c['looping'] else ''), f['lufs'], f['k300'], heard,
                f['peak_db'], f['true_peak_db'], f['limit_db'], f['reference'], m.upper(), rv if rv is not None else float('nan'),
                ref.get('vol'), f['target'], (' (reached %.2f)' % f['reached']) if f.get('short_of_target') else ''))
    L += ['("heard" = the levelled metric - LUFS-I for loops, K300 for one-shots - plus 20*log10(vol/100))']
    L += ['', 'Why each target:']
    for a in ORDER:
        L.append('  %-24s %s' % (a, CUES[a]['target'][3]))
    L += ['', 'Loop seams (listen-proxy, the gate\'s own test): the 30 ms level step across the wrap vs the largest step between neighbouring',
          'windows inside the loop, and the sample jump at the wrap vs the largest sample step inside it (with its percentile among all',
          'steps: a seamless wrap is an ordinary step); stereo: L/R correlation and the loudness change folded to mono; DC offset:']
    for a in ORDER:
        for f in man['cues'][a]['files']:
            extra = []
            if f.get('seam'):
                s = f['seam']
                extra.append('wrap level step %.2f dB (inside max %.2f), wrap jump %.4f (inside max %.4f; %.0fth percentile)' % (
                    s['level_step_db'], s['level_step_inside_max_db'], s['jump'], s['jump_inside_max'], s['jump_percentile']))
            if f.get('st_var_db') is not None:
                extra.append('400 ms movement %.2f dB' % f['st_var_db'])
            if 'lr_corr' in f:
                extra.append('L/R corr %.2f, mono fold %+.2f dB' % (f['lr_corr'], f['mono_fold_db']))
            extra.append('DC %.6f' % f['dc'])
            L.append('  %-26s %s' % (f['file'], '; '.join(extra)))
    sp = os.path.join(REVIEW, 'stt.json')
    if os.path.exists(sp):
        st = json.load(open(sp, encoding='utf-8'))['files']
        cur = {f['file']: f['sha256'] for a in ORDER for f in man['cues'][a]['files']}
        stale = [k for k, v in cur.items() if st.get(k, {}).get('sha256') != v]
        worded = {k: v['words'] for k, v in st.items() if v.get('words') and k in cur}
        L += ['', 'Speech-to-text over every shipped wav (ElevenLabs scribe_v1, `make_sounds.py stt`): %s%s' % (
            ('no words in any file' if not worded else 'WORDS FOUND: %s' % json.dumps(worded)),
            ('' if not stale else ' - STALE for %s (re-run stt)' % ', '.join(sorted(stale))))]
    else:
        L += ['', 'Speech-to-text: not run for this render (python tools/wunderstrahl/sound/make_sounds.py stt).']
    L += ['', 'The references (measured from the files; "drift" = re-measured vs the frozen figure the targets came from):']
    for k, r in man['refs'].items():
        meas = r.get('measured')
        L.append('  %-20s vol %3s  LUFS-I %6.2f  K300 %6.2f  %s%s' % (k, r['vol'], r['lufs'], r['k300'], r['what'],
                                                                   ('  [drift %.2f dB]' % r['drift_db']) if meas else '  [file not on disk: frozen figure]'))
    L += ['', 'The reel (%s, %.1f s, 48 kHz 16-bit stereo; mono cues centred):' % (os.path.basename(reel_path), reel.shape[0] / SR)]
    for t, label in index:
        L.append('  %7.2f s  %s' % (t, label))
    L += ['', 'What each cue is made of:']
    for a in ORDER:
        L.append('  %-24s %s' % (a, CUES[a]['what']))
    open(os.path.join(REVIEW, 'levels.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    print('review: %s (%.1f s) + levels.txt' % (os.path.relpath(reel_path, REPO), reel.shape[0] / SR))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', nargs='?', default='')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--offline', action='store_true', help='never call the API (fail if a take is missing)')
    ap.add_argument('--out-root', default=REPO)
    a = ap.parse_args()
    out_root = os.path.abspath(a.out_root)
    if a.selftest:
        sys.exit(0 if selftest(out_root) else 1)
    if a.check or a.cmd == 'check':
        bad = check(out_root)
        if bad:
            for b in bad[:16]:
                print('  FAIL ' + b)
            print('WUNDERSTRAHL SOUNDS STALE (%d) - %s' % (len(bad), FIX))
            sys.exit(1)
        man = json.load(open(MANIFEST, encoding='utf-8'))
        n = sum(len(c['files']) for c in man['cues'].values())
        szc = os.path.exists(os.path.join(out_root, SZC_REL))
        print('WUNDERSTRAHL SOUNDS OK: %d aliases, %d wavs, %s %d rows%s' % (
            len(man['cues']), n, CSV_REL, man['csv']['rows'],
            '' if szc else '  (NOTE: no sound zone config under this root - the lander adds %s)' % json.dumps(SZC_ENTRY)))
        return
    if a.cmd == 'build':
        build(out_root, a.offline)
        review(out_root)
        return
    if a.cmd == 'verify':
        bad = verify(out_root)
        for b in bad:
            print('  FAIL ' + b)
        print('WUNDERSTRAHL SOUNDS RENDER %s' % ('OK: every wav re-renders byte for byte' if not bad else 'DIFFERS (%d)' % len(bad)))
        sys.exit(1 if bad else 0)
    if a.cmd == 'review':
        review(out_root)
        return
    if a.cmd == 'stt':
        stt_check(out_root)
        review(out_root)
        return
    ap.print_help()


if __name__ == '__main__':
    main()
