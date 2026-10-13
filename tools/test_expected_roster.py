"""Check the requested roster against emitted assets and the runtime bindings."""
import csv
import json
import re
import wave
from inspect_expected_roster import ROOT, TOOLS, blocks


def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')


assets = blocks(ROOT / 'source_data/tod_weapon_twins.gdt')
classes = read('scripts/zm/zm_tod2_cybercity/_tod_classes.gsc')
upgrades = read('scripts/zm/zm_tod2_cybercity/_tod_upgrades.gsc')
zone = read('zone_source/tod_twins.zpkg')
rows = list(csv.DictReader((ROOT / 'sound/aliases/tod_expected_roster.csv').open(newline='', encoding='utf-8-sig')))
aliases = {r['Name'] for r in rows}
# 2026-09-26: the NECROMANCER replaced the Skirmisher; only its tier 1 (the skull) exists.
roster = {'necromancer': ['tod_necro_skull', 'tod_necro_staff2', 'tod_necro_staff3'],
          'assault': ['cc_bow', 'cc_crossbow', 'cc_fire_bow'],
          'heavy': ['cc_mozambique', 'cc_rem870', 'cc_peacekeeper'],
          # 2026-09-26: the Warrior is fists -> gauntlet -> sword (One Inch Punch, Gauntlet of Siegfried, Gold Battle Sword)
          'slasher': ['cc_punch', 'cc_gauntlet', 'cc_gold_sword']}
for cls, guns in roster.items():
    for tier, stem in enumerate(guns, 1):
        assert re.search(r'register_gun\(\s*"'+cls+r'",\s*'+str(tier)+r',\s*"'+stem+r'"', classes), (cls,tier,stem)

new = {'tod_necro_staff2': 2, 'tod_necro_staff3': 2, 'tod_necro_skull': 2, 'cc_bow': 40, 'cc_crossbow': 40, 'cc_fire_bow': 40,   # 32 since 2026-09-28 (QUICK DRAW s0..s3); 24 then; 8 until 2026-09-27 class pass 4 (user): DEADEYE d0..d3 x SHOT SPEED s0..s2 x base/up
         # 2 until 2026-09-27: DEADEYE's d0..d3 forms, base + PaP
       'cc_punch': 8, 'cc_gauntlet': 8, 'cc_gold_sword': 8}   # k0..k3 x base/PaP since 2026-09-28 (was 12: k0..k5)   # 13 until the dark k6 rung retired (2026-09-26)
# build 18: the gauntlet's LEFT-HAND TWINS (gen_tod_twins GAUNTLET_ALT_TWINS, LOCKSTEP with
# _tod_warrior_melee TOD_GAUNTLET_ALT_TWINS) double its forms: <form>_l_zm for every rung.
gen_src = read('tools/gen_tod_twins.js')
alt_gen = re.search(r'^const GAUNTLET_ALT_TWINS = (true|false);', gen_src, re.M)
alt_gsc = re.search(r'^#define TOD_GAUNTLET_ALT_TWINS\s+(\d)', read('scripts/zm/zm_tod2_cybercity/_tod_warrior_melee.gsc'), re.M)
assert alt_gen and alt_gsc, 'GAUNTLET_ALT_TWINS / TOD_GAUNTLET_ALT_TWINS missing'
alt_twins = alt_gen.group(1) == 'true'
assert alt_twins == (alt_gsc.group(1) == '1'), 'GAUNTLET_ALT_TWINS (gen_tod_twins) and TOD_GAUNTLET_ALT_TWINS (_tod_warrior_melee) disagree'
if alt_twins: new['cc_gauntlet'] = 16
# NO PUNCH LUNGE (user 2026-10-05) needs the cone fallback: a punch the engine missed takes the first zombie in its cone
assert 'if ( extra < 1 && !( self engine_landed( token ) ) ) extra = 1;' in read('scripts/zm/zm_tod2_cybercity/_tod_warrior_melee.gsc'), 'the punch has no lunge, so a missed punch must take the first zombie in its cone'
for stem, count in new.items():
    variants = {n:d['fields'] for n,d in assets.items() if n.startswith(stem+'_') and d['type'].endswith('weapon.gdf')}
    assert len(variants) == count, (stem,len(variants),count)
    for name, f in variants.items():
        assert 'weapon,'+name in zone, name
        assert not f.get('altWeapon'), (name, 'unregistered charge or alternate weapon')
        assert f.get('gunModel') and f.get('worldModel'), name
        if stem in ('cc_bow','cc_fire_bow'):
            assert f['startAmmo'] == f['clipSize'] and f['maxAmmo']=='0', (name, 'quiver must start full')
        if stem.startswith('tod_necro_'):
            assert f['inventoryType']=='primary' and f['clipSize']=='100', name
            assert f['loopFireSoundPlayer']=='zmb_wpn_skullgun_loop_plr' and f['loopFireSound']=='zmb_wpn_skullgun_loop_npc'
        if stem in roster['slasher']:
            tier=roster['slasher'].index(stem)
            assert int(f['meleeDamage'])==[1600,3200,5440][tier]*(2 if '_up_' in name else 1)
            assert float(f['meleeLungeRange'])==0
            # NO WARRIOR WEAPON LUNGES (user 2026-10-05: the punch lunge was "causing some screen issues ...
            # just punching and then using our calculated radius"); the gauntlet's juke is 0 too, the sword has none
            if stem=='cc_punch':
                assert float(f['meleeChargeRange'])==0, (name,'no punch lunge (user 2026-10-05)')
                assert float(f['meleeDelay'])==0.1, (name,'punch hit delay')
                # build 16: the Bash proxy swap waits the drop time; 0 = the fist is up for the dash
                assert float(f['dropTime'])==0 and float(f['quickDropTime'])==0, (name,'punch drop time must be 0 (Bash)')
            # both hands swing at the same speed on every form (Knife Speed / PaP scale meleeLeftTime too)
            if f.get('meleeLeftAnim'):
                assert f['meleeLeftTime']==f['meleeTime'], (name,'left swing out of step with the right')
            if stem=='cc_gauntlet':
                assert float(f['meleeJuke'])==0, (name,'gauntlet swing must not dash')
                # build-16 playtest: the boxing gloves' "brawler" set put the LEFT punch on the AIM button
                # (user: "that button shouldn't do anything with the gauntlet") - reverted to the donor's
                assert f['meleeWithLeftHand']=='0', (name,'no left punch on AIM')
                assert f['playerAnimType']=='onehanded', (name,'brawler puts the left punch on AIM')
                # The alternating twin swap owns the end-of-swing input window.
                # Native early queuing can repeat the same hand before that swap.
                assert f['meleeServerResponse']=='0' and float(f['meleeQueueMeleeEarlyTime'])==0, (name,'no native early queue before the hand swap')
                assert float(f['meleeChargeRange'])==0, (name,'no gauntlet lunge (user)')
                assert float(f['dropTime'])==0 and float(f['quickDropTime'])==0, (name,'gauntlet drop time must be 0 (Bash)')
                # build 17 proved a bulletweapon drops meleeAltAnim: the dead keys are gone
                assert 'meleeAltAnim' not in f and float(f.get('meleeAltAnimTime','0'))==0, (name,'dead alt-melee keys shipped')
                assert f.get('meleeLeftAnim','')=='', (name,'meleeLeftAnim stays clear (the left is its own twin)')
                # build 18: the left-hand twin swings the boxing left punch; the right its own swipe
                left = name.endswith('_l_zm')
                assert left <= alt_twins, (name,'a left twin with GAUNTLET_ALT_TWINS off')
                want = 'vm_tod_gauntlet_left_hook' if left else 'vm_z_aint_no_dragon_melee_swipe'
                for k in ('meleeAnim','meleeMissAnim','fireAnim'):
                    assert f[k]==want, (name,k,f[k],'want',want)
                if left:
                    assert name.replace('_l_zm','_zm') in variants, (name,'left twin without its right-hand rung')
                    assert f['meleeTime']==variants[name.replace('_l_zm','_zm')]['meleeTime'], (name,'left swing out of step with the right rung')
                    assert f['firstRaiseAnim']=='vm_z_aint_no_dragon_idle', (name,'the left twin must never play the first raise')
                if alt_twins:
                    # the swap after every punch must not show: both hands raise on the idle, instantly
                    for k in ('raiseAnim','quickRaiseAnim','emptyRaiseAnim'):
                        assert f[k]=='vm_z_aint_no_dragon_idle', (name,k,f[k])
                    for k in ('raiseTime','quickRaiseTime','emptyRaiseTime'):
                        assert float(f[k])<=0.05, (name,k,f[k])
                assert 'tag_body' in f['hideTags'].split('\\r\\n'), (name,'the whelp must be hidden')
            if stem=='cc_gold_sword':
                # MELEE SPEED (build-11 playtest): the k rungs scale the sword like every blade; PaP does not trim it (fixedSwing 'pap')
                k=int(re.search(r'_k(\d)',name).group(1))
                step=[1,0.85,0.76,0.70][k]   # LOCKSTEP gen_tod_twins KNIFE_STEP (2026-09-28)
                assert abs(float(f['meleeTime'])-1.033*step)<0.001 and abs(float(f['fireTime'])-1.033*step)<0.001, (name,'sword swing = 1.033 x MELEE SPEED step',f['meleeTime'],f['fireTime'])
                # the Gold Battle Sword became the CYBER SWORD (user 2026-09-26); the stem stays cc_gold_sword
                assert f['displayName']==('Cyber Sword EX' if '_up' in name else 'Cyber Sword'), (name,'tier 3 is the Cyber Sword')
            if stem!='cc_punch':
                assert float(f['meleeChargeRange'])==0, (name,'no lunge')

for stem in ['cc_saug','cc_m1927','cc_r99','cc_car','t5_enfield','t9_krig6','t9_ak47','t9_me_baseballbat','t9_me_wakizashi','leviathan',
             'cc_twin_knives','cc_plain_sword']:   # the Warrior's Hellbound knives / sword retired 2026-09-26
    assert not any(n.startswith(stem+'_') for n in assets), (stem,'retired generated weapon')
for name in ['cc_gold_sword_up_k6_zm']:   # the dark KNIFE SPEED rung retired whole 2026-09-26 (the sword ignores Knife Speed: fixedSwing); the R-99's h4 and the Archer's r3m4 went before it
    assert name not in assets, (name,'retired dark rung still generated')
# THE REPEATER (2026-10-05, docs/218; user: "the automatic guns on the first map were just so much fun ... hold down
# the shooting"): the tier-2 crossbow is a held full-auto repeater, 10 bolts (13 packed). It was one bolt and a reload
# (clipSize 1) until then; the old single-shot form fails here.
assert assets['cc_crossbow_d0s0']['fields']['clipSize']=='10' and assets['cc_crossbow_d0s0']['fields']['fireType']=='Full Auto', 'the crossbow is the held repeater'
assert assets['cc_crossbow_up_d0s0']['fields']['clipSize']=='13' and assets['cc_crossbow_up_d0s0']['fields']['fireType']=='Full Auto', 'the packed crossbow is the held repeater'
assert 'rune' in assets['cc_fire_bow_d0s0_zm']['fields']['gunModel'], 'Fire Bow must use installed Rune Prison model'
assert '"cc_gold_sword"' in upgrades

paths = set()
for row in rows:
    for key in ['ContextType','ContextValue','ContextType1','ContextValue1','ContextType2','ContextValue2','ContextType3','ContextValue3']:
        assert not row.get(key), (row['Name'],key)
    for key in ['FileSpec','FileSpecSustain','FileSpecRelease']:
        if row.get(key): paths.add(ROOT/'sound_assets'/row[key].replace('\\','/'))
for path in paths:
    assert path.is_file(), path
    with wave.open(str(path),'rb') as wav:
        assert wav.getnframes()>0 and wav.getnchannels() in (1,2), path
szc=json.loads(read('sound/zoneconfig/zm_tod2_cybercity.szc'))
assert 'tod_expected_roster' in json.dumps(szc) and 'elemental_bow_sounds' in json.dumps(szc)
assert (TOOLS/'share/raw/sound/aliases/elemental_bow_sounds.csv').is_file()

entry=read('scripts/zm/zm_tod2_cybercity.gsc')
# Dev/god are playtest settings, not permanent publish requirements.
# tod_dev_maxed left this list 2026-09-26 (user: "on dev mode, I shouldn't have any of my
# abilities locked out ... maxed out class ... all the classes"); the publish gate still refuses it armed.
# R5 (2026-10-04): the bat hoop and its dev probe left with the Map 1 purge; the flag must not come back.
cleanup=read('scripts/zm/zm_tod2_cybercity/_tod_corpse_cleanup.gsc')
assert 'tod_dev_hoop_probe' not in entry and 'tod_dev_hoop_probe' not in cleanup, 'the retired hoop probe flag is back'
assert '[TOD_ROSTER] READY' in read('scripts/zm/zm_tod2_cybercity/_tod_main.gsc')
assert '[TOD_ROSTER] REGISTER' in classes and 'GIVE' in classes
print(f'Expected roster PASS: 10 tier bindings, {sum(new.values())} new variants, dark rungs, full quivers, melee damage, {len(rows)} sound rows / {len(paths)} WAVs, no hoop probe.')
