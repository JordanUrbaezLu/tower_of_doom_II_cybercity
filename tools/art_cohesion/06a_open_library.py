import bpy,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/cybercity_materials/cybercity_material_library.blend'))
print('CROWN_LIBRARY_OPEN: run 06_author_crown.py in the next MCP call after context refresh')
