# Maya RTC → SPECS 的18类多义绑定复核

2026-09-14。只读审核 `modeling_registry.SPECS`、原生操作及本机 Maya2026 MEL；没有改 registry/production，没有启动 GUI。目标是独立展示树的显式 preferred/disabled 表，不能用字典顺序选第一个适配。这里的 preferred 表示**明确的 Blender 适配**，不声称 Maya 历史、所有选项和选择范围完全相同；必须保留差异说明及现有 poll/mode/selection 限制。灰显只针对真实 Maya 主菜单这一入口，原 Blender 能力仍由明确扩展入口访问。

## 可直接采用的固定结果

建议8项 preferred、10项 disabled。未适配 Options 全部独立灰显；本表不能用于给 Options 自动复用正文。若父任务要启用需要补 guard 的项，应另做明确适配和测试，不能偷偷落回 first-match。

```python
PREFERRED = {
    'FillHole': 'mesh.fill_holes',
    'ReducePolygon': 'mesh.reduce_modifier',
    'SmoothPolygon': 'mesh.subdivision_modifier',
    'PolyExtrude': 'mesh.extrude_region',
    'PolyMerge': 'mesh.merge_distance',
    'ConnectComponents': 'mesh.connect_path',
    'AveragePolygonNormals': 'normals.average_custom',
    'PolygonNormalEditTool': 'normals.rotate',
}
DISABLED = {
    'ReorderRotationDialog': 'No rotation-order dialog adaptation',
    'SeparatePolygon': 'Selected-shell separation transaction not implemented',
    'PolyRemesh': 'Surface remesh is not equivalent to voxel-volume reconstruction',
    'CleanupPolygon': 'Complete cleanup selection/options not implemented',
    'TransferAttributes': 'Attribute-set and source/target transfer adaptation not implemented',
    'DetachComponent': 'Component-domain detach dispatch not implemented',
    'DeletePolyElements': 'Delete edge/vertex component semantics not implemented',
    'FlipTriangleEdge': 'Triangle-only edge flip eligibility not implemented',
    'SetVertexNormal': 'Absolute vertex-normal vector settings not implemented',
    'OpenCloseSurfaces': 'Surface direction/selected-boundary adaptation not implemented',
}
```

这些建议不改变 SINGLE unique RTC 的其他自动绑定规则；单一候选也仍需语义审查，不能以“无歧义”视作“已验证”。本轮只处理实际枚举到的18个多候选 RTC。

## 逐项理由、模式与来源

Maya文件路径默认相对 `C:/Program Files/Autodesk/Maya2026/scripts/`。`startup/defaultRunTimeCommands.mel` 下文简称 RTC 文件。

| RTC（候选数） | 建议 | 核实依据与不选择其他候选的原因 |
|---|---|---|
| ReorderRotationDialog (6) | disabled | RTC:2772–2776执行 `pythonRunTimeCommand reorder_rotation.ui 1`，是选择旋转顺序的UI。六个 `transform.rotation_order_*` 都 EXEC 立即改为固定Euler顺序，不能点“Reorder Rotation…”就静默变成XYZ。保留六项Blender扩展；将来需真正对话框，不能改成伪Maya submenu。 |
| SeparatePolygon (3) | disabled；将来补选壳事务 | RTC:8933→`performPolyShellSeparate`。`others/performPolyShellSeparate.mel:10–36`按选对象/面、`polyEvaluate -activeShells`设置 `polySeparate -sss`。当前三项全部仅EDIT_MESH。`mesh.separate_selection`可从连续壳切走任意选面；material按材质；loose虽最像壳分离，但 Blender `editmesh_tools.cc:4446–4500`遍历整张BMesh连通groups，非局部选壳，可能分离未选择壳。不能以名字像Loose优先而改变未选范围。 |
| FillHole (2) | `mesh.fill_holes`，EDIT_MESH/选边 | RTC:9323是 `polyPerformAction polyCloseBorder e 0`。已有 `mesh.fill_holes(sides=0)`针对边界孔，`mesh.fill`会三角填充选边，不是同一种补孔表面。保持现有原生poll，不自动切Object/全选。 |
| ReducePolygon (2) | `mesh.reduce_modifier`，OBJECT/active mesh | RTC:9148→performPolyReduce，核心为减面。既有 `_MODIFIERS['decimate']`为DECIMATE ratio .5，与Edit选面decimate同类但非破坏modifier更适合Mesh对象项，并保留参数编辑。仅active editable mesh是明确限制，不新增批量事务；Edit中灰显，不按mode任意换另一命令。提示“Blender Decimate modifier, 50%, active mesh; edit parameters in Modifiers”。 |
| SmoothPolygon (2) | `mesh.subdivision_modifier`，OBJECT/active mesh | RTC:9109→performPolySmooth。SUBSURF levels/render_levels1提供真正细分表面适配；`mesh.smooth_subdivide`是Edit Subdivide(number_cuts1,smoothness1)，不能把几何边插分+平滑误当同算法。保留既有modifier检查与可撤销性，Options不能借用主项重复加modifier。 |
| PolyRemesh (2) | disabled | RTC:9188→performPolyRemesh。`others/performPolyRemesh.mel:15–21,43–50`按最大边长、collapse threshold、tessellate borders处理表面。两候选都为Blender体素重建：object.voxel_remesh使用mesh voxel_size并破坏属性；modifier固定VOXEL/.1（`modeling_mesh_ops.py:107`）。体素重建可封闭/吞掉开放薄面，不是仅“历史不同”的差异。保留两个清楚命名的Voxel扩展及此前明确标注适配的专用Object工具入口；不要据旧coverage把新的原生Maya行直接赋成任何一种voxel算法。 |
| CleanupPolygon (6) | disabled | RTC:9228→performPolyCleanup；六候选明示“one explicit Blender cleanup operation; does not implement all Maya Cleanup checks”。删除loose、dissolve degenerate/limited、make planar、split nonplanar/concave均不等于完整Cleanup，也不能任意串联构成默认破坏清理。 |
| TransferAttributes (5) | disabled | RTC:9390→performTransferAttributes。候选五个单独data_type(CUSTOM_NORMAL/COLOR_VERTEX/COLOR_CORNER/SHARP_EDGE/CREASE)，均active source→selected destinations、无UV。正文按Maya设置传输哪些属性和源目标顺序尚无适配；不能默选custom normals，更不能把当前目标倒置风险藏在标签后。 |
| PolyExtrude (5) | `mesh.extrude_region`，EDIT_MESH/选顶点集合 | RTC:9910→performPolyExtrude0，源`performPolyExtrude.mel`处理顶点/边/面并读取keepFacesTogether。通用region extrude最少预设特定组件与方向，其他individual faces、along normals、edges、vertices是特化变体，留扩展。现有INVOKE宏保留；提示Blender region extrusion与局部参数不同；Esc可能仅取消位移，新几何须Undo撤销，不能假称原子取消。该项不是Smart Extrude，也不推断额外Faces设置。 |
| PolyMerge (5) | `mesh.merge_distance`，EDIT_MESH/至少两顶点 | RTC:9638→performPolyMerge；源文件:14说明合并选边界边或顶点。distance/threshold .0001是固定距离焊接适配；CURSOR/FIRST/LAST/COLLAPSE改变目标位置规则，不能作为默认Merge。Maya选边行为与阈值持久选项没有完整实现，说明固定Blender阈值，继续既有选择限制；Merge to Center仍独立对应其专用RTC。 |
| ConnectComponents (2) | `mesh.connect_path`，EDIT_MESH/合法顶点路径 | RTC:11490→polyConnectComponents。path为既有连接路径适配，具有`_connect_path`合法路径/selection history检查；pairs只在同一face内连接非相邻顶点，覆盖更窄。不能同时生成两个Maya Connect行，不能因选面/选边看起来相关就扩大现有requires/poll。保留说明“Blender vertex path connection; not all Maya component domains”。 |
| DetachComponent (2) | disabled；将来补组件分派 | RTC:9776→performDetachComponents；源`others/performDetachComponents.mel:9–35`顶点polySplitVertex、边polySplitEdge、面仅断开选区边界。`mesh.split`分离选中区域，不能在多个相邻选顶点时冒充逐顶点解接；`mesh.edge_split(type=EDGE)`只匹配边分支，却没有锁定实际mesh_select_mode。当前统一requires vertices/edges会在其他组件域也成立，不能静态偏选。 |
| DeletePolyElements (2) | disabled | RTC:9797→performPolyDeleteElements，源:23–55按顶点/边/面分派；边RTC:9809为 `polyDelEdge -cv true`，含关联顶点。`mesh.dissolve_edges`默认use_verts False，不同于Maya删除边和顶点；`mesh.delete_edgeloop`要求loop拓扑且会不同地溶解顶点。两者都不覆盖Maya当前分派，不能只按名称Delete Edge Loop选一个。 |
| FlipTriangleEdge (2) | disabled；有triangle guard后可CW | RTC:9747→polyFlipEdge。两个候选同为mesh.edge_rotate，仅use_ccw不同；两三角共享边只有一个另对角线，CW/CCW结果可等价。可是现有 `_edge_rotate`（modeling_mesh_ops.py:485–487）只要求某选边link_faces==2，允许quad/ngon。映射后会将“Maya Flip Triangle Edge”用于非三角拓扑；需所有将处理边均为两三角且有效的严格guard才能preferred CW，当前不能宣称具备。独立Spin Edge前后向RTC仍沿已有映射。 |
| AveragePolygonNormals (3) | `normals.average_custom`，EDIT_MESH/选顶点 | RTC:11892→performPolyAverageNormal，源:20–26、31–67记录prenormalize/postnormalize/空间tolerance/zero policy，不是face area或corner angle权重选择。CUSTOM_NORMAL平均已有法线是最接近的现有适配；AREA/CORNER是显式加权额外能力。说明Blender自定义法线平均、不支持Maya空间容差/锁定选项，Options独立灰显。 |
| PolygonNormalEditTool (2) | `normals.rotate`，EDIT_MESH/选顶点 | RTC:2662 `setToolTo $gPolyNormEdit`，Maya法线编辑工具。Rotate normals的交互方向编辑比Point to Target预设目标行为更接近，保留现有INVOKE及无Recent承诺。必须注明“一次Blender Rotate Normals交互；不保留Maya持久工具/锁定语义”。若产品该行被规定必须是持续工具而非此既有适配，应灰显；不得伪称已适配持久工具。 |
| SetVertexNormal (2) | disabled | RTC:11877→performPolySetNormal0，源`others/performPolySetNormal.mel:20–27`读取绝对XYZ法线值，默认(1,0,0)。Rotate是相对旋转、Point to Target是目标方向，均不是绝对向量设置。不能因为同一SPECS.maya同时填了NormalEditTool和SetVertexNormal，就让两个不同菜单项都打开同一Rotate。 |
| OpenCloseSurfaces (2) | disabled | RTC:8650→closeSurfaceToolScript4，源`others/closeSurfaceToolScript.mel:58–75`是选择/边界相关工具；候选只为CYCLIC_U或CYCLIC_V固定方向toggle。没有当前isoparm/边界方向判定或参数对话框，不应任意选U。保留清楚命名的U/V扩展；未来方向选择适配后再启用。 |

## 关键实现边界

- preferred 是固定ID选择，不覆盖 adapter.available 的 scene editable、mode、selection、native poll 和专用 COMMAND_POLLS。只有当前模式可执行才启用；不能让主菜单视觉对齐顺便开启未经审计Object→Edit或全选事务。
- 为适配原因保留足够可见说明，不把 Blender 参数/算法差异改成“Maya完整功能”。在无法通过准确说明排除范围风险时（Separate、Remesh、Detach），灰显优于隐式改更多几何。
- 明确Blender扩展应保持全部原命令ID及可访问性；本表不授权删除任何已实现能力或快捷键。属于Blender变体的备用实现仍可显式列出，不能藏在真实Maya父目录里重复造项。
- 真实Maya Options 必须是单独经过审计的参数交互。UI计数不能决定绑定；用RTC/源命令身份和相邻optionBox关系。尤其 Reduce/Smooth modifier正文再执行一次会叠加modifier，绝不可当Options。
- 验证建议：显式expected字典完全覆盖这18个歧义；确保disabled项不通过fallback重新获得command；preferred项的Options仍空command。Separate局部壳、Detach多相邻顶点、Delete边附带顶点、Flip两quad是将来新增guard必须先RED的实际反例。

## 证据文件

- `scripts/modules/axismeld/modeling_registry.py`、`modeling_schema.py`：SPECS及maya字段只是覆盖关系。
- `scripts/modules/axismeld/modeling_mesh.py:40–87,145–183,270–280`：候选IDs、调用参数、requires、适配说明。
- `scripts/modules/axismeld/modeling_shapes.py:24–50`：Surface U/V固定切换。
- `scripts/modules/axismeld/modeling_mesh_ops.py:104–146,485–525`：modifier真实预设、edge_rotate/Connect专用poll。
- `scripts/modules/axismeld/modeling_adapter.py:60–105,126–136`：选择、模式、派发不因新的展示树改变。
- Maya本机具体RTC及helper行号已逐行列在表格，未执行任何MEL正文。

## 补充独立审查：唯一候选不代表相同语义

2026-09-15。只读核对新 `maya_menu_catalog.py`、`hotbox_runtime.py`、实际构建的 catalog、相关 SPECS 与本机 Maya/Blender 操作源码。未运行 GUI、未执行菜单动作。本节不重复前述多义项和既知动态菜单边界。

`maya_menu_catalog.py` 的 `_binding()` 会在一个 RTC 只有一个 SPECS 候选时自动绑定。下列三项均已通过纯 Python 读取 `default_catalog()` 确认：Maya 标签下存在对应 command，声明为 enabled；当前上下文仍会经过 runtime/native poll，但该检查不能纠正动作语义。已有宽泛的 Blender 差异提示不足以解释这些操作变化。

| 严重度与真实入口 | 已确认绑定和可复现风险 | Maya 与 Blender 证据 | 最小处理 |
|---|---|---|---|
| **P1 · Deform → Edit Membership Tool** | `EditMembershipTool` 唯一绑定 `deform.vertex_group_assign`。在 Mesh Edit Mode、有可写活动顶点组和选中顶点时，点击工具入口会立即按当前组权重赋值；它不只是启动成员编辑工具。 | Maya `startup/defaultRunTimeCommands.mel:14355–14361` 执行 `setToolTo setEditContext`。`modeling_shapes.py:139–147` 声明 `object.vertex_group_assign`、`EDIT_MESH`、默认 EXEC；Blender `source/blender/editors/object/object_vgroup.cc:2781–2829` 直接调用 `vgroup_assign_verts(..., ts->vgroup_weight)`，并可能按设置归一化。 | 新 Maya 树将此 RTC 明确灰显、command 置空；保留原 `deform.vertex_group_assign` 于 Blender Extensions，使用其准确的 Assign Selected to Active Group 标签。 |
| **P1 · Curves → Duplicate Surface Curves** | `DuplicateCurve` 唯一绑定 `curve.duplicate`，只在 `EDIT_CURVE` 调用 `curve.duplicate_move`。在可编辑 Curve 中选中控制点时会复制这些点并进入移动，不能从 Surface 的边界/isoparm 提取曲线；实际 Surface 上反而没有该模式分支。 | Maya RTC 文件 `:7847–7853` 调用 `duplicateCurveToolScript 4`；`others/duplicateCurveToolScript.mel:67–80` 明确 Surface 提示及 `surfaceEdge` / `isoparm` 输入。`modeling_shapes.py:9–22` 声明 Curve Edit 模式和 Duplicate Control Points；Blender `editors/curve/editcurve.cc:6051–6102` 对所选控制点执行 `adduplicateflagNurb`，`curve_ops.cc:129–134` 将 Duplicate 与 Move 组成宏。 | 新 Maya 树禁用此 RTC，保留该真实目录行及独立 Options；原 `curve.duplicate` 继续以 Duplicate Control Points 留在 Blender Extensions。不能通过放宽到 Surface 模式冒充提取算法。 |
| **P2 · Select → Similar** | `SelectSimilar` 唯一绑定 `selection.similar_vert_normal`，始终调用 `mesh.select_similar(type='VERT_NORMAL')`。它把通用 Similar 入口固定成顶点法线过滤；没有随对象/组件类型选择相似规则，差异提示也没有声明此固定过滤条件。 | Maya RTC 文件 `:1710–1721` 调用 `performSelectSimilar 0/1`；`others/doSelectSimilar.mel:28–33` 将相似容差交给 modelingToolkit 的 `dR_selectSimilar`。`modeling_common.py:119–129` 将 RTC 仅挂在 `VERT_NORMAL` 候选，并只声明 `EDIT_MESH`。这与此前“通用约束入口误接单项过滤”的风险同类。 | 新 Maya 树禁用此 RTC，原 `selection.similar_vert_normal` 及其准确 Vertex Normal 标签继续在 Blender Extensions 中可用；不在本批新增通用 Similar 分派算法。 |

主任务已接受三项发现，并将通过 `UNAVAILABLE_BINDINGS` 只禁用新 Maya 树的这三个 RTC。旧 SPECS、原生操作、命令 ID 与扩展能力保留；对应 Options 继续保持独立灰显，不复用正文。实现及 RED→GREEN 测试由主任务和测试作者负责，本节不将方案接受写成已验证修复。

### Runtime、安全与隔离核对结论

- **未发现原始 Maya 命令执行路径。** Reference 中 RTC 名称仅用于匹配可信注册表；binder 输出既有固定 command ID，不执行快照中的 MEL/Python command 文本，也没有新增 eval/exec 或任意 operator 路径。`modeling_adapter.available()` 的 scene editable、模式、requires、专用 predicate 和 native poll 仍在派发前生效。
- **未发现状态白名单放宽。** 禁用状态仍使用生成的精确 ID→checkbox/radio 映射，要求 empty command、enabled=false、checked=false；既有 Creation Exit On Completion 的特例不因本批扩大。原生 header 与 Python 来自同一生成源。Maya 捕获的 enabled/checked 值没有被固化为当前状态。
- `hotbox_runtime._apply_runtime_capabilities()` 对真实 Maya 行按 authored indicator 决定样式，读取当前 Blender 状态；没有状态适配时灰显，普通 Maya 行移除 Blender 额外状态标记，启用行保留适配说明。此核对未发现未知状态假装成功的问题。
- 主树的 22 个菜单由 reference 决定层级；marking 根与未使用的 Blender 能力分别保留于 `internal.marking` / `internal.blender`。上述三项禁用后应不再进入 `used_commands`，从而恢复其准确命名的扩展入口；这属于需要回归断言的功能保留要求，不能只检查 Maya 主项变灰。
- **审查结论：修复前阻塞本轮语义验收。** 两项会以错误工具/提取标签启动写操作，一项会执行错误的固定选择过滤。建议采取上述三项局部禁用，不扩大实现范围；修复并完成针对性回归后，这轮只读审查没有另报 runtime 安全阻塞项。此结论不替代最终候选 GUI 验收。

### 实施回执（2026-09-15）

三项补充发现已落实至 `UNAVAILABLE_BINDINGS`：Maya 正文保留、禁用且无 command，独立 Options 同样不执行正文；对应原命令在 Blender Extensions 中保持可达。连同前述10项多义及选择约束、两种改名，本批共16个 RTC 显式禁用。`axismeld_maya_menu_binding_test.py` 的15项测试覆盖固定绑定、错误语义禁用、Options隔离、核心入口和原564个注册命令保留；最终22文件179项纯测试通过，证据为 `D:/source/AxisMeld-build/maya-hierarchy-python-green.log`。实机候选验收另记于最终交付文档，不以本回执替代。
