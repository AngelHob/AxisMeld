# 给另一台机器 Codex 的接续提示词

复制下方整段到新任务。无需上传原对话；若本地源码目录不同，让 Codex 自行检查并采用独立目录。

```text
请接续开发我的 AxisMeld 项目。默认用中文，结论优先，主动核实并完成有界任务。

最新交付（2026-10-11）：热盒下方列表 16 像素预览已发布；基于 Blender 5.4 Alpha，固定 upstream 754ebe3c4b4e1402a159df6e1e58823cc93ef887。
本轮6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过。预发布tag：axismeld-2026.10.11-16px-companion-preview；匿名下载、干净解压与factory已核验。本批 Pages `43d73f2bff6c` 的 6 个公开资源逐字节核验通过。
功能/native源码：89fec688b9dd2f0c95f6a814488cd70733b29893。
exe SHA256：4878173623cef3b3485e088c2b1b909a0a57107f7193ffe3fca7de3cf8573240。
发布入口：https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-16px-companion-preview
先读docs/compatibility/2026-10-11-16px-companion-acceptance.md及docs/compatibility/2026-10-11-16px-companion-preview-snapshot.json。
人工状态：公开目录 344 项（当前 331、历史 13），47 项仅历史已测，当前初始未测 284、全表初始未测 297；最新标记 GU-27。既有编号与人工结果保持，自动化不替用户勾选。
仅将热盒下方伴随列表及其级联普通行高设为 16 逻辑像素（100% 界面缩放），Options 宽 16、细分隔 4；文字、图标、列宽和留白沿 16/24 的局部比例同步，高 DPI 保持 Blender 界面缩放规则；周围方向按钮、四视图间隔、主热盒栏及普通原生菜单保持原尺寸。完整条目、底部避让和说明无空间时隐藏的规则保持，不折叠、不滚动，不随窗口继续缩小。保留极低窗口完整说明避让、七根菜单、独立Options与占位、取消恢复；新算法暂停。

仓库：https://github.com/AngelHob/AxisMeld
最新开发分支：axismeld/phase-2a
重要：默认分支 axismeld/integration 目前不是最新功能实现；gh-pages 只是公开测试网页。
请先确认远端现状，不从默认分支误开工，也不自动合并/重置/改写既有分支。
有源码目录就先读 git status 和 AGENTS.md；没有则优先在 D 盘独立目录拉取正确分支。
遵循仓库 docs/BUILD_AND_DELIVERY.md 的 LFS/依赖流程，避免 GitHub Blender fork 的 LFS 问题。

开始时按顺序阅读：
1. AGENTS.md
2. docs/ROADMAP.md
3. docs/CURRENT_ISSUES.md
4. docs/HANDOFF.md 和 docs/BUILD_AND_DELIVERY.md
5. docs/CHANGELOG.md、当前模块设计、相关源码及测试
不依赖其他电脑的 Codex 记忆或聊天摘要；有冲突先检查当前实现与最新用户决定。

2026-09-17 的 native 历史发布基线：
- tag：axismeld-2026.09.17-rigging-preview
- 对应功能源码：617986ac184125fe2169456bdb525965530ea736
- 后续开发提交以远端分支为准，不能用这个固定 tag 覆盖后续工作。
- public site：https://angelhob.github.io/AxisMeld/
- docs/compatibility/2026-09-17-handoff-snapshot.json 保存公开校验值与历史验证范围。
- A1 历史试用 tag：axismeld-2026.09.17-skin-weights-preview，Python源码：bf35ab393b7c4d94bfdd78680a862ab76c71fc6e；native仍复用以上基线。
- A1公开资源/ZIP指纹与验证边界见 docs/compatibility/2026-09-17-skin-weights-snapshot.json。
- 历史ZIP与.sha256按各自旧快照核验；当前试用采用本提示词开头的新GUI preview。
  原电脑build/candidate/outputs/work不是开发依赖。

当前产品约束：
- 这是 Blender 原生衍生项目；Rigify 已默认内置，不再作为用户启停的插件；Rigging 是原生工作区。
- 保留 Blender 原全局 File/Edit 等菜单和 Workspace 栏。
- Modeling 视窗七根：Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、UV。
  Vertex/Edge/Face 已作为子菜单收纳在 Edit Mesh 内；不要恢复独立根。不要 Deform/Generate 根，变形使用 Modifier。
- Maya 正文、Options、分组和层级完整保留；未实现功能灰色占位，不能通过删除占位装作完成。
  Blender 原有能力按同类菜单归纳，保留原生 Menu 宿主、插件回调、参数和执行上下文。
- 使用统一 Blender 图标，Options 齿轮右对齐；正文再执行一次不是参数设置。
- 方向/肌肉记忆动作放紧凑 marking 热盒，设置/选项/深目录用原生普通菜单。
  四视图二级热盒是布局和操作标杆：五行的第2/4/3行净间隔、中心取消区、缺席方向和外延划选必须验证。
  伴随菜单不折叠/滚动，下方放不下时底部对齐；保留 QWER 持键时重复长按 LMB 唤出。
- 不为使按钮可点而暗改选区/模式；测试实际结果、取消和一次 Undo。
- Rigging 的 Skeleton/Skin 保留82条Maya正文、33个Options，其中一次Normalize Weights/Prune Small Weights及2个Options已做有界适配，其余80正文/31 Options仍灰显；9个Blender入口保留。
  旧文件/用户startup不自动插入Rigging；startup.blend已提交且该文件单独用普通Git存储。
- AXM-COMPAT-001（Object Global缩放差异）用户明确搁置，不自动重启。

首批 GUI 收敛的历史起点为 b9d0977557c6e2991810bc91f3f9d6b117a16eb8；当前交付见开头，后续以远端为准。
2026-09-29 用户决定先完成 UI、交互、Maya 默认快捷键，暂停新算法；
2026-10-11 用户进一步要求完成全部当前 GUI，当前范围实现已完成，保留以下入口和回归：
- Ctrl+RMB 转换与伴随菜单、Ctrl+Shift+RMB 当前工具菜单。
- Edit空选择只读捕获，确认后才操作；UID/拓扑保护及原生模态取消恢复。
- A+LMB History八方向：LMB松开排队，A松开提交；取消不FrameAll，队列绑定原目标。
- 原生X/V/J临时吸附：按下/释放、Ctrl/重叠键、模式切换、失焦、Redo保护。
- 九个无provider空目录灰占位及原因；Grease Pencil绘画键位隔离。
- Modeling原生灰项有上下文原因，不创建无效原生子菜单预览；有效模式仍走原生宿主/poll/参数和插件回调。
- W/E/R持键时每次LMB stroke结束清理伴随路径，下一次从根目录开始；保留当前stroke内父子返回与取消。
- 极低窗口说明只在能容纳全文的菜单外空白绘制；无空白时隐藏，扩大窗口后恢复，不修改菜单布局、字号、命中或选区。
- Space → File只开放Open Scene / Save Scene As两条正文，无新增默认快捷键；
  精确调用token穿过原生未保存场景/修改图像确认链，只关联对应文件选择器。
  不跳过确认、不加全局键盘拦截，独立Options和其他File/Window项保持原状态。
  设计见docs/development/2026-10-11-file-window-release-design.md。
最终实际状态必须读取 docs/compatibility/2026-10-11-16px-companion-acceptance.md 和最新CHANGELOG，
不得只凭这段提示词宣布GUI已通过；不要重复开发已落地入口。

当前审计：58 默认命令、60 条含别名绑定、7 个操纵器辅助入口、3 个原生模态持键入口、499 条原生继承、45 条移除、187 个受保护 keymap；基准/生成 keymap 为 281/282。
原18+2项参考核对完成，事实/原文件指纹见docs/reference/2026-10-11-input-reference.json。
先跑 tools/utils/axismeld_input_audit.py --check 和菜单/公开目录生成器 --check，勿重做工具。
原生继承（包括F1–F5）不宣称Maya等价；D/C/F12/1/2/3及Shift+J缺底层能力，保留明确边界。
不新增Influences、绑定/解绑、Mirror/Copy、Skeleton、建模或完整UV算法；A1保持现状。
UI阶段结束先报告待人工验收与能力边界，后续优先处理明确GUI反馈，由用户决定恢复功能开发。

本批改了C++，必须按BUILD_AND_DELIVERY重新编译，不能向9月17日Skin ZIP仅复制Python冒充新版。
固定旧native的Python打包器也不适用；禁止关闭其保护强行发包。
真实事件使用 axismeld_hotbox_ui_runner.py 的 hotbox-reasons、modeling-disabled-reason、hotbox-repost、context-entries、history-hotbox、temporary-snap、
workspace-menu-layout、file-window、release-cross-window，以及相关原有Modeling/Rigging/QWER/菜单回归；
隔离配置和临时场景，保留实际File入口、确认继续/取消与精确token所有权断言。
从已验证的新install打包，记录源码完整SHA、资源/二进制/ZIP指纹、许可、运行时边界，重新解压验证。
新完整native的静态门禁使用tools/utils/axismeld_native_preview_audit.py；
staging/extract核对提交源码、全部文件、受管模块集合、许可与ZIP。静态PASS不替代启动/GUI/跨机验证。
最终候选/发布状态看GUI验收及公开config，不能把旧包当作本批新C++。

公开目录 344 项（当前 331、历史 13），47 项仅历史已测，当前初始未测 284、全表初始未测 297；最新标记 GU-27。既有编号与人工结果保持，自动化不替用户勾选。
本轮人工范围：GU-27；原 GU/IN/RG 等编号和状态保持，自动化不替我勾选。
公开网页数据在各访客浏览器，可导出JSON，不自动跨设备同步；GitHub Issue用于公开共享反馈。

交付已授权：每批完成并验证后，更新 docs/CHANGELOG.md、相关设计和新的待人工测试内容，提交并推送GitHub，
核验远端收到。验收变化时同步公开catalog/Pages；新版试用包必须记录对应源码SHA、资源指纹、许可证，
重新解压启动后再更新下载版本。不要把自动测试当人工验收，也不要自动提交测试反馈Issue。
必要的公开源码、文档、工具和发布包可以上传；不上传凭据、私人配置/场景、浏览器数据或Autodesk安装源码。
无需每批再次询问是否推送；本机缺权限时完成可做工作并明确报告，不能假称已上传。
```
