# M2c 空白处多边形创建热盒对照

日期：2026-09-14。只读核对基线 `77844b7582e` 与本机原版 Maya 2026 安装脚本。本记录提取输入、菜单身份、方向和可观察配置，不复制 Autodesk 实现。未启动 Maya GUI；源配置事实与 AxisMeld 适配契约分别列出，不宣称已复现 Maya 的全部鼠标释放行为。

Maya 来源根目录：`C:/Program Files/Autodesk/Maya2026/scripts/`。

## 1. 实际入口与上下文来源

| 来源文件及行号 | 核实事实 | 本批处理 |
|---|---|---|
| `others/ModelEdMenu.mel:80-92` | 3D model panel 的 CommandPop 使用 button 3、Shift=true、Ctrl=false；打开时调用 `contextToolsMM`。这是面板鼠标 popup 配置，不是 `startup/hotkeySetup.mel` 的键盘 hotkey。 | Shift+RMB 为独立入口，不能直接沿用无修饰组件 RMB 的“任何修饰键都取消”判断。Alt/Ctrl/OSKey 组合继续保留原生路由。 |
| `others/ModelEdMenu.mel:66-77` | Ctrl+RMB 是独立的 ConvertPop。 | 留后续 M2d-P07，不被本片截获。 |
| `others/ModelEdMenu.mel:95-107` | Ctrl+Shift+RMB 是独立的 ToolOptionsPop。 | 留后续 M2d-P07，不被本片截获。 |
| `others/contextToolsMM.mel:30-58` | 先尝试 XGen、polygon、NURBS curve 上下文；都不处理时使用 polygon creation 默认菜单。 | 本片只覆盖无选择 Object 的空白创建，不扩展 XGen、曲线或其他模式。 |
| `others/contextPolyToolsMM.mel:186-191` | 优先当前 selection；只有 selection 为空才读取 preSelectHilite。 | 不直接套用 M2b 无修饰 RMB 的鼠标目标逻辑；不能用鼠标下对象覆盖已有选择。 |
| `others/contextPolyToolsMM.mel:193-271` | 分支优先顺序是 Vertex(mask 31)、Face(34，含 UV Shell 分支)、Edge(32)、UV(35)、Polygon Object(12)。 | Edit、已有选择和鼠标下有可拾取对象时保留原生 Shift+RMB。完整上下文留 M2d。 |
| `others/contextToolsMM.mel:53-58` | 没有适用的 polygon/NURBS 对象或组件菜单时，创建菜单作为默认分支。 | 本片的空白范围有意更窄：Object、无选择、鼠标下无原生可拾取目标。不能宣称与 Maya preSelectHilite/全部默认回退等价。 |

`startup/hotkeySetup.mel:409-416` 另核实 Windows Ctrl+Backspace/Delete 的 DeletePolyElements、Ctrl+Alt+Left/Right 的边旋转、Ctrl+E 的 Extrude、Ctrl+B 的 Bevel。这些键位属于后续组件操作片；本片七种基本体不凭空新增所谓 Maya 默认快捷键。

## 2. 本片方向与原生对应入口

来源均为 `others/contextPolyToolsDefaultMM.mel`。每个方向的紧接条目还有 Maya option box，本片不将 option box 冒充额外方向。

| 方向 | Maya 条目与来源行 | AxisMeld 原生对应 | 分类与差异 |
|---|---|---|---|
| N | Create Polygon Tool，56-70 | 暂无本片直接等价入口 | 本片 M2c-P01 不可执行占位，后续工作见 M2d-P01；不以 Blender Poly Build 直接冒充任意点绘制新多边形。 |
| NE | Polygon Disc，72-87 | `mesh.primitive_circle_add(fill_type='NGON')` | adapted；生成有面的圆盘，不生成空心圆线。Maya Disc 的 subdivisionMode/sides/subdivisions 不等价于 Blender circle 分段/填充。 |
| E | Polygon Sphere，89-103 | `mesh.primitive_uv_sphere_add` | adapted；使用 Blender UV Sphere 几何。名称中的 UV 是球体类型，不开启 UV 编辑专题。 |
| SE | Polygon Torus，105-119 | `mesh.primitive_torus_add` | adapted；保留 Blender 主/次半径与分段语义。此 Python operator 没有 enter_editmode RNA 属性，创建后模式沿用用户原生“Enter Edit Mode”偏好；本片不临时修改用户偏好或追加模式切换。 |
| S | Polygon Cube，121-135 | `mesh.primitive_cube_add` | adapted；保留 Blender 尺寸与对象语义。 |
| SW | Polygon Cone，137-151 | `mesh.primitive_cone_add` | adapted；保留 Blender radius1/radius2、深度和底盖语义。 |
| W | Polygon Cylinder，153-167 | `mesh.primitive_cylinder_add` | adapted；保留 Blender 半径、深度、分段和盖面语义。 |
| NW | Polygon Plane，169-183 | `mesh.primitive_plane_add` | adapted；默认原生四顶点平面，不声称 Maya subdivision/history 一致。 |

Disc 的进一步来源：`startup/defaultRunTimeCommands.mel:3573-3586` 将 CreatePolygonDisc 路由到 `performPolyDisc`；`others/performPolyDisc.mel:28-35,258-268` 记录其独立的 sides、subdivisionMode、subdivisions、radius 参数。这里仅记录参数差异，不移植其生成方式。

原生代码核对：

- `source/blender/editors/mesh/editmesh_add.cc:271-287` Plane、`:330` Cube、`:403-423` Circle、`:474-496` Cylinder、`:547-572` Cone、`:831-853` UV Sphere 均有原生 operator；这些创建操作使用 scene-editable poll，并登记原生 UNDO。
- Circle 的 `fill_type` 位于 `editmesh_add.cc:420`，默认没有填充；Disc 适配必须传入已核实的填充值，不能仅更改菜单标签。
- `scripts/startup/bl_operators/add_mesh_torus.py:115-119` 提供 Torus operator，并登记 REGISTER/UNDO/PRESET。
- 创建尺寸、网格拓扑、朝向和历史系统均沿用 Blender；本批不改全局坐标轴、不移植 Maya construction history，也不偷偷迁移用户 primitive 选项。

## 3. M2c 有界行为契约

主任务采用：Shift+RMB 仅在 **3D View WINDOW + Object + 无选择 + 鼠标下无原生可拾取目标** 时进入本片创建环。已有选择、Edit、鼠标悬停可拾取对象或其他模式保留原生 Shift+RMB，不能误创建基本体，也不能默默切换编辑模式。

同一个菜单 root 同时放入 Space → Create → Polygon Primitives。此显式目录入口允许 Object 中已有选择，不做鼠标目标拾取；创建新对象，不把基本体加入现有编辑网格。

稳定标识（按本片实现规格，不产生两个内容副本）：

- root：`context.create`；鼠标入口 command：`context.create_hotbox`。
- 叶 command：`mesh.create_disc`、`mesh.create_sphere`、`mesh.create_torus`、`mesh.create_cube`、`mesh.create_cone`、`mesh.create_cylinder`、`mesh.create_plane`。
- `common.create` 在基线中是占位；本批启用为原生普通目录，内含同一个 Polygon Primitives radial root。设置/后续选项继续使用普通菜单。

每次 Shift+RMB 只拥有一次划选：RMB 松开提交；中心、Esc、失焦或不再满足会话条件时取消。Shift 的释放及附加修饰键变化必须由 operator 明确处理，不能让已经松开的 RMB 留在释放屏障中。以上为 AxisMeld 的本片实现契约；Maya 源文件只证明 popup 触发配置，没有单独证明各种释放顺序的结果。

创建使用 Blender 原生操作及其撤销。不得给通用 dispatcher 整体加 UNDO。提交前关闭热盒并完成鼠标 ownership 清理，再创建并记录成功结果；取消、占位和不适用上下文不修改场景、不生成 Recent 或撤销项。默认创建位置/对齐应在实现计划明确，沿用 Blender 3D Cursor 创建语义时不得移动 3D Cursor 本身。六种 C++ primitive 显式保持 Object 模式；Torus 原生 Python operator 通过 `scripts/modules/bpy_extras/object_utils.py:153` 读取用户“Enter Edit Mode”偏好，作为公开差异保留。Torus 在该偏好开启时应进入 Edit，但仍须一次撤销完整移除新对象，不改变偏好本身。

验收至少包括七种实体几何、Disc 确实有面、每次一次撤销完整恢复、Space 已选择对象路径、错误上下文原生回退、Shift/RMB 两种释放顺序、Alt 导航、中心/占位取消、连续重开、单/四视图和非法配置拒绝。源代码核对不代表这些动态验证已经通过。

## 4. 已核实的后续上下文方向

下表是 Maya 2026 源配置，不代表本批将启用这些操作。已选上下文不得显示空白创建菜单。

| 上下文 | 根环方向 | 来源 |
|---|---|---|
| Polygon Object | N Merge Vertex Tool；NE Fill Holes；E Append to Polygon Tool；SE Soften/Harden 子菜单；S Extrude；SW Insert Edge Loop Tool；W Multi-Cut；NW Sculpt Tool | `contextPolyToolsObjectMM.mel:27-136` |
| Vertex | N Merge Vertices 子菜单；NE Average Vertices；E Chamfer Vertex；SE Vertex Normals 子菜单；S Extrude Vertex；SW Delete Vertex；W Multi-Cut；NW Paint Select Vertices | `contextPolyToolsVertexMM.mel:27-75,127-208` |
| Edge | N Merge/Collapse 子菜单；NE Flip/Spin 子菜单；E Bevel Edge；SE Soften/Harden 子菜单；S Extrude Edge；SW Delete Edge；W Multi-Cut；NW Paint Select Edges | `contextPolyToolsEdgeMM.mel:27-75,119-257` |
| Face | N Merge Faces to Center；NE Poke Face；E Bevel Face；SE Face Normals 子菜单；S Extrude Face；SW Wedge Face；W Multi-Cut；NW Paint Select Faces | `contextPolyToolsFaceMM.mel:27-174` |

上述 `contextPolyTools*.mel` 文件均位于本机 `scripts/others/`。Maya 的 Multi-Cut/部分工具菜单还受 modelingToolkit 是否加载影响；本表只说明注册方位，不把当前插件状态推定为已验证。

## 5. 后续 M2d 计划编号

| 编号 | 剩余内容 | 原生候选/依赖与验收目标 |
|---|---|---|
| M2d-P01 | Create Polygon Tool（本片 N 占位）及其设置 | 先核对 Blender Poly Build/绘制新面工作流的作用对象和确认方式；验收空白创建、多点绘制、结束/取消和一次撤销。没有对应能力前不启用同名假实现。 |
| M2d-P02 | 已选 Object/Vertex/Edge/Face 与 preSelectHilite 路由 | 当前选择优先；明确定义 Blender 多模式选择和多对象 Edit 语义，鼠标拾取不得覆盖已有选择。分别验证空选择、混合组件、非网格遮挡与取消。 |
| M2d-P03 | 组件直接建模动作及对应键位 | 候选包括 `mesh.poke`（`editmesh_tools.cc:5453`）、`mesh.bevel`（`editmesh_bevel.cc:1055`）、`mesh.merge`（`editmesh_tools.cc:3603`）、`mesh.vertices_smooth`（`:2833`）、原生挤出。逐项核对对象、参数、确认/取消、几何结果、一次撤销，再接 Ctrl+E/Ctrl+B 等已核实键位。Extrude Vertex、Delete Vertex、Face Bevel 不因名称相近直接映射到不同几何任务。 |
| M2d-P04 | 持续工具：Multi-Cut、Insert Edge Loop、Append、Target Weld | 候选工具在 `space_toolsystem_toolbar.py`，包括 `builtin.knife`、`builtin.poly_build`、原生 loop cut。先区分持久工具与一次模态；热盒关闭后再启动工具，验证后续操作、Esc、退出与撤销，不复制 Maya 工具实现。 |
| M2d-P05 | 法线、软硬边及相应方向子菜单 | 核对 Blender 锐边标记、面平滑及分裂法线数据的实际作用域；不可把 Soften/Harden 仅映射到任意 shading toggle。菜单设置用 native list，方向动作保留已核实方位。 |
| M2d-P06 | 默认创建菜单的 option box、列表尾项与创建偏好 | 本片只有七个基本体及 N 占位。Maya 默认菜单在 185 行以后还有列表尾项；后续独立核对并按能力归类，不伪造 Maya 默认键位、不混入 UV。 |
| M2d-P07 | Ctrl+RMB 转换、Ctrl+Shift+RMB 工具选项 | 入口证据见 ModelEdMenu；先核对 buildConvertMM/buildToolOptionsMM 内容和 release ownership，再接原生能力。M2a 的 UV/Vertex Face/Multi Component 原占位继续保留，不以本片完成宣称其完成。 |

UV 全专题、Sculpt/绑定/动画独立工作流以及 Global 对象缩放差异继续遵守已批准规格的后置范围。新增计划编号是剩余工作索引，不是本片已实现清单。
