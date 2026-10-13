"""Read the installed pad definitions and preserve their measured assembly."""
import json, sqlite3, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/teleporter'
OUT.mkdir(parents=True, exist_ok=True)
MT = Path('C:/BO3Tools/TOD2Cybercity')
sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
db = sqlite3.connect((MT / 'gdtdb/gdt.db').as_uri() + '?mode=ro', uri=True)
db.execute('pragma writable_schema=ON')
db.row_factory = sqlite3.Row
def entry(kind, name):
    row = db.execute('select * from '+kind+' where _name=?', (name,)).fetchone()
    assert row is not None, (kind, name)
    return {k:v for k,v in dict(row).items() if not k.startswith('_') and k != 'PK_id' and v is not None}
report = {'models':{}, 'materials':{}, 'images':{}}
for name in ('p7_zm_der_teleporter','p7_zm_der_teleporter_pad_wires_blue','p7_zm_der_teleporter_pad_wires_red','p7_zm_der_teleporter_pad_glass'):
    fields = entry('xmodel', name)
    path = MT / 'model_export' / fields['filename'].replace('\\','/')
    m = xmodel.Model(); m.LoadFile_Bin(str(path), split_meshes=False)
    coords = [v.offset for mesh in m.meshes for v in mesh.verts]
    report['models'][name] = {'fields':fields, 'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'bounds':[[min(p[i] for p in coords) for i in range(3)],[max(p[i] for p in coords) for i in range(3)]], 'triangles':sum(len(mesh.faces) for mesh in m.meshes), 'materials':[mat.name for mat in m.materials]}
    for mat in m.materials:
        props = entry('material', mat.name); report['materials'][mat.name] = props
        for key, val in props.items():
            if key in ('colorMap','normalMap','cosinePowerMap','specColorMap','colorMap00') and val and not val.startswith('$'):
                try: report['images'][val] = entry('image', val)
                except AssertionError: pass
(OUT / 'original_sources.json').write_text(json.dumps(report, indent=2))
print(json.dumps({n:{k:v for k,v in x.items() if k!='fields'} for n,x in report['models'].items()}, indent=2))
