# M3 建模菜单与快捷键覆盖实施计划

> 执行方式：使用独立子任务并行实现，共享接口先冻结，集成与 GUI 验证串行。

**Goal:** 完成已批准 M3 的 12 组菜单、原生能力接入、默认快捷键核实与缺失能力计划，并统一人工测试清单。

**Architecture:** 保留现有语义命令、上下文适配与热盒架构。新增不可变的建模命令声明，按公共编辑、网格、曲线曲面变形分模块；固定原生 operator 与参数不能来自配置文件。通用 dispatcher 不拥有撤销，原生子操作或特定复合操作拥有单步撤销。

**Tech Stack:** Blender C++ / Python / RNA / native event test runner。

**Spec:** ../specs/2026-09-11-modeling-interaction-alignment-design.md

## 约束

- 先完成热盒间距修复并验证，再实施 M3。Views 是五行热盒间距和安全区域的实测标杆，参见 ../../development/2026-09-14-hotbox-reference-contract.md。
- UV 整体后置；不启动动画、绑定、渲染、雕刻完整流程；不改变已搁置的 Global 物体缩放算法。
- 保留 QWER 连续划选、原生列表、Space 与鼠标释放所有权、已有个人配置。
- 仅对主 Space 热盒和明确支持的命令扩展 Curve / Surface / Lattice Edit 上下文，原组件 RMB / QWER 不扩展。
- F9 仍是 Vertex；参数入口使用 Edit > Adjust Last Operation。交互操作启动不代表完成，不提前写 Recent。
- 原生 poll、目标数量、可编辑状态、域和参数需校验；添加无目标空修改器不算实现 Boolean / 变形功能。
- 真实缺失能力按唯一计划记录；不得用未适配作为原生不存在的证据。
- 构建和 GUI 使用唯一锁，所有安装更新保留备份并核对个人配置哈希。

## Task 1: Views 间距修复

- [x] 原生回归比较所有径向菜单与 Views 的第二/四行、第三行真实内边距。
- [x] 替换固定 24 宽锚点；中心返回区与缺失方向阻挡同步。
- [x] 54 项几何测试、工具/组件/创建三组 GUI 事件通过；截图确认。

## Task 2: 固定注册接口与公共命令

文件：scripts/modules/axismeld/modeling_schema.py、modeling_common.py、modeling_common_ops.py。

- [x] 冻结 CommandSpec / NativeCall，按 category / section 构建原生列表；记录来源、差异、模式、执行、撤销和可重放策略。
- [x] Select / Modify / Edit / Create / Display 全部可用原生候选接入，复合 Group / Match 使用有界专用操作。
- [x] 核对默认键位与冲突；真实状态选项沿用单选/多选表达。

## Task 3: 网格命令

文件：modeling_mesh.py、modeling_mesh_ops.py；拥有 Mesh / Edit Mesh / Mesh Tools / Mesh Display。

- [x] 固定原生调用、选择域、目标和工具身份，禁止仅改标签。
- [x] Boolean 的目标/操作与求值结果、编辑拓扑、法线/颜色及工具交互做针对性测试。

## Task 4: 曲线曲面变形

文件：modeling_shapes.py、modeling_shapes_ops.py；拥有 Curves / Surfaces / Deform。

- [x] 为真实 Curve / Surface 原生项接入对应 Edit 模式；不用网格模式假接入。
- [x] 变形目标必须就绪，复合步骤原子撤销；非线性默认值产生可观察结果。

## Task 5: 集成与完整性审计

文件：modeling_registry.py、modeling_adapter.py、commands.py、adapter.py、hotbox_catalog.py、hotbox_runtime.py、keymap.py、startup bl_operators/axismeld.py、native view3d_axismeld_hotbox*。

- [x] 12 组逐项映射 Maya 静态菜单身份，选项框与重复声明合并；目录、动态供应商和范围外项明确分类。
- [x] 每个范围内动作映射已接入命令或有理由的能力计划；Blender 扩展归入对应功能组。
- [x] 生成并检查 native 明确命令白名单；JSON 节点和字节限制保持有界，未知 ID 拒绝。
- [x] 上下文准入、菜单路径、旧配置、默认键冲突与占位不可执行测试。

## Task 6: 验证与交付

- [x] 全声明实际 RNA/参数校验，代表性真实几何与单步撤销；模态确认/取消、Recent、参数入口和上下文 GUI 测试。
- [x] 相关现有原生/配置/热盒 GUI 回归；不把自动化等同人工手感通过。
- [x] 同一构建实例更新，二进制/资源与配置哈希验收，保留回退副本。
- [x] 统一 ledger：既有 47 项用户确认已测、G10/K12 仍待测、本轮布局与 M3 新增待测；记录明确差异和缺失计划。

完成证据：../../compatibility/2026-09-14-m3-modeling-acceptance.md；人工状态仍按统一清单。
