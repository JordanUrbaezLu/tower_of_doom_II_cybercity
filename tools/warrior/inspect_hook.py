"""Read-only inspection of the left-hook source motion and conversion rig."""
import pathlib, sys, json, math
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/cyber_elites'))
from inspect_assets import asset, native_path, xmodel
from PyCoD import xanim

def inspect():
    a = xanim.Anim()
    a.LoadFile_Bin(str(ROOT / 'xanim_export/tod_warrior/vm_boxing_gloves_melee_swipe_l.XANIM_BIN'))
    print('clip', len(a.frames), 'frames', a.framerate, 'fps')
    for name in ['tag_view', 'tag_weapon', 'j_wrist_le', 'j_wrist_ri']:
        i = next((i for i,p in enumerate(a.parts) if p.name == name), None)
        if i is None: continue
        print(name, [(f, tuple(round(x, 2) for x in a.frames[f].parts[i].offset)) for f in range(0, len(a.frames), 3)])
    for name in ['wpn_t7_zmb_dlc3_gauntlet_dragon_view']:
        fields = asset('xmodel', name)
        m = xmodel.Model(); m.LoadFile_Bin(str(native_path('model_export', fields['filename'])), split_meshes=True)
        print(name, 'rig', fields['filename'], 'bones', [b.name for b in m.bones])
        for mesh in m.meshes:
            weights = {}
            for v in mesh.verts:
                for bone, weight in v.weights:
                    if weight: weights[m.bones[bone].name] = weights.get(m.bones[bone].name, 0) + 1
            print('mesh', mesh.name, 'weighted bones', weights)
    print('native left anim', json.dumps({k:v for k,v in asset('xanim', 'vm_boxing_gloves_melee_swipe_l').items() if v}))

if __name__ == '__main__': inspect()
