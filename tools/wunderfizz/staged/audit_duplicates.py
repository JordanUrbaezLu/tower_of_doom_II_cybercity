"""Read-only exact definition-owner audit of private and shared GDT source roots."""
from pathlib import Path
import json, subprocess, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from stage_bo6_machine import ROOT,STAGE,definitions
def main():
    import re
    names=sorted(set(name for name,kind,fields,block in definitions((STAGE/'source_data/tod2_bo6_wunderfizz.gdt').read_text())))
    pattern=r'^\s*"(?:'+'|'.join(re.escape(n) for n in names)+r')"\s*\(\s*"[^"\n]+\.gdf"\s*\)'
    rows=[]
    for owner,path in [('private',Path('C:/BO3Tools/TOD2Cybercity/source_data')),
                       ('shared_read_only',Path('C:/Program Files (x86)/Steam/steamapps/common/Call of Duty Black Ops III 455130/source_data')),
                       ('repository',ROOT/'source_data')]:
        run=subprocess.run(['rg','--json',pattern,str(path)],capture_output=True,text=True)
        assert run.returncode in (0,1),(owner,run.stderr)
        matches=[]
        for line in run.stdout.splitlines():
            item=json.loads(line)
            if item['type']=='match':matches.append({'path':item['data']['path']['text'],'line':item['data']['line_number'],'definition':item['data']['lines']['text'].strip()})
        rows.append({'scope':owner,'root':str(path),'duplicates':matches,'count':len(matches)})
    receipt={'requested_exact_names':names,'searches':rows,'all_unambiguous':all(r['count']==0 for r in rows),'writes':'This receipt only; all source/database/cache roots read-only.'}
    (ROOT/'tmp/wunderfizz/assets/duplicate_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
