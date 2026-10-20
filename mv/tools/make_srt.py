"""make_srt.py - export a bilingual .srt from mv/data/timeline.json (for accessibility / delivery)."""
import json
import os

MV = r'D:\Code\Code MV\new-word.search(you)'
TL = os.path.join(MV, 'mv', 'data', 'timeline.json')
OUT = os.path.join(MV, 'mv', 'out', 'final', 'world.search(you).srt')


def ts(t, sep=','):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return '%02d:%02d:%02d%s%03d' % (h, m, s, sep, ms)


def main():
    d = json.load(open(TL, encoding='utf-8'))
    lines = []
    for i, ly in enumerate(d['lyrics'], 1):
        en = (ly.get('en') or '').strip()
        zh = (ly.get('zh') or '').strip()
        if not en:
            continue
        txt = en if not zh else en + '\n' + zh
        lines.append('%d\n%s --> %s\n%s\n' % (i, ts(ly['start']), ts(ly['end']), txt))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('wrote', OUT, len(lines), 'cues')


if __name__ == '__main__':
    main()
