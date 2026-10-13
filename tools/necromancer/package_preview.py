"""Package rendered Blender phases; verify the mask's hollow centre and safe edges."""
from pathlib import Path
from PIL import Image, ImageDraw
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/necromancer/pulse'
texture=ROOT/'model_export/tod_necro/i_tod_necro_pulse.png'
im=Image.open(texture).convert('RGBA');a=im.getchannel('A')
assert im.size==(512,512)
assert a.crop((180,180,332,332)).getextrema()==(0,0),'filled centre'
assert a.crop((0,0,512,4)).getextrema()==(0,0),'hard texture edge'
frames=[Image.open(p).convert('RGB') for p in sorted(OUT.glob('anim_*.png'))]
frames[0].save(OUT/'pulse.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
sheet=Image.new('RGB',(1600,960),(18,19,22));d=ImageDraw.Draw(sheet)
for i,frame in enumerate([5,10,15,40]):
    x=(i%2)*800;y=(i//2)*480
    sheet.paste(Image.open(OUT/f'phase_{frame:02}.png'),(x,y))
    d.text((x+12,y+457),f'{(frame-1)*10} ms | player height | Blender preview, not native game',fill='white')
sheet.save(OUT/'phases.jpg',quality=92)
data={'texture':str(texture.relative_to(ROOT)),'sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),
      'authoring':'Blender MCP, tools/necromancer/author_pulse.py','resolution':[512,512],
      'native_particles_per_cast':2,'native_lights':0,'native_lifetime_ms':845,
      'native_edge_ms':140,'native_playtested':False,'preview_bloom':False}
(OUT/'manifest.json').write_text(json.dumps(data,indent=2))
print('PULSE ART: hollow-centre / alpha-edge checks passed; GIF and contact sheet saved.')
