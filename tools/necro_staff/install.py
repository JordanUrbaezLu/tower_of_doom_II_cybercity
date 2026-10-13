"""Generate map-owned staff weapon definitions; retain skull combat mechanics."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2]
def blocks(path):
    return {m[1]:dict(re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"',m[2])) for m in re.finditer(r'"([^"\n]+)"\s*\([^)]*\)\s*\{([^}]+)\}',path.read_text(encoding='latin1'))}
def emit(n,f):return '\t"'+n+'" ( "projectileweapon.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+v+'"\n' for k,v in f.items())+'\t}\n'
base=blocks(ROOT/'source_data/tod_necro_skull.gdt')
staff=blocks(ROOT/'archive/mage_retired/source_data/tod_staff.gdt')['tod_staff_ice']   # archived with its class 2026-10-04
anims=json.loads((ROOT/'art/necro_staff/animations.json').read_text())
out=[]
for tier in [2,3]:
    for up in [False,True]:
        name=f'tod_necro_staff{tier}'+('_up' if up else '')
        f=dict(base['tod_necro_skull_up' if up else 'tod_necro_skull'])
        # Clear every inherited skull animation before applying the complete staff set.
        for key in f:
            if key.endswith('Anim') or f[key].startswith('vm_zom_skull_'):f[key]=''
        # A long two-handed staff must also inherit native presentation scalars.
        # Skull sway/idle magnitudes and its un-suffixed swim animation do not fit.
        for key in f:
            if key.startswith(('sway','adsSway','adsIdle','adsAdditive','adsDof','adsGunKick','hipGunKick','adsViewKick','hipViewKick')) or key in ['adsAimPitch','adsBobFactor','adsViewBobMult','hipIdleAmount','hipIdleSpeed','swimCombatAdsFire']:
                if key in staff:f[key]=staff[key]
        f.update(anims['slots'])
        f.update(gunModel=f'tod_necro_staff{tier}_view',worldModel=f'tod_necro_staff{tier}_world',
                 handModel=staff.get('handModel',''),isHandModelOverridable=staff.get('isHandModelOverridable','1'),
                 viewmodelTag='tag_weapon_right',worldModelTagLeft='tag_weapon_right',worldModelTagRight='tag_weapon_right',playerAnimType='armminigun',
                 displayName=('Soul Staff' if tier==2 else 'Crown of the Damned')+(' EX' if up else ''),
                 ammoName=name,clipName=name,holdFireTime='0.266667',introFireTime='0.266667',fireTime='0.3',
                 adsTransInTime=staff['adsTransInTime'],adsTransOutTime=staff['adsTransOutTime'])
        # PK27 (2026-10-05): the staff's own foley (sound/aliases/tod_necro_foley.csv, tools/sfx/w2c_sounds): its lower
        # for both ears (the skull block's putaway named unshipped Der Eisendrache foley = silent), and its MELEE: the
        # swing clip carries no sound note, so the whoosh / hit / surface come from the shared sound table
        # tod_necro_staff_sounds (source_data/tod_necro_sounds.gdt). The Soul Pulse proxies copy these (dict(f, ...)).
        f.update(putawaySound='tod_necro_staff_lower_npc',putawaySoundPlayer='tod_necro_staff_lower_plr',
                 firstRaiseSound='tod_necro_first_raise_npc',sharedWeaponSounds='tod_necro_staff_sounds')
        # Staff handling duration follows the animations. Damage, meter, firing
        # type and stock skull FX stay on the original script-controlled path.
        for key in ['raiseTime','quickRaiseTime','firstRaiseTime','dropTime','quickDropTime','emptyRaiseTime','sprintInTime','sprintLoopTime','sprintOutTime']:
            if key in staff:f[key]=staff[key]
        for key in list(f):
            if key.startswith('attachViewModel') or key.startswith('attachWorldModel'):
                if 'Offset' not in key:f[key]=''
        out.append(emit(name,f))
        if not up:
            proxy=dict(f,inventoryType='primary',displayName='Soul Pulse',altWeapon='',
                       fireType='Single Shot',holdFireAnim='',holdFireLoopAnim='',holdFireCancelAnim='',
                       damage='0',damage2='0',damage3='0',damage4='0',minDamage='0',explosionRadius='0',explosionInnerDamage='0',explosionOuterDamage='0',
                       dropTime='0',quickDropTime='0',fireTime='1',meleeDamage='0')
            for slot in ['raiseAnim','firstRaiseAnim','quickRaiseAnim','emptyRaiseAnim']:proxy[slot]='tod_vm_necro_staff_pulse'
            for key in ['raiseTime','firstRaiseTime','quickRaiseTime','emptyRaiseTime']:proxy[key]='0.6'
            for key in ['fireAnim','lastShotAnim','adsFireAnim','adsLastShotAnim']:proxy[key]=anims['slots']['idleAnim']
            out.append(emit(f'tod_necro_pulse{tier}',proxy))
(ROOT/'source_data/tod_necro_staff.gdt').write_text('{\n'+''.join(out)+'}\n',encoding='latin1')
(ROOT/'zone_source/tod_necro_staff.zpkg').write_text('// Cast-only items and complete authored animation set.\nweapon,tod_necro_pulse2\nweapon,tod_necro_pulse3\n'+''.join('xanim,'+r['name']+'\n' for r in anims['clips']))
print('Generated tier 2/3 base + PaP staffs, native viewhands and channeling slots.')
