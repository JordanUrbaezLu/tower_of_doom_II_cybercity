$ErrorActionPreference='Stop'
$repo=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$owned=Get-Content -LiteralPath (Join-Path $repo 'tmp/alarm_lens_repair/visible_process.json') -Raw | ConvertFrom-Json
$previewProcess=Get-Process -Id $owned.pid -ErrorAction Stop
if ($previewProcess.ProcessName -ne 'blender' -or $previewProcess.StartTime.ToFileTimeUtc() -ne $owned.start_filetime) { throw 'Owned preview is no longer running' }
if ($previewProcess.MainWindowTitle -notlike 'native_preview*') { throw 'Owned Blender is not showing the reviewed preview' }
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class AlarmPreviewWindow {
    [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left,Top,Right,Bottom; }
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr handle);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr handle, out Rect rect);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
'@
[void][AlarmPreviewWindow]::SetProcessDPIAware()
[void][AlarmPreviewWindow]::SetForegroundWindow($previewProcess.MainWindowHandle)
Start-Sleep -Seconds 2
if ([AlarmPreviewWindow]::GetForegroundWindow() -ne $previewProcess.MainWindowHandle) { throw 'Owned preview is not in the foreground; refusing to capture another app' }
$rect=New-Object AlarmPreviewWindow+Rect
if (![AlarmPreviewWindow]::GetWindowRect($previewProcess.MainWindowHandle,[ref]$rect)) { throw 'Cannot locate the owned preview window' }
$width=$rect.Right-$rect.Left
$height=$rect.Bottom-$rect.Top
if ($width -le 0 -or $height -le 0) { throw 'Preview window has no visible bounds' }
$bitmap=New-Object System.Drawing.Bitmap($width,$height)
$graphics=[System.Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size)
    $path=Join-Path $repo 'tmp/alarm_lens_repair/visible_window.png'
    $bitmap.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
    Write-Output $path
} finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}
