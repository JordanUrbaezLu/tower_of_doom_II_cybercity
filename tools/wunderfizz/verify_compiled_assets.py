"""Verify exact imported BO6 machine in the completed private native build.

Requires source/deployment parity, both seven-LOD model tables, six complete
actual FF material definitions and native image tables, exact dependency bindings,
the original activation note payloads and dependency-selected lossless glass alpha
across all thirteen mips. A name in an asset ledger alone is insufficient.
Only writes a receipt in this repository; never launches a game/native tool.
"""
from __future__ import annotations
import argparse,csv,datetime,importlib.util,json,math,re,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
TOOLS=Path('C:/BO3Tools/TOD2Cybercity')
MAP='zm_tod2_cybercity'
sys.path.insert(0,str(ROOT/'tools/wunderfizz/staged'))
from stage_bo6_machine import sha,definitions,OFF,ON,ACTIVATE

def module(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def dependency_sections(path):
    sections={};active=None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line and not line[0].isspace():
            parts=line.split(',');active=tuple(parts[:2]);sections.setdefault(active,[])
        elif active:sections[active].append(line.strip())
    return sections

def selected_image(sections,name):
    paths=[Path(row.split(',')[1]).resolve() for row in sections.get(('image',name),[]) if row.startswith('file,') and row.split(',')[1].lower().endswith('.iwi')]
    assert len(paths)==1,('Image has no unique completed native conversion',name,paths)
    assert paths[0].is_relative_to((TOOLS/'share/assetconvert/image/v29').resolve()) and paths[0].is_file(),name
    return paths[0]

def glass_mip_layout(raw):
    # Existing dependency-selected uncompressed sRGB3chAlpha controls prove
    # IWi v29 format 14 is raw RGBA8 (not BGRA). Native offset entries point
    # to each mip's exclusive end; complete chains run smallest to largest.
    assert len(raw)>=96 and raw[:4]==b'IWi\x1d' and raw[4]==14,'Glass must compile with lossless RGBA8 sRGB alpha'
    count=raw[5];width,height,depth=struct.unpack_from('<3H',raw,10)
    assert (width,height,depth)==(4096,4096,1),'Original full-resolution glass mip base was lost'
    assert count==13,'Original glass must retain all thirteen mips'
    end=len(raw);layout=[]
    for level in range(count):
        w,h=max(1,width>>level),max(1,height>>level);size=w*h*4;start=end-size
        assert start>=96,'Truncated glass mip payload'
        if level<8:assert struct.unpack_from('<I',raw,64+4*level)[0]==end,'Native mip offset table mismatch'
        layout.append({'level':level,'size':[w,h],'payload_start':start,'payload_end':end,'payload_bytes':size});end=start
    assert end==96,'Unexpected native mip-chain layout'
    return layout

def glass_mips(cache,converter):
    raw=converter.decode_lz4(cache.read_bytes())
    layout=glass_mip_layout(raw)
    mips=[]
    for row in layout:
        w,h=row['size'];pixels=np.frombuffer(raw,dtype=np.uint8,count=row['payload_bytes'],offset=row['payload_start']).reshape(h,w,4)
        mips.append(pixels)
    return mips

def verify_glass_alpha(mips,source):
    # Alpha is a linear scalar; resize that channel directly so no RGB
    # premultiplication or color-space operation can alter the reference.
    assert source.mode=='RGBA' and source.size==(4096,4096),'Original full-resolution explicit RGBA glass required'
    alpha=source.getchannel('A');original_alpha=np.asarray(alpha)
    assert int(original_alpha.min())<64 and int(original_alpha.max())==255,'Original translucent/opaque glass regions were lost'
    assert len(mips)==13,'Original glass must retain all thirteen mips'
    mip_rows=[]
    for level,pixels in enumerate(mips):
        size=(max(1,4096>>level),max(1,4096>>level))
        assert pixels.dtype==np.uint8 and pixels.shape==(size[1],size[0],4),('Glass mip dimensions/channel layout changed',level)
        expected=np.asarray(alpha.resize(size,Image.Resampling.BOX))
        error=np.abs(pixels[:,:,3].astype(np.int16)-expected.astype(np.int16))
        # Preserve both existing limits, including coarse 2x2/1x1 mips.
        # The lossless base RGBA must also be byte-exact. Actual native Average
        # mips are proven within one byte; a full-sheet percentile must not
        # hide a locally corrupt texel, so cap every error at that bound.
        mean=float(error.mean());p99=float(np.percentile(error,99));maximum=int(error.max())
        assert mean<=2 and p99<=12,('Compiled original alpha diverged',level,mean,p99)
        assert maximum<=1,('Compiled glass has locally corrupted alpha',level,maximum)
        if level==0:
            assert np.array_equal(pixels,np.asarray(source)),'Lossless base glass RGBA must match source byte for byte'
            assert int(pixels[:,:,3].min())<64 and int(pixels[:,:,3].max())>240,'Native image lost original translucent/opaque regions'
        mip_rows.append({'level':level,'size':list(size),'alpha_min':int(pixels[:,:,3].min()),'alpha_max':int(pixels[:,:,3].max()),'mean_alpha_error':mean,'p99_alpha_error':p99,'maximum_alpha_error':maximum})
    return mip_rows

def main():
    owned_ff=TOOLS/'usermaps'/MAP/'zone'/(MAP+'.ff')
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=ROOT/'art/wunderfizz/asset_manifest.json');p.add_argument('--output',type=Path,default=ROOT/'art/wunderfizz/compiled_assets.json');p.add_argument('--ff',type=Path,default=owned_ff);args=p.parse_args()
    manifest=json.loads(args.manifest.read_text());out=args.output.resolve();assert out.is_relative_to(ROOT)
    ff=args.ff.resolve();assert ff==owned_ff.resolve(),'Native gate accepts only this map\'s owned private fastfile'
    ledger=TOOLS/'usermaps'/MAP/'zone_source/all/assetinfo'/(MAP+'_xmodel.csv')
    assets=ledger.with_name(MAP+'.csv');deps=ledger.with_name(MAP+'.deps')
    assert all(p.is_file() for p in (ff,ledger,assets,deps)),'Completed native outputs required'
    pins={str(p):sha(p) for p in (ff,ledger,assets,deps)}
    inputs=[]
    for row in manifest['files']:
        source=ROOT/row['file']
        deployed=TOOLS/'usermaps'/MAP/row['file'] if row['file'].startswith('zone_source/') else TOOLS/row['file']
        assert source.is_file() and deployed.is_file(),row['file']
        assert sha(source)==sha(deployed)==row['sha256'],('Source/deployment differs from original candidate',row['file'])
        assert ff.stat().st_mtime>=max(source.stat().st_mtime,deployed.stat().st_mtime),('FF predates exact machine',row['file'])
        inputs.append({'file':row['file'],'sha256':row['sha256'],'bytes':source.stat().st_size})
    defs={(kind,name):fields for name,kind,fields,block in definitions((ROOT/'source_data/tod2_bo6_wunderfizz.gdt').read_text())}
    sections=dependency_sections(deps)
    with ledger.open(encoding='utf-8-sig',newline='') as f:models={r['name']:r for r in csv.DictReader(f)}
    source_inventory=json.loads((ROOT/'art/wunderfizz/source_inspection.json').read_text())
    lods=[]
    for name in (OFF,ON):
        row=models[name];assert int(row['lodCount'])==7,(name,'missing native LODs')
        for m in source_inventory['models']:
            filename=Path(m['file']).name
            stem=filename.rsplit('_LOD',1)[0]
            if stem!=name:continue
            lod=int(filename.rsplit('_LOD',1)[1].split('.')[0]);count=int(row['tris'+str(6-lod)])
            assert count==m['triangles'],(name,lod,'native triangle count changed',count,m['triangles'])
            lods.append({'model':name,'lod':lod,'triangles':count})
    with assets.open(encoding='utf-8-sig',newline='') as f:asset_rows={(r['type'],r['name']) for r in csv.DictReader(f)}
    for kind,name in [('xanim',ACTIVATE),('scriptbundle',ACTIVATE),('fx','_t10/vending/fizz_idle'),('fx','_t10/vending/fizz_activated')]:assert (kind,name) in asset_rows,(kind,name)
    native=module('wunderfizz_ff_reader','tools/crown_alarm/verify_lens_material.py')
    # The Plus transparent shaders have no full-colour specular-map slot. This
    # bounded table reader therefore requires the three common colour/nml/gloss
    # semantics; exact AO/emission/fullspec identities are checked via .deps.
    native.SEMANTICS={0xA0AB1041:'colorMap',0x59D30D0F:'normalMap',0x6D0A6C98:'glossMap'}
    names=['mc/'+name for kind,name in defs if kind=='material']
    records,total=native.material_records(ff,names+['mc/mtl_tod_alarm_cast'])
    assert any(r['name']=='mc/mtl_tod_alarm_cast' and r['classification']=='complete material definition' for r in records),'Native material layout control missing'
    materials=[]
    for name in names:
        full=[r for r in records if r['name']==name and r['classification']=='complete material definition']
        assert len(full)==1,('Missing complete native machine material/texture table',name)
        fields=defs['material',name[3:]];rows=sections.get(('material',name),[])
        binding_assets=[r.split(',')[1:3] for r in rows if r.startswith('asset,')]
        # Match this source port's actual native shader texture declarations.
        # Plus uses BASE_SPEC with no specColorMap image; Fullspec explicitly
        # binds the supplied colour specular image. The Plus tint mask is a
        # legitimate scalar stock image and must survive native linking too.
        texture_fields=['colorMap','normalMap','cosinePowerMap','occMap']
        if fields['materialType']=='lit_advanced_fullspec':texture_fields.append('specColorMap')
        elif fields['materialType']=='lit_transparent_plus':texture_fields.append('colorMap00')
        elif fields['materialType']=='lit_emissive_scroll_transparent_plus':texture_fields.extend(['colorMap00','colorMap01'])
        else:raise AssertionError(('Unexpected source shader',name,fields['materialType']))
        expected={fields[key] for key in texture_fields}
        assert all(['image',image] in binding_assets for image in expected),('Missing actual native image binding',name,expected,binding_assets)
        assert any(kind=='techset' and tech.startswith('mc/'+fields['materialType']+'#') for kind,tech in binding_assets),('Incorrect actual native shader',name)
        materials.append({'material':name,'source_type':fields['materialType'],'expected_shader_texture_fields':texture_fields,'expected_images':sorted(expected),'dependency_bindings':binding_assets,'complete_ff_record':full[0]})
    # Require actual compiled note/action strings in the completed xanim-selected
    # cache, not only the source GDT's intended frame positions.
    anim_files=[Path(r.split(',')[1]) for r in sections.get(('xanim',ACTIVATE),[]) if r.startswith('file,') and 'assetconvert' in r.split(',')[1].lower()]
    assert anim_files,'No completed activation animation conversion selected'
    payload=b''.join(path.read_bytes() for path in anim_files if path.is_file())
    assert b'evt_wunderfizz_activate' in payload and b'sphere_jnt' in payload,'Original activation sound note did not survive native conversion'
    assert b'fizz_activated' in payload and b'body_jnt' in payload,'Original activation FX note did not survive native conversion'
    converter=module('wunderfizz_iwi_reader','tools/crown_alarm/verify_lens_conversion.py')
    asset='i_t10_zm_machine_wunderfizz_glass_c';cache=selected_image(sections,asset);cache_pin=sha(cache)
    assert defs['image',asset]['compressionMethod']=='uncompressed' and defs['image',asset]['coreSemantic']=='sRGB3chAlpha','Glass source must select lossless sRGB RGBA conversion'
    mips=glass_mips(cache,converter)
    with Image.open(ROOT/defs['image',asset]['baseImage']) as source:mip_rows=verify_glass_alpha(mips,source)
    assert sha(cache)==cache_pin
    for path,pin in pins.items():assert sha(Path(path))==pin,'Native outputs changed during audit'
    result={'verified_at':datetime.datetime.now().astimezone().isoformat(),'source_candidate_manifest':str(args.manifest),'source_candidate_manifest_sha256':sha(args.manifest),'source_deployment':inputs,'native_outputs_sha256':pins,'native_model_lods':lods,'complete_ff_materials':materials,'decompressed_ff_size':total,
        'glass_alpha':{'asset':asset,'selected_cache':str(cache),'sha256':cache_pin,'compression':'uncompressed RGBA8 sRGB alpha-capable','native_iwi_format':14,'channel_order':'RGBA','base_alpha_byte_exact':True,'base_rgba_byte_exact':True,'maximum_alpha_error_limit':1,'mean_alpha_error_limit':2,'p99_alpha_error_limit':12,'mips':mip_rows},
        'compiled_animation_sound_and_fx_payload_present':True,'complete_native_material_definitions_and_texture_tables_verified':True,
        'compiled_constant_buffers_reflected':False,'material_relocation_targets_resolved':False,
        'binding_identity_evidence':'Actual FF headers/image-table structure plus fresh completed native material dependency bindings; constant buffers and relocation targets are not decoded.',
        'native_visual_verified':False,'native_playtested':False,'game_launched':False}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print('BO6_WUNDERFIZZ_COMPILED_OK: original fourteen LODs, six complete FF materials/image tables, original native activation sound/FX notes and all thirteen alpha-preserving glass mips; user visual playtest pending.')
if __name__=='__main__':main()
