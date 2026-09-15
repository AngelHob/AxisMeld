# Maya 逻辑的顶部 Menu Bar

## 用户目标与范围

2026-09-15：用户明确要求整理窗口顶部 Menu Bar。Maya 有而 Blender 尚无等价适配的功能保持原位、灰色占位；Blender 独有功能按 Maya 的用途收纳到相应菜单。此要求更新前批仅在内部 Blender Extensions 中提供额外能力的决定。本批落实顶部菜单，不将 Current Pane 六菜单误当全局主菜单。

源码基线为 `bff4cd9448aeec0af09741baef6b9be3a4176397`。原顶部为 Blender 图标、File/Edit/Render/Window/Help；与前批热盒展示树不是同一 UI。基础证据见同目录 `2026-09-15-maya-menubar-reference-audit.md`、`2026-09-15-blender-menubar-inventory.md`。

## 产品结构

1. AxisMeld Maya 配置启用时，顶部使用真实 Maya 公共菜单和五个标准菜单集 Modeling/Rigging/Animation/FX/Rendering，再按实际顺序显示 Cache/Help 等永久入口。菜单集只切换专用菜单，不替换 Blender workspace、不切换对象模式；工作区标签及 Back to Previous 保留。
2. 顶部顺序及 Maya 子树取自独立隔离 Maya 2026 的实际 UI。既有22根含6个视口局部菜单；不能直接复制为顶栏。补采四个菜单集、Cache、Help，原始证据另存，不覆盖前批快照。归一化仅处理明确列出的动态实例、历史名称和独立 Options，不能按“未实现”删行。
3. 复用公共/建模树的既有受审语义绑定，正文与独立 Options 分开。未经证明等价的 Maya 功能保持灰显并说明原因，不因相似名称调用另一个写操作。Blender 专有功能保留准确原名，插入对应真实用途目录；需要新增用途子目录时明确属于 Blender 适配，不伪称 Maya 原项。
4. File 收纳真实文件、引用/追加、项目、导入导出、恢复、外部数据、预览与清理；Edit 收纳真实撤销/重复历史和搜索；Modify 收纳 Blender 命名；Windows 收纳编辑器、偏好/启动配置、工作区与窗口控制；Rendering 的 Render 菜单保留原渲染/序列/音频能力，Windows 提供可发现的渲染入口；Help 保留真实 Blender 帮助、About 和诊断。
5. 既有564个语义命令全部保持可达。未被 Maya 正文采用的能力按其 category/section 插入对应用途菜单，保留层次和语义差异，不形成新的平铺大目录。新顶栏不会把全局文件/窗口操作加入热盒 JSON 执行白名单。

## 实现边界

- `menubar_reference.py`：由独立捕获转换出的顶部集合与专用子树；生成器和纯测试不依赖 bpy，不执行任何捕获到的 MEL/Python 文本。
- `menubar_catalog.py`：纯 Python 顶部树，复用受审 Maya 参考绑定，声明固定原生 UI 入口及用途归类。节点使用 menu/command/native/disabled/separator，原生入口仅接受源码固定 key；Options 独立表达。
- `menubar_native.py`：可信原生 UI draw 小函数，保留 Save/Copy/Increment 的 EXEC/INVOKE 和参数、原 Import/Export/Recent/Undo 菜单 ID、条件项及 RNA 状态。该模块不统一覆写为 VIEW_3D，不从配置读取 operator/RNA 路径。
- `menubar_actions.py`：补齐顶部 Create 所需的原生相机、四类灯光及 Armature、Metaball、Volume、Grease Pencil、Speaker、Force 对象；只在真实 Object 来源可用。Windows 的 Blender 编辑器创建独立窗口，必须证明新窗口唯一、独立屏幕且只有一个区域才改变其编辑器类型；失败只关闭本次唯一新建窗口。已有564命令没有这些基础入口，新增适配不扩展到完整 Maya Rigging/FX 算法。
- `menubar_runtime.py` 与 `bl_ui/space_axismeld_menubar.py`：动态菜单类、灰显/图标/状态绘制、菜单集选择及受审语义命令调用。仅语义建模动作解析当前窗口的可见3D来源，原生全局菜单保持当前上下文；窗口/区域/场景失效时取消，不切换模式或选择目标以通过 poll。没有3D区域时建模项灰显。
- `space_topbar.py` 和 `bl_ui/__init__.py`：最小接入和注册。切换到非 AxisMeld keyconfig 时使用原 Blender 菜单。保留原 TOPBAR 菜单类供插件、搜索、右键和其它调用方使用。

菜单当前层完整绘制；保留真正子目录，无人为分页/Back 层。较高固定列表在窗口范围内按原顺序分列；显示/操作使用 Blender 原生 UI。不能通过减少行、缩字、删除禁用项或轮滚搜索来满足验证。

无原生入口的列用实际 BLF 字体测量标签，并保留图标、状态和 Options 空间。含原生入口的列使用 Blender 自身测宽，保留原生快捷键列，不能用仅包含标签的估宽覆盖它。顶栏分类保留完整文字；功能与子菜单使用统一 Blender 图标。

实机发现原生 `interface.cc:block_bounds_calc_text` 对横向按钮组同时存在迭代和列坐标问题：后缀递减跳过下一行正文、末尾可能产生空指针，多列归一化还会改变组内相对位置。本批改为先按原坐标收集完整行组与列，再统一归一化列位置；Options 行整体平移并保留组内宽度与纵向位置，普通行填满列宽，最小宽度只作用于最后一列。独立数值回归使用实际 C++ 函数体，另以真实菜单验证字体与点击区域。

File 的原生正文还有一处不同原因：隔离调用上下文的内部 `row()` 默认不继承外部对齐组，导致正文与 Options 被分开识别。内部单行改为 `row(align=True)`，仍隔离 enabled 和 operator_context；原生 Render 多行内容继续用 column。不能以补空白或缩字掩盖这些错误。

## 上下文与兼容

顶栏本身不是3D区域。建模命令在直接3D来源有效时使用该来源，否则使用同一窗口可见主3D区域；选择目标前不修改场景或选区。菜单绘制捕获的区域/窗口/场景身份在执行前重新确认，既有 adapter 再检查 mode、selection、poll。原生 File/Render/Preferences 等入口继续使用其原上下文，特别保留 Sequencer 渲染分支。

导入导出复用原菜单 ID 以保留附加组件 append 的格式；Recent 和 Undo History 读取当前运行数据。普通保存、未保存另存、Save Copy、Increment、启动配置、工厂设置不能合并为一个语义。菜单集选择仅为会话 UI 状态，不覆盖场景或个人配置文件。

## 验收

- 独立实际参考核对五套顶部顺序、层级、标签、分隔、Options 和灰占位；明确动态与插件边界。
- 纯测试核对原顶部全能力保留、564语义ID可达、每个补充入口有唯一用途归属、未授权/歧义 RTC 不可调用、原生 key 闭集与 no eval。
- Blender 实例验证顶部绘制/菜单集切换/非AxisMeld回退、公共树与关键建模动作、无3D场景灰显、多区域和失效来源取消；保留单次 Undo。
- 原生入口核对真实 Import/Export 扩展、Recent/Undo、Save/Copy/Increment 对临时文件的行为、Preferences、状态项和必要上下文。测试只使用独立配置、临时目录与自建实例。
- 独立候选安装、原候选保护、脚本资源指纹、正常主题截图；新的人工条目加入统一台账和私人测试网页，自动测试不改用户手工结果。
