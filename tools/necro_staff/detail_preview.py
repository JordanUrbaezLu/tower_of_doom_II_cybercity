"""MCP: export and render staged detail without touching the live build inputs."""
from pathlib import Path
source=Path(__file__).with_name('export_preview.py').read_text()
source=source.replace("ART=ROOT/'art/necro_staff';OUT=ROOT/'model_export/tod_necro_staff'","ART=ROOT/'art/necro_staff/detail_pass';OUT=ART/'models'")
source=source.replace("(ROOT/'source_data/tod_necro_staff_art.gdt')","(ART/'tod_necro_staff_art.gdt')")
exec(compile(source,__file__,'exec'))
