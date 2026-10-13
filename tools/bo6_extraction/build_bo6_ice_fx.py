"""Compose the BO6-INSPIRED ice staff shot effects for Cybercity (v18.90).

Honesty first: these are NOT ported BO6 particle systems. Saluki (the only BO6
extractor here) has no particle/vfx asset type at all (Models / Animations /
Images / Materials / Sounds / Camos / Sound Banks / Animation Packages /
Additional), the name dictionaries hold no `vfx_t10_..._staff_ice` entry, and the
loaded index returned zero rows. So the BO6 look (The Tomb's ice staff: a hard
cyan-white flash, a shower of glittering ice crystals, a frost puff, an icy bolt
that sheds crystals, a frost nova on impact) is REBUILT from BO3 emitters that
already exist in the mod tools -- reuse over authoring -- by composing whole
emitter blocks out of:

  * our own trimmed ice effects (the v18.75 glare pass stays in force: no lens
    flare, no dynamic light on the 1p muzzle),
  * Winter's Howl (dlc5 freezegun) flash / impact: spark-cloud "flakes", a dust-
    mote frost puff, the phosphorous core flash, the thin ring nova,
  * the stock Origins ice impact (kept whole underneath the new layer).

Each output is `iwfx 2` + a list of verbatim donor blocks with only three kinds
of edits, all recorded in the manifest: a unique `name`, an optional uniform
size scale (the leading `sizeGraph0` value), and an optional colour-graph
override. Child-effect references (`fxOnImpact` / `fxOnDeath`) must be empty on
every copied block, so the composed effect has no unzoned dependency.

Run:  python tools/bo6_extraction/build_bo6_ice_fx.py          (writes share/raw/fx/tod/bo6/)
      python tools/bo6_extraction/build_bo6_ice_fx.py --check  (hashes only; build gate)
"""
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[2]
TOOLS_FX = Path(r'C:/BO3Tools/TOD2Cybercity\share\raw\fx')
OUT = REPO/'share/raw/fx/tod/bo6'
MANIFEST = REPO/'docs/bo6_ports/manifests/ice_staff_bo6_fx.json'

OURS = REPO/'share/raw/fx/tod'
FLASH = TOOLS_FX/'dlc5/zmb_weapon/fx_freezegun_flash_upg.efx'
FIMPACT = TOOLS_FX/'dlc5/zmb_weapon/fx_exp_freezegun_impact.efx'
SIMPACT = TOOLS_FX/'dlc5/zmb_weapon/fx_staff_ice_impact.efx'

# The Tomb's staff reads cyan-white, not Winter's Howl's teal: colour graphs are
# (t r g b) rows; two-row override = start colour, end colour.
ICE_CORE = ((0.85, 0.98, 1.0), (0.45, 0.85, 1.0))
ICE_CRYSTAL = ((0.75, 0.95, 1.0), (0.35, 0.70, 1.0))

# (output, [ (source file, block name, {scale: float, color: ((r,g,b),(r,g,b))}) ... ])
RECIPES = {
    'fx_bo6_ice_muzzle_1p': [
        # v18.92 (user: "I like the powder haze. But just not in my face. Or we can move the
        # spot it shoots from farther from the player's body"): the base muzzle's three
        # one-shot sprites (the haze 120, glow 50/18) are pushed 48 units further down the
        # shaft axis; the small looping sparkles stay at the tip.
        *[(OURS/'fx_tod_ice_muzzle_1p.efx', 'wraith_looping_def%d' % i, {}) for i in (0, 1, 2, 3, 4, 5, 6, 8, 9, 10)],
        *[(OURS/'fx_tod_ice_muzzle_1p.efx', 'wraith_oneshot_def%d' % i, {'org_x': 48.0}) for i in (0, 1, 2)],
        # v18.91 (user: "a big puff and flash on the player's screen ... the only part I
        # don't like"): NO core flash and NO frost puff in first person. Crystals only.
        (FLASH, 'smaller_flakes', {'scale': 1.0, 'color': ICE_CRYSTAL}),  # glittering crystals
        (FLASH, 'bigger_flakes', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FLASH, 'swirling_flakes', {'scale': 0.8, 'color': ICE_CRYSTAL}),
    ],
    'fx_bo6_ice_muzzle_3p': [
        (OURS/'fx_tod_ice_muzzle_3p.efx', '*', {}),
        (FLASH, 'initial_flash', {'scale': 0.6, 'color': ICE_CORE}),
        (FLASH, 'smaller_flakes', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FLASH, 'bigger_flakes', {'scale': 1.2, 'color': ICE_CRYSTAL}),
        (FLASH, 'swirling_flakes', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FLASH, 'frost', {'scale': 0.5, 'color': ICE_CORE}),
    ],
    'fx_bo6_ice_trail': [
        # v18.92 (user: "have the projectile size grow as it goes, so it starts tiny and there
        # is no way I can see the flash"): the bolt's body sprites are gated by DISTANCE FROM
        # THE CAMERA (spawnRange min + a fadeInRange over the next 48 units). At 2200 u/s the
        # bolt clears 96 units in ~45 ms and 176 in ~80 ms, so it leaves the muzzle as bare
        # sparkles, the medium glows come in a few feet out, the big body last. Elements
        # are listed by their base size: tiny ones (<= 25) stay ungated.
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def0', {}),                      # 25
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def5', {}),                      # 3
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def7', {}),                      # 2
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def9', {}),                      # model host
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def2', {'spawn_min': 96}),       # 73
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def8', {'spawn_min': 96}),       # 75
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def1', {'spawn_min': 136}),      # 87
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def6', {'spawn_min': 176}),      # 110
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def14', {'spawn_min': 176}),     # 111
        (OURS/'mage/fx_staff_ice_trail_clean.efx', 'wraith_oneshot_def13', {'spawn_min': 216}),     # 150
        (FLASH, 'smaller_flakes', {'scale': 0.8, 'color': ICE_CRYSTAL}),  # crystals shed along the bolt
        (FLASH, 'swirling_flakes', {'scale': 0.5, 'color': ICE_CRYSTAL}),
        # v18.91: no frost wisp on the trail either; it spawned at the muzzle, in the player's face.
    ],
    'fx_bo6_ice_impact': [
        (SIMPACT, '*', {}),                                               # stock Origins impact underneath
        (FIMPACT, 'light', {'scale': 1.0, 'color': ICE_CORE}),
        (FIMPACT, 'IGC_glow', {'scale': 1.2, 'color': ICE_CORE}),
        (FIMPACT, '0_snow_flakes_out', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FIMPACT, 'sparks_A', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FIMPACT, '11tendrils', {'scale': 1.0, 'color': ICE_CRYSTAL}),
        (FLASH, 'ring_inner', {'scale': 0.5, 'color': ICE_CORE}),        # the nova ring, 500 -> 250
        (FLASH, 'bigger_flakes', {'scale': 1.5, 'color': ICE_CRYSTAL}),
    ],
    # v18.93 (user: "enhance the frost, flame, and electricity fx on each staff ... like 25%
    # more" — "the fx on the staff when it just sits there. It's on the tips"): the three
    # Origins persistent tip glows, every emitter at 125% size, colours untouched (that IS
    # their personality). The CSC attaches these instead of the dlc5 originals.
    'fx_tod_staff_glow_elec': [(TOOLS_FX/'dlc5/zmb_weapon/fx_staff_elec_persistent.efx', '*', {'scale': 1.25})],
    'fx_tod_staff_glow_fire': [(TOOLS_FX/'dlc5/zmb_weapon/fx_staff_fire_persistent.efx', '*', {'scale': 1.25})],
    'fx_tod_staff_glow_ice': [(TOOLS_FX/'dlc5/zmb_weapon/fx_staff_ice_persistent.efx', '*', {'scale': 1.25})],
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blocks(text):
    out, i = [], text.find('{')
    while i != -1:
        depth, j = 0, i
        while j < len(text):
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(text[i:j+1])
        i = text.find('{', j+1)
    return out


def block_name(b):
    return re.search(r'\n\tname "([^"]+)";', b)[1]


def child_refs(b):
    return [m for m in re.findall(r'\n\t(?:fxOnImpact|fxOnDeath|emission)\s+"?([^";\n]*)"?;', b) if m.strip()]


def recolor(b, colors):
    (r0, g0, b0), (r1, g1, b1) = colors

    def repl(m):
        body = m[1]
        rows = re.findall(r'([\d.]+)\s+[\d.]+\s+[\d.]+\s+[\d.]+', body)
        if not rows:
            return m[0]
        new = ['\t\t{']
        for k, t in enumerate(rows):
            f = k/max(1, len(rows)-1)
            r, g, bb = (r0+(r1-r0)*f, g0+(g1-g0)*f, b0+(b1-b0)*f)
            new.append(f'\t\t\t{float(t):.6f} {r:.6f} {g:.6f} {bb:.6f}')
        new.append('\t\t}')
        return '\n'.join(new)
    # colorGraph holds two sub-graphs (min/max); tint both.
    head = re.search(r'\n\tcolorGraph[^\n]*\n\t\{', b)
    if not head:
        return b
    start = head.end()
    depth, j = 1, start
    while depth:
        if b[j] == '{':
            depth += 1
        elif b[j] == '}':
            depth -= 1
        j += 1
    inner = b[start:j-1]
    inner = re.sub(r'\t\t\{([^{}]*)\}', repl, inner)
    return b[:start]+inner+b[j-1:]


def rescale(b, scale):
    return re.sub(r'(\n\tsizeGraph0 )([\d.]+)', lambda m: f'{m[1]}{float(m[2])*scale:.6f}', b, count=1)


def gate_by_distance(b, near):
    """Do not spawn this element within `near` units of the camera, and fade it in
    over the next 48 units: spawnRange min / fadeInRange. The far bounds are kept."""
    b = re.sub(r'(\n\tspawnRange )([\d.]+) ([\d.]+);', lambda m: f'{m[1]}{max(float(m[2]), near):.6f} {m[3]};', b, count=1)
    b = re.sub(r'(\n\tfadeInRange )([\d.]+) ([\d.]+);', lambda m: f'{m[1]}{near:.6f} {near+48:.6f};', b, count=1)
    return b


def v3_header():
    """Our effects are `iwfx 2`, the freezegun donors `iwfx 3`; the BLOCK keyword
    sets are identical (compared 2026-09-13), only the file header differs, and
    this map already ships v3 files (acc/light perk glows). Emit v3 with the
    donor's header verbatim."""
    text = FLASH.read_text(encoding='latin1').replace('\r', '')
    assert text.startswith('iwfx 3')
    return text[:text.index('{')].rstrip()+'\n\n'


def compose(name, recipe, report):
    parts, used = [], set()
    for src, want, edits in recipe:
        text = src.read_text(encoding='latin1').replace('\r', '')
        assert text.startswith(('iwfx 2', 'iwfx 3')), src
        for b in blocks(text):
            n = block_name(b)
            if want != '*' and n != want:
                continue
            refs = child_refs(b)
            assert not refs, (src.name, n, refs, 'copied block references a child effect')
            if 'scale' in edits and edits['scale'] != 1.0:
                b = rescale(b, edits['scale'])
            if 'color' in edits:
                b = recolor(b, edits['color'])
            if 'spawn_min' in edits:
                b = gate_by_distance(b, edits['spawn_min'])
            if 'org_x' in edits:
                b = re.sub(r'(\n\tspawnOrgX )([-\d.]+) ([-\d.]+);', lambda m: f"{m[1]}{float(m[2])+edits['org_x']:.6f} {m[3]};", b, count=1)
            new = n if n not in used else f'{n}_{len(used)}'
            if new != n:
                b = b.replace(f'\n\tname "{n}";', f'\n\tname "{new}";', 1)
            used.add(new)
            parts.append(b)
            report['effects'][name]['blocks'].append(dict(source=str(src), block=n, name=new, edits={k: (v if k in ('scale', 'spawn_min', 'org_x') else 'tint') for k, v in edits.items()}))
        if want != '*':
            assert any(x['block'] == want and x['source'] == str(src) for x in report['effects'][name]['blocks']), (src.name, want, 'missing donor block')
    out = OUT/(name+'.efx')
    out.write_text(v3_header()+'\n\n'.join(parts)+'\n', encoding='latin1')
    report['effects'][name]['path'] = str(out.relative_to(REPO)).replace('\\', '/')
    report['effects'][name]['sha256'] = digest(out)
    print(f'FX {name}: {len(parts)} emitters', flush=True)


def check():
    r = json.loads(MANIFEST.read_text())
    for name, e in r['effects'].items():
        assert (REPO/e['path']).is_file() and digest(REPO/e['path']) == e['sha256'], ('BO6 ice fx changed/missing', name)
    print(f"BO6 ICE FX OK: {len(r['effects'])} composed effects pinned (BO3 emitters; not ported BO6 vfx)")


def main():
    if '--check' in sys.argv:
        check()
        return
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(scope='BO6-INSPIRED rebuild from BO3 emitters; Saluki exports no particle systems, so no BO6 vfx data exists here',
                  effects={n: dict(blocks=[]) for n in RECIPES}, native_verified=False)
    for name, recipe in RECIPES.items():
        compose(name, recipe, report)
    MANIFEST.write_text(json.dumps(report, indent=2)+'\n')
    print('COMPOSED 4 effects into share/raw/fx/tod/bo6/; wire them in tod_staff.gdt + the zone, then a FULL build')


if __name__ == '__main__':
    main()
