# AxisMeld 当前问题与验收边界

更新：2026-10-11，首批 GUI 收敛的历史起点为 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8`，本批版本见下文。本文件区分已确认未关闭的问题、尚未开发的能力和待人工验收，不把灰色占位、自动测试通过或历史用户反馈互相替代。

**最新交付（2026-10-11 18px companion preview）：热盒下方列表 18 像素预览已发布。** 仅将热盒下方伴随列表及其级联普通行高设为 18 逻辑像素（100% 界面缩放），Options 宽 18、细分隔 4.5；文字、图标、列宽和留白沿 18/24 的局部比例同步，高 DPI 保持 Blender 界面缩放规则；周围方向按钮、四视图间隔、主热盒栏及普通原生菜单保持原尺寸。完整条目、底部避让和说明无空间时隐藏的规则保持，不折叠、不滚动，不随窗口继续缩小。 沿用 Blender 5.4 Alpha 固定上游 `754ebe3c4b4e1402a159df6e1e58823cc93ef887`，本批未再次合并上游。6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-18px-companion-preview)，源码/native `f72fb413ba9c16f41c453dde98469ef1933285c1`；匿名下载、干净解压及工厂启动已核验。详见[本批验收](compatibility/2026-10-11-18px-companion-acceptance.md)与[发布快照](compatibility/2026-10-11-18px-companion-preview-snapshot.json)。本批 Pages `b448822d223e` 的 6 个公开资源逐字节核验通过。公开目录 345 项（当前 331、历史 14），47 项仅历史已测，当前初始未测 284、全表初始未测 298；最新标记 GU-28。既有编号与人工结果保持，自动化不替用户勾选。新增建模、Skin/Skeleton、UV 算法继续暂停。

当前优先级（2026-09-29 用户更正）：**先完成 UI、交互和快捷键对齐，暂停新增功能**。P1 为当前 UI/输入阶段应优先处理的对齐和验收；P2 为支撑交付或后续验证；P3 为已明确后置的新增功能。下述后置建议不是当前实施授权；进入实现前先核实源码和对应设计。

状态依据：[修改日志](CHANGELOG.md)、[统一人工清单](compatibility/2026-09-14-manual-test-ledger.md)、[Rigging 设计及交付记录](development/2026-09-17-rigging-workspace.md)、[公开目录](../tools/testing_site/catalog.json)。A1 已实现一次 Normalize Weights / Prune Small Weights 与独立 Options；[审计与验证](development/2026-09-17-skin-weight-cleanup.md)记录其有界行为。U0–U3 当前范围的实现已完成；Influences 等新算法继续暂缓，整批验证与发布状态见本页开头。

## 当前 GUI 收敛与验收（P1）

本批完成热盒下方列表及级联 18 逻辑像素行高调整与独立新构建交付，验收见[18 像素列表](compatibility/2026-10-11-18px-companion-acceptance.md)。周围方向按钮、Views 与普通菜单保持原尺寸；先前固定主干、Modeling 灰项保护、W/E/R 重复唤出复位、菜单快捷键/Options 和极低窗口说明避让保持。

- **目录与输入**：58 默认命令、60 条含别名绑定、7 个操纵器辅助入口、3 个原生模态持键入口、499 条原生继承、45 条移除、187 个受保护 keymap；基准/生成 keymap 为 281/282。原 18+2 参考已核对；静态定义一致不能直接推导行为等价。
- **已实施修复**：转换/当前工具/空组件预选、A History、X/V/J 临时吸附、9 空动态目录与 Grease Pencil 键位保护。定向审查同时修复原生模态取消残留、Face Path 接线/门禁、preheld Ctrl 时序、History 队列目标变化及 File 窗口残留松键泄漏。
- **File 交付边界**：只开放 Open Scene / Save Scene As 两条正文，无新增默认快捷键；精确 token 穿过未保存场景/修改图像确认链，只把捕获松键交给对应窗口。独立 Options 和其他未实现 File/Window 项保持原状态，不跳过原生确认。见 [File 设计](development/2026-10-11-file-window-release-design.md)。
- **验证状态**：6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过；实际范围见[本批验收](compatibility/2026-10-11-18px-companion-acceptance.md)。公开目录 345 项（当前 331、历史 14），47 项仅历史已测，当前初始未测 284、全表初始未测 298；最新标记 GU-28。既有编号与人工结果保持，自动化不替用户勾选。
- **能力边界**：D 自定义/独立枢轴、C 曲线吸附、F12 UV 域、1/2/3 平滑预览、Shift+J 相对模式后置；独立 Vertex Face、动态数据提供器仍缺能力。未接管 Blender 原生扩展键不宣称 Maya 等价，不因此扩大当前算法范围。

范围见 [UI/输入阶段](development/2026-09-29-ui-interaction-shortcuts.md)。高 DPI、任意插件/资产规模和实体鼠标手感保持单独验收；后续发现的具体 UI 缺陷继续优先修复。

## 已确认仍存在的问题和限制

### AXM-ISS-001 · 本批完整新 native 包发布门禁已关闭；跨机自动化仍后置（P2）

- **范围与证据**：当前发布包已有重新解压启动、源码资源比对及公开下载核验；这不证明一台全新机器仅凭仓库即可重复整条开发交付过程。历史候选组装与发布步骤使用过本机脚本、旧安装及回执，不能把这些旧目录当成新机器的必要输入。
- **已完成部分**：A1 已在独立 Windows checkout 完成公开基线审计/启动/GUI，增加固定 native 基线的 Python 包组装工具并发布 Skin 包。9 月 18 日已完成新环境原生构建、干净安装、141 个资源核对、所选五组 1,982 项 CTest、20 项 Runtime 和指定显示条件下的 GUI 验证；不能继续把“新机原生构建”列为未做。
- **本批已完成部分**：新 native 构建及针对性测试已执行，仓库已有完整安装静态审计工具；其正式模式核对提交源码、全部文件、受管模块集合、许可、运行库和 ZIP，拒绝残留模块、未扫描文本及 ZIP 文件/目录冲突。此工具不证明二进制可复现构建，也不替代实际启动。
- **首批关闭证据（历史）**：完整原生 `axismeld-2026.10.11-gui-preview` 已发布，功能与 native 源码均为 `41d71f26ccf12be5addd5c3453106bfa66f8de5f`。297,073,941 字节 ZIP 与校验文件已匿名重新下载核验；完整解压 6,498 个文件、144 项资源通过静态审计，工厂/portable 启动和解压包 File、上下文、临时吸附回归通过。线上目录 330 项、13 项新增与新 buildId 一致，见[发布快照](compatibility/2026-10-11-gui-preview-snapshot.json)。
- **文件完整性边界**：干净 ZIP 不含生成缓存；运行后新增的 517 个 pyc 仅为缓存，manifest 记录的 6,497 个文件完全不变。本批门禁已经关闭，不再作为当前 GUI 未交付内容。
- **跨机边界**：历史新机原生构建已经完成；跨机统一自动化、不同机器运行与可复现二进制仍需独立验证。一次本机完整包发布不证明每台新机器的全链验证已完成，相关工程保持后置。
- **后续交付规则**：继续记录源码修订、工具链、完整文件/资源清单与包校验值，独立解压启动及公开下载必须一致。旧 native 的 Python 组装器不适用于含新 C++ 的版本，不得关闭保护或拿旧可执行文件冒充新构建。
- **入口**：先读[当前构建与交付](BUILD_AND_DELIVERY.md)和[换机接续](HANDOFF.md)，再按需参考[Windows 历史构建基线](build/windows.md)、[上游更新](build/upstream-update.md)、[默认布局生成器](../tools/utils/axismeld_rigging_workspace_asset.py)与[构建身份核验](../tools/axismeld/verify_windows_build.ps1)。旧文档的固定机器路径和分支不能直接覆盖当前接续指引。

### AXM-ISS-002 · Isolate Select 书签动态参考仍不完整（P2，来源采集问题）

- **范围与证据**：Maya 的 `Current Pane → Show → Isolate Select → Bookmarks` 动态构建回调曾在隔离环境报原生命令错误。固定 `Bookmark Current Objects` 及 Options 已确认，动态书签成员未完整验证。不要与已核对的 `View → Bookmarks` 相机分支混淆，也不要称为当前 Blender 崩溃。
- **下一步**：单独复核该 Maya 原生回调和非空书签场景，先标明 UI 参考与占位边界；新增 Blender 场景数据提供器暂缓。原始命令文本只作参考，不执行到 Blender。
- **完成标准**：有固定结构及非空动态成员的独立证据，运行时成员反映当前场景；没有提供器时保持明确不可用状态，不伪造完整菜单。
- **入口**：[动态菜单边界](development/2026-09-14-maya-dynamic-menu-boundaries.md)、[参考快照](reference/maya2026-menu-tree.json)、[层级验收边界](compatibility/2026-09-15-maya-hierarchy-acceptance.md)。

### AXM-COMPAT-001 · Object Mode 的 Global 缩放差异（P3，用户决定不开发）

- **现状**：旋转对象的 Global 单轴缩放保留 Blender 原生变换计算，不保证与严格世界轴几何缩放等价；此差异未修复。
- **处置**：用户试用后明确无需开发，暂无开发计划，不阻挡建模或 Rigging；只有用户重新提出才启动。不得自行烘焙网格、应用旋转或增加隐藏补偿父级。
- **重新启动标准**：先确认参考操作与预期，再界定基础几何、修改器、层级、共享数据和 Undo。历史讨论不是待实施承诺。
- **入口**：[完整兼容性记录](compatibility/global-object-scale.md)、[变换命令声明](../scripts/modules/axismeld/commands.py)。

截至上述发布记录，未从最新证据确认仍未修复的阻断性崩溃或数据破坏问题。这不是“已知零缺陷”的保证；旧安装的应用级 CTest 历史失败也未被当成当前发布包失败。换机后应针对实际安装重新验证，不能沿用旧安装结果。

## 后置功能积压（当前暂停新增）

### Skin 当前适配与后置 Influences（P3）

当前 Skin 已有真实 `Armature Deform`、`Weight Paint Mode`、`Weights`、`Vertex Groups` 和 `Vertex Group Specials` 子菜单。归一化、清理、平滑、镜像、传递、限制权重数量等 Blender 操作已经可以从原生子菜单使用。Maya 正文和 Options 保留为灰色占位的部分，不能因此写成“功能已实现”。

| 建议顺序与范围 | 已有能力与需要补齐的部分 | 完成标准 |
|---|---|---|
| 1. Normalize Weights、Prune Small Weights（A1 已实施） | 单活动网格/唯一骨架的变形骨组；锁定、非骨骼组和选区保持，严格阈值、零值与最强保留有明确规则；独立 Options。 | 自动结果与 GUI 验证见 A1 设计；RG-15～RG-20 待人工验收。多骨架、共享/链接网格和多对象 Edit 暂拒绝。 |
| 2. Edit Influences（暂缓） | 尚未新增适配；恢复功能开发后建议先 Remove Unused，再 Add、Remove。可复用 A1 上下文保护与原生 Undo/Options 结构，但删除未使用组必须检查全网格，含隐藏和未选顶点。 | 正确处理锁组、非变形组、其他用途引用、多骨架和只读数据，验证删除后索引及活动组；不把一般顶点组删除当成完整 Influence 操作。 |
| 3. Bind/Unbind Skin 流程 | 原生四种 Armature Deform 已接入。Maya 位置的绑定参数、解绑保留权重/变换及修改器范围尚未适配。 | 明确只处理哪个骨架、网格和修改器；结果可观察且可撤销，不误删其他权重或变形器，不冒充 Maya 专有绑定算法。 |
| 4. Mirror/Copy Skin Weights | 原生 Mirror 和 Transfer Weights 已有；单向复制、镜像轴、源目标、骨骼名和空间映射需单独适配。 | 不因活动对象顺序产生反向覆盖；验证方向、不同拓扑、锁定、未匹配骨骼及 Undo，并公开算法差异。 |

实现前必须保留这些语义边界：

- Blender **Normalize** 把活动顶点组的最大值缩放为 1；**Normalize All** 才是逐顶点权重和归一化。后者默认锁定活动组，并会选择变形骨组范围，不能只换标签后直接声明等价。
- Maya Normalize 菜单的 Disable、Enable、Post 是持续模式；一次归一化或绘制工具的 Auto Normalize 不能代替完整模式语义。
- Clean 删除阈值以下或等于阈值的权重，包含组范围和 `keep_single` 参数；Prune 的目的相近不代表默认参数、锁定与归一化行为完全一致。Smooth 现有操作针对选中顶点；仅凭名称和菜单说明不能确认与 Maya 平滑算法等价。
- Limit Total 是一次性裁减，不是持续约束最大 Influences。Hammer、Interactive Bind 等没有等价实现的项继续灰显。

依据：[Rigging 目录](../scripts/modules/axismeld/rigging_workspace_catalog.py)、[原生 Rigging 入口与上下文保护](../scripts/startup/bl_ui/space_axismeld_native_rigging.py)、[原生权重菜单](../scripts/startup/bl_ui/space_view3d.py)、[顶点组操作实现](../source/blender/editors/object/object_vgroup.cc)、[Maya 菜单参考](reference/maya2026-menubar-tree.json)。

### 建模与 UV 功能计划保留；交互问题转入当前阶段

| 范围 | 当前缺口 | 下一步与完成标准 |
|---|---|---|
| M2 组件和工具上下文 | 前三个 GUI 入口与取消恢复已在本批实现，回归状态见本页开头；独立 Vertex Face 选择域未完成。 | 已有入口按 GU-01～GU-05 验收；需新增选择域或算法的部分暂缓。保留原选区、取消、按键释放、QWER 重复唤出和原生 fallback，不以“已有组合菜单”关闭全 M2。 |
| M3 建模语义适配 | Separate、Remesh、Cleanup、Transfer Attributes、Duplicate Special、通用 Similar 等仍有明确不可绑定原因；NURBS、曲面连续性和特定 deformer 关系保留独立缺失计划。 | 恢复功能开发后按 `M3-P-*` 稳定计划 ID 收敛，用真实几何与参数语义验收；相似原生操作可独立保留，不以错误 Maya 名称执行。 |
| UV 全工作流 | 已保留原生 UV 菜单与部分投影操作，但完整 Maya 风格 UV 工作区和操作链未完成。 | 恢复功能开发后先定义选择、展开、编辑、打包及跨编辑器上下文范围，再做小批真实操作与 Undo 验证，不把入口齐全当作完整工作流。 |
| 完整 Paint/Hair 与其他领域 | 完整绘制/毛发已明确后置；其他菜单集的结构可达不代表全部动画、FX、渲染算法完成。 | 保留既有原生能力和占位，用户明确新范围后独立设计；不因 UI 优先而删除原有缺失计划。 |

入口：[统一清单的已知边界](compatibility/2026-09-14-manual-test-ledger.md)、[M3 能力与计划映射](maya-mapping/2026-09-14-m3-modeling-coverage.md)、[稳定缺失计划声明](../scripts/modules/axismeld/modeling_gaps.py)、[禁止错误语义绑定的清单](../scripts/modules/axismeld/maya_menu_catalog.py)、[总体架构](design/2026-09-08-axismeld-architecture.md)。

## 待人工验收

目录统计来自仓库内供公开页部署的 `catalog.json`，并非私人云端记录或所有访客的实时进度；网页是否已收到本批目录须单独核验：

| 口径 | 数量与含义 |
|---|---|
| 全部稳定编号 | 345 项 |
| 当前有效验收 | 331 项 |
| 已替代的历史方案 | 14 项；保留可查询，不再要求按旧布局验收 |
| 历史已测试 | 47 项；历史状态保持，不补造通过/失败 |
| 目录初始未测 | 298 项；当前初始未测 284 项 |
| 最近新增 | GU-28，共 1 项；人工状态独立，原结果保持 |

| 优先级与范围 | 现有编号/依据 | 人工完成标准 |
|---|---|---|
| P1 · GUI 新入口/持键/取消 | GU-01～GU-13 | 用包含本批原生代码的新构建验证；按清单记录实际释放顺序、目标变化、显示缩放和一次 Undo。 |
| P1 · 建模灰项与热盒重复唤出 | GU-20～GU-21 | 无对象或错误模式时能查看原因，灰 Extrude 不预览错误原生子菜单；W/E/R 保持按下时再次 LMB 从根目录开始。原生可用内容、选区和取消行为保持。 |
| P1 · 极低窗口说明避让 | GU-22 | 检查说明全文及背板与所有菜单零交叠；无完整空白时隐藏，扩大窗口后恢复；菜单文字、布局、命中、选区及取消保持。 |
| P1 · Blender 主干兼容 | GU-23～GU-25 | 在新 5.4 包检查菜单原生入口、持键/文件窗口、Rigging 与旧场景副本；记录实际结果，不覆盖原场景。 |
| P1 · 热盒下方列表尺寸 | GU-28 | 在 100%/150% 与低窗口检查 18 逻辑像素伴随列表及级联的全文、可读性、状态/齿轮、命中与持键重复唤出；方向按钮、Views、普通菜单保持原尺寸，完整显示和底部避让保留。GU-27 旧 16 像素方案仅保留历史。 |
| P1 · 插件键位冲突诊断 | [IN-01～IN-03](compatibility/2026-10-11-input-diagnostics-acceptance.md) | 互斥模式不误报，真实模式/共享视图冲突仍提示，清理临时条目后恢复；不修改其他插件或用户键位。旧 9 月 17 日 Skin 包不含修复，不能用它验收本项。 |
| P1 · Rigging 布局与生命周期 | RG-07、RG-08、RG-14 | 两种键位、旧文件 Load UI、原生添加、改名/复制/保存重开，以及含用途标记的活动和非活动副本删除；剩余布局完整且无错误。 |
| P2 · 已交付蒙皮与权重 | RG-09 至 RG-13、RG-15 至 RG-20 | 保留既有待测状态；涉及当前菜单改动时核对占位、参数和可达性，真实变形/权重及 Undo 按原清单独立验收。 |
| P2 · 内置 Rigify 回归 | RG-01 至 RG-06 | 普通/工厂启动、生成与重开、旧偏好、禁用 Feature Set、原生设置和重载；生产角色变形与第三方骨架扩展仍需真实样本。 |
| P1 · 热盒实体鼠标与显示 | G、L、VR、K、FM、MT 等现有待测项 | 在实际缩放、单/四视图和用户布局下检查间隔、误触、原位取消、边缘完整显示与反复唤出。历史极小空间限制需在当前构建复核，不能拿旧失败直接判当前有缺陷。 |
| P1 · 建模与动态菜单 UI；功能结果另记 | M3、D、O、OM、MB-36 至 MB-41 等当前有效项 | 当前先验证菜单归属、参数齿轮、资产/插件入口与大量动态内容的高度；原生结果和撤销沿用原验收项，不能以菜单可见代替功能验收。 |

固定菜单与受测窗口通过，不证明任意动态资产、插件数量或高 DPI 下都不会出现长菜单问题。验收时记录构建标签、操作、显示缩放、实际结果和必要截图；失败应保留，不通过修改清单来消除失败。

[公开测试页](https://angelhob.github.io/AxisMeld/)的勾选只存当前浏览器，不自动跨设备同步或提交维护者。更换电脑前导出 JSON 备份；本地保存不等于已发 GitHub Issue。详见[门户说明](../tools/testing_site/README.md)。

## 已修复，保留回归但不再列为开放问题

- 极低窗口没有完整说明横带时仍画回菜单上：现按实际菜单边缘寻找二维空白，重新测量全文；无处容纳时隐藏，扩大窗口后恢复。实际 GUI 使用悬停前菜单截图验证全文、背板零交叠及菜单文字完整，GU-22 待人工。

- Modeling 原生灰项缺少模式/对象/视窗说明、无活动对象时灰 Extrude 悬停访问空对象：不适用入口现用带原因的灰按钮，保留静态条目及 UV/Modifiers 顶层内容；有效原生宿主、参数、poll 和插件回调保持，GU-20 待人工。
- W/E/R 持键时重复 LMB 唤出残留旧伴随菜单路径：每次 stroke 结束同步清理伴随路径，下次从根目录开始，真实 GUI 与既有工具/History/生命周期回归通过；GU-21 待人工。

- Space → File 新文件窗口残留松键泄漏：精确 token 绑定原生确认链与对应接收窗口，7 个实际 File 流程已通过；完整批次和发布状态见本页开头。取消不加载场景或保存目标文件，失焦/窗口销毁清理独立验证，GU-13 保持人工待测。
- Object Mode/Mesh 互斥模式插件键位冲突误报：本批只修提示作用域，仍报告共享 3D View/工具 map 的潜在冲突；针对性审计、输入及真实 RNA 验证见本页开头。新 GUI preview 已包含修复；IN-01～IN-03 保持人工待测，9 月 17 日旧包不适用。
- Rigging 默认资产缺少原生窗口关系而导致工厂启动失败：已修复并重新构建。
- 无对象时灰色 Edit Bones 菜单被悬停预览而读取空对象：无效入口现用灰标签，不创建可预览宿主。
- 本地对象使用链接只读 Armature 数据时 Pose、IK 和绑定目标被整组禁用：已按对象/数据写入边界修复。
- 带自定义属性的工作区删除时 Screen 用户被二次递减：已先清除自身引用，再释放该用户，完成新构建生命周期回归。
- 热盒五行横向间隔、Tool Header/侧栏遮挡及多个 Maya 标签误绑问题：相应修复已记录；继续保留人工手感及场景回归，不沿用旧报告把它们重新标成开放缺陷。

这些关闭依据是[修改日志](CHANGELOG.md)、[Rigging 设计验收](development/2026-09-17-rigging-workspace.md)、[四视图布局约束](development/2026-09-14-hotbox-reference-contract.md)和[菜单语义审查的实施回执](development/2026-09-14-maya-menu-binding-review.md)。自动检查、实际 GUI 样本和人工验收仍分别记账。
