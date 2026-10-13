"""Verify native binaries, baked dependencies and optional packed LOD counts."""
import sys,json,hashlib,csv,math,argparse,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];KIT=ROOT/'art/partner_shop/engine_kit'
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
p=argparse.ArgumentParser();p.add_argument('--compiled-ledger',type=Path);args=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((KIT/'install_manifest.json').read_text())
assert sha(ROOT/m['master'])==m['master_sha256'];assert sha(ROOT/'source_data/tod_shop.gdt')==m['gdt_sha256']
for name,digest in m['textures'].items():assert sha(ROOT/'model_export/tod_shop/_images'/name)==digest
# Decode the small PNG without an optional Pillow dependency. The game marks
# color maps sRGB: decoded radiance must reproduce the master's linear values.
def png_rgb(file):
    raw=file.read_bytes();pos=8;compressed=b''
    while pos<len(raw):
        size=struct.unpack_from('>I',raw,pos)[0];kind=raw[pos+4:pos+8];data=raw[pos+8:pos+8+size];pos+=size+12
        if kind==b'IHDR':w,h,bits,color,_,_,interlace=struct.unpack('>IIBBBBB',data);assert bits==8 and color in (2,6) and interlace==0
        if kind==b'IDAT':compressed+=data
    bpp=3 if color==2 else 4;stride=w*bpp;data=zlib.decompress(compressed);rows=[];previous=[0]*stride
    for y in range(h):
        f=data[y*(stride+1)];encoded=data[y*(stride+1)+1:(y+1)*(stride+1)];row=[]
        for i,v in enumerate(encoded):
            a=row[i-bpp] if i>=bpp else 0;b=previous[i];c=previous[i-bpp] if i>=bpp else 0
            pred=0
            if f==1:pred=a
            elif f==2:pred=b
            elif f==3:pred=(a+b)//2
            elif f==4:
                p=a+b-c;dist=[abs(p-a),abs(p-b),abs(p-c)];pred=(a,b,c)[dist.index(min(dist))]
            row.append((v+pred)&255)
        rows.append(row);previous=row
    return lambda x,y:rows[y][x*bpp:x*bpp+3]
palette=json.loads((KIT/'palette_sources.json').read_text())
for suffix in ('c','e','s'):
    sample=png_rgb(ROOT/'model_export/tod_shop/_images'/('i_tod_shop_glow_'+suffix+'.png'))
    for i,row in enumerate(palette):
        rgb=sample((i%8)*8+4,63-((i//8)*8+4))
        decoded=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in rgb]
        assert all(abs(a-b)<.005 for a,b in zip(decoded,row[suffix])),(suffix,i,decoded,row[suffix])
for group in {row['group'] for row in palette}:
    geo=json.loads((KIT/(group+'_lod0.json')).read_text());actual={int(c['uv'][0]*8)+8*int((1-c['uv'][1])*8) for f in geo['faces'] for c in f}
    assert actual=={i for i,row in enumerate(palette) if row['group']==group},group
ledger={}
if args.compiled_ledger:
    with args.compiled_ledger.open(encoding='utf-8-sig',newline='') as f:ledger={r['name']:r for r in csv.DictReader(f)}
totals={};bounds={}
for r in m['models']:
    file=ROOT/r['file'];assert sha(file)==r['sha256'];model=xmodel.Model();model.LoadFile_Bin(str(file),split_meshes=True)
    assert len(model.bones)==1 and model.bones[0].name=='tag_origin'
    count=sum(len(mesh.faces) for mesh in model.meshes);assert count==r['triangles'];totals.setdefault(r['asset'],[]).append(count)
    xyz=[]
    for i,mesh in enumerate(model.meshes):
        for v in mesh.verts:assert v.weights==[(0,1.)] and all(math.isfinite(x) for x in v.offset);xyz.append(v.offset)
        assert all(f.mesh_id==i and f.material_id<len(model.materials) for f in mesh.faces)
        assert all(.99<sum(x*x for x in c.normal)<1.01 and all(math.isfinite(x) for x in c.uv) for f in mesh.faces for c in f.indices)
        for f in mesh.faces:
            if 'glow' not in model.materials[f.material_id].name:continue
            a,b,c=[tuple(struct.unpack('e',struct.pack('e',v))[0] for v in corner.uv) for corner in f.indices]
            assert abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))>1e-5, (r['asset'],r['lod'],'packed UV collapse')
    b=[[min(v[i] for v in xyz) for i in range(3)],[max(v[i] for v in xyz) for i in range(3)]]
    if r['lod']==0:bounds[r['asset']]=b
    else:
        original=bounds[r['asset']];assert all(b[0][i]>=original[0][i]-.001 and b[1][i]<=original[1][i]+.001 for i in range(3)),(r,b,original)
    if ledger:
        row=ledger[r['asset']];assert int(row['lodCount'])==7;assert int(row['tris'+str(6-r['lod'])])==count,(r,row)
for asset,counts in totals.items():assert all(a>=b>0 for a,b in zip(counts,counts[1:])),(asset,counts)
off=bounds['tod_shop_off'];assert off[0][0]>-104 and off[1][0]<97 and off[1][1]<64,off
report={'models':len(totals),'lod_files':len(m['models']),'triangles':totals,'bounds':bounds,'native_compiled_checked':bool(ledger),'native_playtested':False,'game_launched':False}
(KIT/('compiled_validation.json' if ledger else 'source_validation.json')).write_text(json.dumps(report,indent=2))
print('SHOP_NATIVE_VALIDATED',len(totals),'models;',len(m['models']),'LOD files; compiled='+str(bool(ledger)))
