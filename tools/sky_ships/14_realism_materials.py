"""Refresh the existing fleet master through real MCP after make_textures.py.

No geometry, bone, light, scale, lane, animation, or peak emission changes.
Adds missing UVs only to the two existing vein/crystal meshes.
06_export.py then captures the new actual native bindings and image hashes.
"""
import bpy, pathlib, sys, importlib, json
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/sky_ships'))
job_path=ROOT/'tmp/sky_realism/author_job.json'
job=json.loads(job_path.read_text()) if job_path.exists() else {}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/job.get('source_blend','art/sky_ships/sky_fleet.blend')))
import sky_lib
importlib.reload(sky_lib)
sky_lib.TEX=ROOT/job.get('images','model_export/tod_sky_ships/_images')
from sky_lib import load_image, make_material, EMIT, CARGO
for p in sorted(sky_lib.TEX.glob('*.png')):
    load_image(p.stem)
for label, prefix, rough in [('hull','plate',.45), ('hull2','plate2',.4)]:
    make_material(label, load_image('i_tod_sky_'+prefix+'_c'), 'hull', rough=rough, metal=.85,
                  maps={ch:'i_tod_sky_'+prefix+'_'+ch for ch in ('n','g','s')}, surface='metal')
for label, rgb in CARGO.items():
    make_material(label, load_image('i_tod_sky_'+label), 'glow', emit=EMIT['container'], rough=.5,
                  maps={ch:'i_tod_sky_cargo_'+ch for ch in ('n','g','s')}, viewport_rgb=rgb,
                  surface='metal')
for label, rgb in [('rock',(.1,.095,.09)), ('rock2',(.13,.1,.075))]:
    make_material(label, load_image('i_tod_sky_'+label+'_c'), 'rock', emit=EMIT['rock'], rough=.85,
                  maps={ch:'i_tod_sky_rock_'+ch for ch in ('n','g','s')}, viewport_rgb=rgb,
                  surface='rock')
drive=make_material('drive_metal',load_image('i_tod_sky_drive_c'),'hull',rough=.4,metal=1,
                    maps={ch:'i_tod_sky_drive_'+ch for ch in ('n','g','s')},surface='metal')
for ob in bpy.data.objects:
    if ob.type=='MESH' and (ob.name.endswith('engine bell') or ob.name.endswith('engine bells') or ob.name=='dreadnought aux bells'):
        assert ob.data.materials[0].name in ('mtl_tod_sky_hull2','mtl_tod_sky_drive_metal'),ob.name
        ob.data.materials[0]=drive
minerals={key:make_material('mineral_'+key,load_image('i_tod_sky_mineral_'+key+'_c'),'glow',
                           emit=EMIT['neon'],rough=.45,maps={ch:'i_tod_sky_mineral_'+ch for ch in ('n','g','s')},surface='rock')
          for key in ('magenta','cyan','amber')}
for key,color,replacement in [('3','magenta','cyan'),('4','cyan','amber')]:
    col=bpy.data.collections['ROCK '+key]
    col['variants']=json.dumps([['',[]],['_b',[['mineral_'+color,'mineral_'+replacement]]]])
    for ob in col.objects:
        if ob.type!='MESH' or ob.get('sky_group')!='vein':continue
        ob.data.materials[0]=minerals[color]
        uv=ob.data.uv_layers.get('UVMap') or ob.data.uv_layers.new(name='UVMap')
        for f in ob.data.polygons:
            axis=max(range(3),key=lambda i:abs(f.normal[i]))
            a,b=[(1,2),(0,2),(0,1)][axis]
            for li in f.loop_indices:
                co=ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv.data[li].uv=(co[a]/240,co[b]/240)
for material in bpy.data.materials:
    if material.name.startswith('mtl_tod_sky_'):
        material['surface_revision'] = 'fine-wear-20260929'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/job.get('output_blend','art/sky_ships/sky_fleet.blend')))
print('REALISM_MATERIALS_REFRESHED', len(CARGO), 'cargo coatings; matched dark/light hull maps; fractured mineral rock')
