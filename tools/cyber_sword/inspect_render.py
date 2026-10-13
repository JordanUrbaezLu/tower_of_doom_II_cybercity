import bpy,json
scene=bpy.context.scene
print('SCENE',scene.name,'nodes',[(n.name,n.type,getattr(n,'scene',None).name if getattr(n,'scene',None) else None) for n in scene.node_tree.nodes])
for frame in (1,60):
    scene.frame_set(frame);scene.update_tag();bpy.context.view_layer.update()
    print('FRAME',frame,'charge',scene['cyber_charge'])
    for m in bpy.data.materials:
        if m.name.startswith('CS | '):
            p=m.node_tree.nodes.get('Principled BSDF');print(m.name,p.inputs['Emission Strength'].default_value,'links',[(l.from_node.name,l.to_socket.name) for l in p.inputs['Base Color'].links])
for o in scene.objects:
    if o.name.startswith('Blade') and o.type=='MESH':print('BLADE',o.name,len(o.data.polygons),[m.name for m in o.data.materials],[(m.name,m.type) for m in o.modifiers])
