# AxisMeld 五小时批次集中验收

## 2026-09-11 人工反馈修正版（当前测试程序）

本节取代下方五小时冻结版的程序身份；旧清单保留为历史证据，不用于验证当前exe。
当前exe SHA-256：`7A735492DD5A006CFA0B0E30BC0D945A4FD97981758A3D79A23484636534F3C1`。
仍使用同一个`D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`，只更新编译后的exe，
不新增完整安装目录，不修改个人配置或Python语义模块。第4项Alt/Shift默认保持不变。

| 用户反馈 | 本次修正 | 重点手测 |
|---|---|---|
| 二级热盒不够显眼、入口底色不一致 | 椭圆按钮和位于热盒上的独立菜单入口共用中灰底及透明度；入口保留原生箭头和高亮，展开的连续菜单仍沿用Blender主题 | H5-00：一级/二级对比、入口同色、文字和高亮可读性 |
| 二级按钮长短不齐 | 同组动作按最长项统一横向宽度，整段延长区域可点击；保留24px高度、字体和4px间隙，Style尾部入口独立按菜单内容定宽 | H5-00/04：Views、Controls等宽及窄窗/四视图可达性 |
| 跨级拖曳退回 | 原生菜单展开后，无关背景热盒只显示不命中；当前路径入口、普通菜单兄弟项和Back保留 | H5-02/03：按住拖往三级、四级，途经其他热盒按钮；返回、取消及松键 |
| 菜单间距过大 | 普通级联菜单间距由10变0，左右或上下贴边；一级中央留白及椭圆内间距不变 | H5-04：标准、窄窗和四视图的贴边与可达性 |

### 等宽与同色追加验证（2026-09-11 11:09）

原版先出现预期失败：`h5-uniform-width-red.log`证实短按钮延长区域尚不可命中，
`h5-uniform-color-red.log`实际GUI显示Style入口背景亮度0.141、旁边热盒0.359。
修改后入口/热盒实际取样约0.361/0.359，字形、箭头及原生悬停高亮保留。
窄窗使用短视图名称，优先保留Style入口；七个实际视图方向均可达，不缩小字体。

41项原生布局测试、41项Python测试、5组CTest通过；构建及C++格式检查通过。
9组实际GUI通过：contrast、drag、native-style（1×/2×）、quad、
mappings-standard/narrow/quad、release、guide；均使用隔离测试配置。
日志位于`D:/source/AxisMeld-build/`，前缀`h5-uniform-`；原生最终日志为
`h5-uniform-native-green-r2.log`。独立静态审查未发现可执行问题。
当前安装exe与build同SHA；6份portable配置逐项与本轮更新前一致，回退程序未变，测试进程已退出。
只复用原安装目录，没有推送或合并。实际鼠标手感仍待按H5-00/02/04集中验收；旧Tool Header极窄遮挡不在本次修改范围。

### 上一轮反馈修复验证（历史程序 FFAB969E…15A823）

修复前证据：`h5-feedback-native-red.log`两项失败；真实GUI
`h5-feedback-drag-red.log`显示跨越背景入口后目标设置未执行，
`h5-feedback-contrast-red.log`显示二级底色比一级更暗。修复后对应两个GUI专项通过，
真实设置只分派一次；取样一级亮度0.212、二级0.359。日志均位于`D:/source/AxisMeld-build/`。
最终验证（2026-09-11 10:46）：40项原生布局测试、41项Python测试、5组CTest通过；
9组GUI运行通过：drag、contrast、mappings-standard/narrow/quad、native-style、menus、release、guide。
日志前缀`h5-feedback-`；映射最终日志为`h5-feedback-mappings-{standard,narrow,quad}-r2.log`，
布局最终日志为`h5-feedback-native-final.log`。独立静态审查无阻断项，其建议的窄窗上下贴边断言已补齐并通过。
程序与build同SHA；6份portable配置与本轮更新前逐项一致；回退exe仍为`F84108D2…DE02F`，测试进程已退出。
仅本地更新，没有推送、合并或新建完整安装目录。原始libpng警告保留，不作为失败或隐藏。
人工手感尚未验收；下方历史Tool Header极窄遮挡问题仍未修复。

## 五小时冻结版记录（历史）

状态：实现、自动验证与整批代码终审已完成，候选已统一交付，人工验收待进行。
约定工作窗口2026-09-10 23:53:35至2026-09-11 04:53:35（北京时间）；04:53:38完成交付身份复核，随后停用本批定时任务。
本表是唯一集中审核入口；实际开发与验证在04:25前完成，后续为冻结与交付，不表示连续计算满5小时，也不表示体验已获认可。
交付复核：程序、4个源码/安装模块、6份portable配置、回退程序及17份GUI日志均与冻结清单一致；受审源码未变，Blender进程数0。未推送、合并或删除。

## 最终程序与变更

最终候选的生产检查点为 `837f1af156d`，测试至 `ee4fcaf04ff`，整批终审范围`137c428cf0d..5b89b65311d`已通过；
程序仍复用 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`。
当前 exe SHA-256：`7152D3288CFCFBED587ADE9F9C7F4537A97CF71746FA37514C829E0ADE5AC87C`。
版本标识已实测为`AxisMeld 0.1.0-dev (based on Blender 5.3.0 Alpha)`。已停止新增切片，
当前没有终审要求的新修复；交付时只重新核对身份，不重复开发已经通过的内容。
程序/模块、配置保护及17组GUI日志的机器可读证据见[构建核验清单](2026-09-11-batch-artifact.json)。
最新纯Python测试41项、定向CTest5组通过；自动结果不等同Maya物理手感验收。

| 本批变更 | 实现状态 | 自动化证据 | 人工编号 |
|---|---|---|---|
| 短设置选项列表原生菜单 | 完成，独立终审通过，待统一手测 | 1a61bb81f3c + 45e9357edbf + 8965cbe5c58；33/33 原生测试，8 套 GUI/配置回归及窄窗专项通过 | H5-01 |
| 长映射列表及层级操作 | 完成，终审修订复核通过，待手测 | 生产8341fdac9b0、测试86aa564a5d6；38 原生、40 Python、5 CTest；实际映射与禁用行 held 取消补测通过；已知边界见下 | H5-02 |
| 三个基础选择动作 | 完成，整批终审通过，待统一手测 | 生产837f1af156d、测试ee4fcaf04ff；实际选择、一次撤销、不同no-op状态/Recent、个人绑定及9套GUI回归通过 | H5-08 |

## 一次性人工审核顺序

使用 AxisMeld Maya 2026 预设、空白测试场景；先确认程序路径，再检查以下项目。
请按编号集中反馈“通过／失败／偏好调整”；失败时注明单视图/四视图、模式和鼠标键即可。

测试前先保存正在编辑的场景，自己退出旧测试实例，再从上方准确路径启动；不要用一个已运行的
旧窗口判断本次更新是否生效。先记录当前 Rows、Transparency 和中央三键映射，结束后恢复。
H5-02 至少测试一次窄视口：出现上下箭头时，滚到底后立即反向滚一格，并点击一次灰色边界箭头。
H5-07 中热盒设置保存在 `portable/config/axismeld/hotbox_user.json`，键位覆盖是同目录
`user.json`，两者不是同一份文件；不需要为了测试删除个人配置。

| 编号 | 操作 | 期望 / 需要你确认 | 状态 |
|---|---|---|---|
| H5-00 | Space 打开一级，RMB 进入 Views；原地松RMB再进入；观察一级占位行、Style入口和中央左右留白 | 一级不消失；二级没有额外中心按钮；未实现项灰显；原生入口与热盒动作可区分；二级24px/4px间隙、一级38px及左右83.6px留白是否易点 | 汇总既有 B12-17/20/24/26/27/28，待手测；本批不恢复或改写个人配置 |
| H5-01 | Controls → Menu Rows / Transparency，分别点击与按住划选 | 连续原生选项、整块背景；父级保留；设置仅执行一次；视觉分工是否合理 | 自动化通过，留待最终统一手测 |
| H5-02 | Controls → Center Mouse Buttons → 单个鼠标键的完整选项列表 | 目录易浏览、全部选项可达；层级返回、边缘和高 DPI 不误触 | 自动化通过，待手测 |
| H5-03 | Space 保持，选项中先松鼠标、先松 Space、Esc、松非拥有鼠标键 | 无粘键、无场景误操作；按既有所有权规则退出或返回 | 自动化通过，待手测 |
| H5-04 | 1×/2×、四视图、视口边角打开所有新增列表 | 避让直接入口及 Views 真实返回起点；窄窗可见项数/翻阅手感自然；特别核对下述Tool Header未修复遮挡 | 测定尺寸自动化通过，已知遮挡保留，待手测 |
| H5-05 | 完成热盒操作后立即 W/E/R；各四视窗拖轴、点轴后空白 MMB | 工具正确、轴保持；不卡住或退化为普通抓取；极窄横条处原地W例外仍未修复 | 继承B12-11，绘图区回归通过，待手测 |
| H5-06 | Alt 导航及固定正交视图；重开热盒并切回一级 | 右/下拉近，左/上拉远；固定视图不被 Alt+LMB 旋转 | 当前映射安装自动回归通过，最终手感仍待确认 |
| H5-07 | 修改后重启、切换配置覆盖开关，再恢复用户偏好 | 公共默认与个人覆盖仍独立；不丢设置或污染默认 | 使用私有测试配置，最终手测 |
| H5-08 | Common → Select：Object全选；网格Edit全选/扩展/收缩；每次先试W/E/R，再只撤销一次 | 选择范围符合预期；隐藏/不可选不误选；Grow/Shrink不自动切模式；一次撤销回到操作前。采用Blender原生拓扑规则、默认无新快捷键，请确认是否适合作为adapted入口 | 安装态实际结果/撤销/个人绑定已通过，待统一手测 |
| H5-09 | Space+RMB划向视图；进入Style再拖回真实起点、短划切视图；试松开后无按键移动 | 按下点至指针有细线、文字在线上方；退回起点能恢复方向选择；松拥有鼠标键后线消失；New Camera仍灰显不执行 | 汇总 B12-18/19/21/22/23，既有行为回归，不算本批新增功能 |

## 需用户拍板的事项

2026-09-11人工反馈：用户已认可Select All按Object/mesh Edit当前上下文执行且不自动换模式，
也已认可Grow/Shrink仅mesh Edit、使用Blender原生Face Step规则。仅这两项语义获认可，
不代表H5-08全部实操、撤销或整批手感已通过。Recent按原生命令返回状态记录的说明待解释确认。
新增反馈已落实于顶部“人工反馈修正版”：二级热盒灰底突出、Center Mouse Buttons跨级拖曳隔离、
普通菜单与子菜单边缘贴合。Alt旋转中Shift吸附标准视图需与Maya的Shift约束相机行为区分，暂不改默认。

新增选择动作的差异集中如下，不要求现在逐项答复：

| 动作 | 本版行为 | 不承诺的Maya等价 |
|---|---|---|
| Select All | Object选择当前可选对象，mesh Edit选择当前组件；不自动换模式 | 不复刻Maya DAG/UFE选择规则 |
| Grow / Shrink | 仅mesh Edit，使用Blender原生Face Step拓扑规则 | 不保证与Maya的扩展/收缩算法一致；面选择可能包含共顶点的对角邻面 |
| Recent与无变化操作 | 只依据原生FINISHED记录；CANCELLED/PASS_THROUGH不记录 | 可见锁定对象或Edit无变化时仍可能FINISHED，不以视觉变化判定历史 |

三个动作均默认不新增快捷键；A仍是Frame All，F8–F11和W/E/R保持原绑定。个性化可通过既有
`selection.select_all` / `selection.grow` / `selection.shrink`语义ID覆盖，不污染公共默认。

- 热盒与连续菜单组合的视觉偏好、收紧后的命中容错、物理鼠标平滑度只能由用户确认。
- Transparency 仍作用于热盒按钮背景/边框；普通原生菜单沿用 Blender 主题背景，不跟随
  热盒透明度变淡。这延续已有 Style 菜单行为，H5-01 一并确认是否符合你的视觉偏好。
- 任何新增原生建模适配都应逐条写出与 Maya 的差异；确认前保留 adapted 标识。
- 本批尚未遇到需扩大权限或全局架构的新决策；遇到后在这里追加证据和选项，不能默认批准。

## 本批代做的决定

这些是为了不中断本批而做的可逆决定；不表示用户已经认可视觉效果。

| 决定 | 依据 | 如果不合适，返工范围 |
|---|---|---|
| 短列表阶段，同层热盒菜单入口各画独立背景，叶子列表连续 | 否则 Controls 的三个入口会被一整块背景跨间隙连接 | 局部绘制分组，可独立调整，不改输入契约 |
| 曾在新审查代理受数量限制时复用已完成的独立审查者 | 保持作者与审查者分离，并提供新范围、完整新 diff | 旧上下文可能分散注意力；可针对同一 diff 再审 |
| 增加真实字体窄窗与 2× 四视图专项，不把通用 quad PASS 当作新列表覆盖 | 新列表尺寸与标签必须由真实窗口证明 | 只增加有限测试时间，不改变用户行为 |
| 长菜单采用显式独立入口标记区分背景块 | 原生列表内的子菜单行应连续，热盒上的入口应分离 | 局部 C++ 布局/绘制接口返工，不迁移配置 schema |
| 溢出列表使用原生上下图标行，复用一项滚动和已有鼠标所有权 | 保留文字尺寸，避免新增弹窗输入处理器 | 局部导航视觉/操作微调；自动悬停滚动本批不承诺 |
| 为尾页滚轮缺陷允许局部修正现有事件函数中的 offset 算术 | 分页页首上限与旧子项数上限不一致，反向滚轮会出现空行程 | 局部 C++ 布局/事件算术与回归，不扩展全局输入架构 |
| 禁用的原生滚动箭头点击后保留当前列表 | 实测原来会被当成空白点击退回一级；禁用导航应不执行操作 | 一处原生控件按下分类与回归；旧椭圆和其他禁用项保持原状 |
| 将最初无效的旧版渲染 RED 留作明确未满足的历史证据项 | 精确旧程序已在发现夹具错误前被替换；不把后补历史构建伪装为当时失败 | 缺少旧渲染器的真实回归敏感性证明；保留原生语义 RED、真实禁用箭头 RED/GREEN，并加强当前 GUI 断言 |
| 取消后的 W/E/R 验证限定在明确的绘图区，保留 Tool Header 重叠问题 | 极窄视口上翻行与工具选项横条重叠；松键后 modal 已空，鼠标移回绘图区才恢复按键 | 后续可能需可用区域避让或键盘上下文修正；本批不声称停在重叠横条上也能立即 W/E/R |
| 在菜单审查关闭后只启动三个原生选择动作，默认不绑键 | 同步原生操作范围可控，明确标为 adapted，避免扩大 Maya 语义承诺 | 局部适配器、菜单和测试可返工；不迁移文件格式或快捷键 schema |
| 将既有Select椭圆测试的子项数从5更新为8，保留几何断言 | 新目录确实追加3项，安装前测试发现旧数量假设 | 仅测试夹具数量返工，不放宽椭圆/间距/Back断言 |
| 三个新选择动作显式启用原生子命令撤销 | 实际一次撤销跳过操作前状态；本地bpy调用默认不记录子撤销 | 局部适配器/撤销测试返工，不给通用包装器加UNDO，不改全局历史 |
| 无可见选择变化时，Recent仍跟随原生返回状态 | 可见但不可选对象可能使原生全选返回FINISHED；真正全部可见对象已选则CANCELLED | 局部状态/历史测试与说明可调整；本批不增加几何比较或改变历史策略 |

## 未完成与已知边界

- Global 物体缩放保持既有延期；不在本轮恢复开发。
- 极窄视口有实测未修复边界：392×281逻辑像素窗口中，原生上翻行点(100,335)同时落入
  Tool Header(2,324,392,26)与Window(2,95,392,281)。取消热盒后保持鼠标不动，W未切换工具；
  松键后的modal已清空，移至绘图区中心后W/E/R恢复。H5-04/H5-05需一并复核这处视觉遮挡和
  上下文差异；本批未扩展可用区域避让，不把移回绘图区的PASS称为该问题已修复。
  原始无移动失败证据：`D:/source/AxisMeld-build/batch5h-mapping-gui-fix2-no-move-failure.log`。
- UV 编辑器大改、展开/布局算法、临时吸附/枢轴仍是后续独立范围。
- 跨新窗口残留释放隔离仍为独立已知问题；相关文件/新窗口命令保持禁用。
- 连续菜单使用 Blender 原生组件绘制，输入仍由父级热盒统一管理；本批不新增普通弹窗的
  键盘焦点或自动悬停滚动，长列表使用明确的上下控件与滚轮。
- 自动化通过不代表 Maya 全面对等，也不代表人工体验验收通过。
- 极窄遮挡的源码边界与后续回归门槛见[专项预检](../development/2026-09-11-hotbox-visible-region-preflight.md)；尚未修复，不需要另开一次人工审核。

## 开发记录

批次 0：计划和续作机制已建立，基线纯测试 30 + 26 + 14 通过。
后续每个完成批次追加提交、测试日志、截图路径和对应手测编号；最后只保留一份清晰交付摘要。

批次 1 证据：`D:/source/AxisMeld-build/batch5h-settings-` 前缀，原生样式/菜单/release/
profiles/manipulator/overlay/guide/quad 全部通过；两份预期 RED 日志单独保留为
`native-list-red-baseline.log` 和 `native-list-red-coalesced.log`，不混作成功记录。
最终正常截图位于 `batch5h-settings-native-list-green/`，主控查看了 Rows 1× 和 Transparency 2×。
主控另核对构建/安装 exe 同哈希、portable 6 文件与备份逐项一致、回退版未变、Blender 进程数 0。
独立任务审查、补测复核及切片终审均通过；不代表五小时开发已经结束。已知 libpng 和预期
warning 输出仅作为非阻断诊断噪声保留，不隐藏原始日志。

审查后补测：实际分割视口 392×375 逻辑像素（1×）和四视图单格 392.5×212.5
逻辑像素（2×）分别逐项选择 Rows 3/3、Transparency 5/5，通过标签、入口分隔、设置值和
Space 清理检查。日志为 `batch5h-settings-native-list-narrow.log` / `batch5h-settings-native-list-quad.log`。
这证明的是这两种实际尺寸，不能扩称任意小窗口都可容纳。
主控定向回归另有 `batch5h-short-main-ctest.log`（5/5）、`batch5h-short-main-python.log`
（26/26）、`batch5h-short-main-input.log`（14/14）。

批次 2 当前证据：`batch5h-mapping-gui-final-standard.log` / `final-narrow.log` / `final-quad.log`
（共同前缀 `D:/source/AxisMeld-build/batch5h-mapping-gui-`）。标准显示13项；实际窄窗392×281
逻辑像素显示8项，四视图392.5×212.5逻辑像素（2×）显示5项并带上下箭头。三种鼠标映射的
全部13项均经真实页面可见性检查；尾页多次下滚后上滚一格分别为5→4和8→7，无反向空行程。
禁用箭头新鲜点击保持当前页，设置/命令不分发；独立 RED/GREEN 日志保留。
最初旧安装的原生渲染 RED 尝试因坐标夹具错误只打开一级，不能作为渲染失败证据；报告已明确
披露这个流程缺口，不将其冒充有效 RED。原生几何测试与禁用箭头的独立实际 RED 不受影响。
正常主题截图分别位于 `batch5h-mapping-gui-final-{standard,narrow,quad}-artifacts/`。
覆盖口径：标准布局的完整13项自动视觉断言是Left；Middle/Right有实际设置结果检查。
三种鼠标映射各13项逐页可见的完整矩阵来自narrow/quad，不将它扩称为标准布局3×13视觉逐项断言。
主控独立核验构建/安装同哈希、6份配置逐项一致、回退版不变；另外串行通过
`batch5h-final-navigation.log` 和 `batch5h-final-view-lock.log`，验证本安装的镜头导航和固定视图。

批次2终审补测：`batch5h-mapping-gui-fix2-{standard,narrow,quad}.log` 均通过。
新增四条实际路径：narrow与quad各测禁用previous按住后Space先松、禁用next按住后Esc取消，
随后补齐拥有鼠标键释放。检查无命令/设置分发、modal清空，移回明确绘图区后的W/E/R及
重新打开热盒选择实际设置；不是所有坐标的原地按键保证。最终测试提交86aa564a5d6，
独立终审提出的该项经一次修订复核关闭，无新增阻断项；极窄Tool Header边界单列保留。

批次3当前检查点：837f1af156d。主控追加27项hotbox纯测试、14项input测试均通过，
日志`batch5h-final2-hotbox-python.log` / `batch5h-final2-input-python.log`。
当前7152D328…E5AC87C安装的`batch5h-final2-navigation.log` / `batch5h-final2-view-lock.log`
均通过，不能以这些自动结果代替物理鼠标手感验收。源码与安装4个Python模块逐项SHA一致；
build/stage exe同SHA，portable6份文件与备份无差异，fallback保持F84108D2…DE02F。
独立任务审查要求补齐：Select ellipse分页的旧item_count5，以及Object已全选和Edit无变化
时的返回状态/Recent策略；这些测试完成复核前不将三个命令写入最终完成表。

批次3任务复核现已通过：ee4fcaf04ff补齐Select分页8项，以及Object可见锁定对象FINISHED、
真正全可见对象已选CANCELLED和Edit全选无变化FINISHED三类Recent分支。最终日志
`batch5h-selection-fix1-gui-r3.log`（6.516s）、`batch5h-selection-fix1-native-ctest-final.log`（1/1）。
这些是原生状态适配，不以“画面没变化”推断命令失败或跳过历史记录。独立复核无新增阻断项。

整批终审结论：Yes，本地候选通过；无新增Critical/Important阻断。不要求新修复波。
极窄Tool Header遮挡仍是已接受延期的Important功能边界，不降格成纯视觉偏好。
原始渲染RED无效、作者所列历史py_compile日志缺失均如实保留；后者已有独立新日志
`batch5h-final2-pycompile.log`证明当前语法通过，不伪称找回历史。原始libpng警告不隐藏。

最终候选追加回归：`batch5h-final2-native-{narrow,quad}.log`逐项验证Rows3/Transparency5；
`batch5h-final2-guide.log`验证1×/2×引导线及释放/取消，`batch5h-final2-overlay.log`验证
父级保留与原地拥有鼠标键释放；`batch5h-final2-menus-quad.log`验证实际2×四视图与末页。
对应PASS和17组GUI日志哈希均已纳入构建核验清单，源代码自整批终审后未再改变。

截图参考（自动测试画面，不替代你的视觉验收）：

- [当前Select热盒](D:/source/AxisMeld-build/batch5h-selection-fix1-artifacts-r3/selection-select-menu.png)
- [四视图中的原生映射列表](D:/source/AxisMeld-build/batch5h-selection-mappings-quad-artifacts/mapping-quad-normal-theme.png)
- [一级保留与二级Views](D:/source/AxisMeld-build/batch5h-final2-overlay-artifacts/overlay-1.0-held.png)
