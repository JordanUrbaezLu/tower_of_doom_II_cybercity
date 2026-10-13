"""Prepare a reviewable patch for Archer; NEVER edits shared working files."""
import difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'art/cyber_sword/integration';OUT.mkdir(parents=True,exist_ok=True)
changes={};hashes={}
def replace(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)
rel='scripts/zm/zm_tod2_cybercity/_tod_class_kit.gsc';s=(ROOT/rel).read_text(encoding='utf-8-sig')
s=replace(s,'#using scripts\\zm\\zm_tod2_cybercity\\_tod_warrior_melee;',
    '#using scripts\\zm\\zm_tod2_cybercity\\_tod_cyber_sword;\n#using scripts\\zm\\zm_tod2_cybercity\\_tod_warrior_melee;')
s=s.replace('hb_gold_sword_cast_zm','tod_cyber_sword_cast_zm').replace('hb_warrior_bash_gold_zm','tod_cyber_sword_bash_zm')
s=replace(s,'function kit_switch( from, to )\n{','function kit_switch( from, to )\n{\n\tself tod_cyber_sword::update( false, "kit_switch" );')
s=replace(s,'\tself.tod_gs_busy = true;','\tself.tod_gs_busy = true;\n\tself tod_cyber_sword::update( false, "gravity_smash_cast" );')
s=replace(s,'\tkey = kit + ":" + lethal + ":" + tac;',
    '\t// Share the actual tier/busy/kill-charge/dev decision, before HUD throttling.\n\tself tod_cyber_sword::update( kit == TOD_KIT_WARRIOR && lethal == 0, "hud_readiness" );\n\tkey = kit + ":" + lethal + ":" + tac;')
changes[rel]=s
rel='scripts/zm/zm_tod2_cybercity.csc';s=(ROOT/rel).read_text(encoding='utf-8-sig')
anchor='#using scripts\\zm\\zm_tod2_cybercity\\_tod_archer;'
changes[rel]=replace(s,anchor,'#using scripts\\zm\\zm_tod2_cybercity\\_tod_cyber_sword;\n'+anchor)
rel='tools/gen_tod_twins.js';s=(ROOT/rel).read_text(encoding='utf-8-sig')
start=s.index("tier: 3, stem: 'cc_gold_sword'");end=s.index("name: 'Cyber Sword'",start)
part=s[start:end]
part=replace(part,"str: { altWeapon: '' }","str: { altWeapon: '', gunModel: 'tod_cyber_sword_view', worldModel: 'tod_cyber_sword_world' }")
part=part.replace('The user supplies the model.','Blender MCP art uses the original grip and animation skeleton.')
changes[rel]=s[:start]+part+s[end:]
rel='zone_source/zm_tod2_cybercity.zone';s=(ROOT/rel).read_text(encoding='utf-8-sig')
# Keep legacy donor assets for compatibility; new runtime callers use our package.
assert 'include,tod_cyber_sword' not in s
changes[rel]=s.rstrip()+'\n\ninclude,tod_cyber_sword\n'
patch=[]
for rel,new in changes.items():
    p=ROOT/rel;old=p.read_text(encoding='utf-8-sig');hashes[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    dst=OUT/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(new,encoding='utf-8')
(OUT/'shared_integration.patch').write_text(''.join(patch),encoding='utf-8')
(OUT/'base_hashes.json').write_text(json.dumps(hashes,indent=2))
print('CYBER_SWORD_PATCH_STAGED',len(changes),'shared files; working copies untouched; lead regeneration still required')
