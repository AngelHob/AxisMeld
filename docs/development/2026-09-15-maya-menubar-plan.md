# Maya Menu Bar Implementation Plan

> **For agentic workers:** 使用 subagent-driven-development 的有界分工和独立审查。按下列步骤执行，源文件所有权明确，GUI一次只由一位作者操作。

**Goal:** 顶部菜单按Maya逻辑组织，灰色保留缺失项，并按用途收纳Blender独有能力。

**Architecture:** 独立Maya参考决定顶栏；纯目录复用既有受审绑定，原生UI draw保留动态入口和调用参数。顶栏只在AxisMeld配置启用，语义建模调用与原生全局入口分开处理上下文。

**Tech Stack:** Blender 5.3开发树、Python bpy/UILayout、既有AxisMeld适配器、本机Maya 2026只读UI捕获。

**Spec:** `2026-09-15-maya-menubar-design.md`

## Global Constraints

- 不把Current Pane六菜单加入全局顶栏；不执行捕获到的命令文本。
- 原native Import/Export/Recent/Undo菜单ID、保存参数、564语义命令可达性必须保留。
- 不自动改模式或选择目标；语义命令执行前重新验证区域、场景和poll。
- 不修改用户运行中的Maya/Blender、个人场景和已完成候选；验证用独立实例。

## Task 1：真实顶部参考（GUI作者）

Files：新 `docs/reference/maya2026-menubar-tree.json`、`tools/axismeld/build_menubar_reference.py`、`scripts/modules/axismeld/menubar_reference.py`、`tests/python/axismeld_menubar_reference_test.py`。

Interface：生成 `MENU_SETS`（五个稳定key到顶层参考节点ID序列）和 `REFERENCE_MENUS`（唯一节点树）。节点字段沿前批 reference，公共参考可标稳定引用；动态规范化另记明确清单。

- [x] 用独立Maya进程按真实menuMode切五集合，只执行菜单构建回调，记录最终可见顶部顺序、场景不变、error与插件状态。
- [x] 原始结果单独保存；核对Common7/Modeling9/Cache/Help，排除局部Pane与隐藏插件项。
- [x] 为顺序、缺根拒绝、Options相邻关系、动态历史归一化和原始命令惰性写失败测试。
- [x] 最小生成器转换，运行 `python tools/axismeld/build_menubar_reference.py --check` 和纯测试，输出不可变接口供目录作者使用。

## Task 2：固定原生入口（native作者）

Files：新 `scripts/modules/axismeld/menubar_native.py`、`tests/python/axismeld_menubar_native_test.py`。

Interface：`draw_native(layout, context, key, *, text, icon)`；`NATIVE_KEYS`为固定闭集。key清单与root目录作者同步，禁止任意operator字符串派发。

补充 `menubar_actions.py` 与独立纯测试：11类基础原生对象创建和10类编辑器窗口；相机/灯光等价RTC明确绑定，其他使用Blender准确名称按Create/Windows用途收纳。对象只允许Object模式、真实3D区域，编辑器仅修改本次唯一新建且独立的窗口。全部复用原生undo，不加父级undo或手动push。

- [x] 基于保留清单定义固定key，按File/Edit/Modify/Windows/Render/Help用途分组；为保存kwargs、动态菜单ID与条件分支建立录制UILayout测试。
- [x] 实现小draw函数，严格保留EXEC_AREA/INVOKE_AREA/INVOKE_SCREEN、copy/incremental/modified-images与RNA状态。
- [x] 复用原Import/Export/Recent/Undo History类；模板、项目、External Data等复用实际子菜单；不得复制附加组件列表。
- [x] 运行纯录制测试和隔离Blender入口核验，交回固定keys及每项预期语义。

## Task 3：目录与顶栏呈现（root）

Files：新 `scripts/modules/axismeld/menubar_catalog.py`、`menubar_runtime.py`、`scripts/startup/bl_ui/space_axismeld_menubar.py`；修改 `space_topbar.py`、`bl_ui/__init__.py`；测试 `tests/python/axismeld_menubar_catalog_test.py`。

Interface：`build_menubar()`返回 `{'sets': MENU_SETS, 'menus': tuple(nodes)}`；每个node有稳定id/kind/label/children，command仅既有语义ID，native_key仅Task2闭集。`enabled(context)`控制AxisMeld配置；`draw_bar(layout, context)`绘制集合选择及实际顶层。

- [x] 先写目录测试：真实Maya子序列不丢失；Blender额外能力按category/section落到具体用途；564语义IDs可达；无pane六根或巨大平铺扩展根。
- [x] 复用Common/Modeling受审绑定；新参考默认灰显，只有核实等价的native key可启用，Options不可复用正文。
- [x] 建立动态Menu类和菜单集枚举，会话状态SKIP_SAVE；原native TOPBAR类保持注册。
- [x] 语义命令在可见3D来源下重验adapter，捕获身份失效取消；全局native入口保持原context。
- [x] 当前层按可用高度分列，保持原顺序和完整条目；使用原生图标和灰状态，不人为分页。
- [x] 更新顶部draw条件与模块注册，运行目录/上下文测试及已有相关纯回归。

## Task 4：验收与交付（独立GUI作者，root汇总）

Files：新 `tests/python/axismeld_menubar_events.py`、对应后台集成测试；更新统一manual-test-ledger，候选验收记录。

- [x] 验证真实顶部五集合、关键子树、无3D灰显、正常/2x菜单完整及原生配置回退。
- [x] 通过顶部真实入口验证Cube/Camera/Point Light创建与各一次Undo、独立Outliner窗口和Save Scene As临时文件保存；纯测试核对Copy/Increment参数、动态格式菜单ID、Preferences及条件状态。
- [ ] 人工补测Copy/Increment、实际导入导出格式、Preferences及个人场景操作手感；合并在MB-01–MB-20中，不由自动验证改成已测试。
- [x] 新独立安装，比较源脚本资源与保护文件哈希；按改动运行相关回归，保存完整成功/失败日志。
- [x] 追加人工测试至总台账与私人网页，保留用户历史标记；输出正常主题Menu Bar与关键菜单截图、启动入口和验收说明。
- [x] 最终审查用途归类与全入口保留，diff-check后本地提交并生成干净源码核验回执。
