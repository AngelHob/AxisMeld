# 全部菜单与热盒按 Maya 实际层级重建

## 用户修正

2026-09-14：用户指出 Maya 不存在一层 56 项的 Display 菜单，并要求所有菜单与热盒逐项对照 Maya。前轮把现有 Display 的 56 个同级节点当作正确内容，再通过分列解决高度，未验证菜单层级，不能作为 Maya 对齐的验收结果。

## 已有证据

`modeling_catalog.py` 根据命令注册表的 `category/section` 生成目录，依次追加可执行命令、别名及缺失能力。它没有使用 Maya 菜单构建顺序，也没有完整表达分隔和独立 Options；因此能力覆盖表不能作为展示树。

本机 Maya 2026 的 `scripts/startup/buildDisplayMenu.mel:865` 明确创建 Heads Up Display、Hide、Show、Per Camera Visibility、Object Display、Transform Display、Polygons、NURBS、Animation、Rendering 等真实子菜单。子菜单中的边、法线、关节和晶格选项不应被集中放在 Display 根层。

## 实施顺序

1. 在隔离 Maya 进程提取公开 UI 菜单元数据，按需触发菜单构建，不执行功能叶条目。保存原始层级、标签、顺序、分隔、Options、状态形态与运行环境；用安装 MEL/英文资源核对延迟构建及条件目录。
2. 覆盖 Common 七菜单、Current Pane 六菜单、Modeling 九菜单，以及全部已实现方向热盒、伴随列表和嵌套目录。每一组记录对照来源和实际差异；不能因为旧审计写“已齐”跳过。
3. 展示树以独立 Maya 参考定义为准。既有命令注册表仅做受信任功能绑定，不再推导层级或插入无依据的目录。执行仍走原有白名单，参考里的 MEL/Python 字符串不得在 Blender 中执行。
4. 未适配的真实 Maya 条目保留原层级及禁用说明；独立 Options 不借用正文执行。动态场景/插件目录依据明确边界处理，不把一次快照里的对象名当固定目录。
5. Blender 专有操作不得混入 Maya 名称目录冒充对应功能；保留其命令、快捷键和已有独立访问能力。方向热盒内部根与菜单栏展示根分别登记，避免为保持内部 ID 把热盒塞进 Maya 不存在的子菜单。
6. 内容正确后保留完整可见、底部对齐、固定行高和 Views 净距；真实 Maya 子目录按原层级进入。分列只作为经过核实的真实目录或极端设备尺寸的空间后备，不再以错误的 Display 56 项作为产品样例。

Blender 扩展目录也不得重新制造单层超长列表：剩余能力按既有 `SPECS.section` 保留分组，每个命令 ID 不变。这些分组仅用于明确命名的 Blender Extensions；22 个 Maya 主菜单始终使用独立 Maya 实际树，不采用注册表分组。扩展和内部 marking 入口可从键位偏好的中心按钮菜单映射访问，不添加到 Maya 的 Modify/Controls 内。

## 验证

绑定复核中发现：旧 `PolygonSelectionConstraints` 指向“选择非流形”，而 `PrefixHierarchyNames` 与 `SearchAndReplaceNames` 均指向未设置操作和范围的 Blender Batch Rename。这三条不能冒充原功能，保留原 Maya 菜单条目及禁用理由，原 Blender 操作保留在扩展目录。Select 的 Deselect All、Object/Component、Grow、Shrink 则接回既有核心操作；明确模式切换和拓扑遍历采用 Blender 语义。

实际入口回归继续检查创建与工具：Maya Create→Polygon Primitives 的七种基本体接同一已实现创建适配器，保留3D Cursor/Blender拓扑及模式边界，独立Options仍禁用。旧 Single/Quad View 菜单命令和明确命名的 Blender Select Tool 放在扩展目录，避免核心命令只剩内部实现而没有可达菜单。

独立参考树与产品树递归比较父子归属、顺序、标签、分隔、Options 及状态类型。单独使用明确命名的合成菜单测试布局容量和覆盖后释放，不能将合成压力数据称为 Maya 菜单。实机展示修正后的 Display 及其 Polygons 子菜单，再回归全部热盒、操作来源和释放行为。更新待测网页中旧 Display 56 项假设，保留历史用户记录。

本次修正完成前不发布“全部菜单已对齐”或“最终候选回归全通过”的结论。已有 A659 原生样式通过仅证明颜色混合修复，不证明菜单层级正确。
