"""Repeatable alarm-only intensity pass. No shared files, sync, build or launch."""
import ast, hashlib, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
ART = ROOT / 'art/crown_alarm'
PROFILE = json.loads((ROOT / 'tools/crown_alarm/light_profile.json').read_text())
FX = ROOT / 'share/raw/fx/tod/crown_alarm/fx_tod_alarm_sweep.efx'
GDT = ROOT / 'source_data/tod_crown_alarm.gdt'
BEFORE = ART / 'intensity_before'
BEFORE.mkdir(exist_ok=True)
for path in (FX, GDT, ART / 'manifest.json', ART / 'crown_alarm.blend'):
    dst = BEFORE / path.name
    if path.exists() and not dst.exists():
        shutil.copyfile(path, dst)

donor = ast.parse((ROOT / 'tools/gen_tod_inducer_fx.py').read_text())
exec(compile(ast.Module(body=[n for n in donor.body if isinstance(n, ast.FunctionDef)
     and n.name in ('replace_graph', 'retint')], type_ignores=[]), 'fx_helpers', 'exec'))
s = retint((ROOT / 'share/raw/fx/tod/fx_tod_inducer_on.efx').read_text(), tuple(PROFILE['color']))
for key, value in [('lightIntensityGraph', PROFILE['intensity']),
                   ('lightRadiusGraph', PROFILE['radius']),
                   ('lightFovGraph', PROFILE['fov_degrees']), ('alphaGraph', 1)]:
    s = replace_graph(s, key, value, [(0, 1), (1, 1)])
fields = {
    'name': '"crown_rotor_red_spot"',
    'spawnLooping': f"{PROFILE['interval_ms']} 0",
    'lifeSpanMsec': f"{PROFILE['interval_ms']} 0",
    'spawnOrgX': '9 0', 'spawnOrgY': '0 0', 'spawnOrgZ': '2 0',
    'spawnRange': f"0 {PROFILE['spawn_range']}",
    'spawnFrustumCullRadius': PROFILE['bounds'],
    'spawnOffsetRadius': '0 0', 'initialRot': '0 0',
    'efBoundingBoxMin': ' '.join([str(-PROFILE['bounds'])] * 3),
    'efBoundingBoxMax': ' '.join([str(PROFILE['bounds'])] * 3),
}
for key, value in fields.items():
    # Only semicolon-terminated element fields; never consume embedded KVPs.
    s, count = re.subn(r'(?m)^(\t' + re.escape(key) + r') [^;\r\n]+;',
                      lambda m: m[1] + ' ' + str(value) + ';', s)
    assert count == 1, (key, count)
s = s.replace('PRIMARY_TYPE PRIMARY_OMNI', 'PRIMARY_TYPE PRIMARY_SPOT')
s = re.sub(r'(?m)^(\s*_color) [^\r\n]+', r'\1 1 0 0', s)
FX.parent.mkdir(parents=True, exist_ok=True)
FX.write_text(s)

# Distant crown lamps previously had NO light. A shadowless omni reveals the
# surrounding arms from below regardless of the rotating reflector's direction.
high_fx = FX.with_name('fx_tod_alarm_high.efx')
hs = s.replace('PRIMARY_TYPE PRIMARY_SPOT', 'PRIMARY_TYPE PRIMARY_OMNI')
for key, value in [('lightIntensityGraph', PROFILE['high_intensity']),
                   ('lightRadiusGraph', PROFILE['high_radius'])]:
    hs = replace_graph(hs, key, value, [(0, 1), (1, 1)])
for key, value in dict(name='"crown_high_red_spill"', spawnOrgX='0 0',
                      spawnOrgZ='0 0', spawnRange=f"0 {PROFILE['high_spawn_range']}",
                      spawnFrustumCullRadius=PROFILE['high_bounds'],
                      efBoundingBoxMin=' '.join([str(-PROFILE['high_bounds'])]*3),
                      efBoundingBoxMax=' '.join([str(PROFILE['high_bounds'])]*3)).items():
    hs, count = re.subn(r'(?m)^(\t' + re.escape(key) + r') [^;\r\n]+;',
                       lambda m: m[1] + ' ' + str(value) + ';', hs)
    assert count == 1, key
high_fx.write_text(hs)

gdt = GDT.read_text()
pattern = r'("mtl_tod_alarm_lamp_on" \( "material.gdf" \)\s*\{[^}]*?"scaleRGB" ")[^"]+("[\s\S]*?\n\t\})'
gdt, count = re.subn(pattern, lambda m: m[1] + str(PROFILE['lamp_emission']) + m[2], gdt)
assert count == 1

# The distant 16 crown points and apex reuse all three existing rotor meshes.
# A material skin variant isolates their brightness from the accepted hall lamps.
def clone_block(source, target, updates):
    global gdt
    pattern = r'\t"' + re.escape(source) + r'" \( "([^"]+)" \)\s*\{(.*?)\n\t\}'
    match = re.search(pattern, gdt, re.S)
    assert match, source
    fields = dict(re.findall(r'"([^"\n]+)" "([^"\n]*)"', match[2]))
    fields.update(updates)
    old = r'\t"' + re.escape(target) + r'" \( "[^"]+" \)\s*\{.*?\n\t\}\n?'
    gdt = re.sub(old, '', gdt, flags=re.S)
    block = '\t"' + target + '" ( "' + match[1] + '" )\n\t{\n'
    block += ''.join('\t\t"' + key + '" "' + str(value) + '"\n' for key, value in fields.items())
    block += '\t}\n'
    end = gdt.rfind('}')
    gdt = gdt[:end] + block + gdt[end:]

for source, target in [('tod_crown_alarm_housing', 'tod_crown_alarm_housing_high'),
                       ('tod_crown_alarm_rotor_off', 'tod_crown_alarm_rotor_high_off')]:
    clone_block(source, target, {key: 'tod_crown_alarm/' + target + '_lod' + str(lod) + '.xmodel_bin'
                                for lod, key in enumerate(['filename', 'mediumLod', 'lowLod'])})
variant = dict(asset='tod_crown_alarm_rotor_high_on', source_asset='tod_crown_alarm_rotor_high_off',
               skin_override='mtl_tod_alarm_lamp_off mtl_tod_alarm_lamp_high_on')
clone_block('mtl_tod_alarm_lamp_on', 'mtl_tod_alarm_lamp_high_on',
            dict(scaleRGB=PROFILE['lamp_emission'] * PROFILE['high_lamp_multiplier']))
clone_block(variant['source_asset'], variant['asset'], dict(skinOverride=variant['skin_override']))
GDT.write_text(gdt)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((ART / 'manifest.json').read_text())
manifest.update(light_profile=PROFILE, gdt_sha256=sha(GDT), spotlight_sha256=sha(FX), high_light_sha256=sha(high_fx), variants=[variant])
(ART / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('ALARM_INTENSITY_SOURCE_READY', json.dumps(PROFILE))
