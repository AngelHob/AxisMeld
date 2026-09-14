# M2d 首片：已有组件选择的建模热盒

2026-09-14 用户批准按后续清单逐步修复和补齐能力，人工测试暂缓。本片在可见区域修复之后实施，复用 M3 已有语义命令，不重新实现挤出、倒角或切割算法。

## 入口与选择边界

- 新增 `context.modeling_hotbox`，默认 Shift+RMB，仅生成到 Mesh keymap。已有 `context.create_hotbox` 默认输入保持，生成范围明确为 Object Mode。二者上下文互斥，可以共享输入；旧创建配置 ID、禁用及改绑仍分别有效。
- 配置冲突仅对确切无序命令对 `{context.create_hotbox, context.modeling_hotbox}` 的实际不相交 keymap 放行；同一 Mesh/Object 范围、普通命令和全局 Window/Screen 冲突仍拒绝。重生成先移除旧 CREATE 在 Object/Mesh 两处的 AxisMeld 条目，再按新范围插入，保留共享 3D View 的原生 fallback。不要靠删除冲突检查启用新默认键。
- `EDIT_MESH` 中明确只开启一种 `mesh_select_mode`（点/边/面），且该域有可见可编辑组件选择时，选择对应根环。根环不由向低维 flush 的选中数量推断。
- 当前 editing set/组件选择优先，不拾取鼠标下其他对象，不改变 active/selection/mode 来打开热盒。多对象编辑继续使用 M3 的逐 Mesh 最小选择数量检查。
- Object、空组件选择、混合组件模式、非网格、不支持/不可编辑上下文原生回退。原生的空白创建仍由原入口处理。Object/预选事务、Ctrl+RMB 与 Ctrl+Shift+RMB 后续独立片实施。

## 方向及功能

三个独立根 `context.modeling_vertex`、`context.modeling_edge`、`context.modeling_face`，保留 Maya 2026 源菜单方位。节点 ID 独立；叶子引用已有 M3 semantic ID，标签表达当前 Blender 能力。

| 根/方向 | 已有能力或具体缺口 |
|---|---|
| Vertex N/NE/E | Merge 子菜单 / `mesh.average_vertices` / `mesh.bevel_vertices` |
| Vertex SE | Vertex Normals 子菜单 |
| Vertex S/SW | Maya Vertex Extrude / Delete Vertex 差异保留具体计划，不冒充已实现 |
| Vertex W/NW | `tool.mesh_knife` / `selection.paint`（明确 Circle Select） |
| Edge N/NE/E | Merge/Collapse 子菜单 / Spin CW/CCW 子菜单 / `mesh.bevel_edges` |
| Edge SE/S/SW | Sharpness 子菜单 / `mesh.extrude_edges` / `mesh.dissolve_edges`（明确 Dissolve） |
| Edge W/NW | `tool.mesh_knife` / `selection.paint` |
| Face N/NE | `mesh.merge_center`（明确 Blender 点合并） / `mesh.poke_faces` |
| Face E/SW | Face Boundary Bevel / Wedge 保留具体计划 |
| Face SE/S | Face Normals 子菜单 / `mesh.extrude_region` |
| Face W/NW | `tool.mesh_knife` / `selection.paint` |

Merge Vertex 子菜单 N/NE 使用 `mesh.merge_center`/`mesh.merge_distance`；Edge Merge N/E 使用 `mesh.merge_center`/`mesh.collapse`；Target Weld、边界配对焊接等保留已登记能力计划。Spin 子菜单 E/W 为 `mesh.edge_rotate_cw`/`mesh.edge_rotate_ccw`，专用 Flip Triangle 另留计划。Face N 同样对选中顶点求均值合并；Blender 按每个 Mesh 独立处理，Face 模式完成后清空组件选择并保留模式，不描述成“合并为一个面”。

Vertex Normals 子菜单：S=`display.vertex_normals`，NE=`normals.average_custom`，E=`normals.rotate`，SE=`normals.set_from_faces`。Face Normals：S=`display.face_normals`，E=`normals.reverse`，SE=`normals.conform_outside`，NE Reverse and Propagate 留计划。Sharpness：NE=`normals.soften_edges`，E=`normals.harden_by_angle`，SE=`normals.harden_edges`，S=`display.sharp_edges`，均沿用具体 Blender 名称与现有条件。

现有命令的 unavailable/poll 原样保留，例如点选择下未满足 faces 的 Set From Faces 不能被菜单强行启用。方向动作可用子环，参数与更深列表使用原生普通菜单。

## 事件与退出

持有与释放规则沿用已验证的 Shift+RMB 创建会话：触发鼠标松开只提交一次，中心/返回原始按下点/Esc/修饰键改变/失焦取消。非拥有鼠标松开不提交；补齐释放后无残留拦截。键盘改绑遵循已有 direct context 行为。

构建根环时不修改场景；提交真实叶子前关闭热盒，再由已登记原生操作或持久工具接收后续事件。组件选择域改变时取消旧会话，避免沿用错误根环；不修改通用 dispatcher Undo 属性。Recent 沿用当前真实成功、可重放策略。

## 验证与未覆盖范围

先以现版 Shift+RMB 在 Edit 已选组件时原生回退为 RED，再验证三根方向、真实 Poke/Merge/Bevel/Extrude 几何、一次 Undo、持续 Knife/Circle 后续输入、取消/释放、单/四视图和 Views 净间距。已有 Ctrl+E/Ctrl+B 与菜单同 ID，无新增重复绑定。配置测试要证明两个互斥入口可单独改绑/禁用且实际 keymap 不相交；其他碰撞仍失败。

Maya 来源：本机 scripts/others/ModelEdMenu.mel、contextPolyToolsMM.mel、contextPolyToolsVertexMM.mel、contextPolyToolsEdgeMM.mel、contextPolyToolsFaceMM.mel；只记录身份/方向/行为事实，不复制实现。Face Bevel 源逻辑先转换选区边界、Vertex Extrude 有宽度/分段、Delete Vertex 有拓扑清理，不能仅按名字接近来替换。

本片不宣称完整 M2 完成。UV、Global 物体缩放、完整雕刻/绑定/动画保持既定边界；人工测试仅追加清单，继续暂缓。

### Native 接口落实（2026-09-14）

Python `context_modeling_hotbox.modeling_root(context)` 负责入口选根；native 每次事件和提交前只读校验原有单域、可见可编辑组件仍存在，不进行 GPU 拾取、改 active/selection 或模式切换。C++ 使用 live BMesh 检查，避免 50 Hz 定时事件重建完整 Python 目录；其 editable/visible、逐 Mesh editing set、显式选择域必须与 Python 一致。

新增 `AXM_context_modeling.hh` 仅集中三个精确根/域与每根固定叶 command 白名单，native fixture 从真实 Python 菜单递归核对。现有通用 command allowlist（当前源码没有名为 `allowed_tool_command` 的函数）只限制所有热盒可调用的 semantic 集合，不能证明新 direct 根里的命令属于该根；旧 `tool_command_rearms` 只决定 QWER 是否重新待命，也不能作为 M2d 叶授权。MODEL 提交独立先关闭会话再分发，不能进入 QWER rearm 或创建/组件改选分支。
