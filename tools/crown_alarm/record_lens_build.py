"""Collect exact alarm repair delivery evidence after the guarded FULL build."""
import datetime, hashlib, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOLS = pathlib.Path('C:/BO3Tools/TOD2Cybercity')
WORK = ROOT / 'tmp/alarm_lens_repair'
ART = ROOT / 'art/crown_alarm/lens_review'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
log = WORK / 'full_build.log'
raw_log = log.read_bytes()
# Windows PowerShell redirection writes UTF-16LE; other approved wrappers use
# UTF-8. Preserve the actual transcript and accept either explicit BOM.
text = raw_log.decode('utf-16') if raw_log.startswith((b'\xff\xfe', b'\xfe\xff')) else raw_log.decode('utf-8-sig')
assert '[build] === BUILD OK ===' in text
assert '[build] mode = FULL geometry' in text
assert 'LENS_MATERIAL_VERIFIED:' in text and 'LENS_CONVERSION_PASS' in text
image = json.loads((ART / 'compiled_image.json').read_text())
material = json.loads((ART / 'compiled_material.json').read_text())
ff = TOOLS / 'usermaps/zm_tod2_cybercity/zone/zm_tod2_cybercity.ff'
ff_hash = sha(ff)
assert ff_hash == material['fastfile_sha256'], 'Fastfile changed after the actual material check'
deps = pathlib.Path(material['dependencies'])
assert sha(deps) == material['dependencies_sha256'], 'Dependency ledger changed after material verification'
baseline = json.loads((WORK / 'baseline_hashes.json').read_text())
runtime = {}
for rel in baseline:
    if not rel.startswith(('model_export/', 'source_data/', 'share/raw/', 'zone_source/')):
        continue
    source = ROOT / rel
    deployed = TOOLS / 'usermaps/zm_tod2_cybercity' / rel if rel.startswith('zone_source/') else TOOLS / rel
    assert sha(source) == sha(deployed), 'Deployed asset differs: ' + rel
    assert ff.stat().st_mtime >= max(source.stat().st_mtime, deployed.stat().st_mtime), 'Later sync: ' + rel
    runtime[rel] = sha(source)
authoring = {}
for p in (ROOT / 'tools/crown_alarm').glob('*.py'):
    if p.name in {'01_author.py', '02_integrate.py', 'surface_realism.py', '16_native_lens_preview.py',
                  '17_clear_lens.py', '18_finish_lens_preview.py', 'prepare_lens_repair.py',
                  'lens_repair_gate.py', 'verify_native.py', 'verify_surface_realism.py',
                  'verify_lens_conversion.py', 'verify_lens_material.py', 'mcp_call.py', 'mcp_render_server.py',
                  '19_review_binding_candidate.py', 'publish_lens_binding.py'}:
        authoring[p.relative_to(ROOT).as_posix()] = sha(p)
renders = {p.name: sha(p) for p in ART.glob('*.png')}
proof = {'verified_at': datetime.datetime.now().astimezone().isoformat(),
         'guarded_full_build': True, 'build_log': log.relative_to(ROOT).as_posix(), 'build_log_sha256': sha(log),
         'fastfile': str(ff), 'fastfile_sha256': ff_hash, 'fastfile_bytes': ff.stat().st_size,
         'fastfile_modified_at': datetime.datetime.fromtimestamp(ff.stat().st_mtime).astimezone().isoformat(),
         'geometry_and_lighting_reused': '[geom_key] REUSE:' in text,
         'runtime_source_deployment_parity': runtime, 'runtime_files': len(runtime),
         'authoring_sources': authoring, 'renders': renders,
         'compiled_image_receipt_sha256': sha(ART / 'compiled_image.json'),
         'compiled_material_receipt_sha256': sha(ART / 'compiled_material.json'),
         'all_18_alarm_lods_checked_by_build': 'CROWN_ALARM_NATIVE_PASS' in text and '"compiled_lods": 18' in text,
         'native_game_launched': False, 'native_playtested': False}
assert sha(ff) == ff_hash, 'Fastfile changed during delivery recording'
(ART / 'build.json').write_text(json.dumps(proof, indent=2) + '\n')
print('ALARM_LENS_BUILD_RECORDED', proof['runtime_files'], 'runtime files; native playtest pending')
