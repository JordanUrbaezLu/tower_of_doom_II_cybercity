"""Cheap, in-memory safety gate for the authored sky FX material pass.

Call check(base_effect_texts, refined_effect_texts) before writing generated FX.
No generator/native_detail imports, file writes, asset conversion or game launch.
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'sky_ships'))
import efx_lib as E

CUSTOM = {'mtl_tod_sky_detail_' + key for key in ('fibre', 'dust', 'void', 'wake')}
ATLAS = {
    'atlasBehavior': 'startFixed', 'atlasIndex': '0', 'atlasFps': '0',
    'atlasLoopCount': '1', 'atlasColIndexBits': '0', 'atlasRowIndexBits': '0',
    'atlasEntryCount': '1', 'atlasIndexRange': '0',
}
CHILD_REFS = ('attachment', 'emission', 'fxOnImpact', 'fxOnDeath')
LIFECYCLE = ('flags', 'editorFlags', 'spawnDelayMsec', 'spawnOneShot',
             'spawnLoopingSpawnCount')


def require(ok, message):
    if not ok:
        raise ValueError('SKY DETAIL FX: ' + message)


def field(element, key):
    if not element.has(key):
        return None
    value = element.get(key)
    return value.text() if hasattr(value, 'text') else value


def finite_tokens(text, label):
    """Reject NaN/Inf in numeric scalar fields while allowing symbolic flags."""
    for token in text.split():
        try:
            value = float(token.rstrip(';'))
        except ValueError:
            continue
        require(math.isfinite(value), label + ' contains non-finite geometry/value')


def finite_element(element, label):
    for item in element.items:
        if isinstance(item, tuple):
            finite_tokens(item[2], label + '/' + item[1])
        elif isinstance(item, E.Graph):
            require(math.isfinite(item.scale), label + '/' + item.key + ' non-finite scale')
            require(len(item.curves) == 2 and all(item.curves), label + '/' + item.key + ' empty curves')
            for curve in item.curves:
                for row in curve:
                    require(len(row) >= 2 and all(math.isfinite(v) for v in row),
                            label + '/' + item.key + ' non-finite or empty row')
                    if item.key == 'alphaGraph':
                        require(len(row) == 2 and 0 <= row[1] * item.scale <= 1,
                                label + ' alpha outside 0..1')
                    elif item.key in ('sizeGraph0', 'sizeGraph1'):
                        require(row[1] * item.scale >= 0, label + ' negative size')
        elif item.key == 'trailDef':
            finite_tokens(item.text(), label + '/trailDef')


def particle_cap(element, label):
    """Conservative simultaneous particles: maximum life/count, minimum interval.

    Native pairs are base + nonnegative random range. This counts spawned
    particles, not ribbon vertices or pixel overdraw; it is not a GPU benchmark.
    """
    if 'looping' not in element.flags('editorFlags'):
        values = element.nums('spawnOneShot')
        require(all(math.isfinite(v) and v >= 0 for v in values), label + ' invalid one-shot count')
        return sum(values)
    life = element.nums('lifeSpanMsec')
    interval = element.nums('spawnLooping')
    count = element.nums('spawnLoopingSpawnCount')
    require(all(len(v) == 2 for v in (life, interval, count)), label + ' invalid particle range')
    require(all(math.isfinite(v) and v >= 0 for pair in (life, interval, count) for v in pair),
            label + ' invalid particle range')
    require(interval[0] > 0, label + ' zero loop interval')
    return math.ceil(sum(life) / interval[0]) * sum(count)


def check(base, refined):
    """Raise ValueError on an integration regression; return compact gate counts."""
    require(set(base) == set(refined), 'effect names/count changed')
    stats = {'effects': len(base), 'changed': 0, 'emitters': 0, 'custom_emitters': 0}
    for name in sorted(base):
        before, after = E.parse(base[name]), E.parse(refined[name])
        require(before.version == after.version and before.header == after.header,
                name + ' effect version/header/bounds changed')
        for line in after.header:
            finite_tokens(line, name + '/header')
        require(len(before.elements) == len(after.elements), name + ' emitter count changed')
        require([e.name for e in before.elements] == [e.name for e in after.elements],
                name + ' emitter names/order changed')
        stats['changed'] += base[name] != refined[name]
        stats['emitters'] += len(after.elements)
        for old, new in zip(before.elements, after.elements):
            label = name + '/' + new.name
            old_kind, old_materials = old.visual
            kind, materials = new.visual
            require(old_kind == kind, label + ' visual type changed')
            for key in CHILD_REFS + LIFECYCLE:
                require(field(old, key) == field(new, key), label + '/' + key + ' changed')
            if old_materials != materials:
                require(len(materials) == 1 and materials[0] in CUSTOM,
                        label + ' unexpected material/runner reference change')
            if kind == 'runner':
                require(old_materials == materials, label + ' runner child changed')
            if kind == 'trail':
                # Covers cross-section UVs, split/repeat distances, scroll,
                # fade distances and future trail fields already in the donor.
                keys = {it[1] if isinstance(it, tuple) else it.key for it in old.items + new.items}
                for key in keys:
                    if key.startswith('trail') and key != 'trail':
                        require(field(old, key) == field(new, key), label + '/' + key + ' changed')
            if any(material in CUSTOM for material in materials):
                stats['custom_emitters'] += 1
                for key, value in ATLAS.items():
                    require(field(new, key) == value, label + '/' + key + ' single-image atlas not reset')
            finite_element(new, label)
            if name.startswith('fx_sky_worm_open_'):
                require(particle_cap(new, label) <= particle_cap(old, label),
                        label + ' particle cap increased')
    return stats


def negative_controls(base, refined):
    """Prove the gate rejects an inherited flipbook and an orphan emitter.

    Both mutations are made to fresh in-memory parses; inputs stay untouched.
    Intended for a one-off verification, not every generator invocation.
    """
    check(base, refined)
    target = next((name for name, text in refined.items()
                   if any(any(m in CUSTOM for m in e.visual[1]) for e in E.parse(text).elements)), None)
    require(target is not None, 'negative controls need a custom sprite')
    for defect, expected in (('atlas', 'single-image atlas not reset'), ('orphan', 'emitter count changed')):
        changed = dict(refined)
        fx = E.parse(refined[target])
        if defect == 'atlas':
            sprite = next(e for e in fx.elements if any(m in CUSTOM for m in e.visual[1]))
            sprite.set('atlasColIndexBits', 3)  # Removing reset leaves an 8-column donor atlas.
            sprite.set('atlasEntryCount', 64)
        else:
            orphan = fx.elements[0].copy()
            orphan.name = 'unexpected_orphan'
            fx.elements.append(orphan)
        changed[target] = fx.text()
        try:
            check(base, changed)
        except ValueError as exc:
            require(expected in str(exc), defect + ' failed for an unrelated reason: ' + str(exc))
        else:
            raise ValueError('SKY DETAIL FX: negative control accepted ' + defect)
    return ('inherited_atlas_rejected', 'orphan_emitter_rejected')
