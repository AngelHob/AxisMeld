# 新机器接续开发

本页面向未读过聊天记录的开发者和 Codex。首批 GUI 收敛的历史起点为 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8`；本批版本见下文，执行前核对远端与当前源码。新算法仍暂停，不因 UI 实施完成自动启动 A2。

**最新交付（2026-10-11 GUI menu polish）：三项菜单 GUI 修复及完整原生预览包已发布。** 菜单显示实际快捷键；灰 Options 不再增加键盘停点；窄窗长说明完整换行并避让菜单。本轮通过 81 项纯 Python、42 项原生和 6 组实际 GUI（长说明覆盖三个窗口/缩放组合）。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-menu-preview)，源码/native 均为 `74dd7159d3a2481780915e065e0bd63312cbdaa0`；匿名下载、完整解压及启动已核验。详见[本轮验收](compatibility/2026-10-11-gui-menu-polish-acceptance.md)与[发布快照](compatibility/2026-10-11-gui-menu-preview-snapshot.json)。新增 GU-17～GU-19 待人工，原结果保持；极低窗口无说明空带时可能覆盖菜单。新算法继续暂停。

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
3. [构建与交付](BUILD_AND_DELIVERY.md)、[当前发布快照](compatibility/2026-10-11-gui-menu-preview-snapshot.json)：命令、源码与发布版本关系；9 月 17 日快照仅用于对应历史包。
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
3. 已发布 ZIP 按对应侧边 SHA256 和快照核验；`tools/utils/axismeld_release_audit.py` 只支持固定 9 月 17 日 Rigging 包。本批完整新 native 使用 `tools/utils/axismeld_native_preview_audit.py` 的 candidate/staging/extract 检查，按 BUILD_AND_DELIVERY 操作。静态核验不证明新机器已经完成编译或 GUI 验收，不混用旧包与新源码回执。
4. 准备新机器原生构建并用隔离配置启动。若本批只改 Python 可针对性验证，但 `startup.blend` 或 C++ 有变化必须重新编译内嵌资源，不能复用旧 exe。
5. 简短报告本机源码 SHA、运行 exe 的来源、检查结果与当前限制，然后继续选定的有界任务。没有图形环境时仍完成可做的开发/结果测试，GUI 留作明确待验收项，不能冒称已经运行。

## 5. 当前 GUI 收敛与下一步

先读 [GUI 验收](compatibility/2026-10-11-gui-menu-polish-acceptance.md) 和最新 CHANGELOG，确认最终验证状态，再运行输入/菜单/公开目录生成器的 `--check`。不要重复开发 Ctrl+RMB 转换、Ctrl+Shift+RMB 当前工具、Edit 空选预选、A+LMB History、X/V/J 临时吸附、九个空动态目录修复或 Space → File 跨窗口释放。

当前输入导出为 58 默认命令、60 条绑定、7 操纵器入口、3 原生模态持键入口、497 条继承、45 条移除、186 个受保护 keymap。原 18+2 条缺参考已闭合，参考记录的是已核实的 Maya 2026 默认事实与原文件指纹，不上传安装源码。原生继承键（含 F1–F5）不宣称 Maya 等价。

- 当前上下文入口：`context_conversion_hotbox.py`、`edit_preselection.py`、native hotbox；确认组件后才写选择，终结回调处理独立原生模态取消，不通过 Python 定时器写回旧 BMesh。
- 持键入口：`history_hotbox.py`、`AXM_history_hold.hh`、`transform_axismeld_snap.cc/.hh`。A 的动作延后至 A 释放，旧队列绑定原目标；临时吸附归一次 TransInfo，不持久写入用户设置或 Redo。
- 菜单入口：`workspace_menu_catalog.py`、原生 UI 宿主及本批菜单审计；保持批准的七根/两根、灰项、右侧齿轮、真实原生 provider 和插件回调。
- File 入口：只开放 `file.open` / `file.save_as`，无默认快捷键，保留独立 Options 灰占位。精确 token 穿过未保存场景/修改图像确认，只绑定对应文件选择器；取消、失焦和窗口销毁不能残留松键所有权。不得替换为全局拦截或绕过确认，见 [File 设计](development/2026-10-11-file-window-release-design.md)。
- 实际事件 suites：`context-entries`、`history-hotbox`、`temporary-snap`、`workspace-menu-layout`、`file-window`、`release-cross-window`；配合既有 Modeling、Rigging、菜单和释放回归，按验收回执指定的新构建运行。9 月 17 日的旧 native 不支持本批交互。

D/C/F12/1/2/3 及 Shift+J 的缺口分别涉及独立枢轴、曲线最近点、UV 选择域、可恢复预览和相对吸附，不用近似操作冒充完成。独立 Vertex Face、Isolate 动态书签提供器、Skin/Skeleton/建模/UV 新算法继续后置，Global 缩放继续搁置。

人工目录 336 项，当前 324、历史 12；47 项只保留历史“已测试”状态，当前初始待测 277。GU-17～GU-19 最新新增，原 IN/RG/G 等编号和结果保留。网页勾选属于各访客浏览器，GitHub Issue 才是共享反馈。

后续优先处理新构建的具体 UI/输入反馈与显示/手感验收，保留已通过的实现和回归。阶段收敛后先向用户报告范围与限制，恢复功能开发须由用户决定，不自动回到旧 A2 队列。

## 6. 每批如何交付

按 [AGENTS](../AGENTS.md) 更新设计、CHANGELOG 和有变化的测试条目，执行相称验证，再 commit/push 并核验远端 SHA；用户已授权每批开发完成上传 GitHub，不需要重复确认。未通过的必要检查不得用“已完成”掩盖。

Pages 只同步前端运行资源；发布新试用包先固定源码提交，打包/解压/启动核验成功后才改页面的 `buildId` 与下载链接。本批已发布完整原生 GUI menu preview，匿名下载与线上目录核验通过，记录见[当前发布快照](compatibility/2026-10-11-gui-menu-preview-snapshot.json)。

历史 A1 另发的 Skin weights 预览包（Python 源码 bf35ab393b7c）复用 Rigging native，旧 tag 和历史测试结果保持；对应记录为 compatibility/2026-09-17-skin-weights-snapshot.json。

9 月 18 日新环境曾从 `33dd3a3e591b` 完成原生构建和指定测试，当时没有另发该 native 的 ZIP；这段历史不代表本批 GUI preview 未发布。步骤与限制见 BUILD_AND_DELIVERY。固定旧 native 的 Python 打包器不适用于包含本轮 CMake 改动的 HEAD，不能因只计划修改 Python 就绕过它的源码白名单。

若新机器无法登录 GitHub，可先完成本机可验证工作并准确说明推送阻碍；不要向用户索取令牌粘贴进对话或文档。使用该机器已有的 Git/凭据管理器或用户自行登录。

给另一台 Codex 的完整文本见 [CODEX_HANDOFF_PROMPT](CODEX_HANDOFF_PROMPT.md)。
