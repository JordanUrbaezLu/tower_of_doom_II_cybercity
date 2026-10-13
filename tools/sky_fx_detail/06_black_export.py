"""MCP: lossless black aperture export (disable Blender's default 1-LSB dither)."""
import bpy,pathlib,hashlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/sky_fx_detail/staged'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'sky_detail.blend'))
scene=bpy.context.scene
for col in scene.collection.children:
    col.hide_render=col.name!='Rift absorbing aperture'
    col.hide_viewport=False
scene.render.dither_intensity=0
scene.render.film_transparent=True
scene.render.use_compositing=False
scene.render.resolution_x=scene.render.resolution_y=512
scene.camera.location=(0,0,8);scene.camera.rotation_euler=(0,0,0);scene.camera.data.ortho_scale=2
scene.render.filepath=str(OUT/'i_tod_sky_rift_void.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail.blend'))
m=json.loads((OUT/'manifest.json').read_text())
m['images']['i_tod_sky_rift_void.png']=hashlib.sha256((OUT/'i_tod_sky_rift_void.png').read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
print('SKY VOID BLACK EXPORT OK')
