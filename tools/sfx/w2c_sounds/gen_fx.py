"""THE BOLT IMPACT EFFECTS (PK28, 2026-10-05): share/raw/fx/tod/archer/fx_tod_crossbow_bolt_impact(_ug).efx, generated
from stock BO3 donors through tools/ability_fx/gen_fx.py's render (filter, recolour, scale, children renamed
<parent>_c<N> under the 63-character fx path limit; a stub donor exits).

The R1 Shadowhunter's bolt landed with nothing: no puff, no spark, no thunk (PK28). What a bolt hit now looks like:
  BASE   a cold CYAN electric spark burst (the stock xsm omni blue spark burst, its sparks bouncing off the surface,
         no light, no lens flare) over the stock small concrete impact's grit, dust puff and lingering smoke (no decal,
         no rock model, no underwater runner). Under one second; every particle small.
  _UG    the Pack-a-Punched bolt: the same burst run HOT (an ember-white recolour, 15 % larger) and the burst's own
         dynamic light kept, ember, at half its radius - a brief glint at the hit.
Consumer: the bolt's impact tables (source_data/tod_crossbow_impacts.gdt: every surface -> this effect), named by the
crossbow's normalImpactsFxTable / bounceImpactsFXTable (tools/gen_tod_twins.js cc_crossbow tune). LOCKSTEP: the
zone's fx,tod/archer/fx_tod_crossbow_bolt_impact* lines (LAND.md WIRING), printed by this tool.

  python tools/sfx/w2c_sounds/gen_fx.py [--out-root DIR]          write the effects
  python tools/sfx/w2c_sounds/gen_fx.py --check [--root DIR]      regenerate in memory and compare (make_sounds --check)
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "tools", "ability_fx"))
OUT_PREFIX = "tod/archer/"
FIX = "run: python tools/sfx/w2c_sounds/gen_fx.py"

CYAN = (0.55, 0.92, 1.00)       # the cyber kit's cyan (tools/ability_fx/gen_fx.py CYAN)
EMBER = (1.00, 0.62, 0.26)      # the PaP bolt: hot


_GF = None


def _gf():
    """tools/ability_fx/gen_fx.py, loaded under its own name (this file shares its basename)"""
    global _GF
    if _GF is None:
        import importlib.util
        sys.path.insert(0, os.path.join(REPO, "tools", "necromancer"))
        spec = importlib.util.spec_from_file_location("abfx_gen_fx", os.path.join(REPO, "tools", "ability_fx", "gen_fx.py"))
        _GF = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_GF)
    _GF.OUT_PREFIX = OUT_PREFIX   # children are renamed under OUR prefix
    return _GF


def _names(*names):
    s = set(names)

    def keep(b):
        import make_soul_fx as msf
        return msf.elem_name(b) in s
    return keep


def _not_names(*names):
    s = set(names)

    def keep(b):
        import make_soul_fx as msf
        return msf.elem_name(b) not in s
    return keep


SPARKS_BASE = ("spark_glow", "sparks_impact", "spark_line", "spark_out_core", "sparks_bounce_blue", "spark_out",
               "spark_glow_1", "sparks_round_0", "sparks_round_glow_0")
DUST_DROP = ("_decal", "0_debris_rock_model", "uw_runner")

EFFECTS = {
    "fx_tod_crossbow_bolt_impact": dict(
        donor="electric/fx_elec_sparks_burst_xsm_omni_blue_os", tint=CYAN, gain=1.05, alpha=0.9, size=0.75,
        keep=_names(*SPARKS_BASE),
        extra=[dict(donor="impacts/fx_bul_impact_concrete_sm", keep=_not_names(*DUST_DROP), tint=None)]),
    "fx_tod_crossbow_bolt_impact_ug": dict(
        donor="electric/fx_elec_sparks_burst_xsm_omni_blue_os", tint=EMBER, gain=1.15, alpha=1.0, size=0.86, light=0.5,
        keep=_names(*(SPARKS_BASE + ("light_blue", "spark_glow_2", "sparks_round_1", "sparks_round_glow_1"))),
        extra=[dict(donor="impacts/fx_bul_impact_concrete_sm", keep=_not_names(*DUST_DROP), tint=None)]),
}


def render_all():
    gf = _gf()
    made, stats = {}, {}
    for name, spec in EFFECTS.items():
        gf.render(name, spec, made, stats)
    # one line ending per file: the spliced donor (the concrete impact) is LF, the spark donor CRLF - every stock .efx
    # and every generated neighbour here is CRLF throughout
    for name in made:
        made[name] = made[name].replace("\r\n", "\n").replace("\n", "\r\n")
    for name in made:
        if len(OUT_PREFIX + name) > gf.FX_PATH_MAX:
            raise SystemExit("fx path %s%s is over %d chars" % (OUT_PREFIX, name, gf.FX_PATH_MAX))
    return made, stats


def zone_lines():
    made, _ = render_all()
    return ["fx,%s%s" % (OUT_PREFIX, n) for n in sorted(made)]


def check(root):
    try:
        made, _ = render_all()
    except SystemExit as e:
        return [str(e)]
    bad = []
    for name, text in sorted(made.items()):
        p = os.path.join(root, "share", "raw", "fx", OUT_PREFIX.replace("/", os.sep), name + ".efx")
        cur = open(p, "r", encoding="latin-1", newline="").read() if os.path.exists(p) else None
        if cur != text:
            bad.append("share/raw/fx/%s%s.efx stale - %s" % (OUT_PREFIX, name, FIX))
    zone = os.path.join(root, "zone_source", "zm_tod2_cybercity.zone")
    zt = open(zone, encoding="utf-8", errors="replace").read() if os.path.exists(zone) else ""
    for line in ["fx,%s%s" % (OUT_PREFIX, n) for n in sorted(made)]:
        if line not in zt.splitlines():
            bad.append("the zone lacks '%s'" % line)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--out-root", default=REPO)
    a = ap.parse_args()
    if a.check:
        bad = check(os.path.abspath(a.root))
        print("BOLT FX " + ("OK" if not bad else "STALE: " + "; ".join(bad)))
        sys.exit(1 if bad else 0)
    made, stats = render_all()
    d = os.path.join(os.path.abspath(a.out_root), "share", "raw", "fx", OUT_PREFIX.replace("/", os.sep))
    os.makedirs(d, exist_ok=True)
    for name, text in sorted(made.items()):
        with open(os.path.join(d, name + ".efx"), "w", encoding="latin-1", newline="") as f:
            f.write(text)
        donor, total, kept = stats.get(name, ("child", None, None))
        print("wrote %s%s (%d B, %d elems%s) <- %s" % (OUT_PREFIX, name, len(text), text.count('\n\tname "'),
                                                      "" if total is None else " of %d" % total, donor))
    print("zone lines:\n  " + "\n  ".join(zone_lines()))


if __name__ == "__main__":
    main()
