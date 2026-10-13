"""Run through Blender MCP. Retarget glove-only motion onto visible viewhands.

Keep the gauntlet and dragon bones in their own native idle pose. Move the left
arm, sleeve and fist with the real boxing hook; preserve the held fist shape.
The editable preview and native clip are written only inside this repository.
"""
import bpy, sys, pathlib, copy, json, hashlib, math, shutil, re
from mathutils import Matrix, Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset, native_path, xmodel
from PyCoD import xanim
OUT = ROOT/'art/warrior_hook'; OUT.mkdir(parents=True, exist_ok=True)
NAME = 'vm_tod_gauntlet_left_hook'

def load(path):
    a = xanim.Anim(); a.LoadFile_Bin(str(path)); return a

def mat(p):
    m = Matrix(p.matrix).transposed().to_4x4(); m.translation = Vector(p.offset); return m

glove_path = ROOT/'xanim_export/tod_warrior/vm_boxing_gloves_melee_swipe_l.XANIM_BIN'
idle_fields = asset('xanim', 'vm_z_aint_no_dragon_idle')
idle_path = native_path('xanim_export', idle_fields['filename'])
glove, idle = load(glove_path), load(idle_path)
gi = {p.name:i for i,p in enumerate(glove.parts)}
ii = {p.name:i for i,p in enumerate(idle.parts)}
clip = copy.deepcopy(idle); clip.frames = []; clip.notes = []; clip.framerate = 30
rig_source = native_path('model_export', idle_fields['model'])
rig = xmodel.Model(); rig.LoadFile_Bin(str(rig_source), split_meshes=True)
parents = {b.name.lower(): (rig.bones[b.parent].name.lower() if b.parent >= 0 else None) for b in rig.bones}
mapping = {}
for n in ii:
    if not re.search(r'_le(?:_\d+)?$', n): continue
    if n in ['j_shoulder_le','j_elbow_le','j_wrist_le']: mapping[n] = n.replace('j_', 'j_glove_', 1)
    else: mapping[n] = 'follow_parent'   # sleeves/twists/fingers retain their native local poses
# The donor's viewhands tracks are a static bind pose. Never copy those tracks.
assert 'j_wrist_le' in mapping and 'j_elbow_le' in mapping
# ONE PUNCH, ONE SMOOTH RETURN (2026-09-27, user: "after the left hand punch, when it tries
# to go back into the pose, there's a little bit of jiggle"). The boxing donor is a double
# pump (its wrist peaks at glove frame 12 and again at 20) with a small settle wobble, and
# the first pass squeezed all 38 frames into 19: on the way back the arm pushed out again
# (shoulder 44.8 -> 38.5 -> 41.0 deg) before it came home. Now the attack is the donor's
# first punch only (glove 0..PEAK_SRC over clip 0..PEAK_CLIP), then the relative motion at
# that apex eases to the idle pose on a smoothstep that reaches it at SETTLE_CLIP and holds
# it: no second pump, and zero velocity where the engine hands back to the idle.
# verify_hook.py gates it (the arm never moves back out on the way home).
PEAK_SRC, PEAK_CLIP, SETTLE_CLIP = 12, 6, 16
def glove_rel(src, sample):
    lo, hi = math.floor(sample), math.ceil(sample)
    a, b = mat(glove.frames[lo].parts[src]), mat(glove.frames[hi].parts[src])
    return a.lerp(b, sample-lo) @ mat(glove.frames[0].parts[src]).inverted()
for frame in range(19):
    if frame <= PEAK_CLIP:
        sample, weight = frame * PEAK_SRC / PEAK_CLIP, 1.0
    else:
        t = min(1.0, (frame - PEAK_CLIP) / (SETTLE_CLIP - PEAK_CLIP))
        sample, weight = PEAK_SRC, 1.0 - t*t*(3 - 2*t)
    f = xanim.Frame(frame)
    posed = {}
    for p in idle.parts:
        base = mat(idle.frames[0].parts[ii[p.name]])
        if p.name in mapping:
            parent = parents[p.name]
            inherited = posed[parent] @ mat(idle.frames[0].parts[ii[parent]]).inverted() @ base
            if mapping[p.name] == 'follow_parent':
                base = inherited
            else:
                rel = Matrix.Identity(4).lerp(glove_rel(gi[mapping[p.name]], sample), weight)
                base = rel @ base
                if p.name != 'j_shoulder_le': base.translation = inherited.translation
        posed[p.name] = base
        f.parts.append(xanim.FramePart(tuple(base.translation), tuple(tuple(r) for r in base.to_3x3().transposed())))
    clip.frames.append(f)
dest = ROOT/'xanim_export/tod_warrior'/f'{NAME}.XANIM_BIN'
clip.WriteFile_Bin(str(dest), header_message='TOD2 visible left hook, Blender MCP retarget')
rig_dest = ROOT/'model_export/tod_warrior/gauntlet_hook_skeleton.XMODEL_BIN'
shutil.copyfile(rig_source, rig_dest)
gdt = '{\n\t"'+NAME+'" ( "xanim.gdf" )\n\t{\n'
for k,v in {'filename':f'tod_warrior\\\\{NAME}.XANIM_BIN','model':'tod_warrior\\\\gauntlet_hook_skeleton.XMODEL_BIN','type':'relative','looping':'0','useBones':'0'}.items():
    gdt += '\t\t"'+k+'" "'+v+'"\n'
gdt += '\t}\n}\n'
(ROOT/'source_data/tod_warrior_hook.gdt').write_text(gdt)

# Native skinned models, animated with the exact exported global bone poses.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 0; scene.frame_end = 18; scene.render.fps = 30
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 960; scene.render.resolution_y = 540; scene.render.resolution_percentage = 100
scene.world = bpy.data.worlds.new('Hook preview world'); scene.world.color = (.06,.06,.06)
material = bpy.data.materials.new('Neutral rig preview'); material.diffuse_color = (.3,.45,.55,1)
for name in ['c_t7_mp_warrior_viewarms1','wpn_t7_zmb_dlc3_gauntlet_dragon_view']:
    fields = asset('xmodel', name)
    model = xmodel.Model(); model.LoadFile_Bin(str(native_path('model_export', fields['filename'])), split_meshes=True)
    bone_ids = [ii.get(b.name.lower()) for b in model.bones]
    rest_inv = [mat(b).inverted() for b in model.bones]
    for mi, mesh in enumerate(model.meshes):
        # Hide the dragon hierarchy, as the shipping weapon does.
        if 'gauntlet' in name and any(model.bones[b].name.startswith('j_') for v in mesh.verts for b,w in v.weights if w):
            continue
        verts = [Vector(v.offset) for v in mesh.verts]
        faces = [tuple(v.vertex for v in face.indices) for face in mesh.faces]
        data = bpy.data.meshes.new(name+str(mi)); data.from_pydata(verts, [], faces); data.materials.append(material)
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj)
        obj.shape_key_add(name='Rest')
        for fi,frame in enumerate(clip.frames):
            transforms = [mat(frame.parts[ai]) @ inv if ai is not None else Matrix.Identity(4) for ai,inv in zip(bone_ids,rest_inv)]
            key = obj.shape_key_add(name=f'Native frame {fi:02}')
            for vi,v in enumerate(mesh.verts):
                pos = Vector((0,0,0))
                for bi,w in v.weights: pos += (transforms[bi] @ verts[vi])*w
                key.data[vi].co = pos if v.weights else verts[vi]
            for at,value in [(fi-1,0),(fi,1),(fi+1,0)]:
                key.value=value; key.keyframe_insert('value',frame=at)
            key.value=0
camdata=bpy.data.cameras.new('First person'); cam=bpy.data.objects.new('First person',camdata); scene.collection.objects.link(cam)
cam.location=(0,0,0); cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler(); camdata.lens=20; camdata.clip_start=.05; scene.camera=cam
for loc,power,size in [((10,-15,22),20000,30),((30,20,15),15000,25)]:
    light=bpy.data.lights.new('Softbox','AREA'); light.energy=power; light.shape='DISK'; light.size=size
    obj=bpy.data.objects.new('Softbox',light); scene.collection.objects.link(obj); obj.location=loc; obj.rotation_euler=(Vector((20,0,-5))-obj.location).to_track_quat('-Z','Y').to_euler()
scene.frame_set(6)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'left_hook.blend'))
for frame in [0,3,6,9,12,18]:
    scene.frame_set(frame); scene.render.filepath=str(OUT/f'frame_{frame:02}.png'); bpy.ops.render.render(write_still=True)
manifest={'clip':NAME,'frames':19,'fps':30,'mapped_bones':mapping,'inputs':{},'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'timing':{'peak_source_frame':PEAK_SRC,'peak_clip_frame':PEAK_CLIP,'settled_clip_frame':SETTLE_CLIP,'recovery':'smoothstep to idle, single punch'},'status':'source retarget, smooth single-punch recovery (2026-09-27); native user review pending'}
for path in [glove_path,idle_path,rig_source]: manifest['inputs'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'clip':str(dest),'frames':19,'mapped_bones':len(mapping),'blend':str(OUT/'left_hook.blend')}))
