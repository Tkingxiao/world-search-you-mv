"""Final README polish: v2 file size + validation note."""
import io

P = r'D:\Code\Code MV\new-word.search(you)\README.md'
s = io.open(P, encoding='utf-8').read()

old = '| `mv/out/final/world.search(you)_final_v2.mp4` | **v2 成片**（H.264 CRF16 / AAC 320k，split-tone 调色 + 暗角 + 颗粒 + 字幕/HUD） |'
new = ('| `mv/out/final/world.search(you)_final_v2.mp4` | **v2 成片**（1541 MB / 1.54 GiB，H.264 CRF16 43.8 Mbps / AAC 320k，'
       'split-tone 调色 + 暗角 + 颗粒 + 字幕/HUD；17,721 帧、295.350s；34/34 项自动校验 PASS，报告见 '
       '`mv/out/tests/ui/final_qc_v2/validate_v2.json`） |')
assert old in s
s = s.replace(old, new, 1)

old2 = '| `mv/out/final/poster_2560x1440.png` / `poster_1800x2700.png` | 海报（横版 1440p / 竖版） |'
new2 = '| `mv/out/final/poster_2560x1440.png` / `poster_1800x2700.png` | 海报（v2 场景重渲：横版 2560×1440 / 竖版 1800×2700） |'
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('[ok] README polished')
