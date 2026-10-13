"""Export the MCP pending art and a green derivative of the emission bake."""
import bpy,json,hashlib,sys,array,math,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';KIT=ART/'engine_kit';OUT=ROOT/'model_export/tod_teleporter'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
palette=json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from cyber_reference_one.native_geometry import clean
bpy.ops.wm.open_mainfile(filepath=str(ART/'teleporter_cyber.blend'));scene=bpy.context.scene
scene['teleporter_preview_auto']=0;scene['teleporter_state']=2;scene.update_tag();scene.frame_set(151);bpy.context.view_layer.update()
deps=bpy.context.evaluated_depsgraph_get();geo={'verts':[],'faces':[]}
for ob in scene.objects:
    if not ob.get('tp_state_art'):continue
    ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();offset=len(geo['verts']);nm=ev.matrix_world.to_3x3().inverted().transposed()
    geo['verts'] += [list(ev.matrix_world@v.co) for v in me.vertices]
    for tri in me.loop_triangles:
        face=[]
        for li,uv in zip((tri.loops[0],tri.loops[2],tri.loops[1]),((.2,.2),(.8,.2),(.2,.8))):
            n=(nm@me.corner_normals[li].vector).normalized();face.append({'v':offset+me.loops[li].vertex_index,'n':list(n),'uv':list(uv),'band':int(ob['tp_state_band'])})
        geo['faces'].append(face)
    ev.to_mesh_clear()
clean(geo,min_altitude=.001);(KIT/'recharge.json').write_text(json.dumps(geo,separators=(',',':')))
source=OUT/'_images/i_tod_teleporter_e.png';im=bpy.data.images.load(str(source),check_existing=False);pixels=array.array('f',[0])*(im.size[0]*im.size[1]*4);im.pixels.foreach_get(pixels)
def encode(x):return 12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055
mask=array.array('f',(max(pixels[i:i+3]) for i in range(0,len(pixels),4)))
for i in range(0,len(pixels),4):
    # Byte-backed image.pixels exposes normalized PNG bytes. Decode first;
    # preserve the existing peak radiance while changing only emission hue.
    peak=max(pixels[i:i+3]);peak=peak/12.92 if peak<=.04045 else ((peak+.055)/1.055)**2.4
    pixels[i:i+4]=array.array('f',[*(encode(peak*c) for c in palette['ready_linear']),1])
ready=bpy.data.images.new('i_tod_teleporter_ready_e',width=im.size[0],height=im.size[1],alpha=False);ready.colorspace_settings.name='sRGB';ready.pixels.foreach_set(pixels);ready.filepath_raw=str(OUT/'_images/i_tod_teleporter_ready_e.png');ready.file_format='PNG';ready.save()
color_source=ART/'checkpoints/i_tod_teleporter_original_c.png'
if not color_source.exists():shutil.copyfile(OUT/'_images/i_tod_teleporter_c.png',color_source)
color=bpy.data.images.load(str(color_source),check_existing=False);cp=array.array('f',[0])*(color.size[0]*color.size[1]*4);color.pixels.foreach_get(cp)
for i,peak in enumerate(mask):
    if peak<=0:continue
    blend=min(1,peak*255/8)
    for c,target in enumerate((.008,.008,.011)):
        v=cp[i*4+c];linear=v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
        cp[i*4+c]=encode(linear*(1-blend)+target*blend)
dark=bpy.data.images.new('State glass base',width=color.size[0],height=color.size[1],alpha=False);dark.colorspace_settings.name='sRGB';dark.pixels.foreach_set(cp);dark.filepath_raw=str(OUT/'_images/i_tod_teleporter_c.png');dark.file_format='PNG';dark.save()
manifest={'master_sha256':sha(ART/'teleporter_cyber.blend'),'base_master_sha256':sha(ART/'checkpoints/before_power_states.blend'),'emission_source_sha256':sha(source),'ready_image_sha256':sha(Path(ready.filepath_raw)),'base_color_source_sha256':sha(color_source),'state_color_sha256':sha(Path(dark.filepath_raw)),'recharge_geometry_sha256':sha(KIT/'recharge.json'),'recharge_triangles':len(geo['faces']),'states':['off','ready','pending'],'palette':palette,'revolution_seconds':3,'native_playtested':False}
(KIT/'state_source.json').write_text(json.dumps(manifest,indent=2));print('TELEPORTER_STATES_EXPORTED',json.dumps(manifest),flush=True)
