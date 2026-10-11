# AxisMeld 修改日志

## 2026-10-11 · 热盒下方列表16像素

- 按试用反馈，将伴随列表及级联的普通行高从21.6改为16逻辑像素（100%界面缩放），分隔从5.4改为4；字号、图标、列宽与右侧Options沿同一局部比例同步。高DPI仍遵循Blender界面缩放。
- 周围方向按钮、四视图间距、主热盒栏和普通原生菜单保持；全部条目、独立齿轮、底部避让和取消规则保留，不折叠、不滚动或随窗口再次缩小。
- 6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过；候选、解压包与公开下载工厂启动通过；网页目录和状态校验通过。实际范围见[本批验收](compatibility/2026-10-11-16px-companion-acceptance.md)。
- 首轮 repost 失败源于小字号全屏模板误识别，原始失败日志保留；观察器改为限定真实子列并保持原阈值，最终结果读取本批发布配置指定的 GUI 回执。这项测试观察器修正不计为产品修复。
- 新增待人工GU-27；GU-26的旧90%尺寸方案保留为历史。目录344项（当前331、历史13），47项历史已测及既有人工结果保持，当前初始未测284。

完整 [16px companion preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-16px-companion-preview) 已发布；源码/native `89fec688b9dd2f0c95f6a814488cd70733b29893`，基于既有 Blender 5.4 Alpha。ZIP 303,157,273 字节，SHA256 `b52299370b7a1e2d41e2f528323868042ae0cea376bba01bc19851fe11120e40`；EXE SHA256 `4878173623cef3b3485e088c2b1b909a0a57107f7193ffe3fca7de3cf8573240`。6,572 个发行文件、145 项选定资源通过干净解压审计；解压包 factory 与 100%/150% 列表 GUI、匿名重下载后的校验/解压/factory 通过。[发布快照](compatibility/2026-10-11-16px-companion-preview-snapshot.json)保存精确指纹；旧预览包保留。

本批 Pages `43d73f2bff6ce309d426ea5df0010782381d1773` 的6个公开资源与已推送Git对象逐字节一致；目录和状态检查通过。GU-27仍待人工，既有结果保持。

## 2026-10-11 · 热盒下方列表缩小

- 按用户明确选择，只将热盒下方的伴随列表及其级联子菜单缩为原尺寸的 90%。文字、图标、行高、留白和右侧 Options 同步；周围方向按钮、四视图间距、主热盒栏和其他原生菜单保持原尺寸。
- 固定列表行高由 24 调为 21.6，绘制与点击使用同一矩形；保留全部菜单内容、底部避让、灰项保护和说明无空间时隐藏，不因窗口变小继续缩放、不折叠或滚动。
- 新增 3 项几何回归先 RED 后 GREEN；6 组 42 项相关 Python、2 组 114 项原生测试、5 组既有 GUI 回归及新构建工厂启动通过。新增真实截图观察器在旧版实际失败、新版 100%/150% 通过，列表宽度约 90%，周围按钮归一化像素矩形完全一致；完整预览包已发布并完成匿名下载启动核验，证据见[本批验收](compatibility/2026-10-11-compact-companion-acceptance.md)。
- 新增待人工 GU-26；目录 343 项（当前 331、历史 12），47 项历史已测记录和既有人工状态保持，当前初始未测 284。新增功能开发继续暂停。

完整 [Compact companion preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-compact-companion-preview) 已发布；源码/native `7ebc757ae0826bce1506174f14e639344553423e`，基于既有 Blender 5.4.0 Alpha。ZIP 303,157,268 字节，SHA256 `47b59ad6547b23eb045e52f1dbfed2f8b8f57069169caa98b6f4bd33e127d113`；EXE SHA256 `dff87613bb00e70594023312a0cd401ab8b8dd599fdd7fdf4a509f8cdfa34cdf`。6,572 个发行文件、145 项选定资源通过干净解压审计；解压包 factory 与 100%/150% 列表 GUI、匿名重下载后的校验/解压/factory 通过。[发布快照](compatibility/2026-10-11-compact-companion-preview-snapshot.json)保存精确指纹；旧预览包保留。

本地网站静态与状态检查通过；Pages `01fbd41b47e6` 的 6 个公开资源逐字节核验通过。本批仅更新目录和发布配置，未重记历史浏览器检查为当前结果。

## 2026-10-11 · Blender 5.4 主干同步

- 将官方 main `754ebe3c4b4e1402a159df6e1e58823cc93ef887` 合入开发分支，保留非变基合并历史；原基线 `18d84097b4f859582afdec57eece2ae880371adc`，982 个上游提交。Windows 库同步到精确 `aa0c5db72fa9488bb685bdddbede780d19f483f5`，默认分支只同步首页。
- 窗口标题冲突适配上游 `fmt::memory_buffer` 接口，同时保留 AxisMeld 产品名与版本。原生 Project 设置跟随上游；Loop Tools 的新增原生入口通过既有 Edit Mesh → Transform 分类继承，不增加 Deform/Generate 根菜单。
- 原生键位继承 497 → 499、受保护 keymap 186 → 187；两条增量来自 Grease Pencil Carver。AxisMeld 58 个默认命令、60 条含别名绑定、七根 Modeling 菜单和冻结 Maya 参考保持。顶栏测试增加真实 Project 上下文分支。
- 新增 GU-23～GU-25 主干回归，与 GU-22 一起待人工；目录 342 项、当前 330、历史 12，47 项历史已测保持，当前初始待测 283。详情见[主干验收](compatibility/2026-10-11-blender-main-acceptance.md)。

### 最终自动验证


- 42 组 415 项纯 Python、8 组 144 项原生，另有 4 组 CLI（profiles 18 项、Blender input 11 项；profiles 与纯 Python 重合，不累加），15 组 GUI 回归、5 组 bpy 功能及 factory、5 个说明矩阵组合全部通过；GUI 与说明矩阵分别计数。
- GUI suites：modeling-viewport、menu-shortcuts、menu-options-navigation、menu-options-access、menu-options-geometry、modeling-disabled-reason、hotbox-repost、context-entries、temporary-snap、history-hotbox、tools-modifiers、tools、full-menu-lifecycle、file-window、release-cross-window。
- 145 项资源、6,572 个发行文件通过静态审计；解压包 factory/说明 GUI 与匿名下载 factory 通过。
- 本地网站静态/状态检查及 12 项浏览器检查通过；Pages 实际字节核验见下方交付。
- 输入现状：58 默认命令、60 条含别名绑定、7 个操纵器辅助入口、3 个原生模态持键入口、499 条原生继承、45 条移除、187 个受保护 keymap；基准/生成 keymap 为 281/282。

### 发布与交付


完整 [Blender main preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-blender-main-preview) 已发布；源码/native `7beedde071ca5eaa8fce6090f01cf2ddd40b6804`，基于 Blender 5.4.0 Alpha。ZIP 303,157,226 字节，SHA256 `f3692f9813cb6c7d144a371e42768229591b89ca5944671a8c886e62d4ae0a52`；EXE SHA256 `0a4de344f93bafcea9414668746fe1fa0d2fec5dd1bc0b62d86ae3a9acbd56a9`。6,572 个发行文件、145 项选定资源通过干净解压审计；解压包 factory 和实际说明 GUI、匿名重下载后的校验/解压/factory 已通过。本地网站 12 项浏览器检查通过，Pages `9fc6257e35e4` 的 6 个公开资源逐字节核对通过。[发布快照](compatibility/2026-10-11-blender-main-preview-snapshot.json)保存精确指纹。旧预览包保留。

## 2026-10-11 · 极低窗口说明避让

完整 [GUI short-window preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-short-window-preview) 已发布；源码/native `665cb38b123d89d273d6f68e2c748a258abfff47`。ZIP 297,083,907 字节，SHA256 `d49d7fd4a11bb4cdb54e8931c4391deb0a7d07661d64ea22e3e6341c4645d766`。6,498 个发行文件、145 项资源通过干净解压审计；解压包工厂启动和实际说明 GUI 通过，匿名重下载后再次核验 ZIP、解压和工厂启动。本地网站 12 项浏览器检查通过；Pages `c2904572e2ad` 的 6 个公开资源逐字节核对通过。[发布快照](compatibility/2026-10-11-gui-short-window-preview-snapshot.json)保存精确指纹。旧预览包保留。

- 热盒说明保留可用的原位置；没有完整横向空带时，按实际菜单背景、方向按钮、Options 和保留父级寻找二维空白，并重新测量完整文字。菜单布局、字号、命中与释放规则保持。
- 按用户明确选择，完全没有空间时暂不显示说明；窗口恢复空间后应完整显示。禁止回落到覆盖菜单的位置，不折叠、滚动或删减菜单。
- 旧版 840×480、150% 的 Duplicate Special 实际截图复现覆盖；新版本通过完整说明与菜单零交叠检查。94 项纯 Python、4 组 133 项原生、5 组 GUI 回归及 5 个说明矩阵组合通过；含无位置抑制和实际放大后的同一说明恢复。完整证据见[本批验收](compatibility/2026-10-11-gui-short-window-acceptance.md)。
- 新增待人工 GU-22，目录 339 项、当前 327、历史 12；47 项历史已测和既有结果保持，当前初始待测 280。随后进行独立的 Blender 主干合并与新构建验证；本批说明修复不能代替主干兼容性证据。

## 2026-10-11 · 建模灰项与热盒重复唤出

- Modeling 不适用的原生菜单项保留名称和图标，增加所需视窗、模式或活动对象的说明；阻止无对象时灰 Extrude 悬停预览触发 `NoneType.data`。UV 九项、Modifier 条目和可用上下文的原生参数、poll、扩展回调保持。
- W/E/R 保持按下期间，一次 LMB 操作结束后清空旧伴随子菜单路径，下一次 LMB 从根目录重新唤出；保留灰项/原点取消、World 实际设置与 History 队列。
- 针对性验证通过 94 项纯 Python、42 项原生和 7 组实际 GUI；其中 W/E/R 重复唤出覆盖 9 组、18 次 LMB，Modeling 灰项与有效上下文恢复覆盖 4 个场景。完整结果与发布状态见[本批验收](compatibility/2026-10-11-gui-interaction-polish-acceptance.md)。
- 新增待人工 GU-20～GU-21；目录 338 项、当前 326、历史 12，47 项历史已测及其他结果保持，当前初始未测 279。完整 [GUI interaction preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-interaction-preview) 已发布；源码/native `534eec00698397cc55e27f23f3575e6d4894331a`。ZIP 297,076,617 字节，SHA256 `271fb168454b8f3413dc4f73114a1c941883823eac67d40decde1a9b2b82fa76`。6,498 个发行文件、145 项资源通过干净解压审计；解压包工厂启动和 Modeling 灰项实际 GUI 通过；匿名重新下载后再次核验 ZIP、解压和工厂启动。网站 12 项浏览器检查通过，Pages `185800d9799c` 的 6 个公开资源逐字节核对通过；[发布快照](compatibility/2026-10-11-gui-interaction-preview-snapshot.json)保存指纹。旧预览包保留。

## 2026-10-11 · 菜单快捷键、灰齿轮导航与窄窗说明

- 菜单正文按捕获来源视窗查询真实用户快捷键，支持重绑、禁用及删除；保留原执行 token，组合键文字与右侧 Options 区域独立。
- 上下方向键跳过同排灰色辅助齿轮；普通灰正文、启用 Options、纯图标组和 Blender 原生导航保持。真实 Normalize 参数仍可通过键盘打开。
- 热盒长说明按窗口像素宽度及实际字体换行，增加主题底板并优先避开菜单；不改变完整菜单、底部对齐、热盒几何或命中。极低窗口没有足够空带时仍可能覆盖菜单，作为明确边界保留。
- 已通过 81 项纯 Python、42 项原生、快捷键/导航/Options/几何实际 GUI，以及窄窗 100%/150% 和宽窗长说明检查；详情与最终发布状态见[本批验收](compatibility/2026-10-11-gui-menu-polish-acceptance.md)。
- 新增待人工 GU-17～GU-19；目录 336 项，当前 324、历史 12，47 项历史已测保持，当前初始待测 277。自动化没有改动人工结果。完整 [GUI menu preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-menu-preview) 已发布，源码/native `74dd7159d3a2481780915e065e0bd63312cbdaa0`；297,074,985 字节 ZIP 匿名下载、解压和启动一致。网站更新 336 项目录，12 项浏览器检查通过，Pages `00ca645b2bf6` 的 6 个公开资源逐字节核对通过；详见[发布快照](compatibility/2026-10-11-gui-menu-preview-snapshot.json)。


每批开发完成时更新本文件并与代码一起推送 GitHub。记录功能与修复、验证结果、待人工测试编号；历史日志保留。

## 2026-10-11 · GUI 改键与灰项提示

- 工具热盒保存实际触发修饰键，自定义 Ctrl 组合键不再在首次移动时提前关闭；保持反复 LMB、触发键/修饰键释放、失焦取消和默认 QWER/Space 行为，未改布局或算法。
- Keymap 首选项使用集中语义标签显示和搜索各功能名称；operator 标识符、原名称、按键搜索、未知命令回退及原生展开编辑保留。
- Rigging 原生灰项增加实际上下文原因 tooltip；仍是不可执行按钮，错误上下文不展开原生子菜单，不修改模式或选区。链接骨架数据的已有例外保持。
- 新候选验证通过：8 组 80 项纯 Python、2 组 42 项原生、16 项真实 RNA；6 组 GUI 和 1 组 profiles 后台回归通过，含实际快捷键展开/搜索和灰项悬停截图。旧版 Ctrl 改键失败→新版通过；两项 Python 修复也保留红→绿记录。145 项运行资源与源码一致，独立审查未发现可操作缺陷。
- 新增待人工 GU-14～GU-16；目录 333 项、当前 321、历史 12，47 项历史已测及原记录保留，当前初始待测 274。菜单快捷键提示、灰齿轮键盘导航、窄窗长原因说明和 Modeling 灰项一致性留作下一批 GUI 候选问题。
- 发布与验证边界见 [本轮验收](compatibility/2026-10-11-gui-input-polish-acceptance.md)。完整 [GUI input preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-input-preview) 已发布；源码/native `3a614cad8a1bd4df8d05049f6f051d47bfef62e3`，ZIP 297,074,164 字节，匿名重下载/解压/启动一致。公开页同步 333 项目录和新版本，12 项浏览器检查通过；[发布快照](compatibility/2026-10-11-gui-input-preview-snapshot.json)记录指纹。

## 2026-10-11 · 当前 GUI、热盒与临时输入收敛

- 补齐 Ctrl+RMB 转换、Ctrl+Shift+RMB 当前工具、Edit 空选择只读捕获与提交；转换复用已有能力，Face Path 保留两面/Face域条件和适配说明。
- 原生操作结束回调恢复 Bevel/Crease 等独立模态取消前的空选择；通过 UID、几何和当前选择重新查找 BMesh，运行期状态不保存到 DNA/Redo。菜单打开/悬停/取消不改场景。
- 增加 A+LMB History Operations 八方向；LMB 松开排队、A 松开执行，未 posted 才 Frame All；队列绑定活动对象/完整选集/数据身份，改变目标即取消，不转移旧操作。
- 原生 X/V/J 临时吸附覆盖预持键、Ctrl、重叠键、模式切换、松开/确认/取消及失焦；恢复持久设置与原生 Redo 基线，其他编辑器/键位预设保持。Grease Pencil 绘画工具免于 Modeling 键位过滤。
- 固定菜单逐级核对，9 个无内容/无提供器动态目录用原名、图标和原因灰显；非空灰目录与真实原生提供器保持。输入参考原 18+2 项闭合，生成审计更新为 58 默认命令、60 绑定、3 原生模态持键与 186 个受保护 keymap。
- Space → File 仅开放 Open Scene / Save Scene As，精确临时 token 覆盖原生脏场景/图片确认链和文件窗口释放；其余 File/Window 与独立 Options 边界保持。
- 新增完整 native 包只读审计，核对已提交源码、全文件清单、144 个资源、CRT/shared DLL、许可证、隐私文本和 ZIP 路径冲突；保留原固定 native 打包器保护。
- 当前 40 组、354 项纯测试、8 组139项原生测试、11项 Blender RNA 与7条真实 File GUI 流程通过；统一最终候选另有18组回归全部通过（17 GUI + 1 后台 profiles），每组前后 exe hash 一致。新完整 [GUI preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-preview) 已发布，功能源码/原生同为 `41d71f26ccf12be5addd5c3453106bfa66f8de5f`；完整ZIP约297MB。干净解压、portable/factory、3组关键GUI、匿名公开重下载及启动通过；网站12项浏览器验证和线上330/13目录核对通过。完整[构建/包指纹](compatibility/2026-10-11-gui-preview-snapshot.json)与最终回执见 [GUI 验收](compatibility/2026-10-11-gui-completion-acceptance.md)。代码审查发现的模态取消、Face Path、预持 Ctrl 和排队目标身份问题已修复；实际 GUI 不以纯测试代替。
- 新增待人工 GU-01～GU-13：目录330项、当前318、历史12、历史已测47、当前初始待测271；旧编号和结果保留。D/C/F12/1/2/3、Shift+J、动态提供器和新算法边界明确保留，不通过近似绑定假称完成。

## 2026-10-11 · U0 当前输入清单与模式冲突提示

- 新增可重复生成的[当前输入对照](compatibility/current-input-audit.md)与 JSON：直接运行真实 Industry Compatible / AxisMeld 生成器，记录 56 个默认命令、58 条含别名输入、7 条独立操纵器入口、489 条原生继承及 53 条移除项；检查 177 个非目标 keymap 保持。保留区域、事件值、顺序和执行属性，`--check` 检查源码漂移，不读取个人配置。
- 修复插件诊断把 Object Mode 与 Mesh 互斥模式误报为冲突的问题；共享视图与工具 keymap 的潜在冲突继续提示，不修改插件项或实际键位。默认、Move 重绑定和禁用 Redo 三组生成结果与修复前一致。同步纠正 QWER、Space 和组件指针目标的旧元数据描述。
- 验证：12 项审计、18 项输入、6 项工具热盒、4 项组件热盒、10 项建模目录测试，共 50 项 Python 测试通过；独立安装实例另有 4 项真实 Blender RNA 验证通过，包括当前源码与生成文件一致。回归包含原误报和审计遗漏的红→绿证明。
- 新增 [IN-01～IN-03](compatibility/2026-10-11-input-diagnostics-acceptance.md) 待人工；统一目录 317 项（当前 305、历史 12），保留 47 条历史已测试及原结果。公开目录同步，新增项明确要求包含本轮修复的开发构建；当前下载仍为 9 月 17 日 Skin preview，本批没有新 ZIP、原生编译或 GUI 验收。
- U0 只完成输入切片。已存参考中 38 条仅文本同名、18 条需核对正文、2 条需核对符号；菜单、持键事件及真实手感仍待 U0–U3 收敛。Alt+LMB 双击与 Measure/X 的继承差异保留调查，不据静态同键直接改行为，也不恢复 A2 功能开发。

## 2026-09-29 · 用户更正：UI、交互与快捷键优先

- 按用户最新决定暂停新增功能，取代本日早先的 A2 Influences 优先建议。已交付 A1 保持，Influences、绑定/解绑、镜像/复制、Skeleton、建模新算法与完整 UV 能力后置；灰占位继续保留。
- 更新 AGENTS、ROADMAP、CURRENT_ISSUES、HANDOFF 与跨机提示词；当前顺序为 U0 对照表 → U1 菜单/布局 → U2 热盒/鼠标交互 → U3 默认快捷键/上下文冲突。新增 [UI/输入阶段入口](development/2026-09-29-ui-interaction-shortcuts.md)，记录首批只读审计发现、来源、范围与验证边界。
- 本轮重跑输入配置 14 项、工具热盒 6 项、组件热盒 4 项，共 24 项通过；未修改产品代码、默认键位或发布包，未运行 GUI。此结果不代表完整 Maya 对齐。
- 人工验收编号和原结果保持；没有新行为，因此不新增重复测试项或改动公开 catalog/Pages。完成本阶段后先报告边界，由用户决定恢复功能开发，不自动跳回 A2。

## 2026-09-29 · 同步远端进度并明确 A2 入口

- 从本机 `96e0ce6dd08` 快进至远端 `f9d388a6bb35`，接收 A1 实现/发布、Hotbox 测试构建依赖修复及新环境原生验证等四个提交；不重复开发已经交付的 Normalize/Prune。
- 校正 ROADMAP、CURRENT_ISSUES 和跨机接续文本：独立环境原生构建已完成；尚未闭合的是新 native 的完整打包发布链和统一自动化。当前公开包继续使用 Skin weights preview，不能把本机新 native 构建记录当作已发布新版。
- 默认分支首页的旧 Rigging 下载入口同步为已经发布的 Skin weights preview，与公开测试页一致；只同步首页说明，不合并未验收功能到默认分支。
- 明确下一批 A2 建议顺序：Remove Unused Influences → Add Influence → Remove Influence，随后独立处理绑定/解绑。首项必须核查全网格权重、锁组、其他用途引用、组索引和 Undo；本轮没有实现该新功能。
- 本机同步后重新运行 36 项 Skin 计划器、5 项 Rigging 目录和 16 项菜单 UI 测试，57 项通过；菜单去向、314 项公开目录及网站静态校验通过。线上核实 Skin 发布资产与当前公开目录，GitHub 当前无开放 Issue；既有 47 条历史已测及 RG-15～RG-20 待测状态保持。
- 本轮只更新进度与交接说明，没有新建人工验收项，也没有重跑原生全量构建或 GUI；9 月 18 日的构建和运行结果仍以历史记录标注。

## 2026-09-18 · 新环境原生构建与测试前置条件

- 用 VS 2022 Community 17.14.41、MSVC 19.44.35229、CMake/CTest 3.31.6-msvc6 完成 `full developer with_tests` 的 Release 构建和独立干净安装。文档补充低并发命令、显式 `bin/Release` CTest 运行资源安装前缀，以及所选五组测试所需的既有 `tests/files` 资产。
- 修复 Hotbox 模型测试漏声明 guardedalloc 直接依赖、导致 `MEM_guardedalloc.h` 无法解析的问题；提交 `33dd3a3e591b` 只补测试目标依赖，不改变热盒交互或默认布局。
- 新 native 来源为干净源码 `33dd3a3e591b825ea983045fbb8e4f7aeb877330`，exe SHA256 为 `d4675f91773fae33b08c007d5bf050fbb0fbb4e036b8702aa7826c417dcc6cdc`。141 个 Python 资源逐字节一致；Runtime 矩阵 20 项通过、0 失败/跳过，含 19 项 Skin 数据测试和官方旧版 fixture 迁移检查。
- 原生 CTest 的 `BLI`、`guardedalloc`、`blenkernel`、`editor_hotbox`、`editor_hotbox_icons` 五组共 1,982 项通过、0 失败/跳过；这是所选核心组的结果，不是全套 Blender 测试。OptiX SDK 缺失，可选 CUDA/HIP/oneAPI 预编译 kernels 未启用。
- 新 native GUI 最终 5 项通过、0 失败/跳过（资源验证及四个 GUI 组，Skin 含 7 例）。首轮 1 通过/4 失败由桌面降为 1024 宽度、窗口标签/菜单遮挡触发，原失败记录保留；临时恢复 1920×1080 后复测通过，`finally` 已还原原 1024×768。最终未保留产品或 GUI 测试源码改动。
- 本轮是本地开发环境和构建接续，没有发布新产品版本、变更公开目录/Pages 或勾选人工验收；既有待人工测试项目保持。完整命令与验证边界见 [构建与交付](BUILD_AND_DELIVERY.md)。

## 2026-09-17 · Skin 权重整理 A1

- 在 Maya 原位置适配一次 Normalize Weights 与 Prune Small Weights，分别提供独立参数齿轮；82 条正文/33 个 Options、9 个原生入口与原层级保留，持续 Normalize 模式及其他未适配项继续灰显。
- 只处理活动网格、唯一 Armature 的变形骨组及当前模式的可见顶点范围；锁组和无关组保持。严格小于阈值修剪，支持最强正影响保留和一次归一化；全零不猜测权重，输入不可满足时整批取消。原生 Clean 的锁定/阈值/镜像/对象范围差异已明确记录，未直接重命名冒充等价。
- 修复评审发现的 F9 无变化重算恢复旧删除结果，以及 Fake User 导致单对象网格误灰显；均有红→绿证据。没有改选区/模式或 C++/默认布局资产。
- 验证：36 项计划器、19 项 Blender 数据、97 项既有菜单/输入回归通过；7 项真实 GUI 检查覆盖正文、参数、取消、F9 与一次 Undo。新机公开基线完成审计/启动/Rigify/原 Rigging GUI，仍未宣称新机全量 C++ 构建完成。
- 新增可移植的固定基线 Python 试用包组装工具，从已提交 Git blob 替换受审资源，记录 native 复用来源，保留许可与完整运行时；拒绝 native 改动和未知运行资源。去向审计采用 LF 文本指纹，避免不同换行 checkout 伪差异。
- 新增待人工 RG-15～RG-20，清单314项（当前302、历史12），保留47条历史已测试且不改人工结果。公开目录/状态与12项本地浏览器验收通过。设计见 [A1 权重整理](development/2026-09-17-skin-weight-cleanup.md)，下一批为 ROADMAP A2 Influences。

- 已发布 [Skin 权重整理 Windows x64 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-skin-weights-preview)，对应功能源码 `bf35ab393b7c`。10项打包工具故障/完整性测试通过；新ZIP的141资源、35许可及独立解压启动/19数据/7GUI复验通过，GitHub资产SHA256与本地一致；公开指纹见本批快照。

## 2026-09-17 · 整体路线与跨机器开发交接

- 新增 [整体路线图](ROADMAP.md)、[当前问题](CURRENT_ISSUES.md)、[新机接续说明](HANDOFF.md)、[可复制 Codex 提示词](CODEX_HANDOFF_PROMPT.md)及[构建交付配方](BUILD_AND_DELIVERY.md)。区分已交付、灰占位、建议开发和人工验收；建议先推进 Skin 归一化/清理，继而影响骨、绑定、镜像复制，保留建模缺口及后续 UV 主线。
- 明确开发代码在 `axismeld/phase-2a`，默认 `axismeld/integration` 尚未集成最新实现；更新根规则与两处 README，旧架构/构建文档增加历史状态提示，避免新机器从旧分支或本机固定路径开工。
- 增加公开交接快照及可移植的 `tools/utils/axismeld_release_audit.py`。它只验证已发布 Rigging ZIP、源码资源、内嵌资产来源、许可和校验值；不依赖维护者本机回执，不是未来新构建的通用发布器。
- 本次重新验证：已发布 ZIP 的 139 项脚本资源、88 个 Rigify 文件、源码布局及哈希对应通过；错误校验侧文件和缺失资源的故障注入被拒绝。菜单去向和 308 项公开目录检查、网站状态检查及 12 项本地浏览器验收通过。
- 测试网页增加路线图与接续入口，保留现有配置、下载版本、稳定测试 ID 和全部历史结果。本次没有改 Blender 功能、没有新建人工测试项、没有重打包或移动既有 release tag；仍待新机器实际构建全链验证和既有人工验收。

## 2026-09-17 · Rigging 独立工作区

- 默认启动布局新增 Rigging，采用 Modeling 的 3D View、Outliner、Properties 布局，保留原 11 个工作区和默认 Layout；旧文件与个人 startup 不自动插入页面，可用原生 `+ → General → Rigging` 添加。
- Rigging 视窗提供 Skeleton / Skin，Blender 与 Maya 键位均可使用；工作区改名、复制后通过用途标记保留菜单。原生全局栏和 Modeling 的七个根菜单保持。
- 完整保留 Maya Skeleton / Skin 的 82 条正文、33 个独立 Options、原顺序和层级；未适配算法仍为灰色占位。新增 9 个原生入口，将骨架创建、Rigify、骨骼编辑、IK、Pose、绑定、权重和顶点组收进对应章节，不把相似操作冒充 Maya 实现。
- 复用真实原生菜单宿主，保留参数、执行上下文、资产和插件回调；补齐原生普通条目的缺省 Blender 图标，保留显式图标和 RNA 枚举行。修复本地对象引用链接骨架数据时 Pose、IK 和绑定目标被错误禁用的问题。
- 默认资产通过原生工作区激活建立窗口关联，避免仅普通 blend 可打开而内嵌工厂启动崩溃；重新编译可执行文件，工厂启动已通过。57 项菜单测试通过，独立核对 115 个 Maya 条目无缺失、重复或原内容变化，原建模目录 392 条映射保持。
- 无有效对象或模式时，原生入口显示灰色标签，避免灰色子菜单被预览时错误读取空对象；删除工作区时先解除自身屏幕引用，再释放该用户，修复工作区带自定义属性时屏幕用户被二次递减的问题。
- 最终运行验证：8 个独立 Blender 进程及原始布局关系检查通过；GUI 实际创建 29 骨 Basic Human、绑定与一次 Undo、Normalize 与一次 Undo、三个原生插件菜单宿主、添加/改名/删除工作区及独立进程重开通过。139 项运行资源与源码一致。
- 默认布局文件约 128 KB，单独改为普通 Git 二进制存储，避免 GitHub 公开 fork 拒绝新 LFS 对象导致源码无法获取；仅调整这一文件的属性，资产内容不变。
- 新增待人工测试 RG-07 至 RG-14；复杂变形质量、第三方扩展和不同显示缩放仍需用户验收。设计见 [Rigging 独立工作区](development/2026-09-17-rigging-workspace.md)。
- 发布 [Rigging 工作区 Windows x64 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-rigging-preview)，对应源码 `617986ac1841`；独立解压与实际启动通过，GitHub ZIP SHA256 与本地一致。测试清单共 308 项，当前 296 项，最近新增 8 项；原 300 项和 47 条历史已测状态保留。
- 发布后匿名核验通过：六份网页资源、发布下载校验值与实际源码布局资产一致；线上浏览器六项验收通过，访客记录隔离、刷新持久化及反馈版本正确，未提交测试 Issue。

## 2026-09-15 · Rigify 默认内置

- Rigify 移入原生模块目录，由 Blender 启动脚本加载，工厂配置和普通启动均可直接使用；插件管理不再显示、启停或重复加载 Rigify。
- 设置入口位于 Edit → Preferences → Animation → Rigify；保留 metarig、生成器、骨架 RNA 和旧偏好存储，外部 Feature Sets 保持用户选择。
- 修复重载脚本时残留的版本升级回调；补齐偏好重读前后的外部扩展注销/注册，以及初始化失败后的清理和恢复。
- 验证：40 项菜单与插件隔离测试通过，6 个独立进程场景通过；Basic Human 实际生成 222 根骨骼、80 根控制骨和 209 个约束，保存重开数据一致；已启用/禁用/未记录 Feature Sets 的状态与回调次数已核对。
- 实际 GUI 验证通过：原生菜单创建 Basic Human、生成 Rig、Animation 中设置面板，以及插件列表没有 Rigify 或缺失提示；136 项运行资源与候选源码一致。
- 待人工测试：RG-01 至 RG-06，包含原生入口、生成操控、保存重开、旧设置、设置面板和脚本重载。清单共 300 项，保留原编号与历史结果；第三方骨架扩展和变形质量仍需人工验收。
- 本轮仅修改 Python 模块和界面脚本，沿用已验证的原生可执行文件；设计见 [Rigify 默认内置模块](development/2026-09-15-rigify-builtin.md)。
- 9 月 16 日发布 [Windows x64 内置 Rigify 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.15-rigify-preview)，对应源码 `3a673dcf1e078`；重新解压启动通过，GitHub 资产 SHA256 与本地 ZIP 一致。公开测试页与仓库首页下载入口同步至此版本。
- 发布后匿名资源核验与 6 项线上浏览器验收通过，下载、RG 记录持久化、独立访客和反馈版本正确；未提交测试 Issue，原人工结果保持。

## 2026-09-15 · 固定开发交付流程

- 将“开发完成后提交并推送 GitHub，同时更新修改日志”写入项目规则，作为已获用户授权的固定流程。
- 建立本日志入口；本次仅修改文档，检查了差异和链接，无新增功能测试项。

## 2026-09-15 · 紧凑建模菜单与公开测试

- Vertex、Edge、Face 收入 Edit Mesh；建模栏保留七个根菜单，原功能、参数齿轮和插件入口保留。
- 发布[公开测试页](https://angelhob.github.io/AxisMeld/)与 [Windows 便携预览版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.15-modeling-preview)，支持浏览器记录、JSON 导出及 GitHub Issue 反馈。
- 清单保留 294 个编号，12 项已替代方案归入历史；维护者的历史已测与访客自己的结果分开保存。
- 验证：105 项针对自动测试、实际 Blender GUI 操作与撤销、试用包重新解压启动、12 项本地浏览器检查和 6 项线上验收通过。
- 待人工测试：MB-40（组件子菜单和紧凑栏）、MB-41（公开下载、试用与反馈）。其余未测项沿用[测试清单](compatibility/2026-09-14-manual-test-ledger.md)，自动化结果不替代人工结果。
- 对应提交：建模与试用包 `7246459183c4`；公开门户 `b2fa955d24e7`。
