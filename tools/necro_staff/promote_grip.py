"""Promote the reviewed seam correction after all native builds have stopped."""
import pathlib,json,shutil,hashlib,subprocess,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff';STAGE=ART/'detail_pass'
command="@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('BlackOps3.exe','linker_modtools.exe','cod2map64.exe','Radiant_modtools.exe','gdtdb.exe') -or ($_.Name -in @('powershell.exe','pwsh.exe') -and $_.CommandLine -match '-File\\s+[^\\r\\n]*tools[\\/]build_map\\.ps1') }).Count"
assert subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True).stdout.strip()=='0','Game or guarded build is active'
meta=json.loads((STAGE/'models.json').read_text());live=json.loads((ART/'models.json').read_text())
assert meta['tags_canonical']==live['tags_canonical'] and meta['view_tags']==live['view_tags']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(STAGE/'tod_necro_staff_art.gdt')==sha(ROOT/'source_data/tod_necro_staff_art.gdt'),'This promotion is mesh-only; unexpected material definition change'
for p in (STAGE/'models').glob('*.png'):
    assert sha(p)==sha(ROOT/'model_export/tod_necro_staff'/p.name),'Unexpected texture change in seam-only promotion'
for r in meta['models']:assert sha(ROOT/r['file'])==r['sha256']
evidence=ROOT/'tmp/necro_staff_build';archive=evidence/('detail3_before_final_'+datetime.datetime.now().strftime('%H%M%S'));archive.mkdir(exist_ok=True)
for name in ['status.json','source_snapshot.json','full_build.log']:
    if (evidence/name).exists():shutil.copy2(evidence/name,archive/name)
for r in meta['models']:
    src=ROOT/r['file'];dest=ROOT/'model_export/tod_necro_staff'/src.name;shutil.copyfile(src,dest)
    r['file']=dest.relative_to(ROOT).as_posix()
(ART/'models.json').write_text(json.dumps(meta,indent=2))
for name in ['staff_master.blend','staff_review.blend','surface_detail_review.blend','tier2_full.png','tier2_head.png','tier3_full.png','tier3_head.png','detail_bone.png','detail_blade.png','detail_grip.png']:
    shutil.copyfile(STAGE/name,ART/name)
record=json.loads((ART/'detail.json').read_text());record['grip_seams']='Separated spiral turns, outer-surface stitching; macro reviewed'
(ART/'detail.json').write_text(json.dumps(record,indent=2))
(evidence/'status.json').write_text(json.dumps(dict(state='source_ready',detail='Final grip seam correction promoted; full build required.',time=datetime.datetime.now().isoformat()),indent=2))
print('FINAL GRIP PROMOTED: exact staged mesh hashes, unchanged grip/FX tags; full build required')
