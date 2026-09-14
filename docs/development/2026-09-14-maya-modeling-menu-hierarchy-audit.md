# Maya 2026 九个 Modeling 主菜单层级审计

日期：2026-09-14。范围仅 Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、Deform、UV、Generate。未改触发、方向、几何、registry 或 catalog。Common/Display 由父任务独立核验。

## 结论与重建边界

当前 `modeling_catalog.py:19–43` 是能力目录生成器，不是 Maya 菜单树。它把 `SPECS.section` 的每个字符串变成 submenu，再依次追加所有已实现 spec、ALIASES、GAPS。这会改变真实父子关系、同级顺序、重复入口位置和分隔，完全没有构造 Maya Options 或 separator。不能只把现有 section 全部展开：真正的 Booleans、Sculpting Tools、Bezier Curves、Stitch 等子菜单仍须保留。

应以本机真实运行时树为展示 reference，MEL 为来源与动态分支复核；registry 仅为固定命令绑定表。保留每个真实菜单、分隔、Options、状态形态及未实现占位。已实现 Blender 操作不等于真实 Maya 行：Maya 标签与适配说明分开，不能用 `Merge by Distance` 等替换标题后宣称内容一致。多个 Blender 行对应同一 Maya RTC 时必须显式选择唯一合适适配，其他能力留在清晰独立的原生扩展入口，不能随意复制成 Maya 行。

`modeling_registry.py:9–16` 的 CATEGORIES 不含 UV/Generate；`hotbox_catalog.py:259–260` 仅生成两个无子项 disabled 根。因此“九个主菜单存在”不等于九个内容已对齐。

## 来源与证据限度

基准根：`C:/Program Files/Autodesk/Maya2026/`。`scripts/startup/initMainMenuBar.mel:707–796` 明确九根 builder 及顺序，407–420 的 Modeling menu set 使用同一组根。下文 MEL 路径默认相对该基准。

源码中的 `uiRes(...)` key 与 `-rtc` 不是已解析的英文 UI 标签。下列层级和行号由真实 MEL 直接确认；精确最终 label、动态 enable/check、postMenuCommand 生成列表、XGen 加载分支须与 GUI agent 的运行时导出逐项比对。不要把正则扫描次数当成实际菜单节点数。此文没有运行 Maya/Blender GUI。

## 当前实际 Python 树数量

统计 `default_catalog()`；descendants 不含根。七个非空根合计 427 descendants：270 command、87 disabled、70 menu，**separator=0、Options 子节点=0**。这就是结构失真的直接证据，不能用命令覆盖率替代菜单覆盖率。

| 根 | 直接子项 | descendants | menu | command | disabled |
|---|---:|---:|---:|---:|---:|
| Mesh | 8 | 69 | 11 | 47 | 11 |
| Edit Mesh | 11 | 74 | 10 | 61 | 3 |
| Mesh Tools | 3 | 30 | 3 | 23 | 4 |
| Mesh Display | 11 | 70 | 12 | 54 | 4 |
| Curves | 7 | 56 | 11 | 33 | 12 |
| Surfaces | 6 | 56 | 11 | 14 | 31 |
| Deform | 8 | 72 | 12 | 38 | 22 |
| UV | 0 | 0 | 0 | 0 | 0 |
| Generate | 0 | 0 | 0 | 0 | 0 |

## 逐根核验

### Mesh — `scripts/startup/PolygonsMeshMenu.mel`

- 带名分隔：Combine(26)、Remesh(177)、Mirror(298)、Transfer(319)、Optimize(394)，不是五个 submenu。
- 真 submenu：Booleans(28–159)、Clipboard Actions(321–365)、Smooth Proxy(407–454)。Booleans 顺序由35–151确认：Union、Difference、Difference BA、Intersection、Slice、Hole Punch、Cut Out、Split Edges，各有真实 Options；当前将前四项置根 Booleans、后四项置 Combine→Booleans，拆裂同一目录且 Intersection/BA 顺序错误。
- Combine/Separate 在161–175是同级普通行。当前 Combine submenu 塞入三种 Blender Separate 变体，不能当成 Maya 的三行。
- Remesh 组的 Conform、Fill Hole、Reduce、Remesh、Retopologize、Smooth、Unsmooth、Triangulate、Quadrangulate 在178–296同级；当前增加 Modifiers、Element Order 等非 Maya 分类，且把 Mirror 操作藏入 Modifiers。
- Transfer Attributes/Transfer Shading Sets/Transfer Vertex Order 在367–394。当前拆成多种 Blender 数据传递/元素排序，必须区分适配与真实入口，不能用 Sort Elements 冒充 Transfer Vertex Order。
- 可复用候选：mesh.combine_objects、四个 mesh.boolean_*、mesh.fill_holes/reduce/smooth_subdivide/unsubdivide/triangulate/quadrangulate、mesh.mirror_geometry；准确目标模式和参数仍沿 registry 原约束。Retopologize/Remesh 不因名称相近就扩大适用域或 Options。

### Edit Mesh — `scripts/startup/PolygonsBuildMenu.mel`

- 真主序列是 Components(76)、Vertex(201)、Edge(231)、Face(264)、Curve(322) 五个 dividerLabel 组。主体56–345中没有把这些组声明为 submenu。
- Components 内有 Add Divisions、Bevel、Bridge、Circularize、Collapse、Connect、Detach、Extrude、Smart Extrude、Merge、Merge to Center、Transform/Flip/Symmetrize 等 RTC（78–198），多数后接独立 Options；当前 Extrude、Components、Merge、Topology、Interactive Topology、Face Boolean、Projected Cutting 是人为能力分类。
- Vertex 的 Average/Chamfer/Reorder(202–225)、Edge 的 Delete/Edit Edge Flow/Flip/Spin(232–261)、Face 的 Invisible/Duplicate/Extract/Poke/Wedge(266–312)、Curve 的 Project/Split(324–335) 须恢复真实位置。
- `createSelectCreaseSetsMenu`(8–41) 是额外动态构造 helper；不能凭源文件开头顺序把 helper 生成项硬插根级。运行时导出应明确其实际挂载点。
- 可复用候选 mesh.subdivide/bevel_edges/bridge/circularize/collapse、对应 extrude/merge、average_vertices、edge_flow/edge_rotate、duplicate_faces/extract_faces/poke_faces/spin/project_cut；Blender 的额外 merge variants/face boolean 等不能伪装成 Maya 同级项。

### Mesh Tools — `scripts/startup/PolygonsBuildToolsMenu.mel`

- Modeling Toolkit 行在34；Tools 是38的 divider。当前 Tools/Immediate Tools/Shape Authoring 三目录不是原生主层级。
- 原顺序：Append(40)、Connect(53)、Crease(65)、Create Polygon(78)、Insert Edge Loop(93)、Make Hole(104)、Multi-Cut(116)、Offset Edge Loop(127)、Paint Reduce Weights(144)、Paint Transfer Attributes(154)、Quad Draw(162)、Sculpting Tools submenu(173)、Slide Edge(414)、Target Weld(426)。Options 按源相邻声明保留，不可批量给所有可执行行生成设置。
- Sculpting Tools 是真实目录：182–352有18个 sculpt brushes；内部 Shape divider(361) 后还有 Smooth Target/Clone Target/Mask/Erase(365–401)，合计22主操作，非22个根行。当前全部漏失，包括灰显占位。
- 可复用 tool.mesh_* / mesh.interactive_* 仅是适配候选；不可同时将即时/modal 两套实现都塞入同一个 Maya 行或改其持久工具含义。

### Mesh Display — `scripts/startup/ModelingMeshDisplayMenu.mel`

- Normals(46)、Vertex Colors(136)、Vertex Color Sets(161)、Vertex Bake Sets(202)、Display Attributes(243) 全是分隔标题。当前 Normals/Vertex Colors/Display Attributes 变成 submenu，且多插 Average Normals、Edit Normals、Face Strength、Shading、Normal Modifiers、Viewport Analysis、Data Marks 等 Blender 目录。
- 真 submenu：Assign Existing Set(223–239，动态 bake set)、Color Material Channel(250–264)、Material Blend Setting(268–282)、Per Instance Sharing(285–296)。后两种枚举目录当前整个缺失；不能用普通 Display 模式/颜色属性操作替代。
- Normals 固定顺序48–134：Average、Conform、Reverse、Set to Face、Set Vertex Normal、Harden、Soften、Soften/Harden、Lock、Unlock、Vertex Normal Edit Tool，Options 逐项源证；当前把 Blender 方向/平均变体扩为多行。
- 漏项证据：Set Keyframe for Vertex Color(193)、Preflight(205)、Assign New Set(217)、Edit Assigned Set(241)、Color Material 六项(257–262)、Blend Setting 七项(274–280)。动态已存在集合为空也不意味着删除固定父目录。
- 可复用 normals.*、color.* 的准确适配，不扩大 OBJECT/EDIT_MESH 约束；保留当前已有 Blender 诊断能力作为独立扩展，不冒充 Maya 原层级。

### Curves — `scripts/startup/ModelingCurvesMenu.mel`

- Modify(42) 与 Edit(103) 是组分隔，当前七个顶层分类 Control Points/Topology/Construct/Bezier Handles/Spline Type/Geometry/Edit 非原结构。
- 开头 Modify 七项：Lock Curve Length(45)、Unlock(48)、Bend(53)、Curl(63)、Scale Curvature(73)、Smooth Hair Curves(83)、Straighten(93)，当前连缺失占位也没有。
- Edit 普通行从 Duplicate/Align/Add Points/Attach/Detach/Edit Tool/Move Seam/Open-Close 到 Fillet/Cut/Intersect 等(105–222)，不是仅把未实现项放进 Edit submenu。
- 真目录 Extend(232–263)、Offset(280–312) 受 SurfaceUIExists 条件影响；Bezier Curves(374–414) 内 Presets 和 Tangent Options 两个真实子目录。当前 Bezier Handles/Spline Type 是 Blender 抽象，且只保留 Tangent Options 的部分 gap。
- Rebuild/Reverse 位于末尾418–437。可复用 curve.* 的控制点/样条操作，但 Lock、Bend 等不可用名称近似操作假接。

### Surfaces — `scripts/startup/ModelingSurfacesMenu.mel`

- Create(42) 与 Edit NURBS Surfaces(201) 都是 divider，不是真 submenu。当前 Create/Edit NURBS Surfaces 目录只收 gaps，已实现项另放 Control Points/Topology/Construct/Geometry，破坏真实混排。
- Create 真顺序：Loft、Planar、Revolve(44–84)、Birail submenu(87–125)、Extrude、Boundary、Square、Bevel、Bevel Plus(127–199)。当前 Revolve/Extrude 适配与灰显其他项被分到不同父级。
- 真目录：Birail、Stitch(374–415)、Surface Fillet(417–459)、Surface Editing(474–499)、Booleans(503–543)。这些真实层级应留，不能随错误组目录一起 flatten。
- Edit 主体203–571包括 Duplicate/Align/Attach/Attach Without Moving/Detach/Move Seam/Open Close/Intersect/Project/Trim/Untrim/Extend/Insert Isoparms/Offset/Round/Sculpt Geometry/Rebuild/Reverse 等。SculptGeometryTool(464) 在当前 SPECS.maya/GAPS/ALIASES 中无声明。
- surface.* 多是 Blender NURBS 控制点操作而不是 Maya surface patch construction；重绑前核对差异说明，不以可执行性优先覆盖真实缺失项。

### Deform — `scripts/startup/ChaDeformationsMenu.mel`

- 761–780按顺序调用 Create、Edit、Weights、Legacy section。Create(100)、Edit(408)、Intermediate Objects(567)、Weights(687)、Membership(718) 是分隔标题，当前大部分误变成父目录。
- 真 submenu 包括 Pose Space Deformation(235–252)、Nonlinear(265–321)、Jiggle(356–381)、Edit 下同级 Blend Shape(411–447)、Lattice(449–462)、Wrap(464–474)、ShrinkWrap(476–502)、Wire(504–565)、Paint Weights(584–682)、Prune Membership(725–747)。不应把所有变形按 Blender “Nonlinear and Smooth/Targets and Binding/Shape Keys/Membership and Hooks”重排。
- 明确漏项/缺占位：MLDeformer(139)、Wrinkle(228)、Pose Interpolator/Pose Editor(242–249)、Sculpt/Jiggle/Disk Cache(335–379)、Paint Weights完整工具组(588–674)、Prune Sculpt(739)、Paint Set Membership(751)。CurveWarp(89)及Muscle由插件动态加入，必须注明插件快照，不能当成无条件常量树。
- 可复用 deform.bend/twist/taper/stretch、lattice、shape keys、binding、weights 等固定实现；Morph/CreateBlendShape/AddBlendShape 共映射单个适配能力的情况不能据此宣称三个 Maya 行语义都相同。

### UV — `scripts/startup/ModelingUVMenu.mel`

- 固定入口 UV Editor(42–46)、UV Set Editor(48–51)，随后 Create(54)、Cut/Sew(181)、Tools(223) 三个带名分隔；主 builder没有人工折叠目录。
- 19个 RTC 主项包括 Create Shader 状态(60)、Automatic/Best Plane/Camera/Contour/Normal/Cylindrical/Planar/Spherical projection(66–167)、Auto Seams(186)、Cut/Sew/Split/Delete/Merge(198–215)、Cut/Sew Tool、Grab UV Tool(227–235)。Options 与状态逐项保留。
- 当前整根 disabled、0 children；不应以未来 UV 开发范围为理由删 Maya 内容。未实现可灰显，但导航目录必须可浏览。没有本 registry 内的直接候选，禁止临时通配 bpy.ops.uv 自动开启。

### Generate — `scripts/startup/ModelingGenerateMenu.mel`

- 26–39按 xgenToolkit 加载状态增删 XGen。63设置 anchor；67–69按 MayaCreatorExists 调用 `scripts/paintEffects/buildCreatorMenu.mel:131`；所以检查这一个69行 builder 或其菜单数量不能代表内容。
- Paint Effects builder：Cloud Services divider(141)，Character Generator/ReCap(143–152)；Paint Effects divider(161)；工具、Make Paintable、Brush/Template/Flip/Collide(163–190)，Paint on Objects/View Plane radio(194–201)，stroke settings等；真目录 Brush Animation(234)、Curve Utilities(256)、Auto Paint(278)，Preset Blending checkbox(303)及独立Options(306)。全部目前缺失。
- XGen builder `plug-ins/xgen/scripts/xgenUI.mel:75`，118起用 insertAfter 在 Generate anchor 后插入。XGen Editor/Library/Create/Import/Export/Archive/Convert 等并非一个自由排序数组。运行时按实际加载插件取真实树；插件关闭/无当前集合时保留已审计的固定可见层级边界，不生成假实例名。
- 无可直接复用 registry 主动作。Cloud links 不应自动接网络；全部未适配操作可明确灰显，但不把整根删空。

## 建议实现方式与验收

1. 由真实 runtime 提取九根完整树，强制触发 lazy postMenuCommand，逐节点记录 source menu path、label、separator（含 dividerLabel）、optionBox、command/RTC、check/radio/enabled 以及动态来源。运行时树与此文 MEL 分组/嵌套双向比对，不能只比较扁平 command set。
2. 保存独立版本化 reference 模块/JSON。不能再从 SPECS.section 生成 Maya 层级；不要把未知项统一删掉或挪到“未实现”目录。生成命令ID/父子序号稳定，Options 只对应紧邻源主项。
3. 固定显式 binding map 从 reference 身份映射已有 registry id；无映射节点保持禁用及准确原因。多对一 Maya identity 和一对多 Blender variant 都需人工明确判定。现有纯 Blender 额外能力保留独立入口，根布局由父任务统合。
4. 已实现主项不代表其 Maya Options 已实现；不得把主项 EXEC 当 Options。状态也不能把 Maya 当前启用值复制成 Blender 真实状态，未适配使用已批准 unavailable state 表。
5. 纯测试以独立真实树验证九根顺序、完整路径、separator 类型/标签、Options 邻接、checkbox/radio 形态、固定 disabled 占位及无未知命令。覆盖 UV/Generate 非空、Booleans 不拆分、Sculpting Tools22、Curves Modify7、Deform Paint Weights 和动态父目录。
6. GUI按实际新内容浏览主根/真子菜单，保留所有原方向、Views内缘、释放、取消、源上下文事务。不得继续把人为目录或“56 flat Display”旧 fixture 当源事实。布局是否可容纳以新真实树重新测量，不为通过旧高度断言删内容。

## 静态主 RTC 覆盖差额（辅助复核）

以下将各文件 `-rtc`（含前文 `$cmd` 字符串赋值）与当前 `SPECS.maya ∪ GAPS.identity ∪ ALIASES.identity` 比较，排除 Options。它是身份声明差额，**不是自动推断行为绝对缺失**：例如已有近似 Conform 适配仍需人工确认。非 RTC/direct command/dynamic callbacks 不在此表，因此表不能替代完整运行时 reference。

- **PolygonsMeshMenu.mel**：`ConformPolygon`(178)、`TransferVertexOrder`(389)。
- **PolygonsBuildMenu.mel**：`MovePolygonComponent`(178)、`FlipMesh`(193)、`ReorderVertex`(225)。
- **PolygonsBuildToolsMenu.mel**：`PaintReduceWeightsTool`(144)、`PaintTransferAttributes`(154)、`SetMeshSculptTool`(182)、`SetMeshSmoothTool`(192)、`SetMeshRelaxTool`(202)、`SetMeshGrabTool`(212)、`SetMeshPinchTool`(222)、`SetMeshFlattenTool`(232)、`SetMeshFoamyTool`(242)、`SetMeshSprayTool`(252)、`SetMeshRepeatTool`(262)、`SetMeshImprintTool`(272)、`SetMeshWaxTool`(282)、`SetMeshScrapeTool`(292)、`SetMeshFillTool`(302)、`SetMeshKnifeTool`(312)、`SetMeshSmearTool`(322)、`SetMeshBulgeTool`(332)、`SetMeshAmplifyTool`(342)、`SetMeshFreezeTool`(352)、`SetMeshSmoothTargetTool`(365)、`SetMeshCloneTargetTool`(377)、`SetMeshMaskTool`(389)、`SetMeshEraseTool`(401)。
- **ModelingMeshDisplayMenu.mel**：`SetKeyframeForVertexColor`(193)、`PreflightPolygon`(205)、`AssignNewSet`(217)、`EditAssignedSet`(241)、`SetCMCNone`(257)、`SetCMCAmbient`(258)、`SetCMCAmbientDiffuse`(259)、`SetCMCDiffuse`(260)、`SetCMCSpecular`(261)、`SetCMCEmission`(262)、`SetMBSOverwrite`(274)、`SetMBSAdd`(275)、`SetMBSSubtract`(276)、`SetMBSMultiply`(277)、`SetMBSDivide`(278)、`SetMBSAverage`(279)、`SetMBSModulate2`(280)。
- **ModelingCurvesMenu.mel**：`LockCurveLength`(45)、`UnlockCurveLength`(48)、`BendCurves`(53)、`CurlCurves`(63)、`ScaleCurvature`(73)、`SmoothHairCurves`(83)、`StraightenCurves`(93)。
- **ModelingSurfacesMenu.mel**：`SculptGeometryTool`(464)。
- **ChaDeformationsMenu.mel**：`CurveWarp`(89)、`MLDeformer`(139)、`WrinkleTool`(228)、`CreatePoseInterpolator`(242)、`PoseEditor`(249)、`CreateSculptDeformer`(335)、`CreateJiggleDeformer`(360)、`CreateDiskCache`(370)、`GlobalDiskCacheControl`(379)、`ArtPaintBlendShapeWeightsTool`(588)、`PaintClusterWeightsTool`(597)、`PaintDeltaMushWeightsTool`(605)、`PaintTensionWeightsTool`(613)、`PaintProximityWrapWeightsTool`(621)、`PaintLatticeWeightsTool`(629)、`PaintShrinkWrapWeightsTool`(637)、`PaintWireWeightsTool`(645)、`PaintNonlinearWeightsTool`(655)、`PaintJiggleWeightsTool`(663)、`PaintTextureDeformerWeightsTool`(671)、`PruneSculpt`(739)、`PaintSetMembershipTool`(751)。
- **ModelingUVMenu.mel**：`TextureViewWindow`(45)、`UVSetEditor`(50)、`TogglePolyUVsCreateShader`(60)、`UVAutomaticProjection`(66)、`BestPlaneTexturingTool`(81)、`UVCameraBasedProjection`(88)、`UVContourStretchProjection`(105)、`UVNormalBasedProjection`(119)、`UVCylindricProjection`(136)、`UVPlanarProjection`(152)、`UVSphericalProjection`(167)、`AutoSeamUVs`(186)、`CutUVsWithoutHotkey`(198)、`SewUVsWithoutHotkey`(202)、`SplitUV`(205)、`DeleteUVsWithoutHotkey`(211)、`MergeUV`(215)、`SetCutSewUVTool`(227)、`SetMeshGrabUVTool`(235)。

## 实机 reference 到达后的独立复核

已只读核验 `docs/reference/maya2026-menu-tree.json`（GUI agent 生成）。快照 Maya 2026/API 20260200，空场景 perspective；XGen 不在已加载插件列表。该次 Generate 因而只有 Cloud Services/Paint Effects 主体；XGen 补充树仍须按插件边界单独声明。唯一构造错误是 Current Pane/View/Bookmarks，九 Modeling 根没有 callback errors。Options 的某些 label 是动态控件名，产品必须将其表现为独立参数格，不能把 menuItem994 一类名字当正文标签。

下表是实际运行时顶层槽数（含 Options 与 divider），真实 submenu 名称及其直接槽数。它确认上文带名 divider 与真子目录的区别，不把槽数当主动作数。

| 根 | 顶层槽 | 真实顶层 submenu（直接槽数） |
|---|---:|---|
| Mesh | 38 | Booleans (16)、Clipboard Actions (6)、Smooth Proxy (9) |
| Edit Mesh | 53 | 无 |
| Mesh Tools | 29 | Sculpting Tools (45) |
| Mesh Display | 47 | Assign Existing Set (1)、Color Material Channel (6)、Material Blend Setting (7)、Per Instance Sharing (2) |
| Curves | 57 | Extend (4)、Offset (4)、Bezier Curves (2) |
| Surfaces | 67 | Birail (6)、Stitch (6)、Surface Fillet (6)、Surface Editing (4)、Booleans (6) |
| Deform | 61 | Pose Space Deformation (3)、Nonlinear (12)、Jiggle (5)、Blend Shape (8)、Lattice (2)、Wrap (2)、ShrinkWrap (6)、Wire (13)、Paint Weights (24)、Prune Membership (4) |
| UV | 37 | 无 |
| Generate | 38 | Brush Animation (6)、Curve Utilities (6)、Auto Paint (4) |

复核要点：Edit Mesh、UV 实机顶层没有 submenu；Mesh Tools 只出现 Sculpting Tools 这一真实目录（45槽=22操作+22 Options+1 Shape标题）；Deform 的 Paint Weights 为24槽，应依据真实内容保留，不把源码静态身份差额误当实际行数。Curves 开头准确显示 Lock Length、Unlock Length，源码 RTC `LockCurveLength` 不应直接变成产品标签。

Reference SHA256：`22fed70cfbab6cddfd955160952929d1456fc19f8999755e6406b4e56ad27522`。
