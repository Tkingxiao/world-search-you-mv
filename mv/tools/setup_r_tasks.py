"""Create the three re-render tasks (s05/s07/s08 with the fixed specimen labels) and a
filler task that starts them as soon as a render slot frees up.

Tasks:
  MVv2_V2R1..3   one shot each (created, not started)
  MVv2_FILL      polls every 60 s; whenever fewer than 4 MVv2_* render tasks are Running
                 it starts the next pending re-render. Exits when all three finished.
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
PY = sys.executable

R_SHOTS = [('V2R1', 's05'), ('V2R2', 's07'), ('V2R3', 's08')]
WATCH = ['MVv2_V2A', 'MVv2_V2B', 'MVv2_V2C', 'MVv2_V2D']


def make_queue_bat(tag, shots):
    path = os.path.join(JOBS, 'run_%s.bat' % tag)
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        '"%s" "%s" --shots %s --tag %s >> "%s" 2>&1' % (
            PY, os.path.join(MV, 'mv', 'tools', 'render_queue.py'), shots, tag,
            os.path.join(JOBS, 'dispatch_%s.out' % tag)),
    ]
    with open(path, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return path


def make_fill_bat():
    path = os.path.join(JOBS, 'run_FILL.bat')
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        '"%s" "%s" >> "%s" 2>&1' % (
            PY, os.path.join(MV, 'mv', 'tools', 'fill_v2.py'),
            os.path.join(JOBS, 'fill_v2.out')),
    ]
    with open(path, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return path


def schtasks(args):
    return subprocess.run(['schtasks'] + args, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def create_task(name, bat):
    p = schtasks(['/Create', '/TN', name, '/TR', '"%s"' % bat, '/SC', 'ONCE',
                  '/ST', '23:59', '/F', '/RL', 'LIMITED'])
    print('[create] %s rc=%s' % (name, p.returncode))


if __name__ == '__main__':
    for tag, shot in R_SHOTS:
        create_task('MVv2_%s' % tag, make_queue_bat(tag, shot))
    create_task('MVv2_FILL', make_fill_bat())
    if '--run' in sys.argv:
        p = schtasks(['/Run', '/TN', 'MVv2_FILL'])
        print('[run] MVv2_FILL rc=%s' % p.returncode)
    print('re-render tasks + filler ready')
