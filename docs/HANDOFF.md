# 新机器接续开发

本页面向未读过聊天记录的开发者和 Codex。2026-10-11 本批开始时已核对远端基线 `19add3316c828bb9028bc55a3d3d3b4cb80e9fc3`；A1 已实现并发布。当前先完成 UI、交互和快捷键，暂停新增功能；U0 输入审计切片和模式冲突诊断修复已完成，接续剩余菜单、参考与手势核对，A2 暂缓。执行前重新核对远端和当前源码，不把本页固定 SHA 当作永远最新。

## 1. 先用正确分支

仓库：<https://github.com/AngelHob/AxisMeld>。最新开发在 **`axismeld/phase-2a`**，默认 **`axismeld/integration` 不是最新功能代码**；`gh-pages` 仅承载公开静态页。不要自动合并功能分支到默认分支或改写历史。

优先在本机 D 盘独立源码目录工作；盘符不同可换，禁止照搬另一台机器的 CMakeCache、虚拟环境或旧安装路径。新建克隆、Git LFS 和依赖的完整命令见 [BUILD_AND_DELIVERY](BUILD_AND_DELIVERY.md)。已有 checkout 先做只读检查：

```powershell
git status --short --branch
git remote -v
git branch --show-current
git log -5 --oneline
```

有未提交改动先辨认来源，不执行 reset/clean 或覆盖。`git pull` 不是上游升级授权；只更新用户项目对应分支。Blender 上游更新作为独立批次处理。

## 2. 阅读顺序

1. 根目录 [AGENTS.md](../AGENTS.md)：热盒与交付硬约束。
2. [ROADMAP](ROADMAP.md)、[CURRENT_ISSUES](CURRENT_ISSUES.md)、[CHANGELOG](CHANGELOG.md)：现状、下一批和已修复事项。
3. [构建与交付](BUILD_AND_DELIVERY.md)、[公开快照](compatibility/2026-09-17-handoff-snapshot.json)：命令、源码与发布版本关系。
4. 当前模块设计；例如 [Rigging](development/2026-09-17-rigging-workspace.md)、[Rigify](development/2026-09-15-rigify-builtin.md)、[紧凑建模栏](development/2026-09-15-compact-modeling-public-testing.md)。
5. 当前模块源码、测试和[人工总清单](compatibility/2026-09-14-manual-test-ledger.md)。历史架构、旧 plans 用作背景；冲突时遵循用户后续决定及当前总览。

不依赖 Codex 私人记忆、原电脑会话或某个已安装技能。若新机器没有同名技能，按仓库文档完成设计、针对性验证和交付，不因此停工。

## 3. 应当同步什么

| 内容 | 获取方式与边界 |
|---|---|
| 源码、设计、接续提示词、测试、Maya 功能身份参考 | 开发分支 Git；参考资料是功能身份/层级/差异记录，不是 Autodesk 安装文件或实现源码 |
| Rigging 默认资产 | `release/datafiles/startup.blend` 已单独采用普通 Git 二进制；不得误恢复为新 LFS 指针 |
| 其他 LFS 资产和预编译依赖 | 按构建文档从 Blender 官方源获取；按提交固定子模块，不跟随其远端 main 漂移 |
| 可直接运行的已发布环境 | 下载 GitHub Release ZIP 及 `.sha256`；完整解压，先运行验证器，再启动；不需要复制原电脑候选目录 |
| 测试步骤和公开反馈 | Git 中 catalog/ledger，GitHub Pages 和 Issues；保留 ID 与版本 |
| 某人的浏览器测试记录 | 当事人从网页导出 JSON 自行转移；当前页面没有跨设备自动同步，也没有 JSON 导入功能，不承诺导出后自动恢复勾选 |
| 编译缓存、SDK、工具链 | 在新机器安装/重建；不提交 CMakeCache、整个 build tree、PDB 或库缓存 |
| 登录、凭据、个人偏好、私人场景 | 留在各自机器，由用户配置；不上传 token、Git credential、个人 userpref/startup 或私人站点数据库 |

公开快照记录前一发布的校验值和验证范围，不是原始本机日志全集。新机器生成的新回执属于新证据，不覆盖历史发布记录。

## 4. 首次接手的验证与交接成果

1. 确认源码分支和干净程度，确认 `startup.blend` 不是 LFS 文本指针，核对依赖和工具链。
2. 跑构建文档中的不依赖 Blender GUI 的菜单/目录/网站检查。失败先定位版本和环境，不用删断言让它通过。
3. 下载已发布 ZIP，与侧边 SHA256 和快照比对；运行 `tools/utils/axismeld_release_audit.py` 的只读校验。它证明公开包与固定源数据相符，不证明新机器已经完成编译或 GUI 验收。
4. 准备新机器原生构建并用隔离配置启动。若本批只改 Python 可针对性验证，但 `startup.blend` 或 C++ 有变化必须重新编译内嵌资源，不能复用旧 exe。
5. 简短报告本机源码 SHA、运行 exe 的来源、检查结果与当前限制，然后继续选定的有界任务。没有图形环境时仍完成可做的开发/结果测试，GUI 留作明确待验收项，不能冒称已经运行。

## 5. 下一任务：UI、交互与快捷键对齐

先读 [UI/输入阶段](development/2026-09-29-ui-interaction-shortcuts.md)，按 ROADMAP U0–U3 推进。[当前输入对照](compatibility/current-input-audit.md)及[完整 JSON](compatibility/current-input-audit.json)已由真实键位生成器导出，不要重做导出器。它覆盖 56 个默认命令、含别名的 58 条绑定、7 条操纵器入口、489 条原生继承、53 条移除项和 177 个受保护 keymap。先运行 `python tools/utils/axismeld_input_audit.py --check` 检查源码与快照是否漂移，再继续剩余 U0 菜单、参考与手势核对；后续按 U1 菜单/布局、U2 热盒事件、U3 快捷键冲突推进。

已存参考的 38 条文本记法一致不等于行为已对齐；18 条历史文字参考与 2 条标点记法或差异仍待核对。Maya 2026 默认参考、当前生成键位、按下/按住/松开、作用模式与区域、差异、测试编号和验证状态必须可追溯；历史 Phase 1 描述不能覆盖当前实现。本批不是完整 U0、Maya 或 GUI 验收完成。

- 输入入口：`scripts/modules/axismeld/commands.py`、`keymap.py`、`profiles.py` 和 `modeling_registry.py`；`tests/python/axismeld_input_test.py`、`axismeld_input_audit_test.py`、`axismeld_input_diagnostics_blender.py`。历史 `axismeld_input_blender.py` 中的上下文假设需先对照当前生成键位，不能直接作为全量验收依据。
- 热盒入口：`hotbox_catalog.py`、`tool_hotbox.py`、原生事件处理及[四视图标杆](development/2026-09-14-hotbox-reference-contract.md)；保留 QWER 持键反复唤出、父子返回与取消。
- 菜单入口：`workspace_menu_catalog.py`、`workspace_native_groups.py`、`rigging_workspace_catalog.py` 及原生 UI 宿主；保留 Blender 全局栏、Modeling 七根、灰项和右侧 Options。
- 验收入口：[统一人工清单](compatibility/2026-09-14-manual-test-ledger.md)现有 G/L/VR/K/FM/MT/MB/RG/IN 编号；自动测试不替代实体键鼠和显示条件验收。

本批修复仅在 Object Mode/Mesh 互斥模式间出现的插件冲突误报，共享 3D View 和工具 map 仍保留潜在冲突提示，不改插件键位或实际事件匹配。12 项审计、18 项输入及 4 项真实 Blender RNA 检查通过；RNA 检查使用既有可运行安装加载当前源码，不代表新 native 构建或 GUI 手感验证。新 [IN-01～IN-03](compatibility/2026-10-11-input-diagnostics-acceptance.md) 全部待测，须用包含本批修复的开发构建；9 月 17 日 Skin 包不含此修复。本批未发布 ZIP，勿修改公开下载版本来冒充已发包。

当前测试目录 317 项，其中当前 305、历史 12；47 项仅有历史已测试信息，全表初始待测 270、当前待测 258。目录统计与每位访客自己的测试记录分开；新增 IN 项不改变旧 RG 项结果。

A1 的 Normalize/Prune 已交付，保持可用，见[原设计](development/2026-09-17-skin-weight-cleanup.md)；RG-15～RG-20 仍待人工测试。Influences、绑定/解绑、镜像/复制、Skeleton、建模新算法与完整 UV 能力均后置；需要这些能力的快捷键记为缺口，不解除灰显。全局缩放差异继续搁置。

每批先记录审计结论和有界差异，再实施与验证；已有设计内的 UI/输入修复主动推进，无法从现有决定判断的语义分歧才提出具体问题。U0–U3 完成后报告验收边界，由用户决定恢复功能开发，不自动回到旧 A2 计划。

## 6. 每批如何交付

按 [AGENTS](../AGENTS.md) 更新设计、CHANGELOG 和有变化的测试条目，执行相称验证，再 commit/push 并核验远端 SHA；用户已授权每批开发完成上传 GitHub，不需要重复确认。未通过的必要检查不得用“已完成”掩盖。

Pages 只同步前端运行资源；发布新试用包先固定源码提交，打包/解压/启动核验成功后才改页面的 `buildId` 与下载链接。A1 已另发 Skin weights 预览包（Python 源码 bf35ab393b7c），复用已审计的 Rigging native；未移动旧 tag 或修改历史测试结果。新快照见 compatibility/2026-09-17-skin-weights-snapshot.json。

9 月 18 日新环境已从 `33dd3a3e591b` 完成原生构建和指定测试，但没有另发此 native 的 ZIP；步骤与限制见 BUILD_AND_DELIVERY。固定旧 native 的 Python 打包器不适用于包含本轮 CMake 改动的 HEAD，不能因只计划修改 Python 就绕过它的源码白名单。

若新机器无法登录 GitHub，可先完成本机可验证工作并准确说明推送阻碍；不要向用户索取令牌粘贴进对话或文档。使用该机器已有的 Git/凭据管理器或用户自行登录。

给另一台 Codex 的完整文本见 [CODEX_HANDOFF_PROMPT](CODEX_HANDOFF_PROMPT.md)。
