"""MCP: preserve the original sword in a private Cybercity authoring scene."""
import bpy, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/cyber_sword';OUT.mkdir(parents=True,exist_ok=True)
source=Path.home()/'Downloads/Hellbound_Gold_Battle_Sword/03_gold_battle_sword.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.data.scenes[0]
for win in bpy.context.window_manager.windows:win.scene=scene
objects=[]
for ob in scene.objects:
    objects.append(dict(name=ob.name,type=ob.type,collections=[c.name for c in ob.users_collection],
                        location=list(ob.location),dimensions=list(ob.dimensions),
                        materials=[m.name if m else None for m in ob.data.materials] if ob.type in ('MESH','CURVE','FONT') else []))
materials=[]
for mat in bpy.data.materials:
    p=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if mat.use_nodes else None
    if p:materials.append(dict(name=mat.name,base=list(p.inputs['Base Color'].default_value),metal=p.inputs['Metallic'].default_value,
                              rough=p.inputs['Roughness'].default_value,emission=p.inputs['Emission Strength'].default_value,
                              linked=[s.name for s in p.inputs if s.is_linked]))
(OUT/'source_inventory.json').write_text(json.dumps(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),objects=objects,materials=materials),indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'original_reference.blend'))
print('CYBER_SWORD_REFERENCE_OPEN',len(objects),'objects',len(materials),'materials',flush=True)
