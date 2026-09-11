# Blender 开发接续与热盒修正

状态：已实现、构建并更新原测试入口。仅本地交付，未推送远程。

## 接续内容

原任务「检索 Blender Maya 操作分支」最后两次失败发生在 Codex 远程对话压缩阶段：`Error running remote compact task: stream disconnected before completion`。这是本次已核实的中断位置，不能据此宣称网络问题已经修好。

从原任务最后用户消息恢复的未完成要求：Left View 外侧误选 Top View；QWER 热盒布局对齐所附 Maya 截图。接续基线为 `cfa6824494b`，当时工作区干净。最新用户要求优先于历史“所有父热盒保留”“工具同组等宽”等旧约定。

## 改动

- Views 按可见矩形处理按钮附近命中；外侧水平/垂直划动延续对应行/列，避免突然落入另一固定扇区。
- 中心使用真实布局空白区；真实按下点的取消和短划、边角菜单移入后的空白通道仍受保护。可见按钮与原生 Style 菜单优先。
- 窄视口不显示 Camera 时仍保留不可执行的 NE 命中占位，不填入其他视角，也不会反向命中 Left。
- QWER 按内容定宽，最小84px、按钮高24px、行隙8px、斜行内收16px；子热盒入口有原生箭头，文字留白和对齐避免箭头挤压。
- 保留各工具内容、Global/Local 命名及未实现项；没有新增 UV、对称或变换算法。布局对照不等于新增 Maya 全部功能，人工快速划选手感仍待用户试用。

## 验证

| 验证 | 结果与证据（日志位于 D:/source/AxisMeld-build） |
|---|---|
| 原误触 | `reference-hit-red.log` 对旧安装版失败；新增 Left/Back/Bottom 外侧与短划用例随后通过 |
| 原生 | 5个原生CTest目标通过，其中47项布局测试；`reference-native-ctest.log`、`reference-native-final.log` |
| Python | tool_hotbox 6、catalog 20、runtime 7，共33项通过 |
| 完整视图事件 | `reference-final-menus.log` 通过四角、1/1.25/1.5/2倍缩放、取消、原生设置及不支持视口；其后仅增加紧凑空NE占位及QWER文字留白 |
| 2倍四视图 | `reference-final-quad.log` 通过七视角、隐藏Camera位置与右外沿不执行、分页 |
| 最终QWER | `reference-delivery-tools.log` 通过工具派发、三级返回、Space入口、撤销、焦点变化、单/四视图及改键；四张截图已目视核对 |
| 原安装入口 | `reference-installed-hotbox.log`、`reference-installed-native-style.log`、`reference-installed-release.log` 均有PASS且退出0；release覆盖同窗口范围 |
| 独立只读复核 | 发现并修复紧凑NE空方向填满问题；最后复核未发现新的重要问题。审查不替代上述运行证据 |

扩大CTest筛选时还触发了三个指向旧 `D:/source/AxisMeld-build/install/blender.exe` 的应用级失败（input_blender、manipulator_events、hotbox_events），见 `reference-ctest-final.log`。该旧安装路径未在本次更新；不宣称全部CTest通过。实际交付入口按上表独立验证。既有PNG ICC警告仍存在。

## 使用与回退

测试入口：[blender.exe](D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe)。

新exe SHA256：`5760561C92F648A47BD58FB87A02D2E84C9F10D83045398918AE6F4B2EE2CE34`，与编译产物一致。

更新前exe保存在 `D:/source/AxisMeld-build/reference-20260912-before-blender.exe`，SHA256为 `6ED27572F02C5D4D28BA8885D33A556F93BB0D107C1314DFEA7CB31EB4E9E6C1`。需要回退时，退出程序后将此文件复制回上述测试入口。

安装前未发现运行中的用户Blender；未终止用户进程。只替换exe，6个portable个人文件前后哈希一致，见 `reference-install-before.json` 和 `reference-install-verification.json`。

实现设计及原图：`docs/design/2026-09-12-marking-hit-reference.md`、`docs/design/references/2026-09-11-user-tool-hotbox.png`。

建议试用：从Left View向左拉出按钮再松开；近中心短划；四个窗口角落；QWER进入Axis/Select后返回；窄视口右上空方向不执行。
