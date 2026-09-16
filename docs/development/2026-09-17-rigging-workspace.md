# Rigging 独立工作区

## 用户要求与范围

用户要求将蒙皮作为参考 Modeling 的独立 layout，随后明确名称为 Rigging，并补充：既保留 Blender 原有 rigging 功能，也参考 Maya Rigging 的 Skeleton 和 Skin 增加功能占位。本轮不实现缺席的 Maya 专有算法，不增加 Constrain、Control、Bifrost、Cache 等根菜单。

## 设计

- 在 `release/datafiles/startup.blend` 中添加唯一 Rigging Workspace，复制 Modeling 的 3D View、Outliner、Properties 几何，初始对象模式为 OBJECT，默认活动页仍为 Layout。用 `axismeld_workspace_role=RIGGING` 标记用途；重命名和复制后仍显示对应菜单。保留现有场景、对象及其他工作区。
- 通过 Blender 原生内嵌启动数据构建发布，让工厂启动和顶部 `+ → General → Rigging` 使用同一份默认布局。不向用户已有 startup 或旧 blend 自动注入页面，不注册 load_post 布局改写器。原生添加、复制、删除、保存和 Load UI 负责生命周期。
- 默认资产生成必须经原生工作区切换建立窗口与新工作区布局的关联。普通 blend 能重开不等于能作内嵌 startup：工厂默认更新直接读取这层关系，因此以重新构建后的实际 factory 启动为必要验收，不用 C++ 空指针绕过来掩盖不完整资产。
- Rigging 视窗固定 Skeleton / Skin 两个领域根。此用途与快捷键选择分离，默认 Blender 键位和 Maya 键位均显示；其他工作区和全局 File/Edit 等栏保持现有逻辑。
- 完整保留已采集 Maya Skeleton/Skin 的原始条目、章节、稳定 ID、独立 Options 和层级。不存在等价实现的仍为灰色占位，原始 Maya 命令仅为资料，绝不执行。原生工具使用其真实 Blender 名称和默认参数，不将相似操作冒充 Maya 算法。
- Skeleton 的 Joints/IK 章节收纳 Add Armature（含 Rigify）、Edit Bones、名称/骨骼集合及 IK；Pose 与约束按用途收进 Pose 子目录，复用真实原生菜单宿主，保留插件回调。Skin 的 Bind/Weight Maps/Other 章节分别收纳 Armature Deform 绑定、Weight Paint/Weights、Vertex Groups/Influences 等已有功能。
- 原 Armature、Pose、Weights 模式根在 Rigging 收入对应领域目录，避免并列重复；原生 View/Select/Add/Object 及非骨架编辑模式的菜单保留。所有原生复杂子目录、参数、operator_context 和插件 append/prepend 必须保留；统一 Blender 图标，参数齿轮继续使用现有右对齐机制。
- 进入工作区不隐式绑定、切到 Weight Paint、改动权重或骨架姿态。原生按钮按真实上下文可用；没有有效对象时禁用相应子目录，不能用替换选区或模式来绕过 poll。
- 区分骨架数据编辑与姿态/绑定使用：本地对象引用链接 Armature 数据时，原生 Pose、IK 和作为绑定目标的能力仍可用；只有真正写骨架数据的 Edit Bones 要求该数据可编辑。
- 修复实际添加/删除验收发现的原生所有权问题：旧程序给 Layout 加任意字符串自定义属性后删除也会复现 screen 引用二次递减。工作区删除先清除自己的 layout.screen 引用，再释放对应 screen 用户，避免释放过程再次遍历同一引用；不移除用途标记或人为增加引用计数。以带/不带属性、活动/非活动及共享使用场景核对所有权。

## 接口与文件职责

- `scripts/modules/axismeld/rigging_workspace_catalog.py`：纯目录投影，声明 `RIGGING_ROOTS`，提供 `integrate_rigging_groups(catalog)`；只向两个指定根插入用途明确的 `rigging_native` 节点。
- `scripts/startup/bl_ui/space_axismeld_native_rigging.py`：原生功能绘图，提供 `draw_entry(layout, context, key)` 与专属菜单/必要模式切换 operator；原生功能使用真实 bpy operator / Menu，未适配功能不增执行绑定。
- `space_axismeld_menubar.py`：识别名称或用途标记、绘制两根及 dispatch `rigging_native` 节点；包装 header 布局只隐藏已迁移的 Armature/Pose/Weights 根，不影响 Modeling。
- `workspace_menu_catalog.py`：在建模投影完成后调用纯 Rigging 投影，原 Maya 导航也能到达新增原生功能。
- `release/datafiles/startup.blend` 与可重跑的 `tools/utils/axismeld_rigging_workspace_asset.py`：仅生成新的默认工作区资产；修改前后输出语义清单，拒绝不合预期输入或重复创建。

## 实施与验证计划

- [x] 先记录旧发布包缺少 Rigging 的失败证据；纯测试断言两根完整 Maya ID/Options 与顺序、不被建模投影改写，以及正确章节和有限目录深度。
- [x] 生成默认工作区，验证保持原11页、默认场景和活动页，新增 Rigging 的三个 area 与 OBJECT 模式；重建内嵌 startup 数据，不复用旧 exe 冒充新默认工作区。
- [x] 接入原生菜单与标记识别；针对测试验证不同 workspace、键位、对象模式、重命名和复制；核对原生菜单完整调用参数与真实插件宿主。
- [x] 独立候选 GUI：工厂默认标签、三栏、+菜单添加、Layout/Modeling/Rigging 切换；实际 metarig 创建、原生绑定和权重操作/Undo、Pose/Armature/Weights 插件入口；保存后新进程重开和旧文件布局保持。
- [ ] 汇总未覆盖人工验收至 RG 后续稳定编号，保留全部原300条与用户状态；更新 CHANGELOG、公开目录、源码提交和预览包，推送 GitHub 并验证 Pages 与下载对应版本。

## 验证边界

只证明工作区、原生入口与占位的组织方式及受测操作。Maya 专有蒙皮算法和 Options 不因入口可见而视为完成；真实生产权重质量、第三方骨架扩展和高 DPI 仍需人工验收。新默认数据需记录独立 exe 哈希和源码资源清单，发布前从 ZIP 重新解压启动。
