# Object Shift+RMB 组合菜单

本批修正用户截图所指出的下方菜单遗漏。来源为本机 Maya 2026 `scripts/others/contextPolyToolsObjectMM.mel`：上方八向1–180行，下方列表181–690行。只提取菜单结构、名称和方向事实，不移植 MEL 实现。

## 结构

同次 Shift+RMB 同时显示八向与下方22个主条目、7处分隔和 Mapping、Booleans、Polygon Display 三个普通级联目录。列表空间不足时分页，必要时侧放；径向按钮仍以 Views 的实际内缘间距为基准。Options 是独立的24逻辑像素点击区，使用 Blender 原生偏好图标；可用性与主行独立。

| 下方入口 | 当前行为 |
|---|---|
| Offset Edge Loop Tool | 进入 Edit，激活 Blender Offset Edge Loop Cut；后续笔划沿用原生工具 |
| Smooth / Options | 给活动 Mesh 添加 Subdivision Surface；默认1级，参数1–6级 |
| Mirror / Options | 活动 Mesh 的 Mirror 修改器；默认X轴、剖切和合并，可选轴及两个开关 |
| Reduce / Options | 活动 Mesh 的 Decimate 修改器；默认50%，参数窗口可改比例 |
| Remesh / Options | 活动 Mesh 的 Voxel Remesh 修改器；默认体素0.1，参数窗口可改大小 |
| Combine | 使用已有 Mesh Join 适配；要求有效的真实多选择 |
| Booleans | Union、A−B、B−A、Intersection 复用已有 Exact Boolean；要求恰好两个有效已选 Mesh，保留原物体 |
| Quad Draw Tool | 复用 Blender Poly Build，不能视为 Maya Quad Draw 算法完成 |
| Polygon Display → Backface Culling | 当前视口的背面剔除设置，并非 Maya 的逐对象显示属性 |

其他下方行与未适配的 Options 保留位置和明确灰显原因。Mapping/UV、Unsmooth、Subdiv Proxy、Crease、曲线投射/切割、整体 Triangulate/Quadrangulate、Separate、Transfer Vertex Order、Cleanup、Connect 和其他显示项仍有能力缺口。Retopologize 的主行与 Options 均灰显：Blender 原生 QuadriFlow 参数窗口在确认时读取当前 active，尚无固定原目标的确认事务；既有 Space Mesh 原生入口维持原语义。

八向标签采用 Maya 名称，但功能仍是原来的三种工具适配（E Append/Poly Build、SW Insert Edge Loop/Loop Cut、W Multi-Cut/Knife）和五个缺口。**上方八向的 Options 与 Soften/Harden 子菜单不在本批完成范围内。** 本批不能称为完整 Maya Object 建模还原或 M2d 全部完成。

## 交互与事务

直接 Shift+RMB 在打开时记录源视口、模式、完整选择、active 和对象/data 身份；完全无选择才读取鼠标预选。显示/取消不选中对象。主行/Options/分隔/级联走廊阻止径向穿透；列表外的空白继续允许有效方向外划。整个组合只由一个持键会话管理，分页不提交建模。

四种修改器仅作用于活动 Mesh，其他已选对象保留。Options 打开只捕获身份；取消无副作用，确认重新验证后才提交预选和创建修改器，确认操作一条 Undo。参数窗口期间改变目标、active、完整选择或 Mesh data 会取消，不能转投另一对象。未提供预选事务的 Combine/Boolean/Display 要求真实选择。

Space → Select 的 Object 入口延续已有“提交时当前有效选择”语义，不提供直接 Shift+RMB 的鼠标预选固定保证；其修改器参数窗口仍在打开后锁定确认目标。

## 后续

优先继续 Object 整体几何作用域与撤销（Fill Holes、Soften/Harden、Extrude），再补 Edit 无选择预选和 Ctrl 系列上下文。上方 Options、Target Weld/Sculpt、完整 Append/Quad Draw、UV 与代理流程需要独立有界设计和验收。统一人工记录使用 OM-01～OM-16；开发自动化与用户手感测试分开。
