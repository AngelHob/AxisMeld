# Maya Menu Bar 开发与验收

日期：2026-09-15。源码基线：`bff4cd9448aeec0af09741baef6b9be3a4176397`。

## 已实现

- 顶部接入 Modeling、Rigging、Animation、FX、Rendering 五个菜单集，按隔离 Maya 2026 实际捕获的顺序和层级组织，共43个去重根目录。Current Pane 六菜单继续属于视口局部菜单。
- Maya 缺失功能及未实现 Options 保留灰色入口；Blender 独有能力按 Create、Select、Modify、Windows 等真实用途目录收纳。既有564个语义命令全部可达；加入必要的基础对象创建及独立编辑器窗口。
- File/Edit/Windows/Render/Help 原生能力通过固定67个 key 接入；保留动态 Import/Export/Recent/Undo History 菜单 ID、原生调用上下文、保存参数和条件分支。
- 菜单使用 Blender 图标，正文与 Options 独立；当前层完整分列，保留真实子目录。修复相邻 Options 覆盖正文、原生行阶梯偏移、多列坐标及长标签宽度问题。
- 建模执行前重验窗口、场景及3D区域身份；无3D来源时灰显，不自动切换模式或改变选区。非 AxisMeld 配置继续显示原 Blender 顶栏，工作区标签保留。

## 验证证据

最终安装：`D:\source\AxisMeld-build\maya-menubar-test-install`。

可执行文件 SHA256：`0dc5122a114cfb32b65b8720878451fb18e1d0ba44481abf560662620b268724`。

38个安装脚本资源与源码逐项一致；完整资源指纹：`357ac9cfabea5c10b1b2065872afb48507ac539181579d394c2724048de37c29`。GUI专用36资源子集指纹：`f8d507eb5779bad912b0baeef974c4c8ae84753902927d0968ccead97d208b2e`。

| 验证层 | 结果与范围 |
| --- | --- |
| Python | 新7套69项通过；保留并核验未改动的旧22套179项，合计248项。`menubar-python-suite.json` 保存测试与源码哈希及日志。 |
| 原生数值 | 提取实际 `block_bounds_calc_text` 函数体，旧多列用例失败、新版4组通过；覆盖相邻/末行 Options、多列位置、纵坐标及组内宽度。该层不替代字体和点击实测。 |
| 实际启动 | 43根、2934个目录节点、338个菜单类注册成功，62个图标均为有效 RNA 枚举。启动脚本实际启用候选自带 Maya 配置。 |
| menubar-actions | 真实菜单创建 Cube（8顶点/6面）、Camera、Point Light，各一次 Edit→Undo 恢复；灰 Options 与无3D灰行不执行；Outliner 使用独立新窗口；File→Save Scene As 通过真实文件浏览器保存临时文件。 |
| menubar-sets | 通过实际输入切换五集合，并独立核对捕获参考的顶栏顺序，场景与工作区保持不变。 |
| menubar-layout | 1倍/2倍缩放实际 File/Create/Edit 弹出菜单；完整长标签、Options、原生快捷键、首末项和多列均在测试窗口内。 |
| 旧UI回归 | 最终同一程序和资源运行 native-style、maya-hierarchy，两套通过。 |
| 旧安装保护 | 228个保护文件、前一候选可执行程序及30个脚本资源均未改变。 |

最终各 GUI 日志、截图和测试文件哈希由 `D:\source\AxisMeld-build\menubar-gui-final.json` 汇总。探索中失败的 attempt 不作为最终通过证据。

## 人工验收与边界

统一台账和私人测试网页追加 **MB-01–MB-20**，全部保持待测试。已有253条目录和服务端用户状态保留；当前总目录273条。自动验证不代替用户人工勾选。

待人工补测包括个人场景手感、Copy/Increment、实际导入导出插件格式、Preferences、各用途子目录及复杂多窗口上下文。Maya Rigging/FX/插件算法和未实现 Options 本批仍为明确灰色占位；没有用名称相似的 Blender 操作代替其语义。

2倍缩放的1920像素窗口无法在同一行同时容纳20个完整类别、工作区和右侧 Scene 区。顶栏使用继承自 Industry Compatible 的 **Alt+中键拖动**横向查看；独立实机探针确认可看到完整 Arnold/Help，并返回 Modeling。日志为 `menubar-header-pan-alt.log`。弹出菜单当前层的完整显示单独验收，不缩短类别名或缩小字号。一般更窄的窗口、任意附加组件生成的巨大菜单不属于本次完整显示实测范围。

开发源码在本地分支提交；测试网页作为既有私人站点更新发布。源仓库推送不包含在本批交付中。
