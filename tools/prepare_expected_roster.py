"""Stage map-owned donor snapshots and the requested September 24 loadout wiring.

Only this repository is written. Installed donor libraries are read-only inputs.
The authoritative result is the generator and its normal checked build pipeline.
"""
import json
import re
import shutil
from pathlib import Path
from inspect_expected_roster import ROOT, TOOLS, OUT

SIBLING = ROOT.parent / 'tower_of_doom_II_hellbound'
REPLACEMENTS = {'cc_car': 'cc_r99', 't5_enfield': 'cc_bow', 't9_krig6': 'cc_crossbow',
    't9_ak47': 'cc_fire_bow', 't9_me_baseballbat': 'cc_twin_knives',
    't9_me_wakizashi': 'cc_plain_sword', 'leviathan': 'cc_gold_sword'}


def write(relative, text):
    path = ROOT / relative
    assert path.resolve().is_relative_to(ROOT.resolve())
    backup = OUT / 'before' / relative
    if path.exists() and not backup.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_gun(text, old, new):
    marker = f"stem: '{old}'"
    if marker not in text:
        return text
    at = text.index(marker)
    start = text.rfind('\n    {', 0, at)
    end = text.index('\n    },', at) + len('\n    },')
    return text[:start] + '\n' + new.strip('\n') + text[end:]


if __name__ == '__main__':
    for name in ('hb_r99.gdt', 'hb_warrior_tiers.gdt', 'hb_gold_sword.gdt', 'hb_bow.gdt', 'hb_crossbow.gdt', 'hb_fire_bow.gdt'):
        write('donor_gdt/hellbound/' + name, (TOOLS / 'source_data' / name).read_text(encoding='utf-8-sig'))
    rel = 'tools/gen_tod_twins.js'
    text = (ROOT / rel).read_text(encoding='utf-8')
    text = replace_gun(text, 'cc_car', '''    {
      tier: 3, stem: 'cc_r99', enabled: true,
      src: HB('hb_r99.gdt'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{ srcAsset: 'hb_r99', name: s => 'cc_r99' + s, up: false },
              { srcAsset: 'hb_r99_up', name: s => 'cc_r99_up' + s, up: true }],
      axes: ['h'], axisMaxUp: { h: 4 },
      tune: { recoil: RECOIL_BUMP, ads: ADS_BUMP, set: { clipSize: 40, minDamage: 87 }, reserveMags: 11,
              str: { penetrateType: 'medium', altWeapon: '' } },
      csv: { cost: 1300, vo: 'smg', cls: 'smg' },
    },''')
    for old, stem, source, base, packed, tier, ref, quiver in (
        ('t5_enfield','cc_bow','hb_bow.gdt','hb_bow_zm','hb_bow_up_zm',1,'t5_enfield',True),
        ('t9_krig6','cc_crossbow','hb_crossbow.gdt','hb_crossbow','hb_crossbow_up',2,'t9_krig6',False),
        ('t9_ak47','cc_fire_bow','hb_fire_bow.gdt','hb_fire_bow_zm','hb_fire_bow_up_zm',3,'t9_ak47',True)):
        suffix = " + '_zm'" if quiver else ''
        text = replace_gun(text, old, f'''    {{
      tier: {tier}, stem: '{stem}', enabled: true,
      src: HB('{source}'), gdf: 'projectileweapon.gdf', encoding: 'utf8',
      forms: [{{ srcAsset: '{base}', name: s => '{stem}' + s{suffix}, up: false }},
              {{ srcAsset: '{packed}', name: s => '{stem}_up' + s{suffix}, up: true }}],
      axes: ['r', 'm'], {"axisMaxUp: { r: 3, m: 4 }," if tier == 3 else ""}
      sustainedRef: '{ref}', {"nativeQuiver: true," if quiver else ""}
      {"capReference: { damage: 176, fireTime: 0.08, shot: 1 }," if tier == 1 else ""}
      tune: {{ recoil: RECOIL_BUMP, ads: ADS_BUMP, str: {{ altWeapon: '' }} }},
      csv: {{ cost: {1250 if tier == 1 else 1500}, vo: 'rifle', cls: 'rifle' }},
    }},''')
    # Preserve this map's established melee hit damage and swing timings while
    # taking donor models/animations. No Hellbound-only bash/smash systems.
    baseline = json.loads((OUT / 'baseline_weapons.json').read_text())
    for old, stem, source, asset, tier in (
        ('t9_me_baseballbat','cc_twin_knives','hb_warrior_tiers.gdt','hb_twin_knives',1),
        ('t9_me_wakizashi','cc_plain_sword','hb_warrior_tiers.gdt','hb_plain_sword',2),
        ('leviathan','cc_gold_sword','hb_gold_sword.gdt','hb_gold_sword',3)):
        fields = baseline[old + '_k0_zm']['fields']
        timings = {k: float(fields[k]) for k in ('fireTime','meleeTime','meleeChargeTime')}
        text = replace_gun(text, old, f'''    {{
      tier: {tier}, stem: '{stem}', enabled: true, melee: true,
      src: HB('{source}'), gdf: 'bulletweapon.gdf', encoding: 'utf8',
      forms: [{{ srcAsset: '{asset}_zm', name: s => '{stem}' + s + '_zm', up: false }},
              {{ srcAsset: '{asset}_up_zm', name: s => '{stem}_up' + s + '_zm', up: true }}],
      axes: ['k'], {"axisMaxUp: { k: 6 }," if tier == 3 else ""}
      tune: {{ ads: ADS_BUMP, set: {json.dumps(timings)}, str: {{ altWeapon: '' }} }},
      csv: {{ cost: 3000, vo: 'wpck_bowie', cls: 'special', melee: true }},
    }},''')
    if "t5_enfield: { base:" not in text:
        entries = []
        for stem, tail in [('t5_enfield','_zm'),('t9_krig6',''),('t9_ak47','')]:
            b = baseline[stem + '_r0m0']['fields']
            u = baseline[stem + '_up_r0m0' + tail]['fields']
            def stats(f):
                return dict(damage=int(f['damage']), fireTime=float(f['fireTime']), clip=int(f['clipSize']), reload=float(f['reloadEmptyTime']))
            entries.append(f"  {stem}: {{ base: {json.dumps(stats(b))}, up: {json.dumps(stats(u))}, mags: {b['maxAmmo']} }},")
        text = text.replace('const BREACHER_RETIRED = {', 'const BREACHER_RETIRED = {\n  // Archer swaps: preserve retired full-cycle DPS, without the rifle clip floor.\n' + '\n'.join(entries))
        text = text.replace('gun.tune.reserveMags = Math.max(1, Math.round(ret.mags * retiredCycle(ret.base) / probe.cycle));',
            'if (!gun.nativeQuiver) gun.tune.reserveMags = Math.max(1, Math.round(ret.mags * retiredCycle(ret.base) / probe.cycle));\n        else { gun.tune.set = Object.assign({}, gun.tune.set, { maxAmmo: 0, startAmmo: readNum(raw, "clipSize") }); }')
    retired = '"t6_mk48", "t5_hk21", "t6_death_machine"'
    if '"cc_car", "t5_enfield"' not in text:
        text = text.replace(retired, retired + ', ' + ', '.join(json.dumps(n) for n in REPLACEMENTS))
    write(rel, text)

    for rel in ['scripts/zm/zm_tod2_cybercity/_tod_classes.gsc', 'scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc',
                'ui/uieditor/widgets/HUD/AetheriumWidgets/AetheriumLoadout.lua']:
        text = (ROOT / rel).read_text(encoding='utf-8')
        for old, new in REPLACEMENTS.items():
            # Bat-only presentation must remain bat-only even when it retires.
            if old == 't9_me_baseballbat' and rel.endswith('_tod_upgrades.gsc'):
                text = text.replace('"t9_me_baseballbat"', '"cc_twin_knives"')
            else:
                text = text.replace(old, new)
        if rel.endswith('_tod_classes.gsc'):
            text = text.replace('"ASSAULT",', '"ARCHER",').replace('"SLASHER",', '"WARRIOR",')
        write(rel, text)
    rel = 'scripts/zm/zm_tod2_cybercity.gsc'
    text = (ROOT / rel).read_text(encoding='utf-8')
    text = re.sub(r'level\.tod_dev = false;[^\n]*', 'level.tod_dev = true;   // 2026-09-24: user-requested roster playtest; diagnostics and test money.', text)
    text = re.sub(r'level\.tod_god = false;[^\n]*', 'level.tod_god = true;   // 2026-09-24: user-requested protection for this test.', text)
    write(rel, text)
