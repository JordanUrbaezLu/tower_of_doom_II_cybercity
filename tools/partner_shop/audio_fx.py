"""Make bounded electrical transients and native mesh particles from authored art."""
import json,csv,hashlib,shutil,subprocess,re,wave,array,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/'art/partner_shop';OUT=ROOT/'sound_assets/tod/shop';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path.home()/'Downloads/freesound_community-electricity-sound-6066.wav'
original=ART/'references/electricity-sound-6066.wav'
if not original.exists():shutil.copyfile(SOURCE,original)
with wave.open(str(original),'rb') as w:
    rate=w.getframerate();channels=w.getnchannels();data=array.array('h',w.readframes(w.getnframes()))
mono=[sum(data[i:i+channels])/channels for i in range(0,len(data),channels)]
# Highest-energy short bursts, separated enough to avoid three identical samples.
window=int(rate*.04);scores=[(sum(v*v for v in mono[i:i+window]),i/rate) for i in range(0,len(mono)-window,int(rate*.02))]
chosen=[]
for score,pos in sorted(scores,reverse=True):
    start=max(0,pos-.012)
    if all(abs(start-p)>.45 for p in chosen):chosen.append(start)
    if len(chosen)==3:break
records=[]
for i,(start,duration) in enumerate(zip(chosen,(.17,.23,.31))):
    file=OUT/('spark_'+str(i+1)+'.wav')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(original),'-t',str(duration),'-af',f'atrim=duration={duration},afade=t=in:d=0.002,afade=t=out:st={duration-.035}:d=0.035,alimiter=limit=0.8:level=false:latency=true','-ac','1','-ar','48000','-c:a','pcm_s16le',str(file)],check=True)
    records.append({'file':file.relative_to(ROOT).as_posix(),'source_start':start,'seconds':duration,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
with (ROOT/'sound/aliases/tod_ui.csv').open(newline='',encoding='utf-8-sig') as f:
    reader=csv.DictReader(f);header=reader.fieldnames;donor=next(r for r in reader if r['Name']=='tod_secret_laugh')
with (ROOT/'sound/aliases/tod_shop.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=header);writer.writeheader()
    for i in range(3):
        row=dict(donor);row.update(Name='tod_shop_spark_'+str(i+1),FileSpec='tod\\shop\\spark_'+str(i+1)+'.wav',VolMin='72',VolMax='72',DistMin='80',DistMaxDry='600',DistMaxWet='700',LimitCount='4',LimitType='oldest',EntityLimitCount='2',EntityLimitType='oldest',PitchMin='0',PitchMax='0',Bus='bus_fx',Pauseable='yes',StopOnEntDeath='yes',PanType='3d',Storage='loaded');writer.writerow(row)
szc=ROOT/'sound/zoneconfig/zm_tod2_cybercity.szc';config=json.loads(szc.read_text(encoding='utf-8-sig'))
if not any(r.get('Name')=='tod_shop' for r in config['Sources']):config['Sources'].append({'Type':'ALIAS','Name':'tod_shop','Filename':'tod_shop.csv','Specs':[]})
szc.write_text(json.dumps(config,indent=1,separators=(',', ' : '))+'\n')
# Both native elements use mesh art exported from the Blender master.
sys.path.insert(0,str(ROOT/'tools/teleporter'));from generate_fx import field,graph,common,FLAT
donor=(ROOT/'share/raw/fx/acc/light/fx_perk_glow_amber.efx').read_text();head,*raw=re.split(r'\n\{\n\tname "',donor);blocks={b.split('"')[0]:'\n{\n\tname "'+b for b in raw}
template=blocks['glow'];fx=[]
for kind,life,count in [('arc',115,1),('spark',310,5)]:
    b=common(template,'shop_'+kind,0,life,6000,(1,1,1));b=field(b,'editorFlags','');b=field(b,'spawnOneShot',str(count)+' 0');b=field(b,'spawnRange','0 1500');b=field(b,'fadeOutRange','1000 500');b=field(b,'spawnFrustumCullRadius',24)
    b=field(b,'flags','spawnRelative spawnOffsetNone runRelToSpawn nonUniformScale');b=b.replace('\tbillboardSprite\n','\tmodel\n').replace('"gfx_light_phosphorous_em"','"tod_shop_'+kind+'"')
    b=graph(b,'sizeGraph0',1,FLAT);b=graph(b,'sizeGraph1',1,FLAT)
    b=graph(b,'scaleGraph',1,[(0,1),(.65,1),(1,0)])
    if kind=='spark':
        b=field(b,'gravity','40 0')
        for axis,speed,lo,hi in [('X',24,-1,1),('Y',18,-1,-.3),('Z',16,.15,1)]:
            value=f'\tvelGraph0{axis} {speed}\n\t{{\n\t\t{{\n\t\t\t0 {lo}\n\t\t\t1 {lo}\n\t\t}}\n\t\t{{\n\t\t\t0 {hi}\n\t\t\t1 {hi}\n\t\t}}\n\t}};'
            b=re.sub(r'(?m)^\tvelGraph0'+axis+r'\s+[^;]*;',lambda _:value,b,count=1)
        b=field(b,'editorFlags','useRandVel0');b=field(b,'initialRot','0 360')
    fx.append(b)
head=field(head,'efBoundingBoxMin','-24 -24 -24');head=field(head,'efBoundingBoxMax','24 24 24')
dest=ROOT/'share/raw/fx/tod/shop';dest.mkdir(parents=True,exist_ok=True);(dest/'fx_tod_shop_spark.efx').write_text(head+'\n'+'\n'.join(fx))
timing=json.loads((ART/'electrical_timing.json').read_text());events=sorted(timing['events'],key=lambda e:e[2]);lines=['#namespace tod_shop_timing;','// Generated from the authored Blender electrical timeline.']
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
(ROOT/'scripts/zm/zm_tod2_cybercity/_tod_shop_timing.csc').write_text('\n'.join(lines)+'\n')
# A sample-accurate reference mix uses the exact same burst start times as native FX.
mix=[0.0]*(48000*6)
for event in audio_events:
    f=event['frame']
    with wave.open(str(OUT/(event['sound'].replace('tod_shop_','')+'.wav')),'rb') as w:samples=array.array('h',w.readframes(w.getnframes()))
    offset=round((f-1)*48000/30)
    for j,v in enumerate(samples):
        if offset+j<len(mix):mix[offset+j]+=v*.7
with wave.open(str(ART/'electrical_preview.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(array.array('h',(round(max(-32767,min(32767,v))) for v in mix)).tobytes())
(ART/'audio_manifest.json').write_text(json.dumps({'source':str(original.relative_to(ROOT)),'source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'samples':records,'events':events,'audio_events':audio_events,'sync':'One sound per simultaneous fault cluster; same client callback and shared 30-fps server-time clock as sign/FX. Zero random pitch/start delay.','native_playtested':False},indent=2))
print('SHOP_AUDIO_FX_AUTHORED',len(records),'samples;',len(events),'synchronized bursts; 2 mesh emitters, 6 particles maximum per event')
