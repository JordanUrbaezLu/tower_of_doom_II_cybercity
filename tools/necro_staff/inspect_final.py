"""MCP: record final editable-source material bindings after promotion."""
from pathlib import Path
source=Path(__file__).with_name('inspect_detail.py').read_text()
source=source.replace("ART=ROOT/'art/necro_staff/detail_pass'","ART=ROOT/'art/necro_staff'")
exec(compile(source,__file__,'exec'))
