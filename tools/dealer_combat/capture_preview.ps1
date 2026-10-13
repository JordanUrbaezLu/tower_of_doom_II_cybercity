$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$owned=Get-Content -LiteralPath (Join-Path $repo 'tmp/dealer_boss_mcp/launch.json') -Raw | ConvertFrom-Json
$previewProcess=Get-Process -Id $owned.pid -ErrorAction Stop
$command=Get-CimInstance Win32_Process -Filter "ProcessId=$($owned.pid)"
if ($previewProcess.ProcessName -ne 'blender' -or $command.CommandLine -notlike '*tools/dealer_boss/mcp_bootstrap.py*') { throw 'Owned Dealer preview is no longer running' }
$started=[DateTime]::Parse($owned.started_utc).ToUniversalTime()
if ([Math]::Abs(($previewProcess.StartTime.ToUniversalTime()-$started).TotalSeconds) -gt 5) { throw 'Owned preview process identity changed' }
if ($previewProcess.MainWindowTitle -notlike '*dealer_combat*') { throw 'Owned Blender is not showing the combat review' }
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class DealerPreviewWindow {
    [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[void][DealerPreviewWindow]::SetProcessDPIAware()
[void][DealerPreviewWindow]::SetForegroundWindow($previewProcess.MainWindowHandle)
Start-Sleep -Seconds 2
if ([DealerPreviewWindow]::GetForegroundWindow() -ne $previewProcess.MainWindowHandle) { throw 'Owned preview is not foreground; refusing to capture another app' }
$rect=New-Object DealerPreviewWindow+Rect
if (![DealerPreviewWindow]::GetWindowRect($previewProcess.MainWindowHandle,[ref]$rect)) { throw 'Cannot locate the owned preview window' }
$width=$rect.Right-$rect.Left
$height=$rect.Bottom-$rect.Top
if ($width -le 0 -or $height -le 0) { throw 'Preview window has no visible bounds' }
$bitmap=New-Object System.Drawing.Bitmap($width,$height)
$graphics=[System.Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size)
    $path=Join-Path $repo 'art/dealer_combat/review/visible_window.png'
    $bitmap.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
    [pscustomobject]@{pid=$owned.pid;started_utc=$owned.started_utc;title=$previewProcess.MainWindowTitle;captured_utc=[DateTime]::UtcNow.ToString('o');image=$path} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $repo 'art/dealer_combat/review/visible_window.json') -Encoding UTF8
    Write-Output $path
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}
