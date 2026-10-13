"""Land the reviewed complete candidate only between builds. No sync or deployment."""
import datetime
import hashlib
import json
import pathlib
import subprocess

ROOT=pathlib.Path(__file__).resolve().parents[2]
STAGE=ROOT/'tmp/dealer_combat_stage'
PIN=STAGE/'inputs.json'


def main():
    scan="Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(BlackOps3|Radiant|cod2map|linker_modtools|gdtdb)' -or ($_.Name -match '^(powershell|pwsh)' -and $_.CommandLine -match ' -File (?:[^ ]*[\\\\/])?build_map.ps1') } | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    r=subprocess.run(['powershell','-NoProfile','-Command',scan],capture_output=True,text=True,check=True)
    assert not r.stdout.strip(),'Live build/native process: '+r.stdout
    pins=json.loads(PIN.read_text())
    files=set(pins)
    for folder in ('share/raw/fx/tod/dealer_combat','sound_assets/tod/dealer_combat','xanim_export/tod_dealer'):
        files.update(p.relative_to(STAGE).as_posix() for p in (STAGE/folder).iterdir() if p.is_file())
    files.update(('sound/aliases/tod_dealer_combat.csv','source_data/tod_dealer_combat.gdt'))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    for rel,pin in pins.items():
        assert sha((ROOT/rel).read_bytes())==pin['before'],'Peer changed original: '+rel
        assert sha((STAGE/rel).read_bytes())==pin['after'],'Candidate changed: '+rel
    for rel in files-set(pins):
        assert not (ROOT/rel).exists(),'New asset already exists: '+rel
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup=ROOT/'art/dealer_combat/landing'/stamp
    hashes={}
    for rel in sorted(files):
        target=ROOT/rel
        if target.exists():
            old=backup/rel;old.parent.mkdir(parents=True,exist_ok=True);old.write_bytes(target.read_bytes())
        data=(STAGE/rel).read_bytes()
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        hashes[rel]=sha(data)
    proof=ROOT/'art/dealer_combat/landing.json'
    proof.write_text(json.dumps(dict(timestamp=stamp,backup=backup.relative_to(ROOT).as_posix(),files=hashes),indent=2))
    print('DEALER COMBAT LANDED:',len(files),'inputs; all shared originals matched; no deployment')


if __name__=='__main__':main()
