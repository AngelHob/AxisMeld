# 对象属性快捷访问

日期：2026-10-29。用户在审阅“先做 Transform 与 Modifier 属性入口，再按需完善 Options / Channel Box”的建议后授权开始开发。

## 目标与方案

让使用 Maya 风格菜单的用户能快速进入当前活动对象的 Blender 原生对象变换和修改器属性。首批复用当前窗口已有的 Properties 编辑器，不增加常驻栏、复制属性控件或改变场景数据。完整 Channel Box / Attribute Editor 与新算法不在本批范围。

评估过三个方案：复制一套通道面板会重复现有属性控件；每次新建属性窗口会增加窗口管理负担；复用现有 Properties 编辑器只需补入口和上下文规则，因此采用第三种方案。菜单明确使用 Blender 属性名称，Maya Attribute Editor / Channel Box 原占位保持。

## 交互约定

- 在现有 Space → Windows → General Editors 下增加 `Blender Object Properties` 分组，包含 `Object Transform Properties` 和 `Modifier Properties` 两个入口；同时提供 Blender F3 可搜索的具名操作。不增加默认快捷键、菜单根或方向热盒按钮。
- 对象变换入口切换到 Properties 的 Object 页，复用已有 Transform 区；修改器入口切换到 Modifier 页，复用完整原生修改器面板。保留用户面板折叠状态，不宣称模拟 Maya 历史节点。
- 从发起操作的窗口 / 场景 / View Layer 获取当前已选中的活动对象；菜单执行复用已有来源 token。仅选择同一窗口内可见的 Properties 区域，优先当前 Properties 区域，其次按面积、位置稳定选择。不得把别的窗口或不同 View Layer 的对象当作目标。
- 可以使用未固定的 Properties，或已经固定到同一对象的 Properties；固定到其他对象或数据块的区域不修改，也不解除固定。没有合适属性区域时显示原因并取消，不替换编辑器、不改变布局、不另开窗口。
- 无活动选中对象、失效来源以及不支持 Modifier 页的对象明确不可用。允许原生支持的对象 / 编辑 / Pose 模式查看属性，不为可用性切换模式或选择对象。只读对象可查看，字段编辑限制由原生 UI 决定。
- 成功导航只更新所选 Properties 的页签并清空该编辑器的属性搜索过滤，保证目标页可见；保留固定状态、对象名称、几何、变换、修改器、选区、模式、工作区和其他窗口。导航本身不产生场景 Undo 或 Recent；实际字段修改使用 Blender 原生撤销。
- 界面与不可用说明同时提供英文和简体中文。保留英文稳定 ID、现有两语言规则、Views 净间隔、18px 伴随列表、七根 Modeling 菜单及 QWER / Space 生命周期。

## 验收与交付

针对性测试覆盖菜单路由和原 Maya 灰项、确定性区域选择、固定面板、多窗口 / 失效来源、无选择、类型门禁、打开无数据修改与双语。实际 Blender GUI 检查目标页、目标对象、原生字段修改 / 撤销、中英文及缩放；静态替身测试不能代替原生交互证据。

完成后更新修改日志、当前路线 / 交接、统一人工测试目录及 GitHub Pages，保留全部旧编号和人工结果。发布包记录实际源码 / native 身份并独立启动验证。人工鼠标手感与生产文件验收继续单独待测。
