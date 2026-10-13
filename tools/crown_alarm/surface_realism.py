"""Surface-space material authoring shared by the two alarm MCP studios.

No game/build/deployment access. The original editable masters and all native
LODs are captured once, then every iteration is staged from that same baseline.
Only UV coordinates change in native meshes. Fine wear follows part edges,
fasteners, seal contacts and touched surfaces instead of covering everything.
"""
import bpy, hashlib, json, math, pathlib, re, shutil, sys
import numpy as np
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORK = ROOT / 'tmp/alarm_realism'
STAGE = WORK / 'staged'
BASE = WORK / 'baseline'
sys.path.insert(0, str(pathlib.Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def capture(family):
    files = [ROOT/'source_data'/('tod_'+family+'.gdt')]
    files += list((ROOT/'model_export'/('tod_'+family)).rglob('*'))
    files += [ROOT/'art'/family/'manifest.json', ROOT/'art'/family/(family+'.blend')]
    if family == 'crown_alarm':
        files += [ROOT/'art/crown_alarm/visibility_review/high_fixture.blend']
    for p in files:
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        for dest in (BASE/rel, STAGE/rel):
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                original=ROOT/'art'/family/'realism_before'/rel
                shutil.copy2(original if original.exists() else p, dest)
    return json.loads((BASE/'art'/family/'manifest.json').read_text())

def fields(family):
    s=(BASE/'source_data'/('tod_'+family+'.gdt')).read_text()
    return {n:dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"',b))
            for n,k,b in re.findall(r'"([^"\n]+)" \( "([^"\n]+).gdf" \)\s*\{(.*?)\n\t\}',s,re.S)}

def pixel_data(ob, size):
    """Rasterize the actual authored UV triangles to surface coordinates."""
    me=ob.data; me.calc_loop_triangles()
    loc=np.zeros((size,size,3),np.float32); world=loc.copy(); mask=np.zeros((size,size),bool)
    uv=me.uv_layers.active.data
    for tri in me.loop_triangles:
        t=np.array([uv[i].uv[:] for i in tri.loops],np.float64)*size-.5
        low=np.maximum(np.floor(t.min(0)).astype(int),0); high=np.minimum(np.ceil(t.max(0)).astype(int),size-1)
        if np.any(high<low): continue
        xx,yy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1))
        a,b,c=t; den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-8: continue
        q=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        r=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
        take=(q>=-1e-5)&(r>=-1e-5)&(q+r<=1.00001)
        yy=yy[take];xx=xx[take];q=q[take,None];r=r[take,None]
        ps=np.array([me.vertices[i].co[:] for i in tri.vertices])
        ws=np.array([(ob.matrix_world@me.vertices[i].co)[:] for i in tri.vertices])
        loc[yy,xx]=q*ps[0]+r*ps[1]+(1-q-r)*ps[2]
        world[yy,xx]=q*ws[0]+r*ws[1]+(1-q-r)*ws[2]
        mask[yy,xx]=True
    return loc,world,mask

def layout(parts):
    areas=[]
    for ob in parts:
        ob.data.calc_loop_triangles()
        area=sum(((ob.matrix_world@ob.data.vertices[t.vertices[1]].co-ob.matrix_world@ob.data.vertices[t.vertices[0]].co).cross(
                  ob.matrix_world@ob.data.vertices[t.vertices[2]].co-ob.matrix_world@ob.data.vertices[t.vertices[0]].co)).length/2
                 for t in ob.data.loop_triangles)
        areas.append((ob,area))
    largest=max(a for _,a in areas)
    hero=4 if largest>=100 else 2
    wanted=[(ob,hero if area/largest>.40 else 2 if area/largest>.045 else 1) for ob,area in areas]
    # Preserve a 512-pixel hero region; lesser fasteners receive smaller tiles.
    for width in (8,16):
        occupied=np.zeros((width,width),bool); result={}
        for ob,s in sorted(wanted,key=lambda t:(-t[1],t[0].name)):
            found=False
            for y in range(width-s+1):
                for x in range(width-s+1):
                    if not occupied[y:y+s,x:x+s].any():
                        occupied[y:y+s,x:x+s]=True;result[ob.name]=(x*128,y*128,s*128);found=True;break
                if found:break
            if not found:break
        if len(result)==len(parts):return width*128,result
    raise RuntimeError('Atlas packing exceeded the material budget')

def material_maps(ob,size,label,family):
    loc,p,mask=pixel_data(ob,size)
    seed=int(hashlib.sha256((family+'|'+ob.name).encode()).hexdigest()[:8],16)
    rng=np.random.default_rng(seed)
    x,y,z=np.moveaxis(p,-1,0)
    # Several non-repeating physical scales, all subordinate to placed wear.
    broad=(np.sin(x*.87+y*.43+seed)*np.cos(z*.63-x*.28)+np.sin(y*1.91-z*.47))*.5
    fine=.5*np.sin(x*23.77+y*4.66+np.sin(z*7.3))+.5*np.sin(y*29.17+z*10.53+np.cos(x*.9))
    grain=rng.normal(0,1,mask.shape)
    rough_noise=.018*grain+.045*broad
    lo=np.min([v.co[:] for v in ob.data.vertices],axis=0)
    hi=np.max([v.co[:] for v in ob.data.vertices],axis=0)
    near=np.minimum(np.abs(loc-lo),np.abs(hi-loc))
    if any(k in ob.name for k in ('strut','shoulder')):
        edge=np.exp(-np.sort(near,axis=-1)[:,:,1]/.13)
    else:
        # Axial pieces: rim intersections, never a whole coplanar top face.
        radius=np.sqrt(loc[:,:,0]**2+loc[:,:,1]**2)
        rmax=max(math.hypot(v.co.x,v.co.y) for v in ob.data.vertices)
        edge=np.exp(-np.abs(radius-rmax)/.20)*np.exp(-near[:,:,2]/.24)
    broken=np.clip((np.sin(x*10.1+y*8.3+z*11.4)+fine*.8+broad-.3)/1.15,0,1)
    chip=edge*broken
    grime=np.zeros(mask.shape,np.float32)
    if family=='alarm_button':
        for contact in [3.05,8.2,28.0,35.4,37.0,38.2]:
            grime=np.maximum(grime,np.exp(-((z-contact)/.18)**2)*.44)
        if 'base' in ob.name or 'lip' in ob.name:
            for i in range(6):
                a=math.tau*(i+.5)/6
                grime=np.maximum(grime,np.exp(-((x-9.7*math.cos(a))**2+(y-9.7*math.sin(a))**2)/1.25)*.64)
    else:
        for contact in [3.6,4.4,10.3,11.6,12.5,45.6]:
            grime=np.maximum(grime,np.exp(-((z-contact)/.20)**2)*.46)
        if 'flange' in ob.name:
            for i in range(4):
                a=math.tau*(i+.5)/4
                grime=np.maximum(grime,np.exp(-((x-23*math.cos(a))**2+(y-23*math.sin(a))**2)/2.8)*.65)
    grime*=np.clip(.75+.32*broad,0,1)
    scratch=np.zeros(mask.shape,np.float32)
    # Sparse short rubbed/scored marks with feathered ends in world units.
    wlo=np.array([p[:,:,i][mask].min() for i in range(3)]);whi=np.array([p[:,:,i][mask].max() for i in range(3)])
    surface_points=p[mask]
    for i in range(18 if label in ('cast','hazard','steel') else 9):
        anchor=surface_points[rng.integers(len(surface_points))];length=rng.uniform(.35,2.5)
        along=(x-anchor[0])*.8+(y-anchor[1])*.6
        cross=(x-anchor[0])*(-.6)+(y-anchor[1])*.8+(z-anchor[2])*.4
        mark=np.exp(-(cross/.025)**2)*np.clip(1-np.abs(along)/length,0,1)*np.exp(-((z-anchor[2])/1.5)**2)
        scratch=np.maximum(scratch,mark)
    base={'cast':(.045,.049,.055),'steel':(.34,.36,.38),'rubber':(.012,.014,.016),
          'reflector':(.65,.66,.68),'lens':(.42,0,0),'hazard':(.86,.58,.02),
          'red_off':(.22,.01,.01),'red_on':(1,.03,.02)}[label]
    c=np.ones((*mask.shape,4),np.float32);c[:,:,:3]=np.array(base)*(1+.09*broad[:,:,None]+.008*grain[:,:,None])
    gloss=np.full(mask.shape,{'cast':.48,'steel':.72,'rubber':.18,'reflector':.85,'lens':.77,'hazard':.52,'red_off':.7,'red_on':.75}[label],np.float32)
    spec=np.full(mask.shape,.6 if label in ('steel','reflector') else .045,np.float32)
    height=.00012*grain+.00018*fine
    if label in ('cast','hazard'):
        # Coated metal: chips expose steel; rust is confined to a small fraction
        # of damaged edges/fastener contacts, not spread over intact coating.
        damage=np.clip(chip*.8+scratch*.42,0,.85)
        rust=np.clip((broad-.55)*1.8,0,1)*(damage*.65+grime*.15)
        steel=np.array((.22,.24,.25))
        c[:,:,:3]=c[:,:,:3]*(1-damage[:,:,None])+steel*damage[:,:,None]
        c[:,:,:3]=c[:,:,:3]*(1-rust[:,:,None])+np.array((.13,.057,.024))*rust[:,:,None]
        c[:,:,:3]*=(1-grime[:,:,None]*.48)
        gloss+=rough_noise-grime*.2+damage*.08-rust*.25
        spec+=damage*.38-rust*.025
        height+=.0007*fine-.004*damage-.001*rust
    elif label in ('steel','reflector'):
        tarnish=np.clip((broad-.05)*.5,0,.25)+grime*.25
        c[:,:,:3]*=(1-tarnish[:,:,None]*.5)
        c[:,:,:3]+=edge[:,:,None]*.018
        gloss+=rough_noise*.45-tarnish*.46-scratch*.06
        spec-=tarnish*.3
        height+=np.sin(z*190+x*5)*.00012-scratch*.002
        if label=='steel':
            # Old oil/oxide residue settles at the fitted joint and around
            # hardware; the broad machined faces retain clean metal highlights.
            residue=np.clip((broad+.05)*1.4,0,.8)*(grime*.6+edge*.10)
            c[:,:,:3]=c[:,:,:3]*(1-residue[:,:,None])+np.array((.12,.079,.04))*residue[:,:,None]
            c[:,:,:3]+=scratch[:,:,None]*.042
            gloss-=residue*.23+scratch*.065
            spec-=residue*.2
    elif label=='rubber':
        c[:,:,:3]*=(1+grime[:,:,None]*.8+edge[:,:,None]*.14)
        gloss+=rough_noise*.6-grime*.035
        height+=fine*.0002
    elif label=='lens':
        # Molded polycarbonate stays clear/red; very sparse fine cleaning marks.
        c[:,:,0]*=(1-grime*.16)
        # A clear dome must reveal the separate rotor. Overlapping optical
        # ribs use less opacity; no normal/gloss/color detail is changed.
        c[:,:,3]=.05 if ob.name.startswith('lens optical rib ') else .10
        gloss+=rough_noise*.25-scratch*.1-grime*.07
        height+=fine*.00005-scratch*.0006
    else:
        # Red polymer: frequently touched dome is burnished, its lower seating
        # seam collects dirt. Keep the on/off color and emissive roles intact.
        radial=np.hypot(x,y)
        handled=np.exp(-(radial/2.3)**2)*np.clip((z-40)/1.8,0,1)
        touch=np.exp(-((x+.45)/1.7)**2-((y+1.05)/1.3)**2)*np.clip((z-40.15)/.9,0,1)
        scuffs=np.zeros(mask.shape,np.float32)
        for i in range(6):
            # Six incomplete strokes, clustered on the actual hand-contact
            # shoulder; soft tapered ends read as rubbed polymer, not paint.
            dxp=x-(-1.2+i*.29);dyp=y-(-1.25+i*.08)
            along=dxp*.87+dyp*.5;across=dyp*.87-dxp*.5
            scuffs=np.maximum(scuffs,np.exp(-(across/.024)**2)*np.clip(1-np.abs(along)/(.38+i*.07),0,1))
        scuffs*=np.clip((z-40.4)/.55,0,1)
        c[:,:,:3]*=(1-grime[:,:,None]*.12+touch[:,:,None]*.08)
        c[:,:,:3]+=scuffs[:,:,None]*np.array((.035,.012,.009))
        gloss+=handled*.10+touch*(.08+.06*broad)+rough_noise*.5-scratch*.10-grime*.08-scuffs*.11
        height+=fine*.00005-scratch*.001
        height-=scuffs*.0012
    c[:,:,:3]=np.clip(c[:,:,:3],0,1)
    gloss=np.clip(gloss,.08,.94);spec=np.clip(spec,.02,.72)
    # Padding first, then differentiate, so UV island borders do not become
    # false hard seams in the normal map. Native Y is DirectX; preview flips it.
    vals=np.dstack((c,gloss,spec,height));valid=mask.copy()
    for _ in range(10):
        added=np.zeros_like(valid);total=np.zeros_like(vals);count=np.zeros_like(valid,dtype=np.float32)
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            v=np.roll(valid,(dy,dx),(0,1));take=(~valid)&v
            total[take]+=np.roll(vals,(dy,dx),(0,1))[take];count[take]+=1;added|=take
        vals[added]=total[added]/count[added,None];valid|=added
    c=vals[:,:,:4];gloss=vals[:,:,4];spec=vals[:,:,5];height=vals[:,:,6]
    dy,dx=np.gradient(height)
    # Small physical relief, deliberately bounded so compression never turns
    # this pass into lumpy/pitted silhouettes or excessive sparkle.
    nx=np.clip(-dx*size*.14,-.10,.10);ny=np.clip(dy*size*.14,-.10,.10)
    norm=np.sqrt(nx*nx+ny*ny+1)
    n=np.ones((*mask.shape,4),np.float32);n[:,:,0]=.5+.5*nx/norm;n[:,:,1]=.5+.5*ny/norm;n[:,:,2]=.5+.5/norm
    maps={'c':c,'n':n}
    for key,values in [('g',gloss),('s',spec)]:
        a=np.ones_like(c);a[:,:,:3]=values[:,:,None];maps[key]=a
    return maps,{'coverage':float(mask.mean()),'chip_fraction':float((chip[mask]>.2).mean()),
                 'gloss_range':[float(gloss[mask].min()),float(gloss[mask].max())]}

# Advanced transparent expects a linear scalar specularMask. The original
# full-color lens_s binding prevented a complete native material conversion.
# Black is the stock nonmetal mask; gray32 belongs to thermalHeatmap.
LENS_SPECULAR_MAP = '$black_specular'
LENS_SPECULAR_MASK = 0.0
LENS_SPECULAR_TINT = '.220916 .220916 .220916 1'


def native_lens_mask(fields):
    """Read only valid stock scalar masks; never guess an invalid RGB binding."""
    image = fields.get('specColorMap', '')
    if image == '$black_specular':
        return 0.0
    if image in ('', '$white_specular'):
        return 1.0  # specular_base's documented empty-field default.
    raise ValueError('Advanced lens needs a valid linear scalar specularMask: ' + image)


def native_lens_f0(fields):
    """Packed-shader F0: mix(.04, sRGB-to-linear tint, native scalar mask)."""
    values = [float(v) for v in fields.get('specColorTint', '1 1 1 1').split()[:3]]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    mask = native_lens_mask(fields)
    return tuple(.04 + mask * (v - .04) for v in linear)


def bind_material(mat,f,folder):
    """Read the real native maps/range, using the project's GGX approximation."""
    n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial')
    def tex(key,linear=False):
        path=folder/(f[key]+'.png')
        im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color' if linear else 'sRGB';im.pack()
        node=n.new('ShaderNodeTexImage');node.image=im;node.label=key
        return node
    c=tex('colorMap');normal=tex('normalMap',True)
    basic=f['materialType']=='lit_emissive_transparent'
    # The actual packed advanced-glass variants consume a scalar specular
    # mask and the sRGB native tint. A previously preserved alpha-test sample
    # was unrelated to this techset and incorrectly suggested constant F0.
    advanced_glass=f['materialType']=='lit_emissive_transparent_advanced'
    lens_mask=native_lens_mask(f) if advanced_glass else None
    constant_spec=f['materialType'] in ('lit_emissive_transparent','lit_emissive_transparent_advanced')
    g=None if basic else tex('cosinePowerMap',True)
    s=None if constant_spec else tex('specColorMap')
    def mathnode(op,a,b):
        node=n.new('ShaderNodeMath');node.operation=op
        for i,v in enumerate((a,b)):
            if isinstance(v,(int,float)):node.inputs[i].default_value=v
            else:l.new(v,node.inputs[i])
        return node.outputs[0]
    absolute=mathnode('ADD',mathnode('MULTIPLY',1 if basic else g.outputs['Color'],float(f['glossRangeMax'])-float(f['glossRangeMin'])),float(f['glossRangeMin']))
    rough=mathnode('POWER',mathnode('DIVIDE',2,mathnode('ADD',mathnode('POWER',2,absolute),2)),.25)
    split=n.new('ShaderNodeSeparateXYZ');combine=n.new('ShaderNodeCombineXYZ');l.new(normal.outputs['Color'],split.inputs[0])
    l.new(split.outputs[0],combine.inputs[0]);l.new(mathnode('SUBTRACT',1,split.outputs[1]),combine.inputs[1]);l.new(split.outputs[2],combine.inputs[2])
    nm=n.new('ShaderNodeNormalMap');l.new(combine.outputs[0],nm.inputs['Color'])
    # Same diffuse + full-color GGX approximation as art_cohesion/native_preview:
    # no invented metallic constant or cosmetic per-prop roughness override.
    dif=n.new('ShaderNodeBsdfDiffuse')
    if advanced_glass:
        # Native shader removes the mask's metallic fraction from diffuse.
        attenuation=n.new('ShaderNodeMixRGB');attenuation.blend_type='MULTIPLY'
        attenuation.inputs[0].default_value=1
        attenuation.inputs[2].default_value=(1-lens_mask,)*3+(1,)
        l.new(c.outputs['Color'],attenuation.inputs[1]);l.new(attenuation.outputs[0],dif.inputs['Color'])
    else:l.new(c.outputs['Color'],dif.inputs['Color'])
    l.new(nm.outputs[0],dif.inputs['Normal'])
    gloss=n.new('ShaderNodeBsdfAnisotropic')
    if constant_spec:gloss.inputs['Color'].default_value=(*native_lens_f0(f),1) if advanced_glass else (.04,.04,.04,1)
    else:l.new(s.outputs['Color'],gloss.inputs['Color'])
    l.new(rough,gloss.inputs['Roughness']);l.new(nm.outputs[0],gloss.inputs['Normal'])
    mix=n.new('ShaderNodeAddShader');l.new(dif.outputs[0],mix.inputs[0]);l.new(gloss.outputs[0],mix.inputs[1])
    em=n.new('ShaderNodeEmission');em.inputs[1].default_value=float(f.get('scaleRGB',0));l.new(c.outputs['Color'],em.inputs[0])
    add=n.new('ShaderNodeAddShader');l.new(mix.outputs[0],add.inputs[0]);l.new(em.outputs[0],add.inputs[1])
    if mat.name.endswith('lens'):
        transparent=n.new('ShaderNodeBsdfTransparent');alpha=n.new('ShaderNodeMixShader');l.new(c.outputs['Alpha'],alpha.inputs[0]);l.new(transparent.outputs[0],alpha.inputs[1]);l.new(add.outputs[0],alpha.inputs[2]);l.new(alpha.outputs[0],out.inputs['Surface']);mat.surface_render_method='DITHERED'
    else:l.new(add.outputs[0],out.inputs['Surface'])
    mat['preview_limit']='Native maps and gloss-range driven; approximate Blender BRDF, not BO3 approval.'
    if advanced_glass:
        mat['preview_specular']='Native scalar specColorMap: F0=mix(0.04,sRGB-to-linear specColorTint,mask); black mask=0, full diffuse. Full-color lens_s is unbound.'
        mat['preview_specular_mask']=lens_mask
        mat['preview_specular_f0']=native_lens_f0(f)
    elif constant_spec:mat['preview_specular']='Basic transparent historical approximation: dielectric F0=0.04.'

def remap_uv(ob,tile,total):
    x,y,size=tile
    for loop in ob.data.uv_layers.active.data:
        loop.uv=((x+loop.uv.x*size)/total,(y+loop.uv.y*size)/total)

def render_review(scene,out,family,state):
    scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=6
    scene.render.resolution_x=1000;scene.render.resolution_y=1100 if family=='alarm_button' else 850
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(out/(state+'.png'));bpy.ops.render.render(write_still=True)

def author(family):
    manifest=capture(family);definitions=fields(family)
    before_definitions={k:dict(v) for k,v in definitions.items()}
    if family=='crown_alarm':
        # Preserve the accepted advanced transparent shader/gloss and give
        # the scalar mask a dielectric tint instead of white metallic F0.
        definitions['mtl_tod_alarm_lens']['materialType']='lit_emissive_transparent_advanced'
        definitions['mtl_tod_alarm_lens']['specColorTint']=LENS_SPECULAR_TINT
        definitions['mtl_tod_alarm_lens']['specColorMap']=LENS_SPECULAR_MAP
        gdt=STAGE/'source_data/tod_crown_alarm.gdt'
        text=(BASE/'source_data/tod_crown_alarm.gdt').read_text()
        text,count=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"materialType" ")lit_emissive_transparent(")',r'\1lit_emissive_transparent_advanced\2',text,flags=re.S)
        assert count==1
        text,count=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorTint" ")[^"\n]*(")',
                           lambda m:m.group(1)+LENS_SPECULAR_TINT+m.group(2),text,flags=re.S)
        assert count==1
        text,count=re.subn(r'("mtl_tod_alarm_lens" \( "material.gdf" \)\s*\{.*?"specColorMap" ")[^"\n]*(")',
                           lambda m:m.group(1)+LENS_SPECULAR_MAP+m.group(2),text,flags=re.S)
        assert count==1
        gdt.write_text(text);manifest['gdt_sha256']=sha(gdt)
    art=STAGE/'art'/family;review=art/'realism_review';review.mkdir(parents=True,exist_ok=True)
    texdir=STAGE/'model_export'/('tod_'+family)/'_images'
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'art'/family/(family+'.blend')))
    scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
    group='alarm_group' if family=='crown_alarm' else 'btn_group'
    parts=[o for o in scene.objects if o.type=='MESH' and group in o]
    # Use off-state for an honest surface inspection (on state also reviewed).
    for ob in parts:
        for slot in ob.material_slots:
            if slot.material.name.endswith('red_on'):slot.material=bpy.data.materials['mtl_tod_abtn_red_off']
            elif slot.material.name.endswith('lamp_on'):slot.material=bpy.data.materials['mtl_tod_alarm_lamp_off']
    for mat in list(bpy.data.materials):
        if mat.name in before_definitions:bind_material(mat,before_definitions[mat.name],BASE/'model_export'/('tod_'+family)/'_images')
    # Matched before uses the exact same native-map preview and lighting.
    render_review(scene,review,family,'before')
    assignments={};stats={};newmaps={}
    for mat in list(bpy.data.materials):
        if mat.name not in definitions or 'lamp_' in mat.name or mat.name.endswith('red_on'):continue
        obs=[o for o in parts if o.data.materials[0]==mat]
        if not obs:continue
        label=mat.name.replace('mtl_tod_alarm_','').replace('mtl_tod_abtn_','')
        size,tiles=layout(obs);atlases={k:np.zeros((size,size,4),np.float32) for k in ('c','g','s','n')}
        for a in atlases.values():a[:,:,3]=1
        # Empty atlas space contributes to generated distant mip levels.
        # Keep lens color alpha transparent instead of opaque black gutters.
        if label=='lens':atlases['c'][:,:,3]=.045
        atlases['n'][:,:,:3]=(.5,.5,1)
        for ob in obs:
            x,y,s=tiles[ob.name];maps,metrics=material_maps(ob,s,label,family)
            for k,a in maps.items():atlases[k][y:y+s,x:x+s]=a
            assignments[ob.name]={'tile':tiles[ob.name],'size':size,'material':mat.name}
            stats[ob.name]=metrics
            remap_uv(ob,tiles[ob.name],size)
        for suffix,a in atlases.items():
            asset=definitions[mat.name][{'c':'colorMap','g':'cosinePowerMap','s':'specColorMap','n':'normalMap'}[suffix]]
            # Preserve the authored S atlas as an unbound source artifact;
            # never overwrite or create a stock-image name under this repo.
            if label=='lens' and suffix=='s':asset='i_tod_alarm_lens_s'
            im=bpy.data.images.new(asset+'_surface_authored',width=size,height=size,alpha=True)
            im.colorspace_settings.name='Non-Color' if suffix in ('g','n') else 'sRGB'
            # Blender's float pixel API is linear even when the saved PNG is sRGB.
            # The artist palette and fullspec F0 above use linear values.
            im.pixels.foreach_set(a.ravel());im.filepath_raw=str(texdir/(asset+'.png'));im.file_format='PNG';im.save();im.pack()
            newmaps[asset+'.png']=sha(texdir/(asset+'.png'))
    if family=='alarm_button':
        # On/off twins share a footprint, wear masks and physical maps. Preserve
        # the existing emissive color separately without changing its strength.
        for suffix in ('g','s','n'):
            shutil.copyfile(texdir/('i_tod_abtn_red_off_'+suffix+'.png'),texdir/('i_tod_abtn_red_on_'+suffix+'.png'))
            newmaps['i_tod_abtn_red_on_'+suffix+'.png']=sha(texdir/('i_tod_abtn_red_on_'+suffix+'.png'))
        redparts=[o for o in parts if o.get('btn_group')=='cap']
        onsize=assignments[redparts[0].name]['size']
        off=bpy.data.images.load(str(texdir/'i_tod_abtn_red_off_c.png'),check_existing=False)
        pix=np.array(off.pixels[:],np.float32).reshape(onsize,onsize,4)
        pix[:,:,:3]*=np.array((1/.22,.03/.01,.02/.01));pix[:,:,:3]=np.clip(pix[:,:,:3],0,1)
        im=bpy.data.images.new('i_tod_abtn_red_on_c_surface_authored',width=onsize,height=onsize,alpha=True)
        im.pixels.foreach_set(pix.ravel());im.filepath_raw=str(texdir/'i_tod_abtn_red_on_c.png');im.file_format='PNG';im.save();im.pack()
        newmaps['i_tod_abtn_red_on_c.png']=sha(texdir/'i_tod_abtn_red_on_c.png')
    for mat in list(bpy.data.materials):
        if mat.name in definitions:bind_material(mat,definitions[mat.name],texdir)
    scene['surface_realism_revision']='2026-09-29 fine material-specific wear'
    scene['preview_limit']='Actual native maps, approximate BRDF; user native visual test pending.'
    bpy.ops.wm.save_as_mainfile(filepath=str(art/(family+'.blend')))
    render_review(scene,review,family,'after')
    # Native meshes use V down. Remap every LOD/state/high derivative with the
    # same part atlas transform; positions, normals, weights and faces untouched.
    for row in manifest['models']:
        model=xmodel.Model();model.LoadFile_Bin(str(BASE/row['file']),split_meshes=True)
        for mesh in model.meshes:
            if mesh.name not in assignments:continue
            entry=assignments[mesh.name];x,y,s=entry['tile'];size=entry['size']
            for face in mesh.faces:
                for c in face.indices:
                    u,v=c.uv;c.uv=((x+u*s)/size,1-(y+(1-v)*s)/size)
        dest=STAGE/row['file'];model.WriteFile_Bin(str(dest),version=7);row['sha256']=sha(dest)
    manifest['textures'].update(newmaps)
    manifest['surface_realism']={'revision':'2026-09-29','authoring':'Actual Blender MCP execute_blender_code',
        'geometry':'All native vertices, normals, faces, bones, bounds and material roles retained; UV-only atlas update.',
        'native_visual_verified':False,'atlas_parts':assignments,'review':'realism_review/before.png and after.png'}
    if family=='crown_alarm':
        # Preserve the clear-glass contract when regenerating the full atlas
        # from the archived authoring baseline; the strict gate permits only
        # this revision's lens tint alongside the existing shader upgrade.
        manifest['lens_repair']={'revision':'2026-10-01 clear glass',
            'authoring':'Actual Blender MCP execute_blender_code',
            'dome_alpha':.10,'rib_alpha':.05,'padding_alpha':.045,
            'rgb_unchanged':True,'native_geometry_unchanged':True,'glow_unchanged':True,
            'specColorTint':LENS_SPECULAR_TINT,'specColorMap':LENS_SPECULAR_MAP,
            'native_specular_mask':0.0,
            'native_f0_after':.04,'review':'realism_review',
            'native_visual_verified':False,'native_playtested':False}
    (art/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (review/'surface_metrics.json').write_text(json.dumps(stats,indent=2)+'\n')
    # Close view isolates the tactile detail and retains the same studio rig.
    cam=scene.camera
    cam.location=(27,-37,54) if family=='alarm_button' else (72,-84,48)
    target=Vector((0,0,37.4) if family=='alarm_button' else (0,0,11))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=25 if family=='alarm_button' else 60
    render_review(scene,review,family,'detail')
    # States retain the existing native glow strength and color maps.
    for ob in parts:
        for slot in ob.material_slots:
            if slot.material.name.endswith('red_off'):slot.material=bpy.data.materials['mtl_tod_abtn_red_on']
            elif slot.material.name.endswith('lamp_off'):slot.material=bpy.data.materials['mtl_tod_alarm_lamp_on']
    render_review(scene,review,family,'on_detail')
    if family=='crown_alarm':
        bpy.ops.wm.open_mainfile(filepath=str(BASE/'art/crown_alarm/visibility_review/high_fixture.blend'))
        for ob in bpy.context.scene.objects:
            if ob.name in assignments and ob.type=='MESH':
                a=assignments[ob.name];remap_uv(ob,a['tile'],a['size'])
        for mat in list(bpy.data.materials):
            if mat.name in definitions:
                f=dict(definitions[mat.name])
                if mat.name=='mtl_tod_alarm_lamp_on':f['scaleRGB']=definitions['mtl_tod_alarm_lamp_high_on']['scaleRGB']
                bind_material(mat,f,texdir)
        bpy.ops.wm.save_as_mainfile(filepath=str(art/'visibility_review/high_fixture.blend'))
    receipt={'family':family,'native_lods':len(manifest['models']),'updated_maps':len(newmaps),
             'parts':len(assignments),'staged':str(STAGE),'baseline_inputs':{str(p.relative_to(BASE)):sha(p) for p in BASE.rglob('*') if p.is_file() and family in str(p)}}
    (review/'authoring_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('SURFACE_REALISM_STAGED',json.dumps({k:v for k,v in receipt.items() if k!='baseline_inputs'}),flush=True)
