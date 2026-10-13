"""Record this pass's synthetic classifier and real no-launch preflight evidence."""
import datetime
import json
import pathlib
import subprocess
from pass_config import ROOT, REVIEW, sha

def run(name, *args):
    result = subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',
                             str(pathlib.Path(__file__).with_name(name)), *args],
                            cwd=ROOT, capture_output=True, text=True, timeout=30)
    return dict(exit_code=result.returncode, stdout=result.stdout.strip(), stderr=result.stderr.strip())

classifier = run('test_resource_guard.ps1')
assert classifier['exit_code'] == 0, classifier
tested = json.loads(classifier['stdout'])
assert tested['status'] == 'pass' and tested['os_processes_created_or_stopped'] == 0
preflight = run('render.ps1', '-CheckOnly')
assert (preflight['exit_code'] == 0 and 'CheckOnly never launches Blender' in preflight['stdout']) or (
    preflight['exit_code'] != 0 and any(phrase in preflight['stderr'] for phrase in
                                     ('Another Blender is open', 'game/editor/native build stage running'))), preflight
files = {p.relative_to(ROOT).as_posix():sha(p) for p in (pathlib.Path(__file__).parent/name for name in
         ('resource_guard.ps1','test_resource_guard.ps1','watch_studio.ps1','render.ps1','start_studio.ps1',
          'open_preview.ps1','finish.ps1','render_native_card.ps1','review_quality.ps1','mcp_call.py'))}
report = dict(schema=1, pass_name='sky_depth_v13', recorded=datetime.datetime.now().astimezone().isoformat(),
              classifier=tested, live_check_only=preflight, source_hashes=files,
              heavy_processes_started_or_stopped=0,
              limitations='Synthetic classification proves naming/ownership decisions. Live CheckOnly proves the current refusal or free slot only; no real process was terminated. Overlap is possible memory pressure, not a proved historical Radiant cause.')
(REVIEW/'resource_guard.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
radiant = dict(schema=1, pass_name='sky_depth_v13', recorded=report['recorded'],
               tested_names=[v for v in tested['cases'] if 'Radiant' in v['name']],
               source_hashes=files, live_check_only=preflight,
               note='Current-pass synthetic Radiant classifier coverage. The live CheckOnly result records only the processes actually observed now; it is not represented as a live Radiant refusal.')
(REVIEW/'radiant_guard.json').write_text(json.dumps(radiant,indent=2)+'\n',encoding='utf-8')
print('DEPTH GUARDS RECORDED: classifier passed; live preflight exit',preflight['exit_code'],'; no heavy process launched/stopped')
