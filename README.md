# AxisMeld

**Maya-style modeling workflow, built on Blender.**

AxisMeld 是一个基于 Blender 开发、完全非盈利、自由开源的独立项目。它以 Maya 2026 默认交互为公开基线，在尽量保持 Blender 上游兼容性的前提下，改进快捷键、操作逻辑、热盒、视图导航、建模和 UV 编辑体验。

除继承的 Blender 上游代码和第三方依赖外，AxisMeld 的全部新增代码、测试、构建脚本及项目文档均由 AI 完成；人类负责提出目标、制定需求、进行取舍与最终验收。

AxisMeld 官方版本永久免费，不销售软件，不设置付费功能，也不向维护者分配利润。项目可以接受公开透明、仅用于构建、托管、测试设备和维护成本的捐赠。非盈利是官方项目的运营承诺，不限制用户依据 GNU GPL 将软件用于个人、教育或商业创作。

AxisMeld 与 Blender Foundation、Autodesk 及其产品均无隶属、合作、赞助或官方背书关系。Blender、Autodesk 和 Maya 等名称仅用于事实性说明软件基础及兼容目标。

## 当前开发与接续（2026-10-11）

最新开发位于 **`axismeld/phase-2a`**；GitHub 默认 `axismeld/integration` 尚未集成最新功能。
**最新交付（2026-10-11 GUI interaction polish）：两项菜单/热盒交互修复及完整原生预览包已发布。** Modeling 原生灰项显示上下文原因，并阻止无效子菜单预览；W/E/R 持键时每次 LMB 重复唤出从根目录开始。本轮通过 94 项纯 Python、42 项原生和 7 组实际 GUI。[下载新版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-interaction-preview)，源码/native 均为 `534eec00698397cc55e27f23f3575e6d4894331a`；匿名下载、干净解压及工厂启动已核验。详见[本轮验收](docs/compatibility/2026-10-11-gui-interaction-polish-acceptance.md)与[发布快照](docs/compatibility/2026-10-11-gui-interaction-preview-snapshot.json)。新增 GU-20～GU-21 待人工，GU-01～GU-19 及原结果保持；极低窗口无说明空带时可能覆盖菜单。新算法继续暂停。

本批只修 UI 与交互；保留已实现的上下文、History、临时吸附和文件窗口功能。缺失 Maya 能力继续灰显，实体鼠标和生产场景仍需人工验收。

- [整体规划与路线图](docs/ROADMAP.md) · [当前问题](docs/CURRENT_ISSUES.md) · [修改日志](docs/CHANGELOG.md)。
- [新机器接续开发](docs/HANDOFF.md) · [直接复制给 Codex 的提示词](docs/CODEX_HANDOFF_PROMPT.md) · [构建与交付](docs/BUILD_AND_DELIVERY.md)。
- [公开测试页](https://angelhob.github.io/AxisMeld/) · [Windows x64 GUI interaction 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-interaction-preview)（完整原生包，附 ZIP 校验文件）· [发布指纹与验证范围](docs/compatibility/2026-10-11-gui-interaction-preview-snapshot.json)。

Modeling 视窗保留 Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、UV；Vertex/Edge/Face 收于 Edit Mesh。Rigging 的 Skeleton/Skin 保留 Maya 82 条正文和 33 个 Options，并收纳已有 Blender 骨架、绑定、权重、姿态及 Rigify 入口。

仓库新完整便携包采用干净工厂配置，初次为 Blender 键位与 Layout。试用 Maya 流程时，在 Edit → Preferences → Keymap 选择 **AxisMeld Maya 2026**，再切 Modeling 或 Rigging；需要保留时主动保存偏好。

公开清单保留 338 项（当前 326、历史 12）；47 项只记录历史已测，当前初始未测 279、全表初始未测 291 项。本批新增 GU-20～GU-21 两项待人工，既有编号和结果保持。网页勾选保存在各访客浏览器；通过 GitHub Issue 分享结果。

下面的 Phase 0～2B 段落保留基础能力说明；后续完整进度以路线图和修改日志为准。原始架构见 [AxisMeld 架构设计](docs/design/2026-09-08-axismeld-architecture.md)。

## AxisMeld project statement

AxisMeld is an independent, completely non-profit, free and open-source project based on Blender. It aims to provide Maya-style hotkeys, interaction logic, hotbox, viewport navigation, modeling, and UV editing workflows while remaining maintainable against Blender upstream.

Except for inherited Blender upstream code and third-party dependencies, all AxisMeld-specific code, tests, build scripts, and project documentation are produced by AI. Humans define the goals and requirements, make product decisions, and perform final review and acceptance.

Official AxisMeld releases are free of charge, contain no paid features, and distribute no profit to maintainers. Transparent donations may only cover infrastructure, hosting, test hardware, and direct maintenance costs. This operating commitment does not restrict personal, educational, or commercial use permitted by the GNU GPL.

AxisMeld is not affiliated with, endorsed by, sponsored by, or an official release of the Blender Foundation or Autodesk.

## Phase 0 status

AxisMeld `0.1.0-dev` has a verified Windows 11 x64 Release build based on Blender commit
`18d84097b4f859582afdec57eece2ae880371adc`. Phase 0 retains the compatibility filename
`blender.exe`, identifies the running product as AxisMeld, and stores development preferences under
the adjacent `portable` directory. The three focused identity and isolation tests pass.

## Phase 1 input foundation

The bundled **AxisMeld Maya 2026** keymap preset is available under **Edit → Preferences → Keymap**.
It covers Q/W/E/R tools, F8–F11 mesh component modes, A/F framing, Alt+mouse navigation and
4/5 shading in the 3D View, with separate studio/user JSON overrides and conflict diagnostics.
These are adapted Blender behaviors, not full Maya parity. Other editors inherit Industry
Compatible bindings. [Activation, mapping differences and profile format](docs/maya-mapping/phase-1.md).

## Phase 1.1 transform-axis interaction

In the Maya preset, click a Move/Rotate/Scale single-axis handle to keep it selected, then
middle-drag in empty viewport space. Native transform operators retain confirmation, cancellation
and undo; direct handle dragging and Alt navigation remain available. Axis state is transient and
viewport-local. [Usage and manual acceptance checklist](docs/maya-mapping/phase-1-1.md).
Real simulated-event tests cover object transforms, repeated drags, cancellation/undo, mesh editing,
tool/mode changes and preset isolation. Physical mouse feel and reported stutter still need user acceptance.

## Phase 2B Maya-style hotbox

The opt-in AxisMeld Maya 2026 preset now has a native Space hotbox in the 3D View WINDOW for
Object and mesh Edit Mode. A short tap toggles single/quad view; hold shows the actual Common,
Current Pane, center and Modeling rows. The three center mouse buttons default to a seven-direction
view marking menu. Click/drag submenus, session-only Recent Commands, display style/transparency,
row visibility and per-button menu mappings are connected. Preferences and Hotbox Controls share
the same validated settings model; user differences are atomically stored in `hotbox_user.json`
without changing schema-1 keybindings. [Scope and manual acceptance](docs/compatibility/phase-2b-manual-test.md).

Subsequent batches added tool/context hotboxes, modeling command mappings, companion menus,
native modeling groups and a Rigging workspace. Unsupported Maya actions remain disabled;
menu visibility does not claim algorithm parity. See the current [roadmap](docs/ROADMAP.md)
and [issues](docs/CURRENT_ISSUES.md). Physical handfeel, production deformation quality and
broader display/plugin coverage remain separate manual acceptance work.

---

## Upstream Blender information

<!--
Keep this document short & concise,
linking to external resources instead of including content in-line.
See 'release/text/readme.html' for the end user read-me.
-->

Blender
=======

Blender is the free and open source 3D creation suite.
It supports the entirety of the 3D pipeline—modeling, rigging, animation, simulation, rendering, compositing,
motion tracking and video editing.

![Blender screenshot](https://code.blender.org/wp-content/uploads/2018/12/springrg.jpg "Blender screenshot")

Project Pages
-------------

- [Main Website](https://www.blender.org)
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
