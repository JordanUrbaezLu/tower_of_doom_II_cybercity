param([ValidateSet(2048,4096,8192)][int]$Width=4096, [double]$DisplayMult=10,
      [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')][string]$Review='preview4096', [string]$Views='')
$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$profilePath=Join-Path $PSScriptRoot 'finish_profile.json'
$profile=Get-Content -LiteralPath $profilePath -Raw | ConvertFrom-Json
$profileHash=(Get-FileHash -LiteralPath $profilePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($profile.schema -ne 1 -or $profile.mode -ne 'fixed_baseline_gain') { throw 'Unknown finish profile' }
$baselinePath=Join-Path $repo $profile.baseline_stats
if ((Get-FileHash -LiteralPath $baselinePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $profile.baseline_stats_sha256) { throw 'Reviewed baseline stats changed' }
$baseline=Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json
$fixedGain=[double]$profile.fixed_gain
if ([double]::IsNaN($fixedGain) -or [double]::IsInfinity($fixedGain) -or $fixedGain -le 0 -or $fixedGain -ne [double]$baseline.gain) { throw 'Gain must equal the exact reviewed baseline' }
if ([double]$profile.nominal_target_score -ne [double]$baseline.target_score) { throw 'Nominal target differs from baseline metadata' }
$gainArg=$fixedGain.ToString('R',[Globalization.CultureInfo]::InvariantCulture)
$targetArg=([double]$profile.nominal_target_score).ToString('R',[Globalization.CultureInfo]::InvariantCulture)
$raw=Join-Path $repo "tmp/sky_consistency/raw_$Width.exr"
$mask=Join-Path $repo "tmp/sky_consistency/raw_$Width.sign.exr"
$receipt=Join-Path $repo "tmp/sky_consistency/raw_$Width.render.json"
if (!(Test-Path $receipt) -or !(Test-Path $raw) -or !(Test-Path $mask)) { throw 'Render and paired sign AOV must finish first' }
if ((Get-Item $mask).LastWriteTime -lt (Get-Item $raw).LastWriteTime.AddSeconds(-10)) { throw 'Stale sign AOV' }
$renderProof=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
$rawHash=(Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash.ToLowerInvariant()
$maskHash=(Get-FileHash -LiteralPath $mask -Algorithm SHA256).Hash.ToLowerInvariant()
if ($rawHash -ne $renderProof.raw_sha256 -or $maskHash -ne $renderProof.mask_sha256) { throw 'Raw sky/sign AOV differ from the render receipt' }
$preview=Join-Path $repo "art/sky3d/consistency_review/$Review"
$out=Join-Path $repo "tmp/sky_consistency/finished_$Width.exr"
$filterArgs=@()
if ($Views) { $filterArgs=@('--views',$Views) }
& 'C:\Program Files\Blender Foundation\Blender 4.2\blender.exe' -b --factory-startup -P (Join-Path $repo 'tools/sky3d/finish_sky.py') -- --in $raw --sign-mask $mask --out $out --preview-dir $preview --tag consistency --target-score $targetArg --fixed-gain $gainArg --white 1 --knee-w 0.70 --knee-max-w 1 --display-mult $DisplayMult --sat 1.2 --roll 0 @filterArgs
if ($LASTEXITCODE -ne 0) { throw "Sky finish failed: $LASTEXITCODE" }
if ((Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash.ToLowerInvariant() -ne $rawHash -or (Get-FileHash -LiteralPath $mask -Algorithm SHA256).Hash.ToLowerInvariant() -ne $maskHash) { throw 'Paired render changed while finishing' }
$stats=Join-Path $preview 'consistency_stats.json'
if ((Get-FileHash -LiteralPath $profilePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $profileHash) { throw 'Finish profile changed during processing' }
$finishedStats=Get-Content -LiteralPath $stats -Raw | ConvertFrom-Json
if ($finishedStats.gain_mode -ne 'fixed' -or [double]$finishedStats.fixed_gain -ne $fixedGain -or [double]$finishedStats.gain -ne $fixedGain) { throw 'Finished sky did not use the fixed baseline gain' }
$proof=[ordered]@{
    finished_at=(Get-Date).ToString('o')
    raw=$raw; raw_sha256=$rawHash
    mask=$mask; mask_sha256=$maskHash
    asset=$out; asset_sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLowerInvariant()
    stats=$stats; stats_sha256=(Get-FileHash -LiteralPath $stats -Algorithm SHA256).Hash.ToLowerInvariant()
    finish_source_sha256=(Get-FileHash -LiteralPath (Join-Path $repo 'tools/sky3d/finish_sky.py') -Algorithm SHA256).Hash.ToLowerInvariant()
    finish_profile_sha256=$profileHash
    gain_mode='fixed'; fixed_gain=$fixedGain
    nominal_target_score=[double]$profile.nominal_target_score
    measured_city_score=[double]$finishedStats.score_city
    measured_whole_score=[double]$finishedStats.score
}
[IO.File]::WriteAllText((Join-Path $preview 'finish.json'),($proof | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
