# 热盒方向模型验证

日期：2026-09-13。基线：`129373b45c6`。仅模型与原生测试；本记录不代表 GUI 或实体键鼠验收。

## RED

先新增四组原生行为测试，并让新 `hit_marking_menu_rect` API 暂时直接调用已有 `nearest_marking_rect`，以实际旧解析暴露缺失保护；随后构建测试目标并运行 CTest。结果：52 项中 48 项通过，以下 4 项失败。

- `RadialTemplateKeepsShortStrokeTargetsReachable`：`(576,400)` / `(590,432)` 的短划目标返回空串，预期分别是 Move Global / Local；旧工具侧间隔仍为 32px。
- `RadialOutwardHitsRetainDisplayedRowsAndDisabledTargets`：当前中心和错误 owner 仍返回方向；不等宽短按钮外移可被长邻行抢占，例如 Q Clear → Camera、Rotate Gimbal → Discrete Rotate。
- `MissingRadialDirectionsBlockInsteadOfStealingNeighbours`：Component 缺 NW，但 `marking_gaps.size()` 是 0，预期 1。
- `RadialHitUsesCurrentCenterAndNeverAnOpenNativeList`：子环中心返回方向；隐藏 Views 祖先中心又令合法子环外延返回空。该组也包含最终必须满足的 native list 隔离断言。

RED 的原始结果仅保存在本次任务工具输出，未持久保存到单独文件。临时编译适配壳因尚未使用 `owner` 产生 C4100；GREEN 实现后已消除。

## 实现边界

- `marking_position` 统一五行与 16px 斜行内收，工具 side 由 32px 改为 Views 的 8px；保留工具每项内容定宽、最小 84px、24px 中心/按钮和 32px 行步长。
- 所有 radial 缺席方向在成功布局后生成不可提交 gap；不绘制、不参与布局可达性计算，换环时清除旧 gap。
- 新 API 限定当前 owner 和当前深度，活动 native list 阻断外延，可见/禁用方向优先；仅当前中心作为该解析器的中心保护。
- 不等宽按钮跨过自身外侧边缘后先沿所在显示行延续，再使用公共矩形投影。原 Views API 的中心、真实起点通道及投影路径保持原行为。
- API 返回原 `MenuLayout` 内指针，调用方必须在重建布局前复制；原始 12px 取消、返回状态与提交/释放仍由 operator 管理。

## GREEN

测试构建目标：`axismeld_hotbox_menu_test`，Release，parallel 2。

CTest：`--test-dir D:\source\AxisMeld-build -C Release -R '^axismeld_hotbox_menu$' --output-on-failure`。

结果：CTest 1/1 通过，内部 52/52 原生测试全部通过，包括原有 Views、native list、边缘布局及中心返回模型测试。最终构建未报告警告。三个源码/测试文件的 `git diff --check` 通过。

GREEN 原始日志已从 CTest `Testing/Temporary/LastTest.log` 复制至 `D:\source\AxisMeld-build\gesture-native-model-green.log`。未运行 GUI、Blender 构建或安装。

尚需主任务集成验证：`retract_at_center` 的旧祖先返回策略先于新 helper 执行；其与本轮隐藏父环/子环外延要求的交界由 operator 审查及 GUI 手势测试覆盖。
