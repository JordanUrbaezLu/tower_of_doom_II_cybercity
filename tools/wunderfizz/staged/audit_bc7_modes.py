import json,math,struct,sys
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/wunderfizz'))
from verify_compiled_assets import TOOLS,MAP,module,dependency_sections,selected_image
reader=module('wf_bc7_mode_reader','tools/crown_alarm/verify_lens_conversion.py')
file=selected_image(dependency_sections(TOOLS/'usermaps'/MAP/'zone_source/all/assetinfo'/(MAP+'.deps')),'i_t10_zm_machine_wunderfizz_glass_c')
raw=reader.decode_lz4(file.read_bytes());end=len(raw);rows=[]
with Image.open(ROOT/'model_export/tod2_bo6_wunderfizz/_images/t10_zm_machine_wunderfizz_glass/t10_zm_machine_wunderfizz_glass_c.png') as im:source=im.convert('RGBA').copy()
for level in range(13):
    w=max(1,4096>>level);size=math.ceil(w/4)**2*16;data=raw[end-size:end];end-=size
    modes=Counter((data[i]&-data[i]).bit_length()-1 for i in range(0,len(data),16))
    actual=reader.decode_bc7(data,w,w);expected=np.asarray(source.resize((w,w),Image.Resampling.BOX))
    row={'level':level,'size':w,'mode_counts':dict(modes)}
    if w<=4:row.update(source_rgba=expected.tolist(),native_rgba=actual.tolist(),encoded_block_hex=data.hex())
    rows.append(row);print(level,w,dict(modes),flush=True)
out=ROOT/'tmp/wunderfizz/assets/bc7_mode_audit.json';out.write_text(json.dumps(rows,indent=2)+'\n');print(out)
