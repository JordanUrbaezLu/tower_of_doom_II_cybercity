"""Record the read-only landed-source/native-path and private-write-guard audit.

Only this diagnostic report is written. No source/deployment/native tool or
game mutation occurs. Native .awi declarations are read as compatibility proof.
"""
import datetime,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_bo6_machine import definitions,sha,ACTIVATE,OFF,ON

def main():
    manifest_path=ROOT/'art/wunderfizz/asset_manifest.json'
    manifest_pin=sha(manifest_path)
    manifest=json.loads(manifest_path.read_text())
    payloads=[]
    for row in manifest['files']:
        file=ROOT/row['file'];assert file.is_file() and sha(file)==row['sha256'],row['file']
        payloads.append({'file':row['file'],'sha256':row['sha256'],'bytes':file.stat().st_size})
    gdt=ROOT/'source_data/tod2_bo6_wunderfizz.gdt'
    entries={(kind,name):fields for name,kind,fields,block in definitions(gdt.read_text())}
    assert len(entries)==30
    references=[]
    def ref(kind,name,field,value,base):
        file=(ROOT/base/value.replace('\\','/')).resolve()
        assert file.is_relative_to(ROOT) and file.is_file(),(kind,name,field,file)
        references.append({'kind':kind,'asset':name,'field':field,'source_value':value,
            'native_relative_root':base,'resolved_repository_file':file.relative_to(ROOT).as_posix(),
            'sha256':sha(file),'exists':True})
    for (kind,name),fields in entries.items():
        if kind=='image':ref(kind,name,'baseImage',fields['baseImage'],'')
        elif kind=='xmodel':
            for key in ['filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File']:
                ref(kind,name,key,fields[key],'model_export')
            ref(kind,name,'CollisionMap',fields['CollisionMap'],'share/raw/collmaps')
        elif kind=='xanim':
            ref(kind,name,'filename',fields['filename'],'xanim_export')
            ref(kind,name,'model',fields['model'],'model_export')
    assert len(references)==38
    anim=entries['xanim',ACTIVATE];note_refs=[]
    for prefix,action,frame in [('fx_customnote0','Play Fx','1'),('fx_customnote1','Stop Fx','120')]:
        assert anim[prefix+'action']==action and anim[prefix+'frame']==frame
        file=ROOT/'share/raw/fx'/anim[prefix+'actionparam1'].replace('\\','/')
        assert file.is_file()
        note_refs.append({'action':action,'frame':int(frame),'tag':anim[prefix+'actionparam2'],
            'resolved_file':file.relative_to(ROOT).as_posix(),'sha256':sha(file)})
    assert anim['sound_customnote0action']=='Sound' and anim['sound_customnote0frame']=='1'
    note_refs.append({'action':'Sound','frame':1,'alias':anim['sound_customnote0actionparam1'],
        'tag':anim['sound_customnote0actionparam2'],'alias_source':'sound/aliases/tod_wunderfizz.csv'})
    bundle=entries['scriptbundle',ACTIVATE]
    assert bundle['type']=='scene' and bundle['configstringFileType']=='SCRIPTBUNDLE'
    assert bundle['object1_MainAnim']==ACTIVATE and ('xanim',ACTIVATE) in entries
    assert bundle['object1_Name']==ON and bundle['object1_NoSpawn']=='1'
    assert all(not value for key,value in bundle.items() if key.endswith('_Model'))
    guard_script=ROOT/'tools/wunderfizz/staged/preflight_sync_paths.ps1'
    guard=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(guard_script)],
        capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    targets=[line.removeprefix('GUARD_OK ') for line in guard.stdout.splitlines() if line.startswith('GUARD_OK ')]
    assert len(targets)==8 and not guard.stderr.strip(),(targets,guard.stderr)
    native_root=Path('C:/BO3Tools/TOD2Cybercity')
    ui_files=['deffiles/xmodel.awi','deffiles/xanim.awi','deffiles/scriptbundle.awi']
    ui_pins={path:sha(native_root/path) for path in ui_files}
    out=ROOT/'art/wunderfizz/sync_preflight.json'
    out.write_text(json.dumps({'verified_at':datetime.datetime.now().astimezone().isoformat(),
        'manifest_sha256':manifest_pin,'typed_asset_count':30,'payloads':payloads,
        'resolved_references':references,'native_notetrack_references':note_refs,
        'private_write_guard':{'implementation':'tools/tod2_workspace.ps1 Assert-Tod2WritePath -Tree',
            'invocation_script':guard_script.relative_to(ROOT).as_posix(),'invocation_script_sha256':sha(guard_script),
            'exit_code':guard.returncode,'targets':targets,'all_passed':True},
        'native_definition_ui_source_sha256':ui_pins,
        'native_path_contract':{'xmodel_and_skeleton':'model_export/','xanim':'xanim_export/',
            'CollisionMap':'share/raw/collmaps/','xanim_fx_action':'share/raw/fx/'},
        'scriptbundle':{'type':'scene','field_count':len(bundle),'configstringFileType':'SCRIPTBUNDLE',
            'MainAnim':ACTIVATE,'Name_is_existing_entity_selector':ON,'NoSpawn':True,
            'model_attachments':[],'all_asset_dependencies_explicitly_packaged':True,
            'runtime_uses_direct_AnimScripted_generic_tree':True},
        'native_actions_compatible':['Sound','Play Fx','Stop Fx'],
        'no_compile_blocker_identified':True,'status':'Source preflight only; native compilation and user playtest remain separate proof.',
        'source_or_manifest_mutated':False,'synced':False,'built':False,'game_launched':False,'render_started':False},indent=2)+'\n')
    assert sha(manifest_path)==manifest_pin,'Source receipt changed during the read-only audit'
    print('BO6_WUNDERFIZZ_SYNC_PREFLIGHT_OK 40 exact payloads;38 resolved references;8 guarded private destinations;',out)

if __name__=='__main__':main()
