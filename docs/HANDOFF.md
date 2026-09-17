# 新机器接续开发

本页面向未读过聊天记录的开发者和 Codex。状态基线为 2026-09-17；执行前重新核对远端和当前源码，不把本页固定 SHA 当作永远最新。

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

## 5. 下一任务：Influences；先核对已完成的 A1

A1 已完成有界 Normalize Weights / Prune Small Weights 及独立 Options，勿重复实现；先读[本批设计与验证](development/2026-09-17-skin-weight-cleanup.md)，核实远端后按 ROADMAP A2 推进 Add/Remove/Remove Unused Influences，再处理绑定。新人工 RG-15～RG-20 全部待测。A1 入口文件：

- `scripts/modules/axismeld/rigging_workspace_catalog.py` 和 `scripts/startup/bl_ui/space_axismeld_native_rigging.py`：目录及真实原生功能入口。
- `scripts/startup/bl_ui/space_view3d.py` 的 `VIEW3D_MT_paint_weight`，以及 `source/blender/editors/object/object_vgroup.cc`：核实原生 Normalize All/Clean 实际语义。
- `docs/reference/maya2026-menubar-tree.json`：Maya 原路径、正文、Options 和命令身份；不执行其中原始命令。
- `tests/python/axismeld_native_rigging_test.py`、`axismeld_rigging_catalog_test.py`、`axismeld_rigging_workspace_events.py`：既有菜单与上下文回归入口。

Normalize 单组最大值归一化不等于 Normalize All；Maya Enable/Disable/Post 是持续模式。Clean 还要检查最后影响、阈值、锁定和非骨骼用途组。没有明确定义前不能仅去掉灰色状态。此批不一并开启镜像/复制、Skeleton、UV 或全局缩放改造。

下一批同样先把审计结论和实际选择的参数策略写入该批设计，再实施；日常实现选择可主动完成，只有影响用户数据、范围或产品语义且无法从现有决定推断的分歧才提出一个具体问题。

## 6. 每批如何交付

按 [AGENTS](../AGENTS.md) 更新设计、CHANGELOG 和有变化的测试条目，执行相称验证，再 commit/push 并核验远端 SHA；用户已授权每批开发完成上传 GitHub，不需要重复确认。未通过的必要检查不得用“已完成”掩盖。

Pages 只同步前端运行资源；发布新试用包先固定源码提交，打包/解压/启动核验成功后才改页面的 `buildId` 与下载链接。本次文档交接不重打 Rigging 预览包，不改其 tag 或历史测试结果。

若新机器无法登录 GitHub，可先完成本机可验证工作并准确说明推送阻碍；不要向用户索取令牌粘贴进对话或文档。使用该机器已有的 Git/凭据管理器或用户自行登录。

给另一台 Codex 的完整文本见 [CODEX_HANDOFF_PROMPT](CODEX_HANDOFF_PROMPT.md)。
