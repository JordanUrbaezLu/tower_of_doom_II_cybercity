"""Verify a fresh, complete native crown-alarm lens material in the linked FF.

Reads current source/deployment parity, the completed dependency ledger and the
actual T7 fastfile. A material dependency row alone is insufficient: the lens
must have a full named material record with a nonempty image table and techset,
rather than the empty comma-prefixed record found in the previous shipping FF.

This is intentionally a bounded structural check, not a complete T7 loader.
Compiled constant buffers can be deduplicated into another FF stream. Their
relocations are not decoded here, so source tint and shader-contract F0 are
reported separately and never presented as reflected compiled constants.
Only the requested repository evidence files are written. No native programs
are launched, and no source, cache, deployment or game state is changed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
MAP = 'zm_tod2_cybercity'
NAME = 'mc/mtl_tod_alarm_lens'
GDT = 'source_data/tod_crown_alarm.gdt'
PACKAGE = 'zone_source/tod_crown_alarm.zpkg'
LENS = 'model_export/tod_crown_alarm/_images/i_tod_alarm_lens_c.png'
MANIFEST = 'art/crown_alarm/manifest.json'
TECHSET = 'mc/lit_emissive_transparent_advanced#e6142445'
FF_SOURCE = 'https://raw.githubusercontent.com/ate47/atian-cod-tools/main/src/core/acts/tools/bo3/bo3_ff.cpp'
MATERIAL_SOURCE = 'https://raw.githubusercontent.com/Scobalula/Greyhound/master/src/WraithXCOD/WraithXCOD/DBGameAssets.h'
SEMANTICS = {
    0xA0AB1041: 'colorMap', 0x59D30D0F: 'normalMap',
    0x6D0A6C98: 'glossMap', 0xEC443804: 'specColorMap',
}


def asset_pointer(value):
    # T7 serialized inline pointer or a nonempty asset-stream relocation.
    return value == 0xffffffffffffffff or value >> 60 == 5 and value & ((1 << 60) - 1) > 0


def image_table(data, name_end, limit, count):
    """Check actual contiguous native 32-byte image records, not just a pointer.

    The T7 MaterialImage prefix (pointer + semantic hash) is documented by
    Greyhound. UV scale/offset fields are checked against this task's known
    untransformed native maps and independent alarm controls. Material buffer
    serialization can vary, so locate the table using its exact color semantic
    and validate every entry rather than inventing a fixed body offset.
    """
    tables = []
    for match in re.finditer(re.escape(struct.pack('<I', 0xA0AB1041)), data[name_end:limit]):
        color_hash = name_end + match.start()
        for color_index in range(count):
            start = color_hash - 8 - 32 * color_index
            if start < name_end or start + 32 * count > limit:
                continue
            entries = []
            for index in range(count):
                pointer, semantic, scale_u, scale_v, offset_u, offset_v, flags = struct.unpack_from('<QI5I', data, start + 32 * index)
                if (not asset_pointer(pointer) or semantic == 0 or
                        scale_u != 0x3f800000 or scale_v != 0x3f800000 or
                        offset_u != 0 or offset_v != 0):
                    break
                entries.append({'index': index, 'image_pointer': hex(pointer),
                                'semantic_hash': hex(semantic),
                                'semantic': SEMANTICS.get(semantic, 'other native material image'),
                                'native_flags': flags})
            else:
                if set(SEMANTICS).issubset({int(row['semantic_hash'], 16) for row in entries}):
                    tables.append((start, entries))
    unique = {start: entries for start, entries in tables}
    return next(iter(unique.items())) if len(unique) == 1 else None


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def deployed_path(relative):
    # Guarded sync sends zone_source into this map's usermap directory; GDTs
    # and model exports live at the private tools root.
    return TOOLS / 'usermaps' / MAP / relative if relative.startswith('zone_source/') else TOOLS / relative


def ff_chunks(path):
    """Read documented T7 0x251/0x265 zlib blocks without retaining the FF."""
    with path.open('rb') as stream:
        prefix = stream.read(16)
        require(prefix[:8] == b'TAff0000', 'Expected a T7 TAff0000 fastfile')
        version = struct.unpack_from('<I', prefix, 8)[0]
        require(version in (0x251, 0x265), 'Unsupported T7 fastfile version')
        require(prefix[13] == 1, 'This check supports documented zlib T7 FFs only')
        position = 0x248 if version == 0x251 else 0x638
        file_size = path.stat().st_size
        blocks = 0
        while True:
            require(position + 16 <= file_size, 'Truncated FF block header')
            stream.seek(position)
            compressed, decompressed, size, declared_position = struct.unpack('<4i', stream.read(16))
            if size == 0:
                break
            require(declared_position == position, 'FF block position mismatch')
            require(size > 0 and compressed >= 0 and decompressed >= 0,
                    'Invalid FF block dimensions')
            if decompressed == 0:
                position = (position + 16 + 0x7fffff) & ~0x7fffff
                continue
            require(compressed <= size and position + 16 + size <= file_size,
                    'FF compressed block overruns the file')
            require(decompressed <= 16 * 1024 * 1024,
                    'Unexpected FF decompression block size')
            data = zlib.decompress(stream.read(compressed))
            require(len(data) == decompressed, 'FF decompressed block size mismatch')
            yield data
            blocks += 1
            position += 16 + size
        require(blocks > 0, 'Fastfile contains no decompressed data')


def material_records(path, names=(NAME,)):
    """Locate exact material names and retain enough bytes to inspect headers.

    Greyhound documents the T7 image count at native Material +624 and image
    table pointer at +640. The 672-byte serialized header/name boundary is
    additionally checked against independent full alarm materials in this FF;
    unknown layouts fail rather than silently accepting a text occurrence.
    """
    needles = {name: name.encode('ascii') + b'\0' for name in names}
    records, seen, carry, output_offset = [], set(), b'', 0

    def scan(data, base, final=False):
        for name, needle in needles.items():
            cursor = 0
            while True:
                index = data.find(needle, cursor)
                if index < 0:
                    break
                cursor = index + 1
                absolute = base + index
                if absolute in seen or index < 673:
                    continue
                if not final and index + 4096 > len(data):
                    continue
                seen.add(absolute)
                reference = data[index - 1] == ord(',')
                header_start = index - int(reference) - 672
                header = data[header_start:header_start + 672]
                inline_name = header[:8] == b'\xff' * 8
                image_count = header[624] if inline_name else None
                image_pointer = struct.unpack_from('<Q', header, 640)[0] if inline_name else None
                techset_pointer = struct.unpack_from('<Q', header, 632)[0] if inline_name else None
                limit = min(index + 4096, len(data))
                # Do not borrow an image table from a subsequent material.
                for match in re.finditer(rb'(?:,)?(?:mc|wc|ei|ui)/[A-Za-z0-9_./#-]+\0', data[index + len(needle):limit]):
                    next_name = index + len(needle) + match.start()
                    next_header = next_name - 672
                    if next_header >= index + len(needle) and data[next_header:next_header + 8] == b'\xff' * 8:
                        limit = next_header
                        break
                table = None
                if inline_name and not reference and 0 < image_count <= 64 and asset_pointer(image_pointer) and asset_pointer(techset_pointer):
                    table = image_table(data, index + len(needle), limit, image_count)
                record = {
                    'name': name, 'name_decompressed_offset': absolute,
                    'header_decompressed_offset': base + header_start,
                    'comma_prefixed': reference, 'inline_name_pointer': inline_name,
                    'image_count': image_count,
                    'image_table_pointer': hex(image_pointer) if inline_name else None,
                    'techset_pointer': hex(techset_pointer) if inline_name else None,
                    'header_sha256': hashlib.sha256(header).hexdigest(),
                    'header_hex': header.hex(),
                    'image_table_decompressed_offset': base + table[0] if table else None,
                    'image_table_entries': table[1] if table else None,
                    'classification': 'unrecognized text occurrence',
                }
                if inline_name and reference and not any(header[8:]):
                    record['classification'] = 'empty comma-prefixed reference'
                elif table:
                    record['classification'] = 'complete material definition'
                records.append(record)

    for chunk in ff_chunks(path):
        data = carry + chunk
        scan(data, output_offset - len(carry))
        carry = data[-65536:]
        output_offset += len(chunk)
    scan(carry, output_offset - len(carry), final=True)
    return records, output_offset


def dependency_block(path):
    active, headers, rows = False, 0, []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line and not line[0].isspace():
            active = line.split(',')[:2] == ['material', NAME]
            if active:
                headers += 1
        elif active:
            rows.append(line.strip())
    require(headers == 1, 'Expected one completed native lens material dependency block')
    assets = [row.split(',')[1:3] for row in rows if row.startswith('asset,')]
    require(['techset', TECHSET] in assets, 'Lens selects an unexpected native techset')
    for image in ('i_tod_alarm_lens_c', 'i_tod_alarm_lens_n', 'i_tod_alarm_lens_g', '$black_specular', '$gray_32_one_channel'):
        require(['image', image] in assets, 'Missing native lens binding: ' + image)
    require(['image', 'i_tod_alarm_lens_s'] not in assets,
            'Invalid RGB specular image is still a native lens texture binding')
    require(any(row.startswith('gdt,material,mtl_tod_alarm_lens,') for row in rows),
            'Native lens material has no source GDT dependency')
    return {'assets': assets, 'rows': rows}


def srgb_to_linear(value):
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'art/crown_alarm/lens_review/compiled_material.json')
    args = parser.parse_args()
    source_root, output = args.source_root.resolve(), args.output.resolve()
    require(output.is_relative_to(ROOT.resolve()), 'Evidence must remain in this repository')
    ff = TOOLS / 'usermaps' / MAP / 'zone' / (MAP + '.ff')
    deps = TOOLS / 'usermaps' / MAP / 'zone_source/all/assetinfo' / (MAP + '.deps')
    require(ff.is_file() and deps.is_file(), 'Completed FF and dependency ledger are required')
    ff_hash, deps_hash = sha(ff), sha(deps)
    manifest_path = source_root / MANIFEST
    manifest_hash = sha(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    require(manifest.get('lens_repair', {}).get('revision') == '2026-10-01 clear glass',
            'Current manifest is missing the reviewed lens repair')
    inputs = []
    paths = [GDT, PACKAGE, *(row['file'] for row in manifest['models']),
             *('model_export/tod_crown_alarm/_images/' + name for name in manifest['textures'])]
    for relative in paths:
        source, deployed = (source_root / relative).resolve(), deployed_path(relative).resolve()
        require(source.is_relative_to(source_root) and deployed.is_relative_to(TOOLS.resolve()),
                'Alarm manifest path leaves the permitted source/deployment roots')
        require(source.is_file() and deployed.is_file(), 'Missing alarm source/deployment: ' + relative)
        digest = sha(source)
        require(digest == sha(deployed), 'Native deployment differs from current source: ' + relative)
        inputs.append({'path': relative, 'sha256': digest,
                       'source_mtime': source.stat().st_mtime,
                       'deployed_mtime': deployed.stat().st_mtime})
    input_hashes = {row['path']: row['sha256'] for row in inputs}
    require(input_hashes[GDT] == manifest['gdt_sha256'], 'Reviewed GDT manifest hash is stale')
    for row in manifest['models']:
        require(input_hashes[row['file']] == row['sha256'], 'Reviewed model hash is stale: ' + row['file'])
    for name, digest in manifest['textures'].items():
        require(input_hashes['model_export/tod_crown_alarm/_images/' + name] == digest,
                'Reviewed texture hash is stale: ' + name)
    package = (source_root / PACKAGE).read_text(encoding='utf-8-sig')
    require(package.splitlines().count('material,' + NAME) == 1,
            'Alarm package must explicitly include exactly one model-mode lens material')
    gdt = (source_root / GDT).read_text(encoding='utf-8-sig')
    blocks = re.findall(r'"mtl_tod_alarm_lens"\s*\(\s*"material.gdf"\s*\)\s*\{(.*?)\n\s*\}', gdt, re.S)
    require(len(blocks) == 1, 'Expected exactly one lens source material')
    fields = dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"', blocks[0]))
    tint = [float(value) for value in fields.get('specColorTint', '').split()]
    require(len(tint) == 4 and all(abs(value - .220916) < 1e-6 for value in tint[:3]) and tint[3] == 1,
            'Source lens tint is stale; old white specular tint is disallowed')
    require(fields.get('materialType') == 'lit_emissive_transparent_advanced',
            'Source lens no longer selects its reviewed transparent shader')
    require(fields.get('specColorMap') == '$black_specular',
            'Source lens requires the valid stock scalar nonmetal specularMask')
    require(float(fields.get('scaleRGB', '-1')) == 0, 'Lens self-emission changed')
    newest_source = max(manifest_path.stat().st_mtime, *(row['source_mtime'] for row in inputs))
    newest_deployed = max(row['deployed_mtime'] for row in inputs)
    require(ff.stat().st_mtime >= max(newest_source, newest_deployed),
            'Linked FF predates current reviewed alarm inputs')
    require(deps.stat().st_mtime >= max(newest_source, newest_deployed),
            'Dependency ledger predates current reviewed alarm inputs')
    block = dependency_block(deps)
    controls = ('mc/mtl_tod_alarm_cast', 'mc/mtl_tod_alarm_steel', 'mc/mtl_tod_alarm_lamp_on')
    records, size = material_records(ff, (NAME, *controls))
    for name in controls:
        require(any(row['name'] == name and row['classification'] == 'complete material definition'
                    for row in records), 'Unknown material serialization layout or missing control: ' + name)
    lens = [row for row in records if row['name'] == NAME]
    full = [row for row in lens if row['classification'] == 'complete material definition']
    require(len(full) == 1,
            'Linked FF lens lacks exactly one complete native material definition; '
            'reference-only/default output is not a repaired material')
    require(sha(ff) == ff_hash and sha(deps) == deps_hash,
            'Native outputs changed during material verification')
    require(sha(manifest_path) == manifest_hash, 'Reviewed alarm manifest changed during verification')
    for row in inputs:
        require(sha(source_root / row['path']) == row['sha256'] and sha(deployed_path(row['path'])) == row['sha256'],
                'Alarm source/deployment changed during material verification: ' + row['path'])
    linear = [srgb_to_linear(value) for value in tint[:3]]
    mask = 0.0  # $black_specular is the stock linear nonmetal mask.
    receipt = {
        'verified_at': dt.datetime.now().astimezone().isoformat(),
        'source_root': str(source_root), 'source_manifest_sha256': manifest_hash,
        'alarm_source_deployment_parity': inputs,
        'fastfile': str(ff), 'fastfile_sha256': ff_hash, 'fastfile_size': ff.stat().st_size,
        'decompressed_size': size, 'dependencies': str(deps), 'dependencies_sha256': deps_hash,
        'lens_dependency_block': block, 'lens_material_records': lens,
        'control_material_records': [row for row in records if row['name'] in controls],
        'complete_native_material_definition_verified': True,
        'ff_image_table_structure_and_semantics_verified': True,
        'ff_relocation_targets_resolved': False,
        'binding_identity_evidence': 'Image-table shape and semantic hashes are verified in actual FF bytes. '
                                     'Exact image names and transparent-techset identity are verified through '
                                     'the fresh completed .deps material block; relocation targets are not resolved '
                                     'by this bounded structural reader.',
        'source_specColorTint': tint, 'source_shader_contract_linear_tint': linear,
        'source_specColorMap': '$black_specular', 'source_shader_contract_scalar_mask': mask,
        'source_shader_contract_diffuse_factor': 1.0,
        'source_shader_contract_effective_F0': [.04 + mask * (value - .04) for value in linear],
        'compiled_constants_verified': False,
        'compiled_constants_limit': 'T7 constant buffers use serialized/deduplicated relocation pointers. '
                                    'This bounded reader does not resolve those pointers. Tint/F0 values above '
                                    'are current source plus proven shader-contract calculations, not reflected FF constants.',
        'format_sources': [FF_SOURCE, MATERIAL_SOURCE],
        'header_layout_evidence': 'Native imageCount +624 and imageTablePtr +640 from Greyhound; '
                                  '672-byte serialized header boundary checked independently against three '
                                  'complete alarm materials in this same linked FF.',
        'native_visual_verified': False, 'native_playtested': False, 'game_launched': False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('LENS_MATERIAL_VERIFIED: fresh complete FF material, transparent-techset bindings and current source/deployment parity')
    print('COMPILED_TINT_LIMIT: exact reflected constant values remain unparsed; source shader contract F0=' + str(receipt['source_shader_contract_effective_F0']))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, zlib.error) as error:
        print('LENS_MATERIAL_VERIFICATION_FAILED: ' + str(error), file=sys.stderr)
        sys.exit(1)
