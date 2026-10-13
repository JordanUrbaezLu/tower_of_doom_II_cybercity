"""Send one Dealer boss authoring script to the live studio through a real MCP ClientSession.

usage: python mcp_call.py                 -> scene info
       python mcp_call.py screenshot      -> viewport screenshot (saved under tmp/dealer_boss_mcp)
       python mcp_call.py <script.py>     -> execute a tools/dealer_boss script inside Blender
Every call's full result is retained as JSON evidence beside any screenshot.
"""
import asyncio, base64, datetime, json, os, pathlib, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/dealer_boss_mcp'
OUT.mkdir(parents=True, exist_ok=True)
PROMPT = ('Author the Black Market Dealer as the final boss: a deformable hooded, long-coated figure on the '
          'Keeper animation skeleton with a graphite X-eyed mask, long red nails and worn materials, '
          'for live user review in Blender.')


async def main():
    env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9899',
               PYTHONDONTWRITEBYTECODE='1')
    params = StdioServerParameters(command=sys.executable, args=['-m', 'blender_mcp.server'], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=datetime.timedelta(seconds=1800)) as session:
            await session.initialize()
            if len(sys.argv) < 2:
                name, args = 'get_scene_info', {'user_prompt': PROMPT}
            elif sys.argv[1] == 'screenshot':
                name, args = 'get_viewport_screenshot', {'max_size': 1600, 'user_prompt': PROMPT}
            else:
                path = pathlib.Path(sys.argv[1]).resolve()
                if not path.is_relative_to(ROOT / 'tools/dealer_boss'):
                    raise RuntimeError('Only tools/dealer_boss scripts may be sent to the Dealer boss studio')
                code = '__file__ = ' + repr(str(path)) + '\n' + path.read_text(encoding='utf-8-sig')
                name, args = 'execute_blender_code', {'code': code, 'user_prompt': PROMPT}
            result = await session.call_tool(name, args)
            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            (OUT / (stamp + '.json')).write_text(json.dumps(result.model_dump(mode='json'), indent=2), encoding='utf-8')
            failed = bool(result.isError)
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
                    failed |= 'Error executing code' in content.text or 'Error getting scene info' in content.text
                elif getattr(content, 'type', '') == 'image':
                    p = OUT / (stamp + '.png')
                    p.write_bytes(base64.b64decode(content.data))
                    print('SCREENSHOT', p)
            if failed:
                raise SystemExit(1)


asyncio.run(main())
