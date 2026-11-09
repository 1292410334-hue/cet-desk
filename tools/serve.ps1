# 在本机起一个静态服务器，手机连同一个 Wi-Fi 就能看
$py = "C:\Users\lv\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$ip = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.InterfaceAlias -notlike '*VPN*' } |
  Sort-Object -Property InterfaceAlias | Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "  电脑： http://127.0.0.1:8080/"
Write-Host "  手机： http://$ip`:8080/"
Write-Host ""
Write-Host "  手机要和电脑连同一个 Wi-Fi。按 Ctrl+C 停止。"
Write-Host ""
& $py -m http.server 8080 --bind 0.0.0.0 --directory $PSScriptRoot\..
