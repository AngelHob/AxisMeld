# Menu Bar 对齐纠偏

## 触发与证据

用户在运行 `maya-menubar-test-install` 后指出菜单仍未对齐 Maya。当前源码基线为 `948aaf000e507efe0473650ac481afcffb3707c2`；本机进程路径已核实为该候选，不归因于旧版本。

第一轮结构检查沿用既有归一化结果，未发现留下的 Maya 行在父级、标签、顺序及 Options 上的差异；这不能证明归一化未删错内容，也不能证明混合菜单对齐。进一步直接核对本机 Maya 2026 的 `buildViewMenu.mel` 和工作区预设，确认旧归一化误删了 14 个 Factory 工作区及模块提供的 Bifrost Fluids。另有 `menubar_catalog._section()` 的缺省追加使 Select 扩展归入 USD、Modify 变换归入 Assets、Edit Mesh 面/组件操作归入 Curve、Mesh Display 法线归入 Display Attributes、Deform 扩展归入 legacy。

另外，Modify → Naming Tools 重复显示两组同名重命名操作。Maya Point to Point 将整对象按两点位移，而当前绑定的 Blender Selection to Active 在编辑模式修改选中几何点；两者不能使用同一 Maya 标签。Maya Duplicate Special 使用保留的复制/实例与变换设置，当前绑定的 Duplicate Linked 却固定链接复制，也不等价。

## 修复约束

1. 保留 Maya 原行和真实层级。新增目录按明确的 Maya 章节或具体操作邻接放置；无章节规则时不静默追加到最后一节。
2. 带名分隔代表章节，章节中的无名分隔代表小组。章节末定位不能误以第一条无名分隔为章节末；开场无名段和具体 leaf 邻接分别明确表达。
3. 混合变形目录按创建、编辑和权重用途拆分。没有单一 Maya 对应章节的 Mesh 修饰器使用明确的 Blender Modifiers 小节，不借用 Optimize 或其它无关标题。
4. 重命名使用一个原生入口，同时保留原语义 ID 的可达记录，消除同名等价重复。Point to Point 和 Duplicate Special 的 Maya 正文与 Options 均保留灰项；Selection to Active、Duplicate Linked 保留准确 Blender 名称与独立入口。
5. 此批只处理已证实的菜单内容与归属问题，不改热盒方向/几何。用户的具体菜单例子仍在等待补充，后续按其反馈继续核实。
6. 顶部 Windows → Workspaces 恢复 15 个预设及其 Options；删除 General 的捕获状态星号，不伪造 Blender 工作区映射。Blender Next/Previous Workspace 位于独立 Blender Workspaces 章节。此次修正顶部菜单的归一化，原始捕获及旧热盒参考生成器保持不变。

## 验证与交付

- 用独立预期的章节归属及相邻 Maya 行写失败测试；覆盖所有顶层扩展、最末无关章节、重命名去重及 Point to Point 灰显。保留原树不丢行与固定入口闭集检查。
- 新候选目录独立安装，保护用户正在运行的候选及旧配置。只使用隔离实例验证修改后的实际 Select/Modify/Edit Mesh/Mesh Display/Deform 菜单与关键灰行。
- 新人工测试记录追加到统一台账；自动验证不更改用户人工结果。完成后核对源码、程序及脚本资源，再交付启动入口。

## 完成证据

- Python 30 套、259 项通过。新增章节归属、15 个固定工作区、两个错误语义绑定的失败测试先失败，再修复通过；记录位于 `D:/source/AxisMeld-build/menubar-alignment-python-suite.json`。
- 独立 GUI `menubar-alignment` 通过：10 个根菜单实际章节顺序、File/Polygon Primitives 邻接、重命名唯一入口、Object/Edit 模式灰项点击不改变对象或几何、15 个工作区占位及真实 Next/Previous 往返。53 张原始截图与通过日志见 `D:/source/AxisMeld-build/menubar-alignment-gui-final.json`。前两次失败来自观察器对多栏顺序及重叠子菜单背景的假设，失败证据保留，没有据此放宽产品行为要求。
- 新候选 `D:/source/AxisMeld-build/maya-menubar-alignment-test-install`，使用既有已构建原生程序及此次更新的 Python 资源；安装 38 个资源匹配源码，GUI 覆盖其中 36 个。用户正在运行的旧候选 38 个资源及程序均未改动。
- 原热盒树的变化仅限两处错误 Maya 绑定灰显及相应 Blender 独立入口恢复；17 处树字段差异均有旧提交隔离生成的对照，见 `menubar-alignment-hotbox-tree-diff.json`。不把合法变化通过直接刷新快照掩盖。
- 人工台账追加 MB-21–MB-27，新增 7 项全部待测，原 273 项记录完整保留。自动通过不代替人工测试；本批也不声称所有 Maya 算法已实现。
