"""Verify the completed private build's actual lens alpha and mip conversion.

Reads the dependency-selected IWi, never a newest-file guess. The BO3 IWi is an
LZ4 block containing a 96-byte header followed by BC7 mips from small to large.
The decoder wraps each mip in a DDS DX10 header in memory for Pillow. No cache,
deployment, material, geometry or game state is changed; only the requested
repository receipt is written, after all checks pass.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('C:/BO3Tools/TOD2Cybercity')
MAP = 'zm_tod2_cybercity'
LENS = 'model_export/tod_crown_alarm/_images/i_tod_alarm_lens_c.png'
ASSET = 'i_tod_alarm_lens_c'
MATERIAL = 'mtl_tod_alarm_lens'
OPAQUE_LIMIT = 220


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def histogram(values):
    levels, counts = np.unique(values, return_counts=True)
    return {str(int(level)): int(count) for level, count in zip(levels, counts)}


def decode_lz4(data):
    """Decode the private tool's FB:LZ4:0 frame, with bounds/size checks."""
    require(data[:8] == b'FB:LZ4:0' and len(data) >= 17,
            'Expected BO3 FB:LZ4:0 compressed image')
    expected = struct.unpack_from('<Q', data, 8)[0]
    require(96 <= expected <= 128 * 1024 * 1024, 'Invalid decompressed image size')
    source, result, index = memoryview(data)[16:], bytearray(), 0

    def length(base):
        nonlocal index
        value = base
        if base == 15:
            while True:
                require(index < len(source), 'Truncated LZ4 length')
                extra = source[index]
                index += 1
                value += extra
                if extra != 255:
                    break
        return value

    while index < len(source):
        token = source[index]
        index += 1
        literal = length(token >> 4)
        require(index + literal <= len(source) and len(result) + literal <= expected,
                'Invalid LZ4 literal run')
        result.extend(source[index:index + literal])
        index += literal
        if index == len(source):
            break
        require(index + 2 <= len(source), 'Truncated LZ4 match offset')
        offset = struct.unpack_from('<H', source, index)[0]
        index += 2
        require(0 < offset <= len(result), 'Invalid LZ4 match offset')
        match = length(token & 15) + 4
        require(len(result) + match <= expected, 'LZ4 match exceeds declared image size')
        # Overlapping runs intentionally repeat newly appended bytes.
        for _ in range(match):
            result.append(result[-offset])
    require(len(result) == expected, 'LZ4 decoded size differs from declared image size')
    return bytes(result)


def decode_bc7(payload, width, height):
    require(len(payload) == math.ceil(width / 4) * math.ceil(height / 4) * 16,
            'BC7 mip payload size mismatch')
    # DDS_HEADER followed by DDS_HEADER_DXT10; DXGI_FORMAT_BC7_UNORM_SRGB=99,
    # D3D10_RESOURCE_DIMENSION_TEXTURE2D=3. Bytes are decoded, not color graded.
    header = ([124, 0x000A1007, height, width, len(payload), 0, 1] + [0] * 11 +
              [32, 4, struct.unpack('<I', b'DX10')[0], 0, 0, 0, 0, 0] +
              [0x1000, 0, 0, 0, 0])
    dds = (b'DDS ' + struct.pack('<31I', *header) +
           struct.pack('<5I', 99, 3, 0, 1, 0) + payload)
    with Image.open(io.BytesIO(dds)) as image:
        require(image.size == (width, height), 'Decoded BC7 dimensions changed')
        return np.asarray(image.convert('RGBA')).copy()


def decode_iwi(path):
    raw = decode_lz4(path.read_bytes())
    require(raw[:4] == b'IWi\x1d', 'Expected BO3 IWi version 29')
    require(raw[4] == 31, 'Expected alpha-capable BC7 sRGB lens conversion')
    mip_count = raw[5]
    width, height, depth = struct.unpack_from('<3H', raw, 10)
    require(depth == 1 and width == height and width in (512, 1024, 2048),
            'Unexpected native lens dimensions/depth')
    require(mip_count == int(math.log2(width)) + 1, 'Lens must retain a complete mip chain')
    end = len(raw)
    result = []
    for level in range(mip_count):
        w, h = max(1, width >> level), max(1, height >> level)
        size = math.ceil(w / 4) * math.ceil(h / 4) * 16
        start = end - size
        require(start >= 96, 'Mip chain overruns native image header')
        if level < 8:
            require(struct.unpack_from('<I', raw, 64 + 4 * level)[0] == end,
                    'Native mip offset table disagrees with decoded payload')
        result.append((decode_bc7(raw[start:end], w, h), start, end))
        end = start
    require(end == 96, 'Unexpected data outside native header and complete mip chain')
    return result


def selected_cache(dependencies):
    text = dependencies.read_text(encoding='utf-8-sig')
    matches, active = [], False
    for line in text.splitlines():
        if line and not line[0].isspace():
            active = line.split(',')[:2] == ['image', ASSET]
        if active and line.lstrip().startswith('file,'):
            # Native file rows carry path,time,checksum. Paths on this private
            # workspace contain no commas; require the selected path precisely.
            name = line.strip().split(',')[1]
            if name.lower().endswith('.iwi'):
                matches.append(Path(name))
    require(len(matches) == 1, 'Expected exactly one lens cache selected by completed dependencies')
    path = matches[0].resolve()
    require(path.is_relative_to((TOOLS / 'share/assetconvert/image/v29').resolve()),
            'Selected image cache leaves the private map tools root')
    require(path.is_file() and path.name.startswith(ASSET + '_'),
            'Dependency-selected lens conversion is missing')
    return path


def lens_uvs(source_root, manifest):
    sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
    from PyCoD import xmodel

    result = []
    for row in manifest['models']:
        if not row['asset'].startswith('tod_crown_alarm_housing'):
            continue
        file = (source_root / row['file']).resolve()
        require(file.is_relative_to(source_root), 'Manifest model path leaves source root')
        require(sha(file) == row['sha256'], 'Housing differs from reviewed manifest: ' + row['file'])
        model = xmodel.Model()
        model.LoadFile_Bin(str(file), split_meshes=True)
        triangles = []
        for mesh in model.meshes:
            for face in mesh.faces:
                if model.materials[face.material_id].name == MATERIAL:
                    triangles.append([corner.uv for corner in face.indices])
        uv = np.asarray(triangles, dtype=np.float64)
        require(uv.ndim == 3 and uv.shape[1:] == (3, 2) and len(uv),
                'Housing LOD has no native lens triangles')
        require(np.isfinite(uv).all() and (uv >= -1e-5).all() and (uv <= 1.00001).all(),
                'Native lens UVs leave valid image range')
        result.append((row, uv))
    require({(row['asset'], row['lod']) for row, _ in result} ==
            {(asset, lod) for asset in ('tod_crown_alarm_housing', 'tod_crown_alarm_housing_high')
             for lod in range(3)}, 'Expected both housing variants and every lens LOD')
    return result


def uv_alpha(image, triangles):
    """Sample triangle interiors/corners and their bilinear texel footprints.

    Native xmodel V points DOWN, as PNG rows do. Blender import flips it.
    A dense set of interior points plus every corner catches an opaque unused
    tile and mip bleed without mistaking the Blender UV convention for native.
    """
    barycentric = [(1 / 3, 1 / 3, 1 / 3), (1, 0, 0), (0, 1, 0), (0, 0, 1),
                   (.8, .1, .1), (.1, .8, .1), (.1, .1, .8),
                   (.5, .5, 0), (.5, 0, .5), (0, .5, .5)]
    uv = np.einsum('bi,tij->tbj', np.asarray(barycentric), triangles).reshape(-1, 2)
    h, w = image.shape[:2]
    points = uv * (w, h) - .5
    low = np.floor(points).astype(int)
    values = []
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x = np.clip(low[:, 0] + dx, 0, w - 1)
        y = np.clip(low[:, 1] + dy, 0, h - 1)
        values.append(image[y, x, 3])
    return np.concatenate(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'art/crown_alarm/lens_review/compiled_image.json')
    args = parser.parse_args()
    source_root, output = args.source_root.resolve(), args.output.resolve()
    require(output.is_relative_to(ROOT.resolve()), 'Receipt must stay inside this repository')
    source = source_root / LENS
    deployed = TOOLS / LENS
    dependencies = TOOLS / 'usermaps' / MAP / 'zone_source/all/assetinfo' / (MAP + '.deps')
    require(dependencies.is_file(), 'Completed dependency ledger is missing; partial build output is not proof')
    deps_hash = sha(dependencies)
    cache = selected_cache(dependencies)
    cache_hash = sha(cache)
    require(source.is_file() and deployed.is_file() and sha(source) == sha(deployed),
            'Current source lens does not match the deployed lens image')
    require(cache.stat().st_mtime >= source.stat().st_mtime,
            'Dependency-selected lens conversion predates the current source image')
    with Image.open(source) as image:
        require(image.mode == 'RGBA', 'Source lens lost its explicit alpha channel')
        original = np.asarray(image).copy()
    mip_chain = decode_iwi(cache)
    converted = mip_chain[0][0]
    require(converted.shape == original.shape, 'Compiled lens dimensions differ from source')
    alpha_error = np.abs(converted[:, :, 3].astype(np.int16) - original[:, :, 3].astype(np.int16))
    require(int(alpha_error.max()) <= 1, 'Compiled lens alpha differs from source by more than one byte')
    manifest = json.loads((source_root / 'art/crown_alarm/manifest.json').read_text(encoding='utf-8'))
    require(manifest['textures']['i_tod_alarm_lens_c.png'] == sha(source),
            'Lens source differs from reviewed manifest')
    uv_sets = lens_uvs(source_root, manifest)
    lods = []
    for row, uv in uv_sets:
        source_alpha = uv_alpha(original, uv)
        require(int(source_alpha.max()) < OPAQUE_LIMIT,
                'Source lens samples near-opaque texels: ' + row['asset'] + ' LOD' + str(row['lod']))
        levels = []
        for level, (rgba, _, _) in enumerate(mip_chain):
            values = uv_alpha(rgba, uv)
            require(int(values.max()) < OPAQUE_LIMIT,
                    'Compiled lens mip samples near-opaque texels: ' + row['asset'] +
                    ' LOD' + str(row['lod']) + ' mip' + str(level))
            levels.append({'level': level, 'min': int(values.min()), 'max': int(values.max()),
                           'samples': len(values)})
        lods.append({'asset': row['asset'], 'lod': row['lod'], 'lens_triangles': len(uv),
                     'source_alpha_min': int(source_alpha.min()),
                     'source_alpha_max': int(source_alpha.max()), 'compiled_mips': levels})
    require(sha(dependencies) == deps_hash and sha(cache) == cache_hash,
            'Native build outputs changed during conversion verification')
    receipt = {
        'verified_at': dt.datetime.now().astimezone().isoformat(),
        'source_root': str(source_root), 'source_image': LENS,
        'source_sha256': sha(source), 'deployed_source_sha256': sha(deployed),
        'dependencies': str(dependencies), 'dependencies_sha256': deps_hash,
        'selected_cache': str(cache), 'selected_cache_sha256': cache_hash,
        'cache_modified_at': dt.datetime.fromtimestamp(cache.stat().st_mtime).astimezone().isoformat(),
        'format': 'BC7_SRGB', 'source_alpha_histogram': histogram(original[:, :, 3]),
        'compiled_alpha_histogram': histogram(converted[:, :, 3]),
        'maximum_alpha_error_bytes': int(alpha_error.max()),
        'near_opaque_threshold': OPAQUE_LIMIT,
        'mips': [{'level': level, 'width': rgba.shape[1], 'height': rgba.shape[0],
                  'payload_start': start, 'payload_end': end,
                  'alpha_histogram': histogram(rgba[:, :, 3])}
                 for level, (rgba, start, end) in enumerate(mip_chain)],
        'housing_lods': lods, 'native_geometry_changed': False,
        'game_launched': False, 'native_visual_verified': False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('LENS_CONVERSION_PASS', len(mip_chain), 'mips;', len(lods),
          'housing LODs; max alpha error', int(alpha_error.max()), 'byte(s);', output)


if __name__ == '__main__':
    main()
