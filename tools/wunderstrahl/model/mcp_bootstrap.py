"""Dedicated Wunderstrahl studio: upstream Blender MCP on loopback 9893 (docs/219, the model track).

Launch (visible window):  tools/wunderstrahl/model/start_studio.ps1
The addon is a private copy of the vendored upstream server (tmp/wunderstrahl/vendor/addon.py, sha256 recorded in
art/wunderstrahl/record.json), so another session cleaning its own tmp/ folder cannot take this studio down.
"""
import bpy, importlib.util, pathlib, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('tod_wunderstrahl_mcp', ROOT / 'tmp/wunderstrahl/vendor/addon.py')
addon = importlib.util.module_from_spec(spec); sys.modules[spec.name] = addon
spec.loader.exec_module(addon); addon.register()
bpy.context.scene.blendermcp_auto_start_server = False
bpy.types.tod_wunderstrahl_mcp = addon.BlenderMCPServer(host='127.0.0.1', port=9893)
bpy.types.tod_wunderstrahl_mcp.start()
print('WUNDERSTRAHL_MCP_READY port=9893', flush=True)
