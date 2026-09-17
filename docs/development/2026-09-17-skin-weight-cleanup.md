# A1 · Skin 权重整理

基线：`axismeld/phase-2a` 的 `96e0ce6dd081d6e3df001565e9f7fe223843358a`；Blender 5.3.0 alpha。范围仅一次性 Normalize Weights 和 Prune Small Weights，保留原 ID、层级、正文和 Options。Enable/Disable/Post 持续模式继续灰显。

## 语义审计与选择

- 单组 Normalize 把该组最大值缩放到 1，不能用于逐顶点蒙皮归一化。Normalize All 接近目标，但本版本在执行时自行选择骨骼组范围，默认锁活动组，不能据传入 subset 参数保证作用域。
- 本仓库 `object_vgroup.cc` 的 Clean 删除 `weight <= limit`；不检查组锁、不归一化；对象模式遍历所选对象。`keep_single` 根据所有组的成员数量保留最后一项，不能保证留下最大骨骼影响，非骨骼组也可能使最后骨骼影响被删。
- Maya `skinPercent` 的 pruneWeights 是严格小于阈值，Hold Weights 不剪除；归一化还受 skinCluster 持续模式影响。AxisMeld 本批不创建该持续状态，也不宣称完全复刻 Maya。
- 原生 Clean 的 X 镜像路径还可能触及未选镜像顶点；Normalize All 可将唯一零成员变成 1。适配器不扩展镜像选区，全零顶点始终保持，避免隐式创建变形。0.01 是本批明确选用的阈值，不宣称是 Maya 出厂值。
- 因此使用 Blender 原生 Mesh/BMesh 顶点权重数据和单一原生 Undo operator，先计算完整变更计划，再写入；不串联不符合上述保护的 Clean/Normalize All，不切模式或临时替换选区。原生 Weights 子菜单保持不变。

## 有界产品行为

1. 只处理活动、已选择、可编辑且非共享 Mesh。只允许 OBJECT、EDIT_MESH、PAINT_WEIGHT；多对象 Edit 暂拒绝。需恰好一个 Armature Modifier（包括关闭项也计入歧义检测），目标有效且启用顶点组变形和视窗显示。组范围为该骨架 `use_deform` 骨骼的同名组，非骨骼组和非变形骨组始终保留。骨架仅只读引用，可以是链接数据；网格/对象链接或 override 暂拒绝。
2. OBJECT 默认全部未隐藏顶点；EDIT_MESH 仅当前选中且未隐藏顶点；PAINT_WEIGHT 顶点遮罩按选中顶点，面遮罩按选中且未隐藏面所引用的未隐藏顶点，无遮罩为全部未隐藏顶点。Options 不提供隐式全选或跨对象范围扩展，显示当前范围。活动骨骼的选择不限制组范围。
3. 组 `lock_weight` 始终尊重。Normalize Options 可额外 Lock Active（默认关），不会改写永久组锁。正权重总和缩放到 1，锁定值固定，剩余配额按未锁定正权重比例分配。全零顶点保持原状并报告；无可分配权重或锁定和大于 1 时整次取消、无修改。不会凭空创建影响。
4. Prune 默认阈值 0.01，严格 `<`，支持 0..1。只移除未锁定变形骨成员。默认 Keep Strongest 防止清空最后正骨骼影响（并列取最小组索引）；默认 Normalize After 在修剪后执行同样的锁定归一化。关闭保护可明确清空顶点，零权重仍不自动补权；关闭 Normalize After 保留剩余值。不会删组或改变 modifier、父级、变换。
5. 正文用明确默认参数执行一次；右侧齿轮打开原生参数对话框，打开、修改参数和取消不写权重，确认才执行。Blender 键位的 F9 或 Edit → Adjust Last Operation 可调整本次操作；Maya 键位保留原 F9 Vertex 映射。每次有效操作一次 Undo；首次无变化返回 CANCELLED，不制造空 Undo；F9 已先撤销旧操作，重算为空时返回 FINISHED 保留恢复的原值，避免原生重做机制把旧修改重新套回。操作执行时重新校验上下文，所有可预见输入错误先于写入。

## 验证计划

- 纯函数先写失败测试：比例/锁定/活动锁、严格阈值边界、零成员/零总和、非骨骼组、最强保留、错误输入、整批原子预检。
- Blender 实际 Mesh/BMesh：所有支持模式、顶点/面遮罩、隐藏和未选顶点、第二所选对象保持、共享/链接/多骨架/多对象 Edit 拒绝；锁定和非骨骼组保持。
- 真实原生菜单/齿轮、取消和一次 Undo；原 82 正文/33 Options 顺序与身份不变，其中只开放 2 正文/2 Options。其余保持灰显，9 个 Blender 入口及插件宿主保留。
- 公开人工项使用新稳定 RG 编号，旧结果不改；自动结果单独记录。候选只替换公开发布包中的已核验 Python 脚本，C++/startup 不变；明确记录二进制来源、源码 SHA、资源指纹与许可，重新解压启动后才更新下载版本。

## 官方资料

- [Maya 2026 skinPercent](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Tech-Docs/CommandsPython/skinPercent.html)
- [Blender 顶点组编辑](https://docs.blender.org/manual/en/latest/modeling/meshes/properties/vertex_groups/vertex_groups.html)
- [Maya Prune Options](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-CharacterAnimation/files/GUID-8F1059A8-D31C-4F4D-A8B4-9C8E3322F320.htm)
- [Maya 持续归一化模式](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-CharacterAnimation/files/GUID-CF2C698A-44BB-4CA0-BCB9-DB36500DA812.htm)

## 实现与验证记录

- `skin_weight_plan.py` 先做完整不可变计划；结果按 Blender float32 存储精度比较，已经归一化的 RNA 值不产生空变更。`skin_weight_ops.py` 写 Mesh/BMesh，直接拥有一个原生 Undo 步骤；没有调用改选区/模式的 operator。菜单仅为这两个已审计 Maya 命令身份提供正文/齿轮。
- 36 项纯计划器测试已验证红→绿；19 项真实 Blender 数据测试通过，包含实际 Edit BMesh、绘制顶点/面遮罩、隐藏点、第二对象、多对象 Edit、共享/链接网格拒绝（Fake User 不算第二个对象）、链接骨架可用、全零/锁定和失败、float32 无变化及保存读回。
- 原 Rigging、menubar、workspace 及 input 共 97 项针对测试通过。当前 82 正文/33 Options 身份与顺序保留，开放 2 正文/2 Options，剩余 80 正文/31 Options 保持灰显；9 原生入口保持。
- 新机器公开包基线通过 ZIP/139资源/88 Rigify文件审计、启动/portable/raw布局、factory/reset、Rigify生成/重开/生命周期，以及原 Rigging GUI/独立重开。未进行本机 C++ 全量构建；C++/startup 与已发布 native 来源完全不变。
- 本批新增人工 RG-15～RG-20，全部待测；RG-07～RG-14 和 47 条历史已测试信息没有被自动测试覆盖或改写。生产角色变形、性能、第三方扩展与高 DPI 仍待人工验收。

- 真实 GUI 7 项通过：两个正文、两个齿轮的修改/取消、Prune 参数确认、F9 重算与一次 Undo；F9 从有效修剪改为零阈值且关闭归一化时恢复原权重。该缺陷先由真实界面得到 RED，再验证修正后的 GREEN。受测窗口 1920×1017、默认缩放；自动事件不是人工操作结果。
- 修正单对象 Mesh 的 Fake User 被误当第二个对象的问题，有独立真实数据红→绿回归。保留拒绝真正共享 Mesh 的保护。
- 公开目录 314 项、当前 302、历史 12、历史已测试 47；站点结构/状态与 12 项本地浏览器检查通过。建模映射仍为 392 条、85 有绑定/307 灰显；去向审计的源码文本指纹统一 LF，避免 Windows CRLF checkout 产生伪变化。

发布核验在完成后补入；本记录不等于人工验收。
