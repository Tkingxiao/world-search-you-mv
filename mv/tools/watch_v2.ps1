# watch_v2.ps1 - poll the four v2 render tasks until they finish (or 100 min elapse)
$ErrorActionPreference = 'SilentlyContinue'
$deadline = (Get-Date).AddMinutes(100)
while ((Get-Date) -lt $deadline) {
    $running = 0
    foreach ($t in @('MVv2_V2A','MVv2_V2B','MVv2_V2C','MVv2_V2D')) {
        $q = schtasks /Query /TN $t /FO LIST 2>$null | Out-String
        if ($q -match 'Running' -or $q -match '正在运行') { $running++ }
    }
    $shots = Get-ChildItem "D:\Code\Code MV\new-word.search(you)\mv\out\shots\s*.mp4" | Where-Object { $_.Name -ne 'preview_s14.mp4' }
    $line = "{0} running={1} sizes: {2}" -f (Get-Date -Format 'HH:mm:ss'), $running, (($shots | ForEach-Object { "$($_.Name)=$([math]::Round($_.Length/1MB,1))" }) -join ' ')
    Write-Output $line
    if ($running -eq 0) { Write-Output 'ALL TASKS FINISHED'; break }
    Start-Sleep 60
}
Write-Output 'WATCH END'
