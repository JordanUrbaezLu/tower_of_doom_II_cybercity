"""Background render of the MCP-prepared exported-mesh review scenes."""
import bpy
from pathlib import Path
folder=Path(__file__).resolve().parents[2]/'art/teleporter/surface_repair'
for stage in ('before','after'):
    bpy.ops.wm.open_mainfile(filepath=str(folder/('binary_'+stage+'.blend')))
    bpy.context.scene.render.filepath=str(folder/('binary_'+stage+'.png'))
    bpy.ops.render.render(write_still=True)
    print('TELEPORTER_SURFACE_RENDERED',stage,flush=True)
