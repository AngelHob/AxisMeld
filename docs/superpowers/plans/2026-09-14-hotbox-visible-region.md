# 热盒可见区域修复实施计划

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复窄视口内 Tool Header 遮挡热盒导航行及取消后原地 W/E/R 的上下文问题。

**Architecture:** 从活跃区域取得无遮挡布局矩形；纯布局入口做局部坐标转换并统一变换所有输出命中几何，事件仍使用原 WINDOW 坐标。遮挡变化使会话失效，沿用已有释放清理。

**Tech Stack:** Blender C++/CMake/CTest，Python 隔离 GUI 事件与像素测试。

**Spec:** ../specs/2026-09-14-hotbox-visible-region-design.md

## Global Constraints

- 遵循根 AGENTS.md 和 docs/development/2026-09-14-hotbox-reference-contract.md；不得缩小四视图横向净距。
- 不移动用户鼠标、隐藏工具栏、抢全局焦点或猜测性修改 release guard。
- 原 62 项人工测试保留，新增内容统一记录；自动化成功不写成人工通过。
- 使用当前隔离 worktree 与 D:/source/AxisMeld-build；保留用户配置及当前可回退程序。

## Task 1: 遮挡布局与原地取消恢复

**Files:**
- Modify: source/blender/axismeld/AXM_hotbox_menu.hh and intern/hotbox_menu.cc — 安全布局矩形与输出平移。
- Modify: source/blender/editors/space_view3d/view3d_axismeld_hotbox_internal.hh, view3d_axismeld_hotbox.cc, view3d_axismeld_hotbox_draw.cc — 捕获和核验区域、调用纯布局。
- Test: source/blender/axismeld/tests/hotbox_menu_test.cc — 几何与无遮挡断言。
- Test: tests/python/axismeld_hotbox_native_style_events.py and axismeld_hotbox_geometry_fixture.py — 真实窄视口复现及可见区域测试坐标。

**Interfaces:** consumes `layout_menu` and `HotboxVisual` from the current implementation; returns `MenuLayout` in unchanged WINDOW logical coordinates including `rects`, `return_regions`, and `marking_gaps`.

- [x] 移除窄窗 held-disabled cancel 测试中的中心鼠标移动，旧安装 `mappings` narrow 已重现原地 E 未切 Rotate，与旧 W 失败同类；保留实际 hit-regions。
- [x] 添加纯几何失败测试：WINDOW 392×281，内部顶端横条 y=229..255；非零偏移验证全部命中/返回/缺席方向同坐标转换。
- [x] 实现安全布局矩形及统一坐标变换；按原 WINDOW 相交裁剪完整输入遮挡，source_live 核验安全范围及容器存活。
- [x] 构建 native tests 和 blender；本片60项菜单测试及五组 CTest通过，合并M2d后61项菜单测试/五组继续通过。
- [x] standard/narrow/2x quad 的 mappings 与 native-style 六组GUI通过；真实导航、设置、像素、原地WER、双向动画与DPI变化有证据。
- [x] 独立审查、修复所有实质问题；安装到既有测试入口并核验配置、资源与 binary。
- [x] 更新缺陷记录与统一人工清单，记录取消和空间不足边界，提交本地分支。本片不擅自推送后续新提交。

## 执行记录

起点：687dc1db83bc1e890f31d683dbf4aacce6ef63c8；当前工作区干净且已在隔离 worktree。

审查修正：Python oracle 改为始终相对原 WINDOW 求交，加入顺序相反的独立字面测试。四视图保留 TOOL_HEADER/TOOLS/UI，实测相交上窗和不相交下窗；隐藏动画中完整输入范围保持会话有效，实际范围改变才取消。

验证边界：同 DPI 下直接拖动 Sidebar 手柄的原生 action-zone 在热盒模态中无法通过 poll，探索日志保留为未通过自动化，不计入 GREEN。该项放统一 VR-04/05 人工待测；DPI 变化测试单独命名，不用旧有 scale 失效检查冒充新 safe-bounds 独立证明。原47项人工已测/原62项待测状态保留。

完成记录：实现、独立审查、99项Python、五组native及本批12组GUI验证通过；独立候选与26份资源及复制配置已核验。统一人工清单131项/47已测/84待测，其中新增22项，人工继续暂缓。源码与本地提交见构建核验记录。
