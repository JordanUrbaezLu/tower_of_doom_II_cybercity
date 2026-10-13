"""Gate actual animated arm tracks, rig continuity, and native weapon bindings."""
import pathlib, sys, json, hashlib, math, re
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import asset, native_path
from PyCoD import xanim
NAME='vm_tod_gauntlet_left_hook'
path=ROOT/'xanim_export/tod_warrior'/f'{NAME}.XANIM_BIN'
a=xanim.Anim();a.LoadFile_Bin(str(path));ids={p.name:i for i,p in enumerate(a.parts)}
assert len(a.frames)==19 and a.framerate==30
position=lambda f,n:a.frames[f].parts[ids[n]].offset
distance=lambda a,b:math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
for name in ['j_elbow_le','j_wrist_le']:
    assert max(distance(position(0,name),position(f,name)) for f in range(19))>3,('static hook',name)
for p in a.parts:
    if p.name.startswith('tag_camera') or p.name in ['tag_weapon','j_wrist_ri']:
        assert all(a.frames[f].parts[ids[p.name]].offset==position(0,p.name) for f in range(19)),p.name
for start,end in [('j_shoulder_le','j_elbow_le'),('j_elbow_le','j_wrist_le'),('j_wrist_le','j_index_le_3')]:
    lengths=[distance(position(f,start),position(f,end)) for f in range(19)]
    assert max(lengths)-min(lengths)<.002,('retarget stretches the arm/fist',start,end,lengths)
for p in a.parts:
    assert distance(position(0,p.name),position(18,p.name))<.002,('idle seam',p.name)
# SMOOTH RETURN (2026-09-27, user: "a little bit of jiggle" going back into the pose):
# from the punch's apex home, the arm only ever closes on the idle pose. The first pass
# failed this (shoulder 44.8 -> 38.5 -> 41.0 deg: the donor's second pump).
def turn(f,n):
    m0,m=a.frames[0].parts[ids[n]].matrix,a.frames[f].parts[ids[n]].matrix
    return math.degrees(math.acos(max(-1,min(1,(sum(m0[i][j]*m[i][j] for i in range(3) for j in range(3))-1)/2))))
def returns_smoothly(turn,frames=19,tol=.05):
    for n in ['j_shoulder_le','j_elbow_le','j_wrist_le']:
        apex=max(range(frames),key=lambda f:turn(f,n))
        for f in range(apex,frames-1):
            if turn(f+1,n)>turn(f,n)+tol: return (n,f)
    return None
bad=returns_smoothly(turn)
assert bad is None,('left hook pushes back out on the way home (jiggle)',bad)
double=lambda f,n:[0,40,30,40,20,0][min(f,5)] if n=='j_shoulder_le' else 0
assert returns_smoothly(double,6)==('j_shoulder_le',2),'negative control: a second pump must fail'
manifest=json.loads((ROOT/'art/warrior_hook/manifest.json').read_text())
assert manifest['output_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
for source,sha in manifest['inputs'].items():
    assert hashlib.sha256(pathlib.Path(source).read_bytes()).hexdigest()==sha,('donor changed; reauthor hook',source)
def blocks(path):
    return {n:dict(re.findall(r'"(\w+)" "([^"\n]*)"',b)) for n,b in re.findall(r'\t"([^"]+)" \( "bulletweapon.gdf" \)\s*\{(.*?)\n\t\}',path.read_text(encoding='latin1'),re.S)}
weapons=blocks(ROOT/'source_data/tod_weapon_twins.gdt')
left={n:b for n,b in weapons.items() if n.startswith('cc_gauntlet') and n.endswith('_l_zm')}
assert len(left)==8,len(left)   # k0..k3 x base/PaP since 2026-09-28 (was 12: k0..k5)
for n,b in left.items():
    for field in ['meleeAnim','meleeAnimEmpty','meleeMissAnim','fireAnim','lastShotAnim','meleeChargeAnimHit']:
        assert b[field]==NAME,(n,field)
punch=blocks(ROOT/'source_data/tod_warrior_punch.gdt')['tod_bash_punch_zm']
for field in ['raiseAnim','quickRaiseAnim','firstRaiseAnim','emptyRaiseAnim']:
    assert punch[field]=='vm_zom_1inchpunch_melee',(field,punch[field])
for field in ['idleAnim','emptyIdleAnim']:assert punch[field]=='vm_zom_1inchpunch_idle'
print('WARRIOR ART PASS: visible left-arm motion, rigid bone lengths, idle seam, 8 left twins, and one ordinary Bash punch.')
