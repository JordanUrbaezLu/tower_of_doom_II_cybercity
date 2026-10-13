"""Necromancer soul effects (2026-09-26, user: "a blue grayish ... aura instead of
that fire aura", "a blast of souls ... soul-like, not electricity-like").

Copies stock BO3 effects from the private tools root into the repo's
share/raw/fx/tod/necro/ and RECOLOURS every colorGraph key to one blue-grey
tint, keeping each key's brightness (the channel maximum) so the effect keeps
its shape and pulse. Materials, sizes, motion and timing are untouched. Child
effects the donor spawns (runner elements, fxOnImpact / fxOnDeath / emission)
are copied and recoloured too and the references rewritten, so no stock-coloured
child sneaks back in.

Re-run it; never hand-edit the outputs. `--check` verifies the outputs match a
fresh render (the build can gate on it).
"""
import argparse, os, re, sys, hashlib, math

TOOLS_FX = r"C:\BO3Tools\TOD2Cybercity\share\raw\fx"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, "share", "raw", "fx", "tod", "necro")
OUT_PREFIX = "tod/necro/"

# the soul colour: blue-grey, a touch of white at the top
TINT = (0.66, 0.78, 1.00)
FLOOR = 0.06   # keeps a dark key from going pure black-blue
# the PACK-A-PUNCHED skull's beam (Archer/lead 2026-09-26: a visible PaP
# difference without art): a hotter, whiter violet-soul hue, brighter keys
TINT_PAP = (0.94, 0.80, 1.00)

# the HELPER AURAS 25% more intense (user 2026-09-26: "intensify that soul-like
# aura they have by like 25%"): their colour gain x AURA_BOOST (the keys already sit
# near the 1.0 clamp, median 0.64-1.0, so colour alone barely moves) AND their alpha
# x AURA_BOOST (median 0.23-0.4: the headroom), clamped to 1. Children inherit both.
AURA_BOOST = 1.25
ALPHA = {
    "fx_necro_hound_aura": AURA_BOOST,
    "fx_necro_thrall_aura": AURA_BOOST,
    "fx_necro_mangler_aura": AURA_BOOST,
}

# out name -> (donor, gain[, tint])
EFFECTS = {
    "fx_necro_soul_bomb":     ("dlc4/genesis/fx_keeperprot_360_attack", 1.00),  # the Soul Bomb blast
    "fx_necro_summon":        ("dlc4/genesis/fx_keeperprot_spawn",      1.00),  # a helper rises
    "fx_necro_hound_aura":    ("dlc1/castle/fx_wolf_ink_run_body",      1.00 * AURA_BOOST),  # soul hound body (loops)
    "fx_necro_thrall_aura":   ("dlc1/castle/fx_keeper_ghost_ambient_torso", 1.00 * AURA_BOOST),  # thrall torso (loops)
    "fx_necro_mangler_aura":  ("dlc1/castle/fx_keeper_ghost_ambient_torso", 1.25 * AURA_BOOST),  # the Mangler, brighter
    "fx_necro_soul_rip":      ("dlc4/genesis/fx_corrupteng_zombie_soul_115", 1.10),  # a soul torn out
    "fx_necro_soul_wisp":     ("zombie/fx_trail_blood_soul_zmb",        1.20),  # a soul in flight (loops on a moving client host: the beam's stream + the bind)
    # the HELPER Mangler's cannon, soul-coloured (user 2026-09-26: its orange made the
    # white smoke read orange; the enemy Mangler keeps the stock orange shot)
    "fx_necro_mgl_shot":      ("hb/mangler/fx_hb_mangler_projectile",   1.10),
    "fx_necro_mgl_blast":     ("dlc3/stalingrad/fx_raz_mc_shockwave_projectile_impact", 1.00),
    # the PaP skull's beam: the stock Zetsubou beam emitters, recoloured (the
    # base skull keeps the stock beam; _tod_necro_skull.csc picks by weapon)
    "fx_necro_pap_beam_start":      ("dlc2/zmb_weapon/fx_wpn_skull_beam_start_island",      1.35, TINT_PAP),
    "fx_necro_pap_beam_loop":       ("dlc2/zmb_weapon/fx_wpn_skull_beam_loop_island",       1.35, TINT_PAP),
    "fx_necro_pap_beam_start_3p":   ("dlc2/zmb_weapon/fx_wpn_skull_beam_start_3p_island",   1.35, TINT_PAP),
    "fx_necro_pap_beam_loop_3p":    ("dlc2/zmb_weapon/fx_wpn_skull_beam_loop_3p_island",    1.35, TINT_PAP),
    "fx_necro_pap_beam_side_start": ("dlc2/zmb_weapon/fx_wpn_skull_beam_side_start_island", 1.35, TINT_PAP),
    "fx_necro_pap_beam_side_loop":  ("dlc2/zmb_weapon/fx_wpn_skull_beam_side_loop_island",  1.35, TINT_PAP),
}

# the engine's fx-path buffer is 64 bytes: folder + name must fit in 63 (see child())
FX_PATH_MAX = 63

REF_RE = re.compile(r'(\n\t(?:fxOnImpact|fxOnDeath|emission)\s+")([^"]+)(")')
RUNNER_RE = re.compile(r'(\n\trunner\s*\n\t\{\s*\n\t\t")([^"]+)(")')


def recolour_rows(text, gain, tint):
    # a colorGraph block: "colorGraph N\n\t{" ... matching close brace
    out, i = [], 0
    for m in re.finditer(r'\n\tcolorGraph[^\n]*\n\t\{', text):
        if m.start() < i:
            continue
        j, depth = m.end(), 1
        while depth:
            c = text[j]
            depth += (c == '{') - (c == '}')
            j += 1
        out.append(text[i:m.end()])
        block = text[m.end():j]
        block = re.sub(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',
                       lambda r: recolour_row(r, gain, tint), block)
        out.append(block)
        i = j
    out.append(text[i:])
    return "".join(out)


def scale_alpha(text, alpha):
    # an alphaGraph block: "alphaGraph N\n\t{" ... matching close brace; each key is
    # "time value" on its own line - the value x alpha, clamped to 1
    if alpha == 1.0:
        return text
    out, i = [], 0
    for m in re.finditer(r'\n\talphaGraph[^\n]*\n\t\{', text):
        if m.start() < i:
            continue
        j, depth = m.end(), 1
        while depth:
            c = text[j]
            depth += (c == '{') - (c == '}')
            j += 1
        out.append(text[i:m.end()])
        block = re.sub(r'(?m)^(\t+)([\d.]+) ([\d.]+)(\r?)$',   # donors mix CRLF keys into LF files
                       lambda r: "%s%s %.6f%s" % (r.group(1), r.group(2), min(1.0, float(r.group(3)) * alpha), r.group(4)),
                       text[m.end():j])
        out.append(block)
        i = j
    out.append(text[i:])
    return "".join(out)


def recolour_row(r, gain, tint):
    t, cr, cg, cb = (float(x) for x in r.groups())
    v = max(cr, cg, cb)
    v = min(1.0, max(FLOOR, v * gain)) if v > 0 else 0.0
    return "%.6f %.6f %.6f %.6f" % (t, v * tint[0], v * tint[1], v * tint[2])


def render(out_name, donor, gain, made, tint=TINT, alpha=1.0):
    src = os.path.join(TOOLS_FX, donor.replace("/", os.sep) + ".efx")
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
            # SHORT child names, on purpose (Archer/lead 2026-09-26, two crash dumps):
            # BO3 keeps an fx path in a 64-byte buffer and TRUNCATES a longer one at
            # runtime; "<parent>_<donor name>" made the Mangler aura's child 64 chars,
            # the cut name matched nothing, and the parent spawning a null child was
            # an access violation the instant a Mangler rose. The thrall's child,
            # one letter shorter, worked. So a child is "<parent>_c<N>" and every
            # path is asserted <= FX_PATH_MAX.
            seen[ref] = "%s_c%d" % (out_name, len(seen))
            render(seen[ref], ref, gain, made, tint, alpha)
        return m.group(1) + OUT_PREFIX + seen[ref] + m.group(3)
    text = REF_RE.sub(child, text)
    text = RUNNER_RE.sub(child, text)
    text = recolour_rows(text, gain, tint)
    text = scale_alpha(text, alpha)
    if out_name.startswith("fx_necro_mangler_aura"):
        # These two donor emitters use a baked orange FLAME atlas. A white color
        # graph multiplies that orange; it cannot turn the atlas into soul smoke.
        nl, head, blocks = elements(text)
        text = head + nl.join(b.rstrip() + nl for b in blocks
                              if "gfx_fire_" not in b)
    made[out_name] = text


# ---------------------------------------------------------------------------
# SOUL PULSE, 2026-09-27: a wide authored white ground wave, without any
# caster-centred burst, light, distortion or flare. The legacy root is retained
# for existing precaches but now also resolves to the safe base-radius ring.
PULSE = "fx_necro_soul_bomb"
# The four bands are selected by the replicated tod_necro_bomb_band field.
RING_TEMPLATE = "wraith_oneshot_def3"          # the donor's gfx_ring_thin rotatedSprite
RING_RADII = (360, 440, 520, 600)             # LOCKSTEP _tod_necro_summon bomb_band(): radius 360 + 30/Lv -> the nearest band
RING_SIZE_PER_UNIT = 1.0                      # sprite size per unit of radius: THE knob if the ring stops short of / past the kill edge
RING_LIFE_MS = 800
RING_REACH = 0.175                            # exactly 140 ms: preserve the existing damage timing
RING_WHITE = (0.94, 0.97, 1.00)


def elements(text):
    nl = "\r\n" if "\r\n" in text else "\n"
    parts = re.split(r'(?=\{\r?\n\tname ")', text)
    return nl, parts[0], parts[1:]


def elem_name(b):
    return re.search(r'\tname "([^"]+)"', b).group(1)


def set_field(b, key, value):
    b2, n = re.subn(r'(\n\t%s )[^;\r\n]*;' % re.escape(key), lambda m: m.group(1) + value + ";", b, count=1)
    if n != 1:
        sys.exit("ring template has no %s" % key)
    return b2


def set_graph(b, key, base, rows, nl):
    curve = nl.join("\t\t\t" + " ".join("%.6f" % v for v in r) for r in rows)
    head = "1" if key in ("colorGraph", "alphaGraph") else "%.6f" % base   # every stock efx writes these two as a bare 1 (48,535 of 48,535)
    body = "\t%s %s%s\t{%s\t\t{%s%s%s\t\t}%s\t\t{%s%s%s\t\t}%s\t};" % (
        key, head, nl, nl, nl, curve, nl, nl, nl, curve, nl, nl)
    b2, n = re.subn(r'\t%s [\d.\-]+\r?\n\t\{.*?\r?\n\t\};' % re.escape(key), lambda m: body, b, count=1, flags=re.S)
    if n != 1:
        sys.exit("ring template has no %s graph" % key)
    return b2


def ring_elem(template, nl, name, radius, delay_ms, alpha, scale):
    b = template.replace('\tname "%s";' % RING_TEMPLATE, '\tname "%s";' % name, 1)
    b = set_field(b, "lifeSpanMsec", "%d 0" % RING_LIFE_MS)
    b = set_field(b, "spawnDelayMsec", "%d 0" % delay_ms)
    b = set_field(b, "spawnOrgX", "0.000000 0.000000")
    b = b.replace('"gfx_ring_thin"', '"mtl_tod_necro_pulse"')
    # Custom authored mask's bright leading rim is at UV radius .90.
    size = radius * RING_SIZE_PER_UNIT * scale / 0.90
    grow = [(0.0, 0.0), (RING_REACH, 1.0), (1.0, 1.08)]
    b = set_graph(b, "sizeGraph0", size, grow, nl)
    b = set_graph(b, "sizeGraph1", size, grow, nl)
    b = set_graph(b, "colorGraph", 1.0, [(0.0,) + RING_WHITE, (1.0,) + RING_WHITE], nl)
    b = set_graph(b, "alphaGraph", 1.0, [(0.0, 0.0), (0.04, alpha), (RING_REACH, alpha), (0.5, alpha * 0.65), (1.0, 0.0)], nl)
    return b


def soul_pulse(made):
    nl, head, blocks = elements(made[PULSE])
    by = {elem_name(b): b for b in blocks}
    for k in (RING_TEMPLATE,):
        if k not in by:
            sys.exit("%s lost element %s - re-read the donor" % (PULSE, k))
    template = by[RING_TEMPLATE].rstrip()
    _, _, aura = elements(made['fx_necro_mangler_aura_c0'])
    smoke = next(b for b in aura if 'gfx_smk_whisp_anim_em' in b)
    symbol = next(b for b in aura if 'gfx_keeper_symbols_zod_em' in b)
    for i, r in enumerate(RING_RADII):
        ring = ring_elem(template, nl, "soul_pulse_ring", r, 0, 1.0, 1.0)
        echo = ring_elem(template, nl, "soul_pulse_echo", r, 45, 0.45, 0.88)
        souls = [outgoing_soul(smoke, nl, r, j, False) for j in range(24)]
        souls += [outgoing_soul(symbol, nl, r, j * 2, True) for j in range(12)]
        made["fx_necro_pulse_ring%d" % i] = head + (nl + nl).join([ring, echo] + souls) + nl
    made[PULSE] = made["fx_necro_pulse_ring0"]


def outgoing_soul(template, nl, radius, index, glyph):
    """White native soul art travels with the wave, clear of the caster.

    PlayFX supplies world-up as local X: Y/Z form the ground plane. Explicit
    positions avoid a spherical spawn spraying particles through the camera.
    """
    b = re.sub(r'\tname "[^"]+";', '\tname "soul_%s_%02d";' % ('glyph' if glyph else 'wisp', index), template, count=1)
    angle = index * math.tau / 24
    start = 88.0
    speed = (radius - start) / .140
    fields = dict(flags='spawnRelative spawnOffsetNone runRelToSpawn',
                  spawnRange='0 0', fadeInRange='0 0', fadeOutRange='0 0',
                  spawnLooping='1 0', spawnLoopingSpawnCount='0 0', spawnOneShot='1 0',
                  spawnDelayMsec='0 0', lifeSpanMsec='750 0', gravity='0 0',
                  spawnOrgX='%f 0' % (30 + (index % 3) * 9),
                  spawnOrgY='%f 0' % (start * math.cos(angle)),
                  spawnOrgZ='%f 0' % (start * math.sin(angle)))
    for key, value in fields.items(): b = set_field(b, key, value)
    travel = [(0,1),(.140/.750,1),(.140/.750+.001,0),(1,0)]
    for axis, velocity in [('X',0),('Y',speed*math.cos(angle)),('Z',speed*math.sin(angle))]:
        b = set_graph(b, 'velGraph0'+axis, velocity, travel, nl)
        b = set_graph(b, 'velGraph1'+axis, 0, [(0,0),(1,0)], nl)
    for key, size in [('sizeGraph0',14 if glyph else 30),('sizeGraph1',14 if glyph else 46)]:
        b = set_graph(b, key, size, [(0,.65),(.19,1),(.5,1.12),(1,.8)], nl)
    b = set_graph(b, 'colorGraph', 1, [(0,)+RING_WHITE,(1,)+RING_WHITE], nl)
    b = set_graph(b, 'alphaGraph', 1, [(0,0),(.04,.9),(.19,.9),(.55,.6),(1,0)], nl)
    return b.rstrip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    made = {}
    for name, spec in EFFECTS.items():
        render(name, spec[0], spec[1], made, spec[2] if len(spec) > 2 else TINT, ALPHA.get(name, 1.0))
    soul_pulse(made)
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in made:
        if len(OUT_PREFIX + name) > FX_PATH_MAX:
            sys.exit("fx path %s%s is %d chars; the engine truncates at %d and crashes on the child"
                     % (OUT_PREFIX, name, len(OUT_PREFIX + name), FX_PATH_MAX))
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
            print("wrote %s (%d B, sha %s)" % (OUT_PREFIX + name, len(text), hashlib.sha1(text.encode("latin-1")).hexdigest()[:10]))
    if a.check:
        print("make_soul_fx --check:", "OK" if not bad else "%d stale" % bad)
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
