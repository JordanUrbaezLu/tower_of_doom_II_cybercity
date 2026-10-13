"""Read-only donor inventory and pre-migration balance snapshot for this map."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
OUT = ROOT / 'tmp/expected_roster'


def blocks(path):
    text = path.read_text(encoding='utf-8-sig')
    result = {}
    for m in re.finditer(r'"([^"\n]+)"\s*\(\s*"([^"\n]+\.gdf)"\s*\)\s*\{([^{}]*)\}', text):
        result[m[1]] = dict(type=m[2], fields=dict(re.findall(r'"([^"\n]+)"\s+"((?:\\.|[^"\\])*)"', m[3])))
    return result


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'source_data/tod_weapon_twins.gdt'
    baseline = OUT / 'baseline_weapons.json'
    if not baseline.exists():
        baseline.write_text(json.dumps(blocks(source), indent=2))
    paths = ['hb_r99.gdt', 'hb_warrior_tiers.gdt', 'hb_gold_sword.gdt',
             'hb_bow.gdt', 'hb_crossbow.gdt', 'hb_fire_bow.gdt']
    donors = {}
    for name in paths:
        donor = blocks(TOOLS / 'source_data' / name)
        donors[name] = donor
        for asset, data in donor.items():
            if 'weapon.gdf' not in data['type'] or re.search(r'_q[0-9]', asset):
                continue
            wanted = ['displayName', 'gunModel', 'worldModel', 'damage', 'minDamage',
                      'meleeDamage', 'fireTime', 'meleeTime', 'meleeChargeTime', 'clipSize',
                      'reloadTime', 'reloadEmptyTime', 'maxAmmo', 'weaponType', 'weaponClass',
                      'altWeapon', 'DualWieldWeapon', 'projExplosionType', 'explosionInnerDamage',
                      'explosionOuterDamage', 'projectileModel', 'projImpactExplode', 'chargeType',
                      'chargeTime', 'chargeShot0', 'continuousFire', 'fireSound', 'fireSoundPlayer']
            print(asset, json.dumps({k: data['fields'].get(k) for k in wanted if data['fields'].get(k)}))
    (OUT / 'donors.json').write_text(json.dumps(donors, indent=2))
