# 可见区域修复与 M2d 首片开发记录

用户于 2026-09-14 明确暂缓人工测试，按既定顺序逐步修复和补齐能力。本记录覆盖两片：热盒可见区域，以及已有单域组件选择的 Shift+RMB 建模菜单。实现、构建、开发验证和独立审查已完成；人工结果保持原状态。

## 可见区域修复

窄视口中的 Tool Header 位于 WINDOW 内部。原布局仍使用整个 WINDOW，因此分页按钮能落到工具横条上；取消后 modal 虽已清空，同一点的 W/E/R 仍被横条上下文接收。旧构建已重现原地 E 未切换 Rotate，以及菜单颜色像素落入横条区域。

本片保留 Blender 原可见区域裁剪，并依据当前 WINDOW 与实际重叠区域的交集排除工具横条、左工具栏和右侧栏。动画期间按完整输入区域避让。绘制按钮、返回区、缺席方向同时平移；手势真实按下点不变。遮挡范围改变后取消旧会话并清理绘制。

没有改变四视图标杆的按钮净距。空间不足时沿用原有完整拒绝，不缩小按钮或间距，不改变用户工具栏显隐。

## M2d 已选组件首片

仅在 Edit Mesh、明确单一点/边/面选择域且有有效选择时接管 Shift+RMB。三个根环按当前选择域固定，打开时不改变模式、活动对象或选区。Object 空白创建保留自己的入口，两者只在实际互斥的 Object Mode / Mesh keymap 共享默认输入。

新增3个根热盒、6个子热盒，31个命令位置复用25个既有语义命令，包含 Merge、Smooth Vertices、Bevel、Poke、Extrude、Dissolve、法线和锐边显示等。Knife 与 Circle Select 为原生持久工具，后续输入仍由原生工具完成。这些数量不是新增25个几何算法，也不改变M3原有缺失计划的统计口径。

Maya Vertex Extrude、Delete Vertex、Face Boundary Bevel、Wedge 等语义不等价的能力保留具体计划与禁用原因。Face Merge at Center 是将同一 Mesh 的所选顶点合并到一个中心点；多 Mesh 分别处理，Face 域操作后原生清空选择，并非把选中面合成一个保留面积的大面。

Object 已选对象/鼠标预选事务、Ctrl+RMB 选择转换、Ctrl+Shift+RMB 当前工具上下文是后续独立片。UV、完整绘制/雕刻/绑定/动画不计入本片；Global 物体缩放按既定决定无开发计划。

## 已完成的开发验证

| 检查 | 结果/证据 |
|---|---|
| 旧版行为 RED | 可见区域：禁用导航上原地 E 未切 Rotate，另有2363个菜单颜色像素落入工具横条；M2d：旧版已有面选择时 Shift+RMB 后 modal 为空，先于任何新模块 import 失败 |
| Python | `python -m unittest discover -s tests/python -p 'axismeld*test.py'`：99项通过，含新上下文/配置/迁移单测与7项可见区域fixture字面测试 |
| Native | Release构建成功；五组相关CTest通过，菜单组61项包含全部radial与Views内缘、中心取消、外延/缺席方向及新根白名单一致性 |
| 可见区域 GUI | standard/narrow/2x quad × mappings/native-style 共六组通过；上/下分窗保留真实遮挡，双向动画、DPI变化、原地WER、真实设置和像素有证据 |
| M2d GUI | 完整 context-modeling 通过，收紧连续宽高像素识别后复验58.97秒通过；三根、真实Poke/Merge/两类Bevel/两类Extrude及一次Undo，Knife/Circle后续笔划、取消/改绑/fallback、multi-Edit与子环往返均已执行 |
| 标杆实测 | 单/四视图的三根截图内缘间距均与同实例Views一致，当前测试字号实测第2/4行95、第3行127逻辑像素；此数字不是所有字体/DPI的硬编码标准，比较的是同环境实际内缘 |
| 配置和安装 | 26份AxisMeld Python/入口/键位资源与源码逐一哈希一致，构建和候选exe一致；原实例7份程序/配置文件未改变，4份配置复制后一致；实际保存的Maya配置经原生keyconfig初始化后，CREATE仅Object/MODEL仅Mesh |
| 独立审查 | 未发现未决生产缺陷；fixture顺序、带遮挡quad、真实multi-Edit和子环覆盖、D-11文案等反馈已处理 |
| 既有入口回归 | 创建25.3秒、普通组件RMB27.5秒、QWER75.9秒、M3建模25.0秒、新候选narrow mappings93.5秒，五组全部通过；与本片主GUI及前片六组共12组GUI验证 |

日志在 `D:/source/AxisMeld-build/`：`visible-region-*-green.log`、`m2d-python-all.log`、`m2d-native-all-green.log`、`m2d-context-gui.log`、`m2d-profiles-green.log`、`m2d-user-config-startup.log`。初次native锚点测试因Select列表从24增到27项而双重夹紧，已用充分高度及明确未夹紧断言修正；未修改生产锚点算法。

测试输入与结论边界：数字键事件须附真实unicode；孤立面原生Extrude Region对照确认为8顶点/12边/6面，保留源面。菜单像素用独立测试色和连续宽高识别，避开坐标轴/3D Cursor污染。斜行视觉留白不是全部取消区，Views同点姿态确有变化；取消验证使用实际中心return区两侧，外延和子环返回仍分别验证。没有为这些测试假设修改生产几何。

## 构建实例与人工记录

使用入口：`D:/source/AxisMeld-build/m2d-ui-test-install/blender.exe`。

当前exe SHA-256：`8A810D8972A9D185F778D943531A340BC96FAAEF87FF2E5FCBAEA734E71C52CE`。构建核验：`D:/source/AxisMeld-build/visible-m2d-install-verification.json`。源码提交以该核验最终记录为准。

用户原主实例位于 `phase2b-ui-test-install`，保留运行和原配置；临时可见区域检查alias已还原旧M3程序。不要使用旧实例验证本片新功能。

统一人工清单：`docs/compatibility/2026-09-14-manual-test-ledger.md`。本轮新增 **VR-01至VR-08、D-01至D-14，共22项**；总计131项，原47个已测试行经逐字核对未改，**84项待测**，继续暂缓。

同 DPI 下拖动 Sidebar 手柄：原生action-zone在热盒模态中不能通过测试入口poll，未实现稳定自动化，保留VR项人工验证。DPI变化取消单独计为已测，不冒充同DPI调整的独立证据；真实鼠标手感、用户常用布局和125/150/200%DPI仍以人工清单为准。
