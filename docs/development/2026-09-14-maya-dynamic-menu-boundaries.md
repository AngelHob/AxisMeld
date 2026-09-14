# Maya 2026 动态菜单边界（2026-09-14）

本说明约束 `docs/reference/maya2026-menu-tree.json` 的消费方式。该文件是独立 Maya GUI 的一次真实菜单快照，不是可跨场景直接复制的常量目录。Common 7、Current Pane 6、Modeling 9 根均已捕获；叶命令从未执行。命令字符串只作来源证据，禁止交给 Blender 执行。

## 捕获与修正

- 程序：`C:/Program Files/Autodesk/Maya2026/bin/maya.exe`；独立 `MAYA_APP_DIR=D:/source/AxisMeld-build/maya-menu-audit-20260914/isolated-profile`。用户 Maya PID 41244 未操作。
- 上下文：英文默认空场景、无选择、modelPanel4/persp；实际插件列表在 JSON metadata。启动禁自动加载不能解释为“没有任何插件”：基础初始化仍加载 modelingToolkit/renderSetup 等。
- 查询必须使用完整 UI 路径。初版 `menuArray` 返回的短名 View/Panels 歧义命中 modelPanel1；已修正为 modelPanel4 下的完整路径，六根现在属于同一原区。数字 menuItem 名与实例 UI 路径不应成为跨启动稳定业务 ID。
- `divider=true` 的 `dividerLabel` 是不可点击分组标题，不得变成子菜单。Options 独立条目没有正常可见文字，其自动生成 label 不是功能名。

## Bookmarks 的未解决原生命令错误

先前报告把错误笼统称为 View→Bookmarks，不准确。成功的相机分支是 **Current Pane → View → Bookmarks**。失败的是 **Current Pane → Show → Isolate Select → Bookmarks**。

本机 `scripts/others/createModelPanelMenu.mel:426–439` 明确先建立 Bookmarks 子目录、`Bookmark Current Objects` 主项和相邻 Options，再以 postMenuCommand 调用 `buildBookmarkMenu -type bookmarkModelView -editor modelPanel4 <完整菜单路径>`。`whatIs buildBookmarkMenu` 的实机结果是 `Command`，不是 MEL procedure；安装中没有可读的 buildBookmarkMenu.mel。`cmds.help` 验证它只有 editor/type 两参数。

完整路径菜单与 editor 均实测存在。原 MEL 调用、Python 命令、长/短路径、空场景以及独立实例中临时创建又删除的 bookmarkModelView set 都返回原生命令错误，没有补足动态枚举。故保留 JSON errors，不能将其宣称已修复，也不能把当前两个固定槽宣称为全部可能内容。固定主项与 Options 由实机和上述 MEL 双重证实，应保留；动态书签枚举标记为未验证，不造条目。

诊断：`D:/source/AxisMeld-build/maya-menu-audit-20260914/bookmark-probe.json`、`command-diagnostics.json`、`export.py`。临时夹具已删除，未执行任何菜单叶命令。

## 精确分支处理建议

以下路径使用显示标签链，避免依赖本次启动的 menuItem 数字 ID。分支内部仍应保留 Maya 原本顺序和固定操作；动态成员不从快照固化。

| 路径 | 固定结构 | 动态内容与处理 |
|---|---|---|
| Common → File → Recent Files / Recent Increments / Recent Projects | 三个目录入口 | 文件、增量、项目来自用户记录与当前文件。当前空字符串文件条目不是功能；不移植个人路径或伪造空条目。来源 `startup/FileMenu.mel:87,224`。 |
| Common → Edit → Recent Commands List | 入口 | 命令历史属于当前会话，不能当固定子功能。 |
| Common → Edit → Delete by Type → Sounds | Sounds 目录 | `No sounds available` 是空状态。`others/updateSoundMenu.mel:62–82` 枚举 audio 节点；有声音时应显示实时节点，不永久保留空提示。 |
| Common → Select → Quick Select Sets | 目录 | `No Quick Select Sets Defined` 是空状态；内容来自场景集合。`startup/buildEditMenu.mel:50`。 |
| Common → Modify → Asset → Advanced Assets → Set Current Asset | 目录与 None/ClearCurrentContainer 操作 | 资产成员来自场景，None 是清除当前资产的真实操作，不可与纯空提示混删。 |
| Common → Windows → Workspaces | 目录、分组机制、Reset/Save/Import/Delete/Disable Docking 操作 | factory/user/module 三类工作区源分别处理。`General*` 中 `*` 是当前状态；Reset 文案内 General 也是上下文插值。不得把 General* 或 Bifrost Fluids 模块贡献当所有机器恒定项。factory 基线有本机源码列表，可另作版本基线；用户/模块项运行时生成。来源 `startup/buildViewMenu.mel:29,77–159,192`。 |
| Current Pane → View → Bookmarks | Edit Bookmarks... 操作、书签容器 | 相机 `.bookmarks` 连接生成成员；本次仅空分隔与 Edit 操作不能定义非空场景。`others/buildCameraBookmarkMenu.mel:89–126`。 |
| Current Pane → View → Predefined Bookmarks | 本版预定义视图动作 | 与上述命名书签不同；不因含 Bookmarks 一词就全部删除。 |
| Current Pane → View → Image Plane | Import Image... / Import Movie... / Image Plane Attributes | Attributes 子成员来自原区相机图像平面；空目录不意味着缺固定功能。导入命令里的 perspShape 必须替换为实时原区相机绑定。`others/buildImagePlaneMenu.mel:31–48,63–90,111–144`。 |
| Current Pane → Show → Isolate Select → Bookmarks | Bookmark Current Objects + Options | 原生动态构建错误尚未解决，保留缺口标记；不能宣称固定两槽为完整所有书签。 |
| Current Pane → Panels → Perspective | New 动作及目录 | persp 是场景相机实例名；`others/buildPerspLookthruMenu.mel:29–58` 使用 listCameras。运行时枚举当前场景，不冻结 persp。 |
| Current Pane → Panels → Orthographic | New 子目录与其固定方向创建项 | front/side/top 是场景相机名而非这个目录的永久动作。来源 `others/buildOrthoLookthruMenu.mel:26`。不要与 View→Predefined Bookmarks 的固定方向混淆。 |
| Current Pane → Panels → Stereo | 创建相机/层等固定操作 | rigs、相机集以及插件类型依赖安装和场景；空分隔不要生成伪功能。 |
| Current Pane → Panels → Layouts | Single/Two/Three/Four Panes 与 Previous/Next Arrangement | 这是原生固定布局操作，可以作为版本基线；不是 Saved Layouts 的用户配置列表。 |
| Current Pane → Panels → Saved Layouts | Edit Layouts... 操作及目录 | `getPanel -allConfigs` 枚举已注册配置，factory 默认名也是可变配置实例。不要固化本次19个名称。来源 `others/buildPanelPopupMenu.mel:203–226`。 |
| Current Pane → Panels → Panel / Hypergraph Panel | 类型入口/容器 | 已注册 panel 类型、已有面板实例与插件贡献动态；命令中的 modelPanel4、graphEditor1 等只是本次实例引用。来源 `others/buildPanelPopupMenu.mel:34`。 |
| Current Pane → Renderer | 渲染器入口与配置方式 | 当前仅 Viewport 2.0 并不证明所有插件环境只有一个渲染器；本次 enabled/radio 是状态快照。 |
| Modeling → Mesh Display → Assign Existing Set | 目录 | `No bakesets defined` 为空状态，真实 bake set 名属于场景。来源 `startup/PolygonsColorMenu.mel:100`。 |
| Common → Create → Lights / Cameras / Scene Assembly；插件或模块贡献项 | 已有原生固定入口保留 | factory 创建类型与插件注册类型分别处理。Scene Assembly 当前空树不能当“永久无内容”；必须标注册能力条件。 |

## 跨所有22根的统一规则

1. `checkBox/radioButton/enable` 是本次上下文状态；结构可复用，值必须由 AxisMeld 当前原区、选择与能力计算。尤其显示模式、相机锁定、选择与当前workspace不可冻结。
2. 固定命令的参数也可能动态：相机名、modelPanel 编号、UI路径、节点名。菜单label固定不代表绑定字符串可照搬。
3. 插件命令缺失时保留用户要求的已确认目录占位并明确不可用原因；不将未加载状态误判为 Maya 没有该功能。不得为了填空自动执行插件功能叶命令。
4. 参考 JSON 保留原始快照供审计；实现应以固定骨架 + 明确的动态成员提供器消费。没有提供器时显示清晰不可用状态，不把 No sounds / persp / General* / No bakesets 等样本作为永久功能。
5. 空容器、空状态提示、真实的 None 操作、固定方向动作属于不同语义，不能使用“删除所有空/禁用项”之类统一过滤。
