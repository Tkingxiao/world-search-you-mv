"""Late-stage v3 rebalance: create/run single-purpose queue tasks on demand.

  python mv/tools/rebalance_v3_tasks.py create V3S10 s10
  python mv/tools/rebalance_v3_tasks.py run    V3S10
  python mv/tools/rebalance_v3_tasks.py end    MVv2_V2A

Kept generic so the tail of the render can be re-planned without editing setup scripts.
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')


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


cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 'create':
    tag, shots = sys.argv[2], sys.argv[3]
    b = make_bat(tag, shots)
    r = subprocess.run(['schtasks', '/Create', '/TN', 'MVv3_' + tag, '/TR', '"%s"' % b,
                        '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[create] %s rc=%s %s' % (tag, r.returncode, (r.stdout or r.stderr).strip()[-100:]))
elif cmd == 'run':
    tag = sys.argv[2]
    r = subprocess.run(['schtasks', '/Run', '/TN', 'MVv3_' + tag],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[run] %s rc=%s %s' % (tag, r.returncode, (r.stdout or r.stderr).strip()[-100:]))
elif cmd == 'end':
    name = sys.argv[2]
    r = subprocess.run(['schtasks', '/End', '/TN', name],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('[end] %s rc=%s %s' % (name, r.returncode, (r.stdout or r.stderr).strip()[-100:]))
elif cmd == 'status':
    for tag in sys.argv[2:]:
        r = subprocess.run(['schtasks', '/Query', '/TN', 'MVv3_' + tag, '/FO', 'LIST'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(tag, '->', (r.stdout or r.stderr).strip()[-200:])
else:
    print('usage: create TAG SHOTS | run TAG | end TASKNAME | status TAG...')
