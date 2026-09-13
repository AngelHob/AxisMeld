# M2b 组件右键目标对照

日期：2026-09-13。状态：有界适配已安装、人工待测，最终结果见[本批验收记录](../compatibility/2026-09-13-m2b-pointer-target.md)。

只读核对本机 Maya 2026 安装脚本，提取输入路由与命令身份，不复制实现。

| 来源位置 | 核实事实 | AxisMeld适配及差异 |
|---|---|---|
| others/buildObjectMenuItemsNow.mel:142-155 | 使用dagObjectHit；没有命中时查看当前选择/高亮集合，再路由dagMenuProc | Object鼠标入口拾取，空白沿用活动选中网格；不宣称复刻Maya高亮集合/UFE所有规则 |
| others/dagMenuProc.mel:2564-2577 | 参数对象为空时从现有选择/高亮确定默认对象 | Edit/键盘/Space保持原上下文，本片不跨编辑集合拾取 |
| others/dagMenuProc.mel:1276-1292 | 组件动作绑定目标对象与选择mask；Object Mode在NE | 复用selection.vertex_mode/edge_mode/face_mode与mode.object；方位保持M2a |

稳定入口命令：context.component_hotbox。分类：adapted。默认输入：无修饰RMB PRESS→划选→RMB RELEASE。不新增PRESS之外的profile schema值。

本片采用“按下只捕获目标，提交才改变选择”，取消/占位不修改选择、活动对象或模式。未选目标提交使用替换选择；已选目标保留原生多对象集合；这是明确的Blender适配策略，不声称与Maya全部选择偏好等价。

原生对应入口使用只读nearest-selectable GPU拾取，普通选择API的默认策略保持不变。组件目标在X-Ray下仍选最近可选对象，不循环穿透选择，不启用骨骼优先；这是本片与原生普通选择的显式差异。Object或Mesh数据为library override时不作为本片新目标，遵循原生Edit准入边界。

原生接口：ED_view3d_give_nearest_selectable_base_under_cursor；事件验证：tests/python/axismeld_component_hotbox_events.py。安装态新目标/取消/失效/非网格遮挡/键盘与Edit边界通过，日志m2b-installed-components.log；Mesh数据override只完成源码防御核对，未成功构造动态fixture。

人工状态：全部待测，见../compatibility/2026-09-13-manual-test-ledger.md 的P-01至P-13。UV、Vertex Face、Multi Component仍是不可执行占位；Shift/Ctrl建模热盒不属本片。
