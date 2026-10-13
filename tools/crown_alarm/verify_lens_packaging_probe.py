"""Check native positive/negative material controls in the isolated probe."""
import datetime
import hashlib
import json
from pathlib import Path
from verify_lens_material import material_records

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_lens_repair/packaging_probe'
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
inputs = json.loads((WORK / 'inputs.json').read_text())
ff = TOOLS / 'zone' / (inputs['zone'] + '.ff')
records, size = material_records(ff, tuple(inputs['materials']))
valid = {'mc/mtl_tod_alarm_cast', 'mc/mtl_tod_alarm_probe_correct_black',
         'mc/mtl_tod_alarm_probe_correct_white', 'mc/mtl_tod_alarm_probe_correct_black_hdr1'}
for name in inputs['materials']:
    complete = [r for r in records if r['name'] == name and r['classification'] == 'complete material definition']
    assert len(complete) == int(name in valid), 'Unexpected native material control: ' + name
proof = {
    'verified_at': datetime.datetime.now().astimezone().isoformat(),
    'inputs': inputs, 'fastfile': str(ff), 'fastfile_bytes': ff.stat().st_size,
    'fastfile_sha256': hashlib.sha256(ff.read_bytes()).hexdigest(),
    'decompressed_bytes': size, 'native_records': records,
    'valid_scalar_specular_masks_pack': True,
    'invalid_full_color_specular_binding_rejected': True,
    'zero_hdr_is_not_the_failure': True,
    'chosen_binding': '$black_specular',
    'native_visual_verified': False,
}
(WORK / 'native_controls.json').write_text(json.dumps(proof, indent=2) + '\n')
print('LENS_PACKAGING_CONTROLS_PASS: compatible scalar mask packs; zero HDR preserved')
