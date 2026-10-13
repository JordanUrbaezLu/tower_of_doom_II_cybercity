"""Read actual shipped material bindings, image semantics and UV-sampled gloss."""
import sys,sqlite3,json,hashlib,re,datetime
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];MT=Path('C:/BO3Tools/TOD2Cybercity')
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
db=sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True);db.execute('pragma writable_schema=ON');db.row_factory=sqlite3.Row
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for folder,model,mat,prefix in [('tod_teleporter','tod_teleporter','mtl_tod_teleporter','i_tod_teleporter'),('tod_heavenly_altar','tod_heavenly_altar','mtl_tod_altar','i_tod_altar'),('tod_shop','tod_shop_solid','mtl_tod_shop_body','i_tod_shop_body')]:
    r=dict(db.execute('select * from material where _name=?',(mat,)).fetchone())
    g=dict(db.execute('select * from image where _name=?',(prefix+'_g',)).fetchone())
    m=xmodel.Model();m.LoadFile_Bin(str(ROOT/'model_export'/folder/(model+'_lod0.xmodel_bin')),split_meshes=True)
    image=Image.open(ROOT/'model_export'/folder/'_images'/(prefix+'_g.png')).convert('RGB');w,h=image.size;v=[]
    for mesh in m.meshes:
        for f in mesh.faces[::max(1,len(mesh.faces)//1200)]:
            if m.materials[f.material_id].name!=mat:continue
            u=sum(c.uv[0] for c in f.indices)/3;vv=sum(c.uv[1] for c in f.indices)/3
            v.append(image.getpixel((min(w-1,max(0,int(u*w))),min(h-1,max(0,int(vv*h)))))[0]/255)
    v.sort();p=ROOT/'source_data'/(folder+'.gdt');dep=MT/'source_data'/p.name
    row={'material':mat,'database':{k:r.get(k) for k in ['glossRangeMin','glossRangeMax','specAmount','specColorTint','reflectionProbeAmount','specMapEnable','materialType']},'gloss_image':{k:g.get(k) for k in ['coreSemantic','semantic','colorSRGB','baseImage','compressionMethod']},'samples':len(v),'gloss_uv_centroids':{'p10':v[int(len(v)*.1)],'median':v[len(v)//2],'p90':v[int(len(v)*.9)]},'source_deployed_gdt_equal':sha(p)==sha(dep)}
    rows.append(row);print(json.dumps(row))
out=ROOT/'tmp/art_cohesion';out.mkdir(exist_ok=True)
(out/('finish_audit_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')).write_text(json.dumps(rows,indent=2))
