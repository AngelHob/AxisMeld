# AxisMeld 修改日志

每批开发完成时更新本文件并与代码一起推送 GitHub。记录功能与修复、验证结果、待人工测试编号；历史日志保留。

## 2026-09-17 · Rigging 独立工作区

- 默认启动布局新增 Rigging，采用 Modeling 的 3D View、Outliner、Properties 布局，保留原 11 个工作区和默认 Layout；旧文件与个人 startup 不自动插入页面，可用原生 `+ → General → Rigging` 添加。
- Rigging 视窗提供 Skeleton / Skin，Blender 与 Maya 键位均可使用；工作区改名、复制后通过用途标记保留菜单。原生全局栏和 Modeling 的七个根菜单保持。
- 完整保留 Maya Skeleton / Skin 的 82 条正文、33 个独立 Options、原顺序和层级；未适配算法仍为灰色占位。新增 9 个原生入口，将骨架创建、Rigify、骨骼编辑、IK、Pose、绑定、权重和顶点组收进对应章节，不把相似操作冒充 Maya 实现。
- 复用真实原生菜单宿主，保留参数、执行上下文、资产和插件回调；补齐原生普通条目的缺省 Blender 图标，保留显式图标和 RNA 枚举行。修复本地对象引用链接骨架数据时 Pose、IK 和绑定目标被错误禁用的问题。
- 默认资产通过原生工作区激活建立窗口关联，避免仅普通 blend 可打开而内嵌工厂启动崩溃；重新编译可执行文件，工厂启动已通过。57 项菜单测试通过，独立核对 115 个 Maya 条目无缺失、重复或原内容变化，原建模目录 392 条映射保持。
- 无有效对象或模式时，原生入口显示灰色标签，避免灰色子菜单被预览时错误读取空对象；删除工作区时先解除自身屏幕引用，再释放该用户，修复工作区带自定义属性时屏幕用户被二次递减的问题。
- 最终运行验证：8 个独立 Blender 进程及原始布局关系检查通过；GUI 实际创建 29 骨 Basic Human、绑定与一次 Undo、Normalize 与一次 Undo、三个原生插件菜单宿主、添加/改名/删除工作区及独立进程重开通过。139 项运行资源与源码一致。
- 默认布局文件约 128 KB，单独改为普通 Git 二进制存储，避免 GitHub 公开 fork 拒绝新 LFS 对象导致源码无法获取；仅调整这一文件的属性，资产内容不变。
- 新增待人工测试 RG-07 至 RG-14；复杂变形质量、第三方扩展和不同显示缩放仍需用户验收。设计见 [Rigging 独立工作区](development/2026-09-17-rigging-workspace.md)。
- 发布 [Rigging 工作区 Windows x64 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.17-rigging-preview)，对应源码 `617986ac1841`；独立解压与实际启动通过，GitHub ZIP SHA256 与本地一致。测试清单共 308 项，当前 296 项，最近新增 8 项；原 300 项和 47 条历史已测状态保留。

## 2026-09-15 · Rigify 默认内置

- Rigify 移入原生模块目录，由 Blender 启动脚本加载，工厂配置和普通启动均可直接使用；插件管理不再显示、启停或重复加载 Rigify。
- 设置入口位于 Edit → Preferences → Animation → Rigify；保留 metarig、生成器、骨架 RNA 和旧偏好存储，外部 Feature Sets 保持用户选择。
- 修复重载脚本时残留的版本升级回调；补齐偏好重读前后的外部扩展注销/注册，以及初始化失败后的清理和恢复。
- 验证：40 项菜单与插件隔离测试通过，6 个独立进程场景通过；Basic Human 实际生成 222 根骨骼、80 根控制骨和 209 个约束，保存重开数据一致；已启用/禁用/未记录 Feature Sets 的状态与回调次数已核对。
- 实际 GUI 验证通过：原生菜单创建 Basic Human、生成 Rig、Animation 中设置面板，以及插件列表没有 Rigify 或缺失提示；136 项运行资源与候选源码一致。
- 待人工测试：RG-01 至 RG-06，包含原生入口、生成操控、保存重开、旧设置、设置面板和脚本重载。清单共 300 项，保留原编号与历史结果；第三方骨架扩展和变形质量仍需人工验收。
- 本轮仅修改 Python 模块和界面脚本，沿用已验证的原生可执行文件；设计见 [Rigify 默认内置模块](development/2026-09-15-rigify-builtin.md)。
- 9 月 16 日发布 [Windows x64 内置 Rigify 预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.15-rigify-preview)，对应源码 `3a673dcf1e078`；重新解压启动通过，GitHub 资产 SHA256 与本地 ZIP 一致。公开测试页与仓库首页下载入口同步至此版本。
- 发布后匿名资源核验与 6 项线上浏览器验收通过，下载、RG 记录持久化、独立访客和反馈版本正确；未提交测试 Issue，原人工结果保持。

## 2026-09-15 · 固定开发交付流程

- 将“开发完成后提交并推送 GitHub，同时更新修改日志”写入项目规则，作为已获用户授权的固定流程。
- 建立本日志入口；本次仅修改文档，检查了差异和链接，无新增功能测试项。

## 2026-09-15 · 紧凑建模菜单与公开测试

- Vertex、Edge、Face 收入 Edit Mesh；建模栏保留七个根菜单，原功能、参数齿轮和插件入口保留。
- 发布[公开测试页](https://angelhob.github.io/AxisMeld/)与 [Windows 便携预览版](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.09.15-modeling-preview)，支持浏览器记录、JSON 导出及 GitHub Issue 反馈。
- 清单保留 294 个编号，12 项已替代方案归入历史；维护者的历史已测与访客自己的结果分开保存。
- 验证：105 项针对自动测试、实际 Blender GUI 操作与撤销、试用包重新解压启动、12 项本地浏览器检查和 6 项线上验收通过。
- 待人工测试：MB-40（组件子菜单和紧凑栏）、MB-41（公开下载、试用与反馈）。其余未测项沿用[测试清单](compatibility/2026-09-14-manual-test-ledger.md)，自动化结果不替代人工结果。
- 对应提交：建模与试用包 `7246459183c4`；公开门户 `b2fa955d24e7`。
