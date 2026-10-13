"""Regenerate ONLY the client timing script and the audio manifest's event sites.

audio_fx.py makes the spark WAVs, the alias CSV, the zone sound config, the spark
.efx, this timing script and the preview mix in one pass. When only where a spark
happens moves (18_black_market_sign.py moved the sign sparks with their letters),
the WAVs, aliases, efx and mix do not change, so this writes just the two files
that name positions: scripts/.../_tod_shop_timing.csc (same generator as
audio_fx.py, byte for byte) and art/partner_shop/audio_manifest.json events.
Run with plain Python after 18 + 14. --check exits 1 if either file is stale.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop'
CSC=ROOT/'scripts/zm/zm_tod2_cybercity/_tod_shop_timing.csc';MANIFEST=ART/'audio_manifest.json'
timing=json.loads((ART/'electrical_timing.json').read_text())
events=sorted(timing['events'],key=lambda e:e[2])   # stable: the sign event stays first in its frame
lines=['#namespace tod_shop_timing;','// Generated from the authored Blender electrical timeline.']
lines+=['function power_bus( frame )','{','    v = 1;']
for f,v in timing['power_bus']:lines.append('    if ( frame >= '+str(f)+' ) v = '+str(v)+';')
lines+=['    return v;','}','function letter( kind, frame )','{','    return power_bus( frame );','}']
lines+=['function events()','{','    a = [];']
audio_events=[];seen=set()
for i,(name,org,f) in enumerate(events):
    sound=''
    if f not in seen:
        sound='tod_shop_spark_'+str(len(seen)%3+1);audio_events.append({'frame':f,'sound':sound,'org':org});seen.add(f)
    lines+=['    a[ '+str(i)+' ] = SpawnStruct();','    a[ '+str(i)+' ].frame = '+str(f)+';','    a[ '+str(i)+' ].org = ( '+', '.join(map(str,org))+' );','    a[ '+str(i)+' ].site = "'+name+'";','    a[ '+str(i)+' ].sound = "'+sound+'";']
lines+=['    return a;','}']
csc='\n'.join(lines)+'\n'
manifest=json.loads(MANIFEST.read_text());manifest['events']=events;manifest['audio_events']=audio_events
text=json.dumps(manifest,indent=2)
if '--check' in sys.argv:
    stale=[str(p.relative_to(ROOT)) for p,want in ((CSC,csc),(MANIFEST,text)) if p.read_text()!=want]
    print('SHOP_TIMING '+('STALE: '+', '.join(stale) if stale else 'OK'));sys.exit(1 if stale else 0)
CSC.write_text(csc);MANIFEST.write_text(text)
print('SHOP_TIMING_WRITTEN',len(events),'events;',', '.join(e['sound']+'@'+str(e['frame'])+' '+next(n for n,o,f in events if f==e['frame']) for e in audio_events))
