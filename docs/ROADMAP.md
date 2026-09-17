# AxisMeld 整体规划与路线图

状态日期：2026-09-17。本文件是当前路线入口；旧日期的规格保留设计与证据，不代表当前完成度。

## 1. 目标与当前基线

AxisMeld 是可独立拉取、构建、运行的 Blender 衍生版本，以 Maya 2026 默认工作流为参照，优先改进建模、选择、导航、热盒与后续 UV；Rigify 和 Rigging 已纳入原生模块。继续使用 Blender 的数据、依赖图、渲染、文件格式及扩展生态。

| 入口 | 当前内容 |
|---|---|
| 开发源码 | [AngelHob/AxisMeld 的 axismeld/phase-2a](https://github.com/AngelHob/AxisMeld/tree/axismeld/phase-2a)；本批接续基线为 `96e0ce6dd081d6e3df001565e9f7fe223843358a`；后续以远端为准 |
| 默认分支 | `axismeld/integration`；目前承担仓库首页入口，**未包含最新开发实现**，不能直接用它继续功能开发 |
| 最新试用包 | [2026.09.17 Rigging preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-rigging-preview)，源码固定为 `617986ac184125fe2169456bdb525965530ea736` |
| Blender 基线 | `18d84097b4f859582afdec57eece2ae880371adc`，版本宏为 5.3.0 alpha；不等于后续上游最新版本 |
| 测试门户 | [GitHub Pages](https://angelhob.github.io/AxisMeld/)，源码 `tools/testing_site/`，部署分支 `gh-pages` |
| 交接与问题 | [新机器接续](HANDOFF.md) · [可复制提示词](CODEX_HANDOFF_PROMPT.md) · [当前问题](CURRENT_ISSUES.md) · [构建与交付](BUILD_AND_DELIVERY.md) |

当前是开发预览版。自动化通过、菜单可见、历史“已测试”和生产可用性是四个不同状态；不给出混合这些口径的完成百分比。

## 2. 已交付到哪里

| 模块 | 当前已交付 | 仍需区分的边界 |
|---|---|---|
| 基础发行与输入 | Windows x64 原生构建、AxisMeld 标识、Maya 键位预设、语义命令与分层配置 | 不是全平台稳定版；个人配置不得进入公开默认值 |
| 导航、操纵器与热盒 | Alt 导航、轴选择后中键拖动、单/四视图、Space/QWER/组件/上下文建模与创建热盒；图标、单选组、外延划选及伴随菜单整理 | 真实手感、高 DPI、窄视窗与第三方冲突仍按清单验收；不重新推翻四视图热盒基准 |
| 建模菜单与 M3 覆盖 | 全局 Blender 栏保留；Modeling 视窗七根菜单；原生功能分类接入、Maya 正文/Options 保留、缺失项灰显 | M3 是映射、可用原生能力和缺口计划的交付，**不是 Maya 所有建模算法完成** |
| Rigify 原生化 | 内置模块自动加载；创建、生成、偏好、Feature Sets 与重载生命周期已有验证 | 不再按可启停插件开发；复杂生成器及真实变形仍需人工验收 |
| Rigging 工作区 | 默认资产新增 Rigging；Skeleton/Skin 两根；9 个真实 Blender 入口；保留 Maya 82 条正文和 33 个 Options | A1 已适配一次 Normalize Weights / Prune Small Weights（含独立 Options），余下 80 正文/31 Options 仍灰显；原生 Weights 与新适配分开记账 |
| 公开测试与反馈 | 可下载预览包，稳定测试编号，本浏览器记录与 JSON 导出，GitHub Issue 反馈 | 网页勾选不会自动上传或跨设备同步；不是共用云数据库 |

建模菜单映射当前保留 **392 条 Maya 项（231 正文、161 Options）**，其中 85 条有执行绑定、307 条灰显。这是七根建模菜单的目录统计，不能与 M3 语义命令数或整套 Maya 功能数相加。详见[去向清单](compatibility/maya2026-workspace-menu-routes.json)。

Rigging 已发布验证包括 57 项针对菜单测试、8 个独立 Blender 进程及布局关系检查、实际 GUI 操作/撤销和发布包独立启动。这里只引用已发布证据，**本次文档整理没有重新宣称全量功能回归通过**。公开摘要见[交接快照](compatibility/2026-09-17-handoff-snapshot.json)。

## 3. 开发顺序

以下是按现状整理的建议路线，不是已执行任务，也不是对每个参数语义的预先批准。每批先核实设计和当前源码，再实现一个有界结果；具体安排可随用户反馈调整。人工测试暂缓不阻止可自动验证的开发。

| 顺序 | 交付批次 | 工作内容 | 完成标准 |
|---|---|---|---|
| A0 当前交接 | 可从 GitHub 恢复工作 | 统一路线、问题、分支、构建和提示词，公开经过筛选的发布指纹；清除陈旧首页状态 | 新代理无需聊天记录即可找到正确源码、资产、测试和下一任务；新机器实测仍单独记录 |
| A1 已实施 | Skin：归一化与小权重清理 | 审计 Normalize Weights / Prune Small Weights；明确骨架、顶点范围、锁定、零权重与阈值；接入可证明的原生适配和独立 Options | 实际权重结果、无关顶点组保持、失败无修改、一次 Undo、参数入口和真实菜单路由有测试；差异明确可见 |
| A2 下一批 | Skin：影响骨与绑定管理 | Add/Remove/Remove Unused Influences，随后 Bind/Unbind；识别目标 Armature Modifier，区分保留权重、父级与变换 | 不误删其他用途组；多修改器、链接数据、无效选择和撤销有确定行为；不拿 Clear Parent 冒充解绑 |
| A3 | Skin：镜像与复制 | 明确源目标、方向、骨名匹配、拓扑/空间映射及锁定处理，适配 Mirror/Transfer | 对称/非对称、同/异拓扑、不同变换及一次 Undo 可验证；保留 native Blender 参数差异 |
| A4 | Skeleton 常用操作 | 在现有 Edit Bones/Pose/IK/Rigify 上按使用频率补 Joint 创建/插入/镜像/定向等语义映射 | 区分 rest/pose、bone roll/关节定向、连接/父子关系；不能仅改标签认定算法相同 |
| B1 持续主线 | 建模剩余缺口 | 按 M3 现有计划 ID 处理高频灰项、Options 和严格上下文限制；优先能准确适配原生的条目 | 逐项记录 exact/adapted/unsupported、结果/撤销/参数与可达性；不删除未实现占位来减少问题数 |
| B2 | 动态目录和交互收尾 | 场景相关材质、集合、历史/输入输出等目录按 Blender 数据语义适配；修复人工或回归明确发现的问题 | 空/非空/失效对象有证据；动态内容不能冻结为某次 Maya 场景实例；热盒布局约束保持 |
| C1 后续独立阶段 | UV 基础 | UV 工作区与输入、组件/shell 选择、Cut/Sew/Move and Sew、分裂/缝合 | 使用原生 Mesh/BMesh/UV 数据；快捷键范围、Undo、保存重开和热盒回归通过 |
| C2 | UV 生产能力 | Align/Straighten/Orient/Stack → Unfold/Relax/Pins → Layout/密度/间距/UDIM → 检查诊断与预设 | 分阶段性能与结果测试，避免 UI 和算法耦合；每段都可独立使用和回退 |
| D 持续工程 | 构建、回归与上游维护 | 新机器全链验证、统一打包、针对性测试入口、依赖固定、上游接缝审计；以后再扩展其他平台 | 干净安装、源码/二进制/资源对应、许可证、公开下载与测试版本一致；不以一次本机成功声称可复现构建 |

A1 的语义审计、实现及验证见[Skin 权重整理](development/2026-09-17-skin-weight-cleanup.md)。本批已开放两项一次操作，下一批从 A2 Influences 开始。Native `Normalize` 只把单个组最大值缩放为 1，不能映射为 Maya Normalize Weights；本批已审计 `Normalize All` 和 Clean 的范围/锁定差异，使用明确保护的 Mesh/BMesh 适配。Maya Disable/Enable/Post 是持续模式，不是一次性归一化。Clean/Smooth/Limit Total 也不能直接宣称与 Maya 的 Prune/Smooth/最大影响数约束等价。

建模 B1 可与 Rigging 分批交替，但不要同时扩大两套实现范围。用户新报告的数据损坏、崩溃、错误命令或严重误触优先于上表新增功能。

## 4. 已确定的产品约束

1. 保留原生 Blender 全局菜单与 Workspace 栏；Modeling 只保留 Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、UV。Vertex/Edge/Face 在 Edit Mesh 内；不恢复 Deform/Generate 根，变形通过 Modifier。
2. 方向动作放紧凑热盒，设置/选项/深目录用原生菜单。四视图二级热盒是布局和操作标杆；五行实际按钮净间距、中心取消区、缺席方向和外延命中一起验证。伴随菜单不靠折叠/滚动压缩，下方放不下时底部对齐。
3. 每项使用统一 Blender 图标，Options 齿轮右侧对齐。保留 Maya 已核实的层级、分组、正文和 Options；灰占位不执行、不写 Recent、不制造 Undo。正文重复执行不能当作 Options。
4. 复用真实 Blender Menu/operator 宿主和插件回调；保留上下文、选区、poll、调用方式、取消与 Undo。不能为启用按钮而暗中换对象、全选或切模式。
5. Rigging 是原生工作区，Rigify 是内置模块；不向旧文件或个人 startup 自动注入布局。仍按用户明确决定搁置 [AXM-COMPAT-001](compatibility/global-object-scale.md)，不自动重启全局缩放改造。

## 5. 验收与每批交付

人工清单共 **314 项**，其中当前 302、已替代历史 12。47 项仅有历史“已测试”信息，不等于全通过；全表初始未测 267，剔除历史后的当前初始未测 255。RG-07～RG-14 仍待测；新增 RG-15～RG-20 全部待测。每位网页访客有自己的记录，不能据维护者历史自动替他勾选。

每批完成顺序：更新设计 → 实现 → 与改动相称的静态/结果/真实事件或 GUI 验证 → 记录未覆盖人工项 → 更新 [CHANGELOG](CHANGELOG.md) → 提交推送并核验远端。验收变化时同步 Markdown 清单与公开 catalog；发布新版时绑定确切源码 SHA、校验包内资源、重新解压启动，再更新 Pages 构建版本。自动测试不改变人的测试结果。

## 6. 源码与证据入口

| 领域 | 首读文件 |
|---|---|
| 命令、配置与键位 | `scripts/modules/axismeld/commands.py`、`profiles.py`、`keymap.py`、`adapter.py` |
| 热盒目录与交互 | `scripts/modules/axismeld/hotbox_catalog.py`、`hotbox_runtime.py`、`tool_hotbox.py`；[热盒约束](development/2026-09-14-hotbox-reference-contract.md) |
| 建模执行 | `scripts/modules/axismeld/modeling_registry.py`、`modeling_adapter.py`、`modeling_*_ops.py`；[M3 对照](maya-mapping/2026-09-14-m3-modeling-coverage.md) |
| 菜单与原生归类 | `menubar_reference.py`、`workspace_menu_catalog.py`、`workspace_native_groups.py`；`scripts/startup/bl_ui/space_axismeld_menubar.py` |
| Rigging/Rigify | `rigging_workspace_catalog.py`、`scripts/startup/bl_ui/space_axismeld_native_rigging.py`、`scripts/modules/rigify/`、`scripts/startup/rigify_builtin.py` |
| 默认布局与所有权 | `release/datafiles/startup.blend`、`source/blender/editors/screen/workspace_edit.cc`；[Rigging 设计和验证](development/2026-09-17-rigging-workspace.md) |
| 人工验收与公开页面 | [总清单](compatibility/2026-09-14-manual-test-ledger.md)、`tools/testing_site/`；生成器 `tools/utils/axismeld_public_test_catalog.py` |

新机器第一步按 [HANDOFF](HANDOFF.md) 核对分支和启动基线，核实 A1 后从 A2 开始；不要根据旧规格中的历史“尚未实现”重做已经交付的工作。
