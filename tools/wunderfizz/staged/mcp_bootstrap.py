"""Dedicated exact-import review using upstream Blender MCP, loopback port 9912."""
import importlib.util,pathlib,sys,bpy
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('tod2_wunderfizz_mcp',ROOT/'tmp/archer_assets_mcp/vendor/addon.py')
addon=importlib.util.module_from_spec(spec);sys.modules[spec.name]=addon;spec.loader.exec_module(addon)
addon.register();bpy.context.scene.blendermcp_auto_start_server=False
bpy.types.tod2_wunderfizz_mcp=addon.BlenderMCPServer(host='127.0.0.1',port=9912)
bpy.types.tod2_wunderfizz_mcp.start()
print('TOD2_WUNDERFIZZ_MCP_READY port=9912',flush=True)
