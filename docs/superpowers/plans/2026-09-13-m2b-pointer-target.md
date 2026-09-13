# M2b Pointer Target Implementation Plan

> REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Continue the approved modeling interaction design; no new project architecture.

**Goal:** Object 模式组件右键根据鼠标下可选择网格定位目标，只有提交真实组件动作时才改变选择。

**Spec:** ../specs/2026-09-11-modeling-interaction-alignment-design.md

**Architecture:** 复用 Blender 视口拾取与现有组件 native session。捕获目标身份而不立即修改选择；提交前重新确认目标有效、可编辑、可选。共用原生组件命令，不改通用 dispatcher 的撤销策略。

## 契约和约束

- Object 无修饰 RMB：鼠标下有效可选可编辑 Mesh 优先；命中未选 Mesh 后提交点/边/面时切为该网格目标；命中已选 Mesh 保留原生多对象选择集合并令目标活动。
- 右上 Object Mode 同样只在有效提交时定位目标；不进入 Edit，不切换回来。
- 中心、Esc、失焦、修饰键取消、不可执行占位均不改变原选择/活动对象/模式。
- 空白处保留 M2a 活动可编辑选中网格规则；鼠标命中非网格保留原生右键，不能意外编辑后面的网格。不可选/隐藏/不可编辑对象不能变成目标，拾取遵循原生视口可见性和选择过滤。
- Edit Mesh 维持当前原生编辑集合，不跨对象拾取；键盘改绑入口仍按当前活动选择上下文，不依赖不明确的鼠标目标。
- 不改 UV、Shift/Ctrl 建模热盒、Global 缩放、其他编辑器/模式；M2b 本片不代表完整 M2。
- 不在 PRESS 上先选对象再回滚；此方案会污染撤销/Recent并在取消或上下文失效时丢选择。
- 目标生命周期失效或提交时不可用必须取消，不退回另一个对象执行。多对象行为明确记录为 Blender 原生适配。

## Task 1: 目标捕获与提交

Owner: implementer。涉及 view3d_axismeld_hotbox native session、必要的原生拾取适配、Python invoke 入口/命令可用性、对应事件测试；维护现有模块边界，不复制第三方实现。

- [x] 读现有原生选择实现并选择能遵循视口遮挡/可选过滤的最小接口；不要用临时选择探测。
- [x] 先失败用例：鼠标对未选网格，提交作用于新目标，取消原选择不变；非网格回退；已选多对象、Edit和键盘改绑规则。
- [x] 实现捕获/验证/提交及生命周期清理；无几何修改，无虚假撤销历史。
- [x] 跑针对性Python/native和新GUI suite；独立审查后修复。

## Task 2: 回归、安装与人工清单

Owner: main。更新设计/映射事实、保留历史人工结果并明确被本片替代的预期。

- [x] 追加 P-xx 待测项：目标、取消、遮挡、不可选、原生回退、多选、四视图/边缘、实体手感。
- [x] 备份原测试exe/Python，记录portable哈希；GUI独占串行，最终安装态新功能+components/tools/hotbox/release适当回归。
- [x] 校验实际安装和源码一致，保存本地提交、输出集中清单与本批记录；不推送。

## Rulings

默认未选目标提交采用原生替换选择，已选目标提交保留选择集合；取消完全不改选择。此行为扩展 M2a 明示后续鼠标拾取范围，保留原生多对象编辑语义。原生拾取无法可靠辨别的对象/实例宁可取消或原生回退，不声明支持。
