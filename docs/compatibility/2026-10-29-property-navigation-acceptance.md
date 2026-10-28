# 2026-10-29 属性导航预览验收

**当前交付（2026-10-29）：Transform / Modifiers 属性导航预览已发布并核验。** 在现有界面中打开 Blender 原生变换与修改器属性，保留中英文显示、18px 伴随列表与现有交互；不增加建模算法。 [下载完整预览包](https://github.com/AngelHob/AxisMeld/releases/tag/axismeld-2026.10.29-property-navigation-preview)；功能/native 源码 `45a5a51a01925164f11dcf4ce1ecbb8be217dced`，固定 Blender 5.4 Alpha upstream `754ebe3c4b4e1402a159df6e1e58823cc93ef887`。

10 组 127 项针对性 Python、当前真实事件 hotbox-repost、最终安装和独立解压副本各 14 项 GUI、本地网站 14 项浏览器检查通过。完整包 6,533 文件、154 选定资源，stage/extract、匿名下载和公开包工厂启动通过。ZIP 280,173,712 字节，SHA256 `88c3a3728bed8f3d83fd6229545a06493c071ffc4e458b27c482cff048027858`；EXE SHA256 `e85cc631490981c0a4893ffd6fe60b4bc70c2534108c21c181219c86772a74a4`。本批为 Python 改动且 buildinfo OFF，EXE hash 与双语基线相同；如实记录，不称独立可复现重编证明。

公开目录 400 项（当前 386、历史 14），47 项仅为历史已测；当前初始待测 339、全表初始待测 353。本批新增 PN-01～PN-06，六项均待人工；既有编号与人工结果保留。

实际 GUI 验证覆盖原生 RNA 属性与 operator/Undo：最终安装候选 14 项、独立解压运行副本 14 项通过；物理 F3 键盘搜索和字段鼠标编辑未自动化，仍待人工。启动截图存在覆盖视窗的启动模态框，不能据此宣称全部视觉布局已验清。

继续 UI、交互与 Maya 2026 默认快捷键优先；新增建模、Skin/Skeleton、UV 算法暂停。后续可按用户反馈改进既有 Options 体验，不自动开启新算法开发。

公开 Pages 本批六资源已逐字节核验通过，提交 `22f6ad60ddac2261e44ac26e64540dc8b390f74b`；最终网站配置下 14 项浏览器检查通过。 详见[本批验收](2026-10-29-property-navigation-acceptance.md)与[发布快照](2026-10-29-property-navigation-preview-snapshot.json)。

当前人工维护且按入口分组的 tools/testing_site/catalog.json 是公开目录权威来源。不要运行旧 tools/utils/axismeld_public_test_catalog.py 导出：它遗漏多段 BI 编号和新组，会把当前目录回退；同步维护人工 ledger 与按入口索引。

## 具体行为与本批修复

入口为 Space → Windows → General Editors → Blender Object Properties → Object Transform Properties / Modifier Properties；两项同名操作也注册到 Blender F3 搜索，不增加默认快捷键。Transform 进入原生 Object 页既有 Transform 区，Modifiers 进入原生 Modifier 页，保留面板折叠状态，只切换目标属性页并清空其搜索过滤。

目标来自发起窗口、场景和 View Layer 中当前已选中的活动对象；只复用同窗口可见 Properties，优先当前 Properties，再按面积和位置稳定选择。仅接受真正未固定或已固定同一对象的区域；其他对象/数据块固定不改、不解锁。不满足来源、选中对象、对象类型或合适属性区域时取消并给出原因，不替换编辑器、不新开窗口、不改布局/选区/模式/场景数据；导航不增加场景 Undo/Recent，实际字段编辑使用原生 Undo。

本批修复原生 pin 状态判定：仅 use_pin_id=False 而 pin_id 仍残留另一对象时，Blender 原生上下文仍可能使用该 pin_id，不能按“未固定”处理。现在要求 pin_id=None 且固定标记关闭，或 pin_id 就是目标对象；不清除用户固定状态来绕过门禁。

GUI 测试夹具也单独修正：用于多窗口隔离的窗口改为 wm.window_new_main()，避免子 wm.window_new 随父窗口同步场景而污染来源断言；夹具解除固定时同时核对/清空 pin_id。这些是测试场景搭建修正，与上面的产品 pin 判定修复分开记录。

## 验证范围与证据

| 验证 | 结果与范围 |
|---|---|
| 针对性 Python | 10 组 127 项通过，focused-final/receipt.json |
| 当前事件回归 | hotbox-repost 真实事件通过 |
| 最终候选 GUI | gui-final：14 项；原生 RNA 与 operator/Undo |
| 独立解压运行副本 GUI | package-gui：14 项；运行副本与干净发行目录分开 |
| 本地网站 | 14 项浏览器检查通过，不等于公开 Pages 已更新 |
| 完整发行 | 6,533 文件 / 154 选定资源，stage/extract、匿名下载及公开包 factory 通过 |
| 人工状态 | PN-01～PN-06 仍待测，既有结果保留 |

旧 menubar-actions GUI runner 针对历史 application-bar 布局，尝试时 top Create 查找失败；该尝试保留诊断记录，不计本批验收通过，也没有据此证明当前产品回归。

实际 GUI 验证覆盖原生 RNA 属性与 operator/Undo：最终安装候选 14 项、独立解压运行副本 14 项通过；物理 F3 键盘搜索和字段鼠标编辑未自动化，仍待人工。启动截图存在覆盖视窗的启动模态框，不能据此宣称全部视觉布局已验清。

不得用后台 RNA、operator 调用冒称真实字段鼠标拖拽或物理 F3 键盘路径已测。默认语言、完整视觉布局、生产模型与第三方插件仍按具体人工用例验收。

公开 Pages 六资源与提交 22f6ad60ddac2261e44ac26e64540dc8b390f74b 逐字节一致；最终配置下网站 14 项浏览器检查通过。
