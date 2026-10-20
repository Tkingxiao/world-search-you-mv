import io

p = 'mv/docs/创作手记.md'
s = io.open(p, encoding='utf-8').read()
s = s.replace('OFPLINE', 'OFFLINE')
s = s.replace(
    'EEVEE-Next 逐帧直出 2560×1440 H.264 mp4（12 samples + AgX + 合成器 Glare）。',
    'EEVEE-Next 逐帧直出 2560×1440 H.264 mp4（8–12 samples + AgX + 合成器 Glare；为压住显存与多进程争用，正式渲染统一 8 samples，最重的打字页镜头 10）。')
s = s.replace(
    '无声加速技巧：单网格 bmesh 建模（场景仅 5–17 个对象）、2–4 个 Blender 进程并行、每镜独立进程避免场景累积。',
    '加速技巧：单网格 bmesh 建模（场景仅 5–17 个对象）、关闭 raytracing / 体积 tile 8 / 小灯不投阴影、每镜独立进程避免场景累积、4 个 Blender 进程并行（实测单进程约 1.2–2 s/帧，4 进程聚合约 2.5 帧/秒，全片 17,721 帧约 2 小时）。')
io.open(p, 'w', encoding='utf-8').write(s)
print('patched', len(s))
