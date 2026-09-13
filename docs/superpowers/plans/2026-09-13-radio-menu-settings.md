# Restore Radio Menu Settings

> Execute with superpowers:subagent-driven-development and verification-before-completion.

**Goal:** 修复用户报告的热盒单选菜单组未还原：已有互斥设置用左圆圈+右label，并显示真实当前值。

**Spec:** ../specs/2026-09-11-modeling-interaction-alignment-design.md；本次直接用户反馈优先。

## 已核实范围

Maya2026/scripts/startup/HotboxControlsMenu.mel:227-244 定义Transparency 0/25/50/75/100为radio组。当前AxisMeld已提供这些设置但缺少状态标记。先修此明确遗漏，同时统一已有互斥Hotbox Style和三个中心按钮映射目录的单选显示。Style/映射是本项目已有设置，不宣称其所有文字/路径逐项复刻Maya。

Maya2026/scripts/others/scaleMarkingMenuImpl.mel:145-156的Component Pivot、commonSelectionConstraintsOptionsPopup.mel的选择约束也含radio组；其完整能力尚未接入，本批只记录缺口，不伪造可切换功能。

## 契约

- radio菜单为普通纵向菜单，左侧空心圆/实心选中圆，右侧label；悬停高亮不等于持久选中。
- 透明度、Style、每个中心按钮映射各自互斥；点击执行现有设置操作并刷新，重复选择幂等。配置重载/外部设置改变后新打开菜单显示真实当前值。
- 当前透明度配置只允许五个预设；非法值被拒绝。内部helper对非预设快照全空的防御仅作单测，不宣称支持自定义透明度。
- Rows等独立开关不改成radio；普通命令、占位、QWER方向按钮不乱加圆圈。
- 沿用原生图标绘制与布局，不叠加新鼠标handler，不改Release/Space取消、个人配置schema或新建第二套持久状态。
- 优先从现有snapshot设置字段推导状态，不为只显示既有设置引入非必要JSONschema扩展。

## Task 1: 单选状态与原生菜单绘制

Implementer owns native hotbox draw/layout/helper and tests; minimal catalog presentation changes if needed. Main owns docs/install.

- [x] 找到当前setting目录/原生MenuOverlay图标路径；先补失败用例证明缺少标记/列表布局。
- [x] 实现状态推导及左图标列，确保宽度包含圆圈且长label不截断。
- [x] 验证互斥、不同中心按钮组独立、非预设全空、配置刷新及旧快照兼容；实际截图核对空心/实心和对齐。
- [x] 独立复审，修问题后交付候选；不改原测试exe。

## Task 2: 安装回归与人工记录

- [x] 备份原exe/Python，保留portable哈希；GUI严格串行。
- [x] 实际安装态radio专项、native-style/设置释放及必要QWER/组件回归。
- [x] 向当前40项清单追加S编号，保持原项待测，记录本次范围与其余未还原组。
- [x] 本地提交、提供独立预览入口（用户原程序仍有未保存场景）、输出清单与截图；不推送，不重复尝试已被策略拒绝的临时目录递归清理。
