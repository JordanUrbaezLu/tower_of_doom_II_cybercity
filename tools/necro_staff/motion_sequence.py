"""MCP: animated review of exact exported channel/pulse clip frames."""
from pathlib import Path
source=Path(__file__).with_name('motion_preview.py').read_text()
start=source.index('cases=');end=source.index('\nhandpath=',start)
source=source[:start]+"cases=[]\nfor mode,frames in [('channel_in',range(0,9,2)),('channel_loop',range(0,34,3)),('channel_out',range(0,10,2)),('pulse',range(0,19,2))]:\n    cases.extend((mode+'_'+str(i).zfill(2),'tod_vm_necro_staff_'+mode,i) for i in frames)"+source[end:]
source=source.replace('for tier in [2,3]:','for tier in [3]:').replace('resolution_x=1280;scene.render.resolution_y=720','resolution_x=640;scene.render.resolution_y=360')
source=source.replace("ART/f'tier{tier}_vm_{label}.png'","ART/'motion'/f'{label}.png'")
source=source.replace("ART/'first_person_review.blend'","ART/'casting_motion_review.blend'")
(Path(__file__).resolve().parents[2]/'art/necro_staff/motion').mkdir(exist_ok=True)
exec(compile(source,__file__,'exec'))
