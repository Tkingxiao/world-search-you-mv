"""assemble.py - concat shot mp4s in film order, verify frame counts, mux audio.

Usage:
  python mv/tools/assemble.py --check          # verify each shot mp4 exists + frame count
  python mv/tools/assemble.py --video          # concat -> mv/out/final/master_video_no_text.mp4
  python mv/tools/assemble.py --audio          # audio -> mv/out/final/master_audio.wav
  python mv/tools/assemble.py --all

Order comes from mv/data/shot_plan.json ("shots": [{id, t0, t1}]). Every shot must
have exactly round(t1*60)-round(t0*60) frames or the result is reported as MISMATCH
(concat still proceeds but timeline drift is printed).
"""
import argparse
import json
import os
import subprocess
import sys

MV = r'D:\Code\Code MV\new-word.search(you)'
FFMPEG = r'C:\ffmpeg\bin\ffmpeg.exe'
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
FINAL = os.path.join(MV, 'mv', 'out', 'final')
PLAN = os.path.join(MV, 'mv', 'data', 'shot_plan.json')
WAV = os.path.join(MV, 'mv', 'ref', 'song44100.wav')
FPS = 60


def plan():
    with open(PLAN, encoding='utf-8') as f:
        d = json.load(f)
    items = d.get('shots') or d
    out = []
    for it in items:
        sid = it.get('id') or it.get('shot') or it.get('name')
        t0, t1 = float(it['t0']), float(it['t1'])
        out.append((sid, t0, t1, int(round(t1 * FPS)) - int(round(t0 * FPS))))
    return out


def profile():
    with open(PLAN, encoding='utf-8') as f:
        d = json.load(f)
    return int(d.get('width', 1920)), int(d.get('height', 1080))


def probe_frames(path):
    p = subprocess.run([FFPROBE, '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                        '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
                        '-of', 'json', path], capture_output=True, text=True)
    try:
        st = json.loads(p.stdout)['streams'][0]
    except Exception:
        return None
    return {'frames': int(st.get('nb_read_frames', 0)), 'w': int(st.get('width', 0)),
            'h': int(st.get('height', 0)), 'fps': st.get('r_frame_rate', '')}


def check(verbose=True):
    total = 0
    bad = []
    pw, ph = profile()
    for sid, t0, t1, frames in plan():
        path = os.path.join(SHOTS, sid + '.mp4')
        total += frames
        if not os.path.exists(path) or os.path.getsize(path) < 10000:
            bad.append((sid, 'MISSING', frames, 0))
            if verbose:
                print('%-4s MISSING (expect %d frames)' % (sid, frames))
            continue
        info = probe_frames(path)
        if not info:
            bad.append((sid, 'UNREADABLE', frames, 0))
            continue
        if info['frames'] != frames:
            bad.append((sid, 'COUNT', frames, info['frames']))
            if verbose:
                print('%-4s COUNT MISMATCH expect %d got %d' % (sid, frames, info['frames']))
        elif info['w'] != pw or info['h'] != ph:
            bad.append((sid, 'RES', (pw, ph), (info['w'], info['h'])))
            if verbose:
                print('%-4s RES MISMATCH expect %dx%d got %dx%d' % (
                    sid, pw, ph, info['w'], info['h']))
        else:
            if verbose:
                print('%-4s ok  %4d frames  %dx%d@%s' % (sid, frames, info['w'], info['h'], info['fps']))
    print('TOTAL expected %d frames = %.3fs | shots ready %d/%d' % (
        total, total / FPS, len(plan()) - len(bad), len(plan())))
    return bad


def concat_video():
    items = [sid for sid, *_ in plan()]
    missing = [s for s in items if not os.path.exists(os.path.join(SHOTS, s + '.mp4'))]
    if missing:
        print('cannot concat, missing:', missing)
        return False
    os.makedirs(FINAL, exist_ok=True)
    lst = os.path.join(FINAL, 'concat_list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for s in items:
            f.write("file '%s'\n" % os.path.join(SHOTS, s + '.mp4').replace('\\', '/'))
    out = os.path.join(FINAL, 'master_video_no_text.mp4')
    cmd = [FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
           '-movflags', '+faststart', out]
    print(' '.join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(p.stdout[-800:])
    if p.returncode != 0:
        print(p.stderr[-2000:])
        return False
    print('video ->', out, probe_frames(out))
    return True


def make_audio():
    os.makedirs(FINAL, exist_ok=True)
    out = os.path.join(FINAL, 'master_audio.wav')
    cmd = [FFMPEG, '-y', '-i', WAV, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', out]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print(p.stderr[-600:])
    print('audio ->', out, os.path.getsize(out) if os.path.exists(out) else 'FAIL')
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--video', action='store_true')
    ap.add_argument('--audio', action='store_true')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    if a.check or a.all:
        check()
    if a.video or a.all:
        concat_video()
    if a.audio or a.all:
        make_audio()
