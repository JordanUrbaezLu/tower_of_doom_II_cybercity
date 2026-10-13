<#
tools/sky3d/render_sky3d.ps1 - TOWER OF DOOM II: the rendered sky, one command (docs/166)

  .\tools\sky3d\render_sky3d.ps1                       # preview: 2048x1024, 64 spp, previews only (no asset)
  .\tools\sky3d\render_sky3d.ps1 -Ship                 # 8192x4096, 256 spp -> source_data/tod_skybox/_images/i_skybox_tod_cybercity.exr
  .\tools\sky3d\render_sky3d.ps1 -Width 4096 -Samples 128 -Asset
  .\tools\sky3d\render_sky3d.ps1 -FinishOnly -Raw C:\...\raw_8192.exr -Mirror    # re-finish a kept raw (no re-render)
  .\tools\sky3d\render_sky3d.ps1 -Ship -Sat 1.15 -ScreensDir none            # v6: the saturation grade; without the billboards
  .\tools\sky3d\render_sky3d.ps1 -Ship -Ships                                # v7b A/B: WITH the retired static ships (the sky fleet replaced them)
  .\tools\sky3d\render_sky3d.ps1 -FinishOnly -Raw C:\...\raw_8192.exr -NoSignMask   # v7b A/B: the title gate under the city's knee (as v7)

Two stages, both in Blender 4.2's own Python (numpy + the EXR reader come with it):
  1. build_city.py  builds the procedural megacity and renders it through Cycles' equirectangular camera
                    (OptiX on the GPU) into a raw LINEAR EXR under %TEMP%\tod_sky3d\ - kept, so a re-finish is free.
  2. finish_sky.py  solves the exposure (score = mean x 1024 -> -TargetScore, the docs/104 contract), soft-clips the
                    peaks, writes the half-float ZIP16 asset and the previews (docs/sky_preview/sky3d_*.png).
                    v7b: the title gate writes its own mask (<raw>.sign.exr) and gets its own brighter knee; the
                    exposure is solved on the city outside it (docs/166 s9.7).
A sky change is a FULL map build (.\tools\build_map.ps1). The master scene is saved to art/sky3d/tod2_sky.blend.
#>
param(
    [int]$Width = 2048,
    [int]$Samples = 64,
    [int]$Seed = 7,
    [double]$CamH = 220,
    [double]$Detail = 1.0,
    [double]$TargetScore = 0.64,   # v7: the shipped recipe is the default (2026-09-27 score 0.64 / sat 1.2 / display-mult 10; 2026-09-29 v7b roll 0)
    [double]$Knee = 10,
    [double]$KneeMax = 32,
    [double]$White = 1.0,          # v4: build_city.py authors in W = display white; the knee is then in W (KneeW..KneeMaxW) - 0 = the old mean-relative knee
    [double]$KneeW = 0.70,
    [double]$KneeMaxW = 1.0,
    [string]$DisplayMult = '10',    # v4: the worldspawn sky_intensity_factor the previews assume ('auto' = the value that puts W at display white; copy the printed number into gen_tower_map.js)
    [double]$Roll = 0,             # v7b: 0 - the TURN lives in the material. Engine truth (docs/196 s3): the centre column (the gate) faces yaw
                                   #      -(SSI sun azimuth 140 + "skyRotation" in mtl_skybox_tod_cybercity), not mirrored; skyRotation 40 = due
                                   #      WEST, where session 61's jump reveal looks. test_jumppad checks the sum.
    [string]$Tint = '1,1,1',
    [double]$Sat = 1.2,             # v6: finish_sky.py --sat, a saturation grade in linear light (the mean is re-held); the title gate divides it out
    [switch]$Mirror,
    [switch]$Ships,                 # v7b: build the retired airships / battlecruisers / fighters (A/B only; the ship has none)
    [switch]$Asteroids,             # v7c: build the retired rocks - belt, drifting rocks, black-hole debris (A/B only; the ship has none)
    [switch]$NoSignMask,            # v7b: finish without the title gate's own knee (its mask, <raw>.sign.exr)
    [ValidateSet('gpu', 'cpu')][string]$Device = 'gpu',   # v7b: 'cpu' for a test while the game holds the GPU
    [switch]$Ship,
    [switch]$Asset,
    [switch]$FinishOnly,
    [string]$Raw = '',
    [string]$Skip = '',
    [string]$ScreensDir = '',       # default: art\sky3d\billboards when it exists (docs/167); 'none' = the procedural mosaic only
    [string]$Tag = 'sky3d',
    [string]$Blender = 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe'
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ($Ship) { $Width = 8192; if ($Samples -lt 160) { $Samples = 160 }; $Asset = $true }
if (-not (Test-Path $Blender)) { throw "Blender not found at $Blender" }
$scratch = Join-Path $env:TEMP 'tod_sky3d'
New-Item -ItemType Directory -Force $scratch | Out-Null
if (-not $Raw) { $Raw = Join-Path $scratch "raw_$Width.exr" }
$blend = Join-Path $repo 'art\sky3d\tod2_sky.blend'
if (-not $ScreensDir) { $bb = Join-Path $repo 'art\sky3d\billboards'; if (Test-Path $bb) { $ScreensDir = $bb } }
if ($ScreensDir -eq 'none') { $ScreensDir = '' }

if (-not $FinishOnly) {
    $args1 = @('-b', '--factory-startup', '-P', (Join-Path $repo 'tools\sky3d\build_city.py'), '--',
        '--width', $Width, '--samples', $Samples, '--seed', $Seed, '--cam-h', $CamH, '--detail', $Detail,
        '--out', $Raw, '--save-blend', $blend)
    if ($Skip) { $args1 += @('--skip', $Skip) }
    if ($ScreensDir) { $args1 += @('--screens-dir', $ScreensDir) }
    if ($Ships) { $args1 += '--ships' }
    if ($Asteroids) { $args1 += '--asteroids' }
    if ($Device -ne 'gpu') { $args1 += @('--device', $Device) }
    Write-Host "== build + render ($Width x $($Width/2), $Samples spp) -> $Raw"
    $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'   # v5: Blender prints a TBBmalloc note on stderr; under Stop + 2>&1 that one line killed the wrapper
    & $Blender @args1 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match '^\[sky3d|Error|Traceback|line \d+|Time:' }
    $ErrorActionPreference = $eap
    if ($LASTEXITCODE -ne 0) { throw "render failed ($LASTEXITCODE)" }
    if (-not (Test-Path $Raw)) { throw "no raw EXR at $Raw" }
}
$args2 = @('-b', '--factory-startup', '-P', (Join-Path $repo 'tools\sky3d\finish_sky.py'), '--',
    '--in', $Raw, '--target-score', $TargetScore, '--knee', $Knee, '--knee-max', $KneeMax, '--roll', $Roll, '--tint', $Tint, '--sat', $Sat, '--tag', $Tag, '--display-mult', $DisplayMult)
if ($White -gt 0) { $args2 += @('--white', $White, '--knee-w', $KneeW, '--knee-max-w', $KneeMaxW) }
if ($Mirror) { $args2 += '--mirror' }
if ($NoSignMask) { $args2 += '--no-sign-mask' }
if (-not $Asset) { $args2 += '--no-asset' }
Write-Host "== finish ($(if ($Asset) { 'ASSET + previews' } else { 'previews only' }))"
$eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $Blender @args2 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match '^\[finish|Error|Traceback|line \d+' }
$ErrorActionPreference = $eap
Write-Host "NOTE (v4): the previews assume worldspawn sky_intensity_factor0/1 = the 'display-mult auto' number printed above; gen_tower_map.js must carry the same value (a full build)."
if ($LASTEXITCODE -ne 0) { throw "finish failed ($LASTEXITCODE)" }
if ($Asset) { Write-Host "asset written: source_data\tod_skybox\_images\i_skybox_tod_cybercity.exr - a sky change is a FULL build" }
