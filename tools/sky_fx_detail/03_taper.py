"""MCP fine art refinement: tapered filament ends and softer turbulent dust.
Run after 01/02; the texture is rendered from authored geometry, never painted
over the finished PNG. Keeps editable source and native outputs in agreement.
"""
import bpy, pathlib, math, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'tmp/sky_fx_detail/staged'
scene=bpy.context.scene
scene.frame_set(1)
for obj in bpy.data.collections['Rift filaments'].objects:
    for spline in obj.data.splines:
        points=spline.points
        for i,p in enumerate(points): p.radius=max(.01,math.sin(math.pi*i/(len(points)-1))**.6)
for obj in bpy.data.collections['Rift dust'].objects:
    for spline in obj.data.splines:
        points=spline.points
        for i,p in enumerate(points):
            u=i/(len(points)-1)
            p.radius=max(.005,math.sin(math.pi*u)**1.3*(.65+.35*math.sin(u*27+.7)))
    # Transparent grazing edges on the round curve soften each gas filament.
    base=obj.data.materials[0]
    m=bpy.data.materials.get(base.name+' soft')
    if not m:
        m=base.copy();m.name=base.name+' soft'
        n=m.node_tree.nodes;l=m.node_tree.links
        out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
        em=next(x for x in n if x.type=='EMISSION')
        geo=n.new('ShaderNodeLayerWeight')
        power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=3
        trans=n.new('ShaderNodeBsdfTransparent')
        mix=n.new('ShaderNodeMixShader')
        # Facing rises toward grazing; invert it to retain only the middle.
        inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1
        l.new(geo.outputs['Facing'],inv.inputs[1]);l.new(inv.outputs[0],power.inputs[0])
        l.new(power.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2])
        l.new(mix.outputs[0],out.inputs['Surface'])
    obj.data.materials.clear();obj.data.materials.append(m)
scene.render.resolution_x=scene.render.resolution_y=1024
scene.cycles.samples=12
for group,name in [('Rift filaments','i_tod_sky_rift_fibre'),('Rift dust','i_tod_sky_rift_dust')]:
    for c in scene.collection.children:c.hide_render=c.name!=group
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sky_detail.blend'))
m=json.loads((OUT/'manifest.json').read_text())
m['images']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('i_tod_*.png')}
m['refinement']='tapered torn fibres; tapered soft grazing-alpha dust'
(OUT/'manifest.json').write_text(json.dumps(m,indent=2))
print('SKY DETAIL TAPERED')
