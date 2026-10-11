# 当前默认键位与交互对照（自动生成）

由 `tools/utils/axismeld_input_audit.py` 从当前源码生成；运行 `--check` 检查漂移。

这是静态生成配置与已存 Maya 参考的对照，不是完整 Maya 等价性或 GUI 验收。人工状态：**not_reassessed**；既有人工记录不变。

JSON 同名文件保留事件值、实际 keymap/区域/顺序/操作属性、来源、差异以及原生继承/移除项完整清单。个人配置不读取。

默认命令 56；含别名输入 58；生成 keymap 281；检查未改动的受保护 keymap 177。

| 输入 | 命令 | 生成到的 keymap | 已存参考身份/输入 | 参考比较 |
|---|---|---|---|---|
| Ctrl+Shift+I | selection.invert | Curve, Lattice, Mesh, Object Mode | InvertSelection: Ctrl+Shift+I | same_notation |
| Ctrl+F9 | selection.convert_vert | Mesh | ConvertSelectionToVertices: Ctrl+F9 | same_notation |
| Ctrl+F10 | selection.convert_edge | Mesh | ConvertSelectionToEdges: Ctrl+F10 | same_notation |
| Ctrl+F11 | selection.convert_face | Mesh | ConvertSelectionToFaces: Ctrl+F11 | same_notation |
| Z | edit.undo | Curve, Lattice, Mesh, Object Mode | Undo: Z, Ctrl+Z | same_notation |
| Shift+Z | edit.redo | Curve, Lattice, Mesh, Object Mode | Redo: Shift+Z, Ctrl+Y | same_notation |
| Ctrl+Y（别名） | edit.redo | Curve, Lattice, Mesh, Object Mode | Redo: Shift+Z, Ctrl+Y | same_notation |
| Ctrl+C | edit.copy_objects | Object Mode | CopySelected: Ctrl+C | same_notation |
| Ctrl+V | edit.paste_objects | Object Mode | PasteSelected: Ctrl+V | same_notation |
| Ctrl+X | edit.cut_objects | Object Mode | CutSelected: Ctrl+X | same_notation |
| Ctrl+G | edit.group | Object Mode | Group: Ctrl+G | same_notation |
| P | edit.parent | Object Mode | Parent: P | same_notation |
| Shift+P | edit.unparent | Object Mode | Unparent: Shift+P | same_notation |
| Ctrl+D | edit.duplicate | Curve, Mesh, Object Mode | Duplicate: Ctrl+D | same_notation |
| Ctrl+Shift+D | edit.duplicate_linked | Object Mode | DuplicateSpecial: Ctrl+Shift+D | same_notation |
| Shift+D | edit.duplicate_repeat_transform | Object Mode | DuplicateWithTransform: Shift+D | same_notation |
| Delete | edit.delete | Curve, Mesh, Object Mode | docs/maya-mapping/phase-1.md | prose_reference_review |
| Ctrl+H | display.hide_selected | Object Mode | HideSelectedObjects: Ctrl+H | same_notation |
| Alt+H | display.hide_unselected | Object Mode | HideUnselectedObjects: Alt+H | same_notation |
| Shift+H | display.show_selected | Object Mode | ShowSelectedObjects: Shift+H | same_notation |
| Ctrl+Shift+H | display.show_last_hidden | Object Mode | ShowLastHidden: Ctrl+Shift+H | same_notation |
| H | display.toggle_visibility | Object Mode | ToggleVisibilityAndKeepSelection: H | same_notation |
| Ctrl+Alt+H | display.show_components | Curve, Mesh | ShowAllPolyComponents: Ctrl+Alt+H | same_notation |
| Shift+F | display.frame_selected_all | Curve, Lattice, Mesh, Object Mode | FrameSelectedWithoutChildrenInAllViews: Shift+F; FrameSelectedInAllViews: Ctrl+Shift+F | same_notation |
| Ctrl+Shift+F（别名） | display.frame_selected_all | Curve, Lattice, Mesh, Object Mode | FrameSelectedWithoutChildrenInAllViews: Shift+F; FrameSelectedInAllViews: Ctrl+Shift+F | same_notation |
| Shift+A | display.frame_all_panes | Curve, Lattice, Mesh, Object Mode | FrameAllInAllViews: Shift+A | same_notation |
| F7 | selection.multi_component | Mesh | SelectMultiComponentMask: F7 | same_notation |
| Ctrl+T | transform.universal_tool | Curve, Lattice, Mesh, Object Mode | UniversalManip: Ctrl+T | same_notation |
| Alt+Shift+D | edit.bake_selected | Object Mode | DeleteHistory: Alt+Shift+D | same_notation |
| Ctrl+E | mesh.extrude_region | Mesh | PolyExtrude: Ctrl+E | same_notation |
| Ctrl+B | mesh.bevel_edges | Mesh | BevelPolygon: Ctrl+B | same_notation |
| Ctrl+Alt+Right | mesh.edge_rotate_cw | Mesh | PolySpinEdgeForward: Ctrl+Alt+Right | same_notation |
| Ctrl+Alt+Left | mesh.edge_rotate_ccw | Mesh | PolySpinEdgeBackward: Ctrl+Alt+Left | same_notation |
| Ctrl+Shift+Q | tool.mesh_poly_build | Mesh | docs/maya-mapping/phase-1.md | prose_reference_review |
| Ctrl+Shift+X | tool.mesh_knife | Mesh | docs/maya-mapping/phase-1.md | prose_reference_review |
| Shift+RMB | context.create_hotbox | Object Mode | docs/maya-mapping/2026-09-14-empty-create-hotbox.md | prose_reference_review |
| Shift+RMB | context.modeling_hotbox | Mesh, Object Mode | docs/maya-mapping/2026-09-14-empty-create-hotbox.md | prose_reference_review |
| Alt+D | selection.clear | Mesh, Object Mode | SelectNone: Alt+D | same_notation |
| Q | tool.select | Mesh, Object Mode | docs/maya-mapping/2026-09-11-tool-marking-menus.md | prose_reference_review |
| W | transform.move | Mesh, Object Mode | docs/maya-mapping/2026-09-11-tool-marking-menus.md | prose_reference_review |
| E | transform.rotate | Mesh, Object Mode | docs/maya-mapping/2026-09-11-tool-marking-menus.md | prose_reference_review |
| R | transform.scale | Mesh, Object Mode | docs/maya-mapping/2026-09-11-tool-marking-menus.md | prose_reference_review |
| RMB | context.component_hotbox | Mesh, Object Mode | docs/maya-mapping/2026-09-13-component-pointer-target.md | prose_reference_review |
| F8 | selection.toggle_component | Mesh, Object Mode | SelectToggleMode: F8 | same_notation |
| F9 | selection.vertex_mode | Mesh, Object Mode | SelectVertexMask: F9 | same_notation |
| F10 | selection.edge_mode | Mesh, Object Mode | SelectEdgeMask: F10 | same_notation |
| F11 | selection.face_mode | Mesh, Object Mode | SelectFacetMask: F11 | same_notation |
| Ctrl+Shift+A | selection.select_all | Mesh, Object Mode | SelectAll: Ctrl+Shift+A | same_notation |
| Shift+. | selection.grow | Mesh, Object Mode | GrowPolygonSelectionRegion: > (Shift+逗号/句号，US布局) | review_notation_or_difference |
| Shift+, | selection.shrink | Mesh, Object Mode | ShrinkPolygonSelectionRegion: < (Shift+逗号/句号，US布局) | review_notation_or_difference |
| F | view.focus_selected | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| A | view.frame_all | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| Alt+LMB | view.orbit | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| Alt+MMB | view.pan | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| Alt+RMB | view.dolly | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| 4 | view.wireframe | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| 5 | view.shaded | 3D View | docs/maya-mapping/phase-1.md | prose_reference_review |
| Space | hotbox.open | AxisMeld Hotbox | docs/maya-mapping/hotbox-maya2026.md | prose_reference_review |

`same_notation` 仅表示与已存输入文本相同；`review_notation_or_difference` 需要核对写法或差异；`prose_reference_review` 需要读取所指文档。均不等于功能通过。

## 直接注入的操纵器输入

这些输入由 AxisMeld 注入，不属于原生继承：

| 输入 | 操作 | keymap |
|---|---|---|
| LMB / CLICK | axismeld.axis_select | Generic Gizmo Maybe Drag |
| MMB / PRESS | axismeld.axis_drag | 3D View Tool: Move |
| ESC / PRESS | axismeld.axis_clear | 3D View Tool: Move |
| MMB / PRESS | axismeld.axis_drag | 3D View Tool: Rotate |
| ESC / PRESS | axismeld.axis_clear | 3D View Tool: Rotate |
| MMB / PRESS | axismeld.axis_drag | 3D View Tool: Scale |
| ESC / PRESS | axismeld.axis_clear | 3D View Tool: Scale |

## 按住、松开与人工入口

- PRESS dispatches declared command; result/poll/Undo remain native or adapted; see M3 and input acceptance.
- RMB context session; pointer target/selection/domain choose branch; commit or cancel on release: P/C/K/D/O groups.
- QWER press selects tool; held key + repeated LMB opens marking menu; owned release/cancel: G-03/G-04/G-07.
- Alt + mouse press starts native navigation; drag/release handled by native modal operator.
- Tap toggles quad; hold opens main menu; center mouse dispatches Views; Space/owned release/cancel: G/MT groups.

[统一人工清单](2026-09-14-manual-test-ledger.md) · [当前 UI/输入阶段](../development/2026-09-29-ui-interaction-shortcuts.md)

## 预留、继承与待核实

预留裸键：D、X、C、V、J、F12、ONE、TWO、THREE。缺失能力暂缓，不解除灰显。

原生继承项标为 `native_inherited_not_maya_verified`；移除项保留原事件值，便于发现 PRESS/双击等差异。

- Same-map RMB native fallback and Shift+RMB create/model dispatch are intentional; verify runtime predicates.
- Shared Frames Space and mode/3D View overlaps need handler order and poll; equality is not proof of a bug.
- Alt+LMB DOUBLE_CLICK edgering_select is removed by current PRESS ownership; requires modal event verification.
- Measure X ruler_remove is removed by reserved-X ownership; DEL remains. Classify before changing.
- Reference same_notation compares only stored input text, not operation equivalence or release behavior.

## 生成一致性错误

无。仅表示当前绑定位置及受保护 keymap 检查通过。
