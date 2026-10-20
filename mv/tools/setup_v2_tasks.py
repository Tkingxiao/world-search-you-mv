"""Set up v2 renders as Windows scheduled tasks (immune to DSH turn/job cleanup).

Plan: 15 shots in 4 balanced serial queues. Each queue is one python driver
(mv/tools/render_queue.py) which renders its shots one by one via headless Blender.

Usage:
  python mv/tools/setup_v2_tasks.py           # create tasks only
  python mv/tools/setup_v2_tasks.py --run     # create + start all queues
  python mv/tools/setup_v2_tasks.py --status  # print task states + shot mp4 status
  python mv/tools/setup_v2_tasks.py --stop    # end all tasks
"""
import argparse
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')

QUEUES = [
    ('V2A', 's11,s10,s01,s09'),
    ('V2B', 's05,s13,s02,s03'),
    ('V2C', 's08,s12,s04,s06'),
    ('V2D', 's07,s15,s14'),
]

PLAN = {  # shot -> frames (60fps)
    's01': 360, 's02': 502, 's03': 837, 's04': 753, 's05': 1638,
    's06': 883, 's07': 1610, 's08': 1642, 's09': 885, 's10': 1658,
    's11': 1660, 's12': 1598, 's13': 1638, 's14': 881, 's15': 1176,
}


def bat_path(tag):
    return os.path.join(JOBS, 'run_%s.bat' % tag)


def make_bat(tag, shots):
    log = os.path.join(JOBS, 'queue_%s.log' % tag)
    out = os.path.join(JOBS, 'dispatch_%s.out' % tag)
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        'echo [V2] queue %s shots=%s start %%DATE%% %%TIME%% >> "%s"' % (tag, shots, out),
        '"%s" "%s" --shots %s --tag %s >> "%s" 2>&1' % (
            sys.executable, os.path.join(MV, 'mv', 'tools', 'render_queue.py'),
            shots, tag, out),
        'echo [V2] queue %s DONE %%DATE%% %%TIME%% >> "%s"' % (tag, out),
    ]
    with open(bat_path(tag), 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return bat_path(tag)


def task_name(tag):
    return 'MVv2_%s' % tag


def create(tag, shots):
    b = make_bat(tag, shots)
    cmd = ['schtasks', '/Create', '/TN', task_name(tag), '/TR', '"%s"' % b,
           '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[create] %s rc=%s %s' % (tag, p.returncode, (p.stdout or p.stderr).strip()[-120:]))
    return p.returncode == 0


def run_task(tag):
    p = subprocess.run(['schtasks', '/Run', '/TN', task_name(tag)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[run] %s rc=%s %s' % (tag, p.returncode, (p.stdout or p.stderr).strip()[-120:]))


def status():
    print('--- tasks ---')
    for tag, shots in QUEUES:
        p = subprocess.run(['schtasks', '/Query', '/TN', task_name(tag), '/FO', 'LIST'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        state = '?'
        for line in (p.stdout or '').splitlines():
            if 'Status' in line or '状态' in line:
                state = line.split(':', 1)[-1].strip()
        print('%-5s %-22s %s' % (tag, shots, state))
    print('--- shots ---')
    done = 0
    for s in sorted(PLAN):
        f = os.path.join(SHOTS, s + '.mp4')
        if os.path.exists(f):
            sz = os.path.getsize(f)
            try:
                pr = subprocess.run([r'C:\ffmpeg\bin\ffprobe.exe', '-v', 'error',
                                     '-count_frames', '-select_streams', 'v:0',
                                     '-show_entries', 'stream=nb_read_frames',
                                     '-of', 'csv=p=0', f],
                                    capture_output=True, text=True, timeout=120)
                nf = int((pr.stdout or '0').strip() or 0)
            except Exception:
                nf = -1
            ok = 'OK' if nf == PLAN[s] else 'PARTIAL(%s)' % nf
            if nf == PLAN[s]:
                done += 1
            print('%-4s %10.1f MB  %s' % (s, sz / 1e6, ok))
        else:
            print('%-4s %s' % (s, 'MISSING'))
    print('done %d / %d shots' % (done, len(PLAN)))


def stop_all():
    for tag, _ in QUEUES:
        subprocess.run(['schtasks', '/End', '/TN', task_name(tag)],
                       capture_output=True, text=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--stop', action='store_true')
    a = ap.parse_args()
    if a.status:
        status()
        sys.exit(0)
    if a.stop:
        stop_all()
        print('stopped all v2 tasks')
        sys.exit(0)
    for tag, shots in QUEUES:
        create(tag, shots)
    if a.run:
        for tag, _ in QUEUES:
            run_task(tag)
    print('tasks created' + (' and started' if a.run else ''))
