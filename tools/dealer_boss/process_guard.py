"""Read-only workstation guard for the Dealer boss studio and its renders.

This PC has 16 GB. A Radiant bake alone peaks near the whole of it, so no
Blender authoring, export or render here may overlap a native build stage or
the game. Foreign Blender windows (another map's preview) are reported, never
closed: they are someone else's work.
"""
import json, subprocess, sys

# bake stages and the game: hard block for everything (a Radiant bake alone can take the whole 16 GB)
# (the Mod Tools LAUNCHER window itself is a GUI, not a build stage: it is reported, never a block)
NATIVE = ("$_.ProcessName -like 'Radiant*' -or $_.ProcessName -like 'BlackOps3*' -or $_.ProcessName -like 'cod2map*' "
          "-or $_.ProcessName -like 'gdtdb*'")
# a linker (~2 GB) blocks only heavy work (exports, bakes, Cycles renders); light authoring in the
# visible studio may continue beside it (user 2026-09-30: "reopen so I can see")
LINKER = "$_.ProcessName -like 'linker*'"


def processes(filter_expr):
    cmd = ("Get-Process -ErrorAction SilentlyContinue | Where-Object { " + filter_expr +
           " } | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress")
    r = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, check=True)
    out = json.loads(r.stdout) if r.stdout.strip() else []
    return out if isinstance(out, list) else [out]


def available_mb():
    cmd = "(Get-Counter '\\Memory\\Available MBytes').CounterSamples[0].CookedValue"
    r = subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, check=True)
    return float(r.stdout.strip() or 0)


def check(min_mb=900, strict=False):
    """strict=True (exports, bakes, renders) also refuses while a linker runs."""
    native = processes(NATIVE)
    if native:
        raise RuntimeError('Dealer studio held for an active native process: ' + json.dumps(native))
    linker = processes(LINKER)
    if linker and strict:
        raise RuntimeError('Dealer heavy work held for an active linker: ' + json.dumps(linker))
    mb = available_mb()
    if mb < min_mb:
        raise RuntimeError('Dealer studio held: only %.0f MB available (need %d)' % (mb, min_mb))
    foreign = processes("$_.ProcessName -like 'blender*'")
    return {'available_mb': mb, 'foreign_blender': foreign, 'linker_running': linker}


if __name__ == '__main__':
    print('DEALER_BOSS_GUARD_CLEAR', json.dumps(check(strict='--strict' in sys.argv)))
