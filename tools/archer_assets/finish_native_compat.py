"""Use BO3's sound-note actions and vendor the charge ring's original texture."""
import sys,re,json,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/archer_assets'))
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xanim
from install_native import block
p=ROOT/'xanim_export/tod_archer/tod_archer_flourish.xanim_bin'
a=xanim.Anim();a.LoadFile_Bin(str(p));a.notes=[]
raw=p.with_suffix('.XANIM_EXPORT');a.WriteFile_Raw(str(raw));raw.write_text(raw.read_text().split('NOTETRACKS')[0]+'NUMKEYS 0\n')
result=subprocess.run(['C:/BO3Tools/TOD2Cybercity/bin/export2bin.exe',raw.name],cwd=p.parent,capture_output=True,text=True,timeout=120)
(ROOT/'tmp/archer_assets/flourish_export2bin.log').write_text(result.stdout+'\n'+result.stderr)
if result.returncode:raise RuntimeError(result.stdout+result.stderr)
gdt=ROOT/'source_data/tod_archer_motion.gdt';s=gdt.read_text().replace('"translationQuality"','"translationError"').replace('"rotationQuality"','"angleError"')
m=re.search(r'"tod_archer_flourish"\s*\(\s*"xanim.gdf"\s*\)\s*\{([^}]+)\}',s)
fields=dict(re.findall(r'"([^"\n]+)"\s+"([^"\n]*)"',m[1]))
fields.update({'customnote0action':'2D Sound','customnote0actionparam1':'tod_archer_axe_first_raise','customnote0actionparam2':'','customnote0frame':0,'customnote0useexistingnote':''})
gdt.write_text(s[:m.start()]+block('tod_archer_flourish','xanim',fields).strip()+s[m.end():])
source=Path('C:/BO3Tools/TOD2Cybercity/texture_assets/black_ops_2/effect/i_fxt_fx_emp_ring_wave.tiff')
destination=ROOT/'model_export/tod_archer/_images/i_tod_archer_charge_ring.tiff';shutil.copy2(source,destination)
blocks=[block('i_tod_archer_charge_ring','image',{'baseImage':destination.relative_to(ROOT).as_posix(),'imageType':'Texture','semantic':'effectMap','coreSemantic':'sRGB3chAlpha','streamable':0,'compressionMethod':'compressed high color'}),block('mtl_tod_archer_charge_ring','material',{'materialCategory':'Effect','materialType':'effect_lit_emissive_add','template':'material.template','surfaceType':'<none>','colorMap':'i_tod_archer_charge_ring','colorTint':'1 1 1 1','scaleRGB':1,'textureAtlasRowCount':1,'textureAtlasColumnCount':1,'cullFace':'None','usage':'<not in editor>'})]
(ROOT/'source_data/tod_archer_charge.gdt').write_text('{\n'+''.join(blocks)+'}\n')
path=ROOT/'art/archer_assets/engine_kit/native_motion.json';data=json.loads(path.read_text())
for rec in data['animations']:
    if rec['asset']=='tod_archer_flourish':rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();rec['sound_note']='native GDT 2D Sound at original frame 0'
path.write_text(json.dumps(data,indent=2)+'\n')
print('NATIVE_COMPAT official flourish binary, executable frame-0 sound action, original charge ring texture')
