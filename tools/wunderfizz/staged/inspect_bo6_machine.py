"""Inspect the exact supplied BO6 native machine without running an extractor/game.

Only writes bounded task-owned staging receipts. Never edits native source payloads.
"""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT/'tmp/wunderfizz/assets/source'
MACHINE = SOURCE/'_custom/_wetegg/models/t10/t10_zm_machine_wunderfizz_fxanim'
sys.path.insert(0, str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel, xanim
from PIL import Image

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def blocks(text):
    return [(name,kind,dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*(?:\n[^"\n]*)*)"',body)))
            for name,kind,body in re.findall(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)\.gdf"\s*\)\s*\{(.*?)\n\s*\}',text,re.S)]

def inspect():
    gdt = MACHINE/'t10_zm_machine_wunderfizz_fxanim.gdt'
    definitions = blocks(gdt.read_text(encoding='utf-8-sig'))
    selected = {}
    for name,kind,fields in definitions:
        keep = [k for k,v in fields.items() if v and (kind != 'material' or any(s in k.lower() for s in ('type','map','tint','scale','alpha','gloss','spec','reflection','normal','shadow','falloff','cull','depth','emissive')))]
        if kind == 'xmodel':
            keep = [k for k,v in fields.items() if v and any(s in k.lower() for s in ('file','lod','skin','scale','surface','coll','phy','type'))]
        elif kind == 'xanim':
            keep = [k for k,v in fields.items() if v and any(s in k.lower() for s in ('file','frame','loop','type','use','note','delta'))]
        elif kind == 'image':
            keep = [k for k in ('baseImage','compressionMethod','coreSemantic','semantic','mipBase','mipMode','mipNorm','colorSRGB','noPicMip') if k in fields]
        selected[name]={'kind':kind,'fields':{k:fields[k] for k in keep}}
    models=[]
    for file in sorted((MACHINE/'xmodels').glob('*')):
        model=xmodel.Model(); model.LoadFile_Bin(str(file),split_meshes=True)
        coords=[v.offset for mesh in model.meshes for v in mesh.verts]
        assert coords and all(math.isfinite(v) for p in coords for v in p)
        material_names=[m.name for m in model.materials]
        assert all(name in selected and selected[name]['kind']=='material' for name in material_names)
        models.append({'file':str(file.relative_to(SOURCE)).replace('\\','/'),'sha256':sha(file),
            'triangles':sum(len(m.faces) for m in model.meshes),'vertices':len(coords),
            'bounds':[[min(p[j] for p in coords),max(p[j] for p in coords)] for j in range(3)],
            'materials':material_names,'bones':[{'name':b.name,'parent':b.parent,'offset':b.offset} for b in model.bones],
            'meshes':[{'name':m.name,'triangles':len(m.faces),'vertices':len(m.verts),'materials':sorted(set(material_names[f.material_id] for f in m.faces)),
                'bounds':[[min(v.offset[j] for v in m.verts),max(v.offset[j] for v in m.verts)] for j in range(3)]} for m in model.meshes]})
    images=[]
    for file in sorted((MACHINE/'_images').rglob('*.png')):
        with Image.open(file) as im:
            images.append({'file':str(file.relative_to(SOURCE)).replace('\\','/'),'sha256':sha(file),'size':list(im.size),'mode':im.mode,'extrema':im.getextrema()})
    animations=[]
    for file in sorted((MACHINE/'xanims').glob('*')):
        animation=xanim.Anim(); animation.LoadFile_Bin(str(file))
        animations.append({'file':str(file.relative_to(SOURCE)).replace('\\','/'),'sha256':sha(file),
            'parts':[p.name for p in animation.parts],'frames':len(animation.frames),'frame_indices':[animation.frames[0].frame,animation.frames[-1].frame],
            'framerate':animation.framerate,'notes':[{'frame':n.frame,'string':n.string} for n in animation.notes]})
    result={'source':'WetEgg BO6 machine port supplied in KingslayerKyle BO6Overhaul Assets v1.0',
        'archive_sha256':'3c6a12b993e32b667bdb10defc2b9392801dc1d7fd9462812b288a974088a0fa',
        'gdt_sha256':sha(gdt),'definitions':selected,'models':models,'images':images,'animations':animations,
        'source_payloads_unchanged':True,'native_visual_approval':'User playtest pending; no game launched.'}
    out=ROOT/'tmp/wunderfizz/assets/source_inspection.json'
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(out),'model_count':len(models),'image_count':len(images),'definitions':{k:sum(d['kind']==k for d in selected.values()) for k in ('image','material','xmodel','xanim')},
        'lod0':[{k:m[k] for k in ('file','triangles','bounds','materials','bones')} for m in models if 'LOD0.' in m['file']], 'animations':animations},indent=2))

if __name__=='__main__': inspect()
