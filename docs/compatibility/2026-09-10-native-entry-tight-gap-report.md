# 原生 Style 入口与紧凑间距验证

日期：2026-09-10；基于用户批准的 [局部设计](../design/2026-09-10-compact-secondary-native-style.md)。

## 交付身份

- 测试程序：`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
- SHA-256：`32BF08140F8F66DE0E832455E6D7B2189A4836ACC79049FA2E424A2EB5A92C1D`。
- 源码为本报告所在提交，基于 `5729a04f6c8`，分支 `axismeld/phase-2a`；未推送、未发布。
- 回退程序 `phase2b-roomy-test-install/blender.exe` 保持原样，SHA-256：
  `F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`。
- 复用现有安装，不增加整套测试版本；6 个 portable 配置与本次 tight-entry 备份逐文件哈希一致。

## 改动

| 项目 | 结果 |
|---|---|
| 两处 Hotbox Style 入口 | 真正使用 Blender 原生 submenu button 绘制，左对齐、原生悬停及右箭头；为图标槽和箭头保留宽度 |
| 二级热盒间隙 | 最小碰撞间隔和 Views 尾项间隔从 10 改为 4 逻辑像素；椭圆收紧，24px 目标及字体不变 |
| 一级热盒 | 38px 高度、83.6px 中央两侧留白、上下目录保持不变 |
| 原生菜单背景 | 按层单独绘制，入口和子列表之间不再由同一大背景连接 |
| 窄窗回退 | 左右均放不下时尝试上下；保留 10px 菜单间隔，并避开真实 marking 起点 12px 返回区；空间完全不足则拒绝布局 |

4px 是根据参考图作出的适配，不宣称 Maya 官方固定值或逐像素一致。沿用既有统一
输入所有权；本次没有修改 modal、W/E/R、Space/RMB 释放或用户个性化配置。
原生组件仅参与绘制，不建立第二套 popup handler，不宣称完整原生键盘导航接入。

## 验证

日志位于 `D:/source/AxisMeld-build/`；GUI 测试均使用独立 factory-startup、临时配置和隐藏进程。

| 检查 | 证据 |
|---|---|
| 收紧间距 RED | `tight-gap-mutation.log`：改回 10px 后，1050/540 的短距 Right 命中及尾项 4px 断言失败；已恢复 4px |
| 原生入口 RED | `tight-entry-red.log`：旧自绘入口未使用原生 hover 背景，实际像素断言失败 |
| 窄窗 RED | `tight-narrow-red.log` 复现入口重叠；`tight-narrow-origin-red.log` 复现向上避让覆盖起点返回区 |
| 原生布局 | `tight-native.log`，30/30；含 340/392px 窄窗和不同于热盒中心的实际 popup origin |
| CTest | `tight-final-ctest.log`，5/5 组；含上述布局，不重复计数 |
| Python | `tight-final-python.log`，26 项热盒配置/目录 + 14 项输入通过 |
| 原生样式 | `tight-final-native-style.log`，两个入口 × 1×/2×：背景、原生 hover、箭头像素、分离空隙、设置生效及 Space 释放通过 |
| 完整菜单 | `tight-final-menus.log`，Style 选择、回起点后短划 Right、Space 取消、禁用项、分页和边角命中通过 |
| 生命周期与配置 | `tight-final-hotbox.log`、`tight-final-release.log`、`tight-final-profiles.log`，热盒、同窗口释放隔离与配置层通过 |
| W/E/R | `tight-final-manipulator.log`，四个窗格、实际工具菜单选择、单轴点击/空白 MMB/直接拖轴、取消撤销、编辑模式和 Alt 导航通过 |
| 父级叠加 | `tight-final-overlay.log`，1×/2× 原位一级、拥有键原地释放退回及保持 Space 重进通过 |
| 拖曳线 | `tight-final-guide.log`，1×/2× 实际像素、真实按下原点、拥有键释放与 Esc/Space 清理通过 |
| 高 DPI 四视图 | `tight-final-quad.log`，真实 2× 窗格七方向和长目录末页事件通过 |

最终构建及上述隔离 GUI 综合/专项回归均通过。

已查看最终 Views 1× 与 Controls 2× 正常主题截图：标签完整、入口箭头、分离背景和
一级保留正常。独立只读审查发现的窄窗重叠及返回区覆盖均已修复并复核无阻塞项。
工具 GUI 脚本原先点击旧环的固定 +80px 坐标；已改用公共几何 fixture 提供输入坐标，
仍独立断言实际 Move 执行、Recent 记录与后续 W/E/R 场景变换，未放宽行为断言。

## 人工验收与边界

优先手测 [B12-27／B12-28](phase-2b-manual-test.md)，同时保留 B12-11、B12-20 至 B12-22。
自动化不等于物理鼠标手感或 Maya 一致性验收通过；窄窗特殊回退有几何测试，仍需人工试用。
Global 物体缩放、跨新窗口释放隔离、尚未实现的 Modeling/UV 功能不在本次范围。
