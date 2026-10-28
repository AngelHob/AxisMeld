# AxisMeld

**Maya-style modeling workflow, built on Blender.**

AxisMeld 是一个基于 Blender 开发、完全非盈利、自由开源的独立项目。它以 Maya 2026 默认交互为公开基线，在尽量保持 Blender 上游兼容性的前提下，改进快捷键、操作逻辑、热盒、视图导航、建模和 UV 编辑体验。

除继承的 Blender 上游代码和第三方依赖外，AxisMeld 的全部新增代码、测试、构建脚本及项目文档均由 AI 完成；人类负责提出目标、制定需求、进行取舍与最终验收。

AxisMeld 官方版本永久免费，不销售软件，不设置付费功能，也不向维护者分配利润。项目可以接受公开透明、仅用于构建、托管、测试设备和维护成本的捐赠。非盈利是官方项目的运营承诺，不限制用户依据 GNU GPL 将软件用于个人、教育或商业创作。

AxisMeld 与 Blender Foundation、Autodesk 及其产品均无隶属、合作、赞助或官方背书关系。Blender、Autodesk 和 Maya 等名称仅用于事实性说明软件基础及兼容目标。

## 当前开发与接续（2026-10-29）

最新功能分支为 `axismeld/phase-2a`，默认 `axismeld/integration` 尚未集成。

**当前交付（2026-10-29）：Transform / Modifiers 属性导航预览已发布并核验。** 在现有界面中打开 Blender 原生变换与修改器属性，保留中英文显示、18px 伴随列表与现有交互；不增加建模算法。 [下载完整预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.29-property-navigation-preview)；功能/native 源码 `45a5a51a01925164f11dcf4ce1ecbb8be217dced`，固定 Blender 5.4 Alpha upstream `754ebe3c4b4e1402a159df6e1e58823cc93ef887`。

10 组 127 项针对性 Python、当前真实事件 hotbox-repost、最终安装和独立解压副本各 14 项 GUI、本地网站 14 项浏览器检查通过。完整包 6,533 文件、154 选定资源，stage/extract、匿名下载和公开包工厂启动通过。ZIP 280,173,712 字节，SHA256 `88c3a3728bed8f3d83fd6229545a06493c071ffc4e458b27c482cff048027858`；EXE SHA256 `e85cc631490981c0a4893ffd6fe60b4bc70c2534108c21c181219c86772a74a4`。本批为 Python 改动且 buildinfo OFF，EXE hash 与双语基线相同；如实记录，不称独立可复现重编证明。

公开目录 400 项（当前 386、历史 14），47 项仅为历史已测；当前初始待测 339、全表初始待测 353。本批新增 PN-01～PN-06，六项均待人工；既有编号与人工结果保留。

实际 GUI 验证覆盖原生 RNA 属性与 operator/Undo：最终安装候选 14 项、独立解压运行副本 14 项通过；物理 F3 键盘搜索和字段鼠标编辑未自动化，仍待人工。启动截图存在覆盖视窗的启动模态框，不能据此宣称全部视觉布局已验清。

继续 UI、交互与 Maya 2026 默认快捷键优先；新增建模、Skin/Skeleton、UV 算法暂停。后续可按用户反馈改进既有 Options 体验，不自动开启新算法开发。

公开 Pages 本批六资源已逐字节核验通过，提交 `22f6ad60ddac2261e44ac26e64540dc8b390f74b`；最终网站配置下 14 项浏览器检查通过。 详见[本批验收](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-29-property-navigation-acceptance.md)与[发布快照](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-29-property-navigation-preview-snapshot.json)。

当前人工维护且按入口分组的 tools/testing_site/catalog.json 是公开目录权威来源。不要运行旧 tools/utils/axismeld_public_test_catalog.py 导出：它遗漏多段 BI 编号和新组，会把当前目录回退；同步维护人工 ledger 与按入口索引。

默认 Blender 键位、Layout 和英文；简中在 Preferences → Interface → Language 选择，Maya 流程选择 AxisMeld Maya 2026 键位后进入 Modeling/Rigging。

前批双语界面与迁移的日期证据保留于[双语验收](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/2026-10-13-bilingual-ui-acceptance.md)，不当作本批新测。

[路线图](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/ROADMAP.md) · [问题](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CURRENT_ISSUES.md) · [接续](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/HANDOFF.md) · [构建交付](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/BUILD_AND_DELIVERY.md) · [公开测试页](https://angelhob.github.io/AxisMeld/)

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
Compatible bindings. [Activation, mapping differences and profile format](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/maya-mapping/phase-1.md).

## Phase 1.1 transform-axis interaction

In the Maya preset, click a Move/Rotate/Scale single-axis handle to keep it selected, then
middle-drag in empty viewport space. Native transform operators retain confirmation, cancellation
and undo; direct handle dragging and Alt navigation remain available. Axis state is transient and
viewport-local. [Usage and manual acceptance checklist](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/maya-mapping/phase-1-1.md).
Real simulated-event tests cover object transforms, repeated drags, cancellation/undo, mesh editing,
tool/mode changes and preset isolation. Physical mouse feel and reported stutter still need user acceptance.

## Phase 2B Maya-style hotbox

The opt-in AxisMeld Maya 2026 preset now has a native Space hotbox in the 3D View WINDOW for
Object and mesh Edit Mode. A short tap toggles single/quad view; hold shows the actual Common,
Current Pane, center and Modeling rows. The three center mouse buttons default to a seven-direction
view marking menu. Click/drag submenus, session-only Recent Commands, display style/transparency,
row visibility and per-button menu mappings are connected. Preferences and Hotbox Controls share
the same validated settings model; user differences are atomically stored in `hotbox_user.json`
without changing schema-1 keybindings. [Scope and manual acceptance](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/compatibility/phase-2b-manual-test.md).

Subsequent batches added tool/context hotboxes, modeling command mappings, companion menus,
native modeling groups and a Rigging workspace. Unsupported Maya actions remain disabled;
menu visibility does not claim algorithm parity. See the current [roadmap](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/ROADMAP.md)
and [issues](https://github.com/AngelHob/AxisMeld/blob/axismeld/phase-2a/docs/CURRENT_ISSUES.md). Physical handfeel, production deformation quality and
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
