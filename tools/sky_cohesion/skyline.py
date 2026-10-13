"""Conservative angular skyline from projected solid-architecture faces."""
import json
import math
import pathlib
import bpy
import numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[2]
profile = np.full(720, -90.0)
names = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH' or not (ob.name in ('city_facades','city_roofs','city_struct','city_neon','city_crystal','city_cyber_armour','city_cyber_decks') or ob.name.startswith('sky3d_cyber_title')):
        continue
    names.append(ob.name)
    xyz = np.empty(len(ob.data.vertices)*3, dtype=np.float64)
    ob.data.vertices.foreach_get('co', xyz)
    xyz = xyz.reshape(-1,3) @ np.array(ob.matrix_world)[:3,:3].T + np.array(ob.matrix_world)[:3,3]
    xyz[:,2] -= 220.0
    az = np.degrees(np.arctan2(xyz[:,0],xyz[:,1]))
    el = np.degrees(np.arctan2(xyz[:,2], np.hypot(xyz[:,0],xyz[:,1])))
    for face in ob.data.polygons:
        idx = np.array(face.vertices)
        top = float(el[idx].max())
        if top < 5:
            continue
        a = az[idx]
        if a.max()-a.min()>180:
            a = np.where(a<0,a+360,a)
        lo = math.floor((float(a.min())+180)*2)
        hi = math.ceil((float(a.max())+180)*2)
        bins = np.arange(lo,hi+1) % 720
        profile[bins] = np.maximum(profile[bins],top)
out = {'method':'conservative per-face angular bounds at 0.5 degrees; architecture, attached neon rings/crowns/crystals and title, not atmospheric volumes',
       'objects':names,'azimuth_start':-180,'step':.5,'elevation_deg':profile.tolist()}
(ROOT/'tmp/sky_cohesion/skyline.json').write_text(json.dumps(out,indent=1))
for center in (-176,-150,-137,-118,-98,-82,-60,-20,0,32,52,60,75,96,110,128,140,160,172):
    bins = [(round((center+180)*2)+k)%720 for k in range(-20,21)]
    print('SKYLINE',center,round(float(max(profile[bins])),2))
