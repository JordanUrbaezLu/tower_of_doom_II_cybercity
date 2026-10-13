"""Run a sky dealer script through a real upstream MCP ClientSession (port 9896) and keep the evidence.

  <mcp python> tools/sky_dealer/mcp_call.py                 -> scene info
  <mcp python> tools/sky_dealer/mcp_call.py screenshot      -> viewport screenshot (tmp/sky_dealer_mcp/*.png)
  <mcp python> tools/sky_dealer/mcp_call.py <script.py>     -> execute a tools/sky_dealer script in the studio
The MCP Python environment on this machine: ../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe
"""
import asyncio
import base64
import datetime
import json
import os
import pathlib
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / 'tmp/sky_dealer_mcp'
OUT.mkdir(parents=True, exist_ok=True)
PROMPT = 'Replace only the engineered sky title crest with the Black Market dealer hood, red X eyes and stitched grin. Preserve the accepted cyber city, station, celestial restraint and massive lettering. Bake the dull sky plus matching native bright reveal card from the same source and exact camera geometry.'

def require_resource_slot():
    guard = str(ROOT / 'tools/sky_dealer/resource_guard.ps1').replace("'", "''")
    result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                             ". '"+guard+"'; Assert-SkyResourceSlot 'Sky MCP action'"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'Sky resource preflight failed')

async def main():
    require_resource_slot()
    env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9896', PYTHONDONTWRITEBYTECODE='1')
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
                if not path.is_relative_to(ROOT / 'tools/sky_dealer'):
                    raise RuntimeError('Only tools/sky_dealer scripts may be sent to this dedicated studio')
                name, args = 'execute_blender_code', {'code': '__file__ = ' + repr(str(path)) + '\n' + path.read_text(encoding='utf-8-sig'), 'user_prompt': PROMPT}
            require_resource_slot()  # imports/connection can take time; recheck immediately before work
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
