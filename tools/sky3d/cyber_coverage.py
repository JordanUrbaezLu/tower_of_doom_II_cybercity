"""One architectural family for every ordinary Cybercity sky building.

All ordinary lots receive the approved close-building kit, including tall and
distant lots. The separately authored landmark silhouettes are outside this
policy. Distance controls detail in the kit, never architectural identity.
There are no random draws or Blender dependencies here.
"""

import math


COVERAGE_VERSION = 'cyber_coverage_2'


def modernize_lot(spire, h, distance):
    """Every valid ordinary lot uses the cyber kit, at every height/distance.

    ``spire`` remains in the API because callers preserve the original layout
    and random-draw history. It no longer selects a different building family.
    Distance zero remains valid for a lot at the city origin.
    """
    if not all(math.isfinite(value) for value in (h, distance)):
        raise ValueError('Cyber coverage height and distance must be finite')
    if h <= 0 or distance < 0:
        raise ValueError('Cyber coverage needs positive height and nonnegative distance')
    return True
