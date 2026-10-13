"""Create memory-bounded preview copies; never alter original native 4K sheets."""
import pathlib,sys
from PIL import Image
sys.dont_write_bytecode=True
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from stage_bo6_machine import ROOT,STAGE,definitions
out=ROOT/'tmp/wunderfizz/assets/review';out.mkdir(parents=True,exist_ok=True)
count=0
for name,kind,fields,block in definitions((STAGE/'source_data/tod2_bo6_wunderfizz.gdt').read_text()):
    if kind!='image':continue
    with Image.open(STAGE/fields['baseImage']) as im:im.resize((1024,1024),Image.Resampling.LANCZOS).save(out/(name+'.png'))
    count+=1
print('BO6 preview copies:',count,'original sheets untouched')
