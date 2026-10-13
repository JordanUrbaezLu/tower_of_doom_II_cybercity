"""Run through Blender MCP: authored annular mask and editable native-scale preview."""
import bpy, math, pathlib, json
import numpy as np
from mathutils import Vector
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/necromancer/pulse'
OUT.mkdir(parents=True, exist_ok=True)
TEX = ROOT / 'model_export/tod_necro/i_tod_necro_pulse.png'
N = 512
y, x = np.mgrid[0:N, 0:N].astype(float)
x = (x+.5)/N*2-1
y = (y+.5)/N*2-1
r = np.sqrt(x*x+y*y)
a = np.arctan2(y,x)
# Leading white rim and a broad wispy tail; neither fills the centre.
undulate = .005*np.sin(a*17)+.003*np.sin(a*31)
rim = np.exp(-((r-.90-undulate)/.012)**2)
filament = np.exp(-((r-.858-.013*np.sin(a*13))/.007)**2)
tail = np.exp(-((r-.84)/.055)**2)*(.48+.20*np.sin(a*23+r*110)+.12*np.sin(a*41-r*70))
v = np.clip(rim*.92+filament*.30+tail*.5, 0, 1)
v[(r<.66)|(r>.96)] = 0
pixels = np.zeros((N,N,4), dtype=np.float32)
pixels[:,:,:3] = np.array([.94,.97,1])
pixels[:,:,3] = v
img = bpy.data.images.new('i_tod_necro_pulse', width=N, height=N, alpha=True)
img.pixels.foreach_set(pixels.ravel())
img.filepath_raw = str(TEX)
img.file_format = 'PNG'
img.save()

# Saved crown source is an input; author only this separate review file.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/crown_alarm/visibility_review/before.blend'))
scene = next(s for s in bpy.data.scenes if s.name.startswith('Actual crown'))
bpy.context.window_manager.windows[0].scene = scene
image = bpy.data.images.load(str(TEX), check_existing=True)
mat = bpy.data.materials.new('Soul pulse — authored white annulus')
mat.use_nodes = True
n = mat.node_tree.nodes
n.clear()
out = n.new('ShaderNodeOutputMaterial')
mix = n.new('ShaderNodeMixShader')
transparent = n.new('ShaderNodeBsdfTransparent')
emit = n.new('ShaderNodeEmission')
emit.inputs['Color'].default_value=(.94,.97,1,1)
emit.inputs['Strength'].default_value=2
tex = n.new('ShaderNodeTexImage'); tex.image=image
links = mat.node_tree.links
links.new(tex.outputs['Alpha'],mix.inputs[0])
links.new(transparent.outputs[0],mix.inputs[1])
links.new(emit.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],out.inputs[0])
scene.render.fps=100
scene.frame_start=1; scene.frame_end=86
center=Vector((100,-598,16))
for name,delay,ratio in [('Leading rim',0,1),('Trailing soul echo',4,.88)]:
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new()
    for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]): loop.uv=co
    ob=bpy.data.objects.new(name,mesh); scene.collection.objects.link(ob)
    ob.location=center+Vector((0,0,ratio))
    ob.data.materials.append(mat)
    for frame,scale in [(1,0),(1+delay,0),(15+delay,360/.90*ratio),(81+delay,360/.90*ratio*1.08)]:
        ob.scale=(scale,scale,scale); ob.keyframe_insert('scale',frame=frame)
    for fc in ob.animation_data.action.fcurves:
        for key in fc.keyframe_points:key.interpolation='LINEAR'
    # Preview emission alpha uses the same lifetime envelope as the native sprites.
    fade_mat=mat.copy(); ob.data.materials[0]=fade_mat
    strength=fade_mat.node_tree.nodes[emit.name].inputs['Strength']
    for frame,value in [(1+delay,0),(4+delay,2*ratio),(15+delay,2*ratio),(41+delay,1.3*ratio),(81+delay,0)]:
        strength.default_value=value; strength.keyframe_insert('default_value',frame=frame)
scene.camera.location=center+Vector((0,0,64))
scene.camera.rotation_euler=(Vector((0,400,-50))).to_track_quat('-Z','Y').to_euler()
scene.camera.data.lens=20
scene.render.resolution_x=800;scene.render.resolution_y=450;scene.render.resolution_percentage=100
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene['review_limits']='Actual crown geometry, player-height mask/timing study; not BO3 exposure, sprites, alpha or pose validation. No compositor bloom.'
scene.frame_set(15)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'pulse.blend'))
for frame in [5,10,15,40]:
    scene.frame_set(frame);scene.render.filepath=str(OUT/f'phase_{frame:02}.png')
    bpy.ops.render.render(write_still=True)
print('PULSE_AUTHORED', TEX, '512 RGBA; hollow core; native peak UV radius .90')
