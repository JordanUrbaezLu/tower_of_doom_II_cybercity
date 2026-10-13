"""Blender-side helpers for the Wunderstrahl studio (imported by the MCP step scripts; needs bpy).

* xmodel -> Blender mesh with the native corner normals, UVs (v flipped) and optional skinning to a pose;
* an APPROXIMATE fullspec preview material (diffuse + Schlick-Fresnel GGX lobe coloured by the specular map, native
  gloss range, DirectX normal maps, HDR emission). It is a review aid, never BO3's BRDF, probes or exposure;
* the matched review studio (lights, cameras, render settings) shared by the before and after renders.
"""
import bpy, math, subprocess
from mathutils import Vector, Matrix

FP_HFOV = 80.0   # first-person review camera: BO3's default 80 degree horizontal field of view at 16:9


def game_running():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq BlackOps3.exe', '/NH'], capture_output=True, text=True, timeout=20)
        return 'BlackOps3.exe' in r.stdout
    except Exception:
        return True   # unknown = assume the game is up: render on the CPU


def clear_scene():
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for store in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                  bpy.data.node_groups, bpy.data.armatures):
        for block in list(store):
            store.remove(block)
    for im in list(bpy.data.images):
        if im.type == 'IMAGE':
            bpy.data.images.remove(im)
    return scene


def collection(name, parent=None, hide_render=False):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(coll)
    coll.hide_render = hide_render
    return coll


def bone_matrix(b):
    m = Matrix(b.matrix).transposed().to_4x4()
    m.translation = b.offset
    return m


def frame_matrix(part):
    m = Matrix(part.matrix).transposed().to_4x4()
    m.translation = part.offset
    return m


def pose_from_clip(model, clip, frame_index=0):
    """Per-bone skinning transforms (pose @ bind^-1) for `model` posed by one frame of a native clip. Bones the clip
    lacks follow their parent at bind offsets (the necro-staff review recipe, tools/necro_staff/motion_preview.py)."""
    idx = {p.name.lower(): i for i, p in enumerate(clip.parts)}
    frame = clip.frames[frame_index]
    poses = []
    for b in model.bones:
        key = b.name.lower()
        if key in idx:
            p = frame_matrix(frame.parts[idx[key]])
        elif b.parent >= 0:
            p = poses[b.parent] @ bone_matrix(model.bones[b.parent]).inverted() @ bone_matrix(b)
        else:
            p = bone_matrix(b)
        poses.append(p)
    return [p @ bone_matrix(b).inverted() for p, b in zip(poses, model.bones)]


def hold_bone(model, skin, anchor='tag_weapon'):
    """Re-express a posed skin so `anchor` stays at its bind transform: the weapon sits where the review cameras
    expect it, with every other bone (the clip, bolt, switch...) placed by the clip RELATIVE to it - the DG-2's
    bind pose leaves tag_clip's part floating under the gun, which no player ever sees."""
    i = [b.name for b in model.bones].index(anchor)
    fix = skin[i].inverted()
    return [fix @ s for s in skin]


def ads_skin(model, idle_clip, ads_clip):
    """The ADS pose: the idle frame with the torso moved to the last frame of ads_base_up (the ADS clips animate only
    tag_view and tag_torso; every other bone keeps its idle placement relative to the torso)."""
    skin = pose_from_clip(model, idle_clip, 0)
    ti = {p.name.lower(): i for i, p in enumerate(idle_clip.parts)}['tag_torso']
    ta = {p.name.lower(): i for i, p in enumerate(ads_clip.parts)}['tag_torso']
    move = frame_matrix(ads_clip.frames[-1].parts[ta]) @ frame_matrix(idle_clip.frames[0].parts[ti]).inverted()
    return [move @ s for s in skin]


def mesh_from_xmesh(name, model, xmesh, materials, coll, skin=None, keep_groups=False, skip_bones=None):
    """One Blender object for one native mesh. `materials` maps native material name -> bpy material.
    skip_bones: bone indices whose rigid faces are left out of THIS review object (the DG-2's reload bracket, which
    every non-reload clip parks behind the camera)."""
    verts = []
    for v in xmesh.verts:
        if skin is None or not v.weights:
            verts.append(tuple(v.offset))
        else:
            p = Vector((0, 0, 0))
            for bi, w in v.weights:
                p += (skin[bi] @ Vector(v.offset)) * w
            verts.append(tuple(p))
    faces, keep = [], []
    skip = set(skip_bones or ())
    for f in xmesh.faces:
        ids = (f.indices[0].vertex, f.indices[2].vertex, f.indices[1].vertex)
        if skip and all(xmesh.verts[i].weights and all(b in skip for b, _ in xmesh.verts[i].weights) for i in ids):
            continue
        if len(set(ids)) == 3:
            faces.append(ids); keep.append(f)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    slots = {}
    for f in keep:
        if f.material_id not in slots:
            slots[f.material_id] = len(me.materials)
            me.materials.append(materials[model.materials[f.material_id].name])
    uv = me.uv_layers.new(name='UVMap')
    normals = []
    rot = None
    if skin is not None:
        rot = []
        for v in xmesh.verts:
            if v.weights:
                m = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
                for bi, w in v.weights:
                    r = skin[bi].to_3x3()
                    m = Matrix([[m[i][j] + r[i][j] * w for j in range(3)] for i in range(3)])
                rot.append(m)
            else:
                rot.append(Matrix.Identity(3))
    for poly, f in zip(me.polygons, keep):
        poly.material_index = slots[f.material_id]
        poly.use_smooth = True
        for li, c in zip(poly.loop_indices, (f.indices[0], f.indices[2], f.indices[1])):
            uv.data[li].uv = (c.uv[0], 1.0 - c.uv[1])
            n = Vector(c.normal)
            if rot is not None:
                n = rot[c.vertex] @ n
            normals.append(n.normalized())
    me.normals_split_custom_set(normals)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    if keep_groups:
        groups = {}
        for vi, v in enumerate(xmesh.verts):
            for bi, w in v.weights:
                g = groups.get(bi)
                if g is None:
                    g = groups[bi] = ob.vertex_groups.new(name=model.bones[bi].name)
                g.add([vi], w, 'REPLACE')
    ob['native_faces'] = len(xmesh.faces)
    ob['native_degenerate_skipped'] = len(xmesh.faces) - len(keep)
    return ob


def srgb_to_linear(c):
    return tuple((x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4) for x in c)


def load_image(path, linear):
    im = bpy.data.images.load(str(path), check_existing=True)
    im.colorspace_settings.name = 'Non-Color' if linear else 'sRGB'
    return im


def fullspec(name, c, s=None, g=None, n=None, gloss=(0.0, 8.0), e=None, e_scale=0.0, e_tint=(1, 1, 1),
             color_tint=(1, 1, 1), spec_tint=(1, 1, 1), spec_const=None, gloss_const=None, alpha=None, uv='UVMap',
             e_falloff=0.0):
    """APPROXIMATE native preview. c/s/g/n/e are PNG paths (or None). alpha = (scale, offset): opacity from the colour
    map alpha * scale + offset (transparent materials). spec_const / gloss_const stand in for stock constant images.
    e_falloff mirrors the native emissiveFalloff power: emission * (N.V)^falloff (brightest facing the viewer)."""
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat['preview_limit'] = 'Approximate fullspec preview (diffuse + Fresnel GGX); not BO3 lighting or tone mapping'
    nt = mat.node_tree; N = nt.nodes; L = nt.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial'); out.location = (1400, 0)
    uvn = N.new('ShaderNodeUVMap'); uvn.uv_map = uv; uvn.location = (-1400, 0)

    def tex(path, linear, x, y):
        t = N.new('ShaderNodeTexImage'); t.image = load_image(path, linear); t.location = (x, y)
        t.interpolation = 'Linear'
        L.new(uvn.outputs['UV'], t.inputs['Vector'])
        return t

    def math_node(op, a, b=None, x=0, y=0):
        m = N.new('ShaderNodeMath'); m.operation = op; m.location = (x, y)
        for i, val in enumerate((a, b)):
            if val is None:
                continue
            if isinstance(val, (int, float)):
                m.inputs[i].default_value = val
            else:
                L.new(val, m.inputs[i])
        return m.outputs[0]

    def tint(socket, rgb, x, y):
        m = N.new('ShaderNodeMix'); m.data_type = 'RGBA'; m.blend_type = 'MULTIPLY'; m.location = (x, y)
        m.inputs['Factor'].default_value = 1.0
        L.new(socket, m.inputs['A']); m.inputs['B'].default_value = (*srgb_to_linear(rgb), 1)
        return m.outputs['Result']

    ct = tex(c, False, -1100, 400)
    base = tint(ct.outputs['Color'], color_tint, -800, 400)
    if s:
        spec = tint(tex(s, False, -1100, 100).outputs['Color'], spec_tint, -800, 100)
    else:
        rgb = N.new('ShaderNodeRGB'); rgb.location = (-800, 100)
        rgb.outputs[0].default_value = (*srgb_to_linear(spec_const or (.22, .22, .22)), 1)
        spec = rgb.outputs[0]
    if g:
        gv = tex(g, True, -1100, -200).outputs['Color']
        gv = math_node('MULTIPLY', gv, 1.0, -900, -200)   # colour -> scalar (grey maps)
    else:
        v = N.new('ShaderNodeValue'); v.outputs[0].default_value = gloss_const if gloss_const is not None else .5
        v.location = (-900, -200); gv = v.outputs[0]
    absolute = math_node('ADD', math_node('MULTIPLY', gv, gloss[1] - gloss[0], -750, -200), gloss[0], -600, -200)
    rough = math_node('POWER', math_node('DIVIDE', 2.0, math_node('ADD', math_node('POWER', 2.0, absolute, -450, -200),
                                                                   2.0, -300, -200), -150, -200), .25, 0, -200)
    normal_socket = None
    if n:
        nt_tex = tex(n, True, -1100, -500)
        sep = N.new('ShaderNodeSeparateXYZ'); sep.location = (-800, -500)
        com = N.new('ShaderNodeCombineXYZ'); com.location = (-500, -500)
        L.new(nt_tex.outputs['Color'], sep.inputs[0])
        L.new(sep.outputs[0], com.inputs[0])
        L.new(math_node('SUBTRACT', 1.0, sep.outputs[1], -650, -560), com.inputs[1])   # DirectX green -> Blender
        L.new(sep.outputs[2], com.inputs[2])
        nm = N.new('ShaderNodeNormalMap'); nm.location = (-300, -500); nm.uv_map = uv
        L.new(com.outputs[0], nm.inputs['Color'])
        normal_socket = nm.outputs['Normal']
    # Schlick Fresnel on the native F0 colour: F = F0 + (1 - F0) (1 - cos)^5
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .5; lw.location = (-300, 250)
    if normal_socket:
        L.new(normal_socket, lw.inputs['Normal'])
    f5 = math_node('POWER', lw.outputs['Facing'], 5.0, -100, 250)
    mixf = N.new('ShaderNodeMix'); mixf.data_type = 'RGBA'; mixf.location = (100, 200)
    L.new(f5, mixf.inputs['Factor']); L.new(spec, mixf.inputs['A']); mixf.inputs['B'].default_value = (1, 1, 1, 1)
    dif = N.new('ShaderNodeBsdfDiffuse'); dif.location = (300, 400)
    L.new(base, dif.inputs['Color'])
    glo = N.new('ShaderNodeBsdfAnisotropic'); glo.location = (300, 150)
    L.new(mixf.outputs['Result'], glo.inputs['Color']); L.new(rough, glo.inputs['Roughness'])
    if normal_socket:
        L.new(normal_socket, dif.inputs['Normal']); L.new(normal_socket, glo.inputs['Normal'])
    add = N.new('ShaderNodeAddShader'); add.location = (550, 300)
    L.new(dif.outputs[0], add.inputs[0]); L.new(glo.outputs[0], add.inputs[1])
    surface = add.outputs[0]
    if e and e_scale > 0:
        et = tex(e, False, -1100, -800)
        emc = tint(et.outputs['Color'], e_tint, -800, -800)
        em = N.new('ShaderNodeEmission'); em.location = (550, 0)
        L.new(emc, em.inputs['Color']); em.inputs['Strength'].default_value = e_scale
        if e_falloff > 0:
            lw2 = N.new('ShaderNodeLayerWeight'); lw2.inputs['Blend'].default_value = .5; lw2.location = (100, -900)
            if normal_socket:
                L.new(normal_socket, lw2.inputs['Normal'])
            ndv = math_node('SUBTRACT', 1.0, lw2.outputs['Facing'], 250, -900)
            L.new(math_node('MULTIPLY', math_node('POWER', ndv, e_falloff, 400, -900), e_scale, 550, -900),
                  em.inputs['Strength'])
        add2 = N.new('ShaderNodeAddShader'); add2.location = (800, 200)
        L.new(surface, add2.inputs[0]); L.new(em.outputs[0], add2.inputs[1])
        surface = add2.outputs[0]
    if alpha:
        op = math_node('ADD', math_node('MULTIPLY', ct.outputs['Alpha'], alpha[0], 800, -300), alpha[1], 950, -300)
        op = math_node('MINIMUM', op, 1.0, 1100, -300)
        tr = N.new('ShaderNodeBsdfTransparent'); tr.location = (950, -100)
        mix = N.new('ShaderNodeMixShader'); mix.location = (1200, 100)
        L.new(op, mix.inputs['Fac']); L.new(tr.outputs[0], mix.inputs[1]); L.new(surface, mix.inputs[2])
        surface = mix.outputs[0]
        mat.blend_method = 'BLEND'
    L.new(surface, out.inputs['Surface'])
    return mat


def flat_material(name, rgb, rough=.5, metal=0.0, emit=None, strength=0.0):
    """rgb / emit in sRGB 0-255 code values."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*srgb_to_linear([c / 255.0 for c in rgb]), 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if emit:
        p.inputs['Emission Color'].default_value = (*srgb_to_linear([c / 255.0 for c in emit]), 1)
        p.inputs['Emission Strength'].default_value = strength
    return mat


def look_at(ob, target, roll=0.0):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll)


def setup_render(scene, samples=96, res=(1600, 1000), glare=True):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transparent_max_bounces = 16
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    # Khronos PBR Neutral keeps authored hues (AgX bleached the yellow emitters to cream and greyed the brass); it
    # is still a review transform, not BO3's tone mapping.
    try:
        scene.view_settings.view_transform = 'Khronos PBR Neutral'
        scene.view_settings.look = 'None'
    except TypeError:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.0
    device = 'CPU'
    if not game_running():
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = 'OPTIX'
            prefs.get_devices()
            usable = [d for d in prefs.devices if d.type == 'OPTIX']
            for d in prefs.devices:
                d.use = d.type == 'OPTIX'
            if usable:
                device = 'GPU'
        except Exception:
            device = 'CPU'
    scene.cycles.device = device
    set_glare(scene, glare)
    return device


def set_glare(scene, on):
    """Optional bloom stand-in (compositor fog glow) so the yellow emitters read; renders are also made without it."""
    scene.use_nodes = True
    nt = scene.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    rl = nt.nodes.new('CompositorNodeRLayers'); rl.location = (0, 0)
    comp = nt.nodes.new('CompositorNodeComposite'); comp.location = (600, 0)
    if on:
        gl = nt.nodes.new('CompositorNodeGlare'); gl.location = (300, 0)
        gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.threshold = 1.0; gl.size = 7; gl.mix = -0.55
        nt.links.new(rl.outputs['Image'], gl.inputs['Image']); nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
    else:
        nt.links.new(rl.outputs['Image'], comp.inputs['Image'])


def studio(scene, centre=(15.0, 0.6, -1.0), scale=1.0):
    """Neutral review studio: warm-white key, neutral fill and rim, dark neutral world. Never tinted blue/cyan, so a
    render never invents a cool cast on the weapon."""
    coll = collection('STUDIO | lights + cameras (review only, never exported)')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    c = Vector(centre)

    def area(name, loc, energy, size, rgb):
        d = bpy.data.lights.new(name, 'AREA'); d.energy = energy * scale * scale; d.shape = 'DISK'; d.size = size * scale
        d.color = rgb
        o = bpy.data.objects.new(name, d); coll.objects.link(o); o.location = c + Vector(loc) * scale; look_at(o, c)
        return o
    area('Key softbox (warm white)', (-30, 60, 55), 42000, 40, (1.0, .97, .92))
    area('Fill softbox (neutral)', (40, -70, 20), 19000, 50, (.96, .96, .96))
    area('Rim strip (neutral)', (60, 40, -10), 26000, 22, (1, 1, 1))
    area('Top bounce', (0, 0, 90), 9000, 70, (1, 1, 1))
    w = scene.world or bpy.data.worlds.new('WS review world')
    scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (.032, .032, .034, 1); bg.inputs[1].default_value = .70
    return coll


def camera(name, loc, target, lens=50.0, ortho=None, roll=0.0, sensor=36.0):
    coll = collection('STUDIO | lights + cameras (review only, never exported)')
    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); coll.objects.link(cam)
    cam.data.sensor_width = sensor
    cam.data.clip_start = .05; cam.data.clip_end = 5000
    cam.location = Vector(loc); look_at(cam, target, roll)
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'; cam.data.lens = lens
    return cam


def fp_lens(sensor=36.0, hfov=FP_HFOV):
    return (sensor / 2.0) / math.tan(math.radians(hfov) / 2.0)


def render(scene, cam, path, samples=None):
    scene.camera = cam
    if samples:
        scene.cycles.samples = samples
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


def show_in_viewport(cam=None, shading='MATERIAL'):
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces.active
                sp.shading.type = shading
                sp.overlay.show_overlays = True
                if cam is not None:
                    bpy.context.scene.camera = cam
                    sp.region_3d.view_perspective = 'CAMERA'
