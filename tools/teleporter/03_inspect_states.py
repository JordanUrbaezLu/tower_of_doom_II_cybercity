import bpy,json
scene=bpy.context.scene
print('TELEPORTER_STATE_INSPECT',json.dumps({'file':bpy.data.filepath,'scene':scene.name,'objects':len(scene.objects),'glow':[{ 'name':m.name,'strength':n.inputs['Emission Strength'].default_value,'color':list(n.inputs['Emission Color'].default_value)} for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value>0],'design_parts':sum(bool(o.get('teleporter_design')) for o in scene.objects)},indent=2))
