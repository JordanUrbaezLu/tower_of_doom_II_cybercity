"""Expose TIFF's unspecified fourth sample as alpha for the Blender preview.

BO3 stock sources carry this fourth channel. Pillow otherwise discards it.
Only review copies are written; native source TIFFs are read-only.
"""
import io,struct,pathlib,sys
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset,MT
out=ROOT/'art/necro_staff/soul_wave';out.mkdir(exist_ok=True)
for name in ['gfx_smk_whisp_anim_em','gfx_keeper_symbols_zod_em']:
    fields=asset('image',asset('material',name)['colorMap'])
    raw=bytearray((MT/fields['baseImage'].replace('\\','/')).read_bytes())
    order='<' if raw[:2]==b'II' else '>'
    assert struct.unpack_from(order+'H',raw,2)[0]==42
    offset=struct.unpack_from(order+'I',raw,4)[0]
    count=struct.unpack_from(order+'H',raw,offset)[0]
    for i in range(count):
        pos=offset+2+12*i;tag,kind,n=struct.unpack_from(order+'HHI',raw,pos)
        if tag==338:
            assert kind==3 and n==1
            struct.pack_into(order+'H',raw,pos+8,2)
    image=Image.open(io.BytesIO(raw));assert image.mode=='RGBA'
    assert image.getchannel('A').getextrema()==(0,255)
    image.save(out/(name+'.png'))
print('Native atlas review copies retain all four TIFF channels')
