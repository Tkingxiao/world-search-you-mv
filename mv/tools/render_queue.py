"""render_queue.py - render a list of shots sequentially in one background process.

Usage:
  python mv/tools/render_queue.py --shots s03,s06,s09,s12 --tag A [--force] [--skip-existing]
  python mv/tools/render_queue.py --shots s05,s07,s08 --tag B

Each shot runs its own `blender -b -P mv/build/render_shot.py -- --shot sNN`
so a failure of one shot does not kill the queue. Progress is appended to
mv/out/jobs/queue_<tag>.log; finished shots are reported with frame counts.
"""
import argparse
import json
import os
import subprocess
import sys
import time

MV = r'D:\Code\Code MV\new-word.search(you)'
BLENDER = r'D:\Blender Foundation\Blender 4.5\blender.exe'
RENDER = os.path.join(MV, 'mv', 'build', 'render_shot.py')
OUT = os.path.join(MV, 'mv', 'out', 'shots')
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
PLAN = os.path.join(MV, 'mv', 'data', 'shot_plan.json')


def log(path, msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', required=True)
    ap.add_argument('--tag', default='A')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--skip-existing', action='store_true')
    a = ap.parse_args()

    os.makedirs(JOBS, exist_ok=True)
    logfile = os.path.join(JOBS, 'queue_%s.log' % a.tag)
    shots = [s.strip() for s in a.shots.split(',') if s.strip()]
    log(logfile, 'QUEUE %s start: %s' % (a.tag, ','.join(shots)))

    for shot in shots:
        mp4 = os.path.join(OUT, shot + '.mp4')
        if a.skip_existing and os.path.exists(mp4) and os.path.getsize(mp4) > 10000:
            log(logfile, '%s SKIP (exists, %d bytes)' % (shot, os.path.getsize(mp4)))
            continue
        mod = os.path.join(MV, 'mv', 'build', 'shot_%s.py' % shot)
        if not os.path.exists(mod):
            log(logfile, '%s MISSING MODULE %s' % (shot, mod))
            continue
        t = time.time()
        cmd = [BLENDER, '-b', '--factory-startup', '-P', RENDER, '--', '--shot', shot]
        log(logfile, '%s BEGIN' % shot)
        # stream blender stdout to a per-shot log so live progress / s-per-frame is
        # observable while the queue runs (capture_output=True hid it until the end).
        shotlog = os.path.join(JOBS, 'render_%s_%s.log' % (shot, a.tag))
        try:
            with open(shotlog, 'w', encoding='utf-8', errors='replace') as sl:
                p = subprocess.Popen(cmd, cwd=MV, stdout=sl, stderr=subprocess.STDOUT)
                try:
                    rc = p.wait(timeout=7200)
                except subprocess.TimeoutExpired:
                    p.kill()
                    rc = -1
            tail = ''
            try:
                with open(shotlog, encoding='utf-8', errors='replace') as f:
                    tail = f.read()[-800:].replace('\n', ' | ')
            except Exception:
                pass
            ok = rc == 0 and os.path.exists(mp4) and os.path.getsize(mp4) > 10000
            log(logfile, '%s %s %.1fs size=%s rc=%s' % (
                shot, 'DONE' if ok else 'FAIL',
                time.time() - t,
                os.path.getsize(mp4) if os.path.exists(mp4) else '-', rc))
            if not ok:
                log(logfile, '%s TAIL: %s' % (shot, tail))
        except Exception as e:  # noqa
            log(logfile, '%s EXC %r' % (shot, e))

    log(logfile, 'QUEUE %s end' % a.tag)


if __name__ == '__main__':
    main()
