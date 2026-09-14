# M2d Object 与预选工具入口验收记录

本片继续 M2d-P02/P04，接通 Object 选择和鼠标预选上的三个原生持久工具。人工测试继续暂缓；完整 M2d、对象级几何动作和 UV 不在本片完成声明内。

## 已实现行为

- Shift+RMB 的 Object 根保留 Maya 方向：E Poly Build（Append 适配）、SW Loop Cut、W Knife（Multi-Cut 适配）。其余五向保留具体缺口，NW 仍为 Sculpt，不替换成 Circle Select。
- 已有选择优先，完全无选择才 GPU 预选；前景可选非网格不穿透。直接手势固定对象/data/active/完整选择身份，开盒与取消不修改模式、选择或几何。
- 有效方向确认后，专用操作器一次提交预选、进入 Edit 并激活工具。开启 Global Undo 时一次撤销启动；后续笔划独立撤销。失败恢复组件标志、对象选择及两个模式已有工具槽，不写 Recent。
- 多个独立 Mesh 保留多对象编辑；共享 Mesh data 只让原生代表进入 Edit，其余实例继续共享并保持选择。没有已有工具槽时，失败允许初始化到原生 select_box；Blender RNA 无删除槽接口。
- CREATE/MODEL 两个配置 ID 独立改绑/禁用。MODEL 覆盖 Object/Mesh；直接绑定三工具命令仅作用于 Object，重绑与禁用清除旧生成项，不夺取 Mesh/3D View 原生输入。
- Space Select 目录/自定义中心的 Object 根使用提交时有效选择，不预选鼠标对象；直接 MODEL 手势与此常规目录语义明确区分。

## 开发验证

| 项目 | 证据 |
|---|---|
| 原缺失 RED | 旧候选 SHA8A810D，真实选中 Object + Shift+RMB 后 modal=[]，在导入新模块前失败 |
| Python | 110项纯测试通过，覆盖固定目录、完整目标资格、回滚/回滚报错、缺席工具槽、作用域和绑定迁移 |
| Native | Release构建成功；editor_hotbox_hotbox_model 与四组 AxisMeld CTest 共五组通过，包含实际JSON parser三命令准入/非法命令拒绝及双向目录allowlist |
| Object 实际GUI | 三工具已选/预选启动和单Undo、真实Knife/Loop Cut/Poly Build笔划、失败回滚与无多余Undo、multi/shared、目标失效、选择优先、前景阻挡、实际锁定/隐藏/局部视图、重绑/禁用/反向keymap顺序及Space当前选择提交 |
| 真实几何 | 单/四视图截图均测得Object第2/4行95、第3行127逻辑像素，与同实例Views一致；这是当前字体实测，不是所有字体/DPI固定数值 |
| 配置 | 保存的Maya键位经原生初始化后，Object Mode有MODEL与CREATE，Mesh仅MODEL；候选原portable/config内容保持 |

最终各套件通过标志、测试时二进制哈希及资源一致性，以 `D:/source/AxisMeld-build/object-tools-install-verification.json` 为准。日志统一使用该目录 `object-tools-*` 前缀；旧试验和失败日志保留供复核。


最终回归六套全部通过：Object建模、Edit组件建模、空白创建、组件RMB、QWER工具和M3建模。独立复核未发现剩余阻断问题；110项Python、五组native、配置迁移与已保存配置启动也通过。构建核验同时确认28个安装资源与源码一致、4个候选配置不变、31个回滚文件完整、原M3实例8个抽查文件不变。

## 修复与测试界限

第一次实际GUI发现 JSON parser 白名单漏了三个新命令，导致整份snapshot被拒绝。已增加精确准入与真正调用parse_menu_snapshot的正负测试；菜单布局fixture与parser准入是两层检查，不能互相替代。

Blender锁定/隐藏对象后会原生清空不可选base的选择。测试先观察稳定后的真实选择状态；完全无选择且无可拾取目标时CREATE可打开，不把这个行为误报为Object工具接受了锁定选择。已打开的固定目标会在资格变化后取消。

组件热盒旧回归曾要求全部修饰键加RMB走原生处理，与本批已授权的Object Shift+RMB入口冲突。测试现在分别验证Shift+RMB只开一个建模热盒且中心取消不改变上下文，以及Alt/Ctrl/OSKey加RMB继续原生回退；保留失败日志，不通过改生产路由满足旧断言。

单视图下窄行像素扫描曾把禁用标签文字两侧的背景分割成小段，误报第4行107而非95。对同一保存截图独立扫描确认真实边缘未变；测量改为覆盖整行背景高度，保留连续宽高过滤与3像素容差。没有改生产布局或放宽间距判定。

界面自动化在隔离工厂场景和临时配置下运行；真实手感、常用复杂模型与125/150/200%DPI仍等待人工记录，不算已通过。VR前批同DPI Sidebar手柄拖动仍待人工。

## 构建与人工清单

本批入口：`D:/source/AxisMeld-build/m2d-ui-test-install/blender.exe`。

二进制 SHA-256：`8568A5126E57EED5EC62B64BDA1DD27B6E36D7E6D5E08DC819334B961D3FC5AC`。原M3运行实例保持；上一份M2d程序/资源/config共31文件另存 `rollback-before-object-tools` 并逐一核验。

统一清单本批新增 **O-01至O-16，16项**，合计 **147项 / 47项用户确认已测试 / 100项待测**。原47行反馈逐字保留，自动化未把人工项改成通过。

下一步：整物体Fill Holes、锐边与Extrude适配、无选择Edit组件预选；随后Ctrl+RMB转换与Ctrl+Shift+RMB工具菜单，再补QWER/M3具体缺口和UV。Global物体缩放无开发计划。
