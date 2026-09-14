# M2d 已选组件建模热盒实施计划

> **For agentic workers:** Use superpowers:subagent-driven-development to execute this bounded slice and review it independently.

**Goal:** Shift+RMB 在已有单域组件选择时打开对应建模热盒，并复用 M3 已实现能力。

**Architecture:** 独立 context semantic 入口仅绑定 Mesh，旧空白创建仅绑定 Object Mode。Python 解析显式选择域与能力；C++ direct context 会话统一拥有鼠标与修饰键，根环和命令来源固定白名单。

**Tech Stack:** Python 命令/菜单/配置、Blender C++ modal、CTest 与隔离 GUI。

**Spec:** ../specs/2026-09-14-m2d-edit-context-design.md

## Global Constraints

- 可见区域 C++ 实现通过独立审查并冻结后，再修改共用 session 文件；前片 GUI 使用已构建且哈希固定的二进制完成补充验收，两片 GUI 串行执行。
- 保持四视图净距、真实起点、取消与外延命中一致；不缩目标以迁就测试。
- 已有 M3 几何与 Ctrl+E/Ctrl+B 不重新实现；缺口保留具体计划。
- 不通过简单放开所有同键冲突来绑定新入口；只允许实际上下文互斥的创建/组件建模入口。
- 人工暂缓，旧 47 项已测试记录保留，新增内容统一记待测。

## Task 1: 单域 Edit 上下文菜单与输入

**Files:**
- Create scripts/modules/axismeld/context_modeling_hotbox.py: 三根与子菜单，以及不变选区的根选择。
- Modify commands.py, adapter.py, hotbox_catalog.py, hotbox_runtime.py, keymap.py, profiles.py and scripts/startup/bl_operators/axismeld.py: 注册、独立输入范围、能力、直接会话入口。
- Modify source/blender/editors/space_view3d/view3d_axismeld_hotbox.cc: 固定 direct roots、修饰键与选择域生命周期。
- Create source/blender/axismeld/AXM_context_modeling.hh and update its CMakeLists.txt: 固定根/域/叶白名单与默认菜单fixture依赖，原生测试双向核对实际目录。
- Tests tests/python/axismeld_context_modeling_hotbox_test.py and axismeld_context_modeling_events.py; extend UI runner and native geometry fixtures/tests as required for new roots.
- Update tests/python/axismeld_create_hotbox_events.py: Edit 已选单域现在属于 MODEL；旧创建回归改用空 Edit 选择继续证明真实 Cursor fallback，已选单域行为由新 M2d GUI 覆盖。

**Interfaces:** root selector returns one of `context.modeling_vertex`, `context.modeling_edge`, `context.modeling_face`, or no root without state mutation; existing `context.create_hotbox` remains independent. Leaf IDs come from existing COMMANDS/MODELING_SPECS.

- [x] 编写行为 RED：当前 Edit 有选中面 Shift+RMB 不开启建模热盒；默认 profile 与生成后的 Object/Mesh 同键路由应互斥，非法同上下文冲突仍失败。
- [x] 实现根和菜单表，按设计逐项引用现有命令；层级配置不得注入任意 operator 或新的可执行缺口。
- [x] 实现独立入口和 narrow context collision 规则；检查旧个人 create 改绑/禁用仍工作，原生 fallback 未被删除。
- [x] 扩展 C++ direct mouse 会话：立即显示、拥有鼠标、修饰键改变取消、选择域变化取消；复用纯布局可见区域修复。
- [x] GUI 验证真实 Poke/Bevel/Merge/Extrude 与一次 Undo，模态取消差异与持久工具下一步输入，当前选择不被鼠标覆盖、空/混合/非网格回退。
- [x] 验证新增根/子环与 Views 间距、返回区、缺席方向及外延；运行 Python、五组 native 和相关 GUI 回归。
- [x] 独立审查后安装隔离候选实例，保留正在运行的旧实例和配置，补齐构建与人工清单记录，提交本地分支。

## 执行记录

依赖：2026-09-14-hotbox-visible-region 的 C++ 独立审查未发现实现缺陷；两项测试覆盖问题由原测试作者收尾。M2d 可以基于冻结的可见区域实现接入会话，前片固定候选二进制不受源码后续编辑影响。任何前片生产修正均由控制者顺序合入并重新构建，不允许两个作者同时修改共用文件。

安装约束：用户当前主实例正在运行。候选使用独立的 `D:/source/AxisMeld-build/m2d-ui-test-install`，不向运行中的旧实例覆盖 Python 资源。候选二进制与 Python 资源须共同核验；原配置只复制到候选，不写回旧实例。

Native接口补充：使用 `AXM_context_modeling.hh` 的精确root/domain/per-root叶表，实际默认fixture检验一致性及伪造prefix/跨根命令拒绝；C++ BMesh只读实时条件与Python selector保持一致。保持既有可见区域布局实现，不增加通用框架或Python定时目录重建。

完成记录：实现、独立审查、99项Python、五组native及本批12组GUI验证通过；独立候选与26份资源及复制配置已核验。统一人工清单131项/47已测/84待测，其中新增22项，人工继续暂缓。源码与本地提交见构建核验记录。
