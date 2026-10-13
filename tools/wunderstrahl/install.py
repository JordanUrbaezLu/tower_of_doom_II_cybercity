"""THE WUNDERSTRAHL's weapon + zone (docs/219, 2026-10-05). GENERATED - never hand-edit the outputs.

  python tools/wunderstrahl/install.py [--out-root DIR]      write source_data/tod2_wunderstrahl.gdt + zone_source/tod2_wunderstrahl.zpkg
  python tools/wunderstrahl/install.py --check [--out-root]  regenerate in memory; FAIL (exit 1) on drift or a broken reference
  python tools/wunderstrahl/install.py --vendor              re-copy the stock template block (refuses if the stock file moved)

THE WEAPON is a native BO3 gas weapon (gasweapon.gdf), the type the Purifier and the Gauntlet of Siegfried's dragon breath
use: while the trigger is held the engine draws flameBeamFirstPerson from the viewmodel's tag_flash and
flameBeamThirdPerson from the world model's. Its template is the stock gauntlet's "dragon_gauntlet_flamethrower_zm" block,
vendored ELEMENT FOR ELEMENT into donor/ (provenance.json records the stock file's sha256), so every field the gdf
expects is present and only the ones below change. The stock gauntlet's own assets (its anims, models, sounds, effects,
its "default_laser" flame table, which no GDT we build from defines) are all replaced or cleared; generate() fails if a
gauntlet name survives.

  identity   a primary-inventory weapon (never a hero gadget), no parent / alt weapon, unlimitedAmmo, no overheat
  damage     ZERO: the beam's damage is script (_tod_wunderstrahl.gsc beam_tick), so the engine's burn lane is off
  beams      tod2_ws_beam_1p / _3p + the flame table tod2_ws_flametable (tools/wunderstrahl/fx/make_fx.py)
  models     tod2_ws_view / tod2_ws_world (tools/wunderstrahl/model/install_art.py)
  anims      the DG-2's clips renamed tod2_ws_vm_* (fireIntroAnim = the DG-2 fire kick, the held loop = the idle pose,
             the engine's gun kick per fire tick is the tremble)
  sounds     the native continuous-fire lane: startFireSound(Player) = the ignition (tod_ws_fire_start_*), loopFireSound(Player)
             = the held beam, loopFireEndSound(Player) = the release; the flame-table sound fields stay empty (no doubled loop)

LOCKSTEP (checked): the weapon name = _tod_wunderstrahl.gsc TOD_WS_WEAPON; the pickup model = TOD_WS_PICKUP_MODEL; every
fx the script precaches is zoned; every referenced model / anim / beam / flame table exists in the companion GDTs when
they are present in the tree (tod2_wunderstrahl_art.gdt, tod2_wunderstrahl_fx.gdt).
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
DONOR = HERE / 'donor'
PROVENANCE = DONOR / 'provenance.json'
STOCK_GDT = pathlib.Path(r'C:\BO3Tools\TOD2Cybercity\source_data\wpn_t7_zmb_dlc3_gauntlet_dragon.gdt')
TEMPLATE_NAME = 'dragon_gauntlet_flamethrower_zm'
TEMPLATE_FILE = DONOR / 'gauntlet_flamethrower.gdt'
GSC = 'scripts/zm/zm_tod2_cybercity/_tod_wunderstrahl.gsc'
CSC = 'scripts/zm/zm_tod2_cybercity/_tod_wunderstrahl.csc'
OUT_GDT = 'source_data/tod2_wunderstrahl.gdt'
OUT_ZPKG = 'zone_source/tod2_wunderstrahl.zpkg'
ART_GDT = 'source_data/tod2_wunderstrahl_art.gdt'
FX_GDT = 'source_data/tod2_wunderstrahl_fx.gdt'
FX_DIR = 'share/raw/fx/tod/wunderstrahl'

WEAPON = 'tod2_wunderstrahl'
PICKUP = 'tod2_ws_pickup'

# the DG-2 clip each gauntlet clip's role maps to ("" = this weapon has no such clip)
ANIM_MAP = {
    'ads_base_down': 'tod2_ws_vm_ads_base_down',
    'ads_base_up': 'tod2_ws_vm_ads_base_up',
    'fire_loop': 'tod2_ws_vm_idle',          # the held beam: the idle pose (looping); the gun kick per tick trembles it
    'fire_in': 'tod2_ws_vm_fire',            # the ignition kick (its sound is the weapon's startFireSoundPlayer)
    'fire_out': '',
    'first_raise': 'tod2_ws_vm_first_raise',
    'pullout': 'tod2_ws_vm_pullout',
    'pullout_quick': 'tod2_ws_vm_pullout_quick',
    'putaway': 'tod2_ws_vm_putaway',
    'putaway_quick': 'tod2_ws_vm_putaway_quick',
    'alt_putaway': '',
    'alt_pullout': '',
    'alt_raise': '',
    'idle': 'tod2_ws_vm_idle',
    'crawl_b': 'tod2_ws_vm_crawl_b',
    'crawl_f': 'tod2_ws_vm_crawl_f',
    'crawl_l': 'tod2_ws_vm_crawl_l',
    'crawl_r': 'tod2_ws_vm_crawl_r',
    'crawl_in': 'tod2_ws_vm_crawl_in',
    'crawl_out': 'tod2_ws_vm_crawl_out',
    'fall': 'tod2_ws_vm_fall',
    'jump': 'tod2_ws_vm_jump',
    'jump_land': 'tod2_ws_vm_jump_land',
    'sprint_in': 'tod2_ws_vm_sprint_in',
    'sprint_loop': 'tod2_ws_vm_sprint_loop',
    'sprint_out': 'tod2_ws_vm_sprint_out',
    'slide_in': 'tod2_ws_vm_slide_in',
    'slide_loop': 'tod2_ws_vm_slide_loop',
    'slide_out': 'tod2_ws_vm_slide_out',
    'slide_air_in': 'tod2_ws_vm_slide_air_in',
    'walk_f': 'tod2_ws_vm_walk_f',
    'melee_swipe': '',
}
GAUNT_PREFIX = 'vm_z_dragon_gaunt_'

# every field the gauntlet sets that this weapon sets differently
OVERRIDES = {
    'displayName': 'Wunderstrahl',                 # raw Title Case like every weapon here; the HUD upper-cases it
    'inventoryType': 'primary',
    'gadget_type': 'none',
    'activate_mode': 'hold',
    'parentWeaponName': '',
    'altWeapon': '',
    'castAbility': '',
    'heroVersion_2_0': '0',
    'fuelTankWeapon': '0',
    'weaponType': 'gas',
    'weaponClass': 'gas',
    # models
    'gunModel': 'tod2_ws_view',
    'worldModel': 'tod2_ws_world',
    'handModel': '',
    'isHandModelOverridable': '1',
    # fire + ammo: hold it for the whole window, nothing to reload, nothing to overheat
    'fireTime': '0.1',
    'holdFireTime': '0.1',
    'unlimitedAmmo': '1',
    'clipOnly': '1',
    'clipSize': '100',
    'maxAmmo': '100',
    'startAmmo': '100',
    'ammoName': WEAPON,
    'clipName': WEAPON,
    'ammoCounterClip': 'None',
    'noAmmoOnDpadIcon': '1',
    'overheatWeapon': '0',
    'coolWhileFiring': '0',
    'noPartialReload': '1',
    # the engine's burn lane is OFF: the script owns the beam's damage
    'damage': '0',
    'damageDuration': '0',
    'damageInterval': '1000',
    'burnDamage': '0',
    'burnDuration': '0',
    'burnDamageInterval': '0',
    # the beam + its flame table (the effects track's GDT)
    'flameBeamFirstPerson': 'tod2_ws_beam_1p',
    'flameBeamFirstPersonUnderWater': 'tod2_ws_beam_1p',
    'flameBeamThirdPerson': 'tod2_ws_beam_3p',
    'flameBeamThirdPersonUnderWater': 'tod2_ws_beam_3p',
    'flameTableFirstPerson': 'tod2_ws_flametable',
    'flameTableThirdPerson': 'tod2_ws_flametable',
    'canUseUnderWater': '1',
    # timings to the DG-2 clips (first raise 1.67 s / pullout 1.0 / putaway 0.67, played a touch quicker)
    'firstRaiseTime': '1.25',
    'raiseTime': '0.8',
    'emptyRaiseTime': '0.8',
    'dropTime': '0.5',
    'emptyDropTime': '0.5',
    'quickRaiseTime': '0.5',
    'quickDropTime': '0.4',
    'quickRaiseAnim': 'tod2_ws_vm_pullout_quick',   # by field: the gauntlet borrowed its alt clips here
    'quickDropAnim': 'tod2_ws_vm_putaway_quick',
    'lastShotAnim': '',
    'adsLastShotAnim': '',
    # the tremble: a small kick every fire tick that recentres fast (a laser has no climb)
    'hipGunKickPitchMin': '-0.6',
    'hipGunKickPitchMax': '0.6',
    'hipGunKickYawMin': '-0.5',
    'hipGunKickYawMax': '0.5',
    'adsGunKickPitchMin': '-0.3',
    'adsGunKickPitchMax': '0.3',
    'adsGunKickYawMin': '-0.25',
    'adsGunKickYawMax': '0.25',
    'hipViewKickPitchMin': '0.1',
    'hipViewKickPitchMax': '0.25',
    'hipViewKickYawMin': '-0.15',
    'hipViewKickYawMax': '0.15',
    'adsViewKickPitchMin': '0.05',
    'adsViewKickPitchMax': '0.12',
    'adsViewKickYawMin': '-0.08',
    'adsViewKickYawMax': '0.08',
    'fireRumble': 'flamethrower',
    'moveSpeedScale': '1',
    'adsMoveSpeedScale': '1',
    # sounds: the loop-fire lane owns the held beam; flame-table sounds stay empty (no doubled loop)
    'fireSound': '',
    'fireSoundPlayer': '',
    'loopFireSound': 'tod_ws_fire_loop_npc',
    'loopFireSoundPlayer': 'tod_ws_fire_loop_plr',
    'loopFireEndSound': 'tod_ws_fire_stop_npc',
    'loopFireEndSoundPlayer': 'tod_ws_fire_stop_plr',
    'startFireSound': 'tod_ws_fire_start_npc',       # the ignition, played by the engine as continuous fire starts
    'startFireSoundPlayer': 'tod_ws_fire_start_plr',
    'flameIgniteSound': '',
    'flameIgniteSoundPlayer': '',
    'flameOnLoopSound': '',
    'flameOnLoopSoundPlayer': '',
    'flameOffLoopSound': '',
    'flameOffLoopSoundPlayer': '',
    'flameCooldownSound': '',
    'flameCooldownSoundPlayer': '',
    # the beam's originEffect is the muzzle; no stock flash
    'viewFlashEffect': '',
    'worldFlashEffect': '',
    'hudIcon': '',
    'killIcon': '',
    'dpadIcon': '',
    'hideTags': '',
    'AIOverlayDescription': '',
    'viewPersistentEffectSet': '',                  # the gauntlet's whelp glow set; the Wunderstrahl's glow is its emissive model
}
KEEP_SOUNDS = {k for k, v in OVERRIDES.items() if v.startswith('tod_ws_')}
FOREIGN = ('dragon', 'gaunt', 'drag_', 'default_laser', 'hero_flamethrower', 'flamethrower_beam', 'stalingrad')


# ---- GDT text ------------------------------------------------------------------------------------------------------------
BLOCK_RE = re.compile(r'^\t"([^"]+)" \( "([^"]+)" \)\s*\n\t\{\n(.*?)\n\t\}', re.S | re.M)
FIELD_RE = re.compile(r'^\t\t"([^"]+)" "(.*)"\s*$')


def parse_block(text, name):
    text = text.replace('\r\n', '\n')
    for m in BLOCK_RE.finditer(text):
        if m.group(1) == name:
            fields = []
            for line in m.group(3).split('\n'):
                f = FIELD_RE.match(line)
                if f:
                    fields.append((f.group(1), f.group(2)))
            return m.group(2), fields
    raise SystemExit('WUNDERSTRAHL: block %s not found' % name)


def emit(blocks):
    out = ['{']
    for name, gdf, fields in blocks:
        out.append('\t"%s" ( "%s" )' % (name, gdf))
        out.append('\t{')
        for k, v in fields:
            out.append('\t\t"%s" "%s"' % (k, v))
        out.append('\t}')
    out.append('}')
    return '\n'.join(out) + '\n'


def names_in_gdt(path, gdf=None):
    if not path.exists():
        return None
    text = path.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n')
    return {m.group(1) for m in BLOCK_RE.finditer(text) if gdf is None or m.group(2) == gdf}


# ---- the donor -----------------------------------------------------------------------------------------------------------
def vendor(force=False):
    raw = STOCK_GDT.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    old = json.loads(PROVENANCE.read_text(encoding='utf-8')) if PROVENANCE.exists() else {}
    if old and old.get('source_sha256') != sha and not force:
        sys.exit('WUNDERSTRAHL: the stock gauntlet GDT changed since it was vendored; review it, then --vendor --force')
    gdf, fields = parse_block(raw.decode('utf-8', errors='replace'), TEMPLATE_NAME)
    body = emit([(TEMPLATE_NAME, gdf, fields)])
    DONOR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_FILE.write_bytes(body.encode('utf-8'))
    PROVENANCE.write_text(json.dumps({'source': str(STOCK_GDT), 'source_sha256': sha, 'block': TEMPLATE_NAME,
                                      'vendored_sha256': hashlib.sha256(body.encode('utf-8')).hexdigest()}, indent=1) + '\n',
                          encoding='utf-8')
    print('WUNDERSTRAHL DONOR VENDORED: %s (%d fields)' % (TEMPLATE_FILE.relative_to(ROOT), len(fields)))
    return 0


def template():
    if not PROVENANCE.exists() or not TEMPLATE_FILE.exists():
        raise SystemExit('WUNDERSTRAHL: donor missing - run --vendor')
    prov = json.loads(PROVENANCE.read_text(encoding='utf-8'))
    body = TEMPLATE_FILE.read_bytes()
    if hashlib.sha256(body).hexdigest() != prov['vendored_sha256']:
        raise SystemExit('WUNDERSTRAHL: donor/gauntlet_flamethrower.gdt changed since it was vendored')
    return parse_block(body.decode('utf-8'), TEMPLATE_NAME)


# ---- generation ----------------------------------------------------------------------------------------------------------
def map_anim(value):
    role = value[len(GAUNT_PREFIX):]
    if role not in ANIM_MAP:
        raise SystemExit('WUNDERSTRAHL: the template names a gauntlet clip with no mapping: %s (add it to ANIM_MAP)' % value)
    return ANIM_MAP[role]


def is_sound_key(k):
    return k.endswith('Sound') or k.endswith('SoundPlayer') or 'Sound' in k and k.endswith('Left')


def weapon_fields():
    gdf, fields = template()
    if gdf != 'gasweapon.gdf':
        raise SystemExit('WUNDERSTRAHL: the template is not a gas weapon (%s)' % gdf)
    out = []
    seen = set()
    for k, v in fields:
        seen.add(k)
        if k in OVERRIDES:
            v = OVERRIDES[k]
        elif v.startswith(GAUNT_PREFIX):
            v = map_anim(v)
        elif is_sound_key(k) and v:
            v = ''                       # every stock gauntlet alias is cleared: this map ships none of them
        elif v.lower().endswith('.efx') or v.startswith('dlc3') or v.startswith('fx\\'):
            v = ''                       # stock effects: the beam owns ours
        out.append((k, v))
    missing = sorted(k for k in OVERRIDES if k not in seen)
    for k in missing:                    # an override the template lacks is appended (the gdf has the field)
        out.append((k, OVERRIDES[k]))
    out.sort(key=lambda kv: kv[0].lower())
    for k, v in out:
        low = v.lower()
        if any(f in low for f in FOREIGN):
            raise SystemExit('WUNDERSTRAHL: a gauntlet name survived in %s = %s' % (k, v))
    return out, missing


def fx_names(root):
    d = root / FX_DIR
    if not d.exists():
        d = ROOT / FX_DIR
    return sorted(p.stem for p in d.glob('*.efx')) if d.exists() else []


def zpkg_text(root):
    lines = []                           # no comment lines: the zone parser reads every line as an asset
    lines.append('weapon,' + WEAPON)
    lines.append('xmodel,' + PICKUP)
    for n in fx_names(root):
        lines.append('fx,tod/wunderstrahl/' + n)
    lines.append('scriptparsetree,' + GSC)
    lines.append('scriptparsetree,' + CSC)
    return '\n'.join(lines) + '\n'


def gsc_text(root, rel):
    for base in (root, ROOT):
        p = base / rel
        if p.exists():
            return p.read_text(encoding='utf-8')
    return None


def problems(root, gdt_text, zpkg):
    bad = []
    gsc = gsc_text(root, GSC)
    if gsc is None:
        bad.append('%s missing' % GSC)
    else:
        m = re.search(r'#define\s+TOD_WS_WEAPON\s+"([^"]+)"', gsc)
        if not m or m.group(1) != WEAPON:
            bad.append('TOD_WS_WEAPON in the GSC is not %s' % WEAPON)
        m = re.search(r'#define\s+TOD_WS_PICKUP_MODEL\s+"([^"]+)"', gsc)
        if not m or m.group(1) != PICKUP:
            bad.append('TOD_WS_PICKUP_MODEL in the GSC is not %s' % PICKUP)
        for fx in re.findall(r'#precache\(\s*"fx",\s*"([^"]+)"\s*\)', gsc):
            if 'fx,' + fx not in zpkg.split('\n'):
                bad.append('the GSC precaches %s but the zone does not carry it' % fx)
    if gsc_text(root, CSC) is None:
        bad.append('%s missing' % CSC)
    fields = dict(FIELD_RE.match(l).groups() for l in gdt_text.split('\n') if FIELD_RE.match(l))
    art = names_in_gdt(root / ART_GDT) or names_in_gdt(ROOT / ART_GDT)
    fxg = names_in_gdt(root / FX_GDT) or names_in_gdt(ROOT / FX_GDT)
    if art is not None:
        for k in ('gunModel', 'worldModel'):
            if fields.get(k) and fields[k] not in art:
                bad.append('%s %s is not in %s' % (k, fields[k], ART_GDT))
        for k, v in fields.items():
            if v.startswith('tod2_ws_vm_') and v not in art:   # by value: the slide clips' keys carry no "Anim"
                bad.append('%s %s is not in %s' % (k, v, ART_GDT))
        if PICKUP not in art:
            bad.append('the pickup model %s is not in %s' % (PICKUP, ART_GDT))
    if fxg is not None:
        for k in ('flameBeamFirstPerson', 'flameBeamThirdPerson', 'flameTableFirstPerson', 'flameTableThirdPerson'):
            if fields.get(k) not in fxg:
                bad.append('%s %s is not in %s' % (k, fields.get(k), FX_GDT))
    return bad


def generate(root):
    fields, missing = weapon_fields()
    gdt = emit([(WEAPON, 'gasweapon.gdf', fields)])
    return gdt, zpkg_text(root), missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--vendor', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--out-root', default=str(ROOT))
    a = ap.parse_args()
    if a.vendor:
        return vendor(a.force)
    root = pathlib.Path(a.out_root).resolve()
    gdt, zpkg, missing = generate(root)
    bad = problems(root, gdt, zpkg)
    if a.check:
        for rel, want in ((OUT_GDT, gdt), (OUT_ZPKG, zpkg)):
            p = root / rel
            if not p.exists():
                bad.append('%s missing - run tools/wunderstrahl/install.py' % rel)
            elif p.read_text(encoding='utf-8') != want:
                bad.append('%s differs from its generator - run tools/wunderstrahl/install.py' % rel)
        if bad:
            print('WUNDERSTRAHL CHECK FAILED:\n  ' + '\n  '.join(bad))
            return 1
        print('WUNDERSTRAHL CHECK OK: %s, %s (%d weapon fields)' % (OUT_GDT, OUT_ZPKG, gdt.count('\n\t\t')))
        return 0
    for rel, text in ((OUT_GDT, gdt), (OUT_ZPKG, zpkg)):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode('utf-8'))
    print('WUNDERSTRAHL WRITTEN under %s: %s, %s' % (root, OUT_GDT, OUT_ZPKG))
    if missing:
        print('  appended overrides the template lacked: ' + ', '.join(missing))
    if bad:
        print('  OPEN REFERENCES (fine while the other tracks are still staging):\n    ' + '\n    '.join(bad))
    return 0


if __name__ == '__main__':
    sys.exit(main())
