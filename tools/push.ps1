# 改完就跑这一条，把改动推上去（凭据已经存在 Windows 里，不会再弹授权）
param([string]$Message = "")
$ErrorActionPreference = "Stop"
$env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $Message) { $Message = "update " + (Get-Date -Format "yyyy-MM-dd HH:mm") }

git add -A
git commit -m $Message 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "没有新改动，直接同步" -ForegroundColor Yellow }

git push origin main
if ($LASTEXITCODE -ne 0) { throw "推送失败：检查网络/代理，或重新登录一次凭据" }

Write-Host ""
Write-Host "已推送。GitHub Pages 会在 1 分钟左右重新构建：" -ForegroundColor Green
Write-Host "  https://1292410334-hue.github.io/cet-desk/" -ForegroundColor Cyan
Write-Host ""
Write-Host "看构建状态：https://github.com/1292410334-hue/cet-desk/actions"
