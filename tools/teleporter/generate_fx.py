"""Pad-height green ready/release and yellow charge fields.

The stock ring material is already a dependency of the Sophia charge effect.
All emitters loop for the proven server PlayFxOnTag lane. Burst emitters have
a five-second interval, longer than their host lifetime: exactly one pulse.
Ready uses the existing beam host; charge/discharge share their stock FX host.
Run normally to author, or --check to reject source drift without writing.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DONOR = ROOT / 'share/raw/fx/acc/light/fx_perk_glow_amber.efx'
OUT = ROOT / 'share/raw/fx/tod/teleporter'
PALETTE = json.loads((ROOT / 'tools/teleporter/state_palette.json').read_text())
GREEN = tuple(PALETTE['ready_linear'])
YELLOW = tuple(PALETTE['pending_linear'])
FLAT = [(0, 1), (1, 1)]


def field(block, key, value):
    result, count = re.subn(r'(?m)^\t' + key + r'\s+[^;]*;',
                            lambda _: f'\t{key} {value};', block, count=1)
    assert count == 1, key
    return result


def graph(block, key, base, curve):
    rows = '\n'.join('\t\t\t' + ' '.join(str(v) for v in row) for row in curve)
    body = '\t\t{\n' + rows + '\n\t\t}\n'
    value = f'\t{key} {base}\n\t{{\n' + body + body + '\t};'
    result, count = re.subn(r'(?m)^\t' + key + r'\s+[^;]*;',
                            lambda _: value, block, count=1)
    assert count == 1, key
    return result


def tint(block, color):
    return graph(block, 'colorGraph', 1, [(0, *color), (1, *color)])


def common(block, name, z, life, period, color):
    values = dict(name=f'"{name}"', editorFlags='looping',
                  flags='spawnRelative spawnFrustumCull spawnOffsetNone runRelToEffect nonUniformScale',
                  spawnRange='0 2400', fadeInRange='0 0', fadeOutRange='1800 600',
                  spawnFrustumCullRadius=170, spawnLooping=f'{period} 0',
                  spawnLoopingSpawnCount='1 0', spawnOneShot='1 0',
                  spawnDelayMsec='0 0', lifeSpanMsec=f'{life} 0',
                  spawnOrgX='0 0', spawnOrgY='0 0', spawnOrgZ=f'{z} 0',
                  spawnOffsetRadius='0 0', spawnOffsetHeight='0 0',
                  spawnAnglePitch='0 0', spawnAngleYaw='0 0', spawnAngleRoll='0 0',
                  angleVelPitch='0 0', angleVelYaw='0 0', angleVelRoll='0 0',
                  initialRot='0 0', gravity='0 0', windinfluence=0,
                  atlasIndex=0, atlasEntryCount=1, atlasIndexRange=0, zFeather=0)
    for key, value in values.items():
        block = field(block, key, value)
    for axis in ('0X', '0Y', '0Z', '1X', '1Y', '1Z'):
        block = graph(block, 'velGraph' + axis, 0, FLAT)
    block = graph(block, 'rotGraph', 0, FLAT)
    block = graph(block, 'scaleGraph', 1, FLAT)
    block = graph(block, 'alphaGraph', 1, FLAT)
    return tint(block, color)


def ring(sprite, name, z, color, size, curve, alpha, life, period):
    block = common(sprite, name, z, life, period, color)
    # Oriented sprite's forward normal is turned up, so the ring lies on XY.
    block = field(block, 'spawnAnglePitch', '-90 0')
    block = graph(block, 'sizeGraph0', size, curve)
    block = graph(block, 'sizeGraph1', size, curve)
    block = graph(block, 'alphaGraph', 1, alpha)
    block = block.replace('\tbillboardSprite\n', '\torientedSprite\n')
    return block.replace('"gfx_light_phosphorous_em"', '"gfx_water_ring_em"')


def motes(sprite, name, z, color, period, speed):
    block = common(sprite, name, z, 700, period, color)
    block = field(block, 'spawnOrgX', '-32 64')
    block = field(block, 'spawnOrgY', '-32 64')
    block = graph(block, 'velGraph0Z', speed, FLAT)
    block = graph(block, 'sizeGraph0', 1.4, [(0, .3), (.2, 1), (1, 0)])
    block = graph(block, 'sizeGraph1', 1.4, [(0, .3), (.2, 1), (1, 0)])
    return graph(block, 'alphaGraph', 1, [(0, 0), (.2, .7), (.7, .5), (1, 0)])


def light(template, name, z, color, intensity, radius, life, period, curve):
    block = common(template, name, z, life, period, color)
    block = graph(block, 'lightRadiusGraph', radius, FLAT)
    return graph(block, 'lightIntensityGraph', intensity, curve)


def author():
    head, *raw = re.split(r'\n\{\n\tname "', DONOR.read_text())
    blocks = {b.split('"')[0]: '\n{\n\tname "' + b for b in raw}
    sprite, lamp = blocks['glow'], blocks['light_small']
    # Explicit bounds include the low field and its brief rising particles.
    head = field(head, 'efBoundingBoxMin', '-170 -170 -32')
    head = field(head, 'efBoundingBoxMax', '170 170 96')
    breathe = [(0, .2), (.5, .5), (1, .2)]
    fade = [(0, 0), (.12, .7), (.55, .5), (1, 0)]
    charge = [(0, 0), (.2, .3), (.8, 1), (1, 0)]
    variants = {
        # Host = floor + 2. Keep both rings above the 9.46-unit deck.
        'fx_tod_tp_ready': [
            ring(sprite, 'ready_outer_green', 10, GREEN, 64, FLAT, breathe, 1600, 1600),
            ring(sprite, 'ready_inner_green', 10.5, GREEN, 40, FLAT, breathe, 1600, 1600),
            motes(sprite, 'ready_ions', 12, GREEN, 140, 14),
            light(lamp, 'ready_floor_light', 26, GREEN, 150, 100, 1600, 1600,
                  [(0, .65), (.5, 1), (1, .65)]),
        ],
        # Existing charge host = floor + 40. The overlay stays at pad height.
        'fx_tod_tp_charge_field': [
            ring(sprite, 'charge_outer_yellow', -28, YELLOW, 70,
                 [(0, 1), (.75, .28), (1, .1)], charge, 700, 5000),
            ring(sprite, 'charge_inner_yellow', -27.5, YELLOW, 52,
                 [(0, 1), (.75, .2), (1, .08)], charge, 700, 5000),
            motes(sprite, 'charge_ions', -26, YELLOW, 65, 45),
            light(lamp, 'charge_floor_light', -12, YELLOW, 900, 130, 700, 5000, charge),
        ],
        # Existing discharge host = floor + 4. One expanding release, no strobe.
        'fx_tod_tp_release_field': [
            ring(sprite, 'release_outer_green', 8, GREEN, 76,
                 [(0, .16), (.65, .85), (1, 1)], fade, 650, 5000),
            ring(sprite, 'release_inner_green', 8.5, GREEN, 62,
                 [(0, .1), (.7, .8), (1, 1)], fade, 800, 5000),
            light(lamp, 'release_floor_light', 24, GREEN, 1150, 155, 650, 5000,
                  [(0, 1), (.2, .7), (1, 0)]),
        ],
    }
    return {name + '.efx': head.rstrip() + '\n' + '\n'.join(b.rstrip() for b in parts) + '\n'
            for name, parts in variants.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for name, text in author().items():
        dest = OUT / name
        if args.check:
            assert dest.read_text() == text, f'{dest}: rerun generate_fx.py'
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding='utf-8', newline='\n')
    print('TELEPORTER_FX_OK: 3 effects; shared hosts; bounded low fields, charge and release; native appearance pending.')
