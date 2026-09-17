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

2026-09-17 的已发布基线：
- tag：axismeld-2026.09.17-rigging-preview
- 对应功能源码：617986ac184125fe2169456bdb525965530ea736
- 后续开发提交以远端分支为准，不能用这个固定 tag 覆盖后续工作。
- public site：https://angelhob.github.io/AxisMeld/
- docs/compatibility/2026-09-17-handoff-snapshot.json 保存公开校验值与历史验证范围。
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
- Rigging 的 Skeleton/Skin 保留82条Maya正文、33个Options，但这些Maya算法仍未适配；9个Blender入口已可用。
  旧文件/用户startup不自动插入Rigging；startup.blend已提交且该文件单独用普通Git存储。
- AXM-COMPAT-001（Object Global缩放差异）用户明确搁置，不自动重启。

默认下一批任务：先做 Skin 权重整理的有界适配。
先核实 Normalize Weights / Prune Small Weights 对 Blender Normalize All / Clean 的作用域、锁定、阈值、
零权重、非骨骼顶点组、Options 和 Undo；更新该批设计后，实施证据充分的适配。
不要把单组 Normalize 当 Normalize All，也不要把一次归一化冒充 Maya Enable/Disable/Post 持续模式。
不要仅换标签或解除灰显。后续顺序见 ROADMAP：Influences及绑定/解绑 → Mirror/Copy → Skeleton；
建模缺口继续按已有M3计划处理，UV后置独立推进，不在这一批同时展开。
如果这些已被新提交完成，就先报告实际状态并接下一项，避免重复开发。

先完成本机基线核验，报告源码分支/SHA、构建或下载exe来源、已跑检查和限制，然后继续开发。
原生Weights现成能力不等于新实现；人工测试暂缓不阻止可自动验证的工作。
截至该基线，测试清单308项、当前296、历史12；47项只标历史已测不等于通过，RG-07～14仍待测。
保留所有稳定编号与原结果。网页记录只在访客浏览器，可导出JSON；不自动跨设备同步，不替我勾选已测。

交付已授权：每批完成并验证后，更新 docs/CHANGELOG.md、相关设计和新的待人工测试内容，提交并推送GitHub，
核验远端收到。验收变化时同步公开catalog/Pages；新版试用包必须记录对应源码SHA、资源指纹、许可证，
重新解压启动后再更新下载版本。不要把自动测试当人工验收，也不要自动提交测试反馈Issue。
必要的公开源码、文档、工具和发布包可以上传；不上传凭据、私人配置/场景、浏览器数据或Autodesk安装源码。
无需每批再次询问是否推送；本机缺权限时完成可做工作并明确报告，不能假称已上传。
```
