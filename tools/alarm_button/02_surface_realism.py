"""Run via the button's real MCP client on port 9887; outputs are staged."""
import pathlib, sys, importlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'crown_alarm'))
import surface_realism
importlib.reload(surface_realism)
surface_realism.author('alarm_button')
