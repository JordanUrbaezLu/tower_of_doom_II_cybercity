"""Locate one already-built native uncompressed RGBA control read-only."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/wunderfizz'))
from verify_compiled_assets import TOOLS,MAP,module,dependency_sections,selected_image,definitions,sha
converter=module('wf_uncompressed_control_reader','tools/crown_alarm/verify_lens_conversion.py')
deps=TOOLS/'usermaps'/MAP/'zone_source/all/assetinfo'/(MAP+'.deps')
sections=dependency_sections(deps);rows=[]
for gdt in sorted((ROOT/'source_data').glob('*.gdt')):
    for name,kind,fields,block in definitions(gdt.read_text(encoding='utf-8-sig',errors='replace')):
        if kind!='image' or fields.get('compressionMethod')!='uncompressed' or fields.get('coreSemantic')!='sRGB3chAlpha':continue
        if ('image',name) not in sections:continue
        try:cache=selected_image(sections,name)
        except AssertionError:continue
        raw=converter.decode_lz4(cache.read_bytes())
        rows.append({'name':name,'gdt':gdt.relative_to(ROOT).as_posix(),'fields':fields,'cache':str(cache),
            'source_sha256':sha(ROOT/fields['baseImage']),'cache_sha256':sha(cache),
            'header_hex':raw[:96].hex(),'decompressed_bytes':len(raw),'format_id':raw[4],'mip_count':raw[5]})
        print(name,'FORMAT',raw[4],'MIPS',raw[5],'BYTES',len(raw),flush=True)
        if len(rows)>=4:break
    if len(rows)>=4:break
out=ROOT/'tmp/wunderfizz/assets/uncompressed_controls.json';out.write_text(json.dumps(rows,indent=2)+'\n');print(out)
