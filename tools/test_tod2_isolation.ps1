$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'tod2_workspace.ps1')
function Must-Reject($Action, $Label) {
    $rejected = $false
    try { & $Action } catch { $rejected = $true }
    if (-not $rejected) { throw "Isolation guard accepted $Label" }
    Write-Host "PASS: rejected $Label"
}
$null = Resolve-Tod2Root
Must-Reject { Resolve-Tod2Root 'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130' } 'shared tools override'
Must-Reject { Assert-Tod2WritePath (Join-Path $script:Tod2Repo '..\tower_of_doom_cybercity\sentinel') -Repository } 'Map One repository write'
Must-Reject { Assert-Tod2WritePath (Join-Path $script:Tod2Root '..\MapOne\sentinel') } 'parent traversal'
$sourceLink = Get-ChildItem (Join-Path $script:Tod2Root 'model_export') -Attributes ReparsePoint | Select-Object -First 1
if (-not $sourceLink) { throw 'Expected stock-input reference for guard test.' }
Must-Reject { Assert-Tod2WritePath (Join-Path $sourceLink.FullName 'sentinel') } 'write through stock-input junction'
Must-Reject { Assert-Tod2WritePath (Join-Path $script:Tod2Root 'model_export') -Tree } 'tree copy containing stock junctions'
Assert-Tod2WritePath (Join-Path $script:Tod2Root 'model_export\tod_teleporter') -Tree
Assert-Tod2WritePath (Join-Path $script:Tod2Root 'usermaps\zm_tod2_cybercity') -Tree
$userEnv = [Environment]::GetEnvironmentVariable('TA_GAME_PATH','User')
Set-Tod2ProcessEnvironment
if ($env:TA_GAME_PATH -ne ($script:Tod2Root + '\')) { throw 'Compiler environment not private.' }
if ([Environment]::GetEnvironmentVariable('TA_GAME_PATH','User') -ne $userEnv) { throw 'User environment changed.' }
$workshop = Get-Content (Join-Path $script:Tod2Repo 'zone\workshop.json') -Raw | ConvertFrom-Json
if ($workshop.FolderName -ne $script:Tod2Map -or $workshop.PublisherID) { throw 'Inherited Workshop identity.' }
Write-Host 'TOD II ISOLATION PASS: map ownership, path traversal, junction writes, process environment and Workshop identity.'
