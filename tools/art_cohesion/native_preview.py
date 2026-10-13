"""Shared, explicitly APPROXIMATE Blender view of exported fullspec materials.

BO3 is the final authority: this is a diffuse + colored GGX lobe, not its BRDF,
probe system, baked lighting, exposure or tone mapping. Gloss uses the native
range, then an approximate Blinn-exponent to GGX perceptual-roughness conversion.
No arbitrary per-prop metallic value or cosmetically softened roughness remap.
"""
import pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2]
DESCRIPTION='Exported maps and gloss range; approximate fullspec GGX preview, not BO3 parity'

def fields(file,name,kind='material'):
    text=pathlib.Path(file).read_text(encoding='utf-8-sig')
    match=re.search(r'"'+re.escape(name)+r'"\s*\(\s*"'+kind+r'.gdf"\s*\)\s*\{([^}]+)\}',text)
    assert match,(file,name)
    return dict(re.findall(r'"([^"\r\n]+)"\s*"([^"\r\n]*)"',match.group(1)))

def fullspec(file,name,image_folder=None):
    import bpy
    f=fields(file,name)
    mat=bpy.data.materials.new('Native approximation | '+name);mat.use_nodes=True
    mat.use_fake_user=True  # Keep unavailable-state variants through save/reopen.
    mat['preview_limit']=DESCRIPTION;mat['native_fields']=str(f)
    n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial')
    def math(op,a,b=None):
        node=n.new('ShaderNodeMath');node.operation=op
        for i,x in enumerate((a,b)):
            if x is None:continue
            if isinstance(x,(int,float)):node.inputs[i].default_value=x
            else:l.new(x,node.inputs[i])
        return node.outputs[0]
    def tex(key,linear=False):
        asset=f[key]
        if image_folder:path=pathlib.Path(image_folder)/(asset+'.png')
        else:
            path=ROOT/fields(file,asset,'image')['baseImage'].replace('\\','/')
        im=bpy.data.images.load(str(path),check_existing=True)
        im.colorspace_settings.name='Non-Color' if linear else 'sRGB'
        node=n.new('ShaderNodeTexImage');node.image=im
        return node.outputs['Color']
    def tint(socket,key):
        values=[float(x) for x in f.get(key,'1 1 1 1').split()]
        linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values[:3]]
        node=n.new('ShaderNodeMixRGB');node.blend_type='MULTIPLY';node.inputs[0].default_value=1;node.inputs[2].default_value=(*linear,1);l.new(socket,node.inputs[1]);return node.outputs[0]
    # Installed color_base/specular_base techsetdefs explicitly convert these
    # GDT colors from sRGB. Keep palette variants consistent with that binding.
    c,s,g,normal=tint(tex('colorMap'),'colorTint'),tint(tex('specColorMap'),'specColorTint'),tex('cosinePowerMap',True),tex('normalMap',True)
    # Native glossRange maps relative [0,1] to exponent stops; conversion below
    # is a documented approximation. It still responds to real GDT changes.
    absolute=math('ADD',math('MULTIPLY',g,float(f['glossRangeMax'])-float(f['glossRangeMin'])),float(f['glossRangeMin']))
    rough=math('POWER',math('DIVIDE',2,math('ADD',math('POWER',2,absolute),2)),.25)
    sep=n.new('ShaderNodeSeparateXYZ');comb=n.new('ShaderNodeCombineXYZ');l.new(normal,sep.inputs[0]);l.new(sep.outputs[0],comb.inputs[0]);l.new(math('SUBTRACT',1,sep.outputs[1]),comb.inputs[1]);l.new(sep.outputs[2],comb.inputs[2])
    nm=n.new('ShaderNodeNormalMap');l.new(comb.outputs[0],nm.inputs['Color'])
    dif=n.new('ShaderNodeBsdfDiffuse');l.new(c,dif.inputs['Color']);l.new(nm.outputs[0],dif.inputs['Normal'])
    gloss=n.new('ShaderNodeBsdfAnisotropic');l.new(s,gloss.inputs['Color']);l.new(rough,gloss.inputs['Roughness']);l.new(nm.outputs[0],gloss.inputs['Normal'])
    # specAmount/probeAmount are retained as metadata: their precise shader
    # influence is not established. Do not pretend to reproduce native probes.
    mix=n.new('ShaderNodeAddShader');l.new(dif.outputs[0],mix.inputs[0]);l.new(gloss.outputs[0],mix.inputs[1])
    em=n.new('ShaderNodeEmission')
    if f.get('colorMap00') and float(f.get('scaleRGB',0)):
        l.new(tex('colorMap00'),em.inputs[0]);em.inputs[1].default_value=float(f['scaleRGB'])
    else:em.inputs[1].default_value=0
    add=n.new('ShaderNodeAddShader');l.new(mix.outputs[0],add.inputs[0]);l.new(em.outputs[0],add.inputs[1]);l.new(add.outputs[0],out.inputs['Surface'])
    return mat
