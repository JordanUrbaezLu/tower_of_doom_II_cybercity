"""Preserve/close only our known idle art studios before the memory-heavy bake."""
import asyncio
import datetime
import os
import pathlib
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=pathlib.Path(__file__).resolve().parents[2]
async def main():
    for port,name in ((9890,'fleet'),(9885,'alarm'),(9887,'button'),(9896,'sky')):
        env=dict(os.environ,BLENDER_MCP_DISABLE_TELEMETRY='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT=str(port),PYTHONDONTWRITEBYTECODE='1')
        async with stdio_client(StdioServerParameters(command=sys.executable,args=['-m','blender_mcp.server'],env=env)) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=datetime.timedelta(seconds=180)) as session:
                await session.initialize()
                code="import bpy\nprint('PRESERVED_STUDIO',bpy.data.filepath)\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(ROOT/'tmp/sky_cohesion'/('preserved_'+name+'.blend')))+")\nbpy.app.timers.register(lambda: bpy.ops.wm.quit_blender(),first_interval=1.0)"
                result=await session.call_tool('execute_blender_code',{'code':code,'user_prompt':'Preserve our saved preview and release memory for the authorized full sky lighting bake.'})
                if result.isError:raise RuntimeError(str(result))
                for content in result.content:
                    if hasattr(content,'text'):print(content.text)
asyncio.run(main())
