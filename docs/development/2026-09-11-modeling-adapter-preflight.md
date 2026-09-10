# 常用选择适配预检（尚未实施）

日期：2026-09-11。为五小时批次后续候选准备；不是 API 或功能完成声明。
检查的是本机正版 Maya 2026 脚本中的菜单身份/命令路由和当前 Blender 源码，
没有复制 Maya 实现代码或算法到项目；完整行为仍需专题设计和实际测试。

## 已核实来源

本机 `C:/Program Files/Autodesk/Maya2026/scripts/startup/`：

- `buildSelectMenu.mel:40`：Select All；`:250` 附近 Select None；`:264` Invert Selection；
  `:285` GrowPolygonSelectionRegion；`:302` ShrinkPolygonSelectionRegion。
- `defaultRunTimeCommands.mel:1673-1697`：Select All 使用 Maya 选择上下文工具；Select None
  不只是简单清空组件选中，它还经过选择模式切换；Invert Selection 进入专门选择过程。
- `defaultRunTimeCommands.mel:10996-11017`：Grow/Shrink 分别使用多边形选择遍历。

本地 Blender：

- `source/blender/editors/object/object_select.cc:1127`：对象 select_all 明确依赖可见/可选对象，
  无改变时可能 CANCELLED、无可见对象时可能 PASS_THROUGH，不能一律伪造 FINISHED。
- `source/blender/editors/mesh/editmesh_select.cc:2637`：网格 select_all 接受 SELECT/DESELECT/INVERT，
  遍历唯一数据的编辑模式对象、刷新选择与依赖图，operator 标记 UNDO。
- 同文件 `:5017` / `:5066`：select_more/select_less 为编辑网格操作，`use_face_step` 默认 true；
  不应无说明地宣称与 Maya 的点/边/面遍历完全一致。
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
   多对象编辑、无变化/失败不进 Recent、确认/撤销、热盒退出后 W/E/R。
6. 此预检不改变计划顺序；先完成短/长设置菜单，时间不足就不启用这些候选。
