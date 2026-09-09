# Phase 2B：Maya 风格热盒人工验收

状态：自动化验证完成；B12 物理键鼠手感与视觉体验仍待人工验收，未批准发布。

## 启动正确测试版

只启动 `D:/source/AxisMeld-build/phase2b-test-install/blender.exe`。旧的
`phase2a-test-install/blender.exe` 不含本轮设置/Recent 产品接入。独立测试目录不保证已保存
预设，请进入 **Edit → Preferences → Keymap**，选择 **AxisMeld Maya 2026**；不要把新
exe 与当前激活的键位预设混为一件事。

生效范围仍仅为该预设下 3D View 的 WINDOW 区域、Object Mode 或网格 Edit Mode。
默认短按阈值 0.4 秒（可设 0.1–1.0，等于阈值按保持处理），中央死区 12 个逻辑像素。

## 人工验收表

| 编号 | 操作 | 预期 | 结果 |
|---|---|---|---|
| B12-1 | 按住 Space 查看首层 | 依次显示 Common、Current Pane、Recent/AxisMeld/Hotbox Controls、Modeling；未接入项灰显并说明原因 | 待手测 |
| B12-2 | Space+RMB 分别划向 N/E/S/W/NW/SW/SE，另试 NE 与死区 | 依次为透视/侧/前/顶/左/后/底；NE 与死区不执行；LMB/MMB 默认行为相同 | 待手测 |
| B12-3 | 点击 Pane→Shading 后再点叶项；另从标题按住拖到叶项释放 | 点击式浏览和划选式各只执行一次；空白或禁用项释放取消 | 待手测 |
| B12-4 | 在四边和四个真实内容角打开；分别试 UI scale 1.0 与 2.0 | 指针仍是手势原点，按钮向内适配，无错误重叠；原生工具栏重叠区不被抢占 | 待手测 |
| B12-5 | Space 与鼠标几乎同时按下并快速划选；反向释放、Esc、切模式后松键 | 快速手势无需等 0.4 秒；取消不执行；残留 Space/鼠标释放不触发播放或第二次命令 | 待手测 |
| B12-6 | 在 Hotbox Controls 中分别改 LMB/MMB/RMB 为另一菜单或 Disabled | 下一次 invoke 使用新映射；三键互不串位；Preferences 显示同一值 | 待手测 |
| B12-7 | 修改样式 rows/zones/center、透明度与三行显隐，重载预设并重启测试版 | 开启文件覆盖时差异保存在 `hotbox_user.json` 并恢复；旧 schema-1 按键编辑不变 | 待手测 |
| B12-8 | 关闭 Use Studio and User Profile Files 后再改 Controls 并 Reload | 界面提示 Session only；本次会话保留，但不改磁盘；显式清空/重启后回到基线 | 待手测 |
| B12-9 | 连续成功执行多个热盒叶命令，再打开 Recent 并点第一项 | 最新命令在首位、去重且最多 10 项；点击前重新检查当前可用性，失败不改历史 | 待手测 |
| B12-10 | 短按 Space 两次；在四视图各导航后最大化/恢复 | 单/四视图只切一次，各窗格姿态与 BOXCLIP 安全行为保持 | 待手测 |
| B12-11 | 选择 W/E/R，点单轴后在空白处 MMB 拖动；测试确认、Esc 与 Undo | 既有 Move/Rotate/Scale 单轴工作流无回归 | 待手测 |
| B12-12 | Alt+RMB 向右/下、左/上及双轴拖动；分别试透视、正交、四视图 | 右/下拉近，左/上拉远；双轴叠加，投影和四视图同步/裁剪保持 | 待手测 |

## 已知边界

- 指数 dolly 灵敏度是 AxisMeld 为方向与稳定性做的适配，不是 Maya 数值一致性声明；自动化不能证明物理鼠标手感或卡顿已解决。
- File/Edit/Create、Lighting/Show/Renderer、绝大多数 Modeling 与全部 UV 叶功能仍未接入；灰色目录只是稳定入口规划。
- Recent 不监听全局历史、不保存文件路径或对象引用，并在退出程序后清空。
- 跨新窗口的残留释放隔离仍是独立已知失败；文件/新窗口命令因此保持禁用。同窗口弹窗转交已通过自动化。
- 独立 stage 的 `bpy.app.build_hash` 因 `WITH_BUILDINFO=OFF` 显示 `Unknown`；源码与可执行文件身份以报告中的 Git 提交和 SHA-256 为准。

自动化证据与哈希见 [Phase 2B 验证报告](phase-2b-report.md)。只有本表人工通过后，才能写“体验验收通过”。
