"""Snapshot before build; prove exact art/map inputs and native packed coverage."""
import pathlib,sys,hashlib,json,csv,datetime,sqlite3
from profiles import PROFILES
from surface_definition import DEFINITIONS,definition
ROOT=pathlib.Path(__file__).resolve().parents[2];MT=pathlib.Path('C:/BO3Tools/TOD2Cybercity');DEP=MT/'usermaps/zm_tod2_cybercity';ART=ROOT/'art/cybercity_materials'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
    paths=[]
    for folder in ('scripts','ui','zone_source','sound','model_export/tod_surface','model_export/tod_shop','model_export/tod_teleporter','model_export/tod_heavenly_altar','share/raw/fx/tod/shop','share/raw/fx/tod/teleporter','sound_assets/tod/shop'):
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and not any(x in ('all','english','loc','__pycache__') for x in p.relative_to(ROOT/folder).parts))
    for name in ('tod_surface','tod_power_conduits','tod_conduit_batches','tod_shop','tod_teleporter','tod_teleporter_states','tod_heavenly_altar','tod_materials','tod_skybox'):paths.append(ROOT/'source_data'/(name+'.gdt'))
    paths.extend([ROOT/'map_source/zm/zm_tod2_cybercity.map',ROOT/'source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr'])
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths}
snapshot=ART/'build_inputs.json'
if '--snapshot' in sys.argv:
    snapshot.write_text(json.dumps({'time':datetime.datetime.now().isoformat(),'inputs':inputs()},indent=2));print('ART_BUILD_SNAPSHOT',len(json.loads(snapshot.read_text())['inputs']));raise SystemExit
captured=json.loads(snapshot.read_text());assert inputs()==captured['inputs'],'Sources changed after snapshot'
ff=DEP/'zone/zm_tod2_cybercity.ff';stamp=ff.stat().st_mtime;assert stamp>snapshot.stat().st_mtime
for name,digest in captured['inputs'].items():
    p=pathlib.Path(name);target=(MT if p.parts[0] in ('model_export','source_data','share','sound_assets','map_source') else DEP)/p
    assert target.is_file() and sha(target)==digest,('deployment',name)
    assert target.stat().st_mtime<=stamp,('synced after build',name)
assets=set()
for lang in ('all','english'):
    p=DEP/'zone_source'/lang/'assetinfo/zm_tod2_cybercity.csv';assert p.stat().st_mtime>snapshot.stat().st_mtime
    with p.open(encoding='utf-8-sig',newline='') as f:
        assets.update((r['type'],r['name']) for r in csv.DictReader(f))
coverage=json.loads((ART/'crown_validation.json').read_text())
world_materials=set(coverage['world_materials'])|{coverage['gate_material']}
tiles={DEFINITIONS[name.removeprefix('tod_cc_')]['tile'] for name in world_materials}
for name in world_materials:assert ('material','wc/'+name) in assets,('world material',name)
for tile in tiles:
    for suffix in 'cnsge':assert ('image','i_tod_cc_'+tile+'_'+suffix) in assets,(tile,suffix)
for name in ('tod_teleporter','tod_teleporter_off','tod_tp_recharge','tod_heavenly_altar','tod_shop_solid'):assert ('xmodel',name) in assets,name
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True);db.execute('pragma writable_schema=ON');db.row_factory=sqlite3.Row
checked={}
for name,role in [('mtl_tod_teleporter','teleporter'),('mtl_tod_tp_off','teleporter'),('mtl_tod_altar','altar')]+[('tod_cc_'+k,'architecture') for k in DEFINITIONS]:
    row=dict(db.execute('select * from material where _name=?',(name,)).fetchone())
    expected=PROFILES[role] if role!='architecture' else definition(name.removeprefix('tod_cc_'))
    for key,val in expected.items():assert (row[key]==val if isinstance(val,str) else float(row[key])==val),(name,key,row[key],val)
    checked[name]={k:row[k] for k in PROFILES[role]}
report={'ff_bytes':ff.stat().st_size,'ff_sha256':sha(ff),'ff_time':datetime.datetime.fromtimestamp(stamp).isoformat(),'inputs_matched':len(captured['inputs']),'world_materials_packed':len(world_materials),'surface_images_packed':len(tiles)*5,'native_profiles':checked,'source_and_deployment_match':True,'game_launched':False,'native_visual_approved':False}
(ART/'deployment.json').write_text(json.dumps(report,indent=2)+'\n');print('ART_DEPLOYMENT_PASS',json.dumps({k:v for k,v in report.items() if k!='native_profiles'}))
