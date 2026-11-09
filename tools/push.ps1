# 用临时 token 一条命令推完并开 Pages
# 用法：powershell -ExecutionPolicy Bypass -File tools/push.ps1 -Token github_pat_xxx
param(
  [Parameter(Mandatory=$true)][string]$Token,
  [string]$Owner = "1292410334-hue",
  [string]$Repo  = "cet-desk",
  [string]$Branch = "main"
)
$ErrorActionPreference = "Stop"
$env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 1. 推送（用 token 走 https，不走被墙的 OAuth 登录页）
$url = "https://$Owner`:$Token@github.com/$Owner/$Repo.git"
git remote remove origin 2>$null
git remote add origin $url
git push -u origin $Branch --force
if ($LASTEXITCODE -ne 0) { throw "推送失败，检查 token 权限（需要 Contents: Read and write）" }
git remote set-url origin "https://github.com/$Owner/$Repo.git"
Write-Host "推送完成" -ForegroundColor Green

# 2. 开 Pages（已开过会返回 409，忽略）
$h = @{ Authorization = "Bearer $Token"; Accept = "application/vnd.github+json"; "User-Agent" = "cet-desk" }
$body = @{ source = @{ branch = $Branch; path = "/" } } | ConvertTo-Json
try {
  Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/pages" -Method Post -Headers $h -Body $body -ContentType "application/json" | Out-Null
  Write-Host "Pages 已开启" -ForegroundColor Green
} catch {
  Write-Host "Pages 开启返回：$($_.Exception.Message)" -ForegroundColor Yellow
}

# 3. 等构建
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 10
  try {
    $p = Invoke-RestMethod -Uri "https://api.github.com/repos/$Owner/$Repo/pages" -Headers $h
    Write-Host ("状态：{0}  地址：{1}" -f $p.status, $p.html_url)
    if ($p.status -eq "built") { break }
  } catch { }
}
Write-Host ""
Write-Host ("打开：https://$Owner.github.io/$Repo/") -ForegroundColor Cyan
