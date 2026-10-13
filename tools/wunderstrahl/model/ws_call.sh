#!/usr/bin/env bash
# Git-Bash convenience wrapper: run one Wunderstrahl studio call with the machine's MCP Python environment.
#   tools/wunderstrahl/model/ws_call.sh tools/wunderstrahl/model/02_render_reference.py RENDER_SET=main
# The MCP server's own chatter goes to tmp/wunderstrahl/mcp/client_stderr.log; the script output prints here.
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MCPPY="$ROOT/../tower_of_doom_II_hellbound/tmp/gold_sword_env/Scripts/python.exe"
cd "$ROOT" || exit 9
"$MCPPY" -B tools/wunderstrahl/model/mcp_call.py "$@" 2>>tmp/wunderstrahl/mcp/client_stderr.log
