"""Dedicated, VISIBLE Dealer boss studio; upstream Blender MCP on loopback port 9899.

The user steers from this window. Nothing here opens the shop, sky or
dealer-presence masters: the boss is its own file, art/dealer_boss/dealer_boss.blend.
"""
import importlib.util, pathlib, sys, os, json
import bpy
sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from process_guard import check
check()
log = ROOT / 'tmp/dealer_boss_mcp'
log.mkdir(parents=True, exist_ok=True)
(log / 'studio_pid.json').write_text(json.dumps({'pid': os.getpid(), 'port': 9899,
                                                'bootstrap': str(pathlib.Path(__file__).resolve()),
                                                'blender': bpy.app.version_string}))
spec = importlib.util.spec_from_file_location('tod2_dealer_boss_mcp', ROOT / 'tmp/archer_assets_mcp/vendor/addon.py')
addon = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = addon
spec.loader.exec_module(addon)
addon.register()
bpy.context.scene.blendermcp_auto_start_server = False
bpy.types.tod2_dealer_boss_mcp = addon.BlenderMCPServer(host='127.0.0.1', port=9899)
bpy.types.tod2_dealer_boss_mcp.start()
bpy.context.scene['tod2_dealer_boss_studio'] = True
print('TOD2_DEALER_BOSS_MCP_READY port=9899', flush=True)
