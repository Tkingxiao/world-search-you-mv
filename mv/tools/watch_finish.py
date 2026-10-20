"""Wait until every v3 shot mp4 exists with the exact planned frame count."""
import os
import subprocess
import sys
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
PLAN = {'s01': 360, 's02': 502, 's03': 837, 's04': 753, 's05': 1638, 's06': 883,
        's07': 1610, 's08': 1642, 's09': 885, 's10': 1658, 's11': 1660, 's12': 1598,
        's13': 1638, 's14': 881, 's15': 1176}


def frames(name):
    p = os.path.join(SHOTS, name + '.mp4')
    if not os.path.exists(p):
        return -1
    try:
        r = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                            '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                           capture_output=True, text=True, timeout=300)
        return int((r.stdout or '0').strip() or 0)
    except Exception:
        return -1


deadline = time.time() + 4 * 3600
while time.time() < deadline:
    done = [s for s in PLAN if frames(s) == PLAN[s]]
    rend = subprocess.run(['powershell', '-NoProfile', '-Command',
                           "(Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | Where-Object { $_.CommandLine -match 'render_shot' }).Count"],
                          capture_output=True, text=True)
    n = (rend.stdout or '').strip()
    print('%s done=%d/15 renderers=%s' % (time.strftime('%H:%M:%S'), len(done), n), flush=True)
    if len(done) == 15:
        print('ALL_SHOTS_COMPLETE', flush=True)
        sys.exit(0)
    time.sleep(120)

print('TIMEOUT', flush=True)
sys.exit(1)
