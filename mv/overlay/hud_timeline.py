#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world.search(you); — 文字/信息层时间轴生成器（libass ASS）

读 mv/data/timeline.json，生成 mv/overlay/film.ass，覆盖 0–295.35s：
  · 74 行双语歌词（Georgia Italic 宽字距 + Microsoft YaHei Light 小字）
  · 左上 STAGE 标签 + 页码（等宽小字 NN / 08；无刻度条、无进度条）
  · 右上 MEMORY 状态（her xx% (n/total) → merged → ?，纯文字 + 来源行，无进度条）
  · 左下终端日志（最多三行上滚，terminal 感）
  · 8 张章节条（stage 边界，纸标签样式）+ 3 个次级段落标记
  · 1.0–4.4s 片头小标题（左下角，博物馆登录卡式；s01 void page 之上）
  · 291.2s 起的片尾卡（片名 / 专辑 / 角色美术署名 / CC 许可证）

设计基调：沉没纸雕档案库 + AI 检索终端 = 博物馆标签 + 终端。
克制、精确、有呼吸感；常规不透明度 ~55%（ASS alpha 0x73）。

用法（在仓库根目录执行）：
    python mv/overlay/hud_timeline.py            # 生成 film.ass
    python mv/overlay/hud_timeline.py --check    # 生成 + 校验（歌词数/重叠/字宽）

所有时间严格来自 timeline.json，精度 0.01s。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# 路径与画布
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]          # 仓库根
DATA = ROOT / "mv" / "data" / "timeline.json"
SHOT_PLAN = ROOT / "mv" / "data" / "shot_plan.json"
OUT = ROOT / "mv" / "overlay" / "film.ass"

W, H = 2560, 1440
SAFE = 96                                            # 安全边距 96px

# 色板（RGB）
INK = (0x1D, 0x20, 0x29)      # #1d2029
PAPER = (0xEC, 0xE8, 0xDE)    # #ece8de
BLUE = (0x4D, 0x6B, 0xFE)     # #4d6bfe  her blue
WARM = (0xFF, 0x6B, 0x4A)     # #ff6b4a
GOLD = (0xFF, 0xD2, 0x8A)     # #ffd28a
ABYSS = (0x0A, 0x22, 0x30)    # #0a2230

# 字体族名（必须与 mv/overlay/fonts 下字体文件内的 family name 完全一致）
F_SERIF = "Georgia"
F_MONO = "Consolas"
F_ZH = "Microsoft YaHei Light"

# 版式锚点
LYRIC_EN_Y = 1116             # 78% 高度附近（底部安全区内）
LYRIC_ZH_Y = 1178
# 逐窗位置微调：默认全部 \an5\pos(1280,1116)/(1280,1178)，只对确实撞主体的窗口
# 单独下移，其余窗口一律不动（依据 specimen-lab master QC phase1）。
#   12 → s06 archive rise（68.17–82.89s）推镜时 "I'm searching" 正落在她眼睛/鼻梁上；
#        下移到 1240（中线偏下、下巴以下的地面区），仍在底部安全区内，且与左下 log 块不重叠。
LYRIC_Y_OVERRIDE = {12: (1240, 1302)}
HUD_L = SAFE
HUD_R = W - SAFE
LOG_BOTTOM = H - SAFE
LOG_STEP = 36
CHORUS = (179.47, 233.77)     # EVERYWHERE：歌词略强一点，但仍克制

T_STAGE_FADE_IN = 0.45        # HUD 从黑场里浮出的时刻
T_HUD_OUT = 290.9             # stage / 页码 / log 收束
T_END = 291.2                 # 片尾卡
T_FILM_END = 295.35

# 片头小标题（s01 void page 之上，左下角；1.0s 淡入 → 4.40s 收）
OPEN_T0, OPEN_T1 = 1.00, 4.40
OPEN_X = SAFE
OPEN_RULE_Y = 1092            # 金色短横线
OPEN_MILI_Y = 1104            # 艺术家微标签
OPEN_TITLE_Y = 1134           # 片名（Georgia italic 40）
OPEN_ALBUM_Y = 1194           # 专辑行

# 章节条（museum label）几何
CARD_X0, CARD_X1 = 280, 2280
CARD_Y0, CARD_Y1 = 608, 832
CARD_CY = (CARD_Y0 + CARD_Y1) // 2

# 章节条右下的数据行（取自 timeline 的 log_events / 剧情结果）
CARD_DATA = {
    "01": "8 files \u00b7 her 100%",
    "02": "candidate #1 \u00b7 table \u00b7 sim 0.31",
    "03": "candidate #3 \u00b7 cat \u00b7 sim 0.22",
    "04": "word \u201clove\u201d \u2192 low confidence",
    "05": "recall rate 1.00 \u00b7 precision 0.00",
    "06": "72 files \u00b7 14 peers \u00b7 1 bucket",
    "07": "depth 0 m",
    "08": "result: you",
}


# --------------------------------------------------------------------------- #
# 基础工具
# --------------------------------------------------------------------------- #
def ts(t: float) -> str:
    """秒 → ASS 时间 H:MM:SS.cc（0.01s 精度）。"""
    cs = max(0, int(round(t * 100)))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def esc(text: str) -> str:
    """ASS 文本转义。"""
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def c(rgb: tuple[int, int, int]) -> str:
    """RGB → ASS 颜色标签（不含 alpha）。"""
    r, g, b = rgb
    return f"\\c&H{b:02X}{g:02X}{r:02X}&"


def a(alpha: int) -> str:
    return f"\\alpha&H{alpha:02X}&"


def fad(i_ms: int, o_ms: int) -> str:
    return f"\\fad({i_ms},{o_ms})"


def pos(x: float, y: float) -> str:
    return f"\\pos({x:g},{y:g})"


def move(x1: float, y1: float, x2: float, y2: float, t1: int, t2: int) -> str:
    return f"\\move({x1:g},{y1:g},{x2:g},{y2:g},{t1},{t2})"


def draw(shapes: str) -> str:
    """矢量绘图（\\p1）。shapes 使用绝对/相对坐标由调用方给出。"""
    return "{\\p1\\bord0\\shad0}" + shapes


# --------------------------------------------------------------------------- #
# 样式表
# --------------------------------------------------------------------------- #
STYLE_FIELDS = (
    "Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
    "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
    "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"
)


def style(
    name: str,
    font: str,
    size: float,
    rgb: tuple[int, int, int],
    alpha: int = 0x00,
    *,
    italic: int = 0,
    bold: int = 0,
    spacing: float = 0.0,
    outline: float = 0.0,
    shadow: float = 0.0,
    align: int = 7,
    outline_alpha: int = 0x8C,
    shadow_alpha: int = 0xFF,
) -> str:
    r, g, b = rgb
    primary = f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"
    outline_col = f"&H{outline_alpha:02X}000000"
    # BackColour 同时是 Shadow 的颜色；默认全透明（不画阴影），只有显式给了
    # shadow/shadow_alpha 的样式（歌词）才会落下来一层柔和的深色投影。
    back = f"&H{shadow_alpha:02X}000000"
    return (
        f"Style: {name},{font},{size:g},{primary},{primary},{outline_col},{back},"
        f"{bold},{italic},0,0,100,100,{spacing:g},0,1,{outline:g},{shadow:g},{align},"
        f"{SAFE},{SAFE},{SAFE},1"
    )


# 样式名 → 定义。alpha: 0x00 不透明，0xFF 全透明；0x73 ≈ 55% 不透明度。
STYLES: list[str] = [
    # 歌词（2026-10-19 全局增对比：outline 1.8→2.6 + Shadow 2，解决白围裙/白光辉
    # 上纸白字只有细描边可读的问题；ZH 同步加一档，保持两种语言观感一致）
    style("LyricEN", F_SERIF, 54, PAPER, 0x66, italic=-1, spacing=3.2,
          outline=2.6, shadow=2.0, shadow_alpha=0x99, align=5),
    style("LyricZH", F_ZH, 31, PAPER, 0x80, spacing=0.8,
          outline=2.2, shadow=2.0, shadow_alpha=0x99, align=5),
    # HUD
    style("HudMicro", F_MONO, 19, PAPER, 0x8C, spacing=7, outline=1.0, align=7),
    style("HudStage", F_MONO, 34, PAPER, 0x73, spacing=3, outline=1.2, align=7),
    style("HudPage", F_MONO, 19, PAPER, 0x8C, spacing=4, outline=1.0, align=7),
    style("HudMem", F_MONO, 32, PAPER, 0x73, spacing=0, outline=1.2, align=9),
    style("HudSrc", F_MONO, 19, PAPER, 0x99, spacing=0.5, outline=1.0, align=9),
    style("HudLog", F_MONO, 23, PAPER, 0x73, spacing=0, outline=1.0, align=1),
    # 章节条（纸标签）
    style("CardNum", F_SERIF, 150, INK, 0x1A, italic=-1, align=4, outline=0),
    style("CardName", F_SERIF, 76, INK, 0x1A, spacing=14, align=4, outline=0),
    style("CardData", F_MONO, 21, INK, 0x59, spacing=1.2, align=6, outline=0),
    style("SubMark", F_MONO, 22, PAPER, 0x73, spacing=8, outline=1.0, align=5),
    # 片尾卡
    style("EndMicro", F_MONO, 20, PAPER, 0x73, spacing=8, outline=1.0, align=5),
    style("EndTitle", F_SERIF, 112, PAPER, 0x1A, italic=-1, spacing=2, outline=1.6, align=5),
    style("EndAlbum", F_SERIF, 38, PAPER, 0x4D, italic=-1, spacing=1, outline=1.2, align=5),
    style("EndCreditZH", F_ZH, 25, PAPER, 0x4D, spacing=0.5, outline=1.2, align=5),
    style("EndCreditEN", F_SERIF, 27, PAPER, 0x4D, italic=-1, spacing=0.5, outline=1.2, align=5),
    style("EndLicense", F_MONO, 20, PAPER, 0x73, spacing=2, outline=1.0, align=5),
    # 片头小标题（左下角登录卡；比 HUD 更轻，淡入即退场）
    style("OpenMicro", F_MONO, 18, GOLD, 0x8C, spacing=8, outline=1.0, align=7),
    style("OpenTitle", F_SERIF, 40, PAPER, 0x66, italic=-1, spacing=1.4, outline=1.2, align=7),
    style("OpenAlbum", F_MONO, 17, PAPER, 0x8C, spacing=2.4, outline=1.0, align=7),
    # 纯绘图（颜色/alpha 由事件内联覆盖）
    style("Draw", F_MONO, 20, INK, 0x00, align=7, outline=0),
]
STYLE_NAMES = {s.split(",")[0].split(":", 1)[1].strip() for s in STYLES}


# --------------------------------------------------------------------------- #
# 事件
# --------------------------------------------------------------------------- #
@dataclass
class Ev:
    start: float
    end: float
    style: str
    name: str          # 写入 ASS 的 Name(Actor) 字段，用于定位/QA
    text: str
    layer: int = 2


def ev(start, end, style_name, name, text, layer=2) -> Ev:
    if style_name not in STYLE_NAMES:
        raise KeyError(f"unknown style {style_name}")
    return Ev(float(start), float(end), style_name, name, text, layer)


def load_timeline(path: Path = DATA) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# 1) 双语歌词
# --------------------------------------------------------------------------- #
def caret_tags(duration: float) -> str:
    """长句（>8s 的 'I'm searching'）尾部闪烁终端光标。"""
    tags = [f"\\fn{F_MONO}\\i0\\fs44{c(BLUE)}{a(0xFF)}"]
    t = 0
    while t < duration * 1000 - 200:
        tags.append(f"\\t({t},{t + 700},{a(0x66)})")
        tags.append(f"\\t({t + 700},{t + 1400},{a(0xFF)})")
        t += 1400
    return "{" + "".join(tags) + "} |"


def build_lyrics(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    for line in tl["lyrics"]:
        idx, start, end = line["id"], line["start"], line["end"]
        # 最后一行（id73: 287.35–294.447 "Full of juice"）会压到 291.2 的片尾卡上：
        # 在 291.0 截断并加长淡出，让位片名。其余行严格沿用 timeline.json。
        cut = end > T_END - 0.2
        if cut:
            end = T_END - 0.2
        chorus = CHORUS[0] <= start < CHORUS[1]
        a_en = 0x4D if chorus else 0x66      # 70% / 60%
        a_zh = 0x66 if chorus else 0x80      # 60% / 50%
        en = esc(line["en"])
        if end - start > 8.0:
            en += caret_tags(end - start)
        en_y, zh_y = LYRIC_Y_OVERRIDE.get(idx, (LYRIC_EN_Y, LYRIC_ZH_Y))
        out.append(ev(
            start, end, "LyricEN", f"LYR_EN_{idx:02d}",
            f"{{\\an5{pos(1280, en_y)}{fad(250, 320 if cut else 300)}{a(a_en)}}}{en}", 3,
        ))
        out.append(ev(
            start, end, "LyricZH", f"LYR_ZH_{idx:02d}",
            f"{{\\an5{pos(1280, zh_y)}{fad(250, 320 if cut else 300)}{a(a_zh)}}}{esc(line['zh'])}", 3,
        ))
    return out


# --------------------------------------------------------------------------- #
# 2) 左上 STAGE + 索引刻度
# --------------------------------------------------------------------------- #
def build_stage(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    stages = tl["stages"]
    sections = tl["sections"]

    # 微标签
    out.append(ev(
        T_STAGE_FADE_IN, T_HUD_OUT, "HudMicro", "HUD_STAGE_MICRO",
        f"{{\\an7{pos(HUD_L, SAFE)}{fad(600, 280)}}}STAGE", 3,
    ))

    # 阶段值（每次切换：淡出旧值 → 淡入新值 + 2px 上浮）
    for i, stage in enumerate(stages):
        start = T_STAGE_FADE_IN if i == 0 else stage["t"]
        end = stages[i + 1]["t"] if i + 1 < len(stages) else T_HUD_OUT
        fi = 600 if i == 0 else 240
        text = (
            f"{{\\an7{move(HUD_L, 132, HUD_L, 122, 0, fi)}{fad(fi, 200)}}}"
            f"{esc(stage['label'])}"
        )
        out.append(ev(start, end, "HudStage", f"HUD_STAGE_{i:02d}", text, 3))

    # 页码：等宽小字「NN / 08」+ 2px her-blue 短横线 + 当前 section 名（仅当名字与
    # 上一行 stage 值不同时补出，避免重复）。数字与 stage 编号同一轴，绝不使用连续
    # 刻度条/填充条，避免被读成播放进度条。
    last_stage = len(stages) - 1
    page_w = 98                 # "03 / 08" 在 Consolas 19 + tracking 4 下约 97px
    dash_x = HUD_L + page_w + 18
    name_x = dash_x + 22 + 18
    n = len(sections)
    for j, sec in enumerate(sections):
        start = T_STAGE_FADE_IN if j == 0 else sec["start"]
        end = sections[j + 1]["start"] if j + 1 < n else T_HUD_OUT
        fade = fad(600, 0) if j == 0 else (fad(0, 280) if j == n - 1 else "")
        stage_num, stage_name = sec["stage"].split(" ", 1)
        page = f"{int(stage_num):02d} / {last_stage:02d}"
        out.append(ev(
            start, end, "HudPage", f"HUD_PAGE_{j:02d}",
            f"{{\\an7{pos(HUD_L, 176)}{fade}{c(PAPER)}{a(0x8C)}}}{esc(page)}", 3,
        ))
        # 当前段标记：2px her-blue 短横线（不是填充条）
        out.append(ev(
            start, end, "Draw", f"HUD_PAGE_DASH_{j:02d}",
            f"{{\\an7{pos(dash_x, 184)}{fade}{c(BLUE)}{a(0x59)}}}"
            f"{draw('m 0 0 l 22 0 l 22 2 l 0 2')}", 2,
        ))
        if sec["name"] != stage_name:
            out.append(ev(
                start, end, "HudPage", f"HUD_PAGE_NAME_{j:02d}",
                f"{{\\an7{pos(name_x, 176)}{fade}{c(PAPER)}{a(0x73)}}}{esc(sec['name'])}", 3,
            ))
    return out


# --------------------------------------------------------------------------- #
# 3) 右上 MEMORY
# --------------------------------------------------------------------------- #
def memory_states(tl: dict) -> list[dict]:
    """把 memory_events 展开成状态序列（含 14.36s 的初始 100% 与 290.8s 的 ?）。"""
    states: list[dict] = [
        dict(
            t=tl["sections"][1]["start"],
            label="memory: her 100% (8/8)",
            pct=1.0,
            src="~/memory/you/ \u00b7 8 files",
        )
    ]
    for e in tl["memory_events"]:
        label = e["label"]
        if label.endswith("merged"):
            states.append(dict(t=e["t"], label=label, pct=1.0,
                               src="72 files \u00b7 14 peers \u00b7 1 bucket"))
            continue
        m = re.search(r"(\d+)%", label)
        states.append(dict(
            t=e["t"], label=label,
            pct=(int(m.group(1)) / 100.0) if m else 1.0,
            src=f"{e['writer']} \u00b7 {e['file']}",
        ))
    states.append(dict(t=290.8, label="memory: ?", pct=0.0, src=None))
    return states


def mem_value_text(label: str, duration: float) -> str:
    m = re.match(r"memory: her (\d+)% \((\d+)/(\d+)\)", label)
    if m:
        pct, tot, n = m.groups()
        return (
            f"{{\\fn{F_MONO}\\fs25{a(0x99)}}}memory: "
            f"{{\\fn{F_MONO}\\fs32{a(0x73)}}}her "
            f"{{\\fn{F_MONO}\\fs32{c(BLUE)}{a(0x4D)}}}{pct}%"
            f"{{\\c&HDEE8EC&{a(0x73)}}} "
            f"{{\\fn{F_MONO}\\fs23{a(0x99)}}}({tot}/{n})"
        )
    if label.endswith("merged"):
        return (
            f"{{\\fn{F_MONO}\\fs25{a(0x99)}}}memory: "
            f"{{\\fn{F_MONO}\\fs30{c(GOLD)}{a(0x33)}}}merged"
        )
    if label.endswith("?"):
        blink = ""
        t = 0
        while t < duration * 1000 - 200:
            blink += f"\\t({t},{t + 650},{a(0xAA)})\\t({t + 650},{t + 1300},{a(0x33)})"
            t += 1300
        return (
            f"{{\\fn{F_MONO}\\fs25{a(0x99)}}}memory: "
            f"{{\\fn{F_MONO}\\fs32{c(BLUE)}{a(0x33)}{blink}}}?"
        )
    return f"{{\\fn{F_MONO}\\fs28{a(0x73)}}}{esc(label)}"


def build_memory(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    states = memory_states(tl)
    t_first = states[0]["t"]
    # "memory: ?" 是全片最后的终端陈述：比 HUD 多活 1.1s，在片尾卡淡入时收掉
    T_MEM_END = 292.0
    out.append(ev(
        t_first, T_MEM_END, "HudMicro", "HUD_MEM_MICRO",
        f"{{\\an9{pos(HUD_R, SAFE)}{fad(500, 280)}}}MEMORY", 3,
    ))

    # 注意：右上不再画百分比条（Lead 拍板：只留数字与来源行，避免读成播放进度条）。
    for i, st in enumerate(states):
        start = st["t"]
        last = i == len(states) - 1
        end = states[i + 1]["t"] if not last else T_MEM_END
        fi = 500 if i == 0 else 220
        fo = 500 if last else 180

        # 数值行
        out.append(ev(
            start, end, "HudMem", f"HUD_MEM_{i:02d}",
            f"{{\\an9{pos(HUD_R, 122)}{fad(fi, fo)}}}{mem_value_text(st['label'], end - start)}", 3,
        ))
        # 来源行（博物馆标签的 provenance）
        if st["src"]:
            out.append(ev(
                start, end, "HudSrc", f"HUD_MEM_SRC_{i:02d}",
                f"{{\\an9{pos(HUD_R, 162)}{fad(fi, fo)}{c(PAPER)}{a(0x99)}}}"
                f"\u2514\u2500 {esc(st['src'])}", 3,
            ))
    return out


# --------------------------------------------------------------------------- #
# 4) 左下终端日志（三行上滚）
# --------------------------------------------------------------------------- #
def _norm_log(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def build_log(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    logs = tl["log_events"]
    n = len(logs)
    for i, entry in enumerate(logs):
        start0 = entry["t"]
        if i == 0:
            start0 = 0.25                       # 从黑场浮出
        body = (
            f"{{\\c&H{BLUE[2]:02X}{BLUE[1]:02X}{BLUE[0]:02X}&{a(0x73)}}}> "
            f"{{\\c&H{PAPER[2]:02X}{PAPER[1]:02X}{PAPER[0]:02X}&{a(0x66)}}}"
            f"{esc(_norm_log(entry['text']))}"
        )
        for k in range(3):
            j = i + k
            if j >= n:
                break
            start = logs[j]["t"] if j > 0 else start0
            if k == 0 and i == 0:
                start = start0
            if j + 1 < n:
                end = logs[j + 1]["t"]
            else:
                # 最后一条日志陪片尾卡停留，作为全片最后的终端陈述
                end = 294.9 if i == n - 1 else T_HUD_OUT
            y = LOG_BOTTOM - LOG_STEP * k
            if k == 0:
                mv = move(HUD_L, y + 10, HUD_L, y, 0, 220)
                fi = 200
            else:
                prev_y = LOG_BOTTOM - LOG_STEP * (k - 1)
                mv = move(HUD_L, prev_y, HUD_L, y, 0, 220)
                fi = 0
            fo = 500 if (i == n - 1 and j + 1 >= n) else (280 if end == T_HUD_OUT else 0)
            fade = fad(fi, fo) if (fi or fo) else ""
            out.append(ev(
                start, end, "HudLog", f"HUD_LOG_{i:02d}_s{k}",
                f"{{\\an1{mv}{fade}}}{body}", 3,
            ))
    return out


# --------------------------------------------------------------------------- #
# 5) 章节条 + 次级段落标记
# --------------------------------------------------------------------------- #
def chapter_sections(tl: dict) -> list[dict]:
    """stage 发生变化（= 主章节）的 section 边界。"""
    out: list[dict] = []
    secs = tl["sections"]
    for i, sec in enumerate(secs):
        if i == 0:
            continue
        if sec["stage"] != secs[i - 1]["stage"]:
            out.append(sec)
    return out


def sub_sections(tl: dict) -> list[dict]:
    """同一 stage 内的次级段落边界（SEARCH-A / SEARCH-B / ASCENT）。"""
    out: list[dict] = []
    secs = tl["sections"]
    for i, sec in enumerate(secs):
        if i == 0:
            continue
        if sec["stage"] == secs[i - 1]["stage"]:
            out.append(sec)
    return out


def chapter_strip(start: float, num: str, name: str, data: str) -> list[Ev]:
    """一张纸标签式章节条（8 个 stage 章节共用同一版式）。

    start 为章节开始时间；条从 start+0.10 显示到 start+1.30（1.2s）。
    """
    out: list[Ev] = []
    end = start + 1.30
    start = start + 0.10
    tag = f"CARD_{num}_{name}"
    # 纸标签底
    cw, chh = CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0
    fill_shape = f"m 0 0 l {cw} 0 l {cw} {chh} l 0 {chh}"
    out.append(ev(
        start, end, "Draw", f"{tag}_FILL",
        f"{{\\an7{pos(CARD_X0, CARD_Y0)}{fad(240, 340)}{c(PAPER)}{a(0x66)}}}"
        f"{draw(fill_shape)}", 1,
    ))
    # 内衬细线
    iw, ih = (CARD_X1 - 14) - (CARD_X0 + 14), (CARD_Y1 - 14) - (CARD_Y0 + 14)
    inner = (
        f"m 0 0 l {iw} 0 l {iw} 1.5 l 0 1.5 "
        f"m 0 {ih - 1.5} l {iw} {ih - 1.5} l {iw} {ih} l 0 {ih} "
        f"m 0 0 l 1.5 0 l 1.5 {ih} l 0 {ih} "
        f"m {iw - 1.5} 0 l {iw} 0 l {iw} {ih} l {iw - 1.5} {ih}"
    )
    out.append(ev(
        start, end, "Draw", f"{tag}_RULE",
        f"{{\\an7{pos(CARD_X0 + 14, CARD_Y0 + 14)}{fad(240, 340)}{c(INK)}{a(0x8C)}}}{draw(inner)}",
        2,
    ))
    # 编号
    out.append(ev(
        start, end, "CardNum", f"{tag}_NUM",
        f"{{\\an4{move(348, CARD_CY + 12, 348, CARD_CY, 0, 320)}{fad(240, 340)}}}{num}", 3,
    ))
    # 章名
    out.append(ev(
        start, end, "CardName", f"{tag}_NAME",
        f"{{\\an4{move(604, CARD_CY + 12, 604, CARD_CY, 0, 320)}{fad(240, 340)}}}{esc(name)}", 3,
    ))
    # 数据行（右侧）
    if data:
        out.append(ev(
            start, end, "CardData", f"{tag}_DATA",
            f"{{\\an6{pos(CARD_X1 - 40, CARD_CY)}{fad(240, 340)}}}{esc(data)}", 3,
        ))
    return out


def build_cards(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    for sec in chapter_sections(tl):
        num, name = sec["stage"].split(" ", 1)
        out += chapter_strip(sec["start"], num, name, CARD_DATA.get(num, ""))

    # 次级段落标记：细线 + 小字
    for sec in sub_sections(tl):
        name = sec["name"]
        start, end = sec["start"] + 0.08, sec["start"] + 1.08
        half = len(name) * 13.2 / 2 + 7 * 8 / 2
        gap = 30
        xl = 1280 - half - gap - 100
        xr = 1280 + half + gap
        sub_shape = (
            f"m 0 0 l 100 0 l 100 1.6 l 0 1.6 "
            f"m {xr - xl} 0 l {xr - xl + 100} 0 l {xr - xl + 100} 1.6 l {xr - xl} 1.6"
        )
        out.append(ev(
            start, end, "Draw", f"SUBCARD_{sec['id']}_RULE",
            f"{{\\an7{pos(xl, 419)}{fad(240, 320)}{c(PAPER)}{a(0x8C)}}}"
            f"{draw(sub_shape)}", 2,
        ))
        out.append(ev(
            start, end, "SubMark", f"SUBCARD_{sec['id']}",
            f"{{\\an5{pos(1280, 420)}{fad(240, 320)}}}{esc(name)}", 3,
        ))
    return out


# --------------------------------------------------------------------------- #
# 6) 片尾卡（291.2s → 295.35s）
# --------------------------------------------------------------------------- #
def build_end_card(tl: dict) -> list[Ev]:
    out: list[Ev] = []
    T0, T1 = T_END, T_FILM_END
    fi, fo = 700, 400

    # 暗场（让片名与署名可读，同时保留水面余韵）
    out.append(ev(
        T0, T1, "Draw", "END_VEIL",
        f"{{\\an7{pos(0, 0)}{fad(800, 400)}{c(ABYSS)}{a(0x66)}}}"
        f"{draw(f'm 0 0 l {W} 0 l {W} {H} l 0 {H}')}", 0,
    ))
    # MILI（微标签）
    out.append(ev(
        T0, T1, "EndMicro", "END_MICRO_ARTIST",
        f"{{\\an5{pos(1280, 452)}{fad(fi, fo)}{c(GOLD)}{a(0x73)}}}MILI", 2,
    ))
    # 片名
    out.append(ev(
        T0, T1, "EndTitle", "END_TITLE",
        f"{{\\an5{pos(1280, 560)}{move(1280, 572, 1280, 560, 0, 700)}{fad(fi, fo)}}}"
        f"world.search(you);", 2,
    ))
    # 金色细线
    out.append(ev(
        T0, T1, "Draw", "END_RULE",
        f"{{\\an7{pos(900, 640)}{fad(fi, fo)}{c(GOLD)}{a(0x8C)}}}"
        f"{draw('m 0 0 l 760 0 l 760 2 l 0 2')}", 1,
    ))
    # 专辑
    out.append(ev(
        T0, T1, "EndAlbum", "END_ALBUM",
        f"{{\\an5{pos(1280, 700)}{fad(fi, fo)}}}from the album Hue", 2,
    ))
    # 角色美术署名
    out.append(ev(
        T0, T1, "EndMicro", "END_MICRO_CREDIT",
        f"{{\\an5{pos(1280, 852)}{fad(fi, fo)}}}CHARACTER ART", 2,
    ))
    credit = (
        f"{{\\fn{F_ZH}\\fs25{a(0x4D)}}}角色美术：溟月 \u00a9 上善无形"
        f"{{\\c&H8AD2FF&{a(0x8C)}}}  \u00b7  "
        f"{{\\c&HDEE8EC&{a(0x4D)}\\fn{F_ZH}\\fs25}}女仆版 "
        f"{{\\fn{F_SERIF}\\i1\\fs26}}ZipZipPipe"
        f"{{\\c&H8AD2FF&{a(0x8C)}}}  \u00b7  "
        f"{{\\c&HDEE8EC&{a(0x4D)}\\fn{F_ZH}\\fs25}}立绘 "
        f"{{\\fn{F_SERIF}\\i1\\fs26}}Small-tailqwq"
        f"{{\\c&H8AD2FF&{a(0x8C)}}}  \u00b7  "
        f"{{\\c&HDEE8EC&{a(0x4D)}\\fn{F_ZH}\\fs25}}表情 "
        f"{{\\fn{F_SERIF}\\i1\\fs26}}JAdpp"
    )
    out.append(ev(
        T0, T1, "EndCreditZH", "END_CREDIT_ART",
        f"{{\\an5{pos(1280, 898)}{fad(fi, fo)}}}{credit}", 2,
    ))
    # 许可证
    out.append(ev(
        T0, T1, "EndLicense", "END_LICENSE",
        f"{{\\an5{pos(1280, 952)}{fad(fi, fo)}}}licensed under CC BY-NC-SA 4.0", 2,
    ))
    # 底部微标签
    out.append(ev(
        T0, T1, "EndMicro", "END_MICRO_FILM",
        f"{{\\an5{pos(1280, 1320)}{fad(fi, fo)}{c(PAPER)}{a(0x8C)}}}"
        f"THE MUSEUM OF APPROXIMATIONS", 2,
    ))
    return out


# --------------------------------------------------------------------------- #
# 6b) 片头小标题（1.0–4.4s，叠在 s01 void page 的左下角）
# --------------------------------------------------------------------------- #
def build_opening_title() -> list[Ev]:
    """博物馆登录卡式小标题：金色钉线 + MILI + 片名 + 专辑行，左下角，极轻。

    三层错开淡入（+0.00 / +0.05 / +0.14 / +0.30s），4.40s 前全部收掉；
    不进入画面中央（页面主体），也不压住 0.45s 起的 STAGE 与 0.0s 起的终端日志。
    """
    out: list[Ev] = []
    # 金色短横线（纸标签的钉线）
    out.append(ev(
        OPEN_T0, OPEN_T1, "Draw", "OPEN_RULE",
        f"{{\\an7{pos(OPEN_X, OPEN_RULE_Y)}{fad(600, 450)}{c(GOLD)}{a(0x73)}}}"
        f"{draw('m 0 0 l 64 0 l 64 2 l 0 2')}", 1,
    ))
    # 艺术家微标签
    out.append(ev(
        OPEN_T0 + 0.05, OPEN_T1, "OpenMicro", "OPEN_MILI",
        f"{{\\an7{pos(OPEN_X, OPEN_MILI_Y)}{fad(550, 450)}}}MILI", 3,
    ))
    # 片名（Georgia italic，轻微上浮 6px）
    out.append(ev(
        OPEN_T0 + 0.14, OPEN_T1, "OpenTitle", "OPEN_TITLE",
        f"{{\\an7{pos(OPEN_X, OPEN_TITLE_Y)}"
        f"{move(OPEN_X, OPEN_TITLE_Y + 6, OPEN_X, OPEN_TITLE_Y, 0, 700)}"
        f"{fad(700, 450)}}}world.search(you);", 3,
    ))
    # 专辑行
    out.append(ev(
        OPEN_T0 + 0.30, OPEN_T1, "OpenAlbum", "OPEN_ALBUM",
        f"{{\\an7{pos(OPEN_X, OPEN_ALBUM_Y)}{fad(700, 450)}}}from the album Hue", 3,
    ))
    return out


# --------------------------------------------------------------------------- #
# 组装 / 写出 / 校验
# --------------------------------------------------------------------------- #
def build_events(tl: dict) -> list[Ev]:
    events: list[Ev] = []
    events += build_lyrics(tl)
    events += build_stage(tl)
    events += build_memory(tl)
    events += build_log(tl)
    events += build_cards(tl)
    events += build_opening_title()
    events += build_end_card(tl)
    events.sort(key=lambda e: (e.layer, e.start, e.name))
    return events


def ass_header(tl: dict) -> str:
    return (
        "[Script Info]\n"
        "Title: world.search(you); \u2014 The Museum of Approximations\n"
        "Original Script: ui-lab / hud_timeline.py\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        "YCbCr Matrix: TV.709\n"
        f"PlayResX: {W}\n"
        f"PlayResY: {H}\n"
        "Timer: 100.0000\n"
        "\n"
        "[V4+ Styles]\n"
        f"Format: {STYLE_FIELDS}\n"
        + "\n".join(STYLES)
        + "\n\n[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def write_ass(path: Path, tl: dict, events: list[Ev]) -> None:
    lines = [ass_header(tl)]
    for e in events:
        lines.append(
            f"Dialogue: {e.layer},{ts(e.start)},{ts(e.end)},{e.style},{e.name},"
            f"0,0,0,,{e.text}\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def load_shot_plan() -> dict | None:
    """读 mv/data/shot_plan.json（只读；缺失时跳过交叉校验）。"""
    if not SHOT_PLAN.exists():
        return None
    with SHOT_PLAN.open(encoding="utf-8") as f:
        return json.load(f)


def shot_at(plan: dict, t: float) -> dict | None:
    for s in plan["shots"]:
        if s["t0"] - 1e-6 <= t < s["t1"] + 1e-6:
            return s
    return None


def check_shot_plan(tl: dict) -> list[str]:
    """与 15 镜 shot_plan 交叉校验：卡片/标题/片尾窗口不得跨镜。"""
    problems: list[str] = []
    plan = load_shot_plan()
    if plan is None:
        return problems
    shots = plan["shots"]
    if len(shots) != 15:
        problems.append(f"shot_plan 镜数 {len(shots)} != 15")
    if abs(shots[0]["t0"]) > 1e-6:
        problems.append(f"shot_plan 首镜起点 {shots[0]['t0']} != 0")
    for a, b in zip(shots, shots[1:]):
        if abs(a["t1"] - b["t0"]) > 1e-6:
            problems.append(f"shot_plan 断点 {a['id']}→{b['id']}: {a['t1']} != {b['t0']}")
    if abs(shots[-1]["t1"] - tl["duration"]) > 0.01:      # shot_plan 时间取 0.01s 精度
        problems.append(f"shot_plan 末镜终点 {shots[-1]['t1']} != 片长 {tl['duration']:.3f}")

    windows: list[tuple[str, float, float]] = []
    for sec in chapter_sections(tl):
        windows.append((f"章节条 {sec['stage']}", sec["start"] + 0.10, sec["start"] + 1.30))
    for sec in sub_sections(tl):
        windows.append((f"次级标记 {sec['name']}", sec["start"] + 0.08, sec["start"] + 1.08))
    windows.append(("片头小标题", OPEN_T0, OPEN_T1))
    windows.append(("片尾卡", T_END, T_FILM_END))
    for label, t0, t1 in windows:
        s0, s1 = shot_at(plan, t0), shot_at(plan, t1 - 1e-3)
        if s0 is None or s1 is None:
            problems.append(f"{label} 超出 shot_plan 时间范围")
        elif s0["id"] != s1["id"]:
            problems.append(f"{label} 跨镜 {s0['id']}→{s1['id']}（{t0:.2f}–{t1:.2f}）")
    return problems


def check(tl: dict, events: list[Ev]) -> list[str]:
    """基本一致性校验，返回问题列表（空 = 通过）。"""
    problems: list[str] = []
    lyrics = [e for e in events if e.name.startswith("LYR_")]
    en = [e for e in lyrics if e.name.startswith("LYR_EN_")]
    zh = [e for e in lyrics if e.name.startswith("LYR_ZH_")]
    if len(en) != 74:
        problems.append(f"EN 歌词事件数 {len(en)} != 74")
    if len(zh) != 74:
        problems.append(f"ZH 歌词事件数 {len(zh)} != 74")

    # 时间必须与 timeline.json 完全一致（末行在片尾卡前截断，见 build_lyrics）
    for line, e in zip(tl["lyrics"], en):
        want_end = min(line["end"], T_END - 0.2)
        if abs(e.start - line["start"]) > 1e-6 or abs(e.end - want_end) > 1e-6:
            problems.append(f"歌词 {line['id']} 时间漂移")
    # 相邻不重叠
    for prev, cur in zip(en, en[1:]):
        if cur.start < prev.end - 1e-6:
            problems.append(f"歌词事件重叠 {prev.name} / {cur.name}")

    # 字宽校验（用 PIL 量，若字体可用）
    try:
        from PIL import ImageFont

        f_en = ImageFont.truetype(str(ROOT / "mv/overlay/fonts/georgiai.ttf"), 54)
        f_zh = ImageFont.truetype(str(ROOT / "mv/overlay/fonts/msyhl.ttc"), 31, index=0)
        limit = W - 2 * SAFE
        for line in tl["lyrics"]:
            w_en = sum(f_en.getlength(ch) for ch in line["en"]) + 3.2 * (len(line["en"]) - 1)
            if w_en > limit:
                problems.append(f"EN 歌词 {line['id']} 过宽 {w_en:.0f}px > {limit}")
            w_zh = sum(f_zh.getlength(ch) for ch in line["zh"]) + 0.8 * (len(line["zh"]) - 1)
            if w_zh > limit:
                problems.append(f"ZH 歌词 {line['id']} 过宽 {w_zh:.0f}px > {limit}")
    except Exception as exc:                       # 字体缺失时不影响生成
        problems.append(f"(跳过字宽校验: {exc})")

    # HUD：页码 12 段、无刻度条、无百分比条（Lead 拍板：不许读成播放进度条）
    pages = [e for e in events
             if e.name.startswith("HUD_PAGE_") and "_DASH_" not in e.name and "_NAME_" not in e.name]
    dashes = [e for e in events if e.name.startswith("HUD_PAGE_DASH_")]
    if len(pages) != 12:
        problems.append(f"页码事件数 {len(pages)} != 12")
    if len(dashes) != 12:
        problems.append(f"页码短横线事件数 {len(dashes)} != 12")
    if any("HUD_TICK_" in e.name for e in events):
        problems.append("仍存在旧的 12 段刻度事件 HUD_TICK_*")
    if any("HUD_MEM_BAR_" in e.name for e in events):
        problems.append("仍存在 memory 百分比条事件 HUD_MEM_BAR_*")

    # 章节条 / 次级标记 / 片尾卡
    if len(chapter_sections(tl)) != 8:
        problems.append("主章节数量不是 8")
    if len(sub_sections(tl)) != 3:
        problems.append("次级段落数量不是 3")
    if not any(e.name == "END_TITLE" for e in events):
        problems.append("缺少片尾片名事件")

    # 片头小标题：4 条事件、1.0–4.4s 内、与首行歌词拉开距离、不超安全区
    opening = [e for e in events if e.name.startswith("OPEN_")]
    if len(opening) != 4:
        problems.append(f"片头标题事件数 {len(opening)} != 4")
    for e in opening:
        if e.start < OPEN_T0 - 1e-6 or e.end > OPEN_T1 + 1e-6:
            problems.append(f"{e.name} 时间越界 {e.start:.2f}–{e.end:.2f}")
    if not any(e.name == "OPEN_TITLE" for e in opening):
        problems.append("缺少片头片名事件")
    if en and opening and max(e.end for e in opening) >= en[0].start - 0.2:
        problems.append("片头标题与首行歌词时间过近")
    try:
        from PIL import ImageFont

        f_t = ImageFont.truetype(str(ROOT / "mv/overlay/fonts/georgiai.ttf"), 40)
        f_m = ImageFont.truetype(str(ROOT / "mv/overlay/fonts/consola.ttf"), 18)
        f_a = ImageFont.truetype(str(ROOT / "mv/overlay/fonts/consola.ttf"), 17)
        w_t = sum(f_t.getlength(ch) for ch in "world.search(you);") + 1.4 * 17
        w_m = sum(f_m.getlength(ch) for ch in "MILI") + 8 * 3
        w_a = sum(f_a.getlength(ch) for ch in "from the album Hue") + 2.4 * 17
        w_max = max(w_t, w_m, w_a)
        if OPEN_X + w_max > W - SAFE:
            problems.append(f"片头标题过宽 {w_max:.0f}px（右缘 {OPEN_X + w_max:.0f} > {W - SAFE}）")
    except Exception as exc:                       # 字体缺失时不影响生成
        problems.append(f"(跳过片头标题字宽校验: {exc})")

    # 与 15 镜 shot_plan 交叉校验（窗口不得跨镜）
    problems += check_shot_plan(tl)
    return problems


def main() -> None:
    try:                                    # Windows 控制台默认 GBK，统一按 UTF-8 输出
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="生成 mv/overlay/film.ass")
    ap.add_argument("--out", default=str(OUT), help="输出 ASS 路径")
    ap.add_argument("--check", action="store_true", help="生成后做一致性校验")
    args = ap.parse_args()

    tl = load_timeline()
    events = build_events(tl)
    out = Path(args.out)
    write_ass(out, tl, events)

    layers = {0: 0, 1: 0, 2: 0, 3: 0}
    for e in events:
        layers[e.layer] = layers.get(e.layer, 0) + 1
    print(f"film.ass → {out}")
    print(f"  事件 {len(events)} 条 / 歌词 {len(tl['lyrics'])} 行 / "
          f"章节条 {len(chapter_sections(tl))} 张 / 次级标记 {len(sub_sections(tl))} 个 / "
          f"片头标题 4 条")
    print(f"  分层 {layers}  时长 {ts(tl['duration'])}")
    plan = load_shot_plan()
    if plan is not None:
        print(f"  shot_plan：{len(plan['shots'])} 镜，末镜终点 {plan['shots'][-1]['t1']:.2f}s")

    if args.check:
        problems = check(tl, events)
        if problems:
            print("校验未通过：")
            for p in problems:
                print("  ✗", p)
            raise SystemExit(1)
        print("校验通过：74 行歌词时间与 timeline.json 一致，相邻不重叠，字宽均在安全区内；"
              "章节条/片头标题/片尾卡窗口与 15 镜 shot_plan 无跨镜冲突。")


if __name__ == "__main__":
    main()
