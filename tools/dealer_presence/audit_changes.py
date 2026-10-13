"""Record exact isolated generator/map/zone delta from the pre-edit copies."""
from pathlib import Path
import hashlib,json,re,difflib
ROOT=Path(__file__).resolve().parents[2];BEFORE=ROOT/'tmp/dealer_presence_before';ART=ROOT/'art/dealer_presence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(BEFORE/'zm_tod2_cybercity.map').read_text(encoding='utf-8');new=(ROOT/'map_source/zm/zm_tod2_cybercity.map').read_text(encoding='utf-8')
patches=list(re.finditer(r'^// brush \d+ [\u2014-] dealer presence [^\n]*\n\{[\s\S]*?^\}\n?',new,re.M))
assert len(patches)==42
reduced=re.sub(r'^// brush \d+ [\u2014-] dealer presence [^\n]*\n\{[\s\S]*?^\}\n?','',new,flags=re.M)
def normalize(s):
    s=re.sub(r'^\s*guid "[^"\n]+"\s*\n','',s,flags=re.M)
    s=re.sub(r'^(// (?:brush|entity)) \d+',r'\1 N',s,flags=re.M)
    return '\n'.join(line for line in s.splitlines() if line.strip())
assert normalize(old)==normalize(reduced),'Non-Dealer map geometry/state changed during generator pass'
summary={'schema':1,'before':{},'after':{},'map_delta':{'added_noncolliding_quads':42,'added_triangles':84,'added_entities':0,'non_dealer_map_unchanged_ignoring_guids_and_numbering':True},'new_gdt_before':'absent; created by this pass'}
for name,rel in [('gen_tower_map.js','tools/gen_tower_map.js'),('zm_tod2_cybercity.zone','zone_source/zm_tod2_cybercity.zone'),('zm_tod2_cybercity.map','map_source/zm/zm_tod2_cybercity.map')]:
    summary['before'][rel]=sha(BEFORE/name);summary['after'][rel]=sha(ROOT/rel)
    if not name.endswith('.map'):
        diff=''.join(difflib.unified_diff((BEFORE/name).read_text(encoding='utf-8-sig').splitlines(True),(ROOT/rel).read_text(encoding='utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile=rel))
        (ART/(name+'.diff')).write_text(diff,encoding='utf-8')
(ART/'changes.json').write_text(json.dumps(summary,indent=2)+'\n');print('DEALER_CHANGE_AUDIT_OK: only 42 patches added; all other map content unchanged')
