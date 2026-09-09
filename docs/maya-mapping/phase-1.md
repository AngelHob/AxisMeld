# Maya 2026 建模输入：Phase 1

## 启用

构建后运行安装目录里的 `blender.exe`，打开 **Edit → Preferences → Keymap**，
在预设列表选择 **AxisMeld Maya 2026**（内部名称 `AxisMeld_Maya_2026`）。
使用 Blender 的 Save Preferences 保存选择。它随源码构建安装，无需安装插件。
首次启动仍允许选择原版 Blender 或 Industry Compatible；不会覆盖已有偏好。

适用范围为 3D View 的 Object Mode 和网格 Edit Mode。其他编辑器沿用 Blender
Industry Compatible 的配置，不代表已经完成 Maya 对照。

## 已适配命令

| 默认输入 | 语义 ID | 当前行为与差异 |
|---|---|---|
| Q | `tool.select` | Blender 框选工具；重复按键保持该工具，未实现按住后的菜单 |
| W | `transform.move` | 移动操纵器；使用 Blender 轴向、枢轴和拖动语义 |
| E | `transform.rotate` | 旋转操纵器；未实现按住后的菜单 |
| R | `transform.scale` | 缩放操纵器；未实现按住后的菜单 |
| F8 | `selection.toggle_component` | 可编辑网格的 Object / Edit 切换；保留上次组件类型 |
| F9 | `selection.vertex_mode` | 进入网格编辑并切到顶点选择 |
| F10 | `selection.edge_mode` | 进入网格编辑并切到边选择 |
| F11 | `selection.face_mode` | 进入网格编辑并切到面选择 |
| F | `view.focus_selected` | 当前区域聚焦；Blender 包围盒与隐藏对象规则 |
| A | `view.frame_all` | 当前区域全部聚焦；未实现 Maya 的历史菜单 |
| Alt + 左键拖动 | `view.orbit` | Blender 原生旋转；相机枢轴、锁定和灵敏度仍按 Blender 设置 |
| Alt + 中键拖动 | `view.pan` | Blender 原生平移 |
| Alt + 右键拖动 | `view.dolly` | Blender 原生 zoom；投影和相机语义与 Maya dolly 不完全相同 |
| 4 | `view.wireframe` | Blender Wireframe 显示 |
| 5 | `view.shaded` | Blender Solid 显示；材质和灯光模式未映射 |

全部标记为 `adapted`，不是完全等价实现。组件选择使用 Blender 的选择转换规则；
多对象 Edit Mode 使用 Blender 自身的网格编辑规则。F8–F11 不处理 NURBS、绑定或
不可编辑链接对象。变换工具由原生 operator 执行，采用原有撤销逻辑。

键位依据：[Autodesk Maya 2026 官方快捷键表](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-KeyboardShortcuts/files/GUID-30CACC9D-8FBE-4B85-8A8F-C5ADF32DDD4E.htm)。
组件和聚焦绑定另与本机 Maya 2026 默认配置核对；未复制其脚本或个人设置。

## 保留但尚未实现

建模键位中的裸按 Space、D、X、C、V、J、F12、1/2/3 暂不绑定操作：分别为后续
热盒/四视图、临时枢轴、吸附、UV 选择与平滑预览预留。Ctrl/Shift 等组合、其他
未列入命令表的键仍可能沿用 Industry Compatible；例如 F1–F5 的标准视图切换。
不要把这些继承键位视为 Maya 一一对照完成。

## 团队、个人和会话覆盖

优先级：公共基线 → studio.json → user.json → 会话覆盖。
Blender 适配器在独立模块内，不改变公共基线含义。每个 JSON 文件仅记录差异。
路径显示在该 Keymap 预设的偏好面板。当前便携构建通常为
`portable/config/axismeld/user.json`；目录不存在时可自行创建。

示例仅说明格式，并非 Tachikoma 的实际个人修改：把移动改为 T，并停用旋转快捷键。

```json
{
  "schema_version": 1,
  "bindings": {
    "transform.move": {"type": "T"},
    "transform.rotate": null
  }
}
```

每项是完整事件替换；省略的 ctrl/shift/alt/oskey 默认为 false，value 默认为 PRESS。
schema 1 不接受释放、按住、通配修饰键，也不执行 Python 或自定义 operator 字符串。
保存文件后，在该预设偏好中点 **Reload AxisMeld Profiles**。冲突、未知命令、重复
JSON 字段、错误 schema 或坏文件会显示诊断；问题文件保持原样。
与 Window/Screen/Frames 全局命令相撞的覆盖也会被拒绝，例如将 Move 改为 Ctrl+Q。
插件冲突仅报告，不自动修改插件键位。

关闭 **Use Studio and User Profile Files** 可忽略文件覆盖，恢复公共预设。
Blender 原生 Keymap 面板中的个人编辑仍由 Blender 管理，需要用其 Restore 按钮恢复。
没有个人覆盖文件时就是公开默认键位。

Python 调试/后续热盒可以用 `bpy.ops.axismeld.command(command="transform.move")`
调用相同命令，必须提供正确的 3D View 上下文。`axismeld.runtime.load(session=...)`
接受相同 schema 的会话覆盖，不写入文件；下次普通 reload 会移除该会话覆盖。

## 验证范围

覆盖配置层合并、冲突/损坏回退、原文件保护、独立编辑器 keymap 保持、安装预设
发现、operator 注册、组件切换、重复工具选择、上下文拒绝、重载和切回原预设。
后台 operator 测试不等于实际键鼠事件端到端验收。Alt 拖动手感、热盒保持逻辑和
启动画面的人工验收仍需交互测试。启用 Emulate 3 Button Mouse 会占用 Alt+左键，
预设显示提示；使用三键鼠标时应关闭该 Blender 选项。
