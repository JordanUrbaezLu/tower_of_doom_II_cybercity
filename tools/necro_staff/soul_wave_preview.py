"""MCP review of outgoing native soul sprites at player eye height.

Composition preview only: native particle renderer/exposure remain user tested.
Existing BO3 sprite art is reused, not represented as newly authored textures.
"""
import bpy, math, pathlib, sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset,MT
OUT=ROOT/'art/necro_staff/soul_wave';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Dark review');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.025,.03,.035,1)
scene.view_settings.view_transform='Standard'
data=bpy.data.cameras.new('Player height');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
cam.location=(0,0,64);cam.rotation_euler=Vector((0,1,-.14)).to_track_quat('-Z','Y').to_euler();data.lens=20;data.clip_end=2000
def material(name,path):
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');tr=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.94,.97,1,1)
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path));tex.interpolation='Linear'
    alpha=n.new('ShaderNodeMath');alpha.name='Native phase alpha';alpha.operation='MULTIPLY';alpha.inputs[1].default_value=1
    l.new(tex.outputs['Alpha'],alpha.inputs[0]);l.new(alpha.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    return m
materials={}
for kind,name in [('wisp','gfx_smk_whisp_anim_em'),('glyph','gfx_keeper_symbols_zod_em')]:
    materials[kind]=material(name,OUT/(name+'.png'))
ringmat=material('Authored ring',ROOT/'model_export/tod_necro/i_tod_necro_pulse.png')
def quad(name,mat,w,h,loc,uvs,face=True):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-w,-h,0),(w,-h,0),(w,h,0),(-w,h,0)],[],[(0,1,2,3)])
    mesh.materials.append(mat);uv=mesh.uv_layers.new()
    for v,co in zip(uv.data,uvs):v.uv=co
    ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);ob.location=loc
    if face:ob.rotation_euler=(cam.location-ob.location).to_track_quat('Z','Y').to_euler()
for secs in [.04,.14,.32,.60]:
    for ob in list(scene.objects):
        if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
    radius=88+(600-88)*min(secs/.14,1)
    size=(600/.9)*min(secs/.14,1)
    def curve(keys,t):
        for (a,x),(b,y) in zip(keys,keys[1:]):
            if a<=t<=b:return x+(y-x)*(t-a)/(b-a)
        return keys[-1][1]
    soul_alpha=curve([(0,0),(.04,.9),(.19,.9),(.55,.6),(1,0)],secs/.75)
    soul_size=curve([(0,.65),(.19,1),(.5,1.12),(1,.8)],secs/.75)
    for m in materials.values():m.node_tree.nodes['Native phase alpha'].inputs[1].default_value=soul_alpha
    ringmat.node_tree.nodes['Native phase alpha'].inputs[1].default_value=curve([(0,0),(.04,1),(.175,1),(.5,.65),(1,0)],secs/.8)
    quad('White ground wave',ringmat,size,size,(0,0,12),[(0,0),(1,0),(1,1),(0,1)],False)
    for kind,count,cols,rows in [('wisp',24,8,4),('glyph',12,4,4)]:
        for j in range(count):
            i=j if kind=='wisp' else j*2;a=i*math.tau/24
            frame=min(cols*rows-1,int(secs/.75*cols*rows));u=(frame%cols)/cols;v=1-(frame//cols+1)/rows
            quad(kind,materials[kind],soul_size*(30 if kind=='wisp' else 14),soul_size*(46 if kind=='wisp' else 14),
                 (radius*math.cos(a),radius*math.sin(a),42+(i%3)*9),[(u,v),(u+1/cols,v),(u+1/cols,v+1/rows),(u,v+1/rows)])
    scene.render.filepath=str(OUT/('wave_%03d.png'%round(secs*1000)));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'wave.blend'))
print('OUTGOING SOUL REVIEW: native smoke/symbol atlases, ground ring, 4 player-height phases')
