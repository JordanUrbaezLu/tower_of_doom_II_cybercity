"""Read-only source/native registration proof for the independently authored gun clips."""
import argparse
import hashlib
import json
import pathlib
import sys

REPO=pathlib.Path(__file__).resolve().parents[2]


def check(root):
    man=json.loads((root/'xanim_export/tod_dealer/combat_clips.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for rel,want in man['inputs'].items():
        assert sha(REPO/rel)==want, 'Changed gun clip source: '+rel
    sys.path.insert(0,str(pathlib.Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
    from PyCoD import xanim
    skeleton=json.loads((REPO/'art/dealer_boss/skeleton.json').read_text())
    bones={b['name'] for b in skeleton['bones']}
    gdt=(root/'source_data/tod_dealer_combat.gdt').read_text()
    for kind,frames,lift in [('shock',78,14),('burst',105,0)]:
        name='tod_dealer_c_'+kind
        entry=man['clips'][name]
        path=root/entry['file']
        assert sha(path)==entry['sha256'],name+' binary pin'
        assert entry['hand_gap_max']<.05 and entry['lift']==lift,name+' hand/stance'
        a=xanim.Anim();a.LoadFile_Bin(str(path))
        assert len(a.frames)==frames and a.framerate==30 and not a.notes,name+' frames/notes'
        assert {p.name for p in a.parts}==bones,name+' full native skeleton'
        assert '"'+name+'" ( "xanim.gdf" )' in gdt,name+' native GDT'
        assert '"filename" "tod_dealer\\\\'+name+'.xanim_bin"' in gdt,name+' native filename'
    preview=REPO/'art/dealer_combat/review/review.json'
    review=json.loads(preview.read_text())
    for item in review['poses'].values():
        assert item['clip_sha256']==man['clips'][item['clip']]['sha256'],'preview uses stale clip'
    print('DEALER COMBAT ASSETS OK: two full-skeleton clips, no melee notes, source/binary/preview pins and native GDT')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=pathlib.Path,default=REPO)
    check(ap.parse_args().root)
