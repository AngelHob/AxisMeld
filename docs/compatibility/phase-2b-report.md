# Phase 2B 本地验证报告

最终验证日期：2026-09-10。结论：设置持久化、可见 Recent、真实菜单和既有输入回归均通过自动化；
B12 人工手感待验收，跨新窗口残留释放仍是独立已知失败，因此未批准发布。

## 交付身份

| 项目 | 核对值 |
|---|---|
| 原始 Phase 2B/native 实现提交 | `ef4f0b56709997da3a7faf969c2a234a9f31fabc` (`Add persistent hotbox settings and recent menu`) |
| Python 严格引用校验修复 | `437861476926a4ca4abf990c33db85326d8c05f8` (`Reject unresolved hotbox setting menu references`) |
| 当前 native/Python 最终审查修复 | `3273b0a39e2f6afe149c37c6ad4ef08283f2ea23` (`Fix center-only hotbox area mapping and empty Recent state`) |
| Blender 上游基点 | `18d84097b4f859582afdec57eece2ae880371adc` |
| 新测试版 | `D:/source/AxisMeld-build/phase2b-test-install/blender.exe` |
| 新 exe SHA-256 | `0A119F484EFAAC09156470810795BEC9A6EC7DBE34AF4CFA06529D464789A6E9` |
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
| Recent | `center.recent` 始终是合法映射菜单身份；空历史禁用并说明原因，有历史启用；显示本会话最近 10 个成功、可重放叶命令，点击时重新检查可用性 |
| Center Zone Only | 整片非菜单 WINDOW 内容区使用各鼠标键的中央映射；实际按下点为划选原点，菜单/标题/禁用项/分隔符/滚动矩形优先；rows/zones 空白行为不变 |
| 产品 UI | rows/zones/center、透明度、三行显隐及三键映射在预设偏好和 Controls 可见；当前原生快照继续安全持有，下一次 invoke 读取新 generation |
| 未实现边界 | File/窗口、绝大多数 Modeling、UV、Maya Center Zone RMB Popups 完整语义均未开放；19 项命令 allowlist 未扩大 |

## 最终验证

日志根目录：`D:/source/AxisMeld-build/phase2b-validation-20260909/`。所有 Blender 测试均使用
`phase2b-test-install/blender.exe` 和私有 `BLENDER_USER_CONFIG/TEMP/TMP/TMPDIR`；GUI 串行执行。

| 门禁 | 命令摘要 | 结果/证据 |
|---|---|---|
| 构建/独立安装 | `cmake --build ... --target blender --parallel 8`；`cmake --install ... --prefix .../phase2b-test-install` | exit 0；`finalfix-build.log`、`finalfix-install.log` |
| Python pure | `C:/Python314/python.exe -m unittest discover -s tests/python -p axismeld_hotbox_*_test.py -v` | 26/26：`finalfix-green-pure.log` |
| 输入 pure | `C:/Python314/python.exe tests/python/axismeld_input_test.py` | 14/14；`finalfix-input.log` |
| native 五套 | `ctest ... -R ^(axismeld_(hotbox_menu\|hotbox_state\|identity\|transform_axis)\|editor_hotbox_hotbox_model)$` | 5/5 targets；`finalfix-native-five.log` |
| 安装态输入 | staged exe `-b --factory-startup --python-exit-code 1 --python tests/python/axismeld_input_blender.py` | 11/11；`finalfix-installed-input.log` |
| 安装态 profiles | hotbox runner `--suite profiles` | 新 stage PASS；`finalfix-profiles.log` |
| CLI/portable（历史） | `axismeld_cli_identity.py`、`axismeld_portable_paths.py --blender <原2B-stage>` | 原实现两项 exit 0，未作为新二进制复跑证据；`task5-final-cli.log`、`task5-final-portable.log` |
| 完整菜单 GUI | hotbox runner `--suite menus` | 新 stage PASS；新增空白七方向/三键映射/菜单优先及 rows/zones 隔离；既有 Controls/Recent、缩放/四角/小视口继续通过；`finalfix-green-menus.log` |
| 旧 hotbox GUI | hotbox runner 默认 `hotbox` | PASS；`finalfix-hotbox.log` |
| 同窗口 release | hotbox runner `--suite release` | PASS；`finalfix-release.log` |
| 操纵器 | `axismeld_manipulator_ui_runner.py --blender <new-stage>` | PASS；`finalfix-manipulator.log` |
| 导航 | `axismeld_navigation_ui_runner.py --blender <new-stage>` | 43 条 PASS；`finalfix-navigation43.log` |
| 跨窗口诊断 | hotbox runner `--suite release-cross-window` | 预期 exit 1：`new file window: captured residual release reached child`；不计通过；`task5-final-release-cross-window-known-fail.log` |

历史验收已实际查看 `task5-final-menus-artifacts-with-lists/` 中的 Controls、Recent、1x 真实角点和 2x
marking 截图；菜单文字可读，Controls 长列表未越出窗口，Recent 顺序可见，角点分离组无重复，
2x 标记区未与右侧原生面板重叠。共保存 29 张最终菜单截图。
本次新二进制截图位于 `finalfix-green-menus-artifacts/`，已查看新增
`menus-center-blank-mapped-shading.png`：center 样式显示中央按钮与可读的 Wireframe/Solid 下拉。

## RED/GREEN 与非 pristine 输出

- 文件层 RED：pure 导入缺少 `load_hotbox_profiles/save_hotbox_user`；旧 stage 安装态断言不能解析 hotbox 文件层。
- native RED：重建 parser 测试后二进制明确拒绝新增 `center.RIGHTMOUSE` setting；实现后 model 6/6。
- 会话语义 RED：普通 reload 丢失 session、无效 session 覆盖旧有效值；实现后两项通过。
- 审查修复 RED：从当前 snapshot 树移除已注册 `pane.shading`、保留 Controls setting option 时，Python 错误接受；`task5-fix1-red-python-unresolved-setting.log` 为 0/1。完整遍历后校验 center setting 引用属于当前 `menu_ids`，定点 GREEN 1/1、pure 25/25。该 Python 修复来自 `43786147692`，原 native 实现与 exe 不变。
- 最终审查 RED：`finalfix-red-menus.log` 真实 GUI 在空白 RMB `view.left` 断言失败；`finalfix-red-recent.log` 的空历史断言失败（`True is not false`）。最小修复后上述新 stage menus 与 pure 26/26 通过；disabled File 取消夹具按独立七项公共行修正，旧四向文档已明确历史身份。
- 首轮旧 hotbox 在 Preferences draw 暴露 `NameError: bpy`；补齐导入并重新安装后，完整 hotbox 无 traceback 通过。
- 预期输出包括损坏 user 文件拒绝覆盖警告、测试夹具的无效 JSON/小视口/不支持上下文警告、
  addon 冲突夹具警告和既有 libpng iCCP 警告；因此不声称输出 pristine，也不声称已解决卡顿。

人工步骤和未接入目录见 [Phase 2B 人工验收表](phase-2b-manual-test.md)。
