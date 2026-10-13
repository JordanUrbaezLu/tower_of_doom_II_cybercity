"""Load geometry helpers into an existing shop scene without resetting it."""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'art/partner_shop'
scene = bpy.context.scene
if not scene.get('tod2_shop_studio'): raise RuntimeError('Not the shop studio')
shell=bpy.data.collections['SHOP | 01 HUT - always present']
detail=bpy.data.collections['SHOP | 02 HARDWARE - always present']
stock=bpy.data.collections['SHOP | 03 INVENTORY - always present']
vendor=bpy.data.collections['SHOP | 04 MERCHANT - active only']
active=bpy.data.collections['SHOP | 05 ACTIVE lamps']
stage=bpy.data.collections['SHOP | 90 STUDIO - exclude from export']
anchors=bpy.data.collections['SHOP | 91 SOCKETS - metadata only']
_src=(ROOT/'tools/partner_shop/01_structure.py').read_text(encoding='utf-8')
exec(compile(_src[_src.index('def material('):_src.index('# Raised skid')],str(ROOT/'tools/partner_shop/01_structure.py'),'exec'))
