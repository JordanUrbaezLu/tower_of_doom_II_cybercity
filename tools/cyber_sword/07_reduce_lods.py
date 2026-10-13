"""Explicit distance meshes from the baked native geometry; no rebake."""
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
kit=ROOT/'art/cyber_sword/engine_kit'
source=ROOT/'tools/cyber_reference_one/reduce_game_lods.py'
code=source.read_text()
needle='            bpy.ops.object.modifier_apply(modifier=mod.name)'
assert code.count(needle)==1
code=code.replace(needle,needle+'''
            ob.data.normals_split_custom_set([(0,0,0)]*len(ob.data.loops))
            ob.data.set_sharp_from_angle(angle=math.radians(45))
            normal=ob.modifiers.new('Final machined normals','WEIGHTED_NORMAL');normal.keep_sharp=True
            bpy.ops.object.modifier_apply(modifier=normal.name)''')
code=code.replace('if n.length_squared<.9:n=tri.normal.normalized()',
                  'if tri.center.z>5 or n.length_squared<.9 or n.dot(tri.normal)<.2:n=tri.normal.normalized()')
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__',
    'CYBER_LOD_SOURCE':kit,'CYBER_LOD_OUTPUT':kit})
