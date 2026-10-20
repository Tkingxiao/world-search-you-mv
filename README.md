# world.search(you); — MV 工程

非商业同人 MV：Mili《world.search(you);》（专辑 *Hue*，2025）的影像化再创作，同时是对"大肥鱼 / DeepSeek-V4.1-Flash"这一社区设定的回应。
全片程序化生成：Blender 4.5.3 EEVEE-Next 逐镜渲染 + ffmpeg/libass 合成。角色没有三维建模——只用官方立绘做 2.5D 纸偶（硬约束，也是主题）。

当前渲染档案：**1920×1080 / 60fps / 10 spp / 17,721 帧 / 4:55.35**

历史 v2 成片（1440p）：**2560×1440 / 60fps / 17,721 帧 / 4:55.35**

---

## 交付物（渲染产物，均已 `.gitignore`，需本地重建，不随仓库分发）

| 文件 | 说明 |
|---|---|
| `mv/out/final/world.search(you)_final_v4.mp4` | **当前 v4 成片**（1920×1080 / 60fps / 17,721 帧 / 295.350s，H.264 CRF16 / AAC 320k，split-tone 调色 + 暗角 + 颗粒 + 字幕/HUD；已修复 2:53 地板 z-fighting 等全部场景问题） |
| `mv/out/final/master_video_no_text.mp4` / `master_audio.wav` | 无字母版 + 音频轨（拼接中间产物） |
| `mv/out/final/world.search(you).srt` | 中英双语字幕（外挂） |
| `mv/out/shots/s01..s15.mp4` | 逐镜 1080p60 母版 |
| `mv/docs/创作手记.md` | 创作阐述（主题、视觉、技术、署名） |
| `mv/docs/TREATMENT.md` | 前期分镜/视觉方案 |
| `mv/docs/UI_SPEC.md` / `CHAR_INTERFACE.md` / `SPECIMEN_INTERFACE.md` / `SPECIMEN_NOTES.md` / `SHOT_CONTRACT.md` | 各管线的接口文档 |

> 旧版本成片（v1 1080p 早期版、v2/v3 1440p 版）与 lookdev / 抓取参考 / perf 缓存已从工作树清理，历史归档在本地 `_archive_old_pre_v4_*`，同样不入库。

## 仓库里有什么 / 不包含什么

本仓库**只保留源代码、文档、README，以及标了来源的官方立绘素材**。以下全部经 `.gitignore` 排除：

- 渲染缓存与产物：`mv/out/`、`out/`、`*.mp4`、`*.wav`、`*.npy`、`*.blend`
- **版权音频**：Mili 原曲 `*.flac/*.mp3/*.lrc` 不随仓库分发（见下方"自行准备"）
- **专有字体**：`mv/overlay/fonts/` 里的 MS YaHei / Consolas / Georgia 版权归微软，不入库
- 生成物：`mv/overlay/cards/`（由 `make_cards.py` 重建）
- 参考抓取：`mv/ref/`（上游社区仓库/网页缓存与第三方素材，不重新分发）

**有意保留的图像素材**（随仓库分发，来源与许可见"素材来源与致谢"）：
`mv/assets/char/`（`expr_atlas.png`、`maid_card.png`、`halo_serious.png`、`whale_paper*.png` 及同名 `.json`/生成脚本）、`mv/assets/whale_silhouette.png`。

### 自行准备（一次即可，然后按"重建流程"跑）

- **音乐**：把 Mili《world.search(you);》音频放到项目根目录，命名 `Mili - world.search (you) ;.flac`（或改 `mv/tools/assemble.py` 里的音频路径）。仓库不含此文件。
- **字体**：`mv/overlay/film.ass` 使用 微软雅黑 / Consolas / Georgia；在 Windows 上系统已自带，libass 会按字体名解析；其它系统请自行安装同名字体或改 `.ass` 的 `Fontname`。

## 目录

```
mv/
  data/        timeline.json（歌词/中文/节拍/阶段/memory 事件）、shot_plan.json、shots.json   [入库]
  build/       core.py geo.py world.py world_theater.py stage.py shotkit.py
               char_paper.py specimens.py（队友产出）
               shot_s01..s15.py（每镜一个模块）
               render_shot.py（单镜渲染入口）、poster.py                       [入库]
  overlay/     film.ass（字幕+HUD，345 事件）、hud_timeline.py、render_overlay.py、
               make_cards.py                                                   [入库]
               fonts/（专有字体，不入库）、cards/（生成物，不入库）
  tools/       render_queue.py（并行队列）、assemble.py（校验/拼接/音频）、
               final_encode.py（烧录+QC）、make_srt.py、build_timeline.py、
               setup_1080p_tasks.py（计划任务托管）、finalize_and_clean_1080p.py [入库]
  assets/      char/（官方立绘素材，CC BY-NC-SA，入库并致谢）、whale_silhouette.png [入库]
  docs/        创作手记与接口文档                                                [入库]
  out/         shots/、final/、jobs/ 等渲染产物与日志                          [不入库，可重建]
  ref/         上游企划/网页抓取参考                                            [不入库]
```

## 重建流程

```powershell
# 0) 依赖：Blender 4.5.3（D:\Blender Foundation\Blender 4.5\blender.exe）、ffmpeg（C:\ffmpeg\bin）、Python3（numpy/Pillow）
# 1) 单镜渲染（固定 1080p60 / 10spp；建议最多 3 个并行进程）
python mv/tools/render_queue.py --shots s03,s06,s09 --tag A
python mv/tools/render_queue.py --shots s04,s11    --tag B
# 2) 校验帧数/分辨率/拼接母版/生成音频
python mv/tools/assemble.py --check
python mv/tools/assemble.py --video
python mv/tools/assemble.py --audio
# 3) 烧字幕/HUD + split-tone 调色 + 暗角 + 颗粒 → 当前成片
python mv/tools/final_encode.py --burn --fast
python mv/tools/final_encode.py --qc
```

1080p / 10 spp 单进程约 0.6 s/帧；3 进程并行实测聚合约 2.7 fps，全片 17,721 帧约 1.8–2.2 小时。4 进程会接近显存/CPU 上限，不建议继续加并发。

> 旧的 1440p 镜头母版（例如当前 `s02.mp4`）和 0 帧残片不属于当前档案；`assemble.py --check` 会报 `RES MISMATCH`，重渲前需清理。字幕/HUD 仍按 2560×1440 的 `film.ass` 制作，libass 烧录时会等比缩到 1080p。

## 素材来源与致谢 / Credits

**音乐**
- Mili《world.search(you);》，词 Cassie Wei，曲 Yamato Kasai & Cassie Wei，出自专辑 *Hue*（2025）。
- 本仓库**不含**该曲目音频（版权归 Mili / Cinematic Room 所有）；请从正规渠道购买或获取后自行放入根目录再合成。此处仅为非商业同人致敬。

**角色与立绘（已随仓库保留、来源已标注）**
- 角色"大肥鱼 / 溟月"（DeepSeek-V4.1-Flash 社区设定）：
  - 原作：**上善无形**
  - 女仆版人设：**ZipZipPipe**
  - 立绘：**Small-tailqwq**
  - 表情图集：**JAdpp**
- 上述素材位于 `mv/assets/char/`，采用 **CC BY-NC-SA 4.0** 授权；`mv/assets/whale_silhouette.png`、`mv/assets/char/make_*.py` 为本工程基于该设定生成的派生轮廓。
- 本片整体同以 **CC BY-NC-SA 4.0** 分享，仅限非商业使用。

**叙事框架参考**
- 社区企划 *world-search-you-dsh-pv*（[`MisakaZentai/world-search-you-dsh-pv`](https://github.com/MisakaZentai/world-search-you-dsh-pv)）；本片为独立的影像化再创作，未复制其工程文件。原始抓取的上游素材/网页缓存放在 `mv/ref/`（已 `.gitignore`，不重新分发）。

**工具与技术**
- 渲染：[Blender 4.5.3](https://www.blender.org/) EEVEE-Next（Cycles / OIDN 曾用于测速基准，见 `mv/out` 相关脚本）。
- 合成/字幕：[FFmpeg](https://ffmpeg.org/) + libass（`mv/overlay/film.ass`）。
- 数据处理：Python 3 + [NumPy](https://numpy.org/) + [Pillow](https://pillow.readthedocs.io/)。
- 字体：微软雅黑 / Consolas / Georgia 版权归 Microsoft，本仓库不打包，需系统自带或自行安装。

**致谢**：感谢上述音乐人、画师与社区企划作者；本作品为学习与致敬性质的非商业二次创作，如涉权益问题请联系处理。
