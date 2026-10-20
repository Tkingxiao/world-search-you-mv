# CHAR_INTERFACE — 2.5D 纸偶角色 API（char_paper.py）

`mv/build/char_paper.py` 把官方立绘做成**一张带 alpha 的纸卡**：不是建模、不是雕刻、不是骨骼蒙皮。
纸卡正面就是官方立绘（1:1 像素，不重绘、不重打光），用 UV 偏移在图集里切换表情，用
`Simple Deform(BEND)` 让纸微微弯，用 2 mm `Solidify` 给纸一个边——侧看时角色塌成一条线。

素材授权：CC BY-NC-SA 4.0（上善 → ZipZipPipe → Small-tailqwq/dsh-deep-whale → dsh-whale-galgame，
见 `mv/ref/art/galgame/NOTICE.md`）。衍生使用需保留署名、非商业、同协议。

---

## 1. 图集

| 文件 | 说明 |
|---|---|
| `mv/assets/char/expr_atlas.png` | 3372×6066 RGBA，3×3 格；8 表情 + `maid`（提裙伸手） |
| `mv/assets/char/expr_atlas.json` | 每格 rect（**x0,y0,x1,y1**，不是宽高）、alpha bbox、feet/head/face 锚点（像素 + UV）、Mapping 的 scale/location |
| `mv/assets/char/maid_card.png` + `.json` | 单独导出的 maid 纸卡（给别的合成/贴图流程用） |

格子：cell 1124×2022，脚底锚点固定在同一格像素 (562, 2013)，`HEIGHT_REF_PX = 1653`
（1653 px = 1.75 m 身高参考）。所有表情**像素 1:1 贴入**，从不重采样，所以官方图零失真。
`maid` 原画在 1.2× 密的画布上，已按 `scale_ref_px = 2006` 归一化到同一身高。

`mv/assets/char/make_atlas.py` 是图集生成脚本（可重跑，纯 numpy/Pillow）：
透明像素做 8 px 颜色扩散（bleed），避免双线性/多级渐远采样时出现白边。

## 2. 快速用法（10 行）

```python
import sys; sys.path.insert(0, r"D:\Code\Code MV\new-word.search(you)\mv\build")
import char_paper as paper

ctrl = paper.build_character(name="fish", expr="cheerful", height=1.75,
                             location=(0, 0, 0), bend=2.5)
ctrl["set_expression"]("starry", frame=48)   # 硬切（CONSTANT 插值），可 K 帧
ctrl["set_bend"](4.0, frame=48)              # 纸的软弯，可 K 帧
ctrl["set_edge_glow"](paper.PALETTE["cyan"], 2.0)
ctrl["set_fog"](paper.PALETTE["ink"], 0.014) # EEVEE 不雾化 blended 面，必须手接
ctrl["set_flash"](1.0, frame=60)             # 切表情时的白闪（帧 60 亮、帧 62 灭）
```

`build_character()` 返回的 `ctrl` 是个 dict：

| key | 类型 | 说明 |
|---|---|---|
| `root` | Empty | 整个角色挂在它下面；移动/旋转它 = 走位/朝向 |
| `card` | Mesh | 纸卡（局部 +Z 朝上，脚底在 z=0，正面朝 **-Y**） |
| `head` / `head_card` | Empty / Mesh | 仅 `split_head=True` 时存在 |
| `mat` / `paper_mat` / `rim_mat` | Material | 正面立绘 / 背面纸色 / 纸边发光 |
| `image` | Image | `expr_atlas.png`（sRGB, STRAIGHT alpha） |
| `uv_mapping_node` | ShaderNodeMapping | 表情切换靠它的 scale/location |
| `image_node` / `bsdf` / `output` | nodes | 需要自定义时用 |
| `expr` / `height` / `px_per_m` / `card_w` / `card_h` | 数据 | 当前状态与尺寸 |
| `set_expression` `set_bend` `set_edge_glow` `add_alpha_edge` `set_flash` `set_backface` `set_fog` `anchor` | lambda | 见下 |

## 3. API

```python
build_character(name="fish", expr="cheerful", height=1.75, location=(0, 0, 0),
                split_head=False,
                yaw=0.0,            # root 的 Z 旋转（度）；0 = 正面朝 -Y
                bend=2.5,           # Simple Deform BEND 角度（度），纸的软弯
                bend_lateral=None,  # 横向弯（默认 = bend*0.35），轴 Z
                edge_mm=2.0,        # Solidify 厚度，纸边
                glow=1.0,           # 纸边发光强度
                glow_strength=None, # 同上（别名）
                backface="art",     # 'art' = 双面印刷（默认）/ 'paper' = 背面空白纸
                head_split=0.80, head_overlap=0.02,   # split_head 的切点（占身高比）
                nx=24, nz=64,       # 纸卡细分（bend 平滑度）
                collection=None)    # 不传则放 "CHAR" collection
```

| 方法 | 说明 |
|---|---|
| `set_expression(expr, frame=None, flash=0)` | 表情硬切。`expr` ∈ `EXPRESSIONS` + `maid`，也接受别名（见 §5）。给 `frame` 会插 CONSTANT 关键帧，**不会**有中间过渡；`flash>0` 时同时打一个白闪。 |
| `set_bend(degrees, lateral=None, frame=None)` | 纸的软弯。`degrees` 是 BEND 总角，横向默认 `degrees*0.35`。K 帧后可做"风吹纸"的呼吸。 |
| `set_edge_glow(color=None, strength=None, frame=None)` | 纸边发光颜色/强度。TREATMENT：0.3 mm 发光纸边 → 青色。 |
| `add_alpha_edge(thickness_mm=2.0)` | 重建 Solidify（改纸厚）。 |
| `set_flash(amount, frame=None)` | 白闪：0=正常，1=整张纸发白（Emission 乘数）。切表情那帧给 0.8~1，2 帧后回 0。 |
| `set_backface(mode, color=None)` | `'art'` 双面印刷 / `'paper'` 背面纯纸色。 |
| `set_fog(color=None, density=None)` | 空中透视：把纸卡颜色按相机距离往雾色混。**EEVEE-Next 在体积雾之后合成 blended 面，纸卡不会被场景雾影响**，所以必须用它手动接上，否则角色在雾里会"浮"出来。 |
| `anchor(which="feet")` | 世界坐标锚点：`feet` / `head` / `face`（face 是肤色质心，含手，偏低；取景对准用 `head`）。 |

模块级：`EXPRESSIONS`（8 个）、`EXTRA_POSES`、`ALL_POSES`、`ALIASES`、`PALETTE`、
`ATLAS`（json 内容）、`mapping_for(expr)`、`atlas_image()`、`clear_character(ctrl)`。

## 4. 渲染要点

- 材质：Principled + 图集颜色/alpha，`surface_render_method = "BLENDED"`（24 samples 下边缘干净，
  不是 DITHERED 的噪点），`use_transparent_shadow=True`（阴影按 alpha 剪影），
  `use_backface_culling=True`（挡住背面，避免轮廓 1 px 淡边）。
- **纸边发光**：2 mm Solidify 的 rim 面用 Emission 材质（slot 2），并按"纸卡有多侧对镜头"开合：
  `|dot(视线, 纸卡法线)|` 越接近 0 越亮，POWER 4。正面/斜 35° 时纸边完全透明（否则矩形纸边会在
  画面上画出一条 1 px 竖线），侧到 90° 时满亮 → 塌成一条发光线。
- **EEVEE 体积雾不作用在 blended 面上** → 用 `set_fog()`；场景雾密度与 `set_fog` 密度给同一个值。
- 光照：纸卡是 albedo 打印，灯光只做氛围。主光总辐照 ≈ π 时立绘以 ~1.0× 原色还原
  （`char_preview.py --mode calib` 的验证：RGB MAE 4.31/255 = 1.7%，无曝光偏差）。
- 相机：`anchor("head")` 取景；85–110 mm 全身/半身；200 mm 大特写会看出源图分辨率。
- **景深（重要）**：EEVEE-Next 的 DOF 深度预通道**不记录 BLENDED（alpha 混合）面**，所以纸卡被
  当成"背景"套上背景的 CoC —— 只要 `fstop ≤ 8`，她整张卡就会糊掉（实测边缘能量 lap-p99：
  BLENDED+DOF 31 vs DITHERED+DOF 57 vs 关 DOF 57；把材质切 DITHERED 立刻变清晰，证明是深度问题）。
  三个可选对策，按推荐顺序：
  1. **有角色的镜头把相机 DOF 关掉**（`K.cam_path(..., dof=False)`）——纸卡本身是平的，不需要景深；
  2. 必须留 DOF 时把 `fstop` 提到 **16 以上**（实测 f/16 基本恢复清晰，代价是背景也没虚化了）；
  3. 真要"角色清晰 + 背景虚化"：把 `ctrl["mat"].surface_render_method = "DITHERED"`（会写深度），
     但 alpha 边缘变成抖动噪点，需要把 samples 提到 48–64，12 samples 下边缘会脏。

## 5. 限制 / 已知问题

1. **没有 `sad` 表情**：官方 8 张里没有哭/难过，`sad`/`cry` 映射到 `shy`（低头、眼睑下垂，最接近）。
   若镜头需要真哭，只能在后期叠纸屑/泪滴，或找主美术补图。
2. **8 张立绘姿势不同**（手的位置、站姿、裙摆方向），不是同一张画换脸。切表情时姿势会跳——
   TREATMENT 要求"硬切"所以这是风格内行为；但**同一镜头里连续切表情会看到身体跳**，镜头脚本里
   要么切在剪辑点/闪光帧上，要么接受这种 2D 自觉。
3. 源图 935 px 宽（1.75 m 身高 → ≈1.5 px/mm）：全身 2K 够用，**超过 200 mm 的大特写会糊**。
4. 8 张 bbox 高度差 ±4%（构图/姿势差异），图集按脚底锚点对齐，身高不额外归一化（避免缩放失真）。
5. `maid` 原画 1122×2019（1.2× 密），已按身高归一化；它只有一个姿势。
6. 纸边发光只在侧看时出现，**正面/斜视角看不到纸边**——这是有意的（否则会露出矩形纸边）。
7. 双面印刷：绕到背面看到的是镜像立绘。要"背面是白纸"用 `set_backface('paper')`。
8. `split_head=True` 会把头/身切成两张卡（头卡在 1.5 mm 前面），用于轻微歪头；默认关闭。
9. Blender 每次 `build_character` 会打印一行 `RNA_float_set: NodeSocket.default_value not found.`，
   无害（某个 socket 在 4.5 改名）。
10. 卡是**平面**：不要指望它接收真实的高光/反射；它的"光"来自打印的颜色 + 发光纸边 + 雾。

## 6. 预览渲染

```bash
# 快速 5 视图（front / 3-4 / edge / back / face），960×540
blender -b --factory-startup -P mv/build/char_preview.py -- --mode quick
# 8 表情 + maid 静帧 1920×1080
blender -b --factory-startup -P mv/build/char_preview.py -- --mode stills
# 4 秒 360° 转台 1920×1080（240 帧 @60fps）
blender -b --factory-startup -P mv/build/char_preview.py -- --mode turntable
# 英雄帧 2560×1440（starry，110 mm，f/2.8）
blender -b --factory-startup -P mv/build/char_preview.py -- --mode hero
# 色彩保真校验：正交相机 1:1 渲一格，和 atlas cell 做像素差
blender -b --factory-startup -P mv/build/char_preview.py -- --mode calib
```

产物在 `mv/out/tests/char/`：`expr_*.png`、`turntable/frame_####.png`、`turntable_360.mp4`、
`hero_2560x1440.png`、`_diag/`（迭代/诊断图）。场景：暗青雾 + 暖主光 + 青轮廓光 + 金射灯，
AgX Medium High Contrast，24 samples，Glare BLOOM。

## 7. Shot integration notes（s10/s13/s14/s15 实战踩坑）

给后续写 `mv/build/shot_*.py` 的同学（都是我在 4 个镜头里实际撞到的）：

1. **`K.cam_path()` 的 keys 必须是 5 元组** `(frame, loc, target, lens, fstop)`。
   少传 fstop 会在 `mv/build/shotkit.py:107` 抛
   `ValueError: not enough values to unpack (expected 5, got 4)`；补齐任意 fstop 即可（dof 已被 lead 全局关掉）。
2. **`SP.build_koinobori(color=...)` 只能传十六进制字符串或 `PEER_COLORS` 键名，不能传 RGB 元组**：
   传元组会在 `mv/build/specimens.py:159` 的 `hex_rgba()` 里抛
   `AttributeError: 'tuple' object has no attribute 'lstrip'`。例：`'#ff5733'`、`'#3878ff'`、`'#ffc756'`、`'#eeeeea'`。
3. **`C.light(..., target=...)` 的 target 必须是 Blender 对象，不能传坐标元组**：
   `TypeError: bpy_struct: item.attr = val: TrackToConstraint.target expected a Object type`。
   正确姿势：先建灯，再 `C.look_at(light_obj, point)`。
4. **`C.illustration_card(..., emission_strength=0)` 不会接 Emission Color/Strength 节点**；
   之后再给 `bsdf.inputs['Emission Strength']` 打关键帧是无效的（表现为"该发光的东西永远不亮"）。
   要做发光卡，建卡时给一个非零 `emission_strength`，或自己把贴图 Color 接到 `Emission Color` 上。
5. **EEVEE-Next 里"不透明 + 自发光"的大卡片仍然遮挡灯光**：它会在地面/背景上投出硬阴影带
   （我 s13 找了一轮：调雾色、加大地板都没用）。可靠的解法是**在地面上叠一张纯自发光平面**
   （`C.emissive(...)` + `C.plane(...)`，`visible_shadow=False`，贴地 +0.012 m），或在建卡后
   统一扫一遍 `ob.visible_shadow = False`（我 s15 就是这么做的）。
6. **隐藏 `root` 空物体不会隐藏它的子卡片**，要隐藏就 `ctrl["card"]` / `ctrl["head_card"]`。
7. **硬切表情**用 `ctrl["set_expression"](expr, frame=...)`（内部 CONSTANT 插值），
   溶解/闪光连续镜头用 `set_flash()` + `set_edge_glow()` 打关键帧即可（s13→s14 的交接：
   s13 末帧只剩青色轮廓 → s14 首帧 `set_flash(0.80)` + `set_edge_glow(3.0)` 白色发光剪影）。
8. `K.char_actor()` 会自动朝向 `face=` 点（yaw = atan2 + 180），镜头在 +Y 侧时纸面朝向镜头，不需要额外翻面。
