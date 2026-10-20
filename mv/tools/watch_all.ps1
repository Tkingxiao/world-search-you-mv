# watch_all.ps1 - log render throughput until every renderer has exited
$ErrorActionPreference = 'SilentlyContinue'
$mv = 'D:\Code\Code MV\new-word.search(you)'
$deadline = (Get-Date).AddMinutes(150)
while ((Get-Date) -lt $deadline) {
    $renderers = @(Get-CimInstance Win32_Process -Filter "Name='blender.exe'" |
        Where-Object { $_.CommandLine -like '*render_shot.py*' })
    $shots = Get-ChildItem "$mv\mv\out\shots\s*.mp4" | Where-Object { $_.Name -ne 'preview_s14.mp4' }
    $sizes = ($shots | Sort-Object Name | ForEach-Object { "$($_.BaseName)=$([math]::Round($_.Length/1MB,1))" }) -join ' '
    Write-Output ("{0} renderers={1} {2}" -f (Get-Date -Format 'HH:mm:ss'), $renderers.Count, $sizes)
    if ($renderers.Count -eq 0) { Write-Output 'ALL RENDERERS EXITED'; break }
    Start-Sleep 90
}
Write-Output 'WATCH END'
