# Maya 参考图间距与拖曳引导线验证

## 交付身份

- 源码基线：`b9d39fc9938d44569fb9e18cdf9100344ecef840`，本报告随修复提交。
- 新测试程序：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`
- SHA-256：`3E3E7C8E52D77AD9CB49B743BB3997C83AC0559A5FD1B73B8CAB189816642CB2`
- 回退程序：`D:/source/AxisMeld-build/phase2b-roomy-test-install/blender.exe`
- 回退 SHA-256：`F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`
- `WITH_BUILDINFO=OFF`，运行时 Unknown 不用于版本识别。没有推送或发布。

复用了原有 ui-test-install；正在运行的 roomy 版未改动。覆盖前备份并校验 ui 版
portable 共 5 个文件，安装后再次逐文件核对配置未变。没有新增完整测试安装目录。

## 本轮变化

| 项目 | 实现 |
|---|---|
| 中央留白 | 用户截图两侧约 86–87px、中央高度约 40px；按约 2.2 倍高度适配为 83.6 逻辑像素，随 DPI 缩放 |
| 左右入口 | 文本、图标加原有内边距决定宽度，移除填满整行的额外拉伸；可见区域与命中矩形一致 |
| 小视口 | 无法容纳三入口时使用独立行／分页；480×320 必要时利用固定锚点上下两侧，保持顺序和可达性 |
| 拖曳线 | 实际按下坐标至当前指针，1.25 逻辑像素线宽，Blender 主题前景色，绘制在按钮／文字之下 |
| 生命周期 | 只在持有鼠标且指针离开起点时出现；释放、取消随既有所有权清理；定时器不会移动端点 |

参考图不是 Maya 内部几何规格，也不能证明空隙的动态区域规则。本轮不新增全局禁用区、
五区域映射或新的手势死区，不改变原有视图方向、中央 Style 防误触、菜单设置和命令行为。

## 验证证据

所有 GUI 用独立 factory-startup 隐藏进程、临时配置，未向用户场景输入。
日志和截图目录均在 `D:/source/AxisMeld-build`。

| 检查 | 结果／证据 |
|---|---|
| 先失败后修复：间距 | 旧实现返回 10px 间距且侧命中矩形被拉伸，新测试失败；修复后同测试通过 |
| 先失败后修复：引导线 | `reference-guide-red.log` 在旧 F841 程序中因 NE 路径无引导线像素而失败 |
| 完整原生布局测试 | `reference-layout-green.log`，22/22 通过，包括全树小视口／四角可达性 |
| 原生 CTest | hotbox menu/state、identity、transform axis、editor hotbox model 共 5/5 通过 |
| Python 纯测试 | `reference-pure.log`，热盒 26 项、输入 14 项通过 |
| 引导线实际渲染 | `reference-guide-green.log`，1×／2×、偏离中心的真实按下位置、非持有键释放、松开后再次移动、普通菜单、Esc／Space 清理通过 |
| 完整菜单真实输入 | `reference-menus.log`，63.750s，通过；包含多段划选、全部方向、二级菜单、设置、Recent、边缘、DPI、小视口、模式失效和取消 |
| 四视图操纵器真实输入 | `reference-manipulator.log`，44.485s，通过；包含四窗格 W/E/R、轴选择、重复 MMB、取消、Undo、直接拖轴、编辑模式和预设隔离 |
| 热盒完整生命周期 | `reference-hotbox.log`，30.203s，通过 |
| 同窗口释放隔离 | `reference-release.log`，5.375s，通过；不包含已知独立跨新窗口边界 |

主任务亲自查看了 `reference-guide-green/menus-main.png` 和 `guide-2.0-dragged.png`，
确认实际绘制留白和细线；这些是 AxisMeld 默认工厂场景，不是用户场景。
截图测试偶有既存 libpng 色彩配置警告，完整菜单测试的最小视口警告为预期负向用例。

独立只读审查未发现阻塞性生产问题；提出的释放测试盲区已补充：松开后再移动回原终点，
确保没有按键时不会重新出现线，最新渲染测试已通过。

## 人工验收

选择 **AxisMeld Maya 2026** 键位预设，优先测试 B12-17 至 B12-19，保留 B12-11 回归。
物理鼠标手感及用户审美验收仍待用户完成。Global 物体缩放、UV 功能和跨新窗口释放隔离
不在本次修复范围内。
