# UI_SPEC — 文字层规格书

**项目**：Mili《world.search(you);》MV — *The Museum of Approximations*
**Owner**：ui-lab（task-3）　**画布**：2560×1440 @ 60 fps，295.3467 s
**数据源**：`mv/data/timeline.json`（74 行歌词 / 9 stage / 12 section / 18 memory_events / 21 log_events）
**设计基调**：博物馆标签 + 检索终端。克制、精确、有呼吸感；常规 HUD 不透明度 ≈55%，让画面说话。
**版本**：film.ass 345 条事件（layer 0:1 / 1:10 / 2:30 / 3:304），58,075 B，时长 0:04:55.35（2026-10-19 片头小标题 4 条；同日 Lead 拍板：去掉右上 memory 百分比条与左上 12 段刻度，改「页码」+ 2 px her-blue 短横线）。**终混前补丁（同日，master QC 触发）**：歌词样式全局加对比（EN 描边 2.6 + Shadow 2，ZH 描边 2.2 + Shadow 2），仅 `id12 "I'm searching"`（s06 窗口）下移到 1240/1302——事件数/时长/字节均未变。

---

## 1. 交付物

| 文件 | 说明 |
|---|---|
| `mv/overlay/hud_timeline.py` | 唯一生成器：样式 / 时间轴 / 图层 / 校验，读 `timeline.json` 生成 `film.ass` |
| `mv/overlay/film.ass` | 烧录用字幕：74×2 行歌词、HUD、8 张章节条、3 个次级标记、片头小标题、片尾卡 |
| `mv/overlay/cards/card_title.png` | 片名字卡，2560×1440 RGBA（不透明纸纹底） |
| `mv/overlay/cards/card_chapter_01_sort.png` … `card_chapter_08_restore.png` | 8 张章卡，2560×1440 RGBA（透明底，只有纸标签） |
| `mv/overlay/cards/card_end.png` | 片尾卡（片名 + 专辑 + 角色美术署名 + 许可证） |
| `mv/overlay/make_cards.py` | 生成上述 10 张 PNG（numpy 现场生成纸纹，字体排版） |
| `mv/overlay/render_overlay.py` | 生成 ASS / 烧测试片 / 出 QC 静帧 / 烧最终成片 |
| `mv/overlay/fonts/` | 自带字体（Georgia / Consolas / 微软雅黑），供 libass `fontsdir` |
| `mv/out/tests/ui/test_overlay.mp4` | 10 s 烧录证明：片名 + 一次 stage 切换 + 一次 memory 变化 + 一行歌词 + 一行 log |
| `mv/out/tests/ui/test_frames/`、`qc_frames/`、`qc_sheet.png`、`cards_sheet.png` | 目检素材 |
| `mv/out/tests/ui/qc_hud_0096.00.png` / `qc_hud_0240.00.png` / `qc_hud_0291.50.png` | memory 三态单帧：百分比态 / merged / `?` |
| `mv/out/tests/ui/qc_opening_title.png` + `qc_opening_title_strip.png` | 片头小标题合成测试（叠在 `mv/out/lookdev/s01.png` 上；strip 为淡入/保持/淡出三连） |

---

## 2. 一键重建（在仓库根 `D:\Code\Code MV\new-word.search(you)` 下）

```bat
python mv/overlay/hud_timeline.py --check     :: → mv/overlay/film.ass + 一致性校验
python mv/overlay/make_cards.py --preview     :: → mv/overlay/cards/*.png + cards_sheet.png
python mv/overlay/render_overlay.py all       :: ass + test_overlay.mp4 + QC 静帧
```

环境：Python 3.14 + numpy / Pillow；ffmpeg 完整构建在 `C:\ffmpeg\bin`（需 `--enable-libass --enable-fontconfig --enable-libharfbuzz`）。
`film.ass` 的时间全部来自 `timeline.json`——**不要手改 ASS 时间**，改数据后重跑生成器。

---

## 3. 最终合成命令（确定版）

前提：剪辑母版 **无字幕**、2560×1440、60 fps、H.264/ProRes；音频单独 48 kHz WAV。

```bat
cd /d "D:\Code\Code MV\new-word.search(you)"

C:\ffmpeg\bin\ffmpeg.exe -y ^
  -i "mv/out/final/master_video_no_text.mp4" ^
  -i "mv/out/final/master_audio.wav" ^
  -map 0:v:0 -map 1:a:0 ^
  -vf "ass=mv/overlay/film.ass:fontsdir=mv/overlay/fonts" ^
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -profile:v high -level 5.1 ^
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 ^
  -c:a aac -b:a 320k -ar 48000 ^
  -shortest -movflags +faststart ^
  "mv/out/final/world.search(you)_final.mp4"
```

变体：

```bat
:: 母版已带音轨（只烧字，音频直接过）
C:\ffmpeg\bin\ffmpeg.exe -y -i "master.mp4" -map 0:v:0 -map 0:a:0 ^
  -vf "ass=mv/overlay/film.ass:fontsdir=mv/overlay/fonts" ^
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -c:a copy -movflags +faststart "final.mp4"

:: 只烧 5 s 抽检（不动全片）
... 同上，在 -i 后加 -t 5，输出 final_check_5s.mp4
```

要点：

* **必须给 `fontsdir`**：Windows 下 libass 若只按 family 名匹配，可能命中别的字体（尤其中文）。
* **滤镜路径用 `/`，且从仓库根用相对路径**——仓库路径含空格和括号（`Code MV`、`(you)`），绝对路径需转义成 `D\:/Code/Code MV/new-word.search\(you\)/...`，容易出错。
* 不要加 `-r`（保持 60 fps）；不要加 `-shortest` 以外的时长参数。
* 烧完用 ffprobe 复核：`-show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt`，并在 292.5 s 抽一帧确认片尾卡。

---

## 4. 字体

| 用途 | ASS fontname | 文件 | 说明 |
|---|---|---|---|
| 英文衬线（片名/歌词/章名/编号） | `Georgia`，歌词与片名 `italic=-1` | `georgiai.ttf` / `georgia.ttf` | 歌词字距 +3.2，章名 +14 |
| 中文（歌词、署名） | `Microsoft YaHei Light` | `msyhl.ttc`（index 0） | 注意 `msyh.ttc` 的 index 1 是 YaHei **UI**，不要用错 |
| 等宽（HUD/日志/微标签/数据行） | `Consolas` | `consola.ttf` | 微标签字距 +7/+8，终端感 |

所有渲染入口都带 `fontsdir=mv/overlay/fonts`。ASS 中不要写 `YaHei`、`Georgia Italic` 这类别名，用上表的精确 fontname。

---

## 5. 画布 / 安全区 / 排版锚点

`[Script Info]`：`PlayResX 2560 / PlayResY 1440`、`WrapStyle 2`、`ScaledBorderAndShadow yes`、`YCbCr Matrix TV.709`。
安全区 `SAFE = 96 px` → 文本域 x∈[96, 2464]、y∈[96, 1344]。所有文字都在安全区内，无出框。

| 元素 | 字体/字号 | 锚点（ASS） | 位置 | 透明度 |
|---|---|---|---|---|
| 歌词 EN | Georgia italic 54，字距 3.2；**描边 2.6 / 投影 2（40% 黑）** | `\an5` 居中 | (1280, **1116**)；例外 id12 → (1280, **1240**) | alpha 0x66（60%） |
| 歌词 ZH | YaHei Light 31，字距 0.8；**描边 2.2 / 投影 2（40% 黑）** | `\an5` 居中 | (1280, **1178**)；例外 id12 → (1280, **1302**) | alpha 0x80（50%） |
| STAGE 微标签 | Consolas 19，字距 7 | `\an7` | (96, 96) | 0x8C |
| stage 值 | Consolas 34，字距 3 | `\an7` | (96, 122)，切换时 2 px 上浮 240 ms | 0x73 |
| 页码 | Consolas 19，字距 4 | `\an7` | (96, 262) `NN / 08`；22×2 px 短横线 (212, 270)；段名 (252, 262) 仅在子段落补出 | 页码 0x8C；短横线 0x59；段名 0x73 |
| MEMORY 微标签 | Consolas 19，字距 7 | `\an9` 右对齐 | (2464, 96) | 0x8C |
| memory 值 | Consolas 25/32（"her"/百分比 32） | `\an9` | (2464, 122) | 0x73 / 0x4D |
| memory 来源行 | Consolas 19 | `\an9` | (2464, 162) | 0x99 |
| 日志 | Consolas 23 | `\an1` | x=96，底边 1344，行距 36，最多 3 行 | 0x66（prompt 0x73） |
| **片头小标题** | Consolas 18/17 + Georgia italic 40 | `\an7` 左对齐 | x=96；金线 y1092 / MILI y1104 / 片名 y1134 / 专辑 y1194 | 金线 0x73；MILI 0x8C；片名 0x66；专辑 0x8C |
| 章节条 | — | 纸标签 | x 280–2280，y 608–832（高 224） | 纸底 0x66 |
| 编号 | Georgia italic 150 | `\an4` | (348, 720) | ink 0x1A |
| 章名 | Georgia 76，字距 14 | `\an4` | (604, 720) | ink 0x1A |
| 章数据 | Consolas 21，字距 1.2 | `\an6` 右对齐 | (2240, 720) | ink 0x59 |
| 次级标记 | Consolas 22，字距 8 | `\an5` | (1280, 420)，两侧 160 px 细线 | 0x73 |
| 片尾卡 | 见 §8.7 | `\an5` | MILI 452 / 片名 560 / 金线 640 / 专辑 700 / CHARACTER ART 852 / 署名 898 / 许可证 952 / 片名标签 1320 | 见样式表 |

**ASS 锚点语义（易错）**：`\an7` 左上、`\an9` 右上、`\an5` 正中、`\an1` 左下、`\an4` 中左、`\an6` 中右。右上角文字必须 `\an9`，否则会从 x=2464 向右溢出画面。

---

## 6. 颜色与透明度

| 名称 | HEX | 用途 |
|---|---|---|
| INK | `#1d2029` | 纸标签上的深墨字 |
| PAPER | `#ece8de` | 字幕 / HUD / 纸 |
| HER BLUE | `#4d6bfe` | 页码短横线、百分比、日志 prompt、光标 |
| GOLD | `#ffd28a` | 片名细线、MILI 微标签、merged 状态 |
| WARM | `#ff6b4a` | 保留（本层未用于文字） |
| ABYSS | `#0a2230` | 片尾暗场 veil |

**ASS alpha 语义**：`0x00` = 完全不透明，`0xFF` = 完全透明。`0x73` = 55% 不透明度（常规 HUD），`0x66` = 60%，`0x80` = 50%，`0x8C` = 45%，`0x99` = 40%，`0x4D` = 70%，`0x1A` = 90%。
目标：常规 HUD 55%；歌词 EN 60% / ZH 50%（合唱段 179.47–233.77 提到 70% / 60%，仍克制）；日志 40%；章节纸底 60%。

---

## 7. 图层与 Event 命名

| Layer | 内容 |
|---|---|
| 0 | 全屏 veil（`END_VEIL`） |
| 1 | 绘图底（章节纸底、片头/片尾金线） |
| 2 | 细线与需压在 veil 上的文字（页码短横线、章卡内衬线、次级标记线；片尾卡部件——在 veil 上、日志下） |
| 3 | 全部正文文本 |

命名规则 `模块_序号[_槽位]`（写入 ASS 的 `Name` 字段，便于定位/QA）：

| 前缀 | 含义 |
|---|---|
| `LYR_EN_nn` / `LYR_ZH_nn` | 第 nn 行歌词英文/中文 |
| `HUD_STAGE_MICRO` / `HUD_STAGE_nn` | 左上微标签 / 第 nn 个 stage |
| `HUD_PAGE_nn` / `HUD_PAGE_DASH_nn` / `HUD_PAGE_NAME_nn` | 页码文本 / 当前段短横线 / 子段落名（仅 PROLOGUE、SEARCH-A、SEARCH-B、ASCENT） |
| `HUD_MEM_MICRO` / `HUD_MEM_nn` / `HUD_MEM_SRC_nn` | 右上 memory 各部件（纯文字，无条形） |
| `HUD_LOG_nn_sk` | 第 nn 条日志在第 k 个滚动槽位 |
| `OPEN_RULE / OPEN_MILI / OPEN_TITLE / OPEN_ALBUM` | 片头小标题 4 个部件 |
| `CARD_nn_<NAME>_FILL/_RULE/_NUM/_NAME/_DATA` | 章节条 5 个部件 |
| `SUBCARD_Snn` / `SUBCARD_Snn_RULE` | 次级段落标记（S03 / S05 / S10） |
| `END_VEIL / END_MICRO_ARTIST / END_TITLE / END_RULE / END_ALBUM / END_MICRO_CREDIT / END_CREDIT_ART / END_LICENSE / END_MICRO_FILM` | 片尾卡各部件 |

---

## 8. 时间轴规则

### 8.1 Stage（9 段，左上）

| t | label |
|---|---|
| 0.00 | 00 OFFLINE |
| 14.36 | 01 SORT |
| 40.86 | 02 RECALL |
| 82.89 | 03 ROUTE |
| 151.84 | 04 FORGET |
| 179.47 | 05 EVERYWHERE |
| 207.14 | 06 MERGE |
| 233.77 | 07 RESURFACE |
| 275.75 | 08 RESTORE |

HUD 于 0.45 s 从黑场浮出（`T_STAGE_FADE_IN`）；290.9 s（`T_HUD_OUT`）stage / 页码收束（`memory: ?` 到 292.0 s 单独收）。

### 8.2 Section（12 段，页码）

`S00 PROLOGUE 0.00`、`S01 SORT 14.36`、`S02 RECALL 40.86`、`S03 SEARCH-A 68.17`、`S04 ROUTE 82.89`、`S05 SEARCH-B 137.09`、`S06 FORGET 151.84`、`S07 EVERYWHERE 179.47`、`S08 MERGE 207.14`、`S09 RESURFACE 233.77`、`S10 ASCENT 261.06`、`S11 RESTORE 275.75`。
页码规则：左上显示 `NN / 08`（NN = 当前 stage 编号 00–08，与 stage 值同轴，不另起 12 段编号，避免与 stage 读数错位）；当前段用一条 22×2 px her-blue 短横线标记（不用连续刻度条、不做填充，避免读成进度条）。section 名与 stage 名相同的 8 段不重复显示（stage 值已给出），仅在 4 个 stage 内子段落补出段名：`PROLOGUE`（S00）、`SEARCH-A`（S03）、`SEARCH-B`（S05）、`ASCENT`（S10）。
若确要 12 段页码，把 `build_stage` 的 `last = sections[-1]["index"]` 改为 `len(sections) - 1` 并把页码改从 section index 取。

### 8.3 章节卡（8 张，1.2 s）与次级标记（3 个）

* 章节卡 = stage 变化（01–08），**start+0.10 → +1.30**，纸标签淡入 240 ms / 淡出 340 ms；`00 OFFLINE` 无卡（开场让位给画面与 HUD 浮出）。
* 卡片数据（右侧小字）：01 `8 files · her 100%`｜02 `candidate #1 · table · sim 0.31`｜03 `candidate #3 · cat · sim 0.22`｜04 `word "love" → low confidence`｜05 `recall rate 1.00 · precision 0.00`｜06 `72 files · 14 peers · 1 bucket`｜07 `depth 0 m`｜08 `result: you`。
* 次级标记（同 stage 内的段落，居中 y=420，1.6 s）：`S03 SEARCH-A 68.17`、`S05 SEARCH-B 137.09`、`S10 ASCENT 261.06`。

### 8.4 Memory 状态机（右上）

| t (s) | label | 来源行 |
|---|---|---|
| 14.36 | memory: her 100% (8/8) | writer · file（合成初值） |
| 40.86 | memory: her 89% (8/9) | kimi · table_2 |
| 54.46 | memory: her 80% (8/10) | qwen · eggplant_3 |
| 68.17 | memory: her 73% (8/11) | mimo · cat_2 |
| 76.40 | memory: her 67% (8/12) | glm · steak_2 |
| 82.89 | memory: her 57% (8/14) | kimi · flower_2 |
| 96.64 | memory: her 50% (8/16) | doubao · human_9 |
| 109.72 | memory: her 44% (8/18) | minimax · piece |
| 123.44 | memory: her 38% (8/21) | hy4 · dope |
| 137.09 | memory: her 33% (8/24) | ernie · love |
| 151.84 | memory: her 29% (8/28) | step · asked_again |
| 165.73 | memory: her 25% (8/32) | longcat · her_again |
| 179.47 | memory: her 22% (8/37) | qwen · flower_3 |
| 193.28 | memory: her 19% (8/42) | kimi · human_10 |
| 200.25 | memory: her 17% (8/48) | glm · table_3 |
| 207.14 | memory: her 15% (8/54) | mimo · eggplant_4 |
| 214.35 | memory: her 13% (8/60) | doubao · cat_3 |
| 221.18 | memory: her 12% (8/66) | minimax · steak_3 |
| 228.16 | memory: merged | 72 files · 14 peers · 1 bucket（金色） |
| 290.80 | memory: ? | 无来源行、无条形，问号闪烁（0x33↔0xAA，650 ms） |

`memory: ?` 到 **292.0 s** 才收（比 HUD 多活 1.1 s，在片尾卡淡入时消失）。

### 8.5 日志（左下，21 条 → 3 行滚动）

* 每条新日志从底部 +10 px 滑入 220 ms；旧行同时上移一格（36 px）；最多 3 行。
* prompt `> ` 用 her blue 0x73，正文 PAPER 0x66。
* 最后一条 `memory: ?`（290.8）**留到 294.9 s**，作为全片最后的终端陈述，陪片尾卡。

### 8.6 歌词（74 行，EN + ZH）

* 时间严格取 `timeline.json` 的 `start/end`，EN/ZH 同进同出；淡入 250 ms / 淡出 300 ms；相邻行不重叠（数据本身首尾相接）。
* 长句（>8 s 的 3 条 `I'm searching`：68.17 / 137.09 / 261.06）尾部加闪烁终端光标（`|`，alpha 0x66↔0xFF，700 ms 交替）。
* **例外**：末行 `id73 "Full of juice"` 原始 287.35–294.447 会压到片尾卡上，生成时在 **291.0 s** 截断（fade out 320 ms）让位片名；校验器对此行按 `min(end, 291.0)` 比对。若剪辑想保留完整歌词，把片尾卡后移到 294.4 之后即可（改 `T_END`）。
* **全局可读性（2026-10-19 修订，master QC 触发）**：`LyricEN` 描边 1.8 → **2.6**、`Shadow` 0 → **2**（BackColour `&H99000000`，40% 黑投影）；`LyricZH` 描边 1.4 → **2.2**、同样 `Shadow 2`。解决纸白字落在白围裙（s04 38.30 s）、白光辉（s14 261.5–266 s）、白围裙（s11 201.1 s）上只剩细描边可读的问题。只改样式表，未改动任何事件时间/透明度，也未加底板（避免横向暗带破坏画面）。
* **逐窗位置例外**：仅 `id12 "I'm searching"`（s06 68.17–82.89 s 窗口）在 `LYRIC_Y_OVERRIDE` 里把 EN/ZH 从 1116/1178 下移到 **1240/1302**——s06 推镜时原位置正落在她的眼睛/鼻梁上；下移后落在下巴以下（胸衣/围裙区），不再压脸，且不碰左下 log 块。其余 73 行窗口位置不动。

### 8.7 片尾（291.2–295.35）

`END_VEIL` 全屏 abyss（60% 不透明，淡入 800 ms）→ MILI（金微标签 y452）→ `world.search(you);`（Georgia italic 112，y560，上浮 12 px / 700 ms）→ 金线（760×2，y640）→ `from the album Hue`（38，y700）→ `CHARACTER ART`（微标签 y852）→ 角色美术署名（y898，混合字体：`角色美术：溟月 © 上善无形 · 女仆版 ZipZipPipe · 立绘 Small-tailqwq · 表情 JAdpp`，中文 YaHei 25 / 拉丁 Georgia italic 26 / 金色 ·）→ `licensed under CC BY-NC-SA 4.0`（y952）→ `THE MUSEUM OF APPROXIMATIONS`（y1320）。

### 8.8 片头小标题（1.0–4.4 s，左下角）

* 位置：s01 `void_page` 之上、画面**左下角**（x=96，y 1092–1214）；避开画面中央的页面主体、右下的场景终端文本（`> search(you);`）、顶部 STAGE（y96–190）与底部终端日志（y1272–1360）。
* 内容（博物馆登录卡式）：金色钉线（64×2）→ `MILI`（Consolas 18，字距 8，金）→ `world.search(you);`（Georgia italic 40，字距 1.4，纸）→ `from the album Hue`（Consolas 17，字距 2.4）。
* 节奏：四层错开淡入 +0.00 / +0.05 / +0.14 / +0.30 s（淡入 550–700 ms），片名上浮 6 px / 700 ms；4.40 s 前全部收掉（淡出 450 ms）。不压任何歌词（首行 14.36 起）。
* 事件：`OPEN_RULE`（layer 1 绘图）、`OPEN_MILI` / `OPEN_TITLE` / `OPEN_ALBUM`（layer 3）。
* 校验：4 条事件、时间在 [1.00, 4.40]、与首行歌词拉开 ≥0.2 s、字宽不出安全区。

### 8.9 与 15 镜 shot_plan 对齐（`mv/data/shot_plan.json`）

生成器 `--check` 会读 `shot_plan.json` 做交叉校验：15 镜连续、首镜 0、末镜 295.35、每个「窗口」完整落在单镜内（不跨镜）。窗口 = 8 张章节条（start+0.10 → +1.30）、3 个次级标记（+0.08 → +1.08）、片头小标题（1.00–4.40）、片尾卡（291.20–295.35）。

| 窗口 | 入点 | 所在镜 | 结论 |
|---|---|---|---|
| 章节条 01 SORT | 14.46 | s03 14.36–28.32 | 完整 |
| 章节条 02 RECALL | 40.96 | s05 40.86–68.17 | 完整 |
| 章节条 03 ROUTE | 82.99 | s07 82.89–109.72 | 完整 |
| 章节条 04 FORGET | 151.94 | s10 151.84–179.47 | 完整 |
| 章节条 05 EVERYWHERE | 179.57 | s11 179.47–207.14 | 完整 |
| 章节条 06 MERGE | 207.24 | s12 207.14–233.77 | 完整 |
| 章节条 07 RESURFACE | 233.87 | s13 233.77–261.06 | 完整 |
| 章节条 08 RESTORE | 275.85 | s15 275.75–295.35 | 完整 |
| 次级 SEARCH-A | 68.25 | s06 68.17–82.89 | 完整 |
| 次级 SEARCH-B | 137.17 | s09 137.09–151.84 | 完整 |
| 次级 ASCENT | 261.14 | s14 261.06–275.75 | 完整 |
| 片头小标题 | 1.00–4.40 | s01 0.00–6.00 | 完整 |
| 片尾卡 | 291.20–295.35 | s15 275.75–295.35 | 完整 |

结论：**无跨镜冲突**。8 张章节条与 3 个次级标记的入点都恰好落在镜切点后 0.08–0.10 s（stage/section 边界与 shot_plan 切点重合），1.2 s 卡片完整留在新镜内；歌词时间未受分镜合并影响。

---

## 9. PNG 卡（`mv/overlay/cards/`）

全部 2560×1440 RGBA，与 film.ass 同一套几何/字号/颜色：

| 文件 | 底 | 用途 |
|---|---|---|
| `card_title.png` | 不透明：深水渐变 + 冷/暖微光 + 纸纤维噪声 + 暗角 | 片名字卡（光心居中，可作开场/封面/缩略图） |
| `card_chapter_01_sort.png` … `card_chapter_08_restore.png` | 透明：只有带纤维的纸标签 + 轻投影 + ink 内衬线 | 章卡，可与 ASS 章节条二选一 |
| `card_end.png` | 不透明：同片名底（更暗 0.82） | 片尾卡 |

章卡时间码（若用 PNG 替代 ASS 章节条，剪辑里按此入点）：01 14.36 / 02 40.86 / 03 82.89 / 04 151.84 / 05 179.47 / 06 207.14 / 07 233.77 / 08 275.75，各 1.2 s。
**材质差异**：ASS 章节条是平涂纸（libass 无法贴纸纹），PNG 卡是精修纸纹版——两者同源，风格一致但质感不同；正式烧录用 ASS 条，PNG 卡留给剪辑/平面使用。

---

## 10. QC 流程

```bat
python mv/overlay/render_overlay.py qc        :: 16 个时间点静帧 + contact sheet + memory 三态单帧
python mv/overlay/render_overlay.py opening   :: 片头小标题叠在 s01 lookdev 上出 QC 帧
```

* 抽帧法：`-loop 1 -framerate 60 -i 测试底 -frames:v 1 -vf "setpts=PTS+t/TB,ass=film.ass:fontsdir=..."`，可在任意时刻取 film.ass 的一帧。
* 覆盖点：3.2（boot）/ 15.0（章节卡 01）/ 22.0 / 40.9（memory 首次 89%）/ 45.0 / 68.6（SEARCH-A + "I'm searching"）/ 96.0（memory 百分比态 57%）/ 155.0 / 180.0（合唱 + 章节卡 05）/ 210.0 / 240.0（merged）/ 245.0 / 280.0（stage 08 + 页码 08）/ 291.5（`memory: ?` 叠片尾淡入）/ 292.5（片尾）/ 294.6（片尾 + 末条日志）。
* 目检 checklist：Georgia italic 是否生效 / 中文是否 YaHei Light / 右上是否右对齐且不出框、**无条形** / 左上页码 `NN / 08` 是否与 stage 编号一致、**无连续刻度条** / 歌词是否在底部 78% 且不挡主体 / 章节条是否 1.2 s / 片尾卡是否无歌词残留 / 片头小标题是否在左下且不压页面与场景文本 / 96 px 安全区。
* 产物：`mv/out/tests/ui/qc_frames/qc_<t>.png`、`qc_sheet.png`（3 列缩略）、`cards_sheet.png`（卡合成在测试底上）；memory 三态另拷 `qc_hud_0096.00.png` / `qc_hud_0240.00.png` / `qc_hud_0291.50.png` 到 `mv/out/tests/ui/` 根下。
* 片头 QC：`opening` 子命令把 `film.ass` 叠到 `mv/out/lookdev/s01.png`（960×540，先 lanczos 放大到 2560×1440），出 1.20 / 2.60 / 4.20 s 三帧 → `qc_opening_title.png`（保持段）+ `qc_opening_title_strip.png`（淡入/保持/淡出三连）。
* **终混前可读性 QC（2026-10-19 补丁）**：直接用 specimen-lab 的 `mv/out/qc/master_qc/frames/` master 原图，按同一 `setpts` 法烧新 `film.ass` → `qc_fix_0038.30.png`（s04_f0600，白围裙）/ `qc_fix_0073.15.png`（s06_f0300，推镜面部）/ `qc_fix_0201.10.png`（s11_f1300，白围裙）；另出 `_crop.png`（歌词带 1:1 裁切）与 `_ab.png`（master / 旧样式 / 新样式 三行对照）。逐张目检：描边与投影在亮背景上给出清晰字缘；s06 歌词已完全离开面部。

---

## 11. 已知问题 / 注意事项

1. **末行歌词截断**：id73 在 291.0 截断（见 §8.6）；如需完整保留，后移片尾卡。
2. **libass 字体匹配**：Windows 下必须带 `fontsdir`；中文用 `Microsoft YaHei Light`（对应 `msyhl.ttc` index 0），不要写 `YaHei`；`msyh.ttc` 的 index 1 是 YaHei UI。
3. **ASS 锚点**：右上 `\an9`、居中 `\an5`、左下 `\an1`；写错会导致文字出框/偏移（本项目已踩过）。
4. **ASS 路径**：`ass=` / `fontsdir=` 里用 `/`；从仓库根用相对路径，避免空格与括号。
5. **母版规格**：先确保 2560×1440 / 60 fps 再烧字；若母版是 1080p 或 24/30 fps，先转码，否则按 PlayRes 缩放会亚像素抖动。
6. **合唱段**歌词仅提透明度，不做字号/颜色突变；不做卡拉 OK（`timeline.json` 无逐字时间，TREATMENT §3 也要求整行淡入）。
7. **测试片**用暗青渐变测试底，不是最终画面；`test_overlay.mp4` 只证明"能烧对"，不代表成片观感。
8. `memory: ?` 与最后一条日志在 291.2–292.0 会短暂叠在片尾卡上方（有意：终端还在说话，随后收掉）。
9. **片头小标题依赖 s01 构图**：位置按 `mv/out/lookdev/s01.png` 定（页面在中央、场景终端文本在右下）；若成片 s01 构图变化（页面移向左侧等），改 `hud_timeline.py` 的 `OPEN_X / OPEN_*_Y` 常量后重跑。`--check` 现已同时校验与 15 镜 `shot_plan.json` 无跨镜冲突（见 §8.9）。
10. **不做进度条**（2026-10-19 Lead 拍板）：HUD 里任何条状元素都不表示播放进度或记忆进度——右上 memory 只有百分比 / `merged` / `?` 文本，无条形；左上页码是离散读数 `NN / 08` + 一条 22×2 px 当前段短横线，不做连续刻度、不做填充。页码与 stage 编号同轴（stage 内子段落不另起编号）；section 名只在 PROLOGUE / SEARCH-A / SEARCH-B / ASCENT 补出，其余与 stage 值重复故省略。若后续有人想「加进度条」，先回看此条。
