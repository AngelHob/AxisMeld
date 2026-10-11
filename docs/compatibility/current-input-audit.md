# 当前默认键位与交互对照（自动生成）

由 `tools/utils/axismeld_input_audit.py` 从当前源码生成；运行 `--check` 检查漂移。

这是静态生成配置与已存 Maya 参考的对照，不是完整 Maya 等价性或 GUI 验收。人工状态：**not_reassessed**；既有人工记录不变。

JSON 同名文件保留事件值、实际 keymap/区域/顺序/操作属性、来源、差异以及原生继承/移除项完整清单。个人配置不读取。

默认命令 58；含别名输入 60；生成 keymap 282；检查未改动的受保护 keymap 187。

| 输入 | 命令 | 生成到的 keymap | 已存参考身份/输入 | 参考比较 |
|---|---|---|---|---|
| Ctrl+RMB | context.conversion_hotbox | Mesh, Object Mode | buildConvertMM: Ctrl+RMB | same_event_definition |
| Ctrl+Shift+RMB | context.tool_hotbox | Mesh, Object Mode | buildToolOptionsMM: Ctrl+Shift+RMB | same_event_definition |
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
| Delete | edit.delete | Curve, Mesh, Object Mode | Delete: Delete | same_event_definition |
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
| Ctrl+Shift+Q | tool.mesh_poly_build | Mesh | QuadDrawTool: Ctrl+Shift+Q | same_event_definition |
| Ctrl+Shift+X | tool.mesh_knife | Mesh | MultiCutTool: Ctrl+Shift+X | same_event_definition |
| Shift+RMB | context.create_hotbox | Object Mode | contextToolsMM.empty: Shift+RMB | same_event_definition |
| Shift+RMB | context.modeling_hotbox | Mesh, Object Mode | contextToolsMM.selection: Shift+RMB | same_event_definition |
| Alt+D | selection.clear | Mesh, Object Mode | SelectNone: Alt+D | same_notation |
| Q | tool.select | Mesh, Object Mode | SelectToolOptions: Q | same_event_definition |
| W | transform.move | Mesh, Object Mode | TranslateToolWithSnapMarkingMenu: W | same_event_definition |
| E | transform.rotate | Mesh, Object Mode | RotateToolWithSnapMarkingMenu: E | same_event_definition |
| R | transform.scale | Mesh, Object Mode | ScaleToolWithSnapMarkingMenu: R | same_event_definition |
| RMB | context.component_hotbox | Mesh, Object Mode | buildObjectMenuItemsNow: RMB | same_event_definition |
| F8 | selection.toggle_component | Mesh, Object Mode | SelectToggleMode: F8 | same_notation |
| F9 | selection.vertex_mode | Mesh, Object Mode | SelectVertexMask: F9 | same_notation |
| F10 | selection.edge_mode | Mesh, Object Mode | SelectEdgeMask: F10 | same_notation |
| F11 | selection.face_mode | Mesh, Object Mode | SelectFacetMask: F11 | same_notation |
| Ctrl+Shift+A | selection.select_all | Mesh, Object Mode | SelectAll: Ctrl+Shift+A | same_notation |
| Shift+. | selection.grow | Mesh, Object Mode | GrowPolygonSelectionRegion: > (Shift+逗号/句号，US布局); GrowPolygonSelectionRegion: Shift+. | same_event_definition |
| Shift+, | selection.shrink | Mesh, Object Mode | ShrinkPolygonSelectionRegion: < (Shift+逗号/句号，US布局); ShrinkPolygonSelectionRegion: Shift+, | same_event_definition |
| F | view.focus_selected | 3D View | FitSelectedWithoutChildren: F | same_event_definition |
| A | view.frame_all | 3D View | FitAllInActivePanelMMenu: A | same_event_definition |
| Alt+LMB | view.orbit | 3D View | Tumble: Alt+LMB | same_event_definition |
| Alt+MMB | view.pan | 3D View | Track: Alt+MMB | same_event_definition |
| Alt+RMB | view.dolly | 3D View | Dolly: Alt+RMB | same_event_definition |
| 4 | view.wireframe | 3D View | WireframeDisplay: 4 | same_event_definition |
| 5 | view.shaded | 3D View | ShadedDisplay: 5 | same_event_definition |
| Space | hotbox.open | AxisMeld Hotbox | PopHotbox: Space | same_event_definition |

`same_event_definition` 仅表示与已核实的按键/修饰键/事件值相同；松键说明单独保留。`same_notation` 仅表示与已存输入文本相同；`review_notation_or_difference` 需要核对写法或差异；`prose_reference_review` 需要读取所指文档。均不等于功能通过。

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

## 原生变换中的持键输入

这些按键没有全局 PRESS 命令；仅由原生变换会话拥有，单独按键不修改场景设置。

| 持键 | 原生吸附 | 生效范围 |
|---|---|---|
| X | GRID | AxisMeld preset; Object or Mesh Edit; VIEW_3D WINDOW; Translate/Rotate/Scale; excluding camera-view, cursor and texture-space transforms |
| V | VERTEX | AxisMeld preset; Object or Mesh Edit; VIEW_3D WINDOW; Translate/Rotate/Scale; excluding camera-view, cursor and texture-space transforms |
| J | INCREMENT | AxisMeld preset; Object or Mesh Edit; VIEW_3D WINDOW; Translate/Rotate/Scale; excluding camera-view, cursor and texture-space transforms |

## 按住、松开与人工入口

- RMB context session; pointer target/selection/domain choose branch; commit or cancel on release: P/C/K/D/O groups.
- PRESS dispatches declared command; result/poll/Undo remain native or adapted; see M3 and input acceptance.
- QWER press selects tool; held key + repeated LMB opens marking menu; owned release/cancel: G-03/G-04/G-07.
- Alt + mouse press starts native navigation; drag/release handled by native modal operator.
- Tap toggles quad; hold opens main menu; center mouse dispatches Views; Space/owned release/cancel: G/MT groups.

[统一人工清单](2026-09-14-manual-test-ledger.md) · [当前 UI/输入阶段](../development/2026-09-29-ui-interaction-shortcuts.md)

## 预留、继承与待核实

预留裸键：D、X、C、V、J、F12、ONE、TWO、THREE。按逐项原因区分临时交互和缺失能力。

原生继承项标为 `native_inherited_not_maya_verified`；移除项保留原事件值，便于发现 PRESS/双击等差异。

- D / `deferred_capability`：Maya custom component and independent rotate/scale pivots need transient transform-center data. Blender Object Origins Only mutates object origin and cannot stand in for the Maya pivot tool. No equivalent pivot capability is present.
- X / `native_modal_input`：Existing Blender GRID snapping can be held temporarily. Maya sets grid on then off; restoration of prior Blender settings is an explicit adaptation.
- C / `deferred_capability`：Blender EDGE snapping follows mesh edges and is not Maya closest point on arbitrary parametric curves. No equivalent curve-target solver is implemented; do not relabel EDGE as curve snap.
- V / `native_modal_input`：Existing Blender VERTEX snapping can be held temporarily. Target and transform behavior remain native.
- J / `native_modal_input`：Maya toggles incremental snapping on both press/release; Shift+J additionally toggles relative mode. Blender increment settings and units differ.
- F12 / `deferred_capability`：UV selection domain and synchronized viewport UV editing are deferred; mapping F12 to face selection or opening UV Editor would not implement the Maya selection mask.
- ONE / `deferred_capability`：Maya base/cage/smooth mesh preview needs nondestructive per-object preview state; not equivalent to changing selection mode.
- TWO / `deferred_capability`：Cage plus smooth preview needs managed preview state. Silently adding/changing subdivision modifiers is outside the GUI-only scope.
- THREE / `deferred_capability`：Smooth preview and restoring previous state need a preview capability, not an arbitrary Subdivision modifier command.

[输入参考复核说明](../development/2026-10-11-input-reference-review.md)

- Same-map RMB native fallback and Shift+RMB create/model dispatch are intentional; verify runtime predicates.
- Shared Frames Space and mode/3D View overlaps need handler order and poll; equality is not proof of a bug.
- Alt+LMB DOUBLE_CLICK edgering_select is removed by current PRESS ownership; requires modal event verification.
- Measure X ruler_remove is removed by reserved-X ownership; DEL remains. Classify before changing.
- Reference same_notation/event_definition compares inputs only, not operation equivalence or release behavior.

## 生成一致性错误

无。仅表示当前绑定位置及受保护 keymap 检查通过。
