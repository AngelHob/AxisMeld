# 2026-10-29 自定义属性参数窗口修复验收

版本 `axismeld-2026.10.29-custom-property-preview`；[下载](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.29-custom-property-preview)；[完整指纹快照](2026-10-29-custom-property-preview-snapshot.json)。

- Edit Attribute 打开或无改确认时保留 FLOAT、INTEGER、BOOLEAN、STRING 的名称、类型和值，布尔类型先于整数判别。
- Property 下拉切换后同步所选项草稿；切换、取消和打开不写回场景数据，Delete Attribute 使用当前所选项。
- 首次确认核对原窗口、场景、View Layer、对象和模式；来源变化、属性失效或类型不支持时取消写回，并保留显式 EXEC 参数及原生 Undo/Redo/F9。

本批针对性 Python 5 组/63 项；最终安装 GUI 记录 21 条（含 complete；simulated-native-events）、独立解压运行 GUI 记录 21 条（含 complete；simulated-native-events）；网站浏览器 14 项通过。发行目录 6533 文件/154 选定资源；stage/extract、匿名下载、公开包 factory 与 Pages 六资源逐字节核验通过。

公开目录 405 项（当前 391、历史 14），历史已测 47，当前待测 344、全表待测 358；既有编号与人工结果保留。

CP-01～CP-05 与原 PN-01～PN-06 继续待人工；物理鼠标操作、物理 F3 搜索、双语和高 DPI 可读性及完整视觉布局仍待人工验收。

GUI 的 caseCount 是记录数，包含 complete 完成标记，不等于独立测试数。此前失败 GUI 报告与日志保留为诊断，不计入最终 PASS；夹具修正不能替代最终运行实际完成的 PASS 回执。legacy M3 检查在基线与当前实现均于 line 81 失败，本批未将它计为 PASS。

GUI 证据边界：Property 选择通过 RNA 设置并显式刷新；已验证真实对话框绘制、模拟 RET/ESC 确认或取消，以及原生 Adjust Last Operation 弹窗中的模拟输入重算。物理鼠标下拉选择、选择后的自动刷新、完整 Space 菜单路由仍待人工验收。

Adjust Last Operation 在 Blender 默认键位下使用 F9；Maya 键位不使用 F9 代替该命令，应按该键位对应的命令入口执行。

GUI 记录数与交互方式按本批回执原值记录；原生模拟事件不等于物理鼠标。后台工厂启动与静态清单不证明完整视觉布局、生产场景或第三方插件。

本批仅修改 Python UI，固定 Blender 5.4 Alpha 上游、Buildinfo OFF；nativeSourceCommit 为构建安装的发行源码断言，不是 EXE 内嵌版本或独立可复现证明。

继续以 UI、交互和 Maya 2026 默认快捷键为优先；新增建模、Skin/Skeleton、UV 算法保持暂停。
