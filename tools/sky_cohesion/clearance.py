"""Measure celestial geometry against the conservative architecture skyline.

Evaluate raising each world (including rings/moons), keeping azimuth fixed.
Does not mutate the scene. This is geometric composition evidence, not runtime.
"""
import ast
import json
import math
import pathlib
import bpy
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
tree=ast.parse((ROOT/'tools/sky3d/build_city.py').read_text(encoding='utf8'))
def literal(n):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict':
        return {k.arg:literal(k.value) for k in n.keywords}
    if isinstance(n,(ast.List,ast.Tuple)):
        return [literal(v) for v in n.elts]
    return ast.literal_eval(n)
bodies=next(literal(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BODIES' for t in n.targets))
moon=next(literal(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MOON_DISC' for t in n.targets))
bodies.append(dict(kind='moon',name='primary',**moon))
prof=np.array(json.loads((ROOT/'tmp/sky_cohesion/skyline.json').read_text())['elevation_deg'])
eye=np.array([0,0,220.])
def basis(az,el):
    a,e=np.radians([az,el]); s,c=math.sin,math.cos
    return np.array([[c(a),-s(a)*s(e),s(a)*c(e)],[-s(a),-c(a)*s(e),c(a)*c(e)],[0,c(e),s(e)]])
out=[]
for b in bodies:
    if b['kind'] not in ('gas','cracked','moon'):continue
    names=[b['kind']+'_'+b['name'],'ring_'+b['name']]+['moon_'+b['name']+'_m'+str(i) for i in range(len(b.get('moons',[])))]
    if b['name']=='primary': names=['moon']
    pts=[]
    for name in names:
        ob=bpy.data.objects.get(name)
        if not ob:continue
        xyz=np.empty(len(ob.data.vertices)*3)
        ob.data.vertices.foreach_get('co',xyz)
        mat=np.array(ob.matrix_world)
        pts.append(xyz.reshape(-1,3)@mat[:3,:3].T+mat[:3,3]-eye)
    xyz=np.concatenate(pts)
    local=xyz@basis(b['az'],b['el'])
    def measure(el):
        q=local@basis(b['az'],el).T
        az=np.degrees(np.arctan2(q[:,0],q[:,1])); elev=np.degrees(np.arctan2(q[:,2],np.hypot(q[:,0],q[:,1])))
        idx=np.floor((az+180)*2).astype(int)%720
        return float(np.min(elev-prof[idx])),float(elev.min())
    old,bottom=measure(b['el']); target=b['el']; margin=old
    while margin<3.0 and target<79:
        target+=1; margin,bottom=measure(target)
    rec=dict(name=b['name'],az=b['az'],old_el=b['el'],suggested_el=target,old_min_clearance=round(old,2),new_min_clearance=round(margin,2),new_lowest_el=round(bottom,2))
    out.append(rec);print('CLEARANCE',json.dumps(rec))
(ROOT/'tmp/sky_cohesion/clearance.json').write_text(json.dumps(out,indent=2))
