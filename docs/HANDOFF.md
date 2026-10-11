# 新机器接续开发

本页面向未读过聊天记录的开发者和 Codex。首批 GUI 收敛的历史起点为 `b9d0977557c6e2991810bc91f3f9d6b117a16eb8`；本批版本见下文，执行前核对远端与当前源码。新算法仍暂停，不因 UI 实施完成自动启动 A2。

**最新交付（2026-10-11 Compact companion preview）：热盒下方列表缩小预览已发布。** 仅将热盒下方伴随列表及其级联缩为原尺寸的 90%，文字、图标、行高、留白和 Options 同步；周围方向按钮、四视图间隔、主热盒栏及普通原生菜单保持原尺寸。完整条目、底部避让和说明无空间时隐藏的规则保持，不折叠、不滚动，不随窗口继续缩小。 沿用 Blender 5.4 Alpha 固定上游 `754ebe3c4b4e1402a159df6e1e58823cc93ef887`，本批未再次合并上游。6 组 42 项相关 Python、2 组 114 项原生、5 组既有 GUI 回归与 1 组新增列表几何验证通过。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-compact-companion-preview)，源码/native `7ebc757ae0826bce1506174f14e639344553423e`；匿名下载、干净解压及工厂启动已核验。详见[本批验收](compatibility/2026-10-11-compact-companion-acceptance.md)与[发布快照](compatibility/2026-10-11-compact-companion-preview-snapshot.json)。本批 Pages `01fbd41b47e6` 的 6 个公开资源逐字节核验通过。公开目录 343 项（当前 331、历史 12），47 项仅历史已测，当前初始未测 284、全表初始未测 296；最新标记 GU-26。既有编号与人工结果保持，自动化不替用户勾选。新增建模、Skin/Skeleton、UV 算法继续暂停。

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
3. [构建与交付](BUILD_AND_DELIVERY.md)、[当前快照](compatibility/2026-10-11-compact-companion-preview-snapshot.json)：命令、源码与发布版本关系；早期发布验收仅用于对应历史包。
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

先读 [本批验收](compatibility/2026-10-11-compact-companion-acceptance.md) 和最新 CHANGELOG，核对固定 upstream `754ebe3c4b4e1402a159df6e1e58823cc93ef887` 及源码/native `7ebc757ae0826bce1506174f14e639344553423e` 的包指纹，再运行输入与菜单导出的 `--check`。本批只缩小 companion 列表及级联，保留方向按钮、Views、普通菜单和已交付 UI/输入行为，不重复实现，也不恢复新算法。

当前输入导出为 58 默认命令、60 条含别名绑定、7 个操纵器辅助入口、3 个原生模态持键入口、499 条原生继承、45 条移除、187 个受保护 keymap；基准/生成 keymap 为 281/282。原 18+2 输入参考已闭合；原生继承不宣称 Maya 等价。

- 当前上下文入口：`context_conversion_hotbox.py`、`edit_preselection.py`、native hotbox；确认组件后才写选择，终结回调处理独立原生模态取消，不通过 Python 定时器写回旧 BMesh。
- 持键入口：`history_hotbox.py`、`AXM_history_hold.hh`、`transform_axismeld_snap.cc/.hh`。A 的动作延后至 A 释放，旧队列绑定原目标；临时吸附归一次 TransInfo，不持久写入用户设置或 Redo。
- 菜单入口：`workspace_menu_catalog.py`、原生 UI 宿主及本批菜单审计；保持批准的七根/两根、灰项、右侧齿轮、真实原生 provider 和插件回调。
- File 入口：只开放 `file.open` / `file.save_as`，无默认快捷键，保留独立 Options 灰占位。精确 token 穿过未保存场景/修改图像确认，只绑定对应文件选择器；取消、失焦和窗口销毁不能残留松键所有权。不得替换为全局拦截或绕过确认，见 [File 设计](development/2026-10-11-file-window-release-design.md)。
- 本批实际事件 suites：hotbox-repost、context-entries、tools、history-hotbox、full-menu-lifecycle；另有 1 组新增 compact-companion 新旧像素比较，覆盖 100%/150% 与 Mapping 级联。既有主干批次更广矩阵保留在历史验收，不转记为本批重跑；当前完整范围见本批验收。

D/C/F12/1/2/3 及 Shift+J 的缺口分别涉及独立枢轴、曲线最近点、UV 选择域、可恢复预览和相对吸附，不用近似操作冒充完成。独立 Vertex Face、Isolate 动态书签提供器、Skin/Skeleton/建模/UV 新算法继续后置，Global 缩放继续搁置。

公开目录 343 项（当前 331、历史 12），47 项仅历史已测，当前初始未测 284、全表初始未测 296；最新标记 GU-26。既有编号与人工结果保持，自动化不替用户勾选。网页勾选属于各访客浏览器，GitHub Issue 才是共享反馈。

后续优先处理新构建的具体 UI/输入反馈与显示/手感验收，保留已通过的实现和回归。阶段收敛后先向用户报告范围与限制，恢复功能开发须由用户决定，不自动回到旧 A2 队列。

## 6. 每批如何交付

按 [AGENTS](../AGENTS.md) 更新设计、CHANGELOG 和有变化的测试条目，执行相称验证，再 commit/push 并核验远端 SHA；用户已授权每批开发完成上传 GitHub，不需要重复确认。未通过的必要检查不得用“已完成”掩盖。

Pages 只同步前端运行资源；先验证源码/包/解压启动，再发布新版并核对匿名下载和线上字节。完整 [Compact companion preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-compact-companion-preview) 已发布；源码/native `7ebc757ae0826bce1506174f14e639344553423e`，基于 Blender 5.4 Alpha。ZIP 303,157,268 字节，SHA256 `47b59ad6547b23eb045e52f1dbfed2f8b8f57069169caa98b6f4bd33e127d113`；EXE SHA256 `dff87613bb00e70594023312a0cd401ab8b8dd599fdd7fdf4a509f8cdfa34cdf`。候选、本地解压包及匿名下载解压包工厂启动通过；本地解压包的列表 GUI 也已通过。[发布快照](compatibility/2026-10-11-compact-companion-preview-snapshot.json)保存精确指纹。旧预览包保留。本批 Pages `01fbd41b47e6` 的 6 个公开资源逐字节核验通过。

历史 A1 另发的 Skin weights 预览包（Python 源码 bf35ab393b7c）复用 Rigging native，旧 tag 和历史测试结果保持；对应记录为 compatibility/2026-09-17-skin-weights-snapshot.json。

9 月 18 日新环境曾从 `33dd3a3e591b` 完成原生构建和指定测试，当时没有另发该 native 的 ZIP；这段历史不代表本批 GUI preview 未发布。步骤与限制见 BUILD_AND_DELIVERY。固定旧 native 的 Python 打包器不适用于包含本轮 CMake 改动的 HEAD，不能因只计划修改 Python 就绕过它的源码白名单。

若新机器无法登录 GitHub，可先完成本机可验证工作并准确说明推送阻碍；不要向用户索取令牌粘贴进对话或文档。使用该机器已有的 Git/凭据管理器或用户自行登录。

给另一台 Codex 的完整文本见 [CODEX_HANDOFF_PROMPT](CODEX_HANDOFF_PROMPT.md)。
