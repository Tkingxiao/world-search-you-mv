"""final_encode.py - assemble all shots, mux audio, burn subtitles/HUD + film grade.

Usage:
  python mv/tools/final_encode.py --check          # verify shot mp4s + frame counts
  python mv/tools/final_encode.py --concat         # concat -> master_video_no_text.mp4
  python mv/tools/final_encode.py --burn [--fast]  # ass + vignette + grain -> final mp4
  python mv/tools/final_encode.py --qc             # extract 6 QC frames from the final

The burn chain order is: vignette (before subtitles so HUD stays crisp) ->
ass (fonts from mv/overlay/fonts) -> film grain.
"""
import argparse
import json
import os
import subprocess

MV = r'D:\Code\Code MV\new-word.search(you)'
FFMPEG = r'C:\ffmpeg\bin\ffmpeg.exe'
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
FINAL = os.path.join(MV, 'mv', 'out', 'final')
MASTER = os.path.join(FINAL, 'master_video_no_text.mp4')
AUDIO = os.path.join(FINAL, 'master_audio.wav')
ASS = os.path.join(MV, 'mv', 'overlay', 'film.ass')
FONTS = os.path.join(MV, 'mv', 'overlay', 'fonts')
OUT = os.path.join(FINAL, 'world.search(you)_final_v4.mp4')

OVERLAY = os.path.join(MV, 'mv', 'overlay')

# Grade B (ui-lab prototype): split-tone -- shadows cooler, highlights warmer -- then
# vignette, subtitles/HUD, film grain. The burn runs with cwd=mv/overlay and refers to
# film.ass / fonts relatively: ffmpeg's filtergraph parser cannot handle the spaces in
# this project's absolute path.
VF_GRADE = ("colorbalance=rs=-0.04:gs=0.0:bs=0.04:rh=0.03:gh=0.0:bh=-0.03,"
            "vignette=angle=PI/7,"
            "ass=film.ass:fontsdir=fonts,"
            "noise=alls=7:allf=t+u")


def run(cmd, tail=1500, cwd=None):
    print(' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=cwd or MV, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if p.returncode != 0:
        print('FAILED rc=%s' % p.returncode)
        print((p.stderr or '')[-tail:])
        return False
    if p.stderr:
        print((p.stderr or '')[-400:])
    return True


def burn(fast=False):
    if not (os.path.exists(MASTER) and os.path.exists(AUDIO)):
        print('missing master/audio')
        return False
    preset = 'medium' if fast else 'slow'
    cmd = [FFMPEG, '-y', '-v', 'warning',
           '-i', MASTER, '-i', AUDIO,
           '-map', '0:v:0', '-map', '1:a:0',
           '-vf', VF_GRADE,
           '-c:v', 'libx264', '-preset', preset, '-crf', '16',
           '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '5.1',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
           '-c:a', 'aac', '-b:a', '320k', '-ar', '48000',
           '-movflags', '+faststart', OUT]
    ok = run(cmd, cwd=OVERLAY)
    print('final ->', OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 'FAIL')
    return bool(ok and os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024 * 1024)


def qc():
    times = [8, 30, 60, 96, 160, 205, 240, 288]
    os.makedirs(os.path.join(MV, 'mv', 'out', 'qc'), exist_ok=True)
    for t in times:
        out = os.path.join(MV, 'mv', 'out', 'qc', 'final_%03ds.jpg' % t)
        run([FFMPEG, '-y', '-v', 'error', '-ss', str(t), '-i', OUT, '-vframes', '1', '-q:v', '3', out])
    print('qc frames in mv/out/qc/')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--concat', action='store_true')
    ap.add_argument('--burn', action='store_true')
    ap.add_argument('--fast', action='store_true')
    ap.add_argument('--qc', action='store_true')
    a = ap.parse_args()
    if a.check:
        import assemble
        assemble.check()
    if a.concat:
        import assemble
        assemble.concat_video()
        assemble.make_audio()
    if a.burn:
        burn(fast=a.fast)
    if a.qc:
        qc()
