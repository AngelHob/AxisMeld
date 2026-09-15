# 工作区栏位于 Menu Bar 上方

> 历史方案，已被用户后续确认的 [Modeling 视窗菜单方案](2026-09-15-modeling-viewport-menus.md) 替代。双排构建和测试证据仅用于追溯，不作为当前交付或验收标准。MB-28/29 记录保留，当前验收使用 MB-30–34。

用户要求将 Blender 原有 Layout、Modeling、Sculpting、UV Editing 等工作区标签栏放在 Maya Menu Bar 上方。采用两个原生 TOPBAR 区域，避免菜单数量挤占工作区标签。

1. Maya 配置下，原 HEADER 行仅显示工作区标签，右侧保留 Scene、View Layer 和原有运行状态。既有 WINDOW 区域在其下方绘制菜单集选择和 Maya 顶层菜单。
2. 顶部全局区域高度使用原生 header 高度的两倍，随 DPI 缩放；切换回 Blender 配置恢复原一行。区域 poll 状态变化驱动原生 screen refresh，不使用定时器修改布局。
3. 配置启用判定同时检查实际已加载 keyconfig，避免仅保存预设名而预设缺失时出现空白第二行。尺寸刷新同时更新最小/最大固定高度。
4. 保留原工作区切换、新增、右键菜单、最大化时 Back to Previous 入口，以及顶部场景/视图层控件。弹出菜单目录、热盒及语义执行不变。

实施后在隔离实例验证实际上下位置、工作区点击往返、菜单动作及撤销、配置双向切换、缩放与窄窗口。旧安装不覆盖，新候选单独交付；新增人工测试追加到统一台账及私人测试网页。

## 验证记录

- 原生 Release 构建及独立安装通过，候选为 `D:/source/AxisMeld-build/workspace-bar-test-install`。程序 SHA-256 为 `2669ddc56aadf011f3212f5eb9f595a2d9190d4c09503f817de8f7c65c9bce3a`；38 个 Python 资源与源码逐项匹配。启动入口已在独立后台进程启用 Maya 配置核验。
- 既有 Menu Bar UI 测试 10 项通过，菜单内容与语义目录未改。旧候选上的同一双排断言先失败：HEADER 26px，WINDOW 1px，总高度27px；新候选实际 HEADER 26px、WINDOW 27px、总高度53px。
- 1920×1017 实机完整验证通过：工作区点选往返、下排五菜单集展开、Cube 创建及一次 Undo、Maya/Blender 两排/一排无手动 resize 往返、编辑区几何恢复、150% 缩放后的菜单执行及恢复。日志 `D:/source/AxisMeld-build/workspace-bar-green04.log`。
- 工作区模拟点击需要分帧移动、按下和抬起，遵循原生标签先进入 HIGHLIGHT 再响应 PRESS 的行为。截图观察器按工作区主题文字颜色匹配完整字形，菜单边界计入原生内边距。失败日志保留，未改变产品代码来迎合观察器。
- 1100×800 下已验证分行和工作区点选往返；后续测试期间窗口意外变成1920宽，无法将该次完整动作结果记为窄窗口通过。完整窄窗口操作、工作区新增/右键、最大化编辑器返回等保留在 MB-29 人工复测。最终实机记录见 `D:/source/AxisMeld-build/workspace-bar-gui-final.json`。
- 私人网页追加 MB-28、MB-29 两项待测，原280项及用户服务端状态保留。旧两个 Menu Bar 候选的程序与资源均独立校验未修改。
