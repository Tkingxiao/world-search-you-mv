"""Prepare (but do not start) two extra tasks for s02 / s03 so they can be pulled out of
the slow V2B queue once s13 finishes."""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
PY = sys.executable

JOBS_TO_CREATE = [('V2S2', 's02'), ('V2S3', 's03')]


def make_bat(tag, shots):
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


for tag, shots in JOBS_TO_CREATE:
    bat = make_bat(tag, shots)
    p = subprocess.run(['schtasks', '/Create', '/TN', 'MVv2_%s' % tag, '/TR', '"%s"' % bat,
                        '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[create] %s rc=%s' % (tag, p.returncode))
print('ready (not started)')
