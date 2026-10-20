"""Re-balance the v3 queue: the old V2B (s05,s13,s02,s03) is serial and s13 is the
long pole (~90 min). Split the tail into three parallel scheduled tasks so the GPU is
not idle behind s13.

  V3S05 -> s05
  V3S13 -> s13
  V3S23 -> s02,s03
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')

QUEUES = [
    ('V3S05', 's05'),
    ('V3S13', 's13'),
    ('V3S23', 's02,s03'),
]


def make_bat(tag, shots):
    b = os.path.join(JOBS, 'run_%s.bat' % tag)
    out = os.path.join(JOBS, 'dispatch_%s.out' % tag)
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        'echo [V3] queue %s shots=%s start %%DATE%% %%TIME%% >> "%s"' % (tag, shots, out),
        '"%s" "%s" --shots %s --tag %s >> "%s" 2>&1' % (
            sys.executable, os.path.join(MV, 'mv', 'tools', 'render_queue.py'),
            shots, tag, out),
        'echo [V3] queue %s DONE %%DATE%% %%TIME%% >> "%s"' % (tag, out),
    ]
    with open(b, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return b


def task_name(tag):
    return 'MVv3_%s' % tag


for tag, shots in QUEUES:
    b = make_bat(tag, shots)
    subprocess.run(['schtasks', '/Create', '/TN', task_name(tag), '/TR', '"%s"' % b,
                    '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED'],
                   capture_output=True, text=True)
    subprocess.run(['schtasks', '/Run', '/TN', task_name(tag)],
                   capture_output=True, text=True)
    print('[v3] started %s -> %s' % (tag, shots))

# the old serial queue would duplicate s05/s13: stop it (s05 is re-rendered by V3S05)
subprocess.run(['schtasks', '/End', '/TN', 'MVv2_V2B'], capture_output=True, text=True)
print('[v3] ended MVv2_V2B (was rendering s05)')
