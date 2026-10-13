"""Map-owned alarm integration; repeatable and restricted to this repository."""
import pathlib,re,sys,runpy
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
def edit(rel,fn):
    p=ROOT/rel;s=p.read_text(encoding='utf-8-sig');n=fn(s)
    if n!=s:p.write_text(n,encoding='utf-8')
def fall(s):
    imp='#using scripts\\zm\\zm_tod2_cybercity\\_tod_crown_alarm;'
    # BO3 rejects a #using below #precache. Keep imports in the header block.
    match=re.search(r'(?m)^'+re.escape(imp)+r'[^\n]*\n',s)
    if match is None or match.start()>s.index('#precache('):
        if match:s=s[:match.start()]+s[match.end():]
        anchor='#using scripts\\zm\\zm_tod2_cybercity\\_tod_crown_data;'
        assert anchor in s
        s=s.replace(anchor,imp+'\n'+anchor,1)
    if '\ttod_crown_alarm::init();' not in s:s=s.replace('\tlever_spawn();','\ttod_crown_alarm::init();\n\tlever_spawn();',1)
    if 'function alarm_spin()' in s:
        a=s.index('// THE BEACON:');b=s.index('// The siren:',a)
        s=s[:a]+'''// Physical fixtures share this existing alarm edge and siren anchor.
function alarm_start()
{
    level endon( "end_game" );
    if ( IS_TRUE( level.tod_crown_alarm_active ) || IS_TRUE( level.tod_fall_sealed ) )
        return;
    tod_crown_alarm::start();
    if ( IS_TRUE( level.tod_crown_alarm_active ) )
        level thread siren( tod_crown_data::alarm_org() );
}

'''+s[b:]
    s=re.sub(r'// The seal brings the beacon down:.*?^function alarm_stop\(\).*?^}', '''// The seal leaves the physical beacons mounted, dark and stationary.
function alarm_stop()
{
    siren_stop();
    tod_crown_alarm::stop();
}''',s,flags=re.S|re.M)
    s=re.sub(r'^#define TOD_FALL_(?:ALARM_FX|ORBIT_FX|ORBIT_SECS).*\n','',s,flags=re.M)
    a=s.index('//   * THE ALARM.');b=s.index('//   * THE POWER.',a)
    s=s[:a]+'''//   * THE ALARM. Thirty Blender-authored rotating red fixtures: all twelve
//     hall pillars, central pendant, sixteen crown points and the apex.
//     _tod_crown_alarm owns the models, red spot FX and off/on state. This
//     module retains the trigger, original 30-second siren and seal edge.
'''+s[b:]
    return s
edit('scripts/zm/zm_tod2_cybercity/_tod_fall.gsc',fall)
def csc(s):
    s=s.replace('light/fx_light_flashing_red_factory_zmb','tod/crown_alarm/fx_tod_alarm_sweep')
    if '\t// 11: THE FALL' in s:
        a=s.index('\t// 11: THE FALL');b=s.index('\tlevel._effect[ "tod_glow_11" ]',a)
        s=s[:a]+'\t// 11: tight red spotlight attached to each physical hall reflector.\n'+s[b:]
    return s
edit('scripts/zm/zm_tod2_cybercity/_tod_perk_lights.csc',csc)
def zone(s):
    s=re.sub(r'^fx,light/fx_light_flashing_red_factory_zmb.*\n','',s,flags=re.M)
    if 'include,tod_crown_alarm\n' not in s:s+='\ninclude,tod_crown_alarm\n'
    return s
edit('zone_source/zm_tod2_cybercity.zone',zone)
(ROOT/'zone_source/tod_crown_alarm.zpkg').write_text('''// Blender-authored physical red alarm beacons.
// Keep the model glass as a complete native material definition.
material,mc/mtl_tod_alarm_lens
scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_crown_alarm.gsc
xmodel,tod_crown_alarm_housing
xmodel,tod_crown_alarm_rotor_off
xmodel,tod_crown_alarm_rotor_on
xmodel,tod_crown_alarm_rotor_high_on
xmodel,tod_crown_alarm_housing_high
xmodel,tod_crown_alarm_rotor_high_off
fx,tod/crown_alarm/fx_tod_alarm_sweep
fx,tod/crown_alarm/fx_tod_alarm_high
// Small surface wires: independent power state, shared art initialization.
scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_power_conduits.gsc
scriptparsetree,scripts/zm/zm_tod2_cybercity/_tod_conduit_data.gsc
xmodel,tod_power_conduit_off
xmodel,tod_power_conduit_on
include,tod_power_conduits
''')
def sync(s):
    line='    Copy-Tree (Join-Path $RepoRoot "model_export\\tod_crown_alarm") (Join-Path $ModTools "model_export\\tod_crown_alarm") "physical red crown alarm models and textures" $false\n'
    if line.strip() not in s:
        s=re.sub(r'(    Copy-Tree .*"model_export\\tod_cyber_elites".*\n)',lambda m:m[1]+line,s)
    return s
edit('tools/sync_to_modtools.ps1',sync)

# Alarm-only writer also runs independently without touching shared integration.
runpy.run_path(str(ROOT/'tools/crown_alarm/04_tune_light.py'),run_name='__main__')

# Update prior tests to the new physical contract, retaining siren/switch tests.
def tests(s):
    s=s.replace("'tod_perk_lights::set_glow( core, TOD_FALL_ALARM_FX )'","'tod_crown_alarm::start();'")
    s=s.replace('light/fx_light_flashing_red_factory_zmb','tod/crown_alarm/fx_tod_alarm_sweep')
    s=s.replace("ok(zone.split(/\\r?\\n/).some(l => l.trim().startsWith('fx,tod/crown_alarm/fx_tod_alarm_sweep')), 'zone line for the alarm light');", "ok(read(path.join(root, 'zone_source/tod_crown_alarm.zpkg')).includes('fx,tod/crown_alarm/fx_tod_alarm_sweep'), 'alarm package includes the red sweep light');")
    s=s.replace("ok((map.match(/crown hall alarm (gantry|pendant|core)/g) || []).length === 3, 'the alarm housing: gantry, pendant, core');", "ok((map.match(/crown hall alarm (gantry|pendant|core)/g) || []).length === 2 && !map.includes('crown hall alarm core'), 'gantry and pendant support the modeled beacon; old cube removed');")
    return s
edit('tools/test_doppelghast.js',tests)
print('CROWN_ALARM_INTEGRATED: models, mounts, lifecycle, red spot, zone and guarded sync')
