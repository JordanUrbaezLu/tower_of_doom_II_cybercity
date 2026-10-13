"""Read the retained motion in Blender's math types; no native inputs changed."""
import bpy, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tmp/archer_assets/seanim'))
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
import seanim
from PyCoD import xmodel
hands=Path('C:/Users/jorda/Documents/BO3_tools/Greyhound/exported_files/black_ops_3/xmodels/c_zom_der_dempsey_viewhands/c_zom_der_dempsey_viewhands_LOD0.XMODEL_BIN')
m=xmodel.Model();m.LoadFile_Bin(str(hands));a=seanim.Anim(str(hands.parents[2]/'xanims/vm_hatchet_throw.seanim'))
def mat(b):
    r=Matrix(b.matrix).transposed().to_4x4();r.translation=b.offset;return r
bind=[mat(b) for b in m.bones]
local=[bind[b.parent].inverted()@bind[i] if b.parent>=0 else bind[i] for i,b in enumerate(m.bones)]
def value(keys,f,quat=False):
    if not keys:return None
    k0=next((k for k in reversed(keys) if k.frame<=f),keys[0]);k1=next((k for k in keys if k.frame>=f),keys[-1])
    t=0 if k1.frame==k0.frame else (f-k0.frame)/(k1.frame-k0.frame)
    if quat:
        q=lambda k:Quaternion((k.data[3],*k.data[:3])).normalized()
        return q(k0).slerp(q(k1),t)
    return Vector(k0.data).lerp(Vector(k1.data),t)/2.54
for f in (0,2,4,6,8,10,14,20):
    world=[];lookup={b.name:b for b in a.bones}
    for i,b in enumerate(m.bones):
        l=local[i].copy();sb=lookup.get(b.name)
        if sb:
            p=value(sb.posKeys,f);q=value(sb.rotKeys,f,True)
            if q:l=q.to_matrix().to_4x4();l.translation=local[i].translation
            if p is not None:l.translation=p
        world.append(world[b.parent]@l if b.parent>=0 else l)
    print(f,{name:tuple(round(x,2) for x in world[next(i for i,b in enumerate(m.bones) if b.name==name)].translation) for name in ('j_shoulder_le','j_elbow_le','j_wrist_le','tag_weapon_right')})
