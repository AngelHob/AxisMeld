# 当前菜单 GUI 收敛与逐项核对

## 范围与判定

2026-10-11 用户要求完成现有 GUI。本切片覆盖已经开放的工作区菜单、原生 Blender 菜单接入、热盒普通目录与伴随菜单；不增加未适配算法，也不把灰色功能项计为 GUI 未完成。继续保留 Blender 全局栏、Modeling 七根以及 Edit Mesh 内的 Vertex / Edge / Face，Rigging 保留 Skeleton / Skin 两根。

核对使用仓库内隔离 Maya 2026 采集后保存的参考，逐级比较固定目录的标签、顺序、父子、分隔、独立 Options 与状态类型。自动化能证明当前源码和参考一致、绘制调用与上下文保护成立，不能替代实体鼠标手感与任意设备尺寸的人工验收。

## 可执行差异清单（实现前）

| 检查项 | 当前证据与处置 |
|---|---|
| Blender 全局栏与工作区栏 | 已保留；验证原生类与真实菜单宿主，避免重复开发 |
| Modeling 目录 | 已有七根、392 条 Maya 正文/Options、完整 Blender 原生绘制归类；用递归与来源引用检查守住无遗漏 |
| Rigging 目录 | Skeleton / Skin 已有 Maya 层级和原生入口；保持已有 Normalize / Prune 正文与独立 Options |
| 热盒普通目录 | 22 个完整固定根已有逐级对照；伴随菜单与方向环另按截图参考检查 |
| 无 provider 的动态空目录 | **确认缺陷**：菜单栏仍生成可展开 submenu；实际没有内容，缺失原因不可见。改为同位置灰色占位按钮，显示原有缺失原因；目录身份与来源保留 |
| 含固定条目的动态目录 | 继续开放子目录，即使固定条目全部灰显也允许查看；不可把未适配功能整组隐藏 |
| 原生动态 provider | 继续调用真实 Blender provider，不按当前空快照禁用，不冻结用户场景或资产内容 |
| 右侧齿轮与图标 | 已有 C++ 最终列对齐、Blender 图标与 radio/checkbox 区分；本切片不重写几何 |
| 不折叠、不滚动与底部对齐 | 目录层级已有独立 Maya 树；完整布局和边缘处理由热盒 C++ 切片核验，保留合理原生子目录 |

## 最小修复设计

仅当自有目录没有任何非分隔子项时，将该目录绘制为不可执行的灰色占位，tooltip 使用记录的动态原因或明确的默认说明。不能调用 runtime source capture、不能创建空 submenu、不能制造 Undo/Recent。含灰色正文的目录仍可展开，原生 `native` / `native_group` / `rigging_native` 路由不受影响。纯目录内容审计同时保留这些空目录，以免“消灭空菜单”变成删掉 Maya 功能占位。

先新增空目录、只有标题/分隔的目录、全灰但有正文目录的绘制回归，观察失败后再修改实现。最终核对数量与验证回执追加在本文件后部。

## 全目录核对结果

本次重新运行当前源码的完整递归比较，不以几个菜单截图替代目录审计：

- 应用菜单参考共 **43 根、3,108 个来源节点**，含 1,829 正文、639 独立 Options、392 分隔/标题以及 248 根/子目录。当前投影共 3,722 个节点、401 个目录；Maya 来源正文和 Options 全部保留，不同工作区的入口限制仍按用户决定。
- Modeling 七根保留 **231 正文 + 161 Options**。34 个 Blender 扩展功能按用途归类；162 个原生模式放置引用逐项核对为 149 个实际绘制引用、11 个完整调用等价别名和 2 个原生等价别名。未将动态 provider 内部条目虚报为固定功能数。
- Rigging 两根保留 **82 正文 + 33 Options**及 9 个真实原生入口。Normalize / Prune 的 2 正文与 2 Options 已适配，其余继续明确灰显。所有来源条目、分组、顺序与独立 Options 逐项比较。
- 热盒的 **22 个固定目录根、1,949 个来源节点、369 个 Options**完成递归标签、顺序、父子、分隔、状态类型比较。创建/建模伴随菜单继续按已有完整截图参考核对，不能把新交互入口算成新增 Maya 算法。
- 当前应用目录使用 **71 种 Blender 图标名**；所有非分隔正文与目录都有图标声明，独立 Options 在绘制端使用 `PREFERENCES`，checkbox/radio 与正文图标分别呈现。原生 provider 的动态内部内容继续由其真实菜单负责。

### 当前工作区九根

“根记录”包含标题与分隔，Options 是右侧同一行按钮，不额外增加垂直行数。正文数量含各级子目录；因此不能拿正文总数当作一层菜单高度。

| 当前根 | 根记录 | Maya 正文 | Maya Options | 当前目录数（含该根） |
|---|---:|---:|---:|---:|
| Mesh | 37 | 32 | 26 | 14 |
| Edit Mesh | 23 | 27 | 16 | 37 |
| Mesh Tools | 20 | 38 | 37 | 6 |
| Mesh Display | 48 | 38 | 10 | 16 |
| Curves | 50 | 36 | 24 | 24 |
| Surfaces | 53 | 41 | 37 | 16 |
| UV | 31 | 19 | 11 | 6 |
| Skeleton | 27 | 54 | 8 | 3 |
| Skin | 33 | 28 | 25 | 3 |

Edit Mesh 的 2 个 Curve 正文及 Options 已在先前批准的布局中移到 Mesh Tools → Curve Projection；上表统计实际去向。目录数是目录节点数量，不是最大嵌套深度。

较长根的来源拆分：Surfaces 的 **43 条 Maya 原记录（31 非分隔 + 12 标题/分隔）+ 10 个 Blender 用途子目录**；Curves 为 37 + 13；Mesh Display 为 37 + 11。新增入口已经进入 Construct、Geometry、Topology、Control Points、Transform 等用途子目录，没有展开原生内部按钮。保持这些已批准归类，不再添加模糊的总目录，也不移动或删减 Maya 原正文来缩短根层。

### 热盒固定根完整覆盖

下表是当前每个固定根的可见记录数与各级目录中最长一层记录数。每一层的顺序、标题、状态类型和 Options 均由 `axismeld_maya_hierarchy_test.py` 递归校验，不是只对比数量。

| 组/根 | 根记录 | 最长一层 |
|---|---:|---:|
| Common / File | 37 | 37 |
| Common / Edit | 25 | 41 |
| Common / Create | 22 | 22 |
| Common / Select | 36 | 36 |
| Common / Modify | 34 | 34 |
| Common / Display | 21 | 36 |
| Common / Windows | 22 | 22 |
| Current Pane / View | 28 | 28 |
| Current Pane / Shading | 22 | 22 |
| Current Pane / Lighting | 8 | 8 |
| Current Pane / Show | 12 | 53 |
| Current Pane / Renderer | 1 | 1 |
| Current Pane / Panels | 14 | 26 |
| Modeling / Mesh | 26 | 26 |
| Modeling / Edit Mesh | 35 | 35 |
| Modeling / Mesh Tools | 16 | 23 |
| Modeling / Mesh Display | 37 | 37 |
| Modeling / Curves | 37 | 37 |
| Modeling / Surfaces | 43 | 43 |
| Modeling / Deform（保留参考/既有热盒，非 Modeling 视窗根） | 42 | 42 |
| Modeling / UV | 26 | 26 |
| Modeling / Generate（保留参考/既有热盒，非 Modeling 视窗根） | 36 | 36 |

最长固定目录为 `Show → Playblast Display`，**53 记录 / 46 非分隔**，这是 Maya 原目录，不是之前错误展平的 Display。Display 根仍为 21 记录，Polygons 是独立子目录。

## 修复结果与验证

9 个空目录逐个保持原标签、Blender 图标与来源数据，统一显示灰色按钮和缺失原因：Recent Increments、Recent Projects、Delete by Type → Sounds、Quick Select Sets、Mesh Display → Assign Existing Set、FX → Effects → Apply Effect / Collide with Effect、Rendering → Lighting/Shading → Assign Existing Material、Toon → Set Camera Background Color。后四个属于已存在的其它菜单集访问入口，本轮没有增加相关功能。

回归先在原实现观察到 `Empty submenu must not open` 失败，再实现绘制修复并通过。新增测试同时覆盖仅有标题/分隔的目录、含灰色正文但必须可展开的目录，以及所有 9 个真实空目录不修改源 catalog。原生动态提供器保留，不会因为当前没有资产或场景成员而被误禁用。

本切片最终 **17 个纯 Python 套件、169 项测试通过**：menubar UI 19、runtime 12、reference 11、native 14、catalog 12、actions 10；Maya snap binding 4、reference generator 12、menu binding 15、hierarchy 6、companion 4；workspace catalog 14、native modeling 9、native rigging 11、rigging catalog 5、rigging UI 7、native topbar 4。

审计发现原 `native_modeling_groups` AST 测试只加载 `enabled` / `modeling_workspace`，遗漏后者现在依赖的 `rigging_workspace`，导致测试探针 NameError。已补齐真实依赖，并新增 Rigging 工作区以及带 Rigging role 但改名为 Modeling 的隔离用例；不修改生产模式判定来迁就旧测试。

全量搜索现有 `*events.py`：没有用例依赖上述 9 个应用空目录展开。`maya_hierarchy` / `full_menu_entry` 验证独立热盒目录，不受这个菜单栏修复影响；齿轮几何测试仍保留原真实执行与灰齿轮不执行断言，没有跳过现有用例。

## 完整显示与尺寸边界

对当前 **401 个自有目录**的完整分列规划重新实算，四种窗口高度/缩放下每个已规划列均不超过现有行高预算，所有原记录顺序保留、没有折叠或截断：

| 窗口高度 / UI 缩放 | 所有非空目录合计列数 | Mesh / Edit Mesh / Mesh Tools / Mesh Display / Curves / Surfaces / UV / Skeleton / Skin 列数 |
|---|---:|---|
| 1080 px / 100% | 398 | 1 / 1 / 1 / 1 / 2 / 2 / 1 / 1 / 1 |
| 1080 px / 150% | 412 | 2 / 1 / 1 / 2 / 2 / 2 / 2 / 1 / 2 |
| 720 px / 100% | 412 | 2 / 1 / 1 / 2 / 2 / 2 / 2 / 1 / 2 |
| 720 px / 150% | 454 | 3 / 2 / 2 / 3 / 3 / 3 / 2 / 2 / 2 |

**这张表验证 Python 分列规划，不是完整像素几何或 GUI 验收**：它不测最终字体/菜单边框的宽度，也不枚举外部插件和用户资产 provider 的动态数量。本批实际 GUI 测试另由统一交付回执记录，至少应覆盖 Surfaces、Curves、Mesh Display 及两种界面缩放，核对末行、右齿轮、屏幕边缘和点击行为。

热盒已有明确几何规则：`AXM_hotbox_menu.hh` 约定 legacy scroll offset 被忽略、完整目录没有滚动/分页/人工 Back；C++ 按真实标签宽度和行高分列，下方不足将整组上移使列表底部贴可用区域下缘，不压缩四视图基准间距。目录不可能装入可用宽高时返回 `supported=false`，不会裁掉一半、缩小按钮或暗中启用滚动。因此“固定目录在受测常规窗口完整可用”和“任何尺寸及无限动态资产都完整显示”必须分开；后者没有物理上的无限保证。

动态边界继续透明保留：Maya Isolate Select → Bookmarks 的固定 Bookmark Current Objects 与 Options 已知，但非空动态成员来源未核实；未实现的 Maya 动态数据提供器保持灰占位。原生 Blender 节点资产、插件追加项和用户自定义内容使用真实 provider，其数量不属于固定 Maya GUI 目录完成数，不伪造动态数据或替用户改变测试状态。

## 最终统一候选回执

2026-10-11 的 Build07 已完成原生重新编译与144个资源校验；所选8组139项原生、40组354项纯测试、11项RNA通过。同一最终候选的18组回归全部通过（17 GUI事件 + 1 后台profiles），覆盖本文对应入口、取消/Undo、实际几何与事件状态。前文过程中的“待构建/待GUI”为历史切片状态；最终逐组证据和手工未测边界见[统一验收](../compatibility/2026-10-11-gui-completion-acceptance.md)及[GUI回执](../compatibility/2026-10-11-gui-event-tests.json)。自动事件不将人工条目标为已通过。
