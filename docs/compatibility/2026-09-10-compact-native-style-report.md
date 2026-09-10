# 紧凑二级热盒与原生 Style 菜单验证

日期：2026-09-10。基于用户批准的二级尺寸、热盒＋普通菜单组合和恢复一级菜单行要求。
设计见 [本次设计](../design/2026-09-10-compact-secondary-native-style.md) 与
[后续复用规范](../design/hotbox-menu-composition.md)。

## 交付身份

- 当前程序：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
- SHA-256：`8039E8FF861CCB891DFBDB114CADC9BFC1F006AEB2117383BDD940E875F95283`。
- 源码为本报告所在提交，基于 `426037bf2d2`，分支 `axismeld/phase-2a`。
- 回退程序 `D:/source/AxisMeld-build/phase2b-roomy-test-install/blender.exe` 未修改，SHA-256：
  `F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`。
- 沿用已有测试目录，无新增整套 stage；未推送、未发布，未改变用户场景。

## 改动表

| 项目 | 本次实现 |
|---|---|
| 二级热盒 | 高度从 38 降为 24 逻辑像素，文本左右总留白从 40 降为 16；不缩小字体；椭圆、间隙、分页和真实划选原点保留 |
| 一级热盒 | 保持 38px 高度、83.6px 中央两侧安全间距；不会随二级一起缩小 |
| Hotbox Style | Views 尾项与 Controls 入口均使用 Blender 原生菜单 block/button 绘制；连续三项、统一背景、原生悬停／禁用样式，靠边向左展开 |
| 文本完整性 | 普通菜单单独保留 40px 原生组件边距；修正首轮渲染中最长名称被截断的问题，不把菜单边距与热盒边距绑定 |
| 一级上下目录 | 此安装的持久化 style 从 zones 恢复为 rows；未实现项仍灰显，用户之后仍可主动选择 Zones Only／Center Zone Only |
| 后续复用 | 新 `UI_menu_overlay.hh` 适配器与组合设计规范；未修改上游菜单事件处理逻辑 |

原生 block 不注册到 region，不建立第二套 popup handler；输入仍由原热盒统一处理。
已有父级保留、回中心取消、拥有鼠标键释放和 Space 关闭逻辑继续生效。
这复用的是原生菜单绘制组件，并不宣称接入原生菜单全部键盘／可访问性导航能力。

## 配置保护

确认用户旧进程退出后，先复制 portable 的 6 个文件并逐文件 SHA-256 校验，备份位置：
`D:/source/AxisMeld-build/preserved-test-configs/2026-09-10-compact/phase2b-ui-test-install/portable`。
仅修改 `config/axismeld/hotbox_user.json` 的 style；安装和全部隔离 GUI 测试后，另外 5 个
配置文件仍与备份哈希一致，当前 style 确认为 rows。需要恢复原样式时可从菜单切换或使用该备份。

## 验证证据

日志和截图根目录为 `D:/source/AxisMeld-build/`。测试使用隔离配置和 factory-startup 隐藏进程。

| 验证 | 结果／证据 |
|---|---|
| 原生布局 RED | `compact-native-red.log`，新增紧凑命中和连续 Style 布局在原实现上失败 |
| 原生背景 RED | `compact-native-style-red-current.log`，原版浮动卡片之间露出视口，连续原生菜单背景断言失败 |
| 布局 GREEN | `compact-final-native.log`，27/27，包括主级留白、紧凑二级、两处原生 Style、四视图命中、分页和禁用遮挡 |
| CTest | `compact-final-ctest.log`，5/5 组通过；含上述布局测试，不与其重复计数 |
| Python | `compact-final-python.log`，26 项热盒配置／目录与 14 项输入测试通过 |
| 原生 Style 矩阵 | `compact-style-matrix.log`，两个入口 × 1×/2× 的真实背景像素、设置生效与 Space 释放无播放泄漏通过 |
| 完整菜单交互 | `compact-final-menus.log`，Style 选择、回中心后 15px Right、Space 取消、New Camera 禁用、分页／映射／Recent 与角落通过 |
| 热盒与释放 | `compact-final-hotbox.log`、`compact-final-release.log`、`compact-final-profiles.log`，生命周期、四视图恢复、同窗口释放隔离和配置层通过 |
| W/E/R | `compact-final-manipulator.log`，四个子窗与单视图、单轴点击＋空白 MMB、直接拖轴、取消／撤销、编辑模式和 Alt 导航通过 |
| 父级叠加 | `compact-final-overlay.log`，1×/2× 父级原位显示、非拥有键释放、中心释放回一级、保持 Space 重进通过 |
| 拖曳提示线 | `compact-final-guide.log`，1×/2× 实际渲染像素、真实原点、拥有键释放、普通菜单及 Esc／Space 清理通过 |
| 实际高 DPI 四视图 | `compact-final-quad.log`，392.5×212.5 逻辑像素窗格内七视图按钮和长目录末页命令通过 |

已直接查看 `compact-style-matrix/native-style-views-1.0-normal.png` 和
`native-style-controls-2.0-normal.png`：最长名称完整、统一菜单背景、父级保留以及向左避边正常。
独立只读审查及限定复核未留下阻断问题；补充了两个 Style 路径三个条目的原生绘制标志和高度回归。
像素检查证明背景连续，完整文字另由实际截图检查验证，不把前者冒充文字识别测试。

## 待人工验收与边界

优先验收 [B12-24 至 B12-26](phase-2b-manual-test.md)，并保留 B12-11 与 B12-20 至 B12-23 回归。
自动化通过不等于 Maya 逐像素一致或物理鼠标手感验收通过。
小视口仍可使用七方向短名布局，普通目录仍有 Back／分页；New Camera、未接入的 Modeling／UV 功能
保持占位。Global 物体缩放差异和跨新窗口释放隔离仍按先前边界搁置，未在本轮解决。
