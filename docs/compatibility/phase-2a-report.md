# Phase 2A 本地验证报告

状态：Task 3 本地实现完成，等待独立任务审查、全分支审查和用户人工验收；不代表批准集成。

## 已连接的产品路径

- `AxisMeld_Maya_2026` 公共预设默认把 Space 绑定到 `hotbox.open`；专用
  `AxisMeld Hotbox` 映射位于 3D View WINDOW，未修改全局 Frames/Screen 数据。
- 语义 wrapper 将真实键盘 invoke 事件交给原生热盒，并把预设的 0.1–1.0 秒阈值传入一次。
- `view.toggle_quad`、`view.perspective`、`view.side`、`view.front`、`view.top` 是有效语义 ID，
  但公共预设不为它们制造独立键位；schema 1 覆盖可绑定、改键或停用。
- 配置错误只回退当前层；热盒只接受键盘触发。个人原生 keymap 编辑、文件覆盖开关和
  公共默认值继续分离。

## Task 3 验证记录

独立可运行目录：`D:/source/AxisMeld-build/phase2a-test-install/blender.exe`。
它的脚本来源冒烟测试确认 `axismeld` 模块和 `AxisMeld_Maya_2026.py` 均从该目录的
`5.3/scripts` 加载，没有注入源码脚本路径。

| 门禁 | 实际命令摘要 | 结果 | 完整日志 |
|---|---|---|---|
| 隔离暂存 | `cmake --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2a-test-install` | exit 0；仅同步独立目录 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/cmake-install.log` |
| 原生 AxisMeld | `ctest -C Release --test-dir D:/source/AxisMeld-build -R "^axismeld_(hotbox_state\|identity\|transform_axis)$" --output-on-failure` | 3/3 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/native-ctest.log` |
| CLI 身份 | `C:/Python314/python.exe tests/python/axismeld_cli_identity.py --blender <staged-exe>` | exit 0 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/cli-identity.log` |
| portable 路径 | `C:/Python314/python.exe tests/python/axismeld_portable_paths.py --blender <staged-exe>` | exit 0 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/portable-paths.log` |
| 纯配置 | `C:/Python314/python.exe tests/python/axismeld_input_test.py` | 14/14 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/input-profiles.log` |
| 安装态输入 | `<staged-exe> -b --factory-startup --python-exit-code 1 --python tests/python/axismeld_input_blender.py` | 11/11 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/installed-input-fix1-green.log` |
| 操纵器 GUI | `C:/Python314/python.exe tests/python/axismeld_manipulator_ui_runner.py --blender <staged-exe>` | 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/manipulator-gui.log` |
| 热盒 GUI | `C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender <staged-exe>` | 通过且无 Python traceback | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/hotbox-gui.log` |
| 安装脚本来源 | `<staged-exe> -b --factory-startup --python-exit-code 1 --python-expr <path assertions>` | 模块、预设、exe 均来自暂存目录 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/installed-script-identity.log` |
| exe 哈希 | `Get-FileHash <built-exe>,<staged-exe> -Algorithm SHA256` | 两者均为 `35156F750077F5F1C884D81D0B977D2FC1236D9FFB47C2DD7E740F716A865124` | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/exe-hashes.log` |

这里的 `<staged-exe>` 均为上面的独立可运行文件。持久日志独立于最终会清理的 SDD scratch。
配置期 whole CTest 仍指向旧的 normal install，因此没有拿它替代上述显式暂存测试。

Task 3 首轮审查补充了“删除唯一 user hotbox 项后，设置层级不得显示空行”的回归。
修复前的定点 RED 为 11 项中该项失败，日志 `installed-input-fix1-red.log`；改为检查
`keyconfigs.user` 的有效 map 后，安装态 11/11 与偏好 GUI 均通过。补充日志位于同一
持久目录的 `cmake-install-fix1.log`、`installed-input-fix1-green.log`、
`hotbox-gui-fix1-green.log` 和 `exe-hashes-fix1.log`，未覆盖首轮日志。

私有 GUI runner 为子进程设置独占 `BLENDER_USER_CONFIG`、`TEMP`、`TMP` 和 `TMPDIR`；
不会向用户正在运行的正常安装注入事件或复制偏好。已知预期输出包括 PNG 色彩 metadata
警告、刻意制造的 addon 冲突报告和 unsupported-view 警告；验收不会把这些描述成无警告。

## 仍需人工确认

见 [Phase 2A 人工验收表](phase-2a-manual-test.md)。尤其不能由自动化推断视觉平滑、
物理重复键边界、实际鼠标手感或完整 Maya 对等。

## 全分支审查后的最终修复验证（2026-09-09）

最终审查发现：AxisMeld 自身刷新有贡献窗格检查，但原生 zoom/pan 经
`view3d_boxview_sync` 直接进入 `view3d_boxview_clip`，仍会在缺少 TOP/BOTTOM 或
FRONT/BACK 的 BOXCLIP 窗格时写入退化裁剪。检查现已统一放在该原生入口的私有
AxisMeld 谓词中，只在当前预设为 AxisMeld、区域已有缓存且拓扑匹配时保留原有裁剪体积。
完整贡献恢复后继续原生计算；原生联动位置/距离、锁定标记和独立用户裁剪保持既有语义。
缓存仍只持有数值，`clipbb` 继续归 RegionView3D 所有。

取消测试现在先创建有效 SIDE 候选再取消；偏好里的热盒说明改为与触发键无关的文字。
边缘标签裁切和既有 PNG metadata 警告保持原有披露，没有扩大到全局导航、缩放、UV
或完整 Maya 菜单。Phase 1.1 仍需另行批准。

本轮使用同一独立测试安装目录。最新构建和暂存 exe 的 SHA256 均为
`7A606A5B96723A75129DD9124657165097BCBB56389FB7ADE89E5E3BEB92050F`。
上面 Task 3 表中的 `35156F...` 是当时实际测试的历史哈希，未改写为本轮结果。

持久日志目录：`D:/source/AxisMeld-build/phase2a-final-fix-validation-20260909`。

| 门禁 | 结果 | 日志文件 |
|---|---|---|
| 真实导航 RED | 修复前 exit 1；缺 TOP/FRONT × zoom/pan 均导致两个裁剪窗格的六面数值错误，共 8 条失败 | `hotbox-native-red.log` |
| Release 构建 | `cmake --build D:/source/AxisMeld-build --config Release --target blender axismeld_hotbox_state_test --parallel 8`，exit 0 | `build-green.log` |
| 独立暂存 | `cmake --install D:/source/AxisMeld-build --config Release --prefix D:/source/AxisMeld-build/phase2a-test-install`，exit 0 | `install-green.log` |
| 状态机 | `ctest -C Release --test-dir D:/source/AxisMeld-build -R '^axismeld_hotbox_state$' --output-on-failure`；1/1 target、13/13 cases | `state-ctest-green.log`、`state-ctest-detail-green.log` |
| 安装态输入 | `C:/Python314/python.exe <日志目录>/installed-input-runner.py`；私有 TEMP/config，11/11 | `installed-input-green.log` |
| 完整热盒 GUI | `C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender D:/source/AxisMeld-build/phase2a-test-install/blender.exe`；exit 0、终态 PASS 标记 | `hotbox-native-final-green.log` |
| 哈希与日志检查 | raw/stage 哈希一致；最终 GUI/安装输入日志均为 0 traceback、0 空 hotbox keymap 警告 | `exe-hashes.log`、`log-checks.log` |

新增 GUI 检查直接执行原生 `zoom('EXEC_DEFAULT')` 和 `view_pan('INVOKE_DEFAULT')`，
验证实际六个面、原生锁定窗格联动、独立裁剪、恢复贡献后的原生 zoom 数值，以及切到
Industry Compatible 和 AxisMeld 预设内从未接管的原生区域两种隔离情形。RNA 赋值仅用于
还原测试夹具，没有替代这些真实导航调用。既有完整 GUI 覆盖仍通过。

首个修复后 GUI 日志 `hotbox-native-green.log` 中，新增导航用例已通过，但新增原生区域
夹具留下隐藏四视图布局，使后续旧区域用例失败；补上原生退出四视图的夹具清理后，
上表最终完整 GUI 通过。该失败日志保留，没有覆盖或误报为最终成功。

本轮只完成最终审查修复及覆盖验证，仍等待控制器的限定复审和用户人工验收；不代表集成批准。
