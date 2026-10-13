"""Explain native triangle differences rather than silently accepting loss."""
import pathlib,json,csv,re,math,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];ART=ROOT/'art/necro_staff'
sys.path.insert(0,str(ROOT/'tools/cyber_elites'))
from inspect_assets import xmodel
MT=pathlib.Path('C:/BO3Tools/TOD2Cybercity')
ledger=MT/'usermaps/zm_tod2_cybercity/zone_source/all/assetinfo/zm_tod2_cybercity_xmodel.csv'
with ledger.open(encoding='utf-8-sig',newline='') as f:rows={r['name']:r for r in csv.DictReader(f)}
transcript=(ROOT/'tmp/native_build/linker_last.log').read_text(encoding='utf-8-sig')
logs=[pathlib.Path(s) for s in re.findall(r'Log can be found here: ([^\r\n]+\.log)',transcript)]
def area(v):
    a,b,c=v;u=[b[i]-a[i] for i in range(3)];w=[c[i]-a[i] for i in range(3)]
    return .5*math.sqrt(sum(x*x for x in [u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]]))
counts=[]
for r in json.loads((ART/'models.json').read_text())['models']:
    row=rows[r['asset']];assert int(row['lodCount'])==3
    actual=int(row['tris'+str(2-r['lod'])]);difference=r['triangles']-actual
    result=dict(asset=r['asset'],lod=r['lod'],source=r['triangles'],compiled=actual,removed_slivers=difference)
    assert difference>=0
    if difference:
        log=next(p for p in logs if p.name.startswith(r['asset']+'_lod'+str(r['lod'])+'_'))
        areas=[]
        for block in log.read_text().split('Error:Triangle:Degenerate triangle (pre-bone)')[1:]:
            block=block.split('ErrorEnd:')[0]
            assert 'Material:mtl_tod_necro_staff_forge\n' in block,'Unexpected loss outside the blade geometry'
            verts=[tuple(map(float,line.split(':')[1].split(','))) for line in block.splitlines() if line.startswith(('Vert1:','Vert2:','Vert3:'))]
            areas.append(area(verts))
        assert len(areas)==difference,'Native triangle loss is not fully explained by converter diagnostics'
        m=xmodel.Model();m.LoadFile_Bin(str(ROOT/r['file']),split_meshes=True)
        total=sum(area([mesh.verts[ix.vertex].offset for ix in face.indices]) for mesh in m.meshes for face in mesh.faces)
        result.update(max_removed_triangle_area=max(areas),removed_surface_area=sum(areas),source_surface_area=total,removed_surface_percent=sum(areas)/total*100)
        # Tiny Boolean bevel slivers, not lost blade faces. Quantities use native
        # converter coordinates rounded to six decimals; this is an area bound,
        # not a claim of observed in-game pixels.
        assert max(areas)<.001 and sum(areas)/total<.0002,result
    counts.append(result)
data=dict(lods=counts,models_sha256=hashlib.sha256((ART/'models.json').read_bytes()).hexdigest(),native_visual_verified=False,note='All Tier 2 triangles retained. Tier 3 drops are fully accounted for by microscopic forged-blade slivers; under 0.02 percent of surface area in every LOD. Leather rim UV stretching warnings do not remove its geometry.')
(ART/'compiled_geometry.json').write_text(json.dumps(data,indent=2))
print('NATIVE STAFF GEOMETRY: all 12 LODs accounted for; Tier 3 loss limited to microscopic blade slivers')
