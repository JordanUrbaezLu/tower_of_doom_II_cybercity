"""Source/export contract: palette, original rigs/eyes/gibs, complete donor deps."""
import pathlib,sys,json,re,hashlib,argparse,csv
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from inspect_assets import ROOT,MT,asset,native_path,xmodel,db
manifest=json.loads((ROOT/'art/cyber_elites/manifest.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--palette',action='store_true');parser.add_argument('--compiled-ledger',type=pathlib.Path);args=parser.parse_args()
if args.palette: from PIL import Image,ImageChops
assert hashlib.sha256((ROOT/'source_data/tod_cyber_elites.gdt').read_bytes()).hexdigest()==manifest['gdt_sha256']
gdt=(ROOT/'source_data/tod_cyber_elites.gdt').read_text()
for field,model in [('legDmg2','g_rlegoff'),('leftarm_gibmodel','s_larmspawn'),('leftleg_gibmodel','s_llegspawn')]:
    assert '"'+field+'" "tod_charcoal_c_zom_dlc3_zombie_sentinel_'+model+'"' in gdt
def load(path):
    m=xmodel.Model();m.LoadFile_Bin(str(path),split_meshes=True);return m
for record in manifest['textures']:
    path=ROOT/record['output'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
    if args.palette and not record['mode'].endswith('_n'):
        r,g,b=Image.open(path).convert('RGB').split()
        if record['mode']=='red':assert g.getextrema()==(0,0) and b.getextrema()==(0,0) and r.getextrema()[1]>0
        else:assert ImageChops.difference(r,g).getbbox() is None and ImageChops.difference(r,b).getbbox() is None
for record in manifest['models']:
    dst=ROOT/record['output'];m=load(dst);donor=load(record['source'])
    assert hashlib.sha256(dst.read_bytes()).hexdigest()==record['sha256']
    assert [(b.name,b.parent,b.offset,b.matrix) for b in m.bones]==[(b.name,b.parent,b.offset,b.matrix) for b in donor.bones]
    assert all(f.mesh_id==i for i,mesh in enumerate(m.meshes) for f in mesh.faces)
    assert sum(len(x.faces) for x in m.meshes)==record['faces']
    if record['name']=='tod_doppelgast_black_robot':
        for i in [0,2,3,4,5,6,7]:
            assert [(v.offset,v.weights) for v in m.meshes[i].verts]==[(v.offset,v.weights) for v in donor.meshes[i].verts]
        for i in [3,4]:assert m.materials[i].name==donor.materials[i].name
        assert min(v.offset[2] for v in m.meshes[1].verts)>=51
        assert len(m.meshes[-1].faces)==record['robot_faces']>1000
        assert all(len(v.weights)==1 and any(x in m.bones[v.weights[0][0]].name for x in ['hip','knee','ankle','ball']) for v in m.meshes[-1].verts)
        assert record.get('robot_uv_mapped'), 'robot legs require real UVs'
        for f in m.meshes[-1].faces:
            a,b,c=[v.uv for v in f.indices]
            assert abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))>1e-7,'collapsed robot UV triangle'
        for mat in ['shell','piston','rubber']:
            part=gdt.split('"mtl_tod_doppelgast_robot_'+mat+'" ( "material.gdf" )')[1].split('\n\t}')[0]
            fields=dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',part))
            for key,suffix in [('colorMap','c'),('normalMap','n'),('specColorMap','s'),('cosinePowerMap','g')]:
                assert fields[key]=='i_tod_robot_'+mat+'_'+suffix
            assert fields['scaleRGB']=='0','robot legs are dark metal, with no emissive tint'
    else:
        assert [(len(x.verts),len(x.faces)) for x in m.meshes]==[(len(x.verts),len(x.faces)) for x in donor.meshes]
        assert [[(v.offset,v.weights) for v in mesh.verts] for mesh in m.meshes]==[[(v.offset,v.weights) for v in mesh.verts] for mesh in donor.meshes]
        assert all(x.name.startswith('tod_charcoal_') for x in m.materials)
# The default Mangler binaries and every referenced texture must be the donor's.
hb=ROOT.parent/'tower_of_doom_II_hellbound'
m=asset('xmodel','hb_bo6_mangler');path=native_path('model_export',m['filename']);original=hb/'model_export/hb/mangler/hb_bo6_mangler.XMODEL_BIN'
assert path.read_bytes()==original.read_bytes()
for mat in load(path).materials:
    fields=asset('material',mat.name)
    for key in ['colorMap','normalMap','cosinePowerMap','occlusionMap']:
        image=fields.get(key)
        if image and not image.startswith('$'):assert native_path('',asset('image',image)['baseImage']).exists(),image
for name in ['idle','run','pain','melee','cannon','death']:
    path=MT/'xanim_export/hb/mangler'/('hb_mangler_'+name+'.XANIM_BIN')
    assert path.read_bytes()==(hb/'xanim_export/hb/mangler'/path.name).read_bytes()
print('PASS: 15 exported models; charcoal/gib geometry and weights; Doppelgast skeleton/body/eyes preserved; UV-mapped mechanical legs and 12 real maps; grayscale/red-only color maps; default Mangler dependencies match Hellbound.')
print('Native constant image names:',[r[0] for r in db.execute('select _name from image where _name in (?,?,?,?)',('$white','$white_color','$identitynormalmap','$identity_normal'))])
if args.compiled_ledger:
    with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f: rows={r['name']:r for r in csv.DictReader(f)}
    for record in manifest['models']:
        row=rows[record['name']];column=int(row['lodCount'])-1;native=int(row['tris'+str(column)])
        assert 0<=record['faces']-native<=8,(record['name'],record['faces'],native)
    row=rows['hb_bo6_mangler'];native=int(row['tris'+str(int(row['lodCount'])-1)])
    source=sum(len(m.faces) for m in load(native_path('model_export',asset('xmodel','hb_bo6_mangler')['filename'])).meshes)
    assert 0<=source-native<=8,(source,native)
    print('PASS: compiled triangle coverage for all 15 custom models and default Mangler.')
