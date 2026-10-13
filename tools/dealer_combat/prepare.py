"""Prepare the complete source change OUTSIDE live scripts; no deployment or receipt edits."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGE = ROOT / 'tmp/dealer_combat_stage'


def change(rel, edits, tail=''):
    original = (ROOT / rel).read_bytes()
    text = original.decode('utf-8')
    nl = '\r\n' if b'\r\n' in original else '\n'
    for before, after in edits:
        before, after = before.replace('\n', nl), after.replace('\n', nl)
        assert text.count(before) == 1, (rel, before[:100], text.count(before))
        text = text.replace(before, after)
    if tail:
        text += nl + tail.replace('\r\n', '\n').replace('\n', nl)
    out = STAGE / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode('utf-8'))
    return {'before': hashlib.sha256(original).hexdigest(), 'after': hashlib.sha256(out.read_bytes()).hexdigest()}


def main():
    clips = json.loads((STAGE / 'xanim_export/tod_dealer/combat_clips.json').read_text())
    resources = ['tools/dealer_boss/18_combat_clips.py', 'tools/dealer_boss/author_clips.py',
                 'art/dealer_boss/skeleton.json']
    donors = json.loads((ROOT/'art/dealer_boss/donors/manifest.json').read_text())
    resources += ['art/dealer_boss/donors/'+donors['models'][k]['file'] for k in ('dg2','dingo')]
    for item in clips['clips'].values():
        source = None
        for folder in ('art/dealer_boss/clips_src', 'xanim_export/tod_keeper', 'xanim_export/tod_dealer'):
            hits = [p for p in (ROOT/folder).iterdir() if p.stem == item['source']]
            if hits:
                assert len(hits) == 1, item['source']
                source = hits[0]
                break
        assert source, item['source']
        resources.append(source.relative_to(ROOT).as_posix())
    clips['inputs'] = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in resources}
    (STAGE/'xanim_export/tod_dealer/combat_clips.json').write_text(json.dumps(clips,indent=2))
    defines = '''#define TOD_DC_OPENING_GRACE  6.0
#define TOD_DC_POLL           0.05
#define TOD_DC_RANGE          2800
#define TOD_DC_TARGET_MAX     4
#define TOD_DC_RADIUS         100
#define TOD_DC_HEIGHT         90
#define TOD_DC_SHOT_RADIUS    24
#define TOD_DC_SHOCK_TELL     1.8
#define TOD_DC_BURST_TELL     1.3
#define TOD_DC_SHOCK_GAP      8.0
#define TOD_DC_BURST_GAP      5.0
#define TOD_DC_RECOVERY       0.65
#define TOD_DC_SHOCK_LIFE     0.45
#define TOD_DC_SHOCK_DAMAGE   30
#define TOD_DC_SHOT_DAMAGE    8
#define TOD_DC_BURST_SHOTS    6
#define TOD_DC_SHOT_GAP       0.25
#define TOD_DC_SHOT_TRAVEL    0.10
#define TOD_DC_FX_WARNING     "tod/dealer_combat/fx_dc_warning"
#define TOD_DC_FX_CHARGE      "tod/dealer_combat/fx_dc_charge"
#define TOD_DC_FX_SHOCK       "tod/dealer_combat/fx_dc_shock"
#define TOD_DC_FX_MUZZLE      "tod/dealer_combat/fx_dc_muzzle"
#define TOD_DC_FX_TRACER      "tod/dealer_combat/fx_dc_tracer"
#define TOD_DC_SND_WARNING    "tod_dc_warning"
#define TOD_DC_SND_BURST_TELL "tod_dc_burst_tell"
#define TOD_DC_SND_SHOCK      "tod_dc_shock"
#define TOD_DC_SND_SHOT       "tod_dc_shot"
'''
    defines += '#define TOD_DC_LMG_MUZZLE (' + ', '.join(str(v) for v in clips['weapon_muzzles']['dingo']) + ')\n'
    precaches = ''.join('#precache( "fx", "tod/dealer_combat/fx_dc_%s" );\n' % n for n in ('warning', 'charge', 'shock', 'muzzle', 'tracer'))
    rel = 'scripts/zm/zm_tod2_cybercity/_tod_dealer_finale.gsc'
    edits = [
        ('// NOT YET (docs/199 s4): the Wunderwaffe shock, the machine-gun bursts, the adds.',
         '// WEAPON PASS (2026-10-07): warned Wunderwaffe strikes and fixed-aim Dingo bursts. No adds.'),
        ('#namespace tod_dealer_finale;', '#using_animtree( "generic" );\n\n' + precaches + '\n' + defines + '\n#namespace tod_dealer_finale;'),
        ('INIT rev=2 spawner=', 'INIT rev=3 spawner='),
        ('actor.tod_dealer_state = 1;', 'actor.tod_dealer_state = 1;\n\tactor.tod_dealer_attack_serial = 0;\n\tactor.tod_dealer_attacking = false;'),
        ('actor thread brain();', 'actor thread brain();\n\tactor thread combat();'),
        ('function mask_crack()\n{', 'function mask_crack()\n{\n\tself dc_cancel( "phase" );'),
        ('self.ignoreall = false;\n\t\t\tself ASMSetAnimationRate( 1.0 );',
         'self.ignoreall = ( IS_TRUE( level.tod_dealer_hold ) || IS_TRUE( self.tod_dealer_attacking ) || ( self dc_disabled() ) );\n\t\t\tself ASMSetAnimationRate( 1.0 );'),
        ('self.ignoreall = false;\n\t\t\twas_held = false;',
         'self.ignoreall = ( IS_TRUE( level.tod_upgrade_pause ) || IS_TRUE( self.tod_dealer_attacking ) || ( self dc_disabled() ) );\n\t\t\twas_held = false;'),
        ('// STUCK: not moved', 'if ( IS_TRUE( self.tod_dealer_attacking ) || ( self dc_disabled() ) ) continue;\n\t\t// STUCK: not moved'),
        ('// THE BURST before the reward:', 'self dc_cancel( "death" );\n\t\t// THE BURST before the reward:'),
        ('now = GetTime();\n\tif ( isdefined( level.tod_dealer_hit_ms )',
         'if ( !isdefined( sMeansOfDeath ) || sMeansOfDeath != "MOD_MELEE" ) return -1;\n\tnow = GetTime();\n\tif ( isdefined( level.tod_dealer_hit_ms )'),
    ]
    files = {rel: change(rel, edits, pathlib.Path(__file__).with_name('combat_functions.gsc').read_text())}
    rel = 'scripts/zm/zm_tod2_cybercity/_tod_house.gsc'
    files[rel] = change(rel, [
        ('IS_TRUE( eAttacker.tod_dealer ) && isdefined( level.tod_house_swipes )',
         'IS_TRUE( eAttacker.tod_dealer ) && isdefined( level.tod_house_swipes ) && isdefined( sMeansOfDeath ) && sMeansOfDeath == "MOD_MELEE"'),
        ('wait 1.5;   // his last word, the body',
         'wait ( TOD_HOUSE_DEATH_LINE_DELAY + tod_shop_vo::secs( "tod_house_vo_death" ) + 0.25 );   // his full last word before the reward screen\n\tdev_log( "DEATH_LINE_COMPLETE" );'),
    ])
    rel = 'scripts/zm/zm_tod2_cybercity/_tod_bosses.gsc'
    files[rel] = change(rel, [
        ('// non-player attacker carrying it hits this much harder. Same place as the',
         '// non-player melee attacker carrying it hits this much harder. Ranged attacks\n\t// have their own tuned damage; do not multiply them by the swing bonus. Same place as the'),
        ('if ( isdefined( eAttacker ) && !isplayer( eAttacker ) && isdefined( eAttacker.tod_keeper_dmg ) )',
         'if ( isdefined( eAttacker ) && !isplayer( eAttacker ) && isdefined( eAttacker.tod_keeper_dmg ) && isdefined( sMeansOfDeath ) && sMeansOfDeath == "MOD_MELEE" )'),
    ])
    (STAGE / 'inputs.json').write_text(json.dumps(files, indent=2))
    blocks = []
    for clip in clips['clips']:
        blocks.append('\t"%s" ( "xanim.gdf" )\n\t{\n\t\t"model" "tod_keeper\\\\c_zom_dlc4_keeper_fb.XMODEL_BIN"\n\t\t"filename" "tod_dealer\\\\%s.xanim_bin"\n\t\t"type" "delta"\n\t\t"useBones" "1"\n\t\t"looping" "0"\n\t\t"loopsync" "0"\n\t}' % (clip, clip))
    dest = STAGE/'source_data/tod_dealer_combat.gdt'
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text('{\n'+'\n'.join(blocks)+'\n}\n',newline='\n')
    print('DEALER COMBAT STAGED: three scripts; live sources unchanged')


if __name__ == '__main__':
    main()
