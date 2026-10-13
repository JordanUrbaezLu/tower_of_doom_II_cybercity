"""The approved ominous cyber gate, authored RGBA art on a Blender sky card.

make_ominous_title(GATE, CAM_H, REPO, sign_aov='sign', log=print) -> report.
The art contains its rendered metal relief; additional decorative geometry is
unnecessary. Sparse coplanar tiles omit fully transparent canvas regions while
preserving every nonzero-alpha pixel, including the narrow authored glows.

No world, lights, camera, render/compositor settings or source image is changed.
Only this module's named collection/material/image are replaced. The image is
packed immediately, and its preserved repository path is recorded. The decoder
matches the prior reference card and the existing sky finisher: display RGB ->
gamma2.2 -> inverse saturation about Rec.709 Y -> white/neon W -> true alpha.
The gate is visible to camera/glossy rays only; it cannot light city or fog.

FEATURE_PIXELS and colors are literal, Blender-independent jump-FX contracts.
Pixel coordinates are top-left-origin. The main row uses its optical text
center, not a luminous centroid biased by the oversized right-hand numeral.
Eye centers were measured from their hot cores; halo center/radius from a
least-squares fit to its upper/lateral illuminated annulus. Image/provenance:
art/sky3d/sign/v9_ominous_gate.png and v9_ominous_gate.provenance.json.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


COLLECTION = 'sky3d_ominous_title'
PREFIX = COLLECTION + '_'
REFERENCE_WIDTH = 1414.0
IMAGE_SIZE = (1414, 1112)
TITLE_CENTER_PX = (707.0, 481.0)
CREST_LIGHT_RADIUS_FRACTION = 0.10254596888260255  # 145px / 1414px
FEATURE_PIXELS = {
    'title': (0.0, 0.0),
    'sub': (0.0, 134.0),
    'ring': (1.0, -174.0),
    'eye_l': (-37.0, -191.0),
    'eye_r': (41.0, -191.0),
}
# Linear emission hues, deliberately red/violet/red, matching the approved
# gate rather than the former white/cyan title and blue-white sensor glows.
CINEMATIC_COLORS = {
    'title': (1.0, 0.025, 0.045),
    'title_core': (1.0, 0.10, 0.12),
    'sub': (0.46, 0.025, 1.0),
    'ring': (1.0, 0.035, 0.12),
    'eye_l': (1.0, 0.015, 0.025),
    'eye_r': (1.0, 0.015, 0.025),
}
SOURCE_IMAGE = 'art/sky3d/sign/v9_ominous_gate.png'
SOURCE_SHA256 = 'c57446ab29a92f3c85b7cbc421ec3d04a8f96aed0b5e01e1b82cb6c31db9b580'
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
TEXT_RECTS_PX = {
    'TOWER OF DOOM II': (249.0, 373.0, 1165.0, 606.0),
    'FALLEN CYBERCITY': (416.0, 554.0, 1004.0, 678.0),
}


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
    emission = node('ShaderNodeEmission', 'Authored metal relief and local glow')
    links.new(inverse_sat.outputs['Color'], emission.inputs['Color'])
    links.new(energy, emission.inputs['Strength'])
    transparent = node('ShaderNodeBsdfTransparent', 'Open arch / sky remains transparent')
    surface = node('ShaderNodeMixShader', 'Preserved source alpha, including soft glow')
    links.new(tex.outputs['Alpha'], surface.inputs[0])
    links.new(transparent.outputs[0], surface.inputs[1])
    links.new(emission.outputs[0], surface.inputs[2])
    aov = node('ShaderNodeOutputAOV', 'Complete gate alpha to sign finish')
    aov.aov_name = aov_name
    links.new(tex.outputs['Alpha'], aov.inputs['Value'])
    output = node('ShaderNodeOutputMaterial', 'Ominous gate output')
    links.new(surface.outputs[0], output.inputs['Surface'])
    material.cycles.emission_sampling = 'NONE'
    material['display_decode_gamma'] = 2.2
    material['source_alpha_unchanged'] = True
    material['lights_city'] = False
    material['presentation_scale'] = PRESENTATION_SCALE
    material['neon_boost_response'] = NEON_BOOST_RESPONSE
    return material


def make_ominous_title(gate, cam_h, repo, sign_aov='sign', log=print):
    import bpy
    import numpy as np
    from mathutils import Vector

    source = Path(repo) / SOURCE_IMAGE
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError('Ominous gate image changed; remeasure its literal feature contract')
    if gate.get('lights', False):
        raise ValueError('Ominous title is camera/glossy only; GATE lights must remain False')
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
    effective_white = float(gate.get('white', 1.0)) * PRESENTATION_SCALE
    effective_neon = 1.0 + (float(gate.get('neon', 3.0)) - 1.0) * NEON_BOOST_RESPONSE
    reference_amplification = (CALIBRATION_REFERENCE['gain'] * CALIBRATION_REFERENCE['display_mult']
                               / CALIBRATION_REFERENCE['preview_gain'])
    report = dict(version='ominous_gate_1', collection=COLLECTION,
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
                  objects=1, base_faces=len(faces),
                  notes='Approved image contains rendered material relief. Coplanar alpha-aware card; packed source; no source-image edits or extra halo layer. Native presentation awaits the user.')
    collection['authoring_receipt'] = json.dumps(report, sort_keys=True)
    log('ominous title: ' + json.dumps(report, sort_keys=True))
    return report
