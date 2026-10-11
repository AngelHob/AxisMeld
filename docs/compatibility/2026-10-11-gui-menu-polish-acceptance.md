# 菜单快捷键、导航与窄窗说明验收

日期：2026-10-11。源码起点 `74615d357c9a0e5c27c07b5cb74d95fea2a16a0d`。设计见 [本批 GUI 修复](../development/2026-10-11-gui-menu-polish.md)。本批不增加算法，不改变热盒或菜单结构。

## 已执行验证

| 范围 | 本轮结果 |
| --- | --- |
| 纯 Python | menubar_ui 21、menubar_runtime 14、menubar_actions 10、menubar_native 14、workspace_menu_catalog 14、native_preview_audit 8，共 81 项通过 |
| 原生构建与 CTest | Release 重新构建；editor_hotbox_hotbox_model 24、axismeld_hotbox_state 18，共 42 项通过；安装内 145 项受管脚本与源码一致 |
| 快捷键实际 GUI | 100%/150% 下默认、重绑、禁用、删除绑定，24 次完整文字/空白验证通过；8 次正文执行保持来源视窗，独立灰齿轮不执行正文；从 Outliner 打开时也使用已捕获的 3D 来源 |
| 导航与 Options 实际 GUI | 34 个上下/首尾/循环及对照用例通过，含普通灰正文、可用 Options、纯图标末格、两类 Skin 灰齿轮与原生 Blender；真实 Normalize Options 可键盘打开，取消后权重/选择不变；灰齿轮原因提示截图可见 |
| 布局回归 | menu-options-geometry 在 100%/150% 下通过，右侧齿轮位置、正文区域、灰状态与独立命中保持；当前 modeling-viewport 的实际菜单、上下文保护、原生入口与 Undo 回归通过 |
| 长说明实际 GUI | 960×720 的 100%/150% 与 1920 宽窗口通过；每组验证 Duplicate Special、两条 History 长说明及一条短说明，逐行核对完整文字；默认主题截图确认说明避开菜单 |

候选 exe SHA256：`d8af26aff3b5ae2099ea2c3e3e8d4242b3cbc1354bdcd8de47a6876bee1f400a`。构建配置沿用 Blender 5.3 Alpha / MSVC 14.51.36231；WITH_BUILDINFO=OFF、WITH_CYCLES_NATIVE_ONLY=ON，未启用可选 GPU 预编译内核或 OptiX。

## 失败复现与边界

- 旧候选真实菜单有 Move 正文而没有 W 提示；旧菜单 Home→Down→Enter 停在灰齿轮，未执行第二行；旧 960 像素宽窗口的说明文字延伸至 x=959，完整句尾不可见。新候选分别通过同类实际事件检查。
- 测试中的全局 Edit 与热盒 Edit 同名、Scale Tool 子字符串、悬停字色及背景均需正确区分；修正定位后保持完整字形匹配门槛。测试定位错误不计为产品缺陷或修复成果。
- 历史 `menubar-actions` 仍查找已取消的应用顶栏 Create，当前布局不适用；旧、新候选均在同处失败。保留失败记录，当前 Modeling 视窗入口回归通过，不恢复旧顶栏来满足历史脚本。
- 如果窗口高度极低，已没有容纳完整说明的空白带，当前保留底部全文，可能覆盖部分菜单；本批没有新增复杂排布或滚动。本轮已实测窗口范围见上表。
- 本轮自动检查及截图观察不代替人工手感、多机器、任意插件或所有显示缩放验收。其他批次的测试数量不能作为本轮复测数量。

## 重跑入口

用独立配置安装新候选，串行运行 `tests/python/axismeld_hotbox_ui_runner.py --blender <candidate>/blender.exe --suite <suite> --artifacts <audit>`。本批 suite 为 `menu-shortcuts`、`menu-options-navigation`、`menu-options-access`、`menu-options-geometry`、`hotbox-reasons`，当前视窗回归为 `modeling-viewport`。

长说明通过环境变量 `AXISMELD_TEST_WINDOW_SIZE=960x720` 与 `AXISMELD_REASON_SCALE=1.0` 或 `1.5` 指定窗口及 UI 缩放；再用 `1920x1017`/`1.0` 检查宽窗口。矩阵以实际窗口报告为准，不假设操作系统总能按请求创建任意大小。

## 人工与发布

新增 GU-17～GU-19 三项待人工测试。目录 336 项，当前 324、历史 12；47 项保留历史已测试记录，当前初始待测 277。既有编号及人工结果不变。

发布尚待本批最终打包与公开下载核验；计划独立标签 `axismeld-2026.10.11-gui-menu-preview`，不覆盖旧 input preview。最终发布状态将在此补记。
