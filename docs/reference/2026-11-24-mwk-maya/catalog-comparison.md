# Maya 按下时根菜单 ↔ MWK v0.22.0 静态目录对照

日期：2026-11-24。结论：**这10个场景的68个径向槽位，其标签与方向均与固定MWK定义相符；主要差异在少数正文项、分隔数量和可用性。** 不能据此宣称命令行为、释放/取消或完整Maya工作流等价。

## 证据范围

- 只读取主任务指定的10个 `native-01/*.json`，并按指定的活动popup精确取根层：QWER=`tempMM`，RMB=`modelPanel4ObjectPop`，Shift+RMB=`modelPanel4CommandPop`。没有从dump中别的旧popup补内容。
- 每个源文件保存SHA256；菜单由真实Maya GUI中的合成Qt press打开，截图由主任务观察。本子任务未操作GUI，也未执行MWK。
- **仅按下时快照**：部分后续release曾触发fixture场景中的AE/Extrude等意外选择，因此这批目录数据不能证明释放/取消已通过。
- MWK `menus.py` 固定commit `63e33723ad9e81fc79c94c424aa7cf2ee64daf24`；通过Python标准库AST提取字面量、已识别的返回表达式和数据别名，不import、exec或eval第三方文件。没有把README或注释的Maya声称作为验收。
- 本次只比根层。根项 `subMenu=True` 不证明其子目录的内容或行为相同。

## 提取规模与对应定义

“正文记录”包含分隔，不包含Options独立记录；径向和正文都保留原始源索引。

| Press快照 | popup | MWK定义及menus.py行 | 原始记录 | 径向 | 正文记录 | 分隔 | Options |
|---|---|---|---:|---:|---:|---:|---:|
| 12-q-first-lmb | tempMM | OPT_SELECT:951-959 | 6 | 4 | 2 | 0 | 0 |
| 12-w-first-lmb | tempMM | OPT_MOVE:857-890 | 20 | 8 | 12 | 3 | 0 |
| 12-e-first-lmb | tempMM | OPT_ROTATE:892-917 | 22 | 8 | 14 | 3 | 0 |
| 12-r-first-lmb | tempMM | OPT_SCALE:919-949 | 21 | 8 | 13 | 3 | 0 |
| 15-empty-rmb | modelPanel4ObjectPop | RMB_EMPTY:376-379 | 2 | 2 | 0 | 0 | 0 |
| 16-unselected-hit-rmb | modelPanel4ObjectPop | RMB_MESH:233-248 / _object_items:196-230 | 40 | 7 | 32 | 10 | 1 |
| 17-selected-blank-rmb | modelPanel4ObjectPop | 同上 | 40 | 7 | 32 | 10 | 1 |
| 18-create-shift-rmb | modelPanel4CommandPop | SHIFT_DEFAULT:679-712 | 46 | 8 | 19 | 3 | 19 |
| 19-object-shift-rmb | modelPanel4CommandPop | SHIFT_OBJECT:479-541 | 57 | 8 | 29 | 7 | 20 |
| 20-face-shift-rmb | modelPanel4CommandPop | SHIFT_FACE:629-677 | 52 | 8 | 24 | 4 | 20 |

总计：306条根层原始记录=68方向+177正文记录+61 Options；43条分隔记录。QWER、空白RMB、创建及Object Shift根层方向/标签/正文顺序一致；Mesh RMB仅分隔数量有差，Face Shift多一项，详见下文。相同标签的根项菜单标志也未发现差异。

## 最关键内容差异

### 1. MWK Face正文多了 Smart Bevel

Maya `20-face-shift-rmb.json` 正文开头为：

`分隔 → Smart Extrude → Smooth Faces → Assign Invisible Faces → …`

MWK `menus.py:647-651` 则为：

`分隔 → Smart Extrude → Smart Bevel → Smooth Faces → Assign Invisible Faces → …`

`Smart Bevel` 在本次原生Maya 2026.2的这个上下文中没有出现。不能将MWK完整正文直接当成此Maya快照的权威目录；也不能据一次上下文断言所有Maya版本都没有它。

### 2. 可见目录相符，不代表可用性相符

以下Maya根项本次均 `enable=True`，但MWK静态定义明确为空动作或不可用空Sub：

| 入口 | 项目 | MWK静态证据 |
|---|---|---|
| W | Keep Spacing；Update Triad | menus.py:863、887，None |
| E | Free Rotate | menus.py:910，None |
| 空白RMB | Complete Tool | menus.py:379，None |
| Mesh RMB | Vertex Face | menus.py:243，None |
| Mesh RMB | Metadata；Time Editor；Scene Assembly | menus.py:217、226、228，unavailable()；150-152返回空Sub |
| Object Shift | Project Curve on mesh；Transfer Vertex Order | menus.py:503、515，None |
| Face Shift | Assign Invisible Faces | menus.py:651，None |

这是源码能确认的“不可用差异”下限。其他非空动作仍可能被MWK运行时poll或当前Blender数据限制，本次未运行，不能把它们都写为enabled=True；更不能把Maya enabled直接用作Axis能力白名单。

### 3. 两个 Options 在MWK目录中有声明，但其布局不生成格子

- `Project Curve on mesh`：Maya正文后有启用的Options记录；MWK `menus.py:539` 声明Options，但正文动作在503行是None。
- `Assign Invisible Faces`：Maya正文后有启用的Options记录；MWK `menus.py:674` 声明Options，但正文动作在651行是None。

MWK `menu_layout.py:151,179` 只有非None且非Sub动作才构造Options；所以不能只比 `options` 标签集合就判“参数入口已对齐”。本次61个原生Options都能在对应MWK声明中找到，只有上述两项在静态构造条件下被排除。未执行MWK，仍不称已观察其实际UI。

Axis已有独立Options子节点；后续可将“正文不可用、Options仍保留或可用”作为单独fixture，不搬MWK主项与参数格共用enabled的模型。

### 4. Mesh RMB少了三条API分隔记录

两份Mesh RMB在脱敏后根层结构一致：未选中物体命中、已选中后在空白处打开都出现相同根目录。

Maya的线性投影在物体标题后有三条分隔记录，MWK `_object_items` 只有一条；在 `Select Similar` 后Maya两条，MWK一条。因此Maya10条、MWK7条，缺3条，正文动作标签顺序一致。

这描述的是 `itemArray` 记录，不证明屏幕上一定画出10条独立可见横线。需要视觉布局判断时仍读对应截图，不能把API分隔数当像素几何。

### 5. 复选状态与radio必须区别处理

原生 `checkBox=True` 的根项：

| 快照 | True项 |
|---|---|
| W | World、Keep Spacing、Shift Extrude、Shift Duplicate、Update Triad |
| E | Object、Shift Extrude、Shift Duplicate、Free Rotate |
| R | Object、Shift Extrude、Shift Duplicate、Prevent Negative Scale |
| Create Shift | Exit On Completion |

本批唯一 `enable=False` 的根记录是创建菜单 `Exit On Completion`，同时 `checkBox=True`；应保留“勾选但禁用”，不能处理成false。

306条根记录的 `radioButton` 查询全部返回error，fixture统一保留 `value:null,status:query_error`，**没有任何已核验的radio真假值**。其他行的 `checkBox=False` 只是该查询返回值；采集器未查询“是否具有复选框”独立类型，故不能据false断言它一定不是复选项。MWK checked值依赖运行时，本次全部标未观察。

## 可直接复用的对照fixture

公开文件：[catalog.json](catalog.json)。原始提取工具 `build_catalog_fixture.py` 与完整原始输入留在本机研究目录；这里发布的是脱敏固定结果。

每个 `menus[]` 案例有：

1. `native.root_sequence`：完整按下时根序列，保留原始零基 `source_index`、方向、divider/submenu/Options标志，以及enabled/checkbox/radio的值和查询状态。
2. `native.radial` / `native.linear`：按位置和正文分流；Options只按“紧邻前一主项且方向相同”附加，原始Options记录不删除。没有按自动生成的menuItem名字误配。
3. `mwk.radial` / `mwk.linear`：AST静态对应，含源行、Options声明/可构造性、已知None或空Sub；动态状态保留未知。
4. `comparison`：径向差异、正文编辑段、submenu标志差异、Options差异、明确不可用项，均能直接用于审阅或生成Axis测试参数。
5. `native.source_sha256` 和固定MWK commit：可追到原始证据。脱敏仅移除场景名称、命令正文、临时菜单项ID、选区名称、窗口标题/位置；原始证据未改。

建议直接复用的断言：

- QWER根目录：方向/标签和正文分隔顺序按本fixture比较；不比较未核验的MWK运行时enabled。
- Create：8个方向、19个Options声明、正文顺序及Exit On Completion=true且enabled=false。
- Object/Face：Options作为独立期望；Project Curve on mesh与Assign Invisible Faces不因主动作未实现而自动丢参数格。
- Mesh RMB：动态物体标题用 `<object>...`，分别保留“未选中命中”和“选中后空白”两种输入上下文；不硬编码场景对象名。
- 状态错误：`query_error`不能转成false；遇到 `items` 为error字典不迭代为菜单项。本次指定的10个活动popup全部得到list，但代码已作类型检查。

## 验证边界

已核验：10/10精确popup命中、306条根记录守恒、Options相邻关联且方向一致、原始文件SHA256、场景名称/命令/临时ID已移除、AST不执行第三方代码。原始采集文件未改；本报告与脱敏结果作为 Axis 文档归档，未改变 Axis 运行时。

未核验：MWK实际绘制和执行、Maya物理按键/鼠标手感、子目录内容、命令效果/Undo、释放与取消路径。根层相符不是端到端工作流验收。
