# M1 工具热盒集中验收

状态：M1 候选已构建并进入审查，尚未更新用户测试程序。下表人工结果全部待测。
范围：[M1 实现计划](../superpowers/plans/2026-09-11-m1-tool-hotboxes.md)；
功能对照与占位：[Maya 工具菜单对照](../maya-mapping/2026-09-11-tool-marking-menus.md)。

## 测试时的操作方式

在 3D 视口先选中一个 Mesh。点按 Q/W/E/R 仍立即选择工具；要打开工具热盒，
保持工具键按下，再按住鼠标左键，拖向目标并先松左键。仅长按工具键不会弹出菜单。
先松工具键或按 Esc 是取消路径，不应提交当次划选。

不要把本批 World/Object/Normal 方向选项当成新的变换算法：它们调用 Blender 原生方向，
先前搁置的 Object 模式 Global 缩放差异仍然存在。Paint Selection 是 Blender 圆形选择适配，
不是完整的 Maya 涂抹选择。

优先反馈 M1 编号、工具、Object/Edit 模式、单/四视图以及按键释放顺序。
人工测试请使用临时场景；个人热盒颜色和改键配置应保持原样。

## 手工测试清单

每项完成自动化后仍保留人工手感审核，不把合成事件当作实体键鼠验收。

| 编号 | 操作 | 预期 | 人工结果 |
|---|---|---|---|
| M1-01 | 分别点按 Q/W/E/R | 立即切换选择/移动/旋转/缩放；不出现额外热盒，不延迟选工具 | 待测 |
| M1-02 | 按住 Q/W/E/R，不点击鼠标 | 工具已选中，画面没有大菜单挡住视口；松键后可正常操作 | 待测 |
| M1-03 | 按住各工具键，再按住左键 | 在左键按下的位置出现对应椭圆热盒，无多余中心按钮 | 待测 |
| M1-04 | W/E/R 热盒拖向 World、Object、Normal Average；E 另测 Gimbal | 方向与对照表一致，实际操纵器方向改变；不是启动抓取/旋转模态 | 待测 |
| M1-05 | W 设 Object、E 设 World、R 设 Normal，来回切工具 | 保留各工具自己的方向；直接拖轴与点轴后空白中键拖动一致 | 待测 |
| M1-06 | Q 热盒选择 Marquee / Lasso / Paint | 进入对应 Blender 框选/套索/圆形选择工具；松 Q 后不被重置回框选 | 待测 |
| M1-07 | Object 和 Mesh Edit 分别使用 Clear Selection | 只清空当前可操作选择集合，不自动切换模式；一次撤销恢复 | 待测 |
| M1-08 | 从热盒拖入 Select / Axis 等普通设置菜单，再横穿背景其他按钮 | 原热盒仍显示，背景不抢选择，级联贴边，释放只执行一次 | 待测 |
| M1-09 | 拖到未实现项释放 | 不修改模型、不生成撤销或 Recent，缺口能在计划表定位 | 待测 |
| M1-10 | 左键先松、工具键先松、Esc、切出窗口，各测一次 | 正确提交或取消，没有粘住的菜单/鼠标；回到视口原地 Q/W/E/R 正常 | 待测 |
| M1-11 | 长按键自动重复、快速 W/E/R 切换、Alt 导航 | 不重复打开，不误弹菜单，不阻断轨道/平移/缩放 | 待测 |
| M1-12 | 在 Object / 点 / 边 / 面、单视图 / 四视图重复核心步骤 | 命令上下文正确，不误切工具、不旋转锁定的标准正交视图 | 待测 |
| M1-13 | Space → Modify → Tool Settings → 对应工具菜单 | 与键盘入口功能一致；原 Space 热盒中央视图和设置仍正常 | 待测 |
| M1-14 | 使用个人改键和禁用项后重启 | 触发跟随实际改键，旧键不留下释放监听；原个人外观配置不变 | 待测 |
| M1-15 | 在 UV、文本输入、非建模模式操作同一按键 | 本批建模热盒不抢输入、不改 UV 功能 | 待测 |

## 自动化与交付记录

本批开始前：47 项 Python 基线通过，源码在隔离工作区；未发现运行中的 Blender。
安装前必须再次核对进程状态；不能据启动时快照直接覆盖。

原测试入口：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
更新前 SHA256：`87C6A0989066AEF83E6047DD0CBFCE650DDF7C3BA970058AC6F81BA99F62A59B`。
回退入口：`D:/source/AxisMeld-build/phase2b-roomy-test-install/blender.exe`。
更新前回退 SHA256：`F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`。
六个 portable 文件的 SHA256 已单独采集，交付时逐项比较。

候选实现提交：`0b27a59ba1a`，校验修复：`89b6bba7273`。修复后候选 exe SHA256：
`8760100020BBFD92035C1450DD5FCA966A37648645A9BA0099A41211744D6D0D`。
主任务已独立比较候选与编译产物哈希，结果相同；工作树及差异检查干净。

| 验证 | 当前证据 | 边界 |
|---|---|---|
| Python 全部 AxisMeld 单元测试 | 修复后实现者及主任务分别运行，52/52 通过 | 不等于实体键鼠验收 |
| Native CTest | 实现者及主任务分别运行，5/5 目标通过；含 480×320 全树路径 | 不宣称所有极窄视口都已完善 |
| 候选 GUI | tools、menus、native-style、release、selection、appearance 及独立 manipulator 回归通过 | source resources 环境；最后文字布局修订后重跑 tools 和 Native，安装版仍需独立回归 |
| 截图 | 主任务查看最终工具环和普通子菜单：等宽、无中心按钮、父级可见、Keep Spacing 完整 | 不是 Maya Toolkit 所有变体的视觉一比一验收 |

测试命令：`python -m unittest discover -s tests/python -p 'axismeld_*test.py'`；
`ctest --test-dir D:/source/AxisMeld-build -C Release -R '^(axismeld_(hotbox_menu|hotbox_state|identity|transform_axis)|editor_hotbox_hotbox_model)$' --output-on-failure`；
GUI 使用 `tests/python/axismeld_hotbox_ui_runner.py --blender <候选或安装exe> --suite <suite>`。
日志位于 `D:/source/AxisMeld-build/m1-tools-*.log`；最终候选工具截图位于 `m1-tools-artifacts`。

候选使用源码资源时出现 Cycles 未加载和 libpng ICC 配置警告，报告中保留原文；
安装版将使用自带资源独立核实，不能把环境警告隐藏为无噪声通过。

未覆盖/保留差异：没有方向勾选标记；同工具再次点按不复刻 Maya 轴柄重置；
Circle 不是完整 Paint Select；普通子列表只接入有界子集及占位；真实 OS 自动重复标记、
跨窗口实体失焦和每工具方向下直接/中键轴拖拽手感仍需人工确认。

M2 上下文右键、M3 全部建模菜单/快捷键及 UV 尚不属于本批完成范围。

### 开发中发现的回归

- 从 Space 目录进入工具环时，普通目录留白使 480×320 全树布局测试失败；两个入口需共用紧凑尺寸。
- 工具键按住、左键未按下时，侧键等其他鼠标动作没有退出等待状态；新增对应事件断言。
- 窗口失焦后不再收到旧按键释放时，释放监听器残留；必须用“不补发旧 release”的用例验证清理。
- 紧凑按钮的子菜单箭头挤占文字，导致 Keep Spacing 截短；除尺寸测试外需要检查实际渲染截图。
- 审查发现径向菜单缺方向时两端仍接受、布局却拒绝；修复后两端拒绝，原生测试确认旧 generation 99 不被覆盖，普通旧快照仍兼容。见 `m1-tools-fix1-*-red/green.log`。

这些记录用于保留失败证据；最终通过状态以本页交付记录为准，不将开发中某次通过等同于最终安装版通过。
