"""Promote reviewed staged art only after the preceding guarded build is idle."""
import pathlib,json,shutil,hashlib,subprocess,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff';STAGE=ART/'detail_pass';OUT=ROOT/'model_export/tod_necro_staff';EVIDENCE=ROOT/'tmp/necro_staff_build'
state=json.loads((EVIDENCE/'status.json').read_text(encoding='utf-8-sig'))
assert state['state'] in {'built','interrupted'},'Do not replace inputs during an active build'
check=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-Process BlackOps3,linker_modtools,cod2map64,Radiant_modtools,gdtdb -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True)
assert check.stdout.strip()=='0','Game or native builder is active'
meta=json.loads((STAGE/'models.json').read_text());prior=json.loads((ART/'models.json').read_text())
assert meta['tags_canonical']==prior['tags_canonical'] and meta['view_tags']==prior['view_tags'],'FX attachment positions changed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in meta['models']:assert sha(ROOT/r['file'])==r['sha256']
assert len(meta['models'])==12
detail=json.loads((STAGE/'detail.json').read_text());assert detail['recessed_blades']==11 and detail['material_images']==19 and 'bone_pigmentation' in detail
archive=ART/'iteration2';archive.mkdir(exist_ok=True)
for p in ART.iterdir():
    if p.is_file() and p.suffix in {'.png','.json'}:shutil.copy2(p,archive/p.name)
archive=EVIDENCE/'iteration2';archive.mkdir(exist_ok=True)
for name in ['status.json','source_snapshot.json','full_build.log','deployment.log']:shutil.copy2(EVIDENCE/name,archive/name)
for pattern in ['*.png','tod_necro_staff*.XMODEL_BIN','materials.gdtpart']:
    for p in (STAGE/'models').glob(pattern):shutil.copyfile(p,OUT/p.name)
shutil.copyfile(STAGE/'tod_necro_staff_art.gdt',ROOT/'source_data/tod_necro_staff_art.gdt')
for r in meta['models']:r['file']='model_export/tod_necro_staff/'+pathlib.Path(r['file']).name
(ART/'models.json').write_text(json.dumps(meta,indent=2))
for name in ['staff_master.blend','staff_review.blend','first_person_review.blend','detail.json','material_bindings.json']:
    shutil.copyfile(STAGE/name,ART/name)
for p in STAGE.glob('tier*.png'):shutil.copyfile(p,ART/p.name)
record=json.loads((ART/'authoring.json').read_text());record['detail_pass']=detail
(ART/'authoring.json').write_text(json.dumps(record,indent=2))
# The native audit must now require the extra four leather images.
p=ROOT/'tools/necro_staff/record_build.py';s=p.read_text()
s=s.replace("or _name like 'i_tod_necro_staff_soul_%'","or _name like 'i_tod_necro_staff_soul_%' or _name like 'i_tod_necro_leather_%'")
s=s.replace('len(resident)==15','len(resident)==19').replace("'i_tod_necro_forge','i_tod_necro_bone'","'i_tod_necro_forge','i_tod_necro_bone','i_tod_necro_leather'")
p.write_text(s)
(EVIDENCE/'status.json').write_text(json.dumps(dict(state='source_ready',time=datetime.datetime.now().isoformat(),detail='Hero detail 3 promoted; full guarded build required. Prior build archived as iteration2.'),indent=2))
print('DETAIL 3 PROMOTED: native model/map inputs ready; preceding deployment archived; FULL rebuild required')
