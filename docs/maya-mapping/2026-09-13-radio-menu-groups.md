# 热盒单选菜单组对照与缺口

用户反馈：Maya热盒中一些“左圆圈、右label”的单选菜单组尚未还原。日期2026-09-13。

## 当前修复范围

| 菜单组 | Maya来源/分类 | 当前真实状态来源 | 修复内容 |
|---|---|---|---|
| Hotbox Controls → Transparency | Maya2026/scripts/startup/HotboxControlsMenu.mel:227-244，明确radioMenuItemCollection和0/25/50/75/100单选项 | MenuSnapshot.transparency | 左侧空/实心圆，与现有实际透明度一致 |
| Hotbox Style（两个入口） | 现有AxisMeld互斥设置；Maya HotboxControlsMenu.mel:129-134列有相应显示方式命令，未声明其原菜单也是radio | MenuSnapshot.style | 统一互斥状态显示，为本项目适配 |
| Center Mouse Buttons → 左/中/右菜单映射 | 现有AxisMeld配置能力，不声称Maya菜单逐项一致 | MenuSnapshot.center_buttons对应组 | 每个按钮独立单选，包括Disabled；共享目录入口一致 |

使用原生单选图标列；悬停高亮与选中圆点分开。根据现有快照推导，不添加配置文件字段、不保存第二套selected状态。当前配置校验只接受0/25/50/75/100；非法非预设值被拒绝，不作为可操作功能。内部状态推导对非预设值保留全空防御，不选最近值。透明度25%对应一级不透明度75%，不将两者混淆。

Rows是独立开关，不改为单选；普通命令、QWER方向按钮和不可执行占位不自动加圆圈。

## 仍未还原的真实Maya单选组

| 计划编号 | 来源与选项 | 缺失能力/依赖 | 验收目标 |
|---|---|---|---|
| RG-P01 | others/scaleMarkingMenuImpl.mel:145-156，Component Use Object Pivot下Default/Object/Manip Pivot | 组件枢轴语义尚未映射；不能直接把Blender Median/Individual/Cursor改名当成完全等价 | 明确组件、多对象及工具独立状态，真实执行/取消/撤销，再恢复radio组 |
| RG-P02 | others/commonSelectionConstraintsOptionsPopup.mel:19-33，Off/Angle/Border/Edge Loop/Edge Ring/Shell | 持续选择约束适配未接入；一次性环选或相似选择不等于此约束 | 启用后连续选择遵循约束，Off恢复，持久状态/取消清晰；UV分支后置 |
| RG-P03 | others/buildObjectMenuItemsNow.mel:127-136，重置枢轴取中心或原点 | 枢轴编辑与重置入口尚未完成对应适配 | 不破坏对象/组件位置，证明默认与原点策略和radio状态一致 |

本表仅覆盖本次实际核对的菜单，不宣称完整Maya所有工作区的radio组清单。工具选项进一步恢复依这些计划推进，不用有圈但不能执行的菜单冒充功能完成。
