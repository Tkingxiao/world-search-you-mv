"""Start the 1080p60 / 10spp film render as 3 scheduled-task queues.

Groups are balanced by estimated shot cost; the task is disabled immediately after
launch, so it cannot fire again at the scheduled time while the queue keeps running.

  python mv/tools/setup_1080p_tasks.py --run
  python mv/tools/setup_1080p_tasks.py --status
  python mv/tools/setup_1080p_tasks.py --stop
"""
import argparse
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
RENDER_QUEUE = os.path.join(MV, 'mv', 'tools', 'render_queue.py')
FINALIZE_SCRIPT = os.path.join(MV, 'mv', 'tools', 'finalize_and_clean_1080p.py')

GROUPS = [
    ('A', 's12,s13,s06,s04,s01'),
    ('B', 's10,s11,s05,s03,s09'),
    ('C', 's08,s07,s15,s14,s02'),
]


def task_name(tag):
    return 'MVV4_' + tag


def make_bat(tag, shots):
    path = os.path.join(JOBS, 'run_V4_%s.bat' % tag)
    out = os.path.join(JOBS, 'dispatch_V4_%s.out' % tag)
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        'echo [V4] queue %s shots=%s start %%DATE%% %%TIME%% >> "%s"' % (tag, shots, out),
        '"%s" "%s" --shots %s --tag V4%s >> "%s" 2>&1' % (
            sys.executable, RENDER_QUEUE, shots, tag, out),
        'echo [V4] queue %s DONE %%DATE%% %%TIME%% >> "%s"' % (tag, out),
    ]
    os.makedirs(JOBS, exist_ok=True)
    with open(path, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return path


def create(tag, shots):
    bat = make_bat(tag, shots)
    cmd = ['schtasks', '/Create', '/TN', task_name(tag), '/TR', '"%s"' % bat,
           '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    msg = (p.stdout or p.stderr or '').strip()
    msg = msg.encode('ascii', 'replace').decode('ascii')
    print('[create] %s rc=%s %s' % (tag, p.returncode, msg[-120:]))
    return p.returncode == 0


def make_finalize_bat():
    path = os.path.join(JOBS, 'run_V4_Finalize.bat')
    out = os.path.join(JOBS, 'dispatch_V4_Finalize.out')
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        'echo [V4] finalize start %%DATE%% %%TIME%% >> "%s"' % out,
        '"%s" "%s" >> "%s" 2>&1' % (sys.executable, FINALIZE_SCRIPT, out),
        'echo [V4] finalize DONE %%DATE%% %%TIME%% >> "%s"' % out,
        'schtasks /Change /TN "MVV4_Finalize" /DISABLE >nul 2>&1',
    ]
    os.makedirs(JOBS, exist_ok=True)
    with open(path, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return path


def create_finalize():
    bat = make_finalize_bat()
    cmd = ['schtasks', '/Create', '/TN', task_name('Finalize'), '/TR', '"%s"' % bat,
           '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    msg = (p.stdout or p.stderr or '').strip()
    msg = msg.encode('ascii', 'replace').decode('ascii')
    print('[create] Finalize rc=%s %s' % (p.returncode, msg[-120:]))
    return p.returncode == 0


def start(tag):
    run = subprocess.run(['schtasks', '/Run', '/TN', task_name(tag)],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    msg = (run.stdout or run.stderr or '').strip()
    msg = msg.encode('ascii', 'replace').decode('ascii')
    print('[run] %s rc=%s %s' % (tag, run.returncode, msg[-120:]))
    # Prevent the 23:59 trigger from launching a second instance; disabling a task
    # does not stop the instance that is already running.
    off = subprocess.run(['schtasks', '/Change', '/TN', task_name(tag), '/DISABLE'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[disable] %s rc=%s' % (tag, off.returncode))


def status():
    for tag, shots in GROUPS:
        p = subprocess.run(['schtasks', '/Query', '/TN', task_name(tag), '/FO', 'LIST'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        msg = (p.stdout or p.stderr or '').strip()
        msg = msg.encode('ascii', 'replace').decode('ascii')
        print('---', task_name(tag), '---')
        print(msg[-400:])
        for s in shots.split(','):
            f = os.path.join(SHOTS, s + '.mp4')
            print('%-4s %s' % (s, ('%d MB' % (os.path.getsize(f) / 1e6)) if os.path.exists(f) else 'MISSING'))


def stop():
    for tag, _ in GROUPS:
        subprocess.run(['schtasks', '/End', '/TN', task_name(tag)],
                       capture_output=True, text=True)
    subprocess.run(['schtasks', '/End', '/TN', task_name('Finalize')],
                   capture_output=True, text=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--finalize', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--stop', action='store_true')
    a = ap.parse_args()
    if a.run:
        for tag, shots in GROUPS:
            if create(tag, shots):
                start(tag)
    elif a.finalize:
        if create_finalize():
            start('Finalize')
    elif a.status:
        status()
    elif a.stop:
        stop()
    else:
        for tag, shots in GROUPS:
            print('%s -> %s' % (task_name(tag), shots))
