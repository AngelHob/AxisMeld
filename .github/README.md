# AxisMeld

基于 Blender 的 Maya 风格建模工作流，免费、非盈利、自由开源。

## 公开试用

- [打开公开测试清单](https://angelhob.github.io/AxisMeld/)：查看完整测试步骤，记录自己的结果，提交 GitHub 反馈。
- [下载 Windows x64 便携预览版（热盒下方列表 16 像素，Blender 5.4 Alpha）](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-16px-companion-preview)：完整解压后运行 `AxisMeld-Preview/blender.exe`。
- [查看反馈与测试结果](https://github.com/AngelHob/AxisMeld/issues?q=is%3Aissue+label%3Atest-feedback)。
- [当前开发源码](https://github.com/AngelHob/AxisMeld/tree/axismeld/phase-2a)。
- [修改日志](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CHANGELOG.md)。
- [整体规划与路线图](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/ROADMAP.md) · [当前问题](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CURRENT_ISSUES.md)。
- [换机开发说明](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/HANDOFF.md) · [复制给 Codex 的接续提示词](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CODEX_HANDOFF_PROMPT.md)。

开发请使用 **`axismeld/phase-2a`**；默认 `axismeld/integration` 目前只同步公开入口，尚未包含最新开发功能。

首次为 Blender 键位与 Layout；在 Edit → Preferences → Keymap 选择 **AxisMeld Maya 2026**，再切 Modeling 或 Rigging。仅将热盒下方伴随列表及其级联普通行高设为 16 逻辑像素（100% 界面缩放），Options 宽 16、细分隔 4；文字、图标、列宽和留白沿 16/24 的局部比例同步，高 DPI 保持 Blender 界面缩放规则；周围方向按钮、四视图间隔、主热盒栏及普通原生菜单保持原尺寸。完整条目、底部避让和说明无空间时隐藏的规则保持，不折叠、不滚动，不随窗口继续缩小。公开目录 344 项（当前 331、历史 13），47 项仅历史已测，当前初始未测 284、全表初始未测 297；最新标记 GU-27。既有编号与人工结果保持，自动化不替用户勾选。新算法继续暂停。

6 组 42 项相关 Python、2 组 114 项原生、3 组既有 GUI 回归与 1 组本批列表几何验证通过；源码/native `89fec688b9dd2f0c95f6a814488cd70733b29893`。匿名下载、干净解压及工厂启动已核验；[验收](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-11-16px-companion-acceptance.md)与[快照](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-11-16px-companion-preview-snapshot.json)保存实际范围和指纹。本批 Pages `43d73f2bff6c` 的 6 个公开资源逐字节核验通过。

建模顶栏保留 7 项，Vertex / Edge / Face 位于 Edit Mesh 内；原生工具、插件入口和右侧参数齿轮保留。灰色项可能表示当前上下文不满足条件或尚未适配，悬停查看原因；开发预览版仍需人工测试。

Rigging 工作区采用 Modeling 的三栏布局，Skeleton / Skin 保留 Maya 的 82 条功能和 33 个 Options（其中已适配 2 条一次性权重操作及其 Options），并收纳 Blender 原生骨架、绑定、权重与姿态功能。旧文件可用顶部 + → General → Rigging 添加；新增 Skin 人工验收 RG-15 至 RG-20；RG-07 至 RG-14 仍待测。

Rigify 默认内置，无需安装或启用插件。通过 Add → Armature → Rigify Meta-Rigs 创建骨架，设置位于 Edit → Preferences → Animation → Rigify；外部 Feature Sets 保持用户选择。

测试页和下载公开可访问。各访客的网页勾选保存在自己的浏览器，可导出记录；实际提交反馈需登录 GitHub，不会把浏览器本地勾选自动当作公开测试结果。

AxisMeld 与 Blender Foundation、Autodesk 均无隶属或官方背书关系。软件和衍生源码沿用原开源许可证，许可证随便携包提供。

## Blender 上游说明

<!--
Keep this document short & concise,
linking to external resources instead of including content in-line.
See 'release/text/readme.html' for the end user read-me.
-->

> [!IMPORTANT]
> Cloning from this [GitHub mirror](https://github.com/blender/blender) may cause Git LFS errors. To avoid this, use `GIT_LFS_SKIP_SMUDGE=1` when doing your initial clone.  
> See [the documentation](https://developer.blender.org/docs/handbook/contributing/using_git/clone_update/#github-mirror) for full instructions.

Blender
=======

Blender is the free and open source 3D creation suite.
It supports the entirety of the 3D pipeline—modeling, rigging, animation, simulation, rendering, compositing,
motion tracking and video editing.

![Blender screenshot](https://code.blender.org/wp-content/uploads/2018/12/springrg.jpg "Blender screenshot")

Project Pages
-------------

- [Main Website](http://www.blender.org)
- [Reference Manual](https://docs.blender.org/manual/en/latest/index.html)
- [User Community](https://www.blender.org/community/)

Development
-----------

- [Build Instructions](https://developer.blender.org/docs/handbook/building_blender/)
- [Code Review & Bug Tracker](https://projects.blender.org)
- [Developer Forum](https://devtalk.blender.org)
- [Developer Documentation](https://developer.blender.org/docs/)


License
-------

Blender as a whole is licensed under the GNU General Public License, Version 3.
Individual files may have a different but compatible license.

See [blender.org/about/license](https://www.blender.org/about/license) for details.
