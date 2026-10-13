$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $repo 'tools/sky_depth/resource_guard.ps1')
Assert-SkyResourceSlot 'Wunderfizz exact-import MCP review'
$available=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024
if ($available -lt 2GB) { throw "Wunderfizz review waits: only $available physical bytes free." }
$others=@(Get-CimInstance Win32_Process -Filter "Name='blender.exe'")
if (@($others | Where-Object { $_.CommandLine -match '--background|--render-frame|--render-anim|\s-f\s|\s-a\s' }).Count) { throw 'Another Blender render is active; no studio launched.' }
$samples=@{}
foreach ($other in $others) { $samples[$other.ProcessId]=(Get-Process -Id $other.ProcessId -ErrorAction Stop).CPU }
Start-Sleep -Seconds 2
foreach ($other in $others) {
    $current=Get-Process -Id $other.ProcessId -ErrorAction SilentlyContinue
    if ($current -and $current.CPU-$samples[$other.ProcessId] -gt 1) { throw "Another Blender workload is active: PID $($other.ProcessId)." }
}
$env:PYTHONDONTWRITEBYTECODE='1'
$studio=Start-Process -FilePath 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -ArgumentList @('--factory-startup','--python','tools/wunderfizz/staged/mcp_bootstrap.py') -WorkingDirectory $repo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $repo 'tmp/wunderfizz/assets/studio.log') -RedirectStandardError (Join-Path $repo 'tmp/wunderfizz/assets/studio.err') -PassThru
$watch=Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $PSScriptRoot 'watch_studio.ps1'),'-OwnedProcessId',$studio.Id,'-StartFileTime',$studio.StartTime.ToFileTimeUtc()) -WindowStyle Hidden -PassThru
[pscustomobject]@{pid=$studio.Id;start_filetime=$studio.StartTime.ToFileTimeUtc();watcher=$watch.Id;port=9912;other_blenders_untouched=@($others.ProcessId);free_physical_bytes_before=$available} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $repo 'tmp/wunderfizz/assets/studio_process.json')
Get-Content -LiteralPath (Join-Path $repo 'tmp/wunderfizz/assets/studio_process.json')
