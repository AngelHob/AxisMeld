# 给另一台机器 Codex 的接续提示词

复制下方整段到新任务。无需上传原对话；若本地源码目录不同，让 Codex 自行检查并采用独立目录。

```text
请接续开发我的 AxisMeld 项目。默认用中文，结论优先，主动核实并完成有界任务。

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
- A1 新试用 tag：axismeld-2026.09.17-skin-weights-preview，Python源码：bf35ab393b7c4d94bfdd78680a862ab76c71fc6e；native仍复用以上基线。
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

2026-10-11 本批开始时已核实远端基线19add3316c828bb9028bc55a3d3d3b4cb80e9fc3；后续提交以远端为准。
9月18日新环境已从33dd3a3e591b完成原生构建和指定测试，但尚未另发这个native的ZIP。
固定旧native的Python组装工具不接受当前HEAD的CMake差异，不能关闭保护来强行发包。

最新用户决定（2026-09-29）：先完成UI、交互和快捷键对齐，暂停新增功能。
这取代同日早些时候的“A2 Influences下一批”建议。先读
docs/development/2026-09-29-ui-interaction-shortcuts.md，按 ROADMAP U0–U3 收敛：
1. 先核对已生成的当前输入审计，接续U0剩余菜单、参考和手势对照；记录当前事件、区域/模式、差异和验证状态，勿照抄旧Phase 1的完成状态。
2. 对齐正文、层级、分组、图标、右侧齿轮与完整显示，保留已确定的Blender全局栏及工作区组织。
3. 对齐四视图标杆间距、外延划选、父子返回、取消/松键与QWER持键反复LMB唤出。
4. 核实Maya 2026默认快捷键、修饰键、别名、临时状态和上下文冲突；个人覆盖、其他编辑器与插件保持边界。
允许改现有能力的UI、键位、鼠标事件和状态恢复；缺少底层能力的项仍灰显并明确记录。
暂不新增Influences、绑定/解绑、Mirror/Copy、Skeleton操作、建模算法和完整UV能力。
已完成的A1 Normalize/Prune保留，勿回退或重复实现；不要把一次归一化冒充Maya持续模式。
本阶段完成后报告自动/人工验收边界，由用户决定何时恢复功能开发，不自动跳回A2。
如果当前U阶段已被新提交完成，就先报告实际状态并接后续UI/输入项，避免重复开发。

2026-10-11已完成的U0输入切片：
- tools/utils/axismeld_input_audit.py 从真实Industry Compatible/AxisMeld生成器导出
  docs/compatibility/current-input-audit.md及同名JSON；先运行 --check，勿重做导出器。
- 56个默认命令、含别名58条绑定、7条AxisMeld操纵器入口、489条原生继承、53条移除项；177个受保护keymap检查不变。
- 已存参考38条仅文本记法一致，18条历史文字参考、2条标点记法或差异仍待核对；不是完整U0、Maya行为或GUI验收完成。
- 修复Object Mode/Mesh互斥模式插件冲突误报，共享3D View/工具map仍提示；不修改插件键位、命令执行或事件值匹配。
- 12项审计测试、18项输入测试、4项真实Blender RNA检查通过。RNA使用既有安装加载当前源码，未新构建native、未发新ZIP，也未代替人工手感验收。
- Alt+LMB双击的事件所有权和Measure的X保留键边界仍待核对，不猜测性改键。
- IN-01～IN-03是新待测项，步骤见docs/compatibility/2026-10-11-input-diagnostics-acceptance.md；
  必须使用包含本批修复的开发构建，旧9月17日Skin发布包不含修复，不能用它验收本项。

先完成本机基线核验，报告源码分支/SHA、构建或下载exe来源、已跑检查和限制，然后继续开发。
原生Weights现成能力不等于新实现；人工测试暂缓不阻止可自动验证的工作。
当前测试清单317项、当前305、历史12；47项只标历史已测不等于通过；全表初始待测270、当前待测258。
最近新增IN-01～03全部待测；RG-07～14及RG-15～20仍待测，不以新增分组替换旧结果。
保留所有稳定编号与原结果。网页记录只在访客浏览器，可导出JSON；不自动跨设备同步，不替我勾选已测。

交付已授权：每批完成并验证后，更新 docs/CHANGELOG.md、相关设计和新的待人工测试内容，提交并推送GitHub，
核验远端收到。验收变化时同步公开catalog/Pages；新版试用包必须记录对应源码SHA、资源指纹、许可证，
重新解压启动后再更新下载版本。不要把自动测试当人工验收，也不要自动提交测试反馈Issue。
必要的公开源码、文档、工具和发布包可以上传；不上传凭据、私人配置/场景、浏览器数据或Autodesk安装源码。
无需每批再次询问是否推送；本机缺权限时完成可做工作并明确报告，不能假称已上传。
```
