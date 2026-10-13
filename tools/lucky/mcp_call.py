"""Execute modeling through a real upstream MCP ClientSession and retain evidence."""
import asyncio
import base64
import datetime
import json
import os
import pathlib
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/lucky_mcp'
OUT.mkdir(parents=True, exist_ok=True)
PROMPT = 'Author the Lucky Clover power-up (a four-leaf clover, gold rim, glowing veins), its small amulet twin for the Golden Zombie, and the Lucky Meteor (a dark rock with glowing gold cracks and emerald crystals) as native BO3 meshes with textures and previews (docs/197).'

async def main():
    env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9888', PYTHONDONTWRITEBYTECODE='1')
    params = StdioServerParameters(command=sys.executable, args=['-m', 'blender_mcp.server'], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=datetime.timedelta(seconds=1200)) as session:
            await session.initialize()
            if len(sys.argv) < 2:
                name, args = 'get_scene_info', {'user_prompt': PROMPT}
            elif sys.argv[1] == 'screenshot':
                name, args = 'get_viewport_screenshot', {'max_size': 1600, 'user_prompt': PROMPT}
            else:
                path = pathlib.Path(sys.argv[1]).resolve()
                if not path.is_relative_to(ROOT / 'tools/lucky'):
                    raise RuntimeError('Only tools/lucky scripts may be sent to this dedicated studio')
                name, args = 'execute_blender_code', {'code': '__file__ = ' + repr(str(path)) + '\n' + path.read_text(encoding='utf-8-sig'), 'user_prompt': PROMPT}
            result = await session.call_tool(name, args)
            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            (OUT / (stamp + '.json')).write_text(json.dumps(result.model_dump(mode='json'), indent=2), encoding='utf-8')
            failed = bool(result.isError)
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
                    failed |= 'Error executing code' in content.text or 'Error getting scene info' in content.text
                elif getattr(content, 'type', '') == 'image':
                    path = OUT / (stamp + '.png')
                    path.write_bytes(base64.b64decode(content.data))
                    print('SCREENSHOT', path)
            if failed:
                raise SystemExit(1)

asyncio.run(main())
