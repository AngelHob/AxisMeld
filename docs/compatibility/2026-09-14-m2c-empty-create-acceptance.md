# M2c 空白创建热盒验收记录

2026-09-14。源码基线77844b7582e；本批继续已批准的M2路线。用户确认此前47项已经测试，保留其反馈原意，不补写逐项通过结论。G组10项仍待测，本批K组新增12项，合计22项待测。

## 本批行为

- Object无选择且鼠标位于空白处，Shift+RMB立即打开Polygon Primitives；保持Shift，外划后释放RMB创建。复用四视图/工具热盒的紧凑五行布局与按钮外方向延续。
- NE Disc、E Sphere、SE Torus、S Cube、SW Cone、W Cylinder、NW Plane创建真实Blender网格，位置为3D Cursor。中心、N占位、Esc、先松修饰键和失焦均可取消；完成后清理本次输入，再接受新手势。
- Space→Create→Polygon Primitives共用同一命令；Object已有选择时可用，Edit创建不可执行。成功命令进入Recent，重放继续受上下文限制。
- 当前已有选择、Edit模式或鼠标指向可选对象时，Shift+RMB保留Blender原生回退。独立创建入口支持配置改绑及禁用，原组件RMB无修饰限制不变。

## 已知差异与后续

七种基本体沿用Blender的尺寸、Z-up、细分和Undo；没有实现Maya交互拖放和construction history。Disc为NGON填充圆，不是Maya polyDisc拓扑。

Torus原生Python operator没有enter_editmode参数，遵循“新建后进入编辑模式”偏好；默认关闭时Object，开启时Edit Mesh。其余六种显式保持Object。实现不临时修改偏好。

N Create Polygon Tool是M2c-P01不可执行占位。已选对象/点/边/面的完整Shift+RMB建模菜单、Ctrl组合菜单等见映射文档M2d-P01至P07。极窄Tool Header遮挡、Global物体缩放差异和UV专题保持原有后续范围。

## 验证证据

构建根目录为`D:/source/AxisMeld-build`，下列日志均位于该目录：

- 旧安装真实Shift+RMB入口RED：`m2c-create-old-red.log`，失败为未打开创建session，而非模块导入错误。
- Python先RED再GREEN：`m2c-python-red.log`与`m2c-python-scene-red.log`记录入口/命令/可编辑Scene边界失败；最终`m2c-python-root-confirm.log`为67项通过，其中新增10项。
- Native先RED再GREEN：`m2c-parser-red.log`记录七个新命令尚未加入白名单；`m2c-native-build.log`构建完成，`m2c-native-tests.log`为5个针对性CTest全部通过。
- 创建真实GUI最终`m2c-create-candidate-3.log`通过：七种几何与Cursor、按钮外划选、每项一次Undo、Torus偏好、取消与重开、原生回退、Space已有选择创建与Undo、Recent快照与真实命令重放、Edit拒绝、F13/F14 Ctrl+Shift改绑、禁用和四视图代表。
- 初次Space流程失败见`m2c-create-candidate.log`；仅修正测试中的MOUSEMOVE后等待视口上下文时序，未修改生产或重载预设。第2次及扩充后的第3次完整流程均通过，保留原失败日志。
- 配置后台回归`m2c-profiles.log`通过；其中非法style警告来自主动构造的非法配置用例。
- 独立静态审查与独立10项单元测试见`m2c-independent-review.md`，未发现确定阻断问题。

- 原工具/组件/目录/单选/释放/视图GUI全部通过：`m2c-tools.log`、`m2c-components.log`、`m2c-menus.log`、`m2c-native-style.log`、`m2c-release.log`、`m2c-hotbox.log`。释放套件为同窗口范围，不冒充实体跨窗口验收。
- 同步后从正式`blender.exe`再次运行完整创建套件，`m2c-installed-create.log`退出0且完整PASS。

自动验证不替代人工手感、真实Windows DPI、实体双窗口、Redo和文件配置重载验收。Recent新用例通过实际命令重放及快照验证；其新增条目的实体菜单点击仍列K-12手测。

## 交付与回退

使用原目录`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。本批更新前的三个二进制与AxisMeld Python资源已备份到`D:/source/AxisMeld-build/m2c-20260914-before`；个人portable目录不参与覆盖，更新前六个文件哈希记录在`m2c-install-before.json`。

`m2c-install-verification.json`确认构建、候选、正式入口和preview别名四份二进制一致；13个Python资源与源码一致，6个portable文件哈希不变。二进制SHA-256为`A8603FFB991CB9DCFB70C3D3930799C4606CF064783A1F16C5BBEA3BB68E3F4D`。文件哈希比构建内嵌的提交时间戳更适合识别本批实际安装。

人工清单：`docs/compatibility/2026-09-14-manual-test-ledger.md`。此前2026-09-13清单保留为历史快照，当前反馈以2026-09-14清单为准。
