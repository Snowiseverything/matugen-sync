@echo off
title OpenRGB Server Setup (Admin Required)
echo ============================================
echo  OpenRGB Server Setup - Run as Administrator
echo ============================================
echo.
echo This will create a scheduled task to start
echo OpenRGB server as admin at each logon.
echo.

set OPENRGB_PATH=%LOCALAPPDATA%\OpenRGB\OpenRGB.exe

if not exist "%OPENRGB_PATH%" (
    echo ERROR: OpenRGB not found at %OPENRGB_PATH%
    echo Please download OpenRGB 1.0rc3 from https://openrgb.org/releases.html
    echo and extract it to %%LOCALAPPDATA%%\OpenRGB\
    echo.
    echo Or run: python -m matugen_sync --setup-openrgb
    pause
    exit /b 1
)

echo Using: %OPENRGB_PATH%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$taskName = 'OpenRGB Server'; " ^
  "$openrgb = '%LOCALAPPDATA:\=\\%\\OpenRGB\\OpenRGB.exe'; " ^
  "$action = New-ScheduledTaskAction -Execute $openrgb -Argument '--server --startminimized'; " ^
  "$trigger = New-ScheduledTaskTrigger -AtLogOn -User '%USERDOMAIN%\\%USERNAME%'; " ^
  "$principal = New-ScheduledTaskPrincipal -UserId '%USERDOMAIN%\\%USERNAME%' -RunLevel Highest -LogonType S4U; " ^
  "$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable; " ^
  "Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force; " ^
  "echo. & echo Task '$taskName' created. Starting now...; " ^
  "Start-ScheduledTask -TaskName $taskName"

echo.
echo ============================================
echo  Setup complete!
echo  The OpenRGB server will start automatically
echo  at each logon.
echo.
echo  To verify RAM detection, run:
echo    matugen-sync --list-devices
echo ============================================
pause
