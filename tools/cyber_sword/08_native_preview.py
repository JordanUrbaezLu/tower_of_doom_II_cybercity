"""Blender preview of binary-roundtripped geometry and actual game atlases."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword'
sys.path.insert(0,str(ROOT/'tools'))
from art_cohesion.native_preview import fullspec
bpy.ops.wm.open_mainfile(filepath=str(ART/'cyber_sword.blend'))
scene=bpy.context.scene
for ob in scene.objects:
    if ob.get('cyber_sword_part'):ob.hide_render=True;ob.hide_set(True)
guide=Matrix(json.loads((ART/'authoring.json').read_text())['guide_matrix'])
data=json.loads((ART/'engine_kit/binary_roundtrip.json').read_text())
verts=[]
for v in data['verts']:
    p=Vector(v);p.z-=1.1;verts.append(guide@(p*.0254))
# Native corners have independent normals/UVs. Keeping source position indices
# welded gives Blender a different normal fan along the very thin blade edge.
corners=[c for f in data['faces'] for c in (f[0],f[2],f[1])]
me=bpy.data.meshes.new('Native binary roundtrip');me.from_pydata([verts[c['v']] for c in corners],[],
    [tuple(range(i,i+3)) for i in range(0,len(corners),3)]);me.update()
uv=me.uv_layers.new();normals=[]
for poly,face in zip(me.polygons,data['faces']):
    poly.use_smooth=True
    for li,i in zip(poly.loop_indices,(0,2,1)):
        c=face[i];uv.data[li].uv=(c['uv'][0],1-c['uv'][1]);normals.append((guide.to_3x3()@Vector(c['n'])).normalized())
me.set_sharp_from_angle(angle=math.radians(45))
me.normals_split_custom_set(normals)
flat_faces=0
for face in me.polygons:
    if all(normals[li].dot(face.normal)>.9999 for li in face.loop_indices):
        face.use_smooth=False;flat_faces+=1
print('BINARY_PREVIEW_FLAT_FACES',flat_faces,flush=True)
normal_error=max((a.vector-b).length for a,b in zip(me.corner_normals,normals))
print('BINARY_PREVIEW_NORMAL_ERROR',normal_error,flush=True)
assert normal_error<.02,'preview failed to preserve exported corner normals'
mat=fullspec(ROOT/'source_data/tod_cyber_sword.gdt','mtl_tod_cyber_sword',ROOT/'model_export/tod_warrior/cyber_sword/_images');me.materials.append(mat)
ob=bpy.data.objects.new('Cyber Sword | actual exported mesh and maps',me);scene.collection.objects.link(ob)
em=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
scene['preview_limit']='Actual exported mesh/atlas; approximate fullspec material, not BO3 lighting'
scene.cycles.samples=32
for name,strength in [('native_charging',0),('native_ready',12)]:
    em.inputs[1].default_value=strength
    scene.render.filepath=str(ART/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('CYBER_SWORD_BINARY_RENDERED',name,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'native_preview.blend'))
# Close and oblique checks retain the same exported maps and surface response.
import math
scene.render.resolution_x=1100;scene.render.resolution_y=850
scene.camera.location=(.20,-1.3,1.0)
scene.camera.rotation_euler=(Vector((0,0,1.0))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.rotation_euler.rotate_axis('Z',math.pi)
scene.camera.data.ortho_scale=.50
scene.render.filepath=str(ART/'native_hilt.png');bpy.ops.render.render(write_still=True)
scene.camera.location=(1.3,-2.0,.53)
scene.camera.rotation_euler=(Vector((0,0,.53))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.rotation_euler.rotate_axis('Z',math.pi)
scene.camera.data.ortho_scale=1.9
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.30,1)
scene.render.filepath=str(ART/'native_oblique.png');bpy.ops.render.render(write_still=True)
