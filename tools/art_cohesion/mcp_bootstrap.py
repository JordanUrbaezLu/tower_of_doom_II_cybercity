import bpy, importlib.util, pathlib, sys
sys.dont_write_bytecode=True
root=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('tod_cohesion_mcp',root/'tmp/partner_shop_mcp/vendor/addon.py')
addon=importlib.util.module_from_spec(spec);sys.modules[spec.name]=addon;spec.loader.exec_module(addon);addon.register()
bpy.context.scene.blendermcp_auto_start_server=False
bpy.types.tod_cohesion_mcp=addon.BlenderMCPServer(host='127.0.0.1',port=9883)
bpy.types.tod_cohesion_mcp.start()
print('TOD_COHESION_MCP_READY port=9883',flush=True)
