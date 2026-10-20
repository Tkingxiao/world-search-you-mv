"""v2 burn patch against the *current* final_encode.py (grade B, relative ass, no -shortest)."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\tools\final_encode.py'
s = io.open(P, encoding='utf-8').read()

old = '''VF_GRADE = ("vignette=angle=PI/7,"
            "ass=%s:fontsdir=%s,"
            "noise=alls=6:allf=t+u" % (ASS.replace('\\\\', '/'), FONTS.replace('\\\\', '/')))'''
new = '''OVERLAY = os.path.join(MV, 'mv', 'overlay')

# Grade B (ui-lab prototype): split-tone -- shadows cooler, highlights warmer -- then
# vignette, subtitles/HUD, film grain. The burn runs with cwd=mv/overlay and refers to
# film.ass / fonts relatively: ffmpeg's filtergraph parser cannot handle the spaces in
# this project's absolute path.
VF_GRADE = ("colorbalance=rs=-0.04:gs=0.0:bs=0.04:rh=0.03:gh=0.0:bh=-0.03,"
            "vignette=angle=PI/7,"
            "ass=film.ass:fontsdir=fonts,"
            "noise=alls=7:allf=t+u")'''
assert old in s, 'VF_GRADE anchor missing'
s = s.replace(old, new, 1)

old_run = """def run(cmd, tail=1500):
    print(' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=MV, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')"""
new_run = """def run(cmd, tail=1500, cwd=None):
    print(' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=cwd or MV, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')"""
assert old_run in s
s = s.replace(old_run, new_run, 1)

old_burn = """    ok = run(cmd)
    print('final ->', OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 'FAIL')
    return ok"""
new_burn = """    ok = run(cmd, cwd=OVERLAY)
    print('final ->', OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 'FAIL')
    return bool(ok and os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024 * 1024)"""
assert old_burn in s
s = s.replace(old_burn, new_burn, 1)

# keep the last frame: -shortest trims it (17720 vs 17721)
old_short = "           '-shortest', '-movflags', '+faststart', OUT]"
assert old_short in s
s = s.replace(old_short, "           '-movflags', '+faststart', OUT]", 1)

io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] final_encode v2 patched')
