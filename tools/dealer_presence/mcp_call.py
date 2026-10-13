"""Run a Dealer panel script through a real upstream MCP ClientSession (port 9897) and keep the evidence.

  <mcp python> tools/dealer_presence/mcp_call.py                 -> scene info
  <mcp python> tools/dealer_presence/mcp_call.py screenshot      -> viewport screenshot (tmp/dealer_presence_mcp/*.png)
  <mcp python> tools/dealer_presence/mcp_call.py <script.py>     -> execute a tools/dealer_presence script in the studio
The MCP Python environment on this machine: ../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe
"""
import asyncio
import base64
import datetime
import json
import os
import pathlib
import sys
from process_guard import check
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/dealer_presence_mcp'
OUT.mkdir(parents=True, exist_ok=True)
PROMPT = 'Create three restrained static wall portraits of the actual Black Market Dealer on existing walls along the descent. Preserve canonical hood, red X eyes and uneven grin. Use worn native city materials, exact wall geometry and matched player views; no new lights, collision or runtime effects.'

async def main():
    check()
    env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9897', PYTHONDONTWRITEBYTECODE='1')
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
                if not path.is_relative_to(ROOT / 'tools/dealer_presence'):
                    raise RuntimeError('Only tools/dealer_presence scripts may be sent to this dedicated studio')
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
