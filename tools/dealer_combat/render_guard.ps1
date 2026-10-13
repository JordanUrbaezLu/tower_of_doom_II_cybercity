param([int]$OwnedBlenderPid, [string]$ResultLog)
$ErrorActionPreference='Stop'
$launch=Get-Content -LiteralPath 'tmp/dealer_boss_mcp/launch.json' -Raw | ConvertFrom-Json
if ($launch.pid -ne $OwnedBlenderPid) { throw 'Not the owned Dealer studio' }
$deadline=[DateTime]::UtcNow.AddMinutes(8)
while ([DateTime]::UtcNow -lt $deadline) {
    $tail=Get-Content -LiteralPath $ResultLog -Tail 8 -ErrorAction SilentlyContinue
    if ($tail -match '^Code executed successfully:|^Error executing code:') { Write-Output 'Render finished'; exit 0 }
    $native=@(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(Radiant|BlackOps3|cod2map|linker_modtools|gdtdb)' })
    if ($native.Count -gt 0) {
        Stop-Process -Id $OwnedBlenderPid -ErrorAction SilentlyContinue
        Write-Output ('Stopped ONLY owned render '+$OwnedBlenderPid+' for '+(($native.ProcessName)-join ','))
        exit 1
    }
    Start-Sleep -Seconds 1
}
throw 'Render guard timed out; inspect the owned studio'
