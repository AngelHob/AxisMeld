# M2d Object Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 接通已选 Object 与鼠标预选的三个持久建模工具入口，开盒只读、提交有撤销、失败可回滚。

**Architecture:** Python 固定命令与专用 UNDO 操作器负责 Object→Edit 工具事务。C++ 负责真实 GPU 候选、身份固定、互斥路由与直接热盒 ownership。现有 CREATE/MODEL 配置 ID 保持。

**Tech Stack:** Blender C++、Python bpy/BMesh、CMake/CTest、隔离 GUI event_simulate。

**Spec:** `docs/superpowers/specs/2026-09-14-m2d-object-tools-design.md`

## Global Constraints

- 阅读 AGENTS.md 与 `docs/development/2026-09-14-hotbox-reference-contract.md`，四视图不缩小，设置继续原生普通菜单。
- 本片固定三个工具；其他方向使用诚实 disabled 原因。Global 物体缩放无开发计划。
- 选择优先；无选择才允许鼠标 GPU 候选；已有任何不合格选择不偷偷过滤。
- 开盒与取消不修改场景。提交只在专用事务操作器内改变选择/模式，失败完全回滚；一 Undo 恢复启动前模式/选择。
- 人工测试继续搁置，统一追加清单，47 条旧用户反馈保留。只本地实现，不自动 push。

## Task 1: Object 根、入口与工具事务

**Files:**
- Create: `scripts/modules/axismeld/object_modeling_hotbox.py`（纯常量/菜单/只读资格），`scripts/modules/axismeld/object_modeling_ops.py`（bpy 操作器与回滚）。
- Modify: `context_modeling_hotbox.py`、`commands.py`、`adapter.py`、`keymap.py`、`profiles.py`、`hotbox_runtime.py`、`hotbox_catalog.py`（均位于 scripts/modules/axismeld），`scripts/startup/bl_operators/axismeld.py`。
- Modify: `source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc` 与需要的 internal/release bridge，`source/blender/axismeld/AXM_context_modeling.hh` 及现有 catalog fixture test/CMake dependency。
- Test: `tests/python/axismeld_object_modeling_hotbox_test.py`，更新既有 Edit-only 断言使其明确 Object 新路由；现有三 Edit 根契约保持。

**Interfaces:**
- `OBJECT_ROOT = 'context.modeling_object'`；`OBJECT_TOOLS` 固定 semantic ID → builtin tool ID 映射，三个值严格按 spec。
- `object_modeling_menu(node)` 返回一个 radial node。`object_modeling_targets(context, target_uid='')` 只读返回严格目标 tuple，无法适用返回空 tuple；不要更改 active/selection/mode。模块可在无 bpy 的纯测试导入。
- `AXISMELD_OT_object_modeling_tool` 属性 `command: StringProperty`、`target_uid: StringProperty`，ID 前缀 `tool.object_mesh_`。native 只调用该操作器，target_uid 保存 unsigned session uid 十进制文本，已有选择传空字符串。
- MODEL 在 Object 选择 `OBJECT_ROOT`（空选择鼠标直入 native 判定），Edit 继续 `modeling_root(context)`；CREATE 不改写为综合命令。
- 固定 native Object allowlist 与 Python fixture 双向比较；Object 不参与 V/E/F domain index 运算。

- [x] 添加 RED 单测：固定 Object 八向中 E/W/SW 命令、其余 disabled 无 command；MODEL 生成 Object + Mesh，CREATE 仍仅 Object；严格 mixed/hidden/active/target 选择资格与只读输入。
- [x] 跑 `python -m unittest discover -s tests/python -p axismeld_object_modeling_hotbox_test.py`，记录行为缺失而非语法错误。
- [x] 实现上述 Python 接口与 bpy 事务；子 `mode_set`、`tool_set_by_id` 都传 False undo；失败恢复前置状态；拒绝未注册 command/失效 UID/已有选择加预选。
- [x] 实现 native Object direct session、只读 GPU picking、全选择及 data UID/active signature、每次 modal/提交校验与 cleanup-before-dispatch；保持 Object session 返回专用 dispatch 实际结果。
- [x] 更新固定 fixture 与受影响已有单测；运行 Python 全套和 native tests；提交前由 root 统一 GUI 验证与独立 review。此任务不要启动 GUI、安装或提交。

## Task 2: 实际 GUI、独立复核与交付

**Files:** `tests/python/axismeld_object_modeling_events.py`、`tests/python/axismeld_hotbox_ui_runner.py`（若需 suite 注册）、`docs/compatibility/2026-09-14-manual-test-ledger.md`、`docs/compatibility/2026-09-14-object-tools-acceptance.md`、`docs/maya-mapping/2026-09-14-object-modeling-hotbox.md`。

**Interfaces:** GUI 仅用生产输入事件打开菜单；测试端用 `bpy.context.window.modal_operators`、对象/组件状态、工具 id 与 Undo 结果作为独立观察。runner 复用隔离 config 与工厂场景，不能写用户偏好。

- [x] 在旧候选运行测试首个断言：选中 Mesh Object + Shift+RMB 必须打开一个 VIEW3D_OT_axismeld_hotbox；确认旧版 RED。
- [x] 用函数式 fixture 记录 mode、active、所有对象选择、mesh 坐标/拓扑/组件 select/hide、tool id；校验开盒/取消与失效相等。
- [x] 三个方向启动并独立操作原生后续笔划；验证一次 Undo 恢复模式/选择，确认用户还可普通选择/QWER。测试无选择预选、前景 Curve 遮挡、空白创建、多对象及共享 Mesh data、失败回滚与 profile 所有组合。
- [x] 对照同实例 Views 的行 2/4、3 间隔，至少单/四视图；跑现有 Edit/create/tool/component 与相关 native suite。
- [x] 独立 reviewer 阅读 spec 与全部 diff，修复有证据的问题再做针对性复验。
- [x] 追加人工清单与真实差异、同步 outputs，记录构建/资源/config SHA256 和实际测试标志，本地提交最终实现。
