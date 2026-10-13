"""Approved engineered cyber gateway: packed authored RGBA on sparse sky tiles.

The imagegen edit replaces the crest with the Black Market dealer's hood,
red X eyes and stitched grin. The accepted engineered lettering/frame remain.
The crest glow follows the measured violet forehead channel.
Feature pixels use top-left source coordinates relative to the DOOM II center.
Same camera, AOV and no-city-light contract as the historical gate author.
Native quality awaits the user's playtest; source pixels are never edited here.

THE DULL STATE (2026-09-30, the first jump's title moment, docs/196 s6; the user: "the sign to not glow and
actually be very dull and then after explosion it should glow very bright"): GATE['sign_state'] == 'dull'
(build_city.py --sign-state dull) bakes the gate UNLIT into the sky - after the shared finish below, every pixel's
max channel is capped to DULL_CAP (the tubes' cores become dark tinted glass), desaturated by DULL_DESAT (the
metal loses the neon's pink rim light), the body emitted at DULL_BODY of its lit level, no neon boost. The LIT
sign is then not in the sky at all: the flyer's client draws it as a card model on the sign's bearing after the
crash (tools/jump_title/make_sign_card.py builds that card from the SAME source pixels and GATE geometry). The
'lit' state stays the default for A/B renders.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


COLLECTION = 'sky3d_cyber_hero_title'
PREFIX = COLLECTION + '_'
REFERENCE_WIDTH = 1536.0
IMAGE_SIZE = (1536, 1024)
TITLE_CENTER_PX = (768.0, 435.0)
CREST_LIGHT_RADIUS_FRACTION = 0.052083333333333336
# Feature centres measured from v12's bright cores; fixed title/text placement.
# Read-only source comparison and tolerances: sky_dealer/measure_art.py.
FEATURE_PIXELS = {'title': (0.0, 0.0), 'sub': (0.0, 121.0), 'ring': (3.3, -306.8), 'eye_l': (-28.5, -231.9), 'eye_r': (23.6, -232.0)}
# Linear emission hues, deliberately red/violet/red, matching the approved
# gate rather than the former white/cyan title and blue-white sensor glows.
CINEMATIC_COLORS = {'title': (1.0, 0.025, 0.045), 'title_core': (1.0, 0.15, 0.16), 'sub': (0.55, 0.025, 1.0), 'ring': (0.42, 0.025, 1.0), 'eye_l': (1.0, 0.015, 0.025), 'eye_r': (1.0, 0.015, 0.025)}
SOURCE_IMAGE = 'art/sky3d/sign/v12_dealer.png'
SOURCE_SHA256 = 'e22016bec6747396b71b4aa20aff1ff472f696f28704ced746191d277a995a17'
TILE_PIXELS = 12
# Presentation only: the first 4096 projection amplified this card by 8.0195
# before its original 3x highlight boost. Keep the shared GATE/FX contract and
# finish bracket intact while retaining the source's charcoal/crimson relief.
PRESENTATION_SCALE = 0.16
NEON_BOOST_RESPONSE = 0.20
CALIBRATION_REFERENCE = {
    'gain': 0.014114323569157832,
    'display_mult': 10.0,
    'preview_gain': 0.0176,
}
TEXT_RECTS_PX = {'TOWER OF DOOM II': (350.0, 297.0, 1187.0, 522.0), 'FALLEN CYBERCITY': (438.0, 529.0, 1094.0, 581.0)}
SIGN_STATES = ('lit', 'dull')
# THE DULL STATE (linear, applied to the finished card colour; see the docstring)
DULL_CAP = 0.05        # every pixel's max channel capped here: the tubes' white-hot cores become dark tinted glass
DULL_DESAT = 0.55      # then desaturated this far toward its luminance (the metal loses the neon's pink rim light)
DULL_BODY = 0.7        # ... and the whole card emitted at this share of the lit body level (an unlit gate at night)


def _material(image, gate, aov_name):
    import bpy

    material = bpy.data.materials.new(PREFIX + 'authored_relief')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()

    def node(kind, label):
        value = nodes.new(kind)
        value.name = value.label = label
        return value

    def math_node(operation, a, b, label):
        value = node('ShaderNodeMath', label)
        value.operation = operation
        for i, item in enumerate((a, b)):
            if isinstance(item, (float, int)):
                value.inputs[i].default_value = item
            else:
                links.new(item, value.inputs[i])
        return value.outputs[0]

    tex = node('ShaderNodeTexImage', 'Approved worn-metal RGBA; true straight alpha')
    tex.image = image
    tex.extension = 'CLIP'
    tex.interpolation = 'Linear'
    uv = node('ShaderNodeTexCoord', 'Unaltered image coordinates')
    links.new(uv.outputs['UV'], tex.inputs['Vector'])
    gamma = node('ShaderNodeGamma', 'Display decode: pure gamma 2.2')
    gamma.inputs['Gamma'].default_value = 2.2
    links.new(tex.outputs['Color'], gamma.inputs['Color'])
    luminance = node('ShaderNodeVectorMath', 'Rec.709 luminance')
    luminance.operation = 'DOT_PRODUCT'
    luminance.inputs[1].default_value = (0.2126, 0.7152, 0.0722)
    links.new(gamma.outputs['Color'], luminance.inputs[0])
    gray = node('ShaderNodeCombineXYZ', 'Luminance as neutral RGB')
    for socket in gray.inputs:
        links.new(luminance.outputs['Value'], socket)
    inverse_sat = node('ShaderNodeMixRGB', 'Undo finish saturation around luminance')
    inverse_sat.blend_type = 'MIX'
    inverse_sat.inputs[0].default_value = 1.0 / float(gate.get('sat', 1.2))
    links.new(gray.outputs['Vector'], inverse_sat.inputs[1])
    links.new(gamma.outputs['Color'], inverse_sat.inputs[2])
    split = node('ShaderNodeSeparateColor', 'Display-channel highlight selection')
    links.new(tex.outputs['Color'], split.inputs['Color'])
    peak = math_node('MAXIMUM', math_node('MAXIMUM', split.outputs['Red'],
                                         split.outputs['Green'], 'Max red / green'),
                     split.outputs['Blue'], 'Max display channel')
    gate_mask = node('ShaderNodeMapRange', 'Smooth neon highlight gate')
    gate_mask.clamp = True
    gate_mask.interpolation_type = 'SMOOTHSTEP'
    gate_mask.inputs['From Min'].default_value = float(gate.get('neon_lo', .55))
    gate_mask.inputs['From Max'].default_value = float(gate.get('neon_hi', .95))
    links.new(peak, gate_mask.inputs['Value'])
    boost = math_node('ADD', 1.0,
                      math_node('MULTIPLY', gate_mask.outputs['Result'],
                                (float(gate.get('neon', 3.0)) - 1.0) * NEON_BOOST_RESPONSE,
                                'Calibrated neon boost range'),
                      'Body white through restrained neon peak')
    energy = math_node('MULTIPLY', boost, float(gate.get('white', 1.0)) * PRESENTATION_SCALE,
                       'Existing W units with local presentation calibration')
    # Match the frame's prelit metal to the city's worn graphite. Preserve all
    # lettering and saturated light channels; no source pixels/alpha are edited.
    minimum = math_node('MINIMUM', math_node('MINIMUM', split.outputs['Red'],
                        split.outputs['Green'], 'Min red / green'), split.outputs['Blue'], 'Min display channel')
    saturation = math_node('DIVIDE', math_node('SUBTRACT', peak, minimum, 'Display chroma'),
                           math_node('MAXIMUM', peak, 0.001, 'Safe chroma divisor'), 'Relative chroma')

    def smooth(value, low, high, label):
        n = node('ShaderNodeMapRange', label)
        n.clamp = True
        n.interpolation_type = 'SMOOTHSTEP'
        n.inputs['From Min'].default_value = low
        n.inputs['From Max'].default_value = high
        links.new(value, n.inputs['Value'])
        return n.outputs['Result']

    neutral = math_node('SUBTRACT', 1.0, smooth(saturation, 0.10, 0.50, 'Metal versus colored light'), 'Neutral metal')
    uv_split = node('ShaderNodeSeparateXYZ', 'Source image UV')
    links.new(uv.outputs['UV'], uv_split.inputs['Vector'])
    u, v = uv_split.outputs['X'], uv_split.outputs['Y']
    horizontal = math_node('MULTIPLY', smooth(u, 345/1536, 350/1536, 'Text left feather'),
                          math_node('SUBTRACT', 1.0, smooth(u, 1187/1536, 1192/1536, 'Text right feather'), 'Before text right'), 'Text horizontal')
    vertical = math_node('MULTIPLY', smooth(v, 1-586/1024, 1-581/1024, 'Text bottom feather'),
                        math_node('SUBTRACT', 1.0, smooth(v, 1-297/1024, 1-292/1024, 'Text top feather'), 'Below text top'), 'Text vertical')
    outside_text = math_node('SUBTRACT', 1.0, math_node('MULTIPLY', horizontal, vertical, 'Protected lettering'), 'Architectural frame')
    metal_mask = math_node('MULTIPLY', neutral, outside_text, 'Frame metal only')
    shoulder = math_node('DIVIDE', 1.0, math_node('ADD', 1.0,
                         math_node('MULTIPLY', luminance.outputs['Value'], 2.0, 'Soft metal highlight compression'),
                         'Metal shoulder denominator'), 'Graphite highlight response')
    metal = node('ShaderNodeVectorMath', 'Graphite frame with retained surface relief')
    metal.operation = 'SCALE'
    links.new(inverse_sat.outputs['Color'], metal.inputs[0])
    links.new(shoulder, metal.inputs['Scale'])
    finish = node('ShaderNodeMixRGB', 'Shared city metal finish / unchanged title lights')
    finish.blend_type = 'MIX'
    links.new(metal_mask, finish.inputs[0])
    links.new(inverse_sat.outputs['Color'], finish.inputs[1])
    links.new(metal.outputs['Vector'], finish.inputs[2])
    state = gate.get('sign_state', 'lit')
    if state not in SIGN_STATES:
        raise ValueError('Unknown sign_state ' + repr(state) + '; want one of ' + repr(SIGN_STATES))
    colour_out, energy_out = finish.outputs['Color'], energy
    if state == 'dull':
        # THE DULL STATE (docs/196 s6): cap every pixel's max channel (the tubes, their halos and the neon's rim
        # light on the metal all go dark), desaturate toward luminance, no neon boost, the body dimmed. Same alpha,
        # same tiles, same finish above: only the emitted colour and strength change.
        lin_split = node('ShaderNodeSeparateColor', 'Linear channels for the dull cap')
        links.new(finish.outputs['Color'], lin_split.inputs['Color'])
        lin_peak = math_node('MAXIMUM', math_node('MAXIMUM', lin_split.outputs['Red'], lin_split.outputs['Green'],
                                                  'Max linear red / green'),
                             lin_split.outputs['Blue'], 'Max linear channel')
        cap_scale = math_node('MINIMUM', 1.0,
                              math_node('DIVIDE', DULL_CAP, math_node('MAXIMUM', lin_peak, 1e-4, 'Guarded peak'),
                                        'Cap over peak'),
                              'Dull cap scale (<= 1)')
        capped = node('ShaderNodeVectorMath', 'Capped linear colour')
        capped.operation = 'SCALE'
        links.new(finish.outputs['Color'], capped.inputs[0])
        links.new(cap_scale, capped.inputs['Scale'])
        cap_lum = node('ShaderNodeVectorMath', 'Rec.709 luminance of the capped colour')
        cap_lum.operation = 'DOT_PRODUCT'
        cap_lum.inputs[1].default_value = (0.2126, 0.7152, 0.0722)
        links.new(capped.outputs['Vector'], cap_lum.inputs[0])
        cap_gray = node('ShaderNodeCombineXYZ', 'Capped luminance as neutral RGB')
        for socket in cap_gray.inputs:
            links.new(cap_lum.outputs['Value'], socket)
        dull_mix = node('ShaderNodeMixRGB', 'Desaturate the dead sign')
        dull_mix.blend_type = 'MIX'
        dull_mix.inputs[0].default_value = DULL_DESAT
        links.new(capped.outputs['Vector'], dull_mix.inputs[1])
        links.new(cap_gray.outputs['Vector'], dull_mix.inputs[2])
        colour_out = dull_mix.outputs['Color']
        energy_out = math_node('MULTIPLY', 1.0, float(gate.get('white', 1.0)) * PRESENTATION_SCALE * DULL_BODY,
                               'Dull body level, no neon boost')
    emission = node('ShaderNodeEmission', 'Authored metal relief and local glow')
    links.new(colour_out, emission.inputs['Color'])
    links.new(energy_out, emission.inputs['Strength'])
    transparent = node('ShaderNodeBsdfTransparent', 'Open arch / sky remains transparent')
    surface = node('ShaderNodeMixShader', 'Preserved source alpha, including soft glow')
    links.new(tex.outputs['Alpha'], surface.inputs[0])
    links.new(transparent.outputs[0], surface.inputs[1])
    links.new(emission.outputs[0], surface.inputs[2])
    aov = node('ShaderNodeOutputAOV', 'Complete gate alpha to sign finish')
    aov.aov_name = aov_name
    links.new(tex.outputs['Alpha'], aov.inputs['Value'])
    output = node('ShaderNodeOutputMaterial', 'Cyber hero gate output')
    links.new(surface.outputs[0], output.inputs['Surface'])
    material.cycles.emission_sampling = 'NONE'
    material['display_decode_gamma'] = 2.2
    material['source_alpha_unchanged'] = True
    material['lights_city'] = False
    material['presentation_scale'] = PRESENTATION_SCALE
    material['neon_boost_response'] = NEON_BOOST_RESPONSE
    material['frame_metal_highlight_compression'] = 2.0
    material['lettering_and_saturated_channels_protected'] = True
    material['sign_state'] = state
    return material


def make_cyber_hero_title(gate, cam_h, repo, sign_aov='sign', log=print):
    import bpy
    import numpy as np
    from mathutils import Vector

    source = Path(repo) / SOURCE_IMAGE
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError('Cyber hero gate image changed; remeasure its literal feature contract')
    if gate.get('lights', False):
        raise ValueError('Cyber hero title is camera/glossy only; GATE lights must remain False')
    if float(gate.get('sat', 1.2)) <= 0:
        raise ValueError('Gate saturation decode must be positive')
    for key in ('D', 'w_deg', 'box_el'):
        if not math.isfinite(float(gate[key])):
            raise ValueError('Gate geometry must be finite')
    if float(gate['D']) <= 0 or not 0 < float(gate['w_deg']) < 150:
        raise ValueError('Gate distance/width are outside the authored card contract')

    old = bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                bpy.data.meshes.remove(data)
        bpy.data.collections.remove(old)
    for material in list(bpy.data.materials):
        if material.name.startswith(PREFIX) and material.users == 0:
            bpy.data.materials.remove(material)
    for image in list(bpy.data.images):
        if image.name.startswith(PREFIX) and image.users == 0:
            bpy.data.images.remove(image)

    collection = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    image = bpy.data.images.load(str(source), check_existing=False)
    image.name = PREFIX + 'packed_art'
    image.colorspace_settings.name = 'Non-Color'
    image.alpha_mode = 'STRAIGHT'
    width_px, height_px = tuple(image.size)
    if (width_px, height_px) != IMAGE_SIZE:
        raise ValueError('Gate image dimensions do not match its measured anchors')
    image.pack()

    eye = Vector((0.0, 0.0, float(cam_h)))
    elevation = math.radians(float(gate['box_el']))
    direction = Vector((0.0, math.cos(elevation), math.sin(elevation)))
    right = Vector((1.0, 0.0, 0.0))
    up = Vector((0.0, -math.sin(elevation), math.cos(elevation)))
    center = eye + direction * float(gate['D'])
    width_m = 2.0 * float(gate['D']) * math.tan(math.radians(float(gate['w_deg'])) / 2.0)
    scale = width_m / REFERENCE_WIDTH

    def point(u, v):
        return center + right * ((u - TITLE_CENTER_PX[0]) * scale) + up * ((TITLE_CENTER_PX[1] - v) * scale)

    def angles(p):
        q = p - eye
        return [math.degrees(math.atan2(q.x, q.y)),
                math.degrees(math.atan2(q.z, math.hypot(q.x, q.y)))]

    pixels = np.empty(width_px * height_px * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    alpha = pixels.reshape(height_px, width_px, 4)[::-1, :, 3]
    vertices, faces, uvs = [], [], []
    for v0 in range(0, height_px, TILE_PIXELS):
        for u0 in range(0, width_px, TILE_PIXELS):
            u1, v1 = min(u0 + TILE_PIXELS, width_px), min(v0 + TILE_PIXELS, height_px)
            # Include a one-pixel neighbor for linear texture interpolation at
            # a tile boundary; no nonzero alpha or glow is thresholded away.
            sample = alpha[max(0, v0 - 1):min(height_px, v1 + 1),
                           max(0, u0 - 1):min(width_px, u1 + 1)]
            if not np.any(sample > 0):
                continue
            base = len(vertices)
            corners = ((u0, v1), (u1, v1), (u1, v0), (u0, v0))
            vertices.extend(tuple(point(u, v)) for u, v in corners)
            uvs.extend((u / width_px, 1.0 - v / height_px) for u, v in corners)
            faces.append((base, base + 1, base + 2, base + 3))
    mesh = bpy.data.meshes.new(PREFIX + 'alpha_tiles_mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    uv.data.foreach_set('uv', np.asarray(uvs, dtype=np.float32).ravel())
    mesh.materials.append(_material(image, gate, sign_aov))
    obj = bpy.data.objects.new(PREFIX + 'authored_gate', mesh)
    collection.objects.link(obj)
    obj.visible_camera = True
    obj.visible_glossy = True
    obj.visible_shadow = False
    obj.visible_diffuse = False
    obj.visible_transmission = False
    obj.visible_volume_scatter = False
    obj['source_image'] = SOURCE_IMAGE
    obj['source_sha256'] = digest
    obj['source_alpha_unchanged'] = True
    obj['skyline_alpha_threshold'] = 0.25

    # Optional exact skyline audit contour: uppermost substantial-alpha pixel
    # in every four-column bin. It avoids treating faint glow as a solid roof.
    skyline_points = []
    for u0 in range(0, width_px, 4):
        u1 = min(width_px, u0 + 4)
        rows = np.flatnonzero(np.any(alpha[:, u0:u1] >= .25, axis=1))
        if len(rows):
            skyline_points.extend((tuple(point(u0, int(rows[0]))),
                                   tuple(point(u1, int(rows[0])))))
    obj['skyline_alpha_profile_world'] = [float(v) for p in skyline_points for v in p]

    layer = bpy.context.view_layer
    aov = next((a for a in layer.aovs if a.name == sign_aov), None)
    if aov is None:
        aov = layer.aovs.add()
        aov.name = sign_aov
    aov.type = 'VALUE'

    def bounds(points):
        values = [angles(Vector(p)) for p in points]
        return dict(azimuth_deg=[min(p[0] for p in values), max(p[0] for p in values)],
                    elevation_deg=[min(p[1] for p in values), max(p[1] for p in values)])

    features = {name: dict(reference_offset_px=list(offset),
                           source_pixel=[TITLE_CENTER_PX[0] + offset[0], TITLE_CENTER_PX[1] + offset[1]],
                           azimuth_elevation_deg=angles(point(TITLE_CENTER_PX[0] + offset[0], TITLE_CENTER_PX[1] + offset[1])),
                           sign_plane_offset_m=[offset[0] * scale, -offset[1] * scale])
                for name, offset in FEATURE_PIXELS.items()}
    state = gate.get('sign_state', 'lit')
    effective_white = float(gate.get('white', 1.0)) * PRESENTATION_SCALE * (DULL_BODY if state == 'dull' else 1.0)
    effective_neon = 1.0 if state == 'dull' else 1.0 + (float(gate.get('neon', 3.0)) - 1.0) * NEON_BOOST_RESPONSE
    reference_amplification = (CALIBRATION_REFERENCE['gain'] * CALIBRATION_REFERENCE['display_mult']
                               / CALIBRATION_REFERENCE['preview_gain'])
    report = dict(version='cyber_hero_title_dealer_3', collection=COLLECTION, sign_state=state,
                  dull=(dict(cap_linear=DULL_CAP, desaturate=DULL_DESAT, body=DULL_BODY) if state == 'dull' else None),
                  source_image=SOURCE_IMAGE, source_sha256=digest, image_size=[width_px, height_px],
                  image_packed=bool(image.packed_file), alpha_mode=image.alpha_mode,
                  reference_width_px=REFERENCE_WIDTH, reference_width_deg=float(gate['w_deg']),
                  title_anchor_deg=[0.0, float(gate['box_el'])], title_center_pixel=list(TITLE_CENTER_PX),
                  distance_m=float(gate['D']), width_m=width_m, metres_per_pixel=scale,
                  sign_bounds=bounds(vertices), skyline_alpha_threshold=.25,
                  skyline_alpha_profile_points=len(skyline_points),
                  text_bounds={name: bounds([point(u, v) for u, v in ((rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3]))])
                               for name, rect in TEXT_RECTS_PX.items()},
                  cinematic_features=features, cinematic_colors_linear_rgb=CINEMATIC_COLORS,
                  crest_light_radius_m=CREST_LIGHT_RADIUS_FRACTION * width_m,
                  sign_aov=sign_aov, sign_aov_value='unaltered source alpha', lights_city=False,
                  camera_glossy_only=True, display_decode_gamma=2.2, inverse_finish_saturation=float(gate.get('sat', 1.2)),
                  emission_w=dict(configured_white=float(gate.get('white', 1.0)),
                                  configured_neon_multiplier=float(gate.get('neon', 3.0)),
                                  white=effective_white, neon_multiplier=effective_neon,
                                  maximum_strength=effective_white * effective_neon),
                  presentation_correction=dict(scale=PRESENTATION_SCALE, neon_boost_response=NEON_BOOST_RESPONSE,
                                               reference_bracket=CALIBRATION_REFERENCE,
                                               reference_linear_amplification=reference_amplification,
                                               reference_body_linear_multiplier=reference_amplification * effective_white,
                                               reference_peak_linear_multiplier=reference_amplification * effective_white * effective_neon,
                                               note='Reference bracket is the first 4096 preview, not a runtime or subsequent render measurement.'),
                  frame_material_match=dict(metal_highlight_compression=2.0, protects_lettering=True,
                                            protects_saturated_light_channels=True, source_pixels_changed=False),
                  objects=1, base_faces=len(faces),
                  notes='Approved image contains rendered material relief. Coplanar alpha-aware card; packed source; no source-image edits or extra halo layer. Native presentation awaits the user.'
                        + (' DULL: baked unlit (the first jump lights it with a client card, docs/196 s6).' if state == 'dull' else ''))
    collection['authoring_receipt'] = json.dumps(report, sort_keys=True)
    log('cyber hero title: ' + json.dumps(report, sort_keys=True))
    return report
