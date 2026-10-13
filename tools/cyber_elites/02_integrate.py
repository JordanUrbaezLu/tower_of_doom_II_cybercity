"""One-time Hellbound Mangler port and map integration. Writes this repo only."""
from pathlib import Path
import re,json,csv,shutil
ROOT=Path(__file__).resolve().parents[2]; HB=ROOT.parent/'tower_of_doom_II_hellbound'
MOD=ROOT/'scripts/zm/zm_tod2_cybercity'
src=(HB/'scripts/zm/zm_tower_of_doom_ii/_tod_mangler.gsc').read_text(encoding='utf-8-sig')
src=src.replace('zm_tower_of_doom_ii','zm_tod2_cybercity')
for name in ['descent_data','start_maze_data','citadel_swords','difficulty','upgrades']:
    src=re.sub(r'^#using .*_tod_'+name+r';[^\n]*\n','',src,flags=re.M)
src=re.sub(r'^#insert .*_tod_(mangler_variants|roster)\.gsh;[^\n]*\n','',src,flags=re.M)
src=re.sub(r'^#precache\( "fx", "acc/light/fx_perk_glow_red".*\n','',src,flags=re.M)
src=src.replace('#insert scripts\\shared\\shared.gsh;', '\n'.join('#using scripts\\zm\\zm_tod2_cybercity\\_tod_'+n+';' for n in ['doppelghast','luck','perk_scatter'])+'\n#insert scripts\\shared\\shared.gsh;')
def replace_function(text,name,new):
    start=re.search(r'^function '+name+r'\(',text,re.M).start()
    end=text.index('\n}',start)+2
    return text[:start]+new+text[end:]
src=replace_function(src,'configure_variant','''function configure_variant( actor )
{
    actor.tod_mangler_black = false;
    actor.tod_mangler_color = "normal";
    actor.tod_mangler_variant = "normal";
    actor.tod_mangler_speed = 1;
    actor.tod_mangler_hp_zombies = 5;
    actor.tod_mangler_cannon_rate = TOD_MANGLER_CANNON_RATE;
}''')
src=replace_function(src,'init','''function init()
{
    tod_bo6_audio::init();
    level.tod_mangler_generation = 0;
    dev_log( "INIT skin=default animations=Hellbound director=tod_cyber_elites" );
}''')
src=replace_function(src,'spawn_position','''function spawn_position( target )
{
    return tod_doppelghast::reloc_point( target );
}''')
src=replace_function(src,'valid_target','''function valid_target( p )
{
    return tod_doppelghast::valid_target( p );
}''')
src=src.replace('tod_bosses::boss_hp_zombies( level.round_number, actor.tod_mangler_hp_zombies, true )','tod_doppelghast::hunter_hp( actor.tod_mangler_hp_zombies )')
src=src.replace('    level thread life_watch( actor );','    actor thread death_watch();')
src=replace_function(src,'life_watch','''function death_watch()
{
    level endon( "end_game" );
    generation = self.tod_mangler_generation;
    self waittill( "death", attacker );
    if ( isdefined( attacker ) && isplayer( attacker ) )
        tod_luck::boss_kill( attacker, "mangler" );
    org = undefined;
    if ( isdefined( self ) ) org = self.origin;
    tod_bosses::grant_elite_reward( "MANGLER", attacker, org );
    dev_log( "DEATH generation=" + generation + " reward=elite_killer live=" + live_manglers().size );
    if ( isdefined( self ) )
    {
        tod_bo6_audio::death( self, "mangler" );
        self thread corpse_cleanup();
    }
}''')
src=src.replace('    if ( self.tod_mangler_black ) self SetModel( "hb_bo6_mangler_black" );\n','')
src=src.replace('    self thread tod_citadel_swords::watch_custom_enemy_death();\n','')
a=src.index('    // THE RARE BLACK VARIANT\'S TELL',src.index('function body_lights'))
b=src.index('    dev_log( "LIGHT_READY',a)
src=src[:a]+'    expected = 2;\n'+src[b:]
src=re.sub(r'    .*apply_projectile_slow.*\n','',src)
src=re.sub(r'    .*dev_log\( "CANNON_SLOW.*\n','',src)
src=re.sub(r'        behind_seal = .*?;','        behind_seal = false; // Cybercity relocates through its own door/zone frontier.',src)
for alias,origin in [('zmb_hellhound_prespawn','org'),('zmb_hellhound_bolt','org'),('hb_mangler_fire','muzzle'),('hb_mangler_impact','impact_org')]:
    src=src.replace('PlaySoundAtPosition( "'+alias+'", '+origin+' )','tod_perk_scatter::play_sound_at_origin( '+origin+', "'+alias+'" )')
src=src.replace('#precache( "fx", "hb/mangler/fx_hb_mangler_cannon_idle" );','#precache( "fx", "hb/mangler/fx_hb_mangler_cannon_idle" );\n#precache( "fx", "hb/mangler/fx_hb_mangler_projectile" );')
src=src.replace('if ( !isdefined( target ) || !zm_utility::is_player_valid( target ) )','if ( !valid_target( target ) )')
src=src.replace('&& zm_utility::is_player_valid( target )','&& valid_target( target )')
src=src.replace('&&\n                 DistanceSquared', '&&\n                 DistanceSquared')
src=src.replace('    host SetModel( "tag_origin" );\n    host.angles', '    if ( !isdefined( host ) ) return undefined;\n    host SetModel( "tag_origin" );\n    host.angles')
src=src.replace('    wave PlaySound( "hb_mangler_pulse" );','    if ( !isdefined( wave ) ) { dev_log( "CANNON_DENIED reason=entity_pool" ); return; }\n    wave PlaySound( "hb_mangler_pulse" );')
src=src.replace('            charge LinkTo( self, "tag_flash", (0,0,0), (0,0,0) );\n            charge thread expire_fx( windup, self );','            if ( isdefined( charge ) )\n            {\n                charge LinkTo( self, "tag_flash", (0,0,0), (0,0,0) );\n                charge thread expire_fx( windup, self );\n            }')
for host in ['bolt','flash','impact']:
    src=re.sub(r'^(\s*)'+host+r' thread expire_fx\((.*?)\);',r'\1if ( isdefined( '+host+r' ) ) '+host+r' thread expire_fx(\2);',src,flags=re.M)
# Remove donor history comments, retaining code and inline timing/API comments.
src=re.sub(r'^\s*//[^\n]*\n','',src,flags=re.M)
src='// Default Hellbound Mangler: original body, skin, six clips, sounds and cannon.\n// Cybercity owns round delivery, target/frontier checks and killer rewards.\n// No donor rare variants, class-path player slows or continuous replacement.\n'+src
(MOD/'_tod_mangler.gsc').write_text(src)

# Tables/snapshot and the unchanged donor effects. Native model/images/anims are
# already installed in the private tools root and audited before the build.
for name in ['hb_mangler.ai_am','hb_mangler.ai_ast']:
    shutil.copy2(HB/'animtables'/name,ROOT/'animtables'/name)
# Scripted %anims must also enter the actor's generic tree through its mapping
# table. A zone xanim line alone only packs the clip (load error 2026-09-25).
am=ROOT/'animtables/hb_mangler.ai_am';table=am.read_text()
if not any('hb_mangler_cannon' in row.split(',')[1:] for row in table.splitlines()):
    am.write_text(table.rstrip()+'\nanim_zombie_mangler_cannon,hb_mangler_cannon\n')
shutil.copy2(HB/'source_data/hb_mangler.gdt',ROOT/'donor_gdt/hellbound/hb_mangler.gdt')
fx=ROOT/'share/raw/fx/hb/mangler';fx.mkdir(parents=True,exist_ok=True)
for p in (HB/'share/raw/fx/hb/mangler').glob('*.efx'):shutil.copy2(p,fx/p.name)
shutil.copy2(HB/'sound/aliases/hb_mangler.csv',ROOT/'sound/aliases/hb_mangler.csv')
with (HB/'sound/aliases/hb_bo6_enemy_audio.csv').open(newline='') as f:
    reader=csv.DictReader(f);header=reader.fieldnames;rows=list(reader)
# R5 (2026-10-04): only the Mangler aliases _tod_bo6_audio emits (the notetrack table, attach, death, PK02's timed
# cues and the heavy step); their Secondaries are added below. The rest of the BO6 set left with the Map 1 purge.
LIVE={'hb_bo6_fly_ai_mangler_cannon_charge','hb_bo6_fly_ai_mangler_cannon_preshot','hb_bo6_fly_ai_mangler_cannon_pullback',
      'hb_bo6_fly_ai_mangler_mvmt_melee','hb_bo6_fly_ai_mangler_spawn','hb_bo6_fly_ai_mangler_death_collapse',
      'hb_bo6_fly_ai_mangler_mvmt_heavystep_land'}
names={r['Name'] for r in rows if r['Name'] in LIVE}
while True:
    more={r['Secondary'] for r in rows if r['Name'] in names and r.get('Secondary')}
    if more<=names:break
    names |= more
selected=[r for r in rows if r['Name'] in names]
with (ROOT/'sound/aliases/hb_bo6_mangler.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,header);w.writeheader();w.writerows(selected)
with (ROOT/'sound/aliases/hb_mangler.csv').open(newline='') as f: selected+=list(csv.DictReader(f))
for r in selected:
    rel=Path(r['FileSpec'].replace('\\','/'));target=ROOT/'sound_assets'/rel
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HB/'sound_assets'/rel,target)
p=ROOT/'sound/zoneconfig/zm_tod2_cybercity.szc';szc=json.loads(p.read_text())
for name in ['hb_mangler','hb_bo6_mangler']:
    if not any(s['Filename']==name+'.csv' for s in szc['Sources']):szc['Sources'].append(dict(Type='ALIAS',Name=name,Filename=name+'.csv',Specs=[]))
p.write_text(json.dumps(szc,indent=1)+'\n')
print('Mangler default port, 2 AI tables, 3 unchanged FX and audio staged in Cybercity.')
