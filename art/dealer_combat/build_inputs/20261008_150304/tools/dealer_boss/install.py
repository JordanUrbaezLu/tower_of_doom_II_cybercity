#!/usr/bin/env python3
"""install.py -- THE DEALER, the final boss, as a native BO3 character (docs/dealer_finale_design.md).

User 2026-09-30: "make the black market dealer the final boss ... build a model using the
Blender MCP ... steal an animation ... pick the right set of animations".

The Dealer rides the Keeper's skeleton (the stock humanoid zombie rig with robe-skirt chains,
jaw and fingers), so every Keeper clip already installed by tools/keeper/install_keeper.py
plays on him, plus 27 raw Keeper clips (the SOURCES of the Dealer's own 45 authored clips) this installer brings from the T7 asset pack: the
Keeper PROTECTOR's composed walk / run / sprint, idle scans, standing attacks (left / right /
up / combo), the bamf-in / bamf-out teleport, an intro and an outtro, the channeling loop,
and the Shadows-of-Evil keeper's attacks and front death.

Reads  art/dealer_boss/engine_kit/export_manifest.json (written by export_native.py) and the
       Keeper's own GDT (source_data/tod_keeper.gdt) for block shapes.
Writes source_data/tod_dealer.gdt       images, 3 materials, xmodel tod_dealer_body (autogen
                                       LODs like the cyber roster), character c_tod_dealer,
                                       27 xanims, the aitype chain archetype -> variant ->
                                       spawner_tod_dealer (archetype "dealer")
       xanim_export/tod_dealer/         the 27 clips (byte copies out of the pack)
       animtables/tod_dealer.ai_am|ast  the Keeper's tables + the Dealer's locomotion /
                                       melee / idle remaps + script-only aliases
       share/raw/animstatemachines/tod_dealer.ai_asm, share/raw/behavior/tod_dealer.ai_bt
                                       the Keeper's, with the death StartFunction renamed
                                       to dealerDeathStart (registered by the Dealer script)
       model_export/tod_dealer/install_manifest.json

Re-run after any change; never hand-edit the outputs. `--check` verifies every output
matches what this script would write (a build gate, like the Keeper's).
"""
import os, re, sys, json, hashlib, shutil, tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'keeper'))
import install_keeper as K   # extract / read / index_blocks / set_field / rename / field, RAR, PACK, MB

EXPORT_MANIFEST = os.path.join(REPO, 'art', 'dealer_boss', 'engine_kit', 'export_manifest.json')
KEEPER_GDT = os.path.join(REPO, 'source_data', 'tod_keeper.gdt')
KIT_GDT = os.path.join(REPO, 'source_data', 'tod_cyber_zombie.gdt')
OUT_GDT = os.path.join(REPO, 'source_data', 'tod_dealer.gdt')
MODEL_DIR = os.path.join(REPO, 'model_export', 'tod_dealer')
XANIM_DIR = os.path.join(REPO, 'xanim_export', 'tod_dealer')
AM_OUT = os.path.join(REPO, 'animtables', 'tod_dealer.ai_am')
AST_OUT = os.path.join(REPO, 'animtables', 'tod_dealer.ai_ast')
ASM_OUT = os.path.join(REPO, 'share', 'raw', 'animstatemachines', 'tod_dealer.ai_asm')
BT_OUT = os.path.join(REPO, 'share', 'raw', 'behavior', 'tod_dealer.ai_bt')
MANIFEST = os.path.join(MODEL_DIR, 'install_manifest.json')
CLIPS_SRC = os.path.join(REPO, 'art', 'dealer_boss', 'clips_src')
CLIPS_REPORT = os.path.join(REPO, 'art', 'dealer_boss', 'engine_kit', 'clips_report.json')

BODY = 'tod_dealer_body'
CHARACTER = 'c_tod_dealer'
GROUPS = ('body', 'head', 'hands')
# the mask's wires and the nails glow: scaleRGB is the one brightness knob per atlas
SURFACE = {'body': ('cloth', 6, 1, 9), 'head': ('plastic', 10, 2, 14), 'hands': ('cloth', 6, 1, 11)}   # surfaceType, scaleRGB, glossRangeMin, glossRangeMax

# THE RAW PACK CLIPS the Dealer's own clips are authored from (tools/dealer_boss/author_clips.py bakes the levitation
# and the two-hand scythe hold into them). Extracted into art/dealer_boss/clips_src (gitignored, never zoned);
# every one checked against the skeleton: 145 parts, none missing. The enslaved / SoE keeper sources are the
# installed Keeper's own files (xanim_export/tod_keeper).
SOURCE_CLIPS = [
    'ai_zm_dlc4_keeper_prtctr_walk', 'ai_zm_dlc4_keeper_prtctr_run', 'ai_zm_dlc4_keeper_prtctr_sprint',
    'ai_zm_dlc4_keeper_prtctr_idle', 'ai_zm_dlc4_keeper_prtctr_idle_scan_1', 'ai_zm_dlc4_keeper_prtctr_idle_scan_2',
    'ai_zm_dlc4_keeper_prtctr_idle_attack', 'ai_zm_dlc4_keeper_prtctr_idle_attack_combo', 'ai_zm_dlc4_keeper_prtctr_idle_attack_left',
    'ai_zm_dlc4_keeper_prtctr_idle_attack_right', 'ai_zm_dlc4_keeper_prtctr_idle_attack_up',
    'ai_zm_dlc4_keeper_prtctr_walk_attack', 'ai_zm_dlc4_keeper_prtctr_run_attack', 'ai_zm_dlc4_keeper_prtctr_sprint_attack',
    'ai_zm_dlc4_keeper_prtctr_bamf_in', 'ai_zm_dlc4_keeper_prtctr_bamf_out', 'ai_zm_dlc4_keeper_prtctr_intro', 'ai_zm_dlc4_keeper_prtctr_outtro',
    'ai_zm_dlc4_keeper_prtctr_revive_intro', 'ai_zm_dlc4_keeper_prtctr_revive_loop', 'ai_zm_dlc4_keeper_prtctr_revive_outtro',
    'ai_zm_dlc4_keeper_prtctr_ee_idle', 'ai_zm_dlc4_keeper_cmpn_revive',
    'ai_zombie_zod_keeper_attack_v1', 'ai_zombie_zod_keeper_attack_v2', 'ai_zombie_zod_keeper_attack_v4',
    'ai_zombie_zod_keeper_dth_f_v1',
    # NOT ai_zombie_zod_keeper_run_attack_v4: the Keeper GDT already owns that block (gdtdb refuses a duplicate
    # asset across GDTs and every build in the repo failed on it, 2026-09-30 23:48); the mapping references it as-is
]

# THE DEALER'S MOTION (anim mapping overrides; every other row is the Keeper's):
#   TWO STATES on the zombie blackboard's arms position (the Dealer script sets self.zombie_arms_position):
#   "up"   = STATE ONE, the masked Dealer LEVITATING with the scythe: the Protector's glide (walk 85 in/s, run
#            118, sprint 159) lifted 14 in, his idle and scans, two scythe cuts (the Protector's left / right swipes)
#   "down" = STATE TWO, the CRACKED MASK (user 2026-10-02), ON THE GROUND with the machine gun: the enslaved Keeper's stepping
#            run / sprint (it has no walk: its run at walk speed, as the Keeper's own table does), its idle, its
#            four swipes + the SoE keeper's three, its run-swipes, its four deaths
#   Every clip is the authored tod_dealer_f_* / tod_dealer_g_* file (author_clips.py), never a raw pack clip.
F = lambda n: 'tod_dealer_f_' + n
G = lambda n: 'tod_dealer_g_' + n
WALK_F, RUN_F, SPRINT_F = F('walk'), F('run'), F('sprint')
WALK_G, RUN_G, SPRINT_G = G('ens_run_v1'), G('ens_run_v1'), G('ens_sprint_v1')
SWIPES_F = [F('idle_attack_left'), F('idle_attack_right')]
SWIPES_G = [G('ens_attack_v%d' % i) for i in (1, 2, 3, 4)] + [G('zod_attack_v1'), G('zod_attack_v2'), G('zod_attack_v4')]
RUN_SWIPES_G = [G('ens_run_attack_v%d' % i) for i in (1, 2, 3, 4)] + [G('zod_run_attack_v4')]
DEATHS_G = [G('ens_dth_v%d' % i) for i in (1, 2, 3, 4)]
# THE LINKER'S RULES (2026-10-01, paid for three times on the shared root): a clip named by a move@zombie
# selector row must carry "looping" 1 AND "loopsync" 1 ("requires loop sync animations"); a clip named by an
# idle@zombie or melee@zombie row must carry NEITHER ("requires non-looping" / "non-loop sync"), and the pack's
# own Protector idle_attack blocks ship looping 1, so the flags are FORCED both ways from the generated tables
# (selector_loop_sets below), never hand-listed. SCRIPT_LOOPS = loops no selector row names, played by script.
SCRIPT_LOOPS = {F('revive_loop'), F('ee_idle')}
OVERRIDES = {}
for arms, (walk, run, sprint) in (('au', (WALK_F, RUN_F, SPRINT_F)), ('ad', (WALK_G, RUN_G, SPRINT_G))):
    for v in range(4):
        OVERRIDES['anim_zombie_walk_%s_v%d' % (arms, v)] = [walk]
        OVERRIDES['anim_zombie_run_%s_v%d' % (arms, v)] = [run]
        OVERRIDES['anim_zombie_sprint_%s_v%d' % (arms, v)] = [sprint]
        # pains ride the same clips (the Keeper's pain rows name clips this map never ships)
        OVERRIDES['anim_zombie_walk_%s_v%d_pain_chest_f' % (arms, v)] = [walk]
        OVERRIDES['anim_zombie_run_%s_v%d_pain_chest_f' % (arms, v)] = [run]
        OVERRIDES['anim_zombie_sprint_%s_v%d_pain_chest_f' % (arms, v)] = [sprint]
OVERRIDES['anim_zombie_melee_walk_au'] = SWIPES_F
OVERRIDES['anim_zombie_melee_run_au'] = SWIPES_F
OVERRIDES['anim_zombie_melee_walk_ad'] = SWIPES_G
OVERRIDES['anim_zombie_melee_run_ad'] = RUN_SWIPES_G
OVERRIDES['anim_zombie_super_sprint'] = [SPRINT_F]
OVERRIDES['anim_zombie_keeper_idle'] = [F('idle'), F('idle_scan_1'), F('idle_scan_2')]
OVERRIDES['anim_zombie_death_front'] = DEATHS_G   # the Keeper's one death row (its tree reads no direction)
# script-only aliases (AnimScripted by _tod_dealer_finale.gsc; an %anim must be in the mapping table - the Mangler lesson)
SCRIPT_ALIASES = {
    'anim_dealer_intro': F('intro'),
    'anim_dealer_outtro': F('outtro'),
    'anim_dealer_bamf_in': F('bamf_in'),
    'anim_dealer_bamf_out': F('bamf_out'),
    'anim_dealer_cast_up': F('idle_attack_up'),
    'anim_dealer_cast_combo': F('idle_attack_combo'),
    'anim_dealer_cast_left': F('idle_attack_left'),
    'anim_dealer_cast_right': F('idle_attack_right'),
    'anim_dealer_idle_attack': F('idle_attack'),
    'anim_dealer_channel_intro': F('revive_intro'),
    'anim_dealer_channel_loop': F('revive_loop'),
    # Dedicated gun holds live in the independently generated combat sidecar GDT.
    'anim_dealer_weapon_shock': 'tod_dealer_c_shock',
    'anim_dealer_weapon_burst': 'tod_dealer_c_burst',
    'anim_dealer_channel_outtro': F('revive_outtro'),
    'anim_dealer_ee_idle': F('ee_idle'),
    'anim_dealer_kneel': G('cmpn_revive'),
    'anim_dealer_death_front': G('zod_dth_f_v1'),
    'anim_dealer_walk_attack': F('walk_attack'),
    'anim_dealer_run_attack': F('run_attack'),
    'anim_dealer_sprint_attack': F('sprint_attack'),
    # the selector table's state-two rows (idle@zombie / move@zombie, ARMS_DOWN)
    'anim_dealer_idle_ground': G('ens_idle'),
    'anim_dealer_super_sprint_ground': SPRINT_G,
}
DEATH_START = 'dealerDeathStart'

# HIS OWN SOUNDS ON HIS OWN CLIPS (W2B / PK10, 2026-10-05). Every authored clip's GDT block is cloned from its source's,
# so its "Sound" custom notes named the Revelations Keeper Protector's aliases (zmb_keeperprot_* / zmb_vocals_keeperprot_*
# / keeper_teleport_* / keeper_spawn_*): DLC4 aliases no table this map loads defines, so every swing, grunt and bamf of
# his played NOTHING. The pack's state-two (enslaved Keeper) clips name "zombie_melee" / "footstep_*_large" as Sound
# notes: no alias by those names exists either. Each such note now names the Dealer's own alias (tools/dealer_sfx/
# make_sounds.py -> sound/aliases/tod_dealer.csv, 3D on him); a second note on the same beat (the pack's twin
# keeper_teleport_* / keeper_spawn_* rows, the outtro's ambient growl) goes quiet (action None) so a beat plays ONE sound.
# ONLY "Sound" actions are touched: the "Self Notify" zombie_melee note is the melee hit itself and stays exactly as it is.
NOTE_ALIASES = {
    'zmb_keeperprot_attack': 'tod_dealer_scythe_swing',          # state one: the scythe cut (the swipe frame)
    'zmb_keeperprot_attack_large': 'tod_dealer_scythe_swing',    # the combo's last, rising cut
    'zmb_vocals_keeperprot_attack': 'tod_dealer_attack_vox',     # his effort as the swipe starts (65 % of the time: the row's probability)
    'zmb_keeperprot_teleport_out': 'tod_dealer_bamf_out',        # bamf_in = he steps INTO the rift (vanishes)
    'zmb_keeperprot_teleport_in': 'tod_dealer_bamf_in',          # bamf_out = he steps out of it
    'zmb_keeperprot_spawn_in': 'tod_dealer_bamf_in',             # the intro's arrival
    'zmb_keeperprot_spawn_out': 'tod_dealer_bamf_out',           # the outtro's leaving
    'keeper_teleport_out': None, 'keeper_teleport_in': None,     # the pack's twin rows on the same bamf: one sound per beat
    'keeper_spawn_in': None, 'keeper_spawn_out': None,
    'zmb_vocals_keeperprot_amb': None,                           # the outtro's ambient groan: his own voice owns his words
    'zombie_melee': 'tod_dealer_bash',                           # state two: the gun swung like a club (Sound note ONLY)
    'footstep_left_large': 'tod_dealer_step',                    # state two: his boots on the house's steel
    'footstep_right_large': 'tod_dealer_step',
    'dlc4/genesis/fx_keeperprot_spawn': None,                    # an EFFECT path the pack exported as a Sound note: no alias, quiet
}


def remap_sound_notes(blk):
    """every "Sound" custom note naming a NOTE_ALIASES key names the Dealer's own alias (or goes quiet); -> (blk, n)"""
    n = 0
    for key in ['customnote%d' % i for i in range(50)] + ['sound_customnote%d' % i for i in range(20)]:
        if K.field(blk, key + 'action') != 'Sound':
            continue
        alias = K.field(blk, key + 'actionparam1')
        if alias not in NOTE_ALIASES:
            continue
        new = NOTE_ALIASES[alias]
        if new is None:
            blk = K.set_field(blk, key + 'action', 'None')
            blk = K.set_field(blk, key + 'actionparam1', '')
        else:
            blk = K.set_field(blk, key + 'actionparam1', new)
        n += 1
    return blk, n


def blockify(name, kind, fields):
    def val(v):
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).replace('"', '\\"').replace('\r', '\\r').replace('\n', '\\n')
    return '\t"%s" ( "%s.gdf" )\n\t{\n' % (name, kind) + ''.join('\t\t"%s" "%s"\n' % (k, val(v)) for k, v in fields.items() if v is not None) + '\t}'


def image_block(kit_blocks, group, suffix, png):
    donor = kit_blocks['i_tod_cyber_kit_' + suffix]
    b = K.rename(donor, 'i_tod_dealer_%s_%s' % (group, suffix))
    return K.set_field(b, 'baseImage', r'model_export\tod_dealer\_images\%s' % png)


def material_block(kit_blocks, group):
    b = K.rename(kit_blocks['mtl_tod_cyber_kit'], 'mtl_tod_dealer_' + group)
    surf, scale, gmin, gmax = SURFACE[group]
    for key, suffix in (('colorMap', 'c'), ('normalMap', 'n'), ('cosinePowerMap', 'g'), ('specColorMap', 's'), ('colorMap00', 'e')):
        b = K.set_field(b, key, 'i_tod_dealer_%s_%s' % (group, suffix))
    b = K.set_field(b, 'surfaceType', surf)
    b = K.set_field(b, 'scaleRGB', str(scale))
    b = K.set_field(b, 'glossRangeMin', str(gmin))
    b = K.set_field(b, 'glossRangeMax', str(gmax))
    return b


def xmodel_block(keeper_blocks):
    b = K.rename(keeper_blocks['tod_keeper_body'], BODY)
    b = K.set_field(b, 'filename', r'tod_dealer\tod_dealer_lod0.xmodel_bin')
    # the converter derives the distance LODs from LOD0, the way the skinned cyber roster ships
    for key, pct in (('MediumLod', 50), ('LowLod', 25), ('LowestLod', 12), ('Lod4', 7), ('Lod5', 4), ('Lod6', 2), ('Lod7', 1)):
        b = K.set_field(b, 'autogen' + key, '1')
        b = K.set_field(b, 'autogen%sPercent' % key, str(pct))
    b = K.set_field(b, 'lodPresets', 'performance')
    return b


def am_text(keeper_am):
    rows = []
    seen = set()
    for line in keeper_am.rstrip('\n').split('\n'):
        if not line or line.startswith('#'):
            rows.append(line); continue
        alias = line.split(',')[0]
        seen.add(alias)
        if alias in OVERRIDES:
            rows.append(alias + ',' + ','.join(OVERRIDES[alias]) + ',')
        else:
            rows.append(line)
    for alias, clip in sorted(SCRIPT_ALIASES.items()):
        assert alias not in seen, alias
        rows.append('%s,%s,' % (alias, clip))
    missing = [a for a in OVERRIDES if a not in seen]
    assert not missing, 'Keeper AM lacks aliases the Dealer overrides: %s' % missing
    return '\n'.join(rows) + '\n'


def ast_text(keeper_ast):
    """the Keeper's selector table with the idle and move selectors split on _arms_position: ARMS_UP = state one
    (the float set), ARMS_DOWN = state two (the ground set); a trailing * row keeps the Keeper's default"""
    t = keeper_ast.replace('\r\n', '\n')
    old_idle = ('idle@zombie\n_arms_position,_has_legs,_blend_in_time,_blend_out_time,_animation_alias,_animation_mocomp,\n'
                '*,*,0.2,0.2,ANIM_ZOMBIE_KEEPER_IDLE,MOCOMP_GENERIC_ANIMATION,\n')
    new_idle = ('idle@zombie\n_arms_position,_has_legs,_blend_in_time,_blend_out_time,_animation_alias,_animation_mocomp,\n'
                'ARMS_UP,*,0.2,0.2,ANIM_ZOMBIE_KEEPER_IDLE,MOCOMP_GENERIC_ANIMATION,\n'
                'ARMS_DOWN,*,0.2,0.2,ANIM_DEALER_IDLE_GROUND,MOCOMP_GENERIC_ANIMATION,\n'
                '*,*,0.2,0.2,ANIM_ZOMBIE_KEEPER_IDLE,MOCOMP_GENERIC_ANIMATION,\n')
    assert old_idle in t, 'Keeper AST idle selector changed shape'
    t = t.replace(old_idle, new_idle)
    m0 = t.index('move@zombie\n'); m1 = t.index('\n,\n', m0)
    block = t[m0:m1].split('\n')
    assert block[1] == '_locomotion_speed,_blend_in_time,_blend_out_time,_animation_alias,_animation_mocomp,', block[1]
    rows = ['move@zombie', '_arms_position,' + block[1]]
    for row in block[2:]:
        alias = row.split(',')[3]
        if alias.startswith('ANIM_ZOMBIE_SUPER_SPRINT'):
            rows.append('ARMS_UP,' + row)
            rows.append('ARMS_DOWN,' + row.replace('ANIM_ZOMBIE_SUPER_SPRINT', 'ANIM_DEALER_SUPER_SPRINT_GROUND'))
            rows.append('*,' + row)
        else:
            assert '_AU_' in alias, row
            rows.append('ARMS_UP,' + row)
            rows.append('ARMS_DOWN,' + row.replace('_AU_', '_AD_'))
    t = t[:m0] + '\n'.join(rows) + t[m1:]
    return t



def selector_loop_sets(am, ast):
    """(loop, noloop): the clips the move@zombie rows reach (must loop + loop-sync) and the clips the
    idle@zombie / melee@zombie rows reach (must not); mirrors the linker's own check"""
    amap = {}
    for line in am.replace('\r\n', '\n').split('\n'):
        if not line or line.startswith('#'):
            continue
        c = [x.strip() for x in line.split(',') if x.strip()]
        amap[c[0].lower()] = c[1:]
    t = ast.replace('\r\n', '\n')
    def clips_of(table):
        i = t.index(table + '\n'); j = t.index('\n,\n', i)
        found = set()
        for row in t[i:j].split('\n')[2:]:
            for m in re.finditer(r'\b(ANIM_[A-Z0-9_]+)\b', row):
                found.update(amap.get(m.group(1).lower(), []))
        return found
    loop = clips_of('move@zombie')
    noloop = clips_of('idle@zombie') | clips_of('melee@zombie')
    both = loop & noloop
    assert not both, 'clip(s) on both a move row and an idle/melee row (the linker refuses either way): %s' % sorted(both)
    return loop, noloop

def bt_text(keeper_bt):
    tree = json.loads(keeper_bt)
    hits = []
    def walk(n):
        for k in ('StartFunction', 'UpdateFunction', 'TerminateFunction'):
            if n.get(k, '').lower() == 'genesiskeeperdeathstart':
                n[k] = DEATH_START.lower(); hits.append(k)
        for c in n.get('children') or []:
            walk(c)
    walk(tree)
    assert hits == ['StartFunction'], hits
    return json.dumps(tree, indent=4) + '\n'


DONORS = os.path.join(REPO, 'art', 'dealer_boss', 'donors')
DONOR_IMG_DIR = os.path.join(MODEL_DIR, '_donor_images')
WEAPON_MODELS = {'dg2': 'tod_dealer_dg2', 'dingo': 'tod_dealer_lmg'}
# donor materials every model names that the pack does not define: stock, already in the tools root (checked 2026-09-30)
STOCK_MATERIALS = {'mtl_wpn_t7_paint_left', 'mtl_wpn_t7_paint_right', 'mtl_wpn_t7_paint_top'}
# a Dingo sight material with no block anywhere (pack or tools root): authored from a sibling Dingo material
AUTHORED_MATERIALS = {'mtl_wpn_t7_smg_wvl_tritium_grn': 'mtl_wpn_t7_lmg_dingo_sight_front'}


def donor_blocks(dman, files, out):
    """The DG-2 / Dingo materials and images, byte-copied from the pack under their own names (none is in the
    tools root), images repointed into model_export/tod_dealer. ONLY what the two weapon models name: the Dealer
    is his own character (user 2026-10-02) and no other donor (no borrowed head) ships, whatever an older
    donors/manifest.json still lists."""
    need_mats = set()
    for key in WEAPON_MODELS:
        need_mats |= set(dman['models'][key]['materials'])
    need_imgs = set()
    for name in need_mats:
        info = dman['materials'].get(name) or {}
        need_imgs |= set((info.get('maps') or {}).values())
        if name in AUTHORED_MATERIALS:
            need_imgs |= set((dman['materials'][AUTHORED_MATERIALS[name]].get('maps') or {}).values())
    for name, info in sorted(dman['images'].items()):
        if name not in need_imgs or not info.get('png'):
            continue
        b = info.get('block')
        if not b:
            continue
        out.append(K.set_field(b, 'baseImage', r'model_export\tod_dealer\_donor_images\%s' % info['png']))
        files[os.path.join(DONOR_IMG_DIR, info['png'])] = os.path.join(DONORS, '_images', info['png'])
    for name, info in sorted(dman['materials'].items()):
        if name not in need_mats:
            continue
        if info.get('block'):
            out.append(info['block'])
        elif name in AUTHORED_MATERIALS:
            out.append(K.rename(dman['materials'][AUTHORED_MATERIALS[name]]['block'], name))
        else:
            assert name in STOCK_MATERIALS, 'donor material neither in the pack nor known stock: ' + name
    for key, new in WEAPON_MODELS.items():
        info = dman['models'][key]
        b = K.rename(info['block'], new)
        b = K.set_field(b, 'filename', r'tod_dealer\%s' % info['file'])
        for lodfield in ('mediumLod', 'lowLod', 'lowestLod', 'lod4File', 'lod5File', 'lod6File', 'lod7File'):
            if K.field(b, lodfield) is not None:
                b = K.set_field(b, lodfield, '')
        for key2, pct in (('MediumLod', 50), ('LowLod', 25), ('LowestLod', 12), ('Lod4', 7), ('Lod5', 4), ('Lod6', 2), ('Lod7', 1)):
            b = K.set_field(b, 'autogen' + key2, '1'); b = K.set_field(b, 'autogen%sPercent' % key2, str(pct))
        out.append(b)
        files[os.path.join(MODEL_DIR, info['file'])] = os.path.join(DONORS, info['file'])


def build(tmp):
    man = json.load(open(EXPORT_MANIFEST))
    dman = json.load(open(os.path.join(DONORS, 'manifest.json')))
    keeper_blocks = K.index_blocks(K.read(KEEPER_GDT))
    kit_blocks = K.index_blocks(K.read(KIT_GDT))
    members = [r'source_data\%s\t7_zm_ai.gdt' % K.MB]
    K.extract(members, tmp)
    root = os.path.join(tmp, K.PACK)
    pack_blocks = K.index_blocks(K.read(os.path.join(root, 'source_data', K.MB, 't7_zm_ai.gdt')))

    out = []
    files = {}
    for g in GROUPS:
        for suffix, png in sorted(man['groups'][g]['images'].items()):
            assert png == 'i_tod_dealer_%s_%s.png' % (g, suffix), png
            assert os.path.exists(os.path.join(MODEL_DIR, '_images', png)), png
            out.append(image_block(kit_blocks, g, suffix, png))
    for g in GROUPS:
        out.append(material_block(kit_blocks, g))
    # the scythe: its own small atlas and a rigid xmodel attached to tag_weapon_right by script
    assert man.get('scythe'), 'the export carries no scythe'
    for suffix, png in sorted(man['scythe']['images'].items()):
        out.append(image_block(kit_blocks, 'scythe', suffix, png))
    SURFACE['scythe'] = ('metal', 6, 2, 16)
    out.append(material_block(kit_blocks, 'scythe'))
    out.append(xmodel_block(keeper_blocks))
    # STATE TWO: the same body with the CRACKED mask (export_native.py writes it from the same bake)
    b = K.rename(keeper_blocks['tod_keeper_body'], BODY + '_cracked')
    b = K.set_field(b, 'filename', r'tod_dealer\tod_dealer_cracked_lod0.xmodel_bin')
    for key2, pct in (('MediumLod', 50), ('LowLod', 25), ('LowestLod', 12), ('Lod4', 7), ('Lod5', 4), ('Lod6', 2), ('Lod7', 1)):
        b = K.set_field(b, 'autogen' + key2, '1'); b = K.set_field(b, 'autogen%sPercent' % key2, str(pct))
    out.append(b)
    b = K.rename(keeper_blocks['tod_keeper_body'], 'tod_dealer_scythe')
    b = K.set_field(b, 'filename', r'tod_dealer\tod_dealer_scythe_lod0.xmodel_bin')
    for key2, pct in (('MediumLod', 50), ('LowLod', 25), ('LowestLod', 12), ('Lod4', 7), ('Lod5', 4), ('Lod6', 2), ('Lod7', 1)):
        b = K.set_field(b, 'autogen' + key2, '1'); b = K.set_field(b, 'autogen%sPercent' % key2, str(pct))
    out.append(b)
    donor_blocks(dman, files, out)
    b = K.rename(keeper_blocks['c_tod_keeper'], CHARACTER)
    b = K.set_field(b, 'body', BODY); b = K.set_field(b, 'previewxmodel', BODY)
    out.append(b)

    # the raw pack sources go beside the master for author_clips.py (never zoned, never synced)
    xanim_members = []
    dup = [c for c in SOURCE_CLIPS if c in keeper_blocks]
    assert not dup, 'clip(s) already owned by tod_keeper.gdt (gdtdb refuses a duplicate asset): ' + ', '.join(dup)
    for c in SOURCE_CLIPS:
        assert c in pack_blocks, 'pack has no xanim block for ' + c
        src = K.field(pack_blocks[c], 'filename')
        base = src.replace('\\\\', '\\').split('\\')[-1]
        xanim_members.append('xanim_export\\' + src.replace('\\\\', '\\'))
        files[os.path.join(CLIPS_SRC, base)] = os.path.join(root, 'xanim_export', src.replace('\\\\', os.sep).replace('\\', os.sep))
    # one GDT block per AUTHORED clip, cloned from its source's block (the notetracks - melee fire, teleport
    # sound and fx - ride along), pointed at the authored file
    if not os.path.exists(CLIPS_REPORT):
        raise SystemExit('no authored clips: run author_clips.py (background Blender) first')
    report = json.load(open(CLIPS_REPORT))
    am_out = am_text(K.read(os.path.join(REPO, 'animtables', 'tod_keeper.ai_am')))
    ast_out = ast_text(K.read(os.path.join(REPO, 'animtables', 'tod_keeper.ai_ast')))
    loop_clips, noloop_clips = selector_loop_sets(am_out, ast_out)
    authored = {}
    for out_name, st in sorted(report['clips'].items()):
        src = st['source']
        sb = pack_blocks.get(src) or keeper_blocks.get(src)
        assert sb is not None, 'no xanim block anywhere for the source ' + src
        name = out_name[:-len('.xanim_bin')]
        b = K.rename(sb, name)
        b = K.set_field(b, 'filename', r'tod_dealer\%s' % out_name)
        if name in loop_clips or name in SCRIPT_LOOPS:
            b = K.set_field(b, 'looping', '1')
            b = K.set_field(b, 'loopsync', '1')   # the move selector's rows "require loop sync animations" (the Keeper's sprint carries both)
        elif name in noloop_clips:
            b = K.set_field(b, 'looping', '0')    # idle@zombie / melee@zombie rows refuse a looping clip (the pack's idle_attack blocks ship 1)
            b = K.set_field(b, 'loopsync', '0')
        if K.field(b, 'model'):
            b = K.set_field(b, 'model', r'tod_keeper\c_zom_dlc4_keeper_fb.XMODEL_BIN')
        if K.field(b, 'previewModel') is not None:
            b = K.set_field(b, 'previewModel', BODY)
        b, _ = remap_sound_notes(b)   # PK10: his clips play his own sounds (the pack's notes named the Keeper's)
        out.append(b)
        p = os.path.join(XANIM_DIR, out_name)
        assert os.path.exists(p) and sha(p) == st['sha256'], 'authored clip missing or stale (re-run author_clips.py): ' + out_name
        authored[name] = st['sha256']
    for c in SOURCE_CLIPS:   # the raw copies an earlier install put beside the authored clips are not shipped
        stale = os.path.join(XANIM_DIR, c + '.xanim_bin')
        if os.path.exists(stale):
            os.remove(stale)
    man['authored'] = authored

    over = {'animMappingTableName': 'tod_dealer.ai_am', 'animSelectorTableName': 'tod_dealer.ai_ast',
            'animStateMachineName': 'tod_dealer.ai_asm', 'behaviorTreeName': 'tod_dealer.ai_bt',
            'character1': CHARACTER, 'character2': '', 'csvInclude': '', 'aiFxBundle': '', 'radiantModel': BODY,
            'archetype': 'dealer'}
    for src, new, parent in (('archetype_tod_keeper', 'archetype_tod_dealer', None), ('variant_tod_keeper', 'variant_tod_dealer', 'archetype_tod_dealer'),
                             ('spawner_tod_keeper', 'spawner_tod_dealer', 'variant_tod_dealer')):
        b = K.rename(keeper_blocks[src], new, parent)
        for k, v in over.items():
            if K.field(b, k) is not None or parent is None:
                b = K.set_field(b, k, v)
        out.append(b)

    K.extract(xanim_members, tmp)
    gdt = '{\n' + '\n'.join(out) + '\n}\n'
    texts = {OUT_GDT: gdt,
             AM_OUT: am_out,
             AST_OUT: ast_out,
             ASM_OUT: K.read(os.path.join(REPO, 'share', 'raw', 'animstatemachines', 'tod_keeper.ai_asm')),
             BT_OUT: bt_text(K.read(os.path.join(REPO, 'share', 'raw', 'behavior', 'tod_keeper.ai_bt')))}
    return files, texts, man


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    check = '--check' in sys.argv
    if not os.path.exists(EXPORT_MANIFEST):
        raise SystemExit('no export manifest: run export_native.py first')
    if not os.path.exists(K.RAR):
        raise SystemExit('T7 asset pack not found: ' + K.RAR)
    tmp = tempfile.mkdtemp(prefix='tod_dealer_')
    try:
        files, texts, man = build(tmp)
        bad = []
        manifest = {'pack': os.path.basename(K.RAR), 'export_manifest_sha256': sha(EXPORT_MANIFEST), 'master_sha256': man['master_sha256'],
                    'clips': sorted(man['authored']), 'authored': man['authored'], 'source_clips': SOURCE_CLIPS,
                    'script_aliases': SCRIPT_ALIASES, 'overrides': {k: v for k, v in OVERRIDES.items()},
                    'death_start': DEATH_START, 'files': {}, 'texts': {},
                    'lod0_triangles': {r['model']: r['triangles_total'] for r in man['lods'] if r['lod'] == 0},
                    'weapon_models': WEAPON_MODELS, 'states': man.get('states')}
        for dst, src in sorted(files.items()):
            if not os.path.exists(src):
                raise SystemExit('pack file missing: ' + src)
            want = sha(src)
            manifest['files'][os.path.relpath(dst, REPO).replace('\\', '/')] = want
            if check:
                if not os.path.exists(dst) or sha(dst) != want:
                    bad.append(os.path.relpath(dst, REPO))
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
        for dst, text in sorted(texts.items()):
            data = text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')   # CRLF: the AI tables assert otherwise (Keeper, 2026-09-28)
            manifest['texts'][os.path.relpath(dst, REPO).replace('\\', '/')] = hashlib.sha256(data).hexdigest()
            if check:
                if not os.path.exists(dst) or open(dst, 'rb').read() != data:
                    bad.append(os.path.relpath(dst, REPO))
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                open(dst, 'wb').write(data)
        for lod in man['lods']:
            if lod['lod'] != 0:
                continue   # the converter derives distance LODs from LOD0; the others are reference exports
            p = os.path.join(REPO, lod['file'])
            if check and (not os.path.exists(p) or sha(p) != lod['sha256']):
                bad.append(lod['file'])
        for png, h in man['textures'].items():
            p = os.path.join(MODEL_DIR, '_images', png)
            if check and (not os.path.exists(p) or sha(p) != h):
                bad.append('model_export/tod_dealer/_images/' + png)
        if check:
            if bad:
                raise SystemExit('dealer install --check: STALE/MISSING:\n  ' + '\n  '.join(bad))
            print('dealer install --check OK: %d files + %d generated texts, lod0 %s' % (len(files), len(texts), manifest['lod0_triangles']))
        else:
            open(MANIFEST, 'w').write(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
            print('dealer install: wrote %d clips + %d generated texts -> %s' % (len(files), len(texts), REPO))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
