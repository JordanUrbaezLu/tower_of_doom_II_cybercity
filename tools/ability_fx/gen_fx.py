"""THE ABILITY EFFECTS (docs/203, 2026-10-02; user: "Tower of Doom 1 has such good
visual effects on the players abilities and I feel this map lacks that interaction
and awesome visuals ... Dash upgrade could use some, The soul pulse is super ugly
and dull ... Breacher explosive jump and heal ... Demon Slayer activation ... how
they look in 3d world from other perspectives too").

Every effect here is GENERATED from a stock BO3 donor in the private tools root:
copied into share/raw/fx/tod/abfx/, filtered to the elements the design wants,
recoloured to the ability's hue (every colorGraph key, brightness kept), alpha
and size scaled, lights re-radiused. Children (runner / fxOnImpact / fxOnDeath /
emission) are copied and recoloured with the parent, under short names
(<parent>_c<N>) because the engine truncates an fx path at 63 characters and a
parent spawning a missing child is an access violation (memory
fx-name-63-char-limit-crashes).

The donors were CHECKED for the gfx_debug_missing_fx stub (several stock effects
in this tools root are stubs: fx_embers_falling_sm, fx_elec_burst_lg_z270_os,
fx_ash_embers_light, fx_fire_debris_xsmall, fx_blood_torso_explo_zmb) - a stub
donor exits here.

Consumer: _tod_ability_fx.csc (every effect by name). LOCKSTEP: the EFFECTS table here, the #precache / level._effect
table in _tod_ability_fx.csc, the zone's `fx,tod/abfx/` lines
(tools/test_ability_fx.js gates all three).

Re-run it; never hand-edit the outputs. `--check` verifies the outputs match a
fresh render (the build gates on it).
"""
import argparse, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "necromancer"))
import make_soul_fx as msf   # recolour_rows / scale_alpha / elements / set_field / elem_name

TOOLS_FX = msf.TOOLS_FX
REPO = os.path.dirname(os.path.dirname(HERE))
OUT_DIR = os.path.join(REPO, "share", "raw", "fx", "tod", "abfx")
OUT_PREFIX = "tod/abfx/"
FX_PATH_MAX = msf.FX_PATH_MAX

# ---- the hues --------------------------------------------------------------------
CYAN   = (0.55, 0.92, 1.00)   # the Cyber Sword / the cyber kit
WHITE  = (0.92, 0.95, 1.00)   # the fists
EMBER  = (1.00, 0.56, 0.18)   # the Gauntlet of Siegfried / the Breacher's fire
SOUL   = msf.TINT             # the Necromancer's blue-grey soul (ONE hue, make_soul_fx's)
DEMON  = (1.00, 0.16, 0.10)   # Demon Slayer
# docs/206 (2026-10-03): the second pass
ARCHER = (0.55, 1.00, 0.62)   # the Archer's bow / draw glow
SHIELD = (0.70, 0.90, 1.00)   # the Breacher's shield (the Lv9 cyber shield's cold white-blue)
RED    = (1.00, 0.12, 0.08)   # the C4's arming light
# the four card rarities (docs/187: COMMON white / RARE blue / EPIC purple / LEGENDARY gold)
RARITY = {1: (0.92, 0.95, 1.00), 2: (0.35, 0.60, 1.00), 3: (0.72, 0.36, 1.00), 4: (1.00, 0.82, 0.30)}

# ---- the recipes -----------------------------------------------------------------
# name: dict(donor, tint, gain, alpha, keep=<predicate on an element block> or None,
#            size=<sprite size multiplier>, light=<light radius multiplier>)
def has(*mats):
    return lambda b: any(('"%s"' % m) in b for m in mats)

def has_not(*mats):
    return lambda b: not any(('"%s"' % m) in b for m in mats)

def is_light(b):
    # a dynamic light element carries no sprite material; its radius graph is non-zero
    m = re.search(r'\n\tlightRadiusGraph ([\d.]+)', b)
    return bool(m) and float(m.group(1)) > 0

def soul_dome_keep(b):
    # the Keeper's 360 attack minus everything ELECTRIC or SOLID (user 2026-09-26: "soul-like,
    # not electricity-like"): the fog dome, the distortion rings, the thin rings, the embers (as
    # soul motes), the sparks and the two lights stay; the lightning beam, the electric
    # shockwaves, the concrete / metal gibs and the debris clump go.
    if is_light(b):
        return True
    return has("gfx_fog_slow_lg_anim_em_i512", "gfx_fog_slow_lg_anim_em", "gfx_fog_slow_md_anim_em",
               "gfx_distort_ring_hvy", "gfx_ring_thin", "gfx_debris_embers_em_i1024",
               "gfx_spark_01_pcloud_em", "gfx_light_incandescent_hot_lg")(b)

def bash_impact_keep(b):
    # the Gravity Spikes ground hit minus its metal gibs (a blade is not a machine): the
    # shockwave, the heavy distortion ring, the crater decal, the fog, the smoke tendrils
    # and the light.
    return has_not("gfx_gib_metal_01_lit", "gfx_gib_metal_02_lit")(b)

def smoke_only(b):
    return has("gfx_smk_whisp_anim_em")(b)

def elem_is(b, *names):
    return msf.elem_name(b) in names

def glow_only(b):
    # a perk glow minus its ring and spike sprites: the soft glow card + the light
    return is_light(b) or elem_is(b, "glow")

def no_models(b):
    # the glass shard burst without its xmodel shards (a model element is a dependency the linker must
    # resolve; the sprites, glints, smoke and the impact line carry the break)
    return not elem_is(b, "model", "glass_model")

def light_only(b):
    return is_light(b)

EFFECTS = {
    # ---- WARRIOR: BASH, the blade dash ------------------------------------------------
    # the streak behind the body for the 400 ms of the dash (3p, j_spine4); one per blade
    "fx_abfx_dash_sword":    dict(donor="dlc1/zmb_weapon/fx_wpn_spike_torso_trail", tint=CYAN,  gain=1.10, alpha=1.0, size=1.35),
    "fx_abfx_dash_gauntlet": dict(donor="dlc1/castle/fx_elec_jumppad_player_trail",  tint=EMBER, gain=1.00, alpha=0.9, size=1.0),
    "fx_abfx_dash_punch":    dict(donor="dlc1/zmb_weapon/fx_wpn_spike_torso_trail", tint=WHITE, gain=0.90, alpha=0.6, size=1.2),
    # the caster's own half: the gold sword's glyph light ramp on the viewmodel (1p, tag_weapon)
    "fx_abfx_dash_vm":       dict(donor="hb/gold_sword/fx_charge_light_ramp_1p",     tint=CYAN,  gain=1.00, alpha=1.0, light=1.3),
    # the end burst, sized to the burst radius (150 / Lv9 225; the donor's shockwave is ~240 u)
    "fx_abfx_bash_impact":     dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit", tint=CYAN, gain=1.00, alpha=1.0, keep=bash_impact_keep, size=150 / 240.0, light=150 / 240.0),
    "fx_abfx_bash_impact_lv9": dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit", tint=CYAN, gain=1.05, alpha=1.0, keep=bash_impact_keep, size=225 / 240.0, light=225 / 240.0),
    # the caster's screen at the burst: the slam's camera arcs, dimmed (1p only)
    "fx_abfx_bash_1p":       dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit_1p", tint=CYAN, gain=0.9, alpha=0.5),

    # ---- NECROMANCER: SOUL PULSE, the dome -------------------------------------------
    # the Keeper's 360 attack as a SOUL wave: four bands (LOCKSTEP make_soul_fx RING_RADII 360/440/520/600;
    # the donor's wave is ~700 u), its two lights re-radiused to the band
    "fx_abfx_pulse_dome0": dict(donor="dlc4/genesis/fx_keeperprot_360_attack", tint=SOUL, gain=1.10, alpha=0.85, keep=soul_dome_keep, size=360 / 700.0, light=360 / 700.0),
    "fx_abfx_pulse_dome1": dict(donor="dlc4/genesis/fx_keeperprot_360_attack", tint=SOUL, gain=1.10, alpha=0.85, keep=soul_dome_keep, size=440 / 700.0, light=440 / 700.0),
    "fx_abfx_pulse_dome2": dict(donor="dlc4/genesis/fx_keeperprot_360_attack", tint=SOUL, gain=1.10, alpha=0.85, keep=soul_dome_keep, size=520 / 700.0, light=520 / 700.0),
    "fx_abfx_pulse_dome3": dict(donor="dlc4/genesis/fx_keeperprot_360_attack", tint=SOUL, gain=1.10, alpha=0.85, keep=soul_dome_keep, size=600 / 700.0, light=600 / 700.0),
    # the caster's own half: a soul mist crossing the camera, NEVER a flash (docs/necro_visibility_fix:
    # the caster-centred burst whitened the view) - the slam's camera smoke only, dim
    "fx_abfx_pulse_1p":    dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit_1p", tint=SOUL, gain=0.8, alpha=0.4, keep=smoke_only),

    # ---- BREACHER: EXPLOSIVE FUSION -----------------------------------------------------
    "fx_abfx_fusion_launch":  dict(donor="dlc4/genesis/fx_jumppad_launch",            tint=EMBER, gain=1.10, alpha=1.0, light=1.4),
    "fx_abfx_fusion_trail":   dict(donor="dlc1/castle/fx_elec_jumppad_player_trail",  tint=EMBER, gain=1.00, alpha=0.9, size=1.1),
    "fx_abfx_fusion_land":    dict(donor="dlc5/moon/fx_moon_jump_pad_dust_ground",    tint=(1.0, 0.86, 0.7), gain=1.0, alpha=1.0, size=1.2),
    "fx_abfx_fusion_heal":    dict(donor="zombie/fx_bgb_burned_out_3p_zmb",            tint=EMBER, gain=1.10, alpha=0.9),
    "fx_abfx_fusion_heal_1p": dict(donor="zombie/fx_bgb_burned_out_1p_zmb",            tint=EMBER, gain=1.00, alpha=0.7),

    # ---- WARRIOR: DEMON SLAYER ------------------------------------------------------------
    "fx_abfx_demon_aura":  dict(donor="dlc1/castle/fx_keeper_ghost_ambient_torso", tint=DEMON, gain=1.15, alpha=1.0, size=1.1),
    "fx_abfx_demon_light": dict(donor="acc/light/fx_perk_glow_red",               tint=DEMON, gain=1.00, alpha=1.0, light=1.1),
    "fx_abfx_demon_on":    dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=DEMON, gain=1.15, alpha=1.0, size=1.2),
    "fx_abfx_demon_on_1p": dict(donor="zombie/fx_bgb_burned_out_1p_zmb",          tint=DEMON, gain=1.00, alpha=0.75),

    # ---- docs/206: THE SECOND PASS (2026-10-03) ----------------------------------------------------
    # CYBER SMASH, the air dive: the landing mark on the floor the dive traced (the Archer's charge ring,
    # looping, on a server carrier for the dive's length) + the streak rides the sword dash's effect.
    "fx_abfx_dive_ring":   dict(donor="tod/archer/fx_tod_archer_charge",          tint=CYAN,  gain=1.10, alpha=0.9, size=1.5, light=1.3),
    "fx_abfx_dive_trail":  dict(donor="dlc1/castle/fx_elec_jumppad_player_trail",  tint=CYAN,  gain=1.05, alpha=0.9, size=1.0),
    # CYBER SMASH charged: the glow a TEAMMATE sees on the blade hand (the perk glow's soft card + light,
    # small), and the one-shot flash when it charges (the burned-out burst, cyan, small).
    "fx_abfx_sword_glow":  dict(donor="acc/light/fx_perk_glow_teal",              tint=CYAN,  gain=1.00, alpha=0.8, keep=glow_only, size=0.32, light=0.55),
    "fx_abfx_sword_charged": dict(donor="zombie/fx_bgb_burned_out_3p_zmb",        tint=CYAN,  gain=1.10, alpha=0.9, size=0.7),
    # INVISIBILITY CLOAK: the vanish (soul motes imploding) and the reappear (the same burst, smaller).
    "fx_abfx_cloak_on":    dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=SOUL,  gain=1.10, alpha=1.0, size=1.15),
    "fx_abfx_cloak_off":   dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=SOUL,  gain=0.90, alpha=0.8, size=0.9),
    # A CARD TAKEN: a rarity-coloured burst on the body, growing with the rarity; the LEGENDARY adds a
    # one-shot gold light (the Gravity Spikes ground hit's light, alone).
    "fx_abfx_card_1":      dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=RARITY[1], gain=0.95, alpha=0.8, size=0.85),
    "fx_abfx_card_2":      dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=RARITY[2], gain=1.05, alpha=0.9, size=1.0),
    "fx_abfx_card_3":      dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=RARITY[3], gain=1.10, alpha=1.0, size=1.2),
    "fx_abfx_card_4":      dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=RARITY[4], gain=1.20, alpha=1.0, size=1.45),
    "fx_abfx_card_light":  dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit",   tint=RARITY[4], gain=1.00, alpha=1.0, keep=light_only, light=0.9),
    # RIOT SHIELD: the break (glass shards, glints, smoke, the impact line; no xmodel shards) and the
    # return (a cold glow pulse on the body).
    "fx_abfx_shield_break": dict(donor="destruct/fx_dest_glass_shard_impact_burst", tint=SHIELD, gain=1.05, alpha=1.0, keep=no_models, size=1.1),
    "fx_abfx_shield_back": dict(donor="zombie/fx_bgb_burned_out_3p_zmb",          tint=SHIELD, gain=1.00, alpha=0.9, size=1.0),
    # STICKY C4 armed: a red light that BLINKS (the perk glow's light alone, one instance at a time, its
    # intensity graph rewritten to a 120 ms flash each second).
    "fx_abfx_c4_blink":    dict(donor="acc/light/fx_perk_glow_red",               tint=RED,   gain=1.00, alpha=1.0, keep=light_only, light=0.55, blink=True),
    # PIERCING: the through-hit on each pierced zombie (the knife flesh hit, as is).
    "fx_abfx_pierce":      dict(donor="impacts/fx_flesh_hit_knife_zmb",           tint=None,  gain=1.00, alpha=1.0),
    # THE BOW at full draw: a glow on the viewmodel (the sword's charge light ramp in the Archer's green).
    "fx_abfx_draw_vm":     dict(donor="hb/gold_sword/fx_charge_light_ramp_1p",    tint=ARCHER, gain=1.00, alpha=1.0, light=1.0),
    # THE BLADES' HITS (gen_tod_twins meleeImpactEffect on cc_gauntlet / cc_gold_sword; the punch keeps
    # the Origins fist puff): an ember spark burst for the gauntlet, a cold spark burst for the sword.
    "fx_abfx_gauntlet_hit": dict(donor="electric/fx_elec_sparks_burst_xsm_omni_blue_os", tint=EMBER, gain=1.10, alpha=1.0, size=1.2),
    "fx_abfx_sword_hit":   dict(donor="electric/fx_elec_sparks_burst_xsm_omni_blue_os", tint=CYAN,  gain=1.10, alpha=1.0, size=1.3),
    # THE CLUSTER's top-tier pop with a LIGHT (the Fuse bomblet burst + the Gravity Spikes hit's one-shot
    # light, ember): the tier-3 pop was the one burst in the kit with no light.
    "fx_abfx_cl_pop_t3":   dict(donor="tod/fuse/fx_tod_fuse_bomblet_exp",          tint=None,  gain=1.00, alpha=1.0,
                                extra=[dict(donor="dlc1/zmb_weapon/fx_wpn_spike_grnd_hit", keep=light_only, tint=EMBER, light=0.45)]),
}

REF_RE = msf.REF_RE
RUNNER_RE = msf.RUNNER_RE


def scale_sizes(text, mult, key_re=r'(?:sizeGraph0|sizeGraph1)'):
    if mult == 1.0:
        return text
    return re.sub(r'(\n\t%s )([\d.]+)' % key_re,
                  lambda m: "%s%.6f" % (m.group(1), float(m.group(2)) * mult), text)


def scale_lights(text, mult):
    if mult == 1.0:
        return text
    return re.sub(r'(\n\tlightRadiusGraph )([\d.]+)',
                  lambda m: "%s%.6f" % (m.group(1), float(m.group(2)) * mult), text)


def blink_light(text, nl):
    """the perk glow's light, one instance at a time (spawnLooping = its life), its intensity a 120 ms
    flash each second: the C4's arming light"""
    _, head, blocks = msf.elements(text)
    out = []
    for b in blocks:
        if is_light(b):
            b = msf.set_field(b, "spawnLooping", "1000 0")
            b = msf.set_field(b, "lifeSpanMsec", "1000 0")
            b = msf.set_graph(b, "lightIntensityGraph", 1.0,
                              [(0.0, 0.0), (0.02, 1.0), (0.12, 1.0), (0.16, 0.0), (1.0, 0.0)], nl)
        out.append(b)
    return head + nl.join(x.rstrip() + nl for x in out)


def splice_elements(text, extra, stats, out_name):
    """append elements from another donor (filtered, recoloured, lights scaled) to the end of `text`"""
    nl, head, blocks = msf.elements(text)
    for i, ex in enumerate(extra):
        src = os.path.join(TOOLS_FX, ex["donor"].replace("/", os.sep) + ".efx")
        if not os.path.exists(src):
            sys.exit("extra donor %s missing from the tools root" % ex["donor"])
        with open(src, "r", encoding="latin-1", newline="") as f:
            t2 = f.read()
        if t2.count("gfx_debug_missing_fx"):
            sys.exit("extra donor %s is a stub" % ex["donor"])
        _, _, b2 = msf.elements(t2)
        if ex.get("keep"):
            b2 = [b for b in b2 if ex["keep"](b)]
        if not b2:
            sys.exit("extra donor %s kept no elements" % ex["donor"])
        taken = set(msf.elem_name(b) for b in blocks)
        fixed = []
        for b in b2:
            n = msf.elem_name(b)
            if n in taken:
                b = b.replace('\tname "%s"' % n, '\tname "%s_x%d"' % (n, i), 1)
            fixed.append(b)
        joined = nl.join(b.rstrip() + nl for b in fixed)
        if ex.get("tint") is not None:
            joined = msf.recolour_rows(joined, ex.get("gain", 1.0), ex["tint"])
        joined = scale_lights(joined, ex.get("light", 1.0))
        blocks.append(joined.rstrip() + nl)
        stats[out_name + "+" + str(i)] = (ex["donor"], None, len(b2))
    return head + nl.join(b.rstrip() + nl for b in blocks)


def filter_elements(text, keep):
    nl, head, blocks = msf.elements(text)
    kept = [b for b in blocks if keep(b)]
    if not kept:
        sys.exit("filter kept no elements")
    return head + nl.join(b.rstrip() + nl for b in kept), len(blocks), len(kept)


def render(out_name, spec, made, stats):
    donor = spec["donor"]
    src = os.path.join(TOOLS_FX, donor.replace("/", os.sep) + ".efx")
    if not os.path.exists(src):
        sys.exit("donor %s missing from the tools root" % donor)
    with open(src, "r", encoding="latin-1", newline="") as f:
        text = f.read()
    if text.count("gfx_debug_missing_fx"):
        sys.exit("donor %s is a stub (gfx_debug_missing_fx) - pick another" % donor)
    seen = {}

    def child(m):
        ref = m.group(2).strip()
        if not ref or ref.startswith(OUT_PREFIX):
            return m.group(0)
        if ref not in seen:
            seen[ref] = "%s_c%d" % (out_name, len(seen))
            render(seen[ref], dict(spec, donor=ref, keep=None, size=1.0, light=1.0, blink=False, extra=None), made, stats)
        return m.group(1) + OUT_PREFIX + seen[ref] + m.group(3)

    text = REF_RE.sub(child, text)
    text = RUNNER_RE.sub(child, text)
    total = kept = None
    if spec.get("keep"):
        text, total, kept = filter_elements(text, spec["keep"])
    if spec.get("tint", msf.TINT) is not None:   # tint None = the donor's own colours (docs/206: the flesh hit, the Fuse burst)
        text = msf.recolour_rows(text, spec.get("gain", 1.0), spec.get("tint", msf.TINT))
    text = msf.scale_alpha(text, spec.get("alpha", 1.0))
    text = scale_sizes(text, spec.get("size", 1.0))
    text = scale_lights(text, spec.get("light", 1.0))
    if spec.get("blink"):
        text = blink_light(text, msf.elements(text)[0])
    if spec.get("extra"):
        text = splice_elements(text, spec["extra"], stats, out_name)
    made[out_name] = text
    stats[out_name] = (donor, total, kept)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    made, stats = {}, {}
    for name, spec in EFFECTS.items():
        render(name, spec, made, stats)
    for name in made:
        if len(OUT_PREFIX + name) > FX_PATH_MAX:
            sys.exit("fx path %s%s is %d chars; the engine truncates at %d and crashes on the child"
                     % (OUT_PREFIX, name, len(OUT_PREFIX + name), FX_PATH_MAX))
    os.makedirs(OUT_DIR, exist_ok=True)
    bad = 0
    for name, text in sorted(made.items()):
        p = os.path.join(OUT_DIR, name + ".efx")
        if a.check:
            cur = open(p, "r", encoding="latin-1", newline="").read() if os.path.exists(p) else None
            if cur != text:
                print("STALE", p); bad += 1
        else:
            with open(p, "w", encoding="latin-1", newline="") as f:
                f.write(text)
            d, total, kept = stats.get(name, ("child", None, None))
            n = text.count("\n\tname \"")
            print("wrote %s%s (%d B, %d elems%s, sha %s) <- %s" % (
                OUT_PREFIX, name, len(text), n,
                "" if total is None else " of %d" % total,
                hashlib.sha1(text.encode("latin-1")).hexdigest()[:10], d))
    if a.check:
        print("ability_fx gen_fx --check:", "OK (%d effects)" % len(made) if not bad else "%d stale" % bad)
        sys.exit(1 if bad else 0)
    print("%d effects" % len(made))


if __name__ == "__main__":
    main()
