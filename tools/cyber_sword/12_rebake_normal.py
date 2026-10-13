"""Repair-only normal rebake: geometry, UVs and the other four channels match."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/cyber_sword';IMG=ROOT/'model_export/tod_warrior/cyber_sword/_images'
bpy.ops.wm.open_mainfile(filepath=str(ART/'native_bake.blend'))
scene=bpy.context.scene;ob=scene.objects[scene['native_kit_object']]
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
image=bpy.data.images.new('i_tod_cyber_sword_n',width=4096,height=4096,alpha=False);image.colorspace_settings.name='Non-Color'
for mat in ob.data.materials:
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node
bpy.ops.object.bake(type='NORMAL',normal_space='TANGENT')
image.filepath_raw=str(IMG/'i_tod_cyber_sword_n.png');image.file_format='PNG';image.save()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'native_baked.blend'))
p=ART/'engine_kit/source_manifest.json';manifest=json.loads(p.read_text());manifest['textures'][Path(image.filepath_raw).name]=hashlib.sha256(Path(image.filepath_raw).read_bytes()).hexdigest();p.write_text(json.dumps(manifest,indent=2))
print('CYBER_SWORD_NORMAL_REBAKE_DONE',flush=True)
