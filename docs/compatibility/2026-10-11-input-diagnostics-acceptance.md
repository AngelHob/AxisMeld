# 输入冲突提示：人工验收 IN-01～IN-03

需要包含 **2026-10-11 输入诊断修复** 的开发构建。当前公开的 2026.09.17 Skin preview 不含此修复；本批没有发布新的试用包。此处的测试保持待测，不用旧包结果替代新源码验收。

用隔离配置和临时空白文件，选择 AxisMeld Maya 2026 预设。下面的临时测试项只调用 Blender 搜索菜单，不修改对象；不要保存偏好。在 Text Editor 运行准备代码，然后打开 Edit → Preferences → Keymap，点击 Reload AxisMeld Profiles 查看诊断。

```python
import bpy

axm_test_kc = bpy.context.window_manager.keyconfigs.addon
assert axm_test_kc is not None, 'Use a separate GUI test instance'
axm_test_items = []

def axm_add(map_name, key, **modifiers):
    space = 'VIEW_3D' if map_name == '3D View' else 'EMPTY'
    km = axm_test_kc.keymaps.new(map_name, space_type=space, region_type='WINDOW')
    item = km.keymap_items.new('wm.search_menu', key, 'PRESS', **modifiers)
    axm_test_items.append((km, item))

axm_add('Object Mode', 'F9', ctrl=True)
axm_add('Mesh', 'P')
axm_add('3D View', 'F10', ctrl=True)
```

1. **IN-01**：重载后，Object Mode/Ctrl+F9 不报告与 Mesh 的 `selection.convert_vert` 冲突，Mesh/P 不报告与 Object 的 `edit.parent` 冲突。3D View/Ctrl+F10 应保留 `selection.convert_edge` 潜在重叠提示。测试项仍启用，type/modifiers 未被更改。
2. **IN-02**：在同一 Text Editor 末尾追加并运行 `axm_add('Mesh', 'F9', ctrl=True)` 和 `axm_add('Object Mode', 'P')`，只运行这两行，避免重复执行准备部分。再次重载，新增两条对应模式冲突提示，共三条相关提示；原有不同模式的两项仍不误报。此步骤也核对原生共享视图没有因过滤规则而漏报。
3. **IN-03**：仅运行下方清理，再重载。三条测试提示消失；原有插件和键位仍保持。退出隔离实例，正常配置不受影响。

```python
for km, item in axm_test_items:
    km.keymap_items.remove(item)
axm_test_items.clear()
```

脚本可能留下空的测试 keymap 容器，随隔离进程结束销毁；不删除可能共用的原生/插件容器。本批自动验证使用独立进程中的真实 RNA keymap 对象，仅证明诊断与静态生成结果，不宣称实际 GUI 提示已经人工验收。
