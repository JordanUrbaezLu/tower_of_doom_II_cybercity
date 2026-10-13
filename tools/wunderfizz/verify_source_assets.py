"""Check installed/staged exact BO6 assets against persistent source provenance.

All imported native payloads must match the author's source hashes. The original
GDT's thirty typed definitions may differ only by the explicitly recorded native
path, full-mip-base and glass alpha-compatible compression retargets. No tool or
game is launched. Writes one source-check receipt in art/wunderfizz.
"""
import argparse,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/wunderfizz/staged'))
from stage_bo6_machine import definitions,sha,STAGE
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',action='store_true');args=parser.parse_args()
    source=STAGE if args.stage else ROOT
    art=ROOT/'art/wunderfizz';manifest_path=art/'asset_manifest.json';m=json.loads(manifest_path.read_text())
    checked=[]
    for row in m['files']:
        p=source/row['file'];assert p.is_file() and sha(p)==row['sha256'],('Missing or changed exact source payload',row['file'])
        checked.append({'file':row['file'],'bytes':p.stat().st_size,'sha256':row['sha256'],'original_payload_preserved':row['original_payload_preserved']})
    original=art/'source/t10_zm_machine_wunderfizz_fxanim.original.gdt';assert sha(original)==m['source_gdt_sha256']
    orig={(kind,name):fields for name,kind,fields,block in definitions(original.read_text())}
    installed={(kind,name):fields for name,kind,fields,block in definitions((source/'source_data/tod2_bo6_wunderfizz.gdt').read_text())}
    assert installed.keys()==orig.keys() and len(installed)==30,'A complete typed source asset definition was lost or replaced'
    for name,fields in orig.items():
        expected=dict(fields)
        for change in m['native_definition_changes']:
            if name==(change['kind'],change['asset']):
                assert expected[change['field']]==change['before'];expected[change['field']]=change['after']
        assert installed[name]==expected,('Unrecorded native material/animation/model definition change',name)
    assert m['original_geometry_texture_labels_colors_uvs_rig_lods_animation_fx_preserved']
    out=art/('staged_source_validation.json' if args.stage else 'source_validation.json')
    out.write_text(json.dumps({'source_root':str(source),'manifest_sha256':sha(manifest_path),'original_gdt_sha256':sha(original),'files':checked,'typed_definition_count':30,'original_material_values_and_native_payloads_preserved':True,'changes_are_exactly_recorded':True,'native_compiled_verified':False,'native_playtested':False,'game_launched':False},indent=2)+'\n')
    print('BO6_WUNDERFIZZ_SOURCE_OK: persistent provenance, all forty payloads, original labels/material values/rig/UV/LODs, exact native path/mip/alpha compatibility changes.')
if __name__=='__main__':main()
