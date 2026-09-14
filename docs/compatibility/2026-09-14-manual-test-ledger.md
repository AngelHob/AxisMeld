# AxisMeld 待人工测试清单

更新：2026-09-14。人工测试继续暂缓。S/P/C/V/T/R 共47项保持已测试（用户确认，未逐项报告通过/失败）；原 G/K/L/M3/VR/D/O/OM 共116项仍待测。前轮 IC-01至IC-14 热盒与菜单统一图标14项保留。本轮追加 MC-01至MC-14 Maya组合菜单对齐14项。本轮再追加 HC-01至HC-20 全热盒菜单内容核对20项。历史191项及其47项已测试状态不变；现合计211项：已测试47项，待测164项。自动化不覆盖历史人工结果，也不将待测项自动改为通过。

## 测试准备与反馈

本文件保存测试目录、操作预期和历史初始状态；私人测试网页的服务端记录保存此后每次人工勾选、结果、备注与版本。网页是后续个人测试进度的记录入口，不能用此文件中的初始状态覆盖网页记录。追加或更新目录只更新条目说明，保留已有编号及用户已保存的进度。“已测试”与“通过/失败”分别记录，历史已测试条目不补造结果。

本轮 HC 使用独立候选 `D:/source/AxisMeld-build/maya-content-test-install/blender.exe`；构建与验证记录见 `2026-09-14-maya-content-acceptance.md`。本轮主要对齐内容，不改变既有触发、方向和四视图布局标杆。

前轮 MC 候选已构建到 `D:/source/AxisMeld-build/maya-companion-test-install/blender.exe`，程序哈希前12位 `9E84E857BB414`；安装及回归证据见 `2026-09-14-maya-companion-acceptance.md`。先保存原场景，再使用临时 Cube 场景，选择 AxisMeld Maya 2026 键位。前轮图标候选为 `D:/source/AxisMeld-build/hotbox-icons-test-install/blender.exe`；其安装证据见 `2026-09-14-hotbox-icons-acceptance.md`，程序哈希前12位 `C2B75B7D1999`；历史批次哈希不代表当前安装。

前批OM组合菜单的构建与资源核验见 `2026-09-14-object-menu-acceptance.md`，程序哈希前12位 `51B833EBCB4E`。前批Object工具入口证据见 `2026-09-14-object-tools-acceptance.md`；VR/D前批证据保留在 `2026-09-14-visible-region-m2d-acceptance.md`。旧M3安装及当前运行的旧M2d窗口保留，不用旧入口验证本轮新功能。开始测试前核对主入口，避免混入另一个旧安装。破坏性编辑、Cut、转换、绑定与颜色测试只在临时场景进行，每组先保存一个可还原副本。四种新修改器可从右侧参数入口调整；其他原生参数使用 **Space → Edit → Adjust Last Operation**，修改器也可在原生Modifier属性中继续调整；**F9仍是Vertex入口**。Vertex Paint入口只切换到Blender原生绘制模式，不代表本批实现了完整Maya绘制工具链。

先跑优先级 P0，再跑 P1。反馈格式：`编号 / 通过或失败 / Object或Edit / 单或四视图 / 实际结果`。涉及误触时补充鼠标路线与释放顺序；涉及显示时补充 Windows 缩放比例和视口大小。通过与失败均保留日期、版本；未反馈不推定通过。

## P0：热盒划选与重复唤出（上一批仍待测）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| G-01 | QWER与四视图二级热盒对照，单/四视图查看 | 以四视图Views热盒实际横向留白为标杆，第2/4行和第3行左右按钮内缘间距分别对齐；不缩小Views迁就其他菜单，不只凭“未重叠”判定；标签完整、方向不变 | 待测 |
| G-02 | W/E/R经过World/Object按钮后继续水平向外滑出很远，再松LMB | 对应方向仍高亮且提交，不要求停在按钮上；远处不跳相邻行 | 待测 |
| G-03 | Q选择工具与组件RMB环，在未被伴随列表覆盖的按钮外延释放；划向禁用方向或缺席的NW；组件S方向另从Face主按钮提交 | 未遮挡有效外延提交正确命令；列表和分隔线优先命中，不穿透执行S方向；禁用/空方向不误选相邻项，组件取消不改变目标 | 待测 |
| G-04 | 进入Axis/Custom Axis/Select子环继续外划，再回当前中心后重新划选 | 外延按当前子环计算；只返回一层，隐藏父环不夺取选择 | 待测 |
| G-05 | 从Space→Modify→Tool Settings打开工具热盒，外划释放或回最初LMB点 | 与QWER外延一致；返回真实按下点取消，不误执行 | 待测 |
| G-06 | 分别持续按住Q/W/E/R，反复按住/松开LMB至少三次，在不同鼠标位置唤出 | 每次都在新的位置开环；松LMB隐藏本次热盒，持键可继续，无需重新按QWER | 待测 |
| G-07 | 同次QWER持键先空中心松LMB，再禁用项松LMB，再选择有效项 | 前两次取消后仍可重新唤出，有效项正确提交，无残留高亮/子菜单 | 待测 |
| G-08 | 第二次开环后分别先松QWER、Esc、切应用、W切E并交换释放顺序 | 不提交取消中的动作，无粘键；新工具及重新进入窗口后正常 | 待测 |
| G-09 | Edit中Q Clear Selection后仍持Q再次LMB切Lasso，松Q后撤销；个人改键也重复 | 选择撤销仍一条原生步骤；键位映射与多次唤出一致 | 待测 |
| G-10 | 四角/窄视口与125/150/200%DPI，进入原生列表/单选设置后滑出列表 | 夹紧中心可取消；列表外不虚选列表项，radio与分页/返回不变 | 待测 |

## P0：空白创建热盒（本批新增12项）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| K-01 | Object无选择，鼠标位于空白；按住Shift并按住RMB，中心松RMB，反复重开 | 立即显示Polygon Primitives八向环及下方16项Maya伴随列表；保留全部占位和3条6逻辑像素分隔；每次中心释放关闭，不改变场景 | 待测 |
| K-02 | 将3D Cursor移到可辨位置，分别创建NE Disc、E Sphere、SE Torus、S Cube、SW Cone、W Cylinder、NW Plane；每次先清空选择并移到空白 | 每次只创建一个对应网格、选中新物体、位于Cursor；Disc有填充面；不移动Cursor，默认尺寸/细分沿用Blender | 待测 |
| K-03 | 对K-02七种创建分别只撤销一次，再重做一次 | 一次撤销完整移除本次新物体并恢复原场景；重做仅恢复一个，无额外热盒撤销步骤 | 待测 |
| K-04 | 经过七个有效方向按钮后，在未被伴随菜单遮挡的外延区域松RMB；S Cube另在主按钮释放，再向下进入列表及连接间隔释放 | 未遮挡外延保持对应方向；Cube主按钮创建一次；新增列表优先命中列表项、连接间隔取消，不穿透菜单继续执行Cube或误选邻项 | 待测 |
| K-05 | 在中心释放、出中心再回划、划到N Create Polygon Tool后释放 | 三种情况均不创建、不写Recent、不增加撤销；N明确灰显占位；随后可正常重开 | 待测 |
| K-06 | 开环后先松Shift、加按Ctrl或Alt、Esc、切应用、切模式/窗口；交换Shift/RMB释放顺序再重试 | 变化中的手势取消；不误创建、不留残余鼠标/热键拦截；恢复条件后新手势可用 | 待测 |
| K-07 | 已选择网格/非网格、Edit Mode、空选择但鼠标指向可选物体；各用Shift+RMB | 不显示空白创建菜单、不偷偷选中鼠标下对象；合格Object选择/鼠标预选转入O项工具根。Edit单一点/边/面且已有有效选择转入D项建模热盒，空选/混合域仍原生回退 | 待测 |
| K-08 | Object已有选中对象时Space→Create→Polygon Primitives创建；Edit中再查看该入口 | Object可创建且一次撤销恢复原有对象和选择；Edit下创建项不可执行 | 待测 |
| K-09 | 临时配置改绑创建热盒至键盘或Ctrl/Shift组合，再禁用，重新加载配置 | 新绑定仅在无选择Object开启；禁用/改绑CREATE后，未由MODEL接管的上下文保留原生行为，MODEL在Object/Mesh的配置独立；Alt/OSKey非法配置被拒绝，普通组件RMB限制不变 | 待测 |
| K-10 | 单/四视图、视口四角/较窄区域、125/150/200%DPI重试K-01/K-04/K-05 | 标签可读，菜单夹紧后真实按下点仍可取消，命中与显示一致；本轮Tool Header避让另见VR项 | 待测 |
| K-11 | 分别关闭/开启Blender“新建后进入编辑模式”偏好，创建Cube和Torus并一次撤销 | 默认关闭均Object；开启后Cube仍Object、Torus遵循原生进入Edit Mesh；一次撤销移除新物体，偏好本身不变 | 待测 |
| K-12 | 创建成功后检查Space→Recent并在Object重放；再在Edit查看同项；取消创建后重新检查 | 成功命令可在Object再次创建且一次撤销；Edit不可执行；取消不加入成功历史，个人配置不被改写 | 待测 |

## P0：单选菜单组

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| S-01 | Space → Hotbox Controls → Transparency | 左侧空心/实心圆，右侧百分比纵向对齐；当前透明度那一项选中，默认25%透明对应75%不透明 | 已测试（用户确认） |
| S-02 | 悬停未选项，再选择不同透明度；重复选择同一项并重开 | 悬停不变圆点；实际设置改变后只有当前值选中；重复幂等 | 已测试（用户确认） |
| S-03 | 在临时配置中填写非法透明度37并重载，再打开Transparency | 现有校验拒绝非法值，保持有效设置及对应圆圈；不声称支持非预设透明度 | 已测试（用户确认） |
| S-04 | 从Controls和Views两个入口打开Hotbox Style，依次改显示方式再重开 | 两个入口显示同一真实选中项，切换生效，取消不改状态 | 已测试（用户确认） |
| S-05 | 分别修改左/中/右Center Mouse Buttons映射，含Disabled与目录后页选项 | 三组状态独立；每组当前选项显示圆点；长label与圆圈不相互遮挡 | 已测试（用户确认） |
| S-06 | 重载个人配置或重启预览程序，确认外观/改键 | 单选状态跟随真实配置，未创建另一套状态；原有配置与其他输入不被重置 | 已测试（用户确认） |
| S-07 | 窄视口、四视图、125/150/200%DPI查看三类列表；再测Rows和QWER普通项 | 圆圈和文字对齐，分页/返回/释放正常；Rows和普通命令不误变单选 | 已测试（用户确认） |

## P0：鼠标下网格目标（M2b）

准备两个分开的临时网格 A、B 和一台 Camera。实体鼠标先对准目标再按右键；目标在**按下时**确定，划向菜单项时不随鼠标换到别的对象。Object 模式才启用拾取，Edit 与键盘改绑仍使用当前编辑/选择上下文。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| P-01 | A选中，B未选；在B上右键拖上/左/下并释放，分别重做 | 提交时以B为活动目标进入边/点/面；不编辑A | 已测试（用户确认） |
| P-02 | 无活动/选中对象，在B上右键划选 | 可直接进入B组件模式；无需先左键选中 | 已测试（用户确认） |
| P-03 | A选中，在B上打开；中心释放、Esc、拉回起点释放分别重做 | A的选择和活动状态完全不变；B不被选中，不切模式 | 已测试（用户确认） |
| P-04 | A选中，在B上打开后划向UV/Vertex Face/Multi Component释放 | 占位不执行，目标和模式不变，无额外Recent/撤销 | 已测试（用户确认） |
| P-05 | A选中，在B上打开后切应用；另试中途Ctrl后松右键 | 取消不更换目标，回来可重开，无残留释放监听 | 已测试（用户确认） |
| P-06 | A、B同时选中且A活动；在B上提交，再选A/B之外的C提交 | 已选目标保留原生多对象集合并改变活动目标；未选C使用替换选择，不把A/B一起带入Edit | 已测试（用户确认） |
| P-07 | A选中，在B上右键向右上Object Mode释放；重复一次 | B成为当前目标且保持Object，不误进Edit；重复不切回 | 已测试（用户确认） |
| P-08 | A选中时在空白处打开；无选择时在空白处右键；在Camera形状上右键 | 空白有有效活动网格沿用其上下文；无有效目标或命中非网格保留原生右键 | 已测试（用户确认） |
| P-09 | 两网格前后重叠；再将前物体隐藏/设不可选，测试实心、线框、X-Ray | 拾取遵循本批记录的原生视口选择过滤，不选择隐藏或不可选对象；记录各显示模式的遮挡差异 | 已测试（用户确认） |
| P-10 | 打开后通过另一区域删除目标或将其不可选，再尝试提交 | 取消或不执行，不能退回A执行，不能崩溃 | 已测试（用户确认） |
| P-11 | Edit A时鼠标对准B；将入口临时改绑键盘后Object A活动且鼠标对B | Edit和键盘入口继续当前上下文，不跨对象换目标 | 已测试（用户确认） |
| P-12 | 四视图、视口四角、125/150/200% DPI重复P-01/P-03；细小目标边缘慢划和快速划 | 起点目标稳定，显示与命中一致，取消保留选择，实体手感无误触 | 已测试（用户确认） |
| P-13 | 用临时链接资产分别测试不可编辑对象、Object override、Mesh数据override | 不作为本片可进入Edit的鼠标目标；拒绝前不更改选择或模式，仍可走原生右键 | 已测试（用户确认） |

## P0：组件右键共同回归

模式切换沿用 Blender 原生选择集合语义。Object鼠标入口使用本批P项规则；空白处、Edit、键盘改绑和Space目录继续当前有效上下文。以下47项中已确认行保留历史测试表述；本轮Edit已选组件Shift+RMB覆盖D项，Ctrl组合热盒仍后续开发。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| C-01 | Object 下选 Cube；按住右键，向上/左/下拖动后松右键，分别重做 | 进入边/点/面 Edit 选择模式；一次手势仅提交一次 | 已测试（用户确认） |
| C-02 | 分别从点、边、面 Edit 按住右键拖向右上 Object Mode；已在 Object 再做一次 | 回 Object；已在 Object 保持 Object，不意外进入 Edit | 已测试（用户确认） |
| C-03 | 原地按下并松右键；拖出再回按下点释放 | 中心取消，模型与选择模式不变，无残留菜单 | 已测试（用户确认） |
| C-04 | 打开后按 Esc，再释放右键；再打开并切到另一应用后回来 | 取消，重新右键能打开，后续左键选择和中键操作正常 | 已测试（用户确认） |
| C-05 | 向右 UV、左下 Vertex Face、右下 Multi Component 释放 | 占位不可执行，不改模式/模型，不产生 Recent 或额外撤销 | 已测试（用户确认） |
| C-06 | Cube 活动时分别在其表面、空白处、另一个未选网格上打开 | 前两种沿用Cube；第三种只有提交有效动作才切到鼠标下网格；取消不换目标 | 已测试（用户确认） |
| C-07 | 无有效目标的空白处、Camera/Light形状、Sculpt、其他编辑器分别右键 | 原生右键仍可使用；Object鼠标命中有效未选网格的例外见P-02 | 已测试（用户确认） |
| C-08 | 有活动 Cube 时 Alt/Ctrl/Shift + 右键；另试已打开热盒后按 Ctrl 并松右键，随后无修饰右键 | 修饰键原有导航/操作不被抢占；中途修饰取消不残留已释放键，普通右键仍能打开组件热盒 | 已测试（用户确认） |
| C-09 | 快速连续两次右键划选；右键尚未释放时切换工具键；完成后左键选择 | 不重复提交、无粘键或释放监听残留 | 已测试（用户确认） |
| C-10 | 临时改绑到键盘上可用的无修饰空闲键，或禁用组件入口，重载后检查原右键，再恢复配置 | 新绑定按下打开、松该键提交；禁用/改绑不吞原生右键、不残留旧入口；个人其他配置不变；带修饰键的配置会明确拒绝 | 已测试（用户确认） |
| C-11 | Space → Select → Active Mesh Components 切点/边/面/Object；另从 Space → Modify → Tool Settings 打开工具环 | 与右键/QWER入口共用命令；沿用 Space 释放规则，执行后不残留鼠标监听 | 已测试（用户确认） |
| C-12 | 同时选两个可编辑网格，指定活动对象；用组件热盒进/出 Edit | 沿用 Blender 原生多对象编辑语义，不偷偷取消其他对象选择；切模式本身不改变几何 | 已测试（用户确认） |

## P0：上一批修复与工具热盒

以下以 2026-09-12 布局为准：QWER 按内容定宽；径向工具子环切换遵循当前实现，不使用早期“所有父环常驻/全部等宽”的历史验收文字。

| 编号 | 操作 | 预期 | 人工状态 |
|---|---|---|---|
| V-01 | Space 视图热盒，从左上 Left View 向左拉出按钮后释放 | 保持 Left View，不误选中左 Top View | 已测试（用户确认） |
| V-02 | 对 Back/Bottom 重复外侧划动；从中心做短划和原地释放 | 外侧延续对应行/列；安全区取消，无邻项误触 | 已测试（用户确认） |
| V-03 | 在视口四角、单视图/四视图、窄视口重复；隐藏 Camera 时划向右上空方向 | 菜单移入后仍按实际路线命中；空方向不替代执行 Left 或其他视角 | 已测试（用户确认） |
| T-01 | 点按 Q/W/E/R；再仅长按，不按鼠标 | 立即选工具，单纯长按不弹热盒 | 已测试（用户确认） |
| T-02 | 保持工具键，按住左键打开，拖向目标先松左键 | QWER 五行布局、文字和箭头不拥挤；单次正确提交 | 已测试（用户确认） |
| T-03 | 进入 Axis/Select 子环或设置目录，返回父级后选另一项 | 返回可预测，父子不同时抢命中，普通目录贴边且文字完整 | 已测试（用户确认） |
| T-04 | 分别先松左键、先松工具键、Esc、切应用；左边缘原地释放及返回起点释放 | 正确提交或取消；无意外动作或粘住状态 | 已测试（用户确认） |
| T-05 | W 未松时按 E；依次交换 W/E 释放顺序；长按产生键盘重复 | 新工具入口可用，旧键释放不取消新会话，不重复打开 | 已测试（用户确认） |
| T-06 | W/E/R 分别设不同 Global/Local/Normal；切换工具后直接拖轴和点轴后空白中键拖 | 各工具保留方向，两种拖法一致；不把已有缩放差异当成本批修复 | 已测试（用户确认） |
| T-07 | Q 切换 Marquee/Lasso/Paint，再松 Q；Object/Edit 执行 Clear Selection 并撤销 | 工具不被复位；Clear 只处理当前集合，一次撤销恢复；Paint 是 Blender 圆形选择适配 | 已测试（用户确认） |

## P1：环境与共同回归

| 编号 | 操作 | 预期 | 人工状态 |
|---|---|---|---|
| R-01 | 100%、125%、150%、200% 缩放下，单/四视图重复 C-01、V-01、T-03 | 标签可读、命中与显示一致、边缘不误选；记录实际系统缩放而非仅模拟倍率 | 已测试（用户确认） |
| R-02 | Space 点按切单/四视图，长按打开；移动到标准正交视图后 Alt 导航 | 点按/长按保持原规则；正交旋转锁定和导航仍正确 | 已测试（用户确认） |
| R-03 | UV Editor、文本输入、Sculpt 下使用 QWER/右键 | 建模入口不抢输入、不提前改变 UV 工作流 | 已测试（用户确认） |
| R-04 | 保留个人改键、底色、不透明度、文字颜色后重启 | 外观和绑定保留；重置外观不重置操作配置 | 已测试（用户确认） |
| R-05 | 两个 Blender 窗口间切换，弹窗打开时尝试热盒；返回后重试 | 不穿透弹窗、不留跨窗口按键监听；本项须实体窗口测试 | 已测试（用户确认） |

## P0：四视图标杆布局回归（本轮新增6项，全部待人工验证）

对照依据：[四视图热盒布局标杆与回归约束](../development/2026-09-14-hotbox-reference-contract.md)。这里的“标杆”是Views按钮之间的真实可见净距；文字长度可以不同，不要求所有按钮等宽。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| L-01 | 同一窗口与缩放下，依次打开Views、Q/W/E/R主环；截取或目视比较第2/4行和第3行左右内缘 | 两类横向净距分别与Views对应行一致；Views本身不被压窄，文字与箭头不挤入留白 | 待测 |
| L-02 | 在临时Cube上打开组件RMB，再到空白无选择处打开Shift+RMB创建环，与Views比较；只在中心取消 | 组件与创建环采用同一横距标杆；五行方向不变，取消不换选择或创建物体 | 待测 |
| L-03 | W/E/R进入Axis与Custom Axis子环，Q进入选择子环，再从Space→Modify→Tool Settings进入相同子环 | 深层环不退回旧窄间距；短长标签均完整，父级不可见部分不抢子环命中 | 待测 |
| L-04 | 单视口将鼠标移入第2/4行左右内缘之间的新留白，分别原地松键、回起点释放；再向对应按钮外侧远划释放 | 内侧留白不因旧命中范围误触邻项；有效外划仍保持正确方向，回真实起点取消 | 待测 |
| L-05 | 在四视图各分区和视口四角打开Views、W与创建环；重复有效外划、缺席/禁用方向、回中心 | 夹紧后的显示与命中一致，缺席方向不借邻项执行；当前中心返回层级正确 | 待测 |
| L-06 | 分别在125/150/200%系统缩放和较窄视口重做L-01/L-04；同时查看长标签原生列表 | 相同缩放下横距仍按Views对齐，标签/箭头/圆圈不重叠；列表与径向命中分离；记录实际宽度，极窄Tool Header已知问题单独记录 | 待测 |

## P0/P1：M3建模菜单与快捷键（本轮新增34项，全部待人工验证）

默认从Space目录寻找表中原生名称；部分项位于下一页或子组。菜单中的“适配”需按其差异说明验收，例如曲线采样精度不是保形重建、Mesh Deform不是Maya的Proximity Wrap算法。灰显计划项以本批覆盖记录的唯一计划编号为准，不执行占位命令。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| M3-01 | Object临时场景按住Space，依次进入Select、Modify、Edit、Create、Display、Mesh、Edit Mesh、Mesh Tools、Mesh Display、Curves、Surfaces、Deform；浏览子组与后页 | 12组均有可读目录和实际项；标签不显示资源键；各项按当前模式启用或灰显，返回不串组 | 待测 |
| M3-02 | 空场景、仅Empty、Mesh Object、Mesh Edit空选择分别检查Mesh/Deform/组件编辑项；尝试点击灰显项 | 无有效对象/域/目标的项不可执行，不创建空修改器、不报脚本异常；有效Create入口仍可用 | 待测 |
| M3-03 | Select：准备两个Mesh和一条Curve，依次使用All、None、Invert及按类型选择；再在Mesh Edit重复全选/反选 | 对象与组件命令处理各自域；按类型不误选其他类型，非选择对象不被编辑；操作可按原生规则撤销 | 待测 |
| M3-04 | Select：在带规则四边面的网格选一圈边，测试相邻扩展/收缩、Loop/Ring以及点边面转换；从Convert Selection→Multi-Component及F7同时启用三域；在两个独立Edit对象各选一个点再看Connect/Merge | 选择结果符合菜单所写原生拓扑规则；菜单与F7均启用Blender点/边/面组合，不假装独立Vertex Face域；不足的独立选区不跨对象累加为有效连接/合并输入 | 待测 |
| M3-05 | Modify：Cube移动、旋转、非均匀缩放后测试Apply、Reset、Origin to Geometry与Origin to Cursor，每次撤销；Ctrl+T激活Universal工具；在Object Relationships→Replace with Active Object Data中明确活动源A和同类型目标B/C，再试混合类型 | Apply/Reset/Origin符合原生规则，Ctrl+T激活原生组合变换工具；Replace将B/C链接到A的数据块，保留各自对象变换和原有modifier；一次Undo恢复原数据关系，混合类型灰显；不声称独立Maya双枢轴或Global缩放已解决 | 待测 |
| M3-06 | Edit/Modify：两个已变换对象Group、Ungroup、Match；另以静态单条开口/闭合Curve为活动源，从Object Relationships→Place Along Active Curve分布无父级、约束、动画及delta位移的对象，源加旋转/非均匀缩放后重试；再试父子循环、零长度Curve与受驱动目标，每个有效动作单Undo/Redo | 层级/匹配方向清楚；路径目标按名称顺序取得固定参数位置，闭合首尾不重合；新增Follow Path指向活动Curve，基础位置归零并保留缩放，参数间距不承诺等弧长；不支持的输入灰显，一次Undo恢复本次约束、变换和Curve路径设置 | 待测 |
| M3-07 | Edit：临时对象Duplicate与Duplicate Linked、Copy/Paste与Cut/Paste，分别Undo；再从Object Relationships→Copy Active Scalar Custom Properties将活动源的数值/字符串/布尔复制到两个目标，含已有同名scalar与缺失键；加入同名数组/字典目标后重试 | 普通/共享副本及Cut复制成功后删除符合说明；属性只从活动源复制到目标，源数组不复制；目标同名非scalar或override使整批灰显，不留下半复制；一次Undo恢复旧值并移除本次新增键 | 待测 |
| M3-08 | Edit→Adjust Last Operation修改参数，Mesh Object按F9，并检查Undo/Redo不可用状态；G重复上一原生动作；另在Delete by Type依次测试Bake Selected Mesh History、Bake All Mesh History及对应Non-Deformer项，每次单Undo/Redo；使用两个对象、拓扑modifier在deformer前的栈、共享Mesh实例、shape key及动画/driver/NLA/override对象作对照 | 参数生效且F9仍为Vertex入口；G沿用原生Repeat Last，不新增冲突绑定，不等于Recent；History实际烘焙拓扑，Non-Deformer保留原对象和剩余deformer栈，All范围含当前Scene未选对象；一次Undo恢复整批几何/栈/数据关系；共享Mesh、shape key、动画/driver/NLA/override、待应用Collision、禁用或不合法交错栈不执行，不静默拆开共享数据 | 待测 |
| M3-09 | Create：在可辨位置放3D Cursor，分别创建新增网格原语、Bezier/NURBS曲线和Surface原语；每次Undo一次 | 每次只创建一个对应数据类型的对象，位置与说明一致；一次Undo完整移除，不修改创建偏好 | 待测 |
| M3-10 | Create：选对象创建Collection，再添加其Collection Instance；打开Reference Image选择器后取消；激活Measure并量一段距离 | 集合与实例关系真实存在；文件选择取消不留空对象；Measure使用原生工具，不声称创建Maya测量节点 | 待测 |
| M3-11 | Display：选择部分对象使用Hide/Show及Hide/Show by Type；对同一明确Show或Hide命令执行两次，再在Outliner或原生显示设置核对；Mesh Edit隐藏部分组件后按Ctrl+Alt+H | 固定Show/Hide重复幂等，不是每次反转；仅命令指定的对象/类型改变；Ctrl+Alt+H恢复原生隐藏组件，不切换选择域或全局对象显示状态 | 待测 |
| M3-12 | Display/Modify设置：分别改变X-Ray、Wire/Solid、选择/变换相关可选设置；悬停另一项但不提交，然后从原生UI改回并重开菜单 | radio/checkbox跟随真实状态，悬停不等于选中；多个独立组互不覆盖，原生UI与热盒显示一致 | 待测 |
| M3-13 | Mesh：两个相交Cube明确活动A，分别Union、A−B、B−A、Intersection，每次观察修改器目标/几何后Undo一次；再只选一个或加入非网格目标 | 实际布尔结果与方向正确，操作数保留策略符合说明；一次Undo还原；无合法操作数时灰显，不添加无目标修改器 | 待测 |
| M3-14 | Mesh：两网格Combine，再Edit Separate Loose Parts；在临时细分网格执行Triangulate、Quadrangulate、Reduce/Subdivision与Remesh代表项 | 对象数量/拓扑确实变化；Undo可还原；Remesh遵循原生数据损失提示与输入限制，不把仅增加modifier当结果 | 待测 |
| M3-15 | Edit Mesh：选面用菜单与Ctrl+E各启动一次Extrude；第一轮移动后确认并Undo一次，第二轮移动后Esc取消 | 菜单释放不误确认子操作；确认产生正确挤出且一次Undo恢复；取消按原生宏语义处理，不记成成功Recent | 待测 |
| M3-16 | Edit Mesh：选边用菜单与Ctrl+B启动Bevel，调整宽度并确认/取消；随后测试Bridge两圈边与Merge有序顶点 | 边域与目标数量不足时不可用；Bevel参数/确认归原生操作；Bridge连接正确环，Merge First/Last遵循有效历史 | 待测 |
| M3-17 | Edit Mesh：选面Duplicate Faces和Extract Faces，再试Split、Dissolve和Delete Edge Loop；另在点/边/面域分别按Ctrl+Backspace与Ctrl+Delete，每次单Undo | 重复、分离和删除产生各自不同结果，未选区域不被误删；两快捷键沿用Blender按当前域Dissolve语义，本批Maya DeletePolyElements只提供边域近似，不冒充其顶点删除/面删除与边界选择路由；一次Undo恢复本次拓扑 | 待测 |
| M3-18 | Mesh Tools：通过目录激活Knife、Loop Cut、Poly Build，再在视口实际切割/添面；也试Ctrl+Shift+X与Ctrl+Shift+Q | 切换的是已注册原生工具，后续实际操作可用；工具选择不提前写几何成功Recent；Poly Build差异保持可见，不宣称完整Quad Draw | 待测 |
| M3-19 | Mesh Tools：启动Immediate Knife/Loop Cut/Edge Slide，移动鼠标后Esc或确认；将有边界投影对象配合编辑中的目标面执行Knife Project | 开菜单的释放不误完成modal；取消无额外热盒Undo；投影按当前视图切割，缺投影轮廓/目标时灰显 | 待测 |
| M3-20 | Mesh Display：临时封闭网格先Reverse再Recalculate Outside；选部分边Mark/Clear Sharp并切平滑显示，查看法线overlay | 法线方向/锐边确实改变对应数据；未选区域符合原生命令范围；不将sharp标记当作持久锁定所有custom normals | 待测 |
| M3-21 | Mesh Display：Create Color Attribute，分别POINT与CORNER设不同颜色；Edit仅选部分顶点/面Set Color，空选及CORNER只选边再查看可用性 | 只改变对应选中域；空域操作灰显；Rename/Convert/Remove作用于明确活动属性，Undo还原；Display Active Colors反映真实颜色 | 待测 |
| M3-22 | Vertex Paint入口：在临时Mesh使用菜单提供的原生Vertex Paint跳转，画一笔后Undo，再退出到Object/Edit | 进入正确原生模式，笔划归原生工具并可撤销；旧Mesh/Curve热盒不强行抢绘制输入；完整Maya Paint流程不作为本批已实现项 | 待测 |
| M3-23 | Curves：创建Bezier，Edit选择部分控制点，执行Subdivide、Smooth、Reverse、Handle Auto/Vector/Free；清空控制点选择再查看菜单 | 真实Curve控制点改变，Bezier句柄行为与标签一致；空选编辑项灰显，Handle项不在无Bezier点的NURBS上假启用 | 待测 |
| M3-24 | Curves：在原生属性将闭合曲线设2D后试Geometry Offset，再试Round Bevel/Resolution；激活Curve Pen实际加点/编辑后取消一次 | Offset与Bevel改变输出几何，Resolution只改采样；不冒充保形Rebuild或独立Offset曲线；Pen后续事件归原生工具 | 待测 |
| M3-25 | Surfaces：创建NURBS Surface Curve，Edit选完整控制行执行Spin Selected NURBS Row；另在曲面选控制行测试Extrude、Subdivide、Cyclic U/V与Reverse | 实际生成/改变SURFACE控制网格；Spin只在合法行可用，方向和参数符合说明；不切Mesh伪造NURBS结果 | 待测 |
| M3-26 | Surfaces：Object选一条路径Curve和一个Curve截面，活动对象为路径，执行Sweep Selected Curve Profile；撤销后只选路径再查看入口 | profile目标真实配置，输出为原生Curve扫掠几何且一次Undo恢复；缺截面灰显；明确不是完整Maya NURBS Extrude patch | 待测 |
| M3-27 | Deform：临时细分网格试Bend/Twist/Taper/Stretch、Static Wave、Texture Displace与Smooth，调参并Undo；再从Edit→Delete by Type依次执行Delete All Hook Modifiers、Delete All Lattice Modifiers、Delete All Nonlinear Modifiers、Delete All Curve Deform Modifiers，准备当前Scene已选/未选对象及另一Scene独立对象，每项单Undo/Redo | 默认形变可见，参数与新增数据可撤销；四项仅删除当前Scene匹配族（Hook、Lattice、Simple Deform/Wave、Curve），保留其他modifier、顶点组和控制器/笼/曲线对象，另一Scene独立对象不变；动画/driver/NLA或override目标使整批不可用；一次Undo恢复整批栈顺序及Hook目标/点索引/逆矩阵，不留下部分删除 | 待测 |
| M3-28 | Deform：对带父级非均匀缩放且自身旋转的网格Create Enclosing Lattice，编辑笼点，再回Lattice Edit执行Reset；分别Undo | 初始笼正确包围源，默认形变和后续笼点改变可见；父级变换不致笼偏移；创建一次Undo连同笼/数据移除，Reset仅恢复格点 | 待测 |
| M3-29 | Deform：活动源网格配选目标，分别Shrinkwrap、Curve Deform、Surface Deform bind与封闭笼Mesh Deform bind；绑定后移动目标顶点，再Unbind/Rebind；最后缺目标/错误类型重试 | 每种目标明确、绑定状态真实、求值随目标变化；不修改原目标来假造成功；无目标/开口笼等非法输入灰显或拒绝且不留新修改器 | 待测 |
| M3-30 | Deform：两个同索引拓扑且形状不同Mesh，活动源执行Selected Targets to Shape Keys；另在Edit选少量点Hook；分别单Undo | Shape Key实际改变源并保留目标，拓扑不匹配不可用；Hook控制器只驱动所选点；一次Undo还原key/basis或hook/empty全套 | 待测 |
| M3-31 | 成功执行可重复的非modal命令后查看Recent并重放；对modal启动后取消、参数窗取消、灰显计划释放分别检查Recent；切不支持模式再看旧Recent项 | 仅可重放成功动作进入历史；启动/取消/计划不记成功；历史项按当前上下文灰显，重放保留单Undo语义 | 待测 |
| M3-32 | 两个Blender窗口或单/四视图之间切换，保持Space进深层列表后先松Space、Esc、切应用；紧接着按QWER和普通RMB重试 | 新目录不遗留鼠标/修饰键所有权；已支持的QWER/RMB流程保持；Curve/Surface新增Space范围不等于扩展旧网格工具手势 | 待测 |
| M3-33 | 窄视口/四视图/125–200%DPI打开M3长列表，翻页、返回、悬停最下项与移出列表；在设置项重复改变值 | 长标签、radio和分页互不遮挡；原生菜单当前不显示快捷键文本，快捷键另按M3-15/16/18实际按键验证；移出不虚选列表项，翻页后命令/状态对应正确；Tool Header避让按VR项回归 | 待测 |
| M3-34 | 备份个人配置；临时改一个M3快捷键、保留原QWER/底色/透明度，重载并重启；浏览M3灰显计划、UV及M2后续占位 | 改键生效且无旧绑定残留，其他配置不被覆盖；计划显示明确理由/编号且不执行；UV与独立M2后续不因本批菜单接入被误标完成 | 待测 |

## P0：可见区域与原地取消恢复（本轮新增8项，人工暂缓）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| VR-01 | 窄视口保留Tool Header，打开Controls长列表并翻页/返回，悬停上下禁用箭头 | 标签、radio、导航与命中均位于工具横条下方，不出现画面移走但旧位置仍可点的情况 | 待测 |
| VR-02 | 在VR-01禁用箭头上保持鼠标不动，分别先松Space、Esc及交换拥有鼠标释放顺序，再直接按W/E/R | 取消不改变设置、不遗留modal；同一点能切Move/Rotate/Scale，随后可重新开热盒 | 待测 |
| VR-03 | 分别保留左工具栏、右侧栏及二者同时可见，在四角打开方向热盒和原生长列表 | 菜单避开真实输入区域，标签可读；工具栏显隐与宽度不被热盒擅自改变 | 待测 |
| VR-04 | 热盒开启后切换Tool Header/左工具栏/右侧栏显隐，并调整侧栏宽度 | 可用区域改变后旧热盒取消并清除画面，不提交旧选项；补齐释放后普通操作正常 | 待测 |
| VR-05 | 开启动画，在侧栏显隐动画过程中反复打开热盒，再等动画结束 | 按完整输入区域避让，动画结束可用空间改变时旧会话取消；不落到尚会接收输入的透明/滑动区域 | 待测 |
| VR-06 | 四视图保留Tool Header与侧栏，在四个分窗分别测试VR-01/02/03；125/150/200%DPI重试 | 只依据与当前分窗相交的障碍避让，下方分窗不被上方不相交横条额外裁短，显示与命中一致 | 待测 |
| VR-07 | 四角打开Views、QWER、普通组件RMB与创建环，向按钮外延划选，再回真实按下点 | Views标杆净距不缩；外延、缺席方向、中心取消及父子返回保持原有语义 | 待测 |
| VR-08 | 将视口缩到不足以完整容纳热盒，再恢复大小 | 不显示残缺按钮或缩窄净距，不留下热盒输入拦截；恢复后可正常重开 | 待测 |

## P0：M2d 已选组件建模热盒（本轮新增14项，人工暂缓）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| D-01 | Edit Mesh分别只启用点/边/面域并选择组件，Shift+RMB开环 | 分别显示Vertex/Edge/Face建模环，按显式选择域选择根；面选择向顶点flush不误开Vertex环；打开不改模式和选区 | 待测 |
| D-02 | 适当选区分别执行Smooth Vertices、Poke Faces、Spin CW/CCW、Collapse与Dissolve Edges，每次单Undo | 实际顶点/面/边关系按标签改变，Undo恢复几何与选择；不足条件灰显，Dissolve不冒充Maya附带顶点清理 | 待测 |
| D-03 | 点域/边域分别从E启动Bevel，移动鼠标、调整参数并确认；另一次Esc | 开环释放不提前确认倒角，参数交互归原生操作；确认后一次Undo恢复，取消沿用原生规则 | 待测 |
| D-04 | 边域S Extrude Edges、面域S Extrude Region，移动后确认并单Undo；另一次Esc，再与Ctrl+E对照 | 正确域几何挤出，拥有鼠标释放不误确认子操作；菜单与既有命令一致，不新增重复快捷键或Undo步骤 | 待测 |
| D-05 | 面域选择同一Mesh相邻/分离面执行N Merge at Center，再以两个Mesh不同位置重复并单Undo | 每个Mesh所选顶点各合并到一个中心；按Blender规则清空组件选择并保留Face域，不自动改点域；Undo恢复原几何/域/选择 | 待测 |
| D-06 | 点/面Normals与边Sharpness子环切换真实法线/锐边显示，执行Reverse、Recalculate、Mark/Clear Sharp等适用项 | overlay/数据实际对应；不满足faces等既有条件时灰显，不因新菜单强行启用；不把Sharp标记当Maya完整法线锁定 | 待测 |
| D-07 | W激活Knife后在临时面实际切一刀并确认/撤销；NW激活Circle Select并实际改变选区 | 后续鼠标/确认归原生持久工具，没有热盒抢输入；Circle Select名称诚实，不冒充完整Paint Selection工具 | 待测 |
| D-08 | 尝试Vertex Extrude/Delete Vertex、Face Boundary Bevel/Wedge、Target Weld等计划项 | 显示具体缺失理由/计划，释放不执行近似但语义不同的算法，不改变几何、Recent或Undo | 待测 |
| D-09 | 中心/回真实起点/Esc/失焦取消；交换Shift和RMB释放；松非拥有鼠标；中途加Ctrl/Alt或更换选择域 | 仅拥有鼠标的有效释放提交一次；取消和域变化不执行旧菜单命令，补齐释放后可重开且不残留拦截 | 待测 |
| D-10 | Edit空选择、混合域、非网格模式；Object无选择空白及有选择对象分别Shift+RMB | 不支持的Edit情况沿用原生Cursor回退；Object空白创建独立工作，合格Object选择/预选进入O项工具根；开盒不偷偷改选鼠标目标 | 待测 |
| D-11 | 备份配置，分别改绑/禁用CREATE与MODEL，尝试F13、Ctrl+F13、Shift+MMB；重载两次并检查冲突提示 | 旧Mesh CREATE条目被清除，CREATE/MODEL上下文路由互斥且幂等；两个入口可独立配置，第三AxisMeld命令及global碰撞拒绝；共享keymap冲突诊断与原生fallback保留，Alt/OSKey限制保留 | 待测 |
| D-12 | 单/四视图、四角、125–200%DPI打开三根与所有子环，对照Views第2/4行、第3行左右内缘；远处释放和缺席方向 | 实际横向净距不小于标杆；外延选中、中心/返回取消不误触相邻行，空间不足完整拒绝 | 待测 |
| D-13 | 多对象Edit各保留不同选区，鼠标移到未编辑对象再开环；每Mesh仅1点时查看需要2点的Merge等 | 当前编辑/选择集合优先，鼠标不替换目标；最小数量按每个Mesh判断，不把两对象各1点累加成合法2点 | 待测 |
| D-14 | 执行可重放非modal项后查看Recent；取消、灰显计划、仅激活Knife、挤出启动后取消分别对照，再测试普通RMB/QWER/Space | Recent沿用真实成功/可重放策略，取消不冒充成功；普通入口、QWER持键重复开环与Space释放行为保持 | 待测 |

## P0：M2d Object 与预选工具入口（本轮新增16项，人工暂缓）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| O-01 | Object选中一个网格，Shift+RMB开环，中心释放；鼠标移到另一网格上重复 | 显示Object Modeling；已有选择与active优先，开盒/中心取消不改模式、选择、组件或几何 | 待测 |
| O-02 | Object完全无选择，鼠标指向网格，开环后中心/Esc取消，再确认W | 开盒只读；取消仍无选择；确认W才选中该候选并进入Edit Knife，不穿透前景可选非网格 | 待测 |
| O-03 | 混选Mesh与非Mesh、缺少active、局部视图外仍被选中的对象；另测试锁定/隐藏后开环 | 不静默过滤仍存在的不合格选择；若Blender锁定/隐藏已自动清空选择，按实际无选择状态路由，空白CREATE仍独立工作 | 待测 |
| O-04 | Object选择临时平面，E进入Poly Build，拖边建面/移动顶点，再Undo | 显示Append适配标签；后续由原生Poly Build完成，不冒充完整Maya Append；撤销恢复本笔几何 | 待测 |
| O-05 | Object从W进入Knife，点击两点切割并Enter确认，另一次Esc | 仅在方向确认后进入Edit；后续切割/确认/取消由Knife接管，没有开盒释放提前确认 | 待测 |
| O-06 | Object从SW进入Loop Cut，在可切边环操作并确认/取消 | 激活原生循环切割工具；有效边环实际产生拓扑，原生不支持的拓扑不强行执行 | 待测 |
| O-07 | 开启Global Undo，分别从已选/无选择预选启动三工具后立即单Undo；再做笔划分别Undo | 启动一步恢复Object及原对象选择；笔划与启动分别撤销。关闭Undo时遵循用户偏好，不擅自改设置 | 待测 |
| O-08 | 同时选中两个独立Mesh；另用Alt+D共享数据实例重复，并保留非默认active | 保留选择及active；独立data进入多对象Edit；共享data仅一个代表进入Edit，其他实例仍Object且已选，data不被拆分 | 待测 |
| O-09 | 保留部分组件选择、隐藏组件及不同点/边/面选择域，退出Object再启动工具 | 不为了启动工具将残留组件全选；原生模式进入规则保留，实际笔划仍遵循工具有效目标与隐藏状态 | 待测 |
| O-10 | 划向W后分别Esc、先松Shift、切应用、回起点、增加Ctrl；恢复后重开 | 取消不启动工具，不产生Recent/Undo；释放补齐后无残余输入拦截，可反复唤出 | 待测 |
| O-11 | 开盒后通过外部操作更改选择/active、锁定集合、移除目标或替换其Mesh data，再释放 | 直接MODEL会取消原手势；不转投新目标，不撤回外部修改；恢复条件后新手势可用 | 待测 |
| O-12 | 分别改绑/禁用CREATE和MODEL，测试Shift+RMB、Ctrl+Shift+MMB及键盘映射 | 两个配置独立；MODEL覆盖Object与Mesh，CREATE仅空白Object；第三命令冲突仍拒绝，旧输入保留适用的原生回退 | 待测 |
| O-13 | MODEL改绑键盘，完全无选择时将鼠标停在网格上按键；已有选择时再按 | 键盘入口不做鼠标预选；已有合格选择可打开Object根并提交 | 待测 |
| O-14 | 从Space Select目录或自定义中心按钮进入Object根，提交W；开着目录时更换有效选择再提交 | 目录使用提交时的有效选择，不做鼠标预选；工具可执行且一次Undo恢复提交前模式/选择，不出现启用却无响应的项 | 待测 |
| O-15 | 单/四视图、四角、125/150/200%DPI，将Object根与Views比较并外划释放 | 第2/4行及第3行真实内缘间距对齐Views，标签完整；真实起点可取消，未遮挡外延有效；伴随列表及连接间隔按列表优先或取消处理，对角视觉空白不擅自扩大为取消区 | 待测 |
| O-16 | 尝试N/NE/S/NW占位及SE Soften/Harden目录，再测试普通RMB、QWER持键重复开盒、已有Edit根及Recent | 占位有明确缺失原因且不执行；Object NW仍Sculpt缺口；SE以普通目录呈现，仅已有安全动作可用，其余内容灰显；旧入口可用，单纯激活持久工具不写Recent | 待测 |

## P0/P1：Object 建模组合菜单修正（新增16项）

本批针对用户截图反馈“Shift+RMB与Maya差距较大、没有下方菜单”。原Object工具片的三个入口验证不代表完整Maya菜单还原；本批单独记录组合结构与真实功能，人工测试继续暂缓。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| OM-01 | Object选中Cube，Shift+RMB唤出；与提供的Maya截图对照 | 八向热盒和下方列表同时显示；下方22个主条目按Maya顺序排列，不精简删除缺口；保留7条6逻辑像素分隔、Mapping/Booleans/Polygon Display三个目录；不必另进Space | 待测 |
| OM-02 | 持住RMB在长列表滚轮翻页，再展开三个目录，移回父项和主环 | 条目均可达，分页不执行建模、不关闭父热盒；子菜单按普通列表展开，返回仍看见主环与主列表 | 待测 |
| OM-03 | 分别在Smooth/Mirror/Reduce/Remesh主文字与右侧方框释放RMB | 主按钮执行默认操作，方框独立打开参数；两块命中无重叠，不会打开参数同时执行主按钮 | 待测 |
| OM-04 | 对四种参数框分别点取消或Esc；无选择鼠标预选对象时也重复 | 打开与取消不改变模式、对象选择、活动对象、修改器或几何；不新增撤销步骤 | 待测 |
| OM-05 | 调Smooth层级、Mirror轴/剖切/合并、Reduce比例、Remesh体素大小后确认，再撤销 | 参数真实影响新修改器；只增加一个，确认操作可一步撤销；原有修改器保留 | 待测 |
| OM-06 | 参数框打开期间改变active/完整选择、对象data或目标可见/可选资格后确认 | 不转投新对象；失效时取消，场景维持变化后的用户状态，不创建修改器 | 待测 |
| OM-07 | 多选两个Mesh，交换活动对象后分别执行四种修改器操作 | 与标明的Active Mesh范围一致，只作用于活动Mesh；其余选择及修改器不变，不暗中批量执行 | 待测 |
| OM-08 | 两个独立Mesh执行Combine，再一步撤销；单Mesh时观察Combine | 合并到活动Mesh并保留原生语义；撤销恢复两个对象；目标不足时禁用 | 待测 |
| OM-09 | 两个有重叠体积的Mesh分别执行四种Boolean，交换active并撤销 | Union/A−B/B−A/Intersection目标与菜单说明一致；保留原物体和可见性，新增Exact Boolean修改器；撤销不影响旧修改器 | 待测 |
| OM-10 | 从下方列表启动Offset Edge Loop与Quad Draw，完成原生笔划并撤销 | 分别进入Offset Edge Loop和Poly Build适配；启动及后续笔划的撤销边界明确，不宣称实现完整Maya Quad Draw流程 | 待测 |
| OM-11 | 八向按钮外延长划；经过下方列表的有效/禁用/分隔/Options区域后松RMB | 列表实际区域优先命中或取消，不穿透误触径向；其他空白仍保留原有八向外划，不要求停在按钮上 | 待测 |
| OM-12 | 中心释放、移出再返回、Esc、提前松Shift、切应用；顺序交替重复 | 整会话取消不修改场景、不粘键；下一次Shift+RMB、普通选择和QWER正常 | 待测 |
| OM-13 | 完全无选择，指向可选Mesh开盒，取消或选modifier/工具；再指向前景非Mesh | 开盒不提交预选；已提供预选事务的命令确认时才提交；Combine/Boolean仍要求真实选择，Retopologize本入口灰显；不穿透非Mesh | 待测 |
| OM-14 | 将MODEL及Object专用命令改绑、禁用、恢复；在Object和Edit分别测试 | 主热盒与列表共用正确触发/释放；Object专用快捷键不抢占Edit/3D View原生同键，旧生成项正确清理 | 待测 |
| OM-15 | 单/四视图、视口四角、Sidebar打开、125/150/200%DPI下使用组合菜单 | 实际八向内缘留白仍对齐Views；列表/方框可读且不覆盖真实按下取消区；空间不足分页或无重叠翻边，不缩小径向间距 | 待测 |
| OM-16 | 检查灰显缺口与适配说明，特别是Retopologize主项及参数方框 | UV/Proxy/Connect/Transfer/整体拓扑等未实现项不伪装成可用；新菜单的Retopologize两入口明确灰显，说明缺少确认时的目标身份适配，不能转投新active；既有Space原生入口语义不变 | 待测 |

## P0/P1：热盒与菜单统一图标（新增14项）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| IC-01 | Space打开主热盒，查看File/Edit/Create/Select/Modify及中心控制等入口 | 每个功能和目录文字左侧都有Blender内置图标；标题完整，中心区和原按下点可取消 | 待测 |
| IC-02 | 打开Views，依次查看透视及六个正交视图，单/四视图重复 | 每个方向按钮都有图标；保持24逻辑像素行高和既有真实内缘留白，图标不挤压中心或相邻按钮 | 待测 |
| IC-03 | 分别持Q/W/E/R反复按LMB开盒，进入Axis/Custom Axis等子环 | 一级和子环各功能都有图标，长标签完整；反复开盒、回中心和外延释放行为不变 | 待测 |
| IC-04 | Object及Edit分别用组件RMB热盒切点/边/面和其他现有选择入口 | 左图标与功能一致；状态可识别，空方向/禁用方向不误选 | 待测 |
| IC-05 | 无选择在空白Shift+RMB打开基本体创建热盒，再经Space→Create查看列表 | Cube/Sphere/Cylinder等使用相应Blender图标，同一创建功能跨入口图标一致；创建和取消正常 | 待测 |
| IC-06 | 选中Object与Edit单域组件，Shift+RMB检查建模环及Object下方列表 | 每个工具和灰显缺口左侧都有图标；上下两部分间距保留，标签和右侧参数格不重叠 | 待测 |
| IC-07 | 展开Edit/Create/Mapping/Booleans等普通菜单和多级目录，滚动翻页 | 目录与叶项均有左图标，右侧级联箭头保留；翻页前后文字和图标列对齐，边缘不裁切 | 待测 |
| IC-08 | 打开含radio/checkbox的设置列表，切换选项、重新开盒，再翻页 | 功能图标和单选圈/勾选各自显示；有状态与无状态的兄弟条目列对齐；状态随实际设置刷新 | 待测 |
| IC-09 | 在Smooth/Mirror/Reduce/Remesh文字与右侧Options格分别释放 | 主文字左侧是对应功能图标；参数格只有一个齿轮，仍独立命中且不同时执行主功能 | 待测 |
| IC-10 | 比较同一热盒或列表内的可用项与灰显项，悬停及尝试释放 | 禁用功能的图标和文字同步变灰；禁用原因可见，禁用图标不制造可执行错觉 | 待测 |
| IC-11 | 100/125/150/200% UI缩放，检查短标签、最长标签和级联目录 | 图标随界面清晰缩放，左图标/文字/状态/右箭头不相互覆盖；窄区域按既有规则夹紧或分页 | 待测 |
| IC-12 | 使用Blender深色和浅色主题，比较普通/悬停/禁用状态 | 图标沿用Blender原生主题风格，对比清楚，尺寸与文字协调，无混入emoji或外部图标风格 | 待测 |
| IC-13 | 同一实例将Views与QWER/组件/创建/建模五行热盒对照，经过第2/4行及第3行间隙后外划 | 新增宽度向外容纳；真实内缘和命中间隔以Views为标杆；取消区、外延提交和原有方向不变 | 待测 |
| IC-14 | 执行一个进入Recent的功能，再从Recent/普通菜单比较；切换个人热盒配置和中英文标签 | 同一命令在不同入口保持同一图标，翻译不改变语义；返回/翻页仍为单一导航图标，无重复图标 | 待测 |

## 已知问题与后续范围

- **本轮可见区域修复**：已修复 Tool Header/工具栏/侧栏遮挡布局及原地取消后的工具上下文问题；开发证据见本轮记录，实体鼠标、用户布局和DPI人工回归仍待VR项。
- **M2c 本批**：空白Shift+RMB七种基本体及Space→Create入口，验收见K项；Create Polygon Tool为M2c-P01占位，Disc为Blender填充圆适配。
- **M2d 当前进度**：已有单域点/边/面选择的Shift+RMB已接入，验收见D项。已选Object/预选事务及Object组合菜单已接入，验收见O/OM项。Edit无选择预选、Ctrl+RMB选择转换和Ctrl+Shift+RMB当前工具上下文仍为独立后续片；不代表全M2完成。
- **M3 本批已接入**：12组建模菜单、已核实原生能力与相应快捷键；最终安装验收见本批M3记录，人工验证见M3-01至M3-34。已接入、近似适配与带唯一编号的缺失能力计划分开记录；本清单不等于所有Maya能力已齐全。
- **M3缺失计划边界**：NURBS修剪/轨道构面/连续性、特定deformer关系等按本批逐leaf覆盖记录验收；近似原生项只承诺其差异说明中的能力。已有明确计划不是将无效可执行项或已接功能回归合理化。
- **完整Paint/Hair范围**：按本批覆盖记录的 `scope_override: deferred` 明确后置，不计入本轮范围内缺失native能力计划；Vertex Paint原生入口已接，不代表完整绘制/毛发工作流已完成。
- **独立后续不混算**：M2对象/组件组合热盒、UV与其他明确后置能力不因M3菜单尚无等效动作而自动算作本批实现缺陷；若本批改动破坏它们已有的fallback/占位/输入边界，仍需记录回归。
- **组件能力边界**：Select → Convert Selection → Multi-Component 已接入Blender点/边/面同时启用的原生多域组合；Vertex Face独立交互选择域仍后置。UV全链路继续后置；Global物体缩放按既定决定无开发计划。
- **测试设施已知限制**：旧 `AxisMeld-build/install/blender.exe` 对应的应用级 CTest 有历史失败；实际交付入口应独立验证。

## 人工结果记录

2026-09-14 用户确认S/P/C/V/T/R共47项已测试；未提供逐项通过/失败、测试构建和环境明细。本记录不额外推定全部通过，也不擅自关闭“已知待修”。G组10项未包含在本次已测试反馈中。

记录模板：`日期 | 构建哈希前12位 | 编号 | 环境 | 结果 | 复现/备注`。


## P0/P1：Maya组合菜单内容与分组对齐（本轮MC新增14项，全部待测）

按用户最终要求，保留Maya菜单内容、顺序与分组，不删除未实现占位。Object固定22个主项、7个分隔；创建固定16个主项、3个分隔。自动化结果与下列人工状态分开记录。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| MC-01 | 选中Object Mesh，Shift+RMB，与本轮Maya建模截图逐行对照并滚动到末尾；1x/2x检查右侧目录箭头 | 22个主项全部保留且顺序一致，Mapping/Booleans/Polygon Display目录及所有未实现占位仍可见；目录箭头不被相邻参数列背景遮住，未擅自精简占位 | 待测 |
| MC-02 | Object无选择且鼠标为空白，Shift+RMB，逐组检查创建下拉并翻页 | 依次为Platonic Solid、Pyramid、Prism、Pipe、Helix、Gear、Soccer Ball；Super Ellipse、Spherical Harmonics、Ultra Shape、Type、SVG、Quad Draw Tool；Interactive Creation、Exit On Completion；Polygon Display All，共16主项、3分隔 | 待测 |
| MC-03 | 单视图1x/2x对照普通行和每个分隔，慢移鼠标跨过所有分隔 | 功能行24逻辑像素、细分隔6逻辑像素；分组清楚，布局/点击/高亮使用同一实际高度，分隔不占完整功能行 | 待测 |
| MC-04 | 持住RMB在Object及创建的分隔线上释放，再在其左右列表背景释放 | 不穿透执行径向按钮、不执行上下邻行，不新增物体/修改器、Recent或Undo；新手势可重开 | 待测 |
| MC-05 | 检查Object N Target Weld、NW Sculpt、W Multi-Cut、E Append、SW Insert Edge Loop的参数格，各在格内释放 | 五个径向参数格独立可见，本轮新增Options全部禁用；参数格不误执行主工具，也不改变原方向命中与Views内缘 | 待测 |
| MC-06 | 在创建八个方向的文字、图标、右侧参数格分别悬停/释放 | 八方向均有独立参数格，图标与文字完整；本轮新增Options全部禁用；主动作仍只创建对应对象一次 | 待测 |
| MC-07 | 检查创建下拉每个主项右侧，逐个尝试可用与灰显参数格 | 除Type/SVG外的11个功能项保留参数格；设置与Polygon Display All目录不伪装成参数功能；没有删除占位或点击灰格执行主动作 | 待测 |
| MC-08 | Object径向SE Soften/Harden展开，查看子目录并返回主环；创建Polygon Display All也展开 | 都以普通目录呈现；仅已有可验证适配动作启用，其余保留灰显与原因；父环/伴随列表保持，级联不出现孤立handler | 待测 |
| MC-09 | 检查创建Interactive Creation与Exit On Completion，点击后重开；记录相关偏好前后值 | 未实现工作流保持灰显，Exit On Completion显示截图勾选且禁用；勾选与语义图标分列，不改写全局偏好或伪装可切换设置 | 待测 |
| MC-10 | 在无选择空白、有效Mesh选择、鼠标预选Mesh、非Mesh阻挡、Edit各状态分别重开；再从Space Create目录进入 | 各入口遵循已有选择/预选/模式规则，创建只在适用上下文执行；新伴随列表不绕过过滤、不暗中改变目标，Space显式创建保留其既有语义 | 待测 |
| MC-11 | 单/四视图与1x/2x，分别对比Views、Object、创建的真实按钮内缘及长标签 | 保留24高、Views中心和横向净距；参数格向外占宽，普通列表依真实6px分隔分页；极窄不支持时安全拒绝、不残留handler | 待测 |
| MC-12 | 在四个视口角落及125/150/200%DPI展开伴随列表与末页子菜单，再回真实按下点 | 菜单/参数/级联夹紧在有效视口内，必要时分页；显示与命中一致，原起点仍能取消；Tool Header/侧栏不被当作可用空间 | 待测 |
| MC-13 | 创建与Object连续开关各三次；Q/W/E/R持键LMB重复唤出；Space中心目录交替进入 | 伴随列表不会遗留到另一根，分页/悬停状态按当前会话正确重置；旧QWER持键重复规则与鼠标释放所有权不变 | 待测 |
| MC-14 | 径向主项/参数/下拉/级联中分别Esc、先松Shift、切应用、改选择/模式后释放；随后再开Views和创建 | 取消不提交动作、不污染Undo/Recent，不留粘键；失效的捕获目标不转投别的对象，后续有效输入正常 | 待测 |

## P0/P1：全热盒菜单内容对齐（本轮 HC 新增20项）

以本机 Maya 2026 MEL 与实际显示资源为内容依据。灰显表示能力尚未适配，人工核对菜单存在不等于该能力已实现。

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| HC-01 | Object模式，无任何选择，在可见Mesh上RMB；再选A指向B重复 | 环下显示22项DAG菜单和7处分隔，首项是实际指针目标名称；从Select到材质三组的名称和顺序对齐截图；打开和关闭不改变选择 | 待测 |
| HC-02 | RMB依次进入UV、Inputs/Outputs、Paint、Metadata、Actions、Time Editor和材质子菜单 | UV含UV/UV Shell；固定项目保持Maya顺序。动态DG、UV/颜色集、插件材质和收藏未适配处灰显说明，不显示猜造的场景数据 | 待测 |
| HC-03 | RMB伴随列表悬停禁用项、Select Similar参数格、Metadata状态和参数格后取消 | 禁用项有原因且不能执行，参数格与正文独立；不改变选择、模式、对象属性、偏好或Recent | 待测 |
| HC-04 | A选中指向B打开RMB，分别从列表执行Select All、Deselect All、Invert Selection | 按原始场景选择执行全局操作，不先把指针B提交为选中对象；重复、撤销与原生命令一致 | 待测 |
| HC-05 | 指针目标为当前已选活动Mesh时测试Select Hierarchy和Actions的Template/Untemplate/Unparent；然后改为未选目标 | 只有上下文安全时可执行；未选或变化后的目标相关操作不偷偷提交指针选择，不作用到旧活动对象 | 待测 |
| HC-06 | Edit Vertex有有效选择，Shift+RMB，并依次展开列表子菜单 | 顶点菜单下方9个主项、3处分隔；参数入口与Maya一致；Reorder Vertices依赖能力保留灰显说明 | 待测 |
| HC-07 | Edit Edge有有效选择，Shift+RMB，核对Merge子菜单及下方列表 | 边菜单下方14个主项、3处分隔；Merge Border Edges及其参数入口存在，不把未适配参数绑定为直接执行 | 待测 |
| HC-08 | Edit Face有有效选择，Shift+RMB，查看Mapping和Polygon Display | 面菜单下方20个主项、4处分隔，含顶部的分隔；保留Smart Extrude、完整Mapping及对应显示菜单 | 待测 |
| HC-09 | Q+LMB，核对Marquee、Drag、Camera-Based Selection和下方菜单 | 下方为Automatic Camera-Based Selection；Marquee勾选反映实际工具，其他未适配状态灰显且不伪造选中 | 待测 |
| HC-10 | W+LMB，核对下方主项、约束和Move Options | 下方9个主项、3处分隔，Preserve UVs/Children、Tweak Mode、Update Triad等位置正确；方向名称World/Object/Component与真实方向状态一致 | 待测 |
| HC-11 | E+LMB，核对下方主项并展开Rotate Center | 下方11个主项、3处分隔；Rotate Center含Default/Object/Manip/Selection，保留Free Rotate、Relative和Rotate Options | 待测 |
| HC-12 | R+LMB，核对下方主项并展开Scale Center | 下方10个主项、3处分隔；Scale Center含Default/Object/Manip，保留Prevent Negative Scale和Scale Options | 待测 |
| HC-13 | 从Q/W/E/R各进入Select子环，然后进入Soft Select并返回 | Select子环有自己的Automatic Camera-Based Selection下方列表；切换和返回不残留父层或上一工具的菜单内容 | 待测 |
| HC-14 | 分别进入W/E/R的Selection Constraints、Transform Constraints与中心选项 | 完整7项选择约束与4项变换约束顺序正确，单选圆圈与复选框形态准确；未适配状态均灰显且无虚假选中 | 待测 |
| HC-15 | 逐个检查QWER的Symmetry、Soft Select、Axis/Custom和Snap子菜单 | 使用Maya实际显示标签、条目和状态形态；不添加Maya不存在的批量齿轮；Blender View方向仍可从Space→Modify→Blender View Orientations访问 | 待测 |
| HC-16 | Space→Hotbox Controls，检查Show/Hide、Custom Menu Set、Hotbox Style、Window Options | 补齐固定菜单项和分隔；已有Common/Pane/Modeling行开关显示真实checkbox，Style和Transparency单选状态不受影响；未适配选项有原因 | 待测 |
| HC-17 | 创建热盒→Polygon Display All，连续执行Backface Culling on两次，再off两次 | 目录10项、4处分隔，On/Off为两个独立普通命令；重复On保持开、重复Off保持关，不交替反转 | 待测 |
| HC-18 | Object建模和创建热盒逐项对照Maya截图，并检查Mapping、Booleans和Polygon Display | Object22项与Create16项主目录保留；不单纯删除占位缩短列表；嵌套内容、名称、分隔和Options逐项匹配 | 待测 |
| HC-19 | 全部新列表滚动到底，查看长标签、子目录箭头、Options方格和左侧图标 | 图标使用统一Blender风格；24逻辑像素行高、6像素分隔，参数背景不覆盖箭头，正文与Options可独立命中 | 待测 |
| HC-20 | 在单/四视图、窄视口和125/150/200%DPI，重试RMB、建模与QWER嵌套菜单及取消 | 以Views实际内缘间距为标杆；未遮挡外延保持长划，被列表覆盖的方向从主按钮提交，列表与分隔不穿透执行环；子菜单夹紧/滚动及重复唤出、释放正确。200%较小四视图放不下完整环和最少分页行时取消打开且无输入残留；放大窗格后重试 | 待测 |
