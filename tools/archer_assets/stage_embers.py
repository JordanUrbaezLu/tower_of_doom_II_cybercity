"""Blender MCP: translate T6 reveal/ember/heat inputs to a native T7 flipbook.

The T6 custom shader bytecode cannot run in T7. Preserve its source textures,
UV directions, 100-second common period, brightness and flicker range. This is
a renderer translation, not a claim of pixel-identical cross-engine shading.
"""
import bpy,json,re,sys,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/archer_assets'))
from install_native import block
SRC=ROOT/'source_library/archer_equipment/retriever/images';OUT=ROOT/'model_export/tod_archer/_images'
size=512;tiles=8;frames=64;period=100.0
def load(name):
    im=bpy.data.images.load(str(SRC/(name+'.dds')),check_existing=False)
    return im,np.array(im.pixels[:],dtype=np.float32).reshape(im.size[1],im.size[0],4)
reveal,mask=load('~-gmtl_t6_wpn_zmb_tomahawk_reveal')
ember,embers=load('jun_ter_wood_burnt_e');heat,heats=load('glowcycle_random_01_c')
y,x=np.mgrid[0:size,0:size];u=(x+.5)/size;v=(y+.5)/size
def sample(a,du,dv):
    h,w=a.shape[:2];sx=((u+du)%1)*w-.5;sy=((v+dv)%1)*h-.5
    ix=np.floor(sx).astype(int);iy=np.floor(sy).astype(int);fx=(sx-ix)[...,None];fy=(sy-iy)[...,None]
    return (a[iy%h,ix%w]*(1-fx)+a[iy%h,(ix+1)%w]*fx)*(1-fy)+(a[(iy+1)%h,ix%w]*(1-fx)+a[(iy+1)%h,(ix+1)%w]*fx)*fy
reveal_pixels=sample(mask,0,0)
atlas=np.zeros((size*tiles,size*tiles,4),dtype=np.float32);atlas[:,:,3]=1
for frame in range(frames):
    t=period*frame/frames
    e=sample(embers,-.01*t,-.02*t)
    h=sample(heats,.02*t,.03*t)
    rgb=e[:,:,:3]*h[:,:,:3]*reveal_pixels[:,:,:3]
    # Native flipbook starts at the upper left; Blender's pixels start below.
    row=tiles-1-frame//tiles;col=frame%tiles
    atlas[row*size:(row+1)*size,col*size:(col+1)*size,:3]=rgb
asset_name='i_tod_retriever_ember_atlas'
image=bpy.data.images.new(asset_name,width=size*tiles,height=size*tiles,alpha=True)
image.pixels.foreach_set(atlas.ravel());image.filepath_raw=str(OUT/(asset_name+'.png'));image.file_format='PNG';image.save()
gdt=ROOT/'source_data/tod_retriever.gdt';s=gdt.read_text()
m=re.search(r'("mtl_tod_retriever_blade"\s*\(\s*"material.gdf"\s*\)\s*\{)([^}]+)',s)
fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',m[2]))
fields.update({'materialCategory':'Geometry Advanced','materialType':'lit_emissive_scroll_advanced_fullspec',
 'colorMap00':asset_name,'colorTint1':'1 1 1 1','scaleRGB':10,'emissiveIncompetence':0,
 'uvMotionToggle1':1,'rowCount':tiles,'columnCount':tiles,'imageTime':period/frames,
 'detailScaleX':1,'detailScaleY':1,'zoomMin':1,'zoomMax':1,'waterRoughness':0,
 'flickerMin':.85,'flickerMax':1.1,'flickerSpeed':1,'flickerPower':1,'flickerSeedU':.2,'flickerSeedV':0})
start=m.start();end=s.index('}',m.end())+1
s=s[:start]+block('mtl_tod_retriever_blade','material',fields).strip()+s[end:]
s=re.sub(r'"i_tod_retriever_ember_atlas"\s*\(\s*"image.gdf"\s*\)\s*\{[^}]+\}', '', s)
s=s.rstrip()[:-1]+block(asset_name,'image',{'baseImage':Path(image.filepath_raw).relative_to(ROOT).as_posix(),'imageType':'Texture','semantic':'diffuseMap','coreSemantic':'sRGB3chAlpha','streamable':0,'compressionMethod':'compressed high color'})+'}\n'
gdt.write_text(s)
# Preview the same atlas, with native upper-left UV convention.
material=bpy.data.materials['mtl_tod_retriever_blade'];n=material.node_tree.nodes;l=material.node_tree.links
p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=image
uv=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value=(1/tiles,1/tiles,1);mapping.inputs['Location'].default_value=(0,(tiles-1)/tiles,0)
l.new(uv.outputs['UV'],mapping.inputs['Vector']);l.new(mapping.outputs['Vector'],tex.inputs['Vector'])
l.new(tex.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=10
for frame in range(frames):
    mapping.inputs['Location'].default_value=(frame%tiles/tiles,(tiles-1-frame//tiles)/tiles,0)
    mapping.inputs['Location'].keyframe_insert(data_path='default_value',frame=frame+1)
scene=bpy.data.scenes['BO2 native first person'];bpy.context.window_manager.windows[0].scene=scene
for ob in scene.objects:
    if ob.type=='MESH':
        ob.hide_render=not ob.name.startswith('flourish ');ob.hide_viewport=ob.hide_render
        for poly in ob.data.polygons:poly.use_smooth=True
scene.frame_set(30);scene.render.filepath=str(ROOT/'art/archer_assets/preview/retriever_ember_flourish.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
report={'source_maps':[im.filepath for im in (reveal,ember,heat)],'source_constants':{'ember_direction':[-.01,-.02],'heat_direction':[.02,.03],'emissive':10,'flicker':[.85,1.1]},'atlas':{'file':Path(image.filepath_raw).relative_to(ROOT).as_posix(),'size':list(image.size),'frames':frames,'frame_size':[size,size],'period_seconds':period},'renderer_translation':'T6 custom shader to BO3 native masked flipbook; not pixel-identical shading','nonzero_fraction':float(np.mean(atlas[:,:,:3].max(axis=2)>.001))}
(ROOT/'art/archer_assets/engine_kit/ember_material.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/archer_assets/archer_equipment.blend'))
print('NATIVE_EMBERS',report)
