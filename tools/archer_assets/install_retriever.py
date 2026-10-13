"""Convert the recovered MOTD world model for this map's native asset root."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
from install_native import block

SOURCE=ROOT/'source_library/archer_equipment/retriever/model_export'
OUT=ROOT/'model_export/tod_archer';ART=ROOT/'art/archer_assets/engine_kit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    records=[]
    for lod in range(3):
        model=xmodel.Model();model.LoadFile_Bin(str(SOURCE/f't6_wpn_zmb_tomahawk_world_lod{lod}.xmodel_bin'))
        for material in model.materials:
            old=material.name
            key='blade' if old.endswith('_blade') else 'fringe' if '_alpha' in old else 'body'
            material.name='mtl_tod_retriever_'+key
        # The source is rigid with tag_weapon only. Keep its geometry and add
        # a separate FX attachment near the blade; do not move the model root.
        blade=[v.offset for mesh in model.meshes for v in mesh.verts]
        center=tuple(sum(v[i] for v in blade)/len(blade) for i in range(3))
        tag=xmodel.Bone('tag_knife_fx');tag.parent=0;tag.offset=center;tag.matrix=[(1,0,0),(0,1,0),(0,0,1)]
        model.bones.append(tag)
        path=OUT/f'tod_archer_retriever_world_lod{lod}.xmodel_bin';model.WriteFile_Bin(str(path),version=7)
        records.append({'asset':'tod_archer_retriever_world','lod':lod,'file':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'triangles':sum(len(mesh.faces) for mesh in model.meshes)})
    fields={'filename':'tod_archer\\\\tod_archer_retriever_world_lod0.xmodel_bin','mediumLod':'tod_archer\\\\tod_archer_retriever_world_lod1.xmodel_bin','lowLod':'tod_archer\\\\tod_archer_retriever_world_lod2.xmodel_bin','mediumLodDist':300,'lowLodDist':800,'type':'rigid','scale':1,'CollisionMap':'','BulletCollisionLOD':'None','physicsPreset':'','noCastShadow':0}
    blocks=[block('tod_archer_retriever_world','xmodel',fields)]
    for key in ('body','blade','fringe'):
        prefix='i_tod_retriever_'+key
        fields={'surfaceType':'metal' if key=='blade' else 'wood','template':'material.template','materialCategory':'Geometry','materialType':'lit','colorMap':prefix+'_col','normalMap':prefix+'_nml','cosinePowerMap':prefix+'_gls','specColorMap':prefix+'_spc','specMapEnable':1,'colorTint':'1 1 1 1','normalHeightScale':1,'glossRangeMin':0,'glossRangeMax':8,'specAmount':.4,'usage':'<not in editor>'}
        if key=='fringe':fields['materialType']='lit_alphatest_nocull'
        blocks.append(block('mtl_tod_retriever_'+key,'material',fields))
    gdt=ROOT/'source_data/tod_retriever.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')
    manifest=json.loads((ART/'install_manifest.json').read_text())
    manifest['models']=[r for r in manifest['models'] if r['asset']!='tod_archer_retriever_world']+records
    manifest['additional_gdts']={'source_data/tod_retriever.gdt':sha(gdt)}
    (ART/'install_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('RETRIEVER_NATIVE_INSTALLED',[(r['lod'],r['triangles']) for r in records])

if __name__=='__main__':main()
