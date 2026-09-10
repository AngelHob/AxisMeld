# 极窄视口菜单与工具横条重叠：后续修复入口

状态：已定位现象与当前边界，未实施修复。与五小时批次的 H5-04/H5-05 对应；
本文件不是新的完成声明，也不要求用户现在单独审核。

## 可重复证据

- 安装生产检查点8341fdac9b0，exe SHA25634CCA824…F8603BE7A。
- 实际Window原点(2,95)、尺寸392×281、scale1。
- 禁用previous行的鼠标点(100,335)，同时落入Tool Header(2,324,392,26)
  和Window(2,95,392,281)。截图可见原生菜单与工具选项横条相交。
- Space先松后补齐拥有鼠标键释放，`window.modal_operators == []`，鼠标原地按W
  仍是builtin.select_box；移到明确的Window中心(198,235)后W/E/R及新热盒命令可用。
- 原始日志：`D:/source/AxisMeld-build/batch5h-mapping-gui-fix2-no-move-failure.log`。
- 原始截图：同名`-artifacts/mapping-narrow-held-disabled-previous-space-first-ready.png`。

这说明存在布局遮挡与按键上下文边界，不足以证明残留热盒所有权。不能把移开鼠标后的
成功当作该遮挡缺陷已修复，也不能仅凭“鼠标移动后恢复”就修改全局release guard。

## 当前源码与风险

| 接口 | 已核实事实 | 后续实现要避免的错误 |
|---|---|---|
| view3d_axismeld_hotbox.cc | 按region.winrct建立事件坐标、记录区域尺寸与活性 | 只缩小布局宽高但不平移center/origin/命中坐标，会破坏方向手势 |
| view3d_axismeld_hotbox_draw.cc::hotbox_layout | 将width/height/center、scroll和真实origin传给纯布局 | 不能只移绘制矩形，留下旧输入命中区域 |
| hotbox_menu.cc::native_popup_position | 在整个传入矩形内避让直接入口，Views还避让真实origin | 当前接口没有任意内部遮挡区域集合，不能假定外边距会避开内部横条 |
| ED_region_visible_rect，screen/area.cc:4718起 | 返回region局部坐标，按overlap兄弟的动画矩形裁剪贴边遮挡，跳过float | 当前Tool Header的y上沿350不是Window上沿375；仅换用此函数未必去除内部横条，必须实测 |

## 后续最小修复应满足的门槛

1. 先复现当前无移动失败，记录真实区域和屏幕图；保留本批日志为基线。
2. 比较使用Blender已有可见区域接口后实际矩形，确认能否覆盖工具横条、左右侧栏和四视图。
   若不能，先明确是菜单避障还是键盘上下文路由问题，不同时扩展两套全局机制。
3. 布局、绘制与命中坐标必须使用同一变换；真实marking起点和返回死区不能被虚拟中心替换。
4. 窄窗和2×四视图测可读选项、禁用箭头、先松Space/Esc及鼠标原地W/E/R；另测
   工具横条/侧栏显隐与尺寸改变，确保不出现旧区域指针或悬空绘制。
5. 必须保留父热盒和原有菜单所有权规则；不通过隐藏用户工具栏、抢全局键盘焦点或
   强制移动用户鼠标来让测试通过。

需要用户最后确认的是遮挡是否出现在其常用布局、以及狭小空间中菜单避让/减少可见项的
取舍。无需修改Global缩放或UV模块来解决这项问题。
