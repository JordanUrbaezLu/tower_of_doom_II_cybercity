"""Project-owned upstream Blender MCP transport for the shared art kit."""
import asyncio,datetime,json,os,pathlib,sys,base64
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/art_cohesion/mcp';OUT.mkdir(parents=True,exist_ok=True)
async def main():
    env=dict(os.environ,BLENDER_MCP_DISABLE_TELEMETRY='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT='9883',PYTHONDONTWRITEBYTECODE='1')
    async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','blender_mcp.server'],env=env)) as (r,w):
        async with ClientSession(r,w,read_timeout_seconds=datetime.timedelta(seconds=600)) as session:
            await session.initialize()
            prompt='Author the shared Cybercity material kit and one crown-room review bay; preserve original props and their state colors.'
            if sys.argv[1]=='screenshot':name,args='get_viewport_screenshot',{'max_size':1600,'user_prompt':prompt}
            else:
                p=pathlib.Path(sys.argv[1]).resolve();assert p.is_relative_to(ROOT/'tools/art_cohesion')
                name,args='execute_blender_code',{'code':'__file__ = '+repr(str(p))+'\n'+p.read_text(encoding='utf-8-sig'),'user_prompt':prompt}
            result=await session.call_tool(name,args)
            stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            (OUT/(stamp+'.json')).write_text(json.dumps(result.model_dump(mode='json'),indent=2))
            for c in result.content:
                if hasattr(c,'text'):print(c.text)
                elif getattr(c,'type','')=='image':
                    p=OUT/(stamp+'.png');p.write_bytes(base64.b64decode(c.data));print('SCREENSHOT',p)
            if result.isError or any('Error executing code' in getattr(c,'text','') for c in result.content):raise SystemExit(1)
asyncio.run(main())
