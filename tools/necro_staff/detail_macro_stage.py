"""MCP: review the final seam correction before promoting build inputs."""
from pathlib import Path
source=Path(__file__).with_name('detail_macros.py').read_text()
source=source.replace("ART=ROOT/'art/necro_staff'","ART=ROOT/'art/necro_staff/detail_pass'")
exec(compile(source,__file__,'exec'))
