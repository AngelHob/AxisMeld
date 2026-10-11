# GUI 改键与灰项提示验收

日期：2026-10-11。源码起点 `098ae882c39`。设计见 [GUI 输入修整](../development/2026-10-11-gui-input-polish.md)。本轮只修正三项现有 GUI 行为，不增加算法、不调整热盒几何。旧 GUI preview 不含本轮修复。

## 已执行验证

| 范围 | 本轮实际结果 |
| --- | --- |
| 纯 Python | native_rigging 17、rigging_catalog 5、rigging_ui 7、menubar_ui 19、menubar_runtime 12、tool_hotbox 6、tool_content 6、native_preview_audit 8，共 80 项通过 |
| 原生构建与 CTest | Release 重编 blender；editor_hotbox_hotbox_model 24、axismeld_hotbox_state 18，共 42 项通过 |
| 安装内真实 RNA | Keymap 9 项（遍历 635 个语义名称）；Rigging 7 组、24 次灰项绘制/取消执行；均使用安装内模块，无源码注入 |
| 实际 GUI | tools-modifiers、tools、context-entries、history-hotbox 四组通过；Preferences 四种搜索/展开场景通过；Rigging 默认 Cube 的 Edit Bones 灰项提示完整可见，点击/取消不改模式、对象、选择和位置 |
| 配置与资源 | profiles 后台回归通过；新安装 145 个受管脚本与源码逐字节一致，包含本轮修改的 rna_keymap_ui |
| 独立审查 | 三项修复与整批集成无可操作缺陷；Rigging 新旧门禁 68,544 组模拟上下文及五种实际 RNA 上下文核对一致 |

新候选 exe SHA256：`c78b71f930048ae286fed40c6d15c3c3c18de5ad7a48b82a2bbc2e186bed5c65`。构建配置沿用 Blender 5.3 Alpha / MSVC 14.51.36231；WITH_BUILDINFO=OFF、WITH_CYCLES_NATIVE_ONLY=ON，未启用可选 GPU 预编译内核或 OptiX。

## 失败复现与测试边界

- 旧候选默认 QWER/重复 W 正常，但 Ctrl+F20 在首次 timer/motion 后仅余 release guard；新候选保持工具会话并完成重复 Local/World 划选、释放/失焦取消。
- Keymap 原生产绘制在语义名称/搜索断言失败；修复后通过。原生展开事件编辑器依赖真实窗口，后台调用 `_wm_capabilities()` 会崩溃，因此展开验证在实际 Preferences GUI 执行，不把无窗口探针当成产品 GUI 崩溃。
- Rigging 原灰项只有 label，原因与安全按钮断言失败；修复后通过。`event_simulate` 的鼠标 xy/prev_xy 相同，首次悬停未重新启用 native tooltip；增加同一行内第二次移动后实际截图已确认完整原因，不修改产品提示计时逻辑。
- 这些自动化及维护者截图观察不代替实体鼠标手感、不同机器/缩放、第三方插件和人工测试。上一轮 354/139/18 组数据是历史结果，本轮未声称重跑其全部。

## 重跑入口

使用隔离配置，按 [构建交付](../BUILD_AND_DELIVERY.md) 安装全新候选。运行 `tests/python/axismeld_hotbox_ui_runner.py --blender <candidate>/blender.exe --suite tools-modifiers --artifacts <audit>/tools-modifiers`，其余套件依次为 tools、context-entries、history-hotbox、profiles；GUI 套件串行执行。

Keymap RNA 使用 `--background --factory-startup --python-exit-code 1 --python tests/python/axismeld_keymap_ui_blender.py`。GUI 使用 `--factory-startup --enable-event-simulate --python-exit-code 1 --python tests/python/axismeld_keymap_ui_events.py`，设置独立 BLENDER_USER_CONFIG 和 AXISMELD_TEST_ARTIFACTS；不要设置 AXISMELD_KEYMAP_UI_SOURCE。

## 人工与交付

GU-14 带修饰键改键、GU-15 首选项名称/搜索、GU-16 灰项原因，均待人工；旧项目及状态保留。目录共 333 项，其中当前 321、历史 12；47 项仅历史已测，当前初始待测 274。网页本浏览器勾选和 GitHub Issue 提交保持原机制。

已发布完整 [GUI input preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-input-preview)，源码/native `3a614cad8a1bd4df8d05049f6f051d47bfef62e3`。ZIP 297,074,164 字节；SHA256 `d11d5973a473a7a9b4f307c4959e284fd8d632850014d6a0abefd56c05214c5e`。6,498 个文件与 145 项资源通过干净解压审计、工厂/portable 启动及改键 GUI 复测；匿名重下载后再次核验 ZIP、解压和启动。公开目录更新为 333 项、新增 3 项，网站 12 项浏览器检查通过。[发布快照](2026-10-11-gui-input-preview-snapshot.json)保留完整指纹；旧版未覆盖。
