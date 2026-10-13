"""Dedicated Cyber Sword studio, upstream Blender MCP on loopback 9886."""
import bpy, importlib.util, pathlib, sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('tod_cyber_sword_mcp',ROOT/'tmp/archer_assets_mcp/vendor/addon.py')
addon=importlib.util.module_from_spec(spec);sys.modules[spec.name]=addon
spec.loader.exec_module(addon);addon.register()
bpy.context.scene.blendermcp_auto_start_server=False
bpy.types.tod_cyber_sword_mcp=addon.BlenderMCPServer(host='127.0.0.1',port=9886)
bpy.types.tod_cyber_sword_mcp.start()
print('CYBER_SWORD_MCP_READY port=9886',flush=True)
