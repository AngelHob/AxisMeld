# 当前阶段：UI、交互与快捷键对齐

2026-09-29 用户决定：“还是先别开发功能。先完成UI和交互层面，快捷键的对齐”。本决定覆盖同日早先的 A2 Influences 建议；当前先收敛已存在的工作流，保留已交付功能与缺失项占位。

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

首个可执行任务：从 `baseline_bindings()` / `binding_events()` 和 `modeling_registry.py` 导出当前输入项，以已存 Maya 参考逐项比对；同时列出预留键与继承键。对待修项先保留原始事件序列，再做有界修复。源码元数据中的旧描述也需对照当前实现，不能当作行为真相。

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
