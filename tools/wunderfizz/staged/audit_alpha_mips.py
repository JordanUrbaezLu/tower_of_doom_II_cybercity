"""Diagnose the actual original-glass native mip chain; no source mutation.

Records lossless source references, several standard filter candidates and
controlled corruptions so native compression can be assessed beyond a percentile
on a shrinking pixel population. Only writes task-owned diagnostic staging.
"""
import datetime,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/wunderfizz'))
from verify_compiled_assets import TOOLS,MAP,module,dependency_sections,selected_image,glass_mips,sha

def stats(actual,expected):
    a=np.asarray(actual,dtype=np.int16);e=np.asarray(expected,dtype=np.int16)
    delta=a-e;error=np.abs(delta);boundary=(e>0)&(e<255)
    return {'size':list(a.shape[::-1]),'pixel_count':a.size,'source_min':int(e.min()),'source_max':int(e.max()),
        'native_min':int(a.min()),'native_max':int(a.max()),'source_mean':float(e.mean()),'native_mean':float(a.mean()),
        'mean_signed_error':float(delta.mean()),'mean_absolute_error':float(error.mean()),
        'rms_error':float(np.sqrt(np.mean(delta.astype(float)**2))),
        'p95_absolute_error':float(np.percentile(error,95)),'p99_absolute_error':float(np.percentile(error,99)),
        'maximum_absolute_error':int(error.max()),'pixels_with_error_over12':int((error>12).sum()),
        'intermediate_alpha_pixel_count':int(boundary.sum()),
        'stable_transparent_to_opaque':int(((e<64)&(a>192)).sum()),
        'stable_opaque_to_transparent':int(((e>192)&(a<64)).sum())}

def main():
    source=ROOT/'model_export/tod2_bo6_wunderfizz/_images/t10_zm_machine_wunderfizz_glass/t10_zm_machine_wunderfizz_glass_c.png'
    deps=TOOLS/'usermaps'/MAP/'zone_source/all/assetinfo'/(MAP+'.deps')
    cache=selected_image(dependency_sections(deps),'i_t10_zm_machine_wunderfizz_glass_c')
    pins={str(p):sha(p) for p in [source,deps,cache]}
    converter=module('wunderfizz_alpha_audit_iwi','tools/crown_alarm/verify_lens_conversion.py')
    chain=glass_mips(cache,converter)
    with Image.open(source) as image:alpha=image.getchannel('A').copy();rgba=image.convert('RGBA').copy()
    rows=[];sequential=alpha
    for level,pixels in enumerate(chain):
        actual=pixels[:,:,3];size=(pixels.shape[1],pixels.shape[0]);expected=alpha.resize(size,Image.Resampling.BOX)
        if level:sequential=sequential.resize(size,Image.Resampling.BOX)
        candidates={f.name:stats(actual,np.asarray(alpha.resize(size,f))) for f in [Image.Resampling.BOX,Image.Resampling.BILINEAR,Image.Resampling.HAMMING,Image.Resampling.BICUBIC,Image.Resampling.LANCZOS]}
        candidates['SEQUENTIAL_BOX']=stats(actual,np.asarray(sequential))
        candidates['RGBA_BOX_CURRENT_GATE']=stats(actual,np.asarray(rgba.resize(size,Image.Resampling.BOX))[:,:,3])
        expected_array=np.asarray(expected)
        controls={
            'all_opaque':np.full_like(actual,255),
            'all_transparent':np.zeros_like(actual),
            'alpha_plus32':np.minimum(actual.astype(np.int16)+32,255).astype(np.uint8),
            'alpha_binary_threshold':np.where(actual>=128,255,0).astype(np.uint8),
            'alpha_spatial_shift':np.roll(actual,max(1,size[0]//8),axis=1)}
        rows.append({'level':level,'filter_candidates':candidates,
            'controlled_corruptions':{name:stats(values,expected_array) for name,values in controls.items()}})
        print('MIP',level,'BOX',candidates['BOX']['mean_absolute_error'],candidates['BOX']['p99_absolute_error'],
            'MAX',candidates['BOX']['maximum_absolute_error'],'SIGNED',candidates['BOX']['mean_signed_error'],
            'BEST',min(candidates,key=lambda key:candidates[key]['mean_absolute_error']),flush=True)
        if level in [0,5,6,7,8,9]:
            out=ROOT/'tmp/wunderfizz/assets/alpha_audit';out.mkdir(parents=True,exist_ok=True)
            Image.fromarray(actual,'L').save(out/f'native_alpha_mip{level}.png')
            expected.save(out/f'source_box_alpha_mip{level}.png')
    assert all(sha(Path(path))==pin for path,pin in pins.items())
    result={'verified_at':datetime.datetime.now().astimezone().isoformat(),'source_and_native_pins':pins,
        'compression':'BC7_SRGB','original_dimensions':[4096,4096],'mip_count':len(chain),
        'source_semantics':{'coreSemantic':'sRGB3chAlpha','mipMode':'Average','premulAlpha':'0','mipNorm':'0'},
        'mips':rows,'source_or_native_cache_mutated':False,'native_visual_verified':False,'game_launched':False}
    out=ROOT/'tmp/wunderfizz/assets/alpha_audit.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print('ALPHA_AUDIT',out)

if __name__=='__main__':main()
