#!/usr/bin/env python3
"""install_punch.py -- build the Warrior's tier-1 ONE INCH PUNCH from the T7 asset pack.

The Origins One Inch Punch ships in `~/Downloads/T7 Assets V2.8.rar` as an
OFFHAND melee (a knife replacement: `one_inch_punch_zm`, meleeweapon.gdf,
gunModel wpn_t7_none_view, no raise/drop/sprint clips of its own). The Warrior
needs a HELD PRIMARY, so this tool:

  1. copies the 8 first-person punch clips + 6 bare-hand clips (XANIM_BIN),
     the `wpn_t7_none_view` view model and the 6 punch wavs out of the rar
     into repo-owned folders (xanim_export/tod_warrior, model_export/tod_warrior,
     sound_assets/zmb/level/zm_tomb/oip);
  2. writes source_data/tod_warrior_punch.gdt: the xanim blocks copied from the
     pack's t7_weapons.gdt (FX notes kept: the fist glow rides the melee clip),
     the view model as `tod_punch_none_view`, a `tod_punch_sounds`
     sharedweaponsounds table, and the weapon pair `tod_punch_zm` /
     `tod_punch_up_zm` = the Hellbound twin knives block (the proven held-melee
     primary in this map) with the punch's clips / model / sounds / timings.
     gen_tod_twins.js then emits the cc_punch k-ladder from that pair, exactly
     as it did from hb_twin_knives_zm.

Re-run after any edit here; never hand-edit the outputs. `--check` verifies
the written files match what this script would write (a build gate).
"""
import os, re, sys, subprocess, hashlib, shutil, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS = r'C:\BO3Tools\TOD2Cybercity'   # the private Mod Tools root (the knives' sound tables live there)
RAR = os.path.join(os.path.expanduser('~'), 'Downloads', 'T7 Assets V2.8.rar')
SEVENZ = r'C:\Program Files\7-Zip\7z.exe'
PACK = 'T7 Assets V2.8'

OUT_GDT = os.path.join(REPO, 'source_data', 'tod_warrior_punch.gdt')
XANIM_DIR = os.path.join(REPO, 'xanim_export', 'tod_warrior')
MODEL_DIR = os.path.join(REPO, 'model_export', 'tod_warrior')
WAV_DIR = os.path.join(REPO, 'sound_assets', 'zmb', 'level', 'zm_tomb', 'oip')
KNIVES_GDT = os.path.join(REPO, 'donor_gdt', 'hellbound', 'hb_warrior_tiers.gdt')

PUNCH_CLIPS = ['vm_zom_1inchpunch_ads_down', 'vm_zom_1inchpunch_ads_up', 'vm_zom_1inchpunch_charge',
               'vm_zom_1inchpunch_charge_upgraded', 'vm_zom_1inchpunch_first_raise', 'vm_zom_1inchpunch_idle',
               'vm_zom_1inchpunch_melee', 'vm_zom_1inchpunch_melee_upgraded']
HAND_CLIPS = ['vm_bare_hands_idle', 'vm_bare_hands_pullout', 'vm_bare_hands_putaway',
              'vm_bare_hands_sprint_in', 'vm_bare_hands_sprint_loop', 'vm_bare_hands_sprint_out']
# THE GAUNTLET'S LEFT HOOK (user 2026-09-26: "a right left hook ... the left hook will
# be a little bit weaker"): BO3's boxing-glove left punch, the gauntlet's meleeLeftAnim
# (gen_tod_twins cc_gauntlet). It converts against the gloves' own skeleton (shipped
# beside it); it drives the viewhands' arm bones, which the gauntlet rig shares.
BOXING_CLIPS = ['vm_boxing_gloves_melee_swipe_l']
BOXING_SKELETON = 'wpn_t7_loot_boxing_glove_skeleton.XMODEL_BIN'
# clip -> file extension inside the pack (the punch clips are upper-case .XANIM_BIN)
CLIP_EXT = {c: '.XANIM_BIN' for c in PUNCH_CLIPS}
CLIP_EXT.update({c: '.xanim_bin' for c in HAND_CLIPS + BOXING_CLIPS})
WAVS = ['hit/punch_imp_00.wav', 'hit/punch_imp_01.wav', 'other/punch_imp_wall_00.wav',
        'punch/punch_miss.wav', 'raise/oip_reg_1raise_r2.wav', 'raise/oip_ugd_1raise_r4.wav']

# Clip lengths measured from the pack's SEAnim twins (30 fps): first raise 47 f,
# melee 21 f, pullout/putaway 6 f, sprint in/out 11 f, sprint loop 31 f.
T_FIRST_RAISE = 1.5667
T_MELEE = 0.7
T_RAISE = 0.2
T_SPRINT_IO = 0.3667
T_SPRINT_LOOP = 1.0333


def extract(members, dest):
    subprocess.run([SEVENZ, 'x', '-y', '-o' + dest, RAR] + members, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pack_path(rel):
    return PACK + '\\' + rel


def block(text, name, gdf):
    m = re.search(r'(\t"%s" \( "%s" \)\s*\{.*?\n\t\})' % (re.escape(name), re.escape(gdf)), text, re.S)
    if not m:
        raise SystemExit('block %s (%s) not found' % (name, gdf))
    return m.group(1)


def set_field(blk, key, value):
    """Set "key" "value" in a block; append the line if the key is absent."""
    pat = re.compile(r'^(\t\t"%s" )"[^"\n]*"' % re.escape(key), re.M)
    if pat.search(blk):
        return pat.sub(lambda m: m.group(1) + '"' + value + '"', blk, count=1)
    return blk.replace('\n\t}', '\n\t\t"%s" "%s"\n\t}' % (key, value), 1)


def rename(blk, old, new):
    return blk.replace('"%s"' % old, '"%s"' % new)


def build(tmp):
    src_gdt = os.path.join(tmp, PACK, 'source_data', '_midgetblaster', 't7_weapons.gdt')
    src_snd = os.path.join(tmp, PACK, 'source_data', '_midgetblaster', 't7_sharedweaponsounds.gdt')
    members = [pack_path(r'source_data\_midgetblaster\t7_weapons.gdt'),
               pack_path(r'source_data\_midgetblaster\t7_sharedweaponsounds.gdt'),
               pack_path(r'model_export\_midgetblaster\weapons\t7\wpn_t7_none_view\wpn_t7_none_view_LOD0.XMODEL_BIN')]
    members += [pack_path(r'xanim_export\_midgetblaster\black_ops_3\%s%s' % (c, CLIP_EXT[c])) for c in PUNCH_CLIPS + HAND_CLIPS + BOXING_CLIPS]
    members += [pack_path(r'model_export\_midgetblaster\weapons\t7\wpn_t7_loot_boxing_glove_view\%s' % BOXING_SKELETON)]
    members += [pack_path(r'sound_assets\zmb\level\zm_tomb\oip\%s' % w.replace('/', '\\')) for w in WAVS]
    extract(members, tmp)
    weapons = open(src_gdt, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
    sounds = open(src_snd, encoding='utf-8', errors='replace').read().replace('\r\n', '\n')

    files = {}   # dest path -> source path
    for c in PUNCH_CLIPS + HAND_CLIPS + BOXING_CLIPS:
        files[os.path.join(XANIM_DIR, c + '.XANIM_BIN')] = os.path.join(tmp, PACK, 'xanim_export', '_midgetblaster', 'black_ops_3', c + CLIP_EXT[c])
    files[os.path.join(MODEL_DIR, BOXING_SKELETON)] = os.path.join(tmp, PACK, 'model_export', '_midgetblaster', 'weapons', 't7', 'wpn_t7_loot_boxing_glove_view', BOXING_SKELETON)
    files[os.path.join(MODEL_DIR, 'wpn_t7_none_view_LOD0.XMODEL_BIN')] = os.path.join(tmp, PACK, 'model_export', '_midgetblaster', 'weapons', 't7', 'wpn_t7_none_view', 'wpn_t7_none_view_LOD0.XMODEL_BIN')
    for w in WAVS:
        files[os.path.join(WAV_DIR, w.replace('/', os.sep))] = os.path.join(tmp, PACK, 'sound_assets', 'zmb', 'level', 'zm_tomb', 'oip', w.replace('/', os.sep))

    blocks = []
    # --- xanims: the pack's own blocks, filename repointed at the repo folder. The
    # conversion skeleton (t7_characters\viewmodels\c_t7_mp_warrior_viewhands) is
    # installed at the tools root; every BO3 viewhands clip shares that rig.
    for c in PUNCH_CLIPS + HAND_CLIPS:
        b = block(weapons, c, 'xanim.gdf')
        b = set_field(b, 'filename', 'tod_warrior\\\\%s.XANIM_BIN' % c)
        if c == 'vm_zom_1inchpunch_melee_upgraded':
            # the PaP swing wears Origins' upgraded fist glow (the pack's block
            # names the base glow on both clips)
            b = set_field(b, 'fx_startupnote0actionparam1', 'dlc5\\\\tomb\\\\fx_one_inch_punch_ug.efx')
            b = set_field(b, 'fx_shutdownnote0actionparam1', 'dlc5\\\\tomb\\\\fx_one_inch_punch_ug.efx')
        blocks.append(b)
    for c in BOXING_CLIPS:
        b = block(weapons, c, 'xanim.gdf')
        b = set_field(b, 'filename', 'tod_warrior\\\\%s.XANIM_BIN' % c)
        b = set_field(b, 'model', 'tod_warrior\\\\' + BOXING_SKELETON)
        blocks.append(b)
    # --- the empty view model (the hands are the weapon)
    b = block(weapons, 'wpn_t7_none_view', 'xmodel.gdf')
    b = rename(b, 'wpn_t7_none_view', 'tod_punch_none_view')
    b = set_field(b, 'filename', 'tod_warrior\\\\wpn_t7_none_view_LOD0.XMODEL_BIN')
    blocks.append(b)
    # --- the hit / surface TABLES. meleeEntityImpact* name an entitysoundimpacts
    # ASSET (per body type -> alias) and meleeSurfaceSound* a surfacesounddef
    # ASSET (per surface -> alias), not aliases: the 2026-09-26 lead build died in
    # the linker on exactly that ("not a valid surfacesounddef asset"). Cloned
    # from the twin knives' tables (root-installed, proven to link) with every
    # cell pointed at the punch aliases in tod_warrior.csv.
    heirloom = open(os.path.join(TOOLS, 'source_data', 'hb_apex_heirloom_weapons.gdt'), encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
    surf = open(os.path.join(TOOLS, 'source_data', 't9_weapons', 'melee', 't9_me_surfacesounddef.gdt'), encoding='utf-8', errors='replace').read().replace('\r\n', '\n')
    for src, gdf, dst, alias in [('hb_ah_16_hits_plr', 'entitysoundimpacts.gdf', 'tod_punch_hits_plr', 'tod_punch_hit_plr'),
                                 ('hb_ah_16_hits_npc', 'entitysoundimpacts.gdf', 'tod_punch_hits_npc', 'tod_punch_hit_npc'),
                                 ('t9_melee_knife_surface_plr', 'surfacesounddef.gdf', 'tod_punch_surfaces_plr', 'tod_punch_surface_plr'),
                                 ('t9_melee_knife_surface_npc', 'surfacesounddef.gdf', 'tod_punch_surfaces_npc', 'tod_punch_surface_npc')]:
        b = block(heirloom if gdf.startswith('entity') else surf, src, gdf)
        b = b.replace('"%s" ( "%s" )' % (src, gdf), '"%s" ( "%s" )' % (dst, gdf))
        b = re.sub(r'^(\t\t"[A-Za-z0-9_]+" )"[^"\n]+"', lambda m: m.group(1) + '"' + alias + '"', b, flags=re.M)
        blocks.append(b)
    # --- shared weapon sounds: the stock table's shape, our tables / aliases
    b = block(sounds, 'fist_one_inch_punch', 'sharedweaponsounds.gdf')
    b = rename(b, 'fist_one_inch_punch', 'tod_punch_sounds')
    for k, v in [('meleeEntityImpactChainFinish', 'tod_punch_hits_npc'), ('meleeEntityImpactChainFinishPlayer', 'tod_punch_hits_plr'),
                 ('meleeEntityImpactChainMid', 'tod_punch_hits_npc'), ('meleeEntityImpactChainMidPlayer', 'tod_punch_hits_plr'),
                 ('meleeEntityImpactLunge', 'tod_punch_hits_npc'), ('meleeEntityImpactLungePlayer', 'tod_punch_hits_plr'),
                 ('meleeEntityImpactLungeVictim', 'tod_punch_hits_npc'),
                 ('meleeEntityImpactPower', 'tod_punch_hits_npc'), ('meleeEntityImpactPowerPlayer', 'tod_punch_hits_plr'),
                 ('meleeEntityImpactPowerVictim', 'tod_punch_hits_npc'),
                 ('meleeEntityImpactSwipe', 'tod_punch_hits_npc'), ('meleeEntityImpactSwipePlayer', 'tod_punch_hits_plr'),
                 ('meleeEntityImpactSwipeVictim', 'tod_punch_hits_npc'),
                 ('meleeSurfaceSound', 'tod_punch_surfaces_npc'), ('meleeSurfaceSoundPlayer', 'tod_punch_surfaces_plr'),
                 ('meleeWhoosh', 'wpn_one_inch_punch_npc'), ('meleeWhooshPlayer', 'wpn_one_inch_punch_plr'),
                 ('meleePowerWhoosh', 'wpn_one_inch_punch_npc'), ('meleePowerWhooshPlayer', 'wpn_one_inch_punch_plr')]:
        b = set_field(b, k, v)
    blocks.append(b)

    # --- the weapon pair: Hellbound's twin knives block with the punch's parts
    knives = open(KNIVES_GDT, encoding='utf-8').read().replace('\r\n', '\n')
    for src, dst, up in [('hb_twin_knives_zm', 'tod_punch_zm', False), ('hb_twin_knives_up_zm', 'tod_punch_up_zm', True)]:
        b = block(knives, src, 'bulletweapon.gdf')
        b = b.replace('"%s" ( "bulletweapon.gdf" )' % src, '"%s" ( "bulletweapon.gdf" )' % dst)
        melee = 'vm_zom_1inchpunch_melee_upgraded' if up else 'vm_zom_1inchpunch_melee'
        charge = 'vm_zom_1inchpunch_charge_upgraded' if up else 'vm_zom_1inchpunch_charge'
        anims = {'hb_twin_knives_vm_attack': melee, 'hb_twin_knives_vm_idle': 'vm_zom_1inchpunch_idle',
                 'hb_twin_knives_vm_holster': 'vm_bare_hands_putaway', 'hb_twin_knives_vm_draw': 'vm_zom_1inchpunch_first_raise',
                 'hb_twin_knives_vm_inspect': 'vm_zom_1inchpunch_idle',
                 'hb_twin_knives_vm_sprint_in': 'vm_bare_hands_sprint_in', 'hb_twin_knives_vm_sprint_out': 'vm_bare_hands_sprint_out',
                 'hb_twin_knives_vm_sprint': 'vm_bare_hands_sprint_loop',
                 'hb_ah_16_idle': 'vm_zom_1inchpunch_idle', 'hb_ah_16_holster': 'vm_bare_hands_putaway',
                 'hb_ah_16_draw': 'vm_bare_hands_pullout', 'hb_ah_16_sprint': 'vm_bare_hands_sprint_loop'}
        for old, new in anims.items():
            b = rename(b, old, new)
        for k, v in [('raiseAnim', 'vm_bare_hands_pullout'), ('quickRaiseAnim', 'vm_bare_hands_pullout'),
                     ('adsUpAnim', 'vm_zom_1inchpunch_ads_up'), ('adsDownAnim', 'vm_zom_1inchpunch_ads_down'),
                     ('meleeChargeAnimAbove', charge),
                     ('gunModel', 'tod_punch_none_view'), ('worldModel', 'tag_origin'),
                     ('worldModelTagLeft', 'tag_weapon_left'), ('worldModelTagRight', 'tag_weapon_right'),
                     ('sharedWeaponSounds', 'tod_punch_sounds'),
                     ('displayName', 'Iron Fist' if up else 'One Inch Punch'),
                     ('ammoName', 'tod_punch_up' if up else 'tod_punch'), ('clipName', 'tod_punch_up' if up else 'tod_punch'),
                     ('sharedAmmoCapName', 'tod_punch_up' if up else 'tod_punch'),
                     ('playerAnimType', 'onehanded'),
                     ('meleeImpactEffect', 'dlc5\\\\tomb\\\\fx_one_inch_punch_impact.efx'),
                     ('meleeImpactNoBloodEffect', 'dlc5\\\\tomb\\\\fx_one_inch_punch_impact.efx'),
                     ('doGibbing', '1'), ('doGibbingOnMelee', '1'),
                     ('firstRaiseTime', str(T_FIRST_RAISE)), ('emptyRaiseTime', str(T_FIRST_RAISE)),
                     ('raiseTime', str(T_RAISE)), ('quickRaiseTime', str(T_RAISE)),
                     ('dropTime', str(T_RAISE)), ('emptyDropTime', str(T_RAISE)), ('quickDropTime', str(T_RAISE)),
                     ('sprintInTime', str(T_SPRINT_IO)), ('sprintOutTime', str(T_SPRINT_IO)),
                     ('sprintLoopTime', str(T_SPRINT_LOOP)), ('wallRunLoopTime', str(T_SPRINT_LOOP)),
                     ('reloadTime', '0.1'), ('reloadEmptyTime', '0.1'), ('lowReadyLoopTime', '0.1'),
                     ('fireTime', str(T_MELEE)), ('lastFireTime', str(T_MELEE)), ('meleeTime', str(T_MELEE)),
                     ('meleeLeftTime', str(T_MELEE)),
                     ('meleeDamage', '2000' if up else '1000'), ('damage', '2000' if up else '1000'),
                     ('stowedModelOffsetsF', '0'), ('stowedModelOffsetsR', '0'), ('stowedModelOffsetsU', '0'),
                     ('stowedModelOffsetsPitch', '0'), ('stowedModelOffsetsYaw', '0'), ('stowedModelOffsetsRoll', '0')]:
            b = set_field(b, k, v)
        blocks.append(b)

    # --- BASH proxies. The tactical dash (_tod_class_kit.gsc bash_fire) hands the
    # player a one-swing proxy weapon whose RAISE clip is the dash; Hellbound's
    # hb_warrior_bash_zm draws the plain sword, which a fist or a gauntlet user
    # must never see. Same block, the blade's own clips/model. 2026-09-26 (user,
    # build-6 playtest): the dash is the blade's PUNCH, not a wind-up - the
    # punch's charge clip is Origins' charged uppercut (the "looks up" lunge) and
    # the gauntlet's melee_in is a wind-up with no strike. Both proxies now raise
    # on the weapon's own melee clip. (The gauntlet's AIM dash punch that also used
    # it is retired, user 2026-09-26.)
    bash_gdt = open(os.path.join(REPO, 'donor_gdt', 'hellbound', 'hb_warrior_bash.gdt'), encoding='utf-8').read().replace('\r\n', '\n')
    bash_src = block(bash_gdt, 'hb_warrior_bash_zm', 'bulletweapon.gdf')
    SLASH = {'fireAnim', 'adsFireAnim', 'adsLastShotAnim', 'lastShotAnim', 'meleeAnim', 'meleeMissAnim'}
    RAISE = {'raiseAnim', 'quickRaiseAnim', 'firstRaiseAnim', 'emptyRaiseAnim'}
    PROXIES = {
        'tod_bash_punch_zm': dict(idle='vm_zom_1inchpunch_idle', slash='vm_zom_1inchpunch_melee', raise_='vm_zom_1inchpunch_melee',
                                  sprint={'sprintInAnim': 'vm_bare_hands_sprint_in', 'sprintLoopAnim': 'vm_bare_hands_sprint_loop', 'sprintOutAnim': 'vm_bare_hands_sprint_out'},
                                  explicit={'gunModel': 'tod_punch_none_view', 'worldModel': 'tag_origin', 'displayName': 'One Inch Punch',
                                            'ammoName': 'tod_bash_punch', 'clipName': 'tod_bash_punch', 'sharedAmmoCapName': 'tod_bash_punch',
                                            'raiseTime': '0.7', 'quickRaiseTime': '0.7', 'firstRaiseTime': '0.7', 'emptyRaiseTime': '0.7',
                                            'playerAnimType': 'onehanded', 'sharedWeaponSounds': 'tod_punch_sounds',
                                            # Exactly one ordinary punch in every raise lane. An attack in
                                            # the idle lane restarts it and is not a normal punch animation.
                                            'idleAnim': 'vm_zom_1inchpunch_idle', 'emptyIdleAnim': 'vm_zom_1inchpunch_idle'}),
        'tod_bash_gauntlet_zm': dict(idle='vm_z_aint_no_dragon_idle', slash='vm_z_aint_no_dragon_melee_swipe', raise_='vm_z_aint_no_dragon_melee_swipe',
                                     sprint={'sprintInAnim': 'vm_z_aint_no_dragon_sprint_in', 'sprintLoopAnim': 'vm_z_aint_no_dragon_sprint_loop', 'sprintOutAnim': 'vm_z_aint_no_dragon_sprint_out'},
                                     explicit={'gunModel': 'wpn_t7_zmb_dlc3_gauntlet_dragon_view', 'worldModel': 'wpn_t7_zmb_dlc3_gauntlet_dragon_world',
                                               'displayName': 'Gauntlet of Siegfried', 'hideTags': 'tag_dragon_world',
                                               'raiseTime': '0.6', 'quickRaiseTime': '0.6', 'firstRaiseTime': '0.6', 'emptyRaiseTime': '0.6',
                                               'ammoName': 'tod_bash_gauntlet', 'clipName': 'tod_bash_gauntlet', 'sharedAmmoCapName': 'tod_bash_gauntlet',
                                               'adsDownAnim': 'vm_z_dragon_gaunt_ads_base_down', 'adsUpAnim': 'vm_z_dragon_gaunt_ads_base_up',
                                               'crawlBackAnim': 'vm_z_aint_no_dragon_crawl_b', 'crawlForwardAnim': 'vm_z_aint_no_dragon_crawl_f',
                                               'crawlInAnim': 'vm_z_aint_no_dragon_crawl_in', 'crawlLeftAnim': 'vm_z_aint_no_dragon_crawl_l',
                                               'crawlOutAnim': 'vm_z_aint_no_dragon_crawl_out', 'crawlRightAnim': 'vm_z_aint_no_dragon_crawl_r',
                                               'slide_in': 'vm_z_aint_no_dragon_slide_in', 'slide_loop': 'vm_z_aint_no_dragon_slide_loop', 'slide_out': 'vm_z_aint_no_dragon_slide_out',
                                               'fallAnim': 'vm_z_dragon_gaunt_fall', 'jumpAnim': 'vm_z_dragon_gaunt_jump', 'jumpLandAnim': 'vm_z_dragon_gaunt_jump_land',
                                               'walkAnim': 'vm_z_dragon_gaunt_walk_f', 'dropAnim': 'vm_z_aint_no_dragon_putaway', 'quickDropAnim': 'vm_z_aint_no_dragon_putaway',
                                               'emptyDropAnim': 'vm_z_aint_no_dragon_putaway',
                                               'playerAnimType': 'onehanded', 'sharedWeaponSounds': 'tod_punch_sounds'}),
        # THE SWORD BASH (user, build-14 playtest: "a single swing and a dash forward
        # ... the baseball [bat's] over the head lunge"). The Cyber Sword's own Bash
        # proxy (tod_cyber_sword_bash_zm, the Blender agent's) must stay identical to
        # Hellbound's donor (tools/cyber_sword/verify_native.py), and the donor's
        # hb_warrior_bash clip is the whole two-pass slash - so this is a separate
        # proxy that RAISES on the bat's lunge hit, vm_t9_bat_melee_out (the bat's
        # meleeChargeAnimHit, installed by source_data/tod_baseball_bat.gdt; it drives
        # the same viewhands rig and tag_weapon the sword rides). Every other donor
        # clip IS the sword's own (hb_gold_sword_lh_* / hb_citadel_vm_*), so keep_hb
        # keeps them instead of flattening them to the idle.
        'tod_bash_sword_zm': dict(idle='hb_gold_sword_lh_idle', slash='vm_t9_bat_melee_out', raise_='vm_t9_bat_melee_out',
                                  sprint={}, keep_hb=True,
                                  explicit={'gunModel': 'tod_cyber_sword_view', 'worldModel': 'tod_cyber_sword_world', 'displayName': 'Cyber Sword',
                                            'ammoName': 'tod_bash_sword', 'clipName': 'tod_bash_sword', 'sharedAmmoCapName': 'tod_bash_sword',
                                            'raiseTime': '0.6', 'quickRaiseTime': '0.6', 'firstRaiseTime': '0.6', 'emptyRaiseTime': '0.6',
                                            'playerAnimType': 'sword'}),
    }
    for name, p in PROXIES.items():
        b = bash_src.replace('"hb_warrior_bash_zm" ( "bulletweapon.gdf" )', '"%s" ( "bulletweapon.gdf" )' % name)
        out_lines = []
        for line in b.split('\n'):
            m = re.match(r'^(\t\t"([A-Za-z0-9_]+)" )"(hb_[^"]*)"\s*$', line)
            if m:
                key = m.group(2)
                if key in p['explicit']:
                    val = p['explicit'][key]
                elif key in p['sprint']:
                    val = p['sprint'][key]
                elif key in SLASH:
                    val = p['slash']
                elif key in RAISE:
                    val = p['raise_']
                elif p.get('keep_hb'):
                    val = m.group(3)   # the sword proxy: the donor's clips are the sword's own
                elif key.endswith('Anim') or key.startswith('slide_'):
                    val = p['idle']
                else:
                    val = m.group(3)   # e.g. normalImpactsSoundsTable: a root-installed table, kept
                line = m.group(1) + '"' + val + '"'
            out_lines.append(line)
        b = '\n'.join(out_lines)
        for k, v in p['explicit'].items():
            b = set_field(b, k, v)
        # The fists never inherit the sword's impact sounds (2026-09-27, user: "some of the
        # punches sound like a sword"): the donor Bash is the Cyber Sword's, so the punch and
        # gauntlet proxies carried hb_citadel_surface_impact. The fists' own weapons leave it
        # blank and sound through tod_punch_sounds.
        if name != 'tod_bash_sword_zm':
            b = set_field(b, 'normalImpactsSoundsTable', '')
        blocks.append(b)

    header = ('{\n')
    body = '\n'.join(blocks) + '\n}\n'
    return header + body, files


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    check = '--check' in sys.argv
    if not os.path.exists(RAR):
        raise SystemExit('T7 asset pack not found: ' + RAR)
    tmp = tempfile.mkdtemp(prefix='tod_punch_')
    try:
        gdt, files = build(tmp)
        bad = []
        if check:
            if not os.path.exists(OUT_GDT) or open(OUT_GDT, encoding='utf-8').read() != gdt:
                bad.append(OUT_GDT)
            for dst, src in files.items():
                if not os.path.exists(dst) or sha(dst) != sha(src):
                    bad.append(dst)
            if bad:
                print('install_punch --check: STALE/MISSING:\n  ' + '\n  '.join(bad))
                sys.exit(1)
            print('install_punch --check OK: %d asset files + %s' % (len(files), os.path.relpath(OUT_GDT, REPO)))
            return
        for dst, src in files.items():
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        os.makedirs(os.path.dirname(OUT_GDT), exist_ok=True)
        with open(OUT_GDT, 'w', encoding='utf-8', newline='\n') as f:
            f.write(gdt)
        print('wrote %s (%d blocks) + %d asset files' % (os.path.relpath(OUT_GDT, REPO), gdt.count('.gdf" )'), len(files)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
