# 紧凑工具热盒与子级返回验收

状态：实现、审查修复及安装态自动回归完成；人工手感待确认。未推送远程。

## 本次改动与人工审核表

入口仍为 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
按住 Q/W/E/R 再按住左键划选；Space 主菜单的操作方式不变。

| 编号 | 改动 / 测试方式 | 预期 | 人工结果 |
|---|---|---|---|
| C1-01 | QWER 中间行快速向上下邻行划动；单/四视图分别试 | 五行紧凑错列、等宽；24px 按钮和字号不缩小。普通工具行空隙 8px，标签变长不再撑大纵向行距 | 待测 |
| C1-02 | Space 中央右键进入视图热盒 | 相同紧凑行列逻辑；常规间隙最多 11px，极小视口使用 4px/短标签后备。一级 Space 目录仍保留，Style 仍是原生菜单入口 | 待测 |
| C1-03 | W/E/R 选择 Global、Local；再切换工具 | 使用 Blender 用词、保留各工具独立方向；内部旧 ID 和个人改键不迁移 | 待测 |
| C1-04 | QWER 进入 Select、Symmetry；WER 进入 Axis/Custom Axis；W 进入 Snap | Maya 对应方向式子热盒替换父环，无中心按钮；未接入项灰显，不修改模型 | 待测 |
| C1-05 | 进入普通设置列表后移回原环中央空白区，再划向另一个按钮 | 即时收起子列表，新一划可选择其他动作；返回事件本身不重开或提交 | 待测 |
| C1-06 | W/R：Axis → Custom Axis，向外划一下再回当前子环中心，然后重新选择或再次进入子级 | 退回 Axis 一级，不连续退回根环；普通子环起始中心位置不会导致刚打开就退回 | 待测 |
| C1-07 | 在视口左下角重复进入 Axis、移出再回当前中心；另在原始按下点原地释放 | 被夹紧的父/子中心重叠也能退一级；真实按下点的取消保护仍有效，不误执行按钮 | 待测 |
| C1-08 | Space → Modify → Tool Settings → Move Tool → Axis，再返回并选择 Local | 同一套工具子树；Space 一级背景保留、其他工具父环隐藏；松键不残留输入监听 | 待测 |
| C1-09 | 顺序测试先松鼠标、先松工具键、Esc、Alt 导航以及再次点 QWER | 按原约定提交/取消，不把工具切换变成抓取模态；个人外观和配置不变 | 待测 |

父中心若被当前可见按钮覆盖，按钮仍优先，不放隐形返回区抢走该动作。
此时使用“向外划出，再回当前子环中心”退一级；这也是边缘中心重叠的返回路径。
Space 一级显示是例外，不能推导为所有工具父环都需要显示。

功能适配和占位方向见 [Maya 对照表](../maya-mapping/2026-09-11-tool-marking-menus.md)。
UV 编辑器、Global 缩放数学、新的对称/软选择/吸附算法不在本次交付内。

## 自动验证与审查证据

- Python：53 项通过；目录 300 节点、深度 7，Python/native 节点预算同步为 512，深度 8 和 256 KiB 限制不变。
- 原生：5 个 CTest 目标通过，包含 45 项布局测试、11 项解析测试，覆盖长标签行距、父环移除、Space 背景、中心命中、全树 480×320 路径、窄视口 Style 和 2x 逻辑布局。
- 行距 RED：旧实现相邻行空隙约 36–56px，超出测试上限 11px；改为错行布局后通过。
- 中心 RED：`compact-hotbox-return-red.log` 对旧空实现检测到返回为空；补充实际布局中心区域后通过。
- 三级返回 RED：`compact-hotbox-nested-red.log` 明确失败 `move third-level center return did not restore Axis`；加入路径隔离的移出/返回状态后，`compact-hotbox-tools-green.log` 通过。
- 扩展真实事件：`compact-hotbox-expanded-tools.log` 通过 W/R 三级往返、边缘夹紧中心、经实际 Space 目录进入子级，以及已有按键所有权、撤销、单/四视图、改键回归。
- 独立只读审查发现当前级中心可能遮住祖先中心；上述修复已复审，无未解决 Important/Critical。审查本身不替代 GUI 执行。
- 最终安装态：tools、hotbox、menus、native-style、release、selection、appearance、manipulator 八组均退出 0 并具备各自 PASS 标记。menus 含 1x/2x 分段拖曳、七视图实际姿态、四角及原生 Style 往返；tools 含当前子环中心回收和 Space 工具路径。
- 首次安装态视图/菜单测试仍使用旧 Front 的 -90px 坐标，紧凑后该位置落在 Style 入口；更新输入夹具到新视图行位置，保持原预期四元数和投影不变。顶角原点方向测试改为从同一真实边界按下、向空白区移动 15/-15px（距离约 21.2px，大于 12px 死区），避免旧 90px 终点撞上夹紧后的其他可见按钮；可见按钮优先另有测试。独立复核确认未削弱语义断言。

构建中扩充后的单个深层 C++ 聚合夹具耗尽 MSVC 提交内存，日志 `compact-hotbox-limit-red.log`。
夹具生成器改为逐节点小函数，仍生成真实默认目录；后续构建成功。未修改 Windows 分页设置，未关闭用户应用。

## 安装记录

沿用现有安装和候选位置，只更新 exe 与三个 AxisMeld Python 模块，不新增整套 build/install。
安装前未发现运行中的 Blender；未终止用户进程。

安装 exe SHA256：`6ED27572F02C5D4D28BA8885D33A556F93BB0D107C1314DFEA7CB31EB4E9E6C1`。
编译产物与安装 exe 已匹配；commands.py、tool_hotbox.py、hotbox_runtime.py 三个模块与源码哈希一致。
六个 portable 文件安装前后逐项哈希一致；回退 exe 保持
`F84108D2F474ADF4FD804CBCC9FA16308FC3E22C7718C72082A85628502DE02F`。

安装态日志前缀：`D:/source/AxisMeld-build/compact-hotbox-installed-`；
截图：`D:/source/AxisMeld-build/compact-hotbox-installed-artifacts`。
源码资源候选测试有既有 Cycles 未加载及 PNG ICC 提示；安装态使用自身资源，无 Cycles 缺失提示。
仍有既有 PNG ICC 警告及负向测试的预期警告，不宣称日志零警告。
人工键鼠速度、显示器 DPI 和个人快捷键手感仍以本页人工表为准。
