"""Tiny isolated Dealer-panel studio; never opens shop or sky master."""
import importlib.util,pathlib,sys,bpy,os,json
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from process_guard import check
check()
(ROOT/'tmp/dealer_presence_mcp').mkdir(parents=True,exist_ok=True)
(ROOT/'tmp/dealer_presence_mcp/studio_pid.json').write_text(json.dumps({'pid':os.getpid(),'port':9897,'bootstrap':str(pathlib.Path(__file__).resolve())}))
spec=importlib.util.spec_from_file_location('tod2_dealer_presence_mcp',ROOT/'tmp/archer_assets_mcp/vendor/addon.py')
addon=importlib.util.module_from_spec(spec);sys.modules[spec.name]=addon;spec.loader.exec_module(addon);addon.register()
bpy.context.scene.blendermcp_auto_start_server=False
bpy.types.tod2_dealer_presence_mcp=addon.BlenderMCPServer(host='127.0.0.1',port=9897)
bpy.types.tod2_dealer_presence_mcp.start()
print('TOD2_DEALER_PRESENCE_MCP_READY port=9897',flush=True)
