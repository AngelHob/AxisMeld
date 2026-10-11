# 建模灰项与热盒重复唤出验收

日期：2026-10-11。设计见[交互修复](../development/2026-10-11-gui-interaction-polish.md)。

## 范围与旧版复现

- 无活动对象时，Modeling → Curves → Control Points 的原生灰标签没有说明；Edit Mesh → 底部 Extrude 目录中的灰 Extrude 可被悬停预览，原生绘制实际抛出 `AttributeError: 'NoneType' object has no attribute 'data'`。
- 保持 W 按下，LMB 打开 Selection Constraints、灰 UV Edge Loop 后松 LMB，再次 LMB 会带回旧级联。截图完整匹配旧叶标签，并观察到伴随菜单从根的一列变为两列。
- 复现使用上一版 menu preview 的真实 GUI。测试最初的默认 Edit Mode、同名 Maya Extrude、tooltip 图像匹配和重叠背景组件问题已区分并修正，不作为产品失败证据。

## 修复与验证

- 不适用的 Modeling 原生分组按已有顺序显示灰按钮与上下文说明，阻止依赖缺失对象/模式的原生子菜单预览；静态项、图标、过滤和构建选项保持。UV 九项、Modifier 条目逐项保留，动态 Control Points 维持原单个入口。有效模式继续调用真实原生菜单、参数、poll 与扩展回调。
- 一次工具鼠标操作结束时清空伴随子菜单路径，下一次同一持键中的 LMB 从根目录开始。一次划选内的导航与独立 History 队列保持。
- 8 组 94 项纯 Python、2 组 42 项原生测试通过。独立审查未发现阻断或重要新增问题。
- 新原生候选已完成 W/E/R 各三种结束方式的实际 GUI 验证，共 9 组、18 次 LMB 唤出：灰项取消、原点取消、执行 World 后重开；确认对应方向设置实际变化，场景/选区不被取消路径修改，最终无残留热盒模态。
- 共 7 组实际 GUI 通过：重复唤出、既有工具热盒、History、窗口生命周期、Modeling 灰项、完整建模菜单和菜单 Options 导航。Modeling 灰项覆盖 4 个实际场景：空对象 Control Points / Extrude 的原因提示与安全禁用，以及回到正确曲线 / 网格编辑模式后的原生扩展与 poll 恢复。

## 待人工与交付边界

新增 **GU-20～GU-21**，目录共 338 项，当前有效 326、历史 12、历史已测 47、当前初始未测 279。既有编号和状态保持，自动测试不替用户勾选。

完整 [GUI interaction preview](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.11-gui-interaction-preview) 已发布；源码/native `534eec00698397cc55e27f23f3575e6d4894331a`。ZIP 297,076,617 字节，SHA256 `271fb168454b8f3413dc4f73114a1c941883823eac67d40decde1a9b2b82fa76`。6,498 个发行文件、145 项资源通过干净解压审计；解压包工厂启动和 Modeling 灰项实际 GUI 通过；匿名重新下载后再次核验 ZIP、解压和工厂启动。网站 12 项浏览器检查通过，Pages `185800d9799c` 的 6 个公开资源逐字节核对通过；[发布快照](2026-10-11-gui-interaction-preview-snapshot.json)保存指纹。旧预览包保留。

本批只修交互。实体鼠标手感、其他机器、任意插件组合仍待人工；极低窗口无完整说明空带时的遮挡限制保持，不据本批检查宣称全部 GUI 缺陷消失。
