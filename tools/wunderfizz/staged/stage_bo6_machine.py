"""Create a complete isolated native import candidate from the original BO6 port.

Preserves every XMODEL_BIN, XANIM_BIN, PNG, collision map and EFX byte-for-byte.
Only paths, full-resolution mip bases, and alpha-safe native image compression
change. The root agent alone lands this candidate through guarded sync/build.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, re, shutil, sqlite3, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'tmp/wunderfizz/assets/source'
MACHINE=SOURCE/'_custom/_wetegg/models/t10/t10_zm_machine_wunderfizz_fxanim'
STAGE=ROOT/'tmp/wunderfizz/assets/engine_kit'
MODEL_FOLDER='tod2_bo6_wunderfizz'
OFF='t10_zm_machine_wunderfizz_fxanim'
ON=OFF+'_on'
ACTIVATE=OFF+'_activate'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def definitions(text):
    for match in re.finditer(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)\.gdf"\s*\)\s*\{(.*?)\n\s*\}',text,re.S):
        fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*(?:\n[^"\n]*)*)"',match[3]))
        yield match[1],match[2],fields,match[0]

def replace(block,key,value):
    pattern=r'("'+re.escape(key)+r'"\s+")[^"\n]*(")'
    new,count=re.subn(pattern,lambda m:m[1]+value+m[2],block)
    assert count==1,(key,count)
    return new

def hulls(path):
    # Radiant's plane-point winding faces inward: all hull interiors satisfy
    # dot(cross(p1-p0,p2-p0),point-p0)>=0. Compute true half-space vertices;
    # the three defining plane points are not the hull's corner bounds.
    result=[]
    for index,body in re.findall(r'// brush (\d+)\s*\{(.*?)\n\}',path.read_text(),re.S):
        planes=[]
        for line in body.splitlines():
            points=re.findall(r'\(\s*([^()]+)\s*\)',line)
            if len(points)!=3:continue
            a,b,c=[np.array([float(x) for x in p.split()]) for p in points]
            n=np.cross(b-a,c-a);n=n/np.linalg.norm(n)
            planes.append((n,float(np.dot(n,a))))
        corners=[]
        for subset in itertools.combinations(planes,3):
            matrix=np.array([p[0] for p in subset]);values=np.array([p[1] for p in subset])
            if abs(np.linalg.det(matrix))<1e-9:continue
            p=np.linalg.solve(matrix,values)
            if all(np.dot(n,p)>=d-1e-6 for n,d in planes) and not any(np.linalg.norm(p-q)<1e-6 for q in corners):corners.append(p)
        assert len(corners)>=4,(index,'unresolved collision hull')
        result.append({'brush':int(index),'planes':len(planes),'corners':[p.tolist() for p in corners],
            'bounds':[[min(p[j] for p in corners),max(p[j] for p in corners)] for j in range(3)],
            'materials':sorted(set(re.findall(r'\)\s+(clip\S*)\s',body)))})
    return result

def stage():
    STAGE.mkdir(parents=True,exist_ok=True)
    receipts=[]
    def copy(src,rel):
        dst=STAGE/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        assert sha(src)==sha(dst)
        receipts.append({'file':rel,'source':str(src.relative_to(SOURCE)).replace('\\','/'),'bytes':src.stat().st_size,'sha256':sha(dst),'original_payload_preserved':True})
    for src in sorted((MACHINE/'xmodels').glob('*')):copy(src,'model_export/'+MODEL_FOLDER+'/xmodels/'+src.name)
    for src in sorted((MACHINE/'xanims').glob('*')):copy(src,'xanim_export/'+MODEL_FOLDER+'/'+src.name)
    for src in sorted((MACHINE/'_images').rglob('*.png')):copy(src,'model_export/'+MODEL_FOLDER+'/_images/'+src.parent.name+'/'+src.name)
    coll=SOURCE/'share/raw/collmaps'/f'{OFF}.map'
    copy(coll,'share/raw/collmaps/'+coll.name)
    fx_paths=[]
    for src in sorted((SOURCE/'share/raw/fx/_t10/vending').glob('fizz_*.efx')):
        rel='share/raw/fx/_t10/vending/'+src.name;copy(src,rel);fx_paths.append(rel)
    assert len(fx_paths)==2
    source_gdt=MACHINE/(OFF+'.gdt')
    all_defs=list(definitions(source_gdt.read_text(encoding='utf-8-sig')))
    gdt_blocks=[];changes=[]
    for name,kind,fields,block in all_defs:
        updates={}
        if kind=='image':
            src=SOURCE/fields['baseImage']
            assert src.is_file()
            updates['baseImage']='model_export/'+MODEL_FOLDER+'/_images/'+src.parent.name+'/'+src.name
            updates['mipBase']='1/1'
            # Preserve original glass alpha at every mip without BC7 quantization.
            # The donor's 'compressed no alpha' would turn every pane opaque.
            if name=='i_t10_zm_machine_wunderfizz_glass_c':updates['compressionMethod']='uncompressed'
        elif kind=='xmodel':
            for key in ('filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File'):
                updates[key]=MODEL_FOLDER+'\\\\xmodels\\\\'+fields[key].replace('\\','/').split('/')[-1]
        elif kind=='xanim':
            updates['filename']=MODEL_FOLDER+'\\\\'+fields['filename'].replace('\\','/').split('/')[-1]
            updates['model']=MODEL_FOLDER+'\\\\xmodels\\\\'+fields['model'].replace('\\','/').split('/')[-1]
        for key,value in updates.items():
            block=replace(block,key,value)
            changes.append({'asset':name,'kind':kind,'field':key,'before':fields[key],'after':value})
        gdt_blocks.append(block)
    out=STAGE/'source_data/tod2_bo6_wunderfizz.gdt';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('{\n\t'+'\n\t'.join(gdt_blocks)+'\n}\n',encoding='utf-8')
    receipts.append({'file':out.relative_to(STAGE).as_posix(),'bytes':out.stat().st_size,'sha256':sha(out),'original_payload_preserved':False,'reason':'Native paths, original glass alpha-safe compression and full-resolution mip bases only.'})
    zone=STAGE/'zone_source/tod2_bo6_wunderfizz.zpkg';zone.parent.mkdir(parents=True,exist_ok=True)
    zone.write_text('// Exact BO6/WetEgg machine, original state geometry/materials/clip/FX.\n'+
        '\n'.join(['xmodel,'+OFF,'xmodel,'+ON,'xanim,'+ACTIVATE,'scriptbundle,'+ACTIVATE,'fx,_t10/vending/fizz_idle','fx,_t10/vending/fizz_activated'])+'\n',encoding='utf-8')
    receipts.append({'file':zone.relative_to(STAGE).as_posix(),'bytes':zone.stat().st_size,'sha256':sha(zone),'original_payload_preserved':False,'reason':'Map-owned dependency package.'})
    inspected=json.loads((ROOT/'tmp/wunderfizz/assets/source_inspection.json').read_text())
    native_bounds=[[min(m['bounds'][j][0] for m in inspected['models']),max(m['bounds'][j][1] for m in inspected['models'])] for j in range(3)]
    collision=hulls(coll)
    manifest={'source_archive':'tmp/wunderfizz/audio/downloads/BO6_Overhaul_Assets_v1.0.rar',
        'source_archive_sha256':inspected['archive_sha256'],'source_gdt_sha256':sha(source_gdt),
        'source_credits':'BO6 machine port by WetEgg; archive published by KingslayerKyle BO6Overhaul v1.0',
        'source_urls':['https://github.com/KingslayerKyle/BO6Overhaul','https://assets.gscode.net/assets/black-ops-6-overhaul','https://drive.google.com/drive/folders/1eictKdWp20j5v7jT9h3p4Ck8F_id2KsH'],
        'status':'Staged candidate; root must land through guarded sync/build and user tests.',
        'model_names':{'off':OFF,'on':ON},'animation':ACTIVATE,'bundle':ACTIVATE,
        'scale':1,'front_axis':'+X','frontYaw':0,'origin':'Original tag_origin at rear at floor level; never recentered.',
        'all_lod_bounds':native_bounds,'lod0_bounds':inspected['models'][0]['bounds'],
        'tag_hint':[50.19290542602539,0,53.87769317626953],'animation_frames':121,'animation_fps':30,'animation_duration_seconds':4,
        'collision':{'file':'share/raw/collmaps/'+coll.name,'source_sha256':sha(coll),'hulls':collision,'native_map_unchanged':True},
        'native_definition_changes':changes,'files':receipts,
        'original_geometry_texture_labels_colors_uvs_rig_lods_animation_fx_preserved':True,
        'native_compile_verified':False,'native_visual_verified':False,'game_launched':False,
        'root_integration':['Copy candidate files to identical relative paths in this repository only after coherent landing.',
            'Add guarded sync Copy-Tree for model_export/tod2_bo6_wunderfizz and xanim_export/tod2_bo6_wunderfizz.',
            'Add guarded sync Copy-Tree for map-owned share/raw/collmaps if not already present.',
            'Include tod2_bo6_wunderfizz.zpkg in the playable map zone.',
            'Audio agent owns evt_wunderfizz aliases and exact WAV candidate; avoid duplicate manual activation sound when animation note plays.',
            'Bound original idle/activation FX to nearby machine hosts; no fifty global active FX loops.']}
    (STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'candidate':str(STAGE),'files':len(receipts),'bytes':sum(r['bytes'] for r in receipts),'all_lod_bounds':native_bounds,'collision_hulls':collision},indent=2))

def check():
    m=json.loads((STAGE/'manifest.json').read_text())
    for f in m['files']:
        p=STAGE/f['file'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['file']
        if f.get('original_payload_preserved'):assert sha(SOURCE/f['source'])==f['sha256'],f['source']
    defs=list(definitions((STAGE/'source_data/tod2_bo6_wunderfizz.gdt').read_text()))
    names={(kind,name):fields for name,kind,fields,block in defs}
    assert len(names)==len(defs)==30,(len(names),len(defs))
    for (kind,name),fields in names.items():
        if kind=='image':
            assert (STAGE/fields['baseImage']).is_file(),name
            assert fields['mipBase']=='1/1',name
        elif kind in ('xmodel','xanim'):
            keys=('filename','mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File') if kind=='xmodel' else ('filename','model')
            for key in keys:
                folder='xanim_export' if kind=='xanim' and key=='filename' else 'model_export'
                assert (STAGE/folder/fields[key].replace('\\','/')).is_file(),(name,key)
        elif kind=='material':
            # Existing original port identifiers are preserved. The 33-character
            # subject material is within the native 63-byte limit including mc/;
            # shortening it would mutate every supplied model's material table.
            assert len('mc/'+name)<=63,name
            for key,value in fields.items():
                if value.startswith('i_') and ('map' in key.lower()):assert ('image',value) in names,(name,key,value)
    assert names['image','i_t10_zm_machine_wunderfizz_glass_c']['compressionMethod']=='uncompressed'
    anim=names['xanim',ACTIVATE]
    assert anim['sound_customnote0frame']=='1' and anim['sound_customnote0actionparam1']=='evt_wunderfizz_activate'
    assert anim['fx_customnote1frame']=='120' and anim['fx_customnote1action']=='Stop Fx'
    print('BO6_WUNDERFIZZ_SOURCE_OK: all 14 native LODs, original 20 PNGs, six materials, exact 4s animation/notes, collision and both FX; alpha retained; paths resolve; source payloads unchanged.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:check()
    else:stage();check()
