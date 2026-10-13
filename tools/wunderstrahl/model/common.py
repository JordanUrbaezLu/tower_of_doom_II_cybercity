"""THE WUNDERSTRAHL model track (docs/219): shared paths, hashing, PyCoD access and GDT text helpers.

Importable from Blender (MCP steps) and from plain Python (install_art.py / verify_art.py). No bpy at import time.
Units are BO3 inches = 1 Blender unit; axes are the native ones (X forward, Y left, Z up), so no conversion exists.
"""
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / 'tools/wunderstrahl/model'
SRC_KIT = ROOT / 'tmp/wunderstrahl/src/T7 Assets V2.8'
SRC_T7 = SRC_KIT / 'model_export/_midgetblaster/weapons/t7'
SRC_VIEW = SRC_T7 / 'wpn_t7_zmb_dg2_view/wpn_t7_zmb_dg2_view_LOD0.XMODEL_BIN'
SRC_SKEL = SRC_T7 / 'wpn_t7_zmb_dg2_view/wpn_t7_zmb_dg2_skeleton.XMODEL_BIN'
SRC_WORLD = [SRC_T7 / ('wpn_t7_zmb_dg2_world/wpn_t7_zmb_dg2_world_LOD%d.XMODEL_BIN' % i) for i in range(8)]
SRC_IMG = SRC_T7 / 'wpn_t7_zmb_dg2_view/_images'
SRC_XANIM = SRC_KIT / 'xanim_export/_midgetblaster/black_ops_3'
SRC_GDT = SRC_KIT / 'source_data/_midgetblaster/t7_base_dg2.gdt'

ART = ROOT / 'art/wunderstrahl'
REVIEW = ART / 'review'
KIT = ART / 'engine_kit'
OUT = ROOT / 'model_export/tod_wunderstrahl'
IMG = OUT / '_images'
XOUT = ROOT / 'xanim_export/tod_wunderstrahl'
STAGE = ROOT / 'tmp/wunderstrahl/stage'
SCRATCH = ROOT / 'tmp/wunderstrahl/scratch'

# The DG-2 rig contract: the 26+ vm_dg2 clips animate these exact names, parents and rest offsets.
VIEW_BONES = ['tag_weapon', 'tag_bolt_animate', 'tag_brass', 'tag_bulb_1', 'tag_bulb_2', 'tag_bulb_3', 'tag_clip',
              'tag_flash', 'tag_fx', 'tag_switch_animate', 'tag_switch_cover_animate', 'tag_bolt_handle_animate']
WORLD_BONES = ['tag_weapon', 'tag_brass', 'tag_flash', 'tag_fx']
TAG_FLASH = (40.9997, 0.0001, 3.1414)      # measured from the source view + world rigs; it must never move

# DG-2 material slot -> the Wunderstrahl material that replaces it (the three script bulbs collapse into ONE static
# bulb material: nothing drives their per-bulb shader constants on this map, they glow from the raise on).
MATERIAL_MAP = {
    'mtl_wpn_t7_zmb_dg2_wood': 'mtl_tod2_ws_stock',
    'mtl_wpn_t7_zmb_dg2_pipe': 'mtl_tod2_ws_coil',
    'mtl_wpn_t7_zmb_dg2_body': 'mtl_tod2_ws_body',
    'mtl_wpn_t7_zmb_dg2_glass': 'mtl_tod2_ws_glass',
    'mtl_wpn_t7_zmb_dg2_metal': 'mtl_tod2_ws_frame',
    'mtl_wpn_t7_zmb_dg2_glow': 'mtl_tod2_ws_glow',
    'mtl_wpn_t7_zmb_dg2_power': 'mtl_tod2_ws_core',
    'mtl_wpn_t7_zmb_dg2_bulb1': 'mtl_tod2_ws_bulb',
    'mtl_wpn_t7_zmb_dg2_bulb2': 'mtl_tod2_ws_bulb',
    'mtl_wpn_t7_zmb_dg2_bulb3': 'mtl_tod2_ws_bulb',
}
EMITTER_MATERIAL = 'mtl_tod2_ws_emitter'   # every new part (lens, rings, struts, conduits, clips) shares one atlas
DROP_MATERIAL = 'mtl_x2icon_gold'          # the drop family's stock material: never redefined in our GDT

# The 28 first-person clips of the kit, renamed vm_dg2_<suffix> -> tod2_ws_vm_<suffix> (byte-identical copies).
CLIP_SUFFIXES = ['ads_base_down', 'ads_base_up', 'crawl_b', 'crawl_f', 'crawl_in', 'crawl_l', 'crawl_out', 'crawl_r',
                 'fall', 'fire', 'fire_ads', 'first_raise', 'idle', 'jump', 'jump_land', 'pullout', 'pullout_quick',
                 'putaway', 'putaway_quick', 'reload_empty', 'slide_air_in', 'slide_in', 'slide_loop', 'slide_out',
                 'sprint_in', 'sprint_loop', 'sprint_out', 'walk_f']

PALETTE = {   # sRGB 0-255; the user's call: a YELLOW beam core, warm gold accents, no cyan/blue anywhere
    'core': (255, 214, 64),
    'core_hot': (255, 246, 196),
    'amber': (255, 156, 24),
    'gold': (214, 168, 74),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def pycod():
    path = str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD')
    if path not in sys.path:
        sys.path.insert(0, path)
    from PyCoD import xmodel, xanim
    return xmodel, xanim


def load_model(p, split=True):
    xmodel, _ = pycod()
    m = xmodel.Model()
    m.LoadFile_Bin(str(p), split_meshes=split)
    return m


def load_anim(p):
    _, xanim = pycod()
    a = xanim.Anim()
    a.LoadFile_Bin(str(p))
    return a


def bone_rows(model):
    return [(b.name, b.parent, tuple(round(x, 4) for x in b.offset),
             tuple(tuple(round(x, 5) for x in row) for row in b.matrix)) for b in model.bones]


GDT_BLOCK = re.compile(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{([^}]*)\}')
GDT_FIELD = re.compile(r'"([^"\r\n]+)"\s*"([^"\r\n]*)"')


def parse_gdt_text(text):
    out = {}
    for m in GDT_BLOCK.finditer(text):
        out[m.group(1)] = (m.group(2), dict(GDT_FIELD.findall(m.group(3))))
    return out


def parse_gdt(path):
    return parse_gdt_text(Path(path).read_text(encoding='latin1'))


def gdt_block(name, kind, fields):
    """One GDT block in the house layout (tab-indented, quoted). Values are written verbatim: callers pass
    GDT-escaped text (a path separator is the two characters backslash backslash)."""
    return ('\t"' + name + '" ( "' + kind + '" )\n\t{\n' +
            ''.join('\t\t"' + k + '" "' + str(v) + '"\n' for k, v in fields.items()) + '\t}\n')


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
