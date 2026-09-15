# 紧凑建模菜单与公开测试

## 菜单目录调整

用户明确要求把 Vertex、Edge、Face 收回 Edit Mesh，减少建模视窗顶部栏宽度。本次只调整目录位置，不改变功能、参数或调用上下文。

- 建模顶部栏保留七项：Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、UV。
- Edit Mesh 的共享操作继续位于正文；Vertex、Edge、Face 作为其三个子菜单，按此顺序排列。现有 `viewport.modeling.vertex`、`viewport.modeling.edge`、`viewport.modeling.face` 节点 ID 保持稳定。
- 三个组件子菜单通过原生 `VIEW3D_MT_edit_mesh_vertices`、`VIEW3D_MT_edit_mesh_edges`、`VIEW3D_MT_edit_mesh_faces` Menu 宿主绘制，保留 Blender 的插件 append/prepend 生命周期。其他工作区保持原生布局。
- Maya 正文、独立 Options、Blender 扩展、原生绘制提供器和精确别名只移动位置；不摊平子菜单，不新增重复按钮。Curve Projection 仍在 Mesh Tools 内。
- Native integration 从当前七个建模入口递归查找可达目的菜单，允许三个嵌套组件容器；组件不再单独列入 Modeling 顶部栏或 Window 的 Modeling 集合根目录。

## 验证范围

针对性检查七个顶部入口、组件子菜单及原生宿主，核对 231 个 Maya 正文和 161 个 Options、34 项 Blender 扩展、162 个原生放置引用均保持可达且 payload 不变。更新菜单去向 JSON 和本地 HTML，点线面的主路径与备用路径均增加 Edit Mesh 层级。

本次目录检查不替代操作的人工验收；原生动态资产目录的行数没有固定上界，沿用前一轮已记录的人工验证边界。

## 公开试用与反馈

用户要求开发进度推送GitHub，并让所有人从GitHub页面进入网页、试用和反馈。公开门户采用GitHub Pages，静态源码保存在 `tools/testing_site/`，发布文件使用独立 `gh-pages` 分支。仓库首页提供公开测试页、Windows便携预览包、源码分支与反馈入口；不改变现有开发分支或合并未验收功能到集成分支。

公开清单仅导出技术测试步骤与稳定编号，不复制私人云端备注、账户信息或本机路径。历史已测试只标注为维护者历史记录，不推定通过；访客自己的记录初始全部未测，独立保存在本浏览器并可导出JSON。旧版入口作为历史条目标识，新的七根入口以MB-40验收。

默认反馈采用GitHub Issues，查看网页和下载无需登录，实际提交反馈需要GitHub账号。表单预填测试编号、预览包版本、用户选定的结果和复现说明，提交按钮由访问者在GitHub最终确认；本地勾选不冒充已经提交给维护者。私人Sites测试目录同步新增项，原账号的云端测试结果和备注不变。

预览包由已验证的隔离安装制作，包含必要运行文件、许可证、相对路径启动脚本和来源/哈希说明，不带开发调试符号或任何用户场景、配置。发布为开发预览版，GitHub Release绑定对应源码提交，并保留测试记录的版本号。
