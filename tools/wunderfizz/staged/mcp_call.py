"""Send review-only scripts to the owned upstream MCP studio and retain proof."""
import asyncio,datetime,json,os,pathlib,sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=pathlib.Path(__file__).resolve().parents[3]
async def main():
    env=dict(os.environ,BLENDER_MCP_DISABLE_TELEMETRY='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT='9912',PYTHONDONTWRITEBYTECODE='1')
    params=StdioServerParameters(command=sys.executable,args=['-m','blender_mcp.server'],env=env)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write,read_timeout_seconds=datetime.timedelta(seconds=300)) as session:
            await session.initialize()
            if len(sys.argv)>1:
                path=pathlib.Path(sys.argv[1]).resolve();assert path.is_relative_to(ROOT/'tools/wunderfizz')
                result=await session.call_tool('execute_blender_code',{'code':'__file__ = '+repr(str(path))+'\n'+path.read_text(encoding='utf-8-sig'),'user_prompt':'Inspect the exact BO6 machine source UVs/material scale/off-on-animation states; do not redesign or alter native assets.'})
            else:result=await session.call_tool('get_scene_info',{'user_prompt':'Inspect only the Wunderfizz-owned studio.'})
            stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            (ROOT/'tmp/wunderfizz/assets'/('mcp_'+stamp+'.json')).write_text(json.dumps(result.model_dump(mode='json'),indent=2))
            failed=bool(result.isError)
            for item in result.content:
                if hasattr(item,'text'):
                    print(item.text);failed|='Error executing code' in item.text
            if failed:raise SystemExit(1)
asyncio.run(main())
