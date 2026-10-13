"""MCP: prepare a matched preview of the repaired exported material."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('inspect_native_surface.py')),init_globals={'SURFACE_STAGE':'after'})
