"""Update the delivery paragraph in 创作手记.md with final v2 numbers."""
import io

P = r'D:\Code\Code MV\new-word.search(you)\mv\docs\创作手记.md'
s = io.open(P, encoding='utf-8').read()
old = '- **交付**：v2 成片为 `mv/out/final/world.search(you)_final_v2.mp4`；v1 成片保留作为兜底。'
new = ('- **交付**：v2 成片为 `mv/out/final/world.search(you)_final_v2.mp4`（2560×1440@60 / 17,721 帧 / 295.350s / '
       'H.264 43.8 Mbps / 1.54 GB，含字幕+HUD+split-tone+暗角+颗粒）；v1 成片（933 MB）保留作为兜底；海报 v2 见 '
       '`mv/out/final/poster_2560x1440.png` 与 `poster_1800x2700.png`。')
assert old in s, 'anchor missing'
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('[ok] 创作手记 updated')
