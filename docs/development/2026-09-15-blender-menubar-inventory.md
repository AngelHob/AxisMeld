# Blender 顶部菜单保留清单与 Maya 归属建议

日期：2026-09-15。范围：当前源码只读审计，不操作 GUI、场景、文件保存或外部链接。以下是菜单入口及其 draw 条件核验，不等于每个 operator 的实机成功验证。Maya 归属以本库 Maya 2026 参考树为依据；新增用途子目录是明确的 Blender 适配，不冒充 Maya 原有命令。

## 结论

可重排顶层菜单，但不能只将 Maya 热盒静态 command 表搬到 TOPBAR：原生菜单包含文件选择器调用上下文、保存参数、动态附加组件入口、RNA 状态以及开发/平台/构建条件。建议保留原生菜单类与注册 ID，通过用途目录复用其 draw，叶级搬移必须保留完整参数和上下文。不要把全部 Blender 功能塞入一个 Extensions。

当前顶部是 Blender 图标 / File / Edit / Render / Window / Help（space_topbar.py:106–125）；Workspace 标签及 Back to Previous 属于 Header 其它部分，不应随菜单替换删除（:22–41、:680–707）。

## 保留清单

下表源码路径均相对仓库根目录。

| 当前入口与证据 | 必须保留的能力 / 可靠入口 | 建议 Maya 归属与边界 |
|---|---|---|
| `scripts/startup/bl_ui/space_topbar.py:157–216` File | New / Open / Recent / Revert / Recover；`wm.read_homefile`、`wm.open_mainfile`、原生 Recent 菜单、`wm.revert_mainfile` | File > New Scene / Open Scene / Recent Files；Recover、Revert 留 File 的恢复用途组，不用静态 Maya recent 示例替代真实最近文件 |
| 同文件 :219–298 | New 的 General / 动态 app templates / More；Last Session、Auto Save | File > New Scene 的模板子目录；File > Recover。保留 `wm.read_homefile.app_template` 与模板动态枚举；不能只保留一个空白场景 |
| :171–186 | Save、Save As、Save Copy、Save Incremental | File 对应 Save Scene / Save Scene As / Increment and Save；Save Copy 保留单独命名。已保存 Save 用 EXEC_AREA，未保存用 INVOKE_AREA；前三种需 `show_save_modified_images_dialog=True`；Copy 需 `copy=True`；Increment 需 `incremental=True`，仅 is_saved 可用 |
| :190–203 | `wm.link`、`wm.append`；项目菜单；原生 Import / Export | File > References 下明确区分 Link .blend 与 Append .blend；Append 是本地副本，不能标成仍保持外部引用。Import/Export 可挂原有菜单作为格式目录，不假设全格式统一 operator |
| :338–350 | `project.new_project`、`project.open_blend_in_project`、`screen.project_setup_show` | File > Project；保留 Blender Project 命名，不把 project_setup 等同于 Maya Set Project 路径操作 |
| :381–438 | 构建条件启用的 Alembic、USD、SVG Grease Pencil、OBJ、PLY、STL、FBX import；collection export；SVG/PDF Grease Pencil export | File > Import / Export，继续引用 `TOPBAR_MT_file_import/export`。collection_export_all 仅 view_layer.has_export_collections 可用；GP 导出另依赖 pugixml / haru；不根据参考 JSON 固化当前机器可见格式 |
| :441–471 | 自动打包、Pack/Unpack All、Pack/Unpack Libraries、相对/绝对路径、Report/Find Missing Files | File > External Data（资源管理用途）。Archive Scene 不能未经证明等同 Pack All：打包与创建归档文件不同。保留 autopack 实际状态，以及自动打包启用时 Pack/Unpack All 的 inactive 条件 |
| :146–154、:474–486 | Purge/Manage Unused Data；生成/批量生成/清理/批量清理数据预览 | File > Optimize / Data Management：清理与管理保持单独入口，不能将 Maya Optimize Scene Size 静默绑定成任意 purge 默认动作。Data Previews 留该资源用途组 |
| :301–335 | Save Startup File、加载工厂设置、模板专属 factory startup | Windows > Settings/Preferences > Startup & Defaults；继续 INVOKE_AREA 与模板参数。Save Startup File 不等于 Save Preferences，不能共用错误标签 |
| :533–574 | Undo、Redo、Undo History；Adjust Last Operation、Repeat Last、Repeat History；Menu Search、开发 Operator Search；Rename Active、Batch Rename；Lock Object Modes；Preferences | Undo/Redo/Repeat/History 归 Edit；Rename 归 Modify > Naming（保留 Blender 原生命名语义）；Search 可 Edit > Search；Lock Object Modes 归 Windows > Settings/Preferences > Interaction；Preferences 使用 `screen.userpref_show`，归 Maya 原 Settings/Preferences。Rename panel 保留 name=TOPBAR_PT_name、keep_open=False；不替换成不同语义的 Maya BatchRename |
| :489–530 | Render Image / Animation、条件 Sequencer Image / Animation、Audio mixdown、View Render / Animation、Lock Interface | 保留用途清晰的 Render 顶层（Maya Rendering 菜单集的渲染用途）；如固定 Modeling 菜单集必须提供 Windows > Rendering Editors/Render 的可发现入口，不能因当前22树无 Render 就删除。保留 use_viewport、animation、use_sequencer_scene；Audio 留 Render > Audio；View Render/Animation 可 File > View 镜像入口；Lock Interface 必须实际 RNA `scene.render.use_lock_interface` |
| :577–619 | New Window、New Main Window、Fullscreen、Next/Previous Workspace、Status Bar、全窗/Editor Screenshot、Windows Console、Stereo 3D | Windows > Workspaces / UI Elements / Window Management；Console 可对应 Output Window 的 Blender 控制台入口。New Window 与 New Main Window 不合并；Screenshot Editor 必须 INVOKE_SCREEN；console 仅 win 平台；stereo 仅 use_multiview；workspace_cycle 保留 NEXT/PREV |
| :622–651 | Manual、Support、Communities、Get Involved、Release Notes、开发文档/社区/API/Cheat Sheet、Report Bug、Save System Info | Help，Blender 与 Maya 文档按真实产品分组。保留 url_open_preset 类型 MANUAL/RELEASE_NOTES/API/BUG，不把链接换成 Maya 帮助；开发项保留 show_developer_ui 条件。审计没有打开任何网址 |
| :128–143、:354–371 | Splash / About；Install Application Template；Reload Scripts、Memory Statistics、Debug Menu、Redraw Timer enum、Unused Editor Data / Operator Presets cleanup | Splash/About 归 Help；Install Template 归 Windows > Settings/Preferences > Templates；脚本重载归 Windows > Development；诊断/计时/系统信息归 Help > Diagnostics；保留 enum 展开，不能只绑定无参数 redraw_timer |
| :654–677、:680–707 | File context menu；Workspace Duplicate/Delete/Reorder/Cycle/Delete Others | 保留原类注册和独立右键入口；顶部菜单改造不应破坏这些调用。workspace 管理留 Windows > Workspaces，不能只剩 Next/Previous |

## 动态和上下文丢失风险

1. **高：Import/Export append 扩展丢失。** `scripts/addons_core/io_scene_gltf2/__init__.py:2289–2290`、`io_scene_fbx/__init__.py:733–734`、`io_anim_bvh/__init__.py:390–391`、`io_curve_svg/__init__.py:100` 向原 `TOPBAR_MT_file_import/export` 追加。只复制 space_topbar.py 中静态 draw 会漏 glTF、BVH、插件 FBX export、曲线 SVG 与第三方扩展。保留这些类的 ID、注册和正常 layout.menu 调用，是最稳妥兼容边界。`bl_owner_use_filter=False` 也须保留。
2. **高：保存入口参数或调用方式退化。** 上表 Save/Copy/Increment 不是只靠 operator id 即等价；混用 EXEC/INVOKE 会绕过或丢失文件选择器，漏 modified-images 参数会改变原生保存流程。
3. **高：用统一 VIEW_3D 覆盖 TOPBAR。** 文件/偏好/窗口可由全局菜单原生调用，但 Render 的 sequencer_scene / strips、Rename 的活动数据依赖来源上下文。顶部不是某个固定3D视窗，不应套热盒捕获目标、Edit-mode adapter 或 pointer selection commit。已有原生 poll 应决定当前可用性。
4. **高：动态 Recent / Undo History 被静态替代。** `source/blender/editors/space_topbar/space_topbar.cc:219` 注册 File Recent，`:275` 注册 Undo History；`source/blender/editors/undo/ed_undo.cc:998` 与菜单搜索也按该 ID 调用。它们必须继续读当前 runtime，不能使用 Maya capture 中的文件/历史文字或热盒 Recent actions 冒充。
5. **中：状态项伪装普通命令或静态复选框。** Autopack、Lock Object Modes、Lock Interface、Status Bar 必须继续读写原生 RNA/数据状态；禁用条件和平台/构建条件必须跟随当前上下文。
6. **中：Blender 图标消失连带唯一诊断入口消失。** System 源码注释明确这些操作否则无用户入口 (:353)。移除图标前按用途迁入 Help/Windows，而不是直接删 class。

## 建议实现与验证边界

优先只重排 TOPBAR_MT_editor_menus 的用途菜单，复用动态原生子菜单；需要对齐 Maya 主项时用小型专用 draw 函数保留原生 props/context。保留 Help 与可发现 Render 路径，不把22个 Modeling hotbox 菜单当成跨所有 Maya 菜单集的完整顶部全集。

验证应包括：未保存/已保存的 Save、Save Copy 不改变主文件身份、Increment；Link/Append 入口分别存在；附加组件开关前后 Import/Export 更新；真实 Recent/Undo；Preferences 可打开；3D和Sequencer来源 Render 差异；新窗口/工作区/全屏/Editor Screenshot 上下文；RNA 状态双向反映；Help/诊断入口；原 File/Workspace 右键仍可用。此文仅盘点，以上实机验证尚未运行。
