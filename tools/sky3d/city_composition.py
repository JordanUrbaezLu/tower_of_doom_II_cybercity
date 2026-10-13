"""Moderate city thinning: retain detail, remove whole secondary buildings.

The main builder still spends every original random draw. Stable lot selection
therefore cannot reshuffle surviving architecture, heroes or the sky. Removal
favors depth and small coherent gaps, with a separate station visibility check.
"""
import hashlib
import math
from cyber_station import in_station_footprint

KEEP_FRACTION = 2.0 / 3.0

def key(lot):
    return f"{lot['cx']:.6f},{lot['cy']:.6f},{lot['P']:.6f}"

def unit(value):
    return int.from_bytes(hashlib.blake2s(value.encode(), digest_size=8).digest(), 'big') / 2**64

def band(radius):
    return 'core' if radius < 1430 else 'near' if radius < 3500 else 'middle' if radius < 7000 else 'far' if radius < 14000 else 'outer'

def plan_lots(lots):
    bias = {'core': .22, 'near': .13, 'middle': .01, 'far': -.09, 'outer': -.17}
    ranks = []
    for lot in lots:
        identity = key(lot)
        district = f"{int((lot['az'] + 180) // 12)}:{int(lot['r'] // 1800)}"
        score = unit(identity) + bias[band(lot['r'])] + .22 * (unit(district) - .5)
        # Extra breathing room below and beside the dominant title monument.
        if abs(lot['az']) < 28 and lot['r'] > 1400:
            score -= .05
        ranks.append((score, identity))
    ranks.sort(reverse=True)
    return frozenset(identity for _, identity in ranks[:round(len(lots) * KEEP_FRACTION)])

def keep_mega(index, x, y, hero_count):
    if index < hero_count:
        return True
    distance = math.hypot(x, y)
    return unit(f'mega:{index}:{x:.4f}:{y:.4f}') >= (.42 if distance > 13000 else .30)

def station_conflict(info, plan, cam_h):
    """Conservative direct sightline + footprint clearance for the hero station.

    Tests the actual generated lot bounds, not its empty grid-cell center. The
    keepout ends at the station, preserving the distant district behind it.
    """
    if not plan:
        return False
    keepout = plan['keepout']
    x, y, height = info['cx'], info['cy'], info['h']
    radius = .5 * math.hypot(info['w'], info['d'])
    if in_station_footprint(x, y, plan, radius):
        return True
    distance = math.hypot(x, y)
    az = math.degrees(math.atan2(x, y))
    spread = math.degrees(math.asin(min(.99, radius / max(distance, 1))))
    azmin, azmax = keepout['foreground_azimuth_deg']
    if az+spread < azmin or az-spread > azmax:
        return False
    top = math.degrees(math.atan2(height-cam_h, max(1, distance-radius)))
    return distance-radius < keepout['foreground_max_radius_m'] and top > keepout['max_foreground_top_elevation_deg']


def title_conflict(info, cam_h, gate):
    """Keep foreground crowns below the new gate's low subtitle band.

    The open arch still frames distant city. Only building envelopes in front
    of the title plane and across its subtitle bearing can be retired here.
    """
    x, y, height = info['cx'], info['cy'], info['h']
    radius = .5 * math.hypot(info['w'], info['d'])
    distance = math.hypot(x, y)
    az = math.degrees(math.atan2(x, y))
    spread = math.degrees(math.asin(min(.99, radius / max(distance, 1))))
    if abs(az) - spread > 18.0:
        return False
    el = math.radians(gate['box_el'])
    front = y * math.cos(el) + (height-cam_h) * math.sin(el) - radius
    top = math.degrees(math.atan2(height-cam_h, max(1, distance-radius)))
    return front < gate['D'] and top > .1
