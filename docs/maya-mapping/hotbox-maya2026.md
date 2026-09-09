# Maya 2026 热盒菜单对照与接入清单

日期：2026-09-09。状态：Phase 2B 自动化验证完成，等待 B12 人工手感验收；灰色目录仍是规划项。
关联：[Phase 2B 设计](../superpowers/specs/2026-09-09-phase-2b-maya-hotbox-design.md)。

“已接入”只表示列出的自动化行为已经实现，不表示 Maya 数值或物理手感一致。下文未特别列出的叶命令不自动进入 2B。
`adapted` 表示存在明确语义差异；“规划”不是 `exact` 或可运行承诺。

## 1. 主目录及首批内容

| 行/组 | Maya 目录或区域（保持顺序） | 2B 接入目标 | 后续范围/差异 |
|---|---|---|---|
| 公共 | File | 顶级目录预留，禁用 | 新建/打开/保存/导入导出在文件对话框转交验证后单独接入 |
| 公共 | Edit | 顶级目录预留，禁用 | Undo/Redo、复制等接入前核对撤销和上下文行为 |
| 公共 | Create | 顶级目录预留，禁用 | 多边形基本体；参数不能假装 Maya 等价 |
| 公共 | Select | 已有对象/组件、点/边/面模式 | Object/Component 与 Blender 模式仍 adapted |
| 公共 | Modify | 已有 Move/Rotate/Scale 工具入口 | 枢轴/冻结/重置分别立项；不改 Global 缩放 |
| 公共 | Display | 顶级目录预留，禁用 | 隐藏/显示与场景显示类命令，不混入无关视图项目 |
| 公共 | Windows | 顶级目录预留，禁用 | 编辑器及设置入口需明确窗口/区域策略 |
| 当前视窗 | View | Frame Selected、Frame All | 相机相关命令按 Blender 语义单独适配 |
| 当前视窗 | Shading | Wireframe、Smooth Shade All 的既有适配入口 | Blender solid 模式不保证 Maya 光照/材质结果相同 |
| 当前视窗 | Lighting | 顶级目录预留，禁用 | 视窗光照策略，不直接对应生产渲染灯光 |
| 当前视窗 | Show | 顶级目录预留，禁用 | 对象类型可见性/overlay 需逐项映射 |
| 当前视窗 | Renderer | 顶级目录预留，禁用 | 不把 Blender 渲染引擎伪装成 Maya Viewport 2.0 |
| 当前视窗 | Panels | 七视图入口和单/四视图入口 | 标记 Blender 槽位与 Maya 摄像机/布局语义不同 |
| 中央 | Recent Commands | 10 项会话内可重放热盒命令 | 不收集完整 Maya 式应用历史；adapted |
| 中央 | Maya 对应区域 | AxisMeld 中央按钮，默认右/左/中键视图菜单 | 独立品牌；自定义覆盖按键分离 |
| 中央 | Hotbox Controls | 已接入行显隐、透明度、三种显示样式及中心 LMB/MMB/RMB 映射 | 设置与预设偏好共用模型；Center Zone RMB Popups 的 Maya 完整行为不在本轮 |
| Modeling | Mesh | 目录预留，禁用 | 对象级网格操作 |
| Modeling | Edit Mesh | 目录预留，禁用 | 组件级网格操作 |
| Modeling | Mesh Tools | 目录预留，禁用 | 持续交互式建模工具 |
| Modeling | Mesh Display | 目录预留，禁用 | 法线/软硬边等网格显示数据 |
| Modeling | Curves | 目录预留，禁用 | 曲线工具，非首轮重点 |
| Modeling | Surfaces | 目录预留，禁用 | NURBS 能力不同，不同名替代 |
| Modeling | Deform | 目录预留，禁用 | 变形功能逐项映射，不直接列全部 Blender 修改器 |
| Modeling | UV | 目录预留，禁用 | UV 工作区和命令接口见第 4 节 |
| Modeling | Generate | 目录预留，禁用 | 不将 Maya 特有生成系统标为已支持 |

公共组名称依据 Maya 文档，Modeling 九项顺序依据本机原版 `initMainMenuBar.mel`。
视窗项目按 Maya model panel 分组规划；每个实际叶项接入前核对默认位置、分隔和参数入口，
对照条目保存来源及差异。表中“七视图入口/单四视图”是 Panels 适配目标，不声称完整复刻其子菜单。

## 2. 区域菜单与鼠标键

| 区域 | Maya 默认功能类别 | AxisMeld 阶段 | 映射规则 |
|---|---|---|---|
| Center | 常用模型视图 | 2B | N 透视、E 侧、S 前、W 顶、NW 左、SW 后、SE 底；NE 不填视图 |
| North | 面板布局 | 后续区域批次 | 复用 Blender 布局能力；不破坏用户工作区 |
| South | 面板类型 | 后续区域批次 | UV/Outliner 等编辑器按显式区域目标打开 |
| West | 选择类型/遮罩 | 后续区域批次 | 对象/组件及对象类型过滤分开 |
| East | 面板/界面可见性 | 后续区域批次 | Blender 无对等项需注明 |

默认未自定义的中央 LMB/MMB/RMB 都能调用视图菜单；用户可在 Hotbox Controls 或
Keymap 预设偏好中逐键映射到已注册菜单或禁用。个人差异原子写入
`hotbox_user.json`；关闭文件覆盖时只保留本次会话，不写磁盘。Recent 只保留本次会话中
成功完成、当前仍可用且明确允许重放的最多 10 条热盒叶命令。
Maya 的 `Center Zone RMB Popups` 是可选功能组弹出行为，不是本轮中央右键视图的同义名称。

## 3. 建模后续接入优先清单

下表只是规划候选，不能直接通过名称匹配 Blender operator 后标完成；每项需补
输入对象/组件、参数、结果、撤销、模态行为和与 Maya 的差异测试。

| Maya 路径组 | 优先核对的动作 | 主要适配风险 |
|---|---|---|
| Mesh | Combine、Separate、Boolean、Smooth、Reduce、Cleanup | 对象合并/材质/历史与算法差异 |
| Edit Mesh | Extrude、Bevel、Bridge、Merge、Detach、Extract | 多组件操作、参数/拓扑、撤销边界 |
| Mesh Tools | Multi-Cut、Insert Edge Loop、Connect、Target Weld、Slide Edge | 工具保持、结束按键、预览及吸附 |
| Mesh Display | Soften Edge、Harden Edge、Reverse、Conform | 分裂法线/平滑标记和显示差异 |
| Create | Polygon Primitives | 轴向、尺寸、分段与创建位置 |
| Modify | 枢轴、变换重置/冻结类操作 | 不等同于直接 Apply Transform；Global 缩放不在开发范围 |

命令正式接入时沿用 `commands.py` 的稳定标识及 `adapter.py` 适配模式；本表不提前
声明尚未定义的建模 API。目录标签不充当 ID，第三方扩展不得覆盖公共 ID。

## 4. UV 独立接口规划

这些 ID 是拟定公共语义身份，不代表代码已注册。具体 Blender 实现、参数和菜单叶路径
由 UV 专题规格确定；已公开后不能因更换算法随意改名。

| 能力组 | 拟定语义 ID | 边界 |
|---|---|---|
| 工作区 | `uv.editor_open` | 显式编辑器/窗口管理，不改任意用户面板 |
| 投射 | `uv.project_planar`、`uv.project_cylindrical`、`uv.project_spherical`、`uv.project_automatic` | 明确网格、选择、UV 层、投射参数；不保证 Maya 算法一致 |
| 选择 | `uv.select_shell`、`uv.select_border`、`uv.select_overlap` | 3D 选择、UV 选择同步及 shell 定义单独验证 |
| 拓扑编辑 | `uv.cut`、`uv.sew`、`uv.move_and_sew` | 不能把 mesh seam 标记直接宣称为即时 UV 切缝/缝合 |
| 展开优化 | `uv.unfold`、`uv.optimize` | UV 层、固定点、退化输入、取消与撤销 |
| 整理 | `uv.align`、`uv.straighten`、`uv.orient`、`uv.stack` | 作用于点/边/shell 的选择语义明确 |
| 排布 | `uv.layout`、`uv.texel_density`、`uv.udim_assign` | 尺度、padding 单位、tile 范围、是否允许旋转/缩放 |
| 检查 | `uv.checker_toggle`、`uv.distortion_toggle` | 非破坏性显示，不能污染材质或修改 UV |

所有命令通过能力查询声明“可用/未接入/当前上下文不支持”，失败不得回退到另一网格或 UV 层。
热盒仅负责发现和调用；UV workspace、选择状态、拓扑及算法分别拥有自己的实现和测试。

## 5. 接入完成的判定

单个菜单叶项在测试版启用前必须具备前四项记录；正式宣布体验验收通过还必须具备第五项：

1. Maya 2026 默认菜单路径、功能与来源；非官方推断明确标记。
2. 唯一 command ID、显式上下文要求、实现入口和参数入口（如有）。
3. `exact`/`adapted`/`unsupported` 状态与具体差异；默认不得推定 exact。
4. 输入/取消/撤销/失败测试，以及真实 GUI 操作路径；高风险数据操作独立结果测试。
5. 用户手测结果。无手测只写自动化通过，不写体验已对齐。

第三方模块通过命名空间扩展目录，不修改 Maya 公共基线；个人菜单行显隐和鼠标映射
保存在用户覆盖层，不提交进发行默认。
