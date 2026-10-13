"""Record the complete installed Archer kit after all native asset stages."""
import hashlib,json,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel,xanim
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
path=ROOT/'art/archer_assets/engine_kit/install_manifest.json';manifest=json.loads(path.read_text())
manifest['additional_gdts']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'source_data').glob('tod_archer*.gdt')) if p.name!='tod_archer.gdt'}
manifest['additional_gdts']['source_data/tod_retriever.gdt']=sha(ROOT/'source_data/tod_retriever.gdt')
manifest['textures']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'model_export/tod_archer/_images').iterdir()) if p.suffix.lower() in ('.png','.tiff','.tif')}
for name in ['tod_archer_bo2_hands','tod_archer_retriever_view','tod_archer_grapple_hands','tod_archer_grapple_view']:
    p=ROOT/'model_export/tod_archer'/(name+'.xmodel_bin');m=xmodel.Model();m.LoadFile_Bin(str(p))
    manifest['models']=[r for r in manifest['models'] if r['asset']!=name]
    manifest['models'].append({'asset':name,'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'triangles':sum(len(mesh.faces) for mesh in m.meshes),'bones':len(m.bones)})
manifest['animations']=[]
for p in sorted((ROOT/'xanim_export/tod_archer').glob('*.xanim_bin')):
    a=xanim.Anim();a.LoadFile_Bin(str(p))
    manifest['animations'].append({'asset':p.stem,'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'frames':len(a.frames),'fps':a.framerate,'bones':len(a.parts)})
manifest['conversion_models']={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'model_export/tod_archer').glob('*_rig.xmodel_bin'))}
p=ROOT/'sound_assets/tod/archer/axe_first_raise.wav'
with wave.open(str(p),'rb') as wav:duration=wav.getnframes()/wav.getframerate()
manifest['audio']=[r for r in manifest['audio'] if r['alias']!='tod_archer_axe_first_raise']
source=next((ROOT/'source_library/archer_equipment/retriever').rglob('*first_raise*.wav'),None)
if source is None:source=next((ROOT/'source_library/archer_equipment/retriever').rglob('*first_raise*.flac'))
manifest['audio'].append({'alias':'tod_archer_axe_first_raise','source':source.relative_to(ROOT).as_posix(),'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'seconds':duration})
manifest['gdt_sha256']=sha(ROOT/'source_data/tod_archer.gdt');manifest['native_tested']=False
path.write_text(json.dumps(manifest,indent=2)+'\n')
print('ARCHER_MANIFEST',len(manifest['models']),'model/LOD files;',len(manifest['animations']),'animations;',len(manifest['textures']),'textures;',len(manifest['audio']),'audio samples')
