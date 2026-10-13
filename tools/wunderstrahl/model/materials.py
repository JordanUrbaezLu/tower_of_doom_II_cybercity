"""The ONE registry of the Wunderstrahl's shipped materials and images (read by install_art.py, the Blender previews
and verify_art.py, so the GDT, the review renders and the checks can never disagree).

Material families (CLAUDE.md: the weapon material types the Cyber Sword's proven blocks use; the glass follows the
crown alarm's proven transparent recipe, docs/crown_alarm/GLASS_REPAIR.md):
  opaque   lit_emissive_advanced_fullspec, scaleRGB 0 (no emission map)          stock / body / frame / coils
  emissive lit_emissive_advanced_fullspec, scaleRGB > 0, emissive map             core / bulbs / rear lamp / emitter
  glass    lit_emissive_transparent_advanced, colour-map alpha, $black_specular   the glass tube
Every block states surfaceType, waterRoughness 0 (fullspec binds it to the emissive parallax depth - the teleporter
pink-breakup lesson) and emissiveIncompetence 1. Images: colour + emissive + specular = sRGB 'compressed high color'
(BC7); gloss + normal = linear 'compressed'. A slot reads exactly the semantic its techset declares (SLOT_USAGE).
"""

PREVIEW_EMIT = 0.25   # Blender emission strength = scaleRGB * PREVIEW_EMIT in the (approximate) review renders

MATERIALS = {
    'mtl_tod2_ws_stock': dict(kind='opaque', surface='plastic', maps=dict(c='i_tod2_ws_stock_c', s='i_tod2_ws_stock_s',
                              g='i_tod2_ws_stock_g', n='i_tod2_ws_stock_n'), gloss=(0, 12), spec_amount=.5, probe=.25,
                              role='dark lacquered composite stock + bolt knob, worn to a warm under-layer, rubber butt pad'),
    'mtl_tod2_ws_body': dict(kind='opaque', surface='metal', maps=dict(c='i_tod2_ws_body_c', s='i_tod2_ws_body_s',
                             g='i_tod2_ws_body_g', n='i_tod2_ws_body_n'), gloss=(0, 12), spec_amount=.6, probe=.35,
                             role='receiver: dark gunmetal, brass fittings, heat-tinted radiator fins, charcoal braid with mustard tracer'),
    'mtl_tod2_ws_frame': dict(kind='opaque', surface='metal', maps=dict(c='i_tod2_ws_frame_c', s='i_tod2_ws_frame_s',
                              g='i_tod2_ws_frame_g', n='i_tod2_ws_frame_n'), gloss=(0, 12), spec_amount=.6, probe=.35,
                              role='frame, bellows, battery box: gunmetal worn to brass, black enamel, brass fittings'),
    'mtl_tod2_ws_coil': dict(kind='opaque', surface='metal', maps=dict(c='i_tod2_ws_coil_c', s='i_tod2_ws_coil_s',
                             g='i_tod2_ws_coil_g', n='i_tod2_ws_coil_n'), gloss=(0, 12), spec_amount=.6, probe=.35,
                             role='coils, claws, sockets: aged copper, yellow enamel switch cover, ivory insulators'),
    'mtl_tod2_ws_glass': dict(kind='glass', surface='glass', maps=dict(c='i_tod2_ws_glass_c', s='$black_specular',
                              g='i_tod2_ws_glass_g', n='i_tod2_ws_lamp_n'), gloss=(0, 8), spec_amount=.5, probe=.3,
                              spec_tint='.220916 .220916 .220916 1', role='clear, faintly warm glass tube with smudges'),
    'mtl_tod2_ws_core': dict(kind='emissive', surface='glass', maps=dict(c='i_tod2_ws_core_c', s='i_tod2_ws_core_s',
                             g='i_tod2_ws_core_g', n='i_tod2_ws_core_n', e='i_tod2_ws_core_e'), scale=12, falloff=2.0,
                             gloss=(0, 12), spec_amount=.5, probe=.3, role='the yellow laser filament in the glass tube'),
    'mtl_tod2_ws_bulb': dict(kind='emissive', surface='glass', maps=dict(c='i_tod2_ws_lamp_c', s='i_tod2_ws_lamp_s',
                             g='i_tod2_ws_lamp_g', n='i_tod2_ws_lamp_n', e='i_tod2_ws_lamp_e'), scale=7, falloff=1.5,
                             gloss=(0, 12), spec_amount=.5, probe=.3, role='the three side bulbs, warm yellow'),
    'mtl_tod2_ws_glow': dict(kind='emissive', surface='glass', maps=dict(c='i_tod2_ws_lamp_c', s='i_tod2_ws_lamp_s',
                             g='i_tod2_ws_lamp_g', n='i_tod2_ws_lamp_n', e='i_tod2_ws_lamp_e'), scale=5, falloff=2.5,
                             gloss=(0, 12), spec_amount=.5, probe=.3,
                             role='the rear indicator lamp: dark amber glass shell, glowing core (steep falloff = glass rims)'),
    'mtl_tod2_ws_emitter': dict(kind='emissive', surface='metal', maps=dict(c='i_tod2_ws_emitter_c',
                                s='i_tod2_ws_emitter_s', g='i_tod2_ws_emitter_g', n='i_tod2_ws_emitter_n',
                                e='i_tod2_ws_emitter_e'), scale=16, falloff=0.0, gloss=(0, 12), spec_amount=.6, probe=.35,
                                role='emitter rings, lens housing, focusing crystal, tie rods, conduits (baked atlas)'),
}

SLOT_FIELDS = {'c': 'colorMap', 's': 'specColorMap', 'g': 'cosinePowerMap', 'n': 'normalMap', 'e': 'colorMap00'}
MATERIAL_TYPE = {'opaque': 'lit_emissive_advanced_fullspec', 'emissive': 'lit_emissive_advanced_fullspec',
                 'glass': 'lit_emissive_transparent_advanced'}
# The image usage each (techset, slot) reads (share/raw/techsetdefs_stable: the fullspec techsets declare
# specColorMap 'specularMap'; lit_base's specular_base declares 'specularMask'; emissive_base 'diffuseMap','HDR').
SLOT_USAGE = {
    ('lit_emissive_advanced_fullspec', 'colorMap'): 'diffuseMap',
    ('lit_emissive_advanced_fullspec', 'specColorMap'): 'specularMap',
    ('lit_emissive_advanced_fullspec', 'cosinePowerMap'): 'glossMap',
    ('lit_emissive_advanced_fullspec', 'normalMap'): 'normalMap',
    ('lit_emissive_advanced_fullspec', 'colorMap00'): 'diffuseMap',
    ('lit_emissive_transparent_advanced', 'colorMap'): 'diffuseMap',
    ('lit_emissive_transparent_advanced', 'specColorMap'): 'specularMask',
    ('lit_emissive_transparent_advanced', 'cosinePowerMap'): 'glossMap',
    ('lit_emissive_transparent_advanced', 'normalMap'): 'normalMap',
}
SUFFIX_IMAGE = {   # file suffix -> (semantic, compression, sRGB)
    'c': ('diffuseMap', 'compressed high color', True),
    'e': ('diffuseMap', 'compressed high color', True),
    's': ('specularMap', 'compressed high color', True),
    'g': ('glossMap', 'compressed', False),
    'n': ('normalMap', 'compressed', False),
}


def images():
    """Every map name the materials reference (stock '$' images excluded)."""
    out = []
    for m in MATERIALS.values():
        for v in m['maps'].values():
            if not v.startswith('$') and v not in out:
                out.append(v)
    return sorted(out)
