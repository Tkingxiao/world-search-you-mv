"""start_v2.py - spawn DETACHED render queues for the v2 (quality pass) re-render.

Usage:
  python mv/tools/start_v2.py P1 s01,s02,s03,s04
  python mv/tools/start_v2.py            # spawn the default lead-owned queues

Detached (+ breakaway) so an interrupted chat turn cannot kill the renders.
Each queue is one blender process at a time; logs in mv/out/jobs/dispatch_<tag>.out
"""
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
PY = sys.executable
JOBS = os.path.join(MV, 'mv', 'out', 'jobs')
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
FLAGS = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB

# lead-owned v2 queues (mine first, teammates' shots appended when frozen)
PLAN = [
    ('P1', 's01,s02,s03,s04'),
    ('P2', 's06,s09'),
    ('P3', 's11,s12'),
]

args = sys.argv[1:]
queues = [tuple(args[:2])] if len(args) >= 2 else PLAN

os.makedirs(JOBS, exist_ok=True)
for tag, shots in queues:
    outpath = os.path.join(JOBS, 'dispatch_%s.out' % tag)
    out = open(outpath, 'w', encoding='utf-8')
    p = subprocess.Popen(
        [PY, os.path.join(MV, 'mv', 'tools', 'render_queue.py'),
         '--shots', shots, '--tag', tag],
        cwd=MV, stdout=out, stderr=subprocess.STDOUT,
        creationflags=FLAGS, close_fds=True)
    print('%s -> %s pid=%s shots=%s' % (tag, outpath, p.pid, shots), flush=True)
