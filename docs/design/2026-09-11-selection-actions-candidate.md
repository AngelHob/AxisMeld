# 常用选择动作候选设计

状态：2026-09-11 03:29 启动最小三个动作；映射切片终审修订复核已通过。仍须完整验证和独立审查，未完成前不算交付。
依据：[本机语义预检](../development/2026-09-11-modeling-adapter-preflight.md)。

## 最小范围

先考虑三个已有原生 operator 可以承担的同步动作，不把所有建模候选同时接入。

| 语义 ID | 菜单标签 | 执行上下文与原生路由 | 明确差异 |
|---|---|---|---|
| `selection.select_all` | Select All | Object → object.select_all(SELECT)；mesh Edit → mesh.select_all(SELECT) | 选择 Blender 当前上下文的可选对象或组件，不覆盖 Maya DAG/UFE 规则 |
| `selection.grow` | Grow Selection | 仅 mesh Edit → mesh.select_more(use_face_step=True) | 使用 Blender 原生拓扑遍历，不声称与 Maya GrowPolygonSelectionRegion 算法一致 |
| `selection.shrink` | Shrink Selection | 仅 mesh Edit → mesh.select_less(use_face_step=True) | 使用 Blender 原生拓扑遍历，不声称与 Maya ShrinkPolygonSelectionRegion 算法一致 |

三个动作均标为 adapted，使用 EXEC_DEFAULT，不自动切换对象/编辑模式。默认不绑定新快捷键；
保留 A 的 Frame All、F8–F11 的模式切换和 W/E/R，不在本切片扩展快捷键元数据格式。
个人配置仍可通过现有语义 ID 绑定机制覆盖。

## 接入与门禁

- Common → Select 保留现有五项（包括分隔项）及其顺序，在末尾追加三个动作，总计八项；
  不增加额外目录，不解锁 UV 或其它占位按钮，不更换现有 Select 热盒容器。
- 组件切换的可编辑网格门禁改为匹配既有四个准确 ID，而不是泛化所有 `selection.*`。
  新动作分别用真实上下文与对应 operator.poll() 判断，Object 全选不要求已有活动网格。
- Grow/Shrink 在 Object 或不支持上下文灰显，给出原因；不偷偷进入 Edit Mode。
- commands 元数据、runtime 菜单允许表、catalog close/replay 策略、原生解析允许表同步增加准确 ID。
  未知或未实现 ID 仍拒绝。新动作沿用 close_before=True、replayable=True，执行前释放热盒输入所有权。
- 返回原生状态；仅原生 FINISHED 按现有规则进入 Recent。Select All 在不同模式的 no-op 返回
  不统一包装，不增加几何快照比较，不改全局历史或 undo 包装器。

## 验证门槛

- 新登记测试先 RED：菜单准确顺序与 ID、完整未绑定集合、旧默认绑定逐项不变、原生解析接受新
  ID 而拒绝未知 ID；不能只验证 registry 含有字符串。
- 安装态真实场景：无 active 的 Object 全选；混合对象、隐藏和不可选；mesh Edit 点/边/面模式；
  多对象编辑与共享数据。结果断言用预先定义的对象/组件集合，不用实际结果回填预期。
- 已知拓扑 Grow/Shrink：边界选择与一次撤销；不支持上下文灰显并拒绝分发；无选择/无变化
  保留原生返回状态与 Recent 规则。
- Face Step=true 包含共顶点的对角面；采用 5×5 四边形面片的中心面12，扩展预期
  `{6,7,8,11,12,13,16,17,18}`，随后收缩预期 `{12}`。同时检查网格几何与 UV 坐标不变；
  原生 UV 选择同步缓存可能失效并以网格选择为准，不承诺独立 UV 选择状态完全不变。
- 必须有真实鼠标菜单路径执行、热盒关闭后 W/E/R、执行一次撤销恢复场景、用户绑定保存/重载。
  坐标夹具只供投递事件。添加菜单叶子会改变椭圆布局，既有 Select 菜单事件坐标要同步，
  但保留原有组件切换和退出结果断言。
- 复用当前测试安装与私有 GUI 配置；不新建完整安装。先记录旧阶段失败，再安装并跑相关回归。
- 独立审查通过才写入本批完成列表；真实 undo 或上下文异常优先修复，不以范围扩张掩盖问题。

## 继续延期

Select None 的模式切换组合、空选择 Invert 语义、Duplicate、Linked Selection 均不在这三个动作中。
如果时间不足，这份设计留作后续入口，不以仅登记命令或仅通过纯测试宣称功能完成。
