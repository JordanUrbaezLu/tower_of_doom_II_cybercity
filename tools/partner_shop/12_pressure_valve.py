"""Pressure wheel and gauge move on the same six-second electrical timeline."""
from pathlib import Path
PRESERVE_SHOP_MATERIALS=True
exec(compile(Path(__file__).with_name('studio.py').read_text(),str(Path(__file__).with_name('studio.py')),'exec'))
if bpy.context.screen and bpy.context.screen.is_animation_playing:bpy.ops.screen.animation_cancel(restore_frame=False)
scene.frame_set(1)
for ob in list(scene.objects):
    if ob.name.startswith('Pressure |'):bpy.data.objects.remove(ob,do_unlink=True)
stem=cylinder('Pressure | valve stem',(90,-21,47),1.15,22,brass,detail,(0,-1,0));stem['shop_native_group']='solid'
valvepaint=material('valve wheel chipped red enamel',(.17,.008,.01),.58,.48)
center=Vector((90,-32,47));parts=[]
parts.append(tube('Pressure | handwheel rim',[tuple(center+Vector((5.4*math.sin(i*math.tau/32),0,5.4*math.cos(i*math.tau/32)))) for i in range(32)],.62,valvepaint,detail,True))
parts.append(cylinder('Pressure | handwheel hub',center,1.65,1.8,steel,detail,(0,-1,0)))
for i in range(3):
    a=i*math.tau/3
    parts.append(beam('Pressure | handwheel spoke',center,center+Vector((5*math.sin(a),0,5*math.cos(a))),.35,valvepaint))
wheel=bpy.data.objects.new('Pressure | wheel pivot',None);detail.objects.link(wheel);wheel.location=center
bpy.context.view_layer.update()
for ob in parts:
    mw=ob.matrix_world.copy();ob.parent=wheel;ob.matrix_world=mw;ob['shop_native_group']='valve';ob['shop_native_pivot']=list(center)
needle=bpy.data.objects['Gauge needle']
# Original beam geometry is kept intact while its animated parent owns the pivot.
needle.animation_data_clear();pivot=bpy.data.objects.new('Pressure | gauge pivot',None);detail.objects.link(pivot);pivot.location=(73,-36.55,74)
bpy.context.view_layer.update();mw=needle.matrix_world.copy();needle.parent=pivot;needle.matrix_world=mw
needle['shop_native_group']='needle';needle['shop_native_pivot']=[73,-36.55,74]
def drive(ob,expression):
    fc=ob.driver_add('rotation_euler',1);d=fc.driver;d.type='SCRIPTED';d.expression=expression
    v=d.variables.new();v.name='power';v.type='SINGLE_PROP';v.targets[0].id_type='SCENE';v.targets[0].id=scene;v.targets[0].data_path='["shop_powered"]'
drive(wheel,'power * (0.18*(1-cos((frame-1)*2*pi/90)))')
drive(pivot,'power * (0.15*sin((frame-1)*2*pi/90)+0.035*sin((frame-1)*2*pi/9))')
scene['shop_pressure_animation']='3-second 0..20.6 degree valve turn; gauge +/-10.6 degrees with fine needle chatter; off freezes at rest.'
scene.frame_set(1);bpy.context.view_layer.update()
groups={}
for ob in scene.objects:
    if 'shop_native_group' in ob:groups.setdefault(ob['shop_native_group'],[]).append(ob.name)
(OUT/'native_groups.json').write_text(json.dumps(groups,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'partner_shop.blend'))
print('PRESSURE_ANIMATED',len(parts),'wheel pieces; gauge needle; power gate')
