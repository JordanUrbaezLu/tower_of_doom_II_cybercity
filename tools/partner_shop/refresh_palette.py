"""Re-export only the tiny light palette from the master, preserving geometry/bakes.

Run in background Blender after a build has stopped. Asserts existing UV cells
still match the master material ordering before replacing native textures.
"""
import bpy,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop';KIT=ART/'engine_kit';IMG=ROOT/'model_export/tod_shop/_images'
bpy.ops.wm.open_mainfile(filepath=str(ART/'partner_shop.blend'));scene=bpy.context.scene;scene['shop_powered']=1;scene.frame_set(1);bpy.context.view_layer.update()
names=json.loads((ART/'native_groups.json').read_text());groups=['steady','mask','letter_t','letter_e','letter_c','core_left','core_counter','core_right','scan_0','scan_1','scan_2','scan_3','arc','spark']
palette=[];entries={}
for g in groups:
    objects=[bpy.data.objects[n] for n in names[g]] if g in names else [next(o for o in scene.objects if o.get('fx_kind')==g and o.get('fx_event')=='sign T')]
    for ob in objects:
        for m in ob.data.materials:
            if (g,m.name) in entries:continue
            p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');col=list(p.inputs['Emission Color'].default_value[:3]);base=list(p.inputs['Base Color'].default_value[:3])
            value=m.node_tree.nodes.get('Electrical timeline');strength=value.outputs[0].default_value if value else p.inputs['Emission Strength'].default_value
            if g=='mask':strength=.5 if 'weak' in m.name else 3.1
            elif g.startswith('letter'):strength=5.5
            elif g=='core_left':strength=3.3
            elif g=='core_counter':strength=2.5
            elif g=='core_right':strength=3.1
            elif g.startswith('scan'):strength=3
            entries[(g,m.name)]=len(palette);palette.append({'group':g,'material':m.name,'c':base,'e':[v*strength/6 for v in col],'s':[.06]*3,'g':[1-p.inputs['Roughness'].default_value]*3,'n':[.5,.5,1]})
    geometry=json.loads((KIT/(g+'_lod0.json')).read_text())
    actual={int(c['uv'][0]*8)+8*int((1-c['uv'][1])*8) for f in geometry['faces'] for c in f}
    expected={v for (group,_),v in entries.items() if group==g};assert actual==expected,(g,actual,expected)
size=64;cell=8
for suffix in ('c','e','s','g','n'):
    pixels=[0.0]*(size*size*4)
    for i,entry in enumerate(palette):
        rgb=entry[suffix]
        if suffix in ('c','e','s'):rgb=[12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055 for v in rgb]
        for y in range((i//8)*cell,(i//8+1)*cell):
            for x in range((i%8)*cell,(i%8+1)*cell):pixels[(y*size+x)*4:(y*size+x)*4+4]=rgb+[1]
    im=bpy.data.images.new('i_tod_shop_glow_'+suffix,width=size,height=size,alpha=False);im.colorspace_settings.name='Non-Color' if suffix in ('n','g') else 'sRGB';im.pixels.foreach_set(pixels);im.filepath_raw=str(IMG/(im.name+'.png'));im.file_format='PNG';im.save()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for file in ('source_manifest.json','install_manifest.json'):
    p=KIT/file;m=json.loads(p.read_text());m['textures']={p.name:sha(p) for p in IMG.glob('*.png')};m['palette_encoding']='linear source -> explicit sRGB color bytes; normal/gloss linear';p.write_text(json.dumps(m,indent=2))
(KIT/'palette_sources.json').write_text(json.dumps(palette,indent=2))
print('SHOP_PALETTE_CORRECTED',len(palette),'source swatches; existing UV cells verified')
