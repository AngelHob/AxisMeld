# AxisMeld 当前问题与验收边界

更新：2026-09-17。本文件区分已确认未关闭的问题、尚未开发的能力和待人工验收，不把灰色占位、自动测试通过或历史用户反馈互相替代。当前发布为 `axismeld-2026.09.17-skin-weights-preview`，Python 功能源码为 `bf35ab393b7c`；native 来源仍为 `617986ac1841`，本批未修改 C++ 或内嵌资产。

优先级：P1 为下一批应优先处理的交付或常用流程缺口；P2 为有界后续开发或验证；P3 为已明确后置。下述“建议”不是用户已经批准的具体实现、参数或算法承诺。进入实现前先核实当前源码，再更新对应设计。

状态依据：[修改日志](CHANGELOG.md)、[统一人工清单](compatibility/2026-09-14-manual-test-ledger.md)、[Rigging 设计及交付记录](development/2026-09-17-rigging-workspace.md)、[公开目录](../tools/testing_site/catalog.json)。A1 已实现一次 Normalize Weights / Prune Small Weights 与独立 Options；[审计与验证](development/2026-09-17-skin-weight-cleanup.md)记录其有界行为，下一批为 Influences。

## 已确认仍存在的问题和限制

### AXM-ISS-001 · 新机全链路实测与统一打包自动化未闭合（P1）

- **范围与证据**：当前发布包已有重新解压启动、源码资源比对及公开下载核验；这不证明一台全新机器仅凭仓库即可重复整条开发交付过程。历史候选组装与发布步骤使用过本机脚本、旧安装及回执，不能把这些旧目录当成新机器的必要输入。
- **本轮已补部分**：交接提供独立构建、安装和标准打包配方，并将已发布 ZIP 的只读审计迁入仓库。A1 已在独立新 checkout 完成公开包下载/启动/GUI 验证，新增固定 native 基线的 Python 包组装工具并完成新包解压验收；native 从零编译和完整发布流水线仍未闭合。
- **下一步**：在干净机器或隔离环境，从指定源码、公开上游依赖和明确工具链开始，独立完成构建、安装、资源清单、打包、解压启动与校验；再将需要长期维护的候选组装和打包步骤收敛为仓库内脚本。
- **完成标准**：不读取维护者旧安装或私人回执即可完成；记录源码修订、工具链、资源清单与包校验值；失败退出明确，不拿旧可执行文件冒充新 C++ 或内嵌资产构建。
- **入口**：先读[当前构建与交付](BUILD_AND_DELIVERY.md)和[换机接续](HANDOFF.md)，再按需参考[Windows 历史构建基线](build/windows.md)、[上游更新](build/upstream-update.md)、[默认布局生成器](../tools/utils/axismeld_rigging_workspace_asset.py)与[构建身份核验](../tools/axismeld/verify_windows_build.ps1)。旧文档的固定机器路径和分支不能直接覆盖当前接续指引。

### AXM-ISS-002 · Isolate Select 书签动态参考仍不完整（P2，来源采集问题）

- **范围与证据**：Maya 的 `Current Pane → Show → Isolate Select → Bookmarks` 动态构建回调曾在隔离环境报原生命令错误。固定 `Bookmark Current Objects` 及 Options 已确认，动态书签成员未完整验证。不要与已核对的 `View → Bookmarks` 相机分支混淆，也不要称为当前 Blender 崩溃。
- **下一步**：单独复核该 Maya 原生回调和非空书签场景，再定义 Blender 的场景数据提供器；原始命令文本只作参考，不执行到 Blender。
- **完成标准**：有固定结构及非空动态成员的独立证据，运行时成员反映当前场景；没有提供器时保持明确不可用状态，不伪造完整菜单。
- **入口**：[动态菜单边界](development/2026-09-14-maya-dynamic-menu-boundaries.md)、[参考快照](reference/maya2026-menu-tree.json)、[层级验收边界](compatibility/2026-09-15-maya-hierarchy-acceptance.md)。

### AXM-COMPAT-001 · Object Mode 的 Global 缩放差异（P3，用户决定不开发）

- **现状**：旋转对象的 Global 单轴缩放保留 Blender 原生变换计算，不保证与严格世界轴几何缩放等价；此差异未修复。
- **处置**：用户试用后明确无需开发，暂无开发计划，不阻挡建模或 Rigging；只有用户重新提出才启动。不得自行烘焙网格、应用旋转或增加隐藏补偿父级。
- **重新启动标准**：先确认参考操作与预期，再界定基础几何、修改器、层级、共享数据和 Undo。历史讨论不是待实施承诺。
- **入口**：[完整兼容性记录](compatibility/global-object-scale.md)、[变换命令声明](../scripts/modules/axismeld/commands.py)。

截至上述发布记录，未从最新证据确认仍未修复的阻断性崩溃或数据破坏问题。这不是“已知零缺陷”的保证；旧安装的应用级 CTest 历史失败也未被当成当前发布包失败。换机后应针对实际安装重新验证，不能沿用旧安装结果。

## 待开发能力

### Skin 当前适配与下一批 Influences（P1）

当前 Skin 已有真实 `Armature Deform`、`Weight Paint Mode`、`Weights`、`Vertex Groups` 和 `Vertex Group Specials` 子菜单。归一化、清理、平滑、镜像、传递、限制权重数量等 Blender 操作已经可以从原生子菜单使用。Maya 正文和 Options 保留为灰色占位的部分，不能因此写成“功能已实现”。

| 建议顺序与范围 | 已有能力与需要补齐的部分 | 完成标准 |
|---|---|---|
| 1. Normalize Weights、Prune Small Weights（A1 已实施） | 单活动网格/唯一骨架的变形骨组；锁定、非骨骼组和选区保持，严格阈值、零值与最强保留有明确规则；独立 Options。 | 自动结果与 GUI 验证见 A1 设计；RG-15～RG-20 待人工验收。多骨架、共享/链接网格和多对象 Edit 暂拒绝。 |
| 2. Edit Influences | 顶点组增删和锁定已有；添加/移除影响骨、移除未使用影响骨仍需识别当前 Armature 与实际变形骨。 | 正确处理空组、锁组、非变形组、多骨架和只读数据；不把一般顶点组删除当成完整 Influence 操作。 |
| 3. Bind/Unbind Skin 流程 | 原生四种 Armature Deform 已接入。Maya 位置的绑定参数、解绑保留权重/变换及修改器范围尚未适配。 | 明确只处理哪个骨架、网格和修改器；结果可观察且可撤销，不误删其他权重或变形器，不冒充 Maya 专有绑定算法。 |
| 4. Mirror/Copy Skin Weights | 原生 Mirror 和 Transfer Weights 已有；单向复制、镜像轴、源目标、骨骼名和空间映射需单独适配。 | 不因活动对象顺序产生反向覆盖；验证方向、不同拓扑、锁定、未匹配骨骼及 Undo，并公开算法差异。 |

实现前必须保留这些语义边界：

- Blender **Normalize** 把活动顶点组的最大值缩放为 1；**Normalize All** 才是逐顶点权重和归一化。后者默认锁定活动组，并会选择变形骨组范围，不能只换标签后直接声明等价。
- Maya Normalize 菜单的 Disable、Enable、Post 是持续模式；一次归一化或绘制工具的 Auto Normalize 不能代替完整模式语义。
- Clean 删除阈值以下或等于阈值的权重，包含组范围和 `keep_single` 参数；Prune 的目的相近不代表默认参数、锁定与归一化行为完全一致。Smooth 现有操作针对选中顶点；仅凭名称和菜单说明不能确认与 Maya 平滑算法等价。
- Limit Total 是一次性裁减，不是持续约束最大 Influences。Hammer、Interactive Bind 等没有等价实现的项继续灰显。

依据：[Rigging 目录](../scripts/modules/axismeld/rigging_workspace_catalog.py)、[原生 Rigging 入口与上下文保护](../scripts/startup/bl_ui/space_axismeld_native_rigging.py)、[原生权重菜单](../scripts/startup/bl_ui/space_view3d.py)、[顶点组操作实现](../source/blender/editors/object/object_vgroup.cc)、[Maya 菜单参考](reference/maya2026-menubar-tree.json)。

### 建模、交互与 UV 主线继续保留（P2，逐项立项）

| 范围 | 当前缺口 | 下一步与完成标准 |
|---|---|---|
| M2 组件和工具上下文 | Edit 无选择预选、Ctrl+RMB 选择转换、Ctrl+Shift+RMB 当前工具上下文仍有后续切片；独立 Vertex Face 选择域未完成。 | 按输入和选择事务分别实施，保证原选区、取消、按键释放、QWER 持键重复唤出和原生 fallback；不得以“已有组合菜单”关闭全 M2。 |
| M3 建模语义适配 | Separate、Remesh、Cleanup、Transfer Attributes、Duplicate Special、通用 Similar 等仍有明确不可绑定原因；NURBS、曲面连续性和特定 deformer 关系保留独立缺失计划。 | 继续按 `M3-P-*` 稳定计划 ID 收敛，用真实几何与参数语义验收；相似原生操作可独立保留，不以错误 Maya 名称执行。 |
| UV 全工作流 | 已保留原生 UV 菜单与部分投影操作，但完整 Maya 风格 UV 工作区和操作链未完成。 | 先定义选择、展开、编辑、打包及跨编辑器上下文范围，再做小批真实操作与 Undo 验证，不把入口齐全当作完整工作流。 |
| 完整 Paint/Hair 与其他领域 | 完整绘制/毛发已明确后置；其他菜单集的结构可达不代表全部动画、FX、渲染算法完成。 | 保留既有原生能力和占位，用户明确新范围后独立设计；不因 Skin 优先而删除建模缺失计划。 |

入口：[统一清单的已知边界](compatibility/2026-09-14-manual-test-ledger.md)、[M3 能力与计划映射](maya-mapping/2026-09-14-m3-modeling-coverage.md)、[稳定缺失计划声明](../scripts/modules/axismeld/modeling_gaps.py)、[禁止错误语义绑定的清单](../scripts/modules/axismeld/maya_menu_catalog.py)、[总体架构](design/2026-09-08-axismeld-architecture.md)。

## 待人工验收

目录统计来自当前公开 `catalog.json`，并非私人云端记录或所有访客的实时进度：

| 口径 | 数量与含义 |
|---|---|
| 全部稳定编号 | 314 项 |
| 当前有效验收 | 302 项 |
| 已替代的历史方案 | 12 项；保留可查询，不再要求按旧布局验收 |
| 历史已测试 | 47 项；用户只确认“已测试”，未补造通过/失败 |
| 目录初始未测 | 267 项，包含 12 项历史方案；剔除历史后的当前初始未测为 255 项 |
| 最近新增 | RG-15 至 RG-20，共 6 项，全部待人工测试；RG-07 至 RG-14 仍待测，原结果保持 |

| 优先级与范围 | 现有编号/依据 | 人工完成标准 |
|---|---|---|
| P1 · Rigging 布局与生命周期 | RG-07、RG-08、RG-14 | 两种键位、旧文件 Load UI、原生添加、改名/复制/保存重开，以及含用途标记的活动和非活动副本删除；剩余布局完整且无错误。 |
| P1 · 真实蒙皮与权重 | RG-09 至 RG-13、RG-15 至 RG-20 | 核对完整占位、参数、真实生成和变形、权重及 Undo；包含本地对象引用链接只读骨架数据的 Pose/IK 与绑定；第三方插件样本单独记录。 |
| P1 · 内置 Rigify 回归 | RG-01 至 RG-06 | 普通/工厂启动、生成与重开、旧偏好、禁用 Feature Set、原生设置和重载；生产角色变形与第三方骨架扩展仍需真实样本。 |
| P1 · 热盒实体鼠标与显示 | G、L、VR、K、FM、MT 等现有待测项 | 在实际缩放、单/四视图和用户布局下检查间隔、误触、原位取消、边缘完整显示与反复唤出。历史极小空间限制需在当前构建复核，不能拿旧失败直接判当前有缺陷。 |
| P2 · 建模与动态菜单压力 | M3、D、O、OM、MB-36 至 MB-41 等当前有效项 | 验证菜单归属、参数齿轮、原生操作与撤销、资产和插件入口、大量动态内容的高度，以及公开反馈流程。 |

固定菜单与受测窗口通过，不证明任意动态资产、插件数量或高 DPI 下都不会出现长菜单问题。验收时记录构建标签、操作、显示缩放、实际结果和必要截图；失败应保留，不通过修改清单来消除失败。

[公开测试页](https://angelhob.github.io/AxisMeld/)的勾选只存当前浏览器，不自动跨设备同步或提交维护者。更换电脑前导出 JSON 备份；本地保存不等于已发 GitHub Issue。详见[门户说明](../tools/testing_site/README.md)。

## 已修复，保留回归但不再列为开放问题

- Rigging 默认资产缺少原生窗口关系而导致工厂启动失败：已修复并重新构建。
- 无对象时灰色 Edit Bones 菜单被悬停预览而读取空对象：无效入口现用灰标签，不创建可预览宿主。
- 本地对象使用链接只读 Armature 数据时 Pose、IK 和绑定目标被整组禁用：已按对象/数据写入边界修复。
- 带自定义属性的工作区删除时 Screen 用户被二次递减：已先清除自身引用，再释放该用户，完成新构建生命周期回归。
- 热盒五行横向间隔、Tool Header/侧栏遮挡及多个 Maya 标签误绑问题：相应修复已记录；继续保留人工手感及场景回归，不沿用旧报告把它们重新标成开放缺陷。

这些关闭依据是[修改日志](CHANGELOG.md)、[Rigging 设计验收](development/2026-09-17-rigging-workspace.md)、[四视图布局约束](development/2026-09-14-hotbox-reference-contract.md)和[菜单语义审查的实施回执](development/2026-09-14-maya-menu-binding-review.md)。自动检查、实际 GUI 样本和人工验收仍分别记账。
