# AxisMeld 整体规划与路线图

状态核对日期：2026-10-11，本批 GUI 收敛开始时已拉取并核对远端基线 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8`；本批结果见[GUI 验收](compatibility/2026-10-11-gui-completion-acceptance.md)，后续提交以远端为准。本文件是当前路线入口；旧日期的规格保留设计与证据，不代表当前完成度。

**最新交付（2026-10-11 GUI input polish）：三项 GUI 修复及完整原生预览包已发布。** 修复 Ctrl 组合键工具热盒提前取消、Keymap 功能名称/搜索，以及 Rigging 灰项原因提示。本轮通过 80 项纯 Python、42 项原生、16 项 RNA、6 组 GUI 和 1 组 profiles 后台回归；[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-input-preview)，源码/native 均为 `3a614cad8a1bd4df8d05049f6f051d47bfef62e3`。匿名下载、完整解压及启动已核验；旧 GUI preview 不含本轮三项修复。详见[本轮验收](compatibility/2026-10-11-gui-input-polish-acceptance.md)与[发布快照](compatibility/2026-10-11-gui-input-preview-snapshot.json)。人工新增 GU-14～GU-16，原结果保持；下一批继续处理已记录的具体 GUI 问题，新算法仍暂停。

## 1. 目标与当前基线

AxisMeld 是可独立拉取、构建、运行的 Blender 衍生版本，以 Maya 2026 默认工作流为参照，优先改进建模、选择、导航、热盒与后续 UV；Rigify 和 Rigging 已纳入原生模块。继续使用 Blender 的数据、依赖图、渲染、文件格式及扩展生态。

| 入口 | 当前内容 |
|---|---|
| 开发源码 | [AngelHob/AxisMeld 的 axismeld/phase-2a](https://github.com/AngelHob/AxisMeld/tree/axismeld/phase-2a)；本批开始时的远端基线为 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8`；后续以远端为准 |
| 默认分支 | `axismeld/integration`；目前承担仓库首页入口，**未包含最新开发实现**，不能直接用它继续功能开发 |
| 当前公开试用包 | [2026.10.11 GUI input preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-input-preview)，完整原生包；功能/native 源码均为 `3a614cad8a1bd4df8d05049f6f051d47bfef62e3`，见[发布快照](compatibility/2026-10-11-gui-input-preview-snapshot.json) |
| Blender 基线 | `18d84097b4f859582afdec57eece2ae880371adc`，版本宏为 5.3.0 alpha；不等于后续上游最新版本 |
| 测试门户 | [GitHub Pages](https://angelhob.github.io/AxisMeld/)，源码 `tools/testing_site/`，部署分支 `gh-pages` |
| 交接与问题 | [新机器接续](HANDOFF.md) · [可复制提示词](CODEX_HANDOFF_PROMPT.md) · [当前问题](CURRENT_ISSUES.md) · [构建与交付](BUILD_AND_DELIVERY.md) |

当前是开发预览版。自动化通过、菜单可见、历史“已测试”和生产可用性是四个不同状态；不给出混合这些口径的完成百分比。

## 2. 已交付到哪里

| 模块 | 当前已交付 | 仍需区分的边界 |
|---|---|---|
| 基础发行与输入 | Windows x64 原生构建、AxisMeld 标识、Maya 键位预设、语义命令与分层配置 | 不是全平台稳定版；个人配置不得进入公开默认值 |
| 导航、操纵器与热盒 | Alt 导航、轴选择后中键拖动、单/四视图、Space/QWER/组件/上下文建模与创建热盒；转换/当前工具/History、只读预选、临时吸附和 File 跨窗释放；图标、单选组、外延划选及伴随菜单整理 | 真实手感、高 DPI、窄视窗与第三方冲突仍按清单验收；不重新推翻四视图热盒基准 |
| 建模菜单与 M3 覆盖 | 全局 Blender 栏保留；Modeling 视窗七根菜单；原生功能分类接入、Maya 正文/Options 保留、缺失项灰显 | M3 是映射、可用原生能力和缺口计划的交付，**不是 Maya 所有建模算法完成** |
| Rigify 原生化 | 内置模块自动加载；创建、生成、偏好、Feature Sets 与重载生命周期已有验证 | 不再按可启停插件开发；复杂生成器及真实变形仍需人工验收 |
| Rigging 工作区 | 默认资产新增 Rigging；Skeleton/Skin 两根；9 个真实 Blender 入口；保留 Maya 82 条正文和 33 个 Options | A1 已适配一次 Normalize Weights / Prune Small Weights（含独立 Options），余下 80 正文/31 Options 仍灰显；原生 Weights 与新适配分开记账 |
| 公开测试与反馈 | 可下载预览包，稳定测试编号，本浏览器记录与 JSON 导出，GitHub Issue 反馈 | 网页勾选不会自动上传或跨设备同步；不是共用云数据库 |

建模菜单映射当前保留 **392 条 Maya 项（231 正文、161 Options）**，其中 85 条有执行绑定、307 条灰显。这是七根建模菜单的目录统计，不能与 M3 语义命令数或整套 Maya 功能数相加。详见[去向清单](compatibility/maya2026-workspace-menu-routes.json)。

Rigging 已发布验证包括 57 项针对菜单测试、8 个独立 Blender 进程及布局关系检查、实际 GUI 操作/撤销和发布包独立启动。这里只引用已发布证据，**本次文档整理没有重新宣称全量功能回归通过**。公开摘要见[交接快照](compatibility/2026-09-17-handoff-snapshot.json)。

9 月 17–18 日的历史进度：A1 已发布一次 Normalize/Prune 及独立 Options；9 月 18 日独立 Windows 环境完成源 `33dd3a3e591b` 的原生构建、干净安装、所选五组 1,982 项 CTest、20 项 Runtime 及指定显示条件下的 GUI 验证，详见 [CHANGELOG](CHANGELOG.md) 和 [构建记录](BUILD_AND_DELIVERY.md)。当时没有另发该 native 的试用包，Skin 包复用 `617986ac1841`。本批已另发完整新 native GUI preview，当前发布以本页开头为准；跨机全链自动化仍是独立工程边界。

## 3. 开发顺序

**2026-09-29 用户更正：先完成 UI、交互和快捷键对齐，暂停新增功能。** 这取代同日较早的“A2 Influences 下一批”建议。已实现的 A1 和其他原生能力继续保留；灰项不删除、不错误绑定，也不为了让快捷键可用而新增算法。当前范围是已有工作区、菜单、热盒及输入层，不扩展到全套 Maya 动画、FX、渲染功能。

当前阶段见 [UI、交互与快捷键收敛](development/2026-09-29-ui-interaction-shortcuts.md)。以 Maya 2026 默认配置和仓库已核实参考为基线，保留用户明确选择的 Blender 工作区/全局栏与菜单归纳。每批检查当前实现，先修有证据的差异；个人键位覆盖和其他 Blender 预设保持独立。

| 顺序 | 当前交付批次 | 工作内容 | 完成标准 |
|---|---|---|---|
| U0 当前范围实现完成 | 当前菜单、输入及参考证据 | 当前生成键位已有可复现审计；固定菜单/参考逐项核对，记录上下文、按下/按住/松开、冲突与测试编号 | 每项可追到当前源码及依据；明确已适配、保留差异、灰占位与待人工验收；最终验证状态见本页开头 |
| U1 当前范围实现完成 | 菜单与布局 | 正文、分组、层级、图标、右侧齿轮和工作区归属已整理；热盒伴随菜单完整显示，下方空间不足时底部对齐 | 保留七根 Modeling 及 Edit Mesh 内的 Vertex/Edge/Face；Rigging 菜单结构齐全；缺失功能灰占位；不靠折叠、滚动或删项掩盖问题 |
| U2 当前范围实现完成 | 热盒与鼠标交互 | 四视图二级热盒作标杆；外延划选、父子返回、取消/释放、边缘避让、QWER 持键反复唤出与 File 精确跨窗释放已实现 | 实际间距与事件序列有回归；实体鼠标、显示缩放和复杂生产场景仍待人工验收，不误改对象或选区 |
| U3 当前范围实现完成 | 快捷键与上下文冲突 | 已有命令默认键、组合键、别名、临时状态恢复、原生 fallback 和用户覆盖已核对；需要新算法的键后置 | 默认与有效生成键位一致；冲突可解释，失败/取消不残留状态，不抢其他编辑器或插件键；人工和自动结果分别记录 |

实现完成、自动回归、人工手感验收和包发布分别记录；当前范围的实现完成不等于人工验收完成或所有 Maya 算法已实现。完成本批交付后先报告边界，由用户决定恢复哪批功能，不自动跳回 A2。

2026-10-11 本批补齐 Ctrl+RMB 转换、Ctrl+Shift+RMB 当前工具、Edit 空选择只读预选与原生取消恢复、A+LMB History 操作及 X/V/J 临时吸附；修复九个空动态目录与 Grease Pencil 误过滤。Space → File 的 Open Scene / Save Scene As 复用原生确认链，用精确调用 token 将仍归热盒所有的松键交给对应文件窗口，不扩大到其他 File/Window 入口或继承快捷键。所有当前固定目录逐级核对，原 18+2 条输入参考已闭合。见 [File 设计](development/2026-10-11-file-window-release-design.md)及 [GUI 验收](compatibility/2026-10-11-gui-completion-acceptance.md)。

当前生成输入表为 58 个默认命令、60 条含别名绑定、7 个操纵器入口、3 个原生模态持键入口、497 条原生继承、45 条移除项、186 个受保护 keymap。原生继承不是 Maya 等价声明；D/C/F12/1/2/3 及 Shift+J 的后置能力明确保留，不能用近似功能消灭灰项。

之前完成的 Object Mode/Mesh 插件冲突提示修复保持；IN-01～IN-03 与 GU-01～GU-13 全部待人工验收。新原生代码必须使用对应新构建；旧 Skin 包不适用。最终自动回归和包发布状态统一见本页开头。

以下保留已交付历史和功能积压，**不是当前实施队列**；后置项的具体语义与算法仍需独立核实：

| 顺序 | 交付批次 | 工作内容 | 完成标准 |
|---|---|---|---|
| A0 已整理 | 可从 GitHub 恢复工作 | 统一路线、问题、分支、构建和提示词，公开经过筛选的发布指纹；清除陈旧首页状态 | 新代理无需聊天记录即可找到正确源码、资产、测试和下一任务；新机器实测仍单独记录 |
| A1 已实施 | Skin：归一化与小权重清理 | 审计 Normalize Weights / Prune Small Weights；明确骨架、顶点范围、锁定、零权重与阈值；接入可证明的原生适配和独立 Options | 实际权重结果、无关顶点组保持、失败无修改、一次 Undo、参数入口和真实菜单路由有测试；差异明确可见 |
| A2 暂缓 | Skin：影响骨与绑定管理 | 恢复后建议先 Remove Unused Influences，再 Add Influence、Remove Influence；Bind/Unbind 独立后续处理 | 扫描全网格而非当前选区；不误删锁组、非变形组或其他用途引用；组索引变化、无效上下文及一次 Undo 有验证 |
| A3 暂缓 | Skin：镜像与复制 | 明确源目标、方向、骨名匹配、拓扑/空间映射及锁定处理，适配 Mirror/Transfer | 对称/非对称、同/异拓扑、不同变换及一次 Undo 可验证；保留 native Blender 参数差异 |
| A4 暂缓 | Skeleton 常用操作 | 在现有 Edit Bones/Pose/IK/Rigify 上按使用频率补 Joint 创建/插入/镜像/定向等语义映射 | 区分 rest/pose、bone roll/关节定向、连接/父子关系；不能仅改标签认定算法相同 |
| B1 暂缓 | 建模剩余功能缺口 | 按 M3 现有计划 ID 保留高频灰项、Options 和严格上下文限制，待恢复后再适配 | 逐项记录 exact/adapted/unsupported、结果/撤销/参数与可达性；不删除未实现占位来减少问题数 |
| B2 分流 | 动态目录 | 现有菜单显示、层级及输入缺陷归 U1/U2；新增材质、集合、历史/输入输出数据提供器暂缓 | 空/非空/失效对象有证据；动态内容不能冻结为某次 Maya 场景实例；无实现时保留明确灰占位 |
| C1 后续独立阶段 | UV 基础 | UV 工作区与输入、组件/shell 选择、Cut/Sew/Move and Sew、分裂/缝合 | 使用原生 Mesh/BMesh/UV 数据；快捷键范围、Undo、保存重开和热盒回归通过 |
| C2 | UV 生产能力 | Align/Straighten/Orient/Stack → Unfold/Relax/Pins → Layout/密度/间距/UDIM → 检查诊断与预设 | 分阶段性能与结果测试，避免 UI 和算法耦合；每段都可独立使用和回退 |
| D 持续工程 | 构建、回归与上游维护 | 新机器全链验证、统一打包、针对性测试入口、依赖固定、上游接缝审计；以后再扩展其他平台 | 干净安装、源码/二进制/资源对应、许可证、公开下载与测试版本一致；不以一次本机成功声称可复现构建 |

A1 的语义审计、实现及验证见[Skin 权重整理](development/2026-09-17-skin-weight-cleanup.md)。已开放两项一次操作，当前不继续扩展 A2。Native `Normalize` 只把单个组最大值缩放为 1，不能映射为 Maya Normalize Weights；A1 已审计 `Normalize All` 和 Clean 的范围/锁定差异，使用明确保护的 Mesh/BMesh 适配。Maya Disable/Enable/Post 是持续模式，不是一次性归一化。Clean/Smooth/Limit Total 也不能直接宣称与 Maya 的 Prune/Smooth/最大影响数约束等价。

用户新报告的数据损坏、崩溃、错误命令或严重误触仍优先修复；修复已交付能力不等于恢复新增功能。构建与发布工作仅作为当前 UI/输入验证和交付所需的支撑。

A2 的后置设计线索保留：Remove Unused Influences 需明确全网格没有非零权重的变形骨组如何清理，并保护组锁和其他使用者；不能复用 A1 仅可见/选中顶点的快照。该功能尚未实现，也不在当前 UI/输入阶段展开。

## 4. 已确定的产品约束

1. 保留原生 Blender 全局菜单与 Workspace 栏；Modeling 只保留 Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、UV。Vertex/Edge/Face 在 Edit Mesh 内；不恢复 Deform/Generate 根，变形通过 Modifier。
2. 方向动作放紧凑热盒，设置/选项/深目录用原生菜单。四视图二级热盒是布局和操作标杆；五行实际按钮净间距、中心取消区、缺席方向和外延命中一起验证。伴随菜单不靠折叠/滚动压缩，下方放不下时底部对齐。
3. 每项使用统一 Blender 图标，Options 齿轮右侧对齐。保留 Maya 已核实的层级、分组、正文和 Options；灰占位不执行、不写 Recent、不制造 Undo。正文重复执行不能当作 Options。
4. 复用真实 Blender Menu/operator 宿主和插件回调；保留上下文、选区、poll、调用方式、取消与 Undo。不能为启用按钮而暗中换对象、全选或切模式。
5. Rigging 是原生工作区，Rigify 是内置模块；不向旧文件或个人 startup 自动注入布局。仍按用户明确决定搁置 [AXM-COMPAT-001](compatibility/global-object-scale.md)，不自动重启全局缩放改造。

## 5. 验收与每批交付

人工清单共 **330 项**，其中当前 318、历史 12。47 项仅有历史“已测试”信息，不等于全通过；全表初始未测 283，当前初始未测 271。最近新增 GU-01～GU-13，原 IN 与 RG 等编号和状态保持。新 GUI/输入必须使用包含本批 C++ 的新构建，9 月 17 日 Skin 包不适用。访客自己的记录仍独立保存，不能据自动化或维护者历史替他勾选。

每批完成顺序：更新设计 → 实现 → 与改动相称的静态/结果/真实事件或 GUI 验证 → 记录未覆盖人工项 → 更新 [CHANGELOG](CHANGELOG.md) → 提交推送并核验远端。验收变化时同步 Markdown 清单与公开 catalog；发布新版时绑定确切源码 SHA、校验包内资源、重新解压启动，再更新 Pages 构建版本。自动测试不改变人的测试结果。

## 6. 源码与证据入口

| 领域 | 首读文件 |
|---|---|
| 命令、配置与键位 | `scripts/modules/axismeld/commands.py`、`profiles.py`、`keymap.py`、`adapter.py` |
| 当前输入审计 | [生成对照](compatibility/current-input-audit.md)、[完整快照](compatibility/current-input-audit.json)；生成器 `tools/utils/axismeld_input_audit.py`，用 `--check` 检查漂移 |
| 热盒目录与交互 | `scripts/modules/axismeld/hotbox_catalog.py`、`hotbox_runtime.py`、`tool_hotbox.py`；[热盒约束](development/2026-09-14-hotbox-reference-contract.md) |
| 建模执行 | `scripts/modules/axismeld/modeling_registry.py`、`modeling_adapter.py`、`modeling_*_ops.py`；[M3 对照](maya-mapping/2026-09-14-m3-modeling-coverage.md) |
| 菜单与原生归类 | `menubar_reference.py`、`workspace_menu_catalog.py`、`workspace_native_groups.py`；`scripts/startup/bl_ui/space_axismeld_menubar.py` |
| Rigging/Rigify | `rigging_workspace_catalog.py`、`scripts/startup/bl_ui/space_axismeld_native_rigging.py`、`scripts/modules/rigify/`、`scripts/startup/rigify_builtin.py` |
| 默认布局与所有权 | `release/datafiles/startup.blend`、`source/blender/editors/screen/workspace_edit.cc`；[Rigging 设计和验证](development/2026-09-17-rigging-workspace.md) |
| 人工验收与公开页面 | [总清单](compatibility/2026-09-14-manual-test-ledger.md)、`tools/testing_site/`；生成器 `tools/utils/axismeld_public_test_catalog.py` |

新机器第一步按 [HANDOFF](HANDOFF.md) 核对分支和启动基线，先检查当前 GUI 验收回执、输入/菜单导出是否漂移，再处理实际反馈；不要重做本批入口和审计，也不要自行恢复 A2 算法。
