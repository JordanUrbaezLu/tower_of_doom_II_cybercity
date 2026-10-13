"""MCP: first-person staged detail with the unchanged current casting clips."""
from pathlib import Path
source=Path(__file__).with_name('motion_preview.py').read_text()
source=source.replace("ART=ROOT/'art/necro_staff'","ART=ROOT/'art/necro_staff/detail_pass'")
source=source.replace("(ART/'animations.json')","(ROOT/'art/necro_staff/animations.json')")
source=source.replace("ROOT/f'model_export/tod_necro_staff/tod_necro_staff{tier}_view_lod0.XMODEL_BIN'","ART/f'models/tod_necro_staff{tier}_view_lod0.XMODEL_BIN'")
exec(compile(source,__file__,'exec'))
