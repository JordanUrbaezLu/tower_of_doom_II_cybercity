"""Require the depth/detail pass to preserve the entire accepted city layout."""
import json
from pass_config import ROOT, STAGE, REVIEW, sha
before = REVIEW/'before/composition.json'
after = STAGE/'raw_4096.composition.json'
a,b = [json.loads(p.read_text(encoding='utf-8')) for p in (before,after)]
differences = [k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
assert not differences, 'Accepted city composition changed: '+repr(differences)
ordinary = [v for v in b['buildings'] if v['kept']]
assert len(ordinary)==1189 and b['visible_buildings']==1222
assert all(x['architecture'] in {'tapered_keel','split_crown','cantilever_relay','offset_slot'} for x in ordinary)
result = dict(status='pass',before=str(before.relative_to(ROOT)),after=str(after.relative_to(ROOT)),
              before_sha256=sha(before),after_sha256=sha(after), all_fields_equal=True,
              visible_buildings=1222,ordinary_shared_kit=1189,
              note='Every layout/material-family record equals the preserved v12 baseline. Surface geometry and shading are audited separately; no lots, silhouettes or celestial positions are reassigned.')
(REVIEW/'composition_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('DEPTH COMPOSITION OK: all fields identical to preserved v12')
