"""fill_v2.py - slot filler for the label-fix re-renders (s05/s07/s08).

Slot accounting is done by counting *live blender render processes* (PowerShell WMI,
command line contains render_shot.py), not by parsing localized schtasks output.
Keeps at most 4 concurrent renderers: whenever a slot frees, start the next pending
re-render. Exits once all three re-renders have been started and finished.
"""
import os
import subprocess
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')

PENDING = [('MVv2_V2R1', 's05'), ('MVv2_V2R2', 's07'), ('MVv2_V2R3', 's08')]
STARTED = set()
MAX_RENDERERS = 4

PS_COUNT = ('powershell -NoProfile -Command '
            '"@(Get-CimInstance Win32_Process -Filter \\"Name=\'blender.exe\'\\" | '
            'Where-Object { $_.CommandLine -like \'*render_shot.py*\' }).Count"')


def count_renderers():
    p = subprocess.run(PS_COUNT, shell=True, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    try:
        return int((p.stdout or '0').strip().splitlines()[-1])
    except (ValueError, IndexError):
        return 0


def task_state(name):
    p = subprocess.run(['schtasks', '/Query', '/TN', name, '/XML'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    if '<State>Running</State>' in out:
        return 'running'
    if '<State>Ready</State>' in out or '<State>Disabled</State>' in out:
        return 'idle'
    return 'unknown'


def log(msg):
    line = '%s %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(os.path.join(JOBS, 'fill_v2.out'), 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def main():
    log('FILL start (renderers=%d) pending=%s' % (count_renderers(), [s for _, s in PENDING]))
    deadline = time.time() + 5 * 3600
    while time.time() < deadline:
        n = count_renderers()
        pending_left = [(name, shot) for name, shot in PENDING if name not in STARTED]
        if n < MAX_RENDERERS and pending_left:
            name, shot = pending_left[0]
            p = subprocess.run(['schtasks', '/Run', '/TN', name],
                               capture_output=True, text=True,
                               encoding='utf-8', errors='replace')
            STARTED.add(name)
            log('start %s (%s) rc=%s renderers_before=%d' % (name, shot, p.returncode, n))
        else:
            log('wait: renderers=%d started=%d/%d' % (n, len(STARTED), len(PENDING)))
        if len(STARTED) == len(PENDING):
            still = [name for name, _ in PENDING if task_state(name) == 'running']
            if not still and count_renderers() <= MAX_RENDERERS - 1:
                log('all re-renders finished; FILL exit')
                return
        time.sleep(60)
    log('FILL timeout')


if __name__ == '__main__':
    main()
