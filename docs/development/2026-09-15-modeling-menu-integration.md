# 建模菜单归类与参数列对齐

本轮按用户六点修正前一版建模视窗菜单。保留原生全局栏，仅整理建模范围，不继续扩展动画、绑定、FX或渲染模块。

## 菜单结构

- 用户已确认：只独立 Vertex、Edge、Face；共享操作放回 Edit Mesh，原 Edit Mesh/Curve 的两项进入 Mesh Tools 的曲线投射分组。其他原有子菜单和章节保持层级，不逐项拆成顶层菜单。
- Modeling 的 Deform、Generate 菜单入口移除；变形通过真实 Blender Modifier 添加和管理。原 Maya 参考数据留档，其他模块不在本轮开发范围。当前建模源范围为排除这两个根后的231个正文和161个独立 Options。
- Blender 原有建模按钮按实际用途进入 Mesh、Edit Mesh、Vertex、Edge、Face、Mesh Tools、Mesh Display、Curves、Surfaces、UV 的相应章节或已有子菜单。移除整包 Blender Tools 入口，不另建一个平行的原生菜单集合。
- 原生复杂子菜单（如 Merge、Unwrap、Add Modifier）继续保持合理层级；避免把内部条目展开成超长菜单。重复功能按完整按钮参数与调用方式核对，不能仅因 operator ID 相同就删除变体。

## 实现与兼容

原生菜单的功能段提取为普通 Python 绘图函数，由原组合和新分类复用；保留 operator_context、操作参数、动态条件、节点资产及原 Menu ID。原生实际 Menu.draw 在 Modeling 调用新组合，其他工作区维持原组合，插件 append/prepend 由 Blender 原生命周期处理。不使用运行时菜单录制或私有回调重放。

Options 保持独立按钮；菜单同一列使用统一右侧参数槽，短长标签、灰显和状态图标均不改变齿轮的右侧位置。参数未适配时仍灰显，不用齿轮替代正文执行。

## 验证和交付

以原生按钮语句、参数、调用模式及菜单子树的完整清单核对迁移，验证原生工作区和插件入口；独立GUI检查新分类、Modifier添加/撤销、至少一项原生独有操作、短长标签齿轮位置与灰项不执行。输出新的独立候选和修订后的菜单去向表，追加人工检查至原私人测试网页，保留旧编号和用户状态。旧13根以及全2468项仍在Modeling入口可达的验收要求由本轮明确范围接续。

## 最终范围与核对口径

建模菜单为 Mesh / Edit Mesh / Vertex / Edge / Face / Mesh Tools / Mesh Display / Curves / Surfaces / UV。34项已有Blender扩展归入Vertex 8项、Edge 6项、Face 14项、Edit Mesh 6项。菜单去向表分别核对Maya来源和Blender来源，避免将原生能力重复计为Maya算法实现。

当前Maya来源392项（231正文、161 Options），85项绑定既有操作、307项灰占位。原生162个模式放置引用包含149个保留绘制、11个与现有命令完整等价的别名、2个Edge/UV Seam原生等价别名；无遗漏或重复引用。Curve声明按模式复用于Surface，因此135个唯一源条目不等于162个放置引用；动态provider内部条目也不计作固定按钮总数。

Options对齐在C++最终菜单列边界确定后完成：保持齿轮宽度，将齿轮移到最终右侧，正文吸收新增宽度。普通尾部图标、纯图标行、状态图标和纵坐标保留原几何。独立100%/150%界面缩放测量中，四种标签长度与勾选行的齿轮中心横坐标差为0，右边距均为3像素；扩宽正文区域可执行并Undo，灰齿轮不执行正文。

Curve与Hair Curves按实际模式使用各自原生根Menu宿主；四个Control Points/Segments宿主通过原生menu_contents接入分类目录。每个来源在同一用途目录只展开一次，目录筛选include保持，append/prepend由Blender菜单生命周期执行。不会复制或重放插件私有回调列表。Unwrap与Modifier内联provider的图标只在启用Maya键位的Modeling视窗补齐。

人工测试新增MB-35至MB-39，网页原287个编号及初始状态保留，现292项；后续人工结果仍由原服务端进度记录保存。旧13根、Components和Blender Tools说明保留为历史，以新条目验收。

验证边界：静态菜单目录和受测操作的结果不代表所有Maya算法已经实现；未适配Options仍灰显。原生节点资产目录和第三方插件动态内容继续使用原提供器，数量取决于用户安装与资产库；大量动态内容的滚动/高度行为仍待人工检查，固定行数估算不能作为其无滚动的证据。

针对自动化共103项、9个独立进程套件通过，日志 `D:/source/AxisMeld-build/modeling-menu-integration-unit-final.log`。原生12个Menu在28种模式/编译条件组合中与提取前的绘制输出一致；去向网页13项浏览器验证通过。菜单路由生成器在最终生产源冻结后重新生成并通过 `--check`，更新源码哈希不改变路由内容。

最终独立候选为 `D:/source/AxisMeld-build/modeling-menu-integration-test-install/blender.exe`，程序SHA256 `969c97c527df661df34fea41400ecea921195550c6440b697fc505683ac9fb29`；44个安装资源逐项等于源码，GUI的42资源指纹为 `0010b28d15dcf02cd409620c8bed23381173ce6830edc7a498801bf01b377073`。综合GUI及同快照齿轮套件均PASS/exit 0，日志分别为 `D:/source/AxisMeld-build/modeling-menu-integration-gui04.log` 和 `D:/source/AxisMeld-build/modeling-menu-integration-geometry-final.log`。实际覆盖细分、UV Bounds投影、Modifier各一次Undo，原菜单插件prepend/append各一次及顺序，Curve/Surface/Hair上下文，以及原生Layout往返。早期GUI失败来自相似菜单标题/探针文字的图像识别误判，失败源码与截图留档；以限定当前弹窗区域和不同探针标签修正观察器，未放宽产品断言。
