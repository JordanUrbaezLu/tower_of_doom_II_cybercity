# Tower II's ONLY writable Mod Tools workspace. Never set machine/user TA_*.
$script:Tod2Map = 'zm_tod2_cybercity'
$script:Tod2Root = 'C:\BO3Tools\TOD2Cybercity'
$script:Tod2Repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

function Assert-Tod2WritePath([string]$Path, [switch]$Repository, [switch]$Tree) {
    $base = if ($Repository) { $script:Tod2Repo } else { $script:Tod2Root }
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($full -ne $base -and -not $full.StartsWith($base + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "TOD II ISOLATION: refusing write outside $base : $full"
    }
    # A private-looking path must not traverse a junction into a donor tree.
    $cursor = $full
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "TOD II ISOLATION: refusing write through source reference $cursor"
            }
        }
        $cursor = Split-Path $cursor -Parent
    }
    # Tree copies cannot contain nested source junctions either.
    if ($Tree -and (Test-Path -LiteralPath $full -PathType Container)) {
        $links = @(Get-ChildItem -LiteralPath $full -Recurse -Force -Attributes ReparsePoint)
        if ($links.Count) { throw "TOD II ISOLATION: destination tree contains source references: $full" }
    }
}

function Resolve-Tod2Root([string]$Override = '') {
    if ($Override -and [IO.Path]::GetFullPath($Override).TrimEnd('\') -ne $script:Tod2Root) {
        throw "TOD II ISOLATION: -ModToolsRoot must be $script:Tod2Root; shared installs and Map One are forbidden."
    }
    $marker = Join-Path $script:Tod2Root '.tod2-workspace.json'
    if (-not (Test-Path -LiteralPath $marker)) {
        throw 'Run tools/setup_tod2_workspace.ps1 first. Never fall back to the shared Steam tools.'
    }
    $owner = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    if ($owner.map -ne $script:Tod2Map -or $owner.repository -ne $script:Tod2Repo) {
        throw 'TOD II ISOLATION: workspace marker belongs to another map/repository.'
    }
    foreach ($dir in @('bin','gdtdb','source_data','share\assetconvert','share\raw\maps','share\raw\fx','share\raw\sound','sound','sw4','usermaps','map_source','pc')) {
        Assert-Tod2WritePath (Join-Path $script:Tod2Root $dir) -Tree
    }
    foreach ($dir in @('share\assetconvert\ToolsGfx\shaders_modtools','share\assetconvert\shaders','share\assetconvert\preshader')) {
        $shaderPath = Join-Path $script:Tod2Root $dir
        if (-not (Test-Path -LiteralPath $shaderPath) -or -not (Get-ChildItem -LiteralPath $shaderPath -File -Recurse | Select-Object -First 1)) {
            throw "TOD II workspace lacks required private stock shader binaries: $shaderPath"
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $script:Tod2Root 'sw4\textures\tv_lookup.tif'))) {
        throw 'TOD II workspace lacks the private stock sw4 texture library (i_generic_lookup).'
    }
    return $script:Tod2Root
}

function Set-Tod2ProcessEnvironment {
    $root = Resolve-Tod2Root
    foreach ($name in @('TA_GAME_PATH','TA_TOOLS_PATH','TA_GAME_PATH_PROCESS','TA_TOOLS_PATH_PROCESS')) {
        [Environment]::SetEnvironmentVariable($name, $root + '\', 'Process')
    }
    foreach ($name in @('TA_LOCAL_ASSET_CACHE','TA_LOCAL_ASSET_CACHE_PROCESS')) {
        [Environment]::SetEnvironmentVariable($name, (Join-Path $root 'share\assetconvert'), 'Process')
    }
}

function Connect-Tod2GameFolder {
    $root = Resolve-Tod2Root
    $game = 'C:\Program Files (x86)\Steam\steamapps\common\Call of Duty Black Ops III'
    if (-not (Test-Path -LiteralPath (Join-Path $game 'BlackOps3.exe'))) { throw 'BO3 game installation not found.' }
    $target = Join-Path $root "usermaps\$script:Tod2Map"
    $link = Join-Path $game "usermaps\$script:Tod2Map"
    # Never replace the existing usermaps junction or touch a sibling map.
    if (Test-Path -LiteralPath $link) {
        $item = Get-Item -LiteralPath $link -Force
        if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $item.Target -ne $target) {
            throw "TOD II ISOLATION: existing game folder does not point at our private workspace: $link"
        }
    } else {
        New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    }
}
