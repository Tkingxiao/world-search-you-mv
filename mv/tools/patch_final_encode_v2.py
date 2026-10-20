"""v2 burn: split-tone grade B, no -shortest (keeps the last frame), grain 7."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\tools\final_encode.py'
s = io.open(P, encoding='utf-8').read()

old = '''VF_GRADE = ("vignette=angle=PI/7,"
            "ass=film.ass:fontsdir=fonts,"
            "noise=alls=6:allf=t+u")'''
new = '''# Grade B (ui-lab prototype): split-tone -- shadows cooler, highlights warmer --
# then vignette, subtitles/HUD, film grain. Order matters: vignette before ASS so the
# HUD is not darkened; grade before ASS so the paper-white text stays clean.
VF_GRADE = ("colorbalance=rs=-0.04:gs=0.0:bs=0.04:rh=0.03:gh=0.0:bh=-0.03,"
            "vignette=angle=PI/7,"
            "ass=film.ass:fontsdir=fonts,"
            "noise=alls=7:allf=t+u")'''
assert old in s, 'VF_GRADE anchor missing'
s = s.replace(old, new, 1)

# keep the final frame: -shortest trims one frame (17720 vs 17721)
old2 = "           '-shortest', '-movflags', '+faststart', OUT]"
new2 = "           '-movflags', '+faststart', OUT]"
assert old2 in s, '-shortest anchor missing'
s = s.replace(old2, new2, 1)

io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] final_encode v2: grade B, no -shortest')
