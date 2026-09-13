# M2c 空白创建热盒

2026-09-14，继续用户已批准M2路线。基线77844b7582e。此前47项已由用户确认测试；G组10项继续待测，新验收另加编号。

## 有界交付

新增独立context.create_hotbox，Maya2026默认Shift+RMB PRESS。仅Object、无选中对象且鼠标下无可选对象时开启；当前选择优先于鼠标预选，不复用M2b目标提交。鼠标指向对象、有选择、Mesh Edit和非建模模式保留原生Shift+RMB，待M2d/M2e按真实上下文逐批接入。

复用现有radial模板：N Create Polygon Tool为M2c-P01不可执行占位；NE Disc、E Sphere、SE Torus、S Cube、SW Cone、W Cylinder、NW Plane。七项通过稳定mesh.create_*命令调用Blender原生EXEC_DEFAULT基本体创建，原生子operator拥有唯一undo；圆盘用filled NGON circle适配。使用3D Cursor与Blender原生尺寸、Z-up、拓扑，不冒充Maya交互拖放创建与默认细分完全等价。

Space→Create→Polygon Primitives共用菜单/命令，Object即使已有选择也可创建；其他模式灰显且不执行。创建成功后关闭热盒并清理所持release，下一次手势重新开始。关闭之后才分派几何操作，不把新几何命令放入QWER rearm白名单；Recent仅记录原生FINISHED。

六个C++基本体显式enter_editmode=False。Torus原生Python operator没有该RNA参数，遵循用户“新建后进入编辑模式”偏好；默认关闭时留在Object，开启时进入Edit Mesh。保留此原生差异，不临时覆盖用户偏好或叠加模式操作；两种设置都验证一次撤销及偏好不变。

## 输入与兼容

独立新入口，旧component_hotbox无修饰限制不变。schema1本就有shift等布尔字段，不升级schema；只扩Command默认修饰元数据。新入口支持无Alt/OSKey的键盘或鼠标PRESS改绑，Ctrl/Shift按显式配置捕获（不抢Alt导航）。键盘改绑不依据鼠标预选，但仍要求空选择Object；禁用/改绑后原ShiftRMB原生条目保留。

Native直接鼠标/键盘拥有一次session，捕获trigger与所需modifier mask；保持modifier时释放trigger提交，先释放所需modifier或新增不允许modifier取消并保护后续trigger RELEASE。Esc、失焦、mode/region/scene变化、中心回划与缺失/disabled方向取消均不产生几何、Recent或undo。释放时即使modifiers缺失也必须清除已释放owner，不能留guard。

## 验证与交付

先补profiles/keymap/catalog/白名单失败测试；实际GUI旧构建验证入口不存在。7个基本体分别验证真实mesh类型/新增数量/选中结果/3D Cursor位置及一次undo，中心/Shift-first/Esc/失焦/已选和hover对象回退/键盘改绑/单四视图代表回归。保留上一批tools/组件/radio/Space释放行为。

源码与设计留D盘，原安装目录备份后更新native和必要Python资源，GUI严格串行、factory/temp配置。最终更新2026-09-14人工ledger和本地输出，用户未报告的新项保持待测。不推送、不修改个人配置，不重试以前被策略拒绝的递归临时清理。
