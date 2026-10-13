"""Add a reversible master power switch and explicit native component ownership."""
import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/partner_shop'
scene=bpy.context.scene;assert scene.get('tod2_shop_studio')
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
scene.frame_set(1);scene['shop_powered']=1.0
scene.id_properties_ui('shop_powered').update(min=0,max=1,description='0: empty unpowered hut. 1: merchant, neon and electrical animation.')
def power_driver(socket):
    fc=socket.driver_add('default_value');d=fc.driver;d.type='SCRIPTED';d.expression='power'
    v=d.variables.new();v.name='power';v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path='["shop_powered"]'
def hidden_driver(ob,prop):
    try:ob.driver_remove(prop)
    except TypeError:pass
    fc=ob.driver_add(prop);d=fc.driver;d.expression='power < 0.5'
    v=d.variables.new();v.name='power';v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path='["shop_powered"]'
def fcurves(owner):
    if not owner.animation_data or not owner.animation_data.action:return []
    a=owner.animation_data.action
    return [fc for layer in a.layers for strip in layer.strips for slot in a.slots if (bag:=strip.channelbag(slot)) for fc in bag.fcurves]
emissive=set()
for m in bpy.data.materials:
    if not m.use_nodes or not m.name.startswith('SHOP /'):continue
    p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not p:continue
    if m.get('shop_emissive'):emissive.add(m);continue
    if p.inputs['Emission Strength'].default_value<=0:continue
    m['shop_emissive']=True;emissive.add(m)
    value=m.node_tree.nodes.new('ShaderNodeValue');value.name='Electrical timeline';value.outputs[0].default_value=p.inputs['Emission Strength'].default_value
    old=p.inputs['Emission Strength'].path_from_id('default_value')
    for fc in fcurves(m.node_tree):
        if fc.data_path==old:fc.data_path=value.outputs[0].path_from_id('default_value')
    gate=m.node_tree.nodes.new('ShaderNodeMath');gate.name='Shop master power';gate.operation='MULTIPLY';gate.inputs[1].default_value=1
    power_driver(gate.inputs[1]);m.node_tree.links.new(value.outputs[0],gate.inputs[0]);m.node_tree.links.new(gate.outputs[0],p.inputs['Emission Strength'])
    # Red glass remains physical but looks unpowered when emission is zero.
    p.inputs['Base Color'].default_value=tuple(v*.11 for v in p.inputs['Base Color'].default_value[:3])+(1,)
groups={}
for col in bpy.data.collections:
    if not col.name.startswith('SHOP |') or col.name.startswith(('SHOP | 90','SHOP | 91')):continue
    for ob in col.objects:
        if ob.type not in ('MESH','CURVE','FONT'):continue
        mats=[m for m in ob.data.materials if m];glow=any(m in emissive for m in mats)
        group='solid'
        if col.name.startswith('SHOP | 08'):
            group='preview_fx';hidden_driver(ob,'hide_render');hidden_driver(ob,'hide_viewport')
        elif col.name.startswith('SHOP | 04'):
            group='mask' if glow else 'vendor';hidden_driver(ob,'hide_render');hidden_driver(ob,'hide_viewport')
        elif ob.get('neon_letter') in ('T','E','H'):group='letter_'+ob['neon_letter'].lower()
        elif glow:
            group='steady'
            for suffix in ['left red energy core','counter canister red pulse','existing tall core red pulse']:
                if any(m.name=='SHOP / '+suffix for m in mats):group={'left red energy core':'core_left','counter canister red pulse':'core_counter','existing tall core red pulse':'core_right'}[suffix]
            for idx in range(4):
                if any(m.name=='SHOP / left core scan '+str(idx) for m in mats):group='scan_'+str(idx)
        ob['shop_native_group']=group;groups.setdefault(group,[]).append(ob.name)
for name in ['Window practical','Dark | red shelf backlight']:
    ob=bpy.data.objects.get(name)
    if ob:hidden_driver(ob,'hide_render');hidden_driver(ob,'hide_viewport')
(OUT/'native_groups.json').write_text(json.dumps(groups,indent=2))
scene['shop_power_state_contract']='OFF: merchant absent, all emission/sparks/practicals disabled; physical hut and inventory remain. ON: T/E/H blink, other letters steady, mask slow pulse.'
scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print('SHOP_POWER_STATES',json.dumps({k:len(v) for k,v in groups.items()}))
