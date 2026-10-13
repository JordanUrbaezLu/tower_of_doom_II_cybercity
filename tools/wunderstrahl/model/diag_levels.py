"""MCP diagnostic (read-only): triangle count of the emitter assembly at every detail level."""
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emitter
importlib.reload(emitter)
for level in range(emitter.LEVELS):
    parts = emitter.build(level)
    tris = 0
    for p in parts:
        for f in p.faces:
            tris += len(f[0]) - 2
    print('level', level, 'parts', len(parts), 'triangles', tris)
