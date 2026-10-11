# 当前阶段：UI、交互与快捷键对齐

当前建模灰项与热盒交互修复和发布状态见[交互修复验收](../compatibility/2026-10-11-gui-interaction-polish-acceptance.md)；本批 94 项纯 Python、42 项原生和 7 组实际 GUI 通过。当前测试目录 338 项、326 项有效、GU-20～GU-21 最新待测；47 项仅历史已测，当前初始未测 279、全表初始未测 291。下文首批数字保留为历史记录。

2026-09-29 用户决定：“还是先别开发功能。先完成UI和交互层面，快捷键的对齐”。本决定覆盖同日早先的 A2 Influences 建议；当前先收敛已存在的工作流，保留已交付功能与缺失项占位。

## 2026-10-11 当前收敛状态

**首批 GUI 历史交付状态：当前范围实现、统一候选回归与完整原生预览包发布已完成。** 已通过 40 组 354 项纯 Python、8 组 139 项原生、真实 RNA 7+4 项与 7 个实际 File 流程；统一候选的 18 组回归全部通过（17 组 GUI、1 组 profiles 后台验证，按套件计）；exe SHA256 为 `793731a1ee5b4d510065ab6564d06c03c07711b65a037433f75e24f49f593912`。完整原生 [2026.10.11 GUI preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-preview) 已发布，功能与原生源码同为 `41d71f26ccf12be5addd5c3453106bfa66f8de5f`；匿名下载、全量解压及工厂启动核验通过，见[发布快照](../compatibility/2026-10-11-gui-preview-snapshot.json)。最终结果/构建/包指纹集中于 [本批验收](../compatibility/2026-10-11-gui-completion-acceptance.md)，9 月 17 日旧 Skin 包不包含本批 GUI/原生输入改动。

当前已实现转换/当前工具热盒、Edit 空选只读预选与取消恢复、A+LMB History 队列目标保护、X/V/J 临时吸附、9 个空目录灰显和 Grease Pencil 输入隔离。Space → File 只新增 Open Scene / Save Scene As 两条正文；精确调用 token 穿过未保存场景/修改图像确认链，交给对应文件窗口排空热盒松键。原生确认、无默认快捷键、独立 Options 与其他灰项的边界不变，见 [File 设计](2026-10-11-file-window-release-design.md)。

原 18+2 参考缺口已经核实；当前为 58 默认命令、60 条绑定、7 个操纵器和 3 个原生持键入口。首批历史人工目录 330 项（当时当前 318、历史 12），47 项仅历史已测，当前初始未测 271；GU-01～GU-13 共 13 项全部待人工验收。当前范围的实现完成不等于新算法实现或人工验收完成，功能开发仍暂缓。

下方 U0 切片、U1–U3 当时的工作顺序及日期验证记录保留历史原文。不能把其中的旧参考缺口、待核实入口、计数或“下一步”再次当作当前开发队列；接续状态以本节和本批验收为准。

## 范围与边界

- **对齐对象**：Maya 2026 默认菜单/快捷键和已经确认的操作逻辑；优先现有 Modeling、通用视窗、各热盒及 Rigging 的菜单 UI。不是要求复制全部 Maya 窗口布局。
- **本阶段可改**：内容/分组/层级/图标/参数入口、布局、快捷键、鼠标事件、上下文分派、持键临时状态与取消恢复；复用已有 Blender/AxisMeld 能力。
- **暂缓**：新增 Skin/Skeleton、建模和 UV 算法或功能适配；包括 A2 Influences、绑定/解绑、镜像/复制。独立 Vertex Face 选择域等缺失能力不通过近似绑定冒充实现。
- **保留**：Blender 全局菜单与工作区栏；Modeling 七根、Edit Mesh 内的 Vertex/Edge/Face；Rigging 的 Skeleton/Skin。统一 Blender 图标，齿轮右对齐，未实现正文/Options 独立灰显。
- **输入约束**：四视图二级热盒是标杆；五行实际净间隔、外延命中、中心取消、父子返回和拥有者松键一致；QWER 不松键可多次长按 LMB。伴随菜单不折叠/滚动，下方不足时底部对齐。极小视窗的完整显示边界需实测，不能以缩小目标或丢条目宣称解决。

## U0：先形成当前对照，不重复历史开发

逐项记录：**参考来源 → Maya 输入/菜单位置 → 当前命令与生效区域/模式 → 按下/按住/松开及取消 → 差异/冲突 → 自动化证据 → 人工编号/状态**。只有公开默认键位可作为基线，个人 studio/user/session 覆盖另列。

只读审计已确认以下入口；这里的状态不是完整功能验收结果：

| 范围 | 当前证据与待核实边界 | 接续入口 |
|---|---|---|
| QWER、F8–F11、F/A、Alt 鼠标、4/5、Space | `commands.py` 已有默认声明；QWER 持键菜单已实现。早期 Phase 1 表中“按住菜单未实现”和四向 Space 描述是历史范围，不可直接用作当前完成状态。 | [早期键位表](../maya-mapping/phase-1.md)、[工具热盒参考](../maya-mapping/2026-09-11-tool-marking-menus.md)、`scripts/modules/axismeld/commands.py` |
| 建模命令与组合键 | 已有 M3 功能/默认键位身份与机器可读对照；仍要核对生成后的 keymap、上下文、别名及实际事件，不以有目录认定全部对齐。 | [M3 对照](../maya-mapping/2026-09-14-m3-modeling-coverage.md)、同名 JSON、`modeling_registry.py`、`keymap.py` |
| D/X/C/V/J/F12/1/2/3 等保留键 | `RESERVED_KEYS` 仍明确保留这些裸键；其他未接管的组合键可能继承 Industry Compatible。先逐项归类为已有能力可适配、缺功能暂缓、用户明确保留差异；不直接全部解禁。 | `commands.py`、`keymap.py`、[Phase 1 范围](../maya-mapping/phase-1.md) |
| 模式、编辑器、用户覆盖与插件 | 生成器限制在声明区域/模式；Curve/Lattice 仅获得声明的 M3 键；非建模编辑器保留；profile 的直接绑定 schema 只收 PRESS，持键释放在专用交互中处理；插件冲突只报告。以上保护不等于所有继承键已对齐。 | `keymap.py`、`profiles.py`、`tests/python/axismeld_input_test.py` |
| 热盒与组件交互 | 四视图几何契约和 G-01～G-10 已有验收步骤；Edit 空选择预选、Ctrl+RMB 转换、Ctrl+Shift+RMB 工具上下文仍有后续审计范围。区分入口/事件适配与新增选择算法。 | [标杆约束](2026-09-14-hotbox-reference-contract.md)、[问题清单](../CURRENT_ISSUES.md)、[人工总表](../compatibility/2026-09-14-manual-test-ledger.md) |

首个输入导出切片已于 2026-10-11 完成，见下节。接下来核对表中 18 条正文参考与 2 条符号差异，并补齐菜单/热盒对照；对待修项先保留原始事件序列，再做有界修复。源码元数据中的旧描述也需对照当前实现，不能当作行为真相。

### 2026-10-11 · U0 当前键位审计实施

在既有源码内新增维护工具，直接运行 Industry Compatible 与 AxisMeld 的真实键位生成函数，输出可重复生成的 Markdown/JSON 对照；`--check` 用于检测文档与源码漂移。普通 Python 下仅适配 `bpy.utils.execfile` 的文件加载，不伪造键位或操作结果；Blender 内使用真实加载器。工具不加载个人配置、不改变键位或场景。

每条默认绑定及别名记录实际目标 keymap、已存 Maya 参考身份/默认输入、事件入口、限制和人工记录入口；原生继承项与预留裸键另列。缺失/重复/落入错误 keymap 的 AxisMeld 绑定及被改动的非目标编辑器必须报错；原生 fallback、共享 Space 和条件式 Shift+RMB 并存单独标注，不按字符串相同误报为事件已冲突。此表证明静态生成配置，仍需后续真实事件与人工验收。

审计发现并在本批处理一个有界诊断错误：Object Mode 插件的 Ctrl+F9 被提示与仅在 Mesh 生效的 `selection.convert_vert` 冲突，原因是插件诊断未像生成器一样考虑模式。复用命令的目标声明，仅排除互斥模式；共享 3D View 和工具 map 仍需保守报告潜在重叠，不能直接以目标名称不同隐藏父/子 keymap 冲突。此修复只改变提示，不修改插件、用户键位、事件值匹配或命令执行。Alt+LMB 双击被导航 PRESS 所有权移除、Measure 的 X 被预留键移除，先保留证据待真实事件和范围核对，不在本批猜测性改键。

实施结果见[生成表](../compatibility/current-input-audit.md)及[完整 JSON](../compatibility/current-input-audit.json)：56 个默认命令、58 条输入（含别名），另列 7 个 AxisMeld 操纵器入口、489 条原生继承、53 条移除项；177 个受保护 map 未改变。38 条 `same_notation` 只代表已存文本相同，18 条需读正文，Grow/Shrink 的两条标点需继续核对。字段保留区域、项顺序和操作属性；原生 enum flags 集合按稳定顺序保存为 JSON 数组。

验证回执（2026-10-11）：审计 12、输入 18、工具热盒 6、组件热盒 4、建模目录 10，共 50 项纯 Python 通过；真实 Blender RNA 另 4 项通过。默认、Move 重绑 F20、禁用 Redo 三组生成配置与修改前一致。审计遗漏与模式误报均先重现失败再修复；`--check` 已通过。未改变实际默认键位或热盒事件，未运行 GUI；新增 IN-01～IN-03 的人工状态保持待测。

本机 `bin/Release/blender.exe` 启动遇到 Windows 并行配置错误，改用已有独立 `install/blender.exe` 运行隔离工厂配置测试，载入本 checkout 的隔离审计包。使用的 exe SHA256 为 `72db65ede53c3e5c724d5acf33586ff04eec9c123b5004aae9d3d365df481408`；这不是本轮重新编译或已发布新版的证据。可移植命令：`<blender> --background --factory-startup --python-exit-code 1 --python tests/python/axismeld_input_diagnostics_blender.py`，并将 `BLENDER_USER_CONFIG` / `BLENDER_USER_SCRIPTS` 指向临时隔离目录。

## U1–U3：按证据收敛

1. **U1 菜单与布局**：核对全局栏、Modeling、Rigging、Space/QWER/RMB/Shift+RMB 及子菜单的条目、顺序、分组、图标、Options 和可达性；对比单/四视图、边缘与显示缩放。实现暂缺保留完整身份和灰显。
2. **U2 热盒与鼠标**：验证有/无选择、对象/组件上下文、划出按钮仍可选择、反复唤出、父子返回、Space/鼠标释放与 Esc 取消；检查窗口边缘夹紧后的真实命中区域。不为开启菜单暗改模式/选区。
3. **U3 快捷键与冲突**：逐项验证默认键和组合键、别名、模式及区域、临时状态恢复与失败 fallback；配置重载、重启、切回 Blender/Industry Compatible 和个人覆盖不破坏原有边界。缺底层能力的键列出阻碍，留到功能阶段。

每批只处理已经查明的差异；不能把“验收未做”写成“已发现产品 bug”。用户明确暂缓的 AXM-COMPAT-001 Global 缩放差异不重新启动。

## 验证与完成定义

- 2026-09-29 本次重新运行 `axismeld_input_test.py` 14 项、`axismeld_tool_hotbox_test.py` 6 项、`axismeld_component_hotbox_test.py` 4 项，共 **24 项通过**。它们覆盖部分默认配置和目录/分派基线，不覆盖全部 Maya 键位或实体键鼠手感；本次未运行 Blender GUI。
- 后续涉及实际事件的改动按范围使用 `axismeld_input_blender.py`、`axismeld_tool_hotbox_events.py`、`axismeld_component_hotbox_events.py`、`axismeld_hotbox_release_events.py` 和 `axismeld_menu_options_geometry_events.py`；原生布局改变时加对应 C++/GUI 验证，不拿纯 Python 检查替代。
- 沿用 G/L/VR/K/FM/MT/MB/RG 等稳定人工编号与原状态。只有新行为或新测试场景才补条目、同步公开 catalog/Pages；此次优先级调整不增加重复测试项，也不替用户勾选结果。
- 完成条件：当前范围中的每项有可追溯状态；已确认 UI/输入缺陷经针对性验证；功能缺口明确保留占位；真实键鼠/显示条件验收与自动结果分别记录。人工暂缓时可继续可验证的工作，但整体状态仍是待验收。
- 阶段收敛后报告结果与边界，由用户决定何时恢复功能开发，不自动转 A2。每批照常更新 CHANGELOG、提交、推送并核验 GitHub。
