"""MCP finish pass: correct three donor body/fragment bindings, no mesh changes."""
import pathlib,hashlib,json
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=ROOT/'source_data/tod_cyber_elites.gdt';text=p.read_text()
for field,old,new in [('legDmg2','s_rlegspawn','g_rlegoff'),('leftarm_gibmodel','g_larmoff','s_larmspawn'),('leftleg_gibmodel','g_llegoff','s_llegspawn')]:
    prefix='tod_charcoal_c_zom_dlc3_zombie_sentinel_'
    old_text='"'+field+'" "'+prefix+old+'"';new_text='"'+field+'" "'+prefix+new+'"'
    assert text.count(old_text)==1,(field,'expected original binding once')
    text=text.replace(old_text,new_text)
p.write_text(text)
manifest=ROOT/'art/cyber_elites/manifest.json';m=json.loads(manifest.read_text())
m['gdt_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
m['donor_binding_corrections']={'legDmg2':'g_rlegoff','leftarm_gibmodel':'s_larmspawn','leftleg_gibmodel':'s_llegspawn'}
manifest.write_text(json.dumps(m,indent=2))
print('Corrected right-leg damaged body and detached left arm/leg references; all source meshes remain unchanged.')
