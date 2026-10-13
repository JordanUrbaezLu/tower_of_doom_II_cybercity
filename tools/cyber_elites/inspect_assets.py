"""Read-only donor inventory for the Cybercity elite/charcoal roster."""
import json, pathlib, sqlite3, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
MT = pathlib.Path('C:/BO3Tools/TOD2Cybercity')
sys.path.insert(0, str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
db = sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro', uri=True)
db.execute('pragma writable_schema=ON'); db.row_factory = sqlite3.Row
def asset(kind, name):
    row = db.execute('select * from '+kind+' where _name=?', (name,)).fetchone()
    assert row is not None, (kind,name)
    return {k:v for k,v in dict(row).items() if not k.startswith('_') and k!='PK_id' and v is not None}
def native_path(folder, name):
    return MT/folder/name.replace('\\\\','/').replace('\\','/')
def main():
    for kind,pattern in [('xmodel','hb_bo6_doppelghast'),('material','%ghoul%'),('aitype','%charred%'),('character','%charred%'),('material','%charred%')]:
        for row in db.execute('select _name from '+kind+' where _name like ?', (pattern,)):
            name=row[0]; fields=asset(kind,name)
            print(kind,name,json.dumps({k:v for k,v in fields.items() if v and any(x.lower() in k.lower() for x in ['file','body','head','eye','material','map','tint','scaleRGB','type','character','skin'])}))
    fields=asset('xmodel','hb_bo6_doppelghast')
    model=xmodel.Model();model.LoadFile_Bin(str(native_path('model_export',fields['filename'])),split_meshes=True)
    print('DOPPEL BONES',json.dumps([{'id':i,'name':b.name,'parent':b.parent,'offset':b.offset,'matrix':b.matrix} for i,b in enumerate(model.bones) if any(s in b.name.lower() for s in ['hip','knee','ankle','ball','toe','pelvis','head','eye'])]))
    print('DOPPEL MESHES',json.dumps([{'name':m.name,'verts':len(m.verts),'faces':len(m.faces),'bounds':[[min(v.offset[j] for v in m.verts),max(v.offset[j] for v in m.verts)] for j in range(3)],'materials':sorted(set(model.materials[f.material_id].name for f in m.faces))} for m in model.meshes]))
    print('DOPPEL MATERIALS',json.dumps([{'name':m.name,'fields':{k:v for k,v in asset('material',m.name).items() if v and any(s in k.lower() for s in ['map','tint','scalergb','type'])}} for m in model.materials]))
if __name__=='__main__': main()
