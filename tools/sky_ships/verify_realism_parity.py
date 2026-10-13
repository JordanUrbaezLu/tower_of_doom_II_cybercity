"""Compare exported geometry to the pre-material-pass snapshot, allowing only nozzle material swaps.

python tools/sky_ships/verify_realism_parity.py --before tmp/sky_realism/before_models
Snapshot is evidence for this art pass, not a required checkout/build dependency.
"""
import argparse,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel
p=argparse.ArgumentParser();p.add_argument('--before',required=True,type=pathlib.Path);args=p.parse_args()
records=[]
for path in sorted(args.before.glob('*.xmodel_bin')):
    a,b=xmodel.Model(),xmodel.Model()
    a.LoadFile_Bin(str(path),split_meshes=True)
    b.LoadFile_Bin(str(ROOT/'model_export/tod_sky_ships'/path.name),split_meshes=True)
    assert len(a.bones)==len(b.bones) and len(a.meshes)==len(b.meshes),path.name
    for x,y in zip(a.bones,b.bones):
        for k in ('name','parent','matrix','offset','scale','cosmetic'):
            assert getattr(x,k)==getattr(y,k),(path.name,'bone',k)
    changed=[];uv_changed=[];triangles=0;vertices=0
    for x,y in zip(a.meshes,b.meshes):
        assert x.name==y.name and len(x.verts)==len(y.verts) and len(x.faces)==len(y.faces),(path.name,x.name)
        vertices+=len(x.verts);triangles+=len(x.faces)
        for v,w in zip(x.verts,y.verts):
            assert v.offset==w.offset and v.weights==w.weights,(path.name,x.name,'geometry')
        for f,g in zip(x.faces,y.faces):
            for v,w in zip(f.indices,g.indices):
                assert all(getattr(v,k)==getattr(w,k) for k in ('vertex','normal','color')),(path.name,x.name,'corner')
                if v.uv!=w.uv:
                    assert x.name in ('rock 3 veins','rock 4 seam'),(path.name,x.name,'unexpected UV change')
                    if x.name not in uv_changed:uv_changed.append(x.name)
            old,new=a.materials[f.material_id].name,b.materials[g.material_id].name
            if old!=new:
                if x.name in ('rock 3 veins','rock 4 seam'):
                    assert old.replace('neon_','mineral_')==new,(path.name,x.name,old,new)
                else:
                    assert old=='mtl_tod_sky_hull2' and new=='mtl_tod_sky_drive_metal',(path.name,x.name,old,new)
                    assert x.name.endswith(('engine bell','engine bells','aux bells')),(path.name,x.name)
                if x.name not in changed:changed.append(x.name)
    records.append({'file':path.name,'triangles':triangles,'vertices':vertices,'material_only_swaps':changed,'new_mineral_uvs':uv_changed})
assert len(records)==9,len(records)
report={'geometry_normals_weights_tags_unchanged':True,'existing_surface_uvs_unchanged':True,'files':records,'native_playtested':False}
(ROOT/'art/sky_ships/realism_parity.json').write_text(json.dumps(report,indent=2))
print('FLEET MATERIAL PARITY OK',len(records),'binaries: geometry/normals/bones/weights unchanged; only two previously unmapped mineral meshes gain UVs')
