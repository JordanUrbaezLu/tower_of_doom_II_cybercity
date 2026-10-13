"""Install material twins and the MCP-authored recharge mesh; preserve body geometry."""
import json,re,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/teleporter';KIT=ART/'engine_kit';OUT=ROOT/'model_export/tod_teleporter'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((KIT/'state_source.json').read_text());assert sha(ART/'teleporter_cyber.blend')==state['master_sha256']
palette=json.loads((ROOT/'tools/teleporter/state_palette.json').read_text())
def srgb(x):return 12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055
pending_tint=' '.join(format(srgb(c),'.8f') for c in palette['pending_linear'])+' 1'
gdt=ROOT/'source_data/tod_teleporter.gdt';src=gdt.read_text();blocks={name:(kind,dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',body))) for name,kind,body in re.findall(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{(.*?)\n\t}',src,re.S)}
def block(name,kind,fields):return '\t"'+name+'" ( "'+kind+'" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'
blocks['mtl_tod_teleporter'][1]['colorMap00']='i_tod_teleporter_ready_e'
gdt.write_text('{\n'+''.join(block(n,*v) for n,v in blocks.items())+'}\n')
off=dict(blocks['tod_teleporter'][1]);off['skinOverride']='mtl_tod_teleporter mtl_tod_tp_off'
mat=dict(blocks['mtl_tod_teleporter'][1]);mat.update(scaleRGB=0,colorMap00='i_tod_teleporter_e')
rows=[block('tod_teleporter_off','xmodel.gdf',off),block('mtl_tod_tp_off','material.gdf',mat)]
im=dict(blocks['i_tod_teleporter_e'][1]);im['baseImage']='model_export\\\\tod_teleporter\\\\_images\\\\i_tod_teleporter_ready_e.png'
rows.append(block('i_tod_teleporter_ready_e','image.gdf',im))
d=json.loads((KIT/'recharge.json').read_text());model=xmodel.Model('tod_tp_recharge');bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];model.bones=[bone]
for band,strength in enumerate((5.5,2.3,.75)):
    name='mtl_tod_tp_charge_'+str(band);model.materials.append(xmodel.Material(name,'Phong',{}))
    faces=[f for f in d['faces'] if f[0]['band']==band];used=sorted({c['v'] for f in faces for c in f});remap={v:i for i,v in enumerate(used)}
    mesh=xmodel.Mesh('charge_'+str(band));mesh.verts=[xmodel.Vertex(d['verts'][v],[(0,1.)]) for v in used]
    for face in faces:
        f=xmodel.Face(band,band);f.indices=[xmodel.FaceVertex(remap[c['v']],tuple(c['n']),(1,1,1,1),tuple(c['uv'])) for c in face];mesh.faces.append(f)
    model.meshes.append(mesh)
    rows.append(block(name,'material.gdf',{'surfaceType':'metal','template':'material.template','materialCategory':'Geometry','materialType':'lit_emissive','colorMap':'$black_color','normalMap':'$identitynormalmap','colorMap00':'$white_diffuse','colorTint':'1 1 1 1','colorTint1':pending_tint,'scaleRGB':strength,'emissiveIncompetence':1,'emissiveFalloff':0,'waterRoughness':0,'usage':'<not in editor>'}))
file=OUT/'tod_tp_recharge_lod0.xmodel_bin'
# Preserve an identical compiled-input mesh even if this Python environment's
# optional compression backend differs from the original exporter.
candidate=OUT/'tod_tp_recharge_candidate.xmodel_bin';model.WriteFile_Bin(str(candidate),version=7)
def signature(path):
    m=xmodel.Model();m.LoadFile_Bin(str(path),split_meshes=True)
    return ([ (b.name,b.parent,b.offset,b.matrix) for b in m.bones ],[a.name for a in m.materials],
            [([ (v.offset,v.weights) for v in mesh.verts ],
              [ (f.mesh_id,f.material_id,[(c.vertex,c.normal,c.uv,c.color) for c in f.indices]) for f in mesh.faces ]) for mesh in m.meshes])
if file.exists() and signature(file)==signature(candidate):candidate.unlink()
else:candidate.replace(file)
fields=dict(blocks['tod_teleporter'][1]);fields['filename']='tod_teleporter\\\\tod_tp_recharge_lod0.xmodel_bin';fields['skinOverride']=''
for key in ('mediumLod','lowLod','lowestLod','lod4File','lod5File','lod6File','lod7File'):fields[key]=''
rows.append(block('tod_tp_recharge','xmodel.gdf',fields))
states_gdt=ROOT/'source_data/tod_teleporter_states.gdt';states_gdt.write_text('{\n'+''.join(rows)+'}\n')
(ROOT/'zone_source/tod_teleporter_states.zpkg').write_text('// State twins and the authored circular recharge indicator.\nxmodel,tod_teleporter_off\nxmodel,tod_tp_recharge\n')
p=KIT/'install_manifest.json';m=json.loads(p.read_text());m.setdefault('base_bake_master_sha256',m['master_sha256']);m['master_sha256']=state['master_sha256'];m['gdt_sha256']=sha(gdt);m['textures']['i_tod_teleporter_ready_e.png']=sha(OUT/'_images/i_tod_teleporter_ready_e.png');m['textures']['i_tod_teleporter_c.png']=state['state_color_sha256'];p.write_text(json.dumps(m,indent=2)+'\n')
(KIT/'states_manifest.json').write_text(json.dumps({**state,'gdt_sha256':sha(states_gdt),'recharge_file':file.relative_to(ROOT).as_posix(),'recharge_sha256':sha(file),'off_shared_lods':[r['sha256'] for r in m['models']],'body_geometry_unchanged':True},indent=2))
print('TELEPORTER_STATES_INSTALLED: shared seven body LODs; off skin; green map; '+str(len(d['faces']))+'-triangle yellow chase')
