"""Extend the MCP library with quieter large-scale armor and inset crystal art."""
import bpy,math,pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/cybercity_materials'
assert pathlib.Path(bpy.data.filepath)==ART/'cybercity_material_library.blend','Run 06a_open_library.py through MCP first'
scene=bpy.context.scene
def material(name,color,metal,rough):
    m=bpy.data.materials.new('CC | '+name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    n,l=m.node_tree.nodes,m.node_tree.links;geo=n.new('ShaderNodeNewGeometry');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.2;noise.inputs['Detail'].default_value=3;l.new(geo.outputs['Position'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(x*.87 for x in color),1);ramp.color_ramp.elements[1].color=(*(x*1.04 for x in color),1);l.new(noise.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
    rr=n.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=rough-.045;rr.inputs['To Max'].default_value=rough+.035;l.new(noise.outputs[0],rr.inputs[0]);l.new(rr.outputs[0],p.inputs['Roughness'])
    m.asset_mark();m.asset_data.description='Crown extension: neutral source alloy supports native color-role variants; no world emission during blackout.';return m
alloy=material('architectural alloy',(.30,.30,.30),.78,.55)
edge=material('machined crown edge',(.43,.43,.43),.83,.46)
recess=bpy.data.materials['CC | gasket and recess']
glass=material('frosted crystal insert',(.32,.32,.32),.28,.4)
col=None;offset=0
def box(name,x,y,z,w,h,d,mat,bevel):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(offset+x,y,z));ob=bpy.context.object;ob.name=name;ob.scale=(w,h,d);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(ob.users_collection):c.objects.unlink(ob)
    col.objects.link(ob);ob.data.materials.append(mat)
    if bevel:
        b=ob.modifiers.new('Rounded manufactured edge','BEVEL');b.width=bevel;b.segments=4;n=ob.modifiers.new('Face normals','WEIGHTED_NORMAL');n.keep_sharp=True
    return ob
for index,kind in enumerate(('armor','crystal')):
    offset=640+index*160;col=bpy.data.collections.new('CC_TILE_'+kind);scene.collection.children.link(col)
    box('Sealed backing',64,64,-.4,128,128,.8,recess,0)
    if kind=='armor':
        for x,y,w,h in [(40,34,77,64),(104,34,45,64),(24,98,45,60),(88,98,77,60)]:
            box('Interlocking cast panel',x,y,.28,w,h,.56,alloy,.6)
            for sx in (-1,1):
                for sy in (-1,1):
                    xx,yy=x+sx*(w/2-4),y+sy*(h/2-4)
                    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=1.45,depth=.20,location=(offset+xx,yy,.55));ob=bpy.context.object;ob.name='Flush captive fastener'
                    for c in list(ob.users_collection):c.objects.unlink(ob)
                    col.objects.link(ob);ob.data.materials.append(edge)
                    box('Fastener slot',xx,yy,.67,1.2,.25,.05,recess,.04)
            box('Long panel reinforcement',x,y,w*.002+ .57,w-14,.42,.12,edge,.12)
            for j in range(3):box('Contact edge wear',x-w/2+7+j*1.9,y+h/2-.9,.59,1.2,.16,.04,edge,.035)
    else:
        box('Crystal carrier',64,64,.18,125,125,.36,edge,.4)
        box('Inset seal',64,64,.4,117,117,.25,recess,.35)
        pane=box('Frosted beveled insert',64,64,.54,112,112,.45,glass,1.5)
        for x in (13,115):
            for y in (13,115):box('Protected corner contact',x,y,.91,7,2,.15,edge,.3)
        for j in range(5):
            box('Crystal etched fine line',64,23+j*20,.782,74,.2,.025,edge,.03)
    bpy.ops.mesh.primitive_plane_add(size=128,location=(offset+64,64,0));low=bpy.context.object;low.name='CC receiver '+kind
    for c in list(low.users_collection):c.objects.unlink(low)
    bpy.data.collections['CC_RECEIVERS'].objects.link(low);low.hide_render=True;low.hide_set(True)
scene['crown_extension']='Armor and crystal surface geometry; native world emission stays zero for the blackout/power wave'
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'crown_surface_library.blend'))
print('CROWN_MCP_ART_SAVED armor + crystal; original library preserved',flush=True)
