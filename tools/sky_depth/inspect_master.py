"""Read the saved production master through Blender; do not resave or mutate it."""
import json
import pathlib
import sys
import bpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
sys.modules.pop('pass_config',None)
from pass_config import STAGE,REVIEW,sha
from quality_profile import load_quality, expected_quality, actual_quality, PROFILE_PATH
author=json.loads((STAGE/'author.json').read_text(encoding='utf-8'))
master=STAGE/'depth.blend'
assert pathlib.Path(bpy.data.filepath).resolve()==master
assert sha(master)==author['blend_sha256']
scene=bpy.context.scene
assert scene.render.engine=='CYCLES'
assert scene.camera.name.startswith('sky_cam') and scene.camera.data.type=='PANO'
assert tuple(scene.camera.location)==(0,0,220)
assert scene.world.name.startswith('sky3d_world')
assert not any(n.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} for n in scene.world.node_tree.nodes)
assert not any(o.name.startswith('Native card |') or 'native_model' in o for o in scene.objects)
gates=[o for o in scene.objects if o.name.startswith('sky3d_cyber_hero_title_authored_gate')]
assert len(gates)==1
nodes=gates[0].data.materials[0].node_tree.nodes
assert 'Dull cap scale (<= 1)' in nodes and 'Desaturate the dead sign' in nodes
assert scene.render.resolution_x==8192 and scene.render.resolution_y==4096 and scene.cycles.samples==160
assert len(bpy.data.scenes)==1, 'Authoring master must contain only its production scene'
assert author['quality_profile']==load_quality() and author['quality_profile_sha256']==sha(PROFILE_PATH)
assert actual_quality(scene)==author['render_quality']==expected_quality()
result=dict(master=str(master.relative_to(ROOT)),sha256=sha(master),scene_name=scene.name,
            scene_name_note='Fresh factory-startup master; only the production scene is retained.',
            camera=scene.camera.name,camera_type=scene.camera.data.type,camera_position=list(scene.camera.location),
            world=scene.world.name,world_has_image_nodes=False,native_preview_card_present=False,
            objects=len(scene.objects),authored_title_state='dull',title_source=gates[0]['source_image'],
            render=[8192,4096,160],render_quality=actual_quality(scene),all_scenes=[dict(name=s.name,objects=len(s.objects),
               world=s.world.name if s.world else None) for s in bpy.data.scenes],
            image_datablocks=[dict(name=i.name,filepath=i.filepath,users=i.users,has_data=i.has_data,
               packed=bool(i.packed_file)) for i in bpy.data.images if i.filepath])
(REVIEW/'master_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('DEPTH MASTER VERIFIED',json.dumps(result))
