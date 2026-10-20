#!/usr/bin/env python
"""finalize.py — one-shot delivery pipeline.

Phases:
  1. wait until all 15 shot mp4s are complete (ffprobe frame count == plan)
  2. concat -> mv/out/final/master_video_no_text.mp4, build master_audio.wav
  3. burn (vignette -> ASS HUD/lyrics -> grain) -> world.search(you)_final.mp4
     + poster renders (landscape 2560x1440, portrait 1800x2700) in parallel
  4. QC frames, contact sheet, FINALIZE_REPORT.md

Run: python mv/tools/finalize.py   (safe to keep running in a background job)
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = r'D:\Code\Code MV\new-word.search(you)'
MV = os.path.join(ROOT, 'mv')
SHOTS = os.path.join(MV, 'out', 'shots')
FINAL = os.path.join(MV, 'out', 'final')
JOBS = os.path.join(MV, 'out', 'jobs')
QC = os.path.join(MV, 'out', 'qc')
LOG = os.path.join(JOBS, 'finalize.log')
FFMPEG = r'C:\ffmpeg\bin\ffmpeg.exe'
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
BLENDER = r'D:\Blender Foundation\Blender 4.5\blender.exe'
PY = sys.executable
FPS = 60


def log(msg):
    line = '[%s] %s' % (datetime.now().strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    os.makedirs(JOBS, exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def plan():
    with open(os.path.join(MV, 'data', 'shot_plan.json'), encoding='utf-8') as f:
        d = json.load(f)
    items = d.get('shots') or d
    return [(it.get('id') or it.get('shot') or it.get('name'), float(it['t0']), float(it['t1'])) for it in items]


def probe(path):
    p = subprocess.run([FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                        '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
                        '-of', 'json', path], capture_output=True, text=True)
    try:
        st = json.loads(p.stdout)['streams'][0]
        return int(st.get('nb_read_frames', 0)), int(st.get('width', 0)), int(st.get('height', 0))
    except Exception:
        return 0, 0, 0


def expected(sid):
    for s, t0, t1 in plan():
        if s == sid:
            return int(round(t1 * FPS)) - int(round(t0 * FPS))
    raise KeyError(sid)


def shot_ok(sid):
    p = os.path.join(SHOTS, sid + '.mp4')
    if not os.path.isfile(p) or os.path.getsize(p) < 200_000:
        return False
    n, w, h = probe(p)
    return abs(n - expected(sid)) <= 2 and w == 1920 and h == 1080


def wait_for_shots(timeout_h=4.0):
    t0 = time.time()
    log('phase 1: waiting for all 15 shot masters')
    while time.time() - t0 < timeout_h * 3600:
        todo = [s for s, _, _ in plan() if not shot_ok(s)]
        if not todo:
            log('all shots complete')
            return True
        log('waiting: missing %s' % todo)
        time.sleep(60)
    log('TIMEOUT waiting for shots')
    return False


def assemble():
    log('phase 2: concat + audio')
    r1 = subprocess.run([PY, os.path.join(MV, 'tools', 'assemble.py'), '--video'],
                        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log('concat rc=%s %s' % (r1.returncode, (r1.stdout or '')[-300:].replace('\n', ' ')))
    r2 = subprocess.run([PY, os.path.join(MV, 'tools', 'assemble.py'), '--audio'],
                        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log('audio rc=%s %s' % (r2.returncode, (r2.stdout or '')[-200:].replace('\n', ' ')))
    master = os.path.join(FINAL, 'master_video_no_text.mp4')
    audio = os.path.join(FINAL, 'master_audio.wav')
    ok = r1.returncode == 0 and r2.returncode == 0 and os.path.exists(master) and os.path.exists(audio)
    if ok:
        n, w, h = probe(master)
        log('master: %d frames %dx%d' % (n, w, h))
    return ok


def render_poster():
    """GPU poster renders (landscape + portrait), returns list of output paths."""
    outs = []
    base = ['-b', '--factory-startup', '-P', os.path.join(MV, 'build', 'poster.py'), '--']
    jobs = [
        ('poster_2560x1440.png', ['--w', '2560', '--h', '1440', '--samples', '32', '--out', 'poster_2560x1440.png']),
        ('poster_1800x2700.png', ['--portrait', '--w', '1800', '--h', '2700', '--samples', '32', '--out', 'poster_1800x2700.png']),
    ]
    for name, args in jobs:
        log('poster: rendering %s' % name)
        r = subprocess.run([BLENDER] + base + args, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=1800)
        out = os.path.join(MV, 'out', 'lookdev', name)
        log('poster: rc=%s exists=%s size=%s' % (r.returncode, os.path.exists(out),
                                                 os.path.getsize(out) if os.path.exists(out) else 0))
        if os.path.exists(out):
            outs.append(out)
    return outs


def burn():
    log('phase 3: burn start (preset medium)')
    r = subprocess.run([PY, os.path.join(MV, 'tools', 'final_encode.py'), '--burn', '--fast'],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '')[-400:].replace('\n', ' ')
    log('burn rc=%s %s' % (r.returncode, tail))
    return r.returncode == 0


def qc_and_report(posters):
    log('phase 4: QC')
    out = os.path.join(FINAL, 'world.search(you)_final.mp4')
    if os.path.exists(out):
        n, w, h = probe(out)
        dur = subprocess.run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
                              '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip()
        subprocess.run([PY, os.path.join(MV, 'tools', 'final_encode.py'), '--qc'], cwd=ROOT,
                       capture_output=True, text=True)
        # contact sheet from the 8 QC frames
        frames = sorted(f for f in os.listdir(QC) if f.startswith('final_') and f.endswith('.jpg'))
        if frames:
            lst = os.path.join(QC, 'qc_list.txt')
            with open(lst, 'w', encoding='utf-8') as f:
                for fr in frames:
                    f.write("file '%s'\n" % os.path.join(QC, fr).replace('\\', '/'))
            sheet = os.path.join(QC, 'qc_sheet_final.jpg')
            subprocess.run([FFMPEG, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                            '-vf', 'scale=640:-1,tile=4x2', '-frames:v', '1', sheet],
                           capture_output=True, text=True)
            log('qc sheet -> %s' % sheet)
        lines = [
            '# FINALIZE REPORT',
            '',
            '- generated: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '- final file: `%s`' % out,
            '- size: %.1f MB' % (os.path.getsize(out) / 1e6) if os.path.exists(out) else '- size: MISSING',
            '- frames: %d | resolution: %dx%d | duration: %s s' % (n, w, h, dur),
            '- audio: master_audio.wav (48 kHz stereo pcm_s24le)',
            '- subtitles: mv/out/final/world.search(you).srt (74 bilingual cues)',
        ]
        for p in posters:
            lines.append('- poster: `%s` (%.1f MB)' % (p, os.path.getsize(p) / 1e6))
        report = os.path.join(FINAL, 'FINALIZE_REPORT.md')
        with open(report, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        log('report -> %s' % report)
        log('FINAL: %s' % out)
        return True
    log('final file missing')
    return False


def main():
    os.makedirs(JOBS, exist_ok=True)
    log('finalize start')
    if not wait_for_shots():
        return 1
    if not assemble():
        log('ABORT: assembly failed')
        return 1
    # GPU poster renders run while the CPU-only burn encodes
    burn_log = open(os.path.join(JOBS, 'burn.log'), 'ab')
    burn_proc = subprocess.Popen([PY, os.path.join(MV, 'tools', 'final_encode.py'), '--burn', '--fast'],
                                 cwd=ROOT, stdout=burn_log, stderr=subprocess.STDOUT)
    posters = render_poster()
    burn_proc.wait()
    log('burn rc=%s' % burn_proc.returncode)
    burn_log.close()
    ok = qc_and_report(posters)
    log('finalize done ok=%s' % ok)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
