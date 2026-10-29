# AxisMeld 开发接续

## 2026-10-29 · 自定义属性参数窗口交付

**当前交付：自定义属性参数窗口修复预览。** 版本 `axismeld-2026.10.29-custom-property-preview`；[下载](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.29-custom-property-preview)。 [本批验收](docs/compatibility/2026-10-29-custom-property-acceptance.md) · [集中指纹与验证快照](docs/compatibility/2026-10-29-custom-property-preview-snapshot.json)。

继续以 UI、交互和 Maya 2026 默认快捷键为优先；新增建模、Skin/Skeleton、UV 算法保持暂停。 CP-01～CP-05 与原 PN-01～PN-06 继续待人工；物理鼠标操作、物理 F3 搜索、双语和高 DPI 可读性及完整视觉布局仍待人工验收。

下方既有日期记录保留为历史；当前版本以上段和本批快照为准。

## 2026-10-29 · 属性导航交付

**当前交付（2026-10-29）：Transform / Modifiers 属性导航预览已发布并核验。** 在现有界面中打开 Blender 原生变换与修改器属性，保留中英文显示、18px 伴随列表与现有交互；不增加建模算法。 [下载完整预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.29-property-navigation-preview)；功能/native 源码 `45a5a51a01925164f11dcf4ce1ecbb8be217dced`，固定 Blender 5.4 Alpha upstream `754ebe3c4b4e1402a159df6e1e58823cc93ef887`。

10 组 127 项针对性 Python、当前真实事件 hotbox-repost、最终安装和独立解压副本各 14 项 GUI、本地网站 14 项浏览器检查通过。完整包 6,533 文件、154 选定资源，stage/extract、匿名下载和公开包工厂启动通过。ZIP 280,173,712 字节，SHA256 `88c3a3728bed8f3d83fd6229545a06493c071ffc4e458b27c482cff048027858`；EXE SHA256 `e85cc631490981c0a4893ffd6fe60b4bc70c2534108c21c181219c86772a74a4`。本批为 Python 改动且 buildinfo OFF，EXE hash 与双语基线相同；如实记录，不称独立可复现重编证明。

公开目录 400 项（当前 386、历史 14），47 项仅为历史已测；当前初始待测 339、全表初始待测 353。本批新增 PN-01～PN-06，六项均待人工；既有编号与人工结果保留。

实际 GUI 验证覆盖原生 RNA 属性与 operator/Undo：最终安装候选 14 项、独立解压运行副本 14 项通过；物理 F3 键盘搜索和字段鼠标编辑未自动化，仍待人工。启动截图存在覆盖视窗的启动模态框，不能据此宣称全部视觉布局已验清。

继续 UI、交互与 Maya 2026 默认快捷键优先；新增建模、Skin/Skeleton、UV 算法暂停。后续可按用户反馈改进既有 Options 体验，不自动开启新算法开发。

公开 Pages 本批六资源已逐字节核验通过，提交 `22f6ad60ddac2261e44ac26e64540dc8b390f74b`；最终网站配置下 14 项浏览器检查通过。 详见[本批验收](docs/compatibility/2026-10-29-property-navigation-acceptance.md)与[发布快照](docs/compatibility/2026-10-29-property-navigation-preview-snapshot.json)。

当前人工维护且按入口分组的 tools/testing_site/catalog.json 是公开目录权威来源。不要运行旧 tools/utils/axismeld_public_test_catalog.py 导出：它遗漏多段 BI 编号和新组，会把当前目录回退；同步维护人工 ledger 与按入口索引。

以下原日期记录保留历史证据；当前交付与计数以上段及本批快照为准。

**最新交付（2026-10-13）：双语界面完整预览已发布并核验。** 标签保留 `axismeld-2026.10.12-bilingual-ui-preview`；仅 `en_US`/`zh_HANS`，默认英文。原生词库与补词覆盖热盒、菜单、Options、灰说明和内置 Rigify，测量与显示同文；真实数据名称、18px 列表、Views 间隔及既有交互保持。旧 locale 回退/保留、中文保存重启及重载工厂启动布局保留已保存 prefs 已验证，不能称作重置全部偏好仍保留中文。见[双语验收](docs/compatibility/2026-10-13-bilingual-ui-acceptance.md)。

本批已通过新构建/安装（6,529 文件、153 选定资源）、2 组 114 原生、7 组 90 Python、3,737 固定源词运行时、129 原生按钮/英文往返、5 旧偏好种子/7 新进程、既有 3 套交互、最终双语 GUI 52 记录、中英文说明与 18/27px 几何、本地网站 14 浏览器检查。完整[双语预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.12-bilingual-ui-preview)已公开发布；功能/native 源码 `e0c4bd7f90ebc3a6016b1c934b1f4d15c42d556e`，运行 EXE 与本批验证相同。6,532 个发行文件、153 项选定资源、独立解压/工厂启动、匿名下载和公开包 3,737 源词运行时已核验。Pages `af31ae30e55c79781b3ff42e8d811d2f71ca7725` 的六个公开资源逐字节一致。 另有88项实际Views净间隔比较通过；见[发布快照](docs/compatibility/2026-10-13-bilingual-ui-preview-snapshot.json)。49项BI仍待人工；不自动恢复新算法。

**上一已核验交付（2026-10-11 18px companion preview）：热盒下方列表 18 像素预览已发布。** 仅将热盒下方伴随列表及其级联普通行高设为 18 逻辑像素（100% 界面缩放），Options 宽 18、细分隔 4.5；文字、图标、列宽和留白沿 18/24 的局部比例同步，高 DPI 保持 Blender 界面缩放规则；周围方向按钮、四视图间隔、主热盒栏及普通原生菜单保持原尺寸。完整条目、底部避让和说明无空间时隐藏的规则保持，不折叠、不滚动，不随窗口继续缩小。 沿用 Blender 5.4 Alpha 固定上游 `754ebe3c4b4e1402a159df6e1e58823cc93ef887`，本批未再次合并上游。6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-18px-companion-preview)，源码/native `f72fb413ba9c16f41c453dde98469ef1933285c1`；匿名下载、干净解压及工厂启动已核验。详见[本批验收](docs/compatibility/2026-10-11-18px-companion-acceptance.md)与[发布快照](docs/compatibility/2026-10-11-18px-companion-preview-snapshot.json)。本批 Pages `b448822d223e` 的 6 个公开资源逐字节核验通过。公开目录 345 项（当前 331、历史 14），47 项仅历史已测，当前初始未测 284、全表初始未测 298；最新标记 GU-28。既有编号与人工结果保持，自动化不替用户勾选。新增建模、Skin/Skeleton、UV 算法继续暂停。

- 新接手先读 `docs/ROADMAP.md`、`docs/CURRENT_ISSUES.md`、`docs/HANDOFF.md`，再读当前模块设计与源码。旧日期文档是历史设计，不可据其状态重做已经交付的功能。
- 当前开发分支为 `axismeld/phase-2a`；默认 `axismeld/integration` 未包含最新功能。不要自动合并到默认分支；新机拉取、LFS、构建、验证及发布说明见 `docs/BUILD_AND_DELIVERY.md`。
- 保留 Blender 全局菜单与工作区栏。Modeling 七根菜单保持；Vertex/Edge/Face 在 Edit Mesh 内；不恢复 Deform/Generate 根。Rigging 是原生工作区，Rigify 是内置模块。
- 双语改动先读 `docs/development/2026-10-12-bilingual-ui.md`。保留英文源目录/稳定 ID，只在显示边界翻译；IFACE/TIP 与 Menu/Operator 上下文、测宽和绘制必须一致。内置工作区只翻译标签，不改实际名称；旧“建模”兼容保留，其他用户数据/路径不译。默认 Blender 键位、Layout 和英文不变。
- Maya 未适配功能保留灰占位，Options 与正文独立；使用真实原生 Menu/operator 上下文，不把相似功能冒充等价，不隐式修改选区来绕过不可用条件。
- `AXM-COMPAT-001` 全局缩放差异按用户决定搁置，不自动重启。人工验收暂缓不阻止可验证的开发，但自动化不得替代人工状态。
- 当前优先级（2026-09-29 用户更正）：UI、交互与 Maya 2026 默认快捷键优先，暂停新增建模、Skin/Skeleton、UV 算法和功能适配。U0–U3 当前范围实现已完成；保留已实现入口和回归，接续先查本批验收与具体反馈，不重复开发。阶段交付后报告范围与待人工内容，由用户决定何时恢复功能开发；不自动回到 A2 Influences。
- Space → File 只接入 Open Scene / Save Scene As 两个无默认快捷键的语义命令。跨窗松键依靠精确调用 token 穿过原生确认链；不得改成全局键盘拦截、跳过确认或把其他 File/Window 灰项批量启用。设计见 `docs/development/2026-10-11-file-window-release-design.md`。
- 公开目录为 394 项（当前 380、历史 14），保留 47 项历史已测标记；当前初始未测 333、全表初始未测 347。本批新增 49 项 BI 验收，新增标记共 50 项（含保留 GU-28）。既有编号与人工结果保持，自动化不替用户勾选。 本地网站14项检查和Pages六资源逐字节核验通过，本批下载入口已更新。

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
