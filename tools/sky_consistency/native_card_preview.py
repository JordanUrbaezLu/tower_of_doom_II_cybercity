"""Two preview states using the actual native card over the installed dull sky.

Native geometry/UV/maps/scale are exact source inputs. The display conversion,
alpha blending, tone response and absence of BO3 bloom remain approximations.
"""
import json
import math

from pass_config import ROOT, sha
from card_contract import blocks, load_card, validate_card_art

BEFORE = '01 Before jump - dull sky'
AFTER = '02 After reveal - native sign card'


def add_states(scene, stats):
    import bpy
    from mathutils import Matrix, Vector
    card = load_card()
    derived_art = validate_card_art(card)
    receipt = card['receipt']
    gdt = blocks(ROOT/'source_data/tod_skybox.gdt')
    stops = float(gdt['mtl_skybox_tod_cybercity'][1]['skyStops'])
    # Approximate native HDR -> the existing preview display-linear bracket.
    # The sky's display_mult is already in its world shader; do not apply it a
    # second time to a native emissive model. Record the assumption explicitly.
    display_factor = 1/(stats['preview_gain']*2**stops)
    native_scale = float(card['material']['scaleRGB'])
    scene.name = BEFORE
    scene['sign_state'] = 'before_jump'
    after = scene.copy()
    after.name = AFTER
    after['sign_state'] = 'after_reveal'
    # Scene.copy shares collections. Build a separate after-only collection so
    # the native card never leaks into the before scene through shared linking.
    collection = bpy.data.collections.new('After reveal | native card')
    after.collection.children.link(collection)
    material = bpy.data.materials.new('Native sign emission | approximate display')
    material.use_nodes = True
    material['native_fields'] = json.dumps(card['material'], sort_keys=True)
    material['native_scale_rgb'] = native_scale
    material['approximate_display_linear_per_native_hdr'] = display_factor
    material['native_visual_verified'] = False
    if hasattr(material, 'surface_render_method'):
        material.surface_render_method = 'DITHERED'
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    texture_nodes = {}
    for role in ('colorMap', 'colorMap00'):
        texture = nodes.new('ShaderNodeTexImage')
        texture.label = 'Native '+role
        texture.image = bpy.data.images.load(card['textures'][role]['path'], check_existing=True)
        texture.image.colorspace_settings.name = 'sRGB'
        texture.extension = 'CLIP'
        texture_nodes[role] = texture
    tint_values = [float(v) for v in card['material']['colorTint1'].split()][:3]
    tint_linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in tint_values]
    tint = nodes.new('ShaderNodeMixRGB'); tint.blend_type = 'MULTIPLY'; tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (*tint_linear, 1)
    links.new(texture_nodes['colorMap00'].outputs['Color'], tint.inputs[1])
    scale = nodes.new('ShaderNodeVectorMath'); scale.operation = 'SCALE'
    scale.label = 'Native scaleRGB × documented approximate display conversion'
    scale.inputs['Scale'].default_value = native_scale*display_factor
    links.new(tint.outputs[0], scale.inputs[0])
    gamma = nodes.new('ShaderNodeGamma'); gamma.inputs['Gamma'].default_value = 1/2.2
    links.new(scale.outputs['Vector'], gamma.inputs['Color'])
    emission = nodes.new('ShaderNodeEmission'); links.new(gamma.outputs['Color'], emission.inputs['Color'])
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(texture_nodes['colorMap'].outputs['Alpha'], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1]); links.new(emission.outputs[0], mix.inputs[2])
    output = nodes.new('ShaderNodeOutputMaterial'); links.new(mix.outputs[0], output.inputs['Surface'])
    elevation = math.radians(receipt['box_el'])
    forward = Vector((0, math.cos(elevation), math.sin(elevation)))
    right = Vector((1, 0, 0)); up = Vector((0, -math.sin(elevation), math.cos(elevation)))
    transform = Matrix(((-forward).to_tuple(), right.to_tuple(), up.to_tuple())).transposed().to_4x4()
    transform.translation = forward*receipt['sign_dist']
    model_scale = float(card['model_fields']['scale'])
    names = []
    for source in card['meshes']:
        mesh = bpy.data.meshes.new('Native card | '+source['name'])
        mesh.from_pydata(source['vertices'], [], [face['vertices'] for face in source['faces']]); mesh.update()
        uv = mesh.uv_layers.new(name='Native exported UV')
        for polygon, face in zip(mesh.polygons, source['faces']):
            for index, value in zip(polygon.loop_indices, face['uv']):
                uv.data[index].uv = value
        mesh.materials.append(material)
        obj = bpy.data.objects.new('Native card | '+source['name'], mesh)
        collection.objects.link(obj)
        obj.matrix_world = transform
        obj.scale = (model_scale,)*3
        obj['native_model'] = receipt['model']; obj['native_source_sha256'] = receipt['sha256']['model']
        names.append(obj.name)
    for state in (scene, after):
        state.camera.data.clip_end = max(100000, receipt['sign_dist']*10)
        state['preview_note'] = 'Actual dull sky HDR; after state adds native card geometry/UV/texture/scale. Display response and bloom are approximate; user playtest required.'
        state['preview_state_help'] = 'Choose 01 Before jump or 02 After reveal in the Scene selector.'
    require_visible = set(names)
    assert not require_visible.intersection(o.name for o in scene.objects), 'Native card leaked into before-jump scene'
    assert require_visible.issubset(o.name for o in after.objects), 'After-reveal scene lacks native card'
    for window in bpy.context.window_manager.windows:
        window.scene = after
    return {'default_scene': AFTER, 'states': {'before_jump': BEFORE, 'after_reveal': AFTER},
            'native_card_objects': names, 'native_card_triangles': card['triangles'],
            'native_scale_rgb': native_scale, 'native_model_scale': model_scale,
            'native_inputs': card['input_hashes'], 'sky_gdt_sha256': sha(ROOT/'source_data/tod_skybox.gdt'),
            'derived_art_inputs': derived_art,
            'sky_stops': stops, 'preview_gain': stats['preview_gain'], 'display_mult_sky_only': stats['display_mult'],
            'approximate_native_hdr_to_display_linear': display_factor,
            'mapping_assumption': 'Native emissive HDR uses 1/(preview_gain*2^skyStops); sky display_mult remains sky-only. Gamma 1/2.2 matches existing PNG bracket. Native bloom, alpha blending and tone mapping are not verified.',
            'transient_jump_fx_included': False, 'native_visual_verified': False}


def select(state):
    import bpy
    name = {'before_jump': BEFORE, 'after_reveal': AFTER}[state]
    scene = bpy.data.scenes.get(name)
    assert scene, 'Build the dual-state preview first'
    for window in bpy.context.window_manager.windows:
        window.scene = scene
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()
    print('SKY_PREVIEW_STATE', state, name)
