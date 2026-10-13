# Read-only guard invocation: no directory creation, copy, sync or native tool.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../../tod2_workspace.ps1')
$wfDestinations = @(
    'C:\BO3Tools\TOD2Cybercity\model_export\tod2_bo6_wunderfizz',
    'C:\BO3Tools\TOD2Cybercity\xanim_export\tod2_bo6_wunderfizz',
    'C:\BO3Tools\TOD2Cybercity\share\raw\collmaps',
    'C:\BO3Tools\TOD2Cybercity\share\raw\fx\_t10',
    'C:\BO3Tools\TOD2Cybercity\source_data\tod2_bo6_wunderfizz.gdt',
    'C:\BO3Tools\TOD2Cybercity\sound_assets\_wetegg\t10\wunderfizz',
    'C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\zone_source\tod2_bo6_wunderfizz.zpkg',
    'C:\BO3Tools\TOD2Cybercity\usermaps\zm_tod2_cybercity\sound\aliases\tod_wunderfizz.csv'
)
foreach ($wfDestination in $wfDestinations) {
    Assert-Tod2WritePath $wfDestination -Tree
    Write-Output ('GUARD_OK ' + $wfDestination)
}
