"""Native surface regression gate: mapped wear must survive export on every model family.

Rejects the actual previously flat cargo cards and light-hull/dark-hull gloss mismatch.
This checks data and bindings, not artistic quality or native visual approval.
"""
import json, pathlib, re
import numpy as np
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parents[2]


def verify():
    text = (ROOT/'source_data/tod_sky_ships.gdt').read_text()
    blocks={name:dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',body))
            for name,body in re.findall(r'"([^"\n]+)" \( "material.gdf" \)\s*\{(.*?)\n\t\}',text,re.S)}
    expected={'hull':('plate',0), 'hull2':('plate2',0), 'drive_metal':('drive',0), 'rock':('rock',.6), 'rock2':('rock',.6)}
    expected.update({name:('cargo',3.5) for name in ('cargo_orange','cargo_teal','cargo_red','cargo_white','cargo_yellow')})
    expected.update({'mineral_'+c:('mineral',48) for c in ('magenta','cyan','amber')})
    stats={}
    for label,(family,emit) in expected.items():
        f=blocks['mtl_tod_sky_'+label]
        assert float(f['scaleRGB'])==emit,(label,'accepted glow strength changed')
        for field,suffix in [('normalMap','n'),('cosinePowerMap','g'),('specColorMap','s')]:
            want='i_tod_sky_'+family+'_'+suffix
            assert f[field]==want,(label,field,f[field],want)
        for field in ('colorMap','normalMap','cosinePowerMap','specColorMap'):
            name=f[field]
            if name in stats:continue
            arr=np.array(Image.open(ROOT/'model_export/tod_sky_ships/_images'/(name+'.png')).convert('RGB'))
            assert min(arr.shape[:2])>=1024,(name,'surface map replaced with flat swatch')
            spread=float(np.std(arr.astype(np.float64),axis=(0,1)).max())
            assert spread>1,(name,'flat surface channel',spread)
            stats[name]={'width':arr.shape[1],'height':arr.shape[0],'max_channel_std':round(spread,4)}
    manifest=json.loads((ROOT/'art/sky_ships/manifest.json').read_text())
    for ship in manifest['ships']:
        assert {'mtl_tod_sky_hull','mtl_tod_sky_hull2'} <= set(ship['materials']),ship['ship']
        assert 'mtl_tod_sky_drive_metal' in ship['materials'],(ship['ship'],'engine collars lack authored finish')
    for rock in manifest['rocks']:
        assert {'mtl_tod_sky_rock','mtl_tod_sky_rock2'} & set(rock['materials']),rock['rock']
    report={'models':sum(len(r['models']) for r in manifest['ships']+manifest['rocks']),
            'material_families':len(expected),'maps':stats,'native_visual_approval':False}
    (ROOT/'art/sky_ships/surface_validation.json').write_text(json.dumps(report,indent=2))
    print('SKY SURFACES OK',report['models'],'models;',len(stats),'nonflat maps; native material bindings and glow retained')
    return report


if __name__=='__main__':verify()
