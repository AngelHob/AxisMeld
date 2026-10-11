# 给另一台机器 Codex 的接续提示词

复制下方整段到新任务。无需上传原对话；若本地源码目录不同，让 Codex 自行检查并采用独立目录。

```text
请接续开发我的 AxisMeld 项目。默认用中文，结论优先，主动核实并完成有界任务。

本批交付状态（2026-10-11）：当前范围实现与统一候选回归已完成，发布待本批验收回执。
已通过40组354项纯Python、8组139项原生、真实RNA7+4项及7个实际File流程；
统一候选18组回归全部通过（17组GUI、1组profiles后台验证，按套件计）；
exe SHA256：793731a1ee5b4d510065ab6564d06c03c07711b65a037433f75e24f49f593912。
新包尚未发布。接手先读
docs/compatibility/2026-10-11-gui-completion-acceptance.md 的最终结果/指纹，不能沿用这段中间状态。
9月17日旧Skin包仍可下载，但不包含本批GUI/原生输入改动，不能用于本批人工验收。

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
- 可下载完整试用 ZIP 与 .sha256；原电脑 build/candidate/outputs/work 不是开发依赖。

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

当前 GUI 批次从 b9d0977557c6e2991810bc91f3f9d6b117a16eb8 继续，后续以远端为准。
2026-09-29 用户决定先完成 UI、交互、Maya 默认快捷键，暂停新算法；
2026-10-11 用户进一步要求完成全部当前 GUI，当前范围实现已完成，保留以下入口和回归：
- Ctrl+RMB 转换与伴随菜单、Ctrl+Shift+RMB 当前工具菜单。
- Edit空选择只读捕获，确认后才操作；UID/拓扑保护及原生模态取消恢复。
- A+LMB History八方向：LMB松开排队，A松开提交；取消不FrameAll，队列绑定原目标。
- 原生X/V/J临时吸附：按下/释放、Ctrl/重叠键、模式切换、失焦、Redo保护。
- 九个无provider空目录灰占位及原因；Grease Pencil绘画键位隔离。
- Space → File只开放Open Scene / Save Scene As两条正文，无新增默认快捷键；
  精确调用token穿过原生未保存场景/修改图像确认链，只关联对应文件选择器。
  不跳过确认、不加全局键盘拦截，独立Options和其他File/Window项保持原状态。
  设计见docs/development/2026-10-11-file-window-release-design.md。
最终实际状态必须读取 docs/compatibility/2026-10-11-gui-completion-acceptance.md 和最新CHANGELOG，
不得只凭这段提示词宣布GUI已通过；不要重复开发已落地入口。

当前审计：58默认命令、60含别名绑定、7操纵器入口、3原生模态持键、497原生继承、45移除项、186受保护keymap。
原18+2项参考核对完成，事实/原文件指纹见docs/reference/2026-10-11-input-reference.json。
先跑 tools/utils/axismeld_input_audit.py --check 和菜单/公开目录生成器 --check，勿重做工具。
原生继承（包括F1–F5）不宣称Maya等价；D/C/F12/1/2/3及Shift+J缺底层能力，保留明确边界。
不新增Influences、绑定/解绑、Mirror/Copy、Skeleton、建模或完整UV算法；A1保持现状。
UI阶段结束先报告待人工验收与能力边界，后续优先处理明确GUI反馈，由用户决定恢复功能开发。

本批改了C++，必须按BUILD_AND_DELIVERY重新编译，不能向9月17日Skin ZIP仅复制Python冒充新版。
固定旧native的Python打包器也不适用；禁止关闭其保护强行发包。
真实事件使用 axismeld_hotbox_ui_runner.py 的 context-entries、history-hotbox、temporary-snap、
workspace-menu-layout、file-window、release-cross-window，以及相关原有Modeling/Rigging/QWER/菜单回归；
隔离配置和临时场景，保留实际File入口、确认继续/取消与精确token所有权断言。
从已验证的新install打包，记录源码完整SHA、资源/二进制/ZIP指纹、许可、运行时边界，重新解压验证。
新完整native的静态门禁使用tools/utils/axismeld_native_preview_audit.py；
staging/extract核对提交源码、全部文件、受管模块集合、许可与ZIP。静态PASS不替代启动/GUI/跨机验证。
最终候选/发布状态看GUI验收及公开config，不能把旧包当作本批新C++。

人工目录330项：当前318、历史12；47项只标历史已测，当前初始未测271。
GU-01～GU-13新增待测，原IN/RG及其他编号与结果保持；自动化不替我勾选。
公开网页数据在各访客浏览器，可导出JSON，不自动跨设备同步；GitHub Issue用于公开共享反馈。

交付已授权：每批完成并验证后，更新 docs/CHANGELOG.md、相关设计和新的待人工测试内容，提交并推送GitHub，
核验远端收到。验收变化时同步公开catalog/Pages；新版试用包必须记录对应源码SHA、资源指纹、许可证，
重新解压启动后再更新下载版本。不要把自动测试当人工验收，也不要自动提交测试反馈Issue。
必要的公开源码、文档、工具和发布包可以上传；不上传凭据、私人配置/场景、浏览器数据或Autodesk安装源码。
无需每批再次询问是否推送；本机缺权限时完成可做工作并明确报告，不能假称已上传。
```
