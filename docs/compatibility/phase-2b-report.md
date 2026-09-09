# Phase 2B 本地验证报告

日期：2026-09-09。结论：设置持久化、可见 Recent、真实菜单和既有输入回归均通过自动化；
B12 人工手感待验收，跨新窗口残留释放仍是独立已知失败，因此未批准发布。

## 交付身份

| 项目 | 核对值 |
|---|---|
| 实现提交 | `ef4f0b56709997da3a7faf969c2a234a9f31fabc` (`Add persistent hotbox settings and recent menu`) |
| Blender 上游基点 | `18d84097b4f859582afdec57eece2ae880371adc` |
| 新测试版 | `D:/source/AxisMeld-build/phase2b-test-install/blender.exe` |
| 新 exe SHA-256 | `7A71A11B98B849B9FCFABFDC1CB33B9C39FF79AF694C759DE1C57C2E1A2402FC` |
| 构建目录 exe SHA-256 | 同上；安装后逐字节一致 |
| 旧 Phase 2A SHA-256 | `7A606A5B96723A75129DD9124657165097BCBB56389FB7ADE89E5E3BEB92050F`，未覆盖 |
| 受保护 normal install SHA-256 | `72DB65EDE53C3E5C724D5ACF33586FF04EEC9C123B5004AAE9D3D365DF481408`，未覆盖 |

构建关闭了 build info，因此运行时 `bpy.app.build_hash/build_branch` 是 `Unknown`；这不替代上表
Git/文件哈希证据。测试版仍是 opt-in：启动新 exe 后若预设未激活，必须在
**Edit → Preferences → Keymap** 选择 **AxisMeld Maya 2026**。

## 本轮实际变化

| 能力 | 实际结果 |
|---|---|
| 设置分层 | baseline → `hotbox_studio.json` → `hotbox_user.json` → session；逐层严格校验与原子回退 |
| 用户写入 | Preferences 与 Hotbox Controls 共用一条更新路径；只写相对 studio 的 settings 差异，临时文件复验后 replace；损坏 user 文件拒绝覆盖 |
| 会话边界 | 普通 reload 保留会话层；显式空 settings 清除；无效 session 保留旧有效层并诊断；写单个用户设置不会泄漏其他 session 字段 |
| 中心三键 | LMB/MMB/RMB 可映射任意已注册 menu ID 或禁用；Python/native 两端均拒绝未知 setting、未知值和未解析 menu ID |
| Recent | `center.recent` 始终是菜单身份；显示本会话最近 10 个成功、可重放叶命令，点击时重新检查可用性 |
| 产品 UI | rows/zones/center、透明度、三行显隐及三键映射在预设偏好和 Controls 可见；当前原生快照继续安全持有，下一次 invoke 读取新 generation |
| 未实现边界 | File/窗口、绝大多数 Modeling、UV、Maya Center Zone RMB Popups 完整语义均未开放；19 项命令 allowlist 未扩大 |

## 最终验证

日志根目录：`D:/source/AxisMeld-build/phase2b-validation-20260909/`。所有 Blender 测试均使用
`phase2b-test-install/blender.exe` 和私有 `BLENDER_USER_CONFIG/TEMP/TMP/TMPDIR`；GUI 串行执行。

| 门禁 | 命令摘要 | 结果/证据 |
|---|---|---|
| 构建/独立安装 | `cmake --build ... --target blender <5 native targets> --parallel 8`；`cmake --install ... --prefix .../phase2b-test-install` | exit 0；`task5-final-build.log`、`task5-postcommit-build.log`、`task5-postcommit-install.log` |
| Python pure | `C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_hotbox_*_test.py -v` | 24/24；`task5-final-pure-after-fixes.log` |
| 输入 pure | `C:/Python314/python.exe tests/python/axismeld_input_test.py` | 14/14；`task5-final-input.log` |
| native 五套 | `ctest ... -R ^(axismeld_(hotbox_menu\|hotbox_state\|identity\|transform_axis)\|editor_hotbox_hotbox_model)$` | 5/5 targets；`task5-final-native-five.log` |
| 安装态输入 | staged exe `-b --factory-startup --python-exit-code 1 --python tests/python/axismeld_input_blender.py` | 11/11；`task5-final-installed-input.log` |
| 安装态 profiles | hotbox runner `--suite profiles` | PASS；`task5-final-profiles-after-drawfix.log` |
| CLI/portable | `axismeld_cli_identity.py`、`axismeld_portable_paths.py --blender <new-stage>` | 两项 exit 0；`task5-final-cli.log`、`task5-final-portable.log` |
| 完整菜单 GUI | hotbox runner `--suite menus` | PASS；真实 Controls 写 delta、Recent 点击重放、缩放/四角/小视口；`task5-final-menus-with-list-screenshots.log` |
| 旧 hotbox GUI | hotbox runner 默认 `hotbox` | PASS；`task5-final-hotbox-drawfix.log` |
| 同窗口 release | hotbox runner `--suite release` | PASS；`task5-final-release-sessionfix.log` |
| 操纵器 | `axismeld_manipulator_ui_runner.py --blender <new-stage>` | PASS；`task5-final-manipulator.log` |
| 导航 | `axismeld_navigation_ui_runner.py --blender <new-stage>` | 43 条 PASS；`task5-final-navigation43.log` |
| 跨窗口诊断 | hotbox runner `--suite release-cross-window` | 预期 exit 1：`new file window: captured residual release reached child`；不计通过；`task5-final-release-cross-window-known-fail.log` |

已实际查看 `task5-final-menus-artifacts-with-lists/` 中的 Controls、Recent、1x 真实角点和 2x
marking 截图；菜单文字可读，Controls 长列表未越出窗口，Recent 顺序可见，角点分离组无重复，
2x 标记区未与右侧原生面板重叠。共保存 29 张最终菜单截图。

## RED/GREEN 与非 pristine 输出

- 文件层 RED：pure 导入缺少 `load_hotbox_profiles/save_hotbox_user`；旧 stage 安装态断言不能解析 hotbox 文件层。
- native RED：重建 parser 测试后二进制明确拒绝新增 `center.RIGHTMOUSE` setting；实现后 model 6/6。
- 会话语义 RED：普通 reload 丢失 session、无效 session 覆盖旧有效值；实现后两项通过。
- 首轮旧 hotbox 在 Preferences draw 暴露 `NameError: bpy`；补齐导入并重新安装后，完整 hotbox 无 traceback 通过。
- 预期输出包括损坏 user 文件拒绝覆盖警告、测试夹具的无效 JSON/小视口/不支持上下文警告、
  addon 冲突夹具警告和既有 libpng iCCP 警告；因此不声称输出 pristine，也不声称已解决卡顿。

人工步骤和未接入目录见 [Phase 2B 人工验收表](phase-2b-manual-test.md)。
