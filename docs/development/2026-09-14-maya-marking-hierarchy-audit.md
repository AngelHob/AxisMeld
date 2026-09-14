# Maya 2026 marking 菜单层级独立复核

日期：2026-09-14。范围是当前组件RMB、Create、Object/Vertex/Edge/Face建模、QWER及其子环/伴随列表、Views、Controls与Recent。本报告先独立审计；审计后获授权的局部修正与验证单列于“本轮已授权修正与验证”。来源为本机安装的 Maya2026 MEL 与英文 `resources/MayaStrings`，没有把旧“顶层已齐”说明当作证据。

## 结论与需修差异

当前不能宣称全部菜单树与Maya完全相同。多数静态伴随目录已保留，但存在以下可定位的差异；动态目录也尚未实现完整内容桥。下方完整当前目录展开可用于逐父节点审阅，附加JSON记录803个当前节点（含父ID、顺序、Options、indicator）及18份MEL的886条声明/父级事件。该JSON是静态证据索引，不是执行MEL后得到的运行时树；条件分支、`-rtc`运行时命令、回调和分隔合并仍必须按实际Maya树确认。

| 编号 | 真实Maya证据 | 当前差异 | 最小建议 |
|---|---|---|---|
| MH-01 | `others/translateMarkingMenuImpl.mel:116–146`：Snap下E Discrete Move、SE Vertex、SW Face Center；133–138 Relative Mode有checkbox但**没有radialPosition** | `tool_hotbox.py:124–127`把Relative Mode写成S方向，缺Snap的下方普通列表。不是仅标签差异 | 内容迁移到Snap伴随列表；是否保留旧S快捷行为需root统合，不能偷偷改变用户现有方向约定 |
| MH-02 | `others/contextPolyToolsMM.mel:118,132`；MayaStrings:11230/11234 为 Camera-Based Map / Normal-Based Map | Object→Mapping以及复用该树的Face→Mapping漏连字符 | 仅修两个声明标签，保留ID和灰显/Options |
| MH-03 | `startup/HotboxCenterMenu.mel:146`使用localizedPanelLabel("Side View")；localizedPanelLabel:81/95分别映射Side/Right，MayaStrings:27049/27040也分别存在 | 当前`hotbox_catalog.py:81`与`commands.py:94`均为Side View，核对通过。首次反馈误引用旧GUI的Right View文本，已撤回 | 不改源码；无本轮标签修复，保留方向、触发与Views几何标杆 |
| MH-04 | `HotboxCenterMenu.mel:170–175`和`HotboxControlsMenu.mel:129–134`的三个Style项均普通menuItem，无checkbox/radio | 当前`_style_menu`生成Setting，native `menu_radio_state`对style返回radio | 保留Setting的command/value与执行链，只让精确style命令的视觉状态返回None；无需将Setting伪装command。Transparency:229–244确有radio，必须保留 |
| MH-05 | `others/contextPolyToolsEdgeMM.mel:146–178`：modelingToolkit加载时Target Weld；未加载时NW Merge Edge Tool及Options | 当前只有加载分支的Target Weld，未表达插件缺席替代分支 | 标注默认Maya2026 toolkit条件，不能把分支并列成同一常驻菜单，也不凭静态源码增加错误方向 |
| MH-06 | DAG动态回调详见下一节 | DG/History/Paint/UV/Color/Metadata/SceneAssembly/材质多数用总括未适配占位，不能算完整动态层级已齐 | 保留诚实边界；runtime审计应记录当前对象/插件条件及实际子节点，不造节点名、材质或状态 |

不纳入本次误差修复的既有适配：Controls及Object Soften/Harden以native列表承载设置，Maya Controls本身使用径向位置；Blender方向/模式与Maya算法并不相同；Recent仅保留成功且可重放的最多10个语义命令。这些须明确写成AxisMeld适配，不得用“全树原样”概括。

## 逐族静态父子与参数复核

记号：`[]`独立Options；`|`分隔；C为checkbox、R为radio。原MEL重复相邻divider需要Maya运行时核对有效显示，不能靠源码数量推定可见高度。

| 菜单 | 来源与完整子层复核 | 结果/边界 |
|---|---|---|
| 组件RMB环 | dagMenuProc:991–1010等select-mask分支：Edge/Object/Vertex/UV/VertexFace/Multi/Face；UV→UV、UV Shell | 当前7向与UV子目录存在；本任务不变更触发/方向 |
| 组件伴随 | dagMenuProc:2618–2806；buildShaderMenus:501–557。对象名→选择组→Make Live→DG/Inputs/Outputs/Paint/Metadata/Actions/UVSets/ColorSets/TimeEditor→SceneAssembly→材质三组 | 常见Mesh的22个主行不能代表所有条件：container时还有Select Assembly/Container，SceneAssembly依类型注册，材质插件能增项 |
| Create | contextPolyToolsDefaultMM:53–452；主16项、Polygon Display All子10项/4分隔；workflow两checkbox及所有已有Options逐声明索引保留 | 主目录、PolygonDisplay子目录未发现新固定行漏项；Icosphere/Prism/Pyramid/Text为明确Blender适配，QuadDraw/SVG等仍灰显 |
| Object建模 | contextPolyToolsObjectMM:23–690；8向及5个Options；Soften/Harden子4项含angle Options；22主行、Mapping、Booleans、PolygonDisplay三个伴随子目录 | Mapping两标签见MH-02；Booleans并非仅4种，当前8种含Slice/HolePunch/CutOut/SplitEdges及各Options均保留 |
| Vertex建模 | contextPolyToolsVertexMM:23–388；Merge子3主项，Normals子4主项；下方9主项/3分隔、PolygonDisplay5主项/2分隔 | 静态固定标签及Options存在；Reorder Vertices依meshReorder插件，当前保留灰显解释；不能把插件分支状态当常驻可执行 |
| Edge建模 | contextPolyToolsEdgeMM:23–528；Merge/Collapse、Soften/Harden、Flip/Spin三子环；下方14主项/3分隔、PolygonDisplay6主项/3分隔 | fixed toolkit-loaded分支基本保留；无toolkit替代分支MH-05；TargetWeld Options在MEL用了W而main为S，此源码异常必须runtime判定，不据此改方向 |
| Face建模 | contextPolyToolsFaceMM:23–482；Normals子4主项；下方20主项/4分隔、Mapping复用contextPolyToolsMM、PolygonDisplay6主项/2分隔 | Mapping标签差异；其余固定子层/Options存在。Smart Extrude等为Blender适配，缺能力不能靠Maya标签宣布实现 |
| Q | selectMarkingMenuImpl:31–76；Q ring6动作加Symmetry/Select，主下方Automatic Camera-Based Selection C | 当前完整树包含共享Select/Symmetry及Select伴随；非所有选择动作都有Options |
| W | translateMarkingMenuImpl:19–219；主下方9主项/3分隔，SelectionConstraints、TransformConstraints、Snap、Axis→Custom及共享Select/SoftSelect/Symmetry | Snap Relative Mode落层错误MH-01；其余固定层逐声明索引核对 |
| E | rotateMarkingMenuImpl:19–163；Rotate Center四R，主下方11主项/3分隔；Custom、共同约束/Select/Symmetry | 主/子标签、C/R类型已声明；Custom不是附加参数对话框，不批量加Options |
| R | scaleMarkingMenuImpl:18–187；Scale Center三R，主下方10主项/3分隔；Axis→Custom及共同约束/Select/Symmetry | 同上，无新的固定子层漏项发现 |
| 共享Select | commonSelectOptionsPopup:31–124：Preselection/Nearest/Backfaces/Asset/Marquee/CameraBased/Clear/SoftSelect；SoftSelect→Object/SoftSelect/Volume/Surface/Global/Color Feedback；其后Automatic Camera-Based Selection属于**Select父层**普通下方项 | 当前8个Select companion与正确父层保留；SoftSelect六项全部C，不要凭互斥含义改R |
| 共享Symmetry | commonReflectionOptionsPopup:35–83：Symmetry/World/Object/Topology/X/Y/Z，均C | 当前7项存在；Topology受条件使能但不删除 |
| 共享Constraints | commonSelectionConstraintsOptionsPopup:13–55：Selection Constraints七R；Transform Constraints三R、分隔、Along Normals C | 当前两级结构及状态类型存在 |
| Views/Controls | HotboxCenterMenu:143–175；HotboxControlsMenu:103–256 | Side标签已核对通过；Style状态差异见MH-04；Controls下方Transparency五R/Style三普通项+分隔+RMB C/Window两C，当前后两结构存在 |
| Recent | HotboxRecentMenu:27–53：repeatLast -q -cnl全历史；label单行且最多256字符，普通项 | 当前有10条语义白名单上限，是刻意安全适配，不能宣称Maya全部历史等价；没有Maya固定子目录可伪造 |

## 动态目录：必须追到回调，不能以一个占位验收为完整

| 实际父目录 | 下一级和更深层来源 | 当前未覆盖的实际结构 |
|---|---|---|
| DG Traversal | createTraversalMenuItems:13–40→dgHistoryPopupFill | 目标Select、条件container Select、上游/下游链；深链More...及节点Options。当前仅DG nodes unavailable |
| Inputs/Outputs | dagMenuProc:1944–1992→historyPopupFill:248–262,35–89,367–377 | Select/Enable/Disable All固定三项+分隔+节点/Options、More...嵌套、All Inputs/Outputs。当前固定三项和末项保留，但无真实节点/More树 |
| Paint | dagMenuProc:2259–2298→createPaintingMenuItems/artAttrCreateMenuItems | 固定Paint Select/3D Paint后按paintable node类型生成更深属性目录，当前仅一个属性占位 |
| Metadata | dagMenuProc:1792–1842→createStreamList | Edit Metadata、Visualize Metadata C+Options、Select Stream及真实stream内容；当前前3项结构保留，流数据占位 |
| Actions | dagMenuProc:1845–1859 | Template/Untemplate/Unparent/BoundingBox四普通项，当前结构完整；前三仅捕获已选活动Object可安全复用 |
| UV Sets | dagMenuProc:2029–2118 | 有UV集时UV Linking/UV Set Editor/分隔；每个真实UV集C及关联投影项，集之间分隔。当前固定入口+总括占位，未实现每集/投影层 |
| Color Sets | dagMenuProc:2197–2257 | Color Set Editor、分隔、真实colorSet C、依集操作；当前仅固定入口+占位 |
| Time Editor | dagMenuProc:2153–2189 | Select Clip→Exclude Parent/Include Parent→Match Exact/All/Any/None；当前固定三级完整 |
| Scene Assembly | dagMenuProc:2550–2558→OutlinerEdRepMenu:109–247 | 无选择：按注册type Create及条件Options；非assembly选择：No Scene Assembly selected灰项；assembly：表示列表R、None/Unload、Create Representation及Options、List Assembly Edits；Delete Representation子目录源码存在但showDelete=0，不能算当前可见项。当前单占位未覆盖这些条件层 |
| Assign New/Favorite/Existing Material | buildShaderMenus:501–557及buildAssignFavouriteMenu/buildAssignShaderMenu回调 | New Material固定项+插件插入；Favorite/Existing按类型/场景/对象动态填，支持Options；有材质时还可能Disconnect及其他条件入口。当前保留父目录与未适配描述，不能说逐子节点已齐 |

## 建议的验证边界

先以独立Maya运行时树确定每个真实父节点的children顺序（包括Options/分隔/状态），再与本报告的当前父ID展开逐层比较。至少保存普通Cube、已选Cube、无选择指针Cube、toolkit加载/不加载、具有UV/Color/历史/材质/Assembly数据的场景条件。未覆盖的条件标未验证，不能把资源键合集或顶层数量作为全树通过。

对Style的最小实现建议：保持`kind=setting, command=style, value=rows/zones/center`不变，只在纯`menu_radio_state`对该精确命令返回None；因此measure/draw共享无radio列，而原apply_setting正常。加断言仅style无状态，transparency R与row.* C原样。父目录的内容修正不应更改Views方向或间隔。

以下目录表由当前纯catalog独立展开，不读取native布局。每行保留真实parent ID；序号是当前children声明顺序，带方向项的屏幕排序由方向决定，不能把列表序号误当方向。`[]`表示实际独立Options子节点，而不是正常cascade。

## 本轮已授权修正与验证

- MH-01已修：`tools.move.snap_menu`新增真实下方列表，叶ID `tools.move.snap_menu.relative`，无direction，disabled/emptycommand/checkbox/checked=false；旧S节点删除而成为缺席取消，E/SE/SW不变。`COMPANION_ROOTS`新增`tools.move.snap → tools.move.snap_menu`，tool companion共9个，该步骤总catalog根19个；后续完整Maya层级重建新增内部扩展根后为20根。后续获root授权补`AXM_context_modeling.hh`的精确伴随映射与disabled indicator；parser既有`companion_roots`顺序约束自动覆盖第19根，未修改布局实现。
- MH-02已修：Object Mapping的Camera-Based Map、Normal-Based Map保留ID与Options/灰显；Face复用同一声明因此同步，无额外算法。
- MH-03不是当前缺陷，已撤回首次误报；MH-04后续获授权实现：仅`menu_radio_state`对Setting的精确style命令返回None，command/value与enabled保留，Transparency及center映射radio和row checkbox不变；MH-05/06仍为明确条件/动态适配边界，不宣称已齐。
- 新增Snap层级测试先RED（旧S多余、新列表缺失）后GREEN；Mapping旧标签也先RED后GREEN。`D:/source/AxisMeld-build/marking-hierarchy-tool-green.log` 6项、model-green 5项、object-green 11项通过。未跑GUI。后续仅构建独立native测试：新增parser用例先RED（19/20），修header后parser20/20与layout81/81 GREEN，两CTest组1.30s；证据`snap-native-red.log`/`snap-native-green.log`/`snap-native-green-build.log`。本轮真实Maya runtime tree由另一作者独立采集，不将静态声明索引伪称GUI树。

Style独立原生验证：`style-plain-red.log`先80/81（Style状态组失败），修后`style-plain-green.log`为81/81，CTest1.04s；未改heading布局或GUI脚本。

## 当前完整目录展开（审计基线）

| 父ID | 当前标签 | 按当前顺序的全部直接子项 |
|---|---|---|
| `context.create` | Polygon Primitives | 1. Create Polygon Tool [] @N；2. Disc [] @NE；3. Sphere [] @E；4. Torus [] @SE；5. Cube [] @S；6. Cone [] @SW；7. Cylinder [] @W；8. Plane [] @NW |
| `context.components` | Active Mesh Components | 1. Edge @N；2. Vertex @W；3. Face @S；4. Object Mode @NE；5. UV→ @E；6. Vertex Face @SW；7. Multi @SE |
| `context.components.uv` | UV | 1. UV；2. UV Shell |
| `context.modeling_vertex` | Vertex Modeling | 1. Merge Vertices→ @N；2. Average Vertices @NE；3. Chamfer Vertex [] @E；4. Extrude Vertex [] @S；5. Delete Vertex @SW；6. Vertex Normals→ @SE；7. Multi-Cut [] @W；8. Paint Select Vertices @NW |
| `context.modeling_vertex.merge` | Merge Vertices | 1. Merge Vertices To Center @N；2. Merge Vertices [] @NE；3. Target Weld Tool [] @S |
| `context.modeling_vertex.normals` | Vertex Normals | 1. Toggle Vertex Normal Display @S；2. Average Normals [] @NE；3. Vertex Normal Edit Tool @E；4. Set Normals to Face [] @SE |
| `context.modeling_edge` | Edge Modeling | 1. Merge/Collapse Edges→ @N；2. Flip/Spin Edge→ @NE；3. Bevel Edge [] @E；4. Extrude Edge [] @S；5. Delete Edge @SW；6. Soften/Harden Edges→ @SE；7. Multi-Cut [] @W；8. Paint Select Edges @NW |
| `context.modeling_edge.merge` | Merge/Collapse Edges | 1. Merge Edges To Center @N；2. Collapse Edge @E；3. Target Weld Tool [] @S；4. Merge Border Edges [] @NE |
| `context.modeling_edge.spin` | Flip/Spin Edge | 1. Flip Triangle Edge @N；2. Spin Forward @E；3. Spin Backward @W |
| `context.modeling_edge.normals` | Soften/Harden Edges | 1. Soften Edge @NE；2. Soften/Harden [] @E；3. Harden Edge @SE；4. Toggle Soft Edge Display @S |
| `context.modeling_face` | Face Modeling | 1. Merge Faces To Center @N；2. Poke Face [] @NE；3. Bevel Face [] @E；4. Extrude Face [] @S；5. Wedge Face [] @SW；6. Face Normals→ @SE；7. Multi-Cut [] @W；8. Paint Select Faces @NW |
| `context.modeling_face.normals` | Face Normals | 1. Toggle Face Normal Display @S；2. Reverse Normals [] @E；3. Conform Normals @SE；4. Reverse Propagate @NE |
| `context.modeling_object` | Object Modeling | 1. Target Weld Tool [] @N；2. Fill Holes @NE；3. Append to Polygon Tool [] @E；4. Soften/Harden Edges→ @SE；5. Extrude @S；6. Insert Edge Loop Tool [] @SW；7. Multi-Cut [] @W；8. Sculpt Tool [] @NW |
| `context.modeling_object.normals` | Soften/Harden Edges | 1. Toggle Soft Edge Display；2. Harden Edge；3. Soften/Harden Edges []；4. Soften Edge |
| `tools.select` | Select Tool | 1. Symmetry→ @N；2. Select→ @S；3. Marquee @NW；4. Paint Select @W；5. Lasso @SW；6. Clear Selection @SE；7. Drag checkbox @NE；8. Camera-Based Selection checkbox @E |
| `tools.select.symmetry` | Symmetry | 1. Symmetry checkbox @N；2. World checkbox @W；3. Object checkbox @E；4. Topology checkbox @NE；5. X Axis checkbox @SW；6. Y Axis checkbox @S；7. Z Axis checkbox @SE |
| `tools.select.select` | Select | 1. Preselection Highlight checkbox @N；2. Highlight Nearest Component checkbox @NE；3. Highlight Backfaces checkbox @E；4. Asset Centric checkbox @SE；5. Marquee @NW；6. Camera-Based Selection checkbox @W；7. Clear Selection @SW；8. Soft Select→ @S |
| `tools.select.select.soft` | Soft Select | 1. Object checkbox @N；2. Soft Select checkbox @S；3. Volume checkbox @SW；4. Surface checkbox @W；5. Global checkbox @NW；6. Color Feedback checkbox @E |
| `tools.move` | Move Tool | 1. Symmetry→ @N；2. Select→ @S；3. World @W；4. Object @NW；5. Component @NE；6. Axis→ @SW；7. Snap→ @E；8. Keep Spacing checkbox @SE |
| `tools.move.symmetry` | Symmetry | 1. Symmetry checkbox @N；2. World checkbox @W；3. Object checkbox @E；4. Topology checkbox @NE；5. X Axis checkbox @SW；6. Y Axis checkbox @S；7. Z Axis checkbox @SE |
| `tools.move.select` | Select | 1. Preselection Highlight checkbox @N；2. Highlight Nearest Component checkbox @NE；3. Highlight Backfaces checkbox @E；4. Asset Centric checkbox @SE；5. Marquee @NW；6. Camera-Based Selection checkbox @W；7. Clear Selection @SW；8. Soft Select→ @S |
| `tools.move.select.soft` | Soft Select | 1. Object checkbox @N；2. Soft Select checkbox @S；3. Volume checkbox @SW；4. Surface checkbox @W；5. Global checkbox @NW；6. Color Feedback checkbox @E |
| `tools.move.axis` | Axis | 1. Normal checkbox @NW；2. Parent checkbox @W；3. Along Rotation Axis checkbox @NE；4. Live Object Axis checkbox @N；5. Custom→ @SW |
| `tools.move.axis.custom` | Custom | 1. Custom checkbox @E；2. Set to Component @W；3. Set To Point @SW；4. Set To Edge @S；5. Set To Face @SE；6. Set To Object @N；7. Reset @NW |
| `tools.move.snap` | Snap | 1. Discrete Move checkbox @E；2. Vertex checkbox @SE；3. Face Center checkbox @SW |
| `tools.rotate` | Rotate Tool | 1. Symmetry→ @N；2. Select→ @S；3. World @W；4. Object @NW；5. Component @NE；6. Custom→ @SW；7. Gimbal @E；8. Discrete Rotate checkbox @SE |
| `tools.rotate.symmetry` | Symmetry | 1. Symmetry checkbox @N；2. World checkbox @W；3. Object checkbox @E；4. Topology checkbox @NE；5. X Axis checkbox @SW；6. Y Axis checkbox @S；7. Z Axis checkbox @SE |
| `tools.rotate.select` | Select | 1. Preselection Highlight checkbox @N；2. Highlight Nearest Component checkbox @NE；3. Highlight Backfaces checkbox @E；4. Asset Centric checkbox @SE；5. Marquee @NW；6. Camera-Based Selection checkbox @W；7. Clear Selection @SW；8. Soft Select→ @S |
| `tools.rotate.select.soft` | Soft Select | 1. Object checkbox @N；2. Soft Select checkbox @S；3. Volume checkbox @SW；4. Surface checkbox @W；5. Global checkbox @NW；6. Color Feedback checkbox @E |
| `tools.rotate.axis` | Custom | 1. Custom checkbox @E；2. Set to Component @W；3. Set To Point @SW；4. Set To Edge @S；5. Set To Face @SE；6. Set To Object @N；7. Reset @NW |
| `tools.scale` | Scale Tool | 1. Symmetry→ @N；2. Select→ @S；3. World @W；4. Object @NW；5. Component @NE；6. Axis→ @SW；7. Snap Scale checkbox @E；8. Relative checkbox @SE |
| `tools.scale.symmetry` | Symmetry | 1. Symmetry checkbox @N；2. World checkbox @W；3. Object checkbox @E；4. Topology checkbox @NE；5. X Axis checkbox @SW；6. Y Axis checkbox @S；7. Z Axis checkbox @SE |
| `tools.scale.select` | Select | 1. Preselection Highlight checkbox @N；2. Highlight Nearest Component checkbox @NE；3. Highlight Backfaces checkbox @E；4. Asset Centric checkbox @SE；5. Marquee @NW；6. Camera-Based Selection checkbox @W；7. Clear Selection @SW；8. Soft Select→ @S |
| `tools.scale.select.soft` | Soft Select | 1. Object checkbox @N；2. Soft Select checkbox @S；3. Volume checkbox @SW；4. Surface checkbox @W；5. Global checkbox @NW；6. Color Feedback checkbox @E |
| `tools.scale.axis` | Axis | 1. Normal checkbox @NW；2. Parent checkbox @W；3. Along Rotation Axis checkbox @NE；4. Live Object Axis checkbox @N；5. Custom→ @SW |
| `tools.scale.axis.custom` | Custom | 1. Custom checkbox @E；2. Set to Component @W；3. Set To Point @SW；4. Set To Edge @S；5. Set To Face @SE；6. Set To Object @N；7. Reset @NW |
| `center.recent` | Recent Commands |  |
| `views` | AxisMeld | 1. Perspective View；2. Side View；3. Bottom View；4. Front View；5. Back View；6. Top View；7. Left View；8. Hotbox Style→ |
| `views.style` | Hotbox Style | 1. Zones and Menu Rows；2. Zones Only；3. Center Zone Only |
| `center.controls` | Hotbox Controls | 1. Show Modeling→；2. Show Rigging→；3. Show Animation→；4. Show FX→；5. Show All；6. Hide All；7. Show Rendering→；8. Show Common Menus；9. Show Pane Specific Menus；10. Show Custom Menu Set Menus checkbox；11. Set Transparency→；12. Hotbox Style→；13. 分隔；14. Window Options→；15. 分隔；16. AxisMeld Center Mouse Buttons→ |
| `center.controls.modeling` | Show Modeling | 1. Modeling Only；2. Show/Hide Modeling |
| `center.controls.rigging` | Show Rigging | 1. Rigging Only；2. Show/Hide Rigging checkbox |
| `center.controls.animation` | Show Animation | 1. Animation Only；2. Show/Hide Animation checkbox |
| `center.controls.fx` | Show FX | 1. FX Only；2. Show/Hide FX checkbox |
| `center.controls.rendering` | Show Rendering | 1. Rendering Only；2. Show/Hide Rendering checkbox |
| `center.controls.transparency` | Set Transparency | 1. 0%；2. 25%；3. 50%；4. 75%；5. 100% |
| `center.controls.style` | Hotbox Style | 1. Zones and Menu Rows；2. Zones Only；3. Center Zone Only；4. 分隔；5. Center Zone RMB Popups checkbox |
| `center.controls.window` | Window Options | 1. Show Main Menubar checkbox；2. Show Pane Menubars checkbox |
| `center.controls.buttons` | AxisMeld Center Mouse Buttons | 1. Left Mouse Button→；2. Middle Mouse Button→；3. Right Mouse Button→ |
| `center.controls.buttons.leftmouse` | Left Mouse Button | 1. Disabled；2. AxisMeld Views；3. Recent Commands；4. Hotbox Controls；5. Common；6. Select；7. Modify；8. Current Pane；9. Pane View；10. Pane Shading；11. Panels；12. Panel Views；13. Modeling |
| `center.controls.buttons.middlemouse` | Middle Mouse Button | 1. Disabled；2. AxisMeld Views；3. Recent Commands；4. Hotbox Controls；5. Common；6. Select；7. Modify；8. Current Pane；9. Pane View；10. Pane Shading；11. Panels；12. Panel Views；13. Modeling |
| `center.controls.buttons.rightmouse` | Right Mouse Button | 1. Disabled；2. AxisMeld Views；3. Recent Commands；4. Hotbox Controls；5. Common；6. Select；7. Modify；8. Current Pane；9. Pane View；10. Pane Shading；11. Panels；12. Panel Views；13. Modeling |
| `context.modeling_object_menu` | Object Modeling | 1. Offset Edge Loop Tool []；2. Smooth []；3. Unsmooth []；4. Subdiv Proxy []；5. Crease Tool []；6. 分隔；7. Project Curve on mesh []；8. Split mesh with projected curve []；9. 分隔；10. Mirror []；11. Mapping→；12. 分隔；13. Triangulate；14. Quadrangulate []；15. Reduce []；16. Remesh []；17. Retopologize []；18. 分隔；19. Transfer Vertex Order；20. 分隔；21. Separate；22. Combine []；23. Booleans→；24. 分隔；25. Cleanup...；26. Connect Tool []；27. Quad Draw Tool []；28. 分隔；29. Polygon Display→ |
| `context.modeling_object_menu.mapping` | Mapping | 1. Planar Map X；2. Planar Map Y；3. Planar Map Z；4. Planar Map []；5. 分隔；6. Cylindrical Map []；7. Spherical Map []；8. 分隔；9. Automatic Map []；10. Camera-Based Map []；11. Normal-Based Map [] |
| `context.modeling_object_menu.booleans` | Booleans | 1. Union []；2. Difference (A - B) []；3. Difference B - A []；4. Intersection []；5. Slice []；6. Hole Punch []；7. Cut Out []；8. Split Edges [] |
| `context.modeling_object_menu.polygon_display` | Polygon Display | 1. Backface Culling；2. 分隔；3. Border Edges；4. Texture Border Edges；5. 分隔；6. Face Normals；7. Vertex Normals；8. 分隔；9. Face Centers；10. Hidden Triangles；11. Vertices；12. 分隔；13. Reset Polygon Display |
| `context.create_menu` | Polygon Primitives | 1. Platonic Solid []；2. Pyramid []；3. Prism []；4. Pipe []；5. Helix []；6. Gear []；7. Soccer Ball []；8. 分隔；9. Super Ellipse []；10. Spherical Harmonics []；11. Ultra Shape []；12. Type；13. SVG；14. Quad Draw Tool []；15. 分隔；16. Interactive Creation checkbox；17. Exit On Completion checkbox；18. 分隔；19. Polygon Display All→ |
| `context.create_menu.polygon_display_all` | Polygon Display All | 1. Backface Culling on for All Polys；2. Backface Culling off for All Polys；3. 分隔；4. Toggle All Geometry Border Edges；5. Toggle All Texture Border Edges；6. 分隔；7. Toggle All Face Normals；8. Toggle All Vertex Normals；9. 分隔；10. Toggle All Face Centers；11. Toggle All Hidden Triangles；12. Toggle All Vertices；13. 分隔；14. Reset Display for All Polys |
| `context.component_menu` | Object Context | 1. Object...；2. 分隔；3. Select；4. Select All；5. Deselect All；6. Select Hierarchy；7. Invert Selection；8. 分隔；9. Select Similar []；10. 分隔；11. Make Live；12. 分隔；13. DG Traversal→；14. Inputs→；15. Outputs→；16. Paint→；17. Metadata→；18. Actions→；19. UV Sets→；20. Color Sets→；21. Time Editor→；22. 分隔；23. Scene Assembly→；24. 分隔；25. Material Attributes...；26. 分隔；27. Assign New Material→；28. Assign Favorite Material→；29. Assign Existing Material→ |
| `context.component_menu.dg_traversal` | DG Traversal | 1. DG nodes unavailable |
| `context.component_menu.inputs` | Inputs | 1. Select All Inputs；2. Enable All Inputs；3. Disable All Inputs；4. 分隔；5. History nodes unavailable；6. All Inputs... |
| `context.component_menu.outputs` | Outputs | 1. Select All Outputs；2. Enable All Outputs；3. Disable All Outputs；4. 分隔；5. History nodes unavailable；6. All Outputs... |
| `context.component_menu.paint` | Paint | 1. Paint Select；2. 3D Paint；3. Paintable attributes unavailable |
| `context.component_menu.metadata` | Metadata | 1. Edit Metadata...；2. Visualize Metadata [] checkbox；3. Select Stream→ |
| `context.component_menu.metadata.stream` | Select Stream | 1. Metadata streams unavailable |
| `context.component_menu.actions` | Actions | 1. Template；2. Untemplate；3. Unparent；4. Bounding Box |
| `context.component_menu.uv_sets` | UV Sets | 1. UV Linking...；2. UV Set Editor；3. 分隔；4. UV sets unavailable |
| `context.component_menu.color_sets` | Color Sets | 1. Color Set Editor；2. 分隔；3. Color sets unavailable |
| `context.component_menu.time_editor` | Time Editor | 1. Select Clip→ |
| `context.component_menu.time_editor.select_clip` | Select Clip | 1. Exclude Parent→；2. Include Parent→ |
| `context.component_menu.time_editor.select_clip.exclude_parent` | Exclude Parent | 1. Match Exact；2. Match All；3. Match Any；4. Match None |
| `context.component_menu.time_editor.select_clip.include_parent` | Include Parent | 1. Match Exact；2. Match All；3. Match Any；4. Match None |
| `context.component_menu.scene_assembly` | Scene Assembly | 1. Scene Assembly unavailable |
| `context.component_menu.assign_new_material` | Assign New Material | 1. New Material...；2. Material provider entries unavailable |
| `context.component_menu.assign_favorite_material` | Assign Favorite Material | 1. Material favorites unavailable |
| `context.component_menu.assign_existing_material` | Assign Existing Material | 1. Scene materials unavailable |
| `context.modeling_vertex_menu` | Vertex Modeling | 1. Crease Tool []；2. Connect Components []；3. Detach Components；4. Transform Component []；5. Connect Tool []；6. 分隔；7. Circularize Vertices []；8. Reorder Vertices；9. 分隔；10. Apply Color []；11. 分隔；12. Polygon Display→ |
| `context.modeling_vertex_menu.polygon_display` | Polygon Display | 1. Toggle Backface Culling；2. 分隔；3. Toggle Vertices；4. Toggle Vertex Normals；5. Toggle Vertex Numbers；6. 分隔；7. Reset Polygon Display |
| `context.modeling_edge_menu` | Edge Modeling | 1. Crease Tool []；2. Offset Edge Loop Tool []；3. Insert Edge Loop Tool []；4. Slide Edge Tool []；5. Circularize Components []；6. Edit Edge Flow []；7. 分隔；8. Add Divisions To Edge []；9. Bridge []；10. Fill Hole；11. 分隔；12. Connect Components []；13. Detach Components；14. Transform Component []；15. Connect Tool []；16. 分隔；17. Polygon Display→ |
| `context.modeling_edge_menu.polygon_display` | Polygon Display | 1. Toggle Backface Culling；2. 分隔；3. Toggle Border Edges；4. Toggle Texture Border Edges；5. 分隔；6. Toggle Hidden Triangle Edges；7. Toggle Soft Edge Display；8. 分隔；9. Reset Polygon Display |
| `context.modeling_face_menu` | Face Modeling | 1. 分隔；2. Smart Extrude；3. Smooth Faces []；4. Assign Invisible Faces []；5. Add Divisions To Faces []；6. Circularize Components []；7. Connect Components []；8. Detach Components；9. Triangulate Faces；10. Quadrangulate Faces []；11. Reduce Faces []；12. Remesh []；13. Bridge Faces []；14. 分隔；15. Mirror []；16. Extract Faces []；17. Duplicate Face []；18. Transform Component []；19. Connect Tool []；20. Target Weld Tool []；21. 分隔；22. Mapping→；23. 分隔；24. Polygon Display→ |
| `context.modeling_face_menu.mapping` | Mapping | 1. Planar Map X；2. Planar Map Y；3. Planar Map Z；4. Planar Map []；5. 分隔；6. Cylindrical Map []；7. Spherical Map []；8. 分隔；9. Automatic Map []；10. Camera-Based Map []；11. Normal-Based Map [] |
| `context.modeling_face_menu.polygon_display` | Polygon Display | 1. Toggle Backface Culling；2. 分隔；3. Toggle Face Centers；4. Toggle Face Normals；5. Toggle Face Numbers；6. Toggle Hidden Triangles；7. 分隔；8. Reset Polygon Display |
| `tools.select_menu` | Select Tool Menu | 1. Automatic Camera-Based Selection checkbox |
| `tools.move_menu` | Move Tool Menu | 1. Selection Constraints→；2. Transform Constraints→；3. 分隔；4. Shift Extrude checkbox；5. Shift Duplicate checkbox；6. 分隔；7. Preserve UVs checkbox；8. Preserve Children checkbox；9. Tweak Mode checkbox；10. Update Triad checkbox；11. 分隔；12. Move Options |
| `tools.move_menu.selection_constraints` | Selection Constraints | 1. Off radio；2. Angle radio；3. Border radio；4. Edge Loop radio；5. Edge Ring radio；6. Shell radio；7. UV Edge Loop radio |
| `tools.move_menu.transform_constraints` | Transform Constraints | 1. Off radio；2. Edge Slide radio；3. Surface Slide radio；4. 分隔；5. Along Normals checkbox |
| `tools.rotate_menu` | Rotate Tool Menu | 1. Selection Constraints→；2. Transform Constraints→；3. 分隔；4. Shift Extrude checkbox；5. Shift Duplicate checkbox；6. 分隔；7. Rotate Center→；8. Free Rotate checkbox；9. Preserve UVs checkbox；10. Preserve Children checkbox；11. Tweak Mode checkbox；12. Relative checkbox；13. 分隔；14. Rotate Options |
| `tools.rotate_menu.selection_constraints` | Selection Constraints | 1. Off radio；2. Angle radio；3. Border radio；4. Edge Loop radio；5. Edge Ring radio；6. Shell radio；7. UV Edge Loop radio |
| `tools.rotate_menu.transform_constraints` | Transform Constraints | 1. Off radio；2. Edge Slide radio；3. Surface Slide radio；4. 分隔；5. Along Normals checkbox |
| `tools.rotate_menu.center` | Rotate Center | 1. Default radio；2. Object radio；3. Manip radio；4. Selection radio |
| `tools.scale_menu` | Scale Tool Menu | 1. Selection Constraints→；2. Transform Constraints→；3. 分隔；4. Shift Extrude checkbox；5. Shift Duplicate checkbox；6. 分隔；7. Scale Center→；8. Prevent Negative Scale checkbox；9. Preserve UVs checkbox；10. Preserve Children checkbox；11. Tweak Mode checkbox；12. 分隔；13. Scale Options |
| `tools.scale_menu.selection_constraints` | Selection Constraints | 1. Off radio；2. Angle radio；3. Border radio；4. Edge Loop radio；5. Edge Ring radio；6. Shell radio；7. UV Edge Loop radio |
| `tools.scale_menu.transform_constraints` | Transform Constraints | 1. Off radio；2. Edge Slide radio；3. Surface Slide radio；4. 分隔；5. Along Normals checkbox |
| `tools.scale_menu.center` | Scale Center | 1. Default radio；2. Object radio；3. Manip radio |
| `tools.select.select_menu` | Select Menu | 1. Automatic Camera-Based Selection checkbox |
| `tools.move.select_menu` | Select Menu | 1. Automatic Camera-Based Selection checkbox |
| `tools.rotate.select_menu` | Select Menu | 1. Automatic Camera-Based Selection checkbox |
| `tools.scale.select_menu` | Select Menu | 1. Automatic Camera-Based Selection checkbox |
| `tools.move.snap_menu` | Snap Menu | 1. Relative Mode checkbox |
