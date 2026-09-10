# 常用选择适配预检（尚未实施）

日期：2026-09-11。为五小时批次后续候选准备；不是 API 或功能完成声明。
检查的是本机正版 Maya 2026 脚本中的菜单身份/命令路由和当前 Blender 源码，
没有复制 Maya 实现代码或算法到项目；完整行为仍需专题设计和实际测试。

## 已核实来源

本机 `C:/Program Files/Autodesk/Maya2026/scripts/startup/`：

- `buildSelectMenu.mel:40`：Select All；`:250` 附近 Select None；`:264` Invert Selection；
  `:285` GrowPolygonSelectionRegion；`:302` ShrinkPolygonSelectionRegion。
- `defaultRunTimeCommands.mel:1673-1697`：Select All 使用 Maya 选择上下文工具；Select None
  不只是简单清空组件选中，它先经过 component 再回到 object 模式；Invert Selection 进入专门选择过程。
- `invertSelection.mel:38` 起：空对象选择且无 hilite/UFE 选择时会报错，不等于全选；
  有 hilite 但无组件选择的分支也不能直接等同 Blender 对空集合执行 INVERT。
  `statusLine.mel:375` 起的模式路由进一步确认 Select None 的最终 object 模式。
- `defaultRunTimeCommands.mel:10996-11017`：Grow/Shrink 分别使用多边形选择遍历。
- 同文件 `:2039-2065`：Duplicate、Duplicate Special、Duplicate With Transform 是不同入口；
  普通 Duplicate 不应混同自动重复上次变换。`buildEditMenu.mel:567` / `:594` 也分别列出它们。

本地 Blender：

- `source/blender/editors/object/object_select.cc:1127`：对象 select_all 明确依赖可见/可选对象，
  无改变时可能 CANCELLED、无可见对象时可能 PASS_THROUGH，不能一律伪造 FINISHED。
- `source/blender/editors/mesh/editmesh_select.cc:2637`：网格 select_all 接受 SELECT/DESELECT/INVERT，
  遍历唯一数据的编辑模式对象、刷新选择与依赖图，operator 标记 UNDO；即使没有变化也返回 FINISHED。
- `source/blender/makesrna/intern/rna_mesh_api.cc:411` 与 `blenkernel/intern/mesh.cc:2235`：
  `Mesh.count_selected_items()` 在 Edit 模式读取 BMesh 缓存的点/边/面选中计数，可作为空组件选择
  门禁的候选，不需要为此遍历整个网格；其与选择模式、多对象编辑的组合仍须测试。
- 同文件 `:5017` / `:5066`：select_more/select_less 为编辑网格操作，`use_face_step` 默认 true；
  不应无说明地宣称与 Maya 的点/边/面遍历完全一致。
- `editmesh_utils.cc:417-460` 与 `bmesh/operators/bmo_utils.cc:280-410`：Face 模式且 Face Step=true
  时扩展/收缩依据共顶点的相邻面，包含对角面，不是仅共享边。选用 5×5 四边面片、中心面12
  扩展至 `{6,7,8,11,12,13,16,17,18}`、再收缩至 `{12}` 作为独立预期；3×3 面片一旦全部选中，
  边界行为不能用来证明同样的收缩结果。
- `bmesh/intern/bmesh_uvselect.cc:337`：上述工具经 `EDBM_uvselect_clear` 使 UV 选择同步有效标记
  失效，以网格选择作为后续同步来源；不是删除 UV 图层或清空 UV 坐标。测试应验证坐标不变，
  但不能承诺独立 UV 选择状态完全不受原生选择同步影响。
- `source/blender/editors/object/object_add.cc:5155`：object.duplicate 为 EXEC + UNDO，linked 默认 false；
  复制不是自动进入平移的同义词，多对象、共享数据/材质及撤销结果应单独验证。

## 实现前必须处理的项目内约束

1. `adapter.available()` 目前对所有 `selection.*` 要求有选中的可编辑网格；全选/反选不能
   直接套这个门禁，否则空选择或非网格对象场景无法使用。模式切换命令与集合选择命令须明确分组。
2. `commands.py`、`hotbox_runtime.SUPPORTED_COMMANDS`、`hotbox_catalog.command_policy()`、
   原生 `view3d_axismeld_hotbox_model.cc` 的 allowed_commands 需要同步；任何单层放宽不能构成完整接入。
3. Maya Select None 的模式路由与“保留 Blender 当前编辑模式并清空选择”有差异。若选择后者，
   必须明确 adapted 并加入集中验收待决，不悄悄承诺一一对等。
4. 默认 A 已用于 Frame All；不得为了 Select All 改动默认基线。新命令首批可无默认键位，
   仅菜单接入并允许个人覆盖，现有 baseline 未绑定命令集合测试需相应扩大而非删除断言。
5. 所有命令先做真实临时场景测试：Object/mesh Edit、无当前对象、隐藏/不可选、
   多对象编辑、原生返回状态与 Recent、确认/撤销、热盒退出后 W/E/R。
   保留原生 FINISHED/CANCELLED/PASS_THROUGH，不把失败伪装成功；当前 Recent 依据 FINISHED 记录，
   因此不能笼统承诺“无变化不进 Recent”。不为这批命令引入全几何前后对比或修改全局历史语义。
6. 此预检不改变计划顺序；先完成短/长设置菜单，时间不足就不启用这些候选。
7. `scripts/startup/bl_operators/axismeld.py` 的 command/dispatch 包装器只有 INTERNAL，
   明确由子原生 operator 负责 undo。不要为新建模命令给通用包装器整体加 UNDO，否则会
   同时改变现有导航/工具命令的撤销语义；应在真实菜单调用后验证一次撤销准确恢复场景。
   `wm_event_system.cc:1393-1401` 只对声明 UNDO 的 operator 增减嵌套深度，是该设计的源码依据，
   仍不能代替真实撤销测试。
8. `source/blender/axismeld/intern/hotbox_menu.cc:798-813` 的原生 close-before 规则只允许明确
   列出的即时视图命令保持热盒，其余 ID 默认先关闭；新增三个选择 ID 无需改这里的生产逻辑。
   原生 `RestrictedClosePolicyUsesLiteralCommandIdentities` 应追加三个准确 ID 作为契约测试，
   与 parser 的未知命令拒绝保持独立，不把“默认先关闭”误解成“允许执行任意命令”。

## 尚待后续切片明确的边界

- 若接入 Invert Selection，先明确空选择时遵循 Maya 的不可用/取消语义，还是显式采用 Blender
  的反选全集语义；不能只因名称相同就标为完全一致。
- Select None 涉及退出编辑模式、清空对象选择与撤销组合，暂不与简单集合选择命令打包实现。
- Grow/Shrink 可以先作为明确标注的 Blender 原生适配，不声称遍历算法与 Maya 等价。
- 上述均为源码预检，不代表 GUI 已验证或命令已启用。

## 后续最小验收矩阵（候选，不改变本批优先级）

| 场景 | 需要验证的真实结果 | 失败时不能采取的捷径 |
|---|---|---|
| Object，无活动对象但有可选对象 | Select All 仍可用；只选择可见且可选对象 | 复用组件切换的“先选中可编辑网格”门禁 |
| Object，混合 Mesh / Empty / Camera | 集合选择覆盖原生可选对象；组件切换仍仅对可编辑 Mesh 开放 | 为接入集合选择而整体放宽所有 selection 命令 |
| Object，全部已选中或空场景 | 保留原生 FINISHED / CANCELLED / PASS_THROUGH；历史结果与状态一致 | 包装器无条件返回 FINISHED |
| mesh Edit，多对象且含共享数据 | 按原生唯一数据语义选择，点/边/面模式与隐藏组件不被破坏 | 只改 active_object 的数据或为历史比较遍历全网格 |
| mesh Edit，空组件选择后 Invert | 先按明确的 adapted 决策测试，不猜测与 Maya 同名即等价 | 未说明地把空选择改成全选 |
| mesh Edit，Grow / Shrink | 独立构造已知拓扑，检查预期选中集合、边界和一次撤销 | 仅检查 operator 返回值或用结果生成预期值 |
| 真实热盒调用与个人配置 | 退出后 W/E/R 正常；新增命令默认无键位，个人绑定可保存/重载 | 改 A、F8–F11 默认值或给通用包装器全局加 UNDO |

四层登记的最小校验还应包含：新 ID 在 COMMANDS / runtime / catalog / 原生解析白名单
中的身份一致；输入测试继续逐项断言旧默认绑定和完整未绑定集合；JSON 中未知命令仍被拒绝。
