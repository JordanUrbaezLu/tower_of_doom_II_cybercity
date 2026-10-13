"""Measure original weighted vertices throughout the original BO6 activation clip.

XMODEL/XANIM store evaluated world-space bone matrices (rows represent axes).
Each original vertex is transformed by animation_world * inverse(bind_world),
then original skin weights are applied. No source binary or texture is changed.
"""
from pathlib import Path
import json,sys
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel,xanim
MACHINE=ROOT/'tmp/wunderfizz/assets/source/_custom/_wetegg/models/t10/t10_zm_machine_wunderfizz_fxanim'
def matrix(part):
    m=np.eye(4);m[:3,:3]=np.asarray(part.matrix).T;m[:3,3]=part.offset
    return m
def main():
    anim=xanim.Anim();anim.LoadFile_Bin(str(next((MACHINE/'xanims').glob('*'))))
    parts={part.name:i for i,part in enumerate(anim.parts)}
    rows=[]
    for file in sorted((MACHINE/'xmodels').glob('*')):
        model=xmodel.Model();model.LoadFile_Bin(str(file),split_meshes=True)
        verts=[v for mesh in model.meshes for v in mesh.verts]
        points=np.asarray([v.offset for v in verts]);ones=np.ones((len(points),1));hom=np.hstack((points,ones))
        groups=[]
        total_weight=np.zeros(len(points))
        for index,bone in enumerate(model.bones):
            pairs=[(j,weight) for j,v in enumerate(verts) for b,weight in v.weights if b==index and weight]
            if not pairs:continue
            indices=np.array([p[0] for p in pairs]);weights=np.array([p[1] for p in pairs])
            total_weight[indices]+=weights
            local=hom[indices]@np.linalg.inv(matrix(bone)).T
            groups.append((parts[bone.name],indices,weights,local))
        assert np.max(np.abs(total_weight-1))<1e-4
        bounds_min=np.full(3,np.inf);bounds_max=np.full(3,-np.inf)
        peak_frames={};frame0_error=None
        for frame in anim.frames:
            posed=np.zeros_like(points)
            for partid,indices,weights,local in groups:
                posed[indices]+=(local@matrix(frame.parts[partid]).T)[:,:3]*weights[:,None]
            assert np.isfinite(posed).all()
            lo=posed.min(axis=0);hi=posed.max(axis=0)
            for axis in range(3):
                if lo[axis]<bounds_min[axis]:peak_frames['min_'+str(axis)]=frame.frame
                if hi[axis]>bounds_max[axis]:peak_frames['max_'+str(axis)]=frame.frame
            bounds_min=np.minimum(bounds_min,lo);bounds_max=np.maximum(bounds_max,hi)
            if frame.frame==anim.frames[0].frame:frame0_error=float(np.max(np.abs(posed-points)))
        rows.append({'file':file.name,'bounds':[[float(bounds_min[j]),float(bounds_max[j])] for j in range(3)],'extreme_frames':peak_frames,'first_frame_max_position_difference_from_bind':frame0_error})
    union=[[min(r['bounds'][j][0] for r in rows),max(r['bounds'][j][1] for r in rows)] for j in range(3)]
    result={'method':'Weighted animation_world * inverse(bind_world) using original binary world axes transposed to column transforms.',
        'animation_frames':len(anim.frames),'animation_fps':anim.framerate,'models':rows,'all_lod_animation_bounds':union,
        'native_playtested':False,'source_unchanged':True}
    out=ROOT/'tmp/wunderfizz/assets/motion_bounds.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'receipt':str(out),'all_lod_animation_bounds':union,'lod0':[r for r in rows if 'LOD0.' in r['file']]},indent=2))
if __name__=='__main__':main()
