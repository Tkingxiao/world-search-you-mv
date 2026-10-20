"""qc_shots.py - contact sheets + a QC report for every rendered shot.

For each sNN.mp4 in mv/out/shots: extract 3 frames (10%, 50%, 90%), build a
vertical contact sheet in mv/out/qc/shots/, and write mv/out/qc/shots_report.txt
with frames/size/duration so the final render can be checked at a glance.
"""
import json
import os
import subprocess

MV = r'D:\Code\Code MV\new-word.search(you)'
FFMPEG = r'C:\ffmpeg\bin\ffmpeg.exe'
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
SHOTS = os.path.join(MV, 'mv', 'out', 'shots')
QCD = os.path.join(MV, 'mv', 'out', 'qc', 'shots')
PLAN = os.path.join(MV, 'mv', 'data', 'shot_plan.json')


def probe(path):
    p = subprocess.run([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
                        '-count_frames', '-show_entries',
                        'stream=nb_read_frames,width,height,r_frame_rate',
                        '-of', 'json', path], capture_output=True, text=True)
    try:
        st = json.loads(p.stdout)['streams'][0]
        return int(st['nb_read_frames']), int(st['width']), int(st['height']), st['r_frame_rate']
    except Exception:
        return 0, 0, 0, '?'


def main():
    from PIL import Image
    os.makedirs(QCD, exist_ok=True)
    plan = {s['id']: s for s in json.load(open(PLAN, encoding='utf-8'))['shots']}
    rep = []
    for shot in sorted(plan):
        mp4 = os.path.join(SHOTS, shot + '.mp4')
        if not os.path.exists(mp4) or os.path.getsize(mp4) < 10000:
            rep.append('%s MISSING' % shot)
            continue
        n, w, h, fps = probe(mp4)
        dur = n / 60.0
        times = [0.1 * dur, 0.5 * dur, 0.9 * dur]
        ims = []
        for i, t in enumerate(times):
            tmp = os.path.join(QCD, '%s_%d.png' % (shot, i))
            subprocess.run([FFMPEG, '-y', '-v', 'error', '-ss', '%.3f' % t,
                            '-i', mp4, '-vframes', '1', '-vf', 'format=rgb24', tmp])
            if os.path.exists(tmp):
                ims.append(Image.open(tmp).convert('RGB'))
        if not ims:
            rep.append('%s NOFRAMES' % shot)
            continue
        cw, ch = 853, 480
        sheet = Image.new('RGB', (cw, ch * len(ims)), (8, 8, 10))
        for i, im in enumerate(ims):
            sheet.paste(im.resize((cw, ch), Image.LANCZOS), (0, i * ch))
        out = os.path.join(QCD, 'sheet_%s.jpg' % shot)
        sheet.save(out, quality=90)
        rep.append('%s frames=%d %dx%d@%s dur=%.2fs size=%.2fMB' % (
            shot, n, w, h, fps, dur, os.path.getsize(mp4) / 1048576.0))
        print(rep[-1])
    with open(os.path.join(MV, 'mv', 'out', 'qc', 'shots_report.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(rep) + '\n')
    print('report -> mv/out/qc/shots_report.txt')


if __name__ == '__main__':
    main()
