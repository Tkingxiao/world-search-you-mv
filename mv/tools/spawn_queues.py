"""spawn_queues.py - start render queues as DETACHED processes.

Background jobs launched through the harness are killed when the chat turn is
interrupted; a detached process keeps rendering regardless. Logs:
  mv/out/jobs/dispatch_<tag>.out
Each queue is exactly one blender render at a time.
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

QUEUES = [
    ('J', 's03,s06,s09'),
    ('K', 's10,s11'),
    ('L', 's15,s14'),
    ('M', 's04,s07'),
]

extra = [a for a in sys.argv[1:]]
if extra:
    # allow ad-hoc queues: python spawn_queues.py N s05,s08,s01
    QUEUES.append((extra[0], extra[1]))

os.makedirs(JOBS, exist_ok=True)
for tag, shots in QUEUES:
    outpath = os.path.join(JOBS, 'dispatch_%s.out' % tag)
    out = open(outpath, 'w', encoding='utf-8')
    p = subprocess.Popen(
        [PY, os.path.join(MV, 'mv', 'tools', 'render_queue.py'),
         '--shots', shots, '--tag', tag],
        cwd=MV, stdout=out, stderr=subprocess.STDOUT,
        creationflags=FLAGS, close_fds=True)
    print('spawned queue %s (%s) pid=%s' % (tag, shots, p.pid))
print('done')
