# A + LMB History Operations 热盒

依据本机 Maya 2026 `scripts/startup/hotkeySetup.mel:261` 与 `scripts/startup/buildSelectAllMM.mel`，本批补齐已有建模范围的输入入口，不新增历史图、变形或变换算法。

## 交互契约

- A 按下仅建立会话；在尚未打开热盒时松开 A 执行 Frame All，无短按计时门槛。
- A 按住时按下 LMB 打开 History Operations，并标记已 posted、清空前次候选。移动使用四视图方向热盒的既有可见矩形/外延命中。
- 松开 LMB 仅记录有效候选，不立即执行；松开 A 才执行最后一次鼠标选择。再次 LMB posted 后重置此前候选。
- 已 posted 但在原点、空处、灰项取消，或者 A 先于 LMB 松开，均不补执行 Frame All。Esc、窗口失焦、来源上下文失效取消且不执行。
- 原菜单与非键盘调用的 Frame All 保持立即执行。保留 `view.frame_all` 命令身份与配置层；默认 A 绑定不增加第二个所有者。
- 每次 posted 绑定活动对象 UID、活动对象数据 UID，以及完整选集的对象/数据 UID 对。LMB 记录和 A 提交前重新比较；持键期间观察到变化立即丢弃候选，恢复原选区也不能恢复旧候选，不补 Frame All。重新 LMB posted 可建立新一次选择；不替用户恢复或改变选区。实际执行仍经过既有能力 poll，数据可写性及几何/修改器条件失效时取消。

## 内容与能力边界

| 方向 | Maya 标签 | 当前执行/占位 |
|---|---|---|
| W | Select All Inputs | 灰占位：没有 Maya DG 输入图选择提供器 |
| E | Select All Outputs | 灰占位：没有 Maya DG 输出图选择提供器 |
| N | Enable All Outputs | 灰占位：没有 Maya DG 输出启用适配 |
| S | Disable All Outputs | 灰占位：没有 Maya DG 输出禁用适配 |
| NW | Delete History | 既有 `edit.bake_selected`，保留网格/修改器栈约束与语义差异 |
| NE | Delete Non-Deformer History | 既有 `edit.bake_selected_non_deform`，保留可处理栈限制 |
| SE | Freeze Transformations | 既有 `transform.apply_all`；Blender Apply 语义，Options 独立灰显 |
| SW | Reset Transformations | 既有 `transform.reset_all`；Blender local 变换复位语义，Options 独立灰显 |

目录身份 `context.history` 放入现有 internal marking 树，不添加新的全局根，不混同 Recent Commands。纯状态帮助器负责 posted/候选/触发键释放；原生入口验证八方向及每个可执行命令的对应 ID，拒绝外来命令注入。执行前重新做现有能力 poll，原生子操作拥有 Undo。

验证将覆盖目录全量八方向与两个 Options、默认/自定义 A 绑定单一所有权、键盘建立会话与菜单直接 Frame All 分流、posted 后取消与重复唤出的状态，以及当前 Views 几何模板。真实事件和本批构建由统一 GUI 回执记录。

## 已执行检查与 GUI 回执范围

2026-10-11 源码层针对性检查：`axismeld_history_hotbox_test.py` 4 项、`axismeld_tool_hotbox_test.py` 6 项、`axismeld_hotbox_catalog_test.py` 21 项、`axismeld_menubar_integration_test.py` 7 项及 `axismeld_context_modeling_hotbox_test.py` 12 项均通过；新增 Python 模块与事件脚本通过 `py_compile`，`git diff --check` 无空白错误。新原生帮助器及其状态/严格目录测试需要本批 C++ 增量构建，Python 检查不代表原生测试或实际 UI 已通过。

独立事件脚本 `tests/python/axismeld_history_hotbox_events.py` 使用 `window.event_simulate` 注入实际 A、LMB、Z、Esc 和窗口失焦事件，用截图中八个实际按钮背景定位鼠标目标，不从原生布局状态推导命中位置。执行结果由统一 GUI runner 验证，成功标记为 `AXISMELD_HISTORY_HOTBOX_EVENTS_PASS`。覆盖如下：

| 用例 | 必须观察的结果 |
|---|---|
| 未 posted 短按、长按 A | 按下不改变视图；松开才 Frame All，场景不变 |
| 已 posted 中心、灰项取消 | 不修改场景、不补 Frame All、不遗留 modal |
| Reset、Freeze、Delete History、Delete Non-Deformer History | 松开 LMB 后完整场景不变；松开 A 才出现对应实际变换/网格/修改器变化；一次 Z 恢复完整场景 |
| 单次 A 持键内再次 LMB | 第二次实际热盒重新出现；再次 posted 清空首次候选，第二次取消不执行首选动作 |
| A 先于 LMB 松开 | 不提交悬停动作；吞掉尾随鼠标释放，无 handler 遗留 |
| Esc、失焦取消已记录候选 | 即使 LMB 已选中有效动作，A 后续释放也不提交、不 Frame All |
| 选区切换后的 Reset 与 Delete History | 同 scene/mode 下切到另一对象，旧候选取消；原目标和新目标都不变 |
| 增选、只改活动对象、原对象/另一所选对象的数据 UID 替换 | 完整所选对象身份不一致就取消，不通过隐式选区恢复继续执行 |
| 选区改变后又恢复、LMB 记录前改变选区 | 已观察到的失效不可恢复旧候选；变化发生在方向选择过程中也不提交 |
| 数据 UID 不变但新增 Shape Key | 现有 Delete History 能力 poll 在 A 释放重新判定，取消不再满足条件的命令 |

事件证据写入 runner 的 `history-hotbox-events.json`，包含每个操作前、LMB 释放后、A 释放后与一次 Undo 后的物体变换、网格顶点/面、修改器栈、选区、活动对象和视图状态，配套每次实际热盒截图。该脚本的覆盖定义不是预先宣称 PASS；以本批最终 GUI 回执为准。

评审修复补充了两个纯原生状态测试：完整 UID 签名变更不重定向已排队命令；LMB 记录前或事件间观察到的变更永久取消旧候选。它们使用无 Blender 对象指针的值签名模拟 active、选集、active data 及另一所选对象 data 变化；实际签名采集与 scene/mode 生命周期由 GUI 事件回执验证。本次修复后的 History Python 4 项、事件脚本语法及针对性 `git diff --check` 通过；新增原生和 GUI 用例待统一 Build03 回执。

## 最终统一候选回执

2026-10-11 的 Build07 已完成原生重新编译与144个资源校验；所选8组139项原生、40组354项纯测试、11项RNA通过。同一最终候选的18组回归全部通过（17 GUI事件 + 1 后台profiles），覆盖本文对应入口、取消/Undo、实际几何与事件状态。前文过程中的“待构建/待GUI”为历史切片状态；最终逐组证据和手工未测边界见[统一验收](../compatibility/2026-10-11-gui-completion-acceptance.md)及[GUI回执](../compatibility/2026-10-11-gui-event-tests.json)。自动事件不将人工条目标为已通过。
