"""MCP: execute the isolated reviewed lens author without publishing sources."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
candidate = ROOT / 'tmp/alarm_lens_repair/binding_candidate/tools/crown_alarm/17_clear_lens.py'
helper = ROOT / 'tmp/alarm_lens_repair/staged/tools/crown_alarm/surface_realism.py'
expected = {
    str(candidate): 'ad4d67b7e08bfd74af618742b4c082cf585a4e766b6239a936de3e7e7b128b3d',
    str(helper): '4d461beee39c85d5a99bc3baf613810f128d88885d1d58aed7cf94df50fe0ac2',
}
for path, digest in expected.items():
    assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() == digest, 'Candidate changed: ' + path
code = candidate.read_text(encoding='utf-8-sig')
anchor = 'ROOT = pathlib.Path(__file__).resolve().parents[2]'
assert code.count(anchor) == 1
# An isolated candidate sits deeper than the published tool; supply its actual
# repository root explicitly while keeping the real source filename in traces.
code = code.replace(anchor, 'ROOT = LENS_REVIEW_REPOSITORY_ROOT', 1)
exec(compile(code, str(candidate), 'exec'), {
    '__file__': str(candidate), '__name__': '__main__',
    'LENS_REVIEW_REPOSITORY_ROOT': ROOT,
})
review = ROOT / 'tmp/alarm_lens_repair/staged/art/crown_alarm/lens_review'
# This retained immutable candidate predates the scene-pin field. Add the pin
# immediately after its actual MCP save, before the finishing tool can load it.
authored_path = review / 'authoring.json'
authored = json.loads(authored_path.read_text())
authored['pre_finish_preview_sha256'] = hashlib.sha256((review / 'native_preview.blend').read_bytes()).hexdigest()
authored_path.write_text(json.dumps(authored, indent=2) + '\n')
receipt = review / 'binding_author_sources.json'
receipt.write_text(json.dumps({'executed_candidate_sources': expected, 'transport': 'Actual Blender MCP execute_blender_code', 'native_visual_verified': False}, indent=2) + '\n')
