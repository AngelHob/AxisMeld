# Blender 5.4 主干同步验收

日期：2026-10-11。状态：合并冲突、全新原生构建、候选安装与自动回归通过；完整预览包的打包和公开下载验证待完成。

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
- [x] 全新原生构建与独立安装通过；实际 5.4.0 Alpha，EXE SHA256 `0a4de344f93bafcea9414668746fe1fa0d2fec5dd1bc0b62d86ae3a9acbd56a9`，145 项受管资源一致，候选静态审计通过。
- [x] 最终纯 Python 42 组 415 项、八组原生 144 项通过；另四组 CLI CTest 通过（profiles 18 项已计入纯测试，installed-input 11 项独立）。factory 与五组 bpy 功能检查通过，Rigify 六子进程覆盖真实旧 addon 偏好迁移。
- [x] 15 组当前菜单/热盒 GUI 回归通过；低窗 100%/150%、宽窗、四视图和无位置隐藏后恢复共五组合、18 条实际观察通过。720×480/150% 不显示说明，放大到 1920×1080 后同一说明完整恢复且与菜单零交叠。
- [ ] 完整包静态审计、干净解压、实际运行、匿名下载与公开 Pages 校验。

最终结果和发布快照在取得实际回执后填写；本地完整日志位于 `D:/source/AxisMeld-build/gui-2026-10-11-upstream-main-audit/`。这是本机审计路径，不是公开下载资产。

## 待人工

GU-22 保留极低窗口说明验收；GU-23～GU-25 分别覆盖 5.4 菜单目录、持键/文件窗口、Rigging 与旧场景副本。目录共 342 项、当前有效 330、历史方案 12；47 项历史已测保持，当前初始待测 283。所有新增项均为待人工，自动化不替用户勾选。

仍暂停新增建模、Skin/Skeleton 与 UV 算法；实体鼠标手感、其他机器、任意插件和 GPU 渲染不由这次 GUI 回归代替验收。
