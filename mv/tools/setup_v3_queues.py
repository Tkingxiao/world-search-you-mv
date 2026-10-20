"""Start the v3 re-render as 7 balanced scheduled-task queues (immune to turn cleanup).

s02 is already rendered with the v3 camera (no handheld noise); every other shot is
re-rendered here. Long pole s13 gets its own queue so it never blocks another shot.
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')

QUEUES = [
    ('A', 's13'),
    ('B', 's11,s15,s01'),
    ('C', 's10,s09'),
    ('D', 's08,s06'),
    ('E', 's05,s14'),
    ('F', 's07,s12'),
    ('G', 's03,s04'),
]


def make_bat(tag, shots):
    b = os.path.join(JOBS, 'run_V3%s.bat' % tag)
    out = os.path.join(JOBS, 'dispatch_V3%s.out' % tag)
    lines = [
        '@echo off',
        'cd /d "%s"' % MV,
        'echo [V3] queue %s shots=%s start %%DATE%% %%TIME%% >> "%s"' % (tag, shots, out),
        '"%s" "%s" --shots %s --tag V3%s >> "%s" 2>&1' % (
            sys.executable, os.path.join(MV, 'mv', 'tools', 'render_queue.py'),
            shots, tag, out),
        'echo [V3] queue %s DONE %%DATE%% %%TIME%% >> "%s"' % (tag, out),
    ]
    with open(b, 'w', encoding='ascii') as f:
        f.write('\r\n'.join(lines) + '\r\n')
    return b


for tag, shots in QUEUES:
    b = make_bat(tag, shots)
    subprocess.run(['schtasks', '/Create', '/TN', 'MVv3_' + tag, '/TR', '"%s"' % b,
                    '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED'],
                   capture_output=True, text=True)
    subprocess.run(['schtasks', '/Run', '/TN', 'MVv3_' + tag], capture_output=True, text=True)
    print('[v3] started %s -> %s' % (tag, shots))
