# 2026-10-11 GUI 收敛验收

## 当前状态与范围

本批从 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8` 继续现有 UI/输入阶段。当前范围实现、最终统一候选回归与公开交付已完成。源码/原生提交为 `41d71f26ccf12be5addd5c3453106bfa66f8de5f`，下载 [2026.10.11 GUI preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-preview)，完整指纹见[发布快照](2026-10-11-gui-preview-snapshot.json)。

覆盖 Modeling、通用视窗与 Rigging 已开放菜单、热盒及输入适配。保留 Blender 全局菜单和工作区栏、Modeling 七根、Edit Mesh 内 Vertex/Edge/Face、Skeleton/Skin 两根。未增加 Skin/Skeleton/UV 等算法。

## 交付变化

1. Ctrl+RMB 的 Maya 转换方向环及伴随菜单；Ctrl+Shift+RMB 读取当前工具热盒，不切换工具。转换复用已有能力，To Face Path 明确需要至少两个预选 Blender 面和单独 Face 域，不声称 Maya 连续拾取等价。
2. Edit Mesh 空选择的鼠标组件只读捕获。打开/悬停/菜单取消保持场景；确认后才选择该组件并运行原生命令。UID、原始指针和拓扑保护提交；原生模态取消后通过运行期终结回调重新查找当前 BMesh，核对几何与选择集合再恢复，拒绝回写旧指针。
3. A+LMB History Operations 的八方向、缺失图操作灰占位及独立 Options。LMB 松开只记录候选，A 松开才执行；从未打开热盒的 A 松开执行 Frame All。取消不落回 Frame All，支持持 A 重复 LMB。队列绑定活动对象、完整选集及数据 UID；身份变化永久失效旧候选，提交时重新检查真实能力。
4. 原生变换 X/V/J 临时吸附：持键先于或晚于变换均可，包含 Ctrl、重叠字母、模式切换、确认时仍持键和失焦取消。临时值属于一次 TransInfo，不写 ToolSettings；结束前恢复原生基线，避免污染 Redo。Object 类型不限于 Mesh，Mesh Edit 也支持；其他编辑器与键位预设保持原生行为。
5. 九个无内容且无提供器的动态目录保留为同名灰占位并显示原因。非空灰目录、真实原生动态提供器和插件回调仍可访问。Grease Pencil 绘画工具不再误受 Modeling 预留键过滤。
6. Space → File 的 Open Scene / Save Scene As 接入真实 Blender 文件选择器。临时 token 只匹配本次调用链，穿过原生脏场景和图片确认框；打开接收窗后共享尚未释放的触发键/鼠标状态。分窗释放、正常新输入、取消、关闭和失焦都有回归，独立 Options 保持灰显，不开放其他 File/Window 命令。

菜单完整核对见[目录矩阵](../development/2026-10-11-menu-gui-completion.md)，上下文与事务见[上下文设计](../development/2026-10-11-context-gui-completion.md)，A 的时序见[History 设计](../development/2026-10-11-history-hotbox.md)，输入证据见[参考复核](../development/2026-10-11-input-reference-review.md)，文件窗口见[释放所有权设计](../development/2026-10-11-file-window-release-design.md)。

## 首次试用

完整解压新包后运行 `blender.exe`。干净工厂配置为 Blender 键位和 Layout；在 Edit → Preferences → Keymap 选择 **AxisMeld Maya 2026**，再切 Modeling / Rigging。本包不附带个人偏好，不承诺首次自动切换；旧 MB-41 的自动启用预期已按实际工厂行为修正，编号和人工状态保留。

## 当前机器可复现检查

生成表是静态输入证据，不是手感验收。当前为 **58 个默认命令、60 条含别名绑定、7 个操纵器入口、3 个原生模态持键入口、497 条原生继承、45 条移除项、186 个受保护 keymap**。原 18 条正文与 2 条标点参考已经核对，两个新增 Ctrl 入口也有直接来源。

```powershell
python tools/utils/axismeld_input_audit.py --check
python tools/utils/axismeld_workspace_menu_routes.py --check
python tools/utils/axismeld_public_test_catalog.py --check
```

在按 [BUILD_AND_DELIVERY](../BUILD_AND_DELIVERY.md) 重新构建、安装的候选上执行下列真实 GUI suites。runner 自建隔离配置和一次性场景，不接管用户工作中的实例；测试使用事件模拟与真实原生执行，不给 GUI 用例加 `--background`。

```powershell
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite file-window --artifacts "$Audit/file-window"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite release-cross-window --artifacts "$Audit/release-cross-window"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite context-entries --artifacts "$Audit/context-entries"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite history-hotbox --artifacts "$Audit/history-hotbox"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite temporary-snap --artifacts "$Audit/temporary-snap"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite workspace-menu-layout --artifacts "$Audit/workspace-menu-layout"
python tests/python/axismeld_hotbox_ui_runner.py --blender $Blender --suite menu-options-geometry --artifacts "$Audit/menu-options-geometry"
```

`workspace-menu-layout` 以 100%/150% UI 缩放实际打开 Mesh Display/Curves/Surfaces，匹配各列第一/最后正文标签并核对窗口边界；其他原有 suites 验证 Modeling、Rigging、QWER、释放顺序和完整菜单。坐标/截图测试要求合适的真实图形桌面；窗口尺寸记录在回执，不能用纯规划器结果代替最终像素。

## 验证回执

最终候选 exe SHA256：`793731a1ee5b4d510065ab6564d06c03c07711b65a037433f75e24f49f593912`。Build07 从本批 C++ 重新链接，安装后 144 个选定 Python 资源逐字节匹配当前源码；未复用 9 月旧 native。

| 检查 | 当前证据 |
|---|---|
| 纯 Python | 40 组、354 项全部通过；[可公开逐组摘要](2026-10-11-gui-pure-tests.json) |
| 原生 CTest | 所选 8 组、139 项全部通过，包含完整生产目录解析与仅两条 File 命令准入；不是全套 Blender 测试 |
| Blender RNA | 空选事务/六方向转换 7 项、真实输入诊断 4 项通过 |
| 定向 File GUI | Build07 的 7 条实际流程通过：两热盒入口、Ctrl+O/S 零 token、脏 Open 继续/取消、图片确认后 Save As 取消 |
| 最终 GUI 批次 | 统一使用上述候选，18 组全部通过（17 组 GUI 事件与 1 组后台 profiles）；每组前后 exe hash 保持一致，[逐组回执](2026-10-11-gui-event-tests.json) |
| 便携包与公开下载 | 干净 staging、ZIP/sidecar、6498文件完整解压、144资源核验、版本/portable/factory与3个关键GUI通过；匿名公开重下载的大小/SHA、完整解压与factory启动也通过 |
| 测试门户 | 330 个唯一编号、13 个新增、12 个历史、47 个历史已测；静态/状态与12项浏览器检查通过，线上config/catalog与新buildId逐项一致，Pages提交 `476a248b506712ea416d3b4ce4a7be6a8e9cf323` |

运行副本的后续严格发行审计因517个启动生成的 `.pyc` 正确拒绝；所有6497个 manifest 文件及 manifest 本身再次核对不变。干净 staging/ZIP 保持独立，运行副本不回流打包。

最终 GUI 本地回执目录为 `gui-release-07/`，每组分别保存 runner stdout、退出码、exe SHA256、源脚本/日志 hash 与截图。`--artifacts` 自身只保存截图，不自动落 stdout；发布证据使用显式持久化日志。最终可公开构建、资源与 ZIP 指纹在发布快照中保存，不上传私人路径或用户配置。

失败与修复保留：Build01 的头文件/trivial 初始化错误；Build02 主动停止无关测试重链；旧 native 根计数断言；实际转换参数错误；新 File 原生白名单漏接；中间确认链漏交接。预选 Bevel/Crease 取消残留、Face Path 接线/门禁、预先持 Ctrl 和 History 目标身份问题均已修复。早期 `05481ec...` 候选 15/16 组通过，历史跨窗诊断失败；该旧结果不作为新候选全绿证明。

公开下载首次 urllib 读取正文在0字节超时；独立分段验证后换用 curl 新连接，完整 ZIP 297073941 字节及 sidecar 的 SHA均与GitHub资产和本地一致，公开解压与factory运行通过。此网络重试不替代或覆盖原超时记录。

焦点事件边界：`--enable-event-simulate` 会屏蔽 OS 输入队列；纯 WM 模拟又不更新 GHOST 的 active 状态。跨窗失焦测试用本进程临时 OS 窗口建立真实失焦，再注入对应 WM 事件，检查双 guard 退场和后续释放正常透传。临时吸附预持键通过新增可选 RNA `key_modifier` 明确注入，生产 GHOST 输入路径不变；实体键鼠仍待人工验收。文件取消测试不加载场景、保存目标文件或图片；Blender 测试退出时仅在隔离 TEMP 写自身恢复文件。

## 保留边界与人工清单

- D 自定义/独立枢轴、C 参数曲线吸附、F12 UV 选择域、1/2/3 可恢复平滑预览仍缺底层能力；Shift+J 相对吸附也未声称实现。保留键/灰项不映射到无关近似操作。未接管的 Blender 原生扩展键（含 F1–F5）不标为 Maya 等价。
- 面向已确认组件执行后的 Extrude 宏 Escape 遵循原生 Blender 保留拓扑语义，完整撤回用一次 Undo；不能与仅打开/取消菜单或独立 Bevel/Crease 取消混为一谈。
- 已有固定目录逐项审计；非空 Maya 动态 Isolate 书签成员来源和相应数据提供器仍属后置能力。任意极小窗口、无限插件/资产目录不能保证完整显示，不能通过缩小目标、删除条目或滚动掩盖。
- 原生菜单和自动事件通过不等于生产建模、角色变形或实体鼠标手感全部验收。

[统一清单](2026-09-14-manual-test-ledger.md)新增 **GU-01～GU-13，全为待测**。合计 330 项，当前 318、历史 12；47 项仍仅为历史已测试，当前初始未测 271。其他编号与个人浏览器记录不变。公开站点通过 GitHub Issue 接收反馈，网页勾选仍只保存在各访客本浏览器。
