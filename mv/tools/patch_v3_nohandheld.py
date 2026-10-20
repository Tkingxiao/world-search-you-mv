"""v3: kill the handheld camera noise (user feedback: 镜头一直在晃).

`add_handheld` becomes a no-op so every existing call site (cam_path's automatic call
plus the explicit per-shot calls) stays valid but adds no noise. Then point the burn at
a new v3 output file so the v2 deliverable is never overwritten.
"""
import io
import py_compile

MV = r'D:\Code\Code MV\new-word.search(you)'

P = MV + r'\mv\build\shotkit.py'
s = io.open(P, encoding='utf-8').read()
old = '''def add_handheld(cam, amp=0.012, scale=1.6, seed=0, rot_amp=0.0045):
    """Subtle operator drift: noise modifiers on location + rotation curves.

    Gives every move a living, hand-held quality without fighting the framing.
    Call AFTER cam_path() so the modifiers ride on the baked keys.
    """
    rnd = __import__('random').Random(seed)'''
new = '''def add_handheld(cam, amp=0.012, scale=1.6, seed=0, rot_amp=0.0045):
    """DISABLED (v3): the noise drift read as constant camera shake in motion.

    Kept as a no-op so every existing call site (cam_path's automatic call and the
    explicit per-shot calls) keeps working while the cameras stay rock steady.
    """
    return cam
    rnd = __import__('random').Random(seed)  # noqa: unreachable (kept for reference)'''
assert old in s, 'add_handheld anchor missing'
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('[ok] add_handheld disabled')

P2 = MV + r'\mv\tools\final_encode.py'
s2 = io.open(P2, encoding='utf-8').read()
old2 = "OUT = os.path.join(FINAL, 'world.search(you)_final_v2.mp4')"
new2 = "OUT = os.path.join(FINAL, 'world.search(you)_final_v3.mp4')"
assert old2 in s2, 'final_encode OUT anchor missing'
s2 = s2.replace(old2, new2, 1)
io.open(P2, 'w', encoding='utf-8').write(s2)
py_compile.compile(P2, doraise=True)
print('[ok] burn output -> final_v3.mp4')
