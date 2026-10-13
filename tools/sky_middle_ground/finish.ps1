param([ValidateSet(2048,4096,8192)][int]$Width=4096, [double]$DisplayMult=10,
      [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')][string]$Review='preview4096', [string]$Views='')
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$raw=Join-Path $repo "tmp/sky_middle_ground/raw_$Width.exr"
$mask=Join-Path $repo "tmp/sky_middle_ground/raw_$Width.sign.exr"
$receipt=Join-Path $repo "tmp/sky_middle_ground/raw_$Width.render.json"
if (!(Test-Path $receipt) -or !(Test-Path $raw) -or !(Test-Path $mask)) { throw 'Render and paired sign AOV must finish first' }
if ((Get-Item $mask).LastWriteTime -lt (Get-Item $raw).LastWriteTime.AddSeconds(-10)) { throw 'Stale sign AOV' }
$renderProof=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
$rawHash=(Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash.ToLowerInvariant()
$maskHash=(Get-FileHash -LiteralPath $mask -Algorithm SHA256).Hash.ToLowerInvariant()
if ($rawHash -ne $renderProof.raw_sha256 -or $maskHash -ne $renderProof.mask_sha256) { throw 'Raw sky/sign AOV differ from the render receipt' }
$preview=Join-Path $repo "art/sky3d/middle_ground_review/$Review"
$out=Join-Path $repo "tmp/sky_middle_ground/finished_$Width.exr"
$filterArgs=@()
if ($Views) { $filterArgs=@('--views',$Views) }
& 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -b --factory-startup -P (Join-Path $repo 'tools/sky3d/finish_sky.py') -- --in $raw --sign-mask $mask --out $out --preview-dir $preview --tag middle_ground --target-score 0.64 --white 1 --knee-w 0.70 --knee-max-w 1 --display-mult $DisplayMult --sat 1.2 --roll 0 @filterArgs
if ($LASTEXITCODE -ne 0) { throw "Sky finish failed: $LASTEXITCODE" }
if ((Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash.ToLowerInvariant() -ne $rawHash -or (Get-FileHash -LiteralPath $mask -Algorithm SHA256).Hash.ToLowerInvariant() -ne $maskHash) { throw 'Paired render changed while finishing' }
$stats=Join-Path $preview 'middle_ground_stats.json'
$proof=[ordered]@{
    finished_at=(Get-Date).ToString('o')
    raw=$raw; raw_sha256=$rawHash
    mask=$mask; mask_sha256=$maskHash
    asset=$out; asset_sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
    stats=$stats; stats_sha256=(Get-FileHash -LiteralPath $stats -Algorithm SHA256).Hash.ToLowerInvariant()
    finish_source_sha256=(Get-FileHash -LiteralPath (Join-Path $repo 'tools/sky3d/finish_sky.py') -Algorithm SHA256).Hash.ToLowerInvariant()
}
[IO.File]::WriteAllText((Join-Path $preview 'finish.json'),($proof | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
