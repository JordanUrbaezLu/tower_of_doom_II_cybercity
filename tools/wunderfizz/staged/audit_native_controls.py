"""Read existing owned native materials to audit the bounded FF gate's reader.

This is a reader control, never proof that the staged BO6 machine was built.
Source/deployment inputs and caches are not changed and no tool/game launches.
"""
import datetime,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/wunderfizz'))
from verify_compiled_assets import TOOLS,MAP,sha,module,dependency_sections

def main():
    ff=TOOLS/'usermaps'/MAP/'zone'/(MAP+'.ff')
    deps=TOOLS/'usermaps'/MAP/'zone_source/all/assetinfo'/(MAP+'.deps')
    pins={str(p):sha(p) for p in (ff,deps)}
    sections=dependency_sections(deps)
    types=['lit_advanced_fullspec','lit_transparent_plus','lit_emissive_scroll_transparent_plus']
    picked={}
    for (kind,name),rows in sections.items():
        if kind!='material' or not name.startswith('mc/'):continue
        for material_type in types:
            if material_type not in picked and any(r.startswith('asset,techset,mc/'+material_type+'#') for r in rows):
                picked[material_type]=name
    names=list(picked.values())+['mc/mtl_tod_alarm_cast']
    reader=module('wunderfizz_control_ff_reader','tools/crown_alarm/verify_lens_material.py')
    reader.SEMANTICS={0xA0AB1041:'colorMap',0x59D30D0F:'normalMap',0x6D0A6C98:'glossMap'}
    records,total=reader.material_records(ff,names)
    controls=[]
    for name in names:
        complete=[r for r in records if r['name']==name and r['classification']=='complete material definition']
        assert len(complete)==1,('Control did not match complete native material layout',name,[(r['classification'],r['image_count']) for r in records if r['name']==name])
        controls.append({'material':name,'native_image_count':complete[0]['image_count'],
            'native_image_table_entries':complete[0]['image_table_entries'],
            'complete_native_material_definition':True,
            'dependency_images':[r.split(',')[2] for r in sections.get(('material',name),[]) if r.startswith('asset,image,')]})
    assert all(sha(Path(path))==pin for path,pin in pins.items()),'Native outputs changed during control audit'
    out=ROOT/'art/wunderfizz/native_control_audit.json'
    out.write_text(json.dumps({'verified_at':datetime.datetime.now().astimezone().isoformat(),
        'native_output_pins':pins,'decompressed_bytes':total,'controls':controls,
        'available_shader_controls':picked,'shader_types_without_current_control':[t for t in types if t not in picked],
        'proof':'Current owned FF control materials validate the structural reader/common colour, normal and gloss semantics only. The exact BO6 source still requires its own completed post-link gate.',
        'bo6_machine_compiled_verified':False,'native_visual_verified':False,'game_launched':False},indent=2)+'\n')
    print('BO6_WUNDERFIZZ_NATIVE_CONTROL_OK',[(r['material'],r['native_image_count']) for r in controls])

if __name__=='__main__':main()
