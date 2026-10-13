"""WAVE-2 SOUNDS (2026-10-05): one owner for the sounds of six asset packs.

  PK17  the class TIER PROMOTION sting (tod_tier_sting) + the eight NEAR MISS / HOT STREAK cues, authored, replacing
        tools/near_miss/make_sounds.py's synthesised placeholders BY NAME (same files, same rows, exact lengths: that
        tool keeps its rows and its --check, and reads tools/near_miss/authored.json, which this tool writes)
  PK22  the companions: the destruction burst (3D + the owner's 2D cue) and the Talon / R.A.P.S. / Cerberus
        movement loops (_tod_partners.gsc)
  PK23  the world: the tower WIND bed + gusts and the far CITY bed (2D, client, by altitude), the UNDERCITY and
        PLAZA room tones + drips and pipe knocks (3D, client, generated anchors), the Black Market hut's neon hum,
        the teleporter pads' idle / recharge hums, and the POWER (the terminal boot, the 12 s wave, the grid online)
  PK27  the Necromancer's weapon foley: putaway / 3P first raise for the skull and both staffs, the staffs' melee
        table (tod_necro_staff_sounds: whoosh / hit / surface) and the skull's idle scream (stock wavs)
  PK28  the R1 Shadowhunter's bolt impacts: surface / flesh / headshot / metal (the tod_crossbow_bolt_impact table)
(PK18's five class-kit cues ride tools/ability_fx/make_sounds.py, which owns tod_ability.csv.)

ONE PIPELINE (the ability_fx / card_luck pattern): ElevenLabs sound generation (eleven_text_to_sound_v2, pcm_48000:
16-bit stereo 48 kHz, no codec) takes per PLAN row, every take measured and scored against its cue's PROFILE, the best
take(s) fitted (trimmed, exact length or span, faded, DC-blocked), seamless-looped where the cue is a loop (equal-power
crossfade of the overhang over the head, the seam measured), and levelled to the cue's BS.1770 target under a
look-ahead limiter. A few cues are DESIGNS: a take layered with parts written for the moment (the terminal boot's
three blips land on its three RESTART GRID frames; the power wave recedes down the tower and its relays fall away;
the hums carry a mains-locked harmonic core). Every shipped file and table is sha-pinned in sounds_manifest.json.

  python tools/sfx/w2c_sounds/make_sounds.py adopt                        copy the PK17 pack's earlier takes in (once)
  python tools/sfx/w2c_sounds/make_sounds.py generate [--cue C] [--takes N]   ElevenLabs takes (the PLAN rows not yet taken)
  python tools/sfx/w2c_sounds/make_sounds.py rescore  [--cue C]
  python tools/sfx/w2c_sounds/make_sounds.py pick     [--cue C] [--out-root DIR]   render + write wavs, tables, GDTs, manifest
  python tools/sfx/w2c_sounds/make_sounds.py review   [--out-root DIR]    spectrogram sheet (OLD vs NEW) + listening desk
  python tools/sfx/w2c_sounds/make_sounds.py --check  [--root DIR]        THE BUILD GATE (no API, no DSP)

The gate: every manifest wav present with its sha, format and length; the five alias tables and two GDTs exactly as
this tool writes them; tools/near_miss/authored.json naming the eight near shas; each table in the sound zone config;
the generated ambience anchors (gen_amb_data.py) and the bolt-impact effects (gen_fx.py) current; and every alias the
feature is FOR played by its script. The key is ELEVENLABS_API_KEY (tools/black_market_vo/eleven.py; never printed).
"""
import argparse, csv, io, json, os, re, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "tools", "black_market_vo"))
import dsp
from dsp import SR

WORK = os.path.join(REPO, "tmp", "wave2", "W2C-sounds", "takes")
TAKES_JSON = os.path.join(WORK, "takes.json")
PICKS_JSON = os.path.join(WORK, "picks.json")      # the user's overrides: {"cue": ["take_3", "take_1"]}
PK17_OLD = os.path.join(REPO, "tmp", "asset_prod", "PK17-card-luck-stings", "takes")
MANIFEST_REL = "tools/sfx/w2c_sounds/sounds_manifest.json"
AUTHORED_REL = "tools/near_miss/authored.json"
SZC_REL = "sound/zoneconfig/zm_tod2_cybercity.szc"
HEADER_FROM = "sound/aliases/tod_ui.csv"
MODEL = "eleven_text_to_sound_v2"
PROMPT_INFLUENCE = 0.6
FIX = "run: python tools/sfx/w2c_sounds/make_sounds.py pick"

NM = ", no music, no voice"

# ================================================================================================================
# THE CUES
#   dir      sound_assets/tod/<dir>/ ; stem = the file stem (variants: <stem>_<k>.wav, k >= 2; the first has no suffix)
#   ch       1 mono / 2 stereo          kind  oneshot | loop | design
#   secs     the EXACT shipped length (None = the take's own, clamped into span)
#   lufs / peak   the level (BS.1770) and the limiter ceiling (dBFS)
#   profile  the scoring shape          variants  how many files ship (the rows randomise between them)
#   plan     the takes: dict(prompt, ask[, loop][, reverse]); take_N is generated from plan[(N-1) % len(plan)]
#   rows     the alias rows: (alias, row kind, params); a row per shipped file
# ================================================================================================================
CUES = {}


def cue(name, **kw):
    kw.setdefault("variants", 1)
    kw.setdefault("ch", 1)
    kw.setdefault("secs", None)
    kw.setdefault("span", None)
    kw.setdefault("peak", -1.0)
    kw.setdefault("fade_out", 0.08)
    kw.setdefault("rows", [])
    kw.setdefault("plan", [])
    kw.setdefault("stem", name)
    CUES[name] = kw


# ---- PK17: the tier sting + the near-miss / hot-streak eight (prompts = the PK17 pack's, 2026-10-04) -------------
cue("tod_tier_sting", pack="PK17", table="tod_stings.csv", dir="sfx", ch=2, kind="design", span=(1.5, 2.5),
    lufs=-8.6, peak=-1.0, profile="tier", fade_out=0.35,
    plan=[dict(ask=2.2, prompt="a heavy sci-fi weapon class promotion: a massive metallic mechanical lock-in clunk, then a rising electric "
                                "power surge that swells upward and slams into a deep booming sub bass drop with a glittering electric tail, "
                                "cinematic cyberpunk game rank up sting, no music, no voice"),
          dict(ask=1.0, role="lock-in", prompt="a single heavy mechanical lock-in: a massive steel bolt slamming home into its lock with a deep "
                                               "metallic clunk and a short bright metal ring, close and dry, one hit only, no music"),
          dict(ask=1.6, role="swell (reversed)", reverse=True,
               prompt="a powerful electric energy discharge: a bright crackling burst of electricity with arcing sparks "
                      "and a deep hum that decays away into a shimmering electric tail, sci-fi, no music")],
    rows=[("tod_tier_sting", "ui2d", dict(vol=95))])

NEAR = [  # name, secs, lufs (tools/near_miss/make_sounds.py SOUNDS targets), fit, fade_out, profile, plan
    ("tod_spin_teeter", 0.50, -13.0, "cut", 0.012, "rising", [
        dict(ask=0.8, prompt="a slot machine reel straining against its stop: a fast mechanical ratchet of clicks speeding up under a "
                             "tense rising electric whine that trembles, building suspense that never resolves, dry and close, no music"),
        dict(ask=1.0, prompt="a tense high-pitched electric motor whine straining under load, trembling and wavering, about to "
                             "stall, sustained without stopping, no clicks, no music"),
        dict(ask=0.8, prompt="a ratcheting gear clicking faster and faster under a rising tense tone, cut off before it resolves, "
                             "game slot reel suspense, no music")]),
    ("tod_spin_near", 0.80, -12.5, "ring", 0.12, "fall", [
        dict(ask=0.8, prompt="a short disappointed near miss game sound: two soft glassy synth chime notes falling in pitch, the second "
                             "one bending down and fading out with a small sigh of air, deflated, clean, no music"),
        dict(ask=0.8, prompt="a soft short breath of air, a gentle breathy whoosh that fades away, quiet and close, no voice, no music"),
        dict(ask=0.8, prompt="a soft short whoosh of air, a gentle breeze puff passing by, airy noise only, no tone, no music")]),
    ("tod_pull_reach", 0.66, -11.5, "cut", 0.015, "rising", [
        dict(ask=1.0, prompt="a tense magical energy riser: a shimmering airy swell climbing in pitch under a high trembling crystal tone "
                             "hovering at maximum tension, suspense, about to break, game card reveal, no music"),
        dict(ask=1.2, reverse=True, prompt="a deep airy cinematic boom swoosh that decays away with a long rumbling shimmering tail, "
                                           "suspense, no music")]),
    ("tod_pull_reach_fail", 0.45, -12.5, "ring", 0.08, "fall", [
        dict(ask=0.5, prompt="a quick deflating power down: a synth tone sliding down in pitch fast into a soft muffled thump and a small "
                             "puff of air, letdown, short game UI sound, no music"),
        dict(ask=0.5, prompt="a soft muffled low thump with a small puff of air, like a fist hitting a pillow, short and dry, no music"),
        dict(ask=0.6, prompt="a short synth power down: one electronic tone dropping quickly in pitch and fading, a letdown game sound, "
                             "clean, no music")]),
    ("tod_pull_break", 0.90, -10.0, "ring", 0.18, "burst", [
        dict(ask=1.0, prompt="a magical crystal barrier shattering: a sharp glassy crack and a punchy sub thump that burst into a bright "
                             "rising sparkling chime arpeggio, triumphant breakthrough, game reward, no music"),
        dict(ask=1.0, prompt="a bright magical sparkle burst, glittering chimes and shimmering twinkles scattering and fading out, "
                             "a reward, no music")]),
    ("tod_heat_up", 0.80, -11.5, "ring", 0.12, "whoosh", [
        dict(ask=0.8, prompt="a fire igniting: a quick rising whoosh of flame catching with a few bright crackling sparks, short and "
                             "punchy, close, no music"),
        dict(ask=0.8, prompt="a gas burner igniting with a soft whoomp and a rush of flame, a few crackles, short, close, no music"),
        dict(ask=0.8, prompt="close crackling fire embers popping and sparking, sharp dry crackles and pops, no whoosh, no music")]),
    ("tod_heat_fire", 1.30, -10.0, "ring", 0.22, "blaze", [
        dict(ask=1.4, prompt="a huge fireball igniting: a big rising flame whoosh that erupts into a deep roaring blaze with dense "
                             "crackling embers and a bright rising heroic synth sting on top, on fire power up, no music"),
        dict(ask=1.5, prompt="a large fireball igniting with a big whoomp, roaring up into a blazing fire with crackling embers, "
                             "powerful, close, no music")]),
    ("tod_heat_out", 0.70, -14.0, "ring", 0.15, "fade", [
        dict(ask=0.7, prompt="a fire snuffed out: a sharp steam hiss fading away with a soft descending tone and a few dying embers, "
                             "short, no music"),
        dict(ask=0.8, prompt="a small fire dying out, embers fizzling with a soft fading sizzle and a couple of last quiet crackles, "
                             "no music")]),
]
for _n, _s, _l, _fit, _fo, _p, _plan in NEAR:
    cue(_n, pack="PK17", table=None, dir="near", ch=1, kind="design", secs=_s, lufs=_l, peak=-1.5, profile=_p,
        fit=_fit, fade_out=_fo, plan=_plan, near=True, ratio=6.0)
# the near finisher's high-pass (Hz, default 16): HEATING UP's recorded whoomp carried 64 % of its energy under 45 Hz
# (the placeholder had none), which nobody hears and which held the cue 1.5 dB under its target at the limiter
CUES["tod_heat_up"]["hp"] = 40.0

# ---- PK22: the companions ----------------------------------------------------------------------------------------
cue("tod_ptn_destroyed", pack="PK22", table="tod_partners.csv", dir="partners", kind="oneshot", span=(1.2, 2.0),
    lufs=-14.0, profile="crunch", variants=2, fade_out=0.35,
    plan=[dict(ask=2.0, prompt="a small armored combat robot destroyed: a sharp metal crunch and an electrical short circuit burst with "
                               "crackling sparks, then a descending electronic power down whine as its systems die, a little debris "
                               "clatter, close" + NM),
          dict(ask=2.0, prompt="a flying attack drone exploding and crashing: a crunchy metal impact, a burst of electric sparks and a "
                               "dying motor whine falling in pitch, close" + NM),
          dict(ask=2.0, prompt="a robot breaking apart: metal plates cracking, a short electrical zap and fizz, servos winding down "
                               "with a falling electronic whine, close" + NM),
          dict(ask=2.0, prompt="a combat drone shot down: one loud crunch of metal and glass, a sizzling electrical burst and a "
                               "falling power down whine, close, one continuous event" + NM)],
    rows=[("tod_ptn_destroyed", "w3d", dict(vol=88, dist=(150, 2200, 2600), limit=4))])
cue("tod_ptn_destroyed_plr", pack="PK22", table="tod_partners.csv", dir="partners", kind="oneshot", span=(0.45, 0.8),
    lufs=-18.0, profile="alert", fade_out=0.12,
    plan=[dict(ask=0.8, prompt="a short futuristic HUD warning: a comms link cutting out, a quick descending two tone digital alert "
                               "blip with a burst of radio static, clean" + NM),
          dict(ask=0.8, prompt="a short sci-fi signal lost sound: two falling electronic beeps and a crackle of static that cuts off, "
                               "clean game UI" + NM)],
    rows=[("tod_ptn_destroyed_plr", "ui2d", dict(vol=80))])
cue("tod_ptn_talon_hover_lp", pack="PK22", table="tod_partners.csv", dir="partners", kind="loop", secs=3.0, xfade=0.6,
    lufs=-24.0, profile="bed",
    plan=[dict(ask=8.0, loop=True, prompt="a small quadcopter attack drone hovering in place: a steady high pitched rotor buzz over a low "
                                          "electric motor hum, constant and even, no pitch changes" + NM),
          dict(ask=8.0, loop=True, prompt="a hovering surveillance drone close by: steady whirring propellers and a smooth electric hum, "
                                          "constant, no doppler" + NM)],
    rows=[("tod_ptn_talon_hover_lp", "loop3d", dict(vol=66, dist=(80, 900, 1000), limit=4))])
cue("tod_ptn_raps_roll_lp", pack="PK22", table="tod_partners.csv", dir="partners", kind="loop", secs=2.0, xfade=0.4,
    lufs=-24.0, profile="bed",
    plan=[dict(ask=6.0, loop=True, prompt="a heavy armored metal ball robot rolling fast on a concrete floor: a constant rumbling roll with a "
                                          "high spinning electric motor whir and faint rattling, steady" + NM),
          dict(ask=6.0, loop=True, prompt="a metal sphere rolling continuously on concrete with an electric motor spinning inside it, steady "
                                          "rumble and whir" + NM)],
    rows=[("tod_ptn_raps_roll_lp", "loop3d", dict(vol=64, dist=(60, 700, 800), limit=4))])
cue("tod_ptn_cerberus_servo_lp", pack="PK22", table="tod_partners.csv", dir="partners", kind="loop", secs=2.0, xfade=0.4,
    lufs=-24.0, profile="bed",
    plan=[dict(ask=6.0, loop=True, prompt="a small robotic tank drone driving: continuous whirring electric servo motors and the soft clank "
                                          "of metal tracks, a steady mechanical loop" + NM),
          dict(ask=6.0, loop=True, prompt="robot servo motors whining steadily as a small tracked robot moves, constant electric whir and "
                                          "gentle mechanical ticking" + NM)],
    rows=[("tod_ptn_cerberus_servo_lp", "loop3d", dict(vol=64, dist=(60, 700, 800), limit=4))])

# ---- PK23: the world ---------------------------------------------------------------------------------------------
cue("tod_amb_tower_wind", pack="PK23", table="tod_amb.csv", dir="amb", ch=2, kind="design", secs=48.0, lufs=-26.0,
    profile="bed",
    plan=[dict(ask=30.0, loop=True, prompt="strong steady high altitude wind blowing around the top of a tall skyscraper in wide open air, "
                                           "a constant airflow with soft gusts, no rain" + NM),
          dict(ask=30.0, loop=True, prompt="howling wind high above a city on an open rooftop at night, steady and wide, gentle whistling "
                                           "gusts, no rain" + NM)],
    rows=[("tod_amb_tower_wind", "bed2d", dict(vol=55))])
cue("tod_amb_city_far", pack="PK23", table="tod_amb.csv", dir="amb", ch=2, kind="design", secs=45.0, lufs=-27.0,
    profile="bed",
    plan=[dict(ask=30.0, loop=True, prompt="a vast futuristic city at night heard from a distance: a low distant traffic drone, far away "
                                           "sirens, faint aircraft hum and a dull urban rumble, wide and distant" + NM),
          dict(ask=30.0, loop=True, prompt="distant city ambience at night, a constant low hum of far traffic and machinery with an "
                                           "occasional faraway siren, wide" + NM)],
    rows=[("tod_amb_city_far", "bed2d", dict(vol=52))])
cue("tod_amb_gust", pack="PK23", table="tod_amb.csv", dir="amb", kind="oneshot", span=(3.0, 6.0), lufs=-22.0,
    profile="gust", variants=4, fade_out=0.8,
    plan=[dict(ask=5.0, prompt="a single strong gust of wind rushing past a high building ledge, rising and then falling away, no rain" + NM),
          dict(ask=5.0, prompt="one big whooshing gust of wind sweeping across an open rooftop, swelling then dying away" + NM),
          dict(ask=5.0, prompt="a cold gust of wind whistling past metal railings high above a city, rising and fading" + NM)],
    rows=[("tod_amb_gust", "w3d", dict(vol=70, dist=(400, 3000, 3500), limit=3, pitch=(-80, 80)))])
cue("tod_amb_undercity_lp", pack="PK23", table="tod_amb.csv", dir="amb", kind="loop", secs=14.0, xfade=2.0, lufs=-24.0,
    profile="bed",
    plan=[dict(ask=20.0, loop=True, prompt="an underground concrete maintenance tunnel room tone: a deep low drone, ventilation ducts "
                                           "humming, distant heavy machinery throbbing slowly, eerie and constant" + NM),
          dict(ask=20.0, loop=True, prompt="a sealed underground vault ambience: a low rumbling drone, an air handler humming and a slow "
                                           "distant mechanical throb, dark and steady" + NM)],
    rows=[("tod_amb_undercity_lp", "loop3d", dict(vol=62, dist=(200, 1400, 1600), limit=8))])
cue("tod_amb_plaza_lp", pack="PK23", table="tod_amb.csv", dir="amb", kind="loop", secs=14.0, xfade=2.0, lufs=-24.0,
    profile="bed",
    plan=[dict(ask=20.0, loop=True, prompt="a ruined city plaza at night: a distant traffic wash, far away sirens, faint buzzing neon signs "
                                           "and light wind, constant" + NM),
          dict(ask=20.0, loop=True, prompt="an empty futuristic street at night: far traffic hum, a faint neon buzz, a distant siren now "
                                           "and then and a soft breeze, steady" + NM)],
    rows=[("tod_amb_plaza_lp", "loop3d", dict(vol=60, dist=(200, 1400, 1600), limit=8))])
cue("tod_amb_drip", pack="PK23", table="tod_amb.csv", dir="amb", kind="oneshot", span=(0.4, 2.0), lufs=-26.0,
    profile="drip", variants=4, fade_out=0.3,
    plan=[dict(ask=1.5, prompt="a single water drop falling into a small puddle in a concrete tunnel with a short echo, close" + NM),
          dict(ask=1.5, prompt="one water droplet dripping onto wet stone in an underground room, a clear plip with a little echo" + NM),
          dict(ask=1.5, prompt="a single drip of water into a shallow pool in a sewer, a short resonant plop, close" + NM)],
    rows=[("tod_amb_drip", "w3d", dict(vol=70, dist=(100, 1100, 1300), limit=4, pitch=(-150, 150)))])
cue("tod_amb_pipe", pack="PK23", table="tod_amb.csv", dir="amb", kind="oneshot", span=(1.0, 4.0), lufs=-22.0,
    profile="creak", variants=3, fade_out=0.5,
    plan=[dict(ask=3.0, prompt="a metal pipe knocking and creaking from pressure in an underground tunnel, a few soft hollow clanks, "
                               "slightly distant" + NM),
          dict(ask=3.0, prompt="old steel pipes ticking and groaning as they expand, a low metallic creak and a dull knock, in a "
                               "concrete basement" + NM),
          dict(ask=3.0, prompt="a single deep hollow bang inside a large metal duct followed by a short metallic ring, in a "
                               "tunnel" + NM)],
    rows=[("tod_amb_pipe", "w3d", dict(vol=68, dist=(150, 1400, 1600), limit=4, pitch=(-120, 120)))])
cue("tod_shop_hum", pack="PK23", table="tod_amb.csv", dir="shop", kind="design", secs=10.0, lufs=-24.0, profile="bed",
    plan=[dict(ask=12.0, loop=True, prompt="a buzzing neon sign close up: a constant electrical hum with a faint crackling sizzle of the "
                                           "gas tubes, steady" + NM),
          dict(ask=12.0, loop=True, prompt="an old transformer and neon tubes humming, a steady electric buzz with a light fizzing "
                                           "crackle" + NM)],
    rows=[("tod_shop_hum", "loop3d", dict(vol=64, dist=(80, 600, 700), limit=4))])
cue("tod_teleport_idle_lp", pack="PK23", table="tod_amb.csv", dir="sfx", kind="design", secs=10.0, lufs=-25.0, profile="bed",
    plan=[dict(ask=12.0, loop=True, prompt="a sci-fi teleporter pad idling: a low resonant humming energy field with a soft electric "
                                           "crackle, steady" + NM),
          dict(ask=12.0, loop=True, prompt="a powered energy portal standing ready: a deep warm pulsing hum and a faint shimmering "
                                           "crackle, constant" + NM)],
    # limit 12: the map has 8 transit pads (tod_crown_data::transit_routes) and every one can be ready at once; at 8 a
    # ninth pad would steal the oldest pad's loop for good (a stolen loop never restarts)
    rows=[("tod_teleport_idle_lp", "loop3d", dict(vol=64, dist=(80, 500, 600), limit=12))])
cue("tod_teleport_cool_lp", pack="PK23", table="tod_amb.csv", dir="sfx", kind="design", secs=6.0, lufs=-27.0, profile="bed",
    plan=[dict(ask=8.0, loop=True, prompt="a machine recharging: a quiet steady electric whir with a soft rising tone, constant" + NM)],
    rows=[("tod_teleport_cool_lp", "loop3d", dict(vol=58, dist=(80, 450, 550), limit=12))])
cue("tod_power_wave", pack="PK23", table="tod_amb.csv", dir="sfx", ch=2, kind="design", secs=13.5, lufs=-16.0,
    profile="surge",
    plan=[dict(ask=14.0, prompt="a massive electrical power surge rushing down through a huge building: a deep rising hum, crackling high "
                                "voltage arcs and transformers buzzing to life one after another, receding into the distance, "
                                "cinematic" + NM),
          dict(ask=14.0, prompt="a power grid surging back to life: a deep electric hum swelling, sparks crackling and a long rolling "
                                "rumble of current travelling far away down cables, cinematic" + NM)],
    rows=[("tod_power_wave", "ui2d", dict(vol=85, streamed=True))])
cue("tod_power_relay", pack="PK23", table=None, dir=None, kind="part", profile="impact",
    plan=[dict(ask=1.0, prompt="a single heavy industrial relay contactor clunk, a big electrical switch slamming closed, dry, close" + NM),
          dict(ask=1.0, prompt="one loud electrical breaker switch thrown, a heavy metallic clack with a short buzz, dry, close" + NM)])
cue("tod_power_online", pack="PK23", table="tod_amb.csv", dir="sfx", ch=2, kind="design", span=(2.5, 3.5), lufs=-13.0,
    profile="thump", fade_out=0.6,
    plan=[dict(ask=3.5, prompt="the power of a giant building slamming on all at once: a huge deep electrical thump, a booming low hum "
                               "surge swelling up and settling into a steady buzz, cinematic impact" + NM),
          dict(ask=3.5, prompt="massive floodlights switching on with a heavy electrical clunk and a deep booming hum that rings out, "
                               "cinematic" + NM)],
    rows=[("tod_power_online", "ui2d", dict(vol=90))])
cue("tod_power_boot", pack="PK23", table="tod_amb.csv", dir="sfx", kind="design", secs=1.4, lufs=-16.0, profile="rising",
    fade_out=0.15,
    plan=[dict(ask=1.5, prompt="an electronic control terminal booting up: a capacitor charging whine rising quickly with soft relay "
                               "ticks, a sci-fi computer powering on, short" + NM),
          dict(ask=1.5, prompt="a high voltage capacitor charging up with a rising electric whine, short and clean" + NM)],
    rows=[("tod_power_boot", "w3d", dict(vol=86, dist=(120, 1400, 1600), limit=2))])

# ---- PK27: the Necromancer's foley -------------------------------------------------------------------------------
cue("fly_skull_scream", pack="PK27", table="tod_necro_foley.csv", dir=None, kind="stock",
    files=["zmb\\level\\zm_island\\skull\\scream\\skull_scream_0%d.wav" % i for i in range(4)],
    rows=[("fly_skull_scream", "foley2d", dict(vol=66))])
cue("tod_necro_first_raise_npc", pack="PK27", table="tod_necro_foley.csv", dir=None, kind="stock",
    files=["zmb\\level\\zm_island\\skull\\gun\\fly_skull_first_raise_01.wav"],
    rows=[("tod_necro_first_raise_npc", "foley3d", dict(vol=72))])
cue("tod_necro_skull_lower", pack="PK27", table="tod_necro_foley.csv", dir="necro", kind="oneshot", span=(0.25, 0.55),
    lufs=-20.0, profile="foley", variants=3, fade_out=0.06,
    plan=[dict(ask=0.6, prompt="a carved bone skull lowered against a leather belt: a soft dry bone clack with a cloth rustle, quiet "
                               "close foley" + NM),
          dict(ask=0.6, prompt="a heavy bone relic tucked away into a leather holster, a muffled knock and a short rustle of cloth, "
                               "close foley" + NM),
          dict(ask=0.6, prompt="lowering an old skull talisman, a light hollow bone tap and leather creak, quick, close foley" + NM)],
    rows=[("tod_necro_skull_lower_plr", "foley2d", dict(vol=70)), ("tod_necro_skull_lower_npc", "foley3d", dict(vol=64))])
cue("tod_necro_staff_lower", pack="PK27", table="tod_necro_foley.csv", dir="necro", kind="oneshot", span=(0.35, 0.65),
    lufs=-20.0, profile="foley", variants=2, fade_out=0.08,
    plan=[dict(ask=0.7, prompt="a long wooden and bone magic staff swung down and lowered: a soft short whoosh, a cloth rustle and a "
                               "dull wooden knock, close foley" + NM),
          dict(ask=0.7, prompt="lowering a heavy wooden staff to the side, a quick swish and a soft wooden tap with cloth movement, "
                               "close foley" + NM)],
    rows=[("tod_necro_staff_lower_plr", "foley2d", dict(vol=70)), ("tod_necro_staff_lower_npc", "foley3d", dict(vol=64))])
cue("tod_necro_staff_whoosh", pack="PK27", table="tod_necro_foley.csv", dir="necro", kind="oneshot", span=(0.3, 0.55),
    lufs=-18.0, profile="whoosh", variants=3, fade_out=0.08,
    plan=[dict(ask=0.6, prompt="a heavy wooden staff swung hard through the air: a deep fast whoosh with a faint ghostly hiss, close" + NM),
          dict(ask=0.6, prompt="a fast swing of a long heavy pole cutting the air, a thick swoosh with a cold whispering tail, close" + NM),
          dict(ask=0.6, prompt="a quick powerful staff swipe whoosh, low and heavy, with a short spectral breath, close" + NM)],
    rows=[("tod_necro_staff_whoosh_plr", "foley2d", dict(vol=76)), ("tod_necro_staff_whoosh_npc", "foley3d", dict(vol=72))])
cue("tod_necro_staff_hit", pack="PK27", table="tod_necro_foley.csv", dir="necro", kind="oneshot", span=(0.2, 0.45),
    lufs=-15.0, profile="impact", variants=3, fade_out=0.05,
    plan=[dict(ask=0.5, prompt="a heavy wooden staff striking a zombie body: a dull bone and flesh thud with a short sharp spectral "
                               "crack, close" + NM),
          dict(ask=0.5, prompt="a club smashing into a rotten body, a deep meaty thump with a crunch of bone, close" + NM),
          dict(ask=0.5, prompt="a magic staff hit: a heavy body impact thud with a quick crackle of dark energy, close" + NM)],
    rows=[("tod_necro_staff_hit_plr", "foley2d", dict(vol=82)), ("tod_necro_staff_hit_npc", "foley3d", dict(vol=78))])
cue("tod_necro_staff_surface", pack="PK27", table="tod_necro_foley.csv", dir="necro", kind="oneshot", span=(0.2, 0.45),
    lufs=-17.0, profile="impact", variants=3, fade_out=0.05,
    plan=[dict(ask=0.5, prompt="a wooden staff knocking hard against a concrete wall: a solid dull knock with a short rattle, close" + NM),
          dict(ask=0.5, prompt="a heavy wooden pole hitting a metal surface, a hard wooden clack with a little ring, close" + NM),
          dict(ask=0.5, prompt="a staff striking stone, a sharp dry wooden crack and thud, close" + NM)],
    rows=[("tod_necro_staff_surface_plr", "foley2d", dict(vol=76)), ("tod_necro_staff_surface_npc", "foley3d", dict(vol=72))])

# ---- PK28: the R1 Shadowhunter's bolt impacts --------------------------------------------------------------------
cue("tod_crossbow_impact_surface", pack="PK28", table="tod_crossbow.csv", dir="archer/crossbow", kind="oneshot",
    span=(0.15, 0.4), lufs=-15.0, profile="impact", variants=4, fade_out=0.05,
    plan=[dict(ask=0.5, prompt="a crossbow bolt slamming into a concrete wall: a hard sharp thunk with a short dry crack, close" + NM),
          dict(ask=0.5, prompt="a heavy steel crossbow bolt striking a concrete wall hard: a punchy solid thunk with a sharp crack "
                               "and a short gritty rattle, close" + NM),
          dict(ask=0.5, prompt="an arrow hitting a hard wall and sticking, a quick solid thwack with a tiny rattle, close" + NM),
          dict(ask=0.5, prompt="a steel tipped bolt striking stone, a punchy thunk and a short gritty crack, close" + NM)],
    rows=[("tod_crossbow_impact_surface", "w3d", dict(vol=82, dist=(100, 1800, 2000), limit=4, pitch=(-60, 60)))])
cue("tod_crossbow_impact_flesh", pack="PK28", table="tod_crossbow.csv", dir="archer/crossbow", kind="oneshot",
    span=(0.15, 0.4), lufs=-14.0, profile="impact", variants=4, fade_out=0.05,
    plan=[dict(ask=0.5, prompt="a crossbow bolt punching into flesh: a deep wet thud with a short meaty crunch, close" + NM),
          dict(ask=0.5, prompt="a heavy crossbow bolt thudding deep into a zombie's chest: a punchy wet impact with a meaty crunch "
                               "and a short low thump, close" + NM),
          dict(ask=0.5, prompt="an arrow hitting a body, a heavy wet thwack with a little tearing, close" + NM),
          dict(ask=0.5, prompt="a bolt piercing a zombie torso, a dull fleshy thump and a squelch, close" + NM)],
    rows=[("tod_crossbow_impact_flesh", "w3d", dict(vol=84, dist=(100, 1800, 2000), limit=4, pitch=(-60, 60)))])
cue("tod_crossbow_impact_headshot", pack="PK28", table="tod_crossbow.csv", dir="archer/crossbow", kind="oneshot",
    span=(0.15, 0.45), lufs=-12.5, profile="impact", variants=2, fade_out=0.06,
    plan=[dict(ask=0.5, prompt="a crossbow bolt piercing a skull: a sharp crunching crack of bone with a wet thump, close, brutal" + NM),
          dict(ask=0.5, prompt="an arrow cracking straight through a skull, a hard bony crunch and a wet pop, close" + NM)],
    # (no _plr row: an entitysoundimpacts table has no shooter-side field, so nothing could play one - not shipped)
    rows=[("tod_crossbow_impact_headshot", "w3d", dict(vol=86, dist=(100, 2000, 2200), limit=3, pitch=(-40, 40)))])
cue("tod_crossbow_impact_metal", pack="PK28", table="tod_crossbow.csv", dir="archer/crossbow", kind="oneshot",
    span=(0.15, 0.45), lufs=-15.0, profile="impact", variants=2, fade_out=0.06,
    plan=[dict(ask=0.5, prompt="a crossbow bolt striking armored metal plate: a sharp metallic clang thunk with a short ring, close" + NM),
          dict(ask=0.5, prompt="an arrow glancing off a steel robot body, a hard metal clank with a brief ringing, close" + NM)],
    rows=[("tod_crossbow_impact_metal", "w3d", dict(vol=82, dist=(100, 1800, 2000), limit=4, pitch=(-60, 60)))])

ORDER = list(CUES.keys())
# designs whose length is a timing contract (the gate checks the frame count): the wave = TOD_FALL_WAVE_SECS +
# TOD_FALL_WAVE_HOLD_SECS, the boot = TOD_PDIAL_SPIN, the hums / whir = whole mains cycles / two chase spins
EXACT = ("tod_power_wave", "tod_power_boot", "tod_shop_hum", "tod_teleport_idle_lp", "tod_teleport_cool_lp")
TABLES =["tod_stings.csv", "tod_partners.csv", "tod_amb.csv", "tod_necro_foley.csv", "tod_crossbow.csv"]

# every alias the feature is FOR, and the script that must play it (the gate's "wired" check)
WIRED = {
    "tod_tier_sting": "scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc",
    "tod_ptn_destroyed": "scripts/zm/zm_tod2_cybercity/_tod_partners.gsc",
    "tod_ptn_destroyed_plr": "scripts/zm/zm_tod2_cybercity/_tod_partners.gsc",
    "tod_ptn_talon_hover_lp": "scripts/zm/zm_tod2_cybercity/_tod_partners.gsc",
    "tod_ptn_raps_roll_lp": "scripts/zm/zm_tod2_cybercity/_tod_partners.gsc",
    "tod_ptn_cerberus_servo_lp": "scripts/zm/zm_tod2_cybercity/_tod_partners.gsc",
    "tod_amb_tower_wind": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_city_far": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_gust": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_undercity_lp": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_plaza_lp": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_drip": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_amb_pipe": "scripts/zm/zm_tod2_cybercity/_tod_amb.csc",
    "tod_shop_hum": "scripts/zm/zm_tod2_cybercity/_tod_shop.csc",
    "tod_teleport_idle_lp": "scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc",
    "tod_teleport_cool_lp": "scripts/zm/zm_tod2_cybercity/_tod_teleport.gsc",
    "tod_power_wave": "scripts/zm/zm_tod2_cybercity/_tod_fall.gsc",
    "tod_power_online": "scripts/zm/zm_tod2_cybercity/_tod_fall.gsc",
    "tod_power_boot": "scripts/zm/zm_tod2_cybercity/_tod_power_terminal.gsc",
}


# ================================================================================================================
# THE ALIAS ROWS
# ================================================================================================================
_FULL_2D = ("{name},,loaded,{file},,,,,FLY_WPN_RELOAD_PLR,,,bus_fx,grp_foley,snp_foley,,79,0,{vol},{vol},0,10000,10000,,,,,8,"
            "priority,8,oldest,0,100,70,70,0.25,1,no,2d,front_mostly,,nonlooping,variant,1,0,0,0,0,0.25,no,yes,,0,,no,,,,,,,,,"
            "yes,no,no,0,1,yes,no,,,,,,no,no,,,,,,,,,,,,,,,,,,,,,,,,,,,")     # = tod_necromancer.csv's fly_skull_breathe
_FULL_3D = ("{name},,loaded,{file},,,,,,,,bus_hdrfx,grp_hdrfx,snp_hdrfx,,50,0,{vol},{vol},200,800,800,,,,,4,priority,1,reject,"
            "0,0,40,90,0.25,1,no,3d,default,,nonlooping,variant,1,0,0,0,0,0.25,no,yes,,0,,no,,,,,,,,,yes,no,no,0,1,yes,no,,,,,,"
            "no,no,,,,,,,,,,,,,,,,,,,,,,,,,,,")                                   # = tod_necromancer.csv's zmb_wpn_skullgun_raise_npc


def header_line(root):
    with open(os.path.join(root, HEADER_FROM), encoding="utf-8-sig") as f:
        return f.readline().rstrip("\r\n")


def row_text(cols, kind, name, filespec, p):
    if kind == "foley2d":
        return _FULL_2D.format(name=name, file=filespec, vol=p["vol"])
    if kind == "foley3d":
        return _FULL_3D.format(name=name, file=filespec, vol=p["vol"])
    r = [""] * len(cols)
    col = {h: i for i, h in enumerate(cols)}

    def put(k, v):
        r[col[k]] = str(v)
    put("Name", name)
    put("FileSpec", filespec)
    put("Template", "UIN_MOD")
    put("Storage", "streamed" if p.get("streamed") else "loaded")
    put("VolMin", p["vol"])
    put("VolMax", p["vol"])
    if kind == "ui2d":
        put("PanType", "2d")
        put("Looping", "NONLOOPING")
    elif kind == "bed2d":
        put("Storage", "streamed")
        put("Bus", "BUS_FX")
        put("VolumeGroup", "grp_ambience")
        put("PanType", "2d")
        put("Looping", "LOOPING")
        put("Pauseable", "YES")
    elif kind in ("w3d", "loop3d"):
        put("Bus", "BUS_FX")
        d = p["dist"]
        put("DistMin", d[0])
        put("DistMaxDry", d[1])
        put("DistMaxWet", d[2])
        put("LimitCount", p.get("limit", 4))
        put("LimitType", "oldest")
        pitch = p.get("pitch", (0, 0))
        put("PitchMin", pitch[0])
        put("PitchMax", pitch[1])
        put("PanType", "3d")
        if kind == "loop3d":
            put("VolumeGroup", "grp_ambience")
            put("Looping", "LOOPING")
            put("Pauseable", "YES")
        else:
            put("Looping", "NONLOOPING")
    else:
        raise ValueError(kind)
    out = ",".join(r)
    assert out.count(",") == len(cols) - 1 and '"' not in out, name
    return out


def tables_text(root, man):
    """{table: text} for the five alias tables (LF, tod_ui.csv's header verbatim)"""
    head = header_line(root)
    cols = next(csv.reader([head]))
    out = {t: [head] for t in TABLES}
    for name in ORDER:
        c = CUES[name]
        if not c.get("table"):
            continue
        if c["kind"] == "stock":
            files = c["files"]
        else:
            if name not in man:
                continue
            files = [("tod\\" + f["file"]).replace("/", "\\") for f in man[name]["files"]]
        for alias, kind, p in c["rows"]:
            for fs in files:
                out[c["table"]].append(row_text(cols, kind, alias, fs, p))
    return {t: "\n".join(lines) + "\n" for t, lines in out.items()}


# ================================================================================================================
# THE GDTs: the staffs' melee sound table (PK27) and the bolt-impact tables (PK28)
# ================================================================================================================
def gdt_block(name, gdf, fields):
    return '\t"%s" ( "%s" )\n\t{\n%s\t}\n' % (name, gdf, "".join('\t\t"%s" "%s"\n' % kv for kv in fields))


def necro_sounds_gdt():
    """tod_necro_staff_sounds: modelled field for field on tod_punch_sounds (source_data/tod_warrior_punch.gdt); the
    raise / putaway / first-raise fields stay blank (each staff block names its own), the shield rows are stock's.

    The meleeEntityImpact* fields name an ENTITYSOUNDIMPACTS asset and meleeSurfaceSound* a SURFACESOUNDDEF asset, never
    an alias (the linker refuses an alias there: "is not a valid entitysoundimpacts asset", wave-2 full1.log). Those four
    assets are defined below, each pointing at the alias rows, exactly the tod_punch_hits_* / tod_punch_surfaces_* shape."""
    hit_n, hit_p = "tod_necro_staff_hits_npc", "tod_necro_staff_hits_plr"
    surf_n, surf_p = "tod_necro_staff_surfaces_npc", "tod_necro_staff_surfaces_plr"
    f = [("altSwitch", ""), ("altSwitchPlayer", ""), ("firstRaiseWeapon", ""), ("firstRaiseWeaponPlayer", ""),
         ("lowerADSWeaponPlayer", "")]
    for k in ("ChainFinish", "ChainMid", "Lunge", "Power", "Swipe"):
        f.append(("meleeEntityImpact" + k, hit_n))
        f.append(("meleeEntityImpact" + k + "Player", hit_p))
        if k in ("Lunge", "Power", "Swipe"):
            f.append(("meleeEntityImpact" + k + "Victim", hit_n))
    f += [("meleeFromBehind", ""), ("meleeFromBehindPlayer", ""), ("meleeFromBehindVictim", ""),
          ("meleeHitShield", "wpn_melee_shield_npc_default"), ("meleeHitShieldPlayer", "wpn_melee_shield_plr_default"),
          ("meleeHitShieldVictim", "wpn_melee_shield_plr_default"), ("meleeLungeInWhoosh", ""), ("meleeLungeInWhooshPlayer", ""),
          ("meleePowerWhoosh", "tod_necro_staff_whoosh_npc"), ("meleePowerWhooshLeft", ""),
          ("meleePowerWhooshPlayer", "tod_necro_staff_whoosh_plr"), ("meleePowerWhooshPlayerLeft", ""),
          ("meleeSurfaceSound", surf_n), ("meleeSurfaceSoundPlayer", surf_p),
          ("meleeWhoosh", "tod_necro_staff_whoosh_npc"), ("meleeWhooshPlayer", "tod_necro_staff_whoosh_plr"),
          ("pickupAmmo", ""), ("pickupAmmoPlayer", ""), ("pickupWeapon", ""), ("pickupWeaponPlayer", ""),
          ("putAway", ""), ("putAwayPlayer", ""), ("raiseADSWeaponPlayer", ""), ("raiseWeapon", ""), ("raiseWeaponPlayer", "")]
    f.sort(key=lambda kv: kv[0])
    # the punch's surface table leaves the soft surfaces silent; the staff knocks the same set
    soft = {"cushion", "flesh", "foliage", "fruit", "grass", "paper", "player", "tallgrass", "water"}
    blocks = [gdt_block("tod_necro_staff_sounds", "sharedweaponsounds.gdf", f)]
    for name, alias in ((hit_p, "tod_necro_staff_hit_plr"), (hit_n, "tod_necro_staff_hit_npc")):
        blocks.append(gdt_block(name, "entitysoundimpacts.gdf", [(k, alias) for k in ENT_KEYS]))
    for name, alias in ((surf_p, "tod_necro_staff_surface_plr"), (surf_n, "tod_necro_staff_surface_npc")):
        blocks.append(gdt_block(name, "surfacesounddef.gdf", [(k, "" if k in soft else alias) for k in SURF_KEYS]))
    return "{\n" + "".join(blocks) + "}\n"


# the surfaces, as the stock surface tables name them (source_data/impactsoundbolt.gdt surface_crossbow_impact)
SURF_KEYS = ["asphalt", "bark", "bodyarmor", "brick", "carpet", "ceramic", "cloth", "concrete", "cushion", "defaultsurface",
             "dirt", "flesh", "foliage", "fruit", "glass", "glassbulletproof", "glasscar", "grass", "gravel", "ice", "metal",
             "metalcar", "metalcatwalk", "metalhollow", "metalthin", "mud", "paintedmetal", "paper", "plaster", "plastic",
             "player", "riotshield", "rock", "rubber", "sand", "snow", "tallgrass", "water", "watershallow", "wood"]
METALLIC = {"bodyarmor", "metal", "metalcar", "metalcatwalk", "metalhollow", "metalthin", "paintedmetal", "riotshield"}
ENT_KEYS = ["armorHeavyBody", "armorHeavyBodyFatal", "armorHeavyHead", "armorHeavyHeadFatal", "armorLightBody",
            "armorLightBodyFatal", "armorLightHead", "armorLightHeadFatal", "fleshBody", "fleshBodyFatal", "fleshHead",
            "fleshHeadFatal", "powerArmorBody", "powerArmorBodyFatal", "powerArmorHead", "powerArmorHeadFatal",
            "robotBossBody", "robotBossBodyFatal", "robotBossHead", "robotBossHeadFatal", "robotLightBody",
            "robotLightBodyFatal", "robotLightHead", "robotLightHeadFatal", "skeletonBody", "skeletonBodyFatal",
            "skeletonHead", "skeletonHeadFatal", "zombieBody", "zombieBodyFatal", "zombieHead", "zombieHeadFatal"]
FX_SURFACES = 40      # Surface0 .. Surface39 (the stock surfacefxtable "surface_enter" carries this many)
CROSSBOW_FX = "tod/archer/fx_tod_crossbow_bolt_impact"
CROSSBOW_FX_UG = "tod/archer/fx_tod_crossbow_bolt_impact_ug"


def crossbow_gdt():
    """the bolt's impact SOUNDS (impactsoundstable -> surfacesounddef + entitysoundimpacts, the stock bolt_impact shape)
    and its impact EFFECTS (impactsfxtable -> a surfacefxtable of the generated bolt burst, every surface; the entity
    hits keep stock's small-bullet blood, the table every gun here already links). Base + the hotter PaP (_ug)."""
    surf = [(k, "tod_crossbow_impact_metal" if k in METALLIC else
             ("tod_crossbow_impact_flesh" if k in ("flesh", "player") else "tod_crossbow_impact_surface")) for k in SURF_KEYS]
    ent = []
    for k in ENT_KEYS:
        if k.startswith("skeleton"):
            v = ""
        elif k.endswith("HeadFatal") and not k.startswith(("robot", "powerArmor")):
            v = "tod_crossbow_impact_headshot"
        elif k.startswith(("robot", "armorHeavy", "powerArmor")):
            v = "tod_crossbow_impact_metal"
        else:
            v = "tod_crossbow_impact_flesh"
        ent.append((k, v))
    b = [gdt_block("tod_crossbow_bolt_impact", "impactsoundstable.gdf",
                   [("entitySoundImpacts", "tod_crossbow_entity_snd"), ("surfaceSoundTable", "tod_crossbow_surface_snd"),
                    ("victimSoundImpacts", "")]),
         gdt_block("tod_crossbow_entity_snd", "entitysoundimpacts.gdf", ent),
         gdt_block("tod_crossbow_surface_snd", "surfacesounddef.gdf", surf)]
    for suffix, fx in (("", CROSSBOW_FX), ("_ug", CROSSBOW_FX_UG)):
        # escaped backslashes, exactly as every stock surfacefxtable writes its paths ("skye_efx\\t6_efx\\..efx"): the
        # bow's forward-slash form is proven on a weapon FIELD, never on this asset type (no map-owned table had one)
        efx = fx.replace("/", "\\\\") + ".efx"
        # the stock table leaves Surface7 and Surface29 empty (the entity table owns those hits): so does this one
        rows = sorted([("Surface%d" % i, "" if i in (7, 29) else efx) for i in range(FX_SURFACES)], key=lambda kv: kv[0])
        b.append(gdt_block("tod_crossbow_bolt_enter" + suffix, "impactsfxtable.gdf",
                           [("entityFXImpacts", "entity_enter_bullet_small"), ("surfaceFX", "tod_crossbow_surface_fx" + suffix)]))
        b.append(gdt_block("tod_crossbow_surface_fx" + suffix, "surfacefxtable.gdf", rows))
    return "{\n" + "".join(b) + "}\n"


GDTS = {"source_data/tod_necro_sounds.gdt": necro_sounds_gdt, "source_data/tod_crossbow_impacts.gdt": crossbow_gdt}


# ================================================================================================================
# TAKES: generation, measurement, scoring
# ================================================================================================================
def load(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
        f.write("\n")


def plan_of(name, i):
    plan = CUES[name]["plan"]
    return plan[i % len(plan)]


def take_audio(name, row, ch=None):
    x = dsp.decode(os.path.join(REPO, row["file"]), ch or 2)
    if row.get("reverse"):
        x = np.ascontiguousarray(x[::-1])
    return x


def features(x):
    m = dsp.mono(x)
    if len(m) < int(0.05 * SR) or np.max(np.abs(m)) < 1e-4:
        return None
    e = dsp.envelope(x)
    pk = e.max()
    dur = len(m) / SR
    t = np.arange(len(e)) * 0.010
    ip = int(np.argmax(e))
    onset = float(t[np.where(e >= 0.5 * pk)[0][0]])
    after = e[ip:]
    low = np.where(after <= 0.1 * pk)[0]
    decay = float(low[0] * 0.010) if low.size else float(dur - t[ip])
    tail_db = float(dsp.db(e[-max(1, 5):].mean() / pk))
    third = max(1, len(e) // 3)
    rise_db = float(dsp.db(e[-third:].mean() / (e[:third].mean() + 1e-12)))
    hot = (np.abs(m) >= 0.999).astype(np.int8)
    runs = np.convolve(hot, np.ones(4, dtype=np.int8), "valid") >= 4
    clip = float(np.mean(runs)) if runs.size else 0.0
    spec = np.abs(np.fft.rfft(m * np.hanning(len(m))))
    f = np.fft.rfftfreq(len(m), 1.0 / SR)
    tot = spec.sum() + 1e-12
    s = spec[(f > 60) & (f < 12000)] + 1e-12
    # PRESENCE: the share of the take's energy at or above 250 Hz, UNWINDOWED (a Hann window over a whole one-shot mutes
    # its attack and reads the tail). A hit that is all sub-bass rumble has none: two concrete "thunks" that were pure
    # 28 Hz shipped in the first bolt-impact set (2026-10-05) because nothing here asked for a crack.
    pw = np.abs(np.fft.rfft(m)) ** 2
    pres = float(pw[f >= 250].sum() / (pw.sum() + 1e-20))

    def centroid(seg):
        if len(seg) < 512:
            return 0.0
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        ff = np.fft.rfftfreq(len(seg), 1.0 / SR)
        return float((sp * ff).sum() / (sp.sum() + 1e-12))
    h = len(m) // 2
    c1, c2 = centroid(m[:h]), centroid(m[h:])
    late = e[int(0.45 / 0.010):]
    late_db = float(dsp.db(late.max() / pk)) if late.size else -60.0
    # the EVENTS a take holds (rises above -14 dB of its peak after a fall below -26 dB: a single hit is 1, the
    # "double hit" / "triple tap" takes are 2-3), its longest internal GAP (frames under -45 dB between its first and
    # last sound: a destruction with a hole in the middle) and its DENSITY (the share of frames within 20 dB of the peak:
    # a drip is sparse, a hiss is dense)
    rel = dsp.db(e / pk)
    events, armed = 0, True
    for v in rel:
        if armed and v > -14.0:
            events += 1
            armed = False
        elif v < -26.0:
            armed = True
    live = np.where(rel > -30.0)[0]
    gap, run = 0, 0
    if live.size:
        for v in rel[live[0]:live[-1] + 1]:
            run = run + 1 if v < -45.0 else 0
            gap = max(gap, run)
    return dict(dur=dur, onset=onset, peak_at=float(t[ip] / max(dur, 1e-6)), decay=decay, tail_db=tail_db,
                rise_db=rise_db, clip=clip, low=float(spec[f < 180].sum() / tot), hi=float(spec[f > 4000].sum() / tot),
                flat=float(np.exp(np.mean(np.log(s))) / np.mean(s)), c_trend=float(np.log2((c2 + 1) / (c1 + 1))),
                late_db=late_db, steady=dsp.steady(x), centroid=float(centroid(m)), events=int(events),
                gap=float(gap * 0.010), dens=float(np.mean(rel > -20.0)), pres=pres)


def near(v, lo, hi, soft):
    if lo <= v <= hi:
        return 1.0
    d = (lo - v) if v < lo else (v - hi)
    return max(0.0, 1.0 - d / soft)


def score(name, ft, raw_dur):
    """how well a take fits its cue (0..1): the profile's shape + how much of the take survives the fit"""
    if ft is None:
        return -1.0, {"dead": True}
    c = CUES[name]
    p = c["profile"]
    s = {"clip": 1.0 - min(1.0, ft["clip"] * 50)}
    want = c["secs"] or (c["span"][1] if c.get("span") else plan_of(name, 0)["ask"])
    if c["kind"] in ("loop", "design") and p == "bed":
        s["length"] = near(raw_dur, 0.6 * want, 10 * want, 0.5 * want)
    else:
        s["length"] = near(raw_dur, 0.7 * (c["secs"] or (c["span"][0] if c.get("span") else want)), 3.0 * want, 0.6 * want)
    if p == "bed":
        s["steady"] = near(ft["steady"], 0.0, 5.0, 6.0)
        s["no_hits"] = near(ft["onset"], 0.0, 99.0, 1.0) * near(ft["peak_at"], 0.0, 1.0, 1.0)
        s["not_tonal_only"] = near(ft["flat"], 0.0005, 1.0, 0.001)
    elif p == "rising":
        s["rise"] = near(ft["rise_db"], 4.0, 40.0, 6.0)
        s["peak_at"] = near(ft["peak_at"], 0.45, 1.0, 0.3)
        s["held"] = near(ft["tail_db"], -16.0, 0.0, 12.0)
        s["climb"] = near(ft["c_trend"], 0.0, 3.0, 0.6)
    elif p == "fall":
        s["onset"] = near(ft["onset"], 0.0, 0.08, 0.15)
        s["peak_at"] = near(ft["peak_at"], 0.0, 0.4, 0.3)
        s["sink"] = near(ft["c_trend"], -3.0, -0.05, 0.5)
        s["tonal"] = near(ft["flat"], 0.0, 0.45, 0.3)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "burst":
        s["onset"] = near(ft["onset"], 0.0, 0.06, 0.12)
        s["bright"] = near(ft["hi"], 0.08, 1.0, 0.08)
        s["body"] = near(ft["low"], 0.03, 1.0, 0.05)
        s["ring"] = near(ft["decay"], 0.15, 1.0, 0.3)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "whoosh":
        s["onset"] = near(ft["onset"], 0.02, 0.3, 0.25)
        s["peak_at"] = near(ft["peak_at"], 0.1, 0.65, 0.3)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
        s["noise"] = near(ft["flat"], 0.12, 1.0, 0.15)
        s["single"] = near(ft["events"], 1, 1, 1.5)      # one swing
    elif p == "blaze":
        s["onset"] = near(ft["onset"], 0.0, 0.35, 0.3)
        s["peak_at"] = near(ft["peak_at"], 0.08, 0.6, 0.3)
        s["body"] = near(ft["low"], 0.06, 1.0, 0.08)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "fade":
        s["onset"] = near(ft["onset"], 0.0, 0.1, 0.15)
        s["peak_at"] = near(ft["peak_at"], 0.0, 0.35, 0.3)
        s["hiss"] = near(ft["hi"], 0.15, 1.0, 0.15)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "tier":
        s["onset"] = near(ft["onset"], 0.0, 0.08, 0.15)
        s["swell"] = near(ft["late_db"], -6.0, 0.0, 6.0)
        s["sub"] = near(ft["low"], 0.12, 1.0, 0.1)
        s["span"] = near(ft["dur"], 1.5, 2.5, 0.3)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p in ("impact", "thump"):
        s["onset"] = near(ft["onset"], 0.0, 0.03, 0.08)
        s["peak_at"] = near(ft["peak_at"], 0.0, 0.25, 0.3)
        s["decay"] = near(ft["decay"], 0.03, 0.35 if p == "impact" else 2.0, 0.4)
        s["body"] = near(ft["low"], 0.04 if p == "impact" else 0.15, 1.0, 0.08)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
        s["single"] = near(ft["events"], 1, 1, 1.5)      # one hit, never a double / triple tap
        s["gap"] = near(ft["gap"], 0.0, 0.08, 0.2)
        if p == "impact":                                # a hit you can HEAR on any speaker (a thump may be all sub)
            s["presence"] = near(ft.get("pres", 1.0), 0.15, 1.0, 0.15)
    elif p == "crunch":
        s["onset"] = near(ft["onset"], 0.0, 0.06, 0.12)
        s["bright"] = near(ft["hi"], 0.05, 1.0, 0.06)
        s["long"] = near(ft["decay"], 0.25, 2.0, 0.4)
        s["sink"] = near(ft["c_trend"], -4.0, 0.2, 0.6)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
        s["gap"] = near(ft["gap"], 0.0, 0.12, 0.3)       # one destruction, not two with a hole between
    elif p == "alert":
        s["onset"] = near(ft["onset"], 0.0, 0.08, 0.15)
        s["tonal"] = near(ft["flat"], 0.0, 0.35, 0.3)
        s["sink"] = near(ft["c_trend"], -3.0, 0.1, 0.5)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
    elif p == "gust":
        s["peak_at"] = near(ft["peak_at"], 0.2, 0.75, 0.25)
        s["onset"] = near(ft["onset"], 0.3, 3.0, 0.5)
        s["noise"] = near(ft["flat"], 0.15, 1.0, 0.15)
        s["ends"] = near(ft["tail_db"], -90.0, -20.0, 12.0)
    elif p == "drip":
        s["onset"] = near(ft["onset"], 0.0, 0.03, 0.08)
        s["decay"] = near(ft["decay"], 0.02, 0.6, 0.5)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
        s["not_noise"] = near(ft["flat"], 0.0, 0.35, 0.3)
        s["sparse"] = near(ft["dens"], 0.0, 0.15, 0.2)   # a drip is a plip and a ring, never a held tone or a hiss
        s["few"] = near(ft["events"], 1, 2, 2)
    elif p == "creak":
        s["ends"] = near(ft["tail_db"], -90.0, -22.0, 12.0)
        s["dur"] = near(ft["dur"], 1.0, 4.0, 1.0)
    elif p == "foley":
        s["onset"] = near(ft["onset"], 0.0, 0.12, 0.15)
        s["decay"] = near(ft["decay"], 0.02, 0.35, 0.3)
        s["ends"] = near(ft["tail_db"], -90.0, -24.0, 12.0)
        s["few"] = near(ft["events"], 1, 3, 2)
    elif p == "surge":
        s["long"] = near(ft["dur"], 11.0, 30.0, 4.0)
        s["body"] = near(ft["low"], 0.05, 1.0, 0.06)
    total = sum(s.values()) / len(s)
    return float(total), s


# how hard a one-shot may be compressed to reach its loudness (dsp.level_dense): the 2D card kit most (its targets
# were set by synthesised placeholders), a hit least (its attack is the point)
RATIO = {"impact": 2.5, "thump": 2.0, "foley": 2.0, "whoosh": 2.0, "crunch": 2.0, "alert": 2.0, "gust": 1.5,
         "drip": 2.0, "creak": 2.0}


def ratio_of(name):
    c = CUES[name]
    return c.get("ratio", RATIO.get(c["profile"], 1.0))


def measure(name, row):
    x = take_audio(name, row)
    xt = dsp.trim_tail(dsp.trim_head(x))
    raw = len(xt) / SR
    ft = features(xt)
    row["raw_dur"] = round(raw, 3)
    row["features"] = ft
    row["score"], row["parts"] = score(name, ft, raw)
    c = CUES[name]
    if c["kind"] == "oneshot" and ft is not None:
        # REACH: how close the fitted take gets to its loudness target under the capped limiter + the cue's ratio
        y, _, ratio = dsp.level_dense(fit(name, x), c["lufs"], c["peak"], max_ratio=ratio_of(name))
        row["reach_lufs"] = round(dsp.lufs(y), 2)
        row["reach_ratio"] = ratio
        if c["profile"] == "impact":
            # a hit is judged on its clean PUNCH (dsp.punch): at least -11 dB from a clean -1 dBFS peak
            y, _, _ = dsp.level_dense(fit(name, x), 0.0, c["peak"], max_ratio=ratio_of(name))
            row["punch_db"] = round(dsp.punch(y), 2)
            row["parts"]["reach"] = near(row["punch_db"], -11.0, 0.0, 6.0)
        else:
            row["parts"]["reach"] = near(c["lufs"] - row["reach_lufs"], -99.0, 1.5, 6.0)
        vals = [v for v in row["parts"].values() if isinstance(v, float)]
        row["score"] = float(sum(vals) / len(vals))
    return row


def request(prompt, secs, loop):
    import eleven
    body = {"text": prompt, "duration_seconds": float(max(0.5, min(30.0, secs))), "prompt_influence": PROMPT_INFLUENCE,
            "model_id": MODEL}
    if loop:
        body["loop"] = True
    raw = eleven.call("POST", "/v1/sound-generation", body=body, query={"output_format": "pcm_48000"})
    if not isinstance(raw, (bytes, bytearray)):
        raise RuntimeError("unexpected response %r" % (raw,))
    return dsp.pcm_stereo_to_wav(bytes(raw))


def generate(cues, takes, plan_row=None):
    data = load(TAKES_JSON, {})
    for name in cues:
        c = CUES[name]
        if not c["plan"]:
            continue
        rows = data.get(name, [])
        n = takes if takes else len(c["plan"])
        d = os.path.join(WORK, name)
        os.makedirs(d, exist_ok=True)
        for i in range(len(rows), len(rows) + n):
            p = plan_of(name, i) if plan_row is None else c["plan"][plan_row]
            take = "take_%d" % (i + 1)
            path = os.path.join(d, take + ".wav")
            open(path, "wb").write(request(p["prompt"], p["ask"], p.get("loop", False)))
            row = dict(name=take, file=os.path.relpath(path, REPO).replace("\\", "/"), prompt=p["prompt"], ask=p["ask"],
                       reverse=bool(p.get("reverse")), loop=bool(p.get("loop")), model=MODEL)
            rows.append(measure(name, row))
            print("%-30s %s score %.3f raw %.2fs" % (name, take, row["score"], row["raw_dur"]))
            data[name] = rows
            save(TAKES_JSON, data)
    return data


def adopt():
    """the PK17 pack's takes (2026-10-04, mp3 44.1k) join this tool's takes, prompts and all (copied, not moved)"""
    import shutil
    old = load(os.path.join(PK17_OLD, "takes.json"), {})
    data = load(TAKES_JSON, {})
    n = 0
    for name, rows in old.items():
        if name not in CUES or data.get(name):
            continue
        out = []
        for r in rows:
            src = os.path.join(REPO, r["file"])
            if not os.path.exists(src):
                continue
            d = os.path.join(WORK, name)
            os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, "%s%s" % (r["name"], os.path.splitext(src)[1]))
            shutil.copyfile(src, dst)
            row = dict(name=r["name"], file=os.path.relpath(dst, REPO).replace("\\", "/"), prompt=r.get("prompt", ""),
                       ask=None, reverse=bool(r.get("reverse")), loop=False, model="adopted:PK17 2026-10-04")
            out.append(measure(name, row))
            n += 1
        data[name] = out
    save(TAKES_JSON, data)
    print("adopted %d takes" % n)


def rescore(cues):
    data = load(TAKES_JSON, {})
    for name in cues:
        for r in data.get(name, []):
            measure(name, r)
        rows = data.get(name, [])
        if rows:
            print("%-30s %s" % (name, "  ".join("%s %.2f" % (r["name"], r["score"]) for r in rows)))
    save(TAKES_JSON, data)


def chosen(name, data, picks, k):
    """the k takes to ship: the user's picks first, then the best by score"""
    rows = [r for r in data.get(name, []) if r.get("features")]
    out = []
    for want in picks.get(name, []):
        for r in rows:
            if r["name"] == want and r not in out:
                out.append(r)
    for r in sorted(rows, key=lambda r: -r["score"]):
        if r not in out:
            out.append(r)
    return out[:k]


# ================================================================================================================
# RENDER: fit + level a take; the loops; the designs
# ================================================================================================================
def fit(name, x):
    c = CUES[name]
    x = dsp.to_ch(x, c["ch"])
    x = dsp.trim_head(x, -40.0)
    x = dsp.dc_block(x)
    if c["secs"] is not None:
        x = dsp.fit_len(x, int(round(c["secs"] * SR)))
    else:
        x = dsp.trim_tail(x)
        lo, hi = c["span"]
        n = min(len(x), int(round(hi * SR)))
        n = max(n, int(round(lo * SR)))
        x = dsp.fit_len(x, n)
    x = dsp.fade_in(x, 0.003)
    if c.get("fit") == "cut":
        x = dsp.fade_out(x, c["fade_out"], squared=False)
    else:
        x = dsp.fade_out(x, c["fade_out"])
    x[-1] = 0.0
    return x


def render_oneshot(name, row, target=None):
    c = CUES[name]
    y, gr, ratio = dsp.level_dense(fit(name, take_audio(name, row)), c["lufs"] if target is None else target, c["peak"],
                                   max_ratio=ratio_of(name))
    return y, dict(take=row["name"], ratio=ratio, limiter_gr_db=round(gr, 2))


def render_variants(name, rows):
    """the cue's variants, all at ONE loudness: the target, or (when one variant cannot reach it cleanly) the quietest
    variant's level - a random pick between rows must never jump in level. A HIT (profile impact) is matched on its
    50 ms PUNCH instead: each as loud as it can be cleanly, then all brought down to the softest one's punch"""
    c = CUES[name]
    if c["profile"] == "impact":
        out = [render_oneshot(name, r, target=0.0) for r in rows]
        p = [dsp.punch(y) for y, _ in out]
        eff = min(p)
        res = []
        for (y, info), pi in zip(out, p):
            res.append((y * 10 ** ((eff - pi) / 20), dict(info, punch_db=round(eff, 2))))
        return res
    out = [render_oneshot(name, r) for r in rows]
    eff = min([c["lufs"]] + [dsp.lufs(y) for y, _ in out])
    if eff < c["lufs"] - 0.05:
        out = [render_oneshot(name, r, target=eff) for r in rows]
        for _, info in out:
            info["level_note"] = "set at %.2f LUFS (the quietest variant's clean reach)" % eff
    return out


def render_loop(name, row):
    c = CUES[name]
    x = dsp.to_ch(take_audio(name, row), c["ch"])
    x = dsp.dc_block(x)
    x = dsp.even_out(x, win=0.5, max_db=4.0)
    lp, seam, at = dsp.make_loop_best(x, c["secs"], c["xfade"])
    y, gr = dsp.level(lp, c["lufs"], c["peak"], loop=True)
    return y, dict(take=row["name"], loop_at=round(at, 2), seam=seam, steady_db=round(dsp.steady(y), 2), limiter_gr_db=round(gr, 2))


def best(name, data, picks, k=1):
    rows = chosen(name, data, picks, k)
    if len(rows) < k:
        raise SystemExit("%s: %d usable takes, %d needed - generate first" % (name, len(rows), k))
    return rows


# ---- the designs -------------------------------------------------------------------------------------------------
def design_tier_sting(data, picks):
    """THE PROMOTION: the best whole take, with a written sub drop under its swell (a promotion is FELT: the 0.86 s
    RARE/EPIC sting has no sub at all) - a 55 -> 31 Hz slide landing where the take's late swell peaks"""
    c = CUES["tod_tier_sting"]
    row = best("tod_tier_sting", data, picks)[0]
    x = dsp.to_ch(take_audio("tod_tier_sting", row), 2)
    x = dsp.trim_head(x, -40.0)
    x = dsp.dc_block(x)
    x = dsp.trim_tail(x)
    lo, hi = c["span"]
    n = max(int(lo * SR), min(len(x), int(hi * SR)))
    x = dsp.fit_len(x, n)
    e = dsp.envelope(x)
    i0 = int(0.45 / 0.010)
    t_swell = (i0 + int(np.argmax(e[i0:]))) * 0.010 if len(e) > i0 + 5 else 0.6
    drop = dsp.sub_drop(min(1.4, n / SR - t_swell), 55.0, 31.0, 0.45)
    pk = np.max(np.abs(x))
    x = dsp.place(x, drop * 0.55 * pk, max(0.0, t_swell - 0.04))
    x = dsp.fade_in(x, 0.003)
    x = dsp.fade_out(x, c["fade_out"])
    x[-1] = 0.0
    y, gr = dsp.level(x, c["lufs"], c["peak"])
    return [(y, dict(take=row["name"], swell_at=round(t_swell, 3), limiter_gr_db=round(gr, 2)))]


def bed_from_two(name, data, picks):
    """a long 2D bed from the two best takes: each evened out, joined by a 3 s equal-power crossfade, the overhang
    looped over the head (the take seams and the wrap are all crossfades)"""
    c = CUES[name]
    rows = best(name, data, picks, 2)
    parts = []
    for r in rows:
        x = dsp.to_ch(take_audio(name, r), 2)
        x = dsp.dc_block(x)
        x = dsp.even_out(x, win=1.0, max_db=4.0)
        parts.append(x[int(0.4 * SR):len(x) - int(0.4 * SR)])
    # one place: the second take re-voiced to the first's long-term spectrum, at the first's loudness, so neither the
    # join nor the wrap changes the colour of the air (the first cut of the wind darkened for half of every loop)
    parts[1] = dsp.eq_match(parts[1], parts[0])
    parts[1] = parts[1] * 10 ** ((dsp.lufs(parts[0]) - dsp.lufs(parts[1])) / 20)
    xf = int(3.0 * SR)
    a, b = parts
    t = np.linspace(0, np.pi / 2, xf)[:, None]
    joined = np.concatenate([a[:-xf], a[-xf:] * np.cos(t) + b[:xf] * np.sin(t), b[xf:]])
    lp, seam, _ = dsp.make_loop_best(joined, min(c["secs"], len(joined) / SR - 6.0), 3.0, lo=0.0, hop=0.25)
    y, gr = dsp.level(lp, c["lufs"], c["peak"], loop=True)
    return [(y, dict(take="+".join(r["name"] for r in rows), seam=seam, steady_db=round(dsp.steady(y), 2),
                     limiter_gr_db=round(gr, 2)))]


def hum_core(secs, f0, partials, seed, buzz=0.0, beat=0.0):
    """a mains-locked hum: whole cycles of f0 in `secs` (a loop by construction), partials (k, amp), an optional
    rectified-sine BUZZ (a transformer's 2x f0 growl) and a slow beating detune on the fundamental"""
    n, t = dsp.tl(secs)
    x = np.zeros(n)
    for k, a in partials:
        x += a * np.sin(2 * np.pi * f0 * k * t)
    if beat:
        x += 0.35 * partials[0][1] * np.sin(2 * np.pi * (f0 + beat) * t)
    if buzz:
        r = np.abs(np.sin(2 * np.pi * f0 * t))
        x += buzz * (r - r.mean()) * 2
    return x


def loop_take(name, row, secs, xfade):
    x = dsp.to_ch(take_audio(name, row), 1)
    x = dsp.dc_block(x)
    x = dsp.even_out(x, win=0.5, max_db=4.0)
    lp, _, _ = dsp.make_loop_best(x, secs, xfade)
    return lp[:, 0]


def design_shop_hum(data, picks):
    """THE HUT'S NEON: the BUZZ is written - a 60 Hz transformer core (whole cycles: 600 in 10 s, so it loops
    exactly) carrying the 120 Hz family a neon ballast growls with (the rectified-sine buzz puts harmonics up to ~3 kHz)
    - and the recorded take (the model heard 'neon' as the gas tubes' sizzle: 90 % of it above 4 kHz) is the faint
    SIZZLE on top, band-limited and well under the buzz"""
    c = CUES["tod_shop_hum"]
    row = best("tod_shop_hum", data, picks)[0]
    sizzle = loop_take("tod_shop_hum", row, c["secs"], 1.5)
    sizzle = dsp.band(sizzle, 2500, 11000)[:, 0]
    core = hum_core(c["secs"], 60.0, [(1, 0.35), (2, 1.0), (3, 0.3), (4, 0.45), (6, 0.25), (8, 0.12), (10, 0.06)], 1, buzz=0.6)
    core = dsp.band(core, 45, 3500)[:, 0]
    x = unit(core) * 1.0 + unit(sizzle) * 0.22
    y, gr = dsp.level(x, c["lufs"], c["peak"], loop=True)
    return [(y, dict(take=row["name"], seam=dsp.seam_score(y), limiter_gr_db=round(gr, 2)))]


def design_tp_idle(data, picks):
    """THE READY PAD: a low resonant field (55 Hz with a 0.4 Hz beat and soft upper partials, whole cycles) under the
    best idle-energy take"""
    c = CUES["tod_teleport_idle_lp"]
    row = best("tod_teleport_idle_lp", data, picks)[0]
    tex = loop_take("tod_teleport_idle_lp", row, c["secs"], 1.5)
    core = hum_core(c["secs"], 55.0, [(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.12)], 2, beat=0.4)
    x = unit(tex) * 1.0 + unit(core) * 0.6
    y, gr = dsp.level(x, c["lufs"], c["peak"], loop=True)
    return [(y, dict(take=row["name"], seam=dsp.seam_score(y), limiter_gr_db=round(gr, 2)))]


def design_tp_cool(data, picks):
    """THE RECHARGING PAD: an endless rising whir (a Shepard glissando: six octave-spaced sines climbing one octave
    per loop under a fixed bell-shaped spectral window - it rises forever and the wrap is exact) with the take's
    whir as texture. The chase spins once every 3 s; this loop is two spins."""
    c = CUES["tod_teleport_cool_lp"]
    row = best("tod_teleport_cool_lp", data, picks)[0]
    secs = c["secs"]
    n, t = dsp.tl(secs)
    x = np.zeros(n)
    base = 110.0
    for k in range(6):
        octv = (k + t / secs) % 6.0                       # 0..6 octaves above base, wrapping
        f = base * 2 ** octv
        w = np.exp(-0.5 * ((octv - 3.0) / 1.1) ** 2)      # the window: loudest mid-range, silent at the wrap ends
        ph = 2 * np.pi * np.cumsum(f) / SR
        x += w * np.sin(ph)
    tex = dsp.band(loop_take("tod_teleport_cool_lp", row, secs, 1.0), 300, 8000)[:, 0]
    y, gr = dsp.level(unit(x) * 1.0 + unit(tex) * 0.3, c["lufs"], c["peak"], loop=True)
    return [(y, dict(take=row["name"], seam=dsp.seam_score(y), limiter_gr_db=round(gr, 2)))]


def relay_clunk(data, picks):
    row = best("tod_power_relay", data, picks)[0]
    x = dsp.to_ch(take_audio("tod_power_relay", row), 2)
    x = dsp.trim_tail(dsp.trim_head(x, -40.0), -50.0, 0.02)
    x = dsp.fit_len(dsp.dc_block(x), min(len(x), int(0.6 * SR)))
    x = dsp.fade_out(dsp.fade_in(x, 0.002), 0.12)
    return x / (np.max(np.abs(x)) + 1e-9), row["name"]


# the wave's relays: they trip down the tower with it (the wave lights 51 floors in 12 s): close, then farther and darker
RELAYS = [(0.10, 1.00, 9000), (1.30, 0.85, 7000), (2.60, 0.72, 5200), (4.00, 0.60, 4000), (5.50, 0.48, 3000),
          (7.10, 0.38, 2300), (8.80, 0.29, 1800), (10.50, 0.22, 1400)]


def design_power_wave(data, picks):
    """THE WAVE (13.5 s = TOD_FALL_WAVE_SECS 12 + TOD_FALL_WAVE_HOLD_SECS 1.5, 2D to everyone at its start): the surge
    take RECEDES down the tower - a lowpass gliding 12 kHz -> 1.6 kHz and the level falling 8 dB over the 12 s - its
    relays trip in step, each farther and darker; the last 1.5 s draw a low swell up into the grid-online moment
    (tod_power_online, played on the set_lighting_state(0) frame, carries the hit)."""
    c = CUES["tod_power_wave"]
    row = best("tod_power_wave", data, picks)[0]
    n = int(round(c["secs"] * SR))
    x = dsp.to_ch(take_audio("tod_power_wave", row), 2)
    x = dsp.dc_block(dsp.trim_head(x, -40.0))
    x = dsp.fit_len(x, n)
    x = dsp.tilt_lowpass(x, 12000.0, 1600.0)
    t = np.arange(n) / SR
    g = 10 ** (-8.0 * np.clip(t / 12.0, 0, 1) / 20)
    x = x * g[:, None]
    clunk, rname = relay_clunk(data, picks)
    pk = np.max(np.abs(x)) + 1e-9
    for t0, gain, lp in RELAYS:
        cl = dsp.band(clunk, 40, lp)
        x = dsp.place(x, cl * gain * 0.8 * pk, t0)
    # the anticipation: a low swell (a 41 Hz + 82 Hz hum) rising over the last 1.5 s, cut at the end
    m = int(1.5 * SR)
    tt = np.arange(m) / SR
    sw = (np.sin(2 * np.pi * 41 * tt) + 0.5 * np.sin(2 * np.pi * 82 * tt)) * (tt / 1.5) ** 2
    x = dsp.place(x, dsp.stereo_spread(sw[:, None], 7) * 0.35 * pk, c["secs"] - 1.5)
    x = dsp.fade_in(x, 0.003)
    x = dsp.fade_out(x, 0.02, squared=False)
    x[-1] = 0.0
    y, gr = dsp.level(x, c["lufs"], c["peak"])
    return [(y, dict(take=row["name"], relay=rname, limiter_gr_db=round(gr, 2)))]


def design_power_online(data, picks):
    """THE GRID ONLINE (2D, on the lighting frame): the best slam take with a written sub thump under its hit (a 62 ->
    34 Hz drop), so the moment the whole tower lights is felt in every player's chest"""
    c = CUES["tod_power_online"]
    row = best("tod_power_online", data, picks)[0]
    x = dsp.to_ch(take_audio("tod_power_online", row), 2)
    x = dsp.dc_block(dsp.trim_head(x, -40.0))
    x = dsp.trim_tail(x)
    lo, hi = c["span"]
    x = dsp.fit_len(x, max(int(lo * SR), min(len(x), int(hi * SR))))
    pk = np.max(np.abs(x)) + 1e-9
    x = dsp.place(x, dsp.sub_drop(1.6, 62.0, 34.0, 0.5) * 0.7 * pk, 0.0)
    x = dsp.fade_in(x, 0.002)
    x = dsp.fade_out(x, c["fade_out"])
    x[-1] = 0.0
    y, gr = dsp.level(x, c["lufs"], c["peak"])
    return [(y, dict(take=row["name"], limiter_gr_db=round(gr, 2)))]


# LOCKSTEP _tod_power_terminal.gsc: TOD_PBOOT_DARK 0.15, TOD_PBOOT_STEP 0.35 -> the frames at 0.15 / 0.50 / 0.85,
# the screen ON at 1.20, the dial's TOD_PDIAL_SPIN 1.4 = the cue's length
BOOT_BLIPS = [(0.15, 1320.0, 1480.0), (0.50, 1480.0, 1660.0), (0.85, 1660.0, 1980.0)]
BOOT_ON = 1.20


def design_power_boot(data, picks):
    """THE TERMINAL BOOT (3D at the screen, 1.4 s): the charging-whine take under three confirm blips, one on each
    RESTART GRID frame, each a step higher, and a two-note 'online' chirp when the screen comes on"""
    c = CUES["tod_power_boot"]
    row = best("tod_power_boot", data, picks)[0]
    n = int(round(c["secs"] * SR))
    x = dsp.to_ch(take_audio("tod_power_boot", row), 1)
    x = dsp.dc_block(dsp.trim_head(x, -40.0))
    x = dsp.fit_len(x, n)
    x = dsp.fade_out(x, 0.25)
    pk = np.max(np.abs(x)) + 1e-9
    for t0, f0, f1 in BOOT_BLIPS:
        x = dsp.place(x, dsp.blip(0.09, f0, f1, decay=0.035)[:, None] * 0.55 * pk, t0)
    x = dsp.place(x, dsp.blip(0.08, 1980.0, decay=0.03)[:, None] * 0.5 * pk, BOOT_ON)
    x = dsp.place(x, dsp.blip(0.14, 2640.0, decay=0.06)[:, None] * 0.5 * pk, BOOT_ON + 0.07)
    x = dsp.fade_in(x, 0.003)
    x = dsp.fade_out(x, c["fade_out"])
    x[-1] = 0.0
    y, gr = dsp.level(x, c["lufs"], c["peak"])
    return [(y, dict(take=row["name"], blips=[b[0] for b in BOOT_BLIPS], on=BOOT_ON, limiter_gr_db=round(gr, 2)))]


# ---- THE NEAR MISS + HOT STREAK EIGHT: HYBRIDS ------------------------------------------------------------------
# The placeholders (tools/near_miss/make_sounds.py) were DESIGNED: notes in the card-reveal kit's key, a ratchet that
# closes in, a fifth that hovers, a C-E-G-C bell burst, a G5 -> D6 stinger (docs/201). What they lacked was a real
# recorded surface - every texture was filtered white noise. So each authored cue keeps its musical SPINE, rebuilt
# from the placeholder's own building blocks (imported, never copied), and takes its TEXTURE from the recorded takes:
# the reel, the air, the swell, the crack, the sparkle, the fire. Exact lengths (the pull and spin are timed to them),
# levelled to the placeholders' own targets (compression up to 4:1, the limiter never past 6 dB).
_NM = None


def nm():
    global _NM
    if _NM is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("near_synth", os.path.join(REPO, "tools", "near_miss", "make_sounds.py"))
        _NM = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_NM)
    return _NM


def take_row(name, take, data):
    for r in data.get(name, []):
        if r["name"] == take:
            return r
    raise SystemExit("%s: %s is not a take - generate it first" % (name, take))


def unit(x):
    """x scaled to unit RMS over its live part (frames within 40 dB of its peak)"""
    x = np.asarray(x, dtype=np.float64)
    m = x if x.ndim == 1 else dsp.mono(x)
    e = dsp.envelope(m, 0.01)
    live = e[dsp.db(e / (e.max() + 1e-20)) > -40]
    r = np.sqrt(np.mean(live ** 2)) if live.size else 1.0
    return x / (r + 1e-12)


def tex(name, take, n, data, tail=False):
    """a take as a mono texture of exactly n samples: from its first sound (head) or ending on its last (tail - a
    reversed decay, so it RISES into the cut)"""
    x = dsp.mono(take_audio(name, take_row(name, take, data)))
    x = dsp.dc_block(x)[:, 0]
    if tail:
        x = dsp.mono(dsp.trim_tail(x[:, None] if x.ndim == 1 else x, -50.0, 0.0))
        x = x[-n:] if len(x) >= n else np.concatenate([np.zeros(n - len(x)), x])
    else:
        x = dsp.mono(dsp.trim_head(x[:, None], -40.0))
        x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])
    return x


def near_finish(name, x, info):
    c = CUES[name]
    n = int(round(c["secs"] * SR))
    x = dsp.fit_len(np.asarray(x)[:, None], n)
    x = dsp.dc_block(x, c.get("hp", 16.0))
    x = dsp.fade_in(x, 0.003)
    x = dsp.fade_out(x, c["fade_out"], squared=(c["fit"] != "cut"))
    x[-1] = 0.0
    y, gr, ratio = dsp.level_dense(x, c["lufs"], c["peak"], max_ratio=c["ratio"])
    info.update(limiter_gr_db=round(gr, 2), ratio=ratio)
    return [(y, info)]


def design_spin_teeter(data, picks):
    """STOPPED SHORT: the strained tone climbing a minor third on a tightening tremolo (the placeholder's), its
    ratchet's closing-in clicks quietly underneath for the timing, and the RECORDED reel straining on top"""
    N = nm()
    n, t = N.timeline(0.50)
    gaps = np.linspace(0.055, 0.018, 12)
    times = np.concatenate([[0.0], np.cumsum(gaps)[:-1]])
    ratchet = N.clicks(n, 101, times, 900, 5000, 0.8)
    ph = N.glide(t, 440.0, 523.25, 0.45)
    tone = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * (0.6 + 0.4 * np.sin(2 * np.pi * (9 + 14 * t) * t)) * N.smooth(t / 0.12)
    reel = tex("tod_spin_teeter", "take_1", n, data)
    x = unit(tone) * 0.6 + unit(ratchet) * 0.3 + unit(reel) * 0.8
    return near_finish("tod_spin_teeter", x, dict(take="take_1 + spine"))


def design_spin_near(data, picks):
    """THE SO CLOSE: B5, then F5 bending down a semitone (the placeholder's notes) over a RECORDED breath of air"""
    N = nm()
    n, t = N.timeline(0.80)
    x = N.strike(n, 0.0, 987.77, 0.30, 0.75)
    i0 = int(0.14 * SR)
    k = t[i0:] - t[i0]
    ph = N.glide(k, 698.46, 659.26, 0.45)
    second = np.zeros(n)
    second[i0:] = (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.18 * np.sin(2.76 * ph)) * np.exp(-k / 0.28) * N.smooth(k / 0.006)
    notes = x + 0.8 * second
    air = np.concatenate([np.zeros(int(0.10 * SR)), tex("tod_spin_near", "take_3", n - int(0.10 * SR), data)])
    air = air * np.exp(-np.maximum(t - 0.10, 0) / 0.35)
    return near_finish("tod_spin_near", unit(notes) * 1.0 + unit(air) * 0.4, dict(take="take_3 + spine"))


def design_pull_reach(data, picks):
    """THE REACH: the tone up a fifth hovering on a 14 Hz tremolo (the placeholder's) over the RECORDED swell
    (a reversed boom, rising into the cut, held at full tension)"""
    N = nm()
    n, t = N.timeline(0.66)
    ph = N.glide(t, 329.63, 493.88, 0.35)
    trem = np.where(t < 0.35, 1.0, 0.65 + 0.35 * np.sin(2 * np.pi * 14 * (t - 0.35)))
    tone = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * trem * N.smooth(t / 0.05)
    swell = tex("tod_pull_reach", "take_2", n, data, tail=True)
    return near_finish("tod_pull_reach", unit(tone) * 0.6 + unit(swell) * 0.9, dict(take="take_2 + spine"))


def design_pull_reach_fail(data, picks):
    """SO CLOSE: the swell let go - the tone gliding 520 -> 170 Hz (the placeholder's) into a RECORDED muffled whump"""
    N = nm()
    n, t = N.timeline(0.45)
    ph = N.glide(t, 520.0, 170.0, 0.3)
    tone = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * N.env(t, 0.004, 0.16)
    whump = tex("tod_pull_reach_fail", "take_2", n, data)
    return near_finish("tod_pull_reach_fail", unit(tone) * 0.75 + unit(whump) * 0.6, dict(take="take_2 + spine"))


def design_pull_break(data, picks):
    """BREAK THROUGH: the C6-E6-G6-C7 bell burst and the 60 Hz thump (the placeholder's) inside a RECORDED crystal
    shatter, a RECORDED sparkle trailing it"""
    N = nm()
    n, t = N.timeline(0.90)
    bells = np.zeros(n)
    for i, f in enumerate((1046.50, 1318.51, 1567.98, 2093.0)):
        bells += N.strike(n, 0.04 + 0.055 * i, f, 0.32, 0.55)
    thump = np.sin(2 * np.pi * 60 * t) * N.env(t, 0.003, 0.12)
    crack = tex("tod_pull_break", "take_1", n, data)
    i1 = int(0.15 * SR)
    sparkle = np.concatenate([np.zeros(i1), tex("tod_pull_break", "take_2", n - i1, data)])
    x = unit(bells) * 0.75 + unit(thump) * 0.35 + unit(crack) * 0.8 + unit(sparkle) * 0.3
    return near_finish("tod_pull_break", x, dict(take="take_1 + take_2 + spine"))


def design_heat_up(data, picks):
    """HEATING UP: the RECORDED ignition, its RECORDED crackle underneath"""
    n = int(round(0.80 * SR))
    x = unit(tex("tod_heat_up", "take_1", n, data)) * 1.0 + unit(tex("tod_heat_up", "take_3", n, data)) * 0.15
    return near_finish("tod_heat_up", x, dict(take="take_1 + take_3"))


def design_heat_fire(data, picks):
    """ON FIRE: the RECORDED fireball and blaze, crowned by the G5 -> D6 stinger (the placeholder's)"""
    N = nm()
    n, t = N.timeline(1.30)
    stinger = N.strike(n, 0.30, 784.0, 0.35, 0.5) + N.strike(n, 0.42, 1174.66, 0.45, 0.6)
    blaze = tex("tod_heat_fire", "take_2", n, data)
    return near_finish("tod_heat_fire", unit(blaze) * 1.0 + unit(stinger) * 0.45, dict(take="take_2 + stinger"))


def design_heat_out(data, picks):
    """THE STREAK ENDS: the RECORDED snuff-out hiss over the tone gliding 600 -> 200 Hz (the placeholder's)"""
    N = nm()
    n, t = N.timeline(0.70)
    ph = N.glide(t, 600.0, 200.0, 0.5)
    tone = np.sin(ph) * N.env(t, 0.01, 0.2)
    hiss = tex("tod_heat_out", "take_1", n, data)
    return near_finish("tod_heat_out", unit(hiss) * 1.0 + unit(tone) * 0.25, dict(take="take_1 + spine"))


DESIGNS = {
    "tod_spin_teeter": design_spin_teeter,
    "tod_spin_near": design_spin_near,
    "tod_pull_reach": design_pull_reach,
    "tod_pull_reach_fail": design_pull_reach_fail,
    "tod_pull_break": design_pull_break,
    "tod_heat_up": design_heat_up,
    "tod_heat_fire": design_heat_fire,
    "tod_heat_out": design_heat_out,
    "tod_tier_sting": design_tier_sting,
    "tod_amb_tower_wind": (lambda d, p: bed_from_two("tod_amb_tower_wind", d, p)),
    "tod_amb_city_far": (lambda d, p: bed_from_two("tod_amb_city_far", d, p)),
    "tod_shop_hum": design_shop_hum,
    "tod_teleport_idle_lp": design_tp_idle,
    "tod_teleport_cool_lp": design_tp_cool,
    "tod_power_wave": design_power_wave,
    "tod_power_online": design_power_online,
    "tod_power_boot": design_power_boot,
}


def render_cue(name, data, picks):
    """-> [(array, info)] the shipped files, first = the plain stem"""
    c = CUES[name]
    if c["kind"] == "design":
        return DESIGNS[name](data, picks)
    if c["kind"] == "loop":
        return [render_loop(name, best(name, data, picks)[0])]
    if c["kind"] == "oneshot":
        return render_variants(name, best(name, data, picks, c["variants"]))
    raise ValueError(name)


def file_rel(name, k):
    c = CUES[name]
    return "%s/%s%s.wav" % (c["dir"], c["stem"], "" if k == 0 else "_%d" % (k + 1))


def pick(cues, out_root):
    data = load(TAKES_JSON, {})
    picks = load(PICKS_JSON, {})
    man_path = os.path.join(out_root, MANIFEST_REL.replace("/", os.sep))
    man = load(man_path, {})
    for name in cues:
        c = CUES[name]
        if c["kind"] in ("stock", "part"):
            continue
        outs = render_cue(name, data, picks)
        files = []
        for k, (y, info) in enumerate(outs):
            b = dsp.encode(y)
            rel = file_rel(name, k)
            p = os.path.join(out_root, "sound_assets", "tod", rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            if not (os.path.exists(p) and open(p, "rb").read() == b):
                open(p, "wb").write(b)
            info.update(file=rel, sha256=dsp.sha256(b), channels=y.shape[1], frames=len(y), secs=round(len(y) / SR, 4),
                        lufs=round(dsp.lufs(y), 2), peak_db=round(float(dsp.db(np.max(np.abs(y)))), 2))
            files.append(info)
            extra = ""
            if "seam" in info:
                extra = " seam step %.2f jump %.2f dB" % (info["seam"]["step"], info["seam"]["jump_db"])
            print("%-30s %-44s %6.3fs %dch %6.2f LUFS pk %6.2f lim %4.1f dB%s" % (
                name, rel, info["secs"], info["channels"], info["lufs"], info["peak_db"], info.get("limiter_gr_db", 0), extra))
        man[name] = dict(files=files, kind=c["kind"])
    man = {n: man[n] for n in ORDER if n in man}
    save(man_path, man)
    write_outputs(out_root, man)


def write_outputs(out_root, man):
    for t, text in tables_text(REPO, man).items():
        write_text(os.path.join(out_root, "sound", "aliases", t), text)
    for rel, fn in GDTS.items():
        write_text(os.path.join(out_root, rel.replace("/", os.sep)), fn())
    authored = {n: {"sha256": man[n]["files"][0]["sha256"], "frames": man[n]["files"][0]["frames"],
                    "by": "tools/sfx/w2c_sounds/make_sounds.py"} for n in ORDER if CUES[n].get("near") and n in man}
    save(os.path.join(out_root, AUTHORED_REL.replace("/", os.sep)), authored)
    print("tables + GDTs + authored.json written under", out_root)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cur = open(path, encoding="utf-8", newline="").read() if os.path.exists(path) else None
    if cur != text:
        open(path, "w", encoding="utf-8", newline="").write(text)


# ================================================================================================================
# THE GATE
# ================================================================================================================
def check(root):
    bad = []
    man = load(os.path.join(root, MANIFEST_REL.replace("/", os.sep)), None)
    if not man:
        print("W2C SOUNDS STALE: no manifest - " + FIX)
        sys.exit(1)
    nfiles = 0
    for name in ORDER:
        c = CUES[name]
        if c["kind"] in ("stock", "part"):
            for fs in c.get("files", []):
                if not any(os.path.exists(os.path.join(b, "sound_assets", fs.replace("\\", os.sep)))
                           for b in (root, r"C:\BO3Tools\TOD2Cybercity")):
                    bad.append("stock wav missing: " + fs)
            continue
        info = man.get(name)
        if not info:
            bad.append("%s not shipped" % name)
            continue
        if c["kind"] == "oneshot" and len(info["files"]) != c["variants"]:
            bad.append("%s ships %d files (want %d)" % (name, len(info["files"]), c["variants"]))
        for f in info["files"]:
            nfiles += 1
            p = os.path.join(root, "sound_assets", "tod", f["file"].replace("/", os.sep))
            if not os.path.exists(p):
                bad.append("missing " + f["file"])
                continue
            b = open(p, "rb").read()
            if dsp.sha256(b) != f["sha256"]:
                bad.append("changed " + f["file"])
            try:
                with wave.open(io.BytesIO(b)) as w:
                    if (w.getnchannels(), w.getframerate(), w.getsampwidth()) != (c["ch"], SR, 2):
                        bad.append("%s is not %d ch 48 kHz 16-bit" % (f["file"], c["ch"]))
                    nf = w.getnframes()
                    if c["secs"] is not None and (c["kind"] != "design" or c.get("near") or name in EXACT) \
                            and nf != int(round(c["secs"] * SR)):
                        bad.append("%s is %d frames, the timing wants %d" % (f["file"], nf, int(round(c["secs"] * SR))))
                    if c["span"] and not (c["span"][0] - 0.01 <= nf / SR <= c["span"][1] + 0.01):
                        bad.append("%s is %.2f s (want %.2f - %.2f)" % (f["file"], nf / SR, c["span"][0], c["span"][1]))
            except wave.Error as e:
                bad.append("%s unreadable: %s" % (f["file"], e))
    want_tables = tables_text(root, man)
    for t, text in want_tables.items():
        p = os.path.join(root, "sound", "aliases", t)
        cur = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if cur != text:
            bad.append("sound/aliases/%s differs from the generated table" % t)
    for rel, fn in GDTS.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        cur = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if cur != fn():
            bad.append("%s differs from the generated GDT" % rel)
    authored = load(os.path.join(root, AUTHORED_REL.replace("/", os.sep)), {})
    for name in ORDER:
        if CUES[name].get("near") and name in man and authored.get(name, {}).get("sha256") != man[name]["files"][0]["sha256"]:
            bad.append("%s does not name %s's sha" % (AUTHORED_REL, name))
    try:
        szc = json.loads(open(os.path.join(root, SZC_REL.replace("/", os.sep)), encoding="utf-8-sig").read())
        loaded = {str(s.get("Filename", "")).lower() for s in szc.get("Sources", []) if isinstance(s, dict) and s.get("Type") == "ALIAS"}
        for t in TABLES:
            if t.lower() not in loaded:
                bad.append("%s not loaded by the sound zone config" % t)
    except (OSError, ValueError) as e:
        bad.append("szc unreadable: %s" % e)
    for alias, rel in WIRED.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        txt = open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
        if '"%s"' % alias not in txt:
            bad.append('%s does not play "%s"' % (rel, alias))
    # the generated neighbours: the ambience anchors and the bolt-impact effects
    import gen_amb_data, gen_fx
    bad += gen_amb_data.check(root)
    bad += gen_fx.check(root)
    if bad:
        print("W2C SOUNDS STALE: " + "; ".join(bad[:10]) + (" (+%d more)" % (len(bad) - 10) if len(bad) > 10 else "") + " - " + FIX)
        sys.exit(1)
    rows = sum(t.count("\n") - 1 for t in want_tables.values())
    print("W2C SOUNDS OK: %d cues, %d files, %d alias rows in %d tables, 2 GDTs, amb anchors + bolt fx current"
          % (len(man), nfiles, rows, len(TABLES)))


# ================================================================================================================
# REVIEW: a spectrogram sheet (OLD vs NEW where something shipped before) + a listening desk
# ================================================================================================================
def spectro_panel(x, label, sub, maxs, w=760, h=120, wh=36):
    from PIL import Image, ImageDraw
    m = dsp.mono(x)
    n, hop = 2048, 256
    pad = np.concatenate([np.zeros(n // 2), m, np.zeros(n)])
    frames = np.array([pad[i:i + n] * np.hanning(n) for i in range(0, max(1, len(m)), hop)])
    S = np.abs(np.fft.rfft(frames, axis=1)).T + 1e-9
    f = np.fft.rfftfreq(n, 1 / SR)
    rows = np.geomspace(30, 16000, h)
    D = 20 * np.log10(S[np.clip(np.searchsorted(f, rows), 0, len(f) - 1)] / S.max())
    D = np.clip((D + 80) / 80, 0, 1)[::-1]
    lut = np.array([[int(255 * min(1, 2.2 * v)), int(255 * max(0, min(1, 2 * v - 0.5))), int(255 * max(0, 3 * v - 2))]
                    for v in np.linspace(0, 1, 256)], dtype=np.uint8)
    cols = max(1, int(w * (len(m) / SR) / maxs))
    img = Image.fromarray(lut[(D * 255).astype(int)]).resize((min(cols, w), h))
    c = Image.new("RGB", (w + 330, h + wh + 4), (16, 16, 20))
    c.paste(img, (0, 0))
    d = ImageDraw.Draw(c)
    seg = max(1, len(m) // max(1, min(cols, w)))
    y0 = h + 4 + wh // 2
    for i in range(min(cols, w)):
        a = np.max(np.abs(m[i * seg:(i + 1) * seg])) if (i + 1) * seg <= len(m) else 0.0
        d.line([(i, y0 - int(a * (wh // 2 - 1))), (i, y0 + int(a * (wh // 2 - 1)))], fill=(110, 190, 250))
    d.text((w + 8, 6), label, fill=(255, 255, 255))
    for j, line in enumerate(sub):
        d.text((w + 8, 24 + 14 * j), line, fill=(190, 190, 190))
    return c


def review(out_root):
    from PIL import Image
    man = load(os.path.join(out_root, MANIFEST_REL.replace("/", os.sep)), {})
    out_dir = os.path.join(REPO, "art", "generated", "W2C-sounds")
    os.makedirs(out_dir, exist_ok=True)
    panels = []
    desk = ["<!doctype html><meta charset=utf-8><title>W2C sounds desk</title><style>body{font:14px system-ui;background:#111;"
            "color:#ddd;margin:24px}h2{color:#9ef;margin:22px 0 4px}td{padding:3px 10px;border-bottom:1px solid #333}"
            "audio{height:26px}</style><h1>Wave-2 sounds: OLD (shipped now) vs NEW (staged)</h1>"]
    for name in ORDER:
        c = CUES[name]
        if name not in man:
            continue
        desk.append("<h2>%s <small>(%s, %s)</small></h2><table>" % (name, c["pack"], c["kind"]))
        for k, f in enumerate(man[name]["files"]):
            new = os.path.join(out_root, "sound_assets", "tod", f["file"].replace("/", os.sep))
            old = os.path.join(REPO, "sound_assets", "tod", f["file"].replace("/", os.sep))
            maxs = max(1.0, min(14.0, f["secs"] + 0.2))
            if os.path.exists(old) and k == 0:
                xo = dsp.decode(old, 1)
                panels.append(spectro_panel(xo, name + "  [OLD - shipped now]", ["%.3f s  %.1f LUFS" % (len(xo) / SR, dsp.lufs(xo))], maxs))
                desk.append("<tr><td>OLD</td><td></td><td><audio controls src='%s'></audio></td></tr>" % os.path.relpath(old, out_dir).replace("\\", "/"))
            x = dsp.decode(new, 1)
            sub = ["%s  %.3f s  %d ch" % (f["file"], f["secs"], f["channels"]), "%.1f LUFS  peak %.1f  take %s" % (f["lufs"], f["peak_db"], f.get("take"))]
            if "seam" in f:
                sub.append("loop seam step %.2f  jump %.2f dB" % (f["seam"]["step"], f["seam"]["jump_db"]))
            panels.append(spectro_panel(x, name + ("  [NEW]" if k == 0 else "  [NEW v%d]" % (k + 1)), sub, maxs))
            desk.append("<tr><td>NEW</td><td>%s</td><td><audio controls src='%s'></audio></td></tr>" % (f["file"], os.path.relpath(new, out_dir).replace("\\", "/")))
        desk.append("</table>")
    W = panels[0].width
    per = 18
    for s in range(0, len(panels), per):
        chunk = panels[s:s + per]
        sheet = Image.new("RGB", (W, sum(p.height + 3 for p in chunk)), (0, 0, 0))
        y = 0
        for p in chunk:
            sheet.paste(p, (0, y))
            y += p.height + 3
        sheet.save(os.path.join(out_dir, "_review%s.png" % ("" if s == 0 else "_%d" % (s // per + 1))))
    open(os.path.join(out_dir, "desk.html"), "w", encoding="utf-8").write("\n".join(desk))
    print("review:", out_dir, len(panels), "panels")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="")
    ap.add_argument("--cue", action="append")
    ap.add_argument("--pack", action="append")
    ap.add_argument("--takes", type=int, default=0)
    ap.add_argument("--plan", type=int, default=None)
    ap.add_argument("--out-root", default=REPO)
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cues = a.cue or [n for n in ORDER if not a.pack or CUES[n]["pack"] in a.pack]
    for c in cues:
        if c not in CUES:
            sys.exit("unknown cue " + c)
    if a.check or a.cmd == "check":
        check(os.path.abspath(a.root))
    elif a.cmd == "adopt":
        adopt()
    elif a.cmd == "generate":
        generate(cues, a.takes, a.plan)
    elif a.cmd == "rescore":
        rescore(cues)
    elif a.cmd == "pick":
        pick(cues, os.path.abspath(a.out_root))
    elif a.cmd == "review":
        review(os.path.abspath(a.out_root))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
