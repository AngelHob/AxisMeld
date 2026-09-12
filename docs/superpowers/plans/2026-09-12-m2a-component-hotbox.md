# M2a Component Hotbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 已选可编辑 Mesh 的右键按住拖曳组件切换，并集中记录待人工测试内容。

**Architecture:** 复用 command registry、context adapter 和原生 marking 会话；右键拥有自己的释放事件。保留不适用上下文的 Blender 原生右键。

**Tech Stack:** Blender C++、Python、Windows Release 构建与 event simulation。

**Spec:** ../specs/2026-09-11-modeling-interaction-alignment-design.md

## Global Constraints

- UV 整体后置；不改 Global 缩放算法；不侵入雕刻、动画与其他编辑器。
- 原生操作管理撤销；通用 dispatcher 不整体增加 UNDO。
- 使用既有隔离 worktree，保留个人配置和可回退测试安装，不推送。
- 自动化通过与人工通过分开记录；M2a 不代表 M2/M3 完成。

## M2a 行为契约

在 Object / Mesh Edit 的 WINDOW 区域，已有选中且可编辑的活动 Mesh 时，无修饰 RMB PRESS 立即打开热盒；按住拖向方向，RMB RELEASE 提交一次。中心释放、Esc、失焦取消。方向使用本机 Maya 2026 dagMenuProc.mel 的可观察配置：N Edge、W Vertex、S Face、NE Object Mode；E UV、SW Vertex Face、SE Multi Component 留不可执行占位，分别关联 deferred-uv、M2-vertex-face、M2-multi-component。不复制 Maya 实现代码。

Object Mode 必须幂等，不使用 F8 的 toggle 命令。暂以活动网格为目标，空白处仍操作活动网格；鼠标下换目标留 M2b，明确展示差异。非网格、无选中网格、非 Object/Edit Mesh 或 Alt/Ctrl/Shift 组合保留原生处理。改键与禁用后原生右键不能被误删，schema 仍为 PRESS-only。QWER 和 Space 行为保持现有规则。

行为核对来源为本机 `C:/Program Files/Autodesk/Maya2026/scripts/others/dagMenuProc.mel`：mesh masks 位于 510–517 行，索引到方位位于 887–894 行，Object Mode NE 位于 1288–1292 行。这里只提取命名与方位事实，不移植源码。M2a 的活动对象目标与按住拖曳契约是本项目有界适配，不能宣称完整复刻 Maya 的鼠标拾取或所有右键变体。

### Task 1: 原生组件会话与命令接入

涉及 scripts/modules/axismeld 的 commands、adapter、keymap、catalog；scripts/startup/bl_operators/axismeld.py；view3d_axismeld_hotbox 内部状态/事件；对应 Python 与 C++ 测试。独立 context_hotbox 模块可承载目录定义，避免混入 QWER 菜单配置。

- [x] 先写失败测试：目录方向/禁用占位、Object Mode 幂等、RMB 上下文与原生回退、重复配置无重复绑定。
- [x] 实现最小命令与会话，完整清理拥有鼠标；不让 RMB 释放被键盘触发释放分支提前吞掉。
- [x] 增加真实 Blender event suite：四方向/中心/Esc/连续两次/不适用上下文/修饰键/释放后正常选择。
- [x] 针对性测试、增量构建、自审；交给独立审查。

### Task 2: 验证、可回退安装与人工清单

涉及 docs/compatibility/2026-09-12-manual-test-ledger.md 和本批验收记录；复用现有 GUI runner。

- [x] 建立带 ID、前置条件、步骤、预期、状态的人工清单，包含上一批 M1/Views 未确认项。
- [x] 新组件 suite 和原有 tools/hotbox/release 回归；只对实际测试二进制声明结果。
- [x] 无用户 Blender 进程时备份并更新现有测试安装；逐项校验 portable 配置未变。
- [x] 更新批次证据和计划状态，输出人工测试清单到当前任务 outputs。

## Decisions

Ruling: 首片只处理活动选中网格 — 先交付可独立验收的组件切换，避免把鼠标拾取与多目标选择混入会话改造 — 鼠标下对象与活动对象不同的 Maya 行为暂不等价，进入 M2b。

Ruling: Select 环新增组件目录时移除原有无操作分隔项 — 防止九个节点跨越容量上限而引入额外翻页 — 有效旧命令全部保留，仅减少分隔。

Ruling: M2a 个人触发支持无修饰 PRESS 改绑，带修饰键配置明确拒绝并回退上一有效层 — 与原生会话的修饰键取消保持一致 — 修饰组合入口留后续 M2b，不接受无法触发的配置。
