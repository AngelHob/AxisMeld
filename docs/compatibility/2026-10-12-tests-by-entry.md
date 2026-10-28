# 按热盒与菜单分类的测试索引

更新：2026-10-29。公开网页与本索引按同一分类组织；使用网页记录自己的结果。原[人工总清单](2026-09-14-manual-test-ledger.md)保留开发批次、完整步骤及历史初始状态。

共400项：386项当前、14项历史；当前维护者初始待测339项。分类及排序不会修改已有浏览器记录。以下“历史已测”只表示原维护者记录，不等于通过；访客结果仍在各自浏览器。

本批新增PN-01～PN-06对象属性验收，全部归入“菜单 · Windows 窗口”，适用版本为`axismeld-2026.10.29-property-navigation-preview`。既有49项BI及GU-28的内容和人工状态保持；“最近新增”改为本批6项PN。

按主要验证入口归类；没有明确主入口的跨热盒或跨菜单检查集中在“通用”，同一测试只出现一次。测试某个入口后，可继续检查对应通用类别。Space内的Deform/Generate不代表恢复Modeling视窗栏根菜单。

完整分组目录以`tools/testing_site/catalog.json`为维护资产。旧`axismeld_public_test_catalog.py`尚未支持多段BI编号及当前入口分组，不应用它覆盖本目录。

## 分类目录

| 类别 | 当前条目 | 历史条目 |
|---|---:|---:|
| 热盒 · Space 主热盒 | 3 | 0 |
| 热盒 · Views 视图 | 5 | 0 |
| 热盒 · Q 选择工具 | 4 | 0 |
| 热盒 · W 移动工具 | 3 | 0 |
| 热盒 · E 旋转工具 | 2 | 0 |
| 热盒 · R 缩放工具 | 2 | 0 |
| 热盒 · RMB 组件切换与对象上下文 | 31 | 0 |
| 热盒 · Shift+RMB 空白创建 | 16 | 0 |
| 热盒 · Shift+RMB Object 建模 | 34 | 0 |
| 热盒 · Shift+RMB Vertex 建模 | 2 | 0 |
| 热盒 · Shift+RMB Edge 建模 | 3 | 0 |
| 热盒 · Shift+RMB Face 建模 | 4 | 0 |
| 热盒 · Ctrl+RMB 选择转换 | 2 | 0 |
| 热盒 · A+LMB History Operations | 3 | 0 |
| 菜单 · Hotbox Controls 设置 | 8 | 0 |
| 菜单 · Recent Commands 最近命令 | 2 | 0 |
| 菜单 · File 文件 | 6 | 0 |
| 菜单 · Edit 编辑 | 5 | 0 |
| 菜单 · Create 创建 | 7 | 0 |
| 菜单 · Select 选择 | 5 | 0 |
| 菜单 · Modify 修改 | 6 | 0 |
| 菜单 · Display 显示 | 4 | 0 |
| 菜单 · Windows 窗口 | 11 | 0 |
| 菜单 · Current Pane → View | 2 | 0 |
| 菜单 · Current Pane → Shading | 2 | 0 |
| 菜单 · Current Pane → Lighting | 2 | 0 |
| 菜单 · Current Pane → Show | 2 | 0 |
| 菜单 · Current Pane → Renderer | 2 | 0 |
| 菜单 · Current Pane → Panels | 2 | 0 |
| 菜单 · Mesh 网格 | 5 | 0 |
| 菜单 · Edit Mesh 编辑网格 | 5 | 1 |
| 菜单 · Mesh Tools 网格工具 | 4 | 0 |
| 菜单 · Mesh Display 网格显示 | 5 | 0 |
| 菜单 · Curves 曲线 | 4 | 0 |
| 菜单 · Surfaces 曲面 | 4 | 0 |
| 菜单 · Space → Modeling → Deform | 5 | 1 |
| 菜单 · UV | 2 | 0 |
| 菜单 · Space → Modeling → Generate | 2 | 0 |
| 菜单 · Skeleton 骨架 | 3 | 0 |
| 菜单 · Skin 蒙皮与权重 | 9 | 0 |
| 菜单 · Help 帮助 | 2 | 0 |
| 菜单 · Blender Extensions 原生扩展 | 2 | 0 |
| 菜单 · Preferences → Keymap 键位设置 | 5 | 0 |
| 通用 · Q/W/E/R 工具热盒交互 | 19 | 0 |
| 通用 · 点/边/面建模热盒交互 | 11 | 0 |
| 通用 · 热盒布局、外划与取消 | 26 | 0 |
| 通用 · 完整列表、级联与图标 | 17 | 3 |
| 通用 · 外观设置与真实状态 | 5 | 0 |
| 通用 · 灰项、Options 与键盘导航 | 6 | 0 |
| 通用 · 灰项说明与窗口避让 | 2 | 0 |
| 通用 · 跨入口操作与回归 | 18 | 0 |
| 通用 · 改键、配置与输入隔离 | 10 | 0 |
| 通用 · 全局栏与工作区 | 9 | 2 |
| 通用 · 建模菜单归类与原生扩展 | 5 | 4 |
| 通用 · Maya 菜单集与层级 | 6 | 3 |
| 通用 · 动态菜单与场景数据 | 2 | 0 |
| 通用 · Rigging 菜单与灰项 | 2 | 0 |
| 其他 · Rigify 创建、生成与偏好 | 7 | 0 |
| 其他 · X/V/J 临时吸附 | 3 | 0 |
| 其他 · 预览包与公开测试反馈 | 1 | 0 |

## 热盒 · Space 主热盒

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| R-02 | Space 点按切单/四视图，长按打开；移动到标准正交视图后 Alt 导航 | 历史已测 · 未判定 |
| IC-01 | Space打开主热盒，查看File/Edit/Create/Select/Modify及中心控制等入口 | 待测试 |
| BI-H01 | Space 主热盒：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Views 视图

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| V-01 | Space 视图热盒，从左上 Left View 向左拉出按钮后释放 | 历史已测 · 未判定 |
| V-02 | 对 Back/Bottom 重复外侧划动；从中心做短划和原地释放 | 历史已测 · 未判定 |
| V-03 | 在视口四角、单视图/四视图、窄视口重复；隐藏 Camera 时划向右上空方向 | 历史已测 · 未判定 |
| IC-02 | 打开Views，依次查看透视及六个正交视图，单/四视图重复 | 待测试 |
| BI-H02 | Views 视图：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Q 选择工具

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| G-09 | Edit中Q Clear Selection后仍持Q再次LMB切Lasso，松Q后撤销；个人改键也重复 | 待测试 |
| T-07 | Q 切换 Marquee/Lasso/Paint，再松 Q；Object/Edit 执行 Clear Selection 并撤销 | 历史已测 · 未判定 |
| HC-09 | Q+LMB，核对Marquee、Drag、Camera-Based Selection和下方菜单 | 待测试 |
| BI-H03 | Q 选择工具：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · W 移动工具

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| HC-10 | W+LMB，核对下方主项、约束和Move Options | 待测试 |
| GU-14 | 在 Keymap 首选项将 Move 临时改为 Ctrl+W；持 Ctrl+W 后连续按住、划动和松开 LMB 三次，分别选 World/Local；再测试先松 W、先松 Ctrl、Esc 和切出应用，最后恢复 W 并重试 | 待测试 |
| BI-H04 | W 移动工具：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · E 旋转工具

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| HC-11 | E+LMB，核对下方主项并展开Rotate Center | 待测试 |
| BI-H05 | E 旋转工具：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · R 缩放工具

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| HC-12 | R+LMB，核对下方主项并展开Scale Center | 待测试 |
| BI-H06 | R 缩放工具：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · RMB 组件切换与对象上下文

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| P-01 | A选中，B未选；在B上右键拖上/左/下并释放，分别重做 | 历史已测 · 未判定 |
| P-02 | 无活动/选中对象，在B上右键划选 | 历史已测 · 未判定 |
| P-03 | A选中，在B上打开；中心释放、Esc、拉回起点释放分别重做 | 历史已测 · 未判定 |
| P-04 | A选中，在B上打开后划向UV/Vertex Face/Multi Component释放 | 历史已测 · 未判定 |
| P-05 | A选中，在B上打开后切应用；另试中途Ctrl后松右键 | 历史已测 · 未判定 |
| P-06 | A、B同时选中且A活动；在B上提交，再选A/B之外的C提交 | 历史已测 · 未判定 |
| P-07 | A选中，在B上右键向右上Object Mode释放；重复一次 | 历史已测 · 未判定 |
| P-08 | A选中时在空白处打开；无选择时在空白处右键；在Camera形状上右键 | 历史已测 · 未判定 |
| P-09 | 两网格前后重叠；再将前物体隐藏/设不可选，测试实心、线框、X-Ray | 历史已测 · 未判定 |
| P-10 | 打开后通过另一区域删除目标或将其不可选，再尝试提交 | 历史已测 · 未判定 |
| P-11 | Edit A时鼠标对准B；将入口临时改绑键盘后Object A活动且鼠标对B | 历史已测 · 未判定 |
| P-12 | 四视图、视口四角、125/150/200% DPI重复P-01/P-03；细小目标边缘慢划和快速划 | 历史已测 · 未判定 |
| P-13 | 用临时链接资产分别测试不可编辑对象、Object override、Mesh数据override | 历史已测 · 未判定 |
| C-01 | Object 下选 Cube；按住右键，向上/左/下拖动后松右键，分别重做 | 历史已测 · 未判定 |
| C-02 | 分别从点、边、面 Edit 按住右键拖向右上 Object Mode；已在 Object 再做一次 | 历史已测 · 未判定 |
| C-03 | 原地按下并松右键；拖出再回按下点释放 | 历史已测 · 未判定 |
| C-04 | 打开后按 Esc，再释放右键；再打开并切到另一应用后回来 | 历史已测 · 未判定 |
| C-05 | 向右 UV、左下 Vertex Face、右下 Multi Component 释放 | 历史已测 · 未判定 |
| C-06 | Cube 活动时分别在其表面、空白处、另一个未选网格上打开 | 历史已测 · 未判定 |
| C-07 | 无有效目标的空白处、Camera/Light形状、Sculpt、其他编辑器分别右键 | 历史已测 · 未判定 |
| C-08 | 有活动 Cube 时 Alt/Ctrl/Shift + 右键；另试已打开热盒后按 Ctrl 并松右键，随后无修饰右键 | 历史已测 · 未判定 |
| C-09 | 快速连续两次右键划选；右键尚未释放时切换工具键；完成后左键选择 | 历史已测 · 未判定 |
| C-10 | 临时改绑到键盘上可用的无修饰空闲键，或禁用组件入口，重载后检查原右键，再恢复配置 | 历史已测 · 未判定 |
| C-12 | 同时选两个可编辑网格，指定活动对象；用组件热盒进/出 Edit | 历史已测 · 未判定 |
| IC-04 | Object及Edit分别用组件RMB热盒切点/边/面和其他现有选择入口 | 待测试 |
| HC-01 | Object模式，无任何选择，在可见Mesh上RMB；再选A指向B重复 | 待测试 |
| HC-02 | RMB依次进入UV、Inputs/Outputs、Paint、Metadata、Actions、Time Editor和材质子菜单 | 待测试 |
| HC-03 | RMB伴随列表悬停禁用项、Select Similar参数格、Metadata状态和参数格后取消 | 待测试 |
| HC-04 | A选中指向B打开RMB，分别从列表执行Select All、Deselect All、Invert Selection | 待测试 |
| HC-05 | 指针目标为当前已选活动Mesh时测试Select Hierarchy和Actions的Template/Untemplate/Unparent；然后改为未选目标 | 待测试 |
| BI-H07 | RMB 组件切换与对象上下文：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Shift+RMB 空白创建

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| K-01 | Object无选择，鼠标位于空白；按住Shift并按住RMB，中心松RMB，反复重开 | 待测试 |
| K-02 | 将3D Cursor移到可辨位置，分别创建NE Disc、E Sphere、SE Torus、S Cube、SW Cone、W Cylinder、NW Plane；每次先清空选择并移到空白 | 待测试 |
| K-03 | 对K-02七种创建分别只撤销一次，再重做一次 | 待测试 |
| K-04 | 经过七个有效方向按钮后，在未被伴随菜单遮挡的外延区域松RMB；S Cube另在主按钮释放，再向下进入列表及连接间隔释放 | 待测试 |
| K-05 | 在中心释放、出中心再回划、划到N Create Polygon Tool后释放 | 待测试 |
| K-06 | 开环后先松Shift、加按Ctrl或Alt、Esc、切应用、切模式/窗口；交换Shift/RMB释放顺序再重试 | 待测试 |
| K-07 | 已选择网格/非网格、Edit Mode、空选择但鼠标指向可选物体；各用Shift+RMB | 待测试 |
| K-09 | 临时配置改绑创建热盒至键盘或Ctrl/Shift组合，再禁用，重新加载配置 | 待测试 |
| K-10 | 单/四视图、视口四角/较窄区域、125/150/200%DPI重试K-01/K-04/K-05 | 待测试 |
| K-11 | 分别关闭/开启Blender“新建后进入编辑模式”偏好，创建Cube和Torus并一次撤销 | 待测试 |
| MC-02 | Object无选择且鼠标为空白，Shift+RMB，逐组检查完整创建下拉 | 待测试 |
| MC-06 | 在创建八个方向的文字、图标、右侧参数格分别悬停/释放 | 待测试 |
| MC-07 | 检查创建下拉每个主项右侧，逐个尝试可用与灰显参数格 | 待测试 |
| MC-09 | 检查创建Interactive Creation与Exit On Completion，点击后重开；记录相关偏好前后值 | 待测试 |
| HC-17 | 创建热盒→Polygon Display All，连续执行Backface Culling on两次，再off两次 | 待测试 |
| BI-H08 | Shift+RMB 空白创建：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Shift+RMB Object 建模

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| O-01 | Object选中一个网格，Shift+RMB开环，中心释放；鼠标移到另一网格上重复 | 待测试 |
| O-02 | Object完全无选择，鼠标指向网格，开环后中心/Esc取消，再确认W | 待测试 |
| O-03 | 混选Mesh与非Mesh、缺少active、局部视图外仍被选中的对象；另测试锁定/隐藏后开环 | 待测试 |
| O-04 | Object选择临时平面，E进入Poly Build，拖边建面/移动顶点，再Undo | 待测试 |
| O-05 | Object从W进入Knife，点击两点切割并Enter确认，另一次Esc | 待测试 |
| O-06 | Object从SW进入Loop Cut，在可切边环操作并确认/取消 | 待测试 |
| O-07 | 开启Global Undo，分别从已选/无选择预选启动三工具后立即单Undo；再做笔划分别Undo | 待测试 |
| O-08 | 同时选中两个独立Mesh；另用Alt+D共享数据实例重复，并保留非默认active | 待测试 |
| O-09 | 保留部分组件选择、隐藏组件及不同点/边/面选择域，退出Object再启动工具 | 待测试 |
| O-10 | 划向W后分别Esc、先松Shift、切应用、回起点、增加Ctrl；恢复后重开 | 待测试 |
| O-11 | 开盒后通过外部操作更改选择/active、锁定集合、移除目标或替换其Mesh data，再释放 | 待测试 |
| O-13 | MODEL改绑键盘，完全无选择时将鼠标停在网格上按键；已有选择时再按 | 待测试 |
| O-14 | 通过中心按钮映射Marking Menus或Object Modeling进入Object根并提交W；开着目录时更换有效选择再提交 | 待测试 |
| O-15 | 单/四视图、四角、125/150/200%DPI，将Object根与Views比较并外划释放 | 待测试 |
| OM-01 | Object选中Cube，Shift+RMB唤出；与提供的Maya截图对照 | 待测试 |
| OM-02 | 持住RMB检查完整长列表并滚动滚轮，再展开三个目录，移回父项和主环 | 待测试 |
| OM-03 | 分别在Smooth/Mirror/Reduce/Remesh主文字与右侧方框释放RMB | 待测试 |
| OM-04 | 对四种参数框分别点取消或Esc；无选择鼠标预选对象时也重复 | 待测试 |
| OM-05 | 调Smooth层级、Mirror轴/剖切/合并、Reduce比例、Remesh体素大小后确认，再撤销 | 待测试 |
| OM-06 | 参数框打开期间改变active/完整选择、对象data或目标可见/可选资格后确认 | 待测试 |
| OM-07 | 多选两个Mesh，交换活动对象后分别执行四种修改器操作 | 待测试 |
| OM-08 | 两个独立Mesh执行Combine，再一步撤销；单Mesh时观察Combine | 待测试 |
| OM-09 | 两个有重叠体积的Mesh分别执行四种Boolean，交换active并撤销 | 待测试 |
| OM-10 | 从下方列表启动Offset Edge Loop与Quad Draw，完成原生笔划并撤销 | 待测试 |
| OM-11 | 八向按钮外延长划；经过下方列表的有效/禁用/分隔/Options区域后松RMB | 待测试 |
| OM-12 | 中心释放、移出再返回、Esc、提前松Shift、切应用；顺序交替重复 | 待测试 |
| OM-13 | 完全无选择，指向可选Mesh开盒，取消或选modifier/工具；再指向前景非Mesh | 待测试 |
| OM-14 | 将MODEL及Object专用命令改绑、禁用、恢复；在Object和Edit分别测试 | 待测试 |
| OM-15 | 单/四视图、视口四角、Sidebar打开、125/150/200%DPI下使用组合菜单 | 待测试 |
| OM-16 | 检查灰显缺口与适配说明，特别是Retopologize主项及参数方框 | 待测试 |
| IC-09 | 在Smooth/Mirror/Reduce/Remesh文字与右侧Options格分别释放 | 待测试 |
| MC-01 | 选中Object Mesh，Shift+RMB，与Maya建模截图逐行对照完整列表；1x/2x检查右侧目录箭头 | 待测试 |
| MC-05 | 检查Object N Target Weld、NW Sculpt、W Multi-Cut、E Append、SW Insert Edge Loop的参数格，各在格内释放 | 待测试 |
| BI-H09 | Shift+RMB Object 建模：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Shift+RMB Vertex 建模

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| HC-06 | Edit Vertex有有效选择，Shift+RMB，并依次展开列表子菜单 | 待测试 |
| BI-H10 | Shift+RMB Vertex 建模：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Shift+RMB Edge 建模

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| HC-07 | Edit Edge有有效选择，Shift+RMB，核对Merge子菜单及下方列表 | 待测试 |
| GU-05 | Edit Mesh 空边选择，Shift+RMB 执行 Bevel 后移动鼠标再 Esc；以 Crease 重复；另测试确认后一次 Undo | 待测试 |
| BI-H11 | Shift+RMB Edge 建模：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Shift+RMB Face 建模

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| D-05 | 面域选择同一Mesh相邻/分离面执行N Merge at Center，再以两个Mesh不同位置重复并单Undo | 待测试 |
| HC-08 | Edit Face有有效选择，Shift+RMB，查看Mapping和Polygon Display | 待测试 |
| GU-04 | Edit Mesh 空选择，鼠标指向一个面，用 Shift+RMB 执行已有 Poke 等即时操作，再一次 Undo；在其他可见对象的组件上重复 | 待测试 |
| BI-H12 | Shift+RMB Face 建模：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · Ctrl+RMB 选择转换

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| GU-01 | Edit Mesh 选择组件，Ctrl+RMB 查看转换方向环、下方菜单和各级子环；分别转换 Vertex、Edge、Face，再 Undo；检查空选择和取消 | 待测试 |
| BI-H13 | Ctrl+RMB 选择转换：中英文按钮、说明与热盒显示 | 待测试 |

## 热盒 · A+LMB History Operations

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| GU-09 | A 单按和仅长按后松开；再持 A+LMB 打开 History Operations，选 Freeze/Reset 后先松 LMB、再松 A；执行后一次 Undo | 待测试 |
| GU-10 | A 持键中中心取消、灰方向取消、连续三次 LMB 重开；先松 A 后松 LMB、Esc、切应用及改变选择后再释放 | 待测试 |
| BI-H14 | A+LMB History Operations：中英文按钮、说明与热盒显示 | 待测试 |

## 菜单 · Hotbox Controls 设置

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| S-01 | Space → Hotbox Controls → Transparency | 历史已测 · 未判定 |
| S-02 | 悬停未选项，再选择不同透明度；重复选择同一项并重开 | 历史已测 · 未判定 |
| S-03 | 在临时配置中填写非法透明度37并重载，再打开Transparency | 历史已测 · 未判定 |
| S-05 | 分别修改左/中/右Center Mouse Buttons映射，含Disabled与目录后页选项 | 历史已测 · 未判定 |
| VR-01 | 窄视口保留Tool Header，打开Controls完整列表，进入真实子目录并返回，悬停禁用项 | 待测试 |
| VR-02 | 在VR-01禁用项上保持鼠标不动，分别先松Space、Esc及交换拥有鼠标释放顺序，再直接按W/E/R | 待测试 |
| HC-16 | Space→Hotbox Controls，检查Show/Hide、Custom Menu Set、Hotbox Style、Window Options | 待测试 |
| BI-M01 | Hotbox Controls 设置：中英文菜单与对应界面 | 待测试 |

## 菜单 · Recent Commands 最近命令

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-31 | 成功执行可重复的非modal命令后查看Recent并重放；对modal启动后取消、参数窗取消、灰显计划释放分别检查Recent；切不支持模式再看旧Recent项 | 待测试 |
| BI-M02 | Recent Commands 最近命令：中英文菜单与对应界面 | 待测试 |

## 菜单 · File 文件

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-01 | 在临时场景打开 Common → File，逐层与Maya对照 | 待测试 |
| MB-06 | File 在临时目录新建、Open、Save、Save As、Save Copy、Increment and Save；核对文件和当前文档路径 | 待测试 |
| MB-07 | File 展开 Recent Files、Import、Export；启用一个已安装格式后重新查看 | 待测试 |
| MB-08 | File 查看模板、恢复、Link/Append、Project、External Data、Data Previews 和 Clean Up | 待测试 |
| GU-13 | 在临时场景从 Space 热盒的 File 分别调用 Open Scene、Save Scene As，保持触发键后移到新文件窗口再松键；分别先松鼠标、先松 Space，在两个窗口之间释放，并用 Esc 取消；对未保存场景分别选择 Don't Save 继续和 Cancel 退出确认框；重新打开后测试切应用再返回及关闭文件窗口 | 待测试 |
| BI-M03 | File 文件：中英文菜单与对应界面 | 待测试 |

## 菜单 · Edit 编辑

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-07 | Edit：临时对象Duplicate与Duplicate Linked、Copy/Paste与Cut/Paste，分别Undo；再从Object Relationships→Copy Active Scalar Custom Properties将活动源的数值/字符串/布尔复制到两个目标，含已有同名scalar与缺失键；加入同名数组/字典目标后重试 | 待测试 |
| M3-08 | Edit→Adjust Last Operation修改参数，Mesh Object按F9，并检查Undo/Redo不可用状态；G重复上一原生动作；另在Delete by Type依次测试Bake Selected Mesh History、Bake All Mesh History及对应Non-Deformer项，每次单Undo/Redo；使用两个对象、拓扑modifier在deformer前的栈、共享Mesh实例、shape key及动画/driver/NLA/override对象作对照 | 待测试 |
| MT-02 | 在临时场景打开 Common → Edit，逐层与Maya对照 | 待测试 |
| MB-09 | Edit 打开 Undo/Redo、History、Repeat History、Adjust Last Operation、Search；在临时对象编辑后使用一次撤销 | 待测试 |
| BI-M04 | Edit 编辑：中英文菜单与对应界面 | 待测试 |

## 菜单 · Create 创建

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| K-08 | Object已有选中对象时Space→Create→Polygon Primitives创建；Edit中再查看该入口 | 待测试 |
| M3-09 | Create：在可辨位置放3D Cursor，分别创建新增网格原语、Bezier/NURBS曲线和Surface原语；每次Undo一次 | 待测试 |
| M3-10 | Create：选对象创建Collection，再添加其Collection Instance；打开Reference Image选择器后取消；激活Measure并量一段距离 | 待测试 |
| MT-03 | 在临时场景打开 Common → Create，逐层与Maya对照 | 待测试 |
| MB-11 | Create 从 Polygon/NURBS Primitives、Curve Tools 创建各一个临时对象，再从 Cameras/Lights 创建相机和四类灯光 | 待测试 |
| MB-12 | Create 检查 Armature、Metaball、Empty Volume、Empty Grease Pencil、Speaker、Force Field；在 Object 与 Edit 中分别查看 | 待测试 |
| BI-M05 | Create 创建：中英文菜单与对应界面 | 待测试 |

## 菜单 · Select 选择

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-03 | Select：准备两个Mesh和一条Curve，依次使用All、None、Invert及按类型选择；再在Mesh Edit重复全选/反选 | 待测试 |
| M3-04 | Select：在带规则四边面的网格选一圈边，测试相邻扩展/收缩、Loop/Ring以及点边面转换；从Convert Selection→Multi-Component及F7同时启用三域；在两个独立Edit对象各选一个点再看Connect/Merge | 待测试 |
| MT-04 | 在临时场景打开 Common → Select，逐层与Maya对照 | 待测试 |
| MT-27 | 在Object和Edit依次用Select→Deselect All、Object/Component、Grow、Shrink | 待测试 |
| BI-M06 | Select 选择：中英文菜单与对应界面 | 待测试 |

## 菜单 · Modify 修改

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-05 | Modify：Cube移动、旋转、非均匀缩放后测试Apply、Reset、Origin to Geometry与Origin to Cursor，每次撤销；Ctrl+T激活Universal工具；在Object Relationships→Replace with Active Object Data中明确活动源A和同类型目标B/C，再试混合类型 | 待测试 |
| MT-05 | 在临时场景打开 Common → Modify，逐层与Maya对照 | 待测试 |
| MB-10 | Modify 检查 Transformation Tools、Snap Align Objects、Naming Tools、Convert 等补充目录 | 待测试 |
| MB-26 | 展开 Modify→Naming Tools，在临时对象上查看并使用 Rename Active Item 和 Batch Rename | 待测试 |
| GU-17 | 在 Modeling 打开 Object→Maya Modify→Transformation Tools，查看 Move/Rotate/Scale；临时将 Move 改为 Ctrl+W，再禁用和移除该绑定，每次重新打开菜单；恢复默认后检查正文和右侧齿轮 | 待测试 |
| BI-M07 | Modify 修改：中英文菜单与对应界面 | 待测试 |

## 菜单 · Display 显示

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-11 | Display：选择部分对象使用Hide/Show及Hide/Show by Type；对同一明确Show或Hide命令执行两次，再在Outliner或原生显示设置核对；Mesh Edit隐藏部分组件后按Ctrl+Alt+H | 待测试 |
| MT-06 | 在临时场景打开 Common → Display，逐层与Maya对照 | 待测试 |
| MT-23 | 逐个展开Display的Polygons、NURBS、Animation、Rendering及Heads Up Display | 待测试 |
| BI-M08 | Display 显示：中英文菜单与对应界面 | 待测试 |

## 菜单 · Windows 窗口

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-07 | 在临时场景打开 Common → Windows，逐层与Maya对照 | 待测试 |
| MB-13 | Windows 打开 Outliner、UV/Graph/Dope Sheet、Shader/Geometry Node/Compositor、Text/Python Console/NLA 编辑器 | 待测试 |
| MB-14 | Windows 查看 Settings/Preferences、Startup and Defaults、Workspaces、UI Elements、Window Management | 待测试 |
| MB-24 | 展开 Windows→Workspaces，检查 Factory/Module 章节，再独立操作 Blender Next/Previous Workspace | 待测试 |
| BI-M09 | Windows 窗口：中英文菜单与对应界面 | 待测试 |
| PN-01 | 在临时场景选中网格，经 Windows 菜单及 F3 分别打开 Object Transform Properties；切换另一个已选活动对象后重复，检查对象名称和原生 Transform 数值 | 待测试 |
| PN-02 | 给临时网格添加原生修改器，从菜单和 F3 打开 Modifier Properties；切换不同类型对象并重开；检查 Camera、Light 与原生支持修改器的其他对象 | 待测试 |
| PN-03 | 将 Properties 固定到另一对象，尝试两入口；再固定到当前对象及取消固定后重复；临时最大化视窗，使本窗口没有可见 Properties 后重试 | 待测试 |
| PN-04 | 在两个窗口使用不同场景或 View Layer、不同活动对象；在单/四视图、Object/Edit/Pose 模式分别调用；取消选择并重试 | 待测试 |
| PN-05 | 导航前记录对象位置、修改器、选区及历史；只打开两个入口，再用原生字段实际修改位置或修改器参数并执行 Undo；另打开含搜索文字的 Properties | 待测试 |
| PN-06 | 中英文分别从 Windows 菜单和 F3 找到两入口；在100%/150%缩放和窄窗口检查标签、图标及不可用原因，随后重开 Space/QWER 热盒 | 待测试 |

## 菜单 · Current Pane → View

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-08 | 在临时场景打开 Current Pane → View，逐层与Maya对照 | 待测试 |
| BI-M10 | Current Pane → View：中英文菜单与对应界面 | 待测试 |

## 菜单 · Current Pane → Shading

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-09 | 在临时场景打开 Current Pane → Shading，逐层与Maya对照 | 待测试 |
| BI-M11 | Current Pane → Shading：中英文菜单与对应界面 | 待测试 |

## 菜单 · Current Pane → Lighting

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-10 | 在临时场景打开 Current Pane → Lighting，逐层与Maya对照 | 待测试 |
| BI-M12 | Current Pane → Lighting：中英文菜单与对应界面 | 待测试 |

## 菜单 · Current Pane → Show

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-11 | 在临时场景打开 Current Pane → Show，逐层与Maya对照 | 待测试 |
| BI-M13 | Current Pane → Show：中英文菜单与对应界面 | 待测试 |

## 菜单 · Current Pane → Renderer

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-12 | 在临时场景打开 Current Pane → Renderer，逐层与Maya对照 | 待测试 |
| BI-M14 | Current Pane → Renderer：中英文菜单与对应界面 | 待测试 |

## 菜单 · Current Pane → Panels

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-13 | 在临时场景打开 Current Pane → Panels，逐层与Maya对照 | 待测试 |
| BI-M15 | Current Pane → Panels：中英文菜单与对应界面 | 待测试 |

## 菜单 · Mesh 网格

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-13 | Mesh：两个相交Cube明确活动A，分别Union、A−B、B−A、Intersection，每次观察修改器目标/几何后Undo一次；再只选一个或加入非网格目标 | 待测试 |
| M3-14 | Mesh：两网格Combine，再Edit Separate Loose Parts；在临时细分网格执行Triangulate、Quadrangulate、Reduce/Subdivision与Remesh代表项 | 待测试 |
| MT-14 | 在临时场景打开 Modeling → Mesh，逐层与Maya对照 | 待测试 |
| MB-37 | 临时Cube经Mesh中的Modifier入口添加一个修改器、查看参数并撤销；测试原生独有建模操作及撤销 | 待测试 |
| BI-M16 | Mesh 网格：中英文菜单与对应界面 | 待测试 |

## 菜单 · Edit Mesh 编辑网格

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-15 | Edit Mesh：选面用菜单与Ctrl+E各启动一次Extrude；第一轮移动后确认并Undo一次，第二轮移动后Esc取消 | 待测试 |
| M3-16 | Edit Mesh：选边用菜单与Ctrl+B启动Bevel，调整宽度并确认/取消；随后测试Bridge两圈边与Merge有序顶点 | 待测试 |
| M3-17 | Edit Mesh：选面Duplicate Faces和Extract Faces，再试Split、Dissolve和Delete Edge Loop；另在点/边/面域分别按Ctrl+Backspace与Ctrl+Delete，每次单Undo | 待测试 |
| MT-15 | 在临时场景打开 Modeling → Edit Mesh，逐层与Maya对照 | 待测试 |
| MB-32 | 从 Components、Vertex、Edge、Face、Mesh Projection 逐项对照原 Edit Mesh；在临时网格上执行 Components→Add Divisions 并 Undo，再点击灰色 Options | 历史条目 · 待测试 |
| BI-M17 | Edit Mesh 编辑网格：中英文菜单与对应界面 | 待测试 |

## 菜单 · Mesh Tools 网格工具

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-18 | Mesh Tools：通过目录激活Knife、Loop Cut、Poly Build，再在视口实际切割/添面；也试Ctrl+Shift+X与Ctrl+Shift+Q | 待测试 |
| M3-19 | Mesh Tools：启动Immediate Knife/Loop Cut/Edge Slide，移动鼠标后Esc或确认；将有边界投影对象配合编辑中的目标面执行Knife Project | 待测试 |
| MT-16 | 在临时场景打开 Modeling → Mesh Tools，逐层与Maya对照 | 待测试 |
| BI-M18 | Mesh Tools 网格工具：中英文菜单与对应界面 | 待测试 |

## 菜单 · Mesh Display 网格显示

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-20 | Mesh Display：临时封闭网格先Reverse再Recalculate Outside；选部分边Mark/Clear Sharp并切平滑显示，查看法线overlay | 待测试 |
| M3-21 | Mesh Display：Create Color Attribute，分别POINT与CORNER设不同颜色；Edit仅选部分顶点/面Set Color，空选及CORNER只选边再查看可用性 | 待测试 |
| M3-22 | Vertex Paint入口：在临时Mesh使用菜单提供的原生Vertex Paint跳转，画一笔后Undo，再退出到Object/Edit | 待测试 |
| MT-17 | 在临时场景打开 Modeling → Mesh Display，逐层与Maya对照 | 待测试 |
| BI-M19 | Mesh Display 网格显示：中英文菜单与对应界面 | 待测试 |

## 菜单 · Curves 曲线

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-23 | Curves：创建Bezier，Edit选择部分控制点，执行Subdivide、Smooth、Reverse、Handle Auto/Vector/Free；清空控制点选择再查看菜单 | 待测试 |
| M3-24 | Curves：在原生属性将闭合曲线设2D后试Geometry Offset，再试Round Bevel/Resolution；激活Curve Pen实际加点/编辑后取消一次 | 待测试 |
| MT-18 | 在临时场景打开 Modeling → Curves，逐层与Maya对照 | 待测试 |
| BI-M20 | Curves 曲线：中英文菜单与对应界面 | 待测试 |

## 菜单 · Surfaces 曲面

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-25 | Surfaces：创建NURBS Surface Curve，Edit选完整控制行执行Spin Selected NURBS Row；另在曲面选控制行测试Extrude、Subdivide、Cyclic U/V与Reverse | 待测试 |
| M3-26 | Surfaces：Object选一条路径Curve和一个Curve截面，活动对象为路径，执行Sweep Selected Curve Profile；撤销后只选路径再查看入口 | 待测试 |
| MT-19 | 在临时场景打开 Modeling → Surfaces，逐层与Maya对照 | 待测试 |
| BI-M21 | Surfaces 曲面：中英文菜单与对应界面 | 待测试 |

## 菜单 · Space → Modeling → Deform

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-28 | Deform：对带父级非均匀缩放且自身旋转的网格Create Enclosing Lattice，编辑笼点，再回Lattice Edit执行Reset；分别Undo | 待测试 |
| M3-29 | Deform：活动源网格配选目标，分别Shrinkwrap、Curve Deform、Surface Deform bind与封闭笼Mesh Deform bind；绑定后移动目标顶点，再Unbind/Rebind；最后缺目标/错误类型重试 | 待测试 |
| M3-30 | Deform：两个同索引拓扑且形状不同Mesh，活动源执行Selected Targets to Shape Keys；另在Edit选少量点Hook；分别单Undo | 待测试 |
| MT-20 | 在临时场景打开 Modeling → Deform，逐层与Maya对照 | 待测试 |
| MB-23 | 逐项查看 Deform 的17个补充动作，分别展开 Create、Edit、Weights 与 legacy | 历史条目 · 待测试 |
| BI-M22 | Space → Modeling → Deform：中英文菜单与对应界面 | 待测试 |

## 菜单 · UV

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-21 | 在临时场景打开 Modeling → UV，逐层与Maya对照 | 待测试 |
| BI-M23 | UV：中英文菜单与对应界面 | 待测试 |

## 菜单 · Space → Modeling → Generate

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-22 | 在临时场景打开 Modeling → Generate，逐层与Maya对照 | 待测试 |
| BI-M24 | Space → Modeling → Generate：中英文菜单与对应界面 | 待测试 |

## 菜单 · Skeleton 骨架

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| RG-10 | 在Rigging的Skeleton原生入口添加Single Bone并执行一次骨骼Extrude，再Undo；另建Rigify metarig并从原有Rigify面板生成控制骨架 | 待测试 |
| RG-13 | Pose下从Skeleton原生Pose目录执行Clear Transform或Copy/Paste并撤销；再用本地Object引用链接只读Armature数据，检查Pose与IK目录并执行可用的姿态清除、添加或清除IK；使用已安装兼容扩展对照原生Armature/Pose/Weights及Add Armature菜单，再检查Pose Asset入口 | 待测试 |
| BI-M25 | Skeleton 骨架：中英文菜单与对应界面 | 待测试 |

## 菜单 · Skin 蒙皮与权重

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| RG-11 | 临时网格与骨架按Blender要求选择，以骨架为活动对象从Skin原生Armature Deform入口用Automatic Weights绑定，移动骨骼观察变形并在副本中撤销；另用可编辑的本地Object引用链接只读Armature数据，以它为活动目标用Empty Groups绑定本地网格；再检查空选择、只有网格、只有骨架及错误活动对象 | 待测试 |
| RG-12 | 在已绑定的临时网格明确进入Weight Paint，从Skin的原生权重目录执行Normalize或Clean，比较顶点组/权重并Undo；切回Object、Edit Mesh以及无对象上下文查看目录 | 待测试 |
| RG-15 | 活动网格使用唯一 Armature 修改器，准备两变形骨组、锁定骨组、非变形骨组及普通遮罩组；从Skin→Normalize Weights→Normalize Weights执行并Undo，另检查全零顶点 | 待测试 |
| RG-16 | 同一临时网格从Skin→Prune Small Weights齿轮设置阈值，准备低于、等于、高于阈值及锁定小权重，测试Keep Strongest和Normalize After两选项并Undo | 待测试 |
| RG-17 | 分别在Object、单对象Edit Mesh、Weight Paint无遮罩/顶点遮罩/面遮罩执行两项；加入隐藏和未选顶点、第二所选对象以及X镜像设置 | 待测试 |
| RG-18 | 在常用缩放下分别点击两项正文和右对齐齿轮，打开参数后修改并取消，再确认执行；使用F9调整，再一次Undo | 待测试 |
| RG-19 | 在无骨架、多Armature修改器、共享或链接Mesh、多对象Edit、空顶点选择和锁定和超过1的测试副本尝试两项；另用本地网格引用链接只读骨架 | 待测试 |
| RG-20 | 在自己的生产角色副本执行有界清理后移动骨骼观察变形；保存到临时文件并用新进程重开，对照权重、组锁及原生Weights/插件菜单 | 待测试 |
| BI-M26 | Skin 蒙皮与权重：中英文菜单与对应界面 | 待测试 |

## 菜单 · Help 帮助

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MB-16 | Help 检查 Maya 灰占位及 Blender Help、Scripting Reference、Diagnostics | 待测试 |
| BI-M27 | Help 帮助：中英文菜单与对应界面 | 待测试 |

## 菜单 · Blender Extensions 原生扩展

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-29 | 中心按钮映射Blender Extensions后浏览各原生分组和原有改名/选择/显示操作 | 待测试 |
| BI-M28 | Blender Extensions 原生扩展：中英文菜单与对应界面 | 待测试 |

## 菜单 · Preferences → Keymap 键位设置

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| IN-01 | 使用包含2026-10-11修复的开发构建，按 https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-11-input-diagnostics-acceptance.md 的准备脚本创建Object Mode的Ctrl+F9、Mesh的P及3D View的Ctrl+F10临时测试项；在Keymap偏好重载AxisMeld配置 | 待测试 |
| IN-02 | 同一开发构建与隔离实例，再添加Mesh的Ctrl+F9及Object Mode的P；重载并查看提示，检查对应插件项属性 | 待测试 |
| IN-03 | 用输入诊断验收清理代码移除本次创建的测试项，重载配置；退出隔离实例后检查正常配置 | 待测试 |
| GU-15 | 在 Preferences→Keymap 使用 Name 搜索 Move、Frame All、Convert Selection 和 AxisMeld；展开结果并改键，再用 Key-Binding 搜索；切回 Blender 预设查看原生条目 | 待测试 |
| BI-M29 | Preferences → Keymap 键位设置：中英文菜单与对应界面 | 待测试 |

## 通用 · Q/W/E/R 工具热盒交互

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| G-02 | W/E/R经过World/Object按钮后继续水平向外滑出很远，再松LMB | 待测试 |
| G-04 | 进入Axis/Custom Axis/Select子环继续外划，再回当前中心后重新划选 | 待测试 |
| G-05 | 在键位偏好将一个中心鼠标按钮映射为Marking Menus，再从该入口打开工具热盒，外划释放或回最初LMB点 | 待测试 |
| G-06 | 分别持续按住Q/W/E/R，反复按住/松开LMB至少三次，在不同鼠标位置唤出 | 待测试 |
| G-07 | 同次QWER持键先空中心松LMB，再禁用项松LMB，再选择有效项 | 待测试 |
| G-08 | 第二次开环后分别先松QWER、Esc、切应用、W切E并交换释放顺序 | 待测试 |
| T-01 | 点按 Q/W/E/R；再仅长按，不按鼠标 | 历史已测 · 未判定 |
| T-02 | 保持工具键，按住左键打开，拖向目标先松左键 | 历史已测 · 未判定 |
| T-03 | 进入 Axis/Select 子环或设置目录，返回父级后选另一项 | 历史已测 · 未判定 |
| T-04 | 分别先松左键、先松工具键、Esc、切应用；左边缘原地释放及返回起点释放 | 历史已测 · 未判定 |
| T-05 | W 未松时按 E；依次交换 W/E 释放顺序；长按产生键盘重复 | 历史已测 · 未判定 |
| T-06 | W/E/R 分别设不同 Global/Local/Normal；切换工具后直接拖轴和点轴后空白中键拖 | 历史已测 · 未判定 |
| IC-03 | 分别持Q/W/E/R反复按LMB开盒，进入Axis/Custom Axis等子环 | 待测试 |
| HC-13 | 从Q/W/E/R各进入Select子环，然后进入Soft Select并返回 | 待测试 |
| HC-14 | 分别进入W/E/R的Selection Constraints、Transform Constraints与中心选项 | 待测试 |
| HC-15 | 逐个检查QWER的Symmetry、Soft Select、Axis/Custom和Snap子菜单 | 待测试 |
| FM-09 | QWER重复：持续按住Q/W/E/R，在不同位置连续三次按放LMB，交替进入子环和完整伴随列表 | 待测试 |
| GU-02 | 激活 Q/W/E/R 各工具，Ctrl+Shift+RMB 开当前工具热盒，中心取消并重复打开，再选有效方向；另外选非对应的原生工具 | 待测试 |
| GU-21 | 分别保持 W、E、R 按下，LMB 唤出热盒并进入 Selection Constraints 子菜单；在灰 UV Edge Loop 上松 LMB，再换位置按 LMB；以原点取消、选择 World 后重复，最后松开工具键 | 待测试 |

## 通用 · 点/边/面建模热盒交互

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| D-01 | Edit Mesh分别只启用点/边/面域并选择组件，Shift+RMB开环 | 待测试 |
| D-02 | 适当选区分别执行Smooth Vertices、Poke Faces、Spin CW/CCW、Collapse与Dissolve Edges，每次单Undo | 待测试 |
| D-03 | 点域/边域分别从E启动Bevel，移动鼠标、调整参数并确认；另一次Esc | 待测试 |
| D-04 | 边域S Extrude Edges、面域S Extrude Region，移动后确认并单Undo；另一次Esc，再与Ctrl+E对照 | 待测试 |
| D-06 | 点/面Normals与边Sharpness子环切换真实法线/锐边显示，执行Reverse、Recalculate、Mark/Clear Sharp等适用项 | 待测试 |
| D-07 | W激活Knife后在临时面实际切一刀并确认/撤销；NW激活Circle Select并实际改变选区 | 待测试 |
| D-08 | 尝试Vertex Extrude/Delete Vertex、Face Boundary Bevel/Wedge、Target Weld等计划项 | 待测试 |
| D-09 | 中心/回真实起点/Esc/失焦取消；交换Shift和RMB释放；松非拥有鼠标；中途加Ctrl/Alt或更换选择域 | 待测试 |
| D-10 | Edit空选择、混合域、非网格模式；Object无选择空白及有选择对象分别Shift+RMB | 待测试 |
| D-13 | 多对象Edit各保留不同选区，鼠标移到未编辑对象再开环；每Mesh仅1点时查看需要2点的Merge等 | 待测试 |
| GU-03 | Edit Mesh 单一 Vertex/Edge/Face 模式中清空选择，鼠标分别停在可见组件和空白，Shift+RMB 打开、悬停、中心释放与 Esc；加入隐藏元素及多对象编辑 | 待测试 |

## 通用 · 热盒布局、外划与取消

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| G-01 | QWER与四视图二级热盒对照，单/四视图查看 | 待测试 |
| G-03 | Q选择工具与组件RMB环，在未被伴随列表覆盖的按钮外延释放；划向禁用方向或缺席的NW；组件S方向另从Face主按钮提交 | 待测试 |
| G-10 | 四角/窄视口与125/150/200%DPI，进入完整原生列表/单选设置后滑出列表 | 待测试 |
| R-01 | 100%、125%、150%、200% 缩放下，单/四视图重复 C-01、V-01、T-03 | 历史已测 · 未判定 |
| R-05 | 两个 Blender 窗口间切换，弹窗打开时尝试热盒；返回后重试 | 历史已测 · 未判定 |
| L-01 | 同一窗口与缩放下，依次打开Views、Q/W/E/R主环；截取或目视比较第2/4行和第3行左右内缘 | 待测试 |
| L-02 | 在临时Cube上打开组件RMB，再到空白无选择处打开Shift+RMB创建环，与Views比较；只在中心取消 | 待测试 |
| L-03 | W/E/R进入Axis与Custom Axis子环，Q进入选择子环，再通过中心按钮映射Marking Menus进入相同子环 | 待测试 |
| L-04 | 单视口将鼠标移入第2/4行左右内缘之间的新留白，分别原地松键、回起点释放；再向对应按钮外侧远划释放 | 待测试 |
| L-05 | 在四视图各分区和视口四角打开Views、W与创建环；重复有效外划、缺席/禁用方向、回中心 | 待测试 |
| L-06 | 分别在125/150/200%系统缩放和较窄视口重做L-01/L-04；同时查看长标签原生列表 | 待测试 |
| VR-03 | 分别保留左工具栏、右侧栏及二者同时可见，在四角打开方向热盒和原生长列表 | 待测试 |
| VR-04 | 热盒开启后切换Tool Header/左工具栏/右侧栏显隐，并调整侧栏宽度 | 待测试 |
| VR-05 | 开启动画，在侧栏显隐动画过程中反复打开热盒，再等动画结束 | 待测试 |
| VR-06 | 四视图保留Tool Header与侧栏，在四个分窗分别测试VR-01/02/03；125/150/200%DPI重试 | 待测试 |
| VR-07 | 四角打开Views、QWER、普通组件RMB与创建环，向按钮外延划选，再回真实按下点 | 待测试 |
| VR-08 | 先缩小视口，再缩小整个窗口直到所有固定尺寸列也无法容纳，随后恢复大小 | 待测试 |
| D-12 | 单/四视图、四角、125–200%DPI打开三根与所有子环，对照Views第2/4行、第3行左右内缘；远处释放和缺席方向 | 待测试 |
| IC-13 | 同一实例将Views与QWER/组件/创建/建模五行热盒对照，经过第2/4行及第3行间隙后外划 | 待测试 |
| MC-11 | 单/四视图与1x/2x，分别对比Views、Object、创建的真实按钮内缘及长标签 | 待测试 |
| MC-12 | 在四个视口角落及125/150/200%DPI展开完整伴随列表与末项子菜单，再回真实按下点 | 待测试 |
| FM-02 | 底部对齐：在视口中下方和四角打开可在该视口完整容纳的组合菜单 | 待测试 |
| FM-03 | 不整体侧翻：从中部逐渐靠近视口底边重复打开伴随列表 | 待测试 |
| FM-05 | 跨pane源操作：四视图中从一个pane开菜单，在跨到另一pane的条目上执行可观察的视图/选择动作，再取消一次 | 待测试 |
| FM-08 | 取消起点：平移和跨pane布局后分别回真实按下点、当前父子返回区、按Esc和失焦 | 待测试 |
| FM-10 | 窗口生命周期：持菜单时调整窗口大小、拆合pane、切工作区、关闭独立副窗；整窗极小后恢复重试 | 待测试 |

## 通用 · 完整列表、级联与图标

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| S-07 | 窄视口、四视图、125/150/200%DPI查看三类列表；再测Rows和QWER普通项 | 历史已测 · 未判定 |
| M3-33 | 窄视口/四视图/125–200%DPI打开M3长列表，检查全部条目、真实子菜单、最下项与移出列表；在设置项重复改变值 | 待测试 |
| IC-07 | 展开Edit/Create/Mapping/Booleans等完整普通菜单和多级目录，检查必要的多列布局 | 待测试 |
| IC-11 | 100/125/150/200% UI缩放，检查短标签、最长标签和级联目录 | 待测试 |
| IC-12 | 使用Blender深色和浅色主题，比较普通/悬停/禁用状态 | 待测试 |
| IC-14 | 执行一个进入Recent的功能，再从Recent/普通菜单比较；切换个人热盒配置和中英文标签 | 待测试 |
| MC-03 | 单视图1x/2x对照普通行和每个分隔，慢移鼠标跨过所有分隔 | 待测试 |
| MC-04 | 持住RMB在Object及创建的分隔线上释放，再在其左右列表背景释放 | 待测试 |
| HC-19 | 检查全部新列表的首末条目，查看长标签、子目录箭头、Options方格和左侧图标 | 待测试 |
| HC-20 | 在单/四视图、窄视口和125/150/200%DPI，重试RMB、建模与QWER嵌套菜单及取消 | 待测试 |
| FM-01 | 完整展开：分别打开Object、Create、Component、Face、QWER与Space长目录，逐项对照清单 | 待测试 |
| FM-04 | 在1x/2x和窄视口查看真实Display→Polygons、Show→Viewport等较长子目录，逐列核对顺序和末项 | 待测试 |
| FM-06 | 图标与参数：1x/2x检查每列首末项、禁用项、radio/checkbox和Options；进入Mapping/Booleans等目录 | 待测试 |
| FM-07 | 滚轮消费：持住RMB、Space或QWER，在主环、列表、跨pane列上滚轮及触控板平移/缩放 | 待测试 |
| MT-31 | 在单/四视图中下部打开各层；1x/2x检查带字标题、普通分隔和末项 | 待测试 |
| MB-19 | 在 1x/2x、较矮窗口及靠近下边缘处逐层打开 File、Generate、Delete All by Type 等菜单 | 历史条目 · 待测试 |
| MB-39 | 在100%/150%常用缩放下打开短长标签、状态圆圈/勾选项及多列菜单，分别点击正文和右侧齿轮 | 待测试 |
| GU-26 | 热盒下方列表缩至 90%，周围按钮保持原样 | 历史条目 · 待测试 |
| GU-27 | 热盒下方列表固定16像素行高，周围按钮保持原样 | 历史条目 · 待测试 |
| GU-28 | 热盒下方列表改为18像素行高，检查可读性与操作手感 | 待测试 |

## 通用 · 外观设置与真实状态

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| S-04 | 从Controls和Views两个入口打开Hotbox Style，依次改显示方式再重开 | 历史已测 · 未判定 |
| M3-12 | Display/Modify设置：分别改变X-Ray、Wire/Solid、选择/变换相关可选设置；悬停另一项但不提交，然后从原生UI改回并重开菜单 | 待测试 |
| IC-08 | 打开含radio/checkbox的完整设置列表，切换选项并重新开盒，检查各列 | 待测试 |
| MT-25 | Views和Controls分别打开Hotbox Style，再打开Set Transparency | 待测试 |
| BI-C02 | 翻译开关：界面、工具提示与新建数据名称独立 | 待测试 |

## 通用 · 灰项、Options 与键盘导航

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-02 | 空场景、仅Empty、Mesh Object、Mesh Edit空选择分别检查Mesh/Deform/组件编辑项；尝试点击灰显项 | 待测试 |
| IC-10 | 比较同一热盒或列表内的可用项与灰显项，悬停及尝试释放 | 待测试 |
| MT-26 | 在22主菜单及创建/建模热盒逐个尝试灰显参数方格，再试正文 | 待测试 |
| MT-28 | 尝试Select→Use Constraints/Similar、Modify→Prefix Hierarchy Names/Search and Replace Names、Deform→Edit Membership Tool、Curves→Duplicate Surface Curves | 待测试 |
| GU-18 | 在有灰 Options 的建模菜单中，用上下方向键逐行移动并检查首尾循环；鼠标悬停灰齿轮；在有效绑定网格的 Rigging→Skin 中用键盘打开 Normalize Weights 的可用 Options，再检查普通 Blender 菜单 | 待测试 |
| GU-20 | 在 Modeling 的 Object Mode 清空选择和活动对象，依次悬停 Curves→Control Points 下的原生灰项、Edit Mesh→底部 Extrude 目录里的灰 Extrude；检查 UV 与 Modifier 原生条目；再选网格或曲线切到对应 Edit Mode，重新打开相同菜单 | 待测试 |

## 通用 · 灰项说明与窗口避让

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| GU-19 | 将测试窗口缩窄至约 960 像素，分别使用 100% 和 150% UI 缩放；从 Space→Edit 悬停 Duplicate Special 等长说明，再检查 History 热盒中的适配说明，最后恢复宽窗口 | 待测试 |
| GU-22 | 使用包含本批说明修复的新构建，将窗口缩到低高度，分别在 100% 与 150% 界面缩放下悬停 Space→Edit→Duplicate Special、A+LMB 的灰 History 项；再切四视图、换边缘位置，逐步缩窄后恢复窗口 | 待测试 |

## 通用 · 跨入口操作与回归

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| K-12 | 创建成功后检查Space→Recent并在Object重放；再在Edit查看同项；取消创建后重新检查 | 待测试 |
| C-11 | Space → Select → Active Mesh Components 切点/边/面/Object；另从 Space → Modify → Tool Settings 打开工具环 | 历史已测 · 未判定 |
| M3-06 | Edit/Modify：两个已变换对象Group、Ungroup、Match；另以静态单条开口/闭合Curve为活动源，从Object Relationships→Place Along Active Curve分布无父级、约束、动画及delta位移的对象，源加旋转/非均匀缩放后重试；再试父子循环、零长度Curve与受驱动目标，每个有效动作单Undo/Redo | 待测试 |
| M3-27 | Deform：临时细分网格试Bend/Twist/Taper/Stretch、Static Wave、Texture Displace与Smooth，调参并Undo；再从Edit→Delete by Type依次执行Delete All Hook Modifiers、Delete All Lattice Modifiers、Delete All Nonlinear Modifiers、Delete All Curve Deform Modifiers，准备当前Scene已选/未选对象及另一Scene独立对象，每项单Undo/Redo | 待测试 |
| M3-32 | 两个Blender窗口或单/四视图之间切换，保持Space进深层列表后先松Space、Esc、切应用；紧接着按QWER和普通RMB重试 | 待测试 |
| D-14 | 执行可重放非modal项后查看Recent；取消、灰显计划、仅激活Knife、挤出启动后取消分别对照，再测试普通RMB/QWER/Space | 待测试 |
| O-16 | 尝试N/NE/S/NW占位及SE Soften/Harden目录，再测试普通RMB、QWER持键重复开盒、已有Edit根及Recent | 待测试 |
| IC-05 | 无选择在空白Shift+RMB打开基本体创建热盒，再经Space→Create查看列表 | 待测试 |
| IC-06 | 选中Object与Edit单域组件，Shift+RMB检查建模环及Object下方列表 | 待测试 |
| MC-08 | Object径向SE Soften/Harden展开，查看子目录并返回主环；创建Polygon Display All也展开 | 待测试 |
| MC-10 | 在无选择空白、有效Mesh选择、鼠标预选Mesh、非Mesh阻挡、Edit各状态分别重开；再从Space Create目录进入 | 待测试 |
| MC-13 | 创建与Object连续开关各三次；Q/W/E/R持键LMB重复唤出；Space中心目录交替进入 | 待测试 |
| MC-14 | 径向主项/参数/下拉/级联中分别Esc、先松Shift、切应用、改选择/模式后释放；随后再开Views和创建 | 待测试 |
| HC-18 | Object建模和创建热盒逐项对照Maya截图，并检查Mapping、Booleans和Polygon Display | 待测试 |
| MT-24 | W+LMB→Snap，检查三个方向和下方列表；进入Object/Face建模→Mapping | 待测试 |
| MT-32 | 重复RMB、Shift+RMB、QWER、Views/Controls/Recent，交替进入22主菜单后取消 | 待测试 |
| MB-27 | 检查 Maya Point to Point、Duplicate Special 及独立 Blender Selection to Active、Duplicate Linked | 待测试 |
| GU-24 | 在 5.4 合并构建中重试 QWER 持键重复 LMB、组件与建模 Shift+RMB、X/V/J 临时吸附及一次 Undo；从 Space→File 打开和另存临时文件，跨文件窗口释放触发键并取消，再正常保存、关闭和重开临时场景 | 待测试 |

## 通用 · 改键、配置与输入隔离

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| S-06 | 重载个人配置或重启预览程序，确认外观/改键 | 历史已测 · 未判定 |
| R-03 | UV Editor、文本输入、Sculpt 下使用 QWER/右键 | 历史已测 · 未判定 |
| R-04 | 保留个人改键、底色、不透明度、文字颜色后重启 | 历史已测 · 未判定 |
| M3-34 | 备份个人配置；临时改一个M3快捷键、保留原QWER/底色/透明度，重载并重启；浏览M3灰显计划、UV及M2后续占位 | 待测试 |
| D-11 | 备份配置，分别改绑/禁用CREATE与MODEL，尝试F13、Ctrl+F13、Shift+MMB；重载两次并检查冲突提示 | 待测试 |
| O-12 | 分别改绑/禁用CREATE和MODEL，测试Shift+RMB、Ctrl+Shift+MMB及键盘映射 | 待测试 |
| GU-12 | 在隔离实例切换 Grease Pencil 绘画、UV编辑器、非3D编辑器及 Blender/Industry Compatible 键位；返回 AxisMeld，重载个人改键并重试 Ctrl 入口与持键 | 待测试 |
| BI-C01 | 语言设置：仅英文与简体中文两种版本 | 待测试 |
| BI-C03 | 保存语言后重启：中英偏好与原配置保持 | 待测试 |
| BI-C04 | 旧语言偏好迁移：Automatic、第三语言及原中英文 | 待测试 |

## 通用 · 全局栏与工作区

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MB-17 | 多 3D 区域、四视图以及完全无 3D 的工作区分别打开菜单，检查建模操作可用性 | 待测试 |
| MB-18 | 打开菜单后改变源区域、场景、视图层或工作区，再尝试原菜单动作 | 待测试 |
| MB-20 | 在 AxisMeld 与标准 Blender 键位之间切换，再检查工作区标签和 Back to Previous；复测 RMB/Shift+RMB/QWER/Space | 待测试 |
| MB-28 | 在 Maya 配置中检查顶部双排，点击 Layout、Modeling、UV Editing 往返，再使用下排 Create 创建临时模型并撤销 | 历史条目 · 待测试 |
| MB-29 | 切换 Maya/Blender 键位配置；调整窗口宽度及界面缩放，检查主窗口、最大化编辑器和工作区右键菜单 | 历史条目 · 待测试 |
| MB-30 | 在 Maya/Blender 配置间切换，点击 Layout、Modeling、UV Editing；检查全局 File/Edit/Render/Window/Help、Scene/View Layer | 待测试 |
| RG-07 | 使用本轮Rigging预览构建的隔离工厂配置启动，查看Layout、Modeling、Rigging；在三者之间往返，并分别使用Blender和Maya键位检查Rigging视窗 | 待测试 |
| RG-08 | 在临时配置用顶部+→General→Rigging添加工作区；再打开一个不含Rigging的旧测试blend，分别检查Load UI开启与关闭的行为 | 待测试 |
| RG-14 | 在临时文件中将Rigging重命名并复制，分别检查Skeleton/Skin；保存、退出并以新进程重开；在Object、Edit Armature、Pose、Weight Paint及非骨架编辑模式间切换；分别删除含用途标记的活动与非活动工作区副本 | 待测试 |
| GU-25 | 用 5.4 合并包的隔离配置从工厂启动，检查 Layout、Modeling、Rigging；使用临时副本打开以前的 AxisMeld 场景，切换工作区后保存重开；在 Rigging 创建 metarig、生成测试 rig，查看 Skeleton/Skin 与灰项说明，再切 Blender 键位 | 待测试 |
| BI-C05 | 工作区与用户命名：中文按钮和真实数据名分离 | 待测试 |

## 通用 · 建模菜单归类与原生扩展

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MB-02 | 打开 Modeling 的 Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、Deform、UV、Generate | 历史条目 · 待测试 |
| MB-22 | 检查 Mesh、Edit Mesh、Mesh Display、Curves、Surfaces 的补充操作及分隔标题 | 待测试 |
| MB-31 | 在 Modeling 的 View/Select/Add/Object 所在行检查13个建模根；切 Object、Edit Mesh、无选择和 Curve 编辑，再回 Layout | 历史条目 · 待测试 |
| MB-33 | Edit Mesh 下打开 Mesh/Vertex/Edge/Face/UV→Blender Tools；检查已启用插件的 File/Import 和点线面菜单扩展 | 历史条目 · 待测试 |
| MB-35 | 在Modeling检查Mesh/Edit Mesh/Vertex/Edge/Face/Mesh Tools/Mesh Display/Curves/Surfaces/UV，展开Mesh Tools→Curve Projection | 历史条目 · 待测试 |
| MB-36 | 按新版去向表查找原生切割、法线、UV和点线面操作；对照同一Blender原生工作区 | 待测试 |
| MB-38 | 在Modeling的Object/Edit Mesh/无对象、Curve/Surface编辑及Layout之间切换，检查原生插件菜单和资产入口；增加节点资产后检查动态目录高度与滚动 | 待测试 |
| MB-40 | 在Modeling查看Mesh/Edit Mesh/Mesh Tools/Mesh Display/Curves/Surfaces/UV；打开Edit Mesh的Vertex、Edge、Face，执行原生操作及Undo，检查插件追加菜单，再切回Layout | 待测试 |
| GU-23 | 使用 Blender 5.4 主干合并预览包和临时场景，选择 AxisMeld Maya 2026；检查 Modeling 七根菜单、Edit Mesh 的 Vertex/Edge/Face 子目录及 Transform 内新增的原生 Loop Tools 入口；在 Object、Mesh Edit、Curve Edit 和无活动对象时分别打开相关目录 | 待测试 |

## 通用 · Maya 菜单集与层级

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| M3-01 | Object临时场景按住Space，逐个进入22个Maya主菜单；再从中心映射的Blender Extensions浏览原生扩展能力 | 待测试 |
| MB-01 | 依次切换顶部 Modeling、Rigging、Animation、FX、Rendering 菜单集 | 历史条目 · 待测试 |
| MB-03 | 检查 Rigging、Animation 的 Skeleton/Skin/Constrain/Control、Key/Playback/Audio/Visualize 及 Deform | 待测试 |
| MB-04 | 检查 FX、Rendering 的粒子/流体/布料/毛发/约束/缓存/场/特效及灯光材质/纹理/渲染/Toon/Stereo | 待测试 |
| MB-05 | 展开 Cache、Flow、Arnold、MASH、Bifrost Rigging 和 Generate 的 XGen 区域 | 历史条目 · 待测试 |
| MB-15 | Rendering→Render 和 Windows→Rendering Editors→Render，检查图像、动画、音频、结果查看及 Lock Interface | 待测试 |
| MB-21 | 逐章检查 Select、Modify、Display 的补充目录和前后 Maya 标题 | 待测试 |
| MB-25 | 检查 File→Save and Recover，以及 Create→Polygon Primitives 的 Additional/Subdivision Primitives | 待测试 |
| MB-34 | 打开 Window→Maya Menu Sets 的五个集合，按去向表找公共及专用功能；在窄窗口和常用缩放下复测视窗栏与长菜单末项 | 历史条目 · 待测试 |

## 通用 · 动态菜单与场景数据

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MT-30 | 核对File最近记录、Windows工作区、相机/材质/UV集以及Show→Isolate Select→Bookmarks | 待测试 |
| GU-11 | 查看 Recent Increments、Recent Projects、Delete by Type的Sounds、Quick Select Sets、Assign Existing Set 等空动态目录；同时查看有固定灰正文的目录和真实原生资产/插件菜单 | 待测试 |

## 通用 · Rigging 菜单与灰项

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| RG-09 | 对照Maya参考逐层查看Skeleton的Joints/IK/Joint Labelling和Skin的Bind/Weight Maps/Normalize Weights/Edit Influences；在常用缩放及较矮窗口检查末项、灰正文与独立Options | 待测试 |
| GU-16 | 在 Rigging 默认网格、无活动对象、单骨架和有效绑定选集之间切换，悬停 Skeleton 的 Edit Bones/Pose/IK 与 Skin 的 Armature Deform/Weights 等灰项；满足提示条件后重新打开菜单 | 待测试 |

## 其他 · Rigify 创建、生成与偏好

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| RG-01 | 使用Rigify预览构建，分别以隔离工厂配置和普通方式启动；不安装、不手动启用Rigify，直接查看视窗Add→Armature中的metarig与骨架数据的Rigify入口 | 待测试 |
| RG-02 | 在Rigify预览构建的临时场景，经视窗Add→Armature添加Human metarig；选中它，在骨架数据的Rigify面板执行Generate Rig；选择生成rig进入Pose Mode并移动手或脚控制骨 | 待测试 |
| RG-03 | 将RG-02自建场景另存为临时blend，关闭并用同一Rigify构建重开；检查控制骨、metarig的Rigify属性和目标关联，再修改metarig并执行Re-Generate Rig | 待测试 |
| RG-04 | 准备旧Rigify偏好及Feature Set目录的临时副本，包含至少一个仍已安装但禁用的兼容Feature Set；记录其状态，用Rigify预览构建普通启动，保存临时偏好后再次启动 | 待测试 |
| RG-05 | 在Rigify预览构建打开Preferences→Animation→Rigify，检查Feature Sets列表与选中项详情；关闭并重新打开偏好，再与RG-04记录的设置对照 | 待测试 |
| RG-06 | 在独立临时配置和已保存的临时场景中，通过命令搜索执行Reload Scripts两次，每次检查Add→Armature和Rigify面板并创建、生成一个测试metarig；另用独立临时配置执行Load Factory Settings后重复 | 待测试 |
| BI-C06 | 内置 Rigify：面板、生成控制 UI 与枚举中英切换 | 待测试 |

## 其他 · X/V/J 临时吸附

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| GU-06 | 原吸附关闭及开启两种状态，分别先持 X 再拖动 Move、变换中再按 X；先松 X、确认仍持 X、Esc、切应用后回到窗口 | 待测试 |
| GU-07 | 临时场景设置独立目标顶点，先持 V 再移动及移动中再按 V，先松字母或先确认；之后再移动一次 | 待测试 |
| GU-08 | Translate/Rotate/Scale 中测试 J；按 J→X→V 并按不同顺序释放，叠加 Ctrl，切换变换模式，再取消或确认 | 待测试 |

## 其他 · 预览包与公开测试反馈

| 编号 | 测试内容 | 原始状态 |
|---|---|---|
| MB-41 | 从GitHub仓库首页进入公开测试页，下载Windows便携预览包并启动；用另一个浏览器记录测试结果，导出JSON，再通过GitHub提交带版本的反馈 | 待测试 |
