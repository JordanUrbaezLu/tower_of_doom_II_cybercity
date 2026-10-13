"""MCP: inspect final native-equivalent image bindings in the staged master."""
import bpy,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff/detail_pass'
bpy.ops.wm.open_mainfile(filepath=str(ART/'staff_master.blend'))
result={}
for name in ['mtl_tod_necro_staff_bone','mtl_tod_necro_staff_leather','mtl_tod_necro_staff_forge']:
    m=bpy.data.materials[name];bs=m.node_tree.nodes.get('Principled BSDF')
    result[name]={k:[dict(node=x.from_node.name,type=x.from_node.type) for x in bs.inputs[k].links] for k in ['Base Color','Normal']}
    result[name]['images']=[dict(node=n.name,name=n.image.name,file=bpy.path.abspath(n.image.filepath),source=n.image.source,size=list(n.image.size),colorspace=n.image.colorspace_settings.name) for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    result[name]['uv']=[dict(node=n.name,map=n.uv_map) for n in m.node_tree.nodes if n.type in {'UVMAP','NORMAL_MAP'}]
(ART/'material_bindings.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
