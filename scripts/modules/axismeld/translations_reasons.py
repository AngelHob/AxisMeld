# SPDX-FileCopyrightText: 2026 AxisMeld Authors
# SPDX-License-Identifier: GPL-2.0-or-later
"""Simplified Chinese menu explanations and native hotbox context diagnostics.

Full source strings are keys, including plan IDs and native confirmation suffixes.
Translations preserve selection, topology, data, cancellation and Undo boundaries.
"""

ZH_HANS = {'Custom property source context or object changed': '自定义属性的来源上下文或对象已改变',
 'No supported custom property on the active object': '活动对象上没有支持的自定义属性',
 'Selected custom property is missing or unsupported': '所选自定义属性已丢失或类型不受支持',
 'Custom property value is invalid for the selected type': '自定义属性值不符合所选类型',
 'Choose a unique non-reserved property name': '请选择唯一且非保留的属性名称',
 'Unknown property navigation target': '未知的属性导航目标',
 'Property navigation requires the graphical application': '属性导航需要图形界面',
 'Property navigation requires a live 3D viewport in the source window': '属性导航需要来源窗口中有效的三维视窗',
 'Requires an active selected object in the source view layer': '需要来源视图层中的活动选中对象',
 'The active object has no native Modifier Properties context': '当前活动对象没有原生修改器属性页',
 'No visible unpinned or same-object-pinned Properties editor in this window': '当前窗口没有可见的未固定或固定到同一对象的属性编辑器',
 'Property navigation source or editor is unavailable': '属性导航的来源或编辑器不可用',
 'Navigate native Blender properties in an existing editor; preserve pins and scene data': '在已有编辑器中打开 Blender 原生属性，保留固定状态和场景数据',
 'Absolute vertex-normal vector settings not implemented': '尚未实现顶点法向的绝对向量设置',
 'Activate the Blender Box Select tool': '激活 Blender 框选工具',
 'Activate the registered Blender tool; subsequent viewport strokes perform edits. Poly Build is not the complete Maya Quad Draw/Append/Target Weld workflow.': '激活已注册的 '
                                                                                                                                                                'Blender '
                                                                                                                                                                '工具；后续视窗笔画执行编辑。多边形构建并非完整的 '
                                                                                                                                                                'Maya '
                                                                                                                                                                '四边形绘制、追加多边形或目标焊接工作流。',
 'Activates the native combined move/rotate/scale gizmo; Maya tool-specific manipulator options differ.': '激活原生移动/旋转/缩放组合操纵器；与 '
                                                                                                          'Maya '
                                                                                                          '各工具的操纵器选项有差异。',
 'Active mesh and one selected curve; native local-axis curve deformation, not multi-wire/dropoff nodes. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '需要活动网格和一个选中曲线；使用原生局部轴曲线变形，不包含多线或衰减节点。参数位于“编辑 '
                                                                                                                                                                                    '> '
                                                                                                                                                                                    '调整上一步操作”及原生修改器属性。',
 'Active mesh receives relative keys from equal indexed topology; first target influence is 1. Source targets remain. World-space target coordinates are converted to source local space.': '活动网格从索引拓扑一致的目标接收相对形态键；首个目标影响为 '
                                                                                                                                                                                            '1，源目标保留。目标的世界坐标转换到源网格的局部空间。',
 'Active path curve uses the other selected curve as a bevel profile; creates evaluated curve geometry, not a Maya NURBS surface patch or its path parameterization.': '活动路径曲线以另一个选中曲线为倒角轮廓；生成求值后的曲线几何，不生成 '
                                                                                                                                                                       'Maya '
                                                                                                                                                                       'NURBS '
                                                                                                                                                                       '曲面片或其路径参数化。',
 'Active source, one selected mesh target; nearest surface point with 0.05 offset. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '需要活动源对象和一个选中网格目标；使用最近表面点，偏移为 '
                                                                                                                                                              '0.05。参数位于“编辑 '
                                                                                                                                                              '> '
                                                                                                                                                              '调整上一步操作”及原生修改器属性。',
 'Add Decimate modifier to active Mesh; default ratio 50 percent': '为活动网格添加精简修改器；默认比例为 50%。',
 'Add Mirror modifier to active Mesh; default X bisect and merge': '为活动网格添加镜像修改器；默认沿 X 轴切分并合并。',
 'Add Subdivision Surface modifier to active Mesh; other selected objects are unchanged': '为活动网格添加表面细分修改器；其他选中对象保持不变。',
 'Add Voxel Remesh modifier to active Mesh; original mesh remains': '为活动网格添加体素重构修改器；原始网格保留。',
 'Add one configured Blender modifier to the active editable mesh; geometry evaluation and input compatibility are checked. Parameters remain editable in Modifiers.': '为活动可编辑网格添加一个已配置的 '
                                                                                                                                                                       'Blender '
                                                                                                                                                                       '修改器；检查几何求值与输入兼容性，参数仍可在修改器中编辑。',
 'Additional camera types depend on plugin registration': '其他相机类型依赖插件注册',
 'Additional light types depend on plugin registration': '其他灯光类型依赖插件注册',
 'Adds a native spline at the 3D Cursor; this is primitive creation, not the complete Maya interactive CV/EP tool.': '在三维游标处添加原生样条；这是基本体创建，不是完整的 '
                                                                                                                     'Maya '
                                                                                                                     '交互式控制顶点/编辑点工具。',
 'Assembly types require registered capabilities': '装配类型需要已注册的能力',
 'Asset members require current scene containers; None remains a fixed action': '资产成员需要当前场景容器；“无”仍为固定操作。',
 'Attribute-set and source/target transfer adaptation not implemented': '尚未适配属性集及源/目标传递',
 'Bake set members require current scene sets': '烘焙集成员需要当前场景集合',
 'Bakes local single-user static mesh modifier stacks with native Apply. Non-deformer baking preserves OnlyDeform modifiers and requires topology modifiers to precede them; shared data, shape keys, animation/drivers/NLA, overrides, Collision application, disabled modifiers and interleaved stacks are unavailable. No Maya DG nodes are deleted.': '使用原生“应用”烘焙本地单用户静态网格的修改器堆栈。非变形器烘焙保留 '
                                                                                                                                                                                                                                                                                                                                                          'OnlyDeform '
                                                                                                                                                                                                                                                                                                                                                          '修改器，并要求拓扑修改器位于其前；共享数据、形态键、动画/驱动器/NLA、覆盖数据、碰撞修改器应用、禁用修改器及交错堆栈均不可用。不会删除 '
                                                                                                                                                                                                                                                                                                                                                          'Maya '
                                                                                                                                                                                                                                                                                                                                                          '依赖图节点。',
 'Bezier handle constraint; Blender aligned/free handles do not reproduce all Maya anchor-length and NURBS CV-hardness rules.': '贝塞尔控制柄约束；Blender '
                                                                                                                                '对齐/自由控制柄不能复现全部 '
                                                                                                                                'Maya '
                                                                                                                                '锚点长度和 '
                                                                                                                                'NURBS '
                                                                                                                                '控制顶点硬度规则。',
 'Binds active mesh to one selected target mesh. Target deformation drives source after binding; topology must remain stable. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '将活动网格绑定到一个选中目标网格。绑定后目标变形驱动源网格，拓扑必须保持稳定。参数位于“编辑 '
                                                                                                                                                                                                         '> '
                                                                                                                                                                                                         '调整上一步操作”及原生修改器属性。',
 'Blender Apply bakes transforms into data; not exact Maya Freeze. Native multi-user confirmation is retained.': 'Blender“应用”将变换烘焙进数据，并不完全等同于 '
                                                                                                                 'Maya '
                                                                                                                 '冻结变换；保留原生多用户确认流程。',
 'Blender Batch Rename patterns and current selected-object targets; hierarchy is not implicitly selected.': '使用 '
                                                                                                             'Blender '
                                                                                                             '批量重命名模式和当前选中对象作为目标；不会隐式选择层级。',
 'Blender Beautify Faces; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                               '美化面；使用原生拓扑与参数，不包含 Maya '
                                                                                               '构建历史。',
 'Blender Bridge Edge Loops; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                  '桥接循环边；使用原生拓扑与参数，不包含 '
                                                                                                  'Maya 构建历史。',
 'Blender Circularize; native topology and parameters, without Maya construction history.': 'Blender 圆形化；使用原生拓扑与参数，不包含 '
                                                                                            'Maya 构建历史。',
 'Blender Clear Freestyle Edge; native topology and parameters, without Maya construction history.': 'Blender 清除 '
                                                                                                     'Freestyle '
                                                                                                     '边标记；使用原生拓扑与参数，不包含 '
                                                                                                     'Maya 构建历史。',
 'Blender Clear Freestyle Face; native topology and parameters, without Maya construction history.': 'Blender 清除 '
                                                                                                     'Freestyle '
                                                                                                     '面标记；使用原生拓扑与参数，不包含 '
                                                                                                     'Maya 构建历史。',
 'Blender Collapse Edges; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                               '塌陷边；使用原生拓扑与参数，不包含 Maya '
                                                                                               '构建历史。',
 'Blender Collections are organization/linking sets, not Maya transform groups or exclusive partitions.': 'Blender '
                                                                                                          '集合用于组织和链接，并非 '
                                                                                                          'Maya '
                                                                                                          '变换组或互斥分区。',
 'Blender Connect Vertex Pairs; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                     '连接顶点对；使用原生拓扑与参数，不包含 '
                                                                                                     'Maya 构建历史。',
 'Blender Connect Vertex Path; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                    '连接顶点路径；使用原生拓扑与参数，不包含 '
                                                                                                    'Maya 构建历史。',
 'Blender Delete Edge Loop; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                 '删除循环边；使用原生拓扑与参数，不包含 '
                                                                                                 'Maya 构建历史。',
 'Blender Dissolve Edges; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                               '融并边；使用原生拓扑与参数，不包含 Maya '
                                                                                               '构建历史。',
 'Blender Dissolve Faces; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                               '融并面；使用原生拓扑与参数，不包含 Maya '
                                                                                               '构建历史。',
 'Blender Dissolve Vertices; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                  '融并顶点；使用原生拓扑与参数，不包含 '
                                                                                                  'Maya 构建历史。',
 'Blender Duplicate Faces in Place; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                         '原位复制面；使用原生拓扑与参数，不包含 '
                                                                                                         'Maya 构建历史。',
 'Blender Edit Mesh crease overlay controls edge and vertex creases together; Maya has separate switches.': 'Blender '
                                                                                                            '网格编辑的折痕叠加同时控制边与顶点折痕；Maya '
                                                                                                            '分别设置开关。',
 'Blender Edit Mesh separation; loose parts are connected shells, not Maya DAG history.': '使用 Blender '
                                                                                          '网格编辑分离；松散部分指相连壳体，不包含 Maya '
                                                                                          'DAG 历史。',
 'Blender Extract Faces (Separate); native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                         '提取面（分离）；使用原生拓扑与参数，不包含 '
                                                                                                         'Maya 构建历史。',
 'Blender Face Strength: Medium; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                      '面强度：中；使用原生拓扑与参数，不包含 '
                                                                                                      'Maya 构建历史。',
 'Blender Face Strength: Strong; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                      '面强度：强；使用原生拓扑与参数，不包含 '
                                                                                                      'Maya 构建历史。',
 'Blender Face Strength: Weak; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                    '面强度：弱；使用原生拓扑与参数，不包含 '
                                                                                                    'Maya 构建历史。',
 'Blender Fill Holes; native topology and parameters, without Maya construction history.': 'Blender 填充孔洞；使用原生拓扑与参数，不包含 '
                                                                                           'Maya 构建历史。',
 'Blender Fill; native topology and parameters, without Maya construction history.': 'Blender 填充；使用原生拓扑与参数，不包含 Maya '
                                                                                     '构建历史。',
 'Blender Flatten; native topology and parameters, without Maya construction history.': 'Blender 压平；使用原生拓扑与参数，不包含 Maya '
                                                                                        '构建历史。',
 'Blender Grid Fill; native topology and parameters, without Maya construction history.': 'Blender 栅格填充；使用原生拓扑与参数，不包含 '
                                                                                          'Maya 构建历史。',
 'Blender Icosphere adaptation only; not the full Maya Platonic Solid family': '仅适配 Blender 棱角球，并非完整的 Maya 柏拉图多面体系列。',
 'Blender Intersect Faces; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                '相交面；使用原生拓扑与参数，不包含 '
                                                                                                'Maya 构建历史。',
 'Blender Keep Transform on current Object selection only': '仅对当前对象选区使用 Blender 保持变换',
 'Blender Knife adaptation; Maya Multi-Cut behavior differs': '适配 Blender 切割工具；与 Maya 多重切割行为有差异。',
 'Blender Laplacian Smooth Vertices; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                          '拉普拉斯平滑顶点；使用原生拓扑与参数，不包含 '
                                                                                                          'Maya 构建历史。',
 'Blender Local View isolation, not a saved Maya isolate-set network.': '使用 Blender 局部视图隔离，不建立已保存的 Maya 隔离集网络。',
 'Blender Make Edge / Face; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                 '创建边/面；使用原生拓扑与参数，不包含 '
                                                                                                 'Maya 构建历史。',
 'Blender Mark Freestyle Edge; native topology and parameters, without Maya construction history.': 'Blender 标记 '
                                                                                                    'Freestyle '
                                                                                                    '边；使用原生拓扑与参数，不包含 '
                                                                                                    'Maya 构建历史。',
 'Blender Mark Freestyle Face; native topology and parameters, without Maya construction history.': 'Blender 标记 '
                                                                                                    'Freestyle '
                                                                                                    '面；使用原生拓扑与参数，不包含 '
                                                                                                    'Maya 构建历史。',
 'Blender Merge by Distance; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                  '按距离合并；使用原生拓扑与参数，不包含 '
                                                                                                  'Maya 构建历史。',
 'Blender POINT/CORNER color attributes, not Maya per-instance color sets. Management uses Object mode; Set Color affects the active object or selected Edit-domain elements.': '使用 '
                                                                                                                                                                                'Blender '
                                                                                                                                                                                'POINT/CORNER '
                                                                                                                                                                                '颜色属性，并非 '
                                                                                                                                                                                'Maya '
                                                                                                                                                                                '的逐实例颜色集。管理操作使用对象模式；设置颜色影响活动对象或选中的编辑域元素。',
 'Blender Poke Faces; native topology and parameters, without Maya construction history.': 'Blender 戳面；使用原生拓扑与参数，不包含 '
                                                                                           'Maya 构建历史。',
 'Blender Poly Build adaptation; not Maya Append or Quad Draw algorithms': '适配 Blender 多边形构建；不采用 Maya 追加多边形或四边形绘制算法。',
 'Blender Poly Build adaptation; not Maya Quad Draw algorithm': '适配 Blender 多边形构建，不采用 Maya 四边形绘制算法。',
 'Blender Poly Build; Maya Append behavior is not reproduced exactly': '使用 Blender 多边形构建，不能完全复现 Maya 追加多边形行为。',
 'Blender Quadrangulate; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                              '四边形化；使用原生拓扑与参数，不包含 Maya '
                                                                                              '构建历史。',
 'Blender QuadriFlow, not Maya Retopologize. Opens native parameters and requires valid manifold input.': '使用 Blender '
                                                                                                          'QuadriFlow，并非 '
                                                                                                          'Maya '
                                                                                                          '重拓扑。打开原生参数，且要求有效的流形输入。',
 'Blender Reduce; native topology and parameters, without Maya construction history.': 'Blender 精简；使用原生拓扑与参数，不包含 Maya '
                                                                                       '构建历史。',
 'Blender Relax Edge Loops; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                 '松弛循环边；使用原生拓扑与参数，不包含 '
                                                                                                 'Maya 构建历史。',
 'Blender Smooth Subdivide; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                 '平滑细分；使用原生拓扑与参数，不包含 '
                                                                                                 'Maya 构建历史。',
 'Blender Smooth Vertices; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                '平滑顶点；使用原生拓扑与参数，不包含 '
                                                                                                'Maya 构建历史。',
 'Blender Solid viewport; uses Blender object shading': 'Blender 实体视窗；使用 Blender 对象着色。',
 'Blender Space Edge Loops Evenly; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                        '均匀排列循环边；使用原生拓扑与参数，不包含 '
                                                                                                        'Maya 构建历史。',
 'Blender Split Faces by Edges; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                     '按边拆分面；使用原生拓扑与参数，不包含 '
                                                                                                     'Maya 构建历史。',
 'Blender Split Selected Edges; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                     '拆分选中边；使用原生拓扑与参数，不包含 '
                                                                                                     'Maya 构建历史。',
 'Blender Split Selection; native topology and parameters, without Maya construction history.': 'Blender '
                                                                                                '拆分选区；使用原生拓扑与参数，不包含 '
                                                                                                'Maya 构建历史。',
 'Blender Subdivide; native topology and parameters, without Maya construction history.': 'Blender 细分；使用原生拓扑与参数，不包含 '
                                                                                          'Maya 构建历史。',
 'Blender Symmetrize; native topology and parameters, without Maya construction history.': 'Blender 对称化；使用原生拓扑与参数，不包含 '
                                                                                           'Maya 构建历史。',
 'Blender Triangulate; native topology and parameters, without Maya construction history.': 'Blender 三角化；使用原生拓扑与参数，不包含 '
                                                                                            'Maya 构建历史。',
 'Blender Unsubdivide; native topology and parameters, without Maya construction history.': 'Blender 反细分；使用原生拓扑与参数，不包含 '
                                                                                            'Maya 构建历史。',
 'Blender Wireframe viewport': 'Blender 线框视窗',
 'Blender bevel profile, overlap and miter behavior; interactive native operator.': '使用 Blender '
                                                                                    '倒角轮廓、重叠和斜接行为；由交互式原生操作执行。',
 'Blender control-net subdivision; not exact shape-preserving knot/isoparm insertion.': '使用 Blender '
                                                                                        '控制网格细分，不是严格保持形状的节点/等参线插入。',
 'Blender custom-normal, face-area or corner-angle weighting.': '使用 Blender 自定义法向、面面积或顶角加权。',
 'Blender face dots are visible with face selection in non-X-Ray solid shading; no Maya Object-mode dots.': '在关闭透视的实体着色中，选择面时显示 '
                                                                                                            'Blender '
                                                                                                            '面中心点；没有 '
                                                                                                            'Maya '
                                                                                                            '对象模式下的面中心点。',
 'Blender face-distortion analysis colors non-planarity by its native angular thresholds; not Maya binary non-planar highlighting. Uses the current scene analysis thresholds and requires non-translucent X-Ray.': 'Blender '
                                                                                                                                                                                                                    '面畸变分析按原生角度阈值为非共面程度着色，并非 '
                                                                                                                                                                                                                    'Maya '
                                                                                                                                                                                                                    '二元非平面高亮。使用当前场景分析阈值，且要求关闭半透明透视。',
 'Blender index sorting; does not transfer vertex correspondence from another mesh.': '使用 Blender '
                                                                                      '索引排序；不会从另一个网格传递顶点对应关系。',
 'Blender linked object data instance; arbitrary Maya Duplicate Special arrays/history are not implied.': '创建 Blender '
                                                                                                          '链接对象数据实例；不表示已支持任意 '
                                                                                                          'Maya '
                                                                                                          '特殊复制阵列或历史。',
 'Blender merge target; First/Last require visible selected vertex history.': '使用 Blender 合并目标；“首个/末个”需要可见的选中顶点历史。',
 'Blender native Open file selector; confirms explicitly': 'Blender 原生打开文件选择器；需要显式确认。',
 'Blender native Save As file selector; confirms explicitly': 'Blender 原生另存为文件选择器；需要显式确认。',
 'Blender objects carry transforms; this excludes Maya transform-only DAG nodes.': 'Blender 对象承载变换；不包括 Maya 仅含变换的 DAG '
                                                                                   '节点。',
 'Blender per-view-layer display. Show Last Hidden tracks AxisMeld hides; Untemplate restores selected or the last templated batch and its saved flags.': '使用 '
                                                                                                                                                          'Blender '
                                                                                                                                                          '各视图层显示。“显示上次隐藏”跟踪 '
                                                                                                                                                          'AxisMeld '
                                                                                                                                                          '隐藏操作；“取消模板”恢复选中对象或上次模板批次及保存的标记。',
 'Blender persistent Knife tool; Maya Multi-Cut behavior differs': 'Blender 持续切割工具；与 Maya 多重切割行为有差异。',
 'Blender persistent Loop Cut tool': 'Blender 持续环切工具',
 'Blender persistent Offset Edge Loop Cut tool': 'Blender 持续偏移环切工具',
 'Blender split/custom normals and sharp-edge attributes; sharp flags do not override all custom normals, and split/merge are not Maya persistent normal locks.': '使用 '
                                                                                                                                                                  'Blender '
                                                                                                                                                                  '分离/自定义法向及锐边属性；锐边标记不会覆盖全部自定义法向，分离/合并也不代表 '
                                                                                                                                                                  'Maya '
                                                                                                                                                                  '持续法向锁定。',
 'Blender topology/threshold selection; use Adjust Last Operation for available parameters.': '使用 Blender '
                                                                                              '拓扑/阈值选择；可用参数见“调整上一步操作”。',
 'Blender wildcard names in the current view layer.': '在当前视图层使用 Blender 通配符名称',
 'Bounded one-time deform weights adapter; see Skin weight cleanup design': '有界的一次性变形权重适配；见蒙皮权重清理设计。',
 'Captured object attribute editor not implemented': '尚未实现已捕获对象的属性编辑器',
 'Captured-target data bridge not implemented; active-object data is not substituted': '尚未实现绑定到已捕获目标的数据桥接；不会用活动对象数据替代。',
 'Captured-target material editor not implemented': '尚未实现绑定到已捕获目标的材质编辑器',
 'Captured-target selection transaction not implemented': '尚未实现绑定到已捕获目标的选择事务',
 'Change current 3D View normal overlay length only.': '仅改变当前三维视图法向叠加线的长度。',
 'Changes Euler order while preserving the current local transform; animation curves are not resampled.': '更改欧拉旋转顺序并保留当前局部变换；不会重新采样动画曲线。',
 'Changes current-view-layer visibility; deforming geometry means mesh/curve/surface with enabled deformation modifiers.': '改变当前视图层可见性；变形几何指带有启用的变形修改器的网格、曲线或曲面。',
 'Clear the current Blender selection domain': '清除当前 Blender 选择域',
 'Clears Blender local location/rotation/scale, retaining deltas and parenting.': '清除 Blender 局部位置/旋转/缩放，保留增量变换和父子关系。',
 'Color Blender explicitly marked sharp edges in Edit Mesh; does not isolate hard/soft edges or alter normals.': '在网格编辑模式下为 '
                                                                                                                 'Blender '
                                                                                                                 '显式标记的锐边着色；不隔离硬/软边，也不改变法向。',
 'Complete cleanup selection and options not implemented': '尚未实现完整清理选择及选项',
 'Component-domain detach dispatch not implemented': '尚未实现组件域分离分派',
 'Configure the active Mesh operation; confirmation creates one undo step': '配置活动网格操作；确认后产生一个撤销步骤。',
 'Connect selected compatible endpoints/control rows within the edit object; no Maya tangent-alignment or cross-object rebuild.': '连接编辑对象内部选中且兼容的端点/控制点行；不实现 '
                                                                                                                                  'Maya '
                                                                                                                                  '切线对齐或跨对象重建。',
 'Convert the active Blender color attribute between POINT/CORNER and FLOAT_COLOR/BYTE_COLOR; not Maya color-set representation/per-instance options.': '在 '
                                                                                                                                                        'POINT/CORNER '
                                                                                                                                                        '与 '
                                                                                                                                                        'FLOAT_COLOR/BYTE_COLOR '
                                                                                                                                                        '之间转换活动 '
                                                                                                                                                        'Blender '
                                                                                                                                                        '颜色属性；不实现 '
                                                                                                                                                        'Maya '
                                                                                                                                                        '颜色集表示或逐实例选项。',
 'Converts evaluated Blender data; modifiers and original data may be replaced.': '转换求值后的 Blender 数据；修改器和原始数据可能被替换。',
 'Converts selected Blender mesh elements by containment or selected-region boundary.': '按包含关系或选区边界转换选中的 Blender 网格元素。',
 'Copies named string/number/boolean custom properties from active source to selected editable objects, creating missing keys. Any target non-scalar name collision or override disables the whole action; arrays, connections and Maya typed attributes are excluded.': '将命名的字符串/数值/布尔自定义属性从活动源复制到选中可编辑对象，并创建缺失属性。任一目标存在同名非标量属性或覆盖数据时禁用整个操作；不包含数组、连接及 '
                                                                                                                                                                                                                                                                         'Maya '
                                                                                                                                                                                                                                                                         '类型化属性。',
 'Copies selected editable objects successfully before native deletion; one geometry undo.': '成功复制选中可编辑对象后才执行原生删除；形成一次几何撤销。',
 'Copy/instance choice and Duplicate Special transform settings are not implemented; Duplicate Linked always shares object data': '尚未实现复制/实例选择及特殊复制的变换设置；链接复制始终共享对象数据。',
 'Create a Blender primitive at the 3D Cursor with Blender dimensions, topology and mode rules': '在三维游标处创建 Blender '
                                                                                                 '基本体，遵循 Blender '
                                                                                                 '尺寸、拓扑和模式规则。',
 'Creates a 3 by 3 by 3 cage in object space and offsets its upper region; edit cage control points for further shaping. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '在对象空间创建 '
                                                                                                                                                                                                    '3×3×3 '
                                                                                                                                                                                                    '笼体并偏移其上部；可编辑笼体控制点进一步塑形。参数位于“编辑 '
                                                                                                                                                                                                    '> '
                                                                                                                                                                                                    '调整上一步操作”及原生修改器属性。',
 'Creates a Blender Empty parent and preserves world transforms; Collections are not used as DAG groups.': '创建 Blender '
                                                                                                           '空物体父级并保留世界变换；不使用集合充当 '
                                                                                                           'DAG 组。',
 'Creates a Blender polygon primitive with a level-2 Catmull-Clark modifier; Maya hierarchical subdivision components are not reproduced.': '创建带二级 '
                                                                                                                                            'Catmull-Clark '
                                                                                                                                            '修改器的 '
                                                                                                                                            'Blender '
                                                                                                                                            '多边形基本体；不复现 '
                                                                                                                                            'Maya '
                                                                                                                                            '层级细分组件。',
 'Creates a linked Clouds texture in global coordinates; no UV dependency. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '在全局坐标中创建已链接的云纹理，不依赖 '
                                                                                                                                                      'UV。参数位于“编辑 '
                                                                                                                                                      '> '
                                                                                                                                                      '调整上一步操作”及原生修改器属性。',
 'Creates a native Blender primitive at the 3D Cursor with native dimensions, Z-up and topology.': '在三维游标处创建原生 Blender '
                                                                                                   '基本体，使用原生尺寸、Z '
                                                                                                   '轴向上及拓扑。',
 'Creates the named native Blender object at the 3D Cursor; no Maya construction-node network.': '在三维游标处创建指定原生 Blender '
                                                                                                 '对象；不建立 Maya 构建节点网络。',
 'Creation unavailable': '创建不可用',
 'Current Blender recent-file history': '当前 Blender 最近文件历史',
 'Current Blender viewport overlay; not Maya per-object display. Component indices share one Edit Mesh switch; sharp-edge colors differ from Maya soft-edge display': '控制当前 '
                                                                                                                                                                      'Blender '
                                                                                                                                                                      '视窗叠加，不是 '
                                                                                                                                                                      'Maya '
                                                                                                                                                                      '逐对象显示。组件索引共用一个网格编辑开关；锐边颜色与 '
                                                                                                                                                                      'Maya '
                                                                                                                                                                      '软边显示不同。',
 'Current solid viewport color source toggles VERTEX/MATERIAL; not Maya color-material blend modes.': '在 '
                                                                                                      'VERTEX/MATERIAL '
                                                                                                      '之间切换当前实体视窗的颜色来源，不实现 '
                                                                                                      'Maya 颜色材质混合模式。',
 'Current viewport shading; not Maya per-object polygon display': '控制当前视窗着色，不是 Maya 逐对象多边形显示。',
 'Decimate modifier on the captured Mesh; default ratio 50 percent': '在已捕获网格上使用精简修改器；默认比例为 50%。',
 'Decimate modifier on the captured Mesh; default ratio 50 percent; confirmation applies parameters': '在已捕获网格上使用精简修改器；默认比例为 '
                                                                                                      '50%；确认后应用参数。',
 'Deselect eligible Blender objects or mesh components in the source context': '在源上下文中取消选择符合条件的 Blender 对象或网格组件。',
 'Destructive Blender voxel remeshing using the mesh voxel-size setting; attributes may be lost.': '使用网格体素尺寸设置执行破坏式 '
                                                                                                   'Blender '
                                                                                                   '体素重构；属性可能丢失。',
 'Distributes selected static unparented unconstrained objects with zero delta location along one non-degenerate static standalone curve. Uses persistent native Follow Path constraints; resets base locations and preserves scales. Parent/constraint/modifier/bevel/taper/animation networks are unavailable. Closed splines use non-overlapping parameter fractions.': '沿一条非退化、静态且独立的曲线分布选中的静态对象；对象须无父级、无约束且增量位置为零。使用持续原生跟随路径约束，重置基础位置并保留缩放；不支持父级、约束、修改器、倒角、锥化或动画网络。闭合样条使用不重叠的参数比例。',
 'Dynamic Maya bookmark enumeration failed in the audited capture; fixed actions retained': '审计采集中 Maya '
                                                                                            '动态书签枚举失败；固定操作保留。',
 'Edit Mesh Boolean between selected and unselected face regions; not object operands.': '在选中与未选中面区域之间执行网格编辑布尔，不使用对象作为运算对象。',
 'Edits native curve data. Offset affects 2D output geometry rather than creating an independent Maya offset curve; resolution only changes sampling.': '编辑原生曲线数据。偏移影响二维输出几何，不会创建独立的 '
                                                                                                                                                        'Maya '
                                                                                                                                                        '偏移曲线；分辨率仅改变采样。',
 'Edits only the named Blender viewport/tool setting; no geometry or temporary hold-key emulation.': '仅编辑指定的 Blender '
                                                                                                     '视窗/工具设置；不改变几何，也不模拟临时持键。',
 'Edits scalar custom properties on the active Blender object, not Maya attribute connections or compound attributes.': '编辑活动 '
                                                                                                                        'Blender '
                                                                                                                        '对象的标量自定义属性，不处理 '
                                                                                                                        'Maya '
                                                                                                                        '属性连接或复合属性。',
 'Empty Object Mode only': '仅适用于空选区对象模式',
 'Enables Blender vertex, edge and face domains together; face-corner selection is separate data, not an interactive domain.': '同时启用 '
                                                                                                                               'Blender '
                                                                                                                               '顶点、边与面选择域；面角选择是独立数据，不是交互选择域。',
 'English interface': '英文界面',
 'Enters Blender Curve, Surface or Lattice Edit Mode.': '进入 Blender 曲线、曲面或晶格编辑模式。',
 'Exact Boolean modifier; requires exactly two selected Meshes; originals remain': '精确布尔修改器；要求恰好选中两个网格，原始对象保留。',
 'Exactly two selected meshes; add an Exact Boolean with an explicit operand. Original objects and visibility remain; reverse modifies the other mesh. Modifier evaluation is checked before committing one undo step.': '恰好选中两个网格；添加具有明确运算对象的精确布尔。原始对象及可见性保持；反向操作修改另一个网格。提交一个撤销步骤前检查修改器求值。',
 'Existing Blender Edit Mesh adaptation; native requirements and component-domain scope apply': '使用已有 Blender '
                                                                                                '网格编辑适配；遵循原生要求和组件域范围。',
 'Existing Hypergraph panels require the current panel registry': '现有超级图面板需要当前面板注册表',
 'Existing Object selection required; target identity checked before dispatch': '需要已有对象选区；分派前核验目标身份。',
 'Extracting curves from surface boundaries and isoparms is not implemented': '尚未实现从曲面边界及等参线提取曲线',
 'Factory, user and module workspace registrations require a workspace provider': '出厂、用户及模块工作区注册需要工作区提供器',
 'First create a Curve and enter Edit. Native Draw creates a freehand Bezier fit or Poly spline using native paint settings and error tolerance; it does not create a Maya EP-interpolated NURBS curve. Strokes own confirmation and undo.': '先创建曲线并进入编辑模式。原生绘制按原生绘画设置和误差容限创建手绘贝塞尔拟合或多段线样条，不创建 '
                                                                                                                                                                                                                                             'Maya '
                                                                                                                                                                                                                                             '编辑点插值 '
                                                                                                                                                                                                                                             'NURBS '
                                                                                                                                                                                                                                             '曲线。每个笔画自行负责确认与撤销。',
 'First create a Curve and enter Edit; choose NURBS for BPoint CV extension or Bezier for anchor/handle editing. Native Pen extends selected spline endpoints; no automatic new-object lifecycle, EP interpolation or arc solver.': '先创建曲线并进入编辑模式；NURBS '
                                                                                                                                                                                                                                    '用于 '
                                                                                                                                                                                                                                    'BPoint '
                                                                                                                                                                                                                                    '控制顶点延伸，贝塞尔用于锚点/控制柄编辑。原生钢笔延伸选中样条端点，不提供自动新对象生命周期、编辑点插值或圆弧解算器。',
 'Frame selected items in the source viewport': '在源视窗框显选中项',
 'Frame the source Blender viewport': '框显源 Blender 视窗内容',
 'Frames selected Blender elements across quad regions; child handling follows native selection.': '在四视图区域中框显选中的 '
                                                                                                   'Blender '
                                                                                                   '元素；子级处理遵循原生选择。',
 'Grow with Blender mesh topology traversal': '按 Blender 网格拓扑遍历扩大选区',
 'Hierarchy prefix naming and target scope adaptation not implemented': '尚未适配层级前缀命名及目标范围',
 "Higher domains select incident components; lower domains retain the source components' vertices or edges.": '较高选择域选取相邻组件；较低选择域保留源组件的顶点或边。',
 'Hotbox unavailable': '热盒不可用',
 'Image plane actions require the live source camera': '图像平面操作需要实时源相机',
 'Image plane members require the live source camera': '图像平面成员需要实时源相机',
 'Interactive control-point extrusion; not a prescribed-length extension or a profile swept along a path.': '交互式控制点挤出；不是指定长度的延伸，也不是沿路径扫掠轮廓。',
 'Interactive deformer membership tool not implemented; assigning vertex weights is a different action': '尚未实现交互式变形器成员工具；分配顶点权重是另一项操作。',
 'Invert the current Blender selection domain': '反选当前 Blender 选择域',
 'Join selected editable Meshes into the active Mesh': '将选中可编辑网格合并到活动网格',
 'Join selected editable meshes into the active object; uses its transform and material slots.': '将选中可编辑网格合并到活动对象；使用其变换与材质槽。',
 'Linear native taper; not independent Maya start/end flare factors. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '使用原生线性锥化，不提供 '
                                                                                                                                                'Maya '
                                                                                                                                                '独立起始/末端扩张系数。参数位于“编辑 '
                                                                                                                                                '> '
                                                                                                                                                '调整上一步操作”及原生修改器属性。',
 'Link active mesh material slots to other selected meshes; no spatial matching of Maya per-face shading sets.': '将活动网格材质槽链接到其他选中网格；不执行 '
                                                                                                                 'Maya '
                                                                                                                 '逐面着色集的空间匹配。',
 'Live camera instances; paintEffects/buildCartoonMenu.mel:68-88': '实时相机实例；paintEffects/buildCartoonMenu.mel:68-88',
 'Live pfxToon nodes after two fixed actions; paintEffects/buildCartoonMenu.mel:47-64': '两个固定操作之后的实时 pfxToon '
                                                                                        '节点；paintEffects/buildCartoonMenu.mel:47-64',
 'M1-P08: Maya state not adapted': 'M1-P08：尚未适配 Maya 状态',
 'M1-P08: Maya tool adapter pending': 'M1-P08：Maya 工具适配尚待实现',
 'M2-multi-component: Not implemented': 'M2-multi-component：尚未实现',
 'M2-vertex-face: Not implemented': 'M2-vertex-face：尚未实现',
 'M2c-P01: Maya interactive polygon creation adapter not implemented': 'M2c-P01：尚未实现 Maya 交互式多边形创建适配',
 'M2c-P02.cone: Read-only creation parameters not implemented': 'M2c-P02.cone：尚未实现只读创建参数',
 'M2c-P02.cube: Read-only creation parameters not implemented': 'M2c-P02.cube：尚未实现只读创建参数',
 'M2c-P02.cylinder: Read-only creation parameters not implemented': 'M2c-P02.cylinder：尚未实现只读创建参数',
 'M2c-P02.disc: Read-only creation parameters not implemented': 'M2c-P02.disc：尚未实现只读创建参数',
 'M2c-P02.gear: Read-only parameters not implemented': 'M2c-P02.gear：尚未实现只读参数',
 'M2c-P02.helix: Read-only parameters not implemented': 'M2c-P02.helix：尚未实现只读参数',
 'M2c-P02.pipe: Read-only parameters not implemented': 'M2c-P02.pipe：尚未实现只读参数',
 'M2c-P02.plane: Read-only creation parameters not implemented': 'M2c-P02.plane：尚未实现只读创建参数',
 'M2c-P02.platonic: Read-only parameters not implemented': 'M2c-P02.platonic：尚未实现只读参数',
 'M2c-P02.polygon: Read-only creation parameters not implemented': 'M2c-P02.polygon：尚未实现只读创建参数',
 'M2c-P02.prism: Read-only parameters not implemented': 'M2c-P02.prism：尚未实现只读参数',
 'M2c-P02.pyramid: Read-only parameters not implemented': 'M2c-P02.pyramid：尚未实现只读参数',
 'M2c-P02.quad_draw: Read-only parameters not implemented': 'M2c-P02.quad_draw：尚未实现只读参数',
 'M2c-P02.soccer_ball: Read-only parameters not implemented': 'M2c-P02.soccer_ball：尚未实现只读参数',
 'M2c-P02.sphere: Read-only creation parameters not implemented': 'M2c-P02.sphere：尚未实现只读创建参数',
 'M2c-P02.spherical_harmonics: Read-only parameters not implemented': 'M2c-P02.spherical_harmonics：尚未实现只读参数',
 'M2c-P02.super_ellipse: Read-only parameters not implemented': 'M2c-P02.super_ellipse：尚未实现只读参数',
 'M2c-P02.torus: Read-only creation parameters not implemented': 'M2c-P02.torus：尚未实现只读创建参数',
 'M2c-P02.ultra_shape: Read-only parameters not implemented': 'M2c-P02.ultra_shape：尚未实现只读参数',
 'M2c-P03.QuadDraw: Empty-selection Poly Build startup transaction not implemented': 'M2c-P03.QuadDraw：尚未实现空选区多边形构建工具的启动事务',
 'M2c-P03.gear: Maya creation workflow not implemented': 'M2c-P03.gear：尚未实现 Maya 创建工作流',
 'M2c-P03.helix: Maya creation workflow not implemented': 'M2c-P03.helix：尚未实现 Maya 创建工作流',
 'M2c-P03.pipe: Maya creation workflow not implemented': 'M2c-P03.pipe：尚未实现 Maya 创建工作流',
 'M2c-P03.polygon_display_all.border_edges: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.border_edges：尚未实现 '
                                                                                     'Maya 创建工作流',
 'M2c-P03.polygon_display_all.face_centers: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.face_centers：尚未实现 '
                                                                                     'Maya 创建工作流',
 'M2c-P03.polygon_display_all.face_normals: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.face_normals：尚未实现 '
                                                                                     'Maya 创建工作流',
 'M2c-P03.polygon_display_all.hidden_triangles: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.hidden_triangles：尚未实现 '
                                                                                         'Maya 创建工作流',
 'M2c-P03.polygon_display_all.reset: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.reset：尚未实现 '
                                                                              'Maya 创建工作流',
 'M2c-P03.polygon_display_all.texture_border_edges: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.texture_border_edges：尚未实现 '
                                                                                             'Maya 创建工作流',
 'M2c-P03.polygon_display_all.vertex_normals: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.vertex_normals：尚未实现 '
                                                                                       'Maya 创建工作流',
 'M2c-P03.polygon_display_all.vertices: Maya creation workflow not implemented': 'M2c-P03.polygon_display_all.vertices：尚未实现 '
                                                                                 'Maya 创建工作流',
 'M2c-P03.soccer_ball: Maya creation workflow not implemented': 'M2c-P03.soccer_ball：尚未实现 Maya 创建工作流',
 'M2c-P03.spherical_harmonics: Maya creation workflow not implemented': 'M2c-P03.spherical_harmonics：尚未实现 Maya 创建工作流',
 'M2c-P03.super_ellipse: Maya creation workflow not implemented': 'M2c-P03.super_ellipse：尚未实现 Maya 创建工作流',
 'M2c-P03.svg: Maya creation workflow not implemented': 'M2c-P03.svg：尚未实现 Maya 创建工作流',
 'M2c-P03.ultra_shape: Maya creation workflow not implemented': 'M2c-P03.ultra_shape：尚未实现 Maya 创建工作流',
 'M2c-P04.exit_on_completion: Interactive creation workflow not implemented; preferences unchanged': 'M2c-P04.exit_on_completion：尚未实现交互式创建工作流；偏好设置保持不变',
 'M2c-P04.interactive_creation: Interactive creation workflow not implemented; preferences unchanged': 'M2c-P04.interactive_creation：尚未实现交互式创建工作流；偏好设置保持不变',
 'M2d-P02.Cleanup: Whole-object cleanup parameters are not implemented; individual Edit cleanup actions remain in Mesh menus': 'M2d-P02.Cleanup：尚未实现整个对象的清理参数；单项编辑清理操作仍在网格菜单内',
 'M2d-P02.ObjectExtrude: Whole-mesh extrusion deferred': 'M2d-P02.ObjectExtrude：整个网格的挤出操作暂缓开发',
 'M2d-P02.ObjectFillHoles: Whole-mesh transaction deferred': 'M2d-P02.ObjectFillHoles：整个网格的操作事务暂缓开发',
 'M2d-P02.Retopologize: Target-pinned QuadriFlow confirmation not implemented; native entry remains in Mesh menu': 'M2d-P02.Retopologize：尚未实现锁定目标的 '
                                                                                                                   'QuadriFlow '
                                                                                                                   '确认流程；原生入口仍在网格菜单内',
 'M2d-P02.booleans.cut_out.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.cut_out.Options：尚未实现专用参数',
 'M2d-P02.booleans.difference.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.difference.Options：尚未实现专用参数',
 'M2d-P02.booleans.difference_reverse.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.difference_reverse.Options：尚未实现专用参数',
 'M2d-P02.booleans.hole_punch.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.hole_punch.Options：尚未实现专用参数',
 'M2d-P02.booleans.intersection.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.intersection.Options：尚未实现专用参数',
 'M2d-P02.booleans.slice.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.slice.Options：尚未实现专用参数',
 'M2d-P02.booleans.split_edges.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.split_edges.Options：尚未实现专用参数',
 'M2d-P02.booleans.union.Options: Dedicated parameters not implemented': 'M2d-P02.booleans.union.Options：尚未实现专用参数',
 'M2d-P02.combine.Options: Dedicated parameters not implemented': 'M2d-P02.combine.Options：尚未实现专用参数',
 'M2d-P02.connect.Options: Dedicated parameters not implemented': 'M2d-P02.connect.Options：尚未实现专用参数',
 'M2d-P02.connect: Object adaptation not implemented': 'M2d-P02.connect：尚未实现对象级适配',
 'M2d-P02.crease.Options: Dedicated parameters not implemented': 'M2d-P02.crease.Options：尚未实现专用参数',
 'M2d-P02.crease: Object adaptation not implemented': 'M2d-P02.crease：尚未实现对象级适配',
 'M2d-P02.mapping.automatic.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.automatic.Options：尚未实现专用参数',
 'M2d-P02.mapping.automatic: Object adaptation not implemented': 'M2d-P02.mapping.automatic：尚未实现对象级适配',
 'M2d-P02.mapping.camera.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.camera.Options：尚未实现专用参数',
 'M2d-P02.mapping.camera: Object adaptation not implemented': 'M2d-P02.mapping.camera：尚未实现对象级适配',
 'M2d-P02.mapping.cylindrical.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.cylindrical.Options：尚未实现专用参数',
 'M2d-P02.mapping.cylindrical: Object adaptation not implemented': 'M2d-P02.mapping.cylindrical：尚未实现对象级适配',
 'M2d-P02.mapping.normal.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.normal.Options：尚未实现专用参数',
 'M2d-P02.mapping.normal: Object adaptation not implemented': 'M2d-P02.mapping.normal：尚未实现对象级适配',
 'M2d-P02.mapping.planar.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.planar.Options：尚未实现专用参数',
 'M2d-P02.mapping.planar: Object adaptation not implemented': 'M2d-P02.mapping.planar：尚未实现对象级适配',
 'M2d-P02.mapping.spherical.Options: Dedicated parameters not implemented': 'M2d-P02.mapping.spherical.Options：尚未实现专用参数',
 'M2d-P02.mapping.spherical: Object adaptation not implemented': 'M2d-P02.mapping.spherical：尚未实现对象级适配',
 'M2d-P02.offset_loop.Options: Dedicated parameters not implemented': 'M2d-P02.offset_loop.Options：尚未实现专用参数',
 'M2d-P02.polygon_display.border_edges: Object adaptation not implemented': 'M2d-P02.polygon_display.border_edges：尚未实现对象级适配',
 'M2d-P02.polygon_display.face_centers: Object adaptation not implemented': 'M2d-P02.polygon_display.face_centers：尚未实现对象级适配',
 'M2d-P02.polygon_display.face_normals: Object adaptation not implemented': 'M2d-P02.polygon_display.face_normals：尚未实现对象级适配',
 'M2d-P02.polygon_display.hidden_triangles: Object adaptation not implemented': 'M2d-P02.polygon_display.hidden_triangles：尚未实现对象级适配',
 'M2d-P02.polygon_display.reset: Object adaptation not implemented': 'M2d-P02.polygon_display.reset：尚未实现对象级适配',
 'M2d-P02.polygon_display.texture_border_edges: Object adaptation not implemented': 'M2d-P02.polygon_display.texture_border_edges：尚未实现对象级适配',
 'M2d-P02.polygon_display.vertex_normals: Object adaptation not implemented': 'M2d-P02.polygon_display.vertex_normals：尚未实现对象级适配',
 'M2d-P02.polygon_display.vertices: Object adaptation not implemented': 'M2d-P02.polygon_display.vertices：尚未实现对象级适配',
 'M2d-P02.project_curve.Options: Dedicated parameters not implemented': 'M2d-P02.project_curve.Options：尚未实现专用参数',
 'M2d-P02.project_curve: Object adaptation not implemented': 'M2d-P02.project_curve：尚未实现对象级适配',
 'M2d-P02.quad_draw.Options: Dedicated parameters not implemented': 'M2d-P02.quad_draw.Options：尚未实现专用参数',
 'M2d-P02.quadrangulate.Options: Dedicated parameters not implemented': 'M2d-P02.quadrangulate.Options：尚未实现专用参数',
 'M2d-P02.quadrangulate: Object adaptation not implemented': 'M2d-P02.quadrangulate：尚未实现对象级适配',
 'M2d-P02.separate: Object adaptation not implemented': 'M2d-P02.separate：尚未实现对象级适配',
 'M2d-P02.split_projected.Options: Dedicated parameters not implemented': 'M2d-P02.split_projected.Options：尚未实现专用参数',
 'M2d-P02.split_projected: Object adaptation not implemented': 'M2d-P02.split_projected：尚未实现对象级适配',
 'M2d-P02.subdiv_proxy.Options: Dedicated parameters not implemented': 'M2d-P02.subdiv_proxy.Options：尚未实现专用参数',
 'M2d-P02.subdiv_proxy: Object adaptation not implemented': 'M2d-P02.subdiv_proxy：尚未实现对象级适配',
 'M2d-P02.transfer_order: Object adaptation not implemented': 'M2d-P02.transfer_order：尚未实现对象级适配',
 'M2d-P02.triangulate: Object adaptation not implemented': 'M2d-P02.triangulate：尚未实现对象级适配',
 'M2d-P02.unsmooth.Options: Dedicated parameters not implemented': 'M2d-P02.unsmooth.Options：尚未实现专用参数',
 'M2d-P02.unsmooth: Object adaptation not implemented': 'M2d-P02.unsmooth：尚未实现对象级适配',
 'M2d-P03.DeleteVertex: Maya vertex topology cleanup adapter not implemented': 'M2d-P03.DeleteVertex：尚未实现 Maya '
                                                                               '顶点拓扑清理适配',
 'M2d-P03.FaceBoundaryBevel: Face boundary selection and native bevel transaction not implemented': 'M2d-P03.FaceBoundaryBevel：尚未实现面边界选择与原生倒角事务',
 'M2d-P03.FlipTriangleEdge: Dedicated triangle-edge eligibility adapter not implemented': 'M2d-P03.FlipTriangleEdge：尚未实现专用三角形边适用性检查',
 'M2d-P03.VertexExtrude: Maya vertex width/length/divisions adapter not implemented': 'M2d-P03.VertexExtrude：尚未适配 Maya '
                                                                                      '顶点挤出的宽度、长度和细分参数',
 'M2d-P03.WedgeFace: Selected-edge pivot wedge adapter not implemented': 'M2d-P03.WedgeFace：尚未实现以选中边为枢轴的楔形挤出适配',
 'M2d-P04.ObjectSculpt: Sculpt context transaction deferred': 'M2d-P04.ObjectSculpt：雕刻上下文事务暂缓开发',
 'M2d-P04.TargetWeld / M3-P-TOOLS.MergeVertexTool: Target Weld and boundary pairing adapter not implemented': 'M2d-P04.TargetWeld '
                                                                                                              '/ '
                                                                                                              'M3-P-TOOLS.MergeVertexTool：尚未实现目标焊接和边界配对适配',
 'M2d-P04.TargetWeld: Full target weld tool deferred': 'M2d-P04.TargetWeld：完整目标焊接工具暂缓开发',
 'M2d-P04.append: Dedicated tool parameters not implemented': 'M2d-P04.append：尚未实现专用工具参数',
 'M2d-P04.knife: Dedicated tool parameters not implemented': 'M2d-P04.knife：尚未实现专用工具参数',
 'M2d-P04.loopcut: Dedicated tool parameters not implemented': 'M2d-P04.loopcut：尚未实现专用工具参数',
 'M2d-P04.sculpt: Dedicated tool parameters not implemented': 'M2d-P04.sculpt：尚未实现专用工具参数',
 'M2d-P04.weld: Dedicated tool parameters not implemented': 'M2d-P04.weld：尚未实现专用工具参数',
 'M2d-P05.ReversePropagate: Reverse and propagate transaction not implemented': 'M2d-P05.ReversePropagate：尚未实现反转与传播事务',
 'M2d-P05.angle.Options: Object sharpness parameters not implemented': 'M2d-P05.angle.Options：尚未实现对象级锐度参数',
 'M2d-P05.angle: Object edge-display/sharpness transaction not implemented': 'M2d-P05.angle：尚未实现对象级边显示/锐度事务',
 'M2d-P05.display: Object edge-display/sharpness transaction not implemented': 'M2d-P05.display：尚未实现对象级边显示/锐度事务',
 'M2d-P05.harden: Object edge-display/sharpness transaction not implemented': 'M2d-P05.harden：尚未实现对象级边显示/锐度事务',
 'M2d-P05.soften: Object edge-display/sharpness transaction not implemented': 'M2d-P05.soften：尚未实现对象级边显示/锐度事务',
 'M2d-P06.MergeBorderEdges: Maya boundary-edge pairing adapter not implemented; Merge by Distance is not equivalent': 'M2d-P06.MergeBorderEdges：尚未实现 '
                                                                                                                      'Maya '
                                                                                                                      '边界边配对适配；按距离合并并非等价操作',
 'M2d-P06.Options: Maya parameter adapter not implemented; main action is not invoked': 'M2d-P06.Options：尚未适配 Maya '
                                                                                        '参数；不会执行正文操作',
 'M2d-UV.PlanarX: UV work is postponed': 'M2d-UV.PlanarX：UV 工作暂缓开发',
 'M2d-UV.PlanarY: UV work is postponed': 'M2d-UV.PlanarY：UV 工作暂缓开发',
 'M2d-UV.PlanarZ: UV work is postponed': 'M2d-UV.PlanarZ：UV 工作暂缓开发',
 'M3-P-MESH.cut_out: Maya Boolean mode not implemented': 'M3-P-MESH.cut_out：尚未实现 Maya 布尔模式',
 'M3-P-MESH.hole_punch: Maya Boolean mode not implemented': 'M3-P-MESH.hole_punch：尚未实现 Maya 布尔模式',
 'M3-P-MESH.slice: Maya Boolean mode not implemented': 'M3-P-MESH.slice：尚未实现 Maya 布尔模式',
 'M3-P-MESH.split_edges: Maya Boolean mode not implemented': 'M3-P-MESH.split_edges：尚未实现 Maya 布尔模式',
 'Matches selected editable objects to the active object in world space; partial matches decompose shear.': '在世界空间将选中可编辑对象匹配到活动对象；部分匹配会分解切变。',
 'Maya command adapter not implemented': '尚未实现 Maya 命令适配',
 'Maya component semantics not safely adapted; retained placeholder': '尚未安全适配 Maya 组件语义；保留占位。',
 'Maya contiguous-edge options are not adapted': '尚未适配 Maya 连续相邻边选项',
 'Maya control state not adapted': '尚未适配 Maya 控制状态',
 'Maya dependency-graph input/output operations are not adapted': '尚未适配 Maya 依赖图输入/输出操作',
 'Maya edge and vertex deletion semantics not implemented': '尚未实现 Maya 边与顶点删除语义',
 'Maya live-surface selection and snapping workflow not implemented': '尚未实现 Maya 实时曲面选择与吸附工作流',
 'Maya menu requires optional meshReorder plugin; Blender vertex-order adapter not implemented': 'Maya 菜单需要可选 '
                                                                                                 'meshReorder 插件；尚未实现 '
                                                                                                 'Blender 顶点顺序适配。',
 'Maya option parameters are not adapted; this does not execute the main action': '尚未适配 Maya 选项参数；不会执行正文操作。',
 'Maya parameter adapter not implemented; main action is not invoked': '尚未适配 Maya 参数；不会执行正文操作。',
 'Maya search/replace naming operation and target scope adaptation not implemented': '尚未适配 Maya 名称搜索/替换操作及目标范围',
 'Maya selection operation is not adapted': '尚未适配 Maya 选择操作',
 'Maya surface remesh is not equivalent to voxel-volume reconstruction': 'Maya 曲面重构不等同于体素体积重建',
 'Maya toggle not implemented; existing Blender bounds commands are one-way': '尚未实现 Maya 切换功能；现有 Blender 边界命令为单向设置。',
 'Maya transformation options are not adapted; main action is not invoked': '尚未适配 Maya 变换选项；不会执行正文操作。',
 'Mesh Deform cage binding; one closed selected cage must enclose the active source. Not a proximity-distance wrap algorithm. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '使用网格形变笼绑定；一个选中的闭合笼体必须包围活动源对象，不采用近距包裹算法。参数位于“编辑 '
                                                                                                                                                                                                         '> '
                                                                                                                                                                                                         '调整上一步操作”及原生修改器属性。',
 'Mirror modifier on the captured Mesh; default X bisect and merge': '在已捕获网格上使用镜像修改器；默认沿 X 轴切分并合并。',
 'Mirror modifier on the captured Mesh; default X bisect and merge; confirmation applies parameters': '在已捕获网格上使用镜像修改器；默认沿 '
                                                                                                      'X '
                                                                                                      '轴切分并合并；确认后应用参数。',
 'Named bookmarks require the source camera': '命名书签需要源相机',
 'Native Blender Text at the 3D Cursor; no Maya Type construction network': '在三维游标处创建原生 Blender 文本；不建立 Maya 文字构建网络。',
 'Native Blender active key / vertex group / lattice operation; indexed topology, group naming and weight semantics differ from Maya deformer nodes.': '使用原生 '
                                                                                                                                                       'Blender '
                                                                                                                                                       '活动形态键/顶点组/晶格操作；索引拓扑、组命名和权重语义与 '
                                                                                                                                                       'Maya '
                                                                                                                                                       '变形器节点有差异。',
 'Native Blender control-point operation; NURBS parameterization follows Blender.': '使用原生 Blender 控制点操作；NURBS 参数化遵循 '
                                                                                    'Blender。',
 'Native Blender custom-normal interaction; not Maya per-vertex normal locking.': '使用原生 Blender 自定义法向交互；不是 Maya '
                                                                                  '逐顶点法向锁定。',
 'Native Blender interaction/parameters; Spin uses the current Cursor and axis, not a Maya selected-edge pivot.': '使用原生 '
                                                                                                                  'Blender '
                                                                                                                  '交互与参数；旋绕使用当前游标和轴，而不是 '
                                                                                                                  'Maya '
                                                                                                                  '选中边枢轴。',
 'Native Blender macro: Esc may cancel only movement while retaining new geometry; one Undo removes the operation. Modal launch is not recorded in Recent.': '原生 '
                                                                                                                                                             'Blender '
                                                                                                                                                             '宏：Esc '
                                                                                                                                                             '可能仅取消移动而保留新几何；一次撤销移除该操作。模态启动不记入最近命令。',
 'Native Blender modal operation; input and cancellation belong to the child operator, not the opening menu.': '原生 '
                                                                                                               'Blender '
                                                                                                               '模态操作；输入和取消由子操作负责，而非打开它的菜单。',
 'Native Blender object and defaults; Maya option parameters are not shared': '使用原生 Blender 对象和默认值；不共享 Maya 选项参数。',
 'Native Blender operation': '原生 Blender 操作',
 'Native Hook with selected point membership, a new empty controller and 0.25 world Z offset; not the complete Maya Cluster node system.': '原生钩挂使用选中点作为成员，创建新空物体控制器并沿世界 '
                                                                                                                                           'Z '
                                                                                                                                           '轴偏移 '
                                                                                                                                           '0.25；不是完整的 '
                                                                                                                                           'Maya '
                                                                                                                                           '簇节点系统。',
 'Native Laplacian smoothing, volume preservation disabled. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '使用原生拉普拉斯平滑，禁用体积保持。参数位于“编辑 '
                                                                                                                                       '> '
                                                                                                                                       '调整上一步操作”及原生修改器属性。',
 'Native Link Object Data replaces compatible selected targets with the active source datablock. Targets become linked instances; object transforms and existing modifiers remain.': '原生链接对象数据将兼容的选中目标替换为活动源数据块。目标成为链接实例，对象变换及已有修改器保留。',
 'Native Smooth by Angle geometry-node modifier; requires the bundled Essentials asset.': '原生按角度平滑几何节点修改器；需要随包提供的 '
                                                                                          'Essentials 资产。',
 'Native bind with Smooth Only initially enabled for observable smoothing; disable it in modifier settings for corrective deformation. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '原生绑定初始开启“仅平滑”以观察平滑结果；若需矫正形变，可在修改器设置中关闭。参数位于“编辑 '
                                                                                                                                                                                                                  '> '
                                                                                                                                                                                                                  '调整上一步操作”及原生修改器属性。',
 'Native four-sided cone at the 3D Cursor; Blender dimensions and topology': '在三维游标处创建原生四边锥体；使用 Blender 尺寸与拓扑。',
 'Native full rotation of a selected NURBS control row about world origin/Z; select a valid open row. Adjust Last Operation exposes axis/center.': '将选中 '
                                                                                                                                                   'NURBS '
                                                                                                                                                   '控制点行绕世界原点/Z '
                                                                                                                                                   '轴旋转一周；需要有效的开放控制点行。“调整上一步操作”提供轴和中心参数。',
 'Native iterative vertex smoothing. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '使用原生迭代顶点平滑。参数位于“编辑 '
                                                                                                                '> '
                                                                                                                '调整上一步操作”及原生修改器属性。',
 'Native mesh smooth flags and angle-derived sharp edges; independent of Essentials assets.': '使用原生网格平滑标记和按角度生成的锐边；不依赖 '
                                                                                              'Essentials 资产。',
 'Native modal duplicate/move. Cancel may retain the duplicate while cancelling movement; one undo removes it.': '原生模态复制/移动。取消可能停止移动但保留副本；一次撤销移除副本。',
 'Native parameter popup returns CANCELLED even when opened; UI-only, not Recent. F9 remains Vertex.': '原生参数弹窗即使已打开也返回 '
                                                                                                       'CANCELLED；仅显示界面，不记入最近命令。F9 '
                                                                                                       '仍用于顶点选择。',
 'Native spherical coordinate cast, radius 1. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '原生球形坐标投射，半径为 '
                                                                                                                         '1。参数位于“编辑 '
                                                                                                                         '> '
                                                                                                                         '调整上一步操作”及原生修改器属性。',
 'Native stretch and volume compensation; Maya squash bounds differ. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '原生拉伸与体积补偿；与 '
                                                                                                                                                'Maya '
                                                                                                                                                '挤压边界有差异。参数位于“编辑 '
                                                                                                                                                '> '
                                                                                                                                                '调整上一步操作”及原生修改器属性。',
 'Native surface shell thickness; not Maya Deform Solidify rigid-region preservation. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '原生曲面壳层厚度；不实现 '
                                                                                                                                                                 'Maya '
                                                                                                                                                                 '实体化变形器的刚性区域保持。参数位于“编辑 '
                                                                                                                                                                 '> '
                                                                                                                                                                 '调整上一步操作”及原生修改器属性。',
 'Native triangular prism at the 3D Cursor; Blender dimensions and topology': '在三维游标处创建原生三棱柱；使用 Blender 尺寸与拓扑。',
 'No recent commands in this session': '本次会话尚无最近命令',
 'Object-mode entry to Blender Vertex Paint. Leaves the supported modeling-hotbox context; paint tools/keymaps and the complete Maya painting workflow are not adapted.': '从对象模式进入 '
                                                                                                                                                                          'Blender '
                                                                                                                                                                          '顶点绘制，离开已支持的建模热盒上下文；绘制工具/键位及完整 '
                                                                                                                                                                          'Maya '
                                                                                                                                                                          '绘制工作流尚未适配。',
 'Object/component similarity dispatch not implemented; vertex-normal filtering is only one criterion': '尚未实现对象/组件相似选择分派；顶点法向过滤仅是一项条件。',
 'One Blender Edit Mesh switch shows selected vertex/edge/face indices together; indices are not persistent Maya component identities.': '一个 '
                                                                                                                                         'Blender '
                                                                                                                                         '网格编辑开关同时显示选中的顶点/边/面索引；这些索引不是持久的 '
                                                                                                                                         'Maya '
                                                                                                                                         '组件身份。',
 'One configured Blender normal modifier; does not provide Maya normal lock state.': '一个已配置的 Blender 法向修改器；不提供 Maya '
                                                                                     '法向锁定状态。',
 'One explicit Blender cleanup operation; does not implement all Maya Cleanup checks.': '一项明确的 Blender 清理操作；不实现全部 Maya '
                                                                                        '清理检查。',
 'Open a new Blender editor window; existing layouts stay unchanged': '打开新的 Blender 编辑器窗口；已有布局保持不变。',
 'Open independent parameters without modifying weights': '打开独立参数，不修改权重。',
 'Opens the native active-item naming panel (space_topbar.py:559).': '打开原生活动项命名面板（space_topbar.py:559）。',
 'Operation unavailable': '操作不可用',
 'Orthographic camera members require the current scene': '正交相机成员需要当前场景',
 'Panel types and instances require the current panel registry': '面板类型和实例需要当前面板注册表',
 'Pastes Blender object-buffer data; not component or animation clipboard.': '粘贴 Blender 对象缓冲数据；不处理组件或动画剪贴板。',
 'Perspective camera members require the current scene': '透视相机成员需要当前场景',
 'Project wire/boundary edges of selected non-Edit objects through the active view; does not create Maya curve-on-mesh dependency data.': '通过活动视图投射选中非编辑对象的线框/边界边；不创建 '
                                                                                                                                          'Maya '
                                                                                                                                          '网格上曲线的依赖数据。',
 'Quick select sets require current scene sets': '快速选择集需要当前场景集合',
 'Recent files require current user history': '最近文件需要当前用户历史',
 'Recent increments require current file history': '最近增量版本需要当前文件历史',
 'Recent projects require current user history': '最近项目需要当前用户历史',
 'Removes native Curve modifiers scene-wide as the adapted wire family. Curve objects remain, including ordinary geometry and shared deform targets. Animated/driven/NLA or override objects are unavailable; surviving modifiers retain their original instances during rollback.': '在整个场景移除作为线变形适配的原生曲线修改器。曲线对象保留，包括普通几何和共享变形目标。带动画/驱动器/NLA '
                                                                                                                                                                                                                                                                                     '或覆盖数据的对象不可用；回滚时保留其余修改器的原始实例。',
 'Removes native Hook modifiers scene-wide as the bounded Blender cluster-like influence adaptation. Influence objects and vertex groups remain; arbitrary Maya cluster nodes are not deleted. Animated/driven/NLA or override objects are unavailable; surviving modifiers retain their original instances during rollback.': '在整个场景移除作为有界类簇影响适配的原生钩挂修改器。影响对象和顶点组保留，不删除任意 '
                                                                                                                                                                                                                                                                                                                               'Maya '
                                                                                                                                                                                                                                                                                                                               '簇节点。带动画/驱动器/NLA '
                                                                                                                                                                                                                                                                                                                               '或覆盖数据的对象不可用；回滚时保留其余修改器的原始实例。',
 'Removes native Lattice modifiers scene-wide. Cage objects remain to preserve other references and shared ownership. Animated/driven/NLA or override objects are unavailable; surviving modifiers retain their original instances during rollback.': '在整个场景移除原生晶格修改器。笼体对象保留，以保护其他引用和共享所有权。带动画/驱动器/NLA '
                                                                                                                                                                                                                                                      '或覆盖数据的对象不可用；回滚时保留其余修改器的原始实例。',
 'Removes native Simple Deform and Wave modifiers used by the adapted Maya nonlinear actions. Unrelated modifiers and influence objects remain. Animated/driven/NLA or override objects are unavailable; surviving modifiers retain their original instances during rollback.': '移除用于适配 '
                                                                                                                                                                                                                                                                                'Maya '
                                                                                                                                                                                                                                                                                '非线性操作的原生简易形变与波浪修改器。无关修改器和影响对象保留。带动画/驱动器/NLA '
                                                                                                                                                                                                                                                                                '或覆盖数据的对象不可用；回滚时保留其余修改器的原始实例。',
 'Removes selected Empty parents, preserving child world transforms and the surviving parent chain.': '移除选中空物体父级，保留子级世界变换与其余父级链。',
 'Renderer entries require the current renderer registry': '渲染器条目需要当前渲染器注册表',
 'Repeats a confirmed native Duplicate and Move as the last redoable operation; unavailable after other operations.': '重复已确认的原生复制并移动，作为上一步可重做操作；执行其他操作后不可用。',
 'Repeats native operator history, separate from AxisMeld Recent. Maya G already uses the identical native Screen repeat_last binding, which remains in place.': '重复原生操作历史，与 '
                                                                                                                                                                 'AxisMeld '
                                                                                                                                                                 '最近命令分开。Maya '
                                                                                                                                                                 'G '
                                                                                                                                                                 '已使用相同的原生 '
                                                                                                                                                                 'Screen '
                                                                                                                                                                 'repeat_last '
                                                                                                                                                                 '绑定，保持该绑定。',
 'Replaces each modifier-free editable mesh with its local bounding box, preserving object transforms. Modifier stacks must be applied first.': '将每个无修改器的可编辑网格替换为其局部包围盒，保留对象变换；必须先应用修改器堆栈。',
 'Requires Object Mode': '需要对象模式',
 'Requires an existing Mesh selection; pointer preselection is not supported for this action': '需要已有网格选区；该操作不支持鼠标指针预选。',
 'Requires modeling view': '需要建模视图',
 'Requires the captured target to be the selected active Object; selection is not changed on open': '已捕获目标必须为已选中的活动对象；打开时不改变选区。',
 'Requires the matching selected Mesh component domain': '需要匹配的已选中网格组件域',
 'Reverse native selected spline direction; surface U/V are not independent Maya direction modes.': '反转原生选中样条方向；曲面 U/V '
                                                                                                    '不是 Maya 独立方向模式。',
 'Rotate selected manifold edges shared by exactly two faces; Blender edge-spin direction.': '旋转选中且恰好由两个面共享的流形边；使用 '
                                                                                             'Blender 边旋绕方向。',
 'Rotate/reverse selected face-corner color data, not UV coordinates.': '旋转/反转选中面角颜色数据，不修改 UV 坐标。',
 'Rotation-order dialog adaptation not implemented': '尚未适配旋转顺序对话框',
 'Saved layouts are registered configuration instances': '已保存布局是注册的配置实例',
 'Scene is not editable': '场景不可编辑',
 'Scene material instances; startup/buildShaderMenus.mel:342,546-549': '场景材质实例；startup/buildShaderMenus.mel:342,546-549',
 'Select Mesh Objects': '请选择网格对象',
 'Select Mesh with faces': '请选择具有面的网格',
 'Select all in the current Blender selection domain': '全选当前 Blender 选择域',
 'Select editable Mesh': '请选择可编辑网格',
 'Select editable Meshes': '请选择可编辑网格',
 'Select editable items': '请选择可编辑项',
 'Select one Mesh domain': '请选择单一网格组件域',
 'Select source + target': '请选择源对象与目标',
 'Select valid targets': '请选择有效目标',
 'Selected Object display only; no preselection commit': '仅改变已选中对象的显示；不提交预选。',
 'Selected Object hierarchy only; no preselection commit': '仅处理已选中对象的层级；不提交预选。',
 'Selected mesh vertices become anchors; at least one unselected vertex is required. Anchors move on local Z after binding. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '选中网格顶点成为锚点；至少需要一个未选中顶点。绑定后锚点沿局部 '
                                                                                                                                                                                                       'Z '
                                                                                                                                                                                                       '轴移动。参数位于“编辑 '
                                                                                                                                                                                                       '> '
                                                                                                                                                                                                       '调整上一步操作”及原生修改器属性。',
 'Selected-shell separation transaction not implemented': '尚未实现选中壳体的分离事务',
 'Selection export flags are format-specific; use Export All and the native format selection settings': '选区导出标记因格式而异；请使用导出全部及原生格式的选区设置。',
 'Selection unavailable': '选择不可用',
 'Selection-constraint dialog not implemented; non-manifold selection is only one filter': '尚未实现选择约束对话框；非流形选择仅是一种过滤条件。',
 'Selects Blender object datablocks marked as assets, not Maya asset containers.': '选择标记为资产的 Blender 对象数据块，而非 Maya '
                                                                                   '资产容器。',
 'Selects the U/V control-grid boundary of selected NURBS points; this is not a surface isoparm domain.': '选择已选中 NURBS '
                                                                                                          '点的 U/V '
                                                                                                          '控制网格边界；不是曲面等参线选择域。',
 'Selects visible selectable Blender descendants; no Maya UFE/DAG nodes.': '选择可见且可选择的 Blender 后代对象；不包括 Maya UFE/DAG '
                                                                           '节点。',
 'Set current viewport backface culling off; not Maya global polygon display': '关闭当前视窗的背面剔除；不是 Maya 全局多边形显示。',
 'Set current viewport backface culling on; not Maya global polygon display': '开启当前视窗的背面剔除；不是 Maya 全局多边形显示。',
 'Set object faces or selected Edit Mesh faces shading; does not subdivide geometry.': '设置对象面或选中网格编辑面的着色；不细分几何。',
 'Sets selected Blender object colors and the current viewport wireframe-color source to Object; the same color is shared by solid Object color mode.': '设置选中 '
                                                                                                                                                        'Blender '
                                                                                                                                                        '对象的颜色，并将当前视窗线框颜色来源设为对象；实体对象颜色模式共享同一颜色。',
 'Shrink with Blender mesh topology traversal': '按 Blender 网格拓扑遍历缩小选区',
 'Simple Deform uses the object local axis and bounding-box limits. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '简易形变使用对象局部轴和包围盒范围。参数位于“编辑 '
                                                                                                                                               '> '
                                                                                                                                               '调整上一步操作”及原生修改器属性。',
 'Simplified Chinese interface': '简体中文界面',
 'Sound members require current scene audio nodes': '声音成员需要当前场景音频节点',
 'Spline-type conversion, not fitting or shape-preserving rebuilding.': '转换样条类型，不执行拟合或保持形状的重建。',
 'Static native XY wave with speed zero; not Maya axial Sine or animated Wave. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '使用速度为零的原生静态 '
                                                                                                                                                          'XY '
                                                                                                                                                          '波浪；不是 '
                                                                                                                                                          'Maya '
                                                                                                                                                          '轴向正弦或动画波浪。参数位于“编辑 '
                                                                                                                                                          '> '
                                                                                                                                                          '调整上一步操作”及原生修改器属性。',
 'Stereo rigs and camera sets require scene and plugin providers': '立体绑定和相机集需要场景及插件提供器',
 'Subdivision Surface modifier on the captured Mesh; original mesh data remains': '在已捕获网格上使用表面细分修改器；原始网格数据保留。',
 'Subdivision Surface modifier on the captured Mesh; original mesh data remains; confirmation applies parameters': '在已捕获网格上使用表面细分修改器；原始网格数据保留；确认后应用参数。',
 'Surface direction and selected-boundary adaptation not implemented': '尚未适配曲面方向与选中边界',
 'Target-bound Maya operation not implemented': '尚未实现绑定到目标的 Maya 操作',
 'Target-bound UV selection adapter not implemented': '尚未实现绑定到目标的 UV 选择适配',
 'Target-bound parameter editor not implemented': '尚未实现绑定到目标的参数编辑器',
 'Toggle Blender Object and Mesh Edit modes on the active mesh': '在活动网格上切换 Blender 对象与网格编辑模式。',
 'Toggle one current 3D View overlay; mesh measurements/normals are visible in Edit Mesh.': '切换当前三维视图的一项叠加；网格测量/法向在网格编辑模式下可见。',
 'Toggle the current Blender 3D View toolbar; does not reproduce the Maya Modeling Toolkit panel.': '切换当前 Blender '
                                                                                                    '三维视图工具栏；不复现 Maya '
                                                                                                    '建模工具集面板。',
 'Transfer from active source to selected mesh destinations using Blender nearest-element mappings; no UV transfer.': '使用 '
                                                                                                                      'Blender '
                                                                                                                      '最近元素映射从活动源传递到选中网格目标；不传递 '
                                                                                                                      'UV。',
 'Triangle-only edge flip eligibility not implemented': '尚未实现仅三角形边的翻转适用性检查',
 'Two distinct empty transforms are ordered by object name: from, then to; no falloff. Parameters: Edit > Adjust Last Operation and native Modifier properties.': '两个不同空物体变换按对象名称排序：先为起点，后为终点；没有衰减。参数位于“编辑 '
                                                                                                                                                                  '> '
                                                                                                                                                                  '调整上一步操作”及原生修改器属性。',
 'Unavailable mode': '当前模式不可用',
 'Uses Blender native NURBS control points, dimensions and tessellation at the 3D Cursor.': '在三维游标处使用 Blender 原生 NURBS '
                                                                                            '控制点、尺寸与镶嵌细分。',
 'Uses Blender native selection, geometry and parameter semantics.': '使用 Blender 原生选择、几何与参数语义。',
 'Uses active modifier of this type, or the sole matching modifier. Native target and binding semantics; no Maya multi-influence arrays.': '使用该类型的活动修改器，或唯一匹配的修改器。采用原生目标和绑定语义，不提供 '
                                                                                                                                           'Maya '
                                                                                                                                           '多影响数组。',
 'Uses native curve/surface U/V sampling 12; Hull is minimum sampling, not Maya control-hull-only display. No rebuild or topology conversion.': '使用原生曲线/曲面 '
                                                                                                                                                'U/V '
                                                                                                                                                '采样数 '
                                                                                                                                                '12；控制框表示最低采样，不是 '
                                                                                                                                                'Maya '
                                                                                                                                                '仅显示控制框。不执行重建或拓扑转换。',
 'Uses native curve/surface U/V sampling 1; Hull is minimum sampling, not Maya control-hull-only display. No rebuild or topology conversion.': '使用原生曲线/曲面 '
                                                                                                                                               'U/V '
                                                                                                                                               '采样数 '
                                                                                                                                               '1；控制框表示最低采样，不是 '
                                                                                                                                               'Maya '
                                                                                                                                               '仅显示控制框。不执行重建或拓扑转换。',
 'Uses native curve/surface U/V sampling 24; Hull is minimum sampling, not Maya control-hull-only display. No rebuild or topology conversion.': '使用原生曲线/曲面 '
                                                                                                                                                'U/V '
                                                                                                                                                '采样数 '
                                                                                                                                                '24；控制框表示最低采样，不是 '
                                                                                                                                                'Maya '
                                                                                                                                                '仅显示控制框。不执行重建或拓扑转换。',
 'Uses native curve/surface U/V sampling 4; Hull is minimum sampling, not Maya control-hull-only display. No rebuild or topology conversion.': '使用原生曲线/曲面 '
                                                                                                                                               'U/V '
                                                                                                                                               '采样数 '
                                                                                                                                               '4；控制框表示最低采样，不是 '
                                                                                                                                               'Maya '
                                                                                                                                               '仅显示控制框。不执行重建或拓扑转换。',
 'Uses one Blender origin; independent Maya rotate and scale pivots are not reproduced.': '使用一个 Blender 原点；不复现 Maya '
                                                                                          '独立旋转和缩放枢轴。',
 'Uses the Blender viewport measurement tool; no persistent Maya measurement node.': '使用 Blender 视窗测量工具；不创建持久的 Maya '
                                                                                     '测量节点。',
 'Uses the corresponding native Blender operation and file format': '使用相应的原生 Blender 操作与文件格式',
 'Uses the separate Blender solid/wireframe X-Ray setting in the current viewport.': '使用当前视窗分别设置的 Blender 实体/线框透视。',
 'Uses two preselected Blender faces, not an interactive Maya path-picking context.': '使用两个预先选中的 Blender 面，而非 Maya '
                                                                                      '交互式路径拾取上下文。',
 'View unavailable': '视图不可用',
 'Voxel Remesh modifier on the captured Mesh; original mesh data remains': '在已捕获网格上使用体素重构修改器；原始网格数据保留。',
 'Voxel Remesh modifier on the captured Mesh; original mesh data remains; confirmation applies parameters': '在已捕获网格上使用体素重构修改器；原始网格数据保留；确认后应用参数。',
 'Whole-object translation between selected points is not implemented; Selection to Active snaps selected geometry instead': '尚未实现选中点之间的整个对象平移；“选中项到活动项”吸附的是选中几何。'}

# All explanations have Chinese translations; there are no English fallback entries.
UNCHANGED = frozenset()
