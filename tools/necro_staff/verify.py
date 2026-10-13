"""Validate exported model/animation/texture dependencies and tier bindings."""
import pathlib,sys,json,hashlib,re,math,argparse,csv
from PIL import Image, ImageStat
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel
from PyCoD import xanim
p=argparse.ArgumentParser();p.add_argument('--ledger');args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def blocks(path):
    return {m[1]:(m[2],dict(re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"',m[3]))) for m in re.finditer(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{([^}]+)\}',path.read_text(encoding='latin1'))}
art=blocks(ROOT/'source_data/tod_necro_staff_art.gdt')
meta=json.loads((ROOT/'art/necro_staff/models.json').read_text())
loaded_models={}
for r in meta['models']:
    path=ROOT/r['file'];assert sha(path)==r['sha256'],path
    m=xmodel.Model();m.LoadFile_Bin(str(path),split_meshes=True)
    loaded_models[(r['asset'],r['lod'])]=m
    assert len(m.bones)==5 and m.bones[0].name=='tag_weapon'
    assert {b.name for b in m.bones}=={'tag_weapon','tag_flash','tag_fx_mouth','tag_fx_left','tag_fx_right'}
    assert sum(len(s.faces) for s in m.meshes)==r['triangles']
    for s in m.meshes:
        assert len(s.verts)<65535
        for v in s.verts:
            assert v.weights==[(0,1.0)] and all(math.isfinite(x) for x in v.offset)
        for face in s.faces:
            for ix in face.indices:
                assert all(math.isfinite(v) for v in ix.uv)
                assert all(math.isfinite(v) for v in ix.normal) and .99<sum(v*v for v in ix.normal)<1.01,('Invalid native vertex normal',path,ix.normal)
    for material in m.materials:assert material.name in art,material.name
# A first-person framing edit must never deform the staff relative to world.
# Compare every exported vertex, not just a code constant or the FX tags.
for tier in [2,3]:
    for lod in range(3):
        world=loaded_models[(f'tod_necro_staff{tier}_world',lod)]
        view=loaded_models[(f'tod_necro_staff{tier}_view',lod)]
        assert len(world.meshes)==len(view.meshes)
        for wm,vm in zip(world.meshes,view.meshes):
            assert len(wm.verts)==len(vm.verts)
            for w,v in zip(wm.verts,vm.verts):
                expected=(w.offset[2],-w.offset[0],-w.offset[1])
                assert max(abs(a-b) for a,b in zip(expected,v.offset))<.0001,'Bent first-person staff'
for name,(kind,f) in art.items():
    if kind=='image.gdf':
        assert (ROOT/f['baseImage'].replace('\\','/')).is_file(),name
        assert f.get('streamable')=='0',('First-person staff textures must be resident',name)
        if f['semantic']=='diffuseMap':
            assert f.get('compressionMethod')=='compressed high color' and f.get('coreSemantic')=='sRGB3chAlpha',('native diffuse format',name)
    if kind=='material.gdf':
        for k in ['colorMap','normalMap','cosinePowerMap','specColorMap','colorMap00']:assert f[k] in art,(name,k)
        assert f['waterRoughness']=='0'
        assert f.get('surfaceType') in {'metal','flesh'},('native surface type required',name)
        assert f.get('template')=='material.template'
# Native normal/color inputs must contain authored surface information.
for name in ['i_tod_necro_iron_c','i_tod_necro_iron_n','i_tod_necro_forge_n','i_tod_necro_bone_c','i_tod_necro_bone_n']:
    im=Image.open(ROOT/'model_export/tod_necro_staff'/(name+'.png')).convert('RGB')
    assert im.size==(2048,2048),('hero texture resolution',name,im.size)
    assert max(ImageStat.Stat(im).stddev)>2,('flat material map',name)
anims=json.loads((ROOT/'art/necro_staff/animations.json').read_text())
assert sha(ROOT/'model_export/tod_necro_staff/cast_skeleton.XMODEL_BIN')==anims['rig_sha256']
clips={}
for r in anims['clips']:
    path=ROOT/r['file'];assert sha(path)==r['sha256'],path
    a=xanim.Anim();a.LoadFile_Bin(str(path));clips[r['name']]=a
    assert len(a.frames)==r['frames'] and a.framerate==r['fps']
    if len(a.parts)>20:
        assert set(anims['tags']).issubset({p.name for p in a.parts})
    elif not r['name'].endswith(('ads_up','ads_down','walk_f','jump','jump_land','fall')):raise AssertionError(('unexpected partial clip',r['name']))
for path,h in anims['sources'].items():
    src=pathlib.Path(path);src=src if src.is_absolute() else ROOT/src
    assert sha(src)==h,('animation donor changed',path)
# Exact native handling tracks are the contract, not just arm segment lengths.
# The rejected pose preserved lengths while moving every hand far off-screen.
# The donors are the approved ice-staff clips, read straight from their export
# (their GDT retired with that class on 2026-10-04; the 30 files stay in place).
checked=0
for name,clip in clips.items():
    original=name.replace('tod_vm_necro_staff','tod_vm_staff_ice',1)
    donor_file=ROOT/'xanim_export'/'tod_staff_approved'/(original+'.XANIM_BIN')
    if not donor_file.is_file():continue
    donor=xanim.Anim();donor.LoadFile_Bin(str(donor_file))
    assert len(donor.frames)==len(clip.frames) and donor.framerate==clip.framerate,('changed approved timing',name)
    indices={part.name:i for i,part in enumerate(clip.parts)}
    for df,cf in zip(donor.frames,clip.frames):
        for i,part in enumerate(donor.parts):
            if part.name in anims['tags']:continue
            got=cf.parts[indices[part.name]];expected=df.parts[i]
            assert max(abs(a-b) for a,b in zip(got.offset,expected.offset))<.0001,('changed approved pose',name,part.name)
            assert max(abs(a-b) for ar,br in zip(got.matrix,expected.matrix) for a,b in zip(ar,br))<.0001,('changed approved orientation',name,part.name)
            checked+=1
assert checked>1000
distance=lambda a,b:math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
idle=clips[anims['slots']['idleAnim']];ii={p.name:i for i,p in enumerate(idle.parts)}
cast=clips['tod_vm_necro_staff_pulse'];ci={p.name:i for i,p in enumerate(cast.parts)}
travel=[distance(f.parts[ci['tag_weapon']].offset,cast.frames[0].parts[ci['tag_weapon']].offset) for f in cast.frames]
assert max(travel)>5 and travel.index(max(travel))<=5,'Pulse thrust must peak with the outward wave'
for mode in ['channel_in','channel_loop','channel_out','pulse']:
    a=clips['tod_vm_necro_staff_'+mode];idx={p.name:i for i,p in enumerate(a.parts)}
    for frame in a.frames:
        for first,last in [('j_shoulder_le','j_elbow_le'),('j_elbow_le','j_wrist_le'),('j_wrist_le','tag_weapon'),('j_wrist_ri','tag_weapon')]:
            base=distance(idle.frames[0].parts[ii[first]].offset,idle.frames[0].parts[ii[last]].offset)
            actual=distance(frame.parts[idx[first]].offset,frame.parts[idx[last]].offset)
            assert abs(actual-base)<.004,(mode,first,last,actual,base)
    if mode in ['channel_loop','pulse']:
        assert max(distance(a.frames[0].parts[i].offset,a.frames[-1].parts[i].offset) for i in range(len(a.parts)))<.004,('loop seam',mode)
# The staff presentation the Necromancer inherited: the approved ice staff's own
# values (its weapon block now lives in archive/mage_retired/source_data/tod_staff.gdt).
handling={'swayPitchScale':'0.1','swayMaxAngle':'8','adsIdleAmount':'1','adsSwayMaxAngle':'0.5','swimCombatAdsFire':''}
weapons=blocks(ROOT/'source_data/tod_weapon_twins.gdt');src=blocks(ROOT/'source_data/tod_necro_staff.gdt')
for tier in [2,3]:
    for suffix in ['_b','_up_b']:
        n=f'tod_necro_staff{tier}'+suffix;f=weapons[n][1]
        assert f['gunModel']==f'tod_necro_staff{tier}_view' and f['worldModel']==f'tod_necro_staff{tier}_world'
        assert f['clipSize']=='100' and f['maxAmmo']=='0' and f['fireType']=='Charge Shot'
        for key in ['swayPitchScale','swayMaxAngle','adsIdleAmount','adsSwayMaxAngle','swimCombatAdsFire']:
            assert f[key]==handling[key],('inherited skull presentation',n,key)
        assert f['handModel']=='' and f['isHandModelOverridable']=='1'
        assert f['playerAnimType']=='armminigun' and f['worldModelTagRight']=='tag_weapon_right'
        assert not any(v.startswith('vm_zom_skull_') for v in f.values()),('skull clip on staff',n)
        for k,v in anims['slots'].items():assert f[k]==v,(n,k,v)
        for k,v in f.items():
            if k.endswith('Anim') and v:assert v in clips,(n,k,v)
    proxy=src[f'tod_necro_pulse{tier}'][1]
    assert proxy['inventoryType']=='primary' and proxy['firstRaiseAnim']=='tod_vm_necro_staff_pulse'
    assert proxy['damage']=='0' and proxy['meleeDamage']=='0'
if args.ledger:
    with pathlib.Path(args.ledger).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    names={r['name'].split('|')[0] for r in rows}
    need={r['asset'] for r in meta['models']}|{r['name'] for r in anims['clips']}
    need|={f'tod_necro_staff{t}{s}' for t in [2,3] for s in ['_b','_up_b']}|{'tod_necro_pulse2','tod_necro_pulse3'}
    for n,(kind,_) in art.items():
        if kind=='image.gdf':need.add(n)
        if kind=='material.gdf':need.add('mc/'+n)
    assert not need-names,('missing compiled assets',sorted(need-names))
print('NECRO STAFF PASS: 12 model LODs, resolved maps, native FX tags, complete/partial clip semantics, grip lengths, loop seams, tier/PaP bindings'+('; compiled assets verified' if args.ledger else '; native visual review pending'))
