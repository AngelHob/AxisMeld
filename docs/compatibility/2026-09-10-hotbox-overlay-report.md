# 二级视图热盒叠加修复验证

日期：2026-09-10。基于用户第二张 Maya 截图及“一级未隐藏、松开右键返回一级”的澄清。
设计见 [叠加与释放规则](../design/2026-09-10-hotbox-secondary-overlay.md)。

## 交付身份与范围

- 当前测试程序：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
- SHA-256：`025E9D4E39DCC68B32B8D61E35E64449330FC2F2B18223AA0D2672240777F54B`。
- 源码：本报告所在提交，基于 `8b6f298c265`；`WITH_BUILDINFO=OFF`，不以运行时 Unknown 判断身份。
- 回退程序：`D:/source/AxisMeld-build/phase2b-roomy-test-install/blender.exe`，SHA-256
  `F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`，未修改。
- 复用原测试安装，无新建整套 stage。覆盖前确认未运行；portable 的 6 个文件先备份，安装后逐文件哈希不变。
- 未修改用户场景、未推送、未发布。所有 GUI 检查为隔离配置、factory-startup 的隐藏测试进程。

## 本轮改动

| 项目 | 行为 |
|---|---|
| 层级 | 一级原位显示；视图二级覆盖其上，无额外中心按钮；背景不接收二级操作的命中 |
| RMB 松开 | 中心／无有效候选返回一级；有效候选执行一次；Space 一直保持时可以再次进入 |
| 布局 | 全称视图名称、NE 灰显 New Camera；Style 位于 Front View 下方，子项为右侧纵向列表 |
| Style 返回 | 同一次按住中拖回起点，收起 Style 子列表，恢复短划选方向识别 |
| 绘制 | 原生 Blender 字体、图标、主题透明度；背景标签只因实际内容被覆盖而避让，不因按钮留白相交全部消失 |

小视口放不下完整长名称与底部 Style 时，保留七方向紧凑环；不缩小 38px 目标，
Style 仍从一级 Hotbox Controls 进入。普通目录的原有分页／Back 控件不在本次删除范围。
New Camera 未实现，不把占位当成功能完成。尚不宣称 Maya 逐像素一致或物理鼠标手感已通过。

## RED / GREEN 证据

日志位于 `D:/source/AxisMeld-build/`：

- `overlay-native-red.log`：旧实现缺少保留父级和 Style 尾项，新增两项测试失败。
- `overlay-ui-red.log`：旧程序真实截图中一级 File 消失，像素回归失败。
- `overlay-text-red.log`：按钮留白相交导致未遮挡 Edit 标签消失，像素回归失败。
- `overlay-style-red.log`：Style → 中心 → 15px Right 的真实事件回归失败。
- `overlay-native-final.log`：25/25 原生布局／命中测试通过。
- `overlay-ctest.log`：5/5 CTest 组通过。
- `overlay-pure-final.log`：26 项热盒与 14 项输入 Python 测试通过。
- `overlay-delivery.log`：最终程序 1×／2× 保留父级、真实按下原点、非拥有按钮释放、
  中心释放回一级、未遮挡文字、保持 Space 重进并切 Right View，通过。

- `overlay-delivery-menus.log`：完整菜单真实事件通过，包括 Style 选项、回中心后
  15px Right、禁用 New Camera、Style 内先松 Space、映射、Recent、角落、分页及取消。
- `overlay-delivery-hotbox.log`：热盒生命周期、四视图状态保存／恢复、Preferences 绘制通过。
- `overlay-delivery-release.log`：同窗口释放隔离、动态设置、受限命令派发通过。
- `overlay-delivery-profiles.log`：配置层和非法配置诊断通过；测试预期 warning 不代表用户配置损坏。
- `overlay-delivery-manipulator.log`：W/E/R、单轴点击＋空白 MMB、四视图、取消／撤销、模式隔离通过。

- `overlay-delivery-guide.log`：1×／2× 拖曳线像素、真实起点、拥有／非拥有按钮释放、普通菜单及 Esc／Space 清理通过。
- `overlay-delivery-quad.log`：实际 392.5×212.5 逻辑像素的 2× 四视图中，七个可见视图按钮及长目录末页命令通过。

上述最终包自动化全部通过；人工体验验收待用户测试，不据此关闭物理输入手感问题。

已直接查看最终包的 `overlay-delivery/overlay-1.0-held.png`、`overlay-2.0-held.png`
以及 `overlay-delivery-menus/menus-fresh-style-drag-candidate.png`，核对主层中心仍在、
无二级中心按钮、长名称布局与 Style 的右侧纵向选项。
独立只读审查发现的 Style 回中心后短划选失效已补 RED/GREEN 并复核关闭。

人工优先验收 B12-20 至 B12-23。跨新窗口释放隔离是原有独立已知失败，未在本轮解决；
同窗口测试不能代替跨新窗口验收。Global 物体缩放差异与大规模 UV 功能仍按原约定搁置／后续开发。
