"""dispatch.py - keep 4 render slots busy from a pending shot queue.

The four long-running queue drivers (A/B/C) keep their own shot lists; this
dispatcher only handles the shots that are NOT covered by them, starting one
`render_queue.py` process per free GPU slot (max 4 concurrent blender renders).

Usage:
  python mv/tools/dispatch.py            # blocks until all pending started and GPU idle
  python mv/tools/dispatch.py --dry      # print plan only

Pending plan (tag -> shots):
  E: s10
  F: s13,s15
  G: s14
  H: s01      (re-render; existing mp4 is overwritten)
"""
import argparse
import os
import subprocess
import sys
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
PY = sys.executable
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
LOG = os.path.join(JOBS, 'dispatch.log')
MAX_SLOTS = 4

PLAN = [
    ('E', ['s10']),
    ('F', ['s13', 's15']),
    ('G', ['s14']),
    ('H', ['s01']),
]

PS_COUNT = (
    "powershell -NoProfile -Command \""
    "(Get-CimInstance Win32_Process -Filter \\\"Name='blender.exe'\\\" | "
    "Where-Object { $_.CommandLine -like '*render_shot.py*' } | Measure-Object).Count\""
)


def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    os.makedirs(JOBS, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def active_renders():
    try:
        out = subprocess.run(PS_COUNT, shell=True, capture_output=True, text=True,
                             timeout=60, cwd=MV)
        return int((out.stdout or '0').strip().splitlines()[-1])
    except Exception as e:  # noqa
        log('WARN active_renders failed: %r' % e)
        return MAX_SLOTS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    pending = list(PLAN)
    started = []
    log('DISPATCH start pending=%s' % ([p[0] for p in pending],))
    if a.dry:
        return

    while pending:
        n = active_renders()
        if n < MAX_SLOTS:
            tag, shots = pending.pop(0)
            cmd = [PY, os.path.join('mv', 'tools', 'render_queue.py'),
                   '--shots', ','.join(shots), '--tag', tag]
            logf = open(os.path.join(JOBS, 'dispatch_%s.out' % tag), 'a',
                        encoding='utf-8', errors='replace')
            creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
            p = subprocess.Popen(cmd, cwd=MV, stdout=logf, stderr=subprocess.STDOUT,
                                 creationflags=creationflags)
            started.append(tag)
            log('START %s shots=%s pid=%s (active renders before start=%d)' % (
                tag, shots, p.pid, n))
            time.sleep(20)
        else:
            time.sleep(25)

    log('DISPATCH all queues started: %s' % (started,))
    while active_renders() > 0:
        time.sleep(30)
    log('DISPATCH done, GPU idle')


if __name__ == '__main__':
    main()
