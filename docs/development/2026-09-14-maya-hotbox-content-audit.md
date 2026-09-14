# 现有热盒菜单内容逐项对齐 Maya 2026

## 范围

用户明确本轮问题主要是菜单和内容，不是触发条件或方向。按本机 Maya 2026 MEL 与 resources/MayaStrings 的实际英文文字检查全部现有热盒：组件 RMB、创建、Object/Vertex/Edge/Face 建模、QWER 及子菜单、Views、Space Controls 和 Recent。保持已有触发、拾取、方向、释放与 Views 几何标杆；不借此新增混合组件触发或改空白区规则。

菜单要保留真实条目、顺序、分隔、子目录、状态形态和实际存在的独立参数格。未实现的 Maya 能力逐项保留并说明原因，不能删成总括的短菜单；也不把相近但不同的 Blender 命令换名冒充。动态 DG、材质收藏、插件或场景数据不能用猜测的固定清单伪造。

## 已核实的缺口

Maya 来源根：`C:/Program Files/Autodesk/Maya2026/scripts/`。英文显示文字额外以 `../resources/MayaStrings` 核对，不能仅用 uiRes 的内部键推断。

| 范围 | 核实结果 | 主要来源 |
|---|---|---|
| 组件 RMB | 已有7向环，缺截图中的22项 DAG 下拉；UV缺UV/UV Shell子目录。对象名为动态首项 | others/dagMenuProc.mel:991-1010、2618-2806；startup/buildShaderMenus.mel:501-557 |
| Q | 缺 Automatic Camera-Based Selection 下方列表；部分标签、checkbox被替换为单项目录 | others/selectMarkingMenuImpl.mel:31-65 |
| W | 缺9个主项、3个分隔：两种约束、Shift Extrude/Duplicate、Preserve/Tweak/Triad及Move Options | others/translateMarkingMenuImpl.mel:55-99 |
| E | 缺11个主项、3个分隔，包含Rotate Center四项、Free Rotate、Relative及Rotate Options | others/rotateMarkingMenuImpl.mel:98-163 |
| R | 缺10个主项、3个分隔，包含Scale Center三项、Prevent Negative Scale及Scale Options | others/scaleMarkingMenuImpl.mel:129-187 |
| QWER 子菜单 | 共享Select缺下方自动相机选择项；真实标签、状态形态与当前部分解释性标签不一致；Maya不存在批量参数格 | commonSelectOptionsPopup.mel、commonReflectionOptionsPopup.mel、commonSelectionConstraintsOptionsPopup.mel |
| Vertex/Edge/Face 建模 | 三者均缺伴随列表；Edge Merge缺Merge Border Edges参数行；部分标签、参数格及目录形态需逐项复核 | contextPolyToolsVertexMM.mel、contextPolyToolsEdgeMM.mel、contextPolyToolsFaceMM.mel |
| 创建 | 主列表16项已齐；Polygon Display All实际为Backface Culling On/Off两项及4个分隔，当前合并为单toggle | contextPolyToolsDefaultMM.mel:373-439 |
| Object 建模 | 主列表22项已齐，继续核对嵌套内容与状态 | contextPolyToolsObjectMM.mel |
| Views | 七视图和三种Style已有，核对真实标签；不改现有方向和几何 | startup/HotboxCenterMenu.mel:143-175 |
| Controls | 缺多类Show/Hide条目、Custom Menu Set、Controls专用Style尾项与Window Options | startup/HotboxControlsMenu.mel:103-255 |
| Recent | 动态成功命令历史；保留现有10条及可重放白名单，不编造Maya历史 | startup/HotboxRecentMenu.mel:26-51 |

## 实现约束

1. 扩展既有 companion 映射和单一布局器，为缺失列表提供普通原生菜单；不新建独立 handler。活动子环对应的内容要正确跟随，父环保持既有返回与释放规则。
2. 固定内容放在 Python 声明目录，Maya 实际状态项采用状态图标，未适配状态明确禁用且不写偏好；只有实际存在 Options 的项带独立参数格。
3. 组件下拉只复用安全、作用范围明确的现有命令。打开、悬停、关闭不提交指针对象选择；全选、取消全选、反选不先选中指针对象。目标相关动作无安全适配时保留灰显。
4. 为新增可执行的上下文菜单行建立固定行ID/命令白名单，确认和取消仍经已有提交路径。Maya专有操作保留禁用原因，不扩大任意命令执行面。
5. 完整节点、深度及快照大小须实测；不为省空间删除条目或协议字段。只有有证据的容量需求才调整上限，并保留明确边界测试。
6. 原生图标沿用统一解析器。所有列表共享24逻辑像素行高、6像素分隔；参数背景不得遮挡目录箭头。

## 验证与交付

建立独立的Maya菜单内容预期，与最终目录逐项核对；运行相关Python、原生和真实GUI验证。真实画面检查主项/子菜单/Options/状态/滚动，在现有触发下检查无选择但指针有目标的RMB内容。回归只用于确保内容接入没有破坏既有手势，不把本轮误写为触发或方向修复。

新安装使用独立目录并保留前批候选与用户配置。新增人工检查与已测试历史统一进入清单和私人网页；网页服务端进度不被目录更新覆盖。最终记录固定菜单对齐情况和仍待适配的动态内容边界。

## 已落地的内容与边界

- 组件 RMB 新增22个主项、7处分隔，UV增加UV/UV Shell。标题来自实际捕获目标；全选、取消全选、反选不预提交指针选择，其余目标相关动作必须满足捕获选集与活动对象一致。
- Vertex/Edge/Face 分别增加9/14/20个主项及3/3/4处分隔。33个可执行菜单行复用已有适配器，并限制到对应组件域；未适配参数格不借用正文命令。
- Q/W/E/R 下方列表分别为1/9/11/10个主项，共享 Select 使用独立伴随列表。约束、中心、Symmetry、Soft Select、Axis/Custom 与 Snap 按实际资源文字补齐，状态形态逐项核对；没有给这些菜单虚构批量 Options 格。
- Object22与Create16个主项保留，Object大小写、Cleanup省略号、Difference括号按实际资源修正。创建 Polygon Display All 使用10项与4处分隔；Backface Culling On/Off 分别显式赋值，重复执行幂等。
- Controls补齐固定Show/Hide、Custom、Window和专属Style条目，现有三种行开关读取真实状态。Q的Marquee读取实际工具，方向勾选遵循Blender工具槽对场景方向的继承。
- Views保留七个视图方向及Front下方的Style位置。非Maya的New Camera灰项移除后，NE保留取消区；没有将Style移到NE。几何判断仍使用实际按钮内缘及Views标杆。

伴随列表占据的区域遵循已有Object/Create组合的优先级：命中列表或分隔时不穿透执行环的S外延。组件Face仍可从原S主按钮提交，未遮挡外延保留长划；GUI分别验证被遮挡点取消和主按钮执行。该内容覆盖边界已写入仍待测的G-03与HC-20，历史已测试行不改。

完整组合存在最小可用空间：实测200%、960×462物理像素（480×231逻辑像素）的四视图中，W环与最少分页行既不能上下放置，也不能左右并列。沿用已有组合布局的完整取消契约，不缩小Views间距或隐藏父环；正常W初按仍激活Move并保留持键owner，LMB请求显示失败后结束hotbox，短暂release guard只消费本轮物理释放。释放后无handler，场景/正常W工具状态/Recent不额外变化，Views可重新打开。同四视图150%实际W环与列表可见，三排内缘140/188/140像素与Views严格相等。不能把该不足空间个案报告成“200%所有四视图都可打开”。

动态DG/历史、场景UV与颜色集、Metadata流、材质收藏和插件专有菜单未接入的部分仍说明不可用；固定目录存在不表示这些能力已完成。未适配状态只允许精确声明的图标类型与未选中值，不能伪造当前Maya状态。新增菜单未改写已有触发、拾取与混合组件回退策略。

实际完整快照为18个根组、1798个节点、最大深度7、320056字节。加入10个Recent和已知能力拒绝原因的24种压力场景，最大339998字节；保留2048节点、深度8和512KiB上限。

本轮增加HC-01～HC-20人工检查；目录共211项，历史47项已测试记录逐行保留，164项待测。私人网页只更新目录，不写入或重置个人测试进度。
