"""Read-only donor helpers and map-owned output paths."""
import hashlib,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/cyber_sword';KIT=ART/'engine_kit'
OUT=ROOT/'model_export/tod_warrior/cyber_sword'
DONOR=Path('C:/BO3Tools/TOD2Cybercity/model_export/hb/gold_sword/hb_gold_sword.XMODEL_BIN')
sys.path.insert(0,str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/4.2/scripts/addons/BetterBetterBlenderCOD'))
from PyCoD import xmodel
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
    text=p.read_text(encoding='utf-8-sig')
    return {m[1]:(m[2],dict(re.findall(r'"([^"\r\n]+)"\s*"([^"\r\n]*)"',m[3]))) for m in re.finditer(r'"([^"\n]+)"\s*\(\s*"([^"\n]+)"\s*\)\s*\{([^}]+)\}',text)}
def block(name,kind,fields):
    return '\t"'+name+'" ( "'+kind+'" )\n\t{\n'+''.join('\t\t"'+k+'" "'+str(v)+'"\n' for k,v in fields.items())+'\t}\n'
def load(p):
    m=xmodel.Model();m.LoadFile_Bin(str(p),split_meshes=True);return m
