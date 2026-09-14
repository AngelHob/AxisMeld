# Object Modeling Composition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 按用户Maya截图恢复Object八向热盒与普通菜单组合，接通已有功能和独立Options。

**Architecture:** 固定companion目录、独立级联路径、复用原生列表overlay和单一鼠标所有者；固定命令映射与参数事务。

**Tech Stack:** Blender C++、Python/bpy、CMake/CTest与隔离真实GUI。

**Spec:** `docs/superpowers/specs/2026-09-14-object-modeling-composition-design.md`

## Task 1 — Native组合、Options和输入

- [x] 在hotbox_menu/parser测试加入同时可见列表、独立Options、径向外延、分页/边缘和非法options结构的RED。
- [x] 修改AXM_hotbox_menu.hh、intern/hotbox_menu.cc、view3d_axismeld_hotbox{,_internal,_model,_draw}，保持companion与radial路径独立。
- [x] 独立固定菜单白名单与主行Options映射，提交前保持目标身份检查；真实parser正负测试。
- [x] root统一构建/运行native，不与其他GUI会话并行。

## Task 2 — Maya目录、已有能力与参数

- [x] 按本机Maya脚本写纯目录/命令范围/Options绑定RED；不把Edit-only操作直接套进Object。
- [x] 在Object专用模块声明22主条目、分隔和3级联，接通设计最小能力集；缺口具有明确原因。
- [x] 专用参数窗口捕获身份但保持只读，确认再校验与执行；验证取消、失败、多选、共享data及单Undo。
- [x] 同步COMMANDS、adapter、runtime、keymap及startup注册，Python全套通过。

## Task 3 — 独立GUI、交付

- [x] 旧候选记录缺菜单RED，保留当前运行程序与配置哈希。
- [x] 新独立候选运行实际组合菜单、级联、Options、几何/撤销、Views间距、单/四视图/边缘与已有回归。
- [x] 独立复核后补针对性验证，更新映射/验收及统一人工清单，输出截图、构建核验与开发记录。
- [x] 本地交付；源提交与安装核验写入交付记录，EvoClaw体验留全局审计账本；人工测试继续暂缓。

最终119项Python、5组native、9套GUI通过。菜单恢复的具体范围、未完成的上方Options/几何/UV能力及测试边界以 `docs/compatibility/2026-09-14-object-menu-acceptance.md` 为准。OM新增16项，累计116待测，原47项用户记录未改。
