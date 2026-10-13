$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$py='C:\Users\jorda\Repositories\tower_of_doom_II_hellbound\tmp\gold_sword_env\Scripts\python.exe'
& $py -B (Join-Path $repo 'tools/dealer_boss/process_guard.py') --strict
if ($LASTEXITCODE -ne 0) { throw 'Preview waits for native stages or game to finish' }
$launchPath=Join-Path $repo 'tmp/dealer_boss_mcp/launch.json'
$owned=if (Test-Path $launchPath) { Get-Content $launchPath -Raw | ConvertFrom-Json } else { $null }
$previewProcess=if ($owned) { Get-Process -Id $owned.pid -ErrorAction SilentlyContinue } else { $null }
$identityValid=$false
if ($previewProcess -and $previewProcess.ProcessName -eq 'blender') {
    $command=Get-CimInstance Win32_Process -Filter "ProcessId=$($owned.pid)"
    $started=[DateTime]::Parse($owned.started_utc).ToUniversalTime()
    $identityValid=$command.CommandLine -like '*tools/dealer_boss/mcp_bootstrap.py*' -and [Math]::Abs(($previewProcess.StartTime.ToUniversalTime()-$started).TotalSeconds) -le 5
}
$listener=@(Get-NetTCPConnection -LocalPort 9899 -State Listen -ErrorAction SilentlyContinue)
if ($listener.Count -and (!$identityValid -or @($listener | Where-Object { $_.OwningProcess -ne $owned.pid }).Count)) { throw 'Dealer MCP port belongs to another process; refusing to touch it' }
if (!$identityValid) {
    & (Join-Path $repo 'tools/dealer_boss/start_studio.ps1')
    Start-Sleep -Seconds 8
}
$owned=Get-Content -LiteralPath $launchPath -Raw | ConvertFrom-Json
$listener=@(Get-NetTCPConnection -LocalPort 9899 -State Listen -ErrorAction SilentlyContinue)
if (!$listener.Count -or @($listener | Where-Object { $_.OwningProcess -ne $owned.pid }).Count) { throw 'Owned Dealer MCP listener is not ready' }
$savedPreference=$ErrorActionPreference
$ErrorActionPreference='Continue' # MCP writes routine server diagnostics to stderr.
& $py -B (Join-Path $repo 'tools/dealer_boss/mcp_call.py') (Join-Path $repo 'tools/dealer_boss/19_open_combat.py') 2> (Join-Path $repo 'tmp/dealer_combat_visible_mcp.err.log')
$mcpExit=$LASTEXITCODE
$ErrorActionPreference=$savedPreference
if ($mcpExit -ne 0) { throw 'Owned combat preview did not open' }
