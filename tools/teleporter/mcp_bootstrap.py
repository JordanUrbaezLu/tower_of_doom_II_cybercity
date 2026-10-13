"""Isolated teleporter authoring session using the installed upstream addon."""
import bpy, importlib.util, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
VENDOR = ROOT.parent / 'tower_of_doom_II_hellbound/tmp/blender_mcp_vendor/addon.py'
spec = importlib.util.spec_from_file_location('tod_teleporter_mcp', VENDOR)
addon = importlib.util.module_from_spec(spec); sys.modules[spec.name] = addon
spec.loader.exec_module(addon); addon.register()
bpy.context.scene.blendermcp_auto_start_server = False
bpy.types.tod_teleporter_mcp = addon.BlenderMCPServer(host='127.0.0.1', port=9879)
bpy.types.tod_teleporter_mcp.start()
print('TOD_TELEPORTER_MCP_READY port=9879', flush=True)
