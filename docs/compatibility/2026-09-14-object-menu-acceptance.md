# Object 建模组合菜单验收记录

用户截图指出旧版 Shift+RMB 只有少量径向入口，缺少 Maya 的下方普通菜单。本批恢复同会话组合结构，接通已有可验证能力；完整 Object 建模及 M2d 仍有缺口。人工测试继续暂缓。

## 实现范围

八向保留 Maya 方向和名称，下方恢复22主条目、7处分隔、3个普通级联目录及独立 Options。径向与列表分别维护导航路径，共用一个输入会话。实际列表、禁用项、分隔、Options 和级联走廊阻止外延径向穿透，其他空白仍允许方向外划。空间不足时分页/侧放，保持 Views 的径向内缘间距。

下方可用：Offset Edge Loop、Smooth、Mirror、Reduce、Remesh、Combine、四种 Exact Boolean、Quad Draw/Poly Build、当前视口 Backface Culling。四种修改器有独立参数框；打开和取消只读，确认检查原目标/active/完整选择/data 身份，再执行并产生一条 Undo。多选择时四种修改器只作用于活动 Mesh。

灰显内容及 Blender 适配边界详见 `../maya-mapping/2026-09-14-object-modeling-composition.md`。特别是上方八向仍只有三个已有工具适配，上方 Options 与 Soften/Harden 级联尚未补齐。不能把下方目录恢复称为 Maya 全功能还原。

## 检查中的修正与证据

- 旧安装 SHA `8568A5126E57` 的真实 Shift+RMB 截图没有下方列表，独立事件测试在导入新模块前失败。证据 `object-menu-old-red.log` 与对应截图。
- 新 native parser/Options/组合布局测试先记录 RED，再实现。旧默认树测试暴露 Space 入口避让时误移动 depth0 主菜单；修复为仅平移次级几何，并对480×320和1920×1080四角/中心、实际主行/Options/级联逐页进行正命中验证。
- 独立 Python 复核发现原生 QuadriFlow 参数窗口在确认时重新读取 active，无法满足固定原目标契约。新 Retopologize 主项与 Options 已禁用并保留明确缺口，旧 Space Mesh 入口维持原语义。独立复核确认修复。
- 快照仍限制256KiB。只压缩精确列举的重复上下文拒绝短语，不截断未知错误或独有缺口说明。默认240330字节；测试23种已知拒绝原因、10条按实际字节贡献选出的 Recent 和全部已表示指示状态，最坏261388字节，余756字节。后续扩展须重新验证预算。
- GUI观察器使用实际截图与独立字体模板定位，而非生产布局公式。校准中修正跨分隔线的相同标签页、前置 checkbox 和窄子菜单的识别假设；保留失败截图，不将识别器问题误报为生产修复。
- 既有 Space 菜单回归曾在1x原始 WINDOW 左下角失败；新旧两个安装都复现同一失败，截图均未打开 Views 次级环。来源是旧测试把被工具栏覆盖的原始窗口边缘当作可交互内容角，而已存在的 visible safe bounds 正确拒绝该按下点。修正测试在各比例下测量真实 WINDOW 内容边界，不改生产间距或角落方向预期；保留 `object-menu-menus-visible-boundary-red.log`、`object-menu-menus-old-comparison.log` 与截图。

## 验证状态

119项纯 Python 测试、5组 native CTest、隔离 profile 迁移、复制的保存配置启动及会话 Maya 启动脚本通过。最终9套真实GUI通过：新增 Object组合菜单、已有Object工具、Edit组件建模、空白创建、组件RMB、QWER工具、M3建模、Space菜单和同窗口释放。释放验证限同窗口，不声称覆盖本批未重跑的跨窗口套件。

新增组合套件验证22行顺序/分页/7处分隔、3级联、四种修改器实际结果与一步Undo、选中及预选Options只读/取消/确认/身份失效、四种Exact Boolean目标与体积/Undo、Combine、Offset工具启动、Quad Draw实际笔划及分开的笔划/启动Undo、禁用与各种取消、外划及F13重绑。单/四视图实际内缘为95 / 127 / 95逻辑像素，与同实例Views一致；四个小视口角也验证列表可见和真实按下点取消。该数值仅指当前测试字体与设置，Windows DPI和手感仍待人工确认。

Space回归在1/1.25/1.5/2倍UI比例下使用原边界或最多相邻1像素的实际WINDOW receipt，原方向及一次执行断言未放宽；2x实际TOOLS内部点严格收到TOOLS，Space无热盒执行。小视口534×375与不支持尺寸的取消也通过。既有Object套件验证Space自定义中心Object入口及提交时当前选择；本批未另外增加Select目录组合专用GUI，不将此路径单独称为实测通过。

日志位于 `D:/source/AxisMeld-build/object-menu-*-green.log`，新套件原始 `object-menu-gui-r6.log` 保留。实际正常主题截图为 `object-menu-normal-theme.png`，经独立查看，不是设计稿或调色合成。Python与native独立源码复核的阻断项已关闭。

## 构建与人工记录

新候选为 `D:/source/AxisMeld-build/m2d-object-menu-test-install/blender.exe`。原 `m2d-ui-test-install` 和 `phase2b-ui-test-install` 保留；当前旧 M2d 窗口仍有未保存场景，不更新其程序或配置。新候选复制旧 portable/config；真实加载保存的 AxisMeld Maya 2026 后，Object Mode 有 MODEL/CREATE，Mesh 有 MODEL。交付的独立启动入口也会在本次新窗口启用 Maya 键位并关闭偏好自动保存，不改旧配置。

程序SHA-256：`51B833EBCB4E22C7B6C94C22086E9A0EE7DD4F838D941F68D49E0C0A5B48FFCD`。28个安装Python资源与源码逐一一致；两个旧安装的61个基线文件保持一致；新候选四个配置文件与来源核对一致。`object-menu-install-verification.json` 记录程序、资源、native源码、日志、源提交与人工状态。程序由已验证工作树构建后和文档提交，内嵌build-info可能显示父提交。

统一人工清单追加 OM-01～OM-16，共163项：用户已测试47项、待测116项。47项只代表用户说已测试，未逐项确认通过/失败。当前自动验证不改变这些状态。
