"""Isolated SKY FLEET studio: the actual upstream Blender MCP addon on loopback port 9890 (docs/192)."""
import importlib.util
import pathlib
import sys
import bpy
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('tod2_sky_mcp', ROOT / 'tmp/archer_assets_mcp/vendor/addon.py')
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)
addon.register()
bpy.context.scene.blendermcp_auto_start_server = False
bpy.types.tod2_sky_mcp = addon.BlenderMCPServer(host='127.0.0.1', port=9890)
bpy.types.tod2_sky_mcp.start()
print('TOD2_SKY_MCP_READY port=9890', flush=True)
