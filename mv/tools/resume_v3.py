"""Resume the v3 re-render later (one command at dawn).

What it does:
  1. deletes every shot mp4 whose frame count != plan (killed renders leave moov-less files);
  2. keeps any shot that is already complete (s02 is already v3, saves ~10 min);
  3. re-creates the 7 balanced scheduled-task queues for whatever is still missing and
     starts them (immune to this session ending).

Usage:
  python mv/tools/resume_v3.py          # dry run: show what would be deleted / queued
  python mv/tools/resume_v3.py --run    # do it
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'

PLAN = {'s01': 360, 's02': 502, 's03': 837, 's04': 753, 's05': 1638, 's06': 883,
        's07': 1610, 's08': 1642, 's09': 885, 's10': 1658, 's11': 1660, 's12': 1598,
        's13': 1638, 's14': 881, 's15': 1176}

# 7 balanced groups (long pole s13 alone); filter at runtime to missing shots only
GROUPS = [
    ('A', ['s13']),
    ('B', ['s11', 's15', 's01']),
    ('C', ['s10', 's09']),
    ('D', ['s08', 's06']),
    ('E', ['s05', 's14']),
    ('F', ['s07', 's12']),
    ('G', ['s03', 's04']),
]


def frames(name):
    p = os.path.join(SHOTS, name + '.mp4')
    if not os.path.exists(p):
        return -1
    try:
        r = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                            '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', p],
                           capture_output=True, text=True, timeout=300)
        return int((r.stdout or '0').strip() or 0)
    except Exception:
        return -1


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


def main():
    do_run = '--run' in sys.argv
    print('%-4s %-8s %s' % ('shot', 'frames', 'state'))
    missing = []
    for s in sorted(PLAN):
        n = frames(s)
        if n == PLAN[s]:
            print('%-4s %-8s COMPLETE' % (s, n))
        else:
            print('%-4s %-8s will render (%s)' % (s, 'missing' if n < 0 else n, 'x'))
            missing.append(s)
            if do_run and n >= 0:
                try:
                    os.remove(os.path.join(SHOTS, s + '.mp4'))
                    print('      deleted stale %s.mp4' % s)
                except OSError as e:
                    print('      could not delete: %s' % e)

    if not missing:
        print('\nAll 15 shots complete - nothing to render. Next: assemble + burn.')
        return

    print('\nqueues:')
    for tag, shots in GROUPS:
        todo = [s for s in shots if s in missing]
        if not todo:
            continue
        print('  V3%s -> %s' % (tag, ','.join(todo)))
        if do_run:
            b = make_bat(tag, ','.join(todo))
            subprocess.run(['schtasks', '/Create', '/TN', 'MVv3_' + tag, '/TR', '"%s"' % b,
                            '/SC', 'ONCE', '/ST', '23:59', '/F', '/RL', 'LIMITED'],
                           capture_output=True, text=True)
            subprocess.run(['schtasks', '/Run', '/TN', 'MVv3_' + tag],
                           capture_output=True, text=True)
    print('\n%s' % ('STARTED' if do_run else 'dry run only - pass --run to start'))


if __name__ == '__main__':
    main()
