#!/usr/bin/env python
"""Supervisor for the remaining shot renders (growth-aware, duplicate-safe).

Renders every shot whose mp4 is not yet complete. A shot counts as
"in progress" when its mp4 was modified in the last 150 s and is not yet
complete, so renders started by older (now dead) drivers are never
duplicated. Drivers are spawned detached + breakaway so parent tool-call
cleanup cannot kill them.

Usage: python mv/tools/supervise.py [--slots 4] [--force s01,s03]
"""
import argparse
import json
import re
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'mv', 'out')
JOBS = os.path.join(OUT, 'jobs')
SHOTS = os.path.join(OUT, 'shots')
LOG = os.path.join(JOBS, 'supervisor.log')
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
PY = sys.executable
PLAN = json.load(open(os.path.join(ROOT, 'mv', 'data', 'shot_plan.json'), encoding='utf-8'))
PLAN_SHOTS = PLAN['shots'] if isinstance(PLAN, dict) else PLAN

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
FLAGS = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP  # breakaway is denied by the job object

ALL = ['s01', 's02', 's03', 's04', 's05', 's06', 's07', 's08', 's09',
       's10', 's11', 's12', 's13', 's14', 's15']
INFLIGHT_WINDOW = 150.0  # seconds since mp4 mtime => still being written
ATTEMPTS = {}
MAX_ATTEMPTS = 3


def log(msg):
    line = '[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def expected_frames(shot):
    for s in PLAN_SHOTS:
        if s.get('id') == shot:
            return int(round(s['t1'] * 60)) - int(round(s['t0'] * 60))
    raise KeyError(shot)


def probe_frames(path):
    try:
        r = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                            '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path],
                           capture_output=True, text=True, timeout=300)
        v = r.stdout.strip().split(',')[0]
        return int(v) if v.isdigit() else -1
    except Exception:
        return -1


def mp4_path(shot):
    return os.path.join(SHOTS, shot + '.mp4')


def complete(shot):
    p = mp4_path(shot)
    if not os.path.isfile(p) or os.path.getsize(p) < 200_000:
        return False
    return abs(probe_frames(p) - expected_frames(shot)) <= 2


def in_flight(shot, now):
    p = mp4_path(shot)
    if not os.path.isfile(p):
        return False
    if complete(shot):
        return False
    if os.path.getsize(p) <= 0:
        return False
    return (now - os.path.getmtime(p)) < INFLIGHT_WINDOW


def spawn(shot):
    tag = '%s_%d' % (shot, int(time.time()) % 100000)
    old = mp4_path(shot)
    if os.path.isfile(old) and (time.time() - os.path.getmtime(old)) > INFLIGHT_WINDOW:
        try:
            os.remove(old)
            log('removed stale partial %s' % os.path.basename(old))
        except OSError as e:
            log('could not remove stale %s: %s' % (old, e))
    out = open(os.path.join(JOBS, 'dispatch_%s.out' % tag), 'ab')
    cmd = [PY, os.path.join(ROOT, 'mv', 'tools', 'render_queue.py'), '--shots', shot, '--tag', tag]
    try:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=out,
                             creationflags=FLAGS, close_fds=True)
    except OSError as e:
        log('SPAWN FAILED %s: %s' % (shot, e))
        return None, None
    log('spawn %s tag=%s pid=%s' % (shot, tag, p.pid))
    return tag, p


def planned_by_drivers():
    """Shot ids claimed by live render_queue.py drivers (avoid duplicate renders)."""
    ps = ('Get-WmiObject Win32_Process -Filter "Name=\'python.exe\'" | '
          'ForEach-Object { $_.CommandLine }')
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return set()
    planned = set()
    for line in (r.stdout or '').splitlines():
        m = re.search(r'render_queue\.py.*--shots\s+([\w,]+)', line)
        if m:
            planned.update(s.strip() for s in m.group(1).split(',') if s.strip())
    return planned



def actual_renderers():
    """Count live blender processes currently rendering a shot (any owner)."""
    ps = ('Get-WmiObject Win32_Process -Filter "Name=\'blender.exe\'" | '
          'ForEach-Object { $_.CommandLine }')
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return 0
    return sum(1 for line in (r.stdout or '').splitlines() if '--shot' in line and 'render_shot.py' in line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slots', type=int, default=4)
    ap.add_argument('--force', default='', help='comma list of shots to re-render even if complete')
    args = ap.parse_args()
    os.makedirs(JOBS, exist_ok=True)

    force = [s.strip() for s in args.force.split(',') if s.strip()]
    for s in force:
        p = mp4_path(s)
        if os.path.isfile(p):
            os.remove(p)
            log('force re-render: removed %s' % os.path.basename(p))

    log('supervisor start: slots=%d force=%s' % (args.slots, force))
    running = []  # (tag, shot, Popen)
    while True:
        now = time.time()
        # reap our own drivers
        still = []
        for tag, shot, p in running:
            if p.poll() is None:
                still.append((tag, shot, p))
                continue
            ok = complete(shot)
            log('driver done shot=%s rc=%s complete=%s' % (shot, p.returncode, ok))
            if not ok:
                ATTEMPTS[shot] = ATTEMPTS.get(shot, 0) + 1
                if ATTEMPTS[shot] >= MAX_ATTEMPTS:
                    log('GIVE UP %s after %d attempts' % (shot, ATTEMPTS[shot]))
        running = still
        ours = {s for _, s, _ in running}

        claimed = planned_by_drivers()
        pending = [s for s in ALL if not complete(s) and s not in claimed]
        busy = [s for s in pending if in_flight(s, now) and s not in ours]
        slots_busy = max(len(ours) + len(busy), actual_renderers())
        todo = [s for s in pending if s not in busy and s not in ours]

        if todo and slots_busy < args.slots:
            shot = todo[0]
            if ATTEMPTS.get(shot, 0) >= MAX_ATTEMPTS:
                log('skip %s: attempts exhausted' % shot)
            else:
                tag, p = spawn(shot)
                if p is None:
                    ATTEMPTS[shot] = ATTEMPTS.get(shot, 0) + 1
                    log('spawn failed for %s (attempts=%d) — retry in 30 s' % (shot, ATTEMPTS[shot]))
                    time.sleep(30)
                    continue
                running.append((tag, shot, p))
                time.sleep(10)
                continue

        log('tick pending=%s in_flight=%s ours=%d slots_busy=%d' % (pending, busy, len(ours), slots_busy))
        if not pending and not running:
            log('supervisor done — all shots complete')
            break
        time.sleep(30)


if __name__ == '__main__':
    main()
