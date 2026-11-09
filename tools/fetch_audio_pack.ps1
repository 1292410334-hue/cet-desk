$ErrorActionPreference = 'Continue'
$h = @{'User-Agent' = 'cet'}
$tree = Invoke-RestMethod -Uri "https://api.github.com/repos/0609x/CET46-Resources/git/trees/main?recursive=1" -Headers $h -TimeoutSec 60
$need = $tree.tree | Where-Object { $_.type -eq 'blob' -and $_.path -match '^(四级|六级)真题/(2025\.06|2026\.06)/听力音频/.*\.mp3$' }

$dir = "C:\Users\lv\Downloads\huml\cet\data\audio"
$tmp = "C:\Users\lv\Downloads\huml\_audio_tmp"
New-Item -ItemType Directory -Force -Path $dir, $tmp | Out-Null
$ff = "C:\Users\lv\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

# 与 data/audio.js 的 id 对齐：cet4_2025_06_0 / cet6_2025_06_13 / cet6_2026_06_10 …
$ids = @{
  '四级真题/2025.06/听力音频/2025年6月四级音频1.MP3' = 'cet4_2025_06_0'
  '六级真题/2025.06/听力音频/2025年6月六级音频1.MP3' = 'cet6_2025_06_13'
  '六级真题/2026.06/听力音频/2026年6月六级听力音频.mp3' = 'cet6_2026_06_10'
}

foreach ($f in $need) {
  $name = $ids[$f.path]
  if (-not $name) { Write-Output "skip unlisted $($f.path)"; continue }
  $out = Join-Path $dir "$name.mp3"
  if ((Test-Path $out) -and ((Get-Item $out).Length -gt 1000000)) { Write-Output "have $name"; continue }
  $raw = Join-Path $tmp "$name.src"
  Write-Output "get $($f.path) $([math]::Round($f.size/1MB,1)) MB"
  curl.exe -sSL --fail --retry 6 --retry-all-errors --retry-delay 2 --connect-timeout 20 --max-time 1800 `
    -H "Accept: application/vnd.github.raw" -H "User-Agent: cet" -o $raw `
    "https://api.github.com/repos/0609x/CET46-Resources/git/blobs/$($f.sha)"
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $raw)) { Write-Output "  fail $name"; continue }
  & $ff -y -loglevel error -i $raw -ac 1 -ar 24000 -b:a 40k $out
  if (Test-Path $out) { Write-Output ("  -> " + $name + " " + [math]::Round((Get-Item $out).Length/1MB,2) + " MB") }
  Remove-Item $raw -ErrorAction SilentlyContinue
}
Write-Output "done"
