# 热盒与菜单统一图标验收

## 实现

Space主热盒、Views、QWER及子环、组件、创建、建模环、普通菜单和级联，所有非分隔条目都分配Blender内置语义图标。真实目录1403节点中1388条功能/目录/设置/灰显条目使用110种内置图标；通用工具类回退50条（3.6%）。本批不增加图片或JSON字段，原256KiB快照上限不变，也不把灰显功能变成已实现。

编辑器层解析器按稳定command、目录/缺口ID及设置value分类，不依赖翻译后的文字。相同命令在不同入口与Recent保持一致。参数格、返回和翻页保留单一结构图标。语义图标占20逻辑像素，radio/checkbox另占20；有状态行的普通目录整体预留状态列，未显示页和无状态兄弟也保持对齐。列表子菜单右箭头及24像素Options格独立保留。

测量和显示同时修复原来的三处图标抑制：direction_label清空图标、native_menu只显示状态图标、submenu强制ICON_NONE。Views精简标签也计算图标；Views中心已有图标只计一次。没有修改命令分发、输入生命周期或纯布局的间距算法。独立复核发现depth0自定义文字颜色在图标绘制后才应用，已改为先确定最终颜色，再让图标和文字共用该颜色。

## 证据

- 旧候选SHA `51B833EBCB4E` 上实际Object Shift+RMB打开一个热盒；截图中Multi-Cut完整文字匹配0.866、左图标像素0，获得真实GUI RED。证据 `hotbox-icons-old-red.log`。
- 原生测试先以空resolver运行RED；随后对File/Edit、orientation、extrude与Maya CamelCase固定ID补RED并修正分类。最终4项测试覆盖真实目录、内置枚举边界、语义代表值、别名/Recent、翻译及启用状态无关性。
- 121项Python（含新增两个图标前缀观察器边界用例）与6组原生CTest通过；保存配置加载及只影响新会话的Maya启动脚本通过。日志 `D:/source/AxisMeld-build/hotbox-icons-*-green.log`。
- 新增icons实际GUI套件最终r8通过（73.953秒）：1×/2×主热盒七项、完整Views/QWER/Axis子环、组件/创建/Object、普通及级联、radio与语义双列、checkbox与无状态兄弟对齐、禁用透明度、独立Options只读弹窗。截图用独立BLF完整文字匹配及其左侧实际图标像素观察，不读取生产图标字段。
- 实际Views内缘比较保留：单视图1×/2×各方向环、1×四视图Object以及1×/2×四视图Views/W通过。2×下960×462像素的小四视口（逻辑480×231）无法容纳Object主环与最低分页列表；旧 `51B833EBCB4E` 和新候选实测均无modal handler。保留既有unsupported行为，验证无场景突变并且释放后下一次Views仍可打开，不压缩间距。对照日志 `hotbox-icons-quad-{old,new}-probe.log`。
- 观察器校准保留r1～r7失败证据：区分独立图标与文字、灰显像素、参数框灰背景和普通列表边界。Controls Rows本来没有checkbox状态，按既有原生测试验证语义图标；真正checkbox用Backface Culling验证。未因此新增生产状态或放宽完整文字要求。
- 正常主题实际截图 `hotbox-icons-normal-object.png`、`hotbox-icons-normal-state.png` 和 `hotbox-icons-normal-space.png`，已逐张查看；来源为隔离实例的实际界面，非设计稿。
- Edit Face旧间距观察器仅扫描13像素文字带，被新16像素图标切断按钮背景，误报上排间距111。相同失败截图改看完整24像素按钮背景后，右上真实内缘恢复为1007，实际间距为95/127/95，与同图Views一致；保持原颜色、连续背景、最小跨度和3像素比较门槛，只修正扫描范围，未改生产布局。原始失败保留 `hotbox-icons-context-modeling-regression-r1.log`。
- 最终11套GUI通过：icons、components、create、context-modeling、object-modeling、object-menu、tools、menus、native-style、release、modeling。context-modeling修正观察器后r2完整通过；其他旧套件回归均r1通过。native-style额外验证1×/2×正常/悬停及实际点击前后的完整radio ON/OFF状态；Object-menu回归承担完整参数事务、几何结果与撤销验证，新增icons套件本身只验证图标、两槽可见和参数窗口入口。release仅同窗口，不扩称本批未重跑的跨窗口验收。
- 旧输入与观察器fixture同步新的显示契约：每功能20像素语义槽、独立状态槽，Views回调明确只测文字以免重复计宽；Object菜单仅在真实前缀空白边界尝试零/一/两图标槽，保留完整BLF模板、宽差和评分。native-style圆心按实际截图从左缘14改为约11，保留所有选中状态断言。

## 候选与人工测试

新候选 `D:/source/AxisMeld-build/hotbox-icons-test-install/blender.exe`，程序SHA-256 `C2B75B7D1999F81EF5B11A8614342725D887C0441E6FF1F030C654FC521B88D8`。三个旧安装保持不变；构建和自动测试使用独立实例，未向原窗口发出保存或关闭指令。新候选从前批Object-menu安装复制portable/config。

28个安装Python资源与源码一致，新候选4个配置文件与来源一致；三个旧安装的96个基线文件逐一保持原哈希。`D:/source/AxisMeld-build/hotbox-icons-install-verification.json`记录程序、native源码、资源、截图、通过日志和源提交。程序从验证后的工作树构建并与文档一起本地提交，内嵌build-info可能显示父提交。

2026-09-14，按用户要求将开发进度推送至 `https://github.com/AngelHob/AxisMeld` 的 `axismeld/phase-2a` 分支。已验证的代码提交为 `54cc28a06bb3e2590c98e8663b9c394d2a3807d3`，包含此前可见边界、Edit上下文、Object工具事务及组合菜单的提交。本次发布附带清单总述修正；未改代码或程序，测试结果沿用上述构建验收。

统一人工清单追加IC-01～IC-14，共177项：用户已测试47项、待测130项。47项保持用户原始“已测试”状态，不推定逐项通过；自动验证不替代人工结果。人工测试继续暂缓。
