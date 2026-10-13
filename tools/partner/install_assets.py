"""Install map-owned companion meshes. Never changes donor files or the shared tools.

The Protector keeps its native rig, animations and UVs and wears the Shadows of
Evil Civil Protector's own GOLD finish (W2A 2026-10-05; it wore a flat 4x4 blue
swatch on 41% of its body before): every donor material is cloned field-for-field
and given complete maps - the real ones where the pack has them, authored ones
(tools/companion_maps/) where no readable source does. Talon, R.A.P.S. and
Cerberus use their original T7 meshes with their ORIGINAL materials rebuilt from
the real T7 texture set (partner_materials: every definition cloned field-for-field
from the pack, every image a real pack / stock / authored texture; see the
manifest's "materials" section for what came from where). Run once; outputs
travel with repo. Run tools/companion_maps/compose.py first when its maps change.
"""
from pathlib import Path
import copy, hashlib, json, sqlite3, sys, struct, zlib, re

ROOT = Path(__file__).resolve().parents[2]
MT = Path('C:/BO3Tools/TOD2Cybercity')
OUT = ROOT/'model_export/tod_partner'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
db = sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro', uri=True)
db.execute('pragma writable_schema=ON')
db.row_factory = sqlite3.Row
blocks, records = [], []

def asset(kind, name):
    row = db.execute('select * from '+kind+' where _name=?', (name,)).fetchone()
    assert row, (kind, name)
    return {k:v for k,v in dict(row).items() if not k.startswith('_') and k != 'PK_id' and v is not None}

def block(name, kind, fields):
    def value(v):
        if isinstance(v, float) and v.is_integer(): return str(int(v))
        return str(v).replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n')
    blocks.append('\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join(
        '\t\t"'+k+'" "'+value(v)+'"\n' for k,v in fields.items())+'\t}\n')

def load(path):
    m=xmodel.Model();m.LoadFile_Bin(str(path),split_meshes=True);return m

def bounds(m):
    return [(min(v.offset[i] for me in m.meshes for v in me.verts),
             max(v.offset[i] for me in m.meshes for v in me.verts)) for i in range(3)]

def save(m,name,kind='rigid'):
    # Face object IDs MUST match the written object table after splitting parts.
    for i,me in enumerate(m.meshes):
        for f in me.faces:f.mesh_id=i
    dest=OUT/(name+'.xmodel_bin');m.WriteFile_Bin(str(dest))
    check=load(dest)
    assert sum(len(me.faces) for me in check.meshes)==sum(len(me.faces) for me in m.meshes)
    block(name,'xmodel',{'filename':'tod_partner\\\\'+dest.name,'type':kind,
        'BulletCollisionLOD':'None','ShadowLOD':'Auto','scale':1})
    records.append({'asset':name,'file':str(dest.relative_to(ROOT)).replace('\\','/'),
        'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bounds':bounds(check),
        'triangles':sum(len(me.faces) for me in check.meshes)})

def split_parts(m,short,axis,cut):
    for part in range(2):
        out=copy.deepcopy(m);kept=[]
        for me in out.meshes:
            me.faces=[f for f in me.faces if (sum(me.verts[c.vertex].offset[axis] for c in f.indices)/3 >= cut)==bool(part)]
            if not me.faces:continue
            used=sorted({c.vertex for f in me.faces for c in f.indices});remap={v:i for i,v in enumerate(used)}
            me.verts=[me.verts[i] for i in used]
            for f in me.faces:
                for c in f.indices:c.vertex=remap[c.vertex]
            kept.append(me)
        out.meshes=kept
        b=bounds(out);center=((b[0][0]+b[0][1])/2,(b[1][0]+b[1][1])/2,b[2][0])
        scale=min(1,34/max(high-low for low,high in b))
        for me in out.meshes:
            for v in me.verts:v.offset=tuple((v.offset[i]-center[i])*scale for i in range(3));v.weights=[(0,1)]
        # Rigid pickup pieces need only a root; retain root object shape.
        out.bones=out.bones[:1];out.bones[0].offset=(0,0,0);out.bones[0].parent=-1
        save(out,'tod_partner_'+short+'_part'+str(part+1))

sys.path.insert(0, str(Path(__file__).resolve().parent))
import partner_materials as pm
# Outputs are rebuilt from scratch: stale textures / retired flat swatches never linger.
for stale in list(pm.IMG_OUT.glob('i_tod_ptn_*.png'))+[OUT/('i_tod_partner_'+n+'.png') for n in
                                                       ['steel','dark','rubber','light','brass','enamel']]:
    stale.unlink(missing_ok=True)
pack=pm.pack_index()
res=pm.Resolver(pack)
material_log={}

# ---------------------------------------------------------------- Civil Protector: the SoE GOLD finish
# The gold rig's own skinOverride decides each definition (arm_gold -> the silver arm2; cloth / guts / lights / pelvis /
# torso -> their "2" twins); the four gold shells keep the donor's gold material (black 40% albedo under a gold spec
# tint, gloss to 17). A definition whose every map exists keeps its stock name (leg_2, guts2); every other one is
# cloned map-owned with COMPLETE maps. The stock gold shells sample $white_gloss / $white_specular (one uniform polish,
# no wear) and the upper shell's normal map exists in no source: GOLD_MAPS gives each shell the real wear of its
# steel finish's own gloss / spec maps (tools/companion_maps/compose.py) and the upper its authored normal.
PROTECTOR_FINISH='gold'   # LOCKSTEP: tools/artgen/packs/r1_comp_portraits.py PROTECTOR_FINISH (the HUD portrait)
GOLD_MAPS={'mtl_c_t7_zom_zod_robot_%s_gold'%p:dict({'cosinePowerMap':'i_c_t7_zom_zod_robot_%s_gold_g'%p,
                                                     'specColorMap':'i_c_t7_zom_zod_robot_%s_gold_s'%p},
                                                    **({'normalMap':'i_c_t7_zom_zod_robot_upper_n'} if p=='upper' else {}))
           for p in ['upper','leg','limbs','foot']}
donor=asset('xmodel','c_zom_zod_robot_protector_gold_fb')
src=MT/'model_export'/donor['filename'].replace('\\','/')
protector=load(src)
stock_skin={}
for line in re.split(r'\\+r\\+n',donor['skinOverride']):
    pair=line.split()
    if len(pair)==2:stock_skin[pair[0]]=pair[1]
res.prefetch({'i_t7_micro_concrete_bare_weathered_02_g'})   # cloth2's gloss tile: in the pack, not the stock tools
pro_new,pro_log={},[]
for mat in protector.materials:
    skin=stock_skin.get(mat.name,mat.name)
    d=pm.stock_material(res,skin)
    assert d,('no stock definition',skin)
    over=GOLD_MAPS.get(mat.name)
    maps={k:v for k,v in d.items() if isinstance(v,str) and v and not v.startswith('$') and pm.IMG_KEY.search(k)}
    if over is None and all(res.stock_ok(v) for v in maps.values()):
        pro_log.append({'original':mat.name,'skin':skin,'material':skin,'how':'stock definition, every map present',
                        'maps':maps,'missing':[]})
        mat.name=skin
        continue
    if skin not in pro_new:
        new='mtl_tod_ptn_pro_%02d'%len(pro_new)
        fields=res.material(skin,d,new,over)
        if fields.get('surfaceType') in (None,'','<none>'):fields['surfaceType']='metal'
        block(new,'material',fields)
        pro_new[skin]=new
        pro_log.append({'original':mat.name,'skin':skin,'material':new,'source':'stock gdt.db',
                        'how':('the donor gold material + its wear maps' if over else 'stock definition, maps completed'),
                        'materialType':fields.get('materialType'),
                        'maps':{k:v for k,v in fields.items() if isinstance(v,str) and v and pm.IMG_KEY.search(k)},
                        'missing':sorted({x for x,ws in res.missing.items() for w in ws if w.startswith(new+' ')})})
    mat.name=pro_new[skin]
material_log['protector']=pro_log
save(protector,'tod_partner_protector','animated')
split_parts(protector,'protector',2,40)
character=asset('character','c_zom_zod_robot_protector_gold');character['body']='tod_partner_protector'
block('tod_partner_protector_character','character',character)
ai=asset('aitype','spawner_ally_zod_robot_companion_gold_ar')
ai.update(character1='tod_partner_protector_character',radiantModel='tod_partner_protector',
          defaultGoalRadius=48,health=1500,usesCovernodes=0,grenadeAmmo=0)
block('spawner_tod_partner','aitype',ai)

# ---------------------------------------------------------------- Talon / R.A.P.S. / Cerberus
# Real materials: partner_materials clones each ORIGINAL definition from the T7 pack
# and binds the real textures. Evidence per material lands in the manifest.
PROPS='T7 Assets V2.8/model_export/_midgetblaster/props/'
DONORS=[  # short, tag, donor folder, split axis, split cut
    ('talon','tal','t7_veh/veh_t7_drone_attack_gun_darkcolor',1,0),
    # The MP RAPS (veh_t7_drone_raps_mp_dark) has no definition for 35% of its
    # triangles and none of its reveal masks in the pack; the zombies RAPS below
    # has every material defined and every per-model map present.
    ('raps','rap','p7_zm_stalingrad/veh_t7_dlc_drone_raps_nikolai',2,15),
    ('cerberus','cer','t7_veh/veh_t7_drone_amws_armored_mp_dark',2,20)]
RAPS_FIT='t7_veh/veh_t7_drone_raps_mp_dark'   # the zombies RAPS is scaled to this size
# Same UV layout, clean (undamaged) versions of maps the pack lacks under their live names.
SUBST={'i_veh_t7_drone_attack_body_n':'i_veh_t7_drone_attack_body_litecolor_test_n',
       'i_veh_t7_drone_attack_body_o':'i_veh_t7_drone_attack_body_dead_o',
       'i_veh_t7_drone_attack_body_tile_r':'i_veh_t7_drone_attack_body_litecolor_test_m',
       'i_t7_dirt_chunky_01_lt_c':'i_t7_dirt_chunky_01_c',
       # one layout, two names in the T7 definitions: the armored swingarm's reveal mask (authored once)
       'i_veh_t7_drone_amws_swingarm_armored_r':'i_veh_t7_drone_amws_armored_swingarm_tile_r',
       # the blast decal's spec mask exists nowhere; the stock simple spec is the definition family's default
       'i_t7_decal_damage_bullet_hits_lrg_01_s':'$spec_simple'}
# The per-model base maps of each part (what a borrowed template must point at).
PART_BASE={'talon':{'body':{'normalMap':'i_veh_t7_drone_attack_body_n','occMap':'i_veh_t7_drone_attack_body_o',
                            'alphaRevealMap':'i_veh_t7_drone_attack_body_tile_r'},
                    'wing_gun':{'normalMap':'i_veh_t7_drone_attack_wing_gun_n','occMap':'i_veh_t7_drone_attack_wing_gun_o',
                                'alphaRevealMap':'i_veh_t7_drone_attack_wing_gun_tile_r'},
                    'gun':{'normalMap':'','occMap':'','alphaRevealMap':''}},
           'cerberus':{p:{'normalMap':'i_veh_t7_drone_amws_'+p+'_n','occMap':'i_veh_t7_drone_amws_'+p+'_o',
                          'alphaRevealMap':'i_veh_t7_drone_amws_'+p+'_tile_r'}
                       for p in ['armored_hull','armored_turret','armored_treadcovers','armored_swingarm',
                                 'launcher','minigun','swingarm']}}
PART_BASE['cerberus']['wheels']={'normalMap':'i_t7_drone_amws_wheels_n','occMap':'i_veh_t7_drone_amws_wheels_o',
                                 'alphaRevealMap':'i_veh_t7_drone_amws_wheels_tile_r'}
PART_ALIAS={'hull':'armored_hull','turret':'armored_turret','treadcovers':'armored_treadcovers'}
# Sibling definitions in the SAME donor (same part = same UV layout = same base maps).
SIBLING={'talon':{'body':('drone_attack_body_mp_dark','drone_attack_body_bare_metal_mp_dark_titanium'),
                  'wing_gun':('drone_attack_wing_gun_mp_dark','drone_attack_wing_gun_bare_metal_mp_dark_titanium'),
                  'gun':('drone_attack_gun_mp_dark_highres',None)},
         'cerberus':{'wheels':('drone_amws_wheels_mp_dark_color',None),
                     'swingarm':('drone_amws_swingarm_mp_dark_color',None),
                     'armored_swingarm':('drone_amws_armored_swingarm_mp_dark_color',None),
                     'armored_hull':('drone_amws_armored_hull_mp_dark_color','drone_amws_armored_hull_bare_metal_mp_dark'),
                     'armored_turret':('drone_amws_armored_turret_mp_dark_color',None),
                     'armored_treadcovers':('drone_amws_armored_treadcovers_mp_dark_color',None),
                     'launcher':('drone_amws_launcher_mp_dark_color',None),
                     'minigun':('drone_amws_minigun_mp_dark_color','drone_amws_minigun_bare_metal_mp_dark_color')}}
DARK_SIBLING={'armored_hull':'drone_amws_armored_hull_dark_metal_mp_dark',
              'armored_turret':'drone_amws_armored_turret_dark_metal_mp_dark',
              'armored_treadcovers':'drone_amws_armored_treadcovers_dark_metal_mp_dark',
              'armored_swingarm':'drone_amws_armored_swingarm_dark_metal_mp_dark',
              'launcher':'drone_amws_launcher_thick_metal_mp_dark'}
# Real T7 definitions for a finish the donor never defined (base maps re-pointed to the part).
ROLE_TEMPLATE=[('chrome','mtl_veh_t7_dlc_forklift_modular_drone_chrome'),
               ('rubber','mtl_veh_t7_dlc_forklift_modular_drone_rubber'),
               ('plastic','mtl_veh_t7_dlc_forklift_modular_drone_plastic'),
               ('red_paint','mtl_veh_t7_drone_rcxdh_tile_bomb_plastic_red'),
               ('grenade','mtl_veh_t7_drone_amws_armored_turret_grenade02_mp_dark')]
GENERIC_DARK='mtl_veh_t7_drone_amws_armored_hull_dark_metal_mp_dark'
GENERIC_BARE='mtl_veh_t7_drone_amws_armored_hull_bare_metal_mp_dark'
# An undefined decal -> the T7 definition of that same decal; bolts without art -> the stock bolt.
DECAL_ALIAS={'mtl_veh_t7_decal_greeble_10':'mtl_veh_t7_dlc_decal_greeble_10',
             'mtl_veh_t7_decal_bolt_09':'mtl_veh_t7_dlc_mech_tank_decal_bolt_09',
             # the Cerberus minigun's barrel soot: the stock definition + art of that same burnt-stain decal (W2A)
             't7_decal_grunge_burnt_stain_01_gun_barrel_char':'t7_decal_grunge_burnt_stain_01'}
BOLT_FALLBACK='mtl_t7_veh_decal_bolt_01'

def definition(name):
    d=pack.get(name)
    if d and d.get('_kind')=='material.gdf':return d,'pack:'+d['_file']
    d=pm.stock_material(res,name)
    return (d,'stock gdt.db') if d else (None,None)

def part_of(short,name):
    for p in sorted(list(PART_BASE.get(short,{}))+list(PART_ALIAS),key=len,reverse=True):
        if '_'+p+'_' in name+'_':return PART_ALIAS.get(p,p)
    return None

def plan(short,name):
    """(fields, source, overrides, how) for one original material, or None to drop its faces."""
    d,src=definition(name)
    if d:
        if 'decal' in d.get('materialType',''):
            c=d.get('colorMap','')
            if c and not c.startswith('$') and not res.stock_ok(c) and res.find_file(SUBST.get(c,c)) is None:
                if 'bolt' in name:
                    b,bs=definition(BOLT_FALLBACK);return b,bs,None,'bolt decal art not in pack -> stock '+BOLT_FALLBACK
                return None
        return d,src,None,'original definition'
    if name in DECAL_ALIAS:
        d,src=definition(DECAL_ALIAS[name]);return d,src,None,'same decal, T7 definition '+DECAL_ALIAS[name]
    if 'decal' in name:
        if 'bolt' in name:
            d,src=definition(BOLT_FALLBACK);return d,src,None,'bolt decal undefined -> stock '+BOLT_FALLBACK
        return None
    part=part_of(short,name)
    if part is None:return None
    base=PART_BASE[short][part]
    paint,bare=SIBLING[short][part]
    for key,tmpl in ROLE_TEMPLATE:
        if key in name:
            d,src=definition(tmpl);return d,src,dict(base),'undefined '+key+' -> T7 '+tmpl+' on the '+part+' maps'
    if any(k in name for k in ['bare_metal','titanium']):
        t='mtl_veh_t7_'+bare if bare else GENERIC_BARE
        d,src=definition(t);return d,src,(None if bare else dict(base)),'undefined bare metal -> T7 '+t+' on the '+part+' maps'
    if any(k in name for k in ['dark_metal','thick_metal','metal_dark']):
        t='mtl_veh_t7_'+DARK_SIBLING[part] if part in DARK_SIBLING else GENERIC_DARK
        d,src=definition(t)
        return d,src,(None if part in DARK_SIBLING else dict(base)),'undefined dark metal -> T7 '+t+' on the '+part+' maps'
    if any(k in name for k in ['colored_metal','_color']):
        t='mtl_veh_t7_'+paint;d,src=definition(t);return d,src,None,'undefined painted metal -> sibling '+t
    return None

def retexture(short,tag,m):
    names=[mat.name for mat in m.materials]
    # One 7-Zip pass for every pack texture any candidate definition can use,
    # BEFORE planning (a decal is only kept when its colour art really exists).
    cands=set(names)|set(DECAL_ALIAS.values())|{BOLT_FALLBACK,GENERIC_DARK,GENERIC_BARE}
    cands|={t for k,t in ROLE_TEMPLATE}|{'mtl_veh_t7_'+x for p in SIBLING.get(short,{}).values() for x in p if x}
    cands|={'mtl_veh_t7_'+x for x in DARK_SIBLING.values()}
    want={v for base in PART_BASE.get(short,{}).values() for v in base.values()}|set(SUBST.values())
    for n in cands:
        d,src=definition(n)
        for k,v in (d or {}).items():
            if isinstance(v,str) and pm.IMG_KEY.search(k):want.add(SUBST.get(v,v))
    res.prefetch(want)
    plans={n:plan(short,n) for n in names}
    newname,log,count={},[],{}
    for me in m.meshes:
        for f in me.faces:count[f.material_id]=count.get(f.material_id,0)+1
    for i,n in enumerate(names):
        pl=plans[n]
        if pl is None:
            log.append({'original':n,'triangles':count.get(i,0),'result':'DROPPED (no definition or art in the pack)'});continue
        d,src,ov,how=pl
        mname='mtl_tod_ptn_%s_%02d'%(tag,len(newname))
        assert len(mname)<32
        fields=res.material(n,d,mname,ov,SUBST)
        if fields.get('surfaceType') in (None,'','<none>'):fields['surfaceType']='metal'   # stock decals carry <none>
        block(mname,'material',fields)
        newname[i]=mname
        log.append({'original':n,'material':mname,'triangles':count.get(i,0),'source':src,'how':how,
                    'materialType':fields.get('materialType'),
                    'maps':{k:v for k,v in fields.items() if isinstance(v,str) and v and pm.IMG_KEY.search(k)},
                    'missing':sorted({x for x,ws in res.missing.items() for w in ws if w.startswith(mname+' ')})})
    material_log[short]=log
    # Drop faces with no real material, prune and remap the material table.
    keep=sorted(newname);remap={old:new for new,old in enumerate(keep)}
    for me in m.meshes:me.faces=[f for f in me.faces if f.material_id in remap]
    m.meshes=[me for me in m.meshes if me.faces]
    for me in m.meshes:
        used=sorted({c.vertex for f in me.faces for c in f.indices});vr={v:j for j,v in enumerate(used)}
        me.verts=[me.verts[v] for v in used]
        for f in me.faces:
            f.material_id=remap[f.material_id]
            for c in f.indices:c.vertex=vr[c.vertex]
    m.materials=[m.materials[i] for i in keep]
    for j,i in enumerate(keep):m.materials[j].name=newname[i]

def donor_path(folder):
    name=folder.split('/')[-1]
    rel=PROPS+folder+'/'+name+'_LOD0.xmodel_bin'
    for base in (pm.PACK.parent,pm.STAGE.parent):
        if (base/rel).exists():return base/rel
    pm.extract([name+'_LOD0.xmodel_bin'])
    assert (pm.PACK.parent/rel).exists(),rel
    return pm.PACK.parent/rel

def scale_to(m,ref):
    # Same footprint as the partner it replaces (gameplay spacing/pivot unchanged).
    rb,mb=bounds(ref),bounds(m)
    s=max(h-l for l,h in rb)/max(h-l for l,h in mb)
    for me in m.meshes:
        for v in me.verts:v.offset=tuple(x*s for x in v.offset)
    for b in m.bones:b.offset=tuple(x*s for x in b.offset)
    return s

raps_scale=None
for short,tag,folder,axis,cut in DONORS:
    m=load(donor_path(folder))
    retexture(short,tag,m)
    if short=='raps':raps_scale=scale_to(m,load(donor_path(RAPS_FIT)))
    split_parts(m,short,axis,cut)
    if short=='raps':
        # The visible sphere rotates about its center, not its floor pivot.
        b=bounds(m);cz=(b[2][0]+b[2][1])/2
        for me in m.meshes:
            for v in me.verts:v.offset=(v.offset[0],v.offset[1],v.offset[2]-cz)
        for bone in m.bones:bone.offset=(bone.offset[0],bone.offset[1],bone.offset[2]-cz)
    save(m,'tod_partner_'+short)

for name,fields in sorted(res.images.items()):block(name,'image',fields)

(ROOT/'source_data/tod_partners.gdt').write_text('{\n'+''.join(blocks)+'}\n',encoding='utf-8')
(OUT/'manifest.json').write_text(json.dumps({
        'finish':'Protector: the SoE Civil Protector GOLD finish on the native rig, every map complete. '
                 'Talon/R.A.P.S./Cerberus: original T7 meshes with their original T7 material definitions and real '
                 'T7 textures; maps no source holds are authored (art/companion_maps/authored, see images).',
        'protector_finish':PROTECTOR_FINISH,
        'models':records,
        'donors':{s:('_midgetblaster/props/'+f) for s,t,f,a,c in DONORS},
        'raps_scale_to_mp_size':raps_scale,
        'substitutions':res.subst_used,
        'materials':material_log,
        'images':res.sources,
        'stock_images_referenced':sorted(res.stock_used),
        'not_in_pack':res.missing},indent=2)+'\n')
print('Installed',len(records),'partner models into',OUT)
