import bpy,json
from mathutils import Vector
from pathlib import Path
rows=[]
for ob in bpy.context.scene.objects:
    if ob.type not in ('MESH','CURVE','FONT'):continue
    if not any(c.name.startswith(('01','02','03','04')) for c in ob.users_collection):continue
    points=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    rows.append(dict(name=ob.name,lo=[min(p[i] for p in points) for i in range(3)],hi=[max(p[i] for p in points) for i in range(3)]))
out=Path(__file__).resolve().parents[2]/'art/cyber_sword/source_bounds.json'
out.write_text(json.dumps(rows,indent=2))
for r in rows:
    if r['name'].startswith(('Blade ','Guard ','Gem ','Grip ','Pommel ','Chinese')):print(json.dumps(r))
