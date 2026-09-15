# Maya 建模菜单融入 Blender 视窗

> 本文记录上一版13根与完整Maya导航方案。本轮用户已进一步限定建模范围、取消Deform/Generate并要求原生功能直接归类；当前结构与验收见 [建模菜单归类与参数列对齐](2026-09-15-modeling-menu-integration.md)。历史计数与测试不作为新版的完成结论。

## 用户确认的结构

本设计替代此前双排全局 TOPBAR 方案。用户明确保留 Blender 原全局菜单（File、Edit、Render、Window、Help）和工作区标签，并确认 Maya 建模菜单放入 3D 视窗现有 View、Select、Add、Object/Mesh 所在的一排。

1. 恢复 Blender 原全局栏与原 Menu ID 调用，不重画原生菜单内容。Maya 公共菜单作为对应宿主的补充目录；原生插件回调、工作区标签、Scene/View Layer 保留。
2. Modeling 工作区内的 3D 视窗显示建模菜单。原生 View/Select/Add/Object、模式专用菜单及资产入口保留；Mesh、Vertex、Edge、Face、UV 复用同名宿主，原生工具以同用途子菜单保留，不并列重复同名根。
3. Edit Mesh 按 Maya 实际 Components、Vertex、Edge、Face、Curve 五组拆分，不猜测叶子功能所属组件。Components 保留共享组件操作；Curve 的投射和切割操作保留明确独立组。其他八个 Modeling 根及 Options 原样保留。
4. Maya 公共 File/Edit/Windows/Help 分别进入 Blender File/Edit/Window/Help 的补充目录；Create/Select/Modify/Display 在视窗 Add/Select/Object/View 中提供补充入口。Window 的 Maya Menu Sets 导航保留其他四套菜单集及公共目录的可发现入口，避免离开 Modeling 后失去功能。
5. 原始 Maya 参考与 `build_menubar()` 保持不变。新增纯投影仅改变容器和入口；当前 1829 个 Maya 功能行、639 个 Options 必须从实际宿主入口可达。Modeling 九根的445功能及237 Options逐项核对，原34个 Edit Mesh 的 Blender 扩展同样保留。

## 实施边界

- 当前仅调整 Modeling 工作区的3D视窗；其他工作区继续使用原生视窗菜单。Maya Menu Sets 导航确保其余功能仍可访问，不为此次布局创建或修改用户工作区。
- 自动识别工作区名 `Modeling` 或 `Modeling.*`；自定义改名后仍可经 Window → Maya Menu Sets 访问。Edit Mesh 原 Curve 组在视窗栏标为 `Mesh Projection`，与原生曲线编辑的 Curve 菜单区分。
- 配置仍以已启用 AxisMeld Maya 键位为界。未选对象、Object及Edit模式下保留建模菜单，按实际上下文灰显，不自动改模式或选区。
- 原热盒目录、方向、几何、按钮参数与绑定均不改。旧双排候选和测试证据作为历史保留，其验收条目由本轮新条目接续。
- 自动覆盖检查从UI宿主的根集合遍历，包括所有Options，不以全局ID缓存存在代替真实可达。菜单叶子的命令、参数、原因、状态和来源保持不变。

## 验证计划

纯测试核对五组序列、完整payload、全部Maya源ID的去向，以及原目录未被修改。隔离实例验证原全局菜单与插件扩展、Modeling的Object/Edit/无选择菜单、点线面灰项、真实建模与撤销、非Modeling工作区原生菜单及其他集合入口。新候选独立交付，人工清单追加至私人网页。

## 交付与验证

- 新候选：`D:/source/AxisMeld-build/modeling-viewport-test-install/blender.exe`。本批为 Python 资源修改，复用已核验的单排原生程序（SHA-256 `0dc5122a114cfb32b65b8720878451fb18e1d0ba44481abf560662620b268724`），独立安装内40个资源与当前源码逐项匹配。前一单排候选保持不变，未使用历史双排程序。
- 92项针对性自动测试通过：既有 Menu Bar 的动作、目录、原生菜单、运行时、参考和UI测试79项，投影9项、原生顶栏保护4项。投影从独立源清单核对1829个正文与639个Options，原始命令和参数未变。
- 真正注册的5套导航Menu.draw在只读审查中覆盖47个唯一根，无未注册菜单目标。Modeling的13个根保留445正文与237 Options，拆分组保留29正文、18 Options和34个Blender扩展功能。
- 隔离 GUI 在1920×1017、UI scale 1.0通过：原生全局栏、Layout往返、Modeling的Object/Edit/无选择、13根完整可见、菜单去重、灰选项不执行、细分8→26顶点后一次Undo完整还原；实际 File/Import/Vertex 插件追加入口、File/Import移除后的菜单、其他四套菜单导航也通过。详见 `D:/source/AxisMeld-build/modeling-viewport-gui-final.json`。
- 新GUI首轮观察器未识别原生 View 字体，截图确认文字存在；按同一完整字形适配主题前景阈值后通过，未改产品逻辑迎合观察器。窄窗口/高DPI、曲线模式及真实第三方插件组合仍属于人工检查，未借用历史双排的测试结论。
- [逐项去向数据](../compatibility/maya2026-workspace-menu-routes.json)由 `tools/utils/axismeld_workspace_menu_routes.py` 生成，包含源ID、原路径、实际入口、备用导航、绑定或灰占位状态。`--check` 验证生成数据未过时；`--html PATH`导出可搜索的本地浏览页。300条正文具备现有绑定，是否可执行由上下文决定；其余正文及639个Options为灰占位，不宣称已实现Maya全部算法。
- 私人测试网页新增MB-30–34五项；原282条编号和初始人工状态保留，不写入或重置服务端测试结果。MB-28/29标注为已替代的历史方案。当前目录287项，47项历史已测，240项初始未测（含2项不再用于当前验收的历史方案）。
- 去向表的独立浏览器检查通过10项：搜索、组合筛选、分页、全量JSON下载、390px页面及无网络/无JS错误。确认1829正文及639 Options均可检索。
- 新启动入口使用独立默认场景，禁用偏好保存，启用Maya键位并切换到Modeling。工作区赋值通过通知异步生效，成功检查在通知处理后执行；后台仅确认配置，不能当成GUI成功。独立GUI启动证据为 `D:/source/AxisMeld-build/modeling-viewport-launch-green/launch-verification.json`。
