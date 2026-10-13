"""Publish exact source/candidate evidence and supersede the initial missing-art audit."""
import json,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
DOC=ROOT/'docs/wunderfizz'
def main():
    path=DOC/'asset_inventory.json';old=json.loads(path.read_text(encoding='utf-8-sig'))
    stage=ROOT/'tmp/wunderfizz/assets/engine_kit'
    manifest=json.loads((stage/'manifest.json').read_text())
    motion=json.loads((ROOT/'tmp/wunderfizz/assets/motion_bounds.json').read_text())
    original_status={k:old.get(k) for k in ('status','machine_request','modern_model_present','missing_delivery')}
    old.update({'status':'EXACT_BO6_NATIVE_SOURCE_OBTAINED_AND_STAGED',
        'machine_request':'User explicitly selected the BO6 machine; original author-supplied BO6 port is imported without geometry/texture/label redesign.',
        'modern_model_present':True,'measured_bounds':manifest['all_lod_bounds'],
        'measured_front_axis':'+X at yaw 0; original rear tag_origin retained; native scale 1.',
        'collision_measurement':manifest['collision'],'animated_bounds':motion['all_lod_animation_bounds'],
        'missing_delivery':[],'initial_local_search_history':original_status,
        'delivery_pending':['Root coherent live landing/guarded native build.','Completed FF six full material/image-table gates and all thirteen BC7 alpha mip gates.','User visual/audio/animation playtest; no game launched.'],
        'exact_bo6_candidate':manifest,'audio_candidate':'tmp/wunderfizz/audio/candidate/manifest.json',
        'writes':'Only task-owned extraction/import staging and documentation. This agent has not changed live build inputs, private source/database/cache/deployment, or shared roots.'})
    path.write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
    for src,name in [(stage/'manifest.json','asset_manifest.json'),(ROOT/'tmp/wunderfizz/assets/source_inspection.json','source_inspection.json'),(ROOT/'tmp/wunderfizz/assets/motion_bounds.json','motion_bounds.json'),(ROOT/'tmp/wunderfizz/assets/duplicate_audit.json','duplicate_audit.json')]:shutil.copyfile(src,DOC/name)
    brief=ROOT/'docs/wunderfizz_asset_request.md';text=brief.read_text(encoding='utf-8-sig')
    text=text.replace('STATUS: exact modern model and its complete native asset set are missing locally. Gameplay and layout can be staged; no substitute machine should ship.',
        'STATUS: superseded fallback brief. The user explicitly selected BO6, and its original author-supplied BO6 native port was obtained and staged on 2026-10-07. See [wunderfizz/ASSET_IMPORT.md](wunderfizz/ASSET_IMPORT.md). No model/art request is outstanding; guarded build and user playtest are pending.')
    text=text.replace("The current request is a modern choose-perk Wunderfizz counter, pending the user's edition clarification.",
        'The selected source is the BO6 Wunderfizz machine. The extraction requirements below preserve the original request history.')
    text=text.replace('That metadata is included as reference, not delivered sound.',
        'That metadata is included as historical reference. The BO6 author package now supplies seven actual machine WAVs, original native alias rows, and the frame-1 activation note; see the audio candidate receipt.')
    text=text.replace('Confirm the source game\'s edition before extracting.','The user selected Black Ops 6.')
    brief.write_text(text,encoding='utf-8')
    print('BO6_WUNDERFIZZ_ASSET_INVENTORY_UPDATED: original model/material/clip/audio source obtained; staged checks and native/user-review limits recorded.')
if __name__=='__main__':main()
