"""Read-only post-FULL-build proof; no claim of native visual or decoded BSP-UV parity.

python -B tools/dealer_presence/verify_native.py --build-snapshot <sky build_inputs.json> --build-log <full.log>
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,re,sqlite3,subprocess,time
ROOT=Path(__file__).resolve().parents[2];MT=Path('C:/BO3Tools/TOD2Cybercity');MAP='zm_tod2_cybercity';DEP=MT/'usermaps'/MAP
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fields(text,name):
    m=re.search(r'"'+re.escape(name)+r'"\s*\(\s*"\w+\.gdf"\s*\)\s*\{([^}]+)\}',text)
    assert m,name
    return dict(re.findall(r'"([^"\r\n]+)"\s*"([^"\r\n]*)"',m[1]))
p=argparse.ArgumentParser();p.add_argument('--build-snapshot',required=True);p.add_argument('--build-log',required=True);p.add_argument('--output');args=p.parse_args()
subprocess.run(['python','-B','tools/dealer_presence/verify.py','--check'],cwd=ROOT,check=True)
snapshot=json.loads((ROOT/args.build_snapshot).read_text(encoding='utf-8'));captured=snapshot['captured_ns']
logpath=ROOT/args.build_log;raw=logpath.read_bytes();log=raw.decode('utf-16') if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else raw.decode('utf-8-sig',errors='replace')
assert '[build] === BUILD OK ===' in log and '[build] mode = FULL geometry' in log
ff=DEP/'zone'/f'{MAP}.ff';ffns=ff.stat().st_mtime_ns;assert ffns>captured
assert ffns<=logpath.stat().st_mtime_ns<=ffns+1800*10**9,'Build log is outside current fastfile interval'
inputs={}
for name in ['source_data/tod_dealer_presence.gdt','model_export/tod_dealer_presence/_images/i_tod_dealer_surveillance.png',f'map_source/zm/{MAP}.map',f'zone_source/{MAP}.zone']:
    source=ROOT/name;dest=(DEP if name.startswith('zone_source/') else MT)/name
    assert name in snapshot['inputs'],('Combined snapshot missing Dealer input',name)
    assert sha(source)==snapshot['inputs'][name]['sha256']==sha(dest),name
    assert dest.stat().st_mtime_ns<=ffns
    inputs[name]=sha(source)
ledger=DEP/'zone_source/all/assetinfo'/f'{MAP}.csv';assert captured<ledger.stat().st_mtime_ns<=ffns+5*10**9
with ledger.open(encoding='utf-8-sig',newline='') as f:assets={(r['type'],re.sub(r'#[0-9a-fA-F]+$','',r['name'].strip()).lower().replace('\\','/')) for r in csv.DictReader(f)}
assert ('material','wc/mtl_tod_dealer_surveillance') in assets,'Missing compiled world screen material'
assert ('image','i_tod_dealer_surveillance') in assets,'Missing compiled portrait image'
gdt=(ROOT/'source_data/tod_dealer_presence.gdt').read_text();bindings={}
with sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro',uri=True) as con:
    con.execute('pragma writable_schema=ON');con.row_factory=sqlite3.Row
    for kind,name,keys in [('material','mtl_tod_dealer_surveillance',['materialType','colorMap','colorMap00','scaleRGB','colorTint','colorTint1']),('image','i_tod_dealer_surveillance',['baseImage','coreSemantic','noMipMaps','noPicMip'])]:
        row=con.execute('select * from '+kind+' where _name=?',(name,)).fetchone();assert row,name
        expected=fields(gdt,name)
        for key in keys:
            a,b=expected[key],str(row[key])
            if key in ('scaleRGB','noMipMaps','noPicMip'):same=math.isclose(float(a),float(b),abs_tol=1e-6)
            elif key in ('colorTint','colorTint1'):same=all(math.isclose(float(x),float(y),abs_tol=1e-6) for x,y in zip(a.split(),b.split()))
            else:same=re.sub(r'\\+','/',a)==re.sub(r'\\+','/',b)
            assert same,(name,key,a,b)
        bindings[name]={key:row[key] for key in keys}
rawmap=MT/'share/raw/maps/zm';geompath=rawmap/f'{MAP}.geomkey.json';geom=json.loads(geompath.read_text())
assert captured<geompath.stat().st_mtime_ns<=ffns
parts={k.replace('\\','/'):v for k,v in geom['parts'].items()}
assert parts['map:map_source/zm/'+MAP+'.map']==hashlib.sha1((MT/f'map_source/zm/{MAP}.map').read_bytes()).hexdigest()
compiled={}
for ext in ('d3dbsp','led'):
    file=rawmap/f'{MAP}.{ext}';assert captured<file.stat().st_mtime_ns<=ffns
    assert geom['outputs'][file.name]==hashlib.sha1(file.read_bytes()).hexdigest()
    compiled[ext]=sha(file)
report={'schema':1,'verified_ns':time.time_ns(),'inputs':inputs,'native_bindings':bindings,'fresh_compiled_world':compiled,
 'source_geometry':'Three reviewed noncolliding wall panels; 84 triangles; UVs, normals and support corners validated before compile.',
 'proof_limit':'Fresh BSP/LED consumed exact reviewed map; packed world material and image verified. Compiled BSP vertex UVs are not decoded; native visibility/appearance awaits user playtest.',
 'native_visual_verified':False,'game_launched':False}
if args.output:(ROOT/args.output).write_text(json.dumps(report,indent=2)+'\n')
print('DEALER_PRESENCE_NATIVE_OK: fresh consumed map+BSP/LED; wc material+image packed; deployed hashes and native .65 bindings current; native appearance UNPLAYED')
