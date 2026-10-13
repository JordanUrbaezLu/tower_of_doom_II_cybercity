"""Install the reviewed staged alarm sources; never build, sync or launch.

Only run in the parent's coordinated idle window. All existing source inputs
must still match their capture, so a peer's changes can never be overwritten.
"""
import csv, hashlib, io, json, pathlib, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
WORK=ROOT/'tmp/alarm_realism';BASE=WORK/'baseline';STAGE=WORK/'staged'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
procs=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True)
names={r[0].lower() for r in csv.reader(io.StringIO(procs)) if r}
assert not names.intersection({'blackops3.exe','linker_modtools.exe','cod2map64.exe','radiant_modtools.exe'}),'Game/build active; keep staged inputs intact'
subprocess.run([sys.executable,'-B',str(ROOT/'tools/crown_alarm/verify_surface_realism.py'),'--staged'],check=True)
for p in BASE.rglob('*'):
    if p.is_file():
        live=ROOT/p.relative_to(BASE)
        assert live.exists() and sha(live)==sha(p),'Captured input changed: '+str(live)
installed=[]
for family in ('crown_alarm','alarm_button'):
    # Preserve the real originals, including every exported UV and native map,
    # for deterministic future regeneration and honest matched comparisons.
    archive=ROOT/'art'/family/'realism_before'
    for p in BASE.rglob('*'):
        if p.is_file() and (('/'+family+'/') in p.as_posix() or ('/tod_'+family+'/') in p.as_posix() or p.name=='tod_'+family+'.gdt'):
            dst=archive/p.relative_to(BASE);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists():assert sha(dst)==sha(p),'Original archive conflict'
            else:shutil.copy2(p,dst)
    for folder in (STAGE/'art'/family,STAGE/'model_export'/('tod_'+family)):
        for p in folder.rglob('*'):
            if not p.is_file() or p.suffix=='.blend1':continue
            dst=ROOT/p.relative_to(STAGE)
            if dst.exists() and sha(dst)==sha(p):continue
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);installed.append(p.relative_to(STAGE).as_posix())
    p=STAGE/'source_data'/('tod_'+family+'.gdt');dst=ROOT/p.relative_to(STAGE)
    if sha(p)!=sha(dst):shutil.copy2(p,dst);installed.append(p.relative_to(STAGE).as_posix())
receipt={'installed':installed,'count':len(installed),'native_visual_verified':False,'full_build_required':True}
(WORK/'installation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('ALARM_SURFACES_INSTALLED',len(installed),'files; full guarded build required')
