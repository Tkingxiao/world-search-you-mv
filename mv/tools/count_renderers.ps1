$procs = Get-CimInstance Win32_Process -Filter "Name='blender.exe'" |
    Where-Object { $_.CommandLine -like '*render_shot.py*' }
@($procs).Count
