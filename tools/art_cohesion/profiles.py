"""Explicit native finish profiles; material tuning, not engine-parity claims.

One source for installers and previews. Keep the accepted shop untouched.
The retained nonzero specular/probe contribution avoids the rejected flat altar.
"""
PROFILES={
    'shop':{'glossRangeMin':0,'glossRangeMax':8,'specAmount':.45,'specColorTint':'.5 .5 .5 1','reflectionProbeAmount':.2},
    # Surface-mounted atlas strips must not inherit the shader's 0.1 depth.
    'teleporter':{'glossRangeMin':0,'glossRangeMax':6,'specAmount':.45,'specColorTint':'.5 .5 .5 1','reflectionProbeAmount':.2,'waterRoughness':0},
    # docs/208 (map 1's v19.66): the altar's atlas lights stay ON the surface too (fullspec layerDepth).
    'altar':{'glossRangeMin':0,'glossRangeMax':5,'specAmount':.2,'specColorTint':'.25 .25 .25 1','reflectionProbeAmount':.15,'waterRoughness':0},
    'architecture':{'glossRangeMin':0,'glossRangeMax':7,'specAmount':.45,'specColorTint':'.5 .5 .5 1','reflectionProbeAmount':.2},
}
VERSION='cybercity-satin-1'

def apply(fields,role):
    fields.update(PROFILES[role]);return fields
