"""final_encode v2: ffmpeg runs from mv/overlay with *relative* ass paths (spaces in
the absolute path broke the filtergraph parser), and failures now exit non-zero."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\tools\final_encode.py'
s = io.open(P, encoding='utf-8').read()

old_head = """ASS = os.path.join(MV, 'mv', 'overlay', 'film.ass')
FONTS = os.path.join(MV, 'mv', 'overlay', 'fonts')
OUT = os.path.join(FINAL, 'world.search(you)_final.mp4')

VF_GRADE = ("vignette=angle=PI/7,"
            "ass=%s:fontsdir=%s,"
            "noise=alls=6:allf=t+u" % (ASS.replace('\\\\', '/'), FONTS.replace('\\\\', '/')))"""
new_head = """OVERLAY = os.path.join(MV, 'mv', 'overlay')
ASS = os.path.join(OVERLAY, 'film.ass')
FONTS = os.path.join(OVERLAY, 'fonts')
OUT = os.path.join(FINAL, 'world.search(you)_final.mp4')

# NOTE: ffmpeg's filtergraph parser chokes on the spaces in the project path, so the
# burn step runs with cwd=mv/overlay and refers to film.ass / fonts relatively.
VF_GRADE = ("vignette=angle=PI/7,"
            "ass=film.ass:fontsdir=fonts,"
            "noise=alls=6:allf=t+u")"""
assert old_head in s, 'header anchor missing'
s = s.replace(old_head, new_head, 1)

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

old_burn = "    ok = run(cmd)\n    print('final ->', OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 'FAIL')\n    return ok"
new_burn = ("    ok = run(cmd, cwd=OVERLAY)\n"
            "    print('final ->', OUT, os.path.getsize(OUT) if os.path.exists(OUT) else 'FAIL')\n"
            "    return bool(ok and os.path.exists(OUT) and os.path.getsize(OUT) > 10 * 1024 * 1024)")
assert old_burn in s
s = s.replace(old_burn, new_burn, 1)

old_main = """if __name__ == '__main__':
    ap = argparse.ArgumentParser()"""
new_main = """if __name__ == '__main__':
    import sys
    rc = 0
    ap = argparse.ArgumentParser()"""
assert old_main in s
s = s.replace(old_main, new_main, 1)

old_tail = """    if a.burn:
        burn(fast=a.fast)
    if a.qc:
        qc()"""
new_tail = """    if a.burn:
        if not burn(fast=a.fast):
            rc = 1
    if a.qc:
        qc()
    sys.exit(rc)"""
assert old_tail in s
s = s.replace(old_tail, new_tail, 1)

io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] final_encode patched')
