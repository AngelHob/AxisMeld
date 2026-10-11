# AxisMeld 开发接续

**最新交付（2026-10-11 GUI interaction polish）：两项菜单/热盒交互修复及完整原生预览包已发布。** Modeling 原生灰项显示上下文原因，并阻止无效子菜单预览；W/E/R 持键时每次 LMB 重复唤出从根目录开始。本轮通过 94 项纯 Python、42 项原生和 7 组实际 GUI。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-interaction-preview)，源码/native 均为 `534eec00698397cc55e27f23f3575e6d4894331a`；匿名下载、干净解压及工厂启动已核验。详见[本轮验收](docs/compatibility/2026-10-11-gui-interaction-polish-acceptance.md)与[发布快照](docs/compatibility/2026-10-11-gui-interaction-preview-snapshot.json)。新增 GU-20～GU-21 待人工，GU-01～GU-19 及原结果保持；极低窗口无说明空带时可能覆盖菜单。新算法继续暂停。

- 新接手先读 `docs/ROADMAP.md`、`docs/CURRENT_ISSUES.md`、`docs/HANDOFF.md`，再读当前模块设计与源码。旧日期文档是历史设计，不可据其状态重做已经交付的功能。
- 当前开发分支为 `axismeld/phase-2a`；默认 `axismeld/integration` 未包含最新功能。不要自动合并到默认分支；新机拉取、LFS、构建、验证及发布说明见 `docs/BUILD_AND_DELIVERY.md`。
- 保留 Blender 全局菜单与工作区栏。Modeling 七根菜单保持；Vertex/Edge/Face 在 Edit Mesh 内；不恢复 Deform/Generate 根。Rigging 是原生工作区，Rigify 是内置模块。
- Maya 未适配功能保留灰占位，Options 与正文独立；使用真实原生 Menu/operator 上下文，不把相似功能冒充等价，不隐式修改选区来绕过不可用条件。
- `AXM-COMPAT-001` 全局缩放差异按用户决定搁置，不自动重启。人工验收暂缓不阻止可验证的开发，但自动化不得替代人工状态。
- 当前优先级（2026-09-29 用户更正）：UI、交互与 Maya 2026 默认快捷键优先，暂停新增建模、Skin/Skeleton、UV 算法和功能适配。U0–U3 当前范围实现已完成；保留已实现入口和回归，接续先查本批验收与具体反馈，不重复开发。阶段交付后报告范围与待人工内容，由用户决定何时恢复功能开发；不自动回到 A2 Influences。
- Space → File 只接入 Open Scene / Save Scene As 两个无默认快捷键的语义命令。跨窗松键依靠精确调用 token 穿过原生确认链；不得改成全局键盘拦截、跳过确认或把其他 File/Window 灰项批量启用。设计见 `docs/development/2026-10-11-file-window-release-design.md`。
- 最新 GU-20～GU-21 共 2 项人工待测；公开目录 338 项（当前 326、历史 12），47 项仅历史已测，当前初始未测 279、全表初始未测 291；GU-01～GU-19 等既有项目保持。自动化不修改任何人工测试结果。

## AxisMeld 热盒约束

- 修改或新增方向热盒前，阅读 `docs/development/2026-09-14-hotbox-reference-contract.md`。
- 四视图控制的二级热盒是布局与操作标杆。五行热盒第2/4行及第3行的横向净间隔须与它直接比较；不得只复用公式却留下更窄的中心宽度，不得缩小四视图或牺牲间隔来让测试通过。
- 同时验证实际按钮、中心取消区域、缺席方向与外延命中。既有“短划能命中”测试不能覆盖用户报告的误触问题。
- 方向动作使用热盒；设置、选项列表和深目录使用原生普通菜单。保留按键释放、取消、父子返回及QWER持键反复唤出的规则。

## 开发完成流程

- 用户已明确授权：每次 AxisMeld 开发完成并验证后，都要提交并推送到 GitHub，不再逐次询问。
- 同一批改动更新 `docs/CHANGELOG.md`，记录日期、功能或修复、验证结果与待人工测试内容；提交日志不能代替修改日志。
- 验收内容发生变化时，同步测试清单与公开测试网页，保留稳定编号和已有结果；发布试用包时标明其对应源码版本。
- 结束前确认 GitHub 远端已收到提交；未能推送或发布时明确报告原因，不将本地完成当作远端已更新。用户明确要求仅本地处理时，以当次要求为准。
