"""Watch the v3 tail and rebalance on the fly (no manual babysitting).

Rules:
  * when s05.mp4 is finalized (1638 frames)  -> start V3S10 (s10)
  * when s11.mp4 is finalized (1660 frames)  -> end MVv2_V2A, start V3S0109 (s01,s09)
Runs in a loop until both actions are done (or the deadline passes).
"""
import os
import subprocess
import sys
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'


def frames(name):
    p = os.path.join(SHOTS, name + '.mp4')
    if not os.path.exists(p):
        return -1
    try:
        r = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                            '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                           capture_output=True, text=True, timeout=120)
        return int((r.stdout or '0').strip() or 0)
    except Exception:
        return -1


def schtasks(*args):
    r = subprocess.run(['schtasks'] + list(args), capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    print('[schtasks %s] rc=%s %s' % (' '.join(args), r.returncode,
                                      (r.stdout or r.stderr).strip()[-100:]), flush=True)


done_s10 = False
done_split = False
deadline = time.time() + 60 * 50

while time.time() < deadline and not (done_s10 and done_split):
    if not done_s10 and frames('s05') == 1638:
        schtasks('/Run', '/TN', 'MVv3_V3S10')
        done_s10 = True
        print('started V3S10 (s10) at %s' % time.strftime('%H:%M:%S'), flush=True)
    if not done_split and frames('s11') == 1660:
        schtasks('/End', '/TN', 'MVv2_V2A')
        time.sleep(3)
        schtasks('/Run', '/TN', 'MVv3_V3S0109')
        done_split = True
        print('ended V2A + started V3S0109 at %s' % time.strftime('%H:%M:%S'), flush=True)
    time.sleep(25)

print('AUTO_REBALANCE_DONE s10=%s split=%s' % (done_s10, done_split), flush=True)
