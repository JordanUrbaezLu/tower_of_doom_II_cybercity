"""Send ONE Wunderstrahl model script to the live studio (port 9893) through a real MCP ClientSession.

  <mcp python> -B tools/wunderstrahl/model/mcp_call.py                 -> scene info
  <mcp python> -B tools/wunderstrahl/model/mcp_call.py screenshot      -> viewport screenshot (tmp/wunderstrahl/mcp/*.png)
  <mcp python> -B tools/wunderstrahl/model/mcp_call.py <script.py>     -> execute a tools/wunderstrahl/model script
  <mcp python> -B tools/wunderstrahl/model/mcp_call.py <script.py> RENDER_SET=main   -> same, with a string global

The MCP Python environment on this machine: ../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe
(read-only use; -B and PYTHONDONTWRITEBYTECODE keep it from writing anything there).
Every call's full result is retained as JSON (plus any screenshot) under tmp/wunderstrahl/mcp/ - the authoring record.
A call refuses to start while a native editor/compiler stage or the game runs (16 GB workstation; CLAUDE.md rule 8).
The upstream server answers within 180 s, so every step script is written to finish well inside that.
"""
import asyncio, base64, datetime, json, os, pathlib, subprocess, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'tmp/wunderstrahl/mcp'
OUT.mkdir(parents=True, exist_ok=True)
PROMPT = ('Rebuild the BO3 Wunderwaffe DG-2 into the Wunderstrahl laser wonder weapon: keep its silhouette and its '
          'twelve-bone animation rig, add a compact gunmetal-and-brass emitter ring assembly with a faceted yellow '
          'focusing lens on the tag_flash axis, a yellow laser filament in the glass tube, warm yellow bulbs, thin '
          'yellow conduits, and finished worn surfaces (dark lacquered composite stock, gunmetal body with brass '
          'fittings, aged copper coils). No cyan or blue.')
BLOCKERS = ('Radiant', 'BlackOps3', 'cod2map', 'linker', 'gdtdb')


def native_blockers():
    cmd = ("Get-Process -ErrorAction SilentlyContinue | Where-Object { " +
           ' -or '.join("$_.ProcessName -like '%s*'" % b for b in BLOCKERS) +
           " } | Select-Object -ExpandProperty ProcessName")
    r = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True)
    return [x for x in r.stdout.split() if x]


async def main():
    if len(sys.argv) >= 2 and sys.argv[1] != 'screenshot':
        running = native_blockers()
        if running:
            raise SystemExit('WUNDERSTRAHL studio call held: native stage or game running: ' + ', '.join(running))
    env = dict(os.environ, BLENDER_MCP_DISABLE_TELEMETRY='1', BLENDER_HOST='127.0.0.1', BLENDER_PORT='9893',
               PYTHONDONTWRITEBYTECODE='1')
    params = StdioServerParameters(command=sys.executable, args=['-B', '-m', 'blender_mcp.server'], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=datetime.timedelta(seconds=900)) as session:
            await session.initialize()
            if len(sys.argv) < 2:
                name, args = 'get_scene_info', {'user_prompt': PROMPT}
            elif sys.argv[1] == 'screenshot':
                name, args = 'get_viewport_screenshot', {'max_size': 1600, 'user_prompt': PROMPT}
            else:
                path = pathlib.Path(sys.argv[1]).resolve()
                if not path.is_relative_to(ROOT / 'tools/wunderstrahl/model'):
                    raise RuntimeError('Only tools/wunderstrahl/model scripts may be sent to the Wunderstrahl studio')
                # Optional NAME=value arguments become string globals at the top of the sent script (e.g. a render
                # subset), so a step never needs a scratch copy of itself.
                extra = ''.join('%s = %r\n' % tuple(a.split('=', 1)) for a in sys.argv[2:] if '=' in a)
                code = '__file__ = ' + repr(str(path)) + '\n' + extra + path.read_text(encoding='utf-8-sig')
                name, args = 'execute_blender_code', {'code': code, 'user_prompt': PROMPT}
            result = await session.call_tool(name, args)
            stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            record = dict(tool=name, script=(sys.argv[1] if len(sys.argv) > 1 else None), stamp=stamp,
                          result=result.model_dump(mode='json'))
            (OUT / (stamp + '.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
            failed = bool(result.isError)
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
                    failed |= ('Error executing code' in content.text or 'Error getting scene info' in content.text
                               or '"exception_type"' in content.text)
                elif getattr(content, 'type', '') == 'image':
                    p = OUT / (stamp + '.png')
                    p.write_bytes(base64.b64decode(content.data))
                    print('SCREENSHOT', p)
            print('MCP_RECORD', OUT / (stamp + '.json'))
            if failed:
                raise SystemExit(1)

asyncio.run(main())
