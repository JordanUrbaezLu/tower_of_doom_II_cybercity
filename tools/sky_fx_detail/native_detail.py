"""Authored sprite pass on the existing bounded sky FX; no new runtime owners.

Imported by gen_fx after its normal composition. Donor motion/lifecycle remain
native; only materials, selected opacity/overlap and the hollow aperture change.
"""
import csv, hashlib, json, math, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/sky_ships'))
import efx_lib as E
from check_effects import check

ART = ROOT/'art/sky_fx_detail'
IMAGES = ROOT/'source_data/tod_sky_detail/_images'
GDT = ROOT/'source_data/tod_sky_detail.gdt'
MATERIALS = {
    'fibre': ('i_tod_sky_rift_fibre',128),
    'dust': ('i_tod_sky_rift_dust',64),
    'void': ('i_tod_sky_rift_void',0),
    'wake': ('i_tod_sky_meteor_wake',16),
}

def material(e, key):
    kind,names = e.visual
    for item in reversed(e.items):
        if isinstance(item,E.Block) and item.key==kind:
            item.body=['\t\t"mtl_tod_sky_detail_'+key+'"']
            break
    # Atlas state belongs to the image, not the donor. Never sample a single
    # frame texture using inherited 8x8 flipbook indices or lerp/reverse flags.
    e.set('atlasBehavior','startFixed')
    e.set('atlasIndex',0)
    e.set('atlasFps',0)
    if e.has('atlasLoopCount'): e.set('atlasLoopCount',1)
    if e.has('atlasColIndexBits'): e.set('atlasColIndexBits',0)
    if e.has('atlasRowIndexBits'): e.set('atlasRowIndexBits',0)
    if e.has('atlasEntryCount'): e.set('atlasEntryCount',1)
    if e.has('atlasIndexRange'): e.set('atlasIndexRange',0)

def alpha(e, rows):
    g=e.graph('alphaGraph');g.scale=1;g.curves=[rows,rows]

def refine(effects):
    out=dict(effects)
    for name,text in effects.items():
        is_rift=name.startswith('fx_sky_worm_')
        is_trail=name in ('fx_sky_star_trail','fx_sky_fireball_trail_o','fx_sky_fireball_trail_g','fx_sky_fireball_frag')
        if not (is_rift or is_trail): continue
        fx=E.parse(text)
        for e in fx.elements:
            if is_trail and e.visual[0]=='trail':
                material(e,'wake')
                # The painted wake has generous transparent borders. Retain
                # the dominant streak plus a few fine irregular ion threads.
                e.graph('sizeGraph0').scale *= 1.35
                e.graph('sizeGraph1').scale *= 1.35
            elif is_rift and e.name in ('rim','ring'):
                material(e,'fibre')
            elif is_rift and e.name=='swirl' and '_open_' in name:
                # Keep the stock animated fluid underneath the authored fine
                # rim: the filaments are detail, not a replacement for flow.
                e.set('spawnLooping',[700,0])
                e.set('lifeSpanMsec',[1400,0])
                alpha(e,[(0,0),(.25,.24),(.75,.2),(1,0)])
            elif is_rift and '_open_' in name and e.name=='aura':
                material(e,'dust')
                e.set('spawnLooping',[500,0])
                e.set('lifeSpanMsec',[700,0])
                e.set('angleVelRoll',[7,5])
                alpha(e,[(0,0),(.25,.28),(.65,.22),(1,0)])
            elif is_rift and '_open_' in name and e.name=='core':
                # A true black aperture replaces the sustained white centre.
                # Glow/lightning/flash remain around it, never a white disc.
                material(e,'void')
                e.set('spawnLooping',[600,0])
                e.set('lifeSpanMsec',[600,0])
                # Remain wholly inside the growing fibre's hollow centre:
                # premultiplied OIT must not sort dark over the lit rim.
                for key in ('sizeGraph0','sizeGraph1'): e.graph(key).scale *= 1.6
                g=e.graph('colorGraph');g.curves=[[(0,0,0,0),(1,0,0,0)]]*2
                alpha(e,[(0,.90),(1,.90)])
            elif is_rift and '_open_' in name and e.name=='seed':
                # Only the opening seed is luminous inside the aperture; fade
                # before the ship emerges so surface/negative space survives.
                alpha(e,[(0,.15),(.25,.55),(.5,.18),(.72,0),(1,0)])
        out[name]=fx.text()
    check(effects,out)
    return out

def gdt_text():
    lines=['{']
    for key,(image,scale) in MATERIALS.items():
        rows={
            'baseImage':'source_data/tod_sky_detail/_images/'+image+'.png',
            'imageType':'Texture','semantic':'effectMap','coreSemantic':'sRGB3chAlpha',
            'streamable':'0','compressionMethod':'compressed high color',
            'premulAlpha':'1','clampU':'0' if key=='wake' else '1','clampV':'1',
        }
        lines += ['\t"'+image+'" ( "image.gdf" )','\t{']
        lines += ['\t\t"'+k+'" "'+str(v)+'"' for k,v in rows.items()]
        lines += ['\t}']
        rows={
            'materialCategory':'Effect','materialType':'effect_lit_emissive_blend',
            'template':'material.template','surfaceType':'<none>','colorMap':image,
            'colorTint':'1 1 1 1','scaleRGB':str(scale),'useOldHDRScale':'0',
            'alphaRevealMap':'$white_reveal','falloff':'0','distFalloff':'0',
            'textureAtlasRowCount':'1','textureAtlasColumnCount':'1',
            'cullFace':'None','usage':'<not in editor>',
        }
        lines += ['\t"mtl_tod_sky_detail_'+key+'" ( "material.gdf" )','\t{']
        lines += ['\t\t"'+k+'" "'+str(v)+'"' for k,v in rows.items()]
        lines += ['\t}']
    return '\n'.join(lines+['}'])+'\n'

def verify(ledger=None):
    from PIL import Image
    m=json.loads((ART/'manifest.json').read_text())
    assert GDT.read_text()==gdt_text(), 'sky detail GDT differs from authored material contract'
    for image,_ in MATERIALS.values():
        p=IMAGES/(image+'.png')
        assert hashlib.sha256(p.read_bytes()).hexdigest()==m['images'][p.name], 'unreviewed image change '+image
        im=Image.open(p)
        assert im.mode=='RGBA' and min(im.size)>=256 and max(im.size)<=1024,(image,im.mode,im.size)
        a=im.getchannel('A')
        # No hard rectangle or cropped filament may ride an alpha-blended FX.
        for region in ((0,0,im.width,2),(0,im.height-2,im.width,im.height)):
            assert a.crop(region).getextrema()[1]==0,(image,'nontransparent top/bottom border')
        if image!='i_tod_sky_meteor_wake':
            for region in ((0,0,2,im.height),(im.width-2,0,im.width,im.height)):
                assert a.crop(region).getextrema()[1]==0,(image,'nontransparent side border')
        if 'void' in image:
            assert all(im.getchannel(c).getextrema()[1]==0 for c in 'RGB'),'void must be black RGB, not dark grey'
            assert a.getpixel((im.width//2,im.height//2))>245,'void centre is not opaque'
        else:
            assert a.getextrema()[1]>100 and a.getextrema()[0]==0,(image,'empty or solid texture')
        if 'rift' in image and 'void' not in image:
            c=im.width//2
            assert a.crop((c-64,c-64,c+64,c+64)).getextrema()[1]==0,'rift lost hollow negative space'
    if ledger:
        with pathlib.Path(ledger).open(encoding='utf-8-sig',newline='') as f: have={(r['type'],r['name']) for r in csv.DictReader(f)}
        for key,(image,_) in MATERIALS.items():
            assert ('image',image) in have, 'custom sky image not packed: '+image
            # Native ribbons compile as el/; camera-facing sprites use ei/.
            assert any(('material',prefix+'mtl_tod_sky_detail_'+key) in have for prefix in ('','ei/','el/','mc/','wc/')), 'custom sky material not packed: '+key
    print('SKY DETAIL OK: 4 authored textures/materials, black aperture, clear borders, no added emitter/light/host; native appearance UNPLAYED')

if __name__=='__main__':
    verify(sys.argv[sys.argv.index('--ledger')+1] if '--ledger' in sys.argv else None)
