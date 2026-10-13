"""Promote inspected staged sprite art when the guarded build lane is idle."""
import hashlib,json,pathlib,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import native_detail as N
STAGE=ROOT/'tmp/sky_fx_detail/staged'
m=json.loads((STAGE/'manifest.json').read_text())
for image,_ in N.MATERIALS.values():
    p=STAGE/(image+'.png')
    assert hashlib.sha256(p.read_bytes()).hexdigest()==m['images'][p.name],p
N.IMAGES.mkdir(parents=True,exist_ok=True)
N.ART.mkdir(parents=True,exist_ok=True)
for image,_ in N.MATERIALS.values():shutil.copy2(STAGE/(image+'.png'),N.IMAGES/(image+'.png'))
for name in ('sky_detail.blend','sky_detail_preview.blend','detail_preview.png'):
    shutil.copy2(STAGE/name,N.ART/name)
for p in STAGE.glob('layer_phase_*.png'):shutil.copy2(p,N.ART/p.name)
from PIL import Image
frames=[Image.open(p).convert('RGB') for p in sorted(N.ART.glob('layer_phase_*.png'))]
assert len(frames)==9,'complete the phase preview before installing'
frames[0].save(N.ART/'detail_layers.gif',save_all=True,append_images=frames[1:],duration=250,loop=0)
m['master_sha256']=hashlib.sha256((N.ART/'sky_detail.blend').read_bytes()).hexdigest()
m['sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'tools/sky_fx_detail').glob('0[1-6]_*.py'))}
m['native_preview_limit']='Authored texture layers only; native stock flow/lightning/distortion, bloom/exposure and OIT need user review.'
(N.ART/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
N.GDT.write_text(N.gdt_text(),encoding='utf-8',newline='\n')
N.verify()
print('SKY DETAIL INSTALLED - now regenerate sky FX and perform a full guarded build')
