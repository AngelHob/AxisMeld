# M2d Object 与预选工具入口设计

本片继续已授权的 M2d-P02、P04；先完成可独立验收的持久工具入口。上一片是 `93330f3ef59` 的已有 Edit 单域建模菜单。人工测试仍搁置。

## 来源与范围

Maya 2026 本机 `scripts/others/contextPolyToolsMM.mel:186-191` 先看 selection，完全为空时才看 preSelectHilite。Object 根 `contextPolyToolsObjectMM.mel:27-175`：N Target Weld、NE Fill Holes、E Append、SE Soften/Harden、S Extrude、SW Insert Edge Loop、W Multi-Cut、NW Sculpt。预高亮决定菜单不等于源码保证所有命令自动选中目标；下面的提交行为是 AxisMeld 明确的适配。

选择本片方案：复用已有 Blender 持久工具，提交时一次性进入 Edit。相比直接复用 Object modifier 命令，此方案保留 Maya 八向含义；相比本片同时实现全部几何动作，能先验证目标与模式事务，而不混入挤出宏的取消规则。

- `context.modeling_object` 独立根，E `tool.object_mesh_poly_build` → `builtin.poly_build`，SW `tool.object_mesh_loopcut` → `builtin.loop_cut`，W `tool.object_mesh_knife` → `builtin.knife`。
- 标签明确为 Poly Build (Append Adaptation)、Loop Cut Tool、Knife (Multi-Cut Adaptation)。N/NE/SE/S/NW 保留带父项编号的 disabled 项；Object 的 NW 不复制 Circle Select。设置与深目录仍使用原生普通菜单。
- 整物体填洞/锐边/挤出、Sculpt、Target Weld 完整工具、Edit 无选择组件预选、Ctrl 两类菜单另行开发。本片不宣称完整 M2d 或 Maya 工具算法完成。
- Global 物体缩放无开发计划。

## 路由契约

沿用两个个人配置 ID：CREATE 仅 Object；MODEL 扩展到 Object + Mesh。两者仍可分别改绑/禁用，同事件的特许仅限这一对。CREATE 的空白创建规则保持，MODEL 无候选时 PASS_THROUGH。不要依赖 keymap 插入顺序实现互斥。

Object 有任何已选对象时只用当前选择集，完全忽略鼠标拾取。首片要求所有已选对象均为可见、可选择、可编辑、非 library override 的 Object Mesh，active 在集合内；混合类型、隐藏/锁定/不可编辑选择、缺少有效 active 均原生回退。这比 Maya 的 any polygon match 更窄，属于明确限制。使用完整 view-layer base 选择集，不遗漏隐藏选择。共享 Mesh data 不暗中拆分：原生每份 data 仅一个对象代表进入 Edit，其余共享实例仍为 Object 并保持已选，几何继续共享。验证进入 Edit 的对象属于原捕获集合、active 进入 Edit、全部独立 data 恰好覆盖一次，不要求所有共享实例都显示 Edit。普通多对象与工具实际作用范围遵循原生工具。

完全无选择时，仅鼠标入口允许原生 GPU 最近可选对象预选。前景非 Mesh 不穿透。键盘重映射只使用已有选择。开盒时固定 target session UID / data UID；已有选择时固定全部对象及 data UID 和 active。每次 modal 与提交重查 scene、view layer、原窗口区域、mode、目标资格与选择身份；发生变化即取消，不转投新目标。

开盒、移入方向、子环返回、Esc、中心/缺席方向、修饰键提前释放和源上下文失效均不改变选择、active、组件状态、模式或几何。只在拥有的触发释放到有效叶子时提交，清理热盒及 ownership 后启动工具。

## 提交事务

新增专用 `AXISMELD_OT_object_modeling_tool` / `axismeld.object_modeling_tool`（INTERNAL、UNDO），固定 `command` 与 `target_uid` 字符串属性；空 target 表示完整已有选择，非空 UID 仅接受无选择时捕获的对象。UID 不允许通过有符号 IntProperty 截断。C++ 独立固定三条 allowlist；只在 Object 根中允许这些叶子，拒绝 settings/跨根命令。

目标选择在这个专用操作器内提交，不复用原 `commit_component_target` 的先选中后 dispatch 流程。操作器重新验证目标；预选提交才选中并激活 target，已有选择保留 active 和整个集合。调用原生 `object.mode_set('EXEC_DEFAULT', False, mode='EDIT')`，随后 `wm.tool_set_by_id('EXEC_DEFAULT', False, name=...)`。两子调用均无独立 Undo，外层负责一次撤销。进入工具后保留 Edit 模式，下一笔由原生工具接收。工具启动不写 Recent，也不声称已经改变几何。

与已有 V/E/F 根一样，Object 根也可经 Space 的 Select 目录或自定义中心按钮进入。此显式目录路径沿用其他 Space 动作的“提交时重查当前选择”语义，不启用鼠标预选；固定按下时目标的保证属于直接 MODEL 手势。目录的通用 native→Python bridge 可调用 adapter 中显式 True undo 的专用外层，不能将可见启用项变成无反应的菜单；实际 GUI 单 Undo 必须覆盖此路径。

启动失败恢复 Object、active、原对象选择、mesh_select_mode、原组件 select/hide 状态及 Object/EDIT_MESH 两个原工具槽，返回 CANCELLED，不生成 Undo/Recent；CANCELLED 返回与异常都需回滚，不得以宽泛异常捕获隐瞒回滚失败。启用 Blender Global Undo 且 undo_steps 大于零时，启动成功要求一次 Undo 恢复原模式与对象选择；用户关闭撤销时遵循 Blender 偏好，不擅自打开设置或阻挡正常工具。工具笔划的几何编辑另由原生 Undo 管理。测试必须证明这个边界，不凭嵌套 undo=False 推断。native 直接 WM_operator_name_call 专用 UNDO 操作器，Python 普通调用该外层必须显式 True undo，以免默认 False 抑制整个事务入栈。

Blender 的 WorkSpace.tools RNA 只提供查询/创建，没有删除工具槽接口。若失败前某模式从未有工具槽，恢复到原生 `builtin.select_box` 初始化默认值；已有槽要求精确恢复原 ID。此初始化例外不改变场景、选择或几何。

## 验证与交付

纯 Python：固定根/方向/空命令缺口、仅固定三 action、模型与创建互斥 keymap、独立 remap/disable、第三绑定冲突不放宽、纯只读资格判断。

原生：实际 Python catalog 双向 allowlist fixture、Object root 八向与 Views 真实内缘间隔、settings/跨根拒绝。保留已有全部 native hotbox tests。

实际 GUI：旧候选真实 Shift+RMB RED；已有选择优先于其他鼠标目标，取消无变更；空选择最近 Mesh / 非 Mesh 阻挡 / 真空白 CREATE；三工具分别进入 Edit 且有真实后续笔划；单次 Undo 恢复模式/选择；多对象/共享数据、异常失败回滚、身份/选择变动取消；CREATE/MODEL 同键/分键/禁用/键盘映射；QWER、Edit 与创建已有回归。渲染间隔与同实例 Views 比较，不固定字体像素，也不把对角所有视觉空白视作取消。

安装前检查运行进程。使用现有 M2d 候选作为下一份候选时先留可回滚旧构建，保留 portable config；不覆盖运行实例。旧 47 个用户确认测试条目保持，新的人工项追加到统一清单；自动化不替代手感测试。
