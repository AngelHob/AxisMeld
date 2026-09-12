# M2a 活动网格组件右键验收

状态：已实现、构建并更新原测试安装，人工待测。前一交付基线为 `12eec78b2ac`；仅本地交付。

## 功能边界

本批接入已选可编辑活动网格的组件 marking 热盒：无修饰右键按住并拖向上 Edge、左 Vertex、下 Face、右上 Object Mode，松右键提交。Object Mode 为幂等命令，中心、Esc 和失焦取消。UV、Vertex Face、Multi Component 为不可执行占位。

入口依据活动网格和当前选择上下文，包含鼠标位于空白或另一个未选对象上的情形；不实现鼠标下换目标。多选时模式切换沿用 Blender 原生多对象编辑，不强行取消其他选择。非网格、无选择、非建模模式和其他编辑器保留原生右键。M2 全量上下文、Shift/Ctrl 建模热盒及 M3 仍待后续开发。

## 待人工测试

集中清单：[2026-09-12 人工测试清单](2026-09-12-manual-test-ledger.md)。目前 27 项均待测；自动化不替代实体鼠标手感、OS 按键重复、跨窗口、真实 DPI 或用户个人配置的实际使用确认。

## 验证记录

以下日志均位于 `D:/source/AxisMeld-build`，最终安装 exe SHA256 为 `3D9C8BC0D8D2F95473160B295CC7E2F61255DE9041B28B2BB85FA37C14F2461A`。

| 验证 | 最终结果与证据 |
|---|---|
| Python | 主任务独立运行全部 AxisMeld 单元测试，57项通过；`m2a-main-python.log` |
| Native | 5个针对性 CTest 目标全部通过，含47项布局测试；`m2a-main-native.log` |
| 安装态 components | 四方向、幂等模式、连续手势、中心/Esc/占位、真实原生菜单回退、F13改绑/禁用、失焦无旧release后重开、带修饰release清理、后续左键选择通过；`m2a-installed-components.log` |
| 安装态 tools | QWER、普通子菜单/返回、改键、失焦、区域缩放、单/四视图等回归通过；`m2a-installed-tools.log` |
| 安装态 hotbox | Space/视图、场景保存重开、配置页等回归通过；`m2a-installed-hotbox.log` |
| 安装态 release | 原生派发、异常/取消、子操作拥有、Recent仅成功记录等通过；`m2a-installed-release.log`，仅同窗口范围 |
| 截图 | `m2a-installed-components-artifacts/component-ring.png`；已目视检查同布局候选截图，七个标签完整、方位正确、中心留白 |
| 安装一致性 | exe与候选及构建一致，12个Python资源与源码一致，6份portable文件未变；`m2a-install-verification.json` |
| 独立审查 | 最终无剩余重要问题；先前回退测试假通过风险已改为真实RMB菜单探针 |

开发中保留的失败证据：`m2a-component-red.log`（旧版无 mode.object）、`m2a-model-red.log`（原生快照拒绝该命令）、`m2a-main-python-red.log`/`m2a-main-native-red.log`（目录容量变化）、`m2a-modified-release-red.log`（已释放键残留guard）。Select去除无操作分隔项，保持8个有效入口；最终modified-release在独占串行测试中取得RED/GREEN，先前一次与其他GUI重叠的运行不作为最终证据。

既有PNG ICC警告仍出现；release的负向夹具会产生预期诊断。未宣称完整Blender CTest全部通过；历史旧安装路径限制仍在人工清单中记录。实体跨窗口、DPI、M2a多选使用及Space组件目录手感仍按清单待人工确认。

## 安装与回退

继续使用 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。更新前已备份当前 exe 和 AxisMeld Python 模块到 `D:/source/AxisMeld-build/m2a-20260912-before`，原 exe SHA256 为 `5760561C92F648A47BD58FB87A02D2E84C9F10D83045398918AE6F4B2EE2CE34`。

六份 portable 文件的更新前哈希见 `D:/source/AxisMeld-build/m2a-install-before.json`。本批改动同时涉及 exe 与 Python 资源，回退须恢复两者；不能只换 exe 留下新模块。

更新前再次确认没有运行中的 Blender；没有终止用户进程。回退时先退出 Blender，把备份 `blender.exe` 复制回原入口，备份 `axismeld` 目录内容复制回 `5.3/scripts/modules/axismeld`，备份 `axismeld_operator.py` 复制回 `5.3/scripts/startup/bl_operators/axismeld.py`。本批新增的 `context_hotbox.py` 在旧模块恢复后不再被导入；portable 配置不参与回退。
