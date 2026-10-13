"""Convert MCP-staged geometry/textures and selected Apex audio for private BO3."""
import csv, hashlib, json, re, subprocess, sys, wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/archer_assets';OUT=ROOT/'model_export/tod_archer'
LIB=ROOT/'source_library/archer_equipment/apex_grapple'
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def block(name,kind,fields):
    return '\t"'+name+'" ( "'+kind+'.gdf" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'

def main():
    manifest=json.loads((ART/'engine_kit/source_manifest.json').read_text())
    blocks=[];models=[]
    for rec in manifest['models']:
        kind=rec['asset'];asset='tod_archer_'+kind
        d=json.loads((ART/'engine_kit'/(kind+'.json')).read_text())
        m=xmodel.Model(asset)
        bone=xmodel.Bone('tag_origin');bone.offset=(0,0,0);bone.matrix=[(1,0,0),(0,1,0),(0,0,1)];m.bones=[bone]
        m.materials=[xmodel.Material(d['material'],'Phong',{})]
        mesh=xmodel.Mesh(kind);mesh.verts=[xmodel.Vertex(v,[(0,1.)]) for v in d['verts']]
        for face in d['faces']:
            f=xmodel.Face(0,0);f.indices=[xmodel.FaceVertex(c['v'],tuple(c['n']),(1,1,1,1),tuple(c['uv'])) for c in face];mesh.faces.append(f)
        m.meshes=[mesh]
        file=OUT/(asset+'.xmodel_bin');m.WriteFile_Bin(str(file),version=7)
        blocks.append(block(asset,'xmodel',{'filename':'tod_archer\\\\'+file.name,'type':'rigid','scale':1,'CollisionMap':'','BulletCollisionLOD':'None','physicsPreset':'','mediumLod':'','lowLod':'','lowestLod':'','lod4File':'','lod5File':'','lod6File':'','lod7File':'','autogenMediumLod':0,'autogenLowLod':0,'autogenLowestLod':0,'autogenLod4':0,'autogenLod5':0,'autogenLod6':0,'autogenLod7':0,'noCastShadow':0}))
        prefix='i_tod_archer_'+kind
        blocks.append(block('mtl_tod_archer_'+kind,'material',{'surfaceType':'metal','template':'material.template','materialCategory':'Geometry','materialType':'lit','colorMap':prefix+'_col','normalMap':prefix+'_nml','cosinePowerMap':prefix+'_gls','specColorMap':prefix+'_spc','specMapEnable':1,'colorTint':'1 1 1 1','normalHeightScale':1,'glossRangeMin':0,'glossRangeMax':8,'specAmount':.45,'reflectionProbeAmount':.2,'usage':'<not in editor>'}))
        models.append({'asset':asset,'triangles':len(d['faces']),'file':file.relative_to(ROOT).as_posix(),'sha256':sha(file)})
    for file in (OUT/'_images').glob('*.png'):
        if file.stem.startswith('i_tod_archer_hands_') or file.stem.startswith('i_tod_retriever_ember_atlas'):
            continue # Defined by the first-person/ember stages, not this base kit.
        suffix=file.stem.rsplit('_',1)[-1]
        fields={'baseImage':file.relative_to(ROOT).as_posix(),'imageType':'Texture','type':'image','semantic':{'col':'diffuseMap','nml':'normalMap','spc':'specularMap','gls':'glossMap'}.get(suffix,'diffuseMap'),'streamable':0 if suffix=='hud' else 1,'compressionMethod':'compressed' if suffix in ('nml','gls') else 'compressed high color'}
        if suffix not in ('nml','gls'):fields['coreSemantic']='sRGB3chAlpha'
        if suffix=='hud':fields.update({'semantic':'2d','noMipMaps':1,'clampU':1,'clampV':1,'compressionMethod':'uncompressed'})
        if file.stem=='i_tod_archer_cable':fields['semantic']='effectMap'
        blocks.append(block(file.stem,'image',fields))
    # Native cross-section beam using the original braided cable albedo.
    blocks.append(block('mtl_tod_archer_cable','material',{'surfaceType':'<none>','template':'material.template','materialCategory':'Effect','materialType':'effect_lit_emissive_blend','colorMap':'i_tod_archer_cable','colorTint':'0.55 0.55 0.55 1','scaleRGB':1,'textureAtlasRowCount':1,'textureAtlasColumnCount':1,'cullFace':'None','usage':'<not in editor>'}))
    source=Path('C:/BO3Tools/TOD2Cybercity/source_data/t7_beams.gdt').read_text()
    match=re.search(r'"zod_beast_grapple_beam"\s*\(\s*"beam.gdf"\s*\)\s*\{([^}]+)\}',source)
    fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',match[1]))
    for k in fields:
        if any(k.startswith(p) for p in ('sawtooth','sine','square','triangle')) and ('AmplitudeX' in k or 'AmplitudeY' in k or 'Weight' in k):fields[k]='0'
    fields.update({'material':'mtl_tod_archer_cable','beamShape':'hexagon','curveType':'smooth','startWidth':.3,'endWidth':.3,'numSegments':24,'maxLength':3600,'leadinDistance':0,'leadoutDistance':0,'slackMinSlack':0,'slackDurationMsec':0,'slackEaseInTimeMsec':0,'slackEaseOutTimeMsec':0,'launchSpeed':0,'retractSpeed':0,'textureRepeatLength':24})
    blocks.append(block('tod_archer_cable','beam',fields))
    gdt=ROOT/'source_data/tod_archer.gdt';gdt.write_text('{\n'+''.join(blocks)+'}\n')

    ffmpeg=next((Path.home()/'AppData/Local/Microsoft/WinGet/Packages').glob('Gyan.FFmpeg*/ffmpeg-*/bin/ffmpeg.exe'))
    sound=ROOT/'sound_assets/tod/archer';sound.mkdir(parents=True,exist_ok=True)
    samples={'hook_fire':next((LIB/'audio').rglob('grapple_fire_2ch_v1_01.wav')),
             'hook_attach':next((LIB/'audio').rglob('imp_grapple_default_2ch_v1_01.wav')),
             'hook_pull':next((LIB/'audio').rglob('grapple_traverse_2ch_v1_01.wav')),
             'hook_release':next((LIB/'audio').rglob('grapple_retract_2ch_v1_01.wav')),
             'hook_ready':next((LIB/'audio').rglob('pilot_grapple_ready_2ch_v1_01.wav'))}
    retriever=LIB.parent/'retriever/sound/wpn/tomahawk'
    for index,p in enumerate(sorted((retriever/'imp').glob('tom_imp_*.wav'))):
        samples['axe_hit_'+str(index)]=p
    for index,p in enumerate(sorted((retriever/'throw').glob('tom_throw_*.wav'))):
        samples['axe_throw_'+str(index)]=p
    for name,pattern in {'axe_spin':'tom_spin.*.wav','axe_return':'tom_incoming.*.wav','axe_catch':'tom_catch.*.wav','axe_ready':'tomahawk_cooldown.*.wav'}.items():
        samples[name]=next(retriever.glob(pattern))
    with (ROOT/'sound/aliases/tod_expected_roster.csv').open(newline='') as f:
        reader=csv.DictReader(f);columns=reader.fieldnames;donor=next(r for r in reader if r['Name']=='hb_citadel_swing')
    aliases=[];audio=[]
    for name,src in samples.items():
        dest=sound/(name+'.wav')
        # Native positional sources must be mono PCM; preserve source levels.
        subprocess.run([str(ffmpeg),'-hide_banner','-loglevel','error','-y','-i',str(src),'-ac','1','-ar','48000','-c:a','pcm_s16le',str(dest)],check=True)
        alias='tod_archer_'+('axe_hit' if name.startswith('axe_hit_') else 'axe_throw' if name.startswith('axe_throw_') else name)
        row=dict(donor);row.update({'Name':alias,'FileSpec':str(dest.relative_to(ROOT/'sound_assets')).replace('/','\\'),'FileSpecSustain':'','FileSpecRelease':'','PanType':'3d','Pan':'default','Looping':'looping' if name in ('hook_pull','axe_spin') else 'nonlooping','VolMin':'75','VolMax':'75','DistMin':'80','DistMaxDry':'1800','DistMaxWet':'1800','EntityLimitCount':'2' if name.startswith('axe_hit_') else '1','EntityLimitType':'oldest','StopOnEntDeath':'yes','Storage':'loaded'})
        aliases.append(row)
        with wave.open(str(dest)) as w:seconds=w.getnframes()/w.getframerate()
        audio.append({'alias':row['Name'],'source':src.relative_to(ROOT).as_posix(),'file':dest.relative_to(ROOT).as_posix(),'seconds':seconds,'sha256':sha(dest)})
    alias=ROOT/'sound/aliases/tod_archer.csv'
    with alias.open('w',newline='') as f:
        writer=csv.DictWriter(f,columns);writer.writeheader();writer.writerows(aliases)
    (ART/'engine_kit/install_manifest.json').write_text(json.dumps({'models':models,'audio':audio,'textures':{p.relative_to(ROOT).as_posix():sha(p) for p in (OUT/'_images').glob('*.png')},'gdt_sha256':sha(gdt),'native_tested':False},indent=2))
    print('ARCHER_NATIVE_INSTALLED',len(models),'models;',len(audio),'audio cues; cable beam + HUD icon')

if __name__=='__main__':main()
