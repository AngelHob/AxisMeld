# 2026-09-13 工具热盒重复手势与外延事件验证

状态：旧候选取得真实 GUI 失败，最终候选增强 `tools` 组全部通过，
包含复审后新增的隐藏祖先中心/当前子环外延用例。
本报告只覆盖本次事件测试和抽查截图；完整发布验收由主任务汇总。

## 根因与修复边界

只读诊断基线为 `129373b45c6`。原 `tool_modal` 在拥有的 LMB 释放后，
空中心/禁用项直接进入 `close_guard`，可执行工具动作进入 `submit` 的关闭路径。
这会移除热盒 modal、绘制回调和 timer，留下只等待工具键释放的 guard。
继续按住同一个 Q/W/E/R 时，没有新的键盘 PRESS 来建立会话，第二次 LMB 因而无法重开。

`hotbox_command_closes` 的原例外只有即时视图动作；方向槽动作同样会关闭会话。
修复范围是工具键持有期间的 stroke 生命周期：每次 LMB 结束隐藏并清理当次状态，
保留键盘会话，下一次 LMB 以新原点重新显示。同步工具动作采用明确白名单，
没有把模式切换或启动原生模态的未知命令改为保留热盒。

当前工具树中同步叶子共 18 项：13 个 `orientation.*`、
`selection.marquee/lasso/paint`、`selection.clear/select_all`。
前三个选择工具通过 `wm.tool_set_by_id(EXEC_DEFAULT)` 切换持久工具；
Clear/Select All 通过原生 object/mesh `select_all(EXEC_DEFAULT, True)` 保留原生撤销。

## 旧候选 RED

入口：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender-radio-preview.exe`。
SHA256：`6C8C1A064E360B795F24EF1A95B989FD7088DDC9E3906CBEF06866879DD490BE`。

执行时仅加入持键重复手势测试，几何坐标仍使用旧布局的 side `+32`。
先验证 Q/W/E/R 普通点按通过，然后只发一次 Q PRESS：

1. 第一次 LMB 划选 Lasso，实际工具成为 `builtin.select_lasso`。
2. 不发 Q RELEASE，也不再发 Q PRESS；移动到另一个原点再次按住 LMB。
3. 划选 Paint，实际工具没有成为 `builtin.select_circle`，断言失败。

退出码 1，原文：

```text
AssertionError: Q second LMB stroke under one held key did not reopen at the new origin
```

日志：`D:/source/AxisMeld-build/rearm-old-red-tools.log`。
截图：`D:/source/AxisMeld-build/rearm-old-red-artifacts/rearm-select-second-stroke.png`。
已打开截图核对：第二次按住 LMB 时没有工具热盒，工具仍是 Lasso。
失败依据是实际工具状态和原生 GUI 截图，未增加生产测试钩子。

## 新候选 GREEN

入口：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe`。
最终 SHA256：`E8674E2E653C0819C469CC8FAA91AE870B28FE16EC950F29B5D526812391AB49`。

```text
python tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2b-ui-test-install/blender-opacity-check.exe --suite tools --artifacts D:/source/AxisMeld-build/gesture-tools-final-artifacts
```

`tests/python/axismeld_tool_hotbox_events.py` 已更新到本轮 side `+8` 的显示布局，
方向、实际工具与方向槽预期保持不变。此坐标更新在旧 RED 留证后进行。
测试使用候选安装目录自身的 Python 资源、独立 factory 配置和临时目录，未覆盖原安装入口。

最终结果：runner 退出 0，日志包含 `AXISMELD_TOOL_HOTBOX_EVENTS_PASS`，进程约 72.3 秒后正常退出。
日志：`D:/source/AxisMeld-build/gesture-tools-final-green.log`。
只有已知 `libpng warning: iCCP: cHRM chunk does not match sRGB`，没有 Python Traceback。

此前首版候选 `7EC182C1DCF31265E81C975EEC7DC41230A9C28B9D7718CF7608F9F004EB06B6`
也通过约 70.5 秒的完整 tools 运行，日志保留在 `D:/source/AxisMeld-build/gesture-tools-green.log`。
随后复审修复隐藏祖先返回框与当前子环外延的交界，增加下述 W/R 三级真实事件后重新构建并完整重跑；
最终通过状态以上面的 E867 开头哈希和 `final-green` 日志为准。

| 覆盖 | 实际断言 |
|---|---|
| Q/W/E/R 一次持键五次 LMB | 连续两个不同动作、空中心取消、灰色 Symmetry 叶子、再次有效提交；全程只发一次工具键 PRESS |
| 新原点与隐藏等待 | 第二次 LMB 原点改变仍命中正确工具/方向；每次释放后只保留一个 armed 热盒 modal、没有 release guard；无按键移动不提交 |
| 最终释放与取消 | 最终工具键 RELEASE 完全清理；重复打开后工具键先松、Esc 取消；Esc 在隐藏等待阶段也清理 |
| 失焦后丢失旧 release | 隐藏等待和第二次显示均测试 WINDOW_DEACTIVATE；不补发旧键/鼠标 RELEASE，先用新的 E 重新建立会话 |
| 工具键交接 | 已提交 W stroke 后按 E，两种旧/新 trigger 释放顺序；旧鼠标仍拥有时继续阻挡新会话 |
| 根工具环外延 | Q/W/E/R 三个真实叶子先进入可见按钮，再沿同一显示行越过外边缘 64 px 后释放；保持预期工具/方向；外划后返回原点取消 |
| 隐藏祖先中心 | W/R 经 Axis → Custom Axis，移动到隐藏根环 24×24 返回框的角点；该点距真实起点大于 12 px 且不在任何当前子环可见按钮内；随后当前 Custom Axis 的 View 实际提交成功 |
| Space 工具环 | 复用真实 Space → Modify → Tool Settings → Move Tool 路径；Normal 外边缘释放实际提交；外划后返回 Modify 的真实 LMB PRESS 原点取消 |
| Edit 与原生撤销 | Clear Selection 后保持 Q，第二次 LMB 切 Lasso；最终松 Q 后一次 Undo 恢复选择；Edit 的 Q/W 重复手势 |
| 四视图与改键 | 四视图 W 重复手势；用户改键 F13 同样重复，禁用绑定后不建立会话 |
| 保留回归 | 普通点按、自动重复模拟、原点保护、二/三级子环返回、普通菜单隔离、Alt 导航、场景/区域改变取消、现有工具叶子和独立方向槽 |

外延用例按可见按钮所在行设置终点，不用固定 45 度射线代替不同宽度按钮的实际命中。
Space 原点用例明确断言 LMB 在 Modify 的按下位置与 Space 按下位置相距超过 12 px，
避免把键盘起点或子环中心误当作当前鼠标 stroke 的原点。
隐藏祖先用例运行时筛选根中心四个 `(±10, ±10)` 角点，验证距离和子环矩形前提后才使用，
并以最终方向槽 `VIEW` 判断当前三级子环是否仍在；日志独立记录
`PASS hidden ancestor corners keep current third-level W/R ring`。

## 视觉核对与验证边界

最终截图目录：`D:/source/AxisMeld-build/gesture-tools-final-artifacts`；
首版截图保留在 `D:/source/AxisMeld-build/gesture-tools-artifacts`。
已直接查看首版 Q/W 的 `rearm-*-second-stroke.png` 与 `rearm-*-waiting.png`，
确认第二次 LMB 显示在新原点、松鼠标后热盒隐藏，Q 为 Paint，W 方向为 Global。
也已查看 `space-tool-outer.png` 与 `space-tool-origin-cancel.png`；
工具环保持紧凑五行，Space 背景存在，外部候选可显示。
最终已直接查看 `hidden-root-corner-move.png` 与 `hidden-root-corner-scale.png`，
经过隐藏祖先角点后仍显示 Custom Axis 的八项子环，没有退回 Axis 或根工具环。

事件走可视 GUI 进程的原生 modal 路由，使用 `window.event_simulate` 合成输入；
这不等于实体键鼠速度、OS 自动重复标记、多显示器 DPI 或真实跨窗口失焦的人工验收。
本报告不把该 tools 组替代其他 suite、原生测试或发布入口的独立验证。
