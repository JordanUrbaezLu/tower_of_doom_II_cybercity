"""Display the final native-map material render in the owned crown_alarm window."""
import bpy, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
art=ROOT/'art/crown_alarm'
if not (art/'realism_review/after.png').exists():art=ROOT/'tmp/alarm_realism/staged/art/crown_alarm'
path=art/'crown_alarm.blend'
if pathlib.Path(bpy.data.filepath).resolve()!=path.resolve():
    bpy.ops.wm.open_mainfile(filepath=str(path))
    print('OPENED; call once more after Blender redraws')
else:
    win=bpy.context.window_manager.windows[0]
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.shading.type='SOLID'
    area=max(win.screen.areas,key=lambda a:a.width*a.height)
    area.type='IMAGE_EDITOR'
    area.spaces.active.image=bpy.data.images.load(str(path.parent/'realism_review/after.png'),check_existing=False)
    area.spaces.active.show_region_ui=False
    win.workspace.name='CROWN ALARM - native map render'
    bpy.context.scene['preview_limit']='Actual native maps and native gloss range; saved Blender render, not native BO3 BRDF/probe approval.'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print('CROWN_ALARM_FINAL_MATERIAL_RENDER_VISIBLE')
