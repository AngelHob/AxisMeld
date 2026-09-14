# M2d Object 建模与预选工具入口

后续组合菜单修正见 [Object Shift+RMB 组合菜单](2026-09-14-object-modeling-composition.md)。本文保留三个原生工具入口片的历史范围；下方列表和独立 Options 以新记录为准。

继续 M2d-P02 的 Object/预选事务和 M2d-P04 持久工具入口。本片接入已有 Blender 工具，不新增三套几何算法；M2d 不整体关闭。

## 本机来源与方向

Maya 2026 `scripts/others/contextPolyToolsObjectMM.mel`：E Append（51–64），SW SplitEdgeRing（35–48），W Multi-Cut（90–106），NW Sculpt（112–125）。分别适配 Blender Poly Build、Loop Cut、Knife；Sculpt 仍是缺口，不能将 Circle Select 放到 Object 的 NW。

| 方向 | 本片行为 | 范围 |
|---|---|---|
| E | Poly Build (Append Adaptation) | 提交后进入 Edit 并激活 `builtin.poly_build`；保留 Blender 建面/拖动操作，不是完整 Maya Append |
| SW | Loop Cut Tool | 进入 Edit 并激活 `builtin.loop_cut`；后续点击由 Blender 决定可切割边环 |
| W | Knife (Multi-Cut Adaptation) | 进入 Edit 并激活 `builtin.knife`；后续切割、确认和取消由 Blender 接管 |
| N / NE / SE / S / NW | 禁用并注明原因 | Target Weld / 整物体 Fill Holes / 锐边处理 / 整物体 Extrude / Sculpt 另行完成 |

`contextPolyToolsMM.mel:186–191` 先读取完整 selection，只有空选择才读 preSelectHilite。Maya 后续 any polygon match 可以路由 Object；本片收窄为所有已选对象都合格。Maya 菜单文件只查询预选，不能作为任意建模命令自动选中预选对象的证明；本片的延迟提交是 AxisMeld 适配决策。

## 输入与事务

默认仍为 Shift+RMB。MODEL 扩展到 Object 和 Mesh 两域；CREATE 仍仅 Object 无选择且鼠标空白。两个既有 profile ID 独立改绑/禁用。当前选择优先于鼠标；不合格的选择集不会被过滤后偷偷作用于另一物体。鼠标候选只在完全无选择时启用，键盘改绑不拾取鼠标位置。

开盒固定目标身份，开盒/取消不选中、不切模式。确认有效方向才在专用事务中选中预选对象、进入 Edit、启动工具。已有选择保留 active 和多选集合。Global Undo 开启且步数大于零时，启动这一步可一次撤销到原 Object 模式和对象选择；后续笔划另按原生工具撤销。启动失败恢复两个模式的工具槽及选择/组件状态；启动工具不写 Recent。

多对象 Edit、共享 Mesh data、隐藏组件和后续笔划作用域仍遵循 Blender。同一 Mesh data 只有一个代表对象进入 Edit，其余共享实例仍为 Object 并保持已选，几何仍共享；不拆分 data。不会为了使用某工具把残留组件选区扩成全选，也不会把刀具激活记为切割已完成。

## 后续顺序

1. M2d-P02/P03/P05：整物体 Fill Holes、锐边动作、Object Extrude，各自定义作用域与撤销；补无选择 Edit 组件预选。
2. M2d-P07：Ctrl+RMB 选择转换、Ctrl+Shift+RMB 当前工具上下文。
3. M2d-P01/P04/P06 与 QWER/M3 明确缺口：Create Polygon、持续 Target Weld/Append 差异、创建选项、工具高级参数。
4. UV 独立设计与实现。Global 物体缩放无开发计划。

具体运行证据与人工条目由同批 acceptance 和统一 manual-test-ledger 记录；源码菜单接入不等于完成手感验收。
