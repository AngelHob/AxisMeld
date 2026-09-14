# M2d 首片：已有组件选择的 Shift+RMB

沿用 `2026-09-14-empty-create-hotbox.md` 的 M2d-P01 至 P07 编号，不重新赋义。本片接入 P02 的已有单域 Edit 选择路由、P03 的已有组件命令、P04 的 Knife/Circle 工具入口，以及 P05 的部分法线/锐边子环；不关闭整个 M2d。

## 来源与选择路由

本机 Maya 2026 `scripts/others/ModelEdMenu.mel:66-107` 将 Shift、Ctrl、Ctrl+Shift 的 RMB 菜单分开；`contextPolyToolsMM.mel:186-191` 先看当前选择，再看预选高亮。后续分支按 Vertex、Face、Edge、UV、Object 顺序选择菜单。本片只接已有显式单域选择，不推断 Blender flush 到低维的数量，也不接 GPU 预选事务。

Maya `performPolyExtrude.mel:39-52` 的通用挤出又使用 Face、Edge、Vertex 优先顺序。混合域不能简单套用某一个分支顺序，因此本片明确原生回退，保留混合域策略给后续设计。

## 已有能力的方向适配

| 根 | 方向 | 语义命令/子环 | 当前承诺 |
|---|---|---|---|
| Vertex | N / NE / E | Merge / `mesh.average_vertices` / `mesh.bevel_vertices` | Blender 顶点合并、平滑与倒角；最小选择条件沿用已有命令 |
| Edge | N / NE / E | Merge-Collapse / Rotate Edges / `mesh.bevel_edges` | 旋转边的 CW/CCW 是原生操作，专用三角形 Flip 仍单独缺失 |
| Edge | S / SW | `mesh.extrude_edges` / `mesh.dissolve_edges` | 原生边挤出与溶解；不承诺 Maya Delete Edge 的附带顶点清理 |
| Face | N / NE / S | `mesh.merge_center` / `mesh.poke_faces` / `mesh.extrude_region` | 中心顶点合并、Poke 和区域挤出；并非把多面合成一个保留面积的大面 |
| V/E/F | SE | Vertex Normals / Edge Sharpness / Face Normals | 显示设置与实际法线/锐边操作沿用 M3 条件，不强行启用不足选区 |
| V/E/F | W / NW | `tool.mesh_knife` / `selection.paint` | 激活原生 Knife / Circle Select 持久工具，后续输入由原生工具接收 |

Face Merge 依据：Maya `polyMergeToCenter.mel:68-93` 先转换顶点并求平均；Blender `editmesh_tools.cc:3440-3470,3482-3499` 按每个 Mesh 平均并合并。Blender 在 Edge/Face 域合并后清空选择并保留模式（同文件 3530-3533）。本片不提供 Maya symmetry/history，也不将两个 Mesh 合并成跨对象的一个点。

## 尚缺能力的唯一子编号

这些是原有 P03/P04/P05 的具体子项，不与 M3 的范围内能力计划重复计数，也不冒充可执行菜单。

| 唯一子ID | 父项 | 来源差异/下一步验收边界 |
|---|---|---|
| M2d-P03.VertexExtrude | 组件建模 | Maya `performPolyExtrude.mel:279-292` 含宽度、长度、分段；Blender `bmo_extrude.cc:234-265` 的顶点挤出生成连接的点/边，不是同一几何任务。需要独立算法与确认/取消/Undo 验收。 |
| M2d-P03.DeleteVertex | 组件建模 | Maya `polyDeleteVertex.mel:57-119` 的拓扑清理不能由普通 Blender 顶点删除直接替代；需定义邻接边/面的保留规则。 |
| M2d-P03.FaceBoundaryBevel | 组件建模 | Maya `performPolyBevel.mel:293-305` 对纯面选择先取边界；直接对所有选中边 Bevel 会包含内部边。需边界转换与完整撤销事务。 |
| M2d-P03.FlipTriangleEdge | 组件建模 | 当前 CW/CCW 复用原生旋转边；专用 Flip 仍缺只允许有效三角形共边的条件与结果检查。 |
| M2d-P03.WedgeFace | 组件建模 | 原生 Spin 的 Cursor/轴输入不等价于以所选边为枢轴的 Wedge，需要明确枢轴、角度与分段。 |
| M2d-P04.TargetWeld | 持续工具 | 与既有 `M3-P-TOOLS.MergeVertexTool` 关联；鼠标目标、边界配对、持续确认及取消尚需实现，不把Merge at Center冒充Target Weld。 |
| M2d-P05.ReversePropagate | 法线 | Reverse 与 Recalculate 已接入；Reverse and Propagate 的邻接传播事务仍缺失，不能只调用反转所选面。 |

P01 Create Polygon Tool、P02 Object/预选事务、P06 创建设置、P07 Ctrl 组合菜单仍按原编号继续。本片没有实现完整 UV 或 Paint 工作流；Global 物体缩放按既定决定无开发计划。

## 配置、输入与验收

CREATE 默认 Shift+RMB 仅生成到 Object Mode，MODEL 仅到 Mesh。个人配置可以分别改绑/禁用，只允许这两个确切命令共享输入；第三命令、共享 3D View、Window/Screen 冲突检查保留。迁移会先移除旧 CREATE 在两个域中的条目。

原生会话固定三个根；空/混合域、不可编辑/非网格使用原生回退，开始和结束不偷偷更换目标。持有鼠标与修饰键、选择域改变取消、热盒关闭后再启动原生操作均由开发测试和人工 D 项分别验收。

实施设计见 `docs/superpowers/specs/2026-09-14-m2d-edit-context-design.md`；开发证据见 `docs/compatibility/2026-09-14-visible-region-m2d-acceptance.md`；人工统一见同目录清单 D-01 至 D-14，当前暂缓。
