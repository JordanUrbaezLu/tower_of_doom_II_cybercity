# One-time private compiler/database/cache setup. Stock geometry and texture
# directories are input references only; all writable sources are real copies.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'tod2_workspace.ps1')
$donor = 'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III 455130'
if (Get-Process BlackOps3,linker_modtools,cod2map64,Radiant_modtools -ErrorAction SilentlyContinue) {
    throw 'Close the game / wait for the active build before workspace setup.'
}
if (-not (Test-Path -LiteralPath (Join-Path $donor 'bin\linker_modtools.exe'))) { throw 'Stock Mod Tools not found.' }
$marker = Join-Path $script:Tod2Root '.tod2-workspace.json'
if (Test-Path -LiteralPath $marker) {
    $null = Resolve-Tod2Root
    Write-Host 'TOD II workspace already initialized; no donor sources recopied.'
    exit 0
}
New-Item -ItemType Directory -Path $script:Tod2Root -Force | Out-Null
Assert-Tod2WritePath $script:Tod2Root
function Copy-PrivateTree($rel) {
    $src = Join-Path $donor $rel
    $dst = Join-Path $script:Tod2Root $rel
    if (-not (Test-Path -LiteralPath $src)) { return }
    Assert-Tod2WritePath $dst -Tree
    Write-Host "[TOD2 setup] physical copy: $rel"
    # GDT databases contain absolute source paths. Build a new one locally.
    & robocopy $src $dst /E /XJ /MT:8 /NFL /NDL /NJH /NJS /NP /R:1 /W:1 /XF gdt.db gdt.db-wal gdt.db-shm
    if ($LASTEXITCODE -ge 8) { throw "Copy failed: $rel" }
}
foreach ($rel in @('bin','gdtdb','archetypes','deffiles','map_source','pc','radiant','rex','share\raw','share\zone_source','sound','sound_assets','source_data','sw4','xanim_export','zone_source','win64')) {
    Copy-PrivateTree $rel
}
foreach ($rel in @('share\assetconvert','usermaps','zone')) {
    New-Item -ItemType Directory -Path (Join-Path $script:Tod2Root $rel) -Force | Out-Null
}
# This installed toolchain lacks HLSL needed to regenerate these stock shaders.
# Physical private copies are required even when model/image caches start empty.
foreach ($rel in @('share\assetconvert\ToolsGfx\shaders_modtools','share\assetconvert\shaders','share\assetconvert\preshader')) {
    Copy-PrivateTree $rel
}
# Model/texture libraries exceed 84 GB. Reference installed immutable inputs;
# materialize every repo-owned model directory before sync. Never hardlink.
foreach ($rel in @('model_export','texture_assets','art_assets','_custom')) {
    $dst = Join-Path $script:Tod2Root $rel
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
    foreach ($item in Get-ChildItem -LiteralPath (Join-Path $donor $rel)) {
        $target = Join-Path $dst $item.Name
        if (Test-Path -LiteralPath $target) { continue }
        if ($item.PSIsContainer -and -not (Test-Path -LiteralPath (Join-Path $script:Tod2Repo "$rel\$($item.Name)"))) {
            New-Item -ItemType Junction -Path $target -Target $item.FullName | Out-Null
        } elseif ($item.PSIsContainer) {
            Copy-PrivateTree "$rel\$($item.Name)"
        } else { Copy-Item -LiteralPath $item.FullName -Destination $target }
    }
}
# Root config files only, never run the donor's machine-wide setenv script.
foreach ($name in @('steam_appid.txt','AssetFileList.csv')) {
    if (Test-Path -LiteralPath (Join-Path $donor $name)) {
        Copy-Item -LiteralPath (Join-Path $donor $name) -Destination (Join-Path $script:Tod2Root $name)
    }
}
@{ map=$script:Tod2Map; repository=$script:Tod2Repo; stock_inputs=$donor; created=(Get-Date -Format o) } |
    ConvertTo-Json | Set-Content -LiteralPath $marker -Encoding UTF8
$null = Resolve-Tod2Root
Write-Host 'TOD II private workspace ready. No shared database/cache or Map One output was changed.'
