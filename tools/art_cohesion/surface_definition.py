"""Material roles share baked construction, but retain deliberate color/finish."""
import json,pathlib
from profiles import apply
DEFINITIONS=json.loads((pathlib.Path(__file__).with_name('crown_materials.json')).read_text())['materials']
def definition(role):
    d=DEFINITIONS[role];prefix='i_tod_cc_'+d['tile']
    base=role[:-9] if role.endswith('_scorched') else role   # a scorched twin keeps its base role's finish (docs/205 s7b)
    f={'surfaceType':'metal','template':'material.template','materialCategory':'Geometry Advanced','materialType':'lit_emissive_advanced_fullspec','colorMap':prefix+'_c','normalMap':prefix+'_n','cosinePowerMap':prefix+'_g','specColorMap':prefix+'_s','specMapEnable':1,'colorMap00':prefix+'_e','colorTint':d['color'],'colorTint1':'1 1 1 1','scaleRGB':0,'emissiveIncompetence':1,'emissiveFalloff':0,'normalHeightScale':1,'textureAtlasRowCount':1,'textureAtlasColumnCount':1,'usage':'floor' if d['class']=='deck' else 'wall'}
    apply(f,'architecture')
    if base not in ('floor','wall','ceiling','trim'):
        factor=.22 if base in ('ceramic','velvet','graphite','oxblood') else .8 if base in ('gold','gold_panel','brass','bronze_wall') else .5
        f['specColorTint']=' '.join(f'{float(v)*factor:.5g}' for v in d['color'].split()[:3])+' 1'
    f['glossRangeMax']={'gold':9,'gold_panel':9,'brass':8,'bronze_wall':8,'ceramic':6,'velvet':5,'graphite':6,'oxblood':6}.get(base,7)
    return f
