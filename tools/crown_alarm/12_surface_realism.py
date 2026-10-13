"""Run via this family's real MCP client; all outputs are staged."""
import pathlib, sys, importlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import surface_realism
importlib.reload(surface_realism)
surface_realism.author('crown_alarm')
