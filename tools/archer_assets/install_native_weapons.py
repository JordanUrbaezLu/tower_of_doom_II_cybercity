"""Map the recovered BO2 weapon definition onto BO3's native offhand schema."""
import json,re,sys,hashlib,csv,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/archer_assets'))
from install_native import block
source=ROOT/'source_library/archer_equipment/retriever/source_data/zm_prison.gdt'
text=source.read_text()
match=re.search(r'"bouncing_tomahawk_zm"\s*\(\s*"weapon.gdf"\s*\)\s*\{([^}]+)',text)
original=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',match[1]))
awi=(Path('C:/BO3Tools/TOD2Cybercity/deffiles/grenadeweapon.awi')).read_text()
allowed=set(re.findall(r'Asset.AddEntry_(?:CheckBox|Int|Float)\(\s*"([^"]+)"',awi))
# Reuse numeric/boolean gameplay fields only. All external asset dependencies
# are explicitly remapped below so no T6 path is accidentally installed.
fields={k:v for k,v in original.items() if k in allowed and re.fullmatch(r'-?\d+(?:\.\d+)?',v)}
fields.update({'displayName':"Hell's Retriever",'weaponType':'grenade','weaponClass':'grenade',
 'inventoryType':'offhand','offhandClass':'Frag Grenade','offhandSlot':'Lethal grenade','playerAnimType':'hatchet',
 'gunModel':'tod_archer_retriever_view','handModel':'tod_archer_bo2_hands','worldModel':'tod_archer_retriever_world',
 'projectileModel':'tod_archer_retriever_world','viewmodelTag':'tag_knife_attach','throwLeftHanded':1,
 'idleAnim':'tod_archer_hold','emptyIdleAnim':'tod_archer_hold','holdFireAnim':'tod_archer_hold',
 'raiseAnim':'tod_archer_hold','dropAnim':'tod_archer_hold','altDropAnim':'tod_archer_hold',
 'fireAnim':'tod_archer_throw','lastShotAnim':'tod_archer_throw','fireDelay':'.048','fireTime':'.32',
 'fuseTime':5,'cookOffHold':0,'holdFireTime':0,'holdButtonToThrow':0,'offhandHoldIsCancelable':0,
 'projectileSpeed':690,'projectileSpeedUp':0,'projectileSpeedForward':0,'projectileSpeedRelativeUp':0,
 'projImpactExplode':1,'timedDetonation':0,'damage':1,'minDamage':1,'explosionRadius':0,
 'explosionInnerDamage':0,'explosionOuterDamage':0,'projExplosionType':'grenade','impactType':'blade',
 'projExplosionEffect':'fx/tod/archer/fx_tod_archer_impact.efx','projTrailEffect':'fx/tod/archer/fx_tod_archer_trail.efx',
 'clipSize':1,'startAmmo':1,'maxAmmo':1,'clipOnly':1,'dontTakeClipOnlyWeaponIfEmpty':1,
 'fireSound':'tod_archer_axe_throw','fireSoundPlayer':'tod_archer_axe_throw','hudIcon':'i_tod_archer_axe_hud',
 # 2026-09-25: an OFFHAND in the lethal slot must name an ammo-counter MATERIAL or the engine fatals at arm time
 # ("Com_ERROR: Primary Grenade Ammo Counter Icon Not Found for: tod_archer_retriever", the user's 11:25 run).
 # The stock knife icon is used as ammoCounterIcon by 100+ weapon blocks in the tools root, so it links and loads;
 # a BO2 tomahawk picture is a follow-up (a 2d material over i_tod_archer_axe_hud).
 'ammoCounterIcon':'t7_icon_weapon_special_knife_pu','ammoCounterClip':'None',
 'ammoName':'tod_archer_retriever','clipName':'tod_archer_retriever','sharedAmmoCapName':'',
 'drawOffhandModelInHand':1,'showIndicator':0,'isHoldUseGrenade':0})
flourish={'displayName':"Hell's Retriever",'weaponType':'grenade','weaponClass':'grenade','inventoryType':'item',
 'playerAnimType':'hatchet','offhandSlot':'None','offhandClass':'None','gunModel':'tod_archer_retriever_view',
 'handModel':'tod_archer_bo2_hands','worldModel':'tod_archer_retriever_world','viewmodelTag':'tag_weapon',
 'idleAnim':'tod_archer_flourish_idle','emptyIdleAnim':'tod_archer_flourish_idle',
 'firstRaiseAnim':'tod_archer_flourish','raiseAnim':'tod_archer_flourish','quickRaiseAnim':'tod_archer_flourish',
 'emptyRaiseAnim':'tod_archer_flourish','firstRaiseTime':1.6,'raiseTime':1.6,'quickRaiseTime':1.6,
 'emptyRaiseTime':1.6,'dropTime':.05,'quickDropTime':.05,'isHoldUseGrenade':1,'clipSize':0,
 'startAmmo':0,'maxAmmo':0,'damage':0,'dontTakeClipOnlyWeaponIfEmpty':1,'adsSupported':0}
target=ROOT/'source_data/tod_archer_weapons.gdt'
target.write_text('{\n'+block('tod_archer_retriever','grenadeweapon',fields)+block('tod_archer_retriever_flourish','grenadeweapon',flourish)+'}\n')
report={'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'intentional_map_change':'Lethal slot as requested; BO2 used tactical','weapon':fields,'flourish':flourish,
 'unmapped_numeric_fields':{k:v for k,v in original.items() if k not in allowed and re.fullmatch(r'-?\d+(?:\.\d+)?',v)}}
(ROOT/'art/archer_assets/engine_kit/native_weapon.json').write_text(json.dumps(report,indent=2)+'\n')
# Flourish's original notetrack is retained in the converted clip.
sample=next((ROOT/'source_library/archer_equipment/retriever').rglob('*first_raise*.wav'),None)
if sample is None:sample=next((ROOT/'source_library/archer_equipment/retriever').rglob('*first_raise*.flac'))
ffmpeg=next((Path.home()/'AppData/Local/Microsoft/WinGet/Packages').glob('Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe'))
destination=ROOT/'sound_assets/tod/archer/axe_first_raise.wav'
subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-i',str(sample),'-ar','48000','-ac','2','-c:a','pcm_s16le',str(destination)],check=True)
aliases=ROOT/'sound/aliases/tod_archer.csv'
with aliases.open(newline='') as f:r=csv.DictReader(f);header=r.fieldnames;rows=list(r)
rows=[r for r in rows if r['Name']!='tod_archer_axe_first_raise']
row=dict(next(r for r in rows if r['Name']=='tod_archer_axe_throw'))
row.update({'Name':'tod_archer_axe_first_raise','FileSpec':r'tod\archer\axe_first_raise.wav','PanType':'2d','EntityLimitCount':'1'})
rows.append(row)
with aliases.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(rows)
print('BO2_NATIVE_WEAPONS_INSTALLED',len(fields),'fields; original release=.048s speed=920 (map: 690, user 2026-09-26 "25% slower" in the air) fire=.32s')
