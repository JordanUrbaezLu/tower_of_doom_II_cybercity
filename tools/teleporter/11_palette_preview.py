"""MCP: preview all three states from the actual exported mesh and materials."""
import bpy, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';OUT=ART/'status_colors'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
sys.path.insert(0,str(ROOT/'tools'))
from PyCoD import xmodel
from art_cohesion.native_preview import fullspec,fields
bpy.ops.wm.open_mainfile(filepath=str(ART/'surface_repair/binary_after.blend'))
s=bpy.context.scene
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath and 'tod_teleporter' in im.filepath:im.reload()
s['teleporter_state']=1;s['teleporter_preview_auto']=1
s['teleporter_state_contract']='OFF = no emission; READY = green; PENDING = animated yellow. Native atlas/mesh; approximate fullspec preview.'
s.id_properties_ui('teleporter_state').update(min=0,max=2,description='0 off, 1 green ready, 2 yellow pending')
s.frame_start=1;s.frame_end=360;s.render.fps=30
mode='(state if auto < 0.5 else (0 if frame <= 60 else (1 if frame <= 150 or frame > 330 else 2)))'
def drive(owner,prop,expression,index=None):
    fc=owner.driver_add(prop) if index is None else owner.driver_add(prop,index)
    d=fc.driver;d.type='SCRIPTED';d.expression=expression
    for name,propname in [('state','teleporter_state'),('auto','teleporter_preview_auto')]:
        v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=s;v.targets[0].data_path='["'+propname+'"]'
mat=fullspec(ROOT/'source_data/tod_teleporter.gdt','mtl_tod_teleporter',ROOT/'model_export/tod_teleporter/_images')
em=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
drive(em.inputs['Strength'],'default_value','6*('+mode+' == 1)')
for ob in s.objects:
    if ob.type=='MESH' and ob.name.startswith('Binary surface'):
        ob.data.materials.clear();ob.data.materials.append(mat);ob['tp_preview_body']=True
root=bpy.data.objects.new('Pending yellow | rotation',None);s.collection.objects.link(root)
drive(root,'rotation_euler','(frame-151)*2*pi/90',2)
model=xmodel.Model();model.LoadFile_Bin(str(ROOT/'model_export/tod_teleporter/tod_tp_recharge_lod0.xmodel_bin'),split_meshes=True)
def decode(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
for band,source in enumerate(model.meshes):
    f=fields(ROOT/'source_data/tod_teleporter_states.gdt',model.materials[band].name)
    m=bpy.data.materials.new('Native yellow band '+str(band));m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(0,0,0,1)
    p.inputs['Emission Color'].default_value=(*[decode(float(v)) for v in f['colorTint1'].split()[:3]],1)
    p.inputs['Emission Strength'].default_value=float(f['scaleRGB'])
    me=bpy.data.meshes.new('Exported yellow arc '+str(band))
    me.from_pydata([v.offset for v in source.verts],[],[[f.indices[i].vertex for i in (0,2,1)] for f in source.faces]);me.update();me.materials.append(m)
    normals=[]
    for face,src in zip(me.polygons,source.faces):
        face.use_smooth=True
        normals.extend(src.indices[i].normal for i in (0,2,1))
    me.normals_split_custom_set(normals)
    ob=bpy.data.objects.new('Pending | band '+str(band),me);s.collection.objects.link(ob);ob.parent=root;ob['tp_preview_chase']=True
    drive(ob,'hide_render',mode+' != 2');drive(ob,'hide_viewport',mode+' != 2')
s.frame_set(100);s.render.engine='BLENDER_EEVEE';s.render.resolution_x=960;s.render.resolution_y=704;s.render.resolution_percentage=100
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.region_3d.view_camera_zoom=-10
            area.spaces.active.shading.type='RENDERED';area.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native_states.blend'))
print('TELEPORTER_NATIVE_PALETTE_PREVIEW_READY actual exported body, atlas and yellow mesh')
