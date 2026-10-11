# UI 阶段输入参考复核

先完善参考，再生成审计。2026-10-11 复核 Maya 2026 安装目录的默认 hotkeySetup、ModelEdMenu、defaultRunTimeCommands，与 Autodesk 官方键位表对照；只提交事实、身份、行号及原文件 SHA256，不复制厂商脚本或读取个人配置。

设计：独立 JSON 补充原 M3 参考，保留旧来源；给可规范化的输入保存结构化事件，不用简单字符串替换消除差异。审计比较实际按键、修饰键、事件值，并保留 release 语义。`same_event_definition` 仅说明入口定义相同，不说明功能、菜单内容或按住/松开已验收。新键位必须补充参考，不得默认为“已对齐”。

原 18 条正文参考与 Grow/Shrink 两条 US 标点写法均获得直接来源。Quad Draw→Poly Build、Multi-Cut→Knife、Delete 拓扑行为保留 adapted；A 的 Frame All 与 A+LMB History Operations 在本批接入同一入口：未 posted 时 A 松键聚焦，打开菜单后只执行所选 History 操作。参考中保留独立生命周期与待 GUI 验收状态。

X/V/J 归 UI 临时状态适配，不作为“缺算法”整体排除。D 需要自定义组件枢轴以及独立旋转/缩放枢轴能力；Object Origins Only 会改对象原点，不能冒充临时枢轴。C 需要与参数曲线最近点求解匹配，EDGE 不能冒充；F12 需要实际 UV 选择域；1/2/3 需要可恢复的平滑预览能力。这六个暂缓键继续保留，避免绑定到无关近似操作。

原生继承与移除项保留每一条实际事件、keymap、区域与属性。导航 Alt 鼠标占用和 Measure 的 X/Del 差异明确列入适配边界；Grease Pencil 绘画工具不属于 Modeling 接管范围，应该保护。F1–F5 与其他未接管键属于 Blender 原生扩展，不宣称与 Maya 一致。

来源事实见 [机器可读参考](../reference/2026-10-11-input-reference.json)，当前输出仍由 [审计工具](../../tools/utils/axismeld_input_audit.py) 根据最终源码生成。独立的自动化与人工结果由主批次记录；本文件不替用户确认 GUI 通过。

## 临时吸附实现契约

原生 `TransInfo` 保存一次操作内的按键顺序及原吸附状态；不改变 ToolSettings。仅 AxisMeld 预设、3D WINDOW、Object 或 Mesh Edit 的 Translate/Rotate/Resize 接管 X/V/J。X→原生 GRID，V→VERTEX，J→INCREMENT；J 对当前有效吸附状态临时取反，保持 Maya 的按下/释放双 toggle 含义，步长仍用 Blender 设置。Shift+J 相对模式不伪装成已实现。

初始化读取 invoke 事件的 keymodifier；运行中在原生 X 轴锁/数值处理前接收原始 press/release（含映射事件的原始 type/value）。重复键不重置快照，重叠键以最后按下仍未释放者为准；Ctrl 临时反转在底层快照中更新，字母释放后恢复当前 Ctrl 状态。切换 transform 模式先恢复原状态，原生初始化新模式后再使用仍持有的临时输入。

松键恢复一次操作的原有吸附方式；确认时仍持键也先恢复再写 Redo/用户设置。Esc 使用原生撤销，失焦有临时输入时取消本次变换。单独按字母不开始 transform，不改变设置。UV、绘画、其他编辑器及非 AxisMeld 预设保持原行为。

自动验证必须分为无 Blender 的状态机和真实事件路径。只有状态值测试不能证明没有轴锁、吸附几何有效或松键不污染场景；已有人工结果保持不变。

## 模拟事件证据边界

真实 GHOST 输入在键盘事件中维护 `keymodifier`；`Window.event_simulate` 不走该路径。为验证“先持 X 再开始变换”，测试接口新增末尾可选 `key_modifier` 参数，并由一次性 F20 触发器显式传入 X。它仍受 `--enable-event-simulate` 控制，运行实际 WM / TransInfo / 原生吸附求解器，使用非网格点到网格点的几何断言，不能只靠无轴锁或状态快照判定吸附生效。这不覆盖实体键盘、GHOST 驱动和 gizmo 拾取的人工手感。
