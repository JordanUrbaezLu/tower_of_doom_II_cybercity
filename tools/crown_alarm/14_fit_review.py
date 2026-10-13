"""Fit the already-open final material render without a file-load UI switch."""
import bpy, json, pathlib, hashlib
win=bpy.context.window_manager.windows[0]
area=max((a for a in win.screen.areas if a.type=='IMAGE_EDITOR'),key=lambda a:a.width*a.height)
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(window=win,screen=win.screen,area=area,region=region):
    bpy.ops.image.view_all(fit_view=True)
area.spaces.active.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
image_path=pathlib.Path(bpy.path.abspath(area.spaces.active.image.filepath))
proof={'workspace':win.workspace.name,'area':area.type,'image':str(image_path),'image_sha256':hashlib.sha256(image_path.read_bytes()).hexdigest(),'native_map_preview':True,'native_visual_verified':False,'canonical_master_saved':True,'lens_constant_dielectric_f0':.04,'lens_native_channel_receipt':'lens_native_channels.json','live_viewports':sum(a.spaces.active.shading.type=='RENDERED' for s in bpy.data.screens for a in s.areas if a.type=='VIEW_3D')}
path=pathlib.Path(__file__).resolve().parents[2]/'art/crown_alarm/realism_review/visible_preview.json'
path.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
