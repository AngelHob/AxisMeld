# M1 常用工具热盒：Maya 对照和缺失能力计划

日期：2026-09-11。状态：来源与接入目标已核实，开发中；具体实现/自动化/手测状态以
[M1 集中验收表](../compatibility/2026-09-11-m1-tool-hotboxes.md)为准，不由本表推定已完成。

范围与分类规则见[已批准规格](../superpowers/specs/2026-09-11-modeling-interaction-alignment-design.md)。
UV 的快捷键、选择、编辑器和算法全部后置。本表中的 UV 相关名字只代表保留占位。

## 1. 触发与基线证据

来源为本机 Maya 2026 安装中的 `scripts/startup` 与 `scripts/others`，只提取功能身份、
输入、菜单方位和可观察行为，不复制 Autodesk 实现代码。

| 证据 | 核实内容 | 不能据此宣称的内容 |
|---|---|---|
| `startup/hotkeySetup.mel:319-321,341-346` | Q/W/E/R 有独立按下与释放命令；Shift+Q、Alt+Q 是其他入口 | 其他修饰键热盒已实现 |
| `others/buildSelectMM.mel`、`buildTranslateMM.mel`、`buildRotateMM.mel`、`buildScaleMM.mel` | 按键先进入相应工具；菜单等待 LMB，不是单纯等待长按时间 | 用户自定义菜单/Modeling Toolkit 变体也完全相同 |
| `others/buildToolOptionsMM.mel:31`、`drInit.mel:2530-2536` | Toolkit 活动且开启自定义菜单时可转入 Toolkit 的菜单路径 | 经典工具定义就是所有配置下的唯一显示内容 |
| `others/destroySTRSMarkingMenu.mel` | 原工具再次点按可能重置当前轴柄；打开过菜单则不走该重置 | AxisMeld 本批已复刻重置轴柄和枢轴编辑模式退出 |

本批目标是经典 Maya 工具菜单的固定方向和组合形式。保持 AxisMeld 已有单次选工具行为，
不额外改变同工具再次点按的轴柄重置。用户若使用 Toolkit 特定变体，应作为独立差异记录，
不污染公共 Maya 基线，也不能静默宣称与其个人配置一致。

## 2. 固定方向对照

表中英文为本批功能展示标签；方向及功能身份来自默认 MEL 菜单定义。完整翻译资源文字、
Toolkit 变体及主观手感未据此验收。N/S 是共享设置组入口，展开后按已批准规范使用普通菜单。

| 方向 | Q 选择 | W 移动 | E 旋转 | R 缩放 |
|---|---|---|---|---|
| N | Symmetry | Symmetry | Symmetry | Symmetry |
| NE | Drag Select | Normal Average | Normal Average | Normal Average |
| E | Camera Based Selection | Snap | Gimbal | Discrete Scale |
| SE | Clear Selection | Keep Spacing | Discrete Rotate | Relative |
| S | Select | Select | Select | Select |
| SW | Lasso Select | Axis | Custom Axis | Axis |
| W | Paint Selection | World | World | World |
| NW | Marquee Select | Object | Object | Object |

方向来源：`selectMarkingMenuImpl.mel:31-55`；`translateMarkingMenuImpl.mel:18-42,100-170`；
`rotateMarkingMenuImpl.mel:19-92`；`scaleMarkingMenuImpl.mel:18-123`；
共享 N/S 入口见 `commonReflectionOptionsPopup.mel` 和 `commonSelectOptionsPopup.mel`。
旋转 NW 的内部资源键为 `kLocalLabel`，操作为原生对象轴模式；不能把它与位移/缩放的
父层 Local 轴定义混为一谈。

## 3. 首批已有能力的适配边界

| 功能 | Blender 对应能力 | 对外声明 |
|---|---|---|
| Marquee Select | Box Select 工具 | adapted；沿用 Blender 框选方式 |
| Lasso Select | Lasso Select 工具 | adapted；选区/完成逻辑沿用 Blender |
| Paint Selection | Circle Select 工具 | adapted；不是完整 Maya Paint Select 笔刷 |
| Clear Selection | 当前 Object / Mesh Edit 的原生 DESELECT | 保持当前模式；此处对照 `select -clear`，不冒充另一入口 Select None 的模式切换流程 |
| World / Object | GLOBAL / LOCAL 变换方向 | adapted；不改变原生变换数学或物体 Global 缩放差异 |
| Normal Average | NORMAL 方向 | adapted；平均规则和有效上下文以 Blender 为准 |
| Gimbal（旋转） | GIMBAL 方向 | adapted；欧拉/四元数和锁轴差异不承诺消除 |
| View (Blender) | VIEW 方向 | Blender 独有扩展，放到轴设置的普通菜单，不占用 Maya 固定快速划选方向 |

Blender 现有 `Scene.transform_orientation_slots[1/2/3]` 分别服务位移/旋转/缩放；
`BKE_scene_orientation_slot_get` 检查 SELECT 标志决定是否采用专用槽。
RNA `use` 的显示描述与实际标志容易混淆，必须结合原生 getter 和实际 gizmo 测试确认，
不能只看属性名。AxisMeld 中键轴拖动复用 `WIDGETGROUP_gizmo_invoke_prepare`，应与直接拖轴
读取同一工具方向，测试须确认工具之间不互相覆盖。

本批主任务已定点核实消费链：`DNA_scene_types.h:2775-2777` 定义 1/2/3；
`rna_scene.cc:3392` 将 `use` 映射到 SELECT；`scene.cc:2638-2660` 按工具标志取专用槽；
`transform_gizmo_3d.cc:1986-2010` 按 builtin.move/rotate/scale 设置工具标志，
`:2314-2326` 将该方向写入原生 gizmo 操作参数，`:2382` 的 AxisMeld 中键路径调用同一准备函数。
GUI 已验证三个真实槽相互独立，已有操纵器回归另行通过。此处是源代码消费链与槽状态证据，
不是每种方向下实体鼠标拖拽结果的完整矩阵；后者保留在 M1-05 人工验收。

菜单中的坐标方向是场景工具设置，不写入 `hotbox_user.json` 的颜色/菜单配置，
也不引入独立复制场景数据的 AxisMeld 变换系统。

## 4. 占位计划（非功能完成表）

这些编号覆盖一组相同能力的多个入口；各具体按钮使用自己的稳定节点 ID。
“尚未适配”不等于证明 Blender 没有相似能力。接入前先归类，已有原生能力优先直接适配。

| 编号 | 覆盖内容 | 当前缺口与依赖 | 后续验收目标 |
|---|---|---|---|
| M1-P01 | Symmetry、Object/World/Topology 对称选项 | Maya 对称选择/编辑与 Blender Mirror/拓扑镜像的作用域不完全相同；需明确选择和变形各自适配 | 点/边/面、多对象、对象轴和世界轴、关闭恢复、撤销，不误改未选网格 |
| M1-P02 | Drag Select | Maya 连续拖过组件选择与 Box/Circle/Lasso 不同；需核对原生选择路径 | 拖过增选/减选、可见性、释放/取消以及不误启动变换 |
| M1-P03 | Camera Based / Auto Camera Based Selection | 需要明确深度选择与 Blender X-Ray、遮挡和框选规则的对应；原生可用能力尚未适配 | 可见/背面/遮挡组件、不同 shading 状态和选择工具；切换前后显示状态可预测 |
| M1-P04 | Keep Spacing | 多组件吸附时相对间距语义需与原生吸附组合核对 | 多点相对距离、目标吸附、取消和一次撤销 |
| M1-P05 | Discrete Move/Rotate/Scale、Relative、Vertex、Face Center snapping | 原生吸附可复用，但当前未验证 Maya 步长、相对起点、live 目标与三工具独立设置 | 三工具步长/相对模式、临时按键释放、正负方向、确认/取消；不扩展 Global 缩放数学 |
| M1-P06 | Local/Live Object/Rotation Axis、Custom Axis、轴对齐 | 区分父层 Local 与 Object，核对自定义方向创建/引用及失效对象处理 | 对象父子关系、组件定向、失效目标、保存重载、三工具相互隔离 |
| M1-P07 | Select 组高级选项、Soft Selection、预选高亮 | 可复用原生比例编辑/选择能力，但必须确认模式与临时状态，不用同名假实现 | 点/边/面选区、衰减与半径、进入/退出工具、撤销/取消、非目标模式不受影响 |
| M1-P08 | 其他 Tool Options：Smart Extrude/Duplicate、Pivot 变体、Tweak 等 | 分解成已有原生操作与 Maya 缺失能力；避免一次性开发所有工具选项 | 每项单独记录原生映射/缺口；工具保持、修改器影响、取消、一次撤销和菜单退出 |
| M1-P09 | Preserve UV 等 UV 相关条目 | 用户明确整体后置，本批无算法/交互接入 | 等 UV 专题开始后再定义；当前只验占位不可执行、UV 数据不变 |

## 5. 组合规范的本批应用

- 直接调用 Q/W/E/R 的工具热盒不显示一级 Space 热盒，也不新增中心返回按钮。
- 从 Space → Modify → Tool Settings 进入同一工具菜单，使用同一命令和方向定义。
- 一般选项采用普通菜单；不要因 Maya 某些历史设置子菜单也有 radial 标签就违反
  用户已确认的“方向动作热盒 + 设置普通菜单”组合规范。
- 保留已有 Space 的一级颜色和 75% 默认不透明度；工具热盒与子菜单使用原生不透明样式。
- 新增菜单不能让父背景截走鼠标，也不能让 Q 松键覆盖刚选中的 Lasso/Circle 工具。

## 6. M2 右键菜单的后续衔接（仅预检，不在 M1 启用）

`ModelEdMenu.mel` 将普通对象菜单与工具选项菜单分开；`buildObjectMenuItemsNow.mel`
先处理工具/枢轴特殊状态，再查询鼠标下对象，未命中才回退到当前选择/高亮集合。
空白处且没有适用选择时，可出现 Select All / Complete Tool，而不是固定组件菜单。
因此后续不能把“鼠标下对象”简单等同于 Blender 的 active_object，也不能把所有 RMB
都复用 Q/W/E/R 的菜单。Alt+RMB 导航必须先隔离。

`dagMenuProc.mel:887-895,974` 起按对象组件遮罩分配方向，皮肤工具等状态可以占用方向；
普通网格、曲线和枢轴编辑不能共用一张无上下文的固定表。UV / UV Shell 的原有方向
可以作为不可执行占位保留，但不因此启动 UV 适配。
