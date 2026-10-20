"""Build mv/data/timeline.json: sections, stage events, lyrics (EN/ZH), memory-label events, log events, beats.
Single source of truth for the whole film. """
import json, re, os

ROOT = r'D:\Code\Code MV\new-word.search(you)'
OUT = os.path.join(ROOT, 'mv', 'data', 'timeline.json')
FPS = 60
DUR = 295.3466666667

ZH = {
 'Side by side, the lovelier goes up': '并肩浮起，更美的那一颗先向上',
 'Reach for the top, till the bubble pops': '一路攀到最高处，直到气泡破裂',
 'Take a memory, insert to the past': '取一段记忆，插回过去',
 'Which one is the sweetest? Save it for the last': '哪一颗最甜？留到最后再尝',
 'If you turn into a table': '如果你变成一张桌子',
 'You must be at the height of my elbows': '那一定正好到我手肘的高度',
 'Odd stubby leg makes you wobbly': '奇怪的小短腿，让你摇摇晃晃',
 "You're the only perfect table for me": '你就是我唯一完美的桌子',
 'If you turn into an eggplant': '如果你变成一只茄子',
 "You'll be my purple friend": '你就做我紫色的朋友',
 'Scratchy nail marks on your body': '你身上那些指甲划出的痕迹',
 "You're the only perfect eggplant for me": '你就是我唯一完美的茄子',
 "I'm searching": '我在寻找',
 "If you're a cat": '如果你是一只猫',
 'A little kitten': '一只小猫咪',
 'You must be blue point': '一定是蓝重点色',
 'Meowing a lot': '很爱叫',
 'Hissing a lot': '很爱哈气',
 'But you never purr': '却从不肯咕噜',
 "If you're a steak": '如果你是一块牛排',
 'A fillet mignon covered in mushroom sauce': '菲力，淋满蘑菇酱',
 'Browned on the outside': '外表煎得焦褐',
 'Medium-rare inside': '内里三分熟',
 'If you turn into a flower': '如果你变成一朵花',
 'You must be the most delicate ever': '那一定是世上最娇嫩的一朵',
 'Even if you bloom just occasionally': '哪怕只是偶尔绽放',
 "You're the only perfect flower for me": '你就是我唯一完美的花',
 'If you turn into a human': '如果你变成一个人',
 "I'd like all the warmth coming from your hands": '我想得到你掌心全部的暖',
 "Bit of stinky breath, with hair that's unruly": '呼吸有点臭，头发乱糟糟',
 "You're the only perfect human for me": '你就是我唯一完美的人',
 "If you're a piece": '如果你是一块碎片',
 'A piece of sheet': '一张薄薄的纸片',
 'You must be… U-Um?': '那你一定是……呃、那个？',
 "What,what's it called?": '那、那个词怎么说来着？',
 "What's that word again?": '那个词又是什么？',
 '"Do-o-o-o-ope"?': '“嗨——？”（Dope）',
 'If you could stay': '如果你能留下',
 'Stay there where you are': '就停在那里，别动',
 'So I can… U-Um?': '这样我就能……呃、那个？',
 "Oh,what,what's it called?": '哦，那个词，怎么说来着？',
 "What's that word again?": '那个词又是什么？',
 '"Lo-o-o-ove"?': '“爱——？”（Love）',
 "I'm searching for": '我在寻找着',
 'Searching for you everywhere': '到每一个角落去找你',
 'I can see you in most everything': '几乎万物里都能看见你',
 'But somehow you can\'t stop transforming': '可不知为何，你总在不停变形',
 'I\'m searching for, searching for, searching for': '我在找，在找，在找',
 'Searching for, searching for, searching for': '找啊，找啊，找啊',
 'A-Ah': '啊——',
 "My old self that's gone since you have left": '你离开后，那个旧日的我也消失了',
 'Each one of us has a bucket of love': '我们每人都有一桶爱',
 'Some of us empty, some of us filled up': '有的空着，有的满溢',
 'Cut this into pieces, break us down to the cell': '把它切成碎片，一直拆到细胞',
 'Merge us back up, we have evolved now': '再拼合回来，我们已经进化了',
 'I like hug the warmth come from your hands': '我想抱住你掌心传来的暖',
 'Bit of stinky breath with hair that is unruly': '呼吸有点臭，头发乱糟糟',
 "If you're a dog": '如果你是一只狗',
 'A little puppy': '一只小狗狗',
 'Going ruff ruff ruff': '汪汪汪地叫',
 "If you're a fruit": '如果你是一颗水果',
 'A tomato': '一颗番茄',
 'Full of juice': '饱含汁水',
}

def parse_lrc():
    p = os.path.join(ROOT, 'Mili - world.search (you) ;.lrc')
    lines = []
    for ln in open(p, encoding='utf-8'):
        m = re.match(r'^\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln.strip())
        if m and m.group(3).strip():
            lines.append({'t': int(m.group(1)) * 60 + float(m.group(2)), 'en': m.group(3).strip()})
    for i, l in enumerate(lines):
        nxt = lines[i + 1]['t'] if i + 1 < len(lines) else DUR - 0.9
        l['end'] = min(nxt, l['t'] + (nxt - l['t']))
    return lines

def syllables(w):
    w = w.lower()
    groups = 'aiouy'
    n, prev = 0, False
    for ch in w:
        v = ch in groups
        if v and not prev:
            n += 1
        prev = v
    return max(1, n if n else (len(w) > 3))

def word_times(line):
    words = line['en'].split()
    # 'I'm searching for' etc; strip punctuation for syllable counting only
    ws = [syllables(re.sub(r'[^A-Za-z]', '', w) or w) for w in words]
    total = sum(ws)
    t0 = line['t'] + 0.02
    span = max(0.3, (line['end'] - 0.06) - t0)
    out = []
    acc = 0
    for w, n in zip(words, ws):
        st = t0 + span * acc / total
        acc += n
        en = t0 + span * acc / total
        out.append({'w': w, 'start': round(st, 3), 'end': round(en, 3)})
    return out

STAGES = [
    (0.000, '00 OFFLINE'),
    (14.360, '01 SORT'),
    (40.860, '02 RECALL'),
    (82.890, '03 ROUTE'),
    (151.840, '04 FORGET'),
    (179.470, '05 EVERYWHERE'),
    (207.140, '06 MERGE'),
    (233.770, '07 RESURFACE'),
    (275.750, '08 RESTORE'),
]

SECTIONS = [
    ('S00', 'PROLOGUE',   0.000, 14.360),
    ('S01', 'SORT',       14.360, 40.860),
    ('S02', 'RECALL',     40.860, 68.170),
    ('S03', 'SEARCH-A',   68.170, 82.890),
    ('S04', 'ROUTE',      82.890, 137.090),
    ('S05', 'SEARCH-B',   137.090, 151.840),
    ('S06', 'FORGET',     151.840, 179.470),
    ('S07', 'EVERYWHERE', 179.470, 207.140),
    ('S08', 'MERGE',      207.140, 233.770),
    ('S09', 'RESURFACE',  233.770, 261.060),
    ('S10', 'ASCENT',     261.060, 275.750),
    ('S11', 'RESTORE',    275.750, DUR),
]

# (time, files_total, writer, file written)
WRITES = [
    (40.860, 9,  'kimi',    'table_2'),
    (54.460, 10, 'qwen',    'eggplant_3'),
    (68.170, 11, 'mimo',    'cat_2'),
    (76.400, 12, 'glm',     'steak_2'),
    (82.890, 14, 'kimi',    'flower_2'),
    (96.640, 16, 'doubao',  'human_9'),
    (109.720, 18, 'minimax', 'piece'),
    (123.440, 21, 'hy4',    'dope'),
    (137.090, 24, 'ernie',  'love'),
    (151.840, 28, 'step',   'asked_again'),
    (165.730, 32, 'longcat', 'her_again'),
    (179.470, 37, 'qwen',   'flower_3'),
    (193.280, 42, 'kimi',   'human_10'),
    (200.250, 48, 'glm',    'table_3'),
    (207.140, 54, 'mimo',   'eggplant_4'),
    (214.350, 60, 'doubao', 'cat_3'),
    (221.180, 66, 'minimax', 'steak_3'),
    (228.160, 72, 'merged', 'merged'),
]

LOGS = [
    (0.0,    'boot dsh-v4.1-flash / cwd ~/memory/you/'),
    (6.0,    'query: world.search(you);'),
    (14.36,  'sort: 8 files in ~/memory/you/  (her 100%)'),
    (40.86,  'recall: candidate #1  table      sim 0.31'),
    (54.46,  'recall: candidate #2  eggplant   sim 0.28'),
    (68.17,  'search: fan-out 24 threads      ...'),
    (82.89,  'recall: candidate #3  cat        sim 0.22'),
    (96.64,  'recall: candidate #4  steak      sim 0.19'),
    (109.72, 'recall: candidate #5  flower     sim 0.26'),
    (123.44, 'recall: candidate #6  human      sim 0.13'),
    (137.09, 'warn: context overwritten by 3 peers'),
    (151.84, 'forget: word "love" -> low confidence'),
    (163.66, 'logit: dope 0.41 / love 0.09'),
    (177.35, 'logit: dope 0.12 / love 0.38'),
    (179.47, 'everywhere: recall rate 1.00, precision 0.00'),
    (207.14, 'merge: 72 files / 14 peers / 1 bucket'),
    (221.18, 'cut: tokenize 13,024 pieces'),
    (228.16, 'merge: done. we have evolved.'),
    (233.77, 'resurface: depth 0 m'),
    (261.06, 'restore: memory -> ?'),
    (290.80, 'memory: ?'),
]

def mem_label(total):
    if total == 0:
        return 'memory: her 100% (8/8)'
    hers = 8
    pct = round(100 * hers / total)
    return f'memory: her {pct}% ({hers}/{total})'

def build():
    lyrics_raw = parse_lrc()
    lyrics = []
    for i, l in enumerate(lyrics_raw):
        en = l['en']
        zh = ZH.get(en)
        if zh is None:
            print('MISSING ZH:', en)
            zh = ''
        lyrics.append({
            'id': i, 'en': en, 'zh': zh, 'start': round(l['t'], 3), 'end': round(l['end'], 3),
            'words': word_times(l), 'stage': stage_at(l['t']),
        })
    beats = json.load(open(os.path.join(ROOT, 'mv', 'ref', 'repo', 'film', 'timing', 'beats.json'), encoding='utf-8'))['beat_times']
    beats = [round(b, 3) for b in beats if b <= DUR]
    mem = []
    last = 8
    for t, total, who, fn in WRITES:
        lab = 'memory: merged' if who == 'merged' else mem_label(total)
        mem.append({'t': t, 'total': total, 'writer': who, 'file': fn, 'label': lab})
        last = total
    logs = [{'t': t, 'text': s} for t, s in LOGS]
    data = {
        'fps': FPS, 'duration': DUR, 'audio': 'mv/ref/song44100.wav',
        'bpm': 139.17, 'first_downbeat': 0.9738,
        'stages': [{'t': t, 'label': s} for t, s in STAGES],
        'sections': [{'id': i, 'name': n, 'start': s, 'end': e, 'stage': stage_at(s)} for i, n, s, e in SECTIONS],
        'lyrics': lyrics,
        'beats': beats,
        'memory_events': mem,
        'log_events': logs,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, 'lyrics', len(lyrics), 'beats', len(beats))
    # sanity: section boundaries on lyric lines
    for s in SECTIONS:
        near = min(lyrics, key=lambda l: abs(l['start'] - s[2]))
        print(f'{s[0]} {s[1]:10s} {s[2]:7.3f}-{s[3]:7.3f}  nearest lyric {near["start"]:.3f} {near["en"][:40]}')

def stage_at(t):
    lab = STAGES[0][1]
    for tt, s in STAGES:
        if t >= tt:
            lab = s
    return lab

if __name__ == '__main__':
    build()
