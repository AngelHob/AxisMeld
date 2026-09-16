# AxisMeld

基于 Blender 的 Maya 风格建模工作流，免费、非盈利、自由开源。

## 公开试用

- [打开公开测试清单](https://angelhob.github.io/AxisMeld/)：查看完整测试步骤，记录自己的结果，提交 GitHub 反馈。
- [下载 Windows x64 便携预览版（Rigging 工作区）](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-rigging-preview)：完整解压后运行 `AxisMeld-Preview.cmd`。
- [查看反馈与测试结果](https://github.com/AngelHob/AxisMeld/issues?q=is%3Aissue+label%3Atest-feedback)。
- [当前开发源码](https://github.com/AngelHob/AxisMeld/tree/axismeld/phase-2a)。
- [修改日志](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CHANGELOG.md)。

建模顶栏保留 7 项，Vertex / Edge / Face 位于 Edit Mesh 内；原生工具、插件入口和右侧参数齿轮保留。灰色项表示尚未适配，开发预览版仍需人工测试。

Rigging 工作区采用 Modeling 的三栏布局，Skeleton / Skin 保留 Maya 的 82 条功能和 33 个 Options 占位，并收纳 Blender 原生骨架、绑定、权重与姿态功能。旧文件可用顶部 + → General → Rigging 添加；新增人工验收 RG-07 至 RG-14。

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
> See [the documentation](https://developer.blender.org/docs/handbook/contributing/using_git/#github-mirror) for full instructions.

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
