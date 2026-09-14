# Object Shift+RMB 组合菜单修正

用户截图指出：当前Object热盒只有三个工具方向，缺少Maya完整的下方普通列表。2026-09-14本机Maya2026 `scripts/others/contextPolyToolsObjectMM.mel:181-690`核实列表属于同一个Object菜单；不是Space菜单的替代入口。

## 目标与边界

恢复同次Shift+RMB唤出的八向热盒、下方22个主条目（含3个目录及Transfer Vertex Order条件项，不计分隔和Options）、原顺序与分隔、Mapping/Booleans/Polygon Display级联和独立Options方框。继续已批准的“方向动作热盒，设置和深目录原生列表”设计。先接通已有可验证的Object能力与工具；几何算法、UV、Maya construction history和代理流程不能靠换标签宣称完成。

八向使用Maya可识别名称（Target Weld Tool、Fill Holes、Append to Polygon Tool、Soften/Harden Edges、Extrude、Insert Edge Loop Tool、Multi-Cut、Sculpt Tool），适配差异放状态说明和记录。Views的实际内缘间距、中心取消、外延滑动选择保持。

本片至少接通：Offset Edge Loop、Poly Build形式的Quad Draw、Subdivision Surface形式的Smooth、X轴Mirror、Decimate形式的Reduce、Voxel Remesh修改器、Combine与四种Exact Boolean。参数窗口独立打开，取消不修改场景。其他行保留具体灰显原因，不能偷换Connect Tool、Subdiv Proxy、Transfer Vertex Order或UV含义。已有可复用几何事务只在完整回滚和Undo验证成立后纳入。

## 数据和绘制

- 原Object根 `context.modeling_object` 仍是radial；独立兄弟节点 `context.modeling_object_menu` 为list，固定关联而非新快捷键。
- 原生列表继续由同一hotbox modal驱动 `ui::menu_overlay_draw`，不另开争夺RMB释放的独立WM popup。
- `companion_path` 与径向 `open_path` 分开；下方主列表默认可见，级联悬停不覆盖径向路径。
- Options编码为command/disabled节点唯一的子叶，ID严格为父ID加`.options`；子叶只能为command/disabled，无children/direction/presentation。其他非menu子节点仍非法；Python/native JSON边界同时验证。
- 带Options行保留一个24逻辑像素独立方框，主行扣除这一区域；两者各自enabled、各自命中、各自命令，不靠父节点状态联动。Options不能当子菜单打开。
- 保持快照256KiB边界。对运行时已知、重复的模式/选择/原生poll拒绝说明采用精确等义短句映射；未知错误与唯一缺口原因保留原文。不得为新菜单提高上限、删除功能，或对任意原因静默截断；连同10条Recent验证真实构造预算。
- 先按Views模板放径向按钮，主列表优先放最低按钮下方并留间隔。空间不足对列表分页，必要时翻到不重叠的侧面；不得缩小径向间距或字体。真正按下位置始终保留取消死区。

## 输入与目标事务

实际列表行、禁用行、分隔线、Options和级联通道优先遮挡外延方向；其他空白仍允许八向外延。不能因为常驻列表存在就全局禁用径向命中。滚轮/导航不提交叶子或取消父会话，回到上层保留radial和主列表。

一个RMB释放只走一个submit。Esc、提前松Shift、焦点丢失、源视口/模式/完整已选集/对象data身份变化继续取消；主菜单、子菜单和Options共用此检查。

直接MODEL仍固定对象和选择身份；只有完全无选择才预选。已有工具启动维持一Undo和失败回滚。新增菜单命令与Options使用独立固定白名单；按主行ID检查Options对应关系，不扩大原三个径向工具allowlist。原生parser须实际解析正负fixture。

参数窗口打开时不提交预选、不改变选择/模式/几何。窗口确认时再次核对记录的对象/data/active/完整选择身份；失效取消。新菜单中的目标事务单独验证，不把异步Remesh启动误当同步完成。未提供预选事务的功能明确要求先选择对象，不能偷偷使用另一个active对象。

独立复核确认：原生QuadriFlow的参数窗口在确认时重新读取当前active，已有选择也不能满足上述固定目标约束；EXEC路径又会变成同步阻塞。因此本批新companion中的Retopologize主项和Options都灰显并注明确认身份适配缺口。既有Space Mesh中的原生入口保持其原语义；不为本次UI修复追加后台任务架构，也不把当前active改动解释为合法转投目标。

## 验收

旧候选上记录缺少下方列表的RED。新候选真实截图须同现有Views比较内缘；验证上下同时可见、22行顺序及分页可达、3种级联、Options独立/取消、列表外不误选、下方穿越遮挡、外延方向仍有效、中心/Esc/源失效取消、快捷键重绑、单/四视图与边缘。

功能验证至少覆盖修改器实际结果/撤销、Combine和Boolean目标、工具启动/笔划、参数取消无副作用。运行受影响Python/native和Object/组件/创建/QWER/M3 GUI回归。构建到新独立目录，保留用户两个旧安装及其配置；当前仅PID 44504的旧实例仍在运行，不覆盖该运行实例。人工记录追加到统一清单，既有反馈不被自动化覆盖。
