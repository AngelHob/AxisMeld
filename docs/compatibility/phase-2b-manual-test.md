# Phase 2B：Maya 风格热盒人工验收

状态：自动化验证完成；B12 物理键鼠手感与视觉体验仍待人工验收，未批准发布。

## 启动正确测试版

本轮视觉验收只启动 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
保留的 `phase2b-test-install/blender.exe` 不含本轮椭圆编排与主题绘制。旧的
`phase2a-test-install/blender.exe` 不含本轮设置/Recent 产品接入。独立测试目录不保证已保存
预设，请进入 **Edit → Preferences → Keymap**，选择 **AxisMeld Maya 2026**；不要把新
exe 与当前激活的键位预设混为一件事。

生效范围仍仅为该预设下 3D View 的 WINDOW 区域、Object Mode 或网格 Edit Mode。
默认短按阈值 0.4 秒（可设 0.1–1.0，等于阈值按保持处理），中央死区 12 个逻辑像素。

## 人工验收表

| 编号 | 操作 | 预期 | 结果 |
|---|---|---|---|
| B12-1 | 在正常视口中央按住 Space 查看首层 | 总体横向椭圆编排：Common、Current Pane、中央 Recent/AxisMeld/Hotbox Controls、按原顺序折为两排的 Modeling；中心最宽，上下收窄；单按钮使用当前 Blender 字体、主题圆角与语义图标，未接入项灰显并说明原因 | 自动布局/截图通过，待视觉偏好验收 |
| B12-2 | Space+RMB 分别划向 N/E/S/W/NW/SW/SE，另试 NE 与死区 | 依次为透视/侧/前/顶/左/后/底；NE 与死区不执行；LMB/MMB 默认行为相同 | 待手测 |
| B12-3 | 点击第二行 Shading 标题后再点叶项；另从标题按住拖到叶项释放 | 点击式浏览和划选式各只执行一次；空白或禁用项释放取消 | 待手测 |
| B12-4 | 在四边和四个真实内容角打开；分别试 UI scale 1.0 与 2.0 | 指针仍是手势原点，按钮向内适配，无错误重叠；原生工具栏重叠区不被抢占 | 待手测 |
| B12-4a | 中央分别试 UI scale 1/1.25/1.5/2、主题颜色与菜单字体大小；检查 hover/disabled | 字体、图标与按钮同步缩放；主题颜色实时用于绘制；单按钮是紧凑圆角矩形；空间不足时优先可读与可达，允许放弃精确椭圆轮廓 | 待手测 |
| B12-5 | Space 与鼠标几乎同时按下并快速划选；反向释放、Esc、切模式后松键 | 快速手势无需等 0.4 秒；取消不执行；残留 Space/鼠标释放不触发播放或第二次命令 | 待手测 |
| B12-6 | 在 Hotbox Controls 中分别改 LMB/MMB/RMB 为另一菜单或 Disabled | 下一次 invoke 使用新映射；三键互不串位；Preferences 显示同一值 | 待手测 |
| B12-7 | 修改样式 rows/zones/center、透明度与三行显隐，重载预设并重启测试版 | 开启文件覆盖时差异保存在 `hotbox_user.json` 并恢复；旧 schema-1 按键编辑不变 | 待手测 |
| B12-7a | Center Zone Only 下在 A 点按 Space，移到远处空白 B 点再按 RMB 划选；另试三键映射、null 和已展开菜单 | 整片非菜单 WINDOW 区使用中央映射，以 B 点为划选原点；菜单/禁用/分隔/滚动矩形优先；rows/zones 空白不启用此行为 | 待手测 |
| B12-8 | 关闭 Use Studio and User Profile Files 后再改 Controls 并 Reload | 界面提示 Session only；本次会话保留，但不改磁盘；显式清空/重启后回到基线 | 待手测 |
| B12-9 | 新进程检查 Recent，再连续成功执行多个热盒叶命令，打开 Recent 并点第一项 | 空历史禁用并显示原因；有历史启用，最新命令在首位、去重且最多 10 项；点击前重新检查当前可用性，失败不改历史 | 待手测 |
| B12-10 | 短按 Space 两次；在四视图各导航后最大化/恢复 | 单/四视图只切一次，各窗格姿态与 BOXCLIP 安全行为保持 | 待手测 |
| B12-11 | 短按 Space 进入四视图并停留；鼠标依次进入四个子视窗，各按 W/E/R，先直接拖轴，再点单轴后在同窗空白处 MMB 拖动；最后切回单视图测试 Esc 与 Undo | W 移动、E 旋转、R 缩放；三个新增子视窗不被普通抓取抢占，单轴点击保持激活 | 旧版已复现失败；新版自动化通过，待人工复测 |
| B12-12 | Alt+RMB 向右/下、左/上及双轴拖动；分别试透视、正交、四视图 | 右/下拉近，左/上拉远；双轴叠加，投影和四视图同步/裁剪保持 | 待手测 |

## 已知边界

- 指数 dolly 灵敏度是 AxisMeld 为方向与稳定性做的适配，不是 Maya 数值一致性声明；自动化不能证明物理鼠标手感或卡顿已解决。
- File/Edit/Create、Lighting/Show/Renderer、绝大多数 Modeling 与全部 UV 叶功能仍未接入；灰色目录只是稳定入口规划。
- Recent 不监听全局历史、不保存文件路径或对象引用，并在退出程序后清空。
- 跨新窗口的残留释放隔离仍是独立已知失败；文件/新窗口命令因此保持禁用。同窗口弹窗转交已通过自动化。
- 独立 stage 的 `bpy.app.build_hash` 因 `WITH_BUILDINFO=OFF` 显示 `Unknown`；源码与可执行文件身份以报告中的 Git 提交和 SHA-256 为准。

自动化证据与哈希见 [Phase 2B 验证报告](phase-2b-report.md)。只有本表人工通过后，才能写“体验验收通过”。

本轮视觉补充证据见 [视觉验证说明](../design/2026-09-10-hotbox-visual-verification.md)。
