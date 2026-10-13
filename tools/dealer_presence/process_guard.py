"""Read-only broad native-editor/compiler guard, used before studio/render work."""
import json,subprocess,sys
def blockers(include_blender=False):
    command="Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Radiant*' -or $_.ProcessName -like 'BlackOps3*' -or $_.ProcessName -like 'cod2map*' -or $_.ProcessName -like 'linker*' -or $_.ProcessName -like 'gdtdb*' } | Select-Object Id,ProcessName | ConvertTo-Json -Compress"
    if include_blender:command=command.replace("-like 'gdtdb*'", "-like 'gdtdb*' -or $_.ProcessName -like 'blender*'")
    r=subprocess.run(['powershell','-NoProfile','-Command',command],capture_output=True,text=True,check=True)
    result=json.loads(r.stdout) if r.stdout.strip() else []
    return result if isinstance(result,list) else [result]
def check(include_blender=False):
    running=blockers(include_blender)
    if running:raise RuntimeError('Dealer studio/render held for active native process: '+json.dumps(running))
    return True
if __name__=='__main__':check(include_blender='--launch' in sys.argv);print('DEALER_PROCESS_GUARD_CLEAR')
