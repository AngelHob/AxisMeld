# AxisMeld 待人工测试清单

更新：2026-09-14。用户反馈“除去新增10项，其余都已经测试过了”：S/P/C/V/T/R共47项标记为已测试（用户确认，未逐项报告通过/失败）；G-01至G-10和K-01至K-12共22项仍待测。本轮追加L-01至L-06布局回归和M3-01至M3-34建模人工测试，共40项，全部待人工验证。合计109项：已测试47项，待测62项。历史测试反馈不会被自动化结果覆盖。

## 测试准备与反馈

使用 `D:/source/AxisMeld-build/phase2b-ui-test-install/blender.exe`，先保存原场景，再使用临时 Cube 场景。选择 AxisMeld Maya 2026 键位。最新安装证据以本批验收记录为准；历史批次哈希不代表当前安装。

M3-20260914构建和安装核验已完成，主程序哈希前12位为`03E54896A387`；开发验证与局限见同批M3开发记录。开始测试前核对主入口，避免混入另一个旧安装。破坏性编辑、Cut、转换、绑定与颜色测试只在临时场景进行，每组先保存一个可还原副本。需要原生参数时使用 **Space → Edit → Adjust Last Operation**，修改器也可在原生Modifier属性中继续调整；**F9仍是Vertex入口**。Vertex Paint入口只切换到Blender原生绘制模式，不代表本批实现了完整Maya绘制工具链。

先跑优先级 P0，再跑 P1。反馈格式：`编号 / 通过或失败 / Object或Edit / 单或四视图 / 实际结果`。涉及误触时补充鼠标路线与释放顺序；涉及显示时补充 Windows 缩放比例和视口大小。通过与失败均保留日期、版本；未反馈不推定通过。

## P0：热盒划选与重复唤出（上一批仍待测）

| 编号 | 前置条件与操作 | 预期 | 人工状态 |
|---|---|---|---|
| G-01 | QWER与四视图二级热盒对照，单/四视图查看 | 以四视图Views热盒实际横向留白为标杆，第2/4行和第3行左右按钮内缘间距分别对齐；不缩小Views迁就其他菜单，不只凭“未重叠”判定；标签完整、方向不变 | 待测 |
| G-02 | W/E/R经过Global/Local按钮后继续水平向外滑出很远，再松LMB | 对应方向仍高亮且提交，不要求停在按钮上；远处不跳相邻行 | 待测 |
| G-03 | Q选择工具与组件RMB环，在按钮外释放；划向禁用方向或缺席的NW | 有效方向提交正确命令；禁用/空方向不误选相邻项，组件取消不改变目标 | 待测 |
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
| K-01 | Object无选择，鼠标位于空白；按住Shift并按住RMB，中心松RMB，反复重开 | 立即显示Polygon Primitives；使用既有紧凑模板；每次中心释放关闭，不改变场景 | 待测 |
| K-02 | 将3D Cursor移到可辨位置，分别创建NE Disc、E Sphere、SE Torus、S Cube、SW Cone、W Cylinder、NW Plane；每次先清空选择并移到空白 | 每次只创建一个对应网格、选中新物体、位于Cursor；Disc有填充面；不移动Cursor，默认尺寸/细分沿用Blender | 待测 |
| K-03 | 对K-02七种创建分别只撤销一次，再重做一次 | 一次撤销完整移除本次新物体并恢复原场景；重做仅恢复一个，无额外热盒撤销步骤 | 待测 |
| K-04 | 经过七个方向按钮后继续外划，在按钮外很远处保持Shift并松RMB | 保持当前方向并提交；不要求鼠标停在按钮上，不误选邻项 | 待测 |
| K-05 | 在中心释放、出中心再回划、划到N Create Polygon Tool后释放 | 三种情况均不创建、不写Recent、不增加撤销；N明确灰显占位；随后可正常重开 | 待测 |
| K-06 | 开环后先松Shift、加按Ctrl或Alt、Esc、切应用、切模式/窗口；交换Shift/RMB释放顺序再重试 | 变化中的手势取消；不误创建、不留残余鼠标/热键拦截；恢复条件后新手势可用 | 待测 |
| K-07 | 已选择网格/非网格、Edit Mode、空选择但鼠标指向可选物体；各用Shift+RMB | 不显示空白创建菜单，保留当前Blender原生行为；不偷偷选中鼠标下对象；后续对象/组件建模菜单尚未接入 | 待测 |
| K-08 | Object已有选中对象时Space→Create→Polygon Primitives创建；Edit中再查看该入口 | Object可创建且一次撤销恢复原有对象和选择；Edit下创建项不可执行 | 待测 |
| K-09 | 临时配置改绑创建热盒至键盘或Ctrl/Shift组合，再禁用，重新加载配置 | 新绑定仅在无选择Object开启；禁用/改绑后原Shift+RMB保留原生行为；Alt/OSKey非法配置被拒绝，普通组件RMB限制不变 | 待测 |
| K-10 | 单/四视图、视口四角/较窄区域、125/150/200%DPI重试K-01/K-04/K-05 | 标签可读，菜单夹紧后真实按下点仍可取消，命中与显示一致；极窄Tool Header遮挡仍是独立已知问题 | 待测 |
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

模式切换沿用 Blender 原生选择集合语义。Object鼠标入口使用本批P项规则；空白处、Edit、键盘改绑和Space目录继续当前有效上下文。Shift/Ctrl建模右键仍待后续开发。

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
| M3-33 | 窄视口/四视图/125–200%DPI打开M3长列表，翻页、返回、悬停最下项与移出列表；在设置项重复改变值 | 长标签、radio和分页互不遮挡；原生菜单当前不显示快捷键文本，快捷键另按M3-15/16/18实际按键验证；移出不虚选列表项，翻页后命令/状态对应正确；记录Tool Header已知问题另列 | 待测 |
| M3-34 | 备份个人配置；临时改一个M3快捷键、保留原QWER/底色/透明度，重载并重启；浏览M3灰显计划、UV及M2后续占位 | 改键生效且无旧绑定残留，其他配置不被覆盖；计划显示明确理由/编号且不执行；UV与独立M2后续不因本批菜单接入被误标完成 | 待测 |

## 已知问题与后续范围

- **已知待修**：极窄视口 Tool Header 遮挡，不能将布局自动化通过写成此缺陷已解决。
- **M2c 本批**：空白Shift+RMB七种基本体及Space→Create入口，验收见K项；Create Polygon Tool为M2c-P01占位，Disc为Blender填充圆适配。
- **M2 后续**：已选对象/点/边/面上下文、预选路由、Shift/Ctrl建模组合热盒及相关操作；详见本批映射的M2d-P01至P07，不代表全M2完成。
- **M3 本批已接入**：12组建模菜单、已核实原生能力与相应快捷键；最终安装验收见本批M3记录，人工验证见M3-01至M3-34。已接入、近似适配与带唯一编号的缺失能力计划分开记录；本清单不等于所有Maya能力已齐全。
- **M3缺失计划边界**：NURBS修剪/轨道构面/连续性、特定deformer关系等按本批逐leaf覆盖记录验收；近似原生项只承诺其差异说明中的能力。已有明确计划不是将无效可执行项或已接功能回归合理化。
- **完整Paint/Hair范围**：按本批覆盖记录的 `scope_override: deferred` 明确后置，不计入本轮范围内缺失native能力计划；Vertex Paint原生入口已接，不代表完整绘制/毛发工作流已完成。
- **独立后续不混算**：M2对象/组件组合热盒、UV与其他明确后置能力不因M3菜单尚无等效动作而自动算作本批实现缺陷；若本批改动破坏它们已有的fallback/占位/输入边界，仍需记录回归。
- **组件能力边界**：Select → Convert Selection → Multi-Component 已接入Blender点/边/面同时启用的原生多域组合；Vertex Face独立交互选择域仍后置。UV全链路与Global物体缩放算法继续后置。
- **测试设施已知限制**：旧 `AxisMeld-build/install/blender.exe` 对应的应用级 CTest 有历史失败；实际交付入口应独立验证。

## 人工结果记录

2026-09-14 用户确认S/P/C/V/T/R共47项已测试；未提供逐项通过/失败、测试构建和环境明细。本记录不额外推定全部通过，也不擅自关闭“已知待修”。G组10项未包含在本次已测试反馈中。

记录模板：`日期 | 构建哈希前12位 | 编号 | 环境 | 结果 | 复现/备注`。
