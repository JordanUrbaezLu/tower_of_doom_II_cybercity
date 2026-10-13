"""Render saved master or baked game derivative; never launch BO3."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
view=args[0] if args else 'hero';baked='native' in args
bpy.ops.wm.open_mainfile(filepath=str(ART/('teleporter_native.blend' if baked else 'teleporter_cyber.blend')))
scene=bpy.context.scene
if baked:
    # Round-trip the shipped source binary, including native winding, UVs,
    # cleaned triangles and per-corner normals; do not render the pre-export kit.
    sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
    from PyCoD import xmodel
    model=xmodel.Model();model.LoadFile_Bin(str(ROOT/'model_export/tod_teleporter/tod_teleporter_lod0.xmodel_bin'),split_meshes=True)
    sys.path.insert(0,str(ROOT/'tools'))
    from art_cohesion.native_preview import fullspec
    material=fullspec(ROOT/'source_data/tod_teleporter.gdt','mtl_tod_teleporter',ROOT/'model_export/tod_teleporter/_images')
    for ob in list(scene.objects):
        if ob.type=='MESH':bpy.data.objects.remove(ob,do_unlink=True)
    for source in model.meshes:
        me=bpy.data.meshes.new(source.name);me.from_pydata([v.offset for v in source.verts],[],[[f.indices[i].vertex for i in (0,2,1)] for f in source.faces]);me.update();me.materials.append(material)
        uv=me.uv_layers.new();normals=[]
        for p,f in zip(me.polygons,source.faces):
            p.use_smooth=True
            for li,i in zip(p.loop_indices,(0,2,1)):
                c=f.indices[i];uv.data[li].uv=(c.uv[0],1-c.uv[1]);normals.append(c.normal)
        me.normals_split_custom_set(normals);ob=bpy.data.objects.new('Native binary | '+source.name,me);scene.collection.objects.link(ob)
if view=='low':loc,scale=(100,-220,77),185
elif view=='top':loc,scale=(0,-.1,250),175
else:loc,scale=(152,-198,143),196
cam=scene.camera;cam.location=loc;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
scene.render.filepath=str(ART/(('native_' if baked else '')+view+'.png'))
bpy.ops.render.render(write_still=True)
print('TELEPORTER_RENDER_OK',scene.render.filepath,flush=True)
