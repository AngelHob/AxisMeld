# 2026-10-11 上下文热盒入口与空选择组件拾取

## 依据与边界

本批落实当前 GUI/输入范围，不增加建模算法。依据本机 Maya 2026 的 `ModelEdMenu.mel:64-108`：Ctrl+RMB 调用 `buildConvertMM`，Shift+RMB 调用 `contextToolsMM`，Ctrl+Shift+RMB 调用 `buildToolOptionsMM`。`polyConvertMM.mel` 给出转换八方向、二级方向与七条伴随正文；`buildToolOptionsMM.mel` 按当前工具派发，不能借唤出切换工具。`contextPolyToolsMM.mel:185-192` 在空选区时读取 preSelectHilite。

目录只记录可观察到的名称、分组和方向，不分发 Autodesk 实现。现有转换命令、QWER 菜单和建模命令复用现有适配；缺失算法保留灰项，不用相似操作替代。

## 实施

1. 新增 Ctrl+RMB 转换目录，保留八组及嵌套方向、Options 和伴随菜单。Object/Edit Mesh 上可打开，执行仍遵守现有命令 poll；Object 模式不隐式进入 Edit 或全选。
2. 新增 Ctrl+Shift+RMB 当前工具入口。读取当前 QWER/选择工具根，复用同一目录；未知工具返回原生 fallback。直接鼠标入口由按下的鼠标键释放提交，修饰键提前变化取消，不进入 QWER 持键重唤模式。
3. Edit Mesh 单一选择域且空选区时，原生 EDBM 拾取仅捕获可见组件身份与拓扑，不在打开或悬停期间更改选择。空白、隐藏、不可编辑、多域和过期对象不提交。确认动作后以有界 Undo 事务选中捕获组件并执行已有操作；热盒取消无修改。
4. 预选仅向菜单能力计算提供预测组件数量与当前域；真实 Mesh 保持空选区。最终原生命令仍走真实 poll，不开放跨域或需要更多组件的动作。
5. To Face Path 复用现有 `selection.face_path`，保留“两张预选 Blender 面”的差异说明；能力门禁要求同一编辑 Mesh 至少两面、单独 Face 域。Contained Edges/Faces 与 Vertex/Face Perimeter 同样复用现有 M3 命令。
6. 非建模的 `3D View Tool: Paint Grease Pencil` 映射不参与建模鼠标冲突过滤，避免把绘画 Alt+LMB 笔划误删。

原生命令一经确认，继续遵守它已有的完成/取消语义。特别是原生 Extrude macro 可能在 Esc 取消位移时保留新几何，已有适配已说明该差异；Undo 恢复确认前状态。不能把热盒取消与后续原生模态取消混为一项测试。

## 原生操作取消的生命周期

独立的 Bevel/Crease 等原生 modal 真正返回 CANCELLED 时，需要额外撤销刚提交的目标选择。使用 WM 运行期 terminal callback，数据放在独立 map；不写 DNA、不保存进文件、不复制给 Redo。注册失败保持调用方所有权；完成/取消只回调一次，先移除 map 记录再调用，随后释放；没有可用上下文的 free 仅释放数据。

回调在原生 modal 完成/取消后、其 Undo push 前运行，handler 移除也走同一机制。确认完成不会复原用户操作。取消时按 Scene/Object/Mesh session UID、当前模式/选择域、完整顶点坐标/边面连接/隐藏状态签名重新查找 BMesh，只在选区仍恰好是提交目标时还原为空，并恢复原 active face。不会保留并回写原生取消之前的 BMesh/组件指针，也不会使用已失效区域。即时调用失败同样按 UID 重新取得当前 BMesh，校验值签名后恢复选区与 history。

该机制不会在 Extrude macro 报告 FINISHED 后猜测用户的取消意图或删除几何。原生命令自己的取消行为与热盒打开/悬停/Esc 的零修改承诺分别验收。

## 验证要求

- 目录与绑定纯测试先红后绿：方向/伴随行/灰项/当前工具不切换/键位只进入声明模式。
- 原生合同测试：新增白名单不接受伪造命令；转换伴随映射存在；直接会话取消/释放不影响 QWER 重唤。
- Blender RNA/事件测试：未确认时选区不变，Esc/空白释放取消，已确认命令只作用捕获组件，失效目标拒绝，Undo 还原；已有选区优先，多对象编辑保持边界。
- 编译与 GUI 由主任务统一集成。自动化结果与待人工测试分开记录。

## 本切片自动化证据

- `python tests/python/axismeld_context_entries_test.py`：新增入口缺失和 Grease Pencil map 被过滤的 RED 已复现；实现后 4 PASS。To Face Path 未绑定再单独 RED，绑定及说明后 GREEN。
- `axismeld_context_modeling_hotbox_test.py` 12 PASS、`axismeld_tool_hotbox_test.py` 6 PASS、`axismeld_input_test.py` 18 PASS、`axismeld_component_hotbox_test.py` 4 PASS（集成过程中公共目录增长的旧快照由主任务同步）。
- Blender background `tests/python/axismeld_preselection_blender.py`：6 PASS，含只读目标捕获/预测、过期与非空拒绝、失败恢复、原生 Poke 仅作用一面、Face Path 数量与单域门禁、预览 Poke 可用但跨域和多面动作仍禁用。Face Path 旧数量门禁曾 RED。
- 背景环境的原生 Poke 以 `undo=False` 执行，以免无 HUD 区域的后台原生注册路径崩溃；该测试不证明 GUI Undo。完整菜单 snapshot/真实点击/Undo 由事件套件证明。
- 新增 `wm_operator_completion` 两个 gtest：terminal once/不延续到 Redo、Cancel 与 contextless free 的释放语义。须由主任务编译后执行。
- `axismeld_context_entries_events.py` 已加入可运行脚本：空 Face 打开/悬停/Esc、Poke/一次 Undo；空 Edge 真正点 Bevel 和 Crease、原生移动/Esc、Crease 确认/一次 Undo；Ctrl+RMB 二级转换；Ctrl+Shift+RMB 当前 Move World 与反复打开。此记录写入时尚未在新 binary 执行，不记成人工通过。

## 集成事件定位：转换参数修正

候选 native `E72846D3FBC45B6913D3CD275C2910D604B2444229D3F28C5864BCF90106C9EE` 的实际事件已通过空 Face Poke/Undo、空 Edge Bevel/Crease 移动后 Esc、Crease 确认后一次 Undo；Ctrl+RMB 到 To Vertices 的断言发现旧适配参数问题。截图显示正确二级按钮，原生 `EDBM_selectmode_convert` 的向下转换在 `use_expand=True` 时反而排除与未选高域组件相邻的元素。

两个相邻四边面、一个左面/共享边/共享顶点作为输入的原生后台矩阵如下；数字是目标域选中数量：

| 转换 | use_expand=False | use_expand=True | 本次路由 |
| --- | ---: | ---: | --- |
| Face → Vertex | 4 | 2 | False |
| Face → Edge | 4 | 3 | False |
| Edge → Vertex | 2 | 0 | False |
| Edge → Face | 0 | 2 | True |
| Vertex → Edge | 0 | 3 | True |
| Vertex → Face | 0 | 2 | True |

仅三个基础转换命令的 native 参数按方向路由：向高域展开相邻组件，向低域保留来源组件包含的边/顶点；混合选择模式与原生一样使用最高活动域判断。仍调用同一个原生操作、沿用原生 Undo，Contained/Perimeter 与 Face Path 不变，无新选择算法。

`axismeld_preselection_blender.py` 新增六方向的实际原生结果和参数验收：旧实现三项向下转换 RED，修正后整个套件 7 PASS（六方向为一个参数化测试）；`axismeld_context_entries_test.py` 4 PASS。GUI 原来的四顶点断言保留，增加转换前后截图及 mode/count/modal 日志，等待主控同步 Python 资源后重跑。

## 最终统一候选回执

2026-10-11 的 Build07 已完成原生重新编译与144个资源校验；所选8组139项原生、40组354项纯测试、11项RNA通过。同一最终候选的18组回归全部通过（17 GUI事件 + 1 后台profiles），覆盖本文对应入口、取消/Undo、实际几何与事件状态。前文过程中的“待构建/待GUI”为历史切片状态；最终逐组证据和手工未测边界见[统一验收](../compatibility/2026-10-11-gui-completion-acceptance.md)及[GUI回执](../compatibility/2026-10-11-gui-event-tests.json)。自动事件不将人工条目标为已通过。
