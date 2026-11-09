@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在把改动推到 GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -File "tools\push.ps1"
echo.
echo 一分钟后看：https://1292410334-hue.github.io/cet-desk/
pause
