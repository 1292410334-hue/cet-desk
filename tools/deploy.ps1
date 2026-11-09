# 把站点推到 GitHub，开启 Pages；以后改完再跑一次就是更新
param(
  [string]$Repo = "",                      # 例：https://github.com/你的名字/cet-desk.git
  [string]$Branch = "main",
  [string]$Name = "cet-desk",
  [string]$Email = "cet-desk@example.com"
)
$ErrorActionPreference = "Stop"
$env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (git config user.name))  { git config user.name  $Name }
if (-not (git config user.email)) { git config user.email $Email }
if (-not (Test-Path ".git")) { git init | Out-Null }

git add -A
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "update $stamp" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "没有新改动" }

if (-not $Repo) {
  if (-not (git remote)) {
    Write-Host ""
    Write-Host "第一次用，先给我仓库地址："
    Write-Host "  powershell -ExecutionPolicy Bypass -File tools/deploy.ps1 -Repo https://github.com/你的名字/仓库.git"
    Write-Host ""
    exit 0
  }
} elseif (-not (git remote)) {
  git remote add origin $Repo
} else {
  git remote set-url origin $Repo
}

git branch -M $Branch
git push -u origin $Branch
Write-Host ""
Write-Host "推好了。第一次还要在网页上开一次 Pages："
Write-Host "  仓库 Settings -> Pages -> Source 选 $Branch / (root) -> Save"
Write-Host "  一两分钟后：https://<用户名>.github.io/<仓库名>/"
Write-Host ""
Write-Host "以后每次改完，跑这个脚本就行，Pages 会自己重新构建。"
