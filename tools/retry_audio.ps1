$py = "C:\Users\lv\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
Write-Output "waiting for GitHub rate limit reset..."
Start-Sleep -Seconds 1280
& $py -u "C:\Users\lv\Downloads\huml\cet\tools\fetch_audio_slow.py" 2>&1