"""Keep collapsed distant geometry inside the authored LOD0 footprint."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];STAGE=ROOT/'art/teleporter/engine_kit'
sys.path.insert(0,str(ROOT/'tools/cyber_reference_one'))
from native_geometry import clean
def main():
    base=json.loads((STAGE/'solid_lod0.json').read_text());lo=[min(v[i] for v in base['verts']) for i in range(3)];hi=[max(v[i] for v in base['verts']) for i in range(3)]
    counts=json.loads((STAGE/'lod_counts.json').read_text());changes={}
    for lod in range(1,7):
        path=STAGE/('solid_lod'+str(lod)+'.json');d=json.loads(path.read_text());changed=set()
        for j,v in enumerate(d['verts']):
            q=[max(lo[i],min(hi[i],v[i])) for i in range(3)]
            if q!=v:d['verts'][j]=q;changed.add(j)
        for face in d['faces']:
            if not any(c['v'] in changed for c in face):continue
            a,b,c=[d['verts'][v['v']] for v in reversed(face)];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n))
            if length>1e-10:
                for c in face:c['n']=[x/length for x in n]
        clean(d,min_altitude=.001);counts[str(lod)]['solid']=len(d['faces']);changes[str(lod)]=len(changed)
        path.write_text(json.dumps(d,separators=(',',':')))
    (STAGE/'lod_counts.json').write_text(json.dumps(counts,indent=2)+'\n')
    print('TELEPORTER_LOD_BOUNDS',changes)
if __name__=='__main__':main()
