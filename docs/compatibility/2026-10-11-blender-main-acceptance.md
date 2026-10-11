# Blender 5.4 主干同步验收

日期：2026-10-11。状态：固定主干合并、新构建回归与预览发布已完成；自动证据不代替人工验收。

## 固定基线与合并范围

- 合并前 AxisMeld：`bbce9d3483432f30eff1cc94b61d08838eba25eb`。极低窗口修复已独立发布，源码/native `665cb38b123d89d273d6f68e2c748a258abfff47`。
- 官方 Blender main：`754ebe3c4b4e1402a159df6e1e58823cc93ef887`，5.4.0 Alpha；共同基线 `18d84097b4f859582afdec57eece2ae880371adc`，新增 982 个上游提交。
- Windows x64 库：`aa0c5db72fa9488bb685bdddbede780d19f483f5`。仅切换此平台的精确 gitlink，没有执行浮动依赖更新或变基。
- 采用保留父提交的 merge，目标为 `axismeld/phase-2a`。默认 `axismeld/integration` 只同步首页，不合并开发功能。

唯一文本冲突位于 `wm_window.cc` 的两段窗口标题代码：保留上游 `fmt::memory_buffer` 接口和调用方终止符，在原位置输出 AxisMeld 产品名与版本。自动合并不等于兼容性已经验证，WM 文件窗口、菜单回调所有权、变换与原生菜单来源另行检查。

原生 Project 设置采用上游 `screen.project_settings_show` 与条件全局 Project 菜单。两项新的 Loop Tools 操作由既有 Edit Mesh → Transform 原生来源继承，不增加新的 Modeling 根菜单，不启动新的 Maya 算法适配。

## 输入与菜单目录

本次重生成后仍为 58 个默认命令、60 条含别名绑定、7 个操纵器辅助入口、45 条原生移除；原生继承 497 → 499，受保护 keymap 186 → 187。新增继承来自 Grease Pencil Carver 的原生 LMB/MMB，不改 Maya 冻结参考。菜单 routes 的 392 个声明条目、七个 Modeling 根及内容保持，仅更新四个原生来源文件指纹。

首轮 42 组纯 Python 测试暴露了顶栏测试未提供上游新增 `bpy.data.project` 上下文；生产模块已有正常导入。补齐有/无 Project × Maya 开/关四种断言后，42 组 415 项通过。此结果尚不是最终新构建或发布验证。

## 回归清单修正

本次误纳入的 `workspace-bar` 明确属于历史双排全局菜单方案；它要求第二排高度，实际失败截图显示当前单排原生栏符合已确认设计。保留 FAIL 原回执与截图，不恢复旧布局；当前 `modeling-viewport` 已实际验证原生全局栏、工作区真实往返、七根 Modeling 视窗菜单及 Layout 恢复。本次适用 GUI 清单为 15 组，不把历史方案失败改写为通过，也不宣称所有编辑区几何逐像素验证。

后台输入测试另发现历史断言遗漏已冻结的 Redo 别名和模式外原生 fallback。合并前后的生产命令、生成器及旧测试均相同；只更新测试以逐事件和目标 keymap 验证，保留首次失败与诊断，不为迎合旧断言改变生产键位。

## 构建与交付门禁


- [x] Windows 精确库 checkout、LFS fsck 与 1,239 个唯一对象长度/SHA256 校验通过，子模块干净。
- [x] 当前 index 的 360 项构建 LFS 资产已落盘并核验；补齐七个缺失对象后，assets/release/scripts/startup 中无残留指针。AxisMeld 自定义 startup.blend 普通 Git 内容保持。
- [x] 全新 `D:/source/AxisMeld-build-main-754ebe3c4b4e` 配置完成，使用完整功能预设、Release、CRT、原生测试和 Jolt；不复用旧 5.3 缓存或可执行文件。

- 42 组 415 项纯 Python、8 组 144 项原生，另有 4 组 CLI（profiles 18 项、Blender input 11 项；profiles 与纯 Python 重合，不累加），15 组 GUI 回归、5 组 bpy 功能及 factory、5 个说明矩阵组合全部通过；GUI 与说明矩阵分别计数。
- GUI suites：modeling-viewport、menu-shortcuts、menu-options-navigation、menu-options-access、menu-options-geometry、modeling-disabled-reason、hotbox-repost、context-entries、temporary-snap、history-hotbox、tools-modifiers、tools、full-menu-lifecycle、file-window、release-cross-window。
- 145 项资源、6,572 个发行文件通过静态审计；解压包 factory/说明 GUI 与匿名下载 factory 通过。
- 本地网站静态/状态检查及 12 项浏览器检查通过；Pages 实际字节核验见下方交付。
- 输入现状：58 默认命令、60 条含别名绑定、7 个操纵器辅助入口、3 个原生模态持键入口、499 条原生继承、45 条移除、187 个受保护 keymap；基准/生成 keymap 为 281/282。

| 实际目录 | 窗口 / 缩放 | 验证范围 |
| --- | --- | --- |
| `reason-low-100` | 840×480 / 100% | 完整说明、菜单零交叠 |
| `reason-low-150` | 840×480 / 150% | 完整说明、菜单零交叠 |
| `reason-wide` | 1200×800 / 150% | 完整说明、菜单零交叠 |
| `reason-quad` | 1920×900 / 150% | 完整说明、菜单零交叠；四视图偏移 |
| `reason-no-fit` | 720×480 / 150% | 无完整空白时隐藏；放大后同一说明恢复 |

完整回执位于本机 `D:/source/AxisMeld-build/gui-2026-10-11-upstream-main-audit/`；这是审计路径，不是公开下载资产。

## 发布与交付

完整 [Blender main preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-blender-main-preview) 已发布；源码/native `7beedde071ca5eaa8fce6090f01cf2ddd40b6804`，基于 Blender 5.4.0 Alpha。ZIP 303,157,226 字节，SHA256 `f3692f9813cb6c7d144a371e42768229591b89ca5944671a8c886e62d4ae0a52`；EXE SHA256 `0a4de344f93bafcea9414668746fe1fa0d2fec5dd1bc0b62d86ae3a9acbd56a9`。6,572 个发行文件、145 项选定资源通过干净解压审计；解压包 factory 和实际说明 GUI、匿名重下载后的校验/解压/factory 已通过。本地网站 12 项浏览器检查通过，Pages `9fc6257e35e4` 的 6 个公开资源逐字节核对通过。[发布快照](2026-10-11-blender-main-preview-snapshot.json)保存精确指纹。旧预览包保留。

## 待人工

GU-22 保留极低窗口说明验收；GU-23～GU-25 分别覆盖 5.4 菜单目录、持键/文件窗口、Rigging 与旧场景副本。目录共 342 项、当前有效 330、历史方案 12；47 项历史已测保持，当前初始待测 283。所有新增项均为待人工，自动化不替用户勾选。

仍暂停新增建模、Skin/Skeleton 与 UV 算法；实体鼠标手感、其他机器、任意插件和 GPU 渲染不由这次 GUI 回归代替验收。
