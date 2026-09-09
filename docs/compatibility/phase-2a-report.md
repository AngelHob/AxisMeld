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
| 安装态输入 | `<staged-exe> -b --factory-startup --python-exit-code 1 --python tests/python/axismeld_input_blender.py` | 10/10 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/installed-input.log` |
| 操纵器 GUI | `C:/Python314/python.exe tests/python/axismeld_manipulator_ui_runner.py --blender <staged-exe>` | 通过 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/manipulator-gui.log` |
| 热盒 GUI | `C:/Python314/python.exe tests/python/axismeld_hotbox_ui_runner.py --blender <staged-exe>` | 通过且无 Python traceback | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/hotbox-gui.log` |
| 安装脚本来源 | `<staged-exe> -b --factory-startup --python-exit-code 1 --python-expr <path assertions>` | 模块、预设、exe 均来自暂存目录 | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/installed-script-identity.log` |
| exe 哈希 | `Get-FileHash <built-exe>,<staged-exe> -Algorithm SHA256` | 两者均为 `35156F750077F5F1C884D81D0B977D2FC1236D9FFB47C2DD7E740F716A865124` | `D:/source/AxisMeld-build/phase2a-task3-validation-20260909/exe-hashes.log` |

这里的 `<staged-exe>` 均为上面的独立可运行文件。持久日志独立于最终会清理的 SDD scratch。
配置期 whole CTest 仍指向旧的 normal install，因此没有拿它替代上述显式暂存测试。

私有 GUI runner 为子进程设置独占 `BLENDER_USER_CONFIG`、`TEMP`、`TMP` 和 `TMPDIR`；
不会向用户正在运行的正常安装注入事件或复制偏好。已知预期输出包括 PNG 色彩 metadata
警告、刻意制造的 addon 冲突报告和 unsupported-view 警告；验收不会把这些描述成无警告。

## 仍需人工确认

见 [Phase 2A 人工验收表](phase-2a-manual-test.md)。尤其不能由自动化推断视觉平滑、
物理重复键边界、实际鼠标手感或完整 Maya 对等。
