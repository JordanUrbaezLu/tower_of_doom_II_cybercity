"""Run a Lua 5.1 UI harness (tools/test_*.lua) under lupa from the repo root; exit 1 on any Lua error.
Used by build_map.ps1 on every build (the pause-menu settings crash of 2026-09-26 was a Lua-only
change that no other gate reads)."""
import sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lupa.lua51 as l
for path in sys.argv[1:]:
    L = l.LuaRuntime(unpack_returned_tuples=True)
    try:
        L.execute(open(path, encoding="utf-8").read())
    except Exception as e:
        print("LUA HARNESS FAILED:", path, "->", e)
        sys.exit(1)
