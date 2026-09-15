# Maya 2026 顶部 Menu Bar 来源审计

2026-09-15；基线 AxisMeld HEAD `bff4cd9448a`。只读本机安装源码及既有隔离 Maya GUI 原始参考，未启动或操作 Maya。本次用户决定：Blender 独有能力按 Maya 用途归入对应菜单，覆盖上一批“仅留在独立 Blender Extensions”的展示约束；原能力与安全绑定边界仍保留。

## 结论与最小本批范围

顶部不是现有热盒的22根。Modeling状态的实际顶部顺序为 **Common 7 + Modeling 9 + Cache + Help，共18项**。既有22树中的另外6项属于当前modelPanel局部菜单，不应整体搬入应用顶部。

建议本批先完成这18项真实顶部结构与Blender原顶部能力重归属；复用已核验Common/Modeling静态参考16根，另补Cache/Help来源声明。菜单集选择器独立呈现当前Modeling状态；其他菜单集的真实名称/顺序已有源码依据，但不能用“点击选中而菜单不变”假装支持。若纳入切换，则必须同时有对应菜单集合与可验证切换行为；否则明确禁用尚未适配集合，不扩展为本批全部动画/绑定/FX算法实现。用户若要求本轮覆盖五集合，则必须扩大内容参考，不可称现有22树已覆盖。

Maya存在而Blender尚无等价项保留灰显与原因；Blender独有操作放在最接近用途的Maya菜单/子菜单中，保留真实Blender名称和语义说明。此为新授权的归类策略，不把Blender操作冒称为同名Maya等价实现，不恢复已被精确禁用的16个误绑定。

## 顶部固定来源与顺序

以下路径前缀均为 `C:/Program Files/Autodesk/Maya2026/scripts/`。

| 顶部顺序 | 菜单 | 直接源码/既有原始参考 |
|---|---|---|
| 1–7 | File → Edit → Create → Select → Modify → Display → Windows | `startup/initMainMenuBar.mel:374–393` 的 `commonMenuSet`，逐项数组在385–391；raw `groups.common`同序 |
| 8–16 | Mesh → Edit Mesh → Mesh Tools → Mesh Display → Curves → Surfaces → Deform → UV → Generate | 同文件400–423，逐项数组412–420；raw `groups.modeling`同序 |
| 17 | Cache | 同文件1177–1198，在菜单集之外创建 `mainPipelineCacheMenu`，内建Geometry Cache子菜单；raw `metadata.top_menus`确认visible |
| 18 | Help | `startup/HelpMenu.mel:44–50`，主窗口专用 `-helpMenu 1` / `MainHelpMenu`；`initMainMenuBar.mel:1200–1201`引入；raw确认尾部visible |

原始参考：`docs/reference/maya2026-menu-tree.json`。`metadata.top_menus`的visible项直接确认上述18项；不是根据菜单名猜测。Help标签尾空格为Maya平台绘制兼容细节（HelpMenu.mel:37–41），不是必须复制到AxisMeld可见标题的语义内容。

Cache并非Modeling专有，也不在commonMenuSet七项之内；它独立于集合数组。`others/insertPipelineSubMenu.mel:45–52,58–92,145–159`允许插件插入、重建或移除Cache子项，不能把特定插件贡献当成无条件固定菜单。当前raw只记录Cache顶部存在，**没有捕获其完整子树**；同样没有Help完整子树。不能以现有1949归一化节点声称这两根内容也已实机逐项核对。

## Menu Set 是菜单集合切换，不是视口或对象模式

`startup/initMainMenuBar.mel:58–63`默认集合排列：Common（内部永久集合）、Modeling、Rigging、Animation、FX、Rendering。`updateDropDownMenu2:107–130`枚举集合、排除Common、筛除无现有菜单集合；163–193处理当前选择及Customize。用户自定义集合可加入，不宜硬编码成对象模式/编辑模式。

`changeMenuMode`同文件234–243先隐藏旧集合并把Common移到最前，275–290始终显示Common，再把新集合顺序放到Common之后。故切换不替换File/Edit等全局菜单；也不等价于Blender切换工作区、对象模式或编辑器。

| 集合 | 默认专用菜单顺序 | 来源 |
|---|---|---|
| Modeling | Mesh, Edit Mesh, Mesh Tools, Mesh Display, Curves, Surfaces, Deform, UV, Generate | initMainMenuBar.mel:400–423 |
| Rigging | Skeleton, Skin, Deform, Constrain, Control | 429–443 |
| Animation | Key, Playback, Audio, Visualize, Deform, Constrain | 449–464 |
| FX | nParticles, Fluids, nCloth, nHair, nConstraint, nCache, Fields/Solvers, Effects | 470–495；受loadDynamics/loadNCloth条件影响 |
| Rendering | Lighting/Shading, Texturing, Render, Toon, Stereo | 502–517；受loadRendering条件影响 |

这些非Modeling集合在raw顶菜单metadata中存在但visible=False；原始参考没有导出其完整内容，不能把“标题已找到”当作“整套菜单已对齐”。

## Help 的真实内容边界

`startup/HelpMenu.mel:15–27`延迟构建并更新；不是复用File菜单或外链集合。`startup/doHelpMenuItems.mel`为主窗口与面板窗口分支分别定义内容：

- 35–54：主窗口Find分隔标题、SearchEngine、Help；OpenMenuFinder仅非主窗口分支。
- 57–76：What's New子菜单仅非主窗口分支，不能因注释/RTC存在而误加到顶部Help。
- 79–115：主窗口Learn分隔标题、QuickTour、Interactive Tutorials（基础、建模、动画、灯光/明暗、全部教程），OpenLearningChannel。
- 115–133：Advance分隔标题、Scripting Reference，包含MEL/Python/Node Attribute参考；Python分支受运行时能力条件约束。
- 135–183：Contribute分隔标题、Services and Support（账户、条件性本地patch notes、Release Notes、Support Center）。
- 185–228：Feedback（问题报告、功能建议、研究、分析设置）、分隔、Autodesk Exchange，以及Windows上的ProductInformation/About Maya。
- 237起有后续动态追加；完整静态标签通过Maya资源/RTC定义解析，不从英文代码注释伪造最终label。

AxisMeld可把真实Blender文档、报告问题、系统信息、About归入用途对应的Help区域；必须使用Blender/AxisMeld标签与目标链接，不能让“About Maya”打开Blender信息却不说明。Maya专用服务/教程可保留灰项，不擅自接外部账号或伪称功能等价。

## Current Pane 不属于顶部

raw `groups.current_pane`六根为 **View, Shading, Lighting, Show, Renderer, Panels**，所有path均以 `MainPane|viewPanes|modelPanel4|modelPanel4|...` 开头。它们是透视modelPanel局部菜单，和顶层 `mainDisplayMenu`、Rendering集合的Render/Lighting-Shading不是同一层。

顶部新UI不应改变这些局部菜单、热盒行、QWER/Shift+RMB方向或Views几何。可复用绑定与参考，但必须区分入口和source-context；顶部点击建模项需要明确选用哪个3D视图上下文，不能拿当前鼠标所在TOPBAR region执行3D算子。

## Blender独有能力归类建议与接入点

现有顶部入口在 `scripts/startup/bl_ui/space_topbar.py:106–125`，当前Blender图标、File、Edit、Render、Window、Help。建议逐项盘点原类，避免只替换标题后遗失能力：

| 原Blender能力 | Maya用途归属建议 | 语义界限 |
|---|---|---|
| 新建/打开/保存/恢复、导入导出、打包/外部数据、项目 | File对应区域/子菜单 | 保留Blender文件与数据命名；不得让Maya专用导入格式误启用 |
| Undo/Redo/历史、重命名、偏好 | Edit及Windows → Settings/Preferences适合位置 | 默认全局撤销语义不改；已拒绝的Maya层级改名不重新误绑定 |
| 新建对象、集合、资产实例 | Create对应对象/组织用途 | 不把Collection直接叫Maya Set而隐瞒语义差异 |
| 选择/模式、变换/应用、可见性 | Select / Modify / Display对应区域 | 以真实上下文poll控制，保留模式/对象域边界 |
| 窗口、工作区、编辑器、控制台、状态显示 | Windows对应用途子菜单 | 工作区不等同Menu Set |
| 网格/曲线/法线/UV/变形操作 | Modeling各相应菜单的明确Blender条目或小用途分组 | 使用原注册命令ID；同名不等价不合并 |
| 渲染执行、动画渲染、查看Render Result | Rendering集合Render用途；若本批仅Modeling需明确可达适配入口 | 不暗中丢弃Blender原Render能力；是否常驻由设计显式决定 |
| 文档、支持、版本、系统信息 | Help对应区域 | 明确Blender/AxisMeld来源 |

最小实施需要一个“用途归属表”，将旧顶部所有可执行项逐一映射到新入口或记录明确保留位置；原564命令ID可复用但不涵盖Blender所有TOPBAR操作。避免把旧564可达测试当作顶部能力无遗漏的唯一证明。

验收应分别检查：18根Modeling顶部顺序；Cache/Help来源与条件；Menu Set若实现则Common稳定与专用部分切换；Pane六菜单未混入；所有旧顶部操作可达；Maya灰占位和独立Options保留；建模动作源上下文/Undo；窄窗口菜单可访问，不挤压或伪造热盒几何。
