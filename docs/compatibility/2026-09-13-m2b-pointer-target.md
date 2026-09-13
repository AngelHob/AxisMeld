# M2b 鼠标目标组件热盒验收

状态：已实现、更新原测试安装，人工待测；前一交付基线4d05fb4d60a。仅本地交付。

## 行为

Object模式无修饰鼠标组件入口优先捕获按下点的可选可编辑Mesh。划向有效动作并释放后才更改目标：未选网格使用替换选择，已选网格保留原生多对象选择集合并激活目标。中心、Esc、失焦、修饰键取消及不可执行占位不改变选择或模式。

空白处沿用M2a活动网格；非网格命中保留原生右键。Edit、键盘改绑与Space目录继续当前选择上下文。目标在提交前失效时取消，不改为另一个对象执行。

本片不包含Shift/Ctrl建模热盒、完整空白上下文、UV、Global缩放或所有Maya选择偏好。

X-Ray下采用最近可选目标，不循环选择、不启用骨骼优先；普通原生选择API默认行为不变。集合/Geometry Nodes实例只可能解析到原生Base/拥有者，本片不声明支持单独实例编辑目标。

## 人工测试

[集中清单](2026-09-13-manual-test-ledger.md)：新增P-01至P-13，沿用原27项，共40项全部待测。C-06/C-07的目标预期已更新，历史原文仍保留在2026-09-12清单。自动测试不替代人工通过。

## 自动化证据

主任务独立57项Python单元测试和5个原生CTest目标通过（含47项布局测试），日志为D:/source/AxisMeld-build/m2b-main-python.log与m2b-main-native.log。

安装态components已通过：未选目标提交、取消保留原选择/活动/Recent、已选目标多选、无active命中、提交前不可选、真实删除目标、Edit不跨对象、填充Curve遮挡原生回退、F13仍使用原活动对象及原有生命周期。日志为m2b-installed-components.log。

| 其余安装态回归 | 最终结果与日志（同build目录） |
|---|---|
| QWER tools | 通过工具入口、原生子菜单/返回、Alt/失焦、区域resize、单/四视图及改键；m2b-installed-tools.log |
| Space hotbox | 通过视图、保存重开、配置页等；m2b-installed-hotbox.log |
| release | 通过派发/异常/取消、子操作拥有、Recent仅成功记录等；m2b-installed-release.log，仅同窗口范围 |

最终四组GUI均退出0且有PASS，无Python traceback；既有PNG ICC警告与release负向夹具的预期诊断保留。独立源码复审已通过。未宣称完整Blender CTest全部通过；旧install路径的历史测试限制不在本批改造范围。

审查补齐了Mesh数据override预检，与原生editmode_enter_ex拒绝条件一致；本构建Mesh.override_create返回None，未能构造有效动态fixture，已删除无效测试，不计为自动化通过。该项仅完成源码防御核对，人工P-13仍待测。

已目视检查pointer-before-commit.png：菜单位于未选Cube上，Outliner中Cube.001仍活动选中，说明打开热盒尚未换目标；图中Cube.001实体位于视口外。实体手感、四视图边缘、真实DPI、X-Ray细节仍待人工测试。

## 安装与回退

入口继续为D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe。
本批前备份D:/source/AxisMeld-build/m2b-20260913-before含exe、modules/axismeld与startup操作器；原exe SHA256为3D9C8BC0D8D2F95473160B295CC7E2F61255DE9041B28B2BB85FA37C14F2461A。个人配置清单为m2b-install-before.json，位于同build目录。

最终exe SHA256：3FCEBEBD3C141B01F9A0D091E37DE1DF0D97CCE15B2E7A6F3B3A0CB66BCBFEDF。安装、候选与编译产物一致；12个Python资源与源码一致；6份portable个人文件前后哈希不变，见m2b-install-verification.json。更新前确认没有运行中的Blender，未终止用户进程。

回退须退出Blender后同时恢复exe及Python：备份axismeld目录内容复制回5.3/scripts/modules/axismeld，axismeld_operator.py复制回5.3/scripts/startup/bl_operators/axismeld.py。portable个人配置不参与回退。
