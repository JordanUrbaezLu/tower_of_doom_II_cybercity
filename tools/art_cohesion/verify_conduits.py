"""Native bindings, off/on parity and compiled geometry for the fine power wires."""
import pathlib,sys,json,hashlib,csv,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'));from inspect_assets import xmodel
sys.path.insert(0,str(ROOT/'tools/art_cohesion'));from native_preview import fields
p=argparse.ArgumentParser();p.add_argument('--compiled-ledger',type=pathlib.Path);args=p.parse_args()
ART=ROOT/'art/cybercity_materials/color_restoration';manifest=json.loads((ART/'conduit_manifest.json').read_text());gdt=ROOT/'source_data/tod_power_conduits.gdt'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in manifest['textures'].items():assert sha(ROOT/'model_export/tod_surface/_images'/name)==digest
for mat in ['shell','steel','rubber','wire_off','wire_on']:
 f=fields(gdt,'mtl_tod_conduit_'+mat)
 assert float(f['scaleRGB'])==(manifest['on_emission'] if mat=='wire_on' else 0)
 for key in ['colorMap','normalMap','cosinePowerMap','specColorMap']:
  image=fields(gdt,f[key],'image');assert (ROOT/image['baseImage']).exists()
 if mat=='wire_on':assert f['colorTint1']=='1 1 1 1'
compiled={}
if args.compiled_ledger:
 with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f:compiled={r['name']:r for r in csv.DictReader(f)}
models={}
for row in manifest['models']:
 path=ROOT/row['file'];assert sha(path)==row['sha256'];model=xmodel.Model();model.LoadFile_Bin(str(path),split_meshes=True)
 assert len(model.bones)==1 and model.bones[0].name=='tag_origin'
 assert sum(len(m.faces) for m in model.meshes)==row['triangles']
 assert all(f.mesh_id==i for i,m in enumerate(model.meshes) for f in m.faces)
 assert all(v.weights==[(0,1.)] for m in model.meshes for v in m.verts)
 assert all(v.offset[2]>=-.0001 and v.offset[2]<=2.6 for m in model.meshes for v in m.verts)
 assert any(m.name=='mtl_tod_conduit_wire_'+row['asset'].rsplit('_',1)[1] for m in model.materials)
 models[(row['asset'].rsplit('_',1)[1],row['lod'])]=model
 f=fields(gdt,row['asset'],'xmodel');assert f['CollisionMap']=='' and f['BulletCollisionLOD']=='None'
 if compiled:
  r=compiled[row['asset']];assert int(r['lodCount'])==3
  assert int(r['tris'+str(2-row['lod'])])==row['triangles'],(row['asset'],row['lod'])
for lod in range(3):
 a,b=models['off',lod],models['on',lod]
 assert [[v.offset for v in m.verts] for m in a.meshes]==[[v.offset for v in m.verts] for m in b.meshes]
 assert [len(m.faces) for m in a.meshes]==[len(m.faces) for m in b.meshes]
report=dict(models=2,lods=6,textures=20,emission_off=0,emission_on=manifest['on_emission'],compiled_checked=bool(compiled),native_visual_verified=False)
(ART/('conduit_compiled_validation.json' if compiled else 'conduit_source_validation.json')).write_text(json.dumps(report,indent=2))
print('CONDUIT_ASSETS_PASS',json.dumps(report))
import subprocess
command=[sys.executable,'-B',str(ROOT/'tools/art_cohesion/verify_conduit_batches.py')]
if args.compiled_ledger:command+=['--compiled-ledger',str(args.compiled_ledger)]
subprocess.run(command,cwd=ROOT,check=True)
