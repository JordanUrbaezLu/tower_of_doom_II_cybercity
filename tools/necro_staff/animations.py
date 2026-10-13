"""MCP: fit every native ice-staff clip, then author continuous soul channeling.

The skull's weapon-space casting motion is layered onto the staff pose. Both
hands and the staff receive the same small transform, preserving the approved
grip and bone lengths. Skull arm poses are never substituted for staff arms.
"""
import bpy, pathlib,sys,json,re,copy,hashlib,math
from mathutils import Matrix,Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel,asset,native_path
from PyCoD import xanim
OUT=ROOT/'xanim_export/tod_necro_staff';ART=ROOT/'art/necro_staff'
def blocks(p):
    return {m[1]:dict(re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"',m[2])) for m in re.finditer(r'"([^"\n]+)"\s*\([^)]*\)\s*\{([^}]+)\}',p.read_text(encoding='latin1'))}
def matrix(p):
    m=Matrix(p.matrix).transposed().to_4x4();m.translation=p.offset;return m
def framepart(m):return xanim.FramePart(tuple(m.translation),tuple(tuple(r) for r in m.to_3x3().transposed()))
def load(path):
    a=xanim.Anim();a.LoadFile_Bin(str(path));return a
# The approved ice staff's weapon block + clip GDT were archived with their class (2026-10-04);
# their clips and rig stay in xanim_export/tod_staff_approved + model_export/tod_staff_anim.
staff=blocks(ROOT/'archive/mage_retired/source_data/tod_staff.gdt')['tod_staff_ice']
donors=blocks(ROOT/'archive/mage_retired/source_data/tod_staff_approved_anims.gdt')
# GDF animation slots include slide_in / slide_loop, not just *Anim fields.
slots={k:v for k,v in staff.items() if v in donors}
rig=xmodel.Model();rig.LoadFile_Bin(str(ROOT/'model_export/tod_staff_anim/tod_vm_staff_ice_skeleton.XMODEL_BIN'))
ri={b.name:i for i,b in enumerate(rig.bones)}
meta=json.loads((ART/'models.json').read_text());view=Matrix(meta['view_transform'])
tags={n:Vector(p) for n,p in meta['view_tags'].items()}
root=ri['tag_weapon']
rootrest=matrix(rig.bones[root])
for n,pos in tags.items():
    b=xmodel.Bone(n);b.parent=root
    mat=rootrest@Matrix.Translation(pos);b.offset=tuple(mat.translation);b.matrix=tuple(tuple(r) for r in mat.to_3x3().transposed())
    if n in ri:rig.bones[ri[n]]=b
    else:ri[n]=len(rig.bones);rig.bones.append(b)
rigpath=ROOT/'model_export/tod_necro_staff/cast_skeleton.XMODEL_BIN';rig.WriteFile_Bin(str(rigpath),version=7)
records=[];gdt=[];outputs={};sources={}
def fitted(a):
    # The approved ADS/walk/jump clips are two-track additive overlays. Filling
    # their missing limbs with a bind pose would replace the actual hand pose.
    if not any(p.name=='j_wrist_le' for p in a.parts):return copy.deepcopy(a)
    out=copy.deepcopy(a);old={p.name:i for i,p in enumerate(a.parts)}
    out.parts=[xanim.PartInfo(b.name) for b in rig.bones];out.frames=[];out.notes=[]
    for frame in a.frames:
        f=xanim.Frame(frame.frame);poses={}
        for b in rig.bones:
            if b.name in tags:p=poses['tag_weapon']@Matrix.Translation(tags[b.name])
            elif b.name in old:p=matrix(frame.parts[old[b.name]])
            elif b.parent>=0:p=poses[rig.bones[b.parent].name]@matrix(rig.bones[b.parent]).inverted()@matrix(b)
            else:p=matrix(b)
            poses[b.name]=p;f.parts.append(framepart(p))
        # Preserve approved camera-space weapon and hand tracks exactly.
        # Fit the custom mesh to this grip; never reframe the player skeleton.
        out.frames.append(f)
    return out
def save(name,clip,loop=False,template=None):
    path=OUT/(name+'.XANIM_BIN');clip.WriteFile_Bin(str(path),header_message='TOD2 staff grip / skull casting blend, Blender MCP')
    fields=dict(template or {},filename='tod_necro_staff/'+path.name,model='tod_necro_staff/cast_skeleton.XMODEL_BIN',type='relative',looping='1' if loop else '0',useBones='0')
    # Native ice sounds / BO6 reload cues are not part of this Necromancer weapon.
    fields={k:v for k,v in fields.items() if not k.startswith('customnote')}
    gdt.append('\t"'+name+'" ( "xanim.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v).replace('/','\\\\')+'"\n' for k,v in fields.items())+'\t}\n')
    outputs[name]=clip;records.append(dict(name=name,frames=len(clip.frames),fps=clip.framerate,loop=loop,file=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
renames={}
for name in sorted(set(slots.values())):
    fields=donors[name];src=ROOT/'xanim_export'/fields['filename'].replace('\\','/')
    sources[str(src.relative_to(ROOT))]=hashlib.sha256(src.read_bytes()).hexdigest()
    new=name.replace('tod_vm_staff_ice','tod_vm_necro_staff',1);renames[name]=new
    save(new,fitted(load(src)),fields.get('looping')=='1',fields)
idle=outputs[renames[staff['idleAnim']]];ii={p.name:i for i,p in enumerate(idle.parts)}
skf=asset('xanim','vm_zom_skull_fire_loop');skpath=native_path('xanim_export',skf['filename']);sk=load(skpath);si={p.name:i for i,p in enumerate(sk.parts)}
sources[str(skpath)]=hashlib.sha256(skpath.read_bytes()).hexdigest()
skbase=matrix(sk.frames[0].parts[si['tag_weapon']])
camera={'tag_view','tag_ads','tag_torso','tag_cambone','tag_camera'}
def channel(mode):
    clip=copy.deepcopy(idle);clip.frames=[];clip.notes=[];clip.framerate=30
    count={'in':9,'loop':34,'out':10}[mode]
    for i in range(count):
        phase=i/(count-1)
        weight=1 if mode=='loop' else (phase if mode=='in' else 1-phase)
        weight=weight*weight*(3-2*weight)
        f=copy.deepcopy(idle.frames[0]);f.frame=i
        transform=Matrix.Translation((1.25*weight,0,1.0*weight))
        if mode=='loop':
            # Use stock skull casting cadence, scaled to a two-handed weapon.
            delta=matrix(sk.frames[round(phase*(len(sk.frames)-1))].parts[si['tag_weapon']])@skbase.inverted()
            q=delta.to_quaternion();q=Matrix.Identity(4).to_quaternion().slerp(q,.24*math.sin(math.pi*phase)**2)
            motion=q.to_matrix().to_4x4();motion.translation=delta.translation*.20*math.sin(math.pi*phase)**2
            transform=transform@motion
        for n,index in ii.items():
            if n not in camera:f.parts[index]=framepart(transform@matrix(f.parts[index]))
        clip.frames.append(f)
    return clip
for mode in ['in','loop','out']:save('tod_vm_necro_staff_channel_'+mode,channel(mode),mode=='loop')
# A short outward staff thrust accompanies Soul Pulse. The impact is at frame
# zero (existing gameplay is immediate); recovery settles into the same grip.
pulse=copy.deepcopy(idle);pulse.frames=[];pulse.notes=[];pulse.framerate=30
for i in range(19):
    phase=i/18
    # Attack peaks with the 140 ms outgoing wave, then settle over the rest of
    # the 600 ms clip. The old symmetric motion peaked after the blast passed.
    amount=math.sin(.5*math.pi*phase/.22)**2 if phase<=.22 else math.cos(.5*math.pi*(phase-.22)/.78)**2
    transform=Matrix.Translation((5.5*amount,0,1.2*amount))
    f=copy.deepcopy(idle.frames[0]);f.frame=i
    for n,index in ii.items():
        if n not in camera:f.parts[index]=framepart(transform@matrix(f.parts[index]))
    pulse.frames.append(f)
save('tod_vm_necro_staff_pulse',pulse)
bindings={k:renames[v] for k,v in slots.items()}
bindings.update(holdFireAnim='tod_vm_necro_staff_channel_in',holdFireLoopAnim='tod_vm_necro_staff_channel_loop',holdFireCancelAnim='tod_vm_necro_staff_channel_out',
                fireIntroAnim='tod_vm_necro_staff_channel_in',fireAnim='tod_vm_necro_staff_channel_out',lastShotAnim='tod_vm_necro_staff_channel_out',
                adsFireAnim='tod_vm_necro_staff_channel_out',adsLastShotAnim='tod_vm_necro_staff_channel_out',
                altRaiseAnim=renames[staff['raiseAnim']],altDropAnim=renames[staff['dropAnim']])
(ROOT/'source_data/tod_necro_staff_anims.gdt').write_text('{\n'+''.join(gdt)+'}\n')
(ART/'animations.json').write_text(json.dumps(dict(clips=records,slots=bindings,sources=sources,rig_sha256=hashlib.sha256(rigpath.read_bytes()).hexdigest(),tags=tags and {k:list(v) for k,v in tags.items()},native_visual_verified=False),indent=2))
print('NECRO_CAST_ANIMATIONS',len(records),'native clips, corrected skull FX tags and continuous channel sequence')
