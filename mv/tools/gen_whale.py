"""Generate a paper-cut whale silhouette PNG (white shape + alpha) for the merge shot."""
import math, os
from PIL import Image, ImageDraw, ImageFilter

OUT = r'D:\Code\Code MV\new-word.search(you)\mv\assets\whale_silhouette.png'
S = 4
W, H = 1600, 1000


def rot(pts, ang, cx, cy):
    a = math.radians(ang)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a),
             cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


def ellipse(cx, cy, rx, ry, n=160):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def blob(cx, cy, rx, ry, ang=0.0, n=160):
    return rot(ellipse(cx, cy, rx, ry, n), ang, cx, cy)


def smooth_curve(pts, n=90):
    """Catmull-Rom through pts."""
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        for j in range(n // (len(pts) - 1) + 1):
            t = j / max(1, (n // (len(pts) - 1)))
            t2, t3 = t * t, t * t * t
            out.append((0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    return out


img = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
WHITE = (255, 255, 255, 255)


def P(pts):
    return [(x * S, y * S) for x, y in pts]


# ---- body (chubby, facing left)
d.polygon(P(blob(780, 545, 372, 280, ang=-6)), fill=WHITE)
d.polygon(P(blob(690, 655, 300, 165, ang=-4)), fill=WHITE)   # belly
d.polygon(P(blob(540, 500, 262, 236, ang=2)), fill=WHITE)    # head dome

# ---- tail: smooth peduncle and fluke
tail_pts = [(1040, 470), (1110, 452), (1180, 430), (1240, 400), (1300, 355),
            (1355, 300), (1418, 262), (1436, 320), (1390, 402), (1418, 468),
            (1448, 520), (1386, 566), (1306, 548), (1236, 566), (1160, 590), (1040, 604)]
d.polygon(P(smooth_curve(tail_pts, 120)), fill=WHITE)
d.polygon(P(blob(1140, 520, 132, 92, ang=-14)), fill=WHITE)

# ---- pectoral fin (front, pointing down-left) - smooth
fin_pts = [(690, 650), (620, 712), (586, 790), (622, 848), (706, 862), (786, 820),
           (830, 744), (812, 674)]
d.polygon(P(smooth_curve(fin_pts, 90)), fill=WHITE)

# ---- small dorsal fin
dorsal = [(880, 300), (912, 246), (952, 240), (1000, 300), (1016, 336), (960, 344)]
d.polygon(P(smooth_curve(dorsal, 60)), fill=WHITE)

# ---- bow above the head (maid reference)
bx, by = 486, 214
d.polygon(P([(bx - 6, by), (bx - 104, by - 54), (bx - 92, by + 44)]), fill=WHITE)
d.polygon(P([(bx + 6, by), (bx + 104, by - 54), (bx + 92, by + 44)]), fill=WHITE)
d.polygon(P(ellipse(bx, by, 22, 22)), fill=WHITE)

# ---- droplets from blowhole
for (bx2, by2, r) in ((352, 268, 24), (300, 210, 16), (258, 158, 10)):
    d.polygon(P(ellipse(bx2, by2, r, r)), fill=WHITE)

# ---- close small concavities, then soften
alpha = img.getchannel('A')
alpha = alpha.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
img.putalpha(alpha)

# ---- eye: punch a hole
eye = Image.new('L', img.size, 0)
ed = ImageDraw.Draw(eye)
ed.polygon(P(blob(452, 432, 25, 33, ang=-6)), fill=255)
img.putalpha(Image.composite(Image.new('L', img.size, 0), img.getchannel('A'), eye))

# ---- mouth: punch a small smile
mouth = Image.new('L', img.size, 0)
md = ImageDraw.Draw(mouth)
pts = [(286 + i * 7, 566 + 30 * math.sin(math.pi * i / 26)) for i in range(27)]
md.line([(x * S, y * S) for x, y in pts], fill=255, width=int(8 * S))
img.putalpha(Image.composite(Image.new('L', img.size, 0), img.getchannel('A'), mouth))

img = img.resize((W, H), Image.LANCZOS)
img = img.filter(ImageFilter.GaussianBlur(1.0))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print('WROTE', OUT, img.size)
