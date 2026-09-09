# AxisMeld

**Maya-style modeling workflow, built on Blender.**

AxisMeld 是一个基于 Blender 开发、完全非盈利、自由开源的独立项目。它以 Maya 2026 默认交互为公开基线，在尽量保持 Blender 上游兼容性的前提下，改进快捷键、操作逻辑、热盒、视图导航、建模和 UV 编辑体验。

除继承的 Blender 上游代码和第三方依赖外，AxisMeld 的全部新增代码、测试、构建脚本及项目文档均由 AI 完成；人类负责提出目标、制定需求、进行取舍与最终验收。

AxisMeld 官方版本永久免费，不销售软件，不设置付费功能，也不向维护者分配利润。项目可以接受公开透明、仅用于构建、托管、测试设备和维护成本的捐赠。非盈利是官方项目的运营承诺，不限制用户依据 GNU GPL 将软件用于个人、教育或商业创作。

AxisMeld 与 Blender Foundation、Autodesk 及其产品均无隶属、合作、赞助或官方背书关系。Blender、Autodesk 和 Maya 等名称仅用于事实性说明软件基础及兼容目标。

当前正在本地验证 Phase 1.1 操纵器交互和 Phase 2B Maya 风格热盒；两者均仍待人工验收。
详见 [AxisMeld 架构设计](docs/design/2026-09-08-axismeld-architecture.md)。

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

File/Edit/Create and most Modeling/UV directories remain visible but disabled; they are not claims
of implementation. Temporary snapping/pivot gestures and the UV overhaul remain planned work.
Automated validation is complete, but physical Maya-like handfeel (including adapted exponential
dolly sensitivity) still requires user acceptance before release.

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
