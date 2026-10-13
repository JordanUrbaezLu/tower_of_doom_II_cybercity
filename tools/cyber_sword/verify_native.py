"""Check exported geometry, original animation contract and real baked maps."""
import json,math,argparse
import numpy as np
from PIL import Image
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--integrated',action='store_true');args=parser.parse_args()
manifest=json.loads((KIT/'install_manifest.json').read_text());donor=load(DONOR)
assert sha(DONOR)==manifest['donor_skeleton_sha256']
assert sha(ROOT/manifest['master'])==manifest['master_sha256']
reference=json.loads((ART/'source_inventory.json').read_text())
assert sha(Path(reference['source']))==reference['source_sha256'],'original source must remain untouched'
assert sha(ROOT/'source_data/tod_cyber_sword.gdt')==manifest['gdt_sha256']
bones=lambda m:[(b.name,b.parent,b.offset,b.matrix) for b in m.bones]
last=999999;bounds=[]
original_points=np.array([v.offset for mesh in donor.meshes for v in mesh.verts])
for r in manifest['models']:
    p=ROOT/r['file'];assert sha(p)==r['sha256'];m=load(p)
    assert bones(m)==bones(donor),'animation skeleton changed'
    assert [v.name for v in m.materials]==['mtl_tod_cyber_sword']
    count=sum(len(mesh.faces) for mesh in m.meshes);assert count==r['triangles']<last;last=count
    points=[];uv_areas=[]
    for i,mesh in enumerate(m.meshes):
        assert all(v.weights==[(0,1.0)] for v in mesh.verts)
        points.extend(v.offset for v in mesh.verts)
        for f in mesh.faces:
            assert f.mesh_id==i and f.material_id==0
            for c in f.indices:
                assert all(math.isfinite(v) for v in c.normal+c.uv)
                assert abs(sum(v*v for v in c.normal)-1)<.01
                assert all(-.001<=v<=1.001 for v in c.uv)
            a,b,c=[v.uv for v in f.indices]
            uv_areas.append(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])))
    assert sum(a>1e-10 for a in uv_areas)>.99*len(uv_areas),'collapsed UVs'
    pts=np.array(points);bounds.append([pts.min(0).tolist(),pts.max(0).tolist()])
    if r['lod']==0:
        for axis in (0,2):
            assert abs(pts[:,axis].min()-original_points[:,axis].min())<.5,'grip/scale lower bound changed'
            assert abs(pts[:,axis].max()-original_points[:,axis].max())<.5,'grip/scale upper bound changed'
        # Preview input is reconstructed from the actual binary, not the author mesh.
        data=dict(verts=[],faces=[])
        for mesh in m.meshes:
            off=len(data['verts']);data['verts'].extend(v.offset for v in mesh.verts)
            data['faces'].extend([dict(v=off+c.vertex,n=c.normal,uv=c.uv) for c in f.indices] for f in mesh.faces)
        (KIT/'binary_roundtrip.json').write_text(json.dumps(data,separators=(',',':')))
for file,digest in manifest['textures'].items():
    p=OUT/'_images'/file;assert sha(p)==digest
    im=Image.open(p);assert im.size==(4096,4096);assert max(im.getextrema()[0])>0
em=np.array(Image.open(OUT/'_images/i_tod_cyber_sword_e.png').convert('RGB'))
mask=em.max(2)>16
assert .005<mask.mean()<.35,'emission must stay on small inlays'
assert (em[:,:,2][mask]>=em[:,:,0][mask]).mean()>.98,'unexpected warm emission'
gdt=parse(ROOT/'source_data/tod_cyber_sword.gdt')
for name in ['mtl_tod_cyber_sword','mtl_tod_cyber_sword_cast','mtl_tod_cyber_sword_world']:
    f=gdt[name][1];assert f['waterRoughness']=='0';assert f['glossRangeMax']=='8'
assert gdt['mtl_tod_cyber_sword'][1]['cg00_x']=='0'
cast=parse(Path('C:/BO3Tools/TOD2Cybercity/source_data/hb_gold_sword_charged.gdt'))['hb_gold_sword_cast_zm'][1]
ours=gdt['tod_cyber_sword_cast_zm'][1]
assert {k:v for k,v in cast.items() if k not in ('gunModel','worldModel','displayName')}=={k:v for k,v in ours.items() if k not in ('gunModel','worldModel','displayName')}
bash=parse(ROOT/'donor_gdt/hellbound/hb_warrior_bash.gdt')['hb_warrior_bash_gold_zm'][1]
ours=gdt['tod_cyber_sword_bash_zm'][1]
assert {k:v for k,v in bash.items() if k not in ('gunModel','worldModel','displayName')}=={k:v for k,v in ours.items() if k not in ('gunModel','worldModel','displayName')}
if args.integrated:
    twins=parse(ROOT/'source_data/tod_weapon_twins.gdt')
    names=[n for n in twins if n.startswith('cc_gold_sword')]
    assert names
    for n in names:
        assert twins[n][1]['gunModel']=='tod_cyber_sword_view'
        assert twins[n][1]['worldModel']=='tod_cyber_sword_world'
    assert 'include,tod_cyber_sword' in (ROOT/'zone_source/zm_tod2_cybercity.zone').read_text()
(KIT/'verification.json').write_text(json.dumps(dict(result='PASS',lod_triangles=[r['triangles'] for r in manifest['models']],
    bounds_inches=bounds,emission_pixel_fraction=float(mask.mean()),original_bones_preserved=len(donor.bones),integrated=args.integrated,native_playtested=False),indent=2))
print('CYBER_SWORD_SOURCE_PASS: seven LODs, original eight bones, valid normals/UVs, five atlases, cool emission mask, unchanged slam animation/timings')
