"""Verify retained source payloads and lossless native world-model geometry."""
from pathlib import Path
import hashlib,json,struct,sys

ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel

def main():
    source=ROOT/'source_library/archer_equipment/retriever'
    manifest=json.loads((source/'manifest.json').read_text())
    assert not manifest['missing_audio'],manifest['missing_audio']
    for record in manifest['files']:
        path=source/record['path'];data=path.read_bytes()
        assert len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'],path
    models=[]
    for lod in range(3):
        src=xmodel.Model();src.LoadFile_Bin(str(source/f'model_export/t6_wpn_zmb_tomahawk_world_lod{lod}.xmodel_bin'))
        dst=xmodel.Model();dst.LoadFile_Bin(str(ROOT/f'model_export/tod_archer/tod_archer_retriever_world_lod{lod}.xmodel_bin'))
        assert len(src.meshes)==len(dst.meshes) and len(src.materials)==len(dst.materials)
        assert [b.name for b in dst.bones]==['tag_weapon','tag_knife_fx']
        assert src.bones[0].offset==dst.bones[0].offset
        for a,b in zip(src.meshes,dst.meshes):
            assert len(a.verts)==len(b.verts) and len(a.faces)==len(b.faces)
            for av,bv in zip(a.verts,b.verts):
                assert av.offset==bv.offset and av.weights==bv.weights
            for af,bf in zip(a.faces,b.faces):
                for av,bv in zip(af.indices,bf.indices):
                    assert all(getattr(av,k)==getattr(bv,k) for k in ('vertex','normal','color','uv'))
        models.append({'lod':lod,'triangles':sum(len(m.faces) for m in dst.meshes),'geometry_equal':True})
    staged=json.loads((ROOT/'art/archer_assets/engine_kit/retriever_source.json').read_text())
    for tex in staged['textures']:
        dds=(ROOT/tex['source']).read_bytes();png=(ROOT/tex['file']).read_bytes()
        assert dds[:4]==b'DDS ' and png[:8]==b'\x89PNG\r\n\x1a\n'
        height,width=struct.unpack_from('<II',dds,12)
        assert struct.unpack_from('>II',png,16)==(width,height),tex
    result={'source_hashes_verified':len(manifest['files']),'resolved_audio_alias_rows':len(manifest['audio_aliases']),
            'models':models,'native_texture_dimensions_preserved':True,'native_playtest':False}
    out=ROOT/'docs/archer_equipment_evidence/retriever_source.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print('RETRIEVER_VERIFIED',json.dumps(result))

if __name__=='__main__':main()
