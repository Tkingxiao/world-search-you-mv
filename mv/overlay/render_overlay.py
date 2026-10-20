#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_overlay.py — 文字层渲染 / 烧录 / 目检 一站式脚本

子命令
------
  ass          生成 film.ass（= hud_timeline.py 的全部事件）+ 校验
  test         生成暗青渐变测试底 → test.ass → mv/out/tests/ui/test_overlay.mp4
               （10s / 2560×1440 / 60fps；片名 + 一次 stage 切换 + 一次 memory 变化
                + 一行歌词 + 一行 log），并抽 4 帧到 test_frames/
  qc           用 film.ass 在给定时间点出静帧（setpts 移位法），拼 contact sheet
  opening      片头小标题 QC：叠在 mv/out/lookdev/s01.png 上出 1.20/2.60/4.20s 三帧
               → qc_opening_title.png（保持段）+ qc_opening_title_strip.png（淡入/保持/淡出）
  burn         把 film.ass 烧到成片：--video --audio --out
  all          ass + test + qc

所有 ffmpeg 调用都显式给 :fontsdir=，避免 Windows 下 libass 匹配到别的字体。
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import hud_timeline as ht  # noqa: E402

ROOT = ht.ROOT
FFMPEG = Path(r"C:\ffmpeg\bin\ffmpeg.exe")
FFPROBE = Path(r"C:\ffmpeg\bin\ffprobe.exe")
FONTS_REL = "mv/overlay/fonts"
ASS_REL = "mv/overlay/film.ass"
TESTS = ROOT / "mv/out/tests/ui"
PLATE = TESTS / "test_plate.png"
TEST_ASS = TESTS / "test.ass"

# QC 时间点：覆盖 HUD 各阶段 / 章节卡 / 合唱 / memory 三态 / 片尾
QC_TIMES = [
    (3.2, "boot / stage 00"),
    (15.0, "chapter card 01 SORT"),
    (22.0, "stage 01 + memory 89% + lyric"),
    (40.9, "memory 89% (first event)"),
    (45.0, "stage 02 RECALL"),
    (68.6, "subcard SEARCH-A + 'I'm searching'"),
    (96.0, "memory 57% (percentage state)"),
    (155.0, "stage 04 FORGET"),
    (180.0, "chorus 05 EVERYWHERE + chapter card"),
    (210.0, "stage 06 MERGE"),
    (240.0, "memory merged"),
    (245.0, "stage 07 RESURFACE"),
    (280.0, "stage 08 RESTORE / page 08"),
    (291.5, "memory ? (last) + end card fade-in"),
    (292.5, "end card"),
    (294.6, "end card + last log"),
]


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("  $ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print(p.stdout[-4000:])
        print(p.stderr[-4000:])
        raise SystemExit(f"ffmpeg 失败（{p.returncode}）")


# --------------------------------------------------------------------------- #
# 1) 测试底：暗青渐变 + 径向微光 + 暗角 + 纸纤维颗粒
# --------------------------------------------------------------------------- #
def make_test_plate(path: Path) -> None:
    W, H = ht.W, ht.H
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / (W - 1), yy / (H - 1)

    top = np.array([0.043, 0.106, 0.137])   # #0B1B23
    mid = np.array([0.020, 0.060, 0.082])   # #05151A
    bot = np.array([0.016, 0.031, 0.043])   # #04080B
    t = v[..., None]
    lo = top + (mid - top) * np.clip(t / 0.55, 0, 1)
    hi = mid + (bot - mid) * np.clip((t - 0.55) / 0.45, 0, 1)
    img = np.where(t < 0.55, lo, hi)

    # 右上冷光 + 中下暖光（模拟沉没档案库的窗口与灯）
    def glow(cx, cy, r, color, strength):
        d = np.sqrt(((u - cx) * W / H) ** 2 + (v - cy) ** 2)
        g = np.exp(-(d / r) ** 2) * strength
        return g[..., None] * np.array(color, np.float32)

    img += glow(0.72, 0.18, 0.42, (0.10, 0.30, 0.42), 0.55)
    img += glow(0.30, 0.82, 0.36, (0.30, 0.20, 0.10), 0.30)

    # 暗角
    d = np.sqrt((u - 0.5) ** 2 + (v - 0.5) ** 2) / 0.7071
    img *= (1.0 - 0.45 * d ** 2.2)[..., None]

    # 纸纤维颗粒：两层不同频率的噪声
    rng = np.random.default_rng(2026)
    n1 = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    n1 = np.kron(n1, np.ones((2, 2), np.float32))
    n2 = rng.normal(0, 1, (H, W)).astype(np.float32)
    img += (n1 * 0.006 + n2 * 0.004)[..., None]

    arr = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr, "RGB").save(path)
    print(f"  测试底 → {path}")


# --------------------------------------------------------------------------- #
# 2) 测试 ASS：只截取各模块的一小段，证明能烧对
# --------------------------------------------------------------------------- #
def build_test_ass(path: Path) -> None:
    tl = ht.load_timeline()
    E: list[ht.Ev] = []
    ev = ht.ev

    # ---- 片名（0.45–3.2，居中）----
    E.append(ev(0.45, 3.2, "EndMicro", "TEST_MILI",
                f"{{\\an5{ht.pos(1280, 452)}{ht.fad(700, 400)}}}MILI", 3))
    E.append(ev(0.45, 3.2, "EndTitle", "TEST_TITLE",
                f"{{\\an5{ht.pos(1280, 560)}{ht.fad(700, 400)}}}{ht.esc('world.search(you);')}", 3))
    E.append(ev(0.45, 3.2, "Draw", "TEST_RULE",
                f"{{\\an7{ht.pos(1180, 640)}{ht.fad(700, 400)}"
                f"{ht.c(ht.GOLD)}{ht.a(0x3D)}}}{ht.draw('m 0 0 l 200 0 l 200 1.5 l 0 1.5')}", 2))
    E.append(ev(0.45, 3.2, "EndAlbum", "TEST_ALBUM",
                f"{{\\an5{ht.pos(1280, 700)}{ht.fad(700, 400)}}}from the album Hue", 3))

    # ---- stage：00 OFFLINE → 01 SORT（3.0s 切换；页码版式，无刻度条/进度条）----
    E.append(ev(0.45, 10.0, "HudMicro", "TEST_STAGE_MICRO",
                f"{{\\an7{ht.pos(ht.HUD_L, 96)}{ht.fad(600, 0)}}}STAGE", 3))
    E.append(ev(0.45, 3.0, "HudPage", "TEST_PAGE_00",
                f"{{\\an7{ht.pos(ht.HUD_L, 262)}{ht.fad(600, 0)}"
                f"{ht.c(ht.PAPER)}{ht.a(0x8C)}}}00 / 08", 3))
    E.append(ev(0.45, 3.0, "HudPage", "TEST_PAGE_NAME_00",
                f"{{\\an7{ht.pos(252, 262)}{ht.fad(600, 0)}"
                f"{ht.c(ht.PAPER)}{ht.a(0x73)}}}PROLOGUE", 3))
    E.append(ev(0.45, 3.0, "Draw", "TEST_PAGE_DASH_00",
                f"{{\\an7{ht.pos(212, 270)}{ht.fad(600, 0)}"
                f"{ht.c(ht.BLUE)}{ht.a(0x59)}}}" + ht.draw("m 0 0 l 22 0 l 22 2 l 0 2"), 2))
    E.append(ev(3.0, 10.0, "HudPage", "TEST_PAGE_01",
                f"{{\\an7{ht.pos(ht.HUD_L, 262)}"
                f"{ht.c(ht.PAPER)}{ht.a(0x8C)}}}01 / 08", 3))
    E.append(ev(3.0, 10.0, "Draw", "TEST_PAGE_DASH_01",
                f"{{\\an7{ht.pos(212, 270)}"
                f"{ht.c(ht.BLUE)}{ht.a(0x59)}}}" + ht.draw("m 0 0 l 22 0 l 22 2 l 0 2"), 2))
    E.append(ev(0.45, 3.0, "HudStage", "TEST_STAGE_00",
                f"{{\\an1{ht.move(ht.HUD_L, 250, ht.HUD_L, 240, 0, 320)}{ht.fad(600, 200)}}}"
                "00 OFFLINE", 3))
    E.append(ev(3.0, 10.0, "HudStage", "TEST_STAGE_01",
                f"{{\\an1{ht.move(ht.HUD_L, 250, ht.HUD_L, 240, 0, 320)}{ht.fad(200, 0)}}}"
                "01 SORT", 3))

    # ---- memory：100% → 80%（6.0s 变化）----
    E.append(ev(0.45, 10.0, "HudMicro", "TEST_MEM_MICRO",
                f"{{\\an9{ht.pos(ht.HUD_R, 96)}{ht.fad(600, 0)}}}MEMORY", 3))
    E.append(ev(0.45, 6.0, "HudMem", "TEST_MEM_00",
                f"{{\\an9{ht.pos(ht.HUD_R, 122)}{ht.fad(600, 0)}}}"
                f"memory: her {{\\c&HDEE8EC&{ht.a(0x66)}}}100% (8/8)", 3))
    E.append(ev(6.0, 10.0, "HudMem", "TEST_MEM_01",
                f"{{\\an9{ht.pos(ht.HUD_R, 122)}{ht.fad(0, 0)}}}"
                f"memory: her {{\\c&HDEE8EC&{ht.a(0x66)}}}80% (8/10)", 3))
    E.append(ev(0.45, 10.0, "HudSrc", "TEST_MEM_SRC",
                f"{{\\an9{ht.pos(ht.HUD_R, 162)}{ht.fad(600, 0)}}}└─ writer · file", 3))
    # 右上不画百分比条（与 film.ass 一致：纯文字）

    # ---- log：两行，第二行把第一行顶上去（证明上滚）----
    prompt = f"{{\\c&H{ht.BLUE[2]:02X}{ht.BLUE[1]:02X}{ht.BLUE[0]:02X}&{ht.a(0x73)}}}> "
    prompt += f"{{\\c&H{ht.PAPER[2]:02X}{ht.PAPER[1]:02X}{ht.PAPER[0]:02X}&{ht.a(0x66)}}}"
    E.append(ev(1.6, 5.4, "HudLog", "TEST_LOG_00",
                f"{{\\an1{ht.move(ht.HUD_L, ht.LOG_BOTTOM + 10, ht.HUD_L, ht.LOG_BOTTOM, 0, 220)}"
                f"{ht.fad(200, 0)}}}{prompt}{ht.esc('boot dsh-v4.1-flash  cwd ~/memory/you/')}", 3))
    E.append(ev(5.4, 10.0, "HudLog", "TEST_LOG_00_up",
                f"{{\\an1{ht.move(ht.HUD_L, ht.LOG_BOTTOM, ht.HUD_L, ht.LOG_BOTTOM - ht.LOG_STEP, 0, 220)}}}"
                f"{prompt}{ht.esc('boot dsh-v4.1-flash  cwd ~/memory/you/')}", 3))
    E.append(ev(5.4, 10.0, "HudLog", "TEST_LOG_01",
                f"{{\\an1{ht.move(ht.HUD_L, ht.LOG_BOTTOM + 10, ht.HUD_L, ht.LOG_BOTTOM, 0, 220)}"
                f"{ht.fad(200, 0)}}}{prompt}{ht.esc('query: world.search(you);')}", 3))

    # ---- 一行歌词（6.6–9.6，第 0 行）----
    L = tl["lyrics"][0]
    E.append(ev(6.6, 9.6, "LyricEN", "TEST_LYR_EN",
                f"{{\\an5{ht.pos(ht.W / 2, ht.LYRIC_EN_Y)}{ht.fad(250, 300)}}}"
                f"{ht.esc(L['en'])}", 3))
    E.append(ev(6.6, 9.6, "LyricZH", "TEST_LYR_ZH",
                f"{{\\an5{ht.pos(ht.W / 2, ht.LYRIC_ZH_Y)}{ht.fad(250, 300)}}}"
                f"{ht.esc(L['zh'])}", 3))

    # ---- 章节条（8.0–9.2，证明卡版式）----
    E += ht.chapter_strip(7.90, "01", "SORT", ht.CARD_DATA["01"])

    ht.write_ass(path, tl, E)
    print(f"  测试 ASS → {path}（{len(E)} 条事件）")


# --------------------------------------------------------------------------- #
# 3) 烧录 / 抽帧
# --------------------------------------------------------------------------- #
def burn_test() -> None:
    TESTS.mkdir(parents=True, exist_ok=True)
    make_test_plate(PLATE)
    build_test_ass(TEST_ASS)
    out = TESTS / "test_overlay.mp4"
    run([
        str(FFMPEG), "-y",
        "-loop", "1", "-framerate", "60", "-i", str(PLATE.relative_to(ROOT)),
        "-t", "10",
        "-vf", f"ass={TEST_ASS.relative_to(ROOT).as_posix()}:fontsdir={FONTS_REL},format=yuv420p",
        "-r", "60", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out.relative_to(ROOT)),
    ])
    print(f"  测试视频 → {out}")

    frames = TESTS / "test_frames"
    frames.mkdir(exist_ok=True)
    for t in (1.2, 3.6, 6.9, 8.6):
        run([
            str(FFMPEG), "-y", "-ss", f"{t}", "-i", str(out.relative_to(ROOT)),
            "-frames:v", "1", str((frames / f"t{t:04.1f}.png").relative_to(ROOT)),
        ])
    print(f"  测试帧 → {frames}")


def burn_film(video: str, audio: str, out: str) -> None:
    """最终合成：把 film.ass 烧到已剪辑好的视频上，并换回原音轨。"""
    run([
        str(FFMPEG), "-y",
        "-i", video, "-i", audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"ass={ASS_REL}:fontsdir={FONTS_REL}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "5.1",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart",
        out,
    ])
    print(f"  成片 → {out}")


# --------------------------------------------------------------------------- #
# 4) QC 静帧（setpts 移位：任意时刻取 film.ass 的一帧）
# --------------------------------------------------------------------------- #
def qc_film(times: list[tuple[float, str]] | None = None) -> None:
    times = times or QC_TIMES
    TESTS.mkdir(parents=True, exist_ok=True)
    plate = TESTS / "qc_plate.png"
    make_test_plate(plate)
    qdir = TESTS / "qc_frames"
    qdir.mkdir(exist_ok=True)
    shots: list[tuple[Path, str]] = []
    for t, label in times:
        p = qdir / f"qc_{t:07.2f}.png"
        run([
            str(FFMPEG), "-y",
            "-loop", "1", "-framerate", "60", "-i", str(plate.relative_to(ROOT)),
            "-frames:v", "1",
            "-vf", (f"setpts=PTS+{t:.3f}/TB,"
                    f"ass={ASS_REL}:fontsdir={FONTS_REL},format=yuv420p"),
            str(p.relative_to(ROOT)),
        ])
        shots.append((p, label))
    contact_sheet(shots, TESTS / "qc_sheet.png")
    # Lead 指定的 memory 三态单帧：百分比态 / merged / ?（直接放在 mv/out/tests/ui/ 根下）
    for t in (96.0, 240.0, 291.5):
        src = qdir / f"qc_{t:07.2f}.png"
        dst = TESTS / f"qc_hud_{t:07.2f}.png"
        shutil.copyfile(src, dst)
        print(f"  HUD 态 {t:6.2f}s → {dst.name}")


# --------------------------------------------------------------------------- #
# 4b) 片头小标题 QC（叠在 lookdev s01 上；淡入 / 保持 / 淡出三帧）
# --------------------------------------------------------------------------- #
def qc_opening() -> None:
    """把 film.ass 叠到 mv/out/lookdev/s01.png（void page lookdev）上验证片头小标题。"""
    TESTS.mkdir(parents=True, exist_ok=True)
    src = ROOT / "mv/out/lookdev/s01.png"
    if not src.exists():
        raise SystemExit(f"缺少 lookdev 帧 {src}")
    tmp = TESTS / "qc_opening_title_hold.png"
    targets = [
        (1.20, TESTS / "qc_opening_title_fadein.png", "淡入中"),
        (2.60, tmp, "保持"),
        (4.20, TESTS / "qc_opening_title_fadeout.png", "淡出中"),
    ]
    for t, p, label in targets:
        run([
            str(FFMPEG), "-y",
            "-loop", "1", "-framerate", "60", "-i", str(src.relative_to(ROOT)),
            "-frames:v", "1",
            "-vf", (f"scale={ht.W}:{ht.H}:flags=lanczos,setpts=PTS+{t:.3f}/TB,"
                    f"ass={ASS_REL}:fontsdir={FONTS_REL},format=yuv420p"),
            str(p.relative_to(ROOT)),
        ])
        print(f"  {label} {t:.2f}s → {p.name}")
    shutil.copyfile(tmp, TESTS / "qc_opening_title.png")
    # 三连条：淡入 / 保持 / 淡出（各 1280×720 横排）
    tw, th = 1280, 720
    sheet = Image.new("RGB", (3 * tw, th), (8, 10, 12))
    for i, (_, p, _) in enumerate(targets):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, (i * tw, 0))
    strip = TESTS / "qc_opening_title_strip.png"
    sheet.save(strip)
    print(f"  片头 QC → {TESTS / 'qc_opening_title.png'} / {strip.name}")


def contact_sheet(shots: list[tuple[Path, str]], out: Path, cols: int = 3) -> None:
    tw, th = 640, 360
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (8, 10, 12))
    for i, (p, label) in enumerate(shots):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(f"  contact sheet → {out}（{len(shots)} 帧）")


# --------------------------------------------------------------------------- #
def main() -> None:
    try:                                    # Windows 控制台默认 GBK，统一按 UTF-8 输出
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="文字层渲染 / 烧录 / 目检")
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["ass", "test", "qc", "opening", "burn", "all"])
    ap.add_argument("--video", help="burn: 已剪辑视频")
    ap.add_argument("--audio", help="burn: 原音轨")
    ap.add_argument("--out", help="burn: 输出路径")
    args = ap.parse_args()

    if args.cmd in ("ass", "all"):
        tl = ht.load_timeline()
        events = ht.build_events(tl)
        ht.write_ass(ROOT / ASS_REL, tl, events)
        errs = ht.check(tl, events)
        if errs:
            print("校验失败：\n  " + "\n  ".join(errs))
            raise SystemExit(1)
        print("  film.ass 校验通过")

    if args.cmd in ("test", "all"):
        burn_test()

    if args.cmd in ("qc", "all"):
        qc_film()

    if args.cmd in ("opening", "all"):
        qc_opening()

    if args.cmd == "burn":
        if not (args.video and args.audio and args.out):
            raise SystemExit("burn 需要 --video --audio --out")
        burn_film(args.video, args.audio, args.out)


if __name__ == "__main__":
    main()
