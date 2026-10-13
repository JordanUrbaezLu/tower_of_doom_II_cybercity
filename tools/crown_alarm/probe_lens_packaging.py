"""Prepare isolated native material diagnostics; never edit shipping assets.

The companion guarded PowerShell wrapper owns database/link operations. These
materials are diagnostic controls only, never included by the playable map.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair/packaging_probe'
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
ZONE = 'tod_alarm_lens_packaging_probe'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
WORK.mkdir(parents=True, exist_ok=True)
source = ROOT / 'source_data/tod_crown_alarm.gdt'
deployed = TOOLS / 'source_data/tod_crown_alarm.gdt'
assert sha(source) == sha(deployed), 'Probe requires the current deployed source'
text = source.read_text(encoding='utf-8-sig')
match = re.search(r'\t"mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?\n\t\}', text, re.S)
assert match
base = match.group()
variants = {
    'same': {},
    'zero_black': {'scaleRGB': '1', 'colorTint1': '0 0 0 1'},
    'one_white': {'scaleRGB': '1'},
    'zero_no_shadows': {'noCastShadow': '0', 'noReceiveDynamicShadow': '0'},
    'nonemissive': {'materialType': 'lit_transparent_advanced'},
    'correct_black': {'specColorMap': '$black_specular'},
    'correct_white': {'specColorMap': '$white_specular'},
    'correct_black_hdr1': {'specColorMap': '$black_specular', 'scaleRGB': '1', 'colorTint1': '0 0 0 1'},
}
blocks, material_names = [], ['mc/mtl_tod_alarm_lens', 'mc/mtl_tod_alarm_cast']
for label, values in variants.items():
    name = 'mtl_tod_alarm_probe_' + label
    block = base.replace('"mtl_tod_alarm_lens"', '"' + name + '"', 1)
    for key, value in values.items():
        block, count = re.subn(r'("' + re.escape(key) + r'" ")[^"\n]*(")',
                               lambda m: m[1] + value + m[2], block)
        assert count == 1
    blocks.append(block)
    material_names.append('mc/' + name)
gdt = WORK / 'probe.gdt'
gdt.write_text('{\n' + '\n'.join(blocks) + '\n}\n', encoding='utf-8')
zone = WORK / (ZONE + '.zone')
zone.write_text('// Isolated diagnostics only; never a playable map include.\n'
                + '\n'.join('material,' + n for n in material_names) + '\n', encoding='utf-8')
(WORK / 'inputs.json').write_text(json.dumps({
    'shipping_gdt_sha256': sha(source), 'probe_gdt_sha256': sha(gdt),
    'probe_zone_sha256': sha(zone), 'zone': ZONE, 'materials': material_names,
    'variants': variants, 'shipping_sources_unchanged': True,
    'native_visual_verified': False,
}, indent=2) + '\n', encoding='utf-8')
print('LENS_PACKAGING_PROBE_PREPARED', len(material_names), 'isolated materials')
